# Supervisor journal tests

Owns pure immutable origin reconstruction, tampered-byte rejection and bounded repair ancestry. Run with the dev Python: `-m pytest -c v2/dev/pyproject.toml v2/services/campaign_runtime/tests/supervision_journal`. SQL persistence, actor authorization and accepted graph effects require their later gates; these cases do not prove them.

Actual SQL cases in `test_storage.py` require `AMPHORA_TEST_POSTGRES=1` and the labeled retained fixture. Run serially. They apply forward runtime0018; never use older Runtime migrators afterward. Journal races/process replacement and dispatch/effects remain separate gates.

Delivery and response suites require Runtime0.26/runtime0019. They prove lease expiry/fences, immutable receipt/readback history,64-response bound, late captures and rollback. The reserved64th-event fallback remains uncovered because normal delivery reaches16claims first; process races are verified by the explicit installed-worker helper.

`process_worker.py` requires the dev-owned independent helper and its env-only SQL configuration; do not invoke it as an ordinary test. Seventeen workers/two installs/four abrupt terminations preserve exact state with scoped cleanup and no peer-call claim.
