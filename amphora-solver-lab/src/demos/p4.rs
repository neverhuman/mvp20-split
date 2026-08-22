//! P4 - 2^4 full-factorial DoE screen.
//!
//! Universe: resin{DGEBA, DGEBF} x hardener{IPDA, TETA} x solvent{toluene,
//! MEK} x pigment{TiO2, carbon-black} = 16 formulations, from the CC0-1.0
//! formulation-universe known-answer fixture. Gates applied per cell:
//!   1. envelope gate  - a resin+hardener dosing policy must exist in the
//!      envelope-gates known-answer fixture; nominal dosing must sit inside
//!      every inclusive band. No policy => INFEASIBLE (fail-closed).
//!   2. mass balance   - part_A + part_B must close exactly (f64) to the
//!      nominal total of the dosing policy.
//!   3. GHS gate       - hardener axis, from the pinned GHS KPI: hard
//!      exclusions H334/H340/H350/H351; H314/H317 are advisory flags whose
//!      consequence is the KPI's own procurement_gate_outcome (a PPE-plan
//!      condition, not an exclusion - these are the KPI's published gate
//!      semantics, recorded verbatim, not softened by this demo).
//! The solved/infeasible partition is reported with per-cell reasons.

use crate::demos::{claim_locks, sources_json, AUTHORITY, DEMO_DATE, DEMO_HOST};
use crate::doe::{enumerate_cells, Axis};
use crate::oracle::SourceOracle;
use anyhow::{anyhow, Context, Result};
use serde_json::{json, Map, Value};

const UNIVERSE_ID: &str = "2^4-full-factorial-adhesive-screen";
const GHS_HARD_EXCLUSIONS: [&str; 4] = ["H334", "H340", "H350", "H351"];
const GHS_ADVISORY_FLAGS: [&str; 2] = ["H314", "H317"];

fn factor(cell: &[(String, String)], axis: &str) -> Result<String> {
    cell.iter()
        .find(|(name, _)| name == axis)
        .map(|(_, level)| level.clone())
        .with_context(|| format!("cell missing axis {axis}"))
}

/// Find the unique envelope policy for a resin+hardener pair. Zero matches is
/// a fail-closed infeasibility; more than one match is a hard error
/// (ambiguous source).
fn find_envelope<'a>(envelopes: &'a [Value], resin: &str, hardener: &str) -> Result<Option<&'a Value>> {
    let hardener_lc = hardener.to_ascii_lowercase();
    let mut hits: Vec<&Value> = Vec::new();
    for e in envelopes {
        let resin_str = e["resin"].as_str().unwrap_or_default();
        let eid = e["envelope_id"].as_str().unwrap_or_default().to_ascii_lowercase();
        if resin_str.contains(resin) && eid.contains(&hardener_lc) {
            hits.push(e);
        }
    }
    anyhow::ensure!(
        hits.len() <= 1,
        "ambiguous envelope policies for resin={resin} hardener={hardener} (fail-closed)"
    );
    Ok(hits.pop())
}

