# BP-08 Planning History

Archived first draft at `2026-09-25 13:35:12`. Historical task pairs/percentages are not the active execution tracker. The parent and linked children now own progress. Original scope is preserved below for traceability.

# BP-08 Evolutionary Search Integration

## Canonical Execution Tracker

- Status: **proposed / first draft for user review**; implementation not activated.
- Last refreshed: `2026-09-24 12:10:07` (America/Chicago).
- Owner/scope: Search domain modules and independently packaged scientific operators.
- Parent: [Master Build Tracker](../../Master%20Build%20Tracker.md); baseline: local architecture and BP-01/BP-01A completed foundation, BP-02 active protocol work.
- Overall implementation: **0%**; 10 equally weighted verified tasks, two per phase. Overall = completed tasks / 10; phase = completed tasks / 2. Drafting earns no implementation credit.
- Current phase/task: none; proposed plan.
- Next task: incorporate review, then verify predecessor gates and run the bounded pre-activation coherence audit before P1/T1.
- Prerequisites: Completed BP-04 iteration/checkpoint and BP-06 evidence; BP-07 before LLM-guided topology acceptance.
- Completed implementation/evidence: none. All phase gates remain pending.
- Blockers: predecessor gates are not complete; decisions below block only their dependent tasks.
- Human acceptance: draft is available for review; no approval inferred for dependent deployment/provider actions. Campaigns remain autonomous with human changes between campaigns.
- Active exception: none.
- Draft coherence check: `2026-09-24 12:01:26`; ownership, ordering, scoped tests and handoffs checked against [owning architecture](../../../Architecture/Campaigns/Search.md). This is not the implementation activation audit.

| Phase / status | Completion | Dependency | Required exit |
|---|---:|---|---|
| P1 Reuse and search contracts / proposed | 0% | Completed predecessor gates and activation audit | T1-T2: Reference numeric fixtures establish intended kernel behavior; no source copy without ownership and version traceability; resume inputs are complete and malformed checkpoints reject. |
| P2 Graph-driven numeric evolution / proposed | 0% | P1 exit | T3-T4: Seeded replay and resumed versus uninterrupted runs match the defined deterministic tolerance; late results cannot silently alter a committed generation. |
| P3 Representation and fitness boundaries / proposed | 0% | P2 exit | T5-T6: Wrong representation, dimensions, non-finite values, missing/uncertain evidence and all-infeasible populations cannot receive attractive default fitness; objective/authority mutation is forbidden. |
| P4 Topology successors and comparison / proposed | 0% | P3 exit | T7-T8: No active graph hot-swap, unregistered capability or relaxed hard constraint; lineage explains accepted/rejected topology proposals; results report seeds, budgets and variance. |
| P5 Recovery and closeout / proposed | 0% | P4 exit | T9-T10: No historical score reused outside its declared context; accepted selection receipts remain replayable; real scientific validation remains a separately scoped successor. |

## Outcome and Boundaries

Run inspectable reproducible evolutionary search through the graph while separating general numerical search from representation-specific chemistry/biology.

Included: Read-only v1 kernel reuse review, explicit search checkpoints, numeric operators, distinct representation adapters, evidence-bound fitness/selection and bounded successor-topology proposals.

Excluded: Treating v1 lineage-only mutation as molecular evolution, universal molecule/polymer generator, novel-drug/material efficacy claims or unrestricted graph self-modification.

Primary services retain private state, dependencies, migrations and module READMEs. Public contracts/clients are the only cross-owner dependencies. Any new schema identifies its consumer/migration impact. No broad backend or shared business/ORM package. Later phases refine earlier boundaries under the current task without reopening closed plans.

## Child Work-Package Register

This parent owns outcomes and sequencing. The named packages below are **scoped, not implementation-ready**. The existing task pairs are requirements for child decomposition, not sufficiently detailed coding instructions. Before activating a package, author its canonical child plan with owned objects/API/storage, transition/algorithm decisions, failure/recovery matrix, named fixtures and replacement gates. Parent progress then rolls up verified child deliverables; do not count these task pairs again. No implementation credit is earned here.

| Child / bounded ownership | Implementation | Prerequisite | Scope to decompose |
|---|---:|---|---|
| BP-08.01 / Reuse and search contracts | 0% | Parent predecessor gates | Review the documented numeric NSGA-II/simplex/feature-GA implementations read-only and choose the smallest kernel with a licensing/dependency/provenance record. Define population/attempt/selection/checkpoint contracts binding RNG state, operator/model/data versions, pending evaluations and immutable objective/constraint policy. |
| BP-08.02 / Graph-driven numeric evolution | 0% | BP-08.01 exit | Adapt the chosen kernel into explicit generation steps behind a standalone tool boundary; retain all attempts, parents, rejects and duplicates. Drive evaluations through BP-04 graphs, checkpoint state, restore across worker replacement and implement finite stopping/batch completion policies. |
| BP-08.03 / Representation and fitness boundaries | 0% | BP-08.02 exit | Implement separate bounded numeric and synthetic polymer/biological representation fixtures/operators with declared legal moves and validation, not shared implicit chemistry assumptions. Assemble eligible objective vectors with units/direction/uncertainty and hard constraints, including purpose-bound synthesis feasibility evidence or explicit unknown; version all selection inputs. |
| BP-08.04 / Topology successors and comparison | 0% | BP-08.03 exit | Use BP-07 proposals for a small allowed graph mutation set; compile and evaluate successor plans with explicit carried-state mapping and separate topology ancestry. Compare numeric evolution with a deterministic baseline strategy under equal budgets/evidence and separate software improvement from scientific claims. |
| BP-08.05 / Recovery and closeout | 0% | BP-08.04 exit | Run independent kernel/operator tests, partial-evaluation and correction scenarios, worker replacement and retained-candidate reevaluation after an explicitly adopted evaluator revision. Update rebuild contracts, reusable-kernel provenance, benchmark limits and scoped drift audit, then archive. |

