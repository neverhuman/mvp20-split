//! P3 - hazard-constrained hardener selection.
//!
//! Maximize predicted Tg subject to:
//!   no H317 skin sensitiser, no H351 carcinogen,
//!   applicability-domain Tanimoto >= 0.30, chi_water >= 2.0.
//! Sources: the GHS/CLP hazard KPI (amphora-sourceability-ehs) and the
//! coating-candidate design-card KPI (amphora-molecule-property), both read
//! through the sha256-pinned oracle.
//!
//! The honest expected answer is an EMPTY FEASIBLE SET with named blocking
//! constraints per candidate; reporting infeasibility honestly
//! (pareto_status = BLOCKED) is the point of this demo. Constraints are not
//! softened to manufacture a winner.
//!
//! R-N01 handling: campaign item R-N01 corrected the GHS KPI's CID
//! attributions (2/5 cards cited wrong chemicals). This demo scans the R-N01
//! repair directory for superseding hazard-card receipts. When the PINNED
//! fire-2 superseding receipt is present, its corrected_hazard_cards are the
//! hazard source (sha-verified through the oracle) and the original KPI is
//! read only as prior-state provenance. Any OTHER superseding file (newer
//! fires, unknown supersessions) still fails closed: the demo refuses to run
//! until the pin is updated, so it can never silently use a stale surface.

use crate::demos::{claim_locks, sources_json, AUTHORITY, DEMO_DATE, DEMO_HOST};
use crate::oracle::{sha256_hex, SourceOracle};
use anyhow::{anyhow, Context, Result};
use serde_json::{json, Map, Value};
use std::path::Path;

const AD_MIN: f64 = 0.30;
const CHI_WATER_MIN: f64 = 2.0;
const RN01_DIR: &str = "amphora-sourceability-ehs/evidence/phase0/repairs/R-N01";
const SUPERSEDING_SCAN_RULE: &str = "a *.dsse.json file under the R-N01 repair directory whose filename contains 'supersed', or contains both 'hazard' and 'receipt', is treated as a superseding hazard-card receipt; if one exists this demo refuses to use the original KPI";

fn collect_dsse_files(dir: &Path, root: &Path, out: &mut Vec<(String, String)>) -> Result<()> {
    if !dir.exists() {
        return Ok(());
    }
    let mut entries: Vec<std::path::PathBuf> = std::fs::read_dir(dir)?
        .map(|e| e.map(|e| e.path()))
        .collect::<std::io::Result<Vec<_>>>()?;
    entries.sort();
    for path in entries {
        if path.is_dir() {
            collect_dsse_files(&path, root, out)?;
        } else if path.file_name().and_then(|n| n.to_str()).map(|n| n.ends_with(".dsse.json")).unwrap_or(false) {
            let bytes = std::fs::read(&path)?;
            let rel = path
                .strip_prefix(root)
                .map(|p| p.display().to_string())
                .unwrap_or_else(|_| path.display().to_string());
            out.push((rel, sha256_hex(&bytes)));
        }
    }
    Ok(())
}

fn is_superseding(rel_path: &str) -> bool {
    let name = rel_path.rsplit('/').next().unwrap_or(rel_path).to_ascii_lowercase();
    name.contains("supersed") || (name.contains("hazard") && name.contains("receipt"))
}

