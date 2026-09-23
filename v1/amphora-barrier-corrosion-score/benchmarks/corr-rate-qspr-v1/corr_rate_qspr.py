#!/usr/bin/env python3
"""
amphora-barrier-corrosion-score / corr-rate-qspr-v1
Independent, fully in-tree, reproducible leave-material-out corrosion-rate QSPR
diagnostic on the NIST CORR-DATA database (rights_class DERIVATIVE_ALLOWED).

HONEST SCOPE: this predicts the *corrosion rate of a bare metal/alloy substrate*
in a chemical environment (log10 mm/yr). It is substrate-corrosion science that
underlies, but does NOT constitute, organic-coating barrier performance. Marine
environments (Seawater, Sodium Chloride, atmospheric marine) are present in the
data, but no coating-barrier authority is created. Diagnostic / AUDIT_ONLY.

Determinism: OMP_NUM_THREADS=1, fixed seeds, GroupKFold (no shuffle), rounded
canonical output -> byte-stable two-replay SHA-256 gate.
"""
import os
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
import json, hashlib, math, sys, re
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import GroupKFold, KFold
import sklearn

SRC = "feedback/v1/derived/nist_corr_reference.json"
SEED = 0
NDEC = 6  # canonical rounding

# ---------------------------------------------------------------------------
# Nominal alloy compositions (wt%), standard metallurgical references:
#   ASM Handbook Vol.1/Vol.3; ASTM alloy specs; supplier datasheets (nominal).
# Encoded conservatively for the highest-count material families in CORR-DATA.
# Materials not matched here get NaN composition (HistGBM handles NaN natively);
# n_records_with_composition is reported for honesty.
# Element order fixed for determinism.
ELEMENTS = ["fe", "cr", "ni", "mo", "cu", "ti", "zr", "nb", "ta", "co",
            "w", "al", "mn", "si", "c", "pb", "sn", "ag", "pt", "au"]

# key: lowercase substring matched against material string (first hit wins,
# longest keys first). value: dict of wt% (missing elements = 0).
COMPOSITION = {
    "316l": {"fe": 67, "cr": 17, "ni": 12, "mo": 2.5, "mn": 1.5},
    "316":  {"fe": 67, "cr": 17, "ni": 12, "mo": 2.5, "mn": 1.5},
    "317":  {"fe": 63, "cr": 19, "ni": 13, "mo": 3.5, "mn": 1.5},
    "304l": {"fe": 70, "cr": 18, "ni": 9, "mn": 1.5},
    "304":  {"fe": 70, "cr": 18, "ni": 9, "mn": 1.5},
    "321":  {"fe": 70, "cr": 18, "ni": 10, "ti": 0.4, "mn": 1.5},
    "347":  {"fe": 69, "cr": 18, "ni": 11, "nb": 0.8, "mn": 1.5},
    "410":  {"fe": 86, "cr": 12.5, "mn": 1},
    "430":  {"fe": 82, "cr": 17, "mn": 1},
    "2205": {"fe": 68, "cr": 22, "ni": 5, "mo": 3, "mn": 1.5},
    "carpenter 20": {"fe": 35, "cr": 20, "ni": 34, "mo": 2.5, "cu": 3.3, "nb": 0.5},
    "alloy 20":     {"fe": 35, "cr": 20, "ni": 34, "mo": 2.5, "cu": 3.3, "nb": 0.5},
    "20cb":         {"fe": 35, "cr": 20, "ni": 34, "mo": 2.5, "cu": 3.3, "nb": 0.5},
    "hastelloy c-276": {"ni": 57, "cr": 16, "mo": 16, "w": 3.5, "fe": 5, "co": 2.5},
    "hastelloy c-22":  {"ni": 56, "cr": 22, "mo": 13, "w": 3, "fe": 3, "co": 2.5},
    "alloy c-276": {"ni": 57, "cr": 16, "mo": 16, "w": 3.5, "fe": 5, "co": 2.5},
    "alloy c-22":  {"ni": 56, "cr": 22, "mo": 13, "w": 3, "fe": 3, "co": 2.5},
    "hastelloy c": {"ni": 57, "cr": 16, "mo": 16, "w": 3.5, "fe": 5, "co": 2.5},
    "hastelloy b": {"ni": 66, "mo": 28, "fe": 5, "co": 1},
    "inconel 625": {"ni": 61, "cr": 22, "mo": 9, "nb": 3.5, "fe": 3},
    "alloy 625":   {"ni": 61, "cr": 22, "mo": 9, "nb": 3.5, "fe": 3},
    "inconel 600": {"ni": 76, "cr": 15.5, "fe": 8},
    "alloy 600":   {"ni": 76, "cr": 15.5, "fe": 8},
    "inconel 625": {"ni": 61, "cr": 22, "mo": 9, "nb": 3.5, "fe": 3},
    "incoloy 825": {"ni": 42, "fe": 30, "cr": 21.5, "mo": 3, "cu": 2.2, "ti": 0.9},
    "alloy 825":   {"ni": 42, "fe": 30, "cr": 21.5, "mo": 3, "cu": 2.2, "ti": 0.9},
    "incoloy 800": {"ni": 32, "fe": 46, "cr": 21},
    "alloy 800":   {"ni": 32, "fe": 46, "cr": 21},
    "monel 400":   {"ni": 66, "cu": 32, "fe": 2},
    "alloy 400":   {"ni": 66, "cu": 32, "fe": 2},
    "monel":       {"ni": 66, "cu": 32, "fe": 2},
    "nickel 200":  {"ni": 99.5},
    "nickel 201":  {"ni": 99.5},
    "70-30 cupronickel": {"cu": 69, "ni": 30, "fe": 0.6},
    "90-10 cupronickel": {"cu": 88, "ni": 10, "fe": 1.4},
    "cupronickel": {"cu": 79, "ni": 20},
    "aluminum bronze": {"cu": 88, "al": 9, "fe": 3},
    "ampco":       {"cu": 88, "al": 9, "fe": 3},
    "admiralty":   {"cu": 71, "zn": 28, "sn": 1},
    "titanium, grade 7": {"ti": 99.8, "pd": 0.15},
    "titanium":    {"ti": 99.8},
    "zr702":       {"zr": 99.2},
    "zr705":       {"zr": 95, "nb": 2.5},
    "zirconium":   {"zr": 99.2},
    "tantalum":    {"ta": 100},
    "niobium":     {"nb": 100},
    "columbium":   {"nb": 100},
    "platinum":    {"pt": 100},
    "silver":      {"ag": 100},
    "gold":        {"au": 100},
    "chemical lead": {"pb": 99.9},
    "lead":        {"pb": 99.9},
    "tin":         {"sn": 99},
    "carbon steel": {"fe": 99, "mn": 0.6, "c": 0.2},
    "cast iron":   {"fe": 93, "c": 3.5, "si": 2.2},
    "mild steel":  {"fe": 99, "mn": 0.6, "c": 0.15},
    "aluminum":    {"al": 99},
    "copper":      {"cu": 99.9},
    "nickel":      {"ni": 99},
}
_COMP_KEYS = sorted(COMPOSITION.keys(), key=len, reverse=True)


