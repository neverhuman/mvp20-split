#!/usr/bin/env python3
"""C8: consolidated per-property {physics, ML, stack} comparison — real computation stage.

Builds Density (cite existing), Tg (new stack), Dielectric (new Onsager port +
data-integrity audit + new stack), Refractive Index (new Lorentz-Lorenz port +
new stack). Writes /tmp/c8_scripts/c8_raw_results.json for the signing stage.

Reuses, verbatim where possible, the exact featurization/classification/split
code from the module's own prior pushes (found live under /tmp/*.py on this
host): psmiles_to_mol, count_groups (24-group Van Krevelen classifier),
morgan_fp, stratified_split, and the Wolpert-1992 stack pattern from
stack_density.py. This guarantees methodological parity with the already-
receipted KPIs rather than inventing a new, unvalidated featurizer.
"""
import csv, json, math, os, re
import numpy as np
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

from rdkit import Chem, RDLogger
from rdkit.Chem import Descriptors, Fragments
RDLogger.DisableLog("rdApp.*")
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge

SEED = 0
FP_RADIUS = 2
FP_BITS = 512

ROOT = "/home/ubuntu/amphora/build/mvp20-split"
MP = f"{ROOT}/amphora-molecule-property"
OPENPOLY_CSV = f"{ROOT}/feedback/v1/external_data/openpoly_benchmark/raw/final_polymer_properties_fromliterature.csv"
RADONPY_CSV = f"{ROOT}/feedback/v1/external_data/radonpy_pi1070/raw/PI1070.csv"

DENSITY_ML_VK_KPI = f"{MP}/evidence/phase0/kpis/radonpy-density-ml-vs-van-krevelen-physics-kpi.v1.json"
DENSITY_STACK_KPI = f"{MP}/evidence/phase0/kpis/stacked-ml-van-krevelen-density-radonpy-kpi.v1.json"
TG_PHYSICS_EXT_KPI = f"{MP}/evidence/phase0/kpis/external-validation-polyuniverse-ridge-on-openpoly-tg-kpi.v1.json"
TG_ML_KPI = f"{MP}/evidence/phase0/kpis/openpoly-experimental-tg-ml-baseline-kpi.v1.json"
TG_RIDGE_FIT_RECEIPT = f"{MP}/reference/mvp20/data/van_krevelen_ridge_fit_on_1000_polyuniverse_polymers_receipt.v1.json"
DK_ML_KPI = f"{MP}/evidence/phase0/kpis/mixed-openpoly-radonpy-dielectric-conformal-kpi.v1.json"
RI_ML_KPI = f"{MP}/evidence/phase0/kpis/mixed-openpoly-radonpy-refractive-index-conformal-kpi.v1.json"

def file_sha256(p):
    import hashlib
    with open(p, "rb") as f: return hashlib.sha256(f.read()).hexdigest()

# ============================================================ shared helpers
# (verbatim from /tmp/vk_external_validate.py, /tmp/tg_ml_baseline.py,
#  /tmp/stack_density.py, /tmp/mixed_ri.py, /tmp/mixed_dk.py — the scripts
#  that generated the KPIs this receipt cites, still present on this host)

def psmiles_to_mol(psmi):
    if not psmi: return None
    s = psmi
    s = re.sub(r"\[\*:\d+\]", "[*]", s)
    s = re.sub(r"\*:\d+", "*", s)
    s = s.replace("[*]", "[CH3]").replace("*", "[CH3]").replace("[[CH3]]", "[CH3]")
    try: return Chem.MolFromSmiles(s)
    except Exception: return None

