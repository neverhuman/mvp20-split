# Restore

Refreshed `2026-10-04 23:41:51` (America/Chicago). Read this FIRST after every compression. Continue across gates, commits, pushes and compactions until an actual owner decision blocks work. No subagents, JARVIS access or v1 edits.

Refreshed `2026-10-04 23:41:15` (America/Chicago). Read this FIRST after every compression. Continue across gates, commits, pushes and compactions until an actual owner decision blocks work. No subagents, JARVIS access or v1 edits.

B2.03b.i is verified; commit/push pending. Latest pushed `ce8c7804` (events), prior `82bd2a13` (effects), `ed4c0697` (selection), `02677ecc` (actual compiler owners), `9935048e` (stored origin). Planning/dev **0.65.0**, public Planning0.9.0,510 schemas. Retained database is **planning0013**: NEVER use Planning<=0.64 migrators. No tests or owned hosts running.

Canonical progress: child BP-07.03 **44.44%**, Build59.26%, Acceptance0%; parent BP-07 **48.89%**. Closed deliveries1/4 and9/20. B1=100%; B2.01/.02=100%, B2.03=33.3333%, B2=77.7778%; B3/V1=0%. B2.03 a100%, b33.3333%, c/d0%. Unit b: i history/selection/leases100%, ii operations/events0%, iii SQL/replacement0%.

## Exact next work

1. Review and commit/push verified storage checkpoint. Continue **B2.03b.ii operation/event journal**. Design is in `docs/Build Plans/BP-07/BP-07.03 Compiler handoff.md`. Implement additive operation/event tables after0013; do not edit existing migrations. Selection/control0013 and original histories stay immutable.
2. `campaign_dispatch/history.py` reconstructs PreparedCampaignProposal from owned preparation/attempt/observation, derives declaration/budget/review/authoring from the original witness, verifies actual reserved/settled charge and exact selection. `store.py` registers selection after those immutable reads, uses scoped advisory locks and explicit configured Runtime/Registry identities, retains first bytes/time, and manages DB-clock1..300s holder/fence leases. It has no operation/event writes or peer I/O.
3. Journal operations must derive exact effect bytes from CompilerHistory. Validate registration requires the saved effect's exact terminal readback, never caller flags. Readback replays typed events and checks all indexed digests/positions. Mutation must check the selection lease at the final write, so expiry rolls back all inserted rows. No peer I/O under SQL. Preserve historical candidate expiry and negative/uncertain outcomes.
4. Registry freshness rounds need an explicit finite bound and complete selected-tool coverage. Prefer preparing a batch once; existing CompilerEffect.eligibility re-derives the whole batch per tool, which should not become quadratic work while holding a lease. A new round must not replace unresolved old commands. New check IDs are intentional; lost replies keep original bytes. Record dispatch before effects; current processing/freshness checks remain coordinator c, not historical journal reads.
5. Tests belong in `tests/campaign_dispatch_storage`; original selection14-case suite remains. Actual SQL proof uses current migrations only, serial/opt-in. Independent helper `dev/verify_planning_compiler_origin.py --area selection` runs origin+dispatch-storage suites using a passed current compiler/dispatch wheel manifest. No resets, credentials environment-only. Changing the migration requires raising the minimum compatible migrator in Restore/docs immediately.

Latest evidence `Dispatch_Storage.json`:14 SQL cases72.25s,142 statements8branches100%;12 boundary8.35s;198 isolated dispatch52.577s;26 installed SQL55.645s (14 selection+12 original origin). Installation `.test-results/planning-compiler-selection-storage-independent-20261004/environment/Scripts/python.exe`; SQL manifest `.test-results/planning-compiler-selection-storage-installed-20261004/manifest.json`. Current pure dispatch tests still53; no source/test/dev edits while verification runs.

## Current module contracts and earlier evidence

`campaign_dispatch` now includes selection storage/leases; operation/event persistence and dispatcher remain pending. CompilerSelection retains original actor/attempt, preparation/proposal hashes and exact declaration/budget/Registry configuration. Stable selection ID excludes configuration and generated output. Restore checks read authority and canonical bytes; verify_origin reconstructs original policy. Pure values do not establish persisted provenance.

