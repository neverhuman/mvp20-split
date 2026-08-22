#!/usr/bin/env python3
"""
U-VKAD (ROTATION, molecule-property): applicability-domain / group-scope audit
of external-validation-polyuniverse-ridge-on-openpoly-tg-kpi.v1.json's headline
"Push #20 Ridge MAE=70.42K BEATS published Van Krevelen 1990 baseline MAE=91.34K
on 442 independent OpenPoly experimental Tg polymers" claim.

Never before ledger-attacked (STANDS, unqualified, per RETRACTION-INDEX.md line 40).

This claim applies the FULL unscoped 24-group Ridge Y_gi coefficient table to
442 out-of-distribution OpenPoly polymers. W-PROP1 (2026-08-05, SURVIVED) already
established -- from the model's OWN stored per-group table, no new data -- that
only 15/24 groups have training support above the data-derived sign-admissibility
threshold (n_train>=125); the other 9 (nitrile, F, vinyl_CH2, ester, Br, sulfone,
Cl, sulfide, Si_O) include two sign-REVERSED coefficients (nitrile, vinyl_CH2)
and are explicitly NOT asserted as structurally trustworthy.

This external-validation KPI was published AFTER W8 (REFUTED, 2026-08-03) and
never applies the W-PROP1 scoping. Question: does the "beats published baseline"
finding survive when restricted to the chemistry the model itself claims to
trust (in-scope-only groups), or is the advantage propped up by chemistry that
touches the already-flagged-untrustworthy groups?

Method:
 1. Independently featurize the 442 OpenPoly test polymers (PSMILES column,
    feedback/v1/external_data/openpoly_benchmark/raw/final_polymer_properties_
    fromliterature.csv, rows with valid Tg (K)) into the same 24 Van Krevelen
    groups using self-authored RDKit SMARTS (Van Krevelen 1990 Ch.3 / Bicerano
    2002 Ch.3 group-additive definitions) -- an INDEPENDENT re-derivation, not
    a re-use of any original (undisclosed, not in-tree) featurizer.
 2. Apply the ALREADY-SIGNED, hash-pinned fitted_Ygi_comparison (Ridge) and
    Y_published_K_g_per_mol (published Van Krevelen 1990 Table 6.6) coefficient
    tables verbatim: Tg_pred = sum(Y_gi * n_i) / M_repeat_unit (Van Krevelen
    1990 Eq. 6, additive molar-function group contribution).
 3. Sanity-gate: compare my independently-derived population MAE against the
    KPI's own reported push_20_ridge_on_openpoly.MAE_K=70.4175 /
    van_krevelen_published_on_openpoly MAE to confirm the re-derivation is in
    the right neighborhood (methodology check, not the falsifying criterion).
 4. THE FALSIFYING CHECK: partition the population into
      A = in-scope-only  (zero count in all 9 W-PROP1-excluded groups)
      B = touches-excluded-group (nonzero count in >=1 excluded group)
    Recompute MAE_ridge and MAE_published on A alone using the SAME already-
    fitted coefficients (no re-fit).

PRE-REGISTERED REFUTE CRITERION (fixed before this script inspected results):
  If, on partition A with n>=30, MAE_ridge does NOT beat MAE_published
  (i.e. MAE_reduction = MAE_published - MAE_ridge <= 0), the external-
  validation headline ("Ridge Y_gi DO generalize beyond MD-simulated training
  distribution", "beats published baseline by 22.9%") is REFUTED as a general
  claim -- it would depend on chemistry the model's own admissibility scoping
  has already flagged untrustworthy.
SURVIVAL requires: Ridge beats published baseline on BOTH the full population
  AND partition A, with n_A>=30.
"""
import base64
import csv
import hashlib
import json
import random
import statistics
import sys
from pathlib import Path

from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-molecule-property"
CSV_PATH = ROOT / "feedback/v1/external_data/openpoly_benchmark/raw/final_polymer_properties_fromliterature.csv"
RIDGE_KPI_PATH = MOD / "evidence/phase0/kpis/van-krevelen-ridge-fit-on-1000-polyuniverse-polymers-kpi.v1.json"
EXTVAL_KPI_PATH = MOD / "evidence/phase0/kpis/external-validation-polyuniverse-ridge-on-openpoly-tg-kpi.v1.json"
WPROP1_PATH = MOD / "evidence/phase0/repairs/W-PROP1/done/van-krevelen-ridge-scope-limited-superseding-kpi.v1.dsse.json"

random.seed(0)


def sha(b):
    return hashlib.sha256(b).hexdigest()


