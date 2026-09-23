# phys-ml-stack-comparison-c8-v1 (AUDIT_ONLY)

**Campaign item:** C8 — Receipt-backed phys/ML/stack table (replaces fabricated SCHEMATIC F8)
**Fire:** 1 of 4 (max_fires)
**Authority:** AUDIT_ONLY — promotes nothing, modifies no signed receipt/manifest (stays 66/11).

## What this is

A consolidated, DSSE-signed per-property `{physics, ML, stack}` comparison for
`amphora-molecule-property`, covering density, Tg, dielectric constant, and
refractive index. Density's triplet already existed (cited verbatim). Tg's
stack arm was missing and is built here. Dielectric and refractive-index
physics arms did not exist in this module; they are ported here from the
frozen `amphora-redteam-audit` workshop (Onsager 1936 reaction-field / Eisenlohr
Lorentz-Lorenz molar refraction), which were validated on small-molecule
solvents, not polymers — this fire tests whether that port is honest.

## Method

All new computation reuses, verbatim, the featurization/classification/split
code from this module's own prior pushes — found still present under
`/tmp/*.py` on the execution host (`vk_external_validate.py`,
`tg_ml_baseline.py`, `stack_density.py`, `mixed_ri.py`, `mixed_dk.py`):
PSMILES wildcard-capping, the 24-group Van Krevelen/Bicerano classifier,
Morgan512+log10(MW) featurization, and the `RandomForestRegressor(n_est=300,
max_depth=10, seed=0)` + `Ridge(alpha=1.0)` Wolpert-1992 stacking pattern
from the existing density stack (Push #38). As a fidelity check, this fire's
fresh source-stratified RI-ML re-run reproduced the shipped mixed-RI KPI's
overall test MAE/R² (0.0304 / 0.6381) **bit-identically**.

## Headline finding: RadonPy's dielectric ground truth is broken

The C8 objective assumed Onsager could be ported onto the same population the
shipped `mixed-openpoly-radonpy-dielectric-conformal-kpi` trains/evaluates on.
Testing this surfaced a decisive, model-independent data-integrity defect:
**`static_dielectric_const < n_measured²` (physically impossible — a material's
static permittivity can never be below its purely-electronic/optical limit,
Fröhlich 1949 Ch.2) in 962/1075 = 89.5% of RadonPy PI1070 rows.** OpenPoly's
own internally-consistent DFT decomposition (`Dielectric Constant Total >=
Dielectric Constant Electronic`) has **zero** such violations across all 295
rows, isolating the defect to RadonPy's MD fluctuation-formula route (a known
literature limitation: short-trajectory dipole-fluctuation dielectric
constants under-converge toward the electronic-only limit, especially for
weakly-polar polymers). RadonPy supplies 1077/1372 = 79% of the shipped ML
KPI's combined training/eval population and is the *only* dipole-moment
source in this module — so this is not merely a limitation on how well physics
predicts; it means the shipped ML KPI itself was scored (and largely trained)
against a majority-corrupted target for its dominant data source.

## Scope honestly narrowed (not silently dropped)

- **Density** (RadonPy, n=1077): complete triplet, cited from existing receipts.
- **Tg** (OpenPoly, n=442): complete triplet; stack is new this fire (fresh
  plain-random 60/20/20 split, distinct from the existing scaffold-safe/LOSO
  splits — both cited for context).
- **Dielectric** (RadonPy-only, n=1075): physics/ML/stack triplet built, but
  scored against ground truth 89.5% of which is physically invalid (see
  above). **OpenPoly dielectric physics arm: BLOCKED_DATA** — no dipole-moment
  source anywhere in this module.
- **Refractive index**: ML arm on the full mixed population (n=1223, matches
  existing KPI); physics/stack arms RadonPy-only (n=211 in the physics-
  comparable test subset), because OpenPoly has no density column.
  **OpenPoly RI physics arm: BLOCKED_DATA** — no density source.

Both OpenPoly gaps are filed to the data-acquisition queue.

## Reproducibility

Two-replay SHA-256 gate = PASS (`receipt_body.canonical.json` ==
`receipt_body.runB.json`). DSSE Ed25519 signature (local AUDIT_ONLY key
`local-9028773f…`, same key/format as the accepted C7-fire-3 receipt)
SIGNATURE_VERIFY=PASS, `.signature` is a JSON object.

Run: `python3 c8_compute.py` (writes `/tmp/c8_raw_results_final.json`, also
saved here as `c8_raw_results.json`); sign: `python3 c8_sign_receipt.py`.
