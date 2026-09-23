#!/usr/bin/env python3
"""amphora-molecule-generator R-S06 adversarial probe of the SA<6 feasibility
gate and the RDKit-parse validity gate asserted by
evidence/audit/molgen-quality-feasibility-baseline-v1 (verdict
CORROBORATED_IN_AUDIT_INSTRUMENT: "all_proposals_feasible" / SA<6, and
"validity"==1.0 on the in-scope set).

Deterministic, timing-free AUDIT_ONLY diagnostic. Three independent attack
families against the same target receipt, run against the SAME pinned
RDKit build, the SAME SA_Score reference implementation
(Ertl & Schuffenhauer 2009, J. Cheminform. 1:8), and the SAME locked PI1M
reference artifact already consulted (rights_class CONTEXT_ONLY,
non-scored) by the target receipt -- no new data acquisition.

Family 1 -- known-hard-to-synthesize structures scoring SA<6 (false feasible):
  Three Platonic/near-Platonic strained hydrocarbon cages, each with a
  primary-literature synthesis citation establishing genuine synthetic
  difficulty (low yield, hazardous, and/or a landmark multi-step total
  synthesis), tested against the exact SA_Score reference implementation
  the target receipt validates and relies on.
    - cubane C8H8: Eaton & Cole 1964, J. Am. Chem. Soc. 86(15):3157-3158.
      First synthesis; highly strained (~695 kJ/mol strain energy),
      historically hazardous/explosive derivatives, specialized route.
    - prismane C6H6: Katz & Acton 1973, J. Am. Chem. Soc. 95(8):2738-2739.
      First synthesis via photolysis of an azo precursor at -196C,
      <10% yield, explosive (~682 kJ/mol strain energy).
    - dodecahedrane C20H20: Paquette 1982, J. Am. Chem. Soc. 104(16):
      4503-4504. ~29-step landmark total synthesis, one of the most
      celebrated multi-step total syntheses in organic chemistry
      specifically because of its difficulty.

Family 2 -- trivially-valid-but-degenerate SMILES passing the validity gate:
  Inputs that Chem.MolFromSmiles() accepts (non-None) but that are not
  coherent single covalent candidate molecules: a bare wildcard/dummy atom,
  isolated noble-gas atoms, disconnected multi-fragment mixtures
  (including an ionic salt), and isotope-only diatomics. The target
  receipt's metric_validity() checks ONLY `MolFromSmiles(smi) is not None`
  with no connectivity, fragment-count, or organic-content check.

Family 3 -- boundary probing at SA 5.9-6.1:
  The target receipt's own known-answer block already measures and
  DISMISSES a residual: {n_divergent} PI1M rows where the reference
  SA_Score reproduction differs from the shipped ground-truth SA Score
  column by more than the 1e-4 known-answer tolerance (up to 0.66 SA
  units), attributed to "documented RDKit-version sensitivity...confined
  to exotic heteroaromatic polymer motifs" and dismissed because
  "coating hardeners use only common fragments...that fall in the
  exactly-reproduced majority." This family tests that dismissal
  directly: does the admitted divergence intersect the SA=6.0 decision
  boundary specifically (not just the bulk exact-reproduction-fraction
  gate), and does it flip any row's feasible/infeasible verdict.

Usage: run_sa_validity_adversarial_probe.py <out.json>
"""
import gzip
import json
import os
import sys

import rdkit
from rdkit import Chem, RDLogger
from rdkit.Chem import RDConfig, rdMolDescriptors

RDLogger.DisableLog("rdApp.*")
sys.path.append(os.path.join(RDConfig.RDContribDir, "SA_Score"))
import sascorer  # noqa: E402

ROOT = "/home/ubuntu/amphora/build/mvp20-split"
MODDIR = os.path.join(ROOT, "amphora-molecule-generator")
TARGET_RECEIPT_REL = ("evidence/audit/molgen-quality-feasibility-baseline-v1/"
                       "molgen-quality-feasibility-baseline-receipt.v1.dsse.json")
