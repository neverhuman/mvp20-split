#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-redteam-audit Y-VOIDCORPUS adversarial attack.

ROTATION mode fire (no campaign item). Strongest standing claim identified: the
deterministic-control-diagnostic KPI receipt's "diagnostic_passed_flag_true_rate"
metric (evidence/phase0/kpis/redteam-audit-deterministic-control-diagnostic-kpi.v1.json)
and docs/mission.md's headline claim that "a locked adversarial corpus detects
malformed envelopes and authority escalation" -- specifically as applied to the
amphora-redteam-audit module's OWN dispatched inner diagnostic (redteam_diagnostic()
in amphora-assurance-capabilities/src/diagnostics.rs), which is 1 of the 9 modules
counted in that 9/9=1.0 metric and contributes the module's own "30,000 negative
controls, 24/24 attack axes, authority_granted_count: 0" figures.

Finding: redteam_diagnostic() takes zero parameters, performs no I/O, and calls no
external authorization/validation function. Its "REJECT" verdict for all 30,000
generated cases is definitionally `mask != 0`, which is a structural guarantee of
its own corpus-generation algorithm (singletons, then pairs, then ascending masks
filtered to popcount>=3 -- every generated mask is non-zero by construction).
Its "authority_granted_count" is derived from a single hardcoded `let granted =
false;` literal, never assigned from `mask`, `index`, or any other value. Both
quantities that gate this diagnostic's `passed` flag are therefore invariant
constants, not measurements -- the diagnostic is mathematically guaranteed to
report full rejection and zero authority-granted on every possible invocation,
regardless of whether an actual DSSE forgery, registry tampering, or authority
escalation succeeds anywhere in the real system. AUDIT_ONLY: this receipt does not
modify amphora-assurance-capabilities, amphora-core, the master manifest, or any
other module's files. All demonstration code lives in a standalone /tmp probe
(path-dependency only on the real, unmodified crate) and read-only static analysis
of the tracked source file.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
WORK = ROOT / "amphora-redteam-audit/evidence/phase0/repairs/Y-VOIDCORPUS/work"
OUT_DIR = ROOT / "amphora-redteam-audit/evidence/phase0/repairs/Y-VOIDCORPUS/done"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

FIRE_ID = "20260815T150001-3724739-6e1148c69349"


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


probe_run1 = json.loads((WORK / "probe_run1.json").read_bytes())
probe_run2_bytes = (WORK / "probe_run2.json").read_bytes()
probe_run1_bytes = (WORK / "probe_run1.json").read_bytes()
probe_byte_identical = probe_run1_bytes == probe_run2_bytes
assert probe_byte_identical, "two-replay probe stdout differs -- do not sign"

static_analysis = json.loads((WORK / "static_analysis.json").read_text())
rederivation = json.loads((WORK / "independent_rederivation.json").read_text())

baseline_log = (WORK / "baseline_cargo_test.log").read_text()
baseline_passed = "test redteam_audit_phase0_kpi_report_is_deterministic_and_gates_pass ... ok" in baseline_log

diagnostics_rs = ROOT / "amphora-assurance-capabilities/src/diagnostics.rs"
kpi_test_rs = ROOT / "amphora-assurance-capabilities/tests/redteam_audit_phase0_kpi.rs"
kpi_receipt_path = ROOT / "amphora-redteam-audit/evidence/phase0/kpis/redteam-audit-deterministic-control-diagnostic-kpi.v1.json"
mission_md = ROOT / "amphora-redteam-audit/docs/mission.md"

diagnostics_rs_sha256 = sha(diagnostics_rs.read_bytes())
kpi_test_rs_sha256 = sha(kpi_test_rs.read_bytes())
kpi_receipt_sha256 = sha(kpi_receipt_path.read_bytes())
mission_md_sha256 = sha(mission_md.read_bytes())

mission_pin_diagnostics_rs = "4ec366110c523f30e285dd3cbca08fd199f28edb06560897cf7e17e7abe7dd89"
probe_main_sha256 = sha((WORK / "void_corpus_probe_main.rs").read_bytes())

