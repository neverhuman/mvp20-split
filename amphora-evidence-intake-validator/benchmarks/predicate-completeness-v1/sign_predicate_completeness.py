#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-evidence-intake-validator predicate-completeness-v1
AUDIT_ONLY receipt. Signs an audit receipt under evidence/audit/; does NOT sign a
phase0 evaluation/review, does NOT promote authority, does NOT flip
scientific_readiness (stays NOT_APPLICABLE), does NOT modify the portfolio manifest
(66 receipts / 11 modules), any locked dataset, the Phase-0 KPI, or the benchmark-lock.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-evidence-intake-validator"
EV = MOD / "evidence/audit/predicate-completeness-v1"
BM = MOD / "benchmarks/predicate-completeness-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"
BLOCK = MOD / "evidence/phase0/benchmark/benchmark-lock.v1.json"
SHIPPED_RESULT = MOD / "evidence/phase0/benchmark/result.v1.json"
PRIOR = MOD / "evidence/audit/host-receipt-oracle-parity-v1/eiv_oracle.py"


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
assert diag["all_gates_passed"] is True, "gates not all passed"

harness_sha = sha((BM / "run_predicate_completeness.py").read_bytes())
prior_oracle_sha = sha(PRIOR.read_bytes())
benchmark_lock_sha = sha(BLOCK.read_bytes())
shipped_result_sha = sha(SHIPPED_RESULT.read_bytes())

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

g1 = diag["g1_truth_table_completeness"]
body_obj = {
    "schema": "amphora.evidence-intake-validator.predicate-completeness-receipt.v1",
    "receipt_id": "predicate-completeness-v1",
    "module_id": "amphora-evidence-intake-validator",
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "EVIDENCE_ONLY",
    "phase": "PRE_PHASE_0",
    "scientific_success_required_for_phase0": False,
    "date": diag.get("date", "2026-07-28"),
    "generated_on_host": "xbabe2",
    "promotes_authority": False, "flips_scientific_readiness": False,
    "human_review_performed": False, "organizational_independence_asserted": False,
    "modifies_manifest": False, "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False, "modifies_benchmark_lock": False,
    "claim": (
        "Exhaustive boolean-completeness certificate for the evidence-intake "
        "acceptance predicate. An independent CPython re-derivation of "
        "host_receipt_valid enumerates the FULL 2^11 = 2048 truth table over the 11 "
        "independently value-flippable receipt clauses and shows the predicate accepts "
        "on exactly ONE row (all clauses in their passing state) and rejects on all "
        "2047 other rows -- i.e. acceptance is exactly the conjunction of its clauses, "
        "with zero accepting gap combinations. Every one of the 11 value-clauses plus "
        "the 11-field cardinality guard and the dict-type guard is independently "
        "load-bearing (each single-clause failure flips accept->reject), and the "
        "predicate is antitone (acceptance occurs only at violation-count 0). The 3 "
        "shipped positive-scenario package_sha256 anchors are reproduced byte-exact, "
        "tying the certificate to the actually-shipped canonical-JSON hashing."),
    "theory": diag["theory"],
    "live_authority_under_test": diag["live_authority_under_test"],
    "results": {
        "all_gates_passed": diag["all_gates_passed"],
        "k_value_clauses": g1["k_value_clauses"],
        "truth_table_rows_enumerated": g1["n_assignments_enumerated"],
        "n_accepting_rows": g1["n_accepting_rows"],
        "unique_accepting_row_is_all_pass": g1["unique_accepting_row_is_all_pass"],
        "accept_iff_conjunction_for_every_row": g1["accept_iff_conjunction_for_every_row"],
        "clauses_independently_necessary":
            all(x["single_failure_rejects"] for x in diag["g2_clause_minimality"]["records"]),
        "structural_clauses_load_bearing": diag["g3_structural_clauses"],
        "total_independent_conjuncts": diag["clause_inventory"]["total_independent_conjuncts"],
        "total_decisions_evaluated": diag["counts"]["total_decisions_evaluated"],
    },
    "gates": diag["gates"],
    "clause_inventory": diag["clause_inventory"],
    "closes": diag["closes"],
    "does_not_establish": diag["does_not_establish"],
    "provenance": {
        "harness_sha256": {"run_predicate_completeness.py": harness_sha},
        "shipped_result_v1_sha256": shipped_result_sha,
        "benchmark_lock_sha256": benchmark_lock_sha,
        "reused_prior_oracle_sha256": {
            "host-receipt-oracle-parity-v1/eiv_oracle.py": prior_oracle_sha},
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "replay_method": "independent full enumeration: re-derive canonical-JSON "
                         "stable_hash, reproduce shipped package anchors, enumerate "
                         "the complete 2^11 clause-value lattice, single-clause "
                         "minimality flips, structural cardinality/type guards, and "
                         "the antitone violation-count ordering",
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
ptype = "application/vnd.amphora.evidence-intake-predicate-completeness+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
out = EV / "predicate-completeness-receipt.v1.dsse.json"
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
print("signature_verified", True)
