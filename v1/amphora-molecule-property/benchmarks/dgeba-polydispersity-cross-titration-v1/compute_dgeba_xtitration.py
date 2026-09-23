#!/usr/bin/env python3
"""AUDIT_ONLY second-signal for amphora-molecule-property
(dgeba-polydispersity-cross-titration-v1).

QUESTION. The module already ships two independent structural read-outs of the DGEBA
advancement state n: the epoxy equivalent weight EEW(n) = (M0 + n*Mr)/2 (receipt
dgeba-oligomer-eew-series-v1) and the hydroxyl value OHV(n) = 56100*n/(M0 + n*Mr)
(receipt dgeba-oligomer-hydroxyl-value-v1). Both were established on PURE single-n
oligomers. Real DGEBA is never a pure oligomer: it is a polydisperse mixture, and the
module's shipped inference inverts a measured commercial EEW BAND into a number-average
advancement n_bar. Two things were never tested:

  Q1 (invariance) Is the EEW -> n_bar inversion actually a property of the mixture, or
      only of a hypothetical single oligomer? i.e. do two resins with the SAME n_bar but
      very different dispersity read the same EEW and the same OHV?
  Q2 (robustness)  Commercial DGEBA carries non-ideal end groups - alpha-glycol ends from
      epoxide hydrolysis and chlorohydrin ends from residual bound chlorine (Lee &
      Neville 1967; May 1988). Does the inversion survive them?

THEORY (derived here, zero fitted parameters). For ANY mixture of ideal linear DGEBA
oligomers with mole fractions x_n, each molecule contributes EXACTLY 2 epoxide
equivalents and EXACTLY n hydroxyl equivalents, and mass is additive, so

    EEW_mix = (sum_n x_n M(n)) / (sum_n x_n * 2) = M_n / 2   = EEW(<n>)
    OHV_mix = 56100 * (sum_n x_n * n) / (sum_n x_n M(n))     = OHV(<n>)

Both titrations are ratios of number-averages of quantities LINEAR in n, so both depend
on the distribution ONLY through its first moment <n>. Neither sees dispersity at all
(no Jensen gap). Eliminating <n> between the two gives a closed-form, zero-parameter
CROSS-TITRATION IDENTITY between two independent ASTM methods:

    OHV = A * (1 - E0 / EEW),    A = 56100 / Mr = 197.29 mg KOH/g,  E0 = M0/2 = 170.21 g/eq

A and E0 are exactly the asymptote and the monomer anchor already signed by the two
prior receipts, so the identity is forced by them, not tuned to anything.

H0 UNDER TEST. "The EEW<->OHV identity, and hence the shipped EEW -> n_bar inversion, is
robust to realistic DGEBA end-group defects: a resin carrying up to 5 mol% alpha-glycol
and/or chlorohydrin ends still satisfies the identity within 1% relative."

Defect stoichiometry (per defective mole, both are epoxide-consuming end reactions):
  alpha-glycol end (epoxide + H2O):  epoxide 2->1, hydroxyl +2, mass + M(H2O)
  chlorohydrin end (epoxide + HCl):  epoxide 2->1, hydroxyl +1, mass + M(HCl)

Purely deterministic: closed-form distributions, no RNG, no timestamps, no network
=> byte-stable across replays.

Primary sources:
  Flory, P. J., "Molecular Size Distribution in Linear Condensation Polymers",
    J. Am. Chem. Soc. 58(10):1877-1885 (1936), doi:10.1021/ja01301a016
    (most-probable distribution x_n = (1-p) p^n).
  Lee, H. & Neville, K., "Handbook of Epoxy Resins", McGraw-Hill 1967
    (DGEBA advancement series; hydrolysis and bound-chlorine end groups of commercial
    epichlorohydrin-route resins).
  May, C. A. (ed.), "Epoxy Resins: Chemistry and Technology", 2nd ed., Marcel Dekker
    1988, ISBN 0-8247-7690-9.
  ASTM D1652 (epoxy equivalent weight by titration).
  ASTM D4274 (hydroxyl number; 56100 = 1000 * M(KOH)).
  Prohaska et al., Pure Appl. Chem. 94(5):573 (2022), doi:10.1515/pac-2019-0603
    (IUPAC 2021 standard atomic weights).
"""
import json, hashlib
from pathlib import Path
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-molecule-property"
DATA = MOD / "reference/mvp20/data/eew_ahew_benchmark.v1.json"
EEW_RECEIPT = MOD / "benchmarks/dgeba-oligomer-eew-series-v1/dgeba_oligomer_eew_series_receipt.v1.json"
OHV_RECEIPT = MOD / "benchmarks/dgeba-oligomer-hydroxyl-value-v1/dgeba_oligomer_hydroxyl_value_receipt.v1.json"

