# Planning and execution

Reviewed: 2026-10-16 14:17:15 America/Chicago. Canonical development process; not evidence of implementation.

## Hierarchical Plans

Use `docs/Build Plans/` as the one local plan hierarchy. The Master Build Tracker selects program priority. Parent plans decompose capabilities into linked child plans or bounded phases; child plans own execution detail. Every child names its parent, dependencies and exit contribution. Do not count the same deliverable twice. [The plan template](../templates/Build%20Plan%20Template.md) applies at each execution-owning level.

Maintain one `primary_active` plan and one active phase/current task by default. A plan must name the next task and earliest unmet prerequisite. A backlog is not permission to select the easiest task. Parent rollups must state their accounting basis and derive from child scope without separate contradictory estimates.

Before activating a new or queued plan, audit its objective, included/excluded scope, dependency sequence, single ownership, bounded deliverables, verification, exit gates, progress basis and resume point. Record `ready`, `corrected_ready` or `blocked_on_named_issue` with timestamp and baseline in the owning plan. Correct old planning defects when the plan becomes relevant; do not divert into a whole-roadmap cleanup. This audit establishes plan coherence, not implementation completion.

## Tracker and Phase Execution Rules

1. Before implementation, identify the phase/task, prerequisites, bounded deliverable, verification and exit gate. Complete required phase gates before beginning dependent work. Tests or high percentages cannot waive a prerequisite.
2. Keep numeric overall and per-phase implementation percentages, including `0%` and `100%`, with a stated basis. Separate implementation completion from technical gates and human acceptance. A phase can be implemented at `100%` while progression is blocked by a declared acceptance gate; do not label it complete until required exits pass.
3. Update the canonical tracker as each bounded task completes or changes, before commit/handoff. Record completed deliverables, implementation/test/deployment evidence as applicable, remaining work, next task and exceptions. Last-verified evidence is not a current runtime-health claim.
4. Synchronize MBT for changes in priority, status, progress, dependency, blocker or primary checkpoint, and Restore when the resume point changes. Do not finish work and leave the next session to rediscover its state.
5. Phases are discrete deliveries, not permanent categories of file ownership. Later schema, API, storage or UI refinements belong to the current phase, recording reason, affected contract, migration/compatibility implications and regression evidence. Do not reopen a completed phase merely because its files change.
6. Preserve historical gate evidence and downstream implementation credit. If a prerequisite assumption is materially invalidated, record a current-phase blocker and explicit dependency/design decision. Do not silently rewrite the historical baseline or add dependent complexity before resolution.
7. Scope changes must explain percentage changes. Preserve estimates during rebaselining and reconcile them against remaining work. New substantial scope becomes a named successor or explicit rebaseline; never move unresolved required work out merely to claim completion or weaken a gate after it fails.
8. Human acceptance blocks only the declared transition. Do not infer approval from elapsed time, repeatedly ask for deferred feedback, or treat it as a general block on independent authorized prerequisite work. Routine implementation choices and blocking repairs do not require a new approval ceremony.

Every active tracker must include status, scope/baseline, timestamp, owner, parent/MBT links, overall/per-phase percentages, current and next task, prerequisites/deliverables/gates, completed evidence, remaining work, blockers, acceptance dependency and active exception or `none`.

## Interruptions and Discovery

Out-of-order work needs an explicit user interruption, a defect blocking the active gate, or demonstrated independence. Before switching, record interrupted phase/task, reason, dependency justification, bounded scope, verification and exact return point. Material scope/sequence changes need owner direction; an implementation opportunity alone is not an exception. Return to the recorded task when finished.

Log nonblocking discoveries against their future phase or documentation debt instead of spawning new workstreams. Ordinary downstream contract adjustments remain in the current phase and do not need an interruption entry. Do not create runtime goals just to track this procedure. Delegation is not implied by this process; follow the session's agent-delegation rules.

## Progress checkpoints and authorization

Use named phases beside percentages and explain the denominator. Delivery-checklist completion is not elapsed effort or a forecast of remaining time.

Human acceptance blocks only the declared transition. Continue independently authorized work; approval is never inferred from elapsed time. Routine implementation choices do not add approval gates. See [agent workflow](../agents/Agent_Workflow.md).
