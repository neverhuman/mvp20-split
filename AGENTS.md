# AGENTS Notes

## MVP20 Local Architecture Override

- The active workspace is `Z:\mvp20-split`. Paths under `Z:\JARVIS` in the imported continuity notes below are historical examples and must not be accessed unless the user explicitly requests it.
- The active architecture direction is [`docs/Architecture/Graph_Native_Research_Engine.md`](docs/Architecture/Graph_Native_Research_Engine.md).
- Amphora is now a flexible graph-native research engine rather than an epoxy-shaped fixed pipeline. It has two first-class authored graph types: executable campaign graphs and neuro-symbolic domain graphs. Execution/provenance lineage is a derived projection.
- Executable graph configuration is intentional: reviewed modules provide bounded primitives, while campaign graphs determine composition, branching, iteration, retained state, and evolvable topology without requiring hard-coded pathway changes.
- Deep human graph visualization and interaction are core engine capabilities, including editing, execution inspection, lineage comparison, intervention, and traversal between campaign and domain graphs.
- The local relaunch handoff is [`HANDOFF.md`](HANDOFF.md), and the local architecture index is [`docs/Architecture/README.md`](docs/Architecture/README.md). These local documents take precedence over the imported path examples below.

## Purpose
Short continuity notes for future relaunches so work can resume from the extracted architecture rather than re-reading old source transcripts.

## Current Canonical Docs
- [`Architecture.md`](Z:\JARVIS\Docs\Architecture.md) is the top-level integration document.
- [`Agents/Index.md`](Z:\JARVIS\Docs\Agents\Index.md) is the named-agent directory.
- [`BaseModels/Index.md`](Z:\JARVIS\Docs\BaseModels\Index.md) is the canonical base-model taxonomy.
- [`System/Index.md`](Z:\JARVIS\Docs\System\Index.md) is the runtime and platform architecture index.
- [`BuildPlan/Master Build Tracker.md`](Z:\JARVIS\Docs\BuildPlan\Master%20Build%20Tracker.md) is the program-level build-plan dashboard; [`BuildPlan/Index.md`](Z:\JARVIS\Docs\BuildPlan\Index.md) and [`BuildPlan/Build Order.md`](Z:\JARVIS\Docs\BuildPlan\Build%20Order.md) are the implementation planning entry points.
- [`System/Architecture Cartography.md`](Z:\JARVIS\Docs\System\Architecture%20Cartography.md) defines the design-to-implementation traceability pattern. Significant module or boundary changes should update the relevant module README, generated inventory when available, and the active drift dashboard in [`Audits/Architecture Drift.md`](Z:\JARVIS\Docs\Audits\Architecture%20Drift.md) when there is unresolved or recently closed drift.
- [`Audits/Documentation Debt.md`](Z:\JARVIS\Docs\Audits\Documentation%20Debt.md) tracks places where repeated long reads indicate missing summaries, stale boundaries, or decomposition pressure.

