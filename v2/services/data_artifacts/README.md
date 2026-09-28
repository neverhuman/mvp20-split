# Data and Artifacts Service

- Status: provisional uploads and verified finalization implemented; protective reservation handshake implemented; bounded reconciliation/cleanup sweeps implemented; lifecycle hosting and independent service acceptance pending.
- Package: `amphora-data-artifacts` 0.1.0.
- Architecture: [Artifact publication](../../docs/Architecture/System/Artifact_Publication_Protocol.md), [physical records](../../docs/Architecture/System/Persistence_Record_Design.md).

This independently installed service owns provisional upload records, immutable artifact catalog bindings, protective reservations, command receipts and artifact audit/outbox state. Its [private persistence module](src/amphora_data_artifacts/persistence/README.md) implements migrations and command registration/terminal receipt transactions. `api.create_app(uploads, storage, credentials, outcomes=None)` exposes POST /v1/uploads, PUT /v1/uploads/{id}/content and POST /v1/artifacts/finalize using explicit configured principals and policy. Successful streaming returns a provisional receipt; verified finalization returns ArtifactRef. POST /v1/reservations, /confirm and /reconcile implement the protective handshake with an explicitly configured runtime outcome client. Content retrieval and executable deployment configuration remain later gates.

Dependencies are public core/command/artifact contracts, SQLAlchemy, psycopg, Alembic, FastAPI and Uvicorn. No runtime source imports, runtime database access, shared repository or scientific dependencies are permitted. Future callers use artifact contracts; runtime outcomes require an authenticated public boundary.

`tests/persistence/` owns actual PostgreSQL migrations, scoped binding, immutability, rollback, duplicate-command contention and bounded transaction-retry tests. Run `uv run --project v2/dev --locked python v2/dev/run_tests.py --module data-artifacts` with the explicit fixture enabled as described in [dev tooling](../../dev/README.md). Without opt-in these tests skip; that is not persistence evidence.

A replacement preserves catalog identity, reservation protection, stable command replay and service-owned migration history. Pending uploads are not usable artifacts. Process-kill tests cover finalization before and after catalog commit. Target-filesystem power-loss durability, retention proof, reconciliation and independent service acceptance remain later gates. No production storage path, provider or deployment is configured.

## Provisional Upload Modules

[Publication](src/amphora_data_artifacts/publication/README.md) owns authority, capacity and generation transactions; [storage](src/amphora_data_artifacts/storage/README.md) owns bounded immutable attempt bytes. `access.py` maps explicit opaque credentials to principals; no default secret or network startup occurs on import. `api.py` maps safe errors and enforces bounded JSON/stream timeouts. Database failure is retryable infrastructure failure, not scientific rejection.

Run `uv run --project v2/dev --locked python v2/dev/run_tests.py --module data-artifacts --area publication` with `AMPHORA_TEST_POSTGRES=1`; `--area storage` runs filesystem checks, `--area persistence` runs DB primitives, and `--coverage` keeps the full owner source denominator. Cases cover stale processes, body disconnect/cancellation/timeout, quotas, credential/scope errors and path/link rejection. No automatic cleanup or backup guarantee is implied.

[Retention](src/amphora_data_artifacts/retention/README.md) owns protective reservation identity and authenticated terminal proof. Use `--area retention` for its isolated suite; separate-process scripted peer tests do not substitute for actual runtime integration.

[Maintenance](src/amphora_data_artifacts/maintenance/README.md) owns conservative provisional cleanup and bounded reservation sweeps. Use `--area maintenance` for its process-crash and capacity tests. No automatic finalized-content deletion; markers/evidence and lifetime upload bounds persist.
