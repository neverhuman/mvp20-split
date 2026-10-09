# Campaign launch recovery

Owner UI-01.06/L3. CampaignLaunch owns one pending immutable launch and its browser
recovery record. LaunchJournal stores request bytes and last verified receipt in
actor/tenant/project-scoped local storage before any POST. No credentials are stored.
Storage failure or a different pending request fails closed. The Deployment journal
is authoritative and prevents duplicate admission across tabs/processes; browser
storage is not a lock or an authority grant.

Restored receipt/run remains hidden until a live original-receipt GET passes exact
identity checks. Refresh never creates another request. An explicit retry reuses
the same bytes; conflict blocks reconciliation. Denial/disposal fence late replies.
For a verified recovery_required receipt with an accepted run, the explicit
"Reconcile original campaign" action replays those same bytes and identity. It
requests Deployment reconciliation, never assumes engagement or creates a run.
A live terminal released/rejected receipt permits a deliberately new campaign.
An unresolved or admitted-but-not-engaged launch never becomes execution success.
Runtime observation owns node progress. This model does not select drafts, compile
graphs, change active campaigns, start tools or attest scientific accuracy.

LaunchPreparation lists one bounded public draft page and installed profile catalog,
checks exact saved revisions through existing Runtime validation commands, and builds
the original admission with profile-bounded budget/deadline. The first Run UI accepts
self-contained prepared drafts only; unbound inputs remain explicit and disable Run.
Scientific parameter fixtures must be published and pinned into the draft by the
preparation workflow; no empty-input fallback is permitted. Generic input selection
and profile choice across multiple installations are not implemented in this UI.

LaunchPlanningContext reads only the exact admitted draft and verifies run/scope/plan
against the Runtime observation. One recognized finish context may be a pinned artifact
constant or original admission input. It is labelled planning context until a matching
finish output exists, never an execution result. Denied or changed pins fail closed.

Module tests: tests/page_models/launch.236 page-model checks pass2026-10-09 09:10:00.
Built-browser fixture launch/reload/node-poll/retention passed at1440/390 with no
serious/critical accessibility violations. Actual managed campaign remains L4.
