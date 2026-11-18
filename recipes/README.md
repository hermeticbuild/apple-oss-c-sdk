# Header recipes

`install_c.py` orchestrates producers and writes an empty installation. The
public path set lives in `recipes/default-headers.txt`; `copies.tsv`
is the resolved, explicit selection of directly copied Apple OSS files. Its
columns are `install_path`, `source`, and `selection`. Every source is a path
inside a pinned submodule. The producer is the source repository name.
The Libc recipe lists the selected transformed headers in
`libc/strip-headers.txt`.

Generated files have code beside their owning source family:

- `libc/headers.py`: Apple public list, region stripping, feature flags, unifdef.
- `xnu/headers.py` and `xnu/mig.py`: public lists, macOS unifdef, symbol aliases, and two-target user MIG.
- `libm/headers.py`: guarded arm64 math and fenv derivations.
- `availability_versions/headers.py`: Apple's template preprocessor and xros alias.
- `compat/headers.py`: guarded CarbonHeaders, Libinfo, and dyld derivations.

`assembly.py` rejects an unselected path, missing pinned input, duplicate
owner, or incomplete profile. MIG alone needs the already selected headers as
its sysroot, so assembly writes a private pre-MIG tree before the final tree.
That bootstrap tree is discarded. In the final installation, `header-owners.json`
maps each path to one producer, its direct pinned source inputs, source selection,
and transformation. `header-provenance.json` preserves the audit's hash schema.
The two manifests are generated from the same in-memory header records.
MIG's transitive `.defs` includes, the selected compiler, and the host MIG
binary are action inputs, but are not enumerated per header in this index.

The 535-path profile, not the broad set of source headers, controls what ships.
Adding a header requires a source or derivation, an explicit copy selection if
applicable, the profile path, and a C fixture or consumer proving need.
