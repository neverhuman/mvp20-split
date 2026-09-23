"""DSSE-Ed25519-sign the phase0-scientific-readiness-honesty audit receipt.

Signs the canonical diagnostic whose bytes reproduced identically across two
independent executions (two-replay SHA gate = PASS). Signs with the repo
LOCAL_DEVELOPMENT_AUDIT_ONLY key (local-9028773f...), explicitly NOT a
trust-anchored phase0 key. It records a scientific-readiness honesty finding;
it modifies no existing receipt and promotes nothing.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path(".")
BENCH = Path("amphora-redteam-audit/benchmarks/phase0-scientific-readiness-honesty-v1")
KEY = Path(".amphora/control/local-ed25519.key")
PUB = json.loads(Path(".amphora/control/local-ed25519.pub.json").read_text())
CANONICAL_SHA = "a5555c6f99b20c49de11fc24eab4833814becef12efd954e09882a25aef94c03"


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
harness_sha = sha((BENCH / "phase0_scientific_readiness_honesty_audit.py").read_bytes())

receipt = {
    "schema": "amphora.redteam-audit.phase0-scientific-readiness-honesty-v1-replay-receipt.v1",
    "authority": "AUDIT_ONLY",
    "run_type": "PHASE0_SCIENTIFIC_READINESS_HONESTY_AUDIT_REPLAY",
    "promotes_authority": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "module": "amphora-redteam-audit",
    "benchmark": "amphora-redteam-audit/phase0-scientific-readiness-honesty-v1",
    "purpose": (
        "Machine-checkable red-team of what a PHASE_0 badge MEANS, for the founder "
        "report. Establishes from on-disk facts that (A) 0 of 29 Phase-0 gates require "
        "scientific success, (B) 0 signed evaluation receipts assert VALIDATED "
        "scientific readiness (only LOCKED_INTERNAL / NOT_APPLICABLE), (C) the single "
        "science module now carried at a bound Phase-0 (amphora-solvency-score) is "
        "cryptographically defensible as a governance-lock (valid trust-anchored "
        "evaluator+reviewer Ed25519 signatures, benchmark binding intact with no "
        "post-sign drift, genuine signing-identity independence), and (D) the flagship "
        "physics KPI (amphora-cure-potlife-gate Arrhenius pot-life) reproduces bit-exact "
        "via a from-scratch code path and is non-circular, yet cannot honestly promote "
        "because its dataset rights gate is not passed."),
    "A_gate_semantics_rollup": {
        "n_modules_with_phase0_gate": diag["A_gate_semantics"]["n_modules_with_phase0_gate"],
        "n_gates_requiring_scientific_success_for_phase0":
            diag["A_gate_semantics"]["n_gates_requiring_scientific_success_for_phase0"],
        "distinct_target_scientific_readiness_values":
            diag["A_gate_semantics"]["distinct_target_scientific_readiness_values"],
    },
    "B_signed_readiness_rollup": {
        "n_signed_evaluation_receipts": diag["B_signed_readiness"]["n_signed_evaluation_receipts"],
        "n_asserting_VALIDATED_scientific_readiness":
            diag["B_signed_readiness"]["n_asserting_VALIDATED_scientific_readiness"],
        "readiness_distribution": diag["B_signed_readiness"]["readiness_distribution"],
    },
    "C_solvency_crypto_reverification":
        diag["C_solvency_promotion_crypto_reverification"]["checks"] |
        {"all_checks_pass": diag["C_solvency_promotion_crypto_reverification"]["all_checks_pass"]},
    "D_cure_potlife_independent_reproduction": {
        "all_six_metrics_reproduce_bit_close":
            diag["D_cure_potlife_independent_reproduction"]["all_six_metrics_reproduce_bit_close"],
        "non_circular_cited_Ea_independent_of_scoring_data":
            diag["D_cure_potlife_independent_reproduction"]["non_circular_cited_Ea_independent_of_scoring_data"],
        "rights_gate_passed":
            diag["D_cure_potlife_independent_reproduction"]["rights_gate_passed"],
        "recomputed": diag["D_cure_potlife_independent_reproduction"]["recomputed"],
    },
    "headline_result": diag["verdict"],
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "replays": 2, "independent_runs": True,
        "canonical_diagnostic_sha256": CANONICAL_SHA,
        "runB_diagnostic_sha256": runb_sha,
        "harness_sha256": harness_sha,
    },
    "does_not_close": [
        "EVALUATION_SIGNATURE_ABSENT (trust-anchored phase0 keys not used here)",
        "does not itself remediate the 7 drifted PHASE_0 badges (governance action)",
        "does not clear cure-potlife data rights (requires rights-qualified pot-life data)",
    ],
    "does_not": diag["does_not"],
    "signing_key": {"key_id": PUB["key_id"], "authority": PUB["authority"],
                    "trust_anchored_in_phase0_store": False},
}
body = json.dumps(receipt, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.redteam-phase0-scientific-readiness-honesty+json"
sk = Ed25519PrivateKey.from_private_bytes(KEY.read_bytes())
sig = sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": PUB["key_id"], "sig": base64.standard_b64encode(sig).decode()}]}
out = BENCH / "replay_receipt.v1.dsse.json"
out.write_text(json.dumps(envelope, indent=2, sort_keys=True))
print("WROTE", out)
print("receipt_body_sha256", sha(body))
print("envelope_sha256", sha(out.read_bytes()))
