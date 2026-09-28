# Restore

## Current Checkpoint

- Last refreshed: `2026-09-28 13:10:54` (America/Chicago).
- Workspace: v2 active; v1 frozen. External references require task-specific authorization.
- Canonical position: BP-02 -> [BP-02.06](docs/Build%20Plans/BP-02/BP-02.06%20Recovery%20and%20Integration.md) / V1 / R1 fault orchestration; next R2 publication/acceptance recovery.
- Progress: parent 84.38% (27/32 deliveries). Children .01-.05 complete/audited/archived; .06 at 0% (V1 0%, V2 0%); BP-03..09 at 0%.
- Latest work: actual independently installed runtime/artifact peers proved completion/confirmation, cancellation/release before stale completion resumes, original receipt replay and conserved budgets. [Completion audit](docs/Audits/BP-02.05_Completion_Delivery_Closeout.md) passed.
- Evidence: 298 aggregate tests with PostgreSQL; lint/import/schema gates, eight independent wheels, both standalone probes and paired integration passed. 68 published schemas. HTTP workers have no database credentials; service environments contain only their own database URL.
- Authority: autonomous continuation and significant commit/push checkpoints authorized. No current user blocker. Scientific/provider/host choices remain later gates.
- Environment: Python 3.12, uv and labeled PostgreSQL 17.11 fixture. Dynamic endpoint/credentials only in ignored v2/.test-results/postgres-fixture.json. Set AMPHORA_TEST_POSTGRES=1; never publish credentials. Serialize fixture resets against tests.
- Git: D5 0a31eb5 pushed; D6 closeout verified for commit/push. Identity tkn1234 <alb_gen@live.com>; origin https://github.com/neverhumanbot/mvp20-split.git.
- R1 handoff: reuse runtime-owned tests/acceptance harness. Add explicit test-only fault entrypoints and exact scenario manifests for REC-01..09; ordinary startup has no injection switches. R2/R3 kill actual owned processes and restart retained state; R4 independent install/restore; R5 audit/parent closeout. No private cross-owner imports or SQL assertions. Public GET artifact reservation observes protection without mutation.
- Limits: .06 full crash matrix remains required. Linux/target-storage power-loss/backup stays BP-09. No interpreter/scientific validity/provider/Studio claim. Existing test-client warning is nonblocking.

## Decomposition and Resume Discipline

BP-02 now has six focused child plans and separate history. BP-03..09 now have 34 canonical child plans with owned objects/contracts, transition/algorithm decisions, named failure oracles, independent test tiers and replacement acceptance. BP-02 children have detailed API/transaction/crash matrices. Parent planning histories preserve prior task pairs; new queued-parent denominators are 16/20/16/24/20/20/20, all at 0%. The nearest child gets physical design, failure tests, module replacement boundaries and scoped audit. Parent rollups count child implementation once. The preliminary 34-task count was explicitly corrected to 32 by separating pure design gates S1/A1; prior design work remains complete.

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

Private PostgreSQL schemas/migrations and canonical command registration/terminal receipt transactions exist. Default runtime construction remains validation-only; explicit fixture hosting enables durable lifecycle and read endpoints. General campaign validation reports `executable=false`. Artifact upload/finalization APIs now publish verified immutable references; protective reservation/confirm/reconcile handshake is implemented against a configured public runtime outcome client; bounded reconciliation/cleanup and standalone hosting are implemented. Optional synthetic fixture admission is implemented; configured claim/renewal handlers are implemented; atomic fixture completion acceptance and retention delivery are implemented; interpreter, scientific tools, knowledge reasoner, provider calls and Studio are not implemented. Paired integration establishes fixture retention; process-crash tests do not establish target-host power-loss durability or scientific validity. Those gates remain in their named children/successor plans.

Baseline verification: no changed manifest file content; verifier reports pre-existing added `v1/LICENSE` already present in commit `99d219c`. Do not regenerate the frozen manifest or alter v1 to suppress this discrepancy.
