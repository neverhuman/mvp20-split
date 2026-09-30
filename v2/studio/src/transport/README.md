# Observation transport

Owner: [Studio](../../README.md). `ObservationClient` implements the `ObservationSource` port used by page models. It performs read-only snapshot, selected-node, value-page and invalidation requests; it contains no graph decisions or component state.

The configured prefix is a relative same-origin path, default `/api/runtime`. Request credentials use the browser session; no Runtime bearer key is stored here. A thin server adapter must perform scoped owner routing. Read identifiers/cursors are URL-encoded, redirects are rejected, pages request50 records (events100), response bodies are capped at2MiB and requests default to15 seconds. These are engineering bounds, not measured UI latency targets.

Each request relays caller cancellation to its own controller and clears timer/listener ownership on completion. The body is consumed with a byte limit and fatal UTF-8 decoding before JSON/schema validation. Responses are never accepted solely because TypeScript assigned a static type. Backend raw error text is excluded from `ReadFailure`: denied401/403, missing404, resnapshot409/410, timeout, abort, invalid response and network failure are explicit categories.

The transport owns no retries, caches, polling timers or authority decisions. Page models decide whether a visible invalidated region should refresh. The four endpoint shapes preserve Runtime's public contracts; possession of a cursor is never treated as authorization.

Owned tests: `tests/transport/` cover actual local HTTP encoding/no owner credential, all DTO roots, status mapping, cancellation/timeout, malformed JSON/UTF-8/type and declared/streamed size limits. The local HTTP server is a labeled synthetic contract peer. Real Runtime/gateway/browser acceptance remains later in this child. Replacement must preserve bounds, sanitized failures, cancellation and public shape validation.
