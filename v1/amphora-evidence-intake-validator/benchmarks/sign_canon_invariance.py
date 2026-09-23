#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-evidence-intake-validator
canonicalization-invariance-tamper-completeness-v1 AUDIT_ONLY receipt.
Signs under evidence/audit/; does NOT promote authority, flip scientific_readiness
(stays NOT_APPLICABLE), or modify the portfolio manifest (66 receipts/11 modules),
any locked dataset, the Phase-0 KPI, or the benchmark-lock."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-evidence-intake-validator"
EV = MOD / "evidence/audit/canonicalization-invariance-tamper-v1"
BM = MOD / "benchmarks"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"
BLOCK = MOD / "evidence/phase0/benchmark/benchmark-lock.v1.json"
SHIPPED_RESULT = MOD / "evidence/phase0/benchmark/result.v1.json"
PRIOR_ORACLE = MOD / "evidence/audit/host-receipt-oracle-parity-v1/eiv_oracle.py"
PRIOR_PRED = MOD / "evidence/audit/predicate-completeness-v1/predicate-completeness-receipt.v1.dsse.json"

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

harness_sha = sha((BM / "run_canon_invariance.py").read_bytes())
prior_oracle_sha = sha(PRIOR_ORACLE.read_bytes())
prior_pred_sha = sha(PRIOR_PRED.read_bytes())
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

body_obj = {
    "schema": "amphora.evidence-intake-validator.canonicalization-invariance-tamper-receipt.v1",
    "receipt_id": "canonicalization-invariance-tamper-v1",
    "module_id": "amphora-evidence-intake-validator",
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "EVIDENCE_ONLY",
    "phase": "PRE_PHASE_0",
    "scientific_success_required_for_phase0": False,
    "date": diag.get("date", "2026-07-30"),
    "generated_on_host": "xbabe2",
    "promotes_authority": False, "flips_scientific_readiness": False,
    "human_review_performed": False, "organizational_independence_asserted": False,
    "modifies_manifest": False, "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False, "modifies_benchmark_lock": False,
    "claim": (
        "Byte-binding integrity certificate for the evidence-intake acceptance "
        "predicate. An independent CPython re-derivation of the amphora-core "
        "canonicalize+stable_hash and host_receipt_valid shows that package_sha256 "
        "is (G1) a canonicalization-INVARIANT binding -- across 42 JCS-equivalent "
        "re-encodings (key-order permutation at every nesting depth, source "
        "whitespace, unicode \\uXXXX-vs-literal escape form, compact-vs-spaced "
        "separators) over a 6-package epoxy-amine coating evidence corpus, "
        "package_sha256 is byte-identical and the ACCEPT decision is preserved, so "
        "reorder/reformat cannot evade the front door -- and (G2) a tamper-COMPLETE "
        "binding -- all 97 single-atom semantic mutations (numeric delta incl. "
        "1e-9 epsilon, int<->float type flip, number->string, string char flip, "
        "top/nested key rename, field add, field remove) change package_sha256 with "
        "ZERO silent collisions and ZERO silent accepts, each flipping the runtime "
        "decision ACCEPT->FAILED_GATES because the frozen receipt's package_sha256 "
        "and candidate_contract_hash_v1 no longer match the recomputed bytes -- with "
        "(G3) SHA-256 avalanche mean bit-flip fraction 0.507 (min 0.414) confirming "
        "diffusion is not marginal. The 3 shipped positive package_sha256 anchors are "
        "reproduced byte-exact (G0), tying the certificate to the actually-shipped "
        "canonical hashing. Canonicalization is nominal/type-exact, NOT "
        "numeric-normalizing: int 110, float 110.0 and string '110' are DISTINCT "
        "bindings (exercised as detected changes), matching shipped Rust semantics."),
    "theory": diag["theory"],
    "live_authority_under_test": diag["live_authority_under_test"],
    "corpus": diag["corpus"],
    "results": {
        "all_gates_passed": diag["all_gates_passed"],
        "n_packages": diag["counts"]["n_packages"],
        "g0_shipped_anchors_reproduced": diag["g0_shipped_anchor_reproduction"]["pass"],
        "g1_total_encodings_checked": diag["g1_canonicalization_invariance"]["total_encodings_checked"],
        "g1_invariance_disagreements": diag["g1_canonicalization_invariance"]["disagreements"],
        "g2_total_mutations": diag["g2_tamper_completeness"]["total_mutations"],
        "g2_hash_collisions": diag["g2_tamper_completeness"]["hash_collisions"],
        "g2_silent_accepts": diag["g2_tamper_completeness"]["silent_accepts"],
        "g3_mean_bitflip_fraction": diag["g3_avalanche"]["mean_bitflip_fraction"],
        "g3_min_bitflip_fraction": diag["g3_avalanche"]["min_bitflip_fraction"],
        "total_decisions_evaluated": diag["counts"]["total_decisions_evaluated"],
    },
    "gates": diag["gates"],
    "scope_note": diag["scope_note"],
    "closes": diag["closes"],
    "does_not_establish": diag["does_not_establish"],
    "provenance": {
        "harness_sha256": {"run_canon_invariance.py": harness_sha},
        "shipped_result_v1_sha256": shipped_result_sha,
        "benchmark_lock_sha256": benchmark_lock_sha,
        "reused_prior_artifacts_sha256": {
            "host-receipt-oracle-parity-v1/eiv_oracle.py": prior_oracle_sha,
            "predicate-completeness-v1/predicate-completeness-receipt.v1.dsse.json": prior_pred_sha},
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "replay_method": "independent re-derivation: re-implement amphora-core "
                         "canonicalize+stable_hash, reproduce 3 shipped package "
                         "anchors byte-exact, enumerate 42 JCS-equivalent re-encodings "
                         "for invariance and 97 single-atom semantic mutations for "
                         "tamper-completeness + SHA-256 avalanche bit-flip statistics",
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
ptype = "application/vnd.amphora.evidence-intake-canonicalization-invariance-tamper+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
out = EV / "canonicalization-invariance-tamper-receipt.v1.dsse.json"
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
