# Restore

Refreshed `2026-10-05 16:20:12` (America/Chicago). **Read first after compression.**

## Resume

B1.04d.i independentinstallations verified, ready to commit/push. Latestpush92fd5209(Planningclient),bd110e74(Runtimeclient),50613481(RuntimeHTTP),3b127838(capture/cancel),f37c3a67(PlanningHTTP). Runtime0.29/runtime0020,Planning0.72/planning0015 installed. No verification/hosts running.

Current d.ii actual installed Planning/Runtime/Data exchange, commit-before-dropreply, restart/replacement andrights/history proof. d.i100%,ii0%;B1.04=87.50%,a/b/c100%,d50%;B1=96.88%,Build32.29%,child24.22%,parent64.84%,12/20;Acceptance0%. Trackers/history/devREADME/evidence synced. Commit/push then implement d.ii.

New dev/verify_supervision_installations.py passed .test-results/supervision-owners-installed-20261005-verified/manifest.json: Runtime161cases ineachinitial/replacement,Planning75ineach;472total;38Runtime+28Planning historical migrationfilesunchanged;528schemas/520priorpins. First run allcasespassed butflatglob schemafailure;fixedrglob(relativepaths/excludemanifests),fullrerunpassed. Do notrerun unnecessarily. Both currentowners installedprivatepeersabsent; copiedtestrootunderoutput/root,productionwheels. No SQL/migration.

## d.ii implementation preparation

Read Public transports.md latest actualownerstages. Need newdevharness + owned Runtime/Planning processprobes, actualData0.29 CLI available. InitialRuntimeownedprobe can use tests/supervision_journal/test_storage.setup(graph_env), actualSQL with module-localfixture_env (like oldprocess_worker.py butnewversion);prepareoriginalrequest+outbox thenemitframe/outgoing/capture asbase64 in scopedignoredstatefile. Oldworker hardpins0.26;do notreuseunmodified. Testfixtures copiedonly,productioninstalled. OwnRuntimeSQLenvonly,PlanningSQLenvonly;orchestrator neverimportspeerprivatecode.

Runtimeinstalled PlanningClient sendsoriginaloutgoing throughdrop-after-owner-commit proxy -> recordsunknownDeliveryJournal event. Replacementprocess originalreceipt+readback -> actualPlanningreceipt recordedindeliveryhistory. ActualPlanningCLI usesmodule amphora_agent_planning.supervision_api --port (no serve/config flags): env AMPHORA_PLANNING_DATABASE_URL and AMPHORA_PLANNING_SUPERVISION_CREDENTIALS JSONlist token/actor_id/scope/actions. Configure originalrequestPlanningactor. Intakenoattempts/modelcalls.

Publishsyntheticcapture viaactualData upload/finalize (profilefixture.text/hash1*64/jsonfrompublicresponsefixture acceptedasconfiguredobjectprofile), attachsource via rightsgrant + /acquisition/prepare using utf8_document. ActualArtifactRef replacesfixturecapture ref beforefinalincomingcommandparse. RuntimeHost can usefixturecatalog (prepared-run.payload recursivelyrescope) + supervision:{capture_data:{endpoint,token_env}}, Planningactorgrantsread/supervise_respond/supervise_cancel. GraphrequestalreadyretainedSQLfromRuntimeprobe; nohostgraphconfigneededforrecording. DataRuntimecredentialreadonlyscope;separatefixturecredentialupload/finalize/read/acquire/source_history/manage_source_rights. NoQdrantneeded.

Planninginstalled RuntimeClient sendsresponse throughcommittedreplydrop proxy, observesunknown thenoriginalreceipt/readback. Also cancellationhistory (noeffect). Restartinitialhostswithreplacementinterpreters andcompareoriginalreceipts/committimestamps/capturebytes fromowner-localreaders. Data rights revision2grantedread-only shouldblockfreshprocessing but allowhistoricalreceipt/readback; originalresponsePOST recoversbeforefetch, newresponseID/commanddenied. Regrantrevision3 permitsfreshexplicitresponse. Scopedcleanup cancelsownrun only, retainsSQL/files, shutsownedhosts/proxies. Clearlysynthetic/noactualprovider/winner/scienceclaim. Existing campaign_context_fixture.support.Owner canserveRuntime/Data,notPlanning; ownnewhostadapterorlocalhelper needed. Itshelperslogonlylocal,envcredentials.

