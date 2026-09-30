# Planning Readiness and Cross-Plan Handoffs

- Last reviewed: `2026-09-28 13:45:17` (America/Chicago).
- Design status: roadmap decomposed through immediate execution children; implementation evidence remains in canonical trackers.
- Authority: [Master Build Tracker](Master%20Build%20Tracker.md) selects implementation priority. This reference owns planning gaps and cross-plan dependencies, not duplicate implementation percentages.

## Maturity Boundary

All open plans now name accountable modules, owned objects/contracts, state/algorithm decisions, failure oracles, test tiers, replacement conditions and downstream handoffs. This is the maximum useful static detail before predecessor implementations, model results and target-host measurements exist. Exact generated DTO fields, dependency versions, SQL migrations and benchmark thresholds are reconciled at the named activation gate, not fabricated in advance.

| Parent | Child depth | Current design posture | Evidence still required |
|---|---|---|---|
| BP-02 | 6 closed/audited children | Durable synthetic invocation foundation complete | [Actual acceptance and successor boundaries](../Audits/BP-02_Foundation_Closeout.md) |
| BP-03 | 4 canonical children | Exact identity, independent tools, registry and replacement specified | Registry store, SDK/tools, real replicas and independent builds |
| BP-04 | 5 canonical children | Compiler, frontier, joins/waits and v1 trace oracles specified | Real scheduling, recovery and public inspection APIs |
| BP-05 | 4 canonical children | Task/data ownership, progressive graph access and command UX specified | Frontend spike selection, actual browser and backend workflows |
| BP-06 | 6 canonical children | Source/evidence ownership, replay/CAS, rules, lab and vector profiles specified | Actual owner stores, correction races, retrieval and evidence traversal |
| BP-07 | 5 canonical children | Provider/proposal boundaries, extraction oracles and supervisor races specified | Deterministic implementation followed by selected live model evaluation |
| BP-08 | 5 canonical children | Kernel provenance, explicit generations, representation isolation and benchmarks specified | Kernel choice/proof, seeded recovery and topology evaluation |
| BP-09 | 5 canonical children | Preflight/install/demo/restore/replacement acceptance specified | Owner-selected host/profile, actual installation and measured recovery |

The 34 BP-03..09 child files replace their prior registers and two-task phase estimates. Each has three implementation deliveries plus an acceptance delivery, all initially 0%. These are delivery fractions, not effort estimates. Original scope remains in each parent's Planning History. BP-02 is now closed; historical percentages remain in its archived tracker/history.

## Producer / Consumer Contracts

| Producer -> consumer | Required handoff | Evidence gate / dependency resolution |
|---|---|---|
| BP-02.03 artifacts -> .04/.05 runtime | Scoped provisional/finalized refs and protected reservation identity | .03 tests scripted outcome peer; .06 repeats with actual .05 runtime intent proof |
| BP-02.05 runtime -> .03 retention | Immutable exact committed/aborted intent outcome; unknown distinct | No release from timeout/not-found; .06 verifies abort/commit/late-reserve races |
| BP-02.06 -> BP-03 | Claim/fence/renew/complete, artifact access and receipt lookup | Real process recovery and independent package gates before registry/worker acceptance |
| BP-03 -> BP-04 | Exact LockEntry, eligible releases, independently callable synthetic tools | Healthy capacity never implies scientific eligibility; runtime remains final authority |
| BP-04.05 -> BP-05 | Revision-pinned reads, bounded subgraphs, receipt lookup and event cursors | Read/command schemas and pagination/reconnect semantics before Studio transport |
| BP-04.03 -> BP-06.03/.06 | Typed purpose/issuer-scoped evidence wait | BP-04 uses synthetic issuer; BP-06 actual Knowledge/Research processes prove unblock/correction |
| BP-06.02 -> BP-07.02 | Typed proposals, accepted operation log, base-head conflict and semantic diff | BP-06 reviewed proposals do not claim LLM extraction; BP-07 held-out semantic tests do |
| BP-06.05 -> BP-07.03 | Rights-aware retrieval with pinned encoding profile and explicit omissions | Fixture vectors prove compatibility, not real semantic retrieval quality |
| BP-06 -> BP-08 | Exact evaluation/eligibility receipts, units and synthesis applicability | Unknown evidence is explicit; correction creates new comparison/selection revision |
| BP-07.04 -> BP-08.04 | Bounded topology proposal and accepted decision lineage | Compiler validates; adoption between campaigns; no live topology rewrite |
| BP-07.05 / BP-08.05 -> BP-09.03 | Actual model evaluation / search evidence for selected demo claims | Deterministic demos can prepare earlier; claimed autonomous/search demo cannot bypass these gates |
| BP-09.01 -> .02/.04 | Actual host/exposure/storage/profile and recovery objectives | No provisioning or recovery guarantee inferred from developer fixtures |

