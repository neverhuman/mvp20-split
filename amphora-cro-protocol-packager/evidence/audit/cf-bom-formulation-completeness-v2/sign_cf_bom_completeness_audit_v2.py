#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-cro-protocol-packager CF-BOM formulation-
completeness audit receipt, ROUND 2 (campaign item CF-BOM, founder directive
AMPHORA-DIRECTIVE-2026-08-09 S7, obligation CF-BOM).

AUDIT_ONLY. Fire 2/3. Reconfirms fire 1's CLAIM_REFUTED with a byte-hash
comparison against the fire-1-cited inputs, adds the still-outstanding
positive-control mutation test from the attack shape's first sentence, and
records the cross-module ownership blocker on landing an actual repair.
Filed into evidence/phase0/repairs/CF-BOM/attempts/ (NOT done/, since
done_criteria are still not met -- no repair has landed).
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-cro-protocol-packager/evidence/audit/cf-bom-formulation-completeness-v2"
ATTEMPTS_DIR = ROOT / "amphora-cro-protocol-packager/evidence/phase0/repairs/CF-BOM/attempts"
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
harness_sha = sha((BENCH / "run_cf_bom_completeness_audit_v2.py").read_bytes())

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
    "schema": "amphora.cro-protocol-packager.cf-bom-formulation-completeness-audit-receipt.v2",
    "study_id": diag["study_id"],
    "authority": "AUDIT_ONLY",
    "module": "amphora-cro-protocol-packager",
    "campaign_item_id": "CF-BOM",
    "run_type": "falsification_attack",
    "fire_sequence": 2,
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
    "deliverable_sha256": diag["deliverable_sha256"],
    "sourcing_corpus_under_test": diag["sourcing_corpus_under_test"],
    "sourcing_corpus_sha256": diag["sourcing_corpus_sha256"],
    "refutation_criterion_verbatim": diag["refutation_criterion_verbatim"],
    "refutation_criterion_observed": diag["refutation_criterion_observed"],
    "attack_shape_verbatim": diag["attack_shape_verbatim"],
    "step_a_reconfirm": diag["step_a_reconfirm"],
    "step_b_positive_control": diag["step_b_positive_control"],
    "step_c_discrimination_control": diag["step_c_discrimination_control"],
    "structural_finding": diag["structural_finding"],
    "reconfirms_prior_receipt": diag["reconfirms_prior_receipt"],
    "prior_diagnostic_script_sha256_cited": diag["prior_diagnostic_script_sha256_cited"],
    "finding": (
        "CLAIM_REFUTED (reconfirmed, fire 2/3): the CF-BOM deliverable is byte-"
        "identical to the state fire 1 refuted -- deliverable_unchanged_since_fire1="
        + str(diag["step_a_reconfirm"]["deliverable_unchanged_since_fire1"])
        + ", sourcing_corpus_unchanged_since_fire1="
        + str(diag["step_a_reconfirm"]["sourcing_corpus_unchanged_since_fire1"])
        + ". No repair has landed. This fire additionally ran the attack shape's "
        "still-outstanding positive-control mutation test: deleting the dgeba_828 "
        "line's EEW-bearing TDS citation in an in-memory copy causes the "
        "completeness check to fire on that specific line (detected="
        + str(diag["step_b_positive_control"]["detected"])
        + "), and a synthetic fully-repaired copy (every line given a concrete "
        "domestic determination and an explicit tier label) causes the SAME "
        "checker to report refuted=False (discrimination_control_passed="
        + str(diag["step_c_discrimination_control"]["discrimination_control_passed"])
        + "), confirming the checker genuinely discriminates complete from "
        "incomplete BOMs rather than being hard-wired to always refute. "
        "STRUCTURAL FINDING: landing the actual repair requires edits to "
        "amphora-report-packager/reference/mvp20/out/blueprint.md and "
        "amphora-source-ledger/reference/mvp20/data/source_records.json, both "
        "outside amphora-cro-protocol-packager and thus outside this fire's "
        "binding write-scope; repair cannot be landed from within this module "
        "this fire."
    ),
    "verdict": "CLAIM_REFUTED",
    "repair_status": "in_progress",
    "campaign_item_status": "blocked",
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": sha(canon),
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "diagnostic_script_sha256": harness_sha,
    },
    "does_not_close": (
        "This receipt does not repair the BOM deliverable. It reconfirms the "
        "fire-1 refutation is still the truthful current state (inputs byte-"
        "identical), strengthens it with a positive control demonstrating the "
        "completeness checker actually discriminates complete from incomplete "
        "BOMs, and records the cross-module ownership blocker preventing repair "
        "from landing within amphora-cro-protocol-packager's write scope."
    ),
    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under evidence/audit/ and evidence/phase0/repairs/CF-BOM/attempts/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_derives_pin),
    },
}

body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.cro-protocol-packager-cf-bom-formulation-completeness-audit+json"
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

out = BENCH / "cf-bom-formulation-completeness-audit-receipt.v2.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

ATTEMPTS_DIR.mkdir(parents=True, exist_ok=True)
attempts_out = ATTEMPTS_DIR / "cf-bom-formulation-completeness-audit-receipt.v2.dsse.json"
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
