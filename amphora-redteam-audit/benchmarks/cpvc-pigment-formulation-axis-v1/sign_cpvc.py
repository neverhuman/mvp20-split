"""DSSE-Ed25519-sign the CPVC pigment-formulation-axis AUDIT_ONLY receipt.
Signs the canonical diagnostic whose bytes reproduced identically across two runs
(two-replay SHA gate = PASS), with the repo LOCAL_DEVELOPMENT_AUDIT_ONLY key
(local-9028773f...), explicitly NOT a trust-anchored phase0 key. AUDIT_ONLY:
promotes nothing, signs no phase0 evaluation/review, modifies no existing receipt
or the manifest (still 66 receipts / 11 modules).
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-redteam-audit/benchmarks/cpvc-pigment-formulation-axis-v1"
KEY = ROOT / ".amphora/control/local-ed25519.key"
PUB = json.loads((ROOT / ".amphora/control/local-ed25519.pub.json").read_text())


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" "
            + str(len(body)).encode() + b" " + body)


diag_bytes = (BENCH / "diagnostic.canonical.json").read_bytes()
runb_bytes = (BENCH / "diagnostic.runB.json").read_bytes()
diag_sha, runb_sha = sha(diag_bytes), sha(runb_bytes)
assert diag_sha == runb_sha, f"two-replay gate FAIL {diag_sha} != {runb_sha}"
diag = json.loads(diag_bytes)
harness_sha = sha((BENCH / "cpvc_pigment_axis_audit.py").read_bytes())
sci = diag["cpvc_pigment_axis"]

receipt = {
    "schema": "amphora.redteam-audit.cpvc-pigment-formulation-axis-v1-replay-receipt.v1",
    "authority": "AUDIT_ONLY",
    "run_type": "CPVC_PIGMENT_FORMULATION_AXIS_REPLAY",
    "promotes_authority": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "module": "amphora-redteam-audit",
    "benchmark": "amphora-redteam-audit/cpvc-pigment-formulation-axis-v1",
    "target_module": sci["target_module"],
    "target_capability": sci["target_capability"],
    "theory": sci["theory"],
    "phase0_honesty_redteam": sci["phase0_honesty_redteam"],
    "axis_gap_map": sci["axis_gap_map"],
    "cpvc_engine": sci["cpvc_engine"],
    "assessment": sci["assessment"],
    "verdict": sci["verdict"],
    "non_circularity": sci["assessment"]["non_circularity"],
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "replays": 2, "independent_runs": True,
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": runb_sha,
        "harness_sha256": harness_sha,
    },
    "does_not_close": [
        "does NOT promote any module to PHASE_0: phase-0 is a governance state "
        "(scientific_success_required_for_phase0=false on all 29 live locks; 0/40 "
        "ranked modules scientific_readiness==VALIDATED) and needs two trust-anchored "
        "phase0 signatures this AUDIT_ONLY key cannot supply",
        "does NOT change the manifest (still 66 receipts / 11 modules)",
        "does NOT claim a precision external validation of CPVC: that requires a "
        "rights-clean set of >=12 pigments with INDEPENDENTLY-MEASURED CPVC, which was "
        "not obtainable rights-clean this session (the diagnosed data blocker)",
        "the pigment OA/density are REFERENCE_NOMINAL constants (with ranges) used to "
        "exercise engine physics, not asserted as a measured dataset",
    ],
    "signing_key": {"key_id": PUB["key_id"], "authority": PUB["authority"],
                    "trust_anchored_in_phase0_store": False},
}
body = json.dumps(receipt, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.redteam-cpvc-pigment-formulation-axis+json"
sk = Ed25519PrivateKey.from_private_bytes(KEY.read_bytes())
sig = sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": PUB["key_id"], "sig": base64.standard_b64encode(sig).decode()}]}
out = BENCH / "replay_receipt.v1.dsse.json"
out.write_text(json.dumps(envelope, indent=2, sort_keys=True))
print("WROTE", out)
print("receipt_body_sha256", sha(body))
print("envelope_sha256", sha(out.read_bytes()))
print("two_replay_sha256", diag_sha)
