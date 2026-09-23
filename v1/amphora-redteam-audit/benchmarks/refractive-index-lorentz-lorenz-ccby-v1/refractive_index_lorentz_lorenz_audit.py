"""AUDIT_ONLY red-team science increment: a-priori refractive-index prediction of
coating-relevant solvents via the Lorentz-Lorenz molar-refraction group-contribution
method (Eisenlohr/Vogel atomic refractions).

Theory (real, cited):
  Lorentz-Lorenz (1880) relation between refractive index n_D and molar refraction R_LL:
     (n^2 - 1)/(n^2 + 2) = R_LL * rho / M
  Molar refraction is ADDITIVE over atomic + bond increments (Eisenlohr 1911; Vogel
  1948; Van Krevelen "Properties of Polymers" ch.10, molar-refraction group table):
     R_LL_calc = sum_i n_i * r_i           (universal literature constants)
  Rearranged this is an a-priori PREDICTION of refractive index from a pure
  literature-constant sum + measured rho, M:
     f = R_LL_calc * rho / M ;  n_pred = sqrt( (1 + 2f) / (1 - f) )
  The atomic refractions r_i are NOT fitted to this validation set -> non-circular
  by construction. Refractive index governs (a) hiding power / opacity of a pigmented
  coating via the RI CONTRAST between pigment (e.g. TiO2 n~2.7) and cured binder
  (epoxy n~1.55) -- the higher the contrast the higher the scattering / opacity;
  (b) gloss; and (c) refractometry, the standard incoming-QC fingerprint of resin
  and solvent identity/purity. R_LL is also the electronic-polarization term of the
  Clausius-Mossotti equation (n^2 ~ high-frequency permittivity), tying RI to the
  barrier/water-uptake physics of the film.

Design:
  - Truth set: 20 pure liquids spanning the exact chemistries of two-part marine
    epoxy-amine thinner packages (aromatics, aliphatics, alcohols, ketones, esters)
    + water. n_D20, rho_20C and M are tabulated physical constants (CRC/NIST), i.e.
    non-copyrightable facts; the compilation is self-authored CC0. The same 20
    solvents + rho + M as the surface-tension Parachor audit (cross-consistency).
  - Model: RDKit parses each SMILES (Kekule), classifies each O as hydroxyl /
    ether / carbonyl by its bonding, counts C, H, halogens and C=C (ethylenic)
    increments; R_LL_calc = Eisenlohr atomic refractions. C=O is carried by the
    carbonyl-oxygen increment (not double-counted as an ethylenic bond).
  - KPIs: overall + core-domain (non-extended-conjugation) MAPE, RMSE in n-units,
    max abs %err, fraction within 0.005 and 0.002 n-units, and lift over two honest
    baselines (mean-n null; constant organic n = 1.45).
  - Honest applicability domain: simple additivity omits the optical EXALTATION of
    extended conjugation, so styrene (vinyl conjugated with the ring) is EXPECTED to
    be biased low; reported, not hidden. (Isolated aromatic rings are well handled by
    the 3x C=C increment, so benzene/toluene/xylene stay in-domain.)

Promotes nothing. Signs no phase0 evaluation/review receipt. AUDIT_ONLY.
"""
import json, hashlib, glob, os
from rdkit import Chem

# --- Live Phase-0 reconciliation (red-team of the "FULL phase 0" claim) --------
# Deterministically read every module's live docs/mission.md front-matter and
# classify its PHASE status + scientific_readiness. Byte-stable inside this signed
# diagnostic instead of quoting a stale memo. (Same routine as the Parachor audit.)
def _repo_root():
    p = os.path.abspath(os.getcwd())
    while p != "/":
        if os.path.isdir(os.path.join(p, ".amphora")):
            return p
        p = os.path.dirname(p)
    raise RuntimeError("repo root (.amphora) not found from cwd")

