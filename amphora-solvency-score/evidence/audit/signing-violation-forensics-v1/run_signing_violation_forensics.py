#!/usr/bin/env python3
"""Forensic re-derivation of the 4 SIGNING_VIOLATION alerts flagged against
amphora-solvency-score KPI files. Pure-stdlib + cryptography (Ed25519 verify
only, no wall-clock, no RNG) so this is byte-identical across independent
executions. Writes diagnostic.canonical.json; caller diffs against
diagnostic.runB.json to certify the two-replay gate.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
PUB = json.loads((ROOT / ".amphora/control/local-ed25519.pub.json").read_text())
PK = Ed25519PublicKey.from_public_bytes(bytes.fromhex(PUB["public_key_hex"]))
KPI_DIR = ROOT / "amphora-solvency-score/evidence/phase0/kpis"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" "
            + str(len(body)).encode() + b" " + body)


ALERTS = [
    ("2026-07-27T13:11", "hansen-sphere-coefficient-robustness-v1-kpi.v1.json",
     "amphora-solvency-score/reference/mvp20/data/hansen_sphere_coefficient_robustness_receipt.v1.json"),
    ("2026-07-28T18:10", "hildebrand-vs-hansen-chi-baseline-v1-kpi.v1.json",
     "amphora-solvency-score/reference/mvp20/data/hildebrand_vs_hansen_chi_baseline_receipt.v1.json"),
    ("2026-07-29T23:06", "reduced-representation-discrimination-v1-kpi.v1.json",
     "amphora-solvency-score/reference/mvp20/data/reduced_representation_discrimination_receipt.v1.json"),
    ("2026-07-31T04:09", "hansen-temperature-envelope-v1-kpi.v1.json",
     "amphora-solvency-score/reference/mvp20/data/hansen_temperature_envelope_receipt.v1.json"),
]

per_file = []
for ts, kpi_name, receipt_rel in ALERTS:
    kpi_path = KPI_DIR / kpi_name
    kpi = json.loads(kpi_path.read_text())
    receipt_path = ROOT / receipt_rel
    receipt_bytes = receipt_path.read_bytes()
    receipt = json.loads(receipt_bytes)

    has_top_level_signature_key_in_kpi = "signature" in kpi
    has_scientific_receipt_path_field = "scientific_receipt_path" in kpi
    has_receipt_path_field = "receipt_path" in kpi

    kpi_recorded_sha = kpi.get("receipt_sha256")
    actual_receipt_sha = sha(receipt_bytes)
    sha_match = kpi_recorded_sha == actual_receipt_sha

    env = receipt["signature"]
    body = base64.b64decode(env["payload"])
    pt = env["payloadType"]
    p = pae(pt, body)
    sig_bytes = base64.b64decode(env["signatures"][0]["sig"])
    keyid = env["signatures"][0]["keyid"]
    try:
        PK.verify(sig_bytes, p)
        crypto_valid = True
        crypto_err = None
    except Exception as e:
        crypto_valid = False
        crypto_err = repr(e)

    payload_obj = json.loads(body)
    payload_sha_consistent = sha(
        json.dumps(payload_obj, indent=2, sort_keys=True).encode()) == sha(body)

    two_replay_gate_kpi = kpi.get("two_replay_sha256_gate")
    two_replay_gate_receipt = receipt.get("reproducibility", {}).get("two_replay_sha256_gate")

    chain_clean = (has_receipt_path_field and sha_match and crypto_valid
                   and payload_sha_consistent
                   and two_replay_gate_kpi == "PASS"
                   and two_replay_gate_receipt == "PASS")

    per_file.append({
        "alert_timestamp": ts,
        "kpi_file": f"amphora-solvency-score/evidence/phase0/kpis/{kpi_name}",
        "parent_receipt_file": receipt_rel,
        "kpi_schema": kpi.get("schema"),
        "field_audit": {
            "kpi_has_top_level_signature_key": has_top_level_signature_key_in_kpi,
            "kpi_has_scientific_receipt_path_field": has_scientific_receipt_path_field,
            "kpi_has_receipt_path_field": has_receipt_path_field,
        },
        "receipt_sha256_chain": {
            "kpi_recorded_receipt_sha256": kpi_recorded_sha,
            "actual_parent_receipt_sha256_recomputed": actual_receipt_sha,
            "match": sha_match,
        },
        "signature_verification": {
            "signature_present_on_parent_receipt": True,
            "envelope_type": "DSSE (payload/payloadType/signatures)",
            "algorithm": "Ed25519",
            "signature_count": len(env["signatures"]),
            "keyid": keyid,
            "keyid_matches_pinned_pubkey_id": keyid == PUB["key_id"],
            "cryptographic_verify_against_pinned_pubkey": crypto_valid,
            "crypto_error": crypto_err,
            "payload_bytes_sha256_self_consistent": payload_sha_consistent,
        },
        "two_replay_gate": {
            "kpi_field": two_replay_gate_kpi,
            "parent_receipt_field": two_replay_gate_receipt,
        },
        "chain_verified_clean": chain_clean,
    })

all_clean = all(f["chain_verified_clean"] for f in per_file)
none_missing_signature = all(
    not f["field_audit"]["kpi_has_scientific_receipt_path_field"] for f in per_file)

diagnostic = {
    "schema": "amphora.solvency-score.signing-violation-forensics-diagnostic.v1",
    "purpose": (
        "Forensic close-out of 4 SIGNING_VIOLATION alerts raised against "
        "amphora-solvency-score Phase-0 KPI files. Re-derives, independently "
        "of the original alerting checker, whether each flagged KPI's parent "
        "evidence chain (KPI -> receipt_path -> DSSE Ed25519 signature -> "
        "receipt_sha256 byte match) is intact."
    ),
    "root_cause": (
        "The alerting checker read a field named '.scientific_receipt_path' on "
        "each KPI file and treated its absence as evidence of unsigned data. "
        "Every KPI in this schema family (amphora.solvency-score.phase0-kpi.*) "
        "is a thin pointer object: it has no top-level 'signature' key by design "
        "and instead carries a 'receipt_path' field pointing at a separate, fully "
        "DSSE Ed25519-signed parent receipt under reference/mvp20/data/. The field "
        "name the checker looked for does not exist in this schema; the field that "
        "does the same job is 'receipt_path'. This is a field-name mismatch in the "
        "checker, not evidence that any unsigned artifact was committed."
    ),
    "pinned_verification_pubkey": {
        "key_id": PUB["key_id"],
        "public_key_hex": PUB["public_key_hex"],
        "source": ".amphora/control/local-ed25519.pub.json",
    },
    "alerts_investigated": [a[0] for a in ALERTS],
    "per_file_verification": per_file,
    "aggregate": {
        "n_files_investigated": len(per_file),
        "n_chains_verified_clean": sum(1 for f in per_file if f["chain_verified_clean"]),
        "all_chains_verified_clean": all_clean,
        "all_kpis_missing_scientific_receipt_path_field": none_missing_signature,
        "all_kpis_have_receipt_path_field": all(
            f["field_audit"]["kpi_has_receipt_path_field"] for f in per_file),
    },
    "conclusion": (
        "REFUTED: no unsigned evidence was committed by the loop. All 4 flagged "
        "KPI files correctly reference a DSSE Ed25519-signed parent receipt via "
        "'receipt_path'; every recorded receipt_sha256 matches the actual parent "
        "receipt bytes; every parent receipt's signature cryptographically verifies "
        "against the pinned local-ed25519 public key; every two_replay_sha256_gate "
        "reads PASS on both the KPI and its parent receipt. The alerts were false "
        "positives caused by the checker probing a nonexistent field name "
        "('.scientific_receipt_path' instead of '.receipt_path')."
        if all_clean else
        "NOT FULLY REFUTED: see per_file_verification for the specific chain(s) "
        "that failed independent re-verification."
    ),
    "does_not_close": [
        "the underlying checker code itself (this receipt documents the finding; "
        "it does not patch the launcher's alerting logic)",
        "module promotion to PHASE_0 (requires human dual-identity ceremony keys)",
        "portfolio manifest edit (66 receipts / 11 modules unchanged)",
    ],
    "recommendation": (
        "Update the alert-checker to read '.receipt_path' (with a fallback probe of "
        "'.scientific_receipt_path' only for schemas that actually define it) so this "
        "false-positive class does not recur on the phase0-kpi.* schema family."
    ),
}

diag_bytes = json.dumps(diagnostic, indent=2, sort_keys=True).encode()
print(diag_bytes.decode())
import sys
print("DIAGNOSTIC_SHA256=" + sha(diag_bytes), file=sys.stderr)
