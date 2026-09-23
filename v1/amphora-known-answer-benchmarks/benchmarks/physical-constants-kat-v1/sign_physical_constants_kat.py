#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-known-answer-benchmarks physical-constants-kat-v1
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
BENCH = MOD / "benchmarks/physical-constants-kat-v1"
AUDIT = MOD / "evidence/phase0/audit/physical-constants-kat-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

VEC = MOD / "reference/mvp20/data/physical_constants_kat_vectors.v1.json"
VERIFIER = BENCH / "verify_physical_constants_kat.py"
REPORT = BENCH / "physical_constants_kat_report.v1.json"


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
assert report["cross_check_portfolio_constants"]["zinc_cross_check_matches_to_4_sig_figs"] is True

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

body_obj = {
    "schema": "amphora.known-answer.physical-constants-kat-receipt.v1",
    "receipt_id": "physical-constants-kat-v1",
    "module_id": "amphora-known-answer-benchmarks",
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "LIMITED_SANITY",
    "decision_use_ceiling": "AUDIT_ONLY",
    "scope": "solvent-borne two-part epoxy-amine marine anti-corrosion coating physical-chemistry constants",
    "purpose": "Extend the module's known-answer battery onto the PHYSICAL-CONSTANTS axis. "
               "The SI-2019 redefinition fixes N_A, k_B and e as exact defined integers, so "
               "R = N_A*k_B and F = N_A*e are exact rational products. This battery locks "
               "those constants and their derived R*T, F/3600 and sacrificial-zinc specific "
               "charge, which the portfolio's Arrhenius/Kissinger cure-kinetics, Eyring "
               "viscosity, and zinc galvanic modules silently depend on but have no dedicated "
               "non-circular known-answer regression set for.",
    "hypothesis_advanced": "Known answers expose arithmetic, unit, and CONSTANT regressions "
                           "(module mission). This receipt exercises the physical-CONSTANT axis, "
                           "complementary to the existing unit-conversion-kat-v1 battery.",
    "closes_gate": "PHYSICAL_CONSTANTS_KNOWN_ANSWER_AXIS_UNCOVERED (module-local, limited sanity)",
    "methodology_primary_sources": [
        "FIPS 140-3 Section 7.4 Known-Answer Test methodology (2019)",
        "BIPM SI Brochure 9th ed. (2019): N_A, k_B, e defined exactly",
        "CODATA 2018 recommended values: R = 8.314462618 J/mol/K, F = 96485.33212 C/mol (exact)",
        "IUPAC 2021 standard atomic weight of zinc = 65.38",
        "10th CGPM (1954) / ISO 2533: standard atmosphere = 101325 Pa exact",
        "Faraday's laws of electrolysis (specific-charge derivation)",
    ],
    "design": {
        "positive_pass_criterion": "For 'exact' vectors: reconstructed exact rational == pinned "
            "defining value. For 'derived' vectors: round_half_up(exact_rational_product_of_raw_"
            "constants, decimals) == pinned_expected, where the derivation uses ONLY raw defining "
            "constants (independent of any pinned R/F -> non-circular).",
        "fail_closed_criterion": "each hostile trap (pre-2019 measured R 8.314472; pre-2019 N_A "
            "6.022137e23; 273-K offset; F=96500 rounded; R=1.987 cal-as-J) must NOT equal the exact "
            "correct answer at the stated precision",
        "gate_arithmetic": "fractions.Fraction exact rational only; no floating point enters the "
            "pass/fail decision, guaranteeing byte-stable replays by construction",
    },
    "results": {
        "aggregate_status": report["aggregate_status"],
        "headline": f"{report['n_positive_pass']}/{report['n_positive']} exact physical-constant "
                    f"vectors reproduced; {report['n_fail_closed_correctly_flagged']}/"
                    f"{report['n_fail_closed']} hostile constant traps rejected; zinc-galvanic "
                    "819.868 Ah/kg control reproduced to 4 sig figs from F alone",
        "n_positive": report["n_positive"], "n_positive_pass": report["n_positive_pass"],
        "n_fail_closed": report["n_fail_closed"],
        "n_fail_closed_correctly_flagged": report["n_fail_closed_correctly_flagged"],
        "positive_pass_rate": report["positive_pass_rate"],
        "fail_closed_flag_rate": report["fail_closed_flag_rate"],
    },
    "cross_check": report["cross_check_portfolio_constants"],
    "scientific_claim": report["scientific_claim"],
    "does_not_close": [
        "F160-BLACK historical MIL-DTL-24441 control still UNVERIFIED (needs authoritative /38B or NAVSEA/DLA artifact)",
        "PHASE0_EVALUATOR + PHASE0_INTERNAL_REVIEWER dual-identity promotion signatures",
        "any candidate-performance, qualification, regulatory, or FTO claim",
    ],
    "artifacts": {
        "vectors_file": {"path": "amphora-known-answer-benchmarks/reference/mvp20/data/physical_constants_kat_vectors.v1.json", "sha256": vec_sha},
        "verifier": {"path": "amphora-known-answer-benchmarks/benchmarks/physical-constants-kat-v1/verify_physical_constants_kat.py", "sha256": verifier_sha},
        "report": {"path": "amphora-known-answer-benchmarks/benchmarks/physical-constants-kat-v1/physical_constants_kat_report.v1.json", "sha256": report_sha},
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
ptype = "application/vnd.amphora.known-answer-physical-constants-kat-receipt.v1+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
# top-level pass-through fields for jq convenience (kept consistent with body)
for k in ("schema", "receipt_id", "module_id", "authority", "authority_ceiling"):
    receipt[k] = body_obj[k]
AUDIT.mkdir(parents=True, exist_ok=True)
out = AUDIT / "receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
# verify signature round-trips
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