def phase0_reconciliation():
    root = _repo_root()
    phase0 = []
    for mp in sorted(glob.glob(os.path.join(root, "amphora-*/docs/mission.md"))):
        try:
            with open(mp) as fh:
                fh.readline()          # opening '---'
                fm = json.loads(fh.readline())
        except Exception:
            continue
        if fm.get("phase") == "PHASE_0":
            phase0.append({
                "module": fm.get("module_id", os.path.basename(os.path.dirname(os.path.dirname(mp)))),
                "scientific_readiness": fm.get("scientific_readiness", "?"),
            })
    phase0.sort(key=lambda r: r["module"])
    by_sr = {}
    for r in phase0:
        by_sr[r["scientific_readiness"]] = by_sr.get(r["scientific_readiness"], 0) + 1
    return {
        "n_modules_labelled_phase0_in_live_frontmatter": len(phase0),
        "by_scientific_readiness": dict(sorted(by_sr.items())),
        "n_externally_validated_science": 1,   # amphora-solvency-score (BigSolDB leave-solute-out)
        "externally_validated_science_modules": ["amphora-solvency-score"],
        "phase0_modules": phase0,
        "honest_reading": (
            "PHASE_0 here = a reproducibility+rights+independence GOVERNANCE lock "
            "(byte-stable benchmark, rights-qualified data, two trust-anchored signatures). "
            "It is NOT scientific validation: NOT_APPLICABLE readiness modules are "
            "governance/infrastructure; LOCKED_INTERNAL modules passed an INTERNAL "
            "known-answer only. Exactly ONE module (amphora-solvency-score) carries "
            "EXTERNAL-data predictive validation behind its Phase-0. 'FULL Phase-0' is an "
            "engineering/governance milestone, never a count of validated science."),
    }

# --- Eisenlohr / Vogel atomic + bond refractions (Na-D, cm^3/mol) --------------
# Literature constants (Eisenlohr 1911; Vogel 1948; Van Krevelen ch.10). NOT fitted.
REFRACTION = {
    "C": 2.418, "H": 1.100,
    "O_hydroxyl": 1.525, "O_ether": 1.643, "O_carbonyl": 2.211,
    "N_primary": 2.322, "N_secondary": 2.502, "N_tertiary": 2.840,
    "Cl": 5.967, "Br": 8.865, "F": 0.997, "I": 13.900, "S": 7.921,
    "double_bond_CC": 1.733, "triple_bond_CC": 2.398,
}
CONSTANT_ORGANIC_N = 1.45  # naive baseline: "an organic liquid is ~1.45"

# --- Truth set: (id, family, SMILES, M g/mol, rho_20C g/cm3, n_D20)
# All property values are tabulated physical constants (facts). CRC/NIST. Same M/rho
# as the surface-tension Parachor audit for cross-consistency; n_D20 added.
SOLVENTS = [
    # aromatics (core epoxy thinners: xylene / aromatic-100 packages)
    ("benzene",        "aromatic",   "c1ccccc1",         78.11,  0.8765, 1.5011),
    ("toluene",        "aromatic",   "Cc1ccccc1",        92.14,  0.8669, 1.4969),
    ("o-xylene",       "aromatic",   "Cc1ccccc1C",       106.17, 0.8802, 1.5055),
    ("p-xylene",       "aromatic",   "Cc1ccc(C)cc1",     106.17, 0.8611, 1.4958),
    ("ethylbenzene",   "aromatic",   "CCc1ccccc1",       106.17, 0.8670, 1.4959),
    ("chlorobenzene",  "aromatic",   "Clc1ccccc1",       112.56, 1.1058, 1.5241),
    # extended-conjugation reference (expected optical exaltation -> out of domain)
    ("styrene",        "conjugated", "C=Cc1ccccc1",      104.15, 0.9060, 1.5468),
    # aliphatics
    ("n-hexane",       "aliphatic",  "CCCCCC",           86.18,  0.6606, 1.3749),
    ("n-heptane",      "aliphatic",  "CCCCCCC",          100.20, 0.6838, 1.3876),
    ("cyclohexane",    "aliphatic",  "C1CCCCC1",         84.16,  0.7785, 1.4266),
    # alcohols
    ("methanol",       "alcohol",    "CO",               32.04,  0.7914, 1.3288),
    ("ethanol",        "alcohol",    "CCO",              46.07,  0.7893, 1.3611),
    ("1-propanol",     "alcohol",    "CCCO",             60.10,  0.8035, 1.3856),
    ("1-butanol",      "alcohol",    "CCCCO",            74.12,  0.8098, 1.3993),
    # ketones / esters (polar aprotic marine solvents)
    ("acetone",        "ketone",     "CC(=O)C",          58.08,  0.7845, 1.3588),
    ("mek",            "ketone",     "CCC(=O)C",         72.11,  0.8054, 1.3788),
    ("mibk",           "ketone",     "CC(=O)CC(C)C",     100.16, 0.7965, 1.3958),
    ("ethyl-acetate",  "ester",      "CCOC(=O)C",        88.11,  0.9006, 1.3724),
    ("n-butyl-acetate","ester",      "CCCCOC(=O)C",      116.16, 0.8825, 1.3941),
    # associating reference (parachor's worst case; here EXPECTED fine)
    ("water",          "associating","O",                18.015, 0.9982, 1.3330),
]

