"""Compose separate managed scientific workers with exact image and schema pins."""
import json
from amphora_deployment.scientific_workers.profiles import ToolProfile
from local_numeric_configuration import write

def bind(output,bundle,material,identity,ports,run_id,label):
    root=bundle/label;root.mkdir();workers={};replicas={}
    for stage,image in material['images'].items():
        name=stage.replace('_','-')
        path=write(root/(stage+'.json'),{'actor_id':'science-slot','scope':material['scope'],'run_id':run_id,'image_sha256':image[7:],
            'runtime':{'endpoint':'https://host.docker.internal:'+str(ports['runtime']),'token_env':'AMPHORA_RUNTIME_TOKEN'},
            'artifacts':{'endpoint':'https://host.docker.internal:'+str(ports['artifact']),'token_env':'AMPHORA_ARTIFACT_TOKEN'}})
        profile=ToolProfile.pin(name,image,path,identity.certificate,ports['runtime'],ports['artifact'])
        workers[name]={'image_id':image,'configuration':str(path),'certificate':str(identity.certificate)}
        replicas[name]={'deployment_id':stage,'replica_id':'science-'+stage,'binding_sha256':profile.fingerprint}
    write(output/(label+'-scientific.json'),{'profile':'local-scientific-workers-v1','workers':workers})
    write(output/(label+'-catalog.json'),{'profile':'local-tool-catalog-v1','scope':material['scope'],'worker_id':'science-slot','replicas':replicas})
