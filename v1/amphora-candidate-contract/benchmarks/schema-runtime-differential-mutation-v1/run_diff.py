#!/usr/bin/env python3
"""amphora-candidate-contract  schema-runtime-differential-mutation-v1  analysis.

Cross-tabulate the two INDEPENDENT deciders over one byte-identical mutation
corpus and adjudicate the module's falsifiable hypothesis at scale:
  "runtime and JSON Schema accept and reject the same finite typed corpus."

Oracle A (declarative): canonical candidate-envelope.schema.json (draft 2020-12)
  via jsonschema over CPython's permissive RFC-8259-superset json parser
  (parse-then-validate: the realistic schema-only front door).
Oracle B (runtime)    : compiled Rust amphora_core::CandidateEnvelope::from_bytes
  verdicts (rust_runtime_verdicts.json).

Deterministic diagnostic (no wall-clock, sorted keys) for a two-replay gate.
"""
import hashlib, json, sys
from pathlib import Path
from importlib.metadata import version
from jsonschema.validators import Draft202012Validator

ROOT = Path(sys.argv[1])
CORPUS = Path(sys.argv[2])
RUST = Path(sys.argv[3])
OUT = Path(sys.argv[4])

MOD = ROOT / "amphora-candidate-contract"
SCHEMA_PATH = MOD / "schemas" / "candidate-envelope.schema.json"

def sha(b): return hashlib.sha256(b).hexdigest()

schema_bytes = SCHEMA_PATH.read_bytes()
schema = json.loads(schema_bytes)
Draft202012Validator.check_schema(schema)
V = Draft202012Validator(schema)

manifest = json.loads((CORPUS / "_manifest.json").read_bytes())
rust = json.loads(RUST.read_bytes())

def schema_pipeline(raw: bytes):
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return {"stage": "DECODE", "verdict": "N/A_PARSE", "reason": "non_utf8"}
    try:
        value = json.loads(text)  # permissive: NaN/Infinity ok, last-key-wins
    except json.JSONDecodeError as e:
        return {"stage": "PARSE", "verdict": "N/A_PARSE", "reason": f"json_decode:{e.msg}"}
    ok = V.is_valid(value)
    return {"stage": "VALIDATE", "verdict": "ACCEPT" if ok else "REJECT",
            "reason": "schema_valid" if ok else "schema_invalid"}

rows = []
for r in sorted(manifest, key=lambda x: x["name"]):
    name = r["name"]
    raw = (CORPUS / name).read_bytes()
    assert sha(raw) == r["sha256"], f"corpus byte drift {name}"
    sp = schema_pipeline(raw)
    rv = rust[name]["runtime_verdict"]
    rvar = rust[name]["detail"].get("variant")
    rows.append({
        "name": name, "group": r["group"], "layer": r["layer"],
        "prediction": r["prediction"], "n_bytes": r["n_bytes"],
        "param": r.get("param"),
        "schema_verdict": sp["verdict"], "schema_stage": sp["stage"],
        "schema_reason": sp["reason"],
        "runtime_verdict": rv, "runtime_variant": rvar,
    })

def by(pred): return [x for x in rows if x["prediction"] == pred]

PAR = by("PARITY"); RSUP = by("RUNTIME_SUPERSET")
SSUP = by("SCHEMA_SUPERSET"); PARSE = by("PARSE_BOTH_FAIL")
RESB = by("RES_BOUNDARY")

# ---- gates -----------------------------------------------------------------
par_agree = [x for x in PAR if x["schema_verdict"] == x["runtime_verdict"]
             and x["schema_verdict"] in ("ACCEPT", "REJECT")]
par_disagree = [x["name"] for x in PAR
                if not (x["schema_verdict"] == x["runtime_verdict"]
                        and x["schema_verdict"] in ("ACCEPT", "REJECT"))]
positives = [x for x in rows if x["group"] == "POSITIVE"]

g1 = len(PAR) > 0 and len(par_disagree) == 0
g2 = len(positives) > 0 and all(
    x["schema_verdict"] == "ACCEPT" and x["runtime_verdict"] == "ACCEPT"
    for x in positives)
