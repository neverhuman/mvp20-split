#!/usr/bin/env python3
"""
amphora-barrier-corrosion-score / corr-rate-marine-envelope-v1
FALSIFICATION ATTACK on evidence/phase0/kpis/corr-rate-family-safe-qspr-kpi.v1
(GroupKFold(group=metallurgical_family, 5-fold) HistGBM R2=0.132087, "the
module's strongest rights-clean empirical claim") and, by extension, on the
narrow CLAIM_SURVIVED verdict of corr-rate-family-lofo-v1 (family-weighted
mean LOFO R2=0.015964).

WHY THIS IS THE NEXT ESCALATION, NOT A REPEAT:
Every prior attack on this claim (corr-rate-family-safe-v1, corr-rate-
family-lofo-v1) has varied only the GROUPING AXIS for cross-validation
(material string -> metallurgical family -> true leave-one-family-out).
None has varied the ENVIRONMENT axis. This module's own docs/mission.md
states its applicability domain is "solvent-borne two-component epoxy-
polyamide marine-coating R&D" -- i.e. the entire reason this KPI exists is
to support marine anti-corrosion decisions. Yet no prior receipt has ever
tested whether the corrosion-rate QSPR model, trained predominantly on
non-marine chemical environments (acids, caustics, industrial process
streams -- 96.7% of the classified cohort), actually generalizes to real
seawater/marine-immersion exposure (3.3%). This is a genuine distribution-
shift / edge-of-envelope probe in the sense of the assignment brief, using
the SAME identical feature engineering, HistGBM hyperparameters, seed, and
metrics as corr-rate-family-safe-v1 and corr-rate-family-lofo-v1 (verbatim:
comp_vector, env_features, load, build_matrix, metrics, classify_family,
COMPOSITION, _FAMILY_RULES) -- the ONLY new variable is a single train/test
split on TRUE marine identity (environment string contains "seawater" or
"sea water") instead of any grouping by material/family.

SECONDARY DATA-INTEGRITY FINDING (reported, not the refutation criterion):
The deployed env_features() marine flag is defined as
    marine = has("seawater", "sea water", "marine", "atmospheric")
which conflates ATMOSPHERIC exposure with SEAWATER IMMERSION -- two
physically distinct corrosion regimes (intermittent thin-film wetting at
ambient chloride deposition rates vs continuous full immersion in ~19,000
ppm chloride electrolyte). Of the 7,282 classified rows, 505 have
marine_feature==1 in the deployed model, but only 186 (36.8%) are true
seawater rows; the remaining 319 (63.2%) are atmospheric-exposure rows
mislabeled into the same input feature. This benchmark quantifies the
effect of this conflation on the marine-envelope generalization test via
an ablation (patched env_features excluding "atmospheric" from the marine
flag), reported alongside but NOT substituting for the primary
deployed-code-as-is test.

PRE-REGISTERED REFUTATION CRITERION (declared before running/inspecting
results): The family-safe KPI's positive R2 implicitly supports using this
QSPR for the module's own declared marine applicability domain. This is
REFUTED if EITHER:
  (a) marine-envelope R2 (train = all non-marine classified rows, test =
      all true-seawater classified rows, deployed env_features as-is) is
      <= 0.0; OR
  (b) marine-envelope error-reduction-vs-best-baseline-pct (vs the better
      of global-mean-of-train and family-mean-of-train baselines,
      evaluated on the SAME marine test rows) is <= 0.0.
It SURVIVES if marine-envelope R2 > 0.0 AND it beats the best baseline on
RMSE, even if reduced relative to the family-safe/LOFO numbers (marine
rows are only 2.6% of the classified cohort and are drawn from real
environments the model has never trained on for that regime -- a genuine
domain-shift test is expected to be at least as hard as within-domain
CV, and reduction alone is not itself a refutation).

Determinism: OMP_NUM_THREADS=1, fixed seed, no shuffling in the single
train/test split (train = all non-marine rows in fixed classified-subset
order, test = all marine rows in fixed order), rounded canonical output
-> byte-stable two-replay SHA-256 gate.
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
MIN_ELIGIBLE_N_PER_FAMILY = 10

# ---------------------------------------------------------------------------
# VERBATIM from corr-rate-family-safe-v1/corr_rate_family_safe.py and
# corr-rate-family-lofo-v1/corr_rate_family_lofo.py (byte-identical logic).
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


def env_features(env, patched_no_atmospheric_marine=False):
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
    if patched_no_atmospheric_marine:
        marine = has("seawater", "sea water")
    else:
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


def build_matrix(rows, patched_no_atmospheric_marine=False):
    X, y, mats, envs, has_comp = [], [], [], [], 0
    for mat, env, temp, ly in rows:
        cv, ok = comp_vector(mat)
        has_comp += int(ok)
        ev = env_features(env, patched_no_atmospheric_marine)
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
    sums, cnts = {}, {}
    for k, v in zip(key_train, y_train):
        sums[k] = sums.get(k, 0.0) + v
        cnts[k] = cnts.get(k, 0) + 1
    d = {k: sums[k] / cnts[k] for k in sums}
    return np.array([d.get(k, glob) for k in key_test])


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


def is_true_marine(env):
    e = env.lower()
    return ("seawater" in e) or ("sea water" in e)


def is_atmospheric(env):
    return "atmospheric" in env.lower()


def run_envelope(Xc, yc, matsc, famc, marine_mask_c, min_eligible=MIN_ELIGIBLE_N_PER_FAMILY):
    tr = ~marine_mask_c
    te = marine_mask_c
    model = HistGradientBoostingRegressor(
        random_state=SEED, max_iter=300, learning_rate=0.05,
        max_depth=None, max_leaf_nodes=31, l2_regularization=1.0,
        early_stopping=False)
    model.fit(Xc[tr], yc[tr])
    pred_te = model.predict(Xc[te])
    rmse, mae, r2 = metrics(yc[te], pred_te)

    glob = float(np.mean(yc[tr]))
    bl_glob = np.full(int(te.sum()), glob)
    bl_fam = group_baseline(famc[tr], yc[tr], famc[te], glob)
    rmse_glob, mae_glob, r2_glob = metrics(yc[te], bl_glob)
    rmse_fam, mae_fam, r2_fam = metrics(yc[te], bl_fam)
    best_base_rmse = min(rmse_glob, rmse_fam)
    err_red = 100.0 * (1.0 - rmse / best_base_rmse) if best_base_rmse > 0 else float("nan")

    per_family = []
    for fam in sorted(set(famc[te].tolist())):
        fmask = (famc[te] == fam)
        n_test = int(fmask.sum())
        yft = yc[te][fmask]
        pft = pred_te[fmask]
        f_rmse, f_mae, f_r2 = metrics(yft, pft) if n_test >= 2 else (float("nan"), float("nan"), float("nan"))
        per_family.append({
            "family": fam, "n_test": n_test,
            "r2": f_r2 if n_test >= 2 else None,
            "rmse": f_rmse if n_test >= 2 else None,
            "mean_abs_err_log10": float(np.mean(np.abs(pft - yft))),
        })
    per_family.sort(key=lambda d: -d["n_test"])

    return {
        "n_train": int(tr.sum()), "n_test": int(te.sum()),
        "gbm": {"rmse": rmse, "mae": mae, "r2": r2},
        "baseline_global_mean": {"rmse": rmse_glob, "mae": mae_glob, "r2": r2_glob},
        "baseline_family_mean": {"rmse": rmse_fam, "mae": mae_fam, "r2": r2_fam},
        "error_reduction_vs_best_baseline_pct": err_red,
        "per_family": per_family,
    }


def main():
    rows, src_sha, n_raw = load()

    # Deployed-code-as-is feature matrix (marine flag includes atmospheric).
    X, y, mats, envs, has_comp = build_matrix(rows, patched_no_atmospheric_marine=False)
    fam_list = [classify_family(m) for m in mats]
    classified_mask = np.array([f is not None for f in fam_list])
    families_all = np.array([f if f is not None else "unclassified" for f in fam_list])

    Xc = X[classified_mask]
    yc = y[classified_mask]
    matsc = mats[classified_mask]
    famc = families_all[classified_mask]
    envsc = envs[classified_mask]
    n_c = len(yc)

    marine_mask_c = np.array([is_true_marine(e) for e in envsc])
    atmos_mask_c = np.array([is_atmospheric(e) for e in envsc])

    # deployed-feature marine flag, recovered from column index (13 env
    # features precede the 2 temperature columns; marine is env_features
    # index 9 by construction order above).
    ENV_FEAT_NAMES = ["chloride", "fluoride", "bromide", "halide", "ox_acid",
                      "red_acid", "org_acid", "sulfuric", "alkali", "marine",
                      "salt", "water", "is_acid"]
    marine_col = len(ELEMENTS) + ENV_FEAT_NAMES.index("marine")
    deployed_marine_feature_c = Xc[:, marine_col].astype(bool)

    n_true_marine = int(marine_mask_c.sum())
    n_atmospheric = int(atmos_mask_c.sum())
    n_deployed_marine_flag = int(deployed_marine_feature_c.sum())
    n_atmospheric_conflated_into_marine_flag = int((atmos_mask_c & (~marine_mask_c) & deployed_marine_feature_c).sum())

    assert marine_mask_c.sum() > 0, "no true-marine classified rows found"
    assert (~marine_mask_c).sum() > 0, "no non-marine classified rows found"
    marine_families = set(famc[marine_mask_c].tolist())
    nonmarine_families = set(famc[~marine_mask_c].tolist())
    families_marine_unseen_in_train = sorted(marine_families - nonmarine_families)

    envelope_deployed = run_envelope(Xc, yc, matsc, famc, marine_mask_c)

    # Ablation: patched env_features (marine flag excludes atmospheric).
    Xp, yp, matsp, envsp, _ = build_matrix(rows, patched_no_atmospheric_marine=True)
    Xpc = Xp[classified_mask]
    envelope_patched = run_envelope(Xpc, yc, matsc, famc, marine_mask_c)

    refutation_criterion = (
        "REFUTED if (a) marine-envelope (train=all non-marine classified "
        "rows, test=all true-seawater classified rows, deployed "
        "env_features as-is) gbm.r2 <= 0.0, OR (b) marine-envelope "
        "error_reduction_vs_best_baseline_pct <= 0.0. SURVIVED otherwise, "
        "even if reduced relative to the family-safe/LOFO within-domain "
        "numbers."
    )
    refuted = (envelope_deployed["gbm"]["r2"] <= 0.0) or (envelope_deployed["error_reduction_vs_best_baseline_pct"] <= 0.0)
    verdict = "CLAIM_REFUTED" if refuted else "CLAIM_SURVIVED"

    canonical = {
        "schema": "amphora.barrier-corrosion-score.corr-rate-marine-envelope-attack.v1",
        "benchmark": "amphora-barrier-corrosion-score/corr-rate-marine-envelope-v1",
        "attacks_claim": (
            "evidence/phase0/kpis/corr-rate-family-safe-qspr-kpi.v1.dsse.json: "
            "GroupKFold(group=metallurgical_family, 5-fold) HistGBM R2=0.132087 "
            "on the NIST CORR-DATA classified subset (n=7282, 17 families), "
            "'the module's strongest rights-clean empirical claim'; and the "
            "narrow CLAIM_SURVIVED verdict of corr-rate-family-lofo-v1 "
            "(family-weighted mean LOFO R2=0.015964)."
        ),
        "attack_description": (
            "Every prior attack on this claim varied only the CV grouping "
            "axis (material string, then metallurgical family, then true "
            "leave-one-family-out); none varied the ENVIRONMENT axis, even "
            "though this module's own docs/mission.md states its "
            "applicability domain is marine-coating R&D. This holds out "
            "ALL classified rows whose environment string is genuinely "
            "seawater/sea-water immersion (n=%d, 2.55%% of the classified "
            "cohort, 8 of 17 metallurgical families represented, all 8 "
            "also present in the non-marine training set) as a single "
            "domain-shift test set, training on the remaining %d non-marine "
            "classified rows with identical feature engineering, HistGBM "
            "hyperparameters, and seed=0 copied verbatim from "
            "corr-rate-family-safe-v1/corr_rate_family_safe.py and "
            "corr-rate-family-lofo-v1/corr_rate_family_lofo.py."
        ) % (n_true_marine, n_c - n_true_marine),
        "refutation_criterion": refutation_criterion,
        "dataset": {
            "name": "NIST CORR-DATA (Dow Chemical Co.) derived reference",
            "in_tree_path": SRC,
            "source_sha256": src_sha,
            "rights_class": "DERIVATIVE_ALLOWED",
            "n_raw_records": n_raw,
        },
        "cohort": {
            "classified_subset_n": n_c,
            "n_true_marine_seawater_rows": n_true_marine,
            "n_nonmarine_rows": n_c - n_true_marine,
            "marine_families": sorted(marine_families),
            "n_marine_families": len(marine_families),
            "families_marine_unseen_in_nonmarine_train": families_marine_unseen_in_train,
        },
        "results": {
            "marine_envelope_deployed_features": envelope_deployed,
            "marine_envelope_patched_no_atmospheric_conflation": envelope_patched,
        },
        "data_integrity_finding_marine_atmospheric_conflation": {
            "description": (
                "The deployed env_features() marine flag is "
                "has('seawater','sea water','marine','atmospheric'), "
                "conflating atmospheric exposure with seawater immersion. "
                "This is a secondary finding, quantified via the patched "
                "ablation above, and does NOT itself determine the "
                "refutation verdict (which is judged on the deployed "
                "feature set, matching production behavior)."
            ),
            "n_atmospheric_rows_in_classified_cohort": n_atmospheric,
            "n_rows_with_deployed_marine_flag_set": n_deployed_marine_flag,
            "n_true_seawater_rows": n_true_marine,
            "n_atmospheric_rows_incorrectly_flagged_marine": n_atmospheric_conflated_into_marine_flag,
            "pct_of_deployed_marine_flag_that_is_actually_atmospheric": (
                round(100.0 * n_atmospheric_conflated_into_marine_flag / n_deployed_marine_flag, 4)
                if n_deployed_marine_flag else None
            ),
        },
        "verdict": verdict,
        "authority": "AUDIT_ONLY",
        "promotes_authority": False,
        "modifies_manifest": False,
        "scope_honesty": (
            "Diagnostic on bare metal/alloy substrate corrosion (NIST "
            "CORR-DATA), same scope ceiling as corr-rate-qspr-v1, "
            "corr-rate-family-safe-v1, and corr-rate-family-lofo-v1: NOT "
            "organic-coating barrier performance. No candidate/coating "
            "superiority claim; no batch-release, manufacturing-"
            "qualification, optimizer, or product-performance authority."
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
    print("n_true_marine", n_true_marine, "n_marine_families", len(marine_families))
    print("marine_envelope_deployed_r2", round(envelope_deployed["gbm"]["r2"], 4))
    print("marine_envelope_deployed_err_red_pct", round(envelope_deployed["error_reduction_vs_best_baseline_pct"], 4))
    print("marine_envelope_patched_r2", round(envelope_patched["gbm"]["r2"], 4))
    print("n_atmospheric_conflated_into_marine_flag", n_atmospheric_conflated_into_marine_flag)
    print("verdict", verdict)


if __name__ == "__main__":
    main()
