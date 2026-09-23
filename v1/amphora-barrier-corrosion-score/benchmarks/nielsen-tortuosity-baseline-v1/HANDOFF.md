# nielsen-tortuosity-baseline-v1 — physical a-priori barrier baseline

**Date:** 2026-07-28 · host: xbabe2 (canonical) · authority: **AUDIT_ONLY**
**Module:** amphora-barrier-corrosion-score (PRE_PHASE_0, UNVALIDATED)

## What this is
The first **physical, named, a-priori** barrier baseline for the module. The prior
`barrier-null-char-v1` showed only that *monotone nulls* (solids-only, PVC-only)
fail to reproduce the intermediate Rc optimum. This tests two published
platelet-tortuosity barrier models parameterised with **published densities and
published aspect-ratio ceilings — NOT fit to the Rc data** — against the two strict
in-class epoxy-amine nanofiller EIS ladders (asperti2024 clay, zhu2022 graphene),
respecting their CC-BY within-study-only use limit (no cross-study pooling).

## Named baselines (published, rights-clean)
- **Nielsen 1967** J. Macromol. Sci. A 1(5):929, doi 10.1080/10601326708053745 —
  `Rc/Rc0 = (1 + (a/2)phi)/(1-phi)`.
- **Cussler 1988** J. Membr. Sci. 38(2):161, doi 10.1016/S0376-7388(00)80877-7 —
  `Rc/Rc0 = 1 + a^2 phi^2/(1-phi)` (high-aspect regular-array flake limit).
- Load-bearing assumption stated explicitly: `Rc/Rc0 = P0/P` (ideal defect-free
  two-phase impermeable-platelet-in-resistive-matrix film; same tortuosity factor
  governs permeability and ionic pore resistance). Densities: cured epoxy-amine
  1.10-1.20, Cloisite 30B 1.90-2.00, graphene 2.00-2.26 g/cm^3. a ceilings:
  MMT [50,1000] (LeBaron 1999; Bharadwaj 2001), graphene [1000,30000] (Cui 2016).

## Two results per series
- **(T1) Structural / optimum-location.** Both models strictly increasing in phi ->
  both predict best barrier at MAX loading. Observed optima are interior (clay 1 wt%,
  graphene 0.7 wt%). **Both physical models REFUTED on optimum location** — quantifies
  that the beat-the-monotone signal is dispersion/agglomeration, outside continuum
  tortuosity. Stronger than the trivial monotone null.
- **(T2) Initial-rise aspect-ratio inversion (level0 -> optimum).** Invert each model
  for the effective a the observed Rc-improvement demands, over the density band, vs
  the published a ceiling:
  - **clay (asperti2024):** BIF 200x; Nielsen a_eff ~ 62k-72k, Cussler a_eff ~
    2200-2550 — **both ABOVE the MMT ceiling (1000) => tortuosity_insufficient_REFUTED**
    (even the optimistic quadratic Cussler needs ~2.2-2.5x the published ceiling).
  - **graphene (zhu2022):** BIF 15.4x; Nielsen a_eff ~ 6.8k-8.4k, Cussler a_eff ~
    900-1110 — **within the graphene ceiling [1000,30000] => tortuosity_sufficient**.
    Mica-base confound noted (phi_graphene referenced to total film -> a_eff is a lower
    bound); SECONDARY/DIRECTIONAL.

## Honest verdict
Adds the first physical named baselines and a NEW falsifiable a-priori discriminator
(effective-aspect-ratio inversion) separating tortuosity-consistent (graphene) from
tortuosity-insufficient (clay) initial barrier gains. Does **NOT** establish a
validated positive barrier ranking model — the interior optimum (the part that beats
a monotone predictor) is dispersion/agglomeration, which no zero-parameter continuum
model captures. Standing DATA wall unchanged: >=3 pooled protocol-controlled
formulation->Rc series with dispersion/PVC metadata.

## Reproducibility
- stdlib-only, no random, no timestamp, floats round(.,6). Two runs -> canonical SHA-256
  `c03bd3d83373dece3c115ba13443e9c6c2c446cd6db44dbdedbb4f4b0e9ad2ad` (byte-identical).
  TWO_REPLAY_GATE=PASS. All fail-closed checks pass on both series.
- harness_sha256 `dbf6522c9a042a4d5e60c82394405d309f7b50e970c512fd8109f42ff40d6d77`.
- DSSE Ed25519 signed with trust-anchored Phase-0 evaluator key
  `phase0-evaluator-3ef6b35c...`, **AUDIT_ONLY** (promotes_authority=false,
  modifies_manifest=false; scientific_readiness stays UNVALIDATED; manifest 66/11
  untouched). eval + reviewer key ids both derive the pinned trust store.
  INDEPENDENT_VERIFY=PASS. envelope_sha256 `908c7a78...`.

## Files
- nielsen_tortuosity.py — deterministic benchmark
- result.{runA,runB,canonical}.json — two runs + canonical
- sign_nielsen.py — DSSE signer (AUDIT_ONLY)
- nielsen-tortuosity-baseline-receipt.v1.dsse.json — signed receipt
