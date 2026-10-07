# Local workspace entry

UI-01 N1 adds a question-first landing and Question / Approach and run / Results
and evidence / Next iteration navigation. These compose existing owner views;
they do not claim a new results aggregation API. Missing question or domain pins
remain explicit empty states. Overview reads exact question/need records through
FeedbackModel with optional downstream pins omitted, so an unavailable assessment
cannot hide the objective. Evidence assessment remains in the evidence view.
Overview hides/clears and cancels reads when inactive or document-hidden.
The session workflow helper owns bounded `view` hints and preserves exact selection
parameters (including duplicates for validators); it never copies launch secrets.
Reload restores the selected workflow view. Mounted perspectives preserve local
selection and viewport on navigation; page reload re-reads owner records and does
not imply persistence of unsaved drafts or local canvas pan in browser storage.

DEMO-01 actual-owner rehearsal found that entry.tsx retained only the explore
fragment when removing the one-time launch ticket. It now preserves the three
supported selection keys (explore, feedback, quality_output), including duplicates
for the owning selectors to reject. Ticket removal and session authority are
unchanged. Actual local browser qualification covers question/quality selection
and focus export against real Research records, not merely direct model fixtures.

Owns the compact application identity/local-access strip and session states.
WorkspaceSession owns loading, denial and failure. An authenticated session with
no selected run renders an explicit empty view; it does not fabricate a sample or
claim that no campaign exists on the backend. A selected run reuses Monitor's
existing graph, navigation and evidence models and styles. Each model is disposed
on context replacement. No owner fetches live in presentation components.

Studio0.10 also injects the existing SupervisionModel into Monitor's checkpoint
reasoning region. Users can follow actual checkpoint requests, included/omitted
context, model outcomes and immutable response metadata. Runtime owns every read;
the entry adds no approval, mutation or scientific authority. The model follows the
same context replacement/disposal lifecycle as the graph and evidence models.

This hosting entry exposes Monitor, checkpoint reasoning and explicit domain/evidence
navigation. Design/successor and emergency controls remain explicit assembly work. Browser acceptance must check
entry/session/error/empty states and monitor rendering at desktop/narrow widths.

Studio0.11 hosts Execution and Domain/evidence modes. A launcher may select explicit
ExplorePins in the URL fragment `explore` value (JSON encoded with URLSearchParams).
WorkspaceSelection validates size, uniqueness, published reference shapes and equality
with authenticated scope; links never grant authority. Missing/invalid context renders
a truthful empty/error view with execution still available. No implicit graph ids or
fixture-format interpretation. No selection is persisted in browser storage.
Modes remain mounted after first visit to preserve local controls; inactive models
cancel reads and reconcile on return. Session identity replacement disposes all models.
LocalKnowledge only composes existing owner clients and ExploreModel; graph/source/
artifact authority remains with existing services. Design/successor assembly remains.

Studio0.12 adds Next campaign with a bounded scoped draft library. Users choose titles
and saved revisions, not opaque ids. Library owns reads and loaded command/catalog
objects; LocalDesign renders states and existing DraftWorkspace. Local edits and
unresolved commands prohibit draft replacement. Mounted modes retain editing work;
mutations are not cancelled merely by changing views. Session replacement disposes
all owners. Initial hosting selects existing drafts; creating a draft from campaign
context and predecessor carry remain explicit successor assembly work.

SQ-01 Studio0.15 composes optional FeedbackModel and QualityLinkModel from explicit
launcher selections. LocalKnowledge creates their existing public clients; question
reads and bounded Runtime output reads run only while the feedback surface is
visible. Parent-mode visibility cannot be bypassed by document visibility events.
Invalid question/output links are isolated from valid Explore/Execution views.
No credentials, owner mutations or inferred associations enter these components.
