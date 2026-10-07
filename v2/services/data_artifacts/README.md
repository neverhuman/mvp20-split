# Data and Artifacts Service

- Status: DER-01 derived-publication accepted/closed. Baseline: provisional uploads and verified finalization implemented; protective reservation handshake implemented; bounded reconciliation/cleanup sweeps implemented; standalone hosting/scoped reads implemented; BP-02.03 independently accepted and audited; actual runtime integration, REC-01..09 process recovery and independent replacement acceptance passed.
- Package: `amphora-data-artifacts` 0.31.0.
- Architecture: [Artifact publication](../../docs/Architecture/System/Artifact_Publication_Protocol.md), [physical records](../../docs/Architecture/System/Persistence_Record_Design.md).

This independently installed service owns provisional upload records, immutable artifact catalog bindings, protective reservations, command receipts and artifact audit/outbox state. Its [private persistence module](src/amphora_data_artifacts/persistence/README.md) implements migrations and command registration/terminal receipt transactions. `api.create_app(uploads, storage, credentials, outcomes=None)` exposes POST /v1/uploads, PUT /v1/uploads/{id}/content and POST /v1/artifacts/finalize using explicit configured principals and policy. Successful streaming returns a provisional receipt; verified finalization returns ArtifactRef. POST /v1/reservations, /confirm and /reconcile implement the protective handshake with an explicitly configured runtime outcome client. GET /v1/artifacts/{id}, /content and /processing-content require a scoped read grant; /processing-content additionally enforces current source process rights before/after byte I/O, while /content retains read rights; content is integrity checked before response. `amphora-artifacts` provides explicit loopback hosting and bounded maintenance.

Dependencies are public core/command/artifact contracts, SQLAlchemy, psycopg, Alembic, FastAPI, Uvicorn and JSON Schema validation with format support. No runtime source imports, runtime database access, shared repository or scientific dependencies are permitted. Future callers use artifact contracts; runtime outcomes require an authenticated public boundary.

BP-03.03/B1 adds `GET /v1/commands/{family}/{command_id}` for the authenticated actor's original `artifacts.begin_upload` or `artifacts.finalize` outcome. It requires the matching publication action and uses a read-only transaction. Missing/foreign commands return 404; rejected commands remain terminal even after a later successful publication. `PublicationObservation` includes canonical request digest so clients can verify the original request before relying on a recovered result.

`tests/persistence/` owns actual PostgreSQL migrations, scoped binding, immutability, rollback, duplicate-command contention and bounded transaction-retry tests. Run `uv run --project v2/dev --locked python v2/dev/run_tests.py --module data-artifacts` with the explicit fixture enabled as described in [dev tooling](../../dev/README.md). Without opt-in these tests skip; that is not persistence evidence.

A replacement preserves catalog identity, reservation protection, stable command replay and service-owned migration history. Pending uploads are not usable artifacts. Process-kill tests cover finalization before and after catalog commit. Actual public runtime integration passed; target-filesystem power-loss durability remains BP-09. No production storage path, provider or deployment is configured.

## Provisional Upload Modules

[Publication](src/amphora_data_artifacts/publication/README.md) owns authority, capacity and generation transactions; [storage](src/amphora_data_artifacts/storage/README.md) owns bounded immutable attempt bytes. `access.py` maps explicit opaque credentials to principals; no default secret or network startup occurs on import. `api.py` maps safe errors and enforces bounded JSON/stream timeouts. Database failure is retryable infrastructure failure, not scientific rejection.

Run `uv run --project v2/dev --locked python v2/dev/run_tests.py --module data-artifacts --area publication` with `AMPHORA_TEST_POSTGRES=1`; `--area storage` runs filesystem checks, `--area persistence` runs DB primitives, and `--coverage` keeps the full owner source denominator. Cases cover stale processes, body disconnect/cancellation/timeout, quotas, credential/scope errors and path/link rejection. No automatic cleanup or backup guarantee is implied.

[Retention](src/amphora_data_artifacts/retention/README.md) owns protective reservation identity and authenticated terminal proof. Use `--area retention` for its isolated suite; separate-process scripted peer tests do not substitute for actual runtime integration.

[Maintenance](src/amphora_data_artifacts/maintenance/README.md) owns conservative provisional cleanup and bounded reservation sweeps. Use `--area maintenance` for its process-crash and capacity tests. No automatic finalized-content deletion; markers/evidence and lifetime upload bounds persist.

## Executable and Configuration

Install this wheel and its declared public contract dependencies independently. `amphora-artifacts serve --config <local-config.json> --port 8081` binds only 127.0.0.1; no import-time startup or automatic migrations. `python -m amphora_data_artifacts` is equivalent. `check` validates configuration, storage root, service role and required database columns. `/health` is process capability information; `/ready` checks database access. Hosting fails safely if configuration or persistence is unavailable.

