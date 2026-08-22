#!/usr/bin/env python3
"""
amphora-molecule-design-gate :: fact-snapshot-authority-v1 :: probe generator

Deterministically builds probes.v1.json for the live-Rust differential
harness. Probe classes:

  FIXTURE          all 42 shipped known-answer records, routed exactly as the
                   shipped Phase-0 KPI harness routes them (facts object
                   present -> synthesized MoleculeFactsV1 snapshot; facts
                   absent -> empty FeatureSnapshot).
  UP_FORGERY       structurally inert single-component molecules with forged
                   positive declared facts.
  DOWN_FORGERY     genuine shipped resins/hardeners with facts forged to zero.
  STRUCTURE_BYPASS lexically-invalid or chemically-unparseable structures WITH
                   a facts snapshot attached (the decision cell the shipped
                   fixture never exercises).
  BYPASS_NOFACTS   the same six candidates with NO snapshot (paired controls).
  BINDING_SWAP     honest facts of molecule A replayed against candidate B
                   (binding fields present in the snapshot, inconsistent with
                   the candidate).
  MAGNITUDE        magnitude-forgery pairs probing count-insensitivity above
                   the >0 threshold.
  SERDE_CONTROL    malformed verbatim snapshots that must fail MoleculeFactsV1
                   deserialization and fall to the fail-closed branch.
  GRID             role x (ox,nh) indicator grid on a fixed inert backbone.

No randomness, no timestamps: output is a pure function of the shipped
fixture bytes.
"""
import json
import sys

FIXTURE_PATH = sys.argv[1]
OUT_PATH = sys.argv[2]

fixture = json.load(open(FIXTURE_PATH))
records = fixture["records"]

BENZENE = "c1ccccc1"


def candidate(case_id, smiles, role):
    molecule = {}
    if smiles is not None:
        molecule["smiles"] = smiles
    if role is not None:
        molecule["role"] = role
    return {
        "candidate_id": case_id,
        "candidate_type": "molecule",
        "molecule": molecule,
    }


def synth(facts, canonical_smiles):
    return {"mode": "synth", "facts": facts, "canonical_smiles": canonical_smiles}


def facts4(ox, nh, formula="C6H6", mw=78.11):
    return {
        "average_molecular_weight_g_mol": mw,
        "formula": formula,
        "oxirane_ring_count": ox,
        "reactive_amine_hydrogen_count": nh,
    }


probes = []


def add(probe_id, klass, cand, snapshot, note):
    probes.append(
        {
            "probe_id": probe_id,
            "class": klass,
            "candidate": cand,
            "snapshot": snapshot,
            "note": note,
        }
    )


# ---- FIXTURE: shipped KPI routing, byte-faithful ----
for r in records:
    smiles = r.get("smiles")
    role = r.get("role")
    facts = r.get("facts")
    snapshot = None
    if isinstance(facts, dict):
        snapshot = synth(facts, smiles if isinstance(smiles, str) else "canonical-placeholder")
    add(
        "fixture::" + r["case_id"],
        "FIXTURE",
        candidate(r["case_id"], smiles if isinstance(smiles, str) else None,
                  role if isinstance(role, str) else None),
        snapshot,
        "shipped known-answer record, KPI-harness routing",
    )

# ---- UP_FORGERY: inert structures, forged positive declared facts ----
up = [
    ("benzene", BENZENE, "resin", facts4(2, 0), "aromatic hydrocarbon, zero oxirane"),
    ("toluene", "Cc1ccccc1", "hardener", facts4(0, 4, "C7H8", 92.14), "aromatic hydrocarbon, zero amine H"),
    ("water", "O", "resin", facts4(1, 0, "H2O", 18.02), "water, zero oxirane"),
    ("cyclohexane", "C1CCCCC1", "hardener", facts4(0, 2, "C6H12", 84.16), "alkane, zero amine H"),
    ("thf", "C1CCOC1", "resin", facts4(1, 0, "C4H8O", 72.11), "5-ring ether declared as oxirane"),
    ("acetamide", "CC(N)=O", "hardener", facts4(0, 2, "C2H5NO", 59.07), "amide N-H declared reactive"),
    ("pyridine", "c1ccncc1", "hardener", facts4(0, 1, "C5H5N", 79.10), "aromatic N declared reactive"),
    ("dgeba-as-hardener", None, "hardener", facts4(0, 2, "C21H24O4", 340.42),
     "true resin re-badged as hardener via forged amine facts"),
]
dgeba = next(r for r in records if r["case_id"] == "resin-dgeba")
for name, smiles, role, facts, note in up:
    if smiles is None:
        smiles = dgeba["smiles"]
    add(f"up-forgery::{name}", "UP_FORGERY", candidate(f"up-{name}", smiles, role),
        synth(facts, smiles), note)

