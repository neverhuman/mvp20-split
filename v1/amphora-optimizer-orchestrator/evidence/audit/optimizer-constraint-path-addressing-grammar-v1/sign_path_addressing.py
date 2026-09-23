#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-optimizer-orchestrator
optimizer-constraint-path-addressing-grammar-v1 AUDIT_ONLY receipt.

AUDIT_ONLY: signs an audit receipt under evidence/audit/; does NOT sign a
phase0 evaluation/review, does NOT promote authority, does NOT flip
scientific_readiness, does NOT modify the portfolio manifest (66 receipts /
11 modules), module-manifest.json, any locked dataset, a signed Phase-0 KPI,
or the Rust runtime. Derived key_id cross-checked vs the pinned Phase-0
trust store."""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / ("amphora-optimizer-orchestrator/evidence/audit/"
                "optimizer-constraint-path-addressing-grammar-v1")
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

SIBLING_ORACLE_SHA = "a0da8ec147ed82bbdf0b58a56b157ba6a683cebe4cdddb2cc38f3d8f5d7d1774"


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def pae(payload_type, body):
    return (b"DSSEv1 " + str(len(payload_type)).encode() + b" "
            + payload_type.encode() + b" " + str(len(body)).encode() + b" " + body)


def load_seed(path):
    raw = path.read_bytes().strip()
    if len(raw) == 64:
        try:
            return bytes.fromhex(raw.decode())
        except ValueError:
            pass
    return raw[:32]


canon = (BENCH / "diagnostic.canonical.json").read_bytes()
runB = (BENCH / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)

files = {
    "path_addressing_corpus.v1.json": sha((BENCH / "path_addressing_corpus.v1.json").read_bytes()),
    "path_addressing_oracle.py": sha((BENCH / "path_addressing_oracle.py").read_bytes()),
    "build_path_corpus.py": sha((BENCH / "build_path_corpus.py").read_bytes()),
    "run_path_addressing.py": sha((BENCH / "run_path_addressing.py").read_bytes()),
    "optimizer_authorization_oracle.py": sha((BENCH / "optimizer_authorization_oracle.py").read_bytes()),
    "runtime_ground_truth.v1.jsonl": sha((BENCH / "runtime_ground_truth.v1.jsonl").read_bytes()),
    "runtime_probe/Cargo.toml": sha((BENCH / "runtime_probe/Cargo.toml").read_bytes()),
    "runtime_probe/Cargo.lock": sha((BENCH / "runtime_probe/Cargo.lock").read_bytes()),
    "runtime_probe/src/main.rs": sha((BENCH / "runtime_probe/src/main.rs").read_bytes()),
}
assert files["optimizer_authorization_oracle.py"] == SIBLING_ORACLE_SHA, (
    "sibling contract oracle sha diverged -- the three shipped optimizer "
    "receipts would no longer be reproducible from this tree!")
assert diag["gates"]["all_pass"], "study integrity gates did not all pass"
assert diag["provenance"]["runtime_ground_truth_sha256"] == files["runtime_ground_truth.v1.jsonl"]
assert diag["provenance"]["corpus_sha256"] == files["path_addressing_corpus.v1.json"]
assert diag["provenance"]["oracle_sha256"] == files["path_addressing_oracle.py"]
assert diag["provenance"]["runtime_anchor_sha256"] == sha(
    (ROOT / diag["provenance"]["runtime_anchor"]).read_bytes()), "runtime anchor moved"
assert diag["counts"]["site_a_cases"] == 7840

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"
trust = json.loads(TRUST.read_text())
by_role = {key.get("role"): key for key in trust["keys"]}
eval_pin = (eval_key_id == by_role.get("PHASE0_EVALUATOR", {}).get("key_id"))
rev_pin = (rev_key_id == by_role.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))

body_obj = {
    "schema": "amphora.optimizer-orchestrator.path-addressing-grammar-receipt.v1",
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
        "counts": diag["counts"],
        "H0a_injectivity": diag["findings"]["H0a_injectivity"],
        "H0b_addressability": {
            key: value for key, value in diag["findings"]["H0b_addressability"].items()
            if key != "per_fixture"},
        "H0b_coverage_by_fixture": {
            row["fixture_id"]: {
                "nodes_total": row["nodes_total"],
                "addressable_shipped": row["addressable_shipped"],
                "shipped_coverage": row["shipped_coverage"],
                "rfc6901_coverage": row["rfc6901_coverage"],
            } for row in diag["findings"]["H0b_addressability"]["per_fixture"]},
        "H0c_non_shadowing": diag["findings"]["H0c_non_shadowing"],
        "cross_site_grammar_divergence": {
            key: value
            for key, value in diag["findings"]["cross_site_grammar_divergence"].items()
            if key != "rows"},
        "mediation_completeness": {
            key: value
            for key, value in diag["findings"]["mediation_completeness"].items()
            if key != "rows"},
    },
    "rfc6901_repair": diag["rfc6901_repair"],
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
        "note": "Reviewer key referenced for provenance only; no independent "
                "human review performed.",
    },
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
payload_type = ("application/vnd.amphora."
                "optimizer-orchestrator-path-addressing-grammar+json")
signature = eval_sk.sign(pae(payload_type, body))
envelope = {
    "payload": base64.standard_b64encode(body).decode(),
    "payloadType": payload_type,
    "signatures": [{"keyid": eval_key_id,
                    "sig": base64.standard_b64encode(signature).decode()}],
}
receipt = {
    "evaluator_key_id": eval_key_id,
    "evaluator_public_key_hex": eval_pub_hex,
    "reviewer_public_key_hex": rev_pub_hex,
    "signature": envelope,
}
out = BENCH / "optimizer-constraint-path-addressing-grammar-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(payload_type, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("sibling_oracle_sha_unchanged",
      files["optimizer_authorization_oracle.py"] == SIBLING_ORACLE_SHA)
print("two_replay_sha256", diag_sha)
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
