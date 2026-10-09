# Restore

Refreshed2026-10-09 09:18:00 America/Chicago. Read FIRST after compaction.
Owner says continue until needed; milestones/commits are not stopping points.
No subagents/JARVIS; v1 read-only. Preserve untracked ocular PDF/DOCX.
Do not edit source/tests/module READMEs while verification runs.

Current checkpoint:
- LAN-01 accepted/archived/pushed14df0c8c; K1 pushed e4890ebd.
- UI01 -> UI02 -> POP01 -> ML01. LR01 remains paused25%overall/33.33%Build.
- UI01 parent55%, Build68.75%, N2=75 unchanged pending owning delivery groups.
  UI01.05=53.33%, K1=100%, R1=60%, I1=0. UI01.06=60%, L1/L2/L3=100%,
  L4 actual campaign/restart active0%; L5 installed/local/LAN pending0%.
- Owner APPROVED bounded Deployment launch API2026-10-09. No new permission needed.
- Pushed fda9504f contracts/journal;87634f4e coordinator;de4b993e workeradapter;
  845a6311 supervisor composition/L2 qualification; f177d1d5 API/recovery pushed.
  Current Studio Run integration L3 complete, awaiting checkpoint commit.
- L3 adds Deployment separate loopback launch HTTP/token, --launch-port, Gateway0.4
  explicit whitelist/safeerrors, Studio generated launch DTOs/client/immutable
  LaunchSubmission/localStorage journal/CampaignLaunch recovery model.
- Verification:335 Studio tests,125 combined Deployment launch/Gateway/integration,
  schema regeneration/TypeScript pass. Built-browser fixture launch/reload/graph
  polling/retained output passes1440/390, no serious/critical axe violations:
  v2/.test-results/launch-browser-20261009e. Narrow nested-grid overflow fixed.
  Faileda/b/c preserved; dpassed, eaddsready/fit screenshots. FullStudio log:
  v2/.test-results/launch-ui-20261009.log. No tests running. No live cutover yet.
- Source versions now Deployment0.18, Studio0.23, Gateway0.4; uv locks synced.
  Need installed0.18/0.4 for L4. Existing demo stays installedoldGateway/owners.
- Next L4: prepare bounded launch demo config/new isolated owner installations;
  extend actual scientific graph as self-contained prepared draft by substituting
  FIVE existing admission input ArtifactRefs into original graph input references,
  preserving nodes/edges and scope. Publish via existing public Runtime save/validate.
  Current knowledge-run-b/runtime.json lacks authoring/draft_registry. Add authoring
  and admin author/validate, Registry peer narrow token/principal. Existing helpers
  prepare_local_authoring.py/verify_local_registry_access.py show configuration.
- Studio LaunchPreparation intentionally disables drafts with unbound inputs; API
  supports them but first UI only self-contained prepared drafts. No empty-input
  fallback. LaunchPlanningContext supports constant or original admission input
  finish context, exact draft pins + Runtime scope/run/plan; labelled launch_plan
  until exact matching retained finish output. Actual Runtime node polling visible.
  LocalWorkspace selects returned run above Campaign; localStorage restores original
  request then GET, never rePOST. Browser fixture proved one POST across refresh.
- prepare/source: v2/.test-results/knowledge-run-b contains owners/runtime/native/
  access/admitted-scientific/admitted-catalog/admission.json plus context/artifacts.
  native.json references runtimeconfig and fixedscopeadmin. Keep all existingpins.
  v2/dev/serve_scientific_review.py currently owns localhost+backends via BrowserController;
  serve_lan_review.py separateGateway uses originalvault-only refs, must support new
  launch-token sidecar before newLANconfig. One lifetimeSupervisor/root: drain own
  livehelper only after replacementready. Check sourcehelper imports, don'tguesspaths.
- Audit docs/Audits/UI-01.06_Launch_UI.md; source-adjacent READMEs updated. Existing
  control HTTP test has intermittent Windows unread-body socket-reset; isolated
  unchanged test passed. Don't mistake fixture qualification for live campaign proof.
- Python v2/dev/.venv/Scripts/python.exe; pytest -c v2/dev/pyproject.toml mandatory.
  uv v2/.venv/Scripts/uv.exe; npm.cmd cwdv2/studio. Git safe.directory required.
- L2 evidence v2/.test-results/launch-installation-20261009b:468 independent
  installedDeploymenttests, actualprocessdeath originalreceipt/onePOST,3Docker
  monitoradoptionprobes(started/intent/created),170focusedsourcechecks. Audit
  docs/Audits/UI-01.06_Launch_Recovery.md. Fixture owner, not actualRuntimecampaign.
  Failedattempta retained WindowsStorePython AppData redirection issue; usephysical
  C:/Users/alb_p/AppData/Local/Packages/PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0/LocalCache/Local/Amphora paths.
- Root .test-results/demo-20261008/frozen-original/owners.json NOTv2/.test-results.
  Serving demo remains unchanged. One Supervisor lease/root; do not compete.

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
