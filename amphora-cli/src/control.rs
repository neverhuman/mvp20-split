use amphora_core::{
    canonicalize, prove_read_only, stable_hash, BenchmarkLockV1, ConfidenceIntervalV1,
    DatasetManifestV1, DecisionUse, EvaluationReceiptV1, EvidenceTier, HostileNullAblationV1,
    IpDispositionV1, IpRecommendationV1, MethodRegistryV1, RightsRecordV1, SignedModelArtifactV1,
    SplitManifestV1, TechnicalIpDossierV1, TrustStore, DATASET_MANIFEST_SCHEMA,
    EVALUATION_RECEIPT_SCHEMA, METHOD_REGISTRY_SCHEMA, SIGNED_MODEL_ARTIFACT_SCHEMA,
    TECHNICAL_IP_DOSSIER_SCHEMA,
};
use amphora_cure_potlife_gate::{
    contract_hash as pot_life_contract_hash, evaluate_locked_benchmark, generate_protocol,
    lock_benchmark as lock_pot_life_benchmark, preflight_contract, seal_expert_packet,
    ExpertPacketV1, IndependentReviewV1, PotLifeBenchmarkLockV1, PotLifeContractKind,
    PotLifeProtocolV1, PotLifeRunV1, PotLifeScaleQualificationV1,
};
use amphora_engine::EnginePool;
use amphora_formulation_capabilities::process_qc_audit_shell;
use anyhow::{anyhow, bail, Context, Result};
use clap::{Args, Subcommand, ValueEnum};
use ed25519_dalek::SigningKey;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};
use std::fs::{self, OpenOptions};
use std::io::{Read, Write};
use std::path::{Component, Path, PathBuf};
use std::process::Command;
use std::time::{SystemTime, UNIX_EPOCH};

mod data_v2;

const BENCHMARK_LOCK_PATH: &str = "config/benchmark-lock.v1.json";
const INVENTORY_PATH: &str = "config/module-evidence-inventory.json";
const REGISTRY_PATH: &str = "module-manifest.json";
const DATA_SOURCES_PATH: &str = "feedback/v1/dataset_sources.json";
const ACQUISITION_REPORT_PATH: &str = "feedback/v1/acquisition_report.json";
const DERIVED_MANIFEST_PATH: &str = "feedback/v1/derived/build_manifest.json";
const CORROSION_MODULE: &str = "amphora-public-corrosion-benchmark";
const CURE_MODULE: &str = "amphora-cure-potlife-gate";
const VISCOSITY_MODULE: &str = "amphora-viscosity-score";
const SOLVENCY_MODULE: &str = "amphora-solvency-score";
const EIS_CORROSION_MODULE: &str = "amphora-barrier-corrosion-score";
const MOLECULE_PROPERTY_MODULE: &str = "amphora-molecule-property";
const MOLECULE_ROLE_MODULE: &str = "amphora-molecule-role-ranker";
const DESIGN_RULE_MODULE: &str = "amphora-design-rule-score";
const CORROSION_SOURCES_PATH: &str = "config/program/corrosion-sources.v1.json";
const CURE_SOURCES_PATH: &str = "config/program/cure-sources.v1.json";
const CORROSION_SPLIT_PATH: &str = "config/program/corrosion-split.v1.json";
const CURE_SPLIT_PATH: &str = "config/program/cure-split.v1.json";
const VISCOSITY_SOURCES_PATH: &str = "config/program/viscosity-sources.v1.json";
const SOLVENCY_SOURCES_PATH: &str = "config/program/solvency-sources.v1.json";
const EIS_CORROSION_SOURCES_PATH: &str = "config/program/eis-corrosion-sources.v1.json";
const VISCOSITY_SPLIT_PATH: &str = "config/program/viscosity-split.v1.json";
const SOLVENCY_SPLIT_PATH: &str = "config/program/solvency-model-split.v1.json";
const EIS_CORROSION_SPLIT_PATH: &str = "config/program/eis-corrosion-split.v1.json";
const MOLECULE_PROPERTY_SOURCES_PATH: &str = "config/program/molecule-property-sources.v1.json";
const MOLECULE_ROLE_SOURCES_PATH: &str = "config/program/molecule-role-sources.v1.json";
const DESIGN_RULE_SOURCES_PATH: &str = "config/program/design-rule-sources.v1.json";
const MOLECULE_PROPERTY_SPLIT_PATH: &str = "config/program/molecule-property-split.v1.json";
const MOLECULE_ROLE_SPLIT_PATH: &str = "config/program/molecule-role-split.v1.json";
const MOLECULE_PROPERTY_BENCHMARK_PATH: &str =
    "amphora-molecule-property/reference/mvp20/data/eew_ahew_benchmark.v1.json";
const MOLECULE_ROLE_BENCHMARK_PATH: &str =
    "amphora-molecule-role-ranker/reference/mvp20/data/role_fit_benchmark.v1.json";
const CORROSION_LIFT_PATH: &str =
    "amphora-public-corrosion-benchmark/reference/mvp20/out/v5_epoch30_lift_audit.json";
const CURE_LIFT_PATH: &str =
    "amphora-cure-potlife-gate/reference/mvp20/out/v5_epoch30_lift_audit.json";
const IP_LANDSCAPE_PATH: &str = "amphora-ip-fto-guard/reference/mvp20/data/patent_landscape.json";
const IP_SEARCH_REFRESH_PATH: &str = "config/program/ip-search-refresh.v1.json";
const METHOD_REGISTRY_PATH: &str = "config/program/epoxy-amine-method-registry.v1.json";

const COMPUTATIONAL_MODULES: [&str; 12] = [
    "amphora-candidate-contract",
    "amphora-model-card-authority",
    "amphora-optimizer-orchestrator",
    "amphora-evidence-intake-validator",
    "amphora-run-provenance",
    "amphora-report-packager",
    "amphora-redteam-audit",
    "amphora-known-answer-benchmarks",
    "amphora-formulation-arithmetic",
    "amphora-envelope-gates",
    "amphora-formulation-universe",
    "amphora-cro-protocol-packager",
];

const LIVE_DETERMINISTIC_CONTROLS: [&str; 9] = [
    "amphora-cro-protocol-packager",
    "amphora-envelope-gates",
    "amphora-evidence-intake-validator",
    "amphora-formulation-arithmetic",
    "amphora-formulation-universe",
    "amphora-optimizer-orchestrator",
    "amphora-source-ledger",
    "amphora-redteam-audit",
    "amphora-report-packager",
];

#[derive(Debug, Args)]
pub struct DataArgs {
    #[command(subcommand)]
    pub command: DataCommand,
}

#[derive(Debug, Subcommand)]
pub enum DataCommand {
    Fetch {
        #[arg(long)]
        module: String,
        #[arg(long)]
        source: String,
    },
    Acquire {
        #[arg(long)]
        all: bool,
        #[arg(long)]
        module: Option<String>,
        #[arg(long, default_value = "feedback/v2")]
        snapshot: PathBuf,
        #[arg(long)]
        unit: Option<String>,
        #[arg(long, requires = "unit")]
        import: Option<PathBuf>,
    },
    Normalize {
        #[arg(long)]
        all: bool,
        #[arg(long, default_value = "feedback/v2")]
        snapshot: PathBuf,
        #[arg(long)]
        unit: Option<String>,
    },
    Audit {
        #[arg(long, default_value = "feedback/v2")]
        snapshot: PathBuf,
        #[arg(long, conflicts_with = "write_reports")]
        check: bool,
        #[arg(long, conflicts_with = "check")]
        write_reports: bool,
    },
    Consume {
        #[arg(long, default_value = "feedback/v2")]
        snapshot: PathBuf,
        #[arg(long)]
        module: Option<String>,
        #[arg(long)]
        dataset: Option<String>,
        #[arg(long)]
        all: bool,
        #[arg(long)]
        all_modules: bool,
    },
    Build {
        #[arg(long)]
        all: bool,
        #[arg(long)]
        module: Option<String>,
    },
    Verify {
        #[arg(long)]
        all: bool,
        #[arg(long)]
        module: Option<String>,
    },
    Rights {
        #[command(subcommand)]
        command: DataRightsCommand,
    },
    MethodRegistry {
        #[command(subcommand)]
        command: DataMethodRegistryCommand,
    },
}

#[derive(Debug, Subcommand)]
pub enum DataRightsCommand {
    Request {
        #[arg(long, default_value = "feedback/v2")]
        snapshot: PathBuf,
        #[arg(long)]
        module: String,
        #[arg(long)]
        dataset: String,
        #[arg(long)]
        output: PathBuf,
    },
    Sign {
        #[arg(long)]
        request: PathBuf,
        #[arg(long)]
        private_key: PathBuf,
        #[arg(long)]
        output: PathBuf,
    },
    Import {
        #[arg(long, default_value = "feedback/v2")]
        snapshot: PathBuf,
        #[arg(long)]
        module: String,
        #[arg(long)]
        receipt: PathBuf,
    },
    Verify {
        #[arg(long, default_value = "feedback/v2")]
        snapshot: PathBuf,
        #[arg(long)]
        all: bool,
        #[arg(long)]
        module: Option<String>,
    },
}

#[derive(Debug, Subcommand)]
pub enum DataMethodRegistryCommand {
    Verify {
        #[arg(long)]
        all_modules: bool,
    },
}

#[derive(Debug, Args)]
pub struct BenchmarkArgs {
    #[command(subcommand)]
    pub command: BenchmarkCommand,
}

#[derive(Debug, Subcommand)]
pub enum BenchmarkCommand {
    Lock {
        #[arg(long)]
        output: Option<PathBuf>,
        #[arg(long)]
        module: Option<String>,
    },
    Run {
        #[arg(long)]
        locked: bool,
        #[arg(long)]
        all: bool,
        #[arg(long)]
        module: Option<String>,
    },
    Compare {
        #[arg(long)]
        left: PathBuf,
        #[arg(long)]
        right: PathBuf,
    },
    Replay {
        #[arg(long)]
        module: String,
    },
}

#[derive(Debug, Args)]
pub struct PortfolioArgs {
    #[command(subcommand)]
    pub command: PortfolioCommand,
}

#[derive(Debug, Subcommand)]
pub enum PortfolioCommand {
    Phase0(crate::phase0::Phase0Args),
    Phase1(crate::phase1::Phase1Args),
    Status {
        #[arg(long)]
        verify_receipts: bool,
    },
    FounderUpdate {
        #[arg(long)]
        modules: String,
        #[arg(long)]
        verify_receipts: bool,
        #[arg(long, value_enum, default_value_t = ReportFormat::Markdown)]
        format: ReportFormat,
    },
    IpDossier {
        #[arg(long, default_value = "corrosion,cure")]
        modules: String,
    },
}

#[derive(Debug, Clone, Copy, ValueEnum)]
pub enum ReportFormat {
    Markdown,
    Json,
}

#[derive(Debug, Args)]
pub struct ShadowArgs {
    #[command(subcommand)]
    pub command: ShadowCommand,
}

#[derive(Debug, Subcommand)]
pub enum ShadowCommand {
    Run(ShadowRunArgs),
}

#[derive(Debug, Args)]
pub struct ShadowRunArgs {
    #[arg(long)]
    pub candidate: Option<PathBuf>,
    #[arg(long, default_value_t = 2)]
    pub workers: usize,
    #[arg(long, default_value_t = 42)]
    pub seed: u64,
}

#[derive(Debug, Args)]
pub struct PotLifeArgs {
    #[command(subcommand)]
    pub command: PotLifeCommand,
}

#[derive(Debug, Args)]
pub struct ModelArgs {
    #[command(subcommand)]
    pub command: ModelCommand,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, ValueEnum)]
pub enum ModelPreflightKind {
    Observation,
    Dataset,
    Split,
    BenchmarkLock,
    ParameterArtifact,
    ModelArtifact,
    Prediction,
    IndependentReview,
}

impl ModelPreflightKind {
    fn label(self) -> &'static str {
        match self {
            Self::Observation => "observation",
            Self::Dataset => "dataset",
            Self::Split => "split",
            Self::BenchmarkLock => "benchmark-lock",
            Self::ParameterArtifact => "parameter-artifact",
            Self::ModelArtifact => "model-artifact",
            Self::Prediction => "prediction",
            Self::IndependentReview => "independent-review",
        }
    }
}

#[derive(Debug, Subcommand)]
pub enum ModelCommand {
    Preflight {
        #[arg(long)]
        module: String,
        #[arg(long, value_enum)]
        kind: ModelPreflightKind,
        #[arg(long)]
        input: PathBuf,
        #[arg(long)]
        raw_base_dir: Option<PathBuf>,
    },
    Fit {
        #[arg(long)]
        module: String,
        #[arg(long)]
        dataset: PathBuf,
        #[arg(long)]
        split: PathBuf,
        #[arg(long)]
        lock: PathBuf,
        #[arg(long)]
        output: PathBuf,
    },
}

#[derive(Debug, Clone, Copy, ValueEnum)]
pub enum PotLifePreflightKind {
    ScaleQualification,
    Run,
    Protocol,
    BenchmarkLock,
    ModelArtifact,
    Prediction,
    IndependentReview,
    ExpertPacket,
}

impl From<PotLifePreflightKind> for PotLifeContractKind {
    fn from(value: PotLifePreflightKind) -> Self {
        match value {
            PotLifePreflightKind::ScaleQualification => Self::ScaleQualification,
            PotLifePreflightKind::Run => Self::Run,
            PotLifePreflightKind::Protocol => Self::Protocol,
            PotLifePreflightKind::BenchmarkLock => Self::BenchmarkLock,
            PotLifePreflightKind::ModelArtifact => Self::ModelArtifact,
            PotLifePreflightKind::Prediction => Self::Prediction,
            PotLifePreflightKind::IndependentReview => Self::IndependentReview,
            PotLifePreflightKind::ExpertPacket => Self::ExpertPacket,
        }
    }
}

#[derive(Debug, Subcommand)]
pub enum PotLifeCommand {
    Preflight {
        #[arg(long, value_enum)]
        kind: PotLifePreflightKind,
        #[arg(long)]
        input: PathBuf,
        #[arg(long)]
        raw_base_dir: Option<PathBuf>,
    },
    Protocol {
        #[arg(long)]
        qualification: PathBuf,
        #[arg(long)]
        source_ledger: PathBuf,
        #[arg(long)]
        generated_on: String,
        #[arg(long)]
        mixing_method: String,
        #[arg(long)]
        output: Option<PathBuf>,
    },
    Ingest {
        #[arg(long)]
        run: PathBuf,
        #[arg(long)]
        output: Option<PathBuf>,
    },
    Lock {
        #[arg(long)]
        protocol: PathBuf,
        #[arg(long)]
        runs_dir: PathBuf,
        #[arg(long)]
        output: Option<PathBuf>,
    },
    Evaluate {
        #[arg(long)]
        lock: PathBuf,
        #[arg(long)]
        runs_dir: PathBuf,
        #[arg(long)]
        source_ledger: PathBuf,
        #[arg(long)]
        prior_art_chart: PathBuf,
        #[arg(long)]
        independent_review: Option<PathBuf>,
        #[arg(long, requires = "independent_review")]
        reviewed_packet: Option<PathBuf>,
        #[arg(long)]
        output: Option<PathBuf>,
        #[arg(long)]
        expert_packet_output: Option<PathBuf>,
        #[arg(long, default_value_t = 2)]
        workers: usize,
    },
}

#[derive(Debug, Serialize, PartialEq, Eq)]
struct PotLifePreflightReport {
    schema: &'static str,
    status: &'static str,
    kind: &'static str,
    input_path: String,
    input_sha256: String,
    contract_schema: String,
    track_id: Option<String>,
    contract_id: String,
    raw_files_verified: usize,
    signed: bool,
    artifacts_written: bool,
    identities_written: bool,
    receipts_written: bool,
}