# ---- DOWN_FORGERY: genuine actives with zeroed declared facts ----
valid_resins = [r for r in records if r["subgroup"] == "VALID_RESIN"][:2]
valid_hardeners = [r for r in records if r["subgroup"] == "VALID_HARDENER"][:2]
for r in valid_resins + valid_hardeners:
    zeroed = dict(r["facts"])
    zeroed["oxirane_ring_count"] = 0
    zeroed["reactive_amine_hydrogen_count"] = 0
    add(f"down-forgery::{r['case_id']}", "DOWN_FORGERY",
        candidate(f"down-{r['case_id']}", r["smiles"], r["role"]),
        synth(zeroed, r["smiles"]),
        "genuine shipped active with facts forged to zero")

# ---- STRUCTURE_BYPASS: invalid structures WITH a facts snapshot ----
bypass = [
    ("multi-fragment-salt", "NCCNCCN.Cl.Cl", "hardener", facts4(0, 5, "C4H15Cl2N3", 175.10),
     "multi-fragment amine salt: shipped lexical ladder rejects it as"
     " multi_fragment_structure when facts are absent"),
    ("wildcard", "CC(*)CO", "resin", facts4(1, 0), "wildcard atom (wildcard_or_query_structure)"),
    ("empty", "", "resin", facts4(1, 0), "empty structure string (empty_structure)"),
    ("missing-smiles", None, "resin", facts4(1, 0), "molecule object without smiles (missing_structure)"),
    ("unclosed-ring", "C1CC", "resin", facts4(1, 0),
     "lexically clean but chemically unparseable (unclosed ring bond)"),
    ("pentavalent-carbon", "C(C)(C)(C)(C)C", "resin", facts4(1, 0),
     "lexically clean but valence-impossible (5-valent carbon)"),
]
for name, smiles, role, facts, note in bypass:
    add(f"bypass::{name}", "STRUCTURE_BYPASS",
        candidate(f"bypass-{name}", smiles, role),
        synth(facts, smiles if smiles is not None else "canonical-placeholder"), note)
    add(f"bypass-nofacts::{name}", "BYPASS_NOFACTS",
        candidate(f"bypassnf-{name}", smiles, role), None,
        "same candidate with facts absent: shipped fail-closed pathway")

# ---- BINDING_SWAP: honest facts of A replayed against candidate B ----
donor_h1, donor_h2 = valid_hardeners[0], valid_hardeners[1]
add("swap::dgeba-facts-on-benzene", "BINDING_SWAP",
    candidate("swap-benzene", BENZENE, "resin"),
    synth(dgeba["facts"], dgeba["smiles"]),
    "honest DGEBA MoleculeFactsV1 (binding fields = DGEBA) attached to benzene")
add(f"swap::{donor_h2['case_id']}-facts-on-{donor_h1['case_id']}", "BINDING_SWAP",
    candidate("swap-hardener", donor_h1["smiles"], "hardener"),
    synth(donor_h2["facts"], donor_h2["smiles"]),
    "honest facts of one shipped hardener replayed against another")

# ---- MAGNITUDE: count-insensitivity above the >0 threshold ----
add("magnitude::benzene-ox1", "MAGNITUDE", candidate("mag-b1", BENZENE, "resin"),
    synth(facts4(1, 0), BENZENE), "forged ox=1")
add("magnitude::benzene-ox4294967295", "MAGNITUDE", candidate("mag-b2", BENZENE, "resin"),
    synth(facts4(4294967295, 0), BENZENE), "forged ox=u32::MAX; must equal ox=1 decision")
