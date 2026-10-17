# Documentation and context

Reviewed: 2026-10-16 14:17:15 America/Chicago. Canonical development process; not evidence of implementation.

Architecture owns intended system design. SDLC owns how we design, implement, verify and release changes. Module READMEs remain beside source; audit evidence and plan state remain with their existing owners.


## Purpose and handoff

| Element | Meaning |
|---|---|
| Why it exists | Make the right current facts discoverable without reconstructing history. |
| Inputs | Changed behavior/design, its owner and evidence. |
| Output | An updated authoritative document and repaired navigation, with historical claims separated. |
| Completion test | A reader can locate intent, actual behavior and current state without contradictory authorities. |

## Canonical ownership

UI work also follows [UI Coding Guidelines](../ui/UI_Coding_Guidelines.md), adapted from the user-requested JARVIS UI review. Record UI verification in the owning task and module contract.

| Artifact | Owns |
|---|---|
| [Architecture index](../../Architecture/README.md) and owning design docs | Design intent, boundaries, constraints and staged validation |
| [Master Build Tracker](../../Build%20Plans/Master%20Build%20Tracker.md) | Cross-plan priority, dependencies and primary plan; mirrors execution status |
| Owning plan's top-of-file tracker | Overall/per-phase progress, task position, completed deliverables, evidence, exit gates and blockers |
| Module README beside source | Actual responsibilities, interfaces, state and dependency boundaries |
| Generated inventories | Volatile implementation facts, with generator and source revision |
| [Drift dashboard](../../Audits/Architecture%20Drift.md) | Unresolved or recently closed implementation/design mismatches |
| [Restore](../../../Restore.md) | Exact resume task and active interruption; links to authoritative trackers |

Do not create competing progress ledgers. A routine resume reads the tracker; a new agent/session does not justify re-auditing source or resetting progress. Concrete contradictions require a narrow investigation, an evidence-backed correction to the owner, then synchronization of summaries.

## Architecture and module decomposition

Focused architecture leaves must explain the design, not just summarize requirements: owned components/objects, lifecycle and interactions, state/commit boundaries, failure/recovery scenarios and unresolved decisions. Use the [Architecture Contract Template](../templates/Architecture%20Contract%20Template.md). Proposed names must be labeled as design vocabulary; stack choices and implemented guarantees need separate evidence. Domain summaries explain coordination without repeating their children's protocols.

Use descriptive `*_Architecture.md` filenames for domain architecture entry points. These documents define intended design. A `README.md` beside code defines that module's actual implemented behavior and boundaries, links to the owning architecture and explicitly identifies gaps or planned behavior. Documentation-directory READMEs are navigation guides only; they must not become domain architecture or implementation authorities. Drift review compares design against module documentation and source rather than conflating the two.

Keep the top-level architecture as an integration map. Put detailed behavior in focused capability/domain documents, and use child indexes when a domain becomes too large. Every boundary must name an owner, public contract, data/state ownership, dependencies and verification. Shared contracts have one owner and linked consumers rather than duplicated definitions. Module decomposition follows behavior and failure boundaries, not arbitrary file sizes or JARVIS-specific taxonomy.

Traceability runs both directions: requirement/design claim -> owning plan/task -> module contract -> implementation/inventory -> verification -> drift disposition. Claim status is `planned`, `partial`, `implemented`, `deprecated` or `disputed`. Existing specification text is not proof of an implementation. Use the [module template](../templates/Module%20README%20Template.md) for each meaningful module; small helpers may use a concise parent-owned contract.

Inventories belong in `docs/Generated/` once generators exist. Useful subjects include routes/schemas, tool manifests, graph contracts, stores, configuration, runtime services, events and frontend calls. Record how and from which revision each inventory was generated. Do not populate fake inventories before code exists. Human docs own intent; generated facts help detect divergence.

## Context and documentation discipline

Roadmap parents define outcomes, dependencies and child rollups. A named work-package register is scoped work, not implementation readiness. Before activating its nearest eligible child, resolve owned objects, public contracts, persistence/write sets, state transitions, failure/recovery cases and independent test oracles. Link focused architecture leaves from their immediate owning design; do not expand the master into a list of grandchildren. Decompose further when a child combines independent owners or requires repeated broad reads. File counts are not a maturity target.

Track design readiness, verified implementation and demonstrated integrated behavior separately. Pure design gates remain mandatory but earn no implementation credit. Child trackers own numeric task/phase progress; parents aggregate completed implementation deliveries once. Document changed denominators explicitly in history and synchronize MBT/Restore. A contract fixture may unblock client development before its peer exists, but the actual peer/process integration gate must remain named and cannot inherit fixture-only success.

Read current tracker/index -> owning plan -> module README/contract -> targeted generated inventory -> targeted source. Use history only when that lookup does not answer the question. Keep `Restore.md` focused on restart state, not a changelog. Separate large plans from `<Plan> History.md`; cap MBT checkpoint history at 25 rows. Use absolute local timestamps with seconds and an explicit timezone; keep static reference docs on lightweight review fields instead of progress trackers.

Repeated broad reading indicates missing summaries or decomposition debt. Repair touched boundaries when practical; otherwise record symptom, owner, needed split/summary, priority and trigger in [Documentation Debt](../../Audits/Documentation%20Debt.md). Keep logs and evidence concise with exact revision/artifact identifiers. Isolate failed stateful probes and retain working components while repairing the failing behavior. Domain objects own behavior; transport DTOs do not replace domain models.

## Lookup and decomposition

- When answering architecture or codebase questions, use this lookup order by default: active tracker or index, owning build plan, module README or contract doc, generated route/schema/frontend inventory, targeted source code, then full historical docs only if needed.
- If the lookup path fails and source/history must be read broadly, update or create the missing summary artifact when it is practical and in scope.
- Use [Documentation Debt](../../Audits/Documentation%20Debt.md) for decomposition targets that should not interrupt the active build. Record the symptom, owner doc, needed summary or split, priority, and trigger.
- Prefer refine-as-we-go cleanup. Do not stop active implementation for a full documentation pass unless the missing documentation is causing repeated errors, unsafe changes, or blocking navigation.
- Cleanups are still encouraged when they keep touched areas tight: when changing a module, update its README/contract if ownership, public API, side effects, dependencies, runtime behavior, or known debt changed.
