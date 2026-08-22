#!/usr/bin/env python3
"""DSSE-Ed25519-sign the W-QC campaign-item done receipt: certifies that both
deliverables of the item are complete -- (1) the mr-memory-detector-arl-
degradation-v1 AUDIT_ONLY receipt is signed and self-verified, and (2) the
module's consolidated ARL-characterization Phase-0 KPI has been superseded
(v1 -> v2, supersede-never-rewrite) to fold in that result. AUDIT_ONLY: does
not promote authority, does not flip scientific_readiness, does not modify
the portfolio manifest or any locked dataset.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-process-qc-twin"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

MR_RECEIPT = MOD / "evidence/audit/mr-memory-detector-arl-degradation-v1/mr-memory-detector-arl-degradation-receipt.v1.dsse.json"
KPI_V1 = MOD / "evidence/phase0/kpis/arl-characterization-consolidated-kpi.v1.json"
KPI_V2 = MOD / "evidence/phase0/kpis/arl-characterization-consolidated-kpi.v2.json"
OUTDIR = MOD / "evidence/phase0/repairs/W-QC/done"


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


def load_dsse(path):
    d = json.loads(path.read_bytes())
    sig = d.get("signature", d)
    payload = json.loads(base64.b64decode(sig["payload"]))
    return d, sig, payload


mr_raw, mr_sig, mr_payload = load_dsse(MR_RECEIPT)
kpi2_raw, kpi2_sig, kpi2_payload = load_dsse(KPI_V2)

# independent re-verification of both constituent envelopes before declaring done
eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
assert eval_pin, "evaluator key_id does not derive pinned trust store entry"

for label, sig, raw in (("mr_receipt", mr_sig, mr_raw), ("kpi_v2", kpi2_sig, kpi2_raw)):
    pub = bytes.fromhex(raw["evaluator_public_key_hex"])
    body = base64.b64decode(sig["payload"])
    signature = base64.b64decode(sig["signatures"][0]["sig"])
    Ed25519PublicKey.from_public_bytes(pub).verify(signature, pae(sig["payloadType"], body))
    assert raw["evaluator_public_key_hex"] == eval_pub_hex, f"{label} signed by wrong key"

assert mr_payload["results"]["claim_verdict"] == "SURVIVED"
assert mr_payload["results"]["all_known_answer_gates_passed"] is True
assert kpi2_payload["n_audits_indexed"] == 5
assert kpi2_payload["supersedes"]["superseded_path"] == "evidence/phase0/kpis/arl-characterization-consolidated-kpi.v1.json"
assert kpi2_payload["supersedes"]["superseded_sha256"] == sha(KPI_V1.read_bytes())

body_obj = {
    "schema": "amphora.process-qc-twin.repair-done.w-qc.v1",
    "campaign_item_id": "W-QC",
    "module": "amphora-process-qc-twin",
    "authority": "AUDIT_ONLY",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "done_criterion": "Signed MR-detector receipt AND a Phase-0 KPI restating the ARL characterisation.",
    "done_criterion_met": True,
    "deliverable_1_mr_memory_detector_receipt": {
        "path": "evidence/audit/mr-memory-detector-arl-degradation-v1/mr-memory-detector-arl-degradation-receipt.v1.dsse.json",
        "sha256": sha(MR_RECEIPT.read_bytes()),
        "study_id": mr_payload["study_id"],
        "claim_verdict": mr_payload["results"]["claim_verdict"],
        "all_known_answer_gates_passed": mr_payload["results"]["all_known_answer_gates_passed"],
        "two_replay_byte_identical": mr_payload["reproducibility"]["byte_identical"],
        "signature_independently_reverified_this_receipt": True,
    },
    "deliverable_2_phase0_kpi": {
        "path": "evidence/phase0/kpis/arl-characterization-consolidated-kpi.v2.json",
        "sha256": sha(KPI_V2.read_bytes()),
        "kpi_id": kpi2_payload["kpi_id"],
        "n_audits_indexed": kpi2_payload["n_audits_indexed"],
        "n_audits_all_gates_passed": kpi2_payload["n_audits_all_gates_passed"],
        "supersedes": kpi2_payload["supersedes"],
        "signature_independently_reverified_this_receipt": True,
        "retraction_index_updated": "evidence/phase0/kpis/RETRACTION-INDEX.md",
        "mission_md_updated": True,
    },
    "does_not_close": [
        "No coating-efficacy, product-performance, batch-release, or corrosion-rank authority.",
        "No Phase-0 promotion: PHASE0_EVALUATOR evaluation.v1.dsse.json and "
        "PHASE0_INTERNAL_REVIEWER review remain human dual-identity steps outside this "
        "cron's authority.",
        "Does not modify or re-sign any of the five indexed audit receipts nor the "
        "superseded v1 KPI; all remain independently valid on disk and are referenced by "
        "path + sha256.",
        "Out-of-control (ARL1) performance under estimated parameters and the recall >=90% "
        "half of the module's locked KPI remain uncharacterized.",
    ],
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY repair-done receipt under evidence/phase0/repairs/W-QC/done/",
        "derives_pinned_trust_store_key_id": bool(eval_pin)},
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.process-qc-twin-repair-done-w-qc+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "signature": envelope}

OUTDIR.mkdir(parents=True, exist_ok=True)
out = OUTDIR / "w-qc-done-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("self_verify_signature", True)
print("envelope_sha256", sha(out.read_bytes()))
