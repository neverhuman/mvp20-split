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

UI-01.08c adds v4/fit.v6 after the diagnostic original returned incomplete/max_output_tokens. V4 keeps the exact v3 instructions and strict generation schema, but explicitly selects reasoning effort none on the same pinned model. Its separate descriptor includes that effort. The intended repair reserves output capacity for the graph; live success is not inferred from offline checks. V1-v3 remain byte-exact with low reasoning. No output ceiling, validation, allowance or retry change.

UI-01.08d adds v5/fit.v7 with the same strict schema, instructions and reasoning none. Its distinct descriptor declares16384 maximum output tokens. Oldv1-v4 envelopes replay unchanged. Scoped cost authority is owned by curation_budget, not this module.

UI-01.08e controlled probes isolated NumberConstant.value minimum=-1e100/maximum=1e100 as a generation trigger: full schema without just those bounds passes; a tiny bounded-number schema reproduces zero-usage incomplete. V6/fit.v8 has a distinct generation-schema hash and omits only those two provider constraints. Public CampaignCurationDraft/NumberConstant validation retains the bounds, finite-number rules and all acceptance authority. Oldv1-v5 generation bytes remain unchanged. Same prompt/reasoning none; ordinary8192/$0.25 ceiling, no new campaign allowance. Local numeric-bound enforcement is replacement-critical.

V7/fit.v9 keeps the v6 generation schema, local validation and8192/$0.25 limits.
Its distinct prompt explains proposal-stage limitations and separates graph-language
primitives from scientific tool inventory. Neither non-admission nor unproven run
origin alone vetoes authoring; neither is removed or promoted to acceptance. Old
envelopes remain exact. Live effectiveness pending; no added paid allowance.

V8/fit.v10 isolates reasoning none->low, keeping v7 prompt bytes and v6-compatible schema unchanged. Old request identities/captures remain immutable; no effectiveness claim before live qualification.

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
