# BP-07 Planning History

Archived first draft at `2026-09-25 13:35:12`. Historical task pairs/percentages are not the active execution tracker. The parent and linked children now own progress. Original scope is preserved below for traceability.

# BP-07 Autonomous LLM Campaign Supervision

## Archived draft tracker (non-canonical)

- Status: **proposed / first draft for user review**; implementation not activated.
- Last refreshed: `2026-09-24 12:01:26` (America/Chicago).
- Owner/scope: Agent Planning plus runtime-owned engagement and decision modules.
- Parent: [Master Build Tracker](Master%20Build%20Tracker.md); baseline: local architecture and BP-01/BP-01A completed foundation, BP-02 active protocol work.
- Overall implementation: **0%**; 10 equally weighted verified tasks, two per phase. Overall = completed tasks / 10; phase = completed tasks / 2. Drafting earns no implementation credit.
- Current phase/task: none; proposed plan.
- Next task: incorporate review, then verify predecessor gates and run the bounded pre-activation coherence audit before P1/T1.
- Prerequisites: Completed BP-03 discovery, BP-04 runner, BP-05 UI and BP-06 source/knowledge receipts.
- Completed implementation/evidence: none. All phase gates remain pending.
- Blockers: predecessor gates are not complete; decisions below block only their dependent tasks.
- Human acceptance: draft is available for review; no approval inferred for dependent deployment/provider actions. Campaigns remain autonomous with human changes between campaigns.
- Active exception: none.
- Draft coherence check: `2026-09-24 12:01:26`; ownership, ordering, scoped tests and handoffs checked against [owning architecture](../Architecture/Agents/Planning.md). This is not the implementation activation audit.

| Phase / status | Completion | Dependency | Required exit |
|---|---:|---|---|
| P1 Model and engagement contracts / proposed | 0% | Completed predecessor gates and activation audit | T1-T2: Contract tests reject unsupported actions and authority escalation; secrets/data limits apply at the adapter; fake-model success is not live-model acceptance. |
| P2 Reliable text decomposition / proposed | 0% | P1 exit | T3-T4: Pass predeclared per-case semantic criteria, not only JSON validation; unsupported assertions and replaying stale prose cannot overwrite accepted corrections. |
| P3 Campaign proposals and context / proposed | 0% | P2 exit | T5-T6: Invented tools, conflicting constraints and invalid representations reject; irrelevant retrieved text cannot authorize tool calls; missing evidence yields truthful abstention or blocked proposals. |
| P4 Durable supervisor and races / proposed | 0% | P3 exit | T7-T8: At most one accepted decision per scope/revision; unrelated branch progress continues; stale/late proposals cannot reopen closed work; lost acknowledgements may repeat calls but account for budget. |
| P5 Live evaluation and closeout / proposed | 0% | P4 exit | T9-T10: Actual live-model evidence is required for completion; unavailable provider/egress choice blocks that gate, not earlier deterministic work. No routine human wait and no scientific-validity claim from model fluency. |

## Outcome and Boundaries

Let an LLM propose bounded campaigns and knowledge decompositions while runtime and domain owners retain acceptance authority.

Included: Context assembly, versioned prompts/models, typed proposals, extraction evaluation, durable engagements, relevance-aware staleness, bounded repairs/fallbacks and autonomous terminal outcomes.

Excluded: Model-created tools executing without review, widened permissions, arbitrary code execution, human approval waits during campaigns and unbounded recursive model loops.

Primary services retain private state, dependencies, migrations and module READMEs. Public contracts/clients are the only cross-owner dependencies. Any new schema identifies its consumer/migration impact. No broad backend or shared business/ORM package. Later phases refine earlier boundaries under the current task without reopening closed plans.

## Child Work-Package Register

This parent owns outcomes and sequencing. The named packages below are **scoped, not implementation-ready**. The existing task pairs are requirements for child decomposition, not sufficiently detailed coding instructions. Before activating a package, author its canonical child plan with owned objects/API/storage, transition/algorithm decisions, failure/recovery matrix, named fixtures and replacement gates. Parent progress then rolls up verified child deliverables; do not count these task pairs again. No implementation credit is earned here.

