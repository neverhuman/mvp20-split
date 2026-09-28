# Restore

## Current Checkpoint

- Last refreshed: `2026-09-28 10:56:19` (America/Chicago).
- Workspace: v2 active; v1 frozen. JARVIS is read-only reference only when specifically requested.
- Canonical position: [BP-02](docs/Build%20Plans/BP-02%20Durable%20Runtime%20and%20Artifact%20Foundation.md) -> [BP-02.03](docs/Build%20Plans/BP-02/BP-02.03%20Artifact%20Publication%20and%20Retention.md) / V2 / A6 independent service acceptance.
- Progress: parent 43.75% (14/32 implementation deliveries). Children .01 contracts and .02 persistence complete/audited; .03 artifacts 80% (V1 100%, V2 0%), A2-A5 complete. Children .04-.06 and BP-03..09 remain 0%.
- Latest work: A4 protective reservation handshake passed with real PostgreSQL and a separate authenticated scripted HTTP peer; terminal proof, shared-reference protection, replay and rollback verified. Reference refinements remain in queued plans.
- Authority: user approved deeper decomposition and autonomous continuation. No new permission needed for routine in-scope work; one child/task active. BP-01/BP-01A and closed children stay closed.
- Next bounded work: A6 adds executable hosting, scoped content reads, independent service acceptance and closeout audit. A5 cleanup/reconciliation and separate-process crash tests passed. Actual runtime integration remains .06.
- Evidence: 182 aggregate tests pass with PostgreSQL enabled; lint/import/schema checks and eight independent wheel installs pass, including migration SQL resources. 56 published input/output schemas. Runtime persistence 11 tests, artifact service 71. [Persistence audit](docs/Audits/BP-02.02_Persistence_Closeout.md) records exact scope and coverage limits.
- Environment: Python 3.12, uv bootstrap and Docker Desktop available. Labeled PostgreSQL 17.11 fixture is running; helper reset/restart verified. Dynamic endpoint and credentials are only in ignored `.test-results/postgres-fixture.json`; do not copy them to docs/logs. `dev/postgres_fixture.py verify` refreshes endpoint after restart. Use `AMPHORA_TEST_POSTGRES=1` for actual database tests. Cargo absent; Rust remains later scope.
- Blockers: Git identity configured locally as tkn1234 <alb_gen@live.com>; no A5 implementation blocker. Scientific sources/provider/target-host policy remain later decisions; synthetic fixtures are authorized. Existing Starlette/httpx test-client deprecation is nonblocking dev maintenance.
- Git: implementation checkpoint `82ef9cf` pushed to origin/main. Repository-local author is tkn1234 <alb_gen@live.com>. GitHub reported the repository moved; origin now uses https://github.com/neverhumanbot/mvp20-split.git. Resume A6; no Git identity blocker remains.

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

Private PostgreSQL schemas/migrations and canonical command registration/terminal receipt transactions exist. The public runtime API remains validation-only and reports `executable=false`. Artifact upload/finalization APIs now publish verified immutable references; protective reservation/confirm/reconcile handshake is implemented against a configured public runtime outcome client; reconciliation scheduling/cleanup, invocation handlers, full completion acceptance, interpreter, scientific tools, knowledge reasoner, provider calls and Studio are not implemented. Artifact process-crash tests do not establish integrated runtime retention, target-host power-loss durability or scientific validity. Those gates remain in their named children/successor plans.

Baseline verification: no changed manifest file content; verifier reports pre-existing added `v1/LICENSE` already present in commit `99d219c`. Do not regenerate the frozen manifest or alter v1 to suppress this discrepancy.
