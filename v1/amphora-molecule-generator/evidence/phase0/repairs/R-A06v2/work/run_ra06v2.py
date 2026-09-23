#!/usr/bin/env python3
"""R-A06v2 SUPERSEDING REPAIR compute -- amphora-molecule-generator.

Follow-up repair superseding R-A06
(evidence/phase0/repairs/R-A06/done/molgen-r-a06-superseding-repair-receipt.v1.dsse.json),
whose "29/38 difunctional" LABEL was refuted by the independent verify V-A06
(evidence/phase0/repairs/V-A06/done/v-a06-molecule-generator-repair-verify-receipt.v1.dsse.json,
verdict CLAIM_REFUTED).

V-A06 confirmed R-A06's arithmetic reproduces exactly (Clopper-Pearson to 4dp,
yield 29 under the gate amine_sites==2, family IntDiv_1 to 4dp, 0 mismatches on a
fresh RDKit re-derivation) but refuted the WORD: R-A06 republished those 29 as
"difunctional" while all 29 carry active_nh == 4 under the standard active-hydrogen
functionality convention. V-A06 explicitly declined to assert a new headline.

This v2 does NOT re-litigate the arithmetic. It:
  (1) re-derives BOTH functionality conventions independently from the raw
      canonical SMILES with TWO mutually-independent RDKit implementations
      (explicit atom-rule loop; SMARTS query) and requires them to agree;
  (2) validates the instrument against the in-tree known_answer_amines ground
      truth (amphora-molecule-generator/reference/mvp20/data/
      hardener_stoichiometric_envelope.v1.json, which cites Lee & Neville 1967)
      and its fail_closed_decoys;
  (3) publishes the count under EACH convention side by side;
  (4) quantifies the product-relevant consequence of picking the wrong one
      (AHEW and mix-ratio phr error against DGEBA);
  (5) carries forward, re-derived, the two R-A06 corrections V-A06 confirmed.

Reads only hash-locked existing artifacts. Writes only under
evidence/phase0/repairs/R-A06v2/. Deterministic: no RNG, no wall clock.
"""
import base64
import hashlib
import json
import sys
from itertools import combinations
from pathlib import Path

from scipy.stats import beta
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import Descriptors, rdFingerprintGenerator

RDLogger.DisableLog("rdApp.*")

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-molecule-generator"
R_A06_DONE = MOD / "evidence/phase0/repairs/R-A06/done/molgen-r-a06-superseding-repair-receipt.v1.dsse.json"
R_A06_DONE_SHA = "89fc28d21f7224743a6e0a1d2a0750055058e6167e038eee7a65b90145ea4b52"
V_A06_DONE = MOD / "evidence/phase0/repairs/V-A06/done/v-a06-molecule-generator-repair-verify-receipt.v1.dsse.json"
V_A06_DONE_SHA = "128a24c33c684323fad2cc49611cc36aef628720cfb0da0382c9011baae9de0c"
SRC_DIAG = MOD / "evidence/audit/molgen-deterministic-grammar-yield-v1/diagnostic.canonical.json"
SRC_DIAG_SHA = "55afc806360e6abeab30bbc7e71ed94e8ef4a5ee6e1f67a0b02358c699dc01a8"
ENVELOPE_REF = MOD / "reference/mvp20/data/hardener_stoichiometric_envelope.v1.json"
ENVELOPE_REF_SHA = "b1a08e856cab233c69c09673ed0d96a40c38346753afae4ad415b5948edaa9a8"

WORK = MOD / "evidence/phase0/repairs/R-A06v2/work"
WORK.mkdir(parents=True, exist_ok=True)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def payload_of(p):
    env = json.loads(Path(p).read_bytes())
    env = env.get("signature", env)
    return json.loads(base64.standard_b64decode(env["payload"]))


checks = {}

