# Restore

## Current Checkpoint

- Last refreshed: `2026-10-02 22:56:01` (America/Chicago).
- Active: BP-06.03/V1.02 Research publication process-death proof. V1.01 fresh Research rebuild/cutover passed101.96s. B1 10/10,B2 4/4,B3 3/3 complete. Build100%,child83.33%,parent47.22%; gates3/4,11/24; acceptance33.33%.
- B3.03 passed: actual installed test1 in214.38s, .test-results/runtime-domain-recovery-bounded-20261002.{json,xml}. Both owner receipt acknowledgements suppressed after real commit; Runtime replaced and exact command replay/closure verified. Real Data confirmation ACK suppressed, Runtime replaced, identical confirmation retried; Artifact bytes hash matches. Domain_Receipt_Recovery.json is portable evidence. Prior probe failures retained: wrong assumption first delivery was confirmation, then arbitrary10s one-process-per-entry retry budget. Current first-loss probe advances one delivery at a time; recovery uses normal bounded sweep. Notification sinks intentionally unconfigured; their failures are not Artifact failures.
- Latest pushed53305c0 B3 complete. V1.01 independent Research replacement passed; .test-results/research-v1-replacement-20261002/manifest.json and research-replacement-acceptance-20261002.{json,xml}.14 dev tests, schema publication and production dependency checks pass. V1 units: rebuild complete1/3; publication interruptions active; compatibility/audit/archive pending. Publication README already names process-death acceptance; do not close without this proof. No owner question pending. Keep working across checkpoints.
- Current uncommitted docs also repair Research/Knowledge root/module README stale versions/future statements; verify links when closing. No production code/schema changes in B3.

- Helpers: services/campaign_runtime/tests/waits/acceptance/domain_bridge.py (public Runtime host/compile/receipt), domain_partial.py (partial output). Research actual fixture loads them by path; no Runtime private imports. Runtime compilation/migration in its interpreter only. Source test can use dev Python; installed runs require explicit Runtime peer.
- Installed Runtime .test-results/runtime-domain-receipt-peer-20261002/environment/Scripts/python.exe; Knowledge .test-results/knowledge-correction-installed-20261002/environment/Scripts/python.exe; Data .test-results/knowledge-publication-installed-20261002-1359/initial/data/Scripts/python.exe. Research .test-results/runtime-partial-progress-installed-20261002/environment/Scripts/python.exe. Each isolated.
- Latest evidence .test-results/runtime-partial-progress-installed-20261002/{tests.xml,rerun.xml,rerun-clean.xml,actual-peers-rerun-clean.json}. Only last rerun succeeds; do not relabel original failed batch. B3.01 manifest .test-results/runtime-domain-receipts-installed-20261002/manifest.json passed334.
- Tooling dev/.venv/Scripts/python.exe; PYTHONUTF8=1, AMPHORA_TEST_POSTGRES=1, AMPHORA_TEST_DOMAIN_RUNTIME=1 and AMPHORA_TEST_RUNTIME_PYTHON / AMPHORA_TEST_DATA_PYTHON / AMPHORA_TEST_KNOWLEDGE_PYTHON explicit absolute installed paths. AMPHORA_RESEARCH_RESOLUTION_EVIDENCE names output. pytest -c v2/dev/pyproject.toml from root. Never concurrent PG suites or reset retained PG. Git -c safe.directory=//DesktopNAS/Code/mvp20-split. No v1/JARVIS/subagents.
- Policy: future-only corrections preserve active pins including pending consumption. Campaign completion is progress, not scientific truth. Preserve uncertain points; block only explicit action prerequisites. UI richer quality/focus is queued SQ-01, not implemented. Prior report reuse is context, not renewed scientific acceptance.
- B3 changes test/dev only. Versions unchanged: Runtime0.20.2, Research0.12.1/contracts0.6.0, Knowledge0.15.0/contracts0.7.0, graph-runtime contracts0.13.0, Data0.11.5 metadata (installed actual Data0.11.0 compatible);316 schemas, Research0005/Knowledge0007.

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

Private PostgreSQL schemas/migrations and canonical command registration/terminal receipt transactions exist. Default runtime construction remains validation-only; explicit fixture hosting enables durable lifecycle and read endpoints. General campaign validation reports `executable=false`. Artifact upload/finalization APIs now publish verified immutable references; protective reservation/confirm/reconcile handshake is implemented against a configured public runtime outcome client; bounded reconciliation/cleanup and standalone hosting are implemented. Optional synthetic fixture admission is implemented; configured claim/renewal handlers are implemented; atomic fixture completion acceptance and retention delivery are implemented; configured deterministic graph admission/advancement and process/peer replacement acceptance are complete in BP-04.02; validated scientific tools and provider calls are not implemented; bounded synthetic Knowledge reasoning and Data artifact/logical-receipt publication exist; Research assessment/Runtime receipt integration pending; Studio has verified transport/page models, measured synthetic interaction and production-client browser failure proof; actual-owner observation UI is accepted; topology/navigation accepted under BP-05.02; next-campaign authoring is accepted under closed BP-05.03; integrated interaction/performance/replacement acceptance closed under BP-05.04. Paired integration establishes fixture retention; process-crash tests do not establish target-host power-loss durability or scientific validity. Those gates remain in their named children/successor plans.

Baseline verification: no changed manifest file content; verifier reports pre-existing added `v1/LICENSE` already present in commit `99d219c`. Do not regenerate the frozen manifest or alter v1 to suppress this discrepancy.
