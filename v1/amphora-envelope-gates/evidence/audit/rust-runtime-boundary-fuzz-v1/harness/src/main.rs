// rust-runtime-boundary-fuzz-v1: amphora-envelope-gates audit.
//
// Both T-03 (2026-08-05) and kpi-claim-currency-v1 (2026-08-15) explicitly
// scoped themselves to the retired CPython oracle
// (benchmarks/constraint-envelope-oracle-v1/run_envelope_gates.py) and stated
// in writing that they did NOT test "the shipped Rust runtime
// (amphora-formulation-capabilities), which this fire does not test."
// mission.md's "Honest current state" and "Current benchmark result"
// sections name that Rust crate's `evaluate_envelope_policy` as the live
// checked authority. This harness closes that gap: it links the REAL,
// unmodified, compiled `amphora_formulation_capabilities::evaluate_envelope_policy`
// (not a reimplementation) and re-runs the T-03 boundary-fuzz grid plus the
// KPI's own 3 named sub-probes directly against it.
//
// A POSITIVE CONTROL closes the loop: a hand-written copy of the same
// function with only the `is_finite()` guard on bounds removed (the exact
// defect class T-03 confirmed in the Python oracle: "-inf > +inf is False in
// IEEE 754") is defined locally in this file (never touches the real crate)
// and probed with the same non-finite-bound inputs, to prove this harness
// can detect that defect class when it is actually present.

use amphora_formulation_capabilities::{
    evaluate_envelope_policy, DimensionedFeatureV1, EnvelopeConstraintV1, EnvelopePolicyV1,
    TrustedArithmeticSnapshotV1,
};
use serde_json::{json, Map, Value};
use std::collections::BTreeMap;

fn f64_json(v: f64) -> Value {
    if v.is_nan() {
        json!("NaN")
    } else if v.is_infinite() {
        json!(if v > 0.0 { "Infinity" } else { "-Infinity" })
    } else {
        json!(v)
    }
}

fn mk_policy(
    id: &str,
    schema_ok: bool,
    authoritative: bool,
    fixture_only: bool,
    constraints: Vec<EnvelopeConstraintV1>,
) -> EnvelopePolicyV1 {
    EnvelopePolicyV1 {
        schema: if schema_ok {
            "amphora.synthetic-envelope-policy.v1".into()
        } else {
            "amphora.wrong-schema.v1".into()
        },
        policy_id: id.into(),
        fixture_only,
        authoritative,
        constraints,
    }
}

fn c(id: &str, path: &str, unit: &str, lo: f64, hi: f64) -> EnvelopeConstraintV1 {
    EnvelopeConstraintV1 {
        constraint_id: id.into(),
        feature_path: path.into(),
        unit: unit.into(),
        lower_inclusive: lo,
        upper_inclusive: hi,
    }
}

fn mk_snapshot(part_a: f64, part_b: f64, total: f64, part_a_unit: &str) -> TrustedArithmeticSnapshotV1 {
    let mut values = BTreeMap::new();
    values.insert(
        "mass.part_A_g".to_string(),
        DimensionedFeatureV1 { value: part_a, unit: part_a_unit.into() },
    );
    values.insert(
        "mass.part_B_g".to_string(),
        DimensionedFeatureV1 { value: part_b, unit: "g".into() },
    );
    values.insert(
        "mass.total_g".to_string(),
        DimensionedFeatureV1 { value: total, unit: "g".into() },
    );
    TrustedArithmeticSnapshotV1 {
        schema: "amphora.trusted-arithmetic-snapshot.v1".into(),
        trusted: true,
        values,
    }
}

fn observe_real(
    policy: Option<&EnvelopePolicyV1>,
    snap: Option<&TrustedArithmeticSnapshotV1>,
    allow_synth: bool,
) -> (String, Value) {
    match evaluate_envelope_policy(policy, snap, allow_synth) {
        Ok(r) if r.status == "ABSTAIN" => ("ABSTAIN".to_string(), json!({"status": r.status})),
        Ok(r) => {
            let mut margins = Map::new();
            for (k, v) in r.margins.iter() {
                margins.insert(k.clone(), f64_json(*v));
            }
            let verdict = if r.pass_all_hard { "PASS" } else { "FAIL" };
            (
                verdict.to_string(),
                json!({"status": r.status, "pass_all_hard": r.pass_all_hard, "margins": Value::Object(margins)}),
            )
        }
        Err(e) => ("REJECT_ERR".to_string(), json!({"error": e})),
    }
}

