# Graph Studio

Source release **0.17.0** adds SQ-01/B3/P1 proposal transport, immutable intent
projection and cancellable proposal/criterion models. All285 Studio tests pass;
visible integration and browser qualification remain pending. This source update
does not replace the separately frozen demo assets below.

Current demo release: **0.16.1**, qualified against actual retained owners under
[DEMO-01](../docs/Audits/DEMO-01_Internal_Walkthrough.md). The local entry exposes
execution/authored graphs, checkpoint reasoning, domain/evidence, saved draft
inspection and explicit question/quality focus export. Launch selection pins survive
one-time ticket removal. Frozen assets and operator steps are in the
[presenter guide](../docs/Demo/2026-10-08%20Internal%20Demo.md). AI criterion targeting
and a dependable new-run qualification remain SQ-01/LR-01 work. Earlier release
checkpoints below retain their historical scope; they do not override this status.


Studio0.10 wires the existing checkpoint reasoning inspector into the local Monitor
entry, with the same owned context/disposal lifecycle. Local builds accept an optional
destination argument to scripts/build-local.mjs so new assets can be qualified without
overwriting an earlier deployment. Actual localhost owner/browser acceptance is owned
by tests/integration/local_demo.mjs and dev/verify_local_browser.py; this read-only
trace does not yet assemble Design/Explore/successor navigation into the entry.

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

`/api/runtime` is the same-origin gateway adapter prefix. BP-09.02 now supplies a separately packaged local gateway; successful six-owner deployment remains a later gate. Session/backend credential handling must remain server-side. Components have no local fetches. AuthoringClient carries versioned draft commands and a separate revision-bound runtime.cancel command. Human edits target next-campaign drafts; this package cannot alter a live scientific pathway.

Replacement must preserve generated wire compatibility, bounded reads, cancellation plus generation fencing, truthful stale/denied/partial states and selection scope. Preserve local drafts/layout independently of Runtime revisions and retain exact unresolved command identity during recovery. No persistent browser run store is introduced. [B2 prototype](spikes/interaction/README.md) records the measured React Flow/Cytoscape comparison and actual browser evidence; its synthetic evidence remains distinct from the subsequently accepted B3 production-client browser failures and V1 actual owner integration.

Latest acceptance: BP-05.02 closed100%; final-source scopee222d4cf32604d729ef12146860bc49c passes both independently installed65-test browser builds and actual-owner replacement. [Navigation audit](../docs/Audits/BP-05.02_Navigation_Closeout.md).

Active authoring boundary: [Design models](src/page_models/design/README.md) own draft state, original receipts, reviewed tool/schema discovery, structural comparison and scalar forms. Schema/form models do not grant execution or scientific authority. Emergency control is operational Monitor behavior, independent of draft saves. BP-05.03 authoring, current eligibility, conflicting writers, cancellation orderings and registered-command crash recovery passed. [Authoring audit](../docs/Audits/BP-05.03_Authoring_Closeout.md).135 tests pass in each of two independent Studio installs; actual-owner scopeffe3e49ccc90476684fe8477809f75cd passed25 cases. The module remains an internally hosted consumer, not a deployed authentication gateway.

[Integrated Studio audit](../docs/Audits/BP-05_Studio_Closeout.md) records final137-test independent builds,25 real-owner cases, bounded local performance and focused module replacement. No deployment gateway, scientific applicability, native-zoom/screen-reader conformance or target-host performance claim.

BP-06.06 Studio0.2 adds separate [scientific contracts](src/contracts/scientific/README.md) and [Knowledge/Research transports](src/transport/scientific/README.md). Their exact-query metadata reads are implemented; source provenance and visible Explore are subsequent gates. Existing Monitor/Design and Runtime catalog remain unchanged.

BP-07.05 Studio0.8 adds optional Monitor [checkpoint inspection](src/presentation/supervision/README.md), backed by [owned model](src/page_models/supervision/README.md) and [bounded transport](src/transport/supervision/README.md). This is metadata inspection; no active-campaign human approval or scientific-validity claim.


BP-09.02 Studio0.9 adds a deployable [workspace entry](src/presentation/entry/README.md),
[session transport](src/transport/session/README.md) and [session model](src/page_models/session/README.md).
`npm run build:local` writes dist/local/{index.html,app.js,app.css}. No test fixtures or
owner credentials enter those assets. The entry reuses Monitor for a configured run;
Design/Explore top-level assembly remains explicit integrated-demo work. Readiness is
not inferred from a reachable shell. Standalone schema validators remove runtime eval
and preserve the gateway CSP. Browser tests: `node tests/browser/local_entry.mjs`;
AMPHORA_GATEWAY_TEST_PYTHON selects an independently installed gateway interpreter.
241owned tests and independent Studio generation/build pass. Actual gateway/browser
proof covers desktop/narrow, empty/denied/loading/failure and synthetic Monitor states;
it does not replace six-owner campaign acceptance.

Studio0.11 assembles local Execution/Domain-evidence navigation from an explicit
scoped ExplorePins fragment. The session grants authority independently; invalid
or foreign links supply no research pins. Existing owner projections render actual
concepts, hypothesis posture, metadata and source-format limitations. No graph ids
are inferred from arbitrary artifacts. Hidden modes cancel reads and reconcile on
return; one-use login tickets are removed while non-secret navigation pins survive
reload. Design/successor navigation remains BP-09.03 work.

Studio0.12 adds the scoped saved-draft library and local Design assembly. Draft titles
and exact revisions come from Runtime; dirty/pending work blocks replacement. Real
local owners prove loading, structural validation and unsaved-edit retention across
mode changes. The original numeric draft is explicitly engineering-fixture authored.
Predecessor carry and corrected-successor walkthrough remain separate.

SQ-01/B1 Studio0.14 adds [quality projections and page model](src/page_models/quality/README.md)
over existing strict feedback reads. Exact criterion/evidence identity, multiple
weak points, bounded pages and optional proven Runtime output attachment are
implemented; no new API or scientific verdict. Visible UI is B2, focus/proposals
B3, actual owner/browser/independent qualification V1.

SQ-01/B2 Studio0.15 adds [quality presentation](src/presentation/quality/README.md),
explicit scoped launcher selections and bounded Runtime output proof. Desktop/mobile
quality, existing Explore and actual gateway-entry browser checks pass; actual-owner
quality acceptance remains V1. No new backend route/schema or model call is introduced.

SQ-01/B3 human-focus checkpoint, 2026-10-07 11:51:00, Studio0.16: QualityFocus
owns immutable local drafts of up to32 exact points and two bounded2048character
intent fields. QualityModel retains them through same-context refresh and filters;
hide/denial/failure/rebind/disposal clear them. Export is an explicitly unsubmitted
human JSON document, retaining every unresolved point and optional exact execution
link. No browser storage, owner write, graph repin or model invocation. The inspector
provides save/update/remove and explicit download; renderer owns only form edits and
Blob download cleanup. Export before leaving the view; no reload/import guarantee.
38 scoped tests pass; quality100%lines94.63%branches. Browser verifies exported
contents, filter/navigation retention, axe and no overflow at1440/390; both screenshots
reviewed. Model-result attachment branch covered; defensive/lifecycle branch gaps
remain. Proposal half is blocked on SQ-01.01 criterion-target contract decision;
actual-owner subsequent-campaign and independent replacement acceptance remain V1.
