# Cohesive-energy / Hildebrand-solubility-parameter Fedors audit (AUDIT_ONLY)

**Benchmark:** `amphora-redteam-audit/cohesive-energy-hildebrand-fedors-ccby-v1`
**Date:** 2026-07-25 · **Authority:** AUDIT_ONLY (`local-9028773f…`, LOCAL_DEVELOPMENT) · promotes nothing.
**Two-replay gate:** PASS (`bb9e2596…`, byte-identical) · **DSSE Ed25519:** VERIFIES.

## Red-team headline: is "FULL Phase-0" real? NO — and this run does not change it.
Live front-matter reconciliation (embedded, byte-stable, in the signed diagnostic) reads every
module's `docs/mission.md`. **16 modules are labelled `PHASE_0`, and every one is
`scientific_readiness = NOT_APPLICABLE` (governance/infra) or `LOCKED_INTERNAL`
(internal known-answer only). ZERO are `VALIDATED`.** Even `amphora-solvency-score` — the single
module with genuine external-data predictive validation behind it — still carries
`scientific_readiness = LOCKED_INTERNAL`, not `VALIDATED`. **"FULL Phase-0" is an
engineering/governance milestone (reproducibility + rights + independence locks), NOT a count of
validated coating science.** The founder's skepticism is correct.

## What this increment adds (highest-value un-anchored gap)
The **Hildebrand solubility parameter δ = √(CED)** and its Hansen decomposition are the single
most-used framework for solvent selection, resin/hardener/pigment compatibility, and solvent-blend
design in two-part epoxy-amine coatings — and the **direct input to the crown-jewel
`amphora-solvency-score` (Hansen-distance) module, which today only *looks up* measured δ and has no
a-priori path for a novel molecule.** No existing receipt anchors an a-priori δ/CED predictor; the
only prior CED model in the tree is scored on **CONTEXT_ONLY quarantined polyverse data** (must carry
no KPI). This audit supplies the missing a-priori capability, **rights-clean.**

## Theory (real, cited, non-circular)
- **Ground truth (calorimetric):** δ_ref = √((ΔHvap(298 K) − RT)/Vm), Vm = M/ρ. ΔHvap, M, ρ are
  tabulated CRC/NIST physical constants (non-copyrightable facts).
- **Predictor:** Fedors (1974) additive group cohesive energy E_coh = Σ nᵢ·deᵢ (Van Krevelen,
  *Properties of Polymers*, ch.7). The deᵢ are **universal literature constants, NOT fitted to this
  set → non-circular.** δ_pred = √(E_coh/Vm).
- **Trust design:** predictor and reference share the **measured** Vm, so the test isolates the group
  cohesive-energy sum against the calorimetric cohesive energy (ΔHvap−RT) — **no dependence on any
  uncertain group-*volume* increment.** A second, independent group method (Hoftyzer–Van Krevelen
  partial parameters) supplies δd/δp/δh.

## Result (20 solvents = marine epoxy-amine thinner / co-solvent chemistries)
| KPI (core = aliphatic·cyclic·aromatic·alcohol·ketone·ester, n=17) | value |
|---|---|
| **core-domain δ MAPE** | **1.48 %** |
| core δ RMSE | 0.38 MPa^0.5 |
| core cohesive-energy MAPE | 2.99 % |
| **core lift over mean-δ null** | **89.5 %** |
| core within ±5 % | **100 %** |
| core within ±3 % | 82.4 % |
| core worst case | n-butyl-acetate, 4.9 % |
| **graded outcome** | **VALIDATED_IN_DOMAIN** |

**Three independent trust checks (this is why the number is believable):**
1. **Independent-method corroboration** — Fedors δ vs Hoftyzer–Van Krevelen δ_total agree to **3.6 %**
   on core. Two unrelated group tables landing together is hard to fake by transcription error.
2. **Reference integrity** — the calorimetric δ_ref (from ΔHvap) matches the *independent* literature
   Hansen totals to **0.9 %**. Our reference data is real, not invented.
3. **Secondary HVK dispersion** — δd (the well-behaved HSP component) matches literature Hansen δd to
   **3.2 %**. (δp/δh are only directional — the known group-contribution limit, disclosed.)

Per-family δ MAPE: aliphatic 0.08 %, cyclic 0.23 %, alcohol 0.61 %, aromatic 1.37 %, ketone 2.26 %,
ester 4.37 %. **H-bonding alcohols are IN-domain here** (cohesive energy captures the OH increment).

## Honest applicability boundary (reported, not hidden)
- **styrene** (1.0 %) and **chlorobenzene** (6.3 %) sit outside the core validated increment set —
  extended vinyl–aryl conjugation and the aromatic-halogen cohesive increment (carried at the
  aliphatic-Cl value). Reported as boundary cases.
- **water** is excluded from the group predictor (no organic-group decomposition) but retained for the
  calorimetric reference (δ_ref ≈ 47.8, matching literature to <1 %).

## Coating relevance
δ and its Hansen decomposition gate **solvent-blend design, resin/hardener miscibility, pigment
wetting, and coalescent selection**. An a-priori δ predictor lets the solvency engine screen **novel**
candidates with no measured ΔHvap — the actual capability gap — and gives a rights-clean replacement
for the quarantined polyverse CED model.

## Trust / governance
- Two-replay SHA-256 gate **PASS** (`diagnostic.canonical.json` == `diagnostic.runB.json`, `bb9e2596…`).
- DSSE Ed25519 signature **verifies** (AUDIT_ONLY key). RDKit 2026.03.2 pinned; env reproduces the
  prior refractive-index diagnostic byte-for-byte.
- **Manifest + all 66 receipts untouched. No PHASE_0 added; no `scientific_readiness` changed.**

## Honest limitations
Pure-liquid δ at 25 °C (not the cured-network δ — a Phase-1 repeat-unit extension); predictor uses the
*measured* Vm (a fully a-priori δ chains a group molar-volume, e.g. the anchored solvency Fedors
engine); HVK δp/δh are directional only. Promotion to real Phase-0 remains gated on a **keyed
supersession** by a human trust-anchored key — this AUDIT_ONLY increment deliberately does not, and
cannot, perform it.
