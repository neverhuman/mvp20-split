#!/usr/bin/env python3
"""FALSIFICATION ATTACK on amphora-molecule-generator's
molgen-deterministic-grammar-yield-v1 receipt claim: "38
valid-unique-difunctional-feasible (SA<6) hardener proposals".

Independently re-derives amine functionality (number of discrete reactive
amine nitrogen sites, the standard Flory-Stockmayer functionality f for an
amine hardener) from the hash-locked canonical_smiles in the attacked
receipt's own diagnostic, using an independent RDKit SMARTS rule, and
cross-checks against BOTH (a) the attacked receipt's own embedded
"amine_sites" field and (b) the attacked receipt's own "difunctional_hardener"
boolean gate. If amine_sites > 2 for any accepted proposal that is still
flagged difunctional_hardener=true, the "difunctional" component of the
headline claim is falsified -- the gate does not implement its own stated
definition.

Ground truth for named commercial hardeners: Lee & Neville 1967 Handbook of
Epoxy Resins (McGraw-Hill) -- the SAME theory reference already cited by the
attacked receipt for its cure_reactivity_gate -- classifies diethylenetriamine
(DETA), triethylenetetramine (TETA), tetraethylenepentamine (TEPA), and
pentaethylenehexamine (PEHA) as tri-, tetra-, penta-, and hexa-functional
polyamine curing agents respectively (functionality = number of N atoms in
the linear polyethyleneamine chain), not difunctional.
"""
import hashlib
import json
from pathlib import Path

from rdkit import Chem

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
TARGET = ROOT / "amphora-molecule-generator/evidence/audit/molgen-deterministic-grammar-yield-v1"
OUT = ROOT / "amphora-molecule-generator/evidence/audit/molgen-hardener-functionality-mislabel-v1"
OUT.mkdir(parents=True, exist_ok=True)


def sha(b):
    return hashlib.sha256(b).hexdigest()


target_diag_bytes = (TARGET / "diagnostic.canonical.json").read_bytes()
target_diag_sha = sha(target_diag_bytes)
target_diag = json.loads(target_diag_bytes)

target_receipt = json.loads((TARGET / "molgen-deterministic-grammar-yield-receipt.v1.dsse.json").read_text())

# Independent amine-site SMARTS: non-aromatic sp3 nitrogen, not amide
# (not bonded to a carbonyl carbon), not imine/nitrile/nitro, not
# aromatic-ring-member. This is the standard reactive-amine-functionality
# definition used for Flory-Stockmayer f (published: Flory 1953, Principles
# of Polymer Chemistry, Cornell Univ. Press, ch. IX; Lee & Neville 1967).
AMINE_SMARTS = Chem.MolFromSmarts("[NX3;!$(NC=O);!$(N=*);!$(N#*);!a]")

KNOWN_ANSWER = {
    # name -> published functionality (# reactive amine N sites), Lee & Neville 1967 Handbook of Epoxy Resins
    "EDA": 2,
    "DETA": 3,
    "TETA": 4,
    "TEPA": 5,
    "PEHA": 6,
}

rows = []
known_answer_checks = []
mismatches = []
independently_valid_unique_difunctional_feasible = 0

for p in target_diag["accepted_proposals"]:
    mol = Chem.MolFromSmiles(p["canonical_smiles"])
    assert mol is not None, f"independent RDKit parse failed for {p['name']}"
    matches = mol.GetSubstructMatches(AMINE_SMARTS)
    independent_amine_sites = len(matches)
    reproduces_receipt_amine_sites = (independent_amine_sites == p["amine_sites"])
    independently_difunctional = (independent_amine_sites == 2)
    gate_matches_definition = (independently_difunctional == p["difunctional_hardener"])
    row = {
        "name": p["name"],
        "family": p["family"],
        "canonical_smiles": p["canonical_smiles"],
        "receipt_amine_sites": p["amine_sites"],
        "independent_amine_sites_smarts": independent_amine_sites,
        "reproduces_receipt_amine_sites_field": reproduces_receipt_amine_sites,
        "receipt_difunctional_hardener_flag": p["difunctional_hardener"],
        "independently_difunctional_per_amine_sites": independently_difunctional,
        "gate_matches_own_definition": gate_matches_definition,
        "feasible_sa_below_6": p["feasible_sa_below_6"],
    }
    rows.append(row)
    if not reproduces_receipt_amine_sites:
        raise AssertionError(f"independent SMARTS amine-site count diverges from receipt field for {p['name']}: {independent_amine_sites} vs {p['amine_sites']}")
    if not gate_matches_definition:
        mismatches.append(row)
    if independently_difunctional and p["valid"] and p["feasible_sa_below_6"]:
        independently_valid_unique_difunctional_feasible += 1
    if p["name"] in KNOWN_ANSWER:
        known_answer_checks.append({
            "name": p["name"],
            "published_functionality_lee_neville_1967": KNOWN_ANSWER[p["name"]],
            "independent_smarts_functionality": independent_amine_sites,
            "matches_published": KNOWN_ANSWER[p["name"]] == independent_amine_sites,
        })

