# Tool Invocation and State Boundaries

- Design status: detailed proposed contract; implementation and scientific acceptance pending
- Naming note: component/record/operation names below are proposed logical design, not implemented APIs or selected deployment technology
- Last reviewed: `2026-09-22 18:56:40` (America/Chicago)
- Parent: [Domain overview](Capability_Architecture.md)
- Requirement source: [Product Requirements](../Requirements/Product_Requirements.md#scientific-tools-in-the-execution-graph)

## Owned Contract

Tools declare typed ports, cardinality, units, context, parameters, evidence, operational/scientific dispositions and state/replay behavior. Outputs include curves, structures, sequences, populations, artifacts and job handles; a universal normalized score is insufficient. Calculators can be stateless; optimizers/async jobs declare checkpoint/resume requirements.

Invocations bind run/node/iteration/attempt, input hashes, dependencies, parameters, projection, feedback, seed and grants. Tools return outputs and proposed state changes. They cannot silently mutate shared state or trusted knowledge. A stateful tool owns checkpoint contents; Campaigns owns durable versions, order and commit.

## Boundary and Flow

[Tool Services](Tool_Services.md) proposes independently packaged services/workloads per scientific tool, a common execution envelope and version-specific replicas. Tool internals remain scientifically specific. Runtime retains claim/fence/acceptance authority; tools have no private cross-service imports or general database access.

Runtime adapters execute implementations within Platform grants. Domain operators own representation validity. Agent-facing schemas project the same contracts without bypasses. Reviewed knowledge and LLM suggestions enter declared feedback ports at authorized boundaries.

## Invariants and Verification

Reuse v1 utilities after applicability review; refactor fixed epoxy lanes and resin/hardener assumptions. Wrappers do not establish biological support. Verify a standalone solvency adapter, separate materials/biology fixtures, incompatible inputs, state isolation, abstention, result validation and explicit side-effect/nondeterminism limits.

## Component and Object Design

| Proposed component | Responsibility |
|---|---|
| Invocation adapter | Translate a validated public contract into a native/library/container/provider call |
| Applicability/input policy | Validate representation, units, context and permitted scientific use |
| Tool implementation | Perform the declared calculation, generation, stateful step or external operation |
| Result/evidence mapper | Validate outputs and preserve scientific disposition, uncertainty and provenance |
| Checkpoint adapter | Serialize/restore tool-owned algorithm state under its versioned contract |

These are proposed logical components, not a mandate for separate processes. Tool results separate operational state, scientific disposition and output artifacts. An abstention includes missing inputs or applicability reasons; it is not an exception with a hidden numeric result. Capability-specific values live in typed domain outputs, not arbitrary metrics that later become undocumented fitness.

## Invocation Contract Example

A solvency invocation consumes a candidate/formulation revision, required material-property references, temperature/context and a pinned method profile. It emits method-specific quantities, applicability, uncertainty and evidence. A downstream fitness policy decides whether and how those quantities count. It must reject an unrelated sequence input even if a caller labels it 'molecule'.

A generator consumes domain-specific seeds/design space and authorized feedback, returns candidate attempts and checkpoint changes, and never owns the surrounding campaign loop. A tool can be independently tested with a supplied context and artifact resolver, without booting the entire research system.

## Failure and Recovery Boundary

Adapters classify input failure, unavailable dependency, scientific abstention, retryable operational failure and uncertain external completion separately. Output validation occurs before Campaigns commits state. Cache eligibility declares all result-affecting inputs and side effects; a cached result retains original evidence and does not count as an independent experiment.

## Design Basis and Open Decisions

[Scientific Tools and Graph Execution](../Requirements/Scientific_Tools_and_Graph_Execution.md) is the detailed source. Remaining decisions: adapter ABI/protocol, sandbox profiles and state-schema migration. Existing v1 `Capability.evaluate` is a reuse candidate, not the complete v2 invocation contract.
