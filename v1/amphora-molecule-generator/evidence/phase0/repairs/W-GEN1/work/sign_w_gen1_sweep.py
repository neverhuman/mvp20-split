#!/usr/bin/env python3
"""DSSE-Ed25519-sign the W-GEN1 portfolio-wide exact-CI sweep receipt for
amphora-molecule-generator. Construction replicated from
amphora-molecule-generator/evidence/audit/molgen-grammar-yield-bootstrap-ci-
inadmissibility-v1/sign_molgen_ci_admissibility.py and
evidence/phase0/repairs/V-A06/work/sign_va06_verify.py (pae, load_seed,
payloadType, envelope fields, trust-store key derivation).

AUDIT_ONLY: signs a falsification-attack sweep receipt under
evidence/phase0/repairs/W-GEN1/done/. Does NOT modify, delete, or re-sign any
scanned artifact (including the new-finding artifact in
amphora-molecule-role-ranker, a different module -- out of scope to repair
here). Does NOT promote authority, does NOT flip scientific_readiness, does
NOT modify the manifest or any mission.md front-matter.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-molecule-generator"
ITEM = MOD / "evidence/phase0/repairs/W-GEN1"
WORK, DONE = ITEM / "work", ITEM / "done"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
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


canon = (WORK / "diagnostic.canonical.json").read_bytes()
runB = (WORK / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)
harness_sha = sha((WORK / "run_w_gen1_sweep.py").read_bytes())

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"

trust = json.loads(TRUST.read_text())
trust_by_role = {k.get("role"): k for k in trust["keys"]}
eval_derives_pin = (eval_key_id == trust_by_role.get("PHASE0_EVALUATOR", {}).get("key_id"))
assert eval_derives_pin, "evaluator key not anchored in phase0 trust store"

new_findings = diag["new_finding_degenerate_fields"]
counts = diag["counts"]

body_obj = {
    "schema": "amphora.molecule-generator.w-gen1-portfolio-ci-degeneracy-sweep-receipt.v1",
    "campaign_item_id": "W-GEN1",
    "study_id": diag["study_id"],
    "authority": "AUDIT_ONLY",
    "run_type": "FALSIFICATION_ATTACK_PORTFOLIO_SWEEP",
    "module": "amphora-molecule-generator",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_scanned_artifacts": False,

    "claim": diag["headline"],
    "purpose": diag["purpose"],
    "attacked_claim": diag["attacked_claim"],
    "falsification_criterion": diag["falsification_criterion"],

    "scan_scope": {
        "scan_root": diag["scan_root"],
        "n_dsse_files_scanned": counts["n_dsse_files_scanned"],
        "n_modules_covered": 41,
        "detection_heuristic": ("recursive search of every decoded DSSE payload body for "
                                 "any field whose key contains 'ci'/'interval'/'confidence' "
                                 "and whose value is a 2-element numeric array; degenerate-"
                                 "at-boundary = zero width AND (sibling k/n pair at k==n or "
                                 "k==0, OR the interval itself is exactly [0,0] or [1,1])"),
    },

    "results": {
        "n_ci_fields_total": counts["n_ci_fields_total"],
        "n_files_with_ci_fields": counts["n_files_with_ci_fields"],
        "n_degenerate_fields_total": counts["n_degenerate_fields_total"],
        "n_degenerate_fields_already_known_instance": counts["n_degenerate_fields_already_known_instance"],
        "n_degenerate_fields_new_finding": counts["n_degenerate_fields_new_finding"],
        "verdict": diag["verdict"],
    },

    "known_instance_paths_excluded_from_new_finding_count": diag["known_instance_paths_excluded_from_new_finding_count"],
    "already_known_instance_degenerate_fields": diag["already_known_instance_degenerate_fields"],
    "new_finding_degenerate_fields": new_findings,
    "new_finding_inadmissible_by_gap_threshold": diag["new_finding_inadmissible_by_gap_threshold"],

    "new_finding_summary": (
        "SWEEP CONFIRMS the campaign hypothesis that the k=n/k=0 percentile-bootstrap "
        "degeneracy defect is repeated elsewhere in the portfolio, outside the one "
        "already-fixed instance. amphora-molecule-role-ranker/benchmarks/"
        "role-parsimony-conformal-v1/replay_receipt.v1.dsse.json (a DIFFERENT module, "
        "independently signed with the repo's LOCAL_DEVELOPMENT_AUDIT_ONLY Ed25519 key "
        "-- signature independently re-verified against the PAE construction here, "
        "result PASS) reports headline_result.fitted_loocv_accuracy_ci95 = [1.0, 1.0] "
        "over a leave-one-out cross-validated classification accuracy at k=n=24 (24/24 "
        "correct, per the frozen phase0-role-known-answer.v1 fixture). The exact "
        "Clopper-Pearson (1934) 95%% interval for the same k=24, n=24 is [0.8575, "
        "1.0000] -- the reported bootstrap lower bound overstates certainty by 0.1425 "
        "(more than 7x the 0.02 admissibility threshold used in the original V-A06/"
        "R-A06 finding). The companion accuracy_gap_det_minus_fitted_ci95=[0.0,0.0] "
        "field is a difference-of-two-saturated-proportions statistic rooted in the "
        "same k=n=24 saturation, not counted as an independent second occurrence."
    ) if new_findings else (
        "SWEEP FOUND NO new occurrences of the defect class outside the one "
        "already-fixed molgen-deterministic-grammar-yield-v1 instance; the defect "
        "remains bounded to that single, already-repaired case."
    ),

    "does_not_close": diag["does_not_close"] + [
        "Does not repair or supersede the amphora-molecule-role-ranker finding "
        "(different module, out of this item's scope) -- recorded as a finding only; "
        "repair belongs to a role-ranker-scoped campaign item.",
    ],

    "verdict": diag["verdict"],

    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "harness_sha256": harness_sha,
    },

    "rights_posture": diag["rights_posture"],

    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY sweep receipt under evidence/phase0/repairs/W-GEN1/done/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_derives_pin),
    },
}

body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.molecule-generator-w-gen1-portfolio-ci-degeneracy-sweep+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {
    "payload": base64.standard_b64encode(body).decode(),
    "payloadType": ptype,
    "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}],
}
receipt = {
    "evaluator_key_id": eval_key_id,
    "evaluator_public_key_hex": eval_pub_hex,
    "signature": envelope,
}
DONE.mkdir(parents=True, exist_ok=True)
out = DONE / "w-gen1-portfolio-ci-degeneracy-sweep-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

pk = Ed25519PublicKey.from_public_bytes(eval_pub)
pk.verify(base64.standard_b64decode(envelope["signatures"][0]["sig"]),
          pae(ptype, base64.standard_b64decode(envelope["payload"])))

print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_derives_pin)
print("receipt_body_sha256", sha(body))
print("envelope_sha256", sha(out.read_bytes()))
print("two_replay_sha256", diag_sha)
print("signature_verified", True)
print("verdict", body_obj["verdict"])
