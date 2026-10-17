#!/usr/bin/env python3
"""Locked real-data prefix benchmark. No remote services, tuning, or future features."""
import os
for _key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_key] = "1"
import argparse
import datetime as dt
import hashlib
import importlib.metadata
import json
import platform
import resource
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "vendor"))
from ranking import CandidateScore, ObjectiveSpace

MODELS = ("persistence", "linear", "higuchi", "first_order", "amphora_pareto", "rf", "hist_gradient_boosting", "rf_amphora")
FAMILIES = MODELS[:4]
CONFIG = json.loads((ROOT / "protocol.json").read_text())

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")

def emit(event, **kwargs):
    print(json.dumps({"event": event, "utc": dt.datetime.now(dt.timezone.utc).isoformat(), **kwargs}, allow_nan=False), flush=True)

def read_cohort(artifact):
    features = pd.read_excel(artifact / "raw/mp_dataset_processed_no_dupes.xlsx")
    obs = pd.read_excel(artifact / "raw/mp_dataset_processed_time_release_only.xlsx")
    assert len(features) == 321 and len(obs) == 4913
    assert features["Formulation Index"].is_unique
    low, high = CONFIG["valid_release_range"]
    valid = (np.isfinite(obs.Time) & np.isfinite(obs.Release) & (obs.Time >= 0) & obs.Release.between(low, high))
    excluded_rows = obs.loc[~valid].copy()
    excluded_rows["reason"] = "nonfinite, negative time or release outside locked digitization tolerance"
    excluded_rows.to_csv(artifact / "excluded_observations.csv", index=False)
    clean = obs.loc[valid].groupby(["Formulation Index", "Time"], as_index=False).Release.mean()
    parent = {int(i): int(i) for i in features["Formulation Index"]}
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    def union(a, b):
        a, b = find(a), find(b)
        if a != b: parent[max(a, b)] = min(a, b)
    smiles_seen, descriptor_seen = {}, {}
    for _, row in features.iterrows():
        i = int(row["Formulation Index"])
        s = str(row["Drug SMILES"]).strip()
        descriptor = tuple(round(float(row[c]), 6) for c in ("Drug MW", "Drug TPSA", "Drug LogP"))
        for seen, key in ((smiles_seen, s), (descriptor_seen, descriptor)):
            if key in seen: union(i, seen[key])
            else: seen[key] = i
    features["group"] = ["drug-%04d" % find(int(i)) for i in features["Formulation Index"]]
    numeric = [c for c in features.select_dtypes(include=np.number).columns if c != "Formulation Index"]
    profiles, exclusions = [], []
    for _, row in features.iterrows():
        i = int(row["Formulation Index"])
        points = clean[clean["Formulation Index"] == i].sort_values("Time")
        if len(points) < CONFIG["minimum_distinct_timepoints"]:
            exclusions.append({"formulation": i, "reason": "fewer_than_five_valid_distinct_times", "n": len(points)})
            continue
        profiles.append({"id": i, "group": row["group"], "t": points.Time.to_numpy(float), "y": points.Release.to_numpy(float),
                         "static": {c: float(row[c]) for c in numeric}, "method": str(row["Formulation Method"])})
    pd.DataFrame(exclusions, columns=["formulation", "reason", "n"]).to_csv(artifact / "excluded_profiles.csv", index=False)
    clean.to_csv(artifact / "normalized_observations.csv", index=False)
    audit = {"original_formulations": len(features), "original_timepoints": len(obs), "eligible_formulations": len(profiles),
             "eligible_drug_groups": len({p["group"] for p in profiles}), "eligible_timepoints": sum(len(p["t"]) for p in profiles),
             "tail_timepoints": sum(len(p["t"]) - 3 for p in profiles), "invalid_observations": int((~valid).sum()),
             "duplicate_time_rows_collapsed": int(valid.sum() - len(clean)), "excluded_profiles": len(exclusions),
             "prefix_end_day_quantiles": np.quantile([p["t"][2] for p in profiles], [0, .25, .5, .75, 1]).tolist(),
             "numeric_static_features": numeric, "time_unit": "days", "release_unit": "fraction", "publication_grouping": "unresolved"}
    dump(artifact / "cohort_audit.json", audit)
    return profiles, numeric, audit

