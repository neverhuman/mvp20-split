# Restore

Read FIRST after compression. Refreshed 2026-10-05 22:14:05 (America/Chicago).

## Resume

Owner says continue until needed across milestones/commits/pushes/compaction. Latest pushed ddb7103d; recipe admission checkpoint is next commit. No tests/hosts/workers running. Current BP-07.04/B2.03a.ii atomic request reservation half. Recipe admission half verified. No owner decision needed for deterministic work.

Runtime0.47/runtime0025 APPLIED. NEVER Runtime<=0.46 migrators. Planning0.77/planning0016; never<=0.73 migrators. Data0.29/artifacts0012 (never<=0.25); Research0.34/research0013 (never<=0.33); Knowledge0.18;Registry0.1. PublicSupervision0.5,Planning0.10,graph-runtime0.13. 542 schemas preserve538. Live provider/model/egress/spend TBA blocks real calls only.

## Canonical position

Parent68.61%,13/20;child43.06%,Build57.41%,Acceptance0%,1/4. B1=100%;B2=72.22%(.01/.02=100%,.03=16.67%);B3/V1=0%. B2.03 a50%,b/c0%;a.i100%,a.ii50%,a.iii0%. a.ii halves: recipe admission100%,atomic requests0%. Current atomic reservations, next a.iii preparation bridge. See BP-07.04 Autonomous loop.md and canonical child tracker. Source modules have rebuild READMEs; no whole-history reread needed.

## Latest implementation

supervision_preparation ReviewedRecipe owns canonical private recipe v1, scoped Artifact identity/context limits and pinned prompt/model/objective/budget policy/actions/static context. Excludes supervision policy Artifact/dynamic declaration to avoid hash cycle. 127 static entries leave declaration space. CallReservations reserves full max_attempts per unique request against both slot/campaign request/call ceilings; exact replay no extra charge, no refunds. Pure only so far.

Private RecipePolicyRecord profile runtime-supervision-policy.v2 adds context_recipe_sha256. Old PolicyRecord v1 stays closed; read_policy explicit dispatch. ReviewedPolicy.bind/document supports both. RecipeCatalog exact scoped digest validates initial attempt allowance fits every slot. GraphAdmission recipes keyword selects before creating run, PolicyPins.pin stores recipe before frontier; PolicyPins.load validates retained recipe for v2. RecipePins append-only runtime0025. Missing/mismatched bytes block exposure. No backfill/active recipe update; original command replay precedes catalog lookup. Public admission profile unchanged.

Verified120 scopedSQL/policy/checkpoint/boundary25.96s;8 focused corrupted/missing pin4.97s;35preparation5.14s gives133statements14branches100%. Ruff passed. Evidence Checkpoint_Recipe_Pin.json. Previous domain27tests3.35s84statements4branches100%,39boundary14.15s. Initial fixture issues (package marker, enormous Windows test ID) and private import corrected. Coverage source must be DIRECTORY path, not file.py/dotted leaf.

## Next implementation detail

RequestJournal.prepare in supervision_journal/storage.py already owns run-locked transaction. Prefer integrating a recipe-profile reservation gate inside that existing transaction, protecting every new request and avoiding an unused caller-transaction API. For v2policy load exact slot/recipe, validate request recipe/deadline/target/output/lineage/winner absence, reserve entire attempt allowance, append request/outbox/reservation atomically. Existing v1manual requests remain supported. Exact replay returns original without another charge; fresh request after winner denied. New reservation FK references actual journal request. SQL race/rollback proof required. Do not edit applied0025; add forward0026 if needed, bumpRuntime.

Preparation publication remains a.iii: actual Data policy/declaration Artifacts and rights; never fabricate references. Existing campaign-v1 trusted prompt is schema-generic; reuse CampaignPreparation packet/profile and PlanningRunner issuance/budget/capture. RequestSeries fixes objective/prompt/policy/model, narrows actions/limits, preserves required context except prior declaration role=constraint+artifact.sha==decision_scope. PlanningRunner not wired to supervision intake; APIs only intake/readback. Planning budget ledger remains distinct from Runtime potential-call quota. Existing PreparedCampaignProposal compiler entry still uses old CampaignOutput; new future drafts retained, not automatically compiled.

## Prior verified boundaries

Runtime winner0024: one immutable model/fallback/cancel winner +audit/outbox/selection under runlock; exact replay before currentstatus/deadline. supervision_winners/slot_for and current_seed rederive actual occurrence/footprint. New CheckpointRequest/Snapshot2, CheckpointDraft2 and CheckpointDecision1 explicit; oldprofiles unchanged. GraphPass gates pending, releases committed review/fallback or blocks pinnedtarget. artifact_bindings/effective.resolve_effective feeds conversion opening and source-cut revalidation; original plan immutable. 86winner/binding checks92.54s plus18relocated21.02s, resolver/winner100%; broad86% has oldHTTP/expiry/cache gaps. ActualRuntimeSQL/scriptedMemoryArtifacts, not actualData/tool proof. B3/V1 still required.

Installed predecessors .test-results/checkpoint-effects-installed-20261005 runtime0.42/planning0.77; NEVER their Runtime migrator now0025. dev/verify_supervision_owners.py pinsRuntime0.33/Planning0.75: adapt successor before use. NEVER oldverify_supervision_journal.py (Runtime0.26) migrator. Prior exchange336scoped+1056isolated;46Runtime/32Planning predecessor migrationfiles unchanged. Process recovery proof28PIDs all exited. No hosts left.

## Rules/tools

No subagents, externalJARVIS, v1edits, SQLresets, oldmigrators or externalmessages. No source/test/dev/sourceREADME writes during verification. Rootdocs/Restore okay. SQLtests serial opt-in AMPHORA_TEST_POSTGRES=1, retainedhistory preserved. Credentials envonly, never print URLs/passwords/tokens. Future-only receipt corrections; active pins immutable. Weakscience visible, not blanketveto.

PYTHONUTF8=1 everyPython. v2/dev/.venv/Scripts/python.exe; uv v2/.venv/Scripts/uv.exe; pytest -c v2/dev/pyproject.toml --tb=short. rg --files before unfamiliar paths, no guessed globs. Windows absolute(), neverresolve(). Short tool output; never dump one-line JSONfixtures or huge test IDs. NormalRuff, fix onlytouchedfiles. Keep commentary<=60s. git diff --check beforecommit; one newlineEOF.

Git main: git -c safe.directory=//DesktopNAS/Code/mvp20-split;remote https://github.com/neverhumanbot/mvp20-split.git;identity/authset. Commit/push verified significant work, then CONTINUE. User approvals persist. Existing v1/LICENSE metadata debt untouched.