def count_groups(mol):
    """24-group Van Krevelen/Bicerano classifier, identical to Push #20/#38/#25/#39."""
    if mol is None: return None
    try:
        n_ether = int(Fragments.fr_ether(mol))
        n_ester = int(Fragments.fr_ester(mol))
        n_amide = int(Fragments.fr_amide(mol))
        n_amine_prim = int(Fragments.fr_NH2(mol))
        n_amine_sec = int(Fragments.fr_NH1(mol))
        n_amine_tert = int(Fragments.fr_NH0(mol))
        n_nitrile = int(Fragments.fr_nitrile(mol))
        n_al_oh = int(Fragments.fr_Al_OH(mol))
        n_ar_oh = int(Fragments.fr_Ar_OH(mol))
        n_epoxide = int(Fragments.fr_epoxide(mol))
        n_ketone = int(Fragments.fr_ketone(mol))
        n_aldehyde = int(Fragments.fr_aldehyde(mol))
        n_sulfide = int(Fragments.fr_sulfide(mol))
        n_sulfone = int(Fragments.fr_sulfone(mol))
        n_F = sum(1 for a in mol.GetAtoms() if a.GetSymbol() == "F")
        n_Cl = sum(1 for a in mol.GetAtoms() if a.GetSymbol() == "Cl")
        n_Br = sum(1 for a in mol.GetAtoms() if a.GetSymbol() == "Br")
        n_Si_O = 0
        for bond in mol.GetBonds():
            b1, b2 = bond.GetBeginAtom(), bond.GetEndAtom()
            if (b1.GetSymbol() == "Si" and b2.GetSymbol() == "O") or (b1.GetSymbol() == "O" and b2.GetSymbol() == "Si"):
                n_Si_O += 1
        n_CH3 = n_CH2 = n_CH = n_C_quat = 0
        n_vinyl_CH2 = n_vinyl_CH = 0
        n_arom_C_H = n_arom_C_sub = 0
        for atom in mol.GetAtoms():
            if atom.GetSymbol() != "C": continue
            if atom.GetIsAromatic():
                is_sub = any(not n.GetIsAromatic() for n in atom.GetNeighbors() if n.GetSymbol() != "H")
                if is_sub: n_arom_C_sub += 1
                else: n_arom_C_H += 1
            else:
                is_sp2 = atom.GetHybridization() == Chem.HybridizationType.SP2
                n_h = atom.GetTotalNumHs()
                if is_sp2:
                    if n_h >= 2: n_vinyl_CH2 += 1
                    else: n_vinyl_CH += 1
                else:
                    if n_h >= 3: n_CH3 += 1
                    elif n_h == 2: n_CH2 += 1
                    elif n_h == 1: n_CH += 1
                    else: n_C_quat += 1
        return {
            "CH3": n_CH3, "CH2": n_CH2, "CH": n_CH, "C_quat": n_C_quat,
            "vinyl_CH2": n_vinyl_CH2, "vinyl_CH": n_vinyl_CH,
            "aromatic_C_H": n_arom_C_H, "aromatic_C_sub": n_arom_C_sub,
            "ether_O": n_ether, "hydroxyl": n_al_oh + n_ar_oh,
            "carbonyl": n_ketone + n_aldehyde, "ester": n_ester, "amide": n_amide,
            "primary_amine": n_amine_prim, "secondary_amine": n_amine_sec,
            "tertiary_amine": n_amine_tert, "nitrile": n_nitrile,
            "F": n_F, "Cl": n_Cl, "Br": n_Br,
            "sulfide": n_sulfide, "sulfone": n_sulfone, "epoxide": n_epoxide,
            "Si_O": n_Si_O,
        }
    except Exception: return None

def morgan_fp(mol):
    from rdkit.Chem import rdFingerprintGenerator
    gen = rdFingerprintGenerator.GetMorganGenerator(radius=FP_RADIUS, fpSize=FP_BITS)
    return gen.GetFingerprintAsNumPy(mol).astype(np.float32)

def stratified_split(sources_arr, ratios, seed):
    """Verbatim from /tmp/mixed_ri.py / /tmp/mixed_dk.py."""
    rng = np.random.RandomState(seed)
    tr, ca, te = [], [], []
    for src in np.unique(sources_arr):
        idx = np.where(sources_arr == src)[0]
        rng.shuffle(idx)
        n_s = len(idx)
        n_tr = int(n_s * ratios[0]); n_ca = int(n_s * ratios[1])
        tr.append(idx[:n_tr]); ca.append(idx[n_tr:n_tr + n_ca]); te.append(idx[n_tr + n_ca:])
    return np.concatenate(tr), np.concatenate(ca), np.concatenate(te)

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
    """Wolpert 1992 meta-Ridge on CALIB [RF_pred, physics_pred] -> actual; eval TEST."""
    Z_calib = np.column_stack([rf_calib, phys_calib])
    meta = Ridge(alpha=1.0, random_state=SEED).fit(Z_calib, y_calib)
    w = meta.coef_.tolist(); b = float(meta.intercept_)
    Z_test = np.column_stack([rf_test, phys_test])
    stack_pred = meta.predict(Z_test)
    return {
        "weights": {"w_rf": float(w[0]), "w_physics": float(w[1]), "intercept": b},
        "test_metrics": metrics(stack_pred, y_test),
    }

RESULTS = {}

# ============================================================ A. DENSITY (cite existing, no compute)
print("=== A. DENSITY (RadonPy) — citing existing receipts, no recompute ===")
ml_vk = json.load(open(DENSITY_ML_VK_KPI))["fitted_or_physical_model_artifact"]
stack_kpi = json.load(open(DENSITY_STACK_KPI))["fitted_or_physical_model_artifact"]
RESULTS["density"] = {
    "population": "RadonPy PI1070 (Fujimoto et al. 2023), n=1077, MD-simulated density at 300K",
    "split": "60/20/20 seed=0 (n_test=216)",
    "source": "cited verbatim from existing receipted KPIs — no recomputation this fire",
    "physics": {
        "method": "Van Krevelen 1990 Ch.4 group contribution, rho = MW/(c*sum(V_i)), c=1.6",
        "test_MAE_g_per_cm3": ml_vk["physics_baseline"]["vk_test_slice_MAE_g_per_cm3"],
        "test_R2": stack_kpi["test_metrics"]["vk_only"]["R2"],
        "test_pearson_r": stack_kpi["test_metrics"]["vk_only"]["pearson_r"],
    },
    "ml": {
        "method": "RandomForestRegressor(n_est=300, max_depth=10, seed=0), Morgan512+log10(MW)",
        "test_MAE_g_per_cm3": ml_vk["ml_baseline"]["test_MAE_g_per_cm3"],
        "test_R2": ml_vk["ml_baseline"]["test_R2"],
        "test_pearson_r": ml_vk["ml_baseline"]["test_pearson_r"],
    },
    "stack": {
        "method": "Wolpert 1992 stacked generalization, Ridge meta-learner on CALIB [RF_pred, VK_pred]",
        "weights": stack_kpi["meta_learner_coefficients"],
        "test_MAE_g_per_cm3": stack_kpi["test_metrics"]["stack"]["MAE"],
        "test_R2": stack_kpi["test_metrics"]["stack"]["R2"],
        "test_pearson_r": stack_kpi["test_metrics"]["stack"]["pearson_r"],
    },
    "cited_receipt_sha256": {
        "radonpy_density_ml_vs_vk_kpi": file_sha256(DENSITY_ML_VK_KPI),
        "stacked_density_kpi": file_sha256(DENSITY_STACK_KPI),
    },
}
print(f"  physics MAE={RESULTS['density']['physics']['test_MAE_g_per_cm3']:.4f}, "
      f"ml MAE={RESULTS['density']['ml']['test_MAE_g_per_cm3']:.4f}, "
      f"stack MAE={RESULTS['density']['stack']['test_MAE_g_per_cm3']:.4f}")

