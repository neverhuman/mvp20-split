# Restore

Read FIRST after compression. Refreshed 2026-10-06 03:25:12 (America/Chicago).

## Current task

Refreshed 2026-10-06 04:04:54. Latest pushed8612050e (evaluation runner). B1.03a public inspection contracts verified, UNCOMMITTED. No tests running.124 contract/boundary tests20.40s;ruff fixed __all__ sorting then passed;schema publication --check verified556schemas with548predecessor bytes preserved. Public supervision0.10;Runtime0.61/Planning0.93 dependency updates only. runtime0028/planning0019/Data0.29/artifacts0012 unchanged. NEVER Planning<=0.90 or old Runtime migrators.

Current canonical BP-07.05/B1.03b owned read projection/consistency. a100%,b/c/d0%;B1.03=25%,B1=56.25%,child14.0625%,Build18.75%,Acceptance0%,parent82.8125%,16/20. Finish diff/commit/push contract checkpoint then implement b,cHTTP,dinstalledproof; afterward B1.04 Studio. Live choices only block B2. No owner input needed yet; do not end turn at milestone.

New physical companion BP-07.05 Inspection boundary.md defines exact routes/consistency. Public inspection.py exports CheckpointInspectionPage,CheckpointRequestPage,CheckpointContextPage,CheckpointResponsePage (max10items), SupervisionInspectionCut(GraphReadCut,epoch,snapshot_token), item records. Model includes compact attempts, reportstop/disposition, explicit included/omittedmetadata and response selected_by_winner. Four literal fixtures +26 tests; predecessor pins inspection_predecessor_schema_pins.json. export_schemas has fournewroots. No SQL/HTTP inspection implementation yet.

Implementation plan: Runtime-owned supervision_inspection module using existing RuntimeHistory(engine,cursors), read-only repeatable-read transactions and public DTOs mapped from owned domain objects. Reuse HMAC CursorCodec configuredkey; install paged routes only when supervision AND history configured. Existing exact decision GET stays unchanged. Snapshot epoch hashes runrevision plus counts of append-only checkpoints,requests,responses,executionreports,requestdispositions,winners; responses can arrive without run revision changing, so graph cut alone insufficient. Snapshot token mode/resource binds run,after=(0,0,epoch); page cursor mode binds resource/offset viaafter=(offset,0,epoch). CursorCodec.decode requires after tuple(int,int,str), supports filter/mode/scope/resource/expiry. New relevant append or run revision -> InspectionError('snapshot_unavailable')409; no mixed-snapshot success. Query state and row selections same repeatable-read transaction. No source/prompt/capture bytes or peer I/O.

Routes under /v1/supervision/runs/{run}/checkpoints: rootlist; /{decision}/requests; /{decision}/requests/{sha}/context; /{decision}/requests/{sha}/responses. Dependent reads require snapshot token, pagecursoroptional,limit1..10. Reconstruct original StoredRequest.from_row(SELECT...), StoredReport.from_row/ReportJournal.load, StoredCheckpoint.from_row(row,policy), WinnerStore.load(conn,params,slot), responses StoredResponse. RequestDisposition kindrepair/fallback privateDTO; project onlykind/reason with restoredbinding. Prefer short source reads. ContextManifest entries/omissions eachmax128; artifact refs only. Planning public exact original request/report reads already exist, but new projection uses Runtime-retained evidence only and must say missing report is unobserved, not no call occurred.

Prior runner all97checks61.02s, realSQL/process unknown/late/overage; evidence Execution_Recovery.json. No live efficacy. Test scopes owned; no source/test/dev/README edits duringverification. Git main safe.directory prefix below. No subagents/JARVIS/v1 edits/SQL resets. Preserve .test-results. PYTHONUTF8=1 EVERY shell; stop native failures explicitly before dependent commands. rg --files before unfamiliarpaths; avoid fullone-lineJSON/truncated dumps.

## Verified closeout

- Planning publication terminal race13passed299.35s;workflow58statements14branches100%,selectedmodule99%. Checkpoint_Capture_Closeout.json.
- Runtime decision read40 SQL/API/winner/resolution tests56.66s;12boundaries12.25s;schema publication verified. Existing CheckpointDecision/read permission, scoped404 for unknown/foreign/pending; no resolution on GET. Model/fallback/cancelled and proposal-only/replacement covered.
- Isolated Runtime0.60 read proof4HTTPreads/4processes of retained accepted/fallback winners. .test-results/checkpoint-decision-read-final-20261006; evidence Checkpoint_Decision_Read.json. Fresh loopback ports; first probe failed Windows immediate port reuse, preserved original failed directory. No migrations or writes or available peers. Original0.59 execution code unchanged; earlier three-owner replacement proof retained.
- Previous B3/V1 evidence Checkpoint_SQL_Races,Checkpoint_Process_Barriers,Checkpoint_Branch_Integration,Checkpoint_Isolated_Installations,Checkpoint_Installed_Replacement JSON under docs/Audits/Evidence/BP-07-Supervisor. Actual three-case installed replacement18hosts with same endpoints/config/history;0.59/0.89 two independent installs394/240 checks each.

## Tool and safety discipline

No subagents/external JARVIS/v1 edits/SQL resets/old migrators/external messages. SQL suites serial. No source/test/dev/README edits while tests run. Exact owned-run cleanup only. Preserve all .test-results bytes because SQL references them. Credentials env-only; never print URLs/tokens/passwords. Python v2/dev/.venv/Scripts/python.exe; set PYTHONUTF8=1 EACH shell call before scripts (PowerShell environment changes do not persist across tool calls). uv v2/.venv/Scripts/uv.exe; pytest -c v2/dev/pyproject.toml --tb=short. rg --files BEFORE unfamiliar paths; short reads; Windows absolute(), never resolve(). Check native exit codes before git.

Git prefix git -c safe.directory=//DesktopNAS/Code/mvp20-split; main remote neverhumanbot/mvp20-split. Commit/push significant verified changes then CONTINUE. No owner choice blocks present work.
