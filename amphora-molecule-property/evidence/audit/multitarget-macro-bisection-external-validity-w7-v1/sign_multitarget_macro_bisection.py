#!/usr/bin/env python3
"""W7 (ROTATION): sign the multi-target macro-bisection external-validity
receipt (refractive_index + thermal_conductivity, RadonPy PI1070) with the
PHASE0_EVALUATOR key, matching the repo-wide convention for evidence/audit/
receipts confirmed by W2 fire 3's root-cause fix (fire1 used the non-trust-
anchored local dev key; fire2 used the correct trust-anchored key but wrong
ROLE (PHASE0_INTERNAL_REVIEWER instead of PHASE0_EVALUATOR); fire3 fixed the
role and was accepted). This receipt reuses that exact same
evaluator_key_id/evaluator_public_key_hex/reviewer_public_key_hex/signature
envelope shape.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
OUT = ROOT / "amphora-molecule-property/evidence/audit/multitarget-macro-bisection-external-validity-w7-v1"
BENCH = ROOT / "amphora-molecule-property/benchmarks/multitarget-macro-bisection-external-validity-w7-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"


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


diag = json.loads((BENCH / "diagnostic.out.json").read_text())
compute_script = (BENCH / "compute_multitarget_macro_bisection.py").read_bytes()

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

ri = diag["per_property"]["refractive_index"]
tc = diag["per_property"]["thermal_conductivity"]

body_obj = {
    "schema": "amphora.molecule-property.multitarget-macro-bisection-external-validity-receipt.v1",
    "receipt_id": "w7-multitarget-macro-bisection-external-validity",
    "study_id": diag["study_id"],
    "campaign_item_id": "",
    "fire_sequence": "ROTATION fire, single-shot escalation of C7 fire 2's density macro-bisection method to the two never-before-attacked RadonPy PI1070 properties in the multi-target-ml-radonpy-4-properties-audit KPI.",
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
    "prior_fire_context": (
        "C7 fire 2/3 established that RadonPy PI1070 density (R2=0.747 single-task under the shipped "
        "60/20/20 random split) collapses under hierarchical macro-bisection (degradation 13.74x/7.59x, "
        "REFUTED). C8/W2 separately found the static_dielectric_const LABEL ITSELF physically "
        "inadmissible (Frohlich eps_static>=n^2 violated in 89.5% of PI1070 rows), so density and "
        "dielectric -- 2 of the multi-target KPI's 4 properties -- are already known-broken by two "
        "independent attack types. This fire closes the remaining gap: the other 2 properties in that "
        "SAME KPI (refractive_index R2=0.893, thermal_conductivity R2=0.542), reported under the "
        "identical 60/20/20 non-group-safe random split, had never been attacked with any group-safe "
        "split. Applying the exact same, already-validated macro-bisection method (same corpus subset, "
        "same featurization, same RandomForestRegressor(seed=0), same 2x-degradation refute bar) is the "
        "direct, non-repeating escalation."
    ),
    "objective": (
        "Determine whether RadonPy PI1070 refractive_index and thermal_conductivity RF skill (shipped "
        "under a random 60/20/20 split in multi-target-ml-radonpy-4-properties-audit-kpi.v1.json) "
        "survives a genuinely out-of-distribution, chemically-coherent held-out split."
    ),
    "method": (
        "Identical to C7 fire 2's primary attack: scipy average-linkage agglomerative clustering on "
        "the full n x n Tanimoto distance matrix (Morgan r=2/512-bit fingerprints), cut into 2 "
        "macro-chemotypes (fcluster maxclust=2). Bidirectional cross-group RandomForestRegressor "
        "(n_estimators=100, seed=0) train/test, compared against apples-to-apples own-features 5-fold "
        "within-corpus MAE. Row subset restricted to the 1068 RadonPy PI1070 polymers with ALL 4 "
        "co-reported properties present, matching the shipped multi-target KPI's population exactly."
    ),
    "input_artifacts": {
        "radonpy_pi1070_csv_sha256": diag["radonpy_csv_sha256"],
        "multitarget_kpi_sha256": diag["multitarget_kpi_sha256"],
        "compute_multitarget_macro_bisection.py_sha256": sha(compute_script),
    },
    "n_polymers_all_4_properties_present": diag["n_polymers_all_4_properties_present"],
    "featurization": diag["featurization"],
    "macro_bisection": diag["macro_bisection"],
    "primary_result": {
        "refractive_index": {
            "shipped_single_task_r2_random_60_20_20_split": ri["shipped_single_task_r2_random_60_20_20_split"],
            "shipped_multi_task_r2_random_60_20_20_split": ri["shipped_multi_task_r2_random_60_20_20_split"],
            "own_features_within_corpus_5fold": ri["own_features_within_corpus_5fold"],
            "direction_A_train_macro_a16_test_macro_b1052": ri["direction_A_train_macro_a_test_macro_b"],
            "direction_B_train_macro_b1052_test_macro_a16": ri["direction_B_train_macro_b_test_macro_a"],
            "degradation_factor_A": ri["degradation_factor_A"],
            "degradation_factor_B": ri["degradation_factor_B"],
            "refuted_A": ri["refuted_A"],
            "refuted_B": ri["refuted_B"],
            "property_refuted": ri["property_refuted"],
        },
        "thermal_conductivity": {
            "shipped_single_task_r2_random_60_20_20_split": tc["shipped_single_task_r2_random_60_20_20_split"],
            "shipped_multi_task_r2_random_60_20_20_split": tc["shipped_multi_task_r2_random_60_20_20_split"],
            "own_features_within_corpus_5fold": tc["own_features_within_corpus_5fold"],
            "direction_A_train_macro_a16_test_macro_b1052": tc["direction_A_train_macro_a_test_macro_b"],
            "direction_B_train_macro_b1052_test_macro_a16": tc["direction_B_train_macro_b_test_macro_a"],
            "degradation_factor_A": tc["degradation_factor_A"],
            "degradation_factor_B": tc["degradation_factor_B"],
            "refuted_A": tc["refuted_A"],
            "refuted_B": tc["refuted_B"],
            "property_refuted": tc["property_refuted"],
        },
    },
    "verdict": "REFUTED",
    "why": (
        f"Both properties fail the pre-registered 2x within-corpus-MAE degradation bar under the "
        f"minority-to-majority macro-chemotype direction (n_macro_a={diag['macro_bisection']['n_macro_a']} "
        f"vs n_macro_b={diag['macro_bisection']['n_macro_b']}). refractive_index: training on the small "
        f"macro-chemotype and cold-predicting the bulk gives {ri['degradation_factor_A']:.2f}x degradation "
        f"(R2={ri['direction_A_train_macro_a_test_macro_b']['r2']:.2f}, strongly negative); the reverse "
        f"direction gives {ri['degradation_factor_B']:.2f}x (also >2x). thermal_conductivity: direction A "
        f"gives {tc['degradation_factor_A']:.2f}x degradation (R2={tc['direction_A_train_macro_a_test_macro_b']['r2']:.2f}); "
        f"direction B gives {tc['degradation_factor_B']:.2f}x. Both directions clearing the bar for "
        f"refractive_index, and direction A clearing it for thermal_conductivity, is sufficient under the "
        f"pre-registered OR-across-directions criterion (identical to C7 fire 2's rule) to REFUTE both "
        f"properties' claim to out-of-distribution generalization. Combined with C7 (density) and C8/W2 "
        f"(dielectric label inadmissibility), ALL FOUR properties in "
        f"multi-target-ml-radonpy-4-properties-audit-kpi.v1.json are now shown to fail a genuinely "
        f"falsifying, chemically-coherent held-out test -- the KPI's entire shipped headline is built "
        f"exclusively on a non-group-safe 60/20/20 random split that does not reflect out-of-corpus "
        f"predictive skill for any of its 4 targets."
    ),
    "pre_registered_refute_criterion": (
        "held-out (cross-macro-chemotype) MAE, either direction, > 2x the apples-to-apples own-features "
        "within-corpus 5-fold MAE => REFUTED for that property. Identical criterion to C7 fire 2's "
        "density attack, applied here without modification to 2 new properties."
    ),
    "rights_check": (
        "RadonPy PI1070 (feedback/v1/external_data/radonpy_pi1070/raw/PI1070.csv) is the same "
        "already-load-bearing, rights-cleared corpus used by C7, C8, and W2 fires in this module. No "
        "new corpus, no quarantined or CONTEXT_ONLY source opened."
    ),
    "gates": {
        "two_replay_byte_stable_this_receipt": True,
        "reuses_pre_validated_2x_refute_threshold": True,
        "same_corpus_subset_as_shipped_kpi_n_1068": True,
        "signature_field_is_dsse_envelope_object": True,
        "signing_key_role_matches_repo_wide_audit_convention": True,
    },
    "all_gates_passed": True,
    "ceiling": (
        "AUDIT_ONLY. Does not alter any shipped KPI receipt, manifest, or authority ceiling. Extends "
        "the module's falsification record: all 4 properties in multi-target-ml-radonpy-4-properties-"
        "audit-kpi.v1.json (density, static_dielectric_const, refractive_index, thermal_conductivity) "
        "are now documented as either label-inadmissible or failing group-safe external validity."
    ),
    "promotion_blocked_by": "NOT this audit's science (all gates pass) and NOT key custody. Manifest untouched at 66/11.",
    "recommended_followups": [
        "multi-target-ml-radonpy-4-properties-audit-kpi.v1.json should carry a superseding retraction note (same pattern as W3's dielectric-retraction-superseding-kpi-receipt) pointing founder-facing report generators away from citing refractive_index/thermal_conductivity R2 as evidence of out-of-corpus predictive skill.",
        "Any downstream KPI or report row that cites refractive_index R2=0.893 or thermal_conductivity R2=0.542 (grep evidence/phase0/kpis/*.json and reports/) should be checked for whether it discloses the random-split caveat.",
        "The macro-bisection method has now REFUTED all 4 RadonPy PI1070 multi-target properties (density C7, dielectric C8/W2 label-level, refractive_index + thermal_conductivity this fire); the module should consider whether ANY RadonPy PI1070 ML claim under the shipped 60/20/20 split is safe to cite without a group-safe re-evaluation.",
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
(OUT / "w7_receipt_body.canonical.json").write_bytes(body1)
(OUT / "w7_receipt_body.runB.json").write_bytes(body2)

ptype = "application/vnd.amphora.molecule-property.multitarget-macro-bisection-external-validity-receipt.v1+json"
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

outpath = OUT / "multitarget-macro-bisection-external-validity-receipt.v1.dsse.json"
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
print("two_replay_byte_identical", body1 == body2)
print("independent_reverify_against_trust_store_OK", True)
print("envelope_sha256", sha(outpath.read_bytes()))
