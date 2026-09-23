"""DSSE-Ed25519-sign the phase0-count-integrity audit receipt.

Signs the canonical diagnostic whose bytes reproduced identically across two
independent executions (two-replay SHA gate = PASS). Signs with the repo
LOCAL_DEVELOPMENT_AUDIT_ONLY key (local-9028773f...), explicitly NOT a
trust-anchored phase0 key. Records a count-integrity finding; modifies no
existing receipt and promotes nothing.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path(".")
BENCH = Path("amphora-redteam-audit/benchmarks/phase0-count-integrity-v1")
KEY = Path(".amphora/control/local-ed25519.key")
PUB = json.loads(Path(".amphora/control/local-ed25519.pub.json").read_text())
CANONICAL_SHA = "fa02375b207d25dc03f34111b6bf0ec4536ae0fbd13dbe989d8a077104beaea2"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pae(t, body):
    return b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " + str(len(body)).encode() + b" " + body


diag_bytes = (BENCH / "diagnostic.canonical.json").read_bytes()
runb_bytes = (BENCH / "diagnostic.runB.json").read_bytes()
diag_sha = sha(diag_bytes)
runb_sha = sha(runb_bytes)
assert diag_sha == CANONICAL_SHA, f"{diag_sha} != {CANONICAL_SHA}"
assert runb_sha == CANONICAL_SHA, f"runB {runb_sha} != {CANONICAL_SHA} (two-replay gate)"
diag = json.loads(diag_bytes)
harness_sha = sha((BENCH / "phase0_count_integrity_audit.py").read_bytes())

receipt = {
    "schema": "amphora.redteam-audit.phase0-count-integrity-v1-replay-receipt.v1",
    "authority": "AUDIT_ONLY",
    "run_type": "PHASE0_COUNT_INTEGRITY_AUDIT_REPLAY",
    "promotes_authority": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "module": "amphora-redteam-audit",
    "benchmark": "amphora-redteam-audit/phase0-count-integrity-v1",
    "purpose": (
        "Machine-checkable red-team of the '16 PHASE_0 modules' headline in "
        "config/program/phase0-decision-report.v2.json. For every module the "
        "report calls PHASE_0, recomputes whether its signed evaluation receipt "
        "still binds to the on-disk benchmark result and carries a valid "
        "trust-anchored PHASE0_EVALUATOR signature. Also re-derives the two "
        "pinned trust-anchor public keys from the on-host Ed25519 seeds to record "
        "that the signing keys are present. Fixed on-disk / on-host facts only."),
    "decision_report": diag["decision_report"],
    "trust_store": diag["trust_store"],
    "trust_anchor_key_presence": diag["trust_anchor_key_presence"],
    "headline_result": diag["verdict"],
    "modules": diag["modules"],
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "replays": 2, "independent_runs": True,
        "canonical_diagnostic_sha256": CANONICAL_SHA,
        "runB_diagnostic_sha256": runb_sha,
        "harness_sha256": harness_sha,
    },
    "does_not_close": [
        "EVALUATION_SIGNATURE_ABSENT for the 13 PRE_PHASE_0 science modules "
        "(trust-anchored ceremony not run here)",
        "does not restore the 7 drifted badges (governance: evaluate re-mints "
        "an immutable receipt)",
    ],
    "does_not": diag["does_not"],
    "signing_key": {"key_id": PUB["key_id"], "authority": PUB["authority"],
                    "trust_anchored_in_phase0_store": False},
}
body = json.dumps(receipt, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.redteam-phase0-count-integrity+json"
sk = Ed25519PrivateKey.from_private_bytes(KEY.read_bytes())
sig = sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": PUB["key_id"], "sig": base64.standard_b64encode(sig).decode()}]}
out = BENCH / "replay_receipt.v1.dsse.json"
out.write_text(json.dumps(envelope, indent=2, sort_keys=True))
print("WROTE", out)
print("receipt_body_sha256", sha(body))
print("envelope_sha256", sha(out.read_bytes()))
