# BP-05 Graph Studio First Vertical Slice

## Canonical Parent Tracker

- Status: primary_active; BP-05.01 / Build / B1.
- Last refreshed: `2026-09-29 18:50:04` (America/Chicago).
- Owner/scope: Studio modules and thin gateway/projection adapters.
- Authority: [Master Build Tracker](Master%20Build%20Tracker.md); [planning readiness and handoffs](Planning_Readiness.md).
- Prerequisites: Completed BP-04 runnable fixture and versioned read/command contracts.
- Implementation: **0%**, 0/16 verified child deliveries. Each child owns four deliveries; this parent counts them once. Parent phase Pn equals child .0n overall completion; child Build/Acceptance phases remain canonical in that child.
- Design maturity: all immediate children have owned objects, public boundaries, algorithms, failure oracles, replacement gates and named decision limits. Reconcile predecessor versions before activation; this is not implementation evidence.
- Current implementation task: BP-05.01/B1 transport/page-model spike and public contract mapping. Next: measured canvas/list prototype.
- Demonstrated behavior: none within this parent. Required database/process/browser/model/host evidence remains pending.
- Blockers: none for B1; frontend/canvas choice is an engineering spike, actual browser evidence is required before dependent gates.
- Human acceptance: no routine approval pause for authorized engineering work; host/provider/data decisions still govern their dependent actions.
- Planning review: `2026-09-25 13:35:12`; parent/child scope, evidence tiers and dependencies reconciled. Active BP-02 implementation position remains unchanged by this roadmap review.

## Outcome and Boundaries

Let a user navigate a real campaign, inspect its evidence and failures, and author the next campaign without interrupting autonomous execution.

Included: Progressive graph exploration, live/replay view models, version-consistent details, bounded draft editing, revision/lineage comparison and emergency termination.

Excluded: A universal dashboard, fabricated knowledge views, active-run human editing, model supervision controls that bypass authority, or a new browser-owned run database.

Primary services retain private state, dependencies, migrations and module READMEs. Public contracts/clients are the only cross-owner dependencies. Any new schema identifies its consumer/migration impact. No broad backend or shared business/ORM package. Later phases refine earlier boundaries under the current task without reopening closed plans.

## Canonical Children and Phase Mirror

| Parent phase / child | Overall | Build | Acceptance | Prerequisite |
|---|---:|---:|---:|---|
| P1 / [BP-05.01 Interaction and transport boundaries](BP-05/BP-05.01%20Interaction%20and%20transport%20boundaries.md) | 0% | 0% | 0% | Parent predecessor gates |
| P2 / [BP-05.02 Graph inspection and navigation](BP-05/BP-05.02%20Graph%20inspection%20and%20navigation.md) | 0% | 0% | 0% | BP-05.01 acceptance |
| P3 / [BP-05.03 Drafts and safe commands](BP-05/BP-05.03%20Drafts%20and%20safe%20commands.md) | 0% | 0% | 0% | BP-05.02 acceptance |
| P4 / [BP-05.04 Visual and integration acceptance](BP-05/BP-05.04%20Visual%20and%20integration%20acceptance.md) | 0% | 0% | 0% | BP-05.03 acceptance |

Each linked child is the execution tracker for its scope. Build tasks name concrete implementation; acceptance requires independent evidence and a scoped drift audit. Do not repeat the historical task pairs as a second work list. No dependent child starts before its predecessor acceptance gate; independent design review does not activate implementation.

## Test Ownership and Evidence

Proposed suite locations (create with their modules):

- `studio/<module>/tests/`.
- `services/control_gateway/tests/`.
- `services/projection_serving/tests/`.
- `tests/integration/studio/`.

Each owning README maps public behavior, invariants, failure scenarios and measured source paths to module-local test suites. Register source/suite ownership in `dev/test_scopes.json`; extend granular selectors as modules arrive. Run changed-module tests first, affected consumers next, and separate public-boundary integration/E2E only for cross-owner outcomes. Record line and branch coverage with gaps; coverage percentages are not evidence of scientific correctness.

