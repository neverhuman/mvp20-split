# formulation-arithmetic-coverage-spreading-v1 (AUDIT_ONLY)

Adds the **applied-film** layer of dimensioned formulation arithmetic to
`amphora-formulation-arithmetic`: theoretical/practical **coverage (spreading
rate)**, **wet↔dry film thickness closure**, and **dry-film areal mass** — the
zero-fitted-parameter identities that convert a formulated 2K epoxy-amine
recipe into a paintable marine spec. Composes on the volume-solids output of the
prior dimensioned receipt (`539f3e67…`) and its GUM uncertainty (`5f355eb4…`).

## Engine (zero fitted parameters)
- `TC = 1000·VS_frac / DFT_µm` [m²/L] — theoretical coverage / spreading rate
- `WFT = DFT_µm / VS_frac` [µm] — wet film thickness to hit a target DFT
- `PC = TC·(1 − loss_frac)` [m²/L] — practical coverage (declared transfer loss)
- areal dry mass `= ρ_dry · DFT_µm` [g/m²]; `ρ_dry = M_solid / V_solid`

## Sources
- Wicks, Jones, Pappas & Wicks 2007, *Organic Coatings: Science and
  Technology*, 3rd ed., Wiley, ISBN 978-0-471-69806-7 (Ch. 23).
- ASTM D5145 (spreading rate); ISO 3233 / ASTM D2697 (volume solids).
- **1604 rule** external anchor: `231 in³/gal ÷ (0.001 in · 144 in²/ft²) =
  1604.1667 ft²/gal` per mil at 100 % volume solids — a pure US-customary unit
  identity, reproduced bit-for-bit by the SI-path formula (KA1).

## Result — `COVERAGE_SPREADING_ENGINE_READY__KNOWN_ANSWER_BATTERY_PASS__1604_ANCHOR_EXACT`
- Known-answer battery **9/9 PASS** (targets fixed by definition or by the exact
  1604 unit identity; non-circular — the engine never supplies its own target).
- Reproduces prior volume solids **0.6673699761** and `u_c` **0.0025523912**
  bit-for-bit (density-chain provenance guard).
- Real marine primer @ 127 µm (5 mil) DFT: **TC 5.255 m²/L (149.0 ft²/gal)**,
  **WFT 190.3 µm (7.5 mil)**, PC 3.42 m²/L @ 35 % loss, dry areal mass
  246.0 g/m², ρ_dry 1.937 g/cm³.
- GUM LPU + Monte Carlo (seed 20260729, N=400k) intervals on TC/WFT.
  **Finding:** at a fixed DFT setpoint the coverage interval is driven purely by
  volume-solids uncertainty (dominant: xylene density); once realistic ±20%
  as-applied DFT control is admitted it **dominates** — applied-coverage
  variance is an application-control problem, not a formulation-arithmetic one.

## Reproduce
```
python3 run_coverage_spreading.py diagnostic.canonical.json
python3 run_coverage_spreading.py diagnostic.runB.json   # byte-identical
python3 sign_coverage.py                                  # DSSE Ed25519
```
Two-replay SHA-256 `aed83340…` PASS. Signed PHASE0_EVALUATOR
(`3ef6b35c…`, derives pinned trust-store key), AUDIT_ONLY.

## Scope / what this is NOT
Not product qualification, batch release, or wet-lab coverage on a real
substrate. Transfer-loss is a declared application input, not a validated
predictive model. Does **not** modify the live Rust engine (still MASS_ONLY),
any locked dataset, the signed Phase-0 KPI, or the 66-receipt / 11-module
portfolio manifest. Not a promotion (needs two human dual-identity keys).
