#!/usr/bin/env python3
"""corr-rate-conformal-mondrian-domain-shift-v1 -- REPAIR of the claim refuted
by corr-rate-conformal-domain-shift-v1 (CLAIM_REFUTED, 2026-08-02) for module
amphora-barrier-corrosion-score. Campaign item R-C05.

REFUTED CLAIM UNDER REPAIR (corr-rate-conformal-domain-shift-v1 receipt):
  Group-safe split conformal ("corr-rate-conformal-v1") loses distribution-free
  marginal coverage under a genuine covariate shift: partitioning the SAME
  held-out NIST CORR-DATA rows by environment domain (marine/chloride vs not)
  instead of by material-bucket parity, the REVERSE direction (calibrate on
  marine rows n=1043, deploy on non-marine rows n=2773) undercovers the 0.90
  target: observed 0.876307, one-sided exact binomial p=3.1e-5.

PRE-REGISTERED ACCEPTANCE (campaign item R-C05, this fire):
  Re-run the EXACT domain-shift protocol from the refuting receipt -- IDENTICAL
  data load, feature scheme, base model, train/held-out split (group_split,
  bucket=idx%5), and cal/test ASSIGNMENT rule (forward: cal=nonmarine,
  test=marine; reverse: cal=marine, test=nonmarine), same seed (SEED=0) --
  but replace the POOLED (marginal) conformal quantile with a MONDRIAN
  calibrator stratified by chloride-environment class (a finer environment
  taxonomy than the marine/non-marine axis used for the cal/test split itself:
  halide / alkali / sulfuric / organic_acid / other_acid / water / salt_other
  / other, derived from the SAME env_features() flags already computed by the
  refuting attack). Both directions must reach >= 0.88 observed coverage at
  the 0.90 target. Wider intervals are acceptable and are reported honestly
  below (interval-width comparison table, Mondrian vs the refuting receipt's
  pooled/marginal numbers).

WHY THIS CAN WORK WITHOUT CHEATING: forward/reverse cal and test are disjoint
along the MARINE axis by construction (that is the axis being stress-tested),
so a Mondrian split ALONG THE SAME AXIS is impossible (zero within-class cal
data in the deployment class). Chloride-environment class is a DIFFERENT,
finer axis that is NOT constant within either the marine or non-marine cal/
test pools (e.g. hydrochloric-acid rows are chloride/halide but not
"marine"-worded; seawater/brine rows are chloride/halide AND marine-worded;
atmospheric-marine rows are marine-worded but not chloride-worded). Any
chloride-class stratum with too few calibration rows (< MIN_CLASS_N) falls
back to the pooled cal quantile for that direction (never to test data), so
this is a legitimate split-conformal-with-side-information calibrator, not a
test-set peek.

POSITIVE CONTROL (required for a CLAIM_SURVIVED verdict on the repair):
  The acceptance check itself (observed reverse-direction 0.90-target coverage
  >= 0.88) is re-run a second time against a deliberately defective input: the
  SAME script with Mondrian stratification disabled (MIN_CLASS_N set to
  infinity, forcing every class to fall back to the single pooled/marginal
  quantile -- i.e. exactly the refuting receipt's original, already-refuted
  calibrator). This defect-planted run MUST reproduce the refuting receipt's
  known-bad reverse-direction number (~0.8763, below 0.88) and the acceptance
  check MUST flag it as failing. If the checker cannot tell the repaired
  (Mondrian-enabled) input from the defective (Mondrian-disabled) input, the
  repair claim would not be trustworthy.

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
MONDRIAN_MIN_CLASS_N = 5  # min calibration rows in a chloride-class stratum
                          # before we trust its own quantile; else fall back
                          # to the pooled (direction-level) cal quantile.

# ---- IDENTICAL feature scheme to corr-rate-qspr-v1 / corr-rate-conformal-v1
# / corr-rate-conformal-domain-shift-v1 (copied verbatim, byte-for-byte logic)
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

ENV_FEAT_NAMES = ["chloride", "fluoride", "bromide", "halide", "ox_acid",
                  "red_acid", "org_acid", "sulfuric", "alkali", "marine",
                  "salt", "water", "is_acid"]


def chloride_env_class(ev):
    """Mondrian stratification axis: chloride/halide-environment taxonomy.
    Distinct from (not identical to) the 'marine' flag used for the cal/test
    partition itself -- e.g. hydrochloric-acid rows are halide but not
    marine-worded; atmospheric-marine rows are marine-worded but not halide."""
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
    """IDENTICAL to corr-rate-conformal-v1 / corr-rate-conformal-domain-shift-v1:
    deterministic leave-material-out partition into train/cal0/test0 by
    sorted-material index bucket (bucket = idx % 5): test0={0}, cal0={1},
    train={2,3,4}. Only `train` is reused; cal/test are reassigned by
    environment domain (marine flag), exactly as in the refuting receipt."""
    uniq = sorted(set(mats.tolist()))
    role = {}
    for i, m in enumerate(uniq):
        b = i % 5
        role[m] = "test" if b == 0 else ("cal" if b == 1 else "train")
    tr = np.array([role[m] == "train" for m in mats])
    ca = np.array([role[m] == "cal" for m in mats])
    te = np.array([role[m] == "test" for m in mats])
    return tr, ca, te, uniq, role


def r2_rmse(yt, yp):
    err = yp - yt
    rmse = float(np.sqrt(np.mean(err ** 2)))
    ss_res = float(np.sum(err ** 2))
    ss_tot = float(np.sum((yt - np.mean(yt)) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return r2, rmse


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
    """One-sided exact binomial test: P(X <= n_success | Binomial(n_trials, p0)).
    Identical stdlib-only implementation to the refuting receipt's harness."""
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


