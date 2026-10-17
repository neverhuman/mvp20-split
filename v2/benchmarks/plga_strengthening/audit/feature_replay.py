"""Fresh-process replay of prefix-only features/receipts, without fitting models."""
import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[key]='1'
import argparse,hashlib,json,sys
from pathlib import Path
import numpy as np
import pandas as pd

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--artifacts',type=Path,required=True);args=ap.parse_args();a=args.artifacts
    sys.path.insert(0,str(a/'code'));import campaign as c
    c.validate_lock(a);data=json.loads((a/'cohort.json').read_text());receipts=[];checks=[];fingerprints=[]
    for p in data['profiles']:
        p['t']=np.array(p['t']);p['y']=np.array(p['y']);x,z,r=c.features(p,data['numeric']);receipts.append(r)
        bad={**p,'y':p['y'].copy()};bad['y'][3:]=1-bad['y'][3:][::-1];xx,zz,rr=c.features(bad,data['numeric'])
        assert x.equals(xx) and np.array_equal(z,zz) and r==rr
        control={**p,'y':p['y'].copy()};control['y'][0]+=.01;assert not x.equals(c.features(control,data['numeric'])[0])
        checks.append({'formulation':p['id'],'future_tail_features_anchor_selection_invariant':True,'prefix_positive_control':True})
        fingerprints.append({'formulation':p['id'],'all_feature_table_sha256':hashlib.sha256(x.to_csv(index=False,float_format='%.17g').encode()).hexdigest()})
    c.save(a/'audit/candidate_receipts_replay.json',receipts);pd.DataFrame(checks).to_csv(a/'audit/invariance_checks_replay.csv',index=False);c.save(a/'audit/feature_fingerprints.json',fingerprints)
    proof=[]
    for original,replay in [('candidate_receipts.json','candidate_receipts_replay.json'),('invariance_checks.csv','invariance_checks_replay.csv')]:
        h=c.sha(a/original);assert h==c.sha(a/'audit'/replay);proof.append({'original':original,'replay':replay,'sha256':h,'byte_identical':True})
    c.save(a/'audit/feature_replay_proof.json',{'profiles':len(receipts),'status':'PASS','checks':proof});print(json.dumps({'fresh_feature_replay':'PASS','profiles':len(receipts)}))
