# Restore

## Current Checkpoint

- Last refreshed: `2026-09-28 20:11:30` (America/Chicago).
- Workspace: v2 active; v1 frozen; no external JARVIS access without task-specific request.
- Canonical position: BP-04 -> [BP-04.03](docs/Build%20Plans/BP-04/BP-04.03%20Aggregation%20and%20failure%20policy.md) / Build / B1 versioned aggregation/await boundaries and owner state. Next B2 transition policy.
- Progress: BP-02 closed 100% (32/32); BP-03 closed 100% (16/16); BP-04 active 40% (8/20), .01/.02 closed/audited 100%, .03 active 0% (Build 0%, Acceptance 0%). BP-05..09 queued 0%.
- Latest checkpoint: BP-04.03/B1 aggregate evidence/storage slice verified. Runtime 0.4.1/runtime_0008 adds ordered immutable member cuts, exact replay/stale rejection and deferred closure-audit atomicity; service-role UPDATE/DELETE denied. 33 owned cases, 96/96 statements and 10/10 branches; full gate 842 tests/thirteen installs/actual peer replacement/REC-01..09 passed, recovery scope 75030df6519947e880fecc762e554c2b. Logs .test-results/bp0403-b1-{aggregation,foundation}.log. No public schema change; coordinator integration remains B2. B1 external-wait contracts/state still pending, so child 0/4 and parent 8/20 unchanged.
- Predecessor checkpoint: BP-04.02 closed and archived. Runtime 0.4.0 has durable admission/advancement, finite predicates/branches/all-joins, frozen scatter, loop checkpoints, 256 active worker observations, configured graph HTTP and separate autonomous polling. Artifact reads stay outside SQL locks. No new migration after runtime_0007; worker schemas/tool bytes unchanged.
- Evidence: B2 full gate 799 tests/thirteen independent installs/REC-01..09, scope 4beb3aa18a6b41818bdd97a0620bc674. B3 60 scheduling tests/eight actual coordinator-process scenarios, including measured lock contention and kill after commit/before reply. V1 eight actual installed Registry/Runtime/Artifact/SDK/tool and fresh Runtime replacement cases, scope bab36cf644df43e59a370437d68c94d1. Actual outputs/goldens, Artifact predicate, tool iterations, scatter order, dropped success reply, retained history, installed polling and seven Artifact confirmations pass. See docs/Audits/Evidence/BP-04-Scheduling and BP-04.02_Scheduling_Closeout.md.
- V1 maintenance: repaired a reused test-only Windows marker sharing conflict with bounded replacement retry. Four integration-helper cases pass; no production worker change and BP-03 stays closed. Final log .test-results/bp0402-v1-graphs-final.log; failed initial evidence remains explicitly failed.
- B1 resume: .03 activation audit is corrected_ready. Existing executable wire-v2 has six closed variants and no external wait/issuer receipt. Preserve published v1/v2 schema bytes; introduce a separately versioned await-capable definition/plan/observation boundary, reusing unchanged value/path contracts where compatible. Immutable aggregate snapshot/storage now exists. Finish issuer/scope/purpose/revision/schema/deadline wait identity, transport and owner state before B2 transitions. Existing completion_intents require worker attempts; external waits need separate retention intents and exact outcome lookup, never fictional worker rows. Synthetic issuer is permitted; actual Research/Knowledge authority remains BP-06.06. Runtime keeps sole acceptance/budget/fence authority. No user blocker.
- Environment: Python 3.12, uv, labeled PostgreSQL 17.11 fixture; credentials only in ignored .test-results/postgres-fixture.json. Owner-specific roles/migrations; never reset or run global single-campaign tests concurrently. AMPHORA_TEST_POSTGRES=1 is explicit. Workers/compiler metadata probes receive no owner SQL credentials.
- Tools: numeric 0.2.0 and sequence 0.3.0; image manifest .test-results/tool-images/bp0304-20260928-1706/manifest.json, predecessor bp0303-20260928-1619/manifest.json. Reproduce installed graph gate: dev/verify_graphs.py --images <current-manifest>. Windows installed-process and Linux image goldens remain separate tiers.
- Git: 4bcf7f2 pushed; .03 B1 aggregation slice verified for commit. Identity tkn1234 <alb_gen@live.com>; origin https://github.com/neverhumanbot/mvp20-split.git. Continue autonomously and commit/push significant updates.
- Limits: pure/synthetic tool profile; richer partial/failure/external-wait policies remain .03; v1/successor parity .04; integrated graph recovery .05. LLM/knowledge/Studio/scientific/target-host acceptance remains later gates. No K3s/power-loss/scientific claim. Pre-existing v1/LICENSE manifest discrepancy and test-client deprecation remain unchanged.

