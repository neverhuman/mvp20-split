#!/usr/bin/env python3
"""
Positive control for corr-rate-feature-integrity-v1's refutation criterion
(REFUTED if corrected-feature family_safe R2<=0.0 OR
error_reduction_vs_best_baseline_pct<=0.0). Plants a full random y-shuffle
(classic hostile-null -- destroys ALL true feature<->corrosion-rate signal
while preserving the marginal y distribution and every X feature, including
the corrected marine flag, unchanged) into a COPY of the attack's own
corrected-feature input, then re-runs the identical family-safe GroupKFold
procedure and checks whether the pre-registered criterion correctly fires.
Does not touch or overwrite the real result files.
"""
import os
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
import sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import corr_rate_feature_integrity as attack

SEED = 0
SHUFFLE_SEED = 12345


def err_red(gbm_rmse, base_rmse):
    return 100.0 * (1.0 - gbm_rmse / base_rmse) if base_rmse > 0 else float("nan")


def eval_input(Xc, yc, matsc, famc):
    res = attack.run_family_safe(Xc, yc, matsc, famc)
    best_base = min(res["baseline_global_mean"]["rmse"], res["baseline_group_mean"]["rmse"])
    er = err_red(res["gbm"]["rmse"], best_base)
    refuted = (res["gbm"]["r2"] <= 0.0) or (er <= 0.0)
    return {
        "r2": res["gbm"]["r2"],
        "error_reduction_vs_best_baseline_pct": er,
        "refuted": bool(refuted),
    }


def main():
    rows, src_sha, n_raw = attack.base.load()
    X_fixed, y, mats, envs, _ = attack.build_matrix(rows, attack.env_features_corrected)
    fam_list = [attack.base.classify_family(m) for m in mats]
    classified_mask = np.array([f is not None for f in fam_list])
    families_all = np.array([f if f is not None else "unclassified" for f in fam_list])
    Xc = X_fixed[classified_mask]
    yc = y[classified_mask]
    matsc = mats[classified_mask]
    famc = families_all[classified_mask]

    # ---- REAL input: corrected features, real labels (must NOT fire) ----
    real_result = eval_input(Xc, yc, matsc, famc)

    # ---- PLANTED DEFECT: full random shuffle of yc (hostile null) ----
    rng = np.random.RandomState(SHUFFLE_SEED)
    yc_shuffled = yc.copy()
    rng.shuffle(yc_shuffled)
    defect_result = eval_input(Xc, yc_shuffled, matsc, famc)

    out = {
        "schema": "amphora.barrier-corrosion-score.corr-rate-feature-integrity-positive-control.v1",
        "planted_defect": "full random permutation (numpy RandomState seed=12345) of the "
                           "log10(corrosion_rate) label vector yc across all classified rows "
                           "-- a classic hostile-null y-shuffle -- while every X feature "
                           "(composition vector, corrected env features including the fixed "
                           "marine flag, temperature) and every family assignment is left "
                           "byte-identical to the real (corrected-feature) input.",
        "how_planted": "np.random.RandomState(12345).shuffle(yc) applied to a copy of the "
                        "identical yc array used by corr_rate_feature_integrity.py's real "
                        "corrected-feature run; Xc (incl. corrected marine flag) and famc "
                        "untouched.",
        "real_input": real_result,
        "defect_input": defect_result,
        "detected": bool(defect_result["refuted"] and not real_result["refuted"]),
    }
    txt = json.dumps(out, indent=2, sort_keys=True)
    open(sys.argv[1] if len(sys.argv) > 1 else "positive_control.json", "w").write(txt)
    print("real_refuted", real_result["refuted"], "real_r2", round(real_result["r2"], 4))
    print("defect_refuted", defect_result["refuted"], "defect_r2", round(defect_result["r2"], 4))
    print("detected", out["detected"])


if __name__ == "__main__":
    main()
