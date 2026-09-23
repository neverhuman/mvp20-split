#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-molecule-generator deterministic-grammar
yield study AUDIT_ONLY receipt.

AUDIT_ONLY: signs an audit receipt under evidence/audit/; does NOT sign a
phase0 evaluation/review, does NOT promote authority, does NOT flip
scientific_readiness (stays UNVALIDATED), does NOT modify the manifest (66
receipts / 11 modules), the locked PI1M dataset, or any signed Phase-0 KPI.
The derived key_id is cross-checked against the pinned trust store as an
integrity assertion only.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-molecule-generator/evidence/audit/molgen-deterministic-grammar-yield-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" "
            + str(len(body)).encode() + b" " + body)


def load_seed(path):
    raw = path.read_bytes().strip()
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
harness_sha = sha((BENCH / "run_molgen_grammar.py").read_bytes())

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"

trust = json.loads(TRUST.read_text())
trust_by_role = {k.get("role"): k for k in trust["keys"]}
eval_derives_pin = (eval_key_id == trust_by_role.get("PHASE0_EVALUATOR", {}).get("key_id"))
rev_derives_pin = (rev_key_id == trust_by_role.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))

gg = diag["generator_grammar"]
sa = diag["sa_feasibility_known_answer"]
hyp = diag["hypothesis_evaluation"]

body_obj = {
    "schema": "amphora.molecule-generator.molgen-deterministic-grammar-yield-receipt.v1",
    "study_id": diag["study_id"],
    "authority": "AUDIT_ONLY",
    "run_type": "DETERMINISTIC_GENERATOR_GRAMMAR_YIELD",
    "module": "amphora-molecule-generator",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "claim": diag["headline"],
    "purpose": diag["purpose"],
    "non_circularity": diag["non_circularity"],
    "theory_reference": diag["theory_reference"],
    "rdkit_version": diag["rdkit_version"],
    "hash_and_count_lock": diag["hash_and_count_lock"],
    "results": {
        "metric_self_tests_all_pass": diag["metric_self_tests_all_pass"],
        "sa_instrument_exact_reproduction_fraction": sa["exact_reproduction_fraction"],
        "sa_instrument_known_answer_pass": sa["pass"],
        "sa_instrument_max_abs_delta": sa["max_abs_delta_vs_shipped"],
        "grammar_families": gg["families"],
        "grammar_productions_emitted": gg["productions_emitted"],
        "grammar_validity_fraction": gg["validity_fraction"],
        "grammar_uniqueness_fraction": gg["uniqueness_fraction"],
        "difunctional_hardener_universe": gg["difunctional_hardener_universe"],
        "valid_unique_difunctional_feasible_yield": gg["valid_unique_difunctional_feasible_yield"],
        "novel_vs_prior_curated_seed": gg["novel_vs_prior_curated_seed"],
        "feasible_fraction_over_hardeners": gg["feasible_fraction_over_hardeners"],
        "feasible_fraction_bootstrap95_ci": gg["feasible_fraction_bootstrap95_ci"],
        "sa_median_over_hardeners": gg["sa_median_over_hardeners"],
        "sa_median_bootstrap95_ci": gg["sa_median_bootstrap95_ci"],
        "sa_range": [gg["sa_min"], gg["sa_max"]],
        "bootstrap_seed": gg["bootstrap_seed"],
        "bootstrap_resamples": gg["bootstrap_resamples"],
        "fail_closed_decoys_all_rejected": diag["fail_closed_decoy_demo"]["all_rejected"],
        "fail_closed_n_decoys": diag["fail_closed_decoy_demo"]["n_decoys"],
        "hypothesis_verdict": hyp["verdict"],
        "locked_runtime_yield": hyp["locked_runtime_valid_unique_proposal_yield"],
    },
    "hypothesis_evaluation": hyp,
    "rights_posture": diag["rights_posture"],
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "harness_sha256": harness_sha,
    },
    "closes": diag["closes"],
    "does_not_close": diag["does_not_close"],
    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under evidence/audit/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_derives_pin),
    },
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER",
        "key_id": rev_key_id,
        "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_derives_pin),
        "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed.",
    },
}

body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.molecule-generator-molgen-grammar-yield+json"
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
out = BENCH / "molgen-deterministic-grammar-yield-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

pk = Ed25519PublicKey.from_public_bytes(eval_pub)
pk.verify(base64.standard_b64decode(envelope["signatures"][0]["sig"]),
          pae(ptype, base64.standard_b64decode(envelope["payload"])))

print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_derives_pin)
print("reviewer_derives_pinned_trust_key", rev_derives_pin)
print("receipt_body_sha256", sha(body))
print("envelope_sha256", sha(out.read_bytes()))
print("two_replay_sha256", diag_sha)
print("signature_verified", True)
