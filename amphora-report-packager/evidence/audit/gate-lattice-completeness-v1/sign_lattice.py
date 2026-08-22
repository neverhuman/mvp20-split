#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-report-packager gate-lattice-completeness-v1
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
BENCH = ROOT / "amphora-report-packager/evidence/audit/gate-lattice-completeness-v1"
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
oracle_sha = sha((BENCH / "report_packager_lattice_oracle.py").read_bytes())
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
g0 = diag["g0_runtime_binding"]; g1 = diag["g1_unique_accept"]
g2 = diag["g2_gate_necessity"]; g3 = diag["g3_antitone_monotonicity"]
g4 = diag["g4_authority_non_escalation"]; g5 = diag["g5_tamper_fail_closed"]

body_obj = {
    "schema": "amphora.report-packager.gate-lattice-completeness-receipt.v1",
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
        "g0_runtime_binding": g["g0_runtime_binding"],
        "g0_librs_sha256": g0["librs_sha256"],
        "g0_gate_set_parity": g0["gate_set_parity"],
        "g0_structural_non_escalation_invariant": g0["structural_non_escalation_invariant"],
        "g0_authority_lock_present_insertions": g0["authority_lock_present_insertions"],
        "g0_shipped_all_false": g0["shipped_all_false"],
        "g0_mission_pinned_librs_sha256": g0["mission_pinned_librs_sha256"],
        "g0_stale_mission_anchor_detected": g0["stale_mission_anchor_detected"],
        "g1_unique_accept": g["g1_unique_accept"],
        "g1_config_space": g1["config_space"],
        "g1_accepting_configs": g1["accepting_configs"],
        "g1_rejecting_configs": g1["rejecting_configs"],
        "g1_runtime_parity_reject": g1["runtime_parity_reject"],
        "g2_gate_necessity": g["g2_gate_necessity"],
        "g2_necessary_count": g2["necessary_count"],
        "g2_conjunction_minimal_irredundant": g2["conjunction_minimal_irredundant"],
        "g3_antitone_monotonicity": g["g3_antitone_monotonicity"],
        "g3_ordered_pairs_checked": g3["ordered_pairs_checked"],
        "g3_monotonicity_violations": g3["monotonicity_violations"],
        "g4_authority_non_escalation": g["g4_authority_non_escalation"],
        "g4_pairs_checked": g4["pairs_checked"],
        "g4_meet_is_glb": g4["meet_is_glb"],
        "g4_meet_non_escalating": g4["meet_non_escalating"],
        "g4_join_counter_model_escalates": g4["join_counter_model_escalates"],
        "g5_tamper_fail_closed": g["g5_tamper_fail_closed"],
        "g5_probe_count": g5["probe_count"],
        "g5_all_mutants_caught": g5["all_mutants_caught"],
    },
    "gates": g,
    "closes": diag["closes"], "does_not_close": diag["does_not_close"],
    "provenance": {
        "module_manifest_sha256": manifest_sha,
        "oracle_sha256": oracle_sha,
        "librs_sha256": g0["librs_sha256"],
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
ptype = "application/vnd.amphora.report-packager-gate-lattice-completeness+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
out = BENCH / "gate-lattice-completeness-receipt.v1.dsse.json"
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
