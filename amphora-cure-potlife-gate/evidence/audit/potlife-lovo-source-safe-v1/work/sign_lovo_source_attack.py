#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-cure-potlife-gate LOVO-SOURCE-SAFE attack
AUDIT_ONLY receipt. This re-attacks R-C02 (LOSO cross-system bias correction)
along a THIRD split axis (leave-one-vendor/source-out), orthogonal to the
hardener-family axis already tested by potlife-lofo-family-safe-v1. AUDIT_ONLY:
signs an audit receipt under evidence/audit/; does NOT sign a phase0
evaluation/review, does NOT promote authority, does NOT flip
scientific_readiness (stays UNVALIDATED/PRE_PHASE_0), does NOT modify the
portfolio manifest, the locked known-answer dataset, the signed Arrhenius
Phase-0 KPI, the R-C02 repair receipt, the LOFO attack receipt, or any other
prior signed receipt. Derived key_id cross-checked vs the pinned trust store."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-cure-potlife-gate"
AUDIT = MOD / "evidence/audit/potlife-lovo-source-safe-v1"
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
harness_sha = sha((WORK / "run_lovo_source_attack.py").read_bytes())

assert diag["loso_reproduction_matches_rc02_signed_numbers"] is True, "harness LOSO reproduction does not match R-C02's signed numbers -- harness is not trustworthy"
assert diag["positive_control"]["detected"] is True, "positive control did not fire -- cannot license CLAIM_SURVIVED"

verdict = "CLAIM_SURVIVED" if diag["lovo_result"]["acceptance"]["overall_met"] else "CLAIM_REFUTED"

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
    "schema": "amphora.cure-potlife-gate.lovo-source-safe-attack-receipt.v1",
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
              "on the incumbent per-system published-Ea Arrhenius model generalizes to a "
              "vendor/source-safe (leave-one-source-out) holdout -- i.e. its pass on R-C02's own "
              "acceptance bar, and the LOFO attack's confirmation of it, are not artifacts of "
              "vendor-protocol leakage through same-vendor systems remaining in the correction "
              "pool, an axis that cuts across hardener_family and was not excluded by the LOFO "
              "attack (huntsman, air_products and momentive TDS sources each span 2-3 different "
              "hardener families in this fixture)."),
    "falsification_criterion": diag["falsification_criterion"],
    "dataset": diag["dataset"],
    "loso_reproduction": diag["loso_reproduction"],
    "loso_reproduction_matches_rc02_signed_numbers": diag["loso_reproduction_matches_rc02_signed_numbers"],
    "lovo_result": diag["lovo_result"],
    "comparison": diag["comparison"],
    "verdict": verdict,
    "verdict_meaning": ("The LOVO-corrected candidate meets the identical pre-registered R-C02 "
                         "acceptance bar (40C-leg MAPE <= 0.25 AND beats Q10=2 on >= 2/3 legs): "
                         "40C-leg MAPE 4.338% (ceiling 25%) and beats Q10 on 3/3 legs. Degradation "
                         "vs LOSO is small and non-monotone on every leg (10C -0.239pp [improves], "
                         "30C +0.056pp, 40C +0.384pp), and slightly larger at 40C than LOFO's own "
                         "+0.215pp degradation but still two orders of magnitude below the 25pp "
                         "ceiling headroom. The vendor-protocol-leakage failure mode this attack "
                         "targeted (a population-level correction actually absorbing vendor TDS "
                         "reporting-convention artifacts rather than universal reaction curvature) "
                         "did not manifest: holding out an entire vendor's systems, including ones "
                         "in different hardener families than any remaining pool member, does not "
                         "break the pass."),
    "positive_control": diag["positive_control"],
    "closes": [
        "Shows R-C02's SURVIVED verdict is not an artifact of vendor/source-protocol leakage in "
        "the LOSO correction pool, on an axis that is genuinely orthogonal to hardener_family: "
        "huntsman, air_products and momentive TDS sources each span 2-3 different hardener "
        "families, so LOFO's family-safe pooling alone did not exclude this leakage path -- LOVO "
        "does, and the pass still holds with sub-percentage-point degradation.",
        "Cross-validates the attack harness itself: LOSO reproduction (pooling='loso' in this "
        "script) reproduces R-C02's signed leg_summary numbers exactly (loso_reproduction_matches_rc02_signed_numbers=true).",
    ],
    "does_not_close": [
        "Does NOT test a hardener family or vendor absent from the 12-system fixture entirely; "
        "no new data was acquired or may be acquired this fire.",
        "Does NOT identify the physical mechanism behind the curvature; still an empirical "
        "population-level calibration per R-C02.",
        "Does NOT touch the module's live Rust production fit, the signed cure-potlife-arrhenius-kpi.v1.json, "
        "the R-C02 repair receipt, or the LOFO attack receipt -- all remain unmodified.",
        "mitsubishi has only 1 member (dgeba-mxda) in this fixture, so its LOVO correction pool "
        "(10 systems) differs from LOSO's 11-system pool by only 1; the vendor-safe test is most "
        "informative for the multi-member vendor groups (dow, huntsman, air_products, momentive, "
        "academic_1993).",
        "The academic_1993 group (dgeba-mpda, dgeba-mda) both cite Ellis 1993 Chapter 5 but for "
        "genuinely different original measurements (Aldrich MPDA TDS vs generic MDA); grouping "
        "them together is a conservative (harder) choice, not a weakening of the split.",
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
        "harness_sha256": harness_sha,
        "directive_path": "none",
        "directive_sha256": "",
        "directive_obligation": "none",
    },
    "unmodified_protected_artifacts_sha256": {
        "amphora-cure-potlife-gate/evidence/phase0/kpis/cure-potlife-arrhenius-kpi.v1.json": sha(KPI.read_bytes()),
        "amphora-cure-potlife-gate/evidence/phase0/repairs/R-C02/done/R-C02-repair-receipt.v1.dsse.json": sha(RC02_RECEIPT.read_bytes()),
        "amphora-cure-potlife-gate/evidence/audit/potlife-lofo-family-safe-v1/potlife-lofo-family-safe-receipt.v1.dsse.json": sha(LOFO_RECEIPT.read_bytes()),
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
ptype = "application/vnd.amphora.cure-potlife-gate.lovo-source-safe-attack-receipt.v1+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id,
                            "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex,
           "payload_canonical_sha256": sha(body),
           "signature": envelope}
AUDIT.mkdir(parents=True, exist_ok=True)
out = AUDIT / "potlife-lovo-source-safe-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("verdict", verdict)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("two_replay_sha256", diag_sha)
print("envelope_sha256", sha(out.read_bytes()))
print("signature_len", len(receipt["signature"]["signatures"][0]["sig"]))
print("signature_verified", True)
