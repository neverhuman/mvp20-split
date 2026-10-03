# Restore

## Current Checkpoint

- Last refreshed: `2026-10-03 05:18:56` (America/Chicago).
- Active BP-06.04/Build/B2.04a public status + authenticated private workflow. B2.03 complete100%; B2.04 a/b/c0%. B2=75%,Build58.33%,child43.75%,parent57.29%; closed gates1/4 and13/24 unchanged. No owner blocker; continue authorization persists.
- B2.03c pending commit: Research0.29.0/contracts0.13.0; research_0012 applied.808 source/808 installed +119 compatibility/dev; one old actual scientific HTTP opt-in skipped per suite.21 focused cases (14 contract,7 owner),83 owner statements/14 branches100%.402 schemas preserve392.616 preexisting material dependency links backfilled, canonical decision bytes unchanged. Evidence Correction_Views_Impacts.json. Prior push4485281(b),f5b7156(a),aa4543d(.02). No running processes/tests.
- c adds public exact correction views and MaterialStateImpactRequest/InterpretationImpactRequest/Page; no widening old ScientificImpactRequest or ScientificDecision kinds. observations/material_state correction_views loadexact successor/immediate predecessor; no heads/writes. persistence/material_impact.py and observations/interpretation/index.py expose bounded exact known dependencies with digest-checked cursors, future_campaigns_only. research_0012 locks decisions through backfill/AFTER INSERT trigger; invoker role, scopedFK, append-only maintenance including old writers. No new HTTP yet.
- Next read BP-06.04 Interpretation API design.md: a explicit pending/interpreted status and fresh authenticated source reads for exact store preparation; b optional reviewed host profiles/separate grants/routes; c actual independent Data/Research correction/replay/replacement. Use focused interpretation_api module, do not grow common workflow/backend. Stored intent owns pendingretry profile; completehistory offline.
- observations/interpretation profile/wire/document + intent/preparation/store from a/b own2MiB intent/8MiB result,<=128source dependencies. Original actor/config/request; exact immutable obs/experiment plus report/protocol/applicability/sampleidentity/materialfeature/processing sources. Complete atomically records result+indexes and rechecks owned content. Pure builder consumed inputs are not authentication proof; B2.04 must read fresh current Data rights before newcompletion.
- Latest isolated Research .test-results/research-correction-impacts-installed-20261003/environment/Scripts/python.exe0.29.0 with testdeps; ONLY this installed Research knows0012. All earlier Research owners through0.28 MUST NOT migrate retainedDB0012. Data .test-results/knowledge-publication-installed-20261002-1359/initial/data/Scripts/python.exe0.11.0 unchanged protocol. Pre0012 evidence .test-results/material-impact-pre0012.json, env AMPHORA_TEST_MATERIAL_IMPACT_BASELINE.
- Dependencies: Research contracts0.13.0,Evidence0.5.12/Knowledge contracts0.7.7; Knowledge0.15.7/Data0.11.12. Runtime0.20.2/graph-runtime0.13.0/SDK0.2.0 unchanged.
- B1 complete actual independent scientific HTTP/idle replacement. Defensive route/body-timeout/publication lease-race/exhaustion/release gaps remain B3/V1; actual d was not crash-at-barrier. Closed BP-06.03 remainsclosed. B2.01 normalization and B2.02 quality/corrections complete. SQ-01 owns future quality UI.
- Tooling: PYTHONUTF8=1; dev/.venv/Scripts/python.exe; pytest -c v2/dev/pyproject.toml; ruff --config same. AMPHORA_TEST_POSTGRES=1; never concurrent PG suites/reset retainedDB. Git -c safe.directory=//DesktopNAS/Code/mvp20-split. No v1/JARVIS/subagents. No __init__.py in testfolders. Use rg --files, avoid broad rglob through .venv.

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

Private PostgreSQL schemas/migrations and canonical command registration/terminal receipt transactions exist. Default runtime construction remains validation-only; explicit fixture hosting enables durable lifecycle and read endpoints. General campaign validation reports `executable=false`. Artifact upload/finalization APIs now publish verified immutable references; protective reservation/confirm/reconcile handshake is implemented against a configured public runtime outcome client; bounded reconciliation/cleanup and standalone hosting are implemented. Optional synthetic fixture admission is implemented; configured claim/renewal handlers are implemented; atomic fixture completion acceptance and retention delivery are implemented; configured deterministic graph admission/advancement and process/peer replacement acceptance are complete in BP-04.02; validated scientific tools and provider calls are not implemented; bounded synthetic Knowledge reasoning and Data artifact/logical-receipt publication exist; Research assessment/publication/correction and actual Runtime receipt/partial-output/recovery verified; Studio has verified transport/page models, measured synthetic interaction and production-client browser failure proof; actual-owner observation UI is accepted; topology/navigation accepted under BP-05.02; next-campaign authoring is accepted under closed BP-05.03; integrated interaction/performance/replacement acceptance closed under BP-05.04. Paired integration establishes fixture retention; process-crash tests do not establish target-host power-loss durability or scientific validity. Those gates remain in their named children/successor plans.

Baseline verification: no changed manifest file content; verifier reports pre-existing added `v1/LICENSE` already present in commit `99d219c`. Do not regenerate the frozen manifest or alter v1 to suppress this discrepancy.
