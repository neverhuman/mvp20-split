#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-report-packager report-fixture-title-overclaim-v1
AUDIT_ONLY receipt. AUDIT_ONLY: signs an audit receipt under evidence/audit/;
does NOT sign a phase0 evaluation/review, does NOT promote authority, does NOT
flip scientific_readiness, does NOT modify the portfolio manifest (66 receipts
/ 11 modules), the module-manifest.json, any locked dataset, or a signed
Phase-0 KPI. Derived key_id cross-checked vs pinned trust store."""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-report-packager/evidence/audit/report-fixture-title-overclaim-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pae(t, body):
    return (
        b"DSSEv1 "
        + str(len(t)).encode()
        + b" "
        + t.encode()
        + b" "
        + str(len(body)).encode()
        + b" "
        + body
    )


def load_seed(p):
    raw = p.read_bytes().strip()
    if len(raw) == 64:
        try:
            return bytes.fromhex(raw.decode())
        except Exception:
            pass
    return raw[:32]


canon = (BENCH / "diagnostic.canonical.json").read_bytes()
runB = (BENCH / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)
oracle_sha = sha((BENCH / "oracle.py").read_bytes())
manifest_sha = sha((ROOT / "module-manifest.json").read_bytes())

assert diag["verdict"] == "CLAIM_REFUTED", "unexpected verdict; refusing to sign"
assert diag["calibration"]["calibration_pass"], "calibration failed; oracle not validated"
assert diag["runtime_source_anchors"][
    "runtime_unchanged_since_prior_live_validation"
], "diagnostics.rs drifted from the live-validated anchor; refusing to sign"
assert diag["attack"]["attack_refutes_claim"], "attack did not fire; refusing to sign"

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id")
rev_pin = rev_key_id == tbr.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id")

body_obj = {
    "schema": "amphora.report-packager.title-overclaim-attack-receipt.v1",
    "study_id": diag["study_id"],
    "authority": "AUDIT_ONLY",
    "module": "amphora-report-packager",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_module_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "claim_under_attack": diag["claim_under_attack"],
    "verdict": diag["verdict"],
    "summary": (
        "report_fixture_accepted() (amphora-assurance-capabilities/src/diagnostics.rs) "
        "runs contains_banned_claim() over payload.narrative ONLY; it never scans "
        "payload.title, though render_report() emits title verbatim as the document "
        "H1. A known-answer fixture with a clean narrative but a banned regulatory/"
        "qualification claim ('Product Qualified') in its title -- self-signed with a "
        "fresh, deterministic Ed25519 keypair reusing the ALREADY-DOCUMENTED unpinned-"
        "signing-key precondition from render-claim-lock-preservation-v1 G4 -- is "
        "returned ACCEPT, with a rendered_document whose first line is the overclaim "
        "itself. This refutes both (a) the live-runtime-diagnostic-parity-v1 receipt's "
        "standing claim that the control genuinely polices banned/overclaim content in "
        "a known-answer fixture, and (b) mission.md's red-team dossier requirement that "
        "regulatory/qualification/release overclaim must fail closed."
    ),
    "runtime_source_anchors": diag["runtime_source_anchors"],
    "calibration": diag["calibration"],
    "attack": {
        k: v for k, v in diag["attack"].items() if k != "hostile_fixture"
    },
    "hostile_fixture_full": diag["attack"]["hostile_fixture"],
    "prior_receipts_in_module": [
        "amphora-report-packager-banned-claim-lint-parity-v1 (claim TEXT lint over the 4 shipped deliverables, static)",
        "amphora-report-packager-gate-lattice-completeness-v1 (release DECISION algebra, static)",
        "amphora-report-packager-render-claim-lock-preservation-v1 (packaging MAP projection; G4 documented the unpinned self-derived signing-key gap this attack reuses, static)",
        "amphora-report-packager-live-runtime-diagnostic-parity-v1 (FIRST live Rust harness; the claim this receipt refutes, live)",
    ],
    "distinct_axis": (
        "FIFTH receipt for this module. Reuses the live-runtime-diagnostic-parity-v1 "
        "oracle UNMODIFIED (byte-identical fixture_accepted/render_report/"
        "contains_banned_claim re-derivation, itself already validated byte-exact "
        "against the live compiled runtime) and today re-confirms diagnostics.rs is "
        "STILL byte-identical to the anchor that receipt validated against -- then "
        "applies it to a NEW seventh fixture class outside the six the runtime's own "
        "compiled-in battery exercises. Composes with, and sharpens the consequence "
        "of, render-claim-lock-preservation-v1's unpinned-key finding: not just "
        "silent lock-stripping, but active injection of a live-recognized banned "
        "regulatory/qualification overclaim into an ACCEPTED known-answer rendered "
        "document."
    ),
    "provenance": {
        "module_manifest_sha256": manifest_sha,
        "oracle_sha256": oracle_sha,
        "oracle_path": "amphora-report-packager/evidence/audit/report-fixture-title-overclaim-v1/oracle.py",
        "fixture_sha256": diag["runtime_source_anchors"]["fixture_sha256"],
        "fixture_path": diag["runtime_source_anchors"]["fixture_path"],
        "assurance_diagnostics_rs_sha256": diag["runtime_source_anchors"][
            "assurance_diagnostics_rs_sha256_today"
        ],
        "assurance_diagnostics_rs_sha256_matches_live_validated_anchor": diag[
            "runtime_source_anchors"
        ]["runtime_unchanged_since_prior_live_validation"],
        "prior_receipt_referenced": (
            "amphora-report-packager/evidence/audit/live-runtime-diagnostic-parity-v1/"
            "live-runtime-diagnostic-parity-receipt.v1.dsse.json"
        ),
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "oracle_sha256": oracle_sha,
        "adversary_key_derivation": (
            "sha256(b'amphora-report-packager-title-overclaim-adversary-key-v1') "
            "used as a fixed Ed25519 seed -- deterministic so the two-replay byte "
            "gate holds; models a real-world coordinated adversary who would in "
            "practice generate a fresh random keypair, not evidence of any real "
            "compromised key"
        ),
    },
    "ceiling": (
        "This does not certify signed_report_package_present=true (that gate is "
        "hardcoded false pending the Phase-1 signing pipeline, independent of this "
        "finding). It does not claim the production banned_claim_lint_pass gate "
        "(also hardcoded false) is affected -- that gate is not wired to "
        "report_fixture_accepted at all. The fix (Phase-1 material, not applied by "
        "this AUDIT_ONLY receipt) is to also run contains_banned_claim() over "
        "payload.title inside report_fixture_accepted, and to pin the report-fixture "
        "verifying key as a trust anchor per render-claim-lock-preservation-v1's "
        "existing ask."
    ),
    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under evidence/audit/",
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
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.report-packager-title-overclaim-attack+json"
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
out = BENCH / "title-overclaim-attack-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])),
)
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("verdict", diag["verdict"])
print("two_replay_sha256", diag_sha)
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
