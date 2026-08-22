# wet-adhesion-surface-energetics-ccby-v1 (AUDIT_ONLY)

Autonomous red-team increment. Signed with LOCAL_DEVELOPMENT_AUDIT_ONLY key
(local-9028773f...), NOT a trust-anchored phase0 key. Promotes nothing; modifies
no existing receipt or the manifest (still 66 receipts / 11 modules).

## (A) Phase-0 honesty red-team (recomputed live)
- scientific_readiness == VALIDATED for **0 / 29** modules.
- The 10 PHASE_0 modules = **7 NOT_APPLICABLE** (governance/infra) + **3 LOCKED_INTERNAL**;
  all 10 are decision_use_ceiling==AUDIT_ONLY, promotable==false.
- **29 / 29** benchmark-locks: scientific_success_required_for_phase0 == false.
- => "FULL Phase-0" is a GOVERNANCE state, NOT validated science. This cron cannot
  promote any module (needs two trusted-human-key sigs it does not hold).

## (B) New science: wet-adhesion / cathodic-disbondment surface energetics
Marine failure mode #1 (water displacing the coating<->steel bond). Distinct axis
from osmotic blistering (bulk uptake).

- Data: CC BY 4.0, PMC10780492 (Polymers 2024 16(1):67). Measured water contact
  angles: EP-DDS 61.77, EP-CYDM 75.03, EP-8CH2DA 78.64 deg.
- Parameter-free engine: Young-Dupre W_a(water) = gamma_w(1+cos theta), gamma_w=72.8.
  W_a: DDS 107.24 (reproduces signed OWK value), CYDM 91.61, 8CH2DA 87.14 mN/m.
- Non-circular a-priori predictor: total polar-atom density c_polar (mol/kg), taken
  VERBATIM from the signed barrier-water receipt (defined there for BULK uptake).

### Findings (n=3, not claimed significant)
- Spearman(c_polar, cos theta surface) = **+1.0** (perfect surface-wettability rank).
- Spearman(c_OH, cos theta) = -0.5 (hydroxyl-only is the WRONG surface descriptor;
  DDS surface polarity is the sulfone, captured only by c_polar).
- Spearman(surface cos theta, bulk uptake) = **-0.5**, and c_polar ANTI-ranks bulk
  uptake (-0.5, from signed barrier-water receipt).
  => **Surface (disbondment) and bulk (blistering) are DECOUPLED / different physics.**
- Cross-class positive control (canonical handbook polymers, rank-only): Spearman(
  delta_h, cos theta) = 1.0 -> engine valid at coarse resolution.

### Verdict
DIRECTION_VALIDATED_AND_DECOUPLED_FROM_BULK. Not promotable: n=3, and single probe
liquid gives only W_a(water), not the full polar/dispersive split (needs >=2 probe
liquids, protocol-controlled n>=~10). **Actionable for the founder report:** rank
cathodic-disbondment risk by SURFACE polar-group density, osmotic-blistering risk by
FREE VOLUME -- do NOT collapse them into one "hydrophilicity" number.

## Reproduce
```
python3 wet_adhesion_surface_energetics_audit.py diagnostic.canonical.json
python3 wet_adhesion_surface_energetics_audit.py /tmp/replay.json   # byte-identical
python3 sign_wet_adhesion.py
```
two-replay SHA256 = 8c575179c1ee882e24dc21e19d42a732948c0465537c3f58f7c4d1a458fcffd3
