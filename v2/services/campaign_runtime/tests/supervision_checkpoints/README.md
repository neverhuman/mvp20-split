# Checkpoint creation tests

Pure tests independently construct concrete materialization observations against a compiled fixture. They check byte preservation, stable per-occurrence identity across global progress, loop/run separation and rejection of policy, field or observation tampering. No provider or scientific outcome is exercised.

Runtime owns this suite. Run `dev/run_tests.py --module runtime --area supervision_checkpoints`; test_storage.py uses explicit AMPHORA_TEST_POSTGRES=1 for retained fixture SQL tests: immutable replay, checkpoint ceiling, real deadline expiry, rollback and append-only grants. test_coordinator.py proves actual admission/advance creation, independent ready tool progress, distinct scatter members under a campaign ceiling, and loop materialization holds. Storage tests seed the pre-dispatch transaction directly to isolate storage failure oracles; coordinator tests use production admission.

Versioned scalar tests retain exact original field values/digests, reject field/type/unit mismatch, permit unchanged originals outside adjustment bounds, and reconstruct committed legacy SQL slots without rewriting their bytes or claiming scalar evidence.
