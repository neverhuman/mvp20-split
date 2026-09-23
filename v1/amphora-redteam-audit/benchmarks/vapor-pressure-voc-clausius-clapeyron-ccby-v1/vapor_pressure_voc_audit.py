"""Vapor pressure P(25C) / VOC-evaporation anchor for the amphora coating portfolio.

WHAT THIS IS
------------
A rights-clean, non-circular, AUDIT_ONLY validation of an a-priori engine for the
25 C saturated vapor pressure P0(298.15 K) of coating solvents -- the quantitative
driver of (a) VOC content / regulatory compliance and (b) the fast/medium/slow
evaporation balance that governs application window, sag, solvent-popping and
blush in a two-part epoxy-amine marine coating.

It is the missing ABSOLUTE-volatility companion to the already-anchored axes:
  * Joback normal boiling point Tb          (joback-boiling-point-volatility-ccby-v1)
  * Joback heat of vaporisation dHvap(Tb)    (joback-heat-of-vaporization-ccby-v1)
Boiling point only orders solvents; flash point handles safety; NEITHER gives the
absolute room-temperature vapor pressure a VOC calculation or an evaporation-rate
balance actually needs. This capstone consumes the two anchored thermochemical
axes and closes that gap -- exactly as the Catoire flash-point capstone consumed
the anchored Tb.

THEORY  (all universal published constants; nothing fitted to this panel)
------------------------------------------------------------------------
Clausius-Clapeyron with a temperature-dependent enthalpy of vaporisation:
      d ln P / dT = dHvap(T) / (R T^2)
integrated from the normal boiling point (where P = 101.325 kPa by definition)
down to 298.15 K. dHvap(T) is corrected off its boiling-point value with the
Watson relation (Watson 1943; Poling/Prausnitz/O'Connell 5th ed. eq 7-2.5):
      dHvap(T) = dHvap(Tb) * ((Tc - T)/(Tc - Tb))^0.38
Tc is estimated a-priori from the SAME Joback group multiset used for Tb, via
      Tc = Tb / (0.584 + 0.965*A - A^2),  A = sum_i n_i * tck_i
(Joback & Reid 1987). The Joback Tc constants are cross-validated in-script
against 8 independent NIST/CRC critical temperatures.

TWO NON-CIRCULARITY LEVELS (both reported)
------------------------------------------
  PHYSICS  path : measured Tb + measured dHvap(Tb) + Joback Tc  -> isolates the
                  Clausius-Clapeyron+Watson METHOD given measured thermochemistry.
  A-PRIORI path : Joback Tb + Joback dHvap(Tb) + Joback Tc      -> fully structure
                  -> P0(25C); the end-to-end capability that consumes the anchors.
Ground truth P0(298.15 K) is computed from NIST Chemistry WebBook Antoine
constants (public-domain U.S. Government work) evaluated at 298.15 K -- an
INDEPENDENT measurement source, tuned to none of the above.

This is a graded domain-of-applicability study. It is AUDIT_ONLY: it promotes no
authority, signs no Phase-0 evaluation/review receipt, modifies no existing
receipt and does not touch the master manifest.
"""
import glob, hashlib, json, os
from rdkit import Chem

R = 8.314462618       # J/mol/K
T0 = 298.15           # K  (25 C)
PB_KPA = 101.325      # kPa (1 atm, normal boiling reference)
WATSON_N = 0.38       # Watson enthalpy exponent (universal)
JOBACK_C0 = 198.2     # Joback Tb additive constant (K)

# --- Joback (1987) group increments: (tbk_K, tck, C, H, O) -----------------------
# tbk = normal-boiling contribution (K); tck = critical-temperature contribution.
# Universal published constants (Joback & Reid, Chem.Eng.Commun. 1987, 57, 233;
# Poling/Prausnitz/O'Connell, Properties of Gases and Liquids 5th ed., Table C-1).
# NOT fitted here. (C,H,O) lets each decomposition be formula-checked vs RDKit.
JOBACK = {
    "CH3":          (23.58, 0.0141, 1, 3, 0),
    "CH2":          (22.88, 0.0189, 1, 2, 0),
    "CH":           (21.74, 0.0164, 1, 1, 0),
    "C":            (18.25, 0.0067, 1, 0, 0),
    "ring_CH2":     (27.15, 0.0100, 1, 2, 0),
    "ring_CH":      (21.78, 0.0122, 1, 1, 0),
    "ring_C":       (21.32, 0.0042, 1, 0, 0),
    "arom_CH":      (26.73, 0.0082, 1, 1, 0),
    "arom_C":       (31.01, 0.0143, 1, 0, 0),
    "OH_alcohol":   (92.88, 0.0741, 0, 1, 1),
    "O_ether":      (22.42, 0.0168, 0, 0, 1),
    "O_ring_ether": (31.22, 0.0098, 0, 0, 1),
    "CO_ketone":    (76.75, 0.0380, 1, 0, 1),
    "CO_ring":      (94.97, 0.0284, 1, 0, 1),
    "COO_ester":    (81.10, 0.0481, 1, 0, 2),
}

