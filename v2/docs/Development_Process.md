# Development Process

- Design status: active v2 operating rules; implementation plans not yet activated
- Last reviewed: `2026-09-22 21:03:27` (America/Chicago)
- Scope: architecture decomposition, hierarchical planning, execution state, verification and drift closeout

## Canonical Ownership

UI work also follows [UI Coding Guidelines](UI_Coding_Guidelines.md), adapted from the user-requested JARVIS UI review. Record UI verification in the owning task and module contract.

| Artifact | Owns |
|---|---|
| [Architecture index](Architecture/README.md) and owning design docs | Design intent, boundaries, constraints and staged validation |
| [Master Build Tracker](Build%20Plans/Master%20Build%20Tracker.md) | Cross-plan priority, dependencies and primary plan; mirrors execution status |
| Owning plan's top-of-file tracker | Overall/per-phase progress, task position, completed deliverables, evidence, exit gates and blockers |
| Module README beside source | Actual responsibilities, interfaces, state and dependency boundaries |
| Generated inventories | Volatile implementation facts, with generator and source revision |
| [Drift dashboard](Audits/Architecture%20Drift.md) | Unresolved or recently closed implementation/design mismatches |
| [Restore](../Restore.md) | Exact resume task and active interruption; links to authoritative trackers |

Do not create competing progress ledgers. A routine resume reads the tracker; a new agent/session does not justify re-auditing source or resetting progress. Concrete contradictions require a narrow investigation, an evidence-backed correction to the owner, then synchronization of summaries.

## Decomposed Architecture

Focused architecture leaves must explain the design, not just summarize requirements: owned components/objects, lifecycle and interactions, state/commit boundaries, failure/recovery scenarios and unresolved decisions. Use the [Architecture Contract Template](Templates/Architecture%20Contract%20Template.md). Proposed names must be labeled as design vocabulary; stack choices and implemented guarantees need separate evidence. Domain summaries explain coordination without repeating their children's protocols.

Use descriptive `*_Architecture.md` filenames for domain architecture entry points. These documents define intended design. A `README.md` beside code defines that module's actual implemented behavior and boundaries, links to the owning architecture and explicitly identifies gaps or planned behavior. Documentation-directory READMEs are navigation guides only; they must not become domain architecture or implementation authorities. Drift review compares design against module documentation and source rather than conflating the two.

Keep the top-level architecture as an integration map. Put detailed behavior in focused capability/domain documents, and use child indexes when a domain becomes too large. Every boundary must name an owner, public contract, data/state ownership, dependencies and verification. Shared contracts have one owner and linked consumers rather than duplicated definitions. Module decomposition follows behavior and failure boundaries, not arbitrary file sizes or JARVIS-specific taxonomy.

Traceability runs both directions: requirement/design claim -> owning plan/task -> module contract -> implementation/inventory -> verification -> drift disposition. Claim status is `planned`, `partial`, `implemented`, `deprecated` or `disputed`. Existing specification text is not proof of an implementation. Use the [module template](Templates/Module%20README%20Template.md) for each meaningful module; small helpers may use a concise parent-owned contract.

Inventories belong in `docs/Generated/` once generators exist. Useful subjects include routes/schemas, tool manifests, graph contracts, stores, configuration, runtime services, events and frontend calls. Record how and from which revision each inventory was generated. Do not populate fake inventories before code exists. Human docs own intent; generated facts help detect divergence.

## Hierarchical Plans

Module replacement is an expected development pattern. The source-adjacent module README is the current implementation-boundary contract for a fresh rebuild, with canonical schemas and acceptance fixtures linked rather than duplicated. Before replacement, confirm that public behavior, consumers, state ownership, failure semantics and compatibility/cutover expectations are captured using the module template. Reimplement internals freely within that boundary; intentional boundary changes require versioned contracts, consumer impact and migration evidence. Do not discard authoritative data or restart from incompatible checkpoints merely because code is being replaced. Initial-profile cutovers occur between campaigns. Closed plans stay closed: use a bounded successor plan for substantive replacement and its scoped drift audit for closeout.