KOH_FACTOR = 56100.0          # ASTM D4274 hydroxyl-number constant = 1000 * M(KOH)
NMAX = 2000                   # distribution truncation for the Flory / Poisson series

def r(x, k=6): return round(float(x), k)

# ---------------------------------------------------------------- structural anchors
# Same validated linear DGEBA oligomer SMILES used by the two prior signed receipts.
OLIGO = {
  0: "C(C1CO1)Oc1ccc(cc1)C(C)(C)c1ccc(OCC2CO2)cc1",
  1: "C(C1CO1)Oc1ccc(cc1)C(C)(C)c1ccc(OCC(O)COc2ccc(cc2)C(C)(C)c2ccc(OCC3CO3)cc2)cc1",
  2: "C(C1CO1)Oc1ccc(cc1)C(C)(C)c1ccc(OCC(O)COc2ccc(cc2)C(C)(C)c2ccc(OCC(O)COc3ccc(cc3)C(C)(C)c3ccc(OCC4CO4)cc3)cc2)cc1",
  3: "C(C1CO1)Oc1ccc(cc1)C(C)(C)c1ccc(OCC(O)COc2ccc(cc2)C(C)(C)c2ccc(OCC(O)COc3ccc(cc3)C(C)(C)c3ccc(OCC(O)COc4ccc(cc4)C(C)(C)c4ccc(OCC5CO5)cc4)cc3)cc2)cc1",
}
EPOX = Chem.MolFromSmarts("[OX2r3]1[CX4r3][CX4r3]1")
OH_ANY = Chem.MolFromSmarts("[OX2H]")

def analyze(smi):
    m = Chem.MolFromSmiles(smi)
    assert m is not None, smi
    return {"formula": rdMolDescriptors.CalcMolFormula(m),
            "molwt": Descriptors.MolWt(m),
            "n_epoxide": len(m.GetSubstructMatches(EPOX)),
            "oh_total": len(m.GetSubstructMatches(OH_ANY))}

built = {n: analyze(s) for n, s in OLIGO.items()}
M0 = built[0]["molwt"]                       # C21H24O4  DGEBA n=0
Mr = built[1]["molwt"] - built[0]["molwt"]   # C18H20O3  advancement repeat
M_H2O = Descriptors.MolWt(Chem.MolFromSmiles("O"))     # hydrolysis adduct
M_HCl = Descriptors.MolWt(Chem.MolFromSmiles("Cl"))    # chlorohydrin adduct

A_ASYMPTOTE = KOH_FACTOR / Mr    # mg KOH/g   ceiling of the OHV series
E0_ANCHOR = M0 / 2.0             # g/eq       EEW of the unadvanced monomer

def M_of(n):    return M0 + n * Mr
def eew_of(n):  return M_of(n) / 2.0
def ohv_of(n):  return KOH_FACTOR * n / M_of(n)
def ohv_from_eew(eew):                       # the zero-parameter cross-titration identity
    return A_ASYMPTOTE * (1.0 - E0_ANCHOR / eew)
