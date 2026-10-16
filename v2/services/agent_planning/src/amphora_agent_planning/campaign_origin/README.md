# Campaign origin projection

UI-01.08/P2.2 reads the explicit compiler-review projection for common rationale/
action fields while retaining original curation output hash/schema/context.
A curation proposal is not a repaired legacy provider capture.

- Owner: Planning; UI-01.07/P1-P4 complete; qualified2026-10-11 19:26:42.
- Design: [bounded campaign provenance](../../../../../docs/Build%20Plans/UI-01/UI-01.07%20Campaign%20provenance%20decision.md).
- Tests: `tests/campaign_origin`; public shape tests belong to contracts/planning.

`OriginProjection` reconstructs a bounded historical compiler projection from
the original verified compiler selection, authoring plan, eligibility configuration
and accepted save observation. Existing original-proposal and receipt/readback
policies are reapplied. A pending receipt, rejected save or missing readback cannot
produce provenance. Construction is pure and does not prove durable storage itself.
The owned reader loads these inputs through Planning's journals.

The public response pins an exact scoped draft, original producer/attempt/preparation/
proposal, context reference identities, observed usage, selected tool releases and
accepted save receipt. Research metadata distinguishes consumed question/need
criterion IDs from explicit follow-up targets; selected missing records remain gaps.
Raw prompts/provider output/private preparation packets are excluded. The current
compiler retains its capture privately, so publication is explicitly unavailable.

Canonical sorted compact UTF-8 JSON defines the origin body digest. The full wire
response is limited to256KiB and fails with `origin_response_limit`; no truncation.
Restore checks the digest, requested draft, scope, save commit and Research selection
membership/completeness. A digest proves consistency, not a signature or authority.
Historical compilation establishes neither current eligibility nor scientific truth.

The pure projection performs no I/O. The owned index/reader below use Planning SQL
only; there is no provider invocation, peer-private access, Runtime mutation or admission. The `read_campaign_origin` grant is distinct from attempt
reads and all writes. P3 implements HTTP/authentication and independent Studio verification.

Replacement must preserve exact schema/digest bytes, original identity checks,
bounded failure and honest missing-data semantics. 227 scoped projection/contract/authoring/compiler/schema checks pass. Projection
coverage82/83 statements (98.80%),9/10 branches (90%); no-Research restore branch
remains unexercised, with missing-context projection separately tested. Later P4 qualification below supersedes this early verification checkpoint.

## Owned lookup and reconstruction (Planning0.106.0)

Migration0021 adds campaign_origins, indexed by scope/draft/revision, with an exact
content hash and bounded pointer to compiler selection/effect/observation. The
service can SELECT/INSERT, never update/delete. CompilerJournal.append records the
pointer before its final lease fence, inside the accepted observation transaction.
Pending/rejected effects do not create a pointer; replay is identical or fails closed.
No full response is generated during save, so oversized metadata cannot veto a valid
campaign save. A conflicting lookup fails instead of attributing another proposal.

CampaignOriginReader requires read_campaign_origin before SQL. It reconstructs the
producer through owner-internal read-only journals; it never changes the external
viewer's actor/grants or contacts peers as the producer. Index hashes/columns and
original history are both checked. Missing is None, changed draft pins and corruption
are explicit errors, and the final public response remains bounded256KiB. No scan,
provider call, compiler dispatch or current scientific/eligibility claim follows.

OriginBackfill is owner maintenance, not a public write route: original actor with
record_attempts/read_attempts supplies1..64 unique selection IDs. Each selection is
independently atomic under the compiler lock; missing/pending effects create no origin.
Retry preserves first pointer/history. Rebuild uses retained effects, never peer SQL.

The served projection will use planning.campaign-origin-knowledge/v1 (body2); the
initial origin/v1 wire root remains unchanged. Exact graph context can exist outside
Artifact entries. KnowledgeOrigin reads only the verified retained graph slice.
Unavailable older slices lack head/entity pins and report that absence. Capture
publication refers only to the compiler's retained association, not a global Data
publication search. Public graph/content access still requires its owner's grant.

Evidence:38 PostgreSQL storage/compiler checks; index/reader146/146 statements,
13/14 branches (unprepared-effect backfill path not exercised).43 focused projection/
Knowledge/schema checks,124/124 statements and18/18 branches;236 post-sync contracts
and independent SQL-reader checks. Production boundary guard passes. Independent
installed-package and actual-owner/browser qualification remain P4. Deploy migration
0021 before running this compiler; serving code never applies DDL.

## Authenticated read (Planning0.107.0)

GET /v1/campaign-origins/{draft_id}?revision=...&content_sha256=... returns the
Knowledge-aware projection. Scope comes exclusively from the configured principal;
read_campaign_origin is required before existence lookup. Exactly two unique query
fields, a positive safe revision, exact digest and no request body are accepted.
No list/latest/mutation/backfill route exists. Missing association is named404,
not inferred human authorship; denied403, inconsistent history409 and bounded
response limitation422 remain distinct. Private diagnostics are sanitized. Success
is canonical JSON with no-store. Ready checks migration0021; serving applies no DDL.

18 focused HTTP cases and69 API/Gateway transport checks pass.29 actual-SQL origin
route and existing supervision API checks pass, including foreign-scope404 and
unchanged compiler history. P4 qualification is complete; see the current checkpoint below.

## Current qualification

2026-10-11 19:26:42:206 independent Planning tests pass; Gateway58 independent
checks and Studio349 checks pass. Actual deterministic proposal preparation selected
public Research criteria and the retained Knowledge graph before hashing. Original
compiler saved/validated a four-invocation scientific draft; the browser launched
that draft and inspected its exact origin/Research/Knowledge after completion.
Local/LAN1440/390 and negative manual-origin/changed-pin checks pass. An actual
Planning process replacement returns the same origin digest without another provider
call. Response15377bytes, observed local read3.562s (not a latency guarantee).
No live-model/scientific accuracy claim. [Scoped audit](../../../../../docs/Audits/UI-01.07_Campaign_Provenance.md)
owns detailed evidence and limitations. Coverage gaps above remain explicit.
