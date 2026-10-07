# Foundation Verification Tooling

Local catalog delivery: `verify_catalog_installation.py` builds an independent
standard-library-only Deployment closure, runs copied owned tests and exercises
heartbeat replay against the installed Registry and retained local SQL. It takes
an explicit source manifest and Registry interpreter; no migrations, reset or
model calls. Zero-capacity evidence is not worker readiness. `catalog_contract_probe.py`
runs public wire validation in the separate Registry contract closure.

Checkpoint suites use the existing Planning owner with `--module agent-planning
--area checkpoint_input|checkpoint_openai|checkpoint_budget`; do not register those
directories again as overlapping owners. Deployment test folders are included in
the canonical ownership audit, with `deployment-tool-catalog` independently selectable.

[Numeric comparison harness](numeric_comparison/README.md) owns the predeclared BP-08.04 offline equal-attempt-budget benchmark. No paid calls or production authority.

## Current supervisor installation verifier

`verify_supervision_installations.py --output <new-path> --runtime-predecessor <installed-environment> --planning-predecessor <installed-environment>` builds current Runtime/Planning public closures, two installations each, checks peer-private packages absent, runs copied module-owned protocol tests and verifies immutable historical migrations. No SQL or migration occurs. Current installed proof Runtime0.40/Planning0.76:292/292 Runtime cases,109/109 Planning cases (802 total);42 Runtime and32 Planning predecessor migration files unchanged;538 schema files,536 predecessor pins. Policy/checkpoint pure suites are included. Service API/host files intentionally changed, so the old all-production-byte equality scope helper is not the current compatibility gate. Older Planning verifiers forbidding FastAPI predate the explicit Planning HTTP server; do not use them as current acceptance or run their old migrators against new heads. The historical actual owner/restart integration helper remains pinned to Runtime0.33/Planning0.75; do not pass current installations until its successor gate updates those expectations. That evidence was verified by `verify_supervision_owners.py --output <new-path> --installation <passed-supervisor-installations> --data-python <Data0.29-interpreter>`, with AMPHORA_TEST_POSTGRES=1. It runs serially against retained state, no migrations/resets;11 owner-local stages,6 service processes and2 post-commit reply drops. [Fixture boundary](supervision_owner_fixture/README.md) owns cleanup and claim limits.

BP-06.05 adds `qdrant_fixture.py start|verify|stop|resume` for the separately labeled, digest-pinned Qdrant1.19.1 fixture. It binds an ephemeral loopback port, uses a generated API key kept only in ignored `.test-results/qdrant-fixture.json`, and retains its named Docker volume on stop/restart. It never resets PostgreSQL or deletes index state. Root version metadata is public; verification checks a protected collection route with correct and incorrect keys. Source transport checks require `AMPHORA_TEST_QDRANT=1`; absent opt-in is a skip, not actual-backend evidence. Dev fixture ownership tests live in `tests/qdrant_fixture/`; Data protocol tests live in its own `tests/retrieval/qdrant/` folder. Remote/TLS and target-host deployment remain later gates.

BP-04.04 adds a selectable `solver` profile to `build_tool_images.py` and `verify_graphs.py` for the five seed/select/mutate/score/retain tools. The default image profile remains the two legacy numeric/sequence tools. Image builds verify exact offline closures, public descriptor/golden bytes, non-root execution and absence of every sibling tool. Installed graph verification selects only the profile's tools plus independent owner/SDK environments; actual solver execution and replacement evidence is owned by [solver acceptance](../services/campaign_runtime/tests/baseline/acceptance/README.md). Shared public schema identities are deduplicated across tools without treating a local schema file path as identity.

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

BP-05.01 registers Studio as a separate Node runner in `test_scopes.json`. Install its exact local dependency lock with `npm ci --ignore-scripts` in `v2/studio` using Node24. `run_tests.py --module studio --area transport --coverage` (also `contracts` or `page_models`) runs deterministic schema checks, TypeScript build and only the selected Node tests. An unfiltered foundation run executes Python then Studio suites sequentially. Pytest-only trailing flags require a Python module selection. Node coverage is emitted by its own test runner and reflects loaded browser source; it is not Python/JUnit evidence or browser acceptance. `*.test.ts` files under Studio tests have the same one-owner rule as Python tests.

`run_tests.py` uses `test_scopes.json` as the source/suite ownership registry. The dev tests own `boundaries/` and `schema_publication/`; contract/runtime tests live alongside their packages. Pytest uses importlib mode so module-local filenames can repeat. The full foundation gate aggregates module tests; it is not E2E.

```powershell
v2/.venv/Scripts/uv.exe run --project v2/dev --locked python v2/dev/run_tests.py --module tools --coverage
v2/.venv/Scripts/uv.exe run --project v2/dev --locked python v2/dev/run_tests.py --module runtime --area graph --coverage
v2/.venv/Scripts/uv.exe run --project v2/dev --locked python v2/dev/run_tests.py --coverage
```

Additional pytest selectors such as `-k stale` are forwarded when a Python module is selected. Coverage uses the owning source boundary, includes unexecuted package files and measures branches as well as lines. JSON coverage and JUnit cases share `v2/.test-results/<selection>/`; local results are ignored by Git. No arbitrary coverage threshold is imposed in this first baseline. Dev coverage includes the runner but its CLI is exercised by command smokes outside pytest, so that coverage is not inferred from those smokes. Module READMEs record behavioral gaps. Shared wire fixtures remain reusable across languages.

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

