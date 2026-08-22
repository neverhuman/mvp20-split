#!/usr/bin/env python3
"""DSSE-Ed25519-sign the R-C05 checkpoint receipt (attempts/) for
amphora-barrier-corrosion-score. AUDIT_ONLY: signs an audit receipt under the
module's evidence/phase0/repairs/R-C05/attempts/ dir; does NOT sign a phase0
evaluation/review, does NOT promote authority, does NOT flip
scientific_readiness, does NOT modify the portfolio manifest, any locked
dataset, or any signed Phase-0 KPI."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-barrier-corrosion-score"
WORK = MOD / "evidence/phase0/repairs/R-C05/work"
ATTEMPTS = MOD / "evidence/phase0/repairs/R-C05/attempts"
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


def rd(p):
    return json.loads(p.read_text())


harness_sha = sha((WORK / "mondrian_domain_shift_conformal.py").read_bytes())

repaired_A = rd(WORK / "result.repaired.runA.json")
repaired_B_bytes = (WORK / "result.repaired.runB.json").read_bytes()
repaired_A_bytes = (WORK / "result.repaired.runA.json").read_bytes()
assert repaired_A_bytes == repaired_B_bytes, "naive-mondrian two-replay bytes differ"

conservative_A = rd(WORK / "result.conservative.runA.json")
conservative_B_bytes = (WORK / "result.conservative.runB.json").read_bytes()
conservative_A_bytes = (WORK / "result.conservative.runA.json").read_bytes()
assert conservative_A_bytes == conservative_B_bytes, "conservative-mondrian two-replay bytes differ"

defective_A = rd(WORK / "result.defective.runA.json")
defective_B_bytes = (WORK / "result.defective.runB.json").read_bytes()
defective_A_bytes = (WORK / "result.defective.runA.json").read_bytes()
assert defective_A_bytes == defective_B_bytes, "defective/pooled two-replay bytes differ"

# sanity: the "defective" (Mondrian-disabled / pure pooled) run must reproduce
# the ORIGINAL refuting receipt's numbers exactly -- confirms this harness is
# a faithful re-implementation of the pinned attack, not a different script.
orig_fwd = 0.922339
orig_rev = 0.876307
assert defective_A["forward_calibrate_nonmarine_deploy_marine"]["coverage"]["alpha_0.10"]["observed_test_coverage"] == orig_fwd
assert defective_A["reverse_calibrate_marine_deploy_nonmarine"]["coverage"]["alpha_0.10"]["observed_test_coverage"] == orig_rev

def leg_table(obj):
    out = {}
    for leg in ("forward_calibrate_nonmarine_deploy_marine", "reverse_calibrate_marine_deploy_nonmarine"):
        c = obj[leg]["coverage"]["alpha_0.10"]
        out[leg] = {
            "n_cal": obj[leg]["n_cal"], "n_test": c["n_test"],
            "n_covered": c["n_covered"],
            "observed_test_coverage": c["observed_test_coverage"],
            "meets_acceptance_floor_0.88": c["meets_acceptance_floor_0.88"],
            "binomial_pvalue_coverage_less_than_target_0.90": c["binomial_pvalue_coverage_less_than_target"],
            "mean_interval_width_log10": c["mean_interval_width_log10"],
        }
    return out

per_seed_per_leg_table = {
    "seed_0": {
        "defective_pooled_marginal_reproduces_original_refuting_receipt": leg_table(defective_A),
        "naive_per_class_mondrian": leg_table(repaired_A),
        "conservative_floor_mondrian": leg_table(conservative_A),
    }
}

interval_width_comparison = {
    "reverse_leg_alpha_0.10_mean_interval_width_log10": {
        "pooled_marginal_original": defective_A["reverse_calibrate_marine_deploy_nonmarine"]["coverage"]["alpha_0.10"]["mean_interval_width_log10"],
        "naive_per_class_mondrian": repaired_A["reverse_calibrate_marine_deploy_nonmarine"]["coverage"]["alpha_0.10"]["mean_interval_width_log10"],
        "conservative_floor_mondrian": conservative_A["reverse_calibrate_marine_deploy_nonmarine"]["coverage"]["alpha_0.10"]["mean_interval_width_log10"],
        "honest_note": "conservative-floor Mondrian is WIDER than pooled-marginal (3.449345 vs 3.440187 log10 units) yet still only recovers 3 of the ~11 additional covered test rows needed to cross the 0.88 floor (2433 vs 2430 covered, need >=2441 of 2773). Naive per-class Mondrian is narrower on average in this leg's dominant stratum and makes coverage WORSE (2376 covered)."
    }
}

body_obj = {
    "schema": "amphora.barrier-corrosion-score.corr-rate-conformal-mondrian-domain-shift-repair-checkpoint.v1",
    "module": "amphora-barrier-corrosion-score",
    "repair_item": "R-C05",
    "repair_mode": True,
    "fire_id": "20260812T070001-1574665-dd35fe76da66",
    "authority": "AUDIT_ONLY",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "purpose": (
        "REPAIR ATTEMPT (fire 1 of max_fires=3) on the claim refuted by "
        "corr-rate-conformal-domain-shift-v1 (CLAIM_REFUTED, 2026-08-02): "
        "re-runs the EXACT domain-shift protocol (identical data load, "
        "feature scheme, base model, train/held-out group_split, and "
        "cal/test marine-axis partition, same seed=0) with a Mondrian "
        "calibrator stratified by chloride-environment class, as "
        "prescribed by campaign item R-C05's pre-registered acceptance. "
        "Two Mondrian variants tried (naive per-class quantile; "
        "conservative-floor per-class quantile clamped to >= the pooled "
        "quantile) plus a positive-control replay of the mechanism-disabled "
        "(pure pooled/marginal) case to confirm this harness faithfully "
        "reproduces the original refuting receipt's numbers."),
    "reattack_of_own_repair": {
        "original_refuting_receipt": "amphora-barrier-corrosion-score/benchmarks/corr-rate-conformal-domain-shift-v1/corr-rate-conformal-domain-shift-receipt.v1.dsse.json",
        "original_refuting_receipt_envelope_sha256": "6cfa98626ac5f9e3dce9f2a1011a4d46ab6542c642d11492d787cc1d9366c3fb",
        "original_attack_script": "amphora-barrier-corrosion-score/benchmarks/corr-rate-conformal-domain-shift-v1/domain_shift_conformal.py",
        "original_attack_script_sha256": "382dd05855890a3105d0cc085d2b7f8dc0a088cf9e0a29123fb185aef205ae14",
        "same_seed": 0,
        "same_threshold": "0.90 target coverage, one-sided exact binomial p<0.05 significance test",
        "same_partition_rule": "forward: cal=held-out&nonmarine, test=held-out&marine; reverse: cal=held-out&marine, test=held-out&nonmarine (IDENTICAL to the refuting receipt)",
        "this_harness_reproduces_original_numbers_exactly": True,
        "reproduction_check": {
            "defective_mode_forward_0.90_coverage": defective_A["forward_calibrate_nonmarine_deploy_marine"]["coverage"]["alpha_0.10"]["observed_test_coverage"],
            "defective_mode_reverse_0.90_coverage": defective_A["reverse_calibrate_marine_deploy_nonmarine"]["coverage"]["alpha_0.10"]["observed_test_coverage"],
            "matches_original_refuting_receipt": True,
        },
    },
    "pre_registered_acceptance": {
        "text": "Both directions (forward and reverse) reach >= 0.88 observed coverage at the 0.90 target using a Mondrian calibrator stratified by chloride-environment class.",
        "floor": 0.88,
        "reverse_needs_n_covered_of_2773": 2441,
    },
    "per_seed_per_leg_table": per_seed_per_leg_table,
    "interval_width_comparison": interval_width_comparison,
    "mondrian_mechanisms_tried": [
        {
            "name": "naive_per_class_conformal_quantile",
            "description": "8 chloride-environment classes (halide/alkali/sulfuric/organic_acid/other_acid/water/salt_other/other); a class's own conformal quantile is used whenever it has >=5 calibration rows, else falls back to the pooled direction-level quantile.",
            "outcome": "REJECTED -- worse than the already-refuted pooled/marginal baseline on BOTH directions (forward 0.922339->0.871524, now also fails the 0.88 floor; reverse 0.876307->0.856834). Some strata's own quantile is narrower than pooled because within-class marine-vs-nonmarine residuals remain non-exchangeable.",
        },
        {
            "name": "conservative_floor_mondrian",
            "description": "Same 8-class stratification, but each stratum's own quantile is clamped to max(own_quantile, pooled_direction_quantile) -- per-class information may only widen the interval relative to pooled, per the objective's 'wider intervals are acceptable' allowance. Never reads test data.",
            "outcome": "Forward unchanged (0.922339, passes). Reverse improves only marginally: 0.876307 -> 0.877389 (n_covered 2430->2433 of 2773). STILL BELOW the 0.88 floor (needs n_covered>=2441); short by 8 rows.",
        },
        {
            "name": "coarse_2class_conservative_floor (halide vs other), exploratory probe only, not separately declared",
            "description": "Collapsed the 8 classes to a binary halide/non-halide split under the same conservative-floor rule, to check whether stratum granularity itself was the limiting factor.",
            "outcome": "IDENTICAL numeric result to the 8-class conservative-floor variant (reverse n_covered=2433/2773). Confirms the shortfall is structural: only the 'halide' class has enough marine-calibration mass (928 of 1043) to move the needle under any granularity; the bulk of nonmarine test rows fall in classes with zero marine-calibration representation and are forced to the pooled fallback regardless of how the taxonomy is drawn.",
        },
    ],
    "verdict": {
        "outcome": "CLAIM_REFUTED",
        "repair_status": "in_progress",
        "finding": (
            "Neither Mondrian variant tried this fire (naive per-class, "
            "conservative-floor per-class, at both 8-class and 2-class "
            "granularity) reaches the pre-registered >= 0.88 acceptance "
            "floor on the reverse leg (calibrate=marine, deploy=nonmarine) "
            "of the EXACT domain-shift protocol from the refuting receipt. "
            "The best variant (conservative-floor) reaches 0.877389 "
            "(n_covered=2433/2773), 8 rows short of the 2441 needed. This "
            "is a genuine, reproducible (byte-identical two-replay) result, "
            "not overturned by re-attacking with the identical seed/"
            "threshold/partition as the original refutation. The repair "
            "objective (Mondrian calibrator stratified by chloride-"
            "environment class restoring >=0.88 coverage) is CURRENTLY "
            "REFUTED; this campaign item is fire 1 of max_fires=3, so the "
            "pre-registered re-scope hatch is not yet available "
            "(available only at len(fires)>=max_fires-1=2, i.e. the final "
            "permitted fire)."),
    },
    "positive_control": {
        "planted_defect": "Mondrian stratification disabled (min_class_n forced to 10**9), forcing every chloride-class stratum to fall back to the single pooled/marginal quantile -- i.e. this harness's mechanism-disabled mode should exactly reproduce the ORIGINAL, already-refuted pooled-conformal numbers from corr-rate-conformal-domain-shift-v1.",
        "how_planted": "mondrian_domain_shift_conformal.py CLI mode 'defective' calls run(min_class_n=10**9, conservative=False), which forces class_used_own=False for every stratum in eval_direction_mondrian().",
        "detected": True,
        "evidence": (
            f"defective-mode forward 0.90-target coverage = "
            f"{defective_A['forward_calibrate_nonmarine_deploy_marine']['coverage']['alpha_0.10']['observed_test_coverage']} "
            f"(original refuting receipt: 0.922339, EXACT MATCH); "
            f"defective-mode reverse 0.90-target coverage = "
            f"{defective_A['reverse_calibrate_marine_deploy_nonmarine']['coverage']['alpha_0.10']['observed_test_coverage']} "
            "(original refuting receipt: 0.876307, EXACT MATCH). This confirms "
            "the checking harness faithfully reproduces the pinned attack when "
            "the repair mechanism is disabled, and is not silently passing "
            "regardless of input -- it correctly detects the planted defect "
            "(mechanism-disabled input reproduces the known-bad number, "
            "which the pre-registered 0.88 floor correctly flags as failing)."),
        "note": "This positive control is supplied for rigor even though the fire's overall verdict is CLAIM_REFUTED (not SURVIVED), since a refutation does not strictly require one; it demonstrates the checking harness itself is sound so the CLAIM_REFUTED verdict above is trustworthy rather than an artifact of a broken checker.",
    },
    "fail_closed_checks_all_variants": {
        "train_disjoint_from_all_heldout": True,
        "forward_cal_test_row_disjoint": True,
        "reverse_cal_test_row_disjoint": True,
        "forward_cal_all_nonmarine": True,
        "forward_test_all_marine": True,
        "reverse_cal_all_marine": True,
        "reverse_test_all_nonmarine": True,
        "class_quantiles_derived_only_from_cal_rows": True,
    },
    "state_for_next_fire": {
        "path": "amphora-barrier-corrosion-score/evidence/phase0/repairs/R-C05/work/STATE.json",
        "summary": "Recommends trying likelihood-ratio/covariate-shift-reweighted conformal (Tibshirani et al 2019) as an additional probe, and flags that the final permitted fire should invoke the pre-registered re-scope hatch (per-environment-class coverage table as the new claim) if Mondrian-by-chloride-class remains unable to reach 0.88.",
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS (all three modes: repaired/conservative/defective each byte-identical across runA/runB)",
        "harness_path": "amphora-barrier-corrosion-score/evidence/phase0/repairs/R-C05/work/mondrian_domain_shift_conformal.py",
        "harness_sha256": harness_sha,
        "determinism": {"omp_num_threads": "1", "seed": 0, "no_timestamp": True, "float_round_decimals": 6},
    },
    "scope_honesty": (
        "Bare-metal/alloy substrate corrosion (same ceiling as corr-rate-qspr-v1 "
        "/ corr-rate-conformal-v1). AUDIT_ONLY: does not flip "
        "scientific_readiness, does not modify the manifest (66/11 untouched), "
        "grants no coating-barrier ranking authority."),
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.barrier-corrosion-conformal-mondrian-repair-checkpoint+json"

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

sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex,
           "eval_derives_pinned_trust_key": bool(eval_pin),
           "reviewer_derives_pinned_trust_key": bool(rev_pin),
           "signature": envelope}

ATTEMPTS.mkdir(parents=True, exist_ok=True)
out = ATTEMPTS / "r-c05-mondrian-repair-checkpoint-fire1.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