# ---------------------------------------------------------------- preconditions
r_a06_bytes = R_A06_DONE.read_bytes()
v_a06_bytes = V_A06_DONE.read_bytes()
diag_bytes = SRC_DIAG.read_bytes()
env_bytes = ENVELOPE_REF.read_bytes()
checks["p1_r_a06_done_receipt_byte_intact"] = sha(r_a06_bytes) == R_A06_DONE_SHA
checks["p2_v_a06_verify_receipt_byte_intact"] = sha(v_a06_bytes) == V_A06_DONE_SHA
checks["p3_source_diagnostic_byte_intact"] = sha(diag_bytes) == SRC_DIAG_SHA
checks["p4_known_answer_reference_byte_intact"] = sha(env_bytes) == ENVELOPE_REF_SHA

r_a06 = payload_of(R_A06_DONE)
v_a06 = payload_of(V_A06_DONE)
diag = json.loads(diag_bytes)
envref = json.loads(env_bytes)

props = diag["accepted_proposals"]
assert len(props) == 38, len(props)

# Values read verbatim OUT OF the V-A06 verify receipt bytes (not transcribed
# from any prompt); every one of them is re-measured below and asserted equal.
va06_measured = {
    "n_amine_sites2_but_active_nh_ne_2": v_a06["escalation_attack"]["observed"]["n_amine_sites2_but_active_nh_ne_2"],
    "n_amine_sites2_total": v_a06["escalation_attack"]["observed"]["n_amine_sites2_total"],
    "n_true_difunctional_active_h_eq_2_among_all_38": v_a06["escalation_attack"]["observed"]["n_true_difunctional_active_h_eq_2_among_all_38"],
    "mda_ddm_active_nh": v_a06["escalation_attack"]["observed"]["mda_ddm_case"]["active_nh"],
    "mda_ddm_amine_sites": v_a06["escalation_attack"]["observed"]["mda_ddm_case"]["amine_sites"],
    "independent_yield_by_amine_sites_eq_2": v_a06["checks"]["3_independent_yield_by_amine_sites_eq_2"],
    "clopper_pearson_lower": v_a06["clopper_pearson_independent"]["independent_lower"],
    "clopper_pearson_upper": v_a06["clopper_pearson_independent"]["independent_upper"],
    "intdiv1_F1_r2": v_a06["family_resolved_intdiv1_independent"]["F1_polyethyleneamine"]["intdiv1_r2"],
    "intdiv1_F2_r2": v_a06["family_resolved_intdiv1_independent"]["F2_alpha_omega_diamine"]["intdiv1_r2"],
    "verdict": v_a06["verdict"],
}
checks["p5_v_a06_verdict_is_claim_refuted"] = va06_measured["verdict"] == "CLAIM_REFUTED"

# ==================================================================== CONVENTIONS
# Two mutually-independent RDKit implementations of the SAME two definitions.
#
# CONVENTION A -- AMINE CENTRES (n_amine_centres, a.k.a. amine_sites / n_basicN):
#   the number of distinct epoxy-relevant nitrogen ATOMS. Counted once per N atom
#   regardless of how many hydrogens it bears. Excluded: aromatic-ring N (no N-H
#   available, pyridine-type), amide/thioamide N, imine/nitrile N (multiply-bonded).
#   This is the quantity the ASTM D2074 total amine value is built on
#   (AV = 56105.6 * n_basicN / M) and the quantity the generator's own
#   `amine_sites` column reports.
#
# CONVENTION B -- ACTIVE-HYDROGEN FUNCTIONALITY (n_active_nh, a.k.a. active_NH, f):
#   the number of N-H hydrogens carried by those same nitrogen centres, i.e. the
#   number of hydrogens available for epoxide ring-opening addition. Primary -NH2
#   contributes 2, secondary -NH- contributes 1, tertiary N contributes 0.
#   This is the quantity the amine-hydrogen equivalent weight is built on
#   (AHEW = M / n_activeH, Lee & Neville 1967) and the Flory-Stockmayer network
#   functionality f.
#
# For any amine, n_active_nh is NOT determined by n_amine_centres: a primary
# diamine has 2 centres and f=4, a secondary diamine has 2 centres and f=2, a
# tertiary diamine has 2 centres and f=0.

AMINE_SMARTS = "[NX3;!$(NC=O);!$(N=*);!$(N#*);!a]"
_amine_pat = Chem.MolFromSmarts(AMINE_SMARTS)
assert _amine_pat is not None


