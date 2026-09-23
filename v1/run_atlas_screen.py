#!/usr/bin/env python3
"""Public-label CatBoost GPU screening for the frozen Atlas bundle."""
from __future__ import annotations
import argparse, json, time
from pathlib import Path
import numpy as np
import pandas as pd
from catboost import CatBoostRegressor
from sklearn.model_selection import KFold

def rmsle(y_true, prediction):
    y=np.asarray(y_true,float); p=np.clip(np.asarray(prediction,float),0,None)
    return float(np.sqrt(np.mean((np.log1p(p)-np.log1p(y))**2)))

def main():
    p=argparse.ArgumentParser(); p.add_argument('--artifact-dir',type=Path,default=Path('artifacts/nomad_crystal_atlas')); p.add_argument('--iterations',type=int,default=300); p.add_argument('--folds',type=int,default=2); p.add_argument('--device',default='0'); args=p.parse_args()
    root=args.artifact_dir; train=pd.read_parquet(root/'train_predictors_atlas.parquet'); y=pd.read_parquet(root/'public_targets.parquet')
    base=pd.read_parquet(Path('artifacts/nomad_crystal360/train_predictors_809.parquet'))
    families=json.loads((root/'atlas_definitions.json').read_text())
    family_cols={}
    for d in families: family_cols.setdefault(d['family'],[]).append(d['name'])
    views={'existing_809':list(base.columns),'full_atlas':list(train.columns)}
    for fam,cols in family_cols.items(): views[f'809_plus_{fam}']=list(base.columns)+cols
    kf=KFold(n_splits=args.folds,shuffle=True,random_state=1701); rows=[]; started=time.time()
    for target in ('formation_energy_ev_natom','bandgap_energy_ev'):
      for view,cols in views.items():
        scores=[]
        for fold,(tr,va) in enumerate(kf.split(train),1):
          model=CatBoostRegressor(iterations=args.iterations,depth=7,learning_rate=.05,loss_function='RMSE',random_seed=1701+fold,task_type='GPU',devices=args.device,allow_writing_files=False,verbose=False)
          model.fit(train.iloc[tr][cols],np.log1p(y.iloc[tr][target]),eval_set=(train.iloc[va][cols],np.log1p(y.iloc[va][target])),verbose=False)
          scores.append(rmsle(y.iloc[va][target].to_numpy(),np.expm1(model.predict(train.iloc[va][cols]))))
        rows.append({'target':target,'view':view,'predictors':len(cols),'mean_rmsle':float(np.mean(scores)),'fold_scores':scores,'seconds':time.time()-started})
        print(json.dumps(rows[-1]),flush=True)
    out=pd.DataFrame(rows); out.to_csv(root/'screen_scores.csv',index=False); best=out.sort_values(['target','mean_rmsle']).groupby('target',as_index=False).first(); best.to_json(root/'best_views.json',orient='records',indent=2); print(best.to_string(index=False))
if __name__=='__main__': main()
