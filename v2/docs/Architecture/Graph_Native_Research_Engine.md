# Graph-Native Research Engine

## Status

- Design status: supporting integrated design reference; current decomposition is owned by [Master Architecture](../../Architecture.md)
- Recorded: `2026-09-11`
- Last refreshed: `2026-09-19 15:57:33`
- Scope: flexible campaign execution, neuro-symbolic domain modeling, evolutionary campaign discovery, and deep human graph interaction
- Source influence: KAP research architecture, adapted to Amphora rather than copied as an implementation

## Decision

Amphora will evolve from an epoxy-centered system with predefined optimization pathways into a flexible, graph-native research engine. Executable research campaigns will be configurable graphs whose topology can evolve. Separate neuro-symbolic graphs will describe the knowledge and reasoning boundaries of scientific domains.

The governing principle is:

> Modules define what the system can do; graphs define what it currently chooses to do; evolutionary and LLM processes propose what it might do next; humans inspect and shape why.

Hard-coded modules remain valuable as reliable computational primitives. They are the vocabulary of the engine, not its fixed workflow. Composition, branching, iteration, retained state, and campaign structure belong in executable graph configuration so the system can adapt in complex or changing research environments without requiring a code release for every pathway.

## Composition Across Scientific Domains

Materials, polymer, chemistry, and biological capabilities may be combined in one campaign graph when typed inputs, scientific applicability, and evidence requirements agree. Domain membership is descriptive metadata, not a fixed workflow or a prohibition on cross-domain composition. A delivery campaign can connect polymer/process characterization to release measurements, biological assays, and exposure evaluation; a mechanism campaign can omit materials entirely.

Biological support requires explicit entities and representations for targets, sequences, biological systems, assays, observations, and context-bound claims. Species, tissue/cell system, route, dose/concentration, time, method, controls, and endpoint constrain reuse. Computational plausibility, observed activity, exposure, safety, and therapeutic effect remain distinct claims; a composition cannot acquire more authority than its reviewed evidence supports.

