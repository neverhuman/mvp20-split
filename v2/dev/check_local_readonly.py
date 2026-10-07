"""Public installed owner startup checks with only selected service credentials."""

import argparse
import os
from pathlib import Path
import subprocess

from amphora_deployment.installation import SERVING_HOSTS
from amphora_deployment.lifecycle.configuration import load_bindings
from amphora_deployment.lifecycle.processes import BASE_ENVIRONMENT
from amphora_deployment.lifecycle.routes import Routes


def check(manifest):
    root=Path(os.environ['LOCALAPPDATA'])/'Amphora/local-v2/installation'
    bindings=load_bindings(root,manifest,Routes.load(root))
    failed=False
    for owner,binding in bindings.items():
        if owner in ('planning','gateway'): continue
        environment={k:v for k,v in os.environ.items() if k.upper() in BASE_ENVIRONMENT}
        environment.update(binding.environment)
        result=subprocess.run([str(binding.directory/'environment/Scripts/python.exe'),'-I','-m',
            SERVING_HOSTS[owner].module,'check','--config',str(binding.configuration)],
            env=environment,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=45,
            creationflags=subprocess.CREATE_NO_WINDOW)
        print(owner,'check exit',result.returncode,flush=True)
        failed=failed or result.returncode!=0
    return int(failed)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,required=True)
    args=parser.parse_args()
    try: raise SystemExit(check(args.manifest))
    except Exception: raise SystemExit('Owner qualification failed; raw diagnostics suppressed.') from None
