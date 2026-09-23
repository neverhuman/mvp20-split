#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-molecule-generator generation-quality +
feasibility metric baseline AUDIT_ONLY receipt.

Signs the byte-stable two-replay diagnostic with the on-host Phase-0 evaluator
Ed25519 seed. AUDIT_ONLY: produces a signed audit receipt under evidence/audit/;
does NOT sign a phase0 evaluation/review, does NOT promote authority, does NOT
flip scientific_readiness (stays UNVALIDATED), does NOT modify the manifest
(66 receipts / 11 modules), the locked PI1M dataset, or any signed Phase-0 KPI.
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
BENCH = ROOT / "amphora-molecule-generator/evidence/audit/molgen-quality-feasibility-baseline-v1"
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


# --- two-replay gate --------------------------------------------------------
canon = (BENCH / "diagnostic.canonical.json").read_bytes()
runB = (BENCH / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)
harness_sha = sha((BENCH / "run_molgen_quality.py").read_bytes())

# --- derive keys ------------------------------------------------------------
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

sa = diag["sa_feasibility_known_answer"]
demo = diag["deterministic_inscope_proposal_demo"]
ref = diag["pi1m_reference_characterization"]
hyp = diag["hypothesis_evaluation"]

body_obj = {
    "schema": "amphora.molecule-generator.molgen-quality-feasibility-baseline-receipt.v1",
    "study_id": diag["study_id"],
    "authority": "AUDIT_ONLY",
    "run_type": "GENERATION_QUALITY_FEASIBILITY_BASELINE",
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
        "sa_instrument_median_abs_delta": sa["median_abs_delta_vs_shipped"],
        "sa_instrument_known_answer_pass": sa["pass"],
        "sa_instrument_residual_divergent_rows": sa["n_divergent"],
        "sa_instrument_residual_delta_range": [sa["divergent_delta_min"], sa["divergent_delta_max"]],
        "pi1m_prefix_validity_fraction": ref["validity_fraction"],
        "pi1m_prefix_canonical_uniqueness_fraction": ref["canonical_uniqueness_fraction_prefix"],
        "pi1m_full_canonical_uniqueness_fraction": ref["full_corpus_canonical_uniqueness_fraction_manifest"],
        "inscope_validity": demo["validity"],
        "inscope_uniqueness": demo["uniqueness"],
        "inscope_novelty_vs_pi1m_prefix_structural": demo["novelty_vs_pi1m_prefix_structural"],
        "inscope_sa_range": [demo["sa_min"], demo["sa_max"]],
        "inscope_all_feasible_sa_below_6": demo["all_proposals_feasible"],
        "fail_closed_all_caught": diag["fail_closed_all_caught"],
        "hypothesis_verdict": hyp["verdict"],
        "locked_runtime_yield": hyp["locked_runtime_valid_unique_proposal_yield"],
        "deterministic_generator_valid_unique_feasible_yield":
            hyp["deterministic_generator_valid_unique_feasible_yield"],
    },
    "hypothesis_evaluation": hyp,
    "fail_closed_mutation_demo": diag["fail_closed_mutation_demo"],
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
ptype = "application/vnd.amphora.molecule-generator-molgen-quality-feasibility+json"
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
out = BENCH / "molgen-quality-feasibility-baseline-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

# self-verify
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
