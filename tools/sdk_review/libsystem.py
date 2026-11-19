"""Local libSystem reference comparison and gap investigation."""

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re
import shlex
import sys
import tempfile

from .libsystem_tbd import object_fields, read_json, read_stub, require, run_reader, string, string_list


STUB_PATH = Path("usr/lib/libSystem.B.tbd")
ALIAS_PATH = Path("usr/lib/libSystem.tbd")
SCHEMA = 1
DIGEST = re.compile(r"[0-9a-f]{64}")
SDK = re.compile(r"macosx[0-9]+\.[0-9]+(?:\.[0-9]+)?")


def canonical(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()


def digest(data):
    return sha256(data).hexdigest()


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                     delete=False) as output:
        output.write(data)
    Path(output.name).replace(path)


def write_json(path, value):
    write(path, json.dumps(value, sort_keys=True, indent=2) + "\n")


def input_stub(path):
    path = path.absolute()
    stub = path
    alias = None
    if path.is_dir():
        stub = path / STUB_PATH
        require(stub.is_file(), f"missing expected primary libSystem stub {stub}")
        alias_path = path / ALIAS_PATH
        if alias_path.is_symlink():
            raw_link = alias_path.readlink()
            alias = {
                "kind": "symlink", "link": str(raw_link),
                "resolves_to_primary": alias_path.resolve() == stub.resolve(),
            }
        elif alias_path.is_file():
            alias = {"kind": "file", "sha256": digest(alias_path.read_bytes())}
        else:
            require(not alias_path.exists(), f"unexpected path at {alias_path}")
            alias = {"kind": "missing"}
    data = stub.read_bytes()
    return {"path": str(path), "stub": str(stub), "sha256": digest(data), "alias": alias}, data


def missing_or_extra(reference, candidate, noun):
    if reference is None:
        return f"extra-{noun}"
    if candidate is None:
        return f"missing-{noun}"
    return f"changed-{noun}"


def reachable_providers(stub, target):
    """Find exact-target reachable documents, without guessing LLD's binding."""
    providers = {}
    visited = set()
    pending = [stub.main]
    while pending:
        name = pending.pop()
        if name in visited:
            continue
        visited.add(name)
        entry = stub.libraries.get(name, {}).get(target)
        if entry is None:
            continue
        pending.extend(entry.reexports)
        for identity, attributes in entry.symbols.items():
            if attributes["role"] != "undefined":
                providers.setdefault(identity, set()).add(name)
    return providers