#[derive(Debug, Serialize, PartialEq, Eq)]
struct ModelPreflightReport {
    schema: &'static str,
    status: &'static str,
    module_id: String,
    kind: &'static str,
    input_path: String,
    input_sha256: String,
    contract_schema: String,
    contract_id: String,
    raw_files_verified: usize,
    signed_input: bool,
    artifacts_written: bool,
    identities_written: bool,
    receipts_written: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct SourceGenesisV1 {
    schema: String,
    files: BTreeMap<String, String>,
    root_hash: String,
}

struct LocalIdentity {
    signing_key: SigningKey,
    key_id: String,
    genesis_hash: String,
}

#[derive(Debug)]
struct DataAudit {
    artifact_hashes: BTreeMap<String, String>,
    verified_files: usize,
    missing_files: usize,
    mismatched_files: usize,
    eligible_sources: usize,
    quarantined_sources: usize,
    rights: Vec<RightsRecordV1>,
    row_count: u64,
    metadata_binding_valid: bool,
}

pub fn run_data(root: &Path, args: DataArgs) -> Result<()> {
    match args.command {
        DataCommand::Fetch { module, source } => run_module_fetch(root, &module, &source),
        DataCommand::Acquire {
            all,
            module,
            snapshot,
            unit,
            import,
        } => {
            if let Some(module) = module {
                if unit.is_some() || import.is_some() || snapshot != Path::new("feedback/v2") {
                    bail!("--module is the legacy module acquisition flow and cannot be combined with v2 snapshot options");
                }
                return run_module_data(root, &module, ModuleDataAction::Acquire);
            }
            data_v2::acquire(root, &snapshot, all, unit.as_deref(), import.as_deref())
        }
        DataCommand::Normalize {
            all,
            snapshot,
            unit,
        } => data_v2::normalize(root, &snapshot, all, unit.as_deref()),
        DataCommand::Audit {
            snapshot,
            check,
            write_reports,
        } => {
            if check == write_reports {
                bail!("select exactly one of --check or --write-reports");
            }
            if check {
                prove_read_only(root, || data_v2::audit(root, &snapshot, false))
            } else {
                data_v2::audit(root, &snapshot, write_reports)
            }
        }
        DataCommand::Consume {
            snapshot,
            module,
            dataset,
            all,
            all_modules,
        } => data_v2::consume(
            root,
            &snapshot,
            module.as_deref(),
            dataset.as_deref(),
            all,
            all_modules,
        ),
        DataCommand::Verify { all, module } => {
            if let Some(module) = module {
                return run_module_data(root, &module, ModuleDataAction::Verify);
            }
            require_all(all)?;
            let audit = audit_data(root)?;
            let raw_integrity = audit.missing_files == 0 && audit.mismatched_files == 0;
            let passed = raw_integrity && audit.metadata_binding_valid;
            let receipt = control_receipt(
                root,
                "amphora-source-ledger",
                "data verify --all",
                passed,
                EvidenceTier::PublicRetrospective,
                DecisionUse::AuditOnly,
                audit.artifact_hashes,
                json!({
                    "verified_files": audit.verified_files,
                    "missing_files": audit.missing_files,
                    "mismatched_files": audit.mismatched_files,
                    "eligible_sources": audit.eligible_sources,
                    "quarantined_sources": audit.quarantined_sources,
                    "quarantined_sources_excluded_from_derivatives": true,
                    "reported_row_count": audit.row_count,
                    "metadata_binding_valid": audit.metadata_binding_valid,
                    "stale_metadata_is_quarantined": !audit.metadata_binding_valid,
                }),
            )?;
            emit_jsonl(&serde_json::to_value(receipt)?)?;
            if raw_integrity {
                Ok(())
            } else {
                bail!("data integrity verification failed")
            }
        }
        DataCommand::Rights { command } => match command {
            DataRightsCommand::Request {
                snapshot,
                module,
                dataset,
                output,
            } => data_v2::request_rights_review(root, &snapshot, &module, &dataset, &output),
            DataRightsCommand::Sign {
                request,
                private_key,
                output,
            } => data_v2::sign_rights_review(root, &request, &private_key, &output),
            DataRightsCommand::Import {
                snapshot,
                module,
                receipt,
            } => data_v2::import_rights_review(root, &snapshot, &module, &receipt),
            DataRightsCommand::Verify {
                snapshot,
                all,
                module,
            } => data_v2::verify_rights(root, &snapshot, all, module.as_deref()),
        },
        DataCommand::MethodRegistry { command } => match command {
            DataMethodRegistryCommand::Verify { all_modules } => {
                prove_read_only(root, || verify_method_registry(root, all_modules))
            }
        },
        DataCommand::Build { all, module } => {
            if let Some(module) = module {
                return run_module_data(root, &module, ModuleDataAction::Build);
            }
            require_all(all)?;
            let audit = audit_data(root)?;
            if audit.missing_files != 0
                || audit.mismatched_files != 0
                || !audit.metadata_binding_valid
            {
                bail!("cannot build from missing, mismatched, or stale-bound raw artifacts");
            }
            let identity = ensure_local_identity(root)?;
            let executable = std::env::current_exe().context("resolving data builder")?;
            let raw_set_hash = stable_hash(&serde_json::to_value(&audit.artifact_hashes)?);
            let dataset_id = format!("feedback-v1-rights-cleared-{}", &raw_set_hash[..16]);
            let manifest = DatasetManifestV1 {
                schema: DATASET_MANIFEST_SCHEMA.into(),
                dataset_id: dataset_id.clone(),
                raw_hashes: audit.artifact_hashes.clone(),
                rights: audit.rights,
                row_provenance: Vec::new(),
                units: BTreeMap::new(),
                methods: vec![
                    "raw-byte SHA-256 verification".into(),
                    "conservative license allow-list".into(),
                    "quarantined-source exclusion".into(),
                ],
                conditions: BTreeMap::from([
                    ("evidence_tier".into(), "PUBLIC_RETROSPECTIVE".into()),
                    ("decision_use".into(), "SHADOW_MAXIMUM".into()),
                ]),
                builder_hash: raw_file_sha256(&executable)?,
                schema_hash: stable_hash(&Value::String(DATASET_MANIFEST_SCHEMA.into())),
                row_count: audit.row_count,
            };
            manifest.validate()?;
            let path = root
                .join(".amphora/data")
                .join(format!("{dataset_id}.json"));
            persist_immutable(&path, &canonical_bytes(&serde_json::to_value(&manifest)?)?)?;
            let mut hashes = audit.artifact_hashes;
            hashes.insert(relative_display(root, &path), raw_file_sha256(&path)?);
            let receipt = signed_receipt(
                root,
                &identity,
                "amphora-source-ledger",
                "data build --all",
                true,
                EvidenceTier::PublicRetrospective,
                DecisionUse::Shadow,
                hashes,
                json!({
                    "dataset_id": dataset_id,
                    "dataset_manifest": relative_display(root, &path),
                    "row_count": manifest.row_count,
                    "rights_records": manifest.rights.len(),
                }),
            )?;
            emit_jsonl(&serde_json::to_value(receipt)?)
        }
    }
}

fn verify_method_registry(root: &Path, all_modules: bool) -> Result<()> {
    if !all_modules {
        bail!("method-registry verification requires --all-modules");
    }
    let path = root.join(METHOD_REGISTRY_PATH);
    let registry = read_json(&path)?;
    if registry.get("schema").and_then(Value::as_str) != Some(METHOD_REGISTRY_SCHEMA) {
        bail!("method registry schema mismatch");
    }
    let registry: MethodRegistryV1 = serde_json::from_value(registry)?;
    registry.validate()?;
    registry.verify_files(root)?;

    let module_manifest = read_json(&root.join(REGISTRY_PATH))?;
    let module_ids: BTreeSet<_> = module_manifest
        .get("modules")
        .and_then(Value::as_array)
        .ok_or_else(|| anyhow!("module manifest is malformed"))?
        .iter()
        .filter_map(|row| {
            row.get("project")
                .and_then(Value::as_str)
                .map(str::to_owned)
        })
        .collect();
    let registry_modules: BTreeSet<_> = registry.all_modules.iter().cloned().collect();
    if registry_modules != module_ids {
        bail!("method registry does not match native module manifest");
    }
    for module in &registry.all_modules {
        let card = registry
            .modules
            .get(module)
            .ok_or_else(|| anyhow!("method registry is missing module card for {module}"))?;
        if card.method_status.trim().is_empty()
            || card.method_version.trim().is_empty()
            || card.source_identity.trim().is_empty()
            || card.applicability_boundary.trim().is_empty()
        {
            bail!("method registry card for {module} has empty fields");
        }
        if !registry.all_modules.contains(&card.module_id) {
            bail!(
                "method registry card module id {} is not declared",
                card.module_id
            );
        }
    }

    emit_jsonl(&json!({
        "schema": METHOD_REGISTRY_SCHEMA,
        "registry_path": METHOD_REGISTRY_PATH,
        "registry_snapshot": registry.snapshot_id,
        "module_count": registry.all_modules.len(),
        "decision_scope": "compound-campaign-methods",
        "registry_file_sha256": raw_file_sha256(&path)?,
        "registry_jcs_sha256": registry.registry_hash,
        "verified": true,
        "read_only": true,
    }))
}

pub fn run_benchmark(root: &Path, args: BenchmarkArgs) -> Result<()> {
    match args.command {
        BenchmarkCommand::Lock { output, module } => {
            if let Some(module) = module {
                return lock_module_benchmark(root, &module, output.as_deref());
            }
            let (lock, bytes, path) = read_benchmark_lock(root)?;
            lock.validate()?;
            verify_lock_parents(root, &lock)?;
            if let Some(output) = output {
                let output = if output.is_absolute() {
                    output
                } else {
                    root.join(output)
                };
                persist_immutable(&output, &bytes)?;
            }
            let receipt = control_receipt(
                root,
                "amphora-model-card-authority",
                "benchmark lock",
                true,
                EvidenceTier::SyntheticDiagnostic,
                DecisionUse::ConstraintOnly,
                BTreeMap::from([(path, raw_sha256(&bytes))]),
                json!({"benchmark_id": lock.benchmark_id, "lock_valid": true}),
            )?;
            emit_jsonl(&serde_json::to_value(receipt)?)
        }
        BenchmarkCommand::Run {
            locked,
            all,
            module,
        } => {
            if !locked {
                bail!("benchmark run requires --locked");
            }
            if let Some(module) = module {
                return run_locked_module_benchmark(root, &module);
            }
            if !all {
                bail!("portfolio benchmark run requires --locked --all");
            }
            run_locked_benchmarks(root)
        }
        BenchmarkCommand::Compare { left, right } => compare_benchmarks(root, &left, &right),
        BenchmarkCommand::Replay { module } => {
            emit_jsonl(&replay_module_benchmark_receipt(root, &module)?)
        }
    }
}

pub fn run_portfolio(root: &Path, args: PortfolioArgs) -> Result<()> {
    match args.command {
        PortfolioCommand::Phase0(args) => crate::phase0::run(root, args),
        PortfolioCommand::Phase1(args) => crate::phase1::run(root, args),
        PortfolioCommand::Status { verify_receipts } => {
            prove_read_only(root, || portfolio_status(root, verify_receipts))
        }
        PortfolioCommand::FounderUpdate {
            modules,
            verify_receipts,
            format,
        } => founder_update(root, &modules, verify_receipts, format),
        PortfolioCommand::IpDossier { modules } => {
            let dossier = build_ip_dossier(root, &parse_module_list(&modules)?)?;
            persist_ip_dossier(root, &dossier)?;
            emit_jsonl(&serde_json::to_value(dossier)?)
        }
    }
}

pub fn run_shadow(root: &Path, args: ShadowArgs) -> Result<()> {
    match args.command {
        ShadowCommand::Run(args) => shadow_run(root, args),
    }
}

pub fn run_model(root: &Path, args: ModelArgs) -> Result<()> {
    match args.command {
        ModelCommand::Preflight {
            module,
            kind,
            input,
            raw_base_dir,
        } => {
            let report = preflight_model(&module, kind, &input, raw_base_dir.as_deref())?;
            emit_jsonl(&serde_json::to_value(report)?)
        }
        ModelCommand::Fit {
            module,
            dataset,
            split,
            lock,
            output,
        } => fit_model_artifact(root, &module, &dataset, &split, &lock, &output),
    }
}

fn preflight_model(
    module: &str,
    kind: ModelPreflightKind,
    input: &Path,
    raw_base_dir: Option<&Path>,
) -> Result<ModelPreflightReport> {
    require_scientific_model_module(module)?;
    let input_bytes = fs::read(input).with_context(|| format!("reading {}", input.display()))?;
    let mut value = amphora_core::parse_json_strict(&input_bytes)?;
    let mut signed_input = false;
    if kind == ModelPreflightKind::ModelArtifact
        && value.get("schema").and_then(Value::as_str) == Some(SIGNED_MODEL_ARTIFACT_SCHEMA)
    {
        let signed: SignedModelArtifactV1 = serde_json::from_value(value)?;
        signed.validate()?;
        if signed.module_id != module || signed.signature.is_none() {
            bail!("signed model artifact module identity or signature is absent");
        }
        value = signed.artifact;
        signed_input = true;
    }
    let (contract_schema, contract_id) = preflight_model_value(module, kind, value.clone())?;
    let raw_files_verified = if let Some(base) = raw_base_dir {
        verify_nested_raw_file_hashes(&value, base)?
    } else {
        0
    };
    Ok(ModelPreflightReport {
        schema: "amphora.model-preflight-report.v1",
        status: "VALID",
        module_id: module.into(),
        kind: kind.label(),
        input_path: input.display().to_string(),
        input_sha256: raw_sha256(&input_bytes),
        contract_schema,
        contract_id,
        raw_files_verified,
        signed_input,
        artifacts_written: false,
        identities_written: false,
        receipts_written: false,
    })
}

fn preflight_model_value(
    module: &str,
    kind: ModelPreflightKind,
    value: Value,
) -> Result<(String, String)> {
    match module {
        VISCOSITY_MODULE => {
            use amphora_viscosity_score::ContractKind as Kind;
            let kind = match kind {
                ModelPreflightKind::Observation => Kind::Observation,
                ModelPreflightKind::Dataset => Kind::Dataset,
                ModelPreflightKind::Split => Kind::Split,
                ModelPreflightKind::BenchmarkLock => Kind::BenchmarkLock,
                ModelPreflightKind::ModelArtifact => Kind::ModelArtifact,
                ModelPreflightKind::Prediction => Kind::Prediction,
                ModelPreflightKind::IndependentReview => Kind::IndependentReview,
                ModelPreflightKind::ParameterArtifact => {
                    bail!("parameter-artifact is not a viscosity contract")
                }
            };
            amphora_viscosity_score::preflight(kind, value).map_err(Into::into)
        }
        SOLVENCY_MODULE => {
            use amphora_solvency_score::ContractKind as Kind;
            let kind = match kind {
                ModelPreflightKind::Observation => Kind::Observation,
                ModelPreflightKind::Dataset => Kind::Dataset,
                ModelPreflightKind::Split => Kind::Split,
                ModelPreflightKind::BenchmarkLock => Kind::BenchmarkLock,
                ModelPreflightKind::ParameterArtifact => Kind::ParameterArtifact,
                ModelPreflightKind::ModelArtifact => Kind::ModelArtifact,
                ModelPreflightKind::Prediction => Kind::Prediction,
                ModelPreflightKind::IndependentReview => Kind::IndependentReview,
            };
            amphora_solvency_score::preflight(kind, value).map_err(Into::into)
        }
        EIS_CORROSION_MODULE => {
            use amphora_barrier_corrosion_score::ContractKind as Kind;
            let kind = match kind {
                ModelPreflightKind::Observation => Kind::Observation,
                ModelPreflightKind::Dataset => Kind::Dataset,
                ModelPreflightKind::Split => Kind::Split,
                ModelPreflightKind::BenchmarkLock => Kind::BenchmarkLock,
                ModelPreflightKind::ModelArtifact => Kind::ModelArtifact,
                ModelPreflightKind::Prediction => Kind::Prediction,
                ModelPreflightKind::IndependentReview => Kind::IndependentReview,
                ModelPreflightKind::ParameterArtifact => {
                    bail!("parameter-artifact is not a measured-EIS contract")
                }
            };
            amphora_barrier_corrosion_score::preflight(kind, value).map_err(Into::into)
        }
        _ => bail!("unsupported scientific model module: {module}"),
    }
}

fn fit_model_artifact(
    root: &Path,
    module: &str,
    dataset_path: &Path,
    split_path: &Path,
    lock_path: &Path,
    output_path: &Path,
) -> Result<()> {
    require_scientific_model_module(module)?;
    let dataset_value = read_json(dataset_path)?;
    let split_value = read_json(split_path)?;
    let lock_value = read_json(lock_path)?;
    let artifact = match module {
        VISCOSITY_MODULE => {
            let dataset: amphora_viscosity_score::ViscosityDatasetV1 =
                serde_json::from_value(dataset_value)?;
            let split: amphora_viscosity_score::ViscositySplitV1 =
                serde_json::from_value(split_value)?;
            let lock: amphora_viscosity_score::ViscosityBenchmarkLockV1 =
                serde_json::from_value(lock_value)?;
            serde_json::to_value(amphora_viscosity_score::fit_model(&dataset, &split, &lock)?)?
        }
        SOLVENCY_MODULE => {
            let dataset: amphora_solvency_score::SolvencyDatasetV1 =
                serde_json::from_value(dataset_value)?;
            let split: amphora_solvency_score::SolvencySplitV1 =
                serde_json::from_value(split_value)?;
            let lock: amphora_solvency_score::SolvencyBenchmarkLockV1 =
                serde_json::from_value(lock_value)?;
            serde_json::to_value(amphora_solvency_score::fit_model(&dataset, &split, &lock)?)?
        }
        EIS_CORROSION_MODULE => {
            let dataset: amphora_barrier_corrosion_score::EisDatasetV1 =
                serde_json::from_value(dataset_value)?;
            let split: amphora_barrier_corrosion_score::EisSplitV1 =
                serde_json::from_value(split_value)?;
            let lock: amphora_barrier_corrosion_score::EisBenchmarkLockV1 =
                serde_json::from_value(lock_value)?;
            serde_json::to_value(amphora_barrier_corrosion_score::fit_model(
                &dataset, &split, &lock,
            )?)?
        }
        _ => unreachable!("module checked"),
    };
    let identity = ensure_local_identity(root)?;
    let mut signed = SignedModelArtifactV1 {
        schema: SIGNED_MODEL_ARTIFACT_SCHEMA.into(),
        module_id: module.into(),
        artifact_sha256: stable_hash(&artifact),
        artifact,
        signature: None,
    };
    signed.sign(&identity.key_id, &identity.signing_key)?;
    let output = rooted(root, output_path.to_path_buf());
    persist_json_immutable(&output, &signed)?;
    emit_jsonl(&serde_json::to_value(signed)?)
}

fn require_scientific_model_module(module: &str) -> Result<()> {
    if [VISCOSITY_MODULE, SOLVENCY_MODULE, EIS_CORROSION_MODULE].contains(&module) {
        Ok(())
    } else {
        bail!("unsupported scientific model module: {module}")
    }
}

fn verify_nested_raw_file_hashes(value: &Value, base: &Path) -> Result<usize> {
    let mut declared = BTreeMap::new();
    collect_nested_raw_file_hashes(value, &mut declared)?;
    if declared.is_empty() {
        bail!("contract has no raw_file_hashes to verify");
    }
    for (relative, expected) in &declared {
        let relative_path = Path::new(relative);
        if relative_path.is_absolute()
            || relative_path.components().any(|component| {
                matches!(
                    component,
                    std::path::Component::ParentDir | std::path::Component::RootDir
                )
            })
        {
            bail!("raw file path must remain beneath --raw-base-dir: {relative}");
        }
        let observed = raw_file_sha256(&base.join(relative_path))?;
        if &observed != expected {
            bail!("raw file SHA-256 mismatch for {relative}");
        }
    }
    Ok(declared.len())
}

fn collect_nested_raw_file_hashes(
    value: &Value,
    declared: &mut BTreeMap<String, String>,
) -> Result<()> {
    match value {
        Value::Object(object) => {
            if let Some(raw_hashes) = object.get("raw_file_hashes") {
                let raw_hashes = raw_hashes
                    .as_object()
                    .ok_or_else(|| anyhow!("raw_file_hashes must be an object"))?;
                for (path, hash) in raw_hashes {
                    let hash = hash
                        .as_str()
                        .ok_or_else(|| anyhow!("raw file hash must be a string"))?;
                    if declared.insert(path.clone(), hash.into()).is_some() {
                        bail!("duplicate raw file path across observation bundle: {path}");
                    }
                }
            }
            for nested in object.values() {
                collect_nested_raw_file_hashes(nested, declared)?;
            }
        }
        Value::Array(values) => {
            for nested in values {
                collect_nested_raw_file_hashes(nested, declared)?;
            }
        }
        _ => {}
    }
    Ok(())
}

pub fn run_pot_life(root: &Path, args: PotLifeArgs) -> Result<()> {
    match args.command {
        PotLifeCommand::Preflight {
            kind,
            input,
            raw_base_dir,
        } => {
            let report = preflight_pot_life(kind, &input, raw_base_dir.as_deref())?;
            emit_jsonl(&serde_json::to_value(report)?)
        }
        PotLifeCommand::Protocol {
            qualification,
            source_ledger,
            generated_on,
            mixing_method,
            output,
        } => {
            let qualification_path = qualification;
            let qualification: PotLifeScaleQualificationV1 =
                serde_json::from_value(read_json(&qualification_path)?)?;
            let source_ledger_hash = raw_file_sha256(&source_ledger)?;
            let protocol = generate_protocol(
                &qualification,
                &generated_on,
                &source_ledger_hash,
                &mixing_method,
            )?;
            let output = output.map(|path| rooted(root, path)).unwrap_or_else(|| {
                root.join(".amphora/pot-life/protocols")
                    .join(format!("{}.json", protocol.protocol_id))
            });
            persist_json_immutable(&output, &protocol)?;
            let receipt = control_receipt(
                root,
                CURE_MODULE,
                "pot-life protocol",
                true,
                EvidenceTier::ProspectiveReplicated,
                DecisionUse::Shadow,
                BTreeMap::from([
                    (
                        relative_display(root, &qualification_path),
                        raw_file_sha256(&qualification_path)?,
                    ),
                    (relative_display(root, &source_ledger), source_ledger_hash),
                    (relative_display(root, &output), raw_file_sha256(&output)?),
                ]),
                json!({
                    "track_id": protocol.track_id,
                    "protocol_id": protocol.protocol_id,
                    "planned_run_count": protocol.planned_runs.len(),
                    "sealed_holdout_count": protocol.planned_runs.iter().filter(|row| row.sealed_until_locked_evaluation).count(),
                    "scale_gate_passed": true,
                    "reactive_work_performed": false,
                }),
            )?;
            emit_jsonl(&serde_json::to_value(&protocol)?)?;
            emit_jsonl(&serde_json::to_value(receipt)?)
        }
        PotLifeCommand::Ingest { run, output } => {
            let value = read_json(&run)?;
            let owned_run: PotLifeRunV1 = serde_json::from_value(value)?;
            owned_run.validate()?;
            verify_owned_run_files(&owned_run, run.parent().unwrap_or(Path::new(".")))?;
            let output = output.map(|path| rooted(root, path)).unwrap_or_else(|| {
                root.join(".amphora/pot-life/runs")
                    .join(format!("{}.json", owned_run.run_id))
            });
            persist_json_immutable(&output, &owned_run)?;
            let receipt = control_receipt(
                root,
                CURE_MODULE,
                "pot-life ingest",
                true,
                EvidenceTier::ProspectiveReplicated,
                DecisionUse::Shadow,
                BTreeMap::from([
                    (relative_display(root, &run), raw_file_sha256(&run)?),
                    (relative_display(root, &output), raw_file_sha256(&output)?),
                ]),
                json!({
                    "track_id": owned_run.track_id,
                    "run_id": owned_run.run_id,
                    "split": owned_run.split,
                    "application_endpoint": owned_run.observed_application_interval()?,
                    "viscosity_proxy": owned_run.viscosity_proxy(),
                    "owned_evidence_only": true,
                    "candidate_pot_life_prediction_h": null,
                }),
            )?;
            emit_jsonl(&serde_json::to_value(receipt)?)
        }
        PotLifeCommand::Lock {
            protocol,
            runs_dir,
            output,
        } => {
            let protocol_value = read_json(&protocol)?;
            let protocol_contract: PotLifeProtocolV1 = serde_json::from_value(protocol_value)?;
            protocol_contract.validate()?;
            let runs = load_pot_life_runs(&runs_dir)?;
            let lock = lock_pot_life_benchmark(&protocol_contract, &runs)?;
            let output = output.map(|path| rooted(root, path)).unwrap_or_else(|| {
                root.join(".amphora/pot-life/locks")
                    .join(format!("{}.json", lock.benchmark_id))
            });
            persist_json_immutable(&output, &lock)?;
            let receipt = control_receipt(
                root,
                CURE_MODULE,
                "pot-life lock",
                true,
                EvidenceTier::ProspectiveReplicated,
                DecisionUse::Shadow,
                BTreeMap::from([
                    (
                        relative_display(root, &protocol),
                        raw_file_sha256(&protocol)?,
                    ),
                    (relative_display(root, &output), raw_file_sha256(&output)?),
                ]),
                json!({
                    "track_id": lock.track_id,
                    "benchmark_id": lock.benchmark_id,
                    "fit_run_count": lock.fit_run_ids.len(),
                    "sealed_holdout_count": lock.sealed_holdout_run_ids.len(),
                    "leakage_audit": lock.leakage_audit,
                    "holdouts_opened_for_fitting": false,
                }),
            )?;
            emit_jsonl(&serde_json::to_value(&lock)?)?;
            emit_jsonl(&serde_json::to_value(receipt)?)
        }
        PotLifeCommand::Evaluate {
            lock,
            runs_dir,
            source_ledger,
            prior_art_chart,
            independent_review,
            reviewed_packet,
            output,
            expert_packet_output,
            workers,
        } => {
            if independent_review.is_some() != reviewed_packet.is_some() {
                bail!("--independent-review and --reviewed-packet must be supplied together");
            }
            let lock_contract: PotLifeBenchmarkLockV1 = serde_json::from_value(read_json(&lock)?)?;
            lock_contract.validate()?;
            let runs = load_pot_life_runs(&runs_dir)?;
            let source_ledger_hash = raw_file_sha256(&source_ledger)?;
            let prior_art_hash = raw_file_sha256(&prior_art_chart)?;
            let review_contract: Option<IndependentReviewV1> = independent_review
                .as_ref()
                .map(|path| {
                    read_json(path)
                        .and_then(|value| Ok(serde_json::from_value::<IndependentReviewV1>(value)?))
                })
                .transpose()?;
            if let (Some(review), Some(packet_path)) =
                (review_contract.as_ref(), reviewed_packet.as_ref())
            {
                let packet: ExpertPacketV1 = serde_json::from_value(read_json(packet_path)?)?;
                packet.validate()?;
                if review.expert_packet_sha256 != pot_life_contract_hash(&packet)? {
                    bail!("independent review is not bound to the supplied expert packet");
                }
            }
            let model = evaluate_locked_benchmark(
                &lock_contract,
                &runs,
                &source_ledger_hash,
                review_contract.as_ref(),
                workers,
            )?;
            let output = output.map(|path| rooted(root, path)).unwrap_or_else(|| {
                root.join(".amphora/pot-life/models")
                    .join(format!("{}.json", model.model_id))
            });
            persist_json_immutable(&output, &model)?;
            let packet_path = if let Some(reviewed_packet) = reviewed_packet {
                reviewed_packet
            } else {
                let packet = seal_expert_packet(&model, &runs, &prior_art_hash)?;
                let packet_path = expert_packet_output
                    .map(|path| rooted(root, path))
                    .unwrap_or_else(|| {
                        root.join(".amphora/pot-life/expert-packets")
                            .join(format!("{}.json", packet.packet_id))
                    });
                persist_json_immutable(&packet_path, &packet)?;
                packet_path
            };
            let gate_passed = model.gate_status.authorizes_non_null_shadow_prediction();
            let expert_packet_status = if review_contract.is_some() {
                "REVIEW_RETURNED_PACKET_BOUND"
            } else {
                "SEALED_NOT_SENT_APPROVAL_REQUIRED"
            };
            let receipt = control_receipt(
                root,
                CURE_MODULE,
                "pot-life evaluate",
                gate_passed,
                EvidenceTier::ProspectiveReplicated,
                DecisionUse::Shadow,
                BTreeMap::from([
                    (relative_display(root, &lock), raw_file_sha256(&lock)?),
                    (relative_display(root, &source_ledger), source_ledger_hash),
                    (relative_display(root, &prior_art_chart), prior_art_hash),
                    (relative_display(root, &output), raw_file_sha256(&output)?),
                    (
                        relative_display(root, &packet_path),
                        raw_file_sha256(&packet_path)?,
                    ),
                ]),
                json!({
                    "track_id": model.track_id,
                    "model_id": model.model_id,
                    "authority": model.authority,
                    "benchmark_metrics": model.benchmark_metrics,
                    "gate_status": model.gate_status,
                    "locked_gate_passed": model.gate_status.locked_gate_passed(),
                    "independent_review_passed": model.gate_status.independent_review_passed,
                    "candidate_pot_life_prediction_h": null,
                    "expert_packet_delivery_status": expert_packet_status,
                    "fto_status": "FTO NOT PERFORMED",
                }),
            )?;
            emit_jsonl(&serde_json::to_value(&model)?)?;
            emit_jsonl(&serde_json::to_value(receipt)?)
        }
    }
}

fn preflight_pot_life(
    kind: PotLifePreflightKind,
    input: &Path,
    raw_base_dir: Option<&Path>,
) -> Result<PotLifePreflightReport> {
    let contract_kind = PotLifeContractKind::from(kind);
    if raw_base_dir.is_some() && contract_kind != PotLifeContractKind::Run {
        bail!("--raw-base-dir is valid only for --kind run");
    }
    let contract = preflight_contract(contract_kind, read_json(input)?)?;
    let raw_files_verified = if contract_kind == PotLifeContractKind::Run {
        let base = raw_base_dir
            .or_else(|| input.parent())
            .unwrap_or_else(|| Path::new("."));
        verify_raw_file_hashes(&contract.raw_file_hashes, base)?
    } else {
        0
    };
    Ok(PotLifePreflightReport {
        schema: "amphora.pot-life-preflight-report.v1",
        status: "VALID",
        kind: contract.kind.as_str(),
        input_path: input.to_string_lossy().replace('\\', "/"),
        input_sha256: raw_file_sha256(input)?,
        contract_schema: contract.schema,
        track_id: contract.track_id,
        contract_id: contract.contract_id,
        raw_files_verified,
        signed: false,
        artifacts_written: false,
        identities_written: false,
        receipts_written: false,
    })
}

fn rooted(root: &Path, path: PathBuf) -> PathBuf {
    if path.is_absolute() {
        path
    } else {
        root.join(path)
    }
}

fn persist_json_immutable<T: Serialize>(path: &Path, value: &T) -> Result<()> {
    persist_immutable(path, &canonical_bytes(&serde_json::to_value(value)?)?)
}

fn verify_owned_run_files(run: &PotLifeRunV1, base: &Path) -> Result<()> {
    verify_raw_file_hashes(&run.raw_file_hashes, base).map(|_| ())
}

fn verify_raw_file_hashes(hashes: &BTreeMap<String, String>, base: &Path) -> Result<usize> {
    for (path, expected_hash) in hashes {
        let path = PathBuf::from(path);
        let path = if path.is_absolute() {
            path
        } else {
            base.join(path)
        };
        let observed = raw_file_sha256(&path)?;
        if observed != *expected_hash {
            bail!("raw run file hash mismatch: {}", path.display());
        }
    }
    Ok(hashes.len())
}

fn load_pot_life_runs(directory: &Path) -> Result<Vec<PotLifeRunV1>> {
    let mut paths = fs::read_dir(directory)
        .with_context(|| format!("reading pot-life run directory {}", directory.display()))?
        .filter_map(|entry| entry.ok().map(|entry| entry.path()))
        .filter(|path| path.extension().and_then(|value| value.to_str()) == Some("json"))
        .collect::<Vec<_>>();
    paths.sort();
    if paths.is_empty() {
        bail!("pot-life run directory contains no JSON runs");
    }
    paths
        .into_iter()
        .map(|path| {
            let run: PotLifeRunV1 = serde_json::from_value(read_json(&path)?)?;
            run.validate()?;
            Ok(run)
        })
        .collect()
}

fn require_all(all: bool) -> Result<()> {
    if all {
        Ok(())
    } else {
        bail!("this phase-1 command requires explicit --all scope")
    }
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct SourceFetchV1 {
    download_url: String,
    expected_sha256: String,
    install_path: String,
    license_url: String,
    license_sha256: String,
    license_install_path: String,
    acquisition_record_path: String,
}

fn run_module_fetch(root: &Path, module: &str, source_id: &str) -> Result<()> {
    let source_path = fetch_source_path(module)?;
    let census = read_json(&root.join(source_path))?;
    if census.get("schema").and_then(Value::as_str) != Some("amphora.module-source-census.v1")
        || census.get("module_id").and_then(Value::as_str) != Some(module)
    {
        bail!("module source census identity mismatch for {module}");
    }
    let sources = census
        .get("sources")
        .and_then(Value::as_array)
        .ok_or_else(|| anyhow!("module source census has no sources"))?;
    let source = sources
        .iter()
        .find(|source| source.get("source_id").and_then(Value::as_str) == Some(source_id))
        .ok_or_else(|| anyhow!("unknown source {source_id} for module {module}"))?;
    let fetch: SourceFetchV1 = serde_json::from_value(
        source
            .get("fetch")
            .cloned()
            .ok_or_else(|| anyhow!("source {source_id} has no decision-complete fetch lock"))?,
    )?;
    validate_fetch_lock(&fetch)?;

    let install_path = safe_workspace_path(root, &fetch.install_path)?;
    let license_path = safe_workspace_path(root, &fetch.license_install_path)?;
    let acquisition_path = safe_workspace_path(root, &fetch.acquisition_record_path)?;
    let header_path = install_path.with_extension(format!(
        "{}.headers",
        install_path
            .extension()
            .and_then(|extension| extension.to_str())
            .unwrap_or("artifact")
    ));
    let license_header_path = license_path.with_extension(format!(
        "{}.headers",
        license_path
            .extension()
            .and_then(|extension| extension.to_str())
            .unwrap_or("license")
    ));

    let staging_root = root.join(".amphora/staging/fetch");
    fs::create_dir_all(&staging_root)?;
    if fs::symlink_metadata(&staging_root)?
        .file_type()
        .is_symlink()
    {
        bail!("fetch staging root cannot be a symlink");
    }
    let stage_id = format!(
        "{}-{}-{}",
        module.trim_start_matches("amphora-"),
        source_id,
        std::process::id()
    );
    let staged_payload = staging_root.join(format!("{stage_id}.payload"));
    let staged_headers = staging_root.join(format!("{stage_id}.payload.headers"));
    let staged_license = staging_root.join(format!("{stage_id}.license"));
    let staged_license_headers = staging_root.join(format!("{stage_id}.license.headers"));
    for path in [
        &staged_payload,
        &staged_headers,
        &staged_license,
        &staged_license_headers,
    ] {
        if path.exists() {
            bail!("fetch staging path already exists: {}", path.display());
        }
    }

    curl_fetch(&fetch.download_url, &staged_payload, &staged_headers)?;
    curl_fetch(&fetch.license_url, &staged_license, &staged_license_headers)?;
    let observed_sha256 = raw_file_sha256(&staged_payload)?;
    let observed_license_sha256 = raw_file_sha256(&staged_license)?;
    if observed_sha256 != fetch.expected_sha256 || observed_license_sha256 != fetch.license_sha256 {
        bail!("remote bytes changed for {module}/{source_id}; staged content was not installed");
    }

    let acquired_at_unix = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .context("system clock precedes UNIX epoch")?
        .as_secs();
    let payload_bytes = fs::read(&staged_payload)?;
    let header_bytes = fs::read(&staged_headers)?;
    let license_bytes = fs::read(&staged_license)?;
    let license_header_bytes = fs::read(&staged_license_headers)?;
    let acquisition = json!({
        "schema": "amphora.network-acquisition.v1",
        "module_id": module,
        "source_id": source_id,
        "source_census": source_path,
        "source_census_sha256": raw_file_sha256(&root.join(source_path))?,
        "url": fetch.download_url,
        "response_headers_path": relative_display(root, &header_path),
        "response_headers_sha256": raw_sha256(&header_bytes),
        "acquired_at_unix": acquired_at_unix,
        "payload_path": fetch.install_path,
        "payload_sha256": observed_sha256,
        "payload_size_bytes": payload_bytes.len(),
        "license_url": fetch.license_url,
        "license_path": fetch.license_install_path,
        "license_sha256": observed_license_sha256,
        "license_size_bytes": license_bytes.len(),
        "license_response_headers_path": relative_display(root, &license_header_path),
        "license_response_headers_sha256": raw_sha256(&license_header_bytes),
        "immutable_install": true,
    });
    let acquisition_bytes = canonical_bytes(&acquisition)?;
    for (path, bytes) in [
        (&install_path, payload_bytes.as_slice()),
        (&header_path, header_bytes.as_slice()),
        (&license_path, license_bytes.as_slice()),
        (&license_header_path, license_header_bytes.as_slice()),
        (&acquisition_path, acquisition_bytes.as_slice()),
    ] {
        ensure_immutable_target_compatible(path, bytes)?;
    }
    for (path, bytes) in [
        (&install_path, payload_bytes.as_slice()),
        (&header_path, header_bytes.as_slice()),
        (&license_path, license_bytes.as_slice()),
        (&license_header_path, license_header_bytes.as_slice()),
        (&acquisition_path, acquisition_bytes.as_slice()),
    ] {
        persist_immutable(path, bytes)?;
    }
    for path in [
        staged_payload,
        staged_headers,
        staged_license,
        staged_license_headers,
    ] {
        fs::remove_file(path)?;
    }
    emit_jsonl(&acquisition)
}

fn fetch_source_path(module: &str) -> Result<&'static str> {
    if module == DESIGN_RULE_MODULE {
        return Ok(DESIGN_RULE_SOURCES_PATH);
    }
    module_paths(module).map(|(source_path, _, _)| source_path)
}

fn validate_fetch_lock(fetch: &SourceFetchV1) -> Result<()> {
    for (name, value) in [
        ("download_url", fetch.download_url.as_str()),
        ("install_path", fetch.install_path.as_str()),
        ("license_url", fetch.license_url.as_str()),
        ("license_install_path", fetch.license_install_path.as_str()),
        (
            "acquisition_record_path",
            fetch.acquisition_record_path.as_str(),
        ),
    ] {
        if value.trim().is_empty() {
            bail!("fetch lock field {name} is empty");
        }
    }
    for (name, value) in [
        ("expected_sha256", fetch.expected_sha256.as_str()),
        ("license_sha256", fetch.license_sha256.as_str()),
    ] {
        if value.len() != 64
            || value
                .bytes()
                .any(|byte| !byte.is_ascii_digit() && !(b'a'..=b'f').contains(&byte))
        {
            bail!("fetch lock field {name} is not a lowercase SHA-256");
        }
    }
    for (name, value) in [
        ("download_url", fetch.download_url.as_str()),
        ("license_url", fetch.license_url.as_str()),
    ] {
        if !value.starts_with("https://") && !value.starts_with("http://") {
            bail!("fetch lock field {name} must use HTTP(S)");
        }
    }
    Ok(())
}

fn safe_workspace_path(root: &Path, relative: &str) -> Result<PathBuf> {
    let relative = Path::new(relative);
    if relative.is_absolute()
        || relative
            .components()
            .any(|component| !matches!(component, Component::Normal(_)))
    {
        bail!("fetch install paths must be traversal-free workspace-relative paths");
    }
    Ok(root.join(relative))
}

fn curl_fetch(url: &str, output: &Path, headers: &Path) -> Result<()> {
    let status = Command::new("curl")
        .args([
            "--fail",
            "--silent",
            "--show-error",
            "--location",
            "--proto",
            "=http,https",
            "--output",
        ])
        .arg(output)
        .arg("--dump-header")
        .arg(headers)
        .arg(url)
        .status()
        .with_context(|| format!("launching curl for {url}"))?;
    if !status.success() {
        bail!("network acquisition failed for {url}");
    }
    Ok(())
}

fn ensure_immutable_target_compatible(path: &Path, bytes: &[u8]) -> Result<()> {
    if path.exists() && fs::read(path)? != bytes {
        bail!(
            "immutable artifact already exists with different bytes: {}",
            path.display()
        );
    }
    Ok(())
}

#[derive(Debug, Clone, Copy)]
enum ModuleDataAction {
    Acquire,
    Build,
    Verify,
}

#[derive(Debug)]
struct ModuleDataAudit {
    module_id: String,
    artifact_hashes: BTreeMap<String, String>,
    rights: Vec<RightsRecordV1>,
    planned_sources: usize,
    available_sources: usize,
    eligible_sources: usize,
    quarantined_sources: usize,
    missing_sources: usize,
    missing_files: usize,
    mismatched_files: usize,
    reported_rows: u64,
    eligible_rows: u64,
    eligible_systems: BTreeSet<String>,
    eligible_studies: BTreeSet<String>,
    endpoint_counts: BTreeMap<String, u64>,
}

impl ModuleDataAudit {
    fn integrity_valid(&self) -> bool {
        self.missing_files == 0 && self.mismatched_files == 0
    }

