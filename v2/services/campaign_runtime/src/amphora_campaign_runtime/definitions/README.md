# Runtime definition authoring

Status: BP-05.03/B1 partial. Immutable draft save/read persistence and opt-in HTTP are implemented; executable validation, validated-plan publication, registry-backed forms and activation integration remain unimplemented. Owner: Campaign Runtime, [Definitions design](../../../../../docs/Architecture/Campaigns/Definitions.md). Full foundation1263 Python/65 Node tests,19 installs and REC-01..09 pass; no complete B1 delivery claim.

## Behavior and authority

DraftContent owns exact authored bytes/digest under amphora-draft-content-v1. Public DTO parsing materializes defaults; dictionary keys sort while authored array order remains meaningful. This identity is distinct from the compiler's semantic plan hash. DraftVersion owns optimistic revision advancement, immutable scope/campaign identity and explicit DTO mapping. A no-op save creates another revision with the same content digest. Reads verify stored identity and content digest.

DefinitionCommands.save requires the author permission and exact actor/scope/family before registration. A pending canonical command is recoverable. Its short owner transaction locks that command, then a deterministic scoped draft advisory key; this serializes first creation and later saves. Hash collisions only serialize unrelated drafts. Head advancement, immutable revision, authoring audit and original terminal receipt commit together. Expected-revision conflicts return an immutable rejected receipt; retries cannot turn a previous rejection into acceptance. No peer/network call or execution-state write occurs in this transaction.

Runtime-private runtime_0015 creates definition_heads, definition_revisions and definition_audit. Only head_revision is service-updatable; revision/audit rows grant SELECT/INSERT only. Deferred scoped foreign keys bind head/parent/command operation. Ordinary startup never applies migrations; enabled hosting checks required tables. Persistence shares only Runtime's existing canonical command journal, not a cross-service store.

DefinitionReads returns one immutable revision or current head, bounded identifier-ordered head pages and the current actor's original authoring receipt. Head listing selects header JSON only, never all definition bodies; pages observe current heads rather than claiming one frozen catalog revision. Cross-scope missing records return unavailable. Pending receipts can be read after interrupted saves. Legacy execution receipt routes reject authoring families rather than widening their published union.

## Public host boundary

Hosting requires explicit authoring=true, configured graphs, migrated owner tables and configured author permission for writes. Default validation-only and existing hosts remain unchanged. Routes:

- POST /v1/definition-drafts/save: definition.save canonical command -> DraftCommandReceipt.
- GET /v1/definition-drafts: at most50 heads, optional limit/after.
- GET /v1/definition-drafts/{draft_id}: current or explicit positive revision.
- GET /v1/definition-commands/{family}/{command_id}: current actor's authoring receipt.

Unknown filters and invalid bounds reject. Every route authenticates and checks the owning read/write permission. Graph-runtime0.8.0 owns DTOs; Runtime0.14.0 owns transitions. A saved draft is not executable approval or scientific acceptance. There is no validate/admit-draft route yet and no live-run editing.

## Verification and replacement

Tests: services/campaign_runtime/tests/definitions; select dev/run_tests.py --module runtime --area definitions.9 owned tests pass using actual PostgreSQL for race, original replay, denied pre-registration, rollback-before-receipt, immutable-role grants, scoped HTTP reads and explicit hosting. Coverage for this module only:189/198 statements and27/36 branches. Remaining paths include corruption guards, revision exhaustion, direct invalid read arguments and some unavailable receipts; no claim of full Runtime coverage from this focused suite.

Preserve content/command profiles, immutable prior revisions, scope/campaign identity, conflict/receipt meanings and role grants on rebuild. Independent process replacement and crash/validation/activation workflows remain B1-B3/V1 gates. No scientific authority, capability discovery or worker execution is owned here.
