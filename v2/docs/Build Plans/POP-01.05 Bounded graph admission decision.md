# POP-01.05 Bounded graph admission decision

- Status: approved by owner, 2026-10-14 20:57:38 America/Chicago; implementation authorized within the boundary below.
- Reviewed: 2026-10-13 22:34:04 America/Chicago.
- Owner: [POP-01.01/E1](POP-01.01%20Population%20Execution.md), within its original D1/D4 scope.
- Scope: additive admission profile and run-wide claim capacity; no second runner,
  numerical ranking inside Runtime or new chemistry authority.
- Approval basis: POP-01.04 approves population records but explicitly reserves new
  public Runtime commands/profiles for concrete review.
- Implementation checkpoint: Runtime0.68/Deployment0.20.3 generic capacity and
  recovery qualified under E2.1; [evidence](../Audits/POP-01_Bounded_Admission.md).
  Full population dispatch/collection qualification remains E2.2-E2.4.

## Reproduced contract gap

GraphLimits currently contains max_activations and deadline_seconds only. Runtime
claims serialize under the run lock, reserve one attempt-budget unit and check total
available budget. They do not enforce a separate concurrent-invocation limit.
Scatter max_parallel limits active child scopes. Four candidate scopes containing
two independent evaluator nodes may therefore expose eight concurrent invokes;
four is not an enforceable run-wide cap. Reducing worker count does not establish a
durable admission invariant and fails as tools are replicated remotely.

Source: graph-runtime/models.py GraphLimits; lifecycle/claims.py RuntimeLeases.claim;
lifecycle/model.py RunBudget/ActivationState; coordinator/expansion.py scatter;
lifecycle/settlement.py and completion/recovery.py for reservation settlement.
This is a source-level contract finding, not a claim of a failed live deployment.

## Proposed additive public boundary

Introduce a small separate public contract package `campaign_resources`. Its
`AdmitResourceBoundedDraft` root uses a distinct `graph.admit_draft_bounded` command
family and numeric command profile, with the existing draft/plan/input/attempt-budget
fields plus a required `resources` object:

```json
{
  "profile": "campaign-invocation-cap-v1",
  "max_active_attempts": 4
}
```

The range is1..8 for this profile. Proposed endpoint:
`POST /v1/graph-drafts/admit-bounded`, same scoped admission permission and standard
CommandReceipt as draft admission. It reuses existing draft validity/current-universe,
one-active-campaign, plan/input and budget checks in the same admission transaction.
No population semantics are embedded in this generic resource DTO.

Keep old GraphLimits, admission DTOs, command families, canonical bytes and receipt
replay unchanged. Old runs have no new cap and never acquire one through a process
configuration default. The new immutable admission snapshot explicitly selects the
profile. Within-run generation transitions still use authored iteration; this is not
one new run per candidate or generation. Existing successor/carry admissions remain
unchanged and are not silently redirected through this endpoint.

## Claim and recovery invariant

For new-profile runs, acquire the existing run lock, replay any existing claim
receipt first, reconcile eligible expired reservations through existing owner rules,
then require `reserved < max_active_attempts` before issuing a new lease/reservation.
The reserved attempt counter is campaign-wide across tool releases and nested graph
scopes. Include orchestration tool invocations; control nodes and Artifact conversion
work do not acquire worker leases and retain their separate budgets.

At capacity return the existing no_eligible_work receipt without incrementing fence,
attempt count, dispatch cursor, reserved or spent. A later poll uses a fresh command
ID; replay of the old no-work receipt stays exact. Do not hold a SQL transaction while
waiting for capacity or performing Artifact I/O. Queue/scatter creation can remain
bounded ahead of claims under the existing activation ceiling; dispatch-slice size
is a separate graph-materialization limit, not concurrent scientific work.

Prepared completion intents retain their slot until owner reconciliation. Pure
expiry/failure/cancellation releases exactly once through existing settlement;
uncertain work remains reserved until resolved. Keep global maintenance across tool
types so a vanished worker does not indefinitely hold capacity solely because no
worker of that same type polls again. A final stale completion must not regain authority.

This caps authorized unsettled attempts, not physical CPU processes. A disconnected
remote process may continue after its lease expires; existing fencing prevents its
stale result from being accepted. Hard remote-process termination is a distinct tool
hosting capability, not a claim this admission contract can honestly make.

## Persistence, compatibility and rollback

Persist the complete new request in the existing immutable input_snapshot; load the
resource profile only from that snapshot under the run lock. No new mutable counter
or duplicated reservation authority is needed. Existing budget reserved/spent remains
the single ledger. Implementation must demonstrate that every prepared/uncertain
transition preserves the declared invariant; do not repair drift by resetting counts.

No SQL migration is expected for the profile itself. Any need discovered for a new
mutable ledger or broader command semantics returns to review. Existing snapshots
remain readable and unchanged. An old Runtime cannot safely execute a new-profile
run. New versions reject unsupported active profiles; the deployment/recovery
preflight must also refuse starting an older binary against an active bounded run.
Older binaries cannot retroactively learn this guard. Drain new-profile runs before
downgrading or roll forward; never silently resume them without the cap.

## Bounded implementation and qualification

1. Publish new DTO/schema/command goldens and rejection cases; pin all old schema
   and command bytes. No changes to legacy worker claim/completion wire formats.
2. Add the focused Runtime profile object/admission path and run-locked claim guard;
   document module ownership and unsupported-profile startup/recovery checks.
3. Prove two concurrent claimers at limit1, heterogeneous tools/nested scopes,
   prepared completion, stale lease, cancellation, uncertainty and recovery. Use
   actual Runtime transactions plus isolated installation/restart, not only mocks.
4. Finalize POP graph-step transport and compiled composition. Admission must retain
   the approved resource cap from the original population specification and reject
   incompatible expanded activation/deadline/attempt bounds before starting work.

The ordinary evaluation declaration work remains within POP-01.04: freeze cohort,
method graph and expansion limits before dispatch; resolve exact intermediate inputs
only after their upstream producer is accepted. That requires explicit declared
occurrence coverage before final selection, not invented future Artifact references.
This decision does not approve a new graph primitive for it; E1 must first demonstrate
composition from existing graph/input/Artifact mechanisms.

## Concrete independent review

[Composition/transition review](../Audits/POP-01_Composition_Transitions.md) and13
Runtime-owned compiler/resource checks now demonstrate the existing topology
primitives, including nested generation/slice/scatter and nineteen-stage multi-input
processes. These are synthetic compiler adapters, not implemented scientific workers.
The campaign-wide cap gap remains; no new graph primitive is proposed. D4
composition/resource/write-set units are complete; this decision is the remaining gate.

## Owner decision

Owner replied "Approve" to this concrete boundary. Publish and qualify the additive
contract in E1/D4, then implement Runtime admission and reservation enforcement in
E2. Approval is not implementation or acceptance evidence.

Approve the additive `graph.admit_draft_bounded` contract/route and immutable resource
profile, with legacy bytes preserved and Runtime as the only reservation authority.
The alternative is to defer population execution; worker counts and scatter limits
cannot honestly satisfy the existing campaign-wide invocation requirement.
