#!/usr/bin/env python3
"""Model-free verification of public aggregate/paired error evidence."""
import argparse,csv,hashlib,json,math,statistics
from collections import defaultdict
from pathlib import Path

ARMS=['raw','kin_all','kin_min','kin_pareto','kin_all_pareto','kin_all_pareto_residual']
MODELS=['persistence','linear','higuchi','first_order','amphora_pareto','rf','hist_gradient_boosting','rf_amphora']
def load(p):return json.loads(Path(p).read_text())
def close(a,b):assert math.isclose(float(a),float(b),rel_tol=0,abs_tol=1e-10),(a,b)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def verify(root,bootstrap=False):
    manifest=load(root/'MANIFEST.json')
    for name,v in manifest['files'].items():
        assert Path(name).name==name;f=root/name;assert f.stat().st_size==v['bytes'] and sha(f)==v['sha256'],name
    summary=load(root/'evidence_summary.json');provenance=load(root/'provenance.json');assert summary['new_model_fits_for_publication']==0 and not summary['raw_measurement_data_included']
    pilot=list(csv.DictReader((root/'pilot_formulation_losses.csv').open()));stage=list(csv.DictReader((root/'stage2_formulation_losses.csv').open()));assert len(pilot)==5120 and len(stage)==3840
    assert set(pilot[0])=={'analysis','formulation','group','model','mae_pp'};assert set(stage[0])=={'learner','arm','formulation','group','outer','mae_pp'}
    for rows,kind,model,expected in [(pilot,'analysis','model',summary['pilot']['all_model_mae_pp']),(stage,'learner','arm',summary['stage2']['all_model_mae_pp'])]:
        seen=set();values=defaultdict(list);forms=defaultdict(set);form_groups={}
        for r in rows:
            value=float(r['mae_pp']);assert math.isfinite(value) and value>=0
            key=(r[kind],r['formulation'],r[model]);assert key not in seen;seen.add(key);values[(r[kind],r[model])].append(value);forms[(r[kind],r[model])].add(r['formulation'])
            k=(r[kind],r['formulation']);assert k not in form_groups or form_groups[k]==r['group'];form_groups[k]=r['group']
        for (group,name),v in values.items():assert len(forms[(group,name)])==320;close(statistics.fmean(v),expected[group][name])
    for name,expected in [('primary',88),('joint',78)]:assert len({r['group'] for r in pilot if r['analysis']==name})==expected
    for name in ['rf','lightgbm']:assert len({r['group'] for r in stage if r['learner']==name})==78
    for learner in ['rf','lightgbm']:
        s={int(r['formulation']):int(r['outer']) for r in stage if r['learner']==learner};assert [sum(v==i for v in s.values()) for i in range(5)]==[43,83,93,48,53]
    replay=load(root/'replay_receipts.json');assert len(replay['stage2'])==6 and all(r['fresh_process_identical'] for r in replay['stage2']);assert all(f['byte_identical'] for r in replay['pilot'] for f in r['files'].values())
    result={'status':'PASS','pilot_rows':len(pilot),'stage2_rows':len(stage),'pilot_result_cells':16,'stage2_result_cells':12,'model_fits':0,'manifest_file_hashes_checked':len(manifest['files']),'recorded_replay_receipts_consistent':True,'bootstrap_recomputed':False}
    if bootstrap:
        import numpy as np
        def boot(rows,kind,name,model,names,draws,seed):
            by=defaultdict(lambda:defaultdict(dict))
            for r in rows:
                if r[kind]==name:by[r['group']][int(r['formulation'])][r[model]]=float(r['mae_pp'])
            groups=sorted(by);n=np.array([len(by[g]) for g in groups]);sums=np.array([[sum(by[g][i][m] for i in sorted(by[g])) for m in names] for g in groups]);draw=np.random.default_rng(seed).integers(0,len(groups),size=(draws,len(groups)))
            return sums[draw].sum(axis=1)/n[draw].sum(axis=1)[:,None]
        for analysis in ['primary','joint']:
            b=boot(pilot,'analysis',analysis,'model',MODELS,2000,20261017)
            for c in summary['pilot']['paired_contrasts']:
                if c['analysis']!=analysis:continue
                dif=b[:,MODELS.index('rf_amphora')]-b[:,MODELS.index(c['baseline'])];ci=np.quantile(dif,[.025,.975])
                for x,y in zip(ci,c['conditional_ci95_pp']):close(x,y)
        calculated=[]
        for learner in ['rf','lightgbm']:
            b=boot(stage,'learner',learner,'arm',ARMS,5000,20261020)
            for c in summary['stage2']['paired_contrasts']:
                if c['learner']!=learner:continue
                actual=summary['stage2']['all_model_mae_pp'][learner];point=actual[c['arm']]-actual[c['baseline']];close(point,c['difference_mae_pp']);dif=b[:,ARMS.index(c['arm'])]-b[:,ARMS.index(c['baseline'])];ci=np.quantile(dif,[.025,.975])
                for x,y in zip(ci,c['conditional_ci95_pp']):close(x,y)
                p=float((1+np.sum(abs(dif-point)>=abs(point)))/5001);close(p,c['centered_bootstrap_two_sided_p']);calculated.append((p,c))
        previous=0.
        for j,(p,c) in enumerate(sorted(calculated,key=lambda x:x[0])):previous=max(previous,min(1.,(10-j)*p));close(previous,c['holm_adjusted_p'])
        assert all(c['conditional_ci95_pp'][0]<=0<=c['conditional_ci95_pp'][1] for c in summary['stage2']['paired_contrasts'])
        result.update(bootstrap_recomputed=True,pilot_intervals_recomputed=4,stage2_intervals_recomputed=10,holm_family_recomputed=10,numpy_version=np.__version__)
    print(json.dumps(result));return result

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--evidence',type=Path,default=Path(__file__).resolve().parent/'evidence');ap.add_argument('--bootstrap',action='store_true');ap.add_argument('--output',type=Path);args=ap.parse_args();r=verify(args.evidence,args.bootstrap)
    if args.output:args.output.write_text(json.dumps(r,indent=2)+'\n')