def centres_impl_A_atomrules(mol):
    """Explicit atom-rule loop. No SMARTS. Independent of impl B."""
    out = []
    for atom in mol.GetAtoms():
        if atom.GetAtomicNum() != 7:
            continue
        if atom.GetIsAromatic():
            continue                       # pyridine-type ring N: no N-H site
        if atom.GetFormalCharge() != 0:
            continue                       # ammonium / nitro-type charged N
        if atom.GetTotalDegree() != 3:
            continue                       # NX3 only
        if any(b.GetBondTypeAsDouble() != 1.0 for b in atom.GetBonds()):
            continue                       # imine / nitrile / N-oxide etc.
        acyl = False
        for nb in atom.GetNeighbors():
            if nb.GetAtomicNum() != 6:
                continue
            for b in nb.GetBonds():
                other = b.GetOtherAtom(nb)
                if b.GetBondTypeAsDouble() == 2.0 and other.GetAtomicNum() in (8, 16):
                    acyl = True             # amide / thioamide N: not epoxy-reactive
        if acyl:
            continue
        out.append(atom.GetIdx())
    return sorted(out)


def centres_impl_B_smarts(mol):
    """SMARTS query path. Independent of impl A."""
    return sorted({m[0] for m in mol.GetSubstructMatches(_amine_pat)})


def both_conventions(smiles):
    mol = Chem.MolFromSmiles(smiles)
    assert mol is not None, smiles
    a = centres_impl_A_atomrules(mol)
    b = centres_impl_B_smarts(mol)
    agree = (a == b)
    n_centres = len(a)
    n_active_nh = sum(mol.GetAtomWithIdx(i).GetTotalNumHs() for i in a)
    n_active_nh_b = sum(mol.GetAtomWithIdx(i).GetTotalNumHs() for i in b)
    return {
        "n_amine_centres_conventionA": n_centres,
        "n_active_nh_conventionB": n_active_nh,
        "impl_A_equals_impl_B": agree and (n_active_nh == n_active_nh_b),
        "mol": mol,
    }


# ============================================== (1) instrument validation: in-tree
# known-answer ground truth (Lee & Neville 1967) BEFORE any measurement is trusted.
ka_rows = []
for e in envref["known_answer_amines"]["entries"]:
    r = both_conventions(e["smiles"])
    ka_rows.append({
        "name": e["name"],
        "smiles": e["smiles"],
        "expected_active_nh": e["expected_active_nh"],
        "measured_active_nh_conventionB": r["n_active_nh_conventionB"],
        "expected_basic_n": e["expected_basic_n"],
        "measured_amine_centres_conventionA": r["n_amine_centres_conventionA"],
        "active_nh_matches_ground_truth": r["n_active_nh_conventionB"] == e["expected_active_nh"],
        "amine_centres_matches_ground_truth": r["n_amine_centres_conventionA"] == e["expected_basic_n"],
        "impl_A_equals_impl_B": r["impl_A_equals_impl_B"],
        "ahew_g_per_eq": round(Descriptors.MolWt(r["mol"]) / r["n_active_nh_conventionB"], 4),
    })
decoy_rows = []
for e in envref["fail_closed_decoys"]["entries"]:
    r = both_conventions(e["smiles"])
    decoy_rows.append({
        "name": e["name"],
        "smiles": e["smiles"],
        "expected_active_nh": e["expected_active_nh"],
        "measured_active_nh_conventionB": r["n_active_nh_conventionB"],
        "measured_amine_centres_conventionA": r["n_amine_centres_conventionA"],
        "active_nh_matches_ground_truth": r["n_active_nh_conventionB"] == e["expected_active_nh"],
        "impl_A_equals_impl_B": r["impl_A_equals_impl_B"],
    })

checks["1a_known_answer_active_nh_all_match"] = all(r["active_nh_matches_ground_truth"] for r in ka_rows)
checks["1b_known_answer_amine_centres_all_match"] = all(r["amine_centres_matches_ground_truth"] for r in ka_rows)
checks["1c_decoys_active_nh_all_match"] = all(r["active_nh_matches_ground_truth"] for r in decoy_rows)
checks["1d_two_implementations_agree_on_ground_truth_set"] = all(
    r["impl_A_equals_impl_B"] for r in ka_rows + decoy_rows)
