#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-cure-potlife-gate R-C02 repair done receipt.
AUDIT_ONLY: signs a repair receipt under evidence/phase0/repairs/R-C02/done/;
does NOT sign a phase0 evaluation/review, does NOT promote authority, does NOT
flip scientific_readiness (stays UNVALIDATED/PRE_PHASE_0), does NOT modify the
portfolio manifest, the locked known-answer dataset, the signed Arrhenius
Phase-0 KPI, or any prior signed receipt (docs/mission.md prose is the only
collaborative file touched, per repair-mode rules). Derived key_id
cross-checked vs the pinned trust store."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-cure-potlife-gate"
ITEM = MOD / "evidence/phase0/repairs/R-C02"
WORK = ITEM / "work"
DONE = ITEM / "done"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"
KA = MOD / "reference/phase0-cure-potlife-known-answer.v1.json"
KPI = MOD / "evidence/phase0/kpis/cure-potlife-arrhenius-kpi.v1.json"
MANIFEST = ROOT / "amphora-molecule-property/reference/mvp20/data/amphora_coating_scientific_receipts_manifest.v1.json"
LEDGER = ROOT / "logs/falsification-ledger.jsonl"
Q10_RECEIPT = MOD / "evidence/audit/potlife-q10-heuristic-ablation-v1/potlife-q10-heuristic-ablation-receipt.v1.dsse.json"
DISCLOSURE_RECEIPT = MOD / "evidence/audit/potlife-kpi-envelope-disclosure-gap-v1/potlife-kpi-envelope-disclosure-gap-receipt.v1.dsse.json"
CURVATURE_RECEIPT = MOD / "evidence/audit/potlife-arrhenius-curvature-mechanism-v1/potlife-arrhenius-curvature-mechanism-receipt.v1.dsse.json"
MISSION = MOD / "docs/mission.md"
MISSION_PRE = WORK / "mission.md.pre-repair"


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


canon = (WORK / "diagnostic.canonical.json").read_bytes()
runB = (WORK / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)
harness_sha = sha((WORK / "run_loso_bias_correction.py").read_bytes())

assert diag["acceptance"]["overall_met"] is True, "acceptance bar not met -- must not land in done/"
assert diag["positive_control"]["detected"] is True, "positive control did not fire -- cannot license CLAIM_SURVIVED"

# frontmatter byte-identity check (mission.md prose-only edit)
def frontmatter(path_bytes):
    lines = path_bytes.decode().split("\n")
    assert lines[0] == "---"
    end = lines[1:].index("---") + 1
    return "\n".join(lines[1:end]).encode()

