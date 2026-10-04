# Restore

## Resume here

- Refreshed 2026-10-04 10:06:27 (America/Chicago). **Read this file first after every compression**, explicitly requested by the owner. It was read on the latest compression.
- Continue authorized work across milestones, commits/pushes and compaction. No subagents, JARVIS access or v1 edits. Do not stop simply to report a checkpoint.
- **Current BP-07.02/B2.03b: Planning durable publication and owner handoff.** Owner prerequisites a.i Knowledge processing and a.ii Research registration are verified complete. Next c actual owner acceptance and accepted typed-correction replay.
- Latest pushed Knowledge checkpoint **dbb3b258**. Research0.34 checkpoint is verified and ready for final consistency review/commit/push. If already committed, inspect git log before repeating. No b implementation exists yet.
- Canonical child44.44%, Build59.26%, Acceptance0%,1/4 closed; B1=100%,B2=77.78%,B3/V1=0%. B2 .01/.02=100%,.03=33.33% (a100%,b/c0%). Parent28.89%,5/20 closed; P1=100%,P2=44.44%,others0%. MBT mirrors these values and has25 recent rows.

## Latest Research registration checkpoint

- Research0.34/publicResearch0.14 unchanged. Module declarations owns exact ResearchQuestion/EvidenceNeed registration through optional POST /v1/questions and /v1/evidence-needs. Explicit host declarations=true and separate declare_question/declare_evidence_need grants are required; default routes stay read-only. Existing exact /read routes unchanged. Registration is not scientific acceptance, source rights, method verification or campaign repinning.
- Registration revalidates incoming DTOs, enforces scope/actor/grants, composes IdentityLedger.publish_prepared with immutable first-public-registration actor/time/digest/preexisting metadata under one identity advisory lock and transaction. Existing private publish semantics preserved. Exact retries retain first public origin; preexisting private records are distinguished. No peer I/O occurs under SQL.
- **Research0013 is applied and immutable. Never run Research<=0.33 migrators on this retained database.** New0.34 installs below are the compatible replacements. Existing0001..0012 unchanged; no reset/downgrade.
- Source focused78 cases10.55s; declarations44 statements/4 branches100%. Combined ledger/declarations138 statements40 branches96.63%, with3 older defensive/optional-sample-state branches uncovered. Ruff, production boundary and506-schema checks passed.
- Final `.test-results/research-declarations-final-independent-20261004/manifest.json`:192 owner cases50.48s +190 contract cases6.29s, two isolated0.34 installs,2 actual HTTP process interruption cases. Before-commit kill rolls back; after-commit/before-reply kill preserves original actor/time on exact retry. Changed retry bytes conflict. No peer implementations installed.
- The earlier `.test-results/research-declarations-independent-20261004` ran192 passing owner cases but wrapper rejected1 skipped historical0012 backfill fixture. Final verifier explicitly excludes that unavailable pre-migration fixture rather than resetting retained state. Never call the earlier run fully passing.
- Evidence `docs/Audits/Evidence/BP-07-Extraction/Research_Declarations.json`; source-adjacent declarations/persistence/transport/service and dev READMEs updated. dev/test_scopes.json already owns the whole Research source/test tree.
- Sessions44514(final install),50811(source coverage),76169(schema) are finished. No active test/host processes remain.

## Next authorized work

1. Finish final diff/tracker review and commit/push Research registration if not yet committed, then continue.
2. Read `docs/Build Plans/BP-07/BP-07.02 Owner handoff and accepted replay.md`, b section; a is complete. Refine b into bounded publication and owner-handoff substeps before coding, preserving its existing weight. Update canonical task mirrors with each verified gate; no design credit.
3. Planning0.23 already has trace publication, immutable source/proposal binding, repair feedback values, preparation and bounded repair-chain execution. Its configured producer must still supply published diagnostics: production automatic diagnostics/candidate-answer publication and owner submissions are absent. Do not relabel fixture/manual publication as implemented orchestration.
4. Existing publication module is trace-specific with exact immutable IDs, body/ancestry and fenced events. Read its module README and targeted payload/journal/workflow before deciding narrow reuse. Preserve all old trace bytes/commands. Feedback publication profile is separately pinned; do not change the legacy schema to satisfy Data.
5. b must load exact stored task/attempt/trace/proposal facts, publish diagnostics/candidate-answer bytes through Data derived uploads with complete ancestry, declare questions before needs, submit graph changes to Knowledge, and durably bind exact owner responses. Stable identities precede external effects; no SQL spans network. Lost replies reconcile original identity, not a fresh submission. Earlier useful items survive unrelated failure.
6. c later exercises actual Data/Research/Knowledge acceptance, receipt binding and accepted typed-correction rebuild without another model call. Active campaigns never repin; scientific corrections apply to future campaigns only. Weak/contradictory/unknown points remain useful; no global quality veto or human wait.
7. Closed BP-06 plans stay closed. Update MBT/child/parent/history/Restore before significant commits. Absolute local timestamps with seconds; MBT max25 rows. Live provider/model/egress/spend choices block only real calls; no owner choice blocks deterministic work.

