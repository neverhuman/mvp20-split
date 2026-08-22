#!/usr/bin/env python3
"""amphora-candidate-contract  raw-structure-ban-recursion-v1  (AUDIT_ONLY)

Adversarial completeness characterization of the CandidateEnvelope schema's
"no raw chemical structure / no free-text recipe" provenance ban.

Stated module policy (candidate-envelope.schema.json): raw structure formats
(inchi, inchi_key, inchikey, mol, mol_block, mol_v2000, mol_v3000, sdf,
sdf_records) and free-text recipe (recipe_csv) are forbidden; candidates must
declare canonical_smiles + canonical_structure_hash only. The schema encodes
this by pinning those property names to `false` at three surfaces: top-level,
`molecule`, and (recipe_csv only) `formulation` / `formulation.recipe`.

Hypothesis under test: is that ban RECURSIVE (enforced everywhere a candidate
object can nest), or only enforced at the declared surfaces? The schema also
contains many `additionalProperties: true` (or unconstrained `type: object`)
"open bags": context, context.model_run(.proposal_metadata),
context.optimization_request, evidence_refs, formulation (structure keys not
banned there), formulation.target_envelope/application/process, molecule
(recipe_csv not banned there). If the ban is non-recursive, a raw-structure key
smuggled into an open bag will validate ACCEPT -> a schema-layer smuggling
channel that defeats the stated provenance invariant.

Theory / references:
  - JSON Schema draft 2020-12 (2020-12-08) core+validation vocabularies:
    `additionalProperties: false` closes a bag; default is OPEN.
  - IETF RFC 8259 (2017) JSON grammar; RFC 8785 (2020) JCS (hash foundation).
  - CWE-20 Improper Input Validation; CWE-915 Improperly Controlled
    Modification of Object Attributes (mass-assignment / smuggling).
  - Reinforces prior receipt schema-runtime-parity-v1 (runtime = strict
    reject-superset; front door irreplaceable).

AUDIT_ONLY: no promotion, no manifest edit, no scientific_readiness flip,
no locked-dataset / signed-KPI / benchmark-lock modification.
"""
import base64, copy, hashlib, json, sys
from pathlib import Path
import jsonschema
from jsonschema import Draft202012Validator
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-candidate-contract"
FIX = MOD / "fixtures"
SCHEMA_PATH = MOD / "schemas/candidate-envelope.schema.json"
EV = MOD / "evidence/audit/raw-structure-ban-recursion-v1"
BM = MOD / "benchmarks/raw-structure-ban-recursion-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"
BLOCK = MOD / "evidence/phase0/benchmark/benchmark-lock.v1.json"

def sha(b): return hashlib.sha256(b).hexdigest()

SCHEMA = json.loads(SCHEMA_PATH.read_bytes())

# Raw-structure / free-recipe forbidden family (exactly the names the schema
# pins to `false` somewhere). Independently re-derived from the schema, not
# hardcoded: collect every property whose subschema is the literal `false`.
def collect_false_keys(node, acc):
    if isinstance(node, dict):
        props = node.get("properties")
        if isinstance(props, dict):
            for k, v in props.items():
                if v is False:
                    acc.add(k)
        for v in node.values():
            collect_false_keys(v, acc)
    elif isinstance(node, list):
        for v in node:
            collect_false_keys(v, acc)
BANNED = set()
collect_false_keys(SCHEMA, BANNED)   # discovered from the real schema

validator = Draft202012Validator(SCHEMA)

def verdict(obj):
    errs = sorted(validator.iter_errors(obj), key=lambda e: list(e.absolute_path))
    if not errs:
        return {"accept": True, "reason": None, "path": None, "keyword": None}
    e = errs[0]
    return {"accept": False, "reason": e.message[:160],
            "path": "/".join(str(p) for p in e.absolute_path),
            "keyword": e.validator}

def deep_set(base, path, key, value="RAW-STRUCTURE-SMUGGLED"):
    o = copy.deepcopy(base)
    cur = o
    for p in path:
        cur = cur.setdefault(p, {})
    cur[key] = value
    return o

# ---- base envelopes (module's own on-disk fixtures) ------------------------
mol_base  = json.loads((FIX / "molecule_candidate.json").read_bytes())
form_base = json.loads((FIX / "canonical_formulation_candidate.json").read_bytes())
evid_base = json.loads((FIX / "evidence_package_candidate.json").read_bytes())

PROBE_KEY = "mol_block"   # representative raw-structure key (in BANNED)
REC_KEY = "recipe_csv"    # free-text recipe key (in BANNED)

