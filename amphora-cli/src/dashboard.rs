use amphora_core::Phase1PortfolioStatusV1;
use anyhow::{anyhow, Result};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::fs;
use std::path::Path;

const DASHBOARD_PATH: &str = "config/program/portfolio-progress-dashboard.v1.json";
const DATA_AUDIT_PATH: &str = "feedback/v2/reports/audit-report.json";
const LEAKAGE_PATH: &str = "feedback/v2/reports/leakage-report.json";
const WORK_ORDERS_PATH: &str = "config/program/phase0-closure-phase1-work-orders.v1.json";
const TRAJECTORY_PATH: &str = "config/program/data-activation-promotion-trajectory.v2.json";
const FEEDBACK_STATUS_PATH: &str = "feedback/v2/reports/portfolio-status.txt";

pub(crate) fn write(root: &Path, phase0: &Value, phase1: &Phase1PortfolioStatusV1) -> Result<()> {
    sync_generated_status(root, phase1)?;
    let data = read_json(&root.join(DATA_AUDIT_PATH)).unwrap_or_else(|_| json!({}));
    let leakage = read_json(&root.join(LEAKAGE_PATH)).unwrap_or_else(|_| json!({}));
    let trajectory = read_json(&root.join(TRAJECTORY_PATH)).unwrap_or_else(|_| json!({}));
    let work_orders = read_json(&root.join(WORK_ORDERS_PATH)).unwrap_or_else(|_| json!({}));
    let phase0_modules = phase0
        .get("modules")
        .and_then(Value::as_array)
        .ok_or_else(|| anyhow!("Phase-0 portfolio status has no modules"))?;
    let mut benchmark_prepared = 0;
    let mut benchmark_executed = 0;
    let mut benchmark_passed = 0;
    let mut phase0_evaluations = 0;
    let mut phase0_reviews = 0;
    let mut phase0_movements = 0;
    let mut modules = Vec::new();
    for row in phase0_modules {
        let module_id = row
            .get("module_id")
            .and_then(Value::as_str)
            .ok_or_else(|| anyhow!("Phase-0 module ID is absent"))?;
        if row.get("prepared").and_then(Value::as_bool) == Some(true) {
            benchmark_prepared += 1;
        }
        phase0_evaluations +=
            usize::from(row.get("evaluation_signed").and_then(Value::as_bool) == Some(true));
        phase0_reviews +=
            usize::from(row.get("review_signed").and_then(Value::as_bool) == Some(true));
        phase0_movements += usize::from(row.get("movement_event").is_some_and(|v| !v.is_null()));
        let result_path = root
            .join(module_id)
            .join("evidence/phase0/benchmark/result.v1.json");
        if let Ok(result) = read_json(&result_path) {
            if result
                .get("benchmark_execution_complete")
                .and_then(Value::as_bool)
                == Some(true)
            {
                benchmark_executed += 1;
            }
            if matches!(
                result.get("scientific_outcome").and_then(Value::as_str),
                Some("PASSED" | "NOT_APPLICABLE")
            ) {
                benchmark_passed += 1;
            }
        }
        let phase1_row = phase1
            .modules
            .iter()
            .find(|candidate| candidate.module_id == module_id);
        let next_action = phase1_row
            .filter(|candidate| candidate.phase != "PRE_PHASE_0")
            .and_then(|candidate| candidate.failed_gates.first().map(String::as_str))
            .or_else(|| {
                row.get("failed_gates")
                    .and_then(Value::as_array)
                    .and_then(|gates| gates.first())
                    .and_then(Value::as_str)
            })
            .unwrap_or(
                if phase1_row.is_some_and(|candidate| candidate.phase == "PHASE_1") {
                    "NO_PHASE_MOVEMENT_ACTION_REQUIRED"
                } else {
                    "PREPARE_PHASE1_ONLY_AFTER_CURRENT_PHASE0_VERIFIES"
                },
            );
        modules.push(json!({
            "module_id": module_id,
            "phase": phase1_row.map(|row| row.phase.as_str()).unwrap_or("PRE_PHASE_0"),
            "next_evidence_changing_action": next_action,
        }));
    }
    let phase1_evaluations = phase1
        .modules
        .iter()
        .filter(|row| row.evaluation_signed)
        .count();
    let phase1_reviews = phase1
        .modules
        .iter()
        .filter(|row| row.review_signed)
        .count();
    let phase1_movements = phase1
        .modules
        .iter()
        .filter(|row| row.phase == "PHASE_1")
        .count();
    let expected_bindings = data
        .get("expected_materialized_binding_count")
        .and_then(Value::as_u64)
        .unwrap_or(30);
    let materialized = data
        .get("materialized_binding_count")
        .and_then(Value::as_u64)
        .unwrap_or(0);
    let mut discrepancies = Vec::new();
    if phase1.module_count != 29
        || phase1.phase1_count + phase1.phase0_count + phase1.pre_phase0_count != 29
    {
        discrepancies.push("PHASE_COUNTS_DO_NOT_RESOLVE_TO_29_MODULES");
    }
    if materialized != expected_bindings {
        discrepancies.push("MODULE_ACTIVATION_COUNT_INCOMPLETE");
    }
    if data.get("status").and_then(Value::as_str) != Some("PASS") {
        discrepancies.push("DATA_AUDIT_NOT_PASSING");
    }
    if leakage
        .get("point2_train_test_identity_overlap_count")
        .and_then(Value::as_u64)
        .unwrap_or(0)
        != 0
    {
        discrepancies.push("POINT2_SPLIT_IDENTITY_OVERLAP_REQUIRES_REGROUP_OR_EXCLUSION");
    }
    if trajectory
        .pointer("/current_state/phase0")
        .and_then(Value::as_u64)
        != Some(phase1.phase0_count as u64)
        || trajectory
            .pointer("/current_state/phase1")
            .and_then(Value::as_u64)
            != Some(phase1.phase1_count as u64)
        || trajectory
            .pointer("/current_state/pre_phase0")
            .and_then(Value::as_u64)
            != Some(phase1.pre_phase0_count as u64)
    {
        discrepancies.push("TRAJECTORY_COUNTS_DIFFER_FROM_LIVE_MOVEMENTS");
    }
    let work_order_status = work_orders.get("status").cloned().unwrap_or(Value::Null);
    let work_order_rows = work_orders
        .get("work_orders")
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
        .map(|order| {
            json!({
                "work_order_id": order.get("work_order_id"),
                "modules": order.get("modules"),
                "owner": order.get("owner").cloned().unwrap_or_else(|| json!("UNASSIGNED_IN_SOURCE")),
                "owner_candidates": order.get("counterparties"),
                "status": order.get("status").cloned().unwrap_or_else(|| work_order_status.clone()),
                "due_date": order.get("due_date").cloned().unwrap_or(Value::Null),
                "blocker_age_days": order.get("blocker_age_days").cloned().unwrap_or(Value::Null),
            })
        })
        .collect::<Vec<_>>();
    let report = json!({
        "schema": "amphora.portfolio-progress-dashboard.v1",
        "authority_change": false,
        "ranking_enabled": false,
        "phase_counts": {
            "phase1": phase1.phase1_count,
            "phase0": phase1.phase0_count,
            "pre_phase0": phase1.pre_phase0_count,
        },
        "data": {
            "acquisition_units": data.get("acquisition_unit_count"),
            "acquired_units": data.get("acquired_unit_count"),
            "normalized_units": data.get("normalized_unit_count"),
            "normalized_rows": data.get("normalized_row_count"),
            "blocked_units": data.get("declared_blocked_unit_count"),
            "pending_units": data.get("pending_unit_count"),
            "quarantine_bindings": data.get("quarantine_binding_count"),
        },
        "module_activations": {
            "materialized": materialized,
            "expected": expected_bindings,
            "rights_reviewed": data.get("rights_reviewed_binding_count"),
        },
        "split_and_leakage": {
            "cross_dataset_identity_overlaps": leakage.get("cross_dataset_canonical_identity_overlap_count"),
            "point2_train_test_identity_overlaps": leakage.get("point2_train_test_identity_overlap_count"),
            "status": leakage.get("status"),
        },
        "benchmarks": {
            "prepared": benchmark_prepared,
            "executed": benchmark_executed,
            "passed_or_not_applicable": benchmark_passed,
        },
        "receipts_and_movements": {
            "phase0_evaluations": phase0_evaluations,
            "phase0_reviews": phase0_reviews,
            "phase0_movements": phase0_movements,
            "phase1_evaluations": phase1_evaluations,
            "phase1_reviews": phase1_reviews,
            "phase1_movements": phase1_movements,
        },
        "modules": modules,
        "external_work_orders": work_order_rows,
        "failed_gates": discrepancies,
    });
    write_json(&root.join(DASHBOARD_PATH), &report)
}

