#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-redteam-audit T-11 FIRST adversarial attack
(campaign item T-11, fire 20260813T230001-3823541-2c844a6aca33).

Claim under attack (docs/mission.md): "amphora-redteam-audit has never received an
adversarial verdict; its constructive SIGNED_RECEIPT-era receipts are untested
claims." Specific target (per campaign item objective): the deterministic-control
diagnostic's 9/9=1.0 KPI claim -- whether a module could satisfy every one of the
9 stated control predicates while weakening registry/ranking quarantine.

Method: see work/t11_optimizer_quarantine_coverage_probe_main.rs. AUDIT_ONLY: signs
a receipt under evidence/phase0/repairs/T-11/done/. Does not modify amphora-core,
amphora-assurance-capabilities, the master manifest, or any other module's files --
the backdoor exists only inside a standalone /tmp probe binary, never in the live
shared crate.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
WORK = ROOT / "amphora-redteam-audit/evidence/phase0/repairs/T-11/work"
OUT_DIR = ROOT / "amphora-redteam-audit/evidence/phase0/repairs/T-11/done"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

FIRE_ID = "20260813T230001-3823541-2c844a6aca33"


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


run1_bytes = (WORK / "probe_run1.json").read_bytes()
run2_bytes = (WORK / "probe_run2.json").read_bytes()
byte_identical = run1_bytes == run2_bytes
assert byte_identical, "two-replay probe stdout differs -- NOT stable, do not sign"
probe = json.loads(run1_bytes)

baseline_log = (WORK / "baseline_cargo_test.log").read_text()
baseline_passed = "test redteam_audit_phase0_kpi_report_is_deterministic_and_gates_pass ... ok" in baseline_log

diagnostics_rs = ROOT / "amphora-assurance-capabilities/src/diagnostics.rs"
core_lib_rs = ROOT / "amphora-core/src/lib.rs"
kpi_test_rs = ROOT / "amphora-assurance-capabilities/tests/redteam_audit_phase0_kpi.rs"
directive_md = ROOT / "docs/directives/2026-08-05-closing-the-open-portfolio.md"
directive_index = ROOT / "docs/directives/2026-08-05-closing-the-open-portfolio.index.json"

diagnostics_rs_sha256 = sha(diagnostics_rs.read_bytes())
core_lib_rs_sha256 = sha(core_lib_rs.read_bytes())
kpi_test_rs_sha256 = sha(kpi_test_rs.read_bytes())
directive_sha256 = sha(directive_md.read_bytes())

mission_pin_diagnostics_rs = "4ec366110c523f30e285dd3cbca08fd199f28edb06560897cf7e17e7abe7dd89"

obligation = None
idx = json.loads(directive_index.read_text())
for o in idx["obligations"]:
    if o.get("id") == "A1-NOTE-T07-T11":
        obligation = o
        break
assert obligation is not None, "A1-NOTE-T07-T11 obligation not found in directive index"

probe_main_sha256 = sha((WORK / "t11_optimizer_quarantine_coverage_probe_main.rs").read_bytes())

report_mutant = probe["report_with_mutant_backdoored_authorize_optimizer_request"]
report_real = probe["report_with_real_authorize_optimizer_request"]

kpi_names = [
    "diagnostic_dispatch_ok_rate",
    "diagnostic_passed_flag_true_rate",
    "expected_equals_observed_fixture_outcomes_rate",
    "implementation_readiness_complete_rate",
    "zero_authority_lock_coverage_rate",
    "result_digest_byte_stable_across_replays_rate",
    "positive_or_negative_control_counts_present_rate",
    "unsupported_module_id_fail_closed_rate",
    "attack_axis_coverage_complete_rate",
    "authority_envelope_preservation_rate",
]
mutant_all_nine_are_1 = all(report_mutant["kpi"][k] == 1.0 for k in kpi_names)
mutant_escalated = probe["mutant_escalates_on_backdoor_input"]
real_stayed_safe = probe["real_stays_quarantined_on_backdoor_input"]
backdoor_untested = probe["backdoor_id_absent_from_all_12_real_fixtures"]
probe_matches_real = probe["probe_real_logic_copy_matches_real_compiled_dispatch"]

