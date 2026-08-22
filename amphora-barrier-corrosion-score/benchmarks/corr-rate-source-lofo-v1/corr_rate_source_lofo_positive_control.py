#!/usr/bin/env python3
"""
Positive control for corr-rate-source-lofo-v1's refutation criterion.
Plants a defect (full random y-shuffle -- classic hostile-null, destroys
ALL true source<->corrosion-rate signal while preserving the marginal y
distribution and all X features/source assignments unchanged) into a COPY
of the LOSO harness's own input, then re-runs the identical LOSO procedure
and checks whether the pre-registered refutation criterion
(source_weighted_mean_r2<=0 OR majority of eligible sources R2<=0)
correctly fires. Does not touch or overwrite the real result files.
"""
import os
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
import sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import corr_rate_source_lofo as base

SEED = 0
MIN_ELIGIBLE_N = base.MIN_ELIGIBLE_N
SHUFFLE_SEED = 12345


def main():
    rows, src_sha, n_raw = base.load()
    X, y, mats, envs, srcs, has_comp = base.build_matrix(rows)
    fam_list = [base.classify_family(m) for m in mats]
    classified_mask = np.array([f is not None for f in fam_list])
    Xc = X[classified_mask]
    yc = y[classified_mask]
    srcc = srcs[classified_mask]

    # ---- REAL input (must NOT fire refutation, per this fire's main run) ----
    real_result = base.run_loso(Xc, yc, srcc, min_eligible_n=MIN_ELIGIBLE_N, seed=SEED)

    # ---- PLANTED DEFECT: full random shuffle of yc (hostile null) ----
    rng = np.random.RandomState(SHUFFLE_SEED)
    yc_shuffled = yc.copy()
    rng.shuffle(yc_shuffled)
    defect_result = base.run_loso(Xc, yc_shuffled, srcc, min_eligible_n=MIN_ELIGIBLE_N, seed=SEED)

    out = {
        "schema": "amphora.barrier-corrosion-score.corr-rate-source-lofo-positive-control.v1",
        "planted_defect": "full random permutation (numpy RandomState seed=12345) of the "
                           "log10(corrosion_rate) label vector yc across all classified rows "
                           "-- a classic hostile-null y-shuffle -- while every X feature "
                           "(composition vector, environment features, temperature) and every "
                           "source_text assignment is left byte-identical to the real input.",
        "how_planted": "np.random.RandomState(12345).shuffle(yc) applied to a copy of the "
                        "identical yc array used by corr_rate_source_lofo.py's real run; Xc "
                        "and srcc untouched.",
        "real_input": {
            "source_weighted_mean_r2": real_result["source_weighted_mean_r2"],
            "n_eligible_positive": real_result["n_eligible_sources_r2_positive"],
            "n_eligible": real_result["eligible_sources_n_test_ge_min"],
            "majority_positive": real_result["majority_of_eligible_sources_positive"],
            "refuted": real_result["refuted"],
        },
        "defect_input": {
            "source_weighted_mean_r2": defect_result["source_weighted_mean_r2"],
            "n_eligible_positive": defect_result["n_eligible_sources_r2_positive"],
            "n_eligible": defect_result["eligible_sources_n_test_ge_min"],
            "majority_positive": defect_result["majority_of_eligible_sources_positive"],
            "refuted": defect_result["refuted"],
        },
        "detected": bool(defect_result["refuted"] and not real_result["refuted"]),
    }
    txt = json.dumps(out, indent=2, sort_keys=True)
    open(sys.argv[1] if len(sys.argv) > 1 else "positive_control.json", "w").write(txt)
    print("real_refuted", real_result["refuted"], "real_sw_mean_r2", round(real_result["source_weighted_mean_r2"], 4))
    print("defect_refuted", defect_result["refuted"], "defect_sw_mean_r2", round(defect_result["source_weighted_mean_r2"], 4))
    print("detected", out["detected"])


if __name__ == "__main__":
    main()
