# Winner tests

Runtime-owned actual PostgreSQL tests for one checkpoint winner, exact replay, terminal cancellation, pre-request fallback, immutable permissions, bounded scalar rejection and atomic winner/effect/audit/outbox rollback. Select with `dev/run_tests.py --module runtime --area supervision_winners` and `AMPHORA_TEST_POSTGRES=1`. Synthetic admitted materialization graphs and public capture fixtures prove software behavior only. Coordinator release, actual Artifact publication, process races and provider accounting retain separate gates.
