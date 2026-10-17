# SDLC framework separation

- Timestamp: 2026-10-16 14:17:15 America/Chicago.
- Scope: owner-requested documentation/process separation; no runtime or scientific behavior changed.
- Disposition: aligned within inspected documentation scope.
- Progress preserved: all POP-01 implementation percentages and gates unchanged.
- Active interruption: process cleanup; return to authorized POP-01/E2.3 in integration worktree.

## Review scope correction

The original aligned disposition covers relocation, retained content and link integrity. It does not establish semantic completeness of the SDLC framework. The owner identified a missing tracker information model; the [process completeness review](SDLC_Process_Completeness.md) records that gap and the broader findings/corrections.

## Source review and disposition

| Source material | Disposition |
|---|---|
| `v2/docs/Development_Process.md` / Hierarchical Plans | [Plan_Execution](../sdlc/planning/Plan_Execution.md) |
| `v2/docs/Development_Process.md` / Tracker and Phase Execution Rules | [Plan_Execution](../sdlc/planning/Plan_Execution.md) |
| `v2/docs/Development_Process.md` / Interruptions and Discovery | [Plan_Execution](../sdlc/planning/Plan_Execution.md) |
| `v2/AGENTS.md` / Progress checkpoints and authorization | [Plan_Execution](../sdlc/planning/Plan_Execution.md) |
| `v2/docs/Development_Process.md` / Canonical ownership | [Documentation_Standards](../sdlc/documentation/Documentation_Standards.md) |
| `v2/docs/Development_Process.md` / Architecture and module decomposition | [Documentation_Standards](../sdlc/documentation/Documentation_Standards.md) |
| `v2/docs/Development_Process.md` / Context and documentation discipline | [Documentation_Standards](../sdlc/documentation/Documentation_Standards.md) |
| `v2/AGENTS.md` / Lookup and decomposition | [Documentation_Standards](../sdlc/documentation/Documentation_Standards.md) |
| `v2/docs/Development_Process.md` / Replacement boundary | [Module_Boundaries](../sdlc/documentation/Module_Boundaries.md) |
| `v2/AGENTS.md` / Required module coverage | [Module_Boundaries](../sdlc/documentation/Module_Boundaries.md) |
| `v2/docs/Development_Process.md` / Closeout drift audit | [Audits_and_Closeout](../sdlc/audits/Audits_and_Closeout.md) |
| `v2/docs/Development_Process.md` / Evidence tiers and exit gates | [Testing_and_Coverage](../sdlc/testing/Testing_and_Coverage.md) |
| `v2/docs/Development_Process.md` / Module-owned verification | [Testing_and_Coverage](../sdlc/testing/Testing_and_Coverage.md) |
| `v2/AGENTS.md` / Development debugging patterns | [Diagnostics](../sdlc/testing/Diagnostics.md) |
| `v2/Architecture.md` / Provider schema isolation example | [Diagnostics](../sdlc/testing/Diagnostics.md) |
| `v2/AGENTS.md` / Objects and domain behavior | [Backend_Principles](../sdlc/backend/Backend_Principles.md) |
| `v2/docs/Architecture/System/Interfaces_and_Code_Boundaries.md` / Dependency direction | [Backend_Principles](../sdlc/backend/Backend_Principles.md) |
| `v2/docs/Architecture/System/Contract_Architecture.md` / Validation and safe failures | [API_Principles](../sdlc/api/API_Principles.md) |
| `v2/docs/Architecture/System/Contract_Architecture.md` / Schema and consumer workflow | [API_Principles](../sdlc/api/API_Principles.md) |
| `v2/docs/Architecture/System/Service_Isolation.md` / Isolation and replacement gates | [Build_and_Release](../sdlc/delivery/Build_and_Release.md) |
| `v2/docs/Architecture/Capabilities/Tool_Services.md` / Tool release and replacement | [Build_and_Release](../sdlc/delivery/Build_and_Release.md) |
| `v2/dev/README.md` / Reproduce from repository root | [Local_Verification](../sdlc/delivery/Local_Verification.md) |
| `v2/dev/README.md` / Granular verification | [Local_Verification](../sdlc/delivery/Local_Verification.md) |
| `v2/AGENTS.md` / Continue-until-needed operating rule | [Agent_Workflow](../sdlc/agents/Agent_Workflow.md) |
| `v2/AGENTS.md` / Context window and token discipline | [Agent_Workflow](../sdlc/agents/Agent_Workflow.md) |
| `v2/docs/Development_Process.md` / Reviewed source and local adaptation | [Provenance](../sdlc/governance/Provenance.md) |

Whole UI guidelines, interaction references and four reusable templates relocated; old callers updated. Development_Process was decomposed and replaced by the SDLC index, not retained as a duplicate rulebook. AGENTS retains startup/product/authorization essentials and task-specific links.

## Architectural material retained

Runtime acceptance, validation pipeline, service/state ownership, version negotiation, tool identity, transactional write sets and UI transport snapshot semantics remain system design. Product Requirements and historical remediation/gap proposals retain their authority/status; planned developer-kit requirements were not relabeled as implemented process. Audit results and generated inventories remain with their evidence owners. Source-adjacent READMEs retain actual module behavior, not copied SDLC handbooks.

## Verification and limits

Local links and fragments in newly authored pages are checked; relocated/edited callers are checked for newly broken targets. Old workflow path references are searched. No hosted CI workflow was found; local gates are documented without claiming automated deployment. No code execution, container/service restart, provider call, fleet access or v1 edit is required by this change. Original pre-existing Restore changes and user artifacts are preserved.

## Review corrections

Kept historical computed-property trust and formulation-lineage constraints in the historical implementation design while extracting its coding guidance. The obsolete universal-stateless-tool assumption was not imported into v2 policy. Root and v2 AGENTS both link the SDLC index. Source templates and caller links were relocated without moving module READMEs away from their code.

## Final verification

Checked 179 moved/edited/new documents and 1504 local links: zero missing targets and zero invalid checked fragments. All six whole-document moves preserve prose exactly after link rebasing. Tracked changes are Markdown only. Scientific-qualification guidance links existing product acceptance without relocating or changing requirements. No hosted CI/CD implementation was added or claimed.
