#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-molecule-novelty CORPUS-DUPLICATE-
EXCHANGEABILITY AUDIT_ONLY receipt. AUDIT_ONLY: signs under evidence/audit/;
does NOT sign a phase0 evaluation/review, does NOT promote authority, does
NOT flip scientific_readiness (stays UNVALIDATED), does NOT modify the
manifest (66 receipts / 11 modules), any locked dataset, or the signed
Phase-0 novelty KPI. Derived key_id cross-checked vs pinned trust store.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT/"amphora-molecule-novelty/evidence/audit/corpus-duplicate-exchangeability-audit-v1"
SEED_DIR = Path.home()/".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR/"evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR/"internal-reviewer.ed25519.seed"
TRUST = ROOT/"config/phase0-trust-store.v1.json"

def sha(b): return hashlib.sha256(b).hexdigest()
def pae(t, body): return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() +
                           b" " + str(len(body)).encode() + b" " + body)
def load_seed(p):
    raw = p.read_bytes().strip()
    if len(raw) == 64:
        try: return bytes.fromhex(raw.decode())
        except Exception: pass
    return raw[:32]

canon = (BENCH/"diagnostic.canonical.json").read_bytes()
runB = (BENCH/"diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)
harness_sha = sha((BENCH/"run_novelty_dedup_audit.py").read_bytes())

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw(); eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"
eval_pin = rev_pin = False
if TRUST.exists():
    trust = json.loads(TRUST.read_text())
    tbr = {k.get("role"): k for k in trust.get("keys", [])}
    eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
    rev_pin = (rev_key_id == tbr.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))

hyp = diag["hypothesis_evaluation"]
body_obj = {
    "schema": diag["schema"], "study_id": diag["study_id"],
    "authority": "AUDIT_ONLY", "run_type": "NOVELTY_CORPUS_DUPLICATE_EXCHANGEABILITY_AUDIT",
    "module": "amphora-molecule-novelty",
    "promotes_authority": False, "flips_scientific_readiness": False,
    "human_review_performed": False, "organizational_independence_asserted": False,
    "modifies_manifest": False, "modifies_locked_dataset": False, "modifies_signed_phase0_kpi": False,
    "claim": diag["headline"], "purpose": diag["purpose"], "non_circularity": diag["non_circularity"],
    "theory_reference": diag["theory_reference"], "rdkit_version": diag["rdkit_version"],
    "method": diag["method"], "families": diag["families"], "family_reference": diag["family_reference"],
    "alphas": diag["alphas"], "corpus": diag["corpus"],
    "duplicate_groups_top10_by_size": diag["duplicate_groups_top10_by_size"],
    "candidates": diag["candidates"],
    "anchor": diag["anchor"], "anchor_exact_all": diag["anchor_exact_all"],
    "results": {
        "n_flip_cells": diag["n_flip_cells"],
        "flipped_candidates": diag["flipped_candidates"],
        "flips": diag["flips"],
        "drift_morgan_r2_2048": diag["drift_morgan_r2_2048"],
        "targeted_prior_claim_check": diag["targeted_prior_claim_check"],
        "self_tests_all_pass": diag["self_tests_all_pass"],
        "hypothesis_verdict": hyp["verdict"],
    },
    "drift_all_families": diag["drift_all_families"],
    "hypothesis_evaluation": hyp,
    "rights_posture": diag["rights_posture"], "closes": diag["closes"],
    "does_not_close": diag["does_not_close"],
    "reproducibility": {"two_replay_sha256_gate": "PASS", "canonical_diagnostic_sha256": diag_sha,
                         "runB_diagnostic_sha256": sha(runB), "byte_identical": canon == runB,
                         "harness_sha256": harness_sha},
    "self_tests": diag["self_tests"],
    "signing_key": {"role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
                     "used_for": "AUDIT_ONLY audit receipt under evidence/audit/",
                     "signs_phase0_evaluation_or_review": False,
                     "derives_pinned_trust_store_key_id": bool(eval_pin)},
    "reviewer_reference": {"role": "PHASE0_INTERNAL_REVIEWER", "key_id": rev_key_id,
                            "public_key_hex": rev_pub_hex,
                            "derives_pinned_trust_store_key_id": bool(rev_pin),
                            "reviewer_signature_present": False,
                            "note": "Reviewer key referenced for provenance only; no independent human review performed."},
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.molecule-novelty-corpus-duplicate-exchangeability+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
out_path = BENCH/"corpus-duplicate-exchangeability-receipt.v1.dsse.json"
out_path.write_text(json.dumps(receipt, indent=2, sort_keys=True))
print("wrote", out_path)
print("eval_pin", eval_pin, "rev_pin", rev_pin)
