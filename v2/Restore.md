# Restore

## Current Checkpoint

- Last refreshed: `2026-09-28 17:04:34` (America/Chicago).
- Workspace: v2 active; v1 frozen; no external JARVIS access without task-specific request.
- Canonical position: BP-03 -> [BP-03.04](docs/Build%20Plans/BP-03/BP-03.04%20Replicas%20and%20replacement%20proof.md) / Build / B2 actual death/reclaim and immutable release cutover. Next B3 result/budget/replacement negatives.
- Progress: BP-02 closed 100% (32/32); BP-03 81.25% (13/16), .01-.03 closed/audited 100%, .04 25% (Build 33.33%, Acceptance 0%). BP-04..09 queued 0%.
- Latest checkpoint: .03 eleven actual independent worker/owner cases passed, including fresh numeric/sequence installations preserving prior receipts, completions and result bytes (scope 34f1a759a9bc4af18b0f3e99b21d4a37). Both Linux/amd64 images passed non-root/network-disabled goldens and isolation; internal wheel bytes match Windows process probes. Evidence: docs/Audits/Evidence/BP-03-Workers; audit BP-03.03_Worker_Closeout.md.
- Verification: initial aggregate passed 597 tests/twelve builds/REC-01..09 before a harness stderr deadlock; file-backed server logs repaired it, scoped nine/eleven-case reruns passed. No production change. SDK 82 cases/100% scoped coverage; numeric 16/82%, sequence 19/84%. Process/CLI/image proof separate. Lint/import/schema guards passed.
- Previous deliverable: .04 integration harness under tests/integration/tool_replicas; actual registry registration/discovery/resolve and two real workers through public Runtime/Artifact APIs. Registry never grants execution authority. Record barriers and exact IDs. General interpreter remains BP-04.
- B1 accepted: scope f303014dbbc44baa870a8bf5c01095a7; actual registry selection/admission, two simultaneous distinct invocations, publication before completion, lost-response original-receipt recovery and exact budget settlement. Evidence docs/Audits/Evidence/BP-03-Replicas. Setup now uses per-owner readiness, precreated artifact storage and owned Windows process-tree cleanup.
- Current deliverable: B2 kill worker after claim; real lease expiry, second-worker reclaim, stale completion rejection. Build a new immutable sequence release, drain/cutover between campaigns, retain old replay identity. Extend the existing integration-owned harness, not a production scheduler.
- Assigned refinement TOOL-META-01: .04/B2 new sequence release corrects output representation (statistics rather than sequence) while preserving 0.2.0 image/descriptor/history. No checkpoint support is advertised by current pure tools; reject checkpoint/version mismatches rather than inventing recovery.
- Environment: Python 3.12, uv, labeled PostgreSQL 17.11 fixture; secrets only in ignored .test-results/postgres-fixture.json. Owner-specific roles/migrations; never reset concurrently with tests. AMPHORA_TEST_POSTGRES=1 explicit. Focused `dev/verify_tool_workers.py --images .test-results/tool-images/bp0303-20260928-1619/manifest.json --replacement` rebuilds fresh public closures without unrelated owner-suite reruns.
- Git: c4b4a75 pushed; .04 B1 verified for next commit. Identity tkn1234 <alb_gen@live.com>; origin https://github.com/neverhumanbot/mvp20-split.git.
- Authority: continue autonomously, commit/push significant updates. No user blocker. Actual host/provider/scientific/egress choices remain later named gates.
- Limits: no general interpreter, scientific efficacy, model/knowledge/Studio or target-host/K3s/power-loss claim. Existing test-client warning and pre-existing v1/LICENSE manifest discrepancy remain nonblocking assigned maintenance.

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
