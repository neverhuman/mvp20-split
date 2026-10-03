# BP-06 Knowledge Evidence and Source Loop

## Canonical Parent Tracker

- Status: primary_active; BP-06.01 through BP-06.04 closed; BP-06.05/Build/B1.04c active.
- Last refreshed: `2026-10-03 15:00:03` (America/Chicago).
- Owner/scope: Knowledge, Research and focused Data/Artifacts modules.
- Authority: [Master Build Tracker](Master%20Build%20Tracker.md); [planning readiness](Planning_Readiness.md).
- Prerequisites: completed BP-04 receipt/wait seams, BP-05 inspection and BP-01/02/03 boundaries.
- Scoped implementation/verification completion: **69.10%** = (16 + 7/12)/24; 16/24 closed delivery gates. P1-P4 are 100%; P5 is 14.58%; P6 is 0%.
- Current task: BP-06.05/B1.04c recoverable publication; B1.01-.03 domain/contract/cache verification passed.
- Demonstrated behavior: bounded reasoning, authenticated sufficiency, immutable future-only corrections, actual Runtime receipt/retention, exploratory partial output, acknowledgement-loss recovery and independent owner replacement. Both publication owners have actual process-death evidence.
- Blockers: none requiring owner direction. Scientific sources, assay/route engines and target-host choices remain scoped future decisions.
- Human acceptance: no routine pause for authorized engineering; experimental validity is not inferred from software verification.
- Next gate: BP-06.05/B1.04 source rights and derived binding publication proof.

## Outcome and Boundaries

Turn source documents and experimental returns into versioned, replayable knowledge and purpose-specific evidence that a later campaign can use.

Included: One document/source connector and synthetic lab-return adapter; typed graph changes and rebuilds; bounded symbolic rules; evidence/sample identity; reusable representation profiles; versioned feedback receipts.

Excluded: Live LIMS/CRO integration, universal ontology, validated biological inference, unrestricted autonomous extraction, model training/promotion and a complete commercial data marketplace.

Primary services retain private state, dependencies, migrations and module READMEs. Public contracts/clients are the only cross-owner dependencies. Any new schema identifies its consumer/migration impact. No broad backend or shared business/ORM package. Later phases refine earlier boundaries under the current task without reopening closed plans.

## Canonical Children and Phase Mirror

| Parent phase / child | Overall | Build | Acceptance | Prerequisite |
|---|---:|---:|---:|---|
| P1 / [BP-06.01 Source and evidence contracts](BP-06/Completed/BP-06.01%20Source%20and%20evidence%20contracts.md) | 100% | 100% | 100% | Parent predecessor gates |
| P2 / [BP-06.02 Typed graph authoring and replay](BP-06/Completed/BP-06.02%20Typed%20graph%20authoring%20and%20replay.md) | 100% | 100% | 100% | BP-06.01 acceptance |
| P3 / [BP-06.03 Reasoning and domain receipts](BP-06/Completed/BP-06.03%20Reasoning%20and%20domain%20receipts.md) | 100% | 100% | 100% | BP-06.02 acceptance |
| P4 / [BP-06.04 Laboratory returns and candidate eligibility](BP-06/Completed/BP-06.04%20Laboratory%20returns%20and%20candidate%20eligibility.md) | 100% | 100% | 100% | BP-06.03 acceptance |
| P5 / [BP-06.05 Representation reuse and retrieval](BP-06/BP-06.05%20Representation%20reuse%20and%20retrieval.md) | 14.58% | 19.44% | 0% | BP-06.04 acceptance |
| P6 / [BP-06.06 Feedback integration and closeout](BP-06/BP-06.06%20Feedback%20integration%20and%20closeout.md) | 0% | 0% | 0% | BP-06.05 acceptance |

Each linked child is the execution tracker for its scope. Build tasks name concrete implementation; acceptance requires independent evidence and a scoped drift audit. BP-06.05 owns fractional progress through its canonical milestone basis; parent weights remain24 delivery units. Closed-gate counts are separate from scoped completion. Do not repeat the historical task pairs as a second work list. No dependent child starts before its predecessor acceptance gate; independent design review does not activate implementation.

## Test Ownership and Evidence

Proposed suite locations (create with their modules):

- `services/data_artifacts/tests/acquisition/`.
- `services/data_artifacts/tests/representations/`.
- `services/knowledge/tests/authoring/`.
- `services/knowledge/tests/replay/`.
- `services/knowledge/tests/reasoning/`.
- `services/research/tests/experiments/`.
- `tests/integration/knowledge_feedback/`.

Each owning README maps public behavior, invariants, failure scenarios and measured source paths to module-local test suites. Register source/suite ownership in `dev/test_scopes.json`; extend granular selectors as modules arrive. Run changed-module tests first, affected consumers next, and separate public-boundary integration/E2E only for cross-owner outcomes. Record line and branch coverage with gaps; coverage percentages are not evidence of scientific correctness.

Keep scenario evidence with absolute timestamps, implementation revision, fixture/schema identity, relevant run/artifact IDs and observed outcomes. Unit mocks do not replace required database, process, browser or provider evidence. Record independent build/install and replacement tests for new service/tool boundaries.

## UI Reference Refinement

`2026-09-24 12:10:07`: Use the [interaction reference map](../Architecture/Experience/Interaction_References.md) for P6 evidence/knowledge traversal: search-first bounded exploration and source details, without requiring manual predicate authoring. Implementation and all phase percentages remain 0%; this refines existing tasks.

## Reference Refinement

`2026-09-25 13:54:17`: BP-06.01/.02/.03/.04/.06 now include Research-owned questions/evidence needs, conversion traces, accepted claim/answer links, purpose-bound evidence sufficiency, processing-sensitive tested-material identity and real-view integration. Research, Knowledge and Data retain separate write authority. See [reference assessment](References/Amphora_Lab_Insights.md). Added requirements refine existing child B1-B3 deliveries; each child V1 gate includes them. No task is complete, implementation remains 0%, and the denominator is unchanged.

## Decisions and Handoff

Child decisions and the [cross-plan handoff register](Planning_Readiness.md) identify the exact producer, consumer and required proof. Engineering defaults are planning baselines; validate them against real predecessor contracts before coding. External choices are not inferred from examples. Do not weaken a live model, browser, database or target-host gate to a fixture when that environment is unavailable.

## Accounting and Closeout

On `2026-09-25 13:35:12`, the original two-task-per-phase estimate was decomposed into 24 verified deliveries across 6 children. Implementation stays 0%; no previous implementation credit is lost or added. [Planning history](BP-06%20Planning%20History.md) preserves the original scope and denominator. Pure design review earns no implementation credit.

Child closeout archives that child with its audit and repairs links; the parent remains active until all child gates and the integrated parent outcome pass. The last child's acceptance checks the parent handoff without repeating unchanged earlier audits. Keep implementation, human acceptance, operational readiness and scientific validation separate. Update child -> parent -> MBT -> Restore at each delivery/scope change.
