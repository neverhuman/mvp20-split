# BP-04 Planning History

Archived first draft at `2026-09-25 13:35:12`. Historical task pairs/percentages are not the active execution tracker. The parent and linked children now own progress. Original scope is preserved below for traceability.

# BP-04 Deterministic Graph Runner

## Canonical Execution Tracker

- Status: **proposed / first draft for user review**; implementation not activated.
- Last refreshed: `2026-09-24 12:01:26` (America/Chicago).
- Owner/scope: Campaign Runtime coordinator, aggregator and recovery modules.
- Parent: [Master Build Tracker](Master%20Build%20Tracker.md); baseline: local architecture and BP-01/BP-01A completed foundation, BP-02 active protocol work.
- Overall implementation: **0%**; 10 equally weighted verified tasks, two per phase. Overall = completed tasks / 10; phase = completed tasks / 2. Drafting earns no implementation credit.
- Current phase/task: none; proposed plan.
- Next task: incorporate review, then verify predecessor gates and run the bounded pre-activation coherence audit before P1/T1.
- Prerequisites: Completed BP-02 durable commits and BP-03 indexed callable tools.
- Completed implementation/evidence: none. All phase gates remain pending.
- Blockers: predecessor gates are not complete; decisions below block only their dependent tasks.
- Human acceptance: draft is available for review; no approval inferred for dependent deployment/provider actions. Campaigns remain autonomous with human changes between campaigns.
- Active exception: none.
- Draft coherence check: `2026-09-24 12:01:26`; ownership, ordering, scoped tests and handoffs checked against [owning architecture](../Architecture/System/Graph_Execution_Model.md). This is not the implementation activation audit.

| Phase / status | Completion | Dependency | Required exit |
|---|---:|---|---|
| P1 Compiler and executable contract / proposed | 0% | Completed predecessor gates and activation audit | T1-T2: Reject ambiguous joins, missing bindings, illegal cycles, invalid loop state, unsupported tools and unbounded fanout before dispatch; equivalent input yields stable plan identity. |
| P2 Frontier and scheduling / proposed | 0% | P1 exit | T3-T4: Parallel independent branches progress; duplicate wakeups do not duplicate activation; restart reproduces frontier; branch predicates bind exact accepted outputs. |
| P3 Aggregation and failure policy / proposed | 0% | P2 exit | T5-T6: Failure on one branch follows declared policy without blocking unrelated work; late/duplicate returns, partial batches and receipt loss cannot fabricate completion. |
| P4 V1 baseline and successor graphs / proposed | 0% | P3 exit | T7-T8: Compare stage/event/state expectations, not JSON shape alone; all-failed population terminates safely; no hidden chemistry/ranking claim; active instructions never hot-swap. |
| P5 Recovery and closeout / proposed | 0% | P4 exit | T9-T10: Required graph scenarios and BP-02 regression subset pass; provenance links include plan/activation/attempt/results; source graph parity limits and deliberate v1 bug fixes remain explicit. |

## Outcome and Boundaries

Execute and inspect a pinned campaign through branches, parallel work, joins and bounded iteration, including the extracted v1 orchestration baseline.

Included: Compiler/plan lock, explicit data bindings and activation identities, interpreter frontier, aggregation policies, failure/external-wait dispositions, recovery and successor admission.

Excluded: LLM reasoning, biological accuracy, arbitrary code execution in nodes, live human graph edits and a second scheduler outside Campaign Runtime.

Primary services retain private state, dependencies, migrations and module READMEs. Public contracts/clients are the only cross-owner dependencies. Any new schema identifies its consumer/migration impact. No broad backend or shared business/ORM package. Later phases refine earlier boundaries under the current task without reopening closed plans.

## Child Work-Package Register

This parent owns outcomes and sequencing. The named packages below are **scoped, not implementation-ready**. The existing task pairs are requirements for child decomposition, not sufficiently detailed coding instructions. Before activating a package, author its canonical child plan with owned objects/API/storage, transition/algorithm decisions, failure/recovery matrix, named fixtures and replacement gates. Parent progress then rolls up verified child deliverables; do not count these task pairs again. No implementation credit is earned here.

| Child / bounded ownership | Implementation | Prerequisite | Scope to decompose |
|---|---:|---|---|
| BP-04.01 / Compiler and executable contract | 0% | Parent predecessor gates | Extend the prototype schema with typed bindings, conditional paths, bounded scatter/iteration, join/completion policies and state references; validate exact registered tool/schema applicability. Compile immutable execution plans/lockfiles with resource bounds and deterministic activation paths; define migration/version consequences for the prototype contract. |
| BP-04.02 / Frontier and scheduling | 0% | BP-04.01 exit | Implement a runtime-owned coordinator deriving eligible activations from committed state; preserve single-active-campaign and finite fanout/budget limits. Implement branch/skip/iteration transitions and dispatch through BP-02 primitives; make checkpoints explicit and reconstructible, not coordinator memory. |
| BP-04.03 / Aggregation and failure policy | 0% | BP-04.02 exit | Implement joins/aggregation receipts identifying exact accepted members and terminal/partial policy; distinguish FAILED, ABSTAIN, SKIPPED, CANCELLED and pending scientific receipts. Support deterministic retry/stop/fallback, correlated synthetic external waits, cancellation and unknown-effect dispositions without automatic resubmission. |
| BP-04.04 / V1 baseline and successor graphs | 0% | BP-04.03 exit | Turn BP-01A source graph into runnable synthetic adapters, explicit data/state bindings and semantic assertions for zero/two generations, rejected mutations and ordered result association. Validate successor graph proposals/carried-state mappings after current-run termination and reconcile all attempts; preserve historical graph pins and failure deviations. |
| BP-04.05 / Recovery and closeout | 0% | BP-04.04 exit | Run separate-process scenarios around activation, aggregation and iteration commits; verify simultaneous valid completions, revision conflicts and restart through public APIs. Publish read/command seams for BP-05, module replacement boundaries and scoped audit; archive only after the full deterministic fixture set passes. |

