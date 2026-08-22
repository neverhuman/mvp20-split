#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-cure-potlife-gate EA-UNCERTAINTY-PERTURBATION
audit receipt. Escalates potlife-ea-source-admissibility-v1's framing/
provenance finding (8/12 systems' Ea is a family/class-level literature
average, not system-specific) into a numeric robustness test of R-C02's LOSO
bias-correction acceptance bar. AUDIT_ONLY: signs an audit receipt under
evidence/audit/; does NOT sign a phase0 evaluation/review, does NOT promote
authority, does NOT flip scientific_readiness, does NOT modify the portfolio
manifest, the locked known-answer dataset, the signed Arrhenius Phase-0 KPI,
R-C02, or any prior signed receipt."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-cure-potlife-gate"
AUDIT = MOD / "evidence/audit/potlife-ea-uncertainty-perturbation-v1"
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
ADMISS_RECEIPT = MOD / "evidence/audit/potlife-ea-source-admissibility-v1/potlife-ea-source-admissibility-receipt.v1.dsse.json"
KO_DIAG = MOD / "benchmarks/kissinger-ozawa-baseline-v1/diagnostic.canonical.json"


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
harness_sha = sha((WORK / "run_ea_uncertainty_perturbation.py").read_bytes())

assert diag["positive_control"]["detected"] is True, "positive control did not fire"
verdict = diag["verdict"]
assert verdict in ("CLAIM_REFUTED", "CLAIM_SURVIVED")

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
    "schema": "amphora.cure-potlife-gate.ea-uncertainty-perturbation-audit-receipt.v1",
    "module": "amphora-cure-potlife-gate",
    "authority": "AUDIT_ONLY",
    "axis": "DATA_ADMISSIBILITY_NUMERIC_CONSEQUENCE",
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
    "attack_type": diag["attack_type"],
    "attacks": diag["attacks"],
    "also_examines_lineage": diag["also_examines_lineage"],
    "claim_under_attack": diag["claim_under_attack"],
    "falsification_criterion": diag["falsification_criterion"],
    "dataset": diag["dataset"],
    "uncertainty_magnitude_provenance": diag["uncertainty_magnitude_provenance"],
    "admissibility_classification_provenance": diag["admissibility_classification_provenance"],
    "baseline_unperturbed": diag["baseline_unperturbed"],
    "real_attack_scenarios": diag["real_attack_scenarios"],
    "real_any_scenario_breaches_acceptance": diag["real_any_scenario_breaches_acceptance"],
    "positive_control": diag["positive_control"],
    "verdict": verdict,
    "verdict_meaning": diag["verdict_meaning"],
    "closes": [
        "Escalates potlife-ea-source-admissibility-v1's framing finding (8/12 systems' Ea is "
        "FAMILY_CLASS_APPROXIMATE, not system-specific) into a numeric test: perturbing those 8 "
        "systems' Ea by the real, already-signed, empirically-measured Kissinger-vs-OFW "
        "inter-method spread (5.75%) in either direction leaves R-C02's LOSO-corrected acceptance "
        "bar intact (40C corrected MAPE moves from 3.95% to 4.07%/5.44%, both far under the 25% "
        "ceiling; all 3 legs still beat Q10).",
        "Establishes the acceptance bar's real margin against this specific uncertainty axis: a "
        "naive control at 5x the measured spread (~28.7%) still did not break it; the bar only "
        "breaks (40C MAPE 30.9-31.3%) once the perturbation reaches ~50% (~8.7x measured), which "
        "is far outside the range any of the 8 systems' actual family/class citations plausibly "
        "support -- so the R-C02 acceptance bar has genuine, non-trivial margin against Ea "
        "citation imprecision, not merely an untested one.",
    ],
    "does_not_close": [
        "Does NOT dispute potlife-ea-source-admissibility-v1's finding that the 'per-system "
        "published Ea' framing language is inaccurate for 8/12 systems -- that framing/provenance "
        "defect stands as signed and is orthogonal to this numeric result.",
        "Does NOT test correlated/non-uniform perturbation patterns (e.g. only a subset of the 8 "
        "systems shifted, or shifts correlated with hardener_family) -- only a uniform +/- shift "
        "across all 8 family-class-approximate systems simultaneously was tested.",
        "Does NOT modify the locked known-answer fixture, the signed KPI, R-C02, the "
        "admissibility receipt, or the kissinger-ozawa-baseline benchmark -- all are cited by "
        "sha256 only.",
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
        "ea_source_admissibility_receipt_sha256": sha(ADMISS_RECEIPT.read_bytes()),
        "kissinger_ozawa_baseline_diagnostic_sha256": sha(KO_DIAG.read_bytes()),
        "harness_sha256": harness_sha,
        "directive_path": "none",
        "directive_sha256": "",
        "directive_obligation": "none",
    },
    "unmodified_protected_artifacts_sha256": {
        "amphora-cure-potlife-gate/evidence/phase0/kpis/cure-potlife-arrhenius-kpi.v1.json": sha(KPI.read_bytes()),
        "amphora-cure-potlife-gate/evidence/phase0/repairs/R-C02/done/R-C02-repair-receipt.v1.dsse.json": sha(RC02_RECEIPT.read_bytes()),
        "amphora-cure-potlife-gate/evidence/audit/potlife-ea-source-admissibility-v1/potlife-ea-source-admissibility-receipt.v1.dsse.json": sha(ADMISS_RECEIPT.read_bytes()),
        "amphora-cure-potlife-gate/benchmarks/kissinger-ozawa-baseline-v1/diagnostic.canonical.json": sha(KO_DIAG.read_bytes()),
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
ptype = "application/vnd.amphora.cure-potlife-gate.ea-uncertainty-perturbation-audit-receipt.v1+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id,
                            "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex,
           "payload_canonical_sha256": sha(body),
           "signature": envelope}
AUDIT.mkdir(parents=True, exist_ok=True)
out = AUDIT / "potlife-ea-uncertainty-perturbation-receipt.v1.dsse.json"
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
