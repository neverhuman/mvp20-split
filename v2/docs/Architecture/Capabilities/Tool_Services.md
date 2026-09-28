# Independently Deployable Tool Services

- Design status: recommended service-per-tool deployment model; no cluster or services implemented
- Last reviewed: `2026-09-23 09:41:20` (America/Chicago)
- Implementation boundary: BP-03.01 descriptor identity and pure synthetic selection policy accepted; durable registry/deployments and actual standalone tools remain BP-03.02-.04. This document retains the broader intended design.
- Parent: [Scientific Capability Platform](Capability_Architecture.md)
- Scope: standalone packaging, common invocation protocol, indexing and replica lifecycle

## Tool as an Independent Unit

Package each scientific tool, such as solvency, as its own buildable/versioned unit with README, scientific implementation, schemas, descriptor, dependency lock, contract/scientific fixtures, executable adapter, container recipe and deployment profile. It can run against supplied fixtures without the entire engine. In integrated operation it requires the declared runtime/artifact interfaces, not private engine imports or database access.

One tool package normally owns one cohesive scientific function; related operations may share a package when their scientific/state/dependency boundary is the same and the descriptor makes each operation explicit. A trivial internal helper is not another service. Composite research workflows remain inspectable campaign subgraphs; do not hide a private orchestrator inside a tool.

Common infrastructure governs invocation and observability, not a universal scientific payload or the retired Input/Transform/Retain/Output typology. A solvency calculator, sequence operator and lab adapter have different typed input/output, state and side-effect contracts. None must pretend to produce the same score.

## Identity and Node Index

Extend the existing capability registry into the authoritative node/tool index, not a second catalog. Keep these identities distinct:

| Identity | Meaning |
|---|---|
| Capability ID + contract version | Discoverable scientific operation and its public meaning |
| Tool release + image digest | Exact implementation, dependencies and scientific fixtures |
| Deployment ID | Installed release, environment, resource class and eligibility |
| Replica ID | Ephemeral process/pod serving that deployment |
| Campaign node + activation path | Particular use within a pinned graph/iteration |
| Invocation + attempt/fence | Durable logical work and current authorized execution attempt |

Adding replicas updates deployment inventory/capacity; it does not create additional capabilities or duplicate graph nodes. A Kubernetes Node is a compute host and must not be confused with a campaign node. Registry scientific eligibility is reviewed state; runtime heartbeats provide operational readiness only.

Descriptors include purpose/examples/anti-examples, supported scientific representations/context/units, schema IDs/digests, method/implementation/model/data versions, evidence and uncertainty, authority ceiling, state/checkpoint/replay/cache semantics, side-effect and idempotency class, errors/abstentions, batch support, CPU/RAM/GPU/architecture requirements, time/resource limits, permissions/egress, deployment mode, protocol versions and visualization hints. Runtime addresses, replica health and queue depth are separate mutable inventory. Campaign lockfiles pin scientific identities, never a floating `latest` tag or a pod address.

## Common Execution Protocol

[Graph Runner](../System/Graph_Runner.md) aggregates accepted invocations and owns campaign-level failure/supervision decisions. Tool replicas report progress, result or failure under their attempt fence; they do not independently ask an LLM to reroute the campaign or dispatch peer tools. An explicitly registered model tool may perform its own declared inference, returning a result through the same boundary.

Use the Pydantic/JSON Schema contract architecture for discovery, admission, invocation, heartbeat/progress, completion, cancellation and reason-coded rejection. Discovery exposes declared operation/schema versions. Invocation includes scope, exact tool/contract identity, run/node/activation, logical invocation, attempt fence, deadline/budget, input/artifact references, checkpoint and scoped grants. Completion returns typed outputs, scientific disposition, lineage, checkpoint proposal and verified artifacts.

Default replicated workers claim eligible work from the runtime through an authenticated API. Atomic runtime claims allocate one current attempt/fence; replicas never claim by directly reading the runtime database. A push endpoint is an adapter option with the same admission/identity semantics, not an alternate queue authority. A worker's status response is operational observation; runtime acceptance is authoritative.

Replicas can process distinct invocations/batches concurrently within the one active campaign. Duplicate delivery and restarted containers remain possible; fenced/idempotent runtime acceptance is mandatory. Tool-local memory is scratch or a rebuildable cache. Durable optimizer checkpoints and external-job handles leave the pod before becoming accepted state. No sticky session is required for correctness.

Effectful tools record submission intent and reconcile uncertain outcomes. A stale worker must not issue new effects after losing authority; provider correlation/idempotency remains necessary because a fence cannot undo an already-submitted experiment. Tool services cannot call one another to create hidden campaign transitions. Reviewed external SDK/service dependencies must be declared; scientific composition uses graph nodes.

## K3s / Kubernetes Workload Mapping

Recommended profiles use standard Kubernetes workload types and avoid binding the engine to a cluster-specific workflow controller:

| Workload | Deployment shape | Engine responsibility |
|---|---|---|
| Warm calculator or model-serving tool | Deployment with bounded replicas; internal Service only when an inbound endpoint is needed | Route only pinned eligible work; size batches to amortize network/serialization cost |
| Expensive finite simulation | Job for a bounded task or batch | Bind attempts explicitly; pod/Job completion does not mean accepted scientific result |
| Stateful search step | Replaceable worker receiving an explicit checkpoint | Commit new checkpoint through runtime; never make a pod the only optimizer-state owner |
| Remote scientific provider | Registered adapter deployment | Authenticate, retain provider correlation and reconcile uncertainty |

[Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/) manage replicated application pods. [Jobs](https://kubernetes.io/docs/concepts/workloads/controllers/job/) manage finite work and can recreate pods; their retries must be coordinated with engine attempt ownership. Prefer runtime-controlled scientific retry; a restarted process validates/reclaims its attempt before doing work. Do not combine an independent tool queue and Job retry policy that silently repeats expensive/effectful operations.

[K3s](https://docs.k3s.io/) is a lightweight Kubernetes distribution and a candidate single-server deployment for the internal profile. Selection/installation remains pending. The same tool image/protocol should be runnable locally and in K3s or another conforming Kubernetes environment. Not every registered tool needs an always-on pod; deploy on demand or retain a small warm set.

Define startup/readiness/liveness separately; readiness verifies protocol/dependencies, not scientific authority. Set per-tool resource requests/limits, concurrency and model/GPU eligibility. Verify CPU architecture and accelerator support for each target host/image; replication cannot multiply finite GPU memory or CPU capacity. Use explicit service identities, scoped secrets/artifact grants and enforced network policy; containers alone are not sufficient isolation.

## Updating and Rebuilding a Tool

Build and test a new immutable release independently. Publish it as a candidate, evaluate scientific applicability and protocol compatibility, and register eligible deployment capacity. Activate a replacement between campaigns in the initial profile. Keep the previous release available for pinned replay and rollback where permitted. Do not allow a rolling deployment behind a generic service address to send pinned invocations to a different algorithm version; route by release/digest and reject mismatches on the worker.

Scale replicas of the same pinned release subject to resources and admission policy. A deployment change does not alter scientific identity. Graceful termination stops new claims and drains or relinquishes attempts; forced death follows normal fenced recovery. External effects require reconciliation, not automatic resubmission.

Acceptance proves independent build/start and fixtures; schema rejection; two replicas claiming distinct work; duplicate/stale completion rejection; replica death/checkpoint recovery; version-specific routing; unauthorized data/network access rejection; and replacement without changes to unrelated tool code. No cluster is required to prove the pure scientific kernel, but deployment claims require actual target-environment tests.
