# Successor tests

Owner: Runtime successor module, BP-04.04/B2. `test_admission.py` covers real PostgreSQL accepted/rejected admission, exact source cuts, duplicate/fresh overlap, original receipts, scoped reads, immutable grants and rollback. `test_boundaries.py` covers incompatible reviewed destinations, a succeeded node retained after cancellation, injected unreconciled attempt state, and authenticated public HTTP through TestClient.

Use `dev/run_tests.py --module runtime --area successors`; explicit `AMPHORA_TEST_POSTGRES=1` uses the owned labeled fixture. These tests must not run concurrently with other installation-wide admission tests. `tests/baseline/test_successor_graph.py` adds source-derived generation 0 followed by generations 1/2 in a new plan/run, comparing independently authored state/seed/parent traces. Scripted Artifact evidence is distinct from real peer acceptance.

B3 remains responsible for process interruption and simultaneous admission; V1 for installed peers/replacement. Coverage reporting belongs to the production successor module README when the B2 gate completes.
