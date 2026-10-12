# Campaign curation review

Status: implemented readback and submission presentation; integrated qualification remains P5.
Owner: Studio. Plan: UI-01.08 P3.3c. Reviewed: 2026-10-12.

The internal researcher asks what the next campaign needs and inspects the original
model-requested capability, applicability, typed ports, acceptance criteria and
owner-recorded fulfillment. A compact request list owns selection; one detail pane
owns inspection. Technical identities and evidence references are collapsed.

`CurationPanel` consumes one `CurationModel` and an authenticated-scope selection.
The model owns all reads, immutable records and failure rules. Presentation makes
no requests directly. The separate composer delegates commands to CurationRequestModel. Entry navigation preserves an exact
curation hint; missing, malformed or duplicate hints grant no authority. P4 implements
submission and graph comparison; successor navigation remains the next delivery. No listing endpoint or opaque-ID form is added.

Root and detail loading, missing, failed, stale and denied states are explicit.
Denial clears protected content. Hiding/unmounting clears state and fences responses;
returning reads afresh. Selection moves keyboard focus to the loaded detail heading.
Requested context is never called consumed context. Fulfillment is a historical
owner verification, not scientific validity or current execution eligibility.
Evidence references are inspectable; artifact content is not loaded here.

Replacement acceptance: retain model/transport authority boundaries; run scoped
model/navigation tests and `tests/browser/campaign_curation.mjs`. Inspect actual
1440/390 screenshots, keyboard focus, accessibility, overflow and negative states.
Browser fixtures use scripted public peers and establish no live-model acceptance.

## Revision composer

`CurationComposer` asks for bounded human direction, shows explicitly requested
context counts and submits through the durable request model. It never invents
context, model completion or admission. It restores through exact receipt queries,
with explicit original-byte retries for unknown outcomes. Hiding/unmounting clears
protected models; returning reopens stored intent. Prepared and denied/failed/running
states differ. Request acceptance links to the separately read curation record.

Tests include preparation, request suspension, and curations_request browser fixture
(actual filename tests/browser/curation_request.mjs). Desktop1440/narrow390 screenshots
and WCAG/overflow checks pass. Lost intake reply followed by reload makes exactly one
intake POST and an exact receipt query, then opens the still-queued model record.
This is scripted public-peer evidence; actual owner qualification remains P4.4/P5.

## Graph proposal review

CurationGraphPanel consumes a separate CurationGraphModel for exact revision and
validation reads. Original/proposed switching, nested scope breadcrumbs, bounded
step pages, capability labels, real control/data connections and structural details
answer how the research steps change. Structural validation is distinct from current
execution eligibility and scientific validity. The graph opts into refitting on
canvas resize; ordinary selection preserves the viewport. Public-peer browser proof:
curation-graph-browser-20261012c, desktop1440/mobile390 inspected, all nodes within
canvas after resize, WCAG/overflow and changed-record/denial checks. No live-model
or successor-launch qualification is claimed.

## Successor and next-request controls

SuccessorPanel exposes managed-profile readiness, explicit retained-export input
mapping, original request recovery and an accepted-run navigation action after the
exact graph review. Read-only progress refresh stops while hidden or terminal.
Worker readiness is distinct from Runtime execution. Missing tools/exports, changed
predecessor, denial and unknown launch remain explicit. Next-cycle preparation
requires fresh terminal verification and never posts a model command.

Browser successor-controls-browser-20261012d:1440/390 screenshots inspected, WCAG
and overflow pass. Gateway502 after committed launch then reload uses one intake.
Socket reset caused3 physical browser POSTs of ONE byte-identical intent; recovery
reads that original. This does not replace Deployment idempotency qualification.
Explicit next-cycle preparation sends no launch/model POST. Changed predecessor and
unsupported profiles disable launch. Full production workspace journey remains P4.3d.