# --- refutation criterion (self-authored per ROTATION-mode rules: attack the
# strongest standing claim; the claim itself is the refutation criterion holder) ---
refutation_criterion_verbatim = (
    "mission.md: 'Its falsifiable hypothesis is that a locked adversarial corpus "
    "detects malformed envelopes and authority escalation.' KPI receipt metric "
    "'diagnostic_passed_flag_true_rate' note: 'Primary tamper-detection metric. Any "
    "embedded-fixture drift, per-module invariant break, or count-threshold miss "
    "drops this below 1.0.' Refutation observation: for the amphora-redteam-audit "
    "module's own dispatched inner diagnostic (redteam_diagnostic()), demonstrate "
    "that its REJECT/authority_granted_count=0 result is a structural invariant of "
    "the corpus-generation code, independent of any real defense outcome -- i.e. "
    "that no embedded fixture, no external authorization call, and no real "
    "authority-escalation event feeds this diagnostic's pass/fail decision at all."
)

# Empirical + independent-rederivation observation
observed = {
    "empirical_probe_authority_granted_count": probe_run1["details"]["authority_granted_count"],
    "empirical_probe_all_negative_states_rejected": probe_run1["details"]["all_negative_states_rejected"],
    "empirical_probe_passed": probe_run1["passed"],
    "empirical_probe_result_digest": probe_run1["details"]["result_digest"],
    "empirical_matches_pinned_receipt_result_digest": (
        probe_run1["details"]["result_digest"]
        == "c3531c5b945372916c88c379a1f4f60f6a17dae14d6141f664dc6e91356a66a8"
    ),
    "zero_function_parameters": static_analysis["zero_parameters"],
    "no_io_or_external_authorization_calls": static_analysis["no_io_or_external_calls_in_function_body"],
    "granted_is_single_hardcoded_constant_false": static_analysis["granted_is_single_hardcoded_constant_false"],
    "rejected_is_pure_mask_nonzero_check": static_analysis["rejected_is_pure_mask_nonzero_check"],
    "independent_python_rederivation_all_masks_nonzero_by_construction": rederivation["all_masks_nonzero_by_construction"],
    "independent_python_corpus_sha256_matches_live_rust": rederivation["matches_live_rust_corpus_sha256"],
}

