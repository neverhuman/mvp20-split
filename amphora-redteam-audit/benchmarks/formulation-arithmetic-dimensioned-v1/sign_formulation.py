"""DSSE-Ed25519-sign the formulation-arithmetic dimensioned AUDIT_ONLY receipt.

Signs the canonical diagnostic whose bytes reproduced identically across two runs
(two-replay SHA gate = PASS) with the repo LOCAL_DEVELOPMENT_AUDIT_ONLY key
(local-9028773f...), explicitly NOT a trust-anchored phase0 key. AUDIT_ONLY:
promotes nothing, flips no scientific_readiness flag, signs no phase0
evaluation/review, modifies no existing receipt and does not change the manifest
(still 66 receipts / 11 modules).
"""
import base64
import hashlib
import json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-redteam-audit/benchmarks/formulation-arithmetic-dimensioned-v1"
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
harness_sha = sha((BENCH / "formulation_dimensioned_audit.py").read_bytes())

receipt = {
    "schema": "amphora.redteam-audit.formulation-arithmetic-dimensioned-v1-replay-receipt.v1",
    "authority": "AUDIT_ONLY",
    "run_type": "FORMULATION_ARITHMETIC_DIMENSIONED_REPLAY",
    "promotes_authority": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "module": "amphora-redteam-audit",
    "benchmark": "amphora-redteam-audit/formulation-arithmetic-dimensioned-v1",
    "target_module": diag["target_module"],
    "target_capability": diag["target_capability"],
    "theory": diag["theory"],
    "fitted_parameters": diag["fitted_parameters"],
    "current_module_scope_before": diag["current_module_scope_before"],
    "real_formulation_properties": diag["real_formulation"]["properties"],
    "real_formulation_equivalents": diag["real_formulation"]["equivalents"],
    "real_formulation_closure_residuals": diag["real_formulation"]["closure_residuals"],
    "barrier_gate_lambda": diag["barrier_gate_lambda"],
    "physical_sanity_reported": diag["physical_sanity_reported"],
    "known_answer_battery": diag["known_answer_battery"],
    "non_circularity": diag["non_circularity"],
    "verdict": diag["verdict"],
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "replays": 2, "independent_runs": True,
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": runb_sha,
        "harness_sha256": harness_sha,
    },
    "does_not_close": [
        "does NOT promote amphora-formulation-arithmetic to a VALIDATED "
        "scientific_readiness: phase-0 is a governance state "
        "(scientific_success_required_for_phase0=false on all live locks; 0/40 ranked "
        "modules scientific_readiness==VALIDATED) and needs two trust-anchored phase0 "
        "signatures this AUDIT_ONLY key cannot supply",
        "does NOT change the manifest (still 66 receipts / 11 modules)",
        "does NOT modify the shipped Rust engine (still MASS_ONLY) or the existing "
        "phase0-formulation-arithmetic-known-answer.v1.json fixture; this is a Python "
        "REFERENCE implementation + correctness proof of the dimensioned scope",
        "the pure-amine (TETA) AHEW/density and per-pigment oil-absorption are "
        "REFERENCE_NOMINAL public physical constants (flagged), not a measured dataset; "
        "the load-bearing densities and DGEBA EEW are read live from in-tree facts.json",
    ],
    "signing_key": {"key_id": PUB["key_id"], "authority": PUB["authority"],
                    "trust_anchored_in_phase0_store": False},
}
body = json.dumps(receipt, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.redteam-formulation-arithmetic-dimensioned+json"
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
