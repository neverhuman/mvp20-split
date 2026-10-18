#!/usr/bin/env python3
"""Compare a newly generated full run with the published exact-byte receipts."""
import argparse,hashlib,json
from pathlib import Path

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--work',type=Path,required=True);args=ap.parse_args();root=Path(__file__).resolve().parent;receipts=json.loads((root/'evidence/replay_receipts.json').read_text());checks=[]
    for r in receipts['pilot']:
        folder='plga-prefix-20261017-artifacts' if r['analysis']=='primary' else 'plga-prefix-20261017-joint-artifacts'
        for name,v in r['files'].items():
            p=args.work/folder/'full'/name;digest=hashlib.sha256(p.read_bytes()).hexdigest();assert digest==v['sha256'],str(p);checks.append(str(p.relative_to(args.work)))
    s=args.work/'plga-strengthening-20261017-artifacts'
    for r in receipts['stage2']:
        for run in ['main','replay']:
            p=s/run/r['learner']/r['file'];assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256'],str(p);checks.append(str(p.relative_to(args.work)))
    print(json.dumps({'exact_recorded_hash_comparison':'PASS','files_compared':len(checks),'global_model_fits':0,'condition':'Exact equality is evaluated honestly; mismatches are not silently relaxed on another toolchain or platform.'}))
