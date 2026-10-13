# Campaign packet profiles

UI-01.08/P2.2 adds the separately selected curation-v1 packaged prompt and
curation input-bound descriptor. Exact curation output schema selects the prompt;
old campaign/supervision instruction bytes remain unchanged. PacketFit.v3 counts
the complete curation Responses envelope; existing fit.v1/v2 remain unchanged.

Owner: Agent Planning. Architecture: [Planning](../../../../../docs/Architecture/Agents/Planning.md). Closed instruction/tokenizer profiles and original-request packet budget checks. No model call, network, source processing permission, durable accounting reservation or Runtime/domain acceptance.

FixturePacketTokenizer supports only deterministic/adversarial-fixture/1 with the exact SHA-pinned planning.fixture-byte-tokenizer/1 descriptor. It counts strict UTF-8 packet bytes as synthetic_byte_token units, including the complete supplied envelope. Empty, non-byte, invalid UTF-8 or over8MiB input rejects. This is a deterministic fixture, not an estimate or guarantee for any live tokenizer, chat framing or provider. Unknown models or tokenizer pins fail rather than falling back. The separate [checkpoint input profile](../checkpoint_input/README.md) supports one pinned OpenAI supervision envelope and records conservative input-bound fit v2. Existing fixture fit v1 remains byte-compatible; old evaluation profiles are not accepted as checkpoint profiles.

PacketBudget rebinds the original campaign/supervision RequestSnapshot. Existing ContextPolicy proves max_input_tokens plus the unchanged max_output_tokens reserve fits both the original context window and total ceiling. inspect measures the complete packet and checks the original input ceiling. PacketFit exposes exact packet SHA/byte count, synthetic units, tokenizer pin, original limits and explicit fit/failure. It neither refunds budget nor accounts for prior attempts; the existing durable budget ledger remains authoritative for issuance and accumulated spend. Direct object construction is internal; consumers rebind before use.

CampaignInstructions accepts only the packaged campaign-v1 profile and the original prompt Artifact's exact scope/identity/media/size/digest. Packaged text has canonical LF bytes; supplied Artifact bytes are never normalized to pass. Matching a caller-selected digest alone does not approve arbitrary instructions. Source, graph, tool, Research and retrieval text remain data for later rendering. The profile directs iterative exploration with uncertainty preserved and future-only corrections; prompt text alone is not evidence of live-model injection resistance or scientific quality.

Tests under tests/campaign_packet_profiles cover Unicode byte accounting, exact input boundary/output reserve, unsupported model/tokenizer combinations, malformed/oversize input, original window/total checks and arbitrary instruction rejection. Independent wheel verification must include the packaged prompt. Replacement must retain existing reviewed profile bytes and descriptor identities or add a new profile while preserving old replay. Slice planning, full packet construction, consumed observations, omissions, live adapter framing and durable preparation are subsequent boundaries.

UI-01.08a: curation descriptor v2 selects packaged curation-v2 instructions and fit.v4 with readable schema framing. V1 defaults and replay stay unchanged. Prompt selection follows the exact reviewed request descriptor, never model or human text. Full rendered envelope plus1024 and the original output reserve still govern fitting.

UI-01.08i v9/fit.v11 isolates low->medium reasoning under the existing additional
$10 authority. Same v8 prompt bytes, compatible generation schema, model and8192/
$0.25 limits. Versions1..8 replay unchanged; no new allowance or output repair.

Planning0.139 adds private curation input v10/fit.v12 for the exact reviewed demo
scope: medium reasoning and identical v9 prompt/generation schema, input ceiling
196608 and output ceiling16384. Maximum computed cost221184000 nanodollars stays
within the unchanged250000000 reservation. All prior profiles/holds remain valid;
other scopes cannot select this profile. This addresses a retained scientific
request with45223 reported input/8192 output tokens and incomplete output; it is
not a scientific-validity claim or a refund/retry of that original request.
