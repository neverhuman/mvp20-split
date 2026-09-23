#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-cro-protocol-packager W-CRO1 protocol-lock
content-binding repair receipt (campaign item W-CRO1, repairing T-02 /
directive obligation T2-02).

Signs the byte-stable two-replay diagnostic with the on-host Phase-0
evaluator Ed25519 seed. AUDIT_ONLY: produces a signed audit receipt under
evidence/audit/ and a copy into evidence/phase0/repairs/W-CRO1/done/ (done_criterion
met: recompute-and-reject repair landed, T-02's exact evading vector re-run
REJECTED, 0 regressions on the other 34 probes, cargo test green in crate
and workspace). Does NOT sign a phase0 evaluation/review, does NOT promote
authority, does NOT modify the manifest or any signed Phase-0 KPI, does NOT
touch mission.md front matter (only prose was updated, separately, in this
same fire).
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-cro-protocol-packager/evidence/audit/w-cro1-protocol-lock-content-binding-repair-v1"
DONE_DIR = ROOT / "amphora-cro-protocol-packager/evidence/phase0/repairs/W-CRO1/done"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"
T02_DONE_RECEIPT = ROOT / "amphora-cro-protocol-packager/evidence/phase0/repairs/T-02/done/t02-claim-lock-execution-authority-adversarial-receipt.v1.dsse.json"


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
assert diag["repair_verified"] is True
assert diag["n_regressions"] == 0
assert diag["positive_control"]["detected"] is True
harness_sha = sha((BENCH / "run_w_cro1_protocol_lock_content_binding_repair.py").read_bytes())

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

# --- supersedes block (T-02's finding is not overturned -- it is REPAIRED; --
# --- T-02's own receipt is untouched, this is a NEW artifact that narrows  --
# --- what remains true about the module) ------------------------------------
t02_bytes = T02_DONE_RECEIPT.read_bytes()
supersedes = {
    "superseded_path": "amphora-cro-protocol-packager/evidence/phase0/repairs/T-02/done/t02-claim-lock-execution-authority-adversarial-receipt.v1.dsse.json",
    "superseded_sha256": sha(t02_bytes),
    "superseded_deleted_or_modified": False,
    "reason": (
        "T-02 found protocol_lock_sha256 was format-checked but not "
        "content-bound to locked_numeric_thresholds, so a packet-authored "
        "threshold was accepted end-to-end. This receipt supersedes T-02's "
        "'no repair yet' state by landing the content-binding fix in "
        "CroProtocolPackageV2::validate() and re-running T-02's own, "
        "byte-unmodified probe against the repaired runtime: the previously-"
        "accepted vector now fails closed, with 0 regressions on the other "
        "34 probes T-02 recorded. T-02's receipt itself is NOT deleted or "
        "edited -- it remains the correct historical record of the pre-repair "
        "runtime state."
    ),
}