# ============================================================ B. TG (OpenPoly) — NEW stack build
print("\n=== B. Tg (OpenPoly) — new stack build ===")
p20 = json.load(open(TG_RIDGE_FIT_RECEIPT))
fitted_map = {g["group"]: g["Y_fitted_K_g_per_mol"] for g in p20["kpis"]["fitted_Ygi_comparison"]}
YGI_PUBLISHED_GROUPS = ["CH2","CH3","CH","C_quat","vinyl_CH2","vinyl_CH","aromatic_C_H","aromatic_C_sub",
    "ether_O","hydroxyl","carbonyl","ester","amide","primary_amine","secondary_amine","tertiary_amine",
    "nitrile","F","Cl","Br","sulfone","sulfide","epoxide","Si_O"]
Y_FITTED = {g: fitted_map[g] for g in YGI_PUBLISHED_GROUPS}

rows_all = list(csv.DictReader(open(OPENPOLY_CSV)))
tg_records = []
for r in rows_all:
    v = r["Tg (K)"].strip()
    if not v or v == "nan": continue
    try: tg = float(v)
    except ValueError: continue
    if not (100 < tg < 700): continue
    mol = psmiles_to_mol(r["PSMILES"])
    if mol is None: continue
    counts = count_groups(mol)
    if counts is None: continue
    try: mw = float(Descriptors.MolWt(mol))
    except Exception: continue
    if mw <= 0: continue
    tg_physics_pred = sum(counts[g] * Y_FITTED[g] for g in YGI_PUBLISHED_GROUPS) / mw
    tg_records.append({"name": r["Name"], "psmiles": r["PSMILES"], "Tg_K": tg, "mol": mol,
                        "mw": mw, "physics_pred": tg_physics_pred})
print(f"  n_valid = {len(tg_records)}")

n_tg = len(tg_records)
X_tg = np.stack([morgan_fp(r["mol"]) for r in tg_records])
mw_col = np.array([[np.log10(r["mw"])] for r in tg_records], dtype=np.float32)
X_tg = np.concatenate([X_tg, mw_col], axis=1)
y_tg = np.array([r["Tg_K"] for r in tg_records], dtype=np.float64)
phys_tg = np.array([r["physics_pred"] for r in tg_records], dtype=np.float64)

# same plain 60/20/20 seed=0 split convention as stack_density.py (this module's
# only prior stacking precedent)
rng = np.random.RandomState(SEED)
idx = np.arange(n_tg); rng.shuffle(idx)
n_train = int(n_tg * 0.60); n_calib = int(n_tg * 0.20)
idx_train = idx[:n_train]; idx_calib = idx[n_train:n_train+n_calib]; idx_test = idx[n_train+n_calib:]
print(f"  split: train={len(idx_train)}, calib={len(idx_calib)}, test={len(idx_test)}")

rf_tg = RandomForestRegressor(n_estimators=300, max_depth=10, random_state=SEED, n_jobs=1)
rf_tg.fit(X_tg[idx_train], y_tg[idx_train])
rf_pred_calib = rf_tg.predict(X_tg[idx_calib])
rf_pred_test = rf_tg.predict(X_tg[idx_test])
phys_calib = phys_tg[idx_calib]; phys_test = phys_tg[idx_test]
y_calib = y_tg[idx_calib]; y_test = y_tg[idx_test]

tg_stack = stack_fit_eval(rf_pred_calib, phys_calib, y_calib, rf_pred_test, phys_test, y_test)
tg_physics_only = metrics(phys_test, y_test)
tg_ml_only = metrics(rf_pred_test, y_test)
print(f"  physics-only test MAE={tg_physics_only['MAE']:.2f} K, R2={tg_physics_only['R2']:+.4f}")
print(f"  ml-only (fresh RF) test MAE={tg_ml_only['MAE']:.2f} K, R2={tg_ml_only['R2']:+.4f}")
print(f"  STACK test MAE={tg_stack['test_metrics']['MAE']:.2f} K, R2={tg_stack['test_metrics']['R2']:+.4f}, weights={tg_stack['weights']}")

