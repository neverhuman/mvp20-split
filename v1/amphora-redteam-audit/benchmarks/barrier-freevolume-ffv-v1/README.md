# barrier-freevolume-ffv-v1 — free-volume barrier-transport axis (AUDIT_ONLY)

**Date:** 2026-07-26 · **Key:** local-9028773f… (LOCAL_DEVELOPMENT_AUDIT_ONLY, NOT phase0-trust-anchored)
**Target module:** amphora-barrier-corrosion-score · **Verdict:**
`ENGINE_READY__FOUNDATION_KNOWN_ANSWER_VALIDATED__FFV_BOUNDS_CONSISTENT_DIAGNOSTIC__ABSOLUTE_PERMEABILITY_CALIBRATION_DATA_RIGHTS_BLOCKED`

## Why this exists
Marine anti-corrosion is a **transport** problem: the film must throttle H₂O/O₂/Cl⁻ flux to the
steel. The rate is set by penetrant **diffusion**, which free-volume theory (Doolittle;
Cohen–Turnbull 1959) ties to the polymer's **Fractional Free Volume** FFV = (V − 1.3·Vw)/V
(Bondi 1964 packing factor; Van Krevelen ch.4/18). **All 66 signed receipts reason about the
equilibrium barrier state (uptake, CPVC, wet-Tg, adhesion); none computes the free volume that
sets the diffusion RATE.** This stands up that axis.

## What is VALIDATED (load-bearing, non-circular, zero fitted parameters)
The a-priori occupied/van der Waals molecular volume — the input to FFV — computed **three
independent ways** and cross-checked over 20 live in-tree DGEBA-class epoxy + amine SMILES
(`reports/data/epoxy-amine-20-audit-probes.v1.json`):
- **A · Zhao-Abraham-Zissimos 2003 VABC** (atom-additive VdW volume ≈ Bondi)
- **B · Abraham-McGowan 1987** characteristic volume (independent atomic lineage)
- **C · RDKit** explicit-conformer 3-D grid VdW volume (pure geometry)

**Known-answer battery 8/8 PASS:** McGowan CH₄/EtOH/C₆H₆ reproduce literature Vx exactly
(<0.05 cm³/mol); VABC benzene 48.9 vs Bondi 48.36 (+1.1%) and cyclohexane 60.2 vs 61.42 (−1.9%);
Pearson(VABC, RDKit-geometry)=0.99926, Pearson(VABC, McGowan)=0.99833; atom-additivity reproduces
explicit 3-D VdW volume within ~3.5% (mean RDKit/VABC 1.036). None uses permeability/FFV/barrier
data → non-circular w.r.t. the barrier claim.

## What is DIAGNOSTIC (not gated)
FFV of six real DGEBA-amine networks (correct N–H stoichiometry via RDKit; mass-conserving
addition cure) spans **0.083–0.181** across ρ 1.10–1.20 g/cc — inside the amorphous glassy band
[0.08, 0.20]. Reported as bounds-consistent **only**: the absolute value is density-controlled
(~0.07 FFV per 0.10 g/cc) and additive Vw over-counts occupied volume by a few % at ring-opened
networks. The load-bearing missing input is **measured per-network cured density**, not more theory.

## Honest negatives
- **Penetrant size proxy REFUTED:** VdW-volume-equivalent sphere diameter vs published kinetic
  diameters, Spearman **0.39** — molecular shape (linear CO₂/Cl₂/N₂) breaks the volume→kinetic-
  diameter map. Free volume sets the polymer side; penetrant selectivity needs kinetic diameter.
- **Per-hardener permeability ranking DATA-RIGHTS-BLOCKED** (needs measured density + P_O₂/P_H₂O).

## Does NOT close
Promotes nothing (phase-0 is a governance state; 0/29 ranked modules scientific_readiness==VALIDATED;
needs two trust-anchored phase0 signatures this AUDIT_ONLY key cannot supply). Does not change the
manifest (still 66 receipts / 11 modules) or modify any existing receipt or shipped Rust engine.

## Reproduce
```
python3 barrier_freevolume_audit.py diagnostic.canonical.json   # two-replay SHA 9529db75…
python3 sign_barrier_ffv.py                                     # envelope SHA 6d04a88b…, DSSE_VERIFY=PASS
```
