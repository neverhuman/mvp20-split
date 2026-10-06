# Restore

Read this first after compression. Refreshed 2026-10-05 20:41:28 (America/Chicago).

## Resume

Continue until needed. c.iii.a pushed743004a3. c.iii.b storage COMPLETE verified, ready commit/push; current **c.iii.c coordinator checkpoint creation**, next d SQL fencing/recovery. Runtime0.39/runtime0023;Planning0.76/planning0016;publicSupervision0.4. Actual retained DB runtime0023. NEVER Runtime<=0.38 or Planning<=0.73 migrators.146 SQL/checkpoint/policy/journal33.54s;143checkpoint statements2branches100%,shared current membership100%;12boundary9.03s,Ruff passed. Initial expiry fixture protected deadline UPDATE failed; changed to real one-second admission expiry. No tests running.

CheckpointStore.ensure(conn,params,path) acquires existing run lock, loads actual retained plan/admitted policy, replays original slot before fresh state/deadline checks, snapshots selected observations and verifies actual membership via shared current.verify_footprint. Append-only runtime.supervision_checkpoints; ordinal beyond max_checkpoints or expired deadline records fallback_required, no execution effect. Pending context work, NOT Planning request. Existing verify_current now delegates membership helper plus original request deadline check; old/new journals regressed.

Next: admission after full root frontier create, iterate ALL ready policy targets and ensure slots before Invoke issuance. GraphPass interim guard becomes ensure; return created=True to count a transition once, False on subsequent hold. Use lazy imports for checkpoint storage to avoid coordinator package import cycles. Existing storage tests currently create slots explicitly AFTER admitted run; integration will mean initial slots already exist, so revise fixture to defer target readiness or assert original already-created slots. Preserve store-specific failure tests and real expiry. B2.02 terminal winner/fallback/effects; B2.03 context/request bridge. No live provider needed.

## Canonical progress

Parent66.20%,13/20;child31.02%,Build41.36%,Acceptance0%,1/4. B1=100%;B2=24.07%(.01=72.22%,.02/.03=0%);B3/V1=0%. B2.01 a/b100%,c88.89%,d0%;c.i/ii100%,iii66.67%;iii.a/b100%,c0%. Current iii.c.

## Active boundaries and versions

Runtime0.39/runtime0023; Planning0.76/planning0016; public supervision0.4; graph-runtime0.13; public Planning0.9;536 schema files. Actual DB heads are0021/0016. **NEVER run Runtime<=0.35 or Planning<=0.73 migrators.** Data0.29/artifacts0012 (never<=0.25 migrators), Research0.34/research0013 (never<=0.33), Knowledge0.18, Registry0.1.

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
