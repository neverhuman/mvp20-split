"""DSSE-Ed25519-sign the role-flory-gelation-v1 replay receipt.

Signs the timing-free canonical diagnostic that reproduced byte-identically across
two independent runs (two-replay SHA gate = PASS). Signs with the repo
LOCAL_DEVELOPMENT_AUDIT_ONLY Ed25519 key (local-9028773f..., NOT the trust-anchored
phase0-evaluator key). AUDIT_ONLY: does NOT promote the module, does NOT edit the
master manifest, does NOT close EVALUATION_SIGNATURE_ABSENT.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

BENCH = Path("amphora-molecule-role-ranker/benchmarks/role-flory-gelation-v1")
KEY = Path(".amphora/control/local-ed25519.key")
PUB = json.loads(Path(".amphora/control/local-ed25519.pub.json").read_text())
CANON_SHA = "9f6557d6c01039af30f4acd9b24501f35808b4448119aa12e7d2c26465e49b41"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" "
            + str(len(body)).encode() + b" " + body)


cb = (BENCH / "diagnostic.canonical.json").read_bytes()
rb = (BENCH / "diagnostic.runB.json").read_bytes()
assert sha(cb) == CANON_SHA, f"{sha(cb)} != {CANON_SHA}"
assert sha(rb) == CANON_SHA, f"runB {sha(rb)} != {CANON_SHA} (two-replay gate)"
diag = json.loads(cb)
harness_sha = sha((BENCH / "run_flory_gel.py").read_bytes())

receipt = {
    "schema": "amphora.molecule-role-ranker.role-flory-gelation-v1-replay-receipt.v1",
    "authority": "AUDIT_ONLY",
    "run_type": "SCIENCE_VALIDATION_REPLAY",
    "promotes_authority": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "module": "amphora-molecule-role-ranker",
    "benchmark": "amphora-molecule-role-ranker/role-flory-gelation-v1",
    "purpose": diag["purpose"],
    "primary_references": diag["primary_references"],
    "headline_result": {
        "model": diag["model"]["name"],
        "fitted_parameters": diag["model"]["fitted_parameters"],
        "network_reachable_iff": diag["model"]["network_reachable_iff"],
        "functionality_rederivation_agreement_rate": diag["functionality_rederivation"]["agreement_rate"],
        "adequacy_vs_independent_identity_agreement_rate": diag["adequacy_vs_independent_identity"]["agreement_rate"],
        "n_scored_single_role": diag["adequacy_vs_independent_identity"]["n_scored_single_role"],
        "molecules_reclassified_vs_binary_rule": diag["comparison_to_prior_baseline"]["molecules_reclassified_vs_binary_rule"],
        "dgeba_diamine_gel_conversion_pc": diag["anchor_cross_check"]["dgeba_diamine_pc"],
        "anchor_matches_flory_0577": diag["anchor_cross_check"]["matches"],
        "fail_closed_all_non_single_role": diag["fail_closed"]["all_non_single_role_abstained"],
        "n_abstain": diag["fail_closed"]["n_abstain"],
        "verdict": diag["verdict"],
        "interpretation": diag["interpretation"],
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "replays": 2, "independent_runs": True,
        "canonical_diagnostic_sha256": CANON_SHA,
        "runB_diagnostic_sha256": sha(rb),
        "harness_sha256": harness_sha,
        "fixture_sha256": diag["fixture"]["sha256"],
    },
    "closes": diag["closes"],
    "does_not_close": diag["does_not_close"],
    "phase0_gap_ledger": {
        "EVALUATION_SIGNATURE_ABSENT": "trust-anchored phase0-evaluator private key absent on host (governance, not a build step)",
        "MANIFEST_UNCHANGED": "master receipts manifest (66 receipts / 11 modules) NOT edited; requires human dual-identity Phase-0 ceremony keys",
        "SCOPE": "adds an a-priori Flory-Stockmayer network-adequacy sub-grade on the self-authored CC0 fixture only; Phase-1 needs an external double-labelled expert reference set",
        "ORTHOGONALITY_FINDING": "the gate (f-1)(g-1)>1 separates network-forming monomers from mono-epoxide reactive diluents and mono-amine chain-extenders -- a physical axis the prior binary reactive-function classifier (role-parsimony-conformal-v1) cannot resolve; it adds to, not overturns, that result",
        "KINETICS": "Flory yields the thermodynamic gel-point conversion, not the cure-clock gel time; kinetic gel time remains with cure-kinetics/pot-life modules",
    },
    "claim_locks": diag["claim_locks"],
    "signing_key": {"key_id": PUB["key_id"], "authority": PUB["authority"],
                    "trust_anchored_in_phase0_store": False},
}
body = json.dumps(receipt, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.molecule-role-ranker-role-flory-gelation+json"
sk = Ed25519PrivateKey.from_private_bytes(KEY.read_bytes())
sig = sk.sign(pae(ptype, body))
sig_b64 = base64.standard_b64encode(sig).decode()
envelope = {
    "payload": base64.standard_b64encode(body).decode(),
    "payloadType": ptype,
    "signature": sig_b64,
    "signatures": [{"keyid": PUB["key_id"], "sig": sig_b64}],
}
out = BENCH / "replay_receipt.v1.dsse.json"
out.write_text(json.dumps(envelope, indent=2, sort_keys=True))
print("WROTE", out)
print("receipt_body_sha256", sha(body))
print("envelope_sha256", sha(out.read_bytes()))
