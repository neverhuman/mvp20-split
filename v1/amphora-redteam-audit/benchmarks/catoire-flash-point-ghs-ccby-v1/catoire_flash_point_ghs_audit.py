"""AUDIT_ONLY red-team science increment: a-priori prediction of the CLOSED-CUP
FLASH POINT (and the resulting GHS flammable-liquid category) of coating-relevant
solvents via the Catoire & Naudet (2004) unique flash-point equation, validated
non-circularly against independent experimental closed-cup flash points.

WHY THIS PROPERTY (the highest-value UN-ANCHORED solvent axis remaining):
  The flash point is the single most consequential SAFETY / REGULATORY number on a
  marine two-part epoxy-amine coating's thinner / co-solvent package. It sets:
    - the GHS flammable-liquid CATEGORY on the product label (Cat 1/2/3/4),
    - the IMDG / ADR dangerous-goods class for SHIPPING the paint by sea/road,
    - storage, bonding/earthing and hot-work requirements on site,
    - and is the primary flammability gate the sourceability / EHS lane must honour.
  The tree already anchors the two THERMODYNAMIC drivers of the flash point -- the
  normal boiling point (Joback boiling-point audit) and the enthalpy of vaporization
  (Joback dHvap audit) -- but NOTHING previously turned those into the flash point /
  GHS category a formulator and a shipping desk actually act on. This audit closes
  that loop: it is a CAPSTONE that consumes the two already-anchored solvent
  properties (Tb, dHvap) plus the exact carbon count and predicts a NEW property that
  no other module supplies.

THEORY (real, cited, non-circular):
  Catoire, L.; Naudet, V. "A Unique Equation to Estimate Flash Points of Selected
  Pure Liquids -- Application to the Correction of Probably Erroneous Flash Point
  Values." J. Phys. Chem. Ref. Data 2004, 33(4), 1083-1111. The closed-cup flash
  point is a power-law product of three pure-component quantities:
      FP = 1.477 * Tb^0.79686 * dHvap^0.16845 * nC^(-0.05948)          [FP, Tb in K]
  with dHvap the STANDARD enthalpy of vaporization at 298.15 K (kJ/mol) and nC the
  number of carbon atoms. The four constants (1.477, 0.79686, 0.16845, -0.05948) were
  regressed by Catoire & Naudet on a SEPARATE 59-compound set and are UNIVERSAL
  published constants -- NOT re-fitted to this validation panel -> non-circular by
  construction. Reported accuracy of the original correlation: mean abs deviation
  ~2.9 K, max ~7 K, valid for Tb 250-650 K, dHvap 20-110 kJ/mol, nC 1-21.

  Ground truth: independent experimental CLOSED-CUP flash points (GESTIS / CRC /
  PubChem-aggregated regulatory values, e.g. ethylbenzene 23 C per EC 440/2008 A.9).
  Flash point is a method-dependent, apparatus-sensitive quantity: literature
  closed-cup values scatter by ~+-2-4 K between sources and open-cup values run a few
  K higher. That truth uncertainty is declared up front and is WHY the graded
  operational KPI is the discrete GHS category plus a Kelvin MAE benchmarked against
  Catoire's own ~2.9 K, NOT a spuriously precise sub-1% MAPE.

  TRUST DESIGN (why the number is believable, not a transcription artefact):
   (1) Every molecule's hand-encoded Joback group multiset is formula-checked by
       RDKit: the group atom composition (C,H,O) must reconstruct the exact RDKit
       molecular formula. The multisets are byte-identical to the boiling-point and
       dHvap audits -> cross-audit structural consistency. A miscount cannot pass.
   (2) Self-consistency triangulation: the Catoire equation is fed the experimental
       (Tb, dHvap298) pair and reproduces the INDEPENDENT experimental flash point to
       within a few K for every core solvent. Because Tb and dHvap298 both enter the
       prediction, a materially wrong tabulated Tb or dHvap298 would blow the flash
       point up -- so the close FP agreement is simultaneously a cross-check on the
       thermodynamic inputs themselves.
   (3) A-priori robustness track (Track B): the same flash point is recomputed with
       the boiling point REPLACED by its Joback structure-only prediction (the exact
       increments and multisets of the anchored boiling-point audit). This shows the
       accuracy actually available for a NOVEL solvent with no measured Tb, isolating
       the dominant a-priori input (Tb, exponent 0.797). dHvap298 is itself anchored
       (Joback dHvap audit + Watson), so a fully structure-only path exists; Track B
       substitutes experimental dHvap298 only to isolate the boiling-point term.

Promotes nothing. Signs no phase0 evaluation/review receipt. AUDIT_ONLY.
"""
import json, hashlib, os, glob
from rdkit import Chem


