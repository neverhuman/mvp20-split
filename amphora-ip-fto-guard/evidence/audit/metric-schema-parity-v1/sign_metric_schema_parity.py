#!/usr/bin/env python3
"""DSSE-Ed25519-sign the ip-fto-guard metric-schema-parity AUDIT_ONLY receipt.

Signs the byte-stable two-replay diagnostic with the on-host Phase-0 evaluator
Ed25519 seed. AUDIT_ONLY: produces a signed audit receipt under evidence/audit/,
does NOT sign a phase0 evaluation/review, does NOT promote authority, does NOT
modify the manifest (still 66 receipts / 11 modules), the pinned patent-landscape
fixture, mission.md, capability-profile.json, or any signed Phase-0 KPI. The
derived key_id is cross-checked against the pinned trust store as an integrity
assertion only.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-ip-fto-guard/evidence/audit/metric-schema-parity-v1"
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
harness_sha = sha((BENCH / "run_metric_schema_parity.py").read_bytes())

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

cA = diag["checkA_runtime_metric_key_extraction"]
cB = diag["checkB_repo_wide_occurrence_census"]
cC = diag["checkC_schema_and_doc_declaration"]
cD = diag["checkD_checked_kpi_test_coverage"]
cE = diag["checkE_signed_benchmark_artifact_scan"]
dt = diag["detector_self_test"]

# --- receipt body -----------------------------------------------------------
body_obj = {
    "schema": "amphora.ip-fto-guard.metric-schema-parity-receipt.v1",
    "study_id": diag["study_id"],
    "authority": "AUDIT_ONLY",
    "run_type": diag["run_type"],
    "module": "amphora-ip-fto-guard",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_pinned_fixture": False,
    "modifies_mission_or_capability_profile": False,
    "axis": diag["axis"],
    "claim_under_attack": diag["claim_under_attack"],
    "prior_receipts_this_module": diag["prior_receipts_this_module"],
    "theory_reference": diag["theory_reference"],
    "non_circularity": diag["non_circularity"],
    "results": {
        "lib_rs_sha256_now": cA["lib_rs_sha256_now"],
        "mission_md_pinned_lib_rs_sha256": cA["mission_md_pinned_lib_rs_sha256"],
        "lib_rs_hash_matches_mission_pin": cA["lib_rs_hash_matches_mission_pin"],
        "inserted_metric_keys_by_live_runtime": cA["inserted_metric_keys"],
        "inserted_gate_keys_by_live_runtime": cA["inserted_gate_keys"],
        "target_key_inserted_by_runtime": cA["target_key_inserted_by_runtime"],
        "rust_source_hit_count_repo_wide": cB["rust_source_hit_count"],
        "all_repo_hits_count": cB["all_repo_hits_count"],
        "schema_or_doc_declaration_hits": cB["schema_or_doc_declaration_hits"],
        "prior_audit_diagnostic_only_hits": cB["prior_audit_diagnostic_only_hits"],
        "declared_kpi0_value_path": cC["declared_kpi0_value_path"],
        "declared_kpi0_metric_class": cC["declared_kpi0_metric_class"],
        "declared_kpi0_promotion_phase": cC["declared_kpi0_promotion_phase"],
        "example_shows_target_key_present_as_null": cC["example_shows_target_key_present_as_null"],
        "mission_md_declares_primary_value_path": cC["mission_md_declares_primary_value_path"],
        "mission_md_quotes": cC["mission_md_quotes"],
        "metric_keys_asserted_by_checked_kpi_test": cD["metric_keys_asserted_by_checked_kpi_test"],
        "target_key_asserted_by_checked_kpi_test": cD["target_key_asserted_by_checked_kpi_test"],
        "benchmark_result_sha256": cE["benchmark_result_sha256"],
        "fixture_hash_matches_pin": cE["fixture_hash_matches_pin"],
        "target_key_present_anywhere_in_signed_benchmark_result": cE["target_key_present_anywhere_in_signed_benchmark_result"],
        "cargo_test_reproduced": cE["cargo_test_reproduced"],
        "cargo_test_outcome": cE["cargo_test_outcome"],
        "detector_self_test_catches_injected_key": dt["detector_catches_injected_key"],
    },
    "checkA_runtime_metric_key_extraction": cA,
    "checkB_repo_wide_occurrence_census": cB,
    "checkC_schema_and_doc_declaration": cC,
    "checkD_checked_kpi_test_coverage": cD,
    "checkE_signed_benchmark_artifact_scan": cE,
    "detector_self_test": dt,
    "finding": diag["headline"],
    "verdict": diag["verdict"],
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": sha(canon),
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "harness_sha256": harness_sha,
    },
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
ptype = "application/vnd.amphora.ip-fto-guard-metric-schema-parity+json"
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

out = BENCH / "metric-schema-parity-receipt.v1.dsse.json"
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
