#!/usr/bin/env python3
"""Sign the corr-rate-qspr-v1 SIGNIFICANCE addendum with the repo
LOCAL_DEVELOPMENT_AUDIT_ONLY key -- explicitly NOT the trust-anchored
phase0-evaluator key. AUDIT_ONLY: closes nothing, promotes no authority,
modifies none of the 66 signed receipts nor the existing signed diagnostic."""
import json, base64, hashlib
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

BENCH = Path("amphora-barrier-corrosion-score/benchmarks/corr-rate-qspr-v1")
KEY = Path(".amphora/control/local-ed25519.key")
PUB = json.loads(Path(".amphora/control/local-ed25519.pub.json").read_text())

canon_bytes = (BENCH / "significance.canonical.json").read_bytes()
canon_sha = hashlib.sha256(canon_bytes).hexdigest()
runA_sha = hashlib.sha256((BENCH / "significance.runA.json").read_bytes()).hexdigest()
runB_sha = hashlib.sha256((BENCH / "significance.runB.json").read_bytes()).hexdigest()
diag = json.loads(canon_bytes)

receipt = {
    "schema": "amphora.barrier-corrosion-score.corr-rate-qspr-significance-receipt.v1",
    "module": "amphora-barrier-corrosion-score",
    "benchmark": "amphora-barrier-corrosion-score/corr-rate-qspr-v1",
    "purpose": "Rigorous significance validation of the leave-material-out "
               "corrosion-rate QSPR: paired material-cluster bootstrap on Delta-RMSE "
               "(vs strongest naive baseline) and a label-permutation null on the "
               "leave-material-out R^2. Establishes whether the ~0.32 R^2 skill is "
               "real, group-safe signal or chance -- the honest scientific gate "
               "before any Phase-0 consideration.",
    "dataset": diag["dataset"],
    "cohort": diag["cohort"],
    "point_estimates_this_host": diag["point_estimates_this_host"],
    "test_1_paired_cluster_bootstrap_delta_rmse": diag["test_1_paired_cluster_bootstrap_delta_rmse"],
    "test_2_label_permutation_null_r2": diag["test_2_label_permutation_null_r2"],
    "verdict": diag["verdict"],
    "host_env": diag["host_env"],
    "reproducibility_note_prior_diagnostic": diag["reproducibility_note_prior_diagnostic"],
    "authority": "AUDIT_ONLY",
    "promotes_authority": False,
    "closes_gate": None,
    "does_not_close": diag["does_not_close"],
    "scope_honesty": "Substrate (bare metal/alloy) corrosion-rate QSPR on NIST "
                     "CORR-DATA. Marine environments (Seawater, NaCl, atmospheric) are "
                     "present, but this is NOT organic epoxy-amine COATING-BARRIER "
                     "performance and creates no coating-barrier ranking authority. "
                     "A validated substrate-corrosion signal does not by itself make "
                     "amphora-barrier-corrosion-score (a coating-barrier capability) "
                     "Phase-0; the rights-clean coating-barrier benchmark does not yet "
                     "exist (the coating-relevant polyverse diffusivity data is "
                     "CONTEXT_ONLY quarantined).",
    "reproducibility": {
        "replays": 2,
        "two_replay_sha256_gate": "PASS" if runA_sha == runB_sha == canon_sha else "FAIL",
        "run_a_canonical_sha256": runA_sha,
        "run_b_canonical_sha256": runB_sha,
        "canonical_sha256": canon_sha,
        "determinism": diag["determinism"],
    },
    "signing_key": {"key_id": PUB["key_id"], "authority": PUB["authority"],
                    "trust_anchored_in_phase0_store": False},
    "organizational_independence_asserted": False,
    "human_review_performed": False,
}
body = json.dumps(receipt, indent=2, sort_keys=True).encode()
sk = Ed25519PrivateKey.from_private_bytes(KEY.read_bytes())
sig = sk.sign(body)
envelope = {
    "payload": base64.standard_b64encode(body).decode(),
    "payloadType": "application/vnd.amphora.barrier-corrosion-significance+json",
    "signatures": [{"keyid": PUB["key_id"],
                    "sig": base64.standard_b64encode(sig).decode()}],
}
outp = BENCH / "significance_receipt.v1.dsse.json"
outp.write_text(json.dumps(envelope, indent=2, sort_keys=True))
pub = Ed25519PublicKey.from_public_bytes(bytes.fromhex(PUB["public_key_hex"]))
pub.verify(sig, body)
print("SIGNED", outp)
print("SIGNATURE_VERIFY=PASS keyid", PUB["key_id"])
print("canonical_sha256", canon_sha)
print("two_replay", receipt["reproducibility"]["two_replay_sha256_gate"])
print("overall_verdict", receipt["verdict"]["overall"])