# --- Live Phase-0 reconciliation (red-team of the "FULL phase 0" claim) ---------
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
                fh.readline()
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
    n_sci_required = 0
    n_target_validated = 0
    for pol in sorted(glob.glob(os.path.join(root, "amphora-*/evidence/phase0/promotion/policy.v1.json"))):
        try:
            with open(pol) as fh:
                pj = json.load(fh)
        except Exception:
            continue
        if pj.get("scientific_success_required") is True:
            n_sci_required += 1
        if pj.get("target_scientific_readiness") == "VALIDATED":
            n_target_validated += 1
    return {
        "n_modules_labelled_phase0_in_live_frontmatter": len(phase0),
        "by_scientific_readiness": dict(sorted(by_sr.items())),
        "n_phase0_promotion_policies_requiring_scientific_success": n_sci_required,
        "n_phase0_promotion_policies_targeting_scientific_readiness_VALIDATED": n_target_validated,
        "n_externally_validated_science": 1,
        "externally_validated_science_modules": ["amphora-solvency-score"],
        "phase0_modules": phase0,
        "honest_reading": (
            "PHASE_0 here = a reproducibility+rights+independence GOVERNANCE lock, NOT "
            "scientific validation. Live cross-check of every phase0 promotion policy: "
            "scientific_success_required is FALSE in 100% of them and ZERO target "
            "scientific_readiness=VALIDATED (ceiling is LOCKED_INTERNAL). No module "
            "carries scientific_readiness=VALIDATED. Exactly ONE module (amphora-"
            "solvency-score) has any EXTERNAL-data predictive validation behind it. "
            "'FULL Phase-0' is an engineering/governance milestone, never a count of "
            "validated coating science. This audit does NOT change that count."),
    }


# --- Joback (1987) normal-boiling-point increments tbk (K) -- byte-identical to the
#     anchored boiling-point audit; used only for the Track B a-priori Tb path -------
JOBACK_TB = {
    "CH3":          (23.58, 1, 3, 0), "CH2":         (22.88, 1, 2, 0),
    "CH":           (21.74, 1, 1, 0), "C":           (18.25, 1, 0, 0),
    "ring_CH2":     (27.15, 1, 2, 0), "ring_CH":     (21.78, 1, 1, 0),
    "ring_C":       (21.32, 1, 0, 0), "arom_CH":     (26.73, 1, 1, 0),
    "arom_C":       (31.01, 1, 0, 0), "OH_alcohol":  (92.88, 0, 1, 1),
    "O_ether":      (22.42, 0, 0, 1), "O_ring_ether":(31.22, 0, 0, 1),
    "CO_ketone":    (76.75, 1, 0, 1), "CO_ring":     (94.97, 1, 0, 1),
    "COO_ester":    (81.10, 1, 0, 2),
}
JOBACK_TB_C0 = 198.2  # K

# Catoire & Naudet 2004 universal constants (NOT fitted here)
CAT_A, CAT_B, CAT_C, CAT_D = 1.477, 0.79686, 0.16845, -0.05948


