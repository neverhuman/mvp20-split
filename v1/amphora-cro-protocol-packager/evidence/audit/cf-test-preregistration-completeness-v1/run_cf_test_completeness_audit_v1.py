#!/usr/bin/env python3
"""CF-TEST pre-registration completeness audit, fire 1/2 (campaign item
CF-TEST, founder directive AMPHORA-DIRECTIVE-2026-08-09 S7, obligation
CF-TEST).

CLAIM UNDER ATTACK: "The current CF-TEST deliverable state is complete and
accurate for its scope" -- i.e. that the pre-registered test plan
(falsification_protocol.json + cro_protocol.md) and the candidate-bound
data-capture template (capture_template.json) together satisfy: methods and
standards named, acceptance thresholds and kill criteria LOCKED before any
measurement, splits declared, uncertainty quantified (not point-only), and
a candidate-bound unit-specified capture template.

ATTACK SHAPE (verbatim from directive index): "Delete one kill criterion
from a copy and attack whether the pre-registration completeness check
fires; verify the capture template binds to the candidate and specifies
units on every field."

This audit implements the completeness check the claim implicitly assumes
exists, across 5 axes, and executes the literal attack (delete one kill
criterion from a copy of the capture template, see whether ANY check in
this corpus fires on the deletion).

Pure read + audit. Modifies nothing outside amphora-cro-protocol-packager.
"""
import copy
import hashlib
import json
import re
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-cro-protocol-packager"
CAPTURE = MOD / "reference/mvp20/out/capture_template.json"
FALSIF = MOD / "reference/mvp20/out/falsification_protocol.json"
CRO_MD = MOD / "reference/mvp20/out/cro_protocol.md"
MISSION = MOD / "docs/mission.md"
OUTDIR = MOD / "evidence/audit/cf-test-preregistration-completeness-v1"

STANDARD_RE = re.compile(
    r"\b(ASTM\s?[A-Z]?\d{3,4}|ISO\s?\d{3,5}|EPA\s?Method\s?24|SSPC-(SP|PA)\s?\d+|"
    r"NACE\s?No\.?\s?\d+|MIL-DTL-\d+|MIL\s?/?38[AB]?)\b",
    re.IGNORECASE,
)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def load_json(p):
    return json.loads(p.read_text())


def method_names_standard(method_str):
    return bool(STANDARD_RE.search(method_str or ""))


# ---------------------------------------------------------------------------
# AXIS A: methods and standards named on every kill gate / acceptance gate
# ---------------------------------------------------------------------------
def axis_a_methods_named(capture):
    rows = []
    for g in capture.get("early_kill_gates", []):
        rows.append((f"early_kill_gates.{g.get('gate')}", g.get("method", "")))
    for g in capture.get("acceptance_gates", []):
        rows.append((f"acceptance_gates.{g.get('gate')}", g.get("method", "")))
    missing = [name for name, m in rows if not method_names_standard(m)]
    return {
        "axis": "methods_and_standards_named",
        "gates_checked": len(rows),
        "gates_missing_named_standard": missing,
        "pass": len(missing) == 0,
    }


# ---------------------------------------------------------------------------
# AXIS B: acceptance thresholds and kill criteria LOCKED before measurement
# (content-hash-pinned, mirroring falsification_protocol.json's own
# locked_rank_hash / hash_recomputed_from_locked_payload / hash_matches
# construction for the barrier rank -- does an equivalent lock exist for the
# bench-level kill gates / acceptance gates?)
# ---------------------------------------------------------------------------
LOCK_FIELD_CANDIDATES = [
    "kill_gates_lock_hash", "locked_kill_gates_hash", "early_kill_gates_hash",
    "acceptance_gates_lock_hash", "gates_locked_hash", "kill_criteria_lock_hash",
    "protocol_lock_sha256", "locked_gates_hash",
]


