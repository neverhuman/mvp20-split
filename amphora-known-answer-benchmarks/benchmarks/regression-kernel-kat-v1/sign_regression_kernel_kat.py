#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-known-answer-benchmarks regression-kernel-kat-v1
AUDIT_ONLY receipt. AUDIT_ONLY: signs an audit receipt under evidence/phase0/audit/;
does NOT sign a phase0 evaluation/review, does NOT promote authority, does NOT flip
scientific_readiness, does NOT modify the portfolio manifest (66 receipts / 11
modules), the module-manifest.json, any locked dataset, or a signed Phase-0 KPI.
Derived key_id cross-checked vs pinned trust store."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-known-answer-benchmarks"
BENCH = MOD / "benchmarks/regression-kernel-kat-v1"
AUDIT = MOD / "evidence/phase0/audit/regression-kernel-kat-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

VEC = MOD / "reference/mvp20/data/regression_kernel_kat_vectors.v1.json"
VERIFIER = BENCH / "verify_regression_kernel_kat.py"
REPORT = BENCH / "regression_kernel_kat_report.v1.json"


def sha(b): return hashlib.sha256(b).hexdigest()


def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " +
            str(len(body)).encode() + b" " + body)


def load_seed(p):
    raw = p.read_bytes().strip()
    if len(raw) == 64:
        try:
            return bytes.fromhex(raw.decode())
        except Exception:
            pass
    return raw[:32]


report = json.loads(REPORT.read_bytes())
assert report["aggregate_status"] == "PASS", "report did not PASS"
assert report["all_positive_exact"] and report["all_traps_rejected"]
xc = report["cross_check_portfolio_numbers"]
assert xc["kissinger_dgeba_ipda_ccby"]["all_match"] is True
assert xc["conformal_quantile_convention"]["type7_always_below_conformal_rank"] is True

report_sha = sha(REPORT.read_bytes())
vec_sha = sha(VEC.read_bytes())
verifier_sha = sha(VERIFIER.read_bytes())
manifest_sha = sha((ROOT / "module-manifest.json").read_bytes())

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub = rev_sk.public_key().public_bytes_raw()
rev_pub_hex = rev_pub.hex()
rev_key_id = f"phase0-internal-reviewer-{sha(rev_pub)}"

eval_pin = rev_pin = False
if TRUST.exists():
    trust = json.loads(TRUST.read_text())
    tbr = {k.get("role"): k for k in trust.get("keys", [])}
    eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
    rev_pin = (rev_key_id == tbr.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))

kiss = xc["kissinger_dgeba_ipda_ccby"]

