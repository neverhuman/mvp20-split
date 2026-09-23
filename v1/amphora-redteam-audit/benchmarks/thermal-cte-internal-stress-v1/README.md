# thermal-cte-internal-stress-v1 (AUDIT_ONLY)

NEW marine failure-mode axis untouched by all 66 signed receipts: thermal-cycling
internal stress from coating/steel CTE mismatch (splash-zone cracking ->
under-film corrosion).

## Theory (zero fitted params)
- Simha-Boyer  (alpha_l-alpha_g)*Tg = K1 = 0.113  (volumetric)
- Boyer-Bondi   alpha_l*Tg          = K2 = 0.164  => alpha_g*Tg = K2-K1 = 0.051
- Isotropic identity  alpha_V = 3*alpha_L
- Biaxial thin-film stress  sigma = E*(alpha_coat-alpha_sub)*dT/(1-nu)  (Timoshenko/Corcoran)

## Inputs
- REAL: 7 protocol-consistent DGEBA-amine network Tg, read LIVE from
  network-tg-feasibility-v4/diagnostic.canonical.json (traces to a signed receipt).
- REFERENCE_NOMINAL (flagged, sets magnitude scale only, not ranking): steel CTE
  12 ppm/K, epoxy E 2.5 GPa, nu 0.35, UTS 60 MPa, marine dT 40 K.

## Result
- Known-answer battery 12/12: Tier A (5/5 EXACT non-circular identities) +
  Tier B (2/2 universal-rule consistency, documented +-20-25% scatter).
- Engine ranks cracking risk monotone in Tg: best DGEBA+DDS (aromatic, Tg 208C,
  3.59 MPa) -> worst DGEBA+C8DA (aliphatic, Tg 94C, 5.28 MPa).
- Verdict: ENGINE_READY__EXACT_PHYSICS_VALIDATED__RANKING_DIRECTIONALLY_VALID__
  MAGNITUDE_APPROXIMATE__PRECISION_VALIDATION_MEASUREMENT_BLOCKED.

## Honest limits
Boyer rule under-predicts dense-network glassy CTE ~30-40%; magnitudes DIRECTIONAL.
Only the Tg-driven RANKING is defended. Precise per-network validation needs
measured coating CTE + modulus (TMA/DMA) -- measurement/data-rights blocked.

## Reproduce
python3 thermal_cte_stress_audit.py diagnostic.canonical.json
python3 thermal_cte_stress_audit.py diagnostic.runB.json   # byte-identical
python3 sign_thermal_cte.py                                 # DSSE Ed25519, AUDIT_ONLY

two_replay_sha256 0c406b04b480945ed825b1e0fd78866595e91679536032f374504a020b0196b4
envelope_sha256   dcf1d1c39894af69e6254a134d5805fac2c0d84e1018acfd0c8d6eb6837ce72d
