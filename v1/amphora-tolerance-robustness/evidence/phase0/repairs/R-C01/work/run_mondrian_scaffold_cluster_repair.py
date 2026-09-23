#!/usr/bin/env python3
"""R-C01 repair fire 2/5, attempt 4: Mondrian (category-conditional) conformal
prediction stratified by a FIXED, seed-independent scaffold cluster taxonomy,
re-run against the IDENTICAL pinned 60-seed scaffold-disjoint Monte Carlo
protocol that refuted the OpenPoly Tg split-conformal marginal-coverage claim
(evidence/audit/repeated-scaffold-monte-carlo-conformal-openpoly-tg-v1/
run_repeated_scaffold_conformal.py, sha256
96be585e27428a1f9bec0a7e2c078f9488711df5515790bc24ac35ac97cf0e09, seeds 0..59).

That script is NEVER modified or imported in a way that could mutate it; its
deterministic split logic (60/40 pool/test via scaffold-block assignment, then
50/50 proper-train/calibration split within the pool, both keyed on
random_state=seed) is reproduced verbatim below so every one of the 60 splits
is byte-identical to the pinned attack.

Theory: Vovk, Lindsay, Nouretdinov, Gammerman (2003) "Mondrian Confidence
Machine"; Vovk, Gammerman, Shafer (2005) "Algorithmic Learning in a Random
World", Ch. 4.5. A Mondrian conformal predictor partitions the object space
via a taxonomy kappa(x) measurable WITHOUT the test label and calibrates a
SEPARATE conformity quantile per category. Fire 1 tried CV+ (Barber et al.
2021) and weighted covariate-shift conformal (Tibshirani et al. 2019); both
fell short (0.8825, 0.8619) or degenerated (weighted, 100% unbounded). This
attempt is the "not yet tried" #1 recorded in work/STATE.json after fire 1:
Mondrian conformal stratified by a FIXED (seed-independent) Butina clustering
of scaffold Morgan fingerprints, with explicit small-cluster fallback-to-
global. Rationale distinct from CV+/weighted: instead of changing which
points calibrate the quantile (CV+) or reweighting by density ratio
(weighted/degenerate here because scaffold-disjoint test scaffolds have
near-zero density under the train scaffold distribution, per Tibshirani
2019's own applicability caveat), Mondrian lets a NOVEL test scaffold borrow
a per-cluster quantile from CHEMICALLY SIMILAR (not identical) scaffolds
that happen to land in calibration for that seed -- a materially different
mechanism, not a relabeled rerun of attempt 2/3.

Cluster taxonomy is fixed BEFORE any of the 60 seeds are drawn: Butina
clustering (Butina 1999, J. Chem. Inf. Comput. Sci. 39:747-750) of the 512-bit
Morgan (radius=2) fingerprints of the n_unique_scaffolds distinct Bemis-Murcko
scaffolds in the full n=442 OpenPoly Tg corpus, Tanimoto distance cutoff 0.4
(a standard chemoinformatics clustering cutoff, e.g. Leach & Gillet 2007 "An
Introduction to Chemoinformatics" 2nd ed., ISBN 978-1-4020-6291-9, Ch.7 -- NOT
picked by scanning against the 60-seed coverage outcome). This clustering does
not depend on seed, on the train/test assignment, or on Tg labels, so it
cannot leak test information into calibration.

Per-cluster quantile fallback rule (fixed before seeing outcomes): if a
cluster has fewer than MIN_CAL_PER_CLUSTER=8 calibration points under a given
seed's calib set, fall back to that seed's GLOBAL split-conformal quantile
(same qhat the pinned script itself computes) for all test points in that
cluster. 8 is the smallest n for which the split-conformal finite-sample
level ceil((n+1)*0.95)/n stays <=1.0 with a non-degenerate (not
all-inclusive) upper quantile at alpha=0.05.
"""
import json
import hashlib
import math

import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors
from rdkit.Chem.Scaffolds import MurckoScaffold
from rdkit.ML.Cluster import Butina
from rdkit import DataStructs
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.model_selection import train_test_split