| Child / bounded ownership | Implementation | Prerequisite | Scope to decompose |
|---|---:|---|---|
| BP-07.01 / Model and engagement contracts | 0% | Parent predecessor gates | Define provider/attempt versus logical engagement identity, prompt/context provenance, decision scope, relevant input revisions, allowed actions and bounded budgets. Implement a provider port and deterministic adversarial fake; record the live model/provider/egress decision before any real call and preserve omitted context metadata. |
| BP-07.02 / Reliable text decomposition | 0% | BP-07.01 exit | Build versioned extraction prompts against BP-06 operations using reviewed source-text/expected-meaning fixtures, identity resolution and human-readable semantic diffs. Evaluate source grounding, ambiguity, negation, causality/correlation, merges, contradictions and biological/polymer context; invalid proposals remain uncommitted and repair is bounded. |
| BP-07.03 / Campaign proposals and context | 0% | BP-07.02 exit | Assemble rights-eligible context through public retrieval/graph APIs with exact versions and explicit missing inputs; present registered capability descriptions and applicability limits. Generate campaign/parameter/successor proposals and run deterministic compilation, scientific eligibility and budget/authority checks before acceptance. |
| BP-07.04 / Durable supervisor and races | 0% | BP-07.03 exit | Persist request/outbox before model calls; implement engagement lifecycle and scoped decision commit through the same runtime committer. Handle relevant versus unrelated frontier changes, concurrent independent scopes, overlapping decisions, deterministic fallback races, timeout/cancel and bounded repair exhaustion. |
| BP-07.05 / Live evaluation and closeout | 0% | BP-07.04 exit | Using an explicitly selected model and permitted data, run the bounded campaign/extraction evaluation pack and compare actual outcomes with deterministic fixtures. Expose engagement/context/rejection lineage in Studio, preserve next-campaign topology changes and terminal failure reasons, then audit and archive. |

Readiness gaps are the unresolved decisions below plus concrete storage/API contracts, algorithm choices, test oracles and migration/recovery obligations for each package. Decompose the nearest eligible package first; do not invent distant provider, ontology or deployment decisions merely to fill templates. Child scope remains here until a linked execution plan replaces the register entry. The parent's existing percentages remain 0% because no implementation has occurred.

## Ordered Tasks

### P1 ? Model and engagement contracts

**T1.** Define provider/attempt versus logical engagement identity, prompt/context provenance, decision scope, relevant input revisions, allowed actions and bounded budgets.

**T2.** Implement a provider port and deterministic adversarial fake; record the live model/provider/egress decision before any real call and preserve omitted context metadata.

**Exit:** Contract tests reject unsupported actions and authority escalation; secrets/data limits apply at the adapter; fake-model success is not live-model acceptance.

### P2 ? Reliable text decomposition

**T3.** Build versioned extraction prompts against BP-06 operations using reviewed source-text/expected-meaning fixtures, identity resolution and human-readable semantic diffs.

**T4.** Evaluate source grounding, ambiguity, negation, causality/correlation, merges, contradictions and biological/polymer context; invalid proposals remain uncommitted and repair is bounded.

**Exit:** Pass predeclared per-case semantic criteria, not only JSON validation; unsupported assertions and replaying stale prose cannot overwrite accepted corrections.

### P3 ? Campaign proposals and context

**T5.** Assemble rights-eligible context through public retrieval/graph APIs with exact versions and explicit missing inputs; present registered capability descriptions and applicability limits.

**T6.** Generate campaign/parameter/successor proposals and run deterministic compilation, scientific eligibility and budget/authority checks before acceptance.

**Exit:** Invented tools, conflicting constraints and invalid representations reject; irrelevant retrieved text cannot authorize tool calls; missing evidence yields truthful abstention or blocked proposals.

### P4 ? Durable supervisor and races

**T7.** Persist request/outbox before model calls; implement engagement lifecycle and scoped decision commit through the same runtime committer.

**T8.** Handle relevant versus unrelated frontier changes, concurrent independent scopes, overlapping decisions, deterministic fallback races, timeout/cancel and bounded repair exhaustion.

**Exit:** At most one accepted decision per scope/revision; unrelated branch progress continues; stale/late proposals cannot reopen closed work; lost acknowledgements may repeat calls but account for budget.

### P5 ? Live evaluation and closeout

**T9.** Using an explicitly selected model and permitted data, run the bounded campaign/extraction evaluation pack and compare actual outcomes with deterministic fixtures.

**T10.** Expose engagement/context/rejection lineage in Studio, preserve next-campaign topology changes and terminal failure reasons, then audit and archive.

**Exit:** Actual live-model evidence is required for completion; unavailable provider/egress choice blocks that gate, not earlier deterministic work. No routine human wait and no scientific-validity claim from model fluency.

## Test Ownership and Evidence

Proposed suite locations (create with their modules):

