//! Live-runtime parity probe for `krieger_dougherty` (src/lib.rs:1208-1224).
//!
//! Falsification target: the docstring claim in
//! evidence/phase0/repairs/W-VISC2/done/krieger-dougherty-benchmark-landed-v1/run_kd_positive_control.py
//! ("Curve-fit goodness-of-fit (R^2) for both the fixed-Einstein-intrinsic-viscosity (2-param)
//! and free-intrinsic-viscosity (3-param) Krieger-Dougherty fits, replicated verbatim from
//! run_kd_ccby_reachability_probe.py (itself replicated verbatim from src/lib.rs:1208-1224)")
//! and the identical claim inherited from
//! evidence/phase0/repairs/W-VISC1/attempts/krieger-dougherty-ccby-reachability-probe-v1/run_kd_ccby_reachability_probe.py.
//! Every KD fire to date (C9 fire1/2, W-VISC1, W-VISC2) computed against a hand-written Python
//! `kd_vec` re-derivation and NEVER called the actual compiled Rust `krieger_dougherty` function.
//! This is the same previously-untested-gap class that hb-live-runtime-parity-v1 (2026-08-16)
//! found for HERSCHEL_BULKLEY -- escalated here to KRIEGER_DOUGHERTY, which has never had a
//! live-runtime probe.
//!
//! Additionally, unlike the HB Python oracle (which attempted, imperfectly, to replicate
//! src/lib.rs's guard/validity clauses), the KD `kd_vec` re-derivation used across every prior
//! KD fire implements ONLY the closed-form output line (src/lib.rs:1222-1223) and contains NO
//! guard logic at all -- it never replicates the four input-validity checks at src/lib.rs:1211-1218
//! (liquid_viscosity finite-positive, pigment_volume_fraction in [0,1], maximum_packing_fraction
//! in [0,1], pigment_volume_fraction < maximum_packing_fraction, intrinsic_viscosity finite-positive).
//! So the "replicated verbatim from src/lib.rs:1208-1224" claim -- which names the FULL line range,
//! including the guard clauses -- is checked here directly against the live compiled primitive.

use amphora_viscosity_score::krieger_dougherty;
use serde_json::{json, Value};

// Verbatim copy of the fitted parameters from
// evidence/phase0/repairs/W-VISC2/done/krieger-dougherty-benchmark-landed-v1/diagnostic.canonical.json
// (central_density_fit_result), used as the numeric-parity input set.
const PHI_VALUES: [f64; 5] = [0.088646, 0.076239, 0.064249, 0.052655, 0.041439];

struct FitParams {
    label: &'static str,
    eta_liquid_pa_s: f64,
    phi_max: f64,
    intrinsic_viscosity: f64,
}

const FITS: [FitParams; 2] = [
    FitParams {
        label: "fixed_einstein_intrinsic_viscosity_2p5",
        eta_liquid_pa_s: 7.316387,
        phi_max: 0.089532,
        intrinsic_viscosity: 2.5,
    },
    FitParams {
        label: "free_intrinsic_viscosity_3param",
        eta_liquid_pa_s: 0.929077,
        phi_max: 0.95,
        intrinsic_viscosity: 34.2402,
    },
];

fn main() {
    let mut fit_rows = Vec::new();
    for fit in FITS.iter() {
        let mut curve = Vec::new();
        for &phi in PHI_VALUES.iter() {
            // Live call into the real, unmodified compiled primitive -- not a reimplementation.
            let v = krieger_dougherty(fit.eta_liquid_pa_s, phi, fit.phi_max, fit.intrinsic_viscosity)
                .expect("in-domain call");
            curve.push(json!({"phi": phi, "eta_pa_s_live_rust": v}));
        }
        fit_rows.push(json!({
            "fit_label": fit.label,
            "eta_liquid_pa_s": fit.eta_liquid_pa_s,
            "phi_max": fit.phi_max,
            "intrinsic_viscosity": fit.intrinsic_viscosity,
            "curve": curve,
        }));
    }

    // Guard-rail edge-case battery covering all four validity checks at src/lib.rs:1211-1218,
    // which the promoted benchmarks' Python kd_vec re-derivation never replicates at all.
    let edge_cases: [(&str, f64, f64, f64, f64); 10] = [
        ("negative_liquid_viscosity", -1.0, 0.3, 0.6, 2.5),
        ("zero_liquid_viscosity", 0.0, 0.3, 0.6, 2.5),
        ("negative_pigment_fraction", 1.0, -0.1, 0.6, 2.5),
        ("pigment_fraction_over_one", 1.0, 1.1, 0.95, 2.5),
        ("max_packing_fraction_over_one", 1.0, 0.3, 1.1, 2.5),
        ("pigment_equals_max_packing", 1.0, 0.5, 0.5, 2.5),
        ("pigment_exceeds_max_packing_noninteger_exponent", 1.0, 0.6, 0.5, 2.5),
        ("negative_intrinsic_viscosity", 1.0, 0.3, 0.6, -1.0),
        ("nan_pigment_fraction", 1.0, f64::NAN, 0.6, 2.5),
        ("valid_baseline_sanity", 1.0, 0.3, 0.6, 2.5),
    ];
    let mut edge_out = Vec::new();
    for (label, eta_liq, phi, phi_max, eta_intr) in edge_cases.iter() {
        let res = krieger_dougherty(*eta_liq, *phi, *phi_max, *eta_intr);
        edge_out.push(json!({
            "case": label,
            "eta_liquid_pa_s": eta_liq, "phi": phi, "phi_max": phi_max, "intrinsic_viscosity": eta_intr,
            "is_ok": res.is_ok(),
            "value_if_ok": res.ok(),
        }));
    }

    let out: Value = json!({
        "schema": "amphora.viscosity-score.kd-live-runtime-parity-diagnostic.v1",
        "module_id": "amphora-viscosity-score",
        "function_under_test": "krieger_dougherty (src/lib.rs:1208-1224), called live via the compiled crate -- not reimplemented",
        "fits": fit_rows,
        "edge_case_guard_battery": edge_out,
    });
    println!("{}", serde_json::to_string_pretty(&out).unwrap());
}
