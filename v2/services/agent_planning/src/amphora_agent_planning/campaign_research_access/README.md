# Campaign Research read boundary

- Status: BP-07.03/B1.02a.i verified; Planning0.33/public Planning0.8.
- Owner: Planning reads/reconciliation only; Research owns declarations, assessment and scientific context.
- Design: [campaign context owner clients](../../../../../docs/Build%20Plans/BP-07/BP-07.03%20Physical%20design.md).

CampaignResearchTransport uses the compiled question, evidence-need and assessment read routes with existing public Research DTOs. Assessment reads send the complete original request; no id-only/latest lookup is substituted. Endpoint configuration permits authenticated127.0.0.1 HTTP with an explicit port. Models cannot supply endpoints, routes, credentials or handlers. There are no writes, automatic retries, redirects, SQL, source-content calls or assessment creation.

The profile bounds a review to20 seconds,160 calls and4MiB aggregate reply bytes, with1MiB per response and256KiB per request. Shared peer_reads adds a trusted per-profile request ceiling; existing Knowledge/extraction Research profiles retain their original4KiB requests, deadlines and call limits. Strict parsing rejects duplicate/nonfinite/malformed JSON. Socket shutdown bounds trickled headers/body. A permitted response is still untrusted until its exact identity and selected-record context pass validation before the window expires.

ResearchRecordReader revalidates the immutable selection and calls only its selected references. Each response must match the exact reference requested, even when another selected reference would otherwise be valid. Completed assessment digest/origin and public nested relationships are checked through campaign_context. Pending/failed statuses remain explicit gaps. Per-record denial/missing/protocol/record-binding failures preserve independent useful records. Outage, deadline or aggregate call/byte exhaustion stops further I/O and records reasons for unattempted selections. Unexpected programming errors propagate.

ResearchReadReport contains the immutable context, identity-bound safe failures and call/byte deltas for this invocation. Gap authority is explicit; a report is neither a transactionally consistent owner snapshot nor scientific sufficiency. No peer body or credential enters an error string. No source processing/egress permission, current-campaign repinning or Runtime acceptance is implied. Missing mandatory context must be handled by later preparation policy, never silently omitted.

Tests belong under tests/campaign_research_access. Scripted responses prove selection/policy behavior; real loopback HTTP proves route/body/authentication/transport limits. Actual Research service compatibility remains B1.02a.iii. The independent context harness also retains legacy Research/Knowledge transport tests to prove old caps remain unchanged. Rebuilds preserve exact routes, schema identities, original request bytes, per-item gaps, bounded review behavior and safe error vocabulary. Typed named views are the next substep and are not implemented here yet.

Verified 2026-10-04 17:41:49:135 focused cases24.87s,193 installed cases8.799s. New reader100%; combined reader/shared transport193 statements30 branches97.76%. Shared transport cleanup lines53/54, alternate EOF79 and two branches remain uninstrumented. [Evidence](../../../../../docs/Audits/Evidence/BP-07-Campaigns/Research_Record_Reads.json).

Actual-owner gate verified 2026-10-04 18:00:02: seven isolated Planning0.34 workers and two Research0.34 hosts, exact public reads, denied/foreign/partial results, retained restart and future-only corrections. See Research_Owner_Reads.json; synthetic owner-local setup does not establish source rights or scientific validity.