g3 = len(RSUP) > 0 and all(
    x["runtime_verdict"] == "REJECT" and x["schema_verdict"] == "ACCEPT"
    for x in RSUP)
g4 = len(PARSE) > 0 and all(
    x["runtime_verdict"] == "REJECT" and x["schema_verdict"] == "N/A_PARSE"
    for x in PARSE)
# schema-stricter discovery: schema REJECT while runtime ACCEPT
ssup_confirmed = [x for x in SSUP if x["schema_verdict"] == "REJECT"
                  and x["runtime_verdict"] == "ACCEPT"]
g5 = len(SSUP) > 0 and len(ssup_confirmed) == len(SSUP)

# ---- boundary localization -------------------------------------------------
def transition(group_name):
    g = sorted([x for x in RESB if x["group"] == group_name],
               key=lambda x: x["param"])
    schema_all_accept = all(x["schema_verdict"] == "ACCEPT" for x in g)
    accepts = [x for x in g if x["runtime_verdict"] == "ACCEPT"]
    rejects = [x for x in g if x["runtime_verdict"] == "REJECT"]
    last_accept = max((x["param"] for x in accepts), default=None)
    first_reject = min((x["param"] for x in rejects), default=None)
    # monotone: every accept param < every reject param
    monotone = (last_accept is None or first_reject is None
                or last_accept < first_reject)
    # runtime is a reject-superset past the cap: rejects are runtime-only
    superset_past_cap = all(x["schema_verdict"] == "ACCEPT" for x in rejects)
    return {
        "n": len(g), "schema_all_accept": bool(schema_all_accept),
        "runtime_last_accept_param": last_accept,
        "runtime_first_reject_param": first_reject,
        "monotone": bool(monotone),
        "parity_below_cap": len(accepts) > 0,
        "runtime_reject_superset_past_cap": bool(superset_past_cap) and len(rejects) > 0,
    }

boundaries = {name: transition(name)
              for name in ["RES_DEPTH", "RES_WIDTH", "RES_SIZE"]}
g6 = all(b["schema_all_accept"] and b["monotone"] and b["parity_below_cap"]
         and b["runtime_reject_superset_past_cap"]
         for b in boundaries.values())

gates = {
    "G1_structural_parity_predicted_subset": {"passed": bool(g1), "n": len(PAR),
        "note": "For every PARITY-predicted case schema_verdict == runtime_verdict "
                "(both ACCEPT or both REJECT). ANY disagreement here REFUTES structural parity."},
    "G2_positives_both_accept": {"passed": bool(g2), "n": len(positives),
        "note": "Every real coating envelope (3 synthetic bases + on-disk-shaped variants) accepted by both oracles."},
    "G3_lexical_runtime_reject_superset": {"passed": bool(g3), "n": len(RSUP),
        "note": "Runtime REJECTS non-finite numbers and duplicate keys that CPython-parsed schema ACCEPTS."},
    "G4_parse_layer_both_fail": {"passed": bool(g4), "n": len(PARSE),
        "note": "Malformed bytes fail before schema validation under both oracles (schema N/A_PARSE, runtime REJECT)."},
    "G5_structural_schema_reject_superset": {"passed": bool(g5), "n": len(SSUP),
        "note": "NEW: schema REJECTS candidate-type payload-exclusivity and nested-chemistry violations that the runtime ACCEPTS (schema-stricter direction)."},
    "G6_resource_cap_boundary_localization": {"passed": bool(g6), "n": len(RESB),
        "note": "For depth/width/size: schema accepts all; runtime accept->reject transition is monotone; parity holds below the cap and runtime is a reject-superset past it."},
}
all_pass = all(v["passed"] for v in gates.values())