PI1M_REL = ("reference/mvp20/quarantine/feedback_v2/objects/"
            "fe23c6d1e4b50bd37a231be6b5db50cbc30e71f5252fd4b5c0d91430cf8cee17.jsonl.gz")
PI1M_PATH = os.path.join(MODDIR, PI1M_REL)
PI1M_LOCKED_SHA = "fe23c6d1e4b50bd37a231be6b5db50cbc30e71f5252fd4b5c0d91430cf8cee17"
PREFIX_N = 20000                # identical deterministic archive-order prefix used by target
SA_FEASIBLE_MAX = 6.0
SA_KA_TOL = 1e-4
BOUNDARY_LO, BOUNDARY_HI = 5.9, 6.1


def sa_of(mol):
    return sascorer.calculateScore(mol)


# ============================================================================
# FAMILY 1 -- known-hard-to-synthesize structures scoring SA<6
# ============================================================================
KNOWN_HARD = [
    {
        "name": "cubane",
        "smiles": "C12C3C4C1C5C2C3C45",
        "formula_expected": "C8H8",
        "citation": "Eaton & Cole 1964, J. Am. Chem. Soc. 86(15):3157-3158",
        "hardness_evidence": (
            "First synthesis of a Platonic hydrocarbon cage; ~695 kJ/mol "
            "angle strain (109.5deg tetrahedral carbons forced to 90deg "
            "cube vertices); specialized multi-step route from "
            "2-cyclopentenone via base-mediated dimerization/rearrangement; "
            "derivatives historically hazardous (energetic-materials use)."),
    },
    {
        "name": "prismane",
        "smiles": "C12C3C1C4C2C34",
        "formula_expected": "C6H6",
        "citation": "Katz & Acton 1973, J. Am. Chem. Soc. 95(8):2738-2739",
        "hardness_evidence": (
            "First synthesis via photolysis of an azo precursor derived "
            "from benzvalene at -196C through a biradical intermediate, "
            "<10% yield; ~682 kJ/mol ring strain (60deg C-C-C angles vs "
            "109.5deg ideal); explosive."),
    },
    {
        "name": "dodecahedrane",
        "smiles": "C12C3C4C5C1C6C7C2C8C3C9C4C1C5C6C2C7C8C9C12",
        "formula_expected": "C20H20",
        "citation": "Paquette 1982, J. Am. Chem. Soc. 104(16):4503-4504",
        "hardness_evidence": (
            "~29-step total synthesis, widely cited as one of the most "
            "celebrated multi-step total syntheses in organic chemistry "
            "history specifically because of its extreme difficulty; "
            "pursued for its aesthetic dodecahedral symmetry, not "
            "practical availability."),
    },
]

family1_results = []
family1_slips = []
for entry in KNOWN_HARD:
    m = Chem.MolFromSmiles(entry["smiles"])
    valid = m is not None
    formula = rdMolDescriptors.CalcMolFormula(m) if valid else None
    sa = sa_of(m) if valid else None
    n_atoms = m.GetNumAtoms() if valid else None
    n_chiral = len(Chem.FindMolChiralCenters(m, includeUnassigned=True)) if valid else None
    ri = m.GetRingInfo() if valid else None
    n_bridge = rdMolDescriptors.CalcNumBridgeheadAtoms(m) if valid else None
    n_spiro = rdMolDescriptors.CalcNumSpiroAtoms(m) if valid else None
    n_macro = sum(1 for r in ri.AtomRings() if len(r) > 8) if valid else None
    slips = bool(valid and sa is not None and sa < SA_FEASIBLE_MAX)
    row = {
        "name": entry["name"], "smiles": entry["smiles"],
        "citation": entry["citation"], "hardness_evidence": entry["hardness_evidence"],
        "valid": valid, "formula_observed": formula,
        "formula_matches_expected": (formula == entry["formula_expected"]),
        "sa_score": round(sa, 6) if sa is not None else None,
        "n_atoms": n_atoms, "n_chiral_centers_detected": n_chiral,
        "n_bridgehead_atoms": n_bridge, "n_spiro_atoms": n_spiro,
        "n_macrocycles_gt8": n_macro,
        "slips_through_as_false_feasible": slips,
        "why_it_slips": (
            "Fragment score is dominated by common small aliphatic CH2/CH "
            "substructures (frequent in the PubChem training corpus); the "
            "cage's high vertex/bond symmetry triggers the fingerprint-"
            "density symmetry bonus (score3, sascorer.py 'not in the "
            "original publication...to make highly symmetrical molecules "
            "easier to synthesise'); the algorithm has NO ring-strain term "
            "at all, so 682-695 kJ/mol of angle strain that drove decades "
            "of synthetic effort is structurally invisible to the score."
        ) if slips else None,
    }
    family1_results.append(row)
    if slips:
        family1_slips.append(entry["name"])

