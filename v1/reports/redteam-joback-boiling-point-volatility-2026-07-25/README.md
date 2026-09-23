# Joback normal-boiling-point / solvent-volatility audit (AUDIT_ONLY)

**Benchmark:** `amphora-redteam-audit/joback-boiling-point-volatility-ccby-v1`
**Date:** 2026-07-25 · **Authority:** AUDIT_ONLY (`local-9028773f…`, LOCAL_DEVELOPMENT) · promotes nothing.
**Two-replay gate:** PASS (`4cde6e0b…`, byte-identical) · **DSSE Ed25519:** VERIFIES.

## Red-team headline: is "FULL Phase-0" real? NO — and this run does not change it.
Live front-matter reconciliation (embedded, byte-stable, in the signed diagnostic) reads every
module's `docs/mission.md`. **17 modules are labelled `PHASE_0` = 13 `scientific_readiness =
NOT_APPLICABLE` (governance/infra) + 4 `LOCKED_INTERNAL` (internal known-answer only). ZERO carry
`scientific_readiness = VALIDATED`.** Even `amphora-solvency-score` — the single module with genuine
external-data predictive validation behind it — is still `LOCKED_INTERNAL`, not `VALIDATED`. **"FULL
Phase-0" is an engineering/governance milestone (reproducibility + rights + independence locks), NOT
a count of validated coating science. The founder's skepticism is correct.**

## What this increment adds (the highest-value un-anchored gap this run)
A coating solvent/co-solvent package is designed on **exactly two axes: solubility and volatility.**
- **Solubility** is now anchored — Hildebrand/Hansen **δ** (Fedors audit) → crown-jewel `amphora-solvency-score`.
- **Volatility** had **no a-priori anchor anywhere in the tree.** Nothing predicted the boiling point /
  evaporation ordering of a **novel** solvent or reactive diluent with no measured Tb. Volatility governs
  **VOC compliance, film-formation / flash-off, wet-edge & sag control, fast/medium/slow evaporation
  balancing in a blend, and is a first-order flash-point proxy.**

This audit supplies that missing companion capability, rights-clean, and it **pairs 1:1 with the δ
anchor** to make solvent selection a two-property a-priori screen.

## Theory (real, cited, non-circular)
- **Predictor:** Joback & Reid (Chem. Eng. Commun. 1987, 57, 233; Poling/Prausnitz/O'Connell,
  *Properties of Gases and Liquids* 5th ed., Table C-1): `Tb = 198.2 K + Σ nᵢ·tbkᵢ`. The tbkᵢ are
  **universal published constants, NOT fitted to this panel → non-circular by construction.**
- **Ground truth:** NIST Chemistry WebBook experimental normal boiling points (**U.S. Government work,
  public domain**).
- **Trust guard:** every hand-encoded Joback group multiset carries an explicit (C,H,O) atom
  composition, and its weighted sum **must reproduce the exact RDKit molecular formula** — a miscount
  cannot pass. Asserted for all 19 solvents.
- **Operational KPI:** beyond point accuracy we report the **Spearman rank correlation** of predicted
  vs experimental Tb — the fidelity of the fast/medium/slow evaporation **order** a blend is actually
  designed on.

## Result (19 in-scope marine epoxy-amine thinner / co-solvent chemistries)
| KPI (core = all except methanol, n=18) | value |
|---|---|
| **core Tb MAPE** | **1.448 %** |
| core Tb RMSE | ≈ 6.4 K |
| core within ±5 % | **18 / 18 (100 %)** |
| core within ±3 % | 16 / 18 |
| core worst case | ethanol, 3.96 % |
| **core lift over mean-Tb null** | **77.0 %** |
| **Spearman evap-order (core)** | **0.967** (gated ≥ 0.95) |
| Spearman evap-order (all 19) | 0.970 |
| pair concordance | **161 / 171 (94.2 %)** |
| **graded outcome** | **VALIDATED_IN_DOMAIN** |

Per-family Tb MAPE: ester 0.63 %, aromatic 0.74 %, ketone 1.14 %, cyclic 2.04 %, aliphatic 2.32 %,
alcohol 2.46 %. Standouts: **cyclohexanone 0.04 %, MIBK 0.17 %, ethylbenzene 0.008 %, ethyl-acetate 0.25 %.**

**Gate (conservative):** `core_tb_MAPE ≤ 2.5 % AND 100 % within ±5 % AND lift ≥ 60 % AND
spearman(core) ≥ 0.95`. Gated on the **core** set, not the more-favourable all-modeled set.

## Honest applicability boundary (reported, not hidden)
- **methanol** is **out-of-domain a priori** — the smallest, most strongly self-associating alcohol;
  first-order groups miss C1-alcohol H-bonding (6.8 % under-prediction).
- **ethanol (3.96 %)** and **n-heptane (3.18 %)** are honest boundary cases (Joback under-predicts small
  H-bonding alcohols and n-alkanes).
- **Evaporation order is near-perfect but not perfect:** only **10 / 171 pairs** invert, and they invert
  between solvents that are operationally the same volatility class — the largest is n-heptane vs
  cyclohexane at a **17.7 K** true gap (the alkane family Joback under-predicts); most inversions are
  1–3 K. All ten pairs are enumerated in the signed diagnostic (`kpis.discordant_pairs`).

## Coating relevance
Volatility gates **VOC compliance, evaporation-rate balancing, flash-off, sag/wet-edge, and flash-point
screening.** An a-priori Tb predictor lets the formulation engine rank the **fast/medium/slow** class of
a novel solvent with no measured boiling point, and — combined with the anchored Hansen-δ engine —
turns solvent selection into a genuine two-property (solubility + volatility) a-priori screen.

## Trust / governance
- Two-replay SHA-256 gate **PASS** (`diagnostic.canonical.json` == `diagnostic.runB.json`, `4cde6e0b…`).
- DSSE Ed25519 signature **verifies** (AUDIT_ONLY key, `trust_anchored_in_phase0_store = false`).
  RDKit 2026.03.2 pinned.
- **Manifest + all 66 receipts untouched. No PHASE_0 added; no `scientific_readiness` changed.**

## Honest limitations
Pure-component Tb at 1 atm — a real coating **blend** evaporates non-ideally (Raoult/activity +
boundary-layer), so Tb gives the pure-component ordering, not the true blend flash-off curve (a Phase-1
activity-coefficient extension). No fitted Tb correction is applied (it would break non-circularity).
Promotion to real Phase-0 remains gated on a **keyed supersession by a human trust-anchored key** —
this AUDIT_ONLY increment deliberately does not, and cannot, perform it.