checks["1e_n_known_answer_entries"] = len(ka_rows)
checks["1f_n_decoy_entries"] = len(decoy_rows)
# The decoys are the discriminating cases: triethylamine and N,N-dimethylbenzylamine
# have amine CENTRES but ZERO active hydrogens -- the two conventions disagree by
# construction, which is exactly why the choice of convention is not cosmetic.
checks["1g_decoy_shows_conventions_are_not_equivalent"] = any(
    r["measured_amine_centres_conventionA"] > 0 and r["measured_active_nh_conventionB"] == 0
    for r in decoy_rows)

# ============================================ (2) re-derivation over the 38 accepted
EEW_TECH = envref["dgeba_reference"]["eew_technical_liquid_g_per_eq"]
EEW_MONO = envref["dgeba_reference"]["eew_monomeric_g_per_eq"]

rows = []
for pr in props:
    smi = pr["canonical_smiles"]
    r = both_conventions(smi)
    mol = r["mol"]
    mw = Descriptors.MolWt(mol)
    nA = r["n_amine_centres_conventionA"]
    nB = r["n_active_nh_conventionB"]
    rows.append({
        "name": pr["name"],
        "family": pr["family"],
        "canonical_smiles": smi,
        "molecular_weight": round(mw, 4),
        "n_amine_centres_conventionA": nA,
        "n_active_nh_conventionB": nB,
        "impl_A_equals_impl_B": r["impl_A_equals_impl_B"],
        "diagnostic_amine_sites": pr["amine_sites"],
        "diagnostic_active_nh": pr["active_nh"],
        "diagnostic_difunctional_hardener_flag": pr["difunctional_hardener"],
        "difunctional_under_conventionA_two_amine_centres": nA == 2,
        "difunctional_under_conventionB_active_h_eq_2": nB == 2,
        "ahew_correct_conventionB_g_per_eq": round(mw / nB, 4),
        "ahew_if_wrongly_using_conventionA_g_per_eq": round(mw / nA, 4),
        "phr_correct_conventionB_vs_dgeba_eew190": round(100.0 * (mw / nB) / EEW_TECH, 4),
        "phr_if_wrongly_using_conventionA_vs_dgeba_eew190": round(100.0 * (mw / nA) / EEW_TECH, 4),
        "phr_overdose_ratio_A_over_B": round((mw / nA) / (mw / nB), 6),
    })

checks["2a_two_implementations_agree_on_all_38"] = all(r["impl_A_equals_impl_B"] for r in rows)
checks["2b_conventionA_parity_with_diagnostic_column"] = all(
    r["n_amine_centres_conventionA"] == r["diagnostic_amine_sites"] for r in rows)
checks["2c_conventionB_parity_with_diagnostic_column"] = all(
    r["n_active_nh_conventionB"] == r["diagnostic_active_nh"] for r in rows)

n_A2 = sum(1 for r in rows if r["n_amine_centres_conventionA"] == 2)
n_B2 = sum(1 for r in rows if r["n_active_nh_conventionB"] == 2)
n_B4 = sum(1 for r in rows if r["n_active_nh_conventionB"] == 4)
set_A2 = {r["name"] for r in rows if r["n_amine_centres_conventionA"] == 2}
set_B4 = {r["name"] for r in rows if r["n_active_nh_conventionB"] == 4}

hist_A = {}
hist_B = {}
for r in rows:
    hist_A[str(r["n_amine_centres_conventionA"])] = hist_A.get(str(r["n_amine_centres_conventionA"]), 0) + 1
    hist_B[str(r["n_active_nh_conventionB"])] = hist_B.get(str(r["n_active_nh_conventionB"]), 0) + 1

