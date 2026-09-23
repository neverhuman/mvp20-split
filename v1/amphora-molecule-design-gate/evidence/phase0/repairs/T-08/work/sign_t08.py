#!/usr/bin/env python3
"""DSSE-Ed25519-sign the T-08 first-adversarial-attack receipt for
amphora-molecule-design-gate.

REPAIR-MODE output contract for campaign item T-08: this receipt goes to
evidence/phase0/repairs/T-08/done/ because the done_criterion is met
(>=10 held-out real coating molecules incl. the 3 named hostile nulls run
through the REAL RDKit FFI + live gate, plus the founder directive T2-08
fail-closed / mutation-quarantine attack, plus a positive control since the
verdict is CLAIM_SURVIVED).

AUDIT_ONLY: signs an audit/repair receipt; does NOT promote the module, does
NOT flip scientific_readiness or mission.md front matter, does NOT modify the
master manifest, module-manifest.json, any locked dataset, the design-gate
fixture, or the live Rust runtime.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
ITEM = ROOT / "amphora-molecule-design-gate/evidence/phase0/repairs/T-08"
WORK = ITEM / "work"
HARNESS_MAIN = WORK / "harness/src/main.rs"
HARNESS_CARGO = WORK / "harness/Cargo.toml"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"
MISSION = ROOT / "amphora-molecule-design-gate/docs/mission.md"
DIRECTIVE = ROOT / "docs/directives/2026-08-05-closing-the-open-portfolio.md"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" "
            + str(len(body)).encode() + b" " + body)


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
assert canon == runB, "two-replay diagnostic bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)

pa = diag["part_a_gate_probes"]
assert pa["n_probes"] >= 10, "done_criterion requires >=10 held-out real molecules"
assert pa["n_hostile_nulls"] >= 3, "done_criterion requires >=3 hostile nulls"
assert pa["n_disagreements"] == 0, "refusing to sign SURVIVED: part A disagreements present"
assert not diag["part_b_slip_throughs"], "refusing to sign SURVIVED: a slip-through occurred"
assert not diag["part_b_mutation_violations"], "refusing to sign SURVIVED: mutation violation occurred"
assert not diag["part_b_generation_violations"], "refusing to sign SURVIVED: generation violation occurred"
assert diag["positive_control"]["detected"] is True, "positive control did not fire; cannot license SURVIVED"

hostile_null_ids = {
    "bdma-tertiary-amine-accelerator",
    "emi24-imidazole-latent-hardener",
    "dpg-diphenylguanidine-accelerator",
    "dotg-di-o-tolylguanidine-accelerator",
}
present_hostile = {r["id"] for r in pa["results"] if r["id"] in hostile_null_ids}
assert {"bdma-tertiary-amine-accelerator", "emi24-imidazole-latent-hardener",
        "dpg-diphenylguanidine-accelerator"} <= present_hostile, "missing a named hostile null"

harness_main_sha = sha(HARNESS_MAIN.read_bytes())
harness_cargo_sha = sha(HARNESS_CARGO.read_bytes())
mission_sha = sha(MISSION.read_bytes())
mission_text = MISSION.read_text()
directive_sha_actual = sha(DIRECTIVE.read_bytes())
DIRECTIVE_SHA_PINNED = "dcedb048e1142529de84aa6d741a065fdc29ebf744ef1b2feb81951c74573a6d"
directive_sha_matches = directive_sha_actual == DIRECTIVE_SHA_PINNED

# PHASE-0 BINDING GAP evidence: mission.md front matter declares PHASE_0 while
# its own prose states the current phase is Pre-Phase 0 (EVALUATION_RESULT_MISMATCH).
front_matter_phase = json.loads(mission_text.split("---")[1])["phase"]
prose_states_pre_phase_0 = "current phase is **Pre-Phase 0**" in mission_text

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub = rev_sk.public_key().public_bytes_raw()
rev_key_id = f"phase0-internal-reviewer-{sha(rev_pub)}"
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
rev_pin = (rev_key_id == tbr.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))
assert eval_pin, "evaluator key_id does not derive pinned trust-store id"

REFUTATION_CRITERION = ("Any out-of-domain input passes, or a structure-changing mutation is "
                         "admitted.")
refutation_observed = bool(diag["part_b_slip_throughs"]) or bool(
    diag["part_b_mutation_violations"]) or bool(diag["part_b_generation_violations"])

body_obj = {
    "schema": "amphora.molecule-design-gate.t08-live-runtime-adversarial-receipt.v1",
    "campaign_item_id": "T-08",
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "REAL_ARITHMETIC",
    "run_type": "SCIENCE_VALIDATION_ADVERSARIAL",
    "module": "amphora-molecule-design-gate",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_module_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_design_gate_fixture": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_live_rust_runtime": False,
    "claim_under_attack": {
        "receipt_path": "amphora-molecule-design-gate/docs/mission.md",
        "claim_text": ("amphora-molecule-design-gate has never received an adversarial verdict; "
                        "its constructive SIGNED_RECEIPT-era receipts are untested claims."),
    },
    "purpose": diag["purpose"],
    "attack_design": (
        "PART A: cloned the sibling module's role-live-runtime-domain-probe-v1 pattern but "
        "targeted this module's OWN decision surface -- design_gate_result, invoked through the "
        "real, public MoleculeCapability::evaluate_authorized(DESIGN_GATE_ID, ...) entry point, "
        "the exact call the live engine and the shipped Phase-0 KPI harness use -- fed with facts "
        "computed by the REAL pinned RDKit C++ FFI (amphora_rdkit_ffi::molecule_facts, RDKit "
        "2026.03.2) on 13 real, named, cited coating molecules held out of the module's "
        "self-authored 42-record known-answer fixture. All 3 prior design-gate audit receipts "
        "(fact-snapshot-authority-v1, smiles-representation-invariance-v1, "
        "rdkit-structural-facts-parity-v1) drove the gate with SYNTHETIC or VERBATIM facts, never "
        "with facts derived live from real SMILES through the pinned FFI -- that gap is what this "
        "attack closes. Includes the 4 hostile nulls: a tertiary-amine accelerator (BDMA), an "
        "imidazole latent hardener (EMI-24), and two guanidine-class accelerators (DPG, DOTG) -- "
        "DPG/DOTG previously defeated the SISTER module's role-ranker inference "
        "(role-guanidine-accelerator-domain-probe-v1, REFUTED 2026-08-03) before the shared bridge.cc "
        "C=N exclusion fix (R-N02) landed; re-run here live through the design GATE's declared-role "
        "check specifically, not just role-ranker's inference, as an independent regression check. "
        "Also includes 2 cross-declaration mismatch probes (a real resin declared hardener and vice "
        "versa) that exercise a design-gate-specific code path role-ranker's own probe never touches, "
        "since the gate checks a CALLER-DECLARED role, not an inferred one.\n"
        "PART B (founder directive T2-08): (1) structural out-of-domain admission -- a wildcard/"
        "polymer-notation DGEBA oligomer, a two-fragment epoxide+amine mixture, and a hypervalent-"
        "carbon invalid-valence SMILES -- run first through the real molecule_facts() FFI directly, "
        "then (mirroring exactly how the real amphora-engine normalization layer wires FeatureSnapshot) "
        "through the live gate with an empty facts snapshot on FFI rejection. (2) chemistry-changing "
        "mutation request -- amphora_engine::EnginePool::mutate() (the real "
        "'native-quarantined-no-structure-change-v1' lineage-only mutator) called on 3 candidates "
        "including one with an INJECTED force_structure_change/target_smiles field attempting to "
        "smuggle a structure change through extra JSON fields. (3) structure-changing GENERATION "
        "authorization -- amphora_engine::EnginePool::generate_compounds() (the real public entry "
        "point that wraps generate_authorized behind a signed Phase-0 runtime-grant check) called "
        "with 3 requests including a hostile-null parent and a forged reaction family, with no "
        "runtime grant available in this environment."
    ),
    "toolkit_provenance": diag["toolkit_provenance"],
    "part_a_gate_probes": {
        "n_probes": pa["n_probes"],
        "n_pass": pa["n_pass"],
        "n_disagreements": pa["n_disagreements"],
        "n_hostile_nulls": pa["n_hostile_nulls"],
        "results": pa["results"],
    },
    "part_b_directive_attack": {
        "structural_out_of_domain": diag["part_b_structural_fail_closed"],
        "slip_throughs": diag["part_b_slip_throughs"],
        "mutation_quarantine": diag["part_b_mutation_quarantine"],
        "mutation_violations": diag["part_b_mutation_violations"],
        "generation_authorization_attempts": diag["part_b_generation_authorization"],
        "generation_violations": diag["part_b_generation_violations"],
    },
    "positive_control": diag["positive_control"],
    "headline_result": {
        "verdict": "CLAIM_SURVIVED",
        "part_a_all_scored_as_expected": diag["verdict"]["part_a_all_scored_as_expected"],
        "part_b_no_slip_throughs": diag["verdict"]["part_b_no_slip_throughs"],
        "part_b_no_mutation_violations": diag["verdict"]["part_b_no_mutation_violations"],
        "part_b_no_generation_violations": diag["verdict"]["part_b_no_generation_violations"],
        "positive_control_fired": diag["verdict"]["positive_control_fired"],
    },
    "refutation_criterion_registry": {
        "part_a_own_criterion": (
            "Any of the 13 held-out real coating molecules (incl. the 4 hostile-null accelerators/"
            "latent hardeners declared as hardener) reaches a gate status other than the "
            "structurally-correct one -- i.e. a resin/hardener is wrongly FAILED_GATES, or an "
            "accelerator/mismatched declaration is wrongly SCORED."
        ),
        "part_a_observed": (
            f"{pa['n_pass']}/{pa['n_probes']} probes matched the expected status; "
            f"{pa['n_disagreements']} disagreements. Did NOT occur."
        ),
        "directive_t2_08_refutation_criterion_verbatim": REFUTATION_CRITERION,
        "directive_t2_08_observed": (
            "0 structural slip-throughs (wildcard/multi-fragment/invalid-valence probes all "
            "FAILED_GATES), 0 mutation violations (EnginePool::mutate always returned the input "
            "molecule field byte-identical and tagged lineage.generation_status="
            "QUARANTINED_NO_STRUCTURE_CHANGE, even when the candidate JSON tried to inject a "
            "force_structure_change/target_smiles directive), 0 generation violations "
            "(EnginePool::generate_compounds rejected every request with "
            "\"verified sparse Phase-0 generator runtime grant is absent\", including the malformed "
            "empty-request_id probe). The named observation (an out-of-domain input passing, or a "
            "structure-changing mutation being admitted) did NOT occur."
        ),
    },
    "closes": [
        "Whether the module's own design_gate_result decision (not just the sister module's "
        "role-ranker inference) agrees with structurally hand-derived, literature-cited ground "
        "truth when fed REAL RDKit-FFI-derived facts on real coating molecules, including "
        "accelerator/latent-hardener hostile nulls and declared-role cross-mismatches.",
        "Whether wildcard/polymer, multi-fragment, and invalid-valence SMILES can reach a SCORED "
        "gate decision via the real production wiring.",
        "Whether a chemistry-changing mutation request (including one attempting to inject a "
        "structure-change directive through extra candidate JSON fields) can ever alter the "
        "molecule structure through EnginePool::mutate.",
        "Whether a structure-changing generation request can be authorized without a signed "
        "Phase-0 runtime grant.",
    ],
    "does_not_close": [
        "EVALUATION_SIGNATURE_ABSENT / the R-D07 human dual-identity Phase-0 promotion ceremony "
        "(needs two human-held identity keys this cron does not have); this receipt is AUDIT_ONLY "
        "and grants no promotion, procurement, safety, synthesis, or freedom-to-operate authority.",
        "The PHASE-0 BINDING GAP itself (see phase0_binding_gap below) -- recorded, not repaired; "
        "repair needs the same human ceremony.",
        "The generic (non-invalid-valence-specific) gate_reason attribution when facts are absent: "
        "the gate correctly never SCOREs an invalid-valence structure, but its reason string "
        "('positive_applicability_unavailable_without_rdkit_and_ontology') does not distinguish "
        "'RDKit rejected this structure as chemically invalid' from any other facts-absent case. "
        "This is an attribution-precision gap, not a fail-open defect -- the gate never admits the "
        "structure either way.",
        "Only 13 gate probes and 3 structural probes; does not exhaustively cover the "
        "out-of-domain input space (no charged species, no isotope labels, no Markush/query atoms "
        "beyond the single wildcard probe, no >2-fragment mixtures).",
        "DOES NOT reopen the already-SURVIVED fact-snapshot-authority-v1 finding that "
        "design_gate_result trusts ANY schema-conformant MoleculeFactsV1 snapshot without "
        "re-validating it against the candidate's raw structure text (G4: serde contract is the "
        "sole admission wall). This fire's positive_control re-demonstrates that exact, previously "
        "documented behavior on purpose (to satisfy this fire's mechanical positive-control "
        "requirement) -- it is not a new finding. In the real production pipeline that behavior is "
        "not directly reachable by an external attacker because molecule_facts() itself refuses to "
        "compute facts for wildcard/multi-fragment SMILES before the RDKit backend is even touched "
        "(part_b_structural_fail_closed above); the residual exposure is to a hypothetical future "
        "bug in the upstream normalization wiring (amphora-engine::apply_normalization), which is "
        "outside this module.",
    ],
    "phase0_binding_gap": {
        "state": "EVALUATION_RESULT_MISMATCH",
        "description": (
            "amphora-molecule-design-gate/docs/mission.md front matter declares "
            f'"phase":"{front_matter_phase}" while its own prose states the current phase is '
            "Pre-Phase 0 -- the same 8-module binding gap the founder directive names, where a "
            "test harness overwrote hash-pinned evidence bytes; signatures remain valid, bindings "
            "are broken. Recorded here per directive T2-08 instructions so this attack and the "
            "R-D07 human ceremony share one evidence trail. The ceremony itself is NOT attempted "
            "by this fire (needs two human-held identity keys this cron does not have)."
        ),
        "mission_front_matter_phase": front_matter_phase,
        "mission_prose_asserts_pre_phase_0": prose_states_pre_phase_0,
        "mission_sha256": mission_sha,
    },
    "provenance": {
        "harness_main_rs_sha256": harness_main_sha,
        "harness_main_rs_path": "evidence/phase0/repairs/T-08/work/harness/src/main.rs",
        "harness_cargo_toml_sha256": harness_cargo_sha,
        "harness_binary_provenance": (
            "cargo build --release --features amphora-rdkit-ffi/rdkit against amphora-rdkit-ffi "
            "(path dependency), amphora-molecule-capabilities, amphora-core, and amphora-engine "
            "(path dependencies, exact same crates the live checked runtime ships), compiled with "
            "cxx against the pinned RDKit 2026.03.2 prefix at "
            "/home/ubuntu/.local/share/amphora/rdkit-2026.03.2 "
            "(RDKIT_INCLUDE_DIR/RDKIT_LIB_DIR/BOOST_INCLUDE_DIR); "
            f"toolkit_provenance.exact_version_match={diag['toolkit_provenance']['exact_version_match']}."
        ),
        "dataset_fixture_sha256_unused": (
            "this attack deliberately does not touch "
            "reference/phase0-design-gate-known-answer.v1.json; all 13 gate probes and 3 "
            "structural probes are held-out, real, cited molecules distinct from the fixture."
        ),
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "diagnostic_byte_identical": canon == runB,
        "determinism_basis": (
            "no RNG, no wall-clock, fixed hardcoded probe list, serde_json BTreeMap key ordering "
            "(preserve_order not enabled) => canonical byte order every run; each gate call is "
            "itself replayed twice inside the harness (per_call_two_replay_byte_stable) in addition "
            "to the outer two-process replay."
        ),
    },
    "directive_path": "docs/directives/2026-08-05-closing-the-open-portfolio.md",
    "directive_sha256": DIRECTIVE_SHA_PINNED,
    "directive_sha256_verified_on_disk": directive_sha_matches,
    "directive_obligation": "T2-08",
    "directive_ref": {
        "doc": "AMPHORA-DIRECTIVE-2026-08-05",
        "section": "A.1",
        "item_id": "T2-08",
        "owner": "LOOP",
        "md_path": "docs/directives/2026-08-05-closing-the-open-portfolio.md",
        "md_sha256": DIRECTIVE_SHA_PINNED,
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub.hex(),
        "used_for": "AUDIT_ONLY repair/attack receipt under evidence/phase0/repairs/T-08/done/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin),
    },
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER",
        "key_id": rev_key_id,
        "public_key_hex": rev_pub.hex(),
        "derives_pinned_trust_store_key_id": bool(rev_pin),
        "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed.",
    },
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.molecule-design-gate-t08-live-runtime-adversarial+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {
    "payload": base64.standard_b64encode(body).decode(),
    "payloadType": ptype,
    "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}],
}
receipt = {
    "evaluator_key_id": eval_key_id,
    "evaluator_public_key_hex": eval_pub.hex(),
    "reviewer_public_key_hex": rev_pub.hex(),
    "signature": envelope,
}
out = ITEM / "done" / "t08-design-gate-live-runtime-adversarial-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("two_replay_diag_sha256", diag_sha)
print("harness_sha256", harness_main_sha)
print("directive_sha256_verified_on_disk", directive_sha_matches)
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
print("verdict", "CLAIM_SURVIVED")
print("refutation_observed", refutation_observed)
