"""Source-bound current-study card and freshness checks, not scientific discovery."""
import math
from pathlib import Path

from .core import (SOURCE_REVISION, bounded_read, local_file, require, sha, strict_json)

ARMS = ['raw', 'kin_all', 'kin_min', 'kin_pareto', 'kin_all_pareto', 'kin_all_pareto_residual']
LABELS = ['Raw prefix', 'All candidates', 'Minimum error', 'Pareto', 'All + Pareto', 'First-order residual']
CONTRASTS = {('kin_all', 'raw'), ('kin_pareto', 'kin_all'), ('kin_pareto', 'kin_min'),
             ('kin_all_pareto', 'kin_all'), ('kin_all_pareto_residual', 'kin_all_pareto')}
QUALIFIER = ('Post-pilot internal validation on the development-exposed Bao corpus. '
             'All ten planned conditional 95% intervals include zero; none survives Holm correction. '
             'No Pareto-specific superiority, equivalence, external validation or customer saving is established.')
INTEGRATION = 'Separate isolated PLGA research adapter; no LLM calls and no end-to-end deployed campaign-engine qualification.'


def scientific_card(summary):
    scores = summary['stage2']['all_model_mae_pp']
    require(set(scores) == {'rf', 'lightgbm'}, 'incomplete_learner_matrix')
    for values in scores.values():
        require(set(values) == set(ARMS), 'incomplete_arm_matrix')
        require(all(type(v) in {int, float} and math.isfinite(v) for v in values.values()), 'invalid_scientific_value')
    comparisons = summary['stage2']['paired_contrasts']
    require(len(comparisons) == 10, 'incomplete_contrast_family')
    for learner in ['rf', 'lightgbm']:
        selected = [row for row in comparisons if row['learner'] == learner]
        require(len(selected) == 5 and {(c['arm'], c['baseline']) for c in selected} == CONTRASTS,
                'incomplete_contrast_family')
    for c in comparisons:
        expected = scores[c['learner']][c['arm']] - scores[c['learner']][c['baseline']]
        require(math.isclose(expected, c['difference_mae_pp'], abs_tol=1e-10, rel_tol=0), 'contrast_value_drift')
        require(c['conditional_ci95_pp'][0] <= 0 <= c['conditional_ci95_pp'][1]
                and .05 < c['holm_adjusted_p'] <= 1, 'scientific_interpretation_requires_new_review')
    cohort = summary['cohort']; groups = summary['grouping']['joint_drug_publication_components']
    lines = ['# Amphora | Scientific proof card - version 2', '', INTEGRATION, '',
             f"The retained cohort contains {cohort['eligible_formulations']} formulations and {cohort['tail_targets_per_repeat']:,} observed suffix targets per evaluation pass, grouped into {groups} joint drug/DOI components. The task uses the first three valid recorded observations plus descriptors and requested later time; this is not a fixed-day assay schedule.", '',
             'Metric: formulation-balanced mean absolute suffix error in release percentage points (pp). Derived loss rows and repeated fits are not independent formulations or experiments.', '',
             '| Representation | RF MAE, pp | LightGBM MAE, pp |', '|---|---:|---:|']
    for arm, label in zip(ARMS, LABELS):
        lines.append(f"| {label} | {scores['rf'][arm]:.3f} | {scores['lightgbm'][arm]:.3f} |")
    lines += ['', QUALIFIER, '', '## Complete planned inference family', '',
              '| Learner | Arm minus baseline | Difference, pp | Conditional 95% interval, pp | Holm p |',
              '|---|---|---:|---|---:|']
    for c in comparisons:
        lo, hi = c['conditional_ci95_pp']
        lines.append(f"| {c['learner']} | {c['arm']} - {c['baseline']} | {c['difference_mae_pp']:+.3f} | [{lo:+.3f}, {hi:+.3f}] | {c['holm_adjusted_p']:.3f} |")
    lines += ['', QUALIFIER, '',
              'The next scientific decision needs a frozen method/comparator, overlap-screened genuinely new panel, fixed sampling horizon, predeclared margin and assay-replicate uncertainty. An unfavorable result is retained; this card does not turn documentation work into that study.', '',
              f'Source: [pinned evidence summary](https://github.com/neverhuman/mvp20-split/blob/{SOURCE_REVISION}/docs/review/plga/evidence/evidence_summary.json). Bao et al., Mendeley Data v2, DOI 10.17632/zzvtdrcy76.2, CC BY 4.0. Existing repository/data notices apply; no new blanket license.', '']
    return '\n'.join(lines)


def check_document(root: Path, pdf: Path, receipt: Path, renderer: Path):
    record = strict_json(bounded_read(receipt))
    require(sha(bounded_read(pdf)) == record['pdf_sha256'], 'stale_pdf')
    require(sha(bounded_read(renderer)) == record['renderer_sha256'], 'stale_renderer')
    require(isinstance(record['source_sha256'], dict) and record['source_sha256'], 'missing_document_inputs')
    for name, expected in record['source_sha256'].items():
        require(sha(bounded_read(local_file(root, name))) == expected, 'stale_document_input')
    return {'status': 'fresh', 'pdf_sha256': record['pdf_sha256'],
            'meaning': 'Exact recorded inputs/output/renderer match; visual review and semantic truth remain separate.'}
