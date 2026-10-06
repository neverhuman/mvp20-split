# Checkpoint creation tests

Pure tests independently construct concrete materialization observations against a compiled fixture. They check byte preservation, stable per-occurrence identity across global progress, loop/run separation and rejection of policy, field or observation tampering. No provider or scientific outcome is exercised.

Runtime owns this suite. Run `dev/run_tests.py --module runtime --area supervision_checkpoints`; test_storage.py uses explicit AMPHORA_TEST_POSTGRES=1 for retained fixture SQL tests: immutable replay, checkpoint ceiling, real deadline expiry, rollback and append-only grants. test_coordinator.py proves actual admission/advance creation, independent ready tool progress, distinct scatter members under a campaign ceiling, and loop materialization holds. Storage tests seed the pre-dispatch transaction directly to isolate storage failure oracles; coordinator tests use production admission.

Versioned scalar tests retain exact original field values/digests, reject field/type/unit mismatch, permit unchanged originals outside adjustment bounds, and reconstruct committed legacy SQL slots without rewriting their bytes or claiming scalar evidence.

`process_worker.py` is an explicit installed-process probe, invoked only by dev/verify_checkpoint_recovery.py. It asserts wheel-origin imports and absent private peers, uses environment-only SQL credentials, and exits deliberately at admission/advance transaction barriers. The controller races initial/replacement installs, checks original receipt/seed/scalar/deadline equality, cancels only its scope and verifies process exit. It is not part of ordinary pytest collection.

`test_fences.py` independently checks selected-read changes versus an unrelated real worker claim, explicit refreshed candidate identity without slot/deadline replacement, an issued worker row behind a ready projection, a forged future loop scope and an inactive ancestor. Actual conversion-opening rejection remains covered by supervision_journal/test_checkpoint_storage.py. Both isolated Runtime installations run the new SQL fence suite via dev/verify_checkpoint_fences.py.
