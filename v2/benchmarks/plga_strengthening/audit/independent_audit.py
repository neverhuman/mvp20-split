"""Independent stage-2 audit: no campaign imports and no model fitting."""
import os
for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[k]='1'
import argparse,hashlib,json
from pathlib import Path
import numpy as np
import pandas as pd

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def audit(a,cohort_only=False):
    lock=json.loads((a/'experiment_lock.json').read_text());protocol=json.loads((a/'code/protocol.json').read_text())
    for name,digest in lock['code_sha256'].items():assert sha(a/'code'/name)==digest
    assert sha(a/'nested_splits.csv')==lock['split_sha256']
    source=pd.read_excel(a/'raw/mp_dataset_processed_no_dupes.xlsx');official=pd.read_excel(a/'raw/mp_dataset_initial_formulation.xlsx');obs=pd.read_excel(a/'raw/mp_dataset_processed_time_release_only.xlsx')
    valid=np.isfinite(obs.Time)&np.isfinite(obs.Release)&(obs.Time>=0)&obs.Release.between(-.02,1.02)
    cleaned=obs[valid].groupby(['Formulation Index','Time'],as_index=False).Release.mean();eligible=sorted(cleaned.groupby('Formulation Index').size().loc[lambda s:s>=5].index.astype(int))
    assert len(eligible)==320
    prefix_zero=sum(bool(((d.iloc[:3].Time==0)&(d.iloc[:3].Release==0)).any()) for _,d in cleaned[cleaned['Formulation Index'].isin(eligible)].sort_values('Time').groupby('Formulation Index'))
    assert prefix_zero==317
    parent={int(i):int(i) for i in source['Formulation Index']}
    def root(x):
        while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
        return x
    def join(x,y):
        x,y=root(x),root(y)
        if x!=y:parent[max(x,y)]=min(x,y)
    ss,ds,ps={},{},{}
    for _,r in source.iterrows():
        i=int(r['Formulation Index'])
        for seen,key in [(ss,str(r['Drug SMILES']).strip()),(ds,tuple(round(float(r[c]),6) for c in ['Drug MW','Drug TPSA','Drug LogP']))]:
            if key in seen:join(i,seen[key])
            else:seen[key]=i
    # Publication links only eligible profiles, consistent with the audited pilot components.
    for _,r in official[official['Formulation Index'].isin(eligible)].iterrows():
        i=int(r['Formulation Index']);doi=str(r.DOI).strip().lower().replace('https://doi.org/','').replace('http://dx.doi.org/','')
        if doi in ps:join(i,ps[doi])
        else:ps[doi]=i
    splits=pd.read_csv(a/'nested_splits.csv');outer=splits[splits.stage=='outer'];m=outer.set_index('formulation')
    assert len(outer)==320 and len(set(root(i) for i in eligible))==78
    for i in eligible:
        for j in eligible:assert (root(i)==root(j))==(m.loc[i,'group']==m.loc[j,'group'])
    independence=[]
    for stage,k,n,seed in [('outer',-1,5,20261020)]+[('inner',k,3,20261100+k) for k in range(5)]:
        cut=splits[(splits.stage==stage)&(splits.outer==k)]
        if stage=='inner':assert set(cut.formulation)==set(outer[outer.fold!=k].formulation)
        groups=np.array(sorted(cut.group.unique()));np.random.default_rng(seed).shuffle(groups);mapping={str(g):i%n for i,g in enumerate(groups)}
        assert all(mapping[r.group]==r.fold for r in cut.itertuples())
        for fold in range(n):
            tr=cut[cut.fold!=fold];te=cut[cut.fold==fold]
            assert not(set(root(int(i)) for i in tr.formulation)&set(root(int(i)) for i in te.formulation))
            independence.append({'stage':stage,'outer':k,'fold':fold,'train_n':len(tr),'heldout_n':len(te),'independent_components':True})
    if cohort_only:
        proof={'status':'PASS','profiles':len(eligible),'joint_components':78,'nested_partitions':len(independence),'zero_day_zero_release_prefixes':prefix_zero,'every_partition_component_disjoint':True}
        (a/'independent_cohort_audit.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof));return
    armnames=[x['name'] for x in protocol['arms']];allcurves=[];allresults={};allcontrasts=[];replays=[]
    expected=[]
    for i in eligible:
        d=cleaned[cleaned['Formulation Index']==i].sort_values('Time').iloc[3:]
        for r in d.itertuples():expected.append((i,float(r.Time),float(r.Release)))
    expected=pd.DataFrame(expected,columns=['formulation','time_day','truth'])
    for learner in ['rf','lightgbm']:
        for filename in ['predictions.csv','inner_search.csv','selected_configs.json']:
            first=sha(a/'main'/learner/filename);second=sha(a/'replay'/learner/filename);assert first==second;replays.append({'learner':learner,'file':filename,'sha256':first})
        d=pd.read_csv(a/'main'/learner/'predictions.csv',float_precision='round_trip');assert len(d)==3910*6 and set(d.arm)==set(armnames)
        assert np.isfinite(d[['time_day','observed_release','predicted_release']]).all().all() and d.predicted_release.between(0,1).all()
        assert all(int(m.loc[r.formulation,'fold'])==r.outer for r in d.itertuples())
        for arm in armnames:
            merged=d[d.arm==arm].merge(expected,on=['formulation','time_day'],validate='one_to_one');assert len(merged)==3910 and np.allclose(merged.observed_release,merged.truth,rtol=0,atol=1e-14)
        d['loss']=100*abs(d.observed_release-d.predicted_release);curve=d.groupby(['formulation','group','arm']).loss.mean().unstack('arm')[armnames];allcurves.append(curve)
        allresults[learner]=curve.mean().to_dict()
        recorded=pd.read_csv(a/'all_arm_results.csv');rec=recorded[recorded.learner==learner].set_index('arm').curve_mae_pp
        assert np.allclose(curve.mean(),rec[armnames],rtol=0,atol=1e-11)
        search=pd.read_csv(a/'main'/learner/'inner_search.csv',float_precision='round_trip');selections=json.loads((a/'main'/learner/'selected_configs.json').read_text());assert len(search)==360 and len(selections)==30
        assert search.groupby(['outer','arm','config']).size().eq(3).all()
        for s in selections:
            inner=search[(search.outer==s['outer'])&(search.arm==s['arm'])].copy();inner['total']=inner.curve_mae_pp*inner.validation_profiles
            means=(inner.groupby('config').total.sum()/inner.groupby('config').validation_profiles.sum()).sort_index()
            assert np.allclose(means,s['inner_curve_mae_pp'],rtol=0,atol=1e-11) and s['selected_config']==int(np.argmin(means.to_numpy()))
            for r in inner.itertuples():assert r.validation_profiles==len(splits[(splits.stage=='inner')&(splits.outer==r.outer)&(splits.fold==r.inner)])
        for k in range(5):
            selected={r['arm']:r for r in selections if r['outer']==k}
            assert selected['kin_all_pareto']['features']==selected['kin_all_pareto_residual']['features']
            assert len({selected[n]['feature_count_before_encoding'] for n in ['kin_all','kin_min','kin_pareto']})==1
        g=curve.reset_index().groupby('group');totals=g[armnames].sum().to_numpy();n=g.size().to_numpy();draw=np.random.default_rng(20261020).integers(0,len(n),size=(5000,len(n)));boot=totals[draw].sum(axis=1)/n[draw].sum(axis=1)[:,None]
        for arm,baseline in protocol['contrasts_per_learner']:
            delta=float(curve[arm].mean()-curve[baseline].mean());diff=boot[:,armnames.index(arm)]-boot[:,armnames.index(baseline)];p=float((1+(abs(diff-delta)>=abs(delta)).sum())/5001)
            allcontrasts.append({'learner':learner,'arm':arm,'baseline':baseline,'difference_mae_pp':delta,'conditional_ci95_pp':np.quantile(diff,[.025,.975]).tolist(),'centered_bootstrap_two_sided_p':p})
    order=sorted(range(10),key=lambda i:allcontrasts[i]['centered_bootstrap_two_sided_p']);adjusted=0.
    for rank,i in enumerate(order):adjusted=max(adjusted,min(1.,(10-rank)*allcontrasts[i]['centered_bootstrap_two_sided_p']));allcontrasts[i]['holm_adjusted_p']=adjusted
    retained=json.loads((a/'planned_contrasts.json').read_text())
    for actual,recorded in zip(allcontrasts,retained):
        for key in ['difference_mae_pp','conditional_ci95_pp','centered_bootstrap_two_sided_p','holm_adjusted_p']:assert np.allclose(actual[key],recorded[key],rtol=0,atol=1e-11)
    checks=pd.read_csv(a/'invariance_checks.csv');assert len(checks)==320 and checks.iloc[:,1:].all().all()
    runtime={run:{name:json.loads((a/run/name/'runtime.json').read_text()) for name in ['rf','lightgbm']} for run in ['main','replay']}
    report={'status':'PASS','cohort':{'eligible':320,'suffix_points':3910,'components':78,'prefix_zero_day_zero_release':prefix_zero},'nested_partitions':independence,'all_results':allresults,'all_planned_contrasts':allcontrasts,'replay':replays,'budgets':{'configs_per_arm':4,'inner_folds':3,'outer_folds':5,'arms_per_learner':6,'fits_per_run':780,'total_fits_including_replay':1560},'runtime':runtime,'invariance_checked_profiles':320,'limitations':protocol['stage']+'; no independent external confirmation; conditional uncertainty; prior paper exact reproduction unavailable'}
    (a/'independent_audit.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n');print(json.dumps({'independent_audit':'PASS','all_results':allresults,'contrasts':allcontrasts}),flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--artifacts',type=Path,required=True);ap.add_argument('--cohort-only',action='store_true');args=ap.parse_args();audit(args.artifacts,args.cohort_only)