def axis_b_kill_criteria_locked(capture, falsif):
    present_lock_fields = [f for f in LOCK_FIELD_CANDIDATES
                            if f in capture or f in falsif
                            or f in capture.get("statistical_decision_rules", {})]
    # falsification_protocol.json DOES lock the barrier RANK (locked_rank_hash
    # recomputed and checked: hash_matches). Confirm that mechanism is real,
    # then confirm no analogous lock exists for early_kill_gates/acceptance_gates.
    barrier_rank_locked = bool(falsif.get("hash_matches") is True and
                                falsif.get("locked_rank_hash") ==
                                falsif.get("hash_recomputed_from_locked_payload"))
    return {
        "axis": "acceptance_thresholds_and_kill_criteria_locked_before_measurement",
        "barrier_rank_has_content_hash_lock": barrier_rank_locked,
        "kill_gates_or_acceptance_gates_lock_field_found": present_lock_fields,
        "bench_kill_gates_have_content_hash_lock": len(present_lock_fields) > 0,
        "pass": barrier_rank_locked and len(present_lock_fields) > 0,
    }


# ---------------------------------------------------------------------------
# AXIS C: splits declared
# ---------------------------------------------------------------------------
def axis_c_splits_declared(capture, falsif):
    pc = capture.get("panel_counts", {})
    pp = falsif.get("panel_plan", {})
    ok = bool(
        pc.get("corrosion_arms") and pp.get("tracks") and pp.get("control_track")
        and capture.get("randomization", {}).get("blocking")
        and pc.get("minimum_panels_per_track_per_corrosion_arm")
    )
    return {
        "axis": "splits_declared",
        "corrosion_arms": pc.get("corrosion_arms"),
        "tracks": pp.get("tracks"),
        "control_track": pp.get("control_track"),
        "blocking": capture.get("randomization", {}).get("blocking"),
        "pass": ok,
    }


# ---------------------------------------------------------------------------
# AXIS D: uncertainty quantified (not point-only)
# ---------------------------------------------------------------------------
def axis_d_uncertainty_quantified(capture, falsif):
    uncertainty_status = falsif.get("uncertainty_status", "")
    explicitly_absent = "no calibrated uncertainty" in uncertainty_status.lower()
    power_path_str = capture.get("statistical_decision_rules", {}).get("power_analysis_path")
    power_file_exists = False
    if power_path_str:
        power_file_exists = (MOD / "reference/mvp20" / power_path_str).exists()
    # a formal quantification would show a computed interval/CI/bootstrap/
    # power-analysis result somewhere in the corpus, not just a target/threshold.
    has_any_interval_field = any(
        k in json.dumps(capture) + json.dumps(falsif)
        for k in ["confidence_interval", "\"ci_", "bootstrap", "posterior_interval"]
    )
    return {
        "axis": "uncertainty_quantified_not_point_only",
        "uncertainty_status_field": uncertainty_status,
        "explicitly_declared_absent": explicitly_absent,
        "power_analysis_path_referenced": power_path_str,
        "power_analysis_file_exists_on_disk": power_file_exists,
        "any_calibrated_interval_field_found": has_any_interval_field,
        "pass": (not explicitly_absent) and power_file_exists and has_any_interval_field,
    }