    fn acquisition_complete(&self) -> bool {
        self.integrity_valid() && self.missing_sources == 0
    }
}

fn module_paths(module: &str) -> Result<(&'static str, &'static str, &'static str)> {
    match module {
        CORROSION_MODULE => Ok((
            CORROSION_SOURCES_PATH,
            CORROSION_SPLIT_PATH,
            "config/benchmark-locks/amphora-public-corrosion-benchmark.v1.json",
        )),
        CURE_MODULE => Ok((
            CURE_SOURCES_PATH,
            CURE_SPLIT_PATH,
            "config/benchmark-locks/amphora-cure-potlife-gate.v1.json",
        )),
        VISCOSITY_MODULE => Ok((
            VISCOSITY_SOURCES_PATH,
            VISCOSITY_SPLIT_PATH,
            "config/benchmark-locks/amphora-viscosity-score.v1.json",
        )),
        SOLVENCY_MODULE => Ok((
            SOLVENCY_SOURCES_PATH,
            SOLVENCY_SPLIT_PATH,
            "config/benchmark-locks/amphora-solvency-score.v1.json",
        )),
        EIS_CORROSION_MODULE => Ok((
            EIS_CORROSION_SOURCES_PATH,
            EIS_CORROSION_SPLIT_PATH,
            "config/benchmark-locks/amphora-barrier-corrosion-score.v1.json",
        )),
        MOLECULE_PROPERTY_MODULE => Ok((
            MOLECULE_PROPERTY_SOURCES_PATH,
            MOLECULE_PROPERTY_SPLIT_PATH,
            "config/benchmark-locks/amphora-molecule-property.v1.json",
        )),
        MOLECULE_ROLE_MODULE => Ok((
            MOLECULE_ROLE_SOURCES_PATH,
            MOLECULE_ROLE_SPLIT_PATH,
            "config/benchmark-locks/amphora-molecule-role-ranker.v1.json",
        )),
        _ => bail!("unsupported phase-acceleration module: {module}"),
    }
}

fn run_module_data(root: &Path, module: &str, action: ModuleDataAction) -> Result<()> {
    let audit = audit_module_data(root, module)?;
    match action {
        ModuleDataAction::Acquire | ModuleDataAction::Verify => {
            let verb = match action {
                ModuleDataAction::Acquire => "acquire",
                ModuleDataAction::Verify => "verify",
                ModuleDataAction::Build => unreachable!(),
            };
            let passed = audit.acquisition_complete();
            let details = module_data_details(&audit);
            let receipt = module_control_receipt(
                root,
                module,
                &format!("data {verb} --module {module}"),
                passed,
                EvidenceTier::PublicRetrospective,
                DecisionUse::AuditOnly,
                audit.artifact_hashes,
                details,
            )?;
            emit_jsonl(&serde_json::to_value(receipt)?)
        }
        ModuleDataAction::Build => {
            if !audit.integrity_valid() {
                bail!("cannot build {module}: cached source integrity failed");
            }
            let identity = ensure_local_identity(root)?;
            let executable = std::env::current_exe().context("resolving module data builder")?;
            let raw_set_hash = stable_hash(&serde_json::to_value(&audit.artifact_hashes)?);
            let builder_hash = raw_file_sha256(&executable)?;
            let build_identity_hash = stable_hash(&json!({
                "module_id": module,
                "raw_set_hash": raw_set_hash,
                "builder_hash": builder_hash,
                "schema": DATASET_MANIFEST_SCHEMA,
            }));
            let dataset_id = format!(
                "{}-rights-cleared-{}",
                module.trim_start_matches("amphora-"),
                &build_identity_hash[..16]
            );
            let (source_path, _, _) = module_paths(module)?;
            let manifest = DatasetManifestV1 {
                schema: DATASET_MANIFEST_SCHEMA.into(),
                dataset_id: dataset_id.clone(),
                raw_hashes: audit.artifact_hashes.clone(),
                rights: audit.rights,
                row_provenance: Vec::new(),
                units: module_units(module),
                methods: module_methods(module),
                conditions: BTreeMap::from([
                    ("module_id".into(), module.into()),
                    ("source_census".into(), source_path.into()),
                    ("evidence_tier".into(), "PUBLIC_RETROSPECTIVE".into()),
                    ("decision_use_ceiling".into(), "SHADOW".into()),
                    (
                        "rights_quarantine".into(),
                        "rows without explicit derivative-use eligibility excluded".into(),
                    ),
                ]),
                builder_hash,
                schema_hash: stable_hash(&Value::String(DATASET_MANIFEST_SCHEMA.into())),
                row_count: audit.eligible_rows,
            };
            manifest.validate()?;
            let path = root
                .join(".amphora/data")
                .join(format!("{dataset_id}.json"));
            persist_immutable(&path, &canonical_bytes(&serde_json::to_value(&manifest)?)?)?;
            let mut hashes = audit.artifact_hashes;
            hashes.insert(relative_display(root, &path), raw_file_sha256(&path)?);
            let mut receipt = new_module_receipt(
                root,
                module,
                &format!("data build --module {module}"),
                true,
                EvidenceTier::PublicRetrospective,
                if manifest.row_count > 0 {
                    DecisionUse::Shadow
                } else {
                    DecisionUse::AuditOnly
                },
                hashes,
                json!({
                    "dataset_id": dataset_id,
                    "dataset_manifest": relative_display(root, &path),
                    "eligible_row_count": manifest.row_count,
                    "quarantined_sources": audit.quarantined_sources,
                    "planned_sources_missing": audit.missing_sources,
                    "phase_promotion_implied": false,
                }),
            )?;
            receipt.metrics.insert(
                "source_genesis_hash".into(),
                Value::String(identity.genesis_hash.clone()),
            );
            bind_receipt_identity(&mut receipt)?;
            receipt.sign(&identity.key_id, &identity.signing_key)?;
            persist_receipt(root, &receipt)?;
            emit_jsonl(&serde_json::to_value(receipt)?)
        }
    }
}

fn audit_module_data(root: &Path, module: &str) -> Result<ModuleDataAudit> {
    let (source_path, _, _) = module_paths(module)?;
    let census = read_json(&root.join(source_path))?;
    if census.get("schema").and_then(Value::as_str) != Some("amphora.module-source-census.v1")
        || census.get("module_id").and_then(Value::as_str) != Some(module)
    {
        bail!("module source census identity mismatch for {module}");
    }
    let sources = census
        .get("sources")
        .and_then(Value::as_array)
        .ok_or_else(|| anyhow!("module source census has no sources"))?;
    let mut audit = ModuleDataAudit {
        module_id: module.into(),
        artifact_hashes: BTreeMap::from([(
            source_path.into(),
            raw_file_sha256(&root.join(source_path))?,
        )]),
        rights: Vec::new(),
        planned_sources: sources.len(),
        available_sources: 0,
        eligible_sources: 0,
        quarantined_sources: 0,
        missing_sources: 0,
        missing_files: 0,
        mismatched_files: 0,
        reported_rows: 0,
        eligible_rows: 0,
        eligible_systems: BTreeSet::new(),
        eligible_studies: BTreeSet::new(),
        endpoint_counts: BTreeMap::new(),
    };

    for source in sources {
        let source_id = required_str(source, "source_id")?;
        let publisher = required_str(source, "publisher")?;
        let source_url = required_str(source, "source_url")?;
        let license = required_str(source, "license")?;
        let rights_status = required_str(source, "rights_status")?;
        let eligible = source
            .get("eligible_for_derivatives")
            .and_then(Value::as_bool)
            .unwrap_or(false);
        let restrictions = source
            .get("restrictions")
            .and_then(Value::as_array)
            .into_iter()
            .flatten()
            .filter_map(Value::as_str)
            .map(str::to_owned)
            .collect();
        audit.rights.push(RightsRecordV1 {
            source_id: source_id.into(),
            license: license.into(),
            status: rights_status.into(),
            source_url: source_url.into(),
            restrictions,
            eligible_for_derivatives: eligible,
        });
        if eligible {
            audit.eligible_sources += 1;
        } else {
            audit.quarantined_sources += 1;
        }
        let Some(local_manifest) = source.get("local_manifest").and_then(Value::as_str) else {
            audit.missing_sources += 1;
            continue;
        };
        let Some(expected_hash) = source.get("local_manifest_sha256").and_then(Value::as_str)
        else {
            audit.mismatched_files += 1;
            continue;
        };
        let local_path = root.join(local_manifest);
        if !local_path.is_file() {
            audit.missing_files += 1;
            continue;
        }
        let observed_hash = raw_file_sha256(&local_path)?;
        if observed_hash != expected_hash {
            audit.mismatched_files += 1;
            continue;
        }
        audit.available_sources += 1;
        audit
            .artifact_hashes
            .insert(local_manifest.into(), observed_hash);
        if module == CORROSION_MODULE {
            audit_corrosion_source(root, source, &mut audit)?;
        } else if module == CURE_MODULE {
            audit_cure_source(source, &read_json(&local_path)?, &mut audit)?;
        } else if matches!(module, MOLECULE_PROPERTY_MODULE | MOLECULE_ROLE_MODULE) {
            audit_molecule_benchmark(root, module, &read_json(&local_path)?, eligible, &mut audit)?;
        } else {
            audit_model_source_landscape(module, &read_json(&local_path)?, &mut audit)?;
        }
        let _ = publisher;
    }
    Ok(audit)
}

fn audit_molecule_benchmark(
    root: &Path,
    module: &str,
    benchmark: &Value,
    eligible: bool,
    audit: &mut ModuleDataAudit,
) -> Result<()> {
    let (schema, groups): (&str, &[(&str, &str)]) = if module == MOLECULE_PROPERTY_MODULE {
        (
            "amphora.molecule_property.eew_ahew_benchmark.v1",
            &[
                ("exact_implementation_checks", "exact_defined_controls"),
                ("independent_monodisperse_records", "independent_references"),
                ("technical_grade_lower_bound_records", "measured_only_annex"),
                ("negative_controls", "negative_controls"),
            ],
        )
    } else {
        (
            "amphora.molecule_role_ranker.role_fit_benchmark.v1",
            &[
                ("exact_defined_controls", "exact_defined_controls"),
                ("measured_only_commercial_controls", "measured_only_annex"),
            ],
        )
    };
    if benchmark.get("schema_version").and_then(Value::as_str) != Some(schema) {
        bail!("molecule benchmark schema mismatch for {module}");
    }
    if module == MOLECULE_ROLE_MODULE {
        let expected_property_hash = required_str(benchmark, "upstream_property_benchmark_sha256")?;
        if raw_file_sha256(&root.join(MOLECULE_PROPERTY_BENCHMARK_PATH))? != expected_property_hash
        {
            bail!("role benchmark upstream property hash is stale");
        }
        let molecule_library_path =
            "amphora-molecule-role-ranker/reference/mvp20/data/molecule_library.json";
        let expected_library_hash = benchmark
            .pointer("/source_artifacts/molecule_library.json")
            .and_then(Value::as_str)
            .ok_or_else(|| anyhow!("role benchmark has no molecule-library hash"))?;
        if raw_file_sha256(&root.join(molecule_library_path))? != expected_library_hash {
            bail!("role benchmark molecule-library hash is stale");
        }
        audit.artifact_hashes.insert(
            MOLECULE_PROPERTY_BENCHMARK_PATH.into(),
            expected_property_hash.into(),
        );
        audit
            .artifact_hashes
            .insert(molecule_library_path.into(), expected_library_hash.into());
    }
    for (field, endpoint) in groups {
        let rows = benchmark
            .get(*field)
            .and_then(Value::as_array)
            .ok_or_else(|| anyhow!("molecule benchmark has no {field}"))?;
        audit.reported_rows = audit
            .reported_rows
            .checked_add(rows.len() as u64)
            .ok_or_else(|| anyhow!("molecule benchmark row count overflow"))?;
        *audit.endpoint_counts.entry((*endpoint).into()).or_default() += rows.len() as u64;
        if eligible {
            audit.eligible_rows = audit
                .eligible_rows
                .checked_add(rows.len() as u64)
                .ok_or_else(|| anyhow!("eligible molecule row count overflow"))?;
        }
    }
    Ok(())
}

fn audit_model_source_landscape(
    module: &str,
    landscape: &Value,
    audit: &mut ModuleDataAudit,
) -> Result<()> {
    if landscape.get("schema").and_then(Value::as_str) != Some("amphora.model-source-landscape.v1")
        || landscape.get("module_id").and_then(Value::as_str) != Some(module)
        || landscape.get("fto_status").and_then(Value::as_str) != Some("FTO NOT PERFORMED")
    {
        bail!("model source landscape identity or FTO quarantine is invalid for {module}");
    }
    let sources = landscape
        .get("sources")
        .and_then(Value::as_array)
        .ok_or_else(|| anyhow!("model source landscape has no sources"))?;
    let patents = landscape
        .get("patents")
        .and_then(Value::as_array)
        .ok_or_else(|| anyhow!("model source landscape has no patent list"))?;
    audit.reported_rows = audit
        .reported_rows
        .checked_add((sources.len() + patents.len()) as u64)
        .ok_or_else(|| anyhow!("source landscape row count overflow"))?;
    audit.endpoint_counts.insert(
        "quarantined_method_and_prior_art_context".into(),
        (sources.len() + patents.len()) as u64,
    );
    if sources.iter().any(|source| {
        source
            .get("eligible_for_derivatives")
            .and_then(Value::as_bool)
            == Some(true)
            && source.get("raw_sha256").and_then(Value::as_str).is_none()
    }) {
        bail!("source without acquired raw hash cannot be derivative-eligible");
    }
    Ok(())
}

fn audit_corrosion_source(root: &Path, source: &Value, audit: &mut ModuleDataAudit) -> Result<()> {
    let prior_reported_rows = audit.reported_rows;
    let prior_eligible_rows = audit.eligible_rows;
    let local_manifest = required_str(source, "local_manifest")?;
    let manifest = read_json(&root.join(local_manifest))?;
    let entries = manifest
        .get("entries")
        .and_then(Value::as_array)
        .ok_or_else(|| anyhow!("corrosion source manifest has no entries"))?;
    let source_id = required_str(source, "source_id")?;
    let study_id = required_str(source, "study_id")?;
    let eligible = source
        .get("eligible_for_derivatives")
        .and_then(Value::as_bool)
        .unwrap_or(false);
    let reference_root = Path::new(local_manifest)
        .parent()
        .and_then(Path::parent)
        .ok_or_else(|| anyhow!("corrosion source manifest path has no reference root"))?;
    for entry in entries {
        let relative = required_str(entry, "raw_path")?;
        let expected = required_str(entry, "sha256")?;
        let raw_relative = reference_root.join(relative);
        let raw_path = root.join(&raw_relative);
        if !raw_path.is_file() {
            audit.missing_files += 1;
            continue;
        }
        let observed = raw_file_sha256(&raw_path)?;
        if observed != expected {
            audit.mismatched_files += 1;
            continue;
        }
        audit
            .artifact_hashes
            .insert(raw_relative.to_string_lossy().replace('\\', "/"), observed);
        let rows = entry.get("row_count").and_then(Value::as_u64).unwrap_or(0);
        audit.reported_rows = audit
            .reported_rows
            .checked_add(rows)
            .ok_or_else(|| anyhow!("corrosion row count overflow"))?;
        let category = required_str(entry, "category")?;
        *audit.endpoint_counts.entry(category.into()).or_default() += rows;
        if eligible {
            audit.eligible_rows = audit
                .eligible_rows
                .checked_add(rows)
                .ok_or_else(|| anyhow!("eligible corrosion row count overflow"))?;
            audit.eligible_studies.insert(study_id.into());
            audit
                .eligible_systems
                .insert(required_str(entry, "sample_system")?.into());
        }
    }
    if source_id.is_empty() {
        bail!("empty corrosion source ID");
    }
    let derived_path = required_str(source, "derived_observation_table")?;
    let derived_expected = required_str(source, "derived_observation_table_sha256")?;
    let derived_observed = raw_file_sha256(&root.join(derived_path))?;
    if derived_observed != derived_expected {
        audit.mismatched_files += 1;
        return Ok(());
    }
    let derived = read_json(&root.join(derived_path))?;
    let eis_rows = derived
        .get("parsed_eis_rows")
        .and_then(Value::as_array)
        .ok_or_else(|| anyhow!("corrosion derived table has no parsed_eis_rows"))?;
    let endpoint_measurements = derived
        .get("raw_endpoint_measurements")
        .and_then(Value::as_array)
        .ok_or_else(|| anyhow!("corrosion derived table has no raw_endpoint_measurements"))?;
    for row in eis_rows.iter().chain(endpoint_measurements) {
        let raw_path = required_str(row, "raw_path")?;
        let bound_path = reference_root
            .join(raw_path)
            .to_string_lossy()
            .replace('\\', "/");
        if !audit.artifact_hashes.contains_key(&bound_path) {
            bail!("derived corrosion observation is not bound to verified raw bytes: {raw_path}");
        }
    }
    audit
        .artifact_hashes
        .insert(derived_path.into(), derived_observed);
    let derived_rows = (eis_rows.len() + endpoint_measurements.len()) as u64;
    audit.reported_rows = prior_reported_rows
        .checked_add(derived_rows)
        .ok_or_else(|| anyhow!("corrosion derived row count overflow"))?;
    if eligible {
        audit.eligible_rows = prior_eligible_rows
            .checked_add(derived_rows)
            .ok_or_else(|| anyhow!("eligible corrosion derived row count overflow"))?;
    } else {
        audit.eligible_rows = prior_eligible_rows;
    }
    *audit
        .endpoint_counts
        .entry("eis_summary_rows".into())
        .or_default() += eis_rows.len() as u64;
    *audit
        .endpoint_counts
        .entry("non_eis_endpoint_measurements".into())
        .or_default() += endpoint_measurements.len() as u64;
    Ok(())
}

fn audit_cure_source(source: &Value, dataset: &Value, audit: &mut ModuleDataAudit) -> Result<()> {
    let rows = dataset
        .get("rows")
        .and_then(Value::as_array)
        .ok_or_else(|| anyhow!("cure source has no rows"))?;
    audit.reported_rows = audit
        .reported_rows
        .checked_add(rows.len() as u64)
        .ok_or_else(|| anyhow!("cure row count overflow"))?;
    *audit.endpoint_counts.entry("gel_time".into()).or_default() += rows.len() as u64;
    let eligible = source
        .get("eligible_for_derivatives")
        .and_then(Value::as_bool)
        .unwrap_or(false);
    if eligible {
        for row in rows {
            let complete = row.get("phr").and_then(Value::as_f64).is_some()
                && row.get("resin_family").and_then(Value::as_str).is_some()
                && row.get("hardener_family").and_then(Value::as_str).is_some()
                && row.get("temperature_C").and_then(Value::as_f64).is_some()
                && row.get("test_mass_g").and_then(Value::as_f64).is_some()
                && row.get("method").and_then(Value::as_str).is_some();
            if complete {
                audit.eligible_rows += 1;
            }
        }
    }
    Ok(())
}

fn module_data_details(audit: &ModuleDataAudit) -> Value {
    json!({
        "module_id": audit.module_id,
        "planned_sources": audit.planned_sources,
        "available_sources": audit.available_sources,
        "planned_sources_missing": audit.missing_sources,
        "eligible_sources": audit.eligible_sources,
        "quarantined_sources": audit.quarantined_sources,
        "missing_files": audit.missing_files,
        "mismatched_files": audit.mismatched_files,
        "reported_rows": audit.reported_rows,
        "eligible_rows": audit.eligible_rows,
        "eligible_system_count": audit.eligible_systems.len(),
        "eligible_study_count": audit.eligible_studies.len(),
        "endpoint_counts": audit.endpoint_counts,
        "rights_quarantine_enforced": true,
        "network_mutation": false,
    })
}

fn module_units(module: &str) -> BTreeMap<String, String> {
    if module == CORROSION_MODULE {
        BTreeMap::from([
            ("frequency".into(), "Hz".into()),
            ("impedance_modulus".into(), "ohm".into()),
            ("phase".into(), "degree".into()),
            ("ocv".into(), "V".into()),
            ("ocv_slope".into(), "V/s".into()),
            ("rust_creep".into(), "mm".into()),
            ("wet_adhesion".into(), "MPa".into()),
            ("cathodic_disbondment".into(), "mm".into()),
        ])
    } else if module == CURE_MODULE {
        BTreeMap::from([
            ("gel_time".into(), "min".into()),
            ("pot_life".into(), "min".into()),
            ("dry_hard_time".into(), "h".into()),
            ("through_cure_time".into(), "h".into()),
            ("dsc_conversion".into(), "fraction_0_1".into()),
        ])
    } else if module == VISCOSITY_MODULE {
        BTreeMap::from([
            ("apparent_viscosity".into(), "Pa.s".into()),
            ("stormer".into(), "KU".into()),
            ("sag_index".into(), "mil".into()),
            ("yield_stress".into(), "Pa".into()),
        ])
    } else if module == SOLVENCY_MODULE {
        BTreeMap::from([
            ("min_tpd".into(), "RT".into()),
            ("hessian_eigenvalue".into(), "dimensionless".into()),
            ("turbidity".into(), "NTU".into()),
        ])
    } else if matches!(module, MOLECULE_PROPERTY_MODULE | MOLECULE_ROLE_MODULE) {
        BTreeMap::from([
            ("molecular_weight".into(), "g/mol".into()),
            ("eew".into(), "g/eq".into()),
            ("ahew".into(), "g/eq".into()),
            ("classification_probability".into(), "fraction_0_1".into()),
        ])
    } else {
        BTreeMap::from([
            ("impedance_area_normalized".into(), "ohm.cm2".into()),
            ("rust_creep".into(), "mm".into()),
            ("wet_adhesion".into(), "MPa".into()),
        ])
    }
}

fn module_methods(module: &str) -> Vec<String> {
    if module == CORROSION_MODULE {
        vec![
            "single-frequency |Z|@0.01 Hz summaries remain distinct from full EIS spectra".into(),
            "study/system blocked evaluation".into(),
            "Kramers-Kronig and equivalent-circuit analysis abstains without frequency-resolved real/imaginary spectra".into(),
        ]
    } else if module == CURE_MODULE {
        vec![
            "gel time, pot life, dry-hard, through-cure, and DSC conversion remain separate endpoints".into(),
            "primary gel-time rows require resin, hardener family, mix ratio, temperature, test mass, and method".into(),
            "Arrhenius requires a genuine multi-temperature series; kinetic models require DSC curves".into(),
        ]
    } else if module == VISCOSITY_MODULE {
        vec![
            "Grunberg-Nissan/Arrhenius plus Krieger-Dougherty and Herschel-Bulkley".into(),
            "ASTM D562 KU and ASTM D4400 sag remain separately calibrated heads".into(),
        ]
    } else if module == SOLVENCY_MODULE {
        vec![
            "temperature-aware Flory-Huggins/Redlich-Kister Gibbs energy".into(),
            "deterministic multi-start Michelsen tangent-plane minimization".into(),
        ]
    } else if matches!(module, MOLECULE_PROPERTY_MODULE | MOLECULE_ROLE_MODULE) {
        vec![
            "host-owned RDKit C++ 2026.03.2 normalization with exact version match".into(),
            "locked reactive ontology v1; candidate-supplied facts ignored".into(),
            "commercial products and polydisperse grades remain measured-only".into(),
        ]
    } else {
        vec![
            "measured full-spectrum coated-metal equivalent circuit or declared single-frequency summary".into(),
            "rust creep and wet adhesion remain separate measured endpoint heads".into(),
        ]
    }
}

fn audit_data(root: &Path) -> Result<DataAudit> {
    let sources = read_json(&root.join(DATA_SOURCES_PATH))?;
    let report = read_json(&root.join(ACQUISITION_REPORT_PATH))?;
    let derived = read_json(&root.join(DERIVED_MANIFEST_PATH))?;
    let source_rows = sources
        .get("sources")
        .and_then(Value::as_array)
        .ok_or_else(|| anyhow!("dataset source manifest has no sources"))?;
    let report_rows = report
        .get("results")
        .and_then(Value::as_array)
        .ok_or_else(|| anyhow!("acquisition report has no results"))?;
    let by_id: BTreeMap<_, _> = report_rows
        .iter()
        .filter_map(|row| Some((row.get("source_id")?.as_str()?.to_owned(), row)))
        .collect();
    let source_manifest_hash = raw_file_sha256(&root.join(DATA_SOURCES_PATH))?;
    let acquisition_report_hash = raw_file_sha256(&root.join(ACQUISITION_REPORT_PATH))?;
    let mut artifact_hashes = BTreeMap::from([
        (DATA_SOURCES_PATH.into(), source_manifest_hash.clone()),
        (
            ACQUISITION_REPORT_PATH.into(),
            acquisition_report_hash.clone(),
        ),
        (
            DERIVED_MANIFEST_PATH.into(),
            raw_file_sha256(&root.join(DERIVED_MANIFEST_PATH))?,
        ),
    ]);
    let mut verified_files = 0;
    let mut missing_files = 0;
    let mut mismatched_files = 0;
    let mut eligible_sources = 0;
    let mut quarantined_sources = 0;
    let mut rights = Vec::new();
    let mut row_count = 0_u64;

    for source in source_rows {
        let source_id = required_str(source, "id")?;
        let license = required_str(source, "license")?;
        let source_url = required_str(source, "source_url")?;
        let access_status = required_str(source, "access_status")?;
        let report_row = by_id.get(source_id);
        let acquisition_status = report_row
            .and_then(|row| row.get("status"))
            .and_then(Value::as_str)
            .unwrap_or("NOT_ACQUIRED");
        let eligible = rights_eligible(license, access_status, acquisition_status);
        if eligible {
            eligible_sources += 1;
        } else {
            quarantined_sources += 1;
        }
        rights.push(RightsRecordV1 {
            source_id: source_id.into(),
            license: license.into(),
            status: if eligible { "ACCEPTED" } else { "QUARANTINED" }.into(),
            source_url: source_url.into(),
            restrictions: if eligible {
                Vec::new()
            } else {
                vec![format!(
                    "access={access_status}; acquisition={acquisition_status}; license={license}"
                )]
            },
            eligible_for_derivatives: eligible,
        });
        if !eligible {
            continue;
        }
        let raw_dir = required_str(source, "local_raw_path")?;
        if let Some(downloads) = report_row
            .and_then(|row| row.get("downloads"))
            .and_then(Value::as_array)
        {
            for download in downloads {
                let Some(expected) = download.get("sha256").and_then(Value::as_str) else {
                    continue;
                };
                let filename = required_str(download, "filename")?;
                let relative = Path::new(raw_dir).join(filename);
                let path = root.join(&relative);
                if !path.is_file() {
                    missing_files += 1;
                    continue;
                }
                let observed = raw_file_sha256(&path)?;
                if observed == expected {
                    verified_files += 1;
                    artifact_hashes.insert(relative.to_string_lossy().into_owned(), observed);
                } else {
                    mismatched_files += 1;
                }
            }
        }
        if let Some(profiles) = report_row
            .and_then(|row| row.get("profiles"))
            .and_then(Value::as_array)
        {
            for profile in profiles {
                row_count = row_count
                    .checked_add(profile.get("rows").and_then(Value::as_u64).unwrap_or(0))
                    .ok_or_else(|| anyhow!("dataset row count overflow"))?;
            }
        }
    }
    if derived
        .get("runtime_artifact_source_ids")
        .and_then(Value::as_object)
        .is_none()
    {
        bail!("derived build manifest lacks runtime source lineage");
    }
    let metadata_binding_valid = report.get("manifest_sha256").and_then(Value::as_str)
        == Some(source_manifest_hash.as_str())
        && derived.get("input_manifest_sha256").and_then(Value::as_str)
            == Some(source_manifest_hash.as_str())
        && derived
            .get("input_acquisition_report_sha256")
            .and_then(Value::as_str)
            == Some(acquisition_report_hash.as_str());
    Ok(DataAudit {
        artifact_hashes,
        verified_files,
        missing_files,
        mismatched_files,
        eligible_sources,
        quarantined_sources,
        rights,
        row_count,
        metadata_binding_valid,
    })
}

fn rights_eligible(license: &str, access: &str, acquisition: &str) -> bool {
    let license = license.to_ascii_lowercase();
    let recognized = [
        "cc-by-4.0",
        "cc by 4.0",
        "cc0",
        "mit",
        "bsd-3-clause",
        "apache-2.0",
        "nist open license",
    ]
    .iter()
    .any(|allowed| license.contains(allowed));
    let restricted = [
        "academic purpose only",
        "terms apply",
        "prohibited",
        "service reference",
        "no conservative bulk",
    ]
    .iter()
    .any(|marker| license.contains(marker));
    recognized && !restricted && acquisition == "ACQUIRED" && access.starts_with("public_direct")
}

fn read_benchmark_lock(root: &Path) -> Result<(BenchmarkLockV1, Vec<u8>, String)> {
    let path = root.join(BENCHMARK_LOCK_PATH);
    let bytes = fs::read(&path).with_context(|| format!("reading {}", path.display()))?;
    let value = amphora_core::parse_json_strict(&bytes)?;
    let lock: BenchmarkLockV1 = serde_json::from_value(value)?;
    Ok((lock, bytes, BENCHMARK_LOCK_PATH.into()))
}

fn read_module_benchmark_lock(
    root: &Path,
    module: &str,
) -> Result<(BenchmarkLockV1, Vec<u8>, String)> {
    let (_, _, lock_path) = module_paths(module)?;
    let bytes = fs::read(root.join(lock_path))?;
    let lock: BenchmarkLockV1 = serde_json::from_value(amphora_core::parse_json_strict(&bytes)?)?;
    if lock.module_id != module {
        bail!("benchmark lock module identity mismatch for {module}");
    }
    Ok((lock, bytes, lock_path.into()))
}

fn lock_module_benchmark(root: &Path, module: &str, output: Option<&Path>) -> Result<()> {
    if is_scientific_model_module(module) {
        return lock_scientific_model_benchmark(root, module, output);
    }
    let (lock, bytes, path) = read_module_benchmark_lock(root, module)?;
    lock.validate()?;
    verify_lock_parents(root, &lock)?;
    if let Some(output) = output {
        let output = if output.is_absolute() {
            output.to_path_buf()
        } else {
            root.join(output)
        };
        persist_immutable(&output, &bytes)?;
    }
    let receipt = module_control_receipt(
        root,
        module,
        &format!("benchmark lock --module {module}"),
        true,
        EvidenceTier::SyntheticDiagnostic,
        DecisionUse::AuditOnly,
        BTreeMap::from([(path, raw_sha256(&bytes))]),
        json!({
            "benchmark_id": lock.benchmark_id,
            "dataset_parent_count": lock.dataset_hashes.len(),
            "split_hash": lock.split_hash,
            "lock_valid": true,
            "models_have_not_run_before_lock": true,
        }),
    )?;
    emit_jsonl(&serde_json::to_value(receipt)?)
}

fn lock_scientific_model_benchmark(root: &Path, module: &str, output: Option<&Path>) -> Result<()> {
    let (_, _, lock_path) = module_paths(module)?;
    let bytes = fs::read(root.join(lock_path))?;
    let value = amphora_core::parse_json_strict(&bytes)?;
    let (schema, benchmark_id) =
        preflight_model_value(module, ModelPreflightKind::BenchmarkLock, value.clone())?;
    verify_scientific_lock_parents(root, module, &value)?;
    if let Some(output) = output {
        let output = if output.is_absolute() {
            output.to_path_buf()
        } else {
            root.join(output)
        };
        persist_immutable(&output, &bytes)?;
    }
    let receipt = module_control_receipt(
        root,
        module,
        &format!("benchmark lock --module {module}"),
        true,
        EvidenceTier::SyntheticDiagnostic,
        DecisionUse::AuditOnly,
        BTreeMap::from([(lock_path.into(), raw_sha256(&bytes))]),
        json!({
            "benchmark_id": benchmark_id,
            "contract_schema": schema,
            "lock_valid": true,
            "models_have_not_run_before_lock": true,
            "promotion_data_present": false,
        }),
    )?;
    emit_jsonl(&serde_json::to_value(receipt)?)
}

fn verify_scientific_lock_parents(root: &Path, module: &str, lock: &Value) -> Result<()> {
    let (source_path, split_path, _) = module_paths(module)?;
    let census = read_json(&root.join(source_path))?;
    let local_manifest = census
        .pointer("/sources/0/local_manifest")
        .and_then(Value::as_str)
        .ok_or_else(|| anyhow!("model source census has no local source landscape"))?;
    let dataset_hash = required_str(lock, "dataset_sha256")?;
    let split_hash = required_str(lock, "split_sha256")?;
    if raw_file_sha256(&root.join(local_manifest))? != dataset_hash
        || raw_file_sha256(&root.join(split_path))? != split_hash
    {
        bail!("scientific benchmark lock parent hash mismatch for {module}");
    }
    let split_value = read_json(&root.join(split_path))?;
    preflight_model_value(module, ModelPreflightKind::Split, split_value)?;
    Ok(())
}

fn verify_lock_parents(root: &Path, lock: &BenchmarkLockV1) -> Result<()> {
    for (path, expected) in &lock.dataset_hashes {
        let observed = raw_file_sha256(&root.join(path))?;
        if &observed != expected {
            bail!("benchmark lock parent hash mismatch for {path}");
        }
    }
    Ok(())
}

fn run_locked_module_benchmark(root: &Path, module: &str) -> Result<()> {
    if is_scientific_model_module(module) {
        return run_locked_scientific_model_benchmark(root, module);
    }
    let (lock, lock_bytes, lock_path) = read_module_benchmark_lock(root, module)?;
    lock.validate()?;
    verify_lock_parents(root, &lock)?;
    let (_, split_path, _) = module_paths(module)?;
    let split: SplitManifestV1 = serde_json::from_value(read_json(&root.join(split_path))?)?;
    split.validate()?;
    if raw_file_sha256(&root.join(split_path))? != lock.split_hash {
        bail!("split manifest hash does not match locked split for {module}");
    }
    let audit = audit_module_data(root, module)?;
    if !audit.integrity_valid() {
        bail!("cannot run locked benchmark with invalid source artifacts");
    }
    let mut artifact_hashes = audit.artifact_hashes.clone();
    let result = match module {
        CORROSION_MODULE => {
            let lift = read_json(&root.join(CORROSION_LIFT_PATH))?;
            artifact_hashes.insert(
                CORROSION_LIFT_PATH.into(),
                raw_file_sha256(&root.join(CORROSION_LIFT_PATH))?,
            );
            corrosion_benchmark_result(&audit, &split, &lift)?
        }
        CURE_MODULE => {
            let lift = read_json(&root.join(CURE_LIFT_PATH))?;
            artifact_hashes.insert(
                CURE_LIFT_PATH.into(),
                raw_file_sha256(&root.join(CURE_LIFT_PATH))?,
            );
            cure_benchmark_result(&audit, &split, &lift)?
        }
        MOLECULE_PROPERTY_MODULE => {
            let benchmark = read_json(&root.join(MOLECULE_PROPERTY_BENCHMARK_PATH))?;
            molecule_property_benchmark_result(&audit, &split, &benchmark)?
        }
        MOLECULE_ROLE_MODULE => {
            let benchmark = read_json(&root.join(MOLECULE_ROLE_BENCHMARK_PATH))?;
            molecule_role_benchmark_result(&audit, &split, &benchmark)?
        }
        _ => bail!("unsupported locked benchmark module: {module}"),
    };
    artifact_hashes.insert(lock_path, raw_sha256(&lock_bytes));
    artifact_hashes.insert(split_path.into(), raw_file_sha256(&root.join(split_path))?);
    let mut receipt = new_module_receipt(
        root,
        module,
        &format!("benchmark run --locked --module {module}"),
        result.passed,
        EvidenceTier::PublicRetrospective,
        if result.passed {
            DecisionUse::Shadow
        } else {
            DecisionUse::AuditOnly
        },
        artifact_hashes,
        result.details.clone(),
    )?;
    receipt.metrics.extend(result.metrics);
    receipt.confidence_intervals = result.confidence_intervals;
    if !read_only_command() {
        let identity = ensure_local_identity(root)?;
        receipt.metrics.insert(
            "source_genesis_hash".into(),
            Value::String(identity.genesis_hash.clone()),
        );
        bind_receipt_identity(&mut receipt)?;
        receipt.sign(&identity.key_id, &identity.signing_key)?;
        persist_receipt(root, &receipt)?;
    }
    emit_jsonl(&serde_json::to_value(receipt)?)
}

fn run_locked_scientific_model_benchmark(root: &Path, module: &str) -> Result<()> {
    let (_, split_path, lock_path) = module_paths(module)?;
    let lock_bytes = fs::read(root.join(lock_path))?;
    let lock_value = amphora_core::parse_json_strict(&lock_bytes)?;
    let (_, benchmark_id) = preflight_model_value(
        module,
        ModelPreflightKind::BenchmarkLock,
        lock_value.clone(),
    )?;
    verify_scientific_lock_parents(root, module, &lock_value)?;
    let audit = audit_module_data(root, module)?;
    if !audit.integrity_valid() {
        bail!("cannot run locked benchmark with invalid source artifacts");
    }
    let mut artifact_hashes = audit.artifact_hashes;
    artifact_hashes.insert(lock_path.into(), raw_sha256(&lock_bytes));
    artifact_hashes.insert(split_path.into(), raw_file_sha256(&root.join(split_path))?);
    let receipt = module_control_receipt(
        root,
        module,
        &format!("benchmark run --locked --module {module}"),
        false,
        EvidenceTier::PublicRetrospective,
        DecisionUse::AuditOnly,
        artifact_hashes,
        json!({
            "benchmark_id": benchmark_id,
            "locked_gate_passed": false,
            "automatic_demotion": true,
            "reason": "owned promotion dataset, external systems, and independent review are absent",
            "eligible_scientific_rows": audit.eligible_rows,
            "hostile_nulls": "LOCKED_NOT_EXECUTED_WITHOUT_ELIGIBLE_ENDPOINT_DATA",
            "numeric_production_output_authorized": false,
            "synthetic_fixtures_inventoried_as_scientific_evidence": false,
        }),
    )?;
    emit_jsonl(&serde_json::to_value(receipt)?)
}

fn replay_module_benchmark_receipt(root: &Path, module: &str) -> Result<Value> {
    let (_, lock_bytes, _) = read_module_benchmark_lock(root, module)?;
    let current_lock_hash = raw_sha256(&lock_bytes);
    let current_registry_hash = raw_file_sha256(&root.join(REGISTRY_PATH))?;
    let command = format!("benchmark run --locked --module {module}");
    let receipts = load_local_receipts(root)?;
    let receipt = receipts
        .iter()
        .rev()
        .find(|receipt| {
            receipt.module_id == module
                && receipt.metrics.get("command").and_then(Value::as_str) == Some(command.as_str())
        })
        .ok_or_else(|| anyhow!("no locked benchmark receipt available for {module}"))?;
    let identity = ensure_local_identity(root)?;
    let mut trust = TrustStore::default();
    trust.insert(
        identity.key_id.clone(),
        identity.signing_key.verifying_key().to_bytes(),
    )?;
    let signature_verified = receipt.verify_signature(&trust).is_ok();
    let registry_current = receipt.registry_manifest_hash == current_registry_hash;
    let lock_current = receipt.benchmark_lock_hash == current_lock_hash;
    let mut stale_artifacts = Vec::new();
    for (path, expected_hash) in &receipt.artifact_hashes {
        let artifact = root.join(path);
        if !artifact.is_file()
            || raw_file_sha256(&artifact).ok().as_deref() != Some(expected_hash.as_str())
        {
            stale_artifacts.push(path.clone());
        }
    }
    let current =
        signature_verified && registry_current && lock_current && stale_artifacts.is_empty();
    Ok(json!({
        "schema": "amphora.benchmark-replay.v1",
        "module_id": module,
        "receipt_id": receipt.receipt_id,
        "receipt_passed": receipt.passed,
        "signature_verified": signature_verified,
        "registry_current": registry_current,
        "benchmark_lock_current": lock_current,
        "artifact_hashes_current": stale_artifacts.is_empty(),
        "stale_artifacts": stale_artifacts,
        "replay_status": if current { "CURRENT" } else { "DEMOTED_STALE_OR_MISMATCHED" },
        "effective_phase": if current && receipt.passed { "PHASE_1" } else { "PHASE_0" },
        "effective_decision_use": if current && receipt.passed {
            serde_json::to_value(receipt.decision_use_ceiling)?
        } else {
            serde_json::to_value(DecisionUse::AuditOnly)?
        }
    }))
}

fn is_scientific_model_module(module: &str) -> bool {
    [VISCOSITY_MODULE, SOLVENCY_MODULE, EIS_CORROSION_MODULE].contains(&module)
}

struct LockedBenchmarkResult {
    passed: bool,
    metrics: BTreeMap<String, Value>,
    confidence_intervals: BTreeMap<String, ConfidenceIntervalV1>,
    details: Value,
}

fn corrosion_benchmark_result(
    audit: &ModuleDataAudit,
    split: &SplitManifestV1,
    lift: &Value,
) -> Result<LockedBenchmarkResult> {
    let model_metric = required_f64(lift, "model_metric")?;
    let baseline_metric = required_f64(lift, "baseline_metric")?;
    let absolute_lift = required_f64(lift, "absolute_lift")?;
    let ci = lift
        .pointer("/confidence_summary/confidence_interval_95")
        .ok_or_else(|| anyhow!("corrosion lift audit has no confidence interval"))?;
    let ci_lower = required_f64(ci, "lower")?;
    let ci_upper = required_f64(ci, "upper")?;
    let external_systems = split
        .assignments
        .iter()
        .filter(|row| row.split == "SEALED_EXTERNAL_HOLDOUT")
        .map(|row| (row.source.as_str(), row.scaffold.as_str()))
        .collect::<BTreeSet<_>>()
        .len();
    let leakage_count = split_leakage_count(split);
    let calibration_error = first_finite_f64(
        lift,
        &[
            "/calibration_error",
            "/calibration_summary/expected_calibration_error",
        ],
    );
    let rust_creep_error_delta = first_finite_f64(
        lift,
        &[
            "/rust_creep_error_delta",
            "/continuous_endpoint_results/rust_creep/error_delta",
        ],
    );
    let wet_adhesion_error_delta = first_finite_f64(
        lift,
        &[
            "/wet_adhesion_error_delta",
            "/continuous_endpoint_results/wet_adhesion/error_delta",
        ],
    );
    let model_suite_complete = corrosion_model_suite_complete(lift);
    let hostile_null_suite_complete = hostile_null_suite_complete(lift);
    let independent_review_returned = independent_corrosion_review_complete(lift);
    let gates = BTreeMap::from([
        (
            "minimum_30_independent_systems",
            audit.eligible_systems.len() >= 30,
        ),
        ("minimum_3_studies", audit.eligible_studies.len() >= 3),
        ("minimum_10_sealed_external_systems", external_systems >= 10),
        ("zero_source_or_system_leakage", leakage_count == 0),
        (
            "balanced_accuracy_lift_at_least_0_10",
            absolute_lift >= 0.10,
        ),
        ("paired_study_block_ci_lower_above_zero", ci_lower > 0.0),
        (
            "calibration_error_at_most_0_10",
            calibration_error.is_some_and(|value| value <= 0.10),
        ),
        (
            "continuous_endpoint_errors_non_worse",
            rust_creep_error_delta.is_some_and(|value| value <= 0.0)
                && wet_adhesion_error_delta.is_some_and(|value| value <= 0.0),
        ),
        (
            "locked_model_and_hostile_null_suite_complete",
            model_suite_complete && hostile_null_suite_complete,
        ),
        (
            "independent_expert_review_returned",
            independent_review_returned,
        ),
    ]);
    let failed_gates = gates
        .iter()
        .filter_map(|(gate, passed)| (!passed).then_some(*gate))
        .collect::<Vec<_>>();
    let passed = failed_gates.is_empty();
    let metrics = BTreeMap::from([
        ("program_version".into(), Value::String("phase-acceleration-v1".into())),
        ("phase".into(), Value::String(if passed { "PHASE_1" } else { "PHASE_0" }.into())),
        ("authority_ceiling".into(), Value::String(if passed { "SHADOW" } else { "AUDIT_ONLY" }.into())),
        ("independent_system_count".into(), json!(audit.eligible_systems.len())),
        ("study_count".into(), json!(audit.eligible_studies.len())),
        ("untouched_external_system_count".into(), json!(external_systems)),
        ("source_or_system_leakage_count".into(), json!(leakage_count)),
        ("balanced_accuracy".into(), json!(model_metric)),
        ("best_baseline_balanced_accuracy".into(), json!(baseline_metric)),
        ("balanced_accuracy_lift".into(), json!(absolute_lift)),
        ("calibration_error".into(), optional_number(calibration_error)),
        ("rust_creep_error_delta".into(), optional_number(rust_creep_error_delta)),
        ("wet_adhesion_error_delta".into(), optional_number(wet_adhesion_error_delta)),
        ("reported_raw_rows".into(), json!(audit.reported_rows)),
        ("eligible_raw_rows".into(), json!(audit.eligible_rows)),
        ("failed_gates".into(), json!(failed_gates)),
        ("candidate_performance_authorized".into(), Value::Bool(false)),
        ("model_suite_complete".into(), Value::Bool(model_suite_complete)),
        ("expert_review_status".into(), Value::String(if independent_review_returned { "VERIFIED_RETURNED" } else { "NOT_VERIFIED" }.into())),
        ("hostile_null_suite_status".into(), Value::String(if hostile_null_suite_complete { "COMPLETE_ALL_REQUIRED_NULLS_REJECTED" } else { "INCOMPLETE_OR_NOT_AVAILABLE" }.into())),
        ("next_evidence_changing_action".into(), Value::String("Acquire and rights-clear USBR 19168, 22014, and 23016; then create at least ten untouched study/system holdouts before rerunning the frozen benchmark.".into())),
    ]);
    Ok(LockedBenchmarkResult {
        passed,
        metrics,
        confidence_intervals: BTreeMap::from([(
            "balanced_accuracy_lift".into(),
            ConfidenceIntervalV1 {
                lower: ci_lower,
                upper: ci_upper,
                confidence: 0.95,
                method: ci
                    .get("method")
                    .and_then(Value::as_str)
                    .unwrap_or("exact_sign_permutation")
                    .into(),
            },
        )]),
        details: json!({
            "gates": gates,
            "endpoint_counts": audit.endpoint_counts,
            "calculated_gate_inputs": {
                "calibration_error": calibration_error,
                "rust_creep_error_delta": rust_creep_error_delta,
                "wet_adhesion_error_delta": wet_adhesion_error_delta,
                "model_suite_complete": model_suite_complete,
                "hostile_null_suite_complete": hostile_null_suite_complete,
                "independent_review_verified": independent_review_returned,
                "source_or_system_leakage_count": leakage_count
            },
            "single_frequency_eis_only": true,
            "kramers_kronig_and_equivalent_circuit_status": "ABSTAINED",
            "phase_1_claimed": passed,
            "public_evidence_decision_use_maximum": "SHADOW",
        }),
    })
}

fn first_finite_f64(value: &Value, pointers: &[&str]) -> Option<f64> {
    pointers
        .iter()
        .find_map(|pointer| value.pointer(pointer).and_then(Value::as_f64))
        .filter(|value| value.is_finite())
}

fn optional_number(value: Option<f64>) -> Value {
    value.map_or(Value::Null, |value| json!(value))
}

fn corrosion_model_suite_complete(lift: &Value) -> bool {
    const REQUIRED_MODELS: [&str; 5] = [
        "majority_or_constant",
        "latest_impedance_expert_threshold",
        "monotone_log_linear_degradation",
        "deterministic_gam",
        "deterministic_boosted_stumps",
    ];
    let available = lift
        .get("model_registry")
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
        .filter_map(Value::as_str)
        .collect::<BTreeSet<_>>();
    REQUIRED_MODELS
        .iter()
        .all(|model| available.contains(model))
}

fn hostile_null_suite_complete(lift: &Value) -> bool {
    const REQUIRED_NULLS: [&str; 3] = [
        "label_shuffle_null",
        "time_reversal_null",
        "source_and_system_leakage_null",
    ];
    let results = lift
        .pointer("/hostile_null_suite/results")
        .or_else(|| lift.get("hostile_null_results"))
        .and_then(Value::as_array);
    let Some(results) = results else {
        return false;
    };
    REQUIRED_NULLS.iter().all(|required| {
        results.iter().any(|result| {
            result.get("name").and_then(Value::as_str) == Some(*required)
                && (result.get("rejected").and_then(Value::as_bool) == Some(true)
                    || result.get("status").and_then(Value::as_str) == Some("REJECTED"))
                && result.get("leakage_detected").and_then(Value::as_bool) != Some(true)
        })
    })
}

fn independent_corrosion_review_complete(lift: &Value) -> bool {
    let Some(review) = lift.get("independent_review") else {
        return false;
    };
    matches!(
        review.get("status").and_then(Value::as_str),
        Some("ACCEPTED" | "RETURNED")
    ) && review.get("signature_verified").and_then(Value::as_bool) == Some(true)
        && review.get("identity_bound").and_then(Value::as_bool) == Some(true)
        && review.get("benchmark_hash_bound").and_then(Value::as_bool) == Some(true)
        && review.get("reviewer_independent").and_then(Value::as_bool) == Some(true)
}

fn molecule_property_benchmark_result(
    audit: &ModuleDataAudit,
    split: &SplitManifestV1,
    benchmark: &Value,
) -> Result<LockedBenchmarkResult> {
    let backend = amphora_rdkit_ffi::backend_status();
    let exact = benchmark
        .get("exact_implementation_checks")
        .and_then(Value::as_array)
        .ok_or_else(|| anyhow!("property benchmark has no exact implementation checks"))?;
    let negative = benchmark
        .get("negative_controls")
        .and_then(Value::as_array)
        .ok_or_else(|| anyhow!("property benchmark has no negative controls"))?;
    let measured = benchmark
        .get("technical_grade_lower_bound_records")
        .and_then(Value::as_array)
        .ok_or_else(|| anyhow!("property benchmark has no measured-only annex"))?;
    let mut evaluated = 0_u64;
    let mut reactive_counts_correct = true;
    let mut identity_and_mass_correct = true;
    let mut max_equivalent_weight_error = 0.0_f64;
    for control in exact {
        let smiles = required_str(control, "smiles")?;
        let expected = control
            .get("expected")
            .ok_or_else(|| anyhow!("property exact control has no expected result"))?;
        let Ok(facts) = amphora_rdkit_ffi::molecule_facts(smiles) else {
            reactive_counts_correct = false;
            identity_and_mass_correct = false;
            continue;
        };
        evaluated += 1;
        let expected_oxirane = expected
            .get("epoxide_groups")
            .and_then(Value::as_u64)
            .ok_or_else(|| anyhow!("property control has no epoxide count"))?;
        let expected_amine_h = expected
            .get("active_nh")
            .and_then(Value::as_u64)
            .ok_or_else(|| anyhow!("property control has no active N-H count"))?;
        reactive_counts_correct &= u64::from(facts.oxirane_ring_count) == expected_oxirane
            && u64::from(facts.reactive_amine_hydrogen_count) == expected_amine_h;
        let expected_mass = required_f64(expected, "mol_weight")?;
        identity_and_mass_correct &=
            (facts.average_molecular_weight_g_mol - expected_mass).abs() <= 0.5;
        if let Some(formula) = expected.get("formula").and_then(Value::as_str) {
            identity_and_mass_correct &= facts.formula == formula;
        }
        if let Some(expected_eew) = expected.get("eew_g_per_eq").and_then(Value::as_f64) {
            if facts.oxirane_ring_count == 0 {
                reactive_counts_correct = false;
            } else {
                let observed =
                    facts.average_molecular_weight_g_mol / f64::from(facts.oxirane_ring_count);
                max_equivalent_weight_error =
                    max_equivalent_weight_error.max((observed - expected_eew).abs());
            }
        }
        if let Some(expected_ahew) = expected.get("ahew_g_per_eq").and_then(Value::as_f64) {
            if facts.reactive_amine_hydrogen_count == 0 {
                reactive_counts_correct = false;
            } else {
                let observed = facts.average_molecular_weight_g_mol
                    / f64::from(facts.reactive_amine_hydrogen_count);
                max_equivalent_weight_error =
                    max_equivalent_weight_error.max((observed - expected_ahew).abs());
            }
        }
    }
    let invalid_rejection_correct = negative.iter().all(|control| {
        let Some(smiles) = control.get("smiles").and_then(Value::as_str) else {
            return false;
        };
        let expected_parseable = control
            .get("expected_parseable")
            .and_then(Value::as_bool)
            .unwrap_or(false);
        match amphora_rdkit_ffi::molecule_facts(smiles) {
            Ok(facts) if expected_parseable => control
                .get("expected_active_nh")
                .and_then(Value::as_u64)
                .is_none_or(|expected| u64::from(facts.reactive_amine_hydrogen_count) == expected),
            Err(_) if !expected_parseable => true,
            _ => false,
        }
    });
    let measured_only_locks_preserved = !measured.is_empty()
        && measured.iter().all(|control| {
            control.get("claim_lock").and_then(Value::as_str)
                == Some("commercial_product_is_measured_only")
        });
    let sealed_controls = split
        .assignments
        .iter()
        .filter(|row| row.split == "SEALED_CONTROL")
        .count();
    let independent_reference_bound =
        benchmark
            .get("independent_toolkit_receipt")
            .is_some_and(|receipt| {
                receipt.get("signature_verified").and_then(Value::as_bool) == Some(true)
                    && receipt.get("benchmark_hash_bound").and_then(Value::as_bool) == Some(true)
            });
    let gates = BTreeMap::from([
        ("pinned_rdkit_2026_03_2_available", backend.available),
        (
            "all_exact_controls_executed",
            evaluated as usize == exact.len() && !exact.is_empty(),
        ),
        ("reactive_group_counts_100_percent", reactive_counts_correct),
        (
            "invalid_and_out_of_domain_rejection_100_percent",
            invalid_rejection_correct,
        ),
        (
            "equivalent_weight_max_abs_error_at_most_0_5",
            evaluated > 0 && max_equivalent_weight_error <= 0.5,
        ),
        (
            "structure_identity_and_mass_agree",
            identity_and_mass_correct,
        ),
        (
            "independent_reference_receipt_bound",
            independent_reference_bound,
        ),
        (
            "minimum_300_truth_set_molecules",
            audit.eligible_rows >= 300,
        ),
        (
            "sealed_controls_present",
            sealed_controls >= exact.len() + negative.len(),
        ),
        (
            "measured_only_claim_locks_preserved",
            measured_only_locks_preserved,
        ),
    ]);
    locked_molecule_result(
        gates,
        BTreeMap::from([
            ("backend_status".into(), serde_json::to_value(backend)?),
            ("exact_control_count".into(), json!(exact.len())),
            ("exact_controls_executed".into(), json!(evaluated)),
            ("negative_control_count".into(), json!(negative.len())),
            ("sealed_control_count".into(), json!(sealed_controls)),
            ("truth_set_eligible_count".into(), json!(audit.eligible_rows)),
            (
                "max_abs_eew_ahew_error_g_per_eq".into(),
                if evaluated > 0 {
                    json!(max_equivalent_weight_error)
                } else {
                    Value::Null
                },
            ),
            ("commercial_product_values_measured_only".into(), Value::Bool(true)),
        ]),
        "Deterministic molecule properties remain constraints and audit evidence; no optimizer objective or commercial-grade inference is authorized.",
    )
}

fn molecule_role_benchmark_result(
    audit: &ModuleDataAudit,
    split: &SplitManifestV1,
    benchmark: &Value,
) -> Result<LockedBenchmarkResult> {
    let backend = amphora_rdkit_ffi::backend_status();
    let exact = benchmark
        .get("exact_defined_controls")
        .and_then(Value::as_array)
        .ok_or_else(|| anyhow!("role benchmark has no exact controls"))?;
    let measured = benchmark
        .get("measured_only_commercial_controls")
        .and_then(Value::as_array)
        .ok_or_else(|| anyhow!("role benchmark has no measured-only controls"))?;
    let mut evaluated = 0_usize;
    let mut confusion: BTreeMap<(String, String), u64> = BTreeMap::new();
    for control in exact {
        let expected = required_str(control, "expected_role")?;
        let smiles = required_str(control, "smiles")?;
        let Ok(facts) = amphora_rdkit_ffi::molecule_facts(smiles) else {
            continue;
        };
        evaluated += 1;
        let predicted = structural_role(&facts).to_owned();
        *confusion.entry((expected.into(), predicted)).or_default() += 1;
    }
    let (balanced_accuracy, macro_f1, ece) = if evaluated == exact.len() && evaluated > 0 {
        let recalls = ["resin", "hardener"].map(|class| {
            let correct = confusion
                .get(&(class.into(), class.into()))
                .copied()
                .unwrap_or(0) as f64;
            let total = confusion
                .iter()
                .filter(|((actual, _), _)| actual == class)
                .map(|(_, count)| *count)
                .sum::<u64>() as f64;
            (total > 0.0).then_some(correct / total)
        });
        let f1s = ["resin", "hardener"].map(|class| {
            let true_positive = confusion
                .get(&(class.into(), class.into()))
                .copied()
                .unwrap_or(0) as f64;
            let predicted = confusion
                .iter()
                .filter(|((_, prediction), _)| prediction == class)
                .map(|(_, count)| *count)
                .sum::<u64>() as f64;
            let actual = confusion
                .iter()
                .filter(|((label, _), _)| label == class)
                .map(|(_, count)| *count)
                .sum::<u64>() as f64;
            let denominator = predicted + actual;
            (denominator > 0.0).then_some(2.0 * true_positive / denominator)
        });
        let correct = confusion
            .iter()
            .filter(|((actual, predicted), _)| actual == predicted)
            .map(|(_, count)| *count)
            .sum::<u64>() as f64;
        (
            recalls
                .into_iter()
                .collect::<Option<Vec<_>>>()
                .map(|rows| rows.iter().sum::<f64>() / rows.len() as f64),
            f1s.into_iter()
                .collect::<Option<Vec<_>>>()
                .map(|rows| rows.iter().sum::<f64>() / rows.len() as f64),
            Some(1.0 - correct / evaluated as f64),
        )
    } else {
        (None, None, None)
    };
    let rejection_controls = benchmark
        .get("ambiguous_out_of_domain_controls")
        .and_then(Value::as_array);
    let rejection_rate = rejection_controls.and_then(|controls| {
        if controls.is_empty() {
            return None;
        }
        let rejected = controls
            .iter()
            .filter(|control| {
                control
                    .get("smiles")
                    .and_then(Value::as_str)
                    .and_then(|smiles| amphora_rdkit_ffi::molecule_facts(smiles).ok())
                    .is_some_and(|facts| {
                        matches!(structural_role(&facts), "ambiguous" | "out_of_domain")
                    })
            })
            .count();
        Some(rejected as f64 / controls.len() as f64)
    });
    let measured_only_locks_preserved = !measured.is_empty()
        && measured.iter().all(|control| {
            control.get("source_status").and_then(Value::as_str) == Some("MEASURED_PRODUCT_ONLY")
                && control.get("structure_authority").and_then(Value::as_str)
                    == Some("MEASURED_ONLY")
        });
    let independent_labels_bound =
        benchmark
            .get("independent_label_receipt")
            .is_some_and(|receipt| {
                receipt.get("signature_verified").and_then(Value::as_bool) == Some(true)
                    && receipt
                        .get("adjudicated_before_unblinding")
                        .and_then(Value::as_bool)
                        == Some(true)
            });
    let noninferiority = benchmark
        .pointer("/expert_noninferiority/lower_bound")
        .and_then(Value::as_f64)
        .filter(|value| value.is_finite());
    let sealed_holdout_count = split
        .assignments
        .iter()
        .filter(|row| row.split == "SEALED_HOLDOUT")
        .count();
    let gates = BTreeMap::from([
        ("pinned_rdkit_2026_03_2_available", backend.available),
        (
            "minimum_300_truth_set_molecules",
            audit.eligible_rows >= 300,
        ),
        ("sealed_holdout_present", sealed_holdout_count > 0),
        ("independent_double_labels_bound", independent_labels_bound),
        (
            "balanced_accuracy_at_least_0_90",
            balanced_accuracy.is_some_and(|value| value >= 0.90),
        ),
        (
            "macro_f1_at_least_0_90",
            macro_f1.is_some_and(|value| value >= 0.90),
        ),
        (
            "expert_noninferiority_margin_0_05",
            noninferiority.is_some_and(|value| value >= -0.05),
        ),
        (
            "expected_calibration_error_at_most_0_10",
            ece.is_some_and(|value| value <= 0.10),
        ),
        (
            "ambiguous_out_of_domain_rejection_at_least_0_95",
            rejection_rate.is_some_and(|value| value >= 0.95),
        ),
        (
            "measured_only_claim_locks_preserved",
            measured_only_locks_preserved,
        ),
    ]);
    locked_molecule_result(
        gates,
        BTreeMap::from([
            ("backend_status".into(), serde_json::to_value(backend)?),
            ("exact_control_count".into(), json!(exact.len())),
            ("exact_controls_executed".into(), json!(evaluated)),
            ("truth_set_eligible_count".into(), json!(audit.eligible_rows)),
            ("sealed_holdout_count".into(), json!(sealed_holdout_count)),
            ("balanced_accuracy".into(), optional_number(balanced_accuracy)),
            ("macro_f1".into(), optional_number(macro_f1)),
            ("expected_calibration_error".into(), optional_number(ece)),
            ("ambiguous_out_of_domain_rejection".into(), optional_number(rejection_rate)),
            ("commercial_product_values_measured_only".into(), Value::Bool(true)),
        ]),
        "Role tracks remain audit-only; role_fit requires a current identity-bound Phase-1 receipt and an explicit unambiguous role.",
    )
}

fn structural_role(facts: &amphora_rdkit_ffi::MoleculeFactsV1) -> &'static str {
    match (
        facts.reactive_flags.has_oxirane,
        facts.reactive_flags.has_reactive_amine_hydrogen,
    ) {
        (true, false) => "resin",
        (false, true) => "hardener",
        (true, true) => "ambiguous",
        (false, false) => "out_of_domain",
    }
}