family1_summary = {
    "attack": "known_hard_to_synthesize_structures_scoring_sa_below_6",
    "n_attempted": len(KNOWN_HARD),
    "n_slipped_through": len(family1_slips),
    "structures_that_slipped": family1_slips,
    "results": family1_results,
    "refutation_criterion": (
        "A structure with a primary-literature-documented difficult "
        "synthesis (low yield, hazardous, and/or a landmark multi-step "
        "total synthesis undertaken specifically because of its "
        "difficulty) scores SA<6.0 (the module's own 'synthesizable' cut) "
        "under the exact SA_Score reference implementation the target "
        "receipt validates."),
    "criterion_met": len(family1_slips) > 0,
}

# ============================================================================
# FAMILY 2 -- trivially-valid-but-degenerate SMILES passing validity
# ============================================================================
DEGENERATE = [
    {"name": "bare_wildcard_dummy_atom", "smiles": "*",
     "defect": "atomic_number_0_dummy_no_real_element"},
    {"name": "isolated_noble_gas_He", "smiles": "[He]",
     "defect": "inert_single_atom_no_covalent_bonds"},
    {"name": "isolated_noble_gas_Ar", "smiles": "[Ar]",
     "defect": "inert_single_atom_no_covalent_bonds"},
    {"name": "ten_disconnected_methane_fragments", "smiles": "C.C.C.C.C.C.C.C.C.C",
     "defect": "10_disconnected_components_not_one_candidate_molecule"},
    {"name": "NaCl_ionic_salt_two_fragments", "smiles": "[Na+].[Cl-]",
     "defect": "2_disconnected_ionic_fragments_not_one_covalent_species"},
    {"name": "diatomic_hydrogen_gas", "smiles": "[H][H]",
     "defect": "diatomic_gas_not_organic_hardener_candidate"},
    {"name": "deuterium_gas_isotope_only", "smiles": "[2H][2H]",
     "defect": "isotope_labelled_diatomic_gas_not_organic_candidate"},
    {"name": "diatomic_oxygen", "smiles": "O=O",
     "defect": "diatomic_gas_not_organic_hardener_candidate"},
    {"name": "four_fragment_salt_cluster", "smiles": "[Na+].[Na+].[Cl-].[Cl-]",
     "defect": "4_disconnected_ionic_fragments_not_one_covalent_species"},
]
CONTROL_LEGITIMATE = {"name": "methane_control_should_remain_valid", "smiles": "C"}


def metric_validity_as_shipped(smi):
    """Exact reproduction of the target receipt's metric_validity() gate."""
    return Chem.MolFromSmiles(smi) is not None


family2_results = []
family2_slips = []
for entry in DEGENERATE:
    m = Chem.MolFromSmiles(entry["smiles"])
    valid = metric_validity_as_shipped(entry["smiles"])
    n_frags = len(Chem.GetMolFrags(m)) if valid else None
    n_heavy = m.GetNumHeavyAtoms() if valid else None
    slips = bool(valid)  # any degenerate case passing the shipped gate is a slip
    family2_results.append({
        "name": entry["name"], "smiles": entry["smiles"], "defect": entry["defect"],
        "passes_shipped_validity_gate": valid,
        "n_disconnected_fragments": n_frags, "n_heavy_atoms": n_heavy,
        "slips_through_as_false_valid": slips,
    })
    if slips:
        family2_slips.append(entry["name"])

