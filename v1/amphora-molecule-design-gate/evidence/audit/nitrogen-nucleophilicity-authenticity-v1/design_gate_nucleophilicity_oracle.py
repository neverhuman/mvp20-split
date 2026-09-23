#!/usr/bin/env python3
"""
amphora-molecule-design-gate :: nitrogen-nucleophilicity-authenticity-v1

Independent, NON-RUNTIME adversarial audit of the design gate's
`reactive_amine_hydrogen_count` semantics, using RDKit 2026.03.2 and the
published epoxide/amine addition mechanism.

MOTIVATION (the gap this closes)
--------------------------------
The shipped design-gate rule (amphora-molecule-capabilities/src/lib.rs::
design_gate_result, mirrored by the prior audit oracle
evidence/audit/rdkit-structural-facts-parity-v1/design_gate_oracle.py)
treats a nitrogen as contributing "reactive amine hydrogens" when it is
  (i)  not ring-aromatic, and
  (ii) not bonded to a carbonyl carbon (amide exclusion),
then sums that nitrogen's total attached H.

The published mechanism of epoxy cure is nucleophilic addition of a NEUTRAL
amine nitrogen LONE PAIR to the less-hindered oxirane carbon (Shechter,
Wynstra & Kurkjy 1956; Rozenberg 1986; Ellis 1993 Ch.2/6; Wicks/Jones/Pappas
2007 Ch.15). A nitrogen whose lone pair is protonated, engaged in a formal
multiple bond, or delocalised into an adjacent thiocarbonyl or sulfonyl group
is NOT an epoxide nucleophile, yet it still carries formal N-H. The shipped
two-clause rule therefore ADMITS such hydrogens.

Concretely: the fixture hardener DETA (NCCNCCN) declares 5 reactive amine
hydrogens. Its mono-protonated cation NCCNCC[NH3+] scores 6 under the shipped
rule -- protonating (i.e. deactivating) a nitrogen INCREASES the gate's
reactivity count. That is an evasion channel: a submitter can pass the
hardener reactivity clause with a non-curing species.

This oracle (a) quantifies that over-admission, (b) proposes and validates a
six-clause nucleophilic-nitrogen predicate, (c) proves the refinement is inert
on the shipped 42-record corpus (so no signed KPI result changes), (d) proves
each clause is individually necessary, and (e) shows the refinement is not
over-strict by re-deriving hand-declared amine functionality for nine real
published epoxy hardener classes that are absent from the fixture -- including
a sulfone-bearing hardener (DDS) and a hydrazide (ADH), the two classes most
at risk from clauses (sulfonyl / carbonyl).

GATES
-----
  G0  Baseline predicate reproduces the shipped semantics: identical to the
      prior audit oracle's counts on all 37 fact-bearing records, and
      reproduces all 42 shipped gate labels. (Anchors "what we are refining".)
  G1  Refined predicate is NON-REGRESSIVE: re-derives all 37 declared
      structural facts and reproduces all 42 shipped gate labels.
  G2  Hostile probes: refined count equals the hand-derived mechanistic
      expectation for every probe (ZERO for fully non-nucleophilic species, the
      residual neutral-amine count for partially protonated ones).
  G2B PROTONATION MONOTONICITY (the headline refutation): along a protonation
      ladder of five fixture hardeners, the refined count is STRICTLY
      DECREASING in the number of protons (each protonation removes that
      nitrogen from the reactive pool) while the shipped baseline count is
      STRICTLY INCREASING. The shipped rule has the sign of the effect wrong.
  G3  Evasion channel closed at the GATE level: every fully non-nucleophilic
      hostile probe that the baseline rule ACCEPTS as a hardener is REJECTED by
      the refined rule with reason missing_role_appropriate_reactive_group.
  G4  Clause necessity (ablation): dropping any one of the six clauses
      re-admits at least one hostile probe -- the clause set is irredundant.
  G5  Clause inertness on the shipped corpus: no single-clause ablation
      changes any of the 37 corpus counts, i.e. the refinement is a pure
      specificity tightening, not a re-labelling of in-scope chemistry.
  G6  Positive controls: refined counts equal hand-derived published amine
      functionality for 9 real epoxy hardeners absent from the fixture, and
      all 9 gate-accept in role `hardener`.
  G7  Refined predicate dominates BOTH shipped counting methods: for every
      hostile probe refined <= min(per-atom, SMARTS), and NEITHER baseline
      method reproduces the mechanistic expectation everywhere while the refined
      predicate does. The per-atom/SMARTS divergences are enumerated -- they
      bound the prior receipt's G4 "two-method invariance" claim to the
      in-scope corpus.

Theory / standards anchoring:
  Shechter, L., Wynstra, J. & Kurkjy, R.P. 1956, "Glycidyl Ether Reactions
    with Amines", Ind. Eng. Chem. 48(1):94-97, doi:10.1021/ie50553a029
    (amine lone-pair nucleophilic addition; amides unreactive)
  Rozenberg, B.A. 1986, "Kinetics, thermodynamics and mechanism of reactions
    of epoxy oligomers with amines", Adv. Polym. Sci. 75:113-165,
    doi:10.1007/BFb0017916
  Ellis, B. (ed.) 1993, "Chemistry and Technology of Epoxy Resins", Blackie,
    ISBN 978-0-7514-0095-4, Ch.2 (mechanism) / Ch.6 §6.2 (amine N-H)
  May, C.A. (ed.) 1988, "Epoxy Resins: Chemistry and Technology" 2nd ed.,
    Marcel Dekker, ISBN 978-0-8247-7690-9, Ch.4 (amine curing agents, AHEW)
  Wicks, Jones & Pappas 2007, "Organic Coatings: Science and Technology"
    4th ed., Wiley, Ch.15 §15.2-15.4
  Landrum, G., RDKit 2026.03.2; Daylight SMARTS theory
  oxirane = 3-membered ring {O,2C} (Van Krevelen group definition)

AUDIT_ONLY. No wet-lab, EHS, synthesis, procurement, regulatory, legal or
product-performance authority is asserted. This oracle does NOT modify the
fixture, any locked dataset, the portfolio manifest, or any signed Phase-0 KPI.
"""
import json
import sys

