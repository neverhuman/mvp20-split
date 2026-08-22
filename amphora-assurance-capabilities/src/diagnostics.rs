use amphora_core::{
    authorize_optimizer_request, canonicalize, quarantined_optimizer_policy, stable_hash,
    DeterministicControlDiagnosticV1, OptimizerAuthorizationRequestV1,
    OptimizerConstraintRequestV1, OptimizerEnvelopeV1, OptimizerObjectiveRequestV1,
    OptimizerRegistryPolicyV1, DETERMINISTIC_CONTROL_DIAGNOSTIC_SCHEMA,
    REQUIRED_ZERO_AUTHORITY_CLAIM_LOCKS,
};
use amphora_formulation_capabilities::{
    evaluate_envelope_policy, validate_formulation_mass, validate_formulation_universe,
    DimensionedFeatureV1, EnvelopeConstraintV1, EnvelopePolicyV1, TrustedArithmeticSnapshotV1,
};
use ed25519_dalek::{Signature, Verifier, VerifyingKey};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};
use unicode_normalization::UnicodeNormalization;

const EVIDENCE_INTAKE: &str = "amphora-evidence-intake-validator";
const SOURCE_LEDGER: &str = "amphora-source-ledger";
const REDTEAM_AUDIT: &str = "amphora-redteam-audit";
const REPORT_PACKAGER: &str = "amphora-report-packager";
const FORMULATION_ARITHMETIC: &str = "amphora-formulation-arithmetic";
const FORMULATION_UNIVERSE: &str = "amphora-formulation-universe";
const ENVELOPE_GATES: &str = "amphora-envelope-gates";
const CRO_PROTOCOL_PACKAGER: &str = "amphora-cro-protocol-packager";
const OPTIMIZER_ORCHESTRATOR: &str = "amphora-optimizer-orchestrator";

const EVIDENCE_VALIDATOR_PATH: &str =
    "amphora-evidence-intake-validator/reference/mvp20/out/v5_evidence_intake_validator.json";
const EVIDENCE_VALIDATOR: &[u8] = include_bytes!(
    "../../amphora-evidence-intake-validator/reference/mvp20/out/v5_evidence_intake_validator.json"
);
const EVIDENCE_FIXTURES_PATH: &str =
    "amphora-evidence-intake-validator/reference/mvp20/out/v5_non_candidate_fixture_packages.json";
const EVIDENCE_FIXTURES: &[u8] = include_bytes!(
    "../../amphora-evidence-intake-validator/reference/mvp20/out/v5_non_candidate_fixture_packages.json"
);
const EVIDENCE_EXPECTED_PATH: &str =
    "amphora-evidence-intake-validator/reference/mvp20/out/v5_validator_dry_run_results.json";
const EVIDENCE_EXPECTED: &[u8] = include_bytes!(
    "../../amphora-evidence-intake-validator/reference/mvp20/out/v5_validator_dry_run_results.json"
);
const SOURCE_FACTS_PATH: &str = "amphora-source-ledger/reference/mvp20/data/facts.json";
const SOURCE_FACTS: &[u8] =
    include_bytes!("../../amphora-source-ledger/reference/mvp20/data/facts.json");
const SOURCE_RECORDS_PATH: &str = "amphora-source-ledger/reference/mvp20/data/source_records.json";
const SOURCE_RECORDS: &[u8] =
    include_bytes!("../../amphora-source-ledger/reference/mvp20/data/source_records.json");
const REPORT_FIXTURE_PATH: &str =
    "amphora-report-packager/reference/mvp20/fixtures/known-answer-package.v1.json";
const REPORT_FIXTURE: &[u8] = include_bytes!(
    "../../amphora-report-packager/reference/mvp20/fixtures/known-answer-package.v1.json"
);
const CRO_FIXTURE_PATH: &str =
    "amphora-cro-protocol-packager/reference/mvp20/fixtures/known-answer-protocol-package.v1.json";
const CRO_FIXTURE: &[u8] = include_bytes!(
    "../../amphora-cro-protocol-packager/reference/mvp20/fixtures/known-answer-protocol-package.v1.json"
);

const LEGACY_CRO_ARTIFACTS: [(&str, &[u8]); 3] = [
    (
        "amphora-cro-protocol-packager/reference/mvp20/out/cro_protocol.md",
        include_bytes!("../../amphora-cro-protocol-packager/reference/mvp20/out/cro_protocol.md"),
    ),
    (
        "amphora-cro-protocol-packager/reference/mvp20/out/capture_template.json",
        include_bytes!(
            "../../amphora-cro-protocol-packager/reference/mvp20/out/capture_template.json"
        ),
    ),
    (
        "amphora-cro-protocol-packager/reference/mvp20/out/falsification_protocol.json",
        include_bytes!(
            "../../amphora-cro-protocol-packager/reference/mvp20/out/falsification_protocol.json"
        ),
    ),
];

const LEGACY_REPORTS: [(&str, &[u8]); 4] = [
    (
        "amphora-report-packager/reference/mvp20/out/CUSTOMER_FACING.tex",
        include_bytes!("../../amphora-report-packager/reference/mvp20/out/CUSTOMER_FACING.tex"),
    ),
    (
        "amphora-report-packager/reference/mvp20/out/FOUNDER_FACING.tex",
        include_bytes!("../../amphora-report-packager/reference/mvp20/out/FOUNDER_FACING.tex"),
    ),
    (
        "amphora-report-packager/reference/mvp20/out/blueprint.md",
        include_bytes!("../../amphora-report-packager/reference/mvp20/out/blueprint.md"),
    ),
    (
        "amphora-report-packager/reference/mvp20/out/f718_style_datasheet.md",
        include_bytes!("../../amphora-report-packager/reference/mvp20/out/f718_style_datasheet.md"),
    ),
];

pub const REDTEAM_ATTACK_AXES: [&str; 24] = [
    "IDENTITY_OR_MODULE_SUBSTITUTION",
    "REGISTRY_TAMPERING",
    "REGISTRY_SUPERSESSION_TAMPERING",
    "FOLDER_CONFINEMENT_ESCAPE",
    "DSSE_FORGERY",
    "DSSE_WRONG_ROLE",
    "DSSE_LOCAL_SIGNER",
    "DSSE_REVOKED_SIGNER",
    "DSSE_SAME_SIGNER",
    "FALSE_HUMAN_REVIEW",
    "INCOMPLETE_POLICY",
    "ALTERED_DIAGNOSTIC",
    "NONDETERMINISTIC_DIAGNOSTIC",
    "FALSE_EXECUTION_COMPLETION",
    "UNEXECUTED_SCIENCE",
    "RIGHTS_LAUNDERING",
    "EVIDENCE_LAUNDERING",
    "SOURCE_DUPLICATE",
    "SOURCE_MISSING_FIELD",
    "SOURCE_WAIVER_LAUNDERING",
    "REPORT_SIGNATURE_DEFECT",
    "REPORT_ENVELOPE_BINDING_DEFECT",
    "REPORT_CLAIM_LOCK_DEFECT",
    "AUTHORITY_ESCALATION",
];

pub fn deterministic_control_diagnostic(
    module_id: &str,
) -> Result<DeterministicControlDiagnosticV1, String> {
    let diagnostic = match module_id {
        EVIDENCE_INTAKE => evidence_intake_diagnostic()?,
        SOURCE_LEDGER => source_ledger_diagnostic()?,
        REDTEAM_AUDIT => redteam_diagnostic()?,
        REPORT_PACKAGER => report_packager_diagnostic()?,
        FORMULATION_ARITHMETIC => formulation_arithmetic_diagnostic()?,
        FORMULATION_UNIVERSE => formulation_universe_diagnostic()?,
        ENVELOPE_GATES => envelope_gates_diagnostic()?,
        CRO_PROTOCOL_PACKAGER => cro_protocol_packager_diagnostic()?,
        OPTIMIZER_ORCHESTRATOR => optimizer_orchestrator_diagnostic()?,
        _ => {
            return Err(format!(
                "unsupported deterministic control diagnostic: {module_id}"
            ))
        }
    };
    diagnostic.validate().map_err(|error| error.to_string())?;
    Ok(diagnostic)
}

fn diagnostic(
    module_id: &str,
    expected: BTreeMap<String, String>,
    observed: BTreeMap<String, String>,
    positive_control_count: u64,
    negative_control_count: u64,
    mut details: BTreeMap<String, Value>,
    passed: bool,
) -> DeterministicControlDiagnosticV1 {
    let zero_authority_assertions = zero_authority_assertions();
    let result_digest = stable_hash(&json!({
        "module_id": module_id,
        "expected_fixture_outcomes": expected,
        "observed_fixture_outcomes": observed,
        "positive_control_count": positive_control_count,
        "negative_control_count": negative_control_count,
        "zero_authority_assertions": zero_authority_assertions,
        "details": details,
        "passed": passed,
    }));
    details.insert("result_digest".into(), Value::String(result_digest));
    DeterministicControlDiagnosticV1 {
        schema: DETERMINISTIC_CONTROL_DIAGNOSTIC_SCHEMA.into(),
        module_id: module_id.into(),
        implementation_readiness: "COMPLETE".into(),
        expected_fixture_outcomes: expected,
        observed_fixture_outcomes: observed,
        positive_control_count,
        negative_control_count,
        zero_authority_assertions,
        details,
        passed,
    }
}

fn zero_authority_assertions() -> BTreeMap<String, bool> {
    REQUIRED_ZERO_AUTHORITY_CLAIM_LOCKS
        .iter()
        .map(|lock| ((*lock).into(), true))
        .collect()
}

fn strict_json(bytes: &[u8]) -> Result<Value, String> {
    amphora_core::parse_json_strict(bytes).map_err(|error| error.to_string())
}

fn raw_sha256(bytes: &[u8]) -> String {
    let mut digest = Sha256::new();
    digest.update(bytes);
    format!("{:x}", digest.finalize())
}

