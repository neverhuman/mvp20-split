# Supervisor request intake

Planning0.74/planning0016 supports explicit planning.supervision.request.v2 alongside original commands. CheckpointIntakeSnapshot validates declared target/read correspondence and field uniqueness; it does not prove Runtime plan membership. Original IntakeSnapshot parser remains closed. Retained snapshot dispatch and family-specific receipt lookup preserve original bytes; default receipt family remains v1. Same command ID across families cannot reinterpret an existing wrapper. Forward0016 extends the family whitelist only. Owned intake180 statements22 branches100% in the145-case combined SQL suite. No attempts/provider grants are created. HTTP/client v2 integration follows.

- Implemented: Planning0.70/planning0015, BP-07.04/B1.04a; reviewed `2026-10-05 15:30:37` (America/Chicago).
- Architecture: [Planning](../../../../../docs/Architecture/Agents/Planning.md).
- Tests: service-owned tests/supervision_intake;17 pure/actualSQL cases,155 statements/20 branches100%.

## Owned behavior

`IntakeSnapshot` revalidates the public supervisor wrapper through existing Planning RequestSnapshot/ContextPolicy. It owns exact original Planning bytes, actor/scope/run/cut/policy/hash binding, bounded structural read-set and lineage shape. Runtime observation/footprint hashes remain authenticated owner claims, not locally proven graph state. No Runtime private module or table is consulted.

`SupervisionIntake.receive(principal, command)` accepts only explicit numeric-v2 planning.supervision.request. It requires record_requests with exact actor/scope. Command-key, scoped decision-slot and existing Planning request-key locks serialize atomic registration of the original Planning request, supervisor wrapper and terminal recording receipt. Exact command replay returns its original operation/receipt. Different bytes for the same command conflict. Existing logical-request/wrapper or decision-slot conflicts produce immutable rejected receipts; unchanged wrappers can be acknowledged by another explicit command without creating a second request or attempt.

The public receipt says recorded, never accepted execution. `request` and `receipt` require read_attempts and original actor/scope, revalidate retained bytes/index fields and recover without a new recording permission. Missing records are distinct from terminal rejection. Legacy PlanningJournal registers and reads the same original request bytes; no predecessor request profile changes.

## State and limits

Forward planning0015 adds SELECT/INSERT-only supervision_requests and supervision_commands. Exact wrapper-to-original-request digest and committed receipt-object foreign keys preserve scoped identity. Wrapper and command bytes remain bounded256KiB; receipt16KiB; ordinal1..16. Original tables/migrations are unchanged. Never run Planning<=0.69 migrators on planning0015. Migration is explicit, never an import/startup side effect. Crash before commit rolls back all three records; no half-intake is acknowledged.

Early/out-of-order or late wrappers may be recorded as original evidence. This does not enroll a repair family, prove ancestry/current eligibility, reserve budget, authorize source processing, create a provider attempt or grant issuance. Those remain existing owner algorithms composed by later B2 supervision. No HTTP server, provider adapter, peer request or Runtime graph effect is implemented here.

## Replacement gate

Preserve exact canonical command/wrapper/original request bytes, command operation IDs, receipts and timestamps. Keep actor/scope checks and command/slot/request lock order. Tests prove atomic rollback, same-command concurrency, conflicting decision-slot concurrency, legacy request interoperability, insert-only grants and zero provider-attempt side effects. B1.04b adds configured HTTP; d proves actual-owner installed exchange. Scientific and live-model claims remain separately gated.


The checkpoint output schema requires the explicit CheckpointRequest wrapper; legacy supervision intake rejects that combination before provider work. Existing checkpoint requests with older output profiles remain readable.

The exact checkpoint-followup-draft output pin requires an explicit CheckpointRequest,
as does checkpoint-draft. Old intake and canonical record bytes remain unchanged.
