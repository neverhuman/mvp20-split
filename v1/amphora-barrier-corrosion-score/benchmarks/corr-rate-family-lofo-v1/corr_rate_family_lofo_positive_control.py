#!/usr/bin/env python3
"""
Positive control for corr-rate-family-lofo-v1's refutation criterion.
Plants a defect (full random y-shuffle -- classic hostile-null,
destroys ALL true family<->corrosion-rate signal while preserving the
marginal y distribution and all X features unchanged) into a COPY of the
LOFO harness's own input, then re-runs the identical LOFO procedure and
checks whether the pre-registered refutation criterion
(family_weighted_mean_r2<=0 OR majority of eligible families R2<=0)
correctly fires. Does not touch or overwrite the real result files.
"""
import os
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
import sys, json, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import GroupKFold
import corr_rate_family_lofo as base

SEED = 0
MIN_ELIGIBLE_N = base.MIN_ELIGIBLE_N
SHUFFLE_SEED = 12345


def run_lofo(Xc, yc, famc):
    uniq_families = sorted(set(famc.tolist()))
    n_families = len(uniq_families)
    splitter = GroupKFold(n_splits=n_families)
    it = list(splitter.split(Xc, yc, groups=famc))
    per_family = []
    for tr, te in it:
        fam_name = sorted(set(famc[te].tolist()))[0]
        model = HistGradientBoostingRegressor(
            random_state=SEED, max_iter=300, learning_rate=0.05,
            max_depth=None, max_leaf_nodes=31, l2_regularization=1.0,
            early_stopping=False)
        model.fit(Xc[tr], yc[tr])
        pred_te = model.predict(Xc[te])
        _, _, r2 = base.metrics(yc[te], pred_te)
        per_family.append({"family": fam_name, "n_test": int(len(te)), "r2": r2})
    eligible = [d for d in per_family if d["n_test"] >= MIN_ELIGIBLE_N]
    n_eligible = len(eligible)
    fw_mean = float(np.mean([d["r2"] for d in eligible])) if eligible else float("nan")
    n_pos = sum(1 for d in eligible if d["r2"] > 0.0)
    majority_positive = (n_pos > n_eligible / 2.0) if n_eligible else False
    refuted = (fw_mean <= 0.0) or (not majority_positive)
    return {
        "per_family": sorted(per_family, key=lambda d: -d["n_test"]),
        "n_eligible": n_eligible,
        "family_weighted_mean_r2": fw_mean,
        "n_eligible_positive": n_pos,
        "majority_positive": majority_positive,
        "refuted": refuted,
    }


def main():
    rows, src_sha, n_raw = base.load()
    X, y, mats, envs, has_comp = base.build_matrix(rows)
    fam_list = [base.classify_family(m) for m in mats]
    classified_mask = np.array([f is not None for f in fam_list])
    families_all = np.array([f if f is not None else "unclassified" for f in fam_list])
    Xc = X[classified_mask]
    yc = y[classified_mask]
    famc = families_all[classified_mask]

    # ---- REAL input (must NOT fire refutation, per this fire's main run) ----
    real_result = run_lofo(Xc, yc, famc)

    # ---- PLANTED DEFECT: full random shuffle of yc (hostile null) ----
    rng = np.random.RandomState(SHUFFLE_SEED)
    yc_shuffled = yc.copy()
    rng.shuffle(yc_shuffled)
    defect_result = run_lofo(Xc, yc_shuffled, famc)

    out = {
        "schema": "amphora.barrier-corrosion-score.corr-rate-family-lofo-positive-control.v1",
        "planted_defect": "full random permutation (numpy RandomState seed=12345) of the "
                           "log10(corrosion_rate) label vector yc across all 7282 classified "
                           "rows -- a classic hostile-null y-shuffle -- while every X feature "
                           "(composition vector, environment features, temperature) and every "
                           "family assignment is left byte-identical to the real input.",
        "how_planted": "np.random.RandomState(12345).shuffle(yc) applied to a copy of the "
                        "identical yc array used by corr_rate_family_lofo.py's real run; Xc "
                        "and famc untouched.",
        "real_input": {
            "family_weighted_mean_r2": real_result["family_weighted_mean_r2"],
            "n_eligible_positive": real_result["n_eligible_positive"],
            "n_eligible": real_result["n_eligible"],
            "majority_positive": real_result["majority_positive"],
            "refuted": real_result["refuted"],
        },
        "defect_input": {
            "family_weighted_mean_r2": defect_result["family_weighted_mean_r2"],
            "n_eligible_positive": defect_result["n_eligible_positive"],
            "n_eligible": defect_result["n_eligible"],
            "majority_positive": defect_result["majority_positive"],
            "refuted": defect_result["refuted"],
            "per_family_r2": defect_result["per_family"],
        },
        "detected": bool(defect_result["refuted"] and not real_result["refuted"]),
    }
    txt = json.dumps(out, indent=2, sort_keys=True)
    open(sys.argv[1] if len(sys.argv) > 1 else "positive_control.json", "w").write(txt)
    print("real_refuted", real_result["refuted"], "real_fw_mean_r2", round(real_result["family_weighted_mean_r2"], 4))
    print("defect_refuted", defect_result["refuted"], "defect_fw_mean_r2", round(defect_result["family_weighted_mean_r2"], 4))
    print("detected", out["detected"])


if __name__ == "__main__":
    main()
