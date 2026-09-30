# Graph Studio

Status: BP-05.01/.02 closed with actual-owner replacement accepted. BP-05.03/B1 active: Design editing and separate emergency presentation have scripted-peer proof; actual-owner authoring acceptance pending. Architecture: [Studio](../docs/Architecture/Experience/Studio.md), [read-model protocol](../docs/Architecture/Experience/Studio_Read_Model_Protocol.md).

This independently packaged browser consumer owns presentation state and public HTTP transport. It owns no run database, scientific rules, execution authority or backend credentials. Runtime observations are authoritative; notifications request refresh rather than patching graph state. Design/Monitor/Explore/Compare presentation comes in the following gates; current code implements scoped read-only Monitor transport/state and selection detail; actual Runtime UI observation/replacement is accepted; BP-05.02 now implements authored topology, occurrence navigation, linked evidence and bounded historical pins; its final-source replacement gate is accepted.

| Module | Rebuild responsibility | Owned tests |
|---|---|---|
| [contracts](src/contracts/README.md) | Reproducible schema-derived DTOs and runtime response validation | `tests/contracts/` |
| [transport](src/transport/README.md) | Abortable bounded reads and sanitized failures through one same-origin adapter | `tests/transport/` |
| [presentation](src/presentation/README.md) | Bounded inspection plus separately modeled emergency controls | `tests/browser/` |
| [page models](src/page_models/README.md) | One loader per region, coherent windows, selection/revision races and invalidation reconciliation | `tests/page_models/` |

Node24 is the local build/test profile. Exact versions are in `package.json`/`package-lock.json`; use `npm ci --ignore-scripts` in this directory, then `npm test`. `npm run generate` intentionally refreshes public contract derivatives; `npm run check:contracts` rejects drift. `npm test -- --area=transport --coverage` runs one owned suite after generation/type checks. Repository dispatch: `v2/dev/.venv/Scripts/python.exe v2/dev/run_tests.py --module studio --area transport --coverage`.

The Python-published serialization schemas remain canonical. Generated files are reviewed build artifacts, not a second schema authority. AJV validates actual received JSON without coercion, defaults or property removal. Local fixtures are explicitly synthetic. B1 HTTP fixtures, B2 measured canvas/list, B3 production-client browser failures and V1 actual installed-owner browser/replacement all pass within their named scope. See [integration evidence](../docs/Audits/Evidence/BP-05-Interaction/V1.json) and [scoped audit](../docs/Audits/BP-05.01_Interaction_Closeout.md).

`/api/runtime` is the declared same-origin gateway adapter prefix, not a claim that a deployed gateway exists. Session/backend credential handling must remain server-side. Components have no local fetches. AuthoringClient carries versioned draft commands and a separate revision-bound runtime.cancel command. Human edits target next-campaign drafts; this package cannot alter a live scientific pathway.

Replacement must preserve generated wire compatibility, bounded reads, cancellation plus generation fencing, truthful stale/denied/partial states and selection scope. Preserve local drafts/layout independently of Runtime revisions when those modules arrive. No persistent browser run store is introduced. [B2 prototype](spikes/interaction/README.md) records the measured React Flow/Cytoscape comparison and actual browser evidence; its synthetic evidence remains distinct from the subsequently accepted B3 production-client browser failures and V1 actual owner integration.

Latest acceptance: BP-05.02 closed100%; final-source scopee222d4cf32604d729ef12146860bc49c passes both independently installed65-test browser builds and actual-owner replacement. [Navigation audit](../docs/Audits/BP-05.02_Navigation_Closeout.md).

Active authoring boundary: [Design models](src/page_models/design/README.md) own draft state, original receipts, reviewed tool/schema discovery, structural comparison and scalar forms. Schema/form models do not grant execution or scientific authority. Emergency control is operational Monitor behavior, independent of draft saves. BP-05.03/B1 actual-owner authoring/replacement/cancellation passed; B2 policy and B3 recovery gates remain open.