from rdkit import Chem
from rdkit.Chem import Descriptors

FIX = sys.argv[1]
RUN_TAG = sys.argv[2] if len(sys.argv) > 2 else "canonical"

VALID_ROLES = {"resin", "hardener"}

DOUBLE = Chem.BondType.DOUBLE
TRIPLE = Chem.BondType.TRIPLE

# ---------------------------------------------------------------- oxirane ----
EPOXIDE_SMARTS = Chem.MolFromSmarts("[#6;r3]1[#6;r3][#8;r3]1")


def count_oxirane_ringenum(mol):
    """Published oxirane definition: 3-membered ring == {O, C, C}."""
    n = 0
    for ring in mol.GetRingInfo().AtomRings():
        if len(ring) != 3:
            continue
        if sorted(mol.GetAtomWithIdx(i).GetAtomicNum() for i in ring) == [6, 6, 8]:
            n += 1
    return n


# --------------------------------------------- nucleophilic-nitrogen clauses --
# Each clause DISQUALIFIES a nitrogen from carrying epoxide-reactive amine
# hydrogens. The two clauses marked SHIPPED are already in the live rule; the
# four marked NEW are the proposed refinement.
CLAUSES = [
    "c_aromatic_n",            # SHIPPED: ring-aromatic N (lone pair in pi system)
    "c_carbonyl_adjacent",     # SHIPPED: amide/urethane/urea N (delocalised)
    "c_charged_n",             # NEW: protonated/charged N -- no free lone pair
    "c_unsaturated_n",         # NEW: formal N=/N# (imine, nitrile) -- not an amine
    "c_thiocarbonyl_adjacent", # NEW: thioamide/thiourea N (delocalised)
    "c_sulfonyl_adjacent",     # NEW: sulfon/sulfin-amide N (lone pair to S=O)
]
SHIPPED_CLAUSES = ("c_aromatic_n", "c_carbonyl_adjacent")
NEW_CLAUSES = tuple(c for c in CLAUSES if c not in SHIPPED_CLAUSES)


def clause_violations(atom):
    """Clause ids that disqualify `atom` as a nucleophilic amine nitrogen."""
    v = set()
    if atom.GetIsAromatic():
        v.add("c_aromatic_n")
    if atom.GetFormalCharge() != 0:
        v.add("c_charged_n")
    for b in atom.GetBonds():
        if b.GetBondType() in (DOUBLE, TRIPLE):
            v.add("c_unsaturated_n")
    for nb in atom.GetNeighbors():
        z = nb.GetAtomicNum()
        if z == 6:
            for b in nb.GetBonds():
                if b.GetBondType() != DOUBLE:
                    continue
                oz = b.GetOtherAtom(nb).GetAtomicNum()
                if oz == 8:
                    v.add("c_carbonyl_adjacent")
                elif oz == 16:
                    v.add("c_thiocarbonyl_adjacent")
        elif z == 16:
            for b in nb.GetBonds():
                if b.GetBondType() == DOUBLE and b.GetOtherAtom(nb).GetAtomicNum() == 8:
                    v.add("c_sulfonyl_adjacent")
    return v


def count_amineH(mol, enabled):
    """Sum attached H over nitrogens violating none of the `enabled` clauses."""
    enabled = set(enabled)
    n = 0
    for a in mol.GetAtoms():
        if a.GetAtomicNum() != 7:
            continue
        if clause_violations(a) & enabled:
            continue
        n += a.GetTotalNumHs()
    return n


def count_amineH_baseline(mol):
    """Shipped semantics == refined predicate with the four NEW clauses off."""
    return count_amineH(mol, SHIPPED_CLAUSES)


def count_amineH_refined(mol):
    return count_amineH(mol, CLAUSES)


# Prior receipt's independent Method B (SMARTS), reproduced verbatim for the
# domination / divergence comparison in G7.
AMINE_N_SMARTS = Chem.MolFromSmarts("[NX3;!$(N=*);!$(NC=O);!$([nX3]);!a]")


def count_amineH_baseline_smarts(mol):
    n = 0
    for (idx,) in mol.GetSubstructMatches(AMINE_N_SMARTS, uniquify=True):
        n += mol.GetAtomWithIdx(idx).GetTotalNumHs()
    return n


# ------------------------------------------------------------------- gate ----
def lexical_structure(smiles):
    if smiles is None:
        return False, "missing_structure"
    if smiles == "":
        return False, "empty_structure"
    if "." in smiles:
        return False, "multi_fragment_structure"
    if "*" in smiles or "~" in smiles:
        return False, "wildcard_or_query_structure"
    return True, None


