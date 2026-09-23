# Restore

## Current Checkpoint

- Owner direction: `2026-09-22 21:03:27` — general engine, likely bio-available polymers; first many releases internal/demo, one user/one active autonomous campaign, DGX Spark or partner Threadripper. Human changes apply between campaigns; automated feedback continues within pinned authority. Sources TBA; synthetic fixtures unblock foundation work. Scale/SLO commitments deferred. Product Requirements, System/domain contracts, UI rules and module replacement instructions aligned. Remain in architecture mode; next is bounded schema/rule/runtime-transition design and implementation-plan preparation, not runtime activation.

- Readiness review: `2026-09-22 20:57:10` — [Architecture Readiness Review](docs/Audits/Architecture_Readiness_Review.md) finds sufficient structure for a bounded first slice, with nine tracked findings and six owner questions. Remain in architecture mode: resolve first campaign/audience, hosting/LLM egress, autonomy, source/lab inputs and scale/recovery expectations; then align design and audit the implementation plan. No implementation activated.

- Contract architecture checkpoint: `2026-09-22 20:53:09` — [Contract Architecture](docs/Architecture/System/Contract_Architecture.md) records the accepted Pydantic v2 / versioned JSON Schema direction, family ownership, Rust/UI/LLM boundaries, staged validation and compatibility. System now has six immediate children; the master still links only to its nine direct children. Work remains in architecture mode; no runtime plan activated or schemas implemented.

- UI guidance checkpoint: `2026-09-22 20:46:34` — [UI Coding Guidelines](docs/UI_Coding_Guidelines.md) adapts the JARVIS UI 2.0 instructions for Amphora, with mandatory lookup from AGENTS and Development Process. Qdrant is recorded as a future JARVIS implementation reference in the representation architecture, not a selected dependency. Documentation-only task; no runtime or UI implemented. Return point remains the bounded runtime implementation plan.

- System construction checkpoint: `2026-09-22 20:30:31` ? [System Architecture](docs/Architecture/System/System_Architecture.md) now owns runtime topology, compiled graph execution, authoritative state/transactions, command/code boundaries and an end-to-end research loop. User selected single server with separate workers and remote tools. Master now has nine immediate children; the original eight remain functional ownership views. [System plan](docs/Build%20Plans/Completed/System%20Architecture%20Plan.md) is closed for its proposed-design scope; next task is the bounded graph-runtime implementation plan. No runtime implementation has started.

- Architecture depth checkpoint: `2026-09-22 19:04:40` ? all twenty focused contracts now define proposed components/objects, protocols, state/failure boundaries, examples and open decisions; eight domain summaries explain coordination. [Detail plan](docs/Build%20Plans/Completed/Architecture%20Detail%20Plan.md) is closed at 100% with [scoped audit](docs/Audits/Architecture_Detail_Closeout.md). Exact next task remains author/audit the first runtime implementation plan; no active interruption.

