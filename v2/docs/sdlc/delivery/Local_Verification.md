# Local verification runbook

Reviewed: 2026-10-16 14:17:15 America/Chicago. Canonical development process; not evidence of implementation.

Commands are run from the repository root in the authorized workspace. Bootstrap only when needed. Use the existing environment for documentation checks. [Dev tooling](../../../dev/README.md) owns actual helper interfaces and acceptance-harness limitations; [test ownership](../../../dev/test_scopes.json) owns selectors.

Temporary test containers must be removed in a `finally` cleanup after success or failure, using verified fixture ownership. Preserve active demo containers, volumes and explicit recovery state. Stop-only cleanup leaves stale containers. Never use broad prune/reset as test teardown. Retained volumes need separate disposal authorization.

## Reproduce from repository root

Use Python 3.12 and uv 0.12.18. One local bootstrap on Windows:

```powershell
py -3.12 -m venv v2/.venv
v2/.venv/Scripts/python.exe -m pip install uv==0.12.18
v2/.venv/Scripts/uv.exe sync --project v2/dev --locked
v2/.venv/Scripts/uv.exe run --project v2/dev --locked python v2/dev/verify_foundation.py --builds
```

On Linux, use `python3.12`, `v2/.venv/bin/python` and `v2/.venv/bin/uv`. Dependency installation may contact the package index; tests make no model/provider calls. Root/source paths remain relative in lockfiles. Preserve mapped-drive spelling on Windows when invoking uv against this NAS checkout; resolving one side to a UNC alias can cause uv to rewrite local dependency paths as machine-specific absolute paths.

For an intentional schema change, run `uv run --project v2/dev python v2/dev/export_schemas.py`, review the schema/fixture/version changes, then run the gate. Verification checks artifacts without silently regenerating changed schemas. Lockfiles are explicitly refreshed with `uv lock --project <package>` when dependencies change. Actual release artifacts require target-platform verification separately.

## Granular verification

BP-05.01 registers Studio as a separate Node runner in `test_scopes.json`. Install its exact local dependency lock with `npm ci --ignore-scripts` in `v2/studio` using Node24. `run_tests.py --module studio --area transport --coverage` (also `contracts` or `page_models`) runs deterministic schema checks, TypeScript build and only the selected Node tests. An unfiltered foundation run executes Python then Studio suites sequentially. Pytest-only trailing flags require a Python module selection. Node coverage is emitted by its own test runner and reflects loaded browser source; it is not Python/JUnit evidence or browser acceptance. `*.test.ts` files under Studio tests have the same one-owner rule as Python tests.

`run_tests.py` uses `test_scopes.json` as the source/suite ownership registry. The dev tests own `boundaries/` and `schema_publication/`; contract/runtime tests live alongside their packages. Pytest uses importlib mode so module-local filenames can repeat. The full foundation gate aggregates module tests; it is not E2E.

```powershell
v2/.venv/Scripts/uv.exe run --project v2/dev --locked python v2/dev/run_tests.py --module tools --coverage
v2/.venv/Scripts/uv.exe run --project v2/dev --locked python v2/dev/run_tests.py --module runtime --area graph --coverage
v2/.venv/Scripts/uv.exe run --project v2/dev --locked python v2/dev/run_tests.py --coverage
```

Additional pytest selectors such as `-k stale` are forwarded when a Python module is selected. Coverage uses the owning source boundary, includes unexecuted package files and measures branches as well as lines. JSON coverage and JUnit cases share `v2/.test-results/<selection>/`; local results are ignored by Git. No arbitrary coverage threshold is imposed in this first baseline. Dev coverage includes the runner but its CLI is exercised by command smokes outside pytest, so that coverage is not inferred from those smokes. Module READMEs record behavioral gaps. Shared wire fixtures remain reusable across languages.
