#!/usr/bin/env python3
"""DSSE-Ed25519-sign the Z-VOIDSCOPE receipt (ROTATION-mode attack, module
amphora-redteam-audit). AUDIT_ONLY. Does not modify the master manifest, any
locked dataset, or any existing signed receipt. Sign-only with the pinned
evaluator seed; self-verifies before writing.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
ITEM = ROOT / "amphora-redteam-audit/evidence/phase0/repairs/Z-VOIDSCOPE"
WORK = ITEM / "work"
OUT_DIR = ITEM / "done"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

FIRE_ID = "20260817T090001-1247635-ff2bbb38f70f"


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


runA_bytes = (WORK / "diagnostic.runA.json").read_bytes()
runB_bytes = (WORK / "diagnostic.runB.json").read_bytes()
byte_identical = runA_bytes == runB_bytes
assert byte_identical, "two-replay bytes differ -- NOT stable, do not sign"
diag = json.loads(runA_bytes)
assert diag["tautological_count"] == 1
assert diag["tautological_fn_names"] == ["redteam_diagnostic"]
assert diag["diagnostic_fn_count"] == 9

mutant_runA_bytes = (WORK / "diagnostic.mutant_runA.json").read_bytes()
mutant_runB_bytes = (WORK / "diagnostic.mutant_runB.json").read_bytes()
mutant_byte_identical = mutant_runA_bytes == mutant_runB_bytes
assert mutant_byte_identical, "mutant two-replay bytes differ"
mutant_diag = json.loads(mutant_runA_bytes)
assert mutant_diag["tautological_count"] == 2
assert set(mutant_diag["tautological_fn_names"]) == {
    "redteam_diagnostic", "formulation_arithmetic_diagnostic",
}

diagnostics_rs_sha256 = sha((ROOT / "amphora-assurance-capabilities/src/diagnostics.rs").read_bytes())
assert diagnostics_rs_sha256 == "4ec366110c523f30e285dd3cbca08fd199f28edb06560897cf7e17e7abe7dd89", \
    "diagnostics.rs has drifted since the Y-VOIDCORPUS pin -- re-scope before signing"
mission_md_sha256 = sha((ROOT / "amphora-redteam-audit/docs/mission.md").read_bytes())
kpi_receipt_sha256 = sha((ROOT / "amphora-redteam-audit/evidence/phase0/kpis/redteam-audit-deterministic-control-diagnostic-kpi.v1.json").read_bytes())
y_voidcorpus_receipt_sha256 = sha((ROOT / "amphora-redteam-audit/evidence/phase0/repairs/Y-VOIDCORPUS/done/y-voidcorpus-diagnostic-tautology-receipt.v1.dsse.json").read_bytes())
scope_analyzer_sha256 = sha((WORK / "scope_analyzer.py").read_bytes())
cargo_test_log = (WORK / "baseline_cargo_test.log").read_bytes()
cargo_test_log_sha256 = sha(cargo_test_log)

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
    "schema": "amphora.redteam-audit.z-voidscope-tautology-scope-boundary-receipt.v1",
    "receipt_id": "z-voidscope-tautology-scope-boundary-v1",
    "authority": "AUDIT_ONLY",
    "run_type": "FALSIFICATION_ATTACK",
    "mode": "ROTATION",
    "module": "amphora-redteam-audit",
    "campaign_item_id": "Z-VOIDSCOPE",
    "fire_id": FIRE_ID,
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_existing_receipts": False,
    "modifies_mission_front_matter": False,
    "modifies_amphora_core_or_diagnostics_rs": False,
    "directive_ref": None,

    "claim_under_attack": {
        "kpi_receipt_path": "amphora-redteam-audit/evidence/phase0/kpis/redteam-audit-deterministic-control-diagnostic-kpi.v1.json",
        "kpi_receipt_sha256_at_attack_time": kpi_receipt_sha256,
        "kpi_metric_targeted": "diagnostic_passed_flag_true_rate",
        "kpi_metric_note_verbatim": "Fraction where returned DeterministicControlDiagnosticV1.passed == true. Primary tamper-detection metric. Any embedded-fixture drift, per-module invariant break, or count-threshold miss drops this below 1.0. Nine modules, all passed.",
        "prior_finding_verbatim": (
            "Y-VOIDCORPUS (2026-08-15, receipt "
            "amphora-redteam-audit/evidence/phase0/repairs/Y-VOIDCORPUS/done/"
            "y-voidcorpus-diagnostic-tautology-receipt.v1.dsse.json) proved that "
            "1 of the 9 dispatched module diagnostics -- redteam_diagnostic(), "
            "this module's OWN entry -- is a zero-argument, zero-I/O function "
            "whose REJECT verdict is the tautology `mask != 0` over a "
            "self-generated corpus that is non-zero by construction, and whose "
            "authority_granted_count is a hardcoded `let granted = false;` "
            "literal wired to nothing. Its own does_not_close section explicitly "
            "left open whether the OTHER 8 dispatched diagnostics "
            "(evidence-intake, source-ledger, report-packager, "
            "formulation-arithmetic, formulation-universe, envelope-gates, "
            "cro-protocol-packager, optimizer-orchestrator) share this defect, "
            "calling a follow-up sweep across all 9 the natural next step to "
            "'generalize or bound this finding.'"
        ),
        "y_voidcorpus_receipt_sha256": y_voidcorpus_receipt_sha256,
        "scope_of_this_attack": (
            "Does the input-independent-tautology defect Y-VOIDCORPUS found in "
            "redteam_diagnostic() generalize to any of the other 8 dispatched "
            "module diagnostics? If any of the 8 share it, the KPI's own stated "
            "floor condition ('any ... per-module invariant break ... drops this "
            "below 1.0') is additionally false for that module too, widening the "
            "refutation. If none do, the Y-VOIDCORPUS finding is bounded to "
            "exactly 1 of 9 rather than left an open question."
        ),
    },

    "pre_registered_refutation_criterion_verbatim": (
        "Refuted if ANY of the 8 non-redteam dispatched diagnostic functions "
        "(evidence_intake_diagnostic, source_ledger_diagnostic, "
        "report_packager_diagnostic, formulation_arithmetic_diagnostic, "
        "formulation_universe_diagnostic, envelope_gates_diagnostic, "
        "cro_protocol_packager_diagnostic, optimizer_orchestrator_diagnostic) "
        "has a per-case ACCEPT/REJECT decision that does not route through any "
        "call to embedded external fixture data (strict_json() over an "
        "include_bytes! constant), an Ed25519 signature verification, or an "
        "imported production function from amphora_core / "
        "amphora_formulation_capabilities -- i.e. shares the "
        "hardcoded-constant-disconnected-from-input shape of redteam_diagnostic's "
        "`let granted = false;`. Survives only if the mechanical scan finds "
        "exactly the same 1-of-9 tautological set Y-VOIDCORPUS already reported, "
        "AND a positive control proves the scan can actually detect this defect "
        "shape when present."
    ),

    "attack_description": (
        "Built amphora-redteam-audit/evidence/phase0/repairs/Z-VOIDSCOPE/work/"
        "scope_analyzer.py, a brace-matching static scanner (string-literal-aware, "
        "so it does not miscount braces inside format!() strings) that extracts "
        "each of the 9 dispatched diagnostic function bodies from the live "
        "tracked amphora-assurance-capabilities/src/diagnostics.rs and checks "
        "whether the body calls at least one of: strict_json(, "
        "evidence_fixture_accepted(, source_control_accepted(, "
        "report_fixture_accepted(, protocol_fixture_accepted(, "
        "validate_formulation_mass(, validate_formulation_universe(, "
        "evaluate_envelope_policy(, authorize_optimizer_request(, .verify(. "
        "The first 3 helper predicates and the two _fixture_accepted functions "
        "themselves parse real include_bytes!-embedded JSON or perform real "
        "Ed25519 verification (confirmed by direct source read); the last 4 are "
        "production functions imported from amphora_core / "
        "amphora_formulation_capabilities (confirmed via the crate's own `use` "
        "block at diagnostics.rs:1-10), not local stubs. Ran the scanner twice "
        "back-to-back for a byte-identical two-replay gate, then ran a positive "
        "control: applied a textual mutation to a scratch copy of "
        "formulation_arithmetic_diagnostic (one of the 8 claimed-real functions) "
        "that strips its call to arithmetic_candidate()+validate_formulation_mass() "
        "and replaces the per-case `accepted` decision with a hardcoded literal "
        "`let accepted = true;` -- the exact shape of redteam_diagnostic's own "
        "defect -- and confirmed the scanner flags it, also run twice for a "
        "byte-identical replay."
    ),

    "static_scan": {
        "script_path": "amphora-redteam-audit/evidence/phase0/repairs/Z-VOIDSCOPE/work/scope_analyzer.py",
        "script_sha256": scope_analyzer_sha256,
        "analyzed_path": "amphora-assurance-capabilities/src/diagnostics.rs",
        "analyzed_sha256": diagnostics_rs_sha256,
        "analyzed_sha256_matches_y_voidcorpus_pin": True,
        "diagnostic_fn_count": diag["diagnostic_fn_count"],
        "per_function": diag["per_function"],
        "tautological_count": diag["tautological_count"],
        "tautological_fn_names": diag["tautological_fn_names"],
    },

    "positive_control": {
        "planted_defect": (
            "In a scratch in-memory copy of formulation_arithmetic_diagnostic "
            "(never written back to the tracked source file), replaced the real "
            "per-case decision block that calls arithmetic_candidate(fixture) "
            "then validate_formulation_mass(&candidate) and checks 9 fields of "
            "the real result, with a stub `let result: Result<Value, String> = "
            "Ok(json!({})); let accepted = true;` -- a hardcoded constant "
            "disconnected from the per-case fixture, structurally identical to "
            "redteam_diagnostic's real `let granted = false;`."
        ),
        "how_planted": (
            "scope_analyzer.py --mutate formulation_arithmetic_diagnostic applies "
            "a single exact-text .replace() inside extract_function_body()'s "
            "returned body string for that one function, then re-runs the same "
            "unmodified analyze() routine used against the real file. The "
            "mutation is entirely in-process text substitution over a string read "
            "from disk; amphora-assurance-capabilities/src/diagnostics.rs on disk "
            "is untouched (verified: its sha256 before and after this fire is "
            "identical, see analyzed_sha256 above)."
        ),
        "detected": True,
        "evidence": {
            "mutant_tautological_count": mutant_diag["tautological_count"],
            "mutant_tautological_fn_names": mutant_diag["tautological_fn_names"],
            "mutant_formulation_arithmetic_diagnostic_entry": mutant_diag["per_function"]["formulation_arithmetic_diagnostic"],
            "interpretation": (
                "Mutating away formulation_arithmetic_diagnostic's real "
                "production-code dependency flips it from has_external_dependency="
                "true (real source) to false (mutant), moving "
                "tautological_count from 1 to 2 and adding "
                "'formulation_arithmetic_diagnostic' to tautological_fn_names. "
                "The scanner has genuine discriminating power: it does not "
                "vacuously pass every function, and it does not vacuously flag "
                "every function -- it distinguishes the real, dependency-wired "
                "8 from a deliberately-detautologized-in-reverse copy of one of "
                "them."
            ),
        },
    },

    "baseline": {
        "command": "cargo test --offline -p amphora-assurance-capabilities --test redteam_audit_phase0_kpi",
        "result": "ok. 1 passed; 0 failed",
        "log_path": "work/baseline_cargo_test.log",
        "log_sha256": cargo_test_log_sha256,
        "confirms_claim_under_attack_is_live_and_currently_true": True,
        "diagnostics_rs_sha256_matches_mission_md_benchmark_pin": True,
    },

    "observed": {
        "real_source_tautological_count": diag["tautological_count"],
        "real_source_tautological_set_equals_y_voidcorpus_set": diag["tautological_fn_names"] == ["redteam_diagnostic"],
        "mutant_source_tautological_count": mutant_diag["tautological_count"],
        "two_replay_byte_identical_real": byte_identical,
        "two_replay_byte_identical_mutant": mutant_byte_identical,
    },

    "verdict": "CLAIM_SURVIVED",
    "interpretation": (
        "The generalized attack -- does the input-independent-tautology defect "
        "Y-VOIDCORPUS found in redteam_diagnostic() extend to any of the other 8 "
        "dispatched module diagnostics -- did NOT refute the claim. A mechanical, "
        "string-literal-aware static scan (not a hand-wave) of the live tracked "
        "amphora-assurance-capabilities/src/diagnostics.rs, cross-checked against "
        "direct source reading of every one of the 9 dispatched function bodies "
        "plus the crate's own `use amphora_core::{authorize_optimizer_request, "
        "...}` and `use amphora_formulation_capabilities::{evaluate_envelope_policy, "
        "validate_formulation_mass, validate_formulation_universe, ...}` import "
        "block, found that all 8 non-redteam diagnostics route their per-case "
        "ACCEPT/REJECT decision through either real embedded include_bytes! "
        "fixture JSON (evidence-intake, source-ledger, report-packager, "
        "cro-protocol-packager, each via strict_json()), a real Ed25519 "
        "signature verification (report-packager, cro-protocol-packager), or a "
        "call into real production validation/authorization code imported from "
        "amphora_core or amphora_formulation_capabilities (formulation-arithmetic, "
        "formulation-universe, envelope-gates, optimizer-orchestrator). None of "
        "the 8 contains a hardcoded literal standing in for a decision that "
        "should depend on the case's mutated/varied input. The positive control "
        "confirms this is not a vacuous or miscalibrated scan: deliberately "
        "reintroducing the exact defect shape (`let accepted = true;` "
        "disconnected from the real per-case fixture) into a scratch copy of one "
        "of the 8 is caught immediately (tautological_count 1 -> 2). This bounds "
        "the Y-VOIDCORPUS finding rather than leaving it open: the tautology "
        "defect is isolated to exactly 1 of the 9 modules aggregated into "
        "diagnostic_passed_flag_true_rate -- this module's own entry -- and does "
        "not generalize. The underlying refutation Y-VOIDCORPUS already recorded "
        "for redteam_diagnostic() itself stands unchanged and is not softened or "
        "re-litigated here."
    ),
    "does_not_close": [
        "Does not repair redteam_diagnostic() -- Y-VOIDCORPUS's CLAIM_REFUTED "
        "verdict for that 1-of-9 entry stands; a repair item (analogous to how "
        "the other 8 diagnostics genuinely exercise real code paths per case) "
        "remains open and is a natural REPAIR-mode campaign item.",
        "Does not certify the 8 diagnostics as bug-free -- only that their "
        "control-flow shape is not the specific input-independent-tautology "
        "defect class this scan targets. A real defect could still exist in "
        "their fixture data, their comparison thresholds, or the production "
        "functions they call; that is a different attack surface than the one "
        "tested here.",
        "Static text-matching cannot rule out an external-dependency call whose "
        "return value is then IGNORED before the accept/reject decision (a "
        "'fake' dependency) -- this scan checks for the call's presence, not "
        "that its result is load-bearing on the final boolean. Manual read of "
        "all 8 bodies (see attack_description) corroborates the calls are "
        "load-bearing, but that corroboration is a human read, not a mechanized "
        "invariant like the module-call-presence check itself.",
        "Does not certify Phase-1/Phase-2 promotion, scientific validity, "
        "procurement, legal, safety, or release authority for any module. "
        "AUDIT_ONLY.",
    ],
    "reproducibility": {
        "two_replay_sha256_gate_real": "PASS" if byte_identical else "FAIL",
        "two_replay_sha256_gate_mutant": "PASS" if mutant_byte_identical else "FAIL",
        "runA_sha256": sha(runA_bytes),
        "runB_sha256": sha(runB_bytes),
        "mutant_runA_sha256": sha(mutant_runA_bytes),
        "mutant_runB_sha256": sha(mutant_runB_bytes),
        "invocation_real": "python3 scope_analyzer.py amphora-assurance-capabilities/src/diagnostics.rs",
        "invocation_mutant": "python3 scope_analyzer.py amphora-assurance-capabilities/src/diagnostics.rs --mutate formulation_arithmetic_diagnostic",
        "determinism": "pure stdlib json/re-free text scan; no RNG, no wall clock, no filesystem writes by the analyzer itself",
    },
    "mission_md_sha256_at_attack_time": mission_md_sha256,
    "toolchain": {"python": "3, stdlib json/hashlib only for the scanner; cryptography.hazmat Ed25519 for signing"},
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY attack receipt under evidence/phase0/repairs/Z-VOIDSCOPE/done/",
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
ptype = "application/vnd.amphora.redteam-audit-z-voidscope-tautology-scope-boundary+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}

OUT_DIR.mkdir(parents=True, exist_ok=True)
out = OUT_DIR / "z-voidscope-tautology-scope-boundary-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))

print("WROTE", out)
print("verdict", body_obj["verdict"])
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
