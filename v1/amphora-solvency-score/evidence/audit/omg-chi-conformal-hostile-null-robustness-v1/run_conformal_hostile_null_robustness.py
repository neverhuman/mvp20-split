#!/usr/bin/env python3
"""W-OMG-CONF (rotation, amphora-solvency-score): independent re-derivation +
multi-seed robustness attack on the never-before-attacked OMG chi 3-solvent
split-conformal + applicability-domain claim
(reference/mvp20/data/omg_chi_conformal_and_applicability_domain_receipt.v1.json,
evidence/phase0/kpis/omg-chi-3-solvent-conformal-coverage-and-applicability-domain-kpi.v1.json).

The signed receipt's OWN per-solvent diagnostic reports the hostile-null
y-shuffle coverage for water (0.897210) and ethanol (0.897573) BELOW the
naive 0.90 target -- passed only via a tight "within 1-sigma of asymptotic
target" gate whose own floor is 0.897140 for water, i.e. a margin of just
0.00007 (0.007 percentage points). That is the same "razor-thin boundary
pass" pattern that W-SCAFFOLD (2026-08-15) found and REFUTED for the
BigSolDB headline one fire ago. This script tests whether that razor-thin
water/ethanol hostile-null pass is a robust feature of the calibration
machinery or an artifact of the single fixed seed=0 used in the signed
receipt, by rebuilding an INDEPENDENT (smaller-scale, not byte-identical)
split-conformal + hostile-null harness from the same real OMG corpus, same
scaffold-safe split methodology, and same GBM/feature spec already used
elsewhere in this module (benchmarks/ml-vs-physics-coverage-scope-v1), then
replaying the hostile-null shuffle test across MANY independent seeds
instead of one.

PRE-REGISTERED REFUTATION CRITERION (fixed before any null-seed result is
inspected): across N_NULL_SEEDS independent y-shuffle replicates (retrained
model on shuffled y, exact Papadopoulos et al 2002 split-conformal quantile
formula), if the fraction of seeds whose empirical hostile-null coverage at
alpha=0.10 falls BELOW the conservative worst-case floor (1-2*alpha = 0.80)
exceeds FAIL_FRACTION (0.20, i.e. more than 1 in 5 seeds), the coverage
guarantee's practical reliability is REFUTED for this scope (independent
re-derivation, n_sample=N_SAMPLE, single solvent). If the observed
fail-fraction is 0 and the real-signal (non-shuffled) coverage independently
clears its target with a comfortable margin, the claim SURVIVES this
specific attack in this scope.

POSITIVE CONTROL: after evaluating the real-signal split-conformal interval,
the harness re-scores coverage on a copy of the test set whose predictions
are deliberately shifted by +2*q_hat (simulating exactly the kind of
calibration/deployment exchangeability break -- e.g. novel-scaffold drift --
that a scaffold-disjoint cal/test split is theoretically susceptible to).
This MUST collapse measured coverage far below the floor; if it does not,
the harness itself cannot be trusted to detect a real coverage failure and
no survival verdict may be drawn from it.
"""
import gzip
import hashlib
import json
import math
import random
import sys
import time

import numpy as np
from rdkit import Chem, RDLogger
from rdkit.Chem import AllChem, Descriptors, rdMolDescriptors
from rdkit.Chem.Scaffolds import MurckoScaffold
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import r2_score

RDLogger.DisableLog("rdApp.*")

ROOT = "/home/ubuntu/amphora/build/mvp20-split"
CORPUS = ROOT + "/feedback/v3/normalized/omg_physical_properties_v3.jsonl.gz"
MANIFEST = ROOT + "/amphora-solvency-score/reference/mvp20/data/feedback_v3/manifests/omg_physical_properties_v3.json"
SPLIT_SEED = 0
N_SAMPLE = 20000
SOLVENTS = ["water", "ethanol"]
CHI_FIELDS = {
    "chloroform": "chi_parameter_chloroform_mean",
    "ethanol": "chi_parameter_ethanol_mean",
    "water": "chi_parameter_water_mean",
}
N_NULL_SEEDS = 10
FAIL_FRACTION_THRESHOLD = 0.20
ALPHAS = [0.10, 0.20]

