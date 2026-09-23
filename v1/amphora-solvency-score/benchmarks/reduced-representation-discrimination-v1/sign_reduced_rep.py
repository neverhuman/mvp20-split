"""Assemble + DSSE-Ed25519-sign the reduced-representation discrimination
receipt for amphora-solvency-score. Signs the timing-free canonical diagnostic
whose bytes reproduced identically across two independent executions
(two-replay SHA-256 gate = PASS). Signs with the repo
LOCAL_DEVELOPMENT_AUDIT_ONLY key (local-9028773f...), explicitly NOT the
trust-anchored phase0-evaluator key. AUDIT_ONLY: does not promote the module,
does not edit the portfolio manifest, does not close EVALUATION_SIGNATURE_ABSENT.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

BENCH = Path("amphora-solvency-score/benchmarks/reduced-representation-discrimination-v1")
KEY = Path(".amphora/control/local-ed25519.key")
PUB = json.loads(Path(".amphora/control/local-ed25519.pub.json").read_text())
CANONICAL_SHA = "1bb81064b78e1d68bf4401cf053a0a57812efef87f81474ec0e1f2d0ecc9763c"

OUT_RECEIPT = Path("amphora-solvency-score/reference/mvp20/data/"
                   "reduced_representation_discrimination_receipt.v1.json")
OUT_KPI = Path("amphora-solvency-score/evidence/phase0/kpis/"
               "reduced-representation-discrimination-v1-kpi.v1.json")


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

harness_sha = sha((BENCH / "run_reduced_rep.py").read_bytes())

body_obj = {
    "schema": "amphora.solvency-score.reduced-representation-discrimination-receipt.v1",
    "authority": "AUDIT_ONLY",
    "run_type": "SCIENCE_THEORY_BASELINE_REPLAY",
    "promotes_authority": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "edits_portfolio_manifest": False,
    "module": "amphora-solvency-score",
    "benchmark": "amphora-solvency-score/reduced-representation-discrimination-v1",
    "purpose": (
        "Independent from-scratch head-to-head of two published reduced-"
        "dimensionality simplifications of Hansen solubility space -- the Teas "
        "(1968) fractional-parameter representation and the Bagley (1971) "
        "volume-dependent (dV,dH) representation -- against the full 3-D Hansen "
        "RED sphere, on the module's CC0-1.0 Phase-0 known-answer fixture "
        "(5 polymers x 15 solvents = 75 labelled coating solvent-polymer pairs). "
        "Threshold-free AUROC is the primary metric (no cutoff tuned) with a "
        "pinned-seed paired bootstrap CI on each AUROC gap, to test whether "
        "discarding total cohesive-energy magnitude, the interaction radius R, "
        "and Hansen's factor-of-4 dispersion weighting measurably degrades "
        "compatibility discrimination. No external data; every score is an "
        "a-priori (unfitted) evaluation."),
    "physical_baseline": diag["physical_baseline"],
    "fixture": diag["fixture"],
    "headline_result": {
        "hansen_reproduction": diag["reproduction"],
        "auroc_pooled": diag["auroc_pooled"],
        "auroc_per_polymer_mean": diag["auroc_per_polymer_mean"],
        "bootstrap": diag["bootstrap"],
        "verdicts": diag["verdicts"],
        "interpretation": diag["interpretation"],
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
        "primary_sources": [
            "C. M. Hansen, Hansen Solubility Parameters: A User's Handbook, 2nd ed., CRC Press 2007, ISBN 978-0-8493-7248-3",
            "J. P. Teas, Graphic analysis of resin solubilities, Journal of Paint Technology 40(525):19-25 (1968)",
            "E. B. Bagley, T. P. Nielsen, J. M. Scigliano, Journal of Paint Technology 43(555):35-42 (1971)",
        ],
        "fixture_license": "CC0-1.0",
        "scope": "marine anti-corrosion two-part epoxy-amine (DGEBA epoxy + reference polymers) vs coating-relevant solvents",
    },
    "signing_key": {"key_id": PUB["key_id"], "authority": PUB["authority"],
                    "trust_anchored_in_phase0_store": False},
}

payload_bytes = json.dumps(body_obj, indent=2, sort_keys=True).encode()
receipt_id = "reduced-representation-discrimination-" + sha(payload_bytes)
body_obj["receipt_id"] = receipt_id
payload_bytes = json.dumps(body_obj, indent=2, sort_keys=True).encode()

ptype = "application/vnd.amphora.reduced-representation-discrimination-receipt.v1+json"
sk = Ed25519PrivateKey.from_private_bytes(KEY.read_bytes())
sig = sk.sign(pae(ptype, payload_bytes))
envelope = {
    "payload": base64.standard_b64encode(payload_bytes).decode(),
    "payloadType": ptype,
    "signatures": [{"keyid": PUB["key_id"],
                    "sig": base64.standard_b64encode(sig).decode()}],
}
# self-verify before writing
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
Ed25519PublicKey.from_public_bytes(bytes.fromhex(PUB["public_key_hex"])).verify(
    sig, pae(ptype, payload_bytes))

receipt = dict(body_obj)
receipt["signature"] = envelope
OUT_RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True))

hl = diag["auroc_pooled"]
bt = diag["bootstrap"]
kpi = {
    "schema": "amphora.solvency-score.phase0-kpi.reduced-representation-discrimination.v1",
    "authority": "AUDIT_ONLY",
    "module": "amphora-solvency-score",
    "receipt_id": receipt_id,
    "receipt_path": str(OUT_RECEIPT),
    "receipt_sha256": None,
    "kpis": {
        "hansen_reproduction_correct_of_n": diag["reproduction"]["hansen_correct_of_n"],
        "auroc_hansen_red": hl["hansen_red"],
        "auroc_teas_fractional": hl["teas_fractional"],
        "auroc_bagley_volume_dependent": hl["bagley_volume_dependent"],
        "gap_hansen_minus_teas_ci95": bt["gap_hansen_minus_teas_ci95"],
        "gap_hansen_minus_bagley_ci95": bt["gap_hansen_minus_bagley_ci95"],
        "verdict_teas": diag["verdicts"]["teas_vs_hansen"],
        "verdict_bagley": diag["verdicts"]["bagley_vs_hansen"],
        "fail_closed_rate": diag["fail_closed_rate"],
        "all_gates_pass": diag["all_gates_pass"],
    },
    "two_replay_sha256_gate": "PASS",
    "canonical_diagnostic_sha256": CANONICAL_SHA,
}
OUT_KPI.write_text(json.dumps(kpi, indent=2, sort_keys=True))
kpi["receipt_sha256"] = sha(OUT_RECEIPT.read_bytes())
OUT_KPI.write_text(json.dumps(kpi, indent=2, sort_keys=True))

print("WROTE_RECEIPT", OUT_RECEIPT)
print("WROTE_KPI", OUT_KPI)
print("receipt_id", receipt_id)
print("payload_sha256", sha(payload_bytes))
print("receipt_file_sha256", sha(OUT_RECEIPT.read_bytes()))
print("signature_len_keys", len(envelope))
print("selfverify OK")
