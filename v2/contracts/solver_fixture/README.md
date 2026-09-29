# Synthetic solver fixture contracts

- Owner: BP-04.04/B1, source-derived orchestration verification; version 0.1.0, B1 verified.
- Scope: shared public payload DTOs for independently packaged synthetic seed, parent-selection, mutation, scoring and retention tools.

This package owns validation and serialization of source pins, bounded fixture configuration, candidate identity/seed association, fail-closed module envelopes, current/cumulative state, immutable generation checkpoints and ordered missing-result slots. It contains no selection, mutation, scoring, retention, scheduling or source-reading algorithms. Stage tools own those behaviors behind focused domain objects; the graph owns iteration and candidate dispatch. No service implementation is a dependency.

The synthetic profile supports at most eight candidates and eight offspring generations. Candidate structure is explicitly unchanged. Results cannot assert ranking authority or eligible scientific objectives; module envelopes always carry `NO_AUTHORITY`. Fault inputs deliberately drive mutation rejection, candidate failure and module errors for verification. They are fixture controls, not scientific parameters.

Source-pin syntax does not establish provenance: stage boundaries and graph admission fixtures must compare pins to the reviewed frozen baseline. Cross-record correspondence, cumulative membership and checkpoint consistency are domain invariants enforced by the owning tools, not implied by a structurally valid DTO. Public payload compatibility alone is not execution parity.

Tests belong to `tests/`. Exact tool schema publication and standalone packaging passed B1; real graph failure/recovery and installed peers remain B3/V1. Existing engine and tool contracts are unchanged.
