# macOS SDK 26.5 C headers for review

17 SDK paths lack an approved disposition, plus
0 installed headers absent from this SDK.
Probe reach is recorded but does not approve an extra header:
it can itself change __has_include behavior.
An installed path
still needs a source and scope review; a missing path needs a
supported include or omit decision. New SDK paths always need review.

## Root-level (7)

- `AppleTextureEncoder.h` — proposed review — Standalone C scope and public source remain unproven; do not infer ownership from the SDK path alone.
- `bootstrap.h` — proposed review — launchd publishes servers/bootstrap.h, but the SDK also has a distinct root bootstrap.h; its first-party install source is unresolved.
- `cache.h` — proposed review — The pinned HFS tree has an internal cache.h, but no evidence that it is this root SDK header.
- `cache_callbacks.h` — proposed review — No matching pinned Apple OSS header or public installation rule has been identified.
- `profile.h` — proposed review — XNU publishes architecture-specific machine/profile.h, but no rule maps it to the distinct root profile.h path.
- `sysdir.h` — proposed review — Used by CoreFoundation source, but a public Apple OSS header source and install rule remain unlocated.
- `usbuf.h` — proposed review — No matching pinned Apple OSS header or public installation rule has been identified.

## `os/` (6)

- `os/activity.h` — proposed review — Public user-level logging header source and install rule remain unlocated.
- `os/arch/arm64.h` — proposed include — Installed from XNU with a recorded provenance gap: the os/arch public CopyFiles phases are empty. The SDK 26.5 header also drops bridgeos unavailability from two declarations.
- `os/log.h` — proposed review — XNU provides only a kernel-side os/log.h; public user header source remains unresolved.
- `os/signpost.h` — proposed review — Public user-level logging header source and install rule remain unlocated.
- `os/trace.h` — proposed review — XNU provides only a kernel-side os/trace.h; public user header source remains unresolved.
- `os/trace_base.h` — proposed review — Public user-level tracing header source and install rule remain unlocated.

## `libDER/` (2)

- `libDER/DERItem.h` — proposed include — XNU includes this file under EXTERNAL_HEADERS, but no public usr/include/libDER installation rule has been proven.
- `libDER/libDER_config.h` — proposed include — XNU includes this file under EXTERNAL_HEADERS, but no public usr/include/libDER installation rule has been proven.

## `bsm/` (1)

- `bsm/audit_session.h` — proposed review — Absent from XNU and OpenBSM public header installs; first-party source remains unresolved.

## `infiniband/` (1)

- `infiniband/verbs.h` — proposed review — Likely a separate RDMA library API, but its source and scope decision remain unproven.

## Installation-only headers needing review
