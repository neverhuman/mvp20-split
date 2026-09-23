"""DSSE-Ed25519-sign the role-reactivity-ratio-substitution-effect-v1 replay receipt.

Signs the timing-free canonical diagnostic that reproduced byte-identically across two
independent runs (two-replay SHA gate = PASS). Signs with the repo
LOCAL_DEVELOPMENT_AUDIT_ONLY Ed25519 key (local-9028773f..., NOT the trust-anchored
phase0-evaluator key), matching every prior signed receipt in this module. AUDIT_ONLY: does
NOT promote the module, does NOT edit the master manifest, does NOT close
EVALUATION_SIGNATURE_ABSENT.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

BENCH = Path("amphora-molecule-role-ranker/benchmarks/role-reactivity-ratio-substitution-effect-v1")
KEY = Path(".amphora/control/local-ed25519.key")
PUB = json.loads(Path(".amphora/control/local-ed25519.pub.json").read_text())
CANON_SHA = "1f5a95d058e775985b304e0f9c60cc4caa23f3f9133fc773353258adb5322b17"


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
harness_sha = sha((BENCH / "run_reactivity_ratio.py").read_bytes())

vg = diag["validation_gate"]
atk = diag["attack"]

receipt = {
    "schema": "amphora.molecule-role-ranker.role-reactivity-ratio-substitution-effect-v1-replay-receipt.v1",
    "authority": "AUDIT_ONLY",
    "run_type": "SCIENCE_VALIDATION_REPLAY",
    "promotes_authority": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "module": "amphora-molecule-role-ranker",
    "benchmark": "amphora-molecule-role-ranker/role-reactivity-ratio-substitution-effect-v1",
    "axis": "THEORY_AND_DATA_INTEGRITY",
    "attacks": {
        "target_receipt": "role-macosko-miller-sol-latitude-v1",
        "target_claim": ("H2 direction rule: 'err amine-rich, never amine-starved' -- the "
                         "zero-fitted-parameter directional design rule for every g>f "
                         "marine-primer DGEBA+diamine pair, previously tested only under the "
                         "equal-group-reactivity idealisation"),
        "attack_method": ("independent finite-population kinetic Monte Carlo (weighted "
                          "union-find), not the recursive generating-function method used by "
                          "the target receipt, parameterised with published non-ideal "
                          "primary/secondary amine-H rate ratios instead of the equal-"
                          "reactivity idealisation"),
        "falsification_criterion": atk["hypothesis_H2_reactivity_robust"] + " " + atk["falsification_criterion"],
    },
    "purpose": diag["purpose"],
    "primary_references": diag["primary_references"],
    "reactivity_ratios_tested": diag["reactivity_ratios_tested"],
    "monte_carlo_model": diag["monte_carlo_model"],
    "headline_result": {
        "functionality_rederivation_agrees_with_fixture": diag["functionality_rederivation_agrees_with_fixture"],
        "eligible_hardeners": diag["eligible_hardeners"],
        "excluded_hardeners": diag["excluded_hardeners"],
        "validation_gate_all_pass": vg["all_pass"],
        "validation_gate_n_checks": vg["n_checks"],
        "validation_gate_tolerance": {"abs_pct_points": vg["abs_tol_pct_points"], "rel": vg["rel_tol"]},
        "n_direction_tests": atk["n_direction_tests"],
        "n_direction_holds": atk["n_direction_holds"],
        "n_reversals": atk["n_reversals"],
        "reversals": atk["reversals"],
        "verdict": diag["verdict"],
        "verdict_detail": diag["verdict_detail"],
        "interpretation": diag["interpretation"],
    },
    "validation_gate_rows": vg["rows"],
    "attack_rows": atk["rows"],
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "replays": 2, "independent_runs": True,
        "canonical_diagnostic_sha256": CANON_SHA,
        "runB_diagnostic_sha256": sha(rb),
        "harness_sha256": harness_sha,
        "fixture_sha256": diag["fixture"]["sha256"],
        "prior_receipt_diagnostic_sha256": diag["prior_receipt"]["diagnostic_sha256"],
        "determinism_basis": ("random.Random seeded by int(sha256(run-identifying-string)[:16],16) "
                              "per Monte Carlo run; no wall-clock, no OS entropy, fixed-decimal "
                              "rounding on every emitted float"),
    },
    "closes": diag["closes"],
    "does_not_close": diag["does_not_close"],
    "phase0_gap_ledger": {
        "EVALUATION_SIGNATURE_ABSENT": "trust-anchored phase0-evaluator private key absent on host (governance, not a build step)",
        "MANIFEST_UNCHANGED": "master receipts manifest (66 receipts / 11 modules) NOT edited; requires human dual-identity Phase-0 ceremony keys",
        "SCOPE": "closes the equal_reactivity_idealisation gap left open by role-macosko-miller-sol-latitude-v1, restricted to the 3 all-primary-amine fixture hardeners (IPDA, PACM, MXDA); DETA/TETA and other pre-existing-secondary-amine hardeners are out of scope (see does_not_close)",
        "SUPERSESSION": "does NOT supersede role-macosko-miller-sol-latitude-v1: the H2 direction rule is corroborated, not overturned, under both literature reactivity ratios tested",
        "MC_VS_ANALYTIC": "the Monte Carlo does not reject intra-cluster (cyclization) bonds, unlike the target receipt's analytic idealisation, so absolute sol-fraction magnitudes differ from the analytic model except at the validated equal-reactivity control; only the sign/direction of the starved-vs-rich asymmetry is claimed",
    },
    "claim_locks": diag["claim_locks"],
    "signing_key": {"key_id": PUB["key_id"], "authority": PUB["authority"],
                    "trust_anchored_in_phase0_store": False},
}
body = json.dumps(receipt, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.molecule-role-ranker-role-reactivity-ratio-substitution-effect+json"
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