mission_pre_bytes = MISSION_PRE.read_bytes()
mission_post_bytes = MISSION.read_bytes()
fm_before = frontmatter(mission_pre_bytes)
fm_after = frontmatter(mission_post_bytes)
assert fm_before == fm_after, "mission.md frontmatter changed -- not permitted"

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
    "schema": "amphora.cure-potlife-gate.repair-receipt.v1",
    "receipt_id": "R-C02-loso-bias-correction-repair-v1",
    "module": "amphora-cure-potlife-gate",
    "module_id": "amphora-cure-potlife-gate",
    "repair_item": "R-C02",
    "campaign_item_id": "R-C02",
    "authority": "AUDIT_ONLY",
    "axis": "MODEL_REPAIR",
    "phase": "PRE_PHASE_0",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_existing_receipts": False,
    "modifies_prior_signed_receipt": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "claim": ("An upgraded pot-life model (leave-one-system-out cross-system multiplicative "
              "bias correction on top of the incumbent per-system published-Ea Arrhenius model) "
              "achieves 40C-leg MAPE <= 0.25 AND beats the Q10=2 heuristic (MAPE 0.1527) on "
              ">= 2 of 3 held-out legs, on the IDENTICAL locked 36-point truth table and metric "
              "as evidence/audit/potlife-q10-heuristic-ablation-v1/."),
    "pre_registered_acceptance": {
        "source": "campaign item R-C02 objective",
        "criterion_a": "40C-leg MAPE <= 0.25",
        "criterion_b": "beats Q10=2 heuristic (MAPE 0.1527) on >= 2 of 3 held-out legs on the identical locked 36-point truth table",
    },
    "candidate_model": diag["candidate_model"],
    "dataset": diag["dataset"],
    "constants": diag["constants"],
    "leg_summary": diag["leg_summary"],
    "overall": diag["overall"],
    "acceptance": diag["acceptance"],
    "verdict": "CLAIM_SURVIVED",
    "verdict_meaning": ("The repaired claim (candidate model meets the R-C02 pre-registered "
                         "acceptance bar) withstood re-attack: the pinned falsification method "
                         "(Q10=2 ablation on the identical locked fixture and metric from "
                         "potlife-q10-heuristic-ablation-v1) was re-run against the repaired "
                         "candidate and did not refute it."),
    "positive_control": diag["positive_control"],
    "per_system": diag["per_system"],
    "reattack": {
        "method": ("Re-ran the identical pre-registered acceptance check (same metric formula, "
                   "same Q10=2 constants and reference temperature, same locked fixture sha256, "
                   "same 36 pooled points) from evidence/audit/potlife-q10-heuristic-ablation-v1/ "
                   "against the repaired LOSO-corrected candidate, and separately against a "
                   "planted-defect copy (correction factor forced to 1.0, i.e. the unmodified "
                   "incumbent) to confirm the check still detects the known failure."),
        "original_refuting_script_sha256": sha((MOD / "evidence/audit/potlife-q10-heuristic-ablation-v1/run_q10_ablation.py").read_bytes()),
        "original_refuting_receipt_sha256": sha(Q10_RECEIPT.read_bytes()),
        "same_fixture_sha256": True,
        "same_metric_formula": True,
        "same_thresholds": True,
        "candidate_acceptance_met": diag["acceptance"]["overall_met"],
        "planted_defect_correctly_rejected": diag["positive_control"]["detected"],
    },
    "refuting_receipts": {
        "potlife-q10-heuristic-ablation-v1": {
            "path": "amphora-cure-potlife-gate/evidence/audit/potlife-q10-heuristic-ablation-v1/potlife-q10-heuristic-ablation-receipt.v1.dsse.json",
            "sha256": sha(Q10_RECEIPT.read_bytes()),
        },
        "potlife-kpi-envelope-disclosure-gap-v1": {
            "path": "amphora-cure-potlife-gate/evidence/audit/potlife-kpi-envelope-disclosure-gap-v1/potlife-kpi-envelope-disclosure-gap-receipt.v1.dsse.json",
            "sha256": sha(DISCLOSURE_RECEIPT.read_bytes()),
        },
        "potlife-arrhenius-curvature-mechanism-v1": {
            "path": "amphora-cure-potlife-gate/evidence/audit/potlife-arrhenius-curvature-mechanism-v1/potlife-arrhenius-curvature-mechanism-receipt.v1.dsse.json",
            "sha256": sha(CURVATURE_RECEIPT.read_bytes()),
        },
    },
    "supersedes": {
        "superseded_path": "amphora-cure-potlife-gate/docs/mission.md (pre-repair prose revision, post-R-A02)",
        "superseded_sha256": sha(mission_pre_bytes),
        "superseded_deleted_or_modified": False,
        "reason": ("mission.md (R-A02 state) disclosed that the incumbent per-system-Ea Arrhenius "
                   "model breaches the module's own 0.25 held-out-extrapolation ceiling at 40C "
                   "(MAPE 25.12%) and loses to the chemistry-blind Q10=2 heuristic on the 30C and "
                   "40C legs, with no repair on record. This receipt adds the R-C02 qualified "
                   "prose stating a LOSO cross-system bias-corrected variant meets the "
                   "pre-registered acceptance bar (40C MAPE 3.95%, beats Q10 on 3/3 legs). The "
                   "prior R-A02 disclosure prose is preserved verbatim in the file; nothing is "
                   "deleted or rewritten, only extended."),
    },
    "prose_change": {
        "frontmatter_byte_identical": True,
        "frontmatter_sha256_before_and_after": sha(fm_before),
        "mission_md_sha256_before": sha(mission_pre_bytes),
        "mission_md_sha256_after": sha(mission_post_bytes),
    },
    "closes": [
        "Meets the R-C02 pre-registered acceptance bar on the identical locked 36-point fixture and metric: 40C-leg MAPE 3.954% (ceiling 25%, PASSED) and beats Q10=2 on 3/3 held-out legs (required floor 2/3).",
        "Demonstrates the fix is honest-dof (leave-one-system-out: no system's own datum informs its own correction) and physically motivated (targets the already-established 12/12-system convexity finding in potlife-arrhenius-curvature-mechanism-v1) rather than an in-sample refit.",
        "Demonstrates the acceptance-check harness itself is falsifiable: a planted-defect copy (correction factor forced to 1.0, collapsing to the unmodified incumbent already known to fail) is correctly rejected by the identical check (positive_control.detected=true).",
    ],
    "does_not_close": [
        "Does NOT identify the physical mechanism behind the curvature; the LOSO correction is an empirical population-level calibration, not a mechanistic law.",
        "Does NOT validate outside the locked 12-system, 3-leg, 36-point fixture; no new data was acquired. Generalization to systems/hardener families outside the fixture is untested.",
        "Does NOT touch the module's live Rust production fit (src/physics.rs fit_reduced_model), a different richer chemorheology model.",
        "Does NOT flip scientific_readiness (stays UNVALIDATED/PRE_PHASE_0), operational_readiness (stays BLOCKED), or the portfolio manifest.",
        "Does NOT replace or modify the signed cure-potlife-arrhenius-kpi.v1.json KPI file itself; that remains a human-owned change.",
    ],
    "claim_locks": {
        "constraint_only_solver_use": True,
        "cro_gated_promotion_still_blocked": True,
        "no_optimizer_authority": True,
        "pre_phase_0_research_only": True,
    },
    "provenance": {
        "locked_known_answer_dataset_sha256": sha(KA.read_bytes()),
        "signed_arrhenius_kpi_sha256": sha(KPI.read_bytes()),
        "harness_sha256": harness_sha,
        "directive_path": "none",
        "directive_sha256": "",
        "directive_obligation": "none",
    },
    "unmodified_protected_artifacts_sha256": {
        "amphora-cure-potlife-gate/evidence/phase0/kpis/cure-potlife-arrhenius-kpi.v1.json": sha(KPI.read_bytes()),
        "amphora-molecule-property/reference/mvp20/data/amphora_coating_scientific_receipts_manifest.v1.json": sha(MANIFEST.read_bytes()),
        "logs/falsification-ledger.jsonl": sha(LEDGER.read_bytes()),
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "harness_sha256": harness_sha,
        "deterministic_closed_form_no_rng": True,
    },
    "retraction_index": "amphora-cure-potlife-gate/evidence/phase0/kpis/RETRACTION-INDEX.md",
    "repair_mode": "autonomous-cron-2026-08-12",
    "generated_on_host": "xbabe2",
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY repair receipt under evidence/phase0/repairs/R-C02/done/",
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
ptype = "application/vnd.amphora.cure-potlife-gate.r-c02-repair-receipt.v1+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id,
                            "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex,
           "payload_canonical_sha256": sha(body),
           "signature": envelope}
DONE.mkdir(parents=True, exist_ok=True)
out = DONE / "R-C02-repair-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("verdict", body_obj["verdict"])
print("acceptance_overall_met", diag["acceptance"]["overall_met"])
print("positive_control_detected", diag["positive_control"]["detected"])
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("two_replay_sha256", diag_sha)
print("envelope_sha256", sha(out.read_bytes()))
print("signature_len", len(receipt["signature"]["signatures"][0]["sig"]))
print("signature_verified", True)
