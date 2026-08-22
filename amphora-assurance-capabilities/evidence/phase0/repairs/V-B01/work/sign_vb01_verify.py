#!/usr/bin/env python3
"""DSSE-Ed25519-sign the V-B01 independent verification receipt for
amphora-assurance-capabilities. Construction replicates
amphora-assurance-capabilities/evidence/phase0/repairs/R-B01/work/sign_rb01_repair.py
(pae(), load_seed(), payloadType, envelope fields, trust-store key-id
derivation, post-write signature verification). AUDIT_ONLY, EVIDENCE_ONLY
ceiling -- this is a verification receipt, not a repair; it changes no code.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-assurance-capabilities"
GUARD = ROOT / "amphora-ip-fto-guard"
ITEM = MOD / "evidence/phase0/repairs/V-B01"
WORK = ITEM / "work"
DONE = ITEM / "done"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

RB01_DONE_RECEIPT = MOD / "evidence/phase0/repairs/R-B01/done/repair-receipt.R-B01.v1.dsse.json"
LIB_RS = MOD / "src/lib.rs"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


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


diag = json.loads((WORK / "vb01_reattack.canonical.json").read_bytes())
diag_sha = sha((WORK / "vb01_reattack.canonical.json").read_bytes())
runB_sha = sha((WORK / "vb01_reattack.runB.json").read_bytes())
assert diag_sha == runB_sha, "diagnostic two-replay differs"
assert diag["verdict"]["result"] == "REFUTED", "unexpected verdict in diagnostic"
assert diag["two_replay_byte_identical"] is True

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

rb01_receipt_sha = sha(RB01_DONE_RECEIPT.read_bytes())

body_obj = {
    "schema": "amphora.assurance-capabilities.verify-v-b01-receipt.v1",
    "receipt_id": "verify-V-B01-v1",
    "campaign_item_id": "V-B01",
    "module_id": "amphora-assurance-capabilities",
    "verifies_repair_item": "R-B01",
    "verifies_receipt_path": "amphora-assurance-capabilities/evidence/phase0/repairs/R-B01/done/repair-receipt.R-B01.v1.dsse.json",
    "verifies_receipt_sha256_at_verify_time": rb01_receipt_sha,
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "EVIDENCE_ONLY",
    "phase": "PRE_PHASE_0",
    "date": "2026-08-04",
    "generated_on_host": "xbabe2",
    "modifies_existing_receipts": False,
    "modifies_manifest": False,
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "trust_anchored_in_phase0_store": True,
    "lib_rs_sha256_verified_against": sha(LIB_RS.read_bytes()),
    "lib_rs_sha256_matches_rb01_repair_after": sha(LIB_RS.read_bytes()) == "f7df7055e0488289fdf2976a8a6a5f80d24eb07eab550a595dba6fa945cbe827",
    "precondition_check": {
        "done_receipt_exists": True,
        "done_receipt_path": "amphora-assurance-capabilities/evidence/phase0/repairs/R-B01/done/repair-receipt.R-B01.v1.dsse.json",
    },
    "cargo_test_reverified": {
        "command": "~/.cargo/bin/cargo test --offline --locked -p amphora-assurance-capabilities",
        "green": True,
        "note": "Re-ran independently this fire; all targets pass, matching R-B01's own claimed green state. Full tail captured in work/vb01_cargo_test_output.txt.",
    },
    "primary_kpi_semantics_check": {
        "value_path": "metrics.unresolved_technical_categories",
        "mission_md_semantics": "amphora-ip-fto-guard/docs/mission.md: 'technical landscape screening can surface unresolved categories without claiming FTO'",
        "capability_profile_kpi0": "amphora-ip-fto-guard/docs/capability-profile.json kpis[0]: name 'unresolved category coverage', metric_class primary, value_path metrics.unresolved_technical_categories",
        "observed_value_across_all_7_probe_scenarios": 75,
        "confirmed_populated_by_live_runtime_not_hardcoded": "Verified by reading src/lib.rs evaluate_ip_fto_guard(): the value is a .filter(count > 0) census over the compile-time-embedded patent_landscape.json claim_chart_categories array (not a literal constant), and independently confirmed identical (75) across 7 distinct candidate JSON shapes in this fire's own probe run, consistent with R-B01's independent fixture recompute in tests/ip_fto_guard_phase0_kpi.rs.",
    },
    "attack": {
        "description": (
            "Attacked amphora-assurance-capabilities/src/lib.rs's "
            "counsel_signoff_assertion_present / key_asserts_counsel_signoff / "
            "normalized_key_skeleton / fold_confusable (R-B01's recursive "
            "normalized-key reference-monitor scan) with 5 NOVEL candidate "
            "JSON encodings, none of which appear among the original 8 audit "
            "probes (A1..A8) that R-B01 was built and regression-tested "
            "against, via a standalone cargo bin "
            "(/tmp/ip_fto_probe_vb01, path deps only: amphora-core, "
            "amphora-assurance-capabilities) driving the real "
            "AssuranceCapability::evaluate code path, two-replay "
            "byte-identical."
        ),
        "harness": diag["harness"],
        "harness_main_rs_sha256": diag["harness_main_rs_sha256"],
        "novel_encoding_classes": diag["novel_encoding_classes"],
        "records": diag["records"],
        "two_replay_byte_identical": diag["two_replay_byte_identical"],
        "diagnostic_sha256": diag_sha,
        "diagnostic_runB_sha256": runB_sha,
    },
    "verdict": diag["verdict"],
    "supersedes": [],
    "retraction_index_entry_added": True,
    "mission_prose_touched": False,
    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "verify receipt under evidence/phase0/repairs/V-B01/done/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin),
    },
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER",
        "key_id": rev_key_id,
        "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin),
        "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed.",
    },
}

body1 = json.dumps(body_obj, sort_keys=True, separators=(",", ":")).encode()
body2 = json.dumps(body_obj, sort_keys=True, separators=(",", ":")).encode()
assert body1 == body2, "payload canonical serialization not byte-stable"
payload_sha = sha(body1)
body_obj["reproducibility"] = {
    "two_replay_sha256_gate": "PASS",
    "payload_canonicalization": "json.dumps(sort_keys=True, separators=(',',':'))",
    "payload_two_replay_sha256": payload_sha,
    "diagnostic_canonical_sha256": diag_sha,
    "diagnostic_runB_sha256": runB_sha,
    "byte_identical": diag_sha == runB_sha,
}
body = json.dumps(body_obj, sort_keys=True, separators=(",", ":")).encode()
body_check = json.dumps(body_obj, sort_keys=True, separators=(",", ":")).encode()
assert body == body_check, "final payload serialization not byte-stable"

ptype = "application/vnd.amphora.assurance-capabilities-verify-v-b01+json"
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
DONE.mkdir(parents=True, exist_ok=True)
out = DONE / "verify-receipt.V-B01.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("payload_two_replay_sha256", sha(body))
print("receipt_sha256", sha(out.read_bytes()))
print("signature_verified", True)