## Canonical Structural Rules
- `BaseModels` is the canonical home for base-model taxonomy and agent-to-base-model mapping.
- `Agents` contains named working roles or personalities.
- `System` contains routing, memory, orchestration, deployment, and environment architecture.
- `BuildPlan` contains implementation sequencing and schema-first rollout planning.
- `Input.md` is reserved as user-provided structure input for the active working session and should be left empty unless the user populates it.
- Old source transcripts are no longer primary working docs.
- Living docs should expose their current operational state near the top instead of requiring a reader to infer it from the full history. Use a concise tracker/status block for active build plans, architectural migration plans, audit/remediation docs, module contracts, runbooks, and long-running design records when they are more than static reference material.
- Tracker/status blocks should include the smallest useful set of fields for that document type: status, completion or maturity estimate, active focus, latest implementation checkpoint or reviewed date, current owner/scope when relevant, next steps, and known blockers or deferred work.
- Before each implementation commit that advances an active plan or changes the state of a living doc, update that document's tracker when checkpoint, status, active focus, blocker state, or next-step list changed.
- Before each implementation commit that materially changes a build plan's status, priority, completion estimate, dependency, blocker, or primary checkpoint, update [`BuildPlan/Master Build Tracker.md`](Z:\JARVIS\Docs\BuildPlan\Master%20Build%20Tracker.md) as the program-level source of truth.
- Use absolute local timestamps with seconds (`YYYY-MM-DD HH:mm:ss`) for tracker refreshes, checkpoint tables, smoke evidence, and durable status history. Do not use aging relative labels such as `today`, `yesterday`, or `current session` in durable docs.
- Keep trackers concise and factual; detailed historical notes belong in companion history files, generated inventories, architecture drift records, or narrowly scoped module docs.
- Active plan trackers should preserve accurate completion ranges, current focus, next gate, blockers, handoff/acceptance posture, and recent implementation checkpoints. Avoid expanding active-focus fields into full prose histories.
- For large active build plans, prefer a two-file operating pattern: `<Plan>.md` stays focused on current state, remaining gates, blockers, and next actions; `<Plan> History.md` captures durable completed work, implementation checkpoints, decision logs, and archived plan snapshots. Do not retroactively split every completed plan, but apply this pattern when a plan is touched and has become too large to operate from directly.
- Completion percentages measure scoped work done versus scoped work remaining. They do not measure final functional handoff, human acceptance, soak posture, monitoring maturity, or confidence. If every defined task/gate in a phase is done, that phase is `100%` even when human acceptance, operational soak, or successor functionality remains. Track those separately through status, current gate, blockers, handoff/acceptance notes, monitoring state, or successor plans.
- If scope is added to an active phase, reduce the completion estimate to reflect the new work remaining. If major new work is discovered after the bounded scope is otherwise complete, create a named successor plan or explicitly reset the plan as a new version; do not keep adding scope to a nearly complete or complete plan while leaving its percentage unchanged.
- Closed, completed, and monitoring-only build plans stay closed. Do not reopen an old plan for regression, related follow-on work, or newly discovered scope; create a concise successor plan with its own scope, tracker, gates, and completion baseline. UI 2.0 Build Plan is closed and must not return to Active.
- The Master Build Tracker should keep completed/monitoring-only plans out of active tables. Archive them in `Completed Plan History.md` or the owning plan history file, and describe future work as successor-plan triggers rather than reopen triggers.
- [`BuildPlan/Master Build Tracker.md`] should stay compact: keep current priorities, completion/status, and no more than the latest 25 recent checkpoint rows. Do not duplicate long history that can be recovered from git or the owning plan.
- `Restore.md` is a relaunch handoff, not a permanent changelog. It should emphasize the latest state, recent checkpoints, blockers, and next actions. After a restart has consumed it, trimming older detail is acceptable because detailed history belongs in plans, commits, generated inventories, and module docs.
- Do not add progress trackers to stable taxonomy/reference docs unless they are actively being migrated, audited, or decomposed; prefer `Last Reviewed`, `Design Status`, or `Extraction Readiness` fields for mostly static architecture/module docs.
- [`Audits/Architecture Drift.md`] is an active dashboard, not an append-only archive. Keep unresolved drift and recently closed items there; preserve long aligned evidence, resolved extraction history, and old baseline audits in [`Audits/Architecture Drift History.md`](Z:\JARVIS\Docs\Audits\Architecture%20Drift%20History.md). If a drift entry is `aligned` with `Follow-Up: none`, it belongs in history rather than the active dashboard.

## Documentation Lookup and Decomposition
- When answering architecture or codebase questions, use this lookup order by default: active tracker or index, owning build plan, module README or contract doc, generated route/schema/frontend inventory, targeted source code, then full historical docs only if needed.
- If the lookup path fails and source/history must be read broadly, update or create the missing summary artifact when it is practical and in scope.
- Use [`Audits/Documentation Debt.md`] for decomposition targets that should not interrupt the active build. Record the symptom, owner doc, needed summary or split, priority, and trigger.
- Prefer refine-as-we-go cleanup. Do not stop active implementation for a full documentation pass unless the missing documentation is causing repeated errors, unsafe changes, or blocking navigation.
- Cleanups are still encouraged when they keep touched areas tight: when changing a module, update its README/contract if ownership, public API, side effects, dependencies, runtime behavior, or known debt changed.