# --- Truth set --------------------------------------------------------------------
# id, family, SMILES, nC, Tb_K (CRC/NIST, shared panel), dHvap298_kJ/mol (NIST
# WebBook / Majer-Svoboda 298.15 K basis), FP_exp_C (experimental CLOSED-CUP flash
# point, GESTIS/CRC/PubChem regulatory), joback_groups (formula-checked vs RDKit).
SOLVENTS = [
    ("benzene",        "aromatic",  "c1ccccc1",       353.24, 33.83, -11.0,
        {"arom_CH": 6}),
    ("toluene",        "aromatic",  "Cc1ccccc1",      383.75, 38.06,   4.0,
        {"arom_CH": 5, "arom_C": 1, "CH3": 1}),
    ("o-xylene",       "aromatic",  "Cc1ccccc1C",     417.58, 43.43,  32.0,
        {"arom_CH": 4, "arom_C": 2, "CH3": 2}),
    ("p-xylene",       "aromatic",  "Cc1ccc(C)cc1",   411.51, 42.40,  27.0,
        {"arom_CH": 4, "arom_C": 2, "CH3": 2}),
    ("ethylbenzene",   "aromatic",  "CCc1ccccc1",     409.35, 42.24,  23.0,
        {"arom_CH": 5, "arom_C": 1, "CH2": 1, "CH3": 1}),
    ("n-hexane",       "aliphatic", "CCCCCC",         341.88, 31.55, -22.0,
        {"CH3": 2, "CH2": 4}),
    ("n-heptane",      "aliphatic", "CCCCCCC",        371.57, 36.57,  -4.0,
        {"CH3": 2, "CH2": 5}),
    ("cyclohexane",    "cyclic",    "C1CCCCC1",       353.87, 33.01, -18.0,
        {"ring_CH2": 6}),
    ("acetone",        "ketone",    "CC(=O)C",        329.20, 31.30, -18.0,
        {"CH3": 2, "CO_ketone": 1}),
    ("mek",            "ketone",    "CCC(=O)C",       352.79, 34.79,  -6.0,
        {"CH3": 2, "CH2": 1, "CO_ketone": 1}),
    ("mibk",           "ketone",    "CC(=O)CC(C)C",   389.65, 40.60,  14.0,
        {"CH3": 3, "CH2": 1, "CH": 1, "CO_ketone": 1}),
    ("ethyl-acetate",  "ester",     "CCOC(=O)C",      350.21, 35.60,  -4.0,
        {"CH3": 2, "CH2": 1, "COO_ester": 1}),
    ("n-butyl-acetate","ester",     "CCCCOC(=O)C",    399.15, 43.86,  22.0,
        {"CH3": 2, "CH2": 3, "COO_ester": 1}),
    # alcohols -- boundary (self-associating); Catoire captures H-bonding via dHvap,
    # so it is reported and gated separately from the core non-associating set.
    ("methanol",       "alcohol",   "CO",             337.70, 37.43,  11.0,
        {"CH3": 1, "OH_alcohol": 1}),
    ("ethanol",        "alcohol",   "CCO",            351.44, 42.32,  13.0,
        {"CH3": 1, "CH2": 1, "OH_alcohol": 1}),
    ("1-propanol",     "alcohol",   "CCCO",           370.35, 47.50,  22.0,
        {"CH3": 1, "CH2": 2, "OH_alcohol": 1}),
    ("2-propanol",     "alcohol",   "CC(O)C",         355.41, 45.39,  12.0,
        {"CH3": 2, "CH": 1, "OH_alcohol": 1}),
    ("1-butanol",      "alcohol",   "CCCCO",          390.87, 52.35,  35.0,
        {"CH3": 1, "CH2": 3, "OH_alcohol": 1}),
]
BOUNDARY = {"methanol", "ethanol", "1-propanol", "2-propanol", "1-butanol"}

# FP truth-source scatter that straddles the GHS 23 C boundary (declared honesty)
BOUNDARY_FP_NOTE = {
    "ethylbenzene": "exp closed-cup FP sits exactly on the 23 C GHS Cat2/Cat3 line "
                    "(EC 440/2008 A.9 = 23 C; some vendor SDS quote 15-21 C).",
    "n-butyl-acetate": "exp closed-cup FP quoted 22-27 C across GESTIS/CRC/SDS; the "
                       "23 C GHS boundary falls inside that literature scatter.",
}

K0 = 273.15


def catoire_fp_K(tb_K, dhvap298, nC):
    return CAT_A * (tb_K ** CAT_B) * (dhvap298 ** CAT_C) * (nC ** CAT_D)


def joback_tb_K(groups):
    return JOBACK_TB_C0 + sum(JOBACK_TB[g][0] * n for g, n in groups.items())


def formula_from_groups(groups, table):
    c = h = o = 0
    for g, n in groups.items():
        _, gc, gh, go = table[g]
        c += gc * n; h += gh * n; o += go * n
    return (c, h, o)


def rdkit_formula(smiles):
    m = Chem.MolFromSmiles(smiles)
    assert m is not None, smiles
    mh = Chem.AddHs(m)
    c = h = o = 0
    for a in mh.GetAtoms():
        s = a.GetSymbol()
        if s == "C": c += 1
        elif s == "H": h += 1
        elif s == "O": o += 1
        else:
            raise AssertionError("unexpected element %s in %s" % (s, smiles))
    return (c, h, o)


def rdkit_carbon_count(smiles):
    m = Chem.MolFromSmiles(smiles)
    return sum(1 for a in m.GetAtoms() if a.GetSymbol() == "C")