Use `docs/Build Plans/` as the one local plan hierarchy. The Master Build Tracker selects program priority. Parent plans decompose capabilities into linked child plans or bounded phases; child plans own execution detail. Every child names its parent, dependencies and exit contribution. Do not count the same deliverable twice. [The plan template](Templates/Build%20Plan%20Template.md) applies at each execution-owning level.

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

## Verification and Closeout Drift Audit

Verification must match the promised behavior: focused unit/contract checks, integration/recovery/concurrency checks where relevant, and actual user-path or scientific evaluation when the gate requires them. Compilation or a mocked success alone does not prove usable end-to-end behavior or scientific authority. Preserve failures and explicit validation limits; do not weaken tests to close a gate. Avoid repeated broad testing without a new change or unresolved concern.

At each plan completion, perform a component-scoped architecture drift audit **after implementation/acceptance gates and before archival**. This also applies to a completed child implementation plan; a parent closeout verifies integration without repeating unchanged child audits.

1. Bound the audit to components and directly affected contracts identified by the plan's change/evidence record.
2. Compare architecture claims, module READMEs, source, applicable generated inventories and acceptance evidence. Check ownership, schemas/APIs, state/lifecycle, side effects, privacy, configuration and runtime boundaries.
3. Record timestamp, reviewed revision or working-tree scope, findings, verification and disposition using the [audit template](Templates/Plan%20Audit%20Template.md). Repair in-scope discrepancies; acceptance-invalidating drift blocks closeout. Assign explicitly nonblocking findings to an owner/successor with evidence.
4. Update the drift dashboard; aligned entries with no follow-up go into history. Preserve final percentages and gate evidence. Move the plan/history to `Build Plans/Completed/`, repair all inbound links, and update MBT, plan index and Restore in the same closeout.

Closed and monitoring-only plans stay out of active tables. Regressions or new scope use successors, not reopened old plans. Do not retroactively audit every historical v1 plan. An acceptance-blocking finding cannot be renamed follow-on scope to permit archival.

## Context and Documentation Discipline

Read current tracker/index -> owning plan -> module README/contract -> targeted generated inventory -> targeted source. Use history only when that lookup does not answer the question. Keep `Restore.md` focused on restart state, not a changelog. Separate large plans from `<Plan> History.md`; cap MBT checkpoint history at 25 rows. Use absolute local timestamps with seconds and an explicit timezone; keep static reference docs on lightweight review fields instead of progress trackers.

Repeated broad reading indicates missing summaries or decomposition debt. Repair touched boundaries when practical; otherwise record symptom, owner, needed split/summary, priority and trigger in [Documentation Debt](Audits/Documentation%20Debt.md). Keep logs and evidence concise with exact revision/artifact identifiers. Isolate failed stateful probes and retain working components while repairing the failing behavior. Domain objects own behavior; transport DTOs do not replace domain models.

## Reviewed Source and Local Adaptation

Reviewed read-only from JARVIS on `2026-09-22 13:47:22`: `Docs/AGENTS.md` (including tracker updates confirmed there on 2026-09-19), `Docs/plan audit.md`, `Docs/ProcessSummary.md`, targeted `Docs/Process.md`, `Docs/System/Architecture Cartography.md`, `Docs/Templates/Module README Template.md`, the Master Build Tracker, drift dashboard and the Specialist Lane Backend Extraction execution tracker.

The local rules incorporate the newer canonical-tracker, sequencing, percentage and interruption requirements. JARVIS live plan state, deployment authority, domain taxonomy and closed UI plan names are not imported. The old module template's relative review-date suggestion is superseded by the current absolute-timestamp rule. Amphora uses its existing `Build Plans` directory, not an external JARVIS path. Normal operation requires no further JARVIS access.
