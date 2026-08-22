#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-cro-protocol-packager CF-TEST repair
receipt, fire 2/2 (campaign item CF-TEST, founder directive
AMPHORA-DIRECTIVE-2026-08-09 S7, obligation CF-TEST, max_fires=2, final
fire for this item).

Repairs the 3 axes fire 1's CLAIM_REFUTED receipt found failing (A, B, D)
and re-runs the SAME unmodified checker
(run_cf_test_completeness_audit_v1.py, sha256
a0af1a4c4016a4f19d7f144bdd2d350798e98f76837ae3d2cd2ae034410daf71) against
the repaired corpus as the acceptance test, per REPAIR MODE rule 2
(re-attack your own fix with the same script/command/thresholds). All 5
axes now pass -> CLAIM_SURVIVED (repaired). Filed to
evidence/phase0/repairs/CF-TEST/done/ -- the done_criterion is met.

Does not supersede fire 1's receipt: fire 1's finding was true of the
pre-repair state and remains the accurate historical record. This receipt
documents the truthful CURRENT (post-repair) state.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-cro-protocol-packager"
BENCH = MOD / "evidence/audit/cf-test-preregistration-completeness-v1"
DONE_DIR = MOD / "evidence/phase0/repairs/CF-TEST/done"
ATTEMPTS_DIR = MOD / "evidence/phase0/repairs/CF-TEST/attempts"
WORK_DIR = MOD / "evidence/phase0/repairs/CF-TEST/work"
OUT = MOD / "reference/mvp20/out"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"


def sha(b):
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


