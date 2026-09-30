# Definition authoring tests

Owner: [definitions module](../../src/amphora_campaign_runtime/definitions/README.md). Pure revision tests cover immutable old versions, optimistic conflicts, scope/campaign identity and content tampering; no database authority claim. Run `dev/run_tests.py --module runtime --area definitions`. Persistence races, command replay, HTTP authority and replacement must be added as those boundaries are implemented.
