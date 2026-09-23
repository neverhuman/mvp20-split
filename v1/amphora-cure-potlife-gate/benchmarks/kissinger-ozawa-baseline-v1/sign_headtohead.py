#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-cure-potlife-gate Kissinger/OFW/Starink-baseline
head-to-head AUDIT_ONLY receipt. AUDIT_ONLY: signs an audit receipt under
benchmarks/; does NOT sign a phase0 evaluation/review, does NOT promote
authority, does NOT flip scientific_readiness (stays UNVALIDATED/PRE_PHASE_0),
does NOT modify the portfolio manifest (66 receipts / 11 modules), the locked
known-answer dataset, the signed Arrhenius Phase-0 KPI, or any prior signed
receipt. Derived key_id cross-checked vs the pinned trust store, same pattern
as evidence/audit/potlife-gel-tfs-crossendpoint-v1/sign_crossendpoint.py."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-cure-potlife-gate"
BENCH = MOD / "benchmarks/kissinger-ozawa-baseline-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"
KPI = MOD / "evidence/phase0/kpis/cure-potlife-arrhenius-kpi.v1.json"
FIXTURE = MOD / "reference/phase0-cure-potlife-known-answer.v1.json"


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


canon = (BENCH / "diagnostic.canonical.json").read_bytes()
runB = (BENCH / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)
harness_sha = sha((BENCH / "kissinger_ozawa_headtohead_audit.py").read_bytes())
dataset_sha = sha((BENCH / "dataset.multi.ccby.json").read_bytes())

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
rev_pin = (rev_key_id == tbr.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))

body_obj = {
    "schema": "amphora.cure-potlife-gate.kissinger-ozawa-baseline-headtohead-receipt.v1",
    "module": "amphora-cure-potlife-gate",
    "authority": "AUDIT_ONLY",
    "axis": "BASELINE_UPGRADE",
    "campaign_item_id": "C5",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_prior_signed_receipt": False,
    "claim_under_attack": diag["claim_under_attack"],
    "falsification_criterion": diag["falsification_criterion"],
    "ported_estimator": diag["ported_estimator"],
    "ccby_dataset": diag["ccby_dataset"],
    "provenance_check": diag["provenance_check"],
    "chemistry_match": diag["chemistry_match"],
    "head_to_head_pot_life_prediction": diag["head_to_head_pot_life_prediction"],
    "reaction_ea_vs_pot_life_ea_gap": diag["reaction_ea_vs_pot_life_ea_gap"],
    "honest_caveat_check": diag["honest_caveat_check"],
    "coverage_gap": diag["coverage_gap"],
    "result_summary": diag["result_summary"],
    "verdict": diag["verdict"],
    "does_not_close": diag["does_not_close"],
    "provenance": {
        "signed_arrhenius_kpi_sha256": sha(KPI.read_bytes()),
        "known_answer_fixture_sha256": sha(FIXTURE.read_bytes()),
        "ccby_dataset_sha256": dataset_sha,
        "harness_sha256": harness_sha,
        "ported_from_module": "amphora-redteam-audit",
        "ported_from_benchmarks": [
            "cure-kinetics-kissinger-ccby-anchor-v1",
            "cure-kinetics-kissinger-multisystem-ccby-v1",
            "cure-kinetics-isoconversional-crossmethod-ccby-v1",
        ],
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "harness_sha256": harness_sha,
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under benchmarks/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin)},
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER", "key_id": rev_key_id,
        "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin),
        "reviewer_signature_present": False,
        "note": ("Reviewer key referenced for provenance only; no independent human "
                 "review performed.")},
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.cure-potlife-gate-kissinger-ozawa-baseline-headtohead-receipt.v1+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id,
                            "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
out = BENCH / "kissinger-ozawa-baseline-headtohead-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("two_replay_sha256", diag_sha)
print("envelope_sha256", sha(out.read_bytes()))
print("signature_len", len(receipt["signature"]["signatures"][0]["sig"]))
print("signature_verified", True)
