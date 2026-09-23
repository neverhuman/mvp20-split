#!/usr/bin/env python3
"""DSSE-Ed25519-sign the st19168-preregistered-v1 AUDIT_ONLY receipt for
amphora-barrier-corrosion-score. AUDIT_ONLY: signs an audit receipt under the
module's benchmarks/ dir; does NOT sign a phase0 evaluation/review, does NOT
promote authority, does NOT flip scientific_readiness (stays UNVALIDATED /
PRE_PHASE_0), does NOT modify the portfolio manifest, any locked dataset, or
any signed Phase-0 KPI. Does NOT open, parse, or derive from the quarantined
ST-19168 xlsx -- only synthetic shadow data is referenced.

The core commitment of this receipt: it records SHA256(analyze_st19168_preregistered.py)
as it exists RIGHT NOW, before ST-19168 rights are cleared and before that script
is ever run on real data. Post-unlock execution can be checked byte-for-byte
against this hash."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-barrier-corrosion-score/benchmarks/st19168-preregistered-v1"
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
        try:
            return bytes.fromhex(raw.decode())
        except Exception:
            pass
    return raw[:32]


# --- frozen script hash-lock ---
frozen_script_bytes = (BENCH / "analyze_st19168_preregistered.py").read_bytes()
frozen_script_sha256 = sha(frozen_script_bytes)
prereg_md_sha256 = sha((BENCH / "PREREGISTRATION.md").read_bytes())
generator_sha256 = sha((BENCH / "generate_shadow_data.py").read_bytes())

# --- two-replay checks ---
def replay_check(stem):
    canon = (BENCH / f"{stem}.canonical.json").read_bytes()
    runA = (BENCH / f"{stem}.runA.json").read_bytes()
    runB = (BENCH / f"{stem}.runB.json").read_bytes()
    assert canon == runA == runB, f"{stem}: two-replay bytes differ"
    return sha(canon)

result_null_sha = replay_check("result_null")
result_alt_sha = replay_check("result_alt")

result_null = json.loads((BENCH / "result_null.canonical.json").read_text())
result_alt = json.loads((BENCH / "result_alt.canonical.json").read_text())
calibration = json.loads((BENCH / "calibration_result.canonical.json").read_text())
calibration_sha = sha((BENCH / "calibration_result.canonical.json").read_bytes())

shadow_null_sha = sha((BENCH / "shadow_null.json").read_bytes())
shadow_alt_sha = sha((BENCH / "shadow_alt.json").read_bytes())

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"
eval_pin = rev_pin = False
if TRUST.exists():
    trust = json.loads(TRUST.read_text())
    tbr = {k.get("role"): k for k in trust.get("keys", [])}
    eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
    rev_pin = (rev_key_id == tbr.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))

body_obj = {
    "schema": "amphora.barrier-corrosion-score.st19168-preregistration-receipt.v1",
    "module": "amphora-barrier-corrosion-score",
    "benchmark": "st19168-preregistered-v1",
    "campaign_item_id": "C3",
    "authority": "AUDIT_ONLY",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "opened_or_parsed_quarantined_asset": False,
    "quarantined_asset_touched": {
        "path": "amphora-barrier-corrosion-score/reference/eis/st-19168/raw/19168_inhibitive_coating_system_data.xlsx",
        "sha256": "9e34fccc83fa7b9d7f3cb21c0076ff34f30266cae5d11df02d6d00c72e9d44e1",
        "touched": False,
        "note": "All testing in this package uses synthetic shadow data (pinned seeds, same 10-system x EIS|Z|+rust-creep shape) generated from the campaign item's own public shape description, not from the quarantined file."},
    "purpose": (
        "Pre-registered, frozen analysis plan for the ST-19168 unlock: hypotheses pinned "
        "to mission.md's locked KPI (blinded Kendall tau at metrics.barrier_index >= 0.5 "
        "AND superiority over solids-only + PVC-only hostile nulls), an exact statistical "
        "plan (estimator, exact-permutation test, n, alpha, fixed-sequence multiple-"
        "comparison handling), an honest achievable-power statement at n=10, and a "
        "hash-locked commitment to the frozen analysis script -- all BEFORE ST-19168 "
        "rights are cleared and BEFORE any real data is read."),
    "hash_lock_commitment": {
        "frozen_script_path": "amphora-barrier-corrosion-score/benchmarks/st19168-preregistered-v1/analyze_st19168_preregistered.py",
        "frozen_script_sha256": frozen_script_sha256,
        "preregistration_md_sha256": prereg_md_sha256,
        "shadow_data_generator_sha256": generator_sha256,
        "commitment": (
            "Any execution of this script against the real, rights-cleared ST-19168 "
            "extraction MUST be byte-identical to frozen_script_sha256 to count as the "
            "pre-registered analysis. A differing hash requires disclosure as a post-hoc "
            "amendment with an explicit diff and reason (Nosek et al. 2018 PNAS "
            "115(11):2600-2606 deviation-disclosure norm).")},
    "hypotheses": {
        "H1a_primary": "tau_b(locked_barrier_index, -rust_creep_mm) > 0 one-sided AND observed tau >= 0.50",
        "H1b_superiority_solids": "tau_b(locked,truth) > tau_b(solids_only_null,truth), one-sided; evaluated only if H1a passes",
        "H1c_superiority_pvc": "tau_b(locked,truth) > tau_b(pvc_only_null,truth), one-sided; evaluated only if H1b passes",
        "locked_kpi_is_the_conjunction": "H1a AND H1b AND H1c, exactly matching mission.md's compound target"},
    "statistical_plan_summary": {
        "estimator": "Kendall tau-b",
        "primary_test": "one-sided exact permutation (scipy exact method + independent from-scratch full-enumeration cross-check)",
        "superiority_test": "paired bootstrap (B=100000) + independent permutation-based robustness cross-check",
        "multiple_comparison_handling": "fixed-sequence/hierarchical gatekeeping (Maurer/Hothorn/Lehmacher 1995; Bauer et al. 1998), not Bonferroni -- matches mission.md's AND-structured compound criterion",
        "alpha": 0.05,
        "n_target": 10,
        "n_feasibility_floor": 6,
        "power_reference_formula": "Bonett & Wright 2000, Psychometrika 65(1):23-28, DOI:10.1007/BF02294183"},
    "honest_power_statement": {
        "closed_form_n_required_for_80pct_power_at_tau_0p50_alpha_0p05_one_sided": 25,
        "closed_form_achieved_power_at_n10_primary_test_approx": 0.41,
        "interpretation": (
            "n=10 gives the primary test (H1a) an asymptotic-approximation achieved power "
            "of only ~41% at the locked target effect size; the two dependent secondary "
            "superiority tests (H1b, H1c) are structurally lower-powered still. A "
            "NOT_SUPPORTED verdict on real n=10 ST-19168 data would NOT by itself refute "
            "the population-level locked KPI -- this is disclosed BEFORE data is seen, "
            "consistent with the >=90-system finding in "
            "amphora-public-corrosion-benchmark/evidence/audit/eis-reproducibility-"
            "discrimination-power-v1/ for the analogous cross-modality rank.")},
    "shadow_data_tests": {
        "shadow_null_sha256": shadow_null_sha,
        "shadow_alt_sha256": shadow_alt_sha,
        "result_null_canonical_sha256": result_null_sha,
        "result_alt_canonical_sha256": result_alt_sha,
        "result_null_verdict": result_null["verdict"],
        "result_null_step1_pass": result_null["gate_summary"]["step1_primary_locked_target"],
        "result_alt_verdict": result_alt["verdict"],
        "result_alt_gate_summary": result_alt["gate_summary"],
        "result_alt_tau_locked_this_draw": result_alt["point_estimates"]["tau_locked_vs_rust_creep_truth"],
        "primary_crosscheck_agreement_null": result_null["primary_test_step1"]["cross_check_agreement"],
        "primary_crosscheck_agreement_alt": result_alt["primary_test_step1"]["cross_check_agreement"],
        "two_replay_byte_stable": True,
        "interpretation": (
            "NULL shadow draw (no true signal): pipeline correctly does NOT report "
            "step1_pass=true (Type-I error not triggered on this draw). ALT shadow draw "
            "(true population tau~0.50 embedded): pipeline correctly detects the primary "
            "signal (H1a passes) and correctly demonstrates that a secondary superiority "
            "gate can still fail at n=10 even when the primary signal is real and "
            "detected -- exactly the honest small-n behavior this pre-registration warns "
            "readers to expect.")},
    "calibration": {
        "calibration_result_sha256": calibration_sha,
        "k_replicates_per_arm": calibration["k_replicates_per_arm"],
        "type1_error_probe": {
            "false_positive_count": calibration["type1_error_probe_null_arm"]["false_positive_count"],
            "k": calibration["type1_error_probe_null_arm"]["k"],
            "empirical_type1_rate": calibration["type1_error_probe_null_arm"]["empirical_type1_rate"],
            "clopper_pearson_95ci": calibration["type1_error_probe_null_arm"]["clopper_pearson_95ci"],
            "within_ci_of_nominal_alpha": calibration["type1_error_probe_null_arm"]["within_ci_of_nominal_alpha"]},
        "empirical_power_probe": {
            "step1_empirical_power": calibration["empirical_power_probe_alt_arm"]["step1_empirical_power"],
            "step1_clopper_pearson_95ci": calibration["empirical_power_probe_alt_arm"]["step1_clopper_pearson_95ci"],
            "full_gate_empirical_power": calibration["empirical_power_probe_alt_arm"]["full_gate_empirical_power"],
            "full_gate_clopper_pearson_95ci": calibration["empirical_power_probe_alt_arm"]["full_gate_clopper_pearson_95ci"]},
        "note": ("K=15 replicates per arm is itself a small-sample calibration (a Clopper-"
                 "Pearson CI is reported precisely because K is small) -- offered as "
                 "simulation-grounded corroboration of the closed-form power statement "
                 "above, not a replacement for it.")},
    "does_not_close": [
        "No claim about ST-19168's real numeric content is made anywhere in this package.",
        "This pre-registration does not itself constitute the mission.md locked primary KPI "
        "(a blinded four-track independent-panel comparison); it is a smaller, honestly-"
        "scoped, ST-19168-specific corroborating rehearsal to be executed the day rights clear.",
        "Promotes no authority, phase, or manifest state."],
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under amphora-barrier-corrosion-score/benchmarks/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin)},
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER", "key_id": rev_key_id, "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin), "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed."},
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.barrier-corrosion-st19168-preregistration+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
out = BENCH / "preregistration-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
# verify immediately
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("frozen_script_sha256", frozen_script_sha256)
print("result_null_sha256", result_null_sha)
print("result_alt_sha256", result_alt_sha)
print("calibration_sha256", calibration_sha)
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
