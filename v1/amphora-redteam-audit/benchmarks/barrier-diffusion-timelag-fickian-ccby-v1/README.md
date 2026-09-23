# barrier-diffusion-timelag-fickian-ccby-v1 (AUDIT_ONLY)

NEW marine barrier axis untouched by all 66 signed receipts: transient water/O2
INGRESS KINETICS through a coating film -- the Fickian time-lag, the operational
breakthrough time to the steel, and the Daynes steady-state permeance P = D*S.

Every prior barrier receipt reasons about the EQUILIBRIUM state (water-uptake
hydrophilicity, tortuosity flake, thermal-CTE) or a STATIC free-volume proxy for D
(barrier-freevolume-ffv-v1). None computes the TIME for water/O2 to traverse a real
dry-film-thickness, nor the steady-state permeance that governs the wet coating.

## Theory (zero fitted params -- J. Crank, The Mathematics of Diffusion, OUP 1975)
- Plane-sheet series   Mt/Minf = 1 - sum 8/((2n+1)^2 pi^2) exp(-(2n+1)^2 pi^2 D t/L^2)
- Half-time identity   D t_half / L^2 = 0.04919
- Short-time slope     Mt/Minf = (4/sqrt(pi)) sqrt(D t/L^2),  4/sqrt(pi)=2.256758
- Daynes-Barrer lag    t_L = L^2/(6 D)   (steady permeation intercept = 1/6)
- Permeability         P = D * S   (barrier merit = low P, low permeance P/L)
- Steel-backed film    impermeable substrate = no-flux face => effective 2L (t_half x4)

## Inputs
- REAL in-tree: equilibrium water uptake M_inf of 3 CC-BY DGEBA-amine systems
  (EP-CYDM 0.16% < EP-DDS 1.7% < EP-8CH2DA 2.0%), byte-identical to
  barrier-water-uptake-hydrophilicity-ccby-v1 -> Polymers 2024 16(1):67
  (PMC10780492, CC BY 4.0).
- REAL CC-BY literature anchors for D magnitude (FLAGGED, set timescale only):
  - PMC8877360 DGEBA epoxy-amine  D = 8.0e-13 m2/s, M_inf 2.2%, sqrt-t Fickian, CC BY 4.0
  - Polimeros/scielo DGEBA/TETA   D = 2.17e-11 m2/s, M_inf 4.82%, CC BY 4.0
  - ScienceDirect S0141391019302678 amine-epoxy band 1e-13..3e-13 m2/s (citation)

## Result
- Known-answer battery 6/6 EXACT PASS: half-time constant 0.0491827 vs 0.04919;
  short-time slope 2.256758 (rel err 5e-11); Daynes intercept 0.166666 vs 1/6;
  round-trip recovers the real anchor D=8.0e-13 to 0.015%; steel-backed factor 4.0
  exact; second-anchor timescale physical.
- Operational finding (250 um marine DFT, steel-backed, literature D): water
  half-saturates the film to the steel in ~4.3 h and 90%-saturates in ~18 h.
  Water ARRIVAL is fast -> marine barrier protection is a STEADY-STATE-PERMEANCE
  (P=D*S) and WET-ADHESION problem, NOT a water-arrival-delay problem. This
  inverts the naive "thicker = slower water" intuition.
- Permeance P=D*S ranks the 3 real systems UNAMBIGUOUSLY best->worst:
  EP-CYDM < EP-DDS < EP-8CH2DA. This RESOLVES the ambiguity of the uptake-only
  axis (where hydrophilic-group density anti-correlated): CYDM wins on BOTH low
  uptake (S) and tight free volume (D); the two independent descriptors agree
  once composed into P.
- Verdict: BARRIER_DIFFUSION_TIMELAG__EXACT_FICKIAN_IDENTITIES_VALIDATED__
  MAGNITUDE_LITERATURE_ANCHORED_CCBY__PERMEANCE_RANKING_REAL_INTREE__
  PRECISION_VALIDATION_DATA_RIGHTS_BLOCKED.

## Honest limits
Absolute D is REFERENCE_NOMINAL: the DGEBA-amine band spans 1e-13..2e-11 m2/s across
protocols/temperature (2+ orders) -- only the within-family RANKING (real M_inf,
reinforced by validated FFV) is defended. Real epoxies often show pseudo-Fickian /
two-stage sorption; single-D Fickian is an engineering approximation. D is strongly
Arrhenius in T. n=3, single protocol -> not statistically promotable (same data wall
as barrier-water-uptake). Precise per-system validation needs time-resolved
gravimetric curves for >=~10 protocol-matched DGEBA-amine films.

## Live FULL-phase-0 refutation (recomputed from shipped module-manifest.json)
Claim "FULL phase-0" = REFUTED. 0/29 modules scientific_readiness==VALIDATED;
29/29 ranking_eligible==false; every live benchmark-lock has
scientific_success_required_for_phase0==false. Live phase-0 is a GOVERNANCE state,
not validated science; promotion needs two trust-anchored phase0 human signatures
this AUDIT_ONLY key cannot supply. Manifest steady at 66 receipts / 11 modules.

## Reproduce
python3 barrier_diffusion_timelag_audit.py diagnostic.canonical.json
python3 barrier_diffusion_timelag_audit.py diagnostic.runB.json   # byte-identical
python3 sign_barrier_diffusion.py                                  # DSSE Ed25519, AUDIT_ONLY

two_replay_sha256 17fb17ae1d25c6cc3a8d911b25190dd7c68e4262e432f89c6672be588be71ea3
envelope_sha256   5c6a68a6af4093c95e6dc71e99f1eedac54bab2d490a56aa8ceb45141415b679
harness_sha256    a510c201df9df978f42de938321a0795826fa8fb196048ec9bb7b7c3b6e64f77

## Does NOT close
Does NOT promote amphora-barrier-corrosion-score to VALIDATED (governance-gated).
Does NOT change the manifest (66 receipts / 11 modules). Does NOT modify the shipped
Rust engine or any of the 66 signed receipts. Reported D magnitudes and the 250 um
DFT are REFERENCE_NOMINAL; only the exact identities and the real-M_inf permeance
ranking are defended.
