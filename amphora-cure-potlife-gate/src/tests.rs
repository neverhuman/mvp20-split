use super::*;
use serde_json::{json, Value};
use std::collections::BTreeMap;

fn digest(label: &str) -> String {
    contract_hash(&label).unwrap()
}

fn geometry(id: &str, diameter: f64, volume: f64) -> ContainerGeometryV1 {
    ContainerGeometryV1 {
        geometry_id: id.into(),
        shape: "CYLINDER".into(),
        inside_diameter_mm: diameter,
        fill_height_mm: 80.0,
        headspace_ml: 100.0,
        nominal_volume_ml: volume,
        lid_handling: "LOCKED_COVER_BETWEEN_MEASUREMENTS".into(),
    }
}

fn spray_setup() -> AirlessSpraySetupV1 {
    AirlessSpraySetupV1 {
        setup_id: "AIRLESS-1".into(),
        pump_id: "PUMP-1".into(),
        tip_orifice_in: 0.019,
        tip_fan_width_in: 10.0,
        locked_pressure_psi: 2_500.0,
        hose_length_ft: 50.0,
        hose_inside_diameter_in: 0.25,
        filter_mesh: 60,
        locked_pass_count: 2,
        thinning_allowed: false,
    }
}

fn qualification() -> PotLifeScaleQualificationV1 {
    PotLifeScaleQualificationV1 {
        schema: PROTOCOL_QUALIFICATION_SCHEMA.into(),
        qualification_id: "QUAL-1".into(),
        performed_with_non_reactive_fluid: true,
        qualification_fluid_sha256: digest("qualification-fluid"),
        sprayer_dead_volume_demand_g: 100.0,
        test_card_demand_g: 50.0,
        maximum_facility_approved_fill_g: 500.0,
        primary_geometry: geometry("G1", 100.0, 500.0),
        second_geometry: geometry("G2", 140.0, 1_000.0),
        distinct_geometry_confirmed_safe: true,
        airless_spray_setup: spray_setup(),
        calibration_ids: BTreeMap::from([
            ("stormer".into(), "CAL-STORMER".into()),
            ("temperature_logger".into(), "CAL-TEMP".into()),
            ("sprayer_pressure".into(), "CAL-PRESSURE".into()),
        ]),
    }
}

fn composition() -> PotLifeCompositionV1 {
    let distribution = Some(vec![FunctionalityDistributionV1 {
        functionality: 2.0,
        mole_fraction_0_1: 1.0,
    }]);
    PotLifeCompositionV1 {
        eew_g_per_eq: 190.0,
        ahew_g_per_eq: 95.0,
        epoxy_functionality: distribution.clone(),
        primary_amine_functionality: distribution.clone(),
        secondary_amine_functionality: distribution,
        epoxy_to_active_hydrogen_equivalent_ratio: 1.0,
        solids_mass_pct: 70.0,
        pvc_pct: 30.0,
        solvents_mass_fraction_0_1: BTreeMap::from([("SOLVENT-LOT".into(), 0.30)]),
        filler_mass_fraction_0_1: 0.25,
        catalyst_mass_fraction_0_1: 0.0,
        water_mass_fraction_0_1: 0.001,
        density_g_ml: 1.4,
        initial_rheology_method: "ASTM_D562_CERTIFIED_MAPPING_UNAVAILABLE".into(),
    }
}

fn generated_protocol() -> PotLifeProtocolV1 {
    generate_protocol(
        &qualification(),
        "2026-07-17",
        &digest("source-ledger"),
        "LOCKED_POWER_MIXER_SEQUENCE",
    )
    .unwrap()
}

fn target_celsius(target_f: u16) -> f64 {
    (target_f as f64 - 32.0) * 5.0 / 9.0
}

