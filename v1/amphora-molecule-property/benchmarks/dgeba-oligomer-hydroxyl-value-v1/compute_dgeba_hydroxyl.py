#!/usr/bin/env python3
"""AUDIT_ONLY second-signal for amphora-molecule-property (dgeba-oligomer-hydroxyl-value-v1).

NEW target property (distinct from the module's existing EEW/AHEW work): the HYDROXYL
VALUE (hydroxyl number) OHV of the linear DGEBA oligomer series, in mg KOH / g resin.

Chemistry: the fusion/advancement reaction that turns liquid n=0 DGEBA into higher
oligomers opens one epoxide against one bisphenol-A phenol per step, generating exactly
one SECONDARY ALIPHATIC hydroxyl (the 2-hydroxypropylene linker -O-CH2-CH(OH)-CH2-O-)
per repeat unit. A pure linear DGEBA oligomer of degree n therefore carries EXACTLY n
titratable hydroxyls and no phenolic or primary hydroxyls (every phenol is etherified
into a glycidyl/aryl ether). The published hydroxyl-number definition (ASTM D4274, mg
KOH consumed per g) gives

    OHV(n) = 56100 * n_OH / M(n)          [mg KOH / g]

with n_OH = n and M(n) = M0 + n * M_repeat the same additive molar-mass series already
locked by dgeba-oligomer-eew-series-v1 (M0 = M(C21H24O4), M_repeat = M(C18H20O3)). The
constant 56100 = 1000 * M(KOH) with M(KOH) = 56.1056 g/mol (IUPAC 2021).

This ties the hydroxyl value directly to the EEW advancement variable: the SAME integer n
that sets EEW(n) = (M0 + n*M_repeat)/2 sets n_OH, so OHV and EEW are two independent
structural read-outs of one advancement state. An independent RDKit-2026.03.2 build counts
total -OH and secondary-aliphatic -OH on each oligomer and must find them equal to each
other AND equal to n (no phenolic/primary OH present). Purely deterministic => byte-stable.

Primary sources:
  Lee & Neville, "Handbook of Epoxy Resins", McGraw-Hill 1967 (advancement/fusion reaction;
    secondary-OH generation per repeat unit; hydroxyl content of advanced grades).
  May (ed.), "Epoxy Resins: Chemistry and Technology", 2nd ed., Marcel Dekker 1988,
    ISBN 0-8247-7690-9.
  ASTM D4274, "Standard Test Methods for Testing Polyurethane Raw Materials:
    Determination of Hydroxyl Numbers of Polyols" (hydroxyl-number definition, 56100 factor).
  Prohaska et al., Pure Appl. Chem. 94(5):573 (2022), doi:10.1515/pac-2019-0603
    (IUPAC 2021 standard atomic weights; M(KOH) = 56.1056 g/mol).
"""
import json, hashlib
from pathlib import Path
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
DATA = ROOT / "amphora-molecule-property/reference/mvp20/data/eew_ahew_benchmark.v1.json"
KOH_FACTOR = 56100.0            # 1000 * M(KOH); ASTM D4274 hydroxyl-number constant

def r(x, k=4): return round(float(x), k)

# Same validated linear DGEBA oligomer SMILES used by dgeba-oligomer-eew-series-v1
# (n = 0..3; each retains 2 terminal epoxides and carries exactly n secondary OH).
OLIGO = {
  0: "C(C1CO1)Oc1ccc(cc1)C(C)(C)c1ccc(OCC2CO2)cc1",
  1: "C(C1CO1)Oc1ccc(cc1)C(C)(C)c1ccc(OCC(O)COc2ccc(cc2)C(C)(C)c2ccc(OCC3CO3)cc2)cc1",
  2: "C(C1CO1)Oc1ccc(cc1)C(C)(C)c1ccc(OCC(O)COc2ccc(cc2)C(C)(C)c2ccc(OCC(O)COc3ccc(cc3)C(C)(C)c3ccc(OCC4CO4)cc3)cc2)cc1",
  3: "C(C1CO1)Oc1ccc(cc1)C(C)(C)c1ccc(OCC(O)COc2ccc(cc2)C(C)(C)c2ccc(OCC(O)COc3ccc(cc3)C(C)(C)c3ccc(OCC(O)COc4ccc(cc4)C(C)(C)c4ccc(OCC5CO5)cc4)cc3)cc2)cc1",
}
EPOX  = Chem.MolFromSmarts("[OX2r3]1[CX4r3][CX4r3]1")
OH_ANY = Chem.MolFromSmarts("[OX2H]")                              # any hydroxyl O-H
OH_SEC = Chem.MolFromSmarts("[OX2H][CX4H1]([#6])[#6]")            # secondary aliphatic alcohol
OH_PRI = Chem.MolFromSmarts("[OX2H][CX4H2][#6]")                  # primary aliphatic alcohol
OH_PHE = Chem.MolFromSmarts("[OX2H]c")                            # phenolic (aromatic) OH

