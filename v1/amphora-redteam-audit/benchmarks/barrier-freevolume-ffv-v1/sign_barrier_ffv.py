"""DSSE-Ed25519-sign the barrier free-volume (FFV) AUDIT_ONLY receipt.

Signs the canonical diagnostic whose bytes reproduced identically across two runs
(two-replay SHA gate = PASS) with the repo LOCAL_DEVELOPMENT_AUDIT_ONLY key
(local-9028773f...), explicitly NOT a trust-anchored phase0 key. AUDIT_ONLY:
promotes nothing, flips no scientific_readiness flag, signs no phase0
evaluation/review, modifies no existing receipt, does not change the manifest
(still 66 receipts / 11 modules).
"""
import base64
import hashlib
import json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-redteam-audit/benchmarks/barrier-freevolume-ffv-v1"
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
harness_sha = sha((BENCH / "barrier_freevolume_audit.py").read_bytes())

receipt = {
    "schema": "amphora.redteam-audit.barrier-freevolume-ffv-v1-replay-receipt.v1",
    "authority": "AUDIT_ONLY",
    "run_type": "BARRIER_FREEVOLUME_FFV_REPLAY",
    "promotes_authority": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "module": "amphora-redteam-audit",
    "benchmark": "amphora-redteam-audit/barrier-freevolume-ffv-v1",
    "target_module": diag["target_module"],
    "target_capability": diag["target_capability"],
    "theory": diag["theory"],
    "fitted_parameters": diag["fitted_parameters"],
    "inputs_live_from_tree": diag["inputs_live_from_tree"],
    "cross_method_stats": diag["part_A_volumetric_foundation"]["cross_method_stats"],
    "network_ffv_span_observed": diag["part_B_network_ffv_bounds_DIAGNOSTIC"]["ffv_span_observed"],
    "network_ffv_status": diag["part_B_network_ffv_bounds_DIAGNOSTIC"]["status"],
    "honest_negatives": {
        "penetrant_size_proxy_spearman": diag["honest_negatives"]["penetrant_size_proxy_REFUTED"][
            "spearman_vs_published_kinetic_diameter"],
        "penetrant_size_proxy_verdict": "REFUTED (shape != volume)",
        "per_hardener_ranking": "DATA_RIGHTS_BLOCKED"},
    "non_circularity": diag["non_circularity"],
    "known_answer_battery": diag["known_answer_battery"],
    "verdict": diag["verdict"],
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "replays": 2, "independent_runs": True,
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": runb_sha,
        "harness_sha256": harness_sha,
    },
    "does_not_close": diag["does_not_close"],
    "signing_key": {"key_id": PUB["key_id"], "authority": PUB["authority"],
                    "trust_anchored_in_phase0_store": False},
}
body = json.dumps(receipt, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.redteam-barrier-freevolume-ffv+json"
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
print("harness_sha256", harness_sha)
