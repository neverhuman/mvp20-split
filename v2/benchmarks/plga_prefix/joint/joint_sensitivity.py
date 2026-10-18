#!/usr/bin/env python3
"""Explicit grouping-only sensitivity adapter; preserves the frozen primary pipeline."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import benchmark as primary
import pandas as pd

assert hashlib.sha256((HERE.parent / "benchmark.py").read_bytes()).hexdigest() == "fb963e6001ddfeb8c3cfc7715312dfec5188d982dcbc9f3d84a79f76cf8ba7cc"
assert hashlib.sha256((HERE.parent / "vendor/ranking.py").read_bytes()).hexdigest() == "f80ca634f97f47876329d6418ce7a852a20a8844cc4b5eec1a4900e4c219304f"

original_reader = primary.read_cohort

def joint_reader(artifact):
    profiles, numeric, audit = original_reader(artifact)
    mapping = pd.read_csv(artifact / "publication_mapping.csv").set_index("formulation")
    for profile in profiles:
        profile["group"] = str(mapping.loc[profile["id"], "joint_group"])
    audit["eligible_joint_drug_publication_groups"] = len({p["group"] for p in profiles})
    audit["publication_grouping"] = "joint connected components: shared drug identity OR official DOI"
    primary.dump(artifact / "cohort_audit.json", audit)
    return profiles, numeric, audit

primary.read_cohort = joint_reader
primary.ROOT = HERE
primary.CONFIG = json.loads((HERE / "protocol.json").read_text())

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["prepare", "full", "rerun"])
    ap.add_argument("--artifacts", type=Path, required=True)
    args = ap.parse_args()
    if args.mode == "prepare":
        primary.prepare(args.artifacts)
        folds = pd.read_csv(args.artifacts / "splits.csv")
        mapping = pd.read_csv(args.artifacts / "publication_mapping.csv").set_index("formulation")
        primary_splits = pd.read_csv(args.artifacts.parent / "plga-prefix-20261017-artifacts/splits.csv")
        drug = primary_splits[primary_splits["repeat"] == 0].set_index("formulation")["group"].to_dict()
        for repeat in range(3):
            for fold in range(5):
                cut = folds[folds["repeat"] == repeat]
                train = cut[cut.fold != fold].formulation.tolist()
                test = cut[cut.fold == fold].formulation.tolist()
                assert not (set(mapping.loc[train].doi) & set(mapping.loc[test].doi))
                assert not ({drug[i] for i in train} & {drug[i] for i in test})
        primary.dump(args.artifacts / "group_disjointness.json", {"all_15_splits_drug_disjoint": True, "all_15_splits_publication_disjoint": True})
    else:
        primary.run(args.artifacts, args.mode)