pub fn diagnostic() -> Result<Value> {
    let oracle = SourceOracle::pinned_default().map_err(|e| anyhow!("{e}"))?;
    let universe_src = oracle.read("formulation_universe_known_answer").map_err(|e| anyhow!("{e}"))?;
    let envelopes_src = oracle.read("envelope_gates_known_answer").map_err(|e| anyhow!("{e}"))?;
    let ghs = oracle.read("ghs_clp_hazard_prescreen_kpi").map_err(|e| anyhow!("{e}"))?;
    let audit = oracle
        .read("rn01_fire1_cid_attribution_audit_receipt")
        .map_err(|e| anyhow!("{e}"))?;

    let universe = universe_src
        .value
        .get("universes")
        .and_then(|v| v.as_array())
        .context("fixture missing universes")?
        .iter()
        .find(|u| u["universe_id"].as_str() == Some(UNIVERSE_ID))
        .with_context(|| format!("universe {UNIVERSE_ID} not in fixture"))?;
    let expected_total = universe["expected_cartesian_total"].as_u64().context("expected_cartesian_total")? as usize;
    let declared_infeasible = universe["expected_infeasible_candidate_count"].as_u64().unwrap_or(0);

    let axes_obj = universe["axes"].as_object().context("universe axes")?;
    let mut axes: Vec<Axis> = axes_obj
        .iter()
        .map(|(name, levels)| {
            Ok(Axis {
                name: name.clone(),
                levels: levels
                    .as_array()
                    .with_context(|| format!("axis {name} levels"))?
                    .iter()
                    .map(|v| v.as_str().unwrap_or_default().to_string())
                    .collect(),
            })
        })
        .collect::<Result<Vec<_>>>()?;
    axes.sort_by(|a, b| a.name.cmp(&b.name));

    let cells = enumerate_cells(&axes);
    anyhow::ensure!(
        cells.len() == expected_total,
        "cartesian accounting mismatch: enumerated {} cells but fixture expects {expected_total}",
        cells.len()
    );

    let envelopes = envelopes_src
        .value
        .get("envelopes")
        .and_then(|v| v.as_array())
        .context("envelope fixture missing envelopes")?;
    let hazard_cards = ghs
        .value
        .pointer("/fitted_or_physical_model_artifact/candidate_hazard_cards")
        .and_then(|v| v.as_array())
        .context("GHS KPI missing candidate_hazard_cards")?;

    let mut cell_reports: Vec<Value> = Vec::new();
    let mut solved: Vec<usize> = Vec::new();
    let mut infeasible: Vec<usize> = Vec::new();

    for (idx, cell) in cells.iter().enumerate() {
        let resin = factor(cell, "resin_choice")?;
        let hardener = factor(cell, "hardener_choice")?;
        let solvent = factor(cell, "solvent_choice")?;
        let pigment = factor(cell, "pigment_choice")?;

        let mut reasons: Vec<String> = Vec::new();

        // --- Gate 1: envelope policy lookup + band check at nominal dosing.
        let envelope = find_envelope(envelopes, &resin, &hardener)?;
        let envelope_json: Value;
        let mut envelope_pass = false;
        let mut mass_balance_json = Value::Null;
        let mut mass_balance_pass = false;
        match envelope {
            None => {
                envelope_json = json!({
                    "policy_id": Value::Null,
                    "pass": false,
                    "reason": format!(
                        "no envelope policy for resin={resin} + hardener={hardener}: the envelope-gates source covers DGEBA-only pairs; fail-closed"
                    ),
                });
                reasons.push(format!(
                    "ENVELOPE_GATE_NO_POLICY(resin={resin}, hardener={hardener}) [fail-closed: source has no {resin} envelope]"
                ));
            }
            Some(env) => {
                let policy = &env["policy"];
                let part_a = env["nominal_part_a_g"].as_f64().context("nominal_part_a_g")?;
                let part_b = env["nominal_part_b_g"].as_f64().context("nominal_part_b_g")?;
                let total = env["nominal_total_g"].as_f64().context("nominal_total_g")?;
                let features: Vec<(&str, f64)> = vec![
                    ("mass.part_A_g", part_a),
                    ("mass.part_B_g", part_b),
                    ("mass.total_g", total),
                ];
                let mut band_checks: Vec<Value> = Vec::new();
                let mut all_bands_ok = true;
                for c in policy["constraints"].as_array().context("policy constraints")? {
                    let fp = c["feature_path"].as_str().unwrap_or_default();
                    let lo = c["lower_inclusive"].as_f64().context("lower_inclusive")?;
                    let hi = c["upper_inclusive"].as_f64().context("upper_inclusive")?;
                    let value = features
                        .iter()
                        .find(|(name, _)| *name == fp)
                        .map(|(_, v)| *v)
                        .with_context(|| format!("no nominal feature for {fp}"))?;
                    let ok = value >= lo && value <= hi;
                    if !ok {
                        all_bands_ok = false;
                    }
                    band_checks.push(json!({
                        "constraint_id": c["constraint_id"],
                        "feature_path": fp,
                        "value": value,
                        "lower_inclusive": lo,
                        "upper_inclusive": hi,
                        "margin_lower": value - lo,
                        "margin_upper": hi - value,
                        "pass": ok,
                    }));
                }
                envelope_pass = all_bands_ok;
                if !all_bands_ok {
                    reasons.push("ENVELOPE_GATE_BAND_VIOLATION".to_string());
                }
                envelope_json = json!({
                    "policy_id": policy["policy_id"],
                    "envelope_id": env["envelope_id"],
                    "nominal_dose_g": {"part_a": part_a, "part_b": part_b, "total": total},
                    "band_checks": band_checks,
                    "pass": envelope_pass,
                });

                // --- Gate 2: exact f64 mass-balance closure at nominal dose.
                let sum = part_a + part_b; // ordered reduction (A then B)
                mass_balance_pass = sum == total && part_a > 0.0 && part_b > 0.0;
                if !mass_balance_pass {
                    reasons.push(format!(
                        "MASS_BALANCE_FAILURE(part_a + part_b = {sum} != nominal_total {total})"
                    ));
                }
                mass_balance_json = json!({
                    "part_a_plus_part_b": sum,
                    "nominal_total": total,
                    "exact_f64_closure": sum == total,
                    "pass": mass_balance_pass,
                });
            }
        }

        // --- Gate 3: GHS on the hardener axis (source coverage), from the
        // --- KPI's own published gate semantics.
        let hcard = hazard_cards.iter().find(|c| c["candidate_name"].as_str() == Some(hardener.as_str()));
        let ghs_json: Value;
        let mut ghs_pass = false;
        match hcard {
            None => {
                ghs_json = json!({
                    "hardener_card_found": false,
                    "pass": false,
                    "reason": format!("hardener {hardener} not covered by the pinned GHS KPI; fail-closed"),
                });
                reasons.push(format!("GHS_GATE_NO_HAZARD_CARD({hardener}) [fail-closed]"));
            }
            Some(card) => {
                let codes: Vec<String> = card["h_statement_codes"]
                    .as_array()
                    .context("h_statement_codes")?
                    .iter()
                    .map(|v| v.as_str().unwrap_or_default().to_string())
                    .collect();
                let hard_hits: Vec<String> = codes
                    .iter()
                    .filter(|c| GHS_HARD_EXCLUSIONS.contains(&c.as_str()))
                    .cloned()
                    .collect();
                let advisory_hits: Vec<String> = codes
                    .iter()
                    .filter(|c| GHS_ADVISORY_FLAGS.contains(&c.as_str()))
                    .cloned()
                    .collect();
                ghs_pass = hard_hits.is_empty();
                if !ghs_pass {
                    reasons.push(format!("GHS_HARD_EXCLUSION({}: {})", hardener, hard_hits.join("+")));
                }
                ghs_json = json!({
                    "hardener_card_found": true,
                    "hardener": hardener,
                    "h_statement_codes": codes,
                    "hard_exclusion_hits": hard_hits,
                    "advisory_flags": advisory_hits,
                    "condition": card["procurement_gate_outcome"],
                    "coverage": "HARDENER_AXIS_ONLY - the pinned GHS KPI covers the 5 canonical epoxy amines; solvent and pigment axes carry no hazard claim from this demo",
                    "pass": ghs_pass,
                });
            }
        }

        let cell_solved = envelope_pass && mass_balance_pass && ghs_pass;
        if cell_solved {
            solved.push(idx);
        } else {
            infeasible.push(idx);
        }
        let mut factors = Map::new();
        for (name, level) in cell {
            factors.insert(name.clone(), json!(level));
        }
        let _ = (&solvent, &pigment); // named factors are carried in `factors`
        cell_reports.push(json!({
            "cell_index": idx,
            "factors": Value::Object(factors),
            "status": if cell_solved { "SOLVED" } else { "INFEASIBLE" },
            "gates": {
                "envelope": envelope_json,
                "mass_balance": mass_balance_json,
                "ghs": ghs_json,
            },
            "reasons": reasons,
        }));
    }

    anyhow::ensure!(solved.len() + infeasible.len() == cells.len(), "partition accounting failure");

    let mut root = Map::new();
    root.insert("schema".into(), json!("amphora.solver-lab.demo-p4-2to4-full-factorial-screen.diagnostic.v1"));
    root.insert("demo_id".into(), json!("p4-2to4-full-factorial-screen"));
    root.insert("date".into(), json!(DEMO_DATE));
    root.insert("generated_on_host".into(), json!(DEMO_HOST));
    root.insert("authority".into(), json!(AUTHORITY));
    root.insert("authority_ceiling".into(), json!("EVIDENCE_ONLY"));
    root.insert("claim_locks".into(), claim_locks());
    root.insert("sources".into(), sources_json(&[&universe_src, &envelopes_src, &ghs, &audit]));
    root.insert(
        "problem".into(),
        json!({
            "universe_id": UNIVERSE_ID,
            "design_type": universe["design_type"],
            "axes": universe["axes"],
            "cell_order": "axes sorted by name (byte order); mixed-radix enumeration, last sorted axis fastest",
            "gates": {
                "envelope": "resin+hardener dosing policy must exist in the envelope-gates known-answer fixture and nominal dosing must sit inside every inclusive band; missing policy is fail-closed infeasible",
                "mass_balance": "part_A + part_B must close exactly (f64) to the policy's nominal total",
                "ghs": {
                    "hard_exclusions": GHS_HARD_EXCLUSIONS,
                    "advisory_flags_with_condition": GHS_ADVISORY_FLAGS,
                    "semantics": "advisory flags carry the GHS KPI's own procurement_gate_outcome (PPE-plan condition) rather than exclusion - the source KPI's published gate semantics, recorded verbatim",
                    "coverage": "hardener axis only",
                },
            },
        }),
    );
    root.insert(
        "determinism".into(),
        json!({
            "floats": "f64_only",
            "reductions": "ordered (canonical cell enumeration, sequential gate evaluation)",
            "rng": "none (exhaustive 16-cell enumeration)",
        }),
    );
    root.insert(
        "results".into(),
        json!({
            "n_cells": cells.len(),
            "expected_cartesian_total": expected_total,
            "cartesian_accounting_matches_fixture": true,
            "n_solved": solved.len(),
            "n_infeasible": infeasible.len(),
            "solved_cell_indices": solved,
            "infeasible_cell_indices": infeasible,
            "cells": cell_reports,
            "fixture_declared_infeasible_count_note": format!(
                "the fixture's expected_infeasible_candidate_count = {declared_infeasible} refers to DECLARATIVE Cartesian accounting only (feasibility_basis DECLARATIVE_ACCOUNTING_ONLY); this demo overlays real dosing/hazard gates on top, which is why its partition differs"
            ),
        }),
    );
    root.insert(
        "ghs_data_integrity_caveat".into(),
        json!({
            "campaign_item": "R-N01",
            "note": "the pinned GHS KPI has a documented CID-attribution defect for IPDA and m-XDA (R-N01 fire-1 audit, cited in sources); IPDA cells' GHS rows therefore carry a data-integrity caveat until the superseding hazard-card receipt lands. The IPDA hard-exclusion outcome (none) and advisory flags used here also rest on the ECHA harmonised classification entries cited in the same card.",
        }),
    );
    root.insert("pareto_status".into(), json!("PARTITIONED"));
    Ok(Value::Object(root))
}
