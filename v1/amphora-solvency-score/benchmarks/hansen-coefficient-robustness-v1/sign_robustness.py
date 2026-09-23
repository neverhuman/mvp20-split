"""Assemble + DSSE-Ed25519-sign the Hansen-sphere coefficient-robustness
receipt for amphora-solvency-score.

Signs the timing-free canonical diagnostic whose bytes reproduced identically
across two independent executions (two-replay SHA-256 gate = PASS). Signs with
the repo LOCAL_DEVELOPMENT_AUDIT_ONLY key (local-9028773f...), explicitly NOT
the trust-anchored phase0-evaluator key. AUDIT_ONLY: does not promote the
module, does not edit the portfolio manifest, does not close
EVALUATION_SIGNATURE_ABSENT.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path(".")
BENCH = Path("amphora-solvency-score/benchmarks/hansen-coefficient-robustness-v1")
KEY = Path(".amphora/control/local-ed25519.key")
PUB = json.loads(Path(".amphora/control/local-ed25519.pub.json").read_text())
CANONICAL_SHA = "e783569022c13ec3df776caf2d80ada228aabcb130f3d2012a66d520a24472a7"

OUT_RECEIPT = Path("amphora-solvency-score/reference/mvp20/data/"
                   "hansen_sphere_coefficient_robustness_receipt.v1.json")
OUT_KPI = Path("amphora-solvency-score/evidence/phase0/kpis/"
               "hansen-sphere-coefficient-robustness-v1-kpi.v1.json")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" "
            + str(len(body)).encode() + b" " + body)


diag_bytes = (BENCH / "diagnostic.canonical.json").read_bytes()
runb_bytes = (BENCH / "diagnostic.runB.json").read_bytes()
diag_sha = sha(diag_bytes)
runb_sha = sha(runb_bytes)
assert diag_sha == CANONICAL_SHA, f"{diag_sha} != {CANONICAL_SHA}"
assert runb_sha == CANONICAL_SHA, f"runB {runb_sha} != {CANONICAL_SHA} (two-replay gate)"
diag = json.loads(diag_bytes)
assert diag["all_gates_pass"] is True, "gates did not all pass"

harness_sha = sha((BENCH / "run_robustness.py").read_bytes())
canon = diag["canonical_result"]
slc = diag["canonical_cutoff_dispersion_slice"]
grid = diag["grid"]

body_obj = {
    "schema": "amphora.solvency-score.hansen-sphere-coefficient-robustness-receipt.v1",
    "authority": "AUDIT_ONLY",
    "run_type": "SCIENCE_ROBUSTNESS_REPLAY",
    "promotes_authority": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "edits_portfolio_manifest": False,
    "module": "amphora-solvency-score",
    "benchmark": "amphora-solvency-score/hansen-coefficient-robustness-v1",
    "purpose": (
        "Independent from-scratch re-implementation of the module's Hansen RED "
        "solubility-sphere classifier (independent of the production Rust engine) "
        "on the CC0-1.0 Phase-0 known-answer fixture, followed by a "
        "falsification-oriented robustness sweep of the two free constants of the "
        "Hansen distance metric -- the dispersion weight k (published 4) and the "
        "sphere cutoff (published 1.0) -- to test whether the shipped 67/75 "
        "classification headline is robust to the choice of these constants or a "
        "fragile artifact of tuning them to this fixture. No external data; every "
        "grid cell is an a-priori (unfitted) evaluation."),
    "physical_baseline": diag["physical_baseline"],
    "fixture": diag["fixture"],
    "shipped_reference": diag["shipped_reference"],
    "headline_result": {
        "canonical_constants": {"dispersion_weight_k": 4, "sphere_cutoff": 1.0},
        "canonical_correct_of_n": f"{canon['correct']}/{canon['n']}",
        "canonical_accuracy": canon["accuracy"],
        "canonical_false_compatible": canon["false_compatible"],
        "canonical_min_per_polymer_accuracy": canon["min_per_polymer_accuracy"],
        "majority_class_base_rate": diag["fixture"]["majority_class_base_rate"],
        "dispersion_slice_at_cutoff_1p0_by_k": slc["by_k"],
        "dispersion_argmax_k": slc["argmax_k"],
        "grid_cells_ge_0p85_bar": f"{grid['cells_ge_acceptance_bar']}/{grid['cells_total']}",
        "grid_best_cell": grid["best_cell"],
        "canonical_vs_grid_max_gap_pairs": grid["canonical_vs_best_gap_pairs"],
        "interpretation": (
            "Independent reproduction is exact: the from-scratch Hansen RED "
            "classifier at the published constants (k=4, cutoff=1.0) scores 67/75 "
            "= 0.8933, matching the shipped Phase-0 headline, with zero "
            "high-confidence false-compatibles and 0.80 worst-polymer generalization. "
            "Robustness: holding the sphere boundary at its published value 1.0, "
            "classification accuracy over the fixture peaks EXACTLY at Hansen's "
            "theoretical dispersion weight k=4 (63,65,66,67,66,62,59 correct for "
            "k=1,2,3,4,5,6,8) -- an independent corroboration of the factor-of-4 "
            "from data. Across the full published-plausible 7x7 (k, cutoff) "
            "envelope the a-priori canonical operating point sits only 3 pairs "
            "(<=5%) below the post-hoc grid maximum (k=8, cutoff=1.3, 70/75); the "
            "2-D argmax drifts along a ridge only because k and cutoff are "
            "partially degenerate (scaling k rescales Ra against the cutoff), which "
            "the physical 1-D slice removes. The shipped headline is therefore a "
            "robust, near-optimal, un-tuned operating point rather than a fragile "
            "constant-tuning artifact. Applicability-domain: 6/6 non-physical "
            "inputs (NaN / +Inf / negative HSP / zero or negative radius / missing "
            "field) fail closed to abstention."),
    },
    "gates": diag["gates"],
    "all_gates_pass": diag["all_gates_pass"],
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "replays": 2,
        "independent_runs": True,
        "canonical_diagnostic_sha256": CANONICAL_SHA,
        "runB_diagnostic_sha256": runb_sha,
        "harness_sha256": harness_sha,
        "fixture_sha256": diag["fixture"]["sha256"],
        "shipped_result_sha256": diag["shipped_reference"]["sha256"],
    },
    "closes": [],
    "does_not_close": [
        "EVALUATION_SIGNATURE_ABSENT (trust-anchored phase0-evaluator key absent on host)",
        "module promotion to PHASE_0 (requires human dual-identity ceremony keys)",
        "portfolio manifest edit (66 receipts / 11 modules unchanged)",
        "external solubility validation (this study uses only the CC0 self-authored fixture; the externally-validated science remains the separate BigSolDB leave-solute-out benchmark)",
    ],
    "claim_locks": {
        "authority_ceiling": "RULE_CITED",
        "scientific_readiness": "LOCKED_INTERNAL",
        "constraint_only": True,
        "no_product_or_optimizer_authority": True,
        "self_authored_fixture_not_external_validation": True,
    },
    "provenance": {
        "primary_source": "C. M. Hansen, Hansen Solubility Parameters: A User's Handbook, 2nd ed., CRC Press 2007, ISBN 978-0-8493-7248-3",
        "fixture_license": "CC0-1.0",
        "scope": "marine anti-corrosion two-part epoxy-amine (DGEBA epoxy + linear/uncured reference polymers) vs coating-relevant solvents",
    },
    "signing_key": {"key_id": PUB["key_id"], "authority": PUB["authority"],
                    "trust_anchored_in_phase0_store": False},
}

# receipt_id is content-derived over the signed payload
payload_bytes = json.dumps(body_obj, indent=2, sort_keys=True).encode()
receipt_id = "hansen-sphere-coeff-robustness-" + sha(payload_bytes)
body_obj["receipt_id"] = receipt_id
payload_bytes = json.dumps(body_obj, indent=2, sort_keys=True).encode()

ptype = "application/vnd.amphora.hansen-sphere-coefficient-robustness-receipt.v1+json"
sk = Ed25519PrivateKey.from_private_bytes(KEY.read_bytes())
sig = sk.sign(pae(ptype, payload_bytes))
envelope = {
    "payload": base64.standard_b64encode(payload_bytes).decode(),
    "payloadType": ptype,
    "signatures": [{"keyid": PUB["key_id"],
                    "sig": base64.standard_b64encode(sig).decode()}],
}

receipt = dict(body_obj)
receipt["signature"] = envelope
OUT_RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True))

kpi = {
    "schema": "amphora.solvency-score.phase0-kpi.hansen-sphere-coefficient-robustness.v1",
    "authority": "AUDIT_ONLY",
    "module": "amphora-solvency-score",
    "receipt_id": receipt_id,
    "receipt_path": str(OUT_RECEIPT),
    "receipt_sha256": None,  # filled after write below
    "kpis": {
        "reproduction_correct_of_n": f"{canon['correct']}/{canon['n']}",
        "reproduction_accuracy": canon["accuracy"],
        "dispersion_argmax_k_at_cutoff_1p0": slc["argmax_k"],
        "canonical_vs_grid_max_gap_pairs": grid["canonical_vs_best_gap_pairs"],
        "grid_cells_ge_0p85_bar": grid["cells_ge_acceptance_bar"],
        "grid_cells_total": grid["cells_total"],
        "fail_closed_rate": diag["fail_closed_rate"],
        "all_gates_pass": diag["all_gates_pass"],
    },
    "two_replay_sha256_gate": "PASS",
    "canonical_diagnostic_sha256": CANONICAL_SHA,
}
OUT_KPI.write_text(json.dumps(kpi, indent=2, sort_keys=True))
# bind receipt sha into kpi
kpi["receipt_sha256"] = sha(OUT_RECEIPT.read_bytes())
OUT_KPI.write_text(json.dumps(kpi, indent=2, sort_keys=True))

print("WROTE_RECEIPT", OUT_RECEIPT)
print("WROTE_KPI", OUT_KPI)
print("receipt_id", receipt_id)
print("payload_sha256", sha(payload_bytes))
print("receipt_file_sha256", sha(OUT_RECEIPT.read_bytes()))
print("signature_len_keys", len(envelope))
