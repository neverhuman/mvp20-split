# Restore

## Current Checkpoint

- Last refreshed: `2026-09-29 23:03:28` (America/Chicago).
- Current plan: BP-05 -> BP-05.03 / Build / B1 active. Child0%=0/4, Build0%/Acceptance0%; parent50%=8/16. BP-05.01/.02 closed/audited. No user decision pending.
- Pinned validation verified:18 owned tests; full foundation1272 Python +65 Node tests,19 independent installs and REC-01..09 pass. Runtime0.15.0/runtime_0016 retain exact scoped tool/schema material and immutable validation results with original receipts;194 public schema bytes remain unchanged. Publication/admission integration and Studio authoring remain B1 work. Child0%=0/4, Build0%, Acceptance0%; parent50%=8/16 unchanged.
- Last pushed c7e4125 (save/read); verified validation checkpoint about to commit. Foundation session88270 complete/pass, no process running. Log .test-results/bp0503-validation-foundation.log; durable evidence docs/Audits/Evidence/BP-05-Authoring/Validation.json.
- Next: reviewed-plan publication/resolver integration and registry-driven Studio forms/comparison/emergency commands. Active child has physical design/watchpoints. No B1 credit until whole boundary passes.
- Actual source: Runtime definitions/{revisions,commands,storage,reads,http}.py; private migration runtime_0015; explicit host authoring=true requires configured graphs and author/read grants. Save/head/revision/audit/receipt atomic; advisory per-draft lock covers creation; head only updatable field, revision/audit immutable. Scoped head pages select metadata only. Old Runtime receipt union stays frozen; definition receipts use separate route. New validate/read-validation API and runtime_0016 implemented; no admit-draft API yet.
- Code checkpoints: c262e33 closes .02 (actual navigation replacement scopee222d4cf32604d729ef12146860bc49c). Current Runtime0.15.0/graph-runtime0.8.0/campaigns0.4.1;194 schemas. Preserve published bytes; default validation-only/configured execution remains unchanged. Generated inventory refreshed by passed gate.
- Tooling: mapped v2/dev/.venv/Scripts/python.exe; standalone pytest -c v2/dev/pyproject.toml; PYTHONUTF8=1 and explicit UTF-8; redirected logs may UTF16. Git always -c safe.directory=//DesktopNAS/Code/mvp20-split. v1 frozen; no JARVIS/subagents authorized. AMPHORA_TEST_POSTGRES=1 for ownedPG; never concurrent campaign-admission suites, reset retained fixture or print credentials.
- Full gate takes about12 minutes; keep source fixed during it, communicate progress, do not infer failure from buffered log silence. Focused tests first; repeat broad gate only for new source changes/concerns. Stage owned files and update all trackers before commits/push significant checkpoints.

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

Private PostgreSQL schemas/migrations and canonical command registration/terminal receipt transactions exist. Default runtime construction remains validation-only; explicit fixture hosting enables durable lifecycle and read endpoints. General campaign validation reports `executable=false`. Artifact upload/finalization APIs now publish verified immutable references; protective reservation/confirm/reconcile handshake is implemented against a configured public runtime outcome client; bounded reconciliation/cleanup and standalone hosting are implemented. Optional synthetic fixture admission is implemented; configured claim/renewal handlers are implemented; atomic fixture completion acceptance and retention delivery are implemented; configured deterministic graph admission/advancement and process/peer replacement acceptance are complete in BP-04.02; validated scientific tools, knowledge reasoner and provider calls are not implemented; Studio has verified transport/page models, measured synthetic interaction and production-client browser failure proof; actual-owner observation UI is accepted; topology/navigation accepted under BP-05.02; next-campaign authoring remains active BP-05.03 scope. Paired integration establishes fixture retention; process-crash tests do not establish target-host power-loss durability or scientific validity. Those gates remain in their named children/successor plans.

Baseline verification: no changed manifest file content; verifier reports pre-existing added `v1/LICENSE` already present in commit `99d219c`. Do not regenerate the frozen manifest or alter v1 to suppress this discrepancy.
