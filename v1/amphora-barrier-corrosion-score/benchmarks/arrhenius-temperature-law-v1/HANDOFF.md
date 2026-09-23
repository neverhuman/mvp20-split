# arrhenius-temperature-law-v1 — first a-priori PHYSICAL baseline for the corrosion-RATE target

**Date:** 2026-07-30 · host: xbabe2 (canonical) · authority: **AUDIT_ONLY**
**Module:** amphora-barrier-corrosion-score (PRE_PHASE_0, UNVALIDATED)

## What this is
Every prior corrosion-**rate** receipt in this module (`corr-rate-qspr-v1`,
`corr-rate-significance`, `corr-rate-conformal-v1`) is **purely empirical ML** —
a HistGBM QSPR plus resampling / conformal wrappers. The module's only physical
baselines (Nielsen 1967 / Cussler 1988, in `nielsen-tortuosity-baseline-v1`) are
on the **barrier** side. This benchmark supplies the missing **named, published,
a-priori physical law for the rate target** and tests it adversarially against
the shipped ML model — then measures the dataset's own model-free ceiling.

Dataset: NIST CORR-DATA (`feedback/v1/derived/nist_corr_reference.json`,
sha256 `d0d999e4…`, rights_class `DERIVATIVE_ALLOWED`, NIST public data). No
external download. Series key = (material, environment, concentration_text);
replicates at identical (series, T) collapsed to their median; T window
[0, 150] °C (aqueous liquid-phase proxy, excludes the 500–600 °C rows);
retained **78 series / 396 points** requiring ≥4 distinct temperatures and
≥20 K span.

## Named baselines (published, zero data-fit structure)
- **Arrhenius 1889** — Z. Phys. Chem. **4**:226–248. `rate = A·exp(−Ea/RT)`;
  2 params per series, fitted **only** on the retained lower-T points.
- **van 't Hoff 1884** — *Études de dynamique chimique*, Frederik Muller,
  Amsterdam. Q10 rule ("rate doubles per 10 K"); corrosion-engineering form in
  Fontana & Greene, *Corrosion Engineering* 3rd ed., McGraw-Hill 1986,
  ISBN 0-07-021463-8. **Zero parameters.**
- **R = 8.314462618 J/(mol·K)** exact, SI-2019 / NIST SP 330-2019.
- Incumbent comparator: the shipped HistGBM, features imported **verbatim** from
  `corr-rate-conformal-v1/corr_rate_conformal.py` (source sha recorded).

## Results (honest)
- **A1 Arrhenius adequacy → `ARRHENIUS_REFUTED_AS_ADEQUATE_LAW`.** Median
  per-series R² **0.452**; only **12.0 %** of series reach R² ≥ 0.90; the *sign*
  is right (**76 %** have Ea > 0), the scatter is not.
- **A2 Ea plausibility → CORROBORATED IN SCALE, NOT IN VALUE.** **68.4 %** of
  positive-Ea series land in the van 't Hoff `[0.5×, 2×]` band around
  **Ea(Q10=2) = 52.95 kJ/mol**; median Ea **28.07 kJ/mol**, median implied
  **Q10 = 1.76 over 25–35 °C** — the textbook "doubles per 10 °C" rule
  **overstates** the median observed temperature sensitivity.
- **A3 LOHTO head-to-head (leave-out-highest-temperature, 78 series, identical
  information for every predictor) → NO PREDICTOR SIGNIFICANTLY BETTER.**
  MAE(log10): GBM+conc **0.614** < Arrhenius **0.656** < carry-forward null
  **0.662** < GBM shipped features **0.678** < van 't Hoff Q10=2 **0.732**.
  **Every paired sign test p ≥ 0.30** (Arrhenius vs GBM p = 0.734; Arrhenius vs
  null p = 0.494). A 2-parameter physical law **ties** a 300-tree GBM; the
  zero-parameter Q10=2 rule is the **worst** predictor, consistent with A2.
- **A4 marine/chloride stratum:** n = 9 series, **UNDERPOWERED** (reported, not
  claimed). GBM+conc best at MAE 0.732.
- **A5 hostile null:** permuting rates across temperatures within each series
  drops median R² **0.452 → 0.289** — a real but **modest** collapse, i.e. much
  of the apparent Arrhenius linearity is 4–6-point small-sample fitting
  artefact, not physics.
- **A6 model-free ceiling (new).** Replicate dispersion on **identical**
  (material, environment, concentration, temperature) cells across independent
  literature entries: **93 cells / 451 pairs**, mean pairwise |Δlog10| **0.705**
  (median 0.477). The best predictor's LOHTO MAE (**0.614**) is **inside** that
  floor. **The temperature-extrapolation ceiling on NIST CORR-DATA is set by
  source-to-source data heterogeneity, not by model class.**
- **All 10 fail-closed checks PASS** (held-out never in any fitting set; GBM
  train rows = 396 − 78 = 318 for both feature sets; retention rule; mil→mm KAT;
  Ea(Q10=2) round-trip KAT; SI-2019 R; T-window; null collapse; key uniqueness;
  noise floor measured).

## Consequence for the module
The wide calibrated intervals in `corr-rate-conformal-v1` are **honest, not a
modelling failure** — a factor ~4–5 spread is this data source's irreducible
floor. Adding a physical temperature law does **not** tighten them. Real
improvement needs protocol-controlled primary corrosion-rate series, not a
better estimator. This is a durable negative result that bounds the
environmental-severity input.

## Scope ceiling (held)
Target is **bare metal/alloy SUBSTRATE** corrosion rate in a chemical
environment, **NOT** organic epoxy-amine **COATING-barrier** performance. Grants
no coating-barrier, batch-release, optimizer or product-performance authority.
Does not promote; does not flip `scientific_readiness`; manifest 66 receipts /
11 modules untouched.

## Reproducibility
- OMP_NUM_THREADS=1, fixed seeds, no timestamp, floats round(.,6). Two runs →
  canonical SHA-256 `0d3d3a54df43a6c6461199183c1ead9913349d298f309874fc175e9dd4398690`
  (byte-identical). **TWO_REPLAY_GATE=PASS.**
  harness_sha256 `5af4377742acbc3c5a9d319f3b5eacea0a39c270f614fcd61104074cb210c4bd`.
- DSSE Ed25519 signed with trust-anchored Phase-0 evaluator key
  `phase0-evaluator-3ef6b35c…`, **AUDIT_ONLY** (promotes_authority=false,
  modifies_manifest=false). eval + reviewer key ids both derive the pinned trust
  store. **INDEPENDENT_VERIFY=PASS.** envelope_sha256 `91155459…`.

## Files
- `arrhenius_temperature_law.py` — deterministic benchmark
- `result.{runA,runB,canonical}.json` — two runs + canonical
- `sign_arrhenius.py` — DSSE signer (AUDIT_ONLY)
- `arrhenius-temperature-law-receipt.v1.dsse.json` — signed receipt

## Next honest move
The standing DATA wall is unchanged and now **quantified**: any corrosion-rate
severity work on NIST CORR-DATA is capped at ~0.6–0.7 log10. A forward move
requires either (a) a single-protocol primary corrosion-rate series (one lab,
one method, controlled concentration/aeration) with ≥3 temperatures, or (b) the
barrier-side ask already logged: ≥3 pooled protocol-controlled formulation→Rc
series with dispersion/PVC metadata.
