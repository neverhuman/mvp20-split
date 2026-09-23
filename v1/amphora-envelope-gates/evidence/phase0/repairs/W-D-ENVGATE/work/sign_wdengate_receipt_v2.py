#!/usr/bin/env python3
"""DSSE-Ed25519-sign the W-D-ENVGATE data-sourcing-sweep-and-rescore receipt,
FIRE 2, for amphora-envelope-gates. AUDIT_ONLY. Does NOT promote authority,
does NOT flip scientific_readiness, does NOT modify the manifest, KPI, or
benchmark-lock. This fire's done_criterion IS fully met (5 of 5 required
explicit-tolerance-band sources found; all 4 fail-closed gates re-scored),
so this receipt is signed into done/, extending (not correcting) the fire-1
attempt receipt, which is referenced by path+sha256 for provenance.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-envelope-gates"
ITEM = MOD / "evidence/phase0/repairs/W-D-ENVGATE"
WORK = ITEM / "work"
DONE = ITEM / "done"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

FIRE_ID = "20260813T100001-2022794-5c1bc9465c86"
PRIOR_ATTEMPT_PATH = "amphora-envelope-gates/evidence/phase0/repairs/W-D-ENVGATE/attempts/w-d-envgate-sweep-rescore-attempt-1.v1.dsse.json"


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


canon = (WORK / "diagnostic_v2.runA.json").read_bytes()
runB = (WORK / "diagnostic_v2.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)
assert diag["done_criterion_status"]["overall_done_criterion_met"] is True

harness_sha = sha((WORK / "wdengate_diagnostic_v2.py").read_bytes())
fixture_sha = sha((MOD / "reference/phase0-envelope-gates-known-answer.v1.json").read_bytes())
mission_sha = sha((MOD / "docs/mission.md").read_bytes())
oracle_sha = sha((MOD / "benchmarks/constraint-envelope-oracle-v1/run_envelope_gates.py").read_bytes())
prior_attempt_sha = sha((ROOT / PRIOR_ATTEMPT_PATH).read_bytes())

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw(); eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))

body_obj = {
    "schema": "amphora.envelope-gates.w-d-envgate-data-sourcing-sweep-and-rescore-receipt.v1",
    "study_id": "W-D-ENVGATE-supplier-tds-sweep-and-rescore-fire2",
    "module": "amphora-envelope-gates",
    "authority": "AUDIT_ONLY",
    "campaign_item_id": "W-D-ENVGATE",
    "fire_id": FIRE_ID,
    "fire_sequence": 2,
    "repair_status": "complete",
    "verdict": diag["verdict"],
    "claim_under_attack": diag["claim_under_attack"],
    "attack_description": (
        "Continuation of fire 1's web-sourcing sweep. Fire 1 found 12 named, queried "
        "candidate sources and 4 of the 5 required independent explicit two-part epoxy "
        "mix-ratio tolerance-band sources (all 4 from one manufacturer family, WEST SYSTEM / "
        "Gougeon Brothers). This fire located a 5th, independent source (Hexion EPIKOTE Resin "
        "L 20 / EPIKURE Curing Agent 960 technical data sheet, a boat-building epoxy laminating "
        "system, distinct corporate lineage from every source swept so far), meeting the "
        "done_criterion's >=5 floor, and extended the re-score from the module's G3 gate alone "
        "to all 4 fail-closed gates the oracle exposes (G2, G3, G4, G5), reporting a "
        "disagreement -- or an honest, reasoned not-re-scorable finding -- for each. Every "
        "named source across both fires carries its query string and its licence (or the "
        "blocking licence) quoted verbatim from the source itself."
    ),
    "prior_fire": {
        "fire_id": "20260813T090002-1493988-0529734c83c6",
        "attempt_receipt_path": PRIOR_ATTEMPT_PATH,
        "attempt_receipt_sha256": prior_attempt_sha,
        "relationship": "extends, does not correct or retract -- fire 1's receipt was an "
                        "honest 'in_progress' status (4/5 explicit-tolerance-band sources "
                        "found) filed to attempts/ per repair-mode rules; nothing in fire 1's "
                        "findings was wrong or is being superseded. This receipt is the "
                        "resumable item's next-fire continuation, now meeting the full "
                        "done_criterion, filed to done/.",
    },
    "sweep_summary": diag["sweep_summary"],
    "sources_swept": diag["sources_swept"],
    "mismatches_fixture_nominal_vs_real_supplier": diag["mismatches_fixture_nominal_vs_real_supplier"],
    "citation_not_found": diag["citation_not_found"],
    "internal_self_consistency_defects": diag["internal_self_consistency_defects"],
    "oracle_source_findings_new_this_fire": diag["oracle_source_findings_new_this_fire"],
    "four_fail_closed_gates_rescore": diag["four_fail_closed_gates_rescore"],
    "verdict_basis": diag["verdict_basis"],
    "done_criterion_status": diag["done_criterion_status"],
    "proposed_followups": diag["proposed_followups"],
    "scope_and_limits": {
        "tested_artifact": "the self-authored known-answer fixture "
                          "(reference/phase0-envelope-gates-known-answer.v1.json) and the "
                          "CPython AUDIT_ONLY oracle's G2/G3/G4/G5 gates "
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
        "harness_path": "amphora-envelope-gates/evidence/phase0/repairs/W-D-ENVGATE/work/wdengate_diagnostic_v2.py",
        "harness_sha256": harness_sha,
        "known_answer_fixture_sha256": fixture_sha,
        "oracle_examined_path": "amphora-envelope-gates/benchmarks/constraint-envelope-oracle-v1/run_envelope_gates.py",
        "oracle_examined_sha256": oracle_sha,
        "mission_md_sha256_at_attack_time": mission_sha,
        "prior_fire_diagnostic_sha256_consumed": diag["prior_fire_diagnostic_sha256"],
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "replay_method": "independent full re-run of wdengate_diagnostic_v2.py (no randomness, "
                         "no wall-clock reads, all source facts hardcoded from this fire's and "
                         "fire 1's web sweep)",
        "seed": "n/a -- deterministic arithmetic, no stochastic seed",
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY repair-item receipt under evidence/phase0/repairs/W-D-ENVGATE/done/",
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

DONE.mkdir(parents=True, exist_ok=True)
out = DONE / "w-d-envgate-sweep-rescore-done-1.v1.dsse.json"
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
print("done_criterion_met", diag["done_criterion_status"]["overall_done_criterion_met"])
print("receipt_sha256", sha(out.read_bytes()))
print("signature_verified", True)