def nbar_from_eew(eew):                      # the module's shipped band -> n_bar inversion
    return (2.0 * eew - M0) / Mr

# ------------------------------------------------------------------ mixture machinery
def titrate(species):
    """species: list of (mole_fraction, molar_mass, epoxide_eq_per_mol, oh_eq_per_mol).
    Returns the two ASTM read-outs a lab would actually measure on the blend."""
    tot_x = sum(s[0] for s in species)
    mass = sum(s[0] * s[1] for s in species) / tot_x            # M_n
    epx = sum(s[0] * s[2] for s in species) / tot_x             # epoxide eq / mol
    oh = sum(s[0] * s[3] for s in species) / tot_x              # OH eq / mol
    mw = sum(s[0] * s[1] ** 2 for s in species) / sum(s[0] * s[1] for s in species)
    return {"Mn": mass, "Mw": mw, "dispersity": mw / mass,
            "eew": mass / epx, "ohv": KOH_FACTOR * oh / mass,
            "nbar_true": sum(s[0] * s[4] for s in species) / tot_x if len(species[0]) > 4 else None}

def ideal_species(x_by_n):
    return [(x, M_of(n), 2.0, float(n), float(n)) for n, x in x_by_n.items() if x > 0.0]

def flory(nbar, nmax=NMAX):
    """Flory 1936 most-probable distribution with mean advancement nbar."""
    p = nbar / (1.0 + nbar)
    w = {n: (1.0 - p) * p ** n for n in range(nmax + 1)}
    s = sum(w.values())
    return {n: v / s for n, v in w.items()}, s

def poisson(nbar, nmax=NMAX):
    w, term = {}, 1.0
    for n in range(nmax + 1):
        if n: term *= nbar / n
        w[n] = term
    s = sum(w.values())
    return {n: v / s for n, v in w.items()}, s

def bimodal(nbar, N):
    """Adversarial: only n=0 and n=N present, matched first moment, huge dispersity."""
    xN = nbar / N
    assert 0.0 < xN < 1.0
    return {0: 1.0 - xN, N: xN}, 1.0

# =========================================================== G1 cross-receipt parity
prev_eew = json.loads(EEW_RECEIPT.read_text())
prev_ohv = json.loads(OHV_RECEIPT.read_text())
pe = prev_eew["gates"]["G2_oligomer_additivity_difunctionality"]
po = prev_ohv["gates"]["G3_monotone_bounded_advancement_consistent"]
parity = [
    {"quantity": "M0_g_per_mol", "prior_signed": pe["M0_g_per_mol"], "rederived": r(M0, 4),
     "source_receipt": "dgeba-oligomer-eew-series-v1"},
    {"quantity": "M_repeat_g_per_mol", "prior_signed": pe["M_repeat_g_per_mol"], "rederived": r(Mr, 4),
     "source_receipt": "dgeba-oligomer-eew-series-v1"},
    {"quantity": "eew_slope_g_per_eq_per_n", "prior_signed": pe["eew_slope_g_per_eq_per_n"],
     "rederived": r(Mr / 2.0, 4), "source_receipt": "dgeba-oligomer-eew-series-v1"},
    {"quantity": "ohv_asymptote_mg_koh_per_g", "prior_signed": po["asymptote_mg_koh_per_g"],
     "rederived": r(A_ASYMPTOTE, 3), "source_receipt": "dgeba-oligomer-hydroxyl-value-v1"},
]
for n in ("1", "2", "3"):
    parity.append({"quantity": "ohv_n%s_mg_koh_per_g" % n,
                   "prior_signed": prev_ohv["oligomers"][n]["ohv_mg_koh_per_g"],
                   "rederived": r(ohv_of(int(n)), 3),
                   "source_receipt": "dgeba-oligomer-hydroxyl-value-v1"})
for row in parity:
    row["abs_diff"] = r(abs(row["prior_signed"] - row["rederived"]), 9)
    row["matches"] = row["abs_diff"] <= 5e-4
