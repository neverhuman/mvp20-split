#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-report-packager banned-claim-lint-parity-v1
AUDIT_ONLY receipt. AUDIT_ONLY: signs an audit receipt under evidence/audit/;
does NOT sign a phase0 evaluation/review, does NOT promote authority, does NOT
flip scientific_readiness, does NOT modify the portfolio manifest (66 receipts
/ 11 modules), the module-manifest.json, any locked dataset, or a signed
Phase-0 KPI. Derived key_id cross-checked vs pinned trust store."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-report-packager/evidence/audit/banned-claim-lint-parity-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

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

canon = (BENCH / "diagnostic.canonical.json").read_bytes()
runB = (BENCH / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)
oracle_sha = sha((BENCH / "report_packager_oracle.py").read_bytes())
manifest_sha = sha((ROOT / "module-manifest.json").read_bytes())

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

g = diag["gates"]
g0 = diag["g0_anchor_parity"]; g1 = diag["g1_runtime_decision_parity"]
g2 = diag["g2_banned_claim_lint"]; g3 = diag["g3_tamper_fail_closed"]

body_obj = {
    "schema": "amphora.report-packager.banned-claim-lint-parity-receipt.v1",
    "study_id": diag["study_id"],
    "authority": "AUDIT_ONLY",
    "run_type": diag["run_type"],
    "module": "amphora-report-packager",
    "promotes_authority": False, "flips_scientific_readiness": False,
    "human_review_performed": False, "organizational_independence_asserted": False,
    "modifies_manifest": False, "modifies_module_manifest": False,
    "modifies_locked_dataset": False, "modifies_signed_phase0_kpi": False,
    "claim": diag["closes"], "purpose": diag["purpose"],
    "hypothesis": diag["hypothesis"],
    "non_circularity": diag["non_circularity"],
    "theory_reference": diag["theory_reference"],
    "runtime_source_anchors": diag["runtime_source_anchors"],
    "results": {
        "all_gates_passed": g["all_pass"],
        "g0_anchor_parity": g["g0_anchor_parity"],
        "g0_all_artifacts_byte_exact": g0["all_artifacts_byte_exact"],
        "g0_benchmark_result_byte_exact": g0["benchmark_result_byte_exact"],
        "g0_diagnostic_sha256_reproduced": g0["diagnostic_sha256_reproduced_via_stable_hash"],
        "g1_runtime_decision_parity": g["g1_runtime_decision_parity"],
        "g1_records_checked": g1["records_checked"],
        "g1_generated_document_count": g1["generated_document_count"],
        "g2_banned_claim_lint": g["g2_banned_claim_lint"],
        "g2_total_affirmative_overclaims": g2["total_affirmative_overclaims"],
        "g2_total_disclaimed_occurrences": g2["total_disclaimed_occurrences"],
        "g2_all_deliverables_carry_authority_lock_banner": g2["all_deliverables_carry_authority_lock_banner"],
        "g2_positive_control_flags": g2["positive_control_affirmative_flags"],
        "g2_negative_control_flags": g2["negative_control_affirmative_flags"],
        "g2_controls_validated": g2["controls_validated"],
        "g3_tamper_fail_closed": g["g3_tamper_fail_closed"],
        "g3_probe_count": g3["probe_count"],
        "g3_all_probes_fail_closed": g3["pass"],
    },
    "gates": g,
    "closes": diag["closes"], "does_not_close": diag["does_not_close"],
    "provenance": {
        "module_manifest_sha256": manifest_sha,
        "oracle_sha256": oracle_sha,
        "benchmark_result_sha256": g0["benchmark_result_reproduced_sha256"],
        "artifact_sha256": {k: v["reproduced_sha256"] for k, v in g0["artifact_parity"].items()},
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "oracle_sha256": oracle_sha,
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
ptype = "application/vnd.amphora.report-packager-banned-claim-lint-parity+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
out = BENCH / "banned-claim-lint-parity-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("all_gates_passed", g["all_pass"])
print("two_replay_sha256", diag_sha)
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