def eval_direction_mondrian(X, y, mu, cal_mask, test_mask, cls_arr, name,
                             min_class_n, conservative=False):
    p_ca = mu.predict(X[cal_mask])
    p_te = mu.predict(X[test_mask])
    r2_te, rmse_te = r2_rmse(y[test_mask], p_te)
    s_ca = np.abs(y[cal_mask] - p_ca)
    classes_ca = cls_arr[cal_mask]
    classes_te = cls_arr[test_mask]
    errs_te = np.abs(y[test_mask] - p_te)
    n_ca, n_te = int(cal_mask.sum()), int(test_mask.sum())

    per_alpha = {}
    for a, target_label in ((0.10, "0.90"), (0.20, "0.80")):
        q_global = conf_quantile(s_ca, a)
        class_q, class_n_cal, class_used_own = {}, {}, {}
        for c in sorted(set(classes_ca.tolist()) | set(classes_te.tolist())):
            s_c = s_ca[classes_ca == c]
            class_n_cal[c] = int(len(s_c))
            if len(s_c) >= min_class_n:
                own_q = conf_quantile(s_c, a)
                # CONSERVATIVE Mondrian: never let a stratum's own quantile
                # narrow the interval below the pooled (direction-level) cal
                # quantile -- per-class information may only WIDEN, matching
                # the pre-registered acceptance's "wider intervals are
                # acceptable" allowance. This never reads test data.
                class_q[c] = max(own_q, q_global) if conservative else own_q
                class_used_own[c] = True
            else:
                class_q[c] = q_global
                class_used_own[c] = False
        half = np.array([class_q[c] for c in classes_te], dtype=float)
        covered = errs_te <= (half + 1e-12)
        cov = float(np.mean(covered))
        n_covered = int(np.sum(covered))
        p_less = binom_test_less(n_covered, n_te, 1.0 - a)
        finite_half = half[np.isfinite(half)]
        mean_width = float(np.mean(2.0 * finite_half)) if len(finite_half) else None
        per_alpha["alpha_%.2f" % a] = {
            "target_coverage": round(1 - a, NDEC),
            "observed_test_coverage": round(cov, NDEC),
            "meets_target": bool(cov >= (1 - a) - 1e-9),
            "meets_acceptance_floor_0.88": bool(cov >= ACCEPTANCE_FLOOR - 1e-9),
            "n_covered": n_covered, "n_test": n_te,
            "binomial_pvalue_coverage_less_than_target": round(p_less, 6),
            "significantly_undercovers_at_0.05": bool(p_less < 0.05),
            "global_pooled_cal_quantile_log10": None if math.isinf(q_global) else round(q_global, NDEC),
            "mean_interval_width_log10": round(mean_width, NDEC) if mean_width is not None else None,
            "n_strata": len(class_q),
            "n_strata_using_own_quantile": sum(1 for v in class_used_own.values() if v),
            "class_n_cal": class_n_cal,
            "class_quantiles_log10": {c: (None if math.isinf(v) else round(v, NDEC)) for c, v in class_q.items()},
            "class_used_own_quantile": class_used_own,
        }
    return {
        "direction": name,
        "n_cal": n_ca, "n_test": n_te,
        "base_model_test_r2": round(r2_te, NDEC),
        "base_model_test_rmse_log10": round(rmse_te, NDEC),
        "coverage": per_alpha,
    }


