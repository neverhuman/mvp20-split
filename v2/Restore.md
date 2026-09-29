# Restore

## Current Checkpoint

- Last refreshed: `2026-09-28 19:21:42` (America/Chicago).
- Workspace: v2 active; v1 frozen; no external JARVIS access without task-specific request.
- Canonical position: BP-04 -> [BP-04.02](docs/Build%20Plans/BP-04/BP-04.02%20Frontier%20and%20scheduling.md) / Build / B3 actual competing-coordinator and restart proof. Next V1 actual installed graph/tool/Artifact integration and replacement.
- Progress: BP-02 closed 100% (32/32); BP-03 closed 100% (16/16); BP-04 active 30% (6/20), .01 closed/audited 100%, .02 active 50% (Build 66.67%, Acceptance 0%). BP-05..09 queued 0%.
- Latest checkpoint: B2 accepted. Runtime 0.4.0 durable advancement and configured graph HTTP/polling. Branch/all-join/scatter/loop controls consume committed outcomes; membership and iteration checkpoints survive fresh coordinators. Active queued/leased worker window is 256 despite larger retained history. Artifact predicates verify scoped immutable metadata/content outside owner transactions; missing values block, transport uncertainty leaves retryable commands. No new migration or worker/schema changes.
- Verification: 799 tests/thirteen independent installs/actual predecessor peer replacement and REC-01..09 passed; recovery scope 4beb3aa18a6b41818bdd97a0620bc674, Registry replacement f1f6b9e6aa8e4a478ac8217eca1886c5. 52 owned scheduling cases in full gate; preceding 51-case coverage run 886/942 coordinator statements and 174/208 branches. Logs .test-results/bp0402-b2-*.log. Graph completion tests use a scripted reservation peer; V1 must prove actual graph peers. Fresh objects are not process-crash proof.
- B3 deliverable: race real coordinator processes under the run lock; kill after frontier commit before notification/response and recover original receipt/work; assert exact identities/frontiers for empty scatter, loop limit, dependency/budget blockage and independent progress while another branch is leased. Keep module-owned tests and evidence tiers separate. No user blocker.
- Environment: Python 3.12, uv, labeled PostgreSQL 17.11 fixture; credentials only in ignored .test-results/postgres-fixture.json. Owner-specific roles/migrations, never reset or run global single-campaign suites concurrently. AMPHORA_TEST_POSTGRES=1 is explicit. Worker environments receive no owner SQL credentials.
- Tools remain numeric 0.2.0 and sequence 0.3.0. Current image manifest .test-results/tool-images/bp0304-20260928-1706/manifest.json; predecessor bp0303-20260928-1619/manifest.json. Windows installed-process and Linux image goldens remain separate evidence tiers. No target-host/K3s/power-loss claim.
- Git: 23a5194 pushed; B2 verified for commit. Identity tkn1234 <alb_gen@live.com>; origin https://github.com/neverhumanbot/mvp20-split.git. Continue autonomously and commit/push significant updates.
- Limits: compiler is pure/synthetic-only; richer partial/failure/external-wait policies belong to BP-04.03. LLM/knowledge/Studio/scientific/target-host acceptance remains later gates. Pre-existing v1/LICENSE manifest discrepancy and test-client deprecation remain unchanged.

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

Private PostgreSQL schemas/migrations and canonical command registration/terminal receipt transactions exist. Default runtime construction remains validation-only; explicit fixture hosting enables durable lifecycle and read endpoints. General campaign validation reports `executable=false`. Artifact upload/finalization APIs now publish verified immutable references; protective reservation/confirm/reconcile handshake is implemented against a configured public runtime outcome client; bounded reconciliation/cleanup and standalone hosting are implemented. Optional synthetic fixture admission is implemented; configured claim/renewal handlers are implemented; atomic fixture completion acceptance and retention delivery are implemented; configured deterministic graph admission/advancement is implemented with process/peer acceptance still in BP-04.02; scientific tools, knowledge reasoner, provider calls and Studio are not implemented. Paired integration establishes fixture retention; process-crash tests do not establish target-host power-loss durability or scientific validity. Those gates remain in their named children/successor plans.

Baseline verification: no changed manifest file content; verifier reports pre-existing added `v1/LICENSE` already present in commit `99d219c`. Do not regenerate the frozen manifest or alter v1 to suppress this discrepancy.
