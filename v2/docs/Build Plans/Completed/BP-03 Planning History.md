# BP-03 Planning History

Archived first draft at `2026-09-25 13:35:12`. Historical task pairs/percentages are not the active execution tracker. The parent and linked children now own progress. Original scope is preserved below for traceability.

# BP-03 Tool Index and Standalone Execution

## Canonical Execution Tracker

- Status: **proposed / first draft for user review**; implementation not activated.
- Last refreshed: `2026-09-24 12:01:26` (America/Chicago).
- Owner/scope: Capability Registry and independently packaged tools.
- Parent: [Master Build Tracker](../Master%20Build%20Tracker.md); baseline: local architecture and BP-01/BP-01A completed foundation, BP-02 active protocol work.
- Overall implementation: **0%**; 8 equally weighted verified tasks, two per phase. Overall = completed tasks / 8; phase = completed tasks / 2. Drafting earns no implementation credit.
- Current phase/task: none; proposed plan.
- Next task: incorporate review, then verify predecessor gates and run the bounded pre-activation coherence audit before P1/T1.
- Prerequisites: BP-01 contracts and completed BP-02 claim/artifact/authority gates.
- Completed implementation/evidence: none. All phase gates remain pending.
- Blockers: predecessor gates are not complete; decisions below block only their dependent tasks.
- Human acceptance: draft is available for review; no approval inferred for dependent deployment/provider actions. Campaigns remain autonomous with human changes between campaigns.
- Active exception: none.
- Draft coherence check: `2026-09-24 12:01:26`; ownership, ordering, scoped tests and handoffs checked against [owning architecture](../../Architecture/Capabilities/Tool_Services.md). This is not the implementation activation audit.

| Phase / status | Completion | Dependency | Required exit |
|---|---:|---|---|
| P1 Identity and descriptor contracts / proposed | 0% | Completed predecessor gates and activation audit | T1-T2: Reject floating identity, unsupported contracts, mismatched schema digests, missing applicability and invented scientific eligibility. |
| P2 Registry and version routing / proposed | 0% | P1 exit | T3-T4: Registry role cannot read runtime tables; registration is idempotent; wrong-version replicas cannot receive or accept pinned work; dead capacity is unavailable, not scientifically invalid. |
| P3 Worker protocol and independent tools / proposed | 0% | P2 exit | T5-T6: Each tool installs/runs alone; contract negatives pass; API-only worker access; no shared scientific business layer or private service imports. |
| P4 Replicas and replacement proof / proposed | 0% | P3 exit | T7-T8: Two-replica public-boundary tests reject stale results and denied access; build/install and replacement fixtures pass; no exactly-once external-effect claim. |

## Outcome and Boundaries

Discover a pinned tool release, dispatch through the runtime and execute it in independent replicas without shared private code or state.

Included: Registry identities/descriptors, eligibility and deployment inventory; narrow worker SDK; two deterministic synthetic tools with different payload shapes; independent builds and replacement evidence.

Excluded: General graph interpretation, real chemical validity, full model catalog, production remote-provider effects and Kubernetes installation. Solvency reuse is optional follow-on until applicability and dependency evidence are reviewed.

Primary services retain private state, dependencies, migrations and module READMEs. Public contracts/clients are the only cross-owner dependencies. Any new schema identifies its consumer/migration impact. No broad backend or shared business/ORM package. Later phases refine earlier boundaries under the current task without reopening closed plans.

## Child Work-Package Register

This parent owns outcomes and sequencing. The named packages below are **scoped, not implementation-ready**. The existing task pairs are requirements for child decomposition, not sufficiently detailed coding instructions. Before activating a package, author its canonical child plan with owned objects/API/storage, transition/algorithm decisions, failure/recovery matrix, named fixtures and replacement gates. Parent progress then rolls up verified child deliverables; do not count these task pairs again. No implementation credit is earned here.

| Child / bounded ownership | Implementation | Prerequisite | Scope to decompose |
|---|---:|---|---|
| BP-03.01 / Identity and descriptor contracts | 0% | Parent predecessor gates | Define capability, contract, release/image, deployment and replica identities separately; describe units, representations, applicability, side effects, checkpoint, resource/egress needs and authority ceilings. Publish strict descriptors/discovery contracts and positive/negative fixtures; distinguish scientific eligibility from worker readiness. |
| BP-03.02 / Registry and version routing | 0% | BP-03.01 exit | Implement the isolated registry store/API with immutable releases and separately mutable lifecycle/deployment records; no runtime execution-state ownership. Resolve exact campaign bindings against eligible deployment capacity; make health expiry, revocation and draining observable without rewriting pinned identity. |
| BP-03.03 / Worker protocol and independent tools | 0% | BP-03.02 exit | Implement public claim/heartbeat/artifact/completion/cancel clients using BP-02 contracts; worker scratch is disposable and fences never confer permission to create peer work. Package two deterministic tools with distinct typed payloads, such as numeric transformation and sequence metadata; include manifests, locks, descriptors, READMEs, executable adapters and container recipes. |
| BP-03.04 / Replicas and replacement proof | 0% | BP-03.03 exit | Run two replicas against separate invocations; exercise death, lease loss, checkpoint reuse, delayed completion, finite retry and scoped artifact access. Replace one immutable release between campaigns, prove old pins remain old and new pins select new, then run scoped audit and archive. |

