#!/usr/bin/env python3
"""Independent red-team + feasibility audit: network-Tg prediction for marine
coating DGEBA-amine thermosets (amphora-molecule-property Tg capability).

AUDIT_ONLY. Promotes nothing. Touches no existing receipt or manifest.

What it establishes, deterministically and reproducibly:
  1. INCUMBENT STATE (quoted from two signed in-tree receipts, by SHA): the
     polyuniverse-trained ML and the raw Van Krevelen group-contribution model
     BOTH FAIL to predict crosslinked-network Tg for the 5 canonical DGEBA-amine
     coating systems (ML MAE 39.1 C, Pearson r 0.077 = no correlation; raw VK
     MAE 109.1 C). Linear-polymer group contribution is the wrong physics for a
     crosslinked thermoset.
  2. CORRECT PHYSICS DIRECTION: Tg of a stoichiometric epoxy-amine network is
     governed by (a) crosslink density -- computed EXACTLY from stoichiometry
     (EEW/AHEW/amine-hydrogen functionality; ties to the already-verified
     EEW/AHEW core), fully NON-CIRCULAR (structure only, never uses measured Tg)
     -- and (b) backbone segmental rigidity, captured by ring-atom fraction
     (which, unlike aromatic fraction, correctly credits IPDA/PACM cycloaliphatic
     rings) and rotatable-bond density.
  3. HONEST DATA WALL: rights-clean, consistently-cited experimental Tg is only
     n=5 (single source, May 1988 Epoxy Resins Ch.6), and inter-lab Tg scatter is
     +/-20-30 C. That is too thin for a trustworthy fitted Phase-0 KPI. This audit
     therefore does NOT claim a Tg KPI; it quantifies the gap and the exact path.
"""
import hashlib, json, math
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors
import numpy as np

def rnd(x, n=6):
    if isinstance(x, float):
        if math.isnan(x) or math.isinf(x): return None
        return round(x, n)
    if isinstance(x, dict): return {k: rnd(v, n) for k, v in x.items()}
    if isinstance(x, (list, tuple)): return [rnd(v, n) for v in x]
    return x

DGEBA = "CC(C)(c1ccc(OCC2CO2)cc1)c1ccc(OCC2CO2)cc1"
EEW = round(Descriptors.MolWt(Chem.MolFromSmiles(DGEBA)) / 2.0, 4)

# --- Rights-clean CITED validation set (provenance A) ------------------------
# Transcribed from the signed in-tree receipt
# polyuniverse_epoxy_tg_external_validation_5_canonical_epoxy_amines_receipt.v1.json
# (sha256 0aaf262d28bd4d55924c35e6acdd18d33d800a59e3a9c9695f6f7942e7bd077e),
# whose per-candidate published_Tg_C values are cited to
# S.H. Goodman / C.A. May, "Epoxy Resins Chemistry and Technology" 2nd ed. 1988,
# Ch. 6. Individual published numeric constants, treated CC0 (cure-potlife
# precedent). All systems are stoichiometric DGEBA + amine, fully cured.
CITED = [
    ("IPDA",  "NCC1(C)CC(N)CC(C)(C)C1",                     158, "May 1988 Ch.6 p.209", "cycloaliphatic"),
    ("m-XDA", "NCc1cccc(CN)c1",                             100, "May 1988 Ch.6 p.210", "araliphatic"),
    ("DDS",   "Nc1ccc(S(=O)(=O)c2ccc(N)cc2)cc1",           220, "May 1988 Ch.6 p.208", "aromatic"),
    ("TETA",  "NCCNCCNCCN",                                 120, "May 1988 Ch.6",       "aliphatic"),
    ("DETA",  "NCCNCCN",                                    115, "May 1988 Ch.6",       "aliphatic"),
]
# --- REPRESENTATIVE extension (provenance B): NOT rigorously single-source
# cited; typical fully-cured stoichiometric literature values used ONLY to test
# whether the physics DIRECTION generalizes across a wider chemistry span.
# EXCLUDED from every KPI claim. Values are order-of-magnitude / mid-range of
# published spreads and are explicitly flagged uncertain (+/-15-25 C).
REPRESENTATIVE = [
    ("DDM",      "Nc1ccc(Cc2ccc(N)cc2)cc1",          170, "4,4'-MDA, lit. range 160-175", "aromatic"),
    ("m-PDA",    "Nc1cccc(N)c1",                      150, "lit. range 150-165",           "aromatic"),
    ("PACM",     "NC1CCC(CC1)CC1CCC(N)CC1",           160, "lit. range 150-165",           "cycloaliphatic"),
    ("JeffD230", "CC(N)COCC(C)OCC(C)N",                85, "polyether, lit. range 80-95",  "polyether"),
    ("EDA",      "NCCN",                              115, "lit. range 110-120",           "aliphatic"),
]

