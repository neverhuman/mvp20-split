# Checkpoint creation tests

Pure tests independently construct concrete materialization observations against a compiled fixture. They check byte preservation, stable per-occurrence identity across global progress, loop/run separation and rejection of policy, field or observation tampering. No provider or scientific outcome is exercised.

Runtime owns this suite. Run `dev/run_tests.py --module runtime --area supervision_checkpoints`; persistence and coordinator tests will follow in this folder under explicit PostgreSQL opt-in.
