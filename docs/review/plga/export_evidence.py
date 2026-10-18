#!/usr/bin/env python3
"""Export only derived loss metrics and selected public-safe provenance fields."""
import argparse,csv,hashlib,json
from pathlib import Path
import pandas as pd

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def save(p,d):Path(p).write_text(json.dumps(d,indent=2,allow_nan=False)+'\n')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--primary',type=Path,required=True);ap.add_argument('--joint',type=Path,required=True);ap.add_argument('--stage2',type=Path,required=True);ap.add_argument('--pilot-audit',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args();out=args.out;out.mkdir(parents=True,exist_ok=True)
    primary,joint,s=args.primary,args.joint,args.stage2;pa=read(args.pilot_audit);sa=read(s/'independent_audit.json');assert sa['status']=='PASS'
    parts=[]
    for label,p in [('primary',primary),('joint',joint)]:
        x=pd.read_csv(p/'full/curve_metrics.csv',float_precision='round_trip');x=x.groupby(['formulation','group','model'],as_index=False).mae_pp.mean();x.insert(0,'analysis',label);parts.append(x)
    pilot=pd.concat(parts,ignore_index=True);assert len(pilot)==5120;pilot.to_csv(out/'pilot_formulation_losses.csv',index=False,float_format='%.17g')
    stage=pd.read_csv(s/'curve_metrics.csv',float_precision='round_trip').rename(columns={'ae_pp':'mae_pp'});stage=stage[['learner','arm','formulation','group','outer','mae_pp']];assert len(stage)==3840;stage.to_csv(out/'stage2_formulation_losses.csv',index=False,float_format='%.17g')
    summary={'schema_version':1,'metric':'Mean formulation-level mean absolute suffix error, percentage points','cohort':pa['cohort'],'prefix':pa['prefix'],'grouping':pa['grouping'],'eligible_publication_dois':pa['source_verification']['eligible_publication_dois'],'pilot':{'all_model_mae_pp':pa['all_model_mae_pp'],'paired_contrasts':pa['paired_contrasts'],'bootstrap_draws':2000,'bootstrap_seed':20261017,'classification':'exploratory primary, later joint sensitivity, later boosting audit contrasts'},'stage2':{'all_model_mae_pp':sa['all_results'],'paired_contrasts':sa['all_planned_contrasts'],'bootstrap_draws':5000,'bootstrap_seed':20261020,'budgets':sa['budgets'],'classification':'post-pilot internal validation on development-exposed Bao data; not external confirmation','conditional_ci95_all_include_zero':True,'holm_family_size':10},'raw_measurement_data_included':False,'new_model_fits_for_publication':0,'full_prediction_tables_included':False}
    save(out/'evidence_summary.json',summary)
    replay={'pilot':[],'stage2':read(s/'exact_replay.json'),'feature_replay':read(s/'audit/feature_replay_proof.json'),'interpretation':'These are recorded verification receipts, not a substitute for independently executing the model pipeline.'}
    for r in read(primary.parent/'plga-prefix-20261017-audit-reruns.json'):
        replay['pilot'].append({'analysis':r['analysis'],'completed_utc':r['completed_utc'],'files':r['files'],'fresh_run':r['fresh_run']})
    save(out/'replay_receipts.json',replay)
    runs={}
    for label,p in [('pilot_primary',primary),('pilot_joint',joint),('stage2',s)]:
        l=read(p/'experiment_lock.json');runs[label]={k:l[k] for k in ['created_utc','code_sha256'] if k in l};runs[label].update({k:v for k,v in l.items() if k.endswith('_sha256') and k!='code_sha256'})
    provenance={'source_commits':{'merged_research':'879b6d254e10848020635cc2ae2c654968a0cfc1','pilot':'9e4d4afb444d683761078d2a3bbaa151a3d6177c','stage2':'dfac76aebc18dcf8b2e021c016f53aaa6b14bd3f','manuscript_draft':'ac2273e31ed1429e415d35d3d470557ca21c2742'},'source_artifact_sha256':{'pilot_independent_audit.json':sha(args.pilot_audit),'stage2_independent_audit.json':sha(s/'independent_audit.json'),'pilot_primary_curve_metrics.csv':sha(primary/'full/curve_metrics.csv'),'pilot_joint_curve_metrics.csv':sha(joint/'full/curve_metrics.csv'),'stage2_curve_metrics.csv':sha(s/'curve_metrics.csv')},'locks':runs,'pilot_thread_amendment':read(primary/'protocol_amendments.json'),'runtime':{run:{name:{k:v for k,v in d.items() if k in ['seconds','peak_rss_mib','model_fits']} for name,d in names.items()} for run,names in sa['runtime'].items()},'software':read(s/'environment.json'),'published_loss_fields':{'pilot':list(pilot.columns),'stage2':list(stage.columns)},'loss_rows':{'pilot':len(pilot),'stage2':len(stage)},'privacy_scope':'Derived curve errors only. No time/release observations, SMILES, full prediction rows, private reports, credentials or private links.'}
    save(out/'provenance.json',provenance)
    sources=read(primary/'sources.json');files=[{k:v for k,v in f.items() if k in ['file','url','bytes','sha256']} for f in sources['files']]
    f=primary/'raw/mp_dataset_initial_formulation.xlsx';files.append({'file':f.name,'url':'https://data.mendeley.com/public-files/datasets/zzvtdrcy76/files/0f98021e-47fd-4f24-8226-c450dc796564/file_downloaded','bytes':f.stat().st_size,'sha256':sha(f)})
    save(out/'SOURCE_DATA.json',{'dataset_doi':'10.17632/zzvtdrcy76.2','dataset_version':2,'license':'CC BY 4.0','citation':'Z. Bao, J. Kim, C. Kwok, F. Le Devedec, and C. Allen, Mendeley Data v2 (2024); Scientific Data 12,364 (2025), doi:10.1038/s41597-025-04621-9','derivative_commit':sources['derivative_repo_commit'],'metadata_url':sources['mendeley_metadata_url'],'files':files,'raw_files_committed':False})
    manifest={'schema_version':1,'artifact_kind':'derived reproducibility metrics and provenance, not raw source measurements','files':{p.name:{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(out.iterdir()) if p.is_file() and p.name not in ['MANIFEST.json','verification.json','bootstrap_verification.json'] and p.suffix in ['.json','.csv']}}
    save(out/'MANIFEST.json',manifest);print(json.dumps({'public_export':'complete','pilot_loss_rows':len(pilot),'stage2_loss_rows':len(stage),'raw_measurement_rows_exported':0,'files':list(manifest['files'])}))
