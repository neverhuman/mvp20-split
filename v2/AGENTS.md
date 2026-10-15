# AGENTS Notes

## v2 Local Architecture Override

- Production uses Linux with isolated containerized services/workers (owner correction, 2026-10-14). Windows is the current development workstation only; do not propose Windows as the production core OS or infer production OS from the demo host.

- The active workspace is `Z:\mvp20-split\v2`; the Git repository root is its parent. `../v1/` is a read-only implementation baseline; do not modify it. External JARVIS references are provenance only; do not access that workspace unless the user requests it.
- The active architecture direction is [Master Architecture](Architecture.md).
- Amphora is now a flexible graph-native research engine rather than an epoxy-shaped fixed pipeline. It has two first-class authored graph types: executable campaign graphs and neuro-symbolic domain graphs. Execution/provenance lineage is a derived projection.
- Owner correction (2026-10-14): the LLM generates and improves the research/domain graph from the research objective using its own capabilities. Knowledge enhances generation/refinement with context; a populated corpus is not a prerequisite, and source extraction or campaign-graph curation alone does not satisfy this core behavior. RG-01 owns the queued correction after POP-01. Preserve Knowledge's revision/acceptance authority and explicit model-inferred versus evidenced claims.
- Executable graph configuration is intentional: reviewed modules provide bounded primitives, while campaign graphs determine composition, branching, iteration, retained state, and evolvable topology without requiring hard-coded pathway changes.
- Deep human graph visualization and interaction are core engine capabilities, including editing, execution inspection, lineage comparison, intervention, and traversal between campaign and domain graphs.
- The active relaunch handoff is [`Restore.md`](Restore.md); [`v1/HANDOFF.md`](../v1/HANDOFF.md) is historical operational reference, and the local architecture index is [`docs/Architecture/README.md`](docs/Architecture/README.md). These local documents govern active work.
- For existing search-code reuse, read [`Evolutionary Code Reuse Baseline`](docs/Architecture/Evolutionary_Code_Reuse_Baseline.md). It distinguishes implemented numerical/feature evolution from epoxy-specific adapters, lineage-only mutation, and unimplemented campaign-topology evolution. Do not infer drug-release or biological model readiness from reusable search algorithms.
- Materials, polymers, chemistry, and biology are composable capability domains. Campaign graphs may combine them as the research objective requires; neither the epoxy pathway nor the five-product brief fixes the engine's topology. Biological representations, assay context, species, route, endpoint, and evidence applicability must be explicit, and missing capabilities must remain visible gaps.

## Purpose
Short continuity notes for future relaunches so work can resume from the extracted architecture rather than re-reading old source transcripts.

## Local Canonical Docs and SDLC

- Architecture design documents live under `docs/Architecture/`; domain entry points use descriptive `*_Architecture.md` filenames, never `README.md`. They describe intended design, not evidence of implementation. Code-module `README.md` files live beside source and describe actual responsibilities, service/state boundaries, interfaces, dependencies and limitations, linking to their owning architecture. Documentation-directory READMEs are navigation guides only. Drift audits compare the two roles; do not treat them as interchangeable contracts.
- [Development Process](docs/Development_Process.md) is the governing v2 SDLC contract, including the current JARVIS tracker refinements reviewed on `2026-09-22 13:47:22`.
- [Architecture](Architecture.md) and [architecture index](docs/Architecture/README.md) own design and decomposed capability boundaries.
- [Master Build Tracker](docs/Build%20Plans/Master%20Build%20Tracker.md) owns program priority; the [plan index](docs/Build%20Plans/README.md) owns navigation.
- [Architecture Drift](docs/Audits/Architecture%20Drift.md), [drift history](docs/Audits/Architecture%20Drift%20History.md) and [Documentation Debt](docs/Audits/Documentation%20Debt.md) are local audit surfaces.
- [Build plan](docs/Templates/Build%20Plan%20Template.md), [module README](docs/Templates/Module%20README%20Template.md) and [plan audit](docs/Templates/Plan%20Audit%20Template.md) templates define the minimum useful contracts.
- JARVIS was reviewed read-only at the user's request. Its live priorities, operating permissions and runtime-specific structure are not Amphora instructions. Routine work uses local docs, with no external workspace access unless requested.

## Canonical Execution Rules

### Continue-until-needed operating rule

- When the owner says to continue until needed, that authorization persists across milestones, commits, pushes, plan boundaries and context compaction. After satisfying the current gate, update canonical trackers and Restore.md, commit/push significant verified work, then immediately take the next authorized task in MBT order.
- A completed milestone, clean working tree, passing tests, successful push or updated handoff is a progress checkpoint, not a reason to end the turn. Report those checkpoints in commentary and keep working. Do not end with "no user decision needed" while authorized work remains.
- Stop only when the authorized scope is complete, the owner pauses/redirects work, or a concrete decision, permission or external blocker prevents further authorized progress. Explain the specific blocker and the smallest owner action needed; complete independent authorized work first. Do not invent approval gates or blockers to justify stopping.
- Context pressure is a reason to refresh Restore.md and preserve exact state, not to request another "continue." Resume from that handoff after compaction. Keep bounded phases, prerequisite gates, scoped verification and audit requirements intact; autonomy does not waive them.


- Enforce strict behavioral and functional isolation: primary services and scientific tools have focused packages, public versioned contracts, private state/dependencies, independent builds/tests and replacement READMEs. Do not introduce a catch-all backend, shared business/ORM layer, private cross-service imports or direct access to another service's tables. Use System Service Isolation and Capability Tool Services designs; runtime alone owns execution acceptance.

