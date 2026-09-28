# BP-03 Tool Index and Standalone Execution

## Canonical Parent Tracker

- Status: primary_active; BP-03.02 / Build / B3.
- Last refreshed: `2026-09-28 14:49:59` (America/Chicago).
- Owner/scope: Capability Registry and independently packaged tools.
- Authority: [Master Build Tracker](Master%20Build%20Tracker.md); [planning readiness and handoffs](Planning_Readiness.md).
- Prerequisites: BP-01 contracts and completed BP-02 claim/artifact/authority gates.
- Implementation: **37.50%**, 6/16 verified child deliveries. Each child owns four deliveries; this parent counts them once. Parent phase Pn equals child .0n overall completion; child Build/Acceptance phases remain canonical in that child.
- Design maturity: all immediate children have owned objects, public boundaries, algorithms, failure oracles, replacement gates and named decision limits. Reconcile predecessor versions before activation; this is not implementation evidence.
- Current implementation task: BP-03.02/B3 actual failure/race oracles. Next: V1 installed host/replacement.
- Demonstrated behavior: immutable identity, semantic validation and separate selection observations verified; registry transaction/API boundary verified; deeper routing, installed hosting and actual tools remain pending.
- Blockers: BP-01/BP-02 predecessor gates passed; no current user blocker. External choices remain only at their named dependent gates.
- Human acceptance: no routine approval pause for authorized engineering work; host/provider/data decisions still govern their dependent actions.
- Planning review: `2026-09-25 13:35:12`; parent/child scope, evidence tiers and dependencies reconciled. Active BP-02 implementation position remains unchanged by this roadmap review.

## Outcome and Boundaries

Discover a pinned tool release, dispatch through the runtime and execute it in independent replicas without shared private code or state.

Included: Registry identities/descriptors, eligibility and deployment inventory; narrow worker SDK; two deterministic synthetic tools with different payload shapes; independent builds and replacement evidence.

Excluded: General graph interpretation, real chemical validity, full model catalog, production remote-provider effects and Kubernetes installation. Solvency reuse is optional follow-on until applicability and dependency evidence are reviewed.

Primary services retain private state, dependencies, migrations and module READMEs. Public contracts/clients are the only cross-owner dependencies. Any new schema identifies its consumer/migration impact. No broad backend or shared business/ORM package. Later phases refine earlier boundaries under the current task without reopening closed plans.

## Canonical Children and Phase Mirror

| Parent phase / child | Overall | Build | Acceptance | Prerequisite |
|---|---:|---:|---:|---|
| P1 / [BP-03.01 Identity and descriptor contracts](BP-03/Completed/BP-03.01%20Identity%20and%20descriptor%20contracts.md) | 100% | 100% | 100% | Closed/audited |
| P2 / [BP-03.02 Registry and version routing](BP-03/BP-03.02%20Registry%20and%20version%20routing.md) | 50% | 66.67% | 0% | B2 passed; B3 active |
| P3 / [BP-03.03 Worker protocol and independent tools](BP-03/BP-03.03%20Worker%20protocol%20and%20independent%20tools.md) | 0% | 0% | 0% | BP-03.02 acceptance |
| P4 / [BP-03.04 Replicas and replacement proof](BP-03/BP-03.04%20Replicas%20and%20replacement%20proof.md) | 0% | 0% | 0% | BP-03.03 acceptance |

Each linked child is the execution tracker for its scope. Build tasks name concrete implementation; acceptance requires independent evidence and a scoped drift audit. Do not repeat the historical task pairs as a second work list. No dependent child starts before its predecessor acceptance gate; independent design review does not activate implementation.

## Test Ownership and Evidence

Proposed suite locations (create with their modules):

- `services/capability_registry/tests/catalog/`.
- `services/capability_registry/tests/deployments/`.
- `sdk/tool_protocol/tests/`.
- `tools/<tool>/tests/`.
- `tests/integration/tool_execution/`.

Each owning README maps public behavior, invariants, failure scenarios and measured source paths to module-local test suites. Register source/suite ownership in `dev/test_scopes.json`; extend granular selectors as modules arrive. Run changed-module tests first, affected consumers next, and separate public-boundary integration/E2E only for cross-owner outcomes. Record line and branch coverage with gaps; coverage percentages are not evidence of scientific correctness.

Keep scenario evidence with absolute timestamps, implementation revision, fixture/schema identity, relevant run/artifact IDs and observed outcomes. Unit mocks do not replace required database, process, browser or provider evidence. Record independent build/install and replacement tests for new service/tool boundaries.

## Decisions and Handoff

Child decisions and the [cross-plan handoff register](Planning_Readiness.md) identify the exact producer, consumer and required proof. Engineering defaults are planning baselines; validate them against real predecessor contracts before coding. External choices are not inferred from examples. Do not weaken a live model, browser, database or target-host gate to a fixture when that environment is unavailable.

## Accounting and Closeout

On `2026-09-25 13:35:12`, the original two-task-per-phase estimate was decomposed into 16 verified deliveries across 4 children. Implementation stays 0%; no previous implementation credit is lost or added. [Planning history](BP-03%20Planning%20History.md) preserves the original scope and denominator. Pure design review earns no implementation credit.

Child closeout archives that child with its audit and repairs links; the parent remains active until all child gates and the integrated parent outcome pass. The last child's acceptance checks the parent handoff without repeating unchanged earlier audits. Keep implementation, human acceptance, operational readiness and scientific validation separate. Update child -> parent -> MBT -> Restore at each delivery/scope change.

## Activation Checkpoint

`2026-09-28 13:45:17`: BP-02 closed at 32/32 with actual installed recovery and replacement evidence. .01 activated at 0% after bounded contract/architecture coherence review; other children remain queued. No implementation credit from activation. Preserve existing tool/runtime command compatibility; extension of registry metadata must not turn discovery into runtime authority.
