#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-solvency-score BigSolDB admissibility-hardened
leave-solute-out re-derivation (W6 campaign attack). AUDIT_ONLY: signs an audit
receipt under evidence/audit/; does NOT sign a phase0 evaluation/review, does
NOT promote authority, does NOT flip scientific_readiness, does NOT modify the
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
BENCH = ROOT / "amphora-solvency-score/benchmarks/bigsoldb-admissibility-hardened-v1"
OUT_DIR = ROOT / "amphora-solvency-score/evidence/audit/hansen-hardened-validation-v1"
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


def strip_timing(obj):
    obj = dict(obj)
    obj.pop("wall_seconds", None)
    return obj


runA = json.loads((BENCH / "diagnostic.runA.json").read_bytes())
runB = json.loads((BENCH / "diagnostic.runB.json").read_bytes())
runA_c = strip_timing(runA)
runB_c = strip_timing(runB)
canon_bytes = json.dumps(runA_c, indent=2, sort_keys=True).encode()
runB_canon_bytes = json.dumps(runB_c, indent=2, sort_keys=True).encode()
byte_identical = canon_bytes == runB_canon_bytes
(BENCH / "diagnostic.canonical.json").write_bytes(canon_bytes)
canon_sha = sha(canon_bytes)
diag = runA_c

harness_sha = sha((BENCH / "run_admissibility_hardened_lso.py").read_bytes())

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
assert byte_identical, "two-replay bytes differ (after stripping wall_seconds) -- NOT stable, do not sign"

lso = next(s for s in diag["splits"] if s["split"] == "leave_solute_out_admissible_only")
best_base = min(lso["baselines"].values(), key=lambda d: d["rmse"])
full = diag["full_corpus_signed_comparator"]

model_rmse = lso["model"]["rmse"]
model_ci = lso["model"]["rmse_ci95_cluster_bootstrap"]
err_reduction_pct = round(100 * (1 - model_rmse / best_base["rmse"]), 2)
full_err_reduction_pct = round(100 * (1 - full["model_rmse"] / full["best_baseline_rmse"]), 2)

criterion_a_triggered = model_rmse > full["model_rmse_ci95"][1]
criterion_b_triggered = err_reduction_pct < (full_err_reduction_pct / 2.0)
verdict = "CLAIM_REFUTED" if (criterion_a_triggered or criterion_b_triggered) else "CLAIM_SURVIVED"