Readiness gaps are the unresolved decisions below plus concrete storage/API contracts, algorithm choices, test oracles and migration/recovery obligations for each package. Decompose the nearest eligible package first; do not invent distant provider, ontology or deployment decisions merely to fill templates. Child scope remains here until a linked execution plan replaces the register entry. The parent's existing percentages remain 0% because no implementation has occurred.

## Ordered Tasks

### P1 ? Reuse and search contracts

**T1.** Review the documented numeric NSGA-II/simplex/feature-GA implementations read-only and choose the smallest kernel with a licensing/dependency/provenance record.

**T2.** Define population/attempt/selection/checkpoint contracts binding RNG state, operator/model/data versions, pending evaluations and immutable objective/constraint policy.

**Exit:** Reference numeric fixtures establish intended kernel behavior; no source copy without ownership and version traceability; resume inputs are complete and malformed checkpoints reject.

### P2 ? Graph-driven numeric evolution

**T3.** Adapt the chosen kernel into explicit generation steps behind a standalone tool boundary; retain all attempts, parents, rejects and duplicates.

**T4.** Drive evaluations through BP-04 graphs, checkpoint state, restore across worker replacement and implement finite stopping/batch completion policies.

**Exit:** Seeded replay and resumed versus uninterrupted runs match the defined deterministic tolerance; late results cannot silently alter a committed generation.

### P3 ? Representation and fitness boundaries

**T5.** Implement separate bounded numeric and synthetic polymer/biological representation fixtures/operators with declared legal moves and validation, not shared implicit chemistry assumptions.

**T6.** Assemble eligible objective vectors with units/direction/uncertainty and hard constraints, including purpose-bound synthesis feasibility evidence or explicit unknown; version all selection inputs.

**Exit:** Wrong representation, dimensions, non-finite values, missing/uncertain evidence and all-infeasible populations cannot receive attractive default fitness; objective/authority mutation is forbidden.

### P4 ? Topology successors and comparison

**T7.** Use BP-07 proposals for a small allowed graph mutation set; compile and evaluate successor plans with explicit carried-state mapping and separate topology ancestry.

**T8.** Compare numeric evolution with a deterministic baseline strategy under equal budgets/evidence and separate software improvement from scientific claims.

**Exit:** No active graph hot-swap, unregistered capability or relaxed hard constraint; lineage explains accepted/rejected topology proposals; results report seeds, budgets and variance.

### P5 ? Recovery and closeout

**T9.** Run independent kernel/operator tests, partial-evaluation and correction scenarios, worker replacement and retained-candidate reevaluation after an explicitly adopted evaluator revision.

**T10.** Update rebuild contracts, reusable-kernel provenance, benchmark limits and scoped drift audit, then archive.

**Exit:** No historical score reused outside its declared context; accepted selection receipts remain replayable; real scientific validation remains a separately scoped successor.

## Test Ownership and Evidence

Proposed suite locations (create with their modules):

- `tools/<search-kernel>/tests/`.
- `tools/<representation-operator>/tests/`.
- `services/research/tests/fitness/`.
- `services/campaign_runtime/tests/search/`.
- `tests/integration/evolutionary_search/`.

Each owning README maps public behavior, invariants, failure scenarios and measured source paths to module-local test suites. Register source/suite ownership in `dev/test_scopes.json`; extend granular selectors as modules arrive. Run changed-module tests first, affected consumers next, and separate public-boundary integration/E2E only for cross-owner outcomes. Record line and branch coverage with gaps; coverage percentages are not evidence of scientific correctness.

Keep scenario evidence with absolute timestamps, implementation revision, fixture/schema identity, relevant run/artifact IDs and observed outcomes. Unit mocks do not replace required database, process, browser or provider evidence. Record independent build/install and replacement tests for new service/tool boundaries.

## UI Reference Refinement

`2026-09-24 12:10:07`: Use the [interaction reference map](../../../Architecture/Experience/Interaction_References.md) for population/fitness inspection: linked tables and multi-objective plots with eligibility, units, evaluator version and generation context. Implementation and all phase percentages remain 0%; this refines existing tasks.

## Decisions and Handoff

Select one numerical kernel and a small legal topology operator set in P1; avoid implementing every GA at once. Synthetic biological/polymer fixtures establish boundary separation, not working domain predictors. Real synthesis/biology tools need separate method-specific evidence.

## Progress, Scope Changes and Closeout

The canonical tracker owns overall and P1-P5 percentages; mirror them in MBT at every completed task or changed scope and before commit/handoff. Do not activate downstream phases before their predecessor gate. Record review changes and denominator adjustments here; substantial newly discovered scope gets a named successor.

Final phase includes a component-scoped architecture drift audit. Fix blocking drift, explicitly assign nonblocking follow-ups, update module READMEs/inventories and archive only after all defined gates pass. Synchronize MBT, plan index and Restore and repair moved links. Preserve separate acceptance/operational/scientific readiness status; 100% measures this bounded implementation, not the whole product.

Closeout evidence: pending. No implementation, deployment or scientific validation is claimed by this draft.

## Reference refinement 2026-09-25 13:54:17

BP-08.01/.03 now record reference-code limitations and explicit optional polymer fields, unknown-value behavior and material-state-aware equivalence/fitness caching. Numerical and biological adapters remain separate; empty optimizer files establish no reuse capability. Existing implementation deliveries extended with required acceptance cases; all 0%, denominator unchanged. [Reference assessment](../../References/Amphora_Lab_Insights.md) owns provenance and limitations.
