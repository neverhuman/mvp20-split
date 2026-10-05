# Supervision scope tests

Pure Runtime tests only. The scenarios distinguish exact occurrence identities, shared-read independence versus read/write conflicts, disjoint runs, relevant state/output/absence changes and unrelated frontier progress. Authority, malformed identity, immutable bytes and explicit size limits are negative oracles.

Run dev/run_tests.py --module runtime --area supervision_scope. These tests do not prove authenticated observation acquisition, stored-plan membership, absence of materialized worker rows, SQL serialization, a checkpoint pause or decision acceptance. Those gates belong to BP-07.04's later Runtime integration and process tiers.