# --- Panel: id, family, SMILES, M, Tb_exp_K, dHvap_exp_kJ(Tb), dHvap_joback_kJ(Tb),
#           P0_exp_kPa(298.15K), antoine_ref, joback_groups ----------------------
# Tb_exp / dHvap_exp / dHvap_joback are carried verbatim from the two signed anchors
# (joback-boiling-point-volatility-ccby-v1, joback-heat-of-vaporization-ccby-v1) so
# this capstone literally consumes them. P0_exp is computed from the cited NIST
# Antoine parameter set valid at (or nearest to) 298.15 K. Group multisets are the
# hand-verified Joback decompositions, re-formula-checked against RDKit below.
SOLVENTS = [
    ("benzene","aromatic","c1ccccc1",78.11,353.24,30.72,30.564,12.14,
        "NIST Antoine, Deshpande&Pandya 1967 (297.9-318K)",{"arom_CH":6}),
    ("toluene","aromatic","Cc1ccccc1",92.14,383.75,33.18,33.452,3.791,
        "NIST Antoine, Pitzer&Scott 1943 (273-323K)",{"arom_CH":5,"arom_C":1,"CH3":1}),
    ("o-xylene","aromatic","Cc1ccccc1C",106.17,417.58,36.24,36.34,0.879,
        "NIST Antoine, Pitzer&Scott 1943 (273-323K)",{"arom_CH":4,"arom_C":2,"CH3":2}),
    ("p-xylene","aromatic","Cc1ccc(C)cc1",106.17,411.51,35.67,36.34,1.18,
        "NIST Antoine, Pitzer&Scott 1943 (298-333K)",{"arom_CH":4,"arom_C":2,"CH3":2}),
    ("ethylbenzene","aromatic","CCc1ccccc1",106.17,409.35,35.57,35.678,1.27,
        "NIST Antoine, Willingham et al. 1945 (330-410K)",{"arom_CH":5,"arom_C":1,"CH2":1,"CH3":1}),
    ("n-hexane","aliphatic","CCCCCC",86.18,341.88,28.85,28.95,20.32,
        "NIST Antoine, Willingham et al. 1945 (286-343K)",{"CH3":2,"CH2":4}),
    ("n-heptane","aliphatic","CCCCCCC",100.20,371.57,31.77,31.176,6.02,
        "NIST Antoine, Willingham et al. 1945 (299-372K)",{"CH3":2,"CH2":5}),
    ("cyclohexane","cyclic","C1CCCCC1",84.16,353.87,29.97,29.688,13.03,
        "NIST Antoine, Gaw&Swinton 1968 (303-343K)",{"ring_CH2":6}),
    ("acetone","ketone","CC(=O)C",58.08,329.20,29.1,29.018,30.65,
        "NIST Antoine, Ambrose et al. 1974 (259-508K)",{"CH3":2,"CO_ketone":1}),
    ("mek","ketone","CCC(=O)C",72.11,352.79,31.3,31.244,12.05,
        "NIST Antoine, Nickerson et al. 1961 (315-371K)",{"CH3":2,"CH2":1,"CO_ketone":1}),
    ("mibk","ketone","CC(=O)CC(C)C",100.16,389.65,34.49,35.308,2.61,
        "NIST Antoine, Fuge et al. 1952 (295-389K)",{"CH3":3,"CH2":1,"CH":1,"CO_ketone":1}),
    ("ethyl-acetate","ester","CCOC(=O)C",88.11,350.21,31.94,31.905,12.59,
        "NIST Antoine, Polak&Mertl 1965 (289-349K)",{"CH3":2,"CH2":1,"COO_ester":1}),
    ("n-butyl-acetate","ester","CCCCOC(=O)C",116.16,399.15,36.28,36.357,1.53,
        "NIST Antoine, Kliment et al. 1964 (333-399K)",{"CH3":2,"CH2":3,"COO_ester":1}),
    ("methanol","alcohol","CO",32.04,337.70,35.21,34.499,16.88,
        "NIST Antoine, Ambrose&Sprake 1970 (288-357K)",{"CH3":1,"OH_alcohol":1}),
    ("ethanol","alcohol","CCO",46.07,351.44,38.56,36.725,7.89,
        "NIST Antoine, Ambrose&Sprake 1970 (293-367K)",{"CH3":1,"CH2":1,"OH_alcohol":1}),
    ("1-propanol","alcohol","CCCO",60.10,370.35,41.44,38.951,2.82,
        "NIST Antoine, Kemme&Kreps 1969 (292-370K)",{"CH3":1,"CH2":2,"OH_alcohol":1}),
    ("2-propanol","alcohol","CC(O)C",60.10,355.41,39.85,38.563,5.71,
        "NIST Antoine, Biddiscombe et al. 1963 (330-362K)",{"CH3":2,"CH":1,"OH_alcohol":1}),
    ("1-butanol","alcohol","CCCCO",74.12,390.87,43.29,41.177,0.891,
        "NIST Antoine, Kemme&Kreps 1969 (296-391K)",{"CH3":1,"CH2":3,"OH_alcohol":1}),
]

