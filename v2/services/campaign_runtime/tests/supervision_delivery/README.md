# Delivery tests

Actual Runtime PostgreSQL plus a scripted Planning socket peer. Cases cover original command submission, lost reply recovery, persisted receipt before readback, missing receipt/readback, peer denial/conflict/rejection/outage, cancellation between lookup and write, lease contention and terminal read-only replay. Servers close and threads join in fixture teardown. No paid model or real Planning execution is claimed.

Run `dev/run_tests.py --module runtime --area supervision_delivery` with `AMPHORA_TEST_POSTGRES=1`. Preserve the owned database fixture history. B3 owns separate process-death and winner-race acceptance.