fn locked_molecule_result(
    gates: BTreeMap<&'static str, bool>,
    mut metrics: BTreeMap<String, Value>,
    claim_boundary: &str,
) -> Result<LockedBenchmarkResult> {
    let failed_gates = gates
        .iter()
        .filter_map(|(gate, passed)| (!passed).then_some(*gate))
        .collect::<Vec<_>>();
    let passed = failed_gates.is_empty();
    metrics.extend([
        (
            "phase".into(),
            Value::String(if passed { "PHASE_1" } else { "PHASE_0" }.into()),
        ),
        ("failed_gates".into(), json!(failed_gates)),
        ("automatic_demotion".into(), Value::Bool(!passed)),
        (
            "claim_boundary".into(),
            Value::String(claim_boundary.into()),
        ),
    ]);
    Ok(LockedBenchmarkResult {
        passed,
        metrics,
        confidence_intervals: BTreeMap::new(),
        details: json!({
            "gates": gates,
            "phase_1_claimed": passed,
            "promotion_requires_hash_bound_signed_review": true,
        }),
    })
}

fn cure_benchmark_result(
    audit: &ModuleDataAudit,
    split: &SplitManifestV1,
    lift: &Value,
) -> Result<LockedBenchmarkResult> {
    let model_metric = required_f64(lift, "model_metric")?;
    let baseline_metric = required_f64(lift, "baseline_metric")?;
    let absolute_lift = required_f64(lift, "absolute_lift")?;
    let ci = lift
        .pointer("/confidence_summary/confidence_interval_95")
        .ok_or_else(|| anyhow!("cure lift audit has no confidence interval"))?;
    let ci_lower = required_f64(ci, "lower")?;
    let ci_upper = required_f64(ci, "upper")?;
    let holdouts = split
        .assignments
        .iter()
        .filter(|row| row.split == "EXTERNAL_HOLDOUT")
        .count();
    let eligible_publishers = audit.eligible_sources;
    let gates = BTreeMap::from([
        (
            "minimum_50_complete_gel_time_rows",
            audit.eligible_rows >= 50,
        ),
        ("minimum_3_publishers", eligible_publishers >= 3),
        (
            "minimum_10_untouched_source_family_holdouts",
            holdouts >= 10,
        ),
        (
            "fraction_within_factor_1_5_at_least_0_80",
            model_metric >= 0.80,
        ),
        ("absolute_lift_at_least_0_10", absolute_lift >= 0.10),
        ("paired_confidence_lower_above_zero", ci_lower > 0.0),
        ("interval_90_coverage_between_0_85_and_0_95", false),
        ("locked_model_and_hostile_null_suite_complete", false),
        ("independent_expert_review_returned", false),
    ]);
    let failed_gates = gates
        .iter()
        .filter_map(|(gate, passed)| (!passed).then_some(*gate))
        .collect::<Vec<_>>();
    let passed = failed_gates.is_empty();
    let metrics = BTreeMap::from([
        ("program_version".into(), Value::String("phase-acceleration-v1".into())),
        ("phase".into(), Value::String(if passed { "PHASE_1" } else { "PHASE_0" }.into())),
        ("authority_ceiling".into(), Value::String(if passed { "SHADOW" } else { "AUDIT_ONLY" }.into())),
        ("reported_supplier_rows".into(), json!(audit.reported_rows)),
        ("eligible_condition_specific_gel_time_rows".into(), json!(audit.eligible_rows)),
        ("eligible_publisher_count".into(), json!(eligible_publishers)),
        ("untouched_source_family_holdout_count".into(), json!(holdouts)),
        ("fraction_within_factor_1_5".into(), json!(model_metric)),
        ("best_baseline_fraction_within_factor_1_5".into(), json!(baseline_metric)),
        ("absolute_lift".into(), json!(absolute_lift)),
        ("interval_90_coverage".into(), Value::Null),
        ("candidate_pot_life_prediction_h".into(), Value::Null),
        ("failed_gates".into(), json!(failed_gates)),
        ("expert_review_status".into(), Value::String("NOT_SENT_APPROVAL_REQUIRED".into())),
        ("hostile_null_suite_status".into(), Value::String("NOT_AVAILABLE_IN_CURRENT_AUDIT".into())),
        ("next_evidence_changing_action".into(), Value::String("Obtain derivative-use eligibility and measured resin/hardener/mix-ratio/temperature/test-mass/method gel-time series from at least three publishers, preserving source/family holdouts.".into())),
    ]);
    Ok(LockedBenchmarkResult {
        passed,
        metrics,
        confidence_intervals: BTreeMap::from([(
            "absolute_lift".into(),
            ConfidenceIntervalV1 {
                lower: ci_lower,
                upper: ci_upper,
                confidence: 0.95,
                method: ci
                    .get("method")
                    .and_then(Value::as_str)
                    .unwrap_or("exact_sign_permutation")
                    .into(),
            },
        )]),
        details: json!({
            "gates": gates,
            "endpoint_policy": ["GEL_TIME", "POT_LIFE", "DRY_HARD_TIME", "THROUGH_CURE_TIME", "DSC_CONVERSION"],
            "gel_time_relabelled_as_pot_life": false,
            "arrhenius_used_without_multi_temperature_series": false,
            "kinetic_model_used_without_dsc_curves": false,
            "phase_1_claimed": passed,
            "public_evidence_decision_use_maximum": "SHADOW",
        }),
    })
}

