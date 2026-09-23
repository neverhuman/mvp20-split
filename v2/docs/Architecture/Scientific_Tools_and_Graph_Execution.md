# Scientific Tools and Graph Execution

## Status

- Design status: proposed execution contract; product requirements captured, implementation pending
- Last refreshed: `2026-09-19 15:51:53`
- Scope: scientific tool catalog, invocation/state/feedback boundaries, and migration of the existing domain-coupled execution layer
- Next gate: versioned tool/invocation contracts and a minimal graph adapter for solvency, followed by distinct generation fixtures
- Deferred: production biological tools, generic topology evolution, and scientific validation beyond existing reviewed applicability

## Purpose and Ownership

Tools provide scientific behavior; campaign graphs compose it; the runtime manages execution state. The neuro-symbolic domain graph supplies reviewed knowledge and reasoning context, while LLMs propose changes. Human Graph Studio makes those interactions inspectable and editable. This is the execution contract behind [Product Requirements](Product_Requirements.md#scientific-tools-in-the-execution-graph), using the existing capability-node registry rather than introducing a parallel tool platform.

| Concept | Meaning and owner |
|---|---|
| Tool definition/version | Reusable capability identity, contract, implementation and dependencies; maintained by its scientific/tool owner |
| Deployment | Installed version and execution environment; managed by platform operators |
| Campaign node instance | Binding of a tool version, ports, parameters, context and state policy; authored in a campaign revision |
| Invocation/attempt | One execution, including retries, under a pinned run/node/iteration identity; managed by the runtime |
| Graph control construct | Branch, join, iteration, review, wait or termination semantics; implemented by the graph runtime |
| Composite tool | A versioned subgraph with explicit ports and visible constituent lineage; subject to the same validation |

A package may implement several capabilities, and a capability may have alternative implementations. Registry identity must describe the callable scientific contract rather than assume one repository directory equals one universal tool. An LLM-facing tool schema is a projection of this same contract; all callers use the same validation and execution boundary.

The LLM composes campaigns from this discoverable functional universe, using each tool's actual contract rather than a mandatory input/transform/retain/output template. Tools may be stateless, stateful or asynchronous; control nodes may only route or gate execution. Human editing uses the same contracts. Persisted evidence is not automatically working state or a feedback input: state needs and downstream consumption must be explicitly declared.

## Required Tool Contract

The semantic descriptor and lifecycle requirements already defined in Product Requirements remain binding. The invocation contract must additionally make these dimensions executable:

| Contract area | Required content |
|---|---|
| Identity and dependencies | Immutable tool/schema/implementation versions or digests; model, dataset, ruleset and environment bindings; owner and lifecycle |
| Scientific purpose | Question answered, method, domain applicability, examples and anti-examples, evidence tier and decision-use ceiling |
| Typed ports | Input/output representations, cardinality, units, reference frames, required context, artifact references and conversion requirements |
| Parameters | Typed configuration, defaults, admissible bounds, fixed versus evolvable values, validation and override authority |
| Knowledge/feedback inputs | Required projection/assertion versions, admissible constraint and feedback types, freshness rules and conflict disposition |
| Execution behavior | Pure calculation, stateful step, asynchronous job or external action; timeout, cost/budget, concurrency, cancellation and retry policy |
| Retained state | State ownership/scope/schema, initial state, read/write set, checkpoint format, merge/conflict rules and reset/migration policy |
| Scientific result | Typed outputs, units, uncertainty, applicability, supporting/conflicting evidence, missing inputs and scientific disposition |
| Operational result | Completion/wait/failure/cancellation state, retryability, checkpoint or external job handle and diagnostic reason |
| Replay and caching | Determinism declaration, seed, dependency fingerprints, side effects, cache eligibility and reproducibility limits |
| Inspection | Human-readable purpose, port/state/result views, evidence links and proposed-change comparison |

Source registrations and datasets are resources, not executable tools. Acquisition/preparation tools turn scoped bindings into versioned artifacts under [Data Sources and Acquisition](Data_Sources_and_Acquisition.md). A custom model is a pinned dependency executed by an eligible inference/training tool; it does not inherit scientific authority from being callable.

Do not force all results into `score_0_1`. A tool may produce a structure, sequence, distribution, curve, constraint report, population, assay dataset or asynchronous experiment handle. Objective construction is an explicit downstream policy/tool with units, direction, applicability and evidence eligibility. Missing or inapplicable outputs must not become favorable zero-valued fitness.

## Invocation, State and Recovery

An invocation must bind campaign revision, node identity, run/iteration/attempt identity, tool and dependency lockfile, input artifact hashes, parameter snapshot, domain projection, feedback references, seed, resource allowance and access scope. Large context travels as scoped, authorized artifact/projection references rather than copying the entire knowledge graph or tool catalog into every call.

1. Resolve inputs and verify representation, scientific applicability, evidence eligibility and resource/access prerequisites.
2. Read a pinned state snapshot and record the invocation before work starts.
3. Run the bounded tool; retain output artifacts, diagnostics, uncertainty, external handles and proposed state changes.
4. Validate outputs and atomically commit the accepted state transition and execution events against the expected state revision.
5. Route the operational and scientific dispositions through declared graph edges. Record branch reasons, rejected outputs and termination decisions.

Pure calculators need not implement feedback or state. A stateful optimizer may own algorithm-specific population/checkpoint contents, but the runtime owns their durable versioning and when another step may consume them. Campaign, node, iteration and candidate scopes must be distinct. Parallel branches cannot overwrite each other's state; joins require explicit merge or conflict handling. State schema changes require a reviewed migration or a new run, never silent reinterpretation of a checkpoint.

Retries must preserve logical invocation identity while recording distinct attempts. External job submission needs a deduplication key and reconciliation against the retained provider handle; where provider guarantees are insufficient, ambiguous completion must pause for reconciliation instead of blindly repeating an experiment. Cancellation does not imply an already-submitted external action was undone. Side effects require declared compensation or an explicit unresolved outcome.

Cache keys must include every declared result-affecting input, parameter, seed, state, tool/model/data version and knowledge/feedback snapshot. Cached results retain their original provenance and cannot cross unauthorized scopes. Deterministic fixtures must replay exactly; nondeterministic and external work must declare what can be reconstructed versus recomputed.

## Explicit Feedback Loop

```text
Reviewed domain projection + objective + retained attempts
    -> generation/search step using a domain-specific representation
    -> validation and scientific evaluation tools
    -> retained results + eligible fitness/constraint construction
    -> selection / experiment / review
    -> accepted feedback for the next declared iteration

LLM proposal -> typed change -> applicability/authority/graph checks
    -> authorized iteration update or reviewed graph amendment

New observations -> evidence review -> new domain-graph revision
    -> explicit adoption at an iteration/review boundary
```

Feedback must identify target candidate/population/node, source observations/assertions, producing reasoner/model, proposal rationale, confidence/uncertainty, validity scope, proposed change and acceptance status. Capture the LLM request context, model/configuration and actual response as provenance within access/retention policy. A recorded LLM output is replay evidence, not a guarantee that calling the model again returns the same answer.

Neuro-symbolic outputs must distinguish hard reviewed constraints, defeasible guidance, unresolved contradictions and hypotheses. An LLM cannot override a hard constraint with a persuasive explanation. Conflicting or stale feedback triggers the graph's explicit refresh, abstention or review path. Tools may emit candidate assertions; promotion to trusted domain knowledge remains separate.

Changes within an already authorized parameter/feedback envelope may proceed under its policy. Changes to fixed objectives, scientific authority, tool versions, topology or knowledge scope require the corresponding reviewed revision. Record accepted and rejected proposals. Bound iterations by declared stop conditions and budgets, and detect exhausted search/no feasible candidates without inventing success.

## Domain-Specific Generation and Search

Use a shared execution protocol with separate domain representations, generators, variation operators, repair/validity rules, evaluators and objective policies. Domain objects own these behaviors; wide DTOs and arbitrary JSON fields are transport boundaries, not the scientific model.

| Capability family | Examples of explicit representation/context | Migration posture |
|---|---|---|
| Polymer/material design | Repeat units, chain architecture/distribution, formulation, composition, processing and geometry as required by the method | Preserve applicable materials kernels; isolate epoxy-specific role, cure and fitness assumptions |
| Small-molecule chemistry | Molecular graph, stereochemistry, charge/state, admissible transformations and target/assay context where relevant | Reuse validated identity/chemistry utilities; supply appropriate generation and evaluation policies |
| Peptide/protein or other biological design | Sequence and modifications, structural representation where needed, biological system, target, assay and endpoint | New or independently validated adapters/tools; do not pass through resin/hardener role checks |
| Mixed delivery campaign | Explicit links among active compound, carrier/material, process, measurements and biological context | Compose tools with reviewed mappings; do not flatten distinct objects into one genome by default |

These families overlap scientifically: a peptide is also a polymer, and small molecules may have biological uses. Compatibility is determined by representation, method and validated context, not by a simplistic materials-versus-biology label. A shared SMILES field alone is insufficient.

Parameter search, molecular/sequence variation and campaign-topology search are different search spaces. Each must declare its own genome, operators, admissible changes, fitness and checkpoint semantics. Reusing NSGA-II does not reuse coating objectives or establish biologics generation. Tools must also support campaigns with no evolutionary search.

## Existing Stack Migration

The [source-reviewed reuse baseline](Evolutionary_Code_Reuse_Baseline.md) supplies the evidence for these dispositions. The present [Capability interface](../../../v1/amphora-core/src/capability.rs) evaluates a candidate plus feature snapshot with a run/seed/lineage context; it is not yet the invocation/state/feedback contract described here.

| Existing area | Required treatment |
|---|---|
| `amphora-solvency-score` | First calculator adapter: retain Hansen/precedent applicability and scientific limitations; expose typed inputs/results and reject incompatible contexts |
| `amphora-molecule-generator` / `amphora-molecule-capabilities` | Refactor or rewrite generation coordination; separate reusable chemistry utilities from explicit resin/hardener rules, domain operators and representation validation |
| Engine lane/module dispatch and candidate envelope | Replace fixed workflow selection with graph-bound tool invocation; introduce appropriate domain objects and explicit conversions |
| NSGA-II, simplex and DOE | Reuse reviewed mathematics with typed decoding, domain objectives and retained step/checkpoint integration; do not claim existing synchronous callbacks already support graph feedback |
| Ranking, objective construction and compound workflows | Extract scientific assumptions, eligibility and pairing into explicit policies/tools/subgraphs rather than inherited engine defaults |
| Provenance, authority and evidence infrastructure | Reuse after contract/integration review; preserve quarantine, abstention and existing authority ceilings |

Start with an independently testable solvency adapter and retained existing known-answer fixtures. Next prove separate materials and biology generation/evaluation contracts with synthetic deterministic tools, including deliberately incompatible inputs. Then add a bounded feedback loop with resume and inspectable state. Scientific implementations and validation follow independently; wrapping the legacy generator is not proof of cross-domain readiness. Record per-component keep/adapt/rewrite/new decisions before extraction rather than assuming the whole execution layer is reusable.

## Catalog Scale and Human Use

The catalog must accommodate hundreds of tools through indexed applicability/schema/authority filtering, scoped semantic retrieval and paginated human browsing. Retrieve a bounded candidate set for LLM composition; preserve match/rejection reasons. Registering an implementation behind a supported contract must not require adding a dispatcher case. New scientific domains may require new schemas/adapters, but not a new orchestration engine.

Graph Studio must let scientists inspect and configure tool ports/parameters, developers inspect contract versions and failures, reviewers inspect applicability/evidence, and program leads inspect dependencies/cost/gaps. Show retained inputs/results, feedback consumed, state transitions and iteration differences. Replacing a node must preview compatibility failures and affected downstream results before activating a new revision.

Acceptance is defined in [the product tool gates](Product_Requirements.md#tool-delivery-and-acceptance). The 300-descriptor catalog fixture tests discovery and integration scale; it does not stand in for validated scientific tools. Pin its acceptance profile before evaluation, including latency/prompt budgets and expected compatible/incompatible matches.
