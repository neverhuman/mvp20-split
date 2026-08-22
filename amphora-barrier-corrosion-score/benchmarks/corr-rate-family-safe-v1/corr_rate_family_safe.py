#!/usr/bin/env python3
"""
amphora-barrier-corrosion-score / corr-rate-family-safe-v1
FALSIFICATION ATTACK on corr-rate-qspr-v1's leave-material-out headline
(GroupKFold group=material, HistGBM R2=0.316, RMSE=1.036 log units,
"the reproducible artifact of record" for corrosion-rate QSPR per that
benchmark's own HANDOFF.md).

ATTACK: corr-rate-qspr-v1 groups GroupKFold folds by the raw `material`
string label. The NIST CORR-DATA material vocabulary contains many
near-duplicate alloy designations that are the SAME or near-identical
metallurgical family under a different string (e.g. "316", "316L", "316LN",
"316Ti", "316F" are all 300-series austenitic stainless variants with
near-identical Cr/Ni/Mo content; "Hastelloy C-276", "Alloy C-276",
"Inco C-276" name the same nickel alloy under three different labels).
GroupKFold(group=material) puts these in DIFFERENT folds despite them
being metallurgically near-identical, so a model that has merely learned
"stainless-300-series chemistry" or "Ni-Cr-Mo superalloy chemistry" from
one alias can score well on a held-out alias of the SAME family without
having learned anything about a genuinely novel alloy family.

This benchmark re-runs the IDENTICAL feature engineering, model, seed, and
metrics from corr-rate-qspr-v1/corr_rate_qspr.py verbatim (comp_vector,
env_features, load, build_matrix, metrics, group_baseline, HistGBM
hyperparameters, SEED=0) and adds ONLY one new axis: GroupKFold with
group = metallurgical FAMILY (ASM Handbook Vol.3; Sedriks 1996;
Uhlig-Revie 2008 classification: austenitic/ferritic/duplex stainless
collapsed to one "stainless_steel" family per ASM Vol.3's own single
chapter scope, nickel_alloy, cobalt_alloy, carbon_steel_cast_iron,
copper_alloy, titanium, zirconium_hafnium, tantalum_niobium,
precious_metal, lead, tin, zinc, magnesium, aluminum, molybdenum,
chromium, carbide_cermet) instead of raw material string.

PRE-REGISTERED REFUTATION CRITERION (declared before running):
The leave-material-out R2=0.316 headline implicitly claims the model
generalizes to genuinely novel alloys, not merely to unseen string labels
of already-seen alloy chemistry. This is REFUTED if leave-family-out GBM
R2 collapses to <= 0 (no better than the global-mean baseline) OR fails to
beat the best naive baseline on RMSE (error_reduction_vs_best_baseline_pct
<= 0), on the SAME rows, SAME features, SAME model, SAME seed -- i.e. if
the only thing keeping leave-material-out positive is within-family
alias leakage. It SURVIVES if leave-family-out R2 remains clearly positive
and continues to beat the best naive baseline, even if reduced relative to
leave-material-out (some reduction is expected and not itself a refutation
-- family grouping is strictly harder/coarser than material grouping).

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
from sklearn.model_selection import GroupKFold, KFold
import sklearn

SRC = "feedback/v1/derived/nist_corr_reference.json"
SEED = 0
NDEC = 6

# ---------------------------------------------------------------------------
# VERBATIM from corr-rate-qspr-v1/corr_rate_qspr.py (byte-identical logic;
# reused unchanged so this is a strictly controlled, apples-to-apples
# comparison -- the ONLY new variable introduced below is family grouping).
ELEMENTS = ["fe", "cr", "ni", "mo", "cu", "ti", "zr", "nb", "ta", "co",
            "w", "al", "mn", "si", "c", "pb", "sn", "ag", "pt", "au"]

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
            rate = rate * 0.0254
        if rate <= 0:
            continue
        mat = str(x.get("material") or "").strip()
        env = str(x.get("environment") or "").strip()
        if not mat or not env:
            continue
        temp = x.get("temperature_c")
        rows.append((mat, env, temp, math.log10(rate)))
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
    d = {}
    sums, cnts = {}, {}
    for k, v in zip(key_train, y_train):
        sums[k] = sums.get(k, 0.0) + v
        cnts[k] = cnts.get(k, 0) + 1
    for k in sums:
        d[k] = sums[k] / cnts[k]
    return np.array([d.get(k, glob) for k in key_test])

# ---------------------------------------------------------------------------
# NEW: metallurgical family classifier (ASM Handbook Vol.3; Sedriks 1996;
# Uhlig-Revie 2008 standard family groupings). Ordered, first-match-wins,
# same "keyword substring" methodology already used in-tree for COMPOSITION.
# Families are deliberately COARSER than raw material strings so that
# near-duplicate alloy designations (e.g. 316/316L/316LN/316Ti, or
# Hastelloy-C-276/Alloy-C-276/Inco-C-276) always land in the SAME fold.
_FAMILY_RULES = [
    ("copper_alloy", ["nickel-silver", "nickel silver", "cupronickel",
                       "copper-nickel", "copper nickel", "copper-zinc",
                       "copper zinc", "copper-tin", "copper-aluminum",
                       "copper-silicon"]),
    ("nickel_alloy", ["hastelloy"]),
    ("cobalt_alloy", ["haynes", "stellite", "mp35n", "co-cr", "co-20cr"]),
    ("carbide_cermet", ["wc-", "tac-"]),
    ("nickel_alloy", ["inconel", "incoloy", "monel", "duranickel", "nimonic",
                       "cabot", "illium", "worthite", "durimet", "chlorimet",
                       "durichlor", "durachlor", "carpenter 20", "carpenter20",
                       "20cb", "20 cb", "alloy 20", "nickel alloy",
                       "nickel  alloy"]),
    ("nickel_alloy", [r"\balloy\s*6\d\d\b", r"\balloy\s*8\d\d\b",
                       r"\b6\d\d\b.*inco", r"\b8\d\d\b.*inco",
                       "alloy c-", "alloy b-", "alloy g-", "alloy g\b",
                       "alloy d\b", "alloy s\b", "alloy x\b",
                       "nickel c-", "nickel b-", "nickel g",
                       "nickel-al bronze"]),
    ("nickel_alloy", ["nickel"]),
    ("stainless_steel", [
        r"\b3\d\d\b", r"\b40\d\b", r"\b41\d\b", r"\b42\d\b", r"\b43\d\b",
        r"\b44\d\b", r"\b2205\b", r"\b2304\b", r"\b2507\b",
        "904l", "254 smo", "al-6xn", "al 6xn", "al29-4", "al 29-4",
        "e-brite", "ferralium", "sanicro", "remanit", "26-1", "18-8",
        "cf-8", "cn-7m", "cd-4mcu", "cw-12m", "aci c", "duplex",
        "22cr-13ni", "21cr-6", "18cr-", "13cr", "12cr", "14cr", "9cr",
        "7cr", "5cr", "10cr", "17cr", "27cr", "29cr", "18.5%cr",
        "18cr", "1.25cr-0.5mo", "2.6cr", "5cr-1.5mo", "5cr-mo",
        "16ni, 8cr", "16ni,8cr", "25cr-22ni", "21cr-4ni", "2mo-0.4cu",
    ]),
    ("carbon_steel_cast_iron", [
        "steel", "cast iron", "ductile iron", "ni-resist", "armco iron",
        "white iron", "wrought iron", r"\ba\d\d\d\b", r"\b10\d\d\b",
        r"\b40\d\d\b", "api n", "1.2mn", "1.8ni-0.81cu", "3% nickel-iron",
        "hy-80",
    ]),
    ("copper_alloy", [
        "copper", "brass", "bronze", "admiralty", "ampco", "muntz",
        r"\bc\d{5}\b", "dhp", "ofe", "ofhc", "nickel bronze",
        "nickel- silver", "hydraulic bronze", "g bronze",
    ]),
    ("titanium", ["titanium", r"\bti-", "b/c titanium", "b/c-titanium",
                   "pure ti\b"]),
    ("zirconium_hafnium", ["zr7", "zr70", "zircaloy", "zirconium", "hf-",
                             "zr7o2"]),
    ("tantalum_niobium", ["tantalum", "niobium", "columbium", "cb alloy",
                            r"\bcb\b", "ta-mo", "cb-"]),
    ("precious_metal", ["platinum", "platnium", "silver", "gold", "rhodium",
                          "iridium", "ruthenium", "osmium", "palladium"]),
    ("lead", ["lead", "babbitt", "solder"]),
    ("magnesium", ["magnesium", r"\baz\d\d", "hk31a", "hm21a", "zk60a",
                    r"\bm1a\b"]),
    ("aluminum", ["aluminum", "alclad", r"\b[1-8]\d\d\d-", r"\b[1-8]\d\d\d\b",
                   "fecralloy", "al-3mg", "al-1mn"]),
    ("molybdenum", ["molybdenum"]),
    ("chromium", ["chromium", r"\bfe-47cr\b"]),
    ("tin", [r"\btin\b", "tin brass", "tin \\("]),
    ("zinc", ["zinc"]),
]
_COMPILED = []
for fam, pats in _FAMILY_RULES:
    for p in pats:
        _COMPILED.append((fam, re.compile(p)))


def classify_family(material):
    m = material.lower()
    for fam, rx in _COMPILED:
        if rx.search(m):
            return fam
    return None


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


def run_cv(X, y, mats, envs, families, split_kind):
    if split_kind == "material_safe":
        splitter = GroupKFold(n_splits=5)
        it = list(splitter.split(X, y, groups=mats))
        groups_key = mats
    elif split_kind == "family_safe":
        n_fam = len(set(families.tolist()))
        n_splits = min(5, n_fam)
        splitter = GroupKFold(n_splits=n_splits)
        it = list(splitter.split(X, y, groups=families))
        groups_key = families
    else:
        raise ValueError(split_kind)

    oof_pred = np.full(len(y), np.nan)
    oof_bl_glob = np.full(len(y), np.nan)
    oof_bl_mat = np.full(len(y), np.nan)
    fold_r2 = []
    for tr, te in it:
        model = HistGradientBoostingRegressor(
            random_state=SEED, max_iter=300, learning_rate=0.05,
            max_depth=None, max_leaf_nodes=31, l2_regularization=1.0,
            early_stopping=False)
        model.fit(X[tr], y[tr])
        pred_te = model.predict(X[te])
        oof_pred[te] = pred_te
        glob = float(np.mean(y[tr]))
        oof_bl_glob[te] = glob
        oof_bl_mat[te] = group_baseline(groups_key[tr], y[tr], groups_key[te], glob)
        _, _, r2_fold = metrics(y[te], pred_te)
        fold_r2.append({"n_test": int(len(te)), "r2": r2_fold})
    res = {
        "gbm": dict(zip(("rmse", "mae", "r2"), metrics(y, oof_pred))),
        "baseline_global_mean": dict(zip(("rmse", "mae", "r2"), metrics(y, oof_bl_glob))),
        "baseline_group_mean": dict(zip(("rmse", "mae", "r2"), metrics(y, oof_bl_mat))),
        "n_folds": len(it),
        "per_fold": fold_r2,
    }
    return res, oof_pred


def main():
    rows, src_sha, n_raw = load()
    X, y, mats, envs, has_comp = build_matrix(rows)
    n = len(y)

    fam_list = [classify_family(m) for m in mats]
    classified_mask = np.array([f is not None for f in fam_list])
    families_all = np.array([f if f is not None else "unclassified" for f in fam_list])
    n_classified = int(classified_mask.sum())
    family_coverage_pct = 100.0 * n_classified / n

    # material-safe result on the FULL cohort (replicates corr-rate-qspr-v1 exactly)
    mat_res_full, _ = run_cv(X, y, mats, envs, families_all, "material_safe")

    # restrict to classified rows for a fair apples-to-apples family-safe vs
    # material-safe comparison on the IDENTICAL subset of rows
    Xc, yc, matsc, famc = X[classified_mask], y[classified_mask], mats[classified_mask], families_all[classified_mask]
    n_c = len(yc)
    n_families = int(len(set(famc.tolist())))
    n_materials_in_subset = int(len(set(matsc.tolist())))

    mat_res_subset, _ = run_cv(Xc, yc, matsc, envs[classified_mask], famc, "material_safe")
    fam_res, fam_pred = run_cv(Xc, yc, matsc, envs[classified_mask], famc, "family_safe")

    family_counts = {}
    for f in famc.tolist():
        family_counts[f] = family_counts.get(f, 0) + 1

    def err_red(gbm_rmse, base_rmse):
        return 100.0 * (1.0 - gbm_rmse / base_rmse) if base_rmse > 0 else float("nan")

    mat_subset_best_base_rmse = min(mat_res_subset["baseline_global_mean"]["rmse"],
                                     mat_res_subset["baseline_group_mean"]["rmse"])
    fam_best_base_rmse = min(fam_res["baseline_global_mean"]["rmse"],
                              fam_res["baseline_group_mean"]["rmse"])

    mat_subset_err_red = err_red(mat_res_subset["gbm"]["rmse"], mat_subset_best_base_rmse)
    fam_err_red = err_red(fam_res["gbm"]["rmse"], fam_best_base_rmse)

    refutation_criterion = (
        "REFUTED if family_safe.gbm.r2 <= 0.0 OR "
        "family_safe_error_reduction_vs_best_baseline_pct <= 0.0 "
        "(on the identical classified-subset rows/features/model/seed as "
        "material_safe_subset); SURVIVED otherwise, even if reduced "
        "relative to material_safe_subset."
    )
    refuted = (fam_res["gbm"]["r2"] <= 0.0) or (fam_err_red <= 0.0)
    verdict = "CLAIM_REFUTED" if refuted else "CLAIM_SURVIVED"

    canonical = {
        "schema": "amphora.barrier-corrosion-score.corr-rate-family-safe-attack.v1",
        "benchmark": "amphora-barrier-corrosion-score/corr-rate-family-safe-v1",
        "attacks_claim": (
            "corr-rate-qspr-v1/HANDOFF.md headline: leave-material-out "
            "(GroupKFold group=material) HistGBM R2=0.316 on log10(corrosion "
            "rate mm/yr), described as 'the reproducible artifact of record' "
            "for corrosion-rate QSPR in this module."
        ),
        "attack_description": (
            "GroupKFold(group=material) never separates metallurgically "
            "near-identical alloy aliases (e.g. 316/316L/316LN/316Ti, or "
            "Hastelloy-C-276/Alloy-C-276/Inco-C-276) since each alias is a "
            "distinct string label but the SAME or near-identical chemistry. "
            "This re-runs the identical feature engineering, HistGBM model, "
            "seed, and metrics with the group axis changed from raw material "
            "string to metallurgical FAMILY (ASM Handbook Vol.3; Sedriks 1996; "
            "Uhlig-Revie 2008), which guarantees all aliases of one family "
            "fall in the same fold."
        ),
        "refutation_criterion": refutation_criterion,
        "dataset": {
            "name": "NIST CORR-DATA (Dow Chemical Co.) derived reference",
            "in_tree_path": SRC,
            "source_sha256": src_sha,
            "rights_class": "DERIVATIVE_ALLOWED",
            "n_raw_records": n_raw,
        },
        "family_classification": {
            "method": "ordered keyword/regex substring rules, same methodology "
                     "as in-tree COMPOSITION lookup; first-match-wins",
            "reference": "ASM Handbook Vol.3: Stainless Steels; Sedriks 1996 "
                         "Corrosion of Stainless Steels; Uhlig-Revie 2008 "
                         "Corrosion and Corrosion Control",
            "n_families": n_families,
            "family_row_counts": family_counts,
            "n_modeled_full_cohort": n,
            "n_classified": n_classified,
            "family_coverage_pct": family_coverage_pct,
            "n_unclassified_rows": int(n - n_classified),
        },
        "cohort": {
            "full_cohort_n": n,
            "classified_subset_n": n_c,
            "n_materials_in_classified_subset": n_materials_in_subset,
            "n_families_in_classified_subset": n_families,
        },
        "results": {
            "material_safe_full_cohort_reference": {
                "gbm_r2": mat_res_full["gbm"]["r2"],
                "gbm_rmse": mat_res_full["gbm"]["rmse"],
                "note": "replicates corr-rate-qspr-v1 exactly (full n=%d cohort, "
                        "GroupKFold group=material, 5-fold)" % n,
            },
            "material_safe_classified_subset": {
                "gbm": mat_res_subset["gbm"],
                "baseline_global_mean": mat_res_subset["baseline_global_mean"],
                "baseline_group_mean": mat_res_subset["baseline_group_mean"],
                "n_folds": mat_res_subset["n_folds"],
                "error_reduction_vs_best_baseline_pct": mat_subset_err_red,
            },
            "family_safe_classified_subset": {
                "gbm": fam_res["gbm"],
                "baseline_global_mean": fam_res["baseline_global_mean"],
                "baseline_group_mean": fam_res["baseline_group_mean"],
                "n_folds": fam_res["n_folds"],
                "per_fold_r2": fam_res["per_fold"],
                "error_reduction_vs_best_baseline_pct": fam_err_red,
            },
        },
        "comparison": {
            "r2_material_safe_subset": mat_res_subset["gbm"]["r2"],
            "r2_family_safe_subset": fam_res["gbm"]["r2"],
            "r2_drop_family_minus_material": fam_res["gbm"]["r2"] - mat_res_subset["gbm"]["r2"],
            "family_safe_gbm_r2_positive": bool(fam_res["gbm"]["r2"] > 0.0),
            "family_safe_beats_best_baseline_rmse": bool(fam_err_red > 0.0),
        },
        "verdict": verdict,
        "authority": "AUDIT_ONLY",
        "promotes_authority": False,
        "modifies_manifest": False,
        "scope_honesty": (
            "Diagnostic on bare metal/alloy substrate corrosion (NIST CORR-DATA), "
            "same scope ceiling as corr-rate-qspr-v1: NOT organic-coating "
            "barrier performance. No candidate/coating superiority claim."
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
    print("n_classified", n_classified, "coverage_pct", round(family_coverage_pct, 2),
          "n_families", n_families)
    print("material_safe_subset_r2", round(mat_res_subset["gbm"]["r2"], 4),
          "family_safe_r2", round(fam_res["gbm"]["r2"], 4),
          "family_safe_err_red_pct", round(fam_err_red, 2),
          "verdict", verdict)


if __name__ == "__main__":
    main()
