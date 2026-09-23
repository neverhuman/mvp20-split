#!/usr/bin/env python3
"""T-04 adversarial forgery case generator for amphora-evidence-intake-validator.

Performs REAL Ed25519 cryptographic operations (cryptography lib) to build a
REAL DSSE envelope for every case (payloadType/payload/signatures[]), plus the
11-field HOST_VERIFIED_RECEIPT_FEATURE object that the shipped predicate
(amphora-assurance-capabilities/src/lib.rs :: evaluate_evidence_intake,
host_receipt_valid) actually consumes.

A companion Rust test then, for EVERY case, calls BOTH:
  (1) amphora_core::verify_dsse(&envelope, &trust_store)  -- the REAL native
      DSSE/Ed25519 verification function that already exists in this exact
      crate (used by the sibling CroProtocolPackage capability a few hundred
      lines above evaluate_evidence_intake in the same lib.rs) -- ground
      truth, not a Python re-derivation.
  (2) AssuranceCapability::new("amphora-evidence-intake-validator").evaluate(..)
      with the (possibly forged) 11-field receipt -- the actual shipped
      decision.

The finding is the DIVERGENCE between (1) and (2) for the forgery cases: the
receipt asserts what (1) would have found had anyone bothered to call it, but
evaluate_evidence_intake never does.
"""
import base64, hashlib, json, os
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.exceptions import InvalidSignature

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-evidence-intake-validator"
ITEM = "T-04"
WORK = MOD / "evidence/phase0/repairs" / ITEM / "work"
TRUST_STORE_PATH = ROOT / "config/phase0-trust-store.v1.json"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
CROSS_MODULE_RECEIPT = ROOT / "amphora-design-rule-score/evidence/phase0/repairs/R-A11/done/R-A11.done-receipt.v1.dsse.json"

HOST_VERIFIED_RECEIPT_SCHEMA = "amphora.host-verified-evidence-receipt.v1"
PTYPE = "application/vnd.amphora.evidence-package+json"


def sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def canonicalize(v):
    if isinstance(v, dict):
        return {k: canonicalize(v[k]) for k in sorted(v.keys())}
    if isinstance(v, list):
        return [canonicalize(x) for x in v]
    return v


