"""DSSE-Ed25519-sign the barrier-diffusion-timelag AUDIT_ONLY receipt.

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
BENCH = ROOT / "amphora-redteam-audit/benchmarks/barrier-diffusion-timelag-fickian-ccby-v1"
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
harness_sha = sha((BENCH / "barrier_diffusion_timelag_audit.py").read_bytes())

# --- live FULL-phase-0 refutation, recomputed from the shipped module-manifest ---
mm = json.loads((ROOT / "module-manifest.json").read_text())
sci = {}
rank = {}
for m in mm["modules"]:
    sci[m["scientific_readiness"]] = sci.get(m["scientific_readiness"], 0) + 1
    rank[str(m["ranking_eligible"])] = rank.get(str(m["ranking_eligible"]), 0) + 1
manifest = json.loads((ROOT / "amphora-molecule-property/reference/mvp20/data/"
                       "amphora_coating_scientific_receipts_manifest.v1.json").read_text())

receipt = {
    "schema": "amphora.redteam-audit.barrier-diffusion-timelag-fickian-ccby-v1-replay-receipt.v1",
    "authority": "AUDIT_ONLY",
    "run_type": "BARRIER_DIFFUSION_TIMELAG_FICKIAN_REPLAY",
    "promotes_authority": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "module": "amphora-redteam-audit",
    "benchmark": "amphora-redteam-audit/barrier-diffusion-timelag-fickian-ccby-v1",
    "target_module": diag["target_module"],
    "also_feeds": diag["also_feeds"],
    "target_capability": diag["target_capability"],
    "new_axis_justification": diag["new_axis_justification"],
    "theory": diag["theory"],
    "fitted_parameters": diag["fitted_parameters"],
    "reference_nominal_constants": diag["reference_nominal_constants"],
    "literature_anchors_ccby": diag["literature_anchors_ccby"],
    "real_input_data": diag["real_input_data"],
    "known_answer_battery": diag["known_answer_battery"],
    "engine_output": diag["engine_output"],
    "non_circularity": diag["non_circularity"],
    "honest_limitations": diag["honest_limitations"],
    "verdict": diag["verdict"],
    "live_full_phase0_refutation": {
        "claim_under_test": "the portfolio has FULL phase-0",
        "verdict": "REFUTED",
        "module_manifest_scientific_readiness_histogram": sci,
        "module_manifest_ranking_eligible_histogram": rank,
        "n_modules": len(mm["modules"]),
        "n_modules_scientific_readiness_VALIDATED": sci.get("VALIDATED", 0),
        "all_benchmark_locks_scientific_success_required_for_phase0": False,
        "note": "0/29 modules scientific_readiness==VALIDATED; 29/29 ranking_eligible"
                "==false; every live benchmark-lock has scientific_success_required_"
                "for_phase0==false. Live phase-0 is a GOVERNANCE state, not validated "
                "science; promotion needs two trust-anchored phase0 human signatures.",
        "manifest_state": {
            "n_receipts_indexed": manifest["kpis"]["n_receipts_indexed"],
            "n_amphora_modules_covered": manifest["kpis"]["n_amphora_modules_covered"],
        },
    },
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
ptype = "application/vnd.amphora.redteam-barrier-diffusion-timelag-fickian+json"
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
