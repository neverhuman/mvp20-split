#!/usr/bin/env python3
"""
amphora-barrier-corrosion-score / corr-rate-unclassified-holdout-v1
FALSIFICATION ATTACK on evidence/phase0/kpis/corr-rate-family-safe-qspr-kpi.v1
(GroupKFold(group=metallurgical_family, 5-fold) HistGBM R2=0.132087, "the
module's strongest rights-clean empirical claim").

WHY THIS IS THE NEXT ESCALATION, NOT A REPEAT:
Every prior attack on this claim varied the CV GROUPING axis (material
string -> metallurgical family -> true leave-one-family-out -> leave-one-
SOURCE-out) or the ENVIRONMENT axis (marine domain shift). None has tested
the classifier's own declared blind spot. The KPI receipt itself discloses,
verbatim in its own "awaiting" list: "Phase-1: extend metallurgical-family
taxonomy beyond the 94.58% keyword/regex classifier coverage (417
unclassified rows excluded)". Those 417 rows (5.42% of the full n=7699
cohort) have NEVER been scored by any receipt in this module: they are
structurally excluded from every classified_subset used by
corr-rate-family-safe-v1, corr-rate-family-lofo-v1, corr-rate-marine-
envelope-v1, corr-rate-feature-integrity-v1, and corr-rate-source-lofo-v1
alike, because classify_family() returns None for them and none of those
receipts evaluates on the None branch. This benchmark trains the identical
model on ALL 7282 classified rows (the deployed-equivalent full-data fit,
not a CV fold) and evaluates it on those 417 never-scored rows: a genuine,
previously untested distribution-shift / edge-of-envelope probe on the
population the classifier itself flags as taxonomically out-of-scope.

PRE-REGISTERED REFUTATION CRITERION (declared before running/inspecting
results), mirroring the KPI's own pre-registered pattern for direct
comparability:
  REFUTED if EITHER
    (a) unclassified-holdout gbm.r2 <= 0.0; OR
    (b) unclassified-holdout error_reduction_vs_global_mean_baseline_pct <= 0.0
  on identical feature engineering / HistGBM hyperparameters / seed=0,
  fit on the full 7282-row classified cohort, evaluated on the 417-row
  unclassified holdout (a population disjoint from every family-grouped
  fold ever scored). SURVIVES otherwise, even if reduced relative to the
  family-safe/LOFO/source-LOFO within-taxonomy numbers (the unclassified
  rows are definitionally the hardest-to-characterize materials in the
  cohort and some reduction is expected).

POSITIVE CONTROL: hostile-null full-label-shuffle (fixed seed) applied to
the SAME unclassified-holdout targets; the attack must correctly detect
(REFUTED-triggering) degenerate performance on the shuffled copy while not
firing on the real, unshuffled data, proving the harness can actually
distinguish signal from noise on this exact population/model/metric.

Determinism: OMP_NUM_THREADS=1, fixed seed, single deterministic
train/test split (no shuffling: train = all classified rows in fixed
classified-subset order, test = all unclassified rows in fixed order),
rounded canonical output -> byte-stable two-replay SHA-256 gate.
"""
import os
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
import json, hashlib, math, sys, re
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
import sklearn

SRC = "feedback/v1/derived/nist_corr_reference.json"
SEED = 0
NDEC = 6

# ---------------------------------------------------------------------------
# VERBATIM from corr-rate-family-safe-v1/corr_rate_family_safe.py and
# corr-rate-marine-envelope-v1/corr_rate_marine_envelope.py (byte-identical
# logic: comp_vector, env_features, load, build_matrix, metrics,
# classify_family, COMPOSITION, _FAMILY_RULES, HistGBM hyperparameters).
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


def fit_predict(Xtr, ytr, Xte):
    model = HistGradientBoostingRegressor(
        random_state=SEED, max_iter=300, learning_rate=0.05,
        max_depth=None, max_leaf_nodes=31, l2_regularization=1.0,
        early_stopping=False)
    model.fit(Xtr, ytr)
    return model.predict(Xte)


