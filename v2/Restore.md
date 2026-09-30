# Restore

## Current Checkpoint

- Last refreshed: `2026-09-29 20:55:43` (America/Chicago).
- Canonical position: BP-05 -> BP-05.02 / Build / B1. Child0/4=0%, Build0%/Acceptance0%; parent4/16=25%. BP-05.01 closed100%; BP-04 closed24/24. No user decision pending. Continue the remaining B1 inspector work below, then ordered B2/B3/V1.
- Last known pushed checkpoints: e1944aa closes .01,5d61f43 adds owner topology,53ed5ee adds navigation consumer. Catalog checkpoint verified below; check git status/log for commit position. Identity tkn1234 <alb_gen@live.com>;origin https://github.com/neverhumanbot/mvp20-split.git. Keep child->parent->MBT->Restore synchronized at milestones.
- Windows PowerShell. Use mapped `v2/dev/.venv/Scripts/python.exe`; uv is `v2/.venv/Scripts/uv.exe`. PYTHONUTF8=1 and explicit UTF-8 file reads/writes; redirected logs may be UTF-16. Standalone pytest must specify `-c v2/dev/pyproject.toml` or use dev/run_tests.py. AMPHORA_TEST_POSTGRES=1 for actualPG. Retained labeled fixture config only in ignored .test-results/postgres-fixture.json; never reset or run concurrent campaign-admission suites. COVERAGE_FILE under .test-results.
- Git requires `-c safe.directory=//DesktopNAS/Code/mvp20-split`; preserve newline configuration. v1 frozen/read-only, no JARVIS/subagents authorized. Pre-existing v1/LICENSE discrepancy from99d219c remains untouched. check_changed_links.py is repeat-safe; old one-use closeout/scaffold scripts are not.
- Studio Node24.18/npm11.16, Chromium153 local Playwright; no browser MCP. `npm test`, `npm run test:browser`, `npm run test:navigation`, `npm run test:interaction` are distinct owned tiers. Browser helper credentials remain server-side and excluded from Chromium's environment. No production gateway deployed. The test adapter is not deployment evidence.
- Baseline full foundation at .01/B1:1223 Python/28 Node,19 isolated installs, RECscope1525e057e4434c72af20c5e9948ec4f7. .01 actual-owner browser/replacement evidence is archived in docs/Audits/Evidence/BP-05-Interaction/V1.json. Current .02 evidence is scoped and does not claim a repeat of those full gates.

## BP-05.02 Working Checkpoint

- B1 remains0/4 verified deliveries, Build0/Acceptance0, parent25%. Partial checkpoints5d61f43 (Runtime topology) and53ed5ee (navigation consumer) pushed. Catalog/lineage checkpoint is verified and ready to commit; no process running.
- Runtime0.13.0/graph-runtime0.7.0 add scoped GraphViewCatalog to earlier occurrence/topology reads. Runtime advertises only execution_topology/successor_lineage with versioned schema, typed filters, result bounds/capability names.182 exported schemas, all180 predecessor schema bytes unchanged. Campaigns remains0.4.1. Locks updated/dev synced. No migration.
- Studio consumes eight generated roots; ViewCatalog and NamedViewsModel own capability validation/filter policy/catalog+lineage request fencing. NavigationPane displays real authored links only after both targets load; occurrence groups and bounded200-node scene/windows remain. NamedViews shows retained predecessor pins and unavailable scientific views. No scientific acceptance inferred.
- Verification:111 Python regression tests passed (explicit -c v2/dev/pyproject.toml required for standalone pytest);45 Node tests; seven scripted navigation browser scenarios/two viewport A/AA checks; screenshots inspected. Final navigation manifest .test-results/studio-navigation/2026-09-30T01-53-12-812Z. Isolated Studio installa18fbcff4dfe495b983c7a3db85b5fb2 passes. Seven predecessor Monitor browser cases passed at earlier navigation checkpoint. Boundary checks pass. No actual-owner navigation replacement or full foundation since .01 gate.
- Next B1: finish linked attempt/output/artifact inspector journey, then full compatibility gate. Existing public CompletionRecord endpoint `/v1/runs/{run}/completions/{id}` and ArtifactRef metadata `/v1/artifacts/{id}` suffice; browser must use separate same-origin owner adapter paths and never get service credentials. Check result scope/run/activation/completion/attempt/invocation/fence, accepted revision<=pinned cut, canonical flag, and exact artifact ref. No payload content fetch needed for metadata inspector. Monitor currently owns selected first detail page; preserve one loader owner if adding attempt paging. B2/B3/V1 still unstarted. No user decision pending.

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

Private PostgreSQL schemas/migrations and canonical command registration/terminal receipt transactions exist. Default runtime construction remains validation-only; explicit fixture hosting enables durable lifecycle and read endpoints. General campaign validation reports `executable=false`. Artifact upload/finalization APIs now publish verified immutable references; protective reservation/confirm/reconcile handshake is implemented against a configured public runtime outcome client; bounded reconciliation/cleanup and standalone hosting are implemented. Optional synthetic fixture admission is implemented; configured claim/renewal handlers are implemented; atomic fixture completion acceptance and retention delivery are implemented; configured deterministic graph admission/advancement and process/peer replacement acceptance are complete in BP-04.02; validated scientific tools, knowledge reasoner and provider calls are not implemented; Studio has verified transport/page models, measured synthetic interaction and production-client browser failure proof; actual-owner observation UI is accepted; complete topology/navigation/authoring remains later scope. Paired integration establishes fixture retention; process-crash tests do not establish target-host power-loss durability or scientific validity. Those gates remain in their named children/successor plans.

Baseline verification: no changed manifest file content; verifier reports pre-existing added `v1/LICENSE` already present in commit `99d219c`. Do not regenerate the frozen manifest or alter v1 to suppress this discrepancy.
