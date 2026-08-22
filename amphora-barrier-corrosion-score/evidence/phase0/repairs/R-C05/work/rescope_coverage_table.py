#!/usr/bin/env python3
"""corr-rate-conformal-per-environment-coverage-v1 -- RE-SCOPE deliverable for
R-C05 (fire 3 of 3, the final permitted fire).

CONTEXT: campaign item R-C05 pre-registered acceptance ("both directions
reach >= 0.88 observed coverage at the 0.90 target using a Mondrian
chloride-environment-class calibrator") was tried in fire 1 (empirical:
best variant 0.877389, 8 rows short) and fire 2 (analytic: PROVEN
structurally impossible for ANY Mondrian-by-chloride-class hyperparameter,
because 6 of 8 chloride classes have EXACTLY ZERO marine-calibration rows in
the reverse leg, forcing 75.9% of reverse-leg test rows to the pooled
fallback regardless of tuning; a supplementary reweighted-conformal probe
failed an order of magnitude worse, AUC=1.0 domain separability). Fire 2's
STATE.json recommended fire 3 invoke the item's own pre-registered re-scope
hatch: "per-environment coverage table as the new claim if stratification
cannot reach 0.88."

THIS SCRIPT invokes that hatch. It reuses the IDENTICAL data load, feature
scheme, base model, group_split, and cal/test marine-axis partition as the
refuting receipt and both prior repair fires (byte-identical logic, copied
verbatim), and reports, per direction and per chloride-environment class:
  - n_test rows in that class
  - n_cal (marine or nonmarine, per direction) rows available for that class
  - observed coverage for that class's test rows under the BEST mechanism
    found so far (conservative-floor Mondrian, fire 1) and under the
    ORIGINAL pooled/marginal calibrator (the refuted mechanism), side by
    side, so the table is honest about what is and is not gained.
  - whether that class has ANY marine-calibration support in the reverse
    direction (the structural fact fire 2 proved determines coverage).

This is NOT a new attempt to clear 0.88 pooled -- it is the re-scope
deliverable itself: the new claim is the TABLE, not a single pooled number.

Deterministic: OMP_NUM_THREADS=1, fixed seed, no timestamp, floats round(.,6).
AUDIT_ONLY: creates no coating-barrier ranking authority; does not promote;
does not modify the manifest or any locked dataset/signed KPI.
"""
import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
import json, hashlib, math, sys
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor

SRC = "feedback/v1/derived/nist_corr_reference.json"
SEED = 0
NDEC = 6
ACCEPTANCE_FLOOR = 0.88
MONDRIAN_MIN_CLASS_N = 5

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
            sulfuric, alkali, marine, salt, water, is_acid], bool(chloride or marine)


def chloride_env_class(ev):
    (chloride, fluoride, bromide, halide, ox_acid, red_acid, org_acid,
     sulfuric, alkali, marine, salt, water, is_acid) = ev
    if halide:
        return "halide"
    if alkali:
        return "alkali"
    if sulfuric:
        return "sulfuric"
    if org_acid:
        return "organic_acid"
    if is_acid:
        return "other_acid"
    if water:
        return "water"
    if salt:
        return "salt_other"
    return "other"


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
    X, y, mats, chl, cls = [], [], [], [], []
    for mat, env, temp, ly in rows:
        cv, _ = comp_vector(mat)
        ev, is_marine = env_features(env)
        tnum = float(temp) if temp is not None else float("nan")
        tmiss = 0.0 if temp is not None else 1.0
        X.append(cv + ev + [tnum, tmiss])
        y.append(ly)
        mats.append(mat)
        chl.append(is_marine)
        cls.append(chloride_env_class(ev))
    return (np.array(X, float), np.array(y, float), np.array(mats),
            np.array(chl, bool), np.array(cls, object))


def new_model():
    return HistGradientBoostingRegressor(
        random_state=SEED, max_iter=300, learning_rate=0.05,
        max_depth=None, max_leaf_nodes=31, l2_regularization=1.0,
        early_stopping=False)


def group_split(mats):
    uniq = sorted(set(mats.tolist()))
    role = {}
    for i, m in enumerate(uniq):
        b = i % 5
        role[m] = "test" if b == 0 else ("cal" if b == 1 else "train")
    tr = np.array([role[m] == "train" for m in mats])
    ca = np.array([role[m] == "cal" for m in mats])
    te = np.array([role[m] == "test" for m in mats])
    return tr, ca, te, uniq, role


def conf_quantile(scores, alpha):
    s = np.sort(np.asarray(scores, float))
    n = len(s)
    if n == 0:
        return float("inf")
    k = math.ceil((n + 1) * (1.0 - alpha))
    if k > n:
        return float("inf")
    return float(s[k - 1])


