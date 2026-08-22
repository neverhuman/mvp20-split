#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-report-packager render-claim-lock-preservation-v1
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
BENCH = ROOT / "amphora-report-packager/evidence/audit/render-claim-lock-preservation-v1"
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
oracle_sha = sha((BENCH / "report_packager_preservation_oracle.py").read_bytes())
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
g0 = diag["g0_packaging_map_parity"]
g1 = diag["g1_lock_projection_completeness"]
g2 = diag["g2_lattice_injectivity"]
g3 = diag["g3_escalation_tamper_battery"]
g4 = diag["g4_trust_anchor_adequacy"]

body_obj = {
    "schema": "amphora.report-packager.render-claim-lock-preservation-receipt.v1",
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
    "verdict": diag["verdict"],
    "non_circularity": diag["non_circularity"],
    "theory_reference": diag["theory_reference"],
    "runtime_source_anchors": diag["runtime_source_anchors"],
    "results": {
        "all_gates_passed": g["all_pass"],
        # G0 packaging-map parity / noninterference
        "g0_packaging_map_parity": g["g0_packaging_map_parity"],
        "g0_render_parity_byte_exact": g0["render_parity_byte_exact"],
        "g0_render_sha256": g0["render_sha256"],
        "g0_manifest_binds_render": g0["manifest_binds_render"],
        "g0_score_envelope_hash_parity": g0["score_envelope_hash_parity"],
        "g0_key_id_derivation_parity": g0["key_id_derivation_parity"],
        "g0_fixture_signature_verifies": g0["fixture_signature_verifies"],
        "g0_shipped_fixture_accepted": g0["shipped_fixture_accepted"],
        "g0_clause_count": g0["clause_count"],
        "g0_backtick_token_count": g0["backtick_token_count"],
        "g0_backtick_tokens_foreign_to_payload": g0["backtick_tokens_foreign_to_payload"],
        "g0_render_alphabet_closed": g0["render_alphabet_closed"],
        "g0_rendered_document_passes_banned_claim_lint": g0["rendered_document_passes_banned_claim_lint"],
        "g0_payload_json_number_count": g0["payload_json_number_count"],
        "g0_fixture_sha256": g0["fixture_sha256"],
        "g0_stale_mission_anchor_detected": g0["stale_mission_anchor_detected"],
        "g0_mission_pinned_librs_sha256": g0["mission_pinned_librs_sha256"],
        "g0_librs_sha256": g0["librs_sha256"],
        # G1 lock-projection completeness
        "g1_lock_projection_completeness": g["g1_lock_projection_completeness"],
        "g1_declared_lock_count": g1["declared_lock_count"],
        "g1_lock_set_parity_with_primary_constant": g1["lock_set_parity_with_primary_constant"],
        "g1_all_shipped_locks_true": g1["all_shipped_locks_true"],
        "g1_locks_checked": g1["locks_checked"],
        "g1_conditions_checked": g1["conditions_checked"],
        "g1_conditions_passed": g1["conditions_passed"],
        "g1_rendered_exactly_once_count": g1["rendered_exactly_once_count"],
        "g1_deletion_rejected_count": g1["deletion_rejected_count"],
        "g1_runtime_probe_coverage": g1["runtime_probe_coverage"],
        # G2 injectivity on the claim-lock lattice
        "g2_lattice_injectivity": g["g2_lattice_injectivity"],
        "g2_config_space": g2["config_space"],
        "g2_distinct_documents": g2["distinct_documents"],
        "g2_distinct_document_sha256": g2["distinct_document_sha256"],
        "g2_digest_collisions": g2["digest_collisions"],
        "g2_injective_on_lock_lattice": g2["injective_on_lock_lattice"],
        "g2_roundtrip_exact_count": g2["roundtrip_exact_count"],
        "g2_accepting_configs": g2["accepting_configs"],
        "g2_rejecting_configs": g2["rejecting_configs"],
        "g2_unique_accept_all_locks_true": g2["unique_accept_all_locks_true"],
        "g2_key_orderings_tested": g2["key_orderings_tested"],
        "g2_representation_invariant_over_key_order": g2["representation_invariant_over_key_order"],
        # G3 escalation / tamper battery
        "g3_escalation_tamper_battery": g["g3_escalation_tamper_battery"],
        "g3_mutants_tested": g3["mutants_tested"],
        "g3_mutants_rejected": g3["mutants_rejected"],
        "g3_all_mutants_fail_closed": g3["all_mutants_fail_closed"],
        "g3_lock_strip_mutants": g3["lock_strip_mutants"],
        "g3_lock_strip_all_rejected": g3["lock_strip_all_rejected"],
        "g3_escalation_mutants": g3["escalation_mutants"],
        "g3_escalation_all_rejected": g3["escalation_all_rejected"],
        "g3_clauses_with_at_least_one_kill": g3["clauses_with_at_least_one_kill"],
        "g3_clauses_strictly_necessary": g3["clauses_strictly_necessary"],
        # G4 trust-anchor adequacy (adversarial result)
        "g4_trust_anchor_adequacy": g["g4_trust_anchor_adequacy"],
        "g4_adversaries_tested": g4["adversaries_tested"],
        "g4_adversaries_rejected": g4["adversaries_rejected"],
        "g4_all_adversaries_fail_closed": g4["all_adversaries_fail_closed"],
        "g4_lock_adversary_defense_count": g4["lock_adversary_defense_count"],
        "g4_lock_adversary_surviving_defenses": g4["lock_adversary_surviving_defenses"],
        "g4_lock_adversary_crypto_layer_satisfied": g4["lock_adversary_crypto_layer_satisfied"],
        "g4_lock_adversary_hash_bindings_satisfied": g4["lock_adversary_hash_bindings_satisfied"],
        "g4_single_point_of_defense_clause": g4["single_point_of_defense_clause"],
        "g4_ablating_that_clause_admits_lock_stripped_package": g4["ablating_that_clause_admits_lock_stripped_package"],
        "g4_fixture_signing_key_id": g4["fixture_signing_key_id"],
        "g4_fixture_signing_key_pinned_in_trust_store": g4["fixture_signing_key_pinned_in_trust_store"],
        "g4_signature_provides": g4["signature_provides"],
        "g4_trust_store_roles": g4["trust_store_roles"],
        "g4_trust_store_sha256": g4["trust_store_sha256"],
        "g4_finding": g4["finding"],
    },
    "gates": g,
    "closes": diag["closes"], "does_not_close": diag["does_not_close"],
    "provenance": {
        "module_manifest_sha256": manifest_sha,
        "oracle_sha256": oracle_sha,
        "fixture_sha256": g0["fixture_sha256"],
        "diagnostics_rs_sha256": g0["diagnostics_rs_sha256"],
        "core_rs_sha256": g0["core_rs_sha256"],
        "phase0_rs_sha256": g0["phase0_rs_sha256"],
        "librs_sha256": g0["librs_sha256"],
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "oracle_sha256": oracle_sha,
        "adversary_key_seed_sha256": g4["adversary_seed_sha256"],
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
    "prior_receipts_in_module": [
        "amphora-report-packager-banned-claim-lint-parity-v1 (claim TEXT lint)",
        "amphora-report-packager-gate-lattice-completeness-v1 (release DECISION function algebra)",
    ],
    "distinct_axis": (
        "This receipt is the PACKAGING MAP itself (payload -> rendered "
        "deliverable projection: parity, injectivity, lock preservation, trust "
        "anchoring), which neither prior receipt tested."
    ),
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.report-packager-render-claim-lock-preservation+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
out = BENCH / "render-claim-lock-preservation-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("all_gates_passed", g["all_pass"])
print("verdict", diag["verdict"])
print("two_replay_sha256", diag_sha)
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
