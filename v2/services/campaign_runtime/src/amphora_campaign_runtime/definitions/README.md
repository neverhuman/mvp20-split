# Runtime definition authoring

Status: BP-05.03 closed. Runtime0.20.0 owns draft save/read, pinned validation and transactional draft admission/publication. Tool-bearing admission requires the optional [Registry eligibility adapter](eligibility/README.md); absent configuration rejects. Owner: Campaign Runtime, [Definitions design](../../../../../docs/Architecture/Campaigns/Definitions.md).54 definitions/60 scheduling tests passed; full B2 foundation1336 Python/132 Node/19 installs/REC-01..09/9 standard-worker cases. Independent actual Registry/Runtime/Artifact/Studio proof and pending-command process-kill recovery passed; [authoring audit](../../../../../docs/Audits/BP-05.03_Authoring_Closeout.md).

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
- POST /v1/graph-runs/drafts: explicit graph.admit_draft -> existing Runtime CommandReceipt, requiring admit authority and configured draft guards. Read its original receipt through the existing execution-command route.

Unknown filters and invalid bounds reject. Every route authenticates and checks the owning read/write permission. Graph-runtime0.11.0 owns DTOs; Runtime0.20.0 owns transitions. A saved or structurally valid draft is not executable approval or scientific acceptance. Draft admission requires the existing v4 binding profile; enabling authoring does not enable missing execution peers. No live-run editing is provided.

## Verification and replacement

Tests: services/campaign_runtime/tests/definitions; select dev/run_tests.py --module runtime --area definitions.29 owned tests pass using actual PostgreSQL for save/validation races, original replay, denied pre-registration, rollback-before-receipt, immutable-role grants, scoped HTTP reads and explicit hosting. Pure checks prove digest restoration, bounded material, scope isolation and structural failure without scientific approval. Predecessor061541b coverage for definitions only:427/444 statements and73/90 branches; the new catalog has its separate current denominator below. Remaining paths include corruption/conflicting-material guards, revision exhaustion and direct invalid read arguments; no claim of full Runtime coverage from this focused suite.

Preserve content/command profiles, immutable prior revisions, scope/campaign identity, conflict/receipt meanings and role grants on rebuild. Independent process replacement and crash/validation/activation workflows remain B1-B3/V1 gates. No scientific authority, capability discovery or worker execution is owned here.

## Retained material restoration

ValidationMaterial is an internal scoped repository, not a public authorization surface. It joins immutable validation/revision/universe records, releases the connection and then revalidates hashes and compilation through VerifiedDraftPlan. Restoration rejects failed structural results, mixed revision/content, changed compiler results and foreign-scope missing records. It needs no current process-local catalog. require_selection checks all six public AdmitDraft pins but does not check current head, current eligibility or grant execution. Callers must enforce principal and admission policy. Restoration itself creates no publication or run and supplies no eligibility grant.

## Draft admission and retained execution

DraftAdmissionGuard prepares exact selected material outside the transaction. GraphAdmission owns the original graph.admit_draft command and its existing global admission guard; no second command identity or scheduler is created. Terminal replay precedes current configuration/head checks. The transaction locks the current draft head, checks exact revision/current configured universe, then applies existing binding-profile, input, budget, expansion and single-active-campaign guards. Head edits that commit first reject admission; edits that follow admission create a next-campaign revision and cannot mutate the run.

runtime_0017 adds immutable definition_admissions linking the validated source to the actual graph run/plan and original command operation. Publication, run/frontier, audit/outbox and receipt commit together. Failed commits leave only the recoverable pending canonical command. Scoped foreign keys and SELECT/INSERT-only grants preserve lineage. Tool-bearing drafts return draft_tool_eligibility_unavailable without explicit Registry configuration; retained structural validity is not a substitute for current tool eligibility. Independent process/crash proof remains B3/V1.

PublishedPlanCatalog is used by BindingCoordinator to find retained material for already-admitted runs, including after authoring is disabled or the old configured plan is absent. It does not replace GraphAdmission's configured allowlist. Consequently ordinary graph.admit cannot bypass the draft guard using a previously published plan hash. Resolution uses scoped immutable publication/revision/universe records and verifies the restored plan hash. It performs no Registry or Artifact network request and holds no permanent eligibility cache. Binding-enabled hosting requires runtime_0017 even when authoring is disabled; startup never migrates.