fn read_json(path: &Path) -> Result<Value> {
    Ok(serde_json::from_slice(&fs::read(path)?)?)
}

fn write_json(path: &Path, value: &Value) -> Result<()> {
    let mut bytes = serde_json::to_vec_pretty(value)?;
    bytes.push(b'\n');
    if fs::read(path).ok().as_deref() != Some(bytes.as_slice()) {
        fs::write(path, bytes)?;
    }
    Ok(())
}

fn sync_generated_status(root: &Path, phase1: &Phase1PortfolioStatusV1) -> Result<()> {
    let decision_report = root.join("config/program/phase0-decision-report.v2.json");
    let digest = Sha256::digest(fs::read(&decision_report)?);
    let decision_hash = digest
        .iter()
        .map(|byte| format!("{byte:02x}"))
        .collect::<String>();
    let trajectory_path = root.join(TRAJECTORY_PATH);
    let mut trajectory = read_json(&trajectory_path)?;
    trajectory["current_state"]["module_count"] = json!(phase1.module_count);
    trajectory["current_state"]["phase0"] = json!(phase1.phase0_count);
    trajectory["current_state"]["pre_phase0"] = json!(phase1.pre_phase0_count);
    trajectory["current_state"]["phase1"] = json!(phase1.phase1_count);
    trajectory["current_state"]["decision_report_sha256"] = json!(decision_hash);
    write_json(&trajectory_path, &trajectory)?;

    let status = format!(
        "GENERATED FROM CURRENT VALID MOVEMENTS\nPhase 1: {}/{}\nPhase 0: {}/{}\nPre-Phase 0: {}/{}\nRanking enabled: false\n",
        phase1.phase1_count,
        phase1.module_count,
        phase1.phase0_count,
        phase1.module_count,
        phase1.pre_phase0_count,
        phase1.module_count,
    );
    let path = root.join(FEEDBACK_STATUS_PATH);
    if fs::read(&path).ok().as_deref() != Some(status.as_bytes()) {
        fs::write(path, status)?;
    }
    Ok(())
}
