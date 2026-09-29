# BP-04 Deterministic Graph Runner

## Canonical Parent Tracker

- Status: primary_active; BP-04.03 / Build / B2.
- Last refreshed: `2026-09-28 20:50:52` (America/Chicago).
- Owner/scope: Campaign Runtime coordinator, aggregator and recovery modules.
- Authority: [Master Build Tracker](Master%20Build%20Tracker.md); [planning readiness and handoffs](Planning_Readiness.md).
- Prerequisites: Completed BP-02 durable commits and BP-03 indexed callable tools.
- Implementation: **45%**, 9/20 verified child deliveries. Each child owns four deliveries; this parent counts them once. Parent phase Pn equals child .0n overall completion; child Build/Acceptance phases remain canonical in that child.
- Design maturity: all immediate children have owned objects, public boundaries, algorithms, failure oracles, replacement gates and named decision limits. Reconcile predecessor versions before activation; this is not implementation evidence.
- Current implementation task: BP-04.03/B2 aggregate policy and external-wait execution/retention integration. B1 boundaries passed 920 tests/thirteen installs/REC-01..09; v3 admission remains gated. Next: .03/B3 failure/race proof.
- Demonstrated behavior: .01 closed/audited: compiler, 111-case semantic proof and actual public peer/fresh replacement acceptance passed, including manual numerical plan identity, scoped availability and bounded constructs. .02 closed/audited: durable advancement/hosting, 60 scheduling tests/eight actual coordinator-process cases and eight installed graph/tool/Artifact/replacement cases passed. Richer policies remain .03.
- Blockers: none for the synthetic compiler scope; predecessor BP-02/BP-03 gates passed. Later external choices remain at named gates.
- Human acceptance: no routine approval pause for authorized engineering work; host/provider/data decisions still govern their dependent actions.
- Planning review: `2026-09-25 13:35:12`; parent/child scope, evidence tiers and dependencies reconciled. Active BP-02 implementation position remains unchanged by this roadmap review.

## Outcome and Boundaries

Execute and inspect a pinned campaign through branches, parallel work, joins and bounded iteration, including the extracted v1 orchestration baseline.

Included: Compiler/plan lock, explicit data bindings and activation identities, interpreter frontier, aggregation policies, failure/external-wait dispositions, recovery and successor admission.

Excluded: LLM reasoning, biological accuracy, arbitrary code execution in nodes, live human graph edits and a second scheduler outside Campaign Runtime.

Primary services retain private state, dependencies, migrations and module READMEs. Public contracts/clients are the only cross-owner dependencies. Any new schema identifies its consumer/migration impact. No broad backend or shared business/ORM package. Later phases refine earlier boundaries under the current task without reopening closed plans.

## Canonical Children and Phase Mirror

| Parent phase / child | Overall | Build | Acceptance | Prerequisite |
|---|---:|---:|---:|---|
| P1 / [BP-04.01 Compiler and executable contract](BP-04/Completed/BP-04.01%20Compiler%20and%20executable%20contract.md) | 100% | 100% | 100% | Closed/audited |
| P2 / [BP-04.02 Frontier and scheduling](BP-04/Completed/BP-04.02%20Frontier%20and%20scheduling.md) | 100% | 100% | 100% | Closed/audited |
| P3 / [BP-04.03 Aggregation and failure policy](BP-04/BP-04.03%20Aggregation%20and%20failure%20policy.md) | 25% | 33.33% | 0% | B1 verified; B2 active |
| P4 / [BP-04.04 V1 baseline and successor graphs](BP-04/BP-04.04%20V1%20baseline%20and%20successor%20graphs.md) | 0% | 0% | 0% | BP-04.03 acceptance |
| P5 / [BP-04.05 Recovery and closeout](BP-04/BP-04.05%20Recovery%20and%20closeout.md) | 0% | 0% | 0% | BP-04.04 acceptance |

Each linked child is the execution tracker for its scope. Build tasks name concrete implementation; acceptance requires independent evidence and a scoped drift audit. Do not repeat the historical task pairs as a second work list. No dependent child starts before its predecessor acceptance gate; independent design review does not activate implementation.

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

Child decisions and the [cross-plan handoff register](Planning_Readiness.md) identify the exact producer, consumer and required proof. Engineering defaults are planning baselines; validate them against real predecessor contracts before coding. External choices are not inferred from examples. Do not weaken a live model, browser, database or target-host gate to a fixture when that environment is unavailable.

## Accounting and Closeout

On `2026-09-25 13:35:12`, the original two-task-per-phase estimate was decomposed into 20 verified deliveries across 5 children. Implementation stays 0%; no previous implementation credit is lost or added. [Planning history](BP-04%20Planning%20History.md) preserves the original scope and denominator. Pure design review earns no implementation credit.

Child closeout archives that child with its audit and repairs links; the parent remains active until all child gates and the integrated parent outcome pass. The last child's acceptance checks the parent handoff without repeating unchanged earlier audits. Keep implementation, human acceptance, operational readiness and scientific validation separate. Update child -> parent -> MBT -> Restore at each delivery/scope change.

## Activation Coherence Audit

`2026-09-28 17:23:58`: corrected_ready after BP-02 and BP-03 closeout. Keep compiler, coordinator and aggregator as focused Runtime-owned modules; public campaign contracts contain only wire DTOs. The initial wire-v1 control graph stays validation-only. .01 introduces explicitly versioned executable definitions/locks with finite predicates, explicit data ports, scoped control constructs and deterministic paths; no arbitrary code or LLM interpretation. .02 adds durable execution of the compiled plan, .03 aggregation/failure/external waits, .04 extracted v1 and successor scenarios, .05 actual recovery/parent closeout. Only .01/B1 is active; all child percentages remain 0%. Scientific/provider/UI/host choices do not block these synthetic contracts.
