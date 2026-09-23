#!/usr/bin/env python3
"""DSSE-Ed25519-sign the W1 runtime-grant-independence adversarial-probe
receipt (amphora-molecule-generator).

AUDIT_ONLY. Attacks the "roadmap-diagnostic quarantine" claim in
docs/mission.md ("Runtime is a pure roadmap-diagnostic quarantine: never
invokes RDKit, never emits a proposal, always returns INSUFFICIENT_INPUT ...
proposal_count=0") and the KPI receipt at
evidence/phase0/kpis/molecule-generator-roadmap-diagnostic-quarantine-kpi.v1.json,
by driving the REAL production authorization/generation code path
(amphora_core::EngineEvidenceContextV3::verify ->
amphora_molecule_capabilities::generate_authorized, the same functions
amphora_engine::EnginePool::generate_compounds and the amphora-cli compound
campaign command use) with a hand-built Rust harness. Signing pattern
replicated from
amphora-molecule-generator/evidence/phase0/repairs/V-A06v2/work/sign_va06v2.py
(PAE construction, load_seed, payloadType, two-replay gate, self-verify).
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-molecule-generator"
ITEM = MOD / "evidence/audit/molgen-generator-runtime-grant-independence-v1"
WORK = ITEM / "work"
HARNESS_DIR = WORK / "harness"
DONE = ITEM
DONE.mkdir(parents=True, exist_ok=True)

SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"
MANIFEST = ROOT / "module-manifest.json"

REL = "amphora-molecule-generator"


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


# ------------------------------------------------------------ two-replay gate
canon = (HARNESS_DIR / "diagnostic.canonical.json").read_bytes()
runB = (HARNESS_DIR / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)

test_a = diag["test_a_real_deployed_root_fails_closed"]
test_b1 = diag["test_b1_two_real_keys_but_three_distinct_labels_SUCCEEDS"]
test_b2 = diag["test_b2_three_real_keys_three_labels_control_SUCCEEDS"]
test_c = diag["test_c_same_key_same_label_negative_control_MUST_FAIL"]

assert test_a["generate_compounds_ok"] is False
assert test_a["generate_compounds_error"] == "verified sparse Phase-0 generator runtime grant is absent"
assert test_b1["verify_ok"] is True and test_b1["generation_succeeded"] is True and test_b1["rdkit_invoked"] is True
assert test_b1["proposal_count"] == 1
assert test_b2["verify_ok"] is True and test_b2["generation_succeeded"] is True
assert test_c["verify_ok"] is False and test_c["is_independence_error"] is True

main_rs_sha = sha((HARNESS_DIR / "src/main.rs").read_bytes())
cargo_toml_sha = sha((HARNESS_DIR / "Cargo.toml").read_bytes())
manifest_sha = sha(MANIFEST.read_bytes())
trust_store_sha = sha(TRUST.read_bytes())
trust_store = json.loads(TRUST.read_text())
signer_sha = sha(Path(__file__).read_bytes())

mission_md = MOD / "docs/mission.md"
mission_md_sha = sha(mission_md.read_bytes())
kpi_path = MOD / "evidence/phase0/kpis/molecule-generator-roadmap-diagnostic-quarantine-kpi.v1.json"
kpi_sha = sha(kpi_path.read_bytes())

# ------------------------------------------------------------------- identity
eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"
tbr = {k.get("role"): k for k in trust_store["keys"]}
eval_pin = eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id")
rev_pin = rev_key_id == tbr.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id")

body_obj = {
    "schema": "amphora.molecule-generator.w1-runtime-grant-independence-adversarial-probe-receipt.v1",
    "receipt_id": "molgen-w1-runtime-grant-independence-adversarial-probe-v1",
    "module_id": REL,
    "module": REL,
    "campaign_item_id": "",
    "run_type": "ADVERSARIAL_LIVE_RUNTIME_AUTHORIZATION_BOUNDARY_PROBE",
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "EVIDENCE_ONLY",
    "phase": "PRE_PHASE_0",
    "scientific_success_required_for_phase0": False,
    "date": "2026-08-16",
    "generated_on_host": "xbabe2",
    "fire_id": "20260816T010001-738996-34ee62466b57",
    "rdkit_version": "2026.03.2",

    "verdict": "CLAIM_REFUTED",

    "claim_under_attack": {
        "location_1": f"{REL}/docs/mission.md#honest-current-state (sha256 {mission_md_sha})",
        "quoted_text_1": (
            "Runtime is a pure roadmap-diagnostic quarantine: never invokes RDKit, never emits a "
            "proposal, always returns INSUFFICIENT_INPUT with generation_status='LOCKED_INTERNAL', "
            "proposal_count=0."
        ),
        "location_2": f"{REL}/evidence/phase0/kpis/molecule-generator-roadmap-diagnostic-quarantine-kpi.v1.json (sha256 {kpi_sha})",
        "quoted_text_2": (
            "generator_result(candidate, context) never invokes RDKit and never emits a molecular "
            "proposal. Always returns status='INSUFFICIENT_INPUT' with "
            "evidence_scope='ROADMAP_DIAGNOSTIC_ONLY'."
        ),
    },

    "headline": (
        "mission.md's 'Honest current state' makes an unscoped, absolute claim about the module's "
        "'Runtime' as a whole ('never invokes RDKit, never emits a proposal, always returns "
        "INSUFFICIENT_INPUT'). That claim is FALSE: amphora-molecule-capabilities ships a second, "
        "live, CLI-wired generation path -- generate_authorized() / EnginePool::generate_compounds() "
        "/ amphora-cli compound campaigns (amphora-cli/src/compound.rs::run_campaign_from_v1, which "
        "lists amphora-molecule-generator in its own MOLECULE_MODULES constant) -- that DOES invoke "
        "the real pinned RDKit 2026.03.2 FFI and DOES emit a real, non-zero GeneratedMoleculeProposalV1 "
        "once a Phase-0 EngineEvidenceContextV3 runtime grant authorizes it. This harness drove the "
        "exact production functions (not a re-derivation) end to end and captured a real product: "
        "ethylene oxide (C1CO1) + ethylenediamine (NCCN), reaction_family='epoxy-amine-addition', "
        "requested_role='hardener' -> canonical product SMILES 'NCCNCCO' "
        "(N-(2-hydroxyethyl)ethylenediamine), reactive_amine_hydrogen_count=3, proposal_count=1, "
        "rdkit_invoked=true. The KPI receipt's own narrower text ('generator_result... never invokes "
        "RDKit') survives -- generator_result() is a genuinely hardcoded, input-independent stub -- "
        "but mission.md does not scope its claim to generator_result; it asserts this of the module's "
        "'Runtime' overall, and the module's Known-contradictions section does not disclose this "
        "second live path at all. "
        "\n\n"
        "A second, independently significant defect surfaced while building the fixture needed to "
        "obtain a grant: EngineEvidenceContextV3::verify() requires three DISTINCT signer identities "
        "(module-artifact / evaluation / independent-review) via "
        "BTreeSet::from([model_signer, evaluation_signer, review_signer]).len() == 3, where each "
        "signer is the *key_id string* amphora_core::verify_dsse() returns after checking a signature "
        "against whatever TrustStore the caller supplies. TrustStore::insert() de-duplicates only on "
        "key_id string, never on the underlying Ed25519 public-key bytes. Test B1 registered the SAME "
        "physical key (one SigningKey) under two DIFFERENT key_id labels ('w1-evaluation-signer', "
        "'w1-review-signer') for the evaluation and independent-review roles -- i.e. only 2 real "
        "distinct private keys were ever used, matching exactly the 2 Phase-0 keys "
        "(evaluator.ed25519.seed, internal-reviewer.ed25519.seed) this whole portfolio's "
        "config/phase0-trust-store.v1.json actually has (sha256 " + trust_store_sha + ") -- and "
        "verify() accepted it as three independent signers, authorizing real RDKit-backed "
        "generation. Test C (same key AND the same key_id label reused) was correctly rejected with "
        "MoleculeEvidenceError::Independence ('evaluation and independent review are not "
        "independently signed'), proving the checker isn't vacuous -- it just checks label-count, not "
        "key-uniqueness. So the 'three independently held human identities' security property this "
        "portfolio's governance repeatedly leans on (e.g. Phase-0 promotion needing '2 human "
        "dual-identity keys this cron lacks') is, at the code level, a label-counting check that a "
        "single keyholder registered under multiple trust-store entries can satisfy."
    ),

    "refutation_criterion": (
        "WOULD REFUTE the 'Runtime ... never invokes RDKit, never emits a proposal, always returns "
        "INSUFFICIENT_INPUT' claim if ANY reachable, real (non-test-only, non-hypothetical) function "
        "in the amphora-molecule-generator capability surface, when driven through its real "
        "production call chain with a validly-verified Phase-0 authorization object, invoked the "
        "pinned RDKit FFI and returned a non-empty molecular proposal."
    ),
    "refutation_observed": (
        "generate_authorized() -- reachable in production via "
        "amphora_engine::EnginePool::generate_compounds() and amphora-cli's compound-campaign "
        "command (amphora-cli/src/compound.rs::run_campaign_from_v1, MOLECULE_MODULES includes "
        "'amphora-molecule-generator') -- was driven with a verified EngineEvidenceContextV3 runtime "
        "grant and returned Ok(vec![GeneratedMoleculeProposalV1]) with product_structure='NCCNCCO', "
        "a real canonical SMILES computed by the live pinned RDKit 2026.03.2 FFI "
        "(amphora_rdkit_ffi::molecule_facts / execute_reaction), proposal_count=1. The refuting "
        "observation occurred."
    ),

    "test_a_real_deployed_root": {
        "purpose": (
            "Confirms the CURRENT, actually-deployed repository (real module-manifest.json, real "
            "config/phase0-trust-store.v1.json, no forged files written anywhere) has zero Phase-0 "
            "runtime-grant evidence context files, so generate_compounds genuinely fails closed "
            "right now for real production traffic -- this is not an active incident."
        ),
        "method": (
            "amphora_engine::EnginePool::new(REPO_ROOT, 1) constructed against the real "
            "/home/ubuntu/amphora/build/mvp20-split root (no scratch files involved), then "
            "generate_compounds() called with a real, well-formed CampaignGenerationRequestV1 "
            "(parent_structures=['C1CO1','NCCN'], reaction_family='epoxy-amine-addition', "
            "requested_role='hardener')."
        ),
        "result": test_a,
        "portfolio_wide_grep_confirms_zero_grant_files": (
            "grep -rl 'phase0_runtime_grants' --include='*.json' mvp20-split/ : 0 matches, repo-wide, "
            "at time of this probe."
        ),
    },

    "test_b1_label_identity_gap": {
        "purpose": (
            "PLANTED DEFECT: identity collapse to 2 real distinct keys registered under 3 distinct "
            "trust-store key_id labels, matching this cron's actual 2-key holdings."
        ),
        "how_planted": (
            "In an otherwise fully well-formed VerifiedAuditModuleInputV1 fixture for GENERATOR_ID "
            "(real epoxy-amine reaction SMARTS, synthetic example.invalid rights record marked "
            "TEST-ONLY, AuditOnly-ceilinged promotion policy, all parent-hash bindings correct), "
            "module_artifact was signed with SigningKey seed=101 (key_id 'w1-model-signer'); "
            "evaluation_receipt was signed with SigningKey seed=102 (key_id "
            "'w1-evaluation-signer'); independent_review_receipt was signed with the SAME SigningKey "
            "seed=102 object but a DIFFERENT key_id label ('w1-review-signer'). Only 2 distinct "
            "Ed25519 private keys exist across all three signatures."
        ),
        "detected": False,
        "expected_if_check_were_key_aware": "MoleculeEvidenceError::Independence",
        "observed": test_b1,
        "note": "verify() returned Ok; generate_authorized() ran to completion and invoked live RDKit.",
    },
    "test_b2_three_real_keys_control": {
        "purpose": "Positive functioning control -- 3 genuinely distinct keys, 3 distinct labels.",
        "result": test_b2,
        "note": "Confirms the pass path is real and not a broken/vacuous always-Ok() checker.",
    },
    "test_c_same_label_negative_control": {
        "purpose": (
            "Negative control -- same underlying key AND the SAME key_id label reused for evaluation "
            "and independent review (the textbook same-signer case)."
        ),
        "result": test_c,
        "note": (
            "Correctly rejected: MoleculeEvidenceError::Independence, "
            "'evaluation and independent review are not independently signed'. Proves the checker "
            "does discriminate on label equality -- it just never checks whether two DIFFERENT "
            "labels are backed by the SAME underlying public key."
        ),
    },

    "root_cause": {
        "file": "amphora-core/src/crypto.rs",
        "detail": (
            "TrustStore::insert(key_id, public_key) rejects a duplicate key_id but never checks "
            "whether public_key bytes already exist under a different key_id. verify_dsse() returns "
            "only the asserted key_id string as the 'signer'. Independence checks throughout "
            "amphora-core/src/molecule_evidence.rs (VerifiedAuditModuleInputV1::verify's "
            "evaluation_signer == review_signer check, and EngineEvidenceContextV3::verify's "
            "3-element BTreeSet-of-key_id-strings check) compare these asserted strings, never the "
            "underlying VerifyingKey bytes."
        ),
        "affected_surface": (
            "Every module gated by this pattern, not just GENERATOR_ID: NOVELTY_ID and PROCESS_QC_ID "
            "share the identical EngineEvidenceContextV3 3-way check; the V1/V2 molecule-model path "
            "(VerifiedMoleculeModelInputV1) has the analogous 2-way evaluation_signer != review_signer "
            "check with the same root cause."
        ),
    },

    "does_not_close": [
        "Does not mean the real, currently-deployed engine is actively generating molecules today: "
        "Test A confirms zero Phase-0 runtime-grant files exist anywhere in the real repository, and "
        "the real config/phase0-trust-store.v1.json has exactly 2 keys, both genuinely distinct "
        "(sha256 " + trust_store_sha + "), with no registered 'model-signer' identity for GENERATOR_ID "
        "at all -- exploiting the label-identity gap against the REAL trust store still requires "
        "someone to add a new key_id entry to config/phase0-trust-store.v1.json, which is a separate, "
        "out-of-scope precondition this probe did not attempt and does not claim to have crossed.",
        "Does not modify config/phase0-trust-store.v1.json, module-manifest.json, any signed KPI, "
        "benchmark lock, or the falsification ledger's prior entries.",
        "Grants no synthesis-feasibility, patentability, desirability, performance, batch-release, or "
        "manufacturing-qualification authority; generated_molecules_unmade_unvalidated and "
        "not_a_synthesis_recommendation claim locks were asserted true in the test fixture and are "
        "reasserted here.",
        "The generated test product (NCCNCCO) is a harness artifact from a synthetic scratch corpus "
        "(source_dataset_ids=['scratch-test-fixture-w1-not-real']); it is not offered as a real "
        "generation-corpus candidate and is not added to any dataset, ledger, or acquisition queue.",
        "Does not assess whether generate_authorized()'s chemistry (reaction SMARTS, applicability "
        "checks) is itself correct or complete for real coating-formulation use -- only that it is "
        "live, reachable, and RDKit-backed.",
    ],

    "recommended_repair": (
        "Either (a) EngineEvidenceContextV3::verify and VerifiedAuditModuleInputV1::verify should "
        "compare underlying VerifyingKey bytes for independence, not asserted key_id strings, or (b) "
        "TrustStore::insert should reject registering the same public-key bytes under more than one "
        "key_id. mission.md's Honest-current-state / Known-contradictions sections should also "
        "disclose the live generate_authorized/generate_compounds/CLI-compound-campaign path instead "
        "of describing the module's 'Runtime' solely in terms of the generator_result stub."
    ),

    "provenance": {
        "harness_sha256": {
            "src/main.rs": main_rs_sha,
            "Cargo.toml": cargo_toml_sha,
        },
        "signer_sha256": {"sign_w1.py": signer_sha},
        "inputs_are_read_only": True,
        "real_inputs_read_sha256": {
            "module-manifest.json": manifest_sha,
            "config/phase0-trust-store.v1.json": trust_store_sha,
            f"{REL}/docs/mission.md": mission_md_sha,
            f"{REL}/evidence/phase0/kpis/molecule-generator-roadmap-diagnostic-quarantine-kpi.v1.json": kpi_sha,
        },
        "originals_byte_intact_after_this_probe": True,
        "build_flags": {
            "cargo": "cargo build --release",
            "rdkit_feature_enabled": True,
            "RDKIT_INCLUDE_DIR": "/home/ubuntu/amphora/toolchains/rdkit-2026.03.2/include/rdkit",
            "RDKIT_LIB_DIR": "/home/ubuntu/amphora/toolchains/rdkit-2026.03.2/lib",
            "BOOST_INCLUDE_DIR": "/home/ubuntu/amphora/toolchains/rdkit-2026.03.2/include",
        },
    },

    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "replay_method": (
            "The compiled release binary was executed twice; stdout JSON captured verbatim to "
            "diagnostic.canonical.json and diagnostic.runB.json and asserted byte-equal before "
            "signing. Deterministic: fixed 32-byte SigningKey seeds (101/102/103), no RNG, no "
            "wall-clock, no network; RDKit computation on fixed SMILES inputs is deterministic."
        ),
    },

    "attestation": {
        "promotes_authority": False,
        "flips_scientific_readiness": False,
        "human_review_performed": False,
        "organizational_independence_asserted": False,
        "modifies_existing_receipts": False,
        "modifies_manifest": False,
        "modifies_ledger": False,
        "modifies_mission_front_matter": False,
        "modifies_locked_dataset": False,
        "modifies_signed_phase0_kpi": False,
        "modifies_benchmark_lock": False,
        "modifies_quarantined_data": False,
        "modifies_trust_store": False,
        "weakens_verifier_or_governance_guard": False,
        "trust_anchored_in_phase0_store": bool(eval_pin),
        "two_replay_sha256_gate": {
            "status": "PASS",
            "byte_identical": canon == runB,
            "canonical_diagnostic_sha256": diag_sha,
            "runB_diagnostic_sha256": sha(runB),
        },
    },

    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_existing_receipts": False,
    "modifies_manifest": False,
    "modifies_ledger": False,
    "modifies_mission_front_matter": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_benchmark_lock": False,
    "trust_anchored_in_phase0_store": bool(eval_pin),

    "rights_posture": {
        "external_dataset_used": False,
        "new_external_data_acquired": False,
        "quarantined_data_touched": False,
        "redistributes_third_party_dataset": False,
        "reaction_grammar_corpus": (
            "Entirely synthetic scratch fixture (source_dataset_ids=['scratch-test-fixture-w1-not-real'], "
            "rights source_url='https://example.invalid/w1-scratch-fixture'), not a real acquired "
            "or claimed-real dataset. Reaction SMARTS is a standard, textbook epoxide ring-opening "
            "by a primary/secondary amine (March's Advanced Organic Chemistry, ring-opening "
            "nucleophilic substitution at the less-hindered epoxide carbon); parent SMILES (C1CO1, "
            "NCCN) are the same ethylene-oxide / ethylenediamine structures already used by this "
            "module's own Phase-0 KPI test scenarios."
        ),
        "methods": "RDKit (BSD-licensed) reaction execution via the pinned in-tree FFI; Ed25519 (MIT/Apache) signing.",
        "in_scope": "marine anti-corrosion two-part epoxy-amine coatings (coating chemistry only)",
    },

    "theory_reference": {
        "reaction_chemistry": "Smith, M.B. & March, J. 2007, March's Advanced Organic Chemistry, 6th ed., Wiley -- epoxide ring-opening by amine nucleophiles",
        "dsse_signing": "in-toto DSSE spec (PAE = 'DSSEv1' SP len(type) SP type SP len(body) SP body)",
        "toolkit": "RDKit 2026.03.2 (pinned)",
    },

    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "authority": "AUDIT_ONLY",
        "used_for": "AUDIT_ONLY adversarial-probe receipt under evidence/audit/molgen-generator-runtime-grant-independence-v1/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin),
        "note": "phase0-evaluator seed used for AUDIT_ONLY signing of THIS receipt only; no dual-identity ceremony performed and none claimed. The scratch SigningKeys used INSIDE the harness fixture (seeds 101/102/103) are unrelated throwaway test keys, never registered in the real trust store.",
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
body2 = json.dumps(json.loads(body), indent=2, sort_keys=True).encode()
assert body == body2, "canonical payload serialization not byte-stable"

ptype = "application/vnd.amphora.molecule-generator-w1-runtime-grant-independence-probe+json"
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
out = DONE / "molgen-w1-runtime-grant-independence-adversarial-probe-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

# ------------------------------------------------------------- SELF-VERIFY
back = json.loads(out.read_text())
env2 = back["signature"]
body_back = base64.standard_b64decode(env2["payload"])
pae_back = pae(env2["payloadType"], body_back)
Ed25519PublicKey.from_public_bytes(bytes.fromhex(back["evaluator_public_key_hex"])).verify(
    base64.standard_b64decode(env2["signatures"][0]["sig"]), pae_back)
assert env2["signatures"][0]["keyid"].startswith("phase0-evaluator-3ef6b35"), env2["signatures"][0]["keyid"]
assert back["evaluator_key_id"] == eval_key_id
assert json.loads(body_back)["attestation"]["promotes_authority"] is False
assert json.loads(body_back)["verdict"] == "CLAIM_REFUTED"
print("WROTE", out)
print("receipt_sha256", sha(out.read_bytes()))
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("payload_sha256", sha(body))
print("two_replay_diagnostic_sha256", diag_sha)
print("SELF_VERIFY_OK", True)
