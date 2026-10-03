# Restore

## Current Checkpoint

- Last refreshed: `2026-10-03 13:18:06` (America/Chicago).
- BP-06.05/B1.01 verified; active task is B1.02 public representation DTOs, examples and domain mappings. B1=16.67%, Build=5.56%, child=4.17%, parent BP-06=67.36%. Closed gates remain 0/4 and 16/24. B1 has six equal milestones, B2 four, B3 three, V1 one. No owner blocker; continue authorization persists.
- Data0.12.0 adds private `representations` profiles, exact input/scoped work identities, canonical finite binary32 vectors and deterministic synthetic UTF-8 byte histogram. Complete profile choices participate in the digest. No cache, source-binding publication, API or retrieval implementation yet. No schema/migration change;406 schemas and artifact_0007 unchanged.
- Verification:64 source/64 final-wheel focused tests;236/236 statements and22/22 branches covered;14 dev tests, boundaries and schema checks pass. Existing Data regression initially340/342 source and341/342 installed passes; failures were peer startup timeouts. Cold imports measured25.33s/25.09s against15s readiness. Test-only readiness now60s; all6 affected acquisition/process scenarios pass from source117.76s and final installed wheel107.10s. No operation/crash/replay assertion or production timeout changed. Failed runs retained in `Domain_Identities.json` evidence.
- Independent Data wheel: `.test-results/data-representations-domain-formatted-20261003/environment/Scripts/python.exe`, pytest/httpx installed, peer implementations excluded. Actual Research peer: `.test-results/research-laboratory-closeout-20261003/environment/Scripts/python.exe` (0.31.0). Full installed Data baseline used semantically identical pre-format wheel; final wheel passes64 pure and6 process cases separately. No running tests.
- Commit/push this verified checkpoint, then immediately B1.02. Plan/design/tracker/history/drift/evidence synchronized; Restore refreshed before commit. Last earlier pushed commit was cc466f1. All changes belong to active work; v1 untouched.
- B1.02: create focused `contracts/representations` public package; complete component/profile DTOs, scoped profile reference, exact source-span binding request, canonical hex vector Artifact document, binding/status projections. Explicit Data mappers preserve pure behavior ownership. See physical design wire section. Registry/cache next B1.03; generation/retrieval DTOs accompany B2 transitions. Preserve406 predecessor schema hashes captured in `.test-results/representation-contract-predecessor-schemas.json`.
- Internal computation cache must remain private. Equal bytes from distinct sources may share computation but retain separate derived Artifacts and independent rights. Scientific corrections affect future campaigns only; rights revocation applies to every new use. Qdrant integration is later B2; no deployment claim or scientific encoder selected.
- Tooling: PYTHONUTF8=1; Python `dev/.venv/Scripts/python.exe`; uv `.venv/Scripts/uv.exe`; pytest `-c dev/pyproject.toml`; git `-c safe.directory=//DesktopNAS/Code/mvp20-split`. Explicit UTF-8 file I/O. No concurrent PostgreSQL suites, retained DB reset, v1 edits, JARVIS access or subagents. Milestones and commits are not stopping points.

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
