"""Prepare reviewed public descriptors and exact schema files, never owner state."""
import json
import hashlib
import subprocess
from pathlib import Path
from check_boundaries import ROOT
from local_numeric_configuration import write
from .definition import definition

def prepare_materials(images,output,scope,registry_python,knowledge=None):
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
    schema=(Path(__file__).parent/('context.v2.schema.json' if knowledge else 'context.schema.json')).read_bytes()
    schema_path=output/'context.schema.json';schema_path.write_bytes(schema)
    ref={'schema_id':'demo.campaign-knowledge-context' if knowledge else 'demo.campaign-context','version':'1','sha256':hashlib.sha256(schema).hexdigest()}
    schemas.append({'schema_ref':ref,'path':schema_path.name})
    profiles.append({**ref,'media_type':'application/json','schema_path':schema_path.name})
    design=json.loads((Path(__file__).parent/'review-design.json').read_bytes())
    context={'format':'amphora.demo-campaign-context.v1','scope':scope,'design':design,
        'bindings':[{'method_id':'solvency' if stage=='hansen_solvency' else 'viscosity',
            'node_id':candidate+'_'+stage,'candidate_id':'fixture-polymer-'+letter,'tool':descriptor['tool']['binding']}
            for candidate,letter in [('candidate_a','A'),('candidate_b','B')] for stage,descriptor in releases.items()],
        'limitations':['Synthetic parameter fixtures, not generated molecular structures.','Codex-authored plan, not runtime LLM output.','Synthesis evidence and process targets are missing. No combined ranking is defined.']}
    if knowledge:
        assert knowledge['revision']['graph']['scope']==scope
        context.update(format='amphora.demo-campaign-context.v2',knowledge=knowledge)
        context['limitations'].append('Knowledge is retained planning context; numerical tools consume explicit parameter artifacts, not domain claims.')
    body=(json.dumps(context,sort_keys=True,separators=(',',':'))+'\n').encode()
    (output/'campaign-context.json').write_bytes(body)
    value_type={'kind':'artifact','media_type':'application/json','schema_ref':ref,'representation':'campaign-review-context','unit':'1'}
    pin={'kind':'source','identity':design['id'],'revision':str(design['revision']),'sha256':hashlib.sha256(body).hexdigest()}
    graph=write(output/'graph.json',definition(scope,releases,value_type,pin))
    return write(output/'manifest.json',{'profile':'scientific-screening-materials-v1','scope':scope,
        'images':{stage:item['image'] for stage,item in evidence['tools'].items()},'locks':locks,'profiles':profiles,
        'graph':{'definition':graph.name,'releases':entries,'schemas':schemas},'provider_calls':0})
