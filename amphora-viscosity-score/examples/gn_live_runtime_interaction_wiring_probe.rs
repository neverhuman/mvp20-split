//! Live-runtime wiring audit for `grunberg_nissan_mix` (src/lib.rs:1171-1206) and its
//! sole call site inside `theory_apparent_viscosity` (src/lib.rs:1263-1301, call at line 1285).
//!
//! Falsification target: the standing claim in docs/mission.md ("the module's built-in
//! Grunberg-Nissan blend mixing, Krieger-Dougherty pigment crowding, and Herschel-Bulkley
//! yield flow paths remain scientifically UNVALIDATED and require wet-lab formulation
//! rheology for Phase-1") and in reference/rheology/source-landscape.v1.json (source_id
//! "grunberg-nissan-1949", applicability "Liquid-mixture log-viscosity theory"), which frame
//! Grunberg-Nissan mixing as structurally on par with Krieger-Dougherty and Herschel-Bulkley:
//! a real, cited physical model that is merely awaiting wet-lab data for Phase-1, not an
//! architecture gap.
//!
//! The defining feature of the Grunberg & Nissan (1949, Nature 164:799-800,
//! doi:10.1038/164799b0) mixture law -- what distinguishes it from a trivial ideal
//! (mass-fraction-weighted log-linear / Arrhenius-additive) mixing rule -- is its pairwise
//! interaction term d_ij (here `interactions[i][j]`). Without that term the equation
//! ln(eta_mix) = sum(x_i * ln(eta_i)) + sum_{i<j} x_i x_j d_ij collapses to plain ideal
//! mixing (d_ij = 0 for all i,j).
//!
//! This probe calls the live compiled `grunberg_nissan_mix` primitive directly -- not a
//! reimplementation -- three ways:
//!   (a) exactly as `theory_apparent_viscosity` invokes it at src/lib.rs:1284-1285: an
//!       all-zero interaction matrix sized to the live observation's liquid count;
//!   (b) the same fractions/viscosities with a non-zero, order-unity interaction term
//!       (magnitude chosen only to demonstrate the term is non-negligible when populated,
//!       not fitted to any specific real system);
//!   (c) an independent from-scratch closed-form ideal-mixing computation
//!       (exp(sum(x_i * ln(eta_i)))) that never calls grunberg_nissan_mix at all.
//!
//! It also drives `theory_apparent_viscosity` itself (the actual function called by both
//! `fit_model` and `predict`, i.e. every candidate ever scored) on a live two-liquid
//! `RheologyObservationV1`, to confirm end-to-end that the production call chain reaches
//! the same hardcoded zero-interaction branch.

use amphora_viscosity_score::{
    grunberg_nissan_mix, theory_apparent_viscosity, LiquidComponentV1, PigmentComponentV1,
    RheologyAdditiveV1, RheologyObservationV1, MODULE_ID, OBSERVATION_SCHEMA,
};
use serde_json::{json, Value};
use std::collections::BTreeMap;

fn two_liquid_observation() -> RheologyObservationV1 {
    RheologyObservationV1 {
        schema: OBSERVATION_SCHEMA.into(),
        module_id: MODULE_ID.into(),
        observation_id: "gn-wiring-probe-obs-1".into(),
        candidate_id: "gn-wiring-probe-candidate-1".into(),
        formulation_id: "gn-wiring-probe-formulation-1".into(),
        formulation_family: "gn-wiring-probe-family-1".into(),
        preparation_id: "gn-wiring-probe-preparation-1".into(),
        replicate_id: "gn-wiring-probe-replicate-1".into(),
        ingredients: BTreeMap::from([
            ("liquid-a".into(), "lot-liquid-a".into()),
            ("liquid-b".into(), "lot-liquid-b".into()),
        ]),
        liquids: vec![
            LiquidComponentV1 {
                ingredient_id: "liquid-a".into(),
                lot_id: "lot-liquid-a".into(),
                mass_fraction_0_1: 0.5,
                viscosity_pa_s_at_reference: 1.0,
                reference_temperature_c: 25.0,
                activation_energy_j_mol: 20_000.0,
            },
            LiquidComponentV1 {
                ingredient_id: "liquid-b".into(),
                lot_id: "lot-liquid-b".into(),
                mass_fraction_0_1: 0.5,
                viscosity_pa_s_at_reference: 4.0,
                reference_temperature_c: 25.0,
                activation_energy_j_mol: 20_000.0,
            },
        ],
        pigments: vec![PigmentComponentV1 {
            ingredient_id: "pigment-1".into(),
            lot_id: "lot-pigment-1".into(),
            volume_fraction_0_1: 0.0,
            morphology: Some("ACICULAR".into()),
            oil_absorption_g_per_100g: None,
        }],
        rheology_additives: vec![RheologyAdditiveV1 {
            ingredient_id: "rheology-1".into(),
            lot_id: "lot-rheology-1".into(),
            loading_mass_fraction_0_1: 0.0,
            activation_protocol: "LOCKED_HIGH_SHEAR".into(),
        }],
        density_kg_m3: 1_100.0,
        solids_volume_fraction_0_1: 0.0,
        pvc_fraction_0_1: 0.0,
        maximum_packing_fraction_0_1: 0.64,
        intrinsic_viscosity: 2.5,
        yield_stress_pa: 0.0,
        consistency_pa_s_n: 1e-9,
        flow_index_n: 1.0,
        pre_shear_s_inv: 100.0,
        pre_shear_duration_s: 60.0,
        pot_age_h: 1.0,
        temperature_c: 25.0,
        shear_rate_s_inv: 10.0,
        wet_film_thickness_mil: 10.0,
        application_angle_deg_from_horizontal: 90.0,
        instrument_id: "gn-wiring-probe-rheometer-1".into(),
        calibration_id: "gn-wiring-probe-calibration-1".into(),
        ku_method: "ASTM_D562".into(),
        sag_method: "ASTM_D4400".into(),
        measured_apparent_viscosity_pa_s: None,
        measured_ku: None,
        measured_sag_index_mil: None,
        sag_unsafe: None,
        raw_file_hashes: BTreeMap::from([("flow.csv".into(), "a".repeat(64))]),
        rights_receipt_sha256: "b".repeat(64),
        rights_eligible: true,
    }
}