Readiness gaps are the unresolved decisions below plus concrete storage/API contracts, algorithm choices, test oracles and migration/recovery obligations for each package. Decompose the nearest eligible package first; do not invent distant provider, ontology or deployment decisions merely to fill templates. Child scope remains here until a linked execution plan replaces the register entry. The parent's existing percentages remain 0% because no implementation has occurred.

## Ordered Tasks

### P1 ? Compiler and executable contract

**T1.** Extend the prototype schema with typed bindings, conditional paths, bounded scatter/iteration, join/completion policies and state references; validate exact registered tool/schema applicability.

**T2.** Compile immutable execution plans/lockfiles with resource bounds and deterministic activation paths; define migration/version consequences for the prototype contract.

**Exit:** Reject ambiguous joins, missing bindings, illegal cycles, invalid loop state, unsupported tools and unbounded fanout before dispatch; equivalent input yields stable plan identity.

### P2 ? Frontier and scheduling

**T3.** Implement a runtime-owned coordinator deriving eligible activations from committed state; preserve single-active-campaign and finite fanout/budget limits.

**T4.** Implement branch/skip/iteration transitions and dispatch through BP-02 primitives; make checkpoints explicit and reconstructible, not coordinator memory.

**Exit:** Parallel independent branches progress; duplicate wakeups do not duplicate activation; restart reproduces frontier; branch predicates bind exact accepted outputs.

### P3 ? Aggregation and failure policy

**T5.** Implement joins/aggregation receipts identifying exact accepted members and terminal/partial policy; distinguish FAILED, ABSTAIN, SKIPPED, CANCELLED and pending scientific receipts.

**T6.** Support deterministic retry/stop/fallback, correlated synthetic external waits, cancellation and unknown-effect dispositions without automatic resubmission.

**Exit:** Failure on one branch follows declared policy without blocking unrelated work; late/duplicate returns, partial batches and receipt loss cannot fabricate completion.

### P4 ? V1 baseline and successor graphs

**T7.** Turn BP-01A source graph into runnable synthetic adapters, explicit data/state bindings and semantic assertions for zero/two generations, rejected mutations and ordered result association.

**T8.** Validate successor graph proposals/carried-state mappings after current-run termination and reconcile all attempts; preserve historical graph pins and failure deviations.

**Exit:** Compare stage/event/state expectations, not JSON shape alone; all-failed population terminates safely; no hidden chemistry/ranking claim; active instructions never hot-swap.

### P5 ? Recovery and closeout

**T9.** Run separate-process scenarios around activation, aggregation and iteration commits; verify simultaneous valid completions, revision conflicts and restart through public APIs.

**T10.** Publish read/command seams for BP-05, module replacement boundaries and scoped audit; archive only after the full deterministic fixture set passes.

**Exit:** Required graph scenarios and BP-02 regression subset pass; provenance links include plan/activation/attempt/results; source graph parity limits and deliberate v1 bug fixes remain explicit.

## Test Ownership and Evidence

Proposed suite locations (create with their modules):

- `contracts/campaigns/tests/`.
- `services/campaign_runtime/tests/compiler/`.
- `services/campaign_runtime/tests/coordinator/`.
- `services/campaign_runtime/tests/aggregation/`.
- `tests/integration/graph_runner/`.

Each owning README maps public behavior, invariants, failure scenarios and measured source paths to module-local test suites. Register source/suite ownership in `dev/test_scopes.json`; extend granular selectors as modules arrive. Run changed-module tests first, affected consumers next, and separate public-boundary integration/E2E only for cross-owner outcomes. Record line and branch coverage with gaps; coverage percentages are not evidence of scientific correctness.

Keep scenario evidence with absolute timestamps, implementation revision, fixture/schema identity, relevant run/artifact IDs and observed outcomes. Unit mocks do not replace required database, process, browser or provider evidence. Record independent build/install and replacement tests for new service/tool boundaries.

## Decisions and Handoff

P1 must select precise scatter/join/partial-result semantics before compiler code. BP-06 later supplies real domain receipts through the existing wait contract; fixture receipts in this plan are labeled synthetic. BP-05 receives stable inspection and next-campaign command boundaries.

## Progress, Scope Changes and Closeout

The canonical tracker owns overall and P1-P5 percentages; mirror them in MBT at every completed task or changed scope and before commit/handoff. Do not activate downstream phases before their predecessor gate. Record review changes and denominator adjustments here; substantial newly discovered scope gets a named successor.

Final phase includes a component-scoped architecture drift audit. Fix blocking drift, explicitly assign nonblocking follow-ups, update module READMEs/inventories and archive only after all defined gates pass. Synchronize MBT, plan index and Restore and repair moved links. Preserve separate acceptance/operational/scientific readiness status; 100% measures this bounded implementation, not the whole product.

Closeout evidence: pending. No implementation, deployment or scientific validation is claimed by this draft.
