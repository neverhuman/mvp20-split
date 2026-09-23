# hansen-temperature-envelope-v1 — HANDOFF

**Module:** amphora-solvency-score  **Authority:** AUDIT_ONLY  **Axis:** B (theory)
**Receipt:** `amphora-solvency-score/reference/mvp20/data/hansen_temperature_envelope_receipt.v1.json`
**KPI:** `amphora-solvency-score/evidence/phase0/kpis/hansen-temperature-envelope-v1-kpi.v1.json`
**Canonical diagnostic SHA-256:** `2f6718338836113d0278d10770ccc9901c3e16b5e453573a7263fefbccf944eb` (two-replay PASS)

## What was tested

The shipped Hansen RED solvency verdict is built from 25 C parameter tables and an
interaction radius `R` that carries **no temperature argument at all**. Marine two-part
epoxy-amine coatings are applied near 5 C (ISO 12944-7 / IMO PSPC cold-end practice)
and serviced near 40 C on tropical topsides. This benchmark applies Hansen &
Beerbower's own published, zero-free-parameter HSP temperature law over that envelope
and asks whether the shipped verdict survives its own physics.

    d(dD)/dT = -1.25 a dD ;  d(dP)/dT = -0.50 a dP ;  d(dH)/dT = -(1.22e-3 + 0.50 a) dH
    (Hansen & Beerbower 1971, Kirk-Othmer Suppl. Vol. 2nd ed. pp. 889-910;
     reproduced Hansen 2007 handbook Ch. 1, ISBN 978-0-8493-7248-3)

Integrated exactly for constant `a` about T0 = 298.15 K. Fixture: the module's CC0-1.0
Phase-0 known-answer set, 5 polymers x 15 solvents = 75 labelled pairs.

## Result — H0 REFUTED

H0: "every 25 C RED verdict is invariant over 5-40 C under Hansen's own temperature law."

| quantity | value |
|---|---|
| 25 C baseline | 67/75, AUROC 0.948773 — reproduces shipped headline exactly |
| law implementation vs published derivatives | max rel err **0.0** |
| worst-case verdict flips in 5-40 C | **5 of 75** |
| flipped pairs | nylon66::DMF, nylon66::n-butanol, PS::acetone, PVC::DCM, PVC::THF |
| smallest common alpha breaking invariance | **2.61e-4 1/K** (far below any real organic liquid) |
| common-alpha flip count across 6.0e-4 .. 1.5e-3 grid | constant at 2 — **not alpha-tuned** |
| min Kendall tau-b vs 25 C ordering (a=1e-3) | 0.991351 |
| AUROC range (a=1e-3) | [0.947330, 0.952381] |

Temperature moves the **decision boundary**, not the ranking. Named crossings
(a = 1e-3): `polyamide-nylon66::dimethylformamide` (RED 0.9868 at 25 C) crosses at
**12.13 C**; `polystyrene::acetone` (RED 1.0053) crosses at **29.52 C**.

## Mechanism — fully attributed to fixed R

Scenario S3 co-scales `R(T) = R * |d_p(T)| / |d_p(T0)|` with the polymer's own Hansen-norm
contraction. That removes **5 of 5** flips (S3 flips = 0). Since `RED = Ra/R` and all three
components contract with rising T while R is held fixed, a fixed-R 25 C Hansen sphere is
systematically **more permissive hot, more restrictive cold** than its calibration.

## Honest limitations (carried in the receipt)

- **The alpha-free lower bound S0 flips ZERO verdicts.** The alpha-independent 1.22e-3
  H-bonding term alone does *not* refute H0; non-zero thermal expansion is necessary.
  The refutation is not alpha-*tuned* (see 2.61e-4 threshold + flat flip count), but it
  is alpha-*dependent*.
- **Both bootstrap CIs straddle zero** (5 C: [-0.04, 0.0]; 40 C: [-0.04, 0.0], seed
  20260731, n=5000). Aggregate divergence is not statistically resolvable at n = 75.
  The durable findings are the *named boundary-crossing pairs* and the *fixed-R
  mechanism* — not a headline accuracy change.
- Fixture labels are 25 C observations, so off-25 C counts measure **divergence from the
  shipped verdict set, not predictive error**. No pair is re-labelled.
- No per-liquid thermal expansion coefficients exist in the fixture; none were invented.
  alpha is swept over a declared range, never fitted.
- Self-authored CC0 fixture — NOT external validation. The externally-validated science
  remains the separate BigSolDB leave-solute-out benchmark.

## Next move this unlocks

Whether `R` should co-scale with temperature is **not settled here** and is the single
highest-value follow-up: it needs external solubility data for the same polymer-solvent
pairs at two or more temperatures. That is a DATA ask, not a theory ask.

## Reproduce

    cd /home/ubuntu/amphora/build/mvp20-split
    B=amphora-solvency-score/benchmarks/hansen-temperature-envelope-v1
    python3 $B/run_temperature_envelope.py $B/diagnostic.canonical.json
    python3 $B/run_temperature_envelope.py $B/diagnostic.runB.json   # byte-identical
    python3 $B/sign_temperature_envelope.py

Does not promote the module. Does not edit the portfolio manifest (66 receipts /
11 modules unchanged, mtime 2026-07-24). Does not close EVALUATION_SIGNATURE_ABSENT.
