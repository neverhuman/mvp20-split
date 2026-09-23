#!/usr/bin/env python3
"""DSSE-Ed25519-sign the R-C05 fire-2 checkpoint receipt (attempts/) for
amphora-barrier-corrosion-score. AUDIT_ONLY: signs an audit receipt under the
module's evidence/phase0/repairs/R-C05/attempts/ dir; does NOT sign a phase0
evaluation/review, does NOT promote authority, does NOT flip
scientific_readiness, does NOT modify the portfolio manifest, any locked
dataset, or any signed Phase-0 KPI."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-barrier-corrosion-score"
WORK = MOD / "evidence/phase0/repairs/R-C05/work"
ATTEMPTS = MOD / "evidence/phase0/repairs/R-C05/attempts"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

FIRE_ID = "20260812T080001-2058737-e37de5e02cd1"


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


probe_harness_sha = sha((WORK / "reweighted_probe.py").read_bytes())
mondrian_harness_sha = sha((WORK / "mondrian_domain_shift_conformal.py").read_bytes())

probe_A_bytes = (WORK / "probe.runA.json").read_bytes()
probe_B_bytes = (WORK / "probe.runB.json").read_bytes()
assert probe_A_bytes == probe_B_bytes, "reweighted-probe two-replay bytes differ"
probe = rd(WORK / "probe.runA.json")

# fire-1 artifacts (unchanged, re-cited by hash, not recomputed)
conservative_A = rd(WORK / "result.conservative.runA.json")
conservative_A_bytes = (WORK / "result.conservative.runA.json").read_bytes()
conservative_B_bytes = (WORK / "result.conservative.runB.json").read_bytes()
assert conservative_A_bytes == conservative_B_bytes, "fire-1 conservative-mondrian artifact mutated or non-replayable"
fire1_checkpoint = rd(ATTEMPTS / "r-c05-mondrian-repair-checkpoint-fire1.v1.dsse.json")
fire1_checkpoint_bytes = (ATTEMPTS / "r-c05-mondrian-repair-checkpoint-fire1.v1.dsse.json").read_bytes()
fire1_checkpoint_sha = sha(fire1_checkpoint_bytes)

rev = conservative_A["reverse_calibrate_marine_deploy_nonmarine"]["coverage"]["alpha_0.10"]
fwd = conservative_A["forward_calibrate_nonmarine_deploy_marine"]["coverage"]["alpha_0.10"]

ceiling = probe["ceiling_proof_reverse_leg"]
reweighted = probe["reweighted_conformal_probe_reverse_leg_alpha_0.10"]

body_obj = {
    "schema": "amphora.barrier-corrosion-score.corr-rate-conformal-mondrian-domain-shift-repair-checkpoint.v2",
    "module": "amphora-barrier-corrosion-score",
    "repair_item": "R-C05",
    "repair_mode": True,
    "fire_id": FIRE_ID,
    "fire_number_of_max": "2 of 3",
    "authority": "AUDIT_ONLY",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "purpose": (
        "Fire 2 of max_fires=3 on campaign item R-C05. Does NOT repeat fire "
        "1's already-tried mechanisms (naive per-class Mondrian, "
        "conservative-floor Mondrian at 8-class and 2-class granularity -- "
        "all REJECTED/INSUFFICIENT in fire 1, cited here by hash, not "
        "recomputed). Instead: (A) converts fire 1's empirical finding into "
        "a PROVABLE structural-ceiling accounting of marine-calibration mass "
        "per chloride-environment class in the reverse leg, showing the "
        "Mondrian-by-chloride-class mechanism (as pinned by this item's "
        "acceptance text) cannot reach the floor at ANY MIN_CLASS_N "
        "threshold or class granularity; (B) runs the likelihood-ratio "
        "reweighted split-conformal probe (Tibshirani et al 2019) that fire "
        "1's STATE.json recommended, as an ADDITIONAL diagnostic -- NOT a "
        "substitute for the pinned Mondrian mechanism -- to test whether the "
        "domain shift is repairable by ANY calibration-side fix."),
    "supersedes_fire1_checkpoint": {
        "path": "amphora-barrier-corrosion-score/evidence/phase0/repairs/R-C05/attempts/r-c05-mondrian-repair-checkpoint-fire1.v1.dsse.json",
        "sha256": fire1_checkpoint_sha,
        "superseded_deleted_or_modified": False,
        "reason": "Not a correction -- fire 1's checkpoint stands unmodified. This fire ADDS a structural-ceiling proof and a supplementary reweighted-conformal probe on top of fire 1's findings; both checkpoints remain valid history under REPAIR-MODE supersede-never-rewrite.",
    },
    "mondrian_mechanism_status": {
        "note": "UNCHANGED from fire 1 -- re-cited by hash, not recomputed this fire. Best variant remains conservative-floor Mondrian.",
        "conservative_floor_mondrian_forward_0.90_coverage": fwd["observed_test_coverage"],
        "conservative_floor_mondrian_reverse_0.90_coverage": rev["observed_test_coverage"],
        "reverse_n_covered": rev["n_covered"], "reverse_n_test": rev["n_test"],
        "reverse_needs_n_covered_of_2773": 2441,
        "meets_acceptance_floor_0.88_forward": fwd["meets_acceptance_floor_0.88"],
        "meets_acceptance_floor_0.88_reverse": rev["meets_acceptance_floor_0.88"],
        "artifact_cited": "amphora-barrier-corrosion-score/evidence/phase0/repairs/R-C05/work/result.conservative.runA.json",
        "artifact_sha256": sha(conservative_A_bytes),
    },
    "structural_ceiling_proof": {
        "method": (
            "Exact accounting of marine-calibration-row counts per "
            "chloride-environment class, read from the SAME held-out "
            "rows/partition as the pinned Mondrian mechanism (no new data, "
            "no recomputation of the base model or splits)."),
        "n_marine_cal_total": ceiling["n_marine_cal_total"],
        "n_nonmarine_test_total": ceiling["n_nonmarine_test_total"],
        "n_classes_total": ceiling["n_classes_total"],
        "n_classes_with_zero_marine_cal": ceiling["n_classes_with_zero_marine_cal"],
        "classes_with_zero_marine_calibration_rows": ceiling["classes_with_zero_marine_calibration_rows"],
        "per_chloride_class": ceiling["per_chloride_class"],
        "n_test_rows_forced_to_pooled_fallback_regardless_of_min_class_n": ceiling["n_test_rows_forced_to_pooled_fallback_regardless_of_min_class_n"],
        "fraction_test_rows_forced_to_pooled_fallback": ceiling["fraction_test_rows_forced_to_pooled_fallback"],
        "conclusion": ceiling["conclusion"],
        "implication_for_min_class_n_tuning": (
            "Fire 1 tried MIN_CLASS_N=5 (8-class) and an equivalent 2-class "
            "collapse; this fire's accounting shows tuning MIN_CLASS_N lower "
            "(e.g. to 1) CANNOT help, because 6 of 8 classes have a marine-"
            "calibration count of EXACTLY ZERO -- not merely below a "
            "threshold. A threshold of 0 is meaningless (there is no data to "
            "threshold). This closes off the remaining unexplored corner of "
            "the Mondrian-by-chloride-class hyperparameter space: the "
            "mechanism family named in the pre-registered acceptance is now "
            "EXHAUSTIVELY shown incapable of reaching 0.88 on the reverse "
            "leg, not just empirically short."),
    },
    "supplementary_reweighted_conformal_probe": {
        "note": "DIAGNOSTIC ONLY. Not the pre-registered mechanism; does not count toward or against the pinned Mondrian acceptance criterion.",
        "mechanism": reweighted["mechanism"],
        "domain_classifier": reweighted["domain_classifier"],
        "domain_classifier_auc_on_pooled_cal_test_covariates": 1.0,
        "observed_test_coverage": reweighted["observed_test_coverage"],
        "n_covered": reweighted["n_covered"], "n_test": reweighted["n_test"],
        "meets_acceptance_floor_0.88": reweighted["meets_acceptance_floor_0.88"],
        "mean_interval_width_log10": reweighted["mean_interval_width_log10"],
        "finding": (
            "The theoretically-correct alternative fire 1 recommended FAILS "
            "MORE SEVERELY than Mondrian (observed coverage 0.063800 vs the "
            "0.88 floor, vs Mondrian's 0.877389) -- and this is diagnostic, "
            "not a bug: the domain classifier used to build the likelihood "
            "ratio achieves AUC=1.0 distinguishing marine-calibration rows "
            "from non-marine-test rows on covariates alone, meaning the "
            "positivity/overlap assumption required by Tibshirani et al "
            "2019 weighted conformal is violated almost completely (cal and "
            "test covariate supports are nearly disjoint). This is the SAME "
            "root cause the structural-ceiling proof identifies (76% of "
            "test rows fall in chloride classes with zero marine-cal "
            "representation): the reverse-direction domain shift here is "
            "not a moderate covariate shift correctable by reweighting or "
            "finer calibration -- cal and test populations barely overlap "
            "in covariate space at all."),
        "artifact_cited": "amphora-barrier-corrosion-score/evidence/phase0/repairs/R-C05/work/probe.runA.json",
        "artifact_sha256": sha(probe_A_bytes),
        "two_replay_sha256_gate": "PASS (probe.runA.json byte-identical to probe.runB.json)",
    },
    "pre_registered_acceptance": {
        "text": "Both directions (forward and reverse) reach >= 0.88 observed coverage at the 0.90 target using a Mondrian calibrator stratified by chloride-environment class.",
        "floor": 0.88,
        "met_this_fire": False,
    },
    "verdict": {
        "outcome": "CLAIM_REFUTED",
        "repair_status": "in_progress",
        "finding": (
            "The pre-registered Mondrian-by-chloride-class mechanism remains "
            "REFUTED against its own acceptance floor (reverse leg "
            "0.877389 < 0.88, 8 rows short of 2441/2773), UNCHANGED from "
            "fire 1 (no new Mondrian variant was tried -- fire 1 already "
            "covered the viable hyperparameter space empirically; this fire "
            "closes the remaining corner analytically and shows it cannot "
            "help). The supplementary reweighted-conformal probe this fire "
            "adds shows the shortfall is NOT specific to Mondrian "
            "stratification: it is a genuine near-total covariate-support "
            "mismatch between the marine-calibration and non-marine-test "
            "populations in the reverse leg (AUC=1.0 domain separability; "
            "76% of test rows in chloride classes wholly unrepresented in "
            "marine calibration data). This is now the SECOND independent "
            "calibration-side mechanism to fail this exact acceptance "
            "floor, and the newer one fails an order of magnitude worse. "
            "This campaign item is fire 2 of max_fires=3; the pre-"
            "registered re-scope hatch becomes available at fire 3 (the "
            "final permitted fire, len(fires)>=max_fires-1=2 satisfied "
            "once this fire's record is appended). Given the exhaustive "
            "and now-provable structural incapacity of the pinned "
            "mechanism, this checkpoint recommends the final fire invoke "
            "the re-scope hatch (per-environment-class coverage table as "
            "the new claim) rather than attempt a third calibration "
            "mechanism against a shift this severe."),
    },
    "fail_closed_checks_all_variants": {
        "note": "Identical checks as fire 1 (train/cal/test disjointness, class quantiles derived only from cal rows); domain classifier for the reweighted probe trained on covariates only (X), never on y or test residuals.",
        "train_disjoint_from_all_heldout": True,
        "reverse_cal_test_row_disjoint": True,
        "reverse_cal_all_marine": True,
        "reverse_test_all_nonmarine": True,
        "class_quantiles_derived_only_from_cal_rows": True,
        "reweight_classifier_trained_on_covariates_only_no_y_no_test_residuals": True,
    },
    "state_for_next_fire": {
        "path": "amphora-barrier-corrosion-score/evidence/phase0/repairs/R-C05/work/STATE.json",
        "summary": (
            "Fire 3 (final permitted fire): the Mondrian-by-chloride-class "
            "mechanism space is now exhaustively shown incapable (empirically "
            "in fire 1, analytically in fire 2) of reaching 0.88 on the "
            "reverse leg, and the theoretically-correct alternative "
            "(reweighted conformal) fails worse due to a near-total "
            "positivity violation. Recommend invoking the pre-registered "
            "re-scope hatch: report the per-environment-class coverage "
            "table (already computed in fire 1's per_alpha class_quantiles "
            "breakdown and this fire's per_chloride_class accounting) as "
            "the new claim, honestly stating which chloride classes are "
            "covered by calibration data and which are not, rather than "
            "forcing a single pooled >=0.88 target that this domain shift "
            "structurally cannot support."),
    },
    "reproducibility": {
        "two_replay_sha256_gate_probe": "PASS (probe.runA.json byte-identical to probe.runB.json)",
        "mondrian_harness_path": "amphora-barrier-corrosion-score/evidence/phase0/repairs/R-C05/work/mondrian_domain_shift_conformal.py",
        "mondrian_harness_sha256": mondrian_harness_sha,
        "probe_harness_path": "amphora-barrier-corrosion-score/evidence/phase0/repairs/R-C05/work/reweighted_probe.py",
        "probe_harness_sha256": probe_harness_sha,
        "determinism": {"omp_num_threads": "1", "seed": 0, "no_timestamp": True, "float_round_decimals": 6},
    },
    "scope_honesty": (
        "Bare-metal/alloy substrate corrosion (same ceiling as corr-rate-qspr-v1 "
        "/ corr-rate-conformal-v1 / corr-rate-conformal-domain-shift-v1). "
        "AUDIT_ONLY: does not flip scientific_readiness, does not modify the "
        "manifest (66/11 untouched), grants no coating-barrier ranking "
        "authority."),
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
out = ATTEMPTS / "r-c05-mondrian-repair-checkpoint-fire2.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
print("wrote", out, "sha256", sha(out.read_bytes()))

# self-verify
env = receipt["signature"]
body_check = base64.standard_b64decode(env["payload"])
pub = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED)).public_key()
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
pubkey = Ed25519PublicKey.from_public_bytes(bytes.fromhex(eval_pub_hex))
sigbytes = base64.standard_b64decode(env["signatures"][0]["sig"])
pubkey.verify(sigbytes, pae(env["payloadType"], body_check))
print("SELF-VERIFY OK")
