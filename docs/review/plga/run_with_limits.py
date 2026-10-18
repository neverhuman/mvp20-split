#!/usr/bin/env python3
"""Portable Linux resource wrapper; use with unchanged frozen benchmark commands."""
import argparse,json,os,resource,subprocess,sys

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--cpu',type=int);ap.add_argument('--plan',action='store_true');ap.add_argument('command',nargs=argparse.REMAINDER);args=ap.parse_args();command=args.command
    if command and command[0]=='--':command=command[1:]
    assert command,'Supply the benchmark command after --'
    assert hasattr(os,'sched_getaffinity'),'The recorded benchmark/runtime uses Linux'
    allowed=sorted(os.sched_getaffinity(0));cpu=allowed[0] if args.cpu is None else args.cpu;assert cpu in allowed,'Select an allowed logical CPU'
    limits={'cpu':cpu,'threads':1,'nice_increment':10,'address_space_gib':4,'cpu_seconds':1800,'wall_seconds':2400,'command':command}
    if args.plan:print(json.dumps({'plan_only':True,**limits}));raise SystemExit(0)
    env=os.environ.copy()
    for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:env[key]='1'
    def bound():
        os.nice(10);os.sched_setaffinity(0,{cpu});resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,4*1024**3));resource.setrlimit(resource.RLIMIT_CPU,(1800,1800))
    p=subprocess.Popen(command,env=env,preexec_fn=bound)
    try:status=p.wait(timeout=2400)
    except subprocess.TimeoutExpired:p.terminate();p.wait(timeout=10);raise SystemExit('Benchmark exceeded the declared wall-time limit')
    raise SystemExit(status)