def analyze(smi):
    m = Chem.MolFromSmiles(smi)
    assert m is not None, smi
    return {"formula": rdMolDescriptors.CalcMolFormula(m),
            "molwt": Descriptors.MolWt(m),
            "n_epoxide": len(m.GetSubstructMatches(EPOX)),
            "oh_total": len(m.GetSubstructMatches(OH_ANY)),
            "oh_sec": len(m.GetSubstructMatches(OH_SEC)),
            "oh_pri": len(m.GetSubstructMatches(OH_PRI)),
            "oh_phe": len(m.GetSubstructMatches(OH_PHE))}

built = {n: analyze(smi) for n, smi in OLIGO.items()}
M0 = built[0]["molwt"]
M_repeat = built[1]["molwt"] - built[0]["molwt"]

def M(n):   return M0 + n * M_repeat
def ohv(n): return KOH_FACTOR * n / M(n)

# ---- G1: unadvanced n=0 monomer has ZERO hydroxyl number (structural anchor) ----
g1 = {"oh_total_n0": built[0]["oh_total"], "ohv_n0_mg_koh_per_g": r(ohv(0), 4),
      "passed": bool(built[0]["oh_total"] == 0 and abs(ohv(0)) < 1e-12)}

# ---- G2: per-oligomer OH count == n, and all n OH are secondary aliphatic ----
rows = []
g2_ok = True
for n in OLIGO:
    b = built[n]
    counts_ok = (b["oh_total"] == n) and (b["oh_sec"] == n) and (b["oh_pri"] == 0) and (b["oh_phe"] == 0)
    g2_ok = g2_ok and counts_ok
    rows.append({"n": n, "formula": b["formula"], "molwt_g_per_mol": r(b["molwt"], 4),
                 "n_epoxide": b["n_epoxide"], "oh_total": b["oh_total"],
                 "oh_secondary": b["oh_sec"], "oh_primary": b["oh_pri"], "oh_phenolic": b["oh_phe"],
                 "ohv_rule_mg_koh_per_g": r(ohv(n), 3), "counts_consistent": counts_ok})
g2 = {"rows": rows, "koh_factor": KOH_FACTOR, "M0_g_per_mol": r(M0, 4),
      "M_repeat_g_per_mol": r(M_repeat, 4), "passed": bool(g2_ok)}

# ---- G3: OHV monotone increasing, bounded by the C18H20O3-repeat asymptote 56100/M_repeat,
#          and the hydroxyl count equals the EEW advancement variable n for each oligomer ----
ohv_series = [ohv(n) for n in sorted(OLIGO)]
monotone = all(b > a for a, b in zip(ohv_series, ohv_series[1:]))
asymptote = KOH_FACTOR / M_repeat
below_asymptote = all(v < asymptote for v in ohv_series)
# advancement cross-consistency: n from mass == n from OH == n from (2 - retained epoxide)/... 
# every oligomer keeps 2 epoxides, so advancement n is read purely from OH count vs mass.
adv_consistent = all(built[n]["oh_total"] == round((built[n]["molwt"] - M0) / M_repeat) for n in OLIGO)
g3 = {"ohv_series_mg_koh_per_g": [r(v, 3) for v in ohv_series],
      "monotone_increasing": bool(monotone),
      "asymptote_mg_koh_per_g": r(asymptote, 3),
      "all_below_asymptote": bool(below_asymptote),
      "oh_count_equals_mass_advancement_n": bool(adv_consistent),
      "note": "OHV and EEW are two independent structural read-outs of one advancement "
              "variable n; asymptote = 56100 / M(C18H20O3 repeat).",
      "passed": bool(monotone and below_asymptote and adv_consistent)}

# ---- G4: fail-closed controls: OH present but NOT secondary-aliphatic advancement OH ----
CONTROLS = [
  {"name": "bisphenol-A (2 phenolic OH, precursor)", "smiles": "CC(C)(c1ccc(O)cc1)c1ccc(O)cc1",
   "expect_phe": 2, "expect_sec": 0},
  {"name": "glycidol (1 primary OH)", "smiles": "OCC1CO1", "expect_pri": 1, "expect_sec": 0},
  {"name": "neopentyl glycol (2 primary OH)", "smiles": "OCC(C)(C)CO", "expect_pri": 2, "expect_sec": 0},
  {"name": "DGEBA fully hydrolyzed diol (primary+secondary from opened epoxides, not oligomer)",
   "smiles": "OCC(O)COc1ccc(cc1)C(C)(C)c1ccc(OCC(O)CO)cc1", "expect_pri": 2, "expect_sec": 2},
]
g4_rows = []
for c in CONTROLS:
    a = analyze(c["smiles"])
    # An advancement-series member must have oh_sec == oh_total (only secondary aliphatic OH)
    # AND retain 2 terminal epoxides. Controls must FAIL that test => correctly excluded.
    is_series_member = (a["oh_total"] == a["oh_sec"]) and (a["oh_phe"] == 0) and (a["oh_pri"] == 0) and (a["n_epoxide"] == 2)
    matches_expect = (a["oh_phe"] == c.get("expect_phe", a["oh_phe"])) and \
                     (a["oh_pri"] == c.get("expect_pri", a["oh_pri"])) and \
                     (a["oh_sec"] == c.get("expect_sec", a["oh_sec"]))
    g4_rows.append({"name": c["name"], "oh_total": a["oh_total"], "oh_secondary": a["oh_sec"],
                    "oh_primary": a["oh_pri"], "oh_phenolic": a["oh_phe"], "n_epoxide": a["n_epoxide"],
                    "is_dgeba_advancement_series_member": is_series_member,
                    "expectation_matched": matches_expect,
                    "correctly_excluded": bool(matches_expect and not is_series_member)})
