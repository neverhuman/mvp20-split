# Campaign curation intake

UI-01.08/P2.1: Planning0.109/planning0022 adds durable intake and optional HTTP.
Worker scheduling and live campaign input remain P2.2/P2.3, not implemented.
Architecture: ../../../../../docs/Architecture/Agents/Planning.md.

`CurationCommand.bind` reparses the published command, requires authenticated exact
actor/scope plus `record_curations`, admits only operator-configured policy IDs and
rejects duplicate selected graph/question/need/artifact identities. Direction remains
untrusted intent. The stable curation ID hashes normalized command identity; changing
payload bytes under that identity conflicts instead of creating another job.
`reconcile` compares the original parsed command, including original encoding/bytes.
Reads require the original actor/scope and separate `read_curations` grant.

`FulfillmentCommand` requires the distinct `fulfill_capabilities` grant and unique
acceptance Artifact identities. `read_capabilities` is separate. This command cannot
verify a Registry release or scientific evidence by parsing it; P3 owns actual public
peer verification before immutable fulfillment. Existing supervision grants confer
none of these new permissions. Authentication is performed by the HTTP adapter.

This module owns command admission/replay and original intent persistence, not
provider issuance, budget, Runtime admission, process control or cross-service state.
CurationJournal atomically inserts original bytes and queued receipt into the
SELECT/INSERT-only planning.curation_requests table. Advisory identity locks
serialize retries; any exception before commit rolls back the entire record.
Receipt/query and job reads require original actor/scope plus read_curations.
Retired policy IDs remain replayable; new intents require current configured IDs.
OriginalCuration rebuilds and compares every retained identity/digest/receipt field.
No SQL transaction spans provider/peer I/O. Dependencies stay public/owner-local.

Replacement tests: tests/curation_intake. Exact actor/scope/actions, configured
policy, duplicate pins, retry identity/conflicts and separate read grants must
survive a rebuild. HTTP/SQL concurrency tests are in this module; provider and installed-owner
qualification remain explicit P2/P5 gaps. No live-demo curation API claim.

HTTP: POST /v1/campaign-curations, POST /v1/campaign-curations/receipts/query and
GET /v1/campaign-curations/{curation_id}; no query parameters or GET bodies.
Queries carry exact command identity/hash, never resubmit work.401/403 deny,404
means unavailable,409 conflicts/inconsistent history,422 malformed and413 oversized.
The shared whole-body/depth/deadline middleware applies. Responses are no-store.
Set AMPHORA_PLANNING_CURATION_POLICIES to a JSON array of at most32 unique policy
IDs to install routes; empty allows history only. Configured new grants without
this explicit configuration fail startup. Startup performs no migrations or calls.
Apply0022 explicitly with a compatible migrator; do not run old migrators afterward.
