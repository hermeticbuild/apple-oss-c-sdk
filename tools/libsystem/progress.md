# libSystem implementation journal

## Current handoff

The macOS 26.5 specification is in review. The production generator and local skill are planned deliverables. Once implementation starts, the next milestone is to freeze the inputs and prove the producer and review commands on fixtures before running the full inventory. [Implementation sequence](../sdk_composition/libsystem-spec.md#implementation-sequence-and-evidence-required-to-advance)

## 2026-11-19 · Specification review · macOS 26.5 · arm64 and x86_64

- **Finding.** The official LLVM 23.1.2 Apple Silicon archive includes InstallAPI and tools for both client targets. Its builtins archive has an arm64 slice. The x86_64 reference link for the three tested division helpers succeeded with libSystem alone. A separate Intel static runtime remains conditional on an observed need. [Toolchain experiment](../sdk_composition/libsystem-spec.md#one-official-llvm-toolchain-for-generation)
- **Decisions.** Qualify the published 11–26.5 deployment range by differential linking and record the OS builds actually executed. Evidence-backed omissions and narrowly reviewed runtime provider facts are permitted. Frameworks come from Apple SDK Gen for this milestone. [Decision record](../sdk_composition/libsystem-spec.md#decisions-and-recommendation-for-review)
- **Workflow.** Deliver the tools before the full inventory. The agent must ask before departing from an upstream rule, weakening a gate, or taking any of the other decisions in the escalation table. The local skill must support a clean rebuild, SDK update and first baseline. [Escalation policy](../sdk_composition/libsystem-spec.md#when-the-agent-must-ask-corentin) · [Skill workflow](../sdk_composition/libsystem-spec.md#maintainer-and-agent-procedure)
- **Next action.** Review the plan, then implement the locked-toolchain capability check. The complete libSystem release gate is still unverified.
