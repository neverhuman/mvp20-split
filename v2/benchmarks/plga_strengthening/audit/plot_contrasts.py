"""Publication-resolution descriptive figure; consumes all frozen contrasts."""
import os
for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[k]='1'
import argparse,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--artifacts',type=Path,required=True);args=ap.parse_args();a=args.artifacts
    contrasts=json.loads((a/'planned_contrasts.json').read_text());short={'raw':'Raw','kin_all':'All','kin_min':'Minimum','kin_pareto':'Pareto','kin_all_pareto':'All + Pareto','kin_all_pareto_residual':'Residual'}
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'svg.hashsalt':'amphora-stage2-frozen'})
    fig,ax=plt.subplots(figsize=(8.6,4.7));labels=[]
    for i,x in enumerate(contrasts):
        y=9-i;lo,hi=x['conditional_ci95_pp'];m=x['difference_mae_pp'];color='#147D78' if x['learner']=='rf' else '#566B88'
        ax.errorbar(m,y,xerr=[[m-lo],[hi-m]],fmt='o',color=color,capsize=3,markersize=4,elinewidth=1.2)
        labels.append(('RF' if x['learner']=='rf' else 'LightGBM')+' | '+short[x['arm']]+' - '+short[x['baseline']])
    ax.set_yticks(range(9,-1,-1),labels);ax.axvline(0,color='#687D86',lw=.9,ls='--');ax.axhline(4.5,color='#DCE5E8',lw=.8);ax.set_xlabel('Difference in formulation-balanced suffix MAE (percentage points)')
    ax.set_title('All ten frozen contrasts: conditional 95% component-bootstrap intervals',loc='left',fontsize=10,pad=10);ax.grid(axis='x',alpha=.2);ax.set_axisbelow(True)
    for spine in ['top','right','left']:ax.spines[spine].set_visible(False)
    ax.tick_params(axis='y',length=0);fig.subplots_adjust(left=.34,right=.98,bottom=.16,top=.88)
    out=a/'audit';out.mkdir(exist_ok=True);fig.savefig(out/'planned_contrasts.png',dpi=300,facecolor='white');fig.savefig(out/'planned_contrasts.svg',metadata={'Creator':'Amphora Research','Date':None});plt.close(fig)
    print(json.dumps({'plot':'complete','contrasts':len(contrasts),'dpi':300}))
