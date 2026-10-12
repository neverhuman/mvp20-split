# Campaign curation output

UI-01.08/P2.2. Owns exact `planning.campaign-curation-draft/v1` interpretation.
Architecture: ../../../../../docs/Architecture/Agents/Planning.md.

CurationOutput accepts at most65536 original UTF-8 bytes, strict JSON and closed
schema, exact campaign purpose/output profile/decision digest, allowed actions,
same-scope typed references, unique gap keys and unique port names. Canonical
normalization is bounded separately; the provider journal retains original bytes.
Reconstruction rejects forged domain objects. No I/O, provider calls, graph repair,
tool installation, fulfillment or execution/scientific authority belongs here.

The original output keeps three distinct outcomes. Existing generic provider
observation `action` is propose_campaign for a future graph and abstain when no
executable graph is proposed. A request_capabilities outcome therefore abstains
from proposing execution while retaining all structured requests in the typed
payload. It is not an empty answer or an ordinary abstention in the curation UI;
the job/domain consumer must inspect the original outcome. No legacy action enum
or stored profile is changed to hide this distinction.

review_document() is explicitly an internal compiler-review projection using
the exact proposed FutureCampaignDraft object, original rationale, decision and
unresolved points. It never replaces source bytes/schema/hash or fills a missing
graph. Structured gaps remain in document(); capability persistence consumes that
original document. The compiler still checks the original provider observation,
tool locks, scientific boundaries and Runtime validation independently.

Owned tests: tests/curation_output. Replacement must preserve raw capture and
canonical fingerprints, exact graph equality, gaps without a graph, profile/action/
scope negatives and the distinction between proposal interpretation and acceptance.
