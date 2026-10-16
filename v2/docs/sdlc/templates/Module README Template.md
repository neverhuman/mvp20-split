# <Module Name>

- Document role: implementation contract beside source; link intended design through the owning architecture document. Distinguish actual behavior from planned or missing behavior.
- Design status: planned | partial | implemented | deprecated | disputed
- Last reviewed: YYYY-MM-DD HH:mm:ss (America/Chicago)
- Owner / owning architecture / plan: <links>

## Purpose and Responsibilities

Behavior owned, invariants and failure modes. State explicit non-responsibilities and where adjacent behavior belongs.

## Public Contracts

Name the independent package/build/deployment boundary and allowed public imports/clients. List forbidden cross-owner dependencies and the enforcement check. Document service-owned schema/role and public event/read surfaces; shared database hosting does not grant access to adjacent private tables. For tools, bind descriptor, release/image digest, deployment profile and supported invocation protocols; replicas are runtime capacity, not new capability definitions.

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

## Owned Test and Coverage Map

List the module-local test folders, behavior/invariants and negative/failure scenarios they cover, source paths measured, focused test/coverage commands, and untested boundaries. Register ownership in `dev/test_scopes.json`. Keep integration/E2E scope explicit. Link coverage evidence without equating line coverage or passing test count with behavioral completeness. Preserve these acceptance boundaries during replacement.
