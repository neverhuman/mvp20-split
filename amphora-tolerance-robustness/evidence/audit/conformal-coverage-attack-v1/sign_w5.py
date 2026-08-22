#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-tolerance-robustness W5 conformal-coverage-attack
AUDIT_ONLY receipt. AUDIT_ONLY: signs an audit receipt under evidence/audit/; does
NOT sign a phase0 evaluation/review, does NOT promote authority, does NOT flip
scientific_readiness (stays LOCKED_INTERNAL/UNVALIDATED), does NOT modify the
portfolio manifest, any locked dataset, or any signed Phase-0 KPI. Derived key_id
cross-checked vs pinned trust store.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-tolerance-robustness/evidence/audit/conformal-coverage-attack-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

def sha(b): return hashlib.sha256(b).hexdigest()
def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " +
            str(len(body)).encode() + b" " + body)
def load_seed(p):
    raw = p.read_bytes().strip()
    if len(raw) == 64:
        try: return bytes.fromhex(raw.decode())
        except Exception: pass
    return raw[:32]

canon = (BENCH / "diagnostic.canonical.json").read_bytes()
runB = (BENCH / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)
harness_sha = sha((BENCH / "run_conformal_coverage_attack.py").read_bytes())

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw(); eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
rev_pin = (rev_key_id == tbr.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))
assert eval_pin, "evaluator key_id does not derive pinned trust store entry"

body_obj = {
    "schema": "amphora.tolerance-robustness.conformal-coverage-attack-receipt.v1",
    "study_id": diag["study_id"],
    "campaign_item_id": "W5",
    "authority": "AUDIT_ONLY",
    "module": "amphora-tolerance-robustness",
    "promotes_authority": False, "flips_scientific_readiness": False,
    "human_review_performed": False, "organizational_independence_asserted": False,
    "modifies_manifest": False, "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "claim_under_attack": diag["claim_under_attack"],
    "falsification_criteria": diag["falsification_criteria"],
    "part_a_openpoly_tg_scaffold_safe_split": {
        "dataset": diag["part_a_dataset"],
        "fidelity_replicate_random_split": diag["part_a_fidelity_replicate_random_split"],
        "scaffold_safe_split": diag["part_a_scaffold_safe_split"],
    },
    "part_b_radonpy_eps_r_admissible_subset": {
        "admissibility": diag["part_b_admissibility"],
        "conformal": diag["part_b_conformal"],
    },
    "verdict": diag["verdict"],
    "does_not_close": [
        "Does not establish wet-lab qualification, batch release, or human parity.",
        "Part A scaffold-safe split is a single seed=0 draw; robustness across multiple scaffold-safe partitions is untested (Phase-1 next step).",
        "Part A uses the module's in-pipeline Ridge base learner (audit-chain standard), not the frozen Push-20 group-contribution model behind the single headline 0.9683 KPI; see claim_under_attack.note_on_base_learner.",
        "Part B admissible-subset n=52 (test) / 113 (population) is small; Wilson CI width reflects that, not a bug.",
        "Part A random-split fidelity replicate (0.9326) does not byte-match the module's signed jackknife/mondrian reference (0.9378) -- n=443 vs reference n=442 after RDKit-parseable filtering, a 1-row discrepancy of unresolved origin (likely a duplicate-canonicalization step in the original pipeline not reproduced here); both figures are within 0.5pp and the qualitative conclusions are unaffected.",
    ],
    "closes": [
        "Re-derives RadonPy PI1070 static_dielectric_const (eps_r) split-conformal coverage restricted to the physically-admissible subset (Frohlich/Debye eps_static>=n^2), independently reproducing W3's 10.5% admissibility fraction and showing the blind-population coverage figure is propped up by inadmissible rows.",
        "Extends the module's conditional-coverage battery (Mondrian tercile) with a genuinely non-exchangeable scaffold-safe train/calibration-vs-test split, the exact next step flagged as untested by the module's own signed training-conditional-pac-tolerance-openpoly-tg-v1 receipt (does_not_close[5]).",
    ],
    "provenance": {
        "harness_sha256": harness_sha,
        "prior_receipts_referenced": [
            "amphora-tolerance-robustness/evidence/audit/jackknife-plus-cvplus-openpoly-tg-v1",
            "amphora-tolerance-robustness/evidence/audit/mondrian-conformal-openpoly-tg-v1",
            "amphora-tolerance-robustness/evidence/audit/training-conditional-pac-tolerance-openpoly-tg-v1",
            "amphora-molecule-property/evidence/audit/dielectric-retraction-v1 (W3, source of the eps_static>=n^2 admissibility constraint)",
        ],
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "harness_sha256": harness_sha,
        "numpy": "1.26.4", "sklearn": "1.7.2", "rdkit": "2026.03.2", "pandas": "2.1.4",
        "seed": 0,
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under evidence/audit/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin)},
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER", "key_id": rev_key_id, "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin), "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed."},
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.tolerance-robustness-conformal-coverage-attack+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
out = BENCH / "conformal-coverage-attack-receipt.v1.dsse.json"
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
print("signature_len", len(envelope["signatures"][0]["sig"]))
print("signature_verified", True)
print("verdict_overall", diag["verdict"]["overall"])
