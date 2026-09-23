#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-cro-protocol-packager CF-TIER evidence-tier
crosswalk audit receipt (campaign item CF-TIER, founder directive
AMPHORA-DIRECTIVE-2026-08-09 S7+S1, obligation CF-TIER).

AUDIT_ONLY. This is a falsification-first attack fire, not a repair: the
attack found the deliverable's evidence-tier crosswalk entirely absent, so
this receipt is CLAIM_REFUTED and is filed into
evidence/phase0/repairs/CF-TIER/attempts/ (NOT done/, since done_criteria
are not met). It does not modify the manifest, does not promote authority,
does not touch mission.md front matter.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-cro-protocol-packager/evidence/audit/cf-tier-evidence-tier-crosswalk-v1"
ATTEMPTS_DIR = ROOT / "amphora-cro-protocol-packager/evidence/phase0/repairs/CF-TIER/attempts"
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


# --- two-replay gate --------------------------------------------------------
canon = (BENCH / "diagnostic.canonical.json").read_bytes()
runB = (BENCH / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag = json.loads(canon)
assert diag["verdict"] == "CLAIM_REFUTED"
harness_sha = sha((BENCH / "run_cf_tier_evidence_tier_crosswalk_audit.py").read_bytes())

# --- derive public key / key_id from on-host seed ---------------------------
eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"

trust = json.loads(TRUST.read_text())
trust_by_role = {k.get("role"): k for k in trust["keys"]}
eval_derives_pin = (eval_key_id == trust_by_role.get("PHASE0_EVALUATOR", {}).get("key_id"))

# --- receipt body -----------------------------------------------------------
body_obj = {
    "schema": "amphora.cro-protocol-packager.cf-tier-evidence-tier-crosswalk-audit-receipt.v1",
    "study_id": diag["study_id"],
    "authority": "AUDIT_ONLY",
    "module": "amphora-cro-protocol-packager",
    "campaign_item_id": "CF-TIER",
    "run_type": "falsification_attack",
    "directive_path": diag["directive_path"],
    "directive_sha256": diag["directive_sha256"],
    "directive_obligation": diag["directive_obligation"],
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_pinned_fixture": False,
    "modifies_mission_front_matter": False,
    "modifies_mission_prose": False,
    "claim_under_attack": diag["claim_under_attack"],
    "deliverable_under_test": diag["deliverable_under_test"],
    "blueprint_sha256": diag["blueprint_sha256"],
    "cro_protocol_sha256": diag["cro_protocol_sha256"],
    "capture_template_sha256": diag["capture_template_sha256"],
    "corpus_sha256": diag["corpus_sha256"],
    "dataset_ledger_path": diag["dataset_ledger_path"],
    "dataset_ledger_sha256": diag["dataset_ledger_sha256"],
    "dataset_ledger_n_entries": diag["dataset_ledger_n_entries"],
    "refutation_criterion_verbatim": diag["refutation_criterion_verbatim"],
    "refutation_criterion_observed": diag["refutation_criterion_observed"],
    "attack_shape_verbatim": diag["attack_shape_verbatim"],
    "n_elements_audited": diag["n_elements_audited"],
    "n_ingredient_choice_elements": diag["n_ingredient_choice_elements"],
    "n_loading_level_elements": diag["n_loading_level_elements"],
    "n_process_parameter_elements": diag["n_process_parameter_elements"],
    "n_elements_missing_tag": diag["n_elements_missing_tag"],
    "n_elements_missing_confidence_rating": diag["n_elements_missing_confidence_rating"],
    "n_elements_missing_required_dataset_ledger_or_commissioned_xref": diag["n_elements_missing_required_dataset_ledger_or_commissioned_xref"],
    "n_elements_failing_refutation_criterion": diag["n_elements_failing_refutation_criterion"],
    "elements_missing_tag_ids": diag["elements_missing_tag_ids"],
    "module_gap_coverage": diag["module_gap_coverage"],
    "bom_element_findings": diag["bom_element_findings"],
    "process_parameter_findings": diag["process_parameter_findings"],
    "finding": diag["finding"],
    "verdict": "CLAIM_REFUTED",
    "campaign_item_status": "pending",
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": sha(canon),
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "diagnostic_script_sha256": harness_sha,
    },
    "does_not_close": diag["does_not_close"],
    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under evidence/audit/ and evidence/phase0/repairs/CF-TIER/attempts/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_derives_pin),
    },
}

body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.cro-protocol-packager-cf-tier-evidence-tier-crosswalk-audit+json"
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

out = BENCH / "cf-tier-evidence-tier-crosswalk-audit-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

ATTEMPTS_DIR.mkdir(parents=True, exist_ok=True)
attempts_out = ATTEMPTS_DIR / "cf-tier-evidence-tier-crosswalk-audit-receipt.v1.dsse.json"
attempts_out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

# --- self-verify -------------------------------------------------------------
pk = Ed25519PublicKey.from_public_bytes(eval_pub)
pk.verify(base64.standard_b64decode(envelope["signatures"][0]["sig"]),
          pae(ptype, base64.standard_b64decode(envelope["payload"])))
pk.verify(base64.standard_b64decode(json.loads(attempts_out.read_text())["signature"]["signatures"][0]["sig"]),
          pae(ptype, base64.standard_b64decode(json.loads(attempts_out.read_text())["signature"]["payload"])))

print("WROTE", out)
print("WROTE", attempts_out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_derives_pin)
print("receipt_body_sha256", sha(body))
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