Use the [Evolutionary Code Reuse Baseline](Evolutionary_Code_Reuse_Baseline.md) when selecting existing components. Reusable search kernels do not imply an implemented drug-release/PK model, a biologics design capability, or a generic topology-evolution runtime. See [biological product requirements](Product_Requirements.md#biological-and-cross-domain-research) for acceptance gates.

## Architectural Lineage from KAP

KAP combines knowledge, executable behaviors, links, actions, and history in a graph-oriented research system. Its behavior trees intentionally represent action composition as data, enabling evolutionary growth through configuration rather than limiting behavior to pathways anticipated by developers.

The concepts carried forward are:

- executable behavior graphs
- explicit action-driven change
- explicit tool inputs/outputs, state where needed, and retained execution evidence
- dependency-aware work
- durable execution and failure history
- graph-addressed lineage
- evolutionary modification of behavior structure
- deep human interaction with the graph itself
- local, inspectable research operation

Amphora should implement these ideas using typed module contracts, evidence records, provenance, and scientific assurance gates. The objective is not to reproduce KAP's XML implementation; it is to preserve its configurable and evolutionary research model.

KAP's `Input -> Transform -> Retain -> Output` typology supported dropdown-based wiring of existing functionality within each behavior node. Amphora does not adopt that as a mandatory node lifecycle or configuration template. Its LLM campaign designer discovers the registered functional universe and composes eligible capabilities through their actual contracts; humans inspect and edit the resulting graph. Stateless calculations, stateful search, asynchronous experiments and control gates retain different execution shapes. Contract precision is required; uniform four-stage internals are not.

Working state drives subsequent computation only through declared bindings. Retained artifacts and execution evidence support inspection and recovery without necessarily becoming working state. The runtime enforces persistence and state transitions, tools declare what they need and produce, and campaign edges define consumption. Borrowed concepts must be justified by Amphora use cases and acceptance gates rather than by fidelity to KAP.

## Graph Types

The architecture has two first-class authored graph types and one derived graph-shaped projection:

```text
Neuro-symbolic domain graph
        | constrains and informs
        v
Executable campaign graph
        | instantiates
        v
Execution and provenance projection
        | produces evidence and learning
        +-------------------------------> campaign/domain update candidates
```

Campaign and domain graphs have different semantics and must not be collapsed into an ambiguous generic graph. Execution and provenance lineage is derived from campaign runs rather than independently authored as a competing source of truth.

## Executable Campaign Graph

The campaign graph defines how a research campaign runs and evolves. It replaces fixed epoxy-specific pipelines and predefined genetic-algorithm pathways.

Nodes may represent:

- dataset acquisition and normalization
- molecule, biological candidate, or formulation generation
- reaction-stage construction
- property prediction
- chemistry compatibility or biological mechanism evaluation
- simulation and experimental-design selection
- optimization and novelty search
- uncertainty estimation
- evidence or assurance gates
- human review
- report and protocol packaging

Edges must express more than ordering. The graph language needs typed semantics for data flow, control flow, dependency, conditional activation, branching, joining, iteration, feedback, failure recovery, budget allocation, human approval, and evidence requirements.

### Multi-Stage Reaction Example

```text
Starting materials
        v
Reaction stage 1
        v
Intermediate characterization
        +---- acceptable ----> Reaction stage 2
        |
        +---- unacceptable --> revise precursor or conditions
                                      |
                                      +--> Reaction stage 1
```

The graph retains intermediate materials, conditions, measurements, transformations, and evidence for every stage. This supports reaction plotting, causal inspection, replay, and comparison of alternative pathways.

### Evolutionary Search Space

The evolutionary engine operates over:

1. Parameter evolution within a campaign topology.
2. Topology evolution across modules, edges, branches, evaluators, stage order, and stop policies.

The second space is a defining capability. A campaign graph—not merely a molecule or formulation vector—can be an evolutionary individual. Its genome can include node and module types, module versions, topology, edge conditions, loop policies, parameter ranges, fitness definitions, selection methods, evidence gates, and human intervention points.

Mutation creates descendants rather than overwriting successful designs:

```text
Campaign A v1
  +-- module/topology mutation -----> Campaign A v2
  +-- crossover with Campaign B ----> Campaign AB v1
  +-- human structural revision ----> Campaign A v3
```

## Neuro-Symbolic Domain Graph

The domain graph defines what is known, hypothesized, constrained, or unsupported within a scientific domain. It is not an execution workflow.

For a drug domain:

```text
Compound
  -> binds target
  -> changes pathway
  -> changes cell behavior
  -> produces therapeutic effect
  -> may produce adverse effect
```

Nodes may represent entities, mechanisms, observations, claims, constraints, hypotheses, evidence, and applicability boundaries. Relationships may include `is_a`, `part_of`, `binds`, `inhibits`, `activates`, `causes`, `correlates_with`, `transforms_into`, `requires`, `contraindicates`, `supported_by`, `contradicted_by`, `hypothesized_to`, and `valid_within`.

The relationship vocabulary above is internal to the typed representation. Human domain authors maintain ordinary text documents; the system decomposes them into proposed graph changes. Review shows plain-language meaning against source passages, with graph navigation and optional expert editing. Review corrections must persist as linked document amendments or reviewed overrides so later extraction cannot erase them.

Every scientific assertion should carry:

- evidence and source references
- confidence and evidence strength
- applicability domain and temporal validity
- model, system, or human author
- hypothesis versus established-claim posture
- supporting and contradictory evidence

This gives LLMs and other reasoning systems a bounded scientific environment containing mechanisms, constraints, uncertainty, and unsupported regions rather than an undifferentiated document dump.

Human textual decompositions must become reviewable graph proposals through a versioned extraction prompt and typed validation. [Domain Graph Authoring and Replay](Domain_Graph_Authoring_and_Replay.md) defines the initial prompt, source/identity/evidence requirements, and concurrency protocol. Accepted changes retain both descriptive intent and typed replay operations. Incremental updates and full rebuilds use ordered committed history, revision checks, conflict resolution and atomic snapshot publication; campaigns retain their pinned graph revision until explicit adoption. Re-prompting from a prose changelog is proposal generation, not deterministic replay.

## Configurable Execution

The campaign runtime interprets executable graph configuration:

```text
Registered capabilities and typed contracts
    -> LLM-proposed, human-reviewable campaign graph
    -> Validated tool invocations and graph control constructs
    -> Declared state transitions where needed + retained evidence
    -> Branch, wait, gate, iterate, or terminate
```

It must support module composition, conditional branches, bounded or condition-driven loops, dynamically selected successors, retained state, human decision points, LLM-proposed graph amendments, evolutionary topology mutation, and explicit termination and failure semantics.

Implementation code supplies bounded computational primitives. Configuration determines how those primitives combine. LLMs and evolutionary processes may propose compositions; contract validation, scientific constraints, and human review determine whether a graph is admissible for execution.

## Data Sources and Acquisition

Reusable source registrations describe access, formats, rights, scope, freshness, and supported operations independently of campaigns. Domain packs, products/product envelopes, and projects/programs supply source associations and selection defaults; resolved campaign bindings must preserve authorization boundaries and exact selections.

Acquisition and preparation are executable campaign nodes: query, import, parse, normalize, filter, join, validate, and retain. Reviewed modules accommodate heterogeneous data, documents, molecular structures, images, instrument outputs, and bounded streams through typed contracts. Missing-evidence branches may acquire more data or request experiments within explicit access, cost, retry, freshness, and termination policies.

Outputs are versioned artifacts, linked to source revisions, queries, transformations, quality checks, and execution events. Raw payloads remain in artifact storage. Extracted scientific assertions enter the domain graph through evidence review; acquisition does not confer authority. Source refreshes create new revisions, and runs pin retained inputs or expose replay limitations when retention/versioning is unavailable.

The source registry, connector capabilities, artifact storage, refinery, and Graph Studio share this boundary as specified in [Data Sources and Acquisition](Data_Sources_and_Acquisition.md). It does not introduce another authored graph type.

## Scientific Tool Execution Boundary

[Scientific Tools and Graph Execution](Scientific_Tools_and_Graph_Execution.md) defines the required tool invocation, retained-state, feedback, recovery, and domain-migration contract. A reusable tool version is registered through the capability-node registry; a campaign node binds it to a task, and the runtime owns scheduling and durable state transitions. Graph control constructs remain separate from scientific tools.

Knowledge-engine results and LLM proposals enter through explicit typed feedback ports and reviewed iteration/amendment boundaries. Tools cannot silently change shared campaign state or trusted domain assertions. Polymer, small-molecule, and biological generation require appropriate representations, operators and scientific evaluators under the shared runtime; the current epoxy generator and fixed execution lanes require refactoring, not merely a generic wrapper. The [product tool gates](Product_Requirements.md#tool-delivery-and-acceptance) cover this migration and catalog scale separately from scientific validation.

## Semantic Module Capability Index

An LLM cannot design a reliable campaign from package names or source signatures alone. Every module needs a tightly scoped semantic capability descriptor:

```text
module_id
module_version
human_name
semantic_description
scientific_purpose
input_contracts
output_contracts
preconditions
postconditions
supported_domains
applicability_limits
uncertainty_behavior
cost_profile
runtime_requirements
determinism
side_effects
failure_modes
validation_requirements
compatible_predecessors
compatible_successors
evidence_produced
visualization_metadata
examples
anti_examples
```

The index must explain what scientific question a module answers, what it does not answer, what evidence it requires and produces, how it represents uncertainty, when its output is invalid, and which campaign roles it can fill.

Selection combines deterministic compatibility with semantic retrieval:

```text
Campaign need
    -> contract-compatible module filter
    -> semantic capability retrieval
    -> LLM composition or ranking
    -> graph validation
```

## LLM Campaign Design

An LLM campaign designer receives the research objective, constraints, success criteria, relevant domain-graph projection, module capability index, compute and budget limits, prior campaign patterns and outcomes, and required evidence gates. It returns a proposed graph—not unrestricted execution commands.

Before activation, the graph passes through:

1. Graph-schema validation.
2. Port and type compatibility.
3. Cycle, loop, and termination validation.
4. Resource feasibility.
5. Domain-boundary validation.
6. Evidence sufficiency checks.
7. Simulation or dry run where supported.
8. Human visual review.
9. Explicit activation.

These checks define the physics of the graph language without collapsing the research space back into a predefined pipeline.

## Cross-Project Evolutionary Discovery

Campaign definitions and runs are durable research artifacts:

```text
campaign design
    -> campaign run
    -> intermediate states
    -> final candidates
    -> experimental results
    -> human evaluation
```

Cross-project analysis should discover successful graph motifs, module sequences that generalize across chemistry and biology, failure-prone loops, effective evaluator combinations, topology changes associated with novelty or robustness, and domain-specific versus cross-domain strategies.

Reusable motifs become candidate subgraphs or templates with ancestry, applicability constraints, and result lineage. They must not silently become universal workflows.

## Human Graph Studio

Visualization is a primary reasoning and control interface, not a reporting layer added after execution.

The campaign view should support zoomable nested graphs, typed ports and edges, reaction-stage grouping, live execution state, intermediate artifact inspection, branch activation, loop counts, fitness and uncertainty overlays, campaign-generation comparison, pause/reroute/retry/replace/inject operations, annotations, topology diffs, and time travel through prior runs.

The domain view should support semantic neighborhoods, causal and mechanistic paths, evidence strength, contradictory claims, confidence, applicability boundaries, provenance inspection, hypothesis insertion, alternate explanations, and campaign usage of domain assertions.

Cross-graph traversal is essential:

```text
Campaign module
    -> What knowledge constrained this decision?
    -> highlighted domain subgraph

Domain assertion
    -> Which campaigns depend on this?
    -> impacted campaign nodes and historical runs
```

Human edits are durable, attributable events. The canvas is an editing and reasoning surface over versioned graph state, not transient presentation state.

## Engine Boundaries

```text
Graph Studio
|-- Campaign editor and execution animation
|-- Domain knowledge explorer
|-- Lineage and topology comparison
+-- Human review and intervention

Graph Definition Layer
|-- Campaign and domain graph schemas
|-- Module capability descriptors
+-- Versioning and ancestry

Campaign Runtime
|-- Interpreter and scheduler
|-- Typed data transport
|-- Loop, branch, state, and decision control
+-- Human and LLM gates

Campaign Evolution
|-- Parameter and topology mutation
|-- Crossover, fitness, and novelty search
+-- Cross-project motif discovery

Knowledge Reasoning
|-- Domain traversal and constraint extraction
|-- Evidence/confidence propagation
|-- Hypothesis management
+-- Bounded LLM context projection

Module Registry
|-- Runtime bindings and semantic capability index
+-- Contract, version, and applicability metadata

Data Sources and Acquisition
|-- Source registry and domain/product/project bindings
|-- Reviewed connector and processing capabilities
|-- Campaign acquisition policies and quality gates
+-- Versioned artifacts and evidence-review handoff

Evidence and Provenance
|-- Execution events, artifacts, and scientific evidence
|-- Graph snapshots
+-- Reproducibility receipts
```

## Relationship to Existing Amphora

This direction preserves typed and independently testable scientific modules, explicit evidence production, assurance gates, reconstructible provenance, retained failures and alternatives, and human authority over consequential promotion decisions.

It changes the role of the epoxy workflow. Epoxy becomes one domain pack and one family of campaign graphs used to prove the general engine. It is no longer the shape of the engine itself.

The genetic programming paradigm expands accordingly: candidate-level search remains supported, campaign parameters become evolvable, campaign topology becomes evolvable, and campaign ancestry and outcomes become cross-project learning material.

## Initial Implementation Direction

1. Define versioned campaign-graph and domain-graph schemas.
2. Extend the module manifest into a semantic capability index.
   Include versioned source registrations/bindings and typed connector/processing descriptors; prove acquisition with retained heterogeneous fixtures and explicit replay limits.
3. Define typed ports, edge kinds, loop semantics, and graph validation.
4. Build a deterministic interpreter for a minimal campaign graph.
5. Express one existing epoxy workflow as a graph fixture rather than privileged control flow.
6. Emit execution and provenance events from every node transition.
7. Build the first interactive campaign visualization around that fixture.
8. Add domain-graph projections and campaign-to-domain traceability.
9. Add LLM-proposed graphs behind validation and human activation.
10. Add parameter evolution, then bounded topology evolution and cross-project motif discovery.

## Non-Goals

- Do not replace typed scientific modules with unconstrained LLM execution.
- Do not make the current epoxy pathway the engine's permanent control flow.
- Do not collapse campaign, domain, and provenance semantics into one ambiguous graph schema.
- Do not make visualization a read-only afterthought.
- Do not require hard-coded orchestration changes for every scientifically valid topology.
- Do not promote learned graph motifs without ancestry, applicability, evidence, and human visibility.
