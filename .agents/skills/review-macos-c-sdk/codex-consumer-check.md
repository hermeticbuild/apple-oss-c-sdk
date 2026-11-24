# Codex consumer check

The Codex checkout was detached at
`56bb44c05c9b2056642ed356cf847f004519cc95`. Bazel 9.3.3 used a
repository override containing the unpacked macOS 26.5 SDK from
`cb5c723`. The archive SHA-256 is
`4b8bec003afa00e4612d512423790420fa231067f03dc44ec542c95ce5502cbd`.
The override adds the SDK package's Bazel metadata from the corresponding
hermetic-llvm commit.

## Initial build

Bazel analyzed ansi-escape, keyring-store, sandboxing, realtime-webrtc,
the voice host, and the CLI on arm64. When executing those targets, the
pinned LLVM toolchain at `d27493f0386c9d4d28f7b12630cb91b0cdfd20f1`
could not find `cerrno` in the rules_rust process wrapper or `memory` in
AWS-LC. Xcode 26.5 supplies the C++ headers in the SDK location that
this pin expects. The build was stopped after capturing both compiler errors.

The second pass uses the previously qualified hermetic-llvm commit
`190fc9f5df9c86ed0f1db77e408381f427dcb829` and
`--@llvm//config:macos_libcxx_headers=llvm`. Both overrides are command
line options for the experiment. The SDK archive and Codex sources stay
on their recorded revisions.
[hermetic-llvm PR #978](https://github.com/hermeticbuild/hermetic-llvm/pull/978)

The arm64 ansi-escape and realtime-webrtc test binaries built with this
toolchain and the exact archive. The keyring and sandboxing binaries and
the CLI's schema generator reached the framework link failures below.
The voice host also depends on the failing pkg-config build.

The next pass uses a local diagnostic copy of the SDK repository. It
adds the two existing SDK Gen stubs and removes the two exact
`_pipe2` export rows. The resulting tree serves only the Codex
experiment. The source package, committed composition, and qualified SDK
archive retain their original contents.

## Focused targets

All four suites pass with the diagnostic copy on arm64 and x86_64. The
Intel binaries ran locally under Rosetta.

| Bazel target | SDK surface exercised |
|---|---|
| `//codex-rs/ansi-escape:ansi-escape-unit-tests` | Rust test binary and libSystem linkage |
| `//codex-rs/keyring-store:keyring-store-unit-tests` | Security and its error-message API |
| `//codex-rs/realtime-webrtc:realtime-webrtc-unit-tests` | Rust session implementation |
| `//codex-rs/sandboxing:sandboxing-unit-tests` | CFNetwork and Security linkage, libSystem's Seatbelt exports |

Inspecting the arm64 sandboxing executable confirms that Security supplies the
trust-settings and certificate imports, and libSystem supplies
`sandbox_check`. For local x86_64 tests on Apple Silicon, Bazel also
needs the Intel execution platform:

```sh
bazel --nohome_rc test \
  --override_module="llvm=$LLVM_WITH_HEADER_MODE" \
  --override_repository="llvm++osx+macos_sdk=$SDK_REPO" \
  --@llvm//config:macos_libcxx_headers=llvm \
  --platforms=@llvm//platforms:macos_x86_64 \
  --extra_execution_platforms=@llvm//platforms:macos_x86_64 \
  //codex-rs/ansi-escape:ansi-escape-unit-tests \
  //codex-rs/keyring-store:keyring-store-unit-tests \
  //codex-rs/realtime-webrtc:realtime-webrtc-unit-tests \
  //codex-rs/sandboxing:sandboxing-unit-tests
```

The diagnostic Security and CFNetwork stubs came from SDK Gen 0.0.5.
Their SHA-256 values are
`d39d1ec11da066c0aa9a56612ff22b9f62c664e3524a7a16f859ee8aa6154097` and
`dd56930f3050ce779647aa10a2aba470ba9eed621970c3be9e060344b811fbed`
respectively.

## Voice path

`//third_party/voice:pkg_config_unix` builds on arm64 with the
diagnostic SDK. The resulting tool reports version 0.29.2 and imports
`pipe` from libSystem. The original SDK failed that same dependency
before it could build the voice host.

The four arm64 voice-host tests then reached the real native prefix
action. GLib 2.88.3 failed in `glib/gosxutils.m` because the
Foundation profile lacks `NSPathUtilities`. The required API is
`NSSearchPathForDirectoriesInDomains`, the user-domain bit, and seven
directory constants. A second diagnostic copy adds those declarations.
It uses Apple's public Objective-C API documentation and the numeric
values and underlying type from the pinned Swift Foundation
implementation. Both Objective-C and modular Objective-C++ clients
returned the expected paths on arm64 and x86_64. The same fixture also
passed against Xcode 26.5.
[Apple's directory search documentation](https://developer.apple.com/library/archive/documentation/Cocoa/Conceptual/LowLevelFileMgmt/Articles/StandardDirectories.html)
· [Pinned Swift Foundation enum values](https://github.com/swiftlang/swift-foundation/blob/511394753aa873fd390674301594b4bb8460a74b/Sources/FoundationEssentials/FileManager/SwiftFileManager.swift#L170-L215)

On the next voice attempt, GLib compiled `gosxutils.m` and stopped at
`gio/gcontenttype-osx.m` on `CoreServices/CoreServices.h`. All four
voice test targets failed to build before test execution. The
`voice-host-packaged_runtime-test` fixture also requires a built
`//third_party/voice:native_runtime` exposed through
`CODEX_TEST_VOICE_RUNTIME` before its ignored native initialization
test can be exercised.

The GLib Cocoa selector also builds the following sources in the same
configuration. These are inspected requirements beyond the first
compiler stop.

| Selected source | SDK surface to qualify |
|---|---|
| GLib `gio/gcontenttype-osx.m` | CoreServices uniform type identifier functions and data exports through the umbrella |
| GLib `gio/gosxappinfo.m` | ApplicationServices and its LaunchServices APIs such as `LSCopyApplicationURLsForBundleIdentifier`, plus Foundation bundle and URL methods |
| GLib `gio/gnextstepsettingsbackend.m` | `NSUserDefaults`, autorelease pools, mutable collections, string encodings, and scalar `NSNumber` methods |
| GLib `gio/gcocoanotificationbackend.m` | Cocoa notifications, `NSImage`, and Foundation bundles |
| GStreamer `gst/gstmacos.m` | The AppKit application delegate, `NSApp`, activation policies, and event loop |

SDK Gen 0.0.5's CoreServices umbrella fails in Objective-C on both CPUs.
Its fallback CoreFoundation link macros emit `extern "C"`. After
guarding that syntax, the same include reaches a generated DriverKit
dependency on absent `kernel/kernel.h`. The released stub also lacks the
uniform type identifier data constants used by GLib.
[SDK Gen PR #15](https://github.com/apple-cross-toolchain/apple-sdk-gen/pull/15)
fixes the linkage macros. The CoreServices dependency closure, constant
exports, and ApplicationServices umbrella need separate work. The voice
effort stops here before introducing a larger framework replacement.

## Standalone CLI

The configured action graph for `//codex-rs/cli:codex` has no
`VoiceNativePrefix` or `VoiceNativeRuntime` action. The CLI target reached
its own final Rust executable link. A replay of that Bazel action with
LLD's error limit disabled reported these missing framework inputs and
17 Mach-O imports.

| Framework link input | Missing imports or link requirement |
|---|---|
| CoreGraphics | `CGSessionCopyCurrentDictionary` for the terminal session check |
| LocalAuthentication | The Rust link explicitly requests the framework |
| CoreServices | `FSEventStreamCreate`, `FSEventStreamGetDeviceBeingWatched`, `FSEventStreamInvalidate`, `FSEventStreamRelease`, `FSEventStreamScheduleWithRunLoop`, `FSEventStreamStart`, `FSEventStreamStop`, `FSEventsGetCurrentEventId`, and `FSEventsPurgeEventsForDeviceUpToEventId` |
| AppKit | `NSPasteboardTypeHTML`, `NSPasteboardTypeString`, `NSPasteboardTypeTIFF`, and `NSPasteboardURLReadingFileURLsOnlyKey` |
| IOKit | `IOPMAssertionCreateWithName` and `IOPMAssertionRelease` |
| CoreFoundation | `CFPreferencesAppValueIsForced` |

All named exports exist in SDK Gen 0.0.5. On macOS 26.5.2, each
export resolves through its listed framework on arm64 and x86_64. The
session check resolves through CoreGraphics to SkyLight, and file
watching resolves through CoreServices to FSEvents. Keep the actual
reexports in mind if qualifying a production replacement.
Both IOKit power assertion functions have declarations in the matching
macOS 26.5 Apple OSS IOKitUser gitlink.
[Pinned IOKitUser header](https://github.com/apple-oss-distributions/IOKitUser/blob/23a611d9d194b63465f6df2abfdda63d71c87e97/pwr_mgt.subproj/IOPMLib.h)

The CLI-only diagnostic stages the three missing SDK Gen stubs and
supplements the existing AppKit, IOKit, and CoreFoundation stubs with
just the observed imports. It adds zero framework headers. Replaying the
arm64 Bazel link with this layer produced an executable that printed
`codex-cli 0.0.0`. The ordinary Bazel build then passed on arm64 and
x86_64 using the same SDK repository overlay. Both binaries had the
expected Mach-O architecture, loaded the six framework link inputs, and
ran `--version`. The diagnostic layer remains separate from the
qualified SDK archive.

```sh
for cpu in arm64 x86_64; do
  bazel --nohome_rc build --disk_cache= \
    --override_module="llvm=$LLVM_WITH_HEADER_MODE" \
    --override_repository="llvm++osx+macos_sdk=$CLI_SDK_REPO" \
    --@llvm//config:macos_libcxx_headers=llvm \
    --platforms="@llvm//platforms:macos_$cpu" //codex-rs/cli:codex || exit 1
  bazel-bin/codex-rs/cli/codex --version || exit 1
done
```

## SDK issues for review

| Issue | Evidence | Proposed next step |
|---|---|---|
| Codex's pinned toolchain expects SDK C++ headers | The process wrapper and AWS-LC fail as described above. The SDK intentionally delegates libc++ and libc++abi headers to the toolchain. | Use a hermetic-llvm pin with the tested LLVM header mode in Codex. Keep the mode opt-in. |
| Security is header-only in this SDK | `keyring-store-unit-tests` fails with `framework not found for -framework Security` and an undefined `SecCopyErrorMessageString`. A C client of `Authorization.h` fails on both CPUs. It links against Xcode 26.5 and against the existing SDK Gen 0.0.5 `Security.tbd` used as a diagnostic input. | Qualify the SDK Gen stub against the Rust keyring client before adding it to composition. For clients that compile Security headers, start with the Apple OSS public install rules. |
| CFNetwork is absent | The arm64 `sandboxing-unit-tests` link requests both CFNetwork and Security. Its Security imports also include certificate and trust-settings APIs. SDK Gen 0.0.5 has a CFNetwork stub and contains all four named Security exports. | Qualify both stubs against the sandboxing target. Stage only the linker files while this consumer gets its declarations from Rust. |
| The inherited 27.0 libSystem advertises `pipe2` in a 26.5 archive | Codex's bundled pkg-config configures its internal GLib with `pipe2` enabled, then `glib-unix.c` fails to compile. The composed stub resolves a strong `_pipe2` import on both CPUs. Xcode 26.5 declines the same link. The trial includes that name under both `libsystem_kernel` and `libsystem_sim_kernel`. Runtime lookup on 26.5.2 finds neither `pipe2` nor the related `dup3`, which is also advertised by the stub. [macOS 27 compatibility report](https://github.com/python/cpython/issues/153711) | Select libSystem exports by SDK version and target in the composition. The local diagnostic removes the two exact `_pipe2` entries and reproduces the reference link failure on both CPUs. Keep 27.0 support in the 27.0 generator output. |
| Foundation path-search declarations | GLib's `gosxutils.m` cannot compile the path lookup. The independently sourced header passes the two-architecture path probe. SDK Gen 0.0.5's generated Foundation header repeats the type name for every case in `NSSearchPathDirectory`. | Add the tested header profile after review. [SDK Gen PR #14](https://github.com/apple-cross-toolchain/apple-sdk-gen/pull/14) fixes case names. Qualify numeric values independently. |
| CoreServices header, typed data exports, and dependencies | The native voice failure and two-architecture umbrella probe are recorded above. Guarding C linkage fixes one generator defect. | Qualify the actual CoreServices and LaunchServices header and linker surfaces, including the reexport layout. Check imports against the declared macOS SDK target and avoid treating a DocC module name as a header path. |

[SDK Gen PR #4](https://github.com/apple-cross-toolchain/apple-sdk-gen/pull/4)
already tracks preserving each SDK's Darwin library documents and target
groups. A 26.5 composition still needs a matching version of those export
facts. The SDK Gen 27.0 output remains a different input.

## Codex SDK selection

Codex's `osx.frameworks` names 41 frameworks. The trial contains link
stubs for 12 and the Security authorization header. The other 28
requested framework directories are absent:

```text
ApplicationServices AVFAudio AVFoundation AVRouting CFNetwork ColorSync
CoreGraphics CoreImage CoreMedia CoreServices CoreText CoreVideo DiskArbitration
FontServices ImageIO IOSurface Kernel LocalAuthentication Metal MetalKit
OpenGL OSLog PrintCore QuartzCore ScreenCaptureKit Symbols
UniformTypeIdentifiers VideoToolbox
```

SDK Gen 0.0.5 contains framework directories for 23 of the 28 names.
ApplicationServices, FontServices, Kernel, OpenGL, and PrintCore have no
directory in that release. This is a comparison of the workspace's SDK
selection. Use action and linker diagnostics to decide which names a
specific target needs.

The requested `libproc.tbd` exists as an alias to libSystem. Xcode
26.5 also aliases it to libSystem. The standalone `libsandbox.tbd` is
absent and SDK Gen 0.0.5 has the alias and versioned stub. The trial's
libSystem already exposes the `sandbox_check` and
`SANDBOX_CHECK_NO_REPORT` names called by Codex's Seatbelt tests.

## Local evidence

The diagnostic inputs and logs are in the worktree's
`build/codex-sdk-check.RqcR2E` directory. Its `llvm-upstream-libcxx`
directory supplies `LLVM_WITH_HEADER_MODE`. Use
`sdk-repo-voice-diagnostic` for the focused targets and
`sdk-repo-cli-diagnostic` for the CLI. The full failed-link inventory
is in `arm64-cli-link-replay.log`, and the successful CLI runs are in
the two `*-cli-composed-build.log` and `*-cli-composed-smoke.log` pairs.