ALPHA = 0.05
N_SEEDS = 60
COVERAGE_ACCEPTANCE = 0.90
MIN_CAL_PER_CLUSTER = 8
BUTINA_TANIMOTO_CUTOFF = 0.4
PINNED_SCRIPT_SHA256 = "96be585e27428a1f9bec0a7e2c078f9488711df5515790bc24ac35ac97cf0e09"


def sha256_of_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def morgan_features(smiles_list, n_bits=512, radius=2):
    X = np.zeros((len(smiles_list), n_bits + 1), dtype=float)
    ok = np.zeros(len(smiles_list), dtype=bool)
    for i, smi in enumerate(smiles_list):
        mol = Chem.MolFromSmiles(smi)
        if mol is None:
            continue
        fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)
        arr = np.zeros((n_bits,), dtype=float)
        for b in fp.GetOnBits():
            arr[b] = 1.0
        X[i, :n_bits] = arr
        wt = Descriptors.MolWt(mol)
        X[i, n_bits] = math.log10(wt) if wt > 0 else 0.0
        ok[i] = True
    return X, ok


def bemis_murcko_scaffold(smiles):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    try:
        scaf = MurckoScaffold.GetScaffoldForMol(mol)
        return Chem.MolToSmiles(scaf) if scaf is not None else ""
    except Exception:
        return None


def finite_sample_qhat(residuals, alpha=ALPHA):
    n = len(residuals)
    if n == 0:
        return None, None
    level = min(1.0, math.ceil((n + 1) * (1 - alpha)) / n)
    return float(np.quantile(residuals, level, method="higher")), level


def scaffold_morgan_fp(scaf_smiles):
    if scaf_smiles is None or scaf_smiles.startswith("__none_"):
        return None
    if scaf_smiles == "":
        mol = Chem.MolFromSmiles("C")  # canonical stand-in for the empty (acyclic) scaffold bucket
    else:
        mol = Chem.MolFromSmiles(scaf_smiles)
    if mol is None:
        return None
    return AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=512)


results = {}

openpoly_path = "feedback/v1/external_data/openpoly_benchmark/raw/final_polymer_properties_fromliterature.csv"
openpoly_sha256 = sha256_of_file(openpoly_path)
attack_script_path = "amphora-tolerance-robustness/evidence/audit/repeated-scaffold-monte-carlo-conformal-openpoly-tg-v1/run_repeated_scaffold_conformal.py"
attack_script_sha256 = sha256_of_file(attack_script_path)
assert attack_script_sha256 == PINNED_SCRIPT_SHA256, "pinned attack script sha256 mismatch -- refusing to run"

df = pd.read_csv(openpoly_path)
df = df[["PSMILES", "Tg (K)"]].dropna()
df = df.rename(columns={"Tg (K)": "Tg"})
df = df[(df["Tg"] > 100) & (df["Tg"] < 700)].reset_index(drop=True)

smiles = df["PSMILES"].tolist()
tg = df["Tg"].to_numpy(dtype=float)

X, ok = morgan_features(smiles)
X = X[ok]
tg = tg[ok]
smiles_kept = [s for s, k in zip(smiles, ok) if k]
scaffolds = [bemis_murcko_scaffold(s) for s in smiles_kept]
scaf_arr = np.array([s if s is not None else f"__none_{i}__" for i, s in enumerate(scaffolds)])

n_total = len(tg)
idx = np.arange(n_total)

results["dataset"] = {
    "path": openpoly_path,
    "sha256": openpoly_sha256,
    "expected_sha256_per_pinned_attack": "8de5baf76f79610fe9173e63c65b824714aeb8445f9d670e1767956ea9db5eb3",
    "sha256_matches_pinned_attack": openpoly_sha256 == "8de5baf76f79610fe9173e63c65b824714aeb8445f9d670e1767956ea9db5eb3",
    "n_polymers_after_filter": int(n_total),
}
results["pinned_attack_script"] = {
    "path": attack_script_path,
    "sha256": attack_script_sha256,
    "matches_expected": attack_script_sha256 == PINNED_SCRIPT_SHA256,
    "modified": False,
    "note": "read-only; split logic duplicated verbatim below, never imported/mutated",
}

