# Catoire–Naudet closed-cup FLASH POINT / GHS-category audit (AUDIT_ONLY)

**Benchmark:** `amphora-redteam-audit/catoire-flash-point-ghs-ccby-v1`
**Date:** 2026-07-26 · **Authority:** AUDIT_ONLY (`local-9028773f…`, LOCAL_DEVELOPMENT) · promotes nothing.
**Two-replay gate:** PASS (`551cb6b3…`, byte-identical) · **DSSE Ed25519:** VERIFIES.

## Red-team headline: is "FULL Phase-0" real? NO — and this run does not change it.
Live front-matter + promotion-policy reconciliation (embedded, byte-stable, in the signed
diagnostic) reads every module directly on disk. **17 modules are labelled `PHASE_0` = 13
`scientific_readiness = NOT_APPLICABLE` (governance/infra) + 4 `LOCKED_INTERNAL` (internal
known-answer only). ZERO carry `scientific_readiness = VALIDATED`.** A second independent
cross-check of **all 29 phase-0 promotion policies** confirms `scientific_success_required`
is **FALSE in 100 %** of them and **0 target `scientific_readiness = VALIDATED`** (the ceiling
every policy targets is `LOCKED_INTERNAL`). **"FULL Phase-0" is an engineering/governance
milestone — reproducibility + rights + independence locks — NOT a count of validated coating
science. The founder's skepticism is correct.** Exactly one module (`amphora-solvency-score`)
has any external-data predictive validation behind it. This audit does not touch that count.

## What this increment adds (the highest-value un-anchored axis remaining)
The **flash point** is the single most consequential safety/regulatory number on a marine
epoxy-amine coating's thinner/co-solvent package. It sets the **GHS flammable-liquid category**
on the label, the **IMDG / ADR dangerous-goods class** for shipping the paint, and on-site
storage / hot-work controls — and it is the primary flammability gate the sourceability/EHS
lane must honour.

The tree already anchors the two **thermodynamic drivers** of the flash point:
- **Boiling point** — Joback boiling-point audit (volatility axis).
- **Enthalpy of vaporization** — Joback ΔHvap audit (cohesive-energy / latent-heat axis).

…but nothing previously turned those into the flash point / GHS class a formulator and a
shipping desk act on. **This audit is the capstone that closes that loop:** it consumes the two
already-anchored properties (Tb, ΔHvap) plus the exact carbon count and predicts a NEW property
no other module supplies.

## Theory (real, cited, non-circular)
- **Predictor:** Catoire, L.; Naudet, V. *J. Phys. Chem. Ref. Data* **2004**, 33(4), 1083–1111 —
  a single power-law equation for the closed-cup flash point:
  **FP = 1.477 · Tb^0.79686 · ΔHvap298^0.16845 · nC^(−0.05948)** (FP, Tb in K; ΔHvap298 in kJ/mol;
  nC = carbon count). The four constants were regressed on a **separate 59-compound set** and are
  **universal published constants — NOT re-fit to this panel → non-circular by construction.**
  Reported accuracy of the original correlation: **MAD ≈ 2.9 K, max ≈ 7 K.**
- **Ground truth:** independent experimental **closed-cup** flash points (GESTIS / CRC / PubChem /
  EC 440/2008 A.9 regulatory values). Flash point is method-dependent (closed-cup values scatter
  ~±2–4 K between sources); this uncertainty is declared, and the graded metric is a **discrete GHS
  category + a Kelvin MAE benchmarked to Catoire's own ~2.9 K**, not a spurious sub-1 % MAPE.
- **Trust guards:** (1) every Joback group multiset is **formula-checked vs RDKit** and is
  byte-identical to the boiling-point / ΔHvap audits; (2) **self-consistency triangulation** —
  feeding independent experimental Tb and ΔHvap298 and recovering the independent experimental FP
  to a few K cross-validates the thermodynamic inputs themselves.

## Result — 18 in-scope marine epoxy-amine solvents (13 core non-associating + 5 alcohol boundary)
| KPI (Track A = Catoire with experimental Tb + ΔHvap298) | CORE (n=13) | value |
|---|---|---|
| **Flash-point MAE** | | **2.34 K** (Catoire ref ≈ 2.9 K) |
| max abs error | ethyl acetate | 4.68 K (ref ≈ 7 K) |
| within ±5 K | | **13 / 13 (100 %)** |
| **lift over mean-FP null** | | **84.4 %** |
| **Spearman (flammability order)** | | **0.989** |
| **GHS category exact match** | | **11 / 13** (both misses boundary-adjacent, see below) |
| alcohols (boundary) MAE | n=5 | **1.24 K**, 5/5 within ±3 K, Spearman 1.0 |

**Verdict: `VALIDATED_IN_DOMAIN` (gate PASSED)** — gate = MAE ≤ 5 K **and** max ≤ 8 K **and**
≥(n−2) within ±5 K **and** GHS match ≥ 80 % **and** Spearman ≥ 0.95 **and** lift ≥ 60 %.

