# <Module Name>

- Document role: implementation contract beside source; link intended design through the owning architecture document. Distinguish actual behavior from planned or missing behavior.
- Design status: planned | partial | implemented | deprecated | disputed
- Last reviewed: YYYY-MM-DD HH:mm:ss (America/Chicago)
- Owner / owning architecture / plan: <links>

## Purpose and Responsibilities

Behavior owned, invariants and failure modes. State explicit non-responsibilities and where adjacent behavior belongs.

## Public Contracts

Entry points, typed inputs/outputs, errors/abstention, compatibility and versioning; reference owned schemas rather than duplicating them.

## Data and Dependencies

Reads; writes; owned state and lifecycle; artifact/store boundaries; calls; called by; external side effects. Include configuration and access boundaries without secrets.

## Runtime and Scientific Boundaries

Process/service/transport boundaries; concurrency, retries, recovery and idempotency where relevant; privacy/data classification; scientific applicability and authority where relevant. State what extraction or independent deployment would require.

## Verification and Audit Hooks

Tests/acceptance evidence, relevant generated inventories, architecture claims to compare, and known drift/debt links. Distinguish intended behavior from implemented and last-verified behavior. Update this README when its boundary changes.

## Replacement Contract

This README must let a new implementer rebuild the module without copying its current internals. State:

- Required externally observable behavior and invariants; internal algorithms/structure that may change freely.
- Callers, consumers, owned schema versions, dependency ports and prohibited coupling. Link canonical contracts and representative valid/invalid fixtures.
- Authoritative state versus rebuildable caches; state/schema ownership, checkpoint formats, artifact identity and retention obligations.
- Error/abstention/timeout semantics, ordering, concurrency, idempotency, retry and side-effect boundaries consumers rely on.
- Domain applicability, units, authority limits and evidence obligations that a fresh implementation must preserve.
- Resource/environment assumptions and measured limits, separating actual evidence from intended targets.
- Compatibility tests and end-to-end scenarios required to accept a replacement, including negative and recovery paths where relevant.
- Cutover: drain/finish active work, handle old checkpoints and persistent records, migrate or explicitly reject incompatible versions, and provide rollback/forward-repair behavior. A code rewrite is not authority to delete evidence or owned state.

Record contract changes explicitly with affected consumers and migration requirements. Rebuild behind an unchanged contract when possible; version intentional boundary changes. For initial single-campaign operation, activate module replacements between campaigns. Keep detailed implementation history elsewhere; this section is the current rebuild specification, not a changelog.
