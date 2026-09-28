# Restore

## Current Checkpoint

- Last refreshed: `2026-09-28 12:35:03` (America/Chicago).
- Workspace: v2 active; v1 frozen. External references require task-specific authorization.
- Canonical position: BP-02 -> [BP-02.05](docs/Build%20Plans/BP-02/BP-02.05%20Completion%20and%20Delivery.md) / V1 / D4 bounded outbox delivery; next D5 historical receipt/read projections.
- Progress: parent 75% (24/32 deliveries). Children .01-.04 complete/audited/archived; .05 at 50% (V1 60%, V2 0%); .06 and BP-03..09 at 0%.
- Latest work: exact retention outcomes, atomic terminal delivery intents and bounded abandoned/cancelled command recovery verified; lifecycle standalone runtime and HTTP-only worker death/reclaim accepted; [closeout](docs/Audits/BP-02.04_Invocation_Lifecycle_Closeout.md). Cancellation/revocation, budget conservation and live database-clock fencing are implemented.
- Evidence: 278 aggregate tests with PostgreSQL; final recovery refinement passed 36 focused completion tests; lint/import/schema gates, eight independent wheels and both installed service probes passed. 58 published schemas. Workers have no database credentials.
- Authority: autonomous continuation and significant commit/push checkpoints authorized. No current user blocker. Scientific/provider/host decisions remain later gates.
- Environment: Python 3.12, uv and labeled PostgreSQL 17.11 fixture. Dynamic endpoint/credentials only in ignored v2/.test-results/postgres-fixture.json. Set AMPHORA_TEST_POSTGRES=1; never publish credentials. Do not run fixture restart/reset concurrently with tests.
- Git: D2 acceptance b738825 pushed; D3 retention/recovery checkpoint verified for commit/push. Identity tkn1234 <alb_gen@live.com>; origin https://github.com/neverhumanbot/mvp20-split.git.
- D4 handoff: implement bounded delivery leases/tokens/fences, stable event identities, conditional ack, backoff and explicit exhausted state. Both runtime.outbox and policy_outbox are required. Terminal artifact targets artifact_confirm/artifact_reconcile already carry exact command/binding payloads; notification targets are not execution authority. Keep network outside SQL and validate exact peer acknowledgements. D5 owns history/receipt queries; real runtime/artifact integration remains D6/.06.
- Limits: .05/.06 still own actual accepted completion/artifact retention and crash integration. Linux/target-storage power-loss/backup remains BP-09. Scientific validity is not established by synthetic profiles. Existing test-client warning is nonblocking.

## Decomposition and Resume Discipline

BP-02 now has six focused child plans and separate history. BP-03..09 now have 34 canonical child plans with owned objects/contracts, transition/algorithm decisions, named failure oracles, independent test tiers and replacement acceptance. BP-02 children have detailed API/transaction/crash matrices. Parent planning histories preserve prior task pairs; new queued-parent denominators are 16/20/16/24/20/20/20, all at 0%. The nearest child gets physical design, failure tests, module replacement boundaries and scoped audit. Parent rollups count child implementation once. The preliminary 34-task count was explicitly corrected to 32 by separating pure design gates S1/A1; prior design work remains complete.

Contract and persistence READMEs describe actual implemented boundaries. A4/A5 may use a scripted runtime outcome process to test the artifact client; .06 must repeat acceptance/release races against the actual .05 runtime. Do not treat fixture proof as integrated correctness. Use [MBT](docs/Build%20Plans/Master%20Build%20Tracker.md) and child tracker, not old task IDs in history.

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

Private PostgreSQL schemas/migrations and canonical command registration/terminal receipt transactions exist. Default runtime construction remains validation-only; explicit fixture hosting enables durable lifecycle and read endpoints. General campaign validation reports `executable=false`. Artifact upload/finalization APIs now publish verified immutable references; protective reservation/confirm/reconcile handshake is implemented against a configured public runtime outcome client; bounded reconciliation/cleanup and standalone hosting are implemented. Optional synthetic fixture admission is implemented; configured claim/renewal handlers are implemented; full completion acceptance, interpreter, scientific tools, knowledge reasoner, provider calls and Studio are not implemented. Artifact process-crash tests do not establish integrated runtime retention, target-host power-loss durability or scientific validity. Those gates remain in their named children/successor plans.

Baseline verification: no changed manifest file content; verifier reports pre-existing added `v1/LICENSE` already present in commit `99d219c`. Do not regenerate the frozen manifest or alter v1 to suppress this discrepancy.
