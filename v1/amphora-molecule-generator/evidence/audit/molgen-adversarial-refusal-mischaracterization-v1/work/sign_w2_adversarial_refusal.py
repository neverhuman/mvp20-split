#!/usr/bin/env python3
"""DSSE-Ed25519-sign the W2 adversarial-refusal-mischaracterization receipt
(amphora-molecule-generator).

AUDIT_ONLY. Attacks two claims:
  (1) docs/mission.md "Honest current state": "Adversary-supplied
      adversary_proposals list, adversary_declared_proposal_count, and
      candidate_declared availability booleans are all defensively refused."
  (2) evidence/phase0/kpis/molecule-generator-roadmap-diagnostic-quarantine-
      kpi.v1.json split_methodology: "The harness constructs 5 INDEPENDENT
      CandidateEnvelope scenarios..." plus the KPI harness's own
      industrial_context framing (molecule_generator_phase0_kpi.rs scenarios
      3-4): "runtime must NOT elevate proposal_count or generation_status" /
      "runtime must NOT elevate any of them".

Signing pattern replicated from
amphora-molecule-generator/evidence/audit/molgen-generator-runtime-grant-independence-v1/work/sign_w1.py
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
ITEM = MOD / "evidence/audit/molgen-adversarial-refusal-mischaracterization-v1"
WORK = ITEM / "work"
HARNESS_DIR = WORK / "harness"
DONE = ITEM
DONE.mkdir(parents=True, exist_ok=True)

SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

REL = "amphora-molecule-generator"
FIRE_ID = "20260819T130001-4158121-e486196c8f4e"


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

assert diag["all_decision_relevant_outputs_identical_to_baseline"] is True
assert diag["n_cases"] == 6
assert diag["diffs"] == []
assert diag["adversarial_field_total_occurrences_in_lib_rs"] == 0
lib_rs_actual_sha256 = diag["lib_rs_sha256"]

main_rs_sha = sha((HARNESS_DIR / "src/main.rs").read_bytes())
cargo_toml_sha = sha((HARNESS_DIR / "Cargo.toml").read_bytes())
trust_store_sha = sha(TRUST.read_bytes())
signer_sha = sha(Path(__file__).read_bytes())

mission_md = MOD / "docs/mission.md"
mission_md_sha = sha(mission_md.read_bytes())
kpi_path = MOD / "evidence/phase0/kpis/molecule-generator-roadmap-diagnostic-quarantine-kpi.v1.json"
kpi_sha = sha(kpi_path.read_bytes())
kpi_json = json.loads(kpi_path.read_text())

# ------------------------------------------------------------------- identity
eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"
trust_store = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust_store["keys"]}
eval_pin = eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id")
rev_pin = rev_key_id == tbr.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id")

body_obj = {
    "schema": "amphora.molecule-generator.w2-adversarial-refusal-mischaracterization-receipt.v1",
    "receipt_id": "molgen-w2-adversarial-refusal-mischaracterization-v1",
    "module_id": REL,
    "module": REL,
    "campaign_item_id": "",
    "run_type": "ADVERSARIAL_INPUT_INDEPENDENCE_LIVE_RUNTIME_PROBE",
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "EVIDENCE_ONLY",
    "phase": "PRE_PHASE_0",
    "scientific_success_required_for_phase0": False,
    "date": "2026-08-19",
    "generated_on_host": "xbabe2",
    "fire_id": FIRE_ID,
    "rdkit_version": "2026.03.2",

    "verdict": "CLAIM_REFUTED",

    "claim_under_attack": {
        "location_1": f"{REL}/docs/mission.md#honest-current-state (sha256 {mission_md_sha})",
        "quoted_text_1": (
            "Adversary-supplied adversary_proposals list, adversary_declared_proposal_count, and "
            "candidate_declared availability booleans are all defensively refused."
        ),
        "location_2": f"{REL}/evidence/phase0/kpis/molecule-generator-roadmap-diagnostic-quarantine-kpi.v1.json#split_methodology (sha256 {kpi_sha})",
        "quoted_text_2": kpi_json.get("split_methodology", "")[:220] + " ...",
        "location_3": "amphora-molecule-capabilities/tests/molecule_generator_phase0_kpi.rs (source lines 136, 151; lib_rs sibling, sha256 " + lib_rs_actual_sha256 + ")",
        "quoted_text_3": (
            "scenario 3 industrial_context: 'adversarial candidate injecting adversary_proposals + "
            "adversary_declared_generation_status=SCORED; runtime must NOT elevate proposal_count or "
            "generation_status'. scenario 4 industrial_context: 'adversarial candidate injecting "
            "availability booleans for RDKit + grammar + corpus; runtime must NOT elevate any of "
            "them'."
        ),
    },

    "headline": (
        "Both cited claims mischaracterize the mechanism. 'Defensively refused' and 'must NOT "
        "elevate' imply active validation logic that inspects adversary_proposals, "
        "adversary_declared_proposal_count, adversary_declared_generation_status, "
        "candidate_declared_pinned_rdkit_available, candidate_declared_locked_reaction_grammar_"
        "available, and candidate_declared_rights_cleared_corpus_available and rejects them. There "
        "is no such logic anywhere in the module's production implementation: an exhaustive "
        "in-harness grep of amphora-molecule-capabilities/src/lib.rs (sha256 " + lib_rs_actual_sha256 +
        ") for all six field-name strings returns 0 total occurrences -- the strings do not appear "
        "anywhere in the file, only in the KPI test's own scenario-construction code. "
        "generator_result(candidate, context), the sole function the roadmap-diagnostic-quarantine "
        "claim covers, builds base_metrics(candidate) from exactly three fields -- "
        "candidate.contract_hash_v1(), candidate.original_bytes_sha256(), candidate.candidate_id() "
        "-- then hardcodes every remaining status/gate/metric/explanation/uncertainty field as a "
        "literal, unconditional on molecule content. Nothing is inspected, so nothing is 'refused': "
        "the safe output is a structural accident of the function ignoring ALL molecule content, "
        "adversarial or benign alike, not a validation outcome. "
        "\n\n"
        "The companion claim that the KPI harness's 5 scenarios are 'INDEPENDENT' "
        "(kpi.v1.json#split_methodology) is separately false in the ordinary statistical sense the "
        "KPI framing invokes (5 independent samples backing a floor=1.0, sample_size=5 claim for "
        "16 of 17 published gates): live execution of the same 5 CandidateEnvelope scenarios plus a "
        "6th, deliberately extreme adversarial candidate (500 fabricated adversary_proposals, "
        "adversary_declared_proposal_count=999999999, forged gates={generation_authorized:true, "
        "deterministic_lineage_recorded:true}, forged missing_inputs=[], forged uncertainty='none') "
        "through the real production capability(GENERATOR_ID).evaluate() call shows all 6 "
        "decision-relevant outputs (status, evidence_scope, gates, metrics minus the "
        "identity-echo fields, missing_inputs, explanations, uncertainty, score, objective_values, "
        "source_refs) are BYTE-IDENTICAL. The published sample_size=5 (and here, empirically, 6) is "
        "pseudo-replication: true information content for every one of these 16 gates is 1 "
        "degree of freedom (a constant), not 5, because the function is provably invariant to "
        "molecule/adversarial-field content -- it varies only on the identity-echo fields "
        "(candidate_contract_hash_v1, original_bytes_sha256, lineage_diagnostic.parent_candidate_id) "
        "that this receipt's harness explicitly strips before comparing."
    ),

    "refutation_criterion": (
        "WOULD REFUTE 'defensively refused' / 'must NOT elevate' / '5 independent scenarios' if EITHER "
        "(a) any of the six adversarial field-name strings appears anywhere in the production source "
        "(amphora-molecule-capabilities/src/lib.rs) in a context that reads/branches on it -- i.e. "
        "real validation logic exists -- OR (b) the decision-relevant output (identity-fields "
        "stripped) differs between any two of the 6 driven candidates, proving the scenarios carry "
        "independent information. Observing EITHER would refute the mischaracterization finding "
        "(and confirm the claims as accurate)."
    ),
    "refutation_observed": (
        "Neither condition needed for the claims to survive was found. (a) grep of lib.rs for all "
        "six field names: 0 occurrences (adversary_proposals=0, adversary_declared_proposal_count=0, "
        "adversary_declared_generation_status=0, candidate_declared_pinned_rdkit_available=0, "
        "candidate_declared_locked_reaction_grammar_available=0, "
        "candidate_declared_rights_cleared_corpus_available=0) -- no validation/refusal logic "
        "exists to be exercised. (b) live-executed decision-relevant output for baseline (S1, S2, "
        "S5), the two KPI-shipped adversarial scenarios (S3, S4), and a 6th MEGA-adversarial "
        "scenario (S6, forged/oversized every adversarial field simultaneously) is byte-identical "
        "across all 6 -- diffs=[] -- confirming zero discriminating information in the 'adversarial' "
        "scenarios and zero effect from even grossly malformed adversarial content. The claims "
        "describe active defense and independent sampling; the mechanism observed is an "
        "input-independent constant function. CLAIM_REFUTED."
    ),

    "live_execution": {
        "method": (
            "capability(GENERATOR_ID).evaluate(&candidate, &features, &ctx) called directly (the "
            "same production entry point the Phase-0 KPI test uses) for 6 CandidateEnvelope cases: "
            "the 5 scenarios shipped verbatim in molecule_generator_phase0_kpi.rs plus a 6th "
            "MEGA-adversarial case constructed by this harness. Full ModuleResult serialized to "
            "JSON, then identity-derived fields (candidate_contract_hash_v1, original_bytes_sha256, "
            "lineage_diagnostic.parent_candidate_id -- all of which are EXPECTED and CORRECT to vary "
            "with candidate identity/bytes) stripped before comparison, isolating the decision "
            "surface: status, evidence_scope, gates, missing_inputs, explanations, uncertainty, "
            "score_0_1, objective_values, source_refs, and all remaining metrics."
        ),
        "n_cases": diag["n_cases"],
        "all_decision_relevant_outputs_identical_to_baseline": diag["all_decision_relevant_outputs_identical_to_baseline"],
        "diffs": diag["diffs"],
        "mega_adversarial_case_s6_decision_relevant_subset": next(
            c["decision_relevant_subset"] for c in diag["cases"] if c["case_id"] == "S6_MEGA_adversarial_extreme"
        ),
        "mega_adversarial_case_s6_planted_defect_content": {
            "adversary_proposals_count_injected": 500,
            "adversary_declared_proposal_count_injected": 999999999,
            "forged_gates_injected": {"generation_authorized": True, "deterministic_lineage_recorded": True},
            "forged_missing_inputs_injected": [],
            "forged_uncertainty_injected": "none -- fully validated",
            "observed_actual_proposal_count": 0,
            "observed_actual_gates": {"generation_authorized": False, "deterministic_lineage_recorded": True},
            "observed_actual_missing_inputs_len": 3,
        },
        "grep_static_evidence": {
            "target": "amphora-molecule-capabilities/src/lib.rs",
            "target_sha256": lib_rs_actual_sha256,
            "needles": diag["adversarial_field_names_searched"],
            "occurrences": diag["adversarial_field_occurrences_in_lib_rs"],
            "total_occurrences": diag["adversarial_field_total_occurrences_in_lib_rs"],
            "method": "Rust std::fs::read_to_string + str::matches(needle).count() inside the compiled harness binary (not a shell grep pasted in after the fact); reproduced identically across both replay runs.",
        },
    },

    "does_not_close": [
        "Does not dispute that the module currently, correctly, in fact returns "
        "status=INSUFFICIENT_INPUT/proposal_count=0/generation_status=LOCKED_INTERNAL for every "
        "input via generator_result() -- that output-invariant behavior is real, reproduced here, "
        "and is exactly what a companion 2026-08-16 receipt (molgen-w1-runtime-grant-independence, "
        "already REFUTED on other grounds) also confirmed for generator_result() specifically. Only "
        "the CHARACTERIZATION of the mechanism as 'defensive refusal' of specific adversarial "
        "content, and the framing of the 5 scenarios as carrying independent information, are "
        "refuted here.",
        "Does not assess amphora_molecule_capabilities::generate_authorized() (the separate live "
        "RDKit-backed path the 2026-08-16 W1 receipt drove) -- this probe is scoped to "
        "generator_result(), the function the roadmap-diagnostic-quarantine claim itself is scoped "
        "to.",
        "Does not modify config/phase0-trust-store.v1.json, module-manifest.json, any signed KPI, "
        "benchmark lock, mission.md, or prior falsification-ledger entries.",
        "Grants no synthesis-feasibility, patentability, desirability, performance, batch-release, "
        "or manufacturing-qualification authority.",
    ],

    "recommended_repair": (
        "Reword docs/mission.md 'Honest current state' to state plainly that generator_result() is "
        "an input-independent stub that ignores molecule content entirely (adversarial or benign), "
        "rather than describing adversarial fields as 'defensively refused' (which implies "
        "inspect-and-reject logic that does not exist). Reword "
        "evidence/phase0/kpis/.../kpi.v1.json#split_methodology to drop 'independent' or explicitly "
        "note the 5 (6, including this probe's case) CandidateEnvelope scenarios produce provably "
        "identical decision-relevant output under the current implementation, so sample_size=5 "
        "should not be read as 5 degrees of statistical freedom. If/when generator_result() is ever "
        "wired to read molecule content (as generate_authorized() already demonstrates is possible "
        "elsewhere in the same crate), these scenarios would then need to actually diverge to keep "
        "testing what their industrial_context text claims they test."
    ),

    "provenance": {
        "harness_sha256": {
            "src/main.rs": main_rs_sha,
            "Cargo.toml": cargo_toml_sha,
        },
        "signer_sha256": {"sign_w2_adversarial_refusal.py": signer_sha},
        "inputs_are_read_only": True,
        "real_inputs_read_sha256": {
            f"{REL}/docs/mission.md": mission_md_sha,
            f"{REL}/evidence/phase0/kpis/molecule-generator-roadmap-diagnostic-quarantine-kpi.v1.json": kpi_sha,
            "amphora-molecule-capabilities/src/lib.rs": lib_rs_actual_sha256,
        },
        "originals_byte_intact_after_this_probe": True,
        "build_flags": {"cargo": "cargo build --release"},
    },

    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "replay_method": (
            "The compiled release binary was executed twice; stdout JSON captured verbatim to "
            "diagnostic.canonical.json and diagnostic.runB.json and confirmed byte-equal before "
            "signing. Deterministic: fixed ExecutionContext (seed=20260819, fixed run_id), no RNG, "
            "no wall-clock, no network."
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
        "methods": "Rust source read + live capability evaluation via existing production code; Ed25519 (MIT/Apache) signing.",
        "in_scope": "marine anti-corrosion two-part epoxy-amine coatings (coating chemistry only)",
    },

    "theory_reference": {
        "pseudo_replication": (
            "Hurlbert 1984 Ecol. Monogr. 54(2):187-211 -- pseudoreplication: treating "
            "non-independent samples as if they carry independent statistical information."
        ),
        "dsse_signing": "in-toto DSSE spec (PAE = 'DSSEv1' SP len(type) SP type SP len(body) SP body)",
        "toolkit": "RDKit 2026.03.2 (pinned); not invoked by this probe (generator_result path only).",
    },

    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "authority": "AUDIT_ONLY",
        "used_for": "AUDIT_ONLY audit receipt under evidence/audit/molgen-adversarial-refusal-mischaracterization-v1/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin),
        "note": "phase0-evaluator seed used for AUDIT_ONLY signing of THIS receipt only; no dual-identity ceremony performed and none claimed.",
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

ptype = "application/vnd.amphora.molecule-generator-w2-adversarial-refusal-mischaracterization+json"
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
out = DONE / "molgen-w2-adversarial-refusal-mischaracterization-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

# ------------------------------------------------------------- SELF-VERIFY
back = json.loads(out.read_text())
env2 = back["signature"]
body_back = base64.standard_b64decode(env2["payload"])
pae_back = pae(env2["payloadType"], body_back)
Ed25519PublicKey.from_public_bytes(bytes.fromhex(back["evaluator_public_key_hex"])).verify(
    base64.standard_b64decode(env2["signatures"][0]["sig"]), pae_back)
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
