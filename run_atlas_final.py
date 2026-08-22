#!/usr/bin/env python3
"""Five-fold public-only final folds and nonnegative model blend."""
from __future__ import annotations
import argparse, hashlib, json, time
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.model_selection import KFold
from scipy.optimize import nnls

def rmsle(y,p): return float(np.sqrt(np.mean((np.log1p(np.clip(p,0,None))-np.log1p(y))**2)))
def sha(path):
 h=hashlib.sha256();
 with open(path,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''): h.update(b)
 return h.hexdigest()
def main():
 p=argparse.ArgumentParser(); p.add_argument('--artifact-dir',type=Path,default=Path('artifacts/nomad_crystal_atlas')); p.add_argument('--iterations',type=int,default=400); p.add_argument('--folds',type=int,default=5); args=p.parse_args(); root=args.artifact_dir
 tr=pd.read_parquet(root/'train_predictors_atlas.parquet'); te=pd.read_parquet(root/'test_predictors_atlas.parquet'); y=pd.read_parquet(root/'public_targets.parquet'); ids=pd.read_csv('artifacts/nomad_crystal360/test_row_ids.csv')['id']; cols=list(tr.columns); kf=KFold(args.folds,shuffle=True,random_state=4219); started=time.time(); all_weights={}; models=('catboost','xgboost','lightgbm'); submission=pd.DataFrame({'id':ids})
 for target in ('formation_energy_ev_natom','bandgap_energy_ev'):
  oof=np.zeros((len(tr),len(models))); test_preds=np.zeros((len(te),len(models)))
  for mi,kind in enumerate(models):
   for fold,(a,b) in enumerate(kf.split(tr),1):
    if kind=='catboost':
     from catboost import CatBoostRegressor
     model=CatBoostRegressor(iterations=args.iterations,depth=7,learning_rate=.05,loss_function='RMSE',random_seed=100+fold,task_type='GPU',devices='0',allow_writing_files=False,verbose=False)
    elif kind=='xgboost':
     from xgboost import XGBRegressor
     model=XGBRegressor(n_estimators=args.iterations,max_depth=8,learning_rate=.04,subsample=.8,colsample_bytree=.8,objective='reg:squarederror',tree_method='hist',device='cuda',random_state=100+fold)
    else:
     from lightgbm import LGBMRegressor
     model=LGBMRegressor(n_estimators=args.iterations,num_leaves=63,learning_rate=.04,device_type='gpu',verbosity=-1,random_state=100+fold)
    fit_kwargs={'eval_set':[(tr.iloc[b][cols],np.log1p(y.iloc[b][target]))]}
    if kind=='catboost': fit_kwargs['verbose']=False
    model.fit(tr.iloc[a][cols],np.log1p(y.iloc[a][target]),**fit_kwargs)
    oof[b,mi]=np.expm1(model.predict(tr.iloc[b][cols])); test_preds[:,mi]+=np.expm1(model.predict(te[cols]))/args.folds
   print(json.dumps({'target':target,'model':kind,'rmsle':rmsle(y[target].to_numpy(),oof[:,mi])}),flush=True)
  w,_=nnls(np.log1p(np.clip(oof,0,None)),np.log1p(y[target].to_numpy())); w=w/w.sum() if w.sum()>0 else np.ones(3)/3; all_weights[target]=w.tolist(); blend=np.clip(test_preds@w,0,None); submission[target]=blend; pd.DataFrame(oof,columns=models).assign(target=y[target]).to_parquet(root/f'oof_{target}.parquet',index=False); pd.DataFrame(test_preds,columns=models).to_parquet(root/f'test_models_{target}.parquet',index=False)
 submission.to_csv(root/'submission.csv',index=False); manifest={'created_unix':time.time(),'elapsed_seconds':time.time()-started,'selected_columns':{'formation_energy_ev_natom':cols,'bandgap_energy_ev':cols},'blend_weights':all_weights,'private_grade_used':False,'submission_sha256':sha(root/'submission.csv')}; (root/'freeze_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n'); print(json.dumps(manifest,indent=2))
if __name__=='__main__': main()
