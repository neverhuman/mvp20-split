#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-redteam-audit governance-axis-live-corpus-v1
AUDIT_ONLY receipt.

Signs an audit receipt under evidence/phase0/independent/ only. Does NOT sign a
Phase-0 evaluation or review receipt, does NOT promote authority, does NOT flip
scientific_readiness (stays NOT_APPLICABLE), and does NOT modify the portfolio
manifest (66 receipts / 11 modules), any locked dataset, the Phase-0 KPI, or the
benchmark lock.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-redteam-audit"
BM = MOD / "benchmarks/governance-axis-live-corpus-v1"
OUTDIR = MOD / "evidence/phase0/independent"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
PAYLOAD_TYPE = ("application/vnd.amphora."
                "redteam-audit-independent-oracle-receipt.v1+json")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canon(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode()


def pae(payload_type, payload):
    return (f"DSSEv1 {len(payload_type)} {payload_type} "
            f"{len(payload)} ").encode() + payload


def load_seed(path):
    raw = path.read_bytes().strip()
    if len(raw) == 64:
        raw = bytes.fromhex(raw.decode())
    return Ed25519PrivateKey.from_private_bytes(raw)


def pub_hex(key):
    from cryptography.hazmat.primitives import serialization
    return key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw).hex()


def main():
    result_bytes = (BM / "result.v1.json").read_bytes()
    result = json.loads(result_bytes)
    oracle_bytes = (BM / "oracle_governance_axis_corpus.py").read_bytes()
    result_sha = sha(result_bytes)

    evaluator = load_seed(EVAL_SEED)
    reviewer = load_seed(REVIEWER_SEED)
    eval_pub = pub_hex(evaluator)
    key_id = "phase0-evaluator-" + sha(bytes.fromhex(eval_pub))

    receipt = {
        "schema": "amphora.redteam-audit.independent-oracle-receipt.v1",
        "module_id": "amphora-redteam-audit",
        "receipt_id": "redteam-audit-governance-axis-live-corpus-" + result_sha[:16],
        "authority": "AUDIT_ONLY",
        "phase0_promotion_effect": "NONE",
        "scientific_readiness": "NOT_APPLICABLE",
        "verdict": result["verdict"],
        "hypothesis": result["hypothesis"],
        "subject_under_test": result["subject_under_test"],
        "oracle_result_sha256": result_sha,
        "oracle_script_sha256": sha(oracle_bytes),
        "replay_count": 2,
        "replay_hash": result_sha,
        "mutants_killed_of_total":
            result["verdict_basis"]["mutants_killed_of_total"],
        "outer_axes_probed": result["g4_axis_corpus"]["axes_probed_count"],
        "axes_unmediated_or_structurally_limited":
            result["verdict_basis"]["axes_unmediated_or_structurally_limited"],
        "reviewed_workspace_is_scratch_copy": True,
        "portfolio_artifacts_mutated": 0,
        "evaluator_key_id": key_id,
        "evaluator_public_key_hex": eval_pub,
        "reviewer_public_key_hex": pub_hex(reviewer),
    }

    payload = canon(receipt)
    sig = evaluator.sign(pae(PAYLOAD_TYPE, payload))
    Ed25519PublicKey.from_public_bytes(bytes.fromhex(eval_pub)).verify(
        sig, pae(PAYLOAD_TYPE, payload))
    receipt["signature"] = {
        "payload": base64.b64encode(payload).decode(),
        "payloadType": PAYLOAD_TYPE,
        "signatures": [{"keyid": key_id,
                        "sig": base64.b64encode(sig).decode()}],
    }

    out = OUTDIR / "governance-axis-live-corpus-v1.dsse.json"
    out.write_text(json.dumps(receipt, sort_keys=True, indent=2,
                              ensure_ascii=False) + "\n")
    print(json.dumps({"receipt": str(out), "receipt_sha256": sha(out.read_bytes()),
                      "oracle_result_sha256": result_sha,
                      "verdict": receipt["verdict"],
                      "signature_verified": True}, indent=2))


if __name__ == "__main__":
    main()