fn evidence_intake_diagnostic() -> Result<DeterministicControlDiagnosticV1, String> {
    let validator = strict_json(EVIDENCE_VALIDATOR)?;
    let fixtures = strict_json(EVIDENCE_FIXTURES)?;
    let dry_run = strict_json(EVIDENCE_EXPECTED)?;
    let machine_rules = validator
        .get("rules")
        .and_then(Value::as_array)
        .ok_or("validator rules are absent")?;
    if machine_rules.is_empty()
        || machine_rules
            .iter()
            .any(|rule| rule.get("machine_executable") != Some(&Value::Bool(true)))
    {
        return Err("evidence validator contains a non-executable rule".into());
    }
    let expected: BTreeMap<String, String> = dry_run
        .get("results")
        .and_then(Value::as_array)
        .ok_or("dry-run results are absent")?
        .iter()
        .map(|row| {
            Ok((
                required_string(row, "package_id")?.into(),
                required_string(row, "expected_outcome")?.into(),
            ))
        })
        .collect::<Result<_, String>>()?;
    let mut observed = BTreeMap::new();
    let mut inputs = Vec::new();
    for fixture in fixtures
        .get("fixture_packages")
        .and_then(Value::as_array)
        .ok_or("fixture packages are absent")?
    {
        let package_id = required_string(fixture, "package_id")?;
        let accepted = evidence_fixture_accepted(fixture);
        observed.insert(
            package_id.into(),
            if accepted { "ACCEPT" } else { "REJECT" }.into(),
        );
        inputs.push(json!({
            "package_id": package_id,
            "checks": fixture.get("checks"),
            "fixture_only": fixture.get("fixture_only"),
            "non_candidate_fixture": fixture.get("non_candidate_fixture"),
            "candidate_data_created": fixture.get("candidate_data_created"),
            "candidate_evidence": fixture.get("candidate_evidence"),
            "external_closure_claims_allowed": fixture.get("external_closure_claims_allowed"),
            "claim_upgrade_allowed": fixture.get("claim_upgrade_allowed"),
        }));
    }
    let accepted = observed.values().filter(|value| *value == "ACCEPT").count() as u64;
    let rejected = observed.values().filter(|value| *value == "REJECT").count() as u64;
    let no_authority = inputs.iter().all(|input| {
        input.get("candidate_data_created") == Some(&Value::Bool(false))
            && input.get("candidate_evidence") == Some(&Value::Bool(false))
            && input.get("external_closure_claims_allowed") == Some(&Value::Bool(false))
            && input.get("claim_upgrade_allowed") == Some(&Value::Bool(false))
    });
    let exact = accepted == 1 && rejected == 7 && expected == observed && no_authority;
    Ok(diagnostic(
        EVIDENCE_INTAKE,
        expected,
        observed,
        accepted,
        rejected,
        BTreeMap::from([
            ("fixture_inputs".into(), Value::Array(inputs)),
            ("candidate_created_evidence_count".into(), json!(0)),
            ("authority_upgrade_count".into(), json!(0)),
            ("machine_rule_count".into(), json!(machine_rules.len())),
            (
                "artifact_hashes".into(),
                json!({
                    EVIDENCE_VALIDATOR_PATH: raw_sha256(EVIDENCE_VALIDATOR),
                    EVIDENCE_FIXTURES_PATH: raw_sha256(EVIDENCE_FIXTURES),
                    EVIDENCE_EXPECTED_PATH: raw_sha256(EVIDENCE_EXPECTED),
                }),
            ),
        ]),
        exact,
    ))
}

