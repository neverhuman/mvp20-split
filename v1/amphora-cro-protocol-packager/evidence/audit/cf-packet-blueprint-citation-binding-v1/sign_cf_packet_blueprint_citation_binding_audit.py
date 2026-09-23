#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-cro-protocol-packager CF-PACKET
blueprint-citation-binding refutation receipt (campaign item CF-PACKET,
directive obligation CF-PACKET, AMPHORA-DIRECTIVE-2026-08-09).

Signs the byte-stable two-replay diagnostic with the on-host Phase-0
evaluator Ed25519 seed. AUDIT_ONLY: produces a signed audit receipt under
evidence/audit/ and a copy into evidence/phase0/repairs/CF-PACKET/attempts/
(done_criterion NOT met this fire -- REFUTED, so this is fire 1/2, repair
reserved for a later fire; per REPAIR-MODE rules the receipt does NOT land
in done/). Does NOT sign a phase0 evaluation/review, does NOT promote
authority, does NOT modify the manifest or any signed Phase-0 KPI, does NOT
touch mission.md front matter.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-cro-protocol-packager/evidence/audit/cf-packet-blueprint-citation-binding-v1"
ATTEMPTS_DIR = ROOT / "amphora-cro-protocol-packager/evidence/phase0/repairs/CF-PACKET/attempts"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
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
assert diag["refutation_criterion_observed"] is True
assert diag["t02_w_cro1_attack_shape_holds_no_regression"] is True
harness_sha = sha((BENCH / "run_cf_packet_blueprint_citation_binding_audit.py").read_bytes())

# --- derive public keys / key_ids from on-host seeds ------------------------
eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"

rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"

trust = json.loads(TRUST.read_text())
trust_by_role = {k.get("role"): k for k in trust["keys"]}
eval_derives_pin = (eval_key_id == trust_by_role.get("PHASE0_EVALUATOR", {}).get("key_id"))
rev_derives_pin = (rev_key_id == trust_by_role.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))

# --- receipt body -----------------------------------------------------------
body_obj = {
    "schema": "amphora.cro-protocol-packager.cf-packet-blueprint-citation-binding-receipt.v1",
    "study_id": diag["study_id"],
    "authority": "AUDIT_ONLY",
    "run_type": diag["run_type"],
    "module": "amphora-cro-protocol-packager",
    "campaign_item_id": diag["campaign_item_id"],
    "fire_number": "1_of_2",
    "repair_status": diag["repair_status"],
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
    "directive_context": diag["directive_context"],
    "attack_description": diag["attack_description"],
    "refutation_criterion_verbatim": diag["refutation_criterion_verbatim"],
    "refutation_criterion_source": diag["refutation_criterion_source"],
    "refutation_criterion_clause_tested": diag["refutation_criterion_clause_tested"],
    "refutation_criterion_observed": diag["refutation_criterion_observed"],
    "harness_rs_sha256": diag["harness_rs_sha256"],
    "harness_byte_identical_across_copies": diag["harness_byte_identical_across_copies"],
    "real_blueprint_path": diag["real_blueprint_path"],
    "real_blueprint_sha256": diag["real_blueprint_sha256"],
    "wrong_blueprint_citation_probe": diag["wrong_blueprint_citation_probe"],
    "no_blueprint_citation_probe": diag["no_blueprint_citation_probe"],
    "fabricated_threshold_values_probe": diag["fabricated_threshold_values_probe"],
    "t02_w_cro1_attack_shape_probes": diag["t02_w_cro1_attack_shape_probes"],
    "n_t02_shape_slipped_through": diag["n_t02_shape_slipped_through"],
    "t02_w_cro1_attack_shape_holds_no_regression": diag["t02_w_cro1_attack_shape_holds_no_regression"],
    "blueprint_content_binding_gap_confirmed": diag["blueprint_content_binding_gap_confirmed"],
    "does_not_close": diag["does_not_close"],
    "cargo_test_command": diag["cargo_test_command"],
    "cargo_test_green": diag["cargo_test_green"],
    "source_hashes": diag["source_hashes"],
    "finding": diag["finding"],
    "verdict": diag["verdict"],
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": sha(canon),
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "diagnostic_script_sha256": harness_sha,
        "harness_rs_sha256": diag["harness_rs_sha256"],
        "probe_stdout_runA_sha256": diag["probe_stdout_runA_sha256"],
        "probe_stdout_runB_sha256": diag["probe_stdout_runB_sha256"],
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under evidence/audit/ and evidence/phase0/repairs/CF-PACKET/attempts/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_derives_pin),
    },
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER",
        "key_id": rev_key_id,
        "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_derives_pin),
        "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed.",
    },
}

body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.cro-protocol-packager-cf-packet-blueprint-citation-binding+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {
    "payload": base64.standard_b64encode(body).decode(),
    "payloadType": ptype,
    "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}],
}

receipt = {
    "evaluator_key_id": eval_key_id,
    "evaluator_public_key_hex": eval_pub_hex,
    "reviewer_public_key_hex": rev_pub_hex,
    "signature": envelope,
}

out = BENCH / "cf-packet-blueprint-citation-binding-audit-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

ATTEMPTS_DIR.mkdir(parents=True, exist_ok=True)
attempts_out = ATTEMPTS_DIR / "cf-packet-blueprint-citation-binding-audit-receipt.v1.dsse.json"
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
print("reviewer_derives_pinned_trust_key", rev_derives_pin)
print("receipt_body_sha256", sha(body))
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
