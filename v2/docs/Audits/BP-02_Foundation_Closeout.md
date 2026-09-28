# BP-02 Durable Foundation Closeout

- Status: aligned; parent complete at 100%, 32/32 implementation deliveries.
- Reviewed: `2026-09-28 13:41:06` (America/Chicago).
- Scope: prepared synthetic invocation foundation, two isolated durable services and public-boundary recovery/replacement.

| Child | Deliveries | Scoped evidence |
|---|---:|---|
| Contracts/command identity | 5/5 | [Canonical encoding and boundary audit](BP-02.01_Contracts_Closeout.md) |
| Isolated persistence | 5/5 | [Owner roles, migrations, constraints and transaction audit](BP-02.02_Persistence_Closeout.md) |
| Artifact publication/retention | 5/5 | [Bytes, catalog, protection and maintenance audit](BP-02.03_Artifact_Service_Closeout.md) |
| Invocation lifecycle | 6/6 | [Claims, live fencing, budget and authority audit](BP-02.04_Invocation_Lifecycle_Closeout.md) |
| Completion/delivery | 6/6 | [Atomic acceptance, retention proof, outbox and reads audit](BP-02.05_Completion_Delivery_Closeout.md) |
| Recovery/integration | 5/5 | [Nine installed recovery/replacement scenarios and final audit](BP-02.06_Recovery_Integration_Closeout.md) |

Earlier child audits retain their historical evidence counts and successor statements; the final recovery audit supplies those actual later proofs. Parent accounting adds each implementation delivery once. Pure design gates remain completed design work, not additional implementation credit.

The foundation now provides independent runtime/artifact packages, public versioned contracts (68 published schema artifacts), separate PostgreSQL ownership, immutable command replay, verified immutable bytes, protective retention, live claims/fences, finite attempt spending, atomic completion/checkpoint acceptance, bounded delivery and scoped history. One RUNNING campaign may contain concurrent prepared activations. General campaign validation still reports `executable=false`; this is not yet a graph interpreter or scientific research engine demo.

Verification: 307 final component tests and lint/import/schema gates pass. The immediately preceding installed gate built eight packages and proved separate original/replacement environments, real public peers, actual process kills and retained-state recovery across REC-01..09. [Preserved evidence](Evidence/BP-02-Recovery/README.md) binds exact tested wheels and public identities. The final change added a requirements-alignment test and documentation, not new production behavior. No owner reaches into a peer's private implementation or tables; tools/workers have no database credentials.

BP-03 receives ToolBinding/ToolDescriptor/Invocation/Completion v1, claim/renew/complete HTTP commands, canonical receipts, verified artifact upload/finalize/read, scoped outcome/retention, finite fence/budget semantics and the replacement harness. It must extend descriptor eligibility/resource/egress and release/deployment identities explicitly; the registry and reusable worker SDK are not implemented by this foundation. A registry recommendation never transfers runtime acceptance authority.

BP-04 receives immutable prepared-run snapshots, activation-local attempts/checkpoints, accepted reports, atomic audit/outbox, current snapshots, original receipts and pinned audit pages. It still owns graph compilation, branch/join/scatter/loop interpretation and v1 orchestration parity. REC-08 proves independent prepared activation recovery, not a general graph frontier compiler.

Operating boundaries and replacement prerequisites are in the [runbook](../../services/campaign_runtime/RECOVERY.md). No scientific validity, real effectful-provider dispatch, enterprise identity, scheduler/RTO, production host, backup restoration or power-loss guarantee is claimed. Those remain explicit BP-03..09 gates and owner choices where named. Existing dev warning and frozen-baseline metadata discrepancy remain scoped nonblocking maintenance. No required BP-02 behavior is missing or silently deferred. Follow-up: none within this closed parent scope.
