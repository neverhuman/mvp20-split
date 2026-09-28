# Runtime Contract Package

- Status: implemented wire/encoding boundary; no durable service authority.
- Owner: BP-02.01; [canonical plan](../../docs/Build%20Plans/BP-02/Completed/BP-02.01%20Contracts%20and%20Command%20Identity.md).
- Architecture: [Runtime protocol](../../docs/Architecture/System/Runtime_Command_Protocol.md), [artifact protocol](../../docs/Architecture/System/Artifact_Publication_Protocol.md).

## Owned Behavior

Prepared synthetic admission, attempt references/budgets, claim/renew/complete/cancel/revoke payloads and explicit pending/accepted/rejected receipts. Completion reuses tools.Completion. Claim responses distinguish actual invocation/lease from no eligible work. Public parse_command binds a closed operation family and rejects declared artifact/input/checkpoint scope mismatches before returning canonical bytes.

## Public API and Dependencies

Only import the public `amphora_contracts_runtime` root. See `src/amphora_contracts_runtime/__init__.py` for the explicit surface. The independent pyproject and lockfile define dependencies; no FastAPI, database, filesystem payload access or scientific libraries. Package version 0.1.0, wire version 1. New families extend publication without changing previous core/tool/campaign schemas. Family registry choices belong to the server, not untrusted payloads.

## Semantic and Authority Boundaries

Structural validation and declared-scope consistency do not authenticate identity, authorize an operation, prove a current fence, decide transitions, reserve budget or verify an artifact issuer/outcome. Future owner handlers perform those checks against durable state. UTC lease strings are shape-validated; actual timestamp/calendar validity is an owner semantic check. Domain receipt acceptance is not scientific acceptance. Source diagnostics from Pydantic must not be exposed by API handlers; public canonical parser raises redacted reason codes.

## Verification and Replacement

Tests live under `tests/`; fixtures preserve JSON examples and, for commands, fixed canonical bytes/digests. Run `uv run --project v2/dev --locked python v2/dev/run_tests.py --module contracts-runtime --coverage` from repository root. Full foundation verification checks dependency isolation, schema publication, all owned tests and optionally clean wheel installs. Schema coverage alone is not semantic coverage; pending authoritative cases are explicitly recorded with runtime/artifact children.

Replacements must preserve canonical bytes, defaults, strict rejection, family/scoping semantics and public schema identity or explicitly version the break. Keep receipts and command data immutable. There is no persisted state to migrate inside this package. Runtime stores must preserve old command digest profiles when introduced; no schema rewrite may silently reinterpret stored identities. Independent package build and old-consumer fixture compatibility are acceptance gates.

BP-02.04/I6 adds RunSnapshot as an additive wire-v1 observation schema, with conserved budget fields and bounded current activation/attempt views. Its values never confer authority. Existing command canonical bytes/defaults remain unchanged; generated validation/serialization schemas are published alongside prior artifacts.

BP-02.05/D4 adds RuntimeNotification and DeliveryAcknowledgement as closed wire-v1 transport roots. A notification carries stable scoped event/operation identity and an authoritative-state reference; it never grants execution authority. Matching acknowledgement permits delivery bookkeeping only. Consumers deduplicate stable operation identities.
