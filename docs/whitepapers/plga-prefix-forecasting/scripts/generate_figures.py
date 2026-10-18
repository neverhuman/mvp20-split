#!/usr/bin/env python3
"""Derive manuscript aggregates/figures from retained audited outputs; no model fits."""
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[key]='1'
import argparse,hashlib,json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ARMS=['raw','kin_all','kin_min','kin_pareto','kin_all_pareto','kin_all_pareto_residual']
LABELS=['Raw prefix','All candidates','Minimum error','Pareto selection','All + Pareto','First-order residual']
SHORT={'raw':'Raw','kin_all':'All','kin_min':'Minimum','kin_pareto':'Pareto','kin_all_pareto':'All + Pareto','kin_all_pareto_residual':'Residual'}

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,d):Path(p).write_text(json.dumps(d,indent=2,allow_nan=False)+'\n')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--pilot-audit',type=Path,required=True);ap.add_argument('--pilot-artifacts',type=Path,required=True);ap.add_argument('--stage2-artifacts',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
    out=args.out;figs=out/'figures';figs.mkdir(parents=True,exist_ok=True);a=args.pilot_artifacts;s=args.stage2_artifacts
    pilot=json.loads(args.pilot_audit.read_text());stage=json.loads((s/'independent_audit.json').read_text());assert stage['status']=='PASS'
    checks=pd.read_csv(s/'invariance_checks.csv');assert len(checks)==320 and checks.iloc[:,1:].all().all()
    for item in json.loads((s/'exact_replay.json').read_text()):
        assert sha(s/'main'/item['learner']/item['file'])==item['sha256']==sha(s/'replay'/item['learner']/item['file'])
    cohort=json.loads((s/'cohort.json').read_text());profiles=cohort['profiles'];ends=np.array([p['t'][2] for p in profiles])
    plt.rcParams.update({'font.family':'DejaVu Serif','font.size':8,'axes.titlesize':8.5,'axes.labelsize':8,'legend.fontsize':7,'pdf.fonttype':42,'ps.fonttype':42,'svg.hashsalt':'amphora-ieee-plga-20261018'})
    teal='#146F77';blue='#344F7A';gray='#727A80';gold='#A76A25'
    fig,ax=plt.subplots(figsize=(3.45,2.1));x=np.sort(ends);ax.step(x,np.arange(1,len(x)+1)/len(x),where='post',color=teal,lw=1.5)
    ax.set_xscale('log');ax.set_xlabel('Time of third recorded observation (days)');ax.set_ylabel('Eligible formulation fraction');ax.set_ylim(0,1.02);ax.set_xlim(.018,25)
    for t in [1,3]:ax.axvline(t,color=gray,lw=.7,ls=':')
    ax.grid(alpha=.2);fig.tight_layout(pad=.5);fig.savefig(figs/'prefix_timing.pdf',metadata={'Creator':'Amphora Research','CreationDate':None,'ModDate':None});fig.savefig(figs/'prefix_timing.png',dpi=300);plt.close(fig)
    contrasts=stage['all_planned_contrasts'];fig,axes=plt.subplots(1,2,figsize=(7.1,2.35),sharey=True)
    labs=['All - raw','Pareto - all','Pareto - minimum','Combined - all','Residual - direct']
    for ax,learner,color in zip(axes,['rf','lightgbm'],[teal,blue]):
        data=[z for z in contrasts if z['learner']==learner]
        for j,z in enumerate(data):
            v=z['difference_mae_pp'];lo,hi=z['conditional_ci95_pp'];ax.errorbar(v,4-j,xerr=[[v-lo],[hi-v]],fmt='o',color=color,capsize=2.5,ms=3.5,lw=1)
        ax.axvline(0,color=gray,lw=.8,ls='--');ax.set_xlim(-1.6,1.1);ax.set_ylim(-.5,4.5);ax.set_yticks(range(4,-1,-1),labs);ax.set_title('Random Forest' if learner=='rf' else 'LightGBM');ax.grid(axis='x',alpha=.18);ax.set_xlabel('MAE difference (percentage points)')
        ax.spines[['top','right']].set_visible(False)
    fig.tight_layout(pad=.6,w_pad=1);fig.savefig(figs/'contrasts.pdf',metadata={'Creator':'Amphora Research','CreationDate':None,'ModDate':None});fig.savefig(figs/'contrasts.png',dpi=300);plt.close(fig)
    bins=np.digitize(ends,np.quantile(ends,[1/3,2/3]));chosen=[min((p for p,g in zip(profiles,bins) if g==k),key=lambda p:p['id']) for k in range(3)]
    preds=pd.read_csv(s/'main/rf/predictions.csv',float_precision='round_trip');fig,axes=plt.subplots(1,3,figsize=(7.1,2.35))
    for ax,p in zip(axes,chosen):
        t=np.array(p['t']);y=np.array(p['y']);ax.scatter(t[3:],100*y[3:],s=12,facecolors='none',edgecolors=gray,lw=.7,label='Observed suffix',zorder=4);ax.scatter(t[:3],100*y[:3],s=16,color='black',label='Visible prefix',zorder=5)
        ax.axvline(t[2],color=gray,ls=':',lw=.8)
        for arm,color,ls,label in [('raw',blue,'--','RF raw'),('kin_all',teal,'-','RF ordinary'),('kin_all_pareto',gold,'-.','RF combined')]:
            d=preds[(preds.formulation==p['id'])&(preds.arm==arm)].sort_values('time_day');assert len(d)==len(t)-3;ax.plot(d.time_day,100*d.predicted_release,color=color,ls=ls,lw=1,label=label)
        ax.set_title('Formulation '+str(p['id'])+'; prefix '+format(t[2],'.2f')+' d');ax.set_xlabel('Time (days)');ax.set_ylim(-3,105);ax.grid(alpha=.15)
    axes[0].set_ylabel('Cumulative release (%)');handles,labels=axes[0].get_legend_handles_labels();fig.legend(handles,labels,ncol=5,loc='upper center',bbox_to_anchor=(.5,1.04),frameon=False);fig.tight_layout(rect=(0,0,1,.91),pad=.5,w_pad=1);fig.savefig(figs/'release_examples.pdf',bbox_inches='tight',metadata={'Creator':'Amphora Research','CreationDate':None,'ModDate':None});fig.savefig(figs/'release_examples.png',dpi=300,bbox_inches='tight');plt.close(fig)
    rows=[]
    for arm,label in zip(ARMS,LABELS):rows.append(label+' & '+f"{stage['all_results']['rf'][arm]:.3f}"+' & '+f"{stage['all_results']['lightgbm'][arm]:.3f}"+r' \\')
    table='% Generated from audited aggregate metrics; no raw observations.\n'+r'\newcommand{\StageRows}{'+'\n'+'\n'.join(rows)+'\n}\n'
    rows=[]
    for z in contrasts:
        lo,hi=z['conditional_ci95_pp'];rows.append(('RF' if z['learner']=='rf' else 'LGBM')+' & '+SHORT[z['arm']]+' - '+SHORT[z['baseline']]+' & '+f"{z['difference_mae_pp']:+.3f}"+' & '+f'[{lo:+.3f}, {hi:+.3f}]'+' & '+f"{z['holm_adjusted_p']:.3f}"+r' \\')
    table+=r'\newcommand{\ContrastRows}{'+'\n'+'\n'.join(rows)+'\n}\n'
    labels=['Persistence','Linear','Higuchi','First order','Standalone Pareto','Random Forest','Histogram boosting','RF + Pareto']
    models=['persistence','linear','higuchi','first_order','amphora_pareto','rf','hist_gradient_boosting','rf_amphora'];rows=[]
    for label,model in zip(labels,models):rows.append(label+' & '+f"{pilot['all_model_mae_pp']['primary'][model]:.3f}"+' & '+f"{pilot['all_model_mae_pp']['joint'][model]:.3f}"+r' \\')
    table+=r'\newcommand{\PilotRows}{'+'\n'+'\n'.join(rows)+'\n}\n';(out/'tables.tex').write_text(table)
    ledger={'source_files':{'pilot_independent_audit':{'sha256':sha(args.pilot_audit)},'stage2_independent_audit':{'sha256':sha(s/'independent_audit.json')},'stage2_protocol':{'sha256':sha(s/'code/protocol.json')},'stage2_predictions_rf':{'sha256':sha(s/'main/rf/predictions.csv')}},'cohort':pilot['cohort'],'prefix':pilot['prefix'],'grouping':pilot['grouping'],'pilot_metrics':pilot['all_model_mae_pp'],'pilot_contrasts':pilot['paired_contrasts'],'stage2_metrics':stage['all_results'],'stage2_contrasts':contrasts,'stage2_runtime':{r:{n:{'seconds':d['seconds'],'peak_rss_mib':d['peak_rss_mib']} for n,d in v.items()} for r,v in stage['runtime'].items()},'illustrative_curve_selection':{'rule':'Smallest formulation ID in each tertile of third-observation time; no selection using prediction errors','formulation_ids':[p['id'] for p in chosen]},'model_fits_in_this_script':0,'figures_are_descriptive':True}
    ledger.update({'source_formulations':321,'source_observations':4913,'eligible_formulations':320,'eligible_observations':4870,'suffix_targets':3910,'eligible_publication_dois':pilot['source_verification']['eligible_publication_dois'],'stage2_outer_fold_sizes':[x['heldout_n'] for x in stage['nested_partitions'] if x['stage']=='outer'],'largest_joint_component':max(pd.Series([p['group'] for p in profiles]).value_counts()),'stage2_fit_budget':stage['budgets']});ledger['largest_joint_component']=int(ledger['largest_joint_component']);save(out/'claim_ledger.json',ledger);print(json.dumps({'figures':3,'audited_result_cells':12,'planned_contrasts':10,'illustrative_ids':[p['id'] for p in chosen],'new_model_fits':0}))
