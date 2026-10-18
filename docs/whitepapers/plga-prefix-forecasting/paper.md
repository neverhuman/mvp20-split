# Prefix-Limited Forecasting of PLGA Drug Release

## Kinetic Features and Grouped Evaluation

Jepson Taylor · Amphora technical white paper draft · 18 October 2026

This readable companion accompanies the complete IEEE-style [PDF](paper.pdf) and [LaTeX source](paper.tex). See the [build and evidence README](README.md) for reproducibility commands, immutable source revisions and data-license attribution.

## Abstract and contribution

The study makes the prediction-time information boundary explicit: a target formulation supplies its first three valid recorded time/release pairs, formulation metadata and a requested later time. Its future release labels are used only for scoring. The contribution is an auditable combination of that prefix boundary, connected drug/publication grouping, matched kinetic representation controls and exact computational replay. It does not introduce generic early-release prediction, nested validation, kinetic residual learning or grouped benchmarking as firsts.

The original exploratory pilot is followed by stage-2 **post-pilot internal validation**. Every Bao curve had already been examined before stage 2. New nested folds protect within-run model selection but do not produce an untouched external test. All ten planned conditional 95% intervals include zero; no contrast survives Holm correction. The benchmark characterizes representation effects and uncertainty without establishing a Pareto-specific advantage.

## Source and recorded-prefix task

The sole corpus is the Bao collection: 321 formulations and 4,913 source observations. The version-2 official formulation table joins one-to-one to the pinned processed derivative. Drug SMILES align exactly and loading values numerically; all rows carry publication DOI metadata. The eligible cohort covers 113 publication DOIs. The separate 181-formulation archive is not merged into this dataset.

The locked cleaning rule requires finite nonnegative time and finite release in [-0.02,1.02]. It removes 35 supra-range release rows and averages four duplicate-time rows. Formulation 74 has six original records but only four valid distinct times and fails the five-point minimum. The result is 320 formulations, 4,870 valid distinct-time observations and 3,910 suffix targets. Time is in days; release is a fraction, reported as percentage-point errors.

In 317/320 formulations the prefix includes the recorded origin (0,0). It usually supplies two positive-time records, not three new independent assays. Third-time median is 1.928 days, IQR 0.744–2.945, range 0.0217–21.072. Prefixes end by day 1 for 111 formulations and by day 3 for 248. This is a first-three-record task, not a fixed 24-hour sampling budget. There is no whole-curve interpolation, final-release normalization or duration scaling.

The score averages absolute errors within each observed suffix curve, then averages equally across formulations and multiplies by 100. It is distinct from pooled observation MAE, whole-curve RMSE or integrated trajectory error. Query times are retained observed suffix times, not prospectively designed future measurements. Eligibility itself is retrospective.

## Prior work and scope

