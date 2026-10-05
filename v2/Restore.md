# Restore

Refreshed `2026-10-05 15:53:34` (America/Chicago). **Read first after compression.**

## Resume

B1.04b.ii verified, ready to commit/push. Lastpushf37c3a67 PlanningHTTP. Runtime0.27 installed/runtime0020 applied; NEVER Runtime<=0.26 migrators. Planning0.71/planning0015; NEVER Planning<=0.69 migrators. Public528schemas unchanged.96 capture/journal/persistence cases24.31s,12 boundary11.38s;Ruffpassed;coverage reader93%,cancellation100%,combined96%. No tests/hosts running.

Current B1.04b.iii Runtime HTTP integration. Child21.35%,Build28.47%,Acceptance0%;parent64.27%,12/20. B1=85.42%;B1.04=41.67%,a100%,b66.67%(i/ii100%,iii0%),c/d0%. Trackers/history/READMEs/evidence synced. Commit/push then continue; no owner decision needed.

New supervision_capture CaptureReader exact metadata+/processing-content, configuredloopback2calls/327680bytes/10s, tokenenv,no redirects/retries. None diagnostic nofetch. New supervision_journal CancellationJournal immutable16records/request;supervise_cancel + originalpreparingRuntime/originalPlanningactor;exactrequest;atomicreceipt;readhistory;noexecutionwinner. Migration0020 immutableSELECT/INSERT+FKs. Tests realHTTPprotocolpeers andactualSQL. b.iii must recoveroriginalstoredreceipt before newDatafetch, validateactor/scope/originalrequest beforefetch, integratefocusedroutes into existing api.py and explicit Host configuration. Host in hosting.py; newoptional supervision config can configureDataReader;RequestJournal(engine,{}) sufficient forrecord/readonly routes, requestproducerconfigB2. Noauto modelcalls.

Planning supervision_api HTTP verified39cases19.56s +12boundary;separateCLIactualHTTP host passed. LatestPlanning0.71;publicsupervision0.2. Source/testREADME captures APIboundaries.

## Prior journal evidence (versions above supersede older ones)

## Current module boundary

Runtime supervision_journal owns immutable frames/series, RequestJournal actualSQL prepare/read, DeliveryJournal leases/events, ResponseJournal exact capture/recorded receipts. Source README defines rebuild/API/side-effects/limits. Frame original observations strictbase64/canonicalJSON; bounded16request lineage and nonwideningcontext/calllimits/deadline. Plan/actualnode/path/kind/scope/ancestor/scattermembership/loopiteration rederived under runlock; absence of materialized target required. Globalunrelatedrevision alone notstale. Initialadmission stillissuesreadyroots; B2 mustintercept beforematerialization.

runtime0018 adds immutable requests/outbox;0019 adds lazydeliverycontrol and immutabledeliveryevents/responses. Both preserveoldmigrationbytes. Prepare configured Runtime->Planning actor mapping; supervise_prepare/read rights. Delivery supervise_dispatch,1..300s DBclockcappeddeadline; originalclaimID retries originalexpiry/fence,newIDneededreacquire.16claims/64events; terminal receipt/readback retainsowneroperation. Response supervise_respond originalPlanningactor; exactrequest/attempt/capture;64records/request; atomicresponse+publicrecordedreceipt with private CommandStore accepted-storage status. Latehistoryreadable withoutfreshprocessingpermission. No modelcall, graphdecisionwinner, cancellationwinner or HTTPtransport implemented by these modules.

B1.03a122combined5.22s,105statements12branches100%;b53journal/migration9.96s,14SQL,236statements28branches100%;c65journal/migration20.50s,26SQL,486statements60branches99%. Onlyreserved64th-eventfallback unexecuted; normal16claim limitverified. Boundary12passed8.54s. Initialfixturealreadyissued revisedvalidbranchgraph; parentActivationPath.schema_version omission fixed withrealnestedtests; eventclosure reason-variable error fixed. No unresolved failures.

## Independent recovery evidence

New dev/verify_supervision_journal.py and tests/supervision_journal/process_worker.py. Output .test-results/supervision-journal-independent-20261005. TwoisolatedRuntime0.26/publicclosure installs,privatepeersabsent. Workerpytest --confcutdir=<copiedjournaltests> avoidsparentdevfixtures; modulefixtureenvSQLonly. Copiesownedtestfiles/publicfixtures,notproduction source. Predecessorcompare162files fromoldRuntime0.20.2; neverrunsoldmigrator. dhelper passedfirst run afterRuff fixes.

17processes: initialize; killpreparebeforecommit(exit91); inspectempty;2rootpreparebarrierworkers(exactoriginaltimestamps);changedretryreject;2successorbarrierworkers(onewinner/oneconflict);2leasebarrierworkers(onelease);killafterclaim(exit93);replacementexpiry/reacquire/staleholderreject;killresponsebeforecommit(exit94);inspectpending;killresponseaftercommit(exit95);replacementexactreceipt/capture/timestamp;cleanupownuniquescope. OutgoingPlanningreceipt isdeterministicpublicfixture,noactualPlanningHTTPorpaidprovider claim. Allprocesses ended; cleanup retainedhistory,cancelledownrunonly.