def kinetic(name, t, y, query):
    t, y, query = np.asarray(t), np.asarray(y), np.asarray(query)
    anchor = float(np.clip(y[0], 0, 1)); last = float(np.clip(y[-1], 0, 1))
    if name == "persistence": result = np.full(query.shape, last)
    elif name in ("linear", "higuchi"):
        x = t - t[0] if name == "linear" else np.sqrt(t) - np.sqrt(t[0])
        q = query - t[0] if name == "linear" else np.sqrt(query) - np.sqrt(t[0])
        slope = max(0., float(x @ (y - anchor) / max(float(x @ x), 1e-12)))
        result = np.maximum(last, anchor + slope * q)
    else:
        x = t - t[0]
        remaining = np.clip((1 - y) / max(1 - anchor, 1e-8), 1e-8, 1)
        k = max(0., float(-x @ np.log(remaining) / max(float(x @ x), 1e-12)))
        result = np.maximum(last, 1 - (1 - anchor) * np.exp(-k * np.maximum(0, query - t[0])))
    return np.clip(result, 0, 1)

def representation(p):
    t, y = p["t"][:3], p["y"][:3]
    scores = tuple(CandidateScore(name, (float(abs(kinetic(name, t[:2], y[:2], t[2:3])[0] - y[2])), float(name != "persistence")), 0.) for name in FAMILIES)
    ranks = ObjectiveSpace(("minimize", "minimize")).select(scores, len(scores))
    front = tuple(r.candidate_id for r in ranks.ranks if r.front == 0)
    return {"front": front, "scores": [{"family": s.candidate_id, "prefix_holdout_mae": s.objectives[0], "complexity": s.objectives[1]} for s in scores]}

def rows_for(p, numeric):
    # Only first-three y values are ever read here. Future labels are not an argument to kinetic fits.
    t, y, query = p["t"][:3], p["y"][:3], p["t"][3:]
    rep = representation(p)
    predictions = {name: kinetic(name, t, y, query) for name in FAMILIES}
    front_values = np.stack([predictions[n] for n in rep["front"]])
    predictions["amphora_pareto"] = front_values.mean(axis=0)
    records = []
    for j, day in enumerate(query):
        r = {c: p["static"][c] for c in numeric}
        r.update(method=p["method"], query_day=float(day), query_log_day=float(np.log1p(day)), elapsed_day=float(day - t[-1]),
                 prefix_duration=float(t[-1] - t[0]), prefix_mean=float(y.mean()), prefix_last=float(y[-1]),
                 prefix_slope=float((y[-1] - y[0]) / max(t[-1] - t[0], 1e-12)))
        r.update({"t%d" % k: float(t[k]) for k in range(3)})
        r.update({"y%d" % k: float(y[k]) for k in range(3)})
        r.update(amphora_mean=float(front_values[:, j].mean()), amphora_std=float(front_values[:, j].std()), amphora_front_size=float(len(rep["front"])))
        records.append(r)
    return pd.DataFrame(records), predictions, rep

