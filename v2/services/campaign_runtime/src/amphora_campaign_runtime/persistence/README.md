# Runtime Persistence Boundary

- Implemented: forward migrations through `runtime_0004` and owner-private command transactions.
- Design: [Physical records](../../../../../docs/Architecture/System/Persistence_Record_Design.md), [runtime protocol](../../../../../docs/Architecture/System/Runtime_Command_Protocol.md).

`migrate.upgrade(url)` runs packaged SQL/Alembic migrations as `runtime_migrator`. The explicit CLI is `python -m amphora_campaign_runtime.persistence.migrate`, using privately supplied `AMPHORA_RUNTIME_MIGRATION_URL`. No API startup migration occurs. `runtime.alembic_version` is private to this owner. Downgrade refuses destructive rollback; changes require forward migration.

Runtime owns commands, admission guard, runs, activations, fenced attempts, completion intents, immutable results/revisions, worker policy, audit and outbox records. Exact scoped foreign keys prevent cross-project/run/attempt bindings. A partial unique index permits one running campaign installation-wide. Service grants exclude DDL, DELETE, accepted-result changes and immutable identity updates. Outbox scope derives from its uniquely referenced runtime audit event; no artifact table is referenced.

`CommandStore.register` commits canonical bytes and a stable operation ID, rejecting changed bytes under the same identity. `finish` requires the caller's transaction and locks the command after domain locks. Terminal replay returns the stored disposition. Handlers remain responsible for current authority, lease/fence, budgets, validated receipts and atomic events. This storage seam does not implement execution transitions.

`transact` retries the whole database callback at most three times for SQLSTATE 40001/40P01. Callbacks reload all state and contain no network, filesystem or scientific actions. Other failures roll back and propagate. Actual PostgreSQL tests use independent connections for duplicate registration, serialization retry and rollback; relational probes establish storage constraints, not legal execution transitions.

Default API construction remains validation-only; configured lifecycle handlers own atomic domain audit/outbox transitions. Completion acceptance/delivery and cross-service crash recovery remain later gates. Replacement preserves accepted history, migration ownership, scope/fence uniqueness and public contracts, and reruns module tests. Dev owns disposable reset; target-host backup/power-loss proof is BP-09.

BP-02.04/I3 forward migration runtime_0002 persists activation/attempt deadlines, bounds lease expiry and grants the owner deadline-column update. Existing attempts backfill from original expiry; no extended authority. Claim/renew handlers own atomic run-budget/attempt/receipt/audit/outbox transitions under run locks.

runtime_0003 adds a separate scoped policy audit/outbox for worker revocation without a run. Run audit foreign keys remain strict; no dummy run is created. Both journals are private runtime state and require later owner outbox delivery.

runtime_0004 adds immutable tool_snapshot to each run (legacy default empty; no inferred contract) and intent_reservations keyed by scoped intent/output binding. The runtime service may insert/read receipts but cannot update/delete them or replace admitted tool snapshots. Completion preparation and resumable external reservation acquisition own these records; no artifact private schema is referenced.
