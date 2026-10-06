# Restore

Read FIRST after compression. Refreshed 2026-10-05 22:56:16 (America/Chicago).

## Resume

Owner says continue until needed across milestones/commits/pushes/compaction. Latest pushed8d1851de; b.i template/context checkpoint is next commit. No tests/hosts/workers running. Current BP-07.04/B2.03b.ii Planning packet/preparation and owned provider execution. No owner decision needed for deterministic fixtures. Do not end at commits.

Runtime0.50/runtime0026 APPLIED; NEVER Runtime<=0.47 migrators. Planning0.80/planning0016;never<=0.73migrators. Data0.29/artifacts0012 (never<=0.25),Research0.34/research0013 (never<=0.33),Knowledge0.18,Registry0.1. PublicSupervision0.7,Planning0.10,graph-runtime0.13;544 publishedschemas unchanged,542predecessorpins. Liveprovider/model/egress/spend TBA blocks realcalls only.

## Canonical position

Parent69.07%,13/20;child45.37%,Build60.49%,Acceptance0%,1/4. B1=100%;B2=81.48%(.01/.02=100%,.03=44.44%);B3/V1=0%. B2.03 a100%,b33.33%,c0%. b.i100%,b.ii0%,b.iii0%. Current b.ii packet/owned execution, next b.iii capture response publication, then c autonomous Runtime delivery/repair/fallback. See BP-07.04 Autonomous loop.md and canonical tracker.

## Latest Planning boundary (b.i)

services/agent_planning/src/amphora_agent_planning/supervision_execution: ReviewedBudgetTemplate private planning-supervision-budget-template.v1, immutable canonical<=16KiB. Pins scope/model/prompt/checkpoint output/actions/limits/per-attempt accounting, excludes dynamic RuntimepolicyArtifact. Complete old BudgetPolicy would create policy->recipe->budget->policy hashcycle. Template.bind(originalRequestSnapshot) derives UNCHANGED BudgetPolicy v1 with requestpolicyArtifact and checks existing demand; all other pins/ceilings unchanged. BudgetTemplates exact operator-configured ArtifactRef+canonicalbytes catalog; no model/request installs. Template Artifact matches recipe/publiccontext budget_policy ref.

CheckpointContextBinding.bind(intake,principal,reference,raw) revalidates original authenticated CheckpointIntakeSnapshot, required constraintArtifact/content schema/bodyhash, exact reference/engagement/lineage/checkpoint/roots/snapshot/deadline/actions/target/field names, scalar ASCII-JSON fingerprints and remainingrequest/call allowance. Runtime database membership remains Runtimeauthority. budget_policy(catalog) selects exact template and deriveslegacy policy. No IO/SQL/providercall in this gate. Tests under Planning tests/supervision_execution;72context/template/legacybudget/boundary17.11s,131statements4branches100%. Initialduplicateactionfixtureoverflow repaired. Evidence Checkpoint_Planning_Binding.json.

## Next b.ii facts

SupervisionIntake.request(principal,engagement_id) returns original wrapper; requiresread_attempts. receive already registered original Planning request; no attempt/grant. PlanningRunner.run/execute handles register,reserve,once-onlyissuance,provider outsideSQL,capture,settlement. Existing budget/charge code untouched. Need explicit owner worker boundary to prepare exact original CampaignPacket through fresh Data reads and journal it, then run configured provider under original wrapper deadline/limits/template. No Runtimeprivateimports/tables.

Read campaign_artifact_context/README and campaign_preparations/README before source. CampaignArtifactContextReader(data).read(RequestSnapshot,ReadBudget)->ArtifactContextRead.projection; arbitrary Artifactformats base64, fresh processing reads,required gaps explicit. CampaignSlicePlan.from_artifacts(projection), campaign_packet.prepare(plan) uses unchanged reviewed campaign-v1 prompt/FixturePacketTokenizer; original input+output/total limits. CampaignPreparationJournal.register(principal,plan,packet) requiresrecord_attempts, originalregisteredrequest, noextractionfamily and no prior dispatch/observations; exactreplay immutable. read(principal,EngagementRef) requiresread_attempts. Durable preparation cannot be regenerated to changeoriginalaftercall. Need inspect dispatch/provider integration to consume original packet and fresh processing checks; do not infer ready wiring. Old CampaignDecisionDeclaration private authored-address/floatprofile is not this publiccontext, don't importacrossowner. Old PreparedCampaignProposal still oldoutputprofile; new futuredrafts retainedonly.

## Runtime preparation (a COMPLETE)

supervision_preparation: ReviewedRecipe privatecanonical v1 pins objective,prompt,model/config,staticentries<=127,omissions,actions,limits,PlanningbudgetArtifact; excludes dynamic Runtimepolicy/declaration. RecipePolicyRecord private runtime-supervision-policy.v2 adds context_recipe_sha256; oldv1 staysclosed/readable. GraphAdmission selects exactRecipeCatalog before run and PolicyPins pins append-only recipe before frontier; RecipePins runtime0025 verifieshash/scope onread. Originalreceipt replay beforecatalogs; noactiveconfigurationrebasing.

