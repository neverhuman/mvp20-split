# Graph inspection tests

Owner: [graph inspection](../../src/amphora_campaign_runtime/graph_inspection/README.md). Tests use the labeled local PostgreSQL fixture and their own scope; fixture tools/Artifact clients are scripted unless a scenario explicitly names an independently installed peer.

Run from repository root with `AMPHORA_TEST_POSTGRES=1`:

```powershell
v2/dev/.venv/Scripts/python.exe -m pytest -c v2/dev/pyproject.toml v2/services/campaign_runtime/tests/graph_inspection -q
```

| File | Behavior |
|---|---|
| `test_snapshots.py` | Consistent node pages; stale revision; exact scope/frontier selection; canonical report/Artifact summary; contiguous reconnect and duplicate pages; expiry/mode/filter/scope; missing durable revision; paginated collection/missing members |
| `test_attempts.py` | Failed retry followed by canonical success; attempt page order and receipt lineage; cross-activation token and missing-output rejection |
| `test_http.py` | Explicit graph/history opt-in, authentication, HTTP bounds and resnapshot errors; signing-key replacement |

Boundary schema examples/rejection tests live in `contracts/graph_runtime/tests/test_observations.py`. These tests are not process-crash or installed replacement acceptance. Those remain the next BP-04.05 gates. PostgreSQL suites that admit campaigns must run sequentially because the configured profile permits one active campaign across the installation.