GBM_KW = dict(
    max_iter=500, learning_rate=0.05, max_depth=8,
    min_samples_leaf=25, l2_regularization=0.1, random_state=0,
)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_json(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def load_sample():
    man = json.load(open(MANIFEST))
    assert man["rights_class"] == "DERIVATIVE_ALLOWED", "rights lock not clean"
    assert man["quarantined"] is False, "corpus quarantined"
    corpus_sha = sha256_file(CORPUS)
    assert corpus_sha == man["normalized_sha256"], "corpus bytes do not match manifest lock"
    smi_to_chi = {}
    n_records = 0
    n_chi_records = 0
    with gzip.open(CORPUS, "rt") as f:
        for line in f:
            n_records += 1
            rec = json.loads(line)
            rf = rec.get("raw_fields") or {}
            smi = rf.get("methyl_terminated_product")
            if not smi:
                continue
            if not all(rf.get(v) not in (None, "") for v in CHI_FIELDS.values()):
                continue
            n_chi_records += 1
            if smi not in smi_to_chi:
                smi_to_chi[smi] = {k: float(rf[v]) for k, v in CHI_FIELDS.items()}
    pool = sorted(smi_to_chi.keys())
    rng = random.Random(SPLIT_SEED)
    sample = rng.sample(pool, min(N_SAMPLE, len(pool)))
    prov = {
        "corpus_path": CORPUS, "corpus_sha256": corpus_sha,
        "manifest_rights_class": man["rights_class"], "manifest_quarantined": man["quarantined"],
        "dataset_id": man["dataset_id"], "n_records_streamed": n_records,
        "n_chi_records": n_chi_records, "n_unique_smiles_chi_labeled": len(pool),
        "split_seed": SPLIT_SEED, "n_sample": len(sample),
    }
    return prov, sample, smi_to_chi


def murcko_scaffold(smi, cache={}):
    if smi in cache:
        return cache[smi]
    mol = Chem.MolFromSmiles(smi)
    if mol is None:
        cache[smi] = None
        return None
    try:
        scaf = MurckoScaffold.GetScaffoldForMol(mol)
        r = Chem.MolToSmiles(scaf) if scaf is not None else ""
    except Exception:
        r = ""
    cache[smi] = r
    return r


def scaffold_safe_split(smiles_list, seed=0, fracs=(0.6, 0.2, 0.2)):
    groups = {}
    for smi in smiles_list:
        scaf = murcko_scaffold(smi) or "__NONE__:" + smi
        groups.setdefault(scaf, []).append(smi)
    scaf_keys = sorted(groups.keys())
    rng = random.Random(seed)
    rng.shuffle(scaf_keys)
    n_total = len(smiles_list)
    n_train_target = int(round(fracs[0] * n_total))
    n_val_target = int(round(fracs[1] * n_total))
    train, val, test = [], [], []
    for k in scaf_keys:
        members = groups[k]
        if len(train) < n_train_target:
            train.extend(members)
        elif len(val) < n_val_target:
            val.extend(members)
        else:
            test.extend(members)
    return train, val, test, len(groups)


def compute_descriptors(mol):
    fcsp3 = rdMolDescriptors.CalcFractionCSP3(mol)
    ri = mol.GetRingInfo()
    n_arom_rings = rdMolDescriptors.CalcNumAromaticRings(mol)
    n_aliphatic_rings = rdMolDescriptors.CalcNumAliphaticRings(mol)
    n_arom_hetero = rdMolDescriptors.CalcNumAromaticHeterocycles(mol)
    halogens = {9, 17, 35, 53}
    n_n = sum(1 for a in mol.GetAtoms() if a.GetAtomicNum() == 7)
    n_o = sum(1 for a in mol.GetAtoms() if a.GetAtomicNum() == 8)
    n_s = sum(1 for a in mol.GetAtoms() if a.GetAtomicNum() == 16)
    n_hal = sum(1 for a in mol.GetAtoms() if a.GetAtomicNum() in halogens)
    return [
        Descriptors.MolWt(mol), Descriptors.MolLogP(mol), Descriptors.TPSA(mol),
        rdMolDescriptors.CalcNumHBA(mol), rdMolDescriptors.CalcNumHBD(mol),
        rdMolDescriptors.CalcNumRotatableBonds(mol), n_arom_rings, mol.GetNumHeavyAtoms(),
        n_n, n_o, n_s, n_hal, fcsp3, ri.NumRings(), n_arom_hetero, n_aliphatic_rings,
    ]


_FEAT_CACHE = {}
_FP_CACHE = {}


def featurize(smi):
    if smi in _FEAT_CACHE:
        return _FEAT_CACHE[smi]
    mol = Chem.MolFromSmiles(smi)
    if mol is None:
        _FEAT_CACHE[smi] = None
        return None
    desc = compute_descriptors(mol)
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius=2, nBits=512)
    _FP_CACHE[smi] = fp
    bits = [int(b) for b in fp.ToBitString()]
    vec = desc + bits
    _FEAT_CACHE[smi] = vec
    return vec


