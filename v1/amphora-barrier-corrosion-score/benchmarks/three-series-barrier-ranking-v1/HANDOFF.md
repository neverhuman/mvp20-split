# three-series-barrier-ranking-v1 — first real-data execution of the locked primary KPI

**Date:** 2026-08-02 · host: xbabe2 (canonical) · authority: **AUDIT_ONLY**
**Module:** amphora-barrier-corrosion-score (PRE_PHASE_0, UNVALIDATED) · **Campaign item:** W1

## What this is

The FIRST-EVER execution of mission.md's locked primary KPI test (blinded
Kendall tau at `metrics.barrier_index` >= 0.50, superior to solids-only and
PVC-only hostile nulls) against real, rights-clean data: the 3 strict
in-class CC-BY literature series (asperti2024, zhu2022,
alam2022_pa450_pa3282 E-series) that campaign item C4 (2026-08-01)
hash-locked to bring `corrosion_series.json.strict_literature_count` from 2
to 3. The analysis had never been run before this fire.

It adapts (with full disclosure in the script docstring, per Nosek et al.
2018 PNAS deviation-disclosure norm) the frozen
`benchmarks/st19168-preregistered-v1/analyze_st19168_preregistered.py`
primitives and pre-committed constants (ALPHA=0.05, LOCKED_TAU_TARGET=0.50,
FEASIBILITY_FLOOR=6) unchanged, to a per-series, no-cross-study-pooling
design honoring each source's declared `use_limit`.

## Result: CLAIM_REFUTED

Two independent, decisive, mechanical findings — not an ordinary
underpowered-null result:

1. **`metrics.barrier_index` is unconditionally `None`** on every code path
   in the live `src/lib.rs` implementation. Confirmed by re-running the
   module's own live test suite this fire
   (`cargo test -p amphora-barrier-corrosion-score`: 5/5 passed, including
   `test_fit_keeps_endpoints_separate_and_summary_never_claims_circuit`'s
   `assert!(prediction.barrier_index.is_none())` on a real fitted-model
   prediction). The locked predictor does not exist, independent of sample
   size.
2. **All 3 series are below the pre-registered `FEASIBILITY_FLOOR=6`**
   (asperti2024 n=4, zhu2022 n=5, alam2022 E-series n=3). The n=3 series is
   combinatorially incapable of ever reaching one-sided alpha=0.05
   significance at any observed tau (3!=6 permutations, min exact p=1/6).

Informational-only (non-gated) headroom characterization: `tau_b`
(solids/PVC-null, truth) = 0.0 (asperti2024), 0.4 (zhu2022), -0.333
(alam2022 E-series) — the 0.0/0.4 values exactly reproduce the
independently-computed Spearman rho already reported in
`barrier-null-char-v1`, a useful non-circularity cross-check.

## Honest power statement

- Bonett-Wright n required for 80% power at tau=0.50, alpha=0.05 one-sided:
  ~25 (same formula/citation as the ST-19168 pre-registration).
- At actual per-series n: asperti2024 (n=4) ~13% achieved power, needs
  observed tau~0.99 for 80% power; zhu2022 (n=5) ~19% achieved power, needs
  tau~0.95; alam2022 (n=3) cannot reach significance at ANY tau (exact
  combinatorial fact, not an approximation).
- Meta-level: even a 3-series directional sign test in the best possible
  case (all 3 agreeing) cannot reach alpha=0.05 (min p=1/8=0.125).
  **tau>=0.5 is not resolvable from 3 series of this size, unconditionally.**

## corrosion_series.json update

`predictive_model_status` and `candidate_prediction_status` are **left as
FAILED** — the evidence supports no change — now backed by this signed,
two-replay byte-stable execution receipt instead of an assertion.
`docs/mission.md`'s "Current benchmark result" section is updated to point
here (collaborative edit, logged not fatal).

## Reproducibility

- `analyze_three_series_barrier_ranking.py` — self-contained (frozen
  primitives copied, not imported), stdlib+numpy+scipy, deterministic
  (no RNG needed at n<=10, full enumeration only).
- `result.{runA,runB,canonical}.json` — two runs, byte-identical, SHA-256
  `41c54275b323bb699e8f0cf95465d986b78986cafadea70eb69dbb5fc23e07bc`.
  TWO_REPLAY_GATE=PASS.
- `three-series-barrier-ranking-receipt.v1.dsse.json` — DSSE Ed25519 signed
  with the trust-anchored Phase-0 evaluator key
  `phase0-evaluator-3ef6b35cdbbfea74a96a5c9b98a515d57158a09ecaff10acfa1f15990be00178`,
  AUDIT_ONLY: `promotes_authority=false`, `modifies_manifest=false`, no
  promotion ceremony. Independently re-verified (separate process, PAE
  reconstruction from the envelope bytes): `INDEPENDENT_VERIFY_PASS`.

## Files

- `analyze_three_series_barrier_ranking.py` — deterministic benchmark
- `sign_three_series.py` — DSSE signer
- `result.{runA,runB,canonical}.json` — two runs + canonical
- `three-series-barrier-ranking-receipt.v1.dsse.json` — signed receipt
- `runA.log`, `runB.log` — stderr (RESULT_SHA256 lines)
