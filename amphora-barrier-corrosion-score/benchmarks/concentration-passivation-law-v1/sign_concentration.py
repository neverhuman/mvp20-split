#!/usr/bin/env python3
"""DSSE-Ed25519-sign the concentration-passivation-law-v1 AUDIT_ONLY receipt
for amphora-barrier-corrosion-score. AUDIT_ONLY: signs an audit receipt under
the module's benchmarks/ dir; does NOT sign a phase0 evaluation/review, does
NOT promote authority, does NOT flip scientific_readiness (stays UNVALIDATED /
PRE_PHASE_0), does NOT modify the portfolio manifest (66 receipts / 11
modules), any locked dataset, or any signed Phase-0 KPI. Derived key_id
cross-checked vs the pinned trust store."""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = (ROOT / "amphora-barrier-corrosion-score/benchmarks/"
                "concentration-passivation-law-v1")
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"


def sha(b):
    return hashlib.sha256(b).hexdigest()


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


canon = (BENCH / "result.canonical.json").read_bytes()
runA = (BENCH / "result.runA.json").read_bytes()
runB = (BENCH / "result.runB.json").read_bytes()
assert canon == runA == runB, "two-replay bytes differ"
canon_sha = sha(canon)
res = json.loads(canon)
harness_sha = sha((BENCH / "concentration_passivation_law.py").read_bytes())

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"
eval_pin = rev_pin = False
if TRUST.exists():
    trust = json.loads(TRUST.read_text())
    tbr = {k.get("role"): k for k in trust.get("keys", [])}
    eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
    rev_pin = (rev_key_id == tbr.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))

body_obj = {
    "schema": ("amphora.barrier-corrosion-score."
               "concentration-passivation-law-receipt.v1"),
    "module": "amphora-barrier-corrosion-score",
    "benchmark": "concentration-passivation-law-v1",
    "authority": "AUDIT_ONLY",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "purpose": (
        "First test of the CONCENTRATION axis of the rights-clean NIST "
        "CORR-DATA for amphora-barrier-corrosion-score. The naive severity "
        "assumption a barrier-corrosion score would inherit -- corrosion rate "
        "monotone non-decreasing in chemical concentration -- is tested "
        "against the named published passivation counter-theory (Schoenbein/"
        "Faraday 1836 passivity; Fontana 1986 stainless/H2SO4 isocorrosion "
        "charts) with per-series shuffle-calibrated shape statistics, "
        "family-wise (Bonferroni) decisiveness, and an honest marginal global "
        "enrichment report. Complements arrhenius-temperature-law-v1 "
        "(temperature axis) and the concentration-blind ML rate receipts."),
    "methods": res["methods"],
    "dataset": res["dataset"],
    "cohort": res["cohort"],
    "target_interpretation": res["target_interpretation"],
    "results_summary": {
        "C1_monotone_severity_null": res["C1_monotone_severity_null"],
        "C2_shape_classification": res["C2_shape_classification"],
        "C3_named_system_checks": res["C3_named_system_checks"],
        "C4_hostile_null_shuffled_concentrations":
            res["C4_hostile_null_shuffled_concentrations"],
        "C5_concentration_blind_ml_consequence":
            res["C5_concentration_blind_ml_consequence"],
    },
    "fail_closed_checks": res["fail_closed_checks"],
    "all_fail_closed_checks_pass": res["all_fail_closed_checks_pass"],
    "verdict": res["verdict"],
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_result_sha256": canon_sha,
        "runA_result_sha256": sha(runA),
        "runB_result_sha256": sha(runB),
        "byte_identical": canon == runA == runB,
        "harness_sha256": harness_sha,
        "determinism": res["determinism"],
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": ("AUDIT_ONLY audit receipt under "
                     "amphora-barrier-corrosion-score/benchmarks/"),
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin)},
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER", "key_id": rev_key_id,
        "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin),
        "reviewer_signature_present": False,
        "note": ("Reviewer key referenced for provenance only; no independent "
                 "human review performed.")},
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = ("application/vnd.amphora.barrier-corrosion-"
         "concentration-passivation-law+json")
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(),
            "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id,
                            "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id,
           "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex,
           "signature": envelope}
out = BENCH / "concentration-passivation-law-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("two_replay_canonical_sha256", canon_sha)
print("harness_sha256", harness_sha)
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