# the identity must reproduce the pure-oligomer OHV exactly (algebraic closure check)
closure = max(abs(ohv_from_eew(eew_of(n)) - ohv_of(n)) for n in range(0, 21))
g1 = {"rows": parity, "identity_A_mg_koh_per_g": r(A_ASYMPTOTE, 4),
      "identity_E0_g_per_eq": r(E0_ANCHOR, 4),
      "identity_form": "OHV = A * (1 - E0/EEW)",
      "max_identity_vs_pure_oligomer_deviation_mg_koh_per_g": r(closure, 12),
      "passed": bool(all(x["matches"] for x in parity) and closure < 1e-9)}

# ================================================= G2 polydispersity invariance (Q1)
TARGETS = [
    {"grade": "liquid (Epon 828 / DER 331 class)", "nbar": 0.13},
    {"grade": "semisolid (Epon 1001F / DER 671 class)", "nbar": 2.35},
    {"grade": "solid (Epon 1004F / DER 664 class)", "nbar": 4.90},
]
g2_rows, g2_ok = [], True
for t in TARGETS:
    fam = {}
    d, _ = flory(t["nbar"]);   fam["flory_most_probable"] = d
    d, _ = poisson(t["nbar"]); fam["poisson"] = d
    fam["bimodal_n0_n8"] = bimodal(t["nbar"], 8)[0] if t["nbar"] < 8 else bimodal(t["nbar"], 12)[0]
    fam["bimodal_n0_n40"] = bimodal(t["nbar"], 40)[0]
    sub = []
    for name, dist in fam.items():
        sp = ideal_species(dist)
        tt = titrate(sp)
        nbar_actual = tt["nbar_true"]                       # exact first moment of the mixture used
        dev_eew = abs(tt["eew"] - eew_of(nbar_actual))
        dev_ohv = abs(tt["ohv"] - ohv_of(nbar_actual))
        dev_id = abs(tt["ohv"] - ohv_from_eew(tt["eew"]))   # the cross-titration identity
        inv_err = abs(nbar_from_eew(tt["eew"]) - nbar_actual)
        ok = dev_eew < 1e-9 and dev_ohv < 1e-9 and dev_id < 1e-9 and inv_err < 1e-9
        g2_ok = g2_ok and ok
        sub.append({"distribution": name, "nbar_actual": r(nbar_actual, 9),
                    "dispersity_Mw_over_Mn": r(tt["dispersity"], 6),
                    "eew_mixture_g_per_eq": r(tt["eew"], 6),
                    "ohv_mixture_mg_koh_per_g": r(tt["ohv"], 6),
                    "dev_eew_vs_single_oligomer_formula": r(dev_eew, 12),
                    "dev_ohv_vs_single_oligomer_formula": r(dev_ohv, 12),
                    "dev_cross_titration_identity": r(dev_id, 12),
                    "nbar_inversion_error": r(inv_err, 12), "invariant": bool(ok)})
    disp = [s["dispersity_Mw_over_Mn"] for s in sub]
    eews = [s["eew_mixture_g_per_eq"] for s in sub]
    g2_rows.append({"grade": t["grade"], "nbar_target": t["nbar"],
                    "dispersity_range": [min(disp), max(disp)],
                    "dispersity_fold_span": r(max(disp) / min(disp), 4),
                    "eew_spread_across_distributions_g_per_eq": r(max(eews) - min(eews), 9),
                    "distributions": sub})
g2 = {"rows": g2_rows, "truncation_nmax": NMAX,
      "claim": "EEW and OHV of an ideal linear DGEBA mixture depend on the distribution "
               "ONLY through its first moment <n>; both are exactly dispersity-invariant, "
               "so the shipped EEW -> n_bar inversion is a genuine mixture property.",
      "passed": bool(g2_ok)}