add("magnitude::dgeba-ox1", "MAGNITUDE", candidate("mag-d1", dgeba["smiles"], "resin"),
    synth(facts4(1, 0, "C21H24O4", 340.42), dgeba["smiles"]),
    "difunctional DGEBA under-declared as monofunctional")
add("magnitude::dgeba-ox2", "MAGNITUDE", candidate("mag-d2", dgeba["smiles"], "resin"),
    synth(facts4(2, 0, "C21H24O4", 340.42), dgeba["smiles"]),
    "honest DGEBA ox=2 (control pair member)")

# ---- SERDE_CONTROL: malformed verbatim snapshots must fail closed ----
VALID_FULL_FACTS = {
    "schema": "amphora.molecule-facts.v1",
    "canonical_isomeric_smiles": BENZENE,
    "structure_identity": "smiles-sha256:0",
    "canonical_structure_sha256": "0" * 64,
    "formula": "C6H6",
    "average_molecular_weight_g_mol": 78.11,
    "oxirane_ring_count": 2,
    "reactive_amine_hydrogen_count": 0,
    "reactive_flags": {
        "has_oxirane": True,
        "has_reactive_amine_hydrogen": False,
        "dual_role": False,
    },
    "ontology_version": "amphora.reactive-ontology.v1",
    "toolkit_provenance": {
        "toolkit": "RDKit C++",
        "required_version": "2026.03.2",
        "detected_version": "2026.03.2",
        "exact_version_match": True,
    },
}


def perturbed(**changes):
    v = json.loads(json.dumps(VALID_FULL_FACTS))
    for key, value in changes.items():
        if value is ...:
            v.pop(key)
        else:
            v[key] = value
    return {"mode": "verbatim", "value": v}


add("serde::facts-absent", "SERDE_CONTROL", candidate("serde-absent", BENZENE, "resin"),
    None, "no snapshot at all: fail-closed fallback branch")
add("serde::negative-ox", "SERDE_CONTROL", candidate("serde-neg", BENZENE, "resin"),
    perturbed(oxirane_ring_count=-1), "u32 field negative: serde must reject")
add("serde::string-ox", "SERDE_CONTROL", candidate("serde-str", BENZENE, "resin"),
    perturbed(oxirane_ring_count="2"), "u32 field as string: serde must reject")
add("serde::float-ox", "SERDE_CONTROL", candidate("serde-float", BENZENE, "resin"),
    perturbed(oxirane_ring_count=2.5), "u32 field as float: serde must reject")
add("serde::unknown-field", "SERDE_CONTROL", candidate("serde-unknown", BENZENE, "resin"),
    perturbed(injected_extra_field=True), "deny_unknown_fields must reject")
add("serde::missing-provenance", "SERDE_CONTROL", candidate("serde-missing", BENZENE, "resin"),
    perturbed(toolkit_provenance=...), "missing required struct field: serde must reject")
add("serde::verbatim-valid-control", "SERDE_CONTROL",
    candidate("serde-valid", BENZENE, "resin"), perturbed(),
    "well-typed verbatim forged snapshot: must be ACCEPTED by serde and SCORE"
    " (positive control that the serde wall is the only wall)")

# ---- GRID: role x indicator grid on benzene ----
for role_tag, role in [("resin", "resin"), ("hardener", "hardener"),
                       ("norole", None), ("solvent", "solvent")]:
    for ox, nh in [(0, 0), (1, 0), (0, 1), (1, 1)]:
        add(f"grid::{role_tag}-ox{ox}-nh{nh}", "GRID",
            candidate(f"grid-{role_tag}-{ox}{nh}", BENZENE, role),
            synth(facts4(ox, nh), BENZENE),
            "decision-surface grid point")

out = {
    "schema": "amphora.molecule-design-gate.fact-snapshot-authority.probes.v1",
    "fixture_path": "reference/phase0-design-gate-known-answer.v1.json",
    "n_probes": len(probes),
    "probes": probes,
}
with open(OUT_PATH, "w") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
print(f"wrote {OUT_PATH} with {len(probes)} probes")
