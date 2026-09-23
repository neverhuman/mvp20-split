#!/usr/bin/env python3
"""
amphora-barrier-corrosion-score / corr-rate-feature-integrity-v1
FALSIFICATION ATTACK on the promoted KPI
evidence/phase0/kpis/corr-rate-family-safe-qspr-kpi.v1.dsse.json
(GroupKFold(group=metallurgical_family, 5-fold) HistGBM R2=0.132087,
n=7282 classified NIST CORR-DATA rows, 17 families).

BACKGROUND. The 2026-08-15 corr-rate-marine-envelope-v1 attack
(CLAIM_REFUTED on marine generalization) co-discovered a data-integrity
defect in this module's OWN feature engineering: the deployed
`env_features()` (verbatim in corr_rate_qspr.py / corr_rate_family_safe.py
/ corr_rate_family_lofo.py) computes
    marine = has("seawater", "sea water", "marine", "atmospheric")
which conflates two physically distinct corrosion regimes -- true
seawater/marine immersion and atmospheric exposure -- under one binary
flag. Of the 499 classified rows with marine_feature==1, 313 (62.7%) are
actually atmospheric-exposure rows, not seawater. That prior attack only
quantified the bug's effect on a marine-only train/test SPLIT. It never
asked whether this defect is baked into the promoted KPI's OWN feature
matrix -- because `marine` is one of the 13 env features that
`build_matrix()` feeds into the SAME GroupKFold(family) HistGBM pipeline
that produced R2=0.132087. Every prior attack on this KPI (family-safe-v1,
family-lofo-v1, marine-envelope-v1) varied the CV grouping axis or the
train/test split; NONE has ever held the split fixed and asked whether the
promoted number is fragile to fixing a known, quantified defect in its own
input features.

ATTACK. Re-run the IDENTICAL feature engineering (comp_vector), model
(HistGradientBoostingRegressor), seed (SEED=0), CV scheme
(GroupKFold(group=metallurgical_family), same classify_family() rules),
and metrics as corr-rate-family-safe-v1/corr_rate_family_safe.py verbatim,
changing ONLY env_features()'s `marine` flag to
    marine_corrected = has("seawater", "sea water") only
(dropping the erroneous "marine" and "atmospheric" substring matches),
on the IDENTICAL classified-subset rows.

PRE-REGISTERED REFUTATION CRITERION (declared before running, mirrors the
original corr-rate-family-safe-v1 bar so the two are directly comparable):
REFUTED if corrected-feature family_safe GBM R2 <= 0.0 OR
corrected-feature family_safe error_reduction_vs_best_baseline_pct <= 0.0
on the identical classified-subset rows/model/seed/CV as the promoted KPI.
SURVIVED otherwise, even if R2 changes materially relative to the
buggy-feature promoted number -- a bounded, non-catastrophic change is
disclosed but is not itself a refutation, consistent with the "reduced but
still positive" survival standard already used by family-safe-v1 and
family-lofo-v1 for this exact KPI.

Determinism: OMP_NUM_THREADS=1, fixed seed, GroupKFold (no shuffle),
rounded canonical output -> byte-stable two-replay SHA-256 gate.
"""
import os
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
import json, hashlib, math, sys, re
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import GroupKFold
import sklearn

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "..", "corr-rate-family-safe-v1"))
import corr_rate_family_safe as base

SEED = 0
NDEC = 6


def env_features_corrected(env):
    """IDENTICAL to base.env_features() except the `marine` flag is
    restricted to true seawater/marine-immersion substrings, dropping the
    erroneous 'marine' and 'atmospheric' substring matches that conflate
    atmospheric exposure with seawater immersion (313/499 = 62.7% of
    deployed marine_feature==1 rows per corr-rate-marine-envelope-v1)."""
    e = env.lower()
    def has(*ws): return float(any(w in e for w in ws))
    chloride = has("chlor", "hcl", "seawater", "sea water", "brine", "muriatic")
    fluoride = has("fluor", "hf ")
    bromide = has("brom")
    halide = float(bool(chloride or fluoride or bromide or has("iodide", "iodine")))
    ox_acid = has("nitric", "chromic", "ferric chlor", "hypochlor", "perchlor",
                  "nitrate", "peroxide", "permanganat")
    red_acid = has("hydrochloric", "hydrofluoric", "phosphoric", "formic",
                   "acetic", "sulfurous", "sulphurous", "hydrobromic", "oxalic",
                   "tartaric", "citric", "lactic")
    org_acid = has("acetic", "formic", "oxalic", "tartaric", "citric", "lactic",
                   "propionic", "butyric", "maleic")
    sulfuric = has("sulfuric", "sulphuric")
    alkali = has("hydroxide", "ammoni", "amine", "carbonate", "caustic", "koh",
                 "naoh", "lime")
    marine_corrected = has("seawater", "sea water")  # FIX: dropped "marine", "atmospheric"
    salt = has("chloride", "sulfate", "sulphate", "nitrate", "bromide",
               "carbonate", "phosphate", "acetate") and not (ox_acid or red_acid)
    water = float(e.strip() in ("water", "distilled water", "fresh water",
                                "deionized water"))
    is_acid = float(bool(ox_acid or red_acid or sulfuric or "acid" in e))
    return [chloride, fluoride, bromide, halide, ox_acid, red_acid, org_acid,
            sulfuric, alkali, marine_corrected, salt, water, is_acid]