CallReservations reserves fullmax_attempts perrequest againstslot/campaign request/call ceilings; no refunds. RequestJournal.prepare calls RequestReservation.prepare underexistingrunlock and persist afterrequest/outbox in SAMEtransaction(runtime0026). New recipepolicy requests verifyoriginalslot/footprint/policy/recipe/deadline/winnerabsence and completeaccounting; exactreplaybeforefreshchecks. Legacyv1manualunchanged.155regressions110.07s+61refined26.59s coveredatomicrollback,contention,repairs,cancelledreplay,incompletehistory,contextaliases.

supervision_context ContextBasis/ContextSession deterministicengagement fromseed/recipe/actor/lineage, original exactfields/bounds/digests,remainingquotas,repairs preserve/narrowactions/deadline/limits,clampattempts toremainingcalls. Validatesframecharges matchpreviousallowance. ContextPublisher reuses ArtifactPublisher public receipt-first upload/finalize; content-derivedoperationIDs avoidconflicts onrefresh. ContextPreparer.prepare(principal,reference,parent_request_sha256=None) selectsinitialrequestor exactrepairchild. Originalreplaybeforecurrentstatus/publication. Shorttransactions capture/recheckactualslot/seed/recipe/series/charges; selectedchanges fail,unrelatedcut allowed; publisheroutsideSQL; journal commitsquota. Competingpreparer returnsoriginal,including changedunrelatedcut race. Finalguard->cancel->commitcannotrecordrequest.

Public CheckpointContext DTO (Supervision0.6) exported544schemas preserve542. Data validator rejects$id. AdditiveSupervision0.7 checkpoint_context_content_schema_bytes()/content_schema() is DISTINCT local-pointer-only contentprofile schema_idsupervision.checkpoint-context-content. Old checkpoint_context_schema() export/hash unchanged; noData codechanges. Runtimepolicyvalidator usesrawRecipePolicyRecordschema. ActualData0.29test publishes allstaticroots,policy/declaration,7processingreads,restart/replay;PIDs18048/30528exited. Runtime-ownedfixtureprompt copiedLF fromPlanning campaign-v1. Budget/modelconfigbytes inthat fixture are deliberatelysynthetic; don'tclaimPlanningbudget/packet/provider acceptance.94scoped59.07s+11guard15.73s;preparation81stmts16branches100%. Evidence Checkpoint_Context_Preparation.json.

## Earlier boundaries / verification caveats

Winner runtime0024: oneimmutable model/fallback/cancel +audit/outbox/selection; priorreplay beforestatus/deadline. GraphPass gatespending/releasescommitted orblocktarget. artifact_bindings/effective resolvesselectedfields atopeningand revalidation; originalplanimmutable. Context/current_seed and winner sourcechecks actualconcreteoccurrence/selectedfootprint; relevantrefresh preservesdecisionidentity. ExplicitCheckpointRequest/Snapshot2,CheckpointDraft2,CheckpointDecision1 preserveoldprofiles. B3/V1 process/installedproofstillrequired.

Existing .test-results/checkpoint-effects-installed-20261005 Runtime0.42/Planning0.77 arePREDECESSORS;NEVERtheirRuntime migrator now0026. dev/verify_supervision_installations.py currently542/538: adaptfor544/542/newmodules/currentversions beforelaterproof. dev/verify_supervision_owners.py pinsRuntime0.33/Planning0.75:adaptbeforeuse. NEVERoldverify_supervision_journal.py(Runtime0.26)migrator. Prior336scoped+1056isolatedexchange/46Runtime32Planninghistoricalmigrationfiles. Allpriorprocessesexited.

## Rules/tools

No subagents/externalJARVIS/v1edits/SQLresets/oldmigrators/externalmessages. No source/test/dev/sourceREADMEwrites DURINGverification. Rootdocs/Restoreokay. SQLtestserialopt-inAMPHORA_TEST_POSTGRES=1;preservehistory. Credentialsenvonly,neverprintURLs/tokens/passwords. Future-onlyreceiptcorrections,activepinsimmutable;weaksciencevisible,noblanketveto.

PYTHONUTF8=1 everyPython;v2/dev/.venv/Scripts/python.exe;uvv2/.venv/Scripts/uv.exe;pytest -c v2/dev/pyproject.toml --tb=short. Coverage DIRECTORYfilesystempaths,notfile.py/dottedleaf. rg --files beforeunfamiliarpaths;doNOTguessfilenames/globs (severalwastedreads). Windowsabsolute(),neverresolve(). No giganticone-lineJSONfixture/testIDdumps. NormalRuff,fixonlytouchedfiles. Commentary<=60s. Gitdiffcheckbeforecommit,onenewlineEOF.

Gitmain: git -c safe.directory=//DesktopNAS/Code/mvp20-split;remotehttps://github.com/neverhumanbot/mvp20-split.git;identity/authset. Commit/pushverifiedsignificantwork,thenCONTINUE. Existingv1/LICENSEdebtuntouched.