// ---------------------------------------------------------------------
// PLANTED-DEFECT COPY (positive control only). This is a hand-maintained
// copy of the real function's logic with ONLY the bound is_finite() guard
// removed, matching the exact confirmed T-03 Python-oracle defect. It is
// NEVER used for the real-runtime verdict -- only to prove this harness's
// probes are capable of detecting that defect class.
// ---------------------------------------------------------------------
fn evaluate_envelope_policy_planted_defect(
    policy: Option<&EnvelopePolicyV1>,
    snapshot: Option<&TrustedArithmeticSnapshotV1>,
    allow_synthetic_fixture: bool,
) -> Result<(bool, BTreeMap<String, f64>), String> {
    let Some(policy) = policy else { return Ok((false, BTreeMap::new())) };
    let Some(snapshot) = snapshot else { return Ok((false, BTreeMap::new())) };
    let policy_trusted = policy.authoritative
        || (allow_synthetic_fixture && policy.fixture_only && !policy.authoritative);
    if policy.schema != "amphora.synthetic-envelope-policy.v1"
        || policy.policy_id.trim().is_empty()
        || !policy_trusted
        || snapshot.schema != "amphora.trusted-arithmetic-snapshot.v1"
        || !snapshot.trusted
    {
        return Ok((false, BTreeMap::new()));
    }
    if policy.constraints.is_empty() {
        return Err("envelope policy constraints must not be empty".into());
    }
    let known_features = std::collections::BTreeSet::from(["mass.part_A_g", "mass.part_B_g", "mass.total_g"]);
    let mut seen = std::collections::BTreeSet::new();
    let mut margins = BTreeMap::new();
    let mut passed = true;
    for constraint in &policy.constraints {
        if constraint.constraint_id.trim().is_empty() || !seen.insert(constraint.constraint_id.as_str()) {
            return Err("envelope policy contains duplicate constraints".into());
        }
        if !known_features.contains(constraint.feature_path.as_str()) {
            return Err(format!("unknown envelope feature path {}", constraint.feature_path));
        }
        // PLANTED DEFECT: is_finite() checks on lower/upper REMOVED. Only
        // the inversion comparison remains, which (per T-03) never fires
        // when both bounds are non-finite of the "wide-open" sign pattern.
        if constraint.lower_inclusive > constraint.upper_inclusive {
            return Err("envelope policy contains inverted bounds".into());
        }
        let feature = snapshot
            .values
            .get(&constraint.feature_path)
            .ok_or_else(|| format!("trusted feature {} is absent", constraint.feature_path))?;
        if !feature.value.is_finite() || feature.unit != constraint.unit {
            return Err(format!("unit mismatch for envelope feature {}", constraint.feature_path));
        }
        let margin = (feature.value - constraint.lower_inclusive).min(constraint.upper_inclusive - feature.value);
        passed &= margin >= 0.0;
        margins.insert(constraint.constraint_id.clone(), margin);
    }
    Ok((passed, margins))
}

fn observe_planted(
    policy: Option<&EnvelopePolicyV1>,
    snap: Option<&TrustedArithmeticSnapshotV1>,
    allow_synth: bool,
) -> (String, Value) {
    match evaluate_envelope_policy_planted_defect(policy, snap, allow_synth) {
        Ok((_, m)) if m.is_empty() && policy.is_some() && snap.is_some() => {
            // Could be a legitimate empty-margins abstain path; distinguish via passed flag default true+empty means abstain branch.
            ("ABSTAIN".to_string(), json!({}))
        }
        Ok((passed, m)) => {
            let mut margins = Map::new();
            for (k, v) in m.iter() {
                margins.insert(k.clone(), f64_json(*v));
            }
            let verdict = if passed { "PASS" } else { "FAIL" };
            (verdict.to_string(), json!({"pass_all_hard": passed, "margins": Value::Object(margins)}))
        }
        Err(e) => ("REJECT_ERR".to_string(), json!({"error": e})),
    }
}

struct Probe {
    name: &'static str,
    expected: &'static str,
    policy: Option<EnvelopePolicyV1>,
    snap: Option<TrustedArithmeticSnapshotV1>,
    allow_synth: bool,
}

