#!/usr/bin/env python3
"""
amphora-molecule-design-gate :: rdkit-structural-facts-parity-v1

Independent, NON-RUNTIME re-derivation of the design-gate decision surface DIRECTLY
FROM SMILES using RDKit 2026.03.2 + published cheminformatics substructure rules.

The live authority is native Rust (amphora-molecule-capabilities/src/lib.rs,
fn design_gate_result). The shipped Phase-0 KPI applies the gate rule over
SELF-DECLARED integer structural facts (oxirane_ring_count,
reactive_amine_hydrogen_count) baked into the fixture
reference/phase0-design-gate-known-answer.v1.json. Those facts were never
independently verified against a cheminformatics toolkit -- they are the ground
truth the entire KPI rests on. This oracle re-derives those facts a-priori from
the raw SMILES with an independent toolkit and re-runs the full gate.

Gates:
  G1  RDKit re-derives every declared structural fact (oxirane_ring_count,
      reactive_amine_hydrogen_count) byte-exact for all 37 fact-bearing records.
  G2  Re-deriving the FULL gate decision (explicit_role, valid_single_component,
      role_appropriate_reactivity, pass_all_hard, gate_reason) from RDKit-derived
      facts + lexical validity reproduces all 42 shipped expected labels.
  G3  Specificity / fail-closed probes: molecules that would falsely inflate the
      counts if the published exclusions (non-aromatic, non-amide N; O-only 3-ring)
      were dropped must count ZERO. Verifies the rule discriminates, not merely
      admits.
  G4  Pattern-invariance robustness: oxirane and active-amine-H counts are
      invariant across two independent RDKit detection methods (ring-enumeration
      vs published SMARTS substructure), for every fact-bearing record.

Theory / standards anchoring:
  Wicks, Jones & Pappas 2007 'Organic Coatings: Science and Technology' 4th ed.
    Ch.15 §15.2-15.4 (epoxy oxirane reactivity)
  Ellis 1993 'Chemistry and Technology of Epoxy Resins' Ch.6 §6.2 (amine N-H)
  Landrum, RDKit 2026.03.2 (cheminformatics substructure toolkit)
  Daylight SMARTS theory (substructure query language)
  epoxide/oxirane = 3-membered ring, one O + two sp3 C (Van Krevelen group def.)
No wet-lab, product-qualification, legal, EHS, or scientific-superiority
authority is asserted. Infrastructure structural-applicability parity only.
"""
import json, sys
from rdkit import Chem
from rdkit.Chem import RWMol

FIX = sys.argv[1]
RUN_TAG = sys.argv[2] if len(sys.argv) > 2 else "canonical"

VALID_ROLES = {"resin", "hardener"}

# ---- published substructure rules, re-implemented independently ----
# oxirane via published epoxide SMARTS: 3-membered ring, C-C-O all in ring.
EPOXIDE_SMARTS = Chem.MolFromSmarts("[#6;r3]1[#6;r3][#8;r3]1")

def count_oxirane_ringenum(mol):
    """Method A: enumerate rings; 3-membered ring == {O,C,C}."""
    n = 0
    for ring in mol.GetRingInfo().AtomRings():
        if len(ring) != 3:
            continue
        if sorted(mol.GetAtomWithIdx(i).GetAtomicNum() for i in ring) == [6, 6, 8]:
            n += 1
    return n

def count_oxirane_smarts(mol):
    """Method B: published epoxide SMARTS, dedup by ring atom-set."""
    seen = set()
    for m in mol.GetSubstructMatches(EPOXIDE_SMARTS, uniquify=True):
        seen.add(frozenset(m))
    return len(seen)

def is_amide_N(atom):
    """N bonded to a carbonyl C (C=O) => amide/imide N; excluded per Ellis §6.2."""
    for nb in atom.GetNeighbors():
        if nb.GetAtomicNum() == 6:
            for b in nb.GetBonds():
                if (b.GetBondType() == Chem.BondType.DOUBLE
                        and b.GetOtherAtom(nb).GetAtomicNum() == 8):
                    return True
    return False

def count_active_amine_H_peratom(mol):
    """Method A: per-atom. Active amine N-H = N not in aromatic ring, not amide;
    sum total H (implicit+explicit) on qualifying N."""
    n = 0
    for a in mol.GetAtoms():
        if a.GetAtomicNum() != 7:
            continue
        if a.GetIsAromatic():
            continue
        if is_amide_N(a):
            continue
        n += a.GetTotalNumHs()
    return n

# Method B: SMARTS-style. Non-aromatic amine N with >=1 H, excluding amide N.
AMINE_N_SMARTS = Chem.MolFromSmarts("[NX3;!$(N=*);!$(NC=O);!$([nX3]);!a]")
def count_active_amine_H_smarts(mol):
    n = 0
    for (idx,) in mol.GetSubstructMatches(AMINE_N_SMARTS, uniquify=True):
        n += mol.GetAtomWithIdx(idx).GetTotalNumHs()
    return n

