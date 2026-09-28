# Architecture Readiness Review

- Status: review complete; first-release scope and operating assumptions need owner answers
- Reviewed: `2026-09-22 20:57:10` (America/Chicago)
- Scope: master, six System contracts, twenty focused domain contracts, requirements/acceptance cross-checks, reuse baseline and current continuity records
- Evidence posture: document and paper-path review; no runtime, scientific or capacity validation
- Next step: resolve owner questions, align affected architecture, then author/audit a bounded implementation plan

## Owner Decisions After Review

Recorded `2026-09-22 21:03:27`: engine remains general, likely bio-available polymers; first many releases internal/demo; one user and one active campaign; single server on DGX Spark or partner Threadripper; fully autonomous campaigns with human changes between campaigns; scientific sources TBA; capacity/service-level work deferred. Modules are expected to be replaced from scratch behind documented boundaries.

These answers supersede the recommended human-review cadence and first-domain preferences below, which retain review provenance only. Product Requirements and the affected System/domain docs now describe the initial profile. AR-01 is resolved by making epoxy an optional regression fixture and defining a synthetic initial proof. AR-04's deployment/storage drift is aligned; detailed web-stack recording remains future work. AR-05/06 now have audience/scale constraints; exact host configuration/model-egress policy remains to be selected before real deployment/provider use. AR-02/03/07/08/09 remain bounded engineering design work, not unanswered product questionnaires. Sources TBA is not a blocker to synthetic foundation design. Replacement requirements are captured in Development Process and the module README template.

## Assessment

Enough architecture exists to begin a bounded foundation and vertical slice. It does not yet establish an implementation-ready scope for the whole product. The initial deployment, execution authority, compiler/interpreter boundary, immutable graph revisions, attempt fencing, transactional acceptance, artifact publication, domain/LLM authority and contract infrastructure form a coherent construction spine.

The first release needs a named acceptance scenario and support profile. Remaining design detail should be resolved in focused contracts before the phase that depends on it, rather than adding another broad architecture layer. This review does not activate implementation or reopen completed documentation plans.

## Findings and Disposition