fn synthetic_run(
    protocol: &PotLifeProtocolV1,
    plan: &PlannedPotLifeRunV1,
    critical_clock_min: f64,
    activation_energy_j_mol: f64,
) -> PotLifeRunV1 {
    let material_c = target_celsius(plan.target_temperature_f);
    let rate = effective_cure_rate(
        celsius_to_kelvin(material_c).unwrap(),
        activation_energy_j_mol,
        REFERENCE_TEMPERATURE_K,
    )
    .unwrap();
    let replicate_shift = 1.0 + 0.01 * (plan.replicate as f64 - 2.0);
    let event_min = critical_clock_min * replicate_shift / rate;
    let last_pass = (event_min / 30.0).floor() * 30.0;
    let first_fail = last_pass + 30.0;
    let horizon = first_fail + 120.0;
    let temperature_series = (0..=(horizon / 5.0).ceil() as usize)
        .map(|index| TemperatureObservationV1 {
            elapsed_min: index as f64 * 5.0,
            material_temperature_c: material_c,
            ambient_temperature_c: material_c,
            relative_humidity_pct: 50.0,
        })
        .collect();
    let mut stormer_times = vec![0.0, 10.0, 20.0, 30.0];
    let mut time = 45.0;
    while time <= first_fail + 1e-9 {
        stormer_times.push(time);
        time += 15.0;
    }
    let stormer_series = stormer_times
        .into_iter()
        .map(|elapsed_min| {
            let clock = rate * elapsed_min;
            let log_ratio = 0.8 * clock / (400.0 - clock);
            StormerObservationV1 {
                elapsed_min,
                raw_response_ku: 70.0 * log_ratio.exp(),
                raw_load_g: 500.0 + elapsed_min,
                equivalent_viscosity_mpa_s: None,
                certified_mapping_id: None,
            }
        })
        .collect();
    let spray_checks = (0..=(first_fail / 30.0).round() as usize)
        .map(|index| {
            let elapsed_min = index as f64 * 30.0;
            let pass = elapsed_min < first_fail;
            SprayCheckV1 {
                elapsed_min,
                stable_pumping: true,
                locked_pressure_maintained: true,
                stable_full_fan_30_s: pass,
                wft_mil: vec![8.0, 8.1],
                no_tip_blockage: true,
                no_gel: true,
                no_seed: true,
                no_phase_split: true,
                thinner_added: false,
                pass,
                first_failed_property: (!pass).then_some(SprayFailurePropertyV1::FullFan30Seconds),
            }
        })
        .collect();
    let geometry = if plan.geometry_sha256 == protocol.primary_geometry.identity_hash() {
        protocol.primary_geometry.clone()
    } else {
        protocol.second_geometry.clone()
    };
    let run = PotLifeRunV1 {
        schema: POT_LIFE_RUN_SCHEMA.into(),
        track_id: POT_LIFE_TRACK_ID.into(),
        run_id: plan.run_id.clone(),
        protocol_sha256: protocol.identity_hash(),
        formulation_id: plan.formulation_id.clone(),
        formulation_hash: digest(&format!("formulation-{}", plan.formulation_id)),
        raw_material_lot_hashes: BTreeMap::from([
            (
                "resin".into(),
                digest(&format!("resin-{}", plan.formulation_id)),
            ),
            (
                "hardener".into(),
                digest(&format!("hardener-{}", plan.formulation_id)),
            ),
        ]),
        independent_mix_id: format!("MIX-{}", plan.run_id),
        batch_id: format!("BATCH-{}", plan.run_id),
        run_day: format!("DAY-{}", plan.run_id),
        replicate: plan.replicate,
        split: plan.split,
        target_temperature_f: plan.target_temperature_f,
        evidence_origin: EvidenceOriginV1::Owned,
        derivative_use_review_sha256: None,
        composition: composition(),
        mixed_mass_g: plan.mixed_mass_g,
        mix_ratio_by_volume: "1:1".into(),
        induction_time_min: 30.0,
        geometry,
        spray_setup: protocol.locks.airless_spray_setup.clone(),
        operator_id: "OP-BLINDED".into(),
        calibration_ids: BTreeMap::from([
            ("stormer".into(), "CAL-STORMER".into()),
            ("temperature_logger".into(), "CAL-TEMP".into()),
            ("sprayer_pressure".into(), "CAL-PRESSURE".into()),
        ]),
        mixing_history: vec!["INITIAL_MIXING_AT_T0".into(), "30_MIN_INDUCTION".into()],
        temperature_series,
        stormer_series,
        spray_checks,
        locked_ku_threshold: Some(100.0),
        deviations: Vec::new(),
        photographs_sha256: vec![digest(&format!("photo-{}", plan.run_id))],
        raw_file_hashes: BTreeMap::from([(
            format!("raw/{}.csv", plan.run_id),
            digest(&format!("raw-{}", plan.run_id)),
        )]),
    };
    run.validate().unwrap();
    run
}

