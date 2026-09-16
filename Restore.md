# Restore

## Current Checkpoint

- Status: graph-native architecture and scoped data-acquisition requirements captured; implementation acceptance pending; investor-deck update complete
- Last refreshed: `2026-09-16 11:52:21`
- Active focus: translate Amphora from an epoxy-shaped workflow into a flexible graph-native research engine
- Latest architecture checkpoint: [`docs/Architecture/Graph_Native_Research_Engine.md`](docs/Architecture/Graph_Native_Research_Engine.md)
- Latest product-spec checkpoint: [`Data Sources and Acquisition`](docs/Architecture/Data_Sources_and_Acquisition.md), with product requirements, domain entities, parameters, and architecture index aligned
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
- Updated [`docs/Architecture/README.md`](docs/Architecture/README.md), [`AGENTS.md`](AGENTS.md), and [`HANDOFF.md`](HANDOFF.md) with the new direction and links.
- Updated [`ALB_DeckAddition.pptx`](docs/Artifacts/ALB_DeckAddition.pptx) in its existing visual style.
- Inserted three investor-facing slides after the original platform overview:
  1. `Research pathways become executable, evolvable graphs`
  2. `Two designed graphs create a compounding evidence graph`
  3. `The engine learns better pathways - not just molecules`
- Renumbered downstream deck pages and visually rendered/reviewed the three additions.

## Recommended Next Steps

1. Define versioned schemas for campaign graphs and neuro-symbolic domain graphs.
   Include source registrations, scoped bindings, acquisition records, and versioned artifact/evidence-bundle contracts from the new acquisition specification.
2. Extend `module-manifest.json` into a semantic capability index with scientific purpose, typed inputs/outputs, applicability, uncertainty, evidence, failure modes, examples, and anti-examples.
3. Define campaign node ports, edge kinds, branching, loop/termination, retained-state, human-gate, and validation semantics.
4. Build a deterministic minimal graph interpreter.
5. Express one existing epoxy workflow as a graph fixture rather than privileged control flow.
6. Emit reconstructible execution/provenance events for every node transition.
7. Build the first interactive campaign visualization around that fixture.
8. Add domain-graph projections and bidirectional campaign-to-domain inspection.
9. Introduce LLM-proposed campaign graphs behind schema, compatibility, scientific, resource, dry-run, and human activation gates.
10. Add parameter evolution, followed by bounded topology evolution and cross-project graph-motif discovery.

Read first:

1. [`HANDOFF.md`](HANDOFF.md) for the preserved operational and repository handoff.
2. [`Architecture.md`](Architecture.md) for the local architecture entry point.
3. [`docs/Architecture/Graph_Native_Research_Engine.md`](docs/Architecture/Graph_Native_Research_Engine.md) for executable campaign graphs, neuro-symbolic domain graphs, evolutionary campaign design, the semantic module capability index, and the human Graph Studio.

## Workspace Boundary

- The active workspace is `Z:\mvp20-split`.
- Do not access `Z:\JARVIS` unless the user explicitly requests it; its paths in imported historical notes are examples, not active references.
- KAP informed the graph-native architecture, but future work should use the saved local analysis unless the user explicitly requests another read of `Z:\KAP`.
