# Refractive-index Lorentz–Lorenz group-contribution audit (AUDIT_ONLY)

**Benchmark:** `amphora-redteam-audit/refractive-index-lorentz-lorenz-ccby-v1`
**Date:** 2026-07-25 · **Authority:** AUDIT_ONLY (`local-9028773f…`, LOCAL_DEVELOPMENT) · promotes nothing.

## What this is
First rights-clean, **a-priori** validation of a **refractive-index** predictor for the coating
portfolio — a property not previously covered by any of the 66 signed receipts. Complements the
surface-tension Parachor audit (same 20-solvent panel, same M/ρ).

## Theory (real, cited, non-circular)
Lorentz–Lorenz (1880):  (n²−1)/(n²+2) = R_LL·ρ/M, with molar refraction **R_LL an additive sum of
Eisenlohr/Vogel atomic + bond refractions** (Van Krevelen, *Properties of Polymers*, ch.10).
→ `n_pred = sqrt((1+2f)/(1−f))`, `f = R_LL·ρ/M`. The refraction constants are **universal literature
values, NOT fitted to the validation set → non-circular by construction.** RDKit classifies each O as
hydroxyl/ether/carbonyl by bonding; C=O is carried by the carbonyl-O increment (not double-counted).

## Data (rights-clean, in-scope)
20 pure liquids = exact chemistries of two-part marine epoxy-amine thinner packages (aromatics,
aliphatics, alcohols, ketones, esters) + water. `n_D20`, `ρ_20C`, `M` are tabulated CRC/NIST physical
constants (non-copyrightable facts); compilation self-authored CC0.

## Result
| KPI (core = non-extended-conjugation, n=19) | value |
|---|---|
| core-domain MAPE | **0.158 %** |
| core RMSE (n units) | **0.0031** |
| core lift over mean-n null | **96.1 %** |
| core within ±0.005 n | 89.5 % |
| core within ±0.002 n | 63.2 % |
| worst core case | p-xylene, 0.5 % |
| **graded outcome** | **VALIDATED_IN_DOMAIN** |

Unlike Parachor, **alcohols and water are IN-domain** (RI is an electronic-polarizability property).
The single out-of-domain case is **styrene (−1.6 %)** — the known optical **exaltation of extended
conjugation** the additive scheme omits; reported, not hidden.

## Coating relevance
RI governs **hiding power / opacity** (via pigment-vs-binder RI contrast, e.g. TiO₂ n≈2.7 vs epoxy
n≈1.55), gloss, and is the standard **refractometric incoming-QC fingerprint** of resin/solvent
identity & purity. R_LL is also the electronic-polarization term of Clausius–Mossotti (n² ≈ high-freq
permittivity), linking RI to film barrier/water-uptake physics.

## Trust
- Two-replay SHA-256 gate **PASS** — byte-identical `diagnostic.canonical.json` == `diagnostic.runB.json`
  (`f35b4532…`).
- DSSE Ed25519 signature **verifies** (AUDIT_ONLY key). RDKit 2026.03.2 pinned.
- **Manifest + all 66 receipts untouched.** No PHASE_0 added. Embedded live-front-matter Phase-0
  reconciliation re-verified: 17 labelled = 13 NOT_APPLICABLE + 4 LOCKED_INTERNAL; exactly **1**
  externally-validated science module (solvency).

## Honest limitations
Pure-liquid n_D at 20 °C only (not cured-film RI); requires a measured ρ (an all-a-priori path chains
Fedors molar volume → Phase-1); Eisenlohr is one refraction table (alt. sets shift <0.5 %).