Compiler tests use `run_tests.py --module runtime --area compiler`; coverage keeps the Runtime owner denominator and the compiler README reports its focused subset. `verify_compiler.py --images <manifest>` with PostgreSQL opt-in builds/installs separate Runtime, Registry and tools, then fresh replacement Runtime/Registry packages. Its [owned process suite](../services/campaign_runtime/tests/compiler/acceptance/README.md) proves public metadata/schema compatibility and retained plan identity without admission or simulated capacity. It preserves credential-free evidence under `.test-results/compiler-acceptance/` and does not reset the fixture.

BP-04.02 adds `--module graph-runtime` for its independent command/observation package and `--module runtime --area scheduling` for the owned coordinator tests. Migration runtime_0007 preserves fixture defaults while adding graph-owned tables and immutable mode/dispatch fields. Use the same explicit PostgreSQL fixture opt-in; do not reset or parallelize the single-running-campaign suites. Package builds now include the separate graph-runtime closure without changing scientific worker package bytes.

`verify_graphs.py --images <verified-image-manifest>` independently installs Registry, Runtime, Artifact, SDK, two tools and a fresh Runtime replacement. With the labeled PostgreSQL fixture opt-in it runs the [installed graph acceptance](../services/campaign_runtime/tests/scheduling/acceptance/README.md), checking real outputs, branch projections, iterations/scatter, replacement, lost completion receipt recovery, autonomous polling and artifact confirmation. Run serially with campaign suites; worker/compiler subprocesses receive no owner SQL credentials.

`verify_graphs.py --profile bindings --images <verified-image-manifest>` selects [typed binding acceptance](../services/campaign_runtime/tests/bindings/acceptance/README.md): real producer/scatter/gather/consumer feedback, Artifact finalization interrupted before Runtime acceptance, fresh owner replacement, original publication receipts and confirmed retention. Binding publishers receive explicit Artifact upload/finalize/read grants as well as retention; those grants are test configuration, not implicit production defaults.

Add `--profile waits` for [installed external-wait acceptance](../services/campaign_runtime/tests/waits/acceptance/README.md): a separate synthetic issuer publishes actual Artifact evidence and submits authenticated domain receipts; open and closed waits, original replies and retained results survive fresh Runtime replacement. This uses the same independent package installations but a distinct scenario/evidence directory. Issuer/compiler subprocesses receive no owner SQL credentials.

`verify_studio.py` rebuilds Studio in a verified temporary directory outside the checkout using exact npm locks and only its own source/tests/scripts plus ten observation and fourteen authoring public schema roots. It records source/schema hashes and owned test results under `.test-results/studio-isolated/`; this is independent consumer build proof, not browser/backend acceptance.

Studio actual-owner acceptance: `verify_studio_integration.py --images <accepted-solver-image-manifest>` creates two independent Node builds and invokes the installed observation/solver peers through a dedicated Studio controller. Set `AMPHORA_TEST_POSTGRES=1`; do not run competing campaign-admission suites. The default observation adapter keeps read-only owner credentials outside Chromium. Add `--authoring` for real-owner draft save/validation/replacement and a separately authorized emergency cancel; all owner credentials stay server-side. [Owned boundary and reproduction](../studio/tests/integration/README.md). This is separate from Node unit tests and scripted browser-peer acceptance.

Source-loop acceptance: with AMPHORA_TEST_POSTGRES=1, run `python v2/dev/verify_acquisition.py --output v2/.test-results/<new-run-directory>`. It builds both owner closures twice, installs Data and Research into separate environments without peer implementations, and runs scoped acquisition/rights/Research suites through actual HTTP and retained PostgreSQL. Four Data interruption cases use a separate replacement installation; Research question/need history is read again after its independent replacement. The output directory must be new; manifests retain wheel hashes and exact fixture identities. Test-only peer/interpreter overrides never become production configuration. Run this gate sequentially with other PostgreSQL suites.

Knowledge acceptance: with AMPHORA_TEST_POSTGRES=1, run `python v2/dev/verify_knowledge.py --output v2/.test-results/<new-run-directory>`. It builds Knowledge/Data/Research public dependency closures twice and installs six isolated environments. Knowledge excludes both peer implementations; packaged migrations and exclusion of test barriers are checked. The initial owner runs its complete owner/contract suites; the replacement runs API/rebuild/acceptance suites. Actual peer HTTP and four crash/race scenarios use the retained fixture, exact identities and original receipts. Every suite must have0 failures/errors/skips. New output directories preserve prior manifests and wheel hashes; run sequentially with PostgreSQL suites.

DER-01 extends `verify_knowledge.py` with separate public-SDK producer installations, full installed Data tests and replacement lineage tests. The actual Knowledge/Data handoff uses a test-owned SDK subprocess; it drops committed POST acknowledgements and verifies receipt-first resume, Data/Knowledge restart and revoked-source payload denial. Eight installations exclude peer service implementations. This does not install the SDK into Knowledge or implement its durable publication workflow.

Research assessment resolution: with `AMPHORA_TEST_POSTGRES=1`, run `python v2/dev/verify_research_assessment.py --output <new-output-directory> --data-python <installed-data-python> --knowledge-python <installed-knowledge-python>`. It independently builds/installs Research's public dependency closure, verifies peer implementation exclusion, then runs Research/contract tests including actual peer publication/resolution. Existing compatible installed Data/Knowledge environments are reused; their versions and Research wheel hashes are recorded. It does not rerun unrelated Knowledge crash/replacement suites. Output directories must be new; PostgreSQL tests run sequentially and never reset the retained fixture. Assessment persistence, public submit API, receipt publication and Runtime acceptance are outside this bounded verifier.