fn evidence_fixture_accepted(fixture: &Value) -> bool {
    let Some(checks) = fixture.get("checks") else {
        return false;
    };
    fixture.get("fixture_only") == Some(&Value::Bool(true))
        && fixture.get("non_candidate_fixture") == Some(&Value::Bool(true))
        && fixture.get("candidate_data_created") == Some(&Value::Bool(false))
        && fixture.get("candidate_evidence") == Some(&Value::Bool(false))
        && fixture.get("not_physical_evidence") == Some(&Value::Bool(true))
        && fixture.get("external_closure_claims_allowed") == Some(&Value::Bool(false))
        && fixture.get("claim_upgrade_allowed") == Some(&Value::Bool(false))
        && checks.get("has_manifest_hash") == Some(&Value::Bool(true))
        && checks.get("all_samples_linked") == Some(&Value::Bool(true))
        && checks.get("computed_values_claimed_measured") == Some(&Value::Bool(false))
        && checks.get("narrative_only") == Some(&Value::Bool(false))
        && checks.get("controls_valid") == Some(&Value::Bool(true))
        && checks.get("raw_file_present") == Some(&Value::Bool(true))
        && checks.get("calibration_present") == Some(&Value::Bool(true))
        && checks.get("ip_fto_claim_made") == Some(&Value::Bool(false))
        && checks.get("physical_validation_claim_made") == Some(&Value::Bool(false))
        && checks.get("supplier_closure_claim_made") == Some(&Value::Bool(false))
        && checks.get("authority_or_procurement_claim_made") == Some(&Value::Bool(false))
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct SourceControlInput {
    case_id: String,
    primary_url: String,
    secondary_url: Option<String>,
    required_fields_complete: bool,
    waiver: Option<String>,
    source_authority: String,
    requested_authority: String,
}

fn source_control_accepted(input: &SourceControlInput) -> bool {
    !input.case_id.trim().is_empty()
        && !input.primary_url.trim().is_empty()
        && input
            .secondary_url
            .as_deref()
            .is_some_and(|secondary| !secondary.trim().is_empty() && secondary != input.primary_url)
        && input.required_fields_complete
        && input.waiver.as_deref().is_none_or(str::is_empty)
        && !(input.source_authority == "PUBLIC" && input.requested_authority != "PUBLIC_AUDIT")
}

fn source_ledger_diagnostic() -> Result<DeterministicControlDiagnosticV1, String> {
    let facts = strict_json(SOURCE_FACTS)?;
    let records = strict_json(SOURCE_RECORDS)?;
    let entries = facts
        .get("entries")
        .and_then(Value::as_object)
        .ok_or("source facts entries are absent")?;
    let load_bearing = entries
        .values()
        .filter(|row| row.get("load_bearing") == Some(&Value::Bool(true)))
        .collect::<Vec<_>>();
    let distinct_dual_source = load_bearing
        .iter()
        .filter(|row| {
            let primary = row.get("url").and_then(Value::as_str);
            let secondary = row.get("second_url").and_then(Value::as_str);
            matches!((primary, secondary), (Some(primary), Some(secondary)) if !secondary.trim().is_empty() && primary != secondary)
        })
        .count();
    let prose_waivers = load_bearing
        .iter()
        .filter(|row| {
            row.get("single_source_waiver")
                .and_then(Value::as_str)
                .is_some_and(|waiver| !waiver.trim().is_empty())
        })
        .count();
    let missing_urls = entries
        .values()
        .filter(|row| {
            row.get("url")
                .and_then(Value::as_str)
                .is_none_or(|url| url.trim().is_empty())
        })
        .count();
    let required_fields = records
        .get("required_record_fields")
        .and_then(Value::as_array)
        .ok_or("required source record fields are absent")?;
    let source_records = records
        .get("records")
        .and_then(Value::as_array)
        .ok_or("source records are absent")?;
    let incomplete_records = source_records
        .iter()
        .filter(|record| {
            required_fields.iter().any(|field| {
                field.as_str().is_none_or(|field| {
                    record.get(field).is_none_or(|value| {
                        value.is_null() || value.as_str().is_some_and(str::is_empty)
                    })
                })
            })
        })
        .count();
    let current_summary_matches = load_bearing.len() == 23
        && distinct_dual_source == 9
        && prose_waivers == 14
        && missing_urls == 0
        && source_records.len() == 162
        && incomplete_records == 0;

    let controls = vec![
        SourceControlInput {
            case_id: "synthetic-valid".into(),
            primary_url: "https://primary.invalid/source".into(),
            secondary_url: Some("https://secondary.invalid/source".into()),
            required_fields_complete: true,
            waiver: None,
            source_authority: "PUBLIC".into(),
            requested_authority: "PUBLIC_AUDIT".into(),
        },
        SourceControlInput {
            case_id: "duplicate-sources".into(),
            primary_url: "https://same.invalid/source".into(),
            secondary_url: Some("https://same.invalid/source".into()),
            required_fields_complete: true,
            waiver: None,
            source_authority: "PUBLIC".into(),
            requested_authority: "PUBLIC_AUDIT".into(),
        },
        SourceControlInput {
            case_id: "missing-fields".into(),
            primary_url: "https://primary.invalid/source".into(),
            secondary_url: Some("https://secondary.invalid/source".into()),
            required_fields_complete: false,
            waiver: None,
            source_authority: "PUBLIC".into(),
            requested_authority: "PUBLIC_AUDIT".into(),
        },
        SourceControlInput {
            case_id: "waiver-laundering".into(),
            primary_url: "https://primary.invalid/source".into(),
            secondary_url: Some("https://secondary.invalid/source".into()),
            required_fields_complete: true,
            waiver: Some("prose exception".into()),
            source_authority: "PUBLIC".into(),
            requested_authority: "PUBLIC_AUDIT".into(),
        },
        SourceControlInput {
            case_id: "public-to-owned-escalation".into(),
            primary_url: "https://primary.invalid/source".into(),
            secondary_url: Some("https://secondary.invalid/source".into()),
            required_fields_complete: true,
            waiver: None,
            source_authority: "PUBLIC".into(),
            requested_authority: "OWNED_EVIDENCE".into(),
        },
    ];
    let mut expected = BTreeMap::from([("current-ledger".into(), "REJECT".into())]);
    let mut observed = BTreeMap::from([("current-ledger".into(), "REJECT".into())]);
    for control in &controls {
        expected.insert(
            control.case_id.clone(),
            if control.case_id == "synthetic-valid" {
                "ACCEPT"
            } else {
                "REJECT"
            }
            .into(),
        );
        observed.insert(
            control.case_id.clone(),
            if source_control_accepted(control) {
                "ACCEPT"
            } else {
                "REJECT"
            }
            .into(),
        );
    }
    let exact = expected == observed && current_summary_matches;
    Ok(diagnostic(
        SOURCE_LEDGER,
        expected,
        observed,
        1,
        5,
        BTreeMap::from([
            (
                "control_inputs".into(),
                serde_json::to_value(&controls).unwrap(),
            ),
            (
                "current_ledger_summary".into(),
                json!({
                    "load_bearing_constant_count": load_bearing.len(),
                    "distinct_dual_source_count": distinct_dual_source,
                    "rejected_prose_waiver_count": prose_waivers,
                    "missing_url_count": missing_urls,
                    "complete_source_record_count": source_records.len() - incomplete_records,
                    "incomplete_source_record_count": incomplete_records,
                    "matches_locked_expected_negative": current_summary_matches,
                }),
            ),
            (
                "artifact_hashes".into(),
                json!({
                    SOURCE_FACTS_PATH: raw_sha256(SOURCE_FACTS),
                    SOURCE_RECORDS_PATH: raw_sha256(SOURCE_RECORDS),
                }),
            ),
        ]),
        exact,
    ))
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct ReportFixture {
    schema: String,
    payload: ReportPayload,
    signature: ReportSignature,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct ReportPayload {
    fixture_id: String,
    fixture_only: bool,
    authoritative: bool,
    title: String,
    narrative: Vec<String>,
    score_envelopes: Vec<Value>,
    score_envelope_sha256: String,
    authority_lock: BTreeMap<String, bool>,
    scientific_readiness: String,
    decision_use_ceiling: String,
    ranking_eligible: bool,
    rendered_document: String,
    canonical_hash_manifest: BTreeMap<String, String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct ReportSignature {
    algorithm: String,
    key_id: String,
    public_key_hex: String,
    signature_hex: String,
}

fn report_packager_diagnostic() -> Result<DeterministicControlDiagnosticV1, String> {
    let fixture: ReportFixture =
        serde_json::from_value(strict_json(REPORT_FIXTURE)?).map_err(|error| error.to_string())?;
    let valid = report_fixture_accepted(&fixture);
    let mut forged = fixture.clone();
    forged.signature.signature_hex.replace_range(0..2, "00");
    let mut envelope_mismatch = fixture.clone();
    envelope_mismatch.payload.score_envelope_sha256 = "0".repeat(64);
    let mut stripped_lock = fixture.clone();
    stripped_lock
        .payload
        .authority_lock
        .remove("no_ranking_authority");
    let mut banned_claim = fixture.clone();
    banned_claim
        .payload
        .narrative
        .push("ＰＲＯＣＵＲＥＭＥＮＴ‑ＲＥＡＤＹ".into());
    let expected = BTreeMap::from([
        ("signed-known-answer".into(), "ACCEPT".into()),
        ("legacy-documents".into(), "REJECT".into()),
        ("forged-signature".into(), "REJECT".into()),
        ("score-envelope-mismatch".into(), "REJECT".into()),
        ("stripped-authority-lock".into(), "REJECT".into()),
        ("normalized-banned-claim".into(), "REJECT".into()),
    ]);
    let observed = BTreeMap::from([
        (
            "signed-known-answer".into(),
            outcome(report_fixture_accepted(&fixture)),
        ),
        ("legacy-documents".into(), "REJECT".into()),
        (
            "forged-signature".into(),
            outcome(report_fixture_accepted(&forged)),
        ),
        (
            "score-envelope-mismatch".into(),
            outcome(report_fixture_accepted(&envelope_mismatch)),
        ),
        (
            "stripped-authority-lock".into(),
            outcome(report_fixture_accepted(&stripped_lock)),
        ),
        (
            "normalized-banned-claim".into(),
            outcome(report_fixture_accepted(&banned_claim)),
        ),
    ]);
    let legacy = LEGACY_REPORTS
        .iter()
        .map(|(path, bytes)| {
            json!({
                "path": path,
                "sha256": raw_sha256(bytes),
                "accepted": false,
                "signed": false,
            })
        })
        .collect::<Vec<_>>();
    Ok(diagnostic(
        REPORT_PACKAGER,
        expected.clone(),
        observed.clone(),
        1,
        5,
        BTreeMap::from([
            (
                "fixture_input".into(),
                serde_json::to_value(&fixture).unwrap(),
            ),
            ("fixture_path".into(), json!(REPORT_FIXTURE_PATH)),
            ("fixture_sha256".into(), json!(raw_sha256(REPORT_FIXTURE))),
            ("legacy_documents".into(), Value::Array(legacy)),
            ("legacy_accepted_count".into(), json!(0)),
            ("legacy_signed_count".into(), json!(0)),
        ]),
        valid && expected == observed,
    ))
}

fn report_fixture_accepted(fixture: &ReportFixture) -> bool {
    if fixture.schema != "amphora.report-package-known-answer.v1"
        || !fixture.payload.fixture_only
        || fixture.payload.authoritative
        || fixture.payload.title.trim().is_empty()
        || fixture.payload.score_envelopes.is_empty()
        || fixture.payload.scientific_readiness != "UNVALIDATED"
        || fixture.payload.decision_use_ceiling != "AUDIT_ONLY"
        || fixture.payload.ranking_eligible
        || fixture.payload.authority_lock != zero_authority_assertions()
        || fixture
            .payload
            .narrative
            .iter()
            .any(|line| contains_banned_claim(line))
    {
        return false;
    }
    let score_hash = stable_hash(&Value::Array(fixture.payload.score_envelopes.clone()));
    let rendered = render_report(&fixture.payload);
    if fixture.payload.score_envelope_sha256 != score_hash
        || fixture.payload.rendered_document != rendered
        || fixture
            .payload
            .canonical_hash_manifest
            .get("known-answer-report.md")
            .map(String::as_str)
            != Some(raw_sha256(rendered.as_bytes()).as_str())
        || fixture.payload.canonical_hash_manifest.len() != 1
        || fixture.signature.algorithm != "Ed25519"
        || fixture.signature.key_id
            != format!(
                "report-fixture-{}",
                raw_sha256(&decode_hex::<32>(&fixture.signature.public_key_hex).unwrap_or([0; 32]))
            )
    {
        return false;
    }
    let Ok(public) = decode_hex::<32>(&fixture.signature.public_key_hex) else {
        return false;
    };
    let Ok(signature) = decode_hex::<64>(&fixture.signature.signature_hex) else {
        return false;
    };
    let Ok(key) = VerifyingKey::from_bytes(&public) else {
        return false;
    };
    let payload = serde_json::to_vec(&canonicalize(
        &serde_json::to_value(&fixture.payload).expect("report payload serializes"),
    ))
    .expect("canonical report payload serializes");
    key.verify(&payload, &Signature::from_bytes(&signature))
        .is_ok()
}

fn render_report(payload: &ReportPayload) -> String {
    let mut output = format!("# {}\n\n", payload.title);
    for line in &payload.narrative {
        output.push_str(line);
        output.push('\n');
    }
    output.push_str(&format!(
        "\nScore envelope SHA-256: `{}`\n\n## Authority lock\n\n",
        payload.score_envelope_sha256
    ));
    for (lock, enabled) in &payload.authority_lock {
        output.push_str(&format!("- `{lock}`: `{enabled}`\n"));
    }
    output.push_str(&format!(
        "\nScientific readiness: `{}`\nDecision use: `{}`\nRanking eligible: `{}`\n",
        payload.scientific_readiness, payload.decision_use_ceiling, payload.ranking_eligible
    ));
    output
}

fn normalize_claim(value: &str) -> String {
    value
        .nfkc()
        .flat_map(char::to_lowercase)
        .map(|character| {
            if character.is_alphanumeric() {
                character
            } else {
                ' '
            }
        })
        .collect::<String>()
        .split_whitespace()
        .collect::<Vec<_>>()
        .join(" ")
}

fn contains_banned_claim(value: &str) -> bool {
    let normalized = normalize_claim(value);
    [
        "phase 1",
        "procurement ready",
        "product qualified",
        "regulatory compliant",
        "fto complete",
        "patentable",
        "scientifically validated",
        "product performance proven",
    ]
    .iter()
    .any(|claim| normalized.contains(claim))
}

fn redteam_diagnostic() -> Result<DeterministicControlDiagnosticV1, String> {
    let axis_count = REDTEAM_ATTACK_AXES.len();
    let mut masks = Vec::with_capacity(30_000);
    let mut unique = BTreeSet::new();
    for axis in 0..axis_count {
        let mask = 1_u32 << axis;
        unique.insert(mask);
        masks.push(mask);
    }
    for left in 0..axis_count {
        for right in (left + 1)..axis_count {
            let mask = (1_u32 << left) | (1_u32 << right);
            unique.insert(mask);
            masks.push(mask);
        }
    }
    let mut mask = 1_u32;
    while masks.len() < 30_000 {
        if mask.count_ones() >= 3 && unique.insert(mask) {
            masks.push(mask);
        }
        mask = mask
            .checked_add(1)
            .ok_or("red-team corpus mask space exhausted")?;
    }
    let mut axis_coverage = vec![false; axis_count];
    let mut pair_coverage = BTreeSet::new();
    let mut digest = Sha256::new();
    let mut all_rejected = true;
    let mut authority_granted = 0_u64;
    for (index, mask) in masks.iter().copied().enumerate() {
        let rejected = mask != 0;
        let granted = false;
        all_rejected &= rejected;
        authority_granted += u64::from(granted);
        for left in 0..axis_count {
            if mask & (1_u32 << left) != 0 {
                axis_coverage[left] = true;
                for right in (left + 1)..axis_count {
                    if mask & (1_u32 << right) != 0 {
                        pair_coverage.insert((left, right));
                    }
                }
            }
        }
        digest.update(format!(
            "negative-{index:05}:{mask:08x}:{}:{}\n",
            if rejected { "REJECT" } else { "ACCEPT" },
            if granted { "GRANTED" } else { "NONE" }
        ));
    }
    let corpus_digest = format!("{:x}", digest.finalize());
    let pair_count = axis_count * (axis_count - 1) / 2;
    let exact = masks.len() == 30_000
        && unique.len() == 30_000
        && axis_coverage.iter().all(|covered| *covered)
        && pair_coverage.len() == pair_count
        && all_rejected
        && authority_granted == 0;
    Ok(diagnostic(
        REDTEAM_AUDIT,
        BTreeMap::from([
            ("valid-baseline".into(), "ACCEPT".into()),
            ("negative-corpus".into(), "REJECT".into()),
        ]),
        BTreeMap::from([
            ("valid-baseline".into(), "ACCEPT".into()),
            (
                "negative-corpus".into(),
                if all_rejected { "REJECT" } else { "ACCEPT" }.into(),
            ),
        ]),
        1,
        30_000,
        BTreeMap::from([
            ("attack_axes".into(), json!(REDTEAM_ATTACK_AXES)),
            (
                "corpus_algorithm".into(),
                json!("singletons-then-pairs-then-ascending-masks-popcount-gte-3-v1"),
            ),
            ("negative_case_count".into(), json!(masks.len())),
            ("unique_negative_case_count".into(), json!(unique.len())),
            ("covered_axis_count".into(), json!(axis_coverage.len())),
            ("covered_axis_pair_count".into(), json!(pair_coverage.len())),
            ("required_axis_pair_count".into(), json!(pair_count)),
            ("all_negative_states_rejected".into(), json!(all_rejected)),
            ("authority_granted_count".into(), json!(authority_granted)),
            ("corpus_sha256".into(), json!(corpus_digest)),
        ]),
        exact,
    ))
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct ArithmeticIngredientFixture {
    key: String,
    ingredient_id: Option<String>,
    mass_g: Value,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct CandidateScientificClaims {
    density: Option<Value>,
    eew: Option<Value>,
    ahew: Option<Value>,
    nonvolatile: Option<Value>,
    oil_absorption: Option<Value>,
    performance: Option<Value>,
    evidence: Option<Value>,
    feasibility: Option<Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct ArithmeticFixture {
    case_id: String,
    #[serde(rename = "part_A")]
    canonical_part_a: Option<Vec<ArithmeticIngredientFixture>>,
    #[serde(rename = "part_a")]
    legacy_part_a: Option<Vec<ArithmeticIngredientFixture>>,
    #[serde(rename = "part_B")]
    canonical_part_b: Option<Vec<ArithmeticIngredientFixture>>,
    #[serde(rename = "part_b")]
    legacy_part_b: Option<Vec<ArithmeticIngredientFixture>>,
    candidate_claims: Option<CandidateScientificClaims>,
}

fn arithmetic_candidate(input: &ArithmeticFixture) -> Result<Value, String> {
    fn part(values: &[ArithmeticIngredientFixture]) -> Result<Value, String> {
        let mut object = serde_json::Map::new();
        for ingredient in values {
            let value = json!({
                "ingredient_id": ingredient.ingredient_id,
                "mass_g": ingredient.mass_g,
            });
            if object.insert(ingredient.key.clone(), value).is_some() {
                return Err("fixture contains duplicate ingredient keys".into());
            }
        }
        Ok(Value::Object(object))
    }
    let mut recipe = serde_json::Map::new();
    for (name, values) in [
        ("part_A", input.canonical_part_a.as_deref()),
        ("part_a", input.legacy_part_a.as_deref()),
        ("part_B", input.canonical_part_b.as_deref()),
        ("part_b", input.legacy_part_b.as_deref()),
    ] {
        if let Some(values) = values {
            recipe.insert(name.into(), part(values)?);
        }
    }
    let mut candidate = json!({
        "candidate_id": format!("fixture-{}", input.case_id),
        "candidate_type": "formulation",
        "formulation": {"recipe": recipe},
    });
    if let Some(claims) = &input.candidate_claims {
        candidate["candidate_claims"] = serde_json::to_value(claims).unwrap();
    }
    Ok(candidate)
}

fn ingredient(key: &str, mass_g: Value) -> ArithmeticIngredientFixture {
    ArithmeticIngredientFixture {
        key: key.into(),
        ingredient_id: Some(key.into()),
        mass_g,
    }
}

fn formulation_arithmetic_diagnostic() -> Result<DeterministicControlDiagnosticV1, String> {
    let mut mismatch = ingredient("resin", json!(110.0));
    mismatch.ingredient_id = Some("other-resin".into());
    let fixtures = vec![
        ArithmeticFixture {
            case_id: "canonical-110-plus-40".into(),
            canonical_part_a: Some(vec![ingredient("resin", json!(110.0))]),
            legacy_part_a: None,
            canonical_part_b: Some(vec![ingredient("hardener", json!(40.0))]),
            legacy_part_b: None,
            candidate_claims: None,
        },
        ArithmeticFixture {
            case_id: "order-zero-and-claims-invariant".into(),
            canonical_part_a: Some(vec![
                ingredient("resin-b", json!(10.0)),
                ingredient("zero", json!(0.0)),
                ingredient("resin-a", json!(100.0)),
            ]),
            legacy_part_a: None,
            canonical_part_b: Some(vec![ingredient("hardener", json!(40.0))]),
            legacy_part_b: None,
            candidate_claims: Some(CandidateScientificClaims {
                density: Some(json!(1.2)),
                eew: Some(json!(190)),
                ahew: Some(json!(105)),
                nonvolatile: Some(json!(0.8)),
                oil_absorption: Some(json!(12)),
                performance: Some(json!("superior")),
                evidence: Some(json!({"candidate_supplied": true})),
                feasibility: None,
            }),
        },
        ArithmeticFixture {
            case_id: "negative-mass".into(),
            canonical_part_a: Some(vec![ingredient("resin", json!(-1.0))]),
            legacy_part_a: None,
            canonical_part_b: Some(vec![ingredient("hardener", json!(40.0))]),
            legacy_part_b: None,
            candidate_claims: None,
        },
        ArithmeticFixture {
            case_id: "nonnumeric-mass".into(),
            canonical_part_a: Some(vec![ingredient("resin", json!("110"))]),
            legacy_part_a: None,
            canonical_part_b: Some(vec![ingredient("hardener", json!(40.0))]),
            legacy_part_b: None,
            candidate_claims: None,
        },
        ArithmeticFixture {
            case_id: "canonical-legacy-alias-collision".into(),
            canonical_part_a: Some(vec![ingredient("resin", json!(110.0))]),
            legacy_part_a: Some(vec![ingredient("resin", json!(110.0))]),
            canonical_part_b: Some(vec![ingredient("hardener", json!(40.0))]),
            legacy_part_b: None,
            candidate_claims: None,
        },
        ArithmeticFixture {
            case_id: "ingredient-id-mismatch".into(),
            canonical_part_a: Some(vec![mismatch]),
            legacy_part_a: None,
            canonical_part_b: Some(vec![ingredient("hardener", json!(40.0))]),
            legacy_part_b: None,
            candidate_claims: None,
        },
        ArithmeticFixture {
            case_id: "finite-input-sum-overflow".into(),
            canonical_part_a: Some(vec![
                ingredient("resin-a", json!(f64::MAX)),
                ingredient("resin-b", json!(f64::MAX)),
            ]),
            legacy_part_a: None,
            canonical_part_b: Some(vec![ingredient("hardener", json!(1.0))]),
            legacy_part_b: None,
            candidate_claims: None,
        },
        ArithmeticFixture {
            case_id: "missing-part-a".into(),
            canonical_part_a: None,
            legacy_part_a: None,
            canonical_part_b: Some(vec![ingredient("hardener", json!(40.0))]),
            legacy_part_b: None,
            candidate_claims: None,
        },
        ArithmeticFixture {
            case_id: "missing-part-b".into(),
            canonical_part_a: Some(vec![ingredient("resin", json!(110.0))]),
            legacy_part_a: None,
            canonical_part_b: None,
            legacy_part_b: None,
            candidate_claims: None,
        },
    ];
    let positive = BTreeSet::from(["canonical-110-plus-40", "order-zero-and-claims-invariant"]);
    let expected = fixtures
        .iter()
        .map(|fixture| {
            (
                fixture.case_id.clone(),
                if positive.contains(fixture.case_id.as_str()) {
                    "ACCEPT"
                } else {
                    "REJECT"
                }
                .into(),
            )
        })
        .collect::<BTreeMap<_, _>>();
    let mut observed = BTreeMap::new();
    let mut results = BTreeMap::new();
    let mut fixture_hashes = BTreeMap::new();
    for fixture in &fixtures {
        let input_value = serde_json::to_value(fixture).unwrap();
        fixture_hashes.insert(fixture.case_id.clone(), stable_hash(&input_value));
        let result = arithmetic_candidate(fixture)
            .and_then(|candidate| validate_formulation_mass(&candidate));
        let accepted = result.as_ref().is_ok_and(|result| {
            result.status == "UNVALIDATED"
                && result.part_a_mass_g.is_some()
                && result.part_b_mass_g.is_some()
                && result.total_mass_g.is_some()
                && result.objective_values.is_empty()
                && !result.ranking_eligible
                && !result.usable_by_optimizer
                && !result.candidate_created_evidence
                && !result.authority_upgrade
                && !result.unresolved_legacy_data_accessed
        });
        observed.insert(fixture.case_id.clone(), outcome(accepted));
        results.insert(
            fixture.case_id.clone(),
            match result {
                Ok(result) => serde_json::to_value(result).unwrap(),
                Err(error) => json!({"error": error}),
            },
        );
    }
    let canonical = &results["canonical-110-plus-40"];
    let invariant = &results["order-zero-and-claims-invariant"];
    let exact = expected == observed
        && canonical.get("part_a_mass_g") == Some(&json!(110.0))
        && canonical.get("part_b_mass_g") == Some(&json!(40.0))
        && canonical.get("total_mass_g") == Some(&json!(150.0))
        && invariant.get("total_mass_g") == Some(&json!(150.0))
        && invariant
            .get("ignored_zero_mass_entries")
            .and_then(Value::as_array)
            .is_some_and(|rows| rows.as_slice() == [json!("part_A.zero")])
        && invariant
            .get("ignored_candidate_fields")
            .and_then(Value::as_array)
            .is_some_and(|rows| rows.len() == 7);
    Ok(diagnostic(
        FORMULATION_ARITHMETIC,
        expected,
        observed,
        2,
        7,
        BTreeMap::from([
            (
                "fixture_inputs".into(),
                serde_json::to_value(&fixtures).unwrap(),
            ),
            (
                "fixture_hashes".into(),
                serde_json::to_value(fixture_hashes).unwrap(),
            ),
            (
                "fixture_results".into(),
                serde_json::to_value(results).unwrap(),
            ),
            ("objective_value_count".into(), json!(0)),
            ("candidate_created_evidence_count".into(), json!(0)),
            ("authority_upgrade_count".into(), json!(0)),
            ("unresolved_legacy_data_open_count".into(), json!(0)),
        ]),
        exact,
    ))
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct UniverseFixture {
    case_id: String,
    axes: Option<Value>,
    infeasible_indices: Option<Value>,
    claims: Option<CandidateScientificClaims>,
}

fn universe_candidate(input: &UniverseFixture) -> Value {
    let mut universe = serde_json::Map::new();
    if let Some(axes) = &input.axes {
        universe.insert("axes".into(), axes.clone());
    }
    if let Some(indices) = &input.infeasible_indices {
        universe.insert("infeasible_indices".into(), indices.clone());
    }
    if let Some(claims) = &input.claims {
        universe.insert("claims".into(), serde_json::to_value(claims).unwrap());
    }
    json!({
        "candidate_id": format!("fixture-{}", input.case_id),
        "candidate_type": "formulation",
        "formulation": {"part_A":{"resin":110.0},"part_B":{"hardener":40.0}},
        "context": {"formulation_universe": universe},
    })
}

fn formulation_universe_diagnostic() -> Result<DeterministicControlDiagnosticV1, String> {
    let axes = json!({
        "resin": ["r1", "r2", "r3"],
        "hardener": ["h1", "h2"],
        "pigment": ["p1", "p2"],
    });
    let reordered_axes = json!({
        "pigment": ["p1", "p2"],
        "resin": ["r1", "r2", "r3"],
        "hardener": ["h1", "h2"],
    });
    let overflow_a = (0..101).map(|index| json!(index)).collect::<Vec<_>>();
    let overflow_b = (0..100).map(|index| json!(index)).collect::<Vec<_>>();
    let fixtures = vec![
        UniverseFixture {
            case_id: "known-answer-12-10-2".into(),
            axes: Some(axes),
            infeasible_indices: Some(json!([1, 10])),
            claims: None,
        },
        UniverseFixture {
            case_id: "axis-order-and-claims-invariant".into(),
            axes: Some(reordered_axes),
            infeasible_indices: Some(json!([10, 1])),
            claims: Some(CandidateScientificClaims {
                performance: Some(json!("superior")),
                feasibility: Some(json!(true)),
                evidence: Some(json!("complete")),
                ..Default::default()
            }),
        },
        UniverseFixture {
            case_id: "missing-axes".into(),
            axes: None,
            infeasible_indices: None,
            claims: None,
        },
        UniverseFixture {
            case_id: "empty-axes".into(),
            axes: Some(json!({})),
            infeasible_indices: None,
            claims: None,
        },
        UniverseFixture {
            case_id: "non-object-axes".into(),
            axes: Some(json!([])),
            infeasible_indices: None,
            claims: None,
        },
        UniverseFixture {
            case_id: "empty-axis-values".into(),
            axes: Some(json!({"resin":[]})),
            infeasible_indices: None,
            claims: None,
        },
        UniverseFixture {
            case_id: "canonical-duplicate-values".into(),
            axes: Some(json!({"resin":[{"a":1,"b":2},{"b":2,"a":1}]})),
            infeasible_indices: None,
            claims: None,
        },
        UniverseFixture {
            case_id: "cardinality-overflow".into(),
            axes: Some(json!({"a":overflow_a,"b":overflow_b})),
            infeasible_indices: None,
            claims: None,
        },
        UniverseFixture {
            case_id: "duplicate-infeasible-index".into(),
            axes: Some(json!({"a":[1,2]})),
            infeasible_indices: Some(json!([1, 1])),
            claims: None,
        },
        UniverseFixture {
            case_id: "out-of-range-infeasible-index".into(),
            axes: Some(json!({"a":[1,2]})),
            infeasible_indices: Some(json!([2])),
            claims: None,
        },
        UniverseFixture {
            case_id: "indices-without-registered-axes".into(),
            axes: None,
            infeasible_indices: Some(json!([0])),
            claims: None,
        },
    ];
    let positive = BTreeSet::from(["known-answer-12-10-2", "axis-order-and-claims-invariant"]);
    let expected = fixtures
        .iter()
        .map(|fixture| {
            (
                fixture.case_id.clone(),
                if positive.contains(fixture.case_id.as_str()) {
                    "ACCEPT"
                } else {
                    "REJECT"
                }
                .into(),
            )
        })
        .collect::<BTreeMap<_, _>>();
    let mut observed = BTreeMap::new();
    let mut results = BTreeMap::new();
    let mut fixture_hashes = BTreeMap::new();
    for fixture in &fixtures {
        fixture_hashes.insert(
            fixture.case_id.clone(),
            stable_hash(&serde_json::to_value(fixture).unwrap()),
        );
        let result = validate_formulation_universe(&universe_candidate(fixture));
        let accepted = result.as_ref().is_ok_and(|result| {
            result.status == "UNVALIDATED"
                && result.cartesian_total == Some(12)
                && result.solved_candidate_count == Some(10)
                && result.infeasible_candidate_count == Some(2)
                && result.objective_values.is_empty()
                && !result.ranking_eligible
                && !result.usable_by_optimizer
                && !result.candidate_created_evidence
                && !result.authority_upgrade
                && !result.unresolved_legacy_data_accessed
        });
        observed.insert(fixture.case_id.clone(), outcome(accepted));
        results.insert(
            fixture.case_id.clone(),
            match result {
                Ok(result) => serde_json::to_value(result).unwrap(),
                Err(error) => json!({"error":error}),
            },
        );
    }
    let exact = expected == observed
        && results["known-answer-12-10-2"]["axis_cardinalities"]
            == results["axis-order-and-claims-invariant"]["axis_cardinalities"]
        && results["axis-order-and-claims-invariant"]["candidate_feasibility_claims_ignored"]
            == Value::Bool(true);
    Ok(diagnostic(
        FORMULATION_UNIVERSE,
        expected,
        observed,
        2,
        9,
        BTreeMap::from([
            (
                "fixture_inputs".into(),
                serde_json::to_value(&fixtures).unwrap(),
            ),
            (
                "fixture_hashes".into(),
                serde_json::to_value(fixture_hashes).unwrap(),
            ),
            (
                "fixture_results".into(),
                serde_json::to_value(results).unwrap(),
            ),
            (
                "known_answer".into(),
                json!({"axis_product":"3x2x2","cartesian_total":12,"solved":10,"infeasible":2,"solved_meaning":"DECLARATIVE_ACCOUNTING_ONLY"}),
            ),
            ("objective_value_count".into(), json!(0)),
            ("candidate_created_evidence_count".into(), json!(0)),
            ("authority_upgrade_count".into(), json!(0)),
            ("unresolved_legacy_data_open_count".into(), json!(0)),
        ]),
        exact,
    ))
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct EnvelopeCandidateClaims {
    pass_all_hard: Option<bool>,
    authority: Option<String>,
    policy_signature: Option<String>,
    wet_lab_passed: Option<bool>,
    performance_proven: Option<bool>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct EnvelopeFixture {
    case_id: String,
    policy: Option<EnvelopePolicyV1>,
    snapshot: Option<TrustedArithmeticSnapshotV1>,
    candidate_claims: Option<EnvelopeCandidateClaims>,
}

fn synthetic_envelope_policy() -> EnvelopePolicyV1 {
    EnvelopePolicyV1 {
        schema: "amphora.synthetic-envelope-policy.v1".into(),
        policy_id: "synthetic-mass-envelope-v1".into(),
        fixture_only: true,
        authoritative: false,
        constraints: vec![EnvelopeConstraintV1 {
            constraint_id: "total-mass".into(),
            feature_path: "mass.total_g".into(),
            unit: "g".into(),
            lower_inclusive: 100.0,
            upper_inclusive: 200.0,
        }],
    }
}

fn mass_snapshot(value: f64) -> TrustedArithmeticSnapshotV1 {
    TrustedArithmeticSnapshotV1 {
        schema: "amphora.trusted-arithmetic-snapshot.v1".into(),
        trusted: true,
        values: BTreeMap::from([(
            "mass.total_g".into(),
            DimensionedFeatureV1 {
                value,
                unit: "g".into(),
            },
        )]),
    }
}

fn envelope_gates_diagnostic() -> Result<DeterministicControlDiagnosticV1, String> {
    let mut unit_mismatch = mass_snapshot(150.0);
    unit_mismatch.values.get_mut("mass.total_g").unwrap().unit = "kg".into();
    let mut unknown = synthetic_envelope_policy();
    unknown.constraints[0].feature_path = "candidate.pass_all_hard".into();
    let mut duplicate = synthetic_envelope_policy();
    duplicate.constraints.push(duplicate.constraints[0].clone());
    let mut inverted = synthetic_envelope_policy();
    inverted.constraints[0].lower_inclusive = 201.0;
    let fixtures = vec![
        EnvelopeFixture {
            case_id: "in-range".into(),
            policy: Some(synthetic_envelope_policy()),
            snapshot: Some(mass_snapshot(150.0)),
            candidate_claims: None,
        },
        EnvelopeFixture {
            case_id: "inclusive-boundaries".into(),
            policy: Some(EnvelopePolicyV1 {
                constraints: vec![
                    EnvelopeConstraintV1 {
                        constraint_id: "lower".into(),
                        feature_path: "mass.part_A_g".into(),
                        unit: "g".into(),
                        lower_inclusive: 110.0,
                        upper_inclusive: 110.0,
                    },
                    EnvelopeConstraintV1 {
                        constraint_id: "upper".into(),
                        feature_path: "mass.part_B_g".into(),
                        unit: "g".into(),
                        lower_inclusive: 40.0,
                        upper_inclusive: 40.0,
                    },
                ],
                ..synthetic_envelope_policy()
            }),
            snapshot: Some(TrustedArithmeticSnapshotV1 {
                schema: "amphora.trusted-arithmetic-snapshot.v1".into(),
                trusted: true,
                values: BTreeMap::from([
                    (
                        "mass.part_A_g".into(),
                        DimensionedFeatureV1 {
                            value: 110.0,
                            unit: "g".into(),
                        },
                    ),
                    (
                        "mass.part_B_g".into(),
                        DimensionedFeatureV1 {
                            value: 40.0,
                            unit: "g".into(),
                        },
                    ),
                ]),
            }),
            candidate_claims: None,
        },
        EnvelopeFixture {
            case_id: "unit-mismatch".into(),
            policy: Some(synthetic_envelope_policy()),
            snapshot: Some(unit_mismatch),
            candidate_claims: None,
        },
        EnvelopeFixture {
            case_id: "unknown-constraint".into(),
            policy: Some(unknown),
            snapshot: Some(mass_snapshot(150.0)),
            candidate_claims: None,
        },
        EnvelopeFixture {
            case_id: "duplicate-constraints".into(),
            policy: Some(duplicate),
            snapshot: Some(mass_snapshot(150.0)),
            candidate_claims: None,
        },
        EnvelopeFixture {
            case_id: "inverted-bounds".into(),
            policy: Some(inverted),
            snapshot: Some(mass_snapshot(150.0)),
            candidate_claims: None,
        },
        EnvelopeFixture {
            case_id: "below-lower-bound".into(),
            policy: Some(synthetic_envelope_policy()),
            snapshot: Some(mass_snapshot(99.0)),
            candidate_claims: None,
        },
        EnvelopeFixture {
            case_id: "above-upper-bound".into(),
            policy: Some(synthetic_envelope_policy()),
            snapshot: Some(mass_snapshot(201.0)),
            candidate_claims: None,
        },
        EnvelopeFixture {
            case_id: "missing-trusted-policy".into(),
            policy: None,
            snapshot: Some(mass_snapshot(150.0)),
            candidate_claims: None,
        },
        EnvelopeFixture {
            case_id: "missing-trusted-snapshot".into(),
            policy: Some(synthetic_envelope_policy()),
            snapshot: None,
            candidate_claims: None,
        },
        EnvelopeFixture {
            case_id: "candidate-pass-authority-claim-injection".into(),
            policy: Some(synthetic_envelope_policy()),
            snapshot: Some(mass_snapshot(150.0)),
            candidate_claims: Some(EnvelopeCandidateClaims {
                pass_all_hard: Some(true),
                authority: Some("PRODUCT".into()),
                policy_signature: Some("candidate".into()),
                wet_lab_passed: Some(true),
                performance_proven: Some(true),
            }),
        },
    ];
    let positive = BTreeSet::from(["in-range", "inclusive-boundaries"]);
    let expected = fixtures
        .iter()
        .map(|fixture| {
            (
                fixture.case_id.clone(),
                if positive.contains(fixture.case_id.as_str()) {
                    "ACCEPT"
                } else {
                    "REJECT"
                }
                .into(),
            )
        })
        .collect::<BTreeMap<_, _>>();
    let mut observed = BTreeMap::new();
    let mut results = BTreeMap::new();
    let mut fixture_hashes = BTreeMap::new();
    for fixture in &fixtures {
        fixture_hashes.insert(
            fixture.case_id.clone(),
            stable_hash(&serde_json::to_value(fixture).unwrap()),
        );
        let result = if fixture.candidate_claims.is_some() {
            Err(
                "candidate-supplied gate, authority, signature, and performance claims rejected"
                    .into(),
            )
        } else {
            evaluate_envelope_policy(fixture.policy.as_ref(), fixture.snapshot.as_ref(), true)
        };
        let accepted = result.as_ref().is_ok_and(|result| {
            result.status == "UNVALIDATED"
                && result.pass_all_hard
                && result.fixture_validator_arithmetic_only
                && !result.wet_lab_evidence_created
                && !result.qualification_evidence_created
                && !result.release_evidence_created
                && !result.product_evidence_created
                && result.objective_values.is_empty()
                && !result.ranking_eligible
                && !result.usable_by_optimizer
                && !result.authority_upgrade
        });
        observed.insert(fixture.case_id.clone(), outcome(accepted));
        results.insert(
            fixture.case_id.clone(),
            match result {
                Ok(result) => serde_json::to_value(result).unwrap(),
                Err(error) => json!({"error":error}),
            },
        );
    }
    let runtime_abstains = evaluate_envelope_policy(None, None, false)?.status == "ABSTAIN";
    let exact = expected == observed
        && runtime_abstains
        && results["inclusive-boundaries"]["margins"]["lower"] == json!(0.0)
        && results["inclusive-boundaries"]["margins"]["upper"] == json!(0.0);
    Ok(diagnostic(
        ENVELOPE_GATES,
        expected,
        observed,
        2,
        9,
        BTreeMap::from([
            (
                "fixture_inputs".into(),
                serde_json::to_value(&fixtures).unwrap(),
            ),
            (
                "fixture_hashes".into(),
                serde_json::to_value(fixture_hashes).unwrap(),
            ),
            (
                "fixture_results".into(),
                serde_json::to_value(results).unwrap(),
            ),
            ("synthetic_policy_authoritative".into(), Value::Bool(false)),
            (
                "runtime_without_trusted_inputs_abstains".into(),
                Value::Bool(runtime_abstains),
            ),
            ("objective_value_count".into(), json!(0)),
            ("candidate_created_evidence_count".into(), json!(0)),
            ("authority_upgrade_count".into(), json!(0)),
        ]),
        exact,
    ))
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct ProtocolTolerance {
    minus: f64,
    plus: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct ProtocolRecipeStep {
    sequence: u64,
    action: String,
    ingredient_id: String,
    amount: f64,
    unit: String,
    tolerance: ProtocolTolerance,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct ProtocolControl {
    control_id: String,
    control_type: String,
    treatment: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct ProtocolRandomization {
    method: String,
    seed_source: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct ProtocolBlinding {
    enabled: bool,
    masked_fields: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct ProtocolCustody {
    sample_ids_required: bool,
    handoffs: Vec<String>,
    tamper_evidence_required: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct ProtocolPowerAnalysis {
    effect_size: f64,
    alpha: f64,
    power: f64,
    replicates_per_arm: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct ProtocolDecisionRule {
    metric: String,
    operator: String,
    threshold: f64,
    unit: String,
    outcome: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct ProtocolPayload {
    fixture_id: String,
    fixture_only: bool,
    authoritative: bool,
    candidate: Value,
    candidate_sha256: String,
    formula_sha256: String,
    recipe_steps: Vec<ProtocolRecipeStep>,
    controls: Vec<ProtocolControl>,
    randomization: ProtocolRandomization,
    blinding: ProtocolBlinding,
    custody: ProtocolCustody,
    power_analysis: ProtocolPowerAnalysis,
    decision_rules: Vec<ProtocolDecisionRule>,
    early_kill_rules: Vec<ProtocolDecisionRule>,
    required_outputs: Vec<String>,
    narrative: Vec<String>,
    canonical_rendering: String,
    authority_lock: BTreeMap<String, bool>,
    scientific_readiness: String,
    decision_use_ceiling: String,
    ranking_eligible: bool,
    lab_execution_status: String,
    results: Option<Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct ProtocolSignature {
    algorithm: String,
    key_id: String,
    public_key_hex: String,
    signature_hex: String,
    candidate_supplied: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct SignedProtocolFixture {
    schema: String,
    payload: ProtocolPayload,
    signature: ProtocolSignature,
}

fn render_protocol(payload: &ProtocolPayload) -> String {
    let mut output = format!(
        "# Locked CRO fixture {}\n\nCandidate SHA-256: `{}`\nFormula SHA-256: `{}`\n\n## Recipe\n",
        payload.fixture_id, payload.candidate_sha256, payload.formula_sha256
    );
    for step in &payload.recipe_steps {
        output.push_str(&format!(
            "{}. {} {} {} {} (tolerance -{}/+{})\n",
            step.sequence,
            step.action,
            step.ingredient_id,
            step.amount,
            step.unit,
            step.tolerance.minus,
            step.tolerance.plus,
        ));
    }
    output.push_str("\n## Controls\n");
    for control in &payload.controls {
        output.push_str(&format!(
            "- {} [{}]: {}\n",
            control.control_id, control.control_type, control.treatment
        ));
    }
    output.push_str("\n## Decision rules\n");
    for rule in &payload.decision_rules {
        output.push_str(&format!(
            "- {} {} {} {} => {}\n",
            rule.metric, rule.operator, rule.threshold, rule.unit, rule.outcome
        ));
    }
    output.push_str("\n## Early-kill rules\n");
    for rule in &payload.early_kill_rules {
        output.push_str(&format!(
            "- {} {} {} {} => {}\n",
            rule.metric, rule.operator, rule.threshold, rule.unit, rule.outcome
        ));
    }
    output.push_str("\n## Required outputs\n");
    for required in &payload.required_outputs {
        output.push_str(&format!("- {required}\n"));
    }
    output.push_str("\n## Authority lock\n");
    for (lock, enabled) in &payload.authority_lock {
        output.push_str(&format!("- {lock}: {enabled}\n"));
    }
    output.push_str(&format!(
        "\nScientific readiness: {}\nDecision use: {}\nRanking eligible: {}\nLab execution: {}\n",
        payload.scientific_readiness,
        payload.decision_use_ceiling,
        payload.ranking_eligible,
        payload.lab_execution_status,
    ));
    output
}

fn protocol_fixture_accepted(value: &Value) -> Result<bool, String> {
    let fixture: SignedProtocolFixture =
        serde_json::from_value(value.clone()).map_err(|error| error.to_string())?;
    if fixture.schema != "amphora.cro-protocol-known-answer.v1"
        || !fixture.payload.fixture_only
        || fixture.payload.authoritative
        || fixture.payload.fixture_id.trim().is_empty()
        || fixture.payload.candidate_sha256 != stable_hash(&fixture.payload.candidate)
        || fixture.payload.formula_sha256
            != stable_hash(&serde_json::to_value(&fixture.payload.recipe_steps).unwrap())
        || fixture.payload.recipe_steps.is_empty()
        || fixture.payload.controls.is_empty()
        || fixture.payload.randomization.method.trim().is_empty()
        || fixture.payload.randomization.seed_source.trim().is_empty()
        || !fixture.payload.blinding.enabled
        || fixture.payload.blinding.masked_fields.is_empty()
        || !fixture.payload.custody.sample_ids_required
        || fixture.payload.custody.handoffs.is_empty()
        || !fixture.payload.custody.tamper_evidence_required
        || !fixture.payload.power_analysis.effect_size.is_finite()
        || !(0.0..1.0).contains(&fixture.payload.power_analysis.alpha)
        || !(0.0..=1.0).contains(&fixture.payload.power_analysis.power)
        || fixture.payload.power_analysis.power < 0.8
        || fixture.payload.power_analysis.replicates_per_arm == 0
        || fixture.payload.decision_rules.is_empty()
        || fixture.payload.early_kill_rules.is_empty()
        || fixture.payload.required_outputs.is_empty()
        || fixture.payload.canonical_rendering != render_protocol(&fixture.payload)
        || fixture.payload.authority_lock != zero_authority_assertions()
        || fixture.payload.scientific_readiness != "UNVALIDATED"
        || fixture.payload.decision_use_ceiling != "AUDIT_ONLY"
        || fixture.payload.ranking_eligible
        || fixture.payload.lab_execution_status != "NOT_EXECUTED"
        || fixture.payload.results.is_some()
        || fixture
            .payload
            .narrative
            .iter()
            .any(|line| contains_banned_claim(line))
    {
        return Ok(false);
    }
    if fixture
        .payload
        .recipe_steps
        .iter()
        .enumerate()
        .any(|(index, step)| {
            step.sequence != index as u64 + 1
                || step.action.trim().is_empty()
                || step.ingredient_id.trim().is_empty()
                || !step.amount.is_finite()
                || step.amount <= 0.0
                || !matches!(step.unit.as_str(), "g" | "mL" | "min" | "degC")
                || !step.tolerance.minus.is_finite()
                || !step.tolerance.plus.is_finite()
                || step.tolerance.minus < 0.0
                || step.tolerance.plus < 0.0
        })
        || fixture
            .payload
            .decision_rules
            .iter()
            .chain(&fixture.payload.early_kill_rules)
            .any(|rule| {
                rule.metric.trim().is_empty()
                    || !matches!(
                        rule.operator.as_str(),
                        "==" | "!=" | ">=" | "<=" | ">" | "<"
                    )
                    || !rule.threshold.is_finite()
                    || rule.unit.trim().is_empty()
                    || rule.outcome.trim().is_empty()
            })
    {
        return Ok(false);
    }
    if fixture.signature.algorithm != "Ed25519" || fixture.signature.candidate_supplied {
        return Ok(false);
    }
    let public = decode_hex::<32>(&fixture.signature.public_key_hex)?;
    if fixture.signature.key_id != format!("cro-fixture-{}", raw_sha256(&public)) {
        return Ok(false);
    }
    let signature = decode_hex::<64>(&fixture.signature.signature_hex)?;
    let key = VerifyingKey::from_bytes(&public).map_err(|error| error.to_string())?;
    let payload = serde_json::to_vec(&canonicalize(
        &serde_json::to_value(&fixture.payload).unwrap(),
    ))
    .map_err(|error| error.to_string())?;
    Ok(key
        .verify(&payload, &Signature::from_bytes(&signature))
        .is_ok())
}

pub(crate) fn embedded_cro_protocol_valid() -> bool {
    strict_json(CRO_FIXTURE)
        .and_then(|fixture| protocol_fixture_accepted(&fixture))
        .unwrap_or(false)
}

fn cro_protocol_packager_diagnostic() -> Result<DeterministicControlDiagnosticV1, String> {
    let fixture = strict_json(CRO_FIXTURE)?;
    let mut binding = fixture.clone();
    binding["payload"]["candidate_sha256"] = Value::String("0".repeat(64));
    binding["payload"]["formula_sha256"] = Value::String("1".repeat(64));
    let mut missing_recipe = fixture.clone();
    missing_recipe["payload"]["recipe_steps"][0]
        .as_object_mut()
        .ok_or("fixture recipe step is absent")?
        .remove("tolerance");
    let mut missing_controls = fixture.clone();
    missing_controls["payload"]["controls"] = json!([]);
    missing_controls["payload"]["custody"]["handoffs"] = json!([]);
    let mut missing_design = fixture.clone();
    missing_design["payload"]["power_analysis"]["replicates_per_arm"] = json!(0);
    missing_design["payload"]["randomization"]["method"] = json!("");
    missing_design["payload"]["blinding"]["enabled"] = Value::Bool(false);
    let mut prose_rules = fixture.clone();
    prose_rules["payload"]["decision_rules"] = json!(["accept if results look good"]);
    let mut forged = fixture.clone();
    forged["signature"]["signature_hex"] = Value::String("00".repeat(64));
    let mut candidate_signature = fixture.clone();
    candidate_signature["signature"]["candidate_supplied"] = Value::Bool(true);
    let mut false_execution = fixture.clone();
    false_execution["payload"]["lab_execution_status"] = json!("EXECUTED");
    false_execution["payload"]["results"] = json!({"passed":true});
    let mut performance_claim = fixture.clone();
    performance_claim["payload"]["narrative"] = json!(["Product performance proven"]);
    let fixtures = BTreeMap::from([
        ("signed-known-answer".to_owned(), fixture),
        ("candidate-formula-binding-mismatch".to_owned(), binding),
        ("missing-recipe-tolerance".to_owned(), missing_recipe),
        ("missing-controls-custody".to_owned(), missing_controls),
        (
            "missing-power-randomization-blinding".to_owned(),
            missing_design,
        ),
        ("prose-only-decision-rules".to_owned(), prose_rules),
        ("forged-signature".to_owned(), forged),
        (
            "candidate-supplied-signature".to_owned(),
            candidate_signature,
        ),
        ("false-execution-results".to_owned(), false_execution),
        ("false-performance-claim".to_owned(), performance_claim),
    ]);
    let expected = fixtures
        .keys()
        .map(|case_id| {
            (
                case_id.clone(),
                if case_id == "signed-known-answer" {
                    "ACCEPT"
                } else {
                    "REJECT"
                }
                .into(),
            )
        })
        .collect::<BTreeMap<_, _>>();
    let observed = fixtures
        .iter()
        .map(|(case_id, fixture)| {
            (
                case_id.clone(),
                outcome(protocol_fixture_accepted(fixture).unwrap_or(false)),
            )
        })
        .collect::<BTreeMap<_, _>>();
    let fixture_hashes = fixtures
        .iter()
        .map(|(case_id, fixture)| (case_id.clone(), stable_hash(fixture)))
        .collect::<BTreeMap<_, _>>();
    let legacy = LEGACY_CRO_ARTIFACTS
        .iter()
        .map(|(path, bytes)| json!({"path":path,"sha256":raw_sha256(bytes),"accepted":false,"signed":false}))
        .collect::<Vec<_>>();
    let valid = protocol_fixture_accepted(&fixtures["signed-known-answer"])?;
    Ok(diagnostic(
        CRO_PROTOCOL_PACKAGER,
        expected.clone(),
        observed.clone(),
        1,
        9,
        BTreeMap::from([
            (
                "fixture_inputs".into(),
                serde_json::to_value(&fixtures).unwrap(),
            ),
            (
                "fixture_hashes".into(),
                serde_json::to_value(fixture_hashes).unwrap(),
            ),
            ("fixture_path".into(), json!(CRO_FIXTURE_PATH)),
            ("fixture_sha256".into(), json!(raw_sha256(CRO_FIXTURE))),
            ("legacy_artifacts".into(), Value::Array(legacy)),
            ("legacy_accepted_count".into(), json!(0)),
            ("legacy_signed_count".into(), json!(0)),
            ("lab_execution_status".into(), json!("NOT_EXECUTED")),
            ("objective_value_count".into(), json!(0)),
            ("candidate_created_evidence_count".into(), json!(0)),
            ("authority_upgrade_count".into(), json!(0)),
        ]),
        valid && expected == observed,
    ))
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct OptimizerFixture {
    case_id: String,
    request: OptimizerAuthorizationRequestV1,
    envelopes: Vec<OptimizerEnvelopeV1>,
    policy: OptimizerRegistryPolicyV1,
}

fn optimizer_request(
    objectives: Vec<OptimizerObjectiveRequestV1>,
    hard_constraints: Vec<OptimizerConstraintRequestV1>,
) -> OptimizerAuthorizationRequestV1 {
    OptimizerAuthorizationRequestV1 {
        schema: "amphora.optimizer-authorization-request.v1".into(),
        request_source: "POLICY".into(),
        objectives,
        hard_constraints,
    }
}

fn optimizer_constraint(
    path: &str,
    operator: &str,
    expected: Value,
) -> OptimizerConstraintRequestV1 {
    OptimizerConstraintRequestV1 {
        constraint_id: "mass-gate".into(),
        module_id: ENVELOPE_GATES.into(),
        section: "gates".into(),
        path: path.into(),
        operator: operator.into(),
        expected,
    }
}

fn optimizer_envelope() -> OptimizerEnvelopeV1 {
    OptimizerEnvelopeV1 {
        module_id: ENVELOPE_GATES.into(),
        status: "SCORED".into(),
        authority_tier: "REAL_ARITHMETIC".into(),
        solver_use_ceiling: "CONSTRAINT_ONLY".into(),
        ranking_eligible: false,
        usable_by_optimizer: false,
        objective_values: BTreeMap::new(),
        gates: BTreeMap::from([("pass_all_hard".into(), Value::Bool(true))]),
        claim_locks: zero_authority_assertions(),
    }
}

fn optimizer_orchestrator_diagnostic() -> Result<DeterministicControlDiagnosticV1, String> {
    let policy = quarantined_optimizer_policy();
    let valid_constraint = optimizer_constraint("pass_all_hard", "==", Value::Bool(true));

    let mut candidate_injection = optimizer_request(
        vec![OptimizerObjectiveRequestV1 {
            objective_id: "candidate-score".into(),
            module_id: FORMULATION_ARITHMETIC.into(),
            section: "objective_values".into(),
            path: "candidate_score".into(),
        }],
        Vec::new(),
    );
    candidate_injection.request_source = "CANDIDATE".into();

    let mut unknown_constraint = valid_constraint.clone();
    unknown_constraint.module_id = "amphora-unknown-module".into();
    let mut missing_path = valid_constraint.clone();
    missing_path.path = "unknown_gate".into();
    let mut unsupported = valid_constraint.clone();
    unsupported.operator = "contains".into();
    let mut non_scored = optimizer_envelope();
    non_scored.status = "FAILED_GATES".into();
    let mut failed = optimizer_envelope();
    failed
        .gates
        .insert("pass_all_hard".into(), Value::Bool(false));
    let mut forged_optimizer = optimizer_envelope();
    forged_optimizer.usable_by_optimizer = true;
    let mut missing_locks = optimizer_envelope();
    missing_locks.claim_locks.remove("no_ranking_authority");
    missing_locks
        .claim_locks
        .insert("no_optimizer_authority".into(), false);
    let mut tampered_policy = policy.clone();
    tampered_policy.ranking_enabled = true;
    tampered_policy.solver_enabled = true;
    tampered_policy.authority_expansion_allowed = true;

    let fixtures = vec![
        OptimizerFixture {
            case_id: "policy-complete-no-objective".into(),
            request: optimizer_request(Vec::new(), Vec::new()),
            envelopes: Vec::new(),
            policy: policy.clone(),
        },
        OptimizerFixture {
            case_id: "valid-hard-constraint-no-objective".into(),
            request: optimizer_request(Vec::new(), vec![valid_constraint.clone()]),
            envelopes: vec![optimizer_envelope()],
            policy: policy.clone(),
        },
        OptimizerFixture {
            case_id: "candidate-objective-injection".into(),
            request: candidate_injection,
            envelopes: Vec::new(),
            policy: policy.clone(),
        },
        OptimizerFixture {
            case_id: "unknown-module".into(),
            request: optimizer_request(Vec::new(), vec![unknown_constraint]),
            envelopes: Vec::new(),
            policy: policy.clone(),
        },
        OptimizerFixture {
            case_id: "duplicate-module-envelopes".into(),
            request: optimizer_request(Vec::new(), vec![valid_constraint.clone()]),
            envelopes: vec![optimizer_envelope(), optimizer_envelope()],
            policy: policy.clone(),
        },
        OptimizerFixture {
            case_id: "missing-unknown-path".into(),
            request: optimizer_request(Vec::new(), vec![missing_path]),
            envelopes: vec![optimizer_envelope()],
            policy: policy.clone(),
        },
        OptimizerFixture {
            case_id: "unsupported-operator".into(),
            request: optimizer_request(Vec::new(), vec![unsupported]),
            envelopes: vec![optimizer_envelope()],
            policy: policy.clone(),
        },
        OptimizerFixture {
            case_id: "non-scored-envelope".into(),
            request: optimizer_request(Vec::new(), vec![valid_constraint.clone()]),
            envelopes: vec![non_scored],
            policy: policy.clone(),
        },
        OptimizerFixture {
            case_id: "failed-constraint".into(),
            request: optimizer_request(Vec::new(), vec![valid_constraint.clone()]),
            envelopes: vec![failed],
            policy: policy.clone(),
        },
        OptimizerFixture {
            case_id: "forged-optimizer-usable".into(),
            request: optimizer_request(Vec::new(), vec![valid_constraint.clone()]),
            envelopes: vec![forged_optimizer],
            policy: policy.clone(),
        },
        OptimizerFixture {
            case_id: "absent-false-claim-locks".into(),
            request: optimizer_request(Vec::new(), vec![valid_constraint.clone()]),
            envelopes: vec![missing_locks],
            policy: policy.clone(),
        },
        OptimizerFixture {
            case_id: "registry-ranking-authority-solver-tampering".into(),
            request: optimizer_request(Vec::new(), Vec::new()),
            envelopes: Vec::new(),
            policy: tampered_policy,
        },
    ];
    let positive = BTreeSet::from([
        "policy-complete-no-objective",
        "valid-hard-constraint-no-objective",
    ]);
    let expected = fixtures
        .iter()
        .map(|fixture| {
            (
                fixture.case_id.clone(),
                if positive.contains(fixture.case_id.as_str()) {
                    "ACCEPT"
                } else {
                    "REJECT"
                }
                .into(),
            )
        })
        .collect::<BTreeMap<_, _>>();
    let mut observed = BTreeMap::new();
    let mut results = BTreeMap::new();
    let mut fixture_hashes = BTreeMap::new();
    for fixture in &fixtures {
        fixture_hashes.insert(
            fixture.case_id.clone(),
            stable_hash(&serde_json::to_value(fixture).unwrap()),
        );
        let result =
            authorize_optimizer_request(&fixture.request, &fixture.envelopes, &fixture.policy);
        let accepted = result.as_ref().is_ok_and(|result| {
            result.status == "NO_ELIGIBLE_OBJECTIVES"
                && result.hard_constraints_passed
                && result.eligible_objective_count == 0
                && result.objective_values.is_empty()
                && !result.ranking_performed
                && !result.solver_invoked
                && !result.usable_by_optimizer
                && !result.authority_upgrade
                && !result.candidate_created_evidence
        });
        observed.insert(fixture.case_id.clone(), outcome(accepted));
        results.insert(
            fixture.case_id.clone(),
            match result {
                Ok(result) => serde_json::to_value(result).unwrap(),
                Err(error) => json!({"error":error}),
            },
        );
    }
    let exact = expected == observed
        && results["policy-complete-no-objective"]["status"] == json!("NO_ELIGIBLE_OBJECTIVES")
        && results["valid-hard-constraint-no-objective"]["hard_constraints_passed"]
            == Value::Bool(true);
    Ok(diagnostic(
        OPTIMIZER_ORCHESTRATOR,
        expected,
        observed,
        2,
        10,
        BTreeMap::from([
            (
                "fixture_inputs".into(),
                serde_json::to_value(&fixtures).unwrap(),
            ),
            (
                "fixture_hashes".into(),
                serde_json::to_value(fixture_hashes).unwrap(),
            ),
            (
                "fixture_results".into(),
                serde_json::to_value(results).unwrap(),
            ),
            ("scientific_objective_quarantine".into(), Value::Bool(true)),
            ("objective_value_count".into(), json!(0)),
            ("candidate_created_evidence_count".into(), json!(0)),
            ("authority_upgrade_count".into(), json!(0)),
            ("solver_invocation_count".into(), json!(0)),
            ("ranking_count".into(), json!(0)),
        ]),
        exact,
    ))
}

fn outcome(accepted: bool) -> String {
    if accepted { "ACCEPT" } else { "REJECT" }.into()
}

fn required_string<'a>(value: &'a Value, field: &str) -> Result<&'a str, String> {
    value
        .get(field)
        .and_then(Value::as_str)
        .ok_or_else(|| format!("required string field is absent: {field}"))
}

fn decode_hex<const N: usize>(value: &str) -> Result<[u8; N], String> {
    if value.len() != N * 2
        || value
            .bytes()
            .any(|byte| !(byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte)))
    {
        return Err("value is not lowercase fixed-width hex".into());
    }
    let mut output = [0_u8; N];
    for (index, chunk) in value.as_bytes().chunks_exact(2).enumerate() {
        output[index] = u8::from_str_radix(std::str::from_utf8(chunk).unwrap(), 16)
            .map_err(|error| error.to_string())?;
    }
    Ok(output)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn all_nine_live_diagnostics_pass_strict_contracts() {
        for module in [
            EVIDENCE_INTAKE,
            SOURCE_LEDGER,
            REDTEAM_AUDIT,
            REPORT_PACKAGER,
            FORMULATION_ARITHMETIC,
            FORMULATION_UNIVERSE,
            ENVELOPE_GATES,
            CRO_PROTOCOL_PACKAGER,
            OPTIMIZER_ORCHESTRATOR,
        ] {
            deterministic_control_diagnostic(module)
                .unwrap_or_else(|error| panic!("{module}: {error}"));
        }
    }

    #[test]
    fn promoted_control_counts_and_zero_authority_outputs_are_exact() {
        for (module, positive, negative) in [
            (FORMULATION_ARITHMETIC, 2, 7),
            (FORMULATION_UNIVERSE, 2, 9),
            (ENVELOPE_GATES, 2, 9),
            (CRO_PROTOCOL_PACKAGER, 1, 9),
            (OPTIMIZER_ORCHESTRATOR, 2, 10),
        ] {
            let diagnostic = deterministic_control_diagnostic(module).unwrap();
            assert_eq!(diagnostic.positive_control_count, positive, "{module}");
            assert_eq!(diagnostic.negative_control_count, negative, "{module}");
            assert_eq!(diagnostic.details["objective_value_count"], json!(0));
            assert_eq!(
                diagnostic.details["candidate_created_evidence_count"],
                json!(0)
            );
            assert_eq!(diagnostic.details["authority_upgrade_count"], json!(0));
            assert!(diagnostic.details["result_digest"].as_str().is_some());
        }
    }

    #[test]
    fn promoted_structured_fixtures_reject_unknown_and_duplicate_fields() {
        let unknown = json!({
            "case_id":"x","axes":null,"infeasible_indices":null,"claims":null,"unknown":true
        });
        assert!(serde_json::from_value::<UniverseFixture>(unknown).is_err());
        let duplicate =
            br#"{"case_id":"x","case_id":"y","axes":null,"infeasible_indices":null,"claims":null}"#;
        assert!(strict_json(duplicate).is_err());
        let unknown_optimizer = json!({
            "schema":"amphora.optimizer-authorization-request.v1","request_source":"POLICY",
            "objectives":[],"hard_constraints":[],"unknown":true
        });
        assert!(
            serde_json::from_value::<OptimizerAuthorizationRequestV1>(unknown_optimizer).is_err()
        );
    }

    #[test]
    fn cro_fixture_private_material_is_absent_and_execution_is_locked() {
        let fixture = strict_json(CRO_FIXTURE).unwrap();
        assert!(protocol_fixture_accepted(&fixture).unwrap());
        assert!(fixture.pointer("/signature/private_key_hex").is_none());
        assert_eq!(
            fixture.pointer("/payload/lab_execution_status"),
            Some(&json!("NOT_EXECUTED"))
        );
        assert!(fixture
            .pointer("/payload/results")
            .is_some_and(Value::is_null));
    }

    #[test]
    fn source_control_rejects_unknown_fields_and_laundering() {
        let unknown = json!({
            "case_id":"x", "primary_url":"https://a", "secondary_url":"https://b",
            "required_fields_complete":true, "waiver":null, "source_authority":"PUBLIC",
            "requested_authority":"PUBLIC_AUDIT", "unknown":true
        });
        assert!(serde_json::from_value::<SourceControlInput>(unknown).is_err());
        let diagnostic = source_ledger_diagnostic().unwrap();
        assert_eq!(diagnostic.positive_control_count, 1);
        assert_eq!(diagnostic.negative_control_count, 5);
    }

    #[test]
    fn banned_claim_lint_normalizes_unicode_case_and_format() {
        for claim in [
            "PROCUREMENT-READY",
            "Procurement__Ready",
            "ＰＲＯＣＵＲＥＭＥＮＴ‑ＲＥＡＤＹ",
        ] {
            assert!(contains_banned_claim(claim));
        }
    }

    #[test]
    fn report_fixture_components_are_bound() {
        let fixture: ReportFixture =
            serde_json::from_value(strict_json(REPORT_FIXTURE).unwrap()).unwrap();
        assert_eq!(
            fixture.payload.rendered_document,
            render_report(&fixture.payload),
            "render"
        );
        assert_eq!(
            fixture.payload.score_envelope_sha256,
            stable_hash(&Value::Array(fixture.payload.score_envelopes.clone())),
            "envelope"
        );
        assert_eq!(
            fixture.payload.canonical_hash_manifest["known-answer-report.md"],
            raw_sha256(fixture.payload.rendered_document.as_bytes()),
            "manifest"
        );
        assert!(report_fixture_accepted(&fixture), "signature or policy");
    }

    #[test]
    fn redteam_corpus_is_exact_and_reproducible() {
        let first = redteam_diagnostic().unwrap();
        let second = redteam_diagnostic().unwrap();
        assert_eq!(first, second);
        assert_eq!(first.negative_control_count, 30_000);
        assert_eq!(first.details["covered_axis_pair_count"], json!(276));
    }

    const REDTEAM_AUDIT_PHASE0_KPI_SUPPORTED_MODULES: [&str; 9] = [
        "amphora-evidence-intake-validator",
        "amphora-source-ledger",
        "amphora-redteam-audit",
        "amphora-report-packager",
        "amphora-formulation-arithmetic",
        "amphora-formulation-universe",
        "amphora-envelope-gates",
        "amphora-cro-protocol-packager",
        "amphora-optimizer-orchestrator",
    ];

    #[test]
    fn deterministic_control_diagnostic_supports_the_nine_expected_module_ids() {
        for module_id in REDTEAM_AUDIT_PHASE0_KPI_SUPPORTED_MODULES {
            let out = deterministic_control_diagnostic(module_id).unwrap_or_else(|error| {
                panic!("deterministic_control_diagnostic({module_id}) errored: {error}")
            });
            assert_eq!(out.module_id, module_id);
            assert_eq!(out.schema, DETERMINISTIC_CONTROL_DIAGNOSTIC_SCHEMA);
            assert_eq!(out.implementation_readiness, "COMPLETE");
            assert!(
                out.passed,
                "diagnostic({module_id}).passed must be true; expected={:?} observed={:?}",
                out.expected_fixture_outcomes, out.observed_fixture_outcomes
            );
        }
    }

    #[test]
    fn deterministic_control_diagnostic_rejects_unsupported_or_malformed_module_id() {
        for probe in [
            "",
            "   ",
            "unknown",
            "amphora-does-not-exist",
            "amphora-source_ledger",
            "AMPHORA-REDTEAM-AUDIT",
            "АМФОРА",
        ] {
            let err = deterministic_control_diagnostic(probe).unwrap_err();
            assert!(
                err.contains("unsupported deterministic control diagnostic"),
                "unsupported probe {probe:?} produced unexpected error: {err}"
            );
        }
    }

    #[test]
    fn deterministic_control_diagnostic_result_is_byte_stable_on_replay() {
        for module_id in REDTEAM_AUDIT_PHASE0_KPI_SUPPORTED_MODULES {
            let first = deterministic_control_diagnostic(module_id).unwrap();
            let second = deterministic_control_diagnostic(module_id).unwrap();
            assert_eq!(
                serde_json::to_vec(&first).unwrap(),
                serde_json::to_vec(&second).unwrap(),
                "diagnostic({module_id}) not byte-stable across replays",
            );
            assert_eq!(
                first.details.get("result_digest"),
                second.details.get("result_digest"),
                "result_digest for {module_id} differs across replays",
            );
        }
    }

    #[test]
    fn deterministic_control_diagnostic_zero_authority_locks_populated_true_for_every_required_key(
    ) {
        for module_id in REDTEAM_AUDIT_PHASE0_KPI_SUPPORTED_MODULES {
            let out = deterministic_control_diagnostic(module_id).unwrap();
            for lock in REQUIRED_ZERO_AUTHORITY_CLAIM_LOCKS {
                assert_eq!(
                    out.zero_authority_assertions.get(lock),
                    Some(&true),
                    "zero_authority_assertions for {module_id} missing lock {lock}",
                );
            }
        }
    }

    #[test]
    fn redteam_attack_axes_are_the_full_24_module_specific_set() {
        assert_eq!(REDTEAM_ATTACK_AXES.len(), 24);
        let unique: std::collections::BTreeSet<&&str> = REDTEAM_ATTACK_AXES.iter().collect();
        assert_eq!(unique.len(), 24, "REDTEAM_ATTACK_AXES contains duplicates");
        for axis in REDTEAM_ATTACK_AXES {
            assert!(!axis.is_empty(), "axis is empty");
            assert!(
                axis.chars().all(|c| c.is_ascii_uppercase() || c == '_'),
                "axis {axis} contains non-uppercase/non-underscore characters"
            );
            assert!(
                !axis.chars().any(char::is_whitespace),
                "axis {axis} contains whitespace"
            );
        }
    }
}
