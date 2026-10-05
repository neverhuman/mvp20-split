# Supervisor API tests

Owner: Runtime supervision_api. Run python -m pytest -c dev/pyproject.toml services/campaign_runtime/tests/supervision_api with AMPHORA_TEST_POSTGRES=1 and PYTHONUTF8=1. Uses retained actual PostgreSQL, unique scopes and FastAPI HTTP routes. CaptureProbe is explicitly synthetic and measures read ordering/denial, not actual Data behavior; supervision_capture owns real protocol probes, B1.04d owns actual installed peers.

Six cases cover receipt replay after fresh processing withdrawal, read-only recovery, unknown history, fresh denial, exact response/cancellation readback, no execution mutation, original actor/scope, changed pending command rejection before fetch, unavailable reader, invalid capture redaction, no default routes and configured Host/env secrets. Legacy body and host regression tests are run alongside. Boundary checks register source/test ownership. SQL migrations never reset retained state; old migrators are prohibited.


owner_worker.py is an explicit installed-process acceptance probe, not ordinary test collection. dev/verify_supervision_owners.py copies and invokes it with --confcutdir and own-service SQL/environment only. Current proof11 stages/6 actual service processes verifies original HTTP recording, two post-commit lost replies, replacement history, current processing-rights denial/regrant and scoped cleanup. Runtime checks byte/timestamp/run-status invariants; Planning checks original intake and zero provider attempts. No migrations/reset or peer-private imports.
