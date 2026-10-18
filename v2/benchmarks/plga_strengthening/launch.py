"""Run the frozen matrix twice, max two isolated single-thread low-priority processes."""
import argparse,json,os,resource,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent

def limits(cpu):
    os.nice(10);os.sched_setaffinity(0,{cpu});resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,4*1024**3));resource.setrlimit(resource.RLIMIT_CPU,(1800,1800))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--artifacts',type=Path,required=True);args=ap.parse_args();a=args.artifacts
    env=os.environ.copy()
    for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:env[key]='1'
    records=[]
    for run in ['main','replay']:
        processes=[];started=time.monotonic()
        for learner,cpu in [('rf',113),('lightgbm',114)]:
            log=(a/(run+'-'+learner+'.log')).open('x')
            p=subprocess.Popen([sys.executable,str(HERE/'campaign.py'),'run','--artifacts',str(a),'--learner',learner,'--run',run],stdout=log,stderr=subprocess.STDOUT,env=env,preexec_fn=lambda cpu=cpu:limits(cpu));processes.append((learner,p,log))
        try:
            for name,p,log in processes:
                status=p.wait(timeout=max(1,2400-(time.monotonic()-started)));log.close();records.append({'run':run,'learner':name,'exit_code':status})
                if status:raise RuntimeError((run,name,status))
        finally:
            for _,p,log in processes:
                if p.poll() is None:p.terminate();p.wait(timeout=10)
                log.close()
        print(json.dumps({'event':'full_run_finished','run':run,'seconds':time.monotonic()-started}),flush=True)
    (a/'launch_record.json').write_text(json.dumps(records,indent=2)+'\n')
    subprocess.run([sys.executable,str(HERE/'campaign.py'),'summarize','--artifacts',str(a)],check=True,env=env)