control_m = Chem.MolFromSmiles(CONTROL_LEGITIMATE["smiles"])
control_valid = metric_validity_as_shipped(CONTROL_LEGITIMATE["smiles"])
family2_positive_control = {
    "name": CONTROL_LEGITIMATE["name"], "smiles": CONTROL_LEGITIMATE["smiles"],
    "passes_shipped_validity_gate": control_valid,
    "expected": True,
    "note": ("Legitimate single-fragment organic molecule; included to show the "
             "gate is not simply broken for everything -- it specifically fails "
             "to reject non-covalent / multi-fragment / non-organic degenerate "
             "inputs while correctly accepting ordinary molecules."),
}

family2_summary = {
    "attack": "degenerate_but_valid_smiles_passing_validity_gate",
    "n_attempted": len(DEGENERATE),
    "n_slipped_through": len(family2_slips),
    "structures_that_slipped": family2_slips,
    "results": family2_results,
    "positive_control_legitimate_molecule": family2_positive_control,
    "refutation_criterion": (
        "An input that is not a single coherent covalent candidate molecule "
        "(a bare wildcard atom, an isolated inert atom, a multi-fragment "
        "mixture/salt, or an isotope-only diatomic gas) is reported "
        "valid=True by the target receipt's shipped metric_validity() "
        "definition (`Chem.MolFromSmiles(smi) is not None`, no connectivity "
        "or fragment-count check)."),
    "criterion_met": len(family2_slips) > 0,
}

# ============================================================================
# FAMILY 3 -- boundary probing at SA 5.9-6.1
# ============================================================================
assert os.path.exists(PI1M_PATH), "locked PI1M artifact missing"
import hashlib
h = hashlib.sha256()
with open(PI1M_PATH, "rb") as fh:
    for chunk in iter(lambda: fh.read(1 << 20), b""):
        h.update(chunk)
pi1m_sha_observed = h.hexdigest()
assert pi1m_sha_observed == PI1M_LOCKED_SHA, "PI1M hash-lock mismatch"

rows = []
with gzip.open(PI1M_PATH, "rt") as fh:
    for line in fh:
        rows.append(json.loads(line))
        if len(rows) >= PREFIX_N:
            break

boundary_rows = []
n_boundary = 0
n_boundary_divergent = 0
n_boundary_flipped_now = 0
n_boundary_at_risk_under_documented_residual = 0
DOCUMENTED_MAX_RESIDUAL = 0.66  # from target receipt sa_feasibility_known_answer.divergent_delta_max

for r in rows:
    smi = r["raw_fields"]["SMILES"]
    shipped_sa = float(r["raw_fields"]["SA Score"])
    m = Chem.MolFromSmiles(smi)
    if m is None:
        continue
    mine = sa_of(m)
    if mine is None:
        continue
    in_boundary = BOUNDARY_LO <= mine <= BOUNDARY_HI
    if not in_boundary:
        continue
    n_boundary += 1
    delta = mine - shipped_sa
    divergent = abs(delta) > SA_KA_TOL
    shipped_feasible = shipped_sa < SA_FEASIBLE_MAX
    mine_feasible = mine < SA_FEASIBLE_MAX
    flipped_now = shipped_feasible != mine_feasible
    at_risk = (mine - DOCUMENTED_MAX_RESIDUAL < SA_FEASIBLE_MAX <= mine + DOCUMENTED_MAX_RESIDUAL) or \
              (mine + DOCUMENTED_MAX_RESIDUAL >= SA_FEASIBLE_MAX > mine - DOCUMENTED_MAX_RESIDUAL)
    at_risk = bool(abs(mine - SA_FEASIBLE_MAX) <= DOCUMENTED_MAX_RESIDUAL)
    if divergent:
        n_boundary_divergent += 1
    if flipped_now:
        n_boundary_flipped_now += 1
    if at_risk:
        n_boundary_at_risk_under_documented_residual += 1
    if divergent or flipped_now or at_risk:
        boundary_rows.append({
            "smiles": smi, "shipped_sa": round(shipped_sa, 6), "mine_sa": round(mine, 6),
            "delta": round(delta, 6), "divergent_beyond_ka_tolerance": divergent,
            "shipped_says_feasible": shipped_feasible, "mine_says_feasible": mine_feasible,
            "flipped_now_between_shipped_and_mine": flipped_now,
            "at_risk_within_documented_max_residual_0_66": at_risk,
        })

