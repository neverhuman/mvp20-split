# Foundation Implementation Decisions

- Status: selected for BP-01; implementation evidence belongs to owning plan/module docs
- Last reviewed: `2026-09-23 19:55:48` (America/Chicago)
- Parent: [System Architecture](System_Architecture.md)
- Scope: initial local contract packages and runtime API seam

## Stack and Packaging

Use Python 3.12 for initial control/service packages, Pydantic v2 for boundary validation, FastAPI/Uvicorn for service HTTP transport, PostgreSQL with psycopg 3, SQLAlchemy 2 and Alembic for the future durable runtime. Caddy is the selected front-door/TLS direction for deployment. This does not install PostgreSQL, Caddy or a cluster during BP-01. Rust remains independently packaged scientific computation behind capability contracts.

Use standalone `pyproject.toml` projects, Hatchling builds and per-project uv lockfiles/environments. Local path sources may bind explicitly declared public contract packages. Do not use one global workspace lock or environment for all scientific services: dependency conflicts between tools must not force a shared release. A separate development verification environment can consume all contracts to test interchange, but independent package installs remain required evidence. See [uv workspace guidance](https://docs.astral.sh/uv/concepts/projects/workspaces/) on independent environments and path dependencies.

Initial packages: core wire references, tool protocol, campaign definitions, runtime validation service and foundation verification tooling. No placeholder service fleet. Each owns its dependencies, tests/fixtures and README; only public contract imports cross an owner boundary. Frontend/tool scientific dependencies do not belong in the runtime validation service.

## Wire Profile and Compatibility

Publish JSON Schema Draft 2020-12 input and serialization schemas with stable family/version IDs. Version 1 contracts are pre-release `0.1.0` package artifacts; the wire `schema_version` is explicit and unsupported tags reject. Closed records reject unknown fields. New optional fields still require compatibility assessment against old strict readers. No prior checkpoint migration or arbitrary old-version reader is claimed before persistence exists.

Identifiers are bounded opaque ASCII strings; SHA-256 references are lowercase 64-character hex. Scope is explicit in artifact/invocation references. Timestamps at wire boundaries use explicit UTC strings when introduced; avoid ambiguous local datetimes. Integers crossing JSON stay within the exact JavaScript integer range. This first protocol keeps scientific arrays/measurements in schema-bound immutable artifacts rather than inventing a universal scalar representation; unit and representation semantics are required metadata, not inferred from JSON shape.

Schema publication uses sorted-key compact UTF-8 JSON with no non-finite values and a manifest of SHA-256 file digests. This is a deterministic artifact publication profile, not a promise of universal canonical serialization across languages. Logical command/request hashing will get an explicit canonical profile before durable idempotency implementation. Models are frozen at the boundary; internal domain values use focused immutable objects.

Pydantic structural validation is followed by semantic checks owned by runtime/domain objects. Schema export does not encode every Python validator. Compatibility fixtures run against both Pydantic and an independent JSON Schema validator, with separate semantic-failure evidence. [Pydantic schema documentation](https://docs.pydantic.dev/latest/concepts/json_schema/) describes export behavior. LLM and Rust consumers must use the published schemas and their own conformance gates before support is claimed.

## Development and Deployment Limits

Local Python 3.12 is available on Windows. Docker CLI's Linux daemon was unavailable initially; Docker Desktop was subsequently started and server 29.5.3 responded during BP-01. Cargo is absent. Target Linux/accelerator/container, Rust, browser and actual PostgreSQL tests belong to their dependent phases; Docker availability alone does not pass them. Do not substitute SQLite or an in-memory store as evidence for PostgreSQL transaction correctness.