`verify_knowledge_corrections.py --output <new-directory>` builds and independently installs Knowledge's public dependency closure, rejects peer implementation imports, and runs module-owned correction/publication plus Knowledge contract tests against the explicitly opted-in retained PostgreSQL fixture. It records wheel hashes and test totals. Publication peers in this bounded verifier are synthetic protocol fixtures; it does not replace the actual peer/process recovery gates in verify_knowledge.py or B2.04/B3.

Research's actual correction-transition fixture now requires a Knowledge peer implementing the correction grants/endpoints (verified0.15.0). For verify_research_assessment.py, select the independently installed knowledge-correction-installed-20261002/environment interpreter, not the older0.13.0 publication-only peer. This adds actual owner HTTP transition/replacement/offline proof; Runtime consumption remains its own integration gate.

`install_runtime_receipt_peer.py --output <new-directory>` builds an isolated Runtime closure and records package hashes/import isolation, without claiming integration acceptance. Set AMPHORA_TEST_DOMAIN_RUNTIME=1 and AMPHORA_TEST_RUNTIME_PYTHON to that environment when running verify_research_assessment.py with actual Data/Knowledge peers. The actual fixture then verifies owner receipts, Runtime pins, real Artifact protection and replacement. PostgreSQL suites remain serial.

BP-06.03 replacement tooling: install_owner_peer.py builds an explicitly selected owner/public dependency closure into a new directory and rejects configured peer implementation imports. install_runtime_receipt_peer.py preserves the Runtime entry point; install_research_replacement.py builds Research separately. Installation manifests deliberately say installed, never acceptance. Set AMPHORA_TEST_RESEARCH_REPLACEMENT_PYTHON for the actual Research fixture to switch to that distinct interpreter after immutable correction/publication history exists. Public replay, including Data-offline replay, is the acceptance assertion; a second installation by itself is insufficient.


The Qdrant generation replacement probe retains a second labeled fixture under ignored `.test-results/qdrant-replacement-fixture.json`. It temporarily selects that file only within the test helper context; primary state remains unchanged. Both named volumes are preserved. Source-harness runs set `AMPHORA_TEST_QDRANT_PYTHON` to an independently installed Data interpreter; the fresh probe runs with `-I`, checks forbidden peers are absent, receives only owner credentials via environment, and emits public identities/scores. Installed-harness runs may use their own isolated interpreter. This verifies owner-module reconstruction and actual backend effects, not generation HTTP (B2.04).

## Planning owner verification

`verify_planning.py --output <new-evidence-directory>` requires explicit `AMPHORA_TEST_POSTGRES=1`. It builds the Planning public dependency closure, installs two isolated owners without private peers, copies tests without bytecode, runs explicit migration/owned suites and four fresh journal processes. Only Planning migrator/service URLs enter isolated fixture environments; process probes receive service credentials only. Evidence retains wheels, constraints, test XML, exact request/observation hashes and scoped limits. No reset, live provider call or budget-dispatch authority is implied.

Planning process recovery: `AMPHORA_TEST_POSTGRES=1 python dev/verify_planning_recovery.py --initial <installed-python> --replacement <installed-python> --output .test-results/<new-directory>` requires two compatible Planning installations at schema planning_0004. It uses only the service role, copies owned tests outside source, exits subprocesses abruptly at five committed boundaries, and verifies exact retained history, conservative charges and synthetic call markers. It does not reset fixtures, apply migrations or simulate a real provider network.

Planning extraction/publication verification: verify_planning.py now installs Planning0.15 with public SDK0.2, verifies migration0007/content schema resources and runs403 owner/contract cases plus16 process stages (17 with --legacy-manifest). It does not reset retained fixtures. Planning<=0.13 migrators must not touch0007.

`verify_planning_publication.py --output <new-directory> --installation <passed-verify_planning-directory> --data-python <installed-Data0.29-python>` uses the fixture helper planning_publication_fixture.py and owned acceptance/publication_probe.py. Requires AMPHORA_TEST_POSTGRES=1 and a retained compatible Data schema. It creates public synthetic inputs/source/conversion provenance, publishes an interpretation Artifact, exits installed workers at four durable/remote boundaries, replaces Data and checks current rights/terminal receipt behavior.20 Planning processes/2 Data processes; own-role URLs and bearer secrets enter only process environments. Readiness is bounded30s, workers60s, and probe lease8s expires naturally without control-table edits. Run PostgreSQL gates serially. Fixture host config contains environment variable names, never credentials. Output directories retain exact evidence, not production or scientific readiness claims.

Planning edit-profile verifier2026-10-04 05:57:15:verify_planning.py now requires both prompt resources and runs the optional edits profile through failed/repair/replay processes. Planning0.16/public0.6 independent acceptance429 tests and20 process stages with legacy manifest (19 without). Old task/observation history remains unchanged; no new migration.

Planning Knowledge reads verified 2026-10-04 06:45:26: verify_planning.py builds0.18/public0.6 and checks497 owned cases plus20 process stages with legacy history. `verify_planning_knowledge.py --output <new-directory> --installation <passed-verify_planning-directory> --knowledge-python <installed-Knowledge0.17-python>` requires AMPHORA_TEST_POSTGRES=1 and runs serially after other PostgreSQL suites. planning_knowledge_seed.py executes only in the independent Knowledge environment with its service role, creating a declared synthetic accepted read fixture; Planning workers receive only a public endpoint/token.8 installed Planning workers and2 Knowledge hosts prove exact historical reads after a new head/restart, future revision selection, genesis discovery and denied/missing records. No migrations, resets, Data rights checks or Planning-proposal acceptance are implied. The older publication verifier remains pinned to its B1 Planning0.15 baseline.

