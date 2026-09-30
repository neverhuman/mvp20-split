# Definition authoring tests

Owner: [definitions module](../../src/amphora_campaign_runtime/definitions/README.md). Run dev/run_tests.py --module runtime --area definitions; AMPHORA_TEST_POSTGRES=1 opts into the retained owned PostgreSQL fixture. Never run concurrent campaign-admission suites.

Pure revisions cover immutable old versions, optimistic conflicts, scope/campaign identity and content tampering. Real-owner command tests cover a two-writer barrier race, original success/rejection replay after later edits, injected failure after writes but before receipt, permission rejection before registration and denied destructive SQL through the service role. HTTP tests verify scope/read/write separation, immutable revision access, the separate draft receipt route, strict bounds/filters and explicit typed host enablement.

9 cases pass. This is in-process API/actual persistence evidence; independent installed-host replacement, process-kill durability, validation and browser commands remain later gates. See module README for coverage and gaps.
