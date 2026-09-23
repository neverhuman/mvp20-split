# Joback enthalpy-of-vaporization anchor — AUDIT_ONLY red-team science increment
`amphora-redteam-audit/benchmarks/joback-heat-of-vaporization-ccby-v1` · 2026-07-25 · xbabe2

## Red-team of the "FULL Phase-0" claim (verified live this run)
The founder's skepticism is **correct**. "FULL Phase-0" is a **governance** milestone, not
validated science. Verified live, two independent ways, embedded byte-stable in the signed
diagnostic:
- **Live front-matter:** 17 modules labelled `phase=PHASE_0` = **13 `NOT_APPLICABLE`**
  (governance/infra) + **4 `LOCKED_INTERNAL`** (internal known-answer only). **ZERO** carry
  `scientific_readiness=VALIDATED`.
- **Live promotion policies:** `scientific_success_required` is **`false` in 100%** of the
  29 phase0 promotion policies, and none target `VALIDATED` (ceiling is `LOCKED_INTERNAL`).
- Exactly **1** module (`amphora-solvency-score`) has any external-data predictive validation.

This audit **promotes nothing** and does **not** change that count. It adds one more
rights-clean, externally-validated a-priori science anchor to the audit trail.

## What is new (the highest-value un-anchored physics gap)
An a-priori predictor of the **enthalpy of vaporization at the normal boiling point,
ΔHvap(Tb)** — the single thermodynamic quantity that **drives both** already-anchored
solvent-design axes of a marine two-part epoxy-amine coating solvent package:

| Axis | Governed by ΔHvap via | Prior anchor |
|---|---|---|
| **Volatility** / flash-off / evaporation balance | Clausius–Clapeyron (vapour pressure ∝ ΔHvap) | Joback boiling-point audit |
| **Solubility** / solvency | cohesive energy `E_coh = ΔHvap − RT` → Hildebrand δ = √(E_coh/V) | Fedors cohesive-energy audit → `amphora-solvency-score` |

Nothing in the tree previously predicted ΔHvap for a **novel** solvent / reactive diluent
with no measured latent heat. This supplies it, via a **third, independent** group-contribution
method — so it is also a cross-method consistency check on the cohesive energy the Fedors δ
anchor estimates a different way.

## Theory (real, cited, non-circular)
- **Predictor:** Joback & Reid 1987 first-order group contribution,
  `ΔHvap(Tb) = 15.30 kJ/mol + Σ nᵢ·hvkᵢ`. The `hvkᵢ` are universal published constants
  (Poling/Prausnitz/O'Connell 5th ed., Table C-1), **not fitted** to this panel.
- **Ground truth:** NIST Chemistry WebBook experimental ΔHvap measured **at Tb**, from the
  **Majer & Svoboda 1985** critical compilation (public domain). One **consistent at-Tb basis**
  — values "corrected to 298.15 K" were deliberately rejected (Joback's increments are defined
  at Tb; mixing bases would be a silent error). Each of the 18 truth values was individually
  pulled from the NIST WebBook this run and confirmed to be an at-boiling-point datum.
- **Trust guard:** every hand-encoded Joback group multiset is formula-checked against RDKit
  (C,H,O) — a miscount cannot pass; the group encoding is byte-identical to the boiling-point
  audit for shared solvents.

## Result — `VALIDATED_IN_DOMAIN` (gate passed)
Gate: CORE MAPE ≤ 2.5% **and** 100% within ±5% **and** lift ≥ 60% **and** Spearman ≥ 0.95,
graded on the **CORE non-associating set only** (conservative).

| KPI (CORE, n=13) | value |
|---|---|
| ΔHvap(Tb) MAPE | **0.777 %** |
| within ±3 % | **13/13** |
| worst | mibk, 2.37 % |
| lift over mean-null | **86.1 %** |
| Spearman (order) | **0.989** |

Per-family MAPE: ester 0.16 %, aromatic 0.76 %, cyclic 0.94 %, ketone 0.94 %, aliphatic 1.11 %.
**Honest boundary:** the 5 H-bonding alcohols (methanol / ethanol / 1-,2-propanol / 1-butanol)
under-predict by a mean of **−1.69 kJ/mol (4.18 % MAPE)** — O–H···O association energy is not
additive at first order — and are declared boundary/out a priori (same domain edge as the δ /
boiling-point anchors). **Cyclohexanone** (in the shared panel) is **excluded here** because
NIST has no unambiguous single at-Tb datum for it (only a 298 K-corrected and a mid-range
value) and it is a known cyclic-ketone Joback outlier — logged, not silently dropped.

## Provenance
- Two-replay SHA-256 gate: **PASS** — `canonical == runB == 19d9be63…e189c7b`
- DSSE Ed25519 signature: **VALID**, key `local-9028773f49591193` (`LOCAL_DEVELOPMENT_AUDIT_ONLY`,
  **not** trust-anchored in the phase0 store)
- Receipt body sha256 `60e41461…95ce2ae3` · envelope sha256 `579ae191…13175090`

## Does NOT
Promote any module to PHASE_0; change any `scientific_readiness`; modify any of the 66 signed
receipts or the receipts manifest (verified still 66/11); assert independence / human review;
apply any fitted or Watson temperature correction; perform PHASE0 evaluator/reviewer signing.