- [Bannigan et al.,2023](https://doi.org/10.1038/s41467-022-35343-w) already use 6/12/24-hour release inputs and nested evaluation. Their drug–polymer grouping differs from jointly drug/DOI-disjoint components and acknowledges some drug overlap.
- [Alabsi et al.,2026](https://doi.org/10.1016/j.nexres.2026.101842) predict beyond 24 hours using formulation/early-release information, kinetic features and ensemble trees on 347 formulations/5,265 observations. Our prefix-only ordinary-kinetic control is inspired by this work, not an exact reproduction; documentation differences are not treated as evidence of leakage.
- [MC-NODE,2026](https://doi.org/10.3390/ph19081227) provides structured dynamics and neural residuals, with DOI/drug/chemical-cluster evaluations. Its sparse-time experiment subsamples training observations while test curves remain complete; the original sparse rule keeps both endpoints. That is a different task from conditioning the target curve on its first three observations. Its published whole-trajectory RMSE is not ranked against our suffix MAE.

## Representations and selection

The pilot candidates are persistence, linear, Higuchi and first order. Stage 2 adds KP and Weibull. All fits use visible records only. KP is log-linear with exponent[0.1,2] and rate[1e-6,10]. Weibull uses a transformed fit with beta[0.1,3] and alpha[0.001,10000]days. Insufficient usable points trigger a prefix-only first-order fallback. All forecasts are clipped to[0,1]. These phenomenological fits do not identify mechanisms: in 317 profiles both two-parameter families have exactly two usable positive-time points, leaving no residual degrees of freedom. Prefix R², fit counts and fallback flags remain diagnostic features.

Every candidate fits the first two records and predicts the third for selection, then refits all three for suffix prediction. Pareto ranking minimizes that absolute error and fixed nominal family complexity 0/1/1/1/2/2. It uses the existing ranking primitive, not a full evolutionary optimizer. The ordinary control summarizes every candidate; the minimum-error control uses a stable pool-order tie-break. Both use the same candidate pool and fitting budget as Pareto selection.

All/minimum/Pareto arms share ten KP/Weibull parameter/diagnostic columns and three query-time summary columns. Added column counts are matched, although constant columns can differ in effective complexity. The combined arm adds both all-candidate and Pareto summaries. The residual arm uses exactly its features and learner budget, fits release minus a prefix-only first-order anchor and adds the anchor back. Bounded pointwise predictions need not be monotone.

## Grouped evaluation and tuning

The pilot has 88 connected drug identities, linking exact SMILES or drug MW/TPSA/logP rounded to six decimals. The joint sensitivity and stage 2 link a shared drug identity **or** official DOI, yielding 78 components; the largest has 59 formulations. This blocks identity/DOI chains, not chemical scaffolds, fingerprint clusters or every possible laboratory dependence. Some publication overlap remains in 14/15 original drug-only pilot folds.

The pilot uses three shuffled five-fold repetitions with no tuning. Its joint sensitivity was chosen after the primary analysis and locked before its own scores. The RF threading amendment preceded valid scores; boosting intervals were added later during the audit. Stage 2 freezes all six arms and four configurations per learner before its own scores but remains design-exposed to the earlier corpus.

Stage 2 uses five outer and three inner joint-component folds. Outer held-out counts are 43/83/93/48/53. Training-split imputation and category encoding are refit inside each split. Each training formulation receives equal total weight, normalized to mean row weight one. Configuration choice uses only pooled inner out-of-fold formulation MAE.

RF uses 128 trees and leaf sizes{2,6} crossed with feature fractions{0.7,1.0}. LightGBM uses 256 estimators, rate 0.05, L 2=1, leaves{7,15} crossed with child samples{10,25}. All settings are fixed-budget, single-thread, seeded; no outer-driven grid expansion, early stopping or learner-family winner selection occurs. The matrix has 6×2×5×(4×3+1)=780 fits; full fresh-process replay gives 1,560. No new models were fitted for this manuscript.

## Complete exploratory pilot results

MAE below is formulation-balanced suffix error in percentage points.

| Model | Drug primary | Joint drug/DOI sensitivity |
|---|---:|---:|
| Persistence | 40.730 | 40.730 |
| Linear | 23.204 | 23.204 |
| Higuchi | 23.946 | 23.946 |
| First order | 19.324 | 19.324 |
| Standalone Pareto | 26.840 | 26.840 |
| RF | 14.375 | 14.176 |
| Histogram boosting | 13.959 | 13.726 |
| RF + Pareto | 13.470 | 13.633 |

The primary RF augmentation difference is−0.905 pp with conditional drug-block interval[−1.459,−0.265]; joint blocking gives−0.543 pp[−1.099,+0.071]. Boosting contrasts were later audit comparisons and do not establish an advantage. The sensitivities retain the original model/protocol choices.

## Complete stage-2 result matrix

| Arm | RF MAE pp | LightGBM MAE pp |
|---|---:|---:|
| Raw prefix | 13.798 | 13.592 |
| All candidates | 13.077 | 13.472 |
| Minimum error | 13.535 | 13.169 |
| Pareto | 13.348 | 13.139 |
| All + Pareto | 13.104 | 13.544 |
| First-order residual | 13.145 | 13.867 |

All twelve results are retained. Juxtaposing LightGBM Pareto with raw inputs is descriptive; the ten planned attribution contrasts below are the frozen inferential family. Cross-stage score changes do not form a confirmatory improvement test because learner settings, candidate pool and partitions differ.

## Every planned conditional contrast

Negative delta favors the first named arm. Five thousand paired resamples draw 78 joint components with replacement, retaining each selected component's formulations. The ratio estimator remains formulation-weighted. Fits/configurations stay fixed. Centered-bootstrap two-sided values receive Holm correction across all ten contrasts.

| Learner | Arm minus baseline | Delta pp | Conditional 95% interval pp | Holm p |
|---|---|---:|---:|---:|
| rf | All candidates − Raw prefix | -0.720 | [-1.473, +0.191] | 0.812 |
| rf | Pareto − All candidates | +0.270 | [-0.338, +0.883] | 1.000 |
| rf | Pareto − Minimum error | -0.187 | [-0.469, +0.065] | 1.000 |
| rf | All + Pareto − All candidates | +0.027 | [-0.188, +0.220] | 1.000 |
| rf | First-order residual − All + Pareto | +0.041 | [-0.524, +0.506] | 1.000 |
| lightgbm | All candidates − Raw prefix | -0.120 | [-0.935, +0.903] | 1.000 |
| lightgbm | Pareto − All candidates | -0.334 | [-1.078, +0.246] | 1.000 |
| lightgbm | Pareto − Minimum error | -0.030 | [-0.395, +0.280] | 1.000 |
| lightgbm | All + Pareto − All candidates | +0.072 | [-0.594, +0.574] | 1.000 |
| lightgbm | First-order residual − All + Pareto | +0.323 | [-0.460, +0.846] | 1.000 |

Every interval includes zero; the smallest adjusted value is 0.812. The residual arm does not improve the direct combined arm's point estimate for either learner. This does not establish equivalence or absence of a possible effect. These conditional summaries omit design choice after corpus exposure, retraining under bootstrap recruitment and prospective population/assay variability.

## Computational evidence and next validation

All predictions, inner-search scores and selected configurations replay byte-for-byte for both learners. Independent arithmetic rebuilds groups/splits, cohort, losses, bootstrap contrasts and Holm correction. Fresh feature replay passes all 320 future-label perturbations and prefix-change positive controls. The pilot's two full analyses likewise replayed, with 1,920 fresh held-out-curve invariance checks. Exact software replay is not independent biological validation.

The stage-2 main processes took 648.9 s(RF) and 54.4 s(LightGBM); replay took 664.1 s and 54.8 s. Maximum process RSS was 239.4 MiB. At most two low-priority single-thread processes ran, on two logical CPUs with 4 GiB address-space caps. No GPU, paid service or new lab measurement was used. These process times are not added as parallel wall time and do not quantify assay savings.

The next study should freeze a representation, horizon, comparison margin and fixed-day sampling schedule before inspecting a genuinely new, overlap-screened PLGA panel with independent assay replicate uncertainty. Ocular transfer requires its own materials/route/biological context and external/prospective evidence. The present contribution is a precise, low-compute evidence workflow that retains uncertain and unfavorable results rather than selecting a favorable headline.

## Source and license

The immutable merged research revision is[879b6d254e10848020635cc2ae2c654968a0cfc1](https://github.com/neverhuman/mvp20-split/tree/879b6d254e10848020635cc2ae2c654968a0cfc1), containing pilot `9e4d4afb` and stage 2 `dfac76ae`. Full 64-digit protocol/code digests appear in the PDF appendix and aggregate evidence record. The dataset is[Bao et al., Mendeley Data v2](https://doi.org/10.17632/zzvtdrcy76.2), CC BY 4.0, with[Scientific Data descriptor](https://doi.org/10.1038/s41597-025-04621-9). The manuscript tree contains no raw dataset, individual prediction table or private report. Dataset-derived figures retain attribution; repository license/provenance is not changed.