## Research declaration replacement proof

`verify_research_declarations.py --output <new-retained-directory>` builds the Research0.34 dependency closure, installs two isolated owners and runs module-owned declaration/identity/API/storage tests plus unchanged public contracts. AMPHORA_TEST_POSTGRES=1 is required. It exercises actual HTTP process death before registration commit and after commit/before reply, then exact retry on the second installation. No peer implementations are installed. Research0013 is forward-only; never reuse <=0.33 migrators on this fixture. The earlier0012 optional pre-migration backfill oracle is explicitly excluded because its old-head fixture cannot be recreated by downgrading retained state. Manifest, wheel hashes and test reports remain in the named directory; no reset or deletion occurs.

Planning result producer verification (BP-07.02/B2.03b.ii.c, verified): verify_planning_result_data.py --output <new-directory> --installation <verified-Planning0.27-directory> --data-python <installed-Data0.29-python> configures separately pinned feedback/answer profiles and exercises real Data processing rights, uncertain PUT recovery, terminal replay, bounded repair production and proposal-only answer publication. Run PostgreSQL gates serially. The provider and graph profile are synthetic; actual Research/Knowledge handoff remains a later gate. Secrets stay environment-only; retained fixtures are never reset.


Combined Planning owner acceptance (verified 2026-10-04 15:50:14): `verify_planning_owners.py --output <new-directory> --installation <verified-Planning0.30-directory> --data-python <installed-Data0.29-python> --research-installation <verified-Research0.34-directory> --knowledge-installation <verified-Knowledge0.18-directory>`. Requires AMPHORA_TEST_POSTGRES=1 and serial PostgreSQL execution. Uses initial/replacement interpreters, actual public fixture publication and separate scoped credentials; no peer-private imports, migrators or resets. Knowledge replacement includes a deliberately unavailable Data endpoint for exact pending-intent recovery. Nine Planning workers/six owner hosts; synthetic source/provider data, not scientific acceptance. The service-owned [acceptance README](../services/agent_planning/tests/acceptance/README.md) distinguishes existing scripted proofs.


Synthetic Planning semantics (verified 2026-10-04 16:15:15): `verify_planning_semantics.py --output <new-directory> --installation <verified-Planning0.30-directory>` snapshots module-owned tests, uses both installed interpreters and emits identical split/category review reports.88 tests each; no PostgreSQL or peer host needed. Existing wheel isolation is required; scientific labels are explicit coding-agent synthetic reviews, not machine entailment or live model performance. Original corpus bytes remain unchanged.


Actual Planning failure proof (verified 2026-10-04 16:44:01): `verify_planning_failures.py` takes the same output/installation/peer arguments as `verify_planning_owners.py`. It reruns the base proof, then exits two installed Planning workers at named durable/remote boundaries and waits genuine120s leases; do not run other PostgreSQL suites concurrently. Per-boundary JSON survives later control failures. Nineteen workers/six owners, public conflicting-span/false-digest/grant negatives and no state reset. The base verifier retains its default behavior; the optional extension owns crash claims.


`verify_planning_context.py --output <fresh-path>` builds the current Planning dependency closure and runs public Planning contracts, context/campaign_context/campaign_research_access/research_view_access/registry_access/metadata_reads/runtime_metadata/campaign_data_access/source_access/retrieval_access and legacy Research/Knowledge transport tests in one independent installation. AMPHORA configuration is removed; loopback HTTP is used, with no migration, SQL or actual owner service processes. This is the pure context acceptance tier, not full Planning replacement or actual-owner proof. Existing output directories are rejected.

`verify_planning_campaign_research.py --output <fresh-path> --installation <passed-Planning-context-install> --research-python <Research0.34-python>` verifies actual Research record/view reads from isolated Planning0.34 workers. Set AMPHORA_TEST_POSTGRES=1. The companion owner-local seed prepares synthetic fixtures in a fresh retained scope; no migrator/reset or Data/provider call occurs. Denied/foreign/partial reads, explicit continuations, owner restart and future-only revisions remain separate from scientific acceptance. Never reuse older Research migrators on0013.

`verify_planning_context.py --output <new-directory> --scope proposals` builds an isolated Planning/public-contract wheel closure and runs only proposal policy, typed campaign output, provider compatibility, pure journal reconstruction and Planning contract tests. The default context scope retains its existing broader reader/packet verification. Both modes copy module-owned tests outside source, prohibit private peer implementations/FastAPI, and perform no migration or SQL operations. Use the proposal scope for BP-07.03/B2 policy changes; keep actual-owner/SQL acceptance separate.

`verify_planning_context.py --scope compiler --output <fresh-path>` isolates current decision, authoring, exchange, eligibility, refresh and handoff preparation modules plus public Planning contracts. This focused tier avoids repeatedly collecting unchanged legacy providers and proposal-reader tests; their previous evidence remains retained. Like the other scopes, it copies all helper modules, excludes peer implementations and performs no SQL or migration. Follow with the dedicated installed-origin SQL verifier when changing stored campaign handoff origin.