## Decomposition and Resume Discipline

BP-02 now has six focused child plans and separate history. BP-03..09 now have 34 canonical child plans with owned objects/contracts, transition/algorithm decisions, named failure oracles, independent test tiers and replacement acceptance. BP-02 children have detailed API/transaction/crash matrices. Parent planning histories preserve prior task pairs; new queued-parent denominators are 16/20/16/24/20/20/20; current progress is above. The nearest child gets physical design, failure tests, module replacement boundaries and scoped audit. Parent rollups count child implementation once. The preliminary 34-task count was explicitly corrected to 32 by separating pure design gates S1/A1; prior design work remains complete.

Contract and persistence READMEs describe actual implemented boundaries. Earlier scripted artifact-client probes remain distinct from the actual installed REC-01..09 evidence now completed by .06. Do not confuse either tier with scientific or target-host correctness. Use [MBT](docs/Build%20Plans/Master%20Build%20Tracker.md) and child tracker, not old task IDs in history.

## Product and Architecture Direction

The engine stays general, with bio-available polymers a likely application. First many releases are internal/demo, one user and one active autonomous campaign with concurrent tool invocations. Target host is DGX Spark or a partner Threadripper; exact host/provider/data-egress selection remains a deployment decision.

Human changes apply between campaigns. Deterministic policies and eligible agents handle routine execution/review; unresolved prerequisites produce truthful terminal outcomes rather than indefinite human waits. Emergency termination/revocation remains available. Knowledge, scientific evidence and model promotion retain explicit authority and provenance.

Two authored graphs remain distinct: campaign execution and neuro-symbolic knowledge. Lineage is derived. Graph Runner is within Campaign Runtime and owns coordination, aggregation and supervision; durable model engagements return proposals, never execution authority. Primary services/tools have private code/state and public versioned contracts. Independently packaged tool replicas add capacity; the registry remains the node/tool index. K3s is proposed, not deployed.

Module rewrites are expected. The source-adjacent README and linked schemas/tests define the replacement boundary. Preserve state/evidence and version intentional contract changes. Do not edit v1 to obtain reusable components.

## Read and Resume

1. [AGENTS](AGENTS.md), [MBT](docs/Build%20Plans/Master%20Build%20Tracker.md), then the owning plan.
2. [Master Architecture](Architecture.md), following immediate children to the active boundary.
3. [Product Requirements](docs/Architecture/Requirements/Product_Requirements.md), [requirements guide](docs/Architecture/Requirements/README.md) and [architecture guide](docs/Architecture/README.md).
4. [Contract packages](contracts/README.md), [runtime foundation](services/campaign_runtime/README.md), [foundation tooling](dev/README.md).

The high-level specifications and earlier flat design/history files live in `docs/Architecture/Requirements/`; indexes, source map and reuse baseline stay at Architecture top level. PDF exports may be stale; Markdown is authoritative. JARVIS is external reference only and requires task-specific authorization to access.

## Implementation Limits

Private PostgreSQL schemas/migrations and canonical command registration/terminal receipt transactions exist. Default runtime construction remains validation-only; explicit fixture hosting enables durable lifecycle and read endpoints. General campaign validation reports `executable=false`. Artifact upload/finalization APIs now publish verified immutable references; protective reservation/confirm/reconcile handshake is implemented against a configured public runtime outcome client; bounded reconciliation/cleanup and standalone hosting are implemented. Optional synthetic fixture admission is implemented; configured claim/renewal handlers are implemented; atomic fixture completion acceptance and retention delivery are implemented; configured deterministic graph admission/advancement and process/peer replacement acceptance are complete in BP-04.02; scientific tools, knowledge reasoner, provider calls and Studio are not implemented. Paired integration establishes fixture retention; process-crash tests do not establish target-host power-loss durability or scientific validity. Those gates remain in their named children/successor plans.

Baseline verification: no changed manifest file content; verifier reports pre-existing added `v1/LICENSE` already present in commit `99d219c`. Do not regenerate the frozen manifest or alter v1 to suppress this discrepancy.
