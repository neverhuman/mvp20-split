# Foundation Verification Tooling

- Status: implemented BP-01 development tooling; no production authority
- Architecture: [Foundation Decisions](../docs/Architecture/System/Foundation_Decisions.md)

## Responsibilities

`export_schemas.py` publishes/checks versioned contract input/output schemas and the authoritative digest manifest in versioned contracts/schemas directories. Tool-owned payload schemas are packaged alongside their kernels and checked by module-local compatibility tests. `check_boundaries.py` inspects production imports and declared dependency edges, rejecting private cross-owner imports, undeclared libraries, cycles and common dynamic-import/path-injection bypasses. It is a static engineering gate, not a security sandbox or complete analysis of arbitrary Python execution. `verify_foundation.py` runs lint, dependency guards, fixture/semantic/API tests and optionally independent wheel builds/installs, then refreshes `docs/Generated/foundation-packages.json`.

This tooling imports private runtime modules only for white-box tests, never as a production dependency. The standalone runtime service and each contract family retain their own package/lockfile. The dev environment is intentionally a test consumer of all registered packages; it is not their deployment environment. Build verification installs each wheel with only its declared dependency closure in a fresh temporary environment and checks that contracts do not acquire API/scientific libraries.

## Reproduce from Repository Root

Use Python 3.12 and uv 0.12.18. One local bootstrap on Windows:

```powershell
py -3.12 -m venv v2/.venv
v2/.venv/Scripts/python.exe -m pip install uv==0.12.18
v2/.venv/Scripts/uv.exe sync --project v2/dev --locked
v2/.venv/Scripts/uv.exe run --project v2/dev --locked python v2/dev/verify_foundation.py --builds
```

On Linux, use `python3.12`, `v2/.venv/bin/python` and `v2/.venv/bin/uv`. Dependency installation may contact the package index; tests make no model/provider calls. Root/source paths remain relative in lockfiles. Preserve mapped-drive spelling on Windows when invoking uv against this NAS checkout; resolving one side to a UNC alias can cause uv to rewrite local dependency paths as machine-specific absolute paths.

For an intentional schema change, run `uv run --project v2/dev python v2/dev/export_schemas.py`, review the schema/fixture/version changes, then run the gate. Verification checks artifacts without silently regenerating changed schemas. Lockfiles are explicitly refreshed with `uv lock --project <package>` when dependencies change. Actual release artifacts require target-platform verification separately.

## Limits and Replacement

Fixtures include no credentials or real scientific data. Pure/local API tests alone do not establish database/process behavior. Explicit PostgreSQL owner suites and independently installed recovery probes supply the implemented scope of persistence, authentication and live fencing evidence. They do not establish cross-service atomic transactions, Rust execution, UI usability or scientific validity. Starlette currently emits a deprecation notice for its httpx test client; tests pass and a test-transport update can follow independently. Do not suppress the warning as proof of compatibility.

Replacing this tooling must retain meaningful failing probes, independent installs and deterministic publication checks. Generated inventory contains paths/versions/public dependencies, not manually asserted implementation success. Baseline integrity tests read three frozen v1 source files to verify hashes and scoring-chain order; no v1 files are modified or executed.

## Granular Verification

`run_tests.py` uses `test_scopes.json` as the source/suite ownership registry. The dev tests own `boundaries/` and `schema_publication/`; contract/runtime tests live alongside their packages. Pytest uses importlib mode so module-local filenames can repeat. The full foundation gate aggregates module tests; it is not E2E.

```powershell
v2/.venv/Scripts/uv.exe run --project v2/dev --locked python v2/dev/run_tests.py --module tools --coverage
v2/.venv/Scripts/uv.exe run --project v2/dev --locked python v2/dev/run_tests.py --module runtime --area graph --coverage
v2/.venv/Scripts/uv.exe run --project v2/dev --locked python v2/dev/run_tests.py --coverage
```

Additional pytest selectors such as `-k stale` are forwarded. Coverage uses the owning source boundary, includes unexecuted package files and measures branches as well as lines. JSON coverage and JUnit cases share `v2/.test-results/<selection>/`; local results are ignored by Git. No arbitrary coverage threshold is imposed in this first baseline. Dev coverage includes the runner but its CLI is exercised by command smokes outside pytest, so that coverage is not inferred from those smokes. Module READMEs record behavioral gaps. Shared wire fixtures remain reusable across languages.

## Disposable PostgreSQL

`postgres_fixture.py start` creates a digest-pinned PostgreSQL fixture with random labeled container/volume names, loopback TCP binding and separate migration/service roles. `verify` proves wrong-role denial and retained rows after container restart. `stop` retains data; `resume` starts and verifies it. `reset` explicitly destroys only the runtime/artifact schemas in the named test database, after checking container and volume ownership labels; migrations must run again. Do not run reset while tests are active. No production database URL is accepted by this helper.

