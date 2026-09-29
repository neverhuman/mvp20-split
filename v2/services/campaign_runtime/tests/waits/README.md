# External-wait verification

Owner: [wait module](../../src/amphora_campaign_runtime/waits/README.md). Plan: [BP-04.03](../../../../docs/Build%20Plans/BP-04/BP-04.03%20Aggregation%20and%20failure%20policy.md).

Run the complete owned suite with `dev/run_tests.py --module runtime --area waits --coverage`; PostgreSQL requires the explicitly enabled, labeled local fixture. Keep this suite serial with other single-campaign owner suites. Storage-only fixtures do not establish execution acceptance.

`test_process_recovery.py` runs separate owner processes through production coordinator/authority methods against PostgreSQL. `process_probe.py` is test-only and absent from the installed package. It receives only Runtime's scoped owner connection and a bounded command; generated evidence excludes credentials. Every process is owned and cleaned up by the test.

The process oracles are independent of scheduler arrival order:

- Two measured lock waiters before deadline: exactly one accepted closure; command replay is unchanged.
- Two measured lock waiters after deadline: blocked timeout closure; the receipt cannot extend its deadline.
- Cancellation or timeout while another process reserves: the first closure persists, the prepared intent aborts and late reservation protection queues reconciliation rather than confirmation.
- Sender killed after commit before reply: a replacement returns the original receipt and closure without reserving again.
- Two prepared receipt processes: one accepted command and one rejected command, one immutable closure, one committed and one aborted protection intent.

These tests deliberately script Artifact reservation responses to isolate Runtime failure handling. They do not establish actual Artifact retention, independent package installation, scientific authority or target-host durability. V1 owns installed issuer/peer and replacement acceptance. Aggregation's independent ordered-member/minimum/duplicate/late-cut oracles remain in the separate `aggregation` suite.