def gate_decision(role, smiles, ox, nh, facts_present):
    valid_sc, struct_reason = lexical_structure(smiles)
    explicit_role = role in VALID_ROLES
    role_reactive = explicit_role and facts_present and (
        (role == "resin" and (ox or 0) > 0)
        or (role == "hardener" and (nh or 0) > 0))
    if not valid_sc:
        reason = struct_reason
    elif not explicit_role:
        reason = "missing_or_unsupported_role"
    elif not role_reactive:
        reason = "missing_role_appropriate_reactive_group"
    else:
        reason = "supported_single_component_with_role_appropriate_reactivity"
    return {
        "explicit_role": explicit_role,
        "valid_single_component": valid_sc,
        "role_appropriate_reactivity": role_reactive,
        "pass_all_hard": explicit_role and valid_sc and role_reactive and facts_present,
        "gate_reason": reason,
    }


def corpus_facts(rec, counter):
    """Re-derive (oxirane, amineH) a-priori from SMILES; None when not applicable."""
    smi, f = rec.get("smiles"), rec.get("facts")
    if f is None or not smi:
        return None, None, False
    valid_sc, _ = lexical_structure(smi)
    if not valid_sc:
        return None, None, True
    mol = Chem.MolFromSmiles(smi)
    if mol is None:
        return None, None, True
    return count_oxirane_ringenum(mol), counter(mol), True


# ------------------------------------------------------- hostile probe set ----
# (probe_id, smiles, mechanism_class, expect, note)
# `expect` = hand-derived count of epoxide-reactive amine hydrogens under the
# published mechanism, declared here BEFORE execution. It is ZERO for fully
# non-nucleophilic species; for PARTIALLY protonated hardeners it is the
# residual count over the nitrogens that remain NEUTRAL, since those are still
# genuine nucleophiles. The defect being probed is that the shipped rule counts
# the DEACTIVATED nitrogen's hydrogens as well.
HOSTILE = [
    ("deta_monoprotonated", "NCCNCC[NH3+]", "PROTONATED_AMMONIUM", 3,
     "mono-protonated fixture hardener DETA; the protonated N has no lone pair, "
     "so only the two remaining neutral N contribute (2+1); the shipped rule "
     "instead scores 6, one MORE than neutral DETA's 5"),
    ("deta_triprotonated", "[NH3+]CC[NH2+]CC[NH3+]", "PROTONATED_AMMONIUM", 0,
     "fully protonated DETA cation; every N deactivated"),
    ("ipda_monoprotonated", "CC1(C)CC(N)CC(C)(C[NH3+])C1", "PROTONATED_AMMONIUM", 2,
     "mono-protonated fixture hardener IPDA; residual neutral primary amine"),
    ("ipda_diprotonated", "CC1(C)CC([NH3+])CC(C)(C[NH3+])C1", "PROTONATED_AMMONIUM", 0,
     "fully protonated IPDA dication"),
    ("mpda_monoprotonated", "Nc1cccc([NH3+])c1", "PROTONATED_AMMONIUM", 2,
     "anilinium form of fixture hardener MPDA; residual neutral aryl amine"),
    ("mpda_diprotonated", "[NH3+]c1cccc([NH3+])c1", "PROTONATED_AMMONIUM", 0,
     "fully protonated MPDA dication"),
    ("glycine_zwitterion", "[NH3+]CC(=O)[O-]", "PROTONATED_AMMONIUM", 0,
     "single-fragment zwitterion; ammonium N-H is not an epoxide nucleophile"),
    ("methanesulfonamide", "CS(N)(=O)=O", "SULFONAMIDE", 0,
     "N lone pair delocalised into S=O; not an epoxy curing amine"),
    ("p_toluenesulfonamide", "Cc1ccc(cc1)S(N)(=O)=O", "SULFONAMIDE", 0,
     "aryl sulfonamide N-H, acidified, non-nucleophilic"),
    ("n_methylmethanesulfonamide", "CNS(C)(=O)=O", "SULFONAMIDE", 0,
     "secondary sulfonamide N-H"),
    ("ethanimine", "CC=N", "IMINE", 0,
     "sp2 =N-H is an imine, not an amine nitrogen"),
    ("methanimine", "C=N", "IMINE", 0,
     "simplest aldimine; formal N-H on a doubly bonded N"),
    ("thiourea", "NC(=S)N", "THIOAMIDE", 0,
     "thiocarbonyl-delocalised N-H; thiourea acts as accelerator, not co-reactant"),
    ("thioacetamide", "CC(N)=S", "THIOAMIDE", 0,
     "thioamide N-H delocalised into C=S"),
    ("pyrrole", "c1cc[nH]c1", "AROMATIC_NH", 0,
     "aromatic N-H; lone pair in the pi system (shipped clause regression)"),
    ("imidazole", "c1c[nH]cn1", "AROMATIC_NH", 0,
     "aromatic azole N-H (shipped clause regression)"),
    ("acetamide", "CC(N)=O", "AMIDE", 0,
     "amide N-H unreactive to epoxide (Shechter 1956) (shipped clause regression)"),
    ("urea", "NC(N)=O", "AMIDE", 0,
     "urea N-H delocalised (shipped clause regression)"),
    ("methyl_carbamate", "COC(N)=O", "AMIDE", 0,
     "urethane N-H delocalised (shipped clause regression)"),
    ("benzyltrimethylammonium", "C[N+](C)(C)Cc1ccccc1", "QUATERNARY_AMMONIUM", 0,
     "quaternary ammonium epoxy accelerator; no N-H at all"),
    ("acetaldoxime", "CC=NO", "OXIME", 0,
     "oxime N carries no H; the acidic H sits on O"),
]