| ID | Finding and evidence | Consequence / owner / next gate |
|---|---|---|
| AR-01 | [Product requirements](../Architecture/Requirements/Product_Requirements.md#graph-engine-delivery-and-acceptance-gates) requires an existing epoxy graph fixture; [System proof](../Architecture/System/Research_Loop.md#first-system-proof) uses synthetic tools plus a narrow calculator. Biology has separate required fixtures. | These can be sequential proofs but are not equivalent acceptance. Owner selects first useful scientific campaign and first-release boundary; delivery plan must retain later required gates explicitly. |
| AR-02 | [Reasoning](../Architecture/Knowledge/Reasoning.md) leaves logic formalism, contradiction policy and evidence-strength method open. | Cannot claim neuro-symbolic execution from storing/retrieving edges. Knowledge owner must specify a small executable rule set, unknown/contradictory outcomes, applicability and derivation fixtures before reasoning implementation. Recommend bounded typed rules with satisfied/violated/unknown outcomes and separate contradiction evidence; no unrestricted inference or improvised confidence arithmetic. |
| AR-03 | [Graph execution](../Architecture/System/Graph_Execution_Model.md) names instructions but does not supply complete transition tables, predicate grammar or cancellation/join/partial-batch truth tables. | Runtime owner must close these with contract fixtures before interpreter implementation. Include loop scopes, empty scatter, skipped predecessors, timeout/cancel versus completion, retries, pauses and successor-run carryover. Engineering-owned detail, not a request for the user to design the state machine. |
| AR-04 | [Platform operations](../Architecture/Platform/Operations.md) still lists deployment/storage as open; [Campaign runtime](../Architecture/Campaigns/Runtime.md) still lists transaction technology as open. System already sets single-server deployment and PostgreSQL baseline. Web/API recommendations remain conversational rather than a recorded complete stack decision. | Bounded documentation drift. System is construction owner; align the older open-decision lists and record accepted stack decisions before activating an implementation plan. No need to reopen closed plans. |
| AR-05 | [Security](../Architecture/Platform/Security.md) defines broad controls but first audience, identity provider, egress and deployment trust profile are unsettled. Separate worker processes do not establish a sandbox for arbitrary submitted code. | Owner identifies initial users, data sensitivity and permitted model hosting. Platform owner designs credentials, worker grants, isolation, resource/egress limits and installation accordingly. Keep tenant/project identity from the start even for an internal pilot. |
| AR-06 | [Quantitative requirements](../Architecture/Requirements/Product_Requirements.md#quantitative-non-functional-requirements) lists metrics without a first-profile envelope or recovery targets. | Owner supplies representative scale/hardware and acceptable loss/outage for real use; engineering proposes testable capacity/latency targets. A single server is a topology choice, not a load or durability guarantee. |
| AR-07 | [Reuse baseline](../Architecture/Evolutionary_Code_Reuse_Baseline.md#search-kernel-integration-gaps) identifies synchronous NSGA-II evaluation and missing durable per-generation history/checkpoint integration. | Search owner must select a bounded step/checkpoint adapter and retain evaluation/selection history before asynchronous graph integration. An FFI wrapper alone does not solve this. Baseline source review is not a current toolchain/runtime verification. |
| AR-08 | [Studio](../Architecture/Experience/Studio.md) defines interaction principles but first-user task and representative graph workload remain open. | Include a thin real UI in the first useful slice: inspect a run, see a reason/evidence link, pause, edit a descendant and compare revisions. Avoid deferring the engine's key inspectability claim until after backend completion. |
| AR-09 | [Contract architecture](../Architecture/System/Contract_Architecture.md) establishes ownership and publication but concrete schemas, compatibility fixtures and canonical serialization remain pending. | Contract owner supplies the smallest cross-boundary set for the selected slice. Decide units, reference identity, numerical fidelity and hashes before durable records depend on them. Do not design every future tool schema up front. |

## Owner Questions and Recommended Starting Positions

1. **First useful campaign:** which domain/problem and outcome should the first working release demonstrate? Recommend a small existing materials workflow to prove reuse, plus a distinct biology/assay fixture to expose domain coupling. These are software proofs; choosing a drug-product target adds its own data/evaluator acceptance.
2. **Initial audience:** internal researchers/operators or external customer access? Recommend an internal authenticated pilot with project isolation and audit, while preserving tenant-aware contracts. External access changes the initial identity/support gate.
3. **Deployment and models:** which server OS/hardware will host the pilot, and may authorized project data reach cloud LLMs or must inference stay local? Hardware and egress are product/environment constraints, not inferable from the Windows development workspace or JARVIS configuration.
4. **Autonomy:** after approving a graph and its budget, may it execute bounded iterations without per-step review? Recommend yes for approved computation; exact-revision review for topology changes, knowledge promotion and real lab/spend effects unless a specific standing approval covers them.
5. **Initial inputs and lab boundary:** which existing documents/data define the first knowledge area, who can judge extraction/scientific correctness, and should the pilot import lab files manually or connect to a named provider? Recommend versioned documents and structured result uploads first; preserve simulated external reconciliation tests.
6. **Operating envelope:** roughly how many users/concurrent campaigns, how large are the datasets/graphs, and what loss/outage is acceptable once storing real research? Estimates suffice to propose acceptance budgets; they are not contractual performance promises.

## Engineering Decisions That Do Not Need Owner Micromanagement

Within the accepted Python/Pydantic and PostgreSQL direction, engineering can propose and document API/client packaging, migrations, schema export, bounded predicate grammar, the Rust adapter transport, queue claims/fences, graph renderer selection and observability. Evaluate these against the chosen slice and deployment. Qdrant remains a future derived-index candidate; it is not needed to settle runtime authority or canonical knowledge meaning.

## Recommended First Delivery Boundary

An authenticated user submits a bounded objective; reviewed knowledge is available as a pinned revision; a typed campaign runs registered tools with a branch and bounded loop; a result feeds the next iteration; the UI exposes state and evidence; restart recovers; a reviewed graph change creates a successor run. Start with deterministic fixtures, then introduce scoped LLM proposals through the same validation boundary. Explicitly test cross-domain rejection, duplicate/stale completion and an uncertain external outcome.

This is a sequencing recommendation, not approval to defer the broader product requirements. The release matrix must distinguish foundation proof, internal useful pilot, scientific domain acceptance and enterprise acceptance.

## Verification and Limits

Local link targets in the master and decomposed architecture resolve. Requirements Coverage's source SHA-256 matches Product Requirements. Reviewed paper paths cover graph activation/execution, lab correction/reconciliation, knowledge publication/adoption, tool and LLM boundaries, and UI revision handling. No whole-product completeness certification, runtime tests, scientific benchmark or JARVIS implementation inspection is claimed. The local documents provided enough structural context for this review.