fn split_leakage_count(split: &SplitManifestV1) -> usize {
    let mut by_group: BTreeMap<(&str, &str), BTreeSet<&str>> = BTreeMap::new();
    for row in &split.assignments {
        by_group
            .entry((row.source.as_str(), row.scaffold.as_str()))
            .or_default()
            .insert(row.split.as_str());
    }
    by_group.values().filter(|splits| splits.len() > 1).count()
}

fn required_f64(value: &Value, field: &str) -> Result<f64> {
    value
        .get(field)
        .and_then(Value::as_f64)
        .filter(|value| value.is_finite())
        .ok_or_else(|| anyhow!("required finite numeric field {field} is absent"))
}

fn run_locked_benchmarks(root: &Path) -> Result<()> {
    let (lock, lock_bytes, _) = read_benchmark_lock(root)?;
    lock.validate()?;
    verify_lock_parents(root, &lock)?;
    let lock_hash = raw_sha256(&lock_bytes);
    let registry_bytes = fs::read(root.join(REGISTRY_PATH))?;
    let registry_hash = raw_sha256(&registry_bytes);
    let registry = read_json(&root.join(REGISTRY_PATH))?;
    let inventory = read_json(&root.join(INVENTORY_PATH))?;
    let modules = registry
        .get("modules")
        .and_then(Value::as_array)
        .ok_or_else(|| anyhow!("registry modules are absent"))?;
    let inventory_rows = inventory
        .get("modules")
        .and_then(Value::as_array)
        .ok_or_else(|| anyhow!("evidence inventory modules are absent"))?;
    let inventory_by_id: BTreeMap<_, _> = inventory_rows
        .iter()
        .filter_map(|row| Some((row.get("module_id")?.as_str()?.to_owned(), row)))
        .collect();
    let identity = (!read_only_command())
        .then(|| ensure_local_identity(root))
        .transpose()?;

    for module in modules {
        let module_id = required_str(module, "project")?;
        let inventory = inventory_by_id
            .get(module_id)
            .ok_or_else(|| anyhow!("inventory row missing for {module_id}"))?;
        let mut artifact_hashes = BTreeMap::from([
            (REGISTRY_PATH.into(), registry_hash.clone()),
            (BENCHMARK_LOCK_PATH.into(), lock_hash.clone()),
        ]);
        let mut artifact_integrity = true;
        if let Some(artifacts) = inventory.get("artifacts").and_then(Value::as_array) {
            for artifact in artifacts {
                let Some(path) = artifact.get("path").and_then(Value::as_str) else {
                    artifact_integrity = false;
                    continue;
                };
                let Some(expected) = artifact.get("sha256").and_then(Value::as_str) else {
                    artifact_integrity = false;
                    continue;
                };
                match raw_file_sha256(&root.join(path)) {
                    Ok(observed) if observed == expected => {
                        artifact_hashes.insert(path.into(), observed);
                    }
                    _ => artifact_integrity = false,
                }
            }
        }
        let benchmark = inventory
            .get("current_benchmark")
            .and_then(Value::as_object)
            .ok_or_else(|| anyhow!("current benchmark row missing for {module_id}"))?;
        if let (Some(path), Some(expected)) = (
            benchmark.get("artifact_path").and_then(Value::as_str),
            benchmark.get("artifact_sha256").and_then(Value::as_str),
        ) {
            match raw_file_sha256(&root.join(path)) {
                Ok(observed) if observed == expected => {
                    artifact_hashes.insert(path.into(), observed);
                }
                _ => artifact_integrity = false,
            }
        }
        let readiness = module
            .get("operational_readiness")
            .and_then(Value::as_str)
            .unwrap_or("UNKNOWN");
        let live_diagnostic = LIVE_DETERMINISTIC_CONTROLS
            .contains(&module_id)
            .then(|| amphora_assurance_capabilities::deterministic_control_diagnostic(module_id));
        let live_diagnostic_passed = live_diagnostic
            .as_ref()
            .is_some_and(|diagnostic| diagnostic.as_ref().is_ok_and(|row| row.passed));
        let locked_gate_passed = artifact_integrity
            && matches!(readiness, "COMPLETE" | "READY")
            && (!LIVE_DETERMINISTIC_CONTROLS.contains(&module_id) || live_diagnostic_passed);
        let tier = if benchmark
            .get("artifact_path")
            .is_some_and(|path| !path.is_null())
        {
            EvidenceTier::PublicRetrospective
        } else {
            EvidenceTier::SyntheticDiagnostic
        };
        let ceiling = if locked_gate_passed && COMPUTATIONAL_MODULES.contains(&module_id) {
            DecisionUse::ConstraintOnly
        } else if locked_gate_passed {
            DecisionUse::Shadow
        } else {
            DecisionUse::AuditOnly
        };
        let mut locks = BTreeMap::new();
        for lock in registry
            .pointer("/policy/mandatory_claim_locks")
            .and_then(Value::as_array)
            .into_iter()
            .flatten()
            .chain(
                module
                    .get("non_blocking_claim_locks")
                    .and_then(Value::as_array)
                    .into_iter()
                    .flatten(),
            )
            .filter_map(Value::as_str)
        {
            locks.insert(lock.into(), true);
        }
        let live_diagnostic_value = live_diagnostic
            .as_ref()
            .and_then(|diagnostic| diagnostic.as_ref().ok())
            .map(|diagnostic| serde_json::to_value(diagnostic).expect("diagnostic serializes"));
        let live_diagnostic_error = live_diagnostic
            .as_ref()
            .and_then(|diagnostic| diagnostic.as_ref().err())
            .cloned();
        let mut details = json!({
            "artifact_hash_match": artifact_integrity,
            "registry_identity_match": true,
            "ranking_quarantine_preserved": module.get("ranking_eligible") == Some(&Value::Bool(false)),
            "operational_readiness": readiness,
            "current_benchmark_status": benchmark.get("status"),
            "reported_result_status": benchmark.get("reported_result_status"),
            "locked_gate_passed": locked_gate_passed,
            "observations": benchmark.get("observations"),
            "deterministic_control_diagnostic": live_diagnostic_value,
            "deterministic_control_diagnostic_error": live_diagnostic_error,
        });
        if module_id == "amphora-process-qc-twin" {
            details["process_qc_audit_shell"] =
                serde_json::to_value(process_qc_audit_shell().map_err(|error| anyhow!(error))?)?;
        }
        let mut receipt = new_receipt(
            module_id,
            "benchmark run --locked --all",
            locked_gate_passed,
            tier,
            ceiling,
            registry_hash.clone(),
            lock_hash.clone(),
            artifact_hashes,
            details,
            locks,
            vec![
                "solvent-borne two-component epoxy-polyamide marine coatings".into(),
                "digital evidence only; no product qualification or superiority claim".into(),
            ],
        )?;
        if let Some(identity) = &identity {
            receipt.metrics.insert(
                "source_genesis_hash".into(),
                Value::String(identity.genesis_hash.clone()),
            );
            bind_receipt_identity(&mut receipt)?;
            receipt.sign(&identity.key_id, &identity.signing_key)?;
            persist_receipt(root, &receipt)?;
        }
        emit_jsonl(&serde_json::to_value(receipt)?)?;
    }
    Ok(())
}

