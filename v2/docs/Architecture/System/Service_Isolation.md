# Service Isolation and Replacement

- Design status: strict behavioral/functional isolation required; deployment profiles proposed
- Last reviewed: `2026-09-23 09:41:20` (America/Chicago)
- Parent: [System Architecture](System_Architecture.md)
- Scope: source, state, dependency and release boundaries for primary services

## Isolation Contract

Every primary service owns one coherent behavior, explicit public contracts, private domain/application code, persistence adapters and migrations, configuration, tests, release entry point and a source-adjacent README sufficient for replacement. No catch-all `backend/`, `engine/domains/`, shared business-service directory or global ORM model package. Splitting files into folders without limiting imports and state access is not isolation.

Consumers depend on versioned contracts and public clients/ports. They cannot import another service's internal domain classes, repositories, handlers or ORM entities, read/write its private tables, or share mutable in-memory state. Shared packages contain narrowly scoped protocol primitives, generated clients and execution SDK mechanisms, not scientific policy or cross-service orchestration. Each shared package has its own owner and compatibility contract.

Services are independently buildable, testable and replaceable. The monorepo remains useful for coordinated contract changes; it does not imply a shared release or environment. Every primary service has an explicit executable/deployment boundary. A local developer composition may start several executables on the same host; it must retain the same contracts and ownership. Co-location is not permission for private imports or table access.

## Primary Ownership Map

| Proposed service/package | Exclusive behavior/state ownership | Boundary |
|---|---|---|
| Control gateway | Browser/integration transport, session handling and request routing | Thin clients to owners; no scientific orchestration or second run database |
| Campaign runtime | Definition compilation, activation, run/attempt/dispatch/checkpoint transitions and execution budget reservations | Runtime-owned API and coordinator executables share only this service's package; one transactional completion authority |
| Research | Objectives, candidates, experiments, sample identity and purpose-specific evidence eligibility | Returns immutable research records/decisions; does not advance campaign state |
| Knowledge | Documents, assertions, accepted change log, rule evaluation and graph publication | Versioned projections/change commands; no implicit edits to pinned runs |
| Data/artifacts | Source and representation registries, artifact finalization, dataset/model lifecycle | Scoped artifact access and immutable manifests; evidence acceptance belongs to Research/Knowledge |
| Capability registry | Reviewed descriptors, exact versions, lifecycle and deployment inventory | Discovery/eligibility contracts; no execution-state scheduler |
| Agent planning | Context assembly, prompt/model bindings and typed proposals | Uses public contracts; cannot activate work outside runtime policy or own a rival campaign queue |
| Projection serving | Rebuildable UI/search/lineage read views and consumer watermarks | Versioned events/read APIs; no source-of-truth writes or direct scans of other services' private tables |
| Identity/policy | Subjects, grants, revocation and policy decisions | Scoped authorization contracts; scientific acceptance stays with its owner |
| Studio | Browser view models, drafts, navigation and rendering | Uses public API; no authority through local UI state |

These are initial behavioral owners, not an instruction to scaffold all packages now. Data/artifacts and Research have focused internal submodules; split a coherent behavior into a successor service when contracts justify it. Do not allow these names to become unlimited containers for unrelated functions. Every package exposes a compact index and decomposed module contracts.

Audit event creation belongs to each consequential domain transaction. A separately running audit projection/export function consumes those commitments; a remote audit HTTP call cannot substitute for atomic state/event binding. Operational metering may project usage, but execution budget reservation remains runtime-owned so parallel workers cannot overspend through a distributed check-then-act race.

## State and Transaction Boundaries

[Graph Runner](Graph_Runner.md) is the campaign-runtime component, decomposed into coordinator, aggregator and supervisor modules. It is not another deployable authority. The separate Agent Planning service owns model/context work and returns proposals; engagement/decision records and their effects on execution belong to Campaign Runtime.

A single PostgreSQL installation may host separately owned schemas/roles in the initial single-server profile. Service credentials grant only owned writes and explicitly published read surfaces. No service traverses another owner's tables as an integration shortcut. Cross-service references are scoped immutable IDs/versions, validated through public contracts; private cross-schema foreign keys and migrations must not tie releases together.

Atomic completion remains inside Campaign Runtime: accepted result envelope/artifact references, attempt fence, run/checkpoint changes, runtime budget and audit/outbox commit together. This transaction does not also commit Research's candidate aggregate or Knowledge's assertions. Those owners consume idempotent commands/events and produce versioned acceptance receipts. Dependent graph steps wait for the relevant receipt; eventual domain acceptance must not be displayed as already committed.

Artifact finalization returns a verified, scoped immutable reference before runtime completion. Publication must protect the reference from garbage collection during commit/acknowledgement windows through a reservation/retention protocol; remote-reference checking alone is insufficient. Cross-service multi-step work uses durable intents, receipts and reconciliation. Never wrap network calls in the runtime's database transaction or pretend there is a distributed atomic commit.

The detailed receipt/reservation schemas and consistency protocol are prerequisite design work before extracting an owner into a separate process. Domain ownership is required immediately; service calls must not be introduced with undefined failure semantics. Initial deployment may share a database server, but not general database credentials or an unrestricted application transaction spanning owners.

## Enforcement and Replacement Gates

- Each service/tool builds and tests from its own dependency manifest and declared workspace packages. Unrelated scientific dependencies must not enter its image.
- Automated import/dependency checks reject private cross-owner imports and cycles. Integration checks reject unauthorized table access and verify public contract fixtures.
- Contract changes identify consumers, support windows and migrations. Pin dependencies; do not require every service to update because a shared convenience library changed.
- A replacement passes boundary fixtures, observable behavior, negative cases and relevant state/recovery tests without relying on old internals. Compare scientific results under declared tolerance and method identity; transport conformance alone is insufficient.
- Finish/drain the active campaign before human-initiated replacements. Preserve old versions, checkpoints and evidence as required for replay; explicitly migrate or reject incompatible state. Rollback means selecting an eligible prior version, not overwriting historical outputs.

## Deployment Direction

Scientific tools are independently packaged service/workload units; their focused deployment contract is owned by the Capability domain. Replication, container scheduling and process restarts supply compute capacity. Campaign execution authority remains in the runtime. Kubernetes adoption is a deployment decision, not a dependency of graph semantics or a reason to collapse ownership into one service.
