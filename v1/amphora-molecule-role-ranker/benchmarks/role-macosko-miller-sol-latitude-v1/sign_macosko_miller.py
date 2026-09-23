"""DSSE-Ed25519-sign the role-macosko-miller-sol-latitude-v1 replay receipt.

Signs the timing-free canonical diagnostic that reproduced byte-identically across two
independent runs (two-replay SHA gate = PASS). Signs with the repo
LOCAL_DEVELOPMENT_AUDIT_ONLY Ed25519 key (local-9028773f..., NOT the trust-anchored
phase0-evaluator key). AUDIT_ONLY: does NOT promote the module, does NOT edit the
master manifest, does NOT close EVALUATION_SIGNATURE_ABSENT.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

BENCH = Path("amphora-molecule-role-ranker/benchmarks/role-macosko-miller-sol-latitude-v1")
KEY = Path(".amphora/control/local-ed25519.key")
PUB = json.loads(Path(".amphora/control/local-ed25519.pub.json").read_text())
CANON_SHA = "ceedff0feb1ac4c437e5d4401473f5086882ec2c0480fd5dafb2b60697554b66"


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
harness_sha = sha((BENCH / "run_macosko_miller.py").read_bytes())

s1 = diag["study_1_reduction_to_shipped_baseline"]
s2 = diag["study_2_stoichiometric_latitude"]
s3 = diag["study_3_reactive_diluent_ceiling"]
asym = s2["sol_asymmetry_starved_over_rich_at_pm30pct"]
rule = s2["sol_asymmetry_direction_rule"]

receipt = {
    "schema": "amphora.molecule-role-ranker.role-macosko-miller-sol-latitude-v1-replay-receipt.v1",
    "authority": "AUDIT_ONLY",
    "run_type": "SCIENCE_VALIDATION_REPLAY",
    "promotes_authority": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "module": "amphora-molecule-role-ranker",
    "benchmark": "amphora-molecule-role-ranker/role-macosko-miller-sol-latitude-v1",
    "axis": "THEORY",
    "purpose": diag["purpose"],
    "primary_references": diag["primary_references"],
    "hypotheses": diag["hypotheses"],
    "headline_result": {
        "model": diag["model"]["name"],
        "fitted_parameters": diag["model"]["fitted_parameters"],
        "gel_criterion": diag["model"]["gel_criterion"],
        "stoichiometric_window": diag["model"]["stoichiometric_window"],
        "functionality_rederivation_agreement_rate":
            diag["functionality_rederivation"]["agreement_rate"],
        "H1_reduction_n_pairs": s1["n_pairs"],
        "H1_max_abs_err_vs_shipped_flory_stockmayer": s1["max_abs_err_pc_vs_flory_stockmayer"],
        "H1_reduction_exact_to_1e_12": s1["reduction_exact_to_1e_12"],
        "H1_max_abs_err_numerical_sol_bifurcation_vs_analytic_gel":
            s1["max_abs_err_numerical_sol_bifurcation_vs_analytic_gel"],
        "H1_prior_signed_gel_table_rows_reproduced":
            f"{s1['prior_table_pairs_agreeing']}/{s1['prior_table_pairs_matched']}",
        "H0_part_i_all_gel_capable_pairs_survive_pm5pct_envelope":
            s2["all_gel_capable_pairs_survive_pm5pct_envelope"],
        "n_gel_capable_pairs_at_r1": s2["n_gel_capable_at_r1"],
        "H0_part_ii_sol_asymmetry_at_pm30pct_index": {
            "min": asym["min"], "max": asym["max"],
            "n_pairs_off_by_more_than_2x": asym["n_pairs_off_by_more_than_2x_either_direction"],
            "n_pairs": asym["n_pairs"],
        },
        "H2_direction_rule_holds_on_all_f_ne_g_pairs": rule["rule_holds_on_all_f_ne_g_pairs"],
        "H2_counts": {
            "g_gt_f": f"{rule['n_correct_g_gt_f']}/{rule['n_pairs_g_gt_f']}",
            "f_gt_g": f"{rule['n_correct_f_gt_g']}/{rule['n_pairs_f_gt_g']}",
            "f_eq_g_ties": rule["n_pairs_f_eq_g"],
        },
        "reactive_diluent_ceiling_wt_pct_range": [s3["critical_diluent_wt_pct_min"],
                                                  s3["critical_diluent_wt_pct_max"]],
        "reactive_diluent_closed_form": s3["closed_form"],
        "reactive_diluent_analytic_matches_numeric": s3["analytic_matches_numeric_bisection"],
        "fail_closed_n_abstain": diag["fail_closed"]["n_abstain"],
        "verdict": diag["verdict"],
        "verdict_detail": diag["verdict_detail"],
        "interpretation": diag["interpretation"],
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "replays": 2, "independent_runs": True,
        "canonical_diagnostic_sha256": CANON_SHA,
        "runB_diagnostic_sha256": sha(rb),
        "harness_sha256": harness_sha,
        "fixture_sha256": diag["fixture"]["sha256"],
        "prior_receipt_diagnostic_sha256": s1["prior_receipt_diagnostic_sha256"],
        "determinism_basis": ("fixed-iteration bisection (no tolerance loop, no RNG, no "
                              "wall-clock), fixed-decimal rounding on every emitted float"),
    },
    "closes": diag["closes"],
    "does_not_close": diag["does_not_close"],
    "phase0_gap_ledger": {
        "EVALUATION_SIGNATURE_ABSENT": "trust-anchored phase0-evaluator private key absent on host (governance, not a build step)",
        "MANIFEST_UNCHANGED": "master receipts manifest (66 receipts / 11 modules) NOT edited; requires human dual-identity Phase-0 ceremony keys",
        "SCOPE": "generalises the module's own signed Flory-Stockmayer network gate on the self-authored CC0 fixture; Phase-1 needs an external measured sol-fraction / extractables reference set",
        "SUPERSESSION": "does NOT supersede role-flory-gelation-v1: Macosko-Miller reduces to it exactly at r=1 with monodisperse functionality (max abs err 0.0 over 144 pairs); the prior verdict stands and is extended, not overturned",
        "IDEALISATION": "equal group reactivity and no intramolecular cyclization; the primary-vs-secondary amine substitution effect is representable in Macosko-Miller but no rights-clean rate ratios are pinned in the portfolio",
        "ETHERIFICATION": "amine-starved sol figures are an UPPER bound because epoxide homopolymerisation would consume part of the excess epoxide",
    },
    "claim_locks": diag["claim_locks"],
    "signing_key": {"key_id": PUB["key_id"], "authority": PUB["authority"],
                    "trust_anchored_in_phase0_store": False},
}
body = json.dumps(receipt, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.molecule-role-ranker-role-macosko-miller-sol-latitude+json"
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
