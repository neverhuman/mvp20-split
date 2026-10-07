"""Current installed host inventory and independent Deployment CLI profile checks."""

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import subprocess

from amphora_deployment import DeploymentProfile
from amphora_deployment.credentials import CredentialVault
from amphora_deployment.lifecycle.configuration import load_bindings
from amphora_deployment.lifecycle.processes import BASE_ENVIRONMENT
from amphora_deployment.lifecycle.routes import Routes
from amphora_deployment.persistence.state import LocalState


def verify(output, installation):
    output.mkdir(parents=True,exist_ok=False)
    root=Path(os.environ['LOCALAPPDATA'])/'Amphora/local-v2/installation'
    bindings=load_bindings(root,root/'configurations/readonly-drain-20261006a/manifest.json',Routes.load(root))
    original=DeploymentProfile.from_bytes(Path('.test-results/local-owner-inventory-20261006a/profile.json').read_bytes())
    record=json.loads(original.canonical_bytes())
    record['profile_id']='local-current-infrastructure'
    record['artifacts']=[]
    for name,binding in bindings.items():
        for wheel in binding.installation.wheels:
            package,release=wheel.filename.split('-')[:2]
            record['artifacts'].append({'name':name+'.'+package,'release':release,'sha256':wheel.sha256,
                                       'operating_system':'windows','architecture':'x86_64'})
    assert record['provider']['mode']=='disabled' and record['target']['accelerator']=='none'
    profile=DeploymentProfile.from_bytes(json.dumps(record).encode())
    path=(output/'profile.json').absolute();path.write_bytes(profile.canonical_bytes())
    state=LocalState.snapshot(root)
    token=CredentialVault(root/'credentials.dpapi',state['deployment_id']).load().environment(['GATEWAY_SESSION_KEY'])['GATEWAY_SESSION_KEY']
    environment={k:v for k,v in os.environ.items() if k.upper() in BASE_ENVIRONMENT}
    environment[profile.access.auth_secret_env]=token
    command=[str((installation/'environment/Scripts/python.exe').absolute()),'-I','-m','amphora_deployment']
    reports={}
    for action in ('validate','preflight'):
        result=subprocess.run([*command,action,'--profile',str(path)],env=environment,capture_output=True,text=True,
                              timeout=30,creationflags=subprocess.CREATE_NO_WINDOW)
        assert result.returncode==0,'Independent selected-host CLI rejected profile'
        reports[action]=json.loads(result.stdout)
    evidence={'checked_at':datetime.now().astimezone().isoformat(timespec='seconds'),'status':'passed',
              'owners':{name:{'release':binding.installation.release,'manifest_sha256':binding.installation.installation_manifest_sha256}
                        for name,binding in bindings.items()},'reports':reports,
              'limits':'CPU-only native owner/gateway installations; no accelerator workload or Linux-only scientific eligibility. Provider disabled, zero external calls.'}
    (output/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
    print('Current owner inventory and independently installed profile CLI passed:',output,flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--installation',type=Path,required=True)
    args=parser.parse_args()
    try: verify(args.output,args.installation)
    except Exception: raise SystemExit('Current installed profile verification failed; raw diagnostics suppressed.') from None