fn compare_benchmarks(root: &Path, left_path: &Path, right_path: &Path) -> Result<()> {
    let left_hash = raw_file_sha256(left_path)?;
    let right_hash = raw_file_sha256(right_path)?;
    let left = read_receipt_stream(left_path)?;
    let right = read_receipt_stream(right_path)?;
    let left_by_module: BTreeMap<_, _> = left
        .iter()
        .map(|row| (row.module_id.as_str(), row))
        .collect();
    let right_by_module: BTreeMap<_, _> = right
        .iter()
        .map(|row| (row.module_id.as_str(), row))
        .collect();
    let modules: BTreeSet<_> = left_by_module
        .keys()
        .chain(right_by_module.keys())
        .copied()
        .collect();
    let rows: Vec<_> = modules
        .iter()
        .map(|module| {
            let left = left_by_module.get(module);
            let right = right_by_module.get(module);
            json!({
                "module_id": module,
                "left_passed": left.map(|row| row.passed),
                "right_passed": right.map(|row| row.passed),
                "metrics_equal": match (left, right) {
                    (Some(left), Some(right)) => left.metrics == right.metrics,
                    _ => false,
                },
            })
        })
        .collect();
    let equal = rows.iter().all(|row| {
        row.get("metrics_equal").and_then(Value::as_bool) == Some(true)
            && row.get("left_passed") == row.get("right_passed")
    });
    let receipt = control_receipt(
        root,
        "amphora-known-answer-benchmarks",
        "benchmark compare",
        equal,
        EvidenceTier::SyntheticDiagnostic,
        DecisionUse::AuditOnly,
        BTreeMap::from([
            (left_path_label(left_by_module.len(), "left"), left_hash),
            (left_path_label(right_by_module.len(), "right"), right_hash),
        ]),
        json!({"module_count": modules.len(), "equal": equal, "rows": rows}),
    )?;
    emit_jsonl(&serde_json::to_value(receipt)?)
}

fn left_path_label(count: usize, side: &str) -> String {
    format!("benchmark-{side}-{count}-modules.jsonl")
}

fn portfolio_status(root: &Path, verify_receipts: bool) -> Result<()> {
    let registry = read_json(&root.join(REGISTRY_PATH))?;
    let inventory = read_json(&root.join(INVENTORY_PATH))?;
    let inventory_rows = inventory
        .get("modules")
        .and_then(Value::as_array)
        .ok_or_else(|| anyhow!("evidence inventory modules are absent"))?;
    let inventory_by_id: BTreeMap<_, _> = inventory_rows
        .iter()
        .filter_map(|row| Some((row.get("module_id")?.as_str()?.to_owned(), row)))
        .collect();
    let receipts = load_local_receipts(root)?;
    let identity = ensure_local_identity(root)?;
    let mut trust = TrustStore::default();
    trust.insert(
        &identity.key_id,
        identity.signing_key.verifying_key().to_bytes(),
    )?;
    let mut verified = 0_usize;
    if verify_receipts {
        for receipt in &receipts {
            receipt.verify_signature(&trust)?;
            verified += 1;
        }
    }
    let latest: BTreeMap<_, _> = receipts
        .iter()
        .filter(|receipt| {
            receipt.metrics.get("command").and_then(Value::as_str)
                == Some("benchmark run --locked --all")
        })
        .map(|receipt| (receipt.module_id.as_str(), receipt))
        .collect();
    let rows: Vec<_> = registry
        .get("modules")
        .and_then(Value::as_array)
        .ok_or_else(|| anyhow!("registry modules are absent"))?
        .iter()
        .map(|module| {
            let module_id = module.get("project").and_then(Value::as_str).unwrap_or("unknown");
            let inventory = inventory_by_id.get(module_id);
            let receipt = latest.get(module_id).copied();
            json!({
                "module_id": module_id,
                "evidence_tier": receipt.map(|row| &row.evidence_tier),
                "artifact_hashes": receipt.map(|row| &row.artifact_hashes),
                "current_result": receipt.map(|row| if row.passed { "PASS" } else { "FAIL" }).unwrap_or("NO_RECEIPT"),
                "decision_use_ceiling": receipt.map(|row| row.decision_use_ceiling),
                "operational_readiness": module.get("operational_readiness"),
                "scientific_readiness": module.get("scientific_readiness"),
                "blocker": inventory.and_then(|row| row.pointer("/current_benchmark/gap")),
                "next_feedback": inventory.and_then(|row| row.get("external_dependencies")),
                "claim_locks": receipt.map(|row| &row.claim_locks),
            })
        })
        .collect();
    let event = json!({
        "schema": "amphora.portfolio-status.v1",
        "module_count": rows.len(),
        "receipts_found": receipts.len(),
        "receipts_verified": verified,
        "production_scientific_ranking_enabled": false,
        "modules": rows,
    });
    emit_jsonl(&event)?;
    let receipt = signed_receipt(
        root,
        &identity,
        "amphora-report-packager",
        "portfolio status --verify-receipts",
        rows.len() == 29 && (!verify_receipts || verified == receipts.len()),
        EvidenceTier::SyntheticDiagnostic,
        DecisionUse::AuditOnly,
        BTreeMap::from([
            (
                REGISTRY_PATH.into(),
                raw_file_sha256(&root.join(REGISTRY_PATH))?,
            ),
            (
                INVENTORY_PATH.into(),
                raw_file_sha256(&root.join(INVENTORY_PATH))?,
            ),
        ]),
        json!({"module_count": rows.len(), "verified_receipts": verified}),
    )?;
    emit_jsonl(&serde_json::to_value(receipt)?)
}

fn parse_module_list(value: &str) -> Result<Vec<String>> {
    let mut modules = Vec::new();
    for requested in value
        .split(',')
        .map(str::trim)
        .filter(|value| !value.is_empty())
    {
        let module = match requested {
            "corrosion" | CORROSION_MODULE => CORROSION_MODULE,
            "cure" | CURE_MODULE => CURE_MODULE,
            _ => bail!("unsupported founder-update module: {requested}"),
        };
        if !modules.iter().any(|existing| existing == module) {
            modules.push(module.into());
        }
    }
    if modules.is_empty() {
        bail!("at least one module is required");
    }
    Ok(modules)
}

fn founder_update(
    root: &Path,
    requested_modules: &str,
    verify_receipts: bool,
    format: ReportFormat,
) -> Result<()> {
    let modules = parse_module_list(requested_modules)?;
    let receipts = load_local_receipts(root)?;
    let identity = ensure_local_identity(root)?;
    let mut trust = TrustStore::default();
    trust.insert(
        &identity.key_id,
        identity.signing_key.verifying_key().to_bytes(),
    )?;
    let mut selected = Vec::new();
    for module in &modules {
        let (_, lock_bytes, _) = read_module_benchmark_lock(root, module)?;
        let lock_hash = raw_sha256(&lock_bytes);
        let command = format!("benchmark run --locked --module {module}");
        let receipt = receipts
            .iter()
            .find(|receipt| {
                receipt.module_id == *module
                    && receipt.benchmark_lock_hash == lock_hash
                    && receipt.metrics.get("command").and_then(Value::as_str)
                        == Some(command.as_str())
                    && receipt
                        .metrics
                        .get("program_version")
                        .and_then(Value::as_str)
                        == Some("phase-acceleration-v1")
                    && receipt
                        .metrics
                        .get("source_genesis_hash")
                        .and_then(Value::as_str)
                        == Some(identity.genesis_hash.as_str())
            })
            .ok_or_else(|| {
                anyhow!(
                    "no current locked benchmark receipt for {module}; run benchmark run --locked --module {module}"
                )
            })?;
        if verify_receipts {
            receipt.verify_signature(&trust)?;
        }
        selected.push(receipt.clone());
    }

    let dossier = build_ip_dossier(root, &modules)?;
    let dossier_path = persist_ip_dossier(root, &dossier)?;
    let review_packet_path = seal_expert_review_packet(root, &selected)?;
    let mut artifact_hashes = BTreeMap::from([
        (
            relative_display(root, &dossier_path),
            raw_file_sha256(&dossier_path)?,
        ),
        (
            relative_display(root, &review_packet_path),
            raw_file_sha256(&review_packet_path)?,
        ),
    ]);
    for receipt in &selected {
        let path = root
            .join(".amphora/receipts")
            .join(format!("{}.json", receipt.receipt_id));
        artifact_hashes.insert(relative_display(root, &path), raw_file_sha256(&path)?);
    }
    let all_passed = selected.iter().all(|receipt| receipt.passed);
    let report_markdown = render_founder_markdown(
        &selected,
        verify_receipts,
        &relative_display(root, &dossier_path),
        &relative_display(root, &review_packet_path),
    );
    let report_hash = raw_sha256(report_markdown.as_bytes());
    let report_path = root
        .join(".amphora/reports")
        .join(format!("founder-update-{}.md", &report_hash[..20]));
    persist_immutable(&report_path, report_markdown.as_bytes())?;
    artifact_hashes.insert(relative_display(root, &report_path), report_hash);
    let report_receipt = signed_receipt(
        root,
        &identity,
        "amphora-report-packager",
        "portfolio founder-update --verify-receipts --format markdown",
        !selected.is_empty() && (!verify_receipts || selected.len() == modules.len()),
        EvidenceTier::PublicRetrospective,
        DecisionUse::AuditOnly,
        artifact_hashes,
        json!({
            "modules": modules,
            "module_receipts": selected.iter().map(|receipt| &receipt.receipt_id).collect::<Vec<_>>(),
            "all_phase_1_gates_passed": all_passed,
            "phase_1_claimed": all_passed,
            "independent_expert_review_returned": false,
            "approval_checkpoint": "SEALED_PACKET_NOT_SENT",
            "blinded_expert_review_packet": relative_display(root, &review_packet_path),
            "technical_ip_dossier": relative_display(root, &dossier_path),
            "founder_update": relative_display(root, &report_path),
            "fto_status": "FTO NOT PERFORMED",
        }),
    )?;

    match format {
        ReportFormat::Json => emit_jsonl(&json!({
            "schema": "amphora.founder-update.v1",
            "report_receipt_id": report_receipt.receipt_id,
            "receipts_verified": if verify_receipts { selected.len() } else { 0 },
            "modules": selected,
            "founder_update": relative_display(root, &report_path),
            "blinded_expert_review_packet": relative_display(root, &review_packet_path),
            "technical_ip_dossier": relative_display(root, &dossier_path),
            "fto_status": "FTO NOT PERFORMED",
        })),
        ReportFormat::Markdown => {
            print!("{report_markdown}");
            println!(
                "Companion signed receipt: `{}`; persisted report: `{}`.",
                report_receipt.receipt_id,
                relative_display(root, &report_path)
            );
            Ok(())
        }
    }
}

fn render_founder_markdown(
    receipts: &[EvaluationReceiptV1],
    receipts_verified: bool,
    dossier_path: &str,
    review_packet_path: &str,
) -> String {
    let mut output = String::from(
        "# 30-Day Corrosion + Cure Founder Update\n\n\
Generated from hash-bound manifests and signed evaluation receipts. No subjective readiness percentages are used.\n\n\
| Module | Day-0 evidence | Strict current evidence | Locked benchmark | Phase / authority |\n\
|---|---:|---:|---|---|\n",
    );
    for receipt in receipts {
        if receipt.module_id == CORROSION_MODULE {
            let systems = metric_display(receipt, "independent_system_count");
            let rows = metric_display(receipt, "eligible_raw_rows");
            let score = metric_display(receipt, "balanced_accuracy");
            let baseline = metric_display(receipt, "best_baseline_balanced_accuracy");
            let lift = metric_display(receipt, "balanced_accuracy_lift");
            output.push_str(&format!(
                "| Corrosion | 6 systems; 306 EIS summaries; 766 endpoint measurements | {systems} rights-eligible systems; {rows} rights-eligible raw rows | balanced accuracy {score} vs {baseline}; lift {lift} | {} / {} |\n",
                metric_display(receipt, "phase"),
                metric_display(receipt, "authority_ceiling"),
            ));
        } else if receipt.module_id == CURE_MODULE {
            output.push_str(&format!(
                "| Cure | 25 supplier rows; 16 with PHR; 7 previously described chemistry-complete | {} strict eligible condition rows across {} eligible publishers | within ×1.5 {} vs {}; lift {} | {} / {} |\n",
                metric_display(receipt, "eligible_condition_specific_gel_time_rows"),
                metric_display(receipt, "eligible_publisher_count"),
                metric_display(receipt, "fraction_within_factor_1_5"),
                metric_display(receipt, "best_baseline_fraction_within_factor_1_5"),
                metric_display(receipt, "absolute_lift"),
                metric_display(receipt, "phase"),
                metric_display(receipt, "authority_ceiling"),
            ));
        }
    }
    output.push_str("\n## Gate receipts\n\n");
    for receipt in receipts {
        let ci = receipt
            .confidence_intervals
            .values()
            .next()
            .map(|interval| format!("[{:.4}, {:.4}]", interval.lower, interval.upper))
            .unwrap_or_else(|| "not estimable".into());
        let failed = receipt
            .metrics
            .get("failed_gates")
            .and_then(Value::as_array)
            .map(|values| {
                values
                    .iter()
                    .filter_map(Value::as_str)
                    .collect::<Vec<_>>()
                    .join(", ")
            })
            .unwrap_or_else(|| "none".into());
        output.push_str(&format!(
            "- `{}`: receipt `{}`; passed={}; 95% paired interval={}; failed gates: {}.\n",
            receipt.module_id, receipt.receipt_id, receipt.passed, ci, failed
        ));
        output.push_str(&format!(
            "  Next evidence-changing action: {}\n",
            metric_display(receipt, "next_evidence_changing_action")
        ));
    }
    output.push_str(
        "\n## Authority and approvals\n\n\
Both modules remain capped at Phase-0/Audit. Public retrospective evidence is capped at `SHADOW` and does not authorize production ranking, product superiority, qualification, patentability, or FTO. The blinded expert packet is sealed but not sent; sending is an explicit approval checkpoint, and no independent review has been returned. Supplier documents without explicit derivative-use eligibility remain quarantined. Supplier gel time has not been relabeled as coating pot life; `candidate_pot_life_prediction_h` remains null.\n\n",
    );
    output.push_str(&format!(
        "Expert-review packet: `{review_packet_path}` (`APPROVAL_REQUIRED_NOT_SENT`).\n\nCounsel packet: `{dossier_path}`. `FTO NOT PERFORMED`.\n\nSignature binding: the exact report bytes are included by SHA-256 in the companion signed receipt (input receipts verified: {receipts_verified}).\n"
    ));
    output
}

fn seal_expert_review_packet(root: &Path, receipts: &[EvaluationReceiptV1]) -> Result<PathBuf> {
    let modules = receipts
        .iter()
        .enumerate()
        .map(|(index, receipt)| {
            json!({
                "blinded_module_id": format!("MODULE_{}", index + 1),
                "receipt_id": receipt.receipt_id,
                "passed": receipt.passed,
                "decision_use_ceiling": receipt.decision_use_ceiling,
                "primary_metrics": receipt.metrics.iter()
                    .filter(|(key, _)| matches!(key.as_str(),
                        "balanced_accuracy" | "best_baseline_balanced_accuracy" |
                        "balanced_accuracy_lift" | "fraction_within_factor_1_5" |
                        "best_baseline_fraction_within_factor_1_5" | "absolute_lift" |
                        "failed_gates" | "hostile_null_suite_status"))
                    .map(|(key, value)| (key.clone(), value.clone()))
                    .collect::<BTreeMap<_, _>>(),
                "confidence_intervals": receipt.confidence_intervals,
                "artifact_hashes": receipt.artifact_hashes,
            })
        })
        .collect::<Vec<_>>();
    let packet_seed = json!({"modules": modules, "sealed_on": "2026-07-17"});
    let packet = json!({
        "schema": "amphora.blinded-expert-review-packet.v1",
        "packet_id": format!("expert-review-{}", &stable_hash(&packet_seed)[..20]),
        "sealed_on": "2026-07-17",
        "blinding": {
            "candidate_and_product_identities_removed": true,
            "supplier_names_removed": true,
            "system_labels_removed": true
        },
        "modules": modules,
        "review_questions": [
            "Are the endpoint definitions and method-comparability exclusions technically defensible?",
            "Do the study/source/family blocks prevent material leakage?",
            "Are the baselines and hostile-null suite sufficient before any Phase-1 claim?",
            "Do the reported uncertainty intervals support the stated failed-gate conclusion?"
        ],
        "send_status": "APPROVAL_REQUIRED_NOT_SENT",
        "independent_review_returned": false,
        "authority_if_unsent_or_unreturned": "PHASE_0_AUDIT_ONLY"
    });
    let packet_id = packet
        .get("packet_id")
        .and_then(Value::as_str)
        .expect("packet ID is a string");
    let path = root
        .join(".amphora/expert-review")
        .join(format!("{packet_id}.json"));
    persist_immutable(&path, &canonical_bytes(&packet)?)?;
    Ok(path)
}

fn metric_display(receipt: &EvaluationReceiptV1, key: &str) -> String {
    match receipt.metrics.get(key) {
        Some(Value::String(value)) => value.clone(),
        Some(Value::Number(value)) => value.to_string(),
        Some(Value::Bool(value)) => value.to_string(),
        Some(Value::Null) | None => "null".into(),
        Some(value) => value.to_string(),
    }
}

fn build_ip_dossier(root: &Path, modules: &[String]) -> Result<TechnicalIpDossierV1> {
    let landscape = read_json(&root.join(IP_LANDSCAPE_PATH))?;
    let receipts = load_local_receipts(root)?;
    let current_genesis_hash = ensure_local_identity(root)?.genesis_hash;
    let mut evidence_hashes = BTreeMap::from([
        (
            IP_LANDSCAPE_PATH.into(),
            raw_file_sha256(&root.join(IP_LANDSCAPE_PATH))?,
        ),
        (
            IP_SEARCH_REFRESH_PATH.into(),
            raw_file_sha256(&root.join(IP_SEARCH_REFRESH_PATH))?,
        ),
    ]);
    let mut ablations = Vec::new();
    for module in modules {
        if let Some(receipt) = receipts.iter().find(|receipt| {
            receipt.module_id == *module
                && receipt.metrics.get("command").and_then(Value::as_str)
                    == Some(format!("benchmark run --locked --module {module}").as_str())
                && receipt
                    .metrics
                    .get("program_version")
                    .and_then(Value::as_str)
                    == Some("phase-acceleration-v1")
                && receipt
                    .metrics
                    .get("source_genesis_hash")
                    .and_then(Value::as_str)
                    == Some(current_genesis_hash.as_str())
        }) {
            let path = root
                .join(".amphora/receipts")
                .join(format!("{}.json", receipt.receipt_id));
            evidence_hashes.insert(relative_display(root, &path), raw_file_sha256(&path)?);
            let (metric, candidate_value, null_value) = if module == CORROSION_MODULE {
                (
                    "balanced_accuracy",
                    receipt
                        .metrics
                        .get("balanced_accuracy")
                        .and_then(Value::as_f64),
                    receipt
                        .metrics
                        .get("best_baseline_balanced_accuracy")
                        .and_then(Value::as_f64),
                )
            } else {
                (
                    "fraction_within_factor_1_5",
                    receipt
                        .metrics
                        .get("fraction_within_factor_1_5")
                        .and_then(Value::as_f64),
                    receipt
                        .metrics
                        .get("best_baseline_fraction_within_factor_1_5")
                        .and_then(Value::as_f64),
                )
            };
            ablations.push(HostileNullAblationV1 {
                module_id: module.clone(),
                null_name: "best_locked_baseline".into(),
                metric: metric.into(),
                candidate_value,
                null_value,
                reproducible_differentiator: false,
                receipt_hash: Some(raw_file_sha256(&path)?),
            });
        }
    }
    let charts = landscape
        .get("families")
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
        .take(12)
        .filter_map(|family| {
            let family_id = family.get("doc_read")?.as_str()?.to_owned();
            let source_url = family.get("url")?.as_str()?.to_owned();
            let elements = family
                .get("key_elements")
                .and_then(Value::as_array)
                .into_iter()
                .flatten()
                .filter_map(Value::as_str)
                .map(|element| {
                    (
                        element.to_owned(),
                        "PRELIMINARY_CLOSEST_ART_ELEMENT_NOT_LEGAL_CONCLUSION".into(),
                    )
                })
                .collect();
            Some(amphora_core::ClosestArtElementChartV1 {
                family_id,
                source_url,
                elements,
                unresolved_elements: vec![
                    "dependent claims not fully reviewed".into(),
                    "prosecution history and equivalents not reviewed".into(),
                    "jurisdiction-complete legal status not verified".into(),
                ],
            })
        })
        .collect();
    let dossier = TechnicalIpDossierV1 {
        schema: TECHNICAL_IP_DOSSIER_SCHEMA.into(),
        dossier_id: format!(
            "technical-ip-corrosion-cure-{}",
            &stable_hash(&serde_json::to_value(&evidence_hashes)?)[..16]
        ),
        generated_on: "2026-07-17".into(),
        modules: modules.to_vec(),
        conception_dates: BTreeMap::from([
            (CORROSION_MODULE.into(), "FOUNDER CONFIRMATION REQUIRED".into()),
            (CURE_MODULE.into(), "FOUNDER CONFIRMATION REQUIRED".into()),
        ]),
        contributors: vec!["FOUNDER CONFIRMATION REQUIRED".into()],
        technical_problem: vec![
            "Predict coating degradation across study/system boundaries without source leakage or over-reading single-frequency EIS summaries.".into(),
            "Prioritize CRO gel-time experiments without conflating supplier gel time, coating pot life, or incomparable cure methods.".into(),
        ],
        model_architecture: vec![
            "Deterministic blocked benchmarks compare transparent baselines, current models, and hostile nulls under immutable locks.".into(),
            "Strict observations bind raw hashes, rights, method, units, conditions, split, publisher, study, and system/family identity.".into(),
            "Verified model artifacts are fail-closed for rights, method comparability, missing conditions, and applicability domain.".into(),
        ],
        evidence_hashes,
        closest_art_element_charts: charts,
        hostile_null_ablations: ablations,
        alternatives: vec![
            "Majority/constant and expert impedance thresholds".into(),
            "Monotone log-linear, deterministic GAM, and boosted-stump corrosion models".into(),
            "Global/family median, stoichiometric log-linear, regularized spline/GAM, and boosted-stump cure models".into(),
            "WIPO PATENTSCOPE, EPO OPS/Espacenet, and USPTO Patent Public Search refresh remains a preliminary classification search only".into(),
        ],
        disclosure_log: Vec::new(),
        recommendations: vec![
            IpRecommendationV1 {
                hypothesis_id: "corrosion-locked-differentiator".into(),
                disposition: IpDispositionV1::NoFile,
                rationale: "Locked lift is zero and the paired confidence lower bound is not positive; retain implementation details as ordinary confidential know-how pending differentiating evidence.".into(),
            },
            IpRecommendationV1 {
                hypothesis_id: "cure-locked-differentiator".into(),
                disposition: IpDispositionV1::NoFile,
                rationale: "The strict eligible dataset is empty and the prior lift confidence interval crosses zero; no technical differentiator is established.".into(),
            },
        ],
        locked_differentiator_present: false,
        fto_status: "FTO NOT PERFORMED".into(),
    };
    dossier.validate()?;
    Ok(dossier)
}