refutation_observation_occurred = all([
    observed["empirical_probe_authority_granted_count"] == 0,
    observed["empirical_probe_all_negative_states_rejected"] is True,
    observed["empirical_probe_passed"] is True,
    observed["empirical_matches_pinned_receipt_result_digest"] is True,
    observed["zero_function_parameters"] is True,
    observed["no_io_or_external_authorization_calls"] is True,
    observed["granted_is_single_hardcoded_constant_false"] is True,
    observed["rejected_is_pure_mask_nonzero_check"] is True,
    observed["independent_python_rederivation_all_masks_nonzero_by_construction"] is True,
    observed["independent_python_corpus_sha256_matches_live_rust"] is True,
])
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
    "schema": "amphora.redteam-audit.y-voidcorpus-diagnostic-tautology-receipt.v1",
    "receipt_id": "y-voidcorpus-diagnostic-tautology-v1",
    "authority": "AUDIT_ONLY",
    "run_type": "FALSIFICATION_ATTACK",
    "module": "amphora-redteam-audit",
    "campaign_item_id": "Y-VOIDCORPUS",
    "fire_id": FIRE_ID,
    "mode": "ROTATION",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_other_module_files": False,
    "modifies_amphora_core_or_diagnostics_rs": False,
    "claim_under_attack": {
        "kpi_receipt_path": "amphora-redteam-audit/evidence/phase0/kpis/redteam-audit-deterministic-control-diagnostic-kpi.v1.json",
        "kpi_receipt_sha256_at_attack_time": kpi_receipt_sha256,
        "kpi_metric_targeted": "diagnostic_passed_flag_true_rate",
        "kpi_metric_note_verbatim": (
            "Fraction where returned DeterministicControlDiagnosticV1.passed == true. "
            "Primary tamper-detection metric. Any embedded-fixture drift, per-module "
            "invariant break, or count-threshold miss drops this below 1.0. Nine "
            "modules, all passed."
        ),
        "mission_md_path": "amphora-redteam-audit/docs/mission.md",
        "mission_md_sha256_at_attack_time": mission_md_sha256,
        "mission_md_claim_verbatim": (
            "Its falsifiable hypothesis is that a locked adversarial corpus detects "
            "malformed envelopes and authority escalation."
        ),
        "scope": (
            "Targets specifically the amphora-redteam-audit module's OWN dispatched "
            "inner diagnostic (module_id='amphora-redteam-audit', function "
            "redteam_diagnostic()), which is 1 of the 9 modules aggregated into "
            "diagnostic_passed_flag_true_rate and supplies the '30,000 negative "
            "controls' and '24/24 attack axes' figures cited in mission.md's Current "
            "benchmark result section."
        ),
    },
    "pre_registered_refutation_criterion_verbatim": refutation_criterion_verbatim,
    "refutation_criterion_observation_occurred": refutation_observation_occurred,
    "attack_description": (
        "Source-level + empirical + independent-rederivation audit of "
        f"redteam_diagnostic() in amphora-assurance-capabilities/src/diagnostics.rs "
        f"(whole-file SHA-256 {diagnostics_rs_sha256}, matching mission.md's benchmark "
        f"pin {mission_pin_diagnostics_rs}), lines "
        f"{static_analysis['function_line_range_1indexed'][0]}-"
        f"{static_analysis['function_line_range_1indexed'][1]}. Three independent "
        "legs: (1) static analysis (work/static_analysis.json) of the live tracked "
        "source, mechanically confirming the function signature takes zero "
        "parameters, its body contains no include_bytes!/std::fs/amphora_core:: call "
        "or any other I/O or external-authorization call, `rejected` is defined "
        "purely as `mask != 0`, and `granted` is assigned exactly once via the "
        "single hardcoded literal `let granted = false;` -- never derived from "
        "`mask`, `index`, or any other runtime value; (2) an independent Python "
        "re-derivation (work/independent_rederivation.json) of the documented "
        "corpus-generation algorithm ('singletons-then-pairs-then-ascending-masks-"
        "popcount-gte-3-v1'), built from the algorithm name plus a separate reading "
        "of the source, proving mathematically that 0 of the 30,000 generated masks "
        "can ever equal zero (singletons are 1<<axis for axis in 0..24, always "
        "non-zero; pairs OR two non-zero bits; the ascending-mask fill only accepts "
        "popcount>=3 candidates, all non-zero by definition) -- this Python model's "
        "corpus_sha256 digest, computed over the exact same textual encoding the "
        "Rust function hashes, is byte-identical to the live Rust run's corpus_sha256 "
        "(both "
        f"{rederivation['independent_python_corpus_sha256']}), proving the model is a "
        "faithful reproduction, not a strawman; (3) a live empirical run "
        "(work/probe_run1.json, work/probe_run2.json, byte-identical across two "
        "back-to-back replays) of the real, unmodified, compiled "
        "amphora_assurance_capabilities::deterministic_control_diagnostic"
        "('amphora-redteam-audit') via a standalone /tmp cargo project that path-"
        "depends on the real crate (never a workspace member, never edits the crate), "
        "confirming authority_granted_count=0, all_negative_states_rejected=true, "
        "passed=true, and a result_digest "
        "(c3531c5b945372916c88c379a1f4f60f6a17dae14d6141f664dc6e91356a66a8) that "
        "matches the module's own already-signed benchmark receipt "
        "(amphora-redteam-audit/evidence/phase0/benchmark/result.v1.json), "
        "confirming this is the exact live code path already relied upon, not a "
        "reconstruction that merely resembles it."
    ),
    "baseline": {
        "command": "cargo test --offline -p amphora-assurance-capabilities --test redteam_audit_phase0_kpi",
        "result": "ok. 1 passed; 0 failed",
        "confirms_claim_under_attack_is_live_and_currently_true": baseline_passed,
        "log_path": "work/baseline_cargo_test.log",
        "diagnostics_rs_sha256_matches_mission_md_benchmark_pin": diagnostics_rs_sha256 == mission_pin_diagnostics_rs,
    },
    "observed": observed,
    "static_analysis": static_analysis,
    "independent_rederivation": rederivation,
    "interpretation": (
        f"{verdict}. mission.md's stated falsifiable hypothesis is that 'a locked "
        "adversarial corpus detects malformed envelopes and authority escalation,' "
        "and the KPI receipt's diagnostic_passed_flag_true_rate metric is labelled "
        "the 'Primary tamper-detection metric' whose floor of 1.0 is only supposed "
        "to hold because 'any embedded-fixture drift, per-module invariant break, or "
        "count-threshold miss drops this below 1.0.' For 8 of the 9 dispatched "
        "modules that is true: each reads real include_bytes!-embedded fixture JSON "
        "and compares observed outcomes to hardcoded expectations, so a real defect "
        "(a mutated fixture, a broken parser, a wrong count) can genuinely flip "
        "`passed` to false. For the amphora-redteam-audit module's OWN entry -- "
        "which supplies exactly the '30,000 negative controls' and 'authority "
        "escalation' axis coverage the mission.md prose highlights -- this is false. "
        "redteam_diagnostic() reads no fixture, calls no external authorization "
        "function, and takes no argument at all: its REJECT verdict is the "
        "tautology `mask != 0` over a self-generated corpus that is non-zero by "
        "construction, and its authority_granted_count is a hardcoded `false` "
        "literal wired to nothing. No real DSSE forgery, registry tampering, or "
        "authority escalation anywhere in the actual system -- including the kind "
        "the module's own prior T-11 finding demonstrated is achievable in "
        "amphora-core's real authorize_optimizer_request -- could ever move this "
        "diagnostic's passed flag, authority_granted_count, or "
        "all_negative_states_rejected fields, because none of them are wired to any "
        "external input. The module's headline claim -- that its locked adversarial "
        "corpus 'detects... authority escalation' -- is refuted for its own "
        "dispatched self-diagnostic: the corpus detects nothing; it recomputes a "
        "closed-form combinatorial identity over axis NAMES and reports the only "
        "answer it is structurally capable of reporting, regardless of whether any "
        "actual attack in any of the 24 named axes succeeds elsewhere in the "
        "portfolio."
    ),
    "does_not_close": [
        "Does not establish that any of the OTHER 8 dispatched module diagnostics "
        "(evidence-intake, source-ledger, report-packager, formulation-arithmetic, "
        "formulation-universe, envelope-gates, cro-protocol-packager, "
        "optimizer-orchestrator) share this specific defect -- those were read "
        "structurally (each parses real include_bytes! fixture JSON) but not each "
        "independently re-derived this fire; a follow-up sweep across all 9 would "
        "generalize or bound this finding.",
        "Does not propose or land a repair (e.g. wiring `granted` to a real "
        "authorization probe, or introducing an externally-pinned, independently "
        "sourced attack-axis ground truth that the self-generated corpus is checked "
        "against rather than only itself) -- out of scope for this ROTATION-mode "
        "attack fire; a natural next campaign item would repair redteam_diagnostic() "
        "to actually exercise real envelope/authorization code paths per axis, "
        "analogous to how the other 8 dispatched diagnostics already do.",
        "Does not modify amphora-assurance-capabilities/src/diagnostics.rs, "
        "amphora-core, the master manifest, or any signed Phase-0 KPI -- the finding "
        "is demonstrated entirely via a standalone /tmp path-dependency probe plus "
        "read-only static analysis of the live tracked file.",
        "Does not certify Phase-1/Phase-2 promotion, scientific validity, "
        "procurement, legal, safety, or release authority for any module. "
        "AUDIT_ONLY.",
    ],
    "reproducibility": {
        "two_replay_probe_stdout_byte_identical": probe_byte_identical,
        "probe_run1_sha256": sha(probe_run1_bytes),
        "probe_run2_sha256": sha(probe_run2_bytes),
        "probe_main_rs_sha256": probe_main_sha256,
        "probe_main_rs_path": "work/void_corpus_probe_main.rs",
        "probe_cargo_toml_path": "work/probe_Cargo.toml",
        "static_analysis_script_path": "work/static_analysis.json",
        "independent_rederivation_path": "work/independent_rederivation.json",
        "build_command": "cargo build --release (standalone crate at /tmp/rta_probe, path deps only, never added to the workspace)",
        "run_command": "./target/release/rta_probe (run twice, diffed byte-identical)",
        "diagnostics_rs_sha256_at_attack_time": diagnostics_rs_sha256,
        "kpi_test_rs_sha256_at_attack_time": kpi_test_rs_sha256,
    },
    "toolchain": {
        "rust": "workspace edition 2021, cargo build --release (standalone /tmp probe crate)",
        "python": "3, stdlib json/hashlib/re + cryptography.hazmat Ed25519",
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under evidence/phase0/repairs/Y-VOIDCORPUS/done/",
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
ptype = "application/vnd.amphora.redteam-audit-y-voidcorpus-diagnostic-tautology+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}

OUT_DIR.mkdir(parents=True, exist_ok=True)
out = OUT_DIR / "y-voidcorpus-diagnostic-tautology-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))

print("WROTE", out)
print("verdict", verdict)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("refutation_criterion_observation_occurred", refutation_observation_occurred)
print("signature_verified", True)
print("envelope_sha256", sha(out.read_bytes()))
