#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-cro-protocol-packager CF-TEST
pre-registration completeness audit receipt, fire 1/2 (campaign item
CF-TEST, founder directive AMPHORA-DIRECTIVE-2026-08-09 S7, obligation
CF-TEST, max_fires=2).

AUDIT_ONLY. Verdict CLAIM_REFUTED: axes A (methods/standards named on every
gate), B (kill criteria locked before measurement) and D (uncertainty
quantified) fail on the real, unmodified deliverable corpus; the literal
attack (delete a well-formed kill gate from a copy) confirms axis B's
absence is not theoretical -- nothing in this corpus detects the deletion.
Filed into evidence/phase0/repairs/CF-TEST/attempts/ (NOT done/ -- the
done_criterion is not met).
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-cro-protocol-packager/evidence/audit/cf-test-preregistration-completeness-v1"
ATTEMPTS_DIR = ROOT / "amphora-cro-protocol-packager/evidence/phase0/repairs/CF-TEST/attempts"
WORK_DIR = ROOT / "amphora-cro-protocol-packager/evidence/phase0/repairs/CF-TEST/work"
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
assert diag["refutation_criterion_observed"] is True
harness_sha = sha((BENCH / "run_cf_test_completeness_audit_v1.py").read_bytes())

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
    "schema": "amphora.cro-protocol-packager.cf-test-preregistration-completeness-audit-receipt.v1",
    "study_id": diag["study_id"],
    "authority": "AUDIT_ONLY",
    "module": "amphora-cro-protocol-packager",
    "campaign_item_id": "CF-TEST",
    "run_type": "falsification_attack",
    "fire_sequence": 1,
    "final_fire_for_item": False,
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
    "modifies_mission_prose": True,
    "claim_under_attack": diag["claim_under_attack"],
    "attack_shape_verbatim": diag["attack_shape_verbatim"],
    "refutation_criterion_verbatim": diag["refutation_criterion_verbatim"],
    "refutation_criterion_observed": diag["refutation_criterion_observed"],
    "deliverable_under_test": diag["deliverable_under_test"],
    "axis_results": diag["axis_results"],
    "failing_axes": diag["failing_axes"],
    "deletion_attack": diag["deletion_attack"],
    "finding": diag["finding"],
    "verdict": "CLAIM_REFUTED",
    "repair_status": "in_progress",
    "campaign_item_status": "pending",
    "campaign_item_disposition": (
        "Fire 1/2 for CF-TEST. Real, targeted refutation on 3 of 5 required "
        "axes (methods-named has 2/18 gates without a cited external "
        "standard; kill-criteria/acceptance-threshold locking has no "
        "content-hash mechanism at all for the bench-level gates, unlike "
        "the barrier rank's own locked_rank_hash; uncertainty is "
        "explicitly point-only per the corpus's own uncertainty_status "
        "field, with the one place a quantification would live -- "
        "out/power_analysis.json -- a dangling, nonexistent reference). "
        "Axes C (splits) and E (candidate binding + units) genuinely PASS. "
        "Repair for a future CF-TEST fire (max_fires=2): (1) add a named "
        "external standard citation to early_kill_gates.gel_or_phase_split "
        "and acceptance_gates.raw_data_return; (2) add a "
        "kill_gates_lock_hash / acceptance_gates_lock_hash field to "
        "capture_template.json computed the same way "
        "falsification_protocol.json computes locked_rank_hash (sha256 "
        "over the canonicalized gate set), verified by a check analogous "
        "to hash_matches; (3) either compute and check in an actual "
        "power_analysis.json artifact (sample-size/power calc backing the "
        "minimum_detectable_effect targets already stated) or honestly "
        "remove the dangling power_analysis_path reference and restate "
        "uncertainty_status without implying a quantification exists that "
        "does not."
    ),
    "does_not_close": (
        "This receipt does not repair the deliverable. It establishes the "
        "truthful current state: the pre-registered test plan and capture "
        "template are NOT complete against all 5 named axes of the "
        "done_criterion, with a positive, mechanically-demonstrated "
        "instance (the deletion attack) proving the locking gap is real, "
        "not hypothetical."
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
        "used_for": "AUDIT_ONLY audit receipt under evidence/audit/ and evidence/phase0/repairs/CF-TEST/attempts/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_derives_pin),
    },
}

body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.cro-protocol-packager-cf-test-preregistration-completeness-audit+json"
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

out = BENCH / "cf-test-preregistration-completeness-audit-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

ATTEMPTS_DIR.mkdir(parents=True, exist_ok=True)
attempts_out = ATTEMPTS_DIR / "cf-test-preregistration-completeness-audit-receipt.v1.dsse.json"
attempts_out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

WORK_DIR.mkdir(parents=True, exist_ok=True)
state = {
    "campaign_item_id": "CF-TEST",
    "last_fire_sequence": 1,
    "last_verdict": "CLAIM_REFUTED",
    "max_fires": 2,
    "failing_axes": diag["failing_axes"],
    "passing_axes": [a for a in ["axis_a", "axis_b", "axis_c", "axis_d", "axis_e"] if a not in diag["failing_axes"]],
    "next_fire_should": (
        "REPAIR MODE for fire 2/2: (1) add a named external standard to "
        "early_kill_gates.gel_or_phase_split and acceptance_gates."
        "raw_data_return in capture_template.json; (2) add a content-hash "
        "lock over early_kill_gates+acceptance_gates (mirror "
        "falsification_protocol.json's locked_rank_hash/"
        "hash_recomputed_from_locked_payload/hash_matches construction) "
        "and verify it in the same completeness checker "
        "(script sha256 below); (3) resolve the dangling "
        "out/power_analysis.json reference -- either produce a real power "
        "analysis artifact or remove the reference and restate "
        "uncertainty_status honestly. Then RE-RUN this exact checker "
        "(same script sha256, same command) as the acceptance test -- "
        "verdict = truthful CURRENT state, CLAIM_SURVIVED only if all 5 "
        "axes pass, else CLAIM_REFUTED with repair_status reflecting "
        "partial progress. Do NOT repeat this fire's byte-identical "
        "reconfirm with no new information."
    ),
    "harness_script_sha256": harness_sha,
    "deliverable_shas_at_this_fire": diag["deliverable_under_test"],
    "mission_md_capture_template_hash_pin_stale": diag["deletion_attack"]["mission_md_hash_matches_actual_on_disk_file"] is False,
}
(WORK_DIR / "STATE.json").write_text(json.dumps(state, indent=2, sort_keys=True))

# --- self-verify -------------------------------------------------------------
pk = Ed25519PublicKey.from_public_bytes(eval_pub)
pk.verify(base64.standard_b64decode(envelope["signatures"][0]["sig"]),
          pae(ptype, base64.standard_b64decode(envelope["payload"])))
pk.verify(base64.standard_b64decode(json.loads(attempts_out.read_text())["signature"]["signatures"][0]["sig"]),
          pae(ptype, base64.standard_b64decode(json.loads(attempts_out.read_text())["signature"]["payload"])))

print("WROTE", out)
print("WROTE", attempts_out)
print("WROTE", WORK_DIR / "STATE.json")
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_derives_pin)
print("receipt_body_sha256", sha(body))
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
