# Studio Read-Model and Transport Protocol

Design status: BP-05.01/B1 verified spike. Parent: [Studio](Studio.md). React Flow selected by the [B2 canvas decision](Studio_Canvas_Decision.md); synthetic browser proof does not establish live-owner acceptance. The independent Node source rebuild and28 owned tests pass; the combined foundation gate passed 1223 Python tests, 19 isolated installs and REC-01..09. B2 synthetic interaction is verified; B3 production-model browser failure proof is active.

## Authority and data ownership

The initial consumer targets Runtime0.11.0 and graph-runtime0.5.0 observation routes. Backend owners retain authentication, execution authority and durable history. A thin same-origin gateway keeps scoped owner credentials server-side; browser code sends session requests, not embedded service keys. No second run database or scientific policy layer belongs in Studio.

Each visual region has one loader: graph window, selected detail and event invalidation position. Rendering components receive props from the page model and do not fetch competing copies. Query scope, run, revision and selection participate in request identity. Cancellation is backed by generation checks so an uncancellable late response cannot replace a new run, selection or revision.

## Wire and tooling choice

Generate TypeScript declarations from the published Python-owned serialization schemas and retain their SHA-256 provenance. Validate received JSON against the same Draft2020-12 schemas; static types alone are insufficient. Exact package versions are recorded in the Studio lockfile: TypeScript7.0.2, AJV8.20.0, ajv-formats3.0.1 and json-schema-to-typescript16.0.0; local build/test profile Node24.18.0, npm11.16.0. Version selection was checked against npm metadata on2026-09-29; these are implementation pins, not a recommendation to update other applications.

AJV documents [Draft2020-12-specific support](https://ajv.js.org/json-schema) and [strict validation](https://ajv.js.org/strict-mode). The consumer registers Pydantic's OpenAPI discriminator as annotation metadata while retaining the authoritative `oneOf`/`const` validation. Data coercion/default insertion/property deletion remain disabled. [json-schema-to-typescript](https://github.com/bcherny/json-schema-to-typescript) supplies declarations; runtime validation retains limits that TypeScript cannot express. [Node's test runner](https://nodejs.org/docs/latest-v24.x/api/test.html) supplies module-local tests/coverage without selecting a UI framework.

## Refresh and bounded state

The graph window uses explicit pages and reports loaded versus matching/omitted nodes. Page append requires the same cut and query; duplicate membership or false completeness is an error. No automatic whole-graph download is introduced. B2 adds measured visible-scene budgets and progressive expansion over200 visible/10000 logical synthetic nodes.

A selected detail must match both activation and cut. Refresh preserves selection within a run while clearing the old detail until the new cut is verified. Changing run/scope clears selection. Live snapshots cannot claim immutable historical mutable frontier storage: changed Runtime revisions require a fresh snapshot, while terminal campaigns and immutable receipt/evidence endpoints support historical inspection.

Invalidations mean refresh, never graph patches. The client verifies sequence/identity, deduplicates within a bounded replay window and never rewinds its cursor. Gaps/expiry force resnapshot. Visible regions refresh once; hidden regions mark stale until activation. Poll ownership stays with the active page scheduler; no blanket component polling. Stale/denied/partial/empty/loading/failed states are explicit and denied access clears the graph view.

## Verification boundary

B1 owns schema/type reproducibility, pure state/race tests and bounded HTTP contract tests. These fixtures are labeled synthetic. B2 chooses presentation/canvas technology from actual accessibility/layout/update measurements, B3 supplies actual browser failure/viewport evidence, and V1 uses actual backend peers. The gateway adapter prefix is not a deployment claim. Full run catalog and authored-topology projections are still reconciled in BP-05.02 before live navigation. Domain graph and fitness views remain dependent on their actual later owners.

The native TypeScript7 package supplies the compiler but not its historical compiler API. The owned source import audit therefore uses explicit dev dependency `@babel/parser7.29.9` for a real TypeScript AST; it does not weaken import checks to a text-only scan or pull owner modules into the browser.

## Shared presentation ownership

The Studio shell owns a single token vocabulary for typography, spacing, color/status, focus and reduced motion. Shared primitives are buttons, labeled fields, status indicators, searchable list rows, the selection inspector, error/empty/loading states and bounded-page controls. Design, Monitor, Explore and Compare compose these primitives; they do not introduce independent visual systems or fetch owners. B2 chooses concrete values and a framework through the measured rendered prototype. This is an ownership declaration, not a claim that the components are rendered or accepted yet.
