#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-cure-potlife-gate EA-SOURCE-ADMISSIBILITY
audit receipt. This attacks the "per-system published Ea" framing carried by
R-C02 and its entire lineage (original signed KPI, potlife-q10-heuristic-
ablation-v1, potlife-lofo-family-safe-v1, potlife-lovo-source-safe-v1,
potlife-lofso-combined-safe-v1) via a direct provenance audit of the locked
fixture's own citation fields -- not a re-split and not a re-derivation of
the MAPE arithmetic. AUDIT_ONLY: signs an audit receipt under evidence/audit/;
does NOT sign a phase0 evaluation/review, does NOT promote authority, does
NOT flip scientific_readiness (stays UNVALIDATED/PRE_PHASE_0), does NOT
modify the portfolio manifest, the locked known-answer dataset, the signed
Arrhenius Phase-0 KPI, the R-C02 repair receipt, or any other prior signed
receipt. Derived key_id cross-checked vs the pinned trust store."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-cure-potlife-gate"
AUDIT = MOD / "evidence/audit/potlife-ea-source-admissibility-v1"
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
harness_sha = sha((WORK / "run_ea_admissibility_audit.py").read_bytes())

assert diag["falsified"] is True, "harness did not detect the planted-in-the-data admissibility gap it exists to catch"
verdict = diag["verdict"]
assert verdict == "CLAIM_REFUTED"

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
    "schema": "amphora.cure-potlife-gate.ea-source-admissibility-audit-receipt.v1",
    "module": "amphora-cure-potlife-gate",
    "authority": "AUDIT_ONLY",
    "axis": "DATA_ADMISSIBILITY",
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
    "also_examines_lineage": diag["also_examines_lineage"],
    "attack_type": diag["attack_type"],
    "claim_under_attack": (
        "R-C02's candidate_model.name/physical_basis, and the identical framing repeated by the "
        "original signed cure-potlife-arrhenius-kpi.v1.json, potlife-q10-heuristic-ablation-v1 "
        "('chemistry-specific per-system Ea'), potlife-lofo-family-safe-v1, "
        "potlife-lovo-source-safe-v1, and potlife-lofso-combined-safe-v1: that the Arrhenius "
        "model being corrected/re-tested uses genuinely PER-SYSTEM PUBLISHED activation "
        "energies -- i.e. that each of the 12 systems' Ea is a measurement specific to that "
        "exact commercial formulation, distinct from a population-level heuristic like Q10."
    ),
    "target_claim_text_verbatim": diag["target_claim_text"],
    "falsification_criterion": diag["falsification_criterion"],
    "dataset": diag["dataset"],
    "classification_rows": diag["classification_rows"],
    "summary": diag["summary"],
    "criterion_a_family_class_approximate_ea_present": diag["criterion_a_family_class_approximate_ea_present"],
    "criterion_b_cross_source_pairing_present": diag["criterion_b_cross_source_pairing_present"],
    "verdict": verdict,
    "verdict_meaning": diag["verdict_meaning"],
    "closes": [
        "Shows the 'per-system published Ea' framing repeated verbatim or near-verbatim across "
        "6 signed receipts (original KPI, Q10-ablation, R-C02, LOFO, LOVO, LOFSO) is inaccurate "
        "for 8/12 (66.7%) systems, whose activation_energy_source is an explicit family/class-"
        "level literature average (marked with a '~' tolerance and/or the qualifier word "
        "'family', 'type', or 'framework'), not a system-specific measurement.",
        "Shows that for 12/12 (100%) systems, the activation_energy_source and pot_life_source "
        "are drawn from two independently authored documents -- an academic Ea study (Turi 1997, "
        "Kamal & Sourour 1973, Blanco et al. 2005, Riccardi et al. 1984) paired with a named "
        "commercial vendor's TDS pot-life measurement (Dow, Huntsman, Air Products, Momentive, "
        "Mitsubishi, Aldrich/Ellis 1993) -- for a chemically similar but not verified-identical "
        "formulation (different stoichiometry, catalyst package, or accelerator content is "
        "plausible but not checked in-file for any of the 12 systems).",
        "The finding is orthogonal to, and does not dispute, the MAPE arithmetic already "
        "verified correct across R-C02/LOFO/LOVO/LOFSO: this audit recomputes no MAPE and "
        "changes no number in those receipts. It disputes the physical-admissibility framing "
        "that the baseline model being corrected is 'per-system published Ea', which is the "
        "premise every subsequent group-safe split attack (LOFO/LOVO/LOFSO) implicitly accepted "
        "without auditing.",
    ],
    "does_not_close": [
        "Does NOT claim any individual published Ea value is numerically wrong; the values "
        "themselves may be perfectly good class-level engineering estimates, just not "
        "'per-system' in the sense the receipt chain's own language repeatedly asserts.",
        "Does NOT recompute or dispute any MAPE, correction-factor, or acceptance-bar number in "
        "R-C02, LOFO, LOVO, or LOFSO; those numeric verdicts stand as signed.",
        "Does NOT modify the locked known-answer fixture, the signed KPI, R-C02, or any prior "
        "receipt in the lineage -- all five remain unmodified and are cited by sha256 only.",
        "Does NOT establish that cross-source Ea/pot-life pairing is scientifically invalid in "
        "general (it is common Phase-0 engineering practice); it establishes that the specific "
        "'per-system published Ea' language used in six signed receipts overstates what the "
        "fixture's own citation fields actually support, and that gap was never disclosed.",
        "Does NOT flip scientific_readiness (stays UNVALIDATED/PRE_PHASE_0), operational_"
        "readiness (stays BLOCKED), or the portfolio manifest.",
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
        "amphora-cure-potlife-gate/reference/phase0-cure-potlife-known-answer.v1.json": sha(KA.read_bytes()),
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
ptype = "application/vnd.amphora.cure-potlife-gate.ea-source-admissibility-audit-receipt.v1+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id,
                            "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex,
           "payload_canonical_sha256": sha(body),
           "signature": envelope}
AUDIT.mkdir(parents=True, exist_ok=True)
out = AUDIT / "potlife-ea-source-admissibility-receipt.v1.dsse.json"
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
