"""Bounded observations through public owner HTTP/check CLIs; no foreign SQL."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import json
import os
import subprocess
import urllib.request

from ..installation import SERVING_HOSTS
from .processes import BASE_ENVIRONMENT


def observe_owner(owner, binding):
    endpoint='http://127.0.0.1:'+str(binding.port)
    path={'artifact':'/ready','planning':'/ready','registry':'/v1/releases?limit=1','gateway':'/'}.get(owner,'/health')
    headers={}
    if owner=='registry':
        headers['Authorization']='Bearer '+binding.environment['AMPHORA_REGISTRY_OPERATOR_TOKEN']
    result={'http':'unavailable','database':'not_applicable' if owner=='gateway' else 'unavailable'}
    try:
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(urllib.request.Request(endpoint+path,headers=headers),timeout=3) as response:
            body=response.read(65537)
            if response.status!=200 or len(body)>65536: return result
            if owner=='artifact' and json.loads(body).get('ready') is not True: return result
            if owner=='planning' and json.loads(body).get('status')!='ready': return result
        result['http']='available'
        if owner in ('artifact','planning','registry'):
            result['database']='available'
        elif owner!='gateway':
            environment={k:v for k,v in os.environ.items() if k.upper() in BASE_ENVIRONMENT}
            environment.update(binding.environment)
            command=[str(binding.directory/'environment/Scripts/python.exe'),'-I','-m',SERVING_HOSTS[owner].module,
                     'check','--config',str(binding.configuration)]
            checked=subprocess.run(command,env=environment,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                                   timeout=45,creationflags=subprocess.CREATE_NO_WINDOW)
            if checked.returncode==0: result['database']='available'
    except Exception:
        # Raw configuration/HTTP/driver errors may contain credentials.
        pass
    return result


def observe(bindings):
    # At most seven fixed recipes, each bounded independently; never mutate state.
    with ThreadPoolExecutor(max_workers=7) as pool:
        futures={name:pool.submit(observe_owner,name,binding) for name,binding in bindings.items()}
        owners={name:future.result() for name,future in futures.items()}
    ready=all(row['http']=='available' and row['database'] in ('available','not_applicable') for row in owners.values())
    return {'observed_at':datetime.now().astimezone().isoformat(timespec='seconds'),
            'infrastructure':'available' if ready else 'unavailable','owners':owners,
            'scientific_eligibility':'not_assessed',
            'limits':'Point-in-time owner interface observations; gateway liveness does not imply peer readiness. No campaign or tool authority.'}
