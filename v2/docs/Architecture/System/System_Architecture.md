# System Architecture

- Design status: concrete proposed construction; implementation not started
- Last reviewed: `2026-09-22 21:03:27` (America/Chicago)
- Parent: [Master Architecture](../../../Architecture.md)
- Scope: how the functional domains form one executing, persistent system
- Deployment baseline: user-selected single-server installation with separate worker processes and optional remote scientific tools/model providers. Other system construction choices remain explicit proposals, not implemented guarantees.

## Proposed System

Initial profile: one user and one active campaign for internal use/demos; one server on the owner's DGX Spark or a partner Threadripper host. Multiple worker invocations within the campaign remain supported. Campaign decisions are autonomous under configured authority; human changes take effect in subsequent campaigns. Scientific inputs remain TBA and no polymer-specific execution pathway is privileged. Enterprise capacity and service-level commitments are deferred.

Build a modular control application around a durable graph interpreter. Separate the interpreter's scheduling/commit authority from the processes doing scientific computation. Use a transactional metadata store for authoritative revisions, execution state and decisions; immutable artifact storage for large payloads; and replaceable projections for exploration, retrieval and visualization.

The eight functional domains are internal responsibility boundaries. They are not eight HTTP services, eight databases or eight independent workflow engines. Distribution is initially necessary across unreliable/expensive work and external providers, not across every business noun.

## Architectural Decisions

| Decision | Proposed construction and consequence |
|---|---|
| Execution authority | One campaign execution model and commit protocol. Agents and UI submit commands; workers report results. Only accepted transitions advance a run. |
| Authored graph versus executable plan | Compile a reviewed campaign revision into typed, pinned execution instructions. Validate before activation; interpret control constructs with durable state. |
| Processing split | Control API, runtime coordinator, projection/reconciliation process and isolated workers share versioned contracts. Slow scientific work never holds a database transaction or request thread open. |
| Durable state | Transactional current state plus immutable revisions/events, not an in-memory blackboard and not universal event sourcing. Knowledge's accepted change log retains its specific replay authority. |
| Payload movement | Pass scoped artifact references and typed small values; do not send whole datasets/graphs/populations through every command or LLM prompt. |
| Graph persistence | Initially persist graph definitions, entity/assertion revisions and graph projections behind relational ownership. A dedicated graph database is not the authoritative starting assumption. |
| Feedback | Apply measured/knowledge feedback at declared iteration boundaries. Topology changes create validated successor executions with explicit carried-forward artifacts. |
| Recovery | At-least-once dispatch with fenced/idempotent acceptance, plus explicit reconciliation for external effects. No claim of exactly-once laboratory work. |
| Human interaction | The browser reads revisioned projections and issues expected-revision commands. UI notifications are wakeups; stored execution state is authoritative. |
| Contract infrastructure | Pydantic v2 owns Python boundary definitions; versioned JSON Schema bundles and conformance fixtures govern cross-language interchange. Domain/scientific validation and transactional acceptance remain distinct stages. |

## System Decomposition

- [Runtime Topology](Runtime_Topology.md): processes, communication paths, placement and scaling seams.
- [Graph Execution Model](Graph_Execution_Model.md): compiler/interpreter, control instructions, tokens, iterations and amendments.
- [State and Consistency](State_and_Consistency.md): concrete record ownership, transaction boundaries, artifacts and recovery.
- [Research Loop](Research_Loop.md): one campaign traced across generation, evaluation, knowledge feedback, lab work and graph amendment.
- [Interfaces and Code Boundaries](Interfaces_and_Code_Boundaries.md): command/result protocols, dependency direction and proposed source structure.
- [Contract Architecture](Contract_Architecture.md): Pydantic contract families, schema publication, Rust/UI/LLM adapters, validation and compatibility.

## Consequences and Tradeoffs

A shared control application and transactional store make multi-object invariants reviewable and keep initial deployment manageable. They also create a shared capacity/failure boundary: this first profile is not high availability. Worker isolation prevents long-running calculations from taking ownership of control state, but adds durable dispatch, fencing and reconciliation that must be implemented before parallelism is trusted.

Keeping graphs as typed versioned objects avoids choosing a graph database before traversal requirements are measured. It does not mean arbitrary JSON is the domain model: schema validation, scientific objects and explicit relationships still own behavior. Dedicated graph/vector infrastructure can be introduced as a projection or a separately reviewed migration when measured workloads justify it.

These choices define a falsifiable starting system. Validation must demonstrate graph-driven branching/iteration, one atomic completion, stale-worker rejection, crash recovery, knowledge revision isolation, lab-result reconciliation and usable inspection. Process placement, concrete APIs and tables below are design proposals, not existing code.
