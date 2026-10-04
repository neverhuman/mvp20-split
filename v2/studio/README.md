# Graph Studio

Status: BP-05 closed100%; all four children and integrated parent audited. BP-06 owns scientific knowledge/evidence integration. Architecture: [Studio](../docs/Architecture/Experience/Studio.md), [read-model protocol](../docs/Architecture/Experience/Studio_Read_Model_Protocol.md).

This independently packaged browser consumer owns presentation state and public HTTP transport. It owns no run database, scientific rules, execution authority or backend credentials. Runtime observations are authoritative; notifications request refresh rather than patching graph state. Monitor implements scoped observations, authored topology, occurrence navigation, linked evidence and bounded historical pins. Design implements next-campaign drafts, reviewed tool/schema forms, comparison, explicit rebase, pinned validation and owner-requested activation. Emergency termination is a separate operational control. Scientific Explore/Compare producers remain later owners.

| Module | Rebuild responsibility | Owned tests |
|---|---|---|
| [contracts](src/contracts/README.md) | Reproducible schema-derived DTOs and runtime response validation | `tests/contracts/` |
| [transport](src/transport/README.md) | Abortable bounded reads and sanitized failures through one same-origin adapter | `tests/transport/` |
| [presentation](src/presentation/README.md) | Bounded inspection plus separately modeled emergency controls | `tests/browser/` |
| [page models](src/page_models/README.md) | One loader per region, coherent windows, selection/revision races and invalidation reconciliation | `tests/page_models/` |

Node24 is the local build/test profile. Exact versions are in `package.json`/`package-lock.json`; use `npm ci --ignore-scripts` in this directory, then `npm test`. `npm run generate` intentionally refreshes public contract derivatives; `npm run check:contracts` rejects drift. `npm test -- --area=transport --coverage` runs one owned suite after generation/type checks. Repository dispatch: `v2/dev/.venv/Scripts/python.exe v2/dev/run_tests.py --module studio --area transport --coverage`.

The Python-published serialization schemas remain canonical. Generated files are reviewed build artifacts, not a second schema authority. AJV validates actual received JSON without coercion, defaults or property removal. Local fixtures are explicitly synthetic. B1 HTTP fixtures, B2 measured canvas/list, B3 production-client browser failures and V1 actual installed-owner browser/replacement all pass within their named scope. See [integration evidence](../docs/Audits/Evidence/BP-05-Interaction/V1.json) and [scoped audit](../docs/Audits/BP-05.01_Interaction_Closeout.md).

`/api/runtime` is the declared same-origin gateway adapter prefix, not a claim that a deployed gateway exists. Session/backend credential handling must remain server-side. Components have no local fetches. AuthoringClient carries versioned draft commands and a separate revision-bound runtime.cancel command. Human edits target next-campaign drafts; this package cannot alter a live scientific pathway.

Replacement must preserve generated wire compatibility, bounded reads, cancellation plus generation fencing, truthful stale/denied/partial states and selection scope. Preserve local drafts/layout independently of Runtime revisions and retain exact unresolved command identity during recovery. No persistent browser run store is introduced. [B2 prototype](spikes/interaction/README.md) records the measured React Flow/Cytoscape comparison and actual browser evidence; its synthetic evidence remains distinct from the subsequently accepted B3 production-client browser failures and V1 actual owner integration.

Latest acceptance: BP-05.02 closed100%; final-source scopee222d4cf32604d729ef12146860bc49c passes both independently installed65-test browser builds and actual-owner replacement. [Navigation audit](../docs/Audits/BP-05.02_Navigation_Closeout.md).

Active authoring boundary: [Design models](src/page_models/design/README.md) own draft state, original receipts, reviewed tool/schema discovery, structural comparison and scalar forms. Schema/form models do not grant execution or scientific authority. Emergency control is operational Monitor behavior, independent of draft saves. BP-05.03 authoring, current eligibility, conflicting writers, cancellation orderings and registered-command crash recovery passed. [Authoring audit](../docs/Audits/BP-05.03_Authoring_Closeout.md).135 tests pass in each of two independent Studio installs; actual-owner scopeffe3e49ccc90476684fe8477809f75cd passed25 cases. The module remains an internally hosted consumer, not a deployed authentication gateway.

[Integrated Studio audit](../docs/Audits/BP-05_Studio_Closeout.md) records final137-test independent builds,25 real-owner cases, bounded local performance and focused module replacement. No deployment gateway, scientific applicability, native-zoom/screen-reader conformance or target-host performance claim.

BP-06.06 Studio0.2 adds separate [scientific contracts](src/contracts/scientific/README.md) and [Knowledge/Research transports](src/transport/scientific/README.md). Their exact-query metadata reads are implemented; source provenance and visible Explore are subsequent gates. Existing Monitor/Design and Runtime catalog remain unchanged.
