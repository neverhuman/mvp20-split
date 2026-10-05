# Restore

## Resume here

- Refreshed 2026-10-04 20:40:53 (America/Chicago). Read FIRST after compression. Continue across gates/commits; no subagents, JARVIS or v1 edits.
- Current BP-07.03/B1.04c provider/durable integration. b verified ready to commit/push. Latest pushed05fb6508. No tests/hosts running.
- Planning0.51/public0.9;510 schemas unchanged. Parser73 focused4.17s,97 statements16 branches100%;867 isolated tests59.075s. Manifest .test-results/planning-campaign-parser-independent-20261004/manifest.json. Evidence Campaign_Output_Parser.json.
- Child21.88%,Build29.17%,Acceptance0%,parent44.38%;0/4 and8/20 closed. B1.04 a/b100%,c/d0%;B1.04=50%,B1=87.5%.
- RetainedPG planning0012; NEVER Planning<=0.48 migrators. Research0013/Data0012; neverResearch<=0.33/Data<=0.25 migrators. No reset/history rewrite.

## Immediate next actions

1. Commit/push b; c integrate exact campaign_draft_schema into providers/profiles.py supported/observation_model/parse, delegating CampaignOutput.parse(raw,attempt.request).proposal(). Keep draft_model/attributed_items extraction-only. Existing capture.py maps policy errors using small legacy set; add named campaign purpose/profile/digest/scope/cut policy cases without changing old behavior. Closed exact profile; TaskProviderObservation v2/TypedProposal v1 unchanged.
2. providers/wire.py already decodes observation v1/v2; persistence/records.py verified_observation reconstructs raw through OutputProfiles.parse before equality, so no SQL migration needed. Add pure tests plus scoped SQL runner/readback/late/replay proof, retain raw bytes, preserve unknown charging and failure statuses. Existing tests/providers/test_task_output.py Response and tests/persistence/test_task_output.py patterns; SQL stored fixture in tests/conftest.py uses current migration0012, opt in AMPHORA_TEST_POSTGRES=1.
3. Do NOT change FixtureProvider reference behavior. New deterministic campaign response fixture can be test-owned; actual adapter/live provider later. No scientific or execution claim. Campaign preparation before dispatch integration belongs B2/BP07.04; this step is typed output through existing capture/journal only.
4. New module campaign_output exports CampaignDecisionScope/CampaignCandidate/CampaignOutput; service tests/campaign_output/test_output.py provides output()/request() helpers and copied reviewed fixtures. Module-owned scope already covered by agent-planning in dev/test_scopes.json. verify_planning_context.py includes campaign_output pure tests. No source/test/dev edits during verification.
5. d independent installation/legacy exact compatibility next; then B2.01 semantic policy. Existing journal/ownerpacket harnesses pinnedPlanning0.49: inspect before reuse. Root docs and previous evidence remain intact; old migrators forbidden. Update trackers/history/Restore before commit/push. Live provider choices block only actual calls; corrections future campaigns, weak science preserved.

## Latest acceptance details

- Manifest .test-results/planning-campaign-context-owners-v2-20261004/manifest.json and owner-versions.json. Registry0.1,Runtime0.20.2,Data0.29,Knowledge0.18. Ten stages original/partial/denied/foreign/original-after-correction/future-campaign/original-after-owner-restarts/processing-denied/processing-denied-after-restart/processing-restored. All hosts closed, retained stores intact.
- Initial attempt .test-results/planning-campaign-context-owners-20261004 failed fixture readiness because Knowledge hides /openapi.json. Fixed /health, Data /ready; no product defect/reset. Do not overwrite either output. New Registry isolated install .test-results/registry-campaign-context-independent-20261004/environment/Scripts/python.exe.
- Research proof from b783d7e3 reused explicitly; git diff confirms unchanged campaign_research_access/research_view_access/publicResearchcontracts. No peer implementation installed in Planning.
- Prior client checkpoint Planning0.39 isolated installation .test-results/planning-campaign-knowledge-independent-20261004/environment/Scripts/python.exe. Context installer collects642 pure/regression cases including existing extraction/proposals/knowledge. No SQL suite necessary for pure client refactor; journal work will require scoped SQL tests.

## Canonical navigation

