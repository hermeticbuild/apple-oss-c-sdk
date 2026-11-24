# Qualify SDK Gen composition inputs

Use this evidence when a framework or stub from a new SDK Gen release changes. Check the result against the [consumer profile](../../../tools/sdk_composition/README.md#consumer-archive).

The [framework recipes](../../../frameworks/README.md) reproduce the
qualified CoreFoundation and audio framework replacements. Each directory
records its own provenance. The stock 27.0 CoreFoundation and AudioToolbox
umbrellas fail the C include checks for this composition.

For consumer qualification with SDK Gen 0.0.4, restrict `___divsc3`,
`___divdc3` and `___divxc3` to `x86_64-macos` in the
`/usr/lib/system/libcompiler_rt.dylib` document inside `usr/lib/libSystem.B.tbd`.
Apply this correction to a local SDK Gen input before composing. Runtime
symbol lookup on macOS 26.5.2 found all three on Intel and none on arm64,
which agrees with the SDK 26.5 target groups. The hermetic-llvm
`libomp_test` exercises the arm64 fallback to LLVM's static builtins.

Use `make -C frameworks test` on a new composition to run each replacement
framework's compile or link probe on both architectures. Audit any new
declaration or export against its own documented inputs.

## Expanded public framework composition

The [expanded composition](../../../tools/sdk_composition/README.md#expanded-framework-trial)
imports SDK Gen 0.0.5's 270 top-level frameworks and adds the local Cocoa
and ApplicationServices bundles. Prepared recipes supply the qualified
frameworks. Path overlays preserve generated assets in CoreServices and
Security. The trial retains the qualified SDK Gen 0.0.4 libSystem and
the existing standalone stubs.

The expanded trial with the Security overlay produced the same archive
twice. Its SHA-256 is
`c573e42bea0f697c1205221394c8f9d40fe547ed7e09752d23d70cfe09509207`.
The installed framework probes and the DNS-SD, resolver, Foundation
macros, and Security API probes passed on arm64 and x86_64. The missing
framework paths and generated header failures below remain open.

`@llvm//tools:clang` with `stage1_from_source` built against the expanded
tree on the remote lane for both architectures. c-ares and curl passed
locally on both CPUs. Curl also passed with its default TLS configuration,
which links Security.

[Arm64 Stage 1](https://app.buildbuddy.io/invocation/ee673ad7-e09e-4bd4-9088-af33f5d1726c)
· [Intel Stage 1](https://app.buildbuddy.io/invocation/5b3acf46-718b-47a5-ac85-7e890e3208be)

| Consumer requirement | Result |
| --- | --- |
| Missing framework stubs | SDK Gen 0.0.5 supplies 26 of the 30 requested names, including Network and ModelIO. The ApplicationServices recipe adds a 27th. Carbon, OpenGL, and private FontServices remain open. |
| Foundation macros | The Foundation recipe delegates the enum, options, and nullability macros to the installed CoreFoundation macros. The composed probe compiles, links, and runs on both CPUs. |
| CoreGraphics | SDK Gen's generated Kernel and DriverKit imports came from shared C typedefs. PR #17 resolves them to public headers. Rebuilding then exposed misplaced callback names, corrected by PR #18. Fresh headers still fail on type dependencies such as `CGError` and `CGFloat`, and incomplete declarations. |
| Security | Apple's 26.5 public umbrella compiles as C and Objective-C. A modular Objective-C++ include compiles and a Security API call runs on both CPUs with SDK Gen's stub. |
| Network | The 0.0.5 umbrella defines C++ linkage macros in Objective-C before importing CoreFoundation. Regeneration with PRs #17 and #18 gets through the repaired Security dependency. Both CPUs then fail because callback typedefs precede types such as `nw_browser_state_t`, and the emitted `nw_ethernet_address_t` array places its bound before the name. |
| AVRouting | SDK Gen lacks `AVCustomDeviceRoute.h`. Apple ships the header on macOS and marks the class unavailable there. DocC lists iOS, iPadOS, Mac Catalyst and visionOS for the class. Header availability and API availability need to be represented separately. |
| ModelIO and MetalKit | MetalKit lacks the historical `MTKModel.h` header path. The generated ModelIO umbrella also needs SIMD. SIMD remains deferred. |

[SDK Gen PR #17](https://github.com/apple-cross-toolchain/apple-sdk-gen/pull/17)
· [SDK Gen PR #18](https://github.com/apple-cross-toolchain/apple-sdk-gen/pull/18)
· [AVCustomDeviceRoute DocC](https://developer.apple.com/tutorials/data/documentation/avrouting/avcustomdeviceroute.json)

The macOS SDK preview workflow from SDK Gen PR #13 landed on the manual
release feature branch after that branch merged. The default branch
therefore has no callable preview. A local restoration on
`cerisier/restore-macos-preview` also accepts an SDK version. GitHub
rejected pushing the workflow with the current OAuth credential because
it lacks `workflow` scope. A local macOS 26.5 crawl of the six reported
frameworks used the merged source and the header fixes from PRs #17 and
#18 for diagnostics.

### Security source closure

Apple's pinned 26.5 Security source supplies the umbrella and its
76-header Security include closure. After the CoreFoundation macro
repairs, the remaining dependencies are `xpc_object_t` in `SecCode.h`,
`CF_CLOSED_ENUM` in `SecureTransport.h`, and the two XNU libDER headers
used by `oids.h`.

Apple's BSD-licensed WebKit compatibility header in the matching 26.5
distribution supplies both forms of `xpc_object_t`. It uses libdispatch's
object macro with Objective-C and a void pointer in C. Both forms match
the Xcode 26.5 type checks on arm64 and x86_64. No Apple OSS libxpc
project or public umbrella was found. The older jceel header carries
Apple's all-rights-reserved notice. Darling publishes its own GPL-3.0-or-later
header. Neither is a recipe input.

The approved standalone C recipes install `xpc/xpc.h` for the object
type and `libDER/DERItem.h` plus `libDER/libDER_config.h` from pinned XNU.
The XPC client API remains open. The libDER receipt identifies the XNU
path and the missing upstream public install rule. The C install passed
386 compile checks and the fenv runtime probe. The SDK path review
reported zero installed files without provenance. Its one required SDK
path absent from the stand-alone install is `tgmath.h`, supplied by the
pinned Clang resource directory in the successful C compile checks.

The Security overlay stages the verified Apple OSS source closure and
keeps the SDK Gen linker stub. It takes `CF_CLOSED_ENUM` from pinned
Swift Corelibs Foundation through the CoreFoundation recipe. An
overlay keeps the source filename when DocC changed its case, as with
`cssmaci.h`. The consumer test calls `SecCopyErrorMessageString` and
passes for arm64 and x86_64.

[Apple OSS Security umbrella](https://github.com/apple-oss-distributions/Security/blob/97c3a4296c1ea06b0fe1877a7e616aa84450b5b2/base/Security.h)
· [Pinned WebKit type fallback](https://github.com/apple-oss-distributions/WebKit/blob/2a36545bf8dd89a417b724184900270fb2f523aa/Source/WTF/wtf/spi/darwin/XPCSPI.h)
· [Pinned XNU libDER headers](https://github.com/apple-oss-distributions/xnu/tree/ac9718fb1af618d5ce8678d0dc6e8a58f252216f/EXTERNAL_HEADERS/libDER)
