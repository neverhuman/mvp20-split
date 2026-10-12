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
submission; successor navigation and graph comparison remain the next delivery. No listing endpoint or opaque-ID form is added.

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
