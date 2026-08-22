# amphora-candidate-contract

Shared JSON contract for MVP20 split scoring services.

Every service accepts a `CandidateEnvelope` and emits a `ScoreEnvelope`.
The helper API is intentionally stdlib-only so services can fail closed
without depending on a framework.

Runtime/schema parity is defined over strictly parsed JSON. The contract loader
rejects Python's non-standard `NaN`, `Infinity`, and `-Infinity` tokens before
schema validation; in-memory callers are also checked recursively for non-finite
numbers. Canonical hashes use sorted, compact, unescaped UTF-8 JSON, matching the
Rust boundary.
