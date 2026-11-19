# Darwin stack-probe symbols

The macOS 26.5 rule covers arm64 and x86_64 clients with deployment minima
from 11.0 through 26.5. It emits the global text symbol `____chkstk_darwin`
from `libsystem_pthread` and the renamed symbol reexport
`___chkstk_darwin` from `libcompiler_rt`. The receipt preserves the
destination image and spelling. The pthread source defines the entry point in
each architecture block. Its Xcode project compiles that assembly into the
`libsystem_pthread` dylib target.
[Assembly](https://github.com/apple-oss-distributions/libpthread/blob/1f4f5265b319111142f1bf3a27d4484ef5a98314/src/pthread_asm.s)
· [Dylib target](https://github.com/apple-oss-distributions/libpthread/blob/1f4f5265b319111142f1bf3a27d4484ef5a98314/libpthread.xcodeproj/project.pbxproj#L1077-L1095)
· [Sources phase](https://github.com/apple-oss-distributions/libpthread/blob/1f4f5265b319111142f1bf3a27d4484ef5a98314/libpthread.xcodeproj/project.pbxproj#L1525-L1544)

The Apple SDK for build 25F70 classifies both names as ordinary strong
exports in their respective components. The 25F84 arm64e and x86_64 runtime
export tries record a renamed reexport in compiler-rt and an ordinary
definition in pthread. Corentin approved recording that runtime role in the
candidate. The installed Apple Clang 21 emits the three-underscore spelling
on arm64 and the four-underscore spelling on x86_64 at minima 11.0 and 26.5.
The pinned upstream Clang 23.1.2 does not emit either spelling from the same
dynamic stack-allocation source. Public Apple linker source describes
renamed reexports, and a scratch link with Apple ld reproduced the export
trie record. The shipping compiler-rt packaging rule and pre-11 macOS
linker directives remain unverified.
[Alias handling](https://github.com/apple-oss-distributions/ld64/blob/f60a74eaa2c99585de1dc0f2820e7a9f8aaf522c/src/ld/OutputFile.cpp#L4279-L4290)

Reopen the decision if the source pins, reference role, observed cache
identity or runtime role, or either client link changes. Use the approved
reference SDK and host cache, the verified LLVM bundle, the materialized
libpthread checkout, and a generated candidate. Use a fresh output directory
outside the package.

```sh
python3 -m tools.libsystem.qualify_stack_probe \
  --llvm "$LLVM" --source "$LIBPTHREAD_SOURCE" \
  --reference "$APPLE_SDK" --candidate "$CANDIDATE" \
  --inspector /usr/bin/dyld_info --arm64-cache "$ARM64E_CACHE" \
  --x86-64-cache "$X86_64_CACHE" --out "$WORK"
```

The qualifier checks raw TBD roles separately from linking and retains the
selected cache export records and paired linker receipts for both targets at
11.0 and 26.5. Each link checks both strong references, their two-level
libSystem binding, the binder import, and Mach-O dependency and build
versions. The link fixture uses C declarations to request the exact Mach-O
spellings and is never executed. The Apple SDK and installed caches are
qualification inputs. Generation uses the reviewed source facts and approved
runtime record.

Against the preceding candidate, the same strict link failed on both
spellings on each architecture at 11.0. With the rule, all four reference
and candidate pairs match. Changing the candidate alias to an ordinary export
triggers the raw role check. Changing the candidate umbrella version to
1357 triggers the paired link check even though both names still resolve.