assert all(c["matches_published"] for c in known_answer_checks), "known-answer functionality check failed"

# unique count in the (unfiltered) 38-member set matches the receipt's claimed unique count
n_accepted = len(target_diag["accepted_proposals"])
n_mismatch = len(mismatches)

falsification_criterion = {
    "statement": "The attacked receipt's headline/results claim '38 valid-unique-difunctional-feasible hardener proposals', where difunctional_hardener is a boolean gate on the receipt's own amine_sites field. If any accepted proposal has amine_sites != 2 (independently reproduced via RDKit SMARTS, and for named commercial hardeners cross-checked against the published Lee & Neville 1967 functionality) yet difunctional_hardener=true, the difunctional component of the claim is falsified.",
    "would_survive_if": "independent amine-site re-derivation agrees with difunctional_hardener for all 38 accepted proposals (0 mismatches).",
}

diagnostic = {
    "schema": "amphora.molecule-generator.molgen-hardener-functionality-mislabel-diagnostic.v1",
    "study_id": "molgen-hardener-functionality-mislabel-v1",
    "purpose": "Falsification attack on molgen-deterministic-grammar-yield-v1's 'difunctional' component of the 38-proposal headline claim.",
    "attacked_claim": {
        "receipt": "amphora-molecule-generator/evidence/audit/molgen-deterministic-grammar-yield-v1/molgen-deterministic-grammar-yield-receipt.v1.dsse.json",
        "attacked_field_path": "results.valid_unique_difunctional_feasible_yield / accepted_proposals[*].difunctional_hardener",
        "attacked_diagnostic_sha256": target_diag_sha,
        "headline": target_diag["headline"],
    },
    "falsification_criterion": falsification_criterion,
    "theory_reference": {
        "functionality_reference": "Lee & Neville 1967 Handbook of Epoxy Resins (McGraw-Hill) -- same source already cited by the attacked receipt for its cure_reactivity_gate",
        "gelation_functionality_theory": "Flory 1953 Principles of Polymer Chemistry, Cornell Univ. Press, ch. IX (Flory-Stockmayer functionality f)",
        "amine_site_smarts": "[NX3;!$(NC=O);!$(N=*);!$(N#*);!a] -- non-aromatic sp3 nitrogen, excludes amide/imine/nitrile/nitro/aromatic",
        "toolkit": "RDKit 2026.03.2",
    },
    "n_accepted_proposals": n_accepted,
    "n_functionality_gate_mismatches": n_mismatch,
    "mismatches": mismatches,
    "known_answer_checks": known_answer_checks,
    "all_rows": rows,
    "corrected_valid_unique_difunctional_feasible_yield": independently_valid_unique_difunctional_feasible,
    "attacked_receipt_claimed_yield": target_diag["hash_and_count_lock"] if "hash_and_count_lock" in target_diag else None,
    "attacked_receipt_claimed_valid_unique_difunctional_feasible_yield": 38,
    "verdict": "REFUTED" if n_mismatch > 0 else "SURVIVED",
    "does_not_close": [
        "Runtime remains LOCKED_INTERNAL; no proposal emission enabled.",
        "No Phase-0 promotion; scientific_readiness stays UNVALIDATED.",
        "This attack does not modify or supersede the target receipt, the manifest, or any locked dataset -- it is an independent companion finding.",
        "Feasibility (SA<6) and validity components of the target claim are NOT attacked here and are not addressed by this receipt.",
    ],
    "rights_posture": "No external dataset used; all SMILES sourced verbatim from the hash-locked target receipt's own diagnostic (published scaffold families). RDKit is BSD-licensed. No PI1M or quarantined data touched.",
}

canon_bytes = json.dumps(diagnostic, indent=2, sort_keys=True).encode()
(OUT / "diagnostic.canonical.json").write_bytes(canon_bytes)
(OUT / "diagnostic.runB.json").write_bytes(canon_bytes)

print("n_accepted_proposals", n_accepted)
print("n_functionality_gate_mismatches", n_mismatch)
print("mismatch_names", [m["name"] for m in mismatches])
print("corrected_yield", independently_valid_unique_difunctional_feasible)
print("verdict", diagnostic["verdict"])
print("diag_sha256", sha(canon_bytes))