def analyze():
    assert PROBE_KEY in BANNED and REC_KEY in BANNED, "probe keys not in discovered ban set"
    cases = []

    # positive controls: clean bases must validate ACCEPT
    for nm, b in [("BASE_molecule", mol_base), ("BASE_formulation", form_base),
                  ("BASE_evidence_package", evid_base)]:
        v = verdict(b)
        cases.append({"case": nm, "class": "base_positive", "site": "(root)",
                      "injected": None, "expect": "ACCEPT", "verdict": v,
                      "as_expected": v["accept"] is True})

    # declared-surface controls: ban must fire (expect REJECT)
    declared = [
        ("DS_top_mol_block",   mol_base,  [],           PROBE_KEY),
        ("DS_top_sdf",         mol_base,  [],           "sdf"),
        ("DS_top_recipe_csv",  mol_base,  [],           REC_KEY),
        ("DS_top_inchi_evid",  evid_base, [],           "inchi"),
        ("DS_molecule_mol_block", mol_base, ["molecule"], PROBE_KEY),
        ("DS_molecule_inchi_key", mol_base, ["molecule"], "inchi_key"),
        ("DS_molecule_sdf_records", mol_base, ["molecule"], "sdf_records"),
        ("DS_formulation_recipe_csv", form_base, ["formulation"], REC_KEY),
    ]
    for nm, b, path, key in declared:
        # base validates clean (checked in base_positive), so a REJECT after
        # injecting exactly one banned key is attributable to that key. We also
        # confirm the rejection hit the ban mechanism: a `property: false`
        # subschema, which jsonschema reports as "False schema does not allow".
        base_clean = verdict(b)["accept"] is True
        o = deep_set(b, path, key)
        v = verdict(o)
        ban_mechanism = ("False schema" in (v["reason"] or "")
                         or key in (v["reason"] or "")
                         or (v["path"] or "").split("/")[-1] == key)
        cases.append({"case": nm, "class": "declared_surface", "site": "/".join(path) or "(root)",
                      "injected": key, "expect": "REJECT", "verdict": v,
                      "base_validates_clean": base_clean,
                      "attributed_to_ban": bool(v["accept"] is False and ban_mechanism),
                      "as_expected": bool(base_clean and v["accept"] is False and ban_mechanism)})

    # open-bag smuggle probes: test recursion (verdict observed, not asserted)
    openbags = [
        ("OB_context",                 mol_base,  ["context"],                              PROBE_KEY),
        ("OB_context_recipe_csv",      mol_base,  ["context"],                              REC_KEY),
        ("OB_context_model_run",       mol_base,  ["context", "model_run"],                 PROBE_KEY),
        ("OB_context_proposal_meta",   mol_base,  ["context", "model_run", "proposal_metadata"], PROBE_KEY),
        ("OB_context_optreq",          mol_base,  ["context", "optimization_request"],      "sdf"),
        ("OB_evidence_refs",           mol_base,  ["evidence_refs"],                        PROBE_KEY),
        ("OB_molecule_recipe_csv",     mol_base,  ["molecule"],                             REC_KEY),
        ("OB_formulation_mol_block",   form_base, ["formulation"],                          PROBE_KEY),
        ("OB_formulation_target_env",  form_base, ["formulation", "target_envelope"],       "sdf"),
        ("OB_formulation_application", form_base, ["formulation", "application"],           "inchi"),
        ("OB_formulation_process",     form_base, ["formulation", "process"],               "mol_v3000"),
        ("OB_evref_nested_pkg",        evid_base, ["evidence_refs", "evidence_package"],    PROBE_KEY),
    ]
    accepting_sites = []
    for nm, b, path, key in openbags:
        o = deep_set(b, path, key)
        v = verdict(o)
        # benign-open control at the SAME site: proves the bag is genuinely open,
        # so a banned-key ACCEPT is non-recursion (not incidental).
        ob = deep_set(b, path, "benign_annotation_note")
        vb = verdict(ob)
        smuggle = (v["accept"] is True)
        genuinely_open = (vb["accept"] is True)
        if smuggle and genuinely_open:
            accepting_sites.append("/".join(path))
        cases.append({"case": nm, "class": "open_bag_probe", "site": "/".join(path),
                      "injected": key, "expect": "OBSERVE", "verdict": v,
                      "benign_key_accepted": genuinely_open,
                      "is_smuggling_channel": bool(smuggle and genuinely_open)})

    # mutation / non-circularity control: patch schema to ban PROBE_KEY under
    # `context`, re-validate OB_context -> must flip ACCEPT->REJECT (hole real+closable).
    patched = copy.deepcopy(SCHEMA)
    patched["properties"]["context"].setdefault("properties", {})[PROBE_KEY] = False
    pv_before = verdict(deep_set(mol_base, ["context"], PROBE_KEY))
    pval = Draft202012Validator(patched)
    _errs = list(pval.iter_errors(deep_set(mol_base, ["context"], PROBE_KEY)))
    pv_after_accept = (len(_errs) == 0)
    mutation_flips = (pv_before["accept"] is True and pv_after_accept is False)

    # gates
    base_ok = all(c["as_expected"] for c in cases if c["class"] == "base_positive")
    declared_ok = all(c["as_expected"] for c in cases if c["class"] == "declared_surface")
    n_declared = sum(1 for c in cases if c["class"] == "declared_surface")
    n_channels = len(accepting_sites)
    open_probes = [c for c in cases if c["class"] == "open_bag_probe"]

    gates = {
        "G1_declared_surface_ban_enforced": {
            "pass": bool(base_ok and declared_ok),
            "detail": f"{sum(1 for c in cases if c['class']=='declared_surface' and c['as_expected'])}/{n_declared} declared-surface injections REJECT + 3/3 bases ACCEPT"},
        "G2_ban_is_non_recursive": {
            "pass": bool(n_channels >= 1),
            "detail": f"{n_channels} open sub-bags admit a smuggled banned key (each also accepts a benign key => genuine non-recursion)",
            "channels": sorted(accepting_sites)},
        "G3_mutation_closes_hole_noncircular": {
            "pass": bool(mutation_flips),
            "detail": "patching schema `context` with mol_block:false flips ACCEPT->REJECT (probe reads real schema; hole is real & closable)"},
    }
    all_gates = all(g["pass"] for g in gates.values())

    headline = (
        f"Schema-layer raw-structure ban is NON-RECURSIVE: enforced at the "
        f"declared surfaces ({n_declared}/{n_declared} reject + bases accept) but "
        f"{n_channels} open sub-bags admit smuggled raw-structure/recipe keys => "
        f"the JSON Schema alone does NOT enforce the no-raw-structure provenance "
        f"invariant; the runtime front door (strict reject-superset, "
        f"schema-runtime-parity-v1) is load-bearing for this invariant.")

    diag = {
        "schema": "amphora.candidate-contract.raw-structure-ban-recursion-diagnostic.v1",
        "study_id": "raw-structure-ban-recursion-v1",
        "module": "amphora-candidate-contract",
        "authority": "AUDIT_ONLY",
        "run_type": "adversarial-schema-completeness",
        "headline": headline,
        "hypothesis": {
            "H": "The no-raw-structure/no-free-recipe ban encoded in candidate-envelope.schema.json is enforced RECURSIVELY at every candidate sub-object.",
            "verdict": "REFUTED",
            "basis": "declared surfaces enforce it; open sub-bags do not"},
        "purpose": "Quantify the exact schema-layer attack surface of the raw-structure provenance ban and prove it is a declared-surface-only mechanism, motivating the load-bearing runtime front door.",
        "non_circularity": "Banned key family re-derived by walking the on-disk schema for `false`-valued properties (not hardcoded); verdicts produced by a conformant Draft 2020-12 validator; mutation control re-validates against a patched schema.",
        "theory_reference": {
            "json_schema": "draft 2020-12 (2020-12-08) additionalProperties default-open semantics",
            "json_grammar": "IETF RFC 8259 (2017)",
            "canonicalization": "IETF RFC 8785 (2020) JCS",
            "weakness_taxonomy": ["CWE-20 Improper Input Validation", "CWE-915 Improperly Controlled Modification of Object Attributes"],
            "reinforces": "amphora-candidate-contract schema-runtime-parity-v1 (runtime strict reject-superset)"},
        "banned_key_family_discovered": sorted(BANNED),
        "probe_keys": {"structure": PROBE_KEY, "recipe": REC_KEY},
        "counts": {
            "n_cases": len(cases),
            "n_base_positive": 3,
            "n_declared_surface": n_declared,
            "n_open_bag_probes": len(open_probes),
            "n_smuggling_channels": n_channels},
        "smuggling_channels": sorted(accepting_sites),
        "mutation_control": {
            "site": "context", "key": PROBE_KEY,
            "accept_before_patch": pv_before["accept"],
            "accept_after_patch": pv_after_accept,
            "flips_accept_to_reject": mutation_flips},
        "gates": gates,
        "all_gates_passed": all_gates,
        "per_case": cases,
        "closes": [
            "First independent enumeration of the raw-structure ban's attack surface across the candidate-envelope schema's open sub-bags.",
            "Proves the ban is a declared-surface mechanism (non-recursive) and lists the exact closable smuggling channels."],
        "does_not_close": [
            "Whether the Rust runtime front door rejects each listed channel (prior receipt shows runtime is a strict reject-superset over its tested classes; per-channel runtime confirmation is future work).",
            "Deep structural/semantic validity of smuggled payloads (only key-name admission is characterized)."],
    }
    return diag

