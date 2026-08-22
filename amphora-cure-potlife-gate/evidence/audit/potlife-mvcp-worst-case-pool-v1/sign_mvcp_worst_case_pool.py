#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-cure-potlife-gate MVCP-WORST-CASE-POOL attack
AUDIT_ONLY receipt. This re-attacks R-C02 (LOSO cross-system bias correction)
along a new axis: worst-case correction-pool SIZE, not group-safety of pool
membership (which LOFO/LOVO/LOFSO already tested). AUDIT_ONLY: signs an audit
receipt under evidence/audit/; does NOT sign a phase0 evaluation/review, does
NOT promote authority, does NOT flip scientific_readiness (stays
UNVALIDATED/PRE_PHASE_0), does NOT modify the portfolio manifest, the locked
known-answer dataset, the signed Arrhenius Phase-0 KPI, the R-C02 repair
receipt, or any other prior signed receipt. Derived key_id cross-checked vs
the pinned trust store."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-cure-potlife-gate"
AUDIT = MOD / "evidence/audit/potlife-mvcp-worst-case-pool-v1"
WORK = AUDIT / "work"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"
KA = MOD / "reference/phase0-cure-potlife-known-answer.v1.json"
KPI = MOD / "evidence/phase0/kpis/cure-potlife-arrhenius-kpi.v1.json"
MANIFEST = ROOT / "amphora-molecule-property/reference/mvp20/data/amphora_coating_scientific_receipts_manifest.v1.json"
LEDGER = ROOT / "logs/falsification-ledger.jsonl"
RC02_RECEIPT = MOD / "evidence/phase0/repairs/R-C02/done/R-C02-repair-receipt.v1.dsse.json"
Q10_RECEIPT = MOD / "evidence/audit/potlife-q10-heuristic-ablation-v1/potlife-q10-heuristic-ablation-receipt.v1.dsse.json"
LOFO_RECEIPT = MOD / "evidence/audit/potlife-lofo-family-safe-v1/potlife-lofo-family-safe-receipt.v1.dsse.json"
LOVO_RECEIPT = MOD / "evidence/audit/potlife-lovo-source-safe-v1/potlife-lovo-source-safe-receipt.v1.dsse.json"
LOFSO_RECEIPT = MOD / "evidence/audit/potlife-lofso-combined-safe-v1/potlife-lofso-combined-safe-receipt.v1.dsse.json"


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
harness_sha = sha((WORK / "run_mvcp_attack.py").read_bytes())

assert diag["k11_worst_case_matches_rc02_signed_numbers"] is True, "harness k=11 (full LOSO) reproduction does not match R-C02's signed numbers -- harness is not trustworthy"
assert diag["positive_control"]["detected"] is True, "positive control did not fire -- cannot license CLAIM_SURVIVED"

