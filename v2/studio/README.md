# Graph Studio

Status: BP-05.01/B1 transport/page-model spike verified; no rendered UI or selected canvas yet. Architecture: [Studio](../docs/Architecture/Experience/Studio.md), [read-model protocol](../docs/Architecture/Experience/Studio_Read_Model_Protocol.md).

This independently packaged browser consumer owns presentation state and public HTTP transport. It owns no run database, scientific rules, execution authority or backend credentials. Runtime observations are authoritative; notifications request refresh rather than patching graph state. Design/Monitor/Explore/Compare presentation comes in the following gates; current code implements Monitor's transport/state boundary only.

| Module | Rebuild responsibility | Owned tests |
|---|---|---|
| [contracts](src/contracts/README.md) | Reproducible schema-derived DTOs and runtime response validation | `tests/contracts/` |
| [transport](src/transport/README.md) | Abortable bounded reads and sanitized failures through one same-origin adapter | `tests/transport/` |
| [page models](src/page_models/README.md) | One loader per region, coherent windows, selection/revision races and invalidation reconciliation | `tests/page_models/` |

Node24 is the local build/test profile. Exact versions are in `package.json`/`package-lock.json`; use `npm ci --ignore-scripts` in this directory, then `npm test`. `npm run generate` intentionally refreshes public contract derivatives; `npm run check:contracts` rejects drift. `npm test -- --area=transport --coverage` runs one owned suite after generation/type checks. Repository dispatch: `v2/dev/.venv/Scripts/python.exe v2/dev/run_tests.py --module studio --area transport --coverage`.

The Python-published serialization schemas remain canonical. Generated files are reviewed build artifacts, not a second schema authority. AJV validates actual received JSON without coercion, defaults or property removal. Local fixtures are explicitly synthetic. Tests include an actual local HTTP transport but do not establish live Runtime integration or browser usability; B2/B3/V1 own canvas, actual browser and installed owner integration evidence.

`/api/runtime` is the declared same-origin gateway adapter prefix, not a claim that a deployed gateway exists. Session/backend credential handling must remain server-side. The B1 source has no component-local fetches or mutation commands. Human edits will target next-campaign drafts; this package cannot alter a live scientific pathway.

Replacement must preserve generated wire compatibility, bounded reads, cancellation plus generation fencing, truthful stale/denied/partial states and selection scope. Preserve local drafts/layout independently of Runtime revisions when those modules arrive. No persistent browser run store is introduced. Browser/framework/canvas choices remain the measured B2 spike; do not substitute this package's passing Node tests for visual acceptance.
