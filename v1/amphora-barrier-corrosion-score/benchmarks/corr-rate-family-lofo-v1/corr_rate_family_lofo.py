#!/usr/bin/env python3
"""
amphora-barrier-corrosion-score / corr-rate-family-lofo-v1
FALSIFICATION ATTACK on corr-rate-family-safe-qspr-kpi.v1's promoted claim:
GroupKFold(group=metallurgical_family, 5-fold) HistGBM R2=0.132087 on the
NIST CORR-DATA classified subset (n=7282, 17 families), promoted as "the
module's strongest rights-clean empirical claim" and asserted to fix
within-family alias leakage in the material-safe headline.

WHY THE 5-FOLD FAMILY-SAFE RESULT IS NOT THE HARDEST AVAILABLE TEST:
family_row_counts shows 2 of 17 families (stainless_steel n=1976,
nickel_alloy n=1888) already consume 53.1% of the classified cohort.
GroupKFold(n_splits=5) balances fold SIZE, so it naturally isolates each
giant family into its own solo fold (confirmed: per_fold n_test values
1976 and 1888 match those two families exactly) while packing the
remaining 15 families into only 3 folds. The reported aggregate R2 is a
SAMPLE-weighted OOF statistic, so it is dominated by whichever families
happen to be large. It answers "does the model generalize to the next
withheld ROW" -- not "does the model generalize to the next withheld
FAMILY" -- and a KPI whose stated capability is
"Leave-metallurgical-family-out ... generalization estimate" (verbatim
capability string in the KPI receipt) should be judged per-family, not
per-row.

ATTACK: true Leave-One-Family-Out (LOFO), n_splits = n_families = 17,
one family held out at a time. Identical feature engineering, HistGBM
hyperparameters, and seed=0, copied byte-for-byte from
corr-rate-family-safe-v1/corr_rate_family_safe.py (verbatim functions:
comp_vector, env_features, load, build_matrix, metrics, classify_family,
COMPOSITION, _FAMILY_RULES). The ONLY new variable is the CV split: one
family per fold instead of GroupKFold's size-balanced grouping of
multiple families per fold.

PRE-REGISTERED REFUTATION CRITERION (declared before running/inspecting
LOFO results):
The KPI's promoted claim implicitly asserts the model generalizes ACROSS
metallurgical families broadly, not merely that a sample-weighted average
dominated by 2 giant families is positive. This is REFUTED if EITHER:
  (a) the family-count-weighted (unweighted-per-family) mean LOFO R2,
      averaged over all families with n>=20 test rows (chromium n=6 and
      molybdenum n=2 excluded as statistically unreliable single-fold R2),
      is <= 0.0; OR
  (b) a majority (>50%) of those n>=20 eligible families individually
      score LOFO R2 <= 0.0.
It SURVIVES if the family-count-weighted mean LOFO R2 > 0 AND a majority
of eligible families individually score R2 > 0, even if both are reduced
relative to the sample-weighted 5-fold family-safe number (some reduction
is expected: LOFO is strictly harder per-family than the sample-weighted
5-fold aggregate and is not itself a refutation).

Determinism: OMP_NUM_THREADS=1, fixed seed, GroupKFold(n_splits=n_families)
with groups=family label (equivalent to a manual per-family leave-out
since every family gets its own fold when n_splits==n_groups), rounded
canonical output -> byte-stable two-replay SHA-256 gate.
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

SRC = "feedback/v1/derived/nist_corr_reference.json"
SEED = 0
NDEC = 6
MIN_ELIGIBLE_N = 20

# ---------------------------------------------------------------------------
# VERBATIM from corr-rate-family-safe-v1/corr_rate_family_safe.py
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


def main():
    rows, src_sha, n_raw = load()
    X, y, mats, envs, has_comp = build_matrix(rows)

    fam_list = [classify_family(m) for m in mats]
    classified_mask = np.array([f is not None for f in fam_list])
    families_all = np.array([f if f is not None else "unclassified" for f in fam_list])

    Xc = X[classified_mask]
    yc = y[classified_mask]
    famc = families_all[classified_mask]
    n_c = len(yc)
    uniq_families = sorted(set(famc.tolist()))
    n_families = len(uniq_families)

    # LOFO: GroupKFold with n_splits == n_groups gives exactly one group
    # (family) per fold -- true leave-one-family-out.
    splitter = GroupKFold(n_splits=n_families)
    it = list(splitter.split(Xc, yc, groups=famc))
    assert len(it) == n_families

    oof_pred = np.full(n_c, np.nan)
    per_family = []
    for tr, te in it:
        fam_here = sorted(set(famc[te].tolist()))
        assert len(fam_here) == 1, "LOFO fold leaked >1 family: %r" % fam_here
        fam_name = fam_here[0]
        model = HistGradientBoostingRegressor(
            random_state=SEED, max_iter=300, learning_rate=0.05,
            max_depth=None, max_leaf_nodes=31, l2_regularization=1.0,
            early_stopping=False)
        model.fit(Xc[tr], yc[tr])
        pred_te = model.predict(Xc[te])
        oof_pred[te] = pred_te
        rmse, mae, r2 = metrics(yc[te], pred_te)
        train_mean = float(np.mean(yc[tr]))
        base_rmse, _, _ = metrics(yc[te], np.full(len(te), train_mean))
        per_family.append({
            "family": fam_name,
            "n_test": int(len(te)),
            "r2": r2,
            "rmse": rmse,
            "mae": mae,
            "baseline_global_mean_rmse": base_rmse,
            "beats_global_mean_baseline_rmse": bool(rmse < base_rmse),
        })
    per_family.sort(key=lambda d: -d["n_test"])

    overall_rmse, overall_mae, overall_r2 = metrics(yc, oof_pred)

    eligible = [d for d in per_family if d["n_test"] >= MIN_ELIGIBLE_N]
    excluded = [d for d in per_family if d["n_test"] < MIN_ELIGIBLE_N]
    n_eligible = len(eligible)
    family_weighted_mean_r2 = float(np.mean([d["r2"] for d in eligible])) if eligible else float("nan")
    n_eligible_positive = sum(1 for d in eligible if d["r2"] > 0.0)
    n_eligible_nonpositive = n_eligible - n_eligible_positive
    frac_eligible_positive = (n_eligible_positive / n_eligible) if n_eligible else float("nan")
    majority_positive = (n_eligible_positive > n_eligible / 2.0) if n_eligible else False

    refutation_criterion = (
        "REFUTED if (a) family-count-weighted (unweighted-per-family) mean "
        "LOFO R2 over families with n_test>=%d <= 0.0, OR (b) a majority "
        "(>50%%) of those eligible families individually score LOFO R2 "
        "<= 0.0. SURVIVED if family-weighted mean R2 > 0.0 AND a majority "
        "of eligible families individually score R2 > 0.0, even if reduced "
        "relative to the sample-weighted 5-fold family-safe KPI number "
        "(some reduction from a strictly harder per-family test is "
        "expected and is not itself a refutation)." % MIN_ELIGIBLE_N
    )
    refuted = (family_weighted_mean_r2 <= 0.0) or (not majority_positive)
    verdict = "CLAIM_REFUTED" if refuted else "CLAIM_SURVIVED"

    canonical = {
        "schema": "amphora.barrier-corrosion-score.corr-rate-family-lofo-attack.v1",
        "benchmark": "amphora-barrier-corrosion-score/corr-rate-family-lofo-v1",
        "attacks_claim": (
            "evidence/phase0/kpis/corr-rate-family-safe-qspr-kpi.v1.dsse.json: "
            "GroupKFold(group=metallurgical_family, 5-fold) HistGBM R2=0.132087 "
            "on the NIST CORR-DATA classified subset (n=7282, 17 families), "
            "'the module's strongest rights-clean empirical claim', capability "
            "string 'Leave-metallurgical-family-out ... corrosion-rate QSPR "
            "generalization estimate'."
        ),
        "attack_description": (
            "The promoted KPI's 5-fold GroupKFold(family) naturally isolates "
            "the 2 largest of 17 families (stainless_steel n=1976, "
            "nickel_alloy n=1888, 53.1%% of the classified cohort) into their "
            "own solo folds and packs the remaining 15 families into only 3 "
            "folds, so the reported R2 is a SAMPLE-weighted (per-row) "
            "out-of-fold statistic dominated by whichever families are large. "
            "This re-runs the identical feature engineering, HistGBM model, "
            "and seed with true Leave-One-Family-Out (n_splits=n_families=17, "
            "one family held out per fold) and reports the FAMILY-weighted "
            "(unweighted per family) mean R2 alongside the sample-weighted "
            "OOF R2, to test whether the KPI's claimed 'generalizes across "
            "metallurgical families' capability holds broadly across "
            "families, not just in the row-weighted aggregate."
        ),
        "refutation_criterion": refutation_criterion,
        "min_eligible_n_test": MIN_ELIGIBLE_N,
        "dataset": {
            "name": "NIST CORR-DATA (Dow Chemical Co.) derived reference",
            "in_tree_path": SRC,
            "source_sha256": src_sha,
            "rights_class": "DERIVATIVE_ALLOWED",
            "n_raw_records": n_raw,
        },
        "cohort": {
            "classified_subset_n": n_c,
            "n_families": n_families,
        },
        "results": {
            "sample_weighted_oof": {"rmse": overall_rmse, "mae": overall_mae, "r2": overall_r2},
            "per_family_lofo": per_family,
            "eligible_families_n_test_ge_min": n_eligible,
            "excluded_families_below_min": [d["family"] for d in excluded],
            "family_weighted_mean_r2": family_weighted_mean_r2,
            "n_eligible_families_r2_positive": n_eligible_positive,
            "n_eligible_families_r2_nonpositive": n_eligible_nonpositive,
            "frac_eligible_families_r2_positive": frac_eligible_positive,
            "majority_of_eligible_families_positive": majority_positive,
        },
        "comparison_to_promoted_kpi": {
            "kpi_sample_weighted_5fold_family_safe_r2": 0.132087,
            "lofo_sample_weighted_oof_r2": overall_r2,
            "lofo_family_weighted_mean_r2": family_weighted_mean_r2,
            "note": (
                "kpi number is sample-weighted (row-count-weighted, 5 folds, "
                "2 giant families solo); lofo_sample_weighted_oof_r2 is the "
                "directly comparable per-row OOF statistic under true "
                "17-way LOFO; lofo_family_weighted_mean_r2 treats every "
                "family as one equally-weighted unit, which is the honest "
                "reading of a 'generalizes across families' claim."
            ),
        },
        "verdict": verdict,
        "authority": "AUDIT_ONLY",
        "promotes_authority": False,
        "modifies_manifest": False,
        "scope_honesty": (
            "Diagnostic on bare metal/alloy substrate corrosion (NIST "
            "CORR-DATA), same scope ceiling as corr-rate-qspr-v1 and "
            "corr-rate-family-safe-v1: NOT organic-coating barrier "
            "performance. No candidate/coating superiority claim."
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
    print("n_families", n_families, "n_eligible", n_eligible)
    print("sample_weighted_oof_r2", round(overall_r2, 4))
    print("family_weighted_mean_r2", round(family_weighted_mean_r2, 4))
    print("n_eligible_positive", n_eligible_positive, "/", n_eligible)
    print("verdict", verdict)


if __name__ == "__main__":
    main()
