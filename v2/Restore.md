# Restore

Read first after compression. Refreshed 2026-10-05 21:32:22 (America/Chicago).

## Resume

Owner says continue until needed. Latest pushed128a88e4; B2.02b complete ready commit/push. No tests/hosts/workers running. Current BP-07.04/B2.02c.i atomic winner transaction, then c.ii coordinator release. Do not stop at checkpoint.

Read Winner and effects.md. PublicPlanning0.10 CheckpointDraft (planning.checkpoint-draft/v1,payload2), publicSupervision0.5 CheckpointDecision. Explicit owner parsers and Runtime select_fields implemented. Legacy profiles unchanged; CampaignPrepared stays an old-profile composition entry point.336 scoped cases103.30s/631statements82branches100%;37SQL16.65s;1056 isolated initial/replacement cases. Evidence Checkpoint_Effects_Exchange.json. .test-results/checkpoint-effects-installed-20261005 PASSED. All processes completed. No SQL winner or conversion integration exists yet.

c design: new forward migration after runtime0023, immutable winner/selection bound original slot/request/response; reuse runtime.audit_events/outbox and existing run lock. RuntimeLeases._changed increments revision and commits audit/outbox (requires RunBudget). Replays return original winner before current run/deadline checks. Cancellation/terminal run wins against new acceptance. Fallback derives deadline/eligibility from slot/DB clock, not arbitrary caller reason. Provider/repair exhaustion belongs B2.03 retained evidence. Model effects require actual response journal capture and exact request/policy/slot lineage; select_fields validates seed/cut/prior/occurrence. Refresh seed can reconstruct retained request footprint plus original scalar fields, preserve slot identity/deadline/ceilings and retain selection seed bytes. Current membership/issued checks from supervision_journal.current.verify_footprint. Scalar conversion opening/revalidation will share resolver in d. No source edits during verification.

## Canonical progress

Parent67.50%,13/20;child37.50%,Build50%,Acceptance0%,1/4. B1=100%;B2=50%(.01=100%,.02=50%,.03=0%);B3/V1=0%. B2.02 a/b100%,c/d0%;c.i/ii equal0%. Current c.i,next c.ii then d conversion. No new owner decision.

## Current boundaries

Runtime0.42/runtime0023;Planning0.77/planning0016;publicSupervision0.5;graph-runtime0.13;publicPlanning0.10;542 schemas preserve538 predecessors. Actual retained DB Runtime0023/Planning0016. **NEVER run Runtime<=0.38 or Planning<=0.73 migrators.** Data0.29/artifacts0012 (never<=0.25),Research0.34/research0013 (never<=0.33),Knowledge0.18,Registry0.1.

- Public CheckpointRequest/Snapshot2 use explicit planning.supervision.request.v2; old request parsers/bytes closed. Runtime/Planning journals, separate v2 HTTP/client paths and exact receipts implemented. No provider call grant follows from recording.
- graph.admit_supervised numeric-v2 command pins exact policy hash. PolicyCatalog requires exact scope/plan/policy, no latest fallback. GraphAdmission.admit_supervised pins before frontier/initial issuance; original receipt replay precedes catalog lookup.
- supervision_policy: immutable ReviewedPolicy, exact scalar type/unit/finite bounds/choices, own-or-ancestor authored reads. PolicyPins uses caller transaction and append-only runtime0022; no retrofit after frontier creation. Human changes apply to future admissions only.
- supervision_checkpoints: admission creates initial ready slots; GraphPass creates later loop/scatter slots once while unrelated work proceeds. Held targets remain ready/unissued. CheckpointStore.ensure loads retained plan/policy under run lock, replays original first, verifies actual membership and absence of Invoke/binding intents, then captures selected observations. Append-only runtime0023; checkpoint limit/expiry gives fallback_required record, no request/model grant or execution release.
- CheckpointSeed v1 remains closed/readable. ValueCheckpointSeed v2 captures exact original named scalar values and original_fields_sha256 from ScopeState.environment before conversion. read_seed dispatch preserves old SQL history. Original values may be outside adjustment bounds; only proposals must satisfy bounds. B2.02 must require scalar-bearing v2 for adjustments.
- supervision_journal.current.verify_footprint is shared actual plan/node/ancestor/membership/no-issued-work checker. verify_current additionally checks request deadline. Original scalar/effective values must be revalidated at B2.02 acceptance and shared by conversion opening/revalidation.

## Recent proof

c integration:111 SQL/coordinator/legacy cases65.88s (admission100%,advancement95%,broad selected modules79%). Scalar refinement70 checkpoint/policy10.78s;191 checkpoint statements6branches100%.18 legacy SQL/boundary13.80s. Existing unsupported broad coverage is HTTP/config/polling/projections, not newly claimed behavior.

d.a `.test-results/checkpoint-policy-installed-20261005/manifest.json` PASSED:802 cases, Runtime292 each/Planning109 each,42/32 historical migration files unchanged,538 schemas/536 predecessors. Four isolated wheels/installations; peer-private packages absent. No SQL/migration. Initial/replacement Python paths under that directory can be used for current proof.

d.b `.test-results/checkpoint-recovery-20261005/manifest.json` PASSED:14 actual installed Runtime process runs,2 abrupt exits after admission pin/frontier and checkpoint-before-advance-commit,2 same-command races, exact original receipts/slots after replacement and cancellation. All28 launcher/worker PIDs exited,scoped cleanup complete.12boundary10.33s,Ruff passed. Evidence Checkpoint_Recovery.json. Helpers: dev/verify_checkpoint_recovery.py and Runtime tests/supervision_checkpoints/process_worker.py. No provider/request/effective scalar effect claim.

Historical HTTP owner proof ac5f290c used Runtime0.33/Planning0.75. dev/verify_supervision_owners.py is still hardpinned to those versions; do not pass current installs until a successor gate updates it. NEVER run old verify_supervision_journal.py (0.26) migrator; its barrier pattern is reference only.

## Operating rules

No subagents, external JARVIS, v1 edits, SQL resets, old migrators or external messages. No source/test/dev/source-adjacent README writes during verification; root docs/Restore may be updated. SQL tests serial opt-in, retained fixture history preserved. Secrets env-only; never print credentials/SQL URLs/tokens. Future-only receipt corrections; active pins immutable. Weak science stays visible, not a blanket exploration veto. Live provider/model/egress/spend remains unselected and blocks only real calls.

Use PYTHONUTF8=1 for every Python invocation. Python v2/dev/.venv/Scripts/python.exe; uv v2/.venv/Scripts/uv.exe. Pytest -c v2/dev/pyproject.toml --tb=short; actual SQL AMPHORA_TEST_POSTGRES=1. Filesystem coverage paths only: dotted Planning API leaf caused SQLAlchemy Cython initialization failure; no production workaround. Normal Ruff, no overrides. Use rg --files before paths; avoid guessed filenames and PowerShell directory/*.py globs. Stop shell sequences on nonzero exit. Windows Path.absolute(), never resolve(). Background windows hidden. Communicate at least every60s.

Git main: git -c safe.directory=//DesktopNAS/Code/mvp20-split. Remote https://github.com/neverhumanbot/mvp20-split.git. Commit/push verified significant work after canonical tracker/history/Restore sync, then immediately continue. Existing v1/LICENSE metadata debt remains untouched.
