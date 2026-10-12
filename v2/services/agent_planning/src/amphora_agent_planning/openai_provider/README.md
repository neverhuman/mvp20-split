# OpenAI provider boundary

UI-01.08/P2.3a adds an explicit262144-byte transport body mode for curation.
Existing defaults and body profiles are unchanged; the curation adapter requires
its own exact input/cost profile and fixed server scope before a send.

Owner: Planning,BP-07.05/B2.01. Explicit injection only; no default network activation. Model is pinned gpt-5.4-mini-2026-03-17,standard Responses endpoint,low reasoning,JSON output mode. Existing OutputProfiles independently validates permitted actions,schemas and references; JSON mode is not scientific or execution acceptance.

PreparedInput binds selected Artifact bytes to exact length/hash,request/model/prompt and a separately versioned conservative UTF8 input allowance. The existing fixture tokenizer remains unchanged. The allowance is a reservation bound,not reported tokenization. Input includes only the reviewed prompt plus exact selected synthetic bodies. No source or URL retrieval is owned here. Callers must supply an authorized content reader; no .env file reader exists in service code.

OpenAIHTTP makes one direct TLS request to api.openai.com with no redirects,proxies or retries.45-second default transport deadline,1MiB response envelope,existing64KiB capture limit. Credentials remain constructor-private and are not persisted/logged. Non200 is unavailable with unknown usage; connection/parse/malformed results remain unknown under existing observe. Refusal/incomplete output is not scientific abstention. Usage prices input/output tokens conservatively without cache discounts; reasoning tokens are already included in output and are not counted twice. USD nanodollar rates are750/4500 per token,reviewed2026-10-06. This is estimated cost,not invoice data.

This adapter owns no issuance,ledger or global retry budget. PlanningRunner must issue the original durable ticket; EvaluationBatch must reserve the complete suite before work. Initial max16384 input/4096 output; total initial run ceiling$1 belongs to frozen suite policy. No native tools,background response,conversation continuation or automatic model fallback. Live EvaluationRunner activation and corpus are B2.02; adapter tests alone cannot authorize it.

Owned tests: tests/openai_provider. Replacement preserves versioned model/input/rates,one-request behavior,redacted errors and original usage. Scientific quality,remote cancellation after process death and provider billing ceilings are not established by local transport tests.

Transport revision v2 adds explicit JSON-mode user framing; v1 packet bytes remain replayable. FrozenOpenAIEvaluation validates all packets before live issuance. The dev runner binds both immutable suites to the same initial $1 group ceiling, retaining both full reservations. HTTP failures expose only status, request hash and closed allowlisted error code/parameter; arbitrary provider messages never enter diagnostics.

Adapter revision v3 projects the published ExtractionDraft schema into provider strict JSON-schema format (closed objects, all fields required, defaults/titles omitted). Campaign output remains JSON mode with independent local action/reference validation. Provider schema does not grant semantic or scientific acceptance. Input reservation/HTTP body limit can explicitly use32768 for this version; predecessor defaults remain16384 and original packets remain unchanged. Structured output source: https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses . v5 evaluation uses this adapter, a fresh synthetic set and separate semantic posture instructions. Cumulative group cap$1.70 counts allfive full reservations($1.65888); no automatic refunds or retries.

BP-09.03 checkpoint integration reuses only the bounded decoder/pricing/HTTP transport from
this module. Its separate checkpoint envelope/profile does not alter evaluation v1/v2/v3.
HTTP accepts an explicit65536-byte body ceiling for that caller; the original16384 default
and32768 evaluation profile remain unchanged. See [checkpoint adapter](../checkpoint_openai/README.md).

UI-01.08b diagnostic repair: after a decoded response, retain only an immutable response digest/size, closed status/error/incomplete classifications and refusal boolean in process memory. Curation exposes that diagnostic and existing sanitized transport failure for the qualification exporter. No remote prose, API key, output repair, extra request or public schema change. Existing persisted observations and accounting stay authoritative; diagnostics are not retroactively recoverable after a process exits.

Cost reconciliation2026-10-12: curation additionally exposes HTTP status, fixed endpoint/method, exact request-body digest, receive UTC and bounded x-request-id for qualification export on success or error. No Authorization header or arbitrary response headers/prose are retained. Missing/invalid request IDs remain null; this evidence correlates transport requests, not billing invoices. Existing request body bytes and retry behavior remain unchanged.

UI-01.08d adds immutable ResponseShape diagnostics: closed message/reasoning/other item counts, output text block/UTF-8 byte counts and usage/input/output-field presence. No remote text or arbitrary names retained. Metadata never changes parsing, usage accounting or acceptance.
