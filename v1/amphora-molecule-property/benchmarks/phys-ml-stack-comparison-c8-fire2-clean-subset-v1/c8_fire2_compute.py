#!/usr/bin/env python3
"""C8 fire 2: does ML's apparent edge over Onsager physics for RadonPy dielectric
constant survive when BOTH train and test are restricted to the physically-valid
(eps_static >= n_measured^2) subset -- i.e. a clean-only pipeline with zero
contamination anywhere, not just a clean-test-slice-of-a-contaminated-model as
fire 1 reported (n=20, RF trained on the full 89.5%-corrupted population)?

Pre-registered refute criterion (fixed BEFORE running):
  The claim "ML clearly outperforms Onsager physics for RadonPy dielectric
  constant" (shipped mixed-dielectric-conformal-kpi; fire-1 full-population
  numbers: physics R2=-1.67 MAE=9.63 vs ML R2=+0.64 MAE=1.47) is REFUTED if,
  on a strictly clean-only train/calib/test pipeline (RF retrained from
  scratch on ONLY physically-valid rows), EITHER:
    (a) ML's test R2 <= 0 (no better than predicting the mean), OR
    (b) the paired bootstrap 90% CI (n_boot=2000, seed=0) of
        (physics_MAE - ML_MAE) on the test set includes zero
        (ML's MAE advantage is not distinguishable from chance at this
        honest, uncontaminated sample size).
  Both would show the previously-observed "ML beats physics" gap is an
  artifact of scale (n=1075 contaminated rows) rather than real predictive
  skill on trustworthy dielectric labels.
"""
import csv, json, math, os, re
import numpy as np
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

from rdkit import Chem, RDLogger
RDLogger.DisableLog("rdApp.*")
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge

SEED = 0
FP_RADIUS = 2
FP_BITS = 512

ROOT = "/home/ubuntu/amphora/build/mvp20-split"
RADONPY_CSV = f"{ROOT}/feedback/v1/external_data/radonpy_pi1070/raw/PI1070.csv"
DK_ML_KPI = f"{ROOT}/amphora-molecule-property/evidence/phase0/kpis/mixed-openpoly-radonpy-dielectric-conformal-kpi.v1.json"
FIRE1_RECEIPT = f"{ROOT}/amphora-molecule-property/benchmarks/phys-ml-stack-comparison-c8-v1/c8_phys_ml_stack_comparison_receipt.v1.json"

def file_sha256(p):
    import hashlib
    with open(p, "rb") as f: return hashlib.sha256(f.read()).hexdigest()

# ---- verbatim helper functions (from c8_compute.py / /tmp/*.py, methodological parity)
def psmiles_to_mol(psmi):
    if not psmi: return None
    s = psmi
    s = re.sub(r"\[\*:\d+\]", "[*]", s)
    s = re.sub(r"\*:\d+", "*", s)
    s = s.replace("[*]", "[CH3]").replace("*", "[CH3]").replace("[[CH3]]", "[CH3]")
    try: return Chem.MolFromSmiles(s)
    except Exception: return None

def morgan_fp(mol):
    from rdkit.Chem import rdFingerprintGenerator
    gen = rdFingerprintGenerator.GetMorganGenerator(radius=FP_RADIUS, fpSize=FP_BITS)
    return gen.GetFingerprintAsNumPy(mol).astype(np.float32)

def metrics(pred, actual):
    pred = np.asarray(pred, dtype=np.float64); actual = np.asarray(actual, dtype=np.float64)
    err = pred - actual
    return {
        "MAE": float(np.mean(np.abs(err))),
        "RMSE": float(np.sqrt(np.mean(err ** 2))),
        "R2": float(1 - np.sum(err ** 2) / max(np.sum((actual - np.mean(actual)) ** 2), 1e-12)),
        "pearson_r": float(np.corrcoef(pred, actual)[0, 1]) if np.std(pred) > 0 and np.std(actual) > 0 else 0.0,
        "n": int(len(pred)),
    }

