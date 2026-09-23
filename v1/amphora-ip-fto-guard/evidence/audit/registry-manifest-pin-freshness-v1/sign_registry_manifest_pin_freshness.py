#!/usr/bin/env python3
"""DSSE-Ed25519-sign the ip-fto-guard registry-manifest-pin-freshness
AUDIT_ONLY receipt.

AUDIT_ONLY: produces a signed audit receipt under evidence/audit/. Does NOT
sign a phase0 evaluation/review, does NOT promote authority, does NOT modify
the manifest, the registry succession chain/records/archive, or the pinned
patent_landscape.json fixture. No repair performed -- the claim SURVIVED, so
there is nothing to supersede.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
AUDIT_DIR = ROOT / "amphora-ip-fto-guard/evidence/audit/registry-manifest-pin-freshness-v1"
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
canon = (AUDIT_DIR / "diagnostic.canonical.json").read_bytes()
runB = (AUDIT_DIR / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag = json.loads(canon)
harness_sha = sha((AUDIT_DIR / "run_registry_manifest_pin_freshness.py").read_bytes())

assert diag["results"]["H0_verdict"] == "SURVIVED"

mutate_ctrl = json.loads((AUDIT_DIR / "diagnostic.mutate_control.json").read_bytes())
forge_ctrl = json.loads((AUDIT_DIR / "diagnostic.forge_control.json").read_bytes())
assert mutate_ctrl["results"]["H0_verdict"] == "REFUTED", "positive control A did not fire"
assert forge_ctrl["results"]["H0_verdict"] == "REFUTED", "positive control B did not fire"

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
    "schema": "amphora.ip-fto-guard.registry-manifest-pin-freshness-receipt.v1",
    "study_id": diag["study_id"],
    "authority": "AUDIT_ONLY",
    "run_type": "REGISTRY_MANIFEST_PIN_FRESHNESS_AUDIT",
    "module": "amphora-ip-fto-guard",
    "campaign_item_id": "",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_registry_succession_chain": False,
    "modifies_pinned_fixture": False,
    "claim_under_attack": diag["claim_under_attack"],
    "refutation_criterion": diag["refutation_criterion"],
    "inputs": diag["inputs"],
    "live_manifest_sha256": diag["live_manifest_sha256"],
    "pinned_hash": diag["pinned_hash"],
    "bundle_pinned_hash": diag["bundle_pinned_hash"],
    "pins_self_consistent": diag["pins_self_consistent"],
    "chain_constants_match_amphora_phase0_reviewer_hardcoded_values": diag[
        "chain_constants_match_amphora_phase0_reviewer_hardcoded_values"
    ],
    "pin_known_to_succession_chain": diag["pin_known_to_succession_chain"],
    "pin_archive_file_hash_matches_dirname": diag["pin_archive_file_hash_matches_dirname"],
    "checkA_entry_drift": diag["checkA_entry_drift"],
    "checkB_succession_edits_since_pin": diag["checkB_succession_edits_since_pin"],
    "results": diag["results"],
    "headline": (
        "SURVIVED, not a PIN-01/PIN-02-class defect: ip/claim-contract.v1.json's and "
        "evidence/phase0/bundle.v1.json's registry_manifest_hash pin (25b7b7f0...) is "
        "NOT byte-equal to the live root module-manifest.json (571813ee...), one "
        "registry succession behind HEAD -- but the amphora-ip-fto-guard manifest "
        "entry is byte-identical (canonical sha256 eb6c9b23...) across all 4 registry "
        "snapshots (genesis, first_head, the pinned snapshot, and live HEAD), and none "
        "of the 3 real succession records name amphora-ip-fto-guard in their edits. "
        "The pin correctly identifies the module's current manifest row in effect, "
        "matching amphora-phase0-reviewer's own verify_module_registry_succession "
        "semantics (a module's pin only needs to advance when a succession actually "
        "edits that module)."
    ),
    "positive_control": {
        "planted_defect": (
            "Two independent planted defects, each targeting one half of the "
            "refutation criterion: (A) mutated a COPY (never written to disk) of the "
            "live module-manifest.json's amphora-ip-fto-guard entry, flipping "
            "operational_readiness and readiness from 'GATED' to 'READY'; (B) forged a "
            "synthetic 4th succession record (record_sha256 all-f, not a real file) "
            "whose edits list names module_id='amphora-ip-fto-guard', appended in "
            "memory only to a copy of the succession chain."
        ),
        "how_planted": (
            "run_registry_manifest_pin_freshness.py --mutate-entry sets "
            "modules[project=amphora-ip-fto-guard].operational_readiness = "
            "modules[...].readiness = 'READY' on an in-memory deep copy of the live "
            "manifest object before computing live_entry_sha256; "
            "--forge-edit appends {predecessor_sha256: head, record_sha256: 'f'*64, "
            "successor_sha256: '9'*64, edits: [{module_id: amphora-ip-fto-guard, ...}]} "
            "to an in-memory copy of chain['records'] before walking "
            "edits_touching_module_between(). Neither control writes to any file on "
            "disk; both are captured separately in diagnostic.mutate_control.json and "
            "diagnostic.forge_control.json alongside the real (unmutated) "
            "diagnostic.canonical.json / diagnostic.runB.json two-replay pair."
        ),
        "detected": True,
        "evidence": (
            f"diagnostic.mutate_control.json: checkA_entry_drift.entries_identical=False, "
            f"pinned_snapshot_entry_sha256={mutate_ctrl['checkA_entry_drift']['pinned_snapshot_entry_sha256']} "
            f"!= live_head_entry_sha256={mutate_ctrl['checkA_entry_drift']['live_head_entry_sha256']}, "
            f"results.H0_verdict=REFUTED. "
            f"diagnostic.forge_control.json: checkB_succession_edits_since_pin."
            f"no_succession_edit_since_pin=False, records_touching_module_between_pin_and_head="
            f"{forge_ctrl['checkB_succession_edits_since_pin']['records_touching_module_between_pin_and_head']}, "
            f"results.H0_verdict=REFUTED. Both controls fired on the exact defect class "
            f"(part a: entry drift: 1fa95bf8... vs eb6c9b23...; part b: forged succession edit) "
            f"the refutation_criterion exists to catch; the real (unmutated) inputs did not "
            f"trigger either part, and the two-replay canonical/runB diagnostics for the real "
            f"inputs are byte-identical."
        ),
    },
    "does_not_close": diag["does_not_close"],
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": sha(canon),
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "harness_sha256": harness_sha,
        "mutate_control_diagnostic_sha256": sha((AUDIT_DIR / "diagnostic.mutate_control.json").read_bytes()),
        "forge_control_diagnostic_sha256": sha((AUDIT_DIR / "diagnostic.forge_control.json").read_bytes()),
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
ptype = "application/vnd.amphora.ip-fto-guard-registry-manifest-pin-freshness+json"
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

out = AUDIT_DIR / "registry-manifest-pin-freshness-receipt.v1.dsse.json"
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
