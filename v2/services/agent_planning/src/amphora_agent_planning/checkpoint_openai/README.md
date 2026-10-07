# Configured checkpoint OpenAI adapter

Owner: Planning, BP-09.03/B1.2. Architecture: [Planning](../../../../../docs/Architecture/Agents/Planning.md).
Only `openai_checkpoint_v1` configuration enables this adapter. It requires an environment
key reference, explicit `approved_synthetic_engineering_only` egress selection and exact
reviewed budget templates. Default remains disabled. Configuration asserts operator
review of the selected synthetic scope; it is not a content classifier or a source grant.
Fresh Data processing authorization, retained packet and durable issuance remain owned
by the existing checkpoint worker. Configuration check creates no provider connection.

The adapter accepts only the separate checkpoint input profile and selected model snapshot.
It validates the conservative policy before issuance, rebuilds the exact retained Responses
envelope and checks the original input bound before sending. Transport duration is narrowed
to the lesser of configured1–60 seconds and whole seconds remaining before the original
issued/checkpoint deadline. Less than one second remaining sends nothing. It uses one direct
TLS request to the existing fixed OpenAI endpoint, with an explicit65536-byte body ceiling;
no proxy, redirect, retry, model fallback, background call or native provider tool execution.
Old evaluation transport defaults/revisions remain unchanged.

The existing bounded response decoder and integer price profile own usage handling.
Malformed, refused, incomplete or unavailable responses retain their original uncertainty;
unknown usage never becomes zero. Local CheckpointDraft validation is authoritative;
JSON mode/schema guidance cannot grant Runtime acceptance or scientific validity.
Keys live in process memory from environment references, not config files, repr or logs.

`checkpoint_budget` owns the restart-safe dedicated-scope ceiling. This adapter does not
issue tickets or independently authorize arbitrary calls. Production callers use
CheckpointWorker/PlanningRunner; injected transports are test seams, not config plugins.
History-first recovery returns completed work without rereading source data or calling
the provider. A failed physical attempt is not silently replaced.

Tests under `tests/checkpoint_openai/` cover exact transmitted bytes, narrowed deadlines,
malformed/unsupported input, explicit configuration, actualSQL configured-worker execution,
budget exhaustion and restart replay with scripted Data/intercepted transport. Those tests
are not live-model or actual-owner integration evidence. Independent wheel installation
and later actual-model/browser gates remain separately recorded in the child plan.

Verified `2026-10-07 00:32:46`: 220 affected regressions pass; final focused46 tests pass
with combined new-module coverage114/115 statements,11/12 branches (98.43%). The final
selection omits the legacy bypass, which the earlier broader suite exercised. Independent
Planning0.101 wheel passes114 copied profile/worker/SQL tests; two wheel sets match.
No paid calls or deployed scientific claim.


Planning0.102 adds explicitly selected compact checkpoint guidance while keeping the
same adapter,65,536-byte send ceiling and original profile. The request's pinned input
identity selects framing; the adapter never silently rewrites an old retained packet.
Both identities use the existing cost fence and exact transmitted-envelope checks.