def stack_fit_eval(rf_calib, phys_calib, y_calib, rf_test, phys_test, y_test):
    Z_calib = np.column_stack([rf_calib, phys_calib])
    meta = Ridge(alpha=1.0, random_state=SEED).fit(Z_calib, y_calib)
    w = meta.coef_.tolist(); b = float(meta.intercept_)
    Z_test = np.column_stack([rf_test, phys_test])
    stack_pred = meta.predict(Z_test)
    return {
        "weights": {"w_rf": float(w[0]), "w_physics": float(w[1]), "intercept": b},
        "test_metrics": metrics(stack_pred, y_test),
        "stack_pred_test": stack_pred,
    }

N_A = 6.02214076e23
EPS0 = 8.8541878128e-12
K_B = 1.380649e-23
DEBYE = 3.33564e-30

def onsager_eps(s, rho_g_cm3, M, mu_D, T_K):
    number_density = N_A * (rho_g_cm3 * 1e6) / M
    mu = mu_D * DEBYE
    A = number_density * mu * mu / (9.0 * EPS0 * K_B * T_K)
    B = s + A * (s + 2.0) ** 2
    return (B + (B * B + 8.0 * s * s) ** 0.5) / 4.0

# ---- load RadonPy, rebuild dk_records exactly as fire 1 did
rows_rp = list(csv.DictReader(open(RADONPY_CSV)))
dk_records = []
n_dropped_missing = 0
for r in rows_rp:
    try:
        eps_s = float(r["static_dielectric_const"])
        n_meas = float(r["refractive_index"])
        rho = float(r["density"])
        M = float(r["mol_weight_monomer"])
        mu = float(r["qm_dipole_monomer"])
        T = float(r["temp"])
    except (ValueError, KeyError):
        n_dropped_missing += 1; continue
    if not (eps_s > 0 and n_meas > 1.0 and rho > 0 and M > 0 and T > 0):
        n_dropped_missing += 1; continue
    mol = psmiles_to_mol(r["smiles"])
    if mol is None: n_dropped_missing += 1; continue
    dk_records.append({
        "monomer_ID": r["monomer_ID"], "smiles": r["smiles"], "mol": mol,
        "eps_s": eps_s, "n_meas": n_meas, "rho": rho, "M": M, "mu_D": mu, "T": T,
    })
n_dk_total = len(dk_records)
print(f"n_valid_total = {n_dk_total} (dropped {n_dropped_missing}) -- must equal fire 1's n_dk=1075")
assert n_dk_total == 1075, f"population mismatch vs fire 1: {n_dk_total} != 1075"

for r in dk_records:
    r["physics_pred"] = onsager_eps(r["n_meas"] ** 2, r["rho"], r["M"], r["mu_D"], r["T"])
    r["valid"] = r["eps_s"] >= r["n_meas"] ** 2

n_violations = sum(1 for r in dk_records if not r["valid"])
print(f"violations = {n_violations}/{n_dk_total} = {n_violations/n_dk_total:.1%} -- must equal fire 1's 962/1075=89.5%")
assert n_violations == 962, f"violation count mismatch vs fire 1: {n_violations} != 962"

clean_records = [r for r in dk_records if r["valid"]]
n_clean = len(clean_records)
print(f"n_clean (physically-valid subset, TRAIN+CALIB+TEST all restricted to this) = {n_clean}")

# ---- clean-only split, 60/20/20, seed=0 (plain random, same convention as fire 1's dielectric split)
rng = np.random.RandomState(SEED)
idx = np.arange(n_clean); rng.shuffle(idx)
n_train = int(n_clean * 0.60); n_calib = int(n_clean * 0.20)
idx_train = idx[:n_train]; idx_calib = idx[n_train:n_train + n_calib]; idx_test = idx[n_train + n_calib:]
print(f"clean split: train={len(idx_train)}, calib={len(idx_calib)}, test={len(idx_test)}")