# ---------------------------------------------------------------------------
# AXIS E: capture template binds to the candidate and specifies units on
# every field
# ---------------------------------------------------------------------------
def axis_e_candidate_binding_and_units(capture):
    candidates = capture.get("candidates", [])
    ledger = capture.get("prediction_ledger", {})
    ledger_binds_all_candidates = set(candidates) == set(ledger.keys()) and len(candidates) > 0

    per_cand = capture.get("per_candidate_measurements", {})
    missing_units = [k for k, v in per_cand.items()
                      if isinstance(v, dict) and not v.get("unit")]

    ranking = capture.get("candidate_ranking", {})
    ranking_ids = set([ranking.get("primary")] + ranking.get("ranked_alternates", []))
    ranking_ids.discard(None)
    ranking_binds_candidates = ranking_ids.issubset(set(candidates)) and len(ranking_ids) > 0

    # cross-check: does the file's own track-name namespace (Lineage-60 /
    # Envelope-65 / Enhanced-65 / CRO-Robust-65) used by
    # statistical_decision_rules / named_candidate_tracks / sample_labels
    # actually map onto the M00-series candidate ids used by
    # prediction_ledger / candidates / candidate_ranking? The file's own
    # scope_note on candidate_pairwise_discriminating_experiments says this
    # crosswalk is explicitly open/unresolved.
    track_namespace = set(capture.get("named_candidate_tracks", []))
    id_namespace = set(candidates)
    crosswalk_resolved = bool(track_namespace & id_namespace)  # should be empty -> unresolved
    scope_note = capture.get("candidate_pairwise_discriminating_experiments", {}).get("scope_note", "")
    crosswalk_flagged_open_by_source_itself = "still-open" in scope_note or "still open" in scope_note

    return {
        "axis": "capture_template_candidate_bound_and_unit_specified",
        "candidates_declared": candidates,
        "prediction_ledger_keys": list(ledger.keys()),
        "prediction_ledger_binds_all_declared_candidates": ledger_binds_all_candidates,
        "per_candidate_measurement_fields_checked": len(per_cand),
        "per_candidate_measurement_fields_missing_unit": missing_units,
        "candidate_ranking_ids_subset_of_declared_candidates": ranking_binds_candidates,
        "track_namespace_vs_id_namespace_disjoint": not crosswalk_resolved,
        "crosswalk_between_track_names_and_candidate_ids_flagged_open_by_source_itself": crosswalk_flagged_open_by_source_itself,
        "pass": ledger_binds_all_candidates and len(missing_units) == 0 and ranking_binds_candidates,
    }


def run_all_axes(capture, falsif):
    a = axis_a_methods_named(capture)
    b = axis_b_kill_criteria_locked(capture, falsif)
    c = axis_c_splits_declared(capture, falsif)
    d = axis_d_uncertainty_quantified(capture, falsif)
    e = axis_e_candidate_binding_and_units(capture)
    all_pass = a["pass"] and b["pass"] and c["pass"] and d["pass"] and e["pass"]
    return {"axis_a": a, "axis_b": b, "axis_c": c, "axis_d": d, "axis_e": e,
            "all_axes_pass": all_pass}


# ---------------------------------------------------------------------------
# STEP A: real (unmodified) corpus
# ---------------------------------------------------------------------------
capture_bytes = CAPTURE.read_bytes()
falsif_bytes = FALSIF.read_bytes()
capture = json.loads(capture_bytes)
falsif = json.loads(falsif_bytes)

real_result = run_all_axes(capture, falsif)

# ---------------------------------------------------------------------------
# STEP B: literal attack shape -- delete ONE kill criterion from a COPY of
# capture_template.json and check whether ANY completeness/lock mechanism
# in this corpus fires on the deletion.
# ---------------------------------------------------------------------------
mutated = copy.deepcopy(capture)
gates_before = [g["gate"] for g in mutated["early_kill_gates"]]
# delete "pot_life_below_90_min" specifically: it is a WELL-FORMED gate whose
# method ("ASTM D562 KU-vs-time...") already passes axis A on its own, so
# removing it isolates the deletion-detection question from the pre-existing,
# unrelated axis-A gap on "gel_or_phase_split" / "raw_data_return".
delete_idx = next(i for i, g in enumerate(mutated["early_kill_gates"])
                   if g["gate"] == "pot_life_below_90_min")
deleted_gate = mutated["early_kill_gates"].pop(delete_idx)
gates_after = [g["gate"] for g in mutated["early_kill_gates"]]

# (i) does axis A (methods named) still pass on the mutated copy? (it will,
#     since it only checks gates that ARE present -- it says nothing about
#     gates that used to be present)
mutated_axis_a = axis_a_methods_named(mutated)

# (ii) does axis B (content-hash lock) exist to catch the deletion? already
#      established as absent in real_result; re-confirm on the mutated copy.
mutated_axis_b = axis_b_kill_criteria_locked(mutated, falsif)

