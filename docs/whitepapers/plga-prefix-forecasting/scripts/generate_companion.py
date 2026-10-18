#!/usr/bin/env python3
"""Readable manuscript companion derived from the same aggregate claim ledger."""
import argparse,json
from pathlib import Path

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path('.'));args=ap.parse_args();r=args.root;d=json.loads((r/'claim_ledger.json').read_text())
    text='''# Prefix-Limited Forecasting of PLGA Drug Release

## Kinetic Features and Grouped Evaluation

Jepson Taylor · Amphora technical white paper draft · 18 October 2026

This readable companion accompanies the complete IEEE-style [PDF](paper.pdf) and [LaTeX source](paper.tex). See the [build and evidence README](README.md) for reproducibility commands, immutable source revisions and data-license attribution.

## Abstract and contribution

The study makes the prediction-time information boundary explicit: a target formulation supplies its first three valid recorded time/release pairs, formulation metadata and a requested later time. Its future release labels are used only for scoring. The contribution is an auditable combination of that prefix boundary, connected drug/publication grouping, matched kinetic representation controls and exact computational replay. It does not introduce generic early-release prediction, nested validation, kinetic residual learning or grouped benchmarking as firsts.

The original exploratory pilot is followed by stage-2 **post-pilot internal validation**. Every Bao curve had already been examined before stage 2. New nested folds protect within-run model selection but do not produce an untouched external test. All ten planned conditional 95% intervals include zero; no contrast survives Holm correction. The benchmark characterizes representation effects and uncertainty without establishing a Pareto-specific advantage.

## Source and recorded-prefix task

The sole corpus is the Bao collection: 321 formulations and 4,913 source observations. The version-2 official formulation table joins one-to-one to the pinned processed derivative. Drug SMILES align exactly and loading values numerically; all rows carry publication DOI metadata. The eligible cohort covers 113 publication DOIs. The separate 181-formulation archive is not merged into this dataset.

The locked cleaning rule requires finite nonnegative time and finite release in [-0.02,1.02]. It removes 35 supra-range release rows and averages four duplicate-time rows. Formulation 74 has six original records but only four valid distinct times and fails the five-point minimum. The result is 320 formulations, 4,870 valid distinct-time observations and 3,910 suffix targets. Time is in days; release is a fraction, reported as percentage-point errors.

In 317/320 formulations the prefix includes the recorded origin (0,0). It usually supplies two positive-time records, not three new independent assays. Third-time median is 1.928 days, IQR0.744–2.945, range0.0217–21.072. Prefixes end by day1 for111 formulations and by day3 for248. This is a first-three-record task, not a fixed24-hour sampling budget. There is no whole-curve interpolation, final-release normalization or duration scaling.

The score averages absolute errors within each observed suffix curve, then averages equally across formulations and multiplies by100. It is distinct from pooled observation MAE, whole-curve RMSE or integrated trajectory error. Query times are retained observed suffix times, not prospectively designed future measurements. Eligibility itself is retrospective.

## Prior work and scope

- [Bannigan et al.,2023](https://doi.org/10.1038/s41467-022-35343-w) already use6/12/24-hour release inputs and nested evaluation. Their drug–polymer grouping differs from jointly drug/DOI-disjoint components and acknowledges some drug overlap.
- [Alabsi et al.,2026](https://doi.org/10.1016/j.nexres.2026.101842) predict beyond24hours using formulation/early-release information, kinetic features and ensemble trees on347 formulations/5,265 observations. Our prefix-only ordinary-kinetic control is inspired by this work, not an exact reproduction; documentation differences are not treated as evidence of leakage.
- [MC-NODE,2026](https://doi.org/10.3390/ph19081227) provides structured dynamics and neural residuals, with DOI/drug/chemical-cluster evaluations. Its sparse-time experiment subsamples training observations while test curves remain complete; the original sparse rule keeps both endpoints. That is a different task from conditioning the target curve on its first three observations. Its published whole-trajectory RMSE is not ranked against our suffix MAE.

## Representations and selection

The pilot candidates are persistence, linear, Higuchi and first order. Stage2 adds KP and Weibull. All fits use visible records only. KP is log-linear with exponent[0.1,2] and rate[1e-6,10]. Weibull uses a transformed fit with beta[0.1,3] and alpha[0.001,10000]days. Insufficient usable points trigger a prefix-only first-order fallback. All forecasts are clipped to[0,1]. These phenomenological fits do not identify mechanisms: in317 profiles both two-parameter families have exactly two usable positive-time points, leaving no residual degrees of freedom. Prefix R², fit counts and fallback flags remain diagnostic features.

Every candidate fits the first two records and predicts the third for selection, then refits all three for suffix prediction. Pareto ranking minimizes that absolute error and fixed nominal family complexity0/1/1/1/2/2. It uses the existing ranking primitive, not a full evolutionary optimizer. The ordinary control summarizes every candidate; the minimum-error control uses a stable pool-order tie-break. Both use the same candidate pool and fitting budget as Pareto selection.

All/minimum/Pareto arms share ten KP/Weibull parameter/diagnostic columns and three query-time summary columns. Added column counts are matched, although constant columns can differ in effective complexity. The combined arm adds both all-candidate and Pareto summaries. The residual arm uses exactly its features and learner budget, fits release minus a prefix-only first-order anchor and adds the anchor back. Bounded pointwise predictions need not be monotone.

## Grouped evaluation and tuning

The pilot has88 connected drug identities, linking exact SMILES or drug MW/TPSA/logP rounded to six decimals. The joint sensitivity and stage2 link a shared drug identity **or** official DOI, yielding78 components; the largest has59 formulations. This blocks identity/DOI chains, not chemical scaffolds, fingerprint clusters or every possible laboratory dependence. Some publication overlap remains in14/15 original drug-only pilot folds.

The pilot uses three shuffled five-fold repetitions with no tuning. Its joint sensitivity was chosen after the primary analysis and locked before its own scores. The RF threading amendment preceded valid scores; boosting intervals were added later during the audit. Stage2 freezes all six arms and four configurations per learner before its own scores but remains design-exposed to the earlier corpus.

Stage2 uses five outer and three inner joint-component folds. Outer held-out counts are43/83/93/48/53. Training-split imputation and category encoding are refit inside each split. Each training formulation receives equal total weight, normalized to mean row weight one. Configuration choice uses only pooled inner out-of-fold formulation MAE.

RF uses128 trees and leaf sizes{2,6} crossed with feature fractions{0.7,1.0}. LightGBM uses256 estimators, rate0.05, L2=1, leaves{7,15} crossed with child samples{10,25}. All settings are fixed-budget, single-thread, seeded; no outer-driven grid expansion, early stopping or learner-family winner selection occurs. The matrix has6×2×5×(4×3+1)=780 fits; full fresh-process replay gives1,560. No new models were fitted for this manuscript.

## Complete exploratory pilot results

MAE below is formulation-balanced suffix error in percentage points.

| Model | Drug primary | Joint drug/DOI sensitivity |
|---|---:|---:|
'''
    names=['Persistence','Linear','Higuchi','First order','Standalone Pareto','RF','Histogram boosting','RF + Pareto'];models=['persistence','linear','higuchi','first_order','amphora_pareto','rf','hist_gradient_boosting','rf_amphora']
    for n,m in zip(names,models):text+=f"| {n} | {d['pilot_metrics']['primary'][m]:.3f} | {d['pilot_metrics']['joint'][m]:.3f} |\n"
    text+='''
The primary RF augmentation difference is−0.905pp with conditional drug-block interval[−1.459,−0.265]; joint blocking gives−0.543pp[−1.099,+0.071]. Boosting contrasts were later audit comparisons and do not establish an advantage. The sensitivities retain the original model/protocol choices.

## Complete stage-2 result matrix

| Arm | RF MAE pp | LightGBM MAE pp |
|---|---:|---:|
'''
    arms=['raw','kin_all','kin_min','kin_pareto','kin_all_pareto','kin_all_pareto_residual'];names=['Raw prefix','All candidates','Minimum error','Pareto','All + Pareto','First-order residual']
    for a,n in zip(arms,names):text+=f"| {n} | {d['stage2_metrics']['rf'][a]:.3f} | {d['stage2_metrics']['lightgbm'][a]:.3f} |\n"
    text+='''
All twelve results are retained. Juxtaposing LightGBM Pareto with raw inputs is descriptive; the ten planned attribution contrasts below are the frozen inferential family. Cross-stage score changes do not form a confirmatory improvement test because learner settings, candidate pool and partitions differ.

## Every planned conditional contrast

Negative delta favors the first named arm. Five thousand paired resamples draw78 joint components with replacement, retaining each selected component's formulations. The ratio estimator remains formulation-weighted. Fits/configurations stay fixed. Centered-bootstrap two-sided values receive Holm correction across all ten contrasts.

| Learner | Arm minus baseline | Delta pp | Conditional95% interval pp | Holm p |
|---|---|---:|---:|---:|
'''
    short=dict(zip(arms,names))
    for x in d['stage2_contrasts']:
        lo,hi=x['conditional_ci95_pp'];text+=f"| {x['learner']} | {short[x['arm']]} − {short[x['baseline']]} | {x['difference_mae_pp']:+.3f} | [{lo:+.3f}, {hi:+.3f}] | {x['holm_adjusted_p']:.3f} |\n"
    text+='''
Every interval includes zero; the smallest adjusted value is0.812. The residual arm does not improve the direct combined arm's point estimate for either learner. This does not establish equivalence or absence of a possible effect. These conditional summaries omit design choice after corpus exposure, retraining under bootstrap recruitment and prospective population/assay variability.

## Computational evidence and next validation

All predictions, inner-search scores and selected configurations replay byte-for-byte for both learners. Independent arithmetic rebuilds groups/splits, cohort, losses, bootstrap contrasts and Holm correction. Fresh feature replay passes all320 future-label perturbations and prefix-change positive controls. The pilot's two full analyses likewise replayed, with1,920 fresh held-out-curve invariance checks. Exact software replay is not independent biological validation.

The stage-2 main processes took648.9s(RF) and54.4s(LightGBM); replay took664.1s and54.8s. Maximum process RSS was239.4MiB. At most two low-priority single-thread processes ran, on two logical CPUs with4GiB address-space caps. No GPU, paid service or new lab measurement was used. These process times are not added as parallel wall time and do not quantify assay savings.

The next study should freeze a representation, horizon, comparison margin and fixed-day sampling schedule before inspecting a genuinely new, overlap-screened PLGA panel with independent assay replicate uncertainty. Ocular transfer requires its own materials/route/biological context and external/prospective evidence. The present contribution is a precise, low-compute evidence workflow that retains uncertain and unfavorable results rather than selecting a favorable headline.

## Source and license

The immutable merged research revision is[879b6d254e10848020635cc2ae2c654968a0cfc1](https://github.com/neverhuman/mvp20-split/tree/879b6d254e10848020635cc2ae2c654968a0cfc1), containing pilot `9e4d4afb` and stage 2 `dfac76ae`. Full64-digit protocol/code digests appear in the PDF appendix and aggregate evidence record. The dataset is[Bao et al., Mendeley Data v2](https://doi.org/10.17632/zzvtdrcy76.2), CC BY4.0, with[Scientific Data descriptor](https://doi.org/10.1038/s41597-025-04621-9). The manuscript tree contains no raw dataset, individual prediction table or private report. Dataset-derived figures retain attribution; repository license/provenance is not changed.
'''
    # Normalize prose numeral spacing while preserving links, identifiers and scientific literals.
    import re
    protected=re.compile(r"(\[[^\]]*\]\([^)]*\)|`[^`]*`|https?://[^\s)]+|\b[0-9a-f]{8,64}\b|\b\d+(?:\.\d+)?e[+-]?\d+\b)")
    parts=protected.split(text)
    for i,part in enumerate(parts):
        if not protected.fullmatch(part):
            part=re.sub(r'(?<=[A-Za-z])(?=\d)', ' ', part)
            parts[i]=re.sub(r'(?<=\d)(?=[A-Za-z])', ' ', part)
    text=''.join(parts)
    (r/'paper.md').write_text(text);print('Readable companion and all aggregate tables generated; no model fits')
