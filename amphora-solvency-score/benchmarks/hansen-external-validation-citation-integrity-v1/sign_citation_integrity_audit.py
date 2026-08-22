#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-solvency-score Hansen external-validation
citation-integrity audit (ROTATION falsification attack, fire
20260818T160001-1176865-201f03226513). AUDIT_ONLY: signs an audit receipt
under evidence/audit/; does NOT sign a phase0 evaluation/review, does NOT
promote authority, does NOT flip scientific_readiness, does NOT modify the
portfolio manifest, any locked dataset, or the signed Phase-0 KPI files under
evidence/phase0/kpis/. Uses the pinned PHASE0_EVALUATOR key, cross-checked
against config/phase0-trust-store.v1.json.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-solvency-score/benchmarks/hansen-external-validation-citation-integrity-v1"
OUT_DIR = ROOT / "amphora-solvency-score/evidence/audit/hansen-external-validation-citation-integrity-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" "
            + str(len(body)).encode() + b" " + body)


def load_seed(p):
    raw = p.read_bytes().strip()
    if len(raw) == 64:
        try:
            return bytes.fromhex(raw.decode())
        except Exception:
            pass
    return raw[:32]


runA = json.loads((BENCH / "diagnostic.runA.json").read_bytes())
runB = json.loads((BENCH / "diagnostic.runB.json").read_bytes())
canon_bytes = json.dumps(runA, indent=2, sort_keys=True).encode()
runB_canon_bytes = json.dumps(runB, indent=2, sort_keys=True).encode()
byte_identical = canon_bytes == runB_canon_bytes
canon_sha = sha(canon_bytes)
diag = runA

harness_sha = sha((BENCH / "run_citation_integrity_audit.py").read_bytes())

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
assert eval_pin, "evaluator key_id does not match pinned trust store"
assert byte_identical, "two-replay bytes differ -- NOT stable, do not sign"

verdict = diag["pre_registered_refutation_criteria"]["verdict"]

kpi_path = ROOT / diag["claim_under_attack"]["kpi_path"]
ref_receipt_path = ROOT / diag["claim_under_attack"]["reference_receipt_path"]

body_obj = {
    "schema": "amphora.solvency-score.hansen-external-validation-citation-integrity-audit-receipt.v1",
    "receipt_id": "hansen-external-validation-citation-integrity-audit-v1",
    "authority": "AUDIT_ONLY",
    "run_type": "FALSIFICATION_ATTACK",
    "module": "amphora-solvency-score",
    "campaign_item_id": "",
    "fire_id": "20260818T160001-1176865-201f03226513",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "claim_under_attack": diag["claim_under_attack"],
    "attack_description": (
        "ROTATION-mode falsification attack on the strongest unattacked standing claim in "
        "amphora-solvency-score: the KPI "
        "'hansen-chi-external-validation-8-published-polymer-solvent-pairs-kpi.v1.json', the "
        "module's only external validation of the Hansen 3-component chi baseline against real "
        "experimental (non-COSMO-RS/OMG-synthetic) chi values. Data-integrity audit of the "
        "underlying 8 rows plus independent re-derivation of statistical significance: (1) "
        "recomputed Pearson r / Spearman r / MAE / fraction-within-factor-of-3 directly from the "
        "KPI's own embedded per_pair_results and cross-checked byte-for-byte against the KPI's "
        "self-reported aggregate block; (2) audited each row's `citation` field for genuine "
        "primary-literature provenance (publication year present, not self-disclosed as an "
        "'estimate'); (3) recomputed Pearson significance (two-tailed t-test, n-2 dof) with any "
        "non-literature-sourced rows excluded, and ran a full leave-one-out sweep to confirm the "
        "significance loss is specific to the flagged row and not a generic small-n artifact."
    ),
    "rederivation_cross_check": diag["rederivation_cross_check"],
    "row_audit": diag["row_audit"],
    "capability_claims_8_published_primary_literature_values": diag["capability_claims_8_published_primary_literature_values"],
    "actual_n_literature_sourced_rows": diag["actual_n_literature_sourced_rows"],
    "sensitivity": diag["sensitivity"],
    "leave_one_out": diag["leave_one_out"],
    "pre_registered_refutation_criteria": diag["pre_registered_refutation_criteria"],
    "verdict": verdict,
    "interpretation": diag["interpretation"],
    "reproducibility": {
        "two_replay_sha256_gate": "PASS" if byte_identical else "FAIL",
        "canonical_diagnostic_sha256": canon_sha,
        "runA_diagnostic_sha256": sha((BENCH / "diagnostic.runA.json").read_bytes()),
        "runB_diagnostic_sha256": sha((BENCH / "diagnostic.runB.json").read_bytes()),
        "byte_identical": byte_identical,
        "harness_sha256": harness_sha,
        "determinism": "pure arithmetic re-derivation + regex citation audit over fixed embedded "
                        "KPI row data; no RNG, no model fitting performed by this audit itself",
        "kpi_sha256": sha(kpi_path.read_bytes()),
        "reference_receipt_sha256": sha(ref_receipt_path.read_bytes()),
    },
    "toolchain": {"python": "3", "libraries": ["numpy", "scipy.stats"]},
    "does_not_close": diag["does_not_close"],
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under evidence/audit/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin),
    },
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER", "key_id": rev_key_id, "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin), "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed.",
    },
}

body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.solvency-score-hansen-external-validation-citation-integrity-audit+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}

OUT_DIR.mkdir(parents=True, exist_ok=True)
out = OUT_DIR / "hansen-external-validation-citation-integrity-audit-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))

print("WROTE", out)
print("verdict", verdict)
print("criterion_a_triggered", diag["pre_registered_refutation_criteria"]["criterion_a_triggered"])
print("criterion_b_triggered", diag["pre_registered_refutation_criteria"]["criterion_b_triggered"])
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("two_replay_sha256", canon_sha)
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