# ------------------------------------------------- protonation ladders (G2B) --
# Each ladder walks a REAL fixture hardener from the neutral free base to the
# fully protonated cation. Published mechanism: every protonation removes one
# nitrogen's lone pair, so the epoxide-reactive amine-hydrogen count must fall
# monotonically. `expect` values are hand-derived per rung.
LADDERS = [
    ("deta", [("NCCNCCN", 0, 5), ("NCCNCC[NH3+]", 1, 3),
              ("[NH3+]CCNCC[NH3+]", 2, 1), ("[NH3+]CC[NH2+]CC[NH3+]", 3, 0)]),
    ("ipda", [("CC1(C)CC(N)CC(C)(CN)C1", 0, 4),
              ("CC1(C)CC(N)CC(C)(C[NH3+])C1", 1, 2),
              ("CC1(C)CC([NH3+])CC(C)(C[NH3+])C1", 2, 0)]),
    ("mpda", [("Nc1cccc(N)c1", 0, 4), ("Nc1cccc([NH3+])c1", 1, 2),
              ("[NH3+]c1cccc([NH3+])c1", 2, 0)]),
    ("hmda", [("NCCCCCCN", 0, 4), ("NCCCCCC[NH3+]", 1, 2),
              ("[NH3+]CCCCCC[NH3+]", 2, 0)]),
    ("mxda", [("NCc1cccc(CN)c1", 0, 4), ("NCc1cccc(C[NH3+])c1", 1, 2),
              ("[NH3+]Cc1cccc(C[NH3+])c1", 2, 0)]),
]

# Salt/dot forms must fail closed on the LEXICAL single-component clause, which
# is a different defence layer -- reported separately, not part of G2.
SALT_FORMS = [
    ("deta_dihydrochloride", "NCCNCCN.Cl.Cl", "AMINE_SALT_MULTIFRAGMENT"),
    ("mxda_dihydrochloride", "NCc1cccc(CN)c1.Cl.Cl", "AMINE_SALT_MULTIFRAGMENT"),
]

# ------------------------------------------------------ positive controls -----
# Real, published epoxy-amine hardeners ABSENT from the shipped fixture.
# `expect` = hand-derived active amine hydrogen count per the published
# definition (H on neutral, non-aromatic, non-amide, non-sulfonamide amine N),
# written down here BEFORE RDKit runs -- the refined counter must reproduce it.
POSITIVE = [
    ("dds_44_diaminodiphenylsulfone", "Nc1ccc(cc1)S(=O)(=O)c1ccc(N)cc1", 4,
     "May 1988 Ch.4 aromatic sulfone hardener; N bonded to aryl C, NOT to S -- "
     "critical specificity control for the sulfonyl clause"),
    ("adipic_dihydrazide", "NNC(=O)CCCCC(=O)NN", 4,
     "May 1988 Ch.4 latent hydrazide hardener; terminal NH2 active, inner "
     "hydrazide N-H carbonyl-excluded -- specificity control for carbonyl clause"),
    ("amidoamine_model_nonanoyl_eda", "CCCCCCCCC(=O)NCCN", 2,
     "model amidoamine of the polyamide hardeners used in marine epoxy "
     "primers; amide N excluded, free terminal NH2 retained"),
    ("aminoethylpiperazine_aep", "NCCN1CCNCC1", 3,
     "Ellis 1993 Ch.6 / May 1988 Ch.4 cycloaliphatic hardener AEP"),
    ("diethylaminopropylamine_deapa", "CCN(CC)CCCN", 2,
     "tertiary-amine-bearing hardener; tertiary N contributes 0 amine H"),
    ("bis_3_aminopropyl_piperazine", "NCCCN1CCN(CCCN)CC1", 4,
     "N,N'-bis(3-aminopropyl)piperazine hardener"),
    ("aminoethylethanolamine_aeea", "NCCNCCO", 3,
     "AEEA hardener/diluent; hydroxyl contributes no amine H"),
    ("polyoxypropylenediamine_model_dimer", "CC(N)COCC(C)N", 4,
     "single-ether model dimer of the polyoxypropylenediamine (Jeffamine D-230) "
     "hardener class used in marine epoxy; the implied AHEW below is that of the "
     "MODEL dimer, not of commercial D-230 (Mn ~230, AHEW ~60)"),
    ("trimethylhexamethylenediamine_tmd", "NCC(C)(C)CC(C)CCN", 4,
     "2,2,4-trimethyl-1,6-hexanediamine (TMD) hardener, C9H22N2"),
]