checks["2d_n_amine_centres_eq_2_conventionA"] = n_A2
checks["2e_n_active_nh_eq_2_conventionB"] = n_B2
checks["2f_n_active_nh_eq_4_conventionB"] = n_B4
checks["2g_conventionA_two_centre_set_equals_conventionB_tetrafunctional_set"] = (set_A2 == set_B4)
checks["2h_all_38_have_active_nh_ge_3_network_forming"] = all(
    r["n_active_nh_conventionB"] >= 3 for r in rows)
# every 2-centre member of this corpus is primary,primary -> f = 2 * centres exactly
checks["2i_every_two_centre_member_has_active_nh_exactly_twice_centres"] = all(
    r["n_active_nh_conventionB"] == 2 * r["n_amine_centres_conventionA"]
    for r in rows if r["n_amine_centres_conventionA"] == 2)
checks["2j_phr_overdose_ratio_is_exactly_2x_for_all_two_centre_members"] = all(
    abs(r["phr_overdose_ratio_A_over_B"] - 2.0) < 1e-9
    for r in rows if r["n_amine_centres_conventionA"] == 2)

mda = next(r for r in rows if r["name"] == "MDA/DDM(methylene)")

# ============ (3) parity with the exact values measured in the V-A06 verify receipt
checks["3a_reproduces_va06_n_amine_sites2_total"] = (n_A2 == va06_measured["n_amine_sites2_total"])
checks["3b_reproduces_va06_yield_under_amine_sites_gate"] = (
    n_A2 == va06_measured["independent_yield_by_amine_sites_eq_2"])
checks["3c_reproduces_va06_n_true_difunctional_active_h"] = (
    n_B2 == va06_measured["n_true_difunctional_active_h_eq_2_among_all_38"])
checks["3d_reproduces_va06_mismatch_count_29_of_29"] = (
    sum(1 for r in rows if r["n_amine_centres_conventionA"] == 2
        and r["n_active_nh_conventionB"] != 2) == va06_measured["n_amine_sites2_but_active_nh_ne_2"])
checks["3e_reproduces_va06_mda_active_nh"] = (
    mda["n_active_nh_conventionB"] == va06_measured["mda_ddm_active_nh"])
checks["3f_reproduces_va06_mda_amine_centres"] = (
    mda["n_amine_centres_conventionA"] == va06_measured["mda_ddm_amine_sites"])
# MDA AHEW is the textbook external anchor the envelope reference states (~49.5 g/eq)
checks["3g_mda_ahew_matches_published_tetrafunctional_value_within_0p5"] = (
    abs(mda["ahew_correct_conventionB_g_per_eq"] - 49.5) < 0.5)

# ======================= (4) carry forward the two corrections V-A06 CONFIRMED,
# independently re-derived here so this receipt is self-contained.
K = sum(1 for pr in props if pr["feasible_sa_below_6"])
N = len(props)
ALPHA = 0.05
cp_lower = 0.0 if K == 0 else float(beta.ppf(ALPHA / 2, K, N - K + 1))
cp_upper = 1.0 if K == N else float(beta.ppf(1 - ALPHA / 2, K + 1, N - K))
checks["4a_clopper_pearson_reproduces_r_a06_and_va06_4dp"] = (
    round(cp_lower, 4) == round(va06_measured["clopper_pearson_lower"], 4)
    and round(cp_upper, 4) == round(va06_measured["clopper_pearson_upper"], 4)
    and round(cp_lower, 4) == round(
        r_a06["corrected_values"]["feasible_fraction_exact_clopper_pearson95_ci"][0], 4))

_gen_r2 = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)


def intdiv1(smis):
    fps = [_gen_r2.GetFingerprint(Chem.MolFromSmiles(s)) for s in smis]
    pairs = list(combinations(range(len(fps)), 2))
    sims = [DataStructs.TanimotoSimilarity(fps[i], fps[j]) for i, j in pairs]
    mean = sum(sims) / len(sims)
    return 1.0 - mean, mean, len(pairs)


fam_smiles = {}
for pr in props:
    fam_smiles.setdefault(pr["family"], []).append(pr["canonical_smiles"])
