# Restore

Refreshed2026-10-09 08:44:00 America/Chicago. Read FIRST after compaction.
Owner says continue until needed; milestones/commits are not stopping points.
No subagents/JARVIS; v1 read-only. Preserve untracked ocular PDF/DOCX.
Do not edit source/tests/module READMEs while verification runs.

Current checkpoint:
- LAN-01 accepted/archived/pushed14df0c8c.
- UI-01.05 K1 complete100%, child46.67%; R1=40%, I1=0. ParentUI01=55%, N2=75,
  Build68.75 unchanged until owning delivery groups close. All mirrors updated.
- UI01 -> UI02 -> POP01 -> ML01; LR01 remains paused25%overall/33.33%Build.
  Owner queried LR percentage: unchanged since62ea4966 before UI priority.
- K1 pushed e4890ebd; launch decision pushed e32304b6. OWNER APPROVED UI-01.06
  bounded launch API2026-10-09. Do not ask again. Implement autonomously untilneeded.
- Foundation pushed fda9504f: contracts/campaign_launch0.1 + six additive
  published schemas; Deployment source0.17 adds campaign_launch intent/profile/state/
  privateSQLitejournal; dependencies/locks updated. Existing schema bytes unchanged.
 25tests passed: canonical replay/identity, profilepins/limits, concurrent single-slot,
 restart, stale CAS rollback, admission binding and workerfailure preservesrun.
 Schema check + productionboundary guard passed; no testsrunning.
- Coordinator/runtimepeer/runbindingstore pushed87634f4e.
- Managedadapter/preflight/backup + scientificpreparedturnfix pushedde4b993e.
- Current UNCOMMITTED: LaunchInstallation/config manifest, LocalLaunchReadiness,
 LaunchHost andsupervisor --launch-manifest composition; startuprestore+catalogpins
 BEFOREpendingcontainerguard. Tests170pass incl lifecycle/scientific/launch/contracts.
 Boundariespass. Newdevinstalled/recoveryqualifiers; preparedintent/created options
 addedtoexistingverify_scientific_monitor_recovery.py.
- Verification FINISHED/PASSED: v2/.test-results/launch-installation-20261009b.
 IsolatedDeployment0.17/publiccontracts/Pydantic;468installedDeploymenttests, actual
 coordinatorprocessdeath afterfixtureHTTPadmission + 3actualDockeradoptionprobes
 started/intent/created. Fourprobespassed; originalidentities, singlePOST/request.
 Audit docs/Audits/UI-01.06_Launch_Recovery.md + Evidence/UI-01.06_Launch_Recovery.json.
 Physicalbundle C:/Users/alb_p/AppData/Local/Packages/PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0/LocalCache/Local/Amphora/launch-qualification-20261009b.
 Driverlog v2/.test-results/launch-installation-20261009b-driver.txt;
 owner/verification.log buildlog, verification.log tests/probes. Preservefailedoutput.
 Attempta preserved:468installedtests+receiptprocessdeath passed, TLScreationfailed
 becauseWindowsStorePython redirectedlogicalAppDataLocal andOpenSSLcouldn'tseeit.
 PSverifiedlogicalrequest.cnf absent, physicalPackageLocalCachefilepresent. Retryb
 usesexplicitphysicalpath; no productionchange needed. Do notuse logicalLocalAppData.
 UsesactualinstalledRegistryPython fromROOT .test-results/demo-20261008/frozen-original
 (NOTv2/.test-results!). LocalUIreturned200 at08:33; helpersunchanged.
 Earlier scopedrunner44tests passed, combinedcoverage90% (notnewfilescoverage).
 Productionboundaries pass. Existingregistry_access tests newlyregistered in scopes.
 Use pytest -c v2/dev/pyproject.toml (importlib); defaultmode causes existingtestname
 collisions. Fixedlaunchtestcrossimport; shortparamids avoidWindows oversizednames.
