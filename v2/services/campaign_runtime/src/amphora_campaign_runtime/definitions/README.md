# Runtime definition authoring

Status: BP-05.03/B1 partial. Immutable draft save/read and pinned structural validation are implemented; validated-plan publication, registry-backed forms and activation integration remain unimplemented. Owner: Campaign Runtime, [Definitions design](../../../../../docs/Architecture/Campaigns/Definitions.md).18 owned tests and the full1272-Python/65-Node/19-install foundation gate pass, including REC-01..09. No complete B1 delivery claim.

## Behavior and authority

DraftContent owns exact authored bytes/digest under amphora-draft-content-v1. Public DTO parsing materializes defaults; dictionary keys sort while authored array order remains meaningful. This identity is distinct from the compiler's semantic plan hash. DraftVersion owns optimistic revision advancement, immutable scope/campaign identity and explicit DTO mapping. A no-op save creates another revision with the same content digest. Reads verify stored identity and content digest.

DefinitionCommands.save requires the author permission and exact actor/scope/family before registration. A pending canonical command is recoverable. Its short owner transaction locks that command, then a deterministic scoped draft advisory key; this serializes first creation and later saves. Hash collisions only serialize unrelated drafts. Head advancement, immutable revision, authoring audit and original terminal receipt commit together. Expected-revision conflicts return an immutable rejected receipt; retries cannot turn a previous rejection into acceptance. No peer/network call or execution-state write occurs in this transaction.

Runtime-private runtime_0015 creates definition_heads, definition_revisions and definition_audit. Only head_revision is service-updatable; revision/audit rows grant SELECT/INSERT only. Deferred scoped foreign keys bind head/parent/command operation. Ordinary startup never applies migrations; enabled hosting checks required tables. Persistence shares only Runtime's existing canonical command journal, not a cross-service store.

DefinitionReads returns one immutable revision or current head, bounded identifier-ordered head pages and the current actor's original authoring receipt. Head listing selects header JSON only, never all definition bodies; pages observe current heads rather than claiming one frozen catalog revision. Cross-scope missing records return unavailable. Pending receipts can be read after interrupted saves. Legacy execution receipt routes reject authoring families rather than widening their published union.

## Pinned validation

ValidationUniverse owns an immutable, scoped union of reviewed host tool releases and exact schema bytes. Host loading reads each configured graph/material set once; configured execution and validation use the same loader and compiler. Identical pins deduplicate across graphs within one scope; conflicting pins fail host construction. Bounds are64 releases and256 schemas per universe,64KiB per schema. The amphora-authoring-universe-v1 hash pins scope, compiler profile, tool locks and schema identities independent of list order. Retained material includes verified descriptors and exact schema bytes; restoration verifies descriptor, schema and universe digests. It never fetches arbitrary schema URLs.

DefinitionValidator requires the separate validate permission before command registration. It loads the exact retained draft revision and checks the requested content digest. Pure compilation occurs outside the short transaction. The transaction locks the command, rechecks terminal replay, and atomically retains the universe, validation result and original receipt. Concurrent retries commit one result; a later configuration change cannot rewrite an already committed receipt. Uncommitted interrupted validation can retry against the configured universe and records whichever result commits first. Missing material/revision or mismatched digest produces a terminal rejected command. Structural failure instead produces an accepted recording of an unsuccessful validation with bounded findings.

runtime_0016 stores definition_universes once per scoped digest and immutable definition_validations. Only SELECT/INSERT are granted. Scoped foreign keys bind exact revision/content, universe and operation. Validation of an older immutable revision is permitted and does not claim that it is the current head. Later activation must separately check head/content, current eligibility, permissions, limits and the existing single-campaign guard. Results explicitly leave current eligibility, activation and scientific applicability pending; scientific_acceptance remains not_established. No plan publication or execution side effect occurs.

## Public host boundary

Hosting requires explicit authoring=true, configured graphs, migrated owner tables and separate author/validate permissions for their commands. Default validation-only and existing hosts remain unchanged. Routes:

- POST /v1/definition-drafts/save: definition.save canonical command -> DraftCommandReceipt.
- POST /v1/definition-drafts/validate: definition.validate canonical command -> DraftCommandReceipt.
- GET /v1/definition-validations/{validation_id}: immutable DraftValidation.
- GET /v1/definition-drafts: at most50 heads, optional limit/after.
- GET /v1/definition-drafts/{draft_id}: current or explicit positive revision.
- GET /v1/definition-commands/{family}/{command_id}: current actor's authoring receipt.

Unknown filters and invalid bounds reject. Every route authenticates and checks the owning read/write permission. Graph-runtime0.9.0 owns DTOs; Runtime0.16.0 owns transitions. A saved or structurally valid draft is not executable approval or scientific acceptance. There is no admit-draft route yet and no live-run editing.

## Verification and replacement

Tests: services/campaign_runtime/tests/definitions; select dev/run_tests.py --module runtime --area definitions.18 owned tests pass using actual PostgreSQL for save/validation races, original replay, denied pre-registration, rollback-before-receipt, immutable-role grants, scoped HTTP reads and explicit hosting. Pure checks prove digest restoration, bounded material, scope isolation and structural failure without scientific approval. Coverage for this module only:338/354 statements and62/78 branches. Remaining paths include corruption/conflicting-material guards, revision exhaustion and direct invalid read arguments; no claim of full Runtime coverage from this focused suite.

Preserve content/command profiles, immutable prior revisions, scope/campaign identity, conflict/receipt meanings and role grants on rebuild. Independent process replacement and crash/validation/activation workflows remain B1-B3/V1 gates. No scientific authority, capability discovery or worker execution is owned here.

## Retained material restoration

ValidationMaterial is an internal scoped repository, not a public authorization surface. It joins immutable validation/revision/universe records, releases the connection and then revalidates hashes and compilation through VerifiedDraftPlan. Restoration rejects failed structural results, mixed revision/content, changed compiler results and foreign-scope missing records. It needs no current process-local catalog. require_selection checks all six public AdmitDraft pins but does not check current head, current eligibility or grant execution. Callers must enforce principal and admission policy. No publication table, draft admission route or resolver bypass is enabled by this prerequisite.

Verification for this addition:four material tests plus contract/dev and existing definitions suites total110 passing tests; isolated eight-wheel Runtime dependency closure builds/imports. Definitions coverage384/400 statements and72/88 branches; remaining defensive paths are described above. Predecessor full foundation evidence is deae0fb,1272 Python/65 Node/19 installs/REC-01..09; no new full-foundation or independent authoring-process replacement claim.
