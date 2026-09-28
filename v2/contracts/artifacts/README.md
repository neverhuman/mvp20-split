# Artifacts Contract Package

- Status: implemented wire/encoding boundary; no durable service authority.
- Owner: BP-02.01; [canonical plan](../../docs/Build%20Plans/BP-02/Completed/BP-02.01%20Contracts%20and%20Command%20Identity.md).
- Architecture: [Runtime protocol](../../docs/Architecture/System/Runtime_Command_Protocol.md), [artifact protocol](../../docs/Architecture/System/Artifact_Publication_Protocol.md).

## Owned Behavior

Content descriptors, provisional/finalized references and reserve/confirm/reconcile payloads. Reservation receipts distinguish RESERVED, CONFIRMED with committed proof, and RELEASED with aborted proof. There is no expiry-based release field. Public parse_command binds the operation family and checks reserve artifact scope against command identity. No caller path is accepted.

## Public API and Dependencies

Only import the public `amphora_contracts_artifacts` root. See `src/amphora_contracts_artifacts/__init__.py` for the explicit surface. The independent pyproject and lockfile define dependencies; no FastAPI, database, filesystem payload access or scientific libraries. Package version 0.1.0, wire version 1. New families extend publication without changing previous core/tool/campaign schemas. Family registry choices belong to the server, not untrusted payloads.

## Semantic and Authority Boundaries

Structural validation and declared-scope consistency do not authenticate identity, authorize an operation, prove a current fence, decide transitions, reserve budget or verify an artifact issuer/outcome. Future owner handlers perform those checks against durable state. UTC lease strings are shape-validated; actual timestamp/calendar validity is an owner semantic check. Domain receipt acceptance is not scientific acceptance. Source diagnostics from Pydantic must not be exposed by API handlers; public canonical parser raises redacted reason codes.

## Verification and Replacement

Tests live under `tests/`; fixtures preserve JSON examples and, for commands, fixed canonical bytes/digests. Run `uv run --project v2/dev --locked python v2/dev/run_tests.py --module contracts-artifacts --coverage` from repository root. Full foundation verification checks dependency isolation, schema publication, all owned tests and optionally clean wheel installs. Schema coverage alone is not semantic coverage; pending authoritative cases are explicitly recorded with runtime/artifact children.

Replacements must preserve canonical bytes, defaults, strict rejection, family/scoping semantics and public schema identity or explicitly version the break. Keep receipts and command data immutable. There is no persisted state to migrate inside this package. Runtime stores must preserve old command digest profiles when introduced; no schema rewrite may silently reinterpret stored identities. Independent package build and old-consumer fixture compatibility are acceptance gates.

BP-02.03/A2 adds UploadContentReceipt: streamed upload/attempt/generation identity with no ArtifactRef. Existing schemas remain compatible; schema publication adds two input/output files. Actual finalization/retention authority remains service-owned.

BP-02.03/A4 adds RuntimeOutcome: a versioned exact ReservationBinding plus a closed prepared/unknown/committed/aborted proof union. This is transport evidence only; the artifact owner authenticates its configured runtime peer and enforces transitions. Existing command and receipt shapes stay unchanged.
