#!/usr/bin/env python3
"""Frozen, matched-budget, post-pilot internal validation. No model serialization."""
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[key] = '1'
import argparse, datetime, hashlib, importlib.metadata, json, resource, sys, time
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestRegressor
from lightgbm import LGBMRegressor

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'plga_prefix'))
import benchmark as pilot
from ranking import CandidateScore, ObjectiveSpace
P = json.loads((HERE/'protocol.json').read_text())
FAMILIES = tuple(P['candidate_pool'])
ARMS = [x['name'] for x in P['arms']]
PARAMS = P['common_kinetic_parameters']
OLD_HASH = 'fb963e6001ddfeb8c3cfc7715312dfec5188d982dcbc9f3d84a79f76cf8ba7cc'

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x): Path(p).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def emit(event,**x): print(json.dumps({'event':event,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),**x},allow_nan=False),flush=True)

def cohort(a):
    assert sha(HERE.parent/'plga_prefix/benchmark.py') == OLD_HASH
    expected = {'mp_dataset_processed_no_dupes.xlsx':'72c02ebf13925255fe72c088c4f4470a9a28346e179ea2380f9f14bb05bcd9f3',
                'mp_dataset_processed_time_release_only.xlsx':'45c222184145de01062fabb14e033db80971370cb5699fc912f8000245067448',
                'mp_dataset_initial_formulation.xlsx':'033f01949670afde2aae6d8bdf886b41f6f962170e5d2e5ddf07c520edd51169'}
    for name,digest in expected.items(): assert sha(a/'raw'/name)==digest
    profiles,numeric,audit=pilot.read_cohort(a)
    mapping=pd.read_csv(a/'publication_mapping.csv').set_index('formulation')
    for p in profiles:
        p['drug_group']=p['group'];p['group']=str(mapping.loc[p['id'],'joint_group']);p['doi']=str(mapping.loc[p['id'],'doi'])
    assert len(profiles)==320 and len({p['group'] for p in profiles})==78
    return profiles,numeric,audit

def fitted(name,t,y,q):
    t,y,q=map(lambda x:np.asarray(x,dtype=float),(t,y,q))
    if name in pilot.FAMILIES: return pilot.kinetic(name,t,y,q),{}
    mask=(t>0)&(y>0)&(y<1) if name=='weibull' else (t>0)&(y>0)
    n=int(mask.sum());fallback=n<2 or (n>=2 and np.ptp(np.log(t[mask]))<1e-10)
    if fallback:
        z=pilot.kinetic('first_order',t,y,q)
        return z,{'p1':0.,'p2':1.,'r2':0.,'fit_count':n,'fallback':1.}
    x=np.log(t[mask]);v=np.log(-np.log1p(-y[mask])) if name=='weibull' else np.log(y[mask])
    exponent=float(np.clip(np.sum((x-x.mean())*(v-v.mean()))/np.sum((x-x.mean())**2),.1,3. if name=='weibull' else 2.))
    intercept=float(np.mean(v-exponent*x))
    if name=='weibull':
        p1=float(np.clip(np.exp(np.clip(-intercept/exponent,-30,30)),1e-3,1e4));p2=exponent
        def calc(u): return -np.expm1(-np.minimum(np.maximum(u,0)/p1,1e12)**p2)
    else:
        p1=float(np.clip(np.exp(np.clip(intercept,-30,30)),1e-6,10));p2=exponent
        def calc(u): return p1*np.maximum(u,0)**p2
    pred=np.clip(calc(q),0,1);fit=np.clip(calc(t),0,1)
    ss=float(np.sum((y-y.mean())**2));r2=0. if ss<1e-15 else float(1-np.sum((y-fit)**2)/ss)
    return pred,{'p1':p1,'p2':p2,'r2':float(np.clip(r2,-100,1)),'fit_count':n,'fallback':0.}

