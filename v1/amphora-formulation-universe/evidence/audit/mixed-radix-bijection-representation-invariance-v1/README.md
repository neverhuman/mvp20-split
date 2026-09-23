# mixed-radix-bijection-representation-invariance-v1 (AUDIT_ONLY)

Escalation over `evidence/audit/mixed-radix-bijection-v1` and T-06
(2026-08-06, `evidence/phase0/repairs/T-06`, CLAIM_REFUTED).

**Claim under test:** the mixed-radix-bijection-v1 oracle's
`bijection_holds_all_universes: true` / `acceptance_all_perfect: true`
constitutes independent corroboration that Cartesian enumeration reports
every solved and infeasible combination without silent loss or
duplication — cited in `docs/mission.md`'s T-06 Known Contradictions entry
as "the module's own documented mixed-radix unranking."

**Method:** reproduce T-06's own representation-order counterexample
(hardener axis value order swapped between two accounting-equivalent
universes A/B, declared infeasible index shared) through the
mixed-radix-bijection-v1 oracle's own primitives, reimplemented
byte-for-byte from its published source.

**Result:**
- `accounting_output_equal_a_vs_b`: **true** — A and B are accounting-equivalent
  (identical radices, place_weights, cartesian_total, solved/infeasible counts).
- `both_universes_individually_pass_oracle_acceptance`: **true** — the
  shipped oracle's own metrics (bijection roundtrip/injective/surjective/
  value_tuple_bijection) report perfect on A alone and on B alone.
- Declared infeasible index 1 decodes to `("IPDA","DGEBF")` under A and
  `("TETA","DGEBF")` under B — `representation_invariant_decode_a_vs_b`:
  **false**. Bit-for-bit reproduction of T-06's finding via the oracle's own
  algorithm.
- Negative control (universe C, hardener order unchanged from A):
  `representation_invariant_decode_a_vs_c_negative_control`: **true** —
  isolates the cause to the axis-value reordering, not the harness.

**Verdict: CLAIM_REFUTED.** The mixed-radix-bijection-v1 oracle's
acceptance vocabulary (10 per-universe rate fields + 9 failclosed_probes)
is structurally a property of one axes dict in isolation; it never compares
two representations of what the runtime treats as "the same" universe. It
would report `acceptance_all_perfect: true` on either universe A or B today
if substituted into the fixture, exactly as it did in this test. Its
loss-freedom/duplication-freedom claim holds only within one fixed
representation and does not establish (and cannot detect the absence of)
representation-invariant identity — the exact property T-06 already
disproved live in the Rust runtime.

**Authority:** AUDIT_ONLY. Does not promote, flip scientific_readiness,
edit the portfolio manifest, any locked dataset, the signed Phase-0 KPI,
mission.md, or the live Rust engine. Does not edit the existing
mixed-radix-bijection-v1 receipt or script — this is a new artifact only.
Signed under Phase-0 evaluator seed, DSSE PAE + Ed25519, independently
re-verified.

Files: `run_representation_invariance.py` (harness, reimplements the
oracle's own radices_and_values/place_weights/unrank/rank),
`diagnostic.canonical.json` / `diagnostic.runB.json` (two byte-identical
replays), `sign_representation_invariance.py` (signer),
`mixed-radix-bijection-representation-invariance-receipt.v1.dsse.json`
(signed receipt).
