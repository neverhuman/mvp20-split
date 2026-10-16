# SDLC framework

Reusable development processes live here. Architecture describes the system; these pages describe how changes are designed, built, checked, documented and released.

## Load only what the task needs

On resume, read AGENTS and Restore, use the canonical plan tracker to select work, then open the relevant topic below. Do not load every process page by default. Product requirements, owner authorization and declared gates remain binding.

| Task | Process |
|---|---|
| Planning and execution | [Planning and execution](planning/Plan_Execution.md) |
| Documentation and module boundaries | [Documentation and module boundaries](documentation/Documentation_Standards.md) |
| Backend implementation | [Backend implementation](backend/Backend_Principles.md) |
| API and contract development | [API and contract development](api/API_Principles.md) |
| UI implementation | [UI implementation](ui/UI_Coding_Guidelines.md) |
| Verification and diagnostics | [Verification and diagnostics](testing/Testing_and_Coverage.md) |
| Scientific evidence claims | [Scientific qualification](testing/Scientific_Qualification.md) |
| Build and release | [Build and release](delivery/Build_and_Release.md) |
| Audit procedure | [Audit procedure](audits/Audits_and_Closeout.md) |
| Agent workflow | [Agent workflow](agents/Agent_Workflow.md) |
| Provenance and maintenance | [Provenance and maintenance](governance/Provenance.md) |
| Reusable document skeletons | [Templates](templates/README.md) |

## Where facts and decisions stay

- [Architecture](../Architecture/README.md): intended components, protocols, ownership and system invariants.
- Source-adjacent module READMEs: actual behavior, public boundaries and rebuild requirements.
- [Master Build Tracker](../Build%20Plans/Master%20Build%20Tracker.md) and owning plans: priority, progress and evidence.
- [Architecture drift](../Audits/Architecture%20Drift.md), [documentation debt](../Audits/Documentation%20Debt.md) and audit records: findings and disposition.
- [Generated inventories](../Generated/README.md): reproducible implementation facts.
- [Restore](../../Restore.md): exact authorized workspace and interruption.

[Migration audit](../Audits/SDLC_Framework_Separation.md) records the source review and relocation. No implementation percentage, API contract, authority or deployment policy is changed by organizing these documents.
