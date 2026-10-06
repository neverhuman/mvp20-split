# Evaluation batch tests

Pure test_binding covers exact original request, model/prompt/data binding, stable one-call repetition IDs, whole-suite token/accounting bounds and trusted write grants. test_storage uses opt-in actual PostgreSQL for competing writers, immutable suite replay, changed criteria rejection, scoped reads/grants, service UPDATE/DELETE denial and new-engine replacement. Registration must leave attempt count zero.

Run python -m pytest -c dev/pyproject.toml services/agent_planning/tests/evaluation_batch with AMPHORA_TEST_POSTGRES=1 for SQL evidence. Current Planning0.91 migrator is required; no schema reset and no older migrator. Physical calls and live model acceptance are separate future tests.
