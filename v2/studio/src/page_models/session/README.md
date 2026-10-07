# Workspace session model

One owner for entry loading, session context, denied and failed states. Refreshes
clear prior context, and generation fencing prevents late responses from restoring
stale authority. This is browser presentation state, not authentication authority.
Disposal fences outstanding results. No run cache or campaign selection is inferred.
Tests: tests/page_models/session.test.ts.