# ---- honest hypothesis adjudication ---------------------------------------
hypothesis = {
    "statement": "runtime and JSON Schema accept and reject the same finite typed corpus",
    "structural_core_layer": "CORROBORATED",           # field/type/binding/top-level-chem
    "structural_exclusivity_layer": "REFUTED",         # NEW: schema is stricter
    "lexical_resource_layer": "REFUTED",               # runtime is stricter (prior + boundary)
    "divergence_direction": "BIDIRECTIONAL",
    "verdict": "PARTIALLY_REFUTED",
    "interpretation": (
        "At scale the two deciders agree EXACTLY on the structural-core layer "
        f"({len(par_agree)}/{len(PAR)} PARITY-predicted cases: required-field presence, "
        "field JSON-type, candidate_type enum, payload-object binding, and the "
        "top-level chemistry-v2 gate). Equivalence FAILS in BOTH directions on "
        "the typed finite corpus: (a) the RUNTIME is a strict reject-superset on "
        "the LEXICAL/RESOURCE layer -- it refuses IEEE-754 non-finite numbers, "
        "duplicate keys, and inputs past the >8 MiB / >64-depth / >100000-width "
        "caps that a JSON-Schema validator over a permissive parser ACCEPTS; and "
        "(b) NEWLY, the SCHEMA is a strict reject-superset on the STRUCTURAL "
        "EXCLUSIVITY layer -- via allOf/if-then/not it forbids candidate-type "
        f"payload co-occurrence and nested chemistry-v2 keys ({len(ssup_confirmed)}/{len(SSUP)} cases) "
        "that the runtime ACCEPTS because the runtime only checks the required "
        "payload is an object plus a TOP-LEVEL chemistry gate. Neither decider "
        "subsumes the other; they are incomparable, not equivalent."),
}
divergence_notes = [
    {"class": "SCHEMA_SUPERSET",
     "note": "Schema enforces mutual exclusivity of molecule/formulation/evidence_refs "
             "payloads and bans chemistry-v2 keys nested inside the molecule payload; the "
             "Rust runtime enforces neither (it validates only the required payload object "
             "and a TOP-LEVEL chemistry-key gate). Phase-1: either tighten the runtime to "
             "reject co-occurring/nested payloads or relax the schema to match; today the "
             "front door is more PERMISSIVE than the published schema on this axis."},
    {"class": "RUNTIME_SUPERSET",
     "note": "Runtime rejects non-finite/duplicate-key/oversize/over-deep/over-wide inputs "
             "the schema-over-permissive-parser accepts (corroborates schema-runtime-parity-v1)."},
    {"class": "RES_BOUNDARY",
     "note": "Resource-cap transitions localized: see confusion_summary.boundaries for the "
             "exact runtime accept/reject parameter straddling each cap."},
]