- `services/agent_planning/tests/context/`.
- `services/agent_planning/tests/proposals/`.
- `services/agent_planning/tests/extraction/`.
- `services/campaign_runtime/tests/supervision/`.
- `tests/integration/autonomous_supervision/`.

Each owning README maps public behavior, invariants, failure scenarios and measured source paths to module-local test suites. Register source/suite ownership in `dev/test_scopes.json`; extend granular selectors as modules arrive. Run changed-module tests first, affected consumers next, and separate public-boundary integration/E2E only for cross-owner outcomes. Record line and branch coverage with gaps; coverage percentages are not evidence of scientific correctness.

Keep scenario evidence with absolute timestamps, implementation revision, fixture/schema identity, relevant run/artifact IDs and observed outcomes. Unit mocks do not replace required database, process, browser or provider evidence. Record independent build/install and replacement tests for new service/tool boundaries.

## Decisions and Handoff

Provider/model and egress policy are user-dependent before live calls. Define evaluation cases and acceptance criteria before tuning prompts. BP-08 consumes bounded topology proposals; changing the model requires versioned reevaluation rather than silently reusing earlier evidence.

## Progress, Scope Changes and Closeout

The canonical tracker owns overall and P1-P5 percentages; mirror them in MBT at every completed task or changed scope and before commit/handoff. Do not activate downstream phases before their predecessor gate. Record review changes and denominator adjustments here; substantial newly discovered scope gets a named successor.

Final phase includes a component-scoped architecture drift audit. Fix blocking drift, explicitly assign nonblocking follow-ups, update module READMEs/inventories and archive only after all defined gates pass. Synchronize MBT, plan index and Restore and repair moved links. Preserve separate acceptance/operational/scientific readiness status; 100% measures this bounded implementation, not the whole product.

Closeout evidence: pending. No implementation, deployment or scientific validation is claimed by this draft.

## Reference refinement 2026-09-25 13:54:17

BP-07.02/.03 now preserve extraction/repair provenance, distinguish inferred from source-stated values, and bind proposed experiment steps to exact unmet question criteria. Model answers cannot self-certify scientific sufficiency or bypass between-campaign human changes. Existing implementation deliveries extended with required acceptance cases; all 0%, denominator unchanged. [Reference assessment](References/Amphora_Lab_Insights.md) owns provenance and limitations.

## 2026-10-04 01:53:10 - Activation and B1.01

BP-06 closed90cda1c; corrected-ready activation preserves Runtime/domain authority. New planning0.1/Agent Planning0.1 pure context and attempt boundary.42 source/42 independent;60 including dev;84 statements/8 branches100%;484 schemas preserve466 predecessor bytes.8-wheel isolated closure excludes private peers. Child6.25%,parent1.25%, Build8.33%,Acceptance0%; B1.02 provider port active.

## 2026-10-04 02:00:10 - B1.02 deterministic provider

Additive planning0.2/Agent Planning0.2, bounded64KiB/256-chunk capture and distinct policy/invalid/unavailable/unknown/abstain/proposed outcomes. Reference-only profile cannot invent or substitute selected Artifact identity; actual task payload generation remains later profiles.69 source/69 independent tests,87 with dev;233 statements/42 branches100%;488 schemas preserve484 old bytes. Child12.50%,parent2.50%,Build16.67%; B1.03 persistence active.

## 2026-10-04 02:08:10 - B1.03 private journal

Agent Planning0.3, planning_0001 applied idempotently with separate migrator/service roles. Immutable request, attempt intent and observation/capture records; no public dispatch/budget permission.104 tests25.45s,11 actual PostgreSQL plus6 record-boundary cases;398/399 statements63/64 branches, migration CLI uncovered. Initial FK declaration failed and rolled back; fixed before migration acceptance, no retained peer state reset. Child18.75%,parent3.75%,Build25%; B1.04 independent process/install remains.

## 2026-10-04 02:17:10 - B1 boundary complete

B1.04 reusable installed verifier:8-wheel closure,2 independent installs,86 owned tests5.87s and4 process stages. Original unknown usage/capture preserved across successor proposal and replay; CLI migration explicit. No bytecode copied or private peers installed.18 dev13.87s;488 schemas unchanged. Initial tooling pin for absent optional greenlet corrected, then source-only staging verified. B1=100%,child25%,parent5%,Build33.33%,gates1/4 and1/20. B2.01 durable reservations next; no budget/dispatch or live provider claim.

## 2026-10-04 02:25:10 - B2.01a policy and tracker reconciliation