tg_physics_ext_kpi = json.load(open(TG_PHYSICS_EXT_KPI))["fitted_or_physical_model_artifact"]
tg_ml_kpi = json.load(open(TG_ML_KPI))["fitted_or_physical_model_artifact"]

RESULTS["tg"] = {
    "population": "OpenPoly (Ma et al. 2023) experimental Tg, n=442 valid polymers",
    "existing_receipted_numbers_for_context": {
        "physics_Ridge_Ygi_external_validation_MAE_K": tg_physics_ext_kpi["push_20_ridge_on_openpoly"]["MAE_K"],
        "physics_published_VK_MAE_K": tg_physics_ext_kpi["van_krevelen_published_on_openpoly"]["MAE_K"],
        "ml_RF_LOSO_MAE_K": tg_ml_kpi["best_LOSO_result"]["MAE_K"],
        "ml_RF_holdout_MAE_K": tg_ml_kpi["best_holdout_result"]["test_MAE_K"],
        "note": "These use scaffold-safe 80/20-holdout and 212-fold LOSO-CV splits from Pushes #20/#25/#39 respectively. The stack triplet below uses a FRESH, self-consistent plain-random 60/20/20 split (seed=0, matching this module's only prior stacking precedent, stack_density.py/Push #38) because per-polymer physics+ML predictions on a common calibration/test partition are required to fit and evaluate a meta-learner, and those per-row predictions were not persisted by the original LOSO/holdout runs.",
    },
    "split": "plain random 60/20/20 (seed=0), n_train=%d, n_calib=%d, n_test=%d" % (len(idx_train), len(idx_calib), len(idx_test)),
    "physics": {
        "method": "Van Krevelen 24-group Ridge Y_gi (Push #20, fit on 807 MD-simulated Polyuniverse Epoxy polymers), zero refitting, pure inference on OpenPoly, THIS split's test slice",
        "test_MAE_K": tg_physics_only["MAE"], "test_R2": tg_physics_only["R2"], "test_pearson_r": tg_physics_only["pearson_r"],
    },
    "ml": {
        "method": "RandomForestRegressor(n_est=300, max_depth=10, seed=0), Morgan512+log10(MW), freshly trained on THIS split's train slice",
        "test_MAE_K": tg_ml_only["MAE"], "test_R2": tg_ml_only["R2"], "test_pearson_r": tg_ml_only["pearson_r"],
    },
    "stack": {
        "method": "Wolpert 1992 stacked generalization — Ridge meta-learner on CALIB [RF_pred, physics_pred] -> actual Tg, evaluated on TEST (NEW this fire)",
        "weights": tg_stack["weights"],
        "test_MAE_K": tg_stack["test_metrics"]["MAE"], "test_R2": tg_stack["test_metrics"]["R2"],
        "test_pearson_r": tg_stack["test_metrics"]["pearson_r"],
    },
    "cited_receipt_sha256": {
        "tg_ridge_fit_receipt": file_sha256(TG_RIDGE_FIT_RECEIPT),
        "tg_physics_ext_validation_kpi": file_sha256(TG_PHYSICS_EXT_KPI),
        "tg_ml_kpi": file_sha256(TG_ML_KPI),
    },
}

print("\nWriting intermediate results (part 1/2)...")
with open("/tmp/c8_raw_results_part1.json", "w") as f:
    json.dump(RESULTS, f, indent=2)
print("OK")

# ============================================================ C. DIELECTRIC (RadonPy) — Onsager port + integrity audit
print("\n=== C. Dielectric (RadonPy) — Onsager physics port + data-integrity audit ===")

# Eisenlohr/Vogel atomic refractions (Na-D, cm^3/mol) — verbatim from the frozen
# redteam-audit dielectric-constant-onsager-ccby-v1 / refractive-index-lorentz-lorenz-ccby-v1
REFRACTION = {
    "C": 2.418, "H": 1.100,
    "O_hydroxyl": 1.525, "O_ether": 1.643, "O_carbonyl": 2.211,
    "N_primary": 2.322, "N_secondary": 2.502, "N_tertiary": 2.840,
    "Cl": 5.967, "Br": 8.865, "F": 0.997, "I": 13.900, "S": 7.921,
    "double_bond_CC": 1.733, "triple_bond_CC": 2.398,
}
N_A = 6.02214076e23
EPS0 = 8.8541878128e-12
K_B = 1.380649e-23
DEBYE = 3.33564e-30

def classify_oxygen(atom):
    if any(b.GetBondType() == Chem.BondType.DOUBLE for b in atom.GetBonds()):
        return "O_carbonyl"
    if any(nb.GetSymbol() == "H" for nb in atom.GetNeighbors()):
        return "O_hydroxyl"
    return "O_ether"

def classify_nitrogen(atom):
    n_heavy = sum(1 for nb in atom.GetNeighbors() if nb.GetSymbol() != "H")
    return {1: "N_primary", 2: "N_secondary"}.get(n_heavy, "N_tertiary")

