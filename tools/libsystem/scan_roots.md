# Scan public C roots by architecture and profile

Generate a standalone census for the same C installation and deployment
minimum, then pass its receipt to the offline root scanner. Use the
[verified LLVM projection](../toolchain/README.md). Run from the repository
root.

```sh
python3 -m tools.qualify_headers.census \
  --c-install "$C_INSTALL" --clang "$LLVM/bin/clang" \
  --minimum 11.0 --out "$CENSUS" --report-only
python3 -m tools.libsystem.scan_roots \
  --llvm "$LLVM" --c-install "$C_INSTALL" --census "$CENSUS" --work "$WORK"
```

The default uses every census path on arm64 and x86_64 under the default and
Darwin C profiles. Restrict a run with repeated `--header`, `--arch`, or
`--profile` options. A census can itself name a smaller set of public roots.
The plan requires a matching census row for each selected architecture and
path. A successful census proves the include context. The scanner still checks
that each selected C profile reaches the requested header.

The work directory stores a verified input identity, one deterministic gzip
checkpoint per root, and a summary with architectures, profiles, observed
Mach-O imports, statuses, and checkpoint digests. Each result retains the
complete census row, scanner declarations and relocation evidence, or the
reason the scope could not be scanned. A successful root can still have
unresolved imports. Census failures and contexts requiring preprocessing as
assembly, pre-includes, or macros unavailable in the scan profile remain
explicit findings. Use a new work directory after changing a pinned input or
to retry a completed failing root.

Checkpoints publish atomically. Run the same command again after interruption
to continue with matching inputs. Roots are scanned serially. A root's
temporary objects are discarded after its checkpoint is assembled, so the
aggregate does not need to retain an object tree. Use
`tools.libsystem.scan --objects` for a direct root when you need to inspect the
original objects. The aggregate includes their SHA-256 digests and relocation
observations from the scan. A hard interruption can leave disposable
`.root-*` or `.checkpoint-*` scratch directories in the selected work
directory.

An exit status of 1 indicates the scan finished with findings. The
`--report-only` option returns success for that completed report with the same
findings. Invalid or stale inputs and checkpoint failures exit 2. This is a
header-derived demand inventory. Component ownership, unscanned roots and
non-header demand still need separate evidence.