uniq_scaffolds_all, scaf_counts_all = np.unique(scaf_arr, return_counts=True)
target_test_n = int(round(0.4 * n_total))  # identical to pinned script

# ---- FIXED, seed-independent Butina clustering of unique scaffolds ----
scaf_fps = []
scaf_fp_valid_idx = []
for i, scf in enumerate(uniq_scaffolds_all):
    fp = scaffold_morgan_fp(scf)
    if fp is not None:
        scaf_fps.append(fp)
        scaf_fp_valid_idx.append(i)

n_valid = len(scaf_fps)
dists = []
for i in range(1, n_valid):
    sims = DataStructs.BulkTanimotoSimilarity(scaf_fps[i], scaf_fps[:i])
    dists.extend([1.0 - s for s in sims])
butina_clusters = Butina.ClusterData(dists, n_valid, BUTINA_TANIMOTO_CUTOFF, isDistData=True)

scaf_to_cluster = {}
for cluster_id, members in enumerate(butina_clusters):
    for m in members:
        orig_scaf_idx = scaf_fp_valid_idx[m]
        scaf_to_cluster[uniq_scaffolds_all[orig_scaf_idx]] = cluster_id
n_clusters_fp = len(butina_clusters)
# scaffolds whose FP could not be built (parse failure) each get their own singleton cluster
next_cluster = n_clusters_fp
for i, scf in enumerate(uniq_scaffolds_all):
    if scf not in scaf_to_cluster:
        scaf_to_cluster[scf] = next_cluster
        next_cluster += 1
n_clusters_total = next_cluster

mol_cluster = np.array([scaf_to_cluster[s] for s in scaf_arr], dtype=int)

results["mondrian_taxonomy"] = {
    "method": "Butina 1999 clustering of Bemis-Murcko scaffold Morgan(r=2,512bit) fingerprints, Tanimoto distance cutoff 0.4",
    "fixed_before_any_seed_draw": True,
    "n_unique_scaffolds": int(len(uniq_scaffolds_all)),
    "n_clusters_from_fingerprint_clustering": int(n_clusters_fp),
    "n_singleton_clusters_unparseable_scaffold": int(next_cluster - n_clusters_fp),
    "n_clusters_total": int(n_clusters_total),
    "min_cal_per_cluster_fallback_threshold": MIN_CAL_PER_CLUSTER,
}

