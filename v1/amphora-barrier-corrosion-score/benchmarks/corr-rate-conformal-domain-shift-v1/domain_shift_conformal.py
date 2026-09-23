#!/usr/bin/env python3
"""corr-rate-conformal-domain-shift-v1 -- FALSIFICATION ATTACK on the
corr-rate-conformal-v1 (AUDIT_ONLY, phase0-evaluator-signed) coverage claim for
amphora-barrier-corrosion-score.

STANDING CLAIM UNDER ATTACK (corr-rate-conformal-v1 receipt, 2026-07-29):
  "Group-safe (leave-material-out) split conformal delivers distribution-free
  marginal coverage at the 0.90 and 0.80 targets on the rights-clean NIST
  CORR-DATA corrosion-rate model; the coverage guarantee holds even when the
  base learner is destroyed by label shuffling."

The prior receipt tested exactly ONE partition of the held-out (non-train)
materials into calibration/test: a deterministic material-bucket-parity split
(bucket 0 = test, bucket 1 = cal). Cal and test are therefore both
approximately-representative random subsamples of the SAME held-out-material
environment mixture -- i.e. approximately exchangeable by construction, which
is why the Mondrian marine/chloride stratification in that receipt (cal_marine
vs test_marine drawn from the SAME distribution) only showed a mild dip to
0.875.

Split conformal's *only* formal guarantee is exchangeability of calibration
and test residuals (Vovk-Gammerman-Shafer 2005; Lei et al 2018 JASA
113(523):1094). It is well established that the marginal coverage guarantee
breaks under COVARIATE SHIFT between calibration and test (Tibshirani, Barber,
Candes, Ramdas 2019, NeurIPS "Conformal Prediction Under Covariate Shift" --
requires likelihood-ratio reweighting to restore coverage).

THIS ATTACK constructs a *different*, equally legitimate, still
group(material)-safe partition of the SAME held-out rows used by
corr-rate-conformal-v1: instead of splitting cal/test by material-bucket
parity, we split by ENVIRONMENT DOMAIN (marine/chloride vs not), which is
exactly the axis the module's own scope statement treats as decision-relevant
("marine/chloride environments are the in-scope coating context" --
corr-rate-conformal-v1 mondrian rationale). This is the realistic deployment
risk for this module: a practitioner calibrates intervals on whatever
corrosion data is on hand (often general/lab, not marine-dominated) and then
deploys the interval specifically to assess MARINE anti-corrosion risk (the
actual coating IP use case) -- or the reverse. We test both directions.

Train split (materials) is IDENTICAL to corr-rate-conformal-v1 (same
group_split bucket assignment, same 366 train materials) so the base model is
byte-comparable. Only the cal/test ASSIGNMENT of the held-out rows changes:
  FORWARD:  cal = held-out & NOT marine/chloride,  test = held-out & marine/chloride
  REVERSE:  cal = held-out & marine/chloride,       test = held-out & NOT marine/chloride

If observed coverage falls significantly (one-sided binomial test, alpha=0.05)
below the receipt's stated 0.90 or 0.80 targets in either direction, the
"distribution-free marginal coverage" claim, as a robustness property (not
merely a single-split artifact), is REFUTED: the guarantee depends on a
favorable cal/test partition and does not survive a realistic domain-shifted
recalibration scenario.

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

# ---- features: IDENTICAL scheme to corr-rate-qspr-v1 / corr-rate-conformal-v1
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
    X, y, mats, chl = [], [], [], []
    for mat, env, temp, ly in rows:
        cv, _ = comp_vector(mat)
        ev, is_marine = env_features(env)
        tnum = float(temp) if temp is not None else float("nan")
        tmiss = 0.0 if temp is not None else 1.0
        X.append(cv + ev + [tnum, tmiss])
        y.append(ly)
        mats.append(mat)
        chl.append(is_marine)
    return (np.array(X, float), np.array(y, float), np.array(mats),
            np.array(chl, bool))


def new_model():
    return HistGradientBoostingRegressor(
        random_state=SEED, max_iter=300, learning_rate=0.05,
        max_depth=None, max_leaf_nodes=31, l2_regularization=1.0,
        early_stopping=False)


def group_split(mats):
    """IDENTICAL to corr-rate-conformal-v1: deterministic leave-material-out
    partition into train/cal0/test0 by sorted-material index bucket
    (bucket = idx % 5): test0={0}, cal0={1}, train={2,3,4}. Only `train` is
    reused here -- cal/test are reassigned by environment domain below."""
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
    k = math.ceil((n + 1) * (1.0 - alpha))
    if k > n:
        return float("inf")
    return float(s[k - 1])


def coverage(yt, yp, half):
    return float(np.mean(np.abs(yt - yp) <= half + 1e-12))


def binom_test_less(n_success, n_trials, p0):
    """One-sided exact binomial test: P(X <= n_success | Binomial(n_trials, p0)).
    stdlib-only (no scipy dependency) via log-space summation for determinism
    and reproducibility across environments."""
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


def main():
    rows, src_sha, n_raw = load()
    X, y, mats, marine = build_matrix(rows)
    n = len(y)
    tr, ca0, te0, uniq_mats, role = group_split(mats)
    n_tr = int(tr.sum())

    heldout = ~tr  # buckets 0+1 from corr-rate-conformal-v1: the SAME rows
                   # that receipt used for its cal (bucket1) + test (bucket0)

    # base mu-model on train -- IDENTICAL fit to corr-rate-conformal-v1
    mu = new_model().fit(X[tr], y[tr])

    def eval_direction(cal_mask, test_mask, name):
        p_ca = mu.predict(X[cal_mask])
        p_te = mu.predict(X[test_mask])
        r2_te, rmse_te = r2_rmse(y[test_mask], p_te)
        s_ca = np.abs(y[cal_mask] - p_ca)
        n_ca, n_te = int(cal_mask.sum()), int(test_mask.sum())
        per_alpha = {}
        for a, target_label in ((0.10, "0.90"), (0.20, "0.80")):
            q = conf_quantile(s_ca, a)
            cov = coverage(y[test_mask], p_te, q)
            n_covered = int(round(cov * n_te))
            p_less = binom_test_less(n_covered, n_te, 1.0 - a)
            per_alpha["alpha_%.2f" % a] = {
                "target_coverage": round(1 - a, NDEC),
                "conformal_quantile_log10": None if math.isinf(q) else round(q, NDEC),
                "observed_test_coverage": round(cov, NDEC),
                "mean_interval_width_log10": None if math.isinf(q) else round(2 * q, NDEC),
                "meets_target": bool(cov >= (1 - a) - 1e-9) or math.isinf(q),
                "n_covered": n_covered, "n_test": n_te,
                "binomial_pvalue_coverage_less_than_target": round(p_less, 6),
                "significantly_undercovers_at_0.05": bool(p_less < 0.05),
            }
        return {
            "direction": name,
            "n_cal": n_ca, "n_test": n_te,
            "base_model_test_r2": round(r2_te, NDEC),
            "base_model_test_rmse_log10": round(rmse_te, NDEC),
            "coverage": per_alpha,
        }

    fwd_cal, fwd_test = heldout & ~marine, heldout & marine
    rev_cal, rev_test = heldout & marine, heldout & ~marine

    forward = eval_direction(fwd_cal, fwd_test, "calibrate_nonmarine_deploy_marine")
    reverse = eval_direction(rev_cal, rev_test, "calibrate_marine_deploy_nonmarine")

    any_significant_failure = (
        forward["coverage"]["alpha_0.10"]["significantly_undercovers_at_0.05"]
        or forward["coverage"]["alpha_0.20"]["significantly_undercovers_at_0.05"]
        or reverse["coverage"]["alpha_0.10"]["significantly_undercovers_at_0.05"]
        or reverse["coverage"]["alpha_0.20"]["significantly_undercovers_at_0.05"])

    out = {
        "schema": "amphora.barrier-corrosion-score.corr-rate-conformal-domain-shift.v1",
        "module": "amphora-barrier-corrosion-score",
        "benchmark": "corr-rate-conformal-domain-shift-v1",
        "authority": "AUDIT_ONLY",
        "promotes_authority": False,
        "attacks_claim": {
            "target_receipt": "corr-rate-conformal-v1/corr-rate-conformal-receipt.v1.dsse.json",
            "target_statement": "Group-safe (leave-material-out) split conformal "
                "delivers distribution-free marginal coverage at the 0.90 and 0.80 "
                "targets on the rights-clean NIST CORR-DATA corrosion-rate model.",
            "attack_type": "distribution-shift (covariate shift between "
                "calibration and test sets, induced by environment-domain "
                "partition instead of the receipt's material-bucket-parity "
                "partition of the SAME held-out rows)",
            "refutation_criterion": "Observed test coverage significantly below "
                "(one-sided exact binomial test, alpha=0.05) the receipt's stated "
                "0.90 or 0.80 target in either calibration/deployment direction.",
            "theoretical_basis": "Tibshirani, Barber, Candes, Ramdas 2019 NeurIPS "
                "'Conformal Prediction Under Covariate Shift': split-conformal "
                "marginal coverage requires cal/test exchangeability and is NOT "
                "robust to covariate shift without likelihood-ratio reweighting.",
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
            "note": "train materials IDENTICAL to corr-rate-conformal-v1 "
                "group_split (bucket 2,3,4); only cal/test ASSIGNMENT of the "
                "held-out rows (buckets 0+1) is changed, from material-bucket "
                "parity to environment domain (marine/chloride vs not).",
            "n_train_rows": n_tr,
            "n_train_materials": sum(1 for m in uniq_mats if role[m] == "train"),
            "n_heldout_rows": int(heldout.sum()),
            "n_heldout_marine_rows": int((heldout & marine).sum()),
            "n_heldout_nonmarine_rows": int((heldout & ~marine).sum()),
        },
        "forward_calibrate_nonmarine_deploy_marine": forward,
        "reverse_calibrate_marine_deploy_nonmarine": reverse,
        "fail_closed_checks": {
            "train_disjoint_from_all_heldout": len(
                set(mats[tr].tolist()) & set(mats[heldout].tolist())) == 0,
            "forward_cal_test_row_disjoint": bool(np.sum(fwd_cal & fwd_test) == 0),
            "reverse_cal_test_row_disjoint": bool(np.sum(rev_cal & rev_test) == 0),
            "forward_cal_all_nonmarine": bool(np.all(~marine[fwd_cal])),
            "forward_test_all_marine": bool(np.all(marine[fwd_test])),
            "reverse_cal_all_marine": bool(np.all(marine[rev_cal])),
            "reverse_test_all_nonmarine": bool(np.all(~marine[rev_test])),
        },
        "any_direction_significantly_undercovers_at_0.05": bool(any_significant_failure),
    }
    out["fail_closed_checks"]["all_pass"] = bool(
        all(v for k, v in out["fail_closed_checks"].items() if k != "all_pass"))

    if any_significant_failure:
        out["verdict"] = {
            "outcome": "CLAIM_REFUTED",
            "finding": "The corr-rate-conformal-v1 'distribution-free marginal "
                "coverage' claim does NOT survive a realistic environment-domain "
                "cal/test partition of the SAME held-out rows: at least one "
                "direction (calibrate-on-one-environment-regime, "
                "deploy-on-the-other) shows observed coverage significantly "
                "below the receipt's stated target (one-sided binomial p<0.05). "
                "The prior receipt's Mondrian marine stratification used cal "
                "and test marine subsets drawn from the SAME material-bucket "
                "partition (approximately exchangeable by construction) and so "
                "never exercised this failure mode.",
        }
    else:
        out["verdict"] = {
            "outcome": "CLAIM_SURVIVED",
            "finding": "Even under an environment-domain cal/test partition "
                "(a genuine covariate-shift stress test, not merely a "
                "material-bucket resample), observed coverage did not fall "
                "significantly below the receipt's stated targets in either "
                "direction.",
        }
    out["scope_honesty"] = (
        "Bare-metal/alloy substrate corrosion (same ceiling as "
        "corr-rate-qspr-v1 / corr-rate-conformal-v1). AUDIT_ONLY: does not "
        "flip scientific_readiness, does not modify the manifest (66/11 "
        "untouched), grants no coating-barrier ranking authority.")
    out["determinism"] = {
        "omp_num_threads": "1", "seed": SEED, "no_timestamp": True,
        "float_round_decimals": NDEC, "sklearn_histgbm_early_stopping": False,
        "binomial_test": "exact log-space stdlib implementation (no scipy dependency)",
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
    txt = canonical(main())
    if len(sys.argv) > 1:
        open(sys.argv[1], "w").write(txt + "\n")
        print("wrote", sys.argv[1], "sha256",
              hashlib.sha256((txt + "\n").encode()).hexdigest())
    else:
        print(txt)