- Child docs/Build Plans/BP-07/BP-07.03 Campaign proposals and context.md; physical design BP-07/BP-07.03 Physical design.md; activation docs/Audits/BP-07.03_Activation.md.
- Parent docs/Build Plans/BP-07 Autonomous LLM Campaign Supervision.md; history **BP-07 Planning History.md**; MBT Master Build Tracker.md. Update current prefixes before historical B1.01a evidence; never rewrite historical percentages. MBT25 newest rows; overflow to history.
- Evidence docs/Audits/Evidence/BP-07-Campaigns/: Research_Selection,Research_Context_Records,Research_Record_Reads,Research_View_Reads,Research_Owner_Reads,Registry_Discovery,Runtime_Metadata,Campaign_Artifact_Reads,Retrieval_Context JSON.
- BP-07.02 closed100% atf209a350; archived BP-07/Completed/BP-07.02 Reliable text decomposition.md; audit BP-07.02_Text_Decomposition_Closeout.md.930 installed tests/39 process stages plus explicitly reused actual-owner/crash/corpus evidence. Do not reopen. Provider/model/egress/spend unchosen, blocks **only real calls**; no owner decision blocks deterministic work.
- Human corrections affect future campaigns only; no active repinning/rebasing/invalidation. Preserve weak/contradictory/unknown science, no global veto. Scientific and target-host claims remain separately gated.

## Environment and retained evidence

- Workspace Z:\mvp20-split, active v2; PowerShell, America/Chicago. Git `git -c safe.directory=//DesktopNAS/Code/mvp20-split`; main, https://github.com/neverhumanbot/mvp20-split.git. Author/auth configured, pushes authorized.
- Python v2/dev/.venv/Scripts/python.exe; uv v2/.venv/Scripts/uv.exe. Set PYTHONUTF8=1. pytest -c v2/dev/pyproject.toml --tb=short. Normal Ruff discovery; --config changes rules. No dev --extra test.
- No source/test/dev edits while verification runs. SQL suites serial and opt in with AMPHORA_TEST_POSTGRES=1. No fixture reset/deletion/old migrators/rewriting prior evidence. Planning0012: never<=0.48 migrators; Research0013: never<=0.33; Artifact0012: never Data<=0.25.
- Tests module-owned, importlib mode, no __init__.py in behavioral test folders. Windows paths use .absolute(), not .resolve(). Use rg --files before filenames; avoid wildcard rg operands. Bounded outputs; no full generated schemas/log dumps.
- dev/verify_planning_context.py builds one fresh isolated wheel installation, clears AMPHORA/PYTHONPATH, asserts peer implementations/FastAPI absent and collects explicit pure/context/loopback suites only. No SQL/migrator; copies whole owner tests for support imports. Do not rerun full persistence suite for every pure client edit. Existing output directories rejected.
- Prior0.38 context install: .test-results/planning-retrieval-context-independent-20261004/environment/Scripts/python.exe. Prior .37 campaign-artifacts-independent, .36 runtime-metadata-independent, .35 registry-discovery-independent, .34 research-views-independent, same naming prefix planning- and suffix-20261004/environment.
- Actual Research manifest .test-results/planning-campaign-research-owner-verified-20261004/manifest.json; seven workers/two owner hosts. dev/verify_planning_campaign_research.py pins passed Planning0.34 installation; update deliberately if reusing later. New probe remains public-only; owner-local seed explicitly synthetic and no migrator.
- Research0.34 .test-results/research-declarations-final-independent-20261004/{initial,replacement}/Scripts/python.exe. Knowledge0.18 knowledge-processing-independent-20261004/{initial,replacement}; Data0.29 data-processing-content-independent-20261004/environment; Runtime0.20.2 runtime-domain-receipt-peer-20261002/environment. All paths relative to v2/.test-results unless fully prefixed.
- Full Planning0.30 replacement .test-results/planning-extraction-closeout-independent-20261004/{initial,replacement}/Scripts/python.exe. Old peer scripts may pin old versions; inspect before reuse. verify_knowledge_processing.py pins Research0.33 and migrates: never run unchanged on0013.
- No credentials in tracked logs/docs; fixture keys remain ignored/environment-only. Frozen v1 LICENSE manifest metadata debt unchanged. No skills/goals/subagents active.
