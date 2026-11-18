# SDK coverage audit

This is a read-only route for assessing the C installation against a specific
macOS SDK. `probe_c_closure.py` records the two-target transitive path closure
of a checked-in C fixture with the pinned LLVM Clang and its resource headers.
Its default `inputs/c-probe.c` is deliberately broad. For the shipping profile,
pass `--probe tests/c/default_profile.c` to both reference and generated runs.
`sdk_c_headers.py` inventories SDK paths and joins the checked-in decision
ledgers. It never copies SDK header contents into a recipe.
Set `LLVM_CLANG`, `SDK`, and `C_INSTALL` to absolute paths before running:

```sh
python3 probe_c_closure.py --probe tests/c/default_profile.c \
  --clang "$LLVM_CLANG" --sysroot "$SDK" \
  --out /tmp/minimal-reference-closure.json
python3 probe_c_closure.py --probe tests/c/default_profile.c \
  --clang "$LLVM_CLANG" --sysroot "$C_INSTALL" \
  --out /tmp/minimal-generated-closure.json
python3 audit_sdk_c_headers.py \
  --sdk "$SDK" --installation "$C_INSTALL" --clang "$LLVM_CLANG" \
  --reference /tmp/minimal-reference-closure.json \
  --generated-probe /tmp/minimal-generated-closure.json \
  --baseline inventories/macosx26.5.json \
  --out /tmp/macosx26.5-minimal-audit.json \
  --review-out /tmp/macosx26.5-minimal-review.md
```

`inputs/sdk-header-decisions.tsv` records path or glob, include/omit decision,
reason, evidence, reviewed SDK, and a digest of the approved matching path
set. `inputs/sdk-review-notes.tsv` records unresolved source gaps.
`inputs/sdk-scope-approvals.tsv` records approved out-of-scope path sets.
`inputs/installation-only-decisions.tsv` accounts for paths absent from the
reviewed SDK. `inventories/macosx26.5.json` is the historical full-profile
snapshot, useful as a path baseline but not a release approval for the
535-header profile.

The 2026-11-18 minimal fixture passed 350/350 probes against both official SDK
26.5 and our installation. The path inventory reported 531 matching installed
paths, 1,104 absent SDK paths, and 353 pending review statuses. Five paths
remain `missing_required` under the earlier path-closure policy:
`os/security_config.h`, `pthread/pthread.h`, `string_x86.h`, `tgmath.h`, and
`timingsafe.h`. The first, third, and fifth have old explicit include decisions
that need a minimal-scope review. Clang provides `tgmath.h` with a fallback C
implementation, but its Apple branch uses `include_next` when an SDK header is
present. `pthread/pthread.h` is an Apple OSS public header reached by the
official SDK closure; our selected `<pthread.h>` compiles without that nested
path. Do not silently approve either difference. The command succeeds as an
inventory; `--require-decisions` remains red until these paths and the pending
ledger are reviewed.
