#!/usr/bin/env python3
"""DSSE-Ed25519-sign the U-GEN live-proposal-path DESIGN receipt for
amphora-molecule-generator. Construction replicated from
amphora-evidence-intake-validator/benchmarks/sign_canon_invariance.py and
amphora-molecule-generator/evidence/phase0/repairs/R-A06/work/sign_ra06_repair.py
(pae, load_seed, payloadType, envelope fields, trust-store key derivation).

DESIGN ONLY: this script writes ONE new signed receipt. It does not un-quarantine
the generator, does not modify quarantined_optimizer_policy, does not touch
module-manifest.json, mission.md front-matter, or any file outside
amphora-molecule-generator/evidence/phase0/repairs/U-GEN/.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-molecule-generator"
ITEM = MOD / "evidence/phase0/repairs/U-GEN"
WORK, DONE = ITEM / "work", ITEM / "done"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

REL = "amphora-molecule-generator"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def sha_file(rel_path):
    return sha((ROOT / rel_path).read_bytes())


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


# ---------------------------------------------- cited-source provenance (binds every
# file:line quote in this design to the exact bytes it was read from this fire)
CITED_FILES = {
    "amphora-molecule-capabilities/src/lib.rs": sha_file("amphora-molecule-capabilities/src/lib.rs"),
    "amphora-engine/src/lib.rs": sha_file("amphora-engine/src/lib.rs"),
    "amphora-core/src/lib.rs": sha_file("amphora-core/src/lib.rs"),
    "amphora-core/src/phase0.rs": sha_file("amphora-core/src/phase0.rs"),
    "amphora-core/src/contract.rs": sha_file("amphora-core/src/contract.rs"),
    "amphora-molecule-generator/docs/mission.md": sha_file("amphora-molecule-generator/docs/mission.md"),
    "amphora-molecule-generator/docs/capability-profile.json": sha_file("amphora-molecule-generator/docs/capability-profile.json"),
    "amphora-optimizer-orchestrator/docs/mission.md": sha_file("amphora-optimizer-orchestrator/docs/mission.md"),
    "amphora-solver-lab/README.md": sha_file("amphora-solver-lab/README.md"),
    "module-manifest.json": sha_file("module-manifest.json"),
    "amphora-molecule-generator/evidence/audit/molgen-deterministic-grammar-yield-v1/molgen-deterministic-grammar-yield-receipt.v1.dsse.json":
        sha_file("amphora-molecule-generator/evidence/audit/molgen-deterministic-grammar-yield-v1/molgen-deterministic-grammar-yield-receipt.v1.dsse.json"),
}

# ---------------------------------------------- keys / trust anchoring
eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
rev_pin = (rev_key_id == tbr.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))
assert eval_pin, "evaluator key not anchored in phase0 trust store"

body_obj = {
    "schema": "amphora.molecule-generator.u-gen-live-proposal-path-design-receipt.v1",
    "receipt_id": "molgen-u-gen-live-proposal-path-design-v1",
    "repair_item": "U-GEN",
    "campaign_item_id": "U-GEN",
    "module_id": REL,
    "module": REL,
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "ROADMAP",
    "phase": "PRE_PHASE_0",
    "scientific_success_required_for_phase0": False,
    "date": "2026-08-13",
    "generated_on_host": "xbabe2",
    "run_type": "DESIGN_ONLY_SPECIFICATION",

    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_existing_receipts": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_benchmark_lock": False,
    "modifies_ledger": False,
    "modifies_mission_front_matter": False,
    "modifies_quarantined_optimizer_policy": False,
    "unquarantines_anything": False,
    "changes_any_authority_ceiling": False,
    "writes_outside_this_module": False,

    "objective": (
        "U-GEN objective verbatim scope: produce a signed DESIGN receipt specifying "
        "(1) the minimal runtime path by which grammar proposals could be emitted and "
        "routed to amphora-molecule-design-gate carrying authority=AUDIT_ONLY and every "
        "existing claim lock; (2) exactly which governance assertions currently forbid "
        "it, quoted with file:line, and which are human-ceremony vs engineering; (3) what "
        "amphora-solver-lab would need to consume that path; (4) the concrete test plan "
        "that would demonstrate the path without weakening any gate. This receipt performs "
        "NO implementation: it does not un-quarantine anything, does not change any "
        "authority ceiling, and does not modify quarantined_optimizer_policy."
    ),

    "current_state_confirmed_this_fire": {
        "generator_runtime_always_returns": (
            "generator_result() at amphora-molecule-capabilities/src/lib.rs:458 "
            "unconditionally returns status='INSUFFICIENT_INPUT', proposal_count=0, "
            "gates.generation_authorized=false for every candidate, regardless of input "
            "-- confirmed by reading lines 458-501 this fire."
        ),
        "optimizer_orchestrator_has_no_src_dir": (
            "find amphora-optimizer-orchestrator/src -type f returns nothing this fire; "
            "its only 'implementation' is the 5-line hardcoded stub at "
            "amphora-engine/src/lib.rs:474-482 plus the unwired amphora-core::"
            "authorize_optimizer_request (amphora-core/src/lib.rs:628-706), which the stub "
            "never calls on the live per-candidate path."
        ),
        "only_proposals_in_existence": (
            "38 offline grammar proposals from "
            "amphora-molecule-generator/evidence/audit/molgen-deterministic-grammar-yield-v1/"
            "molgen-deterministic-grammar-yield-receipt.v1.dsse.json (sha256 "
            f"{CITED_FILES['amphora-molecule-generator/evidence/audit/molgen-deterministic-grammar-yield-v1/molgen-deterministic-grammar-yield-receipt.v1.dsse.json']}), "
            "RDKit 2026.03.2, 5 published scaffold families, PI1M-pinned SA feasibility "
            "instrument. Receipt states verbatim: 'Runtime remains LOCKED_INTERNAL; no "
            "proposal emission enabled.'"
        ),
    },

    "deliverable_1_minimal_runtime_path": {
        "summary": (
            "No new dispatch architecture is required. The engine already (a) constructs "
            "any candidate JSON into a CandidateEnvelope via a single documented "
            "constructor, and (b) scores an arbitrary molecule CandidateEnvelope against "
            "amphora-molecule-design-gate through the SAME entrypoint used for every "
            "human-submitted candidate today. The only missing pieces are: the generator "
            "emitting non-empty proposals, something that materializes each proposal back "
            "into a CandidateEnvelope, and a second call into that existing entrypoint "
            "using the generator's own output as input. Five stages:"
        ),
        "stage_A_generator_emits_proposals": (
            "Replace the unconditional refusal body of generator_result() "
            "(amphora-molecule-capabilities/src/lib.rs:458-501) with a conditional path: "
            "when the pinned RDKit 2026.03.2 toolkit and the locked reaction/scaffold "
            "grammar (already demonstrated offline, same 5 families and 38-proposal yield "
            "as molgen-deterministic-grammar-yield-v1) are available in-process, populate "
            "metrics.proposal_count>0 and a metrics.proposals array of {smiles, "
            "scaffold_family, lineage_diagnostic} objects. objective_values stays empty "
            "(BTreeMap::new()); gates.generation_authorized stays a DISTINCT gate name "
            "from any ranking-authority gate, and stays false unless a human flips it -- "
            "emitting a proposal is not the same act as authorizing it for ranking."
        ),
        "stage_B_proposal_to_candidate_materialization": (
            "Each emitted proposal SMILES is wrapped into a new canonical "
            "CandidateEnvelope JSON object via CandidateEnvelope::from_bytes "
            "(amphora-core/src/contract.rs:199) or ::from_value (contract.rs:205) -- the "
            "IDENTICAL constructor already used for every externally submitted candidate. "
            "Proposals therefore re-enter the SAME strict-parsing, normalization, and "
            "candidate-contract hashing path as human-submitted chemistry; there is no "
            "privileged bypass. Provenance (parent_candidate_id, generator run_id, "
            "deterministic_seed) travels as declared payload metadata, not as a trusted "
            "fact -- it is re-derived/re-normalized like any other field."
        ),
        "stage_C_routing_to_design_gate": (
            "The materialized CandidateEnvelope is submitted to the existing "
            "fn execute() (amphora-engine/src/lib.rs:723-760, candidate_value + "
            "requested_modules: Option<&[&str]> at line 730) via EnginePool::score "
            "(amphora-engine/src/lib.rs:633) or ::score_many (line 674), with "
            "requested_modules=[\"amphora-molecule-design-gate\"]. design_gate_result "
            "already evaluates ANY molecule CandidateEnvelope regardless of source "
            "(confirmed: amphora-engine/src/lib.rs:365-372 dispatches design-gate through "
            "the shared MoleculeCapability for every molecule candidate, with no "
            "provenance check). Today execute() scores one externally supplied candidate "
            "against N requested capabilities and returns (confirmed by reading "
            "amphora-engine/src/lib.rs:352-401 and 723-800: single candidate in, N module "
            "results out, no module-to-module chaining). The missing piece is a caller "
            "that invokes execute() a SECOND time per emitted proposal, using Stage B's "
            "materialized envelope as candidate_value -- an orchestration loop, not a new "
            "capability."
        ),
        "stage_D_authority_and_lock_carriage": (
            "Every materialized proposal-candidate's resulting ScoreEnvelope must carry: "
            "authority_tier outside {RANKING, OPTIMIZER, PRODUCTION} and "
            "solver_use_ceiling in {DISABLED, AUDIT_ONLY, CONSTRAINT_ONLY} -- the SAME "
            "shape amphora-core::authorize_optimizer_request already enforces on every "
            "OTHER module's envelope (amphora-core/src/lib.rs:672-688); ranking_eligible=false "
            "and usable_by_optimizer=false; and all 10 REQUIRED_ZERO_AUTHORITY_CLAIM_LOCKS "
            "(amphora-core/src/phase0.rs:32-42: no_ranking_authority, "
            "no_optimizer_authority, no_release_authority, no_qualification_authority, "
            "no_patentability_authority, fto_not_performed, no_procurement_authority, "
            "no_regulatory_authority, no_safety_authority, "
            "no_product_performance_authority) present and true. This is not a new check "
            "to invent -- it is making the generator's own emitted envelope satisfy a "
            "shape the portfolio already validates for the other 28 modules."
        ),
        "stage_E_no_ranking_no_promotion": (
            "The routed design-gate ModuleResult for a generator-sourced candidate is "
            "recorded exactly like any other AUDIT_ONLY ScoreEnvelope (an append-only "
            "proposal log under evidence/, analogous to evidence/phase0/receipts/). It is "
            "never written to module-manifest.json, never flips scientific_readiness, and "
            "never reaches amphora-optimizer-orchestrator's ranking/solver path, which "
            "stays hard-disabled by quarantined_optimizer_policy() regardless (see "
            "deliverable_2, blocker B3)."
        ),
        "explicitly_not_designed": (
            "This design does not specify un-quarantining generator_result, does not "
            "specify changing any authority ceiling or quarantined_optimizer_policy field, "
            "and does not specify a solver-lab wiring beyond deliverable_3's requirements "
            "list. No code in this repo was changed by this receipt."
        ),
    },

    "deliverable_2_governance_blockers": [
        {
            "blocker_id": "B1",
            "file": "amphora-molecule-capabilities/src/lib.rs",
            "line": "458-501 (specifically 481-482, 493-495)",
            "quote": "status: \"INSUFFICIENT_INPUT\".into() ... (\"proposal_count\".into(), json!(0)) ... missing_inputs: vec![\"pinned RDKit C++ 2026.03.2 boundary\".into(), \"locked atom-mapped reaction grammar\".into(), \"rights-cleared generation evidence\".into()]",
            "classification": "ENGINEERING",
            "rationale": (
                "The generator's own runtime unconditionally refuses to emit anything for "
                "every candidate, independent of whether RDKit/grammar are actually usable "
                "-- the offline receipt proves the grammar path works today outside the "
                "runtime gate. Rewriting this function body is ordinary code work; it does "
                "not by itself require new authority (Stage D still gates the output)."
            ),
        },
        {
            "blocker_id": "B2",
            "file": "amphora-molecule-generator/docs/capability-profile.json (datasets block) and docs/mission.md",
            "line": "capability-profile.json datasets[*].rights; mission.md 'Checked datasets and artifacts' section",
            "quote": "\"rights\": \"UNRESOLVED\" ... \"Rights are reported per file; local presence is not evidence of ownership or permission ... All listed artifact rights remain UNRESOLVED because no SHA-bound rights receipt was found.\"",
            "classification": "HUMAN_CEREMONY_RIGHTS",
            "rationale": (
                "corrosion_series.json, cure_verification_set.json, facts.json, "
                "feedback_v1/dataset_context.json, and the pi1m_structures lock are all "
                "rights UNRESOLVED. The generator's own missing_inputs[2] ('rights-cleared "
                "generation evidence') names exactly this gap. Per this fire's standing "
                "rule, rights review is a human step this cron cannot perform -- clearing "
                "it is not an engineering task regardless of how Stage A/B/C are coded."
            ),
        },
        {
            "blocker_id": "B2b",
            "file": "amphora-engine/src/lib.rs",
            "line": "739-741",
            "quote": "(\"rights_cleared_scientific_corpus\".into(), Value::Bool(false),)",
            "classification": "HUMAN_CEREMONY_RIGHTS",
            "rationale": (
                "The engine hardcodes this feature flag false for every execute() call, "
                "portfolio-wide -- it is not module-specific and not something "
                "amphora-molecule-generator can flip unilaterally without a corresponding "
                "rights clearance, which is the same human step named in B2."
            ),
        },
        {
            "blocker_id": "B3",
            "file": "amphora-core/src/lib.rs",
            "line": "610-627 (quarantined_optimizer_policy); 628-706 (authorize_optimizer_request)",
            "quote": "ranking_enabled: false, solver_enabled: false, authority_expansion_allowed: false, decision_use_ceiling: \"AUDIT_ONLY\".into() ... if ... policy.ranking_enabled || policy.solver_enabled || policy.authority_expansion_allowed || policy.decision_use_ceiling != \"AUDIT_ONLY\" ... { return Err(\"optimizer registry policy is altered or incomplete\".into()); }",
            "classification": "HUMAN_CEREMONY_AUTHORITY",
            "rationale": (
                "These four fields ARE the authority ceiling this campaign item explicitly "
                "forbids changing. authorize_optimizer_request fails closed if the policy "
                "struct deviates from this literal at all. Flipping any of them is a "
                "promotion decision requiring the dual-identity ceremony keys this cron "
                "lacks -- not an engineering choice this fire can make."
            ),
        },
        {
            "blocker_id": "B4",
            "file": "amphora-engine/src/lib.rs",
            "line": "474-482",
            "quote": "\"amphora-optimizer-orchestrator\" => { let mut result = ModuleResult::quarantined(\"No scientific objective has passed its locked external gate.\"); result.status = \"FAILED_GATES\".into(); result.gates.insert(\"complete_authorized_objective_vector\".into(), Value::Bool(false)); ... }",
            "classification": "MIXED",
            "rationale": (
                "This arm hardcodes a quarantine result for EVERY live request and never "
                "calls authorize_optimizer_request at runtime (that function is exercised "
                "only by the Phase-0 KPI test harness per optimizer-orchestrator/docs/"
                "mission.md's own 'Focused checked test evidence' section). Wiring the stub "
                "to call the real function is ENGINEERING; letting its result carry any "
                "ranking/solver authority once wired is gated by B3 and therefore "
                "HUMAN_CEREMONY_AUTHORITY."
            ),
        },
        {
            "blocker_id": "B5",
            "file": "amphora-engine/src/lib.rs",
            "line": "340-351",
            "quote": "if manifest.modules.len() != 29 || actual != expected { return Err(RegistryError::Manifest(\"registry must contain exactly the 29 canonical module identities\".into())); }",
            "classification": "HUMAN_CEREMONY_AUTHORITY",
            "rationale": (
                "amphora-solver-lab is confirmed absent from module-manifest.json this "
                "fire (grep -c amphora-solver-lab module-manifest.json = 0) and from "
                "amphora-core::OPTIMIZER_MODULES (amphora-core/src/lib.rs:578-608, 29 "
                "entries, solver-lab not among them), so it is unreachable from "
                "capability_for()/active_modules() (amphora-engine/src/lib.rs:356-388) no "
                "matter what code exists in its own crate. Adding a module to this "
                "portfolio-wide invariant is a governance act requiring the same dual "
                "PHASE0_EVALUATOR/PHASE0_INTERNAL_REVIEWER signatures every module's "
                "promotion/policy.v1.json already requires, not a local code edit."
            ),
        },
        {
            "blocker_id": "B6",
            "file": "amphora-core/src/phase0.rs and amphora-molecule-generator/docs/mission.md (front matter)",
            "line": "phase0.rs:32-42 (REQUIRED_ZERO_AUTHORITY_CLAIM_LOCKS); mission.md front-matter line 1",
            "quote": "REQUIRED_ZERO_AUTHORITY_CLAIM_LOCKS: [&str; 10] = [\"no_ranking_authority\", \"no_optimizer_authority\", \"no_release_authority\", \"no_qualification_authority\", \"no_patentability_authority\", \"fto_not_performed\", \"no_procurement_authority\", \"no_regulatory_authority\", \"no_safety_authority\", \"no_product_performance_authority\"]; mission.md: \"authority_ceiling\": \"ROADMAP\", \"operational_readiness\": \"ROADMAP\", \"phase\": \"PRE_PHASE_0\"",
            "classification": "BOUNDARY_NOT_BLOCKER",
            "rationale": (
                "Not itself an obstacle to the design -- these are exactly the ceilings "
                "Stage D of deliverable_1 is required to preserve unchanged. Listed here "
                "because any future fire that edits mission.md front-matter to reflect a "
                "different phase/readiness would need the same dual-identity signatures "
                "as B3/B5 (promotion/policy.v1.json required_distinct_roles: "
                "PHASE0_EVALUATOR, PHASE0_INTERNAL_REVIEWER) -- HUMAN_CEREMONY if ever "
                "touched, untouched by this design."
            ),
        },
    ],

    "deliverable_3_solver_lab_requirements": {
        "current_state": (
            "amphora-solver-lab has real capability (README.md: 'genuine constrained "
            "formulation optimizer', exhaustive DoE, simplex-projected blend optimization, "
            "NSGA-II with pinned seed, AUDIT_ONLY authority, sha256-pinned oracle reads, "
            "two-replay DSSE signing) but is NOT one of the 29 canonical modules -- it is "
            "structurally invisible to amphora-engine's dispatch."
        ),
        "requirement_1_manifest_registration": {
            "what": "Add amphora-solver-lab to module-manifest.json's canonical module set and to amphora-core::OPTIMIZER_MODULES (amphora-core/src/lib.rs:578-608).",
            "classification": "HUMAN_CEREMONY_AUTHORITY",
            "why": "Blocked by B5 -- amphora-engine/src/lib.rs:340-343 hard-fails registry load unless manifest.modules.len()==29 and the set matches CANONICAL_MODULES exactly.",
        },
        "requirement_2_capability_dispatch_arm": {
            "what": "A new Capability impl (or extension of FormulationCapability, amphora-engine/src/lib.rs:365-372 area) wrapping amphora-solver-lab's existing NSGA-II/simplex/DoE engines (src/nsga2.rs, src/simplex.rs, src/doe.rs) behind the same evaluate() contract every other module implements.",
            "classification": "ENGINEERING",
            "why": "Ordinary trait-wiring once requirement_1 is granted; no new science, the optimizer engines already exist and are tested (tests/nsga2_determinism.rs, tests/simplex_projection.rs).",
        },
        "requirement_3_claim_lock_carriage": {
            "what": "Every envelope solver-lab emits must carry the same 10 REQUIRED_ZERO_AUTHORITY_CLAIM_LOCKS (phase0.rs:32-42) and solver_use_ceiling in {DISABLED, AUDIT_ONLY, CONSTRAINT_ONLY}, so authorize_optimizer_request treats it identically to the other 29 members.",
            "classification": "ENGINEERING (once requirement_1 granted)",
            "why": "solver-lab's README already asserts this posture (authority AUDIT_ONLY, promotes_authority: false, modifies_manifest: false) -- it is a claim to formalize into the envelope schema, not a new constraint to invent.",
        },
        "requirement_4_proposal_intake_pin": {
            "what": "Add the generator's materialized proposal-candidate schema (deliverable_1 Stage B output) to amphora-solver-lab/pins/source_pins.v1.json so solver-lab can read generator-sourced candidates through its existing sha256-pinned, fail-closed oracle-read discipline.",
            "classification": "ENGINEERING",
            "why": "solver-lab already refuses any unpinned or relocated source (README: 'a tampered or relocated source is refused, fail-closed'); this is one new pin entry, not new trust logic.",
        },
        "requirement_5_non_goal": (
            "solver-lab's no-live-model-calls / read-only-pinned-oracle constraint and its "
            "AUDIT_ONLY authority ceiling are NOT to be expanded by this integration -- it "
            "consumes generator proposals as one more sha256-pinned input, exactly as it "
            "already consumes ingredient-library/formulation-universe/envelope-gates "
            "receipts. No capability expansion is requested or required."
        ),
    },

    "deliverable_4_test_plan": [
        {
            "test_id": "T1_positive_control_routing",
            "what": "Construct one proposal SMILES from the hash-pinned 38-member molgen-deterministic-grammar-yield-v1 offline corpus, materialize via CandidateEnvelope::from_bytes (Stage B), call execute()/score() with requested_modules=[\"amphora-molecule-design-gate\"] (Stage C), assert Ok, non-ERROR status, and gates matching the SAME structural rules already exercised by the 42-case design_gate_phase0_kpi.rs fixture -- no new gate logic introduced.",
        },
        {
            "test_id": "T2_authority_non_escalation",
            "what": "Assert the materialized proposal-candidate's envelope carries ranking_eligible=false, usable_by_optimizer=false, solver_use_ceiling=\"AUDIT_ONLY\", and all 10 REQUIRED_ZERO_AUTHORITY_CLAIM_LOCKS=true; feed it through authorize_optimizer_request under the UNMODIFIED quarantined_optimizer_policy() and assert Ok with eligible_objective_count=0 and usable_by_optimizer=false -- the same assertions the existing Phase-0 KPI harness already makes for the other 29 modules (amphora-assurance-capabilities/tests/optimizer_orchestrator_phase0_kpi.rs).",
        },
        {
            "test_id": "T3_negative_control_escalation_attempt",
            "what": "Mutate the materialized envelope to set ranking_eligible=true (or drop one of the 10 locks) and assert authorize_optimizer_request returns Err(\"optimizer envelope attempts authority, score, solver, or lock escalation\") -- proves the EXISTING fail-closed check already catches a hostile proposal; the new path adds no new trust boundary to defend.",
        },
        {
            "test_id": "T4_rights_abstention_regression",
            "what": "Run the routing design against the ACTUAL current state (RDKit/grammar-corpus rights still UNRESOLVED per B2) and assert the generator continues to return proposal_count=0 / INSUFFICIENT_INPUT -- this design is a specification, not an activation; the existing 17+1 Phase-0 gates in molecule_generator_phase0_kpi.rs must continue to pass unchanged and byte-stable until B2 is cleared by a human.",
        },
        {
            "test_id": "T5_two_replay_determinism",
            "what": "Run Stages A-C twice with identical deterministic_seed/run_id and assert byte-identical materialized CandidateEnvelope JSON and byte-identical design-gate ModuleResult -- matching the portfolio's two-replay signing convention already used by every sign_*.py in this module.",
        },
        {
            "test_id": "T6_manifest_invariant_unchanged",
            "what": "Assert amphora-engine's registry-load invariant (lib.rs:340-343, exactly 29 canonical modules) is UNCHANGED and still enforced after wiring T1-T5 -- this whole routing design (generator -> design-gate) activates entirely within the EXISTING 29-module registry (both are already members). Any solver-lab-specific test is explicitly OUT OF SCOPE until B5/requirement_1 is separately granted by human ceremony.",
        },
    ],

    "human_decision_required": {
        "ask_1_live_audit_only_proposal_path": (
            "Authorize implementing Stages A-E of deliverable_1 for "
            "amphora-molecule-generator: generator_result() emits real RDKit/grammar-"
            "derived proposals; each proposal is materialized as a CandidateEnvelope via "
            "the existing CandidateEnvelope::from_bytes/from_value constructor "
            "(amphora-core/src/contract.rs:199,205) and routed through the existing "
            "execute()/score() entrypoint (amphora-engine/src/lib.rs:723,633) to "
            "amphora-molecule-design-gate -- WITHOUT changing quarantined_optimizer_policy "
            "(amphora-core/src/lib.rs:610-627), WITHOUT setting ranking_eligible=true "
            "anywhere, and WITHOUT touching module-manifest.json."
        ),
        "ask_2_rights_clearance": (
            "Clear the rights determination named in blocker B2 for "
            "amphora-molecule-generator/reference/mvp20/data/{corrosion_series.json,"
            "cure_verification_set.json,facts.json,feedback_v1/dataset_context.json} and "
            "reference/mvp20/locks/pi1m_structures-*.json (all currently rights: "
            "UNRESOLVED per docs/capability-profile.json and docs/mission.md), so the "
            "generator's own missing_inputs[2] ('rights-cleared generation evidence') can "
            "be satisfied without a false claim, and so amphora-engine's hardcoded "
            "rights_cleared_scientific_corpus=false (lib.rs:739-741) can be revisited."
        ),
        "ask_3_promote_solver_lab": (
            "Promote amphora-solver-lab to a mission-bearing module: add it to "
            "module-manifest.json's 29-module registry (or an explicitly-approved 30th "
            "slot) and to amphora-core::OPTIMIZER_MODULES (amphora-core/src/lib.rs:578-608), "
            "so it becomes reachable from amphora-engine's capability_for()/"
            "active_modules() dispatch (amphora-engine/src/lib.rs:356-388) and can consume "
            "the AUDIT_ONLY proposal path in ask_1 -- with its existing AUDIT_ONLY / "
            "no-authority-escalation posture (per its own README.md) preserved exactly, "
            "not expanded."
        ),
        "note": (
            "None of these three asks is performable by this cron: ask_1 and ask_3 each "
            "require the 2 human dual-identity PHASE0_EVALUATOR + PHASE0_INTERNAL_REVIEWER "
            "ceremony keys this cron does not hold (per promotion/policy.v1.json "
            "required_distinct_roles, identical for every module); ask_2 is a rights "
            "determination this cron is instructed never to perform unilaterally."
        ),
    },

    "closes": [
        "Specifies, with file:line citations, the minimal engineering path by which "
        "amphora-molecule-generator's proposals could reach amphora-molecule-design-gate "
        "under unchanged AUDIT_ONLY authority.",
        "Enumerates every governance assertion currently forbidding that path and "
        "classifies each as engineering vs human-ceremony (authority or rights).",
        "Specifies amphora-solver-lab's concrete integration requirements.",
        "Specifies a concrete test plan, including negative/positive controls on the "
        "authority boundary, that would demonstrate the path without weakening any "
        "existing gate.",
        "States the governance ask verbatim under human_decision_required for the "
        "operator to file.",
    ],
    "does_not_close": [
        "No code in the repository was changed by this receipt; generator_result() still "
        "returns INSUFFICIENT_INPUT/proposal_count=0 for every candidate.",
        "quarantined_optimizer_policy is unchanged: ranking_enabled=false, "
        "solver_enabled=false, authority_expansion_allowed=false, "
        "decision_use_ceiling=AUDIT_ONLY, all still true after this fire.",
        "module-manifest.json is unchanged; still exactly 29 canonical modules, "
        "amphora-solver-lab still absent.",
        "No rights determination was made or claimed; all datasets named in B2 remain "
        "rights: UNRESOLVED.",
        "No Phase-0 promotion; scientific_readiness and operational_readiness for "
        "amphora-molecule-generator, amphora-optimizer-orchestrator, and "
        "amphora-solver-lab are all unchanged.",
        "This is a design specification, not an implementation plan commitment or "
        "schedule.",
    ],

    "provenance": {
        "cited_source_sha256": CITED_FILES,
        "inputs_are_read_only": True,
        "no_files_written_outside_module": True,
    },

    "rights_posture": {
        "external_dataset_used": False,
        "new_external_data_acquired": False,
        "quarantined_data_touched": False,
        "note": "Pure design/specification receipt; no chemistry data read or produced.",
    },

    "theory_reference": {
        "toolkit": "RDKit 2026.03.2 (as pinned by molgen-deterministic-grammar-yield-v1)",
        "reference_monitor": "Anderson 1980 reference-monitor concept (already cited by this module's mission.md), applied here to the proposed Stage D authority-carriage check.",
    },

    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY design receipt under evidence/phase0/repairs/U-GEN/done/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin)},
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER", "key_id": rev_key_id, "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin), "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed."},
}

body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
assert body == json.dumps(body_obj, indent=2, sort_keys=True).encode(), "body not byte-stable"
ptype = "application/vnd.amphora.molecule-generator-u-gen-live-proposal-path-design+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
DONE.mkdir(parents=True, exist_ok=True)
out = DONE / "u-gen-live-proposal-path-design-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

# self-verify DSSE before declaring
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("receipt_sha256", sha(out.read_bytes()))
print("signature_verified", True)