Owned tests verify publication rollback, original replay after edits/configuration changes, immutable role grants, foreign-scope lookup, existing configured-admission isolation, completion through GraphAdvancer, stale-head/universe rejection, competing admissions and fail-closed tool eligibility. Independent authoring/binding replacement and Studio consumption passed in the B1-B3 owner evidence. Predecessor061541b foundation evidence:1286 Python tests,65 Node tests,19 independent installs and REC-01..09 pass. This validates existing installed boundaries plus owned authoring tests; later actual-owner replacement evidence is retained in the closeout audit.

## Reviewed editor metadata

DefinitionCatalog owns a read-only immutable copy of the configured scoped universe map. GET /v1/definition-universe returns exact reviewed tool locks and schema references, limited to64 releases/256 schemas, without eager schema bodies. GET /v1/definition-schemas/{digest} requires schema_id, version and universe_sha256 query pins; it returns the original bytes in a bounded canonical base64 envelope plus exact scope/reference/universe. Unknown scopes or full identities return404; changed universe returns409; unsupported filters/versions return422. Every read requires read authority. No arbitrary URL is accepted or fetched, and no database state changes.

The compiler_configuration authority marker distinguishes this projection from Registry discovery/lifecycle, resource availability and scientific acceptance. Registry remains the public descriptor/discovery owner. Consumers verify the exact schema digest and support only declared form constructs. Authenticated foreign-scope reads reveal no metadata. tests/definitions/test_catalog.py proves all30 statements/10 branches of this mapper and HTTP pin/authentication/query failures; three metadata/DTO cases also verify bounded canonical base64. All196 predecessor schema files remain byte-identical. No Studio consumer, browser acceptance or new full-foundation claim is inferred.

Numeric command correction: definition.save and graph.admit_draft accept explicit amphora-command-v2 envelopes from Commands0.2.0; existing unmarked commands remain v1. Authored NumberConstant values are floats; graph input NumberValue remains a decimal string. No implicit conversion between these contracts. Owner tests exercise integral/decimal/exponent constants through save/validate/admit/finish, scoped profile persistence and original replay; a separate actual-host process kill verifies old/new saved receipts and cross-profile conflicts. Other command families remain v1.

B2 eligibility checkpoint:114 definitions/scheduling tests pass, including actual PostgreSQL admission guards with scripted Registry responses. EligibilityObservation verifies exact scoped pins/status and expiry; peer calls stay outside owner transactions. Freshness is checked with database time under the admission guard; accepted observations persist in immutable audit_events with the run/publication/receipt. Original terminal replay never refreshes eligibility. Registry candidates are not reservations; no cross-service atomic revocation guarantee or scientific acceptance is claimed. See the focused adapter README for configuration and limits. Actual installed Registry/Studio activation proof passed; full compatibility gates passed.

## Draft successor admission (BP-08.04)

Runtime0.65 exposes POST `/v1/graph-runs/draft-successors` only when draft
admission is configured. Public draft_successor0.1 supplies AdmitDraftSuccessor
and the distinct graph.admit_draft_successor command; graph-runtime0.13 and
existing command profiles remain unchanged. Explicit numeric envelopes use the
existing numeric encoding; graph NumberValue still uses decimal strings.

GraphAdmission enables the existing draft and successor guards together. Exact
terminal replay precedes fresh configuration/peer checks. Draft material and
Registry eligibility resolve outside SQL; under the global admission guard,
current draft head/universe/freshness and locked predecessor terminal/cut/settled
state are checked. Compatible carried plus fresh inputs feed the compiled plan.
New run, draft publication, lineage, audit/outbox and receipt commit atomically.
No migration, catalogue promotion, new scheduler or active-run rewrite occurs.

Owned tests in tests/definitions/test_draft_successor.py cover actual PostgreSQL
carry, changed head/cut/hash/selection/universe, active predecessor, concurrent
successors, rollback after both records, replay without current configuration,
ASGI auth/explicit hosting and current Registry guards through scripted peers.
205 contract/definition/successor/schema/boundary regressions passed. This does
not establish actual remote Registry, Planning topology handoff or target-host
execution; B2.02ii/V1 retain those gates. Replacement preserves both immutable
owner records and all original command receipts.
