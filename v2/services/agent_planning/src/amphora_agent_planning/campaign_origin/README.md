# Campaign origin projection

- Owner: Planning; UI-01.07/P1 complete; P2 storage pending.
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

No I/O, provider invocation, peer-private access, Runtime mutation or campaign
admission occurs here. The `read_campaign_origin` grant is distinct from attempt
reads and all writes. P2 owns the durable indexed association and replay/backfill;
P3 owns HTTP/authentication and Studio. Neither is implemented by this pure module.

Replacement must preserve exact schema/digest bytes, original identity checks,
bounded failure and honest missing-data semantics. 227 scoped projection/contract/authoring/compiler/schema checks pass. Projection
coverage82/83 statements (98.80%),9/10 branches (90%); no-Research restore branch
remains unexercised, with missing-context projection separately tested. No
installed-package or actual-owner acceptance is claimed yet.
