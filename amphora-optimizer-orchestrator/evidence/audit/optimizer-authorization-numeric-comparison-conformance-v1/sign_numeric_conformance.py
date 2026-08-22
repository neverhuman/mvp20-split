#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-optimizer-orchestrator
optimizer-authorization-numeric-comparison-conformance-v1 AUDIT_ONLY receipt.

AUDIT_ONLY: signs an audit receipt under evidence/audit/; does NOT sign a
phase0 evaluation/review, does NOT promote authority, does NOT flip
scientific_readiness, does NOT modify the portfolio manifest (66 receipts /
11 modules), module-manifest.json, any locked dataset, or a signed Phase-0
KPI. Derived key_id cross-checked vs the pinned Phase-0 trust store."""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / ("amphora-optimizer-orchestrator/evidence/audit/"
                "optimizer-authorization-numeric-comparison-conformance-v1")
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

SIBLING_ORACLE_SHA = "a0da8ec147ed82bbdf0b58a56b157ba6a683cebe4cdddb2cc38f3d8f5d7d1774"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " +
            str(len(body)).encode() + b" " + body)


def load_seed(p):
    raw = p.read_bytes().strip()
    if len(raw) == 64:
        try:
            return bytes.fromhex(raw.decode())
        except Exception:
            pass
    return raw[:32]


canon = (BENCH / "diagnostic.canonical.json").read_bytes()
runB = (BENCH / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)

files = {
    "numeric_literals.v1.json": sha((BENCH / "numeric_literals.v1.json").read_bytes()),
    "numeric_comparison_oracle.py": sha((BENCH / "numeric_comparison_oracle.py").read_bytes()),
    "optimizer_authorization_oracle.py": sha((BENCH / "optimizer_authorization_oracle.py").read_bytes()),
    "run_numeric_conformance.py": sha((BENCH / "run_numeric_conformance.py").read_bytes()),
    "runtime_ground_truth.v1.jsonl": sha((BENCH / "runtime_ground_truth.v1.jsonl").read_bytes()),
    "runtime_probe/Cargo.toml": sha((BENCH / "runtime_probe/Cargo.toml").read_bytes()),
    "runtime_probe/Cargo.lock": sha((BENCH / "runtime_probe/Cargo.lock").read_bytes()),
    "runtime_probe/src/main.rs": sha((BENCH / "runtime_probe/src/main.rs").read_bytes()),
}
assert files["optimizer_authorization_oracle.py"] == SIBLING_ORACLE_SHA, (
    "sibling contract oracle sha diverged -- the two shipped optimizer receipts "
    "would no longer be reproducible from this tree!")
assert diag["gates"]["all_pass"], "study integrity gates did not all pass"
assert diag["provenance"]["runtime_ground_truth_sha256"] == files["runtime_ground_truth.v1.jsonl"]
assert diag["counts"]["total_cases"] == 7776

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
rev_pin = (rev_key_id == tbr.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))

body_obj = {
    "schema": "amphora.optimizer-orchestrator.numeric-comparison-conformance-receipt.v1",
    "study_id": diag["study_id"],
    "authority": "AUDIT_ONLY",
    "run_type": diag["run_type"],
    "module": "amphora-optimizer-orchestrator",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_module_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_rust_runtime": False,
    "purpose": diag["purpose"],
    "hypothesis": diag["hypothesis"],
    "non_circularity": diag["non_circularity"],
    "theory_reference": diag["theory_reference"],
    "method_lineage": diag["method_lineage"],
    "runtime_source_anchors": diag["runtime_source_anchors"],
    "preconditions": diag["preconditions"],
    "results": {
        "all_gates_passed": diag["gates"]["all_pass"],
        "findings": diag["findings"],
        "counts": diag["counts"],
        "reachability_table": diag["reachability_table"],
        "representation_orbit": diag["representation_orbit"],
        "ordering_divergence_vs_exact": diag["ordering_divergence_vs_exact"],
        "fail_open_vs_exact_semantics": diag["fail_open_vs_exact_semantics"],
        "fail_closed_vs_exact_semantics": diag["fail_closed_vs_exact_semantics"],
        "sibling_oracle_fidelity": diag["sibling_oracle_fidelity"],
        "distinct_runtime_reason_strings": diag["distinct_runtime_reason_strings"],
    },
    "gates": diag["gates"],
    "acceptance_bar_floors": diag["acceptance_bar_floors"],
    "proposed_hardeners": diag["proposed_hardeners"],
    "closes": diag["closes"],
    "does_not_close": diag["does_not_close"],
    "provenance": dict(diag["provenance"], artifact_sha256=files,
                       sibling_oracle_sha256_matches_shipped_receipts=True),
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "rust_probe_rebuilt_from_clean_target_between_replays": True,
        "runtime_ground_truth_sha256_stable_across_replays": True,
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under evidence/audit/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin),
    },
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER",
        "key_id": rev_key_id,
        "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin),
        "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed.",
    },
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = ("application/vnd.amphora."
         "optimizer-orchestrator-numeric-comparison-conformance+json")
sig = eval_sk.sign(pae(ptype, body))
envelope = {
    "payload": base64.standard_b64encode(body).decode(),
    "payloadType": ptype,
    "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}],
}
receipt = {
    "evaluator_key_id": eval_key_id,
    "evaluator_public_key_hex": eval_pub_hex,
    "reviewer_public_key_hex": rev_pub_hex,
    "signature": envelope,
}
out = BENCH / "optimizer-authorization-numeric-comparison-conformance-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("sibling_oracle_sha_unchanged", files["optimizer_authorization_oracle.py"] == SIBLING_ORACLE_SHA)
print("two_replay_sha256", diag_sha)
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
