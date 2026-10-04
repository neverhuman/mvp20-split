# Restore

## Resume here

- Refreshed 2026-10-04 11:21:46 (America/Chicago). **Read this file first after every compression**, explicitly requested by the owner.
- Continue authorized work across milestones, commits/pushes and compaction. No subagents, JARVIS access or v1 edits. No milestone-only final pauses.
- **Current BP-07.02/B2.03b.ii.c: concrete diagnostic producer and actual Data integration.** Next b.iii owner handoff. c combined owner acceptance/rebuild follows b.
- Latest pushed Planning0.26 workflow checkpoint **e717e9a3**; earlier storage f6b14ef4 and values f9521f97.
- Child45.99%,Build61.32%,Acceptance0%,1/4 closed; B1=100%,B2=83.95%,B3/V1=0%. B2 .01/.02=100%,.03=51.85% (a100%,b55.56%,c0%; b i100%,ii66.67%,iii0%; b.ii a/b100%,c0%). Parent29.20%,5/20 closed; P1=100%,P2=45.99%,others0%. Canonical tracker/parent/MBT/history are updated; MBT25 recent rows.

## Latest SDK workflow checkpoint

- Verified 2026-10-04 11:19:18. Planning0.26/public0.7, planning0010 unchanged.39 focused cases243.14s; result workflow39 statements4 branches100%; combined driver/trace/result104 statements24 branches96.88%. Driver transition ceiling/loop edge and one trace-wrapper defensive line remain uncovered.
- Final .test-results/planning-result-workflow-independent-20261004/manifest.json:705 installed tests314.97s,35 process/replay stages,two installs. Session54350 finished successfully. No PostgreSQL suite running. Evidence Result_Workflow.json.
- publication/driver.py extracts the unchanged bounded upload loop. ResultPublisher registers owned selection, prepares outside SQL, reconstructs/journals exact bytes, then drives upload with DB-clock fencing. Terminal histories avoid preparation/peer calls. Scripted Data/preparer only; concrete current-rights preparer and automatic diagnostic producer remain b.ii.c.
- Three new installed result stages preserve exact payload/identity/time, recover uncertain PUT through a distinct upload and replay with zero preparation/peer calls. No actual Data or abrupt-kill claim. Trace tests protect unchanged prior behavior.
- Ruff for touched files, dependency boundaries,506 schema checks and whitespace checks pass. Explicit dev-only Ruff configuration has unrelated/different formatting rules; normal discovery is the existing project gate. Earlier broad-directory lint found a preexisting untouched payload import formatting issue; no unrelated source change.
- Canonical tracker/parent/MBT/history and module READMEs updated. Workflow committed/pushed as e717e9a3. b.ii.c concrete preparation/diagnostic producer is now active; no new code for it yet.
## Latest result-storage checkpoint

- Planning/dev0.25/public0.7. **planning0010 APPLIED and immutable; never run Planning<=0.24 migrators.** Research0013 also applied; never run Research<=0.33 migrators. No fixture reset/downgrade.
- selection/history/prepared/store/events/journal bind exact actor-owned task/observation/prior/finalized interpretation and complete result ancestry. Separate result selection/preparation/events are immutable; control holds DB-clock lease/fence/position. Existing trace-publication history is unchanged.
- PreparedResult stores exact body/manifest plus bounded review/question witnesses. Historical read-only replay verifies original owned facts, canonical hashes and ancestry without source processing or rerunning scientific validation. Data remains authoritative for future processing rights. No result network workflow or automatic diagnostic producer exists yet.
- Final source54 cases121.15s,531 statements36 branches100%. Full independent `.test-results/planning-result-storage-independent-20261004/manifest.json`:684 tests221.26s,32 process/replay stages,two isolated0.25 installs. Four new result stages: prepare, persist streaming intent/process exit without release, successor upload after lease expiry, read-only replay. Payload/identity/preparation time remain exact. Receipts are scripted; no actual Data upload or abrupt kill claim.
- Earlier storage sessions45341(independent),15458(source),94302(schema) finished; the final workflow coverage session above is now active. Earlier65245 coverage was superseded after a witness task-hash guard was added during that run; final54-case evidence covers final source.
- Evidence `docs/Audits/Evidence/BP-07-Extraction/Result_Storage.json`. Source README/persistence/service boundaries updated. dev/verify_planning.py includes0010 wheel assertion and4 result stages through tests/acceptance/result_storage_probe.py. ResearchCase test helper now takes optional scope for persistent answer fixtures.
- Ruff, dependency boundaries,506-schema and git diff whitespace checks passed before final docs. No public schema or earlier migration changes. Storage checkpoint committed/pushed asf6b14ef4; continue b.ii.b without permission.

## Latest result-payload checkpoint

- Planning/dev0.24; publicPlanning0.7 and planning0001..0009 unchanged. New result_publication values prepare exact feedback and candidate-answer bytes from observed task/trace/source/finalized-interpretation facts. Complete ancestry includes all interpretation inputs plus the interpretation Artifact; no truncation above128 inputs or256KiB body.
- AnswerRecord is proposal_only/quotation_and_structure_only. Feedback body/profile remains diagnostic_only. New LF-pinned candidate-answer-v1.schema.json has distinct planning.candidate-answer-content/v1 identity; installed Data0.29 JsonSchemaRule accepted it. All506 public schema exports unchanged.
- ResultIdentity stable slot hashes actor/trace/kind/local key; changing payload or publisher configuration changes immutable identity but retains slot, requiring later journal conflict. Read-only restore does not require a write grant. Existing pure PublicationAttempt checks work with the compatible interface; trace bytes/commands/events unchanged.
- 24 focused tests19.44s,134 statements6 branches100%. Full independent .test-results/planning-result-payloads-independent-20261004/manifest.json passes654 tests172.00s and28 process/replay stages across two installs. Earlier sessions94015 and52284 finished. Evidence Result_Payloads.json.
- Pure values do not prove owned origin/current rights or implement durable upload/automatic diagnostics. b.ii storage is in flight; see current block above for source tests, applied0010 and active independent verifier. Module README states this boundary. dev/verify_planning.py now checks the new packaged schema and installs jsonschema only as test tooling.