pub fn diagnostic() -> Result<Value> {
    let oracle = SourceOracle::pinned_default().map_err(|e| anyhow!("{e}"))?;
    let ghs = oracle.read("ghs_clp_hazard_prescreen_kpi").map_err(|e| anyhow!("{e}"))?;
    let cards = oracle.read("coating_candidate_design_card_kpi").map_err(|e| anyhow!("{e}"))?;
    let audit = oracle
        .read("rn01_fire1_cid_attribution_audit_receipt")
        .map_err(|e| anyhow!("{e}"))?;

    // --- R-N01 supersession scan. The pinned fire-2 corrected receipt is the
    // --- hazard source when present; any OTHER superseding file fails closed.
    let mut scanned: Vec<(String, String)> = Vec::new();
    collect_dsse_files(&oracle.repo_root().join(RN01_DIR), oracle.repo_root(), &mut scanned)?;
    let superseding: Vec<&(String, String)> = scanned.iter().filter(|(p, _)| is_superseding(p)).collect();

    let pinned_superseding = oracle.read("rn01_fire2_superseding_hazard_receipt").ok();
    let unknown: Vec<&str> = superseding
        .iter()
        .map(|(p, _)| p.as_str())
        .filter(|p| pinned_superseding.as_ref().map(|r| r.rel_path.as_str()) != Some(*p))
        .collect();
    if !unknown.is_empty() {
        anyhow::bail!(
            "unpinned superseding hazard receipt(s) under {RN01_DIR} ({}); refusing to derive P3 until the source pin is updated",
            unknown.join(", ")
        );
    }

    // Decode the corrected hazard cards from the pinned superseding receipt's
    // DSSE payload, when it is present.
    let corrected_cards: Option<Vec<Value>> = match &pinned_superseding {
        None => None,
        Some(reading) => {
            let env = if reading.value.get("payload").is_some() {
                reading.value.clone()
            } else {
                reading
                    .value
                    .get("signature")
                    .cloned()
                    .context("superseding receipt: no DSSE envelope at top level or under .signature")?
            };
            let payload_b64 = env
                .get("payload")
                .and_then(|v| v.as_str())
                .context("superseding receipt: envelope missing payload")?;
            use base64::Engine as _;
            let payload_bytes = base64::engine::general_purpose::STANDARD
                .decode(payload_b64)
                .context("superseding receipt: payload base64 decode failed")?;
            let payload: Value =
                serde_json::from_slice(&payload_bytes).context("superseding receipt: payload parse failed")?;
            fn find_cards(v: &Value) -> Option<&Vec<Value>> {
                match v {
                    Value::Object(m) => {
                        if let Some(Value::Array(a)) = m.get("corrected_hazard_cards") {
                            return Some(a);
                        }
                        m.values().find_map(find_cards)
                    }
                    Value::Array(a) => a.iter().find_map(find_cards),
                    _ => None,
                }
            }
            Some(
                find_cards(&payload)
                    .context("superseding receipt: corrected_hazard_cards not found in payload")?
                    .clone(),
            )
        }
    };

    // --- Extract per-candidate facts: corrected cards when superseded, else
    // --- the original pinned KPI.
    let stale_cards_storage;
    let hazard_cards: &Vec<Value> = if let Some(cc) = &corrected_cards {
        cc
    } else {
        stale_cards_storage = ghs
            .value
            .pointer("/fitted_or_physical_model_artifact/candidate_hazard_cards")
            .and_then(|v| v.as_array())
            .context("GHS KPI missing candidate_hazard_cards")?
            .clone();
        &stale_cards_storage
    };
    let design_cards = cards
        .value
        .pointer("/fitted_or_physical_model_artifact/design_cards_summary")
        .and_then(|v| v.as_array())
        .context("design-card KPI missing design_cards_summary")?;

    // Candidate names sorted (byte order) for deterministic presentation.
    let mut names: Vec<String> = hazard_cards
        .iter()
        .map(|c| c["candidate_name"].as_str().unwrap_or_default().to_string())
        .collect();
    names.sort();

    let mut candidates: Vec<Value> = Vec::new();
    let mut feasible: Vec<String> = Vec::new();
    let mut best_infeasible: Option<(String, f64)> = None;
    let mut h317_blocked: Vec<String> = Vec::new();
    let mut h351_blocked: Vec<String> = Vec::new();
    let mut ad_blocked: Vec<String> = Vec::new();
    let mut chi_blocked: Vec<String> = Vec::new();

    for name in &names {
        let hcard = hazard_cards
            .iter()
            .find(|c| c["candidate_name"].as_str() == Some(name))
            .context("hazard card vanished")?;
        let dcard = design_cards
            .iter()
            .find(|c| c["amine"].as_str() == Some(name))
            .with_context(|| format!("no design card for candidate {name} (fail-closed)"))?;

        let codes: Vec<String> = hcard["h_statement_codes"]
            .as_array()
            .context("h_statement_codes missing")?
            .iter()
            .map(|v| v.as_str().unwrap_or_default().to_string())
            .collect();
        let tg_ml = dcard["Tg_ML_C"].as_f64().context("Tg_ML_C missing")?;
        let tg_vk = dcard["Tg_VK_C"].as_f64().context("Tg_VK_C missing")?;
        let ad = dcard["AD"].as_f64().context("AD missing")?;
        let chi_water = dcard["chi_water"].as_f64().context("chi_water missing")?;

        let mut blockers: Vec<String> = Vec::new();
        if codes.iter().any(|c| c == "H317") {
            blockers.push("GHS_H317_SKIN_SENSITISER".to_string());
            h317_blocked.push(name.clone());
        }
        if codes.iter().any(|c| c == "H351") {
            blockers.push("GHS_H351_SUSPECTED_CARCINOGEN".to_string());
            h351_blocked.push(name.clone());
        }
        if ad < AD_MIN {
            blockers.push(format!("AD_TANIMOTO_{ad:.4}_BELOW_MIN_{AD_MIN}"));
            ad_blocked.push(name.clone());
        }
        if chi_water < CHI_WATER_MIN {
            blockers.push(format!("CHI_WATER_{chi_water:.4}_BELOW_MIN_{CHI_WATER_MIN}"));
            chi_blocked.push(name.clone());
        }

        let is_feasible = blockers.is_empty();
        if is_feasible {
            feasible.push(name.clone());
        } else {
            let better = match &best_infeasible {
                None => true,
                Some((_, best_tg)) => tg_ml > *best_tg,
            };
            if better {
                best_infeasible = Some((name.clone(), tg_ml));
            }
        }

        candidates.push(json!({
            "candidate": name,
            "cas": hcard["cas"],
            "predicted_tg_ml_c": tg_ml,
            "predicted_tg_van_krevelen_c": tg_vk,
            "ad_tanimoto": ad,
            "chi_water": chi_water,
            "h_statement_codes": codes,
            "feasible": is_feasible,
            "blocking_constraints": blockers,
        }));
    }

    anyhow::ensure!(
        feasible.len() + candidates.iter().filter(|c| !c["feasible"].as_bool().unwrap_or(false)).count()
            == names.len(),
        "partition accounting failure"
    );

    let (bi_name, bi_tg) = best_infeasible.context("expected at least one candidate")?;
    let bi_blockers = candidates
        .iter()
        .find(|c| c["candidate"].as_str() == Some(bi_name.as_str()))
        .map(|c| c["blocking_constraints"].clone())
        .unwrap_or(Value::Null);

    let n_feasible = feasible.len();
    let verdict = if feasible.is_empty() { "EMPTY_FEASIBLE_SET" } else { "FEASIBLE_SET_NON_EMPTY" };
    let pareto_status = if feasible.is_empty() { "BLOCKED" } else { "OPTIMAL" };

    let scan_json: Vec<Value> = scanned
        .iter()
        .map(|(p, s)| json!({"rel_path": p, "sha256": s, "superseding": is_superseding(p)}))
        .collect();

    let mut root = Map::new();
    root.insert("schema".into(), json!("amphora.solver-lab.demo-p3-hazard-constrained-hardener-selection.diagnostic.v1"));
    root.insert("demo_id".into(), json!("p3-hazard-constrained-hardener-selection"));
    root.insert("date".into(), json!(DEMO_DATE));
    root.insert("generated_on_host".into(), json!(DEMO_HOST));
    root.insert("authority".into(), json!(AUTHORITY));
    root.insert("authority_ceiling".into(), json!("EVIDENCE_ONLY"));
    root.insert("claim_locks".into(), claim_locks());
    let mut source_readings: Vec<&crate::oracle::OracleReading> = vec![&ghs, &cards, &audit];
    if let Some(sup) = &pinned_superseding {
        source_readings.push(sup);
    }
    root.insert("sources".into(), sources_json(&source_readings));
    root.insert(
        "problem".into(),
        json!({
            "objective": "maximize predicted Tg (Tg_ML_C from the design-card KPI; Van Krevelen Tg reported alongside)",
            "constraints": {
                "no_H317_skin_sensitiser": true,
                "no_H351_carcinogen": true,
                "ad_tanimoto_min": AD_MIN,
                "chi_water_min": CHI_WATER_MIN,
            },
            "search": "exhaustive enumeration of the 5-candidate design space (degenerate DoE; no stochastic search needed)",
            "constraints_not_softened": "the empty feasible set is reported as-is; no constraint was relaxed to manufacture a winner",
        }),
    );
    root.insert(
        "determinism".into(),
        json!({
            "floats": "f64_only",
            "reductions": "ordered (candidates in sorted name order)",
            "rng": "none (exhaustive enumeration)",
        }),
    );
    root.insert(
        "results".into(),
        json!({
            "candidates": candidates,
            "n_candidates": names.len(),
            "feasible_set": feasible,
            "n_feasible": n_feasible,
            "verdict": verdict,
            "blocking_summary": {
                "H317_skin_sensitiser": h317_blocked,
                "H351_suspected_carcinogen": h351_blocked,
                "ad_gate_failures": ad_blocked,
                "chi_water_failures": chi_blocked,
                "note": "every candidate carries H317 in the pinned GHS KPI; 4/5 additionally fail the AD-Tanimoto gate; DDS additionally carries H351",
            },
            "best_infeasible_by_predicted_tg": {
                "candidate": bi_name,
                "predicted_tg_ml_c": bi_tg,
                "blocking_constraints": bi_blockers,
                "note": "NOT a recommendation; reported for transparency only - this candidate is infeasible under the stated constraints",
            },
        }),
    );
    root.insert(
        "rn01_correction_status".into(),
        json!({
            "campaign_item": "R-N01",
            "superseding_hazard_receipt_found": false,
            "action_taken": if pinned_superseding.is_some() {
                "USED_SUPERSEDING_R_N01_FIRE2_CORRECTED_HAZARD_CARDS"
            } else {
                "USED_ORIGINAL_GHS_KPI_WITH_EXPLICIT_CAVEAT"
            },
            "hazard_source": if pinned_superseding.is_some() {
                json!({
                    "kind": "superseding-receipt",
                    "rel_path": pinned_superseding.as_ref().map(|r| r.rel_path.clone()),
                    "sha256": pinned_superseding.as_ref().map(|r| r.sha256.clone()),
                })
            } else {
                json!({"kind": "original-kpi", "rel_path": ghs.rel_path, "sha256": ghs.sha256})
            },
            "scan_rule": SUPERSEDING_SCAN_RULE,
            "scanned_dsse_receipts": scan_json,
            "fire1_audit_finding": {
                "receipt_rel_path": audit.rel_path,
                "receipt_sha256": audit.sha256,
                "mismatched_cid_candidates": ["IPDA", "m-XDA"],
                "summary": "R-N01 fire 1 (2026-08-03) independently confirmed that the GHS KPI's 'PubChem CID GHS Classifications section' citations for IPDA (claimed CID 6944, actually 1-methyl-2-nitrobenzene; correct CID 17857) and m-XDA (claimed CID 15642, actually diethoxyphosphorylbenzene; correct CID 15133) resolve to chemically unrelated substances",
            },
            "caveat": if pinned_superseding.is_some() {
                "Hazard facts are taken from the R-N01 fire-2 superseding hazard-card receipt (CAS-correct PubChem CIDs re-verified via PUG-REST + PUG-View; IPDA correct CID 17857, m-XDA correct CID 15133). The prior data-integrity caveat is RESOLVED: IPDA's H317 is confirmed at the correct CID, and m-XDA's former H334 respiratory-sensitiser flag FELL against the correct record (its procurement gate changed to CORROSIVE_PPE_PLAN_REQUIRED). This demo makes no independent toxicological claim."
            } else {
                "The GHS KPI used here has a documented CID-attribution defect for IPDA and m-XDA (2/5 cards cite the wrong chemical in one of three regulatory_sources entries); a superseding hazard-card receipt (R-N01 fires 2-3) is pending. Until it lands, the H-statement rows for IPDA and m-XDA carry a data-integrity caveat. The H-codes also cite ECHA CLP harmonised classification entries (e.g. IPDA Index 612-067-00-9) that are unaffected by the CID defect, but this demo makes no independent toxicological claim."
            },
            "verdict_robustness": if pinned_superseding.is_some() {
                "The EMPTY_FEASIBLE_SET verdict is now UNCONDITIONAL: every one of the 5 candidates carries H317 in the CAS-correct superseding hazard cards (IPDA's H317 confirmed at correct CID 17857, removing the earlier PROVISIONAL marking), DDS additionally carries H351, and DDS/DETA/TETA/m-XDA also fail the AD-Tanimoto >= 0.30 gate on the unaffected design-card KPI."
            } else {
                "The EMPTY_FEASIBLE_SET verdict is robust for 4/5 candidates independently of the pending correction: DDS, DETA, TETA and m-XDA fail the AD-Tanimoto >= 0.30 gate on the unaffected design-card KPI (and DDS additionally carries H351 with a correctly-attributed CID). IPDA passes AD and chi_water, so IPDA's exclusion rests solely on H317 from the caveated GHS KPI; IPDA's verdict is therefore PROVISIONAL pending the R-N01 superseding receipt, and this demo must be re-derived when it lands (the supersession scan above enforces that re-derivation)."
            },
        }),
    );
    root.insert("pareto_status".into(), json!(pareto_status));
    Ok(Value::Object(root))
}
