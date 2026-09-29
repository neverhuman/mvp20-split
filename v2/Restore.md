# Restore

## Current Checkpoint

- Last refreshed: `2026-09-28 22:09:45` (America/Chicago).
- Workspace: v2 active; v1 frozen; no external JARVIS access without task-specific request.
- Canonical position: BP-04 -> [BP-04.03](docs/Build%20Plans/BP-04/BP-04.03%20Aggregation%20and%20failure%20policy.md) / Build / B3 actual competing-process proof. B1/B2 verified; V1 installed issuer/peer acceptance follows B3.
- Progress: BP-02 closed 100% (32/32); BP-03 closed 100% (16/16); BP-04 active 50% (10/20), .01/.02 closed/audited 100%, .03 active 50% (Build 66.67%, Acceptance 0%). BP-05..09 queued 0%. Child authoritative; parent/MBT mirrors.
- Latest verified boundary: Runtime 0.7.0, campaigns 0.3.1, graph-runtime 0.2.1; locks refreshed. Collection policy plus wire-v3 admission/hosting, passive waits, receipt delivery, exact Artifact protection/closure and timeout/cancellation/terminal cleanup implemented. Public schema bytes unchanged; migrations through runtime_0011.
- Collection semantics: deadline starts at containing scope creation. Expiry permits the next owner-serialized committed revision cut; it does not reconstruct a past clock instant. Minimum alone never closes. Branches must resolve, unrelated pending prerequisites remain blocking, pending/unstarted member slots stay explicit. Overall run deadline wins. Root completion settles unused pure work while preserving prepared Artifact protection. Legacy scopes with unknown clocks explicitly fail deadline behavior.
- Final verification COMPLETE: 68 focused waits (501/507 statements, 69/74 branches); full B2 log `.test-results/bp0403-b2-final-foundation.log`, exit 0: 1,001 tests, thirteen independent installs, paired owners, Registry replacement 7342ea6b54cb426ba8aadee59bfde857 and REC-01..09 b85109f93d704848af90f46f04bf89fe. Exec 38188 finished; no verification process running. No source changes since that gate.
- Resume: B2 verified, trackers synchronized, documentation/link/diff checks passed and implementation pushed as 12212e9. Resume B3. Use scheduling/test_process_recovery.py and process_probe.py as local precedents for actual competing processes. In-process wait callbacks are not process proof; installed predecessor recovery is not new issuer acceptance.
- Next steps: B3 must prove actual competing timeout/receipt commits choose one immutable closure, late/cancelled outputs cannot reopen and original receipts/protection persist. V1 then uses independently installed Runtime, actual synthetic issuer and available Artifact peer, including replacement. Keep child/parent/MBT/Restore synchronized; archive only after all four deliveries and scoped audit.
- B1 prerequisites: wire-v3 Await/compiler/plan profiles, receipt/expectation/closure DTOs and graph-page v2; 134 schema artifacts preserving 116 predecessor hashes. WaitRecords/WaitPreparation already pin/store exact waits and create separate PREPARED protection intents. These are not worker attempts and consume no attempt budget. Existing fixture tests deliberately bypass admission for storage proof; they are not executed-wait acceptance.
- Tracker repair: BP-04 Planning History now contains original scope and completed P1/P2 100% milestones with authoritative links; removed obsolete canonical/0% tables. Dated parent baseline statements are explicitly historical. Update child, parent, MBT and this handoff together; do not recreate duplicate history trackers. MBT keeps at most 25 checkpoints.
- Git: 12212e9 `Integrate protected external waits and synchronize verified B2 trackers` is pushed. Predecessor c3863ad `Execute immutable collection policies and synchronize BP-04 trackers` is pushed. Earlier e20a4a7 implements B1; ac6808b refreshed its handoff. Identity tkn1234 <alb_gen@live.com>; origin https://github.com/neverhumanbot/mvp20-split.git. Continue autonomously; commit/push significant updates and keep this handoff current between commits, explicitly requested by the user.
- Environment: Python 3.12/uv; labeled PostgreSQL 17.11 fixture, credentials only in ignored .test-results/postgres-fixture.json. Owner roles/migrations; never reset or run global single-campaign suites concurrently. AMPHORA_TEST_POSTGRES=1 explicit. Use `exit $LASTEXITCODE` after redirected native PowerShell commands. Default Git newline configuration passes diff checks; overriding core.autocrlf=false on CRLF files produces misleading whitespace failures.
- Reproduce focused gate: dev/run_tests.py --module runtime --area aggregation --coverage. Tests distinguish real persistence, scripted Artifact clients and actual installed predecessor recovery. Closed .02 installed graph evidence remains in docs/Audits/Evidence/BP-04-Scheduling; no child reopened.
- Authority/limits: synthetic issuer permitted; real Research/Knowledge receipt authority BP-06.06. Pure/synthetic tools only. v1/successor parity .04; integrated graph recovery .05; LLM/knowledge/Studio/scientific/target-host acceptance later. No user blocker, K3s, power-loss or scientific claim. Existing v1/LICENSE manifest discrepancy and test-client deprecation remain unchanged.
- Tools: numeric 0.2.0 and sequence 0.3.0; image manifest .test-results/tool-images/bp0304-20260928-1706/manifest.json. Installed graph gate: dev/verify_graphs.py --images <manifest>. Windows process acceptance and Linux image goldens remain separate tiers.

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

Private PostgreSQL schemas/migrations and canonical command registration/terminal receipt transactions exist. Default runtime construction remains validation-only; explicit fixture hosting enables durable lifecycle and read endpoints. General campaign validation reports `executable=false`. Artifact upload/finalization APIs now publish verified immutable references; protective reservation/confirm/reconcile handshake is implemented against a configured public runtime outcome client; bounded reconciliation/cleanup and standalone hosting are implemented. Optional synthetic fixture admission is implemented; configured claim/renewal handlers are implemented; atomic fixture completion acceptance and retention delivery are implemented; configured deterministic graph admission/advancement and process/peer replacement acceptance are complete in BP-04.02; scientific tools, knowledge reasoner, provider calls and Studio are not implemented. Paired integration establishes fixture retention; process-crash tests do not establish target-host power-loss durability or scientific validity. Those gates remain in their named children/successor plans.

Baseline verification: no changed manifest file content; verifier reports pre-existing added `v1/LICENSE` already present in commit `99d219c`. Do not regenerate the frozen manifest or alter v1 to suppress this discrepancy.
