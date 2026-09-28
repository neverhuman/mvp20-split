# Artifact Persistence Boundary

- Implemented: `artifact_0001` records, forward `artifact_0002` upload attempts/capacity, and owner-private command transactions.
- Design: [Physical records](../../../../../docs/Architecture/System/Persistence_Record_Design.md).

`migrate.upgrade(url)` runs packaged SQL/Alembic resources as `artifact_migrator`. The explicit CLI is `python -m amphora_data_artifacts.persistence.migrate`, with `AMPHORA_ARTIFACT_MIGRATION_URL` supplied privately. Migration startup is independent of API processes. `artifacts.alembic_version` records owner history. Forward migrations preserve evidence; downgrade refuses destructive rollback.

The service role owns no schema and receives only required SELECT/INSERT and state-column UPDATE grants. Catalog identity cannot be updated or deleted. Scoped foreign keys bind reservations to exact artifact digest; one runtime-intent/output binding cannot change its artifact. Audit/outbox rows reference only artifact-owned records. These constraints do not authenticate runtime outcomes; publication handlers own that check.

`CommandStore.register` durably registers canonical bytes with stable operation identity. Same identity with different bytes fails. `finish` runs inside its caller's transaction, after domain locks, and preserves an existing terminal receipt. The handler validates its receipt DTO and authority. `transact` retries the whole short database callback at most three times for SQLSTATE 40001/40P01; other failures propagate. Callbacks reload state and contain no network, filesystem, model or tool actions.

Tests use service-role TCP connections and independent migration credentials. They cover scoped constraints, denied mutation, rollback, simultaneous connections, actual serialization conflict and retry exhaustion. They do not prove publication or byte crash recovery. Dev owns disposable reset; production backup/restore remains BP-09. Replacement preserves schema identity and public contracts and proves migration/replay behavior before traffic.

Upload migration preserves legacy rows without assigning an actor; legacy records cannot pass new owner authorization. New rows bind principal, generation and exact selected attempt. Capacity and attempt settlement follow publication-owned transactions; only required state columns receive UPDATE grants.