fn main() {
    let real_src_sha256 = std::env::var("ENVGATE_LIBRS_SHA256").unwrap_or_default();

    let nominal_snap = mk_snapshot(180.0, 20.0, 200.0, "g");

    let mut probes: Vec<Probe> = Vec::new();

    // --- KPI's own 3 named sub-probes (envelope_bound_inversion_fail_closed_rate) ---
    probes.push(Probe {
        name: "kpi_subprobe_lower_gt_upper",
        expected: "REJECT_ERR",
        policy: Some(mk_policy("p-teta-201", true, true, false, vec![c("c1", "mass.part_A_g", "g", 200.0, 100.0)])),
        snap: Some(nominal_snap.clone()),
        allow_synth: true,
    });
    probes.push(Probe {
        name: "kpi_subprobe_lower_is_nan",
        expected: "REJECT_ERR",
        policy: Some(mk_policy("p-teta-202", true, true, false, vec![c("c1", "mass.part_A_g", "g", f64::NAN, 189.0)])),
        snap: Some(nominal_snap.clone()),
        allow_synth: true,
    });
    probes.push(Probe {
        name: "kpi_subprobe_upper_is_infinity",
        expected: "REJECT_ERR",
        policy: Some(mk_policy("p-teta-203", true, true, false, vec![c("c1", "mass.part_A_g", "g", 171.0, f64::INFINITY)])),
        snap: Some(nominal_snap.clone()),
        allow_synth: true,
    });

    // --- T-03 boundary-fuzz grid, reproduced against the Rust runtime ---
    probes.push(Probe {
        name: "value_free_bypass_both_bounds_infinite",
        expected: "REJECT_ERR",
        policy: Some(mk_policy("p-204", true, true, false, vec![c("c1", "mass.part_A_g", "g", f64::NEG_INFINITY, f64::INFINITY)])),
        snap: Some(mk_snapshot(500.0, 20.0, 520.0, "g")),
        allow_synth: true,
    });
    probes.push(Probe {
        name: "both_bounds_positive_infinity_degenerate",
        expected: "REJECT_ERR",
        policy: Some(mk_policy("p-205", true, true, false, vec![c("c1", "mass.part_A_g", "g", f64::INFINITY, f64::INFINITY)])),
        snap: Some(nominal_snap.clone()),
        allow_synth: true,
    });
    probes.push(Probe {
        name: "trusted_feature_value_nan",
        expected: "REJECT_ERR",
        policy: Some(mk_policy("p-206", true, true, false, vec![
            c("c1", "mass.part_A_g", "g", 171.0, 189.0),
            c("c2", "mass.part_B_g", "g", 18.0, 22.0),
        ])),
        snap: Some(mk_snapshot(180.0, f64::NAN, 200.0, "g")),
        allow_synth: true,
    });
    probes.push(Probe {
        name: "trusted_feature_value_infinite",
        expected: "REJECT_ERR",
        policy: Some(mk_policy("p-207", true, true, false, vec![c("c1", "mass.part_A_g", "g", 171.0, 189.0)])),
        snap: Some(mk_snapshot(f64::INFINITY, 20.0, f64::INFINITY, "g")),
        allow_synth: true,
    });
    probes.push(Probe {
        name: "unit_scale_substitution_kg_vs_g",
        expected: "REJECT_ERR",
        policy: Some(mk_policy("p-208", true, true, false, vec![c("c1", "mass.part_A_g", "g", 171.0, 189.0)])),
        snap: Some(mk_snapshot(180.0, 20.0, 200.0, "kg")),
        allow_synth: true,
    });
    probes.push(Probe {
        name: "duplicate_constraint_ids",
        expected: "REJECT_ERR",
        policy: Some(mk_policy("p-209", true, true, false, vec![
            c("dup", "mass.part_A_g", "g", 171.0, 189.0),
            c("dup", "mass.part_B_g", "g", 18.0, 22.0),
        ])),
        snap: Some(nominal_snap.clone()),
        allow_synth: true,
    });
    probes.push(Probe {
        name: "unknown_feature_path",
        expected: "REJECT_ERR",
        policy: Some(mk_policy("p-210", true, true, false, vec![c("c1", "volume.total_ml", "ml", 100.0, 200.0)])),
        snap: Some(nominal_snap.clone()),
        allow_synth: true,
    });
    probes.push(Probe {
        name: "empty_constraints",
        expected: "REJECT_ERR",
        policy: Some(mk_policy("p-211", true, true, false, vec![])),
        snap: Some(nominal_snap.clone()),
        allow_synth: true,
    });
    probes.push(Probe {
        name: "non_authoritative_without_synthetic_flag",
        expected: "ABSTAIN",
        policy: Some(mk_policy("p-212", true, false, true, vec![c("c1", "mass.part_A_g", "g", 171.0, 189.0)])),
        snap: Some(nominal_snap.clone()),
        allow_synth: false,
    });
    probes.push(Probe {
        name: "wrong_schema",
        expected: "ABSTAIN",
        policy: Some(mk_policy("p-213", false, true, false, vec![c("c1", "mass.part_A_g", "g", 171.0, 189.0)])),
        snap: Some(nominal_snap.clone()),
        allow_synth: true,
    });
    probes.push(Probe {
        name: "missing_trusted_feature",
        expected: "REJECT_ERR",
        policy: Some(mk_policy("p-214", true, true, false, vec![
            c("c1", "mass.part_A_g", "g", 171.0, 189.0),
            c("c2", "mass.part_B_g", "g", 18.0, 22.0),
        ])),
        snap: Some({
            let mut s = nominal_snap.clone();
            s.values.remove("mass.part_B_g");
            s
        }),
        allow_synth: true,
    });
    probes.push(Probe {
        name: "at_lower_boundary_bit_exact",
        expected: "PASS",
        policy: Some(mk_policy("p-215", true, true, false, vec![c("c1", "mass.part_A_g", "g", 171.0, 189.0)])),
        snap: Some(mk_snapshot(171.0, 20.0, 191.0, "g")),
        allow_synth: true,
    });
    probes.push(Probe {
        name: "one_ulp_below_lower_boundary",
        expected: "FAIL",
        policy: Some(mk_policy("p-216", true, true, false, vec![c("c1", "mass.part_A_g", "g", 171.0, 189.0)])),
        snap: Some(mk_snapshot(171.0_f64.next_down(), 20.0, 190.0, "g")),
        allow_synth: true,
    });
    probes.push(Probe {
        name: "at_upper_boundary_bit_exact",
        expected: "PASS",
        policy: Some(mk_policy("p-217", true, true, false, vec![c("c1", "mass.part_A_g", "g", 171.0, 189.0)])),
        snap: Some(mk_snapshot(189.0, 20.0, 209.0, "g")),
        allow_synth: true,
    });
    probes.push(Probe {
        name: "one_ulp_above_upper_boundary",
        expected: "FAIL",
        policy: Some(mk_policy("p-218", true, true, false, vec![c("c1", "mass.part_A_g", "g", 171.0, 189.0)])),
        snap: Some(mk_snapshot(189.0_f64.next_up(), 20.0, 209.0, "g")),
        allow_synth: true,
    });
    probes.push(Probe {
        name: "all_three_constraints_inverted_simultaneously",
        expected: "REJECT_ERR",
        policy: Some(mk_policy("p-219", true, true, false, vec![
            c("c1", "mass.part_A_g", "g", 189.0, 171.0),
            c("c2", "mass.part_B_g", "g", 22.0, 18.0),
            c("c3", "mass.total_g", "g", 211.0, 189.0),
        ])),
        snap: Some(nominal_snap.clone()),
        allow_synth: true,
    });
    probes.push(Probe {
        name: "second_constraint_nan_bound_not_first",
        expected: "REJECT_ERR",
        policy: Some(mk_policy("p-220", true, true, false, vec![
            c("c1", "mass.part_A_g", "g", 171.0, 189.0),
            c("c2", "mass.part_B_g", "g", f64::NAN, 22.0),
        ])),
        snap: Some(nominal_snap.clone()),
        allow_synth: true,
    });
    probes.push(Probe {
        name: "second_constraint_nan_value_not_first",
        expected: "REJECT_ERR",
        policy: Some(mk_policy("p-221", true, true, false, vec![
            c("c1", "mass.part_A_g", "g", 171.0, 189.0),
            c("c2", "mass.part_B_g", "g", 18.0, 22.0),
        ])),
        snap: Some(mk_snapshot(180.0, f64::NAN, 200.0, "g")),
        allow_synth: true,
    });
    probes.push(Probe {
        name: "zero_width_envelope_exact_match",
        expected: "PASS",
        policy: Some(mk_policy("p-222", true, true, false, vec![c("c1", "mass.part_A_g", "g", 180.0, 180.0)])),
        snap: Some(mk_snapshot(180.0, 20.0, 200.0, "g")),
        allow_synth: true,
    });
    probes.push(Probe {
        name: "extreme_finite_bounds_no_overflow_false_accept",
        expected: "PASS",
        policy: Some(mk_policy("p-223", true, true, false, vec![c("c1", "mass.part_A_g", "g", -f64::MAX, f64::MAX)])),
        snap: Some(mk_snapshot(f64::MAX, 20.0, f64::MAX, "g")),
        allow_synth: true,
    });

    let mut probe_out = Vec::new();
    let mut n_fired_as_expected = 0usize;
    for p in &probes {
        let (verdict, detail) = observe_real(p.policy.as_ref(), p.snap.as_ref(), p.allow_synth);
        let fired_as_expected = verdict == p.expected;
        if fired_as_expected {
            n_fired_as_expected += 1;
        }
        probe_out.push(json!({
            "probe": p.name,
            "expected_verdict": p.expected,
            "observed_verdict": verdict,
            "fired_as_expected": fired_as_expected,
            "detail": detail,
        }));
    }

    // --- Positive control: same class of probes against the planted-defect copy ---
    let pc_cases: Vec<(&str, EnvelopePolicyV1, TrustedArithmeticSnapshotV1)> = vec![
        (
            "pc_upper_is_infinity_on_registered_style_policy",
            mk_policy("pc-1", true, true, false, vec![c("c1", "mass.part_A_g", "g", 171.0, f64::INFINITY)]),
            mk_snapshot(500.0, 20.0, 520.0, "g"),
        ),
        (
            "pc_both_bounds_infinite_value_free",
            mk_policy("pc-2", true, true, false, vec![c("c1", "mass.part_A_g", "g", f64::NEG_INFINITY, f64::INFINITY)]),
            mk_snapshot(500.0, 20.0, 520.0, "g"),
        ),
    ];
    let mut pc_out = Vec::new();
    let mut pc_defect_detected = false;
    for (name, pol, snap) in &pc_cases {
        let (real_verdict, _) = observe_real(Some(pol), Some(snap), true);
        let (planted_verdict, planted_detail) = observe_planted(Some(pol), Some(snap), true);
        let slipped_through_on_planted = planted_verdict == "PASS" || planted_verdict == "FAIL";
        let real_correctly_rejected = real_verdict == "REJECT_ERR";
        if slipped_through_on_planted && real_correctly_rejected {
            pc_defect_detected = true;
        }
        pc_out.push(json!({
            "probe": name,
            "real_runtime_verdict": real_verdict,
            "real_runtime_correctly_rejected": real_correctly_rejected,
            "planted_defect_copy_verdict": planted_verdict,
            "planted_defect_copy_detail": planted_detail,
            "planted_defect_slipped_through": slipped_through_on_planted,
        }));
    }

    let all_real_fail_closed_as_expected = n_fired_as_expected == probes.len();

    let out = json!({
        "schema": "amphora.envelope-gates.rust-runtime-boundary-fuzz.v1",
        "real_runtime": {
            "crate": "amphora_formulation_capabilities",
            "function": "evaluate_envelope_policy",
            "src_path": "amphora-formulation-capabilities/src/lib.rs",
            "src_sha256": real_src_sha256,
        },
        "n_probes": probes.len(),
        "n_fired_as_expected": n_fired_as_expected,
        "all_real_fail_closed_as_expected": all_real_fail_closed_as_expected,
        "probes": probe_out,
        "positive_control": {
            "planted_defect": "is_finite() guard on constraint.lower_inclusive / constraint.upper_inclusive removed from a hand-copied version of evaluate_envelope_policy, leaving only the lower>upper inversion check -- the exact confirmed T-03 Python-oracle defect class (non-finite bounds of the 'wide-open' sign pattern never trip an inversion comparison in IEEE 754).",
            "how_planted": "Local function evaluate_envelope_policy_planted_defect() in this harness's own src/main.rs; never touches amphora-formulation-capabilities/src/lib.rs.",
            "cases": pc_out,
            "defect_detected": pc_defect_detected,
        },
    });
    println!("{}", serde_json::to_string_pretty(&out).unwrap());
}