def prepare(artifact):
    artifact.mkdir(exist_ok=True)
    profiles, numeric, audit = read_cohort(artifact)
    groups = sorted({p["group"] for p in profiles})
    assignments = []
    for repeat, seed in enumerate(CONFIG["seeds"]):
        order = np.array(groups); np.random.default_rng(seed).shuffle(order)
        mapping = {str(g): j % CONFIG["folds"] for j, g in enumerate(order)}
        assignments.extend({"repeat": repeat, "seed": seed, "fold": mapping[p["group"]], "formulation": p["id"], "group": p["group"]} for p in profiles)
    pd.DataFrame(assignments).to_csv(artifact / "splits.csv", index=False)
    env = {"utc": dt.datetime.now(dt.timezone.utc).isoformat(), "python": sys.version, "platform": platform.platform(),
           "packages": {p: importlib.metadata.version(p) for p in ["numpy", "pandas", "scikit-learn", "scipy", "openpyxl", "matplotlib", "joblib", "threadpoolctl"]},
           "cpu_affinity": sorted(os.sched_getaffinity(0)), "thread_environment": {k: os.environ[k] for k in ["OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"]}}
    dump(artifact / "environment.json", env)
    (ROOT / "requirements.lock").write_text("\n".join(k + "==" + v for k, v in env["packages"].items()) + "\n")
    code = {str(p.relative_to(ROOT)): sha(p) for p in sorted(ROOT.rglob("*")) if p.is_file() and "__pycache__" not in str(p) and p.suffix != ".pyc"}
    lock = {"created_utc": env["utc"], "protocol_sha256": sha(ROOT / "protocol.json"), "splits_sha256": sha(artifact / "splits.csv"), "code_sha256": code,
            "sources_sha256": sha(artifact / "sources.json"), "cohort": audit}
    dump(artifact / "experiment_lock.json", lock)
    emit("locked_before_scoring", **lock)

