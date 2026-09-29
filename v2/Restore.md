# Restore

## Current Checkpoint

- Last refreshed: `2026-09-29 18:38:04` (America/Chicago).
- Canonical position: BP-04 -> BP-04.05 / Acceptance / V1. No owner input needed. BP-04 active95.83%=23/24; .05 active75%=3/4 (Build100%,Acceptance0%); .01/.02/.03/.04A/.04 closed100%.
- B1 verified: new graph_inspection snapshot/detail/value/invalidation boundary, additive graph-runtime0.5.0 DTOs, Runtime0.11.0, campaigns0.4.0; migration runtime_0014 unchanged. 176 schemas;168 predecessors byte-unchanged. Module/test READMEs and granular selector present.
- Verification: foundation session20780 finished0;1202 tests,19 independent installs,REC-01..09 scope792994c7f28c484780f33ed404220a41. Final scoped coverage session91436 finished0:72 tests,217/217 statements12/12 branches. Logs .test-results/bp0405-b1-foundation.log and bp0405-b1-focused.log; evidence docs/Audits/Evidence/BP-04-Recovery/B1.json. No verification running.
- B2 verified: three real process-kill cuts after uncommitted activation INSERT, join commit and iteration checkpoint commit.32 focused/process regression tests passed; session83449 finished0, .test-results/bp0405-b2-focused.log. No production/schema change. Evidence docs/Audits/Evidence/BP-04-Recovery/B2.json. B3 passed76 focused contract/module tests with217/217 statements12/12 branches; session99871 finished0, log bp0405-b3-focused.log; public ASGI concurrency/history/guard/resnapshot failures verified. Resume V1 independently installed observer/Runtime replacement and parent closeout. Plan: add observations profile to dev/verify_graphs.py using solver environment plus independent graph-runtime-contract observer/replacement installs; actual Registry/Artifact/Runtime/tools and existing solver images manifest .test-results/tool-images/bp0404-solver-20260929-1747/manifest.json. Observer must import no owner/SQL, consume cursor across Runtime/observer replacement, validate public DTOs, preserve receipt/lineage/Artifact evidence. B3 scoped audit present but final V1/parent audit open.

- Snapshot/detail/values require unchanged run revision; poll invalidations from ordinal-zero audit events with consecutive revisions. Reuse existing inspection original receipt/report/history authority. No second journal. Keep scientific/provider/host/UI claims at later gates.
- Git: B1 pushed87c529a; B2 pushed1ac3052; B3 verified changes pending commit/push. Identity tkn1234 <alb_gen@live.com>; origin https://github.com/neverhumanbot/mvp20-split.git. Update child -> parent -> MBT -> Restore before significant commits. MBT stale40% queue mirror corrected.
- Environment: Windows PowerShell, mapped-path v2/dev/.venv/Scripts/python.exe (uv run UNC caused native psycopg failure). uv v2/.venv/Scripts/uv.exe for locks/build/sync. AMPHORA_TEST_POSTGRES=1 explicit. Use PYTHONUTF8=1 and explicit UTF-8 docs I/O; redirected PowerShell logs may be UTF-16. Full gate about9min and buffered; use python -u next time for progress. PostgreSQL fixture is retained/labeled; credentials only ignored .test-results/postgres-fixture.json. Never reset or run campaign-admission PG suites concurrently. Set COVERAGE_FILE under ignored .test-results.
- Git safe.directory=//DesktopNAS/Code/mvp20-split; preserve newline config. v2 active, v1 frozen/read-only; external JARVIS not authorized; no subagents authorized. v1/LICENSE preexisting99d219c discrepancy, do not alter baseline. One-use close/scaffold scripts are NOT idempotent; check_changed_links.py is safe to repeat.

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