def main():
    rows, src_sha, n_raw = load()
    X, y, mats, envs, has_comp = build_matrix(rows)
    n = len(y)

    fam_list = [classify_family(m) for m in mats]
    classified_mask = np.array([f is not None for f in fam_list])
    families_all = np.array([f if f is not None else "unclassified" for f in fam_list])
    n_classified = int(classified_mask.sum())
    n_unclassified = int((~classified_mask).sum())
    family_coverage_pct = 100.0 * n_classified / n

    Xc, yc, matsc = X[classified_mask], y[classified_mask], mats[classified_mask]
    Xu, yu, matsu, envu = X[~classified_mask], y[~classified_mask], mats[~classified_mask], envs[~classified_mask]

    assert n_classified == 7282, "classified cohort size drifted from KPI's locked n=7282: %d" % n_classified
    assert n_unclassified > 0, "no unclassified rows found -- classifier coverage is 100pct, attack vacuous"

    has_comp_u = np.array([comp_vector(m)[1] for m in matsu])
    n_unclassified_with_known_composition = int(has_comp_u.sum())

    # --- REAL ATTACK: fit on ALL classified rows (deployed-equivalent full
    # fit, not a CV fold), predict on the never-scored unclassified holdout.
    pred_u = fit_predict(Xc, yc, Xu)
    rmse_u, mae_u, r2_u = metrics(yu, pred_u)

    glob = float(np.mean(yc))
    bl_glob = np.full(len(yu), glob)
    rmse_glob, mae_glob, r2_glob = metrics(yu, bl_glob)
    err_red = 100.0 * (1.0 - rmse_u / rmse_glob) if rmse_glob > 0 else float("nan")

    refutation_criterion = (
        "REFUTED if (a) unclassified-holdout gbm.r2 <= 0.0, OR (b) "
        "unclassified-holdout error_reduction_vs_global_mean_baseline_pct "
        "<= 0.0, fit on all 7282 classified rows / identical feature "
        "engineering / HistGBM hyperparameters / seed=0, evaluated on the "
        "417-row population classify_family() itself returns None for. "
        "SURVIVED otherwise, even if reduced relative to the within-"
        "taxonomy family-safe/LOFO/source-LOFO numbers."
    )
    refuted = (r2_u <= 0.0) or (err_red <= 0.0)
    verdict = "CLAIM_REFUTED" if refuted else "CLAIM_SURVIVED"

    # --- POSITIVE CONTROL: hostile-null full-label-shuffle of the SAME
    # unclassified-holdout targets (fixed seed, independent from SEED=0
    # model seed) -- must trigger the criterion.
    rng = np.random.RandomState(20260819)
    yu_shuffled = yu.copy()
    rng.shuffle(yu_shuffled)
    pred_u_shuf = pred_u  # model/predictions unchanged; only scoring target shuffled
    rmse_u_shuf, mae_u_shuf, r2_u_shuf = metrics(yu_shuffled, pred_u_shuf)
    rmse_glob_shuf, _, _ = metrics(yu_shuffled, bl_glob)
    err_red_shuf = 100.0 * (1.0 - rmse_u_shuf / rmse_glob_shuf) if rmse_glob_shuf > 0 else float("nan")
    positive_control_detected = bool((r2_u_shuf <= 0.0) or (err_red_shuf <= 0.0))

    # Per-family breakdown of the unclassified rows' nearest deployed
    # environment/material context (diagnostic only, not gating).
    material_sample = sorted(set(matsu.tolist()))[:25]

    canonical = {
        "schema": "amphora.barrier-corrosion-score.corr-rate-unclassified-holdout-attack.v1",
        "benchmark": "amphora-barrier-corrosion-score/corr-rate-unclassified-holdout-v1",
        "attacks_claim": (
            "evidence/phase0/kpis/corr-rate-family-safe-qspr-kpi.v1.dsse.json: "
            "GroupKFold(group=metallurgical_family, 5-fold) HistGBM R2=0.132087 "
            "on the NIST CORR-DATA classified subset (n=7282, 17 families), "
            "'the module's strongest rights-clean empirical claim'."
        ),
        "attack_description": (
            "Fits the identical HistGBM (same feature engineering/"
            "hyperparameters/seed=0) on ALL 7282 classified rows (the "
            "deployed-equivalent full fit), then scores it on the 417 "
            "rows classify_family() returns None for -- the population "
            "the KPI's own payload lists as an open Phase-1 gap "
            "('extend metallurgical-family taxonomy beyond the 94.58% "
            "keyword/regex classifier coverage'). This population has "
            "never been evaluated by any receipt in this module: every "
            "prior benchmark restricts to the classified_subset before "
            "any train/test split is drawn."
        ),
        "refutation_criterion": refutation_criterion,
        "dataset": {
            "name": "NIST CORR-DATA (Dow Chemical Co.) derived reference",
            "in_tree_path": SRC,
            "source_sha256": src_sha,
            "rights_class": "DERIVATIVE_ALLOWED",
            "n_raw_records": n_raw,
        },
        "cohort": {
            "full_cohort_n": n,
            "classified_subset_n": n_classified,
            "unclassified_holdout_n": n_unclassified,
            "family_coverage_pct": family_coverage_pct,
            "n_unclassified_with_known_composition_lookup": n_unclassified_with_known_composition,
            "n_unclassified_material_composition_unknown": n_unclassified - n_unclassified_with_known_composition,
            "unclassified_material_sample_first25_sorted": material_sample,
        },
        "results": {
            "unclassified_holdout": {
                "n_train": int(len(yc)), "n_test": int(len(yu)),
                "gbm": {"rmse": rmse_u, "mae": mae_u, "r2": r2_u},
                "baseline_global_mean": {"rmse": rmse_glob, "mae": mae_glob, "r2": r2_glob},
                "error_reduction_vs_global_mean_baseline_pct": err_red,
            },
        },
        "positive_control": {
            "planted_defect": "full random shuffle of the unclassified-holdout log10(corrosion rate) targets (y), fixed seed=20260819, applied AFTER prediction so the model's predictions are unchanged but the targets they are scored against are pure noise",
            "how_planted": "yu_shuffled = np.random.RandomState(20260819).shuffle(copy of yu); scored the SAME pred_u against yu_shuffled instead of yu",
            "detected": positive_control_detected,
            "evidence": {
                "shuffled_r2": round(r2_u_shuf, 6),
                "shuffled_error_reduction_vs_global_mean_baseline_pct": round(err_red_shuf, 6) if not math.isnan(err_red_shuf) else None,
                "criterion_fired": positive_control_detected,
            },
        },
        "verdict": verdict,
        "authority": "AUDIT_ONLY",
        "promotes_authority": False,
        "modifies_manifest": False,
        "scope_honesty": (
            "Diagnostic on bare metal/alloy substrate corrosion (NIST "
            "CORR-DATA), same scope ceiling as corr-rate-qspr-v1, "
            "corr-rate-family-safe-v1, corr-rate-family-lofo-v1, and "
            "corr-rate-marine-envelope-v1: NOT organic-coating barrier "
            "performance. No candidate/coating superiority claim; no "
            "batch-release, manufacturing-qualification, optimizer, or "
            "product-performance authority."
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
    print("n_classified", n_classified, "n_unclassified", n_unclassified)
    print("unclassified_holdout_r2", round(r2_u, 6))
    print("unclassified_holdout_err_red_pct", round(err_red, 6) if not math.isnan(err_red) else None)
    print("positive_control_detected", positive_control_detected)
    print("verdict", verdict)


if __name__ == "__main__":
    main()