def gaps_for(sdk, reference, candidate, reference_input, candidate_input):
    gaps = []

    def add(kind, library, target, field, ref, cand, symbol=None, encoding=None):
        identity = {
            "sdk": sdk, "kind": kind, "library": library, "target": target,
            "field": field, "symbol": symbol, "encoding": encoding,
        }
        gaps.append({
            "id": "libsystem-" + digest(canonical(identity))[:24],
            **identity, "reference": ref, "candidate": cand,
        })

    if reference.main != candidate.main:
        add("changed-main-install-name", reference.main, None, "install_name",
            reference.main, candidate.main)
    reference_alias = reference_input["alias"]
    candidate_alias = candidate_input["alias"]
    if reference_alias is not None and candidate_alias is not None and reference_alias != candidate_alias:
        add("changed-filesystem-alias", reference.main, None, str(ALIAS_PATH),
            reference_alias, candidate_alias)

    all_targets = set()
    for name in sorted(reference.libraries.keys() | candidate.libraries.keys()):
        ref_targets = reference.libraries.get(name, {})
        cand_targets = candidate.libraries.get(name, {})
        if not (ref_targets and cand_targets):
            add("missing-library" if ref_targets else "extra-library",
                name, None, "install_name", sorted(ref_targets) or None, sorted(cand_targets) or None)
        all_targets.update(ref_targets.keys() | cand_targets.keys())
        for target in sorted(ref_targets.keys() | cand_targets.keys()):
            ref = ref_targets.get(target)
            cand = cand_targets.get(target)
            if ref is None or cand is None:
                add(missing_or_extra(ref, cand, "target"), name, target, "target",
                    target if ref is not None else None, target if cand is not None else None)
            else:
                for field in sorted(ref.metadata.keys()):
                    if ref.metadata[field] != cand.metadata[field]:
                        add(f"changed-{field.replace('_', '-')}", name, target, field,
                            ref.metadata[field], cand.metadata[field])
            ref_edges = ref.reexports if ref else set()
            cand_edges = cand.reexports if cand else set()
            for edge in sorted(ref_edges ^ cand_edges):
                add("missing-reexport-edge" if edge in ref_edges else "extra-reexport-edge",
                    name, target, edge, edge if edge in ref_edges else None,
                    edge if edge in cand_edges else None)
            ref_symbols = ref.symbols if ref else {}
            cand_symbols = cand.symbols if cand else {}
            for encoding, symbol in sorted(ref_symbols.keys() | cand_symbols.keys()):
                before = ref_symbols.get((encoding, symbol))
                after = cand_symbols.get((encoding, symbol))
                noun = "export"
                sides = [attributes["role"] for attributes in (before, after) if attributes]
                if symbol.startswith("$ld$"):
                    noun = "linker-directive"
                elif set(sides) == {"undefined"}:
                    noun = "undefined-symbol"
                if before is None or after is None:
                    add(missing_or_extra(before, after, noun), name, target, "symbol",
                        before, after, symbol, encoding)
                else:
                    for field in sorted(before.keys()):
                        if field == "segment" and None in (before[field], after[field]):
                            continue
                        if before[field] != after[field]:
                            add(f"changed-{noun}-{field.replace('_', '-')}", name, target, field,
                                before[field], after[field], symbol, encoding)

    for target in sorted(all_targets):
        # A missing root target is already a raw gap. Do not extrapolate its resolution.
        if any(target not in stub.libraries[stub.main] for stub in (reference, candidate)):
            continue
        before = reachable_providers(reference, target)
        after = reachable_providers(candidate, target)
        for encoding, symbol in sorted(before.keys() | after.keys()):
            old = before.get((encoding, symbol), set())
            new = after.get((encoding, symbol), set())
            if old and new and old != new:
                add("changed-reachable-provider", reference.main, target, "providers",
                    sorted(old), sorted(new), symbol, encoding)
    return sorted(gaps, key=lambda gap: (
        gap["library"], gap["target"] or "", gap["symbol"] or "", gap["kind"], gap["field"]
    ))


def inventory(stub):
    entries = []
    for name, slices in sorted(stub.libraries.items()):
        for target, entry in sorted(slices.items()):
            entries.append({
                "library": name, "target": target, "reexports": len(entry.reexports),
                "symbols": dict(sorted(Counter(value["role"] for value in entry.symbols.values()).items())),
            })
    return {"format": stub.format, "main": stub.main, "libraries": len(stub.libraries), "slices": entries}


def compare(args):
    require(SDK.fullmatch(args.sdk), f"expected canonical SDK name, got {args.sdk!r}")
    reference, reference_data = input_stub(args.reference)
    candidate, candidate_data = input_stub(args.candidate)
    reader = (args.llvm / "bin/llvm-readtapi").absolute()
    require(reader.is_file(), f"missing llvm-readtapi at {reader}")
    ref = read_stub(reference_data.decode(), reader)
    cand = read_stub(candidate_data.decode(), reader)
    # TextAPI's independent comparison can disagree when its data model coalesces raw flags.
    # Read snapshots so the text comparison and structured report use the same input bytes.
    with tempfile.TemporaryDirectory(prefix="libsystem-compare-") as temp:
        directory = Path(temp)
        paths = [directory / "reference.tbd", directory / "candidate.tbd"]
        for path, content in zip(paths, (reference_data, candidate_data)):
            path.write_bytes(content)
        independent = run_reader(reader, ["-compare", *paths], compare=True)
        for snapshot, original in zip(paths, (reference, candidate)):
            independent = independent.replace(str(snapshot), original["stub"])
    gaps = gaps_for(args.sdk, ref, cand, reference, candidate)
    report = {
        "schema": SCHEMA, "sdk": args.sdk, "llvm": str(args.llvm.absolute()),
        "reader_sha256": digest(reader.read_bytes()),
        "reference": {**reference, **inventory(ref)},
        "candidate": {**candidate, **inventory(cand)},
        "independent_diff": "llvm-readtapi-compare.txt",
        "comparison_limits": {
            "filesystem_alias": reference["alias"] is not None and candidate["alias"] is not None,
            "symbol_segments": ref.format == cand.format == 5,
            "provider_view": "exact-target reachable providers; effective binding requires a paired link",
        },
        "counts": dict(sorted(Counter(gap["kind"] for gap in gaps).items())),
        "gaps": gaps,
    }
    write(args.out / report["independent_diff"], independent)
    write_json(args.out / "libsystem-diff.json", report)
    print(f"{len(gaps)} gaps across {len(ref.libraries)} reference and "
          f"{len(cand.libraries)} candidate libraries")
    return int(args.check and bool(gaps))


