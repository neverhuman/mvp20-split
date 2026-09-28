# BP-01 — Contract and Service Foundations

## Canonical Execution Tracker

- Status: complete
- Last refreshed: `2026-09-23 19:55:48` (America/Chicago)
- Baseline: `99d219c` plus reviewed, uncommitted architecture/MBT refinements through `2026-09-23 11:04:44`; v1 remains frozen
- Owner: foundation implementation; parent/program: [Master Build Tracker](../Master%20Build%20Tracker.md)
- Overall implementation: 100%; four equally weighted phases, each measured by its listed task/gate completion
- Current phase/task: none; all four phase gates complete
- Next task: author/audit BP-02 Durable Runtime and Artifact Foundation
- Remaining exit: none within BP-01; successor runtime/scientific gates remain separate
- Evidence: 39 tests, 18 schemas, four isolated wheel installs, dependency/lint checks and [closeout audit](../../Audits/BP-01_Foundation_Closeout.md)
- Blockers: none; Docker Desktop is now running, while Rust is deferred to its own implementation gate
- Human acceptance: none required for this bounded foundation; user authorized execution until input is needed
- Active exception: none
- Pre-activation audit: `2026-09-23 19:37:00`, ready for bounded foundation implementation

| Phase / status | Implementation | Prerequisites | Bounded deliverable | Verification / exit | Evidence |
|---|---:|---|---|---|---|
| 1. Decisions / complete | 100% | Architecture + owner authorization | Stack, package isolation, schema subset and local tooling posture | Decisions distinguish implemented, selected and deferred behavior | [Decisions](../../Architecture/System/Foundation_Decisions.md); Python 3.12 and uv 0.12.18 available |
| 2. Contract families / complete | 100% | Phase 1 | Shared references; tool descriptor/invocation/result; initial typed campaign definition | Strict negative/positive fixtures, external JSON Schema validation, deterministic publication | 21 tests passed; 18 published input/output schemas plus digest manifest |
| 3. Isolated service seam / complete | 100% | Phase 2 | Independently packaged runtime validation service and pure graph boundary objects; private-dependency enforcement | API contract/rejection checks, forbidden-import probes, no persistence/execution claims | 39 tests passed including stale bindings, scope isolation, DAG/loop rules, OpenAPI references and injected forbidden imports |
| 4. Reproducible delivery / complete | 100% | Phase 3 | Package builds/isolated installation checks, verification entry point, module READMEs and inventory | Clean dependency installation, complete foundation checks, drift audit/archive | Four independent wheel/install smokes; [closeout audit](../../Audits/BP-01_Foundation_Closeout.md) |

## Objective and Scope

Implement the smallest foundation for [contracts](../../Architecture/System/Contract_Architecture.md), [service isolation](../../Architecture/System/Service_Isolation.md) and [Graph Runner](../../Architecture/System/Graph_Runner.md). Keep independent package manifests and environments; do not scaffold every future service. No huge backend or shared business-policy package.

The initial graph schema supports typed invoke, branch, join and bounded iteration declarations. Validation checks identities/edges/loop containment and compatibility references; this is not an interpreter or scientific compiler. Primitive IDs, scoped artifact references and immutable version/digest bindings support the next persistence/tool plans. Tool scientific payloads refer to registered schemas/artifacts, not unrestricted inline objects or a universal score.

Excluded: durable database/run implementation (BP-02), tool deployment/registry (BP-03), execution/interpreter (BP-04), UI (BP-05), knowledge reasoning (BP-06), actual model calls (BP-07), Rust kernel extraction (BP-08), cluster deployment (BP-09). Authoring a schema does not establish scientific correctness, Rust conformance, real authorization or production readiness. The foundation API must not accept execution or expose a pretend successful run.

## Ordered Tasks

1.1 Record Python/web/persistence/build choices and the contract/encoding compatibility policy in a focused System child. 1.2 Verify Python/environment and dependency installation; document unavailable target tooling without inventing a block to pure foundation work.

2.1 Implement independently packaged core, tool and campaign contract families with closed strict wire models and explicit tags/versions. 2.2 Create meaningful valid/invalid fixtures including unknown fields, unsupported versions, scope mismatch, invalid output disposition and graph references. 2.3 Publish input/output JSON Schemas with deterministic manifest digests; validate fixtures with Pydantic and an independent JSON Schema validator, documenting semantic checks not expressible in schema.

3.1 Implement a runtime-owned immutable graph domain view/validator separated from transport DTOs. 3.2 Expose health and graph-validation endpoints through a thin FastAPI adapter, with structured findings and no execution. 3.3 Enforce declared external imports and public contract-only cross-owner imports; test the enforcement against deliberately invalid source fixtures, not just a passing empty repository.

4.1 Lock dependencies independently and build/install each package from declared dependencies. 4.2 Add a repeatable verification entry point, module replacement READMEs, contract inventory and concise evidence. 4.3 Compare actual boundaries against architecture, repair in-scope drift, archive this plan and synchronize MBT/Restore. Prepare BP-02 next; do not claim persistence acceptance without real PostgreSQL tests.

## Pre-Activation Coherence Audit

Checked scope against MBT and current requirements. Four bounded phases have dependency order and observable exits. Contract families precede service consumption; independent installs prevent accidental shared-environment dependencies. Numerical/scientific authority, durable runtime and UI remain distinct successor acceptance. Existing schema architecture lists broader Rust/UI/replay acceptance; this plan proves only its explicitly named Python/interchange subset. Later plans retain those obligations. No mandatory human gate blocks authorized engineering choices. Docker and Rust absence do not block these gates. Disposition: ready.

## Checkpoints and Closeout

All defined phase gates passed. [Closeout audit](../../Audits/BP-01_Foundation_Closeout.md) records aligned boundaries, observed tests and explicit successor limits; archive at 100%.

- `2026-09-23 19:43:01`: Phase 2 gate passed; 21 interchange/publication tests, 18 schemas. Domain semantics and runtime HTTP acceptance belong to Phase 3.

- `2026-09-23 19:49:05`: Phase 3 gate passed after repairing strict JSON parsing at the HTTP boundary. 39 checks passed; one upstream Starlette/httpx deprecation warning retained for follow-up. No database or runtime execution implemented.

- `2026-09-23 19:55:48`: Phase 4 and scoped closeout passed. 39 tests, four isolated wheel/install smokes and deterministic schema/import/lint checks; no durable runtime or scientific claims.
