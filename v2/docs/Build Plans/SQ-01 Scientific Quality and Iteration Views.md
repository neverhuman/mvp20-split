# SQ-01 Scientific Quality and Iteration Views

## Canonical tracker

- Status: queued successor to closed BP-05; not activated.
- Last refreshed: `2026-10-02 21:14:00` (America/Chicago).
- Completion: 0%; Build0%, Verification0%; 0/4 scoped gates.
- Owner: Studio presentation; Research/Knowledge own assessments; Agents owns proposals.
- Prerequisites: BP-06 owner quality/correction projections and BP-07.03 proposal contracts; activation coherence audit and exact DTO reconciliation before implementation.
- Current focus: capture owner-directed iterative research behavior; design is not implementation credit.
- Next gate: after prerequisites, activate in MBT order and define public projection contracts.
- Blockers: prerequisite implementations pending; no owner decision needed.
- Requirement: [Campaign progress](../Architecture/Requirements/Product_Requirements.md#campaign-progress-uncertainty-and-subsequent-iteration).
- Architecture: [Studio](../Architecture/Experience/Studio.md#exploratory-quality-and-next-campaign-focus).

## Ordered scope and exit gates

1. B1 - Implement scoped quality projections and page models with exact point/campaign/assessment revisions, reasons, applicability and evidence references. Separate operational state from uncertain, contradictory, unassessed and demonstrated-error scientific states; no fabricated numerical accuracy. Verify public contracts, permissions, pagination and partial/unavailable data.
2. B2 - Implement visible accessible graph markers, filtering, drill-down and affected-consumer navigation. Preserve pinned historical views; label newer correction annotations separately. Verify multiple simultaneous weak points alongside successful execution without UI mutation of active runs.
3. B3 - Implement human focus selection and presentation of authorized AI follow-up proposals through public owner APIs. Link selected points to intended next-campaign improvements, expected information gain and retained unresolved items. Verify proposal lineage and absence of routine approval queues or active-run repinning.
4. V1 - Module-scoped tests, browser visual/interaction proof, independent replacement acceptance and scoped drift audit. Show useful retained results despite several weak points and a subsequent campaign targeting selected weaknesses. Scientific calibration and efficacy require separate evidence.

Each gate contributes one quarter of completion. Build is completed B1-B3 /3; Verification is V1. Keep tests under their owning modules; cross-owner fixtures remain a separate integration tier. Before coding, apply the local UI Coding Guidelines. Update replacement READMEs for touched modules. No private peer imports or SQL; Studio cannot create scientific verdicts or execute AI proposals itself.

BP-05 remains closed. This plan adds no credit or scope to BP-06 B2; its scheduling follows its named dependencies and does not interrupt the current correction implementation.
