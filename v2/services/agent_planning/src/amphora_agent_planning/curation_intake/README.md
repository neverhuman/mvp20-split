# Campaign curation intake

UI-01.08/P1 boundary policy implemented; durable intake/worker is P2, not yet active.
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

This module owns command admission/replay policy, not provider issuance, budget,
Runtime admission, process control or cross-service state. P1 has no state or I/O.
P2 must atomically journal original bytes before work, serialize same-identity
requests and preserve exact read-only receipt recovery. No SQL transaction may span
provider/peer I/O. Contract packages are public; other imports remain owner-local.

Replacement tests: tests/curation_intake. Exact actor/scope/actions, configured
policy, duplicate pins, retry identity/conflicts and separate read grants must
survive a rebuild. HTTP/SQL concurrency, provider and installed-owner qualification
remain explicit P2/P5 gaps; no deployed curation API claim.
