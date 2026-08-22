# owk-adhesion-and-phase0-redteam-v1 (AUDIT_ONLY)

Two-part red-team increment. Deterministic, two-replay byte-stable, signed with
the repo `LOCAL_DEVELOPMENT_AUDIT_ONLY` Ed25519 key (NOT trust-anchored).
Promotes nothing; touches no existing receipt, the manifest, or any governance
artifact. Canonical diagnostic SHA-256
`27a7edcfd5955c19e29daf64dd7101ebe22d17fbf9739c2ad29b92d245caeab5`.

## PART A — Phase-0 honesty red-team (founder-facing), recomputed LIVE
Refutes the equivalence "FULL Phase-0" == "validated science":
- `scientific_readiness == VALIDATED` for **0 / 29** modules.
- The 10 modules labelled PHASE_0 = **7 NOT_APPLICABLE** (pure governance/infra,
  no science object) + **3 LOCKED_INTERNAL** (`process-qc-twin`,
  `solvency-score`, `tolerance-robustness`). Even the crown-jewel
  `solvency-score` is LOCKED_INTERNAL, not externally VALIDATED.
- `scientific_success_required_for_phase0 == false` in **all 29** canonical
  benchmark-locks → Phase-0 is a **governance** gate.
- 19 PRE_PHASE_0 blocker taxonomy: **6 data-rights-walled**, **4
  benchmark-not-executed**, **9 eval-binding-mismatch**.
- Founder answer: this autonomous cron **cannot** move any module PRE→PHASE_0.
  Promotion needs two distinct trusted human-key signatures on a module-local
  movement event; the cron holds only the AUDIT_ONLY key.
All counts are computed at runtime from `config/program/phase0-decision-report.v2.json`
(sha `9467b627…`), `module-manifest.json` (sha `571813ee…`), and the 29
`*/evidence/phase0/benchmark/benchmark-lock.v1.json` files, so the map cannot go stale.

## PART B — real new science: the ADHESION axis engine
Opens the third coating "big three" property (barrier + Tg + **adhesion**).
Fowkes / Owens-Wendt-Kaelble dispersive geometric-mean combining rule
`γ₁₂ = γ₁ + γ₂ − 2√(γ₁ᵈ·γ₂ᵈ)` validated on the public-domain Fowkes (1964)
water/n-alkane interfacial-tension dataset:
- Recovered `γ_wᵈ = 21.96 ± 0.63 mN/m` across 7 aliphatics (literature 21.8).
- **Non-circular leave-one-out** interfacial-tension **MAPE 1.04 %** (MAE 0.53,
  max 1.42 mN/m).
- **Positive control**: benzene / toluene / CCl₄ correctly rejected at >3σ
  (π/induced-dipole interactions violate the pure-dispersive rule).
- In-scope application: Young–Dupré water work of adhesion **107.2 mN/m** on a
  cured DGEBA+DDS marine epoxy from a CC BY 4.0 contact angle (61.77°,
  MDPI Polymers 2024 16(1)67 = PMC10780492).

**Honest limit:** the coating solid-surface-energy capstone (multi-liquid OWK
inversion → γ_sᵈ/γ_sᵖ → predict a held-out liquid's contact angle) is
**data-rights-blocked** — this run's sweep found only single-liquid (water)
contact angles in CC-licensed DGEBA-amine sources. Adhesion is rights-walled
exactly like Tg.

## Reproduce
```
python3 owk_phase0_audit.py diagnostic.canonical.json
python3 owk_phase0_audit.py diagnostic.runB.json   # identical bytes
python3 sign_owk_phase0.py                          # re-sign (asserts two-replay)
```
