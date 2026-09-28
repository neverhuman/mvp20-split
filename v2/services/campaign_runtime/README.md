# Campaign Runtime — Foundation Slice

- Status: partial; validation and persistence foundation implemented; execution handlers/interpreter absent
- Package: `amphora-campaign-runtime` 0.1.0
- Architecture: [Graph Runner](../../docs/Architecture/System/Graph_Runner.md), [Isolation](../../docs/Architecture/System/Service_Isolation.md)

## Owned Behavior and Module Boundaries

- `graph.py`: immutable graph/vertex/route domain values; explicit DTO mapper; bounded nested-scope traversal, node/edge uniqueness, DAG, branch predecessor/routes, join and termination checks.
- `admission.py`: pure invocation/completion binding policy; exact versions, declared ports, artifact/checkpoint scope/schema and supplied attempt/fence identity. It does not prove that a supplied grant or fence is current.
- `api.py`: default validation-only FastAPI application, bounded request decoding, sanitized structural errors and OpenAPI publication. An explicitly configured admission instance enables the synthetic fixture-run endpoint; configured fixture apps expose claim/renewal; completion remains pending.

- `persistence/`: [private migration and command-store boundary](src/amphora_campaign_runtime/persistence/README.md); fixture admission now has an owned transaction; claim/renew handlers now exist; completion remains pending.

Graph Runner coordination, aggregation and supervision remain successor behavior.

## Public API and Data Boundaries

`GET /health` reports validation-only mode and execution unavailable. `POST /v1/campaign-definitions/validate` returns structural findings, `executable=false` and remaining scientific/tool/authority/budget/execution checks. Schema-invalid inputs return 422; request body over 256 KiB returns 413; deeply nested JSON is bounded before DTO parsing. Errors omit raw input values. JSON decoding uses the same Pydantic JSON path as interchange fixtures; generated OpenAPI references the owned input/output schemas.

The validation endpoint performs no database or filesystem payload writes, provider calls, scientific computations, authentication or live grant validation. This is a local developer endpoint: start Uvicorn on loopback only. No deployed identity gateway, enterprise readiness, live lease fencing or scientific activation claim.

Dependencies are public core/tool/campaign/command/runtime contracts, Pydantic, FastAPI, Uvicorn, SQLAlchemy, psycopg and Alembic. No adjacent service imports, shared ORM or scientific libraries. Graph validation values remain ephemeral; persistence owns separate durable records and migration history.

## Replacement and Verification

A rebuild preserves safe rejection, structured findings and truthful non-execution semantics. Consumers rely on public HTTP/contracts, not these private classes. Import enforcement rejects cross-owner private imports/undeclared libraries. A replacement also preserves the linked persistence invariants and migration history. Execution handlers must use explicit owner-domain transactions.

Run [foundation verification](../../dev/README.md) for graph semantic negatives, cross-scope/version/attempt rejection, OpenAPI reference integrity, body/error bounds and isolation tests. Package wheel installation is tested separately from the shared dev environment. The schema is a pre-release subset: duplicate/late commits, authorization, recovery, concurrency and scientific tool applicability require real BP-02/03/04 tests.

Local command from repository root after uv bootstrap: `v2/.venv/Scripts/uv.exe run --project v2/services/campaign_runtime uvicorn amphora_campaign_runtime.api:app --host 127.0.0.1 --port 8000`. This starts only the validation service; stop it after use. Linux uses the equivalent uv executable path.

## Owned Tests and Baseline

| Folder under `tests/` | Behavioral scope | Measured source |
|---|---|---|
| `graph/` | Topology, explicit loops, invalid edges, branches/joins and predicate dependencies | `graph.py` |
| `admission/` | Exact tool identity, artifact scope and completion identity against a supplied attempt | `admission.py` |
| `api/` | Validation-only API, body/depth bounds, redacted errors and OpenAPI | `api.py` |
| `persistence/` | PostgreSQL constraints, command contention/rollback/retry | Private persistence module |
| `baseline/` | Frozen v1 source pins, scoring-chain order and typed campaign scaffold | Graph structural boundary; no execution parity |

From repository root: `uv run --project v2/dev --locked python v2/dev/run_tests.py --module runtime --coverage`. For PostgreSQL, enable the explicit dev fixture and use `--area persistence`. Add `--area graph`, `--area admission`, `--area api` or `--area baseline` for a narrower run. Coverage still uses the full runtime source denominator so a small suite does not masquerade as complete module coverage. Reports are separated by selection under `v2/.test-results/`.

[Initial v1 solver graph](tests/fixtures/v1_solver/README.md) owns the source-derived behavior reference and future parity scenarios. Current tests cannot demonstrate execution/restart/concurrency equivalence because the interpreter is not built. Remaining local branches and schema combinations are visible in coverage reports; real authority, durable fencing and scientific acceptance remain later gates. Keep these suites beside this service across rebuilds.

[Lifecycle domain](src/amphora_campaign_runtime/lifecycle/README.md) implements pure run/worker/budget/activation/lease transitions under BP-02.04/I1. It supplies deterministic policy only; durable handlers and execution endpoints remain pending. Use `--area lifecycle` for its exact-expiry, fencing, uncertainty and settlement oracles.

BP-02.04/I2: `create_app(admission, credentials)` adds authenticated POST /v1/fixture-runs with an exact configured synthetic allowlist and installation-wide single-running-run guard. Run/activation/receipt/audit/outbox commit atomically. General graphs remain non-executable and no worker dispatch occurs. The default module-level app retains validation-only behavior.

BP-02.04/I3 adds configured fixture claim/renew HTTP routes, persisted activation deadlines and increasing attempt fences. Two independently running worker probes contend under the real run lock; expired/replayed requests preserve authority and accounting. Full completion, cancellation/revocation and lifecycle acceptance remain open; the default validation app still exposes no durable handlers.

BP-02.04/I5 configured fixture apps also expose scoped cancellation and durable worker revocation. These commands serialize with claims/renewals, atomically abort prepared intents and preserve uncertain reserved budget. Policy audit/outbox supports revocation before any run. Authenticated public intent-outcome queries and completion transport remain .05; full lifecycle acceptance remains I6.
