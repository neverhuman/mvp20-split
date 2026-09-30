# Definition authoring tests

Owner: [definitions module](../../src/amphora_campaign_runtime/definitions/README.md). Run dev/run_tests.py --module runtime --area definitions; AMPHORA_TEST_POSTGRES=1 opts into the retained owned PostgreSQL fixture. Never run concurrent campaign-admission suites.

Pure revisions cover immutable old versions, optimistic conflicts, scope/campaign identity and content tampering. Real-owner command tests cover a two-writer barrier race, original success/rejection replay after later edits, injected failure after writes but before receipt, permission rejection before registration and denied destructive SQL through the service role. HTTP tests verify scope/read/write separation, immutable revision access, the separate draft receipt route, strict bounds/filters and explicit typed host enablement.

9 cases pass. This is in-process API/actual persistence evidence; independent installed-host replacement, process-kill durability, validation and browser commands remain later gates. See module README for coverage and gaps.

Current B2 scope:54 definitions tests and60 scheduling regression tests pass. The eligibility suites cover exact public Registry candidates, bounded loopback transport, expired/unavailable/rejected observations, no peer I/O under admission locks, atomic audit/run/publication rollback, unchanged terminal replay, active-campaign/stale-head rejection and explicit host configuration. Adapter client47/49 statements,10/12 branches; clock-budget timeout paths remain uncovered in this scoped run. Observation policy28/28 statements,6/6 branches; admission guard42/42 statements,4/4 branches. Installed actual Registry/Studio proof remains a separate gate.
