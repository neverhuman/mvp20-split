#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-molecule-design-gate smiles-representation-
invariance-v1 AUDIT_ONLY receipt. AUDIT_ONLY: signs an audit receipt under
evidence/audit/; does NOT sign a phase0 evaluation/review, does NOT promote
authority, does NOT flip scientific_readiness, does NOT modify the portfolio
manifest (66 receipts / 11 modules), module-manifest.json, any locked dataset,
or a signed Phase-0 KPI. Derived key_id cross-checked vs pinned trust store."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-molecule-design-gate/evidence/audit/smiles-representation-invariance-v1"
FIX = ROOT / "amphora-molecule-design-gate/reference/phase0-design-gate-known-answer.v1.json"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

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

canon = (BENCH / "diagnostic.canonical.json").read_bytes()
runB = (BENCH / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)
oracle_sha = sha((BENCH / "design_gate_repr_invariance_oracle.py").read_bytes())
fixture_sha = sha(FIX.read_bytes())

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw(); eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub = rev_sk.public_key().public_bytes_raw(); rev_pub_hex = rev_pub.hex()
rev_key_id = f"phase0-internal-reviewer-{sha(rev_pub)}"
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
rev_pin = (rev_key_id == tbr.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))

g = diag["gates"]
body_obj = {
    "schema": "amphora.molecule-design-gate.smiles-representation-invariance-receipt.v1",
    "study_id": diag["study_id"],
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "REAL_ARITHMETIC",
    "run_type": diag["run_type"],
    "module": "amphora-molecule-design-gate",
    "promotes_authority": False, "flips_scientific_readiness": False,
    "human_review_performed": False, "organizational_independence_asserted": False,
    "modifies_manifest": False, "modifies_module_manifest": False,
    "modifies_locked_dataset": False, "modifies_signed_phase0_kpi": False,
    "purpose": diag["purpose"],
    "hypothesis": diag["hypothesis"],
    "non_circularity": diag["non_circularity"],
    "adversarial_relevance": diag["adversarial_relevance"],
    "theory_reference": diag["theory_reference"],
    "method": diag["method"],
    "runtime_source_anchors": diag["runtime_source_anchors"],
    "rdkit_version": diag["rdkit_version"],
    "results": {
        "all_gates_passed": g["all_pass"],
        "g1_oxirane_representation_invariant": g["g1_oxirane_representation_invariant"],
        "g2_amineH_representation_invariant": g["g2_amineH_representation_invariant"],
        "g3_decision_representation_invariant": g["g3_decision_representation_invariant"],
        "g4_non_trivial_distinct_encodings": g["g4_non_trivial_distinct_encodings"],
        "g5_aromatic_kekule_robust": g["g5_aromatic_kekule_robust"],
        "counts": diag["counts"],
        "n_oxirane_invariant": sum(1 for x in diag["g1_oxirane_invariance"]["records"] if x["invariant"]),
        "n_amineH_invariant": sum(1 for x in diag["g2_amineH_invariance"]["records"] if x["invariant"]),
        "n_decision_invariant": sum(1 for x in diag["g3_decision_invariance"]["records"] if x["decision_invariant"]),
        "n_meets_distinct_floor": sum(1 for x in diag["g4_non_triviality"]["records"] if x["meets_floor"]),
        "n_aromatic_kekule_match": sum(1 for x in diag["g5_aromatic_kekule_robustness"]["records"] if x["decision_match"] and x["counts_match"]),
    },
    "gates": diag["gates"],
    "closes": diag["closes"], "does_not_close": diag["does_not_close"],
    "provenance": {
        "oracle_sha256": oracle_sha,
        "dataset_fixture_sha256": fixture_sha,
        "dataset_fixture_path": "reference/phase0-design-gate-known-answer.v1.json",
        "prior_receipt": "evidence/audit/rdkit-structural-facts-parity-v1",
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "oracle_sha256": oracle_sha,
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
ptype = "application/vnd.amphora.molecule-design-gate-smiles-representation-invariance+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
out = BENCH / "smiles-representation-invariance-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("two_replay_sha256", diag_sha)
print("fixture_sha256", fixture_sha)
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