Fixture credentials/state live only in ignored `v2/.test-results/postgres-fixture.json`. They are developer-test credentials, not deployment secrets. Migrations run using owner credentials; application probes connect using restricted service roles. Set `$env:AMPHORA_TEST_POSTGRES='1'` before module tests or the foundation gate to include database evidence. Without opt-in, database suites skip. Clear that environment variable for pure-only runs. The fixture uses a retained Docker volume; production backup and power-loss guarantees require BP-09.

Artifact module selection supports `--module data-artifacts --area publication`, `--area storage` and `--area persistence`; the source coverage denominator remains the full artifact service.

Artifact retention handshake tests have their own selector: `--module data-artifacts --area retention`. These include a scripted authenticated runtime process; the independent paired/recovery acceptance tier separately exercises the actual runtime.

With PostgreSQL enabled, `verify_foundation.py --builds` starts independently installed runtime and artifact wheels outside the source checkout. Runtime public-worker probes use a minimal OS environment with no database credentials; service credentials remain confined to the host. Run these sequentially against the single-campaign fixture. Probe scripts are owned by each service under `tests/acceptance/`; subprocess acceptance is separate from pytest coverage.

The build gate also creates two fresh replacement service environments and runs REC-01..09 through runtime-owned acceptance scripts. Explicit migration subprocesses receive only their owner bootstrap credential; service and HTTP worker environments remain isolated. Recovery evidence includes exact wheel hashes and public IDs under `.test-results/recovery/`. [Operating runbook](../services/campaign_runtime/RECOVERY.md) distinguishes retained-state process replacement from target-host backup/power-loss proof.

Registry PostgreSQL tests explicitly add `registry_migrator`/`registry_service` and the private `registry` schema through `registry_owner` on the already labeled fixture. This does not reset peer state. Registry migrations run only through the explicit owner entrypoint. The legacy reset helper still resets only runtime/artifacts; registry tests use unique scopes. JSON Schema verification installs the format extras so date-time assertions actually run.

BP-03.03 adds explicit public SDK libraries under sdk (only manifests declaring public-client=true expose their root), plus independent tools under tools. Private SDK submodules and tool/service implementations remain forbidden cross-owner imports. Module selectors worker-sdk, numeric-affine and sequence-statistics keep coverage denominators separate; SDK transport/lifecycle areas are independently selectable. Isolated installs execute each tool against its own golden JSON and verify no sibling tool or private service is installed. Fixture image pins in those wheel probes are not deployed-image evidence.

`build_tool_images.py --base <digest-pinned-python-3.12-image> --output <new-local-directory>` builds the two tool images from their locked public closures. Target-platform third-party wheels are downloaded with uv-exported hashes; final images install offline. It verifies actual Docker manifest/config identities, Linux x86_64, non-root/network-disabled goldens and absence of peer service/sibling scientific implementations. It writes a credential-free manifest with image and wheel hashes. Images/tags remain local; the tool does not publish them to a registry. Docker build logs use explicit UTF-8 decoding on Windows.

With the labeled PostgreSQL fixture enabled, `verify_foundation.py --builds --tool-images <manifest.json>` adds the [actual SDK/tool-owner harness](../sdk/tool_protocol/tests/acceptance/README.md) after the existing owner recovery gates. Exact internal image wheel hashes must match the new independent installs. The harness is optional for ordinary foundation package checks and mandatory when claiming the BP-03.03 live worker acceptance gate. Scripted and loopback harness tests remain separately selectable with `--module worker-sdk --area acceptance`; those alone do not establish actual owner compatibility.

For scoped worker acceptance after predecessor migrations have passed, enable the same PostgreSQL opt-in and run `verify_tool_workers.py --images <manifest.json>`. It creates fresh isolated worker/owner installs and exercises the actual public HTTP boundary without resetting the fixture or repeating unrelated owner suites. Failed runs preserve partial public observations; server logs go to files to avoid subprocess pipe backpressure.

Add `--replacement` to the focused worker command for fresh second tool/SDK environments and immutable owner-history comparisons before and after subsequent campaigns. This proves same-release reinstall; BP-03.04 owns new-release registry/replica cutover.

`verify_tool_workers.py --images <manifest> --replicas` selects the integration-owned actual Registry/Runtime/Artifact/two-worker harness. It requires accepted registry migrations as well as runtime/artifacts. `run_tests.py --module tool-replicas` is its separate small public-lock conformance tier. Server cleanup on Windows stops the explicitly owned process tree, including virtualenv launchers, before releasing temporary files.

BP-04.01 introduces `contracts/schemas/v2` for executable graphs, keeping wire-v1 files and URNs unchanged. Schema publication/checking verifies both bundles; manifest wire version and URNs match the bundle. Campaign tests support `--area executable`. A valid executable DTO or manually specified plan example is not proof that a compiler/interpreter exists.
