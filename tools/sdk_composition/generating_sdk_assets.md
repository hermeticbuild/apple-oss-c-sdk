# Generating macOS SDK assets without the Xcode SDK

The [libSystem implementation specification](libsystem-spec.md) records the
current toolchain choice, evidence policy and qualification gate. The framework
sections below document research for a later project. The planned libSystem
milestone uses frameworks supplied by Apple SDK Gen.

Use this recipe when qualifying a new macOS version or resolving an API coverage
gap. It covers the public C surface of `libSystem` and the C and Objective-C
surfaces of frameworks for `arm64` and `x86_64`. Clang resource headers and the
C++ toolchain come from pinned LLVM. See [source locks](../../locks/README.md)
for the Apple OSS inputs.

The C install and its tests have working commands. The inventory join, framework
installation, and release TBD emission below describe the proposed production
recipe. The [current composition tool](README.md) still uses SDK Gen assets for
qualification.

## Inputs and outputs

| Input to lock | What it establishes |
| --- | --- |
| Apple OSS commit, project, public install rule and file license | Which source files and declarations the upstream project publishes |
| Framework or library documentation URL, language variant, content digest and reviewed ABI facts | Evidence for public APIs and declarations with source gaps |
| macOS product version, build, runtime image UUID and architecture | Install names, reexports, symbol spellings, and linkage on the observed build |
| Clang and linker revisions, target triple, deployment minimum, language and feature macros | How a client sees and references the interface |

Keep one record per public declaration and target configuration. Give each record
a public include path, declaration kind, source revision or URL, and availability
when known. For external symbols, also record the Mach-O spelling, provider
install name, reexport path when applicable, and weak or thread-local flags.
The declaration and the external symbol can have different sources of evidence.
Keep unresolved source, layout, export, and availability questions in a coverage
report. This makes it possible to audit coverage independently of what LLVM and
`rules_rs` happen to compile.

The release outputs are the C tree and its existing header manifest,
`usr/lib/*.tbd` plus required component stubs, selected public framework trees
under `System/Library/Frameworks`, and the API provenance and license bundle.
Sort records by interface, target and symbol, and normalize archive metadata.
The release build consumes pinned source and reviewed records offline. A
documentation refresh or runtime capture is a distinct maintenance operation.

## 1. The C and libSystem surface

