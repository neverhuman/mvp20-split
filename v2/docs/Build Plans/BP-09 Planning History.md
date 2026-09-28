# BP-09 Planning History

Archived first draft at `2026-09-25 13:35:12`. Historical task pairs/percentages are not the active execution tracker. The parent and linked children now own progress. Original scope is preserved below for traceability.

# BP-09 Single-Server Integrated Demo and Replacement Proof

## Canonical Execution Tracker

- Status: **proposed / first draft for user review**; implementation not activated.
- Last refreshed: `2026-09-24 12:01:26` (America/Chicago).
- Owner/scope: Local deployment/recovery integration with each service retaining ownership.
- Parent: [Master Build Tracker](Master%20Build%20Tracker.md); baseline: local architecture and BP-01/BP-01A completed foundation, BP-02 active protocol work.
- Overall implementation: **0%**; 10 equally weighted verified tasks, two per phase. Overall = completed tasks / 10; phase = completed tasks / 2. Drafting earns no implementation credit.
- Current phase/task: none; proposed plan.
- Next task: incorporate review, then verify predecessor gates and run the bounded pre-activation coherence audit before P1/T1.
- Prerequisites: Completed BP-05/06/07 and BP-08 for evolutionary demo claims; BP-02/03/04 durability and protocol gates.
- Completed implementation/evidence: none. All phase gates remain pending.
- Blockers: predecessor gates are not complete; decisions below block only their dependent tasks.
- Human acceptance: draft is available for review; no approval inferred for dependent deployment/provider actions. Campaigns remain autonomous with human changes between campaigns.
- Active exception: none.
- Draft coherence check: `2026-09-24 12:01:26`; ownership, ordering, scoped tests and handoffs checked against [owning architecture](../Architecture/System/Runtime_Topology.md). This is not the implementation activation audit.

| Phase / status | Completion | Dependency | Required exit |
|---|---:|---|---|
| P1 Host and deployment profile / proposed | 0% | Completed predecessor gates and activation audit | T1-T2: Host/access choice is required before provisioning; document supported architecture and actual model/tool compatibility. No automatic Kubernetes deployment from a proposed architecture. |
| P2 Reproducible installation and boundaries / proposed | 0% | P1 exit | T3-T4: Fresh install reproduces pinned versions; scientific readiness is separate from process health; measured resource limits and failed-dependency behavior are recorded. |
| P3 Integrated autonomous demonstration / proposed | 0% | P2 exit | T5-T6: Real services and selected model produce the recorded trace; no fabricated evidence or in-campaign human rescue required; unsupported outcomes terminate truthfully. |
| P4 Backup restore and module replacement / proposed | 0% | P3 exit | T7-T8: Restored runs preserve accepted state; no dangling artifacts; unrelated services require no private-code edits. Replicated workload tests are required if cluster replication is claimed. |
| P5 Acceptance and successor handoff / proposed | 0% | P4 exit | T9-T10: All selected-profile gates pass on the actual host; optional deployment features are either explicitly excluded before activation or proven, never silently dropped after failure. |

## Outcome and Boundaries

Deploy and demonstrate the bounded autonomous engine on the selected server, recover its state, and replace one module without breaking its consumers.

Included: Target-host composition, pinned service/tool releases, access/configuration, resource/architecture checks, integrated demo, backup/restore and one between-campaign replacement.

Excluded: Multi-tenant production operations, HA/fleet scaling, compliance certification, unsupported GPU guarantees and unselected cluster installation.

Primary services retain private state, dependencies, migrations and module READMEs. Public contracts/clients are the only cross-owner dependencies. Any new schema identifies its consumer/migration impact. No broad backend or shared business/ORM package. Later phases refine earlier boundaries under the current task without reopening closed plans.

## Child Work-Package Register

This parent owns outcomes and sequencing. The named packages below are **scoped, not implementation-ready**. The existing task pairs are requirements for child decomposition, not sufficiently detailed coding instructions. Before activating a package, author its canonical child plan with owned objects/API/storage, transition/algorithm decisions, failure/recovery matrix, named fixtures and replacement gates. Parent progress then rolls up verified child deliverables; do not count these task pairs again. No implementation credit is earned here.

| Child / bounded ownership | Implementation | Prerequisite | Scope to decompose |
|---|---:|---|---|
| BP-09.01 / Host and deployment profile | 0% | Parent predecessor gates | Confirm DGX Spark or Threadripper access, CPU/accelerator compatibility, storage, model/provider/egress policy and the intended internal/demo exposure. Choose direct process/container composition or explicitly selected K3s profile; pin artifacts, resource bounds, identities/secrets and network policy; define acceptance dataset and resource baseline. |
| BP-09.02 / Reproducible installation and boundaries | 0% | BP-09.01 exit | Build/install service and tool artifacts from independent manifests; configure owned DB roles/volumes and front-door transport for the chosen exposure. Add health/readiness, bounded logs/metrics and run/attempt/artifact correlation; validate secrets separation, denied network/data access and graceful stop/drain. |
| BP-09.03 / Integrated autonomous demonstration | 0% | BP-09.02 exit | Execute the approved source/knowledge/campaign/evidence flow in Studio including deterministic execution, bounded LLM decisions and search if included in the accepted demo. Exercise failure/abstention, corrections and successor campaigns; retain inspectable artifacts, proposal lineage and scope-specific scientific limitations. |
| BP-09.04 / Backup restore and module replacement | 0% | BP-09.03 exit | Define local recovery objectives before the drill; restore a consistent metadata/immutable-artifact snapshot to an isolated environment and verify references/receipts. Rebuild one bounded tool/module from its README/contracts/tests, drain between campaigns, activate a new immutable release and demonstrate rollback or explicit forward repair. |
| BP-09.05 / Acceptance and successor handoff | 0% | BP-09.04 exit | Capture installation, target-host/browser, recovery and replacement evidence; compare measured results to agreed demo/recovery thresholds and list operational limitations. Run scoped architecture drift audit, freeze the accepted demo manifest/runbook and archive; create named successors for capacity, new scientific domains or production hardening. |

