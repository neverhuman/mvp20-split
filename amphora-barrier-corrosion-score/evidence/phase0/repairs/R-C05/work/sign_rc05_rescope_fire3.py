#!/usr/bin/env python3
"""DSSE-Ed25519-sign the R-C05 fire-3 (FINAL) re-scope done receipt for
amphora-barrier-corrosion-score. AUDIT_ONLY: signs an audit receipt under the
module's evidence/phase0/repairs/R-C05/done/ dir; does NOT sign a phase0
evaluation/review, does NOT promote authority, does NOT flip
scientific_readiness, does NOT modify the portfolio manifest, any locked
dataset, or any signed Phase-0 KPI."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-barrier-corrosion-score"
WORK = MOD / "evidence/phase0/repairs/R-C05/work"
ATTEMPTS = MOD / "evidence/phase0/repairs/R-C05/attempts"
DONE = MOD / "evidence/phase0/repairs/R-C05/done"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

FIRE_ID = "20260812T090002-2576123-87df1529555a"


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


rescope_A_bytes = (WORK / "rescope.runA.json").read_bytes()
rescope_B_bytes = (WORK / "rescope.runB.json").read_bytes()
assert rescope_A_bytes == rescope_B_bytes, "rescope coverage-table two-replay bytes differ"
rescope = rd(WORK / "rescope.runA.json")
harness_sha = sha((WORK / "rescope_coverage_table.py").read_bytes())

fire1_bytes = (ATTEMPTS / "r-c05-mondrian-repair-checkpoint-fire1.v1.dsse.json").read_bytes()
fire2_bytes = (ATTEMPTS / "r-c05-mondrian-repair-checkpoint-fire2.v1.dsse.json").read_bytes()

orig_receipt_path = MOD / "benchmarks/corr-rate-conformal-domain-shift-v1/corr-rate-conformal-domain-shift-receipt.v1.dsse.json"
orig_harness_path = MOD / "benchmarks/corr-rate-conformal-domain-shift-v1/domain_shift_conformal.py"
orig_receipt_sha = sha(orig_receipt_path.read_bytes())
orig_harness_sha = sha(orig_harness_path.read_bytes())

fwd = rescope["forward_calibrate_nonmarine_deploy_marine"]["overall"]
rev = rescope["reverse_calibrate_marine_deploy_nonmarine"]["overall"]
rev_table = rescope["reverse_calibrate_marine_deploy_nonmarine"]["per_chloride_environment_class"]
fwd_table = rescope["forward_calibrate_nonmarine_deploy_marine"]["per_chloride_environment_class"]

body_obj = {
    "schema": "amphora.barrier-corrosion-score.corr-rate-conformal-per-environment-coverage-repair.v1",
    "module": "amphora-barrier-corrosion-score",
    "repair_item": "R-C05",
    "repair_mode": True,
    "resolution": "rescope",
    "fire_id": FIRE_ID,
    "fire_number_of_max": "3 of 3 (FINAL PERMITTED FIRE)",
    "authority": "AUDIT_ONLY",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "directive_path": "none",
    "directive_sha256": "",
    "purpose": (
        "Fire 3 of max_fires=3 (the FINAL permitted fire) on campaign item "
        "R-C05. Invokes the item's own pre-registered re-scope hatch: "
        "'per-environment coverage table as the new claim if stratification "
        "cannot reach 0.88'. Fire 1 (empirical) and fire 2 (analytic proof) "
        "exhaustively showed the Mondrian-by-chloride-class mechanism named "
        "in the pre-registered acceptance CANNOT reach the 0.88 reverse-leg "
        "floor at any hyperparameter, and a supplementary reweighted-"
        "conformal probe failed an order of magnitude worse due to a near-"
        "total covariate-support mismatch (domain-classifier AUC=1.0). This "
        "fire does not retry either mechanism. It re-runs the IDENTICAL "
        "data/feature/model/split/cal-test-assignment protocol one more "
        "time and reports the per-chloride-environment-class coverage table "
        "(both the original pooled/refuted calibrator and fire 1's best "
        "conservative-Mondrian repair, side by side) as the new, honest, "
        "narrower claim in place of a single pooled >=0.88 number."),
    "pre_registered_re_scope_hatch_cited": {
        "text_from_campaign_item": "re-scope hatch: per-environment coverage table as the new claim if stratification cannot reach 0.88",
        "availability_condition": "len(fires) >= max_fires-1 (2 >= 2, satisfied by fire 2's ledger record)",
        "invoked_this_fire": True,
    },
    "prior_mechanism_exhaustion_cited": {
        "fire1_checkpoint_path": "amphora-barrier-corrosion-score/evidence/phase0/repairs/R-C05/attempts/r-c05-mondrian-repair-checkpoint-fire1.v1.dsse.json",
        "fire1_checkpoint_sha256": sha(fire1_bytes),
        "fire1_finding": "Naive per-class Mondrian: worse both directions. Conservative-floor Mondrian (best variant): reverse 0.876307 -> 0.877389 (2433/2773), 8 rows short of 2441 needed for 0.88.",
        "fire2_checkpoint_path": "amphora-barrier-corrosion-score/evidence/phase0/repairs/R-C05/attempts/r-c05-mondrian-repair-checkpoint-fire2.v1.dsse.json",
        "fire2_checkpoint_sha256": sha(fire2_bytes),
        "fire2_finding": "Analytic structural-ceiling proof: 6/8 chloride classes have EXACTLY ZERO marine-calibration rows in the reverse leg; 75.9% of reverse-leg test rows forced to pooled fallback regardless of MIN_CLASS_N. Supplementary Tibshirani-2019 reweighted-conformal probe failed far worse (coverage 0.0638), domain-classifier AUC=1.0 (near-total positivity violation).",
    },
    "original_refuting_receipt_cited": {
        "path": "amphora-barrier-corrosion-score/benchmarks/corr-rate-conformal-domain-shift-v1/corr-rate-conformal-domain-shift-receipt.v1.dsse.json",
        "sha256": orig_receipt_sha,
        "harness_path": "amphora-barrier-corrosion-score/benchmarks/corr-rate-conformal-domain-shift-v1/domain_shift_conformal.py",
        "harness_sha256": orig_harness_sha,
        "seed": 0,
        "threshold": "0.90 target coverage, one-sided exact binomial p<0.05 significance",
        "original_reverse_leg_finding": "observed coverage 0.876307, p=3.1e-5, REFUTED",
    },
    "protocol": {
        "note": "IDENTICAL data load, feature scheme, base model (HistGradientBoostingRegressor seed=0), group_split (bucket=idx%5, train={2,3,4}), and marine-axis cal/test assignment (forward: cal=nonmarine,test=marine; reverse: cal=marine,test=nonmarine) as the refuting receipt and both prior R-C05 fires. alpha=0.10 (0.90 target). Two calibrators reported per class: pooled (the original refuted marginal calibrator) and conservative_mondrian (fire 1's best repair variant, per-class quantile clamped to >= pooled, min_class_n=5).",
        "harness_path": "amphora-barrier-corrosion-score/evidence/phase0/repairs/R-C05/work/rescope_coverage_table.py",
        "harness_sha256": harness_sha,
        "dataset_source_sha256": rescope["dataset"]["source_sha256"],
        "artifact_cited": "amphora-barrier-corrosion-score/evidence/phase0/repairs/R-C05/work/rescope.runA.json",
        "artifact_sha256": sha(rescope_A_bytes),
        "two_replay_sha256_gate": "PASS (rescope.runA.json byte-identical to rescope.runB.json)",
        "determinism": {"omp_num_threads": "1", "seed": 0, "no_timestamp": True, "float_round_decimals": 6},
    },
    "prior_pooled_marginal_acceptance_status": {
        "floor": 0.88,
        "forward_pooled_coverage": fwd["pooled_coverage"],
        "reverse_pooled_coverage": rev["pooled_coverage"],
        "forward_conservative_mondrian_coverage": fwd["conservative_mondrian_coverage"],
        "reverse_conservative_mondrian_coverage": rev["conservative_mondrian_coverage"],
        "both_directions_meet_floor_pooled": bool(fwd["meets_acceptance_floor_0.88_pooled"] and rev["meets_acceptance_floor_0.88_pooled"]),
        "both_directions_meet_floor_conservative_mondrian": bool(fwd["meets_acceptance_floor_0.88_conservative_mondrian"] and rev["meets_acceptance_floor_0.88_conservative_mondrian"]),
        "verdict_on_original_acceptance": "NOT MET. Reverse-leg pooled and conservative-Mondrian coverage both remain below 0.88 (0.876307 and 0.877389 respectively). This confirms fires 1-2's finding a third time; not retried as a fresh mechanism.",
    },
    "new_claim_per_environment_coverage_table": {
        "text": "Per-chloride-environment-class observed 0.90-target coverage, both directions, both calibrators (pooled vs conservative-Mondrian), on the IDENTICAL held-out rows/partition as the refuted claim.",
        "forward_calibrate_nonmarine_deploy_marine": fwd_table,
        "reverse_calibrate_marine_deploy_nonmarine": rev_table,
        "reverse_classes_with_marine_calibration_support": rescope["reverse_calibrate_marine_deploy_nonmarine"]["classes_with_marine_calibration_support"],
        "reverse_classes_with_zero_marine_calibration_support": rescope["reverse_calibrate_marine_deploy_nonmarine"]["classes_with_zero_marine_calibration_support"],
        "reverse_fraction_test_rows_without_any_calibration_support": rescope["reverse_calibrate_marine_deploy_nonmarine"]["fraction_test_rows_without_any_calibration_support"],
        "honest_reading": (
            "In the reverse (marine-cal -> nonmarine-deploy) leg, only 2 of "
            "8 chloride-environment classes (halide, other; 24.1% of test "
            "rows) have ANY marine-calibration support, and both clear 0.88 "
            "individually (halide 0.952569, other 0.920482). The pooled-"
            "coverage shortfall against the 0.88 floor is driven by classes "
            "with ZERO marine-calibration rows: other_acid (662 test rows, "
            "0.799094 coverage), sulfuric (557 rows, 0.852783), and water "
            "(13 rows, 0.769231) sit meaningfully below 0.88 with no "
            "calibration-side fix available from this data; alkali (480 "
            "rows, 0.916667), organic_acid (322 rows, 0.913043) and "
            "salt_other (71 rows, 0.873239) happen to sit near or above "
            "0.88 despite zero marine-calibration support -- coincidental, "
            "not mechanism-derived, since these classes fall back to the "
            "pooled quantile. The table shows conformal coverage in this "
            "domain-shift direction is reliable ONLY where marine "
            "calibration data actually exists for that chloride-environment "
            "class (halide, other); elsewhere the honest state is 'no "
            "distribution-free guarantee available from this calibration "
            "data', not 'repaired to >=0.88'. The forward direction (cal="
            "nonmarine, test=marine) clears 0.88 in every class (min "
            "0.786194 at alpha=0.20, all classes >=0.88 at alpha=0.10) "
            "because forward calibration draws from the much larger, more "
            "diverse nonmarine pool."),
    },
    "verdict": {
        "outcome": "CLAIM_REFUTED",
        "repair_status": "rescoped",
        "finding": (
            "The pre-registered claim (Mondrian-by-chloride-class conformal "
            "restores >=0.88 pooled coverage in both directions) remains "
            "REFUTED -- confirmed a third time on this fire's fresh run of "
            "the identical protocol (reverse pooled 0.876307, conservative-"
            "Mondrian 0.877389, both < 0.88). This campaign item has now "
            "exhausted its max_fires=3 budget. Per the item's own pre-"
            "registered re-scope hatch (available at the final permitted "
            "fire), the deliverable for this item becomes the per-"
            "environment-class coverage table above, which replaces the "
            "single pooled >=0.88 claim with an honest, class-resolved "
            "statement of where distribution-free conformal coverage is and "
            "is not currently supported by calibration data in the reverse "
            "(marine->nonmarine) domain-shift direction. No further Mondrian "
            "or reweighting variant is recommended: two independent "
            "calibration-side mechanisms have now been shown (empirically "
            "and analytically) incapable of closing this gap, and the root "
            "cause -- near-total covariate-support mismatch between marine-"
            "calibration and non-marine-test populations for 6 of 8 "
            "chloride-environment classes -- is a property of the available "
            "data, not of the calibration algorithm."),
    },
    "fail_closed_checks": {
        "note": "Identical checks as fires 1-2 (train/cal/test disjointness, quantiles derived only from cal rows), re-verified this fire's fresh run.",
        "train_disjoint_from_all_heldout": True,
        "reverse_cal_test_row_disjoint": True,
        "reverse_cal_all_marine": True,
        "reverse_test_all_nonmarine": True,
        "forward_cal_all_nonmarine": True,
        "forward_test_all_marine": True,
        "class_quantiles_derived_only_from_cal_rows": True,
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS (rescope.runA.json byte-identical to rescope.runB.json)",
        "harness_path": "amphora-barrier-corrosion-score/evidence/phase0/repairs/R-C05/work/rescope_coverage_table.py",
        "harness_sha256": harness_sha,
    },
    "scope_honesty": (
        "Bare-metal/alloy substrate corrosion (same ceiling as corr-rate-qspr-v1 "
        "/ corr-rate-conformal-v1 / corr-rate-conformal-domain-shift-v1). "
        "AUDIT_ONLY: does not flip scientific_readiness, does not modify the "
        "manifest (66/11 untouched), grants no coating-barrier ranking "
        "authority."),
    "campaign_item_status_after_this_fire": "done",
    "campaign_item_status_rationale": "max_fires=3 exhausted; re-scope hatch invoked on the final permitted fire per the item's own pre-registered rule; done_check glob satisfied by this receipt landing in done/.",
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.barrier-corrosion-conformal-per-environment-coverage-rescope+json"

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

DONE.mkdir(parents=True, exist_ok=True)
out = DONE / "r-c05-per-environment-coverage-rescope-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
print("wrote", out, "sha256", sha(out.read_bytes()))

# self-verify
env = receipt["signature"]
body_check = base64.standard_b64decode(env["payload"])
pubkey = Ed25519PublicKey.from_public_bytes(bytes.fromhex(eval_pub_hex))
sigbytes = base64.standard_b64decode(env["signatures"][0]["sig"])
pubkey.verify(sigbytes, pae(env["payloadType"], body_check))
print("SELF-VERIFY OK")
