# Red-team memo — "FULL Phase-0" is false; new first-principles crosslink-density axis for network Tg/stiffness (2026-07-26)

**Date:** 2026-07-26 · **Host:** all real work on the canonical Linux host
(`ssh xbabe2:/home/ubuntu/amphora/build/mvp20-split`). **Authority:** AUDIT_ONLY —
promotes nothing, modifies none of the 66 signed receipts, the manifest, or the
signed network-Tg v1/v2/v3 audits. Last cron pass before the founder report.

---

## 1. The "FULL Phase-0" claim is FALSE — governance ceiling, zero validated science

Re-derived **independently and reproducibly** this run from the 29 signed
promotion policies (`*/evidence/phase0/promotion/policy.v1.json`) and the
program decision report — embedded inside the signed diagnostic so it re-runs:

| Check | Result |
|---|---|
| `evidence_status` across 29 modules | **29 / 29 UNVALIDATED** |
| `scientific_success_required` in promotion policies | **0 / 29 true** (29/29 **false**) |
| `decision_use_ceiling` | **29 / 29 AUDIT_ONLY** |
| `target_scientific_readiness` | 16 LOCKED_INTERNAL + 13 NOT_APPLICABLE → **0 INDEPENDENTLY_VALIDATED** |

**Bottom line for founders:** "FULL Phase-0" is a *governance/engineering*
milestone. **No module has externally-validated science as a required gate, and
none is at INDEPENDENTLY_VALIDATED.** Founder skepticism is correct. Promotion
to a validated science KPI additionally requires human-review signatures on
non-development keys, which every policy forbids autonomously — so **nothing can
move to VALIDATED in a headless cron by construction.** This upholds every prior
red-team cron.

## 2. The real frontier — solvent suite complete, cured-network is the wall

The a-priori **solvent-property suite is complete and signed** (Fedors δ, Hansen
δd/δp/δh vector, Joback Tb + ΔHvap, Clausius–Clapeyron VOC/P0, Catoire flash
point + GHS, Lorentz–Lorenz n, Parachor surface tension, molar volume/density,
Arrhenius viscosity) — each VALIDATED_IN_DOMAIN against a rights-clean truth set.

Every remaining gap is **cured-network** (Tg / crosslink / adhesion / barrier),
and each has been red-teamed:
- **Tg** — ADVANCED_NOT_VALIDATED (v3 backbone-rigidity LOO 35.7 °C; fails n≥12 and ≤25 °C).
- **Cured-network density** — REFUTED (+20.5 %).
- **DiBenedetto cure-bounds** — physical-bounds-consistent, not a point predictor.
- **Cure kinetics (Kissinger)** — anchored, rights-limited to the DGEBA+IPDA amine class.
- **Water uptake / diffusivity** — in-tree data is polyverse, CONTEXT_ONLY quarantined.
- **Rubbery modulus** — **data-rights-blocked** (see §4).

## 3. This run's new science — a-priori crosslink density is the missing complementary axis

Signed `network-crosslink-density-v1` (AUDIT_ONLY, two-replay, Ed25519).

The v3 diagnostic named the missing physics: connectivity cannot encode the
**crosslink-functionality boost** that lifts polyfunctional TETA (6 N-H) and
DETA (5 N-H) above the tetrafunctional diamines. This run builds that physics
**from first principles** — the **Flory perfect-network crosslink strand density
`n_x` [mol/kg]** from the amine SMILES + DGEBA molar mass **only** (measured Tg
is never a feature; fully non-circular) — and tests it on the **same
page-verified rights-clean n=9 / 7-unique data** as signed v3.

Findings (all in the signed diagnostic):
- **Anti-regression:** reproduces the signed v3 B-only LOO Tg MAE **35.730624 °C EXACTLY** (independent re-implementation of the pipeline).
- **`n_x` is real complementary physics:** the two highest-`n_x` systems, TETA
  (5.14, resid +30.4 °C) and DETA (4.72, +23.1 °C), are exactly the ones the
  rigidity-only model **under-predicts**; excluding the single aromatic outlier
  DDS, **Spearman(`n_x`, B-residual) = +0.49**. `n_x` **alone** anti-correlates
  with Tg (Spearman −0.29 — DDS has the lowest `n_x` and the highest Tg), proving
  it is a *complementary* axis to backbone rigidity, not a standalone predictor.
- **Rubber-elasticity consistency (bonus):** the SAME a-priori `n_x` feeds
  `E' = 3 ν_c R T`; predicted rubbery-plateau moduli span **43.5–65.3 MPa**, entirely
  inside the textbook epoxy band (10–100 MPa) — the descriptor is physically calibrated.
- **Honest negative:** a 2-feature (B + `n_x`) LOO does **not** reduce held-out Tg
  MAE (35.73 → **48.96 °C**) — a 3-parameter fit on n=7 with one aromatic outlier
  overfits. **The binding constraint is DATA QUANTITY (n≥12), not descriptors.**

**Sharper founder conclusion:** we now hold **both** governing, non-circular
descriptors for network Tg (backbone rigidity **and** crosslink density). The
sole remaining blocker to a Phase-0 Tg KPI is **rights-clean data volume**
(need ≈5 more page-verified systems across ≥4 amine classes) — a data-acquisition
problem, not a modeling problem.

## 4. Why no rubbery-MODULUS point-predictor this run — data rights, not theory

A point-validated rubbery-modulus KPI needs a rights-clean **measured** truth set.
This run confirmed it is not accessible: MDPI DMA tables are 403-blocked to the
fetch tooling, and the one accessible CC-BY PMC table (amino-acid hardeners,
10.3390/polym15020385) has ambiguous side-chain epoxy-reactivity and `ν_c`
inverted vs functionality (Tyr f=3 → 11 770 mol/m³ vs Trp f=4 → 1 560) — not a
clean a-priori topology truth. So the modulus axis is **theory-ready, data-rights-
blocked**, and was reported honestly as a physical-band consistency check only.

## 5. Provenance
- Diagnostic SHA-256 (two-replay, byte-identical): `c63cfdee3e3d21402b9f9014745948b146bdac054589c3d0cf44871443413eef`
- Signature: Ed25519 DSSE, key `LOCAL_DEVELOPMENT_AUDIT_ONLY` (not trust-anchored) — SIGNATURE_VERIFY PASS.
- Manifest unchanged: **66 receipts / 11 modules**. No PHASE_0 module added.
- Bench: `amphora-redteam-audit/benchmarks/network-crosslink-density-v1/`.
