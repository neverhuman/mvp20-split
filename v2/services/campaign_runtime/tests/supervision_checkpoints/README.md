# Checkpoint creation tests

Pure tests independently construct concrete materialization observations against a compiled fixture. They check byte preservation, stable per-occurrence identity across global progress, loop/run separation and rejection of policy, field or observation tampering. No provider or scientific outcome is exercised.

Runtime owns this suite. Run `dev/run_tests.py --module runtime --area supervision_checkpoints`; test_storage.py uses explicit AMPHORA_TEST_POSTGRES=1 for retained fixture SQL tests: immutable replay, checkpoint ceiling, real deadline expiry, rollback and append-only grants. Coordinator integration is the next gate.