def ghs_category(fp_C, tb_K):
    """GHS Rev.* flammable-liquid category from closed-cup FP (C) and boiling pt."""
    if fp_C < 23.0 and tb_K <= 308.15:
        return "Cat1"
    if fp_C < 23.0:
        return "Cat2"
    if fp_C <= 60.0:
        return "Cat3"
    if fp_C <= 93.0:
        return "Cat4"
    return "Not_classified"


def spearman(xs, ys):
    def ranks(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0] * len(v)
        for rank, i in enumerate(order):
            r[i] = rank
        return r
    rx, ry = ranks(xs), ranks(ys)
    n = len(xs)
    mx = sum(rx) / n; my = sum(ry) / n
    num = sum((rx[i] - mx) * (ry[i] - my) for i in range(n))
    dx = sum((rx[i] - mx) ** 2 for i in range(n)) ** 0.5
    dy = sum((ry[i] - my) ** 2 for i in range(n)) ** 0.5
    return num / (dx * dy)


def rmse(errs):
    return (sum(e * e for e in errs) / len(errs)) ** 0.5


def build():
    rows = []
    for name, family, smi, tb, dhv298, fp_exp_C, groups in SOLVENTS:
        # (1) formula guard: hand-encoded Joback groups must reconstruct RDKit formula
        assert formula_from_groups(groups, JOBACK_TB) == rdkit_formula(smi), \
            "group/formula mismatch %s" % name
        nC = rdkit_carbon_count(smi)               # exact carbon count from structure
        assert nC == formula_from_groups(groups, JOBACK_TB)[0], "nC mismatch %s" % name

        # Track A: Catoire with EXPERIMENTAL Tb + dHvap298 (isolates correlation error)
        fpA_K = catoire_fp_K(tb, dhv298, nC)
        fpA_C = fpA_K - K0
        errA = fpA_C - fp_exp_C

        # Track B: Catoire with Joback STRUCTURE-ONLY Tb (novel-molecule path)
        tb_jb = joback_tb_K(groups)
        fpB_C = catoire_fp_K(tb_jb, dhv298, nC) - K0
        errB = fpB_C - fp_exp_C

        cat_exp = ghs_category(fp_exp_C, tb)
        cat_pred = ghs_category(fpA_C, tb)         # classify on the Track A prediction
        rows.append({
            "id": name, "family": family, "smiles": smi, "nC": nC,
            "tb_K": tb, "dhvap298_kJ": dhv298, "fp_exp_C": fp_exp_C,
            "fp_pred_A_C": round(fpA_C, 2), "abs_err_A_K": round(abs(errA), 3),
            "signed_err_A_K": round(errA, 3),
            "tb_joback_K": round(tb_jb, 2),
            "fp_pred_B_C": round(fpB_C, 2), "abs_err_B_K": round(abs(errB), 3),
            "ghs_cat_exp": cat_exp, "ghs_cat_pred": cat_pred,
            "ghs_match": cat_exp == cat_pred,
            "domain": "BOUNDARY" if name in BOUNDARY else "CORE",
            "fp_boundary_note": BOUNDARY_FP_NOTE.get(name),
        })
    rows.sort(key=lambda r: r["id"])

    core = [r for r in rows if r["domain"] == "CORE"]
    alco = [r for r in rows if r["domain"] == "BOUNDARY"]

    def block(subset, track):
        ek = "abs_err_%s_K" % track
        errs = [r[ek] for r in subset]
        preds = [r["fp_pred_%s_C" % track] for r in subset]
        exps = [r["fp_exp_C"] for r in subset]
        mae = sum(errs) / len(errs)
        rms = rmse([r["signed_err_A_K"] for r in subset]) if track == "A" else \
              rmse([p - e for p, e in zip(preds, exps)])
        worst = max(subset, key=lambda r: r[ek])
        within3 = sum(1 for e in errs if e <= 3.0)
        within5 = sum(1 for e in errs if e <= 5.0)
        within8 = sum(1 for e in errs if e <= 8.0)
        # null baseline = predict the mean experimental FP (no per-molecule info)
        mean_fp = sum(exps) / len(exps)
        null_rms = rmse([e - mean_fp for e in exps])
        lift = (null_rms - rms) / null_rms * 100.0
        return {
            "n": len(subset),
            "MAE_K": round(mae, 3),
            "RMSE_K": round(rms, 3),
            "max_abs_err_K": round(worst[ek], 3),
            "max_abs_err_solvent": worst["id"],
            "within_3K": "%d/%d" % (within3, len(subset)),
            "within_5K": "%d/%d" % (within5, len(subset)),
            "within_8K": "%d/%d" % (within8, len(subset)),
            "null_mean_fp_RMSE_K": round(null_rms, 3),
            "lift_over_mean_null_pct": round(lift, 3),
            "spearman_fp_order": round(spearman(preds, exps), 6),
        }

    ghs_core_match = sum(1 for r in core if r["ghs_match"])
    ghs_all_match = sum(1 for r in rows if r["ghs_match"])
    ghs_misses = [{"id": r["id"], "exp": r["ghs_cat_exp"], "pred": r["ghs_cat_pred"],
                   "note": r["fp_boundary_note"]} for r in rows if not r["ghs_match"]]

    kpis = {
        "core_domain_definition": ("aromatic, aliphatic, cyclic, ketone and ester "
            "coating solvents (non-associating); alcohols reported separately as "
            "BOUNDARY (self-associating, though Catoire captures H-bonding via dHvap)"),
        "trackA_definition": "Catoire FP from EXPERIMENTAL Tb + dHvap298 + exact nC (isolates the correlation's own error)",
        "trackB_definition": "Catoire FP with the boiling point REPLACED by its Joback structure-only prediction (novel-molecule path; exponent-0.797 dominant input)",
        "core_trackA": block(core, "A"),
        "core_trackB": block(core, "B"),
        "alcohols_trackA": block(alco, "A"),
        "all_trackA": block(rows, "A"),
        "catoire_reference_accuracy_K": {"reported_MAD": 2.9, "reported_max": 7.0},
        "ghs_category_exact_match_core": "%d/%d" % (ghs_core_match, len(core)),
        "ghs_category_exact_match_all": "%d/%d" % (ghs_all_match, len(rows)),
        "ghs_category_misses": ghs_misses,
        "ghs_miss_note": ("every GHS category miss is a solvent whose experimental "
            "closed-cup FP sits within ~2 K of the 23 C Cat2/Cat3 boundary AND whose "
            "literature FP scatter straddles that boundary (see fp_boundary_note); the "
            "predicted FP is within truth uncertainty of the line. No miss crosses more "
            "than one category or exceeds the flammable/combustible 60 C line."),
        "self_consistency_triangulation": ("Track A feeds INDEPENDENT experimental Tb "
            "and dHvap298 into the Catoire equation and recovers the INDEPENDENT "
            "experimental flash point to a few K for every core solvent; a materially "
            "wrong tabulated Tb or dHvap298 would not reproduce FP, so the agreement "
            "cross-validates the thermodynamic inputs as well as the flash point."),
    }

    a = kpis["core_trackA"]
    passed = (a["MAE_K"] <= 5.0 and a["max_abs_err_K"] <= 8.0
              and int(a["within_5K"].split("/")[0]) >= len(core) - 2
              and ghs_core_match >= int(round(0.80 * len(core)))
              and a["spearman_fp_order"] >= 0.95
              and a["lift_over_mean_null_pct"] >= 60.0)
    verdict = {
        "graded_outcome": "VALIDATED_IN_DOMAIN" if passed else "NOT_VALIDATED",
        "gate_logic": ("core Track A: MAE<=5K (Catoire ref ~2.9K) AND max_abs_err<=8K "
                       "(ref ~7K) AND >=(n-2) within +-5K AND GHS-category exact match "
                       ">=80% AND spearman(FP order)>=0.95 AND lift>=60%"),
        "gate_passed": bool(passed),
        "authority": "AUDIT_ONLY -- graded domain-of-applicability study, NOT a Phase-0 gate",
    }

    diag = {
        "schema": "amphora.redteam-audit.catoire-flash-point-ghs-ccby-v1.diagnostic.v1",
        "target_module": "amphora-molecule-property",
        "target_capability": ("a-priori CLOSED-CUP FLASH POINT and GHS flammable-liquid "
            "category for coating solvents/reactive diluents -- the regulatory/shipping "
            "capstone that consumes the already-anchored boiling-point (Joback) and "
            "enthalpy-of-vaporization (Joback) axes plus the exact carbon count and "
            "predicts the flammability class no other module supplies"),
        "theory": {
            "predictor": "Catoire & Naudet 2004 unique flash-point equation: FP = 1.477*Tb^0.79686*dHvap298^0.16845*nC^(-0.05948)",
            "predictor_citation": ("Catoire, L.; Naudet, V. J. Phys. Chem. Ref. Data "
                                   "2004, 33(4), 1083-1111"),
            "predictor_reported_accuracy": "mean abs deviation ~2.9 K, max ~7 K; valid Tb 250-650 K, dHvap 20-110 kJ/mol, nC 1-21",
            "ground_truth": ("independent experimental CLOSED-CUP flash points "
                             "(GESTIS / CRC / PubChem-aggregated regulatory values; "
                             "ethylbenzene 23 C per EC 440/2008 A.9)"),
            "thermo_inputs": ("Tb: CRC/NIST normal boiling points (shared panel with the "
                              "boiling-point / dHvap audits); dHvap298: NIST WebBook / "
                              "Majer-Svoboda 298.15 K enthalpies of vaporization; nC: exact"),
            "non_circularity": ("the four Catoire constants were regressed on a SEPARATE "
                                "59-compound set and are NOT re-fit here; ground-truth FP "
                                "are independent experimental measurements; no parameter "
                                "is tuned on this validation panel"),
            "trust_guard": ("Joback group multisets formula-checked vs RDKit and byte-"
                            "identical to the boiling-point/dHvap audits; self-consistency "
                            "triangulation of Tb & dHvap298 through the recovered FP"),
            "operational_kpi": ("discrete GHS flammable-liquid CATEGORY exact-match plus "
                                "Kelvin MAE benchmarked against Catoire's own ~2.9 K "
                                "(flash point truth is method-dependent; a discrete class "
                                "+ Kelvin MAE is the honest operational metric, not a "
                                "spurious sub-1% MAPE)"),
        },
        "rights": {
            "predictor_method": "Catoire-Naudet correlation -- published theory, freely usable",
            "ground_truth_data": ("experimental closed-cup flash points -- tabulated "
                                  "physical/regulatory facts (GESTIS/CRC/PubChem/EC), "
                                  "non-copyrightable single-value constants"),
            "thermo_inputs": "Tb, dHvap298, nC -- tabulated NIST/CRC facts (non-copyrightable)",
            "rights_gate_passed": True,
            "in_scope": ("marine two-part epoxy-amine coating thinner / co-solvent "
                         "chemistries; flammability class / IMDG shipping / EHS gate; "
                         "no adjacent-industry data"),
        },
        "n_solvents_total": len(rows),
        "n_core": len(core),
        "n_boundary": len(alco),
        "phase0_reconciliation_redteam": phase0_reconciliation(),
        "kpis": kpis,
        "verdict": verdict,
        "per_solvent": rows,
        "honest_limitations": [
            "flash point is a method-dependent apparatus quantity: closed-cup literature "
            "values scatter ~+-2-4 K between sources and open-cup runs a few K higher; the "
            "graded metric is therefore the discrete GHS category + a Kelvin MAE "
            "benchmarked to Catoire's ~2.9 K, not a sub-1% MAPE.",
            "two GHS-category misses (ethylbenzene, n-butyl acetate) are both solvents "
            "whose experimental FP sits within ~2 K of the 23 C Cat2/Cat3 boundary and "
            "whose literature FP straddles it; the prediction is within truth uncertainty.",
            "Catoire is a PURE-COMPONENT correlation; a real solvent BLEND flash point is "
            "governed by the most volatile component's partial pressure (non-ideal, "
            "activity-coefficient) and is a Phase-1 extension, not claimed here.",
            "isomers with identical Joback first-order groups (o- vs p-xylene) share the "
            "Track B Joback Tb; Track A uses their distinct experimental Tb and resolves them.",
            "outside the stated Catoire validity box (Tb 250-650 K, dHvap 20-110 kJ/mol, "
            "nC 1-21) the correlation is not asserted; all panel solvents are inside it.",
        ],
        "does_not": [
            "does NOT promote amphora-molecule-property (or any module) to PHASE_0 or change scientific_readiness",
            "does NOT modify any of the 66 signed receipts or the receipts manifest",
            "does NOT assert organizational independence or perform human review",
            "does NOT claim a solvent-BLEND flash point (non-ideal; Phase-1 extension)",
            "does NOT re-fit the Catoire constants or tune any parameter on the validation panel",
            "does NOT perform PHASE0_EVALUATOR / PHASE0_INTERNAL_REVIEWER signing (AUDIT_ONLY key custody only)",
        ],
    }
    return diag


def canonical_bytes(obj):
    return json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=True).encode()


if __name__ == "__main__":
    import sys
    diag = build()
    out = sys.argv[1] if len(sys.argv) > 1 else "diagnostic.out.json"
    b = canonical_bytes(diag)
    with open(out, "wb") as fh:
        fh.write(b)
    print("WROTE", out)
    print("sha256", hashlib.sha256(b).hexdigest())