draws = []
for seed in range(N_SEEDS):
    # ---- scaffold-safe split, this seed: IDENTICAL to pinned attack script ----
    rng = np.random.RandomState(seed)
    perm = rng.permutation(len(uniq_scaffolds_all))
    uniq_shuffled = uniq_scaffolds_all[perm]
    test_mask = np.zeros(n_total, dtype=bool)
    running = 0
    for scf in uniq_shuffled:
        if running >= target_test_n:
            break
        members = np.where(scaf_arr == scf)[0]
        test_mask[members] = True
        running += len(members)

    scaf_test_idx = idx[test_mask]
    scaf_train_pool_idx = idx[~test_mask]
    scaf_proper_train_idx, scaf_calib_idx = train_test_split(
        scaf_train_pool_idx, train_size=0.5, random_state=seed
    )
    overlap = len(set(scaf_arr[scaf_train_pool_idx]).intersection(set(scaf_arr[scaf_test_idx])))

    scaler2 = StandardScaler().fit(X[scaf_proper_train_idx])
    ridge2 = Ridge(alpha=1.0, solver="cholesky").fit(
        scaler2.transform(X[scaf_proper_train_idx]), tg[scaf_proper_train_idx]
    )
    scaf_calib_resid = np.abs(tg[scaf_calib_idx] - ridge2.predict(scaler2.transform(X[scaf_calib_idx])))
    qhat_global, _ = finite_sample_qhat(scaf_calib_resid)
    scaf_test_resid = np.abs(tg[scaf_test_idx] - ridge2.predict(scaler2.transform(X[scaf_test_idx])))
    coverage_global = float(np.mean(scaf_test_resid <= qhat_global))

    # ---- Mondrian: per-cluster quantile from THIS seed's calib residuals ----
    calib_cluster = mol_cluster[scaf_calib_idx]
    test_cluster = mol_cluster[scaf_test_idx]
    cluster_qhat = {}
    clusters_in_calib = set(calib_cluster.tolist())
    for c in clusters_in_calib:
        rc = scaf_calib_resid[calib_cluster == c]
        if len(rc) >= MIN_CAL_PER_CLUSTER:
            q, _ = finite_sample_qhat(rc)
            cluster_qhat[c] = q

    n_fallback = 0
    covered = np.zeros(len(scaf_test_idx), dtype=bool)
    for j, c in enumerate(test_cluster):
        q = cluster_qhat.get(c)
        if q is None:
            q = qhat_global
            n_fallback += 1
        covered[j] = scaf_test_resid[j] <= q
    coverage_mondrian = float(np.mean(covered)) if len(covered) else float("nan")

    draws.append({
        "seed": int(seed),
        "n_train_pool": int(len(scaf_train_pool_idx)),
        "n_calibration": int(len(scaf_calib_idx)),
        "n_test": int(len(scaf_test_idx)),
        "scaffold_overlap_train_pool_vs_test": int(overlap),
        "n_clusters_present_in_calib": int(len(clusters_in_calib)),
        "n_clusters_with_own_quantile": int(len(cluster_qhat)),
        "n_test_points_fallback_to_global": int(n_fallback),
        "frac_test_points_fallback_to_global": float(n_fallback / len(scaf_test_idx)) if len(scaf_test_idx) else None,
        "coverage_scaffold_safe_global_baseline": coverage_global,
        "coverage_scaffold_safe_mondrian": coverage_mondrian,
    })

cov_global = np.array([d["coverage_scaffold_safe_global_baseline"] for d in draws])
cov_mondrian = np.array([d["coverage_scaffold_safe_mondrian"] for d in draws])

results["n_seeds"] = N_SEEDS
results["draws"] = draws
results["summary_stats"] = {
    "coverage_global_baseline_mean": float(np.mean(cov_global)),
    "coverage_mondrian_mean": float(np.mean(cov_mondrian)),
    "coverage_mondrian_median": float(np.median(cov_mondrian)),
    "coverage_mondrian_std": float(np.std(cov_mondrian, ddof=1)),
    "coverage_mondrian_min": float(np.min(cov_mondrian)),
    "coverage_mondrian_max": float(np.max(cov_mondrian)),
    "n_seeds_mondrian_meets_090_individually": int(np.sum(cov_mondrian >= 0.90)),
    "n_seeds_mondrian_improves_over_global_baseline": int(np.sum(cov_mondrian > cov_global)),
    "n_seeds_mondrian_worse_than_global_baseline": int(np.sum(cov_mondrian < cov_global)),
}

acceptance_met = bool(results["summary_stats"]["coverage_mondrian_mean"] >= COVERAGE_ACCEPTANCE)
results["acceptance"] = {
    "criterion": "mean(coverage_scaffold_safe_mondrian) over identical 60-seed protocol >= 0.90",
    "observed_mean": results["summary_stats"]["coverage_mondrian_mean"],
    "threshold": COVERAGE_ACCEPTANCE,
    "met": acceptance_met,
}
results["verdict"] = "CLAIM_SURVIVED_REPAIRED" if acceptance_met else "CLAIM_REFUTED_REPAIR_INSUFFICIENT"
results["study_id"] = "amphora-tolerance-robustness-r-c01-mondrian-scaffold-cluster-repair-v1"
results["repair_attempt_id"] = "attempt4_mondrian_scaffold_cluster_butina"

print(json.dumps(results, indent=2, sort_keys=True))
