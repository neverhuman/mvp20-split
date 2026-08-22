#!/usr/bin/env python3
"""
Independent V-A08 escalation re-implementation (written from scratch, NOT a copy
of run_fold_significance.py) of the NIST CORR-DATA LOSD-CV fold-significance
test, to check whether R-A08's "no statistically significant lift" conclusion
survives two escalations the repair's own self-check did not run:
  E1. Per-fold NESTED alpha selection over the full grid [0.01,0.1,1,10,100]
      (the KPI's own stated methodology names this grid; the repair's
      reimplementation fixed alpha=0.01 throughout). If tuning recovers a
      fold-robust effect, the repair's "not fold-robust" conclusion would be
      an artifact of an under-tuned model, not a real null result.
  E2. Fresh bootstrap seed (1234, independent of the repair's seed=0) with
      the same B=20000 replicates, to rule out seed-cherry-picking.
"""
import csv, re, math, statistics, collections, hashlib
import numpy as np
from scipy import stats
from sklearn.linear_model import Ridge
from sklearn.model_selection import KFold

CSV_PATH = "/tmp/corr_extract/CORR-DATA_Database.csv"
EXPECTED_CSV_SHA256 = "9b6b82d0a562cfd68c5c452a8e75f0ae4c8bc21a72d89a7bc07049242e4c5cc5"
TARGET_ENVS = ["Atmospheric Environments", "Seawater", "Sodium Chloride"]
TARGET_MGS = ["Aluminum and alloys", "Carbon and alloy steels", "Copper and alloys",
              "Nickel and alloys", "Stainless steels"]
ALPHA_GRID = [0.01, 0.1, 1.0, 10.0, 100.0]


def parse_rate(s):
    if not s: return None
    s = s.strip()
    m = re.match(r"^([\d.]+)\s*(max|min)?$", s)
    if m:
        try: return float(m.group(1))
        except ValueError: return None
    return None


def parse_num(s):
    if not s: return None
    s = s.strip()
    m = re.search(r"[-+]?\d*\.?\d+", s)
    if m:
        try: return float(m.group(0))
        except ValueError: return None
    return None


def parse_duration_hr(s):
    if not s: return None
    s = s.strip()
    m = re.search(r"([-+]?\d*\.?\d+)", s)
    if not m: return None
    val = float(m.group(1))
    sl = s.lower()
    if "yr" in sl or "year" in sl: return val * 8760.0
    if sl.endswith("d") or "day" in sl: return val * 24.0
    return val


def load():
    raw = open(CSV_PATH, "rb").read()
    assert hashlib.sha256(raw).hexdigest() == EXPECTED_CSV_SHA256
    rows = list(csv.DictReader(open(CSV_PATH, encoding="utf-8-sig")))
    sub = [r for r in rows if r["Environment"] in TARGET_ENVS and r["Material Group"] in TARGET_MGS]
    recs = []
    for r in sub:
        rate = parse_rate(r["Rate (mm/yr) or Rating"])
        if rate is None or rate <= 0:
            continue
        recs.append(dict(r, _rate=rate))
    temps = [parse_num(r["Temperature (deg C)"]) for r in recs]
    tmed = statistics.median([t for t in temps if t is not None])
    concs = [parse_num(r["Concentration (Vol %)"]) for r in recs]
    cmed = statistics.median([c for c in concs if c is not None])
    durs = [parse_duration_hr(r["Duration"]) for r in recs]
    dmed = statistics.median([d for d in durs if d is not None])
    for i, r in enumerate(recs):
        r["_t"] = temps[i] if temps[i] is not None else tmed
        r["_lc"] = math.log10(max(concs[i] if concs[i] is not None else cmed, 1e-6))
        r["_ld"] = math.log10(max(durs[i] if durs[i] is not None else dmed, 1e-6))
        r["_y"] = math.log10(r["_rate"])
        r["_doc"] = r["Reference #"].strip()
    return recs


def build_matrix(recs):
    X = np.zeros((len(recs), len(TARGET_ENVS) + len(TARGET_MGS) + 3))
    y = np.zeros(len(recs))
    for i, r in enumerate(recs):
        X[i, TARGET_ENVS.index(r["Environment"])] = 1.0
        X[i, len(TARGET_ENVS) + TARGET_MGS.index(r["Material Group"])] = 1.0
        X[i, -3] = r["_t"]; X[i, -2] = r["_lc"]; X[i, -1] = r["_ld"]
        y[i] = r["_y"]
    return X, y