## Prior verified foundations

- Knowledge0.18 uses Data /processing-content for new validation, reasoning and publication review, with no /content fallback. Historical terminal decisions and accepted-log reconstruction remain stable. Source42 validation cases, two isolated builds325 cases plus actual three-owner acceptance including9 interruption stages. Evidence Knowledge_Processing.json; pushed dbb3b258. No Knowledge migration/public-schema change.
- Planning0.23/public0.7, planning0009: exact immutable preparation manifests, actual feedback/interpretation source review, shared read deadlines, pinned Knowledge/Research observations and materialized diagnostic packet binding. RepairRunner enrolls/prepares before normal reservation/issuance; issued/completed replay avoids new reads/calls. RepairChain enforces root attempt limits, retains partial work and accepts a configured producer. No automatic production publisher yet. Pushed6ee28ddc.
- Planning final installed630 cases163.34s,28 process stages; actual Data7 Planning workers/2 Data hosts. Combined Data repair fixture uses scripted Knowledge; earlier actual Knowledge/Research read proofs remain separate. Evidence Repair_Workflow.json.
- Legacy feedback-v1.schema.json digest e4cda60bdfb4da8b841d983d9764d374f4972eaa7cab52b823589c50d7acc3e9 is unchanged. Added feedback-publication-v1.schema.json omits only root $id rejected by Data0.29 and uses distinct planning.repair-feedback-publication-content/v1. No broader Data validator change.
- **Never run Planning<=0.22 migrators/writers on the preparation workflow; never Data<=0.25 migrators on artifact0012.** All retained migrations forward-only.

## Environment and installations

- Workspace Z:\mvp20-split; active v2. PowerShell, America/Chicago. Git `git -c safe.directory=//DesktopNAS/Code/mvp20-split`; main; remote https://github.com/neverhumanbot/mvp20-split.git. Commit/push authorization persists.
- Set PYTHONUTF8=1. Python v2/dev/.venv/Scripts/python.exe; uv v2/.venv/Scripts/uv.exe. Sync dev without --extra test (extra does not exist). pytest -c v2/dev/pyproject.toml --tb=short.
- PostgreSQL suites run serially with AMPHORA_TEST_POSTGRES=1. Never reset/downgrade/delete retained fixtures. Secrets stay environment-only. dev/postgres_fixture.py supplies retained owned state and scoped roles. Coverage files under .test-results.
- Tests use importlib mode, no __init__.py in behavioral folders. Use .absolute(), not .resolve(), on mapped drive. rg --files first; no Windows wildcard operands. Give large parametrized payload cases explicit short ids to avoid Windows temp-path failure/log blowup.
- **Research0.34:** .test-results/research-declarations-final-independent-20261004/{initial,replacement}/Scripts/python.exe. Previous research-views-http-20261003 is0.33 and must not run migrations again.
- Knowledge0.18: .test-results/knowledge-processing-independent-20261004/{initial,replacement}/Scripts/python.exe.
- Planning0.23: .test-results/planning-repair-workflow-final-independent-20261004/{initial,replacement}/Scripts/python.exe.
- Data0.29: .test-results/data-processing-content-independent-20261004/environment/Scripts/python.exe.
- Runtime0.20.2: .test-results/runtime-domain-receipt-peer-20261002/environment/Scripts/python.exe.
- Old verify_planning_knowledge/research helpers pinPlanning0.20; verify_planning_publication pins0.15. Update before reuse. verify_knowledge_processing.py pinsResearch0.33; its acceptance helper runs Research migrations, so update to0.34 before rerunning on0013. Keep old evidence historically accurate.
- Qdrant1.19.1 retained fixtures contain keys in ignored .test-results JSON. Never dump/reset/restart them during other suites. No goal, skill or subagents active. v1 LICENSE debt remains unchanged.
