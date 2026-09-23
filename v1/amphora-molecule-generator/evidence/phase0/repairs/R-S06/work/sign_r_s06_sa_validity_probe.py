#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-molecule-generator R-S06 adversarial probe
of the SA<6 validity/feasibility gate components.

AUDIT_ONLY. Produces a signed audit receipt under
evidence/phase0/repairs/R-S06/done/; does NOT sign a phase0
evaluation/review, does NOT promote authority, does NOT flip
scientific_readiness (stays UNVALIDATED), does NOT modify the manifest,
the locked PI1M dataset, or any prior signed Phase-0 KPI/receipt (the
target receipt is left untouched -- this is a NEW, separate audit
artifact that refutes it, per supersede-never-rewrite discipline).
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
ITEM = ROOT / "amphora-molecule-generator/evidence/phase0/repairs/R-S06"
WORK = ITEM / "work"
DONE = ITEM / "done"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" "
            + str(len(body)).encode() + b" " + body)


def load_seed(path):
    raw = path.read_bytes().strip()
    if len(raw) == 64:
        try:
            return bytes.fromhex(raw.decode())
        except Exception:
            pass
    return raw[:32]


# --- two-replay gate --------------------------------------------------------
canon = (WORK / "diagnostic.canonical.json").read_bytes()
runB = (WORK / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)
harness_sha = sha((WORK / "run_sa_validity_adversarial_probe.py").read_bytes())

# --- derive keys ------------------------------------------------------------
eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"

trust = json.loads(TRUST.read_text())
trust_by_role = {k.get("role"): k for k in trust["keys"]}
eval_derives_pin = (eval_key_id == trust_by_role.get("PHASE0_EVALUATOR", {}).get("key_id"))
rev_derives_pin = (rev_key_id == trust_by_role.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))

f1 = diag["family_1_known_hard_structures"]
f2 = diag["family_2_degenerate_valid_smiles"]
f3 = diag["family_3_boundary_probing"]

body_obj = {
    "schema": "amphora.molecule-generator.r-s06-sa-validity-adversarial-probe-receipt.v1",
    "study_id": diag["study_id"],
    "authority": "AUDIT_ONLY",
    "run_type": "ADVERSARIAL_FALSIFICATION_ATTACK",
    "module": "amphora-molecule-generator",
    "campaign_item_id": "R-S06",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "supersedes": None,
    "target_claim": diag["target_claim"],
    "verdict": diag["verdict"],
    "headline": diag["headline"],
    "rdkit_version": diag["rdkit_version"],
    "hash_and_count_lock": diag["hash_and_count_lock"],
    "family_1_known_hard_to_synthesize_structures": {
        "attack": f1["attack"],
        "n_attempted": f1["n_attempted"],
        "n_slipped_through_false_feasible": f1["n_slipped_through"],
        "structures_that_slipped": f1["structures_that_slipped"],
        "refutation_criterion": f1["refutation_criterion"],
        "criterion_met": f1["criterion_met"],
        "results": f1["results"],
    },
    "family_2_degenerate_but_valid_smiles": {
        "attack": f2["attack"],
        "n_attempted": f2["n_attempted"],
        "n_slipped_through_false_valid": f2["n_slipped_through"],
        "structures_that_slipped": f2["structures_that_slipped"],
        "refutation_criterion": f2["refutation_criterion"],
        "criterion_met": f2["criterion_met"],
        "results": f2["results"],
        "positive_control_legitimate_molecule": f2["positive_control_legitimate_molecule"],
    },
    "family_3_boundary_probing_sa_5_9_to_6_1": {
        "attack": f3["attack"],
        "pi1m_prefix_rows_scanned": f3["pi1m_prefix_rows_scanned"],
        "n_rows_in_boundary_band": f3["n_rows_in_boundary_band_5_9_to_6_1"],
        "n_boundary_rows_divergent_beyond_ka_tolerance": f3["n_boundary_rows_divergent_beyond_ka_tolerance"],
        "n_boundary_rows_flipped_now_shipped_vs_mine": f3["n_boundary_rows_flipped_now_shipped_vs_mine"],
        "flipped_structures_named": [
            r for r in f3["flagged_rows"] if r["flipped_now_between_shipped_and_mine"]
        ],
        "representation_invariance_subprobe": {
            "n_checked": f3["representation_invariance_subprobe"]["n_boundary_band_structures_checked"],
            "n_divergent_across_representation": f3["representation_invariance_subprobe"]["n_divergent_across_representation"],
            "divergent_structures_named": [
                r for r in f3["representation_invariance_subprobe"]["rows"]
                if r["divergent_across_representation"]
            ],
        },
        "at_risk_metric_caveat": (
            "n_boundary_rows_at_risk_under_documented_max_residual_0_66 "
            f"({f3['n_boundary_rows_at_risk_under_documented_max_residual_0_66']}) "
            "is TAUTOLOGICAL given the 5.9-6.1 boundary-band definition (any "
            "row within +/-0.1 of 6.0 is trivially within +/-0.66 of 6.0); it "
            "is reported for completeness but is NOT independent evidence. "
            "The load-bearing Family 3 findings are the "
            "n_boundary_rows_flipped_now_shipped_vs_mine count (already-"
            "observed feasible/infeasible disagreement between the target "
            "receipt's shipped ground truth and this run's recomputation) "
            "and the representation-invariance sub-probe (same molecule, "
            "different SMILES serialization, different SA score, crossing "
            "the 6.0 cut)."
        ),
        "refutation_criterion": f3["refutation_criterion"],
        "criterion_met": f3["criterion_met"],
    },
    "any_family_broke_claim": diag["any_family_broke_claim"],
    "theory_reference": diag["theory_reference"],
    "rights_posture": diag["rights_posture"],
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "harness_sha256": harness_sha,
        "harness_command": "python3 run_sa_validity_adversarial_probe.py <out.json>",
    },
    "does_not_close": diag["does_not_close"],
    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under evidence/phase0/repairs/R-S06/done/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_derives_pin),
    },
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER",
        "key_id": rev_key_id,
        "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_derives_pin),
        "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed.",
    },
}

body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.molecule-generator-r-s06-sa-validity-adversarial-probe+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {
    "payload": base64.standard_b64encode(body).decode(),
    "payloadType": ptype,
    "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}],
}
receipt = {
    "evaluator_key_id": eval_key_id,
    "evaluator_public_key_hex": eval_pub_hex,
    "reviewer_public_key_hex": rev_pub_hex,
    "signature": envelope,
}

DONE.mkdir(parents=True, exist_ok=True)
out = DONE / "r-s06-sa-validity-adversarial-probe-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

# self-verify
pk = Ed25519PublicKey.from_public_bytes(eval_pub)
pk.verify(base64.standard_b64decode(envelope["signatures"][0]["sig"]),
          pae(ptype, base64.standard_b64decode(envelope["payload"])))

print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_derives_pin)
print("reviewer_derives_pinned_trust_key", rev_derives_pin)
print("receipt_body_sha256", sha(body))
print("envelope_sha256", sha(out.read_bytes()))
print("two_replay_sha256", diag_sha)
print("signature_verified", True)
print("verdict", body_obj["verdict"])
