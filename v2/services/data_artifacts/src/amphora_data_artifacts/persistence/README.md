# Artifact Persistence Boundary

- Implemented: `artifact_0001` records, forward `artifact_0002` upload attempts/capacity, and owner-private command transactions.
- Earlier scoped addition: `artifact_0008` private representation profiles, work intents, leases and immutable computed results; B1.03 verified; later source-binding publication remains separate.
- Design: [Physical records](../../../../../docs/Architecture/System/Persistence_Record_Design.md).

`migrate.upgrade(url)` runs packaged SQL/Alembic resources as `artifact_migrator`. The explicit CLI is `python -m amphora_data_artifacts.persistence.migrate`, with `AMPHORA_ARTIFACT_MIGRATION_URL` supplied privately. Migration startup is independent of API processes. `artifacts.alembic_version` records owner history. Forward migrations preserve evidence; downgrade refuses destructive rollback.

The service role owns no schema and receives only required SELECT/INSERT and state-column UPDATE grants. Catalog identity cannot be updated or deleted. Scoped foreign keys bind reservations to exact artifact digest; one runtime-intent/output binding cannot change its artifact. Audit/outbox rows reference only artifact-owned records. These constraints do not authenticate runtime outcomes; publication handlers own that check.

`CommandStore.register` durably registers canonical bytes with stable operation identity. Same identity with different bytes fails. `finish` runs inside its caller's transaction, after domain locks, and preserves an existing terminal receipt. The handler validates its receipt DTO and authority. `transact` retries the whole short database callback at most three times for SQLSTATE 40001/40P01; other failures propagate. Callbacks reload state and contain no network, filesystem, model or tool actions.

Tests use service-role TCP connections and independent migration credentials. They cover scoped constraints, denied mutation, rollback, simultaneous connections, actual serialization conflict and retry exhaustion. They do not prove publication or byte crash recovery. Dev owns disposable reset; production backup/restore remains BP-09. Replacement preserves schema identity and public contracts and proves migration/replay behavior before traffic.

Upload migration preserves legacy rows without assigning an actor; legacy records cannot pass new owner authorization. New rows bind principal, generation and exact selected attempt. Capacity and attempt settlement follow publication-owned transactions; only required state columns receive UPDATE grants.

Migration artifact_0003 adds upload creation time and cleaning/cleaned attempt states. Existing uploads receive a fresh cleanup grace interval; identity and retained evidence stay immutable. Maintenance refunds capacity only after filesystem retirement, using the existing restricted column grants.

BP-06.01 adds artifact_0004: immutable acquisition source/delivery records, source heads and conversion traces. [Acquisition](../acquisition/README.md) owns policy and tests. Scope-bound foreign keys link only to this service catalog/source records; no Research SQL access or scientific-use authority. Existing publication/retention rows and migration history are preserved.

BP-06.01 adds artifact_0005: immutable identity observation intents/results, exact scoped trace/hash foreign key and insert/select-only grants. Intents persist before external Research lookup; result insertion is a separate atomic transaction, with the first committed result returned on contention/replay. No transaction holds a lock across HTTP; failed lookup leaves pending intent. Neither historical table permits service-role UPDATE/DELETE.

BP-06.01/B2 adds artifact_0006 rights revisions/current heads and lineage indexes. No historical rights are synthesized. Revision history is insert/select-only; heads allow only revision-column updates. Shared evidence_records helpers own deterministic record bytes and ordered advisory locks inside this service; they are not a cross-owner repository. Source/trace/policy/result commits coordinate through one scope lock for current-use fencing, without filesystem/peer I/O under locks. See [Source Rights](../source_rights/README.md).

`artifact_0007` retains derived-upload declarations, finalized derivations and ordered scoped inputs. `artifact_0008` adds the separately bounded [representation registry/cache](../representations/storage/README.md). Its immutable tables use SELECT/INSERT-only grants; lease updates are restricted to ownership/fence/expiry columns. Existing catalog/source/derivation history is not rewritten. Data through0.13.0 is not a compatible migration tool for the newer schema; no automatic downgrade or startup migration is provided.

`artifact_0009` adds immutable encoding binding jobs, actor-scoped request aliases, publication events and final bindings, plus narrowly mutable publication cursors. See [binding boundary](../representations/bindings/README.md). Data0.16.0 or newer is required to migrate retained artifact_0009; older migrators must not run on it. Existing rows remain intact.

CommandStore.inspect/inspect_in read exact canonical-command history without registering or mutating it; conflicting bytes reject. Binding recovery uses this to distinguish missing/pending from retained rejection.

BP-06.05/B2.01c adds artifact_0010: immutable `index_generations`, ordered `index_generation_bindings`, numbered `index_build_attempts` and `index_generation_events`, with narrow mutable `index_generation_cursors`. Scoped generation/profile/binding foreign keys preserve owner identity. SELECT/INSERT-only history grants and column-limited cursor updates keep the authority in the retrieval lifecycle. No cross-owner SQL, index backend, publication head or query record is introduced. Explicit0009->0010 migration preserved measured catalog/source/derivation/profile/binding/event counts and row checksums. Repeat-upgrade tests retain history; no reset/downgrade.
