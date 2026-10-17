# Tracker purpose and design

A tracker is the current decision record for delivering a bounded outcome. It lets the owner or a fresh implementer determine what works, what remains, what can happen next and what requires a decision without reconstructing the project from chat, Git history or test logs.

Its purpose is to prevent lost scope, repeated work, premature completion and unauthorized sequencing. A tracker must explain progress in terms of delivered behavior. A chronology of activity, a list of files or an unexplained percentage cannot do that.

## Questions the tracker must answer

| Question | Required information | Decision it supports |
|---|---|---|
| Why are we doing this? | Intended user/system outcome and linked requirement; explicit scope and exclusions | Whether work belongs in this plan |
| What will count as delivered? | Named deliverables and observable acceptance conditions | Whether the promised outcome exists |
| What works now? | Demonstrated behavior, evidence revision/environment and limits | What downstream work may rely on |
| What remains? | Incomplete deliverables, unmet gates and unresolved decisions | What must still be done before closeout |
| Where are we? | Current named phase/task, its state and prerequisites | What work is eligible now |
| What happens next? | Exact next bounded task, expected output and verification | How another session resumes |
| What prevents progress? | Blocker, impact, responsible owner and smallest resolution needed; or none | Whether to repair, wait or request a decision |
| What does the number mean? | Named completion measure, denominator/weights and included units | How to interpret progress without confusing it with time |

Lead with a short readable summary: **intended outcome; demonstrated behavior; remaining outcome; current task; next gate**. Keep detailed evidence behind links. State phase names beside IDs, so readers do not need to memorize E1/E2 or follow several links to understand a percentage.

## Different tracker levels make different decisions

- **Master Build Tracker:** selects program priority, dependency order and the primary plan. Mirrors each in-flight plan's current summary and progress; does not maintain a second task ledger.
- **Parent plan tracker:** defines its outcome, immediate children and their contribution. Explains how the children fit together and what integration remains. Child implementation does not automatically establish parent integration.
- **Execution-owning plan tracker:** owns deliverables, current task, prerequisite/acceptance gates, evidence, remaining work and blockers. This is the authoritative record for whether the bounded delivery is complete.
- **Restore:** points to that tracker and records workspace, interruption and exact resume action. It is a session handoff, not a second source of progress truth.
- **Audit record:** evaluates a declared boundary against evidence and records findings/disposition. It does not replace the tracker or independently grant execution authority.

## What each work item describes

Use a stable ID, a concrete outcome, prerequisite, state, verification/exit condition and evidence link. Assign an accountable owner where ownership differs. The current item also needs an exact next action. Decompose items when independent outcomes or owners would otherwise disappear inside one percentage; do not create a tracker row for every edit or shell command.

For example, “population dispatch” is too vague by itself. “Dispatch a frozen cohort in two batches; prove identical membership and candidate/result attribution across restart” identifies an outcome and a falsifiable exit. Test counts are supporting evidence, not the outcome.

## State, progress and evidence are separate

| State | Meaning |
|---|---|
| Proposed | Scope exists; activation prerequisites and readiness have not been satisfied |
| Primary active | The selected plan is executing an eligible bounded task |
| Blocked | A named unmet condition prevents the relevant next step; state its scope |
| Awaiting acceptance | A declared acceptance decision is outstanding; identify only the transition it blocks |
| Complete | Required delivery/acceptance gates and closeout obligations have passed |

Implementation progress, verification results and acceptance disposition remain separate fields. Code can be implemented while an actual-owner integration gate is still pending. A successful fixture does not prove its peer exists or the production user path works. “Last verified” is not “currently healthy.”

Every percentage must name its basis: for example, completed delivery units out of four equally weighted units, or an explicitly weighted implementation breakdown. Do not mix these measures silently. Show the completed and remaining units, retain the denominator and derive parent rollups once. Percentages do not estimate remaining time. A changed denominator requires an explained scope change rather than a quiet rewrite.

## Changes that the tracker must represent

The tracker records changes in delivered capability, verification/acceptance, remaining scope, dependency, blocker, current/next action and accounting basis. It also records a user interruption's bounded purpose and exact return point. Routine edit history belongs in Git; detailed failed/superseded runs belong in linked evidence/history.

Later refinements belong to the current task with compatibility/regression impact. Preserve earned prior credit and historical evidence. If a prior assumption is invalidated, identify the current consequence and required resolution; neither hide the failure nor reset unrelated completion.

## Acceptance test for a useful tracker

A reader should be able to explain the outcome, demonstrated behavior, unfinished delivery, eligible next action and blocking decision from its current summary and immediate table. If they must decode IDs, read a transcript or count passing tests to answer those questions, the tracker needs repair.

The [build plan template](../templates/Build%20Plan%20Template.md) provides the record structure. [Plan execution](Plan_Execution.md) defines sequencing and update discipline. This specification explains what the record means and why it exists; it adds no new execution authority or approval gate.