def features(p,numeric):
    # Every release value read by this function is in y[:3]. Suffix times are query inputs.
    t,y,q=p['t'][:3],p['y'][:3],p['t'][3:]
    base,_,_=pilot.rows_for(p,numeric)
    base=base.drop(columns=[c for c in base if c.startswith('amphora_')])
    forecasts,parameters,errors={},{},[]
    for name in FAMILIES:
        forecasts[name],parameters[name]=fitted(name,t,y,q)
        estimate,_=fitted(name,t[:2],y[:2],t[2:3]);errors.append(float(abs(estimate[0]-y[2])))
    scores=tuple(CandidateScore(n,(e,float(k)),0.) for n,e,k in zip(FAMILIES,errors,P['candidate_complexity']))
    ranked=ObjectiveSpace(('minimize','minimize')).select(scores,len(scores))
    front=[r.candidate_id for r in ranked.ranks if r.front==0]
    selected=FAMILIES[int(np.argmin(errors))]
    all_values=np.stack([forecasts[n] for n in FAMILIES]);front_values=np.stack([forecasts[n] for n in front])
    for label,name in [('kp','korsmeyer_peppas'),('weibull','weibull')]:
        z=parameters[name];first,second=('k','n') if label=='kp' else ('alpha','beta')
        for col,val in [(first,z['p1']),(second,z['p2']),('r2',z['r2']),('fit_count',z['fit_count']),('fallback',z['fallback'])]:base[label+'_'+col]=val
    for label,values,count in [('all',all_values,len(FAMILIES)),('min',forecasts[selected][None,:],1),('pareto',front_values,len(front))]:
        base[label+'_mean']=values.mean(axis=0);base[label+'_std']=values.std(axis=0);base[label+'_count']=float(count)
    receipt={'formulation':p['id'],'errors_first2_predict3':dict(zip(FAMILIES,errors)),'front':front,'minimum_error':selected,'parameters':parameters}
    return base,forecasts['first_order'],receipt

def columns(table,arm):
    special=set(PARAMS+[x+'_'+y for x in ['all','min','pareto'] for y in ['mean','std','count']])
    base=[c for c in table if c not in special]
    if arm=='raw':return base
    labels={'kin_all':['all'],'kin_min':['min'],'kin_pareto':['pareto'],'kin_all_pareto':['all','pareto'],'kin_all_pareto_residual':['all','pareto']}[arm]
    return base+PARAMS+[x+'_'+y for x in labels for y in ['mean','std','count']]

def assignment(profiles,seed,n):
    order=np.array(sorted({p['group'] for p in profiles}));np.random.default_rng(seed).shuffle(order)
    return {str(g):i%n for i,g in enumerate(order)}