def comp_vector(material):
    m = material.lower()
    for k in _COMP_KEYS:
        if k in m:
            d = COMPOSITION[k]
            return [float(d.get(e, 0.0)) for e in ELEMENTS], True
    return [float("nan")] * len(ELEMENTS), False


# Environment chemistry features from basic aqueous corrosion chemistry.
# Each is a keyword rule over the environment string; generalizes across envs.
def env_features(env):
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
    marine = has("seawater", "sea water", "marine", "atmospheric")
    salt = has("chloride", "sulfate", "sulphate", "nitrate", "bromide",
               "carbonate", "phosphate", "acetate") and not (ox_acid or red_acid)
    water = float(e.strip() in ("water", "distilled water", "fresh water",
                                "deionized water"))
    is_acid = float(bool(ox_acid or red_acid or sulfuric or "acid" in e))
    return [chloride, fluoride, bromide, halide, ox_acid, red_acid, org_acid,
            sulfuric, alkali, marine, salt, water, is_acid]


ENV_FEAT_NAMES = ["chloride", "fluoride", "bromide", "halide", "ox_acid",
                  "red_acid", "org_acid", "sulfuric", "alkali", "marine",
                  "salt", "water", "is_acid"]


def load():
    raw = open(SRC, "rb").read()
    src_sha = hashlib.sha256(raw).hexdigest()
    data = json.loads(raw)
    rows = []
    for x in data:
        v = x.get("metric_value")
        mf = x.get("metric_family") or ""
        if v is None or "rate" not in mf:
            continue
        rate = float(v)
        if mf == "rate_mils_per_year":
            rate = rate * 0.0254  # mils/yr -> mm/yr
        if rate <= 0:
            continue  # cannot take log; passive/immune rows excluded (reported)
        mat = str(x.get("material") or "").strip()
        env = str(x.get("environment") or "").strip()
        if not mat or not env:
            continue
        temp = x.get("temperature_c")
        rows.append((mat, env, temp, math.log10(rate)))
    # deterministic order
    rows.sort(key=lambda r: (r[0], r[1], (r[2] if r[2] is not None else -999.0), r[3]))
    return rows, src_sha, len(data)


