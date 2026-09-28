# System Architecture

- Design status: construction design with BP-01 contract/validation foundation implemented; durable runtime pending
- Last reviewed: `2026-09-23 19:55:48` (America/Chicago)
- Parent: [Master Architecture](../../../Architecture.md)
- Scope: how the functional domains form one executing, persistent system
- Deployment baseline: user-selected single-server installation with separate worker processes and optional remote scientific tools/model providers. Other system construction choices remain explicit proposals, not implemented guarantees.

## Proposed System

Initial profile: one user and one active campaign for internal use/demos; one server on the owner's DGX Spark or a partner Threadripper host. Multiple worker invocations within the campaign remain supported. Campaign decisions are autonomous under configured authority; human changes take effect in subsequent campaigns. Scientific inputs remain TBA and no polymer-specific execution pathway is privileged. Enterprise capacity and service-level commitments are deferred.

Build isolated primary services around a durable graph interpreter with one runtime transaction owner. Separate the interpreter's scheduling/commit authority from the processes doing scientific computation. Use a transactional metadata store for authoritative revisions, execution state and decisions; immutable artifact storage for large payloads; and replaceable projections for exploration, retrieval and visualization.

The eight functional domains are responsibility views. Primary implementations are strictly isolated service packages with explicit runtime/deployment boundaries, private state ownership and public contracts. They do not map mechanically to eight databases or independent workflow engines. Service Isolation defines the actual owners; one campaign runtime retains execution authority.

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

- [Foundation Implementation Decisions](Foundation_Decisions.md): selected initial language, service stack, independent packaging and wire-profile limits.

- [Runtime Topology](Runtime_Topology.md): processes, communication paths, placement and scaling seams.
- [Graph Execution Model](Graph_Execution_Model.md): compiler/interpreter, control instructions, tokens, iterations and amendments.
- [Graph Runner and Campaign Supervision](Graph_Runner.md): concurrent coordination, aggregation, failure handling and durable LLM engagement under one runtime authority.
- [State and Consistency](State_and_Consistency.md): concrete record ownership, transaction boundaries, artifacts and recovery.
- [Research Loop](Research_Loop.md): one campaign traced across generation, evaluation, knowledge feedback, lab work and graph amendment.
- [Interfaces and Code Boundaries](Interfaces_and_Code_Boundaries.md): command/result protocols, dependency direction and proposed source structure.
- [Contract Architecture](Contract_Architecture.md): Pydantic contract families, schema publication, Rust/UI/LLM adapters, validation and compatibility.
- [Service Isolation and Replacement](Service_Isolation.md): primary service owners, source/state/dependency enforcement and independent replacement.

## Consequences and Tradeoffs

A runtime-owned transactional boundary makes run/attempt/budget invariants reviewable. Separate services publish domain acceptance through explicit receipts and reconciliation; no distributed atomic transaction is assumed. The initial server/database installation remains a shared capacity/failure boundary, not high availability. Tool isolation adds dispatch, fencing, version routing and operational overhead that must be proved before replication is trusted.

Keeping graphs as typed versioned objects avoids choosing a graph database before traversal requirements are measured. It does not mean arbitrary JSON is the domain model: schema validation, scientific objects and explicit relationships still own behavior. Dedicated graph/vector infrastructure can be introduced as a projection or a separately reviewed migration when measured workloads justify it.

These choices define a falsifiable starting system. Validation must demonstrate graph-driven branching/iteration, one atomic completion, stale-worker rejection, crash recovery, knowledge revision isolation, lab-result reconciliation and usable inspection. Process placement, concrete APIs and tables below are design proposals, not existing code.