- UI-01.06 overall40%; L1/L2=100%, L3/L4/L5=0. L3nowactive: narrowauthenticated
 API/Gateway/Studio. L2allfourgroupscomplete. No publiclaunchlistener/UIyet.
 RunBindingStore retains exactconfig+manifest underROOT/campaign-launches/requestsha;
 no workersstarted. PublicRuntimePeer fixedloopback, exactbytes, receiptbindingchecks.
- BeforeL3: commit/push verifiedcomposition exactownedfiles(excludeocular). README,
 architecture/audit/trackersupdated. MBTrecentcheckpoint added andcapped25rows.
- Journal is new Deployment-private SQLite local state; include quiesced backup/
 restore and fail-closedcorruption handling beforelive release. It does not query
 peer tables. Same scopedactor/requestid inlaunch and Runtimeadmission.
- No testsrunning; livehelpers only. No paid calls.

K1 delivery:
Studio0.22; distinct domain tab; old view=knowledge stays Results. Verified retained
Knowledge pins override exploratory URL selection. Additive internal artifact
demo.campaign-knowledge-context version1 / formatv2 preserves old context.
Public SchemaRef version fixed1, so new schema identity rather than version2.
Six concepts/five hypotheses describe two tools and missing evidence, authored
synthetic engineering text, not LLM extraction/scientific validation.
Actual Data source rights/raw text/conversion and Knowledge records; no privateSQL.
Retained association is planning_context; numerical tools consume parameter artifacts.
New run74de1629bdc6444398239de807df325d, projectknowledge-demo-1b1dc25768334153b58973882627b858
completed4invocations; retentions confirmed and owned workers drained.

Verification:
318Studio tests, TypeScript/contracts and production dependency guard pass.
knowledge-context-b actualtextpublication; knowledge-run-b actualcampaign.
knowledge-browser-c localhost, knowledge-lan-browser-c HTTPS, and
knowledge-connected-regression-c existing five-view walkthrough pass.
Actual assets knowledge-ui/public-b. Browser screenshots desktop/narrow reviewed;
New c narrow screenshot inspected after source-refresh/fit probe refinement.
First knowledge-context-a/run-a/browser-a preserved binary source; text viewer
correctly refused it. Fixed publisher to text/plain and fresh scope/campaign,
never rewrote history or weakened media/hash checks.
Audit docs/Audits/UI-01.05_Knowledge_Integration.md.
Both staged schema byte pins and gitdiffcheck passed before K1commit.

Live:
localhost http://127.0.0.1:57013 session31300, v2/.test-results/knowledge-live-c.
LAN https://192.168.1.70:57013 session87288, knowledge-lan-c.
Both same newrun. Sessions stop after86400seconds from ready.json.
STOP file drains exactly owning helper; localhost also owns backend services.
Separate LAN gateway0.3 isolated lan-gateway-20261008a.
No firewall changes. CA/public-key TLS pinned browser; CA-verified API.
Old connected-flow-live-c, lan-live-20261008a, knowledge-live-a/b and LANa/b drained.
Rollback source run connected-flow-run-a, assets connected-flow-ui/public-e.
New invitation: dev/serve_lan_review.py invite --root ROOT --session SESSION
copies5minsingle-useURLclipboard; no secrets in chat/evidence.
Private TLS physicalLocalCache/Local/Amphora/lan-demo-20261008.

ROOT C:/Users/alb_p/AppData/Local/Packages/PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0/LocalCache/Local/Amphora/local-v2/restore-20261007b
Frozen owner manifests .test-results/demo-20261008/frozen-original/owners.json
Qualified tools v2/.test-results/scientific-tools-c. Public method helper:
prepare_scientific_knowledge.py --output --source-manifest --root [--publish],
run_scientific_demo.py --knowledge-records DIRECTORY (freshcampaign).
serve_scientific_review.py --root --run --output --public --duration86400.
verify_knowledge_review.py --root --session --output [--tls DIR] [--suite connected].
Only one supervisor perroot; never launch competingcontroller.
Python v2/dev/.venv/Scripts/python.exe withPYTHONUTF8=1; npm.cmd cwdv2/studio.
Git -c safe.directory=//DesktopNAS/Code/mvp20-split -c core.safecrlf=false.
Stage exact work, exclude userocularartifacts. Keep schema bytes LF (.gitattributes).

