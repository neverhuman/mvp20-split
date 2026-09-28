# BP-02 Durable Runtime and Artifact Foundation

## Canonical Parent Tracker

- Status: primary_active; child BP-02.03 / V2 / A6.
- Last refreshed: `2026-09-28 10:56:19` (America/Chicago).
- Implementation: **43.75%**, 14/32 verified implementation deliveries across six children. Parent = sum of verified child task counts / 32. These are scoped delivery fractions, not time/effort estimates. Children own task evidence; parent never adds duplicate credit.
- Design: original T1 protocol decisions complete and retained in [Runtime protocol](../Architecture/System/Runtime_Command_Protocol.md) and [Artifact protocol](../Architecture/System/Artifact_Publication_Protocol.md).
- Demonstrated durable behavior: PostgreSQL isolation, scoped constraints, command contention/rollback/retry verified; artifact publication and its process-kill windows verified; protective reservation handshake verified with a scripted peer; cleanup and real runtime execution/process proof remain required.
- Current task: BP-02.03 A6 independent acceptance; next scoped closeout.
- Blockers: no implementation blocker; user-provided Git identity configured for commit/push. Child predecessor gates mandatory; no user decision required at this point.
- Authority: user approved hierarchical decomposition and autonomous continuation; [MBT](Master%20Build%20Tracker.md) mirrors this tracker.

## Explicit Rebaseline

The previous **8.33% (1/12)** counted a protocol-design task as implementation. That completed work is preserved as design evidence, not erased or reopened. On `2026-09-25 08:09:07`, authorized decomposition separated design, implementation and demonstrated behavior, and expanded the original broad tasks into 34 named verified implementation deliveries. The new implementation baseline is **0%**. [History](BP-02%20History.md) preserves prior scope/checkpoints and the old arithmetic. Update the denominator explicitly if further decomposition changes scope; never disguise missing work with a fixed near-complete percentage.

On `2026-09-25 08:47:38`, the preliminary 34-task register was corrected to **32 implementation deliveries**: S1 physical design and A1 filesystem design remain mandatory but earn design credit only. No implementation task was removed or reclassified as complete.

## Owned Children

| Canonical child | Implementation | Delivery tasks | Gate/state |
|---|---:|---:|---|
| [BP-02.01 Contracts and Command Identity](BP-02/Completed/BP-02.01%20Contracts%20and%20Command%20Identity.md) | 100% | 5 | Closed; audit passed |
| [BP-02.02 Isolated Persistence](BP-02/Completed/BP-02.02%20Isolated%20Persistence.md) | 100% | 5 | Closed; audit passed |
| [BP-02.03 Artifact Publication and Retention](BP-02/BP-02.03%20Artifact%20Publication%20and%20Retention.md) | 80% | 5 | Active A6; A2-A5 passed |
| [BP-02.04 Invocation Lifecycle](BP-02/BP-02.04%20Invocation%20Lifecycle.md) | 0% | 6 | Predecessor gate |
| [BP-02.05 Completion and Delivery](BP-02/BP-02.05%20Completion%20and%20Delivery.md) | 0% | 6 | Predecessor gate |
| [BP-02.06 Recovery and Integration](BP-02/BP-02.06%20Recovery%20and%20Integration.md) | 0% | 5 | Predecessor gate |

Each child has separate V1 build and V2 acceptance phases; implementation and phase percentages are canonical there. BP-02.01 and .02 are closed; BP-02.03 owns the active work. Other children expose concrete bounded deliveries but require their own design/activation gate before implementation. No requirement to invent all future SQL/HTTP details now.

## Parent Outcome and Boundaries

Separate runtime/artifact processes and PostgreSQL-owned state support prepared synthetic invocations, exclusive claims/fences, bounded budgets, protected immutable artifacts, atomic completion, at-least-once outbox and process-crash recovery. All changes preserve service-owned roles/tables and public contracts, module-local tests and replacement READMEs. No shared backend/ORM, scientific evaluation, graph interpreter, UI or enterprise identity implementation in this parent. General activation stays unavailable until BP-04.

Dependencies: BP-01 and BP-01A complete. Children execute in table order. Final child proves cross-owner integration rather than repeating every earlier unit test. Use real PostgreSQL for transaction/concurrency evidence. Scope and failure requirements from the historical parent remain binding; child decomposition does not remove them.

## Parent Closeout

Archive only when every child gate passes, scoped audits exist, the integrated public-boundary crash matrix passes, READMEs describe actual state and handoffs to BP-03/04 name concrete public contracts. Target-host power-loss/backup objectives remain BP-09; no process-crash test silently establishes those guarantees. Parent final percentage is separate from scientific/product readiness.
