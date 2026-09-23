# formulation-arithmetic mix-ratio-conversion-v1 (AUDIT_ONLY)

Theory axis (option B). Adds the **metered-dosing** layer of dimensioned
formulation arithmetic: zero-fitted-parameter conversion between the three
equivalent statements of a 2K epoxy-amine mix ratio and their GUM/MC intervals.

* stoichiometric parts-hardener-per-hundred-resin BY WEIGHT: `PHR = 100*AHEW/EEW`
* the same ratio BY VOLUME (what field pumps meter): `Rv = PHR*(rho_A/rho_B)`
* the amine-H:epoxide EQUIVALENTS index that governs cure: `r = (m_B/AHEW)/(m_A/EEW)` (=1 at match)

Sources: Lee & Neville 1967 *Handbook of Epoxy Resins* (LCCN 66-27772);
Petrie 2006 *Epoxy Adhesive Formulations* (ISBN 0-07-145544-2) Ch.3;
Ellis (ed.) 1993 *Chemistry & Technology of Epoxy Resins* (ISBN 978-0-7514-0095-6);
volume conversion is the elementary `V=m/rho` identity (ASTM D1475 density basis).
Inputs are rights-clean in-tree amphora-ingredient-library facts.json TDS constants.

## Results
* KA battery **8/8 PASS** (equal-density identity, round-trip inverse, r=1 at
  stoich, convention-confusion = density ratio exactly, scale invariance,
  external reproduction of the dimensioned primer 100:13, hostile nulls, monotonicity).
* Reproduces the prior dimensioned primer (DER-331+TETA) as near-stoichiometric,
  r=0.9975 (provenance tie to 539f3e67).
* LPU validated by Monte Carlo (seed 20260730, N=400k) on all four outputs.
* **Finding:** amine:epoxide index precision is dominated by the resin's published
  EEW band (~1.5% rel); weight->volume metering adds only ~0.1 pp RSS from the two
  densities. The systematic error of CONFUSING weight vs volume ratio equals the
  density ratio exactly: DER-331(1.16)+Ancamide 350A(0.97) => -16.4% (weight-spec
  poured by volume) or +19.6% (volume-spec weighed), both outside the +/-10%
  mass-tolerance envelope from amphora-envelope-gates-stoichiometric-ratio-tolerance.
  Convention discipline, not density precision, is the load-bearing control.

## Reproduce
```
python3 run_mix_ratio.py diagnostic.canonical.json
python3 run_mix_ratio.py diagnostic.runB.json
cmp diagnostic.canonical.json diagnostic.runB.json   # byte-identical
python3 sign_mix_ratio.py                             # DSSE Ed25519, AUDIT_ONLY
```

Two-replay SHA `6ec4bdf2...`. Signed phase0-evaluator `3ef6b35c...` (AUDIT_ONLY,
derives pinned trust key). No promotion; manifest untouched (66/11); live Rust
engine still MASS_ONLY; no locked dataset or signed KPI modified.
