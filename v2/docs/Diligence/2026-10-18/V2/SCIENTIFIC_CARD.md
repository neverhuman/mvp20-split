# Amphora | Scientific proof card - version 2

Separate isolated PLGA research adapter; no LLM calls and no end-to-end deployed campaign-engine qualification.

The retained cohort contains 320 formulations and 3,910 observed suffix targets per evaluation pass, grouped into 78 joint drug/DOI components. The task uses the first three valid recorded observations plus descriptors and requested later time; this is not a fixed-day assay schedule.

Metric: formulation-balanced mean absolute suffix error in release percentage points (pp). Derived loss rows and repeated fits are not independent formulations or experiments.

| Representation | RF MAE, pp | LightGBM MAE, pp |
|---|---:|---:|
| Raw prefix | 13.798 | 13.592 |
| All candidates | 13.077 | 13.472 |
| Minimum error | 13.535 | 13.169 |
| Pareto | 13.348 | 13.139 |
| All + Pareto | 13.104 | 13.544 |
| First-order residual | 13.145 | 13.867 |

Post-pilot internal validation on the development-exposed Bao corpus. All ten planned conditional 95% intervals include zero; none survives Holm correction. No Pareto-specific superiority, equivalence, external validation or customer saving is established.

## Complete planned inference family

| Learner | Arm minus baseline | Difference, pp | Conditional 95% interval, pp | Holm p |
|---|---|---:|---|---:|
| rf | kin_all - raw | -0.720 | [-1.473, +0.191] | 0.812 |
| rf | kin_pareto - kin_all | +0.270 | [-0.338, +0.883] | 1.000 |
| rf | kin_pareto - kin_min | -0.187 | [-0.469, +0.065] | 1.000 |
| rf | kin_all_pareto - kin_all | +0.027 | [-0.188, +0.220] | 1.000 |
| rf | kin_all_pareto_residual - kin_all_pareto | +0.041 | [-0.524, +0.506] | 1.000 |
| lightgbm | kin_all - raw | -0.120 | [-0.935, +0.903] | 1.000 |
| lightgbm | kin_pareto - kin_all | -0.334 | [-1.078, +0.246] | 1.000 |
| lightgbm | kin_pareto - kin_min | -0.030 | [-0.395, +0.280] | 1.000 |
| lightgbm | kin_all_pareto - kin_all | +0.072 | [-0.594, +0.574] | 1.000 |
| lightgbm | kin_all_pareto_residual - kin_all_pareto | +0.323 | [-0.460, +0.846] | 1.000 |

Post-pilot internal validation on the development-exposed Bao corpus. All ten planned conditional 95% intervals include zero; none survives Holm correction. No Pareto-specific superiority, equivalence, external validation or customer saving is established.

The next scientific decision needs a frozen method/comparator, overlap-screened genuinely new panel, fixed sampling horizon, predeclared margin and assay-replicate uncertainty. An unfavorable result is retained; this card does not turn documentation work into that study.

Source: [pinned evidence summary](https://github.com/neverhuman/mvp20-split/blob/9c3018dcdd17f40be27fc3c6dc7057d2d7cb05bc/docs/review/plga/evidence/evidence_summary.json). Bao et al., Mendeley Data v2, DOI 10.17632/zzvtdrcy76.2, CC BY 4.0. Existing repository/data notices apply; no new blanket license.
