# Restore

## Current Checkpoint

- Last refreshed: `2026-10-03 16:41:32` (America/Chicago).
- Active BP-06.05/B2.01d owned projection verification/PG expected-head publication. c verified, pending commit/push; latest pushed ef72ab8. No owner blocker. Continue through commits/milestones in MBT order.
- B1=100%, B2.01a-c100%/d0%; B2=18.75%, B3/V1=0%, Build39.58%, child29.69%, parent71.61%; closed gates1/4 and17/24. Trackers/history synchronized.
- Data0.21.0 source/isolated; public representations0.2.0/430 schemas unchanged. artifact_0010 applied with actual0009->0010 checked row counts/hashes unchanged. No reset/downgrade; Data<=0.20 must NOT migrate retained0010.
- Generation_State.json:27 scoped source pass11.97s;488 full installed owner/contract cases pass197.42s;14 dev13.94s;lint/boundaries/schema checks pass. Retrieval346/348 statements19/20 branches; expired verified recovery branch remains d. No tests running.
- Independent interpreter `.test-results/data-generation-state-20261003/environment/Scripts/python.exe`, Data0.21, pytest/httpx; forbidden private peers absent. Set AMPHORA_TEST_REPRESENTATION_PYTHON to absolute path for actual HTTP child. Full regression also needs AMPHORA_TEST_RESEARCH_PYTHON `.test-results/research-laboratory-closeout-20261003/environment/Scripts/python.exe` (Research0.31/research_0012).
- B1 implemented exact profiles/cache/compute leases, source preflight/rights, durable derived vector publication/recovery, authenticated opt-in HTTP/hosting and isolated reconstruction. Original request replay remains history; fresh use requires current rights. Scientific corrections remain future campaigns only.
- B2.01a/b pure ordered1..256 binding manifest/4MiB bound, exact generation/attempt identity and namespace, phase policy; public request/ref/manifest/generation/status DTOs and explicit mappings. All420 preceding schema bytes preserved +10 new. No caller vectors/actor/backend/success authority. Examples have placeholder digests and are shape oracles only.
- c retrieval intents/records/leases plus artifact_0010: immutable generation/memberships/attempts/events, narrow mutable cursor. Current process rights before new admission/claim/renew; exact historical replay before fresh rights. Rights lock then corpus lock, no external I/O under SQL. Claims use DB-clock token/fence/namespace; old leases cannot affect successors. Renewal deadline rechecked in UPDATE after rights work. finish only failed/abandoned; prepared abandon allowed. Verified-expiry recovery branch fails generation (next d supplies actual proof).
- Next d physical matrix documented: trusted adapter build/inspect port, exact retained Artifact vector materialization outside transactions, observed bounded point-set/profile/vector comparison, final current-rights/winning-live-lease verification record, then atomic PG expected-head CAS/published marker/event. Actual Qdrant remains B2.02; test-only adapter must be labeled. Add forward0011 for verification/published/head records if needed; never alter applied0010. Keep stale attempts in distinct namespaces; no backend alias authority. Publication replay is historical, queries later recheckrights.
- d required tests: actual PG publication, mismatched/extra/missing/duplicate points, revoked rights/takeover during adapter I/O, verified expiry, competing expected heads, historical replay after later head, reconstruction and migration retention. Backend definition should bound dimensions/metric/points and inspection; fingerprint vector digests rather than serializing all max-size payloads into4MiB manifest limit. No production fake fallback.
- No JARVIS/v1/subagents. Use rg --files before paths. PYTHONUTF8=1; dev/.venv/Scripts/python.exe; uv .venv/Scripts/uv.exe; pytest -c dev/pyproject.toml; COVERAGE_FILE under.test-results. Dev tests may overwrite inherited coverage path: use separate dev coverage file. Git safe.directory=//DesktopNAS/Code/mvp20-split. No concurrent PG suites/environment mutations during tests. No goal/skill active.

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
