# Restore

## Current Checkpoint

- Last refreshed: `2026-09-28 11:51:08` (America/Chicago).
- Workspace: v2 active; v1 frozen. External references require task-specific authorization.
- Canonical position: BP-02 -> [BP-02.04](docs/Build%20Plans/BP-02/BP-02.04%20Invocation%20Lifecycle.md) / V2 / I6 authority/cancellation; next I6 lifecycle acceptance.
- Progress: parent 62.50% (20/32 deliveries). Children .01-.03 complete/audited; .04 at 83.33% (V1 100%, V2 0%); .05-.06 and BP-03..09 at 0%.
- Latest work: I5 cancellation/revocation passed atomic abort/settlement, rollback, scope denial, claim/renew races and uncertainty preservation; 51 lifecycle tests pass. Artifact standalone executable, scoped verified reads and bounded maintenance accepted; [artifact closeout](docs/Audits/BP-02.03_Artifact_Service_Closeout.md) names boundaries and remaining integration/host evidence.
- Evidence: 239 aggregate tests with PostgreSQL, lint/import/schema gates, eight independent wheels and installed artifact HTTP probe passed. 56 published schemas. Artifact suite 77 cases; process-kill evidence includes upload/finalization/cleanup/reservation transitions.
- Authority: autonomous continuation and significant commit/push checkpoints authorized. No current user blocker. Scientific sources/provider/target-host choices remain later decisions.
- Environment: Python 3.12, uv and labeled PostgreSQL 17.11 fixture. Dynamic endpoint/credentials only in ignored .test-results/postgres-fixture.json. Use helper verify and AMPHORA_TEST_POSTGRES=1; never publish credentials.
- Git: I4 checkpoint 6a4792f pushed; I5 authority checkpoint verified for commit/push. Repository-local identity tkn1234 <alb_gen@live.com>, origin https://github.com/neverhumanbot/mvp20-split.git.
- Limits: actual runtime terminal-outcome integration remains .05/.06; Linux/target-storage durability and backup remain BP-09. Synthetic artifact profiles do not establish scientific validity. Existing test-client warning is nonblocking.

## Decomposition and Resume Discipline

BP-02 now has six focused child plans and separate history. BP-03..09 now have 34 canonical child plans with owned objects/contracts, transition/algorithm decisions, named failure oracles, independent test tiers and replacement acceptance. Four open BP-02 children have detailed API/transaction/crash matrices. Parent planning histories preserve prior task pairs; new queued-parent denominators are 16/20/16/24/20/20/20, all at 0%. The nearest child gets physical design, failure tests, module replacement boundaries and scoped audit. Parent rollups count child implementation once. The preliminary 34-task count was explicitly corrected to 32 by separating pure design gates S1/A1; prior design work remains complete.

Contract and persistence READMEs describe actual implemented boundaries. A4/A5 may use a scripted runtime outcome process to test the artifact client; .06 must repeat acceptance/release races against the actual .05 runtime. Do not treat fixture proof as integrated correctness. Use [MBT](docs/Build%20Plans/Master%20Build%20Tracker.md) and child tracker, not old task IDs in history.

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

Private PostgreSQL schemas/migrations and canonical command registration/terminal receipt transactions exist. The public runtime API remains validation-only and reports `executable=false`. Artifact upload/finalization APIs now publish verified immutable references; protective reservation/confirm/reconcile handshake is implemented against a configured public runtime outcome client; bounded reconciliation/cleanup and standalone hosting are implemented. Optional synthetic fixture admission is implemented; configured claim/renewal handlers are implemented; full completion acceptance, interpreter, scientific tools, knowledge reasoner, provider calls and Studio are not implemented. Artifact process-crash tests do not establish integrated runtime retention, target-host power-loss durability or scientific validity. Those gates remain in their named children/successor plans.

Baseline verification: no changed manifest file content; verifier reports pre-existing added `v1/LICENSE` already present in commit `99d219c`. Do not regenerate the frozen manifest or alter v1 to suppress this discrepancy.