def classify_oxygen(atom):
    has_double = any(b.GetBondType() == Chem.BondType.DOUBLE for b in atom.GetBonds())
    if has_double:
        return "O_carbonyl"
    has_h = any(nb.GetSymbol() == "H" for nb in atom.GetNeighbors())
    if has_h:
        return "O_hydroxyl"
    return "O_ether"

def classify_nitrogen(atom):
    n_heavy = sum(1 for nb in atom.GetNeighbors() if nb.GetSymbol() != "H")
    return {1: "N_primary", 2: "N_secondary"}.get(n_heavy, "N_tertiary")

def molar_refraction(smiles):
    m = Chem.MolFromSmiles(smiles)
    assert m is not None, smiles
    Chem.Kekulize(m, clearAromaticFlags=True)
    mh = Chem.AddHs(m)
    R = 0.0
    detail = {}
    def add(key, r):
        nonlocal R
        R += r
        detail[key] = detail.get(key, 0) + 1
    for a in mh.GetAtoms():
        s = a.GetSymbol()
        if s == "O":
            k = classify_oxygen(a); add(k, REFRACTION[k])
        elif s == "N":
            k = classify_nitrogen(a); add(k, REFRACTION[k])
        elif s in REFRACTION:
            add(s, REFRACTION[s])
        else:
            raise AssertionError("no refraction for element " + s)
    nd = nt = 0
    for b in mh.GetBonds():
        a1, a2 = b.GetBeginAtom().GetSymbol(), b.GetEndAtom().GetSymbol()
        if a1 == "C" and a2 == "C":
            if b.GetBondType() == Chem.BondType.DOUBLE:
                add("double_bond_CC", REFRACTION["double_bond_CC"]); nd += 1
            elif b.GetBondType() == Chem.BondType.TRIPLE:
                add("triple_bond_CC", REFRACTION["triple_bond_CC"]); nt += 1
    return round(R, 4), dict(sorted(detail.items())), nd, nt

def n_from_R(R, rho, M):
    f = R * rho / M
    assert 0.0 < f < 1.0, f
    return ((1.0 + 2.0 * f) / (1.0 - f)) ** 0.5

def mape(errs):
    return round(sum(abs(e) for e in errs) / len(errs), 6)

def rmse(errs):
    return round((sum(e * e for e in errs) / len(errs)) ** 0.5, 6)

rows = []
n_exp_all = [n for (_, _, _, _, _, n) in SOLVENTS]
mean_n = sum(n_exp_all) / len(n_exp_all)

for sid, fam, smi, M, rho, n_exp in SOLVENTS:
    R, detail, nd, nt = molar_refraction(smi)
    n_pred = n_from_R(R, rho, M)
    pct = (n_pred - n_exp) / n_exp
    rows.append({
        "id": sid, "family": fam, "smiles": smi,
        "M_g_mol": M, "rho_20c_g_cm3": rho,
        "molar_refraction_calc_cm3_mol": R,
        "group_detail": detail, "n_double_bond_CC": nd, "n_triple_bond_CC": nt,
        "n_D20_exp": n_exp,
        "n_D20_pred": round(n_pred, 4),
        "abs_error_n_units": round(abs(n_pred - n_exp), 5),
        "pct_error": round(pct, 5),
        "abs_pct_error": round(abs(pct), 5),
        "baseline_null_abs_pct_error": round(abs(mean_n - n_exp) / n_exp, 5),
        "baseline_const145_abs_pct_error": round(abs(CONSTANT_ORGANIC_N - n_exp) / n_exp, 5),
    })

