# Restore

Refreshed `2026-10-05 15:18:04` (America/Chicago). **Read first after compression.**

## Resume

BP-07.04/B1.03d VERIFIED but not yet committed. Latest pushed d4cb7dec (c); prior06fd08b0(b),0fdd811a(a). Runtime/dev0.26.0, public supervision0.2.0, GraphRuntime0.13, DB runtime0019;528 public schemas. NEVER run Runtime<=0.25 migrators on this fixture. No running verification or hosts. Independent session71479 completed successfully: two installs,111 initial scope/public cases,33pure journal cases per install,162 unchanged predecessor Runtime productionfiles,17actualSQL processes,4abruptkills,3pairedraces,scopedcleanup. Evidence Journal_Recovery.json generated. Need final diff/links/check and commit/push d, then B1.04 public owner transports. Do not end at checkpoint.

Canonical child18.75%,Build25%,Acceptance0%,0/4;parent63.75%,12/20. B1 .01/.02/.03=100%,.04=0%;B1=75%. B1.03a/b/c/d100%. B2/B3/V1 still0%. B1.04 has not been decomposed/implemented. Closed BP07.03 remains archived100%.

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

Planning0.69/public0.9/DB0014(never<=0.65migrators),Research0.34/public0.14/DB0013(never<=0.33),Data0.29/DB0012(never<=0.25),Knowledge0.18/public0.8,Registry0.1. No activegoals/skills/subagents/hosts. v1/LICENSE metadata debtuntouched. BP07.03Final_Installation.json1262initial/49replacement; actualowner/crash/rights/compiler/semantic/catalogevidence retainedunderBP-07-Campaigns. New supervisorproofunderBP-07-Supervisor. Olderhelperversionsmaymigrate;inspectbeforeuse.
