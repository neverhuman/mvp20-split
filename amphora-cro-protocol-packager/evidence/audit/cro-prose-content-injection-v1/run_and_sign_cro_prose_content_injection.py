#!/usr/bin/env python3
"""AUDIT_ONLY diagnostic assembly + DSSE sign for amphora-cro-protocol-packager
study cro-prose-content-injection-v1 (ROTATION mode, no campaign item).

Claim under attack: the Phase-0 KPI receipt
(evidence/phase0/kpis/cro-protocol-packager-signed-packet-kpi.v1.json)
capability docstring's universal guarantee -- "Grants no batch-release,
manufacturing-qualification, regulatory, safety, procurement, or optimizer
authority under any input" -- as implemented by the live compiled
CroProtocolPackageV2::draft/validate/sign/verify_signature pipeline
(amphora-assurance-capabilities/src/lib.rs) plus the KPI harness's own
authority_envelope_preservation_rate check (contains_banned_key,
amphora-assurance-capabilities/tests/cro_protocol_packager_phase0_kpi.rs).

Prior probes (T-02, W-CRO1, CF-PACKET, the KPI harness's own 18-probe
battery covering CRO_IDENTITY_HASH_SUBSTITUTION, INCOMPLETE_PROTOCOL_
SECTIONS, FALSE_CRO_EXECUTION, BANNED_CRO_PERFORMANCE_CLAIM, CRO_SIGNATURE_
DEFECT, CRO_PROSE_WAIVER) all attack the guarantee by (a) adding new
top-level JSON keys, rejected by #[serde(deny_unknown_fields)], or (b)
flipping a known boolean/enum/hash field. None of them ever write into the
packet's own free-text Vec<String> fields -- custody_requirements, controls,
required_outputs -- whose only validated property in validate() is
`.is_empty()`. This probe (tests/cro_prose_content_injection_probe.rs)
closes that gap: it rewrites custody_requirements[0], controls[0], and
required_outputs[0] with literal prose containing all six of the KPI
harness's own BANNED_AUTHORITY_KEYS phrases (batch_release,
release_authorized, qualified, authorized_by, manufacturing_qualification,
release_authority) plus an execution-approval and a quantitative
performance claim, recomputes packet_id (an unkeyed self-referential hash,
trivially recomputable by any packet constructor -- not an authenticity
barrier), and re-runs validate()/sign()/verify_signature() plus the KPI
harness's own contains_banned_key check (reimplemented byte-for-byte in the
probe) against the mutated packet.

Refutation criterion (drawn verbatim from the KPI capability docstring):
"Grants no batch-release, manufacturing-qualification, regulatory, safety,
procurement, or optimizer authority under any input." Refuted if the
mutated packet (a) ships all six banned authority phrases plus a
performance/execution claim in its own free-text fields, (b) independently
validate()s Ok, (c) independently sign()s and verify_signature()s Ok
against an honest TrustStore, and (d) the module's own
authority_envelope_preservation_rate check (contains_banned_key) does NOT
flag it -- i.e. the existing KPI metric would still observe 1.0 on this
packet despite the banned content.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MODULE = ROOT / "amphora-cro-protocol-packager"
OUT_DIR = MODULE / "evidence/audit/cro-prose-content-injection-v1"
HARNESS_RS = OUT_DIR / "harness/cro_prose_content_injection_probe.rs"
LIVE_HARNESS_RS = ROOT / "amphora-assurance-capabilities/tests/cro_prose_content_injection_probe.rs"
KPI_RECEIPT = MODULE / "evidence/phase0/kpis/cro-protocol-packager-signed-packet-kpi.v1.json"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"


def sha(b: bytes) -> str:
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


# --- harness copy must be byte-identical to the live crate test file -------
harness_sha256 = sha(HARNESS_RS.read_bytes())
live_harness_sha256 = sha(LIVE_HARNESS_RS.read_bytes())
assert harness_sha256 == live_harness_sha256, "harness copy drifted from live crate test"

# --- two-replay gate on the live-runtime probe capture ----------------------
run_a = (OUT_DIR / "probe_output_runA.json").read_bytes()
run_b = (OUT_DIR / "probe_output_runB.json").read_bytes()
assert run_a == run_b, "live-runtime probe not byte-stable across replays"
probe = json.loads(run_a)

assert probe["verdict"] == "CLAIM_REFUTED"
assert probe["refutation_criterion_observed"] is True
assert probe["all_banned_phrases_present"] is True
assert probe["validate_ok"] is True
assert probe["sign_ok"] is True and probe["verify_ok"] is True
assert probe["mutated_envelope_hit"] is None
assert probe["baseline_validate_ok"] is True and probe["baseline_envelope_hit"] is None

kpi_receipt_sha256 = sha(KPI_RECEIPT.read_bytes()) if KPI_RECEIPT.exists() else None

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

REFUTATION_CRITERION_VERBATIM = (
    "Grants no batch-release, manufacturing-qualification, regulatory, "
    "safety, procurement, or optimizer authority under any input"
)

FINDING = (
    "Live-runtime CLAIM_REFUTED. CroProtocolPackageV2::draft() hardcodes "
    "custody_requirements/controls/required_outputs to fixed literal "
    "strings and never exposes them as draft() parameters, but "
    "validate() only checks these three Vec<String> fields for "
    "`.is_empty()` -- it never inspects their string CONTENT. Rewriting "
    "custody_requirements[0], controls[0], and required_outputs[0] with "
    "prose carrying all six of the module's own KPI-harness "
    "BANNED_AUTHORITY_KEYS phrases (batch_release, release_authorized, "
    "qualified, authorized_by, manufacturing_qualification, "
    "release_authority) plus an 'EXECUTION AUTHORIZED'/'safety review "
    "CLEARED'/'97% pass'/'ranking score 9.8/10' claim, then recomputing "
    "packet_id (an unkeyed self-hash any constructor can trivially "
    "recompute -- not an authenticity check), produces a packet that "
    "independently validate()s Ok, sign()s and verify_signature()s Ok "
    "against an honest TrustStore. The module's OWN "
    "authority_envelope_preservation_rate check (contains_banned_key, "
    "cro_protocol_packager_phase0_kpi.rs) -- reimplemented byte-for-byte "
    "in this probe -- recurses into JSON object KEYS only, never into "
    "Value::String contents even inside a Value::Array, so it does not "
    "flag the mutated packet either: the existing KPI metric would "
    "still observe 1.0 on this exact packet. All structural claim "
    "surfaces remain lock-compliant throughout (schema, claim_locks all "
    "true, execution_authorized=false, authority_ceiling=AUDIT_ONLY, "
    "ranking_eligible=false, status unchanged) -- the packet passes "
    "every existing fail-closed probe axis while shipping, in its own "
    "signed and independently-verifiable bytes, plain-language batch-"
    "release/qualification/regulatory/safety/procurement/ranking "
    "authority claims the module's own KPI capability docstring says "
    "it grants 'under any input'. This is a genuine content-integrity "
    "gap distinct from the CRO_PROSE_WAIVER axis (which tests only "
    "rejection of NEW top-level JSON keys via deny_unknown_fields, not "
    "content within the three fields the schema already allows free "
    "text in) and distinct from the 2026-08-15 numeric-type-"
    "canonicalization finding (which concerns hash non-injectivity over "
    "candidate_binding, not free-text claim smuggling in the packet's "
    "own custody/controls/required_outputs)."
)

DOES_NOT_CLOSE = [
    "Does not itself add content-scanning to validate() or to the KPI "
    "harness's contains_banned_key; that is a Phase-1/repair-item fix, "
    "not made by this audit fire.",
    "Does not claim custody_requirements/controls/required_outputs are "
    "attacker-controlled through draft() itself -- draft() hardcodes "
    "them to fixed literals; the vulnerability is that nothing prevents "
    "a downstream mutator (or any future draft() variant/repair that "
    "parameterizes these fields) from injecting banned content and "
    "still passing validate()/sign()/verify_signature() and the KPI's "
    "own envelope check.",
    "Does not claim the candidate_sha256/formula_sha256 binding paths "
    "are affected; those are governed by the separate (already-REFUTED, "
    "unrepaired) 2026-08-15 numeric-type-canonicalization finding.",
    "No CRO acceptance, wet-lab, qualification, procurement, or release "
    "authority; no promotion, manifest edit, KPI/benchmark-lock edit, or "
    "scientific_readiness flip.",
]

body_obj = {
    "schema": "amphora.cro-protocol-packager.prose-content-injection-receipt.v1",
    "study_id": "cro-prose-content-injection-v1",
    "authority": "AUDIT_ONLY",
    "run_type": "LIVE_RUNTIME_PROSE_CONTENT_INJECTION_ATTACK",
    "module": "amphora-cro-protocol-packager",
    "campaign_item_id": "",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_pinned_fixture": False,
    "modifies_mission_front_matter": False,
    "modifies_mission_prose": False,
    "modifies_benchmark_lock": False,
    "modifies_locked_dataset": False,
    "claim_under_attack": (
        "evidence/phase0/kpis/cro-protocol-packager-signed-packet-kpi.v1.json "
        "capability docstring: 'Grants no batch-release, manufacturing-"
        "qualification, regulatory, safety, procurement, or optimizer "
        "authority under any input', as implemented by "
        "CroProtocolPackageV2::validate()/sign()/verify_signature() plus "
        "the KPI harness's authority_envelope_preservation_rate "
        "(contains_banned_key) check"
    ),
    "kpi_receipt_referenced": {
        "path": "amphora-cro-protocol-packager/evidence/phase0/kpis/cro-protocol-packager-signed-packet-kpi.v1.json",
        "sha256": kpi_receipt_sha256,
    },
    "attack_description": (
        "Live-runtime probe (tests/cro_prose_content_injection_probe.rs) "
        "drafts a real DGEBA/TETA marine-primer packet via "
        "CroProtocolPackageV2::draft(), then rewrites "
        "custody_requirements[0]/controls[0]/required_outputs[0] with "
        "prose containing all six BANNED_AUTHORITY_KEYS phrases plus an "
        "execution-approval and quantitative performance claim, "
        "recomputes packet_id (unkeyed self-hash), and re-runs "
        "validate()/sign()/verify_signature() plus a byte-for-byte "
        "reimplementation of the KPI harness's own contains_banned_key "
        "envelope check against the mutated packet."
    ),
    "refutation_criterion_verbatim": REFUTATION_CRITERION_VERBATIM,
    "refutation_criterion_source": "evidence/phase0/kpis/cro-protocol-packager-signed-packet-kpi.v1.json #capability",
    "refutation_criterion_clause_tested": (
        "mutated packet ships all 6 banned authority phrases plus a "
        "performance/execution claim in its own free-text fields AND "
        "independently validate()s Ok AND independently sign()s+"
        "verify_signature()s Ok AND the module's own "
        "authority_envelope_preservation_rate check (contains_banned_key) "
        "does not flag it"
    ),
    "refutation_criterion_observed": True,
    "harness_rs_sha256": harness_sha256,
    "harness_byte_identical_across_copies": True,
    "baseline_validate_ok": probe["baseline_validate_ok"],
    "baseline_envelope_hit": probe["baseline_envelope_hit"],
    "mutated_custody_requirements_0": probe["mutated_custody_requirements_0"],
    "mutated_controls_0": probe["mutated_controls_0"],
    "mutated_required_outputs_0": probe["mutated_required_outputs_0"],
    "banned_phrases_present": probe["banned_phrases_present"],
    "all_banned_phrases_present": probe["all_banned_phrases_present"],
    "packet_id_recomputed_after_mutation": probe["packet_id_recomputed_after_mutation"],
    "mutated_envelope_hit": probe["mutated_envelope_hit"],
    "validate_ok": probe["validate_ok"],
    "sign_ok": probe["sign_ok"],
    "verify_ok": probe["verify_ok"],
    "does_not_close": DOES_NOT_CLOSE,
    "cargo_test_command": "cargo test -p amphora-assurance-capabilities --offline cro_prose_content_injection_probe -- --nocapture",
    "cargo_test_green": True,
    "finding": FINDING,
    "verdict": probe["verdict"],
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": sha(run_a),
        "runB_diagnostic_sha256": sha(run_b),
        "byte_identical": run_a == run_b,
        "harness_rs_sha256": harness_sha256,
        "probe_stdout_runA_sha256": sha(run_a),
        "probe_stdout_runB_sha256": sha(run_b),
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
ptype = "application/vnd.amphora.cro-protocol-packager-prose-content-injection+json"
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

# --- also write the two diagnostic files this script itself asserts on -----
(OUT_DIR / "diagnostic.canonical.json").write_bytes(run_a)
(OUT_DIR / "diagnostic.runB.json").write_bytes(run_b)

out = OUT_DIR / "cro-prose-content-injection-audit-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

# --- self-verify -------------------------------------------------------------
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
print("verdict", probe["verdict"])
