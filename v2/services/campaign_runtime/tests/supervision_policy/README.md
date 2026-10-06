# Supervision policy tests

Pure Runtime-owned fixtures exercise exact decimal bounds, strict scalar types/units, finite choices, immutable canonical policy identity, compiled field eligibility and loop occurrence/ancestor selectors. No database or provider is contacted. Fixtures compile independent small materialization graphs.

Run with `python -m pytest -c v2/dev/pyproject.toml v2/services/campaign_runtime/tests/supervision_policy` from the repository root. Coverage source is the filesystem directory `v2/services/campaign_runtime/src/amphora_campaign_runtime/supervision_policy`.

These tests do not prove admission pinning, runtime membership, policy ceiling consumption, target holds or effective scalar application. Those require the subsequent SQL and coordinator gates.
