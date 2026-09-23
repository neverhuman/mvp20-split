#!/usr/bin/env python3
"""Build the CrystalAtlas bank or exercise its two-host sprint safely."""
from __future__ import annotations
import argparse, json, time
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold

from nomad_crystal360.atlas import build_atlas_matrix, validate_bank, write_definitions
from nomad_crystal360.io import load_structures
from nomad_crystal360.sprint import AppendOnlyQueue, Deadline, Job, freeze_run, gpu_info, validate_public_bundle

ROOT=Path(__file__).resolve().parent
ART=ROOT/"artifacts"/"nomad_crystal_atlas"
NOMAD=Path("/home/ubuntu/nomad")


def build(args: argparse.Namespace) -> None:
    out=Path(args.output_dir); out.mkdir(parents=True,exist_ok=True)
    train_raw=pd.read_csv(args.nomad_root/"train.csv"); test_raw=pd.read_csv(args.nomad_root/"test.csv")
    baseline_train=pd.read_parquet(args.baseline_dir/"train_predictors_809.parquet")
    baseline_test=pd.read_parquet(args.baseline_dir/"test_predictors_809.parquet")
    if list(baseline_train.columns)!=list(baseline_test.columns): raise ValueError("existing 809 train/test columns differ")
    started=time.monotonic(); train_struct=load_structures(train_raw,args.nomad_root/"train"); test_struct=load_structures(test_raw,args.nomad_root/"test")
    train_atlas, defs=build_atlas_matrix(train_struct, n_jobs=args.jobs); test_atlas, test_defs=build_atlas_matrix(test_struct, n_jobs=args.jobs)
    if [d.name for d in defs]!=[d.name for d in test_defs]: raise ValueError("Atlas definition order differs between splits")
    train_atlas,test_atlas,defs,quality=validate_bank(train_atlas,test_atlas,baseline_train,defs)
    train_atlas.to_parquet(out/"train_atlas.parquet",index=False); test_atlas.to_parquet(out/"test_atlas.parquet",index=False)
    pd.concat([baseline_train.reset_index(drop=True),train_atlas],axis=1).to_parquet(out/"train_predictors_atlas.parquet",index=False)
    pd.concat([baseline_test.reset_index(drop=True),test_atlas],axis=1).to_parquet(out/"test_predictors_atlas.parquet",index=False)
    write_definitions(defs,out/"atlas_definitions.json")
    (out/"quality_report.json").write_text(json.dumps({**quality,"elapsed_seconds":time.monotonic()-started,"test_targets_used":False},indent=2)+"\n")
    # Targets are public training labels only; test labels never enter this bundle.
    pd.DataFrame({t:train_raw[t] for t in ("formation_energy_ev_natom","bandgap_energy_ev")}).to_parquet(out/"public_targets.parquet",index=False)
    groups=pd.read_csv(args.baseline_dir/"train_anonymous_prototypes.csv")["anonymous_prototype"] if (args.baseline_dir/"train_anonymous_prototypes.csv").exists() else pd.Series(np.arange(len(train_raw)))
    folds=np.full(len(train_raw),-1,dtype=int)
    for k,(_,va) in enumerate(GroupKFold(7).split(train_raw,groups=groups)): folds[va]=k
    pd.DataFrame({"group":groups,"fold":folds}).to_parquet(out/"public_folds.parquet",index=False)
    (out/"build_manifest.json").write_text(json.dumps({"atlas_predictors":len(defs),"combined_predictors":809+len(defs),"quality":quality,"test_targets_used":False},indent=2)+"\n")
    print(json.dumps({"output":str(out),"atlas_predictors":len(defs),"elapsed_seconds":time.monotonic()-started},indent=2))


def sprint(args: argparse.Namespace) -> None:
    out=Path(args.output_dir); out.mkdir(parents=True,exist_ok=True); queue=AppendOnlyQueue(out/"jobs.jsonl")
    if args.enqueue:
        genomes=[("full",), ("family_composition",), ("family_pair",), ("family_triplet",), ("existing_809",)]
        jobs=[Job(target=t,genome=g,fold=f,seed=1000+f,fidelity=200,preferred_host=("xbabe1" if t=="bandgap_energy_ev" else "local")) for t in ("formation_energy_ev_natom","bandgap_energy_ev") for g in genomes for f in range(2)]
        queue.add(jobs); print(f"queued {len(jobs)} jobs")
    for host in ("local","xbabe1"):
        try: print(json.dumps(gpu_info(host)))
        except RuntimeError as exc: print(json.dumps({"host":host,"error":str(exc)}))
    deadline=Deadline.start(args.seconds)
    (out/"sprint_manifest.json").write_text(json.dumps({"deadline_seconds":args.seconds,"started_unix":time.time(),"queue":str(out/"jobs.jsonl"),"private_grade_used":False},indent=2)+"\n")


def main() -> None:
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest="command",required=True)
    b=sub.add_parser("build"); b.add_argument("--nomad-root",type=Path,default=NOMAD); b.add_argument("--baseline-dir",type=Path,default=ROOT/"artifacts"/"nomad_crystal360"); b.add_argument("--output-dir",type=Path,default=ART); b.add_argument("--jobs",type=int,default=1); b.set_defaults(func=build)
    s=sub.add_parser("sprint"); s.add_argument("--output-dir",type=Path,default=ART/"sprint"); s.add_argument("--seconds",type=float,default=7200); s.add_argument("--enqueue",action="store_true"); s.set_defaults(func=sprint)
    g=sub.add_parser("gpu-check"); g.add_argument("hosts",nargs="*",default=["local","xbabe1"]); g.set_defaults(func=lambda a:[print(json.dumps(gpu_info(h))) for h in a.hosts])
    args=p.parse_args(); args.func(args)

if __name__=="__main__": main()
