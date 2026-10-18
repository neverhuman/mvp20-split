"""Create the separately labeled stage-2 internal-validation results brief."""
import argparse,csv,json,hashlib
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Image

INK=colors.HexColor('#16343E');TEAL=colors.HexColor('#147D78');MUTED=colors.HexColor('#526873');LINE=colors.HexColor('#DCE5E8');PALE=colors.HexColor('#EAF5F2')
LABELS={'raw':'Raw prefix + static descriptors','kin_all':'Ordinary kinetics: all candidates','kin_min':'Kinetics: minimum-prefix-error selection','kin_pareto':'Kinetics: Pareto selection','kin_all_pareto':'All candidates + Pareto','kin_all_pareto_residual':'Combined features, first-order residual'}
SHORT={'raw':'raw','kin_all':'all','kin_min':'minimum','kin_pareto':'Pareto','kin_all_pareto':'all + Pareto','kin_all_pareto_residual':'residual'}

def build(a,out):
    audit=json.loads((a/'independent_audit.json').read_text());assert audit['status']=='PASS'
    protocol=json.loads((a/'code/protocol.json').read_text());lock=json.loads((a/'experiment_lock.json').read_text());contrasts=audit['all_planned_contrasts'];results=audit['all_results']
    styles={
      'title':ParagraphStyle('title',fontName='Helvetica-Bold',fontSize=22,leading=26,textColor=INK,spaceAfter=8),
      'sub':ParagraphStyle('sub',fontName='Helvetica',fontSize=9,leading=12,textColor=MUTED,spaceAfter=12),
      'h':ParagraphStyle('h',fontName='Helvetica-Bold',fontSize=12,leading=16,textColor=INK,spaceBefore=10,spaceAfter=6),
      'body':ParagraphStyle('body',fontName='Helvetica',fontSize=9.3,leading=12.6,textColor=INK,spaceAfter=7),
      'small':ParagraphStyle('small',fontName='Helvetica',fontSize=8.1,leading=10.5,textColor=MUTED,spaceAfter=5),
      'cell':ParagraphStyle('cell',fontName='Helvetica',fontSize=8.5,leading=11,textColor=INK),
      'label':ParagraphStyle('label',fontName='Helvetica-Bold',fontSize=8.2,leading=10.5,textColor=TEAL),
      'mono':ParagraphStyle('mono',fontName='Courier',fontSize=6.6,leading=9,textColor=MUTED,spaceAfter=5)}
    def P(s,k='body'):return Paragraph(s,styles[k])
    def table(rows,widths,header=True):
        t=Table([[P(str(c),'cell') for c in r] for r in rows],colWidths=widths,hAlign='LEFT')
        st=[('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),('LINEBELOW',(0,0),(-1,-2),.35,LINE)]
        if header:st += [('BACKGROUND',(0,0),(-1,0),PALE)]
        t.setStyle(TableStyle(st));return t
    def frame(c,d):
        w,h=A4;c.saveState();c.setTitle('Amphora | Stage 2 PLGA Internal Validation');c.setAuthor('Amphora Research');c.setCreator('Amphora Research');c.setSubject('Post-pilot internal validation, matched kinetic/Pareto ablations and complete replay')
        c.setFillColor(TEAL);c.setFont('Helvetica-Bold',17);c.drawString(42,h-39,'AMPHORA');c.setFillColor(MUTED);c.setFont('Helvetica',7.3);c.drawRightString(w-42,h-35,'STAGE 2 / PRIVATE RESEARCH RESULTS')
        c.setStrokeColor(TEAL);c.setLineWidth(1.2);c.line(42,h-52,w-42,h-52);c.setStrokeColor(LINE);c.setLineWidth(.5);c.line(42,34,w-42,34)
        c.setFont('Helvetica',7);c.setFillColor(MUTED);c.drawString(42,22,'17 October 2026 | Development-exposed corpus; no external confirmation');c.drawRightString(w-42,22,str(d.page));c.restoreState()
    story=[P('Stronger comparisons, separated attribution','title'),P('Frozen stage-2 campaign | Five outer folds, three inner folds, six arms, two learners','sub'),P('<b>Evidence status: post-pilot internal validation.</b> Every Bao curve had been exposed during the original benchmark. New nested grouped folds protect the within-run model-selection boundary; they do not make this an untouched external test. The original audited pilot is retained unchanged.')]
    rows=[['<b>Every frozen arm</b>','<b>RF MAE (pp)</b>','<b>LightGBM MAE (pp)</b>']]
    for arm in LABELS:rows.append([LABELS[arm],f"{results['rf'][arm]:.2f}",f"{results['lightgbm'][arm]:.2f}"])
    story += [table(rows,[301,95,115]),P('Lower is better. Mean absolute error is averaged within each observed suffix curve, then across all 320 formulations. Each formulation is held out once; 3,910 suffix observations per arm. Whole-curve or row-weighted scores from other papers are not comparable.','small')]
    story += [P('What the attribution tests say','h')]
    for learner in ['rf','lightgbm']:
        relevant=[x for x in contrasts if x['learner']==learner]
        text=[]
        for arm,baseline in [('kin_pareto','kin_all'),('kin_all_pareto','kin_all'),('kin_all_pareto_residual','kin_all_pareto')]:
            x=next(z for z in relevant if z['arm']==arm and z['baseline']==baseline);lo,hi=x['conditional_ci95_pp'];text.append(f"{SHORT[arm]} vs {SHORT[baseline]}: <b>{x['difference_mae_pp']:+.2f} pp</b> ({lo:+.2f} to {hi:+.2f})")
        story.append(P('<b>'+('Random Forest' if learner=='rf' else 'LightGBM')+':</b> '+'; '.join(text)+'.'))
    passed=[x for x in contrasts if x['holm_adjusted_p']<.05]
    pareto_passed=[x for x in passed if x['arm'] in ['kin_pareto','kin_all_pareto']]
    if not pareto_passed:story.append(P('<b>All ten planned conditional 95% intervals include zero; no contrast survives Holm correction.</b> Favorable point estimates remain uncertain internal effects. Ordinary kinetic summaries are competitive with Pareto features, and adding Pareto to them does not improve either learner\'s point estimate. A Pareto-specific advantage has not been established.'))
    else:story.append(P('<b>Some planned Pareto contrasts survive the within-campaign Holm correction.</b> This is conditional internal evidence. Selection of this campaign followed the original pilot, and no genuinely unexamined external source was tested.'))
    ident=json.loads((a/'kinetic_identifiability.json').read_text())
    story += [P('Three records impose a hard identification limit','h'),P(f"The prefix includes day-zero/zero-release in 317/320 formulations. KP has exactly two usable positive points in {ident['korsmeyer_peppas']['exactly_two_fit_points']} profiles; Weibull has exactly two in {ident['weibull']['exactly_two_fit_points']}. These two-parameter transformed fits generally have no residual degrees of freedom. Fit quality is not evidence that a release mechanism was identified. Bounded parameters, fallbacks and fit counts are retained."),PageBreak(),P('Every planned paired contrast','title'),P('Negative delta favors the first named arm. Intervals are conditional paired joint-component bootstrap intervals.','sub')]
    rows=[['<b>Learner</b>','<b>Arm minus baseline</b>','<b>Delta pp</b>','<b>95% interval pp</b>','<b>Holm p</b>']]
    for x in contrasts:
        lo,hi=x['conditional_ci95_pp'];rows.append(['RF' if x['learner']=='rf' else 'LightGBM',SHORT[x['arm']]+' - '+SHORT[x['baseline']],f"{x['difference_mae_pp']:+.2f}",f'{lo:+.2f} to {hi:+.2f}',f"{x['holm_adjusted_p']:.3f}"])
    story += [table(rows,[65,170,65,133,78]),P('5,000 paired bootstrap resamples of 78 connected drug/publication blocks, retaining the formulation-weighted estimand. Two-sided centered-bootstrap p-values receive Holm correction across all ten frozen contrasts. These descriptive intervals do not include uncertainty from prior corpus exposure or choosing the stage-2 method family. A nominal interval excluding zero alone is insufficient for a broad superiority claim.','small')]
    fig=a/'audit/planned_contrasts.png'
    if fig.exists():story += [Spacer(1,7),Image(str(fig),width=500,height=270)]
    story += [PageBreak(),P('Protocol, reproduction and limits','title'),P('Locked before stage-2 scoring; all arms retained; no follow-up search on outer scores.','sub')]
    rows=[
      ['<b>Data and independence</b>','The immutable pilot cleaning leaves 320 formulations, 4,870 valid distinct-time observations and 3,910 suffix targets. Joint components connect shared drug identity OR official publication DOI, yielding 78 blocks. Five outer partitions and 15 inner partitions were rebuilt independently; no drug/DOI component crosses any boundary.'],
      ['<b>Equal search budgets</b>','Each learner/arm uses exactly four configurations x three inner folds. Selection minimizes pooled inner out-of-fold formulation MAE, with fixed index tie breaks. Refit only on the outer training set. Median imputation and category encoding are fit inside each training split. Each formulation has equal training weight; weights are normalized to mean one.'],
      ['<b>Candidate attribution</b>','Shared pool: persistence, linear, Higuchi, first order, KP and Weibull. Fit the first two visible records and score the third, then refit all three. Ordinary aggregation uses all six forecasts. Minimum error uses a stable pool-order tie break. Pareto ranks prefix error and parameter count (0,1,1,1,2,2) with the original ranking primitive. All/minimum/Pareto arms have the same ten kinetic-parameter/diagnostic columns and three summary columns.'],
      ['<b>Mechanistic residual</b>','Direct and residual combined arms use exactly the same features, learners, configuration budgets and splits. The residual target subtracts a prefix-only first-order forecast; prediction adds it back. Every forecast is clipped to [0,1]. No full-curve kinetic parameter, final-release normalization or duration scaling is supplied.'],
      ['<b>Parameter bounds</b>','KP: log-linear fit, n in [0.1,2], k in [1e-6,10]. Weibull: transformed linear fit, beta in [0.1,3], alpha in [0.001,10000] days. At least two usable positive records are required; otherwise use the prefix-only first-order fallback. No nonlinear optimizer or untrusted serialized model is loaded.'],
      ['<b>Complete replay</b>','780 model fits per matrix, repeated in fresh processes: 1,560 fits total. Predictions, inner search scores and chosen configurations are byte-identical for both learners. Every eligible profile passes future-label feature/anchor/selection invariance and a visible-prefix positive control. Independent arithmetic verifies the data labels, nested selections, all metrics, intervals and multiplicity correction.'],
      ['<b>Prior-art comparison</b>','The public PLGA comparator model card names KP/Weibull features and LightGBM but does not establish prefix-only kinetic fitting. This benchmark is a safe inspired reimplementation, not an exact reproduction. Reviewer-supplied 2026 article pages were unavailable for complete verification. No cross-paper numeric performance or novelty claim is made.'],
      ['<b>Remaining scope</b>','No genuinely unexamined, overlap-screened external corpus was evaluated. This retrospective literature-digitized in-vitro task does not establish prospective laboratory, ocular or clinical performance, calibrated uncertainty, savings, or patent novelty. Stop after this frozen campaign; fresh confirmation needs a new-study panel with locked sampling and independent assay replicates.']]
    story.append(table(rows,[105,406],header=False))
    runtimes=audit['runtime'];rf=runtimes['main']['rf'];gb=runtimes['main']['lightgbm'];peak=max(runtimes[r][n]['peak_rss_mib'] for r in runtimes for n in runtimes[r])
    story += [P('Resource and provenance record','h'),P(f"Main matrix: RF {rf['seconds']:.1f} s; LightGBM {gb['seconds']:.1f} s. Peak RSS across both runs: {peak:.1f} MiB/process. At most two nice-10 processes, one thread each, CPU affinity 113/114, address-space cap 4 GiB/process. Existing packages; no GPU or paid service.",'small'),
      P('Bao et al., <i>Scientific Data</i> 12, 364 (2025), <link href="https://doi.org/10.1038/s41597-025-04621-9" color="#147D78">doi:10.1038/s41597-025-04621-9</link>. Official data v2: <link href="https://doi.org/10.17632/zzvtdrcy76.2" color="#147D78">doi:10.17632/zzvtdrcy76.2</link>, CC BY 4.0. Public comparator: <link href="https://github.com/Pharmaceutical-ML-lab/Predictive-Modelling-of-Drug-Release-from-PLGA-Microparticles-Using-AI/blob/main/MODEL_CARD.md" color="#147D78">PLGA model card</link>. Exact code, data hashes, splits, all search scores/predictions, licenses and independent audit accompany the evidence archive.','small'),P('Stage-2 lock: '+lock['created_utc'],'small'),P('Protocol SHA-256: '+lock['code_sha256']['protocol.json'],'mono')]
    out.parent.mkdir(parents=True,exist_ok=True);assert not out.exists()
    doc=SimpleDocTemplate(str(out),pagesize=A4,leftMargin=42,rightMargin=42,topMargin=68,bottomMargin=46,title='Amphora | Stage 2 PLGA Internal Validation',author='Amphora Research');doc.build(story,onFirstPage=frame,onLaterPages=frame)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--artifacts',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args();build(args.artifacts,args.out)
