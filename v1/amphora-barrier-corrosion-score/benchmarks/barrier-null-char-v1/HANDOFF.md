# barrier-null-char-v1 — named-baseline + hostile-null characterization

**Date:** 2026-07-26 · host: xbabe2 (canonical) · authority: **AUDIT_ONLY**

## What this is
The first **correct-scope** (organic epoxy-amine coating-barrier EIS) science
increment for `amphora-barrier-corrosion-score`. The prior `corr-rate-qspr-v1`
diagnostic was *bare-substrate* corrosion (scope mismatch). This one works on the
only two strict, in-class, open-table-read, ordered EIS coating-resistance series
in the tree — `asperti2024` and `zhu2022`, both MDPI *Materials* (CC BY 4.0) —
respecting their declared use_limit (within-study direction only; NO cross-study pooling).

## Two results
1. **Named published baseline** — Bacon–Smith–Rugg (1948) electrolytic-resistance
   protective-merit tiers (Ind. Eng. Chem. 40(1) 161–167, DOI 10.1021/ie50457a041):
   GOOD >=1e8, INTERMEDIATE 1e6–1e8, POOR <1e6 ohm.cm2. Applied per level.
   Asperti@1000h: [INTERMEDIATE, GOOD, POOR, GOOD]; Zhu@60h: all GOOD.
2. **Hostile-null characterization** — within a single-resin filler-loading ladder
   the solids-only and PVC-only nulls both collapse to one monotone-in-loading
   prediction. Measured vs observed Rc ranking:
   - Asperti: Spearman rho=0.0, exact perm p=1.0 (optimum at 1 wt%).
   - Zhu: Spearman rho=0.4, exact perm p=0.517 (optimum at 0.7 wt%).
   Neither significant; the monotone null reproduces neither series' optimum.

## Honest verdict
Establishes and quantifies non-trivial ranking headroom for a barrier-aware score
(a necessary precondition for the module's falsifiable hypothesis). Does NOT
establish a validated positive barrier ranking model — no zero-parameter a-priori
model reproduces the intermediate optimum (dispersion/percolation, a formulation-
processing variable). Closing that needs >=3 pooled, protocol-controlled
formulation->Rc series with dispersion/PVC metadata — the standing DATA wall.

## Reproducibility
- stdlib-only, no random, no timestamp; two runs -> canonical SHA-256
  7db2952a9d59008c7def48b44caec633f7c2a84c3e135b75a47a2645626c5156 (byte-identical).
  TWO_REPLAY_GATE=PASS.
- DSSE Ed25519 signed with trust-anchored Phase-0 evaluator key
  phase0-evaluator-3ef6b35cdbbfea74, used AUDIT_ONLY: promotes_authority=false,
  modifies_manifest=false, no promotion ceremony. INDEPENDENT_VERIFY=PASS.

## Files
- barrier_null_char.py — deterministic benchmark
- result.{runA,runB,canonical}.json — two runs + canonical
- null_char_receipt.v1.dsse.json — signed receipt
