#!/usr/bin/env python3
"""DSSE-Ed25519-sign the W-T-EIV DSSE-spec-conformance done receipt for
amphora-evidence-intake-validator. AUDIT_ONLY; does not modify the master
manifest, any locked dataset, the shipped Phase-0 KPI, or the runtime."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-evidence-intake-validator"
ITEM = "W-T-EIV"
WORK = MOD / "evidence/phase0/repairs" / ITEM / "work"
DONE = MOD / "evidence/phase0/repairs" / ITEM / "done"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
SHIPPED_KPI = MOD / "evidence/phase0/kpis/evidence-intake-validator-host-receipt-integrity-kpi.v1.json"
T04_RECEIPT = MOD / "evidence/phase0/repairs/T-04/done/t04-adversarial-forgery-done.v1.dsse.json"
LIB_RS = ROOT / "amphora-assurance-capabilities/src/lib.rs"
CRYPTO_RS = ROOT / "amphora-core/src/crypto.rs"
MISSION = MOD / "docs/mission.md"


def sha(b): return hashlib.sha256(b).hexdigest()


def pae(t, body):
    tb = t.encode()
    return (b"DSSEv1 " + str(len(tb)).encode() + b" " + tb + b" " +
            str(len(body)).encode() + b" " + body)


def load_seed(p):
    raw = p.read_bytes().strip()
    if len(raw) == 64:
        try:
            return bytes.fromhex(raw.decode())
        except Exception:
            pass
    return raw[:32]


canon = (WORK / "diagnostic.canonical.json").read_bytes()
runB = (WORK / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag = json.loads(canon)
diag_sha = sha(canon)
assert diag["summary"]["n_requirements"] >= 8, "fewer than 8 requirements enumerated"

harness_sha = sha((WORK / "run_dsse_spec_conformance.py").read_bytes())
shipped_kpi_sha = sha(SHIPPED_KPI.read_bytes())
t04_sha = sha(T04_RECEIPT.read_bytes())
lib_rs_sha = sha(LIB_RS.read_bytes())
crypto_rs_sha = sha(CRYPTO_RS.read_bytes())
mission_sha = sha(MISSION.read_bytes())

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"

divergent_reqs = [r for r in diag["requirements"] if r["verdict"] == "divergent"]
na_reqs = [r for r in diag["requirements"] if r["verdict"] == "not_applicable"]

proposed_followups = []
for r in divergent_reqs:
    if r["id"] in ("R1-envelope-schema", "R2-payload-field", "R4-sig-required", "R5-signatures-array-multisig"):
        repair = (
            "Either (a) re-scope the module's documentation/KPI theory line to stop "
            "implying DSSE-envelope conformance for this receipt schema and name it "
            "as a distinct, non-DSSE 'pre-verified attestation record' format, or "
            "(b) change HOST_VERIFIED_RECEIPT_FEATURE to literally carry a "
            "DsseEnvelope{payload, payloadType, signatures[]} (amphora-core::crypto) "
            "and have host_receipt_valid call amphora_core::verify_dsse on it."
        )
    elif r["id"] == "R6-pae-construction":
        repair = (
            "If host_receipt_valid is to make any cryptographic claim, it must "
            "compute or receive proof of a PAE(payloadType, body) computation; "
            "acceptance criterion: grep of the evidence-intake code region for "
            "'DSSEv1' or a local pae()/imported amphora_core::crypto::pae usage "
            "returns True."
        )
    elif r["id"] == "R7-verifier-must-decode-and-verify":
        repair = (
            "host_receipt_valid must call amphora_core::verify_dsse (already "
            "imported in this file and already used by the sibling "
            "CroProtocolPackage capability at line 320) instead of trusting "
            "receipt['signature_verified']==true; acceptance criterion: re-run "
            "T-04's 12-case forgery corpus and require 0/12 forged envelopes "
            "admitted (T-04 measured 7/12 admitted under the current code)."
        )
    elif r["id"] == "R9-threshold-counts-verified-signatures":
        repair = (
            "trust_store_status must be derived from an in-module TrustStore "
            "lookup against config/phase0-trust-store.v1.json (as verify_dsse "
            "already does for the sibling capability), not from a caller-"
            "supplied string; acceptance criterion: re-run V1-REAL-EIV's n=66 "
            "real-manifest corpus and report a non-vacuous trust decision "
            "(today 0/66 pass and 0/66 fail for a reason other than 'no anchor "
            "for any real signer exists in-tree')."
        )
    elif r["id"] == "R11-conformant-implementation-exists-unused":
        repair = (
            "Wire evaluate_evidence_intake to call the already-imported "
            "amphora_core::sign_dsse/verify_dsse (used at lib.rs:299,320) "
            "instead of maintaining a second, non-conformant, hand-rolled "
            "receipt schema; acceptance criterion: HOST_VERIFIED_RECEIPT_FEATURE "
            "value is type-checked as a DsseEnvelope, not a serde_json::Value "
            "with ad hoc field checks."
        )
    else:
        repair = "Re-scope documentation to state this divergence explicitly, or implement the missing DSSE construction."
    proposed_followups.append({
        "requirement_id": r["id"],
        "spec_citation": r["spec_citation"],
        "finding": r["evidence"],
        "proposed_repair_criterion": repair,
    })

body_obj = {
    "schema": "amphora.evidence-intake-validator.dsse-spec-conformance-done-receipt.v1",
    "receipt_id": "w-t-eiv-dsse-spec-conformance",
    "module_id": "amphora-evidence-intake-validator",
    "campaign_item_id": "W-T-EIV",
    "directive_ref": None,
    "directive_path": "none",
    "directive_sha256": "",
    "directive_obligation": None,
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "EVIDENCE_ONLY",
    "phase": "PRE_PHASE_0",
    "scientific_success_required_for_phase0": False,
    "date": "2026-08-13",
    "generated_on_host": "xbabe2",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_shipped_runtime": False,
    "modifies_existing_receipts": False,

    "claim_under_attack": diag["claim_under_attack"],

    "baseline": {
        **diag["baseline"],
        "doi_or_url": diag["baseline"]["repo_url"],
        "citation": (
            "secure-systems-lab, \"Dead Simple Signing Envelope (DSSE)\" "
            "specification, Version 1.0.2 (2024-05-10), "
            "https://github.com/secure-systems-lab/dsse "
            "(envelope.md + protocol.md). This is the same DSSE construction "
            "already cited transitively by this module's own shipped KPI "
            "theory line via in-toto Attestation Framework v1.0 (2020) and "
            "SLSA v1.0 (2023), and the construction amphora_core::sign_dsse / "
            "amphora_core::verify_dsse (amphora-core/src/crypto.rs, sha256 "
            f"{crypto_rs_sha}) implement and the sibling CroProtocolPackage "
            "capability in the same source file already uses (T-04, "
            "2026-08-05)."
        ),
    },

    "claim": (
        "THEORY-DIMENSION VERDICT: measured against the DSSE specification "
        "(secure-systems-lab/dsse, v1.0.2, 2024-05-10) for the first time, "
        "the claim 'the validator conforms to the published DSSE "
        "specification, and any divergence is deliberate and stated' is "
        "REFUTED on both halves. CONFORMANCE HALF: of 11 DSSE normative "
        f"requirements enumerated spanning the envelope JSON schema "
        "(payload/payloadType/signatures, keyid optionality, sig "
        "requirement, multi-signature array support) and the PAE "
        "(Pre-Authentication Encoding) construction and verification "
        "procedure, the LIVE authority under test "
        "(amphora-assurance-capabilities/src/lib.rs :: "
        "evaluate_evidence_intake, host_receipt_valid, sha256 "
        f"{lib_rs_sha}) scores "
        f"{diag['summary']['n_conformant']}/11 conformant, "
        f"{diag['summary']['n_divergent']}/11 divergent, and "
        f"{diag['summary']['n_not_applicable']}/11 not-applicable. Zero "
        "requirements are met. The live predicate validates an 11-field "
        "flat, self-asserted JSON object (schema, accepted, "
        "signature_verified, revocation_checked, fresh, "
        "signature_algorithm, trust_store_status, candidate_id, "
        "candidate_contract_hash_v1, package_sha256, verifier_id) that is "
        "structurally incompatible with the DSSE envelope schema: it "
        "carries no payload, no payloadType, no signatures array, and the "
        "predicate performs zero PAE computation and zero calls to any "
        "signature/trust-store/revocation primitive of its own -- it checks "
        "boolean-and-string equality against values the CALLER'S "
        "FeatureSnapshot supplies. A structurally conformant DSSE "
        "implementation (DsseEnvelope{payload_type, payload, signatures}, a "
        "matching PAE builder, and verify_dsse performing real per-signature "
        f"Ed25519 verification) already exists in this repo "
        f"(amphora-core/src/crypto.rs, sha256 {crypto_rs_sha}) and is "
        "already invoked by the sibling CroProtocolPackage capability in "
        "the SAME source file (lib.rs:299 sign_dsse, lib.rs:320 "
        "verify_dsse) -- it is simply never called from "
        "evaluate_evidence_intake/host_receipt_valid. This corroborates, "
        "and gives a spec-named structural cause for, T-04's prior "
        "behavioral finding (2026-08-05, CLAIM_REFUTED: 7/12 forged-DSSE "
        "cases admitted by this predicate while amphora_core::verify_dsse "
        "correctly rejected the same forgeries). DISCLOSURE HALF: this "
        "module's checked-in docs (mission.md, capability-profile.json, the "
        "shipped KPI) never name the DSSE envelope schema or the PAE "
        "construction as a specification this predicate's receipt format "
        "was measured against or deliberately diverges from; the word "
        "'DSSE' appears in mission.md only in reference to the portfolio's "
        "own signed-receipt corpus and to T-04's verify_dsse cross-check, "
        "never as 'this predicate diverges from the DSSE envelope spec, "
        "here is why.' So the divergence found here is real and was NOT "
        "previously stated as DSSE-non-conformance against a named, "
        "versioned baseline -- it is a new finding, not a restatement of a "
        "disclosed and accepted design choice."
    ),

    "requirements_table": diag["requirements"],
    "requirements_summary": diag["summary"],

    "live_authority_under_test": diag["live_authority_under_test"],
    "sibling_conformant_implementation": diag["sibling_conformant_implementation"],
    "host_verified_receipt_schema_construction": diag["host_verified_receipt_schema_construction"],

    "relationship_to_prior_fires": {
        "t04_adversarial_forgery": {
            "path": "amphora-evidence-intake-validator/evidence/phase0/repairs/T-04/done/t04-adversarial-forgery-done.v1.dsse.json",
            "sha256": t04_sha,
            "prior_verdict": "CLAIM_REFUTED",
            "relationship": (
                "T-04 proved BEHAVIORALLY that host_receipt_valid admits forged "
                "DSSE envelopes because it never calls verify_dsse. This W-T-EIV "
                "receipt proves the same root cause STRUCTURALLY and "
                "THEORETICALLY against the named DSSE specification's own "
                "normative requirement list, independent of any specific "
                "forgery case, and is the first artifact for this module to "
                "cite the DSSE spec itself (version pinned) rather than measure "
                "only against the module's own fixtures."
            ),
            "not_a_repeat_of": "T-04 ran 12 forgery-scenario cases through the predicate; this receipt runs 11 spec-requirement structural checks against the predicate's source code and schema. Different method, same module, corroborating conclusion.",
        },
        "v1_real_eiv": {
            "path": "amphora-evidence-intake-validator/evidence/phase0/repairs/V1-REAL-EIV/done/v1-real-eiv-superseding-kpi.v1.dsse.json",
            "relationship": "Cited in R9 as independent evidence that the trust_store_status=='TRUSTED' conjunct cannot be honestly derived from the repo's own trust-store file for any real signer.",
        },
        "shipped_kpi": {
            "path": "amphora-evidence-intake-validator/evidence/phase0/kpis/evidence-intake-validator-host-receipt-integrity-kpi.v1.json",
            "sha256": shipped_kpi_sha,
            "modified_or_deleted": False,
            "note": "Not superseded; this receipt does not change any number in the shipped KPI. It adds a new, independent, previously-absent axis of measurement (named-spec conformance) that the shipped KPI's theory line implicitly claimed but never tested.",
        },
    },

    "proposed_followups": proposed_followups,

    "does_not_establish": [
        "No wet-lab, product-qualification, batch-release, legal, regulatory, or scientific authority.",
        "Not a claim that a 'pre-verified attestation, trust the host' architecture is illegitimate in general -- only that (a) this specific receipt wire format is not a DSSE envelope and could not be verified by the DSSE verification procedure, and (b) no production code path in this repo currently constructs such a receipt from a real verify_dsse() call (the only construction site found is a unit test).",
        "Not a claim that amphora_core::sign_dsse/verify_dsse themselves are non-conformant -- R11's cross-check finds them structurally conformant (DsseEnvelope schema + matching PAE builder); the divergence is that evidence-intake-validator does not use them.",
        "The runtime (amphora-assurance-capabilities/src/lib.rs) is NOT modified by this receipt; this is an independent, non-mutating theory/spec audit (AUDIT_ONLY).",
    ],

    "verdict": "CLAIM_REFUTED",
    "verdict_reason": (
        "The pinned claim under attack asserts BOTH DSSE-spec conformance AND "
        "that any divergence is deliberate and stated. Measured against 11 "
        "DSSE v1.0.2 normative requirements, the live predicate is 0/11 "
        "conformant (8 divergent, 3 not-applicable structurally), and none of "
        "this module's checked-in documentation names the DSSE spec as a "
        "baseline this receipt format was measured against or deliberately "
        "diverges from. Both halves of the claim are false as stated."
    ),

    "provenance": {
        "harness_path": "amphora-evidence-intake-validator/evidence/phase0/repairs/W-T-EIV/work/run_dsse_spec_conformance.py",
        "harness_sha256": harness_sha,
        "diagnostic_canonical_sha256": diag_sha,
        "lib_rs_sha256": lib_rs_sha,
        "crypto_rs_sha256": crypto_rs_sha,
        "mission_md_sha256_at_audit_time": mission_sha,
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "determinism_note": "No RNG, no wall clock; every requirement verdict is a deterministic function of on-disk source bytes (lib.rs, crypto.rs, mission.md, capability-profile.json, the shipped KPI) plus the hardcoded, version-pinned DSSE spec text fetched 2026-08-13.",
        "replay_method": "python3 amphora-evidence-intake-validator/evidence/phase0/repairs/W-T-EIV/work/run_dsse_spec_conformance.py",
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY campaign-item done receipt under evidence/phase0/repairs/W-T-EIV/done/",
        "signs_phase0_evaluation_or_review": False,
    },
}

body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.evidence-intake-validator-w-t-eiv-dsse-spec-conformance+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {
    "payload": base64.standard_b64encode(body).decode(),
    "payloadType": ptype,
    "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}],
}
receipt = {
    "evaluator_key_id": eval_key_id,
    "evaluator_public_key_hex": eval_pub_hex,
    "signature": envelope,
}

DONE.mkdir(parents=True, exist_ok=True)
out = DONE / "w-t-eiv-dsse-spec-conformance-done-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

# self-verify
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))

print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("verdict", body_obj["verdict"])
print("n_requirements", diag["summary"]["n_requirements"])
print("n_conformant", diag["summary"]["n_conformant"])
print("n_divergent", diag["summary"]["n_divergent"])
print("n_not_applicable", diag["summary"]["n_not_applicable"])
print("n_proposed_followups", len(proposed_followups))
print("two_replay_sha256", diag_sha)
print("receipt_sha256", sha(out.read_bytes()))
print("self_verify_signature", "OK")