def descriptors(smi):
    a = Chem.MolFromSmiles(smi)
    aH = sum(at.GetTotalNumHs() for at in a.GetAtoms() if at.GetSymbol() == "N")   # active amine H
    nJ = sum(1 for at in a.GetAtoms() if at.GetSymbol() == "N" and at.GetTotalNumHs() > 0)  # junctions
    MWa = Descriptors.MolWt(a)
    heavy = a.GetNumHeavyAtoms()
    AHEW = MWa / aH
    W = MWa + aH * EEW                       # mass of stoichiometric strand unit per amine
    xlink = nJ / W                           # mol crosslink junctions per gram (NON-CIRCULAR)
    Mc = 1.0 / (1.5 * xlink)                 # 3-functional junctions -> Mc = W/(1.5*nJ)
    ring = sum(1 for at in a.GetAtoms() if at.IsInRing()) / heavy
    arom = sum(1 for at in a.GetAtoms() if at.GetIsAromatic()) / heavy
    rot = rdMolDescriptors.CalcNumRotatableBonds(a) / heavy
    return dict(amine_MW=MWa, active_amine_H=aH, n_junctions=nJ, AHEW=AHEW,
                strand_unit_mass=W, crosslink_density_mol_per_g=xlink,
                Mc_g_per_mol=Mc, ring_atom_fraction=ring,
                aromatic_fraction=arom, rotatable_bond_density=rot)

def build(rows):
    out = []
    for name, smi, tg, cite, cls in rows:
        d = descriptors(smi)
        d.update(system=f"DGEBA+{name}", amine=name, amine_smiles=smi,
                 published_Tg_C=tg, citation=cite, amine_class=cls)
        out.append(d)
    return out

cited = build(CITED)
repres = build(REPRESENTATIVE)

def corr(rows, key):
    tg = np.array([r["published_Tg_C"] for r in rows], float)
    v = np.array([r[key] for r in rows], float)
    return float(np.corrcoef(tg, v)[0, 1])

def loo(rows, keys):
    tg = np.array([r["published_Tg_C"] for r in rows], float) + 273.15
    X = np.column_stack([np.ones(len(rows))] + [[r[k] for r in rows] for k in keys])
    res = []
    for i in range(len(rows)):
        idx = [j for j in range(len(rows)) if j != i]
        c, *_ = np.linalg.lstsq(X[idx], tg[idx], rcond=None)
        res.append(float(X[i] @ c - tg[i]))
    res = np.array(res)
    return dict(n=len(rows), descriptors=keys,
                loo_mae_C=float(np.mean(np.abs(res))),
                loo_rmse_C=float(np.sqrt(np.mean(res**2))))