fn synthetic_dataset() -> (PotLifeProtocolV1, Vec<PotLifeRunV1>) {
    let protocol = generated_protocol();
    let runs = protocol
        .planned_runs
        .iter()
        .map(|plan| {
            let critical = match (plan.formulation_id.as_str(), plan.geometry_id.as_str()) {
                ("M00097", "G2") => 220.0,
                ("M00101", _) => 210.0,
                ("M00109", _) => 240.0,
                _ => 180.0,
            };
            synthetic_run(&protocol, plan, critical, 60_000.0)
        })
        .collect();
    (protocol, runs)
}

#[test]
fn protocol_has_exact_owned_design_and_scale_gate() {
    let protocol = generated_protocol();
    assert_eq!(protocol.planned_runs.len(), 36);
    assert_eq!(
        protocol
            .planned_runs
            .iter()
            .filter(|run| run.sealed_until_locked_evaluation)
            .count(),
        12
    );
    assert_eq!(protocol.primary_mixed_mass_g, 180.0);
    assert_eq!(protocol.second_mixed_mass_g, 360.0);

    let mut unsafe_qualification = qualification();
    unsafe_qualification.second_geometry = unsafe_qualification.primary_geometry.clone();
    assert!(generate_protocol(
        &unsafe_qualification,
        "2026-07-17",
        &digest("source-ledger"),
        "MIX"
    )
    .is_err());
}

#[test]
fn application_endpoint_and_viscosity_proxy_remain_separate() {
    let protocol = generated_protocol();
    let run = synthetic_run(&protocol, &protocol.planned_runs[0], 180.0, 60_000.0);
    let application = run.observed_application_interval().unwrap();
    let viscosity = run.viscosity_proxy().unwrap();
    assert_eq!(viscosity.kind, ViscosityProxyKindV1::KuThresholdOnly);
    assert_eq!(viscosity.threshold, 100.0);
    assert_ne!(
        viscosity.threshold,
        2.0 * run.stormer_series[0].raw_response_ku
    );
    assert_ne!(
        viscosity.observed_or_predicted_time_h.unwrap(),
        application.first_fail_min / 60.0
    );
}

#[test]
fn certified_mapping_is_required_for_viscosity_doubling() {
    let protocol = generated_protocol();
    let mut run = synthetic_run(&protocol, &protocol.planned_runs[0], 180.0, 60_000.0);
    for (index, row) in run.stormer_series.iter_mut().enumerate() {
        row.equivalent_viscosity_mpa_s = Some(1_000.0 + index as f64 * 10.0);
        row.certified_mapping_id = Some("MAP-1".into());
    }
    assert!(run.validate().is_err());
    run.calibration_ids
        .insert("stormer_mapping".into(), "MAP-1".into());
    assert!(run.validate().is_ok());
    assert_eq!(
        run.viscosity_proxy().unwrap().threshold,
        2.0 * run.stormer_series[0].equivalent_viscosity_mpa_s.unwrap()
    );
}

#[test]
fn time_series_ordering_and_cadence_are_strict() {
    let protocol = generated_protocol();
    let mut run = synthetic_run(&protocol, &protocol.planned_runs[0], 180.0, 60_000.0);
    run.temperature_series[2].elapsed_min = run.temperature_series[1].elapsed_min;
    assert_eq!(
        run.validate(),
        Err(PotLifeError::TimeOrder("temperature_series"))
    );

    let mut run = synthetic_run(&protocol, &protocol.planned_runs[0], 180.0, 60_000.0);
    run.stormer_series[4].elapsed_min = 46.0;
    assert_eq!(
        run.validate(),
        Err(PotLifeError::Schedule("Stormer post-30-minute cadence"))
    );
}

#[test]
fn fahrenheit_kelvin_conversion_is_dimensionally_correct() {
    assert!((fahrenheit_to_kelvin(32.0).unwrap() - 273.15).abs() < 1e-12);
    assert!((fahrenheit_to_kelvin(73.0).unwrap() - REFERENCE_TEMPERATURE_K).abs() < 1e-12);
    assert!(fahrenheit_to_kelvin(-500.0).is_err());
}

