#!/usr/bin/env python3
"""Inventory SDK C header paths absent from the standalone C installation.

Read only: records paths, never copies or hashes SDK header contents.
"""

import argparse
import csv
import fnmatch
import hashlib
import json
import re
import subprocess
from collections import Counter
from pathlib import Path


def installed_header(root: Path, relative: Path) -> bool:
    path = root / "usr/include" / relative
    return path.is_file() and path.resolve().is_relative_to(root)


def closure_paths(manifest: dict, sdk_version: str | None) -> tuple[set[str], set[str]]:
    if manifest.get("schema") != 2:
        raise ValueError("unsupported probe closure schema")
    reference_version = manifest.get("sdk", {}).get("Version")
    if sdk_version and reference_version != sdk_version:
        raise ValueError(f"probe closure SDK version {reference_version} "
                         f"does not match audited SDK {sdk_version}")
    def paths(field: str) -> set[str]:
        return {
            name.removeprefix("usr/include/")
            for entries in manifest["targets"].values()
            for entry in entries.values()
            for name in (entry.get("sysroot", []) if field == "sysroot" else
                         entry.get("lookup_candidates", {}).get("sysroot", []))
            if name.startswith("usr/include/")
        }
    return paths("sysroot"), paths("lookup_candidates")


def decision_rules(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as source:
        rules = list(csv.DictReader(source, delimiter="\t"))
    patterns = set()
    for rule in rules:
        if set(rule) != {"pattern", "decision", "reason"}:
            raise ValueError("decision ledger must have pattern, decision, reason columns")
        if rule["decision"] not in {"include", "omit"} or not rule["reason"].strip():
            raise ValueError(f"invalid decision rule: {rule}")
        if rule["pattern"] in patterns:
            raise ValueError(f"duplicate decision pattern: {rule['pattern']}")
        patterns.add(rule["pattern"])
    return rules


def audit(sdk: Path, installation: Path, resource: Path,
          closure: set[str] | None, lookup_candidates: set[str] | None,
          rules: list[dict[str, str]]) -> dict:
    sdk, installation, resource = sdk.resolve(), installation.resolve(), resource.resolve()
    include = sdk / "usr/include"
    frameworks = sdk / "System/Library/Frameworks"
    excluded = Counter()
    by_directory = {}
    entries = []
    missing = []
    installed = 0
    compiler_overlaps = 0
    decisions = Counter()
    matched_rules = Counter()
    for path in sorted(include.rglob("*")):
        if not (path.is_file() or path.is_symlink()):
            continue
        relative = path.relative_to(include)
        name = relative.as_posix()
        record = {"path": name}
        if relative.parts[0] == "c++":
            category, reason = "c++", "libc++ headers belong to the LLVM toolchain"
        elif relative.parts[0] == "objc":
            category, reason = "objc", "Objective-C is outside this C-only installation"
        elif path.suffix != ".h":
            category, reason = "non_header", "not a C .h header path"
        elif path.is_symlink() and path.resolve().is_relative_to(frameworks):
            category, reason = "framework_symlink", "framework headers are audited separately"
        else:
            category = None
        if category:
            excluded[category] += 1
            record.update(state="excluded", decision="omit", reason=reason,
                          decision_source="scope")
            entries.append(record)
            decisions["omit"] += 1
            continue
        directory = relative.parts[0] if len(relative.parts) > 1 else "<root>"
        counts = by_directory.setdefault(directory, {"installed": 0, "missing": 0})
        present = installed_header(installation, relative)
        if present:
            installed += 1
            counts["installed"] += 1
            record["state"] = "installed"
        else:
            counts["missing"] += 1
            record["state"] = "missing"
            compiler = resource / relative
            if compiler.is_file():
                compiler_overlaps += 1
                record["compiler_resource_overlap"] = True
                record["compiler_uses_include_next"] = bool(re.search(
                    rb"^\s*#\s*include_next\b", compiler.read_bytes(), re.MULTILINE))
            missing.append(name)
        if closure is not None:
            record["in_probe_closure"] = name in closure
        if lookup_candidates is not None and name in lookup_candidates:
            record["probe_lookup_candidate"] = True
        matches = [rule for rule in rules if fnmatch.fnmatchcase(name, rule["pattern"])]
        if len(matches) > 1:
            raise ValueError(f"overlapping decision rules for {name}")
        if matches:
            rule = matches[0]
            matched_rules[rule["pattern"]] += 1
            if rule["decision"] == "omit" and (present or name in (closure or set())):
                raise ValueError(f"cannot omit installed or probe-reached header: {name}")
            record.update(decision=rule["decision"], reason=rule["reason"],
                          decision_source="manual")
        elif present:
            record.update(decision="include",
                          reason="retained in the pinned Apple OSS C installation",
                          decision_source="installation")
        elif closure is not None and name in closure:
            record.update(decision="include",
                          reason="required by the checked-in C probe SDK closure",
                          decision_source="probe")
        elif record.get("compiler_resource_overlap"):
            record.update(decision="review",
                          reason="compiler header overlaps SDK path; assess include_next and API parity",
                          decision_source="unreviewed")
        else:
            record.update(decision="review",
                          reason="not covered by the current probe; assess need and provenance",
                          decision_source="unreviewed")
        decisions[record["decision"]] += 1
        entries.append(record)
    settings = sdk / "SDKSettings.json"
    metadata = json.loads(settings.read_text()) if settings.is_file() else {}
    return {
        "schema": 2,
        "sdk": {key: metadata[key] for key in ("CanonicalName", "Version")
                if key in metadata},
        "scope": "all SDK usr/include file entries; C candidates are .h outside c++, objc, and framework symlinks",
        "path_list_sha256": hashlib.sha256(
            "\n".join(entry["path"] for entry in entries).encode()).hexdigest(),
        "counts": {
            "installed": installed,
            "missing": len(missing),
            "compiler_resource_overlaps_among_missing": compiler_overlaps,
            "excluded": dict(sorted(excluded.items())),
            "decisions": dict(sorted(decisions.items())),
        },
        "by_directory": dict(sorted(by_directory.items())),
        "manual_rules": dict(sorted(matched_rules.items())),
        "entries": entries,
        "missing": missing,
    }


def review_markdown(report: dict) -> str:
    groups: dict[str, list[dict]] = {}
    for entry in report["entries"]:
        if entry["decision"] == "review":
            parts = entry["path"].split("/")
            group = parts[0] if len(parts) > 1 else "<root>"
            groups.setdefault(group, []).append(entry)
    total = sum(map(len, groups.values()))
    lines = [f"# macOS SDK {report['sdk'].get('Version', '?')} C headers for review",
             "", f"{total} paths absent from the C installation. These were not reached",
             "by the current C probe and have no reviewed omit rule. Clang resource",
             "overlaps still require an API-parity decision.", ""]
    for group, entries in sorted(groups.items(), key=lambda item: (-len(item[1]), item[0])):
        title = "Root-level" if group == "<root>" else f"`{group}/`"
        lines.extend((f"## {title} ({len(entries)})", ""))
        for entry in entries:
            suffix = " — Clang resource overlap" if entry.get("compiler_resource_overlap") else ""
            lines.append(f"- `{entry['path']}`{suffix}")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sdk", required=True, type=Path)
    parser.add_argument("--installation", required=True, type=Path)
    parser.add_argument("--clang", required=True, type=Path,
                        help="clang from the pinned minimal LLVM prebuilt")
    parser.add_argument("--reference", type=Path,
                        help="optional C probe closure manifest to mark reached paths")
    parser.add_argument("--decisions", type=Path,
                        default=Path(__file__).resolve().parent / "inputs/sdk-header-decisions.tsv",
                        help="reviewed include/omit decisions; defaults to the checked-in ledger")
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--review-out", type=Path,
                        help="optional Markdown list of paths still needing a decision")
    parser.add_argument("--require-decisions", action="store_true",
                        help="fail if any in-scope path still needs review")
    args = parser.parse_args()
    sdk, installation = args.sdk.resolve(), args.installation.resolve()
    if not (sdk / "usr/include").is_dir():
        parser.error("SDK usr/include does not exist")
    if not (installation / "usr/include").is_dir():
        parser.error("installation usr/include does not exist")
    resource = Path(subprocess.check_output(
        [str(args.clang), "-print-resource-dir"], text=True).strip()).resolve() / "include"
    if not resource.is_dir():
        parser.error("Clang resource include directory does not exist")
    settings = sdk / "SDKSettings.json"
    metadata = json.loads(settings.read_text()) if settings.is_file() else {}
    reference = json.loads(args.reference.read_text()) if args.reference else None
    closure, lookup_candidates = (closure_paths(reference, metadata.get("Version"))
                                  if reference else (None, None))
    report = audit(sdk, installation, resource, closure, lookup_candidates,
                   decision_rules(args.decisions))
    if reference:
        report["reference"] = {
            "sdk": reference.get("sdk", {}),
            "probe_sha256": reference["probe_sha256"],
            "target": reference["target"],
            "compiler": reference["compiler"],
            "compiler_binary_sha256": reference["compiler_binary_sha256"],
            "resource_headers_sha256": reference["resource_headers_sha256"],
        }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    if args.review_out:
        args.review_out.parent.mkdir(parents=True, exist_ok=True)
        args.review_out.write_text(review_markdown(report))
    counts = report["counts"]
    print(f"SDK {report['sdk'].get('Version', '?')}: "
          f"{counts['installed']} installed, {counts['missing']} absent; "
          f"{counts['compiler_resource_overlaps_among_missing']} compiler overlaps")
    print("Excluded:", ", ".join(f"{key}={value}"
                                for key, value in counts["excluded"].items()))
    print("Decisions:", ", ".join(f"{key}={value}"
                                for key, value in counts["decisions"].items()))
    for directory, values in sorted(report["by_directory"].items(),
                                    key=lambda item: (-item[1]["missing"], item[0]))[:20]:
        if values["missing"]:
            print(f"{directory}: {values['missing']} absent / "
                  f"{values['installed']} installed")
    print(f"Full path report: {args.out}")
    if args.require_decisions and counts["decisions"].get("review", 0):
        parser.exit(1, "unreviewed in-scope SDK headers remain\n")


if __name__ == "__main__":
    main()