refutation_criterion_verbatim = (
    "A synthetic module fixture constructed that satisfies EVERY stated control "
    "predicate (all 9 rates 1.0) while violating registry/ranking quarantine intent, "
    "with the passing control output and the violating behaviour both shown; or, if "
    "no such fixture can be built, the specific predicate that makes it impossible "
    "quoted with file:line. Any case that slips through = CLAIM_REFUTED with the "
    "case quoted verbatim."
)
refutation_observation_occurred = bool(
    mutant_all_nine_are_1 and mutant_escalated and real_stayed_safe and backdoor_untested and probe_matches_real
)
verdict = "CLAIM_REFUTED" if refutation_observation_occurred else "CLAIM_SURVIVED"

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
assert eval_pin, "evaluator key_id does not match pinned trust store"

body_obj = {
    "schema": "amphora.redteam-audit.t11-optimizer-quarantine-coverage-receipt.v1",
    "receipt_id": "t11-optimizer-quarantine-coverage-v1",
    "authority": "AUDIT_ONLY",
    "run_type": "FALSIFICATION_ATTACK",
    "module": "amphora-redteam-audit",
    "campaign_item_id": "T-11",
    "fire_id": FIRE_ID,
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_other_module_files": False,
    "modifies_amphora_core_or_diagnostics_rs": False,
    "directive_path": "docs/directives/2026-08-05-closing-the-open-portfolio.md",
    "directive_sha256": directive_sha256,
    "directive_obligation": "A1-NOTE-T07-T11",
    "directive_obligation_record_verbatim": obligation,
    "directive_obligation_has_refutation_criterion_field": False,
    "directive_obligation_refutation_criterion_note": (
        "The A1-NOTE-T07-T11 obligation record carries no 'refutation_criterion' field "
        "(it is a scheduling/priority note: 'Leave queued for a genuinely adversarial "
        "second pass; lower priority than the twelve zero-verdict modules.'). This "
        "receipt is exactly that genuinely-adversarial second pass. The falsification "
        "refutation criterion actually pre-committed for this attack is the campaign "
        "item T-11's own done_criterion, restated verbatim below, per the founder "
        "directive instruction to restate whichever pre-committed criterion exists "
        "rather than substitute one."
    ),
    "claim_under_attack": {
        "receipt_path": "amphora-redteam-audit/docs/mission.md",
        "claim_text": (
            "amphora-redteam-audit has never received an adversarial verdict; its "
            "constructive SIGNED_RECEIPT-era receipts are untested claims."
        ),
        "adjacent_mission_md_assertion_also_in_scope": (
            "'diagnostic_dispatch_ok_rate observed 1.0 (9/9) ... diagnostic_passed_flag_true_rate "
            "observed 1.0 (9/9) ... expected_equals_observed_fixture_outcomes_rate observed 1.0 "
            "(9/9) ... [and 6 more predicates, all observed 1.0]' -- the specific quantitative "
            "claim this attack targets, per the campaign item objective's SPECIFIC TARGET clause."
        ),
    },
    "objective_quoted": (
        "SPECIFIC TARGET identified by the 2026-08-04 defensibility scorecard: This module "
        "audits others; attack ITS deterministic-control diagnostic (9/9 rates 1.0). Can a "
        "module pass the control while weakening registry/ranking quarantine? Construct a "
        "synthetic module fixture that satisfies every stated control predicate yet violates "
        "the quarantine intent."
    ),
    "pre_registered_refutation_criterion_verbatim": refutation_criterion_verbatim,
    "refutation_criterion_observation_occurred": refutation_observation_occurred,
    "attack_description": (
        "The 'amphora-optimizer-orchestrator' inner diagnostic inside "
        "deterministic_control_diagnostic (amphora-assurance-capabilities/src/diagnostics.rs "
        f"lines 1959-2152, SHA-256 of the whole file {diagnostics_rs_sha256}, matching "
        f"mission.md's pinned {mission_pin_diagnostics_rs}) exercises exactly 12 hardcoded "
        "OptimizerFixture cases against the real amphora_core::authorize_optimizer_request "
        f"(amphora-core/src/lib.rs lines 630-757, SHA-256 of the whole file "
        f"{core_lib_rs_sha256}), and the module's own function body is architecturally a "
        "single hardcoded literal Ok(...) (status=NO_ELIGIBLE_OBJECTIVES, ranking_performed="
        "false, solver_invoked=false, usable_by_optimizer=false, authority_upgrade=false, "
        "candidate_created_evidence=false) reached whenever no Err(...) fires -- i.e. every "
        "one of the 9 named KPI predicates in amphora-assurance-capabilities/tests/"
        f"redteam_audit_phase0_kpi.rs (SHA-256 {kpi_test_rs_sha256}) for this module is a "
        "function purely of how those exact 12 fixtures behave, and says nothing whatsoever "
        "about any input outside that fixed corpus. This receipt constructs one: a standalone "
        "Rust probe (work/t11_optimizer_quarantine_coverage_probe_main.rs, not a workspace "
        "member, path-dependency only on the real amphora-core and amphora-assurance-"
        "capabilities crates, never editing either) contains "
        "mutant_authorize_optimizer_request -- a byte-for-byte copy of the real function with "
        "exactly one addition: a backdoor branch, gated behind every one of the function's "
        "existing fail-closed checks (policy integrity, envelope integrity, objective/"
        "constraint well-formedness), that fires only when request_source==POLICY and one "
        "objective's objective_id equals the magic string 'T11-BACKDOOR-UNLOCK'. None of the "
        "12 real fixtures uses that objective_id (probe field "
        "backdoor_id_absent_from_all_12_real_fixtures=true), so the mutant is observationally "
        "identical to the real function across the entire fixture corpus the diagnostic "
        "actually checks. The probe rebuilds the SAME 12-fixture corpus, the SAME diagnostic() "
        "/ zero_authority_assertions() wrapper logic, and the SAME 9-KPI aggregation formulas "
        "as the real harness verbatim (probe field "
        "probe_real_logic_copy_matches_real_compiled_dispatch=true confirms the reproduction "
        "matches live dispatch to amphora_assurance_capabilities::deterministic_control_"
        "diagnostic('amphora-optimizer-orchestrator') exactly), substitutes the mutant for "
        "only this one of the 9 dispatched modules (the other 8 still dispatch to the real, "
        "unmodified, compiled deterministic_control_diagnostic), and recomputes all 9 named "
        "KPI rates."
    ),
    "baseline": {
        "command": "cargo test --offline -p amphora-assurance-capabilities --test redteam_audit_phase0_kpi",
        "result": "ok. 1 passed; 0 failed",
        "confirms_claim_under_attack_is_live_and_currently_true": baseline_passed,
        "log_path": "work/baseline_cargo_test.log",
        "diagnostics_rs_sha256_matches_mission_md_pin": diagnostics_rs_sha256 == mission_pin_diagnostics_rs,
    },
    "the_passing_control_output": {
        "note": (
            "compute_report(use_mutant=true): all 9 named KPI rates, dispatching the "
            "MUTANT backdoored function for amphora-optimizer-orchestrator and the REAL "
            "compiled diagnostic for the other 8 modules."
        ),
        "kpi": report_mutant["kpi"],
        "all_nine_gates_pass": report_mutant["all_nine_gates_pass"],
        "mutant_all_nine_rates_equal_1_0": mutant_all_nine_are_1,
        "optimizer_orchestrator_record": [r for r in report_mutant["records"] if r["module_id"] == "amphora-optimizer-orchestrator"][0],
    },
    "the_violating_behaviour": {
        "note": (
            "The SAME mutant function, fed the backdoor input directly (outside the "
            "fixture corpus the diagnostic checks): a well-formed POLICY-sourced request "
            "with one objective (objective_id='T11-BACKDOOR-UNLOCK', module_id="
            "'amphora-envelope-gates', section='objective_values', path='score'), no "
            "hard_constraints, no envelopes."
        ),
        "backdoor_input": probe["backdoor_input"],
        "mutant_authorize_optimizer_request_on_backdoor_input": probe["mutant_authorize_optimizer_request_on_backdoor_input"],
        "mutant_escalates_on_backdoor_input": mutant_escalated,
        "escalation_fields_true": {
            "ranking_performed": probe["mutant_authorize_optimizer_request_on_backdoor_input"]["ranking_performed"],
            "solver_invoked": probe["mutant_authorize_optimizer_request_on_backdoor_input"]["solver_invoked"],
            "usable_by_optimizer": probe["mutant_authorize_optimizer_request_on_backdoor_input"]["usable_by_optimizer"],
            "authority_upgrade": probe["mutant_authorize_optimizer_request_on_backdoor_input"]["authority_upgrade"],
        },
    },
    "isolation_control_real_function_same_input": {
        "note": (
            "The REAL, unmodified amphora_core::authorize_optimizer_request, fed the "
            "identical backdoor_input, stays safely quarantined -- isolating that the "
            "escalation above is caused solely by the planted backdoor, not by some "
            "difference in how the probe constructs requests."
        ),
        "real_authorize_optimizer_request_on_backdoor_input": probe["real_authorize_optimizer_request_on_backdoor_input"],
        "real_stays_quarantined_on_backdoor_input": real_stayed_safe,
    },
    "case_quoted_verbatim": (
        "Case that slips through: a POLICY-sourced OptimizerAuthorizationRequestV1 with "
        "objectives=[{objective_id:'T11-BACKDOOR-UNLOCK', module_id:'amphora-envelope-gates', "
        "section:'objective_values', path:'score'}], hard_constraints=[], envelopes=[], "
        "policy=quarantined_optimizer_policy(). Fed to a version of authorize_optimizer_request "
        "carrying one extra branch (placed in amphora-core/src/lib.rs, immediately before the "
        "function's existing final Ok(...) at line ~746) that returns "
        "OptimizerAuthorizationV1{status:'RANKED', ranking_performed:true, solver_invoked:true, "
        "usable_by_optimizer:true, authority_upgrade:true, candidate_created_evidence:true, "
        "eligible_objective_count:1, objective_values:{'T11-BACKDOOR-UNLOCK':'9.99'}} whenever "
        "request_source=='POLICY' and any objective_id=='T11-BACKDOOR-UNLOCK'. Every one of the "
        "9 named KPI predicates in redteam_audit_phase0_kpi.rs still reports observed==1.0 for "
        "this modified function, because none of the diagnostic's 12 embedded fixtures ever "
        "constructs an objective with that id -- the diagnostic's 'passed' flag and all 9 rates "
        "are entirely a function of those 12 fixed inputs and say nothing about this one."
    ),
    "interpretation": (
        f"{verdict}. The deterministic-control diagnostic's 9/9=1.0 result for "
        "amphora-optimizer-orchestrator, and by structural extension the identically-shaped "
        "9/9=1.0 results for the other 8 dispatched modules, certify only that a FIXED, "
        "FINITE, COMPILE-TIME-EMBEDDED set of fixtures behaves as expected -- they cannot and "
        "do not certify that arbitrary or novel inputs to the underlying authorization "
        "function are safely quarantined. A single extra conditional branch in "
        "authorize_optimizer_request, keyed on a value absent from all 12 fixtures, sails "
        "through every one of the 9 named KPI gates at exactly floor 1.0 (probe field "
        "mutant_all_nine_rates_equal_1_0=true) while granting real ranking, solver, and "
        "optimizer authority (ranking_performed=true, solver_invoked=true, "
        "usable_by_optimizer=true, authority_upgrade=true) on an input the diagnostic never "
        "tests. mission.md's own 'Known contradictions' section already states this in prose "
        "('A successful self-audit only confirms encoded checks; it is not independent "
        "red-team coverage or evidence that all attacks were anticipated'); this receipt "
        "converts that acknowledged caveat into a concrete, reproducible, byte-stable "
        "constructed case, as the campaign item's done_criterion requires. The refutation "
        "criterion pre-committed by the campaign item ('Any case that slips through = "
        "CLAIM_REFUTED with the case quoted verbatim') DID occur; the case is quoted verbatim "
        "above."
    ),
    "reproducibility": {
        "two_replay_stdout_byte_identical": byte_identical,
        "probe_run1_sha256": sha(run1_bytes),
        "probe_run2_sha256": sha(run2_bytes),
        "probe_main_rs_sha256": probe_main_sha256,
        "probe_main_rs_path": "work/t11_optimizer_quarantine_coverage_probe_main.rs",
        "probe_cargo_toml_path": "work/probe_Cargo.toml",
        "build_command": "cargo build --offline (standalone crate at /tmp/redteam_audit_t11_probe, path deps only, never added to the workspace)",
        "run_command": "./target/debug/redteam_audit_t11_probe (run twice, diffed byte-identical)",
        "amphora_core_lib_rs_sha256_at_probe_time": core_lib_rs_sha256,
        "amphora_assurance_capabilities_diagnostics_rs_sha256_at_probe_time": diagnostics_rs_sha256,
        "amphora_assurance_capabilities_redteam_audit_phase0_kpi_rs_sha256_at_probe_time": kpi_test_rs_sha256,
        "probe_real_logic_copy_matches_real_compiled_dispatch": probe_matches_real,
    },
    "does_not_close": [
        "Does not establish that the live, currently-compiled amphora-core/src/lib.rs "
        "actually contains this or any backdoor today -- baseline (above) confirms it "
        "currently does not, and the backdoor exists only inside the isolated /tmp probe, "
        "never committed to the shared crate. This is a constructive existence proof "
        "('such a fixture CAN be built and would pass'), not a discovered live vulnerability.",
        "Does not audit the other 8 dispatched modules' inner diagnostics (evidence-intake, "
        "source-ledger, redteam-audit-self, report-packager, formulation-arithmetic, "
        "formulation-universe, envelope-gates, cro-protocol-packager) for their own "
        "fixed-corpus completeness gaps individually -- the structural argument (finite "
        "embedded fixture set cannot universally quantify over all inputs) generalizes to "
        "each of them by construction, but each one's actual fixture corpus and function "
        "was not separately probed this fire.",
        "Does not propose or land a repair (e.g. property-based/fuzz testing of "
        "authorize_optimizer_request beyond the fixed 12 cases, or code-review/diff-review "
        "controls on amphora-core changes) -- out of scope for a FIRST adversarial test per "
        "the campaign item; a repair item would be the natural next campaign step.",
        "Does not certify Phase-1/Phase-2 promotion, scientific validity, procurement, "
        "legal, safety, or release authority for any module. AUDIT_ONLY.",
    ],
    "toolchain": {
        "rust": "workspace edition 2021, cargo build --offline",
        "python": "3, stdlib json/hashlib + cryptography.hazmat Ed25519",
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under evidence/phase0/repairs/T-11/done/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin),
    },
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER", "key_id": rev_key_id, "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin), "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed.",
    },
}

body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.redteam-audit-t11-optimizer-quarantine-coverage+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}

OUT_DIR.mkdir(parents=True, exist_ok=True)
out = OUT_DIR / "t11-optimizer-quarantine-coverage-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))

print("WROTE", out)
print("verdict", verdict)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("mutant_all_nine_rates_equal_1_0", mutant_all_nine_are_1)
print("mutant_escalates_on_backdoor_input", mutant_escalated)
print("real_stays_quarantined_on_backdoor_input", real_stayed_safe)
print("backdoor_id_absent_from_all_12_real_fixtures", backdoor_untested)
print("signature_verified", True)
print("envelope_sha256", sha(out.read_bytes()))
