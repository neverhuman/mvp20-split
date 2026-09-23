#!/usr/bin/env python3
"""amphora-candidate-contract  schema-runtime-differential-mutation-v1  (AUDIT_ONLY)

Deterministically materialize a LARGE, systematic typed-mutation corpus as raw
bytes files (one per case) plus an independent `_manifest.json` declaring, for
every case, its LAYER and a LAYER-LEVEL PREDICTION about the *relationship*
between the two oracles' verdicts (never the verdict itself -- the two
independent oracles decide; the study measures whether their relationship
matches the prediction).

Scales the prior 24-case hand-authored parity study (schema-runtime-parity-v1)
to a grammar-based mutation space with:
  * combinatorial structural breakage over all 3 candidate types
    (candidate_id / candidate_type / payload-binding x a full JSON type lattice),
  * exhaustive chemistry-v2 top-level key gating (10 keys x optin on/off),
  * BOUNDARY LOCALIZATION of the runtime resource caps
    (depth ~64, collection-width ~100000, size ~8 MiB) -- straddling each cap so
    parity-up-to-cap and runtime-reject-superset-past-cap are both witnessed,
  * a DISCOVERY group probing candidate-type payload EXCLUSIVITY and NESTED
    chemistry-key bans that the declarative schema enforces but the runtime does
    not (schema-stricter direction).

Directly advances the schema-runtime-parity-v1 "does_not_close" item:
"Schema/runtime parity over an exhaustive or fuzz-generated mutation space."

Theory anchors:
  IETF RFC 8259 (2017) JSON grammar; JSON Schema draft 2020-12 (2020-12-08)
  core+validation (incl. allOf/if-then/not, `false` subschemas); IETF RFC 8785
  (2020) JCS; IEEE 754-2019 non-finite; CWE-400/CWE-121 resource caps;
  NIST FIPS 180-4 SHA-256.

Fully deterministic (no wall-clock, no unseeded RNG). AUDIT_ONLY.
"""
import hashlib, json, sys
from pathlib import Path

OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)