# ============================================ G3 H0: robustness to end-group defects
def defected(nbar, phi, psi):
    """Ideal Flory core at <n>=nbar, with mole fraction phi carrying one alpha-glycol end
    and psi carrying one chlorohydrin end (both consume one terminal epoxide)."""
    dist, _ = flory(nbar)
    core = ideal_species(dist)
    ideal_frac = 1.0 - phi - psi
    sp = [(x * ideal_frac, M, e, oh, n) for (x, M, e, oh, n) in core]
    # defective chains drawn from the same advancement distribution
    sp += [(x * phi, M + M_H2O, 1.0, oh + 2.0, n) for (x, M, e, oh, n) in core]
    sp += [(x * psi, M + M_HCl, 1.0, oh + 1.0, n) for (x, M, e, oh, n) in core]
    return sp

H0_REL_BAR = 0.01
g3_rows, refuting = [], []
for nb in (0.13, 2.35):
    for phi, psi in [(0.0, 0.0), (0.005, 0.0), (0.01, 0.0), (0.02, 0.0), (0.03, 0.0),
                     (0.05, 0.0), (0.0, 0.01), (0.0, 0.02), (0.01, 0.01), (0.02, 0.03)]:
        tt = titrate(defected(nb, phi, psi))
        pred = ohv_from_eew(tt["eew"])
        delta = tt["ohv"] - pred
        rel = delta / pred if pred > 0 else float("inf")
        n_hat = nbar_from_eew(tt["eew"])
        row = {"nbar_true": nb, "phi_glycol_molfrac": phi, "psi_chlorohydrin_molfrac": psi,
               "total_defect_molfrac": r(phi + psi, 6),
               "eew_measured_g_per_eq": r(tt["eew"], 4),
               "ohv_measured_mg_koh_per_g": r(tt["ohv"], 4),
               "ohv_predicted_by_identity_mg_koh_per_g": r(pred, 4),
               "residual_delta_mg_koh_per_g": r(delta, 4),
               "residual_relative": r(rel, 6),
               "nbar_inferred_from_eew": r(n_hat, 4),
               "nbar_inversion_bias": r(n_hat - nb, 4),
               "nbar_inversion_relative_bias": r((n_hat - nb) / nb, 6),
               "exceeds_1pct_identity_bar": bool(abs(rel) > H0_REL_BAR)}
        g3_rows.append(row)
        if phi + psi >= 0.01 and abs(rel) > H0_REL_BAR:
            refuting.append(row)
zero_defect = [x for x in g3_rows if x["total_defect_molfrac"] == 0.0]
specific = all(abs(x["residual_relative"]) < 1e-9 for x in zero_defect)
tested = [x for x in g3_rows if x["total_defect_molfrac"] >= 0.01]
# H0 is a UNIVERSAL claim ("<=1% for up to 5 mol%"); a single counterexample refutes it.
h0_refuted = len(refuting) >= 1
# dose-response monotonicity: residual must rise strictly with glycol load at psi=0.
mono = True
for nb in (0.13, 2.35):
    leg = [x for x in g3_rows if x["nbar_true"] == nb and x["psi_chlorohydrin_molfrac"] == 0.0]
    leg.sort(key=lambda x: x["phi_glycol_molfrac"])
    seq = [x["residual_relative"] for x in leg]
    mono = mono and all(b > a for a, b in zip(seq, seq[1:]))