**Input.** Start from the pinned macOS distribution and the installed outputs
of its Apple OSS public-header rules. Add the exact same distribution's
`Libsystem` pin for the umbrella recipes. The
[macOS 26.5 manifest](https://raw.githubusercontent.com/apple-oss-distributions/distribution-macOS/macos-265/release.json)
selects `Libsystem-1356`, commit `c23b51183e46e613375dc7639fb4bf11fbf59ba8`.
Apple's [linker script](https://raw.githubusercontent.com/apple-oss-distributions/Libsystem/Libsystem-1356/xcodescripts/linker_arguments.sh)
uses `requiredlibs` and `optionallibs` to select components, then emits reexport
flags based on the files and architecture slices present in its own build.
Use the lists and rules as evidence, and the installed runtime to see which
choices were made on the sampled OS. The source release omits some listed
components, including XPC and corecrypto.

**Install.** Run these existing commands from the repository root with
`LLVM_REPO` pointing to the hermetic-llvm checkout. The install uses the current
macOS bootstrap tools, including system MIG.

```sh
SDK=macosx26.5
WORK=$(mktemp -d)
C_INSTALL="$WORK/c-install"
LLVM_CLANG=$(python3 -m tools.toolchain.resolve_clang --llvm-repo "$LLVM_REPO")
RESOURCE_DIR=$("$LLVM_CLANG" -print-resource-dir)

python3 -m tools.sources.locked_sources prepare --sdk "$SDK"
make install SDK="$SDK" CLANG="$LLVM_CLANG" OUT="$C_INSTALL"
make test SDK="$SDK" CLANG="$LLVM_CLANG" OUT="$C_INSTALL"
```

**Inventory.** Parse public entry headers, with their include prerequisites, for
each supported target and feature profile. For a first inventory, use Darwin C
and an explicit POSIX profile such as C17 with `_POSIX_C_SOURCE=200809L`.
Keep each profile's results distinct. Use header ownership from
`header-manifest.tsv` and supplement it with upstream public install rules where
an installed path is a transitive dependency. Supplement with source man pages
such as Libc's `stdio/FreeBSD/printf.3` and libpthread's `man/pthread_create.3`.
On the sampled Mac, ordinary `man -w 3 printf` found the man page inside
Xcode's SDK. Use pinned OSS files or
[Apple's public man-page archive](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man3/printf.3.html).

```sh
unset CPATH C_INCLUDE_PATH OBJC_INCLUDE_PATH CPLUS_INCLUDE_PATH SDKROOT
printf '%s\n' '#include <sys/stat.h>' \
  'int probe(const char *p, struct stat *s) { return stat(p, s); }' \
  >"$WORK/stat-probe.c"

for target in arm64 x86_64; do
  "$LLVM_CLANG" --target="$target-apple-macos26.5" \
    -isysroot "$C_INSTALL" -nostdinc \
    -isystem "$RESOURCE_DIR/include" -isystem "$C_INSTALL/usr/include" \
    -std=c11 -extract-api -x c-header "$C_INSTALL/usr/include/sys/stat.h" \
    -o "$WORK/stat-$target.symbols.json"

  "$LLVM_CLANG" --target="$target-apple-macos26.5" \
    -isysroot "$C_INSTALL" -nostdinc \
    -isystem "$RESOURCE_DIR/include" -isystem "$C_INSTALL/usr/include" \
    -O0 -c -H "$WORK/stat-probe.c" -o "$WORK/stat-$target.o" \
    2>"$WORK/stat-$target.includes"
  "${LLVM_CLANG%/*}/llvm-nm" -um "$WORK/stat-$target.o"
done
```

`-extract-api` inventories source declarations. Clang's
`-fsyntax-only -Xclang -ast-dump=json` on the probe also displays the
`FunctionDecl.mangledName` and the declaration's `AsmLabelAttr`. The
`-c` invocation and `llvm-nm -um` show the actual undefined Mach-O symbol the
client emitted. The same C declaration identifier produces `_stat` on
arm64 and `_stat$INODE64` on x86_64. The include trace resolves `sys/stat.h`
and its dependencies through the standalone tree and pinned compiler resources.
For broader coverage, start with pinned Clang's JSON AST and verify eligibility
and ABI names as described below. Use a preprocessor pass with source
locations to inventory public macros absent from a symbol graph.
[LLVM InstallAPI](https://clang.llvm.org/doxygen/namespaceclang_1_1installapi.html) ·
[llvm-nm reference](https://llvm.org/docs/CommandGuide/llvm-nm.html)

For an automated reference probe, parse the AST of a translation unit that
includes the public roots. Walk into their includes while keeping each
declaration's source header. ExtractAPI on `stdio.h` alone returned an empty
graph in the prototype because the declarations are in `_stdio.h`.
Generate a retained, typed address reference for each eligible function or
extern object, then collect undefined symbols from the resulting Mach-O
objects. A pilot generated these references from `stdio.h` and `sys/stat.h`
without a hand-written function list. It compiled 122 references on arm64 and
128 on x86_64, including the target-specific `stat` references and stdio data.
Group compatible headers and keep target and feature profiles separate.
Qualify the other declaration kinds through type, layout or value checks.

**Verify exports and emit.** The following commands read installed runtime
images. The sampled inspection executable is from Xcode. The commands read
Mach-O data from macOS instead of loading a `.sdk` tree. For an independently
packaged capture tool, Apple publishes its
[dyld_info source](https://github.com/apple-oss-distributions/dyld/blob/fd8d0c4d52320ebf64db34f3cb280310d905c5ae/other-tools/dyld_info.cpp).
Building a separately pinned inspector is outside this recipe's verified commands.

```sh
sw_vers
DYLD_INFO=$(xcrun --find dyld_info)
X86_CACHE=/System/Cryptexes/OS/System/Library/dyld/dyld_shared_cache_x86_64
SYSTEM=/usr/lib/libSystem.B.dylib
KERNEL=/usr/lib/system/libsystem_kernel.dylib

"$DYLD_INFO" -arch arm64e -uuid -load_commands "$SYSTEM" >"$WORK/libSystem-arm64e.txt"
"$DYLD_INFO" -arch x86_64 -dyld_cache_path "$X86_CACHE" -uuid -load_commands \
  "$SYSTEM" >"$WORK/libSystem-x86_64.txt"
"$DYLD_INFO" -arch arm64 -exports "$KERNEL" >"$WORK/libsystem_kernel-arm64.txt"
"$DYLD_INFO" -arch x86_64 -dyld_cache_path "$X86_CACHE" -exports \
  "$KERNEL" >"$WORK/libsystem_kernel-x86_64.txt"
```

The x86_64 cache path is from this Rosetta installation. Prefer an exact
runtime slice where available. Record arm64e as the observed slice when it
provides evidence for an arm64 client and qualify that pairing with an actual
arm64 client. Both `stat` spellings above matched the corresponding runtime
slices. Keep the captured build and availability separate. Qualifying older
deployment targets requires its own source annotations or runtime evidence.

Join the ABI names against the matching component image and follow its
reexports. Use public evidence for what to expose, and keep unmatched or
ambiguous rows visible in the coverage report. Derive linker-required symbols
without a C declaration from the pinned toolchain's link behavior and qualify
them separately. Emit `usr/lib/libSystem.B.tbd`, a `usr/lib/libSystem.tbd` alias
for `-lSystem`, and any component TBDs referenced by the umbrella. Give every
document the observed dylib install name. Write target-specific export
sections, preserving reexports, weak definitions, and thread-local symbols
where the evidence establishes them.
[LLVM's TBD format and reader](https://llvm.org/doxygen/TextStub_8cpp_source.html)

Keep the client's weak import flag separate from the provider's weak
definition flag. `llvm-nm -um` shows the former on a client object. The
provider image's export trie supplies the latter, thread-local kind and
symbol-level forwarding. Whole-library reexports come from
`LC_REEXPORT_DYLIB`. For the `stat` probe, `libsystem_kernel` supplies the
symbols and `libSystem.B.dylib` reexports that component. After linking
against a small stub graph with those two images and `libdyld`, the command
`llvm-objdump --macho --dyld-info` showed both client imports binding through
`libSystem`. The arm64 and x86_64 programs both ran on macOS 26.5.2.
[Apple's Mach-O export flags](https://raw.githubusercontent.com/apple-oss-distributions/xnu/xnu-12377.121.6/EXTERNAL_HEADERS/mach-o/loader.h) ·
[llvm-objdump reference](https://llvm.org/docs/CommandGuide/llvm-objdump.html)

Track compiler-generated imports separately. Use the pinned compiler's
runtime libcall definitions to discover candidates. Compile code-generation
fixtures for operations such as complex division and 128-bit division, and
inspect their objects with `llvm-nm -um`. Compare those imports with defined
symbols from the actual runtime archive passed by the toolchain and exports
from the system component images. Inspect the actual link arguments and
bindings to verify which provider is selected. The LLVM 23.1.2 probe emitted
`___divdc3` and `___divsc3` on both targets. macOS 26.5.2's system
`libcompiler_rt` exported those names on x86_64. Its arm64e image lacked them.
[LLVM runtime libcalls](https://github.com/llvm/llvm-project/blob/llvmorg-23.1.2/llvm/include/llvm/IR/RuntimeLibcalls.td)

Treat parity with the Apple SDK as a comparison of target-specific symbols,
flags, reexports, and linker directives. The local Xcode 26.5
`libSystem.B.tbd` contains 371 distinct `$ld$` directives across the macOS
groups, including rules for older deployment targets. These records require
independent SDK policy evidence. Address probes supply client imports, and
the runtime export trie supplies facts about the observed OS build.
[LLD handling of linker directives](https://github.com/llvm/llvm-project/blob/llvmorg-23.1.2/lld/MachO/InputFiles.cpp)

### Header gap baseline before TBD generation

Start with a dated audit of the exact C installation, compiler resource tree
and reference SDK. Hash those inputs. Join the install manifest, the SDK path
decisions, the reference probe closure, isolated include results, and known
semantic differences. A header can be present and still declare the wrong type
or hide a public declaration. A missing path can also have a working compiler
provider. Preserve these as distinct observations. Group shared causes under a
single repair with all affected paths and targets. Give each in-scope failure
a reproducible invocation, expected result and disposition. Rerun the same
invocation after each fix. An unresolved public dependency needs an explicit
decision before relying on the symbol inventory it affects.

The 26.5 snapshot had 765 manifest paths. Under C17, default feature macros
and deployment target 26.5, 730 direct includes passed on arm64 and 728 on
x86_64. The following groups account for all 38 distinct paths that failed on
either architecture in that sweep. These are diagnostic groups. Some still
need their intended context verified.

| Diagnostic or context to check | Installed paths, relative to `usr/include` |
| --- | --- |
| Dispatch umbrella required | `dispatch/{base,block,data,group,io,object,once,queue,semaphore,source,time,workloop}.h` |
| Other umbrella or internal include | `netinet6/in6.h`, `os/workgroup_{base,interval,object,parallel}.h`, `secure/_{stdio,string,strings}.h`, `sys/_{posix_availability,symbol_aliasing}.h` |
| Swift overlay or feature profile | `dispatch/dispatch_swift_shims.h`, `ucontext.h` (verified with `_XOPEN_SOURCE=700`) |
| Architecture or assembler context | `architecture/alignment.h`, `architecture/arm/{asm_help,cframe,reg_help}.h`, `architecture/i386/pio.h`, `mach/arm/syscall_sw.h` |
| Prerequisite types or macros to verify | `mach/doubleagent_types.h`, `mpool.h`, `protocols/{routed,timed}.h` |
| Kernel dependency to review for userspace scope | `sys/dtrace_impl.h`, `sys/ubc.h` |
| Confirmed generated-install gap | `mach/machine/asm.h` fails even with `-x assembler-with-cpp -E`. The reference succeeds. XNU's `osfmk/mach/{arm64,i386}/Makefile` lists `asm.h` in each `INSTALL_MD_GEN_LIST`. Both installed architecture paths are missing. |
| Missing dependency in both trees | `mach/mach_eventlink.h` includes `mach/mach_eventlink_types.h`. The pinned XNU file fixes the include in a diagnostic overlay. Its upstream install list is private. Public scope requires a decision. |

The separate 26.5 path audit reported four required but missing paths.
`string_x86.h`, `timingsafe.h` and `os/security_config.h` already have
include decisions. Reconcile those decisions with the recipe output.
`tgmath.h` exists in the pinned Clang resource tree. A C17
`_Generic(sqrt(1.0f), float: 1, default: 0)` assertion passed on both targets
at macOS 11 using that provider. Record compiler ownership and qualify the
required interface before deciding whether an SDK-side path is necessary.
The audit also had 132 paths pending a disposition. Regenerate these counts
against the chosen release snapshot. The include sweep covers installed
paths, while the path audit can find public entry points absent altogether.
Include the declaration and ABI review for paths present in both trees.

### One stub and multiple deployment targets

Use the SDK release to select the source lock and the client deployment
minimum to configure each independent compile and link. Ship one
`libSystem.tbd` entry point per SDK release. Preserve per-architecture
exports, component reexports and independently evidenced target-dependent
directives. Blindly unioning spellings from different probe configurations
loses information. Check availability and weak imports in client objects
alongside the behavior of the linker for each relevant minimum.

For Xcode 26.5 Apple publishes macOS 11 through 26.5 as deployment targets.
The local SDK's `SupportedTargets.macosx` has a minimum of 10.13, a
recommended target of 11.0 and a default of 26.5. Use the published range
as the proposed qualification scope. Investigate older Intel compatibility
separately if required. Test both ends and both sides of independently
identified behavior changes. Record which older systems actually ran a binary.
The existing macOS 14 probe is one sample. [Apple's Xcode support table](https://developer.apple.com/xcode/system-requirements/)

A small linker fixture uses a v4 TBD with targets `arm64-macos` and
`x86_64-macos` exports `_available` with the synthetic directive
`$ld$hide$os11.0$_available`. Compile a client that calls `available()`.
Link using pinned `ld64.lld -arch "$ARCH" -platform_version macos "$MIN" 26.5
-dylib client.o libExample.tbd -fixup_chains -o client.dylib`. The identical
stub produced an undefined-symbol diagnostic at 11.0 and a successful link
at 12.0 on both architectures. This experiment exercises one LLD directive.
The 371 distinct directives observed in the reference survey carry version
selectors ranging from 10.4 through 10.14.
Keep historical differences visible in local comparisons.

### Tool choices and repeatable investigations

| Operation | Initial tool choice and evidence to retain |
| --- | --- |
| Enumerate declarations | Pinned minimal Clang with `-fsyntax-only -Xclang -ast-dump=json` on a translation unit including a public root. Preserve physical declaration header, root, target, minimum and feature flags. Normalize redeclarations and macro locations. The JSON format can change on a compiler upgrade. |
| Decide which references to generate | Use LLVM InstallAPI's visibility, redeclaration and C inline rules as a reference. Exercise ambiguous cases in focused fixtures. The pilot's 122/128 imports each include one false candidate: taking the address of inline `__sputc` emits `___sputc`, whereas a public `putc_unlocked` call emits `___swbuf` at both optimization levels tested. Use an accessor to take the address of external TLS at runtime. |
| Identify provider and verify binding | Inspect relocations with `llvm-objdump` and undefined imports with `llvm-nm`. Join a spelling to a target-specific export and a reachable reexport path. Retain header owner, defining image and client bind-through image separately. For instance, `getgroups` can resolve to `libsystem_kernel` or `libsystem_c` depending on the feature profile. |
| Find compiler-generated dependencies | Compile fixtures with the pinned compiler. For release qualification obtain the target builtins archive from hermetic-llvm's macOS link action, inspect it with `llvm-nm`, and inspect the final linked image. The toolchain's `//toolchain/args/macos:default_libs` explicitly passes `-lSystem` and `//runtimes/compiler-rt:clang_rt.builtins.static`. Record target, archive digest and link arguments. A separately pinned complete Clang distribution can provide an independent consumer test. |
| Investigate and approve gaps | An investigator should be able to reproduce one header in its intended context, trace one C name from declaration through relocation to image, and compare one candidate/reference link with the same object. Keep reference SDK diffs local. Record each difference as required repair, approved exclusion with evidence, or open question. Production consumes reviewed inputs offline. |

`clang-installapi` is a standalone LLVM tool. The pinned minimal package
does not ship it. A custom Clang C++ tool becomes worth considering if a
reproducible ambiguity in the pinned dump prevents correct attribution or
export classification. Neither extraction method establishes the provider
from the declaration alone. [LLVM's JSON dumper contract](https://github.com/llvm/llvm-project/blob/llvmorg-23.1.2/clang/include/clang/AST/JSONNodeDumper.h) ·
[LLVM's InstallAPI visitor](https://github.com/llvm/llvm-project/blob/llvmorg-23.1.2/clang/lib/InstallAPI/Visitor.cpp)

## 2. Frameworks with Apple OSS public headers

**Input.** Pin the framework source and inspect its public Headers phase or
install target. Start with
[Apple OSS CF](https://github.com/apple-oss-distributions/CF/tree/dc54c6bb1c1e5e0b9486c1d26dd5bef110b20bf3)
for CoreFoundation. This is the CF pin in the archived C prototype. The
[LLVM proof](../llvm_build/README.md) documents that prototype's header producer.
Apple OSS [Security](https://github.com/apple-oss-distributions/Security) and
[`configd`](https://github.com/apple-oss-distributions/configd) are independent
source leads for Security and SystemConfiguration. Inspect their target
membership and platform conditions before assigning them a coverage claim.
[Apple's public/private header phase documentation](https://developer.apple.com/documentation/xcode/customizing-the-build-phases-of-a-target)

**Generate.** Stage the chosen public headers under the framework's
`Headers/` directory. Preserve public include paths and dependencies and use
its source module map where available. A framework recipe can generate a
module map from reviewed umbrella and dependency rules where needed. Run the
same target-specific declaration extraction; set `FRAMEWORK_ROOT` to the
directory containing the staged `CoreFoundation.framework`.

```sh
for target in arm64 x86_64; do
  "$LLVM_CLANG" --target="$target-apple-macos26.5" \
    -isysroot "$C_INSTALL" -nostdinc \
    -isystem "$RESOURCE_DIR/include" -isystem "$C_INSTALL/usr/include" \
    -F "$FRAMEWORK_ROOT" -fblocks -extract-api -x c-header \
    "$FRAMEWORK_ROOT/CoreFoundation.framework/Headers/CFBase.h" \
    -o "$WORK/corefoundation-base-$target.symbols.json"
done
```

Use `-x objective-c-header` for an Objective-C interface and include its
language-specific dependencies. Record the framework install name from the
matching runtime image and verify exported functions and data, Objective-C
class symbols, and reexports as applicable. I verified that the extraction
above finds `CFRelease` in the OSS-derived `CFBase.h` on both targets. The
installed framework resolves it on both targets as well. Objective-C method
declarations belong in headers. Objective-C dispatch uses selectors, so
individual methods need no separate TBD entry.
The output is the staged framework header and module tree plus
`CoreFoundation.framework/CoreFoundation.tbd`. Link a consumer with
`-framework CoreFoundation` and exercise representative calls on both targets.

## 3. Frameworks and libraries with public source gaps

**Discover.** Apple's public DocC site has a
[technologies catalog](https://developer.apple.com/tutorials/data/documentation/technologies.json)
and per-module navigation JSON at
`https://developer.apple.com/tutorials/data/index/<module>`. The URL has no
`.json` suffix for the navigation index. Read `interfaceLanguages.occ` for
C and Objective-C entries. Preserve each published path as written, including
punctuation and parameter labels. Here are the verified indexes.

- [CoreFoundation](https://developer.apple.com/tutorials/data/index/corefoundation)
  contains `/documentation/corefoundation/cfrelease`.
- [AudioToolbox](https://developer.apple.com/tutorials/data/index/audiotoolbox)
  contains `/documentation/audiotoolbox/audioqueuebuffer` and its field pages.
- [XPC](https://developer.apple.com/tutorials/data/index/xpc) contains
  `/documentation/xpc/xpc_connection_create(_:_:)`. XPC has a DocC module and
  its native symbols live in `libxpc`.

```sh
DOCC=https://developer.apple.com/tutorials/data
curl -fsSL "$DOCC/index/audiotoolbox" -o "$WORK/audiotoolbox-index.json"
curl -fsSL "$DOCC/documentation/audiotoolbox/audioqueuebuffer.json" \
  -o "$WORK/audioqueuebuffer.json"
curl -fsSL "$DOCC/documentation/xpc/xpc_connection_create(_:_:).json" \
  -o "$WORK/xpc-connection-create.json"
```

Traverse the index's `children` recursively and deduplicate symbol paths.
Fetch data for those paths from `/tutorials/data<path>.json`. Use each render
node's kind, precise identifier, and language variants to deduplicate APIs
and distinguish symbols from articles and topic collections. Apply the
`variantOverrides` JSON patches with the `occ` trait before reading
declarations. The base `AudioQueueBuffer` page is Swift, and its C
representation comes from that override. Read availability per API rather
than inheriting the module's introduction date. The sample XPC page identifies
macOS 10.7 for `xpc_connection_create`; the CoreFoundation `CFRelease` page
lists macOS without an introduction version.
[DocC render-node variant handling](https://github.com/swiftlang/swift-docc/blob/main/Sources/SwiftDocC/Model/Rendering/RenderNode.swift)

**Review, then generate.** Select C and Objective-C APIs applicable to the
locked macOS release. For each missing header, use explicitly licensed sources
and samples when available. Otherwise record the ABI facts supported by the
references and independently render the declarations. A structure needs
ordered field types and evidence for size, alignment and offsets. A function
needs the exact signature, including calling convention or a block signature
where relevant. A documented structure or enum contributes header
declarations. A callable function or externally bound variable needs a
separate confirmed runtime symbol to appear in the TBD. Qualify layouts on
both architectures and use representative calls to test the bindings.
Track uncovered fields and APIs in the coverage report if the public evidence
ends. [Apple's AudioQueueBuffer reference](https://developer.apple.com/documentation/audiotoolbox/audioqueuebuffer.md)

A refresh of the live documentation should record the URLs, digests, and
approved facts before an offline rebuild. The website terms and macOS license
still matter for bulk acquisition and publication. Apply the project's
[distribution provenance rules](../../LICENSING.md) to decide which evidence
and generated files can enter a public archive.

## Qualify the same SDK that ships

With `SDK_ROOT` pointing to the candidate sysroot and `smoke.c` containing a
call to `puts`, the following links against the candidate's `libSystem` and
shows the dylib load command. Run the resulting binaries on a Mac with the
target OS and architecture. The link itself is also a Linux CI requirement
with the corresponding pinned host toolchain.

```sh
for target in arm64 x86_64; do
  "$LLVM_CLANG" --target="$target-apple-macos26.5" -fuse-ld=lld \
    -isysroot "$SDK_ROOT" -nostdinc \
    -isystem "$RESOURCE_DIR/include" -isystem "$SDK_ROOT/usr/include" \
    smoke.c -o "$WORK/smoke-$target" -Wl,-t
  "${LLVM_CLANG%/*}/llvm-objdump" --macho --dylibs-used "$WORK/smoke-$target"
done
```

On the test Mac, run `arch -arm64 "$WORK/smoke-arm64"` and
`arch -x86_64 "$WORK/smoke-x86_64"` on a host with those execution modes.
For the x86_64 run, record whether the host uses Rosetta or an Intel CPU.

On macOS 26.5.2, this passed with the standalone C installation and an
isolated three-stub example. A `libSystem.tbd` with install name
`/usr/lib/libSystem.B.dylib` reexported `libsystem_c` and `libdyld`. The child
stubs exposed `_puts` and `dyld_stub_binder`, respectively. The linker trace
showed only the generated stubs and the object. Both binaries loaded
`/usr/lib/libSystem.B.dylib` and printed the expected string, with x86_64
running under Rosetta. This result covers that smoke test on the Mac host.

For release qualification, compare reproducibly generated artifacts, check
the coverage report per library and framework, inspect the include and link
traces for any path outside the declared inputs, and exercise normal and weak
linking at the claimed deployment minimum. Run [the LLVM build](../llvm_build/README.md)
through Stage 2 and the macOS suites in hermetic-llvm
and rules_rs against the same candidate archive. Publish the tested target and
deployment matrix so coverage and runtime support can be assessed separately.
