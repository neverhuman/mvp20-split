# barrier-water-uptake-hydrophilicity-ccby-v1 (AUDIT_ONLY)

Two-part red-team increment. Deterministic, two-replay byte-stable, signed with
the repo `LOCAL_DEVELOPMENT_AUDIT_ONLY` Ed25519 key (NOT trust-anchored).
Promotes nothing; touches no existing receipt, the manifest, or any governance
artifact. Canonical diagnostic SHA-256
`b927cf73a117efd958a4954f6407b84bc42723334893c479a12585350a1a2c31`.

## PART A — "Do we actually have FULL Phase-0?" — recomputed LIVE
Answer: **NO, in the scientific sense.** Computed at runtime from
`config/program/phase0-decision-report.v2.json`, `module-manifest.json`, and all
29 `*/evidence/phase0/benchmark/benchmark-lock.v1.json` files:
- `scientific_readiness == VALIDATED` for **0 / 29** modules. The independent
  `module-manifest.json` lists **all 29 as UNVALIDATED**.
- The 10 modules labelled PHASE_0 = **7 NOT_APPLICABLE** (governance/infra: no
  science object) + **3 LOCKED_INTERNAL** (internal ceiling, not externally
  validated — including the crown-jewel solvency-score).
- `scientific_success_required_for_phase0 == false` in **all 29** benchmark-locks
  → "Phase-0" is a **governance** gate. "FULL Phase-0" ≠ "validated science".
- This autonomous AUDIT_ONLY cron **cannot** promote any module; promotion needs
  two distinct trusted human-key signatures it does not hold and must not forge.

## PART B — real new science: the BARRIER-WATER axis (#1 marine mission gap)
Equilibrium water uptake of the cured film drives osmotic blistering and
cathodic disbondment — the corrosion-protection mechanism the barrier module is
meant to model (it currently has only a weak, scope-mismatched substrate QSPR).

**Red-team of the natural a-priori model on REAL rights-clean data.** CC BY 4.0,
already rights-established in-tree: three DGEBA + diamine networks cured and
immersed under one protocol (Polymers 2024, 16(1):67 = doi 10.3390/polym16010067
= PMC10780492): **EP-CYDM 0.16 % < EP-DDS 1.7 % < EP-8CH2DA 2.0 %**.

Parameter-free a-priori descriptors (computed from stoichiometric cured-network
composition; NO fit to the water data → non-circular):
- secondary-hydroxyl concentration `c_OH` and total polar-atom `c_polar`
  (hydrophilicity) → **Spearman −0.50 vs measured uptake (ANTI-correlated)**;
- flexible aliphatic `-CH2-` count in the amine backbone (free-volume proxy) →
  Spearman **+0.50**.

**Honest finding:** the cycloaliphatic CYDM network has the *highest* hydroxyl
density yet the *lowest* uptake — so "more hydrophilic groups → more water" is
**REFUTED for within-family ranking**. The controlling variable is amine-backbone
free volume / crosslink density (rigid cycloaliphatic packs tightest → lowest;
flexible octamethylene opens the most free volume → highest; rigid aromatic-
sulfone DDS intermediate). The free-volume proxy captures the extreme but not
the polar-sulfone DDS, so with n=3 and ≥2 competing effects the model is
underdetermined (no significance claimed at n=3).

**Cross-class positive control** (canonical polymer physical constants, rank-only,
**no coating claim**): across PTFE→PS→PMMA→PA6→PVOH (>3 orders of magnitude of
uptake) the same hydrophilicity descriptor (Hansen δ_h) DOES rank uptake
(**Spearman 1.00**) — the engine is valid at coarse resolution; it is the
within-family, design-relevant resolution that is model-and-data co-limited.

**Verdict:** the barrier-water-uptake axis **cannot be promoted**; it needs a
validated free-volume/crosslink descriptor plus protocol-controlled n≥~10 — the
same wall as network Tg.

## Reproduce
```
python3 barrier_water_uptake_audit.py diagnostic.canonical.json
python3 barrier_water_uptake_audit.py diagnostic.runB.json   # identical bytes
python3 sign_barrier_water_uptake.py                          # re-sign (asserts two-replay)
```