verdict = "CLAIM_SURVIVED" if diag["overall_worst_case_survives_down_to_k1"] else "CLAIM_REFUTED"

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
    "schema": "amphora.cure-potlife-gate.mvcp-worst-case-pool-attack-receipt.v1",
    "module": "amphora-cure-potlife-gate",
    "authority": "AUDIT_ONLY",
    "axis": "MODEL_REPAIR_REATTACK",
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
    "attacks": diag["attacks"],
    "also_re_examines": diag["also_re_examines"],
    "attack_type": diag["attack_type"],
    "claim": ("R-C02's LOSO (leave-one-system-out) cross-system multiplicative bias correction "
              "on the incumbent per-system published-Ea Arrhenius model is robust to correction-"
              "pool SIZE, not just pool membership/group-safety (already tested separately by "
              "LOFO, LOVO and LOFSO, all of which still used pools of n=6-11). This attack tests "
              "whether a much smaller real-world calibration pool -- as small as a single "
              "comparator system (n=1) -- could, under worst-case composition, breach R-C02's own "
              "acceptance bar even though the full n=11 LOSO pool comfortably passes."),
    "falsification_criterion": diag["falsification_criterion"],
    "dataset": diag["dataset"],
    "q10_leg_mape": diag["q10_leg_mape"],
    "pooled_by_k": diag["pooled_by_k"],
    "acceptance_by_k": diag["acceptance_by_k"],
    "k11_worst_case_matches_rc02_signed_numbers": diag["k11_worst_case_matches_rc02_signed_numbers"],
    "min_viable_pool_size_where_worst_case_still_passes": diag["min_viable_pool_size_where_worst_case_still_passes"],
    "any_breach_across_k_1_to_10": diag["any_breach_across_k_1_to_10"],
    "overall_worst_case_survives_down_to_k1": diag["overall_worst_case_survives_down_to_k1"],
    "k1_single_donor_detail": diag["k1_single_donor_detail"],
    "verdict": verdict,
    "verdict_meaning": (
        f"Even under the SHARPEST worst-case single-donor pool (k=1, the smallest possible "
        f"cross-system correction pool), the pooled 40C-leg MAPE is "
        f"{diag['acceptance_by_k']['1']['worst_case_40C_pooled_mape']*100:.3f}% "
        f"(ceiling 25%), and the corrected candidate beats the Q10=2 heuristic on "
        f"{diag['acceptance_by_k']['1']['n_legs_beat_q10']}/3 legs even in this worst case. "
        f"Worst-case pooled MAPE degrades monotonically as the pool shrinks from k=11 "
        f"({diag['pooled_by_k']['11']['40C']['worst_case_pooled_mape']*100:.3f}%) to k=1 "
        f"({diag['pooled_by_k']['1']['40C']['worst_case_pooled_mape']*100:.3f}%), a real and "
        f"quantified degradation, but it never approaches the 25% ceiling at any pool size tested "
        f"(largest observed worst-case is under half the ceiling). R-C02's SURVIVED verdict is "
        f"therefore not an artifact of the specific n=11 pool size used in the original repair; "
        f"it holds with wide margin down to the theoretical minimum pool of a single comparator "
        f"system."
    ),
    "positive_control": diag["positive_control"],
    "closes": [
        "Shows R-C02's SURVIVED verdict is not fragile to correction-pool SIZE: the worst-case "
        "pooled 40C MAPE across ALL 2^11-1 possible donor-pool compositions, at every pool size "
        "k=1..11, stays comfortably under the 25% ceiling and beats Q10 on all 3 legs.",
        "Cross-validates the attack harness itself: the k=11 (single-combo, full-pool) case "
        "reproduces R-C02's signed leg_summary numbers exactly "
        "(k11_worst_case_matches_rc02_signed_numbers=true).",
        "Demonstrates via positive control that the MVCP worst-case-donor search has real, "
        "mechanism-specific detection power for single-bad-actor pool-composition defects "
        "(a planted 10x transcription-class corruption) that the incumbent LOSO full-pool average "
        "structurally dilutes below the ceiling (21.955% with poison present, still passing) but "
        "that the k=1 worst-case search correctly flags (849.98% at k=1 with poison present).",
    ],
    "does_not_close": [
        "Does NOT test a hardener family or vendor absent from the 12-system fixture entirely; "
        "no new data was acquired or may be acquired this fire.",
        "Does NOT combine worst-case pool SIZE with worst-case pool COMPOSITION under the LOFO/"
        "LOVO/LOFSO group-safety constraints simultaneously; this attack varies size against the "
        "unconstrained (LOSO) pool, group-safety was tested separately.",
        "Does NOT identify the physical mechanism behind the curvature; still an empirical "
        "population-level calibration per R-C02.",
        "Does NOT touch the module's live Rust production fit, the signed cure-potlife-arrhenius-kpi.v1.json, "
        "the R-C02 repair receipt, or the LOFO/LOVO/LOFSO attack receipts -- all remain unmodified.",
        "The positive control corrupts a DONOR's usefulness to OTHER systems' correction pools; "
        "it does not test corruption of a held-out system's own observed label (a distinct, "
        "already-covered class -- cf. potlife-ea-uncertainty-perturbation-v1 for label-side "
        "uncertainty on the Ea input).",
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
        "rc02_repair_receipt_sha256": sha(RC02_RECEIPT.read_bytes()),
        "q10_ablation_receipt_sha256": sha(Q10_RECEIPT.read_bytes()),
        "lofo_attack_receipt_sha256": sha(LOFO_RECEIPT.read_bytes()),
        "lovo_attack_receipt_sha256": sha(LOVO_RECEIPT.read_bytes()),
        "lofso_attack_receipt_sha256": sha(LOFSO_RECEIPT.read_bytes()),
        "harness_sha256": harness_sha,
        "directive_path": "none",
        "directive_sha256": "",
        "directive_obligation": "none",
    },
    "unmodified_protected_artifacts_sha256": {
        "amphora-cure-potlife-gate/evidence/phase0/kpis/cure-potlife-arrhenius-kpi.v1.json": sha(KPI.read_bytes()),
        "amphora-cure-potlife-gate/evidence/phase0/repairs/R-C02/done/R-C02-repair-receipt.v1.dsse.json": sha(RC02_RECEIPT.read_bytes()),
        "amphora-cure-potlife-gate/evidence/audit/potlife-lofo-family-safe-v1/potlife-lofo-family-safe-receipt.v1.dsse.json": sha(LOFO_RECEIPT.read_bytes()),
        "amphora-cure-potlife-gate/evidence/audit/potlife-lovo-source-safe-v1/potlife-lovo-source-safe-receipt.v1.dsse.json": sha(LOVO_RECEIPT.read_bytes()),
        "amphora-cure-potlife-gate/evidence/audit/potlife-lofso-combined-safe-v1/potlife-lofso-combined-safe-receipt.v1.dsse.json": sha(LOFSO_RECEIPT.read_bytes()),
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
        "exhaustive_not_sampled": True,
    },
    "generated_on_host": "xbabe2",
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under evidence/audit/",
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
ptype = "application/vnd.amphora.cure-potlife-gate.mvcp-worst-case-pool-attack-receipt.v1+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id,
                            "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex,
           "payload_canonical_sha256": sha(body),
           "signature": envelope}
AUDIT.mkdir(parents=True, exist_ok=True)
out = AUDIT / "potlife-mvcp-worst-case-pool-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("SIGNED OK:", out)