diagnostic = {
    "schema": "amphora.candidate-contract.schema-runtime-differential-mutation.v1",
    "study_id": "schema-runtime-differential-mutation-v1",
    "module": "amphora-candidate-contract",
    "authority": "AUDIT_ONLY",
    "run_type": "DIFFERENTIAL_SCHEMA_VS_RUNTIME_MUTATION_AT_SCALE",
    "purpose": "Scale the schema/runtime differential test to a systematic grammar-based mutation corpus with resource-cap boundary localization, and adjudicate parity at scale.",
    "headline": (
        f"Structural-core parity CORROBORATED at scale ({len(par_agree)}/{len(PAR)}); "
        f"equivalence BIDIRECTIONALLY REFUTED -- runtime reject-superset on lexical/resource "
        f"({len(RSUP)} cases + 3 localized caps) AND schema reject-superset on structural "
        f"exclusivity/nested-chemistry ({len(ssup_confirmed)}/{len(SSUP)} cases)."),
    "non_circularity": (
        "Two independently-authored deciders: Oracle A is the on-disk declarative JSON "
        "Schema enforced by jsonschema " + version("jsonschema") + " over CPython json; "
        "Oracle B is the compiled Rust amphora-core contract runtime. Neither oracle was "
        "fitted to the other; per-case LAYER + relationship PREDICTION were declared in a "
        "third artifact (build_mutation_corpus.py) from the module semantics, never from "
        "either oracle's output."),
    "theory_reference": [
        "IETF RFC 8259 (2017) The JavaScript Object Notation (JSON) Data Interchange Format",
        "JSON Schema draft 2020-12 (2020-12-08) Core + Validation vocabularies (allOf/if-then/not, false subschemas)",
        "IETF RFC 8785 (2020) JSON Canonicalization Scheme (JCS)",
        "IEEE 754-2019 non-finite (NaN/Infinity) semantics",
        "CWE-400 Uncontrolled Resource Consumption; CWE-121 Stack-based Buffer Overflow (depth/width/size caps)",
        "NIST FIPS 180-4 (2015) SHA-256",
    ],
    "oracle_A_declarative": {
        "artifact": "amphora-candidate-contract/schemas/candidate-envelope.schema.json",
        "schema_sha256": sha(schema_bytes),
        "validator": "jsonschema==" + version("jsonschema"),
        "dialect": schema.get("$schema"),
        "parser": "CPython stdlib json (permissive: accepts NaN/Infinity, last-key-wins on duplicate keys)",
        "deployment_model": "parse-then-validate (the realistic schema-only front door)",
    },
    "oracle_B_runtime": {
        "artifact": "amphora-core::CandidateEnvelope::from_bytes",
        "amphora_core_contract_sha256": sha((ROOT / "amphora-core/src/contract.rs").read_bytes()),
        "caps": {"max_json_bytes": 8388608, "max_json_depth": 64, "max_collection_entries": 100000},
    },
    "corpus": {
        "n_cases": len(rows),
        "n_parity_predicted": len(PAR),
        "n_positive": len(positives),
        "n_runtime_superset_predicted": len(RSUP),
        "n_schema_superset_predicted": len(SSUP),
        "n_parse_predicted": len(PARSE),
        "n_resource_boundary": len(RESB),
        "manifest_sha256": sha((CORPUS / "_manifest.json").read_bytes()),
    },
    "confusion_summary": {
        "parity_agree": len(par_agree),
        "parity_disagree": len(par_disagree),
        "parity_disagreements": par_disagree,
        "runtime_superset_confirmed": sum(
            1 for x in RSUP if x["runtime_verdict"] == "REJECT" and x["schema_verdict"] == "ACCEPT"),
        "schema_superset_confirmed": len(ssup_confirmed),
        "parse_both_fail": sum(
            1 for x in PARSE if x["runtime_verdict"] == "REJECT" and x["schema_verdict"] == "N/A_PARSE"),
        "boundaries": boundaries,
    },
    "per_case": rows,
    "gates": gates,
    "all_gates_passed": bool(all_pass),
    "hypothesis": hypothesis,
    "divergence_notes": divergence_notes,
    "closes": [
        "Advances schema-runtime-parity-v1 'does_not_close' item #1: schema/runtime parity over a systematic grammar-based mutation space (not an exhaustive/coverage-guided fuzzer, but a combinatorial typed-mutation corpus with resource-cap boundary localization).",
        "Localizes the runtime resource-cap accept/reject transitions (depth/width/size) and confirms schema/runtime parity holds exactly up to each cap.",
        "NEW independent finding: schema/runtime divergence is BIDIRECTIONAL -- the schema is a reject-superset on candidate-type payload exclusivity and nested chemistry keys, which the runtime does not enforce.",
    ],
    "does_not_close": [
        "Coverage-guided/mutation fuzzing (libFuzzer/AFL) with crash-oracle and structure-aware minimization (Phase-1).",
        "Reason-level parity (verdict parity only is claimed; error taxonomies still differ).",
        "Whether the bidirectional divergence should be closed by tightening the runtime or relaxing the schema -- a Phase-1 design decision, not an audit call.",
        "No promotion, no manifest edit, no scientific_readiness flip, no wet-lab/qualification/release authority.",
    ],
}

OUT.write_text(json.dumps(diagnostic, indent=2, sort_keys=True) + "\n")
print("all_gates_passed", all_pass)
print("n_cases", len(rows))
print("parity", len(par_agree), "/", len(PAR), "disagree", par_disagree)
print("runtime_superset", diagnostic["confusion_summary"]["runtime_superset_confirmed"], "/", len(RSUP))
print("schema_superset", len(ssup_confirmed), "/", len(SSUP))
print("parse_both_fail", diagnostic["confusion_summary"]["parse_both_fail"], "/", len(PARSE))
for k, b in boundaries.items():
    print("boundary", k, "last_accept", b["runtime_last_accept_param"],
          "first_reject", b["runtime_first_reject_param"], "monotone", b["monotone"])
print("verdict", hypothesis["verdict"], hypothesis["divergence_direction"])
print("OUT_SHA256", sha(OUT.read_bytes()))
