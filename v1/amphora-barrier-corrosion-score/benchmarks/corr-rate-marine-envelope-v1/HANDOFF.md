# corr-rate-marine-envelope-v1 — FALSIFICATION ATTACK (CLAIM_REFUTED)

**Date:** 2026-08-15 · host: xbabe2 (canonical) · authority: **AUDIT_ONLY**
**Module:** amphora-barrier-corrosion-score (PRE_PHASE_0, UNVALIDATED)

## What this is
A ROTATION-mode falsification attack on this module's strongest currently-
standing rights-clean claim: `evidence/phase0/kpis/corr-rate-family-safe-
qspr-kpi.v1.dsse.json` (GroupKFold(group=metallurgical_family, 5-fold)
HistGBM R2=0.132087), which had already survived two prior attacks
(`corr-rate-family-safe-v1`, `corr-rate-family-lofo-v1`) — both of which
varied only the cross-validation **grouping axis** (raw material string,
then metallurgical family, then true leave-one-family-out). Neither ever
varied the **environment** axis.

## The attack
`docs/mission.md` states this module's applicability domain is
"solvent-borne two-component epoxy-polyamide **marine**-coating R&D" — the
entire reason the module exists. Yet no prior receipt ever tested whether
the corrosion-rate QSPR generalizes to the module's own declared domain:
true seawater/marine-immersion exposure. This re-runs the identical
feature engineering, HistGBM hyperparameters, and seed=0 verbatim from
`corr-rate-family-safe-v1/corr_rate_family_safe.py` and
`corr-rate-family-lofo-v1/corr_rate_family_lofo.py`, with ONE new
variable: a single train/test split on true marine identity (environment
string contains "seawater" or "sea water") — train on all 7,096 non-marine
classified rows, test on all 186 true-seawater classified rows (8 of 17
metallurgical families, all 8 also present in the non-marine training
set).

## Pre-registered refutation criterion
REFUTED if marine-envelope GBM R2 <= 0.0 OR error-reduction-vs-best-
baseline-pct <= 0.0 (deployed `env_features()` as-is, matching production
behavior). SURVIVED otherwise, even if reduced relative to the family-
safe/LOFO within-domain numbers.

## Result: CLAIM_REFUTED
- marine-envelope R2 (deployed features) = **-0.450740** — the model is
  *worse than predicting the marine test-set mean*.
- 6 of 8 marine families individually score R2 <= 0, two catastrophically:
  carbon_steel_cast_iron R2=-16.03 (n=38), lead R2=-5.15 (n=18).
- Even the naive family-mean baseline (fit on non-marine training data)
  has negative R2 (-0.637) on the marine test set — confirms this is a
  genuine distributional shift, not a modeling artifact the GBM alone
  introduced.
- Ablation with a patched feature set (see below) still gives R2=-0.358497
  — still deeply negative; the co-discovered feature bug is not what's
  driving this refutation.
- `any_refutation_criterion_met = true` (criterion (a) alone: R2 <= 0).

## Co-discovered data-integrity finding (secondary, not the verdict driver)
The deployed `env_features()` marine flag is
`has("seawater", "sea water", "marine", "atmospheric")`, which conflates
atmospheric exposure with seawater immersion — two physically distinct
corrosion regimes. Of 499 classified rows with `marine_feature==1` in the
deployed model, 313 (62.7%) are actually atmospheric-exposure rows, not
seawater. Quantified via a patched ablation (`marine = has("seawater",
"sea water")` only); reported alongside, does not itself determine the
verdict (judged on deployed production behavior).

## Honest interpretation
This refutes the SAFE READING of the promoted family-safe KPI (and its
LOFO-survived nuance) as supporting this module's own declared marine
applicability domain. The QSPR model, as currently trained on NIST
CORR-DATA, has never demonstrated — and here demonstrably fails — to
generalize to genuine seawater/marine-immersion corrosion, which is the
entire reason `amphora-barrier-corrosion-score` exists. This does NOT
retract the promoted KPI's own pre-registered gate (that gate was never
about marine generalization specifically) — it adds a load-bearing nuance
that any citation of the KPI for marine-relevant decisions must carry.
Scope ceiling is otherwise unchanged: bare-metal/alloy substrate
corrosion (NIST CORR-DATA), not organic-coating barrier performance; no
product-performance authority either way.

## Reproducibility
- stdlib+numpy+sklearn, `OMP_NUM_THREADS=1`, fixed seed=0, no shuffling in
  the single train/test split, floats rounded to 6 decimals. Two runs ->
  canonical SHA-256 `20a4d8cf0382595e4bdcf9b6a0a44ad2451682bf0ae6a24137a4223c535ffb87`
  (byte-identical). TWO_REPLAY_GATE=PASS.
- harness_sha256 `80b88a17ede988f3fce3bcc8081c42ed2e1574bbcd2df58dc4eca9da00196c78`.
- DSSE Ed25519 signed with trust-anchored Phase-0 evaluator key
  `phase0-evaluator-3ef6b35c...`, **AUDIT_ONLY** (promotes_authority=false,
  modifies_manifest=false; scientific_readiness stays UNVALIDATED).
  INDEPENDENT_VERIFY=PASS. envelope_sha256 `2d336c5d...`.

## Files
- corr_rate_marine_envelope.py — deterministic benchmark
- result.{runA,runB}.json — two runs (byte-identical)
- sign_marine_envelope.py — DSSE signer (AUDIT_ONLY)
- corr-rate-marine-envelope-receipt.v1.dsse.json — signed receipt