CompilerEffect derives save/validate or exact selected Registry check commands. Its1MiB wrapper pins selection ID/hash, owner, kind, check/tool and exact public command bytes. Validate requires exact saved readback. Restore re-derives bytes from original inputs. Changing configuration keeps the operation slot but changes contents. Public command limits remain256KiB.

CompilerObservation binds typed receipt/readback to selection/effect/request. Registry checks include original configuration, attempt, check and context because policy hash is absent from Registry command bytes. CompilerEvent replays prepared/dispatch/uncertain/blocked/observed, at most64 positions, reserving slot64 for terminal evidence. Individual saved/compiled/structural_invalid/rejected/candidate outcomes do not imply campaign admission. Historical candidate replay never renews expiry.

Latest evidence `Dispatch_Events.json`:53 scoped cases70.06s;277 statements18branches100%;12 boundary cases8.96s;198 isolated dispatch cases53.087s. Installation: `.test-results/planning-dispatch-events-independent-20261004/environment/Scripts/python.exe`. `dev/verify_planning_context.py --scope dispatch` runs public Planning contracts plus dispatch/authoring/eligibility; unchanged compiler proof reused from0.62 (285 cases94.799s). No source/test/dev edits while verification runs.

Actual primitive owner proof: `.test-results/planning-compiler-owners-v3-20261004/manifest.json`,3 worker stages/4 hosts, Runtime0.20.2/Registry0.1; numeric1.25 save/compile, structural-invalid negative, exact restart/drain history and new-check rejection. Scalar graph and separate eligibility only; combined coordinator proof remains B2.03d. Linux capacity metadata is synthetic, with no worker/provider launch. Harness pins Planning0.61; do not run unchanged against0.64.

Stored origin SQL proof: `.test-results/planning-compiler-origin-installed-20261004/manifest.json`,12 cases23.286s using0.61. Pure value additions have no SQL changes. Preparation/observation/reservation/settlement history remains immutable.

## Navigation and environment

- Canonical child: `docs/Build Plans/BP-07/BP-07.03 Campaign proposals and context.md`; parent: `docs/Build Plans/BP-07 Autonomous LLM Campaign Supervision.md`; history: `docs/Build Plans/BP-07 Planning History.md`; MBT: `docs/Build Plans/Master Build Tracker.md`. Update current prefixes and parent phase table, not historical percentages. MBT retains25 recent rows.
- Evidence: `docs/Audits/Evidence/BP-07-Campaigns/`. Drift: `docs/Audits/Architecture Drift.md`. Closed BP-07.02 stays closed. Live provider/model/egress/spend choices block only real calls, not deterministic work.
- Workspace `Z:/mvp20-split`; active v2. Git: `git -c safe.directory=//DesktopNAS/Code/mvp20-split`; main; pushes authorized. Never print credentials.
- Python `v2/dev/.venv/Scripts/python.exe`; uv `v2/.venv/Scripts/uv.exe`. PYTHONUTF8=1. Pytest `-c v2/dev/pyproject.toml --tb=short`; normal Ruff discovery. Test folders belong to modules; use rg --files before choosing paths. Windows paths use absolute(), not resolve().
- PostgreSQL tests serial, opt-in AMPHORA_TEST_POSTGRES=1, retained fixture, no resets. Planning0013: never Planning<=0.64 migrators. Research0013: never Research<=0.33. Artifact0012: never Data<=0.25. Tighten Planning minimum after any new migration. No migration at service startup.
- Peer installations under `v2/.test-results`: Runtime `runtime-domain-receipt-peer-20261002/environment`; Registry `registry-campaign-context-independent-20261004/environment`; Data0.29 `data-processing-content-independent-20261004/environment`; Knowledge0.18 `knowledge-processing-independent-20261004/initial`; Research0.34 `research-declarations-final-independent-20261004/initial`. Append `/Scripts/python.exe`. Old harnesses may pin old versions or migrate: inspect before reuse.
- Human corrections affect future campaigns only. Never repin active inputs. Preserve weak/unknown/contradictory science; no blanket quality veto. Frozen v1/LICENSE manifest metadata debt remains unchanged. No active skills/goals/subagents.
