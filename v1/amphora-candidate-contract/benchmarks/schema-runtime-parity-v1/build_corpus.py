#!/usr/bin/env python3
"""amphora-candidate-contract  schema-runtime-parity-v1  (AUDIT_ONLY)

Deterministically materialize the typed candidate corpus as raw bytes files,
one per case, so BOTH oracles consume byte-identical inputs:

  Oracle A (declarative):  canonical JSON Schema draft 2020-12
       (schemas/candidate-envelope.schema.json) enforced by a conformant
       JSON-Schema validator over CPython's permissive RFC-8259-superset
       parser (jsonschema 4.26.0 + stdlib json).
  Oracle B (runtime):      Rust amphora-core::contract CandidateEnvelope::from_bytes
       (strict StrictSeed parser + structural checks), run by rust_harness.

Theory:
  - IETF RFC 8259 (2017) JSON grammar (Infinity/NaN disallowed; strict tokens).
  - JSON Schema draft 2020-12 (2020-12-08) core+validation vocabularies.
  - IETF RFC 8785 (2020) JCS canonicalization (contract_hash_v1 foundation).
  - CWE-400 / CWE-121 resource-exhaustion (depth / width / size caps).
  - IEEE 754-2019 non-finite semantics.

No promotion, no manifest edit, no scientific_readiness flip. AUDIT_ONLY.
"""
import base64, hashlib, json, os, sys
from pathlib import Path

ROOT = Path(sys.argv[1])                       # mvp20-split root
MOD = ROOT / "amphora-candidate-contract"
FIX = MOD / "fixtures"
OUT = Path(sys.argv[2])                         # corpus bytes dir (created)
OUT.mkdir(parents=True, exist_ok=True)

def raw(name, b):
    """Register a case as literal bytes."""
    return {"name": name, "bytes": b}

def enc(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()

# --- positives sourced from the module's own on-disk fixtures ---------------
p_mol = (FIX / "molecule_candidate.json").read_bytes()
p_form = (FIX / "formulation_candidate.json").read_bytes()
p_evid = (FIX / "evidence_package_candidate.json").read_bytes()

good_mol = {"candidate_id": "m1", "candidate_type": "molecule",
            "molecule": {"smiles": "ClC(Cl)(Cl)Cl", "name": "carbon tetrachloride"}}

cases = []
# ------- Group S : STRUCTURAL layer (schema is expressive; parity expected) --
cases += [
    ("P1_positive_molecule", "S", "ACCEPT", p_mol),
    ("P2_positive_formulation", "S", "ACCEPT", p_form),
    ("P3_positive_evidence_package", "S", "ACCEPT", p_evid),
    ("S01_top_level_array", "S", "REJECT", b"[1,2,3]"),
    ("S02_top_level_string", "S", "REJECT", b"\"hello\""),
    ("S03_candidate_id_missing", "S", "REJECT",
        enc({"candidate_type": "molecule", "molecule": {"smiles": "C"}})),
    ("S04_candidate_id_empty", "S", "REJECT",
        enc({"candidate_id": "", "candidate_type": "molecule", "molecule": {"smiles": "C"}})),
    ("S05_candidate_id_integer", "S", "REJECT",
        enc({"candidate_id": 5, "candidate_type": "molecule", "molecule": {"smiles": "C"}})),
    ("S06_candidate_type_missing", "S", "REJECT",
        enc({"candidate_id": "x", "molecule": {"smiles": "C"}})),
    ("S07_candidate_type_unknown", "S", "REJECT",
        enc({"candidate_id": "x", "candidate_type": "widget", "molecule": {"smiles": "C"}})),
    ("S08_molecule_payload_missing", "S", "REJECT",
        enc({"candidate_id": "x", "candidate_type": "molecule"})),
    ("S09_formulation_payload_missing", "S", "REJECT",
        enc({"candidate_id": "x", "candidate_type": "formulation"})),
    ("S10_evidence_payload_missing", "S", "REJECT",
        enc({"candidate_id": "x", "candidate_type": "evidence_package"})),
    ("S11_molecule_payload_not_object", "S", "REJECT",
        enc({"candidate_id": "x", "candidate_type": "molecule", "molecule": "C"})),
    ("S12_chem_v2_field_no_optin", "S", "REJECT",
        enc({"candidate_id": "x", "candidate_type": "molecule",
             "molecule": {"smiles": "C"}, "inchi": "InChI=1S/CH4/h1H4"})),
    ("S13_chem_v2_field_with_optin", "S", "REJECT",
        enc({"candidate_id": "x", "candidate_type": "molecule",
             "molecule": {"smiles": "C"}, "inchi": "InChI=1S/CH4/h1H4",
             "schema_version": "amphora.candidate-envelope.v2"})),
]

# ------- Group N : LEXICAL / RESOURCE layer -------------------------------
# N-superset: runtime REJECT but schema-over-permissive-parser ACCEPT
cases += [
    ("N01_nonfinite_nan", "N_SUPERSET", "REJECT",
        b'{"candidate_id":"x","candidate_type":"molecule","molecule":{"smiles":"C"},"extra":NaN}'),
    ("N02_nonfinite_infinity", "N_SUPERSET", "REJECT",
        b'{"candidate_id":"x","candidate_type":"molecule","molecule":{"smiles":"C"},"extra":Infinity}'),
    ("N03_duplicate_keys", "N_SUPERSET", "REJECT",
        b'{"candidate_id":"x","candidate_id":"x","candidate_type":"molecule","molecule":{"smiles":"C"}}'),
]
# N04 oversized ( > 8 MiB )
big = "A" * (8 * 1024 * 1024 + 64)
cases.append(("N04_oversize_gt_8mib", "N_SUPERSET", "REJECT",
              enc({"candidate_id": "x", "candidate_type": "molecule",
                   "molecule": {"smiles": "C"}, "pad": big})))
# N05 over-deep nesting ( depth > 64 ) inside context (schema: additionalProperties true)
deep = {"smiles": "C"}
nest = deep
for _ in range(100):
    nest = {"a": nest}
cases.append(("N05_overdeep_nesting_100", "N_SUPERSET", "REJECT",
              enc({"candidate_id": "x", "candidate_type": "molecule",
                   "molecule": {"smiles": "C"}, "context": nest})))
# N06 over-wide collection ( > 100_000 entries )
wide = list(range(100_001))
cases.append(("N06_overwide_collection_100001", "N_SUPERSET", "REJECT",
              enc({"candidate_id": "x", "candidate_type": "molecule",
                   "molecule": {"smiles": "C"}, "wide": wide})))

# N-parse-parity: both reject at the parse layer (no schema value produced)
cases += [
    ("N07_trailing_comma", "N_PARSE", "REJECT",
        b'{"candidate_id":"x","candidate_type":"molecule","molecule":{"smiles":"C"},}'),
    ("N08_non_utf8", "N_PARSE", "REJECT",
        b'{"candidate_id":"\xff\xfe","candidate_type":"molecule","molecule":{"smiles":"C"}}'),
]

# materialize + manifest
manifest = []
for name, group, runtime_expect, b in cases:
    (OUT / name).write_bytes(b)
    manifest.append({
        "name": name, "group": group,
        "runtime_expected": runtime_expect,
        "sha256": hashlib.sha256(b).hexdigest(),
        "n_bytes": len(b),
    })
manifest.sort(key=lambda r: r["name"])
(OUT / "_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True))
print(f"wrote {len(manifest)} corpus cases to {OUT}")
