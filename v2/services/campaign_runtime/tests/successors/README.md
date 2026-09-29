# Successor tests

Owner: Runtime successor module, BP-04.04/B2. `test_admission.py` covers real PostgreSQL accepted/rejected admission, exact source cuts, duplicate/fresh overlap, original receipts, scoped reads, immutable grants and rollback. `test_boundaries.py` covers incompatible reviewed destinations, a succeeded node retained after cancellation, injected unreconciled attempt state, and authenticated public HTTP through TestClient.

Use `dev/run_tests.py --module runtime --area successors`; explicit `AMPHORA_TEST_POSTGRES=1` uses the owned labeled fixture. These tests must not run concurrently with other installation-wide admission tests. `tests/baseline/test_successor_graph.py` adds source-derived generation 0 followed by generations 1/2 in a new plan/run, comparing independently authored state/seed/parent traces. Scripted Artifact evidence is distinct from real peer acceptance.

B3 process interruption and simultaneous admission passed; V1 installed peers/replacement remains. Coverage reporting belongs to the production successor module README when the B2 gate completes.

B3 verified `2026-09-29 17:45:46`: 116 scoped cases, including four real successor admission contention/kill cases and a killed source controller replaced after six accepted scores. Prior accepted records remain byte-for-byte identical and independent generation/seed/membership traces match. Invalid retained checkpoint/source hash/result association and malformed stored graph values reject. Successor module 104/104 statements and 6/6 branches; retain kernel 49/49 and 26/26, parent-process coverage only. No production fixes. Actual installed new-tool/Artifact/Runtime and replacement acceptance remains V1.