def run(artifact, mode):
    lock = json.loads((artifact / "experiment_lock.json").read_text())
    assert lock["protocol_sha256"] == sha(ROOT / "protocol.json") and lock["splits_sha256"] == sha(artifact / "splits.csv")
    for path, digest in lock["code_sha256"].items(): assert sha(ROOT / path) == digest, path
    profiles, numeric, audit = read_cohort(artifact)
    folds = pd.read_csv(artifact / "splits.csv")
    out = artifact / mode; out.mkdir(exist_ok=False)
    tables, preds, receipts = {}, {}, []
    for p in profiles:
        tables[p["id"]], preds[p["id"]], r = rows_for(p, numeric)
        receipts.append({"formulation": p["id"], **r})
    dump(out / "selection_receipts.json", receipts)
    all_predictions, checks, timings = [], [], []
    for repeat in range(1 if mode != "full" else len(CONFIG["seeds"])):
        for fold in range(1 if mode != "full" else CONFIG["folds"]):
            start = time.monotonic(); assignment = folds[folds["repeat"] == repeat].set_index("formulation")
            train = [p for p in profiles if int(assignment.loc[p["id"], "fold"]) != fold]
            test = [p for p in profiles if int(assignment.loc[p["id"], "fold"]) == fold]
            assert not ({p["group"] for p in train} & {p["group"] for p in test})
            X = pd.concat([tables[p["id"]] for p in train], ignore_index=True)
            yt = np.concatenate([p["y"][3:] for p in train])
            weights = np.concatenate([np.full(len(p["t"]) - 3, 1 / (len(p["t"]) - 3)) for p in train])
            models = {}
            for name in ("rf", "hist_gradient_boosting", "rf_amphora"):
                cols = [c for c in X.columns if name == "rf_amphora" or not c.startswith("amphora_")]
                numcols = [c for c in cols if c != "method"]
                pre = ColumnTransformer([("numeric", SimpleImputer(strategy="median"), numcols), ("method", OneHotEncoder(handle_unknown="ignore", sparse_output=False), ["method"])])
                model = RandomForestRegressor(**CONFIG["rf"]) if name != "hist_gradient_boosting" else HistGradientBoostingRegressor(**CONFIG["boosting"])
                pipe = Pipeline([("preprocessing", pre), ("model", model)])
                pipe.fit(X[cols], yt, model__sample_weight=weights)
                models[name] = (pipe, cols)
            for p in test:
                table = tables[p["id"]]
                estimates = dict(preds[p["id"]])
                for name, (model, cols) in models.items(): estimates[name] = np.clip(model.predict(table[cols]), 0, 1)
                perturbed = {**p, "y": p["y"].copy()}; perturbed["y"][3:] = 1 - perturbed["y"][3:][::-1]
                changed_x, changed_pred, changed_rep = rows_for(perturbed, numeric)
                assert table.equals(changed_x), "held-out-tail feature leakage"
                for name in FAMILIES + ("amphora_pareto",): assert np.array_equal(estimates[name], changed_pred[name])
                for name, (model, cols) in models.items(): assert np.array_equal(estimates[name], np.clip(model.predict(changed_x[cols]), 0, 1))
                control = {**p, "y": p["y"].copy()}; control["y"][0] += .01
                assert not table.equals(rows_for(control, numeric)[0]), "invariance harness lacks positive control"
                checks.append({"repeat": repeat, "fold": fold, "formulation": p["id"], "future_tail_invariance": True, "prefix_positive_control": True})
                for name, prediction in estimates.items():
                    assert np.isfinite(prediction).all()
                    all_predictions.extend({"repeat": repeat, "fold": fold, "formulation": p["id"], "group": p["group"], "model": name,
                                            "time_day": float(t), "prefix_end_day": float(p["t"][2]), "observed_release": float(y), "predicted_release": float(z)}
                                           for t, y, z in zip(p["t"][3:], p["y"][3:], prediction))
            elapsed = time.monotonic() - start
            current = pd.DataFrame([x for x in all_predictions if x["repeat"] == repeat and x["fold"] == fold])
            current["ae_pp"] = 100 * (current.observed_release - current.predicted_release).abs()
            metrics = current.groupby(["model", "formulation"]).ae_pp.mean().groupby("model").mean().to_dict()
            timing = {"repeat": repeat, "fold": fold, "seconds": elapsed, "train_profiles": len(train), "test_profiles": len(test),
                      "train_groups": len({p["group"] for p in train}), "test_groups": len({p["group"] for p in test}), "test_points": sum(len(p["t"]) - 3 for p in test)}
            timings.append(timing); emit("fold_result", mode=mode, **timing, curve_mae_pp=metrics)
    result = pd.DataFrame(all_predictions)
    result.to_csv(out / "predictions.csv", index=False, float_format="%.17g")
    result["ae_pp"] = 100 * (result.observed_release - result.predicted_release).abs()
    result["se_pp2"] = (100 * (result.observed_release - result.predicted_release)) ** 2
    curve = result.groupby(["repeat", "fold", "formulation", "group", "model"], as_index=False).agg(mae_pp=("ae_pp", "mean"), mse_pp2=("se_pp2", "mean"))
    curve["rmse_pp"] = np.sqrt(curve.mse_pp2); curve.to_csv(out / "curve_metrics.csv", index=False)
    summary = curve.groupby("model").agg(curve_mae_pp=("mae_pp", "mean"), mean_curve_rmse_pp=("rmse_pp", "mean"), profile_evaluations=("formulation", "count")).reset_index()
    summary.to_csv(out / "summary.csv", index=False)
    pd.DataFrame(checks).to_csv(out / "leakage_checks.csv", index=False); dump(out / "timing.json", timings)
    dump(out / "run_record.json", {"protocol_sha256": lock["protocol_sha256"], "split_sha256": lock["splits_sha256"], "predictions_sha256": sha(out / "predictions.csv"),
                                   "peak_rss_mib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, "seconds": sum(x["seconds"] for x in timings), "failed_models": [], "status": "complete"})
    emit("run_complete", mode=mode, summary=summary.to_dict("records"), predictions_sha256=sha(out / "predictions.csv"))

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("mode", choices=["prepare", "pilot", "full", "rerun"]); ap.add_argument("--artifacts", type=Path, required=True)
    a = ap.parse_args()
    if a.mode == "prepare": prepare(a.artifacts)
    else: run(a.artifacts, a.mode)