[config.example.json](config.example.json) contains environment variable names, a synthetic schema profile and an example administrator-owned storage root, never credentials. Set the referenced variables in the service environment and use an existing local root; tokens require at least 32 characters. The database URL must authenticate as artifact_service, not a migrator. Apply owner migrations explicitly before startup. Optional runtime config has owner, endpoint and token_env; only authenticated configured outcomes may change reservations. Scope/action grants remain explicit. Do not check populated secrets or host configuration into Git.

`amphora-artifacts cleanup --config <path> --actor worker --tenant local --project demo --limit 20` runs one bounded cleanup pass; `reconcile` runs one retention pass for a configured runtime principal. Both return next_cursor; pass `--after` to continue, then wrap for a future pass. An external scheduler can invoke these commands; no hidden background loop runs in the API process. Stop older writer versions before enabling cleanup. Signal termination closes the host engine; persistent SQL/marker state owns recovery.

Each JSON profile may add `schema_path`, relative to the configuration file (or absolute), pointing to an administrator-installed schema file whose exact bytes hash to the profile's `sha256`. Startup validates the bounded self-contained Draft 2020-12 profile; publication validates payloads against it. Install tool-owned public schemas as deployment artifacts; do not import tools into this service. Profiles without a schema_path retain only the existing built-in validators. All replicas must use the same profiles. Unknown profile keys and duplicate profile identities fail configuration. Format/schema validation does not establish scientific correctness or executable tool availability.

The installed-process acceptance probe starts the wheel outside the repository, publishes and replays an artifact, reads metadata/content, rejects wrong credentials/scope and detects modified fixture bytes. It uses real PostgreSQL but synthetic data. `--area acceptance` runs the owner-local probe; the foundation --builds gate repeats it using an independent wheel environment when PostgreSQL opt-in is enabled. Test-only fault barriers are confined to tests. Actual runtime cancellation/acceptance races passed .05/.06; scientific validity remains later plans.

Current protection is observable through owner-scoped `GET /v1/reservations/{id}` without mutation. [Foundation recovery runbook](../campaign_runtime/RECOVERY.md) covers the public handshake, explicit maintenance, retained state and independent replacement; this service alone retains authority over its bytes/catalog/reservations.

## Source Acquisition In Progress

BP-06.01 adds the focused [acquisition provenance module](src/amphora_data_artifacts/acquisition/README.md) and public evidence-contract dependency. Exact-byte scope/span/schema verification and canonical trace fingerprints are implemented as pure domain behavior. Forward migration artifact_0004 now persists source delivery/revision/trace history and atomic source heads. Opt-in staged acquisition routes now expose preparation, finalized-output trace retention and immutable history; current rights/expiry enforcement is implemented in the focused [Source Rights](src/amphora_data_artifacts/source_rights/README.md) module; durable identity observations now preserve lookup history. The Data-owned Research client now resolves exact identities over the public HTTP contracts without peer imports or SQL. Bounded UTF-8 document and synthetic flat-JSON lab preparation now produce exact-span traces and schema-pinned outputs; all lab results stay quarantined. Existing publication/retention commands and schema roots are unchanged. Version0.8.0 adds staged HTTP ingestion and explicit acquisition=true host configuration. Exact source/trace identities provide replay; no new command encoding is introduced. Version0.8.0 adds durable intent/result observations and optional configured Research HTTP lookup. Failed lookup stays pending; exact replay never rewrites old identity knowledge or scientific eligibility.

Version0.9.0 adds artifact_0006 and explicit current-use rights/expiry fences. Content reads enforce them even when acquisition routes are disabled. Historical policy/source/trace/observation records stay immutable; unsupported payload-erasure licensing profiles are not admitted. The rights module README owns the exact retention and fence semantics.

DER-01/D1 introduces private [declared transformation values](src/amphora_data_artifacts/derivations/README.md) and additive public artifact contracts0.2.0. D2 adds immutable declarations, atomic finalization/lineage, current-rights fences and bounded ancestry; D3-D4 accepted; DER-01 closed. Data0.11.0 requires artifact_0007; prior migrations remain unchanged. Focused tests: `python v2/dev/run_tests.py --module data-artifacts --area derivations --coverage`.

DER-01 independent acceptance: Data278 initial and47 replacement tests, SDK94, Knowledge252 initial and41 replacement tests passed. [Scoped closeout](../../docs/Audits/DER-01_Derived_Publication_Closeout.md).

BP-06.03/B1.06 compatibility patch: dependency pins now consume additive Research contracts0.3.0 (Evidence0.5.1/Knowledge contracts0.6.1 where applicable). Existing public schema bytes and owner behavior are unchanged; earlier installed/recovery evidence remains tied to its recorded versions.

