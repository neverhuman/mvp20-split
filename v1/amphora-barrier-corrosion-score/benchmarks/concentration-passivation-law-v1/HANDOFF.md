# concentration-passivation-law-v1 — the CONCENTRATION axis, tested against passivation

**Date:** 2026-07-31 · host: xbabe2 (canonical) · authority: **AUDIT_ONLY**
**Module:** amphora-barrier-corrosion-score (PRE_PHASE_0, UNVALIDATED)

## What this is
The module had mined the temperature axis of NIST CORR-DATA
(arrhenius-temperature-law-v1) and the material/environment axes (the ML rate
receipts), but never the **concentration axis** — 85 retained series with ≥4
strictly-numeric concentrations at fixed (material, environment, T). The naive
severity assumption a barrier-corrosion score would otherwise inherit —
**monotone severity**: "more concentrated = more corrosive" — has a named,
published counter-theory: **passivation** (Schönbein 1836 Phil. Mag. 9:53;
Faraday 1836 Phil. Mag. 9:57 — iron passive in concentrated HNO₃; Fontana 1986
ISBN 0-07-021463-8 — stainless/H₂SO₄ isocorrosion interior maxima; Uhlig &
Revie 1985 ISBN 0-471-07818-2).

Dataset: `feedback/v1/derived/nist_corr_reference.json` (sha256 `d0d999e4…`,
pinned = arrhenius receipt value, DERIVATIVE_ALLOWED, NIST public data). Strict
full-string numeric wt% parse (ranges/qualifiers EXCLUDED, not guessed); T
window [0,150] °C as prior receipts; replicates collapsed to medians.

## Statistics (the interesting part)
Per-series Spearman + exact/seeded-MC permutation p; PAVA monotone fits vs
piecewise-monotone umbrella/valley fits (Barlow 1972; Mack–Wolfe 1981). A first
margin-only peak detector was **refuted by its own hostile null** (shuffled
noise produced MORE margin-peaks than real data, 0.42 vs 0.33) and replaced by
a per-series **shuffle-calibrated shape p-value** (1000 shuffles, stage-2
20000 for floor-hitters) — the detector is calibrated against exactly the
noise process that fooled the margin rule.

## Headline (honest)
- **H0 REFUTED AS UNIVERSAL LAW**: 2 series — 304/H₂SO₄ at 38 °C and 40 °C —
  survive Bonferroni over m=166 tests with 2.26–2.40 log₁₀ peak-to-concentrated
  collapse (e.g. 110 mm/yr at 50 wt% → 0.6 at 95 wt%).
- **Fontana stainless/H₂SO₄ CORROBORATED**: 16/17 retained 304-family/H₂SO₄
  series have interior rate maxima; 10/11 series reaching ≥90 wt% show ≥10×
  concentrated-regime collapse.
- **Global enrichment honestly MARGINAL**: 8 calibrated peaks vs 4.15 expected
  false (exact binomial p=0.056). Most systems ARE monotone increasing
  (18 significantly so) — the refutation is of the *universal* assumption.
- Schönbein/Faraday iron/HNO₃ stratum: **no data in retained cohort** (reported
  as absent, not scored elsewhere). Marine NaCl stratum: 1 series, power-flagged.
- **C5**: the shipped QSPR feature set is concentration-blind; median
  within-series range across concentration is 1.40 log₁₀, well above the
  0.79 log₁₀ replicate noise floor — a real, unmodeled, NON-monotone severity axis.

## Consequence for the module
A severity input cannot treat concentration as a monotone aggressiveness
scalar; any future concentration feature must be shape-free. This is the
concentration analogue of the Arrhenius receipt's "temperature law refuted"
result: both axes resist simple laws, but here the *named counter-theory*
(passivation) is what the data corroborate.

## Reproducibility / governance
- Two-replay byte-stable: canonical sha256 `c7319dee5dce8696…` (runA = runB).
- All 10 fail-closed checks PASS (dataset-sha pin, strict numeric parse,
  exact-perm coverage, PAVA validity, coherence collapse, Bonferroni floor).
- DSSE Ed25519 signed: `concentration-passivation-law-receipt.v1.dsse.json`,
  evaluator key derives pinned trust-store key_id. Envelope sha256
  `f9a57b7c93bb7de3…`, harness sha256 `2fdd7d26a259923a…`.
- AUDIT_ONLY: no promotion, no manifest edit (66 receipts / 11 modules
  untouched), scientific_readiness stays UNVALIDATED. Substrate-severity
  scope only — NOT coating-barrier performance.