Default execution is sequential, with one active implementation child. This review is a user-authorized planning exception across the roadmap; it does not start parallel implementation. Numeric BP-08 preparation can be scoped independently of live topology evaluation, but its parent cannot close without its stated BP-07-dependent gate. Every child activation reconciles exact produced contracts instead of coding against an imagined peer.

## Decisions Resolved for Planning

- Initial tool fixtures: numeric affine transform and sequence symbol statistics; narrow, independently testable, explicitly non-scientific.
- Compiler baseline: explicit iteration scopes, finite typed predicates, frozen scatter membership and deterministic ordering. Default all-join waits for required terminal members; partial policy is explicit, records missing reasons and does not choose an accidental first-arrival subset.
- Data authority: separate source bytes, accepted knowledge changes, purpose-bound Research receipts, execution acceptance and derived indexes. Each keeps its own writer and history.
- Upload safety: distinct immutable attempt files with durable generation checks; filesystem locks alone cannot fence stale writers.
- LLM acceptance: typed outputs and deterministic authority checks precede domain acceptance; actual semantic held-out evaluation is required in addition to schema success.
- Evolution: explicit generation steps and complete RNG/checkpoint inputs; synthetic representation adapters are distinct and do not establish universal molecule generation.
- First restore profile: quiesced backup with metadata/artifact manifest and isolated restore verification; online backup and power-loss promises require separate evidence.

## Engineering Gates with No Owner Question Needed Now

| Gate | Responsible plan | Completion evidence |
|---|---|---|
| Exact new DTOs/migrations and HTTP schema compatibility | Active producing child | Published versioned schemas, migration/consumer negatives and independent install |
| Frontend/canvas implementation choice | BP-05.01 | Selected React19.3/ReactFlow12.12 after measured B2 comparison; .01 actual-owner browser/replacement accepted |
| Numeric kernel reuse choice | BP-08.01 | Source/license/dependency review and independent numerical oracles |
| Qdrant adapter and profile configuration | BP-06.05, later selected deployment | Current backend contract review, fixture parity and actual integration; no automatic JARVIS access |
| Scientific evaluator/encoding quality thresholds | Relevant future real-capability gate | Predeclared corpus/metrics and domain evidence; never infer from synthetic tests |

## Owner Decisions Needed Only at Dependent Gates

| Decision | First dependent gate | Safe preparation before answer |
|---|---|---|
| Model/provider, allowed data/egress and spend limits | BP-07.05 live calls (and provider configuration before any earlier optional real call) | Fake provider, contracts, prompts, held-out synthetic corpus and race harness |
| Actual host/access, exposure and optional cluster profile | BP-09.01 provisioning | Manifest schema, local composition, preflight/runbook and compatibility checklist |
| Recovery objectives and selected demo claims/resource budget | Before BP-09.03/.04 acceptance runs | Draft scenario/backup manifest and isolated failure tests |
| Licensed scientific sources, assay context and validated domain methods | First real source/tool adoption | Synthetic contracts, provenance, applicability and unknown-result behavior |

No owner question is required to complete this planning pass. Unknown selections are retained as explicit gates, not guessed commitments. Production/multi-user and new scientific claims require named successor scope.

## Final Coherence Review

Check child scope coverage against preserved parent task pairs; verify dependency order and fixture-to-real handoffs; resolve conflicting architecture rules; validate local links and tracker denominators. Record planning audit separately from implementation acceptance. No tests or deploys are claimed merely because their scenarios are specified.

## Amphora Lab Reference Incorporation

[Source assessment and ownership map](References/Amphora_Lab_Insights.md) records ten refined children across BP-05/06/07/08. Ingestion and Research question contracts originate in BP-06.01; graph replay/receipts and sample/material-state semantics mature in .02-.04; .06 repeats named-view/trace/question scenarios against actual owners. BP-07 consumes those references; BP-08 consumes material-state/equivalence constraints. Earlier Studio tests use labeled fixtures and do not require future services to exist. Existing dependencies and implementation percentages are unchanged.