fn main() {
    let fractions = [0.5_f64, 0.5_f64];
    let viscosities = [1.0_f64, 4.0_f64];

    // (a) Exactly reproduces the hardcoded call at src/lib.rs:1284-1285.
    let zero_matrix = vec![vec![0.0_f64; fractions.len()]; fractions.len()];
    let gn_zero_interaction =
        grunberg_nissan_mix(&fractions, &viscosities, &zero_matrix).expect("zero-interaction call");

    // (b) Same fractions/viscosities, non-zero order-unity interaction term.
    // Grunberg & Nissan (1949) define the interaction term d_ij as the feature that
    // distinguishes their mixture law from ideal (log-linear) mixing; published d_ij
    // values for real non-ideal binary liquid systems are commonly order-unity in
    // magnitude. 1.0 here is a demonstration magnitude, not a fit to any specific system.
    let nonzero_g12 = 1.0_f64;
    let nonzero_matrix = vec![vec![0.0, nonzero_g12], vec![nonzero_g12, 0.0]];
    let gn_nonzero_interaction = grunberg_nissan_mix(&fractions, &viscosities, &nonzero_matrix)
        .expect("nonzero-interaction call");

    // (c) Independent closed-form ideal (log-linear) mixing, never touching
    // grunberg_nissan_mix at all.
    let ideal_mixing_independent: f64 = (fractions
        .iter()
        .zip(viscosities.iter())
        .map(|(x, eta)| x * eta.ln())
        .sum::<f64>())
    .exp();

    let zero_vs_ideal_abs_diff = (gn_zero_interaction - ideal_mixing_independent).abs();
    let zero_vs_nonzero_rel_diff =
        (gn_nonzero_interaction - gn_zero_interaction).abs() / gn_zero_interaction;

    // End-to-end: the actual production call chain (fit_model / predict both call
    // theory_apparent_viscosity, which is the ONLY caller of grunberg_nissan_mix in the
    // live crate).
    let obs = two_liquid_observation();
    let theory_result = theory_apparent_viscosity(&obs).expect("in-domain observation");
    // theory_apparent_viscosity = krieger_dougherty(gn_liquid_mix, ...) + herschel_bulkley(...).
    // With pigment_volume_fraction=0 and yield_stress=0/negligible consistency, both additive
    // terms collapse toward the bare GN-mixed liquid viscosity, isolating the GN contribution.

    let out: Value = json!({
        "schema": "amphora.viscosity-score.gn-live-runtime-interaction-wiring-diagnostic.v1",
        "module_id": "amphora-viscosity-score",
        "function_under_test": "grunberg_nissan_mix (src/lib.rs:1171-1206) and its sole call site inside theory_apparent_viscosity (src/lib.rs:1263-1301, call at line 1285), called live via the compiled crate -- not reimplemented",
        "inputs": {"fractions": fractions, "viscosities_pa_s": viscosities, "nonzero_g12_demo_magnitude": nonzero_g12},
        "gn_zero_interaction_result_pa_s": gn_zero_interaction,
        "gn_nonzero_interaction_result_pa_s": gn_nonzero_interaction,
        "ideal_mixing_independent_closed_form_pa_s": ideal_mixing_independent,
        "zero_interaction_vs_independent_ideal_mixing_abs_diff": zero_vs_ideal_abs_diff,
        "zero_interaction_vs_nonzero_interaction_rel_diff": zero_vs_nonzero_rel_diff,
        "end_to_end_theory_apparent_viscosity_two_liquid_observation_pa_s": theory_result,
        "end_to_end_observation_pigment_volume_fraction": 0.0,
        "end_to_end_observation_yield_stress_pa": 0.0,
        "finding": "gn_zero_interaction_result_pa_s is bit-identical (to floating point evaluation order) to ideal_mixing_independent_closed_form_pa_s, i.e. the exact live call site's hardcoded zero-interaction matrix makes grunberg_nissan_mix compute plain ideal log-linear mixing, not Grunberg-Nissan mixing. gn_nonzero_interaction_result_pa_s diverges materially (see zero_interaction_vs_nonzero_interaction_rel_diff), proving the omitted term is not negligible when the underlying function IS given real interaction data -- the function itself is not broken, only its sole live caller never supplies anything but zeros."
    });
    println!("{}", serde_json::to_string_pretty(&out).unwrap());
}
