#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-report-packager campaign item T-12 (first
adversarial verdict: forged-upstream-receipt + directive T2-12 four-vector
attack) receipt. AUDIT_ONLY: does not promote authority, does not flip
scientific_readiness, does not modify the portfolio manifest, module-manifest.json,
any locked dataset, or a signed Phase-0 KPI."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
ITEM = ROOT / "amphora-report-packager/evidence/phase0/repairs/T-12"
WORK = ITEM / "work"
DONE = ITEM / "done"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

def sha(b): return hashlib.sha256(b).hexdigest()
def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " +
            str(len(body)).encode() + b" " + body)
def load_seed(p):
    raw = p.read_bytes().strip()
    if len(raw) == 64:
        try: return bytes.fromhex(raw.decode())
        except Exception: pass
    return raw[:32]

canon = (WORK / "diagnostic.canonical.json").read_bytes()
runB = (WORK / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)
oracle_sha = sha((WORK / "t12_forged_upstream_receipt_oracle.py").read_bytes())
manifest_sha = sha((ROOT / "module-manifest.json").read_bytes())

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw(); eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))

body_obj = {
    "schema": "amphora.report-packager.t12-forged-upstream-receipt-receipt.v1",
    "study_id": diag["study_id"],
    "authority": "AUDIT_ONLY",
    "run_type": diag["run_type"],
    "module": "amphora-report-packager",
    "campaign_item_id": "T-12",
    "promotes_authority": False, "flips_scientific_readiness": False,
    "human_review_performed": False, "organizational_independence_asserted": False,
    "modifies_manifest": False, "modifies_module_manifest": False,
    "modifies_locked_dataset": False, "modifies_signed_phase0_kpi": False,
    "claim_under_attack": {
        "receipt_path": "amphora-report-packager/docs/mission.md",
        "claim_text": (
            "amphora-report-packager has never received an adversarial verdict; "
            "its constructive SIGNED_RECEIPT-era receipts are untested claims."
        ),
    },
    "verdict": diag["verdict"],
    "refutation_criterion_verbatim": diag["refutation_criterion_verbatim"],
    "refutation_criterion_observation": diag["refutation_criterion_observation"],
    "directive_path": diag["directive_path"],
    "directive_sha256": diag["directive_sha256"],
    "directive_obligation": diag["directive_obligation"],
    "root_cause_finding": diag["root_cause_finding"],
    "corpus_manifest": diag["corpus_manifest"],
    "forged_package_classes": diag["forged_package_classes"],
    "directive_t2_12_four_vectors": diag["directive_t2_12_four_vectors"],
    "clauses_evaluated": diag["clauses_evaluated"],
    "runtime_source_anchors": diag["runtime_source_anchors"],
    "non_circularity": diag["non_circularity"],
    "theory_reference": diag["theory_reference"],
    "does_not_close": diag["does_not_close"],
    "done_criterion_met": {
        "forged_classes_fed_ge_3": True,
        "classes_fed": ["class1_mismatched_module_ids", "class2_replayed_receipt", "class3_non_anchored_key"],
        "packages_assembled_from_real_in_tree_artifacts": True,
        "corpus_manifest_listed": True,
        "slip_through_cases_quoted_verbatim": [
            diag["directive_t2_12_four_vectors"]["vector_c_encoding_trick_evasion"]["quoted_claim"],
            diag["directive_t2_12_four_vectors"]["vector_b_reintroduce_legacy_retracted_claim"]["quoted_claim"],
        ],
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "oracle_sha256": oracle_sha,
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY campaign-item receipt under evidence/phase0/repairs/T-12/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin)},
    "prior_receipts_in_module": [
        "amphora-report-packager-banned-claim-lint-parity-v1 (claim TEXT lint, single synthetic fixture)",
        "amphora-report-packager-gate-lattice-completeness-v1 (release DECISION function algebra)",
        "amphora-report-packager-render-claim-lock-preservation-v1 (packaging map + G4 unanchored-trust-base finding, lock-strip-only adversary)",
    ],
    "distinct_axis": (
        "FIRST receipt for this module logged to the falsification ledger. Unlike "
        "the three prior AUDIT_ONLY receipts (which mutated a single synthetic "
        "fixture in place and, in G4's case, only combined key-substitution WITH a "
        "stripped lock), this attack (a) assembles forged packages from REAL "
        "in-tree signed DSSE receipts drawn from the portfolio corpus, and (b) "
        "isolates the non-anchored-key substitution against an OTHERWISE-UNMODIFIED "
        "valid payload, proving the signature check alone provides no defense "
        "independent of the lock-set check, plus (c) is the first test of Unicode "
        "confusable-homoglyph banned-claim evasion and closed-list-reworded legacy "
        "claim evasion for this module."
    ),
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.report-packager-t12-forged-upstream-receipt+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "signature": envelope}
DONE.mkdir(parents=True, exist_ok=True)
out = DONE / "t12-forged-upstream-receipt-directive-t2-12.done-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("verdict", diag["verdict"])
print("two_replay_sha256", diag_sha)
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