family_intdiv1 = {}
for fam in sorted(fam_smiles):
    d1, m, np_ = intdiv1(fam_smiles[fam])
    family_intdiv1[fam] = {"n": len(fam_smiles[fam]), "n_pairs": np_,
                           "intdiv1_morgan_r2_2048": d1, "mean_tanimoto": m}
checks["4b_family_intdiv1_F1_reproduces_va06_1e-9"] = abs(
    family_intdiv1["F1_polyethyleneamine"]["intdiv1_morgan_r2_2048"] - va06_measured["intdiv1_F1_r2"]) < 1e-9
checks["4c_family_intdiv1_F2_reproduces_va06_1e-9"] = abs(
    family_intdiv1["F2_alpha_omega_diamine"]["intdiv1_morgan_r2_2048"] - va06_measured["intdiv1_F2_r2"]) < 1e-9

all_bool = [v for v in checks.values() if isinstance(v, bool)]
checks_all_pass = all(all_bool)

headline = (
    f"{n_B2} of {N} accepted hardener proposals are DIFUNCTIONAL under the "
    f"active-hydrogen functionality convention (active_NH == 2, the AHEW / "
    f"Flory-Stockmayer basis); {n_A2} of {N} have exactly TWO AMINE CENTRES "
    f"(are diamines), and all {n_A2} of those carry active_NH == 4, i.e. they are "
    f"TETRAfunctional. R-A06's published headline '{r_a06['corrected_values']['valid_unique_difunctional_feasible_yield']}/38 "
    f"valid-unique-difunctional-feasible' is therefore correct as an amine-CENTRE "
    f"count and wrong as a FUNCTIONALITY count; the two numbers are both published "
    f"here, side by side, under explicit definitions so the label cannot be misread "
    f"a third time. The portfolio must use the active-hydrogen convention for the "
    f"word 'difunctional', because it -- not the nitrogen-atom count -- is what sets "
    f"AHEW, the epoxy:amine mix ratio, and the Flory-Stockmayer network functionality."
)

