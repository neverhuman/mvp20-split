#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-redteam-audit axis-adequacy-subsumption-v1 AUDIT_ONLY
receipt. Signs an audit receipt under evidence/phase0/independent/; does NOT sign a
phase0 evaluation/review, does NOT promote authority, does NOT flip scientific_readiness
(stays NOT_APPLICABLE), does NOT modify the portfolio manifest (66 receipts / 11 modules),
any locked dataset, the Phase-0 KPI, or the benchmark-lock.
"""
import base64, hashlib, json, subprocess
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-redteam-audit"
BM = MOD / "benchmarks/axis-adequacy-subsumption-v1"
OUTDIR = MOD / "evidence/phase0/independent"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
RESULT_V1 = MOD / "evidence/phase0/benchmark/result.v1.json"
BLOCK = MOD / "evidence/phase0/benchmark/benchmark-lock.v1.json"
PRIOR = {
    "meta-integrity-oracle-parity-v1/oracle.py":
        MOD / "benchmarks/meta-integrity-oracle-parity-v1/oracle.py",
    "dispatch-boundary-fail-closed-v1/oracle_dispatch_boundary.py":
        MOD / "benchmarks/dispatch-boundary-fail-closed-v1/oracle_dispatch_boundary.py",
}


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
oracle_py = (BM / "oracle_axis_adequacy.py").read_bytes()
canon = (BM / "result.v1.json").read_bytes()
runB = subprocess.check_output(["python3", str(BM / "oracle_axis_adequacy.py")])
assert canon == runB, "two-replay bytes differ"
result_sha = sha(canon)
diag = json.loads(canon)
assert diag["all_gates_passed"] is True, "gates not all passed"
assert diag["verdict"] == "HYPOTHESIS_PARTIALLY_REFUTED"

oracle_sha = sha(oracle_py)
shipped_result_sha = sha(RESULT_V1.read_bytes())
benchmark_lock_sha = sha(BLOCK.read_bytes())
prior_sha = {k: sha(v.read_bytes()) for k, v in PRIOR.items()}

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw(); eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"

g = diag["gates"]
h = diag["headline_numbers"]
body_obj = {
    "schema": "amphora.redteam-audit.independent-oracle-receipt.v1",
    "receipt_id": f"redteam-audit-axis-adequacy-subsumption-{result_sha[:16]}",
    "oracle_id": "axis-adequacy-subsumption-v1",
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
    "verdict_statement": diag["verdict_statement"],
    "all_gates_passed": diag["all_gates_passed"],
    "theory_sources": diag["theory_sources"],
    "relation_to_prior_oracle": diag["relation_to_prior_oracle"],
    "headline_numbers": h,
    "gate_summary": {
        "G1_lock_multiset_structure_passed": g["G1_lock_multiset_structure"]["passed"],
        "G1_digest_parity": g["G1_lock_multiset_structure"]["digest_parity"],
        "G1_declared_array_len": g["G1_lock_multiset_structure"]["declared_array_length"],
        "G1_declared_unique": g["G1_lock_multiset_structure"]["declared_unique_count"],
        "G1_duplicate_axes": g["G1_lock_multiset_structure"]["duplicate_axes"],
        "G2_shipped_kpi_self_criterion_passed": g["G2_shipped_kpi_self_criterion"]["passed"],
        "G2_recomputed_observed": g["G2_shipped_kpi_self_criterion"]["recomputed_observed"],
        "G2_arithmetic_defect_found": g["G2_shipped_kpi_self_criterion"]["arithmetic_defect_found"],
        "G3_adequacy_subsumption_passed": g["G3_adequacy_subsumption_falsification"]["passed"],
        "G3_observed_C_declared_exact": g["G3_adequacy_subsumption_falsification"]["observed_C_declared_exact"],
        "G3_uncovered_count": g["G3_adequacy_subsumption_falsification"]["uncovered_count"],
        "G3_uncovered_axes": g["G3_adequacy_subsumption_falsification"]["uncovered_axes"],
        "G4_block_partition_passed": g["G4_block_partition_diagnosis"]["passed"],
        "G4_checked_equals_ordered_inner_block": g["G4_block_partition_diagnosis"]["checked_equals_ordered_inner_block"],
        "G4_block_set_overlap": g["G4_block_partition_diagnosis"]["block_set_overlap"],
        "G4_random_subset_null_probability": g["G4_block_partition_diagnosis"]["random_subset_null_probability"],
        "G5_compensating_control_passed": g["G5_compensating_control_search"]["passed"],
        "G5_modules_scanned": g["G5_compensating_control_search"]["modules_scanned"],
        "G5_modules_with_axis_coverage_kpi": g["G5_compensating_control_search"]["modules_with_axis_coverage_kpi"],
        "G5_declared_only_count": g["G5_compensating_control_search"]["declared_only_count"],
        "G5_compensating_kpi_attestations_found": g["G5_compensating_control_search"]["compensating_kpi_attestations_found"],
        "G6_duplicate_counterfactual_passed": g["G6_duplicate_axis_counterfactual"]["passed"],
        "G6_dedup_changes_digest": g["G6_duplicate_axis_counterfactual"]["dedup_changes_digest"],
        "G6_kpi_unchanged_by_dedup": g["G6_duplicate_axis_counterfactual"]["kpi_unchanged_by_dedup"],
        "G7_anchors_and_replay_passed": g["G7_anchors_and_replay"]["passed"],
    },
    "subject_anchors": {
        "shipped_result_v1_sha256": shipped_result_sha,
        "benchmark_lock_sha256": benchmark_lock_sha,
        "kpi_document_sha256": g["G7_anchors_and_replay"]["kpi_document_sha256"],
        "kpi_field_audited": "attack_axis_coverage_complete_rate",
    },
    "provenance": {
        "oracle_script": "benchmarks/axis-adequacy-subsumption-v1/oracle_axis_adequacy.py",
        "oracle_script_sha256": oracle_sha,
        "oracle_result_sha256": result_sha,
        "prior_oracle_sha256": prior_sha,
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "replay_count": 2,
        "canonical_result_sha256": result_sha,
        "runB_result_sha256": sha(runB),
        "byte_identical": canon == runB,
        "replay_method": ("independent CPython: re-derive the declared attack multiset from "
                          "benchmark-lock.v1.json raw bytes, recompute the shipped coverage "
                          "KPI under its own criterion (checked->declared) and under the "
                          "declared-corpus adequacy criterion (declared->checked), diagnose "
                          "the omission as a contiguous concatenation-block seam, search all "
                          "shipped module benchmark-locks and results for a compensating "
                          "axis-coverage KPI, and run a de-duplication counterfactual on the "
                          "lock digest"),
    },
    "remediation_note": diag["remediation_note"],
    "ceiling_note": diag["ceiling_note"],
    "zero_authority_claim_locks": diag["zero_authority_claim_locks"],
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
out = OUTDIR / "axis-adequacy-subsumption-v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("receipt_sha256", sha(out.read_bytes()))
print("two_replay_sha256", result_sha)
print("signature_verified", True)
print("sig_len", len(envelope["signatures"][0]["sig"]))
