# Restore

## Current Checkpoint

- Last refreshed: `2026-09-29 18:50:04` (America/Chicago).
- Canonical position: BP-05 -> BP-05.01 / Build / B1. Activation audit corrected_ready; no owner input needed. BP-04 closed100%=24/24, all six children archived/audited. BP-05 active0%=0/16; .01 Build/Acceptance0%; .02-.04 queued0%.
- BP-04.05 V1 passed actual installed observer/Runtime replacement, scope71ea58db673441bb94e7ee8b5f99b529.17 wheels12 independent installs, actual Registry/Artifact/Runtime/SDK/five solver tools. Read12/28 nodes and48/115 events; three old-cursor/complete-detail comparisons equal after replacement.17 invocations44 confirmed reservations, five delivery passes; original lineage/receipts/Artifact bytes/proofs preserved. Evidence docs/Audits/Evidence/BP-04-Recovery/V1.json; child and parent audits aligned.
- First V1 run29559 failed on Windows worker marker PermissionError after initial observation/replacement passed. Test-only reader now retries transient missing/denied file reads within20sec, never repeats owner request or hides malformed JSON.7 helper tests pass. Full rerun84910 finished0, .test-results/bp0405-v1-installed-retry.log.12 dev tests pass. No verification running.
- Earlier production gate:1202 tests19 installs REC-01..09 scope792994c7f28c484780f33ed404220a41. B3 final focused76 tests, graph_inspection217/217 statements12/12 branches. Runtime0.11.0, graph-runtime0.5.0, campaigns0.4.0,176 schemas preserving168, migration runtime_0014 unchanged.
- Resume: BP-05.01/B1 schema-derived transport/page-model spike (abortable requests, bounded scope/page queries, selection/revision guards and explicit failure states). Read owning activation audit, UI Coding Guidelines (already reviewed), Interaction_References.md, Studio architecture and public observation module README. Framework/canvas choice is engineering spike before production UI; B2 requires200 visible/10000 logical synthetic nodes and accessible list, B3 browser evidence, V1 actual owner integration. Node/npm available; no browser MCP tool, local Playwright can be installed. Existing Runtime does not expose full run catalog/authored topology; .02 must refine actual owner projections before live navigation.
- Git: B1 pushed87c529a,B2 pushed1ac3052,B3 pushedac246d4; V1/parent closeout and BP-05 activation verified docs pending commit/push. Identity tkn1234 <alb_gen@live.com>; origin https://github.com/neverhumanbot/mvp20-split.git. Update child -> parent -> MBT -> Restore before significant commits.
- Windows PowerShell; mapped-path v2/dev/.venv/Scripts/python.exe (uv run UNC native psycopg issue); uv v2/.venv/Scripts/uv.exe for locks/build/sync. AMPHORA_TEST_POSTGRES=1 explicit; PYTHONUTF8=1 and explicit UTF-8 docs I/O. PowerShell redirected logs may be UTF-16. Retained labeled PostgreSQL fixture credentials only ignored .test-results/postgres-fixture.json; never reset or run campaign-admission suites concurrently. Put COVERAGE_FILE under ignored .test-results. Full foundation gate about9min; python -u reveals its available progress.
- Workspace v2 active, v1 frozen/read-only; external JARVIS not authorized, no subagents authorized. Git safe.directory=//DesktopNAS/Code/mvp20-split; preserve newline config. v1/LICENSE preexisting99d219c discrepancy, do not alter baseline. One-use close/scaffold scripts NOT idempotent; check_changed_links.py safe repeat.

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