# --- receipt body -----------------------------------------------------------
body_obj = {
    "schema": "amphora.cro-protocol-packager.w-cro1-protocol-lock-content-binding-repair-receipt.v1",
    "study_id": diag["study_id"],
    "authority": "AUDIT_ONLY",
    "run_type": diag["run_type"],
    "module": "amphora-cro-protocol-packager",
    "campaign_item_id": diag["campaign_item_id"],
    "repair_of": diag["repair_of"],
    "repair_status": "landed_and_verified",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_pinned_fixture": False,
    "modifies_mission_front_matter": False,
    "modifies_mission_prose": True,
    "supersedes": supersedes,
    "claim_under_attack": diag["claim_under_attack"],
    "directive_context": diag["directive_context"],
    "repair_description": diag["repair_description"],
    "acceptance_check": diag["acceptance_check"],
    "refutation_criterion_verbatim": diag["refutation_criterion_verbatim"],
    "refutation_criterion_observed_post_repair": diag["refutation_criterion_observed_post_repair"],
    "harness_rs_sha256": diag["harness_rs_sha256"],
    "t02_recorded_harness_rs_sha256": diag["t02_recorded_harness_rs_sha256"],
    "harness_byte_identical_to_t02": diag["harness_byte_identical_to_t02"],
    "regression_table": diag["regression_table"],
    "n_probes_compared": diag["n_probes_compared"],
    "n_regressions": diag["n_regressions"],
    "encoding_table_byte_identical_to_t02": diag["encoding_table_byte_identical_to_t02"],
    "evading_vector_pre_repair": diag["evading_vector_pre_repair"],
    "evading_vector_post_repair": diag["evading_vector_post_repair"],
    "repair_verified": diag["repair_verified"],
    "positive_control": diag["positive_control"],
    "theory_reference": diag["theory_reference"],
    "non_circularity": diag["non_circularity"],
    "does_not_close": diag["does_not_close"],
    "cargo_test_crate_green": diag["cargo_test_crate_green"],
    "cargo_test_workspace_green": diag["cargo_test_workspace_green"],
    "cargo_test_crate_command": diag["cargo_test_crate_command"],
    "cargo_test_workspace_command": diag["cargo_test_workspace_command"],
    "source_hashes": diag["source_hashes"],
    "pre_repair_lib_rs_sha256": diag["pre_repair_lib_rs_sha256"],
    "finding": (
        f"CLAIM_SURVIVED (repaired): T-02's exact evading vector (protocol_lock_sha256="
        f"'a'*64, content-undereived, locked_numeric_thresholds={{'attacker_pass_fail_yield_strength_min_mpa': 9999.0}}) "
        f"was re-run against the repaired CroProtocolPackageV2::validate() and is now "
        f"REJECTED: validate_ok={diag['evading_vector_post_repair']['validate_ok']}, "
        f"sign_ok={diag['evading_vector_post_repair']['sign_ok']}, "
        f"verify_signature_ok={diag['evading_vector_post_repair']['verify_signature_ok']}, "
        f"packet_authored_threshold_accepted={diag['evading_vector_post_repair']['packet_authored_threshold_accepted']} "
        f"(pre-repair, T-02 recorded: accepted="
        f"{diag['evading_vector_pre_repair']['packet_authored_threshold_accepted']}). "
        f"All other {diag['n_probes_compared'] - 1} probes (19 directive minus the "
        f"repaired one, plus the 16-row encoding table) are byte-identical to T-02's "
        f"recorded results: {diag['n_regressions']} regressions. protocol_lock_sha256 "
        f"is now required to equal computed_protocol_lock_sha256(), a SHA-256 over the "
        f"canonicalized locked_numeric_thresholds map -- a mismatch is rejected with "
        f"CroProtocolPackageError::Binding, which propagates through sign() and "
        f"verify_signature() (both call validate() first). cargo test is green in both "
        f"the amphora-assurance-capabilities crate and the full workspace."
    ),
    "verdict": diag["verdict"],
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": sha(canon),
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "diagnostic_script_sha256": harness_sha,
        "harness_rs_sha256": diag["harness_rs_sha256"],
        "probe_stdout_sha256": diag["probe_stdout_sha256"],
        "post_repair_probe_two_replay_byte_identical": diag["two_replay_byte_identical"],
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under evidence/audit/ and evidence/phase0/repairs/W-CRO1/done/",
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
ptype = "application/vnd.amphora.cro-protocol-packager-w-cro1-protocol-lock-content-binding-repair+json"
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

out = BENCH / "w-cro1-protocol-lock-content-binding-repair-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

DONE_DIR.mkdir(parents=True, exist_ok=True)
done_out = DONE_DIR / "w-cro1-protocol-lock-content-binding-repair-receipt.v1.dsse.json"
done_out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

# --- self-verify -------------------------------------------------------------
pk = Ed25519PublicKey.from_public_bytes(eval_pub)
pk.verify(base64.standard_b64decode(envelope["signatures"][0]["sig"]),
          pae(ptype, base64.standard_b64decode(envelope["payload"])))
pk.verify(base64.standard_b64decode(json.loads(done_out.read_text())["signature"]["signatures"][0]["sig"]),
          pae(ptype, base64.standard_b64decode(json.loads(done_out.read_text())["signature"]["payload"])))

print("WROTE", out)
print("WROTE", done_out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_derives_pin)
print("reviewer_derives_pinned_trust_key", rev_derives_pin)
print("receipt_body_sha256", sha(body))
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
