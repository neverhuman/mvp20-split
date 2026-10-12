# Campaign curation live input

UI-01.08/P2.2. Owns `planning.curation-openai-input-bound/v1` and curation Responses
framing. Architecture: ../../../../../docs/Architecture/Agents/Planning.md.

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
