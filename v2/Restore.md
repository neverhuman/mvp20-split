# Restore

Read this first after compression. Refreshed 2026-10-05 20:55:37 (America/Chicago).

## Resume

Continue until needed. Production checkpoint integration pushed6d167632. d.a installed compatibility COMPLETE, ready commit/push. Current **B2.01d.b independent process barriers**, next d.c relevance/issuance/membership fences. Runtime0.40/runtime0023;Planning0.76/planning0016;publicSupervision0.4;538 schemas. NEVER Runtime<=0.38 or Planning<=0.73 migrators. .test-results/checkpoint-policy-installed-20261005/manifest.json PASSED:802 cases (Runtime292 each,Planning109 each),42/32 predecessor migrations unchanged,536 predecessor schemas. No SQL/migration in installgate. No tests/hosts/processes running.

Read BP-07.04 Checkpoint acceptance.md for bounded process proof. Next create Runtime-owned process_worker.py under tests/supervision_checkpoints and dev/verify_checkpoint_recovery.py orchestrator. Use current installed runtime initial/replacement Python from passed directory. Copy tests only, production imports from wheels. Credentials env-only; actual retained SQL head0023 already applied. Blueprint: nested scalar materialize fixture (policy target loop/pack) -> abrupt exit after admission pin/frontier before commit; replacement sees pending command/no run. Two-process exact admission race returns one original receipt. Abrupt exit after slot insertion during first advance rolls back expansion/slot but keeps pending advance command. Race same advance command across installs ->one slot/identical replies. Fresh advance retains original scalar bytes/deadline, no binding/invocation. Cancel scoped run then replay original receipts/history. Verify all spawned processes exit. No paid provider or graph-effect claim. Existing old verify_supervision_journal.py (0.26) MUST NOT run; use its barrier pattern only. Existing owner HTTP verifier remains hardpinned0.33/0.75, not current acceptance.

Current code: initial/later ready targets create slots; original ready state unchanged. ValueCheckpointSeed private v2 captures actual scalar values/digest, read_seed retains v1. Old profile cannot authorize scalar effect. CheckpointStore loads pinned policy and actual plan, validates selected observations via verify_footprint, bounds deadline/ceiling and replays original slot first. B2.02 winners/effects;B2.03 context/request bridge. c is complete; d.c must demonstrate relevant refresh candidate without rewriting original or refreshing deadline/budget.

## Canonical progress

Parent66.39%,13/20;child31.94%,Build42.59%,Acceptance0%,1/4. B1=100%;B2=27.78%(.01=83.33%,.02/.03=0%);B3/V1=0%. B2.01 a/b/c100%,d33.33%;d.a100%,b/c0%. Current d.b.

## Active boundaries and versions

Runtime0.40/runtime0023; Planning0.76/planning0016; public supervision0.4; graph-runtime0.13; public Planning0.9;536 schema files. Actual DB heads are0021/0016. **NEVER run Runtime<=0.35 or Planning<=0.73 migrators.** Data0.29/artifacts0012 (never<=0.25 migrators), Research0.34/research0013 (never<=0.33), Knowledge0.18, Registry0.1.

Invoke inputs remain Artifact-only. Owner approved scalar checkpoints on named inline fields of `artifact_materialize` before any conversion intent, reservation or publication. Keep original plans/Artifacts/issued inputs immutable. Future admission policy must bind types/units/bounds and concrete occurrences; effective field resolution must be shared by conversion opening and source-cut revalidation. Pure scope/frame support is not admission or execution acceptance.

Implemented:
- `CheckpointTarget`/`CheckpointFootprint` v2 include field names, preserve whole-node conflicts across v1/v2, distinguish loop/scatter occurrences. Original DecisionFootprint stays Invoke-only; legacy export rejects v2.
- Public CheckpointRequest/Snapshot2 and separate `planning.supervision.request.v2` parser; old parser remains closed. New private CheckpointFrame/frame.v2; explicit read_frame dispatch. RequestSeries rejects profile switching.536 schemas preserve528 predecessor bytes; fixtures are pinned.
- Runtime journal recovers both profiles; new delivery.v2 evidence preserves old evidence parser. Request/outbox exact command family is retained. Response/cancel recover original frame. Current-target checks rederive actual plan fields, inline/scalar source and absence of binding_intents. Forward0021 extends outbox family CHECK only.
- Planning CheckpointIntakeSnapshot and explicit command/snapshot dispatch preserve original wrapper/receipt. Receipt lookup accepts keyword family with old default. Forward0016 extends family CHECK only. No model attempt/provider grant side effect.
- Planning0.75 has separate v2 POST request/receipt and GET readback. Wrong-profile reads return409; ready checks compatible family constraint. Runtime0.33 CheckpointPlanningClient selects v2 model/family/routes; original client stays v1-only. Shared bounded10s/3-call transport, exact bytes, guards, receipt-first recovery, no automatic retry/version fallback.