# --- two-replay gate (post-repair re-run of the UNCHANGED v1 checker) -------
canon = (BENCH / "diagnostic.canonical.json").read_bytes()
runB = (BENCH / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag = json.loads(canon)
assert diag["verdict"] == "CLAIM_SURVIVED"
assert diag["failing_axes"] == []
harness_sha = sha((BENCH / "run_cf_test_completeness_audit_v1.py").read_bytes())
assert harness_sha == "a0af1a4c4016a4f19d7f144bdd2d350798e98f76837ae3d2cd2ae034410daf71", "checker script changed -- not the same acceptance test as fire 1"

# --- independent verification beyond the checker's own (presence-only)
# axis-B test: does the new gates_lock hash actually change if the fire-1
# attack's exact gate is deleted from a copy? (this is the positive control:
# real input -> hash matches / no false fire; mutated copy with the SAME
# KIND of defect the item's attack shape names -> hash mismatch / fires)
capture = json.loads((OUT / "capture_template.json").read_bytes())


def lock_hash(payload):
    return sha(json.dumps(payload, sort_keys=True).encode())


real_payload = {"early_kill_gates": capture["early_kill_gates"], "acceptance_gates": capture["acceptance_gates"]}
real_hash = lock_hash(real_payload)
assert real_hash == capture["locked_gates_hash"], "locked_gates_hash does not match its own payload"
assert capture["gates_lock"]["hash_matches"] is True

import copy
mutated = copy.deepcopy(capture)
del_idx = next(i for i, g in enumerate(mutated["early_kill_gates"]) if g["gate"] == "pot_life_below_90_min")
deleted_gate = mutated["early_kill_gates"].pop(del_idx)
mutated_payload = {"early_kill_gates": mutated["early_kill_gates"], "acceptance_gates": mutated["acceptance_gates"]}
mutated_hash = lock_hash(mutated_payload)
deletion_now_detected = mutated_hash != capture["locked_gates_hash"]
assert deletion_now_detected, "gates_lock hash failed to change on the same deletion fire 1 used -- repair did not close the gap"

positive_control = {
    "planted_defect": "deleted the well-formed early_kill_gates entry 'pot_life_below_90_min' "
                       "(the SAME gate fire 1's literal attack deleted) from a deepcopy of the "
                       "repaired capture_template.json",
    "how_planted": "capture_template.json.early_kill_gates: removed the dict where gate=='pot_life_below_90_min' "
                   f"(kill_if='{deleted_gate['kill_if']}') from the list in a deepcopy; recomputed "
                   "sha256(json.dumps({'early_kill_gates':..., 'acceptance_gates':...}, sort_keys=True)"
                   ".encode()).hexdigest() over the mutated arrays and compared to the file's own "
                   "locked_gates_hash field",
    "real_input_result": {
        "locked_gates_hash_field": capture["locked_gates_hash"],
        "recomputed_from_current_unmutated_arrays": real_hash,
        "matches": real_hash == capture["locked_gates_hash"],
        "interpretation": "on the REAL, unmodified repaired corpus the lock is internally consistent -- no false fire",
    },
    "mutated_copy_result": {
        "recomputed_from_mutated_arrays": mutated_hash,
        "locked_gates_hash_field": capture["locked_gates_hash"],
        "matches": mutated_hash == capture["locked_gates_hash"],
        "interpretation": "on a copy with the SAME KIND of defect the item's attack shape names (delete one "
                           "kill criterion), the recomputed hash no longer matches the locked hash -- the "
                           "deletion is now detected, closing the exact gap fire 1 demonstrated was silent "
                           "(fire 1: methods-named check's pass/fail verdict AND missing-gates list were "
                           "byte-identical before/after this same deletion)",
    },
    "detected": bool(deletion_now_detected),
    "evidence": f"real_hash={real_hash} == locked_gates_hash ({real_hash == capture['locked_gates_hash']}); "
                f"mutated_hash={mutated_hash} != locked_gates_hash ({mutated_hash != capture['locked_gates_hash']})",
}

repair_actions = [
    {
        "axis": "axis_a_methods_and_standards_named",
        "action": "named an external standard on the 2 gates fire 1 found missing one",
        "changes": [
            {"path": "capture_template.json#early_kill_gates[gate=gel_or_phase_split].method",
             "before": "visual check plus KU trend during induction and first 90 min",
             "after": "visual check plus ASTM D562 KU trend during induction and first 90 min",
             "justification": "KU-vs-time trend tracking is literally an ASTM D562 Stormer-viscometer measurement, "
                               "already the cited method for the file's own pot_life_below_90_min gate and "
                               "per_candidate_measurements.ku_vs_time_3temps -- not a new/uncited standard."},
            {"path": "capture_template.json#acceptance_gates[gate=raw_data_return].method",
             "before": "CRO data package audit",
             "after": "CRO data package audit against ISO 17025 record-completeness, traceability and calibration-record requirements",
             "justification": "ISO/IEC 17025:2017 (General requirements for the competence of testing and "
                               "calibration laboratories) is the standard governing raw data record completeness, "
                               "traceability and calibration records in a testing-lab context, which is exactly "
                               "this gate's raw_data_required list (complete return_schema, chain of custody, "
                               "randomization map, calibration records)."},
        ],
    },
    {
        "axis": "axis_b_acceptance_thresholds_and_kill_criteria_locked_before_measurement",
        "action": "added a real content-hash lock over early_kill_gates+acceptance_gates, mirroring "
                  "falsification_protocol.json's own locked_rank_hash construction",
        "new_fields": ["capture_template.json#locked_gates_hash", "capture_template.json#gates_lock"],
        "construction_verified_against_precedent": "empirically confirmed falsification_protocol.json's "
            "locked_rank_hash == sha256(json.dumps(locked_payload, sort_keys=True).encode()).hexdigest() "
            "(no indent, default separators) before reusing the identical construction for gates_lock",
        "locked_gates_hash": capture["locked_gates_hash"],
        "positive_control": positive_control,
    },
    {
        "axis": "axis_d_uncertainty_quantified_not_point_only",
        "action": "produced a real a priori power analysis (out/power_analysis.json) and restated "
                  "falsification_protocol.json's uncertainty_status honestly",
        "power_analysis_path": "amphora-cro-protocol-packager/reference/mvp20/out/power_analysis.json",
        "power_analysis_sha256": sha((OUT / "power_analysis.json").read_bytes()),
        "sigma_assumption_citation": "Floyd, F.L., Avudaiappan, S., Gibson, J., Mehta, B., Smith, P., Provder, T., "
            "Escarsega, J. (2009). \"Using electrochemical impedance spectroscopy to predict the corrosion "
            "resistance of unexposed coated metal panels.\" Progress in Organic Coatings, 66(1), 8-34. "
            "doi:10.1016/j.porgcoat.2009.04.009 -- documents EIS log-resistance replicate scatter on coated "
            "panels is real and substantial (~50% percent-SD, 3 independent estimation methods agreeing), "
            "used ONLY to ground the assumed sigma sensitivity range, not as a system-specific measured value "
            "(no EIS has been run on any MVP20 track/candidate yet).",
        "formula_citation": "Cohen, J. (1988). Statistical Power Analysis for the Behavioral Sciences (2nd ed.). "
            "Lawrence Erlbaum Associates. ISBN 978-0-8058-0283-2.",
        "old_uncertainty_status": "no calibrated uncertainty available",
        "new_uncertainty_status": json.loads((MOD / "reference/mvp20/out/falsification_protocol.json").read_bytes())["uncertainty_status"],
        "honest_caveat": "this is a PRE-MEASUREMENT, assumption-based a priori power/CI analysis, not a "
            "post-hoc calibrated interval from this system's own bench data -- no bench data exists yet. The "
            "pre-registered default panel count (6/track/arm) clears >=80% power at every assumed sigma tested "
            "(0.1-0.5); the pre-registered minimum floor (3/track/arm) drops to 68.8% power at the pessimistic "
            "end -- stated honestly, not hidden.",
    },
]

# --- derive public key / key_id from on-host seed ---------------------------
eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"

trust = json.loads(TRUST.read_text())
trust_by_role = {k.get("role"): k for k in trust["keys"]}
eval_derives_pin = (eval_key_id == trust_by_role.get("PHASE0_EVALUATOR", {}).get("key_id"))

REFUTATION_CRITERION = (
    "The test plan lacks named methods and standards, pre-locked acceptance thresholds and kill criteria, "
    "declared splits, quantified uncertainty, or the candidate-bound unit-specified data-capture template."
)

# --- receipt body -----------------------------------------------------------
body_obj = {
    "schema": "amphora.cro-protocol-packager.cf-test-preregistration-completeness-repair-receipt.v2",
    "study_id": "cf-test-preregistration-completeness-v1",
    "authority": "AUDIT_ONLY",
    "module": "amphora-cro-protocol-packager",
    "campaign_item_id": "CF-TEST",
    "run_type": "repair_and_reverify",
    "fire_sequence": 2,
    "final_fire_for_item": True,
    "directive_path": "docs/directives/2026-08-09-dataset-reconnaissance-multilingual.md",
    "directive_sha256": "97fad5d1636f5ccb106562c2d940535651c216d357dd5276088f2db12bdba207",
    "directive_obligation": "CF-TEST",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_pinned_fixture": False,
    "modifies_mission_front_matter": False,
    "modifies_mission_prose": True,
    "claim_under_attack": (
        "The current CF-TEST deliverable state is complete and accurate for its scope "
        "(finding a miss is CLAIM_REFUTED and is progress)."
    ),
    "attack_shape_verbatim": (
        "Delete one kill criterion from a copy and attack whether the pre-registration completeness check "
        "fires; verify the capture template binds to the candidate and specifies units on every field."
    ),
    "refutation_criterion_verbatim": REFUTATION_CRITERION,
    "prior_fire": {
        "fire_sequence": 1,
        "verdict": "CLAIM_REFUTED",
        "receipt": "amphora-cro-protocol-packager/evidence/audit/cf-test-preregistration-completeness-v1/cf-test-preregistration-completeness-audit-receipt.v1.dsse.json",
        "failing_axes_found": ["axis_a", "axis_b", "axis_d"],
        "status": "remains the true historical record of the pre-repair state; NOT superseded, only built upon "
                   "(the deliverable itself changed, not the fact that fire 1's finding was correct when made)",
    },
    "repair_mode": {
        "rule_applied": "REPAIR MODE (objective explicitly invokes it despite item id not carrying an R-/V- "
                        "prefix): supersede-never-rewrite (n/a here -- no signed artifact was rewritten, only "
                        "the underlying deliverable files the item's done_criterion is about); re-attack own "
                        "fix with SAME script sha256, same command, same thresholds; done receipt only into "
                        "done/ because the acceptance criterion is now met.",
        "acceptance_test": "re-ran evidence/audit/cf-test-preregistration-completeness-v1/"
                           "run_cf_test_completeness_audit_v1.py UNCHANGED (sha256 verified equal to fire 1's "
                           "pinned harness_script_sha256) against the repaired corpus",
        "acceptance_test_script_sha256": harness_sha,
    },
    "repair_actions": repair_actions,
    "deliverable_under_test": diag["deliverable_under_test"],
    "axis_results": diag["axis_results"],
    "failing_axes": diag["failing_axes"],
    "mission_md_hash_pin_now_matches": diag["deletion_attack"]["mission_md_hash_matches_actual_on_disk_file"],
    "finding": (
        "CLAIM_SURVIVED (repaired). Re-running the SAME unmodified checker fire 1 used against the repaired "
        "corpus, all 5 done_criterion axes now pass: axis A (2/18 gates that lacked a named standard now name "
        "one, both independently defensible -- ASTM D562 for a KU-trend visual+viscosity gate already using "
        "D562 elsewhere, ISO 17025 for a lab-record-completeness audit gate); axis B (a real sha256 content "
        "lock over early_kill_gates+acceptance_gates now exists, using the identical construction verified "
        "against falsification_protocol.json's own locked_rank_hash; independently re-verified beyond the "
        "checker's own presence-only test that deleting the exact gate fire 1's attack deleted now changes "
        "the recomputed hash -- see repair_actions[1].positive_control); axis C and E were already passing "
        "and are unchanged; axis D (a real, cited, formula-based a priori power analysis now exists at "
        "out/power_analysis.json, and uncertainty_status no longer falsely implies no quantification exists "
        "-- it honestly states this is pre-measurement and assumption-based, with the specific power/CI "
        "numbers and the minimum-floor-vs-default panel-count tradeoff stated plainly). This is a genuine "
        "repair verified by re-running the field's own falsifying checker unchanged, not a redefinition of "
        "the check."
    ),
    "verdict": "CLAIM_SURVIVED",
    "repair_status": "fix_landed_survived",
    "campaign_item_status": "done",
    "campaign_item_disposition": (
        "Fire 2/2 (final fire, max_fires=2) for CF-TEST. All 3 axes fire 1 refuted (A, B, D) are repaired and "
        "re-verified against the SAME unmodified checker; axes C and E remained passing throughout. "
        "done_criterion met: signed receipt filed to evidence/phase0/repairs/CF-TEST/done/."
    ),
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": sha(canon),
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "diagnostic_script_sha256": harness_sha,
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY repair receipt under evidence/audit/ and evidence/phase0/repairs/CF-TEST/done/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_derives_pin),
    },
}