def prepare(a):
    a.mkdir(exist_ok=True);profiles,numeric,audit=cohort(a)
    save(a/'cohort.json',{'profiles':[{**p,'t':p['t'].tolist(),'y':p['y'].tolist()} for p in profiles],'numeric':numeric})
    outer=assignment(profiles,P['outer']['seed'],5);rows=[];checks=[]
    for p in profiles: rows.append({'stage':'outer','outer':-1,'fold':outer[p['group']],'formulation':p['id'],'group':p['group'],'doi':p['doi'],'drug_group':p['drug_group']})
    for k in range(5):
        train=[p for p in profiles if outer[p['group']]!=k];inner=assignment(train,P['inner']['seed_base']+k,3)
        for p in train:rows.append({'stage':'inner','outer':k,'fold':inner[p['group']],'formulation':p['id'],'group':p['group'],'doi':p['doi'],'drug_group':p['drug_group']})
    splits=pd.DataFrame(rows);splits.to_csv(a/'nested_splits.csv',index=False)
    independence=[]
    for stage,k,n in [('outer',-1,5)]+[('inner',i,3) for i in range(5)]:
        s=splits[(splits.stage==stage)&(splits.outer==k)]
        for fold in range(n):
            train=s[s.fold!=fold];test=s[s.fold==fold]
            for col in ['group','doi','drug_group']:assert not(set(train[col])&set(test[col])),(stage,k,fold,col)
            independence.append({'stage':stage,'outer':k,'fold':fold,'train_profiles':len(train),'test_profiles':len(test),'shared_drug_or_doi_components':0})
    receipts=[]
    for p in profiles:
        x,z,r=features(p,numeric);receipts.append(r)
        bad={**p,'y':p['y'].copy()};bad['y'][3:]=1-bad['y'][3:][::-1]
        xx,zz,rr=features(bad,numeric);assert x.equals(xx) and np.array_equal(z,zz) and r==rr
        control={**p,'y':p['y'].copy()};control['y'][0]+=.01
        assert not x.equals(features(control,numeric)[0])
        checks.append({'formulation':p['id'],'future_tail_features_anchor_selection_invariant':True,'prefix_positive_control':True})
    save(a/'candidate_receipts.json',receipts);pd.DataFrame(checks).to_csv(a/'invariance_checks.csv',index=False);save(a/'split_independence.json',independence)
    env={'python':sys.version,'packages':{n:importlib.metadata.version(n) for n in ['numpy','pandas','scikit-learn','lightgbm','scipy','openpyxl','joblib','threadpoolctl']}}
    save(a/'environment.json',env)
    files={str(p.relative_to(HERE)):sha(p) for p in sorted(HERE.iterdir()) if p.is_file() and p.suffix in ['.py','.json','.md']}
    save(a/'experiment_lock.json',{'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'code_sha256':files,'split_sha256':sha(a/'nested_splits.csv'),'data_sha256':{p.name:sha(p) for p in sorted((a/'raw').glob('*.xlsx'))},'mapping_sha256':sha(a/'publication_mapping.csv'),'cohort_sha256':sha(a/'cohort.json'),'cohort':audit,'status':P['stage']})
    emit('locked_before_stage2_scores',profiles=len(profiles),groups=78,arms=ARMS,configurations_per_arm=4,inner_folds=3,outer_folds=5,model_fits_per_run=780)

def validate_lock(a):
    lock=json.loads((a/'experiment_lock.json').read_text())
    for p,d in lock['code_sha256'].items():assert sha(HERE/p)==d
    assert sha(a/'nested_splits.csv')==lock['split_sha256'] and sha(a/'publication_mapping.csv')==lock['mapping_sha256']
    assert sha(a/'cohort.json')==lock['cohort_sha256']
    for p,d in lock['data_sha256'].items():assert sha(a/'raw'/p)==d
    return lock

def learner(name,config):
    return RandomForestRegressor(**P['rf_fixed'],**config) if name=='rf' else LGBMRegressor(**P['lightgbm_fixed'],**config)

def preprocessor(cols):
    return ColumnTransformer([('numeric',SimpleImputer(strategy='median'),[c for c in cols if c!='method']),('method',OneHotEncoder(handle_unknown='ignore',sparse_output=False),['method'])])

def mean_loss(ids,y,z):
    return pd.DataFrame({'id':ids,'ae':100*np.abs(y-z)}).groupby('id').ae.mean()

def run(a,name,run_name):
    validate_lock(a);data=json.loads((a/'cohort.json').read_text());profiles=data['profiles'];numeric=data['numeric']
    for p in profiles:p['t']=np.array(p['t']);p['y']=np.array(p['y'])
    out=a/run_name/name;out.mkdir(parents=True,exist_ok=False)
    tables=[];ys=[];anchors=[];ids=[];groups=[];times=[];weights=[]
    for p in profiles:
        x,z,_=features(p,numeric);tables.append(x);ys.extend(p['y'][3:]);anchors.extend(z);n=len(z)
        ids.extend([p['id']]*n);groups.extend([p['group']]*n);times.extend(p['t'][3:]);weights.extend([1/n]*n)
    X=pd.concat(tables,ignore_index=True);y=np.array(ys);anchor=np.array(anchors);ids=np.array(ids);groups=np.array(groups);times=np.array(times);w=np.array(weights)
    s=pd.read_csv(a/'nested_splits.csv');outer=s[s.stage=='outer'].set_index('formulation').fold.to_dict();outerrow=np.array([outer[i] for i in ids])
    predictions=[];search=[];selections=[];timings=[];start_all=time.monotonic()
    grid=P[name+'_grid']
    for k in range(5):
        start=time.monotonic();tr=outerrow!=k;te=~tr
        inn=s[(s.stage=='inner')&(s.outer==k)].set_index('formulation').fold.to_dict();ir=np.array([inn.get(i,-1) for i in ids])
        for arm in ARMS:
            cols=columns(X,arm);residual=arm.endswith('_residual');target=y-anchor if residual else y;losses=[[] for _ in grid]
            for j in range(3):
                it=tr&(ir!=j);iv=tr&(ir==j);pre=preprocessor(cols);xt=pre.fit_transform(X.loc[it,cols]);xv=pre.transform(X.loc[iv,cols]);ww=w[it]/w[it].mean()
                for ci,c in enumerate(grid):
                    model=learner(name,c);model.fit(xt,target[it],sample_weight=ww)
                    z=np.clip(model.predict(xv)+(anchor[iv] if residual else 0),0,1);loss=mean_loss(ids[iv],y[iv],z);losses[ci].extend(loss.tolist())
                    search.append({'learner':name,'outer':k,'arm':arm,'config':ci,'inner':j,'curve_mae_pp':float(loss.mean()),'validation_profiles':len(loss)})
            averages=[float(np.mean(z)) for z in losses];best=int(np.argmin(averages))
            pre=preprocessor(cols);xt=pre.fit_transform(X.loc[tr,cols]);xv=pre.transform(X.loc[te,cols]);model=learner(name,grid[best]);fitstart=time.monotonic()
            model.fit(xt,target[tr],sample_weight=w[tr]/w[tr].mean());fitseconds=time.monotonic()-fitstart
            z=np.clip(model.predict(xv)+(anchor[te] if residual else 0),0,1)
            # Features/anchors were independently rebuilt under changed held-out labels during prepare.
            assert np.array_equal(z,np.clip(model.predict(xv.copy())+(anchor[te].copy() if residual else 0),0,1))
            for form,g,t,yy,zz in zip(ids[te],groups[te],times[te],y[te],z):predictions.append({'learner':name,'outer':k,'arm':arm,'formulation':int(form),'group':g,'time_day':float(t),'observed_release':float(yy),'predicted_release':float(zz)})
            selections.append({'learner':name,'outer':k,'arm':arm,'selected_config':best,'inner_curve_mae_pp':averages,'features':cols,'feature_count_before_encoding':len(cols),'target':'residual_first_order' if residual else 'direct'})
            timings.append({'learner':name,'outer':k,'arm':arm,'outer_refit_seconds':fitseconds,'n_features_after_encoding':int(xt.shape[1]),'outer_train_profiles':int(len(set(ids[tr]))),'outer_test_profiles':int(len(set(ids[te])))})
        emit('outer_fold_finished',run=run_name,learner=name,outer=k,seconds=time.monotonic()-start)
    pd.DataFrame(predictions).to_csv(out/'predictions.csv',index=False,float_format='%.17g');pd.DataFrame(search).to_csv(out/'inner_search.csv',index=False,float_format='%.17g');save(out/'selected_configs.json',selections)
    save(out/'runtime.json',{'seconds':time.monotonic()-start_all,'peak_rss_mib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,'affinity':sorted(os.sched_getaffinity(0)),'model_fits':390,'details':timings})
    emit('learner_complete',run=run_name,learner=name,seconds=time.monotonic()-start_all,predictions_sha256=sha(out/'predictions.csv'))

def summarize(a):
    validate_lock(a);proof=[];frames=[]
    for name in P['learners']:
        for f in ['predictions.csv','inner_search.csv','selected_configs.json']:
            h=sha(a/'main'/name/f);assert h==sha(a/'replay'/name/f),(name,f);proof.append({'learner':name,'file':f,'sha256':h,'fresh_process_identical':True})
        frames.append(pd.read_csv(a/'main'/name/'predictions.csv'))
    save(a/'exact_replay.json',proof);d=pd.concat(frames,ignore_index=True);d['ae_pp']=100*abs(d.observed_release-d.predicted_release)
    curve=d.groupby(['learner','arm','formulation','group','outer'],as_index=False).ae_pp.mean();curve.to_csv(a/'curve_metrics.csv',index=False,float_format='%.17g')
    summary=curve.groupby(['learner','arm'],as_index=False).agg(curve_mae_pp=('ae_pp','mean'),profile_count=('formulation','nunique'));summary.to_csv(a/'all_arm_results.csv',index=False,float_format='%.17g')
    contrasts=[]
    for name in P['learners']:
        loss=curve[curve.learner==name].pivot(index=['formulation','group'],columns='arm',values='ae_pp')[ARMS]
        g=loss.reset_index().groupby('group');sums=g[ARMS].sum().to_numpy();n=g.size().to_numpy();rng=np.random.default_rng(20261020);draw=rng.integers(0,len(n),size=(5000,len(n)));boot=sums[draw].sum(axis=1)/n[draw].sum(axis=1)[:,None]
        for arm,baseline in P['contrasts_per_learner']:
            point=float(loss[arm].mean()-loss[baseline].mean());diff=boot[:,ARMS.index(arm)]-boot[:,ARMS.index(baseline)];pv=float((1+np.sum(abs(diff-point)>=abs(point)))/5001)
            contrasts.append({'learner':name,'arm':arm,'baseline':baseline,'difference_mae_pp':point,'conditional_ci95_pp':np.quantile(diff,[.025,.975]).tolist(),'centered_bootstrap_two_sided_p':pv,'interpretation':'descriptive exposed-corpus internal evidence'})
    order=sorted(range(len(contrasts)),key=lambda i:contrasts[i]['centered_bootstrap_two_sided_p']);last=0.
    for rank,i in enumerate(order):last=max(last,min(1.,(len(order)-rank)*contrasts[i]['centered_bootstrap_two_sided_p']));contrasts[i]['holm_adjusted_p']=last
    save(a/'planned_contrasts.json',contrasts)
    receipts=json.loads((a/'candidate_receipts.json').read_text());ident={n:{'fallback_profiles':sum(r['parameters'][n].get('fallback',0)>0 for r in receipts),'exactly_two_fit_points':sum(r['parameters'][n].get('fit_count',0)==2 for r in receipts)} for n in ['korsmeyer_peppas','weibull']}
    save(a/'kinetic_identifiability.json',ident);emit('campaign_complete',all_arms=summary.to_dict('records'),contrasts=contrasts,identifiability=ident)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['prepare','run','summarize']);ap.add_argument('--artifacts',type=Path,required=True);ap.add_argument('--learner',choices=['rf','lightgbm']);ap.add_argument('--run',choices=['main','replay']);args=ap.parse_args()
    if args.mode=='prepare':prepare(args.artifacts)
    elif args.mode=='run':run(args.artifacts,args.learner,args.run)
    else:summarize(args.artifacts)
