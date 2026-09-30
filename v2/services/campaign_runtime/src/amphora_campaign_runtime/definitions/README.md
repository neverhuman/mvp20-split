# Runtime definition authoring

Status: BP-05.03/B1 partial; pure revision policy only. No draft API, database table, validation command or activation integration is implemented yet. Owner: Campaign Runtime, [Definitions design](../../../../../docs/Architecture/Campaigns/Definitions.md).

DraftContent owns exact authored-content canonical bytes/digest under amphora-draft-content-v1. Defaults are materialized by public DTO validation; dictionary keys sort, authored array order is retained. This is distinct from the compiler's semantic plan hash. DraftVersion owns expected-revision advancement, immutable scope/campaign identity and explicit conversion to/from the public DraftRevision. Stale saves cannot overwrite a later revision; loading a record verifies its content digest. A no-op save still creates a new revision with the same content digest.

The module performs no I/O, execution mutations, scientific approval or capability discovery. Public graph-runtime authoring DTOs are boundary records; these domain objects own revision behavior. Planned owner persistence must atomically commit head, immutable revision, command receipt and audit. That behavior is not claimed by current pure tests.

Tests: `services/campaign_runtime/tests/definitions/`; select `dev/run_tests.py --module runtime --area definitions`. Preserve immutable prior versions, scope/campaign identity, canonical content profile and conflict semantics when rebuilding. PostgreSQL races, HTTP authority and process replacement remain required B1-B3/V1 work.