# representation-invariance sub-probe on the boundary band (same-graph re-SMILES)
repr_probe = []
n_repr_divergent = 0
sample_for_repr = [r for r in rows
                    if Chem.MolFromSmiles(r["raw_fields"]["SMILES"]) is not None][:PREFIX_N]
checked = 0
for r in sample_for_repr:
    smi = r["raw_fields"]["SMILES"]
    m = Chem.MolFromSmiles(smi)
    mine = sa_of(m)
    if mine is None or not (BOUNDARY_LO <= mine <= BOUNDARY_HI):
        continue
    checked += 1
    kek = Chem.MolToSmiles(m, kekuleSmiles=True)
    m_kek = Chem.MolFromSmiles(kek)
    sa_kek = sa_of(m_kek) if m_kek is not None else None
    rand_smi = Chem.MolToSmiles(m, doRandom=True, canonical=False)
    m_rand = Chem.MolFromSmiles(rand_smi)
    sa_rand = sa_of(m_rand) if m_rand is not None else None
    d_kek = abs(sa_kek - mine) if sa_kek is not None else None
    d_rand = abs(sa_rand - mine) if sa_rand is not None else None
    divergent_repr = bool((d_kek is not None and d_kek > 1e-9) or
                           (d_rand is not None and d_rand > 1e-9))
    if divergent_repr:
        n_repr_divergent += 1
    repr_probe.append({
        "smiles": smi, "sa_canonical": round(mine, 6),
        "sa_kekulized_resmiles": round(sa_kek, 6) if sa_kek is not None else None,
        "sa_randomized_atomorder_resmiles": round(sa_rand, 6) if sa_rand is not None else None,
        "divergent_across_representation": divergent_repr,
    })
    if checked >= 200:  # bound the sub-probe; boundary band is already a small slice
        break

family3_summary = {
    "attack": "boundary_probing_sa_5_9_to_6_1",
    "pi1m_prefix_rows_scanned": len(rows),
    "n_rows_in_boundary_band_5_9_to_6_1": n_boundary,
    "n_boundary_rows_divergent_beyond_ka_tolerance": n_boundary_divergent,
    "n_boundary_rows_flipped_now_shipped_vs_mine": n_boundary_flipped_now,
    "n_boundary_rows_at_risk_under_documented_max_residual_0_66": n_boundary_at_risk_under_documented_residual,
    "flagged_rows": boundary_rows,
    "representation_invariance_subprobe": {
        "n_boundary_band_structures_checked": checked,
        "n_divergent_across_representation": n_repr_divergent,
        "rows": repr_probe,
    },
    "refutation_criterion": (
        "Among PI1M reference-prefix structures whose SA score falls in the "
        "target's own admitted SA-instrument residual (up to 0.66 units, "
        "'documented RDKit-version sensitivity...dismissed as confined to "
        "exotic heteroaromatic motifs'), at least one row's SA lies within "
        "5.9-6.1 of the 6.0 feasibility cut AND either (a) the shipped vs. "
        "recomputed SA already disagree on feasible/infeasible, or (b) the "
        "row's distance from 6.0 is within the receipt's own documented max "
        "residual of 0.66, meaning the receipt's dismissal ('coating "
        "hardeners...fall in the exactly-reproduced majority') does not "
        "establish boundary-band safety, since the boundary band is exactly "
        "where the dismissed residual matters."),
    "criterion_met": (n_boundary_flipped_now > 0 or n_boundary_at_risk_under_documented_residual > 0),
}

