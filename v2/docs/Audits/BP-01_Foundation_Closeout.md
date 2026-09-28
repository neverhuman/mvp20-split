# BP-01 Foundation Closeout Audit

- Type: component-scoped implementation/architecture drift audit
- Reviewed: `2026-09-23 19:55:48` (America/Chicago)
- Plan: [BP-01](../Build%20Plans/Completed/BP-01%20Contract%20and%20Service%20Foundations.md)
- Baseline: uncommitted BP-01 files atop `99d219c` and architecture refinements; no v1 changes
- Scope: three contract packages, validation-only runtime package, schema fixtures/publication, independent packaging and dev verification
- Disposition: aligned for bounded BP-01 scope; named successor obligations remain

## Evidence and Findings

| Boundary | Observed implementation/evidence | Disposition |
|---|---|---|
| Independent packages | Four manifests and independent lockfiles; four built-wheel installs in fresh environments with only declared public dependency closures | Aligned; no scientific/HTTP dependencies in pure contract installs |
| Contract publication | 18 input/output Draft 2020-12 schemas, SHA-256 manifest, positive/negative fixtures checked by Pydantic and jsonschema | Aligned; frozen DTOs do not establish science or permission |
| Domain behavior | Immutable graph domain view checks identities/routes/cycles/branches/joins; separate invocation policy checks exact bindings/scope and supplied attempts | Aligned; no wide DTO constructor used as runtime orchestration |
| API boundary | Health and graph validation only; structured findings and executable=false; request limits, redacted errors and resolvable OpenAPI references tested | Aligned; no fake run/activation endpoint |
| Isolation enforcement | Source/manifest guard plus injected private-import, undeclared-dependency, dynamic-import and path-injection probes | Aligned as static gate, not a hostile-code sandbox |
| Replacement documentation | README per contract/runtime/dev module with behavior, dependencies/state, failure and replacement limits | Aligned; implementation subset explicit |
| Shared environment leakage | Independent wheel smokes establish imports without repository source path or undeclared science libraries | Aligned |

Verification command: `v2/.venv/Scripts/uv.exe run --project v2/dev python v2/dev/verify_foundation.py --builds`. Result: lint/import/schema checks passed; **39 tests passed**; all four independent wheel/install smokes passed; generated package inventory refreshed. Runs use synthetic inputs, not real scientific data or providers.

Two discovered integration defects were repaired before acceptance: FastAPI Python-object parsing rejected immutable tuple fields valid on the JSON wire, so the HTTP boundary now uses the same strict JSON decoder and explicit generated OpenAPI binding; resolving a mapped drive to a UNC alias made uv rewrite local sources as absolute paths, so build tools retain the invocation path and independent lockfiles again contain portable relative sources.

## Limits and Successor Owners

- BP-02 owns live PostgreSQL transactions, durable command/attempt fencing, outbox, artifact reservations and restart/concurrency. Comparing a supplied fence in a pure policy is not proof of live authority.
- BP-03 owns the complete deployment/resource descriptor, registry, grants, standalone scientific tool and tool protocol lifecycle. Current schema is intentionally a pre-release subset.
- BP-04 owns the executable graph machine, typed data ports/scatter/external waits and full graph semantic compatibility. Current validator checks control structure only.
- BP-05/07/08 retain browser/LLM/Rust conformance; no such acceptance is claimed here.
- Identity, scientific review, external effects and container/host deployment are not implemented. Docker Desktop started successfully and server `29.5.3` responded; no PostgreSQL or cluster was launched by BP-01.
- Starlette's httpx TestClient emits a deprecation warning. Tests pass; dev-tool owner should update the test transport with compatibility evidence during later maintenance. This warning does not block the measured foundation behavior.

No acceptance-blocking drift remains within this plan's declared scope. The pre-existing architecture-readiness findings remain assigned to their dependent plans rather than being waived. Close/archive BP-01 at 100%; next is author/audit BP-02. This audit is not full product, security, performance or scientific certification.
