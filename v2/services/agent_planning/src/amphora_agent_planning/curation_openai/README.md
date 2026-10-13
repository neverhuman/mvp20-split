# Curation OpenAI adapter

UI-01.08/P2.3a. Architecture: ../../../../../docs/Architecture/Agents/Planning.md.

CurationOpenAI accepts a server-configured exact scope, synthetic-only egress
selection, environment-supplied key and1..60second timeout. It rebinds the original
curation envelope/cost profile, checks the configured scope and narrows timeout to
the original absolute deadline before one direct OpenAI Responses call. Full body
limit262144 is additive; original transport16384/32768/65536 modes stay unchanged.
There is no redirect, proxy, retry, tool invocation or alternate model/endpoint.

The existing bounded decoder preserves refusal/incomplete/unknown outcomes and
integer usage estimates. Credentials never enter repr, records or errors. The
configuration DTO carries only key environment name/scope/synthetic egress/timeout;
missing reviewed policies or widened settings reject. It grants no source rights.

The adapter does not own issuance or count calls in memory. A managed worker must
freeze context, check current Data processing rights, reserve the approved group
allowance and obtain the original DispatchJournal ticket before invoking it.
Restart/unknown-response recovery must reuse history, never call this adapter again
for an already issued ticket. No worker is activated by importing/configuring it.

Tests: tests/curation_openai with scripted transport; exact sent bytes, timeout
narrowing, fixed scope, expired/invalid input, unknown failure and no retry.
Actual live-model qualification remains P5; this module has made no paid calls.

UI-01.08b diagnostic repair: after a decoded response, retain only an immutable response digest/size, closed status/error/incomplete classifications and refusal boolean in process memory. Curation exposes that diagnostic and existing sanitized transport failure for the qualification exporter. No remote prose, API key, output repair, extra request or public schema change. Existing persisted observations and accounting stay authoritative; diagnostics are not retroactively recoverable after a process exits.

Cost reconciliation2026-10-12: curation additionally exposes HTTP status, fixed endpoint/method, exact request-body digest, receive UTC and bounded x-request-id for qualification export on success or error. No Authorization header or arbitrary response headers/prose are retained. Missing/invalid request IDs remain null; this evidence correlates transport requests, not billing invoices. Existing request body bytes and retry behavior remain unchanged.

Planning0.140 adds explicit scientific-v1 response window up to180s only for the
reviewed demo scope and v10 model profile. Defaults remain60s; transport requires
its own explicit profile and executor requires an explicit180s ceiling. Dispatch
records the chosen deadline, provider narrows to remaining time, existing job
heartbeat renews its60s fence independently. No retry, budget increase, reinterpretation
of retained attempts or promise of remote cancellation. Provider-disabled checks
validate model/window compatibility without loading keys. The earlier managed v10
call remains indeterminate with unknown usage and its full0.25USD hold.