Readiness gaps are the unresolved decisions below plus concrete storage/API contracts, algorithm choices, test oracles and migration/recovery obligations for each package. Decompose the nearest eligible package first; do not invent distant provider, ontology or deployment decisions merely to fill templates. Child scope remains here until a linked execution plan replaces the register entry. The parent's existing percentages remain 0% because no implementation has occurred.

## Ordered Tasks

### P1 ? Identity and descriptor contracts

**T1.** Define capability, contract, release/image, deployment and replica identities separately; describe units, representations, applicability, side effects, checkpoint, resource/egress needs and authority ceilings.

**T2.** Publish strict descriptors/discovery contracts and positive/negative fixtures; distinguish scientific eligibility from worker readiness.

**Exit:** Reject floating identity, unsupported contracts, mismatched schema digests, missing applicability and invented scientific eligibility.

### P2 ? Registry and version routing

**T3.** Implement the isolated registry store/API with immutable releases and separately mutable lifecycle/deployment records; no runtime execution-state ownership.

**T4.** Resolve exact campaign bindings against eligible deployment capacity; make health expiry, revocation and draining observable without rewriting pinned identity.

**Exit:** Registry role cannot read runtime tables; registration is idempotent; wrong-version replicas cannot receive or accept pinned work; dead capacity is unavailable, not scientifically invalid.

### P3 ? Worker protocol and independent tools

**T5.** Implement public claim/heartbeat/artifact/completion/cancel clients using BP-02 contracts; worker scratch is disposable and fences never confer permission to create peer work.

**T6.** Package two deterministic tools with distinct typed payloads, such as numeric transformation and sequence metadata; include manifests, locks, descriptors, READMEs, executable adapters and container recipes.

**Exit:** Each tool installs/runs alone; contract negatives pass; API-only worker access; no shared scientific business layer or private service imports.

### P4 ? Replicas and replacement proof

**T7.** Run two replicas against separate invocations; exercise death, lease loss, checkpoint reuse, delayed completion, finite retry and scoped artifact access.

**T8.** Replace one immutable release between campaigns, prove old pins remain old and new pins select new, then run scoped audit and archive.

**Exit:** Two-replica public-boundary tests reject stale results and denied access; build/install and replacement fixtures pass; no exactly-once external-effect claim.

## Test Ownership and Evidence

Proposed suite locations (create with their modules):

- `services/capability_registry/tests/catalog/`.
- `services/capability_registry/tests/deployments/`.
- `sdk/tool_protocol/tests/`.
- `tools/<tool>/tests/`.
- `tests/integration/tool_execution/`.

Each owning README maps public behavior, invariants, failure scenarios and measured source paths to module-local test suites. Register source/suite ownership in `dev/test_scopes.json`; extend granular selectors as modules arrive. Run changed-module tests first, affected consumers next, and separate public-boundary integration/E2E only for cross-owner outcomes. Record line and branch coverage with gaps; coverage percentages are not evidence of scientific correctness.

Keep scenario evidence with absolute timestamps, implementation revision, fixture/schema identity, relevant run/artifact IDs and observed outcomes. Unit mocks do not replace required database, process, browser or provider evidence. Record independent build/install and replacement tests for new service/tool boundaries.

## Decisions and Handoff

Choose the first two synthetic payloads and descriptor depth in P1. Real solvency remains outside acceptance unless explicitly rebaselined with its scientific fixtures. BP-04 consumes immutable lock resolution and callable synthetic tools; BP-09 owns target-host/cluster proof.

## Progress, Scope Changes and Closeout

The canonical tracker owns overall and P1-P4 percentages; mirror them in MBT at every completed task or changed scope and before commit/handoff. Do not activate downstream phases before their predecessor gate. Record review changes and denominator adjustments here; substantial newly discovered scope gets a named successor.

Final phase includes a component-scoped architecture drift audit. Fix blocking drift, explicitly assign nonblocking follow-ups, update module READMEs/inventories and archive only after all defined gates pass. Synchronize MBT, plan index and Restore and repair moved links. Preserve separate acceptance/operational/scientific readiness status; 100% measures this bounded implementation, not the whole product.

Closeout evidence: pending. No implementation, deployment or scientific validation is claimed by this draft.
