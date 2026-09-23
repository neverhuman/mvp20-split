# formulation-arithmetic reduced-pvc-porosity-v1 (AUDIT_ONLY)

Theory axis (option B). Adds the **pigmentation-regime** layer of dimensioned
formulation arithmetic: zero-fitted-parameter Bierwagen reduced PVC and its
exact geometric consequences above CPVC.

* reduced PVC: `LAMBDA = PVC/CPVC`
* air-void porosity (PVC>=CPVC): `pi = 1 - CPVC/PVC = 1 - 1/LAMBDA` (0 below CPVC)
* dry-film volume amplification: `V_film/V_nv = LAMBDA` => porous DFT = LAMBDA x void-free DFT
* dry-film density: `rho_film = (1-pi) * (PVC*rho_p + (1-PVC)*rho_b)`

Sources: Asbeck & Van Loo 1949 (Ind. Eng. Chem. 41(7) 1470, DOI 10.1021/ie50475a042);
Bierwagen & Hay 1975 (Prog. Org. Coat. 3(4) 281-303, DOI 10.1016/0300-9440(75)80047-4);
Patton 1979 (Paint Flow and Pigment Dispersion, 2nd ed., ISBN 0-471-03272-7).
Inputs: the 10 signed Daniel-CPVC values/densities/OAs from
amphora-ingredient-library oil-absorption-cpvc-v1 (4b127f2d...) and DGEBA-331 +
Ancamide 350A facts.json constants for the ASTM D2697-consistent ideal-mix
nonvolatile binder density (NOT a cured-network density claim; see
amphora-cured-network-density-apriori-refuted).

## Results
* KA battery **12/12 PASS** (continuity at CPVC, pi<->LAMBDA identity, below-CPVC
  clamp, monotonicity, PVC->1 limits, film-volume amplification, mass closure,
  density homogeneity, scale invariance, hostile nulls fail-closed, Daniel
  provenance parity 10/10, independent volume-bookkeeping derivation == closed form).
* **Finding:** porosity onset above CPVC is FIRST-ORDER in relative PVC overshoot
  (`pi = eps/(1+eps)`; +5% PVC at CPVC -> 4.76 vol% voids) — CPVC is a cliff, not
  a soft optimum. Above CPVC the module's void-free coverage/DFT arithmetic
  mis-reads film build by exactly LAMBDA: iron-oxide-red primer at PVC 0.50
  (CPVC 0.4183) => +19.5% DFT, -16.3% dry-film density. GUM LPU (validated by
  400k-draw MC, seed 20260731, all 10 pigments, LPU/MC within 0.1%) puts
  u(pi) ~ 0.02-0.05 at LAMBDA 1.2 from a declared +/-10% OA band — comparable to
  a 5% PVC overshoot, so OA data quality and PVC metering are co-equal controls.
* Below CPVC pi == 0 exactly, consistent with the barrier modules' void-free
  Fickian premise; zinc-rich primers (amphora-zinc-galvanic-percolation) sit
  deliberately in the LAMBDA > 1 porous/contact regime.

## Reproduce
```
python3 run_reduced_pvc.py diagnostic.canonical.json
python3 run_reduced_pvc.py diagnostic.runB.json
cmp diagnostic.canonical.json diagnostic.runB.json   # byte-identical
python3 sign_reduced_pvc.py                           # DSSE Ed25519, AUDIT_ONLY
```

Two-replay SHA `a98c7281...`. Signed phase0-evaluator `3ef6b35c...` (AUDIT_ONLY,
derives pinned trust key). No promotion; manifest untouched (66/11); live Rust
engine still MASS_ONLY; no locked dataset or signed KPI modified.
