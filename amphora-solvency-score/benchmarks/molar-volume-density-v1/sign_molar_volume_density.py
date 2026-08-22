"""Assemble + DSSE-Ed25519-sign the solvency-score molar-volume/density
validation receipt.

Signs the canonical (timing-free) diagnostic whose bytes reproduced identically
across two independent executions (two-replay SHA gate = PASS). Signs with the
repo LOCAL_DEVELOPMENT_AUDIT_ONLY key -- explicitly NOT the trust-anchored
phase0-evaluator key (absent on this host). It records that the module's own
Fedors/Van-Krevelen molar-volume engine (the denominator of every HSP estimate)
is validated out-of-sample against measured liquid densities. It does NOT
promote the module and does NOT close EVALUATION_SIGNATURE_ABSENT.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

BENCH = Path("amphora-solvency-score/benchmarks/molar-volume-density-v1")
KEY = Path(".amphora/control/local-ed25519.key")
PUB = json.loads(Path(".amphora/control/local-ed25519.pub.json").read_text())
CANONICAL_SHA = "9847c803c11fdefc259757b669ad16163556e66b63665f38a4b0fd0ebe618fe5"


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
harness_sha = sha((BENCH / "run_molar_volume_density.py").read_bytes())
s = diag["summary"]

receipt = {
    "schema": "amphora.solvency-score.molar-volume-density-v1-replay-receipt.v1",
    "authority": "AUDIT_ONLY",
    "run_type": "SCIENCE_VALIDATION_REPLAY",
    "promotes_authority": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "module": "amphora-solvency-score",
    "benchmark": "amphora-solvency-score/molar-volume-density-v1",
    "purpose": (
        "Validate the Fedors/Van-Krevelen molar volume V computed by the module's "
        "own hsp.hvk_hsp() -- the denominator of every Hansen/Hildebrand "
        "solubility-parameter estimate the module makes for an unmeasured molecule "
        "(delta = f(sum F_i)/V) -- against MEASURED liquid densities of "
        "coating-relevant solvents. rho_pred = MW / V_Fedors vs experimental rho at "
        "298.15 K. Fedors' 1974 group increments are fixed constants (not fit to the "
        "data), so this is a strict out-of-sample validation of prior theory with "
        "zero train/test leakage."),
    "reference_data": diag["reference_data"],
    "engine": diag["engine"],
    "headline_result": {
        "acceptance_bar_passed": diag["benchmark_acceptance_bar_passed"],
        "gates": diag["gates"],
        "n_solvents_scored": s["n_solvents_scored"],
        "coverage_fraction_of_organic": s["coverage_fraction_of_organic"],
        "density_mae_g_per_cm3": s["density_mae_g_per_cm3"],
        "density_rmse_g_per_cm3": s["density_rmse_g_per_cm3"],
        "mean_abs_rel_err_pct": s["mean_abs_rel_err_pct"],
        "median_abs_rel_err_pct": s["median_abs_rel_err_pct"],
        "max_abs_rel_err_pct": s["max_abs_rel_err_pct"],
        "pearson_r_pred_vs_exp": s["pearson_r_pred_vs_exp"],
        "interpretation": (
            "The module's production molar-volume engine predicts the density of "
            f"{s['n_solvents_scored']} coating-relevant solvents to a median "
            f"{s['median_abs_rel_err_pct']}% (mean {s['mean_abs_rel_err_pct']}%) "
            f"absolute relative error, MAE {s['density_mae_g_per_cm3']} g/cm^3, "
            f"Pearson r {s['pearson_r_pred_vs_exp']}, out-of-sample. Accuracy is "
            "sub-0.2% for aliphatic/aromatic hydrocarbons, esters and ethers (the "
            "bulk of epoxy-coating solvents) and degrades to 15-33% only for small "
            "strongly-associated polar/halogenated liquids (formic acid, CCl4, DMSO, "
            "NMP) -- the exact domain where additive molar-volume group contribution "
            "is documented to be weakest. Validation only; no candidate, product or "
            "superiority claim."),
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "replays": 2, "independent_runs": True,
        "canonical_diagnostic_sha256": CANONICAL_SHA,
        "runB_diagnostic_sha256": runb_sha,
        "harness_sha256": harness_sha,
        "engine_file_sha256": diag["engine"]["engine_file_sha256"],
        "reference_data_sha256": diag["reference_data"]["file_sha256"],
    },
    "closes": diag["closes"],
    "does_not_close": diag["does_not_close"],
    "phase0_gap_ledger": {
        "EVALUATION_SIGNATURE_ABSENT": "trust-anchored phase0-evaluator private key absent on host (governance, not a build step)",
        "SCIENTIFIC_BENCHMARK_scope": "this validates the molar-volume denominator V only; the delta_P/delta_H polar HSP terms and the leave-solute-out solubility benchmark (bigsoldb-v1) are separate evidence",
        "RIGHTS": "BigSolDB v2.0 densities are CC-BY-4.0 DERIVATIVE_ALLOWED but promotion_eligible=false; usable for audit/diagnostic derivatives, not sufficient alone to clear a promotion gate",
        "domain_of_validity_finding": "engine is trustworthy (<3% median) for hydrocarbons/esters/ethers; abstains (fail-closed) on water/formamide; carries 15-33% error on small associated polar/halogenated liquids -- callers should treat V for those species as low-confidence",
    },
    "claim_locks": diag["claim_locks"],
    "signing_key": {"key_id": PUB["key_id"], "authority": PUB["authority"],
                    "trust_anchored_in_phase0_store": False},
}
body = json.dumps(receipt, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.solvency-molar-volume-density+json"
sk = Ed25519PrivateKey.from_private_bytes(KEY.read_bytes())
sig = sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": PUB["key_id"], "sig": base64.standard_b64encode(sig).decode()}]}
out = BENCH / "replay_receipt.v1.dsse.json"
out.write_text(json.dumps(envelope, indent=2, sort_keys=True))
print("WROTE", out)
print("receipt_body_sha256", sha(body))
print("envelope_sha256", sha(out.read_bytes()))