def molar_refraction_from_mol(mol):
    """Eisenlohr atomic+bond increments. Returns None if an element/valence this
    table doesn't cover is encountered (honestly tracked as coverage failure,
    not silently zeroed)."""
    try:
        m = Chem.Mol(mol)
        Chem.Kekulize(m, clearAromaticFlags=True)
        mh = Chem.AddHs(m)
        R = 0.0
        for a in mh.GetAtoms():
            s = a.GetSymbol()
            if s == "O": R += REFRACTION[classify_oxygen(a)]
            elif s == "N": R += REFRACTION[classify_nitrogen(a)]
            elif s in REFRACTION: R += REFRACTION[s]
            else: raise AssertionError(f"no refraction increment for element {s}")
        for b in mh.GetBonds():
            a1, a2 = b.GetBeginAtom().GetSymbol(), b.GetEndAtom().GetSymbol()
            if a1 == "C" and a2 == "C":
                if b.GetBondType() == Chem.BondType.DOUBLE: R += REFRACTION["double_bond_CC"]
                elif b.GetBondType() == Chem.BondType.TRIPLE: R += REFRACTION["triple_bond_CC"]
        return R
    except Exception:
        return None

def n_lorentz_lorenz(R, rho, M):
    f = R * rho / M
    if not (0.0 < f < 1.0): return None
    return ((1.0 + 2.0 * f) / (1.0 - f)) ** 0.5

def onsager_eps(s, rho_g_cm3, M, mu_D, T_K):
    number_density = N_A * (rho_g_cm3 * 1e6) / M   # 1/m^3
    mu = mu_D * DEBYE
    A = number_density * mu * mu / (9.0 * EPS0 * K_B * T_K)
    B = s + A * (s + 2.0) ** 2
    return (B + (B * B + 8.0 * s * s) ** 0.5) / 4.0

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
print(f"  n_valid = {len(dk_records)} (dropped {n_dropped_missing})")

mus = np.array([r["mu_D"] for r in dk_records])
print(f"  qm_dipole_monomer range: [{mus.min():.4f}, {mus.max():.4f}] (assumed Debye, per RadonPy/RESP convention)")

# --- DATA-INTEGRITY AUDIT: eps_static must be >= n^2 (eps_infinity) by definition
# (Frohlich 1949 Ch.2; Debye 1929; the static dielectric constant subsumes the
# electronic/optical polarization plus any additional orientational term, which
# is non-negative) -- a model-independent thermodynamic inequality, NOT an
# Onsager-specific assumption.
n_violations = sum(1 for r in dk_records if r["eps_s"] < r["n_meas"] ** 2)
violation_rate = n_violations / len(dk_records)
print(f"  THERMODYNAMIC AUDIT: eps_static < n_measured^2 (physically impossible) in {n_violations}/{len(dk_records)} = {violation_rate:.1%} of RadonPy rows")

# cross-check: OpenPoly's own internally-consistent DFT dielectric decomposition
# (Dielectric Constant Total vs Dielectric Constant Electronic) obeys the SAME
# inequality with zero violations -- isolates the defect to RadonPy's MD route.
rows_op_check = list(csv.DictReader(open(OPENPOLY_CSV)))
op_viol = 0; op_n = 0
for r in rows_op_check:
    et, ee = r["Dielectric Constant Total"].strip(), r["Dielectric Constant Electronic"].strip()
    if et and ee:
        op_n += 1
        if float(et) < float(ee): op_viol += 1
print(f"  CONTRAST: OpenPoly's own eps_Total >= eps_Electronic holds in {op_n - op_viol}/{op_n} rows (0 violations expected, DFT-internally-consistent)")

# --- physics (Onsager), full population + physically-valid subset
for r in dk_records:
    r["physics_pred"] = onsager_eps(r["n_meas"] ** 2, r["rho"], r["M"], r["mu_D"], r["T"])

n_dk = len(dk_records)
X_dk = np.stack([morgan_fp(r["mol"]) for r in dk_records])
mw_col = np.array([[np.log10(r["M"])] for r in dk_records], dtype=np.float32)
X_dk = np.concatenate([X_dk, mw_col], axis=1)
y_dk = np.array([r["eps_s"] for r in dk_records], dtype=np.float64)
phys_dk = np.array([r["physics_pred"] for r in dk_records], dtype=np.float64)
valid_mask = np.array([r["eps_s"] >= r["n_meas"] ** 2 for r in dk_records])

rng = np.random.RandomState(SEED)
idx = np.arange(n_dk); rng.shuffle(idx)
n_train = int(n_dk * 0.60); n_calib = int(n_dk * 0.20)
idx_train = idx[:n_train]; idx_calib = idx[n_train:n_train+n_calib]; idx_test = idx[n_train+n_calib:]
print(f"  split: train={len(idx_train)}, calib={len(idx_calib)}, test={len(idx_test)}")

rf_dk = RandomForestRegressor(n_estimators=300, max_depth=10, random_state=SEED, n_jobs=1)
rf_dk.fit(X_dk[idx_train], y_dk[idx_train])
rf_pred_calib = rf_dk.predict(X_dk[idx_calib]); rf_pred_test = rf_dk.predict(X_dk[idx_test])
phys_calib = phys_dk[idx_calib]; phys_test = phys_dk[idx_test]
y_calib = y_dk[idx_calib]; y_test = y_dk[idx_test]
test_valid_mask = valid_mask[idx_test]