X_clean = np.stack([morgan_fp(r["mol"]) for r in clean_records])
mw_col = np.array([[np.log10(r["M"])] for r in clean_records], dtype=np.float32)
X_clean = np.concatenate([X_clean, mw_col], axis=1)
y_clean = np.array([r["eps_s"] for r in clean_records], dtype=np.float64)
phys_clean = np.array([r["physics_pred"] for r in clean_records], dtype=np.float64)

rf_clean = RandomForestRegressor(n_estimators=300, max_depth=10, random_state=SEED, n_jobs=1)
rf_clean.fit(X_clean[idx_train], y_clean[idx_train])
rf_pred_calib = rf_clean.predict(X_clean[idx_calib])
rf_pred_test = rf_clean.predict(X_clean[idx_test])
phys_calib = phys_clean[idx_calib]; phys_test = phys_clean[idx_test]
y_calib = y_clean[idx_calib]; y_test = y_clean[idx_test]

clean_stack = stack_fit_eval(rf_pred_calib, phys_calib, y_calib, rf_pred_test, phys_test, y_test)
clean_physics = metrics(phys_test, y_test)
clean_ml = metrics(rf_pred_test, y_test)
print(f"[CLEAN-ONLY pipeline, n_test={len(idx_test)}]")
print(f"  physics: MAE={clean_physics['MAE']:.4f} R2={clean_physics['R2']:+.4f}")
print(f"  ml:      MAE={clean_ml['MAE']:.4f} R2={clean_ml['R2']:+.4f}")
print(f"  stack:   MAE={clean_stack['test_metrics']['MAE']:.4f} R2={clean_stack['test_metrics']['R2']:+.4f}")

# ---- paired bootstrap on (physics_MAE - ML_MAE) at test-set resolution
n_boot = 2000
boot_rng = np.random.RandomState(SEED)
abs_err_phys = np.abs(phys_test - y_test)
abs_err_ml = np.abs(rf_pred_test - y_test)
diffs = []
for _ in range(n_boot):
    bidx = boot_rng.randint(0, len(y_test), size=len(y_test))
    diffs.append(np.mean(abs_err_phys[bidx]) - np.mean(abs_err_ml[bidx]))
diffs = np.array(diffs)
ci_lo, ci_hi = float(np.percentile(diffs, 5)), float(np.percentile(diffs, 95))
point_diff = float(np.mean(abs_err_phys) - np.mean(abs_err_ml))
ci_includes_zero = bool(ci_lo <= 0.0 <= ci_hi)
print(f"paired bootstrap (physics_MAE - ML_MAE): point={point_diff:.4f}, 90% CI=[{ci_lo:.4f},{ci_hi:.4f}], includes_zero={ci_includes_zero}")

criterion_a = clean_ml["R2"] <= 0.0
criterion_b = ci_includes_zero
refuted = bool(criterion_a or criterion_b)
print(f"REFUTE CRITERION (a) ml_R2<=0: {criterion_a}")
print(f"REFUTE CRITERION (b) bootstrap CI includes zero: {criterion_b}")
print(f"VERDICT: {'REFUTED (ML edge is NOT robust to a clean-only pipeline)' if refuted else 'SURVIVED (ML edge holds even with zero-contamination pipeline)'}")

fire1 = json.load(open(FIRE1_RECEIPT))
fire1_dk = fire1["per_property_comparison"]["dielectric"]

