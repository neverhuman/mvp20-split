#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-ingredient-library
load-bearing-classification-completeness-v1 AUDIT_ONLY receipt. AUDIT_ONLY:
signs an audit receipt under evidence/audit/; does NOT sign a phase0
evaluation/review, does NOT promote authority, does NOT flip
scientific_readiness, does NOT modify the portfolio manifest, module-manifest.json,
any locked dataset, or a signed Phase-0 KPI. Derived key_id cross-checked vs
pinned trust store.

This is a REFUTATION receipt (not a survival): no positive_control block is
required. The refutation criterion was pre-registered in the oracle's own
docstring/refutation_criterion field before the search ran, and the oracle
itself found 3 facts.json keys marked load_bearing=false that are genuinely
consumed by DSSE-signed downstream artifacts elsewhere in the portfolio and
have zero gated independent second-source check anywhere in this module's
own audit trail -- refuting the completeness claim every prior
external-verification KPI in this module has relied on.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-ingredient-library/evidence/audit/load-bearing-classification-completeness-v1"
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
oracle_sha = sha((BENCH / "run_lb_completeness.py").read_bytes())
manifest_sha = sha((ROOT / "module-manifest.json").read_bytes())
facts_sha = diag["inputs"]["facts_json_sha256"]

assert diag["verdict"] == "CLAIM_REFUTED", "expected a refutation this fire"

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

body_obj = {
    "schema": "amphora.ingredient-library.load-bearing-classification-completeness-receipt.v1",
    "authority": "AUDIT_ONLY",
    "run_type": diag["run_type"],
    "module": "amphora-ingredient-library",
    "promotes_authority": False, "flips_scientific_readiness": False,
    "human_review_performed": False,
    "modifies_manifest": False, "modifies_module_manifest": False,
    "modifies_locked_dataset": False, "modifies_signed_phase0_kpi": False,
    "purpose": diag["purpose"],
    "refutation_criterion": diag["refutation_criterion"],
    "attacked_claims": [
        "amphora-ingredient-library/evidence/phase0/kpis/hardener-tds-verified-constants-kpi.v1.json "
        "(as extended by repair W-ING2's superseding-kpi): 'every load-bearing constant "
        "externally verified' -- scope defined solely by facts.json's own load_bearing boolean.",
        "amphora-ingredient-library/evidence/audit/pigment-density-second-source-verification-v1/"
        "pigment-density-second-source-verification-receipt.v1.dsse.json: pigment.barytes.density "
        "and pigment.talc.density are 'the LAST two load-bearing pigment density constants ... "
        "needing ... corroboration'.",
    ],
    "results": {
        "headline": diag["headline"],
        "verdict": diag["verdict"],
        "refuted_fact_keys": diag["headline"]["refuted_fact_keys"],
        "flagged_facts_reaching_signed_downstream_artifact": diag["flagged_facts_reaching_signed_downstream_artifact"],
        "downstream_receipt_verification": diag["downstream_receipt_verification"],
        "ledger_cross_check": diag["ledger_cross_check"],
        "gated_status_of_flagged_facts": diag["gated_status_of_flagged_facts"],
    },
    "finding_summary": (
        "3 of facts.json's 60 non-load-bearing entries -- pigment.zinc_phosphate.density "
        "(3.20 g/cm3 class, marine anti-corrosive inhibitive pigment), "
        "pigment.iron_oxide_red.density, and pigment.mica.density (barrier pigment) -- are "
        "genuinely consumed as direct BOM mass/volume-balance inputs by code backing THREE "
        "separate DSSE-signed downstream artifacts in other modules: "
        "amphora-formulation-arithmetic's CF-ARITH done receipt (2026-08-10, SURVIVED), "
        "amphora-formulation-arithmetic's W-T-ARITH done receipt (2026-08-13), and "
        "amphora-redteam-audit's formulation-arithmetic-dimensioned-v1 benchmark replay "
        "receipt. None of the three has ever received a GATED (pass/fail) independent "
        "second-source density check anywhere in amphora-ingredient-library's own audit "
        "trail: constant-crosscheck-v1's own PIG_REF table already carries a CRC/mineralogical "
        "reference value for all three, but that block is explicitly labelled 'Reported only, "
        "NOT gated' in the oracle's own diagnostic text, and "
        "pigment-density-second-source-verification-v1 explicitly scoped itself to only the 2 "
        "facts.json marks load_bearing=true (barytes, talc), asserting those are 'the LAST two' "
        "needing coverage. That completeness assertion is false: facts.json's load_bearing flag "
        "reflects only what THIS module's own scripts happen to gate, not what the portfolio "
        "actually depends on. This mirrors the exact failure class W-ING2 already found once "
        "(2026-08-09, hardener AHEW scope narrower than claimed) -- recurring at the "
        "classification-mechanism level, not just the per-constant level."
    ),
    "grants_no_authority": [
        "no_batch_release_authority", "no_manufacturing_qualification_authority",
        "no_optimizer_authority", "no_patentability_authority", "no_regulatory_authority",
        "no_release_authority", "no_safety_authority", "no_solver_authority",
        "no_wet_lab_evidence_upgrade", "no_phase_1_or_phase_2_claim", "fto_not_performed",
    ],
    "provenance": {
        "facts_json_sha256": facts_sha,
        "module_manifest_sha256": manifest_sha,
        "oracle_sha256": oracle_sha,
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
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
ptype = "application/vnd.amphora.ingredient-library-load-bearing-classification-completeness-receipt.v1+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
out = BENCH / "load-bearing-classification-completeness-receipt.v1.dsse.json"
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
print("verdict", diag["verdict"])
print("signature_verified", True)
