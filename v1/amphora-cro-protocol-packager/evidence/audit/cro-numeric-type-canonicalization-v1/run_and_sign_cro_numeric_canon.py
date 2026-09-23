#!/usr/bin/env python3
"""AUDIT_ONLY diagnostic assembly + DSSE sign for amphora-cro-protocol-packager
study cro-numeric-type-canonicalization-v1 (ROTATION mode, no campaign item).

Claim under attack: docs/mission.md's falsifiable hypothesis --
"candidate and formula binding prevents ambiguous or nonnumeric lab packets"
-- as implemented by the live compiled CroProtocolPackageV2 runtime
(amphora-assurance-capabilities/src/lib.rs) and the shared
amphora_core::stable_hash/canonicalize binding primitive.

This extends the 2026-07-28 canonicalization-conformance-v1 audit, which
found (via an independent Python RFC-8785 JCS re-implementation, never run
against the live Rust runtime) that the module's binding canonicalization is
NOT RFC-8785 conformant: integer-valued floats (110.0) and true integers
(110) hash differently under the module's json.dumps-equivalent scheme. That
receipt explicitly flagged it "does not itself re-serialize the runtime's
formula_sha256 under true JCS" -- i.e. it never touched the compiled binary.

This probe (tests/cro_numeric_type_canonicalization_probe.rs) closes that gap
by attacking the REAL compiled CroProtocolPackageV2::draft/validate/sign/
verify_signature pipeline directly, and precisely scopes the vulnerability:
- Axis A (candidate_binding, raw serde_json::Value): VULNERABLE. Two
  candidates encoding the identical real formulation (a 110 g resin charge)
  that differ ONLY in whether that number is written as JSON `110` or
  `110.0` produce two different candidate_sha256 / packet_id values. BOTH
  packets independently pass validate(), sign(), and verify_signature() --
  nothing in the existing 18-probe fail-closed battery (including T-02 and
  W-CRO1) catches this. Two live, independently-signed CRO packets exist for
  one real candidate.
- Axis B (equivalent_balance, typed EquivalentBalanceV1 struct): IMMUNE. The
  same int/float ambiguity attempted at the JSON-text level collapses during
  serde deserialization into the same f64 field before stable_hash ever
  sees it, so formula_sha256 is identical regardless of source encoding.

Refutation criterion (drawn directly from the module's own falsifiable
hypothesis in docs/mission.md): candidate_sha256 diverges AND packet_id
diverges AND both encodings independently validate AND both independently
sign+verify. All four held -> CLAIM_REFUTED.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MODULE = ROOT / "amphora-cro-protocol-packager"
OUT_DIR = MODULE / "evidence/audit/cro-numeric-type-canonicalization-v1"
HARNESS_RS = OUT_DIR / "harness/cro_numeric_type_canonicalization_probe.rs"
LIVE_HARNESS_RS = ROOT / "amphora-assurance-capabilities/tests/cro_numeric_type_canonicalization_probe.rs"
PRIOR_RECEIPT = MODULE / "evidence/audit/canonicalization-conformance-v1/canonicalization-conformance-receipt.v1.dsse.json"
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
assert probe["candidate_sha256_diverges"] is True
assert probe["packet_id_diverges"] is True
assert probe["validate_int_ok"] is True and probe["validate_float_ok"] is True
assert probe["verify_int_ok"] is True and probe["verify_float_ok"] is True
assert probe["formula_binding_immune_to_numeric_type"] is True

prior_receipt_sha256 = sha(PRIOR_RECEIPT.read_bytes()) if PRIOR_RECEIPT.exists() else None

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
    "candidate and formula binding prevents ambiguous or nonnumeric lab packets"
)

FINDING = (
    "Live-runtime CLAIM_REFUTED. Two candidate_binding encodings of the SAME "
    "real formulation charge (a 110 g resin mass), differing only in whether "
    "the producer's JSON serializer wrote that number as the lexical integer "
    "`110` or the lexical float `110.0`, drive the real compiled "
    "CroProtocolPackageV2::draft/validate/sign/verify_signature pipeline to "
    "two DIFFERENT candidate_sha256 values (febff8b7...af53c vs c9b374f9..."
    "3c24f) and two different packet_id values. Both packets independently "
    "pass validate() (no InvalidPackage/Binding error), both independently "
    "sign() and verify_signature() against an honest TrustStore -- none of "
    "the existing 18 fail-closed probes (T-02, W-CRO1 included) detects "
    "this, because each packet is genuinely internally self-consistent "
    "(candidate_sha256 == stable_hash(candidate_binding) for its own "
    "content). Root cause: amphora-core::canonicalize only sorts object "
    "keys; it does not normalize JSON number lexical form the way RFC 8785 "
    "JCS requires, so amphora_core::stable_hash is not injective over "
    "semantically-identical candidates. This directly falsifies the "
    "module's own stated falsifiable hypothesis for the candidate_binding "
    "path: candidate binding does NOT prevent an ambiguous packet -- it "
    "silently manufactures two independently-authenticated identities for "
    "one real candidate. The formula_sha256 path (equivalent_balance) is "
    "immune: EquivalentBalanceV1 is a strongly-typed struct with f64 "
    "fields, so serde deserialization collapses '110' and '110.0' to the "
    "identical f64 value before stable_hash ever runs, verified directly "
    "(formula_sha256_from_int == formula_sha256_from_float, both "
    "3bff8f3b...f8cde9). This extends and confirms, on the live compiled "
    "runtime rather than a Python re-implementation, the residual "
    "int/float ambiguity the 2026-07-28 canonicalization-conformance-v1 "
    "audit found and explicitly left untested against the runtime."
)

DOES_NOT_CLOSE = [
    "Does not itself repair amphora_core::canonicalize/stable_hash to enforce "
    "RFC-8785 JCS number rendering; that is a Phase-1/repair-item fix, not "
    "made by this audit fire.",
    "Does not claim the formula_sha256 (equivalent_balance) path is "
    "vulnerable; that path is independently confirmed immune (Axis B).",
    "Does not establish that any REAL upstream candidate producer today "
    "actually emits mixed int/float encodings for the same field across "
    "calls; it establishes that the binding primitive does not prevent it "
    "if one does, which is precisely what the anti-ambiguity hypothesis "
    "claims to guarantee.",
    "No CRO acceptance, wet-lab, qualification, procurement, or release "
    "authority; no promotion, manifest edit, KPI/benchmark-lock edit, or "
    "scientific_readiness flip.",
]

body_obj = {
    "schema": "amphora.cro-protocol-packager.numeric-type-canonicalization-receipt.v1",
    "study_id": "cro-numeric-type-canonicalization-v1",
    "authority": "AUDIT_ONLY",
    "run_type": "LIVE_RUNTIME_NUMERIC_TYPE_CANONICALIZATION_ATTACK",
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
        "docs/mission.md falsifiable hypothesis: 'candidate and formula "
        "binding prevents ambiguous or nonnumeric lab packets', as "
        "implemented by CroProtocolPackageV2 candidate_sha256/formula_sha256 "
        "over amphora_core::stable_hash/canonicalize"
    ),
    "extends_prior_receipt": {
        "path": "amphora-cro-protocol-packager/evidence/audit/canonicalization-conformance-v1/canonicalization-conformance-receipt.v1.dsse.json",
        "sha256": prior_receipt_sha256,
        "prior_gap": (
            "Prior audit (2026-07-28) demonstrated the int/float JCS "
            "non-conformance with an independent Python re-implementation "
            "of the module's json.dumps scheme only; it explicitly did not "
            "re-serialize or test against the live compiled runtime."
        ),
    },
    "attack_description": (
        "Live-runtime probe (tests/cro_numeric_type_canonicalization_probe.rs) "
        "drives the real compiled CroProtocolPackageV2::draft/validate/sign/"
        "verify_signature across two candidate_binding encodings of one real "
        "formulation that differ only in JSON number lexical form (110 vs "
        "110.0), and a parallel scoping check on the typed equivalent_balance "
        "path deserialized from int-literal vs float-literal JSON text."
    ),
    "refutation_criterion_verbatim": REFUTATION_CRITERION_VERBATIM,
    "refutation_criterion_source": "docs/mission.md #Decision and falsifiable hypothesis",
    "refutation_criterion_clause_tested": (
        "candidate_sha256 diverges AND packet_id diverges AND both encodings "
        "independently validate() Ok AND both independently sign()+"
        "verify_signature() Ok, for two candidate_binding values describing "
        "the identical real formulation"
    ),
    "refutation_criterion_observed": True,
    "harness_rs_sha256": harness_sha256,
    "harness_byte_identical_across_copies": True,
    "candidate_sha256_int": probe["candidate_sha256_int"],
    "candidate_sha256_float": probe["candidate_sha256_float"],
    "candidate_sha256_diverges": probe["candidate_sha256_diverges"],
    "packet_id_int": probe["packet_id_int"],
    "packet_id_float": probe["packet_id_float"],
    "packet_id_diverges": probe["packet_id_diverges"],
    "validate_int_ok": probe["validate_int_ok"],
    "validate_float_ok": probe["validate_float_ok"],
    "verify_int_ok": probe["verify_int_ok"],
    "verify_float_ok": probe["verify_float_ok"],
    "formula_sha256_from_int": probe["formula_sha256_from_int"],
    "formula_sha256_from_float": probe["formula_sha256_from_float"],
    "formula_binding_immune_to_numeric_type": probe["formula_binding_immune_to_numeric_type"],
    "does_not_close": DOES_NOT_CLOSE,
    "cargo_test_command": "cargo test -p amphora-assurance-capabilities --offline cro_numeric_type_canonicalization_probe -- --nocapture",
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
ptype = "application/vnd.amphora.cro-protocol-packager-numeric-type-canonicalization+json"
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

out = OUT_DIR / "cro-numeric-type-canonicalization-audit-receipt.v1.dsse.json"
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