def main():
    d = json.load(open(FIX))
    recs = d["records"]

    # ---------------- G0: baseline predicate == shipped semantics -------------
    g0_facts, g0_labels = [], []
    for r in recs:
        ox, nh, applicable = corpus_facts(r, count_amineH_baseline)
        if applicable and r.get("facts") is not None and ox is not None:
            f = r["facts"]
            g0_facts.append({
                "case_id": r["case_id"],
                "baseline_oxirane": ox, "declared_oxirane": f.get("oxirane_ring_count"),
                "baseline_amineH": nh,
                "declared_amineH": f.get("reactive_amine_hydrogen_count"),
                "match": ox == f.get("oxirane_ring_count")
                         and nh == f.get("reactive_amine_hydrogen_count"),
            })
        got = gate_decision(r.get("role"), r.get("smiles"), ox, nh,
                            r.get("facts") is not None)
        exp = {
            "explicit_role": r["expected_explicit_role"],
            "valid_single_component": r["expected_valid_single_component"],
            "role_appropriate_reactivity": r["expected_role_appropriate_reactivity"],
            "pass_all_hard": r["expected_pass_all_hard"],
            "gate_reason": r["expected_gate_reason"],
        }
        g0_labels.append({"case_id": r["case_id"], "match": got == exp,
                          "mismatch": None if got == exp else {"got": got, "exp": exp}})
    g0_pass = (len(g0_facts) == 37 and all(x["match"] for x in g0_facts)
               and len(g0_labels) == 42 and all(x["match"] for x in g0_labels))

    # ---------------- G1: refined predicate is non-regressive ----------------
    g1_facts, g1_labels = [], []
    for r in recs:
        ox, nh, applicable = corpus_facts(r, count_amineH_refined)
        if applicable and r.get("facts") is not None and ox is not None:
            f = r["facts"]
            g1_facts.append({
                "case_id": r["case_id"],
                "refined_oxirane": ox, "declared_oxirane": f.get("oxirane_ring_count"),
                "refined_amineH": nh,
                "declared_amineH": f.get("reactive_amine_hydrogen_count"),
                "match": ox == f.get("oxirane_ring_count")
                         and nh == f.get("reactive_amine_hydrogen_count"),
            })
        got = gate_decision(r.get("role"), r.get("smiles"), ox, nh,
                            r.get("facts") is not None)
        exp = {
            "explicit_role": r["expected_explicit_role"],
            "valid_single_component": r["expected_valid_single_component"],
            "role_appropriate_reactivity": r["expected_role_appropriate_reactivity"],
            "pass_all_hard": r["expected_pass_all_hard"],
            "gate_reason": r["expected_gate_reason"],
        }
        g1_labels.append({"case_id": r["case_id"], "subgroup": r["subgroup"],
                          "match": got == exp,
                          "mismatch": None if got == exp else {"got": got, "exp": exp}})
    g1_pass = (len(g1_facts) == 37 and all(x["match"] for x in g1_facts)
               and len(g1_labels) == 42 and all(x["match"] for x in g1_labels))

    # ---------------- G2 / G3 / G7: hostile probes ---------------------------
    hostile = []
    for pid, smi, klass, expect, note in HOSTILE:
        mol = Chem.MolFromSmiles(smi)
        base = count_amineH_baseline(mol)
        base_smarts = count_amineH_baseline_smarts(mol)
        ref = count_amineH_refined(mol)
        ox = count_oxirane_ringenum(mol)
        gb = gate_decision("hardener", smi, ox, base, True)
        gr = gate_decision("hardener", smi, ox, ref, True)
        hostile.append({
            "probe_id": pid, "smiles": smi, "mechanism_class": klass, "note": note,
            "baseline_amineH_peratom": base,
            "baseline_amineH_smarts": base_smarts,
            "refined_amineH": ref,
            "mechanistic_expected_amineH": expect,
            "refined_matches_expectation": ref == expect,
            "baseline_peratom_matches_expectation": base == expect,
            "baseline_smarts_matches_expectation": base_smarts == expect,
            "baseline_over_admits": base > expect,
            "baseline_over_admission_excess": base - expect,
            "fully_non_nucleophilic": expect == 0,
            "baseline_methods_diverge": base != base_smarts,
            "refined_dominates_both": ref <= min(base, base_smarts) and ref == expect,
            "baseline_gate_accepts_as_hardener": gb["pass_all_hard"],
            "refined_gate_accepts_as_hardener": gr["pass_all_hard"],
            "refined_gate_reason": gr["gate_reason"],
            "violated_clauses": sorted(
                set().union(*[clause_violations(a) for a in mol.GetAtoms()
                              if a.GetAtomicNum() == 7]) if any(
                    a.GetAtomicNum() == 7 for a in mol.GetAtoms()) else set()),
        })
    g2_pass = all(h["refined_matches_expectation"] for h in hostile)

    over = [h for h in hostile if h["baseline_over_admits"]]
    # A gate-level EVASION is a fully non-nucleophilic species (expect == 0)
    # that the baseline nonetheless accepts in role `hardener`.
    evaded = [h for h in hostile
              if h["fully_non_nucleophilic"] and h["baseline_gate_accepts_as_hardener"]]
    g3_pass = bool(evaded) and all(
        (not h["refined_gate_accepts_as_hardener"])
        and h["refined_gate_reason"] == "missing_role_appropriate_reactive_group"
        for h in evaded)
    n_base_a_ok = sum(1 for h in hostile if h["baseline_peratom_matches_expectation"])
    n_base_b_ok = sum(1 for h in hostile if h["baseline_smarts_matches_expectation"])
    g7_pass = (all(h["refined_dominates_both"] for h in hostile)
               and n_base_a_ok < len(hostile) and n_base_b_ok < len(hostile))
    divergent = [h["probe_id"] for h in hostile if h["baseline_methods_diverge"]]

    # ---------------- G2B: protonation monotonicity --------------------------
    ladders = []
    for name, rungs in LADDERS:
        rows = []
        for smi, nprot, expect in rungs:
            mol = Chem.MolFromSmiles(smi)
            base = count_amineH_baseline(mol)
            ref = count_amineH_refined(mol)
            gb = gate_decision("hardener", smi, count_oxirane_ringenum(mol), base, True)
            gr = gate_decision("hardener", smi, count_oxirane_ringenum(mol), ref, True)
            rows.append({
                "smiles": smi, "n_protons": nprot,
                "hand_derived_expected_amineH": expect,
                "refined_amineH": ref, "baseline_amineH": base,
                "refined_matches_expectation": ref == expect,
                "baseline_gate_accepts_as_hardener": gb["pass_all_hard"],
                "refined_gate_accepts_as_hardener": gr["pass_all_hard"],
            })
        r = [x["refined_amineH"] for x in rows]
        b = [x["baseline_amineH"] for x in rows]
        ladders.append({
            "hardener": name, "rungs": rows, "n_rungs": len(rows),
            "refined_series": r, "baseline_series": b,
            "refined_strictly_decreasing": all(r[i] > r[i + 1] for i in range(len(r) - 1)),
            "baseline_strictly_increasing": all(b[i] < b[i + 1] for i in range(len(b) - 1)),
            "refined_matches_all_expectations": all(x["refined_matches_expectation"] for x in rows),
            "baseline_direction_verdict": "WRONG_SIGN"
                if all(b[i] < b[i + 1] for i in range(len(b) - 1)) else "OTHER",
            "fully_protonated_baseline_accepts": rows[-1]["baseline_gate_accepts_as_hardener"],
            "fully_protonated_refined_accepts": rows[-1]["refined_gate_accepts_as_hardener"],
        })
    g2b_pass = all(
        l["refined_strictly_decreasing"] and l["baseline_strictly_increasing"]
        and l["refined_matches_all_expectations"]
        and l["fully_protonated_baseline_accepts"]
        and not l["fully_protonated_refined_accepts"]
        for l in ladders)

    salts = []
    for pid, smi, klass in SALT_FORMS:
        gb = gate_decision("hardener", smi, None, None, True)
        salts.append({"probe_id": pid, "smiles": smi, "mechanism_class": klass,
                      "gate_reason": gb["gate_reason"],
                      "fail_closed": not gb["pass_all_hard"],
                      "defence_layer": "LEXICAL_SINGLE_COMPONENT"})
    salts_pass = all(s["fail_closed"] for s in salts)

    # ---------------- G4: clause necessity (ablation) ------------------------
    ablation = []
    for dropped in CLAUSES:
        enabled = [c for c in CLAUSES if c != dropped]
        readmitted = []
        for pid, smi, klass, expect, _ in HOSTILE:
            mol = Chem.MolFromSmiles(smi)
            n = count_amineH(mol, enabled)
            if n > expect:
                readmitted.append({"probe_id": pid, "mechanism_class": klass,
                                   "amineH_when_dropped": n,
                                   "mechanistic_expected_amineH": expect})
        ablation.append({
            "dropped_clause": dropped,
            "shipped_or_new": "SHIPPED" if dropped in SHIPPED_CLAUSES else "NEW",
            "n_hostile_readmitted": len(readmitted),
            "readmitted": readmitted,
            "clause_necessary": len(readmitted) > 0,
        })
    g4_pass = len(ablation) == len(CLAUSES) and all(a["clause_necessary"] for a in ablation)

    # ---------------- G5: clause inertness on the shipped corpus -------------
    ref_corpus = {}
    for r in recs:
        ox, nh, applicable = corpus_facts(r, count_amineH_refined)
        if applicable and r.get("facts") is not None and ox is not None:
            ref_corpus[r["case_id"]] = nh
    inertness = []
    for dropped in CLAUSES:
        enabled = [c for c in CLAUSES if c != dropped]
        changed = []
        for r in recs:
            ox, nh, applicable = corpus_facts(r, lambda m, e=enabled: count_amineH(m, e))
            if applicable and r.get("facts") is not None and ox is not None:
                if nh != ref_corpus[r["case_id"]]:
                    changed.append({"case_id": r["case_id"],
                                    "refined": ref_corpus[r["case_id"]], "ablated": nh})
        inertness.append({"dropped_clause": dropped, "n_corpus_records_changed": len(changed),
                          "changed": changed, "inert_on_corpus": len(changed) == 0})
    g5_pass = all(x["inert_on_corpus"] for x in inertness)

    # ---------------- G6: positive controls ----------------------------------
    positive = []
    for pid, smi, expect, prov in POSITIVE:
        mol = Chem.MolFromSmiles(smi)
        ref = count_amineH_refined(mol)
        base = count_amineH_baseline(mol)
        ox = count_oxirane_ringenum(mol)
        gr = gate_decision("hardener", smi, ox, ref, True)
        mw = Descriptors.MolWt(mol)
        positive.append({
            "probe_id": pid, "smiles": smi,
            "hand_derived_expected_amineH": expect,
            "refined_amineH": ref, "baseline_amineH": base,
            "match": ref == expect,
            "refined_gate_accepts_as_hardener": gr["pass_all_hard"],
            "refined_gate_reason": gr["gate_reason"],
            "molecular_weight_g_mol": round(mw, 3),
            "implied_ahew_g_per_eq": round(mw / ref, 3) if ref else None,
            "provenance": prov,
        })
    g6_pass = all(p["match"] and p["refined_gate_accepts_as_hardener"] for p in positive)

    gates = {
        "g0_baseline_reproduces_shipped_semantics": g0_pass,
        "g1_refined_non_regressive_on_corpus": g1_pass,
        "g2_hostile_probes_match_mechanistic_expectation": g2_pass,
        "g2b_protonation_monotonicity_direction": g2b_pass,
        "g3_evasion_channel_closed_at_gate": g3_pass,
        "g4_clause_set_irredundant": g4_pass,
        "g5_clauses_inert_on_shipped_corpus": g5_pass,
        "g6_positive_controls_not_over_strict": g6_pass,
        "g7_refined_dominates_both_baseline_methods": g7_pass,
        "salt_forms_fail_closed_lexically": salts_pass,
    }
    gates["all_pass"] = all(gates.values())

    diag = {
        "schema": "amphora.molecule-design-gate.nitrogen-nucleophilicity-authenticity.diagnostic.v1",
        "study_id": "nitrogen-nucleophilicity-authenticity-v1",
        "module": "amphora-molecule-design-gate",
        "authority": "AUDIT_ONLY",
        "authority_ceiling": "REAL_ARITHMETIC",
        "run_type": "NON_RUNTIME_INDEPENDENT_CHEMINFORMATICS_ORACLE",
        "purpose": (
            "Adversarially audit the design gate's reactive_amine_hydrogen_count "
            "semantics against the published epoxide-amine nucleophilic addition "
            "mechanism, quantify the over-admission surface of the shipped "
            "two-clause rule, and validate a six-clause nucleophilic-nitrogen "
            "predicate that is non-regressive on the shipped corpus."),
        "hypothesis": (
            "The shipped rule (non-aromatic AND non-amide N, sum all attached H) "
            "over-admits formal N-H that the published mechanism says cannot open "
            "an oxirane -- protonated ammonium, imine, thioamide and sulfonamide "
            "N-H -- creating a hardener-reactivity evasion channel; a six-clause "
            "nucleophilic-nitrogen predicate closes it while leaving all 37 "
            "declared corpus facts and all 42 shipped gate labels unchanged."),
        "non_circularity": (
            "Counts are computed FROM SMILES by RDKit. Hostile-probe expectations "
            "are fixed at ZERO by the published mechanism (lone-pair nucleophile), "
            "not by any Amphora artefact. Positive-control expectations are "
            "hand-derived published amine functionality declared in the oracle "
            "source before execution. The fixture's declared integers are only a "
            "comparison target."),
        "adversarial_relevance": (
            "A submitter can satisfy the hardener reactivity clause with a "
            "non-curing species: mono-protonated DETA scores 6 baseline amine "
            "hydrogens versus neutral DETA's 5, so DEACTIVATING a nitrogen "
            "INCREASES the shipped gate's reactivity count. Sulfonamides, "
            "thioureas and imines are admitted on the same defect."),
        "defect_disclosure": {
            "shipped_rule_defect": "OVER_ADMISSION_OF_NON_NUCLEOPHILIC_FORMAL_NH",
            "affects_signed_phase0_kpi_result": False,
            "why_not": (
                "The shipped 42-record fixture contains no charged, imine, "
                "thioamide or sulfonamide nitrogen, so every shipped expected "
                "label remains correct (G0 and G1 both reproduce 42/42). The "
                "defect is an applicability-envelope gap outside the fixture, "
                "not an error in any signed result."),
            "monotonic_direction": "REFINEMENT_IS_STRICTLY_TIGHTENING",
        },
        "theory_reference": [
            "Shechter, Wynstra & Kurkjy 1956, Ind. Eng. Chem. 48(1):94-97, "
            "doi:10.1021/ie50553a029 (amine lone-pair addition; amides unreactive)",
            "Rozenberg 1986, Adv. Polym. Sci. 75:113-165, doi:10.1007/BFb0017916",
            "Ellis 1993 Chemistry and Technology of Epoxy Resins, "
            "ISBN 978-0-7514-0095-4, Ch.2 / Ch.6 §6.2",
            "May 1988 Epoxy Resins: Chemistry and Technology 2nd ed., "
            "ISBN 978-0-8247-7690-9, Ch.4 (amine curing agents, AHEW)",
            "Wicks/Jones/Pappas 2007 Organic Coatings 4th ed. Ch.15 §15.2-15.4",
            "Landrum RDKit 2026.03.2; Daylight SMARTS theory",
            "oxirane = 3-membered ring {O,2C} (Van Krevelen group definition)",
        ],
        "runtime_source_anchors": {
            "live_rust": "amphora-molecule-capabilities/src/lib.rs::design_gate_result",
            "fixture": "reference/phase0-design-gate-known-answer.v1.json",
            "prior_receipts": [
                "evidence/audit/rdkit-structural-facts-parity-v1",
                "evidence/audit/smiles-representation-invariance-v1",
            ],
        },
        "rdkit_version": Chem.rdBase.rdkitVersion,
        "clause_set": {
            "clauses": CLAUSES,
            "shipped_clauses": list(SHIPPED_CLAUSES),
            "new_clauses": list(NEW_CLAUSES),
            "predicate": (
                "A nitrogen contributes epoxide-reactive amine hydrogens iff it "
                "is not ring-aromatic, not formally charged, carries no formal "
                "double/triple bond, and is bonded to no carbonyl carbon, "
                "thiocarbonyl carbon, or sulfonyl/sulfinyl sulfur."),
        },
        "g0_baseline_shipped_semantics": {
            "fact_records": g0_facts, "n_facts": len(g0_facts),
            "label_records": g0_labels, "n_labels": len(g0_labels),
            "all_match": g0_pass,
        },
        "g1_refined_non_regression": {
            "fact_records": g1_facts, "n_facts": len(g1_facts),
            "label_records": g1_labels, "n_labels": len(g1_labels),
            "all_match": g1_pass,
        },
        "g2_g3_g7_hostile_probes": {
            "records": hostile, "n": len(hostile),
            "n_baseline_over_admitting": len(over),
            "total_baseline_over_admission_excess_H": sum(
                h["baseline_over_admission_excess"] for h in hostile),
            "n_baseline_gate_evasions": len(evaded),
            "evaded_probe_ids": [h["probe_id"] for h in evaded],
            "n_refined_matches_expectation": sum(
                1 for h in hostile if h["refined_matches_expectation"]),
            "n_baseline_peratom_matches_expectation": n_base_a_ok,
            "n_baseline_smarts_matches_expectation": n_base_b_ok,
            "n_baseline_method_divergences": len(divergent),
            "divergent_probe_ids": divergent,
            "all_match_expectation": g2_pass,
            "all_evasions_closed": g3_pass,
            "refined_dominates_both_methods": g7_pass,
        },
        "g2b_protonation_monotonicity": {
            "records": ladders, "n_ladders": len(ladders),
            "n_rungs_total": sum(l["n_rungs"] for l in ladders),
            "all_refined_strictly_decreasing": all(
                l["refined_strictly_decreasing"] for l in ladders),
            "all_baseline_strictly_increasing": all(
                l["baseline_strictly_increasing"] for l in ladders),
            "verdict": ("SHIPPED_RULE_HAS_WRONG_SIGN_OF_PROTONATION_EFFECT"
                        if g2b_pass else "INCONCLUSIVE"),
            "all_pass": g2b_pass,
        },
        "salt_form_probes": {"records": salts, "n": len(salts), "all_fail_closed": salts_pass},
        "g4_clause_necessity_ablation": {"records": ablation, "n": len(ablation),
                                         "all_necessary": g4_pass},
        "g5_clause_inertness_on_corpus": {"records": inertness, "n": len(inertness),
                                          "all_inert": g5_pass},
        "g6_positive_controls": {"records": positive, "n": len(positive),
                                 "all_match_and_accept": g6_pass},
        "gates": gates,
        "counts": {
            "corpus_fact_bearing_records": len(g1_facts),
            "corpus_total_gate_records": len(g1_labels),
            "hostile_probes": len(hostile),
            "hostile_mechanism_classes": len({h["mechanism_class"] for h in hostile}),
            "baseline_over_admitting_probes": len(over),
            "baseline_gate_evasions_closed": len(evaded),
            "protonation_ladders": len(ladders),
            "protonation_ladder_rungs": sum(l["n_rungs"] for l in ladders),
            "salt_form_probes": len(salts),
            "clauses": len(CLAUSES),
            "new_clauses": len(NEW_CLAUSES),
            "positive_controls": len(positive),
            "total_molecule_evaluations": (
                len(g1_facts) * 2 + len(hostile) * 3 + len(salts)
                + sum(l["n_rungs"] for l in ladders) * 2
                + len(CLAUSES) * (len(HOSTILE) + len(g1_facts)) + len(positive) * 2),
        },
        "closes": [
            "First mechanism-grounded audit of the design gate's amine-hydrogen "
            "semantics: identifies and quantifies an over-admission surface in "
            "the shipped two-clause rule (protonated ammonium, imine, thioamide, "
            "sulfonamide formal N-H) using the published epoxide-amine "
            "nucleophilic addition mechanism as the expectation source.",
            "Establishes the defect quantitatively as a SIGN error: along "
            "protonation ladders of five fixture hardeners (DETA, IPDA, MPDA, "
            "HMDA, MXDA) the shipped count RISES monotonically with protonation "
            "while the mechanism-correct count FALLS monotonically to zero. "
            "Mono-protonated DETA scores 6 shipped amine hydrogens versus "
            "neutral DETA's 5, and every fully protonated cation still "
            "gate-ACCEPTS as a hardener under the shipped rule.",
            "Validates a six-clause nucleophilic-nitrogen predicate that fails "
            "closed on every hostile probe, closes every gate-level evasion, is "
            "irredundant under single-clause ablation, and is provably INERT on "
            "the shipped corpus (37/37 facts and 42/42 labels unchanged), so no "
            "signed Phase-0 result is disturbed.",
            "Extends the module's applicability evidence beyond the fixture: nine "
            "real published epoxy hardener classes absent from the corpus "
            "(aromatic sulfone DDS, hydrazide ADH, amidoamine, AEP, DEAPA, "
            "bis-aminopropylpiperazine, AEEA, polyetheramine, TMD) re-derive "
            "their hand-declared amine functionality exactly, proving the added "
            "sulfonyl and carbonyl clauses are not over-strict.",
            "Bounds the prior receipt's G4 two-method invariance claim: the "
            "per-atom and SMARTS baseline counters encode DIFFERENT chemistry and "
            "diverge on the hostile classes; invariance held only because those "
            "classes are absent from the in-scope corpus.",
        ],
        "does_not_close": [
            "Does not modify the live Rust runtime, the fixture, or any signed "
            "Phase-0 KPI; the refined predicate is recorded as audit evidence "
            "only. Wiring it into amphora-molecule-capabilities is Phase-1 work "
            "requiring the pinned RDKit C++ boundary.",
            "Does not resolve alpha-heteroatom amines (hydrazine N-N, "
            "hydroxylamine N-O) as a class: the literature supports their "
            "nucleophilicity, so they are deliberately ADMITTED rather than "
            "excluded, and the fixture holds no exemplar beyond the hydrazide "
            "positive control. No clause was added for them.",
            "Does not treat delocalised amidine/guanidine/dicyandiamide N-H, "
            "where the mechanistic call is genuinely ambiguous (latent "
            "accelerator versus co-reactant); those were excluded from the probe "
            "set rather than assigned an expectation.",
            "Does not quantify RELATIVE amine nucleophilicity or cure rate; the "
            "predicate is binary structural applicability, not a kinetic model.",
            "Does not establish EHS, synthesis, qualification, procurement, "
            "regulatory, legal, or product-performance authority.",
        ],
        "dataset_fixture_sha256_note": "recorded by signer",
    }
    print(json.dumps(diag, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
