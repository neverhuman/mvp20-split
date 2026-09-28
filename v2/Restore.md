# Restore

## Current Checkpoint

- Last refreshed: `2026-09-28 16:11:58` (America/Chicago).
- Workspace: v2 active; v1 frozen. External references require task-specific authorization.
- Canonical position: BP-03 -> [BP-03.03](docs/Build%20Plans/BP-03/BP-03.03%20Worker%20protocol%20and%20independent%20tools.md) / Build / B3 actual independent process/image recovery; next V1 replacement/audit.
- Progress: BP-02 closed 100% (32/32). BP-03 62.50% (10/16), .01/.02 closed/audited 100%, .03 50% (Build 66.67%, Acceptance 0%); BP-04..09 0%.
- Latest work: .03 B2 accepted: exact-pinned clients, receipt-first/pending recovery, monotonic lease/skew policy, terminal versus retryable failures and safe tool/CLI errors. B1 SDK/tool delivery pushed as ade9df2; artifacts prerequisites 254d419.
- Evidence: B2 117 focused cases: SDK 82/100% of 389 statements/102 branches; numeric 16/82% of 86/12; sequence 19/84% of 98/16, separate CLI evidence. Twelve fresh independent package builds/installs plus tool goldens and registry pure replacement passed; lint/import/schema guards passed. No owner persistence changed; B1 529-test/actual REC-01..09 proof (scope 6b88a870ac7844e3b71e5d9c3b0b4e37) retained. Actual SDK/tool-to-owner execution and image/replacement proof remain B3/V1.
- Authority: autonomous continuation and significant commit/push checkpoints authorized. No current user blocker; later scientific/provider/host gates remain explicit.
- Environment: Python 3.12, uv, labeled PostgreSQL 17.11 fixture. Dynamic credentials only in ignored .test-results/postgres-fixture.json. Registry has separate migration/service roles; registry_owner only extends labeled fixture. Set AMPHORA_TEST_POSTGRES=1; never publish credentials or reset concurrently with tests.
- Git: ade9df2 pushed; .03 B2 delivery verified for commit/push. Identity tkn1234 <alb_gen@live.com>; origin https://github.com/neverhumanbot/mvp20-split.git.
- B3 handoff: build independent tool images from locked offline wheel closures and digest-pinned Python base; record actual image identity separately from wheel/source hashes. Tool templates target Linux x86_64; local wheel probes are Windows compatibility evidence and use explicitly fake image pins. Build an owner-local SDK acceptance harness using actual independently installed runtime/artifact/tool processes, least-privilege worker tokens, typed schema files and public APIs only. Inject response loss, interrupted stream and expired/lost authority; prove exact pins, safe failures and no work-admission/private SQL. ToolAttemptContext uses bounded stage renewal and configured clock-skew allowance; long scientific kernels/remote topology need a reviewed profile. V1 adds fresh replacement and scoped audit.
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