## Context Window and Token Discipline
- Treat context capacity and token consumption as related but distinct constraints. Use the available context window when it improves reasoning, integration accuracy, or design continuity; avoid consuming tokens on low-signal history, generated dumps, broad logs, or repeated reads.
- Use `rg`, `git diff --stat`, targeted `Get-Content -TotalCount`, and `Select-Object -Skip -First` before reading full files. Read full files only when the local context is genuinely required.
- Avoid reading generated inventories, schema maps, route maps, or large frontend API type files in full unless debugging that generated artifact directly. Prefer targeted search and regenerated output checks.
- Avoid full `Restore.md` reads except on relaunch or when the latest handoff is specifically needed.
- Avoid dumping full Docker Compose build logs into the conversation unless an issue requires the details. For routine rebuilds, run the build, then use health checks, endpoint smokes, `docker compose ps`, or targeted `docker logs --tail` on failing services.
- For Docker failures, escalate from concise status to targeted logs: first health/status, then the failing service tail, then full logs only when the tail does not identify the issue.
- Keep smoke evidence in docs high-signal: absolute local timestamp, endpoint/path, session or artifact ids, observed status/result, and any relevant blocker. Do not paste full command output.
- If a source file, plan, or doc repeatedly requires long reads to answer narrow questions, treat that as a decomposition smell. Prefer creating or updating a module README, index, contract summary, or generated inventory rather than continuing to rely on large file scans.

## Development Debugging Patterns
- Prefer iterative deconstruction when a rich behavior fails and the intended approach is still valuable. Start from the smallest known-good shape, add one meaningful component at a time, and keep passing components instead of reverting to a weaker design by default.
- Make component probes reusable when they expose a real system failure mode. A good probe should name each variant, keep the production route or boundary intact when possible, isolate rendered inputs independently, and record enough prompt/shape/telemetry markers to explain both passes and failures.
- Restart or reset stateful runtimes between isolated model-failure probes when a failed run can poison later evidence. Treat contaminated follow-on failures as invalid until the runtime has been reset and the variant is rerun.
- When a component breaks, repair that component or insertion path rather than removing the whole context category. Preserve the non-breaking prefix as the next accepted baseline and validate the repair with the same additive ladder before activation.

## Object and Domain Modeling Discipline
- Pydantic schemas and frontend API types are boundary DTOs. They are valid for validation, serialization, route contracts, and UI transport, but they are not a substitute for domain objects that own behavior.
- Do not add new wide schema/DTO constructors as the primary implementation shape. If constructing a record needs many loosely related fields, first look for the missing domain object, value object, projection object, policy object, or builder/factory method that should group the behavior and defaults.
- Group behavior with the data that owns its failure modes. Counts, latest-item selection, evidence status, policy recommendations, privacy/disclosure decisions, replay fingerprints, and lane-specific defaults should live behind focused objects or policy classes when they have nontrivial rules.
- Schema records should generally be produced from domain/projection objects through explicit conversion methods or mappers. Accept direct schema construction only for small boundary responses, tests, or simple pass-through records where no behavior is hiding in the call site.
- When touching existing wide constructor patterns, prefer incremental repair: introduce a focused value object or factory for the behavior being changed, add direct tests for that behavior, and keep the outward API schema stable.


## If Relaunching
Start with [`Restore.md`] first.
Do not begin from older transcript context before reading it.
Treat `Restore.md` as the active implementation checkpoint and next-step handoff. After using it to resume, it may be trimmed back toward recent state, blockers, and next actions so future relaunches do not inherit stale history.

Read in this order:
1. [`Architecture.md`]