Compiler owner compatibility: `verify_planning_compiler_owners.py` consumes a passed Planning0.61 compiler installation plus explicit Runtime0.20.2/Registry0.1 Python paths, requires AMPHORA_TEST_POSTGRES=1, and uses a fresh output directory. Three isolated worker stages/four owner processes prove exact save/validation/resolve replay and new-check rejection after drain. Synthetic Linux deployment metadata only; no worker/provider launch, migrations or reset. Tests are module-owned under agent_planning/tests/acceptance/test_compiler_owners.py.

`verify_planning_context.py --scope dispatch` installs the current Planning wheel and runs public Planning contracts plus campaign_dispatch, campaign_authoring and campaign_eligibility. Use for new pure outgoing-journal values; cite the unchanged compiler/client proof separately. This keeps the independent pytest process within its120-second limit as suites grow; it does not replace required SQL or actual-owner recovery tests.

`verify_planning_compiler_origin.py --area selection` runs copied campaign origin and dispatch-storage SQL suites in a passed current compiler/dispatch wheel installation. It rejects old package versions before migration, uses retained PostgreSQL credentials through environment only, and never resets the fixture. Planning0014 requires Planning0.66 or newer migrators. Each module-owned test file runs serially in a separate bounded120s subprocess; XML reports and counts are aggregated. Default `--area origin` preserves the original narrow origin suite.

`verify_planning_context.py` runs each selected module-owned area serially in its own120s subprocess and aggregates reports. `verify_planning_declaration.py` uses a passed Planning0.67 compiler installation and Data0.29 to publish fixed v2 bytes, process-read original roots, build original request/preparation/review and verify exact restart replay. It starts only owned hidden processes, uses environment-only credentials and no migration/reset. The module-owned acceptance probe is copied over the installation test support.

`verify_planning_compiler_origin.py --area coordinator` runs only module-owned campaign_dispatch_coordinator SQL suites in a passed current compiler/dispatch installation. Each file has its own120s subprocess; synthetic peer responses do not establish actual HTTP-owner recovery.


Coverage checkpoint (BP-07.04/B2.01b.iii): use filesystem source directories, as the owned run_tests.py selectors do. The dotted leaf --cov=amphora_agent_planning.supervision_api.app reproducibly triggered SQLAlchemy Cython InternalTraversal initialization errors before SQL tests; the same tests passed without coverage and with --cov=services/agent_planning/src/amphora_agent_planning/supervision_api (relative to v2). No application/dependency workaround was applied. Full path-based API run24 cases passed; CLI subprocess coverage remains separate.

`verify_checkpoint_recovery.py --output <new-path> --installation <passed-current-installations>` proves Runtime0.40/runtime0023 admission/slot crash recovery and same-command races using two installed environments. Requires AMPHORA_TEST_POSTGRES=1, performs no migration/reset, uses env-only credentials and retains cancelled scoped history.14 process runs,2 abrupt exits, exact original receipts/slots after replacement and cancellation; all owned launcher/worker PIDs checked exited. No provider/request/effective scalar execution claim.

`verify_checkpoint_fences.py --output <new-path> --installation <passed-current-installations>` runs Runtime-owned actual SQL freshness/membership/issuance cases from both isolated Runtime0.40 installations. Source tests/dev fixture helpers are exposed; production imports stay wheel-owned and peer-private packages absent. Requires AMPHORA_TEST_POSTGRES=1; retained state, idempotent current migration-to-head only. No automatic request/effect acceptance is inferred from a refreshed candidate.


verify_supervision_installations.py now verifies the explicit checkpoint effect profiles:542 schemas preserve538 predecessors. It copies public schemas and owner tests only, adds pure scalar selections and Planning checkpoint capture tests, and checks historical migrations from explicitly supplied prior installations. No SQL or migration occurs in this helper.

`verify_checkpoint_decision_read.py --output <new-directory> --retained <actual-owner-proof-directory> ...` installs current isolated Runtime with locked dependencies and reads the retained evidence's exact winners through fresh read-only HTTP hosts and replacement processes. Uses existing owned Runtime SQL via environment-only credentials; no migrations, provider calls or peer-private imports. Replacement uses fresh loopback ports; original history/config remains fixed. It is a focused additive-read verification, not a replacement for the earlier execution integration tier.

OpenAI engineering evaluation: prepare_openai_evaluation.py freezes immutable versioned bundles; openai_evaluation_bundle.py verifies hashes without credentials. run_openai_evaluation.py defaults to read-only; --execute supports only v1/v2/v3/v4 under one cumulative $1.30 full-reservation ceiling and original SQL issuance. v4 supplies the typed Research question missing from previous campaign fixtures; allfour full reservations remain counted. Key is external env or owner-named SSOS.env; no arbitrary environment import. Provider diagnostics retain only closed metadata. No automatic retry,upgrades or reservation refunds. Corpus feasibility tests exercise real OutputProfiles policy before further paid calls.

verify_evaluation_installations.py --output <fresh-path> installs two independent Planning closures, runs130selected module checks in each and replays allfive original live histories with SQL read-only transactions. No API credentials or migrations; no live calls. Worker belongs to agent_planning/tests/evaluation_execution/replay_probe.py. OpenAI runner now includesv5 under cumulative$1.70cap; allfullreservations$1.65888.


## Numeric graph and image verification

`verify_numeric_graph.py --output <new-directory> [--recovery]` independently installs Runtime, Artifact, numeric search, synthetic evaluator and SDK controller and exercises actual public HTTP against the explicitly opted-in owned PostgreSQL fixture. Scope, evidence and limitations live in Runtime tests/numeric_search/acceptance/README.md. Failed and successful runs retain their own directories; no reset or history deletion is performed.

