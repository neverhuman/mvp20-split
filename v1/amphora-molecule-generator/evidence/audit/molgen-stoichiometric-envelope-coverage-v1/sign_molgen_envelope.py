#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-molecule-generator stoichiometric
design-envelope-coverage AUDIT_ONLY receipt.

AUDIT_ONLY: signs an audit receipt under evidence/audit/; does NOT sign a
phase0 evaluation/review, does NOT promote authority, does NOT flip
scientific_readiness (stays UNVALIDATED), does NOT modify the manifest (66
receipts / 11 modules), any locked dataset, or any signed Phase-0 KPI.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = (ROOT / "amphora-molecule-generator/evidence/audit"
         / "molgen-stoichiometric-envelope-coverage-v1")
ENVELOPE = (ROOT / "amphora-molecule-generator/reference/mvp20/data"
            / "hardener_stoichiometric_envelope.v1.json")
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
harness_sha = sha((BENCH / "run_molgen_envelope.py").read_bytes())
envelope_sha = sha(ENVELOPE.read_bytes())
assert envelope_sha == diag["hash_and_count_lock"]["envelope_reference_sha256"], \
    "envelope reference sha256 drifted from the diagnostic lock"

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

gs = diag["generated_set_stoichiometry"]
cov = diag["envelope_coverage_test"]
mech = diag["mechanism_mass_functionality_coupling"]
add = diag["adduct_closure_projection"]
hyp = diag["hypothesis_evaluation"]

body_obj = {
    "schema": "amphora.molecule-generator.molgen-stoichiometric-envelope-coverage-receipt.v1",
    "study_id": diag["study_id"],
    "authority": "AUDIT_ONLY",
    "run_type": "GENERATOR_STOICHIOMETRIC_DESIGN_ENVELOPE_COVERAGE_CHARACTERIZATION",
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
    "new_reference_artifact": {
        "path": "amphora-molecule-generator/reference/mvp20/data/hardener_stoichiometric_envelope.v1.json",
        "sha256": envelope_sha,
        "role": "hash-locked stoichiometric design-envelope anchors, known-answer amines, and fail-closed decoys",
    },
    "results": {
        "instrument_self_tests_pass": diag["instrument_self_tests_summary"]["n_pass"],
        "instrument_self_tests_total": diag["instrument_self_tests_summary"]["n_total"],
        "instrument_self_tests_all_pass": diag["instrument_self_tests_summary"]["all_pass"],
        "fail_closed_pass": diag["fail_closed_summary"]["n_pass"],
        "fail_closed_total": diag["fail_closed_summary"]["n_total"],
        "fail_closed_all_pass": diag["fail_closed_summary"]["all_pass"],
        "active_nh_parity_vs_prior_receipt": diag["parity_vs_prior_receipt"]["n_active_nh_agreements"],
        "active_nh_parity_total": diag["parity_vs_prior_receipt"]["n_molecules"],
        "active_nh_parity_complete": diag["parity_vs_prior_receipt"]["parity_complete"],
        "n_molecules": gs["n_molecules"],
        "ahew_min_g_per_eq": gs["ahew_min_g_per_eq"],
        "ahew_max_g_per_eq": gs["ahew_max_g_per_eq"],
        "ahew_median_g_per_eq": gs["ahew_median_g_per_eq"],
        "amine_value_range_mgKOH_per_g": [gs["amine_value_min_mgKOH_per_g"],
                                          gs["amine_value_max_mgKOH_per_g"]],
        "phr_at_eew_170p21_range": [gs["phr_at_eew_170p21_min"], gs["phr_at_eew_170p21_max"]],
        "ahew_times_av_identity_band_holds_for_all": gs["identity_band_holds_for_all"],
        "n_exactly_on_all_primary_identity_floor": gs["n_exactly_on_all_primary_floor_28052p8"],
        "commercial_envelope_g_per_eq": cov["commercial_envelope_g_per_eq"],
        "generated_hull_g_per_eq": cov["generated_hull_g_per_eq"],
        "n_anchors_inside_generated_hull": cov["n_anchors_inside_generated_hull"],
        "n_anchors": cov["n_anchors"],
        "anchor_coverage_fraction": cov["anchor_coverage_fraction"],
        "interval_overlap_fraction_of_commercial": cov["interval_overlap_fraction_of_commercial"],
        "shortfall_to_commercial_floor_g_per_eq": cov["shortfall_to_commercial_floor_g_per_eq"],
        "shortfall_relative_to_commercial_floor": cov["shortfall_relative_to_commercial_floor"],
        "spearman_rho_molar_mass_vs_active_nh": mech["spearman_rho_molar_mass_vs_active_nh"],
        "marginal_bound_ahew_g_per_eq": mech["marginal_bound_ahew_g_per_eq"],
        "realized_frontier_ahew_g_per_eq": mech["realized_frontier_ahew_g_per_eq"],
        "n_strata_reaching_commercial_floor": sum(
            1 for s in mech["by_active_nh_stratum"] if s["stratum_reaches_commercial_floor"]),
        "n_strata": len(mech["by_active_nh_stratum"]),
        "adduct_k2_in_commercial_band": add["by_k"]["k_2"]["n_in_commercial_band"],
        "adduct_k2_projected": add["by_k"]["k_2"]["n_projected"],
        "adduct_k3_in_commercial_band": add["by_k"]["k_3"]["n_in_commercial_band"],
        "adduct_best_k": add["best_k"],
        "anchors_recovered_under_best_k": add["anchors_recovered_under_best_k"],
        "adduct_status": add["status"],
        "hypothesis_verdict": hyp["verdict"],
    },
    "envelope_coverage_test": cov,
    "mechanism_mass_functionality_coupling": mech,
    "adduct_closure_projection": {
        "operator": add["operator"],
        "citation": add["citation"],
        "status": add["status"],
        "m_dgeba_g_per_mol": add["m_dgeba_g_per_mol"],
        "best_k": add["best_k"],
        "anchors_recovered_under_best_k": add["anchors_recovered_under_best_k"],
        "k_2_summary": {k: v for k, v in add["by_k"]["k_2"].items() if k != "per_molecule"},
        "k_3_summary": {k: v for k, v in add["by_k"]["k_3"].items() if k != "per_molecule"},
    },
    "hypothesis_evaluation": hyp,
    "rights_posture": diag["rights_posture"],
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "harness_sha256": harness_sha,
        "envelope_reference_sha256": envelope_sha,
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
ptype = ("application/vnd.amphora.molecule-generator-"
         "molgen-stoichiometric-envelope-coverage+json")
sig = eval_sk.sign(pae(ptype, body))
envelope = {
    "payload": base64.standard_b64encode(body).decode(),
    "payloadType": ptype,
    "signatures": [{"keyid": eval_key_id,
                    "sig": base64.standard_b64encode(sig).decode()}],
}
receipt = {
    "evaluator_key_id": eval_key_id,
    "evaluator_public_key_hex": eval_pub_hex,
    "reviewer_public_key_hex": rev_pub_hex,
    "signature": envelope,
}
out = BENCH / "molgen-stoichiometric-envelope-coverage-receipt.v1.dsse.json"
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
print("envelope_reference_sha256", envelope_sha)
print("signature_verified", True)
