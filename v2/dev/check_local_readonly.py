"""Public installed owner startup checks with only selected service credentials."""

import argparse
import os
from pathlib import Path
import subprocess
import json
from datetime import datetime
from urllib.parse import quote

from amphora_deployment.credentials import CredentialVault
from amphora_deployment.installation import SERVING_HOSTS
from amphora_deployment.lifecycle.configuration import load_bindings
from amphora_deployment.lifecycle.processes import BASE_ENVIRONMENT
from amphora_deployment.lifecycle.routes import Routes
from amphora_deployment.persistence.state import LocalState


def check(manifest, wrong_role=False, output=None):
    root=Path(os.environ['LOCALAPPDATA'])/'Amphora/local-v2/installation'
    bindings=load_bindings(root,manifest,Routes.load(root))
    state=LocalState.snapshot(root)
    bundle=CredentialVault(root/'credentials.dpapi',state['deployment_id']).load() if wrong_role else None
    failed=False
    observations=[]
    for owner,binding in bindings.items():
        if owner in ('planning','gateway'): continue
        environment={k:v for k,v in os.environ.items() if k.upper() in BASE_ENVIRONMENT}
        environment.update(binding.environment)
        if wrong_role:
            recipe=SERVING_HOSTS[owner]
            name='PG_'+recipe.migration_role.upper()+'_PASSWORD'
            password=bundle.environment([name])[name]
            environment[recipe.database_environment]='postgresql+psycopg://'+recipe.migration_role+':'+quote(password,safe='')+'@127.0.0.1:'+str(state['postgres']['port'])+'/amphora_local?connect_timeout=5'
        result=subprocess.run([str(binding.directory/'environment/Scripts/python.exe'),'-I','-m',
            SERVING_HOSTS[owner].module,'check','--config',str(binding.configuration)],
            env=environment,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=45,
            creationflags=subprocess.CREATE_NO_WINDOW)
        print(owner,'check exit',result.returncode,flush=True)
        passed=result.returncode!=0 if wrong_role else result.returncode==0
        observations.append({'owner':owner,'wrong_role':wrong_role,'exit_code':result.returncode,'passed':passed,
                             'installation_manifest_sha256':binding.installation.installation_manifest_sha256})
        failed=failed or not passed
    if output is not None:
        output.mkdir(parents=True,exist_ok=False)
        (output/'evidence.json').write_text(json.dumps({'checked_at':datetime.now().astimezone().isoformat(timespec='seconds'),
            'owners':observations,'status':'failed' if failed else 'passed','limits':'Public installed startup-check CLIs. Planning wrong-role serving proof is separate.'},indent=2)+'\n',encoding='utf-8')
    return int(failed)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--wrong-role',action='store_true')
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    try: raise SystemExit(check(args.manifest,args.wrong_role,args.output))
    except Exception: raise SystemExit('Owner qualification failed; raw diagnostics suppressed.') from None
