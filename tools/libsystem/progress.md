# libSystem implementation journal

## Current handoff

Implementation started against the approved plan at `bb2ecc9`. The two-architecture fixture now builds and links from independently authored component evidence. Tool readiness and the macOS 26.5 production qualification are tracked separately. [Implementation sequence](../sdk_composition/libsystem-spec.md#implementation-sequence-and-evidence-required-to-advance)

## 2026-11-19 · Specification review · macOS 26.5 · arm64 and x86_64

- **Finding.** The official LLVM 23.1.2 Apple Silicon archive includes InstallAPI and tools for both client targets. Its builtins archive has an arm64 slice. The x86_64 reference link for the three tested division helpers succeeded with libSystem alone. A separate Intel static runtime remains conditional on an observed need. [Toolchain experiment](../sdk_composition/libsystem-spec.md#one-official-llvm-toolchain-for-generation)
- **Decisions.** Qualify the published 11–26.5 deployment range by differential linking and record the OS builds actually executed. Evidence-backed omissions and narrowly reviewed runtime provider facts are permitted. Frameworks come from Apple SDK Gen for this milestone. [Decision record](../sdk_composition/libsystem-spec.md#decisions-and-recommendation-for-review)
- **Workflow.** Deliver the tools before the full inventory. The agent must ask before departing from an upstream rule, weakening a gate, or taking any of the other decisions in the escalation table. The local skill must support a clean rebuild, SDK update and first baseline. [Escalation policy](../sdk_composition/libsystem-spec.md#when-the-agent-must-ask-corentin) · [Skill workflow](../sdk_composition/libsystem-spec.md#maintainer-and-agent-procedure)
- **Next action.** Review the plan, then implement the locked-toolchain capability check. The complete libSystem release gate is still unverified.

## 2026-11-19 · First runnable tools · arm64 and x86_64

- The official archive passed GitHub attestation and content verification. Its projected tools and complete resource headers ran a two-target capability check. The generated macOS headers reproduced the differing `stat` names. The scanner also observed the Darwin-extension spelling of `getgroups` on both architectures.
- The fixture producer builds twice with identical output, rejects a missing provider before installation, and links equivalent clients against an independently authored v4 reference. Both clients still linked when a child's install name moved from `/usr/lib/system/` to `/usr/lib/`, but the paired verifier correctly detected the changed binding.
- The first writer emitted the same reexported library in two target groups. The pinned LLVM v5 reader retained only the first group for that name. The writer now emits one reexport entry with its full target set. Re-run `make -C tools/libsystem check-interface LLVM="$LLVM"` to exercise the regression on both architectures.
- The codegen tool recorded complex division and 128-bit division imports at O0 and O2 for both targets. Paired reference links at minimum 11 used the official arm64 builtins and no static Intel archive. Local capture verified the kernel component's arm64e `_getgroups` export and the x86_64 umbrella's 39 reexports. These are diagnostic observations on the sampled host.
- No header waivers or production symbol rows were added. The component records used in the runnable build describe an authored fixture. A full 26.5 build still needs locked OSS component inputs, reviewed linkage facts, deployment-policy extraction, the full classified header backlog and consumer qualification.
- A fresh C installation built with the verified official LLVM bundle passed all 358 existing compile checks and the runtime floating-point environment probe. Its manifest SHA-256 is `edd27af7689efe140b8511d9d3d8911bc3473e1bda316287aa639481c85de7f8`. Two fixture builds with network and Xcode reads denied produced identical packages in distinct directories. The fixture TBD SHA-256 is `523e5d2af22adfa6f2192242cb26b8428a61552fa4cac670f0ee600f2446a071`.
- **Decision, 26.5 / 25F70.** Corentin approved classifying direct standalone inclusion of `mach/mach_eventlink.h` as a reference limitation when the accompanying diagnostic is the missing private `mach/mach_eventlink_types.h`. Both targets showed that failure under the same default C17 context at deployment minimum 11 in the candidate and reference. XNU's `osfmk/mach/Makefile` puts the prerequisite in `PRIVATE_DATAFILES`. This decision covers the include failure only. The scope and evidence for eventlink exports must still be reviewed. Reopen the decision if the header, diagnostic, reference SDK or intended context changes.

## 2026-11-19 · Header inventory and first repairs · macOS 26.5 / 25F70

- The initial manifest contained 765 headers. The census passed 1,454 of 1,530 direct include contexts. The shipping profile passed 350 of 350 probes on each side. The semantic comparison found 11 cases passing only in the reference on both targets. The joined review contained 3,474 paths, 211 with open findings and two approved eventlink contexts. These counts describe the installation **before** repairs. Read each finding's cause and evidence before treating it as a missing public API. [Backlog runner](../sdk_review/libsystem-headers.mk) · [Semantic fixtures](../sdk_review/fixtures/c_interfaces/)
- **Availability decision.** Corentin approved extending the public Apple DSL for macOS SDK 26.5. The pinned input ends at 14.3; the baseline advertised `140300` as its maximum even for the 26.5 installation. Stage the original DSL with the reviewed macOS version rows and run Apple's generator. Check the original DSL digest before staging; revisit this supplement when the pin or SDK changes. The two public outputs affected within this recipe are `AvailabilityVersions.h` and `AvailabilityInternal.h`. The SDK is used only for comparison. [Input and public release sources](../../recipes/availability_versions/macosx26.5.dsl) · [Targeted fixture](../../tests/installed_headers/macos_26_5_availability.c)
- **Mach dispatch header.** The census found one path passing only in the reference under the same standalone include context, `mach/machine/asm.h`. Follow XNU's architecture-specific public `INSTALL_MD_GEN_LIST` and its `VPATH` to install both child headers. The headers and the two sampled assembled objects matched the reference bytes. [XNU recipe](../../recipes/xnu/asm_headers.py)
- **Platform macros.** The local CarbonHeaders adaptation overrode Apple's `TARGET_OS_UNIX` value for macOS. Restoring the value in the upstream template fixed the platform-branch probe on both targets. The independently missing `TARGET_ABI_USES_IOS_VALUES` macro remains under review.
- **C11 complex constructors.** The existing C99 Libm header failed the C11 `CMPLX` consumer on arm64 and x86_64. Corentin approved deriving the three C11 constructors from §7.3.9.3 and Clang's complex builtin. Verify result types, signed zero, static initializers and single evaluation. [C11 committee draft](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1570.pdf)
- **Composition and tool checks.** A synthetic generated libSystem package composed with selected SDK Gen CoreFoundation, Foundation and CoreAudio frameworks plus named ObjC/libc++ stubs. The composer verified embedded providers and rejected a shadowing alternative. Two architecture links exercised this fixture. The scanner, paired verifier, composer, census and header comparison passed 32 focused tests using the pinned bundle.
- **Reproducibility review.** Ambient `CPATH` could redirect a shipping trace to the reference SDK. The tracer now clears inherited compiler settings and disables default Clang configuration. A mismatched SDK selector fails before the Make target writes reports. The version-aware path audit treats the source lock as metadata and checks its digest against the generated include trace.

### Qualification after the repairs

Two fresh installs on macOS produced identical trees with 767 headers, source-lock SHA-256 `2f656f687b3a9b10b23710ed7e6d1a971da670faaba3fddff28b392c7876cef3` and manifest SHA-256 `4d6344110d0284efbd6ffcd8a5aa2b7ddbd796c2e917a3ced6b1fb2b15b24c72`. This full run used the working checkout's version-locked C recipes and existing consumer-header additions. A clean archive of the committed audit tools also reproduced the shipping traces and path audit against an installed tree with `CPATH` pointing at the official SDK.

| Check | Result |
| --- | --- |
| Installed C tests | 12 recipe tests, 362/362 compile checks, all four host fenv rounding modes |
| C11 constructors | `complex-runtime` passed on native arm64 and Rosetta x86_64, host macOS 26.5.2 build 25F84. Each object imported only `__tlv_bootstrap` for its thread-local fixture. Signed zero, infinity, type, static initialization and single evaluation were exercised. Apple also exposes these macros in default Darwin C99 mode. The approved derivation covers C11 and newer. |
| Shipping and discovery | 350/350 shipping probes on both installations. Broader discovery passed 390/476 against the C installation and 476/476 against the reference. This profile also requests frameworks and optional headers. |
| Direct header census | 1,460/1,534 passed. Both `mach/machine/asm.h` cases now pass. The remaining 70 failures also reproduce in the reference, including the two approved eventlink contexts. Four other contexts reach a Clang resource header in place of the installed path. |
| Semantic comparison | 715 headers identical, 48 divergent, four installation-only. Seven named cases still differ on each architecture, down from eleven. See `probe_differences` in the generated report for the affected APIs. |
| Joined backlog | 210 of 3,474 paths have open findings, compared with 211 before the repairs. The report includes 128 pending scope decisions and four required paths absent under their SDK names. Reasons may overlap on a path. All three input reports matched the installation and SDK. |

The next release milestone is to resolve or classify the remaining header groups and populate the production component and deployment evidence. The full consumer gates and production TBD digest remain outstanding. [Reproduction commands](README.md) · [Decision and finish gates](../sdk_composition/libsystem-spec.md#validation-loop-and-finish-gate)

### Local integration references

The following branches supplied the implementation commits. All were integrated into `main` at `/tmp/apple-oss-c-sdk`. This temporary repository has no Git remote.

| Branch | Local commit | Worktree |
| --- | --- | --- |
| `cerisier/libsystem-llvm` | `55d3c0a` | `/tmp/libsystem-wt-llvm` |
| `cerisier/libsystem-scan` | `630100c` | `/tmp/libsystem-wt-scan` |
| `cerisier/libsystem-diff` | `ec74589` | `/tmp/libsystem-wt-diff` |
| `cerisier/libsystem-compose` | `a28126a` | `/tmp/libsystem-wt-compose` |
| `cerisier/libsystem-semantics` | `bb42f3f` | `/tmp/libsystem-wt-semantics` |
| `cerisier/libsystem-backlog` | `bbce25e` | `/tmp/libsystem-wt-backlog` |
| `cerisier/libsystem-availability` | `70591ba` | `/tmp/libsystem-wt-availability` |
| `cerisier/libsystem-xnu-asm` | `097ffc5` | `/tmp/libsystem-wt-xnu-asm` |
| `cerisier/libsystem-c11-complex` | `5e1beed` | `/tmp/libsystem-wt-c11-complex` |

## 2026-11-19 · Assessment of the seven remaining semantic cases

Scope is the 767-header manifest above and SDK 26.5 build 25F70 on both client architectures. The original failing probes are checked in under [c_interfaces](../sdk_review/fixtures/c_interfaces). Runtime checks used arm64 and Rosetta x86_64 on macOS 26.5.2 build 25F84. Targeted provider inspection used the actual arm64e and x86_64 cache images on that host. These findings guide subsequent recipe decisions. This pass made no release changes or new omission decisions.

| Probe | Finding and recommended disposition |
| --- | --- |
| `malloc_backdeploy` | Highest priority for deployment linking. Apple's public libmalloc header includes the backdeployment code. It selects a different branch in publicly processed SDK headers. With Apple Clang typed memory operations enabled and macOS 13 as the deployment target, the generated headers make unconditional calls to weakly imported typed allocation functions. Reference clients check availability and fall back to the untyped allocator. A scratch change selecting the upstream public branch for this one header reproduced the reference on both targets. At minimum 14 both import the typed functions strongly. Official upstream Clang 23.1.2 lacks this feature, so a complementary Apple Clang qualification probe is necessary to exercise it. Qualification used object imports and IR; runtime execution on macOS 13 remains unverified. Propose recipe-local public preprocessing, with evidence of the chosen branch and the missing shipping transformation. [Public header](https://github.com/apple-oss-distributions/libmalloc/blob/c49dafa25f1efe8607701ae6014a663ad2ee437f/include/malloc/_malloc_type.h#L47-L65) · [Apple's backdeployment test](https://github.com/apple-oss-distributions/libmalloc/blob/c49dafa25f1efe8607701ae6014a663ad2ee437f/tests/malloc_type_backdeploy.c#L6-L38) |
| `darwin_sinpi` | Public math declaration and a real libSystem demand. Apple's open-source Clang records `double __sinpi(double)` and its float companion in math.h. The client objects import `___sinpi` and `___sinpif`; the installed libsystem_m exports both. A scratch pair of declarations passed the client calls on both architectures. Propose a scoped Libm declaration derivation, with deployment and feature-mode checks. [Apple's compiler definitions](https://github.com/apple-oss-distributions/clang/blob/8204159ac8569f29fddc48862412243c2b79ce8c/src/tools/clang/include/clang/Basic/Builtins.def#L1181-L1185) |
| `fenv_denorm_mask` | Observable C runtime behavior. Clearing exceptions with the installed mask leaves bit 0x80 set on arm64 and 0x02 on x86_64. The reference mask clears the injected flag on both. The corrected masks are 0x9f and 0x3f respectively. Propose named architecture-specific flags and a saved/restored runtime regression. The mask changes arguments to existing libm functions. An adjacent arm64 environment data object, `__FE_DFL_DISABLE_DENORMS_ENV` in Mach-O, has separate provider evidence and deserves its own inventory row. [Apple ARM register definitions](https://github.com/apple-oss-distributions/xnu/blob/ac9718fb1af618d5ce8678d0dc6e8a58f252216f/osfmk/arm64/proc_reg.h#L815-L826) · [LLVM Darwin fenv](https://github.com/llvm/llvm-project/blob/85ac560262434c9ccfc0c183ec22d4138ed647fb/libc/src/__support/FPUtil/aarch64/fenv_darwin_impl.h) |
| `os_log_sensitive` | The missing names are deprecated user-space macros. The modern reference client uses `__os_log_impl` and `_os_log_type_enabled` on both targets. Ordinary logging through the shipped XNU header uses `__os_log_internal`. All three were observed in libsystem_trace on both cache slices. Treat user-space log lowering as a required inventory investigation. Track compatibility with the deprecated macros separately. A macro-name alias would leave the lowering difference intact. XNU omits its header from the public user-space list. [XNU install classification](https://github.com/apple-oss-distributions/xnu/blob/ac9718fb1af618d5ce8678d0dc6e8a58f252216f/libkern/os/Makefile#L9-L35) |
| `abi_target_value` | `TARGET_ABI_USES_IOS_VALUES` evaluates to 1 on macOS arm64 and 0 on macOS x86_64. Leaving it undefined in an `#if` silently selects Intel AppKit enum values on arm64, including the right/center text alignment values. Recommend a macOS-only CarbonHeaders derivation and assertions of the actual values. This macro contributes no linker symbol. [Apple's architecture guide](https://developer.apple.com/documentation/apple-silicon/addressing-architectural-differences-in-your-macos-code#Address-Numerical-Differences-in-Specific-Frameworks) |
| `compact_arm32` | `UNWIND_ARM_MODE_MASK` describes 32-bit ARM input records. A macOS tool inspecting such a binary can need it on either host architecture. It contributes no linker symbol. Apple libunwind consumes the identifier; pinned LLDB's decoder supplies its value 0x0f000000. Defer this narrowly evidenced format supplement behind runtime and linking gaps. Review any adjacent fields individually; the LLVM ARM assembler and LLDB disagree on a different mask. [LLDB decoder definitions](https://github.com/llvm/llvm-project/blob/llvmorg-23.1.2/lldb/source/Symbol/CompactUnwindInfo.cpp#L116-L137) |
| `syscall_uexc_identifier` | Retain the earlier approved header difference. Public XNU assigns slot 519 to `enosys`. In a compile-only reference probe a generic call embeds the immediate 519 and imports `_syscall`. Apple's dyld source lists a separate wrapper `_register_uexc_handler` under libsystem_kernel, and both runtime cache slices export it. Keep that wrapper visible for symbol eligibility review. The existing header decision authorizes no automatic inclusion or omission of that wrapper. [XNU syscall input](https://github.com/apple-oss-distributions/xnu/blob/xnu-12377.121.6/bsd/kern/syscalls.master#L822) · [dyld export evidence](https://github.com/apple-oss-distributions/dyld/blob/dyld-1378/cache_builder/mrm_shared_cache_builder.cpp#L2226) |

### Qualified libmalloc repair

Corentin approved selecting Apple's public branch while staging `malloc/_malloc_type.h` for SDK 26.5. The recipe uses `unifdef` on that one source file and cites Apple's own backdeployment test in its receipt. The public OSS release supplies the branches and test; its sanitisation script does not supply this invocation. The generated file retains unrelated upstream text, including bridgeOS annotations. Reassess this local install step when the source pin or SDK changes. [Recipe](../../recipes/libmalloc/Makefile)

The original installation failed the typed allocation check. The repaired installation and SDK passed all eight combinations of sysroot, architecture and deployment minimum (13.0 and 14.0) with Apple Clang 21. The check covers weak imports, the conditional call to each plain allocator, post-14 strong imports and direct-call visibility. All four linked allocation clients ran on macOS 26.5.2 using reference link stubs, including Intel execution under Rosetta. These runs exercise the current runtime; old-OS fallback is qualified by emitted code. [Reproduce the check](../sdk_review/c_interface_review.md)

Two installs were identical. The sole payload change from the previous 767-header package was `malloc/_malloc_type.h`. The new manifest SHA-256 is `e735df126c2f25b24e4da8b0aba468c4664f4cf53a079deb92b4bed6e6bf0cd8`. All 362 C compile checks, 12 recipe tests and the host fenv probe passed. Six of the original seven semantic cases remain on each target. The joined audit still has 210 paths with open findings, with all inputs current. The libmalloc recipe is commit `d42ad25`; qualification is `6e3e34b`, integrated from local branch `cerisier/libmalloc-backdeploy-check` at `a0f3d7c` in `/tmp/libmalloc-backdeploy-check`. This repository has no remote.

### Header decisions and macOS 26.5 client stub

The approved sine-pi, exception-mask and framework ABI changes are in `3a447ef`, `8384b0f` and `68dea5e`; `ba734dd` keeps the Intel fenv transformation tied to the selected source checkout. The generated C manifest digest is `d54e27f267ceec1d6ad13621e1287d8d2f5c6829c747912196a63e43c7c74149`. All 362 C compile checks and 12 recipe tests passed. The semantic comparison with SDK 26.5 now has three distinct open cases on each target. The joined audit has 206 of 3,474 paths with open findings and zero input identity issues.

| Case | Evidence and decision |
| --- | --- |
| Sine-pi declarations | Apple's Clang definitions establish both signatures. Emitted client references and native/Rosetta runtime checks pass. Intel imports change from weak at minimum 10.8 to strong at 10.9. [Receipt](../../recipes/libm/sinpi.md) |
| Floating-point exception mask | Source-backed architecture flags cover the input-denormal bit. Injecting that flag before clearing `FE_ALL_EXCEPT` reproduced the failure and the repair on both CPUs. [Evidence](../../recipes/README.md) |
| AppKit target ABI | Apple's docs establish the actual enum numbers. The objc2 bindings corroborate the macro name and meaning. Preloading our previous target header caused Apple's reference AppKit header to assign the Intel center value on arm64. The generated macro fixes both alignment assertions and preserves the Intel values. Framework sources are used only in the local test. [Receipt and reproduction](../../recipes/CarbonHeaders/macos-abi.md) |
| Modern user-space logging | Keep the public header lowering and its required libsystem_trace entry points open. No omission waiver. |
| Compact unwind ARM32 | Defer this binary-format convenience for old input files. No arm64 or x86_64 client linker symbol arises from the constant. |
| Syscall 519 | Keep the generated public XNU header. The separate wrapper still requires its own eligibility decision. |
| Normal macOS dyld build | Public SDK 26.5 omits `TARGET_OS_EXCLAVEKIT` on both targets. Apple Clang warns and LLVM 23 diagnoses a bare test as an error. Corentin approved a zero definition only while compiling ordinary macOS dyld assembly. Apple separates the two build targets explicitly. The public header keeps its original definedness. [Build settings](https://github.com/apple-oss-distributions/dyld/blob/fd8d0c4d52320ebf64db34f3cb280310d905c5ae/Configs/libdyld.xcconfig#L4) · [Platform switch](https://github.com/apple-oss-distributions/dyld/blob/fd8d0c4d52320ebf64db34f3cb280310d905c5ae/mach_o/Platform.cpp#L749-L785) |

The four-root client experiment scans `math.h`, `stdio.h`, `sys/stat.h` and `unistd.h`. All 39 direct reexports in the observed cache matched separate slots in the public Libsystem build. On macOS 26.5.2 build 25F84, the arm64e and x86_64 cache observations established unique providers for 478 arm64 and 496 Intel demands, including a linker helper. All raw observations stay local.

The first candidate linked and ran a client using `getpid` and `puts`, but its binary lacked the reference linker's `dyld_stub_binder` import. Apple's pinned dyld assembly exports that exact name on both targets. Including it also reproduced the reference Mach-O load and import metadata. Treat a dynamic resolver on an Intel math function as a text export under LLVM's TBD rules. The result passes 28 paired links across both architectures, two real clients and seven deployment minima (11, 12, 13, 14, 15, 26, 26.5). Both clients run on the current arm64 and translated Intel runtime. This does not exercise execution on the older OS builds. [Local reference workflow](../sdk_review/libsystem_review.md)

Two renders from the same observations produced byte-identical partial packages. Candidate digest `cabd13538f77ea9f0ea235073892d9263e19906114dcee07b1e27109366b7d16`. Scratch evidence is in `/tmp/libsystem-provenance-26.5.22E63e`. The raw SDK audit reports 43,027 differences across 40 reference and 40 candidate images, including raw slices outside the two client targets. This is a local four-root diagnostic. The release lock, full coverage decisions and consumer gates remain open.

The four-root omissions are `_profil`, `_add_profil` and `_unwhiteout` on both targets, plus `___fpclassify` on arm64. The pinned Libc profiling implementation says the two profiling syscalls were retired; XNU's syscall master corroborates this. The double-precision arm64 `fpclassify` discrepancy causes an actual client link failure against the official 26.5 SDK. Corentin requires applicable Apple OSS evidence before changing its header. A match for Intel or PowerPC in isolation leaves the arm64 case open. [Apple Libc](https://github.com/apple-oss-distributions/Libc/blob/main/gmon/gmon.c) · [XNU syscall inputs](https://github.com/apple-oss-distributions/xnu/blob/ac9718fb1af618d5ce8678d0dc6e8a58f252216f/bsd/kern/syscalls.master)

Additional local tool branches, all in the temporary repository with no remote:

| Branch | Commits | Worktree and verification |
| --- | --- | --- |
| `cerisier/libsystem-sinpi-repair` | `6a22cea`, `29d5324` | `/tmp/libsystem-sinpi-repair`. Source declarations, both target runtimes, 13 Apple Libc/dispatch directives per architecture. |
| `cerisier/libsystem-fenv-repair` | `bd9a2a3`, `fa8dfdd` | `/tmp/libsystem-fenv-repair`. Runtime exception clearing on both targets. Compiling public compiler-rt produces 318 directives per target. The same 54 reference-only rows on each target remain open. [Directive investigation](compiler_rt_directives.md) |
| `cerisier/libsystem-production-graph` | `3544f69`, `2847ef2` | `/tmp/libsystem-production-graph`. Offline graph reproducibility, 48-cell scanner sample, checkpoint replay, explicit failed controls. [Root scanner](scan_roots.md) |

Compiling the upstream dyld assembly also establishes the `__tlv_bootstrap` entry point for C thread-local variable descriptors. The [assembly recipe](dyld-assembly.md) came from `e04628e` on the component graph branch above and was integrated as `9c20ee5`. Adding that helper produces candidate `05605567ea62ebf3eb5e805df2a679ec1ce15e18820e8e28906f6b63a545b039`. Both renders were identical. The I/O, thread-local and sine-pi clients passed all 42 paired links across the seven sampled minima, and all six candidate executables ran on build 25F84. The partial stub is under `helpers-candidate/usr/lib` in the scratch directory above. The full per-header scan uses separate checkpoint directories by architecture and feature profile.

### SDK-wide provider check before omission decisions

Corentin requested an SDK-wide provider check before deciding the three `unistd.h` cases. Local raw-text and structured searches cover 3,259 physical TBDs and 3,520 library documents, including framework and private stubs. There is no match for `_profil`, `_add_profil` or `_unwhiteout`. After verifying Apple's Libc source and install rule, Corentin approved keeping the declarations and excluding their three exports in 26.5. A separately linked library is a normal outcome for other C headers: six installed paths produced a strict link outside libSystem on both architectures. See the [header census, exact scopes, sample bindings and replay commands](../sdk_review/sdk_header_linkage.md). The SDK-only survey is an investigation input. No SDK-derived library inventory was added to the generator.

The full generated installation scan attempted all 767 installed paths in two C profiles per target. Before the scanner re-inclusion repair in `43bd72b`, each arm64 profile had 701 passing paths and each Intel profile had 699. The initial wider diagnostic emitted 2,623 arm64 and 2,649 Intel unique supported definitions. It kept 360 and 346 demands, respectively, for further review, which includes APIs supplied outside libSystem. Do not convert those counts into missing-libSystem counts. The directly observed `fpclassify` failure remains open after searching all public Apple Libm release history and other Apple OSS projects. [All three C types and the source search](../sdk_review/data/macosx26.5/fpclassify-gap.md)

In each of the four original scan cells (architecture × profile), all 28 tool failures were retried with the corrected scanner. 27 passed and the last reached a real unresolved import. The SDK header survey in `f26a8ee` was integrated from local `cerisier/libsystem-production-graph` at `b98ea67`. The SDK-wide lookup in `7bb89ea` was integrated from `cerisier/libsystem-fenv-repair` at `7883ac4`. The scanner repair and fpclassify evidence came from `cerisier/libsystem-sinpi-repair` at `336e3c4` and `fd06f98`. All use the local worktrees listed above; the repository has no remote.

The [26.5 exemption](data/macosx26.5/expected-undefined.json) entered the offline producer in `f43c215`. The [reference regression](../sdk_review/unistd_expected_undefined.md) in `2f2bd32` (from `cf5a2f2` on the local production-graph branch above) passed all 24 expected-undefined links across both header installations, architectures, and deployment minima 11.0 and 26.5. All three functions compiled from each header installation. Each strict link failed on the exact requested symbol, and the getpid control linked. Two offline builds from a local release lock scoped to unistd.h produced the same stub SHA-256, `421886808191ed47192487bfaa3306c2de9e952b29b9eeee5538ef412e7a3139`. Both target slices omit the three symbols and retain `_getpid`, `_read` and `_write`. This qualifies the exemption. Full-installation release and consumer qualification remain open.

### Libc string and memory aliases

The original four root scans and their corrected checkpoints together identified 2,787 arm64 and 2,813 Intel directly supported names. A client taking the address of all 22 functions from Apple's `xcodescripts/alias.list` compiled for both CPUs. All 22 were undefined in the candidate, while the same objects linked against 26.5. Pinned Libc applies that list with `-alias_list` to libsystem_c. Both installed slices confirmed the forwarding image, implementation spelling, and a function definition in libsystem_platform for each. The offline producer emits the public names as symbol reexports. For example, its receipt traces `_memcpy` through libsystem_c to `__platform_memmove` in libsystem_platform.

The resulting diagnostic contains 2,809 and 2,835 supported names. Both renders matched byte for byte and all 14 paired client links matched across seven deployment minima. Two offline builds scoped to string.h, strings.h and unistd.h produced identical packages (stub SHA-256 `0fe513a4ddd193ae7be7ab909c9e1eed0f0de2e538c8a7c2fa55cf91d887429e`). A default-compiled executable separately exposed the implicit stack-protector function and guard. Local evidence under `/tmp/libsystem-scan-reconciliation.0Gubc2` includes the failing and passing objects and link reports. [Release rule and upstream inputs](README.md)

### Compiler-generated stack protection and LLVM consumer imports

A default-compiled string client failed to link on `___stack_chk_guard` and `___stack_chk_fail`. Pinned Apple Libc's `sys/OpenBSD/stack_protector.c` defines the data object and function, respectively. Direct runtime inspection found both strong definitions in libsystem_c on the arm64e and x86_64 cache slices. Clang independently emitted exactly these two references from a protected local array at O0 and O2 on both client architectures. The offline producer now applies the verified Libc recipe when a release lock supplies `libc_source`. All 28 paired links matched at seven sampled minima. Executables referring to all 22 Libc aliases and exercising memcpy, memmove, strlen and strcmp ran on host build 25F84 natively and under Rosetta. The two offline package trees were byte-identical; stub SHA-256 `084075c4c30f602ab6483394e6b7fae25f826b285d994b28f7b4652e4d6b01e8`. The lock selected string.h, strings.h and unistd.h and carried the locally observed component facts. This remains a qualification candidate.

The [consumer import replay](../sdk_review/libsystem_review.md) reproduced seven missing bindings out of 254 from the existing x86_64 Stage 2 LLVM executable, and eight out of 233 from the official arm64 LLVM Clang binary. The earlier arm64 Stage 2 symlink has no target in the local cache. Strict reference links bound every sampled name; the candidate reproduced the same missing sets at minima 11 and 14.0. The exact lists are in `/tmp/libsystem-scan-reconciliation.0Gubc2/{candidate,native-min}-consumer-{arm64,x86_64}.json`. The first shared source group is Apple's FortifySource target: all 16 `secure/*_chk.c` implementations compiled as published against our C installation on both architectures. Its project also includes two other translation units. Source objects alone do not establish public export eligibility. The complete LLVM rebuild and other release gates remain open.

A second independent check compiled ordinary calls to memcpy, memmove, memset, strcat and strcpy under `-O2 -D_FORTIFY_SOURCE=2` against the standalone headers. Both objects import the checked spelling of all five functions. The source objects from Apple's FortifySource target define those same names. They are the next group to qualify against deployed libsystem_c and the reference linker. The consumer replay checks each import's weak/strong flag as well as its spelling. Both SDK-against-itself controls passed.

### Fortified memory, string and formatted-I/O imports

Apple Libc's FortifySource target builds the sixteen checked wrapper source files in the input lock. A client using the ordinary public functions imports sixteen checked names on each architecture. The recipe compiles every source file and matches actual external text definitions to that client. Two additional definitions in those objects have no reference from this fixture and were not added by this rule. All sixteen reviewed names have ordinary definitions in the installed libsystem_c on both cache slices of 25F84. Twelve per architecture were missing from the preceding stub; four were already present.

Both clean packages match byte for byte (stub `0502842ffbbd36a8fc199f84deca94c80dc9106e87bb8efe321e61f9ef5bd15f`). All 14 paired links across seven minima matched and both executables ran, exercising checked string copy/append, overlapping move and formatted output. At the LLVM consumers' original minimum, 14.0, three Intel Stage 2 imports and four arm64 official-Clang imports remain unresolved. The public C headers were unchanged for this result. Evidence lives under `/tmp/libsystem-fortify-qual.1isE94`. Two math-header questions and a distinct runtime forwarding decision were sent to Corentin. Their linker-side source investigations proceed independently.

### Effective client coverage, macOS 26.5

The release targets ordinary arm64 and x86_64 macOS clients. Apple uses
arm64e in the reference umbrella, and its installed system uses an arm64e
cache. Keep these as inputs for qualifying the arm64 client. Mac Catalyst,
arm64e and x86_64h clients are outside the release gate.

Two offline builds of the candidate produced identical package trees and
stub digest `2c729ceef0000d0dcf40a0844168ec4b56bed72e406e75689377c1e23401c2d5`.
The comparison below reran with the selected installation and the SDK 25F70
header survey. Counts were identical at macOS deployment minima 11.0 and
26.5. Each numerator counts symbols that actually bind through libSystem.

| Client surface | arm64 candidate / Apple | x86_64 candidate / Apple |
| --- | ---: | ---: |
| All linker names found by the export and C declaration survey | 2,837 / 8,960 | 2,863 / 9,500 |
| Reference C declaration survey | 2,636 / 3,112 | 2,660 / 3,133 |
| Survey declarations associated with a header path in the C installation | 2,636 / 2,663 | 2,660 / 2,686 |

The candidate had zero extra bound names. The narrowest row still misses
17 math names and nine logging names on each architecture, plus one arm64
floating-point environment object. Corentin approved qualifying individual
math declarations with independent signature and availability evidence.
5,647 arm64 and 6,164 x86_64 missing names were outside the C survey.
Their public/private status is unresolved. The three approved
`unistd.h` negative links are absent on both sides. The approved
[stack-probe forwarding](stack_probe.md) covers two role differences and
changes neither count. Its [decision record](../sdk_review/data/macosx26.5/libsystem-decisions.json)
matches both findings and reopens on reference or finding drift.

The [client coverage command](../sdk_review/libsystem_review.md) reproduces
the comparison. Raw SDK inventories and linker evidence stay local. This
run is under `/tmp/libsystem-effective.qXI66t`, and the package, reference
diff and log files are under `/tmp/libsystem-fortify-qual.1isE94`. The
full raw metadata diff of 41,185 rows includes other client targets and
repeated differences. It has 2 approved role rows. Neither that total nor
the coverage percentages constitute a release gate pass.

The C installation passed 362/362 compile checks and the native fenv runtime
test. The combined SDK linked and ran the base-10 exponential and paired
trig clients on both architectures. Six replay cases with the preceding
candidate matched all 233 arm64 official Clang and 254 prior Intel Stage 2
LLVM imports. The fresh bootstrap first exhausted disk during LLVM source
extraction. After space was freed, the archive selector rejected absent
private/Cryptex framework directories before compilation. Both public
frameworks were present in the composed archive.

Integrated local branches (the repository has no remote) are
`cerisier/libm-exp10-header` (bd12700, /tmp/libsystem-exp10-header),
`cerisier/libsystem-stack-probe-rule` (11029ca, /tmp/libsystem-stack-probe-rule),
`cerisier/libsystem-compat-links` (51811d3, /tmp/libsystem-compat-links) and
`cerisier/libm-paired-trig` (a5d1213, /tmp/libsystem-paired-trig).

### Scalar pi repair and the original 45 headers

The SDK 25F70 byte audit originally compared 761 installed files. The
current 767-file installation has all 45 original divergent paths plus
`os/log.h`, `pthread/introspection.h` and `sys/syscall.h`. Of the 767,
715 are byte-identical and four have no reference counterpart. Header
qualification uses behavior and provenance. Qualifying a source-derived
repair can preserve a byte difference.

On the latest header tree all 364 standalone compile checks passed. The
paired interface suite ran 56 probes on each target at minimum 14.0.
Three probes differed on each target, down from eleven before repairs:
the open modern logging macro, the deferred ARM32 compact-unwind constant
and the approved public XNU syscall-number difference. The additional
arm64 `fpclassify` client-link issue has a [separate receipt](../sdk_review/data/macosx26.5/fpclassify-gap.md).
Corentin chose to keep the arm64 `_FE_DFL_DISABLE_DENORMS_ENV` C and binding
gap open pending independently sourced public interface evidence.

The [four scalar pi functions](../../recipes/libm/scalar_pi.md) closed four
actual linker gaps on each CPU with no extra bindings. Source branch
`cerisier/libm-scalar-pi`, commit `6d15796`, is at `/tmp/libsystem-scalar-pi`;
integration commits are `c546c5b` and `6fe97e5`.

| Latest candidate at minima 11.0 and 26.5 | arm64 | x86_64 |
| --- | ---: | ---: |
| Effective bindings matching the reference | 2,841 / 8,960 | 2,867 / 9,500 |
| Missing effective linker names | 6,119 | 6,633 |
| Surveyed C names binding through libSystem | 2,640 / 3,112 | 2,664 / 3,133 |
| Subset declared at a path we install | 2,640 / 2,663 | 2,664 / 2,686 |

Stub SHA-256 is `33afec02408b439fc98b1056aa54adff3e8a3b24a60d2cb9670095ba8a0a828e`.
Two full package builds matched. The local reports are
`/tmp/libsystem-fortify-qual.1isE94/scalar-coverage.json` and
`scalar-semantics.json`. The approved stack-probe decision still matched
both raw rows. The raw review now reports all 20,388 Catalyst-only rows
outside the client scope. Real client linkage resolves the reference's
ordinary versus subtype slice differences.

The SDK archive selector fix allowed Bazel to begin bootstrap compilation
with the preceding candidate. All six LLVM binary import replays on that
composition matched. A newly built Stage 2 executable, hermetic-llvm e2e
and rules_rs on the latest digest are still qualification gates. Corentin
left netname header scope to the maintainer. Use XNU's public MIG source
to qualify the four stub entries while retaining the minimal C package.

The complete joined header audit on this installation reports 206 of 3,474
paths with open findings, two approved standalone contexts and zero input
identity errors. These include scope decisions on optional SDK paths and
reference-side failures. The total does not count confirmed header defects.
The [release gate](../sdk_composition/libsystem-spec.md#validation-loop-and-finish-gate)
now requires a post-consumer review of all 48 current byte differences.
Recover the original 45-path review at commit `aa214ae` under
`tools/sdk_review/reports/macosx26.5-header-differences.md`. Review distinct
issues within each file separately against the new manifest.

Scratch hermetic-llvm branch `cerisier/sdk-framework-locations`, commit
`d92a9764364584c8f342db198c6d8cbd312e0e51`, worktree
`/tmp/libsystem-framework-selection`, fixed SDK archive selection for the
three recognized framework locations. The tar fetch passed with each
location individually, with multiple matches and with the composed archive.
Missing requested frameworks and missing required standalone files failed.
Host and pkg behavior matched the original. The branch is local by request.

### Kernel-generated clients and the Objective-C composition

XNU's pinned NetName MIG definitions and the public install rule establish
four additional client entry points. The generator reads the four reviewed
XNU inputs through the optional `xnu_source` field. All four bind through
libSystem on arm64 and x86_64 at 11.0 and 26.5. The generated client code
and observed `libsystem_kernel` definitions qualify the same names. Local
branch `cerisier/libsystem-netname`, `139d5a0`, worktree
`/tmp/libsystem-netname`, supplied the rule. The integration is `e1a778f`.

Two complete offline packages matched, including stub
`5b23b4a5050f208a66a1b9c40872eb66a3b327876ab3451f6d780f3eb2d88998`.
Effective coverage is now 2,845/8,960 and 2,871/9,500 (arm64 and x86_64),
with zero extra names. The installed-path survey remains at 23 and 22 missing
bindings since the standalone C installation excludes the NetName headers.
The scratch `netname-coverage.json` report is alongside the scalar reports.

After fixing archive selection, LLVM's Intel link required Foundation's
reexport of `/usr/lib/libobjc.A.dylib`, and compiler-rt's TSan build required
the public ObjC synchronization header. The current composition selects the
two existing SDK Gen libobjc stub paths and nine pinned ObjC runtime headers
as separate layers, plus SDK Gen libc++ stubs and qualified frameworks.
Archive SHA-256 is `6dc80a49940bc48ea32b45130c3636ad68aa94254ef83677f87ba0f319a080c4`.
The Intel bootstrap, hermetic-llvm e2e and rules_rs runs against that archive
write `netname-bootstrap-intel.log`, `netname-e2e.log` and
`netname-rules-rs.log` under `/tmp/libsystem-fortify-qual.1isE94`.

The Intel Stage 2 build completed and the thin executable was fetched to
`stage2-x86_64`. The arm64 build on the identical archive writes
`netname-bootstrap-arm64.log`. The standalone ObjC layer was integrated
from `cerisier/libsystem-objc-layer`, `03c5203`, `/tmp/libsystem-objc-layer`.
All 17 composer checks passed, and a two-library Objective-C client linked
and ran on both architectures. The scratch branches have no publication.

UBSan subsequently reached its dynamic-library link and requested
`-lc++abi`, three kernel syscall entries, two malloc data exports and four
dyld inspection entries. All nine C bindings linked against the reference
at both supported client architectures and both deployment endpoints.
Apple OSS supplies the implementation evidence for each. The entries are
SPI consumed by the pinned compiler runtime, so their release eligibility
requires an explicit scoped decision. The C headers were sufficient for
this compilation. The SDK Gen `libc++abi.tbd` is a separate composition
input. The broad rules_rs run requests the MSVC runtime EULA through a
cross-target test; native target results are in `netname-rules-native.log`.

### Native bootstrap and sanitizer qualification

The two NetName Stage 2 targets passed. Their action graphs show that the
source-built Stage 1 compiler ran on Linux ARM and cross-compiled the
macOS Stage 2 binaries. Each resulting Clang ran on this Mac and compiled
a scalar math client. Its linked executable ran on the same architecture
(Rosetta for Intel). This establishes executable macOS compilers on both
targets. The separate self-bootstrap gate requires a macOS Stage 1 action.
Selecting `--extra_execution_platforms=@platforms//host` after the release
config produced that action in `native-arm64-action.txt`. The first local
build failed on the host tool's C++ exception cleanup import,
`__Unwind_Resume`. The rules_rs process wrapper exposed the same failure.
The custom registry test passed with Bazel on the test PATH.

The maintainer approved nine compiler-rt dependencies from pinned dyld,
XNU and libmalloc. Commits 40c071c and de2035b select them from the consumer
declarations and record verified definitions in each provider. Paired links
passed on both clients at minima 11.0 and 26.5. Two offline builds matched.
The composition also selected the separate SDK Gen dynamic libc++abi stub.
The e2e rerun reached the TSan dylib link. Its nine outstanding imports were
four private lock functions, three ucontext functions, base-name realpath and
fileno_unlocked. The four locks have scoped linker-only approval.

The libunwind receipt qualifies 32 of 43 system exports per CPU, including
the cleanup import. A C++ exception exercised the destructor in each slice.
Eleven names remain open. CommonCrypto's public export rule qualifies all
245 names, 241 text and four data. The previous candidate covered 54.
The maintainer approved the full verified list with SPI headers outside
the C package. Local qualification receipts are
`/tmp/libsystem-unwind-qual.bEMk41/summary.json` and
`/tmp/commoncrypto-abi.w7cVeA/link-qualification.json`.

### TSan locks and the XPC decision

The four TSan interposers now have strong text bindings through libSystem
on both macOS clients at minima 11.0 and 26.5. The source recipe checks
Apple's provider and LLVM's interceptor declarations. Private lock headers
serve as producer evidence. Commits f9aeb5e and b8865d9 integrate
`cerisier/libsystem-tsan-locks` (dee5fd3, `/tmp/libsystem-tsan-locks`).
The paired positive and negative link receipts are under
`/tmp/libsystem-tsan-lock-audit.bNdPCt`.

The combined candidate's SHA-256 is
`57585ec01d88d01b964e3a8557f8dca0ebc9633cf7fc0e0bc97d4fc6acde9a75`.
Its effective link coverage increased by 236 names per architecture
relative to the NetName build. It supplies 3,081 of 8,960 on arm64 and
3,107 of 9,500 on x86_64, with zero extras at both deployment endpoints.
The installed-header comparison still has 23 and 22 missing names.
`locks-qualified-coverage.json` contains their individual spellings.

The maintainer left libxpc open. The local public-documentation census
identified 147 macOS C functions, 146 absent from both candidates. It is
an investigation record (`/tmp/xpc-docs-audit.Ugcp2q/results.json`).
The XPC provider and standalone public headers remain open for review.

### Consumer gates take priority

The maintainer requested that the macOS LLVM self-bootstrap, hermetic-llvm
e2e and rules_rs pass before further export-parity work. The Libnotify
exploration and the local research input generator are parked on separate
branches. The broad header scans have resumable checkpoints. Libxpc stays
open. Resume parity decisions only after the three consumer gates.

The TSan repro qualified five remaining consumer imports and the public
makecontext companion exercised by the runtime fixture. Apple Libc and
libplatform headers compile as supplied, using POSIX and X/Open feature
profiles where applicable. The fileno interceptor uses the explicit
declaration from compiler-rt. Source commit 1b58d02, integration d999129.
Native and Rosetta runtime receipts live under
`/tmp/libsystem-tsan-public-qual.HzhduL`. The scratch e2e archive with the
six additional bindings has SHA-256
`1dcb8b49737a223fb9974160aca649ef2085a5ee0834579f3a5e6ff9dfca050e`.

Darwin's UBSan target requests both `-lc++` and `-lc++abi`.
The tested hermetic-llvm source-header setting selects the pinned headers
and retains the Apple system runtime. The first link failed when
`usr/lib/libc++abi.tbd` was absent. The composition now includes the SDK
Gen dynamic stub for `/usr/lib/libc++abi.dylib` alongside the system libc++
stub. Both belong to the consumer composition.

The native rules_rs retry passed 23 tests. Sixteen could not build because
Rust's prebuilt standard library refers to `_Unwind_GetTextRelBase` and
`_Unwind_GetDataRelBase` in its panic personality. The maintainer declined
adding the two system compatibility exports. An LLVM-toolchain alternative
is under investigation. The projected LLVM tools directory supplies
the unwind header and omits the prebuilt library. The
current Rust action's libunwind search directory contains an empty
compatibility archive. This differs from hermetic-llvm's explicit
`@llvm//runtimes/libunwind:libunwind.static` source-build target.

Darwin libFuzzer also reads `environ` directly. The baseline failed on
that object. Pinned Apple dyld defines the data, and LLVM supplies the
client declaration. Four paired links passed and the runtime fixture
passed the process environment to a child on both clients.
Source commit 030ec19 and integrations e159e99 and 66848f6 provide an
opt-in producer input. ASan separately failed linking two private
dispatch Mach constructors. The maintainer approved those two only.
The full remote e2e run also attempted to execute Mach-O test binaries
on Linux. Native macOS execution with the declared SDK is required for
the runtime gate.

The scoped ASan rule derives both consumer names from LLVM's interposers.
Apple's private header and Mach implementation identify the APIs and the
provider. The four baseline links failed on precisely those names.
After adding them, both client architectures matched the reference at
both deployment endpoints. Only two strong text entries per slice were
added to libdispatch. Source commit f15d017, integration 6658b83.
Receipts are in `/tmp/libsystem-asan-dispatch-audit.dnBULg`.

### Generating linker entries from LLVM runtime artifacts

Correction to the initial archive inspection: the official macOS ARM64
LLVM 23.1.2 release tarball includes all three shared libraries.
The project's extracted tool projection omits them. Reading the original
tar with `zstd --long=30 -dc`, then applying
`llvm-readtapi -stubify --filetype=tbd-v5` to the three real dylibs,
produced arm64 TBDs with a macOS 14 minimum and `@rpath` install names.
The thin dylibs and resulting stubs are under
`/tmp/libsystem-fortify-qual.1isE94/upstream-runtimes`.

SDK 26.5 clients can request the unwinder through `-lSystem`.
The SDK's `usr/lib/libSystem.B.tbd` reexports the install name
`/usr/lib/system/libunwind.dylib` and embeds the provider's document.
Apple also supplies `usr/lib/system/libunwind.tbd` separately.
The official LLVM arm64 libunwind stub has 44 exported names. Its two
relative-base names both link through Apple's umbrella at minimum 11.
LLVM also exports `_unw_strerror`, which failed that same reference link.
The maintainer requested combining the verified relative-base entries with
our system provider. Keep its install name, reexport edge and deployment
evidence, and derive the two entries for each architecture from its LLVM
artifact. A separate runtime dylib is unnecessary for those clients.

The ASan-plus-fuzzer composition passed the native arm64 hermetic-llvm e2e
run: 36 passed and 45 skipped (`asan-e2e-native.log`). The repeated
offline packages matched. All 42 libSystem producer tests passed.
The Intel e2e run under Rosetta registered the Intel execution platform:
33 passed, three ASan-related targets failed to build and 45 were skipped.
The concrete Intel sanitizer imports are eight unadorned inode-compatibility
names (`asan-e2e-rosetta.log`). Normal Intel C clients compile with the
existing inode64 spellings.

### Two-architecture sanitizer and unwind consumer qualification

The Intel inode compatibility recipe cleared all three sanitizer build
failures. Intel e2e completed with 36 passes and 45 skips under Rosetta
(`intel-e2e-rosetta.log`). The arm64 and Intel e2e runs used successive
compositions. A common-archive rerun is still required.

The maintainer chose the pinned Apple implementation as the production
input for the two relative-base compatibility entries. The LLVM artifacts
provide independent corroboration. Commit `539ecbd` extends the embedded
libunwind section from 32 to 34 names on each CPU. For this change the
distributed inputs are the same Apple source pin and the same public
headers as before. A scratch build of the real arm64 Rust process wrapper
imports both names from libSystem and successfully compiles downstream crates.

Two offline builds with the Intel sanitizer and unwind fixes produced
identical packages. The libSystem.B.tbd SHA-256 is
`08823a35c8ef65406a7d53c46f34b5c5e8fd7319ee2b8a28510b0ffe20f914d5`.
All 44 producer tests passed with their source fixtures enabled.
Six differential links matched SDK 26.5 for both bindings, dependency
versions and deployment metadata on arm64 and x86_64 at 11.0, 14.0 and
26.5. Evidence lives under `/tmp/libsystem-fortify-qual.1isE94` in
`accepted-package`, `accepted-repeat`, `accepted-checked-tests.log` and
`accepted-unwind-links`.

PyO3, two Prost generator tools, and wasm-bindgen reached a separate
`-liconv` link failure. The maintainer approved producing libiconv and
libcharset as separate composition inputs from Apple's libiconv project.
The unversioned-path Rust test itself reported a pass, but Bazel's
`generate-xml.sh` process crashed. The host bash crash report identifies
Homebrew bash in libintl's locale initialization. Rerun the Bazel gate.

Commit `c66899b` generates the two versioned iconv and charset stubs
and their aliases from Apple's libiconv-115.120.2 project. The composition
uses the generated artifacts under `/tmp/iconv-provider-26.5/qualified`.
All 95 direct libiconv exports and both libcharset exports match the 26.5
reference. A client linking with `-liconv` alone binds `_iconv_open` to
libiconv and `_locale_charset` to libcharset on both CPUs. The generated
stubs conservatively mark app-extension use unsafe. Qualification covers
ordinary macOS clients.

The common archive is `qualified-union-composition/MacOSX.sdk.tar.zst`
under the qualification directory above, SHA-256
`463a57dda1cf809b59ba9263375193642c6352996eb28323bb4955ed5b896e0f`.
The native bootstrap and e2e trials moved to this digest. Earlier bootstrap
actions from the locks-only archive do not count as a completed bootstrap.

Stock Rust 1.96.1 at minimum macOS 14 linked and ran the panic fixture on
arm64 with both this archive and Xcode. On x86_64 the control also ran,
while the candidate had one unresolved import, `_close$NOCANCEL` from
Rust std's file-descriptor cleanup. The pinned XNU macOS syscall maps give
that alias on both CPUs. The two-level unwind checks themselves matched.
The candidate and control logs are in `accepted-unwind-links`.

### Rust std non-cancelable close

The XNU syscall generator emits `_close$NOCANCEL` as an assembler alias
of `___close_nocancel` for both macOS CPUs. The restricted source recipe
and the complete pinned XNU checkout produced identical close assembly and
Mach-O objects at minima 11.0 and 26.5. The two strong definitions share
an address in each object and in both deployed kernel images on 25F84.
Enable the recipe with `"close_nocancel": true` in the XNU release lock.

An unlisted `mach/i386/syscall_sw.h` in the C installation could shadow
the private XNU header. The assembler now searches the pinned XNU headers
first and gets its C headers from the manifest-verified composition. The
shadow-header regression is recorded in `shadow-before.log` and
`shadow-after.log`. The corrected recipe reproduced the original assembly
and all four object digests at the two deployment endpoints.

At both minima on both CPUs, the previous package failed on the close
relocation and the updated package matched the Xcode 25F70 bind through
libSystem, dependency versions and deployment metadata. The new TBD adds
one strong kernel export per slice. Two complete offline packages matched,
including manifest and symlinks. The previous lock also reproduced its
earlier package. All 46 producer tests passed. The new TBD SHA-256 is
`68d32af65624ce050a2cddba300010b1bebdfe6d36eb5d9e3d3416842144f6f0`.
Inputs, packages, test log and paired-link reports are under
`/tmp/xnu-close-qual.7LUZ35`.

The composed SDK with that package and the qualified iconv layer has archive
SHA-256 `c0a98a31e6de870f5aa56b928469c09ce2c61e4bb9840fee499c51c6083e5494`.
The checked-in Rust 1.96.1 panic fixture linked and ran on native arm64
and Rosetta x86_64 at deployment minima 11.0, 14.0 and 26.5 on the
26.5.2 host. All six binaries bind both relative-base unwind symbols
through libSystem. The three Intel binaries also bind the non-cancelable
close there. Inspect their Mach-O imports, dependencies, and run logs in
`/tmp/libsystem-fortify-qual.1isE94/close-rust-panic`.
The preceding archive starting with `463a57dd` passed 36 applicable
hermetic-llvm e2e tests on each architecture, with 45 skipped per run.

All 39 macOS-scoped rules_rs tests executed and passed on arm64 with the
iconv archive starting with `463a57dd`, including PyO3, Prost and the
custom registry test (`union-rules-arm64.log`). The command excluded
`//:target_triple_constraints_test`, whose transition requests every
supported platform and whose Windows configuration requires an MSVC
license decision. The Rust and hermetic-llvm runs against the later
close-alias archive have separate `close-rules-*` and `close-e2e-*`
logs. The native Stage 2 bootstrap log is `close-stage2-arm64.log`.

### Same-archive e2e execution and reproducible packaging

With the close-alias archive starting with `c0a98a31`, hermetic-llvm's
rules_cc e2e suite executed and passed all 36 applicable tests on each CPU
with test-result reuse disabled. Bazel skipped 45 targets per CPU. See
`close-e2e-execute-arm64.log` and `close-e2e-execute-x86_64.log` under
`/tmp/libsystem-fortify-qual.1isE94`. The bootstrap, e2e and rules_rs
materialized sysroots all contain the same `libSystem.B.tbd` starting with
`68d32af6`. Every retained manifest file and symlink matched the composition
in `close-materialized-sysroots.json`. The hermetic-llvm extraction rule
selects `usr/include/device` when IOKit is requested by rules_rs.

Two independent package and composition trees produced identical normalized
archives with zstd 1.5.7. The standalone libSystem archive SHA-256 is
`2b5eadab3b94f3b3a5e2b3e74cba7157fc01fe775f915ca24fd4e771642a02f4`.
The composed SDK SHA-256 is
`8117d4ff1e17befb7dfe306dd862a3ba39f6f6c64d320987a4fed4c1c33ec5c2`.
Its 5,252 logical members match the archive used for the consumer runs,
including file contents, executable modes and link targets. Normalization
removed 5,252 AppleDouble entries and the macOS extended attributes.
See `/tmp/sdk-normalized-qualification.LkoaBE/receipt.json`.

The noncancelable close runtime fixture also checks arm64 directly. Both
pre-alias links failed solely on `_close$NOCANCEL`. The same client object
per target and minimum linked against the candidate and Xcode reference
and imported that name from libSystem. All eight executables closed a valid
pipe descriptor, then observed `EBADF` on the second close on macOS 26.5.2
(native arm64 and Rosetta x86_64, minima 11.0 and 26.5). Reports are in
`/tmp/xnu-close-qual.7LUZ35/runtime-close`.
