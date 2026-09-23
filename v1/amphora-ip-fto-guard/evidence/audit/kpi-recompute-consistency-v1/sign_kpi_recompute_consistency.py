#!/usr/bin/env python3
"""DSSE-Ed25519-sign the ip-fto-guard kpi-recompute-consistency AUDIT_ONLY receipt.

AUDIT_ONLY: produces a signed audit receipt under evidence/audit/. Does NOT
sign a phase0 evaluation/review, does NOT promote authority, does NOT modify
the manifest, the pinned patent-landscape fixture, or any signed Phase-0 KPI.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-ip-fto-guard/evidence/audit/kpi-recompute-consistency-v1"
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
harness_sha = sha((BENCH / "run_kpi_recompute_consistency.py").read_bytes())

# --- derive public keys / key_ids from on-host seeds ------------------------
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

# --- receipt body -----------------------------------------------------------
body_obj = {
    "schema": "amphora.ip-fto-guard.kpi-recompute-consistency-receipt.v1",
    "study_id": diag["study_id"],
    "authority": "AUDIT_ONLY",
    "run_type": "KPI_RECOMPUTE_CONSISTENCY_AUDIT",
    "module": "amphora-ip-fto-guard",
    "campaign_item_id": "",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_pinned_fixture": False,
    "claim_under_attack": (
        "The module's 3 standing signed audit receipts (landscape-integrity-v1, "
        "all-elements-rule-v1, cpc-coverage-v1) faithfully reconstruct the SAME "
        "metric (metrics.unresolved_technical_categories) that mission.md "
        "declares to be the module's primary value path and that the live "
        "checked Rust runtime (post-R-B01-repair) actually populates."
    ),
    "claim": diag["headline"],
    "purpose": diag["purpose"],
    "non_circularity": diag["non_circularity"],
    "theory_reference": diag["theory_reference"],
    "inputs": diag["inputs"],
    "hash_and_count_lock": diag["hash_and_count_lock"],
    "recomputation": diag["recomputation"],
    "live_runtime_probe": diag["live_runtime_probe"],
    "standing_audit_receipts": diag["standing_audit_receipts"],
    "standing_claims_asserting_the_metric": diag["standing_claims_asserting_the_metric"],
    "standing_claims_agree_with_each_other": diag["standing_claims_agree_with_each_other"],
    "fixture_sha_matches_all_standing_claims": diag["fixture_sha_matches_all_standing_claims"],
    "standing_receipts_absent_from_retraction_index": diag["standing_receipts_absent_from_retraction_index"],
    "consistency_checks": diag["consistency_checks"],
    "fail_closed_mutation_demo": diag["fail_closed_mutation_demo"],
    "results": {
        "H0": diag["H0"],
        "H0_verdict": diag["H0_verdict"],
        "live_runtime_value": diag["live_runtime_probe"]["single_stable_value"],
        "standing_claims_values": sorted(set(diag["standing_claims_asserting_the_metric"].values())),
        "live_matches_standing_audit_claims": diag["consistency_checks"]["live_matches_standing_audit_claims"],
        "all_mutations_caught": diag["fail_closed_mutation_demo"]["all_mutations_caught"],
    },
    "does_not_close": diag["does_not_close"],
    "proposed_followups": diag["proposed_followups"],
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": sha(canon),
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "harness_sha256": harness_sha,
        "probe_main_rs_sha256": diag["inputs"]["probe_main_rs_sha256"],
        "probe_two_replay_byte_identical": diag["live_runtime_probe"]["two_replay_byte_identical"],
    },
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
ptype = "application/vnd.amphora.ip-fto-guard-kpi-recompute-consistency+json"
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

out = BENCH / "kpi-recompute-consistency-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

# --- self-verify ------------------------------------------------------------
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
print("H0_verdict", body_obj["results"]["H0_verdict"])