diagnostic = {
    "study_id": "molgen-r-a06v2-functionality-convention-repair-v1",
    "schema": "amphora.molecule-generator.r-a06v2-superseding-repair-diagnostic.v1",
    "repair_item": "R-A06v2",
    "supersedes_repair_item": "R-A06",
    "refuted_by_verify_item": "V-A06",
    "date": "2026-08-04",
    "generated_on_host": "xbabe2",
    "rdkit_version": Chem.rdBase.rdkitVersion,
    "headline": headline,
    "convention_definitions": {
        "conventionA_amine_centres": {
            "name": "amine centres (n_amine_centres; the generator's `amine_sites` column; ASTM D2074 n_basicN)",
            "definition": (
                "The number of DISTINCT epoxy-relevant nitrogen ATOMS in the molecule, "
                "counted once per nitrogen regardless of how many hydrogens it bears. "
                "A nitrogen qualifies iff it is trivalent (NX3), formally neutral, not an "
                "aromatic-ring member, carries no multiple bond, and is not attached to a "
                "carbonyl/thiocarbonyl carbon (amide/thioamide N is not epoxy-reactive at "
                "ambient cure). Primary -NH2, secondary -NH- and TERTIARY -N< all count as 1."),
            "governs": "ASTM D2074 total amine value, AV = 56105.6 * n_basicN / M (mg KOH/g).",
            "does_not_govern": "AHEW, epoxy:amine mix ratio, or network functionality.",
            "rdkit_smarts_reference_implementation": AMINE_SMARTS,
        },
        "conventionB_active_hydrogen_functionality": {
            "name": "active-hydrogen functionality (n_active_nh; active_NH; Flory-Stockmayer f)",
            "definition": (
                "The number of N-H HYDROGENS carried by those same qualifying nitrogen "
                "centres, i.e. the number of hydrogens available for epoxide ring-opening "
                "addition. Primary -NH2 contributes 2, secondary -NH- contributes 1, "
                "tertiary -N< contributes 0. Aromatic-ring N, amide N and multiply-bonded N "
                "contribute 0 because they are excluded as centres."),
            "governs": (
                "AHEW = M / n_activeH (Lee & Neville 1967); mix ratio phr = 100 * AHEW / EEW "
                "at 1:1 epoxide:amine-hydrogen stoichiometry; Flory-Stockmayer network "
                "functionality f and hence gel point and crosslink density."),
            "independence": (
                "n_active_nh is NOT a function of n_amine_centres: a primary,primary diamine "
                "has 2 centres and f=4; a secondary,secondary diamine has 2 centres and f=2; "
                "a tertiary,tertiary diamine has 2 centres and f=0."),
        },
        "the_word_difunctional": {
            "portfolio_convention_to_use": "conventionB_active_hydrogen_functionality",
            "difunctional_means": "active_NH == 2 (f = 2)",
            "why": (
                "'Functionality' denotes the number of independent bond-forming reactions the "
                "molecule can undergo with the co-reactant, not the number of heteroatoms it "
                "contains. For an epoxy-amine system that count is the active-hydrogen count: "
                "it is what AHEW is defined as (M / n_activeH), what the mix ratio phr is "
                "computed from (100 * AHEW / EEW), and what Flory-Stockmayer gelation theory "
                "takes as f. The nitrogen-atom count enters only the amine VALUE (ASTM D2074), "
                "a titration quantity, and sets no stoichiometry. This module's own in-tree "
                "reference file already encodes the active-hydrogen convention as ground truth "
                "(hardener_stoichiometric_envelope.v1.json: 'AHEW = M / n_activeH ... Lee & "
                "Neville 1967', with expected_active_nh = 4 for MDA/DDM, IPDA, m-XDA, DDS and "
                "1,3-BAC), so using the nitrogen-atom count for the word 'difunctional' put the "
                "generator's label in direct contradiction with the module's own reference data."),
            "recommended_wording": (
                "Call the 2-centre subset 'diamines' or 'two amine centres', never "
                "'difunctional'. Publish n_amine_centres and active_NH as two separately named "
                "columns and never collapse them into one word."),
            "consequence_if_confused": (
                "For a primary,primary diamine the amine-centre count is exactly half the "
                "active-hydrogen count, so treating centres as functionality doubles AHEW and "
                "therefore doubles the hardener mix ratio phr -- a 2x stoichiometric overdose "
                "that leaves roughly half the epoxide groups unreacted."),
        },
    },
    "instrument_validation": {
        "ground_truth_source": {
            "path": "amphora-molecule-generator/reference/mvp20/data/hardener_stoichiometric_envelope.v1.json",
            "sha256": ENVELOPE_REF_SHA,
            "block": "known_answer_amines + fail_closed_decoys",
            "citation": envref["instrument_definitions"]["ahew_g_per_eq"],
        },
        "known_answer_amines": ka_rows,
        "fail_closed_decoys": decoy_rows,
        "n_known_answer_entries": len(ka_rows),
        "n_known_answer_active_nh_matches": sum(1 for r in ka_rows if r["active_nh_matches_ground_truth"]),
        "n_known_answer_amine_centre_matches": sum(1 for r in ka_rows if r["amine_centres_matches_ground_truth"]),
        "n_decoy_entries": len(decoy_rows),
        "n_decoy_active_nh_matches": sum(1 for r in decoy_rows if r["active_nh_matches_ground_truth"]),
        "coverage_note": (
            "All 8 known_answer_amines entries (DETA, TETA, TEPA, IPDA, MXDA, MDA/DDM, DDS, "
            "1,3-BAC) are themselves members of, or structurally identical to members of, the "
            "38 accepted proposals, so the ground truth covers the corpus directly rather than "
            "by analogy."),
        "two_independent_implementations": {
            "impl_A": "explicit per-atom rule loop (no SMARTS)",
            "impl_B": f"SMARTS substructure query {AMINE_SMARTS}",
            "agreement_required": True,
        },
    },
    "counts_under_each_convention": {
        "n_accepted_proposals": N,
        "conventionA_n_with_exactly_2_amine_centres": n_A2,
        "conventionB_n_with_active_nh_eq_2_true_difunctional": n_B2,
        "conventionB_n_with_active_nh_eq_4_tetrafunctional": n_B4,
        "conventionA_histogram_amine_centres": hist_A,
        "conventionB_histogram_active_nh": hist_B,
        "two_centre_set_is_identical_to_tetrafunctional_set": (set_A2 == set_B4),
        "n_network_forming_active_nh_ge_3": sum(1 for r in rows if r["n_active_nh_conventionB"] >= 3),
    },
    "per_proposal_table": rows,
    "mda_ddm_external_anchor": {
        "name": mda["name"],
        "canonical_smiles": mda["canonical_smiles"],
        "n_amine_centres_conventionA": mda["n_amine_centres_conventionA"],
        "n_active_nh_conventionB": mda["n_active_nh_conventionB"],
        "ahew_correct_conventionB_g_per_eq": mda["ahew_correct_conventionB_g_per_eq"],
        "ahew_if_wrongly_using_conventionA_g_per_eq": mda["ahew_if_wrongly_using_conventionA_g_per_eq"],
        "published_tetrafunctional_ahew_g_per_eq": 49.5,
        "note": (
            "MDA/DDM (4,4'-diaminodiphenylmethane) is one of the 38 accepted proposals and is "
            "listed in the published epoxy literature and in this module's own in-tree "
            "known_answer_amines block as a TETRAfunctional curing agent (expected_active_nh = 4, "
            "AHEW ~= 49.5 g/eq). The re-derivation reproduces that value; the amine-centre "
            "convention would instead give ~99 g/eq."),
    },
    "carried_forward_corrections_confirmed_by_v_a06": {
        "note": (
            "V-A06 independently reproduced these two R-A06 corrections exactly and did not "
            "dispute them. They are re-derived here so this superseding receipt is "
            "self-contained and a reader never has to consult the partially-refuted R-A06."),
        "feasible_fraction_point_estimate": K / N,
        "feasible_fraction_exact_clopper_pearson95_ci": [round(cp_lower, 6), round(cp_upper, 6)],
        "clopper_pearson_k": K,
        "clopper_pearson_n": N,
        "family_resolved_intdiv1_morgan_r2_2048": family_intdiv1,
    },
    "values_read_from_v_a06_verify_receipt_bytes": va06_measured,
    "checks": checks,
    "checks_all_pass": checks_all_pass,
    "theory_reference": {
        "ahew_and_functionality": "Lee, H. & Neville, K. 1967, Handbook of Epoxy Resins, McGraw-Hill (LCCN 66-23992)",
        "gelation_functionality": "Flory 1953, Principles of Polymer Chemistry, Cornell Univ. Press, ch. IX (Flory-Stockmayer)",
        "amine_value": "ASTM D2074 total amine value (AV = 56105.6 * n_basicN / M)",
        "exact_binomial_interval": "Clopper & Pearson 1934, Biometrika 26(4):404-413",
        "fingerprint": "Rogers & Hahn 2010, J. Chem. Inf. Model. 50(5):742-754 (ECFP/Morgan)",
        "similarity_coefficient": "Bajusz, Racz & Heberger 2015, J. Cheminform. 7:20 (Tanimoto)",
        "internal_diversity_metric": "Polykovskiy et al. 2020, Front. Pharmacol. 11:565644 (MOSES IntDiv_p)",
        "toolkit": f"RDKit {Chem.rdBase.rdkitVersion}; scipy 1.16.3",
    },
}

blob = json.dumps(diagnostic, indent=2, sort_keys=True).encode()
outname = sys.argv[1] if len(sys.argv) > 1 else "diagnostic.canonical.json"
(WORK / outname).write_bytes(blob)

print("checks_all_pass:", checks_all_pass)
for k in sorted(checks):
    print("  ", k, "=", checks[k])
print("conventionA n_amine_centres==2 :", n_A2)
print("conventionB active_nh==2       :", n_B2)
print("conventionB active_nh==4       :", n_B4)
print("hist A:", hist_A)
print("hist B:", hist_B)
print("MDA AHEW correct/wrong:", mda["ahew_correct_conventionB_g_per_eq"], mda["ahew_if_wrongly_using_conventionA_g_per_eq"])
print("wrote", WORK / outname, sha(blob))
