# Campaign curation inspection state

UI-01.08/P3.3b. Internal SMEs ask what the model proposed, which tool behavior is
missing, and what evidence is recorded for fulfillment. Primary action: select a
requested capability and inspect its original details. Planning CurationView and
CapabilityRequestView own the data. No mutation, provider call, current catalog,
tool installation or scientific authority belongs to this module.

CurationModel owns one root read lane and one lazy detail lane. Selection binds
actor/scope/curation/predecessor; the selected gap comes from the exact original
proposal. Refresh re-reads only this region, preserves a valid selected gap and
rejects changed original command/specification/provider/proposal, regressed revision
or inconsistent same-revision content. No automatic polling or persistent cache.

RecordedCuration and RecordedCapability own immutable copies, source bindings,
phase labels, gap selection and historical fulfillment semantics. Semantic browser
comparison is not a hash of Python canonical bytes. A validated draft is not an
admitted campaign; verified fulfillment is not current scientific/tool eligibility.

Empty selection, named missing, hidden, loading, stale, denied, failed and loaded
records remain distinct. Loading clears previous protected content. Hiding/disposal,
denial and context replacement cancel/fence both lanes and clear protected records;
only the selected reference/bookmark survive hiding for a fresh visible read.
Denial clears the bookmark. Generic detail failure keeps the independently loaded
curation usable. Subscriber-triggered hiding/rebinding cannot start or revive older
reads. Invalid indices cannot fetch an unrelated record.

Presentation will reuse Studio tokens with one compact request list and selected
detail, preserving the distinctions between requested context, original model
output and fulfillment evidence. Browser rendering/1440/390/keyboard acceptance
remain P3.3c. Tests: tests/page_models/campaign_curation; transport owns network and
schema validation. Replacement preserves the two-lane lifecycle and original binding.

Known original terminal curation records cannot restart themselves. Selected
capability baselines (at most16) bind the owner-reported original proposal digest
and retain an immutable verified winner across visible refresh. They clear with
protected state on hiding/denial/context replacement/disposal. Same pending
fulfillment command may reach a terminal result; terminal receipt bytes stay fixed.
A subscriber selecting detail during root refresh suppresses automatic duplicate
selection.22 model/transport/import checks and tsc pass; visual proof remains c.

## Durable browser intent

`CurationRequestModel` owns one original request per campaign context. It freezes
and stores bytes before intake. Reload hides cached acceptance until an exact live
receipt query succeeds. Lost replies stay unresolved; explicit retry reuses original
bytes. Conflicts and storage failures block replacement. Denial/disposal fence late
responses and clear in-memory protected content. Double clicks cannot mint another
request. Request acceptance and subsequent model progress have separate owners.

`CurationJournal` stores untrusted recovery hints in actor/scope/run-specific local
storage. It includes submitted human direction and context references, no credentials.
This is recovery, not a multi-tab lock or owner authority. A changed pending original
cannot be overwritten. New curation cycles after terminal outcome are a separate
explicit transition still to be wired during the remaining successor UI delivery.
Tests: campaign_curation/request.test.ts and transport/campaign_curation/commands.test.ts.

## Exact campaign preparation

`CurationPreparation` reads a fresh scoped Runtime cut and requires a terminal run
before loading the exact launch-bound draft/provenance. OriginalCurationContext
uses verified original Planning provenance; missing origin or unavailable selected
Knowledge blocks preparation explicitly. It preserves original Research refs.
Requested context is not described as everything consumed by the model.
`PreparedCuration` retains up to8 Knowledge heads and rejects duplicates/oversized
context rather than taking the first or truncating. Scope/graph/cut checks precede
request construction. Context reads never submit commands. Denial, clear and disposal
remove preparation and fence late reads. Tests: preparation.test.ts.

## Original and proposed graph review

CurationGraphReader reads exact original and saved draft revisions and validation
from Runtime. CurationGraphReview binds them to the retained model proposal and
original context; substitution, scope drift and changed validation pins fail closed.
An unsaved proposal remains inspectable without a validated claim. Campaign identity
changes are visible. CurationGraphModel owns cancellation, denial and late responses.
curationGraphScene projects real control/data links within one nested scope, at most
200 nodes per window, with explicit omitted counts. Duplicate identities suppress
the canvas. Missing nested scopes are never replaced by the parent scope.
Tests: graph_review.test.ts and graph_model.test.ts; launch is a separate owner.

## Explicit next request

RecordedCuration owns terminal-state classification. CurationNextCycle performs a
fresh exact read and reconciles the terminal original before CurationJournal archives
its exact stored intent and writes an explicit empty-current marker. Archive/storage
failure preserves the original; cancellation before the write fences release. The
next composer creates a separate request only on explicit submission. No provider
retry, budget refund, scope change or automatic command occurs. Earlier journal
records remain readable; the null current marker represents deliberate preparation
for another direction. Tests: next_cycle.test.ts.
