"""Assemble + DSSE-Ed25519-sign the Hansen temperature-envelope receipt for
amphora-solvency-score. Signs the timing-free canonical diagnostic whose bytes
reproduced identically across two independent executions (two-replay SHA-256
gate = PASS). Signs with the repo LOCAL_DEVELOPMENT_AUDIT_ONLY key, explicitly
NOT the trust-anchored phase0-evaluator key. AUDIT_ONLY: does not promote the
module, does not edit the portfolio manifest (66 receipts / 11 modules
unchanged), does not close EVALUATION_SIGNATURE_ABSENT.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

BENCH = Path("amphora-solvency-score/benchmarks/hansen-temperature-envelope-v1")
KEY = Path(".amphora/control/local-ed25519.key")
PUB = json.loads(Path(".amphora/control/local-ed25519.pub.json").read_text())
CANONICAL_SHA = "2f6718338836113d0278d10770ccc9901c3e16b5e453573a7263fefbccf944eb"

OUT_RECEIPT = Path("amphora-solvency-score/reference/mvp20/data/"
                   "hansen_temperature_envelope_receipt.v1.json")
OUT_KPI = Path("amphora-solvency-score/evidence/phase0/kpis/"
               "hansen-temperature-envelope-v1-kpi.v1.json")


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
assert diag["baseline_25c"]["matches_shipped_headline"] is True

harness_sha = sha((BENCH / "run_temperature_envelope.py").read_bytes())
h = diag["headline"]
m = diag["mechanism"]

body_obj = {
    "schema": "amphora.solvency-score.hansen-temperature-envelope-receipt.v1",
    "authority": "AUDIT_ONLY",
    "run_type": "SCIENCE_THEORY_BASELINE_REPLAY",
    "promotes_authority": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "edits_portfolio_manifest": False,
    "module": "amphora-solvency-score",
    "benchmark": "amphora-solvency-score/hansen-temperature-envelope-v1",
    "purpose": (
        "Falsification test of the temperature-invariance assumption implicit in "
        "amphora-solvency-score's shipped Hansen RED solvency verdict. The shipped "
        "rule scores every solvent-polymer pair from 25 C Hansen parameter tables "
        "with an interaction radius R that carries no temperature argument, yet "
        "marine two-part epoxy-amine coatings are applied near 5 C (ISO 12944-7 / "
        "IMO PSPC cold-end practice) and serviced near 40 C on tropical topsides. "
        "This harness applies Hansen & Beerbower's own published, zero-free-parameter "
        "HSP temperature law across that envelope on the module's CC0-1.0 Phase-0 "
        "known-answer fixture (5 polymers x 15 solvents = 75 labelled pairs) and asks "
        "whether the 25 C verdict survives its own physics. Three declared scenarios "
        "bracket the unknown thermal-expansion coefficient (alpha-free lower bound; "
        "common alpha swept 6.0e-4 .. 1.5e-3 1/K; solvent-only alpha) plus a "
        "mechanism counterfactual co-scaling R. No alpha value is invented or fitted."),
    "physical_baseline": diag["physical_baseline"],
    "fixture": diag["fixture"],
    "envelope": diag["envelope"],
    "headline_result": {
        "baseline_25c": diag["baseline_25c"],
        "law_verification": diag["law_verification"],
        "headline": h,
        "mechanism": m,
        "scenario_summaries": {
            "S0_alpha_free_lower_bound": {
                k: v for k, v in diag["scenarios"]["S0_alpha_free_lower_bound"].items()
                if k != "flips"},
            "S1_common_alpha_1.0e-03": diag["scenarios"]["S1_common_alpha"]["alpha_1.0e-03"],
            "S2_solvent_only_alpha_1.5e-03": diag["scenarios"]["S2_solvent_only_alpha"]["alpha_1.5e-03"],
            "S3_mechanism_R_co_scaled_1.0e-03": diag["scenarios"]["S3_mechanism_R_co_scaled"]["alpha_1.0e-03"],
        },
        "borderline_pairs": diag["borderline_pairs"],
        "bootstrap": diag["bootstrap"],
        "label_temperature_caveat": diag["label_temperature_caveat"],
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
        "determinism": "pure-stdlib, no wall-clock, no unpinned RNG; single pinned-seed "
                       "paired bootstrap (seed 20260731)",
    },
    "closes": [],
    "does_not_close": [
        "EVALUATION_SIGNATURE_ABSENT (trust-anchored phase0-evaluator key absent on host)",
        "module promotion to PHASE_0 (requires human dual-identity ceremony keys)",
        "portfolio manifest edit (66 receipts / 11 modules unchanged)",
        "external solubility validation (this study uses only the CC0 self-authored fixture; "
        "the externally-validated science remains the separate BigSolDB leave-solute-out benchmark)",
        "measured per-liquid thermal expansion coefficients (none present in the fixture; "
        "alpha is swept over a declared range, never fitted or invented)",
        "any re-labelling of fixture pairs (the 25 C observation labels are untouched)",
    ],
    "honest_limitations": [
        "The alpha-free lower bound (S0) flips ZERO verdicts: the alpha-independent 1.22e-3 "
        "hydrogen-bonding term alone does NOT refute H0. Non-zero thermal expansion is "
        "necessary for the refutation.",
        "The refutation is nevertheless not alpha-tuned: invariance breaks at alpha = "
        + str(h["smallest_common_alpha_that_breaks_invariance_per_k"]) +
        " 1/K, far below any real organic liquid, and the common-alpha flip count is constant "
        "across the entire declared 6.0e-4 .. 1.5e-3 1/K grid.",
        "Both paired-bootstrap CIs on the change in agreement with the 25 C label set straddle "
        "zero, so the AGGREGATE divergence is not statistically resolvable at n = 75. The "
        "durable findings are the identified boundary-crossing pairs and the fixed-R mechanism, "
        "not a headline accuracy change.",
        "Fixture labels are 25 C observations, so off-25 C counts measure divergence from the "
        "shipped verdict set, not predictive error at that temperature.",
        "R is treated as temperature-invariant in S0/S1/S2 because that is what the shipped rule "
        "does; S3 shows this is precisely where the drift originates. Whether R should co-scale "
        "is not settled by this study and would need external solubility data at two temperatures.",
        "The fixture is self-authored CC0, not an external benchmark.",
    ],
    "claim_locks": {
        "authority_ceiling": "RULE_CITED",
        "scientific_readiness": "LOCKED_INTERNAL",
        "constraint_only": True,
        "no_product_or_optimizer_authority": True,
        "self_authored_fixture_not_external_validation": True,
        "no_alpha_values_invented": True,
    },
    "provenance": {
        "primary_sources": [
            "C. M. Hansen, Hansen Solubility Parameters: A User's Handbook, 2nd ed., "
            "CRC Press 2007, ISBN 978-0-8493-7248-3 (RED sphere Eq. 1.9; Tables A.1/A.2; "
            "Ch. 1 temperature dependence)",
            "C. M. Hansen, A. Beerbower, 'Solubility Parameters', in Kirk-Othmer Encyclopedia "
            "of Chemical Technology, Suppl. Vol., 2nd ed., Wiley 1971, pp. 889-910 "
            "(origin of the d(dD)/dT, d(dP)/dT, d(dH)/dT relations applied here)",
            "ISO 12944-7 (paint application execution / substrate temperature practice) and "
            "IMO Resolution MSC.215(82) PSPC (ballast-tank coating application conditions) "
            "as the basis for the 5-40 C marine application/service envelope",
        ],
        "fixture_license": "CC0-1.0",
        "scope": "marine anti-corrosion two-part epoxy-amine (DGEBA epoxy + reference polymers) "
                 "vs coating-relevant solvents",
    },
    "signing_key": {"key_id": PUB["key_id"], "authority": PUB["authority"],
                    "trust_anchored_in_phase0_store": False},
}

payload_bytes = json.dumps(body_obj, indent=2, sort_keys=True).encode()
receipt_id = "hansen-temperature-envelope-" + sha(payload_bytes)
body_obj["receipt_id"] = receipt_id
payload_bytes = json.dumps(body_obj, indent=2, sort_keys=True).encode()

ptype = "application/vnd.amphora.hansen-temperature-envelope-receipt.v1+json"
sk = Ed25519PrivateKey.from_private_bytes(KEY.read_bytes())
sig = sk.sign(pae(ptype, payload_bytes))
envelope = {
    "payload": base64.standard_b64encode(payload_bytes).decode(),
    "payloadType": ptype,
    "signatures": [{"keyid": PUB["key_id"],
                    "sig": base64.standard_b64encode(sig).decode()}],
}
Ed25519PublicKey.from_public_bytes(bytes.fromhex(PUB["public_key_hex"])).verify(
    sig, pae(ptype, payload_bytes))

receipt = dict(body_obj)
receipt["signature"] = envelope
OUT_RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True))

ref = diag["scenarios"]["S1_common_alpha"]["alpha_1.0e-03"]
kpi = {
    "schema": "amphora.solvency-score.phase0-kpi.hansen-temperature-envelope.v1",
    "authority": "AUDIT_ONLY",
    "module": "amphora-solvency-score",
    "receipt_id": receipt_id,
    "receipt_path": str(OUT_RECEIPT),
    "receipt_sha256": None,
    "kpis": {
        "h0_verdict": h["h0_verdict"],
        "baseline_25c_correct_of_75": diag["baseline_25c"]["correct_of_75"],
        "baseline_25c_auroc": diag["baseline_25c"]["auroc"],
        "worst_case_verdict_flips_over_declared_scenarios":
            h["worst_case_verdict_flips_over_declared_scenarios"],
        "alpha_free_lower_bound_flips": h["alpha_free_lower_bound_flips"],
        "smallest_common_alpha_that_breaks_invariance_per_k":
            h["smallest_common_alpha_that_breaks_invariance_per_k"],
        "flipped_pair_ids": h["flipped_pair_ids"],
        "s3_r_co_scaled_flips": m["s3_r_co_scaled_flips"],
        "flips_removed_by_co_scaling_R": m["flips_removed_by_co_scaling_R"],
        "temperature_law_max_relative_error":
            diag["law_verification"]["max_relative_error_vs_published_derivatives"],
        "kendall_tau_b_vs_25c_min_at_alpha_1e-3": ref["kendall_tau_b_vs_25c_min"],
        "auroc_range_at_alpha_1e-3": [ref["auroc_min"], ref["auroc_max"]],
        "acc_delta_5c_minus_25c_ci95": diag["bootstrap"]["acc_delta_5c_minus_25c_ci95"],
        "acc_delta_40c_minus_25c_ci95": diag["bootstrap"]["acc_delta_40c_minus_25c_ci95"],
        "aggregate_divergence_statistically_resolvable_at_n75": False,
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
print("selfverify OK")