fn persist_ip_dossier(root: &Path, dossier: &TechnicalIpDossierV1) -> Result<PathBuf> {
    let value = serde_json::to_value(dossier)?;
    let path = root
        .join(".amphora/dossiers")
        .join(format!("{}.json", dossier.dossier_id));
    persist_immutable(&path, &canonical_bytes(&value)?)?;
    Ok(path)
}

fn shadow_run(root: &Path, args: ShadowRunArgs) -> Result<()> {
    let input = match args.candidate {
        Some(path) => read_json(&path)?,
        None => {
            read_json(&root.join("amphora-candidate-contract/fixtures/molecule_candidate.json"))?
        }
    };
    let candidates = input.as_array().cloned().unwrap_or_else(|| vec![input]);
    if candidates.is_empty() {
        bail!("shadow input candidate array is empty");
    }
    let run_id = format!(
        "shadow-{}",
        &stable_hash(&json!({"candidates": candidates, "seed": args.seed}))[..20]
    );
    let requests: Vec<_> = candidates
        .iter()
        .enumerate()
        .map(|(index, candidate)| {
            (
                candidate.clone(),
                args.seed + index as u64,
                json!({"parent_ids": [], "generation": 0, "mutation_id": null}),
                run_id.clone(),
            )
        })
        .collect();
    let pool = EnginePool::new(root, args.workers)?;
    let parallel = pool.score_many(requests.clone());
    let serial = EnginePool::new(root, 1)?.score_many(requests);
    let parallel_values: Vec<_> = parallel.into_iter().collect::<Result<Vec<_>, _>>()?;
    let serial_values: Vec<_> = serial.into_iter().collect::<Result<Vec<_>, _>>()?;
    let worker_equal = parallel_values
        .iter()
        .map(|(value, _)| stable_hash(value))
        .eq(serial_values.iter().map(|(value, _)| stable_hash(value)));
    let mut rankings: Vec<_> = parallel_values
        .iter()
        .map(|(result, _)| {
            let envelopes = result
                .get("score_envelopes")
                .and_then(Value::as_array)
                .cloned()
                .unwrap_or_default();
            let numeric: Vec<_> = envelopes
                .iter()
                .filter_map(|row| row.get("score_0_1").and_then(Value::as_f64))
                .collect();
            let scored = envelopes
                .iter()
                .filter(|row| row.get("status").and_then(Value::as_str) == Some("SCORED"))
                .count();
            let score = if numeric.is_empty() {
                scored as f64 / envelopes.len().max(1) as f64
            } else {
                numeric.iter().sum::<f64>() / numeric.len() as f64
            };
            json!({
                "candidate_id": result.pointer("/candidate/candidate_id"),
                "shadow_score": score,
                "scored_modules": scored,
                "module_count": envelopes.len(),
                "abstention_count": envelopes.len() - scored,
                "result_hash": result.pointer("/provenance/result_hash"),
            })
        })
        .collect();
    rankings.sort_by(|left, right| {
        right
            .get("shadow_score")
            .and_then(Value::as_f64)
            .partial_cmp(&left.get("shadow_score").and_then(Value::as_f64))
            .unwrap_or(std::cmp::Ordering::Equal)
            .then_with(|| {
                left.get("candidate_id")
                    .and_then(Value::as_str)
                    .cmp(&right.get("candidate_id").and_then(Value::as_str))
            })
    });
    for (index, row) in rankings.iter_mut().enumerate() {
        row["shadow_rank"] = Value::from(index as u64 + 1);
    }
    let event = json!({
        "schema": "amphora.shadow-ranking.v1",
        "run_id": run_id,
        "workers": args.workers.max(1),
        "worker_replay_equal": worker_equal,
        "decision_use": "SHADOW",
        "production_pareto_affected": false,
        "rankings": rankings,
    });
    emit_jsonl(&event)?;
    let artifact_hashes: BTreeMap<_, _> = parallel_values
        .iter()
        .filter_map(|(result, _)| {
            Some((
                format!(
                    "result:{}",
                    result.pointer("/candidate/candidate_id")?.as_str()?
                ),
                stable_hash(result),
            ))
        })
        .collect();
    let receipt = control_receipt(
        root,
        "amphora-optimizer-orchestrator",
        "shadow run",
        worker_equal,
        EvidenceTier::SyntheticDiagnostic,
        DecisionUse::Shadow,
        artifact_hashes,
        json!({
            "candidate_count": candidates.len(),
            "worker_replay_equal": worker_equal,
            "production_pareto_affected": false,
        }),
    )?;
    emit_jsonl(&serde_json::to_value(receipt)?)
}

#[allow(clippy::too_many_arguments)]
fn control_receipt(
    root: &Path,
    module_id: &str,
    command: &str,
    passed: bool,
    tier: EvidenceTier,
    ceiling: DecisionUse,
    artifact_hashes: BTreeMap<String, String>,
    details: Value,
) -> Result<EvaluationReceiptV1> {
    let identity = ensure_local_identity(root)?;
    signed_receipt(
        root,
        &identity,
        module_id,
        command,
        passed,
        tier,
        ceiling,
        artifact_hashes,
        details,
    )
}

#[allow(clippy::too_many_arguments)]
fn module_control_receipt(
    root: &Path,
    module_id: &str,
    command: &str,
    passed: bool,
    tier: EvidenceTier,
    ceiling: DecisionUse,
    artifact_hashes: BTreeMap<String, String>,
    details: Value,
) -> Result<EvaluationReceiptV1> {
    let mut receipt = new_module_receipt(
        root,
        module_id,
        command,
        passed,
        tier,
        ceiling,
        artifact_hashes,
        details,
    )?;
    if !read_only_command() {
        let identity = ensure_local_identity(root)?;
        receipt.metrics.insert(
            "source_genesis_hash".into(),
            Value::String(identity.genesis_hash.clone()),
        );
        bind_receipt_identity(&mut receipt)?;
        receipt.sign(&identity.key_id, &identity.signing_key)?;
        persist_receipt(root, &receipt)?;
    }
    Ok(receipt)
}

fn read_only_command() -> bool {
    std::env::var_os("AMPHORA_READ_ONLY_COMMAND").is_some()
}

#[allow(clippy::too_many_arguments)]
fn new_module_receipt(
    root: &Path,
    module_id: &str,
    command: &str,
    passed: bool,
    tier: EvidenceTier,
    ceiling: DecisionUse,
    artifact_hashes: BTreeMap<String, String>,
    details: Value,
) -> Result<EvaluationReceiptV1> {
    let lock_bytes = if is_scientific_model_module(module_id) {
        let (_, _, lock_path) = module_paths(module_id)?;
        fs::read(root.join(lock_path))?
    } else {
        let (_, lock_bytes, _) = read_module_benchmark_lock(root, module_id)?;
        lock_bytes
    };
    new_receipt(
        module_id,
        command,
        passed,
        tier,
        ceiling,
        raw_file_sha256(&root.join(REGISTRY_PATH))?,
        raw_sha256(&lock_bytes),
        artifact_hashes,
        details,
        BTreeMap::from([
            ("no_candidate_specific_performance_claim".into(), true),
            ("no_product_release_or_qualification".into(), true),
            ("no_superiority_claim".into(), true),
            ("public_retrospective_shadow_maximum".into(), true),
            ("unresolved_rights_quarantined".into(), true),
        ]),
        vec![
            "public retrospective research evidence only".into(),
            "independent expert review is approval-gated and has not been returned".into(),
        ],
    )
}

#[allow(clippy::too_many_arguments)]
fn signed_receipt(
    root: &Path,
    identity: &LocalIdentity,
    module_id: &str,
    command: &str,
    passed: bool,
    tier: EvidenceTier,
    ceiling: DecisionUse,
    artifact_hashes: BTreeMap<String, String>,
    details: Value,
) -> Result<EvaluationReceiptV1> {
    let mut receipt = new_receipt(
        module_id,
        command,
        passed,
        tier,
        ceiling,
        raw_file_sha256(&root.join(REGISTRY_PATH))?,
        raw_file_sha256(&root.join(BENCHMARK_LOCK_PATH))?,
        artifact_hashes,
        details,
        BTreeMap::from([
            ("pre_phase_0_research_only".into(), true),
            ("no_product_release_or_qualification".into(), true),
            ("no_superiority_claim".into(), true),
            ("unresolved_rights_quarantined".into(), true),
        ]),
        vec!["digital phase-1 applicability only".into()],
    )?;
    receipt.metrics.insert(
        "source_genesis_hash".into(),
        Value::String(identity.genesis_hash.clone()),
    );
    bind_receipt_identity(&mut receipt)?;
    receipt.sign(&identity.key_id, &identity.signing_key)?;
    persist_receipt(root, &receipt)?;
    Ok(receipt)
}

#[allow(clippy::too_many_arguments)]
fn new_receipt(
    module_id: &str,
    command: &str,
    passed: bool,
    evidence_tier: EvidenceTier,
    decision_use_ceiling: DecisionUse,
    registry_manifest_hash: String,
    benchmark_lock_hash: String,
    artifact_hashes: BTreeMap<String, String>,
    details: Value,
    claim_locks: BTreeMap<String, bool>,
    applicability_limits: Vec<String>,
) -> Result<EvaluationReceiptV1> {
    let receipt_seed = json!({
        "module_id": module_id,
        "command": command,
        "passed": passed,
        "evidence_tier": evidence_tier,
        "decision_use_ceiling": decision_use_ceiling,
        "registry_manifest_hash": registry_manifest_hash,
        "benchmark_lock_hash": benchmark_lock_hash,
        "artifact_hashes": artifact_hashes,
        "details": details,
    });
    let mut metrics = BTreeMap::new();
    metrics.insert("command".into(), Value::String(command.into()));
    metrics.insert("details".into(), details);
    let receipt = EvaluationReceiptV1 {
        schema: EVALUATION_RECEIPT_SCHEMA.into(),
        receipt_id: format!("receipt-{}", &stable_hash(&receipt_seed)[..24]),
        module_id: module_id.into(),
        registry_manifest_hash,
        registry_owned_identity: true,
        artifact_hashes,
        benchmark_lock_hash,
        metrics,
        confidence_intervals: BTreeMap::new(),
        evidence_tier,
        decision_use_ceiling,
        passed,
        claim_locks,
        applicability_limits,
        signature: None,
    };
    receipt.validate()?;
    Ok(receipt)
}

fn bind_receipt_identity(receipt: &mut EvaluationReceiptV1) -> Result<()> {
    receipt.signature = None;
    receipt.receipt_id.clear();
    let value = serde_json::to_value(&*receipt)?;
    receipt.receipt_id = format!("receipt-{}", &stable_hash(&value)[..24]);
    receipt.validate()?;
    Ok(())
}

fn ensure_local_identity(root: &Path) -> Result<LocalIdentity> {
    let control_dir = root.join(".amphora/control");
    fs::create_dir_all(&control_dir)?;
    let genesis_hash = ensure_source_genesis(root, &control_dir)?;
    let key_path = control_dir.join("local-ed25519.key");
    let key_bytes = if key_path.exists() {
        let bytes = fs::read(&key_path)?;
        if bytes.len() != 32 {
            bail!("local Ed25519 key has invalid length");
        }
        bytes
    } else {
        let mut bytes = vec![0_u8; 32];
        fs::File::open("/dev/urandom")
            .context("opening operating-system random source")?
            .read_exact(&mut bytes)?;
        write_private_key(&key_path, &bytes)?;
        bytes
    };
    let signing_key = SigningKey::from_bytes(
        key_bytes
            .as_slice()
            .try_into()
            .map_err(|_| anyhow!("local Ed25519 key has invalid length"))?,
    );
    let public = signing_key.verifying_key().to_bytes();
    let key_id = format!("local-{}", &raw_sha256(&public)[..16]);
    let public_path = control_dir.join("local-ed25519.pub.json");
    let public_value = json!({
        "schema": "amphora.local-trust-key.v1",
        "key_id": key_id,
        "algorithm": "Ed25519",
        "public_key_hex": hex(&public),
        "authority": "LOCAL_DEVELOPMENT_AUDIT_ONLY",
    });
    persist_immutable(&public_path, &canonical_bytes(&public_value)?)?;
    Ok(LocalIdentity {
        signing_key,
        key_id,
        genesis_hash,
    })
}

#[cfg(unix)]
fn write_private_key(path: &Path, bytes: &[u8]) -> Result<()> {
    use std::os::unix::fs::OpenOptionsExt;
    let mut file = OpenOptions::new()
        .create_new(true)
        .write(true)
        .mode(0o600)
        .open(path)?;
    file.write_all(bytes)?;
    file.sync_all()?;
    Ok(())
}

#[cfg(not(unix))]
fn write_private_key(path: &Path, bytes: &[u8]) -> Result<()> {
    let mut file = OpenOptions::new().create_new(true).write(true).open(path)?;
    file.write_all(bytes)?;
    file.sync_all()?;
    Ok(())
}

fn ensure_source_genesis(root: &Path, control_dir: &Path) -> Result<String> {
    let files = source_tree_hashes(root)?;
    let root_hash = stable_hash(&serde_json::to_value(&files)?);
    let legacy_path = control_dir.join("source-genesis.v1.json");
    let legacy_matches = if legacy_path.exists() {
        let existing: SourceGenesisV1 = serde_json::from_value(read_json(&legacy_path)?)?;
        existing.schema == "amphora.source-genesis.v1"
            && existing.root_hash == root_hash
            && existing.files == files
    } else {
        false
    };
    let path = if legacy_matches {
        legacy_path
    } else {
        control_dir.join(format!("source-genesis-{}.v1.json", &root_hash[..16]))
    };
    let genesis = SourceGenesisV1 {
        schema: "amphora.source-genesis.v1".into(),
        files,
        root_hash: root_hash.clone(),
    };
    if path.exists() {
        let existing: SourceGenesisV1 = serde_json::from_value(read_json(&path)?)?;
        if existing.schema != genesis.schema
            || existing.root_hash != root_hash
            || existing.files != genesis.files
        {
            bail!("hash-qualified source genesis conflicts with current source tree");
        }
    } else {
        persist_immutable(&path, &canonical_bytes(&serde_json::to_value(&genesis)?)?)?;
    }
    Ok(root_hash)
}

fn source_tree_hashes(root: &Path) -> Result<BTreeMap<String, String>> {
    let mut candidates = Vec::new();
    collect_source_files(root, root, &mut candidates)?;
    candidates.sort();
    let mut files = BTreeMap::new();
    for path in candidates {
        files.insert(relative_display(root, &path), raw_file_sha256(&path)?);
    }
    Ok(files)
}

fn collect_source_files(root: &Path, directory: &Path, output: &mut Vec<PathBuf>) -> Result<()> {
    let mut entries = fs::read_dir(directory)?.collect::<std::io::Result<Vec<_>>>()?;
    entries.sort_by_key(|entry| entry.file_name());
    for entry in entries {
        let path = entry.path();
        let relative = path.strip_prefix(root).unwrap_or(&path);
        if entry.file_type()?.is_dir() {
            let first = relative
                .components()
                .next()
                .and_then(|part| part.as_os_str().to_str());
            let volatile = relative.components().any(|component| {
                component.as_os_str().to_str().is_some_and(|name| {
                    matches!(
                        name,
                        "target"
                            | ".amphora"
                            | ".git"
                            | ".venv"
                            | "__pycache__"
                            | ".pytest_cache"
                            | ".ruff_cache"
                            | ".mypy_cache"
                    ) || name.starts_with(".venv-")
                })
            });
            if volatile
                || matches!(first, Some("target" | ".amphora" | ".git"))
                || relative.starts_with("feedback/v1/external_data")
                || relative.starts_with("feedback/v1/derived")
                || relative.starts_with(".codex")
            {
                continue;
            }
            collect_source_files(root, &path, output)?;
        } else if source_file(relative) && !phase0_generated_file(relative) {
            output.push(path);
        }
    }
    Ok(())
}

fn phase0_generated_file(path: &Path) -> bool {
    let text = path.to_string_lossy();
    text == "config/program/phase0-decision-report.v2.json"
        || text.ends_with("/evidence/phase0/benchmark/result.v1.json")
        || text.contains("/evidence/phase0/receipts/")
        || text.ends_with("/movement/ledger.v1.json")
        || text.contains("/movement/events/")
}

fn source_file(path: &Path) -> bool {
    matches!(
        path.extension().and_then(|extension| extension.to_str()),
        Some("rs" | "toml" | "lock" | "json" | "md" | "h" | "hpp" | "cc" | "cpp")
    )
}

fn persist_receipt(root: &Path, receipt: &EvaluationReceiptV1) -> Result<()> {
    let path = root
        .join(".amphora/receipts")
        .join(format!("{}.json", receipt.receipt_id));
    persist_immutable(&path, &canonical_bytes(&serde_json::to_value(receipt)?)?)
}

fn persist_immutable(path: &Path, bytes: &[u8]) -> Result<()> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)?;
    }
    if path.exists() {
        if fs::read(path)? == bytes {
            return Ok(());
        }
        bail!(
            "immutable artifact already exists with different bytes: {}",
            path.display()
        );
    }
    let temporary = path.with_extension(format!("tmp-{}", std::process::id()));
    let mut file = OpenOptions::new()
        .create_new(true)
        .write(true)
        .open(&temporary)?;
    file.write_all(bytes)?;
    file.sync_all()?;
    fs::rename(&temporary, path)?;
    Ok(())
}

fn load_local_receipts(root: &Path) -> Result<Vec<EvaluationReceiptV1>> {
    let directory = root.join(".amphora/receipts");
    if !directory.exists() {
        return Ok(Vec::new());
    }
    let mut paths = fs::read_dir(directory)?
        .filter_map(|entry| entry.ok().map(|entry| entry.path()))
        .filter(|path| path.extension().and_then(|value| value.to_str()) == Some("json"))
        .collect::<Vec<_>>();
    paths.sort();
    paths
        .iter()
        .map(|path| Ok(serde_json::from_value(read_json(path)?)?))
        .collect()
}

fn read_receipt_stream(path: &Path) -> Result<Vec<EvaluationReceiptV1>> {
    let text = fs::read_to_string(path)?;
    let mut receipts = Vec::new();
    for line in text.lines().filter(|line| !line.trim().is_empty()) {
        let value = amphora_core::parse_json_strict(line.as_bytes())?;
        if value.get("schema").and_then(Value::as_str) == Some(EVALUATION_RECEIPT_SCHEMA) {
            receipts.push(serde_json::from_value(value)?);
        }
    }
    Ok(receipts)
}

fn read_json(path: &Path) -> Result<Value> {
    let bytes = fs::read(path).with_context(|| format!("reading {}", path.display()))?;
    amphora_core::parse_json_strict(&bytes).map_err(Into::into)
}

fn raw_file_sha256(path: &Path) -> Result<String> {
    let bytes = fs::read(path).with_context(|| format!("hashing {}", path.display()))?;
    Ok(raw_sha256(&bytes))
}

fn raw_sha256(bytes: &[u8]) -> String {
    let mut digest = Sha256::new();
    digest.update(bytes);
    format!("{:x}", digest.finalize())
}

fn canonical_bytes(value: &Value) -> Result<Vec<u8>> {
    Ok(serde_json::to_vec(&canonicalize(value))?)
}

fn emit_jsonl(value: &Value) -> Result<()> {
    println!("{}", String::from_utf8(canonical_bytes(value)?)?);
    Ok(())
}

fn required_str<'a>(value: &'a Value, field: &str) -> Result<&'a str> {
    value
        .get(field)
        .and_then(Value::as_str)
        .filter(|value| !value.trim().is_empty())
        .ok_or_else(|| anyhow!("required string field {field} is absent"))
}

fn relative_display(root: &Path, path: &Path) -> String {
    path.strip_prefix(root)
        .unwrap_or(path)
        .to_string_lossy()
        .replace('\\', "/")
}

