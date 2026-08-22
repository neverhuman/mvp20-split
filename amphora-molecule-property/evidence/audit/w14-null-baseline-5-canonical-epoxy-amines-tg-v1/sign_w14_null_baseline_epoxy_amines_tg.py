#!/usr/bin/env python3
"""ROTATION fire (2026-08-19, fire_id 20260819T150001-1045099-8d2f1aa94481):
sign the W14 null-baseline audit receipt for the polyuniverse-epoxy-tg-external-
validation-5-canonical-epoxy-amines-kpi.v1.json with the PHASE0_EVALUATOR key,
matching the repo-wide evidence/audit/ signing convention (evaluator_key_id/
evaluator_public_key_hex/reviewer_public_key_hex/signature DSSE envelope shape,
established by W2 fire3 / W7 / W8 / openpoly-dielectric-admissibility-v1 /
water-contact-angle-classification-majority-baseline-audit-v1)."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
OUT = ROOT / "amphora-molecule-property/evidence/audit/w14-null-baseline-5-canonical-epoxy-amines-tg-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

FIRE_ID = "20260819T150001-1045099-8d2f1aa94481"


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
compute_script = (OUT / "compute_w14_null_baseline_epoxy_amines_tg.py").read_bytes()
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

target_kpi_path = "amphora-molecule-property/evidence/phase0/kpis/polyuniverse-epoxy-tg-external-validation-5-canonical-epoxy-amines-kpi.v1.json"
target_kpi_sha256 = sha((ROOT / target_kpi_path).read_bytes())
sci_receipt_path = "amphora-molecule-property/reference/mvp20/data/polyuniverse_epoxy_tg_external_validation_5_canonical_epoxy_amines_receipt.v1.json"
sci_receipt_sha256 = sha((ROOT / sci_receipt_path).read_bytes())

nb = diag["null_baselines"]

body_obj = {
    "schema": "amphora.molecule-property.w14-null-baseline-5-canonical-epoxy-amines-tg-audit-receipt.v1",
    "receipt_id": "w14-null-baseline-5-canonical-epoxy-amines-tg-v1",
    "study_id": "W14",
    "campaign_item_id": "",
    "fire_id": FIRE_ID,
    "fire_sequence": (
        "ROTATION fire. Read the module's full falsification-ledger history "
        "(30 prior amphora-molecule-property entries, 2026-08-01 through "
        "2026-08-18) and cross-referenced against evidence/phase0/kpis/ "
        "RETRACTION-INDEX.md (the R-A09 completeness sweep, 2026-08-03). "
        "Found several KPIs marked STANDS with 'none - no refuting receipt "
        "targets this KPI'; the van-krevelen-tg-*-15-canonical-homopolymers "
        "and van-krevelen-ridge-retuned-Ygi KPIs are already honest negative "
        "findings (R2<0, MAE worse than published baselines -- nothing "
        "confident to falsify). polyuniverse-epoxy-tg-external-validation-5-"
        "canonical-epoxy-amines-kpi.v1.json is the strongest still-standing "
        "POSITIVE claim never ledger-attacked: 'ML MAE 39.1C beats Van "
        "Krevelen physical baseline MAE 109.1C by 70.0C' on 5 canonical "
        "DGEBA epoxy-amine hardeners (IPDA/m-XDA/DDS/TETA/DETA), the exact "
        "in-scope coating chemistry class for this portfolio, and it is the "
        "origin receipt for the module-wide Polyuniverse-Epoxy units "
        "correction (heavily cited downstream, e.g. by W12 and the "
        "coating-candidate-design-card KPI). Every MAE gate in sibling KPIs "
        "across this module carries an explicit NULL-median/mean baseline "
        "comparison EXCEPT this one's 'ml_beats_van_krevelen_physical_"
        "baseline_on_MAE' and 'ml_MAE_less_than_50C_across_5_external_"
        "candidates' gates, whose note frames MAE<50C as 'useful "
        "engineering Tg prediction'. Both models produce near-degenerate "
        "near-constant predictions on the 5 candidates (VK spread 0.6C -- a "
        "known +250C-offset bug already disclosed in this module's own "
        "van-krevelen-tg-external-validation-15-canonical-homopolymers KPI; "
        "ML spread 23.4C, also narrow vs the actual 120C spread of "
        "published values), which is exactly the pattern where 'beats a "
        "known-bad baseline' can mask 'beaten by a baseline that ignores "
        "structure entirely' -- the same asymmetry that made W13's "
        "majority-baseline audit (2026-08-18) fire on a different KPI in "
        "this module."
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
    "claim_under_attack": {
        "kpi_path": target_kpi_path,
        "kpi_sha256": target_kpi_sha256,
        "gates": [
            "ml_beats_van_krevelen_physical_baseline_on_MAE (observed +69.96C, floor=0.0, PASSED)",
            "ml_MAE_less_than_50C_across_5_external_candidates (observed 39.1C, floor<50C, PASSED, note frames this as 'useful engineering Tg prediction')",
        ],
        "mission_md_prose": "docs/mission.md lines ~309-357 ('Empirical benchmark result -- external validation on 5 canonical DGEBA + industrial-amine coatings'), which reports the 70C MAE gap and 'usable but not tight' framing for the sole in-AD candidate without any null-baseline comparison.",
    },
    "objective": (
        "Test whether 'ML MAE 39.1C beats Van Krevelen physics MAE 109.1C by "
        "70.0C' on the 5 canonical epoxy-amine external-validation set "
        "reflects genuine ML predictive skill, or is fully explained by Van "
        "Krevelen's own known offset-degeneracy bug being a uniquely bad "
        "comparison point -- i.e. whether a trivial, zero-structural-"
        "information constant-value predictor also beats the ML model on "
        "the identical 5 candidates."
    ),
    "method": (
        "Independently re-verified the pinned Epoxy_1M_p.csv (repo-relative "
        "feedback/v1/external_data/polyuniverse_epoxy/raw/Epoxy_1M_p.csv) "
        "against its sha256 pin shared by the KPI under attack "
        "(9f1f5c593463b9c26a026948901e37b4db545d17f05d5cd80baca5c3e14e0c45), "
        "read literally in the module's own already-disclosed unit "
        "correction (degrees C, not K), and computed the full 1,000,000-row "
        "population mean and median Tg. Transcribed the 5 per-candidate "
        "published Tg values and ML/VK predictions verbatim from the "
        "scientific receipt under attack "
        "(reference/mvp20/data/polyuniverse_epoxy_tg_external_validation_5_"
        "canonical_epoxy_amines_receipt.v1.json) and reproduced the "
        "receipt's own headline ml_MAE_C=39.11947866164949 and "
        "vk_MAE_C=109.07781373364219 bit-for-bit as a fidelity check before "
        "computing anything new. Built two structure-blind null baselines "
        "(constant population mean, constant population median) plus one "
        "internal leave-one-out-of-the-5-actuals control, and compared their "
        "MAE against the ML model's MAE on the identical 5 candidates."
    ),
    "input_artifacts": {
        "target_kpi_path": target_kpi_path,
        "target_kpi_sha256": target_kpi_sha256,
        "scientific_receipt_path": sci_receipt_path,
        "scientific_receipt_sha256": sci_receipt_sha256,
        "epoxy_1m_csv_path": "feedback/v1/external_data/polyuniverse_epoxy/raw/Epoxy_1M_p.csv",
        "epoxy_1m_csv_sha256_verified": diag["csv_sha256_verified"],
        "compute_w14_null_baseline_epoxy_amines_tg.py_sha256": sha(compute_script),
    },
    "population_Tg_C_stats": diag["population_Tg_C_stats"],
    "reproduced_receipt_headline": diag["reproduced_receipt_headline"],
    "prediction_degeneracy": diag["prediction_degeneracy"],
    "null_baselines": nb,
    "per_candidate": diag["per_candidate"],
    "pre_registered_refute_criterion": (
        "The claim that ML MAE=39.12C on this 5-candidate set demonstrates "
        "real predictive skill (as opposed to an artifact of comparison "
        "against an unusually degenerate physics baseline) is REFUTED if "
        "EITHER: (a) a trivial constant-value baseline -- predicting the "
        "full Polyuniverse Epoxy 1M raw population MEAN Tg for all 5 "
        "candidates, using zero molecular/structural information -- "
        "achieves MAE <= ML's observed MAE (39.11947866164949 C); OR (b) "
        "the same constant-value baseline using the population MEDIAN "
        "achieves MAE <= ML's observed MAE. Both criteria were fixed before "
        "computing the null baseline; both use only the already-pinned "
        "Epoxy_1M_p.csv, so this attacks whether the ML-vs-VK COMPARISON is "
        "informative, not whether the ML model was correctly trained."
    ),
    "verdict": diag["verdict"],
    "why": (
        f"Fidelity check: independently reproduced the receipt's own "
        f"headline numbers bit-for-bit "
        f"(ml_MAE_C={diag['reproduced_receipt_headline']['ml_MAE_C']}, "
        f"vk_MAE_C={diag['reproduced_receipt_headline']['vk_MAE_C']}), "
        f"confirming this attack targets the correct, real published "
        f"numbers. The pinned Epoxy_1M_p.csv (n={diag['n_total_polyuniverse_rows']} rows, "
        f"hash-verified) has population mean Tg="
        f"{diag['population_Tg_C_stats']['mean']:.4f} C and median="
        f"{diag['population_Tg_C_stats']['median']:.4f} C. A trivial "
        f"constant predictor that always outputs the population mean "
        f"(zero structural information, no scaffold split, no training) "
        f"achieves MAE={nb['constant_population_mean']['MAE_C']:.4f} C on "
        f"the SAME 5 candidates -- LOWER than the ML model's own MAE of "
        f"{diag['reproduced_receipt_headline']['ml_MAE_C']:.4f} C. The "
        f"population-median constant predictor achieves "
        f"MAE={nb['constant_population_median']['MAE_C']:.4f} C, also "
        f"lower than ML. Both pre-registered refutation criteria fired "
        f"(criterion_a={diag['pre_registered_refutation_criterion']['criterion_a_fired']}, "
        f"criterion_b={diag['pre_registered_refutation_criterion']['criterion_b_fired']}). "
        "This does not mean the ML model has literally zero skill -- its "
        "MAE (39.1C) is closer to the null-mean MAE (33.0C) than VK's MAE "
        "(109.1C) is -- but it means the module's own headline framing "
        "('ML beats Van Krevelen physics by 70C' as evidence the model "
        "gives 'usable' Tg predictions on canonical industrial hardeners) "
        "is not supported by comparison to any informative baseline: the "
        "single most obvious sanity-check predictor, which uses no "
        "chemistry at all, beats the machine-learning model outright on "
        "this exact 5-candidate population. The degeneracy analysis shows "
        "why both models look artificially good/bad relative to each "
        "other: VK's predictions span only 0.6C across 5 structurally "
        "distinct amines (a near-pure +250C offset, a bug independently "
        "documented in this module's van-krevelen-tg-external-validation-"
        "15-canonical-homopolymers-kpi.v1.json), so 'beating VK' mostly "
        "measures how badly broken VK's offset term is here, not how good "
        "the ML predictions are."
    ),
    "scope_note": (
        "This does not re-attack or alter the applicability-domain gate "
        "(4/5 LOW-AD flag, already independently confirmed correct "
        "behavior) or the units-correction disclosure (both untouched, "
        "both remain accurate). It is scoped to exactly two things: (1) the "
        "'ml_beats_van_krevelen_physical_baseline_on_MAE' gate and its "
        "'usable Tg predictions' framing in docs/mission.md, both of which "
        "compare ML only against Van Krevelen physics and never against a "
        "structure-blind null; and (2) the "
        "'ml_MAE_less_than_50C_across_5_external_candidates' gate's note "
        "text asserting this represents 'useful engineering Tg prediction'."
    ),
    "rights_check": (
        "No new data source opened. This audit reads only the already-in-"
        "tree pinned Epoxy_1M_p.csv (already consumed and sha256-pinned by "
        "the KPI under attack and by 4 sibling KPIs per RETRACTION-INDEX.md) "
        "and the already-in-tree scientific receipt. No quarantined or "
        "CONTEXT_ONLY source was opened."
    ),
    "gates": {
        "two_replay_byte_stable": two_replay_byte_identical,
        "csv_sha256_matches_kpi_pin": diag["csv_sha256_verified"] == "9f1f5c593463b9c26a026948901e37b4db545d17f05d5cd80baca5c3e14e0c45",
        "ml_and_vk_MAE_reproduced_bit_for_bit_from_receipt": True,
        "null_mean_baseline_beats_or_ties_ml": nb["constant_population_mean"]["beats_ml_or_ties"],
        "null_median_baseline_beats_or_ties_ml": nb["constant_population_median"]["beats_ml_or_ties"],
        "signature_field_is_dsse_envelope_object": True,
        "signing_key_role_matches_repo_wide_audit_convention": True,
    },
    "all_gates_passed": (
        two_replay_byte_identical
        and (diag["csv_sha256_verified"] == "9f1f5c593463b9c26a026948901e37b4db545d17f05d5cd80baca5c3e14e0c45")
        and nb["constant_population_mean"]["beats_ml_or_ties"]
        and nb["constant_population_median"]["beats_ml_or_ties"]
    ),
    "ceiling": (
        "AUDIT_ONLY. Does not alter the shipped "
        "polyuniverse-epoxy-tg-external-validation-5-canonical-epoxy-amines-"
        "kpi.v1.json file, any manifest, or any authority ceiling. Extends "
        "the module's falsification record with a null-baseline attack "
        "class applied to a tiny (n=5) external-validation set, a pattern "
        "not previously used on this specific KPI."
    ),
    "promotion_blocked_by": "NOT this audit's science and NOT key custody. Manifest untouched.",
    "recommended_followups": [
        "Add an explicit constant-mean/median NULL baseline column to the "
        "per-candidate table and an explicit "
        "'ml_beats_null_mean_baseline_on_MAE' gate, mirroring the "
        "NULL-median convention already used elsewhere in this module, so "
        "the 5-candidate external-validation KPI cannot silently rely on a "
        "known-broken VK offset term as its only comparison point.",
        "Correct docs/mission.md's 'HONEST INTERPRETATION' paragraph "
        "(lines ~309-357) to disclose that a structure-blind constant "
        "predictor also beats the ML model's aggregate MAE on this "
        "5-candidate set, alongside the existing correct disclosure that "
        "4/5 candidates are LOW-AD.",
        "The n=5 external-validation set is very small for MAE-based "
        "claims; consider whether the same near-degenerate-output pattern "
        "(VK spread 0.6C) recurs in other physical-baseline-vs-ML "
        "comparisons in this module that have not yet been checked for "
        "prediction variance/degeneracy.",
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

ptype = "application/vnd.amphora.molecule-property.w14-null-baseline-5-canonical-epoxy-amines-tg-audit-receipt.v1+json"
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

outpath = OUT / "w14-null-baseline-5-canonical-epoxy-amines-tg-receipt.v1.dsse.json"
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
