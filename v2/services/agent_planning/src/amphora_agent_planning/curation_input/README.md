# Campaign curation live input

UI-01.08/P2.2. Owns `planning.curation-openai-input-bound/v1` and curation Responses
framing. Architecture: ../../../../../docs/Architecture/Agents/Planning.md.

UI-01.08a adds explicit input-bound/v2, curation-v2 instructions and fit.v4. V1
descriptors, instructions, fit.v3 and envelope bytes remain unchanged. V2 projects
runtime schema base64 into readable JSON only after exact reference/digest, bounded
encoding and strict JSON checks. It preserves the original packet/hash, all other
lanes and omission metadata; decoded descriptions remain untrusted data. A packaged
field-placement guide strengthens generation without rewriting any model output or
changing published output/graph contracts. V2 must be selected by exact model
descriptor and corresponding immutable prompt artifact; mismatched v1 prompts fail.

CurationInputBound accepts only the pinned OpenAI mini model/revision and exact
curation descriptor. CurationEnvelope requires campaign_proposal purpose, the new
curation output schema, canonical prepared packet and exact packaged curation
instructions. Human direction, context and inventory stay under untrusted_context.
Instructions, complete output schema, packet/context and Responses framing all
count toward the conservative UTF-8 byte bound plus1024. This is not a measured
token count. Original output reserve and context/total limits remain binding.

PacketBudget emits distinct fit.v3 with curation framing and exact envelope hash;
fixture fit.v1 and supervision fit.v2 retain original bytes. Replays reconstruct
the same send body. JSON mode is explicit; local output validation remains the
authority. No tools, URLs, provider-selected schema, streaming, storage or automatic
retry enter this envelope. Fixed model/default tier/low reasoning match the existing
reviewed adapter. No API call or spending reservation is performed here.

Owned tests: tests/curation_input. Replacement requires old profile fingerprints,
complete-envelope fit and omission behavior, hostile text confined to data, exact
replay hashes, wrong purpose/model/schema/prompt rejection and separate legacy
supervision behavior. Worker/issuance/accounting/transport is P2.3, not this module.

V2 also projects verified text/plain and application/json artifact bodies into body_text inside untrusted_context. This exposes the reviewed future revision/declaration without promoting artifact text to instructions. Size/digest/UTF-8 and JSON integrity are checked; unsupported media rejects before issuance. Artifact bytes and immutable source packet stay unchanged. The v2 SchemaRef uses the established distinct schema_id suffix .v2 with wire version1; no Core schema widening.

UI-01.08b adds v3 instructions/input descriptor and fit.v5. GenerationSchema owns a closed, deterministic provider schema projection: disjoint tagged oneOf becomes anyOf; metadata/defaults are removed; all object properties become required, preserving nullable types. Unsupported keywords, open objects, external references and ambiguous unions reject. The complete strict provider schema is included in envelope sizing/hash before issuance. Public output validation remains unchanged; no response repair or retroactive stronger validation. v1/v2 envelopes remain byte-exact.
