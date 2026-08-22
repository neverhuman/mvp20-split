"""DSSE-Ed25519-sign the role-parsimony-conformal-v1 replay receipt.

Signs the canonical timing-free diagnostic that reproduced byte-identically
across two independent runs (two-replay SHA gate = PASS). Signs with the repo
LOCAL_DEVELOPMENT_AUDIT_ONLY Ed25519 key (local-9028773f..., NOT the
trust-anchored phase0-evaluator key). AUDIT_ONLY: does NOT promote the module,
does NOT edit the master manifest, does NOT close EVALUATION_SIGNATURE_ABSENT.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

BENCH = Path("amphora-molecule-role-ranker/benchmarks/role-parsimony-conformal-v1")
KEY = Path(".amphora/control/local-ed25519.key")
PUB = json.loads(Path(".amphora/control/local-ed25519.pub.json").read_text())
CANON_SHA = "075aeaaf8204c712838e41a3c8b42d89f974d1454c65fe75e1862c14700b3ba2"


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
harness_sha = sha((BENCH / "run_role_parsimony_conformal.py").read_bytes())

receipt = {
    "schema": "amphora.molecule-role-ranker.role-parsimony-conformal-v1-replay-receipt.v1",
    "authority": "AUDIT_ONLY",
    "run_type": "SCIENCE_VALIDATION_REPLAY",
    "promotes_authority": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "module": "amphora-molecule-role-ranker",
    "benchmark": "amphora-molecule-role-ranker/role-parsimony-conformal-v1",
    "purpose": diag["purpose"],
    "primary_references": [
        "Efron, B. (1979) Bootstrap methods. Ann. Statist. 7(1):1-26.",
        "Vovk, Gammerman, Shafer (2005) Algorithmic Learning in a Random World (conformal prediction), ISBN 978-0-387-00152-4.",
        "Papadopoulos, H. (2008) Inductive Conformal Prediction. In Tools in AI, doi:10.5772/6078.",
        "Pedregosa et al. (2011) scikit-learn. JMLR 12:2825-2830 (LogisticRegression, L2/lbfgs).",
    ],
    "headline_result": {
        "frozen_artifact_reproduced_within_1e_3": diag["reproduction_of_frozen_artifact"]["frozen_reproducible_within_tol_1e_3"],
        "max_abs_coefficient_diff": diag["reproduction_of_frozen_artifact"]["max_abs_coefficient_diff"],
        "fitted_loocv_accuracy": diag["fitted_model_out_of_sample"]["loocv_accuracy"],
        "fitted_loocv_accuracy_ci95": diag["fitted_model_out_of_sample"]["loocv_accuracy_bootstrap_ci95"],
        "deterministic_rule_accuracy": diag["deterministic_rule_baseline"]["in_domain_accuracy"],
        "noninferiority_verdict": diag["noninferiority_test"]["verdict"],
        "accuracy_gap_det_minus_fitted_ci95": diag["noninferiority_test"]["accuracy_gap_bootstrap_ci95"],
        "hostile_null_det_abstain_rate": diag["hostile_null_safety"]["deterministic_rule_abstain_rate"],
        "hostile_null_raw_logistic_abstain_rate": diag["hostile_null_safety"]["raw_logistic_abstain_rate"],
        "conformal_coverage_alpha_0_10": diag["conformal_prediction"]["alpha_0.10"]["empirical_marginal_coverage"],
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
        "SCOPE": "validates the frozen role classifier on the self-authored CC0 fixture only; Phase-1 needs an external double-labelled expert reference set",
        "PARSIMONY_FINDING": "the frozen 6-parameter logistic buys zero out-of-sample accuracy over the 0-parameter deterministic reactive-function rule; the rule is also strictly safer on hostile nulls (12/12 fail-closed vs 0/12)",
    },
    "claim_locks": diag["claim_locks"],
    "signing_key": {"key_id": PUB["key_id"], "authority": PUB["authority"],
                    "trust_anchored_in_phase0_store": False},
}
body = json.dumps(receipt, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.molecule-role-ranker-role-parsimony-conformal+json"
sk = Ed25519PrivateKey.from_private_bytes(KEY.read_bytes())
sig = sk.sign(pae(ptype, body))
sig_b64 = base64.standard_b64encode(sig).decode()
envelope = {
    "payload": base64.standard_b64encode(body).decode(),
    "payloadType": ptype,
    # top-level `signature` mirrors signatures[0].sig so downstream `.signature`
    # checks resolve; canonical DSSE `signatures` array retained below.
    "signature": sig_b64,
    "signatures": [{"keyid": PUB["key_id"], "sig": sig_b64}],
}
out = BENCH / "replay_receipt.v1.dsse.json"
out.write_text(json.dumps(envelope, indent=2, sort_keys=True))
print("WROTE", out)
print("receipt_body_sha256", sha(body))
print("envelope_sha256", sha(out.read_bytes()))
