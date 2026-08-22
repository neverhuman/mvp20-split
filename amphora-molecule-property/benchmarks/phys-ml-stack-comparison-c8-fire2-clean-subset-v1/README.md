# phys-ml-stack-comparison-c8-fire2-clean-subset-v1 (AUDIT_ONLY)

**Campaign item:** C8 — Receipt-backed phys/ML/stack table (replaces fabricated SCHEMATIC F8)
**Fire:** 2 of 4 (max_fires)
**Authority:** AUDIT_ONLY — promotes nothing, modifies no signed receipt/manifest (stays 66/11).

## What this is

C8 fire 1 built the consolidated density/Tg/dielectric/RI physics-vs-ML-vs-stack
comparison and, while building the dielectric arm, found RadonPy PI1070's
`static_dielectric_const` ground truth violates the thermodynamic inequality
`eps_static >= n_measured^2` (Frohlich 1949 Ch.2) in 962/1075 = 89.5% of rows.
Fire 1 only tested this defect's consequence weakly: an RF trained on the full
89.5%-corrupted population, evaluated on a physically-valid test slice (n=20).
Fire 1's own recommended followup #3 was to re-run the comparison **filtered to
the physically-valid subset for training too**, to check whether the shipped
KPI's ML-beats-physics numbers are themselves inflated by fitting the corrupted
majority. This fire executes exactly that.

## Attack

Rebuilt the RadonPy dielectric population from scratch (byte-for-byte parity
with fire 1: n=1075, 962 violations confirmed by assertion), filtered to the
n=113 physically-valid rows (10.5% of the population), then ran a **zero-
contamination** pipeline: RF retrained from scratch on clean-train only
(n=67), Ridge stack meta-learner fit on clean-calib only (n=22), all three
arms (physics/ML/stack) evaluated on clean-test only (n=24).

Pre-registered refute criteria (fixed before running):
- (a) ML test R² ≤ 0 (no better than the test-set mean), OR
- (b) paired bootstrap (n=2000, seed=0) 90% CI of (physics_MAE − ML_MAE)
  includes zero (ML's advantage not distinguishable from chance).

## Result: REFUTED — both criteria fired

| arm | clean-only test MAE | clean-only test R² |
|---|---|---|
| physics (Onsager) | 19.89 | −1.04 |
| ML (RF) | 13.06 | **−0.026** |
| stack (Ridge) | 14.52 | −0.048 |

Paired bootstrap (physics_MAE − ML_MAE): point +6.83, 90% CI **[−0.40, +13.92]**
— includes zero.

None of physics, ML, or stack beats a constant-mean baseline on the honest
(uncontaminated) 10.5% of the population. The previously-reported large
ML-over-physics gap (shipped KPI: physics R²=−1.67, ML R²=+0.64) is not a real
chemistry-to-dielectric skill signal — it is consistent with RF exploiting the
corrupted majority's low variance (962 rows collapsed toward the
under-converged electronic-only limit, easy to predict near-constant, which
inflates R² against a homogeneous target).

## Consequence

The dielectric row of the founder-facing F8 panel cannot honestly show ANY
competent {physics, ML, stack} predictor from current receipt-backed data.
Recommend it read "no competent model — label integrity failure, n_clean=113"
rather than citing the shipped KPI's contaminated-population R²=0.64. Density,
Tg, and RI arms from fire 1 are unaffected (different, unflagged ground-truth
columns).

## Reproducibility

Two-replay SHA-256 gate = PASS, confirmed both in-process (double-build) and
via an independent second process invocation (`c8_fire2_compute.py` re-run
cross-process byte-identical). DSSE Ed25519 signature (local AUDIT_ONLY key,
same key/format as fire 1) SIGNATURE_VERIFY=PASS, `.signature` is a JSON
object.

Run: `python3 c8_fire2_compute.py` (writes `/tmp/c8_fire2_raw_results.json`);
sign: `python3 c8_fire2_sign_receipt.py`.