def select_alpha_nested(Xtr, ytr, doc_tr, seed):
    """Pick alpha by 5-fold CV on the TRAINING fold only (never touches test fold)."""
    kf = KFold(n_splits=5, shuffle=True, random_state=seed)
    best_alpha, best_mae = ALPHA_GRID[0], float("inf")
    for a in ALPHA_GRID:
        errs = []
        for tr_idx, va_idx in kf.split(Xtr):
            m = Ridge(alpha=a)
            m.fit(Xtr[tr_idx], ytr[tr_idx])
            pred = m.predict(Xtr[va_idx])
            errs.append(np.mean(np.abs(pred - ytr[va_idx])))
        mae = float(np.mean(errs))
        if mae < best_mae:
            best_mae, best_alpha = mae, a
    return best_alpha


def losd_cv_nested_alpha(recs, X, y, seed):
    docs = sorted(set(r["_doc"] for r in recs))
    doc_of = np.array([r["_doc"] for r in recs])
    grp_med = collections.defaultdict(list)
    for r in recs:
        grp_med[r["Material Group"]].append(r["_y"])
    grp_med = {g: statistics.median(v) for g, v in grp_med.items()}
    global_med = statistics.median([r["_y"] for r in recs])

    fold_ridge, fold_null, fold_n, chosen_alphas = {}, {}, {}, {}
    for doc in docs:
        test = doc_of == doc
        train = ~test
        Xtr, ytr, Xte, yte = X[train], y[train], X[test], y[test]
        alpha = select_alpha_nested(Xtr, ytr, doc_of[train], seed)
        chosen_alphas[doc] = alpha
        m = Ridge(alpha=alpha)
        m.fit(Xtr, ytr)
        pred = m.predict(Xte)
        test_recs = [r for r, msk in zip(recs, test) if msk]
        null_pred = np.array([grp_med.get(r["Material Group"], global_med) for r in test_recs])
        fold_ridge[doc] = float(np.mean(np.abs(pred - yte)))
        fold_null[doc] = float(np.mean(np.abs(null_pred - yte)))
        fold_n[doc] = int(test.sum())
    return docs, fold_ridge, fold_null, fold_n, chosen_alphas


def cluster_bootstrap(diffs, n_boot, seed):
    rng = np.random.RandomState(seed)
    arr = np.array(diffs)
    n = len(arr)
    boots = np.array([arr[rng.randint(0, n, size=n)].mean() for _ in range(n_boot)])
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return float(lo), float(hi)


def main():
    recs = load()
    X, y = build_matrix(recs)

    # E1: nested per-fold alpha selection (escalation beyond fixed alpha=0.01)
    docs, fold_ridge, fold_null, fold_n, chosen_alphas = losd_cv_nested_alpha(recs, X, y, seed=7)
    diffs = np.array([fold_null[d] - fold_ridge[d] for d in docs])
    n_better = int(np.sum(diffs > 0))
    n_worse = int(np.sum(diffs < 0))
    sign_p = stats.binomtest(n_better, n_better + n_worse, p=0.5).pvalue
    wil = stats.wilcoxon(diffs[diffs != 0])
    lo1, hi1 = cluster_bootstrap(diffs, 20000, seed=1234)  # E2: fresh seed
    lo2, hi2 = cluster_bootstrap(diffs, 20000, seed=99999)  # second independent fresh seed

    pooled_ridge = sum(fold_ridge[d] * fold_n[d] for d in docs) / sum(fold_n.values())
    pooled_null = sum(fold_null[d] * fold_n[d] for d in docs) / sum(fold_n.values())

    print("N_DOCS:", len(docs))
    print("ALPHA_SELECTION_COUNTS:", collections.Counter(chosen_alphas.values()))
    print("POOLED_RIDGE_MAE_NESTED_ALPHA:", pooled_ridge)
    print("POOLED_NULL_MAE:", pooled_null)
    print("N_FOLDS_RIDGE_BETTER:", n_better, "/", len(docs))
    print("SIGN_TEST_P:", sign_p)
    print("WILCOXON_P:", wil.pvalue)
    print("BOOTSTRAP_CI_SEED1234_B20000:", (lo1, hi1), "crosses_zero:", lo1 <= 0 <= hi1)
    print("BOOTSTRAP_CI_SEED99999_B20000:", (lo2, hi2), "crosses_zero:", lo2 <= 0 <= hi2)
    refutes = (n_better / len(docs) < 0.60) or (lo1 <= 0 <= hi1) or (wil.pvalue > 0.05)
    print("ESCALATED_VERDICT_STILL_REFUTED_NO_SIGNIFICANT_LIFT:", refutes)


if __name__ == "__main__":
    main()