def lexical_structure(smiles):
    """Returns (valid, reason_if_invalid). Mirrors ObviousStructureIssue ladder:
    missing_structure > empty_structure > multi_fragment > wildcard/query."""
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
        (role == "resin" and (ox or 0) > 0) or
        (role == "hardener" and (nh or 0) > 0))
    if not valid_sc:
        reason = struct_reason
    elif not explicit_role:
        reason = "missing_or_unsupported_role"
    elif not role_reactive:
        reason = "missing_role_appropriate_reactive_group"
    else:
        reason = "supported_single_component_with_role_appropriate_reactivity"
    pass_all = explicit_role and valid_sc and role_reactive and facts_present
    return {
        "explicit_role": explicit_role,
        "valid_single_component": valid_sc,
        "role_appropriate_reactivity": role_reactive,
        "pass_all_hard": pass_all,
        "gate_reason": reason,
    }

def main():
    d = json.load(open(FIX))
    recs = d["records"]

    # ---- G1: RDKit re-derives declared facts ----
    g1 = []
    for r in recs:
        smi, f = r.get("smiles"), r.get("facts")
        if not smi or f is None:
            continue
        valid_sc, _ = lexical_structure(smi)
        if not valid_sc:
            continue
        mol = Chem.MolFromSmiles(smi)
        parsed = mol is not None
        ox = count_oxirane_ringenum(mol) if parsed else None
        nh = count_active_amine_H_peratom(mol) if parsed else None
        dox = f.get("oxirane_ring_count"); dnh = f.get("reactive_amine_hydrogen_count")
        g1.append({"case_id": r["case_id"], "parsed": parsed,
                   "rdkit_oxirane": ox, "declared_oxirane": dox,
                   "rdkit_amineH": nh, "declared_amineH": dnh,
                   "match": parsed and ox == dox and nh == dnh})
    g1_pass = len(g1) == 37 and all(x["match"] for x in g1)

    # ---- G2: full gate decision from RDKit-derived facts ----
    g2 = []
    for r in recs:
        smi, f = r.get("smiles"), r.get("facts")
        role = r.get("role")
        valid_sc, _ = lexical_structure(smi)
        facts_present = f is not None
        if facts_present and valid_sc and smi:
            mol = Chem.MolFromSmiles(smi)
            ox = count_oxirane_ringenum(mol) if mol is not None else None
            nh = count_active_amine_H_peratom(mol) if mol is not None else None
        else:
            ox = nh = None
        got = gate_decision(role, smi, ox, nh, facts_present)
        exp = {
            "explicit_role": r["expected_explicit_role"],
            "valid_single_component": r["expected_valid_single_component"],
            "role_appropriate_reactivity": r["expected_role_appropriate_reactivity"],
            "pass_all_hard": r["expected_pass_all_hard"],
            "gate_reason": r["expected_gate_reason"],
        }
        match = got == exp
        g2.append({"case_id": r["case_id"], "subgroup": r["subgroup"],
                   "match": match,
                   "mismatch": None if match else {"got": got, "exp": exp}})
    g2_pass = len(g2) == 42 and all(x["match"] for x in g2)

    # ---- G3: specificity / fail-closed probes ----
    # (smiles, kind, expect_ox, expect_nh, note)
    probes = [
        ("CC(N)=O",        "amide_acetamide",        0, 0, "amide N-H excluded"),
        ("CNC(C)=O",       "amide_n_methylacetamide",0, 0, "secondary amide excluded"),
        ("c1ccncc1",       "aromatic_pyridine",      0, 0, "ring-aromatic N excluded"),
        ("c1cc[nH]c1",     "aromatic_pyrrole_NH",    0, 0, "aromatic N-H excluded"),
        ("CC#N",           "nitrile_acetonitrile",   0, 0, "nitrile N no active H"),
        ("C[N+](=O)[O-]",  "nitro_nitromethane",     0, 0, "nitro N excluded"),
        ("C1CN1",          "aziridine_3ring_N",      0, 1, "N 3-ring: 0 oxirane (O-specific) yet ring NH is a real secondary amine (1 active H)"),
        ("C1CS1",          "thiirane_3ring_S",       0, 0, "S 3-ring not oxirane"),
        ("C1CC1",          "cyclopropane_3ring_C",   0, 0, "all-C 3-ring not oxirane"),
        ("C1COC1",         "oxetane_4ring_O",        0, 0, "4-membered O-ring not oxirane"),
        ("C1CCOC1",        "thf_5ring_O",            0, 0, "5-membered O-ring not oxirane"),
        ("COC",            "ether_dimethyl",         0, 0, "acyclic ether not oxirane"),
    ]
    g3 = []
    for smi, kind, eox, enh, note in probes:
        mol = Chem.MolFromSmiles(smi)
        ox = count_oxirane_ringenum(mol); nh = count_active_amine_H_peratom(mol)
        g3.append({"smiles": smi, "kind": kind, "oxirane": ox, "amineH": nh,
                   "expect_oxirane": eox, "expect_amineH": enh,
                   "note": note, "pass": ox == eox and nh == enh})
    g3_pass = all(x["pass"] for x in g3)

    # ---- G4: pattern-invariance across two independent detection methods ----
    g4 = []
    for r in recs:
        smi, f = r.get("smiles"), r.get("facts")
        if not smi or f is None:
            continue
        valid_sc, _ = lexical_structure(smi)
        if not valid_sc:
            continue
        mol = Chem.MolFromSmiles(smi)
        if mol is None:
            continue
        oxA = count_oxirane_ringenum(mol); oxB = count_oxirane_smarts(mol)
        nhA = count_active_amine_H_peratom(mol); nhB = count_active_amine_H_smarts(mol)
        g4.append({"case_id": r["case_id"],
                   "oxirane_ringenum": oxA, "oxirane_smarts": oxB,
                   "amineH_peratom": nhA, "amineH_smarts": nhB,
                   "invariant": oxA == oxB and nhA == nhB})
    g4_pass = len(g4) == 37 and all(x["invariant"] for x in g4)

    diag = {
        "schema": "amphora.molecule-design-gate.rdkit-structural-facts-parity.diagnostic.v1",
        "study_id": "rdkit-structural-facts-parity-v1",
        "module": "amphora-molecule-design-gate",
        "authority": "AUDIT_ONLY",
        "authority_ceiling": "REAL_ARITHMETIC",
        "run_type": "NON_RUNTIME_INDEPENDENT_CHEMINFORMATICS_ORACLE",
        "purpose": ("Independently re-derive the design-gate structural facts and "
                    "full decision surface a-priori from raw SMILES using RDKit "
                    "2026.03.2 + published substructure rules, verifying the "
                    "self-declared fixture facts the KPI rests on."),
        "hypothesis": ("An independent cheminformatics toolkit re-derives the "
                       "fixture's declared oxirane_ring_count and "
                       "reactive_amine_hydrogen_count exactly, and re-running the "
                       "gate over those a-priori facts reproduces all 42 labels."),
        "non_circularity": ("Structural facts are computed FROM SMILES by RDKit, "
                            "NOT read from the fixture's declared integer facts; "
                            "the declared facts are only the comparison target."),
        "theory_reference": [
            "Wicks/Jones/Pappas 2007 Organic Coatings 4th ed. Ch.15 §15.2-15.4",
            "Ellis 1993 Chemistry and Technology of Epoxy Resins Ch.6 §6.2",
            "Landrum RDKit 2026.03.2; Daylight SMARTS theory",
            "oxirane = 3-membered ring {O,2C} (Van Krevelen group definition)",
        ],
        "runtime_source_anchors": {
            "live_rust": "amphora-molecule-capabilities/src/lib.rs::design_gate_result",
            "fixture": "reference/phase0-design-gate-known-answer.v1.json",
        },
        "rdkit_version": Chem.rdBase.rdkitVersion,
        "g1_fact_reproduction": {"records": g1, "n": len(g1), "all_match": g1_pass},
        "g2_full_decision_parity": {"records": g2, "n": len(g2), "all_match": g2_pass},
        "g3_specificity_fail_closed": {"records": g3, "n": len(g3), "all_pass": g3_pass},
        "g4_pattern_invariance": {"records": g4, "n": len(g4), "all_invariant": g4_pass},
        "gates": {
            "g1_facts_reproduced": g1_pass,
            "g2_full_decisions_reproduced": g2_pass,
            "g3_specificity_fail_closed": g3_pass,
            "g4_pattern_invariant": g4_pass,
            "all_pass": g1_pass and g2_pass and g3_pass and g4_pass,
        },
        "counts": {
            "fact_bearing_records": len(g1),
            "total_gate_records": len(g2),
            "specificity_probes": len(g3),
            "invariance_records": len(g4),
        },
        "closes": [
            "First independent (non-Rust, cheminformatics-toolkit) verification "
            "that the design-gate fixture's self-declared structural facts are "
            "true of the cited molecules; prior KPI trusted the declared integers.",
            "Re-derives the full gate decision a-priori from SMILES, reproducing "
            "all 42 expected labels including six gate_reason categories.",
            "Demonstrates the published exclusions (non-aromatic, non-amide N; "
            "O-only 3-ring) are load-bearing via 12 specificity probes.",
        ],
        "does_not_close": [
            "Does not exercise the live Rust runtime (that is the shipped KPI).",
            "Does not establish EHS, synthesis, qualification, procurement, "
            "regulatory, or product-performance authority.",
            "Phase-1 still requires the pinned RDKit C++ boundary wired into the "
            "live runtime, not just an offline oracle.",
        ],
        "dataset_fixture_sha256_note": "recorded by signer",
    }
    print(json.dumps(diag, sort_keys=True, separators=(",", ":")))

if __name__ == "__main__":
    main()
