# Campaign origin projection

- Owner: Planning; UI-01.07/P1/P2 complete; P3 API/Studio pending.
- Design: [bounded campaign provenance](../../../../../docs/Build%20Plans/UI-01.07%20Campaign%20provenance%20decision.md).
- Tests: `tests/campaign_origin`; public shape tests belong to contracts/planning.

`OriginProjection` reconstructs a bounded historical compiler projection from
the original verified compiler selection, authoring plan, eligibility configuration
and accepted save observation. Existing original-proposal and receipt/readback
policies are reapplied. A pending receipt, rejected save or missing readback cannot
produce provenance. Construction is pure and does not prove durable storage itself.
The future owned reader must load these inputs through Planning's journals.

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
reads and all writes. P3 owns HTTP/authentication and Studio; neither is implemented yet.

Replacement must preserve exact schema/digest bytes, original identity checks,
bounded failure and honest missing-data semantics. 227 scoped projection/contract/authoring/compiler/schema checks pass. Projection
coverage82/83 statements (98.80%),9/10 branches (90%); no-Research restore branch
remains unexercised, with missing-context projection separately tested. No
installed-package or actual-owner acceptance is claimed yet.

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
