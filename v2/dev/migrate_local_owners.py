"""Explicit dedicated-deployment migrations; no legacy fixture discovery or resets."""

import argparse
from datetime import datetime
import json
import os
from pathlib import Path

from amphora_deployment.installation import OWNERS
from amphora_deployment.persistence.migrations import migrate_owner

from check_boundaries import project_specs


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    root=Path(os.environ['LOCALAPPDATA'])/'Amphora/local-v2/installation'
    installations=Path('.test-results/local-owner-inventory-20261006a/owners').absolute()
    specs={cfg['project']['name']:path for path,cfg,_ in project_specs()}
    receipts=[]
    for owner,recipe in OWNERS.items():
        print('Applying explicit owner migration:',owner,flush=True)
        receipts.append(migrate_owner(root,owner,installations/owner,specs[recipe.package]/'uv.lock'))
        print('Owner migration succeeded:',owner,flush=True)
    evidence={'checked_at':datetime.now().astimezone().isoformat(timespec='seconds'),
              'receipts':receipts,'limits':'Dedicated local database only; no serving or scientific readiness claim.'}
    (args.output/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    try:main()
    except Exception:
        raise SystemExit('Dedicated owner migration failed; inspect safe local journal status; raw diagnostics suppressed.') from None