def binom_test_less(n_success, n_trials, p0):
    if n_trials == 0:
        return 1.0
    from math import lgamma, log, exp
    def log_binom_pmf(k, n, p):
        if p <= 0.0:
            return 0.0 if k == 0 else float("-inf")
        if p >= 1.0:
            return 0.0 if k == n else float("-inf")
        lc = lgamma(n + 1) - lgamma(k + 1) - lgamma(n - k + 1)
        return lc + k * log(p) + (n - k) * log(1 - p)
    logs = [log_binom_pmf(k, n_trials, p0) for k in range(0, n_success + 1)]
    m = max(logs)
    total = sum(exp(v - m) for v in logs)
    return float(min(1.0, exp(m) * total))


def per_class_table(X, y, mu, cal_mask, test_mask, cls_arr, alpha=0.10,
                     min_class_n=MONDRIAN_MIN_CLASS_N):
    p_ca = mu.predict(X[cal_mask])
    p_te = mu.predict(X[test_mask])
    s_ca = np.abs(y[cal_mask] - p_ca)
    errs_te = np.abs(y[test_mask] - p_te)
    classes_ca = cls_arr[cal_mask]
    classes_te = cls_arr[test_mask]

    q_pooled = conf_quantile(s_ca, alpha)
    covered_pooled_all = errs_te <= (q_pooled + 1e-12)

    class_q_conservative = {}
    all_classes = sorted(set(classes_ca.tolist()) | set(classes_te.tolist()))
    for c in all_classes:
        s_c = s_ca[classes_ca == c]
        if len(s_c) >= min_class_n:
            own_q = conf_quantile(s_c, alpha)
            class_q_conservative[c] = max(own_q, q_pooled)
        else:
            class_q_conservative[c] = q_pooled
    half_cons = np.array([class_q_conservative[c] for c in classes_te], dtype=float)
    covered_cons_all = errs_te <= (half_cons + 1e-12)

    table = {}
    for c in all_classes:
        m = classes_te == c
        n_te_c = int(m.sum())
        n_ca_c = int((classes_ca == c).sum())
        if n_te_c == 0:
            table[c] = {"n_test": 0, "n_cal": n_ca_c,
                        "has_marine_calibration_support": n_ca_c > 0,
                        "pooled_coverage": None, "conservative_mondrian_coverage": None}
            continue
        cov_pooled_c = float(np.mean(covered_pooled_all[m]))
        cov_cons_c = float(np.mean(covered_cons_all[m]))
        table[c] = {
            "n_test": n_te_c,
            "n_cal": n_ca_c,
            "has_marine_calibration_support": n_ca_c > 0,
            "used_own_quantile_in_conservative_mechanism": n_ca_c >= min_class_n,
            "pooled_coverage": round(cov_pooled_c, NDEC),
            "conservative_mondrian_coverage": round(cov_cons_c, NDEC),
            "n_covered_pooled": int(np.sum(covered_pooled_all[m])),
            "n_covered_conservative_mondrian": int(np.sum(covered_cons_all[m])),
        }
    overall = {
        "n_test": int(test_mask.sum()),
        "pooled_coverage": round(float(np.mean(covered_pooled_all)), NDEC),
        "conservative_mondrian_coverage": round(float(np.mean(covered_cons_all)), NDEC),
        "meets_acceptance_floor_0.88_pooled": bool(np.mean(covered_pooled_all) >= ACCEPTANCE_FLOOR - 1e-9),
        "meets_acceptance_floor_0.88_conservative_mondrian": bool(np.mean(covered_cons_all) >= ACCEPTANCE_FLOOR - 1e-9),
    }
    return table, overall