g4 = {"rows": g4_rows, "passed": all(x["correctly_excluded"] for x in g4_rows)}

# ---- atomic-weight uncertainty on OHV(n=1) (IUPAC 2021), propagated through M and M(KOH) ----
U = {"C": 0.0008, "H": 0.00007, "O": 0.00017, "K": 0.0001}  # IUPAC 2021 interval half-widths
# M(1) = C39H44O7 ; u from atom counts
c1 = {"C": 39, "H": 44, "O": 7}
u_M1 = (sum((c1[e] * U[e])**2 for e in c1))**0.5
# M(KOH)=K+O+H
u_koh = (U["K"]**2 + U["O"]**2 + U["H"]**2)**0.5
# OHV(1)=1000*M(KOH)/M(1); relative u in quadrature
ohv1 = ohv(1)
rel = ((u_koh / 56.1056)**2 + (u_M1 / M(1))**2)**0.5
u_ohv1 = ohv1 * rel
aw = {"target": "OHV(n=1)", "ohv1_mg_koh_per_g": r(ohv1, 4),
      "u_M1_g_per_mol": r(u_M1, 5), "u_MKOH_g_per_mol": r(u_koh, 6),
      "u_ohv1_mg_koh_per_g": r(u_ohv1, 6), "bar_mg_koh_per_g": 0.5,
      "headroom_factor": r(0.5 / u_ohv1, 1)}

diag = {
  "study_id": "dgeba-oligomer-hydroxyl-value-v1",
  "module": "amphora-molecule-property",
  "authority": "AUDIT_ONLY",
  "rule": "OHV(n) = 56100 * n / (M0 + n*M_repeat) [mg KOH/g] for the linear DGEBA "
          "oligomer series; n secondary aliphatic hydroxyls, zero phenolic/primary.",
  "rdkit_version_detected": Chem.rdBase.rdkitVersion,
  "koh_molar_mass_g_per_mol": 56.1056,
  "oligomers": {str(n): {"smiles": OLIGO[n], "formula": built[n]["formula"],
                         "molwt_g_per_mol": r(built[n]["molwt"], 4),
                         "oh_total": built[n]["oh_total"], "oh_secondary": built[n]["oh_sec"],
                         "ohv_mg_koh_per_g": r(ohv(n), 3)} for n in OLIGO},
  "gates": {"G1_monomer_zero_hydroxyl_number": g1,
            "G2_per_oligomer_oh_count_and_class": g2,
            "G3_monotone_bounded_advancement_consistent": g3,
            "G4_failclosed_non_advancement_oh_controls": g4},
  "atomic_weight_uncertainty": aw,
  "benchmark_data_sha256": hashlib.sha256(DATA.read_bytes()).hexdigest(),
  "primary_sources": ["Lee & Neville 1967 Handbook of Epoxy Resins (advancement/secondary-OH)",
                      "May 1988 Epoxy Resins 2nd ed ISBN 0-8247-7690-9",
                      "ASTM D4274 (hydroxyl number; 56100 factor)",
                      "Prohaska et al. Pure Appl. Chem. 94(5):573 (2022) doi:10.1515/pac-2019-0603"],
  "maps_to_module_hypothesis": "Adds a NEW molecular property (hydroxyl value, mg KOH/g) to "
      "the module's 'canonical structure rules reproduce locked known-answer equivalent "
      "weights' claim. OHV(n) is a second, independent structural read-out of the SAME "
      "advancement variable n that governs EEW(n), computed by independent RDKit OH "
      "classification, with fail-closed controls separating advancement secondary OH from "
      "phenolic/primary OH. Corroborative only: asserts no exact OHV for polydisperse "
      "commercial grades (composition is measured, not derived) and modifies no live lock.",
  "all_gates_passed": bool(g1["passed"] and g2["passed"] and g3["passed"] and g4["passed"]),
}
print(json.dumps(diag, indent=2, sort_keys=True))