def report_path(work):
    paths = [path / "libsystem-diff.json" for path in (work, work / "diff")]
    available = [path for path in paths if path.is_file()]
    require(len(available) == 1, f"expected one comparison report among {paths}")
    return available[0]


def read_report(work):
    path = report_path(work)
    report = read_json(path.read_bytes())
    require(isinstance(report, dict) and report.get("schema") == SCHEMA
            and isinstance(report.get("gaps"), list), f"unsupported comparison report {path}")
    return report, path


def decision_digest(gaps):
    return digest(canonical(sorted(gaps, key=lambda gap: gap["id"])))


def apply_decisions(report, path):
    gaps = {gap["id"]: gap for gap in report["gaps"]}
    require(len(gaps) == len(report["gaps"]), "comparison report contains duplicate gap IDs")
    if path is None:
        return {}, [], None
    ledger = read_json(path.read_bytes())
    fields = {"schema", "sdk", "reference_sha256", "decisions"}
    object_fields(ledger, fields, "decision ledger", fields)
    require(type(ledger["schema"]) is int and ledger["schema"] == SCHEMA, "unsupported decision schema")
    require(isinstance(ledger["decisions"], list), "decisions must be an array")
    baseline = string(ledger["reference_sha256"], "reference_sha256")
    require(DIGEST.fullmatch(baseline), "reference_sha256 must be a SHA-256 digest")
    sdk = string(ledger["sdk"], "SDK")
    baseline_matches = (baseline == report["reference"]["sha256"] and sdk == report["sdk"])
    approved = {}
    stale = []
    seen_ids = set()
    seen_members = set()
    for decision in ledger["decisions"]:
        fields = {"id", "members", "member_sha256", "evidence", "impact", "approver", "revisit"}
        object_fields(decision, fields, "decision", fields)
        decision_id = string(decision["id"], "decision id")
        members = string_list(decision["members"], "decision members")
        require(members and decision_id not in seen_ids and not (set(members) & seen_members),
                f"empty, duplicate or overlapping decision {decision_id}")
        seen_ids.add(decision_id)
        seen_members.update(members)
        for field in fields - {"members"}:
            string(decision[field], field)
        require(DIGEST.fullmatch(decision["member_sha256"]), "member_sha256 must be a SHA-256 digest")
        reason = None
        if not baseline_matches:
            reason = "reference baseline or SDK changed"
        elif not all(member in gaps for member in members):
            reason = "one or more decision members disappeared"
        elif decision_digest([gaps[member] for member in members]) != decision["member_sha256"]:
            reason = "decision member IDs or findings changed"
        if reason:
            stale.append({"id": decision_id, "reason": reason})
        else:
            approved.update({member: decision_id for member in members})
    return approved, stale, baseline_matches


def backlog(args):
    report, path = read_report(args.work)
    approved, stale, baseline_matches = apply_decisions(report, args.decisions)
    entries = [
        {**gap, "status": "approved" if gap["id"] in approved else "open",
         "decision": approved.get(gap["id"])}
        for gap in report["gaps"]
    ]
    # Only independently reviewed decisions can mark a row approved.
    counts = dict(sorted(Counter(entry["status"] for entry in entries).items()))
    result = {
        "schema": SCHEMA, "comparison": str(path.absolute()), "sdk": report["sdk"],
        "reference_sha256": report["reference"]["sha256"], "counts": counts,
        "decision_baseline_matches": baseline_matches, "stale_decisions": stale, "gaps": entries,
    }
    write_json((args.out or args.work) / "libsystem-backlog.json", result)
    print(f"{counts.get('open', 0)} open, {counts.get('approved', 0)} approved, "
          f"{len(stale)} stale decisions")
    if baseline_matches is False:
        print("Decision ledger SDK or reference digest differs from the comparison", file=sys.stderr)
    return int(args.check and (bool(counts.get("open")) or bool(stale) or baseline_matches is False))


