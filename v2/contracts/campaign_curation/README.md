# Campaign curation public contracts

UI-01.08/P1, version0.1.1. These additive DTOs describe future-campaign intent,
exact predecessor/draft/Knowledge/Research/Artifact pins, durable job receipts,
model output and explicit capability fulfillment. Planning owns all state and
policy; these types do not schedule providers, authorize reads/spend, install tools
or admit execution. Architecture: ../../docs/Architecture/Agents/Agent_Architecture.md.

`parse_curation` accepts only `planning.curate_campaign` with explicit numeric
command encoding. `parse_fulfillment` accepts only `planning.fulfill_capability`.
Both preserve canonical identity/digest for the owning journal. Shared command
decoding bounds raw bodies to256KiB, rejects duplicate keys/nonfinite numbers and
excessive nesting. Direction is at most4096 characters; provider/schema/prompt/cost
overrides are forbidden. Scoped references must match command scope. Authentication
must independently bind actor/scope; a valid transport identity is not a credential.

The separate `planning.campaign-curation-draft/v1` profile distinguishes a complete
future graph proposal, capability gaps without a graph, and abstention. Model-local
gap keys are not durable request IDs. Ports retain representation, schema when known,
units and description; unknown schemas are explicit. Structured gaps cannot contain
handlers, install commands or fulfillment claims. Planning validates duplicate keys,
original decision scope, scientific eligibility and compiler compatibility.

Capability fulfillment pins a real Registry lock and retained acceptance artifacts.
Planning must verify release/evidence and authorization before recording an immutable
fulfillment event. DTO status alone proves nothing. Existing campaign/checkpoint
outputs and launch requests/receipts are untouched. Read views expose retained
rationale and hashes, not provider credentials or private prompt packets.

Tests: tests/output and tests/test_commands.py. P1 replacement acceptance requires
portable schema roundtrips, predecessor byte pins, malformed/oversized request and
authority negatives. HTTP authorization, journal conflicts/recovery, provider bounds
and fulfillment verification belong to later owner modules; no deployed route is
claimed by this package. Public dependencies only; no persistence or service imports.

The process-constant curation output SchemaRef is frozen and memoized (one entry).
Repeated compiler reconstruction does not regenerate the unchanged schema/hash.
No input, permission, provider output or eligibility observation is cached here.
Published schema bytes remain unchanged; output/test_schema_identity.py verifies
repeated lookup, mutation rejection and the exact checked-in schema digest.