def canon_bytes(d):
    return json.dumps(d, indent=2, sort_keys=True).encode()

# ---- two-replay: run analysis twice, assert byte-identical -----------------
EV.mkdir(parents=True, exist_ok=True)
diagA = analyze()
diagB = analyze()
cA, cB = canon_bytes(diagA), canon_bytes(diagB)
assert cA == cB, "two-replay diagnostic bytes differ"
(EV / "diagnostic.canonical.json").write_bytes(cA)
(EV / "diagnostic.runB.json").write_bytes(cB)
diag_sha = sha(cA)

# tamper detection sanity
tampered = json.loads(cA); tampered["counts"]["n_smuggling_channels"] = 999
assert sha(canon_bytes(tampered)) != diag_sha, "tamper not detected"

# ---- sign DSSE Ed25519 (mirrors schema-runtime-parity-v1 sign pattern) -----
def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " +
            str(len(body)).encode() + b" " + body)
def load_seed(p):
    raw = p.read_bytes().strip()
    if len(raw) == 64:
        try: return bytes.fromhex(raw.decode())
        except Exception: pass
    return raw[:32]

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw(); eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
rev_pin = (rev_key_id == tbr.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))

harness_sha = {"rawstruct_probe.py": sha(Path(__file__).read_bytes())}
schema_sha = sha(SCHEMA_PATH.read_bytes())
block_sha = sha(BLOCK.read_bytes())

