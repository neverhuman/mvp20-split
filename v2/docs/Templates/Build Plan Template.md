# <Plan Name>

## Canonical Execution Tracker

- Status: proposed | primary_active | blocked | awaiting_acceptance | complete
- Last refreshed: YYYY-MM-DD HH:mm:ss (America/Chicago)
- Scope/baseline revision: <bounded scope and revision>
- Owner: <accountable role>
- Parent: <link or none>; Master Build Tracker: <relative link>
- Overall implementation: <numeric % and accounting basis; child rollups must not double count>
- Design readiness: <decisions resolved and remaining; pure design gates earn no implementation credit>
- Demonstrated behavior: <actual unit/service/process evidence and its limits>
- Current phase/task: <one exact position or none before activation>
- Next task: <bounded next task>
- Remaining exit gate: <evidence required>
- Completed deliverables/evidence: <links>
- Blockers: <named or none>
- Human acceptance: <decision and dependent transition or none>
- Active exception: <reason/scope/verification/return point or none>
- Pre-activation audit: <timestamp, baseline, disposition, findings and evidence>

| Phase / status | Implementation % | Prerequisites | Bounded deliverable | Verification / exit gate | Evidence |
|---|---:|---|---|---|---|
| <phase> | <numeric %> | <required prior gates> | <deliverable> | <checks and required acceptance> | <link or pending> |

## Objective and Boundaries

Requirements/design links; included/excluded work; single owner for each cross-cutting capability; parent/child dependencies. Define scientific or runtime claims this plan can and cannot establish.

## Ordered Tasks

For a roadmap parent, register immediate child packages with owner, dependency, bounded outcome and readiness gaps. For the nearest active child, link concrete objects/contracts, state transitions, transaction write sets, failure/recovery cases and independent test oracles before coding. Do not create empty descendant files simply to increase plan counts.

Task IDs, deliverables, verification, dependencies and next action. Detail the current phase; preserve enough downstream scope to explain sequencing. Completed phases are not permanent owners of later refinements.

## Changes, Discoveries and Interruptions

Record current-task adjustments with contract/migration/regression impact. Exceptions include interrupted task, reason, independence or dependency justification, bounded work, verification and exact return point. Assign nonblocking discoveries to future scope.

## Closeout

Record component-scoped drift audit timestamp, revision, scope, findings, verification and disposition before archival. Block on acceptance-invalidating drift; link explicitly owned nonblocking follow-ups. Synchronize MBT, indexes and Restore, repair archive links and preserve final progress/evidence. Link a separate history file when chronology becomes long.

## MBT Completion Mirror

Every in-flight row in MBT must mirror this canonical plan's numeric overall and per-phase implementation percentages. Refresh both on progress/scope changes and before handoff/commit. Explain the denominator here; record acceptance/readiness separately. Closeout removes the active row and archives the completed plan.