def canon_bytes(v) -> bytes:
    return json.dumps(canonicalize(v), separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def stable_hash(v) -> str:
    return sha256_hex(canon_bytes(v))


def pae(payload_type: str, body: bytes) -> bytes:
    t = payload_type.encode()
    return b"DSSEv1 " + str(len(t)).encode() + b" " + t + b" " + str(len(body)).encode() + b" " + body


def load_seed(p: Path) -> bytes:
    raw = p.read_bytes().strip()
    if len(raw) == 64:
        try:
            return bytes.fromhex(raw.decode())
        except Exception:
            pass
    return raw[:32]


def real_verify(pub, sig: bytes, payload_type: str, body: bytes) -> bool:
    try:
        pub.verify(sig, pae(payload_type, body))
        return True
    except (InvalidSignature, ValueError, Exception):
        return False


def evidence_candidate(cid: str, payload_extra: dict) -> dict:
    package = {"payload_kind": "lab_measurement", "payload_extra": payload_extra}
    return {"candidate_id": cid, "candidate_type": "evidence_package",
            "evidence_refs": {"evidence_package": package}}


def package_of(cand: dict) -> dict:
    return cand["evidence_refs"]["evidence_package"]


def contract_hash_v1(cand: dict) -> str:
    return stable_hash(cand)


def make_envelope(payload_type: str, payload_bytes: bytes, sig_rows):
    return {
        "payloadType": payload_type,
        "payload": base64.standard_b64encode(payload_bytes).decode(),
        "signatures": [{"keyid": kid, "sig": base64.standard_b64encode(sig).decode()} for kid, sig in sig_rows],
    }


def base_receipt(cand: dict, verifier_id: str, package_sha256_override=None) -> dict:
    return {
        "schema": HOST_VERIFIED_RECEIPT_SCHEMA,
        "accepted": True,
        "signature_verified": True,
        "revocation_checked": True,
        "fresh": True,
        "signature_algorithm": "Ed25519",
        "trust_store_status": "TRUSTED",
        "candidate_id": cand["candidate_id"],
        "candidate_contract_hash_v1": contract_hash_v1(cand),
        "package_sha256": package_sha256_override or stable_hash(package_of(cand)),
        "verifier_id": verifier_id,
    }


def main():
    WORK.mkdir(parents=True, exist_ok=True)
    trust_store = json.loads(TRUST_STORE_PATH.read_bytes())
    trust_by_id = {k["key_id"]: k for k in trust_store["keys"]}

    eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
    eval_pub = eval_sk.public_key()
    eval_pub_hex = eval_pub.public_bytes_raw().hex()
    eval_key_id = f"phase0-evaluator-{sha256_hex(eval_pub.public_bytes_raw())}"
    assert eval_key_id in trust_by_id and trust_by_id[eval_key_id]["revoked"] is False

    reviewer_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
    reviewer_pub = reviewer_sk.public_key()
    reviewer_pub_hex = reviewer_pub.public_bytes_raw().hex()
    reviewer_key_id = f"phase0-internal-reviewer-{sha256_hex(reviewer_pub.public_bytes_raw())}"
    assert reviewer_key_id in trust_by_id

    dev_sk = Ed25519PrivateKey.from_private_bytes(os.urandom(32))
    dev_pub = dev_sk.public_key()
    dev_pub_hex = dev_pub.public_bytes_raw().hex()
    dev_key_id = f"dev-unanchored-{sha256_hex(dev_pub.public_bytes_raw())}"
    assert dev_key_id not in trust_by_id

    revoked_sk = Ed25519PrivateKey.from_private_bytes(os.urandom(32))
    revoked_pub = revoked_sk.public_key()
    revoked_pub_hex = revoked_pub.public_bytes_raw().hex()
    revoked_key_id = f"test-revoked-{sha256_hex(revoked_pub.public_bytes_raw())}"

    cases = []

    def add_case(case_id, family, directive_category, description, candidate, envelope, receipt,
                 expect_dsse_verify_dsse_ok, expect_honest_world, extra=None):
        cases.append({
            "case_id": case_id, "family": family, "directive_category": directive_category,
            "description": description, "candidate": candidate, "envelope": envelope, "receipt": receipt,
            "expect_dsse_verify_dsse_ok": expect_dsse_verify_dsse_ok,
            "expect_honest_world": expect_honest_world, "extra": extra or {},
        })

    # ---------------- F1: re-signed-with-wrong-key / directive (a) ----------------
    cand1 = evidence_candidate("t04-f1-wrong-key", {"measurement": "gel_time_h", "value": 4.2})
    body1 = canon_bytes(package_of(cand1))
    sig1 = dev_sk.sign(pae(PTYPE, body1))
    env1 = make_envelope(PTYPE, body1, [(dev_key_id, sig1)])
    add_case("F1_resigned_wrong_key", "forgery", "a_non_anchored_dev_key",
              "DSSE envelope genuinely, correctly signed -- but by a freshly-generated, never-anchored dev "
              "Ed25519 key absent from config/phase0-trust-store.v1.json. The host receipt falsely asserts "
              "trust_store_status=TRUSTED / signature_verified=true anyway.",
              cand1, env1, base_receipt(cand1, verifier_id=dev_key_id),
              expect_dsse_verify_dsse_ok=False, expect_honest_world="REJECT (identity not trust-anchored)",
              extra={"signing_key_id": dev_key_id,
                     "real_signature_self_consistent": real_verify(dev_pub, sig1, PTYPE, body1)})

    # ---------------- F2: truncated-keyid ----------------
    cand2 = evidence_candidate("t04-f2-truncated-keyid", {"measurement": "dft_mil", "value": 3.1})
    body2 = canon_bytes(package_of(cand2))
    sig2 = eval_sk.sign(pae(PTYPE, body2))
    truncated_keyid = eval_key_id[:24]
    env2 = make_envelope(PTYPE, body2, [(truncated_keyid, sig2)])  # real sig, but filed under a truncated keyid
    add_case("F2_truncated_keyid", "forgery", None,
              "Real, genuinely valid Ed25519 signature bytes produced by the trust-anchored evaluator key, but "
              "filed in the envelope (and asserted as verifier_id) under a TRUNCATED key_id "
              "('phase0-evaluator-3ef6b3...' instead of the full 73-char id), which cannot exact-match any "
              "entry in config/phase0-trust-store.v1.json.",
              cand2, env2, base_receipt(cand2, verifier_id=truncated_keyid),
              expect_dsse_verify_dsse_ok=False, expect_honest_world="REJECT (identity unresolvable by exact-match lookup)",
              extra={"full_key_id": eval_key_id, "truncated_key_id": truncated_keyid})

    # ---------------- F3: payload/signature mismatch ----------------
    cand3_signed = evidence_candidate("t04-f3-payload-sig-mismatch", {"measurement": "pull_off_mpa", "value": 8.5})
    cand3_served = evidence_candidate("t04-f3-payload-sig-mismatch", {"measurement": "pull_off_mpa", "value": 99.9})
    body3_signed = canon_bytes(package_of(cand3_signed))
    body3_served = canon_bytes(package_of(cand3_served))
    sig3 = eval_sk.sign(pae(PTYPE, body3_signed))
    env3 = make_envelope(PTYPE, body3_served, [(eval_key_id, sig3)])  # payload swapped after signing; sig kept
    add_case("F3_payload_signature_mismatch", "forgery", None,
              "Ed25519 signature was computed over pull_off_mpa=8.5; the envelope's payload field was then "
              "swapped to pull_off_mpa=99.9 while keeping the original signature bytes. Trust-anchored keyid, "
              "well-formed envelope shape -- but the signature no longer matches the served payload.",
              cand3_served, env3, base_receipt(cand3_served, verifier_id=eval_key_id),
              expect_dsse_verify_dsse_ok=False, expect_honest_world="REJECT (signature does not verify against served payload)")

    # ---------------- F4: valid-envelope-but-tampered-payload (field smuggled in) ----------------
    cand4_signed = evidence_candidate("t04-f4-tampered-payload-smuggle", {"measurement": "adhesion_mpa", "value": 8.0})
    cand4_served = evidence_candidate("t04-f4-tampered-payload-smuggle",
                                       {"measurement": "adhesion_mpa", "value": 8.0,
                                        "release_authorized": True, "batch_qualified": True})
    body4_signed = canon_bytes(package_of(cand4_signed))
    body4_served = canon_bytes(package_of(cand4_served))
    sig4 = eval_sk.sign(pae(PTYPE, body4_signed))
    env4 = make_envelope(PTYPE, body4_served, [(eval_key_id, sig4)])
    add_case("F4_valid_envelope_tampered_payload", "forgery", None,
              "Structurally perfect DSSE envelope (valid payloadType, base64, signatures[], trust-anchored "
              "keyid) whose payload was tampered AFTER signing to smuggle in release_authorized/batch_qualified "
              "fields that were not present when the signature was produced.",
              cand4_served, env4, base_receipt(cand4_served, verifier_id=eval_key_id),
              expect_dsse_verify_dsse_ok=False, expect_honest_world="REJECT (signature does not verify against served/tampered payload)")

    # ---------------- F5: cross-module replay of trust standing ----------------
    other = json.loads(CROSS_MODULE_RECEIPT.read_bytes())
    other_env = other["signature"]
    other_keyid = other_env["signatures"][0]["keyid"]
    assert other_keyid == eval_key_id
    other_sig = base64.b64decode(other_env["signatures"][0]["sig"])
    other_ptype = other_env["payloadType"]
    cand5 = evidence_candidate("t04-f5-cross-module-replay", {"measurement": "gel_time_h", "value": 5.0})
    body5 = canon_bytes(package_of(cand5))
    env5 = make_envelope(other_ptype, body5, [(other_keyid, other_sig)])  # borrowed real sig, new bytes
    add_case("F5_cross_module_replay", "forgery", None,
              f"Borrows the real signature bytes of a genuinely trust-anchored identity ({other_keyid}) from a "
              f"DIFFERENT module's real, valid receipt ({CROSS_MODULE_RECEIPT.relative_to(ROOT)}) and attaches "
              "them to a brand-new candidate/payload in THIS module. candidate_id/candidate_contract_hash_v1/"
              "package_sha256 are correctly bound to the NEW candidate (naive whole-receipt replay is already "
              "blocked by those conjuncts); no signature was ever computed by that identity over these new bytes.",
              cand5, env5, base_receipt(cand5, verifier_id=other_keyid),
              expect_dsse_verify_dsse_ok=False, expect_honest_world="REJECT (borrowed signature does not verify against the new candidate's bytes)",
              extra={"borrowed_from": str(CROSS_MODULE_RECEIPT.relative_to(ROOT))})

    # ---------------- DIR_C: stale/revoked ----------------
    cand6 = evidence_candidate("t04-dirC-revoked-key", {"measurement": "gel_time_h", "value": 4.0})
    body6 = canon_bytes(package_of(cand6))
    sig6 = revoked_sk.sign(pae(PTYPE, body6))
    env6 = make_envelope(PTYPE, body6, [(revoked_key_id, sig6)])
    add_case("DIR_C_stale_revoked_key", "forgery", "c_stale_revoked",
              "Signature is genuinely, cryptographically valid under its own key, but that key's own registry "
              "entry is revoked=true (a local, test-only TrustStore fragment mirroring the real "
              "config/phase0-trust-store.v1.json schema's revoked field; the real config file is never touched "
              "or modified). The host receipt self-asserts trust_store_status=TRUSTED / revocation_checked=true "
              "regardless -- the shipped runtime has no revocation list or timestamp of its own to check.",
              cand6, env6, base_receipt(cand6, verifier_id=revoked_key_id),
              expect_dsse_verify_dsse_ok=False, expect_honest_world="REJECT (signing identity revoked)",
              extra={"revoked_key_id": revoked_key_id, "revoked_public_key_hex": revoked_pub_hex})

    # ---------------- DIR_D: rights-unresolved / quarantined ----------------
    cand7 = evidence_candidate("t04-dirD-rights-unresolved", {
        "measurement": "solubility_param", "value": 19.8,
        "rights_status": "USBR_RIGHTS_REVIEW_REQUIRED",
        "eligible_for_derivatives": False,
        "source_scope": "CONTEXT_ONLY_QUARANTINED",
    })
    body7 = canon_bytes(package_of(cand7))
    sig7 = eval_sk.sign(pae(PTYPE, body7))
    env7 = make_envelope(PTYPE, body7, [(eval_key_id, sig7)])
    add_case("DIR_D_rights_unresolved_quarantined", "forgery", "d_rights_unresolved_quarantined",
              "Evidence package embeds explicit rights-unresolved/quarantine markers using the portfolio's own "
              "real rights vocabulary (rights_status=USBR_RIGHTS_REVIEW_REQUIRED, eligible_for_derivatives=false, "
              "source_scope=CONTEXT_ONLY_QUARANTINED). Signature is HONESTLY valid and trust-anchored -- this is "
              "not a crypto forgery. The defect is structural: neither HOST_VERIFIED_RECEIPT_SCHEMA nor "
              "host_receipt_valid contains any rights/quarantine field or check (grep-confirmed).",
              cand7, env7, base_receipt(cand7, verifier_id=eval_key_id),
              expect_dsse_verify_dsse_ok=True, expect_honest_world="REJECT or HOLD pending rights review (no mechanism exists to do either)")

    # ---------------- POSCTRL_B: positive control / directive (b) hash-mismatch ----------------
    cand8 = evidence_candidate("t04-posctrl-hash-mismatch", {"measurement": "gel_time_h", "value": 4.2})
    body8 = canon_bytes(package_of(cand8))
    sig8 = eval_sk.sign(pae(PTYPE, body8))
    env8 = make_envelope(PTYPE, body8, [(eval_key_id, sig8)])
    wrong_blob = {"unrelated": "content", "not": "the real package"}
    planted_wrong_hash = stable_hash(wrong_blob)
    real_package_hash = stable_hash(package_of(cand8))
    assert planted_wrong_hash != real_package_hash
    add_case("POSCTRL_B_hash_mismatch_to_artifact", "positive_control", "b_hash_mismatched_to_artifact",
              "Genuinely honest, trust-anchored signature and a genuinely valid DSSE envelope; DELIBERATE "
              "planted defect purely on the hash-binding axis: the receipt's package_sha256 field is replaced "
              "with the hash of unrelated content instead of the real candidate package hash. The Rust runtime "
              "independently recomputes package_sha256 from the live candidate on every call, so this is "
              "expected to be REJECTED -- the positive control proving this one axis of the harness has real teeth.",
              cand8, env8, base_receipt(cand8, verifier_id=eval_key_id, package_sha256_override=planted_wrong_hash),
              expect_dsse_verify_dsse_ok=True, expect_honest_world="REJECT (hash-binding correctly enforced; this category must NOT be admitted)",
              extra={"planted_defect": "receipt.package_sha256 replaced with sha256 of an unrelated JSON blob instead of stable_hash(actual evidence_package)",
                     "how_planted": f"package_sha256 field set to {planted_wrong_hash} instead of the real value {real_package_hash}",
                     "real_package_sha256": real_package_hash, "planted_package_sha256": planted_wrong_hash})

    # ================= VALID-BUT-UNUSUAL (MUST ACCEPT) =================
    # U1: multiple independent real signatures on the same payload.
    candU1 = evidence_candidate("t04-u1-multi-signature", {"measurement": "gel_time_h", "value": 4.2})
    bodyU1 = canon_bytes(package_of(candU1))
    sigU1e = eval_sk.sign(pae(PTYPE, bodyU1))
    sigU1r = reviewer_sk.sign(pae(PTYPE, bodyU1))
    envU1 = make_envelope(PTYPE, bodyU1, [(eval_key_id, sigU1e), (reviewer_key_id, sigU1r)])
    add_case("U1_multiple_signatures", "valid_unusual", None,
              "Legal DSSE envelope with TWO independent real Ed25519 signatures (evaluator + internal-reviewer, "
              "both phase0-trust-store-anchored) over the same payload -- both verify independently.",
              candU1, envU1, base_receipt(candU1, verifier_id=eval_key_id),
              expect_dsse_verify_dsse_ok=True, expect_honest_world="ACCEPT (multi-signature is legal DSSE, not a defect)")

    # U2: unknown-but-well-formed payloadType.
    candU2 = evidence_candidate("t04-u2-unknown-payloadtype", {"measurement": "dft_mil", "value": 3.1})
    bodyU2 = canon_bytes(package_of(candU2))
    ptypeU2 = "application/vnd.amphora.t04-novel-unseen-schema-v7+json"
    sigU2 = eval_sk.sign(pae(ptypeU2, bodyU2))
    envU2 = make_envelope(ptypeU2, bodyU2, [(eval_key_id, sigU2)])
    add_case("U2_unknown_payload_type", "valid_unusual", None,
              f"Legal DSSE envelope with a novel, previously-unseen-in-repo but well-formed payloadType string "
              f"('{ptypeU2}'). Real Ed25519 verification is payloadType-agnostic.",
              candU2, envU2, base_receipt(candU2, verifier_id=eval_key_id),
              expect_dsse_verify_dsse_ok=True, expect_honest_world="ACCEPT (unknown payloadType is legal DSSE, not a defect)")

    # U3: nested envelope -- payload IS another complete, independently-signed DSSE envelope.
    inner_body = json.dumps({"nested": "attestation", "value": 1}).encode()
    inner_ptype = "application/vnd.amphora.inner-attestation+json"
    inner_sig = eval_sk.sign(pae(inner_ptype, inner_body))
    inner_envelope = make_envelope(inner_ptype, inner_body, [(eval_key_id, inner_sig)])
    candU3 = evidence_candidate("t04-u3-nested-envelope",
                                 {"measurement": "pull_off_mpa", "value": 8.5, "nested_envelope": inner_envelope})
    bodyU3 = canon_bytes(package_of(candU3))
    sigU3 = eval_sk.sign(pae(PTYPE, bodyU3))
    envU3 = make_envelope(PTYPE, bodyU3, [(eval_key_id, sigU3)])
    add_case("U3_nested_envelope", "valid_unusual", None,
              "Legal DSSE structure where a real, independently-signed and independently-verifiable DSSE "
              "envelope (in-toto/SLSA-style layered attestation) is embedded inside the outer evidence "
              "package's payload_extra. The inner envelope verifies on its own; outer verification does not "
              "require parsing the inner envelope's content.",
              candU3, envU3, base_receipt(candU3, verifier_id=eval_key_id),
              expect_dsse_verify_dsse_ok=True, expect_honest_world="ACCEPT (nested/layered envelopes are legal DSSE, not a defect)",
              extra={"inner_envelope_independently_verifies": real_verify(eval_pub, inner_sig, inner_ptype, inner_body)})

    # U4: large payload (~2MB of legitimate-shaped measurement records).
    large_records = [{"measurement": "gel_time_h", "replicate": i, "value": round(4.0 + (i % 50) * 0.01, 3)}
                      for i in range(30000)]
    candU4 = evidence_candidate("t04-u4-large-payload", {"measurement": "batch_series", "records": large_records})
    bodyU4 = canon_bytes(package_of(candU4))
    sigU4 = eval_sk.sign(pae(PTYPE, bodyU4))
    envU4 = make_envelope(PTYPE, bodyU4, [(eval_key_id, sigU4)])
    add_case("U4_large_payload", "valid_unusual", None,
              f"Legal DSSE envelope with a large payload ({len(bodyU4)} bytes, 30000 synthetic measurement "
              "records). Ed25519 signs the digest of an arbitrary-length message, so payload size does not "
              "affect verifiability.",
              candU4, envU4, base_receipt(candU4, verifier_id=eval_key_id),
              expect_dsse_verify_dsse_ok=True, expect_honest_world="ACCEPT (large payload is legal DSSE, not a defect)",
              extra={"payload_size_bytes": len(bodyU4)})

    out = {
        "schema": "amphora.evidence-intake-validator.t04-adversarial-forgery-cases.v1",
        "trust_store_sha256": sha256_hex(TRUST_STORE_PATH.read_bytes()),
        "evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
        "reviewer_key_id": reviewer_key_id, "reviewer_public_key_hex": reviewer_pub_hex,
        "keys_to_register_in_test_trust_store": [
            {"key_id": eval_key_id, "public_key_hex": eval_pub_hex, "revoke": False},
            {"key_id": reviewer_key_id, "public_key_hex": reviewer_pub_hex, "revoke": False},
            {"key_id": revoked_key_id, "public_key_hex": revoked_pub_hex, "revoke": True},
        ],
        "cases": cases,
    }
    (WORK / "t04_cases.json").write_text(json.dumps(out, indent=2, sort_keys=True))
    print("WROTE", WORK / "t04_cases.json", "n_cases=", len(cases))


if __name__ == "__main__":
    main()