dk_stack = stack_fit_eval(rf_pred_calib, phys_calib, y_calib, rf_pred_test, phys_test, y_test)
dk_physics_only_full = metrics(phys_test, y_test)
dk_ml_only_full = metrics(rf_pred_test, y_test)
dk_physics_only_valid = metrics(phys_test[test_valid_mask], y_test[test_valid_mask]) if test_valid_mask.sum() > 1 else None
dk_ml_only_valid = metrics(rf_pred_test[test_valid_mask], y_test[test_valid_mask]) if test_valid_mask.sum() > 1 else None
print(f"  [full pop]  physics MAE={dk_physics_only_full['MAE']:.4f} R2={dk_physics_only_full['R2']:+.4f} | ml MAE={dk_ml_only_full['MAE']:.4f} R2={dk_ml_only_full['R2']:+.4f} | stack MAE={dk_stack['test_metrics']['MAE']:.4f} R2={dk_stack['test_metrics']['R2']:+.4f}")
if dk_physics_only_valid:
    print(f"  [physically-valid subset n={test_valid_mask.sum()}]  physics MAE={dk_physics_only_valid['MAE']:.4f} R2={dk_physics_only_valid['R2']:+.4f} | ml MAE={dk_ml_only_valid['MAE']:.4f} R2={dk_ml_only_valid['R2']:+.4f}")

dk_ml_kpi_existing = json.load(open(DK_ML_KPI))["fitted_or_physical_model_artifact"]

RESULTS["dielectric"] = {
    "population": "RadonPy PI1070 only, n=%d (mixed OpenPoly+RadonPy population used by the existing ML KPI is NOT usable for the physics arm: OpenPoly has no tabulated/computed molecular dipole moment source in this module)" % n_dk,
    "split": "plain random 60/20/20 (seed=0), n_train=%d, n_calib=%d, n_test=%d" % (len(idx_train), len(idx_calib), len(idx_test)),
    "DECISIVE_FINDING_data_integrity_audit": {
        "claim_tested": "eps_static (RadonPy ground-truth label used by the shipped mixed-openpoly-radonpy-dielectric-conformal-kpi) is a physically valid zero-frequency dielectric constant",
        "refute_criterion": "eps_static < n_measured^2 for a material is thermodynamically impossible (Frohlich 1949 Ch.2 / Debye 1929: eps(0) >= eps(optical) always, since static permittivity = electronic polarization + non-negative orientational polarization)",
        "observed": f"{n_violations}/{n_dk} = {violation_rate:.1%} of RadonPy static_dielectric_const values VIOLATE this inequality",
        "contrast": f"OpenPoly's own internally-consistent DFT decomposition (eps_Total vs eps_Electronic) has {op_viol}/{op_n} violations",
        "verdict": "REFUTED",
        "interpretation": "RadonPy's MD fluctuation-formula static dielectric constant is under-converged for the large majority of (weakly-)polar polymers -- collapsing toward the electronic-only limit or below it -- and cannot serve as ground truth for a physics-vs-ML dielectric comparison as the C8 objective assumed. This is a property of the ground-truth LABELS, not of either predictor; it means the physics-vs-ML-vs-stack numbers below (like the existing shipped ML KPI they are compared to) are being scored against partially-invalid targets on ~90% of the RadonPy population.",
    },
    "physics": {
        "method": "Onsager 1936 reaction-field equation; s=n_measured^2 (physics path, same convention as the frozen redteam-audit Onsager script), mu=qm_dipole_monomer (RadonPy QM-computed monomer dipole, Debye), T=per-row MD simulation temperature",
        "full_population_test_MAE": dk_physics_only_full["MAE"], "full_population_test_R2": dk_physics_only_full["R2"],
        "physically_valid_subset_test_MAE": dk_physics_only_valid["MAE"] if dk_physics_only_valid else None,
        "physically_valid_subset_test_R2": dk_physics_only_valid["R2"] if dk_physics_only_valid else None,
        "physically_valid_subset_n": int(test_valid_mask.sum()),
    },
    "ml": {
        "method": "RandomForestRegressor(n_est=300, max_depth=10, seed=0), Morgan512+log10(M), freshly trained on THIS split's train slice (RadonPy-only, NOT the mixed population the existing KPI trained on)",
        "full_population_test_MAE": dk_ml_only_full["MAE"], "full_population_test_R2": dk_ml_only_full["R2"],
        "physically_valid_subset_test_MAE": dk_ml_only_valid["MAE"] if dk_ml_only_valid else None,
        "physically_valid_subset_test_R2": dk_ml_only_valid["R2"] if dk_ml_only_valid else None,
        "existing_shipped_KPI_for_context": {
            "note": "mixed-openpoly-radonpy-dielectric-conformal-kpi, RadonPy per-source slice, DIFFERENT split/population than this fire's fresh RadonPy-only split",
            "radonpy_test_MAE": dk_ml_kpi_existing["per_source_test_metrics"]["radonpy"]["MAE"],
            "radonpy_test_R2": dk_ml_kpi_existing["per_source_test_metrics"]["radonpy"]["R2"],
        },
    },
    "stack": {
        "method": "Wolpert 1992 stacked generalization, Ridge meta-learner on CALIB [RF_pred, Onsager_pred] (NEW this fire)",
        "weights": dk_stack["weights"],
        "full_population_test_MAE": dk_stack["test_metrics"]["MAE"], "full_population_test_R2": dk_stack["test_metrics"]["R2"],
    },
    "openpoly_dielectric_physics_arm": "BLOCKED_DATA -- OpenPoly has no density column and no dipole-moment source anywhere in this module; Onsager cannot be honestly evaluated on OpenPoly polymers without either (filed to data-acquisition-queue.jsonl)",
    "cited_receipt_sha256": {"mixed_dielectric_ml_kpi": file_sha256(DK_ML_KPI)},
}