body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.cro-protocol-packager-cf-test-preregistration-completeness-repair-receipt+json"
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

out = BENCH / "cf-test-preregistration-completeness-repair-receipt.v2.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

DONE_DIR.mkdir(parents=True, exist_ok=True)
done_out = DONE_DIR / "cf-test-preregistration-completeness-repair-receipt.v2.dsse.json"
done_out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

WORK_DIR.mkdir(parents=True, exist_ok=True)
state = {
    "campaign_item_id": "CF-TEST",
    "last_fire_sequence": 2,
    "last_verdict": "CLAIM_SURVIVED",
    "max_fires": 2,
    "final_fire_for_item": True,
    "failing_axes": [],
    "passing_axes": ["axis_a", "axis_b", "axis_c", "axis_d", "axis_e"],
    "harness_script_sha256": harness_sha,
    "deliverable_shas_at_this_fire": diag["deliverable_under_test"],
    "done_receipt": "amphora-cro-protocol-packager/evidence/phase0/repairs/CF-TEST/done/cf-test-preregistration-completeness-repair-receipt.v2.dsse.json",
    "next_fire_should": "none -- done_criterion met, item closed",
}
(WORK_DIR / "STATE.json").write_text(json.dumps(state, indent=2, sort_keys=True))

# --- self-verify -------------------------------------------------------------
pk = Ed25519PublicKey.from_public_bytes(eval_pub)
pk.verify(base64.standard_b64decode(envelope["signatures"][0]["sig"]),
          pae(ptype, base64.standard_b64decode(envelope["payload"])))
pk.verify(base64.standard_b64decode(json.loads(done_out.read_text())["signature"]["signatures"][0]["sig"]),
          pae(ptype, base64.standard_b64decode(json.loads(done_out.read_text())["signature"]["payload"])))

print("WROTE", out)
print("WROTE", done_out)
print("WROTE", WORK_DIR / "STATE.json")
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_derives_pin)
print("receipt_body_sha256", sha(body))
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
print("deletion_now_detected", deletion_now_detected)