# ---------------------------------------------------------------------------
# Load already-signed inputs (hash-pinned, no mutation)
# ---------------------------------------------------------------------------
ridge_kpi_bytes = RIDGE_KPI_PATH.read_bytes()
ridge_kpi = json.loads(ridge_kpi_bytes)
ridge_rows = ridge_kpi["fitted_or_physical_model_artifact"]["fitted_Ygi_comparison"]
assert len(ridge_rows) == 24
Y_fitted = {r["group"]: r["Y_fitted_K_g_per_mol"] for r in ridge_rows}
Y_published = {r["group"]: r["Y_published_K_g_per_mol"] for r in ridge_rows}

extval_kpi_bytes = EXTVAL_KPI_PATH.read_bytes()
extval_kpi = json.loads(extval_kpi_bytes)
reported = extval_kpi["fitted_or_physical_model_artifact"]

wprop1_bytes = WPROP1_PATH.read_bytes()
wprop1 = json.loads(wprop1_bytes)
wprop1_payload = json.loads(base64.standard_b64decode(wprop1["signature"]["payload"]))
IN_SCOPE_GROUPS = set(wprop1_payload["claim_locks"]["in_scope_groups_named"])
EXCLUDED_GROUPS = set(wprop1_payload["claim_locks"]["excluded_groups_named"])
assert len(IN_SCOPE_GROUPS) == 15 and len(EXCLUDED_GROUPS) == 9
assert IN_SCOPE_GROUPS | EXCLUDED_GROUPS == set(Y_fitted.keys())

csv_bytes = CSV_PATH.read_bytes()
csv_sha256 = sha(csv_bytes)

# ---------------------------------------------------------------------------
# Independent 24-group SMARTS featurizer (Van Krevelen 1990 Ch.3 / Bicerano
# 2002 Ch.3 group-additive definitions). Self-authored -- this module carries
# no in-tree per-molecule featurizer for this KPI to reuse verbatim.
# ---------------------------------------------------------------------------
GROUP_SMARTS = {
    "CH3":            "[CH3;!$([CH3][#7,#8,#16])]",
    "CH2":            "[CH2;!R;!$([CH2]=*)]",
    "CH":             "[CH1;!R;!$([CH1]=*);!$([CH1][#7,#8])]",
    "C_quat":         "[CX4H0;!R]",
    "aromatic_C_H":   "[cH]",
    "aromatic_C_sub": "[c;!H0;!cH]",
    "ether_O":        "[OX2;!$([OX2H]);!$([OX2][CX3]=[OX1])]([#6])[#6]",
    "hydroxyl":       "[OX2H1]",
    "carbonyl":       "[CX3;$([CX3]=[OX1]);!$([CX3](=[OX1])[OX2]);!$([CX3](=[OX1])[NX3])]=[OX1]",
    "ester":          "[CX3](=[OX1])[OX2][#6]",
    "amide":          "[CX3](=[OX1])[NX3]",
    "primary_amine":  "[NX3H2;!$([NX3][CX3]=[OX1])]",
    "secondary_amine": "[NX3H1;!$([NX3][CX3]=[OX1]);!R]([#6])[#6]",
    "tertiary_amine": "[NX3H0;!$([NX3][CX3]=[OX1]);!R]([#6])([#6])[#6]",
    "epoxide":        "[C;R1]1[O;R1][C;R1]1",
    "vinyl_CH":       "[CH1]=[CH1]",
    "vinyl_CH2":      "[CH2]=[CH1,CH0]",
    "nitrile":        "[CX2]#[NX1]",
    "F":              "[F]",
    "Cl":             "[Cl]",
    "Br":             "[Br]",
    "sulfide":        "[#6][SX2][#6]",
    "sulfone":        "[SX4](=[OX1])(=[OX1])",
    "Si_O":           "[Si][OX2]",
}
GROUP_MOL = {g: Chem.MolFromSmarts(s) for g, s in GROUP_SMARTS.items()}
for g, m in GROUP_MOL.items():
    assert m is not None, f"bad SMARTS for {g}"
assert set(GROUP_MOL.keys()) == set(Y_fitted.keys()), "group vocabulary mismatch vs ridge-fit KPI"


