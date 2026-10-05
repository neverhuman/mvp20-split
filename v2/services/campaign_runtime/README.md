# Campaign Runtime

Current package0.24.0 adds pure [supervisor journal frames and series](src/amphora_campaign_runtime/supervision_journal/README.md). Exact original observations survive reconstruction; bounded repairs preserve lineage and narrow ceilings. 122 combined scope/request/response/journal tests pass, including33 owned journal cases;105 new statements and12 branches covered100%. SQL persistence and execution authority remain separate gates.


Current package0.23.0 adds the pure [supervisor response/receipt](src/amphora_campaign_runtime/supervision_responses/README.md) boundary with public supervision0.2. It binds exact original request/attempt/captured candidate bytes and separates recorded command receipts from owner decision readbacks. 129 combined cases,42 public wire cases and78 boundary/legacy command cases pass; no durable supervisor or accepted effect is implemented by these profiles.528 public schemas preserve520 predecessors. Independent exchange proof passes265 initial and105 replacement cases with162 unchanged predecessor Runtime files and seven Git checkout-filter byte vectors; [evidence](../../docs/Audits/Evidence/BP-07-Supervisor/Exchange_Compatibility.json).

Predecessor0.22.0 added [supervisor request binding](src/amphora_campaign_runtime/supervision_requests/README.md) and public supervision0.1 contracts. Scope exports and original Planning request/cut/actor/policy/hash/lineage shape are verified by pure binding;62 scope/wire/publication cases cover54 new statements/4 branches100%.520 published schemas preserve510 predecessor bytes. Response/decision/command profiles, actual stored ancestry/auth and accepted execution remain separate BP-07.04 gates.

Predecessor0.21.0 added the pure [supervision scope](src/amphora_campaign_runtime/supervision_scope/README.md) boundary under BP-07.04/B1.01: concrete occurrence identity, selected read-set staleness and symmetric read/write conflict detection.26 scoped tests cover119 statements/16 branches. 111 independently installed scope/contract cases pass;162 predecessor Python/SQL/JSON payload files are unchanged. There is no supervisor journal, checkpoint pause or accepted parameter effect yet. Existing runtime0017 and public graph-runtime0.13 remain unchanged. Earlier checkpoint paragraphs below are historical scope, not current progress.

Runtime0.20.0 / BP-05.03/B2 in progress: [definitions](src/amphora_campaign_runtime/definitions/README.md) adds immutable draft save/read and revision-pinned validation with opt-in authoring HTTP against graph-runtime0.11.0 DTOs. Read-only reviewed tool/schema metadata supports the next editor consumer. Exact retained material now feeds transactional draft admission under the existing runner. Tool-bearing draft admission requires optional server-side draft_registry configuration and fresh exact Registry observations; absent/expired/unavailable eligibility rejects. Scientific authority remains synthetic-only; installed Registry/Studio activation proof passed. Existing configured execution and navigation remain unchanged. Explicit v2 numeric command envelopes support authored float constants; persisted profile/bytes/receipts are preserved and checked across replay. No new migration or NumberValue wire change.

Runtime0.13.0 adds a scoped named-view catalog under graph_navigation. It advertises implemented Runtime read capabilities, not scientific availability or a new projection service. Public schema, PostgreSQL and HTTP regressions plus actual Studio/Runtime independent replacement passed; BP-05.02 is closed.

Runtime0.12.0 adds [graph navigation](src/amphora_campaign_runtime/graph_navigation/README.md): bounded occurrence scopes and retained authored topology. BP-05.02 is accepted: actual initial/successor occurrence topology and linked evidence survive independent browser/Runtime replacement.

Accepted checkpoint `2026-09-29 18:50:04`: BP-04.05 and BP-04 closed/audited. Independent DTO-only observer and Runtime replacement preserve old cursors and all graph/detail/attempt/value/event records across actual five-tool initial/successor execution;17 invocations,44 confirmed reservations. [Evidence](../../docs/Audits/Evidence/BP-04-Recovery/V1.json). Earlier B1-B3/pending statements below describe historical gate positions; no gate in this child remains open.

Runtime 0.11.0 adds [graph inspection](src/amphora_campaign_runtime/graph_inspection/README.md): bounded revision-consistent snapshot/detail/value reads and resumable invalidations from existing durable audit records. Public graph-runtime 0.5.0 contracts are additive; no new migration. BP-04.05/B1 focused tests pass; foundation verification passed1202 tests/19 installs; process and installed observer replacement verification remain in the active child. The accepted 0.10.0 checkpoint below remains predecessor evidence.

Accepted checkpoint `2026-09-29 17:57:39`: BP-04.04 closed/audited. Five real solver images and independent tool/SDK/owner installs passed initial-population -> successor generations 1/2, concurrent scoring and Runtime replacement; 17 invocations, all 44 reservations confirmed. Source/lineage/receipt/artifact history preserved. Scientific validity and target-host execution remain excluded. Earlier B1-B3 statements below describe their historical verification tiers; no gate in this child remains open.

Runtime 0.10.0 adds explicit successor admission under BP-04.04/B2, using graph-runtime 0.4.0 and campaigns 0.4.0. The [successor module](src/amphora_campaign_runtime/successors/README.md) owns terminal source cuts, exact carried values and immutable ancestry; the existing coordinator commits the new run and receipt. Migration runtime_0014 is required; startup never migrates. Earlier typed binding process and installed-peer gates are accepted under closed BP-04.04A.

- Status: configured deterministic execution, aggregation/waits and typed bindings accepted; source-derived solver orchestration B1 verified; successor B2 verified. New solver process proof passed B3; actual installed-peer acceptance passed V1.
- Package: `amphora-campaign-runtime` 0.18.0.
- Architecture: [Graph Runner](../../docs/Architecture/System/Graph_Runner.md), [runtime protocol](../../docs/Architecture/System/Runtime_Command_Protocol.md), [isolation](../../docs/Architecture/System/Service_Isolation.md).

## Ownership and Module Boundaries

| Module | Responsibility |
|---|---|
| [graph_inspection](src/amphora_campaign_runtime/graph_inspection/README.md) | Revision-consistent bounded graph/detail/value reads and durable reconnect invalidations |
| [successors](src/amphora_campaign_runtime/successors/README.md) | Exact predecessor readiness, compatible carry maps, immutable ancestry and source observations |
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
