"""DSSE-Ed25519-sign the multi-method isoconversional cure-kinetics cross-validation.
Signs the canonical diagnostic whose bytes reproduced identically across two runs
(two-replay SHA gate = PASS), using the repo LOCAL_DEVELOPMENT_AUDIT_ONLY key
(local-9028773f...), explicitly NOT a trust-anchored phase0 key. AUDIT_ONLY:
promotes nothing, signs no phase0 evaluation/review receipt, modifies no existing
receipt or manifest, flips no rights gate.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-redteam-audit/benchmarks/cure-kinetics-isoconversional-crossmethod-ccby-v1"
KEY = ROOT / ".amphora/control/local-ed25519.key"
PUB = json.loads((ROOT / ".amphora/control/local-ed25519.pub.json").read_text())


def sha(b): return hashlib.sha256(b).hexdigest()
def pae(t, body): return b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " + str(len(body)).encode() + b" " + body


diag_bytes = (BENCH / "diagnostic.canonical.json").read_bytes()
runb_bytes = (BENCH / "diagnostic.runB.json").read_bytes()
diag_sha, runb_sha = sha(diag_bytes), sha(runb_bytes)
assert diag_sha == runb_sha, f"two-replay gate FAIL {diag_sha} != {runb_sha}"
diag = json.loads(diag_bytes)
harness_sha = sha((BENCH / "isoconversional_crossmethod_audit.py").read_bytes())
dataset_bytes = (BENCH / "dataset.multi.ccby.json").read_bytes()

receipt = {
    "schema": "amphora.redteam-audit.cure-kinetics-isoconversional-crossmethod-ccby-v1-replay-receipt.v1",
    "authority": "AUDIT_ONLY",
    "run_type": "CURE_KINETICS_ISOCONVERSIONAL_CROSSMETHOD_CCBY_REPLAY",
    "promotes_authority": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "module": "amphora-redteam-audit",
    "benchmark": "amphora-redteam-audit/cure-kinetics-isoconversional-crossmethod-ccby-v1",
    "target_module": diag["target_module"],
    "capability": diag["capability"],
    "theory": diag["theory"],
    "known_answer_first_principles": diag["known_answer_first_principles"],
    "dataset": diag["dataset"],
    "systems": diag["systems"],
    "aggregate_kpi": diag["aggregate_kpi"],
    "acceptance_gates": diag["acceptance_gates"],
    "all_acceptance_gates_pass": diag["all_acceptance_gates_pass"],
    "verdict": diag["verdict"],
    "non_circularity": diag["non_circularity"],
    "physics_note": diag["physics_note"],
    "relation_to_cure_potlife": diag["relation_to_cure_potlife"],
    "redteam_phase0_snapshot": diag["redteam_phase0_snapshot"],
    "rights_summary": {
        "all_sources_license": "CC-BY-4.0",
        "all_sources_rights_class": "DERIVATIVE_ALLOWED",
        "commercial_use_allowed": True,
        "dataset_reused_byte_identical_from": "cure-kinetics-kissinger-multisystem-ccby-v1",
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "replays": 2, "independent_runs": True,
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": runb_sha,
        "harness_sha256": harness_sha,
        "dataset_sha256": sha(dataset_bytes),
    },
    "does_not": diag["does_not"],
    "signing_key": {"key_id": PUB["key_id"], "authority": PUB["authority"],
                    "trust_anchored_in_phase0_store": False},
}
body = json.dumps(receipt, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.redteam-cure-kinetics-isoconversional-crossmethod-ccby+json"
sk = Ed25519PrivateKey.from_private_bytes(KEY.read_bytes())
sig = sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": PUB["key_id"], "sig": base64.standard_b64encode(sig).decode()}]}
out = BENCH / "replay_receipt.v1.dsse.json"
out.write_text(json.dumps(envelope, indent=2, sort_keys=True))
print("WROTE", out)
print("receipt_body_sha256", sha(body))
print("envelope_sha256", sha(out.read_bytes()))

pk = Ed25519PublicKey.from_public_bytes(bytes.fromhex(PUB["public_key_hex"]))
pk.verify(base64.standard_b64decode(envelope["signatures"][0]["sig"]), pae(ptype, body))
print("SIGNATURE_VERIFY PASS")
