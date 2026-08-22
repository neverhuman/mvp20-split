# phase0-scientific-readiness-honesty-v1  (AUDIT_ONLY red-team)

**Question:** What does a `PHASE_0` badge in this portfolio actually *mean*? Is any
Phase-0 a *scientific validation*, or is every one a reproducibility/rights/independence
**governance-lock** with the underlying science still unvalidated?

**Method (deterministic, on-disk facts only, two-replay SHA-256 byte gate):**

- **A — Gate semantics.** For all 29 modules with a Phase-0 benchmark lock, read
  `scientific_success_required_for_phase0` (benchmark-lock) and
  `target_scientific_readiness` (promotion policy).
  → **0 / 29** gates require scientific success; the only readiness targets are
  `LOCKED_INTERNAL` and `NOT_APPLICABLE`.
- **B — Signed readiness.** For every signed `evaluation.v1.dsse.json`, verify the
  trust-anchored Ed25519 signature and read the *signed* `scientific_readiness`.
  → **19** signed eval receipts, **0** assert `VALIDATED` (6 `LOCKED_INTERNAL`,
  13 `NOT_APPLICABLE`).
- **C — Solvency re-verification.** The one science module now carried at a bound
  Phase-0 (`amphora-solvency-score`) is cryptographically re-checked: valid
  trust-anchored evaluator **and** distinct-identity independent-reviewer signatures,
  benchmark binding intact (no post-sign drift), review bound to the exact on-disk
  evaluation receipt, honest `LOCKED_INTERNAL` label. → **10/10 checks pass.**
- **D — Cure-potlife independent reproduction.** The flagship physics KPI
  (`amphora-cure-potlife-gate` Arrhenius pot-life) is recomputed from scratch from the
  on-disk locked model params + held-out truth. → all six metrics reproduce **bit-exact**
  (MAPE 0.1473336…, T_ref = 73 °F full precision); the cited activation energies are
  **non-circular** (mean Ea_fit/cited ≈ 0.89, i.e. not reverse-fit from the scored data);
  BUT dataset `rights_gate_passed = false`, so this real physics **cannot honestly
  promote** on current data.

**Founder headline (the thing the deck must not get wrong):**
`PHASE_0` = an engineering/governance milestone (byte-stable benchmark + rights-qualified
data + two distinct trust-anchored signatures at `LOCKED_INTERNAL`). It is **not** a count
of validated scientific capabilities — **0** modules are scientifically `VALIDATED`. The
real predictive science that exists is gated by **data rights**, not by missing science.

Modifies nothing. Promotes nothing. Signed with the repo `LOCAL_DEVELOPMENT_AUDIT_ONLY`
key (`local-9028773f…`), explicitly not a trust-anchored Phase-0 key.