`build_numeric_images.py --base <digest-pinned-python-base> --output <new-directory>` builds the separate numerical and evaluator Linux/amd64 images from locked offline wheel closures. It verifies four numeric capability profiles plus the evaluator, schema hashes, nonroot execution and absence of sibling/private owners. `numeric_image_golden.py` owns fixed-box arithmetic and the public CLI seed/expand/evaluate/collect/vary chain, including duplicate suppression and exact draw counts. Image Artifact references are fixture metadata; actual authorization/retention is a separate HTTP gate. The first BP-08.02/V1 run passed; see docs/Audits/Evidence/BP-08-Search/Images.json. Current-release Registry/HTTP independent replacement passed separately; see Registry_Replacement.json and Eligibility_Requalification.json in the same evidence directory.


The numerical HTTP verifier additionally accepts `--images <numeric-image-manifest> --replacement`. It installs Registry when image pins are supplied and builds fresh Runtime/numeric/evaluator replacements when requested. Image-to-installed local wheel equality and original-to-rebuilt wheel equality are required before execution. Registry registration/activation is distinct from deployment and capacity. Combine with `--recovery` to exercise the replacement tools on a second campaign after original-history checks.

`verify_candidate_handoff.py --output <new-directory>` independently installs Runtime/Data/Research, three synthetic representation operators and an SDK-only controller. It proves actual graph-worker Artifact handoff, candidate declaration/read/retry, retention and Research restart followed by Data-principal removal. Requires owned PostgreSQL opt-in and Research0.35/research_0014 already migrated. No migration/reset, paid model calls, built-image or Registry/deployment claim. Research tests/candidate_registration/acceptance owns cases and retained evidence.

## Topology handoff verification

`build_topology_images.py --base <digest> --output <new-directory> --installs <preserved-owner-installs>` qualifies exact old0.2/new0.3 numeric-affine wheel closures with offline arithmetic/schema/nonroot/isolation checks. `verify_topology_handoff.py --output <new-directory> --installs <owner-installs> --runtime <runtime-install> --benchmark <report> [--images <manifest>] [--replacements <fresh-installs>]` drives Planning-owned public acceptance. Explicit owned PostgreSQL opt-in and already migrated owners are required; no migration/reset or provider call. Controller cannot import private implementations/SQL; only owner processes receive scoped SQL URLs in environment. Original benchmark and handoff are retained Data artifacts. Image pins do not imply deployed Linux workers. Source/test ownership remains Planning tests/topology/acceptance; Runtime combined-admission process tests remain under definitions.

Verified 2026-10-06 19:54:31: BP-08.05 build_recovery_images.py qualifies numeric/evaluator images plus the exact reconstructed test adapter, compares local wheel closures to independent installs, supplies reviewed descriptors through copied stopped-container configuration, and runs offline goldens/nonroot/private-import probes. The NAS path cannot be Docker-bound on this host; no production deployment configuration is changed. Recovery consolidation remains owned under tests/integration/search_recovery.

BP-09.01 verify_local_preflight.py uses the owner-selected local host, exact retained Runtimewheel hashes, owned disposable storagefiles, loopback sockets and environment-only preflight credential; it does not install services. verify_deployment_profile.py installs the deployment package independently, compares originalprofile/CLI output, repeats hostprobes and runs ownedtests. Both preserve explicit target/normal-operation limits.

`verify_local_stores.py` verifies the dedicated LOCALAPPDATA/Amphora/local-v2/installation deployment: actual restricted database identities, Qdrant authentication and non-destructive repeated provisioning. It performs no owner migrations and suppresses credential-bearing driver errors. Evidence is written to the root .test-results/local-stores-20261006a.

`verify_local_lifecycle.py` and `verify_supervisor_commands.py [fresh-output-directory]` exercise actual selected-host routing, independently installed Registry failure and repeated/explicit process commands. They intentionally use invalid Registry configuration and claim no serving readiness. Process handles/jobs own cleanup; control credentials are protected locally and never printed.

BP-09 local infrastructure helpers: compose_local_readonly.py creates a fresh nonsecret configuration directory with read-only principals; check_local_readonly.py invokes the five installed public startup-check CLIs; verify_local_readonly.py starts six isolated owners plus gateway through authenticated supervisor control, checks HTTP, force-stops and shuts down. No model calls or campaign admission. migrate_local_owners.py explicitly migrates only the dedicated demo database using original six installs; newer migration releases require a forward plan. probe_planning_host_role.py qualifies serving identity without printing credentials. Retained outputs are evidence, not a running demo.

B2.02 adds --drain and --dependency-failure to the local verification driver. --registry-evidence requires a newly composed manifest with that flag; it permits only dormant synthetic descriptor registration and proves original receipt replay across outage, never activation/deployment. repair_local_store_ports.py performs the explicit dedicated dynamic-port forward repair once, preserving stopped baseline containers and volumes. The physical Windows Store Python installation is under LOCALAPPDATA/Packages/PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0/LocalCache/Local/Amphora/local-v2; Python transparently redirects its logical LOCALAPPDATA/Amphora path. PowerShell inspection must use the physical path.