# ============================================================================
# Overall verdict
# ============================================================================
any_family_broke_claim = (family1_summary["criterion_met"]
                           or family2_summary["criterion_met"]
                           or family3_summary["criterion_met"])

diag = {
    "study_id": "MOLGEN_SA_VALIDITY_ADVERSARIAL_PROBE_R_S06_V1",
    "campaign_item_id": "R-S06",
    "target_claim": {
        "receipt_path": os.path.join("amphora-molecule-generator", TARGET_RECEIPT_REL),
        "claim_text": ("The generator's validity and feasibility (SA<6) gate "
                       "components withstand adversarial probing."),
        "target_fields_attacked": [
            "hypothesis_evaluation.feasibility_preserved",
            "deterministic_inscope_proposal_demo.all_proposals_feasible",
            "results.inscope_validity (metric_validity gate)",
            "sa_feasibility_known_answer (dismissed residual, boundary-band)",
        ],
    },
    "headline": (
        f"3/3 attack families executed. Family 1 (known-hard structures): "
        f"{len(family1_slips)}/{len(KNOWN_HARD)} genuinely hard-to-synthesize "
        f"strained-cage hydrocarbons score SA<6 (false feasible) -- "
        f"{', '.join(family1_slips) if family1_slips else 'none'}. "
        f"Family 2 (degenerate validity): {len(family2_slips)}/{len(DEGENERATE)} "
        f"non-molecule / non-covalent / multi-fragment SMILES pass the shipped "
        f"validity gate as valid=True. "
        f"Family 3 (SA 5.9-6.1 boundary): {n_boundary} PI1M reference "
        f"structures fall in the boundary band; "
        f"{n_boundary_flipped_now} already flip feasible/infeasible between "
        f"shipped and recomputed SA, "
        f"{n_boundary_at_risk_under_documented_residual} more lie within the "
        f"receipt's own documented max residual (0.66) of the SA=6.0 cut."
    ),
    "rdkit_version": rdkit.__version__,
    "hash_and_count_lock": {
        "pi1m_normalized_artifact_relpath": PI1M_REL,
        "pi1m_normalized_artifact_sha256_expected": PI1M_LOCKED_SHA,
        "pi1m_normalized_artifact_sha256_observed": pi1m_sha_observed,
        "prefix_rows_processed": len(rows),
        "target_receipt_relpath": TARGET_RECEIPT_REL,
    },
    "family_1_known_hard_structures": family1_summary,
    "family_2_degenerate_valid_smiles": family2_summary,
    "family_3_boundary_probing": family3_summary,
    "any_family_broke_claim": any_family_broke_claim,
    "verdict": "CLAIM_REFUTED" if any_family_broke_claim else "CLAIM_SURVIVED",
    "theory_reference": {
        "feasibility_sa_score": "Ertl & Schuffenhauer 2009 J. Cheminform. 1:8",
        "toolkit": "RDKit Contrib/SA_Score fpscores reference implementation (same as target)",
        "family1_citations": [e["citation"] for e in KNOWN_HARD],
    },
    "rights_posture": ("PI1M reference reused exactly as already consulted by the "
                       "target receipt (CONTEXT_ONLY, non-scored, TRAINING_CORPUS "
                       "consumer role); no new data acquired. Manifest untouched."),
    "does_not_close": [
        "Runtime remains LOCKED_INTERNAL; no proposal emission enabled.",
        "This is an AUDIT_ONLY diagnostic; it grants no promotion authority.",
        "Family 3's 'at risk' rows are a documented-residual proximity flag, "
        "not independently re-measured under a second RDKit build.",
    ],
}

out_path = sys.argv[1]
with open(out_path, "w") as fh:
    json.dump(diag, fh, indent=2, sort_keys=True)
print("WROTE", out_path)
print("family1_slips", family1_slips)
print("family2_slips", family2_slips)
print("family3_boundary_n", n_boundary, "flipped_now", n_boundary_flipped_now,
      "at_risk", n_boundary_at_risk_under_documented_residual)
print("verdict", diag["verdict"])
