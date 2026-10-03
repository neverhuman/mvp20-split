# Restore

## Current Checkpoint

- Last refreshed: `2026-10-02 22:33:01` (America/Chicago).
- Active: BP-06.03/B3.03 delivery fault recovery. B1 10/10, B2 4/4, B3 2/3. Build88.89%, child66.67%, parent44.44%. Closed gateschild2/4,parent10/24; acceptance0%. DER-01 closed.
- B3.02 verified: source partial graph passes; installed333 cases plus clean rerun1 pass. Exact report retained as context, two abstained waits share current correction receipt and expose evidence_insufficient missing slots through public inspection. Actual QEV05..07 and wrong-purpose/subject/authority rejection verified. Evidence Partial_Campaign_Progress.json. Original batch failed on test actor mismatch; corrected test's first rerun hit stranded campaign; exact failed run fa5db3d7942148cb92c7358d76608672 cancelled through public API. Harness now cancels its own unfinished run on failure. No DB reset.
- Latest pushed615d016 B3.01. B3.02 ready to commit/push; immediately continue B3.03. No owner decision pending; continuation persists.
- Next: bounded test-only HTTP relay suppresses a successful Runtime receipt acknowledgement, replace Runtime and replay exact original command; suppress actual Data confirmation acknowledgement, verify retry preserves exact identity/closure/output/protection. Reuse existing owner replacement/offline evidence. Then V1 independent replacement/compatibility/audit. No production fault hooks or scope/denominator expansion.
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
