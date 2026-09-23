#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-cro-protocol-packager decision-rule-power-adequacy-v1
AUDIT_ONLY receipt. Signs an audit receipt under evidence/audit/; does NOT sign a phase0
evaluation/review, does NOT promote authority, does NOT flip scientific_readiness (stays
NOT_APPLICABLE), does NOT modify the portfolio manifest (66 receipts / 11 modules), any locked
dataset, the Phase-0 KPI, or the benchmark-lock.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-cro-protocol-packager"
EV = MOD / "evidence/audit/decision-rule-power-adequacy-v1"
BM = MOD / "benchmarks/decision-rule-power-adequacy-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"
BLOCK = MOD / "evidence/phase0/benchmark/benchmark-lock.v1.json"
PROTOCOL = MOD / "reference/mvp20/out/falsification_protocol.json"


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

harness_sha = sha((BM / "run_decision_power.py").read_bytes())
benchmark_lock_sha = sha(BLOCK.read_bytes())
protocol_sha = sha(PROTOCOL.read_bytes())

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
body_obj = {
    "schema": "amphora.cro-protocol-packager.decision-rule-power-adequacy-receipt.v1",
    "study_id": diag["study_id"],
    "authority": "AUDIT_ONLY",
    "run_type": diag["run_type"],
    "module": "amphora-cro-protocol-packager",
    "promotes_authority": False, "flips_scientific_readiness": False,
    "human_review_performed": False, "organizational_independence_asserted": False,
    "modifies_manifest": False, "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False, "modifies_benchmark_lock": False,
    "modifies_shipped_protocol": False,
    "claim": diag["headline"], "purpose": diag["purpose"],
    "novelty_vs_prior_packager_audits": diag["novelty_vs_prior_packager_audits"],
    "non_circularity": diag["non_circularity"],
    "theory_reference": diag["theory_reference"],
    "inputs": diag["inputs"],
    "results": {
        "verdict": diag["verdict"],
        "all_gates_passed": diag["all_gates_passed"],
        "gates_failed": diag["gates_failed"],
        "exact_type_I_primary_rank_rule": g["G1_kendall_exact_null_type_I"]["exact_type_I_primary_rule"],
        "exact_type_I_compound_rule": g["G1_kendall_exact_null_type_I"]["exact_type_I_compound_rule_with_key_pairwise"],
        "key_pairwise_conjunct_redundant": g["G1_kendall_exact_null_type_I"]["key_pairwise_conjunct_is_redundant_given_primary_rule"],
        "finest_attainable_rank_level_at_4_tracks": g["G1_kendall_exact_null_type_I"]["finest_attainable_level_1_over_n_factorial"],
        "power_engine_cohen_kat_matches": g["G2_power_engine_known_answer"]["cohen_kat_matches"],
        "power_engine_usbr_mdd_abs_err_max": g["G2_power_engine_known_answer"]["usbr_mdd_abs_err_max"],
        "sigma_R_decades": g["G3_minimum_detectable_difference"]["sigma_R_decades"],
        "between_panel_variance_share": g["G3_minimum_detectable_difference"]["between_panel_variance_share"],
        "pooled_between_system_sd_decades": g["G3_minimum_detectable_difference"]["pooled_between_system_sd_decades"],
        "mdd_at_shipped_panel_counts": g["G3_minimum_detectable_difference"]["mdd"],
        "power_decisive_pair_at_observed_spread": g["G4_decisive_pairwise_bet_power"]["power_at_observed_between_system_spread"],
        "P_decisive_pair_TIED": g["G4_decisive_pairwise_bet_power"]["P_decisive_pair_TIED_at_observed_spread"],
        "H0_adequately_powered": g["G4_decisive_pairwise_bet_power"]["H0_shipped_pairwise_bet_is_adequately_powered"],
        "n_required_80pct_at_sigma_R": g["G5_inverse_design_n_required"]["headline_n_required_at_observed_spread_and_sigma_R"],
        "shortfall_factor_vs_shipped_default": g["G5_inverse_design_n_required"]["shortfall_factor_vs_shipped_default"],
        "key_pairwise_pins_an_arm": g["G6_arm_multiplicity_endpoint_pinning"]["key_pairwise_names_an_arm"],
        "fwer_upper_bound_post_hoc_arm_choice": g["G6_arm_multiplicity_endpoint_pinning"]["fwer_upper_bound_if_arm_chosen_post_hoc"],
        "specification_items_absent": g["G7_specification_completeness"]["absent"],
    },
    "gates": g,
    "closes": diag["closes"], "does_not_close": diag["does_not_close"],
    "remediation_required_for_phase1": diag["remediation_required_for_phase1"],
    "provenance": {
        "module_benchmark_lock_sha256": benchmark_lock_sha,
        "shipped_falsification_protocol_sha256": protocol_sha,
        "precision_receipt_sha256": diag["inputs"]["precision_receipt_sha256"],
        "harness_sha256": {"run_decision_power.py": harness_sha},
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "rng_used": False, "seed_required": False,
        "replay_method": "independent full pipeline: reload shipped protocol bytes and the signed "
                         "USBR precision receipt, re-enumerate all 4! track orderings, recompute "
                         "every Kendall tau against the locked rank and both hostile nulls, "
                         "re-solve the noncentral-t MDD by bisection and re-scan the inverse-design "
                         "n grid; exhaustive enumeration and deterministic special functions only",
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
ptype = "application/vnd.amphora.cro-protocol-packager-decision-rule-power-adequacy+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
out = EV / "decision-rule-power-adequacy-receipt.v1.dsse.json"
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
