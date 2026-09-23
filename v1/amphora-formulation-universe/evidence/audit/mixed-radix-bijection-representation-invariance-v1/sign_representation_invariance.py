#!/usr/bin/env python3
"""DSSE-Ed25519-sign the mixed-radix-bijection-representation-invariance-v1
receipt for amphora-formulation-universe. AUDIT_ONLY. Does NOT promote
authority, does NOT flip scientific_readiness, does NOT modify the
manifest, KPI, fixture, mission.md, or the live Rust engine, and does NOT
edit the existing mixed-radix-bijection-v1 receipt (adds a new artifact
only).
"""
import base64
import hashlib
import json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-formulation-universe"
ITEM = MOD / "evidence/audit/mixed-radix-bijection-representation-invariance-v1"
ORACLE_DIR = MOD / "evidence/audit/mixed-radix-bijection-v1"
T06_DIR = MOD / "evidence/phase0/repairs/T-06"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

FIRE_ID = "20260818T230001-765727-bc65f9de39bd"


def sha(b):
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


canon = (ITEM / "diagnostic.canonical.json").read_bytes()
runB = (ITEM / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)
assert diag["accounting_output_equal_a_vs_b"] is True
assert diag["both_universes_individually_pass_oracle_acceptance"] is True
assert diag["representation_invariant_decode_a_vs_b"] is False
assert diag["representation_invariant_decode_a_vs_c_negative_control"] is True

harness_sha = sha((ITEM / "run_representation_invariance.py").read_bytes())
oracle_script_sha = sha((ORACLE_DIR / "run_mixed_radix_bijection.py").read_bytes())
oracle_receipt_sha = sha((ORACLE_DIR / "mixed-radix-bijection-receipt.v1.dsse.json").read_bytes())
t06_receipt_sha = sha((T06_DIR / "done/t06-independent-adversarial-attack-receipt.v1.dsse.json").read_bytes())
mission_sha = sha((MOD / "docs/mission.md").read_bytes())
lib_rs_sha = sha((ROOT / "amphora-formulation-capabilities/src/lib.rs").read_bytes())
kpi_sha = sha((MOD / "evidence/phase0/kpis/formulation-universe-cartesian-accounting-kpi.v1.json").read_bytes())

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))