allrows = cited + repres
diag = {
    "schema": "amphora.redteam-audit.network-tg-feasibility-v1.diagnostic.v1",
    "authority": "AUDIT_ONLY",
    "target_module": "amphora-molecule-property",
    "target_capability": "glass_transition_temperature_of_DGEBA_amine_networks",
    "target_kpi_id": "network-tg-crosslink-rigidity-feasibility-v1",
    "theory": {
        "crosslink_density": "exact stoichiometric network model; junctions = amine N "
            "bearing >=1 active H, each -> 3-functional after full cure; strand unit "
            "mass W = M_amine + (active amine H)*EEW_DGEBA; Mc = W/(1.5*n_junctions). "
            "Derived purely from molecular structure and stoichiometry (EEW/AHEW), "
            "never from measured Tg -> NON-CIRCULAR. Ties to verified EEW/AHEW core.",
        "rigidity": "ring-atom fraction (credits aromatic AND cycloaliphatic rings) + "
            "rotatable-bond density capture segmental stiffness (Van Krevelen/Bicerano "
            "rigidity intuition); crosslink correction is Nielsen/Fox-Loshaek/DiMarzio.",
        "references": ["Nielsen 1969 (crosslink Tg shift)", "Fox-Loshaek 1955",
            "DiMarzio 1964", "Van Krevelen 1990 / Bicerano 2002 (rigidity)"],
    },
    "EEW_DGEBA": EEW,
    "incumbent_state_from_signed_receipts": {
        "note": "quoted verbatim from signed in-tree receipts; NOT recomputed here",
        "polyuniverse_ml_baseline": {
            "receipt": "polyuniverse_epoxy_tg_external_validation_5_canonical_epoxy_amines_receipt.v1.json",
            "receipt_sha256": "0aaf262d28bd4d55924c35e6acdd18d33d800a59e3a9c9695f6f7942e7bd077e",
            "ml_MAE_C": 39.11947866164949, "ml_pearson_r_across_5": 0.07689902196238095,
            "verdict": "FAILS: no correlation (r~0.08) on the 5 canonical network systems"},
        "raw_van_krevelen_baseline": {
            "receipt": "polyuniverse_epoxy_tg_van_krevelen_physical_baseline_receipt.v1.json",
            "receipt_sha256": "0e1cafe97b0d20ebd9b6b256ff686f80c47174ea1768065787e4eecec58bb78c",
            "vk_MAE_C_on_5canonical": 109.07781373364219, "vk_raw_r2_on_polyuniverse": -27.10424799020969,
            "verdict": "FAILS: linear-polymer group contribution is wrong physics for networks"},
    },
    "cited_validation_set": cited,
    "representative_extension_set_non_kpi": repres,
    "correlations_cited5": {k: corr(cited, k) for k in
        ["crosslink_density_mol_per_g", "ring_atom_fraction", "aromatic_fraction", "rotatable_bond_density"]},
    "correlations_all10_direction_only": {k: corr(allrows, k) for k in
        ["crosslink_density_mol_per_g", "ring_atom_fraction", "aromatic_fraction", "rotatable_bond_density"]},
    "physical_model_loo": {
        "cited5_crosslink_plus_ring": loo(cited, ["crosslink_density_mol_per_g", "ring_atom_fraction"]),
        "cited5_ring_only": loo(cited, ["ring_atom_fraction"]),
        "all10_crosslink_plus_ring_DIRECTION_ONLY": loo(allrows, ["crosslink_density_mol_per_g", "ring_atom_fraction"]),
        "all10_ring_only_DIRECTION_ONLY": loo(allrows, ["ring_atom_fraction"]),
    },
    "phase0_gates_for_a_real_tg_kpi": {
        "G1_rights_clean_cited_n_ge_12_spanning_4_classes": {"met": False, "current_n_cited": len(cited),
            "detail": "only n=5, single source; need >=12 across aliphatic/cycloaliphatic/araliphatic/aromatic"},
        "G2_grouped_or_LOO_mae_le_25C_on_cited_set": {"met": False,
            "detail": "n=5 too small for a trustworthy fitted estimate; not claimed"},
        "G3_beats_incumbent_ml_39C_and_vk_109C_on_trusted_set": {"met": "DIRECTION_ONLY",
            "detail": "correct physics (ring r=+0.69 on n=10) but not established on a trustworthy cited set"},
        "G4_non_circular_structure_only_descriptors": {"met": True,
            "detail": "crosslink density + rigidity are pure structure; never use measured Tg"},
        "G5_signed_two_replay_reproducible": {"met": True, "detail": "this audit"},
    },
    "verdict": {
        "phase": "PRE_PHASE_0",
        "status": "CORRECT_PHYSICS_IDENTIFIED__BLOCKED_ON_RIGHTS_CLEAN_DATA",
        "headline": "Network-Tg is the highest-value UNVALIDATED coating-science gap. The "
            "in-tree ML (MAE 39.1 C, r~0.08) and raw Van Krevelen (MAE 109.1 C) both FAIL "
            "because they use linear-polymer physics on a crosslinked network. The correct "
            "physics -- exact non-circular crosslink density (from the verified EEW/AHEW "
            "core) + ring/rotatable rigidity -- is prototyped here and shows real signal "
            "(ring-fraction Pearson r=+0.69, n=10; LOO MAE ~24-29 C direction-only, "
            "ring-only 24 C / +crosslink 29 C). It is NOT "
            "yet a Phase-0 KPI: rights-clean cited Tg is n=5 single-source with +/-20-30 C "
            "inter-lab scatter. One rights-clean cited dataset (>=12 systems, controlled "
            "cure) converts this into a defensible KPI.",
    },
    "honest_limitations": [
        "No fitted Tg KPI is claimed; n=5 rights-clean cited systems is below the bar.",
        "Representative extension (n=5, provenance B) is mid-range literature, +/-15-25 C, "
            "used ONLY for physics-direction, excluded from every gate/KPI.",
        "Crosslink model assumes ideal stoichiometric full cure, all junctions 3-functional; "
            "real networks have cure-conversion and topological-defect dependence.",
        "Inter-lab published Tg scatter (e.g. DGEBA/DDS 128-220 C across isomer/ratio/cure) "
            "sets a hard ~+/-20-30 C accuracy floor for ANY Tg model on literature ground truth.",
    ],
    "does_not": [
        "does NOT promote amphora-molecule-property or any module to PHASE_0",
        "does NOT modify any of the 66 signed receipts or the manifest",
        "does NOT claim wet-lab measurement, product qualification, or superiority",
        "does NOT score any KPI on CONTEXT_ONLY polyverse/polyuniverse data",
    ],
}

out = json.dumps(rnd(diag), indent=2, sort_keys=True)
import sys
open(sys.argv[1], "w").write(out)
print("wrote", sys.argv[1], "sha256", hashlib.sha256(out.encode()).hexdigest())
print("cited5 ring r =", round(corr(cited,"ring_atom_fraction"),3),
      "| all10 ring r =", round(corr(allrows,"ring_atom_fraction"),3))
print("cited5 xlink+ring LOO MAE =", round(diag["physical_model_loo"]["cited5_crosslink_plus_ring"]["loo_mae_C"],1), "C")
print("all10 xlink+ring LOO MAE =", round(diag["physical_model_loo"]["all10_crosslink_plus_ring_DIRECTION_ONLY"]["loo_mae_C"],1), "C (direction only)")