#[test]
fn effective_clock_integrates_actual_material_not_ambient_temperature() {
    let series = vec![
        TemperatureObservationV1 {
            elapsed_min: 0.0,
            material_temperature_c: 35.0,
            ambient_temperature_c: 20.0,
            relative_humidity_pct: 50.0,
        },
        TemperatureObservationV1 {
            elapsed_min: 60.0,
            material_temperature_c: 35.0,
            ambient_temperature_c: 20.0,
            relative_humidity_pct: 50.0,
        },
    ];
    let actual =
        integrate_effective_cure_clock(&series, 60.0, 60_000.0, REFERENCE_TEMPERATURE_K).unwrap();
    let mut ambient = series.clone();
    for row in &mut ambient {
        row.material_temperature_c = row.ambient_temperature_c;
    }
    let substituted =
        integrate_effective_cure_clock(&ambient, 60.0, 60_000.0, REFERENCE_TEMPERATURE_K).unwrap();
    assert!(actual > substituted);
}

#[test]
fn interval_censoring_has_zero_error_inside_and_log_distance_outside() {
    assert_eq!(interval_censored_log_error(90.0, 60.0, 120.0).unwrap(), 0.0);
    assert!((interval_censored_log_error(30.0, 60.0, 120.0).unwrap() - 2_f64.ln()).abs() < 1e-12);
    assert!(factor_1_5_correct(50.0, 60.0, 120.0));
    assert!(proper_interval_score(50.0, 130.0, 60.0, 120.0, 0.1).unwrap() > 0.0);
}

#[test]
fn reduced_fit_recovers_synthetic_activation_energy() {
    let (protocol, _) = synthetic_dataset();
    let runs: Vec<_> = protocol
        .planned_runs
        .iter()
        .filter(|plan| {
            plan.formulation_id == "M00097"
                && plan.geometry_id == "G1"
                && plan.target_temperature_f != 73
        })
        .map(|plan| synthetic_run(&protocol, plan, 180.0, 60_000.0))
        .collect();
    let fit = fit_reduced_model(&runs).unwrap();
    assert!((fit.parameters.activation_energy_j_mol - 60_000.0).abs() <= 15_000.0);
    assert!(fit.parameters.primary_amine_rate_constant.is_none());
    assert!(fit.parameters.heat_transfer_coefficient.is_none());
}

#[test]
fn reduced_fit_abstains_when_temperature_contrast_is_absent() {
    let protocol = generated_protocol();
    let runs: Vec<_> = protocol
        .planned_runs
        .iter()
        .filter(|plan| {
            plan.formulation_id == "M00097"
                && plan.geometry_id == "G1"
                && plan.target_temperature_f == 65
        })
        .map(|plan| synthetic_run(&protocol, plan, 180.0, 60_000.0))
        .collect();
    assert_eq!(
        fit_reduced_model(&runs),
        Err(PotLifeError::Model("activation energy is not identifiable"))
    );
}

#[test]
fn owned_run_contract_quarantines_public_and_supplier_rows() {
    let protocol = generated_protocol();
    let mut run = synthetic_run(&protocol, &protocol.planned_runs[0], 180.0, 60_000.0);
    run.evidence_origin = EvidenceOriginV1::Supplier;
    run.derivative_use_review_sha256 = Some(digest("review"));
    assert_eq!(run.validate(), Err(PotLifeError::Rights));
}

#[test]
fn split_leakage_detects_batch_day_and_mix_overlap() {
    let (_, mut runs) = synthetic_dataset();
    let fit = runs
        .iter()
        .position(|run| run.split == PotLifeRunSplitV1::Fit)
        .unwrap();
    let holdout = runs
        .iter()
        .position(|run| run.split == PotLifeRunSplitV1::SealedHoldout)
        .unwrap();
    runs[holdout].batch_id = runs[fit].batch_id.clone();
    runs[holdout].run_day = runs[fit].run_day.clone();
    runs[holdout].independent_mix_id = runs[fit].independent_mix_id.clone();
    let audit = split_leakage_audit(&runs);
    assert!(!audit.batch_ids_disjoint);
    assert!(!audit.run_days_disjoint);
    assert!(!audit.independent_mix_ids_disjoint);
    assert!(!audit.passed());
}