## Latest Research registration checkpoint

- Research0.34/publicResearch0.14 unchanged. Module declarations owns exact ResearchQuestion/EvidenceNeed registration through optional POST /v1/questions and /v1/evidence-needs. Explicit host declarations=true and separate declare_question/declare_evidence_need grants are required; default routes stay read-only. Existing exact /read routes unchanged. Registration is not scientific acceptance, source rights, method verification or campaign repinning.
- Registration revalidates incoming DTOs, enforces scope/actor/grants, composes IdentityLedger.publish_prepared with immutable first-public-registration actor/time/digest/preexisting metadata under one identity advisory lock and transaction. Existing private publish semantics preserved. Exact retries retain first public origin; preexisting private records are distinguished. No peer I/O occurs under SQL.
- **Research0013 is applied and immutable. Never run Research<=0.33 migrators on this retained database.** New0.34 installs below are the compatible replacements. Existing0001..0012 unchanged; no reset/downgrade.
- Source focused78 cases10.55s; declarations44 statements/4 branches100%. Combined ledger/declarations138 statements40 branches96.63%, with3 older defensive/optional-sample-state branches uncovered. Ruff, production boundary and506-schema checks passed.
- Final `.test-results/research-declarations-final-independent-20261004/manifest.json`:192 owner cases50.48s +190 contract cases6.29s, two isolated0.34 installs,2 actual HTTP process interruption cases. Before-commit kill rolls back; after-commit/before-reply kill preserves original actor/time on exact retry. Changed retry bytes conflict. No peer implementations installed.
- The earlier `.test-results/research-declarations-independent-20261004` ran192 passing owner cases but wrapper rejected1 skipped historical0012 backfill fixture. Final verifier explicitly excludes that unavailable pre-migration fixture rather than resetting retained state. Never call the earlier run fully passing.
- Evidence `docs/Audits/Evidence/BP-07-Extraction/Research_Declarations.json`; source-adjacent declarations/persistence/transport/service and dev READMEs updated. dev/test_scopes.json already owns the whole Research source/test tree.
- Earlier sessions44514(final install),50811(source coverage),76169(schema) finished.

## Next authorized work

1. Workflow0.26 committed/pushed as e717e9a3. Continue b.ii.c concrete preparation/diagnostic producer and actual Data proof.
2. Read result_publication README and BP-07.02 Result publication.md. Add concrete ResultPreparer using SourceReviewer and ArtifactReview with one shared ReadBudget outside SQL; verify interpretation body equals owned trace. Exact selected Research QuestionReader inputs for answers; gaps withhold only dependent answers.
3. Derive diagnostic decisions from owned task/observation/trace and configured validators. RepairFeedback.create binds diagnostics to exact history. Do not accept caller acceptance or arbitrary feedback as authoritative producer input. Persist the first diagnostic snapshot; one immutable diagnostics slot per parent. Later model output creates a new trace.
4. Connect actual interpretation/result publication to RepairChain producer.next(step), yielding RepairInputs or a bounded no-repair/unavailable result. Preserve root attempt and aggregate budget limits, prior useful output, abstention/policy stops and future-campaign-only corrections.
5. Prove real installed Data profile/ancestry/current-process-rights denial/regrant and restart behavior. dev/planning_publication_fixture.py and verify_planning_repair_data.py are useful patterns but pin old Planning: update before use. Never run an old migrator.
6. b.iii adds durable Research/Knowledge submissions and receipt binding. c proves combined actual-owner acceptance and typed-correction replay. No cross-owner SQL/private imports. Actual provider choices block only live calls.
7. Keep canonical trackers/MBT/history/Restore current. No milestone pause or new permission needed for authorized deterministic work.
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
- Latest verified Planning0.26: .test-results/planning-result-workflow-independent-20261004/{initial,replacement}/Scripts/python.exe.
- Prior compatible Planning0.25: .test-results/planning-result-storage-independent-20261004/{initial,replacement}/Scripts/python.exe.
- Prior verified Planning0.24 (must not migrate0010): .test-results/planning-result-payloads-independent-20261004/{initial,replacement}/Scripts/python.exe. Prior0.23 final repair installs remain retained.
- Data0.29: .test-results/data-processing-content-independent-20261004/environment/Scripts/python.exe.
- Runtime0.20.2: .test-results/runtime-domain-receipt-peer-20261002/environment/Scripts/python.exe.
- Old verify_planning_knowledge/research helpers pinPlanning0.20; verify_planning_publication pins0.15. Update before reuse. verify_knowledge_processing.py pinsResearch0.33; its acceptance helper runs Research migrations, so update to0.34 before rerunning on0013. Keep old evidence historically accurate.
- Qdrant1.19.1 retained fixtures contain keys in ignored .test-results JSON. Never dump/reset/restart them during other suites. No goal, skill or subagents active. v1 LICENSE debt remains unchanged.
