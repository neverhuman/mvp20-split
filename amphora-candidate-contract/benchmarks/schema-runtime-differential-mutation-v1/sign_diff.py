#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-candidate-contract schema-runtime-differential-
mutation-v1 AUDIT_ONLY receipt.

AUDIT_ONLY: signs an audit receipt under evidence/audit/; does NOT sign a phase0
evaluation/review, does NOT promote authority, does NOT flip scientific_readiness
(stays NOT_APPLICABLE), does NOT modify the portfolio manifest (66 receipts / 11
modules), any locked dataset, the signed Phase-0 candidate-contract KPI, or the
module benchmark-lock. Derived key_id cross-checked against the pinned trust store.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
STUDY = "schema-runtime-differential-mutation-v1"
EV = ROOT / "amphora-candidate-contract/evidence/audit" / STUDY
BM = ROOT / "amphora-candidate-contract/benchmarks" / STUDY
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"
BLOCK = ROOT / "amphora-candidate-contract/evidence/phase0/benchmark/benchmark-lock.v1.json"
SCHEMA = ROOT / "amphora-candidate-contract/schemas/candidate-envelope.schema.json"

def sha(b): return hashlib.sha256(b).hexdigest()
def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " +
            str(len(body)).encode() + b" " + body)
def load_seed(p):
    raw = p.read_bytes().strip()
    if len(raw) == 64:
        try: return bytes.fromhex(raw.decode())
        except Exception: pass
    return raw[:32]

canon = (EV / "diagnostic.canonical.json").read_bytes()
runB = (EV / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)

harness_files = ["build_mutation_corpus.py", "run_diff.py", "rust_harness_main.rs", "Cargo.toml"]
harness_shas = {f: sha((BM / f).read_bytes()) for f in harness_files}
benchmark_lock_sha = sha(BLOCK.read_bytes())
schema_sha = sha(SCHEMA.read_bytes())

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

body_obj = {
    "schema": "amphora.candidate-contract.schema-runtime-differential-mutation-receipt.v1",
    "study_id": diag["study_id"],
    "authority": "AUDIT_ONLY",
    "run_type": diag["run_type"],
    "module": "amphora-candidate-contract",
    "promotes_authority": False, "flips_scientific_readiness": False,
    "human_review_performed": False, "organizational_independence_asserted": False,
    "modifies_manifest": False, "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False, "modifies_benchmark_lock": False,
    "claim": diag["headline"], "purpose": diag["purpose"],
    "non_circularity": diag["non_circularity"],
    "theory_reference": diag["theory_reference"],
    "oracle_A_declarative": diag["oracle_A_declarative"],
    "oracle_B_runtime": diag["oracle_B_runtime"],
    "corpus": diag["corpus"],
    "results": {
        "all_gates_passed": diag["all_gates_passed"],
        "parity_agree": diag["confusion_summary"]["parity_agree"],
        "parity_disagree": diag["confusion_summary"]["parity_disagree"],
        "runtime_superset_confirmed": diag["confusion_summary"]["runtime_superset_confirmed"],
        "schema_superset_confirmed": diag["confusion_summary"]["schema_superset_confirmed"],
        "parse_both_fail": diag["confusion_summary"]["parse_both_fail"],
        "boundaries": diag["confusion_summary"]["boundaries"],
        "hypothesis_structural_core_layer": diag["hypothesis"]["structural_core_layer"],
        "hypothesis_structural_exclusivity_layer": diag["hypothesis"]["structural_exclusivity_layer"],
        "hypothesis_lexical_resource_layer": diag["hypothesis"]["lexical_resource_layer"],
        "hypothesis_divergence_direction": diag["hypothesis"]["divergence_direction"],
        "hypothesis_verdict": diag["hypothesis"]["verdict"],
    },
    "gates": diag["gates"],
    "hypothesis": diag["hypothesis"],
    "divergence_notes": diag["divergence_notes"],
    "closes": diag["closes"], "does_not_close": diag["does_not_close"],
    "provenance": {
        "module_benchmark_lock_sha256": benchmark_lock_sha,
        "candidate_envelope_schema_sha256": schema_sha,
        "harness_sha256": harness_shas,
        "rust_runtime_verdicts_sha256": sha((EV / "rust_runtime_verdicts.json").read_bytes()),
        "corpus_manifest_sha256": sha((EV / "corpus_manifest.json").read_bytes()),
        "prior_study": "schema-runtime-parity-v1",
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "replay_method": "independent full pipeline: regenerate mutation corpus bytes into a fresh directory, re-run the compiled Rust runtime oracle, re-run schema-vs-runtime analysis",
    },
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
ptype = "application/vnd.amphora.candidate-contract-schema-runtime-differential-mutation+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
out = EV / (STUDY + "-receipt.v1.dsse.json")
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("two_replay_sha256", diag_sha)
print("receipt_sha256", sha(out.read_bytes()))
print("signature_len_field", len(receipt["signature"]))
print("signature_verified", True)
