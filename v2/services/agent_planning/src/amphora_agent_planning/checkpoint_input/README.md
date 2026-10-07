# Checkpoint input profile

Owner: Agent Planning. Architecture: [Planning](../../../../../docs/Architecture/Agents/Planning.md).
BP-09.03/B1.1 owns this pure boundary. It performs no I/O, model call, credential read,
budget reservation, source authorization or execution. No SQL or foreign private imports.

`CheckpointEnvelope.bind(request, packet)` rebinds the original request, exact canonical
campaign packet v1, original prompt identity and reviewed instruction bytes. Only supervision
requests with the pinned gpt-5.4-mini-2026-03-17 model, checkpoint input-bound profile and
CheckpointDraft schema are accepted. Request identity and original omissions cannot change.
Owner context remains user-message data; it never selects system instructions. Artifact body
permission, content validity and fresh processing authorization remain the upstream reader's
responsibility. This framing is not evidence of prompt-injection resistance or scientific validity.

One deterministic Responses envelope carries reviewed instructions, untrusted packet context,
packet digest and the local output schema. JSON mode is intentional because proposal parameter
maps do not form a provider strict-schema subset. Existing local output validation remains
authoritative. Store/stream are false, reasoning low, service tier default; no tools, background,
fallback or retry configuration. The original output-token reserve is unchanged.

`CheckpointInputBound` produces a conservative input reservation from the complete serialized
UTF-8 envelope plus 1024 framing units. This is not an actual provider token count. Packet fit
v2 records separate packet/envelope hashes and sizes, unit, original limits and authorization
none. Pre-issuance fitting and future transport must use the same envelope builder. This module
does not independently permit sending: transport/issuance must enforce per-request and group
cost ceilings and original deadlines. Oversized required context fails; optional fitting uses the
existing required-first algorithm. Raw packets are bounded at 8 MiB before parsing.

The fixture tokenizer and fit v1 bytes remain unchanged. Old evaluation adapter profiles are
separate and cannot be substituted. Preparation replay recomputes v2 fit from the original
packet/request; no public DTO or database migration is needed. A changed envelope or algorithm
requires a new profile identity and preserved old replay. Tests live in `tests/checkpoint_input/`
and neighboring packet/preparation suites; they cover hostile/malformed input, exact framing,
required overflow, optional omission and retained replay. Actual model behavior, durable issuance,
egress, cost enforcement and independent installed-worker integration belong to B1.2 and later.

Verified `2026-10-07 00:07:20`: 93 profile/packet/preparation tests pass; scoped coverage179 statements
and4 branches100%. This measures the pure profiles only; no SQL, model or deployment coverage.
