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
