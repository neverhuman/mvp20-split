# Supervision policy tests

Pure Runtime-owned fixtures exercise exact decimal bounds, strict scalar types/units, finite choices, immutable canonical policy identity, compiled field eligibility and loop occurrence/ancestor selectors. Pure tests contact no database or provider. test_storage.py opts into actual PostgreSQL through AMPHORA_TEST_POSTGRES=1; it verifies atomic rollback, exact command binding, append-only grants and reconstruction after connection replacement. Fixtures compile independent small materialization graphs.

Run with `python -m pytest -c v2/dev/pyproject.toml v2/services/campaign_runtime/tests/supervision_policy` from the repository root. Coverage source is the filesystem directory `v2/services/campaign_runtime/src/amphora_campaign_runtime/supervision_policy`.

test_admission.py proves actual admission pinning before Invoke/conversion issuance, original receipt replay without catalog entries, failure rollback and held targets across replacement advancement. Policy ceiling consumption, concrete checkpoint creation and effective scalar application remain subsequent gates.
