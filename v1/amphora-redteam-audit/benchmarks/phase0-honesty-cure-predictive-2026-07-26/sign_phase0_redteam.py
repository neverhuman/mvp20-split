"""DSSE-Ed25519-sign the phase0-honesty + cure-predictive AUDIT_ONLY diagnostic.
Signs the canonical diagnostic whose bytes reproduced identically across two runs
(two-replay SHA gate = PASS), using the repo LOCAL_DEVELOPMENT_AUDIT_ONLY key
(NOT a trust-anchored phase0 key). Promotes nothing, signs no phase0
evaluation/review receipt, modifies no existing receipt or manifest, flips no
rights gate.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-redteam-audit/benchmarks/phase0-honesty-cure-predictive-2026-07-26"
KEY = ROOT / ".amphora/control/local-ed25519.key"
PUB = json.loads((ROOT / ".amphora/control/local-ed25519.pub.json").read_text())


def sha(b): return hashlib.sha256(b).hexdigest()
def pae(t, body): return b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " + str(len(body)).encode() + b" " + body


diag_bytes = (BENCH / "diagnostic.canonical.json").read_bytes()
runb_bytes = (BENCH / "diagnostic.runB.json").read_bytes()
diag_sha, runb_sha = sha(diag_bytes), sha(runb_bytes)
assert diag_sha == runb_sha, f"two-replay gate FAIL {diag_sha} != {runb_sha}"
diag = json.loads(diag_bytes)
harness_sha = sha((BENCH / "phase0_redteam_cure_predictive_audit.py").read_bytes())

receipt = {
    "schema": "amphora.redteam-audit.phase0-honesty-and-cure-predictive-v1-replay-receipt.v1",
    "authority": "AUDIT_ONLY",
    "run_type": "PHASE0_HONESTY_REDTEAM_AND_CURE_PREDICTIVE_REPLAY",
    "run_date": "2026-07-26",
    "promotes_authority": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "module": "amphora-redteam-audit",
    "benchmark": "amphora-redteam-audit/phase0-honesty-cure-predictive-2026-07-26",
    "target_modules": diag["target_modules"],
    "part_a_phase0_honesty": diag["part_a_phase0_honesty"],
    "part_b_provenance_reverification": diag["part_b_provenance_reverification"],
    "part_c_cure_kinetics_predictive": diag["part_c_cure_kinetics_predictive"],
    "gap_map_honest": diag["gap_map_honest"],
    "headline": (
        "Founder skepticism UPHELD: 0/29 modules carry scientific_readiness==VALIDATED; "
        "'FULL Phase-0' is a governance lock (17 PHASE_0 = 4 LOCKED_INTERNAL + 13 NOT_APPLICABLE), "
        "not validated science. Independently re-verified the two load-bearing CC-BY datasets vs "
        "signed in-tree values (match). Banked a new non-circular predictive KPI: leave-one-"
        "heating-rate-out Kissinger Tp forecast MAE 2.25 K on the PMC-verified Lascano peaks."),
    "rights_summary": {
        "part_b_and_c_sources_license": "CC-BY-4.0",
        "commercial_use_allowed": True,
        "sources_reverified_this_run": [
            "10.3390/polym11030391 (PMC6473346) Lascano DGEBA+IPDA DSC peaks, CC-BY-4.0",
            "10.3390/polym16010067 (PMC10780492) DGEBA+{DDS,1,3-BAC,C8DA} pristine Tg, CC-BY-4.0",
        ],
        "no_new_measurement_ingested": True,
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "replays": 2, "independent_runs": True,
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": runb_sha,
        "harness_sha256": harness_sha,
    },
    "does_not_close": [
        "does NOT promote any module to PHASE_0 or assert scientific_readiness==VALIDATED",
        "does NOT change the manifest (stays 66 receipts / 11 modules)",
        "does NOT cross the network-Tg n>=12 gate (declined as gate-gaming, logged honestly)",
        "does NOT flip any rights gate or authority ceiling",
    ],
    "does_not": diag["does_not"],
    "signing_key": {"key_id": PUB["key_id"], "authority": PUB["authority"],
                    "trust_anchored_in_phase0_store": False},
}
body = json.dumps(receipt, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.redteam-phase0-honesty-and-cure-predictive+json"
priv = Ed25519PrivateKey.from_private_bytes(KEY.read_bytes())
sig = priv.sign(pae(ptype, body))
envelope = {
    "payloadType": ptype,
    "payload": base64.standard_b64encode(body).decode(),
    "signatures": [{"keyid": PUB["key_id"], "sig": base64.standard_b64encode(sig).decode()}],
}
(BENCH / "replay_receipt.v1.dsse.json").write_text(json.dumps(envelope, indent=2, sort_keys=True))

pk = Ed25519PublicKey.from_public_bytes(bytes.fromhex(PUB["public_key_hex"]))
pk.verify(base64.standard_b64decode(envelope["signatures"][0]["sig"]), pae(ptype, body))
print("SIGNATURE_VERIFY PASS")
print("receipt_sha256", sha(json.dumps(envelope, indent=2, sort_keys=True).encode()))
print("diag_sha256", diag_sha)
