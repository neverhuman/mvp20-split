# Restore

## Current Checkpoint

- Last refreshed: `2026-10-03 13:32:03` (America/Chicago).
- BP-06.05/B1.02 verified; active B1.03 profile/cache storage. B1=33.33%, Build=11.11%, child=8.33%, parent BP-06=68.06%. Gates remain0/4 and16/24. B1 six equal milestones, B2 four, B3 three, V1 one. No owner blocker; continue authorization persists.
- Latest pushed commit f0e981c completed B1.01. Commit/push the verified B1.02 changes next, then immediately implement B1.03. No tests running. Data0.13.0, representation contracts0.1.0,420 schemas (all406 predecessor bytes preserved), artifact_0007 unchanged.
- B1.02 evidence:103 source/103 independent-wheel tests;397 statements/24 branches fully covered;14 dev tests, lint and dependency boundaries pass. New public package owns complete profile components, scoped refs, source-span requests, canonical hex vector documents, bindings/status. Data mapping/payload objects enforce complete profile/scope/vector consistency. Seven synthetic examples include a placeholder binding digest; no new HTTP/storage/rights claim.
- Independent interpreter `.test-results/data-representation-contracts-20261003/environment/Scripts/python.exe`; pytest/httpx installed; Research/Knowledge/Runtime implementations excluded. Evidence `docs/Audits/Evidence/BP-06-Representations/Public_Contracts.json`. B1.01 regression failures and corrected source/installed6-case process proofs remain in Domain_Identities.json. Test-only startup now60s after measured25s imports exceeded15s; production/fault assertions unchanged.
- B1.03 next: design and implement artifact_0008 immutable profile/work-intent/cache tables plus narrowly mutable DB-clock leases/fences, source-adjacent store README, real PostgreSQL tests for replay/conflicts/grants/lease expiry/concurrency. Profile registry has id/version conflict protection; cache identity is scope+full profile+exact input/context. Compute outside transactions; immutable completion rejects expired/stale workers. No raw cache API. Source-specific binding/rights publication belongs B1.04. Old Data migrators cannot target the newer schema; update test peers intentionally.
- Existing private helpers: persistence/evidence_records.py `_lock` and `_canonical` are owner-local; publication/model.py Principal grants/scope; acquisition/ledger.py illustrates immutable records and rights fencing. Migrations use private artifacts schema and SELECT/INSERT-only immutable tables; serving never migrates. Preserve retained PostgreSQL data and current science policy.
- Scientific corrections affect future campaigns only; access revocation applies to every new use. Equal source bytes may share computation but never merge source permission chains. Qdrant later B2, no scientific encoder chosen.
- Tooling: PYTHONUTF8=1; dev/.venv/Scripts/python.exe; uv .venv/Scripts/uv.exe; pytest -c dev/pyproject.toml. Set COVERAGE_FILE under ignored .test-results. Git -c safe.directory=//DesktopNAS/Code/mvp20-split. No concurrent PostgreSQL suites/reset, v1 edits, JARVIS access or subagents. Milestones/commits are not stopping points.

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
