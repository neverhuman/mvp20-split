#!/usr/bin/env python3
"""DSSE-Ed25519-sign the R-C04 cluster-bootstrap data-availability-audit
checkpoint (CAMPAIGN-mode fire, fire_id
20260812T040001-4187595-821716c37e86). AUDIT_ONLY / repair-checkpoint: does
NOT supersede the FFW-vs-ML KPI (acceptance not met -- data-blocked), does
NOT edit any existing signed receipt, docs/mission.md, or the 66-receipt
master manifest, does NOT open the quarantined Polyverse row-level CSV."""
import base64
import hashlib
import json
import subprocess
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-viscosity-score"
EV = MOD / "evidence/phase0/repairs/R-C04/attempts/cluster-bootstrap-data-audit-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"
FIRE_ID = "20260812T040001-4187595-821716c37e86"


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


canon = (EV / "diagnostic.canonical.json").read_bytes()
runB = (EV / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)
assert diag["conclusion"]["genuine_cluster_bootstrap_executable_from_signed_artifacts"] is False

# independent 3rd confirmatory replay into a temp path
third = EV / "diagnostic.runC.tmp.json"
subprocess.run(["python3", str(EV / "run_cluster_bootstrap_data_audit.py"), str(third)],
               check=True, cwd=str(EV))
third_sha = sha(third.read_bytes())
third.unlink()
assert third_sha == diag_sha, f"3rd replay FAIL {third_sha} != {diag_sha}"

harness_sha = sha((EV / "run_cluster_bootstrap_data_audit.py").read_bytes())

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"
trust = json.loads(TRUST.read_text()) if TRUST.exists() else {"keys": []}
tbr = {k.get("role"): k for k in trust.get("keys", [])}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
rev_pin = (rev_key_id == tbr.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))

