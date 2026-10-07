# Workspace session model

One owner for entry loading, session context, denied and failed states. Refreshes
clear prior context, and generation fencing prevents late responses from restoring
stale authority. This is browser presentation state, not authentication authority.
Disposal fences outstanding results. No run cache or campaign selection is inferred.
Tests: tests/page_models/session.test.ts.

WorkspaceSelection owns untrusted launcher-link interpretation. An optional single
`explore` fragment value contains explicit ExplorePins, bounded to8192 total selection
characters, decoded by existing published reference validators and checked against
the authenticated session scope. Missing/invalid links expose no pins; no owner
request, scope grant, persistence or inference from arbitrary artifacts occurs.
Tests in tests/page_models/workspace_selection.test.ts cover malformed, duplicate,
oversized and cross-project links and frozen successful selection.

SQ-01 adds optional single `feedback` and `quality_output` fragment values within
the same8192-character envelope. WorkspaceFeedbackSelection validates exact FeedbackPins
and session scope; WorkspaceQualityOutputSelection accepts only activation_id/port,
never another run or arbitrary path. Existing ExplorePins remain required for the
local research workspace. These selections grant no authority and infer no graph,
question or consumer. Tests live in page_models/quality selection/runtime_link.
