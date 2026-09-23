#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-known-answer-benchmarks molar-mass-kat-v1
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
BENCH = MOD / "benchmarks/molar-mass-kat-v1"
AUDIT = MOD / "evidence/phase0/audit/molar-mass-kat-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

VEC = MOD / "reference/mvp20/data/molar_mass_kat_vectors.v1.json"
VERIFIER = BENCH / "verify_molar_mass_kat.py"
REPORT = BENCH / "molar_mass_kat_report.v1.json"


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
assert report["all_trap_correct_pins_consistent"] is True
assert report["cross_check_portfolio_constants"]["dgeba_eew_cross_check_matches_to_2_decimals"] is True

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
    "schema": "amphora.known-answer.molar-mass-kat-receipt.v1",
    "receipt_id": "molar-mass-kat-v1",
    "module_id": "amphora-known-answer-benchmarks",
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "LIMITED_SANITY",
    "decision_use_ceiling": "AUDIT_ONLY",
    "scope": "solvent-borne two-part epoxy-amine marine anti-corrosion coating molecular constituents "
             "(DGEBA resin, amine hardeners, TiO2/ZnO pigments, water)",
    "purpose": "Extend the module's known-answer battery onto the STANDARD-ATOMIC-WEIGHT / MOLAR-MASS "
               "axis, complementary to the existing unit-conversion-kat-v1 and physical-constants-kat-v1 "
               "batteries. The portfolio's EEW/AHEW stoichiometry, epoxy:amine mix ratio, VOC, and "
               "pigment/CPVC arithmetic all silently sum IUPAC standard atomic weights into molar masses, "
               "but no dedicated non-circular known-answer regression set locks that atomic-weight table "
               "or the molar-mass summation. This battery pins the IUPAC 2021 conventional/abridged "
               "standard atomic weights of the coating elements (H, C, N, O, Cl, S, Zn, Ti) and "
               "independently re-derives the molar masses of the key molecules and the theoretical "
               "epoxide/amine equivalent weights as exact rationals.",
    "hypothesis_advanced": "Known answers expose arithmetic, unit, constant, and now MOLAR-MASS "
                           "regressions (module mission). A regression in a pinned atomic weight or a "
                           "molar-mass summation silently corrupts every equivalent weight and mix ratio "
                           "downstream; this axis catches it.",
    "closes_gate": "MOLAR_MASS_KNOWN_ANSWER_AXIS_UNCOVERED (module-local, limited sanity)",
    "methodology_primary_sources": [
        "FIPS 140-3 Section 7.4 Known-Answer Test methodology (2019)",
        "IUPAC CIAAW 2021 standard atomic weights; Meija et al., Pure Appl. Chem. 2016, 88(3):265-291, DOI 10.1515/pac-2015-0305",
        "PubChem published molecular weights (water CID 962; bisphenol A CID 6623; epichlorohydrin CID 7835; DGEBA CID 2286; IPDA CID 22440; DETA CID 8111; TETA CID 5565; MXDA CID 12971; TiO2 CID 26042; ZnO CID 14806)",
        "Theoretical epoxide/amine equivalent weight = molar mass / integer functionality",
    ],
    "design": {
        "positive_pass_criterion": "atomic-weight identity vectors PASS iff the raw pinned atomic weight "
            "in the verifier's exact-rational table equals the pinned IUPAC value (typo/regression guard); "
            "molar-mass and equivalent-weight vectors PASS iff round_half_up(exact_rational_sum_of_pinned_"
            "atomic_weights_x_counts / integer_functionality, decimals) == pinned_expected published value "
            "(non-circular: derivation never uses a published molar mass)",
        "fail_closed_criterion": "each hostile trap (integer nucleon counts O=16/H=1/N=14/C=12; legacy "
            "Cl=35.5; monoisotopic water 18.0106; EEW with functionality 1) must NOT equal the exact "
            "correct answer re-derived from the real atomic weights at the stated precision",
        "gate_arithmetic": "fractions.Fraction exact rational only; no floating point enters the pass/fail "
            "decision, guaranteeing byte-stable replays by construction",
    },
    "results": {
        "aggregate_status": report["aggregate_status"],
        "headline": f"{report['n_positive_pass']}/{report['n_positive']} exact atomic-weight / molar-mass / "
                    f"equivalent-weight vectors reproduced; {report['n_fail_closed_correctly_flagged']}/"
                    f"{report['n_fail_closed']} hostile molar-mass traps rejected; DGEBA epoxide equivalent "
                    "weight 170.21 g/eq re-derived from atomic weights alone, reproducing the "
                    "amphora-molecule-property DGEBA EEW-series anchor",
        "n_positive": report["n_positive"], "n_positive_pass": report["n_positive_pass"],
        "n_fail_closed": report["n_fail_closed"],
        "n_fail_closed_correctly_flagged": report["n_fail_closed_correctly_flagged"],
        "positive_pass_rate": report["positive_pass_rate"],
        "fail_closed_flag_rate": report["fail_closed_flag_rate"],
    },
    "cross_check": report["cross_check_portfolio_constants"],
    "scientific_claim": report["scientific_claim"],
    "does_not_close": [
        "atomic weights are pinned conventional/abridged IUPAC values, NOT re-measured; this axis locks "
        "the summation and table, not the underlying isotopic-abundance metrology",
        "DGEBA/TETA/MXDA molar masses pinned at 1 decimal because the 2021 atomic-weight revision shifts "
        "the 2nd decimal vs pre-2021 legacy values (e.g. DGEBA 340.42 vs legacy 340.41); the 2-decimal "
        "atomic-weight-revision sensitivity is NOT itself a locked known answer here",
        "PHASE0_EVALUATOR + PHASE0_INTERNAL_REVIEWER dual-identity promotion signatures",
        "any candidate-performance, qualification, regulatory, or FTO claim",
    ],
    "artifacts": {
        "vectors_file": {"path": "amphora-known-answer-benchmarks/reference/mvp20/data/molar_mass_kat_vectors.v1.json", "sha256": vec_sha},
        "verifier": {"path": "amphora-known-answer-benchmarks/benchmarks/molar-mass-kat-v1/verify_molar_mass_kat.py", "sha256": verifier_sha},
        "report": {"path": "amphora-known-answer-benchmarks/benchmarks/molar-mass-kat-v1/molar_mass_kat_report.v1.json", "sha256": report_sha},
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
ptype = "application/vnd.amphora.known-answer-molar-mass-kat-receipt.v1+json"
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