## Recent verification

B2.01a:66 scope/request tests;197 statements22 branches100%;34 target/boundary cases. B2.01b.i:144 combined contract/frame/schema cases;31 focused/boundary; new frame22 statements100%. Initial pytest process stalled before output, stopped only owned processes; clean retry passed.

B2.01b.ii:145 actual SQL/legacy cases26.76s;18 target/boundary18.26s;824 statements98 branches99%; Planning intake100%. First143pass/1fail exposed a hardcoded v1 family in the outbox insert, fixed; transaction rolled back. No historical migration files changed. Runtime final-event fallback remains an explicit gap; v2 Invoke review separately passed actual SQL.

B2.01b.iii:45 API/host/client tests21.59s;24 path-coverage API tests19.20s;12 boundary8.47s. Client34 statements100%,Planning app96%,whole API87%; CLI subprocess uninstrumented. App gaps: DBAPI handler, one access classification, incompatible-schema readiness.

**Coverage instrumentation issue:** dotted leaf `--cov=amphora_agent_planning.supervision_api.app` reproducibly causes SQLAlchemy Cython InternalTraversal initialization errors before SQL tests. Identical2cases pass without coverage3.94s and with filesystem source coverage4.12s. Use filesystem source directories (as dev/run_tests.py does); no application/dependency workaround applied. Do not claim failed instrumentation runs as passing API evidence. Full filesystem API run24 passed.

Evidence under `docs/Audits/Evidence/BP-07-Supervisor/`: Checkpoint_Targets, Checkpoint_Exchange, Checkpoint_Journals, Checkpoint_HTTP JSON. B1 actual owner proof remains `Actual_Owners.json`, installation proof `Owner_Installations.json`.

## Operating rules

Continue across milestones, commits, pushes and compaction until a concrete blocker or authorized scope completion; never end at a clean checkpoint. Update canonical percentages/history/Restore before significant commits. MBT recent checkpoint rows capped25; detailed history stays in companion files. Completion measures scoped work, not scientific certainty.

No subagents, JARVIS access, v1 edits, resets or old migrators. Source/test/dev/README writes stop during verification. SQL tests are serial and explicitly opt-in; keep retained fixture history. Secrets stay env-only; never print URLs/tokens/passwords. Future-only receipt corrections; no active campaign repinning. Weak science stays explicit without blanket exploration veto. Live provider/model/egress/spend unselected blocks only actual calls.

Workspace Z:/mvp20-split, active v2; PowerShell, America/Chicago. Set PYTHONUTF8=1 every Python shell. Python `v2/dev/.venv/Scripts/python.exe`; uv `v2/.venv/Scripts/uv.exe`; pytest `-c v2/dev/pyproject.toml --tb=short`. Use absolute(), not resolve(), on Windows. Prefer rg --files before paths; avoid guessed filenames and PowerShell directory/*.py globs. Normal Ruff, no lint overrides. Start background helpers hidden. Communicate at least every60s.

Git `git -c safe.directory=//DesktopNAS/Code/mvp20-split`; main; https://github.com/neverhumanbot/mvp20-split.git. Commit/push authorized; identity/auth configured. Existing v1/LICENSE metadata debt untouched.

## Installed predecessor pointers

Read-only migration predecessors: `.test-results/supervision-owners-installed-20261005-verified/{runtime,planning}/initial` (Runtime0.29/Planning0.72); never migrate them. Four old installations passed472 cases; B1 actual proof `.test-results/supervision-actual-owners-20261005-recovery/manifest.json` passed11 stages,6 hosts,2 lost replies. Older Runtime0.26/Planning0.69 installations are historical only. Current installation output named above is usable only after manifest status passed.