def run():
    rows, src_sha, n_raw = load()
    X, y, mats, marine, cls_arr = build_matrix(rows)
    tr, ca0, te0, uniq_mats, role = group_split(mats)
    heldout = ~tr
    mu = new_model().fit(X[tr], y[tr])

    fwd_cal, fwd_test = heldout & ~marine, heldout & marine
    rev_cal, rev_test = heldout & marine, heldout & ~marine

    fwd_table, fwd_overall = per_class_table(X, y, mu, fwd_cal, fwd_test, cls_arr,
                                              alpha=0.10)
    rev_table, rev_overall = per_class_table(X, y, mu, rev_cal, rev_test, cls_arr,
                                              alpha=0.10)

    classes_covered_reverse = [c for c, v in rev_table.items()
                                if v["n_test"] > 0 and v["has_marine_calibration_support"]]
    classes_uncovered_reverse = [c for c, v in rev_table.items()
                                  if v["n_test"] > 0 and not v["has_marine_calibration_support"]]
    n_test_uncovered = sum(rev_table[c]["n_test"] for c in classes_uncovered_reverse)
    n_test_covered = sum(rev_table[c]["n_test"] for c in classes_covered_reverse)

    out = {
        "schema": "amphora.barrier-corrosion-score.corr-rate-conformal-per-environment-coverage.v1",
        "module": "amphora-barrier-corrosion-score",
        "benchmark": "corr-rate-conformal-per-environment-coverage-v1",
        "repair_item": "R-C05",
        "resolution": "rescope",
        "authority": "AUDIT_ONLY",
        "promotes_authority": False,
        "rescope_rationale": (
            "Pre-registered acceptance (both directions >= 0.88 pooled coverage "
            "via Mondrian chloride-environment-class calibration) is now shown "
            "structurally unreachable: fire 1 (empirical, best variant 0.877389, "
            "8 rows short) and fire 2 (analytic proof: 6/8 chloride classes have "
            "EXACTLY ZERO marine-calibration rows in the reverse leg, forcing "
            "75.9% of test rows to the pooled fallback regardless of "
            "hyperparameter; supplementary reweighted-conformal probe failed an "
            "order of magnitude worse, domain-classifier AUC=1.0). This is fire "
            "3 of max_fires=3, the final permitted fire; the item's own "
            "pre-registered re-scope hatch is invoked: the per-environment-class "
            "coverage table below becomes the claim in place of a single pooled "
            ">=0.88 number, honestly reporting which chloride-environment "
            "classes ARE and are NOT covered by any calibration mechanism "
            "tried."),
        "dataset": {
            "name": "NIST CORR-DATA (Dow Chemical Co.) derived reference",
            "in_tree_path": SRC,
            "source_sha256": src_sha,
            "rights_class": "DERIVATIVE_ALLOWED",
            "license": "NIST public data",
            "n_raw_records": n_raw,
        },
        "protocol_note": (
            "IDENTICAL data load, feature scheme, base model (HistGradientBoostingRegressor, "
            "seed=0), group_split (bucket=idx%5, train={2,3,4}), and marine-axis cal/test "
            "assignment (forward: cal=nonmarine,test=marine; reverse: cal=marine,test=nonmarine) "
            "as the refuting receipt corr-rate-conformal-domain-shift-v1 and both prior R-C05 "
            "fires. alpha=0.10 (0.90 target). Two calibrators reported side-by-side per class: "
            "'pooled' = the ORIGINAL refuted marginal calibrator (single direction-level quantile "
            "applied to every class); 'conservative_mondrian' = fire 1's best repair variant "
            "(per-class quantile clamped to >= pooled, min_class_n=5)."),
        "forward_calibrate_nonmarine_deploy_marine": {
            "overall": fwd_overall,
            "per_chloride_environment_class": fwd_table,
        },
        "reverse_calibrate_marine_deploy_nonmarine": {
            "overall": rev_overall,
            "per_chloride_environment_class": rev_table,
            "classes_with_marine_calibration_support": sorted(classes_covered_reverse),
            "classes_with_zero_marine_calibration_support": sorted(classes_uncovered_reverse),
            "n_test_rows_in_classes_with_support": n_test_covered,
            "n_test_rows_in_classes_without_support": n_test_uncovered,
            "fraction_test_rows_without_any_calibration_support": round(
                n_test_uncovered / (n_test_covered + n_test_uncovered), NDEC)
                if (n_test_covered + n_test_uncovered) else None,
        },
        "prior_acceptance_status": {
            "floor": ACCEPTANCE_FLOOR,
            "forward_meets_floor": fwd_overall["meets_acceptance_floor_0.88_conservative_mondrian"],
            "reverse_meets_floor": rev_overall["meets_acceptance_floor_0.88_conservative_mondrian"],
            "both_directions_meet_floor": bool(
                fwd_overall["meets_acceptance_floor_0.88_conservative_mondrian"]
                and rev_overall["meets_acceptance_floor_0.88_conservative_mondrian"]),
        },
    }
    return out


def rnd(o):
    if isinstance(o, float):
        return None if math.isnan(o) else round(o, NDEC)
    if isinstance(o, dict):
        return {k: rnd(o[k]) for k in sorted(o)}
    if isinstance(o, list):
        return [rnd(v) for v in o]
    return o


def canonical(obj):
    return json.dumps(rnd(obj), indent=2, sort_keys=True, ensure_ascii=True)


if __name__ == "__main__":
    outfile = sys.argv[1] if len(sys.argv) > 1 else None
    result = run()
    txt = canonical(result)
    if outfile:
        open(outfile, "w").write(txt + "\n")
        print("wrote", outfile, "sha256",
              hashlib.sha256((txt + "\n").encode()).hexdigest())
    else:
        print(txt)