#[test]
fn locked_evaluation_binds_hashes_runs_hostile_nulls_and_replay() {
    let (protocol, runs) = synthetic_dataset();
    let lock = lock_benchmark(&protocol, &runs).unwrap();
    let model =
        evaluate_locked_benchmark(&lock, &runs, &protocol.source_ledger_sha256, None, 2).unwrap();
    assert_eq!(model.hostile_nulls.len(), 6);
    assert_eq!(
        model
            .replay_hashes
            .values()
            .collect::<std::collections::BTreeSet<_>>()
            .len(),
        1
    );
    assert!(!model.gate_status.independent_review_passed);
    assert_eq!(model.authority, ResearchAuthorityV1::Shadow);
    assert_eq!(model.fto_status, "FTO NOT PERFORMED");

    let mut tampered = runs.clone();
    tampered[0].operator_id = "TAMPERED".into();
    assert!(
        evaluate_locked_benchmark(&lock, &tampered, &protocol.source_ledger_sha256, None, 1)
            .is_err()
    );
}

#[test]
fn geometry_ood_abstains_and_authority_requires_both_gates() {
    let (protocol, runs) = synthetic_dataset();
    let lock = lock_benchmark(&protocol, &runs).unwrap();
    let mut model =
        evaluate_locked_benchmark(&lock, &runs, &protocol.source_ledger_sha256, None, 1).unwrap();
    let holdout = runs
        .iter()
        .find(|run| run.split == PotLifeRunSplitV1::SealedHoldout)
        .unwrap();
    let mut conditions = PredictionConditionsV1 {
        formulation_id: holdout.formulation_id.clone(),
        formulation_hash: holdout.formulation_hash.clone(),
        geometry_sha256: holdout.geometry_hash(),
        spray_setup_sha256: holdout.spray_setup_hash(),
        mixed_mass_g: holdout.mixed_mass_g,
        expected_material_temperature_series: holdout.temperature_series.clone(),
        viscosity_proxy: holdout.viscosity_proxy(),
    };
    let prediction = predict_application_pot_life(&model, &conditions).unwrap();
    assert_eq!(prediction.candidate_pot_life_prediction_h, None);

    conditions.geometry_sha256 = digest("unseen-geometry");
    let prediction = predict_application_pot_life(&model, &conditions).unwrap();
    assert!(!prediction.in_applicability_domain);
    assert_eq!(prediction.candidate_pot_life_prediction_h, None);

    conditions.geometry_sha256 = holdout.geometry_hash();
    conditions.mixed_mass_g += 1.0;
    let prediction = predict_application_pot_life(&model, &conditions).unwrap();
    assert!(!prediction.in_applicability_domain);

    conditions.mixed_mass_g = holdout.mixed_mass_g;
    model.gate_status = passing_gate_status();
    model.validate().unwrap();
    let prediction = predict_application_pot_life(&model, &conditions).unwrap();
    assert!(prediction.candidate_pot_life_prediction_h.is_some());
    assert_eq!(prediction.authority, ResearchAuthorityV1::Shadow);
}

#[test]
fn expert_packet_is_sealed_and_not_sent() {
    let (protocol, runs) = synthetic_dataset();
    let lock = lock_benchmark(&protocol, &runs).unwrap();
    let model =
        evaluate_locked_benchmark(&lock, &runs, &protocol.source_ledger_sha256, None, 8).unwrap();
    let packet = seal_expert_packet(&model, &runs, &digest("prior-art-chart")).unwrap();
    assert_eq!(packet.delivery_status, "SEALED_NOT_SENT_APPROVAL_REQUIRED");
    assert_eq!(packet.blinded_raw_series_hashes.len(), 36);
}

#[test]
fn flory_stockmayer_bounds_require_known_functionality_distributions() {
    let known = composition();
    assert!(flory_stockmayer_bounds(&known).is_some());
    let mut commercial_grade = known;
    commercial_grade.primary_amine_functionality = None;
    assert!(flory_stockmayer_bounds(&commercial_grade).is_none());
}