Agent Planning0.4 private reviewed budget policy/demand:22 source,40 with dev,108 independent cases/four processes;65 statements/2 branches100%. No actual reservation or dispatch claim. Child29.17%,parent5.83%,Build38.89%,gates1/4 and1/20. MBT child/build rows had drifted through substring numeric replacement while canonical child/parent trackers stayed correct; rewrote full rows and asserted readback against canonical values. All future updates use exact rows/fields, never unbounded percentage replacement.

## 2026-10-04 02:37:29 ? B2.01b atomic reservations

Planning0.5/planning_0002 stores policy and conservative holds atomically with intents.47 source cases,116 installed cases,6 processes/2 installations and18 dev cases pass. New ledger75 statements/14 branches100%; combined persistence/budget287/288 statements,33/34 branches (migration CLI independently exercised). Scoped dev-config lint passes. Child33.33%,Build44.44%,parent6.67%; next B2.02. Evidence: [Reservations](../Audits/Evidence/BP-07-Planning/Reservations.json).

## 2026-10-04 02:43:09 ? B2.02 conservative settlements

Planning0.6/planning_0003 preserves policy-v1 bytes and immutable observations. Reserved-floor charges never refund unknown/low usage; exact overage blocks new admission. Prior settlement is required before retry.65 source cases3.89s,134 independent cases/eight processes/two installs,18 dev14.54s and scoped lint pass. Pure charge23 statements100%; settlement59 statements/8 branches100%; combined372/373 statements41/42 branches (migration CLI independently exercised). Child41.67%,Build55.56%,parent8.33%; next B2.03 dispatch/outcomes. [Evidence](../Audits/Evidence/BP-07-Planning/Settlements.json).

## 2026-10-04 02:54:55 ? B2.03 durable dispatch and bounded outcomes

Planning0.7/planning_0004 adds once-only issuance, database-clock deadlines, immutable recovery and separate late evidence. Per-component charge maxima prevent late undercount/double charge. PlanningRunner preserves context/permissions and enforces bounded retries with pending/outcome/budget stops.156 source10.85s,156 installed/11 processes/two installations,18 dev16.63s. Dispatch108 statements/14 branches100%; runner64/66 statements14/16 branches (exception propagation branches remain for B3); total800/803 statements115/118 branches. Installed replacement recovers pending issued first attempt, calls only second, then replays both without dispatch. B1/B2complete; child50%,Build66.67%,parent10%,closed2/4 and2/20. [Evidence](../Audits/Evidence/BP-07-Planning/Orchestration.json). Next B3.01.

## 2026-10-04 02:58:15 ? B3.01 adversarial runner oracles

13 additional actual-PostgreSQL full-runner cases;24 orchestration cases5.11s, runner propagation branches now exercised. Output bounds, schema/action/scope protection, immutable retries, partial usage overage and non-provider storage failures verified. Source/production unchanged; final independent test installation remains V1. Child58.33%,Build77.78%,parent11.67%; next B3.02.

## 2026-10-04 03:01:54 ? B3.02 barrier proof

15 actual PostgreSQL cases9.89s pass, including independent engagement progress while three contenders observe pending, and recovery-first/return-first/simultaneous expiry races. Immutable original outcome, separate late evidence and single charge preserved. Child66.67%,Build88.89%,parent13.33%; next B3.03 abrupt process exit.

## 2026-10-04 03:06:50 ? B3.03 abrupt process-exit proof

Five committed boundaries across15 installed processes passed: reservation, issuance, provider return, observation, settlement. Same-attempt exclusive synthetic call markers never duplicate; fresh replacement preserves pending uncertainty/charges/output hashes and final replay calls nothing. Actual PostgreSQL, no remote/power-loss claim. Child75%,Build100%,parent15%,closed3/4 and3/20; V1.01 active. [Evidence](../Audits/Evidence/BP-07-Planning/Crash_Recovery.json).

## 2026-10-04 03:14:24 ? V1 acceptance and BP-07.01 closeout

V1.01 verified173 source/installed cases,18 dev,11 replay processes and15 abrupt-exit processes on final installations; V1.02 scoped audit aligned after consolidating stale persistence README. Child100%,Build100%,Acceptance100%; parent20%,4/20. Archive child and rebase links; BP-07.02 activation audit next. [Audit](../Audits/BP-07.01_Model_Engagement_Closeout.md). MBT redundant queue had stale5.83%; corrected to20% and removed numeric duplication from navigation prose. Future tracker refresh must include all active phase/queue mirrors, not historical checkpoint rows.
