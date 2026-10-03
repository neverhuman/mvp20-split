# Research receipt corrections

BP-06.03/B2.01 pure policy verified; no persisted correction or HTTP selection capability yet.

The private CorrectionPolicy issues immutable chain-bound revisions from this owner's published DomainReceipt. The source adapter must authenticate the actor and load the exact published source from this owner's state; a caller-supplied receipt is not authoritative. Chain scope/issuer, purpose, subject and accepted output scope must match. Superseded notices cannot be sources. Exact deterministic inputs replay identical bytes; each correction preserves the source verdict/output and records actor, reason and predecessor hash. Root revisions are chain-bound too. A new notice names the old effective revision and replacement, without mutating the original receipt.

CorrectionRevision owns stable record hashing. DTOs only serialize state. No peer SQL, network calls, Runtime mutation or shared owner policy. Active campaign pins remain valid under the future-campaign-only policy. Insufficient evidence remains insufficient; an exploratory workflow may use declared alternatives rather than treating an abstention as acceptance.

Planned store responsibilities: exact change identity replay/conflict, trusted predecessor reconstruction, head compare-and-swap, atomic record/notice publication and scoped authorized reads. Those guarantees are not provided by the pure policy. Tests live under this service's tests/corrections directory. Owning plan: BP-06.03 Receipt correction implementation.
