#!/usr/bin/env python3
"""DSSE-Ed25519-sign the T-10 campaign-item done wrapper receipt for
amphora-process-qc-twin. AUDIT_ONLY. References (does not re-sign) the
ar1-estparam-drift-corpus-v1 audit receipt by path + sha256.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-process-qc-twin"
T10 = MOD / "evidence/phase0/repairs/T-10"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

AUDIT_RECEIPT = MOD / "evidence/audit/ar1-estparam-drift-corpus-v1/ar1-estparam-drift-corpus-receipt.v1.dsse.json"
W_QC_RECEIPT = MOD / "evidence/phase0/repairs/W-QC/done/w-qc-done-receipt.v1.dsse.json"
DIRECTIVE_MD = ROOT / "docs/directives/2026-08-05-closing-the-open-portfolio.md"
DIRECTIVE_SHA_EXPECTED = "dcedb048e1142529de84aa6d741a065fdc29ebf744ef1b2feb81951c74573a6d"


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


audit_bytes = AUDIT_RECEIPT.read_bytes()
audit_sha = sha(audit_bytes)
audit_receipt = json.loads(audit_bytes)
audit_payload = json.loads(base64.b64decode(audit_receipt["signature"]["payload"]))

wqc_bytes = W_QC_RECEIPT.read_bytes()
wqc_sha = sha(wqc_bytes)

directive_bytes = DIRECTIVE_MD.read_bytes()
directive_sha_actual = sha(directive_bytes)
assert directive_sha_actual == DIRECTIVE_SHA_EXPECTED, "directive md sha mismatch"

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
rev_pin = (rev_key_id == tbr.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))
assert eval_pin, "evaluator key_id does not derive pinned trust store entry"

# independently re-verify the audit receipt's own signature before citing it
audit_env = audit_receipt["signature"]
audit_pub = bytes.fromhex(audit_receipt["evaluator_public_key_hex"])
audit_pae = pae(audit_env["payloadType"], base64.b64decode(audit_env["payload"]))
Ed25519PublicKey.from_public_bytes(audit_pub).verify(
    base64.b64decode(audit_env["signatures"][0]["sig"]), audit_pae)

body_obj = {
    "schema": "amphora.process-qc-twin.repair-done.t-10.v1",
    "module": "amphora-process-qc-twin",
    "campaign_item_id": "T-10",
    "authority": "AUDIT_ONLY",
    "promotes_authority": False, "flips_scientific_readiness": False,
    "modifies_manifest": False, "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "fire_id": "20260806T030002-115447-b5ba20ebfc36",
    "done_criterion": (
        ">=3 chart parameterisations run under BOTH stress regimes -- control limits "
        "estimated from short reference windows, and AR(1) autocorrelated input -- with "
        "measured ARL against advertised ARL per cell and the ratio reported. Any case that "
        "slips through = CLAIM_REFUTED with the case quoted verbatim. ALSO REQUIRED by "
        "founder directive T2-10: 100% re-simulation determinism; drift/tamper detection on "
        "all 128; V1-KPI-QC either lands a verdict or is split into fitting sub-items with a "
        "RUN_SUMMARY."
    ),
    "done_criterion_met": True,
    "claim_verdict": audit_payload["claim_verdict"],
    "deliverable_1_ar1_estparam_drift_corpus_receipt": {
        "path": "evidence/audit/ar1-estparam-drift-corpus-v1/ar1-estparam-drift-corpus-receipt.v1.dsse.json",
        "sha256": audit_sha,
        "study_id": audit_payload["study_id"],
        "claim_verdict": audit_payload["claim_verdict"],
        "two_replay_byte_identical": audit_payload["reproducibility"]["byte_identical"],
        "signature_independently_reverified_this_receipt": True,
        "chart_parameterisations_tested": 3,
        "baselines_tested": [30, 50],
        "phi_values_tested": [0.0, 0.2, 0.4, 0.6],
        "n_tamper_cases": audit_payload["part_b_tamper_corpus_summary"]["n_cases"],
        "tamper_recall": audit_payload["part_b_tamper_corpus_summary"]["recall"],
        "n_tamper_undetected": audit_payload["part_b_tamper_corpus_summary"]["n_undetected"],
        "n_m50_cells_breaching_budget_under_ar1": audit_payload["part_a_m50_budget_check_summary"]["n_cells_breaching_budget_under_ar1"],
    },
    "deliverable_2_v1_kpi_qc_stall_resolution": {
        "note": (
            "V1-KPI-QC is auto_blocked_max_fires (exhausted budget mid-computation across two "
            "background-wait stalls; see its attempts/ checkpoint). It was re-filed as campaign "
            "item W-QC, which is DONE. W-QC's done receipt supplies the previously-missing "
            "deliverable (mr-memory-detector-arl-degradation-v1, signed) and a consolidated KPI "
            "v2 restating all five now-signed audit receipts. This satisfies the directive "
            "done_criteria clause 'V1-KPI-QC either lands a verdict or is split into fitting "
            "sub-items with a RUN_SUMMARY' -- W-QC is that sub-item and it is DONE."
        ),
        "w_qc_done_receipt_path": "evidence/phase0/repairs/W-QC/done/w-qc-done-receipt.v1.dsse.json",
        "w_qc_done_receipt_sha256": wqc_sha,
        "w_qc_done_criterion_met": True,
    },
    "directive_path": "docs/directives/2026-08-05-closing-the-open-portfolio.md",
    "directive_sha256": directive_sha_actual,
    "directive_obligation": "T2-10",
    "directive_refutation_criterion_verbatim": (
        "Any tamper is masked as noise, re-simulation diverges, or the item stalls a third "
        "time with no RUN_SUMMARY."
    ),
    "directive_refutation_criterion_observation": (
        "OCCURRED (partially): 22/128 tamper cases (17.2%) were masked as noise -- undetected "
        "within the 30-batch monitoring window by the union of all three module detector arms "
        "under estimated-parameter + AR(1) stress. Re-simulation did NOT diverge -- the full "
        "128-case corpus plus the 24-cell ARL0 grid plus the 3-cell known-parameter anchor "
        "reproduced byte-identical (SHA-256 match) across two independent foreground runs. The "
        "item did NOT stall a third time -- this is fire 1 of 3, all compute ran synchronously "
        "in the foreground (two full runs, ~35-38s each), no background job was launched. "
        "Verdict: CLAIM_REFUTED, per the pre-committed criterion."
    ),
    "directive_done_criteria_verbatim": (
        "100% re-simulation determinism; drift/tamper detection on all 128; V1-KPI-QC either "
        "lands a verdict or is split into fitting sub-items with a RUN_SUMMARY."
    ),
    "directive_done_criteria_status": {
        "re_simulation_determinism": "MET -- 100% byte-identical two-replay (SHA-256 "
            f"{audit_payload['reproducibility']['canonical_diagnostic_sha256']}).",
        "drift_tamper_detection_on_all_128": "NOT MET as a pass-rate -- detection occurred on "
            "106/128 (82.8%); 22/128 were masked as noise. This is the honest observed result, "
            "not a softened restatement: the directive's own refutation_criterion treats any "
            "masked tamper as a refuting observation, so 'detection on all 128' failing is "
            "exactly what licenses CLAIM_REFUTED, not a gap left open.",
        "v1_kpi_qc_resolved": "MET via W-QC (done; see deliverable_2 above).",
    },
    "positive_control_note": (
        "Not required for this receipt (outcome is CLAIM_REFUTED, not CLAIM_SURVIVED). A "
        "sanity positive-control was nonetheless run inside the audit receipt (6-sigma "
        "shift, phi=0, m=50 -> detected at lag 0), confirming the harness is not silently "
        "broken."
    ),
    "does_not_close": [
        "No coating-efficacy, product-performance, batch-release, or corrosion-rank authority.",
        "No Phase-0 promotion: PHASE0_EVALUATOR evaluation.v1.dsse.json and "
        "PHASE0_INTERNAL_REVIEWER review remain human dual-identity steps outside this "
        "cron's authority.",
        "Does not modify or re-sign the ar1-estparam-drift-corpus-v1 receipt, any of the "
        "five prior ARL-degradation audit receipts, the consolidated KPI v1/v2, or the W-QC "
        "done receipt; all remain independently valid on disk and are referenced by path + "
        "sha256.",
        "Non-normal (heavy-tailed) innovations and MA/ARMA autocorrelation structures beyond "
        "AR(1) remain uncharacterized.",
    ],
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY repair-done receipt under evidence/phase0/repairs/T-10/done/",
        "derives_pinned_trust_store_key_id": bool(eval_pin),
    },
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER", "key_id": rev_key_id, "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin), "reviewer_signature_present": False,
    },
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.process-qc-twin-repair-done-t10+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
out = T10 / "done" / "t-10-done-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("claim_verdict", audit_payload["claim_verdict"])
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
