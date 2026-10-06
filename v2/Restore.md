# Restore

Read FIRST after compression. Refreshed 2026-10-06 03:25:12 (America/Chicago).

## Current task

Latest pushed380b7523: BP-07.05/B1.01 complete. Active B1.02a/b executable batch and immutable suite journal, uncommitted. Planning0.91 introduces planning0019 evaluation_suites; NEVER run Planning<=0.90 migrators now. Runtime0.60/runtime0028,Data0.29/artifacts0012 unchanged. Canonical trackers still child6.25%,Build8.33%,parent81.25% pending this verification.

No tests running. Batch verification42passed3.41s;137statements14branches100%;12boundaries9.73s. B1.02a/b verified; canonical child9.375%,Build12.5%,Acceptance0%,parent81.875%,16/20. Commit/push this bounded checkpoint then immediately continue B1.02c actual existing PlanningRunner.execute composition and d failure tests.

Journal persists one immutable original suite row; individual task bindings deterministically reconstruct from exact corpus/request/policy bytes; attempts remain existing ledger, no redundant mutable task table. Read uses pure _bind domain reconstruction after read_attempts permission, never synthetic grants. Source tables planning.evaluation_suites new0019. No source/test edits during verification.

Next runner: one ordinal1 call per repetition using existing PlanningRunner.execute, not run (avoids silent retries). Retain failed/missing/unknown primary observations; do not select late successful result. Need owner status-to-score projection and suite overage guard (settlements and late_observations have overage). Pure scorer currently status proposed/abstention/provider_error/invalid/unknown/authority_violation; add distinct rejected category for authoritative policy_rejected output so hard adversarial cases may expect a valid owner rejection (not false execution acceptance). No remote live calls. Persist runner report or derive read-only exact bound observations from owned journal; preserve all original identities. No SQL transaction across provider I/O. B1.02d actual SQL contention/recovery/overage proof and later process replacement needed.

B1.03 owner inspection/B1.04 Studio independent work remains before live B2 owner choices. Continue across commits/milestones until genuine need, no subagents/external JARVIS/v1 edits/SQL reset. Tests SQL serial. Preserve retained fixture files.

## Verified closeout

- Planning publication terminal race13passed299.35s;workflow58statements14branches100%,selectedmodule99%. Checkpoint_Capture_Closeout.json.
- Runtime decision read40 SQL/API/winner/resolution tests56.66s;12boundaries12.25s;schema publication verified. Existing CheckpointDecision/read permission, scoped404 for unknown/foreign/pending; no resolution on GET. Model/fallback/cancelled and proposal-only/replacement covered.
- Isolated Runtime0.60 read proof4HTTPreads/4processes of retained accepted/fallback winners. .test-results/checkpoint-decision-read-final-20261006; evidence Checkpoint_Decision_Read.json. Fresh loopback ports; first probe failed Windows immediate port reuse, preserved original failed directory. No migrations or writes or available peers. Original0.59 execution code unchanged; earlier three-owner replacement proof retained.
- Previous B3/V1 evidence Checkpoint_SQL_Races,Checkpoint_Process_Barriers,Checkpoint_Branch_Integration,Checkpoint_Isolated_Installations,Checkpoint_Installed_Replacement JSON under docs/Audits/Evidence/BP-07-Supervisor. Actual three-case installed replacement18hosts with same endpoints/config/history;0.59/0.89 two independent installs394/240 checks each.

## Next boundary

BP-07.05 Live evaluation and closeout.md B1 owns repeatable evaluation runner/semantic independent labels and Studio engagement lineage, omissions, rejection/retained outcome. B2 real model/corpus and B3 browser/provider evidence cannot be closed by fixtures. Read UI_Coding_Guidelines and interaction references before UI. UI guidelines and Development_Process activation section already reviewed; need focused existing module inspection and physical decomposition. Studio is v2/studio, not apps. No evaluation module exists yet in Planning.

## Tool and safety discipline

No subagents/external JARVIS/v1 edits/SQL resets/old migrators/external messages. SQL suites serial. No source/test/dev/README edits while tests run. Exact owned-run cleanup only. Preserve all .test-results bytes because SQL references them. Credentials env-only; never print URLs/tokens/passwords. Python v2/dev/.venv/Scripts/python.exe; set PYTHONUTF8=1 EACH shell call before scripts (PowerShell environment changes do not persist across tool calls). uv v2/.venv/Scripts/uv.exe; pytest -c v2/dev/pyproject.toml --tb=short. rg --files BEFORE unfamiliar paths; short reads; Windows absolute(), never resolve(). Check native exit codes before git.

Git prefix git -c safe.directory=//DesktopNAS/Code/mvp20-split; main remote neverhumanbot/mvp20-split. Commit/push significant verified changes then CONTINUE. No owner choice blocks present work.