**Track B (fully a-priori — boiling point replaced by its Joback structure-only prediction, the
novel-molecule path):** core MAE **3.97 K**, 12/13 within ±8 K, Spearman 0.973 — realistic
accuracy for a solvent with **no measured Tb**. (ΔHvap298 is itself anchored, so a fully
structure-only path exists; Track B substitutes experimental ΔHvap298 to isolate the dominant
boiling-point term, exponent 0.797.)

### Per-solvent (Track A)
| solvent | nC | Tb (K) | ΔHvap298 | FP_exp °C | FP_pred °C | err (K) | GHS exp→pred |
|---|---|---|---|---|---|---|---|
| benzene | 6 | 353.24 | 33.83 | −11 | −15.4 | −4.4 | Cat2→Cat2 ✓ |
| toluene | 7 | 383.75 | 38.06 | 4 | 5.1 | +1.1 | Cat2→Cat2 ✓ |
| o-xylene | 8 | 417.58 | 43.43 | 32 | 28.8 | −3.2 | Cat3→Cat3 ✓ |
| p-xylene | 8 | 411.51 | 42.40 | 27 | 24.1 | −2.9 | Cat3→Cat3 ✓ |
| ethylbenzene | 8 | 409.35 | 42.24 | 23 | 22.7 | −0.4 | Cat3→Cat2 ✗ (boundary) |
| n-hexane | 6 | 341.88 | 31.55 | −22 | −25.0 | −3.0 | Cat2→Cat2 ✓ |
| n-heptane | 7 | 371.57 | 36.57 | −4 | −3.8 | +0.2 | Cat2→Cat2 ✓ |
| cyclohexane | 6 | 353.87 | 33.01 | −18 | −16.1 | +1.9 | Cat2→Cat2 ✓ |
| acetone | 3 | 329.20 | 31.30 | −18 | −22.6 | −4.5 | Cat2→Cat2 ✓ |
| MEK | 4 | 352.79 | 34.79 | −6 | −8.2 | −2.2 | Cat2→Cat2 ✓ |
| MIBK | 6 | 389.65 | 40.60 | 14 | 14.2 | +0.2 | Cat2→Cat2 ✓ |
| ethyl acetate | 4 | 350.21 | 35.60 | −4 | −8.7 | −4.7 | Cat2→Cat2 ✓ |
| n-butyl acetate | 6 | 399.15 | 43.86 | 22 | 23.6 | +1.6 | Cat2→Cat3 ✗ (boundary) |
| methanol* | 1 | 337.70 | 37.43 | 11 | 8.2 | −2.8 | Cat2→Cat2 ✓ |
| ethanol* | 2 | 351.44 | 42.32 | 13 | 11.4 | −1.6 | Cat2→Cat2 ✓ |
| 1-propanol* | 3 | 370.35 | 47.50 | 22 | 22.2 | +0.2 | Cat2→Cat2 ✓ |
| 2-propanol* | 3 | 355.41 | 45.39 | 12 | 10.4 | −1.6 | Cat2→Cat2 ✓ |
| 1-butanol* | 4 | 390.87 | 52.35 | 35 | 34.9 | −0.1 | Cat3→Cat3 ✓ |

\* alcohol boundary set.

### The two GHS misses are honest, not hidden
Both misses (ethylbenzene, n-butyl acetate) are solvents whose **experimental** closed-cup FP sits
**within ~2 K of the 23 °C Cat2/Cat3 boundary**, and whose literature FP **straddles** that line
(ethylbenzene: EC 440/2008 A.9 = 23 °C, some SDS 15–21 °C; n-butyl acetate: 22–27 °C across
sources). The predicted FP is within truth uncertainty of the threshold, and no miss crosses more
than one category or the flammable/combustible 60 °C line.

## Honest limitations
- Flash point is a method-dependent apparatus quantity (± a few K, closed vs open cup); the graded
  metric is a discrete GHS class + Kelvin MAE, not a false-precision MAPE.
- Catoire is a **pure-component** correlation; a real solvent **blend** flash point is governed by
  the most volatile component's partial pressure (non-ideal, activity-coefficient) — a Phase-1
  extension, not claimed here.
- Isomers with identical Joback first-order groups (o- vs p-xylene) share the Track B Joback Tb;
  Track A uses their distinct experimental Tb and resolves them.
- All panel solvents are inside the stated Catoire validity box (Tb 250–650 K, ΔHvap 20–110 kJ/mol,
  nC 1–21).

## What this does NOT do
Does **not** promote any module to PHASE_0 or change any `scientific_readiness`; does **not** modify
any of the 66 signed receipts or the receipts manifest (verified still **66 / 11**); does **not**
assert independence or human review; does **not** re-fit the Catoire constants; AUDIT_ONLY key
custody only. **The founder's "FULL Phase-0" skepticism is confirmed by this run.**

## Reproduce
```
cd /home/ubuntu/amphora/build/mvp20-split
B=amphora-redteam-audit/benchmarks/catoire-flash-point-ghs-ccby-v1
python3 $B/catoire_flash_point_ghs_audit.py /tmp/replay.json   # sha256 == 551cb6b3…
python3 $B/sign_catoire_flash_point_ghs.py                     # DSSE Ed25519 verifies
```