- Receipt corrections affect future campaigns only (owner decision, 2026-10-02). Active campaigns retain their pinned receipt revisions, including uncommitted consumption; committed history is immutable. Use explicit owner correction chains/current-selection reads for later campaigns. Do not introduce active-wait invalidation or automatic repinning under this policy.

- Initial product scope is internal/demo, one user and one active autonomous campaign, with domain-general tools and likely later bio-available-polymer use. Human changes take effect between campaigns; do not introduce routine in-campaign human approval gates. Synthetic fixtures are acceptable while scientific sources remain TBA, with no scientific-validity claim.
- Module rewrites are expected. Maintain the source-adjacent README as a sufficient rebuild boundary specification: public contracts, invariants, non-responsibilities, dependencies, state, failure semantics, applicability and replacement acceptance/cutover. Preserve or explicitly version boundaries when replacing implementation. This product direction does not authorize deleting v1 or unrequested files/data.

- Before UI design or coding, read and apply [UI Coding Guidelines](docs/UI_Coding_Guidelines.md). These locally adapted JARVIS rules govern information layout, page-model ownership, truthful state, graph interaction and visual verification.

- Use MBT to select the primary plan, then the owning canonical tracker to select the earliest unmet prerequisite. Keep one active phase and one current task by default; name the next task.
- Before activating a new/queued plan, record a bounded coherence audit under Development Process. Do not re-audit the whole project on ordinary session resumes.
- Before implementation identify task, prerequisites, bounded deliverable, verification and exit gate. Each phase is a discrete delivery and required gates must pass before dependent work starts.
- Owning trackers are authoritative for execution position, overall/per-phase numeric implementation percentages, completed deliveries, evidence and blockers. MBT mirrors status and owns priority; Restore points to the exact resume task and interruption.
- Update the tracker as each bounded task completes or changes, before commit/handoff; synchronize affected MBT and Restore. Investigate only concrete discrepancies, correct the canonical record with evidence, and do not reconstruct project status from code impressions.
- Preserve overall/per-phase percentages with their basis. Implementation at 100% is distinct from required human acceptance and permission to progress. State exactly which next phase an acceptance decision blocks.
- Completed phases remain complete when later work adjusts their schemas/APIs/stores. Record those adjustments under the current phase with compatibility/migration/regression evidence. Invalidated prerequisite assumptions instead require an explicit blocker and design/dependency decision.
- Out-of-order exceptions require user interruption, a blocking defect or demonstrated independence. Record scope, reason, verification and exact return point before switching; return afterward. Material scope/sequence changes need owner direction; routine blocking repairs do not need unnecessary permission requests.
- Assign nonblocking discoveries to future phases/debt. Preserve completed downstream credit without treating it as authority to bypass prerequisites. Never weaken gates, silently reset percentages or defer required scope just to claim completion.
- Every plan closeout requires a component-scoped architecture drift audit before archival. Resolve acceptance-blocking drift, assign nonblocking follow-ups, update drift records and archive/repair links in the same closeout. Closed plans stay closed; later scope uses successors.
- Decompose architecture into owned contracts and hierarchical plans. Each meaningful code module needs a nearby README defining responsibilities, non-responsibilities, interfaces, reads/writes, dependencies, state/runtime/privacy/scientific boundaries, verification and audit hooks. Update it when those boundaries change.
- Use generated inventories for volatile implementation facts once generators exist; do not invent implementation evidence. Follow design -> module contract -> inventory/source -> drift traceability.
- Use absolute local timestamps with seconds (`YYYY-MM-DD HH:mm:ss`, America/Chicago). Active docs expose current state near the top; static references use review fields. Keep long history separate and MBT checkpoints capped at 25.
- `Restore.md` is a concise relaunch handoff, not a permanent changelog. Keep completed plans out of active tables. Leave `Input.md` empty unless populated by the user.

## Documentation Lookup and Decomposition
- When answering architecture or codebase questions, use this lookup order by default: active tracker or index, owning build plan, module README or contract doc, generated route/schema/frontend inventory, targeted source code, then full historical docs only if needed.
- If the lookup path fails and source/history must be read broadly, update or create the missing summary artifact when it is practical and in scope.
- Use [Documentation Debt](docs/Audits/Documentation%20Debt.md) for decomposition targets that should not interrupt the active build. Record the symptom, owner doc, needed summary or split, priority, and trigger.
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

- Remove temporary test containers after their verification completes (owner instruction, 2026-10-14). Do not leave stopped test containers accumulating. Distinguish temporary fixtures from the active demo and explicitly retained recovery state; preserve user data and volumes unless their removal is authorized. Test workflows must include owned-container cleanup.
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

## Test Ownership and Tracker Mirrors

- Keep tests under their owning module's `tests/`, with behavioral subfolders and focused commands. Register source/test ownership in `dev/test_scopes.json`; maintain behavior/coverage gaps in module READMEs. Shared test tooling is owned by dev. E2E is a separate acceptance tier.
- Canonical plan trackers always expose numeric overall and per-phase completion. Mirror those values in MBT for every in-flight plan whenever progress/scope changes and before handoff/commit; archive completed rows.

## Exploratory campaign quality

Campaign completion measures bounded execution, not scientific certainty. Preserve and visibly distinguish weak, contradictory, unknown and inaccurate points without blocking valid exploration solely for evidence quality. Humans and AI agents target improvements between campaigns. Keep explicit action prerequisites and scientific authority intact; never turn an exploratory result into a proven claim. SQ-01 quality/follow-up UI and bounded actual-owner/independent-install acceptance are complete; unresolved diagnostics remain in named successors. Do not infer scientific calibration or reliability guarantees from that implementation.
