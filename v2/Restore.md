# Restore

## Current Checkpoint

- Last refreshed: `2026-09-28 18:20:22` (America/Chicago).
- Workspace: v2 active; v1 frozen; no external JARVIS access without task-specific request.
- Canonical position: BP-04 -> [BP-04.02](docs/Build%20Plans/BP-04/BP-04.02%20Frontier%20and%20scheduling.md) / Build / B1 durable frontier/admission boundary and owner migration. Next B2 recovery and deterministic scheduling.
- Progress: BP-02 closed 100% (32/32); BP-03 closed 100% (16/16); BP-04 active 20% (4/20), .01 closed/audited 100%, .02 active 0% (Build/Acceptance 0%). BP-05..09 queued 0%.
- Latest checkpoint: BP-04.01 closed/audited. 111 compiler cases, 100% of 573 statements/144 branches; 23 contract/6 legacy graph/3 API cases pass. Actual installed compiler/public Registry/two-tool acceptance produced five immutable plans, scope 498bc3389bca4a96b0d7f7690bd39577; fresh compiler/Registry installs and drain preserve old receipts/plans. Evidence docs/Audits/Evidence/BP-04-Compiler; audit BP-04.01_Compiler_Closeout.md. No dispatch/capacity claim.
- Tools: numeric 0.2.0 image 4f5f4b74eec523c55668b0493123cfd3f9e5ba77fc49f51594a536452244dc83; sequence 0.3.0 image 4364cc50b6c6ad07ebec70a8969f65c35fdd7054752e861510fe02b5ec3ae305, corrected output representation with unchanged payload schemas/kernel. Sequence 0.2.0 remains retained for exact old pins. Windows installed peer proof and Linux non-root/network-disabled image goldens are distinct evidence tiers.
- B1 accepted: campaign contracts/Runtime 0.2.0, separate executable wire-v2 roots and eight schemas; legacy 102 schema bytes unchanged. 23 owned cases/100% of 275 declarative statements (not semantic coverage); full 619 tests/twelve builds/actual peer replacement and REC-01..09 passed, scope bf6104d4f24c4441bf2f69e327493080. No new DB migration or executable API.
- Current deliverable: BP-04.02/B1 focused Runtime coordinator boundary. Activation audit identifies fixture-only run closure, missing durable graph frontier and hash-order dispatch as integration points. Preserve fixture behavior with explicit execution mode; graph Finish/frontier owns graph termination. Reuse run-lock/admission guard, keep attempt-budget reservation at claim, persist unique graph activation identity and deterministic priority. Consider focused graph-runtime contract package to avoid changing pinned worker closure. Actual PostgreSQL/migration and later installed worker gates remain required.
- Environment: Python 3.12, uv, labeled PostgreSQL 17.11 fixture; credentials only in ignored .test-results/postgres-fixture.json. Owner-specific roles/migrations; never reset or run global single-campaign tests concurrently. AMPHORA_TEST_POSTGRES=1 is explicit. SDK/worker environments receive no owner SQL credentials.
- Reproduce final replica acceptance: dev/verify_tool_workers.py --replicas --replacement --images .test-results/tool-images/bp0304-20260928-1706/manifest.json --previous-images .test-results/tool-images/bp0303-20260928-1619/manifest.json. Prior manifest needs its hash-verified adjacent built-wheels directory. Setup uses owner-specific readiness/storage and Windows owned-process-tree cleanup.
- Git: 1c0d912 pushed; compiler V1 closeout/BP-04.02 activation verified for commit. Identity tkn1234 <alb_gen@live.com>; origin https://github.com/neverhumanbot/mvp20-split.git.
- Authority: continue autonomously and commit/push significant updates. No user blocker. Actual host/provider/scientific/egress choices remain later named gates.
- Limits: no general interpreter, scientific efficacy, LLM/knowledge/Studio or target-host/K3s/power-loss claim. Pure tools advertise no checkpoint support; unsupported version 2 is rejected before command registration. Fixture budget enforcement is verified, while autonomous terminalization belongs to the future graph supervisor. Existing test-client warning and pre-existing v1/LICENSE manifest discrepancy remain assigned maintenance.

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

Private PostgreSQL schemas/migrations and canonical command registration/terminal receipt transactions exist. Default runtime construction remains validation-only; explicit fixture hosting enables durable lifecycle and read endpoints. General campaign validation reports `executable=false`. Artifact upload/finalization APIs now publish verified immutable references; protective reservation/confirm/reconcile handshake is implemented against a configured public runtime outcome client; bounded reconciliation/cleanup and standalone hosting are implemented. Optional synthetic fixture admission is implemented; configured claim/renewal handlers are implemented; atomic fixture completion acceptance and retention delivery are implemented; interpreter, scientific tools, knowledge reasoner, provider calls and Studio are not implemented. Paired integration establishes fixture retention; process-crash tests do not establish target-host power-loss durability or scientific validity. Those gates remain in their named children/successor plans.

Baseline verification: no changed manifest file content; verifier reports pre-existing added `v1/LICENSE` already present in commit `99d219c`. Do not regenerate the frozen manifest or alter v1 to suppress this discrepancy.
