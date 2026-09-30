# Studio Read-Model and Transport Protocol

Design status: BP-05.01 closed/accepted. Parent: [Studio](Studio.md). React Flow selected by the [canvas decision](Studio_Canvas_Decision.md). Thirty owned Node tests and independent source builds pass; B1 foundation passed1223 Python tests,19 installs andREC-01..09. B2 measured synthetic interaction and B3 seven production-client browser failures pass. V1 compares12/28 actual Runtime activations and all details across independent browser/Runtime replacement, preserving old cursors. [Audit](../../Audits/BP-05.01_Interaction_Closeout.md). BP-05.02/B1 topology/catalog/evidence navigation is implemented and verified; B2/B3/V1 remain open; the test adapter is not a deployed gateway.

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

B1 owns schema/type reproducibility, pure state/race tests and bounded HTTP contract tests. These fixtures are labeled synthetic. B2 chooses presentation/canvas technology from actual accessibility/layout/update measurements, B3 supplies actual browser failure/viewport evidence, and V1 uses actual backend peers. The gateway adapter prefix is not a deployment claim. Authored-topology projections are implemented under BP-05.02/B1; a global run catalog is not part of the current read surface. Domain graph and fitness views remain dependent on their actual later owners.

The native TypeScript7 package supplies the compiler but not its historical compiler API. The owned source import audit therefore uses explicit dev dependency `@babel/parser7.29.9` for a real TypeScript AST; it does not weaken import checks to a text-only scan or pull owner modules into the browser.

## Shared presentation ownership

The Studio shell owns a single token vocabulary for typography, spacing, color/status, focus and reduced motion. Shared primitives are buttons, labeled fields, status indicators, searchable list rows, the selection inspector, error/empty/loading states and bounded-page controls. Design, Monitor, Explore and Compare compose these primitives; they do not introduce independent visual systems or fetch owners. BP-05.01/B2 established these primitives through the measured browser prototype. BP-05.02 extensions reuse the accepted vocabulary while their own integration acceptance remains pending.

## BP-05.02 inspection extension

Runtime0.13.0/graph-runtime0.7.0 adds explicit occurrence/topology/catalog projections. The browser consumes ten generated authoritative roots, including existing immutable successor lineage, completion records and ArtifactRef metadata. Navigation owns scope/topology lanes under Monitor snapshots; NamedViews owns catalog/lineage; Evidence owns completion/value/metadata. Monitor remains the sole selected-detail and attempt-page loader. All producer identities/cuts are validated before a renderer receives a verified region.

Execution topology uses retained authored edges, scoped occurrence identities and radius0..2 discovery. Source-page edge ownership permits explicitly unresolved targets until their page arrives. The canvas draws only links with both endpoints loaded and retains a separate200-node scene bound. Scientific named views remain unavailable until their owner APIs exist. Completion retention/canonical execution status cannot confer scientific acceptance.

The next policy gate must account for actual producer limits: invalidations identify a run/revision, so live views refresh conservatively at run scope. More granular invalidation must await owner evidence. Historical mutable frontier rows are not retained; a historical inspection may preserve captured bounded data and immutable lineage/completion/artifact metadata with its explicit cut and omissions, but cannot fetch an invented older frontier. Scope/revocation clears protected local state. No authoritative browser history store is introduced.