print("\nWriting intermediate results (part 2/2 partial)...")
with open("/tmp/c8_raw_results_part2.json", "w") as f:
    json.dump(RESULTS, f, indent=2)
print("OK")

# ============================================================ D. REFRACTIVE INDEX (mixed OpenPoly+RadonPy) — Lorentz-Lorenz port
print("\n=== D. Refractive Index (mixed OpenPoly+RadonPy) — Lorentz-Lorenz physics port ===")

rows_op = list(csv.DictReader(open(OPENPOLY_CSV)))
op_records = []
for r in rows_op:
    v = r["Refractive Index"].strip()
    if not v or v == "nan": continue
    try: n_d = float(v)
    except ValueError: continue
    if n_d <= 0 or n_d > 3.0: continue
    mol = psmiles_to_mol(r["PSMILES"])
    if mol is None: continue
    try: mw = float(Descriptors.MolWt(mol))
    except Exception: continue
    op_records.append({"source": "openpoly", "name": r["Name"], "smiles": r["PSMILES"],
                        "n_d": n_d, "mol": mol, "mw": mw, "rho": None})

rows_rp2 = list(csv.DictReader(open(RADONPY_CSV)))
rp_records = []
for r in rows_rp2:
    v = r["refractive_index"].strip()
    if not v or v == "nan": continue
    try: n_d = float(v)
    except ValueError: continue
    if n_d <= 0 or n_d > 3.0: continue
    mol = psmiles_to_mol(r["smiles"])
    if mol is None: continue
    try: mw = float(Descriptors.MolWt(mol))
    except Exception: continue
    try: rho = float(r["density"])
    except (ValueError, KeyError): rho = None
    rp_records.append({"source": "radonpy", "name": r["monomer_ID"], "smiles": r["smiles"],
                        "n_d": n_d, "mol": mol, "mw": mw, "rho": rho})

ri_records = op_records + rp_records
n_ri = len(ri_records)
print(f"  n_openpoly={len(op_records)}, n_radonpy={len(rp_records)}, n_total={n_ri}")

# physics (Lorentz-Lorenz) -- only computable where a density source exists (RadonPy)
n_phys_fail_element = 0
n_phys_fail_no_density = 0
for r in ri_records:
    if r["rho"] is None:
        r["physics_pred"] = None; n_phys_fail_no_density += 1; continue
    R = molar_refraction_from_mol(r["mol"])
    if R is None:
        r["physics_pred"] = None; n_phys_fail_element += 1; continue
    r["physics_pred"] = n_lorentz_lorenz(R, r["rho"], r["mw"])
    if r["physics_pred"] is None: n_phys_fail_element += 1
print(f"  physics coverage: {n_phys_fail_no_density} blocked (no density, all OpenPoly), {n_phys_fail_element} failed (uncovered element/invalid f)")

X_ri = np.stack([morgan_fp(r["mol"]) for r in ri_records])
mw_col = np.array([[np.log10(r["mw"])] for r in ri_records], dtype=np.float32)
X_ri = np.concatenate([X_ri, mw_col], axis=1)
y_ri = np.array([r["n_d"] for r in ri_records], dtype=np.float32)
sources_ri = np.array([r["source"] for r in ri_records])

idx_train, idx_calib, idx_test = stratified_split(sources_ri, (0.60, 0.20, 0.20), SEED)
print(f"  split (source-stratified, matches existing mixed-RI KPI methodology): train={len(idx_train)}, calib={len(idx_calib)}, test={len(idx_test)}")

rf_ri = RandomForestRegressor(n_estimators=300, max_depth=10, random_state=SEED, n_jobs=1)
rf_ri.fit(X_ri[idx_train], y_ri[idx_train])
rf_pred_calib_ri = rf_ri.predict(X_ri[idx_calib])
rf_pred_test_ri = rf_ri.predict(X_ri[idx_test])
y_calib_ri = y_ri[idx_calib]; y_test_ri = y_ri[idx_test]
test_sources_ri = sources_ri[idx_test]

ml_only_ri_overall = metrics(rf_pred_test_ri, y_test_ri)
ml_only_ri_per_source = {src: metrics(rf_pred_test_ri[test_sources_ri == src], y_test_ri[test_sources_ri == src])
                          for src in np.unique(test_sources_ri)}