def matches_symbol(spelling, symbol):
    return spelling is not None and any(
        spelling == value or spelling.startswith(value + "$") for value in (symbol, "_" + symbol)
    )


def link_commands(report, path, gaps, args):
    arches = {
        gap["target"].split("-", 1)[0]
        for gap in gaps if gap["target"] and gap["target"].endswith("-macos")
    }
    aliases = {"arm64e": "arm64", "x86_64h": "x86_64"}
    arches = sorted({aliases.get(arch, arch) for arch in arches})
    if any(gap["target"] is None for gap in gaps) and not arches:
        arches = [aliases.get(args.arch, args.arch)] if args.arch else ["arm64", "x86_64"]
    roots = {
        side: report[side]["path"] if report[side]["alias"] is not None
        else f"<{side.upper()}_SDKROOT>"
        for side in ("reference", "candidate")
    }
    return {
        arch: shlex.join([
            "python3", "-m", "tools.sdk_review.verify_libsystem_links",
            "--llvm", report["llvm"], "--reference", roots["reference"],
            "--candidate", roots["candidate"], "--object", "<CLIENT.o>", "--arch", arch,
            "--minimum", args.minimum or "<MINIMUM>",
            "--sdk-version", report["sdk"].removeprefix("macosx"),
            "--out", str(path.with_name(f"libsystem-links-{arch}.json").absolute()),
        ])
        for arch in arches
    }


def explain(args):
    report, path = read_report(args.work)
    targets = {args.arch}
    if args.arch == "arm64":
        targets.add("arm64e")
    if args.arch == "x86_64":
        targets.add("x86_64h")
    selected = [
        gap for gap in report["gaps"]
        if (gap["id"] == args.gap if args.gap else matches_symbol(gap["symbol"], args.symbol))
        and (not args.arch or gap["target"] is None or gap["target"].split("-", 1)[0] in targets)
    ]
    if not selected:
        print("No matching raw differences", file=sys.stderr)
        return 1
    command = [
        "python3", "-m", "tools.sdk_review.libsystem", "compare-libsystem", "--sdk", report["sdk"],
        "--reference", report["reference"]["path"], "--candidate", report["candidate"]["path"],
        "--llvm", report["llvm"], "--out", str(path.parent.absolute()),
    ]
    result = {
        "comparison": str(path.absolute()),
        "independent_diff": str(path.with_name(report["independent_diff"]).absolute()),
        "compare_command": shlex.join(command),
        "paired_link_command_templates": link_commands(report, path, selected, args),
        "requested_context": {"arch": args.arch, "minimum": args.minimum, "profile": args.profile},
        "context_note": "These are raw-target findings. Use paired client links for actual binding, "
                        "minimum deployment and feature-profile behavior.",
        "gaps": selected,
        "member_sha256": decision_digest(selected),
    }
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    compare_parser = commands.add_parser("compare-libsystem")
    compare_parser.add_argument("--sdk", required=True)
    compare_parser.add_argument("--reference", type=Path, required=True)
    compare_parser.add_argument("--candidate", type=Path, required=True)
    compare_parser.add_argument("--llvm", type=Path, required=True)
    compare_parser.add_argument("--out", type=Path, required=True)
    compare_parser.add_argument("--check", action="store_true")
    compare_parser.set_defaults(run=compare)

    backlog_parser = commands.add_parser("backlog")
    backlog_parser.add_argument("--work", type=Path, required=True)
    backlog_parser.add_argument("--out", type=Path)
    backlog_parser.add_argument("--decisions", type=Path)
    backlog_parser.add_argument("--check", action="store_true")
    backlog_parser.set_defaults(run=backlog)

    explain_parser = commands.add_parser("explain-libsystem")
    explain_parser.add_argument("--work", type=Path, required=True)
    selection = explain_parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--gap")
    selection.add_argument("--symbol")
    explain_parser.add_argument("--arch", choices=("arm64", "arm64e", "x86_64", "x86_64h"))
    explain_parser.add_argument("--minimum")
    explain_parser.add_argument("--profile")
    explain_parser.set_defaults(run=explain)

    args = parser.parse_args(argv)
    try:
        return args.run(args)
    except (ValueError, OSError, RuntimeError, KeyError, TypeError) as error:
        print(f"{args.command}: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