def conformal_qhat(residuals, alpha):
    n = len(residuals)
    idx = math.ceil((1 - alpha) * (n + 1))
    srt = np.sort(residuals)
    if idx > n:
        return math.inf
    return float(srt[idx - 1])


def coverage_and_width(y_true, y_pred, qhat):
    lo = y_pred - qhat
    hi = y_pred + qhat
    inside = (y_true >= lo) & (y_true <= hi)
    return float(np.mean(inside)), float(np.median(hi - lo))


def fit_predict(Xtr, ytr, Xcal, Xtest):
    m = HistGradientBoostingRegressor(**GBM_KW)
    m.fit(Xtr, ytr)
    return m.predict(Xcal), m.predict(Xtest)


def bulk_tanimoto_ad(test_smiles, train_smiles):
    from rdkit import DataStructs
    train_fps = [_FP_CACHE[s] for s in train_smiles]
    ad = []
    for s in test_smiles:
        fp = _FP_CACHE[s]
        sims = DataStructs.BulkTanimotoSimilarity(fp, train_fps)
        ad.append(max(sims) if sims else 0.0)
    return np.array(ad)


def quintile_coverage(ad_scores, y_true, y_pred, qhat):
    order = np.argsort(ad_scores)
    n = len(order)
    edges = [int(round(n * i / 5)) for i in range(6)]
    out = []
    for q in range(5):
        idxs = order[edges[q]:edges[q + 1]]
        if len(idxs) == 0:
            continue
        cov, w = coverage_and_width(y_true[idxs], y_pred[idxs], qhat)
        out.append({"quintile": q, "n": int(len(idxs)),
                     "ad_min": float(ad_scores[idxs].min()), "ad_max": float(ad_scores[idxs].max()),
                     "coverage": cov})
    return out


