# formulation-arithmetic-uncertainty-propagation-v1

**AUDIT_ONLY** — adds the first *calibrated uncertainty intervals* to
`amphora-formulation-arithmetic`'s dimensioned outputs. The prior receipt
(`formulation-arithmetic-dimensioned-v1`, two-replay `539f3e67…`) delivered the
dimensioned engine (volume-solids ASTM D2697, PVC, wet-density, VOC EPA M24,
EEW/AHEW stoichiometry) as **point estimates with no stated uncertainty**. This
receipt propagates the documented measurement uncertainty of the load-bearing
physical inputs (ingredient densities + EEW/AHEW) to every output by two
independent methods and cross-validates them.

## Method (zero fitted parameters)
* **Input Type B budget** — GUM (JCGM 100:2008) §4.3: rectangular quoting-
  resolution component convolved with a rectangular grade/source-dispersion
  component (0.5/1.5/2.5/3.0 % rel. half-width for TDS / SUPPLIER_GUIDE /
  DISTRIBUTOR / REFERENCE_NOMINAL).
* **LPU** — first-order numerical-Jacobian Law of Propagation of Uncertainty
  (GUM §5.1 eq. 10, uncorrelated inputs).
* **Monte Carlo** — JCGM 101:2008 Supplement 1, N=400 000, pinned seed, exact
  trapezoidal convolution of the two Type B rectangulars per input.

Because the engine has **zero fitted parameters**, predictive uncertainty is
input-measurement uncertainty — bootstrap / split-conformal do not apply; GUM
propagation is the metrologically-correct calibrated interval.

## Result (marine anti-corrosion epoxy-amine primer)
`GUM_LPU_STANDARD_UNCERTAINTY_VALIDATED_BY_MONTE_CARLO`
* LPU `u_c` matches MC `std` for **every** output (max rel. diff 0.09 %) —
  linearization validated.
* **VOC = 284.13 g/L, u_c = 1.22 g/L, MC 95 % [281.80, 286.38]**; dominant
  contributor = xylene density.
* Finding (reproduces JCGM 101 §8 motivation): Gaussian `k=1.96` **over-covers**
  for one/two-bounded-input budgets — MC effective `k≈1.68` (stoich), `1.78`
  (volume-solids) vs `1.95` (PVC). Report the MC interval as the calibrated
  interval.
* Known-answer sensitivity battery 3/3: neat-solvent ∂VOC/∂ρ=1000 (external
  constant); zero-solvent volume-solids u=0 (exact identity); intensive scale-
  invariance of value **and** uncertainty (exact identity).

## Not closed
No promotion / no scientific_readiness flip (needs two trust-anchored human
phase0 keys). No manifest edit (66 receipts / 11 modules). Rust engine still
MASS_ONLY. Tightening the Type B grade half-widths to measured supplier
tolerance bands is a Phase-1 data ask.

## Reproduce
```
python3 run_uncertainty_propagation.py diagnostic.canonical.json
python3 run_uncertainty_propagation.py diagnostic.runB.json   # two-replay gate
python3 sign_uncertainty.py                                    # DSSE-Ed25519
```
Two-replay SHA-256 `5f355eb4…` (PASS). Signed phase0-evaluator
`3ef6b35c…` (AUDIT_ONLY; derives pinned trust-store key).