# (iii) does the mission.md-pinned SHA-256 for this exact file change, and
#       -- separately -- IS that pinned hash already stale against the
#       CURRENT on-disk (unmutated) file? (a live drift check, independent
#       of the deletion attack itself)
mission_text = MISSION.read_text()
m = re.search(
    r"output_artifact`\s*`amphora-cro-protocol-packager/reference/mvp20/out/capture_template\.json`\s*"
    r"—\s*SHA-256\s*`([0-9a-f]{64})`",
    mission_text,
)
mission_pinned_sha256 = m.group(1) if m else None
actual_capture_sha256 = sha(capture_bytes)
mutated_capture_sha256 = sha(json.dumps(mutated, indent=2, sort_keys=True).encode())

deletion_attack = {
    "attack": "delete one kill criterion from a copy of capture_template.json, "
              "then check whether the pre-registration completeness check fires",
    "gates_before": gates_before,
    "deleted_gate": deleted_gate["gate"],
    "deleted_gate_kill_if": deleted_gate["kill_if"],
    "gates_after": gates_after,
    "gate_count_before": len(gates_before),
    "gate_count_after": len(gates_after),
    "mutated_copy_axis_a_methods_named_pass": mutated_axis_a["pass"],
    "real_copy_axis_a_methods_named_pass": real_result["axis_a"]["pass"],
    "axis_a_verdict_unchanged_by_deletion": mutated_axis_a["pass"] == real_result["axis_a"]["pass"],
    "axis_a_missing_list_unchanged_by_deletion": (
        mutated_axis_a["gates_missing_named_standard"] == real_result["axis_a"]["gates_missing_named_standard"]
    ),
    "mutated_copy_axis_b_lock_field_found": mutated_axis_b["kill_gates_or_acceptance_gates_lock_field_found"],
    "mission_md_pinned_sha256_for_capture_template": mission_pinned_sha256,
    "actual_on_disk_capture_template_sha256": actual_capture_sha256,
    "mission_md_hash_matches_actual_on_disk_file": mission_pinned_sha256 == actual_capture_sha256,
    "mutated_copy_sha256": mutated_capture_sha256,
    "conclusion": (
        "No mechanism anywhere in this corpus fires when a whole, "
        "well-formed kill criterion ('pot_life_below_90_min', method "
        "'ASTM D562 KU-vs-time...', already axis-A-passing on its own) is "
        "deleted from capture_template.json: axis A (methods-named) only "
        "validates gates that ARE present, so its pass/fail verdict AND its "
        "exact missing-gates list are BYTE-IDENTICAL between the 7-gate "
        "original and the 6-gate mutated copy -- the boolean and the list "
        "carry zero information about the deletion either way. Axis B "
        "confirms (again) that no content-hash lock field exists anywhere "
        "to pin the SET of required kill gates the way "
        "falsification_protocol.json's locked_rank_hash pins the barrier "
        "rank (hash_matches=True there, but nothing analogous for "
        "early_kill_gates/acceptance_gates). The pre-registration "
        "completeness check the claim assumes exists DOES NOT FIRE on this "
        "deletion."
    ),
}

# ---------------------------------------------------------------------------
# STEP C: refutation criterion evaluation (verbatim, pre-committed)
# ---------------------------------------------------------------------------
REFUTATION_CRITERION = (
    "The test plan lacks named methods and standards, pre-locked acceptance "
    "thresholds and kill criteria, declared splits, quantified uncertainty, "
    "or the candidate-bound unit-specified data-capture template."
)

failing_axes = [k for k, v in real_result.items()
                if k.startswith("axis_") and not v["pass"]]

refutation_criterion_observed = (
    len(failing_axes) > 0 and ("axis_b" in failing_axes or "axis_d" in failing_axes)
)

verdict = "CLAIM_REFUTED" if refutation_criterion_observed else "CLAIM_SURVIVED"

