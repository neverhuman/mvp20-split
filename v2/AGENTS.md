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

## Required process lookup

Read [Restore](Restore.md) for the authorized workspace, source freeze and exact resume task. Read the [SDLC index](docs/sdlc/README.md), then only the process needed for the task:

- [Agent workflow and context](docs/sdlc/agents/Agent_Workflow.md)
- [Planning, progress and interruptions](docs/sdlc/planning/Plan_Execution.md)
- [Documentation and module rebuild contracts](docs/sdlc/documentation/Documentation_Standards.md)
- [Backend and domain modeling](docs/sdlc/backend/Backend_Principles.md)
- [API and contract development](docs/sdlc/api/API_Principles.md)
- [UI design and visual verification](docs/sdlc/ui/UI_Coding_Guidelines.md)
- [Testing and coverage](docs/sdlc/testing/Testing_and_Coverage.md)
- [Build/release and local verification](docs/sdlc/delivery/Build_and_Release.md)
- [Audits and closeout](docs/sdlc/audits/Audits_and_Closeout.md)

## Essential operating boundaries

- Continue-until-needed authorization persists across checkpoints and compaction. A commit or passing gate is not a stopping point; follow the agent workflow.
- Read the [Master Build Tracker](docs/Build%20Plans/Master%20Build%20Tracker.md) and owning tracker before implementing; preserve completed progress and explicit gates.
- No cross-owner private imports or private table access. Runtime alone accepts execution; follow the system isolation contracts.
- Remove owned temporary test containers after every verification, including failures; preserve active services and volumes.
- Keep v1 read-only, credentials/datasets excluded from Git and external workspace access within existing authorization.

- Receipt corrections affect future campaigns only (owner decision, 2026-10-02). Active campaigns retain their pinned receipt revisions, including uncommitted consumption; committed history is immutable. Use explicit owner correction chains/current-selection reads for later campaigns. Do not introduce active-wait invalidation or automatic repinning under this policy.
- Initial product scope is internal/demo, one user and one active autonomous campaign, with domain-general tools and likely later bio-available-polymer use. Human changes take effect between campaigns; do not introduce routine in-campaign human approval gates. Synthetic fixtures are acceptable while scientific sources remain TBA, with no scientific-validity claim.

## Exploratory campaign quality

Campaign completion measures bounded execution, not scientific certainty. Preserve and visibly distinguish weak, contradictory, unknown and inaccurate points without blocking valid exploration solely for evidence quality. Humans and AI agents target improvements between campaigns. Keep explicit action prerequisites and scientific authority intact; never turn an exploratory result into a proven claim. SQ-01 quality/follow-up UI and bounded actual-owner/independent-install acceptance are complete; unresolved diagnostics remain in named successors. Do not infer scientific calibration or reliability guarantees from that implementation.