Keep scenario evidence with absolute timestamps, implementation revision, fixture/schema identity, relevant run/artifact IDs and observed outcomes. Unit mocks do not replace required database, process, browser or provider evidence. Record independent build/install and replacement tests for new service/tool boundaries.

## UI Reference Refinement

`2026-09-24 12:10:07`: Use the [interaction reference map](../Architecture/Experience/Interaction_References.md) in P1/T1-T2 prototypes and P4 usability checks. Design/Monitor separation and persistent selection refine existing scope; Explore and fitness Compare depend on BP-06/BP-08. Implementation and all phase percentages remain 0%; this refines existing tasks.

## Reference Refinement

`2026-09-25 13:54:17`: BP-05.02 now specifies named, scoped, revision-bound scientific views and matching failure fixtures. Knowledge/lab views use labeled fixtures until BP-06.06 proves the actual owner integration; no graph backend is selected by the reference. See [reference assessment](References/Amphora_Lab_Insights.md). Added requirements refine existing child B1-B3 deliveries; each child V1 gate includes them. No task is complete, implementation remains 0%, and the denominator is unchanged.

## Decisions and Handoff

Child decisions and the [cross-plan handoff register](Planning_Readiness.md) identify the exact producer, consumer and required proof. Engineering defaults are planning baselines; validate them against real predecessor contracts before coding. External choices are not inferred from examples. Do not weaken a live model, browser, database or target-host gate to a fixture when that environment is unavailable.

## Accounting and Closeout

On `2026-09-25 13:35:12`, the original two-task-per-phase estimate was decomposed into 16 verified deliveries across 4 children. Implementation stays 0%; no previous implementation credit is lost or added. [Planning history](BP-05%20Planning%20History.md) preserves the original scope and denominator. Pure design review earns no implementation credit.

Child closeout archives that child with its audit and repairs links; the parent remains active until all child gates and the integrated parent outcome pass. The last child's acceptance checks the parent handoff without repeating unchanged earlier audits. Keep implementation, human acceptance, operational readiness and scientific validation separate. Update child -> parent -> MBT -> Restore at each delivery/scope change.

## Activation Coherence Audit

- Reviewed: `2026-09-29 18:50:04`, baseline ac246d4 plus accepted BP-04.05/V1; result **corrected_ready**. BP-04 closed24/24; no owner input blocks B1.
- Runtime0.11.0/graph-runtime0.5.0/campaigns0.4.0 publish176 schemas. New snapshot/detail/value/event routes require explicit graph/history configuration; API credentials and command authority remain backend-owned. Consume published schemas to generate/validate transport types, not handwritten parallel DTOs.
- First bounded task is `studio/` transport/page-model spike with one loader per region, abort/selection-generation guards, explicit stale/denied/expired states, finite paging and visible incomplete context. Runtime events are resumable invalidations, not UI patches. A changed run invalidates mutable snapshot tokens; do not promise historical mutable frontier retention.
- Read local UI Coding Guidelines and interaction references before presentation. Keep Design/Monitor/Explore/Compare state distinct; live human edits remain forbidden, draft edits apply between campaigns. No fabricated knowledge/scientific views.
- Framework/canvas/version choice requires a measured engineering spike before production UI. B2 must prove200 visible/10000 logical synthetic nodes using bounded expansion, accessible list and preserved selection; B3 actual browser failure/viewport evidence; V1 actual backend integration. Node/npm are locally available; browser automation can be installed locally as needed.
- Existing observations do not expose arbitrary graph traversal or a complete run catalog/authored-topology projection. BP-05.02 must reconcile the precise owner read routes needed for live navigation; B1 uses the accepted run-addressed contracts and explicit transport adapters. Gateway remains thin with backend credentials, no scientific rules, owner SQL or second run database.
- Implementation remains0/16; all phases0%. No new scope or implementation credit from this activation review.
