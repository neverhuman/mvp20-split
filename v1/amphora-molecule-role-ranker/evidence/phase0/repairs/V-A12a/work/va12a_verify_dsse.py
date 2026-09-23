import base64
import hashlib
import json
import sys
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

REPO = Path("/home/ubuntu/amphora/build/mvp20-split")

PINNED_EVALUATOR_HEX = "6cf07abf1a55adaac13e78abc31c531d03d8f0d4232346344a736418c7b45664"
LOCAL_DEV_PUB = json.loads((REPO / ".amphora/control/local-ed25519.pub.json").read_text())
LOCAL_DEV_HEX = LOCAL_DEV_PUB["public_key_hex"] if "public_key_hex" in LOCAL_DEV_PUB else None


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" "
            + str(len(body)).encode() + b" " + body)


def verify(path, key_hex, label):
    raw = json.loads(Path(path).read_text())
    env = raw["signature"] if ("signature" in raw and isinstance(raw["signature"], dict)) else raw
    ptype = env["payloadType"]
    body = base64.standard_b64decode(env["payload"])
    msg = pae(ptype, body)
    pub = Ed25519PublicKey.from_public_bytes(bytes.fromhex(key_hex))
    sigs = env.get("signatures") or [{"sig": env.get("signature")}]
    results = []
    for s in sigs:
        sig_b64 = s["sig"] if isinstance(s, dict) else s
        sig = base64.standard_b64decode(sig_b64)
        try:
            pub.verify(sig, msg)
            results.append(True)
        except InvalidSignature:
            results.append(False)
    ok = any(results)
    print(f"{label}: file={path} key={key_hex[:16]}... verify={ok} payload_sha256={sha(body)} file_sha256={sha(Path(path).read_bytes())}")
    return ok


if __name__ == "__main__":
    print("=== LOCAL_DEV_HEX ===", LOCAL_DEV_HEX)
    targets = [
        ("amphora-molecule-role-ranker/benchmarks/role-live-runtime-domain-probe-v1/replay_receipt.v1.dsse.json", "ORIG_PROBE"),
        ("amphora-molecule-role-ranker/benchmarks/role-reactivity-ratio-substitution-effect-v1/replay_receipt.v1.dsse.json", "ORIG_REACTIVITY"),
        ("amphora-molecule-role-ranker/evidence/phase0/repairs/R-A12/done/ra12_reinstatement_batch_receipt.v1.dsse.json", "REISSUE_BATCH"),
    ]
    summary = {}
    for rel, label in targets:
        p = REPO / rel
        against_pinned = verify(p, PINNED_EVALUATOR_HEX, f"{label} vs PINNED_EVALUATOR")
        against_local = verify(p, LOCAL_DEV_HEX, f"{label} vs LOCAL_DEV") if LOCAL_DEV_HEX else None
        summary[label] = {"path": rel, "verifies_against_pinned_evaluator": against_pinned,
                           "verifies_against_local_dev_key": against_local}
    print("=== SUMMARY ===")
    print(json.dumps(summary, indent=2))
