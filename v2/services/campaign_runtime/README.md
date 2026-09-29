# Campaign Runtime

Runtime 0.9.0 implements explicit typed Artifact/collection execution under BP-04.04A/B2, with campaigns 0.4.0 and graph-runtime 0.3.0. Wire-v4 requires configured binding publication/protection peers; default admission still rejects it. The new [Artifact binding module](src/amphora_campaign_runtime/artifact_bindings/README.md) owns resumable conversion, protected commit and cancellation cleanup. `/v3/graph-runs` exposes the new operators. Migrations runtime_0012/0013 are required; startup never migrates. B3 process and V1 installed-peer gates remain.

- Status: synthetic invocation lifecycle and atomic completion implemented; paired retention/delivery acceptance verified; REC-01..09 recovery/replacement verified; configured deterministic graph execution/replacement accepted in BP-04.02; aggregation and external waits accepted in BP-04.03; typed bindings are being verified in BP-04.04A/B2.
- Package: `amphora-campaign-runtime` 0.9.0.
- Architecture: [Graph Runner](../../docs/Architecture/System/Graph_Runner.md), [runtime protocol](../../docs/Architecture/System/Runtime_Command_Protocol.md), [isolation](../../docs/Architecture/System/Service_Isolation.md).

## Ownership and Module Boundaries

| Module | Responsibility |
|---|---|
| `artifact_bindings/` | Typed Artifact/collection conversion, durable preparation/protection and atomic graph acceptance |
| `graph.py` | Immutable graph values, bounded topology/loop/branch/join validation; no interpreter |
| [compiler](src/amphora_campaign_runtime/compiler/README.md) | Pure wire-v2 semantic compilation, exact tool/schema pins, scoped types/control flow, canonical plans and activation addresses |
| [coordinator](src/amphora_campaign_runtime/coordinator/README.md) | Configured graph admission and durable advancement, branch/all-join/scatter/loop state, bounded observations and recovery polling; actual process/peer/replacement acceptance passed BP-04.02; richer policies remain BP-04.03 |
| `admission.py` | Pure input/tool/completion binding policy against supplied identity; not live authority |
| [aggregation](src/amphora_campaign_runtime/aggregation/README.md) | Immutable ordered member snapshots and atomic audit-linked storage; policy/coordinator integration remains BP-04.03 |
| [waits](src/amphora_campaign_runtime/waits/README.md) | Exact external receipt pins, immutable wait/receipt storage and separate protection preparation; acceptance/timeout hosting remains gated |
| [lifecycle](src/amphora_campaign_runtime/lifecycle/README.md) | Exact fixture admission, claims, renewal, cancellation/revocation, budget settlement and scoped observations |
| [completion](src/amphora_campaign_runtime/completion/README.md) | Immutable prepared intents, resumable artifact reservations and atomic result/checkpoint acceptance |
| [delivery](src/amphora_campaign_runtime/delivery/README.md) | Both runtime journals, fenced delivery leases, bounded retry/exhaustion and exact acknowledgement |
| [inspection](src/amphora_campaign_runtime/inspection/README.md) | Scoped original receipts, accepted reports, signed pinned audit pages and current delivery state |
| [persistence](src/amphora_campaign_runtime/persistence/README.md) | Private runtime schema/migrations, canonical commands, transaction retries, receipts and audit/outbox |
| `api.py`, `lifecycle/http.py` | Bounded decoding, authenticated configured handlers, sanitized errors and OpenAPI |
| `hosting.py`, `__main__.py` | Explicit local configuration, service-role readiness and loopback executable; no startup migrations |

Only this service owns execution authority and runtime tables. Dependencies are public core/tool/campaign/command/runtime/graph-runtime/artifact contracts, Pydantic, FastAPI/Uvicorn, SQLAlchemy/psycopg and Alembic. No private adjacent-service imports, shared ORM, scientific libraries or provider calls. Artifact payloads remain owned by the artifact service. Configured references are trusted pins; graph predicates may verify bounded public Artifact metadata/content outside SQL transactions. This is not scientific validation.

## Public Boundary

Default `create_app()` and module `api:app` expose only health and structural campaign validation. `POST /v1/campaign-definitions/validate` returns findings, `executable=false` and pending checks. No arbitrary campaign dispatch exists. Requests are bounded to 256 KiB, JSON nesting 64 and a ten-second whole-body deadline; errors omit raw payload values.

`Host.load` requires explicit environment-backed database credentials/tokens, scoped actor/action entries and an immutable fixture or graph allowlist. It requires `runtime_service` and migrated owner tables; migration-role startup is rejected. Graph configuration compiles exact public descriptors/locks/schema bytes; tool-bearing plans require a completion peer. See the [coordinator configuration contract](src/amphora_campaign_runtime/coordinator/README.md). No configuration or secret is inferred from a worker request. The configured application exposes:

