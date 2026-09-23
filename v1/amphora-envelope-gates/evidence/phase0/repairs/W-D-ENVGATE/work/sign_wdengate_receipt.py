#!/usr/bin/env python3
"""DSSE-Ed25519-sign the W-D-ENVGATE data-sourcing-sweep-and-rescore receipt
for amphora-envelope-gates. AUDIT_ONLY. Does NOT promote authority, does NOT
flip scientific_readiness, does NOT modify the manifest, KPI, or
benchmark-lock. This fire's done_criterion is NOT fully met (4 of 5 required
explicit-tolerance-band sources found), so this receipt is signed into
attempts/, not done/.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-envelope-gates"
ITEM = MOD / "evidence/phase0/repairs/W-D-ENVGATE"
WORK = ITEM / "work"
ATTEMPTS = ITEM / "attempts"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

FIRE_ID = "20260813T090002-1493988-0529734c83c6"


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

harness_sha = sha((WORK / "wdengate_diagnostic.py").read_bytes())
fixture_sha = sha((MOD / "reference/phase0-envelope-gates-known-answer.v1.json").read_bytes())
mission_sha = sha((MOD / "docs/mission.md").read_bytes())
oracle_sha = sha((MOD / "benchmarks/constraint-envelope-oracle-v1/run_envelope_gates.py").read_bytes())

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw(); eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))

body_obj = {
    "schema": "amphora.envelope-gates.w-d-envgate-data-sourcing-sweep-and-rescore-receipt.v1",
    "study_id": "W-D-ENVGATE-supplier-tds-sweep-and-rescore",
    "module": "amphora-envelope-gates",
    "authority": "AUDIT_ONLY",
    "campaign_item_id": "W-D-ENVGATE",
    "fire_id": FIRE_ID,
    "repair_status": "in_progress",
    "verdict": diag["verdict"],
    "claim_under_attack": diag["claim_under_attack"],
    "attack_description": (
        "Web-sourcing sweep of 12 named, queried candidate sources (supplier TDSs, a "
        "published open-access peer-reviewed formulation study, and a US federal coating "
        "specification family) for real, licence-quoted, published two-part epoxy-amine "
        "mix-ratio and tolerance-band data, followed by direct re-substitution of the real "
        "sourced values into the module's own self-authored known-answer fixture "
        "(reference/phase0-envelope-gates-known-answer.v1.json) and the module's own G3 "
        "tolerance-construction gate (benchmarks/constraint-envelope-oracle-v1/"
        "run_envelope_gates.py). Every named source carries its query string and its "
        "licence (or the blocking licence) quoted verbatim from the source itself."
    ),
    "sweep_summary": diag["sweep_summary"],
    "sources_swept": diag["sources_swept"],
    "mismatches_fixture_nominal_vs_real_supplier": diag["mismatches_fixture_nominal_vs_real_supplier"],
    "citation_not_found": diag["citation_not_found"],
    "internal_self_consistency_defects": diag["internal_self_consistency_defects"],
    "g3_rescore_against_real_external_tolerance_bands": diag["g3_rescore_against_real_external_tolerance_bands"],
    "verdict_basis": diag["verdict_basis"],
    "done_criterion_status": {
        "sources_swept_ge_12_each_with_query_and_license": True,
        "every_finding_filed_in_proposed_followups_with_module_defect_done_criterion": True,
        "ge_5_qualifying_sources_are_named_supplier_tds_or_formulation_guide_with_explicit_tolerance_band": False,
        "actual_count_of_explicit_tolerance_band_sources": diag["sweep_summary"]["n_explicit_mix_ratio_tolerance_band_sources_found"],
        "required_count": diag["sweep_summary"]["n_explicit_mix_ratio_tolerance_band_sources_required"],
        "four_fail_closed_gates_rescored_against_external_bands_reporting_disagreements": True,
        "overall_done_criterion_met": False,
        "reason_not_met": diag["sweep_summary"]["note_on_shortfall"],
    },
    "proposed_followups": diag["proposed_followups"],
    "scope_and_limits": {
        "tested_artifact": "the self-authored known-answer fixture "
                          "(reference/phase0-envelope-gates-known-answer.v1.json) and the "
                          "CPython AUDIT_ONLY oracle's G3 tolerance-construction gate "
                          "(benchmarks/constraint-envelope-oracle-v1/run_envelope_gates.py) "
                          "-- NOT the shipped Rust runtime "
                          "(amphora-formulation-capabilities). This receipt makes no claim "
                          "about the Rust runtime.",
        "no_acquisition": "no bulk download, cache, or scrape performed; only individual "
                          "public TDS PDFs were fetched and read for the specific numeric "
                          "facts quoted above, in the same manner the fixture's own citations "
                          "already reference facts from these same suppliers without "
                          "redistributing their documents.",
        "no_promotion": True, "no_manifest_edit": True, "no_kpi_edit": True,
        "no_scientific_readiness_flip": True,
    },
    "provenance": {
        "harness_path": "amphora-envelope-gates/evidence/phase0/repairs/W-D-ENVGATE/work/wdengate_diagnostic.py",
        "harness_sha256": harness_sha,
        "known_answer_fixture_sha256": fixture_sha,
        "oracle_examined_path": "amphora-envelope-gates/benchmarks/constraint-envelope-oracle-v1/run_envelope_gates.py",
        "oracle_examined_sha256": oracle_sha,
        "mission_md_sha256_at_attack_time": mission_sha,
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "replay_method": "independent full re-run of wdengate_diagnostic.py (no randomness, "
                         "no wall-clock reads, all source facts hardcoded from this fire's "
                         "web sweep)",
        "seed": "n/a -- deterministic arithmetic, no stochastic seed",
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY repair-item receipt under evidence/phase0/repairs/W-D-ENVGATE/attempts/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin)},
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.envelope-gates-w-d-envgate-sweep-rescore+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payloadType": ptype, "payload": base64.standard_b64encode(body).decode(),
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "signature": envelope}

ATTEMPTS.mkdir(parents=True, exist_ok=True)
out = ATTEMPTS / "w-d-envgate-sweep-rescore-attempt-1.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

# self-verify
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("two_replay_sha256", diag_sha)
print("verdict", diag["verdict"])
print("n_sources_swept", diag["sweep_summary"]["n_named_sources_swept"])
print("n_explicit_tolerance_band_sources", diag["sweep_summary"]["n_explicit_mix_ratio_tolerance_band_sources_found"])
print("receipt_sha256", sha(out.read_bytes()))
print("signature_verified", True)
