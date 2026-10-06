# BP-07 Autonomous LLM Campaign Supervision

## Canonical Parent Tracker

- Status: primary_active; BP-07.04/B2.01b public request/frame profiles.
- Last refreshed: `2026-10-05 19:24:50` (America/Chicago).
- Owner/scope: Agent Planning plus runtime-owned engagement and decision modules.
- Authority: [Master Build Tracker](Master%20Build%20Tracker.md); [planning readiness and handoffs](Planning_Readiness.md).
- Prerequisites: Completed BP-03 discovery, BP-04 runner, BP-05 UI and BP-06 source/knowledge receipts.
- Implementation: **65.42%** scoped;13/20 closed deliveries. BP-07.01/.02/.03 complete; BP-07.04=27.08%; BP-07.05 remains0%. Each child is counted once.
- Design maturity: all immediate children have owned objects, public boundaries, algorithms, failure oracles, replacement gates and named decision limits. Reconcile predecessor versions before activation; this is not implementation evidence.
- Current implementation task: BP-07.04/B2.01 public request/frame profiles, then admitted checkpoint policy.
- Demonstrated behavior: BP-07.01/.02 accepted immutable context/provider/budget and attributed text-decomposition boundaries, current-rights publication, bounded repair and actual Research/Knowledge handoff with replacement recovery. BP-07.03 adds bounded campaign context, semantic proposal policy and durable compiler handoff with actual-owner crash/rights and replacement proof. Runtime supervision and live model quality remain subsequent.
- Blockers: none for deterministic implementation. Approved B2.01 correction: scalar adjustments must reconcile Artifact-only Invoke inputs; see [scalar checkpoint decision](BP-07/BP-07.04%20Scalar%20checkpoint%20decision.md). Live provider/model, egress and spend choices separately govern real calls.
- Human acceptance: no routine approval pause for authorized engineering work; host/provider/data decisions still govern their dependent actions.
- Planning review: `2026-09-25 13:35:12`; parent/child scope, evidence tiers and dependencies reconciled. Active BP-02 implementation position remains unchanged by this roadmap review.


## Outcome and Boundaries

Let an LLM propose bounded campaigns and knowledge decompositions while runtime and domain owners retain acceptance authority.

Included: Context assembly, versioned prompts/models, typed proposals, extraction evaluation, durable engagements, relevance-aware staleness, bounded repairs/fallbacks and autonomous terminal outcomes.

Excluded: Model-created tools executing without review, widened permissions, arbitrary code execution, human approval waits during campaigns and unbounded recursive model loops.

Primary services retain private state, dependencies, migrations and module READMEs. Public contracts/clients are the only cross-owner dependencies. Any new schema identifies its consumer/migration impact. No broad backend or shared business/ORM package. Later phases refine earlier boundaries under the current task without reopening closed plans.

## Canonical Children and Phase Mirror

| Parent phase / child | Overall | Build | Acceptance | Prerequisite |
|---|---:|---:|---:|---|
| P1 / [BP-07.01 Model and engagement contracts](BP-07/Completed/BP-07.01%20Model%20and%20engagement%20contracts.md) | 100% | 100% | 100% | Parent predecessor gates |
| P2 / [BP-07.02 Reliable text decomposition](BP-07/Completed/BP-07.02%20Reliable%20text%20decomposition.md) | 100% | 100% | 100% | BP-07.01 acceptance |
| P3 / [BP-07.03 Campaign proposals and context](BP-07/Completed/BP-07.03%20Campaign%20proposals%20and%20context.md) | 100% | 100% | 100% | BP-07.02 acceptance |
| P4 / [BP-07.04 Durable supervisor and races](BP-07/BP-07.04%20Durable%20supervisor%20and%20races.md) | 27.08% | 36.11% | 0% | BP-07.03 acceptance |
| P5 / [BP-07.05 Live evaluation and closeout](BP-07/BP-07.05%20Live%20evaluation%20and%20closeout.md) | 0% | 0% | 0% | BP-07.04 acceptance |

Each linked child is the execution tracker for its scope. Build tasks name concrete implementation; acceptance requires independent evidence and a scoped drift audit. Do not repeat the historical task pairs as a second work list. No dependent child starts before its predecessor acceptance gate; independent design review does not activate implementation.

## Test Ownership and Evidence

Proposed suite locations (create with their modules):

- `services/agent_planning/tests/context/`.
- `services/agent_planning/tests/proposals/`.
- `services/agent_planning/tests/extraction/`.
- `services/campaign_runtime/tests/supervision/`.
- `tests/integration/autonomous_supervision/`.

Each owning README maps public behavior, invariants, failure scenarios and measured source paths to module-local test suites. Register source/suite ownership in `dev/test_scopes.json`; extend granular selectors as modules arrive. Run changed-module tests first, affected consumers next, and separate public-boundary integration/E2E only for cross-owner outcomes. Record line and branch coverage with gaps; coverage percentages are not evidence of scientific correctness.

Keep scenario evidence with absolute timestamps, implementation revision, fixture/schema identity, relevant run/artifact IDs and observed outcomes. Unit mocks do not replace required database, process, browser or provider evidence. Record independent build/install and replacement tests for new service/tool boundaries.

## Reference Refinement

`2026-09-25 13:54:17`: BP-07.02/.03 now preserve extraction/repair provenance, distinguish inferred from source-stated values, and bind proposed experiment steps to exact unmet question criteria. Model answers cannot self-certify scientific sufficiency or bypass between-campaign human changes. See [reference assessment](References/Amphora_Lab_Insights.md). Added requirements refine existing child B1-B3 deliveries; each child V1 gate includes them. No task is complete, implementation remains 0%, and the denominator is unchanged.

## Decisions and Handoff

Child decisions and the [cross-plan handoff register](Planning_Readiness.md) identify the exact producer, consumer and required proof. Engineering defaults are planning baselines; validate them against real predecessor contracts before coding. External choices are not inferred from examples. Do not weaken a live model, browser, database or target-host gate to a fixture when that environment is unavailable.

## Accounting and Closeout

On `2026-09-25 13:35:12`, the original two-task-per-phase estimate was decomposed into 20 verified deliveries across 5 children. Implementation stays 0%; no previous implementation credit is lost or added. [Planning history](BP-07%20Planning%20History.md) preserves the original scope and denominator. Pure design review earns no implementation credit.

Child closeout archives that child with its audit and repairs links; the parent remains active until all child gates and the integrated parent outcome pass. The last child's acceptance checks the parent handoff without repeating unchanged earlier audits. Keep implementation, human acceptance, operational readiness and scientific validation separate. Update child -> parent -> MBT -> Restore at each delivery/scope change.
