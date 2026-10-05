# Restore

## Resume here

Refreshed `2026-10-04 23:32:44` (America/Chicago). Read this FIRST after every compression. Continue across gates, commits, pushes and compactions until an actual owner decision blocks work. No subagents, JARVIS access or v1 edits.

B2.03a.iii is verified; commit/push pending. Latest pushed: `82bd2a13` (exact effect payloads), `ed4c0697` (selection), `02677ecc` (actual compiler owners), `9935048e` (stored origin). Planning/dev version **0.64.0**, public Planning0.9.0,510 schemas, retained Planning migration0012. No tests or owned hosts running.

Canonical progress: child BP-07.03 **43.75%**, Build58.33%, Acceptance0%; parent BP-07 **48.75%**. Closed deliveries remain1/4 and9/20. B1=100%; B2.01/.02=100%, B2.03=25%, B2=75%; B3/V1=0%. B2.03 has four equal units: a values100%, b journal0%, c coordination0%, d installed recovery0%. Unit b has three equal parts: i history/selection/leases, ii operations/events, iii SQL/replacement; all0%.

## Exact next work

1. Review and commit/push verified event work. Continue **B2.03b.i: original history, selection registration and leases**. The design is appended to `docs/Build Plans/BP-07/BP-07.03 Compiler handoff.md`; no new migration is applied yet.
2. Reconstruct PreparedCampaignProposal from owned preparation.record, attempt.binding and attempt.observation. Load declaration/budget from selection witness, derive CampaignDecisionReview/AuthoringPlan and verify CompilerSelection. Compare actual reservation/settlement with StoredCampaignOrigin. Existing CampaignOriginReader exposes the four owned journals. Immutable reads may precede a short registration transaction; never hold SQL across peer I/O.
3. Add campaign-specific selection/control storage and a migration after0012. Pin one original actor/attempt slot; changed configuration must conflict. Use DB-clock holder/fence/expiry, exact scope/actor/configuration and final guarded mutations. Existing `owner_handoff/store.py` is a reviewed same-service pattern; do not change closed extraction tables/formats. Implement/read-test selection and lease scope first; operations/events and saved-readback dependencies are b.ii.
4. Future operation storage must reconstruct expected requests from owned history before event replay. Validation requires the exact terminal saved operation. Registry new freshness checks are bounded, separately journaled operations; lost replies retain original check bytes. Runtime receipt GET/readback comes before retry. Registry has only exact command POST replay, so it remains guarded. Historical reconciliation is distinct from new processing use.

## Current module contracts and evidence

`campaign_dispatch` owns pure values only; no dispatcher or new SQL yet. CompilerSelection retains original actor/attempt, preparation/proposal hashes and exact declaration/budget/Registry configuration. Stable selection ID excludes configuration and generated output. Restore checks read authority and canonical bytes; verify_origin reconstructs original policy. Pure values do not establish persisted provenance.

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
- PostgreSQL tests serial, opt-in AMPHORA_TEST_POSTGRES=1, retained fixture, no resets. Planning0012: never Planning<=0.48 migrators. Research0013: never Research<=0.33. Artifact0012: never Data<=0.25. Tighten Planning minimum after any new migration. No migration at service startup.
- Peer installations under `v2/.test-results`: Runtime `runtime-domain-receipt-peer-20261002/environment`; Registry `registry-campaign-context-independent-20261004/environment`; Data0.29 `data-processing-content-independent-20261004/environment`; Knowledge0.18 `knowledge-processing-independent-20261004/initial`; Research0.34 `research-declarations-final-independent-20261004/initial`. Append `/Scripts/python.exe`. Old harnesses may pin old versions or migrate: inspect before reuse.
- Human corrections affect future campaigns only. Never repin active inputs. Preserve weak/unknown/contradictory science; no blanket quality veto. Frozen v1/LICENSE manifest metadata debt remains unchanged. No active skills/goals/subagents.
