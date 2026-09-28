# Core Wire References

- Status: implemented foundation subset, package `amphora-contracts-core` 0.1.0 / wire v1
- Architecture: [Contract Architecture](../../docs/Architecture/System/Contract_Architecture.md)
- Owner: contract primitives; no database or scientific policy

## Behavior and Public Boundary

Public imports from `amphora_contracts_core` expose frozen, strict, closed records for `Scope`, `SchemaRef`, `ArtifactRef`, `Finding` and reusable ID/digest/integer definitions. IDs are bounded ASCII; digests require lowercase SHA-256 syntax; integers are JSON-safe. Artifact references bind scope, schema, content identity, size and media type. They do not grant access, prove bytes exist or validate scientific content.

## Dependencies, State and Failure

Only Pydantic and the standard library. No filesystem/network effects, credentials, runtime state, mutable cache or domain owner imports. Invalid shape/version/unknown fields raise Pydantic validation errors; consumers must sanitize errors before exposing them. JSON mode intentionally maps arrays where downstream contracts use immutable tuples; Python-object validation is strict.

## Replacement Contract

Preserve public exports, input/output schema identity, strict unknown-field rejection, JSON-safe values and frozen record behavior. Consumers: tool/campaign contracts, runtime transport and verification. No persistent state to migrate in BP-01. Change wire meaning only with explicit schema/package version and compatibility fixtures; a schema reference is not an authorization token.

## Verification

Shared wire fixtures and independent JSON Schema validation run through [foundation verification](../../dev/README.md). Each package is also built and installed into an isolated environment. Generated schemas live in `../schemas/v1/`; they are outputs, not handwritten authorities. Rust/browser conformance and physical artifact verification remain later gates.

## Owned Tests

`tests/test_wire.py` owns this package's strict input/serialization and JSON Schema conformance cases using shared language-neutral examples under `contracts/fixtures/v1`. Core additionally checks immutable scope; tools checks version/unknown-field rejection. The suite measures `src/amphora_contracts_core`; schema import coverage alone is not semantic coverage. More schema edge cases remain future contract-change work.

From repository root: `uv run --project v2/dev --locked python v2/dev/run_tests.py --module core --coverage`. Test and coverage reports are written under `v2/.test-results/core/`. Preserve these tests as the package replacement boundary.
