# Campaign curation review

Status: implemented read-only presentation; integrated qualification remains P5.
Owner: Studio. Plan: UI-01.08 P3.3c. Reviewed: 2026-10-12.

The internal researcher asks what the next campaign needs and inspects the original
model-requested capability, applicability, typed ports, acceptance criteria and
owner-recorded fulfillment. A compact request list owns selection; one detail pane
owns inspection. Technical identities and evidence references are collapsed.

`CurationPanel` consumes one `CurationModel` and an authenticated-scope selection.
The model owns all reads, immutable records and failure rules. Presentation makes
no requests directly and submits no commands. Entry navigation preserves an exact
curation hint; missing, malformed or duplicate hints grant no authority. P4 owns
submission and successor navigation. No listing endpoint or opaque-ID form is added.

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