def sha(b): return hashlib.sha256(b).hexdigest()
def enc(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()

# ---- base valid envelopes (expected ACCEPT by BOTH oracles) ----------------
BASES = {
    "molecule":         {"candidate_id": "c1", "candidate_type": "molecule",
                          "molecule": {"smiles": "C"}},
    "formulation":      {"candidate_id": "c1", "candidate_type": "formulation",
                          "formulation": {"batch_mass_g": 100.0}},
    "evidence_package": {"candidate_id": "c1", "candidate_type": "evidence_package",
                          "evidence_refs": {"package_id": "p1"}},
}
PAYLOAD_KEY = {"molecule": "molecule", "formulation": "formulation",
               "evidence_package": "evidence_refs"}

# JSON type lattice used for wrong-typing scalar/structural slots.
WRONG_SCALARS = {
    "null": None, "true": True, "false": False,
    "int0": 0, "int42": 42, "intneg": -7, "float": 3.14,
    "emptystr": "", "arr": [1, 2], "obj": {"k": "v"},
}
CHEM_KEYS = ["inchi", "inchi_key", "inchikey", "mol", "mol_block",
             "mol_v2000", "mol_v3000", "sdf", "sdf_records", "recipe_csv"]

cases = []  # (name, group, layer, prediction, param, raw_bytes)

def add(name, group, layer, prediction, raw, param=None):
    cases.append((name, group, layer, prediction, param, raw))

# ---------------------------------------------------------------------------
# POSITIVES  (STRUCT_PARITY, both ACCEPT) : 3 synthetic bases + 3 on-disk
# ---------------------------------------------------------------------------
for t, obj in BASES.items():
    add(f"POS_base_{t}", "POSITIVE", "STRUCTURAL", "PARITY", enc(obj))
# formulation carrying a molecule WITHOUT a structure field is schema-legal
# (the `not` fires only on smiles/canonical_smiles/canonical_structure_hash)
form_with_bare_mol = {"candidate_id": "c1", "candidate_type": "formulation",
                      "formulation": {"batch_mass_g": 100.0},
                      "molecule": {"name": "screening system"}}
add("POS_formulation_bare_molecule", "POSITIVE", "STRUCTURAL", "PARITY",
    enc(form_with_bare_mol))
# a benign extra top-level key (additionalProperties:true) stays ACCEPT for both
add("POS_molecule_extra_benign_key", "POSITIVE", "STRUCTURAL", "PARITY",
    enc({**BASES["molecule"], "notes": "benign"}))

# ---------------------------------------------------------------------------
# STRUCTURAL breakage (STRUCT_PARITY, expect both REJECT)
# ---------------------------------------------------------------------------
for t, base in BASES.items():
    pk = PAYLOAD_KEY[t]
    # candidate_id: drop
    o = dict(base); del o["candidate_id"]
    add(f"S_{t}_id_drop", "STRUCT_BREAK", "STRUCTURAL", "PARITY", enc(o))
    # candidate_id: wrong type / empty
    for wn, wv in WRONG_SCALARS.items():
        o = dict(base); o["candidate_id"] = wv
        add(f"S_{t}_id_{wn}", "STRUCT_BREAK", "STRUCTURAL", "PARITY", enc(o))
    # candidate_type: drop
    o = dict(base); del o["candidate_type"]
    add(f"S_{t}_type_drop", "STRUCT_BREAK", "STRUCTURAL", "PARITY", enc(o))
    # candidate_type: wrong non-string types
    for wn in ["null", "true", "int42", "arr", "obj"]:
        o = dict(base); o["candidate_type"] = WRONG_SCALARS[wn]
        add(f"S_{t}_type_{wn}", "STRUCT_BREAK", "STRUCTURAL", "PARITY", enc(o))
    # candidate_type: unknown string values (index-tagged for collision-free names)
    for ui, uv in enumerate(["widget", "Molecule", "MOLECULE", "molecule_trail_ws",
                             "molecule_lead_ws", "mol", "formulation2", "evidence"]):
        real = {"molecule_trail_ws": "molecule ", "molecule_lead_ws": " molecule"}.get(uv, uv)
        o = dict(base); o["candidate_type"] = real
        add(f"S_{t}_type_val_{ui:02d}_{uv}", "STRUCT_BREAK", "STRUCTURAL", "PARITY", enc(o))
    # payload key: drop
    o = dict(base); del o[pk]
    add(f"S_{t}_payload_drop", "STRUCT_BREAK", "STRUCTURAL", "PARITY", enc(o))
    # payload key: wrong (non-object) type
    for wn in ["null", "true", "int42", "float", "emptystr", "arr"]:
        o = dict(base); o[pk] = WRONG_SCALARS[wn]
        add(f"S_{t}_payload_{wn}", "STRUCT_BREAK", "STRUCTURAL", "PARITY", enc(o))

# top-level non-object scalars/arrays (both REJECT)
for name, raw in [
    ("array", b"[1,2,3]"), ("string", b"\"hello\""), ("int", b"42"),
    ("float", b"3.14"), ("true", b"true"), ("false", b"false"), ("null", b"null"),
]:
    add(f"S_toplevel_{name}", "STRUCT_BREAK", "STRUCTURAL", "PARITY", raw)

# ---------------------------------------------------------------------------
# CHEMISTRY-v2 TOP-LEVEL gate (STRUCT_PARITY, expect both REJECT)
#   schema: property `false` -> invalid ; runtime: PayloadMismatch (no optin) or
#   ChemistryNormalizationUnavailable (with optin). Verdict parity either way.
# ---------------------------------------------------------------------------
for k in CHEM_KEYS:
    o = {**BASES["molecule"], k: "x"}
    add(f"CH_top_{k}_no_optin", "CHEM_TOP", "STRUCTURAL", "PARITY", enc(o))
    o2 = {**BASES["molecule"], k: "x",
          "schema_version": "amphora.candidate-envelope.v2"}
    add(f"CH_top_{k}_optin", "CHEM_TOP", "STRUCTURAL", "PARITY", enc(o2))

# ---------------------------------------------------------------------------
# DISCOVERY: SCHEMA-STRICTER direction  (expect schema REJECT / runtime ACCEPT)
#   Runtime only checks the required payload is an object + top-level chem gate;
#   the declarative schema additionally enforces candidate-type payload
#   EXCLUSIVITY (allOf/not) and NESTED chemistry-key bans.
# ---------------------------------------------------------------------------
# molecule candidate ALSO carrying a formulation payload
add("X_molecule_plus_formulation", "SCHEMA_SUPERSET", "STRUCTURAL",
    "SCHEMA_SUPERSET", enc({**BASES["molecule"], "formulation": {"batch_mass_g": 1.0}}))
# evidence candidate ALSO carrying molecule / formulation
add("X_evidence_plus_molecule", "SCHEMA_SUPERSET", "STRUCTURAL",
    "SCHEMA_SUPERSET", enc({**BASES["evidence_package"], "molecule": {"smiles": "C"}}))
add("X_evidence_plus_formulation", "SCHEMA_SUPERSET", "STRUCTURAL",
    "SCHEMA_SUPERSET", enc({**BASES["evidence_package"], "formulation": {"batch_mass_g": 1.0}}))
# formulation candidate carrying a molecule WITH a structure field (schema `not`)
for sf in ["smiles", "canonical_smiles"]:
    add(f"X_formulation_plus_molecule_{sf}", "SCHEMA_SUPERSET", "STRUCTURAL",
        "SCHEMA_SUPERSET",
        enc({**BASES["formulation"], "molecule": {sf: "C"}}))
add("X_formulation_plus_molecule_structhash", "SCHEMA_SUPERSET", "STRUCTURAL",
    "SCHEMA_SUPERSET",
    enc({**BASES["formulation"],
         "molecule": {"canonical_structure_hash": "a" * 64}}))
# NESTED chemistry keys inside molecule payload (schema molecule.<key>:false;
# runtime top-level gate does NOT inspect nested payload keys)
for k in ["inchi", "inchi_key", "inchikey", "mol", "mol_block",
          "mol_v2000", "mol_v3000", "sdf", "sdf_records"]:
    add(f"X_molecule_nested_{k}", "SCHEMA_SUPERSET", "STRUCTURAL",
        "SCHEMA_SUPERSET",
        enc({"candidate_id": "c1", "candidate_type": "molecule",
             "molecule": {"smiles": "C", k: "x"}}))

# ---------------------------------------------------------------------------
# LEXICAL layer  (RUNTIME_SUPERSET: runtime REJECT / schema ACCEPT)
#   CPython json is permissive (NaN/Infinity, last-key-wins on dup); the strict
#   Rust seed rejects. Hand-crafted raw bytes (dups/non-finite can't round-trip
#   through a Python dict).
# ---------------------------------------------------------------------------
add("L_nonfinite_nan", "LEXICAL", "LEXICAL", "RUNTIME_SUPERSET",
    b'{"candidate_id":"x","candidate_type":"molecule","molecule":{"smiles":"C"},"extra":NaN}')
add("L_nonfinite_infinity", "LEXICAL", "LEXICAL", "RUNTIME_SUPERSET",
    b'{"candidate_id":"x","candidate_type":"molecule","molecule":{"smiles":"C"},"extra":Infinity}')
add("L_nonfinite_neg_infinity", "LEXICAL", "LEXICAL", "RUNTIME_SUPERSET",
    b'{"candidate_id":"x","candidate_type":"molecule","molecule":{"smiles":"C"},"extra":-Infinity}')
add("L_nonfinite_nested", "LEXICAL", "LEXICAL", "RUNTIME_SUPERSET",
    b'{"candidate_id":"x","candidate_type":"molecule","molecule":{"smiles":"C","w":NaN}}')
add("L_dup_candidate_id", "LEXICAL", "LEXICAL", "RUNTIME_SUPERSET",
    b'{"candidate_id":"x","candidate_id":"y","candidate_type":"molecule","molecule":{"smiles":"C"}}')
add("L_dup_candidate_type", "LEXICAL", "LEXICAL", "RUNTIME_SUPERSET",
    b'{"candidate_id":"x","candidate_type":"molecule","candidate_type":"molecule","molecule":{"smiles":"C"}}')
add("L_dup_extra_key", "LEXICAL", "LEXICAL", "RUNTIME_SUPERSET",
    b'{"candidate_id":"x","candidate_type":"molecule","molecule":{"smiles":"C"},"z":1,"z":2}')
add("L_dup_escaped_key", "LEXICAL", "LEXICAL", "RUNTIME_SUPERSET",
    b'{"candidate_id":"x","candidate_type":"molecule","molecule":{"smiles":"C"},"a":1,"\\u0061":2}')
add("L_dup_nested_key", "LEXICAL", "LEXICAL", "RUNTIME_SUPERSET",
    b'{"candidate_id":"x","candidate_type":"molecule","molecule":{"smiles":"C","q":1,"q":2}}')

# ---------------------------------------------------------------------------
# RESOURCE boundary localization  (RES_BOUNDARY: schema ACCEPT always; runtime
#   ACCEPT below cap, REJECT past cap). Straddle each cap; report transition.
# ---------------------------------------------------------------------------
def deep_field(k):
    """k nested single-element arrays around scalar 0, as an extra field."""
    v = 0
    for _ in range(k):
        v = [v]
    return v

for k in [1, 32, 60, 61, 62, 63, 64, 65, 66, 67, 68, 100]:
    o = {**BASES["molecule"], "deep": deep_field(k)}
    add(f"R_depth_k{k:03d}", "RES_DEPTH", "RESOURCE", "RES_BOUNDARY",
        enc(o), param=k)

for w in [1, 100, 99990, 99995, 99996, 99997, 99998, 99999, 100000, 100001, 100002]:
    o = {**BASES["molecule"], "wide": list(range(w))}
    add(f"R_width_w{w:06d}", "RES_WIDTH", "RESOURCE", "RES_BOUNDARY",
        enc(o), param=w)

CAP = 8 * 1024 * 1024
def sized(total):
    """Build a molecule envelope whose compact-JSON byte length == total."""
    base = {**BASES["molecule"], "pad": ""}
    # length is affine in len(pad); fit exactly.
    n = total - len(enc(base))
    if n < 0:
        n = 0
    for _ in range(6):
        b = enc({**BASES["molecule"], "pad": "A" * n})
        n += total - len(b)
        if len(b) == total:
            break
    return enc({**BASES["molecule"], "pad": "A" * n})

for label, total in [("at_cap", CAP), ("under_1k", CAP - 1024),
                     ("over_1", CAP + 1), ("over_1k", CAP + 1024)]:
    b = sized(total)
    add(f"R_size_{label}", "RES_SIZE", "RESOURCE", "RES_BOUNDARY",
        b, param=len(b))

# ---------------------------------------------------------------------------
# PARSE layer  (PARSE_BOTH_FAIL: schema N/A_PARSE at decode/parse, runtime REJECT)
# ---------------------------------------------------------------------------
add("P_trailing_comma", "PARSE", "PARSE", "PARSE_BOTH_FAIL",
    b'{"candidate_id":"x","candidate_type":"molecule","molecule":{"smiles":"C"},}')
add("P_non_utf8", "PARSE", "PARSE", "PARSE_BOTH_FAIL",
    b'{"candidate_id":"\xff\xfe","candidate_type":"molecule","molecule":{"smiles":"C"}}')
add("P_leading_zero", "PARSE", "PARSE", "PARSE_BOTH_FAIL",
    b'{"candidate_id":"x","candidate_type":"molecule","molecule":{"smiles":"C"},"n":01}')
add("P_unquoted_key", "PARSE", "PARSE", "PARSE_BOTH_FAIL",
    b'{candidate_id:"x","candidate_type":"molecule","molecule":{"smiles":"C"}}')
add("P_single_quotes", "PARSE", "PARSE", "PARSE_BOTH_FAIL",
    b"{'candidate_id':'x','candidate_type':'molecule','molecule':{'smiles':'C'}}")
add("P_bare_word", "PARSE", "PARSE", "PARSE_BOTH_FAIL", b"candidate")
add("P_empty_input", "PARSE", "PARSE", "PARSE_BOTH_FAIL", b"")
add("P_unterminated_object", "PARSE", "PARSE", "PARSE_BOTH_FAIL",
    b'{"candidate_id":"x","candidate_type":"molecule"')

# ---------------------------------------------------------------------------
# materialize + manifest (sorted, deterministic)
# ---------------------------------------------------------------------------
seen = set()
manifest = []
for name, group, layer, prediction, param, raw in sorted(cases, key=lambda c: c[0]):
    assert name not in seen, f"duplicate case name {name}"
    seen.add(name)
    (OUT / name).write_bytes(raw)
    row = {"name": name, "group": group, "layer": layer,
           "prediction": prediction, "n_bytes": len(raw), "sha256": sha(raw)}
    if param is not None:
        row["param"] = param
    manifest.append(row)

(OUT / "_manifest.json").write_bytes(
    json.dumps(manifest, indent=2, sort_keys=True).encode() + b"\n")

print("n_cases", len(manifest))
from collections import Counter
for g, c in sorted(Counter(m["group"] for m in manifest).items()):
    print("group", g, c)
print("manifest_sha256", sha((OUT / "_manifest.json").read_bytes()))
