"""Run an actual served browser probe with an in-memory launcher credential."""
import argparse
import os
import subprocess
from pathlib import Path
from amphora_deployment.credentials import CredentialVault
from amphora_deployment.persistence.state import LocalState
from check_boundaries import ROOT

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('root','input','output'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--flow',action='store_true')
    parser.add_argument('--public',type=Path)
    args=parser.parse_args();state=LocalState.snapshot(args.root)
    secret=CredentialVault(args.root/'credentials.dpapi',state['deployment_id']).load().environment(['GATEWAY_SESSION_KEY'])
    env={k:v for k,v in os.environ.items() if k.upper() in {'SYSTEMROOT','WINDIR','PATH','TEMP','TMP','USERPROFILE','LOCALAPPDATA','APPDATA','COMSPEC'}}
    env['AMPHORA_BROWSER_LAUNCH_KEY']=secret['GATEWAY_SESSION_KEY']
    script='connected_flow.mjs' if args.flow else 'scientific_review.mjs'
    command=['node',str(ROOT/'studio/tests/integration'/script),str(args.input.absolute()),str(args.output.absolute())]
    if args.public:
        assert args.flow
        command.append(str(args.public.absolute()))
    result=subprocess.run(command,cwd=ROOT/'studio',env=env,timeout=180)
    raise SystemExit(result.returncode)