- Architecture naming checkpoint: `2026-09-22 18:26:30` — eight domain entry points renamed to `*_Architecture.md`; master and descendant links updated. Architecture describes intended design; code-module READMEs document actual implementation boundaries. Documentation READMEs provide navigation only. This is a bounded naming correction, not a reopened architecture plan.
- Status: graph-native, acquisition, and biological-support requirements captured; reuse baseline and internal engine deck complete; implementation acceptance pending
- Last refreshed: `2026-09-22 21:03:27`
- Active focus: translate Amphora from an epoxy-shaped workflow into a flexible graph-native research engine
- SDLC checkpoint: [Development Process](docs/Development_Process.md) and local [Master Build Tracker](docs/Build%20Plans/Master%20Build%20Tracker.md) incorporate the latest reviewed JARVIS tracker rules. No implementation plan/phase is active. Exact next planning task: author/audit the first bounded runtime implementation plan against the completed architecture hierarchy with phase percentages, prerequisites and exit gates. Active interruption: none.
- Workspace checkpoint: active design/development moved to `v2/`; the existing implementation is frozen under `../v1/`. All 6,097 relocated files matched pre-move hashes before active link repairs. See [repository layout](../v1/REPOSITORY_LAYOUT.md); run `py -3 v1/tools/verify_v1_baseline.py` from the repository root to verify the 6,022-file portable baseline. No v2 runtime has been implemented.
- Representation checkpoint: [Embedding and Representation Layer](docs/Architecture/Product_Requirements.md#embedding-and-representation-layer) now specifies versioned profiles, compatible shared reuse, source provenance, access-aware caching, index migration/rebuild and quality acceptance. Vectors remain derived artifacts; implementation and evaluation are pending.
- Synthesis checkpoint: [Synthesis Feasibility and Route Planning](docs/Architecture/Product_Requirements.md#synthesis-feasibility-and-route-planning) now defines domain-specific route assessment, practical constraints, evidence posture, candidate-search feedback and experimental acceptance. Existing structural gates do not supply this capability; implementation and validation remain pending.
- Experimental feedback checkpoint: [Lab-In-The-Loop Optimization](docs/Architecture/Product_Requirements.md#lab-in-the-loop-optimization) now specifies lab sources, graph-based ingestion/validation, immutable experimental evidence, separate campaign/knowledge feedback, asynchronous recovery and acceptance fixtures. Implementation remains pending.
- Domain authoring UX: ordinary versioned text is the primary human authoring surface; typed predicates are machine-facing. Plain-language review and linked document amendments/overrides preserve corrections through subsequent extraction and replay.
- Domain authoring checkpoint: [Domain Graph Authoring and Replay](docs/Architecture/Domain_Graph_Authoring_and_Replay.md) captures the text-decomposition prompt contract, reviewed typed changes with descriptive history, conflict handling and atomic full-rebuild publication. Prompt evaluation, schemas and replay/concurrency implementation remain pending.
- Authoring clarification: the LLM composes graphs from discoverable registered capabilities and their precise contracts; KAP's four-stage node typology is not required. Tools keep function-appropriate execution shapes, and working state is distinct from retained evidence.
- Tool execution checkpoint: [Scientific Tools and Graph Execution](docs/Architecture/Scientific_Tools_and_Graph_Execution.md) and the [explicit product section](docs/Architecture/Product_Requirements.md#scientific-tools-in-the-execution-graph) now define tool/node/runtime ownership, retained state, knowledge/LLM feedback, catalog-scale acceptance and domain-specific generator migration. These are requirements; runtime and scientific implementation remain pending.
- Latest architecture checkpoint: [Master Architecture](Architecture.md) links only to eight domain children, which own twenty focused leaf contracts. [Coverage](docs/Architecture/Requirements_Coverage.md) assigns all 102 requirement headings; the [documentation plan](docs/Build%20Plans/Completed/Architecture%20Decomposition%20Plan.md) is complete with a scoped drift audit. No runtime implementation is claimed.
- Latest product-spec checkpoint: [`Data Sources and Acquisition`](docs/Architecture/Data_Sources_and_Acquisition.md), with product requirements, domain entities, parameters, and architecture index aligned
- Biological scope: [Product Requirements](docs/Architecture/Product_Requirements.md#biological-and-cross-domain-research) defines mixed materials/biology and biology-only campaign acceptance; AGENTS.md and Architecture.md link the [reuse baseline](docs/Architecture/Evolutionary_Code_Reuse_Baseline.md).
- Latest internal presentation: [AMPHORA Research Engine Internal](docs/Artifacts/INTERNAL_ONLY-AMPHORA_Research_Engine_Internal.pptx), 14 editable slides with presenter notes and a [PDF companion](docs/Artifacts/AMPHORA_Research_Engine_Internal.pdf); [build and content guide](docs/Presentations/README.md).
- Investor positioning: [Engine VC Positioning](docs/Artifacts/AMPHORA_Engine_VC_Positioning.pptx), six core slides plus a source appendix, with a [PDF](docs/Artifacts/AMPHORA_Engine_VC_Positioning.pdf) and [competitive research memo](docs/Presentations/VC_Positioning_Research.md). Differentiation and commercial benefits remain hypotheses pending comparative pilot evidence.
- Latest presentation checkpoint: [`docs/Artifacts/ALB_DeckAddition.pptx`](docs/Artifacts/ALB_DeckAddition.pptx), 27 slides, with the new engine sequence at slides 4–6
- Blockers: none identified for continuing architecture design

## Active Direction

Amphora is being developed as a flexible graph-native research engine rather than a fixed epoxy-specific pipeline.

Two authored graph types are first-class:

- executable campaign graphs define module composition, typed flow, branching, iteration, retained state, multi-stage reactions, human gates, and evolvable topology
- neuro-symbolic domain graphs define entities, mechanisms, causal and evidentiary relationships, uncertainty, applicability, hypotheses, and reasoning boundaries

Execution and provenance lineage is a third graph-shaped projection derived from campaign runs. It is not an independently authored source of truth.

The governing principle is:

> Modules define what the system can do; graphs define what it currently chooses to do; evolutionary and LLM processes propose what it might do next; humans inspect and shape why.

Executable behavior configuration is intentional. Hard-coded modules provide reliable scientific primitives, while graphs allow complex and changing campaign pathways to grow without requiring hard-coded orchestration changes.

Deep graph visualization is part of the engine, not a reporting afterthought. The planned Human Graph Studio must support graph editing, execution inspection, lineage and topology comparison, intervention, and traversal between campaign decisions and the domain knowledge that constrained them.

Epoxy remains a proving domain and source of reusable modules. It is not the fixed control-flow architecture of the engine.

Domain-, product-, and project-specific data sources have reusable versioned registrations. Acquisition and preparation run as campaign nodes; heterogeneous payloads become versioned artifacts; scientific assertions enter domain graphs through evidence review. Source bindings preserve scope/access rules, exact queries and transformations, refresh policy, and replay limits. The new source/acquisition acceptance gates remain unimplemented.

## Session Deliverables

- Created [`Architecture.md`](Architecture.md) as the local architecture entry point.
- Created the canonical [`Graph-Native Research Engine`](docs/Architecture/Graph_Native_Research_Engine.md) reference.
- Updated [`docs/Architecture/README.md`](docs/Architecture/README.md), [`AGENTS.md`](AGENTS.md), and [`HANDOFF.md`](../v1/HANDOFF.md) with the new direction and links.
- Updated [`ALB_DeckAddition.pptx`](docs/Artifacts/ALB_DeckAddition.pptx) in its existing visual style.
- Inserted three investor-facing slides after the original platform overview:
  1. `Research pathways become executable, evolvable graphs`
  2. `Two designed graphs create a compounding evidence graph`
  3. `The engine learns better pathways - not just molecules`
- Renumbered downstream deck pages and visually rendered/reviewed the three additions.

## Recommended Next Steps

1. Define versioned schemas for campaign graphs and neuro-symbolic domain graphs.
   Include source registrations, scoped bindings, acquisition records, and versioned artifact/evidence-bundle contracts from the new acquisition specification.
   Include biological context/applicability and product-design-space contracts. Prove search reuse with rod-depot and oral-matrix synthetic fixtures; biological acceptance also needs an assay-focused campaign without polymer/epoxy nodes.
2. Extend `module-manifest.json` into a semantic capability index with scientific purpose, typed inputs/outputs, applicability, uncertainty, evidence, failure modes, examples, and anti-examples.
   Define tool invocation/state/checkpoint/feedback contracts and first adapt solvency scoring; isolate or rewrite epoxy generation and execution assumptions before proving distinct materials/biology paths. Follow the scientific-tool acceptance gates, including catalog-scale discovery and replay/recovery.
3. Define campaign node ports, edge kinds, branching, loop/termination, retained-state, human-gate, and validation semantics.
4. Build a deterministic minimal graph interpreter.
5. Express one existing epoxy workflow as a graph fixture rather than privileged control flow.
6. Emit reconstructible execution/provenance events for every node transition.
7. Build the first interactive campaign visualization around that fixture.
8. Add domain-graph projections and bidirectional campaign-to-domain inspection.
9. Introduce LLM-proposed campaign graphs behind schema, compatibility, scientific, resource, dry-run, and human activation gates.
10. Add parameter evolution, followed by bounded topology evolution and cross-project graph-motif discovery.

Read first:

1. [v2 workspace guide](README.md) for active boundaries; [`v1/HANDOFF.md`](../v1/HANDOFF.md) is historical operational reference only.
2. [`Architecture.md`](Architecture.md) for the local architecture entry point.
3. Follow the immediate domain children in the master to the focused contract needed for the active task. The earlier integrated graph-engine document remains a supporting reference.

## Workspace Boundary

- The active workspace is `Z:\mvp20-split\v2`; Git metadata remains in `Z:\mvp20-split`. The sibling `v1/` tree is read-only reference material.
- Do not access `Z:\JARVIS` unless the user explicitly requests it; its paths in imported historical notes are examples, not active references.
- KAP informed the graph-native architecture, but future work should use the saved local analysis unless the user explicitly requests another read of `Z:\KAP`.
