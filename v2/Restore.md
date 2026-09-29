# Restore

## Current Checkpoint

- Last refreshed: `2026-09-29 15:52:36` (America/Chicago).
- Workspace: v2 active; v1 frozen; no external JARVIS access without task-specific request.
- Canonical position: BP-04 -> BP-04.04A / Build / B3. User explicitly approved prerequisite implementation, phases/ordering/percentages. No approval remains pending.
- Progress: BP-02/BP-03 closed 100%; BP-04 active 58.33% (14/24), .01/.02/.03 closed 100%, .04A active 50% (Build 66.67%, Acceptance 0%), .04/.05 queued 0%. Six phases: compiler, scheduling, aggregation, typed bindings, solver baseline, recovery.
- Latest verified boundary: Runtime 0.9.0, campaigns 0.4.0, graph-runtime 0.3.0; migrations through runtime_0013. Explicit bindings host config enables wire-v4; default admission remains gated. Public worker DTOs unchanged; all 134 predecessor schema bytes preserved.
- B2 verified: artifact_bindings owns finite projection/materialization, exact decimal/schema checks, stable identities/input cuts, run-locked preparation/closure and outside-SQL publication/reservation. Cancellation/deadline and late reservations retain truthful outcomes. New graph observation route /v3/graph-runs. No conversion consumes worker budget.
- Verification: 160 scoped predecessor/binding tests, then 39 focused binding cases (408/442 owned statements, 70/82 branches), including empty/missing/Artifact materialization; two-iteration round trip [7,11,15], ten actual affine-kernel/Runtime worker invocations and twenty conversions. Scripted Artifact peer; actual new peer/process acceptance remains B3/V1.
- Final B2 foundation/build gate passed 1079 tests, thirteen independent installs, paired owners and REC-01..09 4ab86e458ca64f5f88b9a1e2c6927880. Log .test-results/bp0404a-b2-final-foundation.log; exec 41289 finished exit 0. No verification running.
- Resume: BP-04.04A/B3 actual competing/interrupted owner processes with measured lock/lease barriers, immutable closure/protection proof, changed source cuts and malformed/foreign input oracles. Use waits/process_probe.py and test_process_recovery.py as local structural references; B2 authored dynamic graph is tests/bindings/definitions.py. V1 must run installed Artifact/SDK/tool peers and replacement before solver baseline .04. No approval pending; continue autonomously and commit/push milestones.
- Tracker repair: BP-04 Planning History now contains original scope and completed P1/P2 100% milestones with authoritative links; removed obsolete canonical/0% tables. Dated parent baseline statements are explicitly historical. Update child, parent, MBT and this handoff together; do not recreate duplicate history trackers. MBT keeps at most 25 checkpoints.
- Git: 40f03c6 contains the verified B1 checkpoint and approved ordering/percentage correction; pushed to origin/main. Prior eab555b proposal and 6b122a8 .03 closeout remain pushed. Identity tkn1234 <alb_gen@live.com>; origin https://github.com/neverhumanbot/mvp20-split.git. Commit/push significant updates and keep this handoff synchronized.
- Environment: Python 3.12/uv; labeled PostgreSQL 17.11 fixture, credentials only in ignored .test-results/postgres-fixture.json. Owner roles/migrations; never reset or run global single-campaign suites concurrently. AMPHORA_TEST_POSTGRES=1 explicit. Use `exit $LASTEXITCODE` after redirected native PowerShell commands. Default Git newline configuration passes diff checks; overriding core.autocrlf=false on CRLF files produces misleading whitespace failures.
- Reproduce focused gate: dev/run_tests.py --module runtime --area bindings --coverage. Tests distinguish real persistence, scripted Artifact clients and actual installed predecessor recovery. Closed .02 installed graph evidence remains in docs/Audits/Evidence/BP-04-Scheduling; no child reopened.
- Authority/limits: explicit user approval resolves BIND-01 scope decision. Implement approved domain-neutral conversion prerequisite without further permission; scientific authority BP-06.06, scientific search BP-08, host evidence BP-09. v1 frozen.
- Tools: numeric 0.2.0 and sequence 0.3.0; image manifest .test-results/tool-images/bp0304-20260928-1706/manifest.json. Installed graph gate: dev/verify_graphs.py --images <manifest>. Windows process acceptance and Linux image goldens remain separate tiers.

## Decomposition and Resume Discipline

BP-02 now has six focused child plans and separate history. BP-03..09 now have 35 canonical child plans with owned objects/contracts, transition/algorithm decisions, named failure oracles, independent test tiers and replacement acceptance. BP-02 children have detailed API/transaction/crash matrices. Parent planning histories preserve prior task pairs; new queued-parent denominators are 16/24/16/24/20/20/20; current progress is above. The nearest child gets physical design, failure tests, module replacement boundaries and scoped audit. Parent rollups count child implementation once. The preliminary 34-task count was explicitly corrected to 32 by separating pure design gates S1/A1; prior design work remains complete.

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