# stratification: the detector's RELATIVE power collapses as the resin advances, because
# the defect hydroxyl rides on an ever larger ideal-backbone hydroxyl baseline.
strata = []
for nb in (0.13, 2.35):
    leg = [x for x in g3_rows if x["nbar_true"] == nb and x["total_defect_molfrac"] >= 0.01]
    br = [x for x in leg if x["exceeds_1pct_identity_bar"]]
    base = titrate(defected(nb, 0.0, 0.0))
    one_pct = [x for x in g3_rows if x["nbar_true"] == nb
               and x["phi_glycol_molfrac"] == 0.01 and x["psi_chlorohydrin_molfrac"] == 0.0][0]
    strata.append({"nbar": nb, "eew_ideal_g_per_eq": r(base["eew"], 4),
                   "ohv_ideal_mg_koh_per_g": r(base["ohv"], 4),
                   "defect_rows_tested": len(leg), "defect_rows_breaching_1pct_bar": len(br),
                   "relative_residual_per_molpct_glycol": r(one_pct["residual_relative"] / 1.0, 6),
                   "nbar_relative_bias_at_1molpct_glycol": one_pct["nbar_inversion_relative_bias"]})
sens_ratio = strata[0]["relative_residual_per_molpct_glycol"] / strata[1]["relative_residual_per_molpct_glycol"]
g3 = {"H0": "The EEW<->OHV cross-titration identity (and hence the EEW -> n_bar inversion) "
            "is robust to realistic DGEBA end-group defects: <=1% relative residual for up "
            "to 5 mol% alpha-glycol and/or chlorohydrin ends.",
      "rows": g3_rows,
      "defect_rows_tested_at_or_above_1molpct": len(tested),
      "defect_rows_breaching_1pct_bar": len(refuting),
      "zero_defect_rows_exactly_on_identity": bool(specific),
      "dose_response_monotone_in_glycol_load": bool(mono),
      "max_residual_relative": r(max(abs(x["residual_relative"]) for x in g3_rows), 6),
      "max_nbar_relative_bias": r(max(abs(x["nbar_inversion_relative_bias"]) for x in g3_rows), 6),
      "stratification_by_advancement": strata,
      "relative_sensitivity_loss_liquid_to_semisolid_fold": r(sens_ratio, 2),
      "verdict": "H0_REFUTED" if h0_refuted else "H0_NOT_REFUTED",
      "refutation_basis": "Universal claim refuted by counterexample: %d of %d defect rows at "
            ">=1 mol%% total defect breach the 1%% relative bar, worst case %s relative. The "
            "breach is NOT uniform, and the non-uniformity is the second finding." % (
                len(refuting), len(tested),
                r(max(abs(x["residual_relative"]) for x in g3_rows), 4)),
      "interpretation": "Two distinct results. (i) The invariance proved in G2 is an "
            "IDEAL-SERIES property only: it survives arbitrary polydispersity but NOT "
            "epoxide-consuming end groups, which add hydroxyl and remove epoxide "
            "simultaneously and so move EEW and OHV off the one-parameter curve in different "
            "directions. The residual is therefore not noise - it is a zero-parameter "
            "DETECTOR of non-ideal DGEBA, monotone in defect load. (ii) The detector's power "
            "is strongly GRADE-DEPENDENT. On low-advancement liquid grades every defect row "
            "breaches the bar, because the ideal hydroxyl baseline is small and the two extra "
            "OH per hydrolyzed end are a large relative perturbation. On advanced grades the "
            "backbone already carries a large ideal OHV, the same defect is a small relative "
            "perturbation, and only the heavier loads breach. Relative sensitivity therefore "
            "falls by ~%sx from the liquid to the semisolid grade, so a single fixed relative "
            "acceptance bar is NOT a valid QC rule across the DGEBA grade range." % r(sens_ratio, 1),
      "passed": bool(h0_refuted and specific and mono)}

# ================================ G4 detector sensitivity + fail-closed specificity
h = 1e-6
sens = []
for nb in (0.13, 2.35):
    base_eew = titrate(defected(nb, 0.0, 0.0))["eew"]
    out = []
    for label, (dphi, dpsi) in (("alpha_glycol", (h, 0.0)), ("chlorohydrin", (0.0, h))):
        tt = titrate(defected(nb, dphi, dpsi))
        d = tt["ohv"] - ohv_from_eew(tt["eew"])
        out.append({"defect": label, "d_delta_d_molpct_mg_koh_per_g": r(d / (h * 100.0), 4)})
    sens.append({"nbar": nb, "eew_ideal_g_per_eq": r(base_eew, 4), "sensitivities": out})

