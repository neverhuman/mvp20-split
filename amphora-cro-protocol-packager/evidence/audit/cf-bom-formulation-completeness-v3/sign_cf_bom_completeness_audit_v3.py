#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-cro-protocol-packager CF-BOM formulation-
completeness audit receipt, ROUND 3 / FINAL (campaign item CF-BOM, founder
directive AMPHORA-DIRECTIVE-2026-08-09 S7, obligation CF-BOM, max_fires=3).

AUDIT_ONLY. Fire 3/3 (last scheduled fire for this item). Reconfirms fire 1/2's
CLAIM_REFUTED, adds a NEW commercial-source-genuineness axis (silica/naphtha
cite only a government hazard-database page, not a named commercial supplier
-- self-declared by the sourcing corpus's own supplier_status field), with a
positive control targeted at that new axis and a discrimination control.
Records the still-standing cross-module ownership blocker and the genuine
external-data (supplier RFQ) need for the domestic-sourcing sub-piece. Filed
into evidence/phase0/repairs/CF-BOM/attempts/ (NOT done/ -- done_criteria are
still not met; the repair cannot land from this module's write scope).
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-cro-protocol-packager/evidence/audit/cf-bom-formulation-completeness-v3"
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
assert diag["step_b_positive_control"]["detected"] is True
assert diag["step_c_discrimination_control"]["discrimination_control_passed"] is True
harness_sha = sha((BENCH / "run_cf_bom_completeness_audit_v3.py").read_bytes())

# --- derive public key / key_id from on-host seed ---------------------------
eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"

trust = json.loads(TRUST.read_text())
trust_by_role = {k.get("role"): k for k in trust["keys"]}
eval_derives_pin = (eval_key_id == trust_by_role.get("PHASE0_EVALUATOR", {}).get("key_id"))

n_genuine = diag["step_d_new_axis_commercial_source_genuineness"]["n_lines_missing_genuine_commercial_source"]
lines_genuine = diag["step_d_new_axis_commercial_source_genuineness"]["lines_missing_genuine_commercial_source"]

# --- receipt body -----------------------------------------------------------
body_obj = {
    "schema": "amphora.cro-protocol-packager.cf-bom-formulation-completeness-audit-receipt.v3",
    "study_id": diag["study_id"],
    "authority": "AUDIT_ONLY",
    "module": "amphora-cro-protocol-packager",
    "campaign_item_id": "CF-BOM",
    "run_type": "falsification_attack",
    "fire_sequence": 3,
    "final_fire_for_item": True,
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
    "step_d_new_axis_commercial_source_genuineness": diag["step_d_new_axis_commercial_source_genuineness"],
    "step_b_positive_control": diag["step_b_positive_control"],
    "step_c_discrimination_control": diag["step_c_discrimination_control"],
    "envelope_conformance_spot_check": diag["envelope_conformance_spot_check"],
    "structural_finding": diag["structural_finding"],
    "reconfirms_prior_receipts": diag["reconfirms_prior_receipts"],
    "finding": (
        "CLAIM_REFUTED (fire 3/3, FINAL fire for this item): the CF-BOM "
        "deliverable remains byte-identical to the state fire 1 refuted "
        "(deliverable_unchanged_since_fire1="
        + str(diag["step_a_reconfirm"]["deliverable_unchanged_since_fire1"])
        + ", sourcing_corpus_unchanged_since_fire1="
        + str(diag["step_a_reconfirm"]["sourcing_corpus_unchanged_since_fire1"])
        + "); no repair has landed across 3 fires. This fire adds a NEW, "
        "previously-unrecorded refutation axis not checked by fire 1/2: "
        + str(n_genuine) + " of 12 BOM lines (" + ", ".join(lines_genuine) + ") "
        "cite ONLY a US government hazard-chemical database page (NOAA CAMEO) "
        "as their commercial source -- the sourcing corpus's own matched "
        "records self-declare supplier_status='chemical property source "
        "only; supplier not selected', i.e. the corpus itself admits no "
        "commercial entity has been named for silica and naphtha, unlike "
        "every other BOM line. This directly instantiates the refutation "
        "criterion's 'a candidate commercial source' clause. Positive "
        "control (planting the same defect pattern onto a currently-passing "
        "line, iron_oxide_black/SRC-LANXESS-BLACK-OXIDE) confirms the "
        "checker detects it (detected="
        + str(diag["step_b_positive_control"]["detected"])
        + "); a discrimination control (synthetic fully-repaired copy: "
        "concrete domestic determination + confirmed supplier_status + named "
        "commercial URL + explicit tier label on every line) confirms the "
        "SAME checker reports the per-line axes as NOT refuted on that "
        "repaired copy (discrimination_control_passed="
        + str(diag["step_c_discrimination_control"]["discrimination_control_passed"])
        + "), so the checker genuinely discriminates rather than being "
        "hard-wired. The prior 3 grounds (12/12 lines missing a flagged "
        "domestic-sourcing preference, 12/12 lines missing an explicit "
        "line-level evidence tier, 8/8 companion evidence files cited by "
        "blueprint prose absent anywhere in the repo) are reconfirmed "
        "unchanged. Envelope-conformance spot-check re-confirms all 9 "
        "ingredient classes stay inside the two-component epoxy-polyamide "
        "solvent-borne envelope (not a refuting axis)."
    ),
    "verdict": "CLAIM_REFUTED",
    "repair_status": "blocked",
    "campaign_item_status": "blocked",
    "campaign_item_disposition": (
        "This is fire 3/3 (max_fires reached) for CF-BOM. The item cannot "
        "reach done/ from a cro-protocol-packager-scoped fire alone: (1) "
        "blueprint.md is owned by amphora-report-packager and "
        "source_records.json by amphora-source-ledger, both outside this "
        "fire's write scope; (2) the domestic-sourcing/TAA/supplier-naming "
        "determinations specifically require real supplier RFQ responses -- "
        "blueprint.md Section 4 itself states 'Domestic/TAA status ... are "
        "to verify by supplier declaration/RFQ; they are not claimed here', "
        "and this cron's directive grants no procurement authority to "
        "obtain such declarations. Filed as a data-acquisition-queue entry "
        "(fire_id 20260810T200001-1412642-725b9f94d246). Forward progress "
        "requires either (a) a report-packager/source-ledger campaign fire "
        "(or an explicit cross-module scope exception) to populate per-line "
        "tiers, name real commercial suppliers for silica/naphtha, and "
        "create the 8 missing companion files, plus (b) real supplier RFQ "
        "responses for the domestic/TAA determinations -- after which a "
        "future cro-protocol-packager fire should re-run this v3 checker "
        "(script sha256 below) as the acceptance test."
    ),
    "does_not_close": (
        "This receipt does not repair the BOM deliverable. It reconfirms "
        "fire 1/2's refutation is still the truthful current state (inputs "
        "byte-identical), adds a new, independently-verified commercial-"
        "source-genuineness refutation axis with its own positive and "
        "discrimination controls, and records both the cross-module "
        "ownership blocker and the genuine external-data (RFQ) blocker "
        "preventing repair from landing within amphora-cro-protocol-"
        "packager's write scope this campaign."
    ),
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": sha(canon),
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "diagnostic_script_sha256": harness_sha,
    },
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

out = BENCH / "cf-bom-formulation-completeness-audit-receipt.v3.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

ATTEMPTS_DIR.mkdir(parents=True, exist_ok=True)
attempts_out = ATTEMPTS_DIR / "cf-bom-formulation-completeness-audit-receipt.v3.dsse.json"
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
