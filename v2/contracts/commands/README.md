# Commands Contract Package

- Status: implemented wire/encoding boundary; no durable service authority.
- Owner: BP-05.03 numeric extension; legacy BP-02.01; [canonical plan](../../docs/Build%20Plans/BP-02/Completed/BP-02.01%20Contracts%20and%20Command%20Identity.md).
- Architecture: [Runtime protocol](../../docs/Architecture/System/Runtime_Command_Protocol.md), [artifact protocol](../../docs/Architecture/System/Artifact_Publication_Protocol.md).

## Owned Behavior

CommandIdentity and immutable CanonicalCommand own strict input parsing and canonical identity bytes. The unchanged default v1 profile is bounded to 256 KiB/64 containers, rejects duplicate keys, invalid UTF-8/BOM/surrogates, floats and unsafe integers, and materializes defaults from a supplied registered WireModel. SHA-256 hashes sorted compact ASCII-escaped JSON without a newline. This is distinct from schema publication hashing. for_family rejects a route/family mismatch; no dynamic payload dispatch. Identity and bytes are retained, not mutable input dictionaries.

## Public API and Dependencies

Only import the public `amphora_contracts_commands` root. See `src/amphora_contracts_commands/__init__.py` for the explicit surface. The independent pyproject and lockfile define dependencies; no FastAPI, database, filesystem payload access or scientific libraries. Package version 0.1.0, wire version 1. New families extend publication without changing previous core/tool/campaign schemas. Family registry choices belong to the server, not untrusted payloads.

## Semantic and Authority Boundaries

Structural validation and declared-scope consistency do not authenticate identity, authorize an operation, prove a current fence, decide transitions, reserve budget or verify an artifact issuer/outcome. Future owner handlers perform those checks against durable state. UTC lease strings are shape-validated; actual timestamp/calendar validity is an owner semantic check. Domain receipt acceptance is not scientific acceptance. Source diagnostics from Pydantic must not be exposed by API handlers; public canonical parser raises redacted reason codes.

## Verification and Replacement

Tests live under `tests/`; fixtures preserve JSON examples and, for commands, fixed canonical bytes/digests. Run `uv run --project v2/dev --locked python v2/dev/run_tests.py --module commands --coverage` from repository root. Full foundation verification checks dependency isolation, schema publication, all owned tests and optionally clean wheel installs. Schema coverage alone is not semantic coverage; pending authoritative cases are explicitly recorded with runtime/artifact children.

Replacements must preserve canonical bytes, defaults, strict rejection, family/scoping semantics and public schema identity or explicitly version the break. Keep receipts and command data immutable. There is no persisted state to migrate inside this package. Runtime stores must preserve old command digest profiles when introduced; no schema rewrite may silently reinterpret stored identities. Independent package build and old-consumer fixture compatibility are acceptance gates.

## Explicit numeric profile (Commands0.2.0)

`NUMERIC_ENCODING = "amphora-command-v2"` names an additive opt-in envelope: `{"encoding":"amphora-command-v2","identity":{...},"payload":{...}}`. `CanonicalCommand.parse/for_family(..., allow_numeric=True)` accepts it and still applies the original parser to unmarked envelopes. The default remains v1. Only graph-runtime definition.save and graph.admit_draft opt in; other owners/families reject the marker. `CanonicalCommand.profile` derives the profile from immutable retained bytes. The marker participates in the digest; changing profile under an existing command identity conflicts.

V2 accepts finite binary64 JSON float/exponent tokens, rejects overflow and nonzero underflow to zero, and preserves the v1 safe-integer-token, duplicate-key, Unicode, depth and raw/canonical256KiB bounds. Consuming strict DTOs still decide numeric types and ranges; a float token cannot supply a strict integer field. Normalize both signed zeros to positive zero before/after DTO validation. Default materialization precedes the same sorted compact ASCII JSON encoder; Python3.12 `json.dumps` shortest-round-trip float rendering (including `.0` and exponent signs) is the published server-owned profile. It is not a cross-language canonicalization claim. Finite values in existing graph NumberConstant fields remain bounded to +/-1e100. Runtime NumberValue's decimal-string representation, artifact hashing and schema hashing are unchanged.

`tests/fixtures/canonical_v2.json` pins independent expected bytes/digests for integral numbers, decimals, signed zero, exponent and subnormal values. Tests also prove every legacy vector through the opted-in parser, canonical replay, malformed/non-finite/unsafe inputs and default-materialization limits. Browser producers retain original wire bytes and the owner's receipt digest rather than computing this canonical hash. Future equivalent hash implementations must pass both vector sets. No schema publication changes or migration are required by this additive parser API.
