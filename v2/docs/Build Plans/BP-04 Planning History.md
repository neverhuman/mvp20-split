# BP-04 Planning History

Design status: historical scope and planning decisions. Last reviewed: `2026-09-28 21:32:01` (America/Chicago).

The first draft was archived at `2026-09-25 13:35:12`. Its ten tasks (five pairs) were replaced by five canonical child plans with four verified deliveries each (twenty parent deliveries). The original task descriptions below preserve scope history; they do not define a second execution tracker. Superseded percentages and active-status instructions have been removed to prevent conflicting progress reports.

Current overall/per-phase percentages, current task and blockers belong to the [canonical BP-04 parent](BP-04%20Deterministic%20Graph%20Runner.md) and its linked child trackers. [MBT](Master%20Build%20Tracker.md) mirrors those values and owns program priority. Update those documents together whenever delivery status changes; do not recreate a parallel live tracker here.

## Completed Milestones

- P1 / [BP-04.01 Compiler and executable contract](BP-04/Completed/BP-04.01%20Compiler%20and%20executable%20contract.md): closed/audited, **100%**. Its completed tracker and evidence remain in `BP-04/Completed/`.
- P2 / [BP-04.02 Frontier and scheduling](BP-04/Completed/BP-04.02%20Frontier%20and%20scheduling.md): closed/audited, **100%**. Its completed tracker and evidence remain in `BP-04/Completed/`.

These are durable completed milestones, not pending first-draft work. New aggregation and external-wait work belongs to [BP-04.03](BP-04/Completed/BP-04.03%20Aggregation%20and%20failure%20policy.md); it does not reopen P1/P2.

## Outcome and Boundaries

Execute and inspect a pinned campaign through branches, parallel work, joins and bounded iteration, including the extracted v1 orchestration baseline.

Included: Compiler/plan lock, explicit data bindings and activation identities, interpreter frontier, aggregation policies, failure/external-wait dispositions, recovery and successor admission.

Excluded: LLM reasoning, biological accuracy, arbitrary code execution in nodes, live human graph edits and a second scheduler outside Campaign Runtime.

Primary services retain private state, dependencies, migrations and module READMEs. Public contracts/clients are the only cross-owner dependencies. Any new schema identifies its consumer/migration impact. No broad backend or shared business/ORM package. Later phases refine earlier boundaries under the current task without reopening closed plans.

## Historical Decomposition

The original scope was decomposed into compiler, scheduling, aggregation, baseline/successor and recovery children. The [parent's child register](BP-04%20Deterministic%20Graph%20Runner.md#canonical-children-and-phase-mirror) now links each authoritative plan and reports its status. Concrete interfaces, failure oracles, migrations and replacement gates live in those children. The historical task pairs below are not counted again in the twenty-delivery denominator.

## Original Scope Tasks (Superseded Execution Sequence)

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

## Original Handoff Intent

The first draft required precise scatter/join/partial-result semantics before compiler code. P1's completed child records that contract work; BP-04.03 owns execution-policy integration. BP-06 later supplies real domain receipts; fixture receipts are labeled synthetic. BP-05 receives stable inspection and next-campaign command boundaries.

## Progress, Scope Changes and Closeout

The canonical parent and child trackers own overall and phase percentages; MBT mirrors them at every completed task or changed scope and before commit/handoff. Record durable planning/denominator changes here; substantial newly discovered scope gets a named successor.

Final phase includes a component-scoped architecture drift audit. Fix blocking drift, explicitly assign nonblocking follow-ups, update module READMEs/inventories and archive only after all defined gates pass. Synchronize MBT, plan index and Restore and repair moved links. Preserve separate acceptance/operational/scientific readiness status; 100% measures this bounded implementation, not the whole product.

P1/P2 closeout evidence is in their completed children linked above. Remaining closeout gates are owned by their respective child plans; historical drafting does not establish scientific or deployment validity.

`2026-09-29 09:04:11`: P3 / [BP-04.03](BP-04/Completed/BP-04.03%20Aggregation%20and%20failure%20policy.md) closed/audited at 100% (4/4). Canonical parent owns subsequent progress; no live tracker is maintained here.

`2026-09-29 12:52:29`: User approved .04A typed Artifact/collection prerequisite. Parent scope expanded from five children/twenty deliveries to six children/twenty-four deliveries; completed 12 deliveries preserved, progress rebaselined 60% -> 50%. Current order .01/.02/.03/.04A/.04/.05; parent phases P4/P5/P6 now bindings/baseline/recovery. Canonical trackers own subsequent progress.

`2026-09-29 13:25:53`: .04A/B1 verified; one additional delivery under the approved denominator (13/24). Contract/compiler boundary and unchanged predecessor schema evidence are recorded in the canonical child. B2 durable conversion is next; P1/P2/P3 remain closed.

`2026-09-29 15:52:36`: .04A/B2 verified (14/24 total deliveries); explicit protected Artifact conversions and dynamic two-iteration worker graph passed. B3 actual process failure proof follows; canonical trackers own current percentages.

`2026-09-29 16:08:36`: .04A/B3 verified (15/24 total deliveries). Five actual process cases, independent negative input/source-cut oracles and reverse-order two-iteration execution passed within 59 scoped tests. V1 installed peers/replacement is next; no closed phase reopened.

`2026-09-29 16:25:58`: .04A closed 4/4 after installed acceptance and scoped drift audit; parent 16/24. BIND-01 resolved. .04 reactivation audit corrected_ready, B1 active 0/4; v1 source hashes still match.

`2026-09-29 16:59:32`: .04/B1 verified (17/24 parent deliveries). Five standalone synthetic stage tools and exact source-derived graph oracles; 1146 regression tests/nineteen independent installs. B2 successor policy is next; scientific execution authority remains excluded.

`2026-09-29 17:35:32`: .04/B2 verified (18/24 parent deliveries). Exact successor admission and carried-state compatibility, immutable parent history and source-derived split campaign; 1169 tests/nineteen installs. B3 process proof is next. Corrected two MBT historical row totals to their owning milestones: .04A/B2 14/24 and .04A/V1 16/24; no current credit changed by those repairs.

`2026-09-29 17:45:46`: .04/B3 verified (19/24 parent deliveries). 116 scoped tests, five actual process cases and independent source trace after interruption. Production unchanged since B2; V1 actual installed new-tool/peer replacement is next.