def main(out_path):
    t0 = time.time()
    prov, sample, smi_to_chi = load_sample()
    train_s, cal_s, test_s, n_scaf = scaffold_safe_split(sample, seed=SPLIT_SEED)
    print(f"[{time.time()-t0:.1f}s] loaded sample n={len(sample)} scaffolds={n_scaf} "
          f"train={len(train_s)} cal={len(cal_s)} test={len(test_s)}", file=sys.stderr)

    # featurize once, shared across solvents/seeds
    for smi in sample:
        featurize(smi)
    print(f"[{time.time()-t0:.1f}s] featurized {len(sample)} molecules", file=sys.stderr)

    results = {}
    for solvent in SOLVENTS:
        Xtr = np.array([_FEAT_CACHE[s] for s in train_s], dtype=float)
        Xcal = np.array([_FEAT_CACHE[s] for s in cal_s], dtype=float)
        Xtest = np.array([_FEAT_CACHE[s] for s in test_s], dtype=float)
        ytr = np.array([smi_to_chi[s][solvent] for s in train_s], dtype=float)
        ycal = np.array([smi_to_chi[s][solvent] for s in cal_s], dtype=float)
        ytest = np.array([smi_to_chi[s][solvent] for s in test_s], dtype=float)

        # REAL SIGNAL
        pred_cal, pred_test = fit_predict(Xtr, ytr, Xcal, Xtest)
        real_r2 = float(r2_score(ytest, pred_test))
        real = {}
        qhats = {}
        for alpha in ALPHAS:
            resid = np.abs(ycal - pred_cal)
            qhat = conformal_qhat(resid, alpha)
            qhats[alpha] = qhat
            cov, width = coverage_and_width(ytest, pred_test, qhat)
            floor = 1 - alpha
            real[str(alpha)] = {"coverage": cov, "median_width": width, "qhat": qhat,
                                 "target_floor": floor, "meets_target": cov >= floor}
        print(f"[{time.time()-t0:.1f}s] {solvent} REAL fit done: r2={real_r2:.4f} "
              f"cov10={real['0.1']['coverage']:.4f} cov20={real['0.2']['coverage']:.4f}", file=sys.stderr)

        ad_scores = bulk_tanimoto_ad(test_s, train_s)
        quint = {}
        for alpha in ALPHAS:
            quint[str(alpha)] = quintile_coverage(ad_scores, ytest, pred_test, qhats[alpha])
        worst_quintile_010 = min(q["coverage"] for q in quint["0.1"])
        worst_quintile_020 = min(q["coverage"] for q in quint["0.2"])

        # POSITIVE CONTROL: shift test predictions by +2*qhat (alpha=0.10), reusing
        # the REAL qhat computed from unshifted calibration -- simulates a
        # calibration/deployment exchangeability break.
        alpha_pc = 0.10
        shifted_pred_test = pred_test + 2.0 * qhats[alpha_pc]
        pc_cov, pc_width = coverage_and_width(ytest, shifted_pred_test, qhats[alpha_pc])
        positive_control = {
            "planted_defect": f"test predictions shifted by +2*qhat(alpha={alpha_pc}) post-calibration "
                               f"(simulates calibration/deployment exchangeability break)",
            "how_planted": f"shifted_pred_test = pred_test + 2*{qhats[alpha_pc]:.6f}; qhat reused from "
                            f"the REAL (unshifted) calibration residuals, then coverage recomputed on the shift",
            "pre_shift_coverage": real["0.1"]["coverage"],
            "post_shift_coverage": pc_cov,
            "target_floor": 0.90,
            "detected": pc_cov < 0.90 - 0.15,  # must collapse well below floor, not just dip
            "evidence": f"coverage collapsed from {real['0.1']['coverage']:.4f} to {pc_cov:.4f} "
                        f"under the planted post-calibration shift",
        }
        print(f"[{time.time()-t0:.1f}s] {solvent} positive control: "
              f"{real['0.1']['coverage']:.4f} -> {pc_cov:.4f} (detected={positive_control['detected']})",
              file=sys.stderr)

        # HOSTILE-NULL MULTI-SEED SWEEP: shuffle y across the combined sample,
        # retrain on shuffled y_train, recalibrate, evaluate coverage on
        # shuffled y_test. alpha=0.10 only (matches the signed receipt's own
        # hostile-null protocol).
        all_smi = train_s + cal_s + test_s
        n_tr, n_cal = len(train_s), len(cal_s)
        null_runs = []
        for seed in range(N_NULL_SEEDS):
            rng = np.random.default_rng(seed)
            y_all = np.array([smi_to_chi[s][solvent] for s in all_smi], dtype=float)
            y_shuf = rng.permutation(y_all)
            ytr_s = y_shuf[:n_tr]
            ycal_s = y_shuf[n_tr:n_tr + n_cal]
            ytest_s = y_shuf[n_tr + n_cal:]
            pcal_s, ptest_s = fit_predict(Xtr, ytr_s, Xcal, Xtest)
            resid_s = np.abs(ycal_s - pcal_s)
            qhat_s = conformal_qhat(resid_s, 0.10)
            cov_s, width_s = coverage_and_width(ytest_s, ptest_s, qhat_s)
            null_runs.append({"seed": seed, "coverage": cov_s, "median_width": width_s,
                               "below_worst_case_floor_0.80": cov_s < 0.80,
                               "below_naive_0.90": cov_s < 0.90})
            print(f"[{time.time()-t0:.1f}s] {solvent} null seed={seed} cov={cov_s:.4f} "
                  f"width={width_s:.4f}", file=sys.stderr)

        n_fail = sum(1 for r in null_runs if r["below_worst_case_floor_0.80"])
        fail_fraction = n_fail / N_NULL_SEEDS
        n_below_090 = sum(1 for r in null_runs if r["below_naive_0.90"])
        real_width_010 = real["0.1"]["median_width"]
        null_widths = [r["median_width"] for r in null_runs]
        width_inflation_ratios = [w / real_width_010 for w in null_widths]

        results[solvent] = {
            "n_train": len(train_s), "n_cal": len(cal_s), "n_test": len(test_s),
            "real_signal": real, "real_test_r2": real_r2,
            "ad_quintile_coverage": quint,
            "worst_ad_quintile_coverage_alpha010": worst_quintile_010,
            "worst_ad_quintile_coverage_alpha020": worst_quintile_020,
            "positive_control": positive_control,
            "hostile_null_multiseed": {
                "n_seeds": N_NULL_SEEDS,
                "runs": null_runs,
                "n_seeds_below_worst_case_floor_0.80": n_fail,
                "fail_fraction": fail_fraction,
                "n_seeds_below_naive_0.90": n_below_090,
                "mean_null_width_inflation_ratio_over_real_signal": float(np.mean(width_inflation_ratios)),
                "refutation_criterion": f"fail_fraction > {FAIL_FRACTION_THRESHOLD} at worst-case floor 0.80, alpha=0.10",
                "refutation_criterion_met": fail_fraction > FAIL_FRACTION_THRESHOLD,
            },
        }

    verdict = "CLAIM_SURVIVED"
    for solvent, r in results.items():
        if r["hostile_null_multiseed"]["refutation_criterion_met"]:
            verdict = "CLAIM_REFUTED"
        if not r["positive_control"]["detected"]:
            verdict = "HARNESS_INVALID"
        if r["real_signal"]["0.1"]["coverage"] < 0.80 or r["real_signal"]["0.2"]["coverage"] < 0.60:
            verdict = "CLAIM_REFUTED"

    out = {
        "schema": "amphora.solvency-score-omg-chi-conformal-hostile-null-robustness-audit.v1",
        "campaign_item_id": "W-OMG-CONF",
        "claim_under_attack": "reference/mvp20/data/omg_chi_conformal_and_applicability_domain_receipt.v1.json + "
                               "evidence/phase0/kpis/omg-chi-3-solvent-conformal-coverage-and-applicability-domain-kpi.v1.json "
                               "(split-conformal marginal coverage >=90%/80% at alpha=0.10/0.20, hostile-null y-shuffle "
                               "passes, per-AD-quintile floor holds -- scaffold-safe on water/ethanol/chloroform)",
        "provenance": prov,
        "scope_note": "Independent re-derivation at reduced scale (n_sample=20000 vs signed receipt's 98506) using the "
                       "SAME real OMG PhysicalProperties v3 corpus, SAME scaffold-safe 60/20/20-by-scaffold split "
                       "methodology, SAME 528-feature (16 rdkit descriptors + 512-bit Morgan r=2) spec, and SAME "
                       "HistGradientBoostingRegressor hyperparameters already used by this module's own "
                       "ml-vs-physics-coverage-scope-v1 benchmark. NOT a byte-identical replay of the signed receipt "
                       "(different n_sample, split_seed used only for sampling+split not identical to original's "
                       "internal RNG stream) -- scored as an independent re-derivation attack, restricted to "
                       "water and ethanol (the two solvents whose signed hostile-null diagnostic already sits below "
                       "0.90 naive target in the original receipt).",
        "results": results,
        "gbm_hyperparameters": GBM_KW,
        "n_null_seeds": N_NULL_SEEDS,
        "fail_fraction_threshold": FAIL_FRACTION_THRESHOLD,
        "verdict": verdict,
        "elapsed_sec": time.time() - t0,
    }
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2, sort_keys=True)
    print(f"[{time.time()-t0:.1f}s] DONE verdict={verdict} -> {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "diagnostic.canonical.json")
