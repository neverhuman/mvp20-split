# Restore

## Current Checkpoint

- Last refreshed: `2026-09-29 21:23:21` (America/Chicago).
- Canonical position: BP-05 -> BP-05.02 / Build / B2. Child1/4=25%, Build33.33%/Acceptance0%; parent5/16=31.25%. BP-05.01 closed100%; BP-04 closed24/24. No user decision pending. B1 verified; continue B2, then B3/V1.
- Last known pushed checkpoints: e1944aa closes .01,5d61f43 adds owner topology,53ed5ee adds navigation consumer. Catalog checkpoint1b65328 pushed. B1 inspector checkpoint verified; commit/push pending final checks. Identity tkn1234 <alb_gen@live.com>;origin https://github.com/neverhumanbot/mvp20-split.git. Keep child->parent->MBT->Restore synchronized at milestones.
- Windows PowerShell. Use mapped `v2/dev/.venv/Scripts/python.exe`; uv is `v2/.venv/Scripts/uv.exe`. PYTHONUTF8=1 and explicit UTF-8 file reads/writes; redirected logs may be UTF-16. Standalone pytest must specify `-c v2/dev/pyproject.toml` or use dev/run_tests.py. AMPHORA_TEST_POSTGRES=1 for actualPG. Retained labeled fixture config only in ignored .test-results/postgres-fixture.json; never reset or run concurrent campaign-admission suites. COVERAGE_FILE under .test-results.
- Git requires `-c safe.directory=//DesktopNAS/Code/mvp20-split`; preserve newline configuration. v1 frozen/read-only, no JARVIS/subagents authorized. Pre-existing v1/LICENSE discrepancy from99d219c remains untouched. check_changed_links.py is repeat-safe; old one-use closeout/scaffold scripts are not.
- Studio Node24.18/npm11.16, Chromium153 local Playwright; no browser MCP. `npm test`, `npm run test:browser`, `npm run test:navigation`, `npm run test:interaction` are distinct owned tiers. Browser helper credentials remain server-side and excluded from Chromium's environment. No production gateway deployed. The test adapter is not deployment evidence.
- Baseline full foundation at .01/B1:1223 Python/28 Node,19 isolated installs, RECscope1525e057e4434c72af20c5e9948ec4f7. .01 actual-owner browser/replacement evidence is archived in docs/Audits/Evidence/BP-05-Interaction/V1.json. Current .02 evidence is scoped and does not claim a repeat of those full gates.

## BP-05.02 Working Checkpoint

- B1 verified; B2 sole active task. Full foundation session57408 finished0:1245 Python tests,53 Node,19 independent installs, REC-01..09 scope4ad3384b504d40848373fa8fa1be4eae and registry replacementc455ee118dd24ea995a7359f290d690b. Log .test-results/bp0502-b1-foundation.log. Isolated Studioe34a0dbd5382429bbbc09f018dd1424f passed53 tests. No process running.
- Runtime0.13.0/graph-runtime0.7.0/campaigns0.4.1;182 schemas,180 predecessor bytes preserved. Studio consumes10 roots, including pre-existing CompletionRecord/ArtifactRef. Runtime graph_navigation owns topology/scopes/catalog; navigation/capability/lineage/linked-evidence models own bounded, fenced read regions. Evidence never fetches artifact content or infers scientific acceptance.
- Three scripted browser suites (7 Monitor,7 navigation,7 evidence) pass; latest manifests under .test-results/studio-monitor/2026-09-30T02-07-40-723Z, studio-navigation/2026-09-30T02-07-48-911Z, studio-evidence/2026-09-30T02-07-51-389Z. Screenshots inspected. Durable B1 evidence and selected screenshot: docs/Audits/Evidence/BP-05-Navigation/. This is not actual-owner navigation acceptance; B3/V1 still owe that.
- Runtime navigation coverage158/158 statements,8/8 branches (session14445 finished0); loaded Studio99.43% lines/86.70% branches/95.63% functions. Gaps recorded in page_models README; no instrumented React coverage claim. Full gate repaired only import ordering in existing dev/verify_graphs.py.
- B2 next: explicit run-scoped invalidation (producer emits run_changed only), hidden-view staleness, preserve selected occurrence/neighborhood/viewport, bounded historical pins with honest omissions, fixture-only compatible material-state/method/unit/applicability comparison and explanation-vs-causality distinction. Preserve source-local model authority and one loader per region. NamedViews/NavigationPane currently bind on component mount; hidden models need explicit policy coordination. No historical mutable-frontier API exists. Scope/revocation must clear affected protected state.
- Implementation notes: TopologyWindow currently compares graph_scope via JSON.stringify; B2 should compare semantic fields independent of object property order. Graph scope pages replace at100; topology bounded256, visible scene200 with next-window navigation. Scope ordering is currently stable hash order, not natural occurrence index. Child counts mean instantiated occurrences; distinguish not-yet-instantiated nested definitions. Evidence/NamedViews/Navigation source/test READMEs capture remaining failure combinations.
- Commit B1 after final link/diff checks; update this handoff with resulting commit next checkpoint. Then work B2 without asking for approval; no user decision pending. Closed .01/BP-04 remain closed.

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
