#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-redteam-audit dispatch-boundary-fail-closed-v1
AUDIT_ONLY receipt. Signs an audit receipt under evidence/phase0/independent/;
does NOT sign a phase0 evaluation/review, does NOT promote authority, does NOT flip
scientific_readiness (stays NOT_APPLICABLE), does NOT modify the portfolio manifest
(66 receipts / 11 modules), any locked dataset, the Phase-0 KPI, or the benchmark-lock.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-redteam-audit"
BM = MOD / "benchmarks/dispatch-boundary-fail-closed-v1"
OUTDIR = MOD / "evidence/phase0/independent"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
RESULT_V1 = MOD / "evidence/phase0/benchmark/result.v1.json"
BLOCK = MOD / "evidence/phase0/benchmark/benchmark-lock.v1.json"
PRIOR = MOD / "benchmarks/meta-integrity-oracle-parity-v1/oracle.py"

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

# two-replay byte-stability gate over the oracle stdout
oracle_py = (BM / "oracle_dispatch_boundary.py").read_bytes()
canon = (BM / "result.v1.json").read_bytes()
import subprocess
runB = subprocess.check_output(["python3", str(BM / "oracle_dispatch_boundary.py")])
assert canon == runB, "two-replay bytes differ"
result_sha = sha(canon)
diag = json.loads(canon)
assert diag["all_gates_passed"] is True, "gates not all passed"
assert diag["verdict"] == "HYPOTHESIS_CORROBORATED"

oracle_sha = sha(oracle_py)
shipped_result_sha = sha(RESULT_V1.read_bytes())
benchmark_lock_sha = sha(BLOCK.read_bytes())
prior_oracle_sha = sha(PRIOR.read_bytes())

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw(); eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"

g = diag["gates"]
body_obj = {
    "schema": "amphora.redteam-audit.independent-oracle-receipt.v1",
    "receipt_id": f"redteam-audit-dispatch-boundary-fail-closed-{result_sha[:16]}",
    "oracle_id": "dispatch-boundary-fail-closed-v1",
    "module_id": "amphora-redteam-audit",
    "authority": "AUDIT_ONLY",
    "negative_result_authority": "AUDIT_ONLY",
    "phase0_promotion_effect": "NONE",
    "scientific_readiness": "NOT_APPLICABLE",
    "scientific_success_required_for_phase0": False,
    "promotes_authority": False, "flips_scientific_readiness": False,
    "human_review_performed": False, "organizational_independence_asserted": False,
    "modifies_manifest": False, "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False, "modifies_benchmark_lock": False,
    "hypothesis": diag["hypothesis"],
    "verdict": diag["verdict"],
    "all_gates_passed": diag["all_gates_passed"],
    "theory_sources": diag["theory_sources"],
    "relation_to_prior_oracle": diag["relation_to_prior_oracle"],
    "gate_summary": {
        "G1_supported_set_derivation_passed": g["G1_supported_set_derivation"]["passed"],
        "G1_derived_supported_ids": g["G1_supported_set_derivation"]["derived_supported_ids"],
        "G2_shipped_probe_reproduction_passed": g["G2_shipped_probe_reproduction"]["passed"],
        "G2_shipped_probe_count": g["G2_shipped_probe_reproduction"]["shipped_probe_count"],
        "G3_positive_control_acceptance_passed": g["G3_positive_control_acceptance"]["passed"],
        "G3_genuine_id_count": g["G3_positive_control_acceptance"]["genuine_id_count"],
        "G4_near_miss_fuzz_passed": g["G4_near_miss_fuzz_fail_closed"]["passed"],
        "G4_total_near_miss_probes": g["G4_near_miss_fuzz_fail_closed"]["total_near_miss_probes"],
        "G4_fail_closed_rate": g["G4_near_miss_fuzz_fail_closed"]["fail_closed_rate"],
        "G4_accidental_exact_collisions": g["G4_near_miss_fuzz_fail_closed"]["accidental_exact_collisions"],
        "G5_exact_match_necessity_passed": g["G5_exact_match_necessity"]["passed"],
    },
    "subject_anchors": {
        "shipped_result_v1_sha256": shipped_result_sha,
        "benchmark_lock_sha256": benchmark_lock_sha,
        "kpi_field_reproduced": "unsupported_module_id_fail_closed_rate",
    },
    "provenance": {
        "oracle_script": "benchmarks/dispatch-boundary-fail-closed-v1/oracle_dispatch_boundary.py",
        "oracle_script_sha256": oracle_sha,
        "oracle_result_sha256": result_sha,
        "prior_oracle_sha256": {"meta-integrity-oracle-parity-v1/oracle.py": prior_oracle_sha},
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "replay_count": 2,
        "canonical_result_sha256": result_sha,
        "runB_result_sha256": sha(runB),
        "byte_identical": canon == runB,
        "replay_method": ("independent CPython: derive the supported-module accept-set from "
                          "shipped result.v1.json records, reproduce the 6 KPI fail-closed "
                          "probes byte-exact, enumerate a deterministic near-miss corpus over "
                          "each genuine id, and prove exact-byte-match necessity vs case-fold "
                          "and Unicode-TR39 confusable-skeleton relaxations"),
    },
    "ceiling_note": diag["ceiling_note"],
    "zero_authority_claim_locks": {
        "no_ranking_authority": True, "no_optimizer_authority": True,
        "no_release_authority": True, "no_qualification_authority": True,
        "no_patentability_authority": True, "fto_not_performed": True,
        "no_procurement_authority": True, "no_regulatory_authority": True,
        "no_safety_authority": True, "no_product_performance_authority": True,
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY independent-oracle receipt under evidence/phase0/independent/",
        "signs_phase0_evaluation_or_review": False},
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER", "key_id": rev_key_id, "public_key_hex": rev_pub_hex,
        "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no human review performed."},
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.redteam-audit-independent-oracle-receipt.v1+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {
    "evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
    "reviewer_public_key_hex": rev_pub_hex,
    "authority": "AUDIT_ONLY", "phase0_promotion_effect": "NONE",
    "scientific_readiness": "NOT_APPLICABLE",
    "receipt_id": body_obj["receipt_id"], "schema": body_obj["schema"],
    "module_id": "amphora-redteam-audit", "verdict": diag["verdict"],
    "oracle_script_sha256": oracle_sha, "oracle_result_sha256": result_sha,
    "replay_count": 2, "replay_hash": result_sha,
    "signature": envelope,
}
OUTDIR.mkdir(parents=True, exist_ok=True)
out = OUTDIR / "dispatch-boundary-fail-closed-v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("receipt_sha256", sha(out.read_bytes()))
print("two_replay_sha256", result_sha)
print("signature_verified", True)
print("sig_len", len(envelope["signatures"][0]["sig"]))
