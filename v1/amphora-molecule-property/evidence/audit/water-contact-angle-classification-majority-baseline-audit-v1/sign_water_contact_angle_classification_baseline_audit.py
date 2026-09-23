#!/usr/bin/env python3
"""ROTATION fire (2026-08-18, fire_id 20260818T090001-1591292-56d54e59d5a0):
sign the water-contact-angle hydrophobic-classification majority-baseline
audit receipt with the PHASE0_EVALUATOR key, matching the repo-wide
evidence/audit/ signing convention (evaluator_key_id/evaluator_public_key_hex/
reviewer_public_key_hex/signature DSSE envelope shape, established by
W2 fire3 / W7 / W8 / openpoly-dielectric-admissibility-v1 /
openpoly-dielectric-macro-bisection-v1)."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
OUT = ROOT / "amphora-molecule-property/evidence/audit/water-contact-angle-classification-majority-baseline-audit-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

FIRE_ID = "20260818T090001-1591292-56d54e59d5a0"


def sha(b):
    return hashlib.sha256(b).hexdigest()


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


diag = json.loads((OUT / "diagnostic.canonical.json").read_text())
compute_script = (OUT / "compute_water_contact_angle_classification_baseline_audit.py").read_bytes()
diag_canonical = (OUT / "diagnostic.canonical.json").read_bytes()
diag_runB = (OUT / "diagnostic.runB.json").read_bytes()
two_replay_byte_identical = diag_canonical == diag_runB

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"

rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"

trust = json.loads(TRUST.read_text())
by_role = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == by_role.get("PHASE0_EVALUATOR", {}).get("key_id"))
rev_pin = (rev_key_id == by_role.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))
assert eval_pin, "evaluator key_id does not match pinned trust-store PHASE0_EVALUATOR entry"
assert rev_pin, "reviewer key_id does not match pinned trust-store PHASE0_INTERNAL_REVIEWER entry"

real = diag["real_data_result"]
sc_informative = diag["self_check_synthetic_informative_classifier"]
sc_null = diag["self_check_pure_majority_guess"]

body_obj = {
    "schema": "amphora.molecule-property.water-contact-angle-hydrophobic-classification-majority-baseline-audit-receipt.v1",
    "receipt_id": "water-contact-angle-classification-majority-baseline-audit-v1",
    "study_id": diag["study_id"],
    "campaign_item_id": "",
    "fire_id": FIRE_ID,
    "fire_sequence": (
        "ROTATION fire. Read the module's full falsification-ledger history "
        "(46 prior amphora-molecule-property entries, 2026-08-01 through "
        "2026-08-17) and cross-referenced against evidence/phase0/kpis/ "
        "(21 KPI files) and RETRACTION-INDEX.md. Identified "
        "openpoly-water-contact-angle-ml-baseline-kpi.v1.json as never "
        "before ledger-attacked (unlike its sibling openpoly-dielectric-"
        "constant-ml-baseline-kpi.v1.json, which has been macro-bisected, "
        "admissibility-audited, and physically-audited three times). Read "
        "the KPI and its docs/mission.md narrative in full: 9 of its 10 "
        "deterministic gates are honestly self-critical (LOSO-CV positive, "
        "holdout MAE explicitly documented as WORSE than NULL), but gate "
        "10 (hydrophobic_classification_accuracy_at_least_0_7, floor=0.7, "
        "PASSED at 0.711) and mission.md's SCIENTIFIC INTERPRETATION point "
        "3 ('Hydrophobic-vs-hydrophilic classification works... a useful "
        "screening signal') assert a working classifier with no comparison "
        "to a trivial baseline -- unlike this KPI's OWN MAE metrics, which "
        "all carry an explicit NULL-median baseline. That asymmetry is the "
        "attack surface: an imbalanced binary target (27/38 test molecules "
        "are NOT hydrophobic) can pass a bare accuracy floor by base rate "
        "alone."
    ),
    "authority": "AUDIT_ONLY",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "promotes_nothing": True,
    "modifies_no_live_config": True,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "module": "amphora-molecule-property",
    "claim_under_attack": diag["claim_under_attack"],
    "objective": (
        "Test whether the KPI's hydrophobic_classification_accuracy_at_least_0_7 "
        "gate (PASSED, 0.711 >= 0.7) and the mission.md claim that this "
        "classification 'works' and is 'a useful screening signal' reflect "
        "genuine structure-to-property signal, or are fully explained by "
        "class-imbalance base rate (predicting the majority class for every "
        "molecule)."
    ),
    "method": diag["method"],
    "input_artifacts": {
        "target_kpi_path": diag["claim_under_attack"]["kpi_path"],
        "target_kpi_sha256": diag["claim_under_attack"]["kpi_sha256"],
        "scientific_receipt_path": diag["scientific_receipt_path"],
        "scientific_receipt_sha256_observed": diag["scientific_receipt_sha256_observed"],
        "scientific_receipt_sha256_pinned_in_kpi": diag["scientific_receipt_sha256_pinned_in_kpi"],
        "scientific_receipt_sha256_match": diag["scientific_receipt_sha256_match"],
        "n_held_out_test_records_used": diag["n_held_out_test_records"],
        "compute_water_contact_angle_classification_baseline_audit.py_sha256": sha(compute_script),
    },
    "real_data_result": real,
    "self_check_synthetic_informative_classifier": sc_informative,
    "self_check_pure_majority_guess": sc_null,
    "pre_registered_refute_criterion": (
        "The classification gate/claim is REFUTED as evidence of a working "
        "classifier if the model's holdout accuracy is bitwise-identical to "
        "the trivial majority-class-only baseline accuracy on the SAME test "
        "set, AND a two-sided Fisher exact test on the prediction-vs-actual "
        "2x2 table fails to reject independence at alpha=0.05 (i.e. the "
        "predictions are not statistically distinguishable from being drawn "
        "independently of the true label)."
    ),
    "verdict": "CLAIM_REFUTED",
    "why": (
        "Independently reconstructing the confusion matrix from the "
        "scientific receipt's own 38 held_out_test_records reproduces the "
        "published tp=1/fp=1/fn=10/tn=26 and accuracy=0.7105263157894737 "
        "exactly (rederived_accuracy_matches_kpi_published_accuracy=true), "
        "confirming the published numbers are real, not fabricated. But "
        f"the model's accuracy ({real['model_accuracy']:.10f}) is bitwise-"
        f"identical to the trivial always-predict-not-hydrophobic majority "
        f"baseline ({real['trivial_majority_class_baseline_accuracy']:.10f}) "
        "on the identical 38-molecule test set: "
        "model_accuracy_equals_majority_baseline_bitwise=true, "
        f"self_check_pure_majority_guess confirms this is not "
        "coincidental proximity but exact numerical equivalence to a rule "
        "that ignores molecular structure entirely. Balanced accuracy is "
        f"{real['balanced_accuracy']:.4f} (chance=0.5000, only "
        f"+{real['balanced_accuracy_minus_chance_0.5']:.4f} above chance); "
        f"Matthews correlation coefficient is {real['matthews_corrcoef']:.4f} "
        "(weak); the two-sided Fisher exact test on the prediction-vs-"
        f"actual table gives p={real['fisher_exact_two_sided_p_value_prediction_independent_of_actual']:.4f}, "
        "far from significant at alpha=0.05 -- the null hypothesis that "
        "predictions are independent of true class CANNOT be rejected. "
        "recall on the positive (hydrophobic) class is 0.091 (1 of 11 true "
        "hydrophobic polymers correctly flagged); precision=0.5 is driven "
        "by a single true positive against a single false positive. The "
        "self-check against a synthetic genuinely-informative classifier "
        "(same n=38, same 11/27 base rate, tp=8/fp=3/fn=3/tn=24) confirms "
        "the SAME checker correctly detects real skill when present "
        "(accuracy 0.842 clearly exceeds the 0.711 majority baseline, "
        "Fisher p=0.0004, balanced accuracy 0.808) -- so this is not a "
        "vacuous attack that would fire REFUTED on any input. The "
        "mission.md claim ('classification works... a useful screening "
        "signal... often what actually matters') and the KPI gate's PASSED "
        "status both overstate what the held-out evidence supports: on the "
        "single evaluation this KPI actually reports (the 38-molecule "
        "scaffold-safe holdout), the classifier's decisions carry no "
        "statistically demonstrable information about true hydrophobicity "
        "beyond the base rate."
    ),
    "scope_note": (
        "This does NOT refute the KPI's LOSO-CV regression result "
        "(best_LOSO_result R2=+0.0781, MAE beats NULL by 6.0% across 66 "
        "folds) or the honestly-disclosed holdout regression underperformance "
        "(both left untouched, both already correctly characterized in "
        "mission.md as a 'MIXED FINDING'). It is scoped to ONE derived "
        "artifact: the theta>90degC binary hydrophobic/hydrophilic "
        "classification gate and its mission.md narrative, which is the "
        "only part of this KPI asserting a working practical decision tool "
        "('hydrophobic candidate: yes/no') without a null-baseline "
        "comparison."
    ),
    "rights_check": (
        "No new data source opened. This audit reads only the already-in-"
        "tree scientific receipt and KPI files already consumed and pinned "
        "by sha256 in the module. No quarantined or CONTEXT_ONLY source was "
        "opened."
    ),
    "gates": {
        "two_replay_byte_stable": two_replay_byte_identical,
        "scientific_receipt_sha256_matches_kpi_pin": diag["scientific_receipt_sha256_match"],
        "rederived_confusion_matrix_matches_kpi_published": real["rederived_confusion_matrix_matches_kpi_published_confusion_matrix"],
        "rederived_accuracy_matches_kpi_published": real["rederived_accuracy_matches_kpi_published_accuracy"],
        "self_check_confirms_checker_detects_genuine_informativeness": sc_informative["detected_as_informative"],
        "self_check_confirms_real_result_equals_pure_majority_guess": sc_null["real_vs_null_guess_accuracy_identical"],
        "signature_field_is_dsse_envelope_object": True,
        "signing_key_role_matches_repo_wide_audit_convention": True,
    },
    "all_gates_passed": (
        two_replay_byte_identical
        and diag["scientific_receipt_sha256_match"]
        and real["rederived_confusion_matrix_matches_kpi_published_confusion_matrix"]
        and real["rederived_accuracy_matches_kpi_published_accuracy"]
        and sc_informative["detected_as_informative"]
        and sc_null["real_vs_null_guess_accuracy_identical"]
    ),
    "ceiling": (
        "AUDIT_ONLY. Does not alter the shipped "
        "openpoly-water-contact-angle-ml-baseline-kpi.v1.json file, any "
        "manifest, or any authority ceiling. Extends the module's "
        "falsification record with a new attack class (majority-class-"
        "baseline / statistical-significance audit of an imbalanced binary "
        "classification gate) not previously used in this module's ledger."
    ),
    "promotion_blocked_by": "NOT this audit's science (all gates pass) and NOT key custody. Manifest untouched.",
    "recommended_followups": [
        "Repair the gate definition: replace the bare "
        "hydrophobic_classification_accuracy_at_least_0_7 floor with a "
        "chance-corrected metric (balanced accuracy or MCC) plus an "
        "explicit majority-baseline comparison, mirroring the null-median "
        "pattern already used for the MAE gates in this same KPI.",
        "Correct docs/mission.md SCIENTIFIC INTERPRETATION point 3 to stop "
        "asserting the classifier 'works' as a screening signal; either "
        "retract the framing or re-run with a recall-sensitive threshold "
        "(e.g. cost-weighted or precision-recall-optimized cutoff) and "
        "report against the majority baseline honestly.",
        "The same base-rate-vs-floor gate pattern may exist on other "
        "binary/threshold gates elsewhere in this module's 21 KPI files -- "
        "worth a follow-up sweep for any other floor-only accuracy gate "
        "lacking a baseline comparison.",
    ],
    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under evidence/audit/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin),
    },
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER",
        "key_id": rev_key_id,
        "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin),
        "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed.",
    },
}

body1 = json.dumps(body_obj, indent=2, sort_keys=True).encode()
body2 = json.dumps(dict(body_obj), indent=2, sort_keys=True).encode()
assert body1 == body2, "receipt body non-deterministic"
(OUT / "receipt_body.canonical.json").write_bytes(body1)
(OUT / "receipt_body.runB.json").write_bytes(body2)

ptype = "application/vnd.amphora.molecule-property.water-contact-angle-hydrophobic-classification-majority-baseline-audit-receipt.v1+json"
sig = eval_sk.sign(pae(ptype, body1))
envelope = {
    "payload": base64.standard_b64encode(body1).decode(),
    "payloadType": ptype,
    "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}],
}

receipt = {
    "evaluator_key_id": eval_key_id,
    "evaluator_public_key_hex": eval_pub_hex,
    "reviewer_public_key_hex": rev_pub_hex,
    "signature": envelope,
}

outpath = OUT / "water-contact-angle-classification-majority-baseline-audit-receipt.v1.dsse.json"
outpath.write_text(json.dumps(receipt, indent=2, sort_keys=True))

written = json.loads(outpath.read_text())
sig_env = written["signature"]
payload = base64.standard_b64decode(sig_env["payload"])
sig_bytes = base64.standard_b64decode(sig_env["signatures"][0]["sig"])
keyid = sig_env["signatures"][0]["keyid"]
trust_pub_hex = by_role["PHASE0_EVALUATOR"]["public_key_hex"]
assert keyid == by_role["PHASE0_EVALUATOR"]["key_id"]
Ed25519PublicKey.from_public_bytes(bytes.fromhex(trust_pub_hex)).verify(
    sig_bytes, pae(sig_env["payloadType"], payload))
assert payload == body1

print("WROTE", outpath)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("two_replay_byte_identical", two_replay_byte_identical)
print("independent_reverify_against_trust_store_OK", True)
print("all_gates_passed", json.loads(body1)["all_gates_passed"])
print("verdict", json.loads(body1)["verdict"])
print("envelope_sha256", sha(outpath.read_bytes()))