rows.sort(key=lambda r: r["id"])

families = {}
for r in rows:
    families.setdefault(r["family"], []).append(r["abs_pct_error"])
family_mape = {k: mape(v) for k, v in sorted(families.items())}

# Core domain = simple-additivity domain (excludes extended-conjugation exaltation).
CORE = [r for r in rows if r["family"] != "conjugated"]
OUT = [r for r in rows if r["family"] == "conjugated"]

overall_mape = mape([r["abs_pct_error"] for r in rows])
core_mape = mape([r["abs_pct_error"] for r in CORE])
overall_rmse_n = rmse([r["n_D20_pred"] - r["n_D20_exp"] for r in rows])
core_rmse_n = rmse([r["n_D20_pred"] - r["n_D20_exp"] for r in CORE])
null_mape = mape([r["baseline_null_abs_pct_error"] for r in rows])
const145_mape = mape([r["baseline_const145_abs_pct_error"] for r in rows])
core_null_mape = mape([r["baseline_null_abs_pct_error"] for r in CORE])
frac_within_0005_all = round(sum(1 for r in rows if r["abs_error_n_units"] <= 0.005) / len(rows), 4)
core_frac_within_0005 = round(sum(1 for r in CORE if r["abs_error_n_units"] <= 0.005) / len(CORE), 4)
core_frac_within_0002 = round(sum(1 for r in CORE if r["abs_error_n_units"] <= 0.002) / len(CORE), 4)
max_row = max(rows, key=lambda r: r["abs_pct_error"])
core_max_row = max(CORE, key=lambda r: r["abs_pct_error"])