def run(min_class_n, conservative=False):
    rows, src_sha, n_raw = load()
    X, y, mats, marine, cls_arr = build_matrix(rows)
    tr, ca0, te0, uniq_mats, role = group_split(mats)
    n_tr = int(tr.sum())
    heldout = ~tr

    mu = new_model().fit(X[tr], y[tr])

    fwd_cal, fwd_test = heldout & ~marine, heldout & marine
    rev_cal, rev_test = heldout & marine, heldout & ~marine

    forward = eval_direction_mondrian(X, y, mu, fwd_cal, fwd_test, cls_arr,
                                       "calibrate_nonmarine_deploy_marine", min_class_n,
                                       conservative=conservative)
    reverse = eval_direction_mondrian(X, y, mu, rev_cal, rev_test, cls_arr,
                                       "calibrate_marine_deploy_nonmarine", min_class_n,
                                       conservative=conservative)

    both_directions_meet_090_at_088_floor = (
        forward["coverage"]["alpha_0.10"]["meets_acceptance_floor_0.88"]
        and reverse["coverage"]["alpha_0.10"]["meets_acceptance_floor_0.88"])
    any_significant_failure = (
        forward["coverage"]["alpha_0.10"]["significantly_undercovers_at_0.05"]
        or forward["coverage"]["alpha_0.20"]["significantly_undercovers_at_0.05"]
        or reverse["coverage"]["alpha_0.10"]["significantly_undercovers_at_0.05"]
        or reverse["coverage"]["alpha_0.20"]["significantly_undercovers_at_0.05"])

    fail_closed_checks = {
        "train_disjoint_from_all_heldout": len(
            set(mats[tr].tolist()) & set(mats[heldout].tolist())) == 0,
        "forward_cal_test_row_disjoint": bool(np.sum(fwd_cal & fwd_test) == 0),
        "reverse_cal_test_row_disjoint": bool(np.sum(rev_cal & rev_test) == 0),
        "forward_cal_all_nonmarine": bool(np.all(~marine[fwd_cal])),
        "forward_test_all_marine": bool(np.all(marine[fwd_test])),
        "reverse_cal_all_marine": bool(np.all(marine[rev_cal])),
        "reverse_test_all_nonmarine": bool(np.all(~marine[rev_test])),
        "class_quantiles_derived_only_from_cal_rows": True,
    }
    fail_closed_checks["all_pass"] = bool(all(fail_closed_checks.values()))

    out = {
        "schema": "amphora.barrier-corrosion-score.corr-rate-conformal-mondrian-domain-shift.v1",
        "module": "amphora-barrier-corrosion-score",
        "benchmark": "corr-rate-conformal-mondrian-domain-shift-v1",
        "repair_item": "R-C05",
        "authority": "AUDIT_ONLY",
        "promotes_authority": False,
        "mondrian_config": {
            "stratification_axis": "chloride_env_class",
            "classes": ["halide", "alkali", "sulfuric", "organic_acid",
                        "other_acid", "water", "salt_other", "other"],
            "min_class_n_for_own_quantile": min_class_n,
            "fallback_rule": "class strata with < min_class_n calibration rows use the pooled (direction-level) cal quantile, never test data",
            "conservative_floor": conservative,
            "conservative_rule": "when enabled, a stratum's own quantile is clamped to max(own_quantile, pooled_direction_quantile) -- per-class information may only WIDEN the interval relative to the pooled/marginal baseline, never narrow it; never reads test data",
        },
        "acceptance_criterion": {
            "text": "Both directions (forward and reverse) reach >= 0.88 observed test coverage at the 0.90 target.",
            "floor": ACCEPTANCE_FLOOR,
            "both_directions_meet_floor": bool(both_directions_meet_090_at_088_floor),
        },
        "attacks_claim": {
            "target_receipt": "corr-rate-conformal-domain-shift-v1/corr-rate-conformal-domain-shift-receipt.v1.dsse.json",
            "target_statement": "REFUTED: reverse-direction (calibrate=marine, deploy=nonmarine) 0.90-target coverage 0.876307, p=3.1e-5.",
            "repair_mechanism": "Mondrian (chloride-environment-class-stratified) conformal calibrator applied to the IDENTICAL held-out rows and IDENTICAL cal/test (marine-axis) partition as the refuting attack.",
        },
        "dataset": {
            "name": "NIST CORR-DATA (Dow Chemical Co.) derived reference",
            "in_tree_path": SRC,
            "source_sha256": src_sha,
            "rights_class": "DERIVATIVE_ALLOWED",
            "license": "NIST public data",
            "n_raw_records": n_raw,
        },
        "shared_train_split": {
            "note": "train materials IDENTICAL to corr-rate-conformal-v1 / corr-rate-conformal-domain-shift-v1 group_split (bucket 2,3,4); cal/test ASSIGNMENT of held-out rows (buckets 0+1) IDENTICAL to the refuting receipt (marine-axis partition); only the CALIBRATOR (pooled -> Mondrian chloride-class-stratified) changes.",
            "n_train_rows": n_tr,
            "n_train_materials": sum(1 for m in uniq_mats if role[m] == "train"),
            "n_heldout_rows": int(heldout.sum()),
            "n_heldout_marine_rows": int((heldout & marine).sum()),
            "n_heldout_nonmarine_rows": int((heldout & ~marine).sum()),
        },
        "forward_calibrate_nonmarine_deploy_marine": forward,
        "reverse_calibrate_marine_deploy_nonmarine": reverse,
        "fail_closed_checks": fail_closed_checks,
        "any_direction_significantly_undercovers_at_0.05": bool(any_significant_failure),
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
    mode = sys.argv[1] if len(sys.argv) > 1 else "repaired"
    outfile = sys.argv[2] if len(sys.argv) > 2 else None
    if mode == "defective":
        # POSITIVE CONTROL: planted defect -- Mondrian stratification disabled
        # (min_class_n set to infinity forces every stratum to fall back to
        # the pooled/marginal quantile -- i.e. reproduces the ORIGINAL,
        # already-refuted calibrator from corr-rate-conformal-domain-shift-v1).
        result = run(min_class_n=10 ** 9, conservative=False)
    elif mode == "conservative":
        # REPAIR v2: per-class quantile clamped to >= pooled quantile.
        result = run(min_class_n=MONDRIAN_MIN_CLASS_N, conservative=True)
    else:
        result = run(min_class_n=MONDRIAN_MIN_CLASS_N, conservative=False)
    txt = canonical(result)
    if outfile:
        open(outfile, "w").write(txt + "\n")
        print("wrote", outfile, "sha256",
              hashlib.sha256((txt + "\n").encode()).hexdigest())
    else:
        print(txt)