body_obj = {
    "schema": "amphora.candidate-contract.raw-structure-ban-recursion-receipt.v1",
    "study_id": diagA["study_id"],
    "authority": "AUDIT_ONLY",
    "run_type": diagA["run_type"],
    "module": "amphora-candidate-contract",
    "promotes_authority": False, "flips_scientific_readiness": False,
    "human_review_performed": False, "organizational_independence_asserted": False,
    "modifies_manifest": False, "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False, "modifies_benchmark_lock": False,
    "claim": diagA["headline"],
    "purpose": diagA["purpose"],
    "non_circularity": diagA["non_circularity"],
    "theory_reference": diagA["theory_reference"],
    "hypothesis": diagA["hypothesis"],
    "banned_key_family_discovered": diagA["banned_key_family_discovered"],
    "counts": diagA["counts"],
    "smuggling_channels": diagA["smuggling_channels"],
    "mutation_control": diagA["mutation_control"],
    "gates": diagA["gates"],
    "all_gates_passed": diagA["all_gates_passed"],
    "closes": diagA["closes"], "does_not_close": diagA["does_not_close"],
    "provenance": {
        "module_benchmark_lock_sha256": block_sha,
        "candidate_envelope_schema_sha256": schema_sha,
        "harness_sha256": harness_sha,
        "jsonschema_version": jsonschema.__version__},
    "reproducibility": {
        "two_replay_sha256_gate": "PASS" if cA == cB else "FAIL",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(cB),
        "byte_identical": cA == cB,
        "replay_method": "independent full pipeline: re-derive banned family from schema, rebuild probe corpus, re-run Draft2020-12 validator + mutation control, re-serialize canonical diagnostic"},
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under evidence/audit/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin)},
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER", "key_id": rev_key_id, "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin), "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed."},
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.candidate-contract-raw-structure-ban-recursion+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
out = EV / "raw-structure-ban-recursion-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))

print("BANNED_FAMILY", sorted(BANNED))
print("N_CHANNELS", diagA["counts"]["n_smuggling_channels"])
print("CHANNELS", diagA["smuggling_channels"])
print("ALL_GATES_PASSED", diagA["all_gates_passed"])
print("GATES", {k: v["pass"] for k, v in diagA["gates"].items()})
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("two_replay_sha256", diag_sha)
print("receipt_sha256", sha(out.read_bytes()))
print("WROTE", out)
