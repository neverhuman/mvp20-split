# Restore

## Current Checkpoint

- Last refreshed: `2026-09-28 14:25:40` (America/Chicago).
- Workspace: v2 active; v1 frozen. External references require task-specific authorization.
- Canonical position: BP-03 -> [BP-03.02](docs/Build%20Plans/BP-03/BP-03.02%20Registry%20and%20version%20routing.md) / Build / B1 registry boundary; next B2 routing/lifecycle policy.
- Progress: BP-02 closed 100% (32/32). BP-03 25% (4/16), .01 closed/audited 100%, .02 0% (Build 0%, Acceptance 0%); BP-04..09 0%.
- Latest work: immutable descriptors, separate suitability/permission/capacity policy, independent failure corpus and fresh registry installation/actual peer compatibility accepted; [child audit](docs/Audits/BP-03.01_Descriptor_Closeout.md).
- Evidence: 393 component tests; 72 registry cases with 100% current source line/branch coverage (325 statements/102 branches). Nine independent builds, fresh registry/runtime/artifact replacement, paired acceptance and REC-01..09 passed. Eighty schema artifacts preserve earlier contracts. Latest recovery scope bdb0d03685714a2e90f278aaeaf5917b is ignored; BP-02 closeout evidence remains preserved in docs/Audits/Evidence/BP-02-Recovery.
- Authority: autonomous continuation and significant commit/push checkpoints authorized. No current user blocker; later scientific/provider/host gates remain explicit.
- Environment: Python 3.12, uv, labeled PostgreSQL 17.11 fixture. Dynamic credentials only in ignored .test-results/postgres-fixture.json. Set AMPHORA_TEST_POSTGRES=1; never publish credentials or reset concurrently with tests.
- Git: 1612ca3 pushed; .01 closeout verified for commit/push. Identity tkn1234 <alb_gen@live.com>; origin https://github.com/neverhumanbot/mvp20-split.git.
- B1 handoff: .02 activation audit recorded. Implement additive authenticated command envelopes using public canonical identity, registry-private PostgreSQL schema/roles and scoped register/read/resolve/drain/revoke boundaries. Separate immutable releases from revisioned deployments/replicas; preserve exact pins and server-owned policy. No registry persistence/HTTP exists yet. B3 owns actual concurrency/role-denial oracles; V1 retained history and independent replacement. Real tools remain .03; synthetic metadata proves no science.
- Limits: general interpreter, actual scientific tools/evidence, model/knowledge/Studio and host backup/power-loss remain later plans. Existing test-client warning and pre-existing v1/LICENSE manifest discrepancy remain nonblocking assigned maintenance. Recovery operating boundary: services/campaign_runtime/RECOVERY.md.

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
