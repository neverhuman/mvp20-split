#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-cro-protocol-packager CF-BOM formulation-
completeness audit receipt (campaign item CF-BOM, founder directive
AMPHORA-DIRECTIVE-2026-08-09 S7, obligation CF-BOM).

AUDIT_ONLY. This is a falsification-first attack fire, not a repair: the
attack found the deliverable incomplete, so this receipt is CLAIM_REFUTED
and is filed into evidence/phase0/repairs/CF-BOM/attempts/ (NOT done/, since
done_criteria are not met). It does not modify the manifest, does not
promote authority, does not touch mission.md front matter.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-cro-protocol-packager/evidence/audit/cf-bom-formulation-completeness-v1"
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
harness_sha = sha((BENCH / "run_cf_bom_completeness_audit.py").read_bytes())

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
    "schema": "amphora.cro-protocol-packager.cf-bom-formulation-completeness-audit-receipt.v1",
    "study_id": diag["study_id"],
    "authority": "AUDIT_ONLY",
    "module": "amphora-cro-protocol-packager",
    "campaign_item_id": "CF-BOM",
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
    "deliverable_sha256": diag["deliverable_sha256"],
    "sourcing_corpus_under_test": diag["sourcing_corpus_under_test"],
    "sourcing_corpus_sha256": diag["sourcing_corpus_sha256"],
    "refutation_criterion_verbatim": diag["refutation_criterion_verbatim"],
    "refutation_criterion_observed": diag["refutation_criterion_observed"],
    "attack_shape_verbatim": diag["attack_shape_verbatim"],
    "n_bom_lines_parsed": diag["n_bom_lines_parsed"],
    "bom_line_findings": diag["bom_line_findings"],
    "n_lines_missing_domestic_sourcing_preference_flag": diag["n_lines_missing_domestic_sourcing_preference_flag"],
    "lines_missing_domestic_sourcing_preference_flag": diag["lines_missing_domestic_sourcing_preference_flag"],
    "n_lines_missing_line_level_evidence_tier": diag["n_lines_missing_line_level_evidence_tier"],
    "lines_missing_line_level_evidence_tier": diag["lines_missing_line_level_evidence_tier"],
    "companion_evidence_file_check": diag["companion_evidence_file_check"],
    "missing_companion_files_cited_by_blueprint": diag["missing_companion_files_cited_by_blueprint"],
    "envelope_conformance_spot_check": diag["envelope_conformance_spot_check"],
    "observation": diag["observation"],
    "finding": (
        f"CLAIM_REFUTED: of {diag['n_bom_lines_parsed']} BOM lines (both "
        f"Part A epoxy side and Part B polyamide-curative side of the Marine "
        f"Hull Primer candidate), all 12 lines pass the four base "
        f"done_criteria fields (function, target wt%, a commercial-source "
        f"citation URL, and a matched grade/spec sourcing record) but "
        f"{diag['n_lines_missing_domestic_sourcing_preference_flag']}/"
        f"{diag['n_bom_lines_parsed']} lines have NO domestic-sourcing "
        f"preference actually FLAGGED -- the matched sourcing record's "
        f"domestic_taa_status is 'unknown / RFQ required' for every single "
        f"ingredient, never a concrete determination, so the done_criteria "
        f"clause 'at least one candidate commercial source with the "
        f"domestic-sourcing preference flagged' is unmet across the entire "
        f"BOM. Separately, "
        f"{diag['n_lines_missing_line_level_evidence_tier']}/"
        f"{diag['n_bom_lines_parsed']} BOM lines carry no explicit "
        f"line-level evidence tier, and "
        f"{len(diag['missing_companion_files_cited_by_blueprint'])} "
        f"companion evidence files the blueprint prose cites by name for "
        f"its numeric claims do not exist anywhere in the repository "
        f"({', '.join(diag['missing_companion_files_cited_by_blueprint'])}). "
        f"Any one of these three gaps independently satisfies the "
        f"pre-committed refutation criterion; the domestic-sourcing-flag gap "
        f"is total (12/12) and schema-explicit (source_records.json declares "
        f"domestic_taa_status as a required_record_field but never "
        f"populates it with an actual preference for this formulation)."
    ),
    "verdict": "CLAIM_REFUTED",
    "campaign_item_status": "pending",
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": sha(canon),
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "diagnostic_script_sha256": harness_sha,
    },
    "does_not_close": (
        "This receipt does not itself repair the BOM deliverable; it "
        "documents the gap so a follow-on CF-BOM fire (or a human-run RFQ "
        "process) can add a concrete domestic/foreign sourcing "
        "determination and per-line evidence tiers to the blueprint's "
        "Section 1 table and its backing source_records.json entries."
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

out = BENCH / "cf-bom-formulation-completeness-audit-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

ATTEMPTS_DIR.mkdir(parents=True, exist_ok=True)
attempts_out = ATTEMPTS_DIR / "cf-bom-formulation-completeness-audit-receipt.v1.dsse.json"
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