Currentclients separate submit(command,window,guard), receipt(command,window,previous=None), readback(command,observation,window); noauto retry. RuntimePlanningClientonlyrequest;PlanningRuntimeClientrespond/cancel. ExchangeWindow10s/3calls/524288bytes/perresponse256KiB. PlanningRecordingObservation andRuntimeSupervisionReceiptObservation bindoriginalidentity/hash/operation/commit/readback. Guardbeforeconnect/beforesend.

RuntimeAPI POST /v1/supervision/responses,/cancellations; append/receipts/query;GET responses/{id},cancellations/{id};supervision/ready. PlanningAPI POST requests,/v1/supervision/receipts/query;GET requests/{engagement}. RuntimeoriginalreceiptinclpendingbytescheckedbeforefreshDatafetch; noSQLspansnetwork. CaptureReader exactmetadata+/processing-content2GETs10s;CancellationJournal16immutableoriginalactorrecords, noexecutioneffect.

## Persistent rules

Continue across milestones/commits/pushes/compaction until a concrete blocker; never end at a clean checkpoint. Read Restore FIRST after compression. No subagents/JARVIS/v1 edits. Commentary at least every60s. No source/test/dev/source-adjacentREADME edits during verification. Retained SQL serial opt-in, no reset/old migrators. Future-only receipt corrections; weak science explicit, no blanket quality veto. Unselected live provider/model/egress/spend blocks only real calls. No active goals or skills.

Workspace Z:/mvp20-split;activev2;PowerShell;America/Chicago. PYTHONUTF8=1 EACH Python shell invocation. Python v2/dev/.venv/Scripts/python.exe;uv v2/.venv/Scripts/uv.exe. Windows absolute(),notresolve(). Normal Ruff. Secrets env only; never print URLs/tokens. Git -c safe.directory=//DesktopNAS/Code/mvp20-split;main;commit/push authorized. Trackers: child BP-07/BP-07.04 Durable supervisor and races.md, parent BP-07 Autonomous LLM Campaign Supervision.md, MBT(max25rows), BP-07 Planning History.md. Percentages reflect bounded tasks, no design credit. Completed BP-07.01/.02/.03 stayclosed.

Current owner heads: Runtime0.29/runtime0020 (NEVER<=0.26 migrators); Planning0.72/planning0015 (NEVER<=0.69);Data0.29/artifacts0012(NEVER<=0.25);Research0.34/0013(NEVER<=0.33);Knowledge0.18;Registry0.1. Public supervision0.2,Planning0.9,GraphRuntime0.13;528schemas. Existing v1/LICENSE metadata debt untouched.

## Architecture and evidence pointers

B1.03 journal design/moduleREADME owns exact immutableRequestFrame/RequestSeries (16requestmax), actual plan/path/ancestor/no-materialization checks, prepare+outbox atomic, delivery leases1..300s DBclock capped originaldeadline,16claims/64events, explicitunknown/pending/recorded history. ResponseJournal stores64response records/request, exactcapture<=64KiB+publicrecordedreceipt atomic. Late/history reads retained. CancellationJournal16records separatefromwinner. B1.03 independentproof17processes/4abruptkills/3races passed; old helper hardpinsRuntime0.26,DO NOT run its migrator now. Details/evidence docs/Audits/Evidence/BP-07-Supervisor/ and tests/supervision_journal/process_worker.py.

B2 must pin graph-specific supervisionpolicy beforeinitial readyInvoke materialization, pause only targets, retain independentbranch progress, use immutable effective-input overrides, and atomically choose model/fallback/cancel winner+effect/audit/outbox. No rewriting plans/issuedinputs/topology or in-campaign humanapproval. Futuretopology remains retained futurecampaign draft. Runtime owns execution; Planning owns context/providerissuance/conservativeaccounting. Actual autonomousloopB2.03; race/accountingB3; final independentauditV1. No auto-provider call from current HTTP. Private declarationv2 correction alreadyapproved/implemented.

Old independent installations (read-only/no oldmigration): runtime-domain-receipt-peer-20261002/environment0.20.2;supervision-journal-independent-20261005/initial/environment0.26;planning-campaign-final-20261005/initial/environment0.69;data-processing-content-independent-20261004/environment0.29. Paths relativev2/.test-results, appendScripts/python.exe. Current new owner installations liveunder supervision-owners-installed-20261005-verified/{runtime,planning}/{initial,replacement}; onlytrust after manifestpassed. First failed inventory-only run without-verified retained. No SQL in installationhelper.
