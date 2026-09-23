# RETRACTION INDEX — amphora-solvency-score

Append-only index of retracted or qualified claims. Refuting receipts and superseded artifacts are never modified; corrections land as new signed receipts.

## R-A10 — mission.md prose consistency + W7 disclosure (2026-08-03)

Repair receipt: `amphora-solvency-score/evidence/phase0/repairs/R-A10/done/r-a10-prose-consistency-w7-disclosure-repair-receipt.v1.dsse.json` (repair_mode `interactive-2026-08-03`).

| claim | refuted-by receipt | superseded-by | date |
|---|---|---|---|
| "ML (HistGBM) beats classical Flory-Huggins theory" (KPI `evidence/phase0/kpis/omg-chi-flory-huggins-physical-baseline-vs-ml-kpi.v1.json`) — comparison void: delta_p to 5.2e9 MPa^0.5 vs 59.9 ceiling; B2 comparator degenerate (slope ~1e-19); valid classical baseline never run; fair re-run queued (R-B03/W7b) | `evidence/audit/flory-hansen-physical-admissibility-v1/flory-hansen-physical-admissibility-audit-receipt.v1.dsse.json` (W7, `CLAIM_REFUTED`) | `evidence/phase0/repairs/R-A10/done/r-a10-prose-consistency-w7-disclosure-repair-receipt.v1.dsse.json` | 2026-08-03 |
| "ML beats classical Hansen 1967/2007 3-component theory" (KPI `evidence/phase0/kpis/omg-chi-hansen-3component-physical-baseline-vs-ml-kpi.v1.json`) — comparison void: Hansen components to 5.33e17 MPa^0.5 vs 59.9 ceiling; rescaled comparator degenerate (slope ~1e-35); valid classical baseline never run; fair re-run queued (R-B03/W7b) | same W7 receipt | same R-A10 receipt | 2026-08-03 |
| mission.md prose "Operational state is SHADOW; scientific state is UNVALIDATED, so the current phase is Pre-Phase 0" (and the PRE_PHASE_0/SHADOW readiness passage) — contradicted the authoritative front-matter (PHASE_0 / LOCKED_INTERNAL / READY) | no refuting receipt — FOUNDER RULING 2026-08-03: front-matter is authoritative | same R-A10 receipt | 2026-08-03 |

Not a retraction: BigSolDB leave-solute-out headline RMSE 0.8770 stands; the W6
admissibility-hardened 0.8742 (`evidence/audit/hansen-hardened-validation-v1/bigsoldb-admissibility-hardened-lso-receipt.v1.dsse.json`)
is now cited alongside it in mission.md.

## R-B03 — corrected Flory–Huggins / Hansen group-contribution instrument (2026-08-03)

Repair receipt: `amphora-solvency-score/evidence/phase0/repairs/R-B03/done/flory-hansen-corrected-instrument-repair-receipt.v1.dsse.json` (repair_mode `interactive-2026-08-03`). Instrument repaired; the ML-vs-corrected-theory comparison is deliberately NOT run here — queued as W7b for the independent loop.

| claim | refuted-by receipt | superseded-by | date |
|---|---|---|---|
| Fedors 1974 delta_p behind `reference/mvp20/data/omg_chi_flory_huggins_physical_baseline_receipt.v1.json` (sha256 `87c49f22…`) is a valid classical-theory instrument — refuted: delta_p to 5.155e9 MPa^0.5 (envelope [9.6, 59.875]) via denominator collapse sum dV_i → 0 on silent zero-volume fragments; generator never committed | `evidence/audit/flory-hansen-physical-admissibility-v1/flory-hansen-physical-admissibility-audit-receipt.v1.dsse.json` (W7, `CLAIM_REFUTED`) | `evidence/phase0/repairs/R-B03/done/flory-hansen-corrected-instrument-repair-receipt.v1.dsse.json` — committed, tested instrument `benchmarks/flory-hansen-corrected-v1/compute_group_contribution.py` (explicit coverage → REJECTED, volume floor → ABSTAINED, envelope gate → ABSTAINED; seed-0 n=2500 OMG sample: zero out-of-envelope returns) | 2026-08-03 |
| Van Krevelen/Hoftyzer delta_d/delta_p/delta_h behind `reference/mvp20/data/omg_chi_hansen_3component_physical_baseline_receipt.v1.json` (sha256 `f56e179c…`) is a valid classical-theory instrument — refuted: components to 5.33e17 MPa^0.5 by the same defect | same W7 receipt | same R-B03 receipt | 2026-08-03 |
| Instrument-validity premise of KPI `evidence/phase0/kpis/omg-chi-flory-huggins-physical-baseline-vs-ml-kpi.v1.json` (sha256 `98b20b84…`) | same W7 receipt | same R-B03 receipt (KPI claim-scope retraction indexed under R-A10 above) | 2026-08-03 |
| Instrument-validity premise of KPI `evidence/phase0/kpis/omg-chi-hansen-3component-physical-baseline-vs-ml-kpi.v1.json` (sha256 `3950f643…`) | same W7 receipt | same R-B03 receipt (KPI claim-scope retraction indexed under R-A10 above) | 2026-08-03 |