#[test]
fn strict_prediction_contract_rejects_self_escalation() {
    let prediction = PotLifePredictionV1 {
        schema: POT_LIFE_PREDICTION_SCHEMA.into(),
        track_id: POT_LIFE_TRACK_ID.into(),
        prediction_id: "prediction".into(),
        model_artifact_sha256: digest("model"),
        endpoint: PotLifeEndpointV1::AirlessSprayFirstPropertyFailure,
        authority: ResearchAuthorityV1::Shadow,
        formulation_id: "M00097".into(),
        formulation_hash: digest("formulation"),
        geometry_sha256: digest("geometry"),
        spray_setup_sha256: digest("spray"),
        mixed_mass_g: 180.0,
        in_applicability_domain: true,
        locked_gate_passed: false,
        independent_review_passed: true,
        candidate_pot_life_prediction_h: Some(2.0),
        prediction_interval_90_h: Some([1.5, 2.5]),
        viscosity_proxy: None,
        abstention_reasons: Vec::new(),
    };
    assert_eq!(prediction.validate(), Err(PotLifeError::Authority));

    let with_unknown = json!({
        "schema": POT_LIFE_PREDICTION_SCHEMA,
        "track_id": POT_LIFE_TRACK_ID,
        "prediction_id": "p",
        "model_artifact_sha256": digest("m"),
        "endpoint": "AIRLESS_SPRAY_FIRST_PROPERTY_FAILURE",
        "authority": "SHADOW",
        "formulation_id": "M00097",
        "formulation_hash": digest("f"),
        "geometry_sha256": digest("g"),
        "spray_setup_sha256": digest("s"),
        "mixed_mass_g": 180.0,
        "in_applicability_domain": false,
        "locked_gate_passed": false,
        "independent_review_passed": false,
        "candidate_pot_life_prediction_h": null,
        "prediction_interval_90_h": null,
        "viscosity_proxy": null,
        "abstention_reasons": ["NO_AUTHORITY"],
        "unknown": true
    });
    assert!(strict_from_value::<PotLifePredictionV1>(with_unknown).is_err());
}

#[test]
fn test_preflight_accepts_every_contract_kind_and_remains_strict() {
    let qualification = qualification();
    let (protocol, runs) = synthetic_dataset();
    let lock = lock_benchmark(&protocol, &runs).unwrap();
    let model =
        evaluate_locked_benchmark(&lock, &runs, &protocol.source_ledger_sha256, None, 1).unwrap();
    let packet = seal_expert_packet(&model, &runs, &digest("prior-art-chart")).unwrap();
    let review = IndependentReviewV1 {
        schema: INDEPENDENT_REVIEW_SCHEMA.into(),
        track_id: POT_LIFE_TRACK_ID.into(),
        expert_packet_sha256: contract_hash(&packet).unwrap(),
        reviewer_id: "REVIEWER-INDEPENDENT-1".into(),
        independent_of_model_development: true,
        blinded_review: true,
        review_returned: true,
        all_gate_calculations_confirmed: true,
        signed_review_receipt_sha256: digest("signed-review-receipt"),
    };
    let prediction = PotLifePredictionV1 {
        schema: POT_LIFE_PREDICTION_SCHEMA.into(),
        track_id: POT_LIFE_TRACK_ID.into(),
        prediction_id: "PREDICTION-ABSTAINED-1".into(),
        model_artifact_sha256: contract_hash(&model).unwrap(),
        endpoint: PotLifeEndpointV1::AirlessSprayFirstPropertyFailure,
        authority: ResearchAuthorityV1::Shadow,
        formulation_id: "M00097".into(),
        formulation_hash: digest("formulation-M00097"),
        geometry_sha256: protocol.primary_geometry.identity_hash(),
        spray_setup_sha256: protocol.locks.airless_spray_setup.identity_hash(),
        mixed_mass_g: protocol.primary_mixed_mass_g,
        in_applicability_domain: true,
        locked_gate_passed: false,
        independent_review_passed: false,
        candidate_pot_life_prediction_h: None,
        prediction_interval_90_h: None,
        viscosity_proxy: None,
        abstention_reasons: vec!["LOCKED_GATE_NOT_PASSED".into()],
    };
    let cases = [
        (
            PotLifeContractKind::ScaleQualification,
            serde_json::to_value(qualification.clone()).unwrap(),
        ),
        (
            PotLifeContractKind::Run,
            serde_json::to_value(&runs[0]).unwrap(),
        ),
        (
            PotLifeContractKind::Protocol,
            serde_json::to_value(&protocol).unwrap(),
        ),
        (
            PotLifeContractKind::BenchmarkLock,
            serde_json::to_value(&lock).unwrap(),
        ),
        (
            PotLifeContractKind::ModelArtifact,
            serde_json::to_value(&model).unwrap(),
        ),
        (
            PotLifeContractKind::Prediction,
            serde_json::to_value(&prediction).unwrap(),
        ),
        (
            PotLifeContractKind::IndependentReview,
            serde_json::to_value(&review).unwrap(),
        ),
        (
            PotLifeContractKind::ExpertPacket,
            serde_json::to_value(&packet).unwrap(),
        ),
    ];
    for (kind, value) in cases {
        let report = preflight_contract(kind, value).unwrap();
        assert_eq!(report.kind, kind);
        assert!(!report.contract_id.is_empty());
    }

    let mut unknown = serde_json::to_value(&qualification).unwrap();
    unknown["unexpected"] = Value::Bool(true);
    assert!(preflight_contract(PotLifeContractKind::ScaleQualification, unknown).is_err());

    let mut malformed_hash = serde_json::to_value(&qualification).unwrap();
    malformed_hash["qualification_fluid_sha256"] = Value::String("not-a-hash".into());
    assert!(preflight_contract(PotLifeContractKind::ScaleQualification, malformed_hash).is_err());
}

