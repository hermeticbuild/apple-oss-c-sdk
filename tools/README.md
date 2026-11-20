# Maintainer tools

The root Makefile and `recipes/` generate the C installation. They take
Clang as an input. These tools help prepare that input, check the resulting
tree, or review what to ship.

| Workflow | Who runs it and when |
| --- | --- |
| [Prepare locked sources](../locks/README.md) | An installer preparing the selected version's Apple OSS checkouts |
| [Resolve pinned Clang](toolchain/README.md) | An installer or maintainer preparing Clang for Make or the C probes |
| [Check the C installation](qualify_headers/README.md) | A maintainer after changing a recipe or a probe |
| [Review SDK coverage](sdk_review/README.md) | A maintainer or agent qualifying a new SDK, updating source pins, or investigating a header gap |
| [Compose an SDK](sdk_composition/README.md) | A maintainer assembling a sysroot from generated headers and separate link assets |
| [Build LLVM against a test SDK](llvm_build/README.md) | A maintainer after changes affecting cross-compilation or SDK composition |
| [Run the tests](../tests/README.md) | A contributor validating a generated C installation with `make test` |

`header_manifest.py` is the shared manifest reader used by SDK review, LLVM
composition, and the merge tests. It accepts the installer's TSV format and
the JSON format used by archived installations.