## V1-SOLV — fair ML-vs-corrected-physics re-run, closing W7b (2026-08-04)

Repair receipt: `amphora-solvency-score/evidence/phase0/repairs/V1-SOLV/done/ml-vs-physics-corrected-comparison-receipt.v1.dsse.json` (sha256 `386a109b…`, repair_mode `campaign-2026-08-04`). Closes the W7b re-run R-B03 deliberately deferred: identical scaffold-safe 60/20/20 split (seed 0) and identical ML arm (HistGradientBoostingRegressor max_iter=500/lr=0.05/depth=8/min_leaf=25/l2=0.1, 528 features) as the two W7-refuted KPIs, with the R-B03 corrected instrument as the physics arm on a deterministic seed-0 n=40,000 OMG sample (scope-reduced from the original's full pool for single-hour synchronous compute; test n=5,261). Physics R² computed ONLY over instrument-RETURNED test molecules (coverage 85.5% Fedors/Hildebrand, 75.1% Hansen); abstentions/rejections excluded and counted, never zero-filled. Two-replay byte-identical (seed=0 throughout).

**Honest result: ML beats BOTH the pure (0-param) and rescaled (2-param) corrected-physics baselines in all 6 arms (3 solvents × {Hildebrand, Hansen-3-component}), on the identical covered-subset test molecules.** Unlike the W7-refuted run, the rescaled baseline is NOT degenerate in 5/6 arms (real positive R² up to 0.63, not collapsed to the constant predictor); the Hansen/ethanol arm is the one exception, rescaling to ~0 (b2_rescaled_r2 -0.013 vs b0_constant_r2 -0.010) — a genuine weak-physical-signal finding (pure-baseline Pearson r -0.10), not an artifact of the old broken generator, and consistent with this module's already-documented Hansen-theory weakness on H-bonding-dominated aqueous/protic systems.

| claim | prior status | superseded-by | date |
|---|---|---|---|
| Headline scope of KPI `evidence/phase0/kpis/omg-chi-flory-huggins-physical-baseline-vs-ml-kpi.v1.json` (sha256 `98b20b84…`) — instrument-validity retracted by R-B03; ML-vs-theory comparison itself never actually re-run until now | R-B03 (instrument fixed, comparison deferred as W7b) | `evidence/phase0/repairs/V1-SOLV/done/ml-vs-physics-corrected-comparison-receipt.v1.dsse.json` — fair re-run: ML beats corrected FH pure + rescaled baselines, all 3 solvents, honest 85.5% coverage | 2026-08-04 |
| Headline scope of KPI `evidence/phase0/kpis/omg-chi-hansen-3component-physical-baseline-vs-ml-kpi.v1.json` (sha256 `3950f643…`) — instrument-validity retracted by R-B03; ML-vs-theory comparison itself never actually re-run until now | R-B03 (instrument fixed, comparison deferred as W7b) | same V1-SOLV receipt — fair re-run: ML beats corrected Hansen pure + rescaled baselines, all 3 solvents, honest 75.1% coverage | 2026-08-04 |


## W-CITATION-INTEGRITY — Hansen 8-pair external validation significance claim (2026-08-18)

Audit receipt: `amphora-solvency-score/evidence/audit/hansen-external-validation-citation-integrity-v1/hansen-external-validation-citation-integrity-audit-receipt.v1.dsse.json` (ROTATION falsification attack, fire 20260818T160001-1176865-201f03226513).

| claim | refuted-by receipt | superseded-by | date |
|---|---|---|---|
| KPI `evidence/phase0/kpis/hansen-chi-external-validation-8-published-polymer-solvent-pairs-kpi.v1.json` headline "Hansen predictions correlate STRONGLY (Pearson r=+0.8692) with experimental chi" across "8 canonical polymer-solvent chi values from published primary literature" — refuted: 1 of the 8 rows (polystyrene+water) is self-labeled "Order-of-magnitude estimate", not a literature citation; genuine literature coverage is 7/8. Recomputed on the 7 genuinely literature-sourced rows, r drops from 0.8692 (p=0.0051) to 0.6961 (p=0.0823) — not significant at alpha=0.05. Leave-one-out confirms this significance loss is specific to the non-literature row (every other single-row exclusion keeps p<0.02). | `evidence/audit/hansen-external-validation-citation-integrity-v1/hansen-external-validation-citation-integrity-audit-receipt.v1.dsse.json` (`CLAIM_REFUTED`) | mission.md W-CITATION-INTEGRITY DISCLOSURE block (2026-08-18), same audit receipt | 2026-08-18 |

Not retracted: the KPI's own embedded per-pair numbers (chi_published, chi_hansen_predicted) and its self-reported aggregate (r, rho, MAE, fraction-within-factor-3) all independently re-derive byte-for-byte from the 8 rows as stored — nothing was fabricated in the underlying data, and the KPI file itself is unmodified (superseding happens via this new audit receipt plus a mission.md disclosure, per module supersession discipline). The KPI's documented water-soluble-polymer failure mode (PVA/PEG) is unaffected by this finding and stands as previously disclosed.
