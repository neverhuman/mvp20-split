# amphora-barrier-corrosion-score — retraction / supersession index

Each row records a refuted claim, the signed receipt that refuted it, and the signed repair receipt that supersedes the refuted element. Superseded artifacts are never modified or deleted.

## R-B02 — barrier_index structural unevaluability (repaired 2026-08-03)

| claim | refuted-by receipt path | superseded-by | date |
|---|---|---|---|
| `EisPredictionV1.barrier_index` / `metrics.barrier_index` is unconditionally `None` on every code path in `src/lib.rs`, so the locked primary KPI (blinded Kendall tau at `metrics.barrier_index`) is structurally unevaluable | `benchmarks/three-series-barrier-ranking-v1/three-series-barrier-ranking-receipt.v1.dsse.json` | `evidence/phase0/repairs/R-B02/done/barrier-index-repair-receipt.v1.dsse.json` (structural finding only; W1's statistical-infeasibility findings — all 3 in-class series below FEASIBILITY_FLOOR=6 — remain in force) | 2026-08-03 |

## R-C05 — Mondrian/reweighted domain-shift conformal repair rescoped to per-environment coverage table (2026-08-12)

| claim | refuted-by receipt path | superseded-by | date |
|---|---|---|---|
| Environment-stratified (Mondrian, chloride-environment-class) conformal restores >= 0.88 reverse-leg (marine-cal -> nonmarine-deploy) observed coverage at the 0.90 target, repairing `corr-rate-conformal-domain-shift-v1` (which found 0.876307, p=3.1e-5) | `benchmarks/corr-rate-conformal-domain-shift-v1/corr-rate-conformal-domain-shift-receipt.v1.dsse.json` (original refutation, unchanged, stands); this repair claim itself never landed as a positive receipt -- fires 1 (empirical, best variant 0.877389) and 2 (analytic structural-ceiling proof: 6/8 chloride classes have zero marine-calibration rows) of `evidence/phase0/repairs/R-C05/attempts/` REFUTED it before it could be signed as survived | `evidence/phase0/repairs/R-C05/done/r-c05-per-environment-coverage-rescope-receipt.v1.dsse.json` (RESCOPE: replaces the single pooled >=0.88 target with a per-chloride-environment-class coverage table; only 2/8 classes -- halide, other, 24.1% of reverse-leg test rows -- have any marine-calibration support, both individually >=0.88; the remaining 6 classes fall back to the pooled quantile with no calibration-side fix available from this dataset) | 2026-08-12 |