| Endpoint | Access and result |
|---|---|
| `GET /health`, `/ready` | Process capability report/readiness; fixture_lifecycle or explicitly configured_graphs mode |
| `POST /v1/fixture-runs` | `admit`; exact allowlisted pins, one running campaign; original command receipt |
| `POST /v1/invocations/claim` | `claim`; matching actor/worker and exact tool; invocation/lease or stable no-work receipt |
| `POST /v1/attempts/renew` | `renew`; current worker, attempt, fence and database-clock lease; original receipt |
| `POST /v1/invocations/complete` | `complete`; enabled only with configured artifact peer; prepare/protect/recheck/accept or pending/rejected receipt |
| `POST /v1/runs/cancel` | `cancel`; optional revision guard, atomic prepared abort and budget settlement |
| `POST /v1/workers/revoke` | `revoke`; durable scoped worker policy and protected work settlement |
| `GET /v1/runs/{run_id}` | `read`; bounded RunSnapshot with budget and current activation/attempt observations; missing/wrong scope returns 404 |
| `POST /v1/completion-intents/outcome` | `outcome`; configured exact authenticated reservation proof, with unknown distinct from aborted |
| `POST /v1/graph-runs` | `admit`; enabled by graph allowlist, exact scope/plan/input pins |
| `POST /v1/graph-runs/advance` | `maintain`; bounded durable advancement command, replayable receipt |
| `GET /v1/graph-runs/{run_id}` | `read`; up to 100 graph nodes per scoped cursor page |

Every mutation authenticates the configured token, action, actor and scope. Renew/claim additionally consult live authority; replayed receipts never restore expired/revoked authority. Reads use a read-only repeatable-read transaction and never grant authority. Commands serialize under owner locks, compare database time after locks, and commit state/budget/receipt/audit/outbox atomically. External effects remain forbidden in synthetic dispatch; uncertainty is retained explicitly rather than retried or refunded.

## Hosting and Recovery

Use [config.example.json](config.example.json) as a synthetic configuration shape; replace fixture pins and set the named environment variables locally. Migrate with the separate owner migration command first. From repository root: `uv run --project v2/services/campaign_runtime --locked amphora-runtime check --config <local-config>` then `amphora-runtime serve --config <local-config> --port 8080` through the same uv project. The module form is `python -m amphora_campaign_runtime`. Serving binds only 127.0.0.1; TLS/gateway/deployment remains BP-09.

`settle --config <local-config> --actor <actor> --tenant <tenant> --project <project> --run <run>` selects one explicitly configured `maintain` principal. It performs one bounded run sweep; there is no implicit background scheduler. Expired pure work spends its issued unit once and may be reissued within deadline/attempt/budget bounds. Cancellation spends issued work and costs nothing for unclaimed work. A prepared completion intent blocks blind expiry until its owner reconciles/aborts it. Unknown external effects retain reservations and block automatic retry.

Database outages leave registered commands pending/retryable; stable business rejection and original terminal receipts persist. Local credentials are a development profile, not enterprise identity. Runtime notifications and retention commands have explicit bounded durable delivery passes. Configured history routes expose original receipts, accepted reports and bounded audit/delivery pages; these remain observations, not subscriptions or authority.

Configured graphs use a separate `coordinate` process with scoped maintain identity, `--time-budget` and `--poll-interval`; serving HTTP alone does not start it. It reconciles stale intents and reconstructs advancement from committed state. Branches, ordered all/partial/deadline aggregation, bounded scatter, loop checkpoints and external waits are implemented. Runtime 0.7.0 requires migrations through runtime_0011. [Aggregation](src/amphora_campaign_runtime/aggregation/README.md) owns immutable decisions; [waits](src/amphora_campaign_runtime/waits/README.md) owns passive v3 Await execution, authenticated issuer receipts, separate Artifact protection and timeout/cancellation recovery. Graph-page v2 preserves the old observation schema. Actual wait process/installed-issuer acceptance passed BP-04.03/B3-V1. Default validation-only hosting and wire-v1 validation are unchanged. Graph worker snapshots expose at most 256 active queued/leased invocations; retained historical graph nodes use their separate paginated read boundary. Tool package versions and worker command formats are unchanged.

`reconcile-intents` uses the same scoped maintenance selection as `settle`, plus bounded `--limit` (1-100) and `--after` cursor. It aborts expired/ineligible prepared intents and terminalizes previously cancelled pending commands without waiting for caller retries. Run bounded passes before settlement if prepared-intent protection blocks reclaim. Terminal artifact confirm/reconcile operations are queued atomically and delivered through explicit bounded passes. The artifact service must be configured with a scoped outcome credential and this runtime's exact outcome endpoint. Example configurations have independent synthetic profiles/pins and require deliberate matching before an integrated campaign; they are not an already deployed pair.

## Owned Tests and Replacement Acceptance

