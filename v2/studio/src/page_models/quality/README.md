# Scientific quality projection and page model

Owner: SQ-01/B1. This region helps an internal researcher inspect weak points and
their exact evidence before choosing next-campaign work. It does not assess
science, mutate campaigns, publish corrections or authorize proposals.

`QualityProjection` consumes an already validated immutable `FeedbackLineage`.
Each criterion retains its exact question/need/assessment/profile identity,
description, owner gap reason and supporting/contradicting ArtifactRefs. Presentation
categories group existing reasons; they are not new verdicts. Missing decisions,
unselected/pending/failed assessments, unknown answers, contradictions and unmet
evidence requirements remain separate from transport or execution status. A
supported criterion does not mean scientifically established. Calibrated accuracy
and demonstrated error are unavailable in the current owner contract, never inferred.
Adjacent correction records remain separate annotations; pinned records are unchanged.

`QualityAttachment` accepts a pinned Runtime snapshot/node and at most32 explicitly
loaded value pages for one output. It reuses EvidenceContext cut/scope/membership
checks and joins only by the complete ArtifactRef identity of an assessed subject.
Partial membership is explicit; no match means unlinked, not no consumers. Scope,
label similarity or shared bytes alone do not establish an affected node. Execution
status remains a separate field. It performs no cross-owner query or discovery.

`QualityModel` subscribes to one existing FeedbackModel; it never fetches a second
copy. It owns20-row filtering/pagination and local selection. FeedbackModel owns
cancellation, generations, authorization and visibility. Loading, denied, stale,
hidden and failed states clear protected projections. Missing assessment data is
not a network error. Invalid duplicate criterion decisions reject the projection.
Disposing this wrapper unsubscribes and clears it without disposing the host-owned
FeedbackModel. No polling, persistence or background work is introduced.

Tests belong in `tests/page_models/quality/`; transport and FeedbackLineage identity
fixtures remain their own scopes. Rebuilds must preserve exact references, immutable
state, bounded pages, denial clearing, reentrant/late-response safety and no-science
authority. B2 owns visible accessible UI/graph navigation; B3 owns local focus and
public next-campaign proposal presentation. Actual peers/browser/independent Studio
qualification remain V1; pure page-model tests cannot replace those gates.

Verified 2026-10-07 11:14:02:28 focused quality/Feedback/EvidenceContext tests pass;
quality module100% lines97.41% branches,96.30% functions. Disposal/subscription and
defensive invalid-category branches are not all directly exercised. TypeScript
build passes. Same-context refresh preserves selected point; rebind/denial clears
it. No visible UI or actual-owner quality journey is claimed at B1.

B2 adds QualityLinkModel: three bounded public Runtime reads (snapshot, exact
activation detail, first output page), cancellation/generation fencing and explicit
visible lifetime. It never follows guessed consumer links or scans the whole graph.
Wrong run/scope/activation/cut rejects; incomplete output membership stays partial.
One exact ArtifactRef match is necessary for a quality graph marker. The selected
Runtime node label and unresolved-criterion count belong to their owning projection.

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