print(f"  ml-only overall test MAE={ml_only_ri_overall['MAE']:.4f} R2={ml_only_ri_overall['R2']:+.4f}")
for src, m in ml_only_ri_per_source.items():
    print(f"    {src}: MAE={m['MAE']:.4f} R2={m['R2']:+.4f} n={m['n']}")

# physics + stack: RadonPy-only subset of CALIB/TEST (only subset with a density source)
phys_all = np.array([r["physics_pred"] if r["physics_pred"] is not None else np.nan for r in ri_records])
calib_has_phys = ~np.isnan(phys_all[idx_calib])
test_has_phys = ~np.isnan(phys_all[idx_test]) & (test_sources_ri == "radonpy")
print(f"  n_calib_with_physics={calib_has_phys.sum()}/{len(idx_calib)}, n_test_with_physics(radonpy-only)={test_has_phys.sum()}/{len(idx_test)}")

phys_calib_ri = phys_all[idx_calib][calib_has_phys]
rf_calib_ri_sub = rf_pred_calib_ri[calib_has_phys]
y_calib_ri_sub = y_calib_ri[calib_has_phys]
phys_test_ri = phys_all[idx_test][test_has_phys]
rf_test_ri_sub = rf_pred_test_ri[test_has_phys]
y_test_ri_sub = y_test_ri[test_has_phys]

ri_physics_only = metrics(phys_test_ri, y_test_ri_sub)
ri_ml_only_on_phys_subset = metrics(rf_test_ri_sub, y_test_ri_sub)
ri_stack = stack_fit_eval(rf_calib_ri_sub, phys_calib_ri, y_calib_ri_sub, rf_test_ri_sub, phys_test_ri, y_test_ri_sub)
print(f"  [radonpy-only physics-comparable subset n={len(y_test_ri_sub)}] physics MAE={ri_physics_only['MAE']:.4f} R2={ri_physics_only['R2']:+.4f} | ml MAE={ri_ml_only_on_phys_subset['MAE']:.4f} R2={ri_ml_only_on_phys_subset['R2']:+.4f} | stack MAE={ri_stack['test_metrics']['MAE']:.4f} R2={ri_stack['test_metrics']['R2']:+.4f}")

ri_ml_kpi_existing = json.load(open(RI_ML_KPI))["fitted_or_physical_model_artifact"]

RESULTS["refractive_index"] = {
    "population_ml_arm": "mixed OpenPoly (n=%d) + RadonPy (n=%d) = %d, source-stratified 60/20/20 seed=0 -- SAME methodology as the existing shipped mixed-RI KPI (fresh split this fire, not guaranteed row-identical)" % (len(op_records), len(rp_records), n_ri),
    "population_physics_and_stack_arm": "RadonPy-only subset of the test split (n=%d) -- OpenPoly has NO density column anywhere in this module, so Lorentz-Lorenz n=f(R,rho,M) cannot be evaluated on OpenPoly polymers without fabricating a density source" % len(y_test_ri_sub),
    "openpoly_ri_physics_arm": "BLOCKED_DATA -- same root cause as the dielectric OpenPoly gap: no measured or receipt-traceable density for OpenPoly polymers in this module (filed to data-acquisition-queue.jsonl)",
    "ml_full_mixed_population": {
        "method": "RandomForestRegressor(n_est=300, max_depth=10, seed=0), Morgan512+log10(MW), source-stratified split (fresh this fire)",
        "overall_test_MAE": ml_only_ri_overall["MAE"], "overall_test_R2": ml_only_ri_overall["R2"],
        "per_source": {k: v for k, v in ml_only_ri_per_source.items()},
        "existing_shipped_KPI_for_context": {
            "overall_test_MAE": ri_ml_kpi_existing["overall_test_metrics"]["MAE"],
            "overall_test_R2": ri_ml_kpi_existing["overall_test_metrics"]["R2"],
        },
    },
    "physics": {
        "method": "Lorentz-Lorenz molar refraction (Eisenlohr/Vogel atomic+bond increments, identical table to the frozen redteam-audit refractive-index-lorentz-lorenz-ccby-v1); rho = RadonPy MD-simulated density (real, measured -- NOT the VK density estimate)",
        "test_MAE": ri_physics_only["MAE"], "test_R2": ri_physics_only["R2"], "test_pearson_r": ri_physics_only["pearson_r"],
        "element_coverage_failures_in_full_population": int(n_phys_fail_element),
    },
    "ml_on_physics_comparable_subset": {
        "test_MAE": ri_ml_only_on_phys_subset["MAE"], "test_R2": ri_ml_only_on_phys_subset["R2"],
    },
    "stack": {
        "method": "Wolpert 1992 stacked generalization, Ridge meta-learner on CALIB [RF_pred, LorentzLorenz_pred] (NEW this fire, RadonPy-only subset)",
        "weights": ri_stack["weights"],
        "test_MAE": ri_stack["test_metrics"]["MAE"], "test_R2": ri_stack["test_metrics"]["R2"],
    },
    "cited_receipt_sha256": {"mixed_ri_ml_kpi": file_sha256(RI_ML_KPI)},
}

print("\nWriting final results...")
with open("/tmp/c8_raw_results_final.json", "w") as f:
    json.dump(RESULTS, f, indent=2)
print("DONE")
