# dyld simulator host-library provider evidence

The pinned macOS 26.5 dyld source maps `libKernelExports`, `libPthreadExports`,
and `libPlatformExports` to their `/usr/lib/system/` install names. The cache
builder uses those arrays to synthesize stand-ins for host dylibs that are
patched into the simulator cache at runtime. It passes the same name arrays
to the synthesizer independently of target architecture and marks each
placeholder atom as a function. The arrays provide supplemental ownership
evidence. Public eligibility, symbol kind, and availability on each
architecture need independent evidence. [Export mapping and synthesis](https://github.com/apple-oss-distributions/dyld/blob/fd8d0c4d52320ebf64db34f3cb280310d905c5ae/cache_builder/mrm_shared_cache_builder.cpp#L2535-L2625)
· [Simulator build condition](https://github.com/apple-oss-distributions/dyld/blob/fd8d0c4d52320ebf64db34f3cb280310d905c5ae/cache_builder/mrm_shared_cache_builder.cpp#L2643-L2653)

Generate the comparison from the pinned dyld checkout and the existing
provider reports. The audit checks the source digest, considers only names
selected by a C header scan, and compares the per-name array lookup with
independent runtime definitions. It preserves source and report digests and
leaves disagreements open.

```sh
python3 -m tools.libsystem.dyld_provider_evidence \
  --source "$DYLD_SOURCE/cache_builder/mrm_shared_cache_builder.cpp" \
  --arm64 "$ARM64_PROVIDERS_JSON" --x86-64 "$X86_64_PROVIDERS_JSON" \
  > dyld-provider-evidence.json
```

## macOS 26.5 sample

The default-profile sample at deployment minimum 11.0 uses `math.h`,
`stdio.h`, `sys/stat.h`, and `unistd.h`. The runtime observations come from
macOS 26.5.2 build 25F84, using the arm64e and x86_64 slices. The arrays
contain 1,551 kernel, 134 pthread, and 85 platform names.

| Comparison | arm64 client | x86_64 client |
| --- | ---: | ---: |
| Header-selected names | 481 | 498 |
| Kernel provider matches | 109 | 112 |
| Pthread or platform provider matches | 0 | 0 |
| Observed provider covered by dyld with name missing | 0 | 0 |
| Dyld name with no observed runtime definition | 0 | 0 |
| Provider disagreement | 0 | 0 |
| Observed definition outside the three components | 368 | 383 |
| Unresolved outside the arrays | 4 | 3 |

`_add_profil`, `_profil`, and `_unwhiteout` remain unresolved on both clients,
and `___fpclassify` remains unresolved on arm64 in this input. The linker-only
`dyld_stub_binder` demand is excluded from the header comparison. The sample
carries no independently selected pthread or platform provider observations.