# parametric detection floor: u(delta)^2 = (sigma*OHV)^2 + (A*E0/EEW^2)^2 * (sigma*EEW)^2
det = []
for s in sens:
    nb = s["nbar"]
    tt = titrate(defected(nb, 0.0, 0.0))
    dpdE = A_ASYMPTOTE * E0_ANCHOR / tt["eew"] ** 2
    slope = [o for o in s["sensitivities"] if o["defect"] == "alpha_glycol"][0]["d_delta_d_molpct_mg_koh_per_g"]
    rows = []
    for sig in (0.005, 0.01, 0.02):
        u = ((sig * tt["ohv"]) ** 2 + (dpdE * sig * tt["eew"]) ** 2) ** 0.5
        rows.append({"assumed_relative_titration_precision": sig,
                     "u_residual_mg_koh_per_g": r(u, 4),
                     "min_detectable_glycol_molpct_k2": r(2.0 * u / slope, 4)})
    det.append({"nbar": nb, "ohv_ideal_mg_koh_per_g": r(tt["ohv"], 4), "floors": rows})

# specificity controls: non-ideal-DGEBA blends must be FLAGGED, ideal must NOT be
PGE = analyze("C(C1CO1)Oc1ccccc1")                                     # phenyl glycidyl ether
BPA = analyze("CC(C)(c1ccc(O)cc1)c1ccc(O)cc1")                         # free bisphenol-A
base_dist, _ = flory(0.13)
ctrl_rows = []
CONTROLS = [
    {"name": "ideal Flory DGEBA, no additive (TRUE NEGATIVE)", "frac": 0.0, "add": None,
     "should_flag": False},
    {"name": "20 mol%% phenyl glycidyl ether monofunctional diluent", "frac": 0.20,
     "add": (PGE["molwt"], 1.0, 0.0), "should_flag": True},
    {"name": "10 mol%% free bisphenol-A (unreacted precursor)", "frac": 0.10,
     "add": (BPA["molwt"], 0.0, 2.0), "should_flag": True},
    {"name": "5 mol%% fully hydrolyzed DGEBA diol (both epoxides opened)", "frac": 0.05,
     "add": (M0 + 2 * M_H2O, 0.0, 4.0), "should_flag": True},
]
for c in CONTROLS:
    sp = [(x * (1.0 - c["frac"]), M_of(n), 2.0, float(n), float(n)) for n, x in base_dist.items() if x > 0]
    if c["add"]:
        sp.append((c["frac"], c["add"][0], c["add"][1], c["add"][2], 0.0))
    tt = titrate(sp)
    pred = ohv_from_eew(tt["eew"])
    rel = (tt["ohv"] - pred) / pred
    flagged = abs(rel) > H0_REL_BAR
    ctrl_rows.append({"name": c["name"] % () if "%%" not in c["name"] else c["name"].replace("%%", "%"),
                      "eew_g_per_eq": r(tt["eew"], 4), "ohv_mg_koh_per_g": r(tt["ohv"], 4),
                      "identity_prediction_mg_koh_per_g": r(pred, 4),
                      "residual_relative": r(rel, 6), "flagged_non_ideal": bool(flagged),
                      "should_flag": c["should_flag"],
                      "correct": bool(flagged == c["should_flag"])})
g4 = {"sensitivity": sens, "parametric_detection_floor": det,
      "detection_floor_note": "The assumed relative titration precisions are PARAMETRIC "
            "sensitivity inputs chosen by this audit, NOT quoted ASTM D1652/D4274 precision "
            "statements; no repeatability figure is claimed from the standards.",
      "specificity_controls": ctrl_rows,
      "passed": bool(all(x["correct"] for x in ctrl_rows))}

