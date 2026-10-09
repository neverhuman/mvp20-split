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
A live terminal released/rejected receipt permits a deliberately new campaign.
An unresolved or admitted-but-not-engaged launch never becomes execution success.
Runtime observation owns node progress. This model does not select drafts, compile
graphs, change active campaigns, start tools or attest scientific accuracy.

Module tests: tests/page_models/launch. Browser integration and actual managed
campaign proof are remaining L3/L4 gates.
