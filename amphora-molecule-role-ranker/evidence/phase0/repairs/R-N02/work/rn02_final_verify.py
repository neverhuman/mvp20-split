#!/usr/bin/env python3
"""R-N02 final independent verification: re-verify the three signed done
receipts from disk (fresh process, seed-derived pubkey, PAE rebuild, keyid
prefix), and re-assert that every signed/locked artifact in scope is
byte-identical to its pre-repair sha256."""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
SEED = Path.home() / ".local/share/amphora/phase0/keys/evaluator.ed25519.seed"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def load_seed(p):
    raw = p.read_bytes().strip()
    if len(raw) == 64:
        try:
            return bytes.fromhex(raw.decode())
        except Exception:
            pass
    return raw[:32]


def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " +
            str(len(body)).encode() + b" " + body)


pub = Ed25519PrivateKey.from_private_bytes(
    load_seed(SEED)).public_key().public_bytes_raw()
expected_key_id = f"phase0-evaluator-{sha(pub)}"

RECEIPTS = [
    "amphora-rdkit-ffi/evidence/phase0/repairs/R-N02/done/rn02-rdkit-ffi-coordinated-cn-fix-repair-receipt.v1.dsse.json",
    "amphora-molecule-property/evidence/phase0/repairs/R-N02/done/rn02-molecule-property-coordinated-cn-fix-repair-receipt.v1.dsse.json",
    "amphora-molecule-role-ranker/evidence/phase0/repairs/R-N02/done/rn02-molecule-role-ranker-coordinated-cn-fix-repair-receipt.v1.dsse.json",
]

print("== DSSE self-verification (independent process, seed-derived pubkey) ==")
for rp in RECEIPTS:
    d = json.loads((ROOT / rp).read_text())
    env = d["signature"]
    body = base64.standard_b64decode(env["payload"])
    sig = base64.standard_b64decode(env["signatures"][0]["sig"])
    Ed25519PublicKey.from_public_bytes(pub).verify(sig, pae(env["payloadType"], body))
    keyid = env["signatures"][0]["keyid"]
    assert keyid == expected_key_id, keyid
    assert keyid.startswith("phase0-evaluator-3ef6b35"), keyid
    payload = json.loads(body)
    assert payload["repair_item"] == "R-N02"
    assert payload["repair_mode"] == "interactive-2026-08-03"
    assert "supersedes" in payload
    s = payload["supersedes"]
    assert s["superseded_deleted_or_modified"] is False
    assert s["superseded_sha256"] and s["superseded_path"]
    print(f"  OK  {rp}")
    print(f"      keyid={keyid[:32]}... payload_sha256={sha(body)}")

print()
print("== signed/locked artifacts still byte-identical to pre-repair ==")
LOCKED = {
    "amphora-molecule-property/evidence/audit/amine-nh-guanidine-conjugation-gap-v1/amine-nh-guanidine-conjugation-gap-receipt.v1.dsse.json": "59c447c077a069c18a68fede5308d44c2e52dbc20ba4ba3cc4754f17ac3a4701",
    "amphora-molecule-role-ranker/benchmarks/role-guanidine-accelerator-domain-probe-v1/replay_receipt.v1.dsse.json": "414a68af76b1db0c658b1d08e757d187122f81874ae2d4612f96808340904099",
    "amphora-molecule-property/benchmarks/amine-class-active-nh-robustness-v1/amine_class_active_nh_robustness_receipt.v1.json": "74e2c759c1f56ba435ad2807be1f2bdc37c479d68fca81934569901072ba6519",
    "amphora-molecule-role-ranker/reference/phase0-role-known-answer.v1.json": "8ce4d54192a20e8de1bb89f6181b11630fc184b4dda2918ce934610630855c8f",
    "amphora-molecule-role-ranker/evidence/phase0/kpis/role-classification-kpi.v1.json": "88689040b9dcce07560c05f1053dd9d0243f1bd084b259e69b5e727cfc528f36",
    "amphora-molecule-role-ranker/evidence/phase0/benchmark/result.v1.json": "f2a21f74e03b6b20f53fb10d4cdb6f2b477ce2b9a6e5200947c1ed91ad3a136a",
    "amphora-molecule-role-ranker/evidence/phase0/benchmark/benchmark-lock.v1.json": "6960c8cf8f4296aeed47e445148d127f6f5ff51921adb6393780313f84809170",
    "amphora-molecule-property/reference/mvp20/data/amphora_coating_scientific_receipts_manifest.v1.json": "f5623b3171d65de2dc805b740aef71ad6163554dcf9b5b394d84181b3ad6bf08",
    "amphora-molecule-property/reference/mvp20/data/eew_ahew_benchmark.v1.json": "3de26f203423a80212e6c90aaa511e5112c79bf92ac56b4c63260c3086d4638f",
}
ok = True
for p, before in LOCKED.items():
    now = sha((ROOT / p).read_bytes())
    good = now == before
    ok = ok and good
    print(f"  {'INTACT ' if good else 'MODIFIED'} {p}")
    if not good:
        print(f"      before={before} after={now}")
print()
print("ALL_SIGNED_ARTIFACTS_INTACT", ok)
assert ok
