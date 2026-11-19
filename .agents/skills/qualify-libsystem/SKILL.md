---
name: qualify-libsystem
description: Reproduce a reviewed macOS libSystem link-stub build, qualify an updated SDK lock or investigate standalone C header and libSystem binding gaps in this repository.
---

Read the [journal](../../../tools/libsystem/progress.md) for the last verified milestone and the [operator commands](../../../tools/libsystem/README.md) for executable entry points. At the fixture milestone only the independently authored interface has a runnable release description. Keep fixture results labeled as such.

- **Clean rebuild.** Fetch and verify the pinned tools and public sources, then use the version's reviewed release lock and C installation. Run the offline producer twice in distinct directories, compare bytes, symlink and manifest, and match the known release receipt. A missing production lock or receipt means the SDK still needs qualification.
- **SDK update.** Retain the prior receipts. Verify the new source lock and probe configurations, generate the complete header backlog and classify it before repair. Use the comparator on every embedded document. Reopen reviewed exceptions when their evidence, target or member set changes.
- **First baseline.** Start without approvals for that version. Run the same census and reference comparison. Trace each required symbol from receipt and client relocation through its verified provider and bind-through library. Use the deterministic commands as they become available; log any missing operation in the journal.

Use [the escalation table](../../../tools/sdk_composition/libsystem-spec.md#when-the-agent-must-ask-corentin) before introducing a source exception, guessing an ABI fact, changing scope or weakening a gate. Supply a stable gap ID, smallest reproducer, source evidence and recommendation. Record the decision and reopening condition. A scratch result becomes a release fact only after the project's evidence and validation requirements are met. For example, a standalone-include exception for a Mach header has no bearing on its dylib exports.

For each fixed cause, rerun the original case on both architectures, recompute the affected backlog, then run the [finish gates](../../../tools/sdk_composition/libsystem-spec.md#validation-loop-and-finish-gate) against the same candidate digest. Update the journal at each checkpoint. The official SDK, live runtime capture and historical conversations have no role in unattended generation.