def build_matrix(rows, env_fn):
    X, y, mats, envs, has_comp = [], [], [], [], 0
    for mat, env, temp, ly in rows:
        cv, ok = base.comp_vector(mat)
        has_comp += int(ok)
        ev = env_fn(env)
        tnum = float(temp) if temp is not None else float("nan")
        tmiss = 0.0 if temp is not None else 1.0
        X.append(cv + ev + [tnum, tmiss])
        y.append(ly)
        mats.append(mat)
        envs.append(env)
    return (np.array(X, dtype=float), np.array(y, dtype=float),
            np.array(mats), np.array(envs), has_comp)


def run_family_safe(Xc, yc, matsc, famc):
    res, _ = base.run_cv(Xc, yc, matsc, np.array([""] * len(yc)), famc, "family_safe")
    return res


def rnd(o):
    if isinstance(o, float):
        if math.isnan(o):
            return None
        return round(o, NDEC)
    if isinstance(o, dict):
        return {k: rnd(o[k]) for k in sorted(o)}
    if isinstance(o, list):
        return [rnd(v) for v in o]
    return o


def err_red(gbm_rmse, base_rmse):
    return 100.0 * (1.0 - gbm_rmse / base_rmse) if base_rmse > 0 else float("nan")


def main():
    rows, src_sha, n_raw = base.load()

    # Feature matrix using DEPLOYED (buggy) env_features -- reference only.
    X_buggy, y, mats, envs, _ = build_matrix(rows, base.env_features)
    # Feature matrix using CORRECTED marine flag -- this fire's real attack input.
    X_fixed, y2, mats2, envs2, _ = build_matrix(rows, env_features_corrected)
    assert np.array_equal(y, y2) and list(mats) == list(mats2)

    fam_list = [base.classify_family(m) for m in mats]
    classified_mask = np.array([f is not None for f in fam_list])
    families_all = np.array([f if f is not None else "unclassified" for f in fam_list])
    n = len(y)
    n_classified = int(classified_mask.sum())

    Xc_buggy = X_buggy[classified_mask]
    Xc_fixed = X_fixed[classified_mask]
    yc = y[classified_mask]
    matsc = mats[classified_mask]
    famc = families_all[classified_mask]
    n_families = int(len(set(famc.tolist())))

    n_marine_flag_changed = int(np.sum(Xc_buggy[:, 9] != Xc_fixed[:, 9]))

    res_buggy = run_family_safe(Xc_buggy, yc, matsc, famc)
    res_fixed = run_family_safe(Xc_fixed, yc, matsc, famc)

    best_base_buggy = min(res_buggy["baseline_global_mean"]["rmse"],
                           res_buggy["baseline_group_mean"]["rmse"])
    best_base_fixed = min(res_fixed["baseline_global_mean"]["rmse"],
                           res_fixed["baseline_group_mean"]["rmse"])
    err_red_buggy = err_red(res_buggy["gbm"]["rmse"], best_base_buggy)
    err_red_fixed = err_red(res_fixed["gbm"]["rmse"], best_base_fixed)

    refutation_criterion = (
        "REFUTED if corrected_feature.family_safe.gbm.r2 <= 0.0 OR "
        "corrected_feature.family_safe_error_reduction_vs_best_baseline_pct "
        "<= 0.0 (identical classified-subset rows/model/seed/CV as the "
        "promoted corr-rate-family-safe-qspr-kpi.v1); SURVIVED otherwise, "
        "even if r2 changes materially relative to the buggy-feature "
        "promoted number."
    )
    refuted = (res_fixed["gbm"]["r2"] <= 0.0) or (err_red_fixed <= 0.0)
    verdict = "CLAIM_REFUTED" if refuted else "CLAIM_SURVIVED"

    canonical = {
        "schema": "amphora.barrier-corrosion-score.corr-rate-feature-integrity-attack.v1",
        "benchmark": "amphora-barrier-corrosion-score/corr-rate-feature-integrity-v1",
        "attacks_claim": (
            "evidence/phase0/kpis/corr-rate-family-safe-qspr-kpi.v1.dsse.json "
            "(GroupKFold(group=metallurgical_family, 5-fold) HistGBM "
            "R2=0.132087, promoted 2026-08-04, campaign item V1-KPI-BARR, "
            "'the module's strongest rights-clean empirical claim')."
        ),
        "attack_description": (
            "corr-rate-marine-envelope-v1 (2026-08-15) co-discovered that "
            "the deployed env_features() 'marine' flag conflates seawater "
            "immersion with atmospheric exposure (has('seawater','sea "
            "water','marine','atmospheric')): 313/499 (62.7%) of deployed "
            "marine_feature==1 rows are actually atmospheric. That flag is "
            "one of the 13 env features consumed by build_matrix() and fed "
            "directly into the SAME GroupKFold(family) HistGBM pipeline "
            "that produced the promoted KPI's R2=0.132087 -- so the defect "
            "was never isolated to the marine-only test split; it is baked "
            "into the promoted KPI's own training features. This re-runs "
            "the identical family-safe pipeline with ONLY the marine flag "
            "corrected (restricted to true seawater/sea-water substrings) "
            "and compares to the deployed (buggy) feature result on the "
            "identical rows/model/seed/CV."
        ),
        "refutation_criterion": refutation_criterion,
        "dataset": {
            "name": "NIST CORR-DATA (Dow Chemical Co.) derived reference",
            "in_tree_path": base.SRC,
            "source_sha256": src_sha,
            "rights_class": "DERIVATIVE_ALLOWED",
            "n_raw_records": n_raw,
        },
        "cohort": {
            "full_cohort_n": n,
            "classified_subset_n": n_classified,
            "n_families_in_classified_subset": n_families,
            "n_marine_flag_values_changed_by_fix": n_marine_flag_changed,
        },
        "results": {
            "deployed_buggy_feature_family_safe": {
                "gbm": res_buggy["gbm"],
                "baseline_global_mean": res_buggy["baseline_global_mean"],
                "baseline_group_mean": res_buggy["baseline_group_mean"],
                "n_folds": res_buggy["n_folds"],
                "per_fold_r2": res_buggy["per_fold"],
                "error_reduction_vs_best_baseline_pct": err_red_buggy,
                "note": "Reference only (reproduces the promoted KPI's own "
                        "pipeline byte-for-byte on the deployed feature "
                        "set) -- NOT the verdict driver.",
            },
            "corrected_feature_family_safe": {
                "gbm": res_fixed["gbm"],
                "baseline_global_mean": res_fixed["baseline_global_mean"],
                "baseline_group_mean": res_fixed["baseline_group_mean"],
                "n_folds": res_fixed["n_folds"],
                "per_fold_r2": res_fixed["per_fold"],
                "error_reduction_vs_best_baseline_pct": err_red_fixed,
                "note": "This fire's real attack input -- verdict driver.",
            },
        },
        "comparison": {
            "r2_buggy": res_buggy["gbm"]["r2"],
            "r2_corrected": res_fixed["gbm"]["r2"],
            "r2_delta_corrected_minus_buggy": res_fixed["gbm"]["r2"] - res_buggy["gbm"]["r2"],
            "corrected_family_safe_r2_positive": bool(res_fixed["gbm"]["r2"] > 0.0),
            "corrected_family_safe_beats_best_baseline_rmse": bool(err_red_fixed > 0.0),
        },
        "verdict": verdict,
        "authority": "AUDIT_ONLY",
        "promotes_authority": False,
        "modifies_manifest": False,
        "scope_honesty": (
            "Diagnostic on bare metal/alloy substrate corrosion (NIST "
            "CORR-DATA), same scope ceiling as corr-rate-family-safe-v1: "
            "NOT organic-coating barrier performance. No candidate/coating "
            "superiority claim."
        ),
        "model": {
            "estimator": "HistGradientBoostingRegressor",
            "params": {"max_iter": 300, "learning_rate": 0.05,
                       "max_leaf_nodes": 31, "l2_regularization": 1.0,
                       "random_state": SEED},
            "sklearn_version": sklearn.__version__,
        },
        "determinism": {"omp_num_threads": os.environ.get("OMP_NUM_THREADS"),
                        "seed": SEED, "canonical_round_decimals": NDEC},
    }
    out = json.dumps(rnd(canonical), indent=2, sort_keys=True)
    open(sys.argv[1] if len(sys.argv) > 1 else "result.json", "w").write(out)
    sha = hashlib.sha256(out.encode()).hexdigest()
    print("CANONICAL_SHA256", sha)
    print("n_classified", n_classified, "n_families", n_families,
          "n_marine_flag_changed", n_marine_flag_changed)
    print("r2_buggy", round(res_buggy["gbm"]["r2"], 4),
          "r2_corrected", round(res_fixed["gbm"]["r2"], 4),
          "err_red_corrected_pct", round(err_red_fixed, 2),
          "verdict", verdict)


if __name__ == "__main__":
    main()
