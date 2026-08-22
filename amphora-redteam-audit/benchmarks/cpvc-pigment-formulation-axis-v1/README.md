# cpvc-pigment-formulation-axis-v1 (AUDIT_ONLY)

Autonomous red-team increment (xbabe2). Signed with the LOCAL_DEVELOPMENT_AUDIT_ONLY
key (local-9028773f...), **not** a trust-anchored phase0 key. Promotes nothing;
modifies no existing receipt and not the manifest (still **66 receipts / 11 modules**).

## (A) Phase-0 honesty red-team — recomputed LIVE this run
Read directly from the live governance files:
- **0 / 40** ranked modules have `scientific_readiness == VALIDATED`.
- **29 / 29** live benchmark-locks set `scientific_success_required_for_phase0 = false`.
- Phase distribution: 16 PHASE_0, 13 PRE_PHASE_0, 11 unset (infra crates).
- => **"FULL Phase-0" is a GOVERNANCE state, NOT validated science.** This key
  cannot promote anything (promotion needs two trust-anchored phase0 signatures).
  No dishonest promotion was found to revert.

## (B) New science: the PIGMENT-FORMULATION barrier axis (CPVC)
**Gap found:** all ~23 previously-receipted scientific axes reason about *molecules*
(solvent, cured-network, or surface chemistry). **None** reasons about the *pigmented
film*. For a marine anti-corrosion coating the single governing barrier parameter is
the **Critical Pigment Volume Concentration (CPVC)**: below it the film is a continuous
barrier; above it interstitial voids open and water/O2 permeability, blistering and
under-film corrosion rise sharply (reduced PVC Lambda = PVC/CPVC). Highest-value
un-touched layer in the portfolio.

**Engine (zero fitted parameters):** Asbeck & Van Loo, Ind. Eng. Chem. 41 (1949) 1470
    CPVC = 1 / (1 + OA*rho / 93.5)
OA = ISO 787-5 oil absorption (g linseed oil / 100 g pigment); rho = pigment density;
93.5 = 100 x rho(linseed oil). OA and rho are two physically independent measurements
(rub-out endpoint; pycnometry) — neither is a CPVC measurement.

**Non-circular validation (needs ZERO external CPVC data):** first-principles
random-packing-bounds falsification. CPVC is a packing fraction, so for equiaxed/
nodular pigments it must lie in [0.44, 0.7405] (cohesive random-loose -> ordered
close packing pi/(3*sqrt2)). Outside is geometrically impossible and would falsify
the packing premise.
- **Falsification KPI: 7 / 7 equiaxed/nodular pigments in-band (PASS).**
- Directional physics reproduced: dense barytes -> high CPVC 0.68; high-structure
  laminar talc/mica -> low 0.45/0.38 (correctly at/below the equiaxed floor —
  anisotropic platy packing); anticorrosive zinc-phosphate 0.52.
- **TiO2 magnitude anchor:** treated rutile (OA~24) -> engine **0.487**, inside the
  textbook density-method CPVC band **0.45-0.50** (single independent anchor).

### Verdict
`ENGINE_READY__PHYSICAL_BOUNDS_CONSISTENT__PRECISION_VALIDATION_DATA_RIGHTS_BLOCKED`

Genuine pre-phase-0 groundwork: opens the pigment-formulation layer with a ready,
physically-sound, non-circular engine. Not a precision external validation and not
promotable.

### What would move this to a validatable phase-0 KPI (founder data ask)
Acquire a rights-clean (CC-BY / licensed) set of >=12 coating pigments, each with
(i) ISO 787-5 oil absorption, (ii) pycnometric density, and (iii) CPVC measured by an
independent transition method (density-series / gas-permeation / fluorescence). Then
MAPE + Spearman of engine-CPVC vs measured-CPVC is a real external-validation KPI.
Honest blocker this session: paired (OA + independently-measured CPVC) tables were not
obtainable rights-clean — building a "validation" from oil-absorption alone would be
circular, so it was not done.

## Reproduce
    python3 cpvc_pigment_axis_audit.py diagnostic.canonical.json
    python3 cpvc_pigment_axis_audit.py /tmp/replay.json   # byte-identical
    python3 sign_cpvc.py
two-replay SHA256 = 68997d90785825ce530b173a6b5548e775a33e1c6775534caeb6ff8c15476d3f
