# Interfaces and Code Boundaries

- Design status: proposed construction contracts and source layout
- Parent: [System Architecture](System_Architecture.md)
- Scope: how processes and modules communicate without competing authorities

## Command and Query Boundaries

[Contract Architecture](Contract_Architecture.md) owns Pydantic v2 boundary definitions, published JSON Schema, family ownership and cross-language compatibility. This document owns the operations and dependency boundaries that consume those contracts.

Initial external commands pass through the control API into application handlers. Transport routes and implementation language remain to be finalized, but the following semantic operations are concrete boundaries:

| Operation | Required binding | Result / failure |
|---|---|---|
| ProposeCampaign | Objective and source revisions, graph proposal, actor/scope | Draft identity and validation findings; no execution |
| ActivateCampaign | Exact plan hash, lockfile, approved input snapshot, budget and review receipt | Run/command receipt or reason-coded rejection |
| AmendRun | Expected run revision, proposed successor plan, carried-state mapping | Reviewed successor proposal; never silent in-place rewrite |
| ClaimInvocation | Worker identity/class, eligible scope and capacity | Invocation, attempt fence, lease, scoped artifact grants |
| CompleteInvocation | Logical invocation/attempt/fence, result digest, state precondition | Accepted receipt, duplicate receipt or stale/invalid rejection |
| SubmitExternalReturn | Provider/source identity, correlation, result revision and raw artifacts | Reconciled input or explicit unmatched/quarantined disposition |
| PublishKnowledgeChange | Expected graph head, accepted typed change set and review | New revision or conflict; no direct run mutation |
| Intervene | Exact target revision, requested pause/cancel/review action and authority | Attributable transition with in-flight-effect disposition |

Every mutating envelope includes scope, actor/delegation, schema version, command/idempotency identity, request digest and applicable expected revision. Authority is evaluated by handlers, not trusted from caller-supplied labels. Worker completion is a proposal to the committer, not a privileged database write.

Queries specify object/revision or live mode, access scope, projection generation and pagination/cursor. Graph neighborhoods and evidence details are fetched progressively. Cursor/sequence semantics survive reconnects; notifications contain identifiers and revision hints rather than arbitrary private payloads.

## Internal Dependency Direction

```text
transport / process entry points
    -> application command handlers and transaction boundaries
        -> domain objects, graph compiler/interpreter and policies
            -> declared ports for storage, artifacts, tools and model calls

infrastructure adapters implement those ports
scientific plugins implement versioned capability contracts
```

Domain logic cannot import the web framework or provider SDK as its primary behavior model. DTOs validate/serialize the boundary; domain objects enforce invariants. Infrastructure returns explicit failure/uncertainty states rather than exceptions that secretly alter scientific disposition. Query projections may denormalize for performance but cannot become command authority.

## Proposed v2 Source Layout

```text
v2/
  apps/
    control_api/          # transport, authentication and read/command endpoints
    runtime_coordinator/  # durable readiness, attempt dispatch and recovery loop
    worker_runner/        # isolated capability execution and completion reporting
    projection_worker/    # index/UI/lineage builds and recoverable delivery
    studio/               # browser graph and role workspaces
  engine/
    graph/                # typed definitions, compiler, control instructions
    runtime/              # interpreter, activation paths, state/attempt policies
    application/          # command handlers and transaction orchestration
    domains/              # research, knowledge, catalog, agent and data behaviors
    ports/                # repository, artifact, identity and invocation contracts
  adapters/
    persistence/          # transactional implementation and migrations
    artifacts/            # verified local/object-store payload access
    models/               # provider/local inference adapters
    external/             # sources, instruments and laboratory protocols
  capabilities/           # individually versioned scientific tools and fixtures
  contracts/              # versioned transport schemas and compatibility fixtures
  tests/
    contract/
    concurrency_recovery/
    campaign_fixtures/
    user_workflows/
```

This is a proposed source structure, not directories already populated with code. Each meaningful implementation module gets a README describing actual behavior and linking to its intended architecture. The domain documents do not imply one package per paragraph or one process per domain. Language/package conventions may adjust folder names while preserving dependencies and ownership.

## Extension and Release Contract

Modules are intentionally replaceable. Their source-adjacent READMEs own the implemented boundary and must link the schemas, callers/consumers, state/recovery contracts and acceptance fixtures needed for an independent rebuild. Internals are disposable; authoritative evidence and compatibility obligations are not. Replacement activation occurs between campaigns in the initial profile, with old-state handling and rollback/forward-repair recorded. Intended design remains in architecture; the module README states what consumers can actually rely on.

A scientific tool package supplies descriptor, exact implementation/dependency identity, schemas, applicability, state/effect policy and evaluation fixtures. Registration validates compatibility and authority; deployment supplies environment/grants. Campaign bindings pin versions. Code-generating agents may propose packages but cannot register or activate unreviewed code automatically.

Control API, coordinator and workers negotiate supported invocation/contract versions. Unsupported versions reject before work. Release/migration plans must account for outstanding runs and external jobs; changing code does not authorize reinterpreting old checkpoints. A compatibility bridge or explicit successor run is required for incompatible changes.

## Implementation Decisions to Close Next

Pydantic v2 and versioned JSON Schema are the contract direction. Remaining choices include control/runtime language outside that Python boundary layer, web transport/framework, serialization profile and supported version window, PostgreSQL access/migration tooling and first artifact backend. Choose the first capability adapter and the exact synthetic graph fixture. Establish the first profile's limits through tests rather than fabricate latency/scale targets. Do not scaffold all proposed folders until their owning phase has a bounded deliverable.
