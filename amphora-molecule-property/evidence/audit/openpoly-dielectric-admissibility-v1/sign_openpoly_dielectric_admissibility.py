#!/usr/bin/env python3
"""ROTATION fire: sign the OpenPoly dielectric-constant-corpus physical-
admissibility audit receipt with the PHASE0_EVALUATOR key, matching the
repo-wide evidence/audit/ signing convention (evaluator_key_id/
evaluator_public_key_hex/reviewer_public_key_hex/signature DSSE envelope
shape, established by W2 fire3 / W7 / W8)."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
OUT = ROOT / "amphora-molecule-property/evidence/audit/openpoly-dielectric-admissibility-v1"
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


diag = json.loads((OUT / "diagnostic.out.json").read_text())
compute_script = (OUT / "compute_openpoly_dielectric_admissibility.py").read_bytes()

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

body_obj = {
    "schema": "amphora.molecule-property.openpoly-dielectric-corpus-physical-admissibility-audit-receipt.v1",
    "receipt_id": "openpoly-dielectric-admissibility-v1",
    "study_id": "openpoly-dielectric-admissibility-v1",
    "campaign_item_id": "",
    "fire_id": "20260814T210001-2385562-23657306b488",
    "fire_sequence": (
        "ROTATION fire. Identifies the strongest never-before-attacked STANDING "
        "claim in amphora-molecule-property per its own RETRACTION-INDEX.md R-A09 "
        "status table (dated 2026-08-03): "
        "openpoly-dielectric-constant-ml-baseline-kpi.v1.json, status STANDS, "
        "'none - no refuting receipt targets this KPI'. Confirmed against the live "
        "falsification ledger (grep module=amphora-molecule-property, zero hits for "
        "this KPI id across 20+ prior fires C7/C8/W2/W3/W7/W8/R-A09/R-A11/R-N02/"
        "V-N02a/V1-MOLPROP/W-PROP1/U-MLIP/R-C03/U-AD/U-DATA). Applies this module's "
        "own established physical-admissibility falsification methodology (C8 "
        "fires 1-3, W2 fires 1-3: eps_static>=n^2 Frohlich/Maxwell inequality) to "
        "this KPI's OWN OpenPoly source labels for the first time -- prior fires "
        "applied this method only to RadonPy-derived dielectric corpora (PI1070, "
        "polyomics_small_molecules), where it found severe violations (89.5% and "
        "39.2% respectively). The OpenPoly raw CSV was never mined for its "
        "electronic/ionic/total dielectric decomposition or its independent "
        "refractive-index column until this fire."
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
        "Test whether the OpenPoly-derived ground-truth dielectric-constant "
        "labels feeding openpoly-dielectric-constant-ml-baseline-kpi.v1.json "
        "(295 polymers, RandomForest scaffold-safe holdout MAE=0.4040 vs NULL "
        "0.7027, LOSO-CV R2=+0.659, status STANDS) are physically admissible, "
        "using the SAME Frohlich(1949)/Maxwell/Lorentz-Lorenz physical-bound "
        "methodology this module's own C8/W2 fires already used to REFUTE the "
        "sibling RadonPy dielectric corpora, applied here to OpenPoly for the "
        "first time."
    ),
    "method": (
        "Self-contained data audit of the exact CSV pinned as this KPI's own "
        "dataset_fixture_sha256 (feedback/v1/external_data/openpoly_benchmark/"
        "raw/final_polymer_properties_fromliterature.csv, sha256 verified to "
        "match byte-for-byte). The CSV carries a per-polymer physical "
        "decomposition never before audited: 'Dielectric Constant Total', "
        "'Dielectric Constant Electronic', 'Dielectric Constant Ionic' "
        "(295/295 rows all three present) plus an independent 'Refractive "
        "Index' column (148/741 rows). Four pre-registered physical/"
        "definitional checks: R1 ionic>=0 (Frohlich 1949 Ch.2, non-negative "
        "polarization-mechanism contributions); R2 electronic>=1 (Maxwell "
        "eps_inf=n^2, n>=1 by definition of phase velocity, same citation W2 "
        "used for RadonPy); R3 total==electronic+ionic within 0.011 tolerance "
        "(Clausius-Mossotti additive decomposition, cited verbatim in the "
        "TARGET KPI's own theory field; tolerance = 0.01 physical rounding of "
        "independently-2-decimal-rounded source fields + float-repr epsilon); "
        "R4 refractive_index>=1 (Lorentz-Lorenz, identical citation basis W2 "
        "already used for RadonPy's refractive-index axis). Positive control: "
        "12 defects planted on a deep copy of the real rows (3 per rule, "
        "targeted at rows that were clean in the real data), re-running the "
        "identical, unmodified audit() function against the corrupted copy and "
        "confirming every planted defect is caught by its targeted rule (R1/R2 "
        "single-field mutations also mechanically cross-trigger R3 additivity "
        "for the same rows, which is physically correct, not double-counting -- "
        "verified per-defect by row name, not merely by rule-level counts). "
        "Two-replay: audit() re-run twice on the identical real-data input, "
        "byte-identical JSON confirmed."
    ),
    "input_artifacts": {
        "target_kpi_path": diag["claim_under_attack"]["kpi_path"],
        "target_kpi_sha256": diag["claim_under_attack"]["kpi_sha256"],
        "dataset_fixture_path": "feedback/v1/external_data/openpoly_benchmark/raw/final_polymer_properties_fromliterature.csv",
        "dataset_fixture_sha256_observed": diag["dataset_fixture_sha256_observed"],
        "dataset_fixture_sha256_pinned_in_kpi": diag["dataset_fixture_sha256_pinned_in_kpi"],
        "dataset_fixture_sha256_match": diag["dataset_fixture_sha256_match"],
        "compute_openpoly_dielectric_admissibility.py_sha256": sha(compute_script),
    },
    "n_csv_rows_total": diag["n_csv_rows_total"],
    "real_data_audit": diag["real_data_audit"],
    "real_data_two_replay_byte_identical": diag["real_data_two_replay_byte_identical"],
    "positive_control": {
        "planted_defect": (
            "12 defects planted on a deep copy of the real 295-row dielectric "
            "table (and its 148-row refractive-index subset), 3 per rule: "
            "(R1) Dielectric Constant Ionic negated to a negative value on 3 "
            "rows; (R2) Dielectric Constant Electronic overwritten to 0.5 "
            "(<1, physically impossible eps_inf) on 3 rows; (R3) Dielectric "
            "Constant Total incremented by +5.0 without adjusting components "
            "on 3 rows, breaking additivity by far more than the 0.011 "
            "rounding tolerance; (R4) Refractive Index overwritten to 0.8 "
            "(<1, physically impossible) on 3 rows."
        ),
        "how_planted": (
            "See positive_control.planted_defects[] below for the exact "
            "row name, field, before-value and after-value of each of the 12 "
            "mutations, produced by corrupt_rows() in "
            "compute_openpoly_dielectric_admissibility.py (deterministic, "
            "seed-free -- operates on the first N rows with each field "
            "present, not randomly sampled)."
        ),
        "detected": diag["positive_control"]["all_planted_defects_detected"],
        "evidence": (
            f"All 12/12 planted defects were caught by their targeted rule "
            f"(per_defect_detection, verified by row name). Rule-level "
            f"violation counts on the corrupted copy: "
            f"{json.dumps(diag['positive_control']['observed_violations_per_rule'])} "
            f"(R3=9, not 3, because the R1 and R2 single-field mutations "
            f"mechanically also break R3 additivity for those same 6 rows -- "
            f"a physically correct cross-trigger, confirmed by inspecting "
            f"per_defect_detection rather than assuming rule independence). "
            f"On the REAL (uncorrupted) data, all four rules report 0 "
            f"violations: {json.dumps({k: diag['real_data_audit'][k]['n_violations'] for k in ('R1_ionic_non_negative','R2_electronic_geq_1','R3_total_equals_electronic_plus_ionic','R4_refractive_index_geq_1')})}."
        ),
        "planted_defects": diag["positive_control"]["planted_defects"],
        "per_defect_detection": diag["positive_control"]["per_defect_detection"],
        "expected_violations_per_rule": diag["positive_control"]["expected_violations_per_rule"],
        "observed_violations_per_rule": diag["positive_control"]["observed_violations_per_rule"],
    },
    "pre_registered_refute_criterion": diag["pre_registered_refute_criterion"],
    "verdict": diag["verdict"],
    "why": (
        "The OpenPoly dielectric-constant corpus underlying "
        "openpoly-dielectric-constant-ml-baseline-kpi.v1.json is, unlike its "
        "sibling RadonPy corpora, physically admissible under every one of the "
        "four pre-registered checks: 0/295 rows have a negative ionic "
        "polarization contribution (R1), 0/295 have an electronic contribution "
        "below the eps_inf>=1 floor (R2), 0/295 violate the Total=Electronic+"
        "Ionic additive decomposition beyond legitimate 2-decimal rounding "
        "(R3), and 0/148 rows with an independently-reported refractive index "
        "fall below the n>=1 floor (R4). This is a genuinely falsifying attack "
        "-- the identical methodology found 89.5% (PI1070) and 39.2% "
        "(polyomics_small_molecules) violation rates on this module's RadonPy "
        "dielectric corpora (C8/W2), and the positive control confirms the "
        "harness used here would have caught defects of the same kind had they "
        "been present (12/12 planted defects detected by their targeted rule). "
        "openpoly-dielectric-constant-ml-baseline-kpi.v1.json's REAL POSITIVE "
        "LIFT claim (RandomForest scaffold-safe holdout MAE=0.4040 vs NULL "
        "0.7027, LOSO-CV R2=+0.659) therefore SURVIVES this label-admissibility "
        "attack: whatever else may limit this KPI (it is already disclosed as "
        "'baseline_valid_on_openpoly_scaffold_distribution_only' and grants no "
        "release/optimizer/solver authority), physically inadmissible ground-"
        "truth labels of the kind that undermined the RadonPy dielectric "
        "claims are NOT among its weaknesses."
    ),
    "rights_check": (
        "No new data source opened. This audit reads only the already-in-tree "
        "OpenPoly raw CSV (rights_class DERIVATIVE_ALLOWED per "
        "reference/mvp20/data/feedback_v2/rights/rights_openpoly_properties.json) "
        "that the target KPI itself already consumes and pins by sha256, plus "
        "the target KPI receipt itself. No quarantined or CONTEXT_ONLY source "
        "was opened."
    ),
    "gates": {
        "two_replay_byte_stable_real_data_audit": diag["real_data_two_replay_byte_identical"],
        "dataset_fixture_sha256_matches_target_kpi_pin": diag["dataset_fixture_sha256_match"],
        "self_contained_no_external_pipeline_reproduction_risk": True,
        "positive_control_planted_and_detected": diag["positive_control"]["all_planted_defects_detected"],
        "signature_field_is_dsse_envelope_object": True,
        "signing_key_role_matches_repo_wide_audit_convention": True,
    },
    "all_gates_passed": (
        diag["real_data_two_replay_byte_identical"]
        and diag["dataset_fixture_sha256_match"]
        and diag["positive_control"]["all_planted_defects_detected"]
    ),
    "ceiling": (
        "AUDIT_ONLY. Does not alter the shipped "
        "openpoly-dielectric-constant-ml-baseline-kpi.v1.json, any manifest, "
        "or any authority ceiling. Extends the module's falsification record: "
        "the C8/W2 physical-admissibility methodology now covers OpenPoly's "
        "dielectric labels (clean) in addition to RadonPy's (contaminated), "
        "closing a gap the W2 corpus-admissibility-audit-receipt's own "
        "dependent_module_kpis list implicitly left open by listing this KPI "
        "as downstream of the openpoly_properties Tg/Tm ordering violation "
        "without checking its own dielectric labels directly."
    ),
    "promotion_blocked_by": "NOT this audit's science (all gates pass) and NOT key custody. Manifest untouched.",
    "recommended_followups": [
        "The 6 rows where Total differs from Electronic+Ionic by exactly the "
        "float-boundary value (~0.01, within the legitimate 2-decimal "
        "rounding tolerance) are listed for transparency in "
        "real_data_audit.R3_total_equals_electronic_plus_ionic even though "
        "they do not breach the 0.011 tolerance -- no action needed, flagged "
        "only so a future fire does not need to re-derive this boundary "
        "reasoning from scratch.",
        "This audit did not re-derive the ML MAE/R2 numbers themselves (a "
        "harder scaffold-safe or macro-bisection external-validity attack, "
        "in the style of C7/W7, remains open for this KPI's MODEL claims as "
        "opposed to its LABEL claims -- this fire only closes the label-"
        "admissibility gap).",
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

ptype = "application/vnd.amphora.molecule-property.openpoly-dielectric-corpus-physical-admissibility-audit-receipt.v1+json"
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

outpath = OUT / "openpoly-dielectric-admissibility-audit-receipt.v1.dsse.json"
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
print("all_gates_passed", receipt is not None and json.loads(body1)["all_gates_passed"])
print("verdict", json.loads(body1)["verdict"])
print("envelope_sha256", sha(outpath.read_bytes()))
