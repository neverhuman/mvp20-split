# Interfaces and Code Boundaries

- Design status: proposed construction contracts and source layout
- Parent: [System Architecture](System_Architecture.md)
- Scope: how processes and modules communicate without competing authorities

## Command and Query Boundaries

[Contract Architecture](Contract_Architecture.md) owns Pydantic v2 boundary definitions, published JSON Schema, family ownership and cross-language compatibility. This document owns the operations and dependency boundaries that consume those contracts.

Initial external commands pass through the control gateway to the owning service API/application handlers. Runtime commands terminate in the campaign-runtime service; scientific domain commands terminate in their respective owners. Transport routes and implementation language remain to be finalized, but the following semantic operations are concrete boundaries:

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

Graph Runner's public engagement seam sends `EngagementRequest` to Agent Planning and receives `EngagementProposal`; Campaign Runtime records `SupervisionDecision` through its own conditional command boundary. The contracts bind decision identity/scope, frontier/input versions and authority. These semantic names remain proposed schemas, not implemented routes. See [Graph Runner](Graph_Runner.md).

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
  services/
    control_gateway/
    campaign_runtime/    # owns compiler, run state, dispatch, commits and budget
    research/
    knowledge/
    data_artifacts/
    capability_registry/
    agent_planning/
    projection_serving/
    identity_policy/
  tools/
    solvency/            # own README, manifest, scientific code, contracts/tests, image
    <scientific-tool>/   # same delivery boundary, tool-specific science
  studio/                # browser application and focused view modules
  contracts/             # decomposed, independently versioned contract families
  sdk/
    tool_protocol/       # transport/claim/artifact mechanisms, no scientific policy
    clients/             # generated/public clients, no service internals
  deploy/                # composition manifests referencing pinned service/tool images
  tests/
    integration/         # public-boundary, recovery and compatibility scenarios
```

Each service owns its internal domain/application/adapters, migrations, dependency manifest, tests and README. Public clients/contracts are the only cross-service dependencies. No broad `backend/`, `engine/domains/` or shared repository/ORM package is permitted. Independent builds, forbidden-import checks and state-access tests enforce the boundaries described in [Service Isolation](Service_Isolation.md). Runtime API and coordinator entry points may share campaign-runtime internals because they belong to that single owner.

This is a proposed source structure, not directories already populated with code. Each meaningful implementation module gets a README describing actual behavior and linking to its intended architecture. The domain documents do not imply one package per paragraph or one process per domain. Language/package conventions may adjust folder names while preserving dependencies and ownership.

## Extension and Release Contract

Modules are intentionally replaceable. Their source-adjacent READMEs own the implemented boundary and must link the schemas, callers/consumers, state/recovery contracts and acceptance fixtures needed for an independent rebuild. Internals are disposable; authoritative evidence and compatibility obligations are not. Replacement activation occurs between campaigns in the initial profile, with old-state handling and rollback/forward-repair recorded. Intended design remains in architecture; the module README states what consumers can actually rely on.

A scientific tool package supplies descriptor, exact implementation/dependency identity, schemas, applicability, state/effect policy and evaluation fixtures. Registration validates compatibility and authority; deployment supplies environment/grants. Campaign bindings pin versions. Code-generating agents may propose packages but cannot register or activate unreviewed code automatically.

Control API, coordinator and workers negotiate supported invocation/contract versions. Unsupported versions reject before work. Release/migration plans must account for outstanding runs and external jobs; changing code does not authorize reinterpreting old checkpoints. A compatibility bridge or explicit successor run is required for incompatible changes.

## Implementation Decisions to Close Next

[Foundation Decisions](Foundation_Decisions.md) selects Python 3.12, Pydantic v2, FastAPI/Uvicorn, PostgreSQL with psycopg 3/SQLAlchemy 2/Alembic and independent package manifests. [State and Consistency](State_and_Consistency.md) links the BP-02 command and artifact protocol decisions. Its first artifact backend is an owned durable local volume; protocol and database evidence remain pending BP-02 gates. General capability routing and graph compilation remain BP-03/04; establish measured profile limits through tests rather than fabricate latency/scale targets. Do not scaffold all proposed folders until their owning phase has a bounded deliverable.