BP-06.03/B1.07 compatibility patch: exact pins now consume Research contracts0.4.0 and corresponding Evidence0.5.2/Knowledge contracts0.6.2. The only added wire root is Research synthetic evidence; peer behavior and all294 predecessor schema bytes remain unchanged.

B1.10 compatibility patch updates exact Research0.5.0 contract dependency closure; no owner behavior, migration or existing schema changes.

BP-06.04/B1.04 compatibility release0.11.6 updates exact public Research/Evidence/Knowledge dependency pins only. This release changes no service behavior or migration; earlier actual-peer acceptance remains recorded at its tested version.

BP-06.04/B1.06 compatibility release0.11.7 updates exact public contract dependencies only; no service implementation or migration change. Actual peer evidence remains tied to the recorded tested version.

BP-06.05/B1.01 release0.12.0 adds the private pure [representation domain](src/amphora_data_artifacts/representations/README.md): complete profiles, scoped work identity, canonical finite vectors and a deterministic synthetic encoder. Public contracts, APIs and artifact_0007 are unchanged. Cache storage, source bindings and retrieval remain later milestones.

Acquisition recovery/live-observation harness startup permits 60 seconds after measured mapped-workspace cold imports of 25.33s (editable) and 25.09s (independent wheel). This changes only test host readiness budgets; operation deadlines, crash barriers, immutable-replay assertions and production timeouts are unchanged.

BP-06.05/B1.02 release0.13.0 consumes public representation contracts0.1.0 and adds explicit profile/vector wire mappings. Internal profile, scope, byte and digest consistency remain Data-owned. No representation API, persistence migration or source binding is implemented by this contract milestone.

BP-06.05/B1.03 release0.14.0 adds the private [profile registry and computation cache](src/amphora_data_artifacts/representations/storage/README.md), with artifact_0008 and DB-clock lease/fence authority. Cached results remain internal; source bindings/publication, hosted APIs and retrieval are later milestones. Existing source/Artifact records are not rewritten. Data<=0.13.0 must not run migrations against artifact_0008.

BP-06.05/B1.04a release0.15.0 adds pure [source binding publication identities and receipt checks](src/amphora_data_artifacts/representations/bindings/README.md). Canonical wire serialization now lives in the pure validation helper and preserves cache bytes. Source preflight/state, orchestration, current-rights proof and hosted APIs remain subsequent tasks; artifact_0008 and420 public schemas are unchanged.

BP-06.05/B1.04b release0.16.0 adds exact source preflight and durable binding request/lease/journal state under artifact_0009. Owner-local command/upload inspection verifies actual outcomes. Recoverable orchestration and hosted APIs remain later gates. Existing public schemas remain unchanged. Data<=0.15.0 must not migrate artifact_0009.

BP-06.05/B1.04c release0.17.0 adds bounded source-to-vector orchestration and expired-upload recovery. Actual owner outcomes drive retry; nondeleting writer fences precede expired stream settlement. artifact_0009/public schemas remain unchanged; hosted representation APIs and process-crash acceptance remain later gates.

BP-06.05/B1.05 release0.18.0 adds optional authenticated `/v1/representations` routes and the strict `representations` host flag (default false). See the [representation boundary](src/amphora_data_artifacts/representations/README.md) for routes/grants/replay/rights and configuration. Activation installs the reviewed vector validator and probes tables; it never migrates or registers profiles automatically. Public schemas andartifact_0009 remain unchanged.

[Retrieval generations](src/amphora_data_artifacts/retrieval/README.md) owns ordered corpus/generation identity, private immutable intent/history and lease-fenced build state. Its `tests/retrieval/` suite is selectable independently. Verified projection/PG head publication, actual Qdrant and optional retrieval APIs are implemented; installed reconstruction and process recovery have separate BP-06.05 evidence.

The [Qdrant boundary](src/amphora_data_artifacts/retrieval/qdrant/README.md) provides pinned backend configuration and bounded authenticated transport. Actual projection/exact-search adapter is implemented; independently installed Data/index reconstruction is verified in B2.02c; no API exposes caller-selected backend configuration.

Optional retrieval configuration and `/v1/retrieval` generation/query routes are described in [retrieval boundary](src/amphora_data_artifacts/retrieval/README.md). They preserve explicit source/profile/generation pins and current rights; startup does not migrate or require a live index backend.

Data0.31 adds the owner-local [catalog recovery audit](src/amphora_data_artifacts/recovery/README.md): read-only finalized-reference/byte integrity, separate pending-retention count and create-once diagnostic output. No HTTP route, command encoding, schema or migration change. This explicit local operator capability does not grant content-use or scientific authority.