## Next B1.04

Read physical/exchange design then owning modules. Public wire families planning.supervision.request, runtime.supervision.respond, runtime.supervision.cancel, publicreceipt pending/rejected/recorded, decisionreadbackshape. Planning ownsoriginalcontext/task/attempts/accounting; Runtime aloneowns actualwinner/effects. No dependencycycle: publicsupervision importsPlanning+GraphRuntime;GraphRuntime neverimportsPlanning. No liveproviderselection needed for deterministicHTTP. Preserve closedcontracts/migrations; forwardversions forchanges.

Known locations: Runtime api.py (not api/app.py), __main__.py; create_app currently(admission,credentials,completion,history,graphs,authoring,universes), boundedbodymiddleware262KiB/time10/depth64. Extend viafocused ownedroute module,avoidcatchall. Planning currently has NO publicserver/liveadapter. Planning orchestration PlanningRunner combinescontext/budget/issuance/provider/settlement, no networkadapter or Runtimeacceptance. persistence README/RequestSnapshot/PlanningJournal own originalactor/context/replay; DispatchJournal owns once-onlycallticket andconservativeunknown/lateusage. Existing runtime responsehistory suitableforAPI but actualcapture bytes needauthenticatedbounded Data retrieval or explicitownedtransfer. CancellationDTO exists butnoownedcancellationjournal/winner yet; defineboundedtransportmilestones beforecoding, nofakeendpointsuccess. Readactualmodulecontractsfirst, then targetedcode. Architecturally B2 needsadmissionpinnedsupervisorpolicy/checkpoint before readyInvoke materialization, targetonlypausing, immutableeffectiveinputs, atomic model/fallback/cancelwinner and audit. B2.03 actualautonomousloop; B3races;V1audit.

## Persistent rules and environment

Continue milestones/commits/pushes/compaction until concreteblocker. No subagents/JARVIS/v1edits. Commentaryevery60s. No source/test/dev/source-adjacentREADME editsduringverification. SQL serial opt-in retainedfixture,noreset/oldmigrators. Future-onlyreceiptcorrections,noactive repinning. Weakscienceexplicit,noblanketqualityveto. Liveprovider/model/egress/spend unselectedblocksonlyactualcalls. Private declarationv2 correction alreadyowner-approved/implemented.

Workspace Z:/mvp20-split;activev2,PowerShell,America/Chicago. Python v2/dev/.venv/Scripts/python.exe;uv v2/.venv/Scripts/uv.exe. PYTHONUTF8=1 EACH shellPythoncall. Windows absolute(),notresolve(). NormalRuff. Secretsenvonly;neverprintURLs/tokens. Git -c safe.directory=//DesktopNAS/Code/mvp20-split;main;commitpushauthorized. Primarydocs docs/Build Plans/BP-07/BP-07.04 Durable supervisor and races.md;parent BP-07 Autonomous LLM Campaign Supervision.md;MBTmax25rows;BP-07 Planning History.md. Stablephysical/exchange designs hadstale0%labels corrected tocanonicaltrackerreference,notextraimplementationcredit.

Planning0.70/public0.9/DB0015(never<=0.69migrators),Research0.34/public0.14/DB0013(never<=0.33),Data0.29/DB0012(never<=0.25),Knowledge0.18/public0.8,Registry0.1. No activegoals/skills/subagents/hosts. v1/LICENSE metadata debtuntouched. BP07.03Final_Installation.json1262initial/49replacement; actualowner/crash/rights/compiler/semantic/catalogevidence retainedunderBP-07-Campaigns. New supervisorproofunderBP-07-Supervisor. Olderhelperversionsmaymigrate;inspectbeforeuse.


B1.04a design: new Planning supervision_intake, publicsupervision dependency, RequestSnapshot/ContextPolicy existingactor/context rules. PlanningPrincipal already onlyrecord_requests/record_attempts/read_attempts; use first+last grants,no arbitrarynewgrant. Intake originalsupervisorwrapper+canonicalcommand+Planning.requests registration+publicrecordedreceipt atomic undercommand-key thenexistingPlanningJournal._lock; onlyownSQL. Runtime snapshot hashes opaque ownerclaims,shapechecked nofakeactualRuntimeproof. Out-of-order/late wrappers mayberecorded butnotcalled/enrolled. NewPlanning0.70/planning0015,keepallpriorbytes; noHTTPuntilb. See Public transports.md. Runtimeexisting ArtifactProjections.fetch uses /content andparsedJSON, unsuitablefornewcapture; mustuseData /processing-content raw exact bytes outsideSQL. Planning hasprivate DataReader /processing-content, cannotimportacrossservice; buildRuntime-ownedboundedreader orreviewSDKcapability. No sourcewrites/verification running.