body_obj = {
    "schema": "amphora.viscosity-score.r-c04-cluster-bootstrap-data-audit-checkpoint.v1",
    "receipt_id": "cluster-bootstrap-data-audit-v1",
    "campaign_item_id": "R-C04",
    "module_id": "amphora-viscosity-score",
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "EVIDENCE_ONLY",
    "phase": "PRE_PHASE_0",
    "mode": "CAMPAIGN",
    "fire_id": FIRE_ID,
    "date": "2026-08-12",
    "scientific_success_required_for_phase0": False,
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "modifies_manifest": False,
    "modifies_mission_md": False,
    "modifies_signed_phase0_kpi": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "derives_from_quarantined_row_data": False,
    "repair_status": "blocked_on_missing_signed_data",
    "verdict": "BLOCKED_DATA",
    "objective_under_repair": (
        "R-C04: pre-registered cluster bootstrap (resample the 13 test "
        "polymers with replacement, B=5000, seed=0) of the R2 difference "
        "(FFW_B3 - ML_B4) on the identical seed-0 partition from the KPI, "
        "verified via the conformal_receipt_sha256 cross-link. Report the "
        "CI and supersede the FFW KPI with an honest restatement at "
        "whatever strength the interval supports."
    ),
    "claim_under_attack": (
        "amphora-viscosity-score/evidence/phase0/kpis/"
        "polyverse-melt-viscosity-fox-flory-whitten-physical-baseline-vs-ml-"
        "kpi.v1.json :: headline finding 'best_physical_ffw_baseline_beats_"
        "ml_r2_documented' (physical B3 R^2=+0.5972 beats ML B4 R^2=+0.4536 "
        "by +0.1436), previously found in "
        "evidence/audit/ffw-vs-ml-uncertainty-disclosure-gap-v1/ to discose "
        "zero estimation uncertainty for this headline gap despite resting "
        "on only 13 independent test-polymer clusters (below the published "
        "G>=~30 cluster-count-adequacy threshold)."
    ),
    "why_blocked_not_refuted_or_survived": (
        "This fire did not attempt to run the pre-registered bootstrap and "
        "fall short of an acceptance threshold -- the protocol could not be "
        "started at all, because no signed artifact in the module's FFW-vs-"
        "ML lineage persists the per-row or per-polymer actual/predicted "
        "values a cluster bootstrap requires. The underlying physics-beats-"
        "ML point estimate is therefore neither confirmed nor disputed by "
        "this fire; only its testability from currently-available signed "
        "data is established (false). BLOCKED_DATA is the outcome the item "
        "itself pre-authorizes for exactly this situation: 'if per-polymer "
        "predictions are not persisted in any signed artifact, verdict "
        "BLOCKED_DATA with a data-ask specifying exactly which arrays are "
        "missing.'"
    ),
    "attack": (
        "Data-availability audit for R-C04's pre-registered protocol. "
        "Step 1: verified the FFW KPI's conformal_receipt_sha256 field "
        "(4e0f56ca46e41b2ee14b63fa93836cc71b4d2b94b98b8a6bab4028f44a332fc4) "
        "matches the actual sha256 of the conformal+AD scientific receipt "
        "file bytes -- confirms both KPIs share the identical seed=0 "
        "polymer-safe 41-train/13-test-polymer, 863/194-row partition. "
        "Step 2: recursively scanned every JSON body in the module's FFW-"
        "vs-ML lineage (ffw_kpi, conformal_kpi, ffw_scientific_receipt, "
        "conformal_scientific_receipt, parent_model_receipt, and the prior "
        "ffw-vs-ml-uncertainty-disclosure-gap-v1 audit receipt) for any "
        "array whose length equals 194 (per-test-row granularity) or 13 "
        "(per-test-polymer granularity) -- the minimum granularity a "
        "cluster bootstrap needs to resample polymers and re-score. Found "
        "zero qualifying arrays; every array present is either a "
        "fixed-length per-baseline summary (5 entries: B0-B4) or a "
        "5-quintile applicability-domain coverage breakdown, never a "
        "per-row or per-polymer (actual, predicted) pair. Step 3: self-"
        "tested the scanner by planting a synthetic 194-length array into a "
        "copy of the FFW KPI and confirming the scanner correctly flags it "
        "(positive control on the audit tool itself, not on the underlying "
        "scientific claim -- see numeric_self_test below). Reads only "
        "already-signed, non-quarantined downstream JSON KPI/receipt bytes "
        "plus the non-numeric quarantine metadata file confirming rights "
        "status; does not open, parse, or derive any value from the "
        "underlying quarantined Polyverse row-level CSV."
    ),
    "cross_link_check": diag["cross_link_check"],
    "array_scan_summary": {
        "files_examined": list(diag["files_examined"].keys()),
        "n_candidate_per_row_or_per_polymer_prediction_arrays_found": diag["conclusion"]["n_candidate_per_row_or_per_polymer_prediction_arrays_found"],
        "genuine_cluster_bootstrap_executable_from_signed_artifacts": diag["conclusion"]["genuine_cluster_bootstrap_executable_from_signed_artifacts"],
        "reasoning": diag["conclusion"]["reasoning"],
        "quarantine_confirmation": diag["conclusion"]["quarantine_confirmation"],
    },
    "numeric_self_test": {
        "note": (
            "Scanner-soundness self-test (not a scientific positive control "
            "-- BLOCKED_DATA does not require one; this is included anyway "
            "to show the zero-arrays-found result is a true negative, not a "
            "scanner bug). Took a copy of the FFW KPI JSON, added a "
            "synthetic 194-element array under a suspect key name, re-ran "
            "the same scan_for_arrays() function against it."
        ),
        "planted_array": "synthetic_test_row_y_true_log10_viscosity, length 194, values 0..193",
        "detected": True,
        "evidence": (
            "scan_for_arrays() returned one hit: path="
            "'synthetic_test_row_y_true_log10_viscosity', length=194, "
            "length_matches_n_test_rows=True -- confirms the scanner would "
            "have found real per-row prediction data had any existed in the "
            "actual (unmodified) signed artifacts."
        )
    },
    "data_ask": diag["conclusion"]["data_ask"],
    "does_not_close": [
        "Does not modify the FFW KPI, the FFW scientific receipt, the "
        "conformal+AD KPI or receipt, docs/mission.md, or the 66-receipt "
        "master manifest.",
        "Does not open, parse, or derive any value from the underlying "
        "quarantined Polyverse melt-viscosity row-level CSV or its "
        "quarantine/feedback_v2/derived/*.jsonl.gz shadow.",
        "Does not assert the B3/B4 R^2 point estimates are numerically "
        "wrong or right -- takes no position on the underlying physics-"
        "beats-ML finding.",
        "Does not compute any bootstrap interval -- establishes only that "
        "the pre-registered protocol is not currently executable from "
        "signed data.",
    ],
    "human_action_needed": (
        "Re-run the harness that produced "
        "polyverse_melt_viscosity_fox_flory_whitten_physical_baseline_"
        "receipt.v1.json (FFW_B3) and the parent ML B4 HistGBM fit, with "
        "per-row prediction logging enabled, and sign the resulting "
        "(test_row_polymer_id, test_row_y_true, test_row_y_pred_B3, "
        "test_row_y_pred_B4) arrays as a new receipt. This is a pipeline "
        "re-run-and-persist gap, not a new external data acquisition -- no "
        "rights review is needed since it derives from the same already-"
        "cleared, non-quarantined model-fitting step, not the quarantined "
        "row-level CSV."
    ),
    "provenance": {
        "harness_sha256": {"run_cluster_bootstrap_data_audit.py": harness_sha},
        "inputs_sha256": {k: v["raw_file_sha256"] for k, v in diag["files_examined"].items()},
    },
    "reproducibility": {
        "byte_identical": True,
        "two_replay_sha256_gate": "PASS",
        "third_confirmatory_replay": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "third_replay_sha256": third_sha,
        "determinism": (
            "pure-python re-derivation from already-in-tree, already-hashed "
            "JSON files; no RNG, no network, no wall-clock reads at run "
            "time."
        ),
    },
    "signing_key": {
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "role": "PHASE0_EVALUATOR",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": eval_pin,
        "used_for": "AUDIT_ONLY R-C04 checkpoint receipt under evidence/phase0/repairs/R-C04/attempts/",
    },
    "reviewer_reference": {
        "key_id": rev_key_id,
        "public_key_hex": rev_pub_hex,
        "role": "PHASE0_INTERNAL_REVIEWER",
        "derives_pinned_trust_store_key_id": rev_pin,
        "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed.",
    },
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.viscosity-score-r-c04-cluster-bootstrap-data-audit-checkpoint+json"
sig = eval_sk.sign(pae(ptype, body))
sig_b64 = base64.standard_b64encode(sig).decode()
envelope = {
    "evaluator_key_id": eval_key_id,
    "evaluator_public_key_hex": eval_pub_hex,
    "reviewer_public_key_hex": rev_pub_hex,
    "signature": {
        "payload": base64.standard_b64encode(body).decode(),
        "payloadType": ptype,
        "signatures": [{"keyid": eval_key_id, "sig": sig_b64}],
    },
}
out = EV / "cluster-bootstrap-data-audit-v1-receipt.v1.dsse.json"
out.write_text(json.dumps(envelope, indent=2, sort_keys=True))
print("WROTE", out)
print("receipt_body_sha256", sha(body))
print("envelope_sha256", sha(out.read_bytes()))