# Domains inherited from the dHvap anchor (association not captured by first-order
# groups). Alcohols are declared boundary/out a priori for BOTH dHvap and P0.
OUT_OF_DOMAIN = {"methanol", "1-propanol", "1-butanol"}
BOUNDARY = {"ethanol", "2-propanol"}

# Independent measured critical temperatures (NIST/CRC) for the Joback-Tc guard.
TC_KNOWN = {
    "benzene": 562.05, "toluene": 591.75, "n-hexane": 507.6, "n-heptane": 540.2,
    "cyclohexane": 553.6, "acetone": 508.1, "ethanol": 514.0, "methanol": 512.5,
}


def formula_from_groups(groups):
    c = h = o = 0
    for g, n in groups.items():
        _, _, gc, gh, go = JOBACK[g]
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


def joback_tb(groups):
    return JOBACK_C0 + sum(JOBACK[g][0] * n for g, n in groups.items())


def joback_tc(groups, tb):
    a = sum(JOBACK[g][1] * n for g, n in groups.items())
    return tb / (0.584 + 0.965 * a - a * a)


def watson_dhvap(dhvap_tb, tb, tc, t):
    return dhvap_tb * ((tc - t) / (tc - tb)) ** WATSON_N


def pvap_298(tb, dhvap_tb_kJ, tc):
    """Integrate d lnP/dT = dHvap(T)/(R T^2) from Tb (P=PB) down to 298.15 K.

    Watson-corrected dHvap(T). Deterministic 2000-step trapezoid over [T0, Tb];
    ln P(T0) = ln PB - integral_{T0}^{Tb} dHvap(T)/(R T^2) dT.
    """
    dhvap_tb = dhvap_tb_kJ * 1000.0  # J/mol
    n = 2000
    dt = (tb - T0) / n
    total = 0.0
    prev = watson_dhvap(dhvap_tb, tb, tc, T0) / (R * T0 * T0)
    for i in range(1, n + 1):
        t = T0 + i * dt
        cur = watson_dhvap(dhvap_tb, tb, tc, t) / (R * t * t)
        total += 0.5 * (prev + cur) * dt
        prev = cur
    import math
    lnP = math.log(PB_KPA) - total
    return math.exp(lnP)


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
    return {
        "n_modules_labelled_phase0_in_live_frontmatter": len(phase0),
        "by_scientific_readiness": dict(sorted(by_sr.items())),
        "n_modules_scientific_readiness_VALIDATED": by_sr.get("VALIDATED", 0),
        "n_externally_validated_science": 1,
        "externally_validated_science_modules": ["amphora-solvency-score"],
        "phase0_modules": phase0,
        "honest_reading": (
            "PHASE_0 = a reproducibility+rights+independence GOVERNANCE lock, NOT "
            "scientific validation. 13 NOT_APPLICABLE modules are governance/infra; 4 "
            "LOCKED_INTERNAL passed an INTERNAL known-answer only. ZERO modules carry "
            "scientific_readiness=VALIDATED; module-manifest.json lists all 29 modules "
            "UNVALIDATED. 'FULL Phase-0' is an engineering milestone, never a count of "
            "validated coating science. This audit does NOT change that; it promotes "
            "nothing and adds one AUDIT_ONLY anchor."),
    }


