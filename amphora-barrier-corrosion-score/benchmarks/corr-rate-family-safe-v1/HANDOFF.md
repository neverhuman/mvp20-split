# corr-rate-family-safe-v1 — FALSIFICATION ATTACK (CLAIM_SURVIVED, partial)

**Date:** 2026-08-03 · host: xbabe2 (canonical) · authority: **AUDIT_ONLY**
**Module:** amphora-barrier-corrosion-score (PRE_PHASE_0, UNVALIDATED)

## What this is
A falsification attack on the strongest currently-standing corrosion-rate
QSPR claim in the module: `corr-rate-qspr-v1`'s leave-material-out headline
(GroupKFold group=material, HistGBM R2=0.316, RMSE=1.036 log units), which
that benchmark's own HANDOFF.md calls "the reproducible artifact of record"
(superseding the self-attested, non-reproducible `corr_data_corrosion_rate_
qspr_model{,_v3_env_features,_material_safe_v2}.v1.json` receipts).

## The attack
`GroupKFold(group=material)` groups strictly by the raw `material` string.
The NIST CORR-DATA material vocabulary (612 unique strings) contains many
near-duplicate aliases of the SAME or near-identical alloy chemistry, e.g.
`316`/`316L`/`316LN`/`316Ti`/`316F`, or `Hastelloy C-276`/`Alloy C-276`/
`Inco C-276`. These land in *different* GroupKFold folds despite sharing
near-identical composition, so a model that has only learned "300-series
austenitic stainless chemistry" or "Ni-Cr-Mo superalloy chemistry" from one
alias can score well on a held-out alias of the same family without having
generalized to a genuinely unseen alloy family.

This benchmark reruns `corr_rate_qspr.py`'s feature engineering (composition
vector, environment chemistry flags, temperature), HistGBM hyperparameters,
seed=0, and metrics **verbatim**, and adds ONE new grouping axis:
metallurgical **family** (ASM Handbook Vol.3; Sedriks 1996; Uhlig-Revie 2008)
via an ordered keyword/regex classifier (17 families: stainless_steel,
nickel_alloy, cobalt_alloy, carbon_steel_cast_iron, copper_alloy, titanium,
zirconium_hafnium, tantalum_niobium, precious_metal, lead, tin, zinc,
magnesium, aluminum, molybdenum, chromium, carbide_cermet). Coverage
94.58% (7,282/7,699 rows); 417 rows left unclassified and excluded from both
arms of the comparison for honesty. Both `material_safe` and `family_safe`
are recomputed on the IDENTICAL classified-row subset for a controlled
apples-to-apples comparison.

## Pre-registered refutation criterion
REFUTED if family-safe GBM R2 <= 0.0 (no better than global-mean baseline)
OR family-safe error-reduction-vs-best-baseline-pct <= 0.0, on the identical
subset/features/model/seed as material-safe. SURVIVED otherwise, even if
reduced relative to material-safe (family grouping is strictly coarser/
harder, so some reduction is expected and not itself a refutation).

## Result: CLAIM_SURVIVED (with a substantial, honestly-reported caveat)
- material_safe (classified subset, n=7,282): R2 = **0.3555**
- family_safe (same subset, n=7,282, 17-family GroupKFold): R2 = **0.1321**
- Relative reduction: **63%** (R2 drop -0.2234)
- family_safe still beats best naive baseline on RMSE by **7.05%**
- family_safe GBM R2 clearly positive (0.1321 > 0)
- `any_refutation_criterion_met = false`

## Honest interpretation
A meaningful share of the material-safe headline's apparent skill IS
attributable to within-family alias leakage across GroupKFold folds (R2
falls by nearly two-thirds when aliases of the same family are forced into
the same fold). This is a real, quantified weakness the module should
carry forward. But the pre-registered bar for refutation — collapse to
zero/negative or losing to the naive baseline — was not met: family-safe
R2 remains positive and the model still beats the best naive baseline,
so genuine (if reduced) chemistry-level generalization signal survives
even under the harder, alias-proof split.

## What this does NOT show
- Does not modify `corr-rate-qspr-v1`'s own reported material-safe numbers
  (recomputed here on a 94.58%-coverage classified subset, not the full
  cohort; the full-cohort material-safe reference R2=0.3555 vs the original
  0.316 differs because of the subset restriction, not a discrepancy in the
  original computation — both are reported in the signed receipt for
  transparency).
- Does not establish a coating-barrier ranking model; scope ceiling
  unchanged (bare-metal/alloy substrate corrosion only, NIST CORR-DATA).
- Does not modify the manifest (66/11 untouched) or flip
  `scientific_readiness`.

## Practical implication for future work on this module
Any future headline for this QSPR line should report BOTH material-safe
and family-safe (or equivalent alias-proof) group-safe R2, since the gap
between them (0.36 vs 0.13 here) is the honest measure of how much of the
apparent skill is alloy-family memorization vs genuine per-alloy
generalization.

## Reproducibility
- OMP_NUM_THREADS=1, fixed seed=0, no timestamp, floats round(.,6).
  Two independent runs -> canonical SHA-256
  `e6bb9bba921cf1c8b1b2b32b5eb4d42de9569ecc8ba35a2ff3d631a24ef26fee`
  (byte-identical). **TWO_REPLAY_GATE=PASS.**
  harness_sha256 `aeb7a8ac8fdd41fa395d5119218c0bc0187ac6174acce23f4bd84161b04a65c5`.
- DSSE Ed25519 signed with trust-anchored Phase-0 evaluator key
  `phase0-evaluator-3ef6b35c...`, **AUDIT_ONLY** (promotes_authority=false,
  modifies_manifest=false; scientific_readiness stays UNVALIDATED; manifest
  66/11 untouched). Independently re-verified against the pinned trust
  store outside the signing script: **INDEPENDENT_VERIFY=PASS**, key_id
  matches `config/phase0-trust-store.v1.json` PHASE0_EVALUATOR exactly.
  envelope_sha256 `eb015510f84eb9880158b731de8a6eb82fc5ec0aee659bcd07ab07634addc255`.

## Files
- `corr_rate_family_safe.py` — deterministic falsification benchmark
  (reuses corr_rate_qspr.py's feature engineering/model verbatim)
- `result.{runA,runB,canonical}.json` — two runs + canonical
- `sign_family_safe.py` — DSSE signer (AUDIT_ONLY)
- `corr-rate-family-safe-receipt.v1.dsse.json` — signed receipt