body_obj = {
    "schema": "amphora.formulation-universe.mixed-radix-bijection-representation-invariance-receipt.v1",
    "study_id": "mixed-radix-bijection-representation-invariance-v1",
    "module": "amphora-formulation-universe",
    "authority": "AUDIT_ONLY",
    "campaign_item_id": "",
    "fire_id": FIRE_ID,
    "verdict": "CLAIM_REFUTED",
    "claim_under_attack": {
        "artifact_path": "amphora-formulation-universe/evidence/audit/mixed-radix-bijection-v1/mixed-radix-bijection-receipt.v1.dsse.json",
        "artifact_sha256_at_test_time": oracle_receipt_sha,
        "companion_source_path": "amphora-formulation-universe/evidence/audit/mixed-radix-bijection-v1/run_mixed_radix_bijection.py",
        "companion_source_sha256_at_test_time": oracle_script_sha,
        "claim_text": (
            "bijection_holds_all_universes: true; acceptance_all_perfect: "
            "true; README prose: 'this oracle proves the index<->tuple map "
            "is a BIJECTION between the integer index set [0, N) and the "
            "axis-tuple Cartesian product. A bijection is exactly loss-free "
            "(surjective => every combination reachable, no silent loss) "
            "and duplication-free (injective => no cell double-counted).' "
            "This receipt is cited approvingly in docs/mission.md's "
            "2026-08-06 Known Contradictions entry as 'the module's own "
            "documented mixed-radix unranking' -- i.e. treated as standing, "
            "trustworthy independent corroboration of the Cartesian-"
            "accounting no-silent-loss/no-silent-duplication claim."
        ),
        "distinguishing_note": (
            "T-06 (2026-08-06, CLAIM_REFUTED) attacked the LIVE RUST "
            "runtime directly and found the representation-order defect. "
            "kpi-claim-currency-v1 (2026-08-15, CLAIM_REFUTED) attacked "
            "whether the signed KPI register was updated to reflect T-06. "
            "doe-fixture-citation-fidelity-v1 (2026-08-17, CLAIM_REFUTED) "
            "attacked whether the DoE fixture's own textbook citations were "
            "faithful. None of the three examined whether the module's own "
            "SECOND standing artifact -- the independent mixed-radix-"
            "bijection-v1 theory oracle, whose entire stated purpose is to "
            "add assurance beyond the Rust benchmark by proving loss-"
            "freedom/duplication-freedom -- has any power to detect the "
            "exact defect class T-06 already proved live. This fire attacks "
            "that different, more specific target (a completeness claim "
            "about an audit tool, not the runtime itself) and is not a "
            "repeat of any of the three prior verdicts."
        ),
    },
    "attack_description": (
        "Reimplemented the mixed-radix-bijection-v1 oracle's own primitives "
        "(radices_and_values / place_weights / unrank / rank) byte-for-byte "
        "from its published source, then reproduced T-06's own "
        "index_laundering_out_of_universe_smuggling counterexample exactly: "
        "universe A axes={resin:[DGEBA,DGEBF], hardener:[IPDA,TETA]}, "
        "universe B axes={resin:[DGEBA,DGEBF], hardener:[TETA,IPDA]} "
        "(hardener value ORDER swapped, same set), infeasible_indices=[1] "
        "for both. Ran the oracle's own oracle_universe() acceptance "
        "metrics on A and B independently, decoded the declared infeasible "
        "index 1 to a physical value tuple under each using the oracle's "
        "own unrank+values-array logic, and added a negative control "
        "universe C (hardener order identical to A, unpermuted) to isolate "
        "the cause."
    ),
    "directive_ref": None,
    "refutation_criterion_verbatim": diag["refutation_criterion_verbatim"],
    "refutation_criterion_observation_occurred": True,
    "observed_result": {
        "accounting_output_equal_a_vs_b": diag["accounting_output_equal_a_vs_b"],
        "both_universes_individually_pass_oracle_acceptance": diag["both_universes_individually_pass_oracle_acceptance"],
        "decoded_tuple_for_declared_infeasible_index_1": diag["decoded_tuple_for_declared_infeasible_index_1"],
        "representation_invariant_decode_a_vs_b": diag["representation_invariant_decode_a_vs_b"],
        "representation_invariant_decode_a_vs_c_negative_control": diag["representation_invariant_decode_a_vs_c_negative_control"],
        "finding": diag["finding"],
    },
    "scope_and_limits": {
        "tested_artifact": (
            "the mixed-radix-bijection-v1 audit oracle's own published "
            "acceptance vocabulary and primitives, applied to a synthetic "
            "representation-order counterexample reproducing T-06 exactly; "
            "does NOT re-test the live Rust runtime directly (already "
            "covered by T-06) and does NOT claim the oracle's per-fixture "
            "results on the real 10-universe DoE fixture are wrong -- they "
            "are not, because none of those 10 fixture entries contain a "
            "reordered duplicate representation."
        ),
        "no_promotion": True, "no_manifest_edit": True, "no_kpi_edit": True,
        "no_mission_md_edit": True, "no_scientific_readiness_flip": True,
        "no_live_rust_engine_edit": True, "no_fixture_edit": True,
        "no_edit_to_mixed_radix_bijection_v1_receipt_or_script": True,
        "remediation_needed": (
            "Human/future-fire action: extend the mixed-radix-bijection-v1 "
            "oracle (or a successor) with a representation-invariance check "
            "-- for a set of accounting-equivalent axis-value orderings of "
            "the same declared universe, decode every declared infeasible "
            "index under each ordering and assert agreement -- OR fix the "
            "underlying Rust runtime (T-06's root cause: unranking is "
            "keyed to axis-value ARRAY POSITION, not to a stable value "
            "identity) so that no accounting-equivalent representation can "
            "exist in the first place. Until one of these lands, the "
            "mixed-radix-bijection-v1 receipt's loss-freedom/duplication-"
            "freedom claim should not be read as covering representation-"
            "order stability."
        ),
    },
    "provenance": {
        "harness_path": "amphora-formulation-universe/evidence/audit/mixed-radix-bijection-representation-invariance-v1/run_representation_invariance.py",
        "harness_sha256": harness_sha,
        "oracle_script_under_test_path": "amphora-formulation-universe/evidence/audit/mixed-radix-bijection-v1/run_mixed_radix_bijection.py",
        "oracle_script_under_test_sha256": oracle_script_sha,
        "oracle_receipt_under_test_path": "amphora-formulation-universe/evidence/audit/mixed-radix-bijection-v1/mixed-radix-bijection-receipt.v1.dsse.json",
        "oracle_receipt_under_test_sha256": oracle_receipt_sha,
        "t06_prior_finding_receipt_path": "amphora-formulation-universe/evidence/phase0/repairs/T-06/done/t06-independent-adversarial-attack-receipt.v1.dsse.json",
        "t06_prior_finding_receipt_sha256": t06_receipt_sha,
        "lib_rs_reference_path": "amphora-formulation-capabilities/src/lib.rs",
        "lib_rs_reference_sha256": lib_rs_sha,
        "mission_md_path": "amphora-formulation-universe/docs/mission.md",
        "mission_md_sha256": mission_sha,
        "kpi_json_path": "amphora-formulation-universe/evidence/phase0/kpis/formulation-universe-cartesian-accounting-kpi.v1.json",
        "kpi_json_sha256": kpi_sha,
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "replay_method": "two independent, back-to-back invocations of "
            "`python3 run_representation_invariance.py <out>` (deterministic, "
            "no I/O beyond hashing fixed in-tree source files); byte-"
            "identical canonical JSON confirmed via diff.",
        "seed": "n/a -- deterministic, no stochastic seed",
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY ad-hoc audit receipt under "
            "evidence/audit/mixed-radix-bijection-representation-invariance-v1/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin)},
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.formulation-universe-mixed-radix-bijection-representation-invariance+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payloadType": ptype, "payload": base64.standard_b64encode(body).decode(),
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "signature": envelope}

out = ITEM / "mixed-radix-bijection-representation-invariance-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

# self-verify
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("two_replay_sha256", diag_sha)
print("verdict", body_obj["verdict"])
print("receipt_sha256", sha(out.read_bytes()))
print("signature_verified", True)