RESULT = {
    "attack": "C8 fire 2: clean-only (zero-contamination) dielectric physics-vs-ML-vs-stack pipeline on RadonPy PI1070, escalating fire 1's contaminated-train/clean-test-slice (n=20) probe into a fully clean train+calib+test pipeline (n_clean=%d)." % n_clean,
    "pre_registered_refute_criterion": {
        "criterion_a": "ML test R2 <= 0 on the clean-only pipeline (no better than predicting the mean)",
        "criterion_b": "paired bootstrap (n_boot=2000, seed=0) 90%% CI of (physics_MAE - ML_MAE) on the clean test set includes zero",
        "logic": "EITHER criterion refutes the claim that ML's apparent large advantage over Onsager physics (shipped KPI, fire-1 full-population: physics R2=-1.67 vs ML R2=+0.64) is real predictive skill rather than an artifact of scoring against 89.5%-corrupted labels at large n.",
    },
    "population": {
        "total_radonpy_dielectric_rows": n_dk_total,
        "physically_valid_rows_eps_static_ge_n2": n_clean,
        "violation_rows_excluded": n_violations,
        "fraction_clean": n_clean / n_dk_total,
    },
    "split": "clean-only plain random 60/20/20 (seed=0), n_train=%d, n_calib=%d, n_test=%d -- RF retrained FROM SCRATCH on clean-train only (fire 1's RF was trained on the full 89.5%%-corrupted population and only test-sliced to n=20 clean rows)" % (len(idx_train), len(idx_calib), len(idx_test)),
    "physics_clean_only": clean_physics,
    "ml_clean_only": clean_ml,
    "stack_clean_only": clean_stack["test_metrics"],
    "stack_weights_clean_only": clean_stack["weights"],
    "paired_bootstrap_physics_minus_ml_mae": {
        "n_boot": n_boot, "point_estimate": point_diff,
        "ci90_lo": ci_lo, "ci90_hi": ci_hi, "includes_zero": ci_includes_zero,
    },
    "criterion_a_ml_r2_le_0": criterion_a,
    "criterion_b_ci_includes_zero": criterion_b,
    "verdict": "REFUTED" if refuted else "SURVIVED",
    "comparison_to_fire1": {
        "fire1_full_population_contaminated_train_and_test": {
            "physics_MAE": fire1_dk["physics"]["full_population_test_MAE"], "physics_R2": fire1_dk["physics"]["full_population_test_R2"],
            "ml_MAE": fire1_dk["ml"]["full_population_test_MAE"], "ml_R2": fire1_dk["ml"]["full_population_test_R2"],
        },
        "fire1_contaminated_train_clean_test_slice_n20": {
            "physics_MAE": fire1_dk["physics"]["physically_valid_subset_test_MAE"], "physics_R2": fire1_dk["physics"]["physically_valid_subset_test_R2"],
            "ml_MAE": fire1_dk["ml"]["physically_valid_subset_test_MAE"], "ml_R2": fire1_dk["ml"]["physically_valid_subset_test_R2"],
            "n": fire1_dk["physics"]["physically_valid_subset_n"],
        },
        "fire2_clean_train_and_test_this_fire": {
            "physics_MAE": clean_physics["MAE"], "physics_R2": clean_physics["R2"],
            "ml_MAE": clean_ml["MAE"], "ml_R2": clean_ml["R2"],
            "n": len(idx_test),
        },
        "interpretation": (
            "Training the RF from scratch on ONLY the physically-valid rows (n_train=%d) rather than "
            "the full 89.5%%-corrupted population removes the large-n advantage that let ML fit the "
            "corrupted majority's low-variance near-electronic-limit values. This isolates whether ML's "
            "edge over physics reflects genuine chemical-structure-to-dielectric-constant skill or "
            "simply exploiting the corrupted population's homogeneity." % len(idx_train)
        ),
    },
    "cited_receipt_sha256": {"fire1_c8_receipt": file_sha256(FIRE1_RECEIPT), "mixed_dielectric_ml_kpi": file_sha256(DK_ML_KPI)},
}

with open("/tmp/c8_fire2_raw_results.json", "w") as f:
    json.dump(RESULT, f, indent=2)
print("\nWROTE /tmp/c8_fire2_raw_results.json")
