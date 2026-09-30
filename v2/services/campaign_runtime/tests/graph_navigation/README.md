# Graph navigation tests

Owned by Campaign Runtime's `graph_navigation` module. `test_topology.py` independently specifies authored links with activation IDs deliberately out of graph order. `test_reads.py` exercises actual PostgreSQL snapshots, nested scatter scopes, bounded pages and rejected continuations. `test_http.py` exercises the public ASGI routes, credentials and query validation. Fixture peers supply tool/artifact setup only; these tests make no scientific correctness claim.

Run from the repository root with the configured PostgreSQL fixture: `v2/dev/.venv/Scripts/python.exe v2/dev/run_tests.py --module runtime --area graph_navigation`. Set `AMPHORA_TEST_POSTGRES=1`. Do not run another campaign-admission suite concurrently. Browser and independent package replacement are separate acceptance gates.