Next R1:
Approved UI-01.06. Implement journal-backed coordinator against public Runtime,
then managedlocalworker adapter. Never expose operatorcontrol or shelltoStudio.
ExistingDeploymentSupervisor holds lifetimewriterlease: launchlistener/background
coordinator should integrate into that owner, not run competingrootcontroller.
Scientific workerconfig requires run_id. Newbindings only after oldjournalsdrain;
preserve original admission receipt/run throughlostreply, startfailureandrestart.
Contractsparser parse_launch returns exactouter+innerCanonicalCommand; outer
campaign.launch requires numericv2profile, inner graph.admit_draft keepslegacy/numeric.
Request identityactor/scope/id mustmatch both. Wiremodels don'townpolicy.
LaunchState recovery_required latchesinvalidbindings; transientPeerUnavailable keeps
phase. Workerfailure returnsadmitted_not_engaged withpartialreadiness andoriginalrun.
Coordinator verifiesRuntime scope/run/plan andterminal+workerquiescence before release.
LaunchPreflight andManagedLaunchWorkers nowimplementedbehindports; needinstallation
composition. LoopbackPeer inruntime_peer suppliesread forpreflight; explicit404
PeerRecordMissing maps topreflightrejection, notadmissionrecovery/reset.
Supervisor scientificslots/catalogreporters fixed; replaceonlywhenoldnative/scientific
quiescent andcatalogstopped. Startup must loadretainedrunbindings BEFORE checking
configuredpendingjournals. Never omitoldpendingcontainers. RunBindingStoretemplates
mustremain samepinnedinputs acrossrestart. Catalog reporterreplicajournals keepidentity.
capture_local_backup.py coldcopiesROOT except.operation.lock/logs, nowcalls
require_launches_drained andrecordscount. Coldcopyreopen tested; installedrestorepending.
ScientificSlot nowadoptsintent/created andcallsoriginalturn.launch once; starting/
started remainpollonly. 2addedtests covergap; recordasR1blockingrepair, noLRprogress.
Compositionnowimplemented: load_scientific_templates separatespinningfrompendingguard;
LaunchInstallation restores exactactivebindings thenvalidatesconfiguredpending.
Manifestprofilelocal-campaign-launch-v1 fieldsactor_id,launch_profile,scientific_manifest,
catalog_manifest(absolute). NoAPIlistener yet. Supervisorargcan'tcombinelegacytoolflags.
Catalogfactorywritesimmutablegeneratedcatalog.json inrunfolder, preservesreplicapins.
Privateinstallation.json pinsactor/publicprofile/templatefingerprints/cataloghashbefore
admission; unresolvedstartuprequiresit. Nativeworkersprojectscope, configpins, local
images/resources/TLS/ownerhealth verifiedbeforeadmission. launchhost usesexistingowner
operatorcredentials privately; publicAPI/Gateway willrequireseparate scopedcredential.
HostcancelEvent stopsnewpeerrequests, failurerawerrorshidden. Normalshutdownwaitsstop;
forcedteardownmarkssupervisorclosed thencloseshostbeforecleanuporiginalhandles.
L2installedcoordinatorrecovery usesHTTPfixture, NOTactualRuntimecampaign; L4remainstrue
publicdraft/browser/workerendtoendgate. Do notclaimcompleteRunflow yet.
ParentN2 groups still require provider provenance/reasoning, generationalcomparison
and launch; I1 owns liveLLM/nodeinventory and durable missing-capability requests.
Check ordering for real dependency cycles; don't silently wave prerequisites.

Later:
UI02formula/2D first, then POP01. Existing numericBP08 caps128population/256retained/
262144byte; proposed1000/2000 not implemented. POP includes repeatedfork/merge/fork,
19stage typedmaterialprocesses, localreadiness and explicitpairing/cardinality;
controljoin != materialcombination; materiallineage != geneticancestry.
ML01afterPOP. Inheritedmodels exist, rawv1feedback absent. HistoricalPolyverse
R2~.944source split ->~.453polymer-heldout, never currentdemoaccuracy.