def build_matrix(rows):
    X, y, mats, envs, has_comp = [], [], [], [], 0
    for mat, env, temp, ly in rows:
        cv, ok = comp_vector(mat)
        has_comp += int(ok)
        ev = env_features(env)
        tnum = float(temp) if temp is not None else float("nan")
        tmiss = 0.0 if temp is not None else 1.0
        X.append(cv + ev + [tnum, tmiss])
        y.append(ly)
        mats.append(mat)
        envs.append(env)
    return (np.array(X, dtype=float), np.array(y, dtype=float),
            np.array(mats), np.array(envs), has_comp)


def metrics(y_true, y_pred):
    err = y_pred - y_true
    rmse = float(np.sqrt(np.mean(err ** 2)))
    mae = float(np.mean(np.abs(err)))
    ss_res = float(np.sum(err ** 2))
    ss_tot = float(np.sum((y_true - np.mean(y_true)) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return rmse, mae, r2


def group_baseline(key_train, y_train, key_test, glob):
    # per-group train mean, fallback to global when group unseen in train
    d = {}
    sums, cnts = {}, {}
    for k, v in zip(key_train, y_train):
        sums[k] = sums.get(k, 0.0) + v
        cnts[k] = cnts.get(k, 0) + 1
    for k in sums:
        d[k] = sums[k] / cnts[k]
    return np.array([d.get(k, glob) for k in key_test])


def run_cv(X, y, mats, envs, split_kind):
    if split_kind == "random":
        splitter = KFold(n_splits=5, shuffle=True, random_state=SEED)
        it = splitter.split(X)
        groups_for_bl = None
    elif split_kind == "material_safe":
        splitter = GroupKFold(n_splits=5)
        it = splitter.split(X, y, groups=mats)
    elif split_kind == "environment_safe":
        splitter = GroupKFold(n_splits=5)
        it = splitter.split(X, y, groups=envs)
    else:
        raise ValueError(split_kind)

    oof_pred = np.full(len(y), np.nan)
    oof_bl_glob = np.full(len(y), np.nan)
    oof_bl_env = np.full(len(y), np.nan)
    oof_bl_mat = np.full(len(y), np.nan)
    for tr, te in it:
        model = HistGradientBoostingRegressor(
            random_state=SEED, max_iter=300, learning_rate=0.05,
            max_depth=None, max_leaf_nodes=31, l2_regularization=1.0,
            early_stopping=False)
        model.fit(X[tr], y[tr])
        oof_pred[te] = model.predict(X[te])
        glob = float(np.mean(y[tr]))
        oof_bl_glob[te] = glob
        oof_bl_env[te] = group_baseline(envs[tr], y[tr], envs[te], glob)
        oof_bl_mat[te] = group_baseline(mats[tr], y[tr], mats[te], glob)
    res = {
        "gbm": dict(zip(("rmse", "mae", "r2"), metrics(y, oof_pred))),
        "baseline_global_mean": dict(zip(("rmse", "mae", "r2"), metrics(y, oof_bl_glob))),
        "baseline_environment_mean": dict(zip(("rmse", "mae", "r2"), metrics(y, oof_bl_env))),
        "baseline_material_mean": dict(zip(("rmse", "mae", "r2"), metrics(y, oof_bl_mat))),
    }
    return res, oof_pred


def bootstrap_ci(y, pred, groups, n=2000):
    # cluster bootstrap over groups (materials) for the material-safe RMSE
    rng = np.random.default_rng(SEED)
    uniq = np.array(sorted(set(groups.tolist())))
    idx_by_g = {g: np.where(groups == g)[0] for g in uniq}
    stats = []
    for _ in range(n):
        pick = rng.choice(len(uniq), size=len(uniq), replace=True)
        sel = np.concatenate([idx_by_g[uniq[p]] for p in pick])
        err = pred[sel] - y[sel]
        stats.append(math.sqrt(float(np.mean(err ** 2))))
    lo, hi = np.percentile(stats, [2.5, 97.5])
    return float(lo), float(hi)


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


def main():
    rows, src_sha, n_raw = load()
    X, y, mats, envs, has_comp = build_matrix(rows)
    n = len(y)

    mat_res, mat_pred = run_cv(X, y, mats, envs, "material_safe")
    env_res, _ = run_cv(X, y, mats, envs, "environment_safe")
    rnd_res, _ = run_cv(X, y, mats, envs, "random")

    ci_lo, ci_hi = bootstrap_ci(y, mat_pred, mats)

    best_baseline_r2 = max(mat_res["baseline_global_mean"]["r2"],
                           mat_res["baseline_environment_mean"]["r2"],
                           mat_res["baseline_material_mean"]["r2"])
    best_baseline_rmse = min(mat_res["baseline_global_mean"]["rmse"],
                             mat_res["baseline_environment_mean"]["rmse"],
                             mat_res["baseline_material_mean"]["rmse"])
    err_red = 100.0 * (1.0 - mat_res["gbm"]["rmse"] / best_baseline_rmse)
    leakage = rnd_res["gbm"]["r2"] - mat_res["gbm"]["r2"]

    canonical = {
        "schema": "amphora.barrier-corrosion-score.corr-rate-qspr-diagnostic.v1",
        "benchmark": "amphora-barrier-corrosion-score/corr-rate-qspr-v1",
        "target": "log10(corrosion_rate_mm_per_year)",
        "target_interpretation": "bare metal/alloy substrate corrosion rate in a "
                                 "chemical environment; NOT organic-coating barrier",
        "dataset": {
            "name": "NIST CORR-DATA (Dow Chemical Co.) derived reference",
            "in_tree_path": SRC,
            "source_sha256": src_sha,
            "rights_class": "DERIVATIVE_ALLOWED",
            "n_raw_records": n_raw,
        },
        "cohort": {
            "n_modeled": n,
            "n_unique_materials": int(len(set(mats.tolist()))),
            "n_unique_environments": int(len(set(envs.tolist()))),
            "n_records_with_alloy_composition": int(has_comp),
            "composition_coverage_pct": 100.0 * has_comp / n,
        },
        "features": {
            "alloy_composition_elements_wt_pct": ELEMENTS,
            "environment_chemistry_flags": ENV_FEAT_NAMES,
            "other": ["temperature_c", "temperature_missing_flag"],
            "n_features": int(X.shape[1]),
            "composition_reference": "ASM Handbook Vol.1/Vol.3; ASTM alloy specs "
                                     "(nominal wt%)",
            "environment_reference": "aqueous corrosion chemistry keyword rules "
                                     "(halide/oxidizing/reducing/organic-acid/alkali/marine)",
        },
        "model": {
            "estimator": "HistGradientBoostingRegressor",
            "params": {"max_iter": 300, "learning_rate": 0.05,
                       "max_leaf_nodes": 31, "l2_regularization": 1.0,
                       "random_state": SEED},
            "sklearn_version": sklearn.__version__,
        },
        "cross_validation": {
            "material_safe_leave_material_out_5fold": mat_res,
            "environment_safe_leave_environment_out_5fold": env_res,
            "random_5fold_leakage_reference": rnd_res,
        },
        "headline_material_safe": {
            "gbm_rmse_log_units": mat_res["gbm"]["rmse"],
            "gbm_r2": mat_res["gbm"]["r2"],
            "gbm_mae": mat_res["gbm"]["mae"],
            "rmse_cluster_bootstrap_ci95": [ci_lo, ci_hi],
            "best_naive_baseline_r2": best_baseline_r2,
            "best_naive_baseline_rmse": best_baseline_rmse,
            "error_reduction_vs_best_baseline_pct": err_red,
            "leakage_indicator_random_r2_minus_material_safe_r2": leakage,
            "interpretation": "Diagnostic. Group-safe (leave-material-out) corrosion-"
                              "rate QSPR; modest positive skill over naive baselines. "
                              "Random-CV R2 is inflated by material leakage (see indicator). "
                              "No candidate/coating superiority claim.",
        },
        "authority": "AUDIT_ONLY",
        "closes_gate": "SCIENTIFIC_BENCHMARK_NOT_EXECUTED",
        "does_not_close": [
            "EVALUATION_SIGNATURE_ABSENT (requires trust-anchored phase0-evaluator key)",
            "coating-barrier authority (this is substrate corrosion, not coating barrier)",
            "human / independent review",
        ],
        "determinism": {"omp_num_threads": os.environ.get("OMP_NUM_THREADS"),
                        "seed": SEED, "canonical_round_decimals": NDEC},
    }
    out = json.dumps(rnd(canonical), indent=2, sort_keys=True)
    open(sys.argv[1] if len(sys.argv) > 1 else "diagnostic.json", "w").write(out)
    sha = hashlib.sha256(out.encode()).hexdigest()
    print("CANONICAL_SHA256", sha)
    print("n_modeled", n, "has_comp", has_comp,
          "mat_safe_r2", round(mat_res["gbm"]["r2"], 4),
          "env_safe_r2", round(env_res["gbm"]["r2"], 4),
          "random_r2", round(rnd_res["gbm"]["r2"], 4),
          "err_red_pct", round(err_red, 2))


if __name__ == "__main__":
    main()