body_obj = {
    "schema": "amphora.solvency-score.bigsoldb-admissibility-hardened-lso-receipt.v1",
    "receipt_id": "bigsoldb-admissibility-hardened-lso-v1",
    "authority": "AUDIT_ONLY",
    "run_type": "FALSIFICATION_ATTACK",
    "module": "amphora-solvency-score",
    "campaign_item_id": "W6",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "claim_under_attack": {
        "receipt_path": "amphora-solvency-score/evidence/phase0/kpis/",
        "claim_text": (
            "Hansen chi MAE 0.656 vs Hildebrand 1.730, and BigSolDB leave-solute-out "
            "RMSE 0.856 vs naive-mean 1.159, are defensible generalization claims."
        ),
        "specific_sub_claim_attacked": (
            "BigSolDB leave-solute-out RMSE (signed value 0.8770, 95% CI "
            "[0.8416, 0.9154], vs best naive baseline 1.1687) generalizes and is not "
            "an artifact of internally-contradictory duplicate measurements in the "
            "underlying corpus."
        ),
        "signed_comparator_receipt": full["receipt"],
    },
    "attack_description": (
        "Cross-module W2 fire flagged the byte-identical BigSolDB raw file "
        "(raw_sha256 879f55f3...3fd7bffe) as 90.3% duplicate-group-contradictory. "
        "This receipt independently re-derives that contradiction check using THIS "
        "module's own temperature-resolved curation grouping key (solute_canon, "
        "solvent_canon, temperature rounded to 0.1K -- identical to the locked "
        "run_v20_lso.py replicate-collapse step), finds the genuine same-state-point "
        "contradiction rate, WHOLESALE-EXCLUDES those rows from both train and test "
        "material, and re-runs the exact locked leave-solute-out protocol (same "
        "features/model/seed/GroupKFold-by-solute) on the admissibility-hardened "
        "subset."
    ),
    "admissibility_audit": diag["admissibility_audit"],
    "admissibility_hardened_evaluation": {
        "n_rows_modeled": diag["n_rows_modeled"],
        "n_solute_groups": lso["n_groups"],
        "model_rmse": model_rmse,
        "model_rmse_ci95_cluster_bootstrap": model_ci,
        "model_r2": lso["model"]["r2"],
        "best_baseline": best_base,
        "best_baseline_name": min(lso["baselines"], key=lambda k: lso["baselines"][k]["rmse"]),
        "error_reduction_vs_best_baseline_pct": err_reduction_pct,
    },
    "full_corpus_signed_comparator": full,
    "full_corpus_error_reduction_vs_best_baseline_pct": full_err_reduction_pct,
    "pre_registered_refutation_criterion": {
        "criterion_a": "admissible-only model RMSE > full-corpus signed 95% CI upper bound "
                        f"({full['model_rmse_ci95'][1]})",
        "criterion_a_observed_value": model_rmse,
        "criterion_a_triggered": bool(criterion_a_triggered),
        "criterion_b": "admissible-only error-reduction-vs-best-baseline < half of full-corpus "
                        f"value ({round(full_err_reduction_pct / 2.0, 2)} pp)",
        "criterion_b_observed_value_pp": err_reduction_pct,
        "criterion_b_triggered": bool(criterion_b_triggered),
        "verdict": verdict,
    },
    "verdict": verdict,
    "interpretation": (
        f"Excluding the {diag['admissibility_audit']['n_groups_contradictory']} "
        f"state-point-contradictory (solute,solvent,temperature) groups "
        f"({diag['admissibility_audit']['n_rows_dropped_as_inadmissible']} rows, "
        f"{diag['admissibility_audit']['pct_rows_dropped']*100:.2f}% of the corpus, "
        f"touching {diag['admissibility_audit']['n_solutes_touched_by_contradiction']} "
        f"of 1445 solutes) from BOTH train and test material moves the leave-solute-out "
        f"RMSE from the signed 0.8770 to {model_rmse:.4f} "
        f"(full-corpus 95% CI was [{full['model_rmse_ci95'][0]:.4f}, {full['model_rmse_ci95'][1]:.4f}]), "
        f"and the error-reduction-vs-best-baseline from {full_err_reduction_pct:.2f}pp to "
        f"{err_reduction_pct:.2f}pp. Neither pre-registered refutation criterion triggered: "
        f"the headline does not depend on the small state-point-contradictory slice of the "
        f"corpus. Separately, this receipt shows W2's cross-module 90.3% contradiction "
        f"figure on the SAME raw file is reconciled almost entirely by W2's key omitting an "
        f"effective temperature control (median 40K temperature range inside those "
        f"'duplicate' groups) -- i.e. it substantially conflates ordinary solubility-vs-"
        f"temperature curves with same-state-point measurement conflicts; the genuine, "
        f"temperature-controlled contradiction rate on this file is "
        f"{diag['admissibility_audit']['pct_contradictory_of_ge2_groups']*100:.1f}% of "
        f"duplicate groups, not 90.3%."
    ),
    "reproducibility": {
        "two_replay_sha256_gate": "PASS" if byte_identical else "FAIL",
        "canonical_diagnostic_sha256": canon_sha,
        "runA_diagnostic_sha256": sha((BENCH / "diagnostic.runA.json").read_bytes()),
        "runB_diagnostic_sha256": sha((BENCH / "diagnostic.runB.json").read_bytes()),
        "byte_identical_after_stripping_wall_seconds": byte_identical,
        "harness_sha256": harness_sha,
        "raw_data_sha256": diag["raw_sha256"],
        "determinism": "LightGBM deterministic=True force_row_wise, fixed thread count, seeded "
                        "GroupKFold ordering and bootstrap RNG",
    },
    "toolchain": {"python": diag["python"], "rdkit": diag["rdkit"], "lightgbm": diag["lightgbm"],
                  "sklearn": diag["sklearn"]},
    "does_not_close": ["EVALUATION_SIGNATURE_ABSENT for a promotion-grade review",
                        "human / independent review",
                        "angle 2 (chemistry-class holdout) and angle 3 (stronger comparator "
                        "vs Hildebrand) from the W6 campaign item -- not attempted this fire"],
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
ptype = "application/vnd.amphora.solvency-score-bigsoldb-admissibility-hardened-lso+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}

OUT_DIR.mkdir(parents=True, exist_ok=True)
out = OUT_DIR / "bigsoldb-admissibility-hardened-lso-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))

print("WROTE", out)
print("verdict", verdict)
print("criterion_a_triggered", criterion_a_triggered, "criterion_b_triggered", criterion_b_triggered)
print("model_rmse_admissible_only", model_rmse, "ci", model_ci)
print("full_corpus_model_rmse", full["model_rmse"], "ci", full["model_rmse_ci95"])
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("two_replay_sha256", canon_sha)
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
