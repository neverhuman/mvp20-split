#!/usr/bin/env python3
"""DSSE-Ed25519-sign the ip-fto-guard pinned-source-hash-integrity AUDIT_ONLY receipt.

AUDIT_ONLY: produces a signed audit receipt under evidence/audit/. Does NOT
sign a phase0 evaluation/review, does NOT promote authority, does NOT modify
the manifest or any signed Phase-0 KPI. Documents and (in the same fire)
supersedes the module's stale docs/mission.md + docs/capability-profile.json
source-hash pins.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-ip-fto-guard/evidence/audit/pinned-source-hash-integrity-v1"
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
harness_sha = sha((BENCH / "run_pinned_hash_integrity.py").read_bytes())

# --- fixed post-fire fact: mission.md / capability-profile.json corrected --
FIXED_MISSION_SHA256 = sha((ROOT / "amphora-ip-fto-guard/docs/mission.md").read_bytes())
FIXED_CAP_PROFILE_SHA256 = sha((ROOT / "amphora-ip-fto-guard/docs/capability-profile.json").read_bytes())

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
    "schema": "amphora.ip-fto-guard.pinned-source-hash-integrity-receipt.v1",
    "study_id": diag["study_id"],
    "authority": "AUDIT_ONLY",
    "run_type": "PINNED_SOURCE_HASH_INTEGRITY_AUDIT",
    "module": "amphora-ip-fto-guard",
    "campaign_item_id": "",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_pinned_fixture": False,
    "claim_under_attack": (
        "docs/mission.md's and docs/capability-profile.json's checked-in "
        "SHA-256 pins for 'the live checked implementation' "
        "(amphora-assurance-capabilities/src/lib.rs, cited as c0b2540f...) "
        "and for the benchmark receipt (evidence/phase0/benchmark/"
        "result.v1.json, cited as bbd8a967...) currently identify the real "
        "files the compiled runtime built/emitted, so a reader can verify "
        "the module against them."
    ),
    "claim": diag["headline"],
    "purpose": diag["purpose"],
    "inputs": diag["inputs"],
    "live_hashes": diag["live_hashes"],
    "asserted_pins": diag["asserted_pins"],
    "consistency_checks": diag["consistency_checks"],
    "git_history": diag["git_history"],
    "behavior_scoping": diag["behavior_scoping"],
    "known_prior_acknowledgement": diag["known_prior_acknowledgement"],
    "results": {
        "H0": diag["H0"],
        "H0_verdict": diag["H0_verdict"],
        "mission_lib_pin_matches_live": diag["consistency_checks"]["mission_lib_pin_matches_live"],
        "capability_profile_lib_pin_matches_live": diag["consistency_checks"]["capability_profile_lib_pin_matches_live"],
        "mission_result_pin_matches_live": diag["consistency_checks"]["mission_result_pin_matches_live"],
        "mission_lib_pin_ever_matched_a_commit_in_full_git_history": diag["git_history"]["mission_lib_pin_ever_matched_a_commit"],
        "evaluate_ip_fto_guard_behavior_unaffected_by_the_drift": diag["behavior_scoping"]["fn_slice_byte_identical_across_full_tracked_history_and_live"],
    },
    "does_not_close": [
        "Does not modify or supersede the pinned patent_landscape.json fixture, the manifest, or any signed Phase-0 KPI.",
        "Does not touch config/module-evidence-inventory.json, which repeats the same stale c0b2540f... pin for amphora-ip-fto-guard AND for other modules sharing amphora-assurance-capabilities/src/lib.rs -- that file is outside this module's subtree and is flagged as an unresolved portfolio-wide followup, not fixed here.",
        "Does not establish legal FTO, patentability, or counsel review status.",
        "Does not re-verify unresolved_technical_categories semantics (see evidence/audit/kpi-recompute-consistency-v1, still open, unrelated to this receipt).",
    ],
    "repair_performed_this_fire": {
        "description": (
            "Closes the maintainer follow-up recorded 2026-08-03 in "
            "amphora-assurance-capabilities/evidence/phase0/kpis/"
            "RETRACTION-INDEX.md (R-B01 entry) and never actioned: "
            "docs/mission.md (2 lib.rs pin occurrences + 1 result.v1.json "
            "pin occurrence) and docs/capability-profile.json "
            "(evidence_inventory.implementation.sha256 + "
            "evidence_inventory.tests[0].sha256) corrected in place to the "
            "live, mechanically-verified current values. mission.md prose "
            "edits are collaborative/logged per this module's governance, "
            "not a protected file; front-matter (phase/readiness) was not "
            "touched."
        ),
        "mission_md_lib_rs_pin_before": "c0b2540fa84a9b8c98d2be5d82cbb1d21e9fd8b9806edad23815a0d912f4ab4d",
        "mission_md_lib_rs_pin_after": diag["live_hashes"]["lib_rs_sha256"],
        "mission_md_result_pin_before": "bbd8a9675d78bb65d1dfee9209b441bb5cb3ec4c28e2871cf8febf0f7168eec3",
        "mission_md_result_pin_after": diag["live_hashes"]["result_v1_json_sha256"],
        "capability_profile_lib_rs_pin_before": "c0b2540fa84a9b8c98d2be5d82cbb1d21e9fd8b9806edad23815a0d912f4ab4d",
        "capability_profile_lib_rs_pin_after": diag["live_hashes"]["lib_rs_sha256"],
        "mission_md_sha256_after_fix": FIXED_MISSION_SHA256,
        "capability_profile_json_sha256_after_fix": FIXED_CAP_PROFILE_SHA256,
        "note": (
            "Only the pin VALUES were corrected to match the real live "
            "files; no scientific readiness, phase, or gate status was "
            "changed, and evaluate_ip_fto_guard's own function body was "
            "independently confirmed byte-identical across the entire drift "
            "(behavior_scoping above), so this is a documentation-integrity "
            "fix, not a behavior change."
        ),
    },
    "followups_not_performed_this_fire": [
        {
            "defect": (
                "config/module-evidence-inventory.json (shared, outside "
                "amphora-ip-fto-guard/ subtree) repeats the same stale "
                "c0b2540f... pin for amphora-assurance-capabilities/src/"
                "lib.rs across multiple module entries, not just "
                "amphora-ip-fto-guard's."
            ),
            "proposed_done_criterion": (
                "A cron fire scoped to config/ (or a human) re-derives "
                "every module-evidence-inventory.json entry citing "
                "amphora-assurance-capabilities/src/lib.rs against the live "
                "file and corrects them; likely affects every module that "
                "shares this crate, not amphora-ip-fto-guard alone."
            ),
        }
    ],
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": sha(canon),
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "harness_sha256": harness_sha,
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under evidence/audit/",
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
ptype = "application/vnd.amphora.ip-fto-guard-pinned-source-hash-integrity+json"
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

out = BENCH / "pinned-source-hash-integrity-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

# --- self-verify ------------------------------------------------------------
pk = Ed25519PublicKey.from_public_bytes(eval_pub)
pk.verify(base64.standard_b64decode(envelope["signatures"][0]["sig"]),
          pae(ptype, base64.standard_b64decode(envelope["payload"])))

print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_derives_pin)
print("reviewer_derives_pinned_trust_key", rev_derives_pin)
print("receipt_body_sha256", sha(body))
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
print("H0_verdict", body_obj["results"]["H0_verdict"])
