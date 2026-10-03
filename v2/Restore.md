# Restore

## Current Checkpoint


- Last refreshed: `2026-10-02 19:56:27` (America/Chicago).
- Active plan: BP-06.03/Build/B1.09 assessment artifact/receipt publication. B1 milestones8/10=80%; Build26.67%, child20%, parent36.67% ((8+0.8)/24). Closed delivery gates remain child0/4,parent8/24; active acceptance0%. DER-01 stays closed without extra parent credit. Owner approved fractional milestone accounting; the canonical child table owns the denominator/evidence.
- Latest checkpoint: B1.08 complete, Research0.8.0.271 source and271 independently installed tests pass; store123 statements/34 branches covered. Forward research_0003, previous migrations unchanged. Evidence: docs/Audits/Evidence/BP-06-Research/Assessment_Store.json.296 public schemas unchanged. Private immutable assessments exist; no output receipt/public assessment HTTP yet.
- Next: B1.09 Research assessment output publication and atomic owner receipt. Start from assessment store README and publication design; use public derived-publication SDK with Research-owned journal, stable command identities and durable reconciliation. Read stored decisions without reevaluation; recheck current Data rights before publication. No peer I/O inside SQL. B1.10 owns authenticated submit/read API; B2/B3/V1 remain open. No owner decision or process pending.
- Recovery: only verified pending original receipts enable explicit same-identity resume. Unknown transport outcome first reconciles; collision/denial/terminal ambiguity never gets a fresh ID. Newer local edits survive recovery. Cancellation is operational and retains explicit uncertain-effects wording.
- Runtime0.20.0, Commands0.2.0, graph-runtime0.11.0, campaigns0.4.1;296 public schemas; all294 synthetic-evidence predecessors preserved. Numeric v2 only save/admit; other families/unmarked bytes v1. Input NumberValue remains decimal string. Registry eligibility synthetic-only observations are not reservations/atomic revocation. No scientific or target-host deployment claim.
- Tooling: mapped v2/dev/.venv/Scripts/python.exe, PYTHONUTF8=1; pytest/ruff --config equivalents use v2/dev/pyproject.toml. Git always -c safe.directory=//DesktopNAS/Code/mvp20-split. Never reset retained PG or run parallel campaign-admission suites. No v1/JARVIS/subagents. Use Path.absolute for repo tooling; Path.resolve maps Z to UNC and breaks uv source identity.
- Integration: solver images .test-results/tool-images/bp0503-authoring-20260930/manifest.json for verify_studio_integration --authoring. Standard images bp0503-standard-20260930 for foundation optional worker gate. Do not mix profiles.

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