B3 helpers: verify_local_capacity.py launches the independently installed Data owner with a fresh scoped eight-byte quota, publishes native bytes, rejects excess reservation, verifies original receipt/bytes and loopback/auth denial, then drains. This is service quota exhaustion, not physical disk filling. check_local_readonly.py --wrong-role verifies five owner startup CLIs using the correct migrator credentials; Planning role rejection has separate installed-host evidence. verify_local_profile.py binds current installed wheel identities to the CPU-only local profile and invokes isolated Deployment validate/preflight. Model failure simulation lives under Planning tests/openai_provider/unavailable_probe.py and uses a test-only loopback connection factory, never provider credentials or external calls.

verify_native_workers_installation.py independently installs Deployment, copies its owned tests and runs verify_native_workers.py with separate installed Runtime/Planning owners. Empty synthetic scope, disabled provider, unchanged local journal/vault, actual worker sweeps and API drain guard/quiescence. No scientific tool or campaign claims. It requires explicit prior owner manifest, Registry interpreter and Planning installation; no owner migrations or fixture resets.

verify_scientific_turn_installation.py installs Deployment independently, copies owned tests and runs verify_scientific_container_turns.py using exact evolution0.5 image ID, explicit physical NTFS bundle path and public TLS certificate. Two real-container lost-reply probes use synthetic503 upstream and expected exit3; no actual owner eligibility or model call. Only exact exited probe containers are removed, without volumes.

verify_scientific_controller_installation.py installs Deployment independently, runs its copied tests, then verify_managed_scientific_workers.py (actual local Runtime/Data/TLS/Linux unknown-campaign denial) and verify_scientific_monitor_recovery.py (actual monitor-job death while parent TLS fixture stays available; replacement adopts same container). Credentials remain environment/DPAPI only; no migrations, campaign admission or provider calls. Retained local journals must be released before migration; synthetic denial is not tool eligibility.


## Local integrated demonstration probes

`verify_managed_campaign_installation.py` builds an isolated Deployment closure and
runs copied Deployment tests plus `verify_managed_numeric_campaign.py` against the
existing qualified local owners and Linux scientific images. The fixture binds the
Runtime-returned run ID by a graceful restart with new immutable worker configs.
Its oracle checks canonical completions, output bytes, numeric checkpoints and actual
Data retention confirmation; worker exit codes alone never establish success.
`verify_local_retention_recovery.py` drains a named completed campaign backlog without
rerunning science or altering its graph. Raw scoped evidence stays in `.test-results`;
reviewed summaries live under docs/Audits/Evidence/BP-09-Deployment.

`verify_owner_records_installation.py --output <fresh-directory> --source-manifest
<local-owner-manifest>` independently installs Deployment and copies only the public
fixture and four dev helper scripts. It invokes `verify_local_owner_records.py` to
create synthetic Data source/conversion records, Research declarations and a grounded
Knowledge hypothesis, rebuild its accepted log and prove exact three-owner restart
replay, scope denial and immutable-declaration conflict. RecordsController owns only
its exact Windows process job; normal shutdown drains each owner. It keeps root stores,
original byte storage and prior scopes intact. No SQL seed, migration, provider key,
paid call or scientific efficacy claim belongs to this probe. These process acceptance
oracles are separate from owner-local pytest coverage. Failed outputs and scoped
records are retained; a fresh output directory never means resetting the database.

`prepare_local_checkpoint.py` publishes synthetic objective/prompt/budget artifacts
through Data and creates new immutable Runtime/Planning/native worker configurations.
Owner-local exporters compile inside their installed environments without SQL or keys.
`verify_local_live_checkpoint.py` runs the actual supervised graph with one request and
one provider attempt; the previously authorized external key is held only in memory
and the Planning worker environment. Existing project reservations enforce the shared
six-call/USD0.50 ceiling. Preserve the original admission and fallback evidence on failure;
never retry a failed engagement as though it had a different model/input profile.
`inspect_local_checkpoint.py` restarts owners without workers or credentials for a
read-only comparison of original graph/admission/response and actual artifact bytes.
Planning0.102's explicitly selected compact profile retains the original wire profile
and limits. This scalar checkpoint proves real model acceptance, usage and replay;
scientific execution and Research/Knowledge context composition are separate gates.

`prepare_local_integrated.py` reads exact public Research/Knowledge records, publishes
a bounded synthetic context projection and composes immutable six-owner scientific
and supervision configurations. Runtime's numeric-search test exporter compiles the
seed invocation checkpoint without SQL or provider access. Scientific inputs remain
the reviewed fixture's structured artifacts; a model abstention can continue unchanged.
`verify_local_integrated.py` measures the actual required packet before starting
Planning. Default mode cancels after this zero-call preflight. `--key-file` permits
one bounded live attempt; `--science-only` instead runs a separate unsupervised graph
under the same six-owner configuration without loading a key. Preserve every admitted
run, including failures. Registry setup reads existing lifecycle state and never
silently reactivates a drained/revoked release. Fresh scientific worker bindings use
a graceful stopped-configuration transition and the original admission receipt.
`inspect_local_integrated.py` reads retained supervised outcomes through five owners
without workers, confirms original graph/admission/context and inspects model usage,
actual output bytes and retention. A successful readback does not convert failed
invocations into scientific success. The integrated oracle still requires15 canonical
successful invocations,6 evaluations,3 selection checkpoints and confirmed outputs.

`verify_local_browser.py` starts the independently installed gateway and five retained
owners with fresh immutable asset/configuration paths. It supplies a one-use launcher
key only to the browser harness; owner credentials stay gateway-side. Studio's
`tests/integration/local_demo.mjs` verifies desktop/narrow execution and checkpoint
reasoning, keyboard access, accessibility and scoped Research/Knowledge/Data readback.
Gateway drains before owners. No workers, SQL seeding or model calls. This proves
Monitor/reasoning and API history; Design/Explore/successor navigation remains separate.