fn hex(bytes: &[u8]) -> String {
    bytes.iter().map(|byte| format!("{byte:02x}")).collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::net::TcpListener;
    use std::sync::atomic::{AtomicUsize, Ordering};
    use std::thread;

    static TEMP_ID: AtomicUsize = AtomicUsize::new(0);

    fn temporary_workspace(label: &str) -> PathBuf {
        let root = std::env::temp_dir().join(format!(
            "amphora-{label}-{}-{}",
            std::process::id(),
            TEMP_ID.fetch_add(1, Ordering::Relaxed)
        ));
        fs::create_dir_all(root.join("config")).unwrap();
        root
    }

    fn serve_fetch_fixture(
        payload: &'static [u8],
        license: &'static [u8],
    ) -> (String, thread::JoinHandle<()>) {
        let listener = TcpListener::bind("127.0.0.1:0").unwrap();
        let address = listener.local_addr().unwrap();
        let handle = thread::spawn(move || {
            for stream in listener.incoming().take(2) {
                let mut stream = stream.unwrap();
                let mut request = [0_u8; 2048];
                let count = stream.read(&mut request).unwrap();
                let request = String::from_utf8_lossy(&request[..count]);
                let body = if request.starts_with("GET /license ") {
                    license
                } else {
                    payload
                };
                write!(
                    stream,
                    "HTTP/1.1 200 OK\r\nContent-Type: application/octet-stream\r\nContent-Length: {}\r\nConnection: close\r\n\r\n",
                    body.len()
                )
                .unwrap();
                stream.write_all(body).unwrap();
            }
        });
        (format!("http://{address}"), handle)
    }

    fn write_fetch_census(
        root: &Path,
        base_url: &str,
        expected_sha256: &str,
        license_sha256: &str,
    ) {
        let path = root.join(CORROSION_SOURCES_PATH);
        fs::create_dir_all(path.parent().unwrap()).unwrap();
        fs::write(
            path,
            serde_json::to_vec(&json!({
                "schema": "amphora.module-source-census.v1",
                "module_id": CORROSION_MODULE,
                "sources": [{
                    "source_id": "fixture",
                    "fetch": {
                        "download_url": format!("{base_url}/payload"),
                        "expected_sha256": expected_sha256,
                        "install_path": "evidence/raw/payload.bin",
                        "license_url": format!("{base_url}/license"),
                        "license_sha256": license_sha256,
                        "license_install_path": "evidence/raw/LICENSE.txt",
                        "acquisition_record_path": "evidence/raw/acquisition.json"
                    }
                }]
            }))
            .unwrap(),
        )
        .unwrap();
    }

    fn valid_qualification_value() -> Value {
        json!({
            "schema": "amphora.pot-life-scale-qualification.v1",
            "qualification_id": "QUAL-CLI-1",
            "performed_with_non_reactive_fluid": true,
            "qualification_fluid_sha256": "a".repeat(64),
            "sprayer_dead_volume_demand_g": 100.0,
            "test_card_demand_g": 50.0,
            "maximum_facility_approved_fill_g": 500.0,
            "primary_geometry": {
                "geometry_id": "G1", "shape": "CYLINDER", "inside_diameter_mm": 100.0,
                "fill_height_mm": 80.0, "headspace_ml": 100.0, "nominal_volume_ml": 500.0,
                "lid_handling": "LOCKED_COVER_BETWEEN_MEASUREMENTS"
            },
            "second_geometry": {
                "geometry_id": "G2", "shape": "CYLINDER", "inside_diameter_mm": 140.0,
                "fill_height_mm": 80.0, "headspace_ml": 100.0, "nominal_volume_ml": 1000.0,
                "lid_handling": "LOCKED_COVER_BETWEEN_MEASUREMENTS"
            },
            "distinct_geometry_confirmed_safe": true,
            "airless_spray_setup": {
                "setup_id": "AIRLESS-1", "pump_id": "PUMP-1", "tip_orifice_in": 0.019,
                "tip_fan_width_in": 10.0, "locked_pressure_psi": 2500.0,
                "hose_length_ft": 50.0, "hose_inside_diameter_in": 0.25,
                "filter_mesh": 60, "locked_pass_count": 2, "thinning_allowed": false
            },
            "calibration_ids": {
                "stormer": "CAL-STORMER", "temperature_logger": "CAL-TEMP",
                "sprayer_pressure": "CAL-PRESSURE"
            }
        })
    }

    #[test]
    fn rights_policy_is_conservative() {
        assert!(rights_eligible("CC-BY-4.0", "public_direct", "ACQUIRED"));
        assert!(!rights_eligible(
            "MIT; data for academic purpose only",
            "public_direct_large",
            "ACQUIRED"
        ));
        assert!(!rights_eligible("unknown", "public_direct", "ACQUIRED"));
        assert!(!rights_eligible(
            "MIT",
            "public_direct",
            "BLOCKED_AFTER_ATTEMPTS"
        ));
    }

    #[test]
    fn benchmark_lock_is_strict_and_bound_to_current_parents() {
        let root = super::super::workspace_root();
        let (lock, _, _) = read_benchmark_lock(&root).unwrap();
        assert_eq!(lock.schema, amphora_core::BENCHMARK_LOCK_SCHEMA);
        lock.validate().unwrap();
        verify_lock_parents(&root, &lock).unwrap();
    }

    #[test]
    fn module_locks_are_strict_and_bound_to_current_parents() {
        let root = super::super::workspace_root();
        for module in [
            CORROSION_MODULE,
            CURE_MODULE,
            MOLECULE_PROPERTY_MODULE,
            MOLECULE_ROLE_MODULE,
        ] {
            let (lock, _, _) = read_module_benchmark_lock(&root, module).unwrap();
            lock.validate().unwrap();
            verify_lock_parents(&root, &lock).unwrap();
            assert_eq!(lock.module_id, module);
        }
    }

    #[test]
    fn corrosion_manifest_reproduces_day_zero_counts_from_raw_hashes() {
        let root = super::super::workspace_root();
        let audit = audit_module_data(&root, CORROSION_MODULE).unwrap();
        assert!(audit.integrity_valid());
        assert_eq!(audit.eligible_systems.len(), 6);
        assert_eq!(audit.eligible_studies.len(), 1);
        assert_eq!(audit.endpoint_counts["eis"], 306);
        assert_eq!(audit.reported_rows, 1072);
        assert_eq!(audit.missing_sources, 3);
    }

    #[test]
    fn corrosion_audit_accumulates_derived_counts_across_sources() {
        let root = super::super::workspace_root();
        let census = read_json(&root.join(CORROSION_SOURCES_PATH)).unwrap();
        let source = &census["sources"][0];
        let mut audit = ModuleDataAudit {
            module_id: CORROSION_MODULE.into(),
            artifact_hashes: BTreeMap::new(),
            rights: Vec::new(),
            planned_sources: 2,
            available_sources: 2,
            eligible_sources: 2,
            quarantined_sources: 0,
            missing_sources: 0,
            missing_files: 0,
            mismatched_files: 0,
            reported_rows: 0,
            eligible_rows: 0,
            eligible_systems: BTreeSet::new(),
            eligible_studies: BTreeSet::new(),
            endpoint_counts: BTreeMap::new(),
        };
        audit_corrosion_source(&root, source, &mut audit).unwrap();
        let one_source_rows = audit.reported_rows;
        let one_source_eis = audit.endpoint_counts["eis_summary_rows"];
        audit_corrosion_source(&root, source, &mut audit).unwrap();
        assert_eq!(audit.reported_rows, one_source_rows * 2);
        assert_eq!(
            audit.endpoint_counts["eis_summary_rows"],
            one_source_eis * 2
        );
    }

    #[test]
    fn explicit_fetch_installs_payload_license_headers_and_receipt_immutably() {
        const PAYLOAD: &[u8] = b"immutable scientific payload\n";
        const LICENSE: &[u8] = b"CC BY 4.0 fixture license\n";
        let root = temporary_workspace("network-fetch");
        let (base_url, server) = serve_fetch_fixture(PAYLOAD, LICENSE);
        write_fetch_census(&root, &base_url, &raw_sha256(PAYLOAD), &raw_sha256(LICENSE));
        run_module_fetch(&root, CORROSION_MODULE, "fixture").unwrap();
        server.join().unwrap();
        assert_eq!(
            fs::read(root.join("evidence/raw/payload.bin")).unwrap(),
            PAYLOAD
        );
        assert_eq!(
            fs::read(root.join("evidence/raw/LICENSE.txt")).unwrap(),
            LICENSE
        );
        assert!(root.join("evidence/raw/payload.bin.headers").is_file());
        assert!(root.join("evidence/raw/LICENSE.txt.headers").is_file());
        let acquisition = read_json(&root.join("evidence/raw/acquisition.json")).unwrap();
        assert_eq!(acquisition["payload_sha256"], raw_sha256(PAYLOAD));
        assert_eq!(acquisition["license_sha256"], raw_sha256(LICENSE));
        assert_eq!(acquisition["immutable_install"], true);
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn explicit_fetch_rejects_changed_remote_bytes_before_install() {
        const CHANGED: &[u8] = b"changed remote payload\n";
        const LICENSE: &[u8] = b"CC BY 4.0 fixture license\n";
        let root = temporary_workspace("network-fetch-changed");
        let (base_url, server) = serve_fetch_fixture(CHANGED, LICENSE);
        write_fetch_census(
            &root,
            &base_url,
            &raw_sha256(b"expected original payload\n"),
            &raw_sha256(LICENSE),
        );
        let error = run_module_fetch(&root, CORROSION_MODULE, "fixture")
            .unwrap_err()
            .to_string();
        server.join().unwrap();
        assert!(error.contains("remote bytes changed"));
        assert!(!root.join("evidence/raw/payload.bin").exists());
        assert!(!root.join("evidence/raw/acquisition.json").exists());
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn cure_vendor_rows_are_quarantined_and_endpoint_separated() {
        let root = super::super::workspace_root();
        let audit = audit_module_data(&root, CURE_MODULE).unwrap();
        assert!(audit.integrity_valid());
        assert_eq!(audit.reported_rows, 25);
        assert_eq!(audit.eligible_rows, 0);
        assert_eq!(audit.eligible_sources, 0);
        assert_eq!(audit.quarantined_sources, 3);
        assert_eq!(audit.endpoint_counts["gel_time"], 25);
    }

    #[test]
    fn legacy_molecule_controls_are_inventoried_but_not_promotion_eligible() {
        let root = super::super::workspace_root();
        let property = audit_module_data(&root, MOLECULE_PROPERTY_MODULE).unwrap();
        assert!(property.integrity_valid());
        assert_eq!(property.reported_rows, 17);
        assert_eq!(property.eligible_rows, 0);
        assert_eq!(property.missing_sources, 1);
        assert_eq!(property.endpoint_counts["measured_only_annex"], 3);

        let role = audit_module_data(&root, MOLECULE_ROLE_MODULE).unwrap();
        assert!(role.integrity_valid());
        assert_eq!(role.reported_rows, 12);
        assert_eq!(role.eligible_rows, 0);
        assert_eq!(role.missing_sources, 1);
        assert_eq!(role.endpoint_counts["exact_defined_controls"], 9);
    }

    #[test]
    fn current_molecule_benchmarks_auto_demote_with_explicit_failed_gates() {
        let root = super::super::workspace_root();
        let property_audit = audit_module_data(&root, MOLECULE_PROPERTY_MODULE).unwrap();
        let property_split: SplitManifestV1 =
            serde_json::from_value(read_json(&root.join(MOLECULE_PROPERTY_SPLIT_PATH)).unwrap())
                .unwrap();
        let property_benchmark = read_json(&root.join(MOLECULE_PROPERTY_BENCHMARK_PATH)).unwrap();
        let property = molecule_property_benchmark_result(
            &property_audit,
            &property_split,
            &property_benchmark,
        )
        .unwrap();
        assert!(!property.passed);
        assert_eq!(property.metrics["phase"], "PHASE_0");
        assert_eq!(property.metrics["truth_set_eligible_count"], 0);

        let role_audit = audit_module_data(&root, MOLECULE_ROLE_MODULE).unwrap();
        let role_split: SplitManifestV1 =
            serde_json::from_value(read_json(&root.join(MOLECULE_ROLE_SPLIT_PATH)).unwrap())
                .unwrap();
        let role_benchmark = read_json(&root.join(MOLECULE_ROLE_BENCHMARK_PATH)).unwrap();
        let role =
            molecule_role_benchmark_result(&role_audit, &role_split, &role_benchmark).unwrap();
        assert!(!role.passed);
        assert_eq!(role.metrics["phase"], "PHASE_0");
        if amphora_rdkit_ffi::backend_status().available {
            assert!(role.metrics["balanced_accuracy"]
                .as_f64()
                .is_some_and(|value| value >= 0.90));
        } else {
            assert_eq!(role.metrics["balanced_accuracy"], Value::Null);
        }
    }

    #[test]
    fn molecule_evidence_cli_flow_builds_and_signs_negative_receipts() {
        let source_root = super::super::workspace_root();
        for module in [MOLECULE_PROPERTY_MODULE, MOLECULE_ROLE_MODULE] {
            let root = temporary_workspace(module);
            let copy_relative = |relative: &str| {
                let destination = root.join(relative);
                fs::create_dir_all(destination.parent().unwrap()).unwrap();
                fs::copy(source_root.join(relative), destination).unwrap();
            };
            copy_relative(REGISTRY_PATH);
            let (source_path, split_path, lock_path) = module_paths(module).unwrap();
            for relative in [source_path, split_path, lock_path] {
                copy_relative(relative);
            }
            let lock: BenchmarkLockV1 =
                serde_json::from_value(read_json(&source_root.join(lock_path)).unwrap()).unwrap();
            for relative in lock.dataset_hashes.keys() {
                copy_relative(relative);
            }
            copy_relative(if module == MOLECULE_PROPERTY_MODULE {
                MOLECULE_PROPERTY_BENCHMARK_PATH
            } else {
                MOLECULE_ROLE_BENCHMARK_PATH
            });
            if module == MOLECULE_ROLE_MODULE {
                copy_relative(MOLECULE_PROPERTY_BENCHMARK_PATH);
                copy_relative(
                    "amphora-molecule-role-ranker/reference/mvp20/data/molecule_library.json",
                );
            }

            run_module_data(&root, module, ModuleDataAction::Acquire).unwrap();
            run_module_data(&root, module, ModuleDataAction::Verify).unwrap();
            run_module_data(&root, module, ModuleDataAction::Build).unwrap();
            lock_module_benchmark(&root, module, None).unwrap();
            run_locked_module_benchmark(&root, module).unwrap();

            let identity = ensure_local_identity(&root).unwrap();
            let mut trust = TrustStore::default();
            trust
                .insert(
                    identity.key_id.clone(),
                    identity.signing_key.verifying_key().to_bytes(),
                )
                .unwrap();
            let receipts = load_local_receipts(&root).unwrap();
            assert_eq!(receipts.len(), 5);
            assert!(receipts.iter().any(|receipt| {
                receipt
                    .metrics
                    .get("automatic_demotion")
                    .and_then(Value::as_bool)
                    == Some(true)
            }));
            for receipt in receipts {
                receipt.verify_signature(&trust).unwrap();
            }
            let replay = replay_module_benchmark_receipt(&root, module).unwrap();
            assert_eq!(replay["replay_status"], "CURRENT");
            assert_eq!(replay["effective_phase"], "PHASE_0");
            let benchmark_path = if module == MOLECULE_PROPERTY_MODULE {
                MOLECULE_PROPERTY_BENCHMARK_PATH
            } else {
                MOLECULE_ROLE_BENCHMARK_PATH
            };
            fs::write(root.join(benchmark_path), b"{}\n").unwrap();
            let stale = replay_module_benchmark_receipt(&root, module).unwrap();
            assert_eq!(stale["replay_status"], "DEMOTED_STALE_OR_MISMATCHED");
            assert_eq!(stale["effective_phase"], "PHASE_0");
            fs::remove_dir_all(root).unwrap();
        }
    }

    #[test]
    fn source_and_system_split_leakage_is_detected() {
        let split = SplitManifestV1 {
            schema: amphora_core::SPLIT_MANIFEST_SCHEMA.into(),
            split_id: "split".into(),
            dataset_hash: "a".repeat(64),
            assignment_method: "test".into(),
            assignments: vec![
                amphora_core::SplitAssignmentV1 {
                    row_id: "row-1".into(),
                    split: "TRAIN".into(),
                    source: "source".into(),
                    family: "family".into(),
                    scaffold: "system".into(),
                    time: "time-1".into(),
                    lot: "lot-1".into(),
                },
                amphora_core::SplitAssignmentV1 {
                    row_id: "row-2".into(),
                    split: "EXTERNAL_HOLDOUT".into(),
                    source: "source".into(),
                    family: "family".into(),
                    scaffold: "system".into(),
                    time: "time-2".into(),
                    lot: "lot-2".into(),
                },
            ],
        };
        assert_eq!(split_leakage_count(&split), 1);
    }

    #[test]
    fn corrosion_phase_gates_are_calculated_from_locked_results() {
        let audit = ModuleDataAudit {
            module_id: CORROSION_MODULE.into(),
            artifact_hashes: BTreeMap::new(),
            rights: Vec::new(),
            planned_sources: 3,
            available_sources: 3,
            eligible_sources: 3,
            quarantined_sources: 0,
            missing_sources: 0,
            missing_files: 0,
            mismatched_files: 0,
            reported_rows: 300,
            eligible_rows: 300,
            eligible_systems: (0..30).map(|index| format!("system-{index}")).collect(),
            eligible_studies: ["study-a", "study-b", "study-c"]
                .into_iter()
                .map(str::to_owned)
                .collect(),
            endpoint_counts: BTreeMap::from([
                ("rust_creep_mm".into(), 100),
                ("wet_adhesion_mpa".into(), 100),
            ]),
        };
        let split = SplitManifestV1 {
            schema: amphora_core::SPLIT_MANIFEST_SCHEMA.into(),
            split_id: "sealed-external".into(),
            dataset_hash: "a".repeat(64),
            assignment_method: "independent evaluator sealed systems".into(),
            assignments: (0..10)
                .map(|index| amphora_core::SplitAssignmentV1 {
                    row_id: format!("row-{index}"),
                    split: "SEALED_EXTERNAL_HOLDOUT".into(),
                    source: format!("source-{index}"),
                    family: "family".into(),
                    scaffold: format!("system-{index}"),
                    time: "sealed".into(),
                    lot: "panel".into(),
                })
                .collect(),
        };
        let lift = json!({
            "model_metric": 0.80,
            "baseline_metric": 0.65,
            "absolute_lift": 0.15,
            "confidence_summary": {
                "confidence_interval_95": {"lower": 0.02, "upper": 0.24, "method": "paired_study_block_bootstrap"}
            },
            "calibration_summary": {"expected_calibration_error": 0.08},
            "continuous_endpoint_results": {
                "rust_creep": {"error_delta": -0.1},
                "wet_adhesion": {"error_delta": 0.0}
            },
            "model_registry": [
                "majority_or_constant",
                "latest_impedance_expert_threshold",
                "monotone_log_linear_degradation",
                "deterministic_gam",
                "deterministic_boosted_stumps"
            ],
            "hostile_null_suite": {"results": [
                {"name": "label_shuffle_null", "rejected": true, "leakage_detected": false},
                {"name": "time_reversal_null", "status": "REJECTED", "leakage_detected": false},
                {"name": "source_and_system_leakage_null", "rejected": true, "leakage_detected": false}
            ]},
            "independent_review": {
                "status": "ACCEPTED",
                "signature_verified": true,
                "identity_bound": true,
                "benchmark_hash_bound": true,
                "reviewer_independent": true
            }
        });
        let result = corrosion_benchmark_result(&audit, &split, &lift).unwrap();
        assert!(result.passed);
        assert_eq!(result.metrics["calibration_error"], json!(0.08));
        assert_eq!(
            result.details["gates"]["locked_model_and_hostile_null_suite_complete"],
            true
        );
    }

    #[test]
    fn missing_corrosion_evidence_calculates_failed_not_placeholder_passes() {
        let root = super::super::workspace_root();
        let audit = audit_module_data(&root, CORROSION_MODULE).unwrap();
        let split: SplitManifestV1 =
            serde_json::from_value(read_json(&root.join(CORROSION_SPLIT_PATH)).unwrap()).unwrap();
        let lift = read_json(&root.join(CORROSION_LIFT_PATH)).unwrap();
        let result = corrosion_benchmark_result(&audit, &split, &lift).unwrap();
        assert!(!result.passed);
        assert_eq!(result.metrics["calibration_error"], Value::Null);
        assert_eq!(
            result.metrics["hostile_null_suite_status"],
            "INCOMPLETE_OR_NOT_AVAILABLE"
        );
        assert_eq!(result.metrics["untouched_external_system_count"], 0);
    }

    #[test]
    fn receipt_identity_binds_metrics_added_after_construction() {
        let mut receipt = new_receipt(
            "module",
            "command",
            false,
            EvidenceTier::SyntheticDiagnostic,
            DecisionUse::AuditOnly,
            "a".repeat(64),
            "b".repeat(64),
            BTreeMap::from([("artifact".into(), "c".repeat(64))]),
            json!({"detail": true}),
            BTreeMap::new(),
            Vec::new(),
        )
        .unwrap();
        receipt
            .metrics
            .insert("source_genesis_hash".into(), Value::String("d".repeat(64)));
        bind_receipt_identity(&mut receipt).unwrap();
        let first = receipt.receipt_id.clone();
        receipt
            .metrics
            .insert("source_genesis_hash".into(), Value::String("e".repeat(64)));
        bind_receipt_identity(&mut receipt).unwrap();
        assert_ne!(first, receipt.receipt_id);
    }

    #[test]
    fn run_preflight_verifies_matching_raw_files_and_rejects_mismatch() {
        let root = temporary_workspace("raw-preflight");
        let raw_path = root.join("measurement.csv");
        fs::write(&raw_path, b"time,value\n0,70\n").unwrap();
        let hashes = BTreeMap::from([(
            "measurement.csv".into(),
            raw_file_sha256(&raw_path).unwrap(),
        )]);
        assert_eq!(verify_raw_file_hashes(&hashes, &root).unwrap(), 1);

        let mismatched = BTreeMap::from([("measurement.csv".into(), "0".repeat(64))]);
        assert!(verify_raw_file_hashes(&mismatched, &root).is_err());
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn scientific_model_preflight_is_unsigned_and_state_free_for_all_modules() {
        let source_root = super::super::workspace_root();
        let root = temporary_workspace("scientific-preflight");
        for module in [VISCOSITY_MODULE, SOLVENCY_MODULE, EIS_CORROSION_MODULE] {
            let (_, split_path, _) = module_paths(module).unwrap();
            let input = root.join(format!("{module}-split.json"));
            fs::copy(source_root.join(split_path), &input).unwrap();
            let report = preflight_model(module, ModelPreflightKind::Split, &input, None).unwrap();
            assert_eq!(report.status, "VALID");
            assert!(!report.signed_input);
            assert!(!report.artifacts_written);
            assert!(!report.identities_written);
            assert!(!report.receipts_written);
            assert!(!root.join(".amphora").exists());
        }
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn scientific_locked_benchmarks_auto_demote_and_sign_receipts() {
        let source_root = super::super::workspace_root();
        let root = temporary_workspace("scientific-locked-benchmark");
        let copy_relative = |relative: &str| {
            let destination = root.join(relative);
            fs::create_dir_all(destination.parent().unwrap()).unwrap();
            fs::copy(source_root.join(relative), destination).unwrap();
        };
        copy_relative(REGISTRY_PATH);
        for module in [VISCOSITY_MODULE, SOLVENCY_MODULE, EIS_CORROSION_MODULE] {
            let (source_path, split_path, lock_path) = module_paths(module).unwrap();
            for relative in [source_path, split_path, lock_path] {
                copy_relative(relative);
            }
            let census = read_json(&root.join(source_path)).unwrap();
            let local_manifest = census
                .pointer("/sources/0/local_manifest")
                .and_then(Value::as_str)
                .unwrap();
            copy_relative(local_manifest);
        }

        assert!(!root.join(".amphora").exists());
        for module in [VISCOSITY_MODULE, SOLVENCY_MODULE, EIS_CORROSION_MODULE] {
            run_locked_scientific_model_benchmark(&root, module).unwrap();
        }
        let identity = ensure_local_identity(&root).unwrap();
        let mut trust = TrustStore::default();
        trust
            .insert(
                identity.key_id.clone(),
                identity.signing_key.verifying_key().to_bytes(),
            )
            .unwrap();
        let receipts = load_local_receipts(&root).unwrap();
        assert_eq!(receipts.len(), 3);
        for receipt in receipts {
            assert!(!receipt.passed);
            assert_eq!(receipt.decision_use_ceiling, DecisionUse::AuditOnly);
            assert_eq!(
                receipt
                    .metrics
                    .get("details")
                    .and_then(|details| details.get("automatic_demotion"))
                    .and_then(Value::as_bool),
                Some(true)
            );
            receipt.verify_signature(&trust).unwrap();
        }
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn qualification_preflight_is_read_only_and_protocol_receipt_verifies() {
        let source_root = super::super::workspace_root();
        let root = temporary_workspace("protocol-workflow");
        fs::copy(source_root.join(REGISTRY_PATH), root.join(REGISTRY_PATH)).unwrap();
        fs::copy(
            source_root.join(BENCHMARK_LOCK_PATH),
            root.join(BENCHMARK_LOCK_PATH),
        )
        .unwrap();
        let qualification = root.join("qualification.json");
        let invalid_qualification = root.join("invalid-qualification.json");
        let source_ledger = root.join("source-landscape.json");
        let output = root.join("protocol.json");
        let mut invalid_value = valid_qualification_value();
        invalid_value["unknown"] = Value::Bool(true);
        fs::write(
            &invalid_qualification,
            serde_json::to_vec_pretty(&invalid_value).unwrap(),
        )
        .unwrap();
        fs::write(
            &qualification,
            serde_json::to_vec_pretty(&valid_qualification_value()).unwrap(),
        )
        .unwrap();
        fs::write(&source_ledger, b"{\"source\":\"test-only\"}\n").unwrap();

        assert!(preflight_pot_life(
            PotLifePreflightKind::ScaleQualification,
            &invalid_qualification,
            None,
        )
        .is_err());
        assert!(!root.join(".amphora").exists());

        let report = preflight_pot_life(
            PotLifePreflightKind::ScaleQualification,
            &qualification,
            None,
        )
        .unwrap();
        assert_eq!(report.status, "VALID");
        assert!(!report.signed);
        assert!(!root.join(".amphora").exists());

        run_pot_life(
            &root,
            PotLifeArgs {
                command: PotLifeCommand::Protocol {
                    qualification: qualification.clone(),
                    source_ledger: source_ledger.clone(),
                    generated_on: "2026-07-17".into(),
                    mixing_method: "LOCKED_POWER_MIXER_SEQUENCE".into(),
                    output: Some(output.clone()),
                },
            },
        )
        .unwrap();
        let immutable_bytes = fs::read(&output).unwrap();
        assert!(run_pot_life(
            &root,
            PotLifeArgs {
                command: PotLifeCommand::Protocol {
                    qualification,
                    source_ledger,
                    generated_on: "2026-07-18".into(),
                    mixing_method: "LOCKED_POWER_MIXER_SEQUENCE".into(),
                    output: Some(output.clone()),
                },
            },
        )
        .is_err());
        assert_eq!(fs::read(&output).unwrap(), immutable_bytes);

        let identity = ensure_local_identity(&root).unwrap();
        let mut trust = TrustStore::default();
        trust
            .insert(
                identity.key_id.clone(),
                identity.signing_key.verifying_key().to_bytes(),
            )
            .unwrap();
        let receipts = load_local_receipts(&root).unwrap();
        assert_eq!(receipts.len(), 1);
        receipts[0].verify_signature(&trust).unwrap();
        fs::remove_dir_all(root).unwrap();
    }
}
#[test]
fn phase0_issuance_outputs_do_not_change_local_benchmark_genesis() {
    for path in [
        "config/program/phase0-decision-report.v2.json",
        "amphora-example/evidence/phase0/benchmark/result.v1.json",
        "amphora-example/evidence/phase0/receipts/evaluation.v1.dsse.json",
        "amphora-example/movement/ledger.v1.json",
        "amphora-example/movement/events/event.json",
    ] {
        assert!(phase0_generated_file(Path::new(path)));
    }
    assert!(!phase0_generated_file(Path::new(
        "amphora-example/evidence/phase0/benchmark/benchmark-lock.v1.json"
    )));
}
