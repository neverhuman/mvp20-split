#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-run-provenance
anchor-necessity-reforge-resistance-v1 AUDIT_ONLY receipt.

AUDIT_ONLY: signs an audit receipt under evidence/audit/; does NOT sign a
phase0 evaluation/review, does NOT promote authority, does NOT flip
scientific_readiness, does NOT change the shipped Haber-Stornetta linear-chain
scheme or the pinned signature_status/promotion_receipt_eligible, does NOT
modify the portfolio manifest (66 receipts / 11 modules), the
module-manifest.json, any locked dataset, or a signed Phase-0 KPI. Derived
key_id cross-checked vs the pinned trust store."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / ("amphora-run-provenance/evidence/audit/"
                "anchor-necessity-reforge-resistance-v1")
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"


def sha(b): return hashlib.sha256(b).hexdigest()


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


canon = (BENCH / "diagnostic.canonical.json").read_bytes()
runB = (BENCH / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)
assert diag["gates"]["all_pass"], "diagnostic gates did not all pass"
oracle_sha = sha((BENCH / "anchor_necessity_oracle.py").read_bytes())
manifest_sha = sha((ROOT / "module-manifest.json").read_bytes())

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub = rev_sk.public_key().public_bytes_raw()
rev_pub_hex = rev_pub.hex()
rev_key_id = f"phase0-internal-reviewer-{sha(rev_pub)}"

eval_pin = rev_pin = False
if TRUST.exists():
    trust = json.loads(TRUST.read_text())
    tbr = {k.get("role"): k for k in trust.get("keys", [])}
    eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
    rev_pin = (rev_key_id == tbr.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))

c = diag["counts"]
r = diag["rates"]
body_obj = {
    "schema": "amphora.run-provenance.anchor-necessity-reforge-resistance-receipt.v1",
    "study_id": diag["study_id"],
    "authority": "AUDIT_ONLY",
    "run_type": diag["run_type"],
    "module": "amphora-run-provenance",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_module_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "changes_shipped_scheme": False,
    "runs_live_rust_runtime": False,
    "claim": diag["closes"],
    "purpose": diag["purpose"],
    "hypothesis": diag["hypothesis"],
    "non_circularity": diag["non_circularity"],
    "theory_reference": diag["theory_reference"],
    "runtime_source_anchors": diag["runtime_source_anchors"],
    "preconditions": diag["preconditions"],
    "honest_reference_run": diag["honest_reference_run"],
    "results": {
        "all_gates_passed": diag["gates"]["all_pass"],
        "gates": diag["gates"],
        "counts": c,
        "rates": r,
        "shipped_anchor_parity_checks_passed": c["g0_pass"],
        "shipped_anchor_parity_checks_total": c["g0_anchor_checks"],
        "single_mutation_probes_fail_closed": c["g1_fail_closed"],
        "single_mutation_probes_total": c["g1_single_mutation_probes"],
        "consistent_reforge_scenarios_total": c["g2_reforge_scenarios"],
        "consistent_reforge_detected_by_internal_verify":
            c["g2_detected_by_internal_verify"],
        "consistent_reforge_detected_by_external_root_anchor":
            c["g3_detected_by_external_root_anchor"],
        "consistent_reforge_detected_by_dsse_cold_key":
            c["g6_detected_cold_key_custody"],
        "consistent_reforge_detected_by_dsse_hot_key":
            c["g6_detected_hot_key_on_producing_host"],
        "single_anchor_field_coverage": diag["g4_single_anchor_field_coverage"],
        "complete_single_anchor_fields": diag["g4_complete_single_anchor_fields"],
        "localized_by_component_anchors": c["g5_localized_by_component_anchors"],
        "localized_by_root_anchor_only": c["g5_localized_by_root_anchor_only"],
        "reforge_scenario_ids": [x["scenario"]
                                for x in diag["g2_g5_consistent_reforge_probes"]],
        "dsse_attestation_payload_type":
            diag["g6_dsse_in_band_anchor"]["dsse_payload_type"],
        "dsse_honest_attestation_body_sha256":
            diag["g6_dsse_in_band_anchor"]["honest_attestation_body_sha256"],
        "dsse_honest_attestation_sig_sha256":
            diag["g6_dsse_in_band_anchor"]["honest_attestation_sig_sha256"],
    },
    "verdict": diag["verdict"],
    "closes": diag["closes"],
    "does_not_close": diag["does_not_close"],
    "phase1_requirement_derived": (
        "Phase-1 must (a) implement the controlled-key Ed25519 attestation over "
        "at minimum {run_id, root_hash} named in kpi.awaiting, AND (b) hold that "
        "key in custody OUTSIDE the host that writes the run archive, or evolve "
        "it per Kelsey-Schneier 1999 / Bellare-Yee 2003 forward integrity. "
        "Signing alone is measured here as necessary but NOT sufficient: with the "
        "key hot on the producing host, detection of all 8 consistent re-forges "
        "returns to 0/8. Optionally (c) publish or witness the root per "
        "Haber-Stornetta 1991 / Crosby-Wallach 2009 gossip, and (d) retain the "
        "four component hashes alongside the root if forensic LOCALIZATION (8/8 "
        "vs 0/8) is required and not merely accept/reject."),
    "provenance": {
        "module_manifest_sha256": manifest_sha,
        "oracle_sha256": oracle_sha,
        "sibling_parity_oracle_sha256":
            diag["runtime_source_anchors"]["sibling_parity_oracle_sha256"],
        "sibling_merkle_oracle_sha256":
            diag["runtime_source_anchors"]["sibling_merkle_oracle_sha256"],
        "shipped_kpi_sha256": diag["runtime_source_anchors"]["shipped_kpi_sha256"],
        "shipped_result_sha256":
            diag["runtime_source_anchors"]["shipped_result_sha256"],
        "shipped_bundle_sha256":
            diag["runtime_source_anchors"]["shipped_bundle_sha256"],
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "oracle_sha256": oracle_sha,
        "determinism_basis": ("no wall-clock, no RNG; Ed25519 signatures are "
                              "deterministic per RFC 8032; only RunArchiveError "
                              "variant names and booleans recorded, never "
                              "tempdir paths"),
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under evidence/audit/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin)},
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER", "key_id": rev_key_id,
        "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin),
        "reviewer_signature_present": False,
        "note": ("Reviewer key referenced for provenance only; no independent "
                 "human review performed.")},
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = ("application/vnd.amphora.run-provenance-"
         "anchor-necessity-reforge-resistance+json")
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(),
            "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id,
                            "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id,
           "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
out = BENCH / "anchor-necessity-reforge-resistance-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("two_replay_sha256", diag_sha)
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