`prepare_local_authoring.py` creates a new immutable Runtime configuration enabling
existing authoring APIs and Registry discovery, then publishes an explicitly fixture-
authored draft copied from the retained numeric graph. It compares exact public
definition/receipt replay, starts no workers/models, and preserves original histories.
`local_authoring_controller.py` adds optional Registry read lifecycle to retained
owners; gateway drains before Registry and other owners. Local browser proof detects
this prepared profile, opens/validates its exact saved draft and checks local-edit
retention across mode switches. Draft validation is a real owner command, not campaign
admission, scientific validation or model-authored topology.

`verify_registry_access_installation.py` independently builds Deployment, runs its
owned tests and starts actual retained owners through `verify_local_registry_access.py`.
The latter creates a repeatable scoped Runtime/Registry DPAPI sidecar, writes new
immutable owner configurations, proves read/resolve receipt replay and forbidden
activation denial. Current lack of capacity remains an honest rejection. It does
not register/activate tools, start workers or admit campaigns. Original vault and
state stay unchanged. Runtime uses a distinct read/resolve peer, never Registry's
operator credential. Scientific successor admission remains a separate proof.

`verify_local_successor.py` uses exact public carry-source cuts from the retained
scientific run, saves/validates an explicitly fixture-authored tool-free graph, and
invokes the approved graph.admit_draft_successor API. One pure Runtime finish
transition must preserve the carried value hash and original parent history. The
command journal is replayed under the same identity on --resume; payload changes
are rejected instead of retried with a fresh command. This is a lineage/transfer
proof, not repeated science or a claim of improved results. No workers/model calls.

`verify_local_browser.py --successor <directory>` reuses the same scoped gateway
with the selected completed successor. Before browser launch it compares exact
parent/child v3 history after owner restart; the successor browser then checks
public lineage, original admission receipt and retained Artifact bytes. No replayed
execution, workers or provider key is needed for this readback.

`verify_local_evidence_correction.py` journals actual source r2 and Knowledge assertion
revision2 with unresolved synthetic-result interpretation. It verifies accepted-log
rebuild, original snapshot/campaign preservation and exact Research declarations.
Uploads and commands retain their original identities. No lab measurement correction,
scientific assessment or LLM extraction is claimed. A fresh Data configuration enables
its existing acquisition boundary; original profiles and vault remain immutable.
`prepare_local_correction_runtime.py` adds the exact already supported text schema to
a fresh reviewed Runtime universe. Earlier unknown-schema validation stays retained.
`verify_local_successor.py --correction` revalidates the saved draft, pins new source/
knowledge revisions and returns the new interpretation beside the carried original
numeric result. The browser qualifies old/new pinned claims and verified text without
repinning the original campaign. These scripts are integration fixtures, not services.

`verify_local_integrated.py --science-only --interrupt-once` invokes the separate
`local_controller_interruption.py` fixture: one live Linux process, exact owned
supervisor/API/TLS job termination, bounded child-listener teardown, original-turn
migration exclusion/adoption and exact admission replay. It never stops the daemon.
A process recovery pass does not promise campaign success: the retained b probe's
unclaimed seed expired while owners restarted, and the normal15/6/3/15 oracle failed.
Its truthful blocked result remains retained. `inspect_local_failure.py` reads exact
public graph/attempt/completion/receipt history after restart without workers or keys.
`verify_local_idle_resources.py` separately samples five full idle owner process-tree working sets and
control responses, checking1GiB per owner/4GiB combined and0.5s control bounds written
before startup. It records actual Docker capacity; it is not a peak-workload benchmark.
All helpers preserve the original installation/vault, use exact owned process groups,
retain failed probes, and finish with owners drained. Shared-daemon interruption is a
separate approval-scoped runbook because older baseline containers share this daemon.

Shared-daemon drill: `verify_shared_daemon_outage.py` requires explicit outage scope authorization and an exact five-container inventory. It preserves IDs/volumes, restores in cleanup, checks actual bound ports and reconciles one retained managed intent. `--resume-from` resumes the original intent without another outage. Synthetic503 is a lifecycle oracle only. Original/corrected/blocked campaign readbacks use the existing separate helpers; no model calls. Initial ephemeral-port harness failure and qualified recovery are retained in Shared_Daemon.json.

BP-09.04 capture/restore: `capture_local_backup.py` requires stopped owner/control ports and released managed journals, holds the deployment lease, cold-copies only the selected two store volumes and restores their original IDs in cleanup. Exact artifact roots include separately retained historical fixture roots; conflicting immutable keys reject. It snapshots reviewed owner configuration JSON dependencies, selected wheels and protected installation state. `restore_local_backup.py` checks the external manifest digest before new labeled volume allocation, rewraps protected credentials to the new local identity, remaps endpoints/configuration inputs and rebinds only the new target Deployment administrative marker. It enables no workers or traffic. Failed targets/backups remain retained. No host-loss/online consistency guarantee.

`audit_local_catalog.py` invokes the independently installed Data recovery CLI through owner-scoped environment credentials. Deployment never queries the Data catalog. Root-aware original/browser/failure inspection helpers support explicit `--root` for a restored installation while preserving their existing defaults. All restored-history, catalog and pending-retention checks must pass before acceptance; store health and inventory hashes alone are insufficient.