Readiness gaps are the unresolved decisions below plus concrete storage/API contracts, algorithm choices, test oracles and migration/recovery obligations for each package. Decompose the nearest eligible package first; do not invent distant provider, ontology or deployment decisions merely to fill templates. Child scope remains here until a linked execution plan replaces the register entry. The parent's existing percentages remain 0% because no implementation has occurred.

## Ordered Tasks

### P1 ? Host and deployment profile

**T1.** Confirm DGX Spark or Threadripper access, CPU/accelerator compatibility, storage, model/provider/egress policy and the intended internal/demo exposure.

**T2.** Choose direct process/container composition or explicitly selected K3s profile; pin artifacts, resource bounds, identities/secrets and network policy; define acceptance dataset and resource baseline.

**Exit:** Host/access choice is required before provisioning; document supported architecture and actual model/tool compatibility. No automatic Kubernetes deployment from a proposed architecture.

### P2 ? Reproducible installation and boundaries

**T3.** Build/install service and tool artifacts from independent manifests; configure owned DB roles/volumes and front-door transport for the chosen exposure.

**T4.** Add health/readiness, bounded logs/metrics and run/attempt/artifact correlation; validate secrets separation, denied network/data access and graceful stop/drain.

**Exit:** Fresh install reproduces pinned versions; scientific readiness is separate from process health; measured resource limits and failed-dependency behavior are recorded.

### P3 ? Integrated autonomous demonstration

**T5.** Execute the approved source/knowledge/campaign/evidence flow in Studio including deterministic execution, bounded LLM decisions and search if included in the accepted demo.

**T6.** Exercise failure/abstention, corrections and successor campaigns; retain inspectable artifacts, proposal lineage and scope-specific scientific limitations.

**Exit:** Real services and selected model produce the recorded trace; no fabricated evidence or in-campaign human rescue required; unsupported outcomes terminate truthfully.

### P4 ? Backup restore and module replacement

**T7.** Define local recovery objectives before the drill; restore a consistent metadata/immutable-artifact snapshot to an isolated environment and verify references/receipts.

**T8.** Rebuild one bounded tool/module from its README/contracts/tests, drain between campaigns, activate a new immutable release and demonstrate rollback or explicit forward repair.

**Exit:** Restored runs preserve accepted state; no dangling artifacts; unrelated services require no private-code edits. Replicated workload tests are required if cluster replication is claimed.

### P5 ? Acceptance and successor handoff

**T9.** Capture installation, target-host/browser, recovery and replacement evidence; compare measured results to agreed demo/recovery thresholds and list operational limitations.

**T10.** Run scoped architecture drift audit, freeze the accepted demo manifest/runbook and archive; create named successors for capacity, new scientific domains or production hardening.

**Exit:** All selected-profile gates pass on the actual host; optional deployment features are either explicitly excluded before activation or proven, never silently dropped after failure.

## Test Ownership and Evidence

Proposed suite locations (create with their modules):

- `deploy/local/tests/`.
- `deploy/<selected-profile>/tests/`.
- `tests/integration/demo/`.
- `tests/integration/restore/`.
- `tools/<replacement>/tests/`.

Each owning README maps public behavior, invariants, failure scenarios and measured source paths to module-local test suites. Register source/suite ownership in `dev/test_scopes.json`; extend granular selectors as modules arrive. Run changed-module tests first, affected consumers next, and separate public-boundary integration/E2E only for cross-owner outcomes. Record line and branch coverage with gaps; coverage percentages are not evidence of scientific correctness.

Keep scenario evidence with absolute timestamps, implementation revision, fixture/schema identity, relevant run/artifact IDs and observed outcomes. Unit mocks do not replace required database, process, browser or provider evidence. Record independent build/install and replacement tests for new service/tool boundaries.

## Decisions and Handoff

User decisions are required for host access, provider/egress, exposure and any cluster adoption before dependent actions. Scope can be reviewed now without those answers. Backup objectives and demo resource thresholds must be set before testing, not retrofitted to results.

## Progress, Scope Changes and Closeout

The canonical tracker owns overall and P1-P5 percentages; mirror them in MBT at every completed task or changed scope and before commit/handoff. Do not activate downstream phases before their predecessor gate. Record review changes and denominator adjustments here; substantial newly discovered scope gets a named successor.

Final phase includes a component-scoped architecture drift audit. Fix blocking drift, explicitly assign nonblocking follow-ups, update module READMEs/inventories and archive only after all defined gates pass. Synchronize MBT, plan index and Restore and repair moved links. Preserve separate acceptance/operational/scientific readiness status; 100% measures this bounded implementation, not the whole product.

Closeout evidence: pending. No implementation, deployment or scientific validation is claimed by this draft.