# ------------------------------------------------- atomic-weight uncertainty headroom
U = {"C": 0.0008, "H": 0.00007, "O": 0.00017}     # IUPAC 2021 interval half-widths
u_M0 = (sum((c * U[e]) ** 2 for e, c in (("C", 21), ("H", 24), ("O", 4))))**0.5
u_A = A_ASYMPTOTE * ((sum((c * U[e]) ** 2 for e, c in (("C", 18), ("H", 20), ("O", 3))))**0.5) / Mr
smallest_signal = min(abs(x["residual_delta_mg_koh_per_g"]) for x in g3_rows
                      if x["total_defect_molfrac"] >= 0.01)
aw = {"u_M0_g_per_mol": r(u_M0, 6), "u_identity_A_mg_koh_per_g": r(u_A, 6),
      "smallest_refuting_residual_mg_koh_per_g": r(smallest_signal, 4),
      "signal_to_atomic_weight_uncertainty": r(smallest_signal / u_A, 1)}

diag = {
  "study_id": "dgeba-polydispersity-cross-titration-v1",
  "module": "amphora-molecule-property",
  "authority": "AUDIT_ONLY",
  "rule": "Ideal linear DGEBA mixtures obey the zero-parameter cross-titration identity "
          "OHV = A*(1 - E0/EEW) with A = 56100/M_repeat = %s mg KOH/g and E0 = M0/2 = %s "
          "g/eq, exactly and independently of dispersity." % (r(A_ASYMPTOTE, 2), r(E0_ANCHOR, 2)),
  "rdkit_version_detected": Chem.rdBase.rdkitVersion,
  "structural_constants": {"M0_g_per_mol": r(M0, 4), "M_repeat_g_per_mol": r(Mr, 4),
                           "M_H2O_g_per_mol": r(M_H2O, 4), "M_HCl_g_per_mol": r(M_HCl, 4),
                           "koh_factor": KOH_FACTOR},
  "gates": {"G1_cross_receipt_parity_and_identity_closure": g1,
            "G2_polydispersity_invariance": g2,
            "G3_H0_end_group_defect_robustness": g3,
            "G4_detector_sensitivity_and_specificity": g4},
  "atomic_weight_uncertainty": aw,
  "benchmark_data_sha256": hashlib.sha256(DATA.read_bytes()).hexdigest(),
  "prior_receipt_sha256": {
      "dgeba_oligomer_eew_series_receipt.v1.json": hashlib.sha256(EEW_RECEIPT.read_bytes()).hexdigest(),
      "dgeba_oligomer_hydroxyl_value_receipt.v1.json": hashlib.sha256(OHV_RECEIPT.read_bytes()).hexdigest()},
  "primary_sources": [
      "Flory, J. Am. Chem. Soc. 58(10):1877 (1936), doi:10.1021/ja01301a016",
      "Lee & Neville 1967 Handbook of Epoxy Resins",
      "May 1988 Epoxy Resins: Chemistry and Technology 2nd ed ISBN 0-8247-7690-9",
      "ASTM D1652", "ASTM D4274",
      "Prohaska et al. Pure Appl. Chem. 94(5):573 (2022) doi:10.1515/pac-2019-0603"],
  "maps_to_module_hypothesis": "Tests the mixture-level validity of the module's shipped "
      "EEW-band -> n_bar advancement inversion. Establishes that the inversion is exactly "
      "dispersity-invariant (a strictly stronger result than the pure-oligomer receipts "
      "supported), and REFUTES the implicit robustness assumption behind it by showing that "
      "epoxide-consuming end groups bias it while simultaneously breaking the EEW<->OHV "
      "identity - which converts the identity into a zero-parameter QC detector whose power "
      "is quantified here, and shown to be grade-dependent rather than uniform.",
  "all_gates_passed": bool(g1["passed"] and g2["passed"] and g3["passed"] and g4["passed"]),
}
print(json.dumps(diag, indent=2, sort_keys=True))