| Folder under `tests/` | Behavior |
|---|---|
| `graph/`, `admission/`, `api/` | Structural/pin rejection, OpenAPI, redaction, bytes/depth/time limits |
| `persistence/` | Real PostgreSQL roles, constraints, command contention and rollback |
| `lifecycle/` | Pure transitions plus actual admission/claim/renew/budget/authority transactions, races, scope and startup |
| `inspection/` | Scoped historical receipts/reports, pinned pages/cursor failures and delivery visibility |
| `delivery/` | Both journal claims, stale ack fencing, backoff/exhaustion and exact HTTP acknowledgement |
| `completion/` | Immutable descriptor/intent bindings, reservation resume, cancellation during remote I/O and transport negatives |
| `acceptance/` | Independently installed runtime plus HTTP-only workers: worker kill/lease reclaim, higher fences, stale rejection, read isolation and conserved budget |
| `baseline/`, [v1 fixture](tests/fixtures/v1_solver/README.md) | Frozen source pins and behavior graph; structural reference, not execution parity |
| `compiler/`, `scheduling/` | Pure exact-plan compilation; real PostgreSQL graph admission/advancement, frozen membership, checkpoints, public projection transport and configured hosting |
| `aggregation/` | Ordered immutable observation cuts, explicit missingness, exact replay and real PostgreSQL audit/role constraints; policy execution remains pending |
| `waits/` | Exact issuer/subject/revision/output/deadline pins; real PostgreSQL wait/receipt/intent constraints; distinct from later executed-race acceptance |

`uv run --project v2/dev --locked python v2/dev/run_tests.py --module runtime --area lifecycle` is the focused lifecycle suite. Other areas run independently; `--coverage` measures the whole owner source denominator, including unexecuted files. Explicit `AMPHORA_TEST_POSTGRES=1` enables the labeled disposable fixture. `verify_foundation.py --builds` additionally installs wheels outside the checkout and runs both standalone service probes. Its runtime workers receive only HTTP request/token data and a minimal OS environment, never database credentials or owner imports. Database-domain contention probes are distinct from this public-boundary evidence.

A replacement preserves public wire/canonical-command compatibility, immutable snapshots and history, run/worker/attempt fencing, database-clock checks, budget conservation, prepared protection and atomic receipt/audit/outbox behavior. Preserve the migration chain and service-role limits. Pass owner suites plus independent installed HTTP acceptance before cutover. Completion and exact artifact retention integration passed BP-02.05; broader recovery passed BP-02.06; graph interpretation BP-04; target-host durability BP-09. Process-kill evidence does not establish power-loss safety or scientific validity.

BP-02.05 adds optional trusted `tools` descriptors to host configuration and pins matching descriptors in each admitted run. Existing configs still admit/claim fixtures, but missing completion descriptors fail closed. Runtime_0006 is required before hosting this version. Optional `artifacts` peer configuration enables fixture completion. Retention confirmation/reconciliation transport is implemented; actual cross-service acceptance passed D6; REC-01..09 interruption/restart/replacement matrix passed .06. The runtime also depends on the public artifact-contract package; it does not import the artifact service.

Delivery CLI: `deliver --config <local-config> --actor <actor> --tenant <tenant> --project <project> --limit 20 --time-budget 20`. The selected principal needs deliver. Configure notification targets explicitly; missing destinations remain retryable and eventually exhausted. Delivery never changes committed execution authority.

Optional `inspection` configuration requires a stable `cursor_key_env` and accepts `ttl_seconds` (60-3600, default 900). Historical reads require read; cross-actor receipt inspection additionally requires inspect_receipts. [Inspection boundary](src/amphora_campaign_runtime/inspection/README.md) documents public paths and resnapshot/reconnect behavior.

[Installed acceptance harness](tests/acceptance/README.md) owns actual paired-service public-API proof, independent current reservation reads and cancellation/release barriers.

[Foundation recovery and replacement](RECOVERY.md) records retained state/configuration, explicit owner bootstrap, bounded maintenance order and public verification. Actual process recovery is separate from host backup/power-loss guarantees.

BP-04.01/B1 updates the campaign-contract dependency to 0.2.0 while preserving wire-v1 validation and existing durable fixture APIs. B2 adds the pure [compiler](src/amphora_campaign_runtime/compiler/README.md), with jsonschema as an explicit isolated package dependency. It emits exact immutable plans without database writes or execution authority. Interpreter/admission remains a later gate; no old graph is silently converted and no database migration accompanies these changes.

BP-04.02/B1 advances Runtime to 0.3.0 and campaign contracts to 0.2.1 (public literal-type exports, unchanged campaign schema bytes), adds the isolated graph-runtime DTO package and migration runtime_0007. Graph-mode completion waits for the coordinator instead of inferring completion from issued invocations; fixture behavior and worker wire/package closure remain unchanged. The initial graph library is not yet wired into executable HTTP hosting. See the coordinator rebuild boundary and its owned scheduling tests before enabling graph mode or replacing Runtime.
