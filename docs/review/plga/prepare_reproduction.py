#!/usr/bin/env python3
"""Prepare a NEW external reproduction directory; download only explicit public pins.

This command creates data/layout/splits and prefix receipts, but fits no global learners.
"""
import argparse,hashlib,json,os,shutil,subprocess,sys,urllib.request
from pathlib import Path

for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[key]='1'
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
PILOT_REF='9e4d4afb444d683761078d2a3bbaa151a3d6177c'
STAGE_REF='dfac76aebc18dcf8b2e021c016f53aaa6b14bd3f'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):Path(p).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')

def frozen_copy(work,module,ref):
    prefix='v2/benchmarks/'+module+'/'
    paths=subprocess.run(['git','-C',str(REPO),'ls-tree','-r','--name-only',ref,'--',prefix],check=True,capture_output=True,text=True).stdout.splitlines();assert paths
    out=work/'code'/module
    for path in paths:
        target=out/path.removeprefix(prefix);target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(subprocess.run(['git','-C',str(REPO),'show',ref+':'+path],check=True,capture_output=True).stdout)
    return out

def prepare(work,source_cache,download):
    import numpy as np
    import pandas as pd
    work=work.resolve();assert not work.is_relative_to(REPO.resolve()),'Keep raw data and generated outputs outside the Git checkout'
    assert not work.exists(),'Choose a new work directory; retained evidence is never overwritten'
    data=json.loads((HERE/'evidence/SOURCE_DATA.json').read_text());work.mkdir(parents=True);raw=work/'raw';raw.mkdir()
    for spec in data['files']:
        name=spec['file'];assert Path(name).name==name;target=raw/name
        if source_cache:
            source=source_cache/name;assert sha(source)==spec['sha256'] and source.stat().st_size==spec['bytes'],name;shutil.copy2(source,target)
        else:
            assert download,'Specify --download or --source-cache'
            req=urllib.request.Request(spec['url'],headers={'User-Agent':'AmphoraPublicReproduction/1.0','Accept':'application/octet-stream','Referer':'https://data.mendeley.com/'})
            with urllib.request.urlopen(req,timeout=90) as response,target.open('wb') as f:
                total=0
                while True:
                    chunk=response.read(65536)
                    if not chunk:break
                    total+=len(chunk);assert total<=spec['bytes'],'Unexpected source size';f.write(chunk)
        assert target.stat().st_size==spec['bytes'] and sha(target)==spec['sha256'],name
    pilot=frozen_copy(work,'plga_prefix',PILOT_REF);stage=frozen_copy(work,'plga_strengthening',STAGE_REF)
    a=work/'plga-prefix-20261017-artifacts';j=work/'plga-prefix-20261017-joint-artifacts';s=work/'plga-strengthening-20261017-artifacts'
    sources={'derivative_repo_commit':data['derivative_commit'],'files':[x for x in data['files'] if x['file']!='mp_dataset_initial_formulation.xlsx'],'mendeley_metadata_url':data['metadata_url'],'dataset_doi':data['dataset_doi'],'license':data['license']}
    for folder in [a,j,s]:folder.mkdir();(folder/'raw').symlink_to(raw,target_is_directory=True);save(folder/'sources.json',sources)
    # Match the frozen primary drug grouping on all source formulations, then join DOI links.
    features=pd.read_excel(raw/'mp_dataset_processed_no_dupes.xlsx');official=pd.read_excel(raw/'mp_dataset_initial_formulation.xlsx');assert len(features)==len(official)==321
    ids=[int(i) for i in features['Formulation Index']];parent={i:i for i in ids}
    def root(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    def link(a,b):
        a,b=root(a),root(b)
        if a!=b:parent[max(a,b)]=min(a,b)
    smiles,descriptors={},{}
    for _,r in features.iterrows():
        i=int(r['Formulation Index'])
        for seen,key in [(smiles,str(r['Drug SMILES']).strip()),(descriptors,tuple(round(float(r[c]),6) for c in ['Drug MW','Drug TPSA','Drug LogP']))]:
            if key in seen:link(i,seen[key])
            else:seen[key]=i
    drug={i:root(i) for i in ids};dseen,pseen={},{};dois={int(r['Formulation Index']):str(r.DOI).strip().replace('https://doi.org/','').replace('http://dx.doi.org/','') for _,r in official.iterrows()}
    for i in ids:
        for seen,key in [(dseen,drug[i]),(pseen,dois[i].lower())]:
            if key in seen:link(i,seen[key])
            else:seen[key]=i
    mapping=pd.DataFrame([{'formulation':i,'doi':dois[i],'joint_group':'joint-%04d'%root(i)} for i in ids])
    for folder in [a,j,s]:mapping.to_csv(folder/'publication_mapping.csv',index=False)
    # No patched scientific model code: use the original entry points in fresh processes.
    for code,folder in [(pilot/'benchmark.py',a),(pilot/'joint/joint_sensitivity.py',j),(stage/'campaign.py',s)]:subprocess.run([sys.executable,str(code),'prepare','--artifacts',str(folder)],check=True)
    (s/'code').symlink_to(stage,target_is_directory=True);(s/'plga_prefix').symlink_to(pilot,target_is_directory=True);(s/'audit').mkdir()
    provenance=json.loads((HERE/'evidence/provenance.json').read_text())
    actual={'pilot_primary':sha(a/'splits.csv'),'pilot_joint':sha(j/'splits.csv'),'stage2':sha(s/'nested_splits.csv')}
    expected={label:provenance['locks'][label].get('splits_sha256',provenance['locks'][label].get('split_sha256')) for label in actual}
    assert actual==expected,{'split_hash_mismatch':actual,'expected':expected}
    state={'status':'prepared','work':str(work),'source_commits':{'pilot':PILOT_REF,'stage2':STAGE_REF},'split_sha256':actual,'global_model_fits':0,'raw_data_location':str(raw),'recorded_versions':{'numpy':np.__version__,'pandas':pd.__version__}}
    save(work/'reproduction_setup.json',state);print(json.dumps(state));return state

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--work',type=Path,required=True);g=ap.add_mutually_exclusive_group(required=True);g.add_argument('--download',action='store_true');g.add_argument('--source-cache',type=Path);args=ap.parse_args();prepare(args.work,args.source_cache,args.download)
