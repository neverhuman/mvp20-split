"""Prepare reviewed public descriptors and exact schema files, never owner state."""
import json
import subprocess
from pathlib import Path
from check_boundaries import ROOT
from local_numeric_configuration import write
from .definition import definition

def prepare_materials(images,output,scope,registry_python):
    evidence=json.loads((images/'evidence.json').read_bytes());assert evidence['status']=='passed'
    output.mkdir(parents=True,exist_ok=False)
    releases={};locks={};schemas=[];profiles=[];entries=[]
    for stage,item in evidence['tools'].items():
        origin=Path(item['directory']);descriptor=json.loads((origin/'descriptor.json').read_bytes())
        assert descriptor['tool']['binding']['image_sha256']==item['image'][7:]
        result=subprocess.run([str(registry_python),'-I',str(ROOT/'dev/catalog_contract_probe.py')],
            input=json.dumps({'operation':'lock','descriptor':descriptor}).encode(),capture_output=True,timeout=30)
        assert result.returncode==0,'Registry public lock validation failed'
        lock=json.loads(result.stdout);releases[stage]=descriptor;locks[stage]=lock
        path=write(output/(stage+'-descriptor.json'),descriptor);entries.append({'descriptor':path.name,'lock':lock})
        for kind in ('input','output'):
            path=output/(stage+'-'+kind+'.json');path.write_bytes((origin/(kind+'.json')).read_bytes())
            ref=descriptor['tool']['inputs' if kind=='input' else 'outputs'][0]['schema_ref']
            schemas.append({'schema_ref':ref,'path':path.name});profiles.append({**ref,'media_type':'application/json','schema_path':path.name})
        (output/(stage+'-parameters.json')).write_bytes((origin/'parameters.json').read_bytes())
    graph=write(output/'graph.json',definition(scope,releases))
    return write(output/'manifest.json',{'profile':'scientific-screening-materials-v1','scope':scope,
        'images':{stage:item['image'] for stage,item in evidence['tools'].items()},'locks':locks,'profiles':profiles,
        'graph':{'definition':graph.name,'releases':entries,'schemas':schemas},'provider_calls':0})
