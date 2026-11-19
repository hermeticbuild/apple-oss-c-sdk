"""Version-specific decisions for C declarations without a macOS link provider."""

import json
import hashlib
from pathlib import Path
import re

from .emit import ARCHES


def policy_for(sdk):
    if not re.fullmatch(r"macosx[0-9]+(?:\.[0-9]+){1,2}", sdk):
        return None
    path = Path(__file__).parent / "data" / sdk / "expected-undefined.json"
    if not path.exists():
        return None
    policy = json.loads(path.read_bytes())
    names = policy["symbols"]
    if (policy["sdk"] != sdk or policy["architectures"] != list(ARCHES) or not names
            or names != sorted(set(names)) or not all(re.fullmatch(r"_\w+", name) for name in names)):
        raise ValueError(f"invalid expected-undefined policy for {sdk}")
    return policy


def verify_header(policy, root, manifest):
    receipt = manifest[policy["header"]]
    lock = json.loads((root / "source-lock.json").read_bytes())
    if (lock["sdk"]["canonical_name"] != policy["sdk"]
            or lock["sdk"]["reference_build"] != policy["reference_build"]
            or lock["projects"]["Libc"]["commit"] != policy["libc_commit"]
            or receipt["owner"] != "Libc" or receipt["sha256"] != policy["header_sha256"]
            or hashlib.sha256((root / policy["header"]).read_bytes()).hexdigest() != policy["header_sha256"]):
        raise ValueError("reopen expected-undefined decision: unistd.h or its source lock changed")


def filter_demands(policy, images, inventories):
    excluded = set(policy["symbols"])
    for image in images:
        for arch, part in image["slices"].items():
            conflicts = excluded.intersection(part["exports"]) | excluded.intersection(part.get("symbol_reexports", {}))
            if conflicts:
                raise ValueError(f"reopen expected-undefined decision: {image['install_name']} "
                                 f"exports {sorted(conflicts)} on {arch}")
    filtered = {}
    for arch, rows in inventories.items():
        kept = []
        for row in rows:
            if row["symbol"] not in excluded:
                kept.append(row)
            elif row["header"] != policy["header"] or row["kind"] != "function":
                raise ValueError(f"reopen expected-undefined decision: new declaration of {row['symbol']}")
        filtered[arch] = kept
    return filtered
