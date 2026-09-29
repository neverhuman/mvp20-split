# Restore

## Current Checkpoint

- Last refreshed: `2026-09-29 13:25:53` (America/Chicago).
- Workspace: v2 active; v1 frozen; no external JARVIS access without task-specific request.
- Canonical position: BP-04 -> BP-04.04A / Build / B2. User explicitly approved prerequisite implementation, phases/ordering/percentages. No approval remains pending.
- Progress: BP-02/BP-03 closed 100%; BP-04 active 54.17% (13/24), .01/.02/.03 closed 100%, .04A active 25% (Build 33.33%, Acceptance 0%), .04/.05 queued 0%. Six phases: compiler, scheduling, aggregation, typed bindings, solver baseline, recovery.
- Latest verified boundary: Runtime 0.8.0, campaigns 0.4.0, graph-runtime 0.3.0 (v4 compiler only; execution stays v2/v3); locks refreshed. Collection policy plus wire-v3 admission/hosting, passive waits, receipt delivery, exact Artifact protection/closure and timeout/cancellation/terminal cleanup implemented. Public schema bytes unchanged; migrations through runtime_0011.
- Collection semantics: deadline starts at containing scope creation. Expiry permits the next owner-serialized committed revision cut; it does not reconstruct a past clock instant. Minimum alone never closes. Branches must resolve, unrelated pending prerequisites remain blocking, pending/unstarted member slots stay explicit. Overall run deadline wins. Root completion settles unused pure work while preserving prepared Artifact protection. Legacy scopes with unknown clocks explicitly fail deadline behavior.
- B1 verified: Runtime 0.8.0, campaigns 0.4.0, graph-runtime 0.3.0; wire-v4/profile-v3 contracts/compiler with 148 schemas preserve 134 predecessor schema bytes. Twenty binding compiler cases, 142 total compiler cases; scoped coverage 664/668 statements and 172/174 branches. Actual PostgreSQL admission refuses v4 until B2 exists.
- Final foundation/build gate passed 1041 tests, thirteen independent installs, paired owners and REC-01..09 5808a82a94eb42dfa7eac527700364cd. Log .test-results/bp0404a-b1-final-foundation.log, exec 28279 finished exit 0. No verification running. New binding runtime execution is not implemented.
- Resume: BP-04.04A/B2 durable conversion/publication/protection. Read Graph_Artifact_Bindings.md for stable binding identity/input cut and outside-SQL I/O design; implement focused Runtime-owned modules, runtime_0012, exact protection/commit/replay and terminal cleanup before removing admission guard. Keep workers/tool protocol unchanged. B3 actual processes and V1 installed producer/scatter/gather/consumer round trip precede .04 solver parity. No user approval pending.
- Tracker repair: BP-04 Planning History now contains original scope and completed P1/P2 100% milestones with authoritative links; removed obsolete canonical/0% tables. Dated parent baseline statements are explicitly historical. Update child, parent, MBT and this handoff together; do not recreate duplicate history trackers. MBT keeps at most 25 checkpoints.
- Git: this B1 checkpoint is ready for commit/push; prior eab555b proposal and 6b122a8 .03 closeout are pushed. Identity tkn1234 <alb_gen@live.com>; origin https://github.com/neverhumanbot/mvp20-split.git. Commit/push significant updates and keep this handoff synchronized.
- Environment: Python 3.12/uv; labeled PostgreSQL 17.11 fixture, credentials only in ignored .test-results/postgres-fixture.json. Owner roles/migrations; never reset or run global single-campaign suites concurrently. AMPHORA_TEST_POSTGRES=1 explicit. Use `exit $LASTEXITCODE` after redirected native PowerShell commands. Default Git newline configuration passes diff checks; overriding core.autocrlf=false on CRLF files produces misleading whitespace failures.
- Reproduce focused gate: dev/run_tests.py --module runtime --area aggregation --coverage. Tests distinguish real persistence, scripted Artifact clients and actual installed predecessor recovery. Closed .02 installed graph evidence remains in docs/Audits/Evidence/BP-04-Scheduling; no child reopened.
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
