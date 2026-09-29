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

Boundary schema examples/rejection tests live in `contracts/graph_runtime/tests/test_observations.py`. B2 adds `test_process_recovery.py` and test-only `activation_probe.py`: three real coordinator process kills with public observation/receipt checks.32 focused and scheduling-process regression cases pass. Independently installed observer replacement remains V1. PostgreSQL suites that admit campaigns must run sequentially because the configured profile permits one active campaign across the installation.

B2 uses one optional probe-script argument in the existing owned coordinator test harness; its default path remains covered by the scheduling-process regression suite. No production crash hook is installed.