#[test]
fn untouched_operator_templates_fail_preflight() {
    let scale: Value = serde_json::from_str(include_str!(
        "../templates/scale-qualification.incomplete.json"
    ))
    .unwrap();
    assert!(preflight_contract(PotLifeContractKind::ScaleQualification, scale).is_err());

    let review: Value = serde_json::from_str(include_str!(
        "../templates/independent-review.incomplete.json"
    ))
    .unwrap();
    assert!(preflight_contract(PotLifeContractKind::IndependentReview, review).is_err());
}

fn passing_gate_status() -> PotLifeGateStatusV1 {
    PotLifeGateStatusV1 {
        valid_independent_runs_36: true,
        untouched_73f_holdouts_12: true,
        zero_split_leakage: true,
        holdout_factor_1_5_at_least_0_80: true,
        lift_at_least_0_10: true,
        paired_bootstrap_lower_positive: true,
        interval_coverage_0_85_to_0_95: true,
        parameters_finite_identifiable_bounded: true,
        viscosity_proxy_non_worse: true,
        replay_equal_1_2_8_workers: true,
        hostile_null_suite_passed: true,
        independent_review_passed: true,
    }
}

// -------------------------------------------------------------------
// Phase-0 Arrhenius cure-rate red-team tests
// -------------------------------------------------------------------

const T_REF_C_73F: f64 = 22.777_777_777_777_778; // 73 °F = coating industry reference

#[test]
fn effective_cure_rate_rejects_non_finite_inputs() {
    let t_ref = 295.928_f64; // 73 °F in K
    for bad in [f64::NAN, f64::INFINITY, f64::NEG_INFINITY] {
        assert!(effective_cure_rate(bad, 55_000.0, t_ref).is_err(),
            "non-finite temperature_k {bad} must reject");
        assert!(effective_cure_rate(298.0, bad, t_ref).is_err(),
            "non-finite activation_energy {bad} must reject");
        assert!(effective_cure_rate(298.0, 55_000.0, bad).is_err(),
            "non-finite reference_temperature_k {bad} must reject");
    }
}

#[test]
fn effective_cure_rate_rejects_non_positive_temperature_or_ea() {
    let t_ref = 295.928_f64;
    assert!(effective_cure_rate(0.0, 55_000.0, t_ref).is_err());
    assert!(effective_cure_rate(-10.0, 55_000.0, t_ref).is_err());
    assert!(effective_cure_rate(298.0, 0.0, t_ref).is_err());
    assert!(effective_cure_rate(298.0, -1000.0, t_ref).is_err());
    assert!(effective_cure_rate(298.0, 55_000.0, 0.0).is_err());
    assert!(effective_cure_rate(298.0, 55_000.0, -10.0).is_err());
}