def repeat_unit_mw(smiles):
    """Cap the two polymer attachment points ([*]) with H to approximate the
    repeat-unit molar mass, consistent with Van Krevelen's per-repeat-unit
    M0 convention for Tg = sum(Y_gi*n_i)/M0."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    rw = Chem.RWMol(mol)
    for atom in rw.GetAtoms():
        if atom.GetAtomicNum() == 0:
            atom.SetAtomicNum(1)
    try:
        m2 = rw.GetMol()
        Chem.SanitizeMol(m2)
    except Exception:
        return None
    return Descriptors.MolWt(m2)


def group_vector(smiles):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    counts = {}
    for g, patt in GROUP_MOL.items():
        matches = mol.GetSubstructMatches(patt)
        counts[g] = len(matches)
    return counts


def predict_tg(counts, mw, coeff_table):
    if mw is None or mw <= 0:
        return None
    num = sum(coeff_table.get(g, 0.0) * n for g, n in counts.items())
    return num / mw


# ---------------------------------------------------------------------------
# Load + filter OpenPoly rows: valid Tg, valid PSMILES
# ---------------------------------------------------------------------------
records = []
with open(CSV_PATH, newline="", encoding="utf-8") as fh:
    reader = csv.DictReader(fh)
    for i, row in enumerate(reader):
        tg = row.get("Tg (K)", "").strip()
        smi = row.get("PSMILES", "").strip()
        if tg == "" or smi == "":
            continue
        try:
            tg_val = float(tg)
        except ValueError:
            continue
        records.append({"row_idx": i, "name": row.get("Name"), "psmiles": smi, "Tg_K": tg_val})

n_valid_tg_rows = len(records)

parsed = []
n_parse_fail = 0
for rec in records:
    counts = group_vector(rec["psmiles"])
    mw = repeat_unit_mw(rec["psmiles"])
    if counts is None or mw is None:
        n_parse_fail += 1
        continue
    rec2 = dict(rec)
    rec2["counts"] = counts
    rec2["mw"] = mw
    rec2["touches_excluded"] = any(counts[g] > 0 for g in EXCLUDED_GROUPS)
    rec2["n_groups_total_count"] = sum(counts.values())
    parsed.append(rec2)

n_parsed = len(parsed)

# ---------------------------------------------------------------------------
# Step 3: independent MAE reproduction (sanity gate, full population)
# ---------------------------------------------------------------------------
full_ridge_err = []
full_pub_err = []
for r in parsed:
    p_ridge = predict_tg(r["counts"], r["mw"], Y_fitted)
    p_pub = predict_tg(r["counts"], r["mw"], Y_published)
    r["pred_ridge"] = p_ridge
    r["pred_pub"] = p_pub
    if p_ridge is not None:
        full_ridge_err.append(abs(p_ridge - r["Tg_K"]))
    if p_pub is not None:
        full_pub_err.append(abs(p_pub - r["Tg_K"]))

my_mae_ridge_full = statistics.mean(full_ridge_err) if full_ridge_err else None
my_mae_pub_full = statistics.mean(full_pub_err) if full_pub_err else None

reported_mae_ridge = reported["push_20_ridge_on_openpoly"]["MAE_K"]
reported_mae_pub = reported["van_krevelen_published_on_openpoly"]["MAE_K"] if "van_krevelen_published_on_openpoly" in reported else None

# ---------------------------------------------------------------------------
# Step 4: THE FALSIFYING CHECK -- partition A (in-scope-only) vs B (touches-excluded)
# ---------------------------------------------------------------------------
partition_A = [r for r in parsed if not r["touches_excluded"]]
partition_B = [r for r in parsed if r["touches_excluded"]]

def mae_on(rows, key):
    errs = [abs(r[key] - r["Tg_K"]) for r in rows if r[key] is not None]
    return (statistics.mean(errs) if errs else None), len(errs)

mae_ridge_A, n_A = mae_on(partition_A, "pred_ridge")
mae_pub_A, n_A2 = mae_on(partition_A, "pred_pub")
mae_ridge_B, n_B = mae_on(partition_B, "pred_ridge")
mae_pub_B, n_B2 = mae_on(partition_B, "pred_pub")
mae_ridge_full2, n_full = mae_on(parsed, "pred_ridge")
mae_pub_full2, n_full2 = mae_on(parsed, "pred_pub")

reduction_full = (mae_pub_full2 - mae_ridge_full2) if (mae_pub_full2 is not None and mae_ridge_full2 is not None) else None
reduction_A = (mae_pub_A - mae_ridge_A) if (mae_pub_A is not None and mae_ridge_A is not None) else None

REFUTE_MIN_N = 30
refuted = (n_A >= REFUTE_MIN_N) and (reduction_A is not None) and (reduction_A <= 0)
survived = not refuted

# ---------------------------------------------------------------------------
# Positive control (only meaningful if SURVIVED): construct a deliberately
# contaminated copy of partition A by injecting a random sample of partition-B
# rows (known to carry excluded-group, sign-flipped-coefficient chemistry)
# into it, and confirm the beats-baseline margin degrades on the planted-
# defect copy but not on the real clean partition A.
# ---------------------------------------------------------------------------
positive_control = None
if survived and n_B >= 10:
    k = max(5, min(20, n_B // 2, len(partition_A) // 2))
    contaminated = list(partition_A) + random.sample(partition_B, k)
    mae_ridge_contam, n_contam = mae_on(contaminated, "pred_ridge")
    mae_pub_contam, _ = mae_on(contaminated, "pred_pub")
    reduction_contam = (mae_pub_contam - mae_ridge_contam) if (mae_pub_contam is not None and mae_ridge_contam is not None) else None
    detected = (reduction_contam is not None and reduction_A is not None and reduction_contam < reduction_A)
    positive_control = {
        "planted_defect": f"injected {k} partition-B (touches-excluded-group) rows into the clean partition-A (in-scope-only) sample",
        "how_planted": f"random.sample(partition_B, k={k}) with seed=0, concatenated onto partition_A ({len(partition_A)} rows) to form a {len(contaminated)}-row contaminated copy",
        "detected": bool(detected),
        "evidence": {
            "clean_partition_A_MAE_reduction_K": reduction_A,
            "contaminated_copy_MAE_reduction_K": reduction_contam,
            "clean_n": n_A,
            "contaminated_n": n_contam,
            "margin_degraded": bool(detected),
        },
    }

result = {
    "attack": "U-VKAD_applicability_domain_group_scope_audit_external_validation_ridge_openpoly_tg",
    "claim_under_attack": {
        "receipt": "amphora-molecule-property/evidence/phase0/kpis/external-validation-polyuniverse-ridge-on-openpoly-tg-kpi.v1.json",
        "kpi_sha256": sha(extval_kpi_bytes),
        "reported_push_20_ridge_MAE_K": reported_mae_ridge,
        "reported_van_krevelen_published_MAE_K": reported["van_krevelen_published_on_openpoly"],
        "reported_MAE_reduction_K": reported["cross_dataset_comparison"]["MAE_reduction_ridge_over_published_K"],
    },
    "inputs": {
        "openpoly_csv_path": "feedback/v1/external_data/openpoly_benchmark/raw/final_polymer_properties_fromliterature.csv",
        "openpoly_csv_sha256": csv_sha256,
        "ridge_fit_kpi_sha256": sha(ridge_kpi_bytes),
        "wprop1_receipt_sha256": sha(wprop1_bytes),
        "in_scope_groups_15": sorted(IN_SCOPE_GROUPS),
        "excluded_groups_9": sorted(EXCLUDED_GROUPS),
    },
    "row_filter": {
        "n_csv_rows_total": None,  # filled below
        "n_rows_with_valid_Tg": n_valid_tg_rows,
        "n_parse_success": n_parsed,
        "n_parse_fail": n_parse_fail,
        "reported_kpi_n": reported["push_20_ridge_on_openpoly"]["n"],
    },
    "sanity_gate_full_population_reproduction": {
        "my_independent_mae_ridge_K": my_mae_ridge_full,
        "reported_mae_ridge_K": reported_mae_ridge,
        "my_independent_mae_published_K": my_mae_pub_full,
        "reported_mae_published_K": reported_mae_pub,
        "note": "Independent re-derivation using self-authored SMARTS group counter; not expected to match to machine precision (different featurizer implementation from the undisclosed original), used only to confirm same order of magnitude / same qualitative conclusion before trusting the partitioned check below.",
    },
    "falsifying_check": {
        "pre_registered_refute_criterion": f"On partition A (in-scope-only, zero count in all 9 W-PROP1-excluded groups) with n>=({REFUTE_MIN_N}), MAE_ridge does NOT beat MAE_published (MAE_reduction<=0) => REFUTES the external-validation 'beats published baseline' headline as a general claim.",
        "partition_A_in_scope_only": {"n": n_A, "mae_ridge_K": mae_ridge_A, "mae_published_K": mae_pub_A, "MAE_reduction_K": reduction_A},
        "partition_B_touches_excluded_group": {"n": n_B, "mae_ridge_K": mae_ridge_B, "mae_published_K": mae_pub_B, "MAE_reduction_K": (mae_pub_B - mae_ridge_B) if (mae_pub_B is not None and mae_ridge_B is not None) else None},
        "full_population_my_repro": {"n": n_full, "mae_ridge_K": mae_ridge_full2, "mae_published_K": mae_pub_full2, "MAE_reduction_K": reduction_full},
        "refuted": refuted,
    },
    "positive_control": positive_control,
}

print(json.dumps(result, indent=2, default=str))
Path("/tmp/vk_ad_result.json").write_text(json.dumps(result, indent=2, default=str))
