"""Compare selected C imports with dyld's simulator host-library name tables."""

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re

from .scan import dump_json


SOURCE_PATH = "cache_builder/mrm_shared_cache_builder.cpp"
SOURCE_REVISION = "fd8d0c4d52320ebf64db34f3cb280310d905c5ae"
SOURCE_SHA256 = "950a30ec55f962d6661e20080988d5574613783fe16719cc6f02cd82655a2ba4"
ARRAYS = {
    "libKernelExports": "/usr/lib/system/libsystem_kernel.dylib",
    "libPthreadExports": "/usr/lib/system/libsystem_pthread.dylib",
    "libPlatformExports": "/usr/lib/system/libsystem_platform.dylib",
}
OBSERVED_ARCHES = {"arm64": ("arm64", "arm64e"), "x86_64": ("x86_64",)}


def source_providers(source):
    source_bytes = source.read_bytes()
    if hashlib.sha256(source_bytes).hexdigest() != SOURCE_SHA256:
        raise ValueError(f"dyld source SHA-256 mismatch: {source}")

    owners = defaultdict(set)
    counts = {}
    text = source_bytes.decode()
    for name, provider in ARRAYS.items():
        blocks = re.findall(r"^static const char\* const " + name + r"\[\] = \{\n(.*?)^\};$",
                            text, re.MULTILINE | re.DOTALL)
        if len(blocks) != 1:
            raise ValueError(f"expected one dyld array named {name}")
        symbols = set()
        for line in blocks[0].splitlines():
            entry = re.fullmatch(r'\s*"([A-Za-z0-9_$]+)"\s*,?\s*(?://.*)?', line)
            if not entry or entry[1] in symbols:
                raise ValueError(f"unexpected or duplicate dyld array entry in {name}: {line}")
            symbols.add(entry[1])
            owners[entry[1]].add(provider)
        if not symbols:
            raise ValueError(f"empty dyld array: {name}")
        counts[provider] = {"array": name, "names": len(symbols)}
    return owners, counts


def compare(listed, definitions, runtime_status):
    if listed:
        if not definitions:
            return "missing-runtime-definition"
        if listed != definitions:
            return "provider-disagreement"
        if len(definitions) != 1 or runtime_status != "unique-definition":
            return "ambiguous-runtime-definition"
        return "provider-match"
    if definitions.intersection(ARRAYS.values()):
        return "missing-dyld-name"
    return "outside-dyld-coverage" if definitions else "unresolved-outside-dyld-coverage"


def audit(arch, path, owners):
    report_bytes = path.read_bytes()
    report = json.loads(report_bytes)
    if (report["schema"] != 1 or report["client_arch"] != arch or
            report["observed_arch"] not in OBSERVED_ARCHES[arch] or not report["scans"]):
        raise ValueError(f"unexpected provider report or architecture: {path}")
    rows = {}
    excluded = []
    seen = set()
    for row in report["symbols"]:
        symbol = row["symbol"]
        if symbol in seen:
            raise ValueError(f"duplicate provider report symbol: {symbol}")
        seen.add(symbol)
        headers = sorted({header for _, header in row["client_declarations"]
                          if header.startswith("usr/include/")})
        if not headers:
            excluded.append(symbol)
            continue
        definitions = {match["image"] for match in row["matches"] if match["role"] == "definition"}
        listed = owners.get(symbol, set())
        rows[symbol] = {
            "headers": headers,
            "dyld_providers": sorted(listed),
            "runtime_definitions": sorted(definitions),
            "runtime_status": row["status"],
            "comparison": compare(listed, definitions, row["status"]),
        }
    return {
        "providers_sha256": hashlib.sha256(report_bytes).hexdigest(),
        "observed_arch": report["observed_arch"],
        "selected_header_names": len(rows),
        "excluded_non_header_names": sorted(excluded),
        "counts": dict(Counter(row["comparison"] for row in rows.values())),
        "symbols": rows,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--arm64", type=Path, required=True)
    parser.add_argument("--x86-64", type=Path, required=True)
    args = parser.parse_args()
    try:
        owners, arrays = source_providers(args.source)
        targets = {arch: audit(arch, getattr(args, arch), owners) for arch in OBSERVED_ARCHES}
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(1, f"dyld provider evidence: {exc}\n")
    print(dump_json({
        "schema": 1,
        "source": {"repository": "apple-oss-distributions/dyld", "revision": SOURCE_REVISION,
                   "path": SOURCE_PATH, "sha256": SOURCE_SHA256},
        "arrays": arrays,
        "targets": targets,
    }), end="")


if __name__ == "__main__":
    main()
