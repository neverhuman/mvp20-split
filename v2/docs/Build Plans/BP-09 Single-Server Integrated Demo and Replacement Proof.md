# BP-09 Single-Server Integrated Demo and Replacement Proof

## Canonical Parent Tracker

- Status: primary_active; BP-09.01/.02 closed; BP-09.03 B1.3b active.
- Last refreshed: `2026-10-07 02:45:50` (America/Chicago).
- Owner/scope: Local deployment/recovery integration with each service retaining ownership.
- Authority: [Master Build Tracker](Master%20Build%20Tracker.md); [planning readiness and handoffs](Planning_Readiness.md).
- Prerequisites: Completed BP-05/06/07 and BP-08 for evolutionary demo claims; BP-02/03/04 durability and protocol gates.
- Implementation: **43.19%**, (8 + 23/36)/20 verified delivery weight; eight delivery gates closed. Each child owns four deliveries; this parent counts them once. Parent phase Pn equals child .0n overall completion; child Build/Acceptance phases remain canonical in that child.
- Design maturity: all immediate children have owned objects, public boundaries, algorithms, failure oracles, replacement gates and named decision limits. Reconcile predecessor versions before activation; this is not implementation evidence.
- Current implementation task: BP-09.03/B1.3b actual catalog/tool eligibility; native and scientific lifecycle/adoption checkpoints verified.
- Demonstrated behavior: selected-host preflight and independently installed local infrastructure, restricted roles, actual outage/receipt recovery, quota/exposure denial, seven-host replacement/drain and gateway browser compatibility. Full campaign/model integration remains BP-09.03.
- Blockers: none for local installation engineering; later external gates remain scoped to their child trackers.
- Human acceptance: no routine approval pause for authorized engineering work; host/provider/data decisions still govern their dependent actions.
- Planning review: `2026-10-06 19:58:42`; parent/child scope, evidence tiers and dependencies reconciled. Active BP-02 implementation position remains unchanged by this roadmap review.

## Outcome and Boundaries

Deploy and demonstrate the bounded autonomous engine on the selected server, recover its state, and replace one module without breaking its consumers.

Included: Target-host composition, pinned service/tool releases, access/configuration, resource/architecture checks, integrated demo, backup/restore and one between-campaign replacement.

Excluded: Multi-tenant production operations, HA/fleet scaling, compliance certification, unsupported GPU guarantees and unselected cluster installation.

Primary services retain private state, dependencies, migrations and module READMEs. Public contracts/clients are the only cross-owner dependencies. Any new schema identifies its consumer/migration impact. No broad backend or shared business/ORM package. Later phases refine earlier boundaries under the current task without reopening closed plans.

## Canonical Children and Phase Mirror

| Parent phase / child | Overall | Build | Acceptance | Prerequisite |
|---|---:|---:|---:|---|
| P1 / [BP-09.01 Host and deployment profile](BP-09/Completed/BP-09.01%20Host%20and%20deployment%20profile.md) | 100% | 100% | 100% | Parent predecessor gates |
| P2 / [BP-09.02 Reproducible installation and boundaries](BP-09/Completed/BP-09.02%20Reproducible%20installation%20and%20boundaries.md) | 100% | 100% | 100% | BP-09.01 acceptance |
| P3 / [BP-09.03 Integrated autonomous demonstration](BP-09/BP-09.03%20Integrated%20autonomous%20demonstration.md) | 15.97% | 21.30% | 0% | BP-09.02 acceptance |
| P4 / [BP-09.04 Backup restore and module replacement](BP-09/BP-09.04%20Backup%20restore%20and%20module%20replacement.md) | 0% | 0% | 0% | BP-09.03 acceptance |
| P5 / [BP-09.05 Acceptance and successor handoff](BP-09/BP-09.05%20Acceptance%20and%20successor%20handoff.md) | 0% | 0% | 0% | BP-09.04 acceptance |

Each linked child is the execution tracker for its scope. Build tasks name concrete implementation; acceptance requires independent evidence and a scoped drift audit. Do not repeat the historical task pairs as a second work list. No dependent child starts before its predecessor acceptance gate; independent design review does not activate implementation.

## Test Ownership and Evidence

Proposed suite locations (create with their modules):

- `deploy/local/tests/`.
- `deploy/<selected-profile>/tests/`.
- `tests/integration/demo/`.
- `tests/integration/restore/`.
- `tools/<replacement>/tests/`.

Each owning README maps public behavior, invariants, failure scenarios and measured source paths to module-local test suites. Register source/suite ownership in `dev/test_scopes.json`; extend granular selectors as modules arrive. Run changed-module tests first, affected consumers next, and separate public-boundary integration/E2E only for cross-owner outcomes. Record line and branch coverage with gaps; coverage percentages are not evidence of scientific correctness.

Keep scenario evidence with absolute timestamps, implementation revision, fixture/schema identity, relevant run/artifact IDs and observed outcomes. Unit mocks do not replace required database, process, browser or provider evidence. Record independent build/install and replacement tests for new service/tool boundaries.

## Decisions and Handoff

Child decisions and the [cross-plan handoff register](Planning_Readiness.md) identify the exact producer, consumer and required proof. Engineering defaults are planning baselines; validate them against real predecessor contracts before coding. External choices are not inferred from examples. Do not weaken a live model, browser, database or target-host gate to a fixture when that environment is unavailable.

## Accounting and Closeout

On `2026-10-06 19:58:42`, the original two-task-per-phase estimate was decomposed into 20 verified deliveries across 5 children. Implementation stays 0%; no previous implementation credit is lost or added. [Planning history](BP-09%20Planning%20History.md) preserves the original scope and denominator. Pure design review earns no implementation credit.

Child closeout archives that child with its audit and repairs links; the parent remains active until all child gates and the integrated parent outcome pass. The last child's acceptance checks the parent handoff without repeating unchanged earlier audits. Keep implementation, human acceptance, operational readiness and scientific validation separate. Update child -> parent -> MBT -> Restore at each delivery/scope change.
