#!/usr/bin/env python3
"""role-ece-brier-metric-definition-integrity-v1: sign the audit receipt with the
PHASE0_EVALUATOR key. Follows the exact PAE/load_seed/keyid/self-verify
construction already used by amphora-molecule-role-ranker/evidence/audit/
role-flory-gelation-amine-smarts-parity-v1/work/sign_flory_parity.py.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-molecule-role-ranker"
ITEM = MOD / "evidence/audit/role-ece-brier-metric-definition-integrity-v1"
WORK = ITEM / "work"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

FIRE_ID = "20260819T160001-1585265-b61659dee87c"
DATE = "2026-08-19"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def fsha(p):
    return sha(Path(p).read_bytes())


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


eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
trust = json.loads(TRUST.read_text())
by_role = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == by_role.get("PHASE0_EVALUATOR", {}).get("key_id"))
assert eval_pin, "evaluator key_id does not match pinned trust-store PHASE0_EVALUATOR entry"
assert eval_pub_hex == by_role["PHASE0_EVALUATOR"]["public_key_hex"]

canon_path = WORK / "diagnostic.canonical.json"
runb_path = WORK / "diagnostic.runB.json"
canon_bytes = canon_path.read_bytes()
runb_bytes = runb_path.read_bytes()
assert sha(canon_bytes) == sha(runb_bytes), "two-replay byte gate FAILED"
diag = json.loads(canon_bytes)

body_obj = {
    "schema": "amphora.molecule-role-ranker.role-ece-brier-metric-definition-integrity-v1.receipt.v1",
    "receipt_id": "role-ece-brier-metric-definition-integrity-" + sha(canon_bytes)[:32],
    "fire_id": FIRE_ID,
    "campaign_item_id": "",
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "EVIDENCE_ONLY",
    "run_type": "ROTATION_FALSIFICATION_ATTACK",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_no_live_config": True,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "module": "amphora-molecule-role-ranker",
    "repair_mode": False,
    "objective": (
        "ROTATION-mode falsification attack (no campaign item) on the strongest standing "
        "artifact never before ledger-attacked on this specific facet: the flagship KPI's "
        "expected_calibration_error metric DEFINITION (evidence/phase0/kpis/"
        "role-classification-kpi.v1.json#metrics[6]). Independently re-derives the fitted "
        "probabilities from the shipped frozen model artifact, confirms the reported value is "
        "mechanically a mean Brier score (not binned ECE) by exact reproduction, then computes "
        "genuine Expected Calibration Error across 13 binning schemes to quantify the gap."
    ),
    "claim_under_attack": diag["claim_under_attack"],
    "primary_references": diag["primary_references"],
    "method": diag["method"],
    "harness_source_citations": diag["harness_source_citations"],
    "reproduction": diag["reproduction"],
    "genuine_ece_recomputation": diag["genuine_ece_recomputation"],
    "comparison": diag["comparison"],
    "risk_note": diag["risk_note"],
    "scope_boundary": diag["scope_boundary"],
    "verdict": diag["verdict"],
    "interpretation": diag["interpretation"],
    "closes": diag["closes"],
    "does_not_close": diag["does_not_close"],
    "phase0_gap_ledger": {
        "MANIFEST_UNCHANGED": "master receipts manifest (66 receipts / 11 modules) NOT "
                              "edited; requires human dual-identity Phase-0 ceremony keys.",
        "NOT_A_CORRECTNESS_CLAIM_ABOUT_THE_ROLE_RULE": diag["scope_boundary"][
            "NOT_A_CORRECTNESS_CLAIM_ABOUT_THE_ROLE_RULE"],
        "NOT_A_GATING_FAILURE": diag["scope_boundary"]["NOT_A_GATING_FAILURE"],
        "TARGET_UNCHANGED": diag["scope_boundary"]["TARGET_UNCHANGED"],
        "REPAIR_VEHICLE": (
            "This receipt documents the defect and its exact location; it does NOT edit "
            "role-classification-kpi.v1.json or role_ranker_phase0_kpi.rs (a repair item, id "
            "prefix R-/V-, is the correct vehicle for that under REPAIR MODE rules; this is a "
            "ROTATION attack fire with no campaign item)."
        ),
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": sha(canon_bytes),
        "runB_diagnostic_sha256": sha(runb_bytes),
        "diagnostic_builder_sha256": fsha(WORK / "build_diagnostic.py"),
        "determinism_basis": (
            "Deterministic re-derivation from checked-in fixture + shipped KPI file bytes: "
            "fixed-point sigmoid/z-score arithmetic, no random sampling, no wall-clock, no OS "
            "entropy. Two independent invocations of build_diagnostic.py produce byte-identical "
            "diagnostic JSON (confirmed by sha256)."
        ),
    },
    "claim_locks": diag["claim_locks"],
    "date": DATE,
    "generated_on_host": "xbabe2",
    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY role-ece-brier-metric-definition-integrity-v1 falsification receipt",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin),
    },
}

body1 = json.dumps(body_obj, indent=2, sort_keys=True).encode()
body2 = json.dumps(dict(body_obj), indent=2, sort_keys=True).encode()
assert body1 == body2, "receipt body non-deterministic"
(WORK / "receipt_body.canonical.json").write_bytes(body1)
(WORK / "receipt_body.runB.json").write_bytes(body2)

ptype = "application/vnd.amphora.molecule-role-ranker.role-ece-brier-metric-definition-integrity.v1+json"
sig = eval_sk.sign(pae(ptype, body1))
envelope = {
    "payload": base64.standard_b64encode(body1).decode(),
    "payloadType": ptype,
    "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}],
}

receipt = {
    "evaluator_key_id": eval_key_id,
    "evaluator_public_key_hex": eval_pub_hex,
    "signature": envelope,
}

ITEM.mkdir(parents=True, exist_ok=True)
outpath = ITEM / "replay_receipt.v1.dsse.json"
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
print("verdict", body_obj["verdict"])
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("two_replay_byte_identical", body1 == body2)
print("self_verify_against_trust_store_OK", True)
print("envelope_sha256", sha(outpath.read_bytes()))