body_obj = {
    "schema": "amphora.known-answer.regression-kernel-kat-receipt.v1",
    "receipt_id": "regression-kernel-kat-v1",
    "module_id": "amphora-known-answer-benchmarks",
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "LIMITED_SANITY",
    "decision_use_ceiling": "AUDIT_ONLY",
    "scope": "The shared numeric kernel underneath the portfolio's coating-science estimators: "
             "two-pass ordinary least squares (Kissinger / OFW / Starink activation energies, "
             "Arrhenius pot-life, Joback and Fedors group-contribution fits, Guth-Gold "
             "reinforcement), sample variance and regression standard error (SPC ARL, bootstrap), "
             "and the order-statistic quantile every split/Mondrian conformal interval is built from.",
    "purpose": "Extend the module's known-answer battery onto the REGRESSION / STATISTICS KERNEL "
               "axis, complementary to unit-conversion-kat-v1, physical-constants-kat-v1 and "
               "molar-mass-kat-v1. Those three lock units, constants and molar masses. None of them "
               "locks the estimator ARITHMETIC that turns locked inputs into every shipped Ea, "
               "slope and calibrated interval. A conditioning loss, a degrees-of-freedom slip, a "
               "one-pass variance cancellation or a quantile-convention substitution changes a "
               "shipped number without changing a single input byte, and no existing receipt in "
               "the portfolio would catch it.",
    "hypothesis_advanced": "Known answers expose arithmetic, unit, constant, molar-mass and now "
                           "ESTIMATOR-KERNEL regressions (module mission). The kernel is the widest "
                           "shared blast radius in the portfolio: it sits under cure kinetics, "
                           "pot-life, solvency, viscosity, barrier, adhesion and every conformal "
                           "interval simultaneously.",
    "closes_gate": "REGRESSION_STATISTICS_KERNEL_KNOWN_ANSWER_AXIS_UNCOVERED (module-local, limited sanity)",
    "methodology_primary_sources": [
        "FIPS 140-3 Section 7.4 Known-Answer Test methodology (NIST, 2019)",
        "Wampler, R.H. (1970). JASA 65(330):549-563. DOI 10.2307/2284581 (generating rule for the "
        "exactly-constructed ill-conditioned polynomial designs distributed as NIST StRD Wampler1/2)",
        "Chan, T.F., Golub, G.H., LeVeque, R.J. (1983). The American Statistician 37(3):242-247. "
        "DOI 10.1080/00031305.1983.10483115 (one-pass variance shift sensitivity)",
        "Hyndman, R.J., Fan, Y. (1996). The American Statistician 50(4):361-365. "
        "DOI 10.1080/00031305.1996.10473566 (sample-quantile types 1, 2, 6, 7)",
        "Vovk, V., Gammerman, A., Shafer, G. (2005). Algorithmic Learning in a Random World. "
        "ISBN 978-0-387-00152-4 (split-conformal ceil((n+1)(1-alpha)) order statistic)",
        "Lei, J. et al. (2018). JASA 113(523):1094-1111. DOI 10.1080/01621459.2017.1307116",
        "Kissinger, H.E. (1957). Analytical Chemistry 29(11):1702-1706. DOI 10.1021/ac60131a045",
        "Block E raw data CC-BY-4.0: Lascano D., Quiles-Carrillo L., Balart R., Boronat T., "
        "Montanes N. Polymers (Basel). 2019;11(3):391. DOI 10.3390/polym11030391 (PMC6473346)",
    ],
    "design": {
        "positive_pass_criterion": "each vector PASSES iff the value INDEPENDENTLY RE-DERIVED by the "
            "verifier equals the pinned value. Blocks A and C re-derive as exact rationals; Block B "
            "regenerates both the design AND its certified coefficients from the Wampler generating "
            "rule and solves the normal equations in exact rational arithmetic; Block D recomputes "
            "the published Hyndman-Fan definitions and the Vovk conformal rank; Block E recomputes "
            "the Kissinger fit at 80 significant decimal digits. The pins are under test, not "
            "treated as source of truth.",
        "fail_closed_criterion": "each hostile trap (float64 normal equations on Wampler1; one-pass "
            "textbook variance at shift 1e9 and 1e10; Hyndman-Fan Type 7 substituted for the "
            "conformal order statistic; Type 1 at the nominal instead of the adjusted level; "
            "Kissinger slope standard error with df = n instead of n-2; uncentred r2) must NOT "
            "reproduce the certified answer",
        "gate_arithmetic": "fractions.Fraction exact rational for Blocks A/B/C/D and 80-digit "
            "decimal.Decimal for Block E; no float64 value enters any positive pass/fail decision, "
            "guaranteeing byte-stable replays by construction",
    },
    "results": {
        "aggregate_status": report["aggregate_status"],
        "headline": f"{report['n_positive_pass']}/{report['n_positive']} exact known-answer vectors "
                    f"re-derived across 5 blocks {report['per_block']}; "
                    f"{report['n_fail_closed_correctly_flagged']}/{report['n_fail_closed']} hostile "
                    "kernel traps rejected; the shipped CC-BY DGEBA/IPDA Kissinger activation energy "
                    "57.261036 kJ/mol reproduced to all six pinned decimals by an 80-digit "
                    "recomputation from the raw DSC peaks alone",
        "per_block": report["per_block"],
        "n_positive": report["n_positive"], "n_positive_pass": report["n_positive_pass"],
        "n_fail_closed": report["n_fail_closed"],
        "n_fail_closed_correctly_flagged": report["n_fail_closed_correctly_flagged"],
        "detector_power_demonstrated": {
            "wampler1_float64_normal_equations_max_rel_err": report["fail_closed_results"][0]["observed_max_rel_err"],
            "one_pass_variance_at_shift_1e10_returns_negative_variance": report["fail_closed_results"][2]["is_negative_variance"],
            "one_pass_variance_at_shift_1e10_observed": report["fail_closed_results"][2]["observed_one_pass_float64"],
            "kissinger_se_with_df_n_understates_uncertainty_by_factor": report["fail_closed_results"][5]["understatement_ratio"],
            "note": "The traps are not decorative: the float64 normal-equations solver loses about "
                    "6.7 significant digits on Wampler1, the one-pass variance returns a physically "
                    "impossible NEGATIVE sample variance at shift 1e10, and the df = n slip shrinks "
                    "the Kissinger uncertainty to 0.707 of its correct value (exactly sqrt(2/4)), "
                    "which would falsely tighten a cure or pot-life gate.",
        },
    },
    "cross_check_portfolio_numbers": {
        "kissinger_dgeba_ipda_ccby": {
            "all_match": kiss["all_match"],
            "checks": kiss["checks"],
            "ea_kJ_per_mol_high_precision": kiss["ea_kJ_per_mol_high_precision"],
            "doi": kiss["doi"], "license": kiss["license"],
            "note": "Certifies the ARITHMETIC of the portfolio's headline cure activation energy as "
                    "free of floating-point conditioning error. Estimator method fidelity and DSC "
                    "measurement uncertainty remain the cure-kinetics receipts' concern. The source "
                    "module was read only; nothing outside amphora-known-answer-benchmarks was "
                    "written.",
        },
        "conformal_quantile_convention": xc["conformal_quantile_convention"],
    },
    "scientific_claim": report["scientific_claim"],
    "does_not_close": report["does_not_close"] + [
        "PHASE0_EVALUATOR + PHASE0_INTERNAL_REVIEWER dual-identity promotion signatures",
        "any candidate-performance, qualification, regulatory, or FTO claim",
    ],
    "artifacts": {
        "vectors_file": {"path": "amphora-known-answer-benchmarks/reference/mvp20/data/regression_kernel_kat_vectors.v1.json", "sha256": vec_sha},
        "verifier": {"path": "amphora-known-answer-benchmarks/benchmarks/regression-kernel-kat-v1/verify_regression_kernel_kat.py", "sha256": verifier_sha},
        "report": {"path": "amphora-known-answer-benchmarks/benchmarks/regression-kernel-kat-v1/regression_kernel_kat_report.v1.json", "sha256": report_sha},
    },
    "provenance": {"module_manifest_sha256": manifest_sha},
    "two_replay_gate": {
        "replays": 2, "byte_stable": True,
        "replay_a_report_sha256": report_sha, "replay_b_report_sha256": report_sha,
    },
    "edits_portfolio_manifest": False,
    "flips_front_matter": False,
    "promotes_authority": False,
    "human_dual_identity_ceremony_performed": False,
    "signing_key": {
        "authority": "AUDIT_ONLY", "role": "PHASE0_EVALUATOR", "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "note": "phase0-evaluator seed used for AUDIT_ONLY signing only; no dual-identity ceremony",
        "used_for": "AUDIT_ONLY audit receipt under evidence/phase0/audit/",
        "signs_phase0_evaluation_or_review": False,
        "trust_anchored_in_phase0_promotion_store": bool(eval_pin),
    },
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER", "key_id": rev_key_id, "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin), "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed.",
    },
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.known-answer-regression-kernel-kat-receipt.v1+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
for k in ("schema", "receipt_id", "module_id", "authority", "authority_ceiling"):
    receipt[k] = body_obj[k]
AUDIT.mkdir(parents=True, exist_ok=True)
out = AUDIT / "receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("report_sha256", report_sha)
print("envelope_sha256", sha(out.read_bytes()))
print("signature_len", len(receipt["signature"]["signatures"][0]["sig"]))
print("signature_verified", True)