#[test]
fn effective_cure_rate_is_unity_at_reference_temperature() {
    let t_ref = 295.928_f64;
    let rate = effective_cure_rate(t_ref, 55_000.0, t_ref).unwrap();
    let unity_bits = 1.0_f64.to_bits();
    // exp(0) == 1 exactly in IEEE-754.
    assert_eq!(rate.to_bits(), unity_bits,
        "cure rate at T = T_ref must be exactly 1.0, got {rate}");
}

#[test]
fn effective_cure_rate_monotone_increases_with_temperature_for_positive_ea() {
    let t_ref = 295.928_f64;
    let ea = 55_000.0;
    let cold = effective_cure_rate(283.15, ea, t_ref).unwrap(); // 10 °C
    let ref_ = effective_cure_rate(t_ref, ea, t_ref).unwrap();
    let warm = effective_cure_rate(303.15, ea, t_ref).unwrap(); // 30 °C
    let hot = effective_cure_rate(313.15, ea, t_ref).unwrap();  // 40 °C
    assert!(cold < ref_ && ref_ < warm && warm < hot,
        "positive Ea ⇒ cure rate monotone increases with T: {cold} < {ref_} < {warm} < {hot}");
}

#[test]
fn effective_cure_rate_is_byte_deterministic_across_replays() {
    let first = effective_cure_rate(303.15, 55_000.0, 295.928).unwrap();
    let second = effective_cure_rate(303.15, 55_000.0, 295.928).unwrap();
    assert_eq!(first.to_bits(), second.to_bits());
}

#[test]
fn celsius_to_kelvin_rejects_temperatures_below_absolute_zero_and_non_finite() {
    assert!(celsius_to_kelvin(-273.15).is_err(),
        "T = absolute zero should reject to avoid K = 0.0 divide-by-zero downstream");
    assert!(celsius_to_kelvin(-300.0).is_err());
    assert!(celsius_to_kelvin(f64::NAN).is_err());
    assert!(celsius_to_kelvin(f64::INFINITY).is_err());
    // Normal case still works.
    let k = celsius_to_kelvin(22.78).unwrap();
    assert!((k - 295.93).abs() < 1e-2);
}

#[test]
fn fahrenheit_to_kelvin_rejects_non_finite_input() {
    assert!(fahrenheit_to_kelvin(f64::NAN).is_err());
    assert!(fahrenheit_to_kelvin(f64::INFINITY).is_err());
    // 73 °F = 295.928 K (coating industry reference).
    let k = fahrenheit_to_kelvin(73.0).unwrap();
    assert!((k - 295.928).abs() < 1e-2);
}

#[test]
fn arrhenius_potlife_ratio_matches_published_epoxy_amine_rules_of_thumb() {
    // For DGEBA/TETA (Ea ≈ 55 kJ/mol), pot-life ratio at 40°C vs. 22.78°C
    // should shrink to ~1/3 (Ellis 1993 Chapter 5). Verify:
    let ea = 55_000.0_f64;
    let t_ref_k = T_REF_C_73F + 273.15;
    let rate_40 = effective_cure_rate(40.0 + 273.15, ea, t_ref_k).unwrap();
    let pot_life_ratio = 1.0 / rate_40;
    assert!(pot_life_ratio > 0.20 && pot_life_ratio < 0.40,
        "DGEBA/TETA 40C/73F pot-life ratio {pot_life_ratio} outside published band");

    // For DGEBA/MPDA (Ea ≈ 68 kJ/mol), pot-life ratio at 10°C vs. 22.78°C
    // should grow to ~3.5x (Prime, Turi 1997). Verify.
    let ea_mpda = 68_000.0_f64;
    let rate_10 = effective_cure_rate(10.0 + 273.15, ea_mpda, t_ref_k).unwrap();
    let pot_life_ratio_10 = 1.0 / rate_10;
    assert!(pot_life_ratio_10 > 3.0 && pot_life_ratio_10 < 4.0,
        "DGEBA/MPDA 10C/73F pot-life ratio {pot_life_ratio_10} outside published band");
}