def log10(x):
    import math
    return math.log10(x)


def build():
    rows = []
    for name, family, smi, M, tb, dh_exp, dh_job, p_exp, aref, groups in SOLVENTS:
        # (1) formula guard
        assert formula_from_groups(groups) == rdkit_formula(smi), \
            "group/formula mismatch %s" % name
        tb_job = joback_tb(groups)
        tc_meas = joback_tc(groups, tb)       # Joback Tc off MEASURED Tb (physics path)
        tc_job = joback_tc(groups, tb_job)    # Joback Tc off PREDICTED Tb (a-priori path)
        p_phys = pvap_298(tb, dh_exp, tc_meas)
        p_apri = pvap_298(tb_job, dh_job, tc_job)
        domain = ("OUT_OF_DOMAIN" if name in OUT_OF_DOMAIN
                  else "BOUNDARY" if name in BOUNDARY else "CORE")
        rows.append({
            "id": name, "family": family, "smiles": smi, "M_g_mol": M, "domain": domain,
            "tb_exp_K": tb, "tb_joback_K": round(tb_job, 4),
            "tc_joback_K": round(tc_meas, 4),
            "dhvap_exp_Tb_kJ": dh_exp, "dhvap_joback_Tb_kJ": dh_job,
            "p0_exp_kPa": p_exp,
            "p0_pred_physics_kPa": round(p_phys, 5),
            "p0_pred_apriori_kPa": round(p_apri, 5),
            "log10_err_physics": round(log10(p_phys) - log10(p_exp), 5),
            "log10_err_apriori": round(log10(p_apri) - log10(p_exp), 5),
            "abs_pct_err_physics": round(abs(p_phys - p_exp) / p_exp * 100.0, 3),
            "abs_pct_err_apriori": round(abs(p_apri - p_exp) / p_exp * 100.0, 3),
            "antoine_ref": aref,
        })
    rows.sort(key=lambda r: r["id"])

    core = [r for r in rows if r["domain"] == "CORE"]

    def mae(key):
        return sum(abs(r[key]) for r in core) / len(core)

    def rmse(key):
        return (sum(r[key] ** 2 for r in core) / len(core)) ** 0.5

    def within(key, factor):
        thr = log10(factor)
        return sum(1 for r in core if abs(r[key]) <= thr)

    # Joback-Tc guard vs 8 independent measured Tc
    tc_checks = []
    for name, tc_known in sorted(TC_KNOWN.items()):
        r = next(x for x in rows if x["id"] == name)
        pct = abs(r["tc_joback_K"] - tc_known) / tc_known * 100.0
        tc_checks.append({"id": name, "tc_joback_K": r["tc_joback_K"],
                          "tc_known_K": tc_known, "abs_pct_err": round(pct, 3)})
    tc_mape = round(sum(c["abs_pct_err"] for c in tc_checks) / len(tc_checks), 4)

    # null baseline: predict panel geometric-mean P0 for every core solvent
    mean_log = sum(log10(r["p0_exp_kPa"]) for r in core) / len(core)
    null_mae = sum(abs(log10(r["p0_exp_kPa"]) - mean_log) for r in core) / len(core)
    phys_mae = mae("log10_err_physics")
    apri_mae = mae("log10_err_apriori")
    lift_phys = (null_mae - phys_mae) / null_mae * 100.0
    lift_apri = (null_mae - apri_mae) / null_mae * 100.0

    sp_phys = spearman([r["p0_pred_physics_kPa"] for r in core], [r["p0_exp_kPa"] for r in core])
    sp_apri = spearman([r["p0_pred_apriori_kPa"] for r in core], [r["p0_exp_kPa"] for r in core])

    worst_phys = max(core, key=lambda r: abs(r["log10_err_physics"]))
    worst_apri = max(core, key=lambda r: abs(r["log10_err_apriori"]))

    kpis = {
        "core_domain_definition": ("non-associating aromatic/aliphatic/cyclic/ketone/ester "
            "coating solvents (n=13); alcohols declared boundary/out-of-domain a priori "
            "(H-bond association -> Joback dHvap under-counts, inherited from the dHvap anchor)"),
        "n_core": len(core),
        "metric_note": ("vapor pressure spans >1 decade (0.88-30.65 kPa); the honest "
            "metric is error in log10(P0) = multiplicative/geometric error. |log10|<=0.176 "
            "== within a factor of 1.5; |log10|<=0.301 == within a factor of 2."),
        "PHYSICS_path": {
            "definition": "measured Tb + measured dHvap(Tb) + Joback Tc -> Clausius-Clapeyron+Watson",
            "core_MAE_log10": round(phys_mae, 5),
            "core_RMSE_log10": round(rmse("log10_err_physics"), 5),
            "core_median_abs_pct_err": round(sorted(r["abs_pct_err_physics"] for r in core)[len(core)//2], 3),
            "core_max_abs_pct_err": worst_phys["abs_pct_err_physics"],
            "core_max_abs_pct_err_solvent": worst_phys["id"],
            "core_within_factor_1p5": "%d/%d" % (within("log10_err_physics", 1.5), len(core)),
            "core_within_factor_2": "%d/%d" % (within("log10_err_physics", 2.0), len(core)),
            "core_spearman_evap_order": round(sp_phys, 6),
            "lift_over_geomean_null_pct": round(lift_phys, 3),
        },
        "APRIORI_path": {
            "definition": "Joback Tb + Joback dHvap(Tb) + Joback Tc -> structure-only P0(25C)",
            "core_MAE_log10": round(apri_mae, 5),
            "core_RMSE_log10": round(rmse("log10_err_apriori"), 5),
            "core_median_abs_pct_err": round(sorted(r["abs_pct_err_apriori"] for r in core)[len(core)//2], 3),
            "core_max_abs_pct_err": worst_apri["abs_pct_err_apriori"],
            "core_max_abs_pct_err_solvent": worst_apri["id"],
            "core_within_factor_1p5": "%d/%d" % (within("log10_err_apriori", 1.5), len(core)),
            "core_within_factor_2": "%d/%d" % (within("log10_err_apriori", 2.0), len(core)),
            "core_spearman_evap_order": round(sp_apri, 6),
            "lift_over_geomean_null_pct": round(lift_apri, 3),
        },
        "joback_tc_guard": {
            "n_checks": len(tc_checks), "MAPE_pct": tc_mape, "checks": tc_checks,
        },
        "null_geomean_MAE_log10": round(null_mae, 5),
        "systematic_bias_note": ("a-priori path inherits Joback Tb error; because P0(25C) "
            "is exponentially sensitive to the boiling reference, a ~5 K Tb error moves P0 "
            "~15-20%. Reported, NOT corrected (a fitted correction would break "
            "non-circularity). The PHYSICS path isolates the Clausius-Clapeyron+Watson "
            "engine from that inherited Tb error."),
    }

    gates = {
        "G1_n_core>=12": len(core) >= 12,
        "G2_joback_tc_MAPE<=2pct": tc_mape <= 2.0,
        "G3_formula_guard_all_pass": True,  # asserted above or build() would have raised
        "G4_physics_MAE_log10<=0.05": phys_mae <= 0.05,
        "G5_physics_all_within_factor_1p5": within("log10_err_physics", 1.5) == len(core),
        "G6_apriori_MAE_log10<=0.12": apri_mae <= 0.12,
        "G7_apriori_spearman>=0.90": sp_apri >= 0.90,
        "G8_apriori_all_within_factor_2": within("log10_err_apriori", 2.0) == len(core),
        "G9_physics_lift>=60pct": lift_phys >= 60.0,
    }
    all_pass = all(gates.values())
    verdict = {
        "graded_outcome": "VALIDATED_IN_DOMAIN" if all_pass else "PARTIAL",
        "gate_passed": bool(all_pass),
        "gate_logic": ("PHYSICS path validates the Clausius-Clapeyron+Watson VOC engine "
            "(G4,G5,G9); A-PRIORI path validates the end-to-end structure->P0(25C) "
            "capability that consumes the Joback Tb + dHvap anchors (G6,G7,G8); Joback-Tc "
            "input cross-checked vs independent measured Tc (G2); RDKit formula guard (G3)."),
        "authority": "AUDIT_ONLY -- graded domain-of-applicability study, NOT a Phase-0 gate",
    }

    diag = {
        "schema": "amphora.redteam-audit.vapor-pressure-voc-clausius-clapeyron-ccby-v1.diagnostic.v1",
        "target_module": "amphora-molecule-property",
        "target_capability": ("a-priori 25 C saturated vapor pressure P0(298.15 K) for VOC "
            "content / regulatory compliance and fast/medium/slow evaporation-balance "
            "solvent-blend design in two-part epoxy-amine marine coatings; the absolute-"
            "volatility capstone consuming the anchored Joback Tb and dHvap axes and "
            "feeding amphora-sourceability-ehs (VOC) and amphora-solvency-score blends"),
        "theory": {
            "predictor": ("Clausius-Clapeyron d lnP/dT = dHvap(T)/(R T^2) integrated from "
                "the normal boiling point (P=101.325 kPa) to 298.15 K; dHvap(T) Watson-"
                "corrected dHvap(T)=dHvap(Tb)*((Tc-T)/(Tc-Tb))^0.38; Tc via Joback groups"),
            "predictor_citation": ("Clausius-Clapeyron (classical); Watson, Ind.Eng.Chem. "
                "1943, 35, 398; Joback&Reid, Chem.Eng.Commun. 1987, 57, 233; Poling/"
                "Prausnitz/O'Connell, Properties of Gases and Liquids 5th ed., Ch.7 & Table C-1"),
            "ground_truth": ("P0(298.15K) computed from NIST Chemistry WebBook Antoine "
                "constants (public domain) evaluated at 298.15 K -- independent of every "
                "model input; per-solvent Antoine reference cited in each row"),
            "non_circularity": ("Watson exponent, Joback tbk/tck and dHvap increments are "
                "universal published constants NOT fitted to this panel; the two consumed "
                "axes (Tb, dHvap) come from independently-signed anchors; truth P0 is an "
                "independent NIST measurement. No parameter is tuned on the validation set."),
            "trust_guards": ("(a) every Joback group multiset formula-checked vs RDKit; "
                "(b) Joback Tc cross-validated vs 8 independent measured critical temps; "
                "(c) two-replay byte-identical SHA-256 gate at signing"),
        },
        "rights": {
            "predictor_method": "Clausius-Clapeyron / Watson / Joback -- published theory, freely usable",
            "ground_truth_data": "NIST Chemistry WebBook Antoine constants -- U.S. Government work, public domain",
            "physical_constants": "M, measured Tc are tabulated CRC/NIST facts (non-copyrightable)",
            "rights_gate_passed": True,
            "in_scope": ("marine two-part epoxy-amine coating thinner/co-solvent chemistries "
                "(xylenes, toluene, MEK, MIBK, n-butyl acetate, esters, aliphatics); no "
                "adjacent-industry data"),
        },
        "n_solvents_total": len(rows),
        "n_solvents_core": len(core),
        "consumes_anchors": [
            "amphora-redteam-audit/joback-boiling-point-volatility-ccby-v1 (Tb)",
            "amphora-redteam-audit/joback-heat-of-vaporization-ccby-v1 (dHvap at Tb)",
        ],
        "phase0_reconciliation_redteam": phase0_reconciliation(),
        "kpis": kpis,
        "gates": gates,
        "verdict": verdict,
        "per_solvent": rows,
        "does_not": [
            "does NOT promote any module to PHASE_0 or change scientific_readiness",
            "does NOT modify any of the 66 signed manifest receipts or the master manifest",
            "does NOT claim product/VOC-compliance certification -- it is a predictive-model audit",
            "does NOT fit any parameter to the validation panel",
        ],
        "honest_limitations": [
            "alcohols (methanol, ethanol, 1-/2-propanol, 1-butanol) are boundary/out-of-domain: "
            "H-bond association is not captured by first-order Joback dHvap, so their P0 is "
            "reported but excluded from the core KPI (same domain call as the dHvap anchor)",
            "a-priori path is exponentially sensitive to inherited Joback Tb error; it is a "
            "strong VOC-ranking / order-of-magnitude tool, not a metrology-grade P0",
            "n=13 core solvents; a domain-of-applicability study, not a Phase-0 gate",
        ],
    }
    return diag


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()


if __name__ == "__main__":
    import sys
    diag = build()
    out = canonical(diag)
    dest = sys.argv[1] if len(sys.argv) > 1 else "diagnostic.out.json"
    with open(dest, "wb") as fh:
        fh.write(out)
    print("WROTE", dest, "sha256", hashlib.sha256(out).hexdigest())
    print("VERDICT", diag["verdict"]["graded_outcome"], "gate_passed", diag["verdict"]["gate_passed"])
    print("GATES", json.dumps(diag["gates"]))
    print("PHYSICS", json.dumps(diag["kpis"]["PHYSICS_path"]))
    print("APRIORI", json.dumps(diag["kpis"]["APRIORI_path"]))
    print("TC_GUARD_MAPE", diag["kpis"]["joback_tc_guard"]["MAPE_pct"])
