# macOS SDK 26.5 C headers for review

21 SDK paths lack an approved disposition, plus
0 installed headers absent from this SDK.
Probe reach is recorded but does not approve an extra header:
it can itself change __has_include behavior.
An installed path
still needs a source and scope review; a missing path needs a
supported include or omit decision. New SDK paths always need review.

## Root-level (10)

- `AppleTextureEncoder.h` — proposed review
- `bootstrap.h` — proposed review — launchd publishes servers/bootstrap.h, but the SDK also has a distinct root bootstrap.h; its first-party install source is unresolved.
- `cache.h` — proposed review
- `cache_callbacks.h` — proposed review
- `profile.h` — proposed review
- `string_x86.h` — proposed include
- `sysdir.h` — proposed review
- `timingsafe.h` — proposed include
- `unwind_arm_ehabi.h` — proposed review
- `usbuf.h` — proposed review

## `os/` (7)

- `os/activity.h` — proposed review
- `os/arch/arm64.h` — proposed review
- `os/log.h` — proposed review — XNU provides only a kernel-side os/log.h; public user header source remains unresolved.
- `os/security_config.h` — proposed include
- `os/signpost.h` — proposed review
- `os/trace.h` — proposed review — XNU provides only a kernel-side os/trace.h; public user header source remains unresolved.
- `os/trace_base.h` — proposed review

## `libDER/` (2)

- `libDER/DERItem.h` — proposed review
- `libDER/libDER_config.h` — proposed review

## `bsm/` (1)

- `bsm/audit_session.h` — proposed review — Absent from XNU and OpenBSM public header installs; first-party source remains unresolved.

## `infiniband/` (1)

- `infiniband/verbs.h` — proposed review

## Installation-only headers needing review
