#!/usr/bin/env python3
"""Sign the corr-rate-qspr-v1 diagnostic with the repo LOCAL_DEVELOPMENT_AUDIT_ONLY
key -- explicitly NOT the trust-anchored phase0-evaluator key. Closes
SCIENTIFIC_BENCHMARK_NOT_EXECUTED (diagnostic); does not promote authority."""
import json, base64, hashlib
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

BENCH = Path("amphora-barrier-corrosion-score/benchmarks/corr-rate-qspr-v1")
KEY = Path(".amphora/control/local-ed25519.key")
PUB = json.loads(Path(".amphora/control/local-ed25519.pub.json").read_text())

canon_bytes = (BENCH / "diagnostic.canonical.json").read_bytes()
canon_sha = hashlib.sha256(canon_bytes).hexdigest()
runA_sha = hashlib.sha256((BENCH / "diagnostic.runA.json").read_bytes()).hexdigest()
runB_sha = hashlib.sha256((BENCH / "diagnostic.runB.json").read_bytes()).hexdigest()
diag = json.loads(canon_bytes)

receipt = {
    "schema": "amphora.barrier-corrosion-score.inhouse-benchmark-receipt.v1",
    "module": "amphora-barrier-corrosion-score",
    "benchmark": "amphora-barrier-corrosion-score/corr-rate-qspr-v1",
    "purpose": "Independent, in-tree, reproducible leave-material-out corrosion-rate "
               "QSPR diagnostic on NIST CORR-DATA. Red-teams and independently "
               "reproduces the prior (non-trust-anchored, single-run) corr-data QSPR "
               "receipts with a two-replay byte-stable gate.",
    "dataset": diag["dataset"],
    "cohort": diag["cohort"],
    "model": diag["model"],
    "headline_result_leave_material_out": diag["headline_material_safe"],
    "authority": "AUDIT_ONLY",
    "promotes_authority": False,
    "closes_gate": "SCIENTIFIC_BENCHMARK_NOT_EXECUTED",
    "does_not_close": diag["does_not_close"],
    "scope_honesty": "Substrate (bare metal/alloy) corrosion-rate QSPR. Marine "
                     "environments (Seawater, NaCl, atmospheric) are present, but this "
                     "is NOT organic epoxy-amine coating-barrier performance and creates "
                     "no coating-barrier ranking authority.",
    "red_team_note": "Prior in-tree receipts corr_data_corrosion_rate_qspr_model{,_v3_env_"
                     "features,_material_safe_v2} are signed with toolkit-reviewer-cbe8c0fd"
                     " (NOT trust-anchored), carry NO two-replay gate, and their builder "
                     "scripts are absent from the tree. This diagnostic supersedes them as "
                     "the reproducible, honestly-scoped artifact of record; those receipts "
                     "were NOT modified.",
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
    "payloadType": "application/vnd.amphora.barrier-corrosion-benchmark+json",
    "signatures": [{"keyid": PUB["key_id"],
                    "sig": base64.standard_b64encode(sig).decode()}],
}
outp = BENCH / "inhouse_benchmark_receipt.v1.dsse.json"
outp.write_text(json.dumps(envelope, indent=2, sort_keys=True))
# verify immediately
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
pub = Ed25519PublicKey.from_public_bytes(bytes.fromhex(PUB["public_key_hex"]))
pub.verify(sig, body)
print("SIGNED", outp)
print("SIGNATURE_VERIFY=PASS keyid", PUB["key_id"])
print("canonical_sha256", canon_sha)
print("two_replay", receipt["reproducibility"]["two_replay_sha256_gate"])