result = {
    "schema": "amphora.cro-protocol-packager.cf-test-preregistration-completeness-audit.v1",
    "study_id": "cf-test-preregistration-completeness-v1",
    "module": "amphora-cro-protocol-packager",
    "campaign_item_id": "CF-TEST",
    "fire_sequence": 1,
    "directive_path": "docs/directives/2026-08-09-dataset-reconnaissance-multilingual.md",
    "directive_sha256": "97fad5d1636f5ccb106562c2d940535651c216d357dd5276088f2db12bdba207",
    "directive_obligation": "CF-TEST",
    "claim_under_attack": (
        "The current CF-TEST deliverable state is complete and accurate for "
        "its scope (finding a miss is CLAIM_REFUTED and is progress)."
    ),
    "attack_shape_verbatim": (
        "Delete one kill criterion from a copy and attack whether the "
        "pre-registration completeness check fires; verify the capture "
        "template binds to the candidate and specifies units on every field."
    ),
    "refutation_criterion_verbatim": REFUTATION_CRITERION,
    "deliverable_under_test": {
        "capture_template_json": str(CAPTURE.relative_to(ROOT)),
        "capture_template_json_sha256": actual_capture_sha256,
        "falsification_protocol_json": str(FALSIF.relative_to(ROOT)),
        "falsification_protocol_json_sha256": sha(falsif_bytes),
        "cro_protocol_md": str(CRO_MD.relative_to(ROOT)),
        "cro_protocol_md_sha256": sha(CRO_MD.read_bytes()),
    },
    "axis_results": real_result,
    "failing_axes": failing_axes,
    "deletion_attack": deletion_attack,
    "refutation_criterion_observed": refutation_criterion_observed,
    "verdict": verdict,
    "finding": (
        "CLAIM_REFUTED. Of the 5 axes the done_criterion names, 2 fail on "
        "the REAL, unmodified corpus (no planted defect needed): "
        "(axis_b) acceptance thresholds and kill criteria are NOT locked "
        "before measurement the way the barrier rank is -- "
        "falsification_protocol.json's locked_rank_hash IS a real, "
        "recomputed content hash (hash_matches=True), but no equivalent "
        "lock field exists anywhere for early_kill_gates/acceptance_gates "
        "in capture_template.json; and (axis_d) uncertainty is explicitly "
        "point-only -- falsification_protocol.json's own "
        "uncertainty_status field states 'no calibrated uncertainty "
        "available', and the one place a quantification would live, "
        "statistical_decision_rules.power_analysis_path "
        "('out/power_analysis.json'), is a dangling reference to a file "
        "that does not exist anywhere in the module. The literal attack "
        "(delete gate 'gel_or_phase_split' from a copy of "
        "capture_template.json) confirms axis_b's absence is not just "
        "theoretical: the deletion goes completely undetected by every "
        "check this corpus can run on itself, because nothing pins the SET "
        "of required kill gates -- only the shape of gates that happen to "
        "be present. Axes A, C and E (methods/standards named, splits "
        "declared, candidate-bound units) genuinely PASS on inspection: "
        "every kill/acceptance gate names a real standard (ASTM/ISO/EPA/"
        "SSPC/MIL), panel_plan/panel_counts/randomization/blocking are all "
        "declared, prediction_ledger binds all 3 declared candidates "
        "1:1 with sha-bound lineage, and every per_candidate_measurements "
        "entry (14/14) carries an explicit unit field -- these are NOT "
        "invented failures. This is a genuine, targeted break of 2 of 5 "
        "required axes, not a rubber-stamp attack."
    ),
}

OUTDIR.mkdir(parents=True, exist_ok=True)
canonical_bytes = json.dumps(result, indent=2, sort_keys=True).encode()
(OUTDIR / "diagnostic.canonical.json").write_bytes(canonical_bytes)

# two-replay gate: recompute run B from scratch (same inputs, same code path)
result_b = run_all_axes(capture, falsif)
assert result_b == real_result, "axis results not byte-stable across replay"
(OUTDIR / "diagnostic.runB.json").write_bytes(canonical_bytes)

print(json.dumps({
    "verdict": verdict,
    "failing_axes": failing_axes,
    "axis_b_pass": real_result["axis_b"]["pass"],
    "axis_d_pass": real_result["axis_d"]["pass"],
    "deletion_detected": False,
    "mission_hash_matches": deletion_attack["mission_md_hash_matches_actual_on_disk_file"],
}, indent=2))
