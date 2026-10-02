# DER-01 derived publication boundary audit

- Status: aligned; DER-01 closed4/4 (100%).
- Last reviewed: `2026-10-02 12:04:52` (America/Chicago).
- Scope: [DER-01](../Build%20Plans/BP-06/BP-06.03%20Derived%20publication%20prerequisite.md), inside BP-06.03/B1. No parent delivery credit.
- Current gate: none within DER-01;712 installed tests pass with zero failures/errors/skips.
- Next: BP-06.03/B1 Knowledge consumed-input projection and durable publication/receipt orchestration.

## Boundary findings

Data owns immutable upload declarations, exact input catalog checks, current process permission and atomic catalog/lineage/finalization. [Module boundary](../../services/data_artifacts/src/amphora_data_artifacts/derivations/README.md) names state, grants, lock order, routes and replacement obligations. Finalized payload reads traverse both conversion and declared derivation ancestry. No ordinary-finalize bypass or hash-inferred lineage was introduced. Metadata and terminal command receipts remain historical after revocation.

The public SDK uses only public contracts. Derived begin compares the exact returned declaration and descriptor; original command identity/digest bind receipt recovery. Explicit resume inspects before a write. An uncertain stream is not automatically replayed or finalized. Durable caller state, bounded replacement-upload attempts and scientific receipt decisions remain Knowledge/Runtime responsibilities.

Applied artifact_0001..0006 are unchanged; artifact_0007 adds append-only declarations, finalized metadata and input edges. Data service grants deny UPDATE/DELETE on all three tables. Lock order is source-rights scope before capacity/upload/attempt/terminal-command locks. File/peer I/O is outside SQL locks. Legacy identity-converter self-links add no ancestry edge but retain all source rights; distinct-artifact cycles fail closed. Bounds and policy denial are explicit.

Artifacts contracts0.2.0 add10 schema files; all272 predecessor schema bytes and old command canonical fixtures remain unchanged. SDK0.2.0 preserves default legacy behavior. Data0.11.0 requires the new migration for startup/readiness and is the minimum reader after derived publication activation. An older Data implementation is not a supported rollback reader.

## Evidence and limits

- [Transactions](Evidence/BP-06-Knowledge/Derived_Publication_Transactions.json):266 complete Data owner tests; atomic rollback, rights changes during verification, historical replay and legacy regression checks.
- [Recovery](Evidence/BP-06-Knowledge/Derived_Publication_Recovery.json):141 combined tests,94 full SDK and26 focused derivation coverage cases; multi-source revocation/expiry, processing denial, concurrency, immutable SQL grants and cycles.
- Source-process integration: actual Knowledge output, Data/Research/Knowledge HTTP processes and a test-owned SDK producer. Actual committed begin/finalize responses are deliberately discarded; original receipt recovery and process restart preserve identities. Revoked source denies derived payload with403 while metadata remains readable.
- [Installed replacement evidence](Evidence/BP-06-Knowledge/Derived_Publication_Installed.json):278 initial Data,47 replacement Data,94 public SDK,252 initial Knowledge/contracts and41 replacement Knowledge tests;712 total, zero failures/errors/skips. Eight isolated initial/replacement installations exclude peer service implementations.

The test-owned handoff verifies the public boundary. It is not production Knowledge publication orchestration, an owner scientific receipt or Runtime execution acceptance. Data enforces declared lineage; it cannot discover a producer's omitted inputs or certify the claimed transformation. Knowledge must declare every artifact it consumed, including trace outputs and Research applicability contexts. Its current reviewer records direct references only; completing that projection is the first B1 integration task after this prerequisite. No scientific-validity, live-source-license, erasure or target-host durability claim is made.