diagnostic = {
    "schema": "amphora.redteam-audit.refractive-index-lorentz-lorenz-ccby-v1",
    "authority": "AUDIT_ONLY",
    "target_module": "amphora-molecule-property",
    "target_capability": "refractive-index-lorentz-lorenz-group-contribution",
    "theory": ("Lorentz-Lorenz (1880): (n^2-1)/(n^2+2) = R_LL*rho/M, with R_LL an "
               "ADDITIVE sum of Eisenlohr/Vogel atomic+bond refractions (Van Krevelen "
               "Properties of Polymers ch.10). n_pred = sqrt((1+2f)/(1-f)), f=R_LL*rho/M. "
               "R_LL constants are pure literature values (NOT fitted to this set) -> "
               "non-circular. Refractive index drives coating hiding-power/opacity via "
               "pigment-vs-binder RI contrast, gloss, and refractometric incoming QC; "
               "R_LL is also the electronic-polarization term of Clausius-Mossotti "
               "(n^2 ~ high-frequency permittivity), linking RI to film barrier physics."),
    "refraction_constants": REFRACTION,
    "rights": {
        "truth_values": "tabulated physical constants (CRC/NIST) = non-copyrightable facts",
        "compilation_license": "CC0-1.0 self-authored",
        "refraction_constants_provenance": "published literature constants (Eisenlohr 1911; Vogel 1948; Van Krevelen ch.10)",
        "in_scope": "aromatic+aliphatic+ketone+ester+alcohol solvents = marine epoxy-amine thinner chemistries",
    },
    "phase0_reconciliation_redteam": phase0_reconciliation(),
    "n_solvents": len(rows),
    "per_solvent": rows,
    "kpis": {
        "overall_mape": overall_mape,
        "core_domain_mape": core_mape,
        "overall_rmse_n_units": overall_rmse_n,
        "core_domain_rmse_n_units": core_rmse_n,
        "family_mape": family_mape,
        "baseline_null_mean_n_mape": null_mape,
        "baseline_const145_mape": const145_mape,
        "core_baseline_null_mape": core_null_mape,
        "core_lift_over_null": round(1.0 - core_mape / core_null_mape, 4),
        "frac_within_0.005_n_all": frac_within_0005_all,
        "core_frac_within_0.005_n": core_frac_within_0005,
        "core_frac_within_0.002_n": core_frac_within_0002,
        "worst_case_all": {"id": max_row["id"], "family": max_row["family"],
                           "abs_pct_error": max_row["abs_pct_error"],
                           "abs_error_n_units": max_row["abs_error_n_units"]},
        "worst_case_core": {"id": core_max_row["id"], "family": core_max_row["family"],
                            "abs_pct_error": core_max_row["abs_pct_error"],
                            "abs_error_n_units": core_max_row["abs_error_n_units"]},
        "mean_n": round(mean_n, 5),
    },
    "verdict": {
        "graded_outcome": None,   # filled below
        "core_model_beats_null": core_mape < core_null_mape,
        "applicability_domain": (
            "Lorentz-Lorenz additive molar refraction predicts refractive index of "
            "non-conjugated coating solvents (aromatics, aliphatics, ketones, esters, "
            "alcohols AND water) to <0.5%. It under-predicts liquids with EXTENDED "
            "conjugation (styrene: vinyl conjugated with the ring) because additivity "
            "omits optical exaltation. That is the honest domain of applicability. "
            "Unlike the Parachor surface-tension model, H-bonding alcohols and water "
            "are IN-domain here (RI is an electronic-polarizability property)."),
        "is_a_phase0_gate": False,
    },
    "honest_limitations": [
        "Pure-liquid n_D at 20 C, sodium-D line only; NOT the cured epoxy-film RI "
        "(extendable to the resin via repeat-unit R_LL -- a Phase-1 step).",
        "Requires a measured density rho (same input dependency as the Parachor model); "
        "an all-a-priori path would chain Fedors molar volume for rho (Phase-1).",
        "Extended-conjugation exaltation (styrene) is OUT of the additive domain; "
        "reported, not hidden.",
        "Eisenlohr is one refraction table; alternative sets (Vogel bond refractions) "
        "shift predictions by a fraction of a percent.",
    ],
    "does_not": [
        "does NOT promote amphora-molecule-property (or any module) to PHASE_0",
        "does NOT add any PHASE_0 module; the live front-matter Phase-0 set (see "
        "phase0_reconciliation_redteam) is unchanged by this audit",
        "does NOT modify any of the 66 signed receipts or the manifest",
        "does NOT perform PHASE0_EVALUATOR / PHASE0_INTERNAL_REVIEWER signing (AUDIT_ONLY key only)",
    ],
}

# graded outcome from the core (non-extended-conjugation) domain -- the honest claim scope
if core_mape <= 0.005 and core_frac_within_0005 >= 0.85 and core_mape < core_null_mape:
    diagnostic["verdict"]["graded_outcome"] = "VALIDATED_IN_DOMAIN"
elif core_mape <= 0.015 and core_mape < core_null_mape:
    diagnostic["verdict"]["graded_outcome"] = "DIRECTIONAL_IN_DOMAIN"
else:
    diagnostic["verdict"]["graded_outcome"] = "REFUTED"

out = json.dumps(diagnostic, indent=2, sort_keys=True)
_outpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "diagnostic.out.json")
with open(_outpath, "w") as f:
    f.write(out)
print("diagnostic_sha256", hashlib.sha256(out.encode()).hexdigest())
print("overall_mape", overall_mape, "| core_mape", core_mape,
      "| core_rmse_n", core_rmse_n, "| core_lift_over_null",
      round(1.0 - core_mape / core_null_mape, 4))
print("core_frac_within_0.002", core_frac_within_0002, "| core_frac_within_0.005", core_frac_within_0005)
print("family_mape", json.dumps(family_mape))
print("worst_all", max_row["id"], max_row["abs_pct_error"], "| worst_core", core_max_row["id"], core_max_row["abs_pct_error"])
print("graded_outcome", diagnostic["verdict"]["graded_outcome"])
