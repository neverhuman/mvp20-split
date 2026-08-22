use amphora_assurance_capabilities::CroProtocolPackageV2;
use amphora_core::{
    jcs_bytes, parse_json_strict, prove_read_only, stable_hash, verify_dsse,
    verify_toolchain_profile, CampaignExecutionProfileV1, CampaignExecutionReceiptV1,
    CampaignIndependentReviewReceiptV1, CampaignRejectedCandidateV1, CampaignStageCountsV1,
    CompoundCampaignResultV1, CompoundCampaignResultV2, CompoundCampaignV1, CompoundCampaignV2,
    DsseEnvelope, GeneratedCompoundV1, ReactionGrammarCorpusV1, ReactionSplitManifestV1,
    TrustStore, COMPOUND_CAMPAIGN_RESULT_SCHEMA,
};
use amphora_engine::EnginePool;
use amphora_formulation_capabilities::EquivalentBalanceV1;
use anyhow::{anyhow, bail, Context, Result};
use clap::{Args, Subcommand};
use ed25519_dalek::SigningKey;
use serde::{de::DeserializeOwned, Deserialize};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};
use std::fs;
use std::path::{Component, Path, PathBuf};
use std::process::Command;
use std::thread;
use std::time::Instant;

const MOLECULE_MODULES: [&str; 7] = [
    "amphora-candidate-contract",
    "amphora-source-ledger",
    "amphora-molecule-generator",
    "amphora-molecule-property",
    "amphora-molecule-design-gate",
    "amphora-model-card-authority",
    "amphora-run-provenance",
];
const FORMULATION_MODULES: [&str; 4] = [
    "amphora-candidate-contract",
    "amphora-formulation-arithmetic",
    "amphora-cro-protocol-packager",
    "amphora-run-provenance",
];
const EVIDENCE_MODULES: [&str; 4] = [
    "amphora-evidence-intake-validator",
    "amphora-redteam-audit",
    "amphora-report-packager",
    "amphora-run-provenance",
];
const REPORT_CARD_MODULES: [&str; 12] = [
    "amphora-candidate-contract",
    "amphora-source-ledger",
    "amphora-molecule-generator",
    "amphora-molecule-property",
    "amphora-molecule-design-gate",
    "amphora-model-card-authority",
    "amphora-run-provenance",
    "amphora-formulation-arithmetic",
    "amphora-cro-protocol-packager",
    "amphora-evidence-intake-validator",
    "amphora-redteam-audit",
    "amphora-report-packager",
];
const REPORT_MOLECULE_MODULES: [&str; 4] = [
    "amphora-candidate-contract",
    "amphora-molecule-generator",
    "amphora-molecule-property",
    "amphora-molecule-design-gate",
];
const REPORT_FORMULATION_MODULES: [&str; 3] = [
    "amphora-model-card-authority",
    "amphora-formulation-arithmetic",
    "amphora-cro-protocol-packager",
];
const REPORT_EVIDENCE_MODULES: [&str; 5] = [
    "amphora-source-ledger",
    "amphora-run-provenance",
    "amphora-evidence-intake-validator",
    "amphora-redteam-audit",
    "amphora-report-packager",
];

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct AuditCardManifestV1 {
    schema: String,
    set_id: String,
    authority_ceiling: String,
    compounds: Vec<AuditCardCompoundV1>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct AuditCardCompoundV1 {
    proposal_id: String,
    display_name: String,
    requested_role: String,
    smiles: String,
    chemistry_note: String,
}

#[derive(Debug, Args)]
pub struct CompoundArgs {
    #[command(subcommand)]
    command: CompoundCommand,
}

#[derive(Debug, Subcommand)]
enum CompoundCommand {
    Toolchain {
        #[command(subcommand)]
        command: ToolchainCommand,
    },
    Campaign {
        #[command(subcommand)]
        command: CampaignCommand,
    },
    /// Read-only, non-ranking compound control cards for reporting.
    AuditCards {
        #[arg(long)]
        manifest: PathBuf,
    },
    Report {
        #[command(subcommand)]
        command: ReportCommand,
    },
}

#[derive(Debug, Subcommand)]
enum ToolchainCommand {
    Verify {
        /// One of: portable, host-optimized.
        #[arg(long)]
        profile: String,
    },
}

#[derive(Debug, Subcommand)]
enum CampaignCommand {
    Run {
        #[arg(long)]
        locked: bool,
        #[arg(long)]
        manifest: PathBuf,
        #[arg(long)]
        execution_profile: Option<PathBuf>,
        #[arg(long)]
        sealed_review: Option<PathBuf>,
    },
    Verify {
        #[arg(long)]
        campaign: String,
        /// "auto" selects host parallelism; otherwise provide a concrete worker count.
        #[arg(long, default_value = "1")]
        workers: String,
    },
    Benchmark {
        #[arg(long)]
        campaign: String,
        /// Sweep configured workers and batch sizes (best effort, deterministic dry run).
        #[arg(long)]
        worker_sweep: bool,
    },
    ExportCro {
        #[arg(long)]
        campaign: String,
    },
    Review {
        #[command(subcommand)]
        command: CampaignReviewCommand,
    },
}

#[derive(Debug, Subcommand)]
enum CampaignReviewCommand {
    Export {
        #[arg(long)]
        campaign: String,
    },
    Import {
        #[arg(long)]
        campaign: String,
        #[arg(long)]
        receipt: PathBuf,
    },
}

#[derive(Debug, Subcommand)]
enum ReportCommand {
    Build {
        #[arg(long)]
        campaign: String,
    },
    Verify {
        #[arg(long)]
        campaign: String,
    },
}

pub fn run(root: &Path, args: CompoundArgs) -> Result<()> {
    match args.command {
        CompoundCommand::Toolchain { command } => match command {
            ToolchainCommand::Verify { profile } => {
                prove_read_only(root, || verify_toolchain(root, &profile))
            }
        },
        CompoundCommand::Campaign { command } => match command {
            CampaignCommand::Run {
                locked,
                manifest,
                execution_profile,
                sealed_review,
            } => run_campaign(
                root,
                &manifest,
                locked,
                execution_profile.as_deref(),
                sealed_review.as_deref(),
            ),
            CampaignCommand::Verify { campaign, workers } => {
                prove_read_only(root, || verify_campaign(root, &campaign, &workers))
            }
            CampaignCommand::Benchmark {
                campaign,
                worker_sweep,
            } => prove_read_only(root, || benchmark_campaign(root, &campaign, worker_sweep)),
            CampaignCommand::ExportCro { campaign } => export_cro(root, &campaign),
            CampaignCommand::Review { command } => match command {
                CampaignReviewCommand::Export { campaign } => {
                    export_campaign_review(root, &campaign)
                }
                CampaignReviewCommand::Import { campaign, receipt } => {
                    import_campaign_review(root, &campaign, &receipt)
                }
            },
        },
        CompoundCommand::AuditCards { manifest } => audit_cards(root, &manifest),
        CompoundCommand::Report { command } => match command {
            ReportCommand::Build { campaign } => build_report(root, &campaign),
            ReportCommand::Verify { campaign } => {
                prove_read_only(root, || verify_report(root, &campaign))
            }
        },
    }
}

fn verify_toolchain(root: &Path, profile: &str) -> Result<()> {
    let manifest = verify_toolchain_profile(root, profile)?;
    println!(
        "{}",
        serde_json::to_string(&json!({
            "schema": "amphora.toolchain-verification.v1",
            "profile_id": manifest.profile_id,
            "manifest_jcs_sha256": manifest.manifest_payload_jcs_sha256,
            "installed_tree_sha256": manifest.installed_tree_sha256,
            "verified": true,
        }))?
    );
    Ok(())
}

fn audit_cards(root: &Path, manifest_arg: &Path) -> Result<()> {
    let manifest_path = rooted(root, manifest_arg)?;
    let manifest: AuditCardManifestV1 = read_json(&manifest_path)?;
    if manifest.schema != "amphora.compound-audit-card-set.v1"
        || manifest.set_id.trim().is_empty()
        || manifest.authority_ceiling != "AUDIT_ONLY"
        || manifest.compounds.len() != 20
    {
        bail!("audit-card manifest must contain exactly 20 AUDIT_ONLY compounds");
    }
    let mut ids = BTreeSet::new();
    let mut structures = BTreeSet::new();
    for compound in &manifest.compounds {
        if compound.proposal_id.trim().is_empty()
            || compound.display_name.trim().is_empty()
            || compound.smiles.trim().is_empty()
            || compound.chemistry_note.trim().is_empty()
            || !matches!(
                compound.requested_role.as_str(),
                "EPOXIDE_RESIN" | "REACTIVE_AMINE_HARDENER"
            )
            || !ids.insert(compound.proposal_id.as_str())
            || !structures.insert(compound.smiles.as_str())
        {
            bail!("audit-card compounds require unique IDs and structures with valid roles");
        }
    }

    let engine = EnginePool::new(root, 1)?;
    let started = Instant::now();
    let mut cards = Vec::with_capacity(manifest.compounds.len());
    let mut first_hashes = Vec::with_capacity(manifest.compounds.len());
    for (index, compound) in manifest.compounds.iter().enumerate() {
        let (result_hash, module_results) =
            evaluate_audit_card(&engine, &manifest.set_id, compound, index as u64 + 1)?;
        first_hashes.push(result_hash.clone());
        cards.push(json!({
            "proposal_id": compound.proposal_id,
            "display_name": compound.display_name,
            "requested_role": compound.requested_role,
            "smiles": compound.smiles,
            "chemistry_note": compound.chemistry_note,
            "source_status": "UNMADE_PRECAMPAIGN_AUDIT_PROBE",
            "result_sha256": result_hash,
            "module_results": module_results,
            "final_disposition": "BLOCKED_PRECAMPAIGN",
            "final_score_0_1": Value::Null,
            "rank": Value::Null,
        }));
    }
    let elapsed = started.elapsed();

    let mut replay_hashes = Vec::with_capacity(manifest.compounds.len());
    for (index, compound) in manifest.compounds.iter().enumerate() {
        let (result_hash, _) =
            evaluate_audit_card(&engine, &manifest.set_id, compound, index as u64 + 1)?;
        replay_hashes.push(result_hash);
    }
    if first_hashes != replay_hashes {
        bail!("audit-card clean replay was not byte-stable");
    }
    let seconds = elapsed.as_secs_f64();
    let compounds_per_second = if seconds > 0.0 {
        manifest.compounds.len() as f64 / seconds
    } else {
        0.0
    };
    println!(
        "{}",
        serde_json::to_string_pretty(&json!({
            "schema": "amphora.compound-audit-card-result.v1",
            "set_id": manifest.set_id,
            "authority_ceiling": "AUDIT_ONLY",
            "production_scientific_ranking_enabled": false,
            "card_count": cards.len(),
            "module_count_per_card": REPORT_CARD_MODULES.len(),
            "measurement": {
                "worker_count": 1,
                "audited_compounds": cards.len(),
                "engine_candidate_evaluations_per_pass": cards.len() * 3,
                "module_envelopes_per_pass": cards.len() * REPORT_CARD_MODULES.len(),
                "control_plane_pass_elapsed_ns": elapsed.as_nanos(),
                "compounds_per_second": compounds_per_second,
                "clean_replay_passes": 2,
                "all_result_hashes_identical_on_replay": true,
                "scope": "control-plane traversal; exact RDKit chemistry was unavailable"
            },
            "cards": cards,
        }))?
    );
    Ok(())
}

fn evaluate_audit_card(
    engine: &EnginePool,
    set_id: &str,
    compound: &AuditCardCompoundV1,
    seed: u64,
) -> Result<(String, Vec<Value>)> {
    let molecule_role = match compound.requested_role.as_str() {
        "EPOXIDE_RESIN" => "resin",
        "REACTIVE_AMINE_HARDENER" => "hardener",
        _ => bail!("unsupported audit-card role"),
    };
    let molecule = json!({
        "candidate_id": compound.proposal_id,
        "candidate_type": "molecule",
        "context": {"campaign_authority": "AUDIT_ONLY", "report_probe": true},
        "evidence_refs": {},
        "molecule": {
            "role": molecule_role,
            "smiles": compound.smiles,
            "source_status": "UNMADE_PRECAMPAIGN_AUDIT_PROBE"
        }
    });
    let formulation = json!({
        "candidate_id": format!("{}-pair", compound.proposal_id),
        "candidate_type": "formulation",
        "context": {"campaign_authority": "AUDIT_ONLY", "report_probe": true},
        "evidence_refs": {},
        "formulation": {
            "part_A": {(compound.proposal_id.clone()): 100.0},
            "part_B": {"LOCKED_REFERENCE_COUNTERPART": 50.0}
        }
    });
    let evidence = json!({
        "candidate_id": format!("{}-evidence", compound.proposal_id),
        "candidate_type": "evidence_package",
        "context": {"campaign_authority": "AUDIT_ONLY", "report_probe": true},
        "evidence_refs": {
            "molecule_candidate_sha256": stable_hash(&molecule),
            "formulation_candidate_sha256": stable_hash(&formulation)
        }
    });
    let traversals = [
        (
            &molecule,
            REPORT_MOLECULE_MODULES.as_slice(),
            format!("{set_id}-{}-molecule", compound.proposal_id),
        ),
        (
            &formulation,
            REPORT_FORMULATION_MODULES.as_slice(),
            format!("{set_id}-{}-formulation", compound.proposal_id),
        ),
        (
            &evidence,
            REPORT_EVIDENCE_MODULES.as_slice(),
            format!("{set_id}-{}-evidence", compound.proposal_id),
        ),
    ];
    let mut result_hashes = Vec::with_capacity(traversals.len());
    let mut by_module = BTreeMap::new();
    for (candidate, module_ids, run_id) in traversals {
        let result = engine.score_campaign_modules(candidate, seed, &run_id, module_ids)?;
        result_hashes.push(
            result
                .pointer("/provenance/result_hash")
                .and_then(Value::as_str)
                .ok_or_else(|| anyhow!("audit-card result is missing its provenance hash"))?
                .to_owned(),
        );
        let envelopes = result
            .get("score_envelopes")
            .and_then(Value::as_array)
            .ok_or_else(|| anyhow!("audit-card result is missing module envelopes"))?;
        if envelopes.len() != module_ids.len()
            || envelopes.iter().any(|envelope| {
                envelope.get("usable_by_optimizer").and_then(Value::as_bool) != Some(false)
                    || !envelope
                        .get("objective_values")
                        .and_then(Value::as_object)
                        .is_some_and(|values| values.is_empty())
            })
        {
            bail!("audit-card traversal attempted to expose ranking authority");
        }
        for envelope in envelopes {
            let module_id = envelope
                .get("module_id")
                .and_then(Value::as_str)
                .ok_or_else(|| anyhow!("audit-card envelope is missing its module ID"))?;
            by_module.insert(
                module_id.to_owned(),
                json!({
                    "module_id": module_id,
                    "status": envelope.get("status"),
                    "score_0_1": envelope.get("score_0_1"),
                    "evidence_scope": envelope.get("evidence_scope"),
                    "usable_by_optimizer": envelope.get("usable_by_optimizer"),
                    "missing_inputs": envelope.get("missing_inputs"),
                }),
            );
        }
    }
    let ordered = REPORT_CARD_MODULES
        .iter()
        .map(|module_id| {
            by_module
                .remove(*module_id)
                .ok_or_else(|| anyhow!("audit-card traversal missed module {module_id}"))
        })
        .collect::<Result<Vec<_>>>()?;
    Ok((stable_hash(&json!(result_hashes)), ordered))
}

fn run_campaign(
    root: &Path,
    manifest_arg: &Path,
    locked: bool,
    execution_profile_arg: Option<&Path>,
    sealed_review_arg: Option<&Path>,
) -> Result<()> {
    if !locked {
        bail!("compound campaign execution requires --locked");
    }
    let manifest_path = rooted(root, manifest_arg)?;
    let campaign = load_campaign_from_manifest(&manifest_path)?;
    let execution_profile = if let Some(path) = execution_profile_arg {
        Some(parse_execution_profile(&rooted(root, path)?)?)
    } else {
        None
    };
    match campaign {
        LoadedCampaign::V1(campaign) => {
            if sealed_review_arg.is_some() {
                bail!("--sealed-review is supported only by v2 compound campaigns");
            }
            run_campaign_from_v1(root, &campaign, execution_profile.as_ref())
        }
        LoadedCampaign::V2(campaign) => run_campaign_from_v2(
            root,
            &manifest_path,
            &campaign,
            execution_profile.as_ref(),
            sealed_review_arg,
        ),
    }
}

enum LoadedCampaign {
    V1(CompoundCampaignV1),
    V2(CompoundCampaignV2),
}

fn load_campaign_from_manifest(manifest_path: &Path) -> Result<LoadedCampaign> {
    let bytes = parse_json_strict(&fs::read(manifest_path)?)?;
    let schema = bytes
        .get("schema")
        .and_then(Value::as_str)
        .ok_or_else(|| anyhow!("manifest schema is missing"))?;
    match schema {
        "amphora.compound-campaign.v1" => {
            let campaign: CompoundCampaignV1 = serde_json::from_value(bytes)?;
            campaign.validate()?;
            Ok(LoadedCampaign::V1(campaign))
        }
        "amphora.compound-campaign.v2" => {
            let campaign: CompoundCampaignV2 = serde_json::from_value(bytes)?;
            campaign.validate()?;
            Ok(LoadedCampaign::V2(campaign))
        }
        _ => bail!("unsupported compound campaign schema: {schema}"),
    }
}

fn run_campaign_from_v2(
    root: &Path,
    manifest_path: &Path,
    campaign: &CompoundCampaignV2,
    execution_profile: Option<&CampaignExecutionProfileV1>,
    sealed_review_arg: Option<&Path>,
) -> Result<()> {
    campaign.verify_bound_files(root)?;
    let execution_profile = execution_profile
        .ok_or_else(|| anyhow!("v2 compound campaign requires --execution-profile"))?;
    let profile_path = campaign
        .artifacts
        .execution_profiles
        .iter()
        .find(|binding| {
            root.join(&binding.path).is_file()
                && parse_execution_profile(&root.join(&binding.path))
                    .is_ok_and(|bound| bound.profile_id == execution_profile.profile_id)
        })
        .ok_or_else(|| anyhow!("execution profile is not bound by the v2 campaign"))?;
    profile_path.verify(root)?;

    let dsse_path = manifest_path.with_file_name(format!(
        "{}.dsse.json",
        manifest_path
            .file_stem()
            .and_then(|value| value.to_str())
            .ok_or_else(|| anyhow!("campaign manifest filename is invalid"))?
    ));
    let envelope: DsseEnvelope = read_json(&dsse_path)
        .with_context(|| "evaluator-signed v2 campaign DSSE envelope is required")?;
    let trust = v2_evaluator_trust_store(root, &campaign.evaluator_key_id)?;
    campaign.verify_evaluator_envelope(&envelope, &trust)?;

    let grammar: ReactionGrammarCorpusV1 =
        read_json(&root.join(&campaign.artifacts.ord_grammar.path))?;
    let split: ReactionSplitManifestV1 = read_json(&root.join(&campaign.artifacts.ord_split.path))?;
    let selected_toolchain = if execution_profile.rdkit_profile.contains("host-optimized") {
        &campaign.artifacts.optimized_toolchain_manifest.sha256
    } else {
        &campaign.artifacts.portable_toolchain_manifest.sha256
    };
    let _authorized_grammar = campaign.authorize_grammar(
        &envelope,
        &trust,
        &grammar,
        &split,
        &campaign.artifacts.ord_rights_receipt.sha256,
        selected_toolchain,
        &[],
    )?;

    let sealed_review = sealed_review_arg
        .ok_or_else(|| anyhow!("v2 compound campaign requires --sealed-review"))?;
    let sealed_review = rooted(root, sealed_review)?;
    if !sealed_review.is_file() {
        bail!(
            "sealed red-team suite is absent: {}",
            sealed_review.display()
        );
    }

    bail!(
        "v2 campaign inputs and campaign-only grammar are authorized, but no completed v2 scientific result exists; campaign execution remains blocked"
    )
}

fn v2_evaluator_trust_store(root: &Path, evaluator_key_id: &str) -> Result<TrustStore> {
    let path = root.join("config/phase0-trust-store.v2.json");
    let value: Value =
        read_json(&path).with_context(|| "the additive Phase-0 v2 trust store is required")?;
    let keys = value
        .get("keys")
        .and_then(Value::as_array)
        .ok_or_else(|| anyhow!("Phase-0 v2 trust store has no keys"))?;
    let mut trust = TrustStore::default();
    let mut matched = false;
    for key in keys {
        let key_id = key
            .get("key_id")
            .and_then(Value::as_str)
            .ok_or_else(|| anyhow!("Phase-0 v2 trust key has no key_id"))?;
        let roles = key
            .get("roles")
            .and_then(Value::as_array)
            .into_iter()
            .flatten()
            .filter_map(Value::as_str)
            .collect::<BTreeSet<_>>();
        let active = key.get("status").and_then(Value::as_str) == Some("ACTIVE");
        if key_id == evaluator_key_id {
            if !active || !roles.contains("PHASE0_EVALUATOR") {
                bail!("campaign evaluator key is not an active PHASE0_EVALUATOR");
            }
            matched = true;
        }
        let public = decode_hex_32(
            key.get("public_key_hex")
                .and_then(Value::as_str)
                .ok_or_else(|| anyhow!("Phase-0 v2 trust key has no public_key_hex"))?,
        )?;
        trust.insert(key_id, public)?;
        if !active {
            trust.revoke(key_id);
        }
    }
    if !matched {
        bail!("campaign evaluator key is absent from the Phase-0 v2 trust store");
    }
    Ok(trust)
}

fn parse_execution_profile(profile_path: &Path) -> Result<CampaignExecutionProfileV1> {
    let value = parse_json_strict(&fs::read(profile_path)?)?;
    let profile: CampaignExecutionProfileV1 = serde_json::from_value(value)?;
    profile.validate()?;
    Ok(profile)
}

fn run_campaign_from_v1(
    root: &Path,
    campaign: &CompoundCampaignV1,
    execution_profile: Option<&CampaignExecutionProfileV1>,
) -> Result<()> {
    campaign.validate()?;
    verify_locked_inputs(root, &campaign)?;
    let workers = execution_profile
        .and_then(|profile| profile.workers.first().copied())
        .unwrap_or(1);
    let engine = EnginePool::new(root, workers)?;
    let (packet_signing_key, packet_signer_id, packet_trust) = packet_signer(root)?;

    let mut rejects = Vec::new();
    let mut proposals = BTreeMap::new();
    let mut generation_attempts = 0_usize;
    for request in campaign
        .generation_requests
        .iter()
        .take(campaign.maximum_generation_attempts)
    {
        generation_attempts += 1;
        let seed = campaign
            .deterministic_seed
            .wrapping_add(generation_attempts as u64 - 1);
        match engine.generate_compounds(request, seed) {
            Ok(products) => {
                for product in products {
                    if proposals.contains_key(&product.product_structure_sha256) {
                        rejects.push(CampaignRejectedCandidateV1 {
                            request_id: request.request_id.clone(),
                            attempted_product: Some(product.product_structure),
                            reason: "DUPLICATE_CANONICAL_IDENTITY".into(),
                        });
                        continue;
                    }
                    let facts_value = serde_json::to_value(&product.molecule_facts)?;
                    let proposal_id =
                        format!("proposal-{}", &product.product_structure_sha256[..16]);
                    proposals.insert(
                        product.product_structure_sha256.clone(),
                        GeneratedCompoundV1 {
                            proposal_id,
                            request_id: request.request_id.clone(),
                            requested_role: request.requested_role.clone(),
                            canonical_isomeric_smiles: product.product_structure,
                            canonical_structure_sha256: product.product_structure_sha256,
                            scaffold: product.bemis_murcko_scaffold,
                            scaffold_sha256: product.scaffold_sha256,
                            molecule_facts_sha256: stable_hash(&facts_value),
                            molecule_facts: facts_value,
                            reaction_family: product.reaction_family,
                            reaction_template_sha256: product.reaction_template_sha256,
                            grammar_sha256: product.grammar_sha256,
                            source_reaction_ids: product.source_reaction_ids,
                            source_dataset_ids: product.source_dataset_ids,
                            deterministic_seed: product.deterministic_seed,
                            unmade: true,
                            authority_ceiling: "AUDIT_ONLY".into(),
                        },
                    );
                }
            }
            Err(error) => rejects.push(CampaignRejectedCandidateV1 {
                request_id: request.request_id.clone(),
                attempted_product: None,
                reason: format!("GENERATION_REJECTED:{error}"),
            }),
        }
    }
    let generated_structures = proposals.into_values().collect::<Vec<_>>();
    let epoxy_count = generated_structures
        .iter()
        .filter(|proposal| {
            proposal
                .molecule_facts
                .get("oxirane_ring_count")
                .and_then(Value::as_u64)
                .unwrap_or(0)
                > 0
        })
        .count();
    let amine_count = generated_structures
        .iter()
        .filter(|proposal| {
            proposal
                .molecule_facts
                .get("reactive_amine_hydrogen_count")
                .and_then(Value::as_u64)
                .unwrap_or(0)
                > 0
        })
        .count();
    if generated_structures.len() < campaign.cohort_thresholds.unique_structures
        || epoxy_count < campaign.cohort_thresholds.epoxide_bearing
        || amine_count < campaign.cohort_thresholds.reactive_amine_bearing
    {
        bail!(
            "generated cohort missed locked thresholds: unique={} epoxy={} amine={}",
            generated_structures.len(),
            epoxy_count,
            amine_count
        );
    }

    let pair_indexes = deterministic_pairs(&generated_structures, campaign.packet_count)?;
    let scaffold_group_count = pair_indexes
        .iter()
        .map(|(resin, hardener)| {
            (
                generated_structures[*resin].scaffold_sha256.as_str(),
                generated_structures[*hardener].scaffold_sha256.as_str(),
            )
        })
        .collect::<BTreeSet<_>>()
        .len();
    if scaffold_group_count < campaign.cohort_thresholds.scaffold_pair_groups {
        bail!("deterministic pair cohort missed the scaffold-pair threshold");
    }

    let mut module_envelope_hashes = BTreeMap::<String, Vec<String>>::new();
    for proposal in &generated_structures {
        let candidate = molecule_candidate(proposal);
        let result = engine.score_campaign_modules(
            &candidate,
            proposal.deterministic_seed,
            &format!("{}-{}", campaign.campaign_id, proposal.proposal_id),
            &MOLECULE_MODULES,
        )?;
        collect_envelope_hashes(&result, &mut module_envelope_hashes)?;
    }

    let mut pair_calculations = Vec::new();
    let mut cro_packets = Vec::new();
    for (packet_index, (resin_index, hardener_index)) in pair_indexes.iter().enumerate() {
        let resin = &generated_structures[*resin_index];
        let hardener = &generated_structures[*hardener_index];
        let resin_facts = serde_json::from_value(resin.molecule_facts.clone())?;
        let hardener_facts = serde_json::from_value(hardener.molecule_facts.clone())?;
        let balance = EquivalentBalanceV1::from_host_facts(
            &resin_facts,
            &hardener_facts,
            campaign.pairing_rule.resin_mass_g,
            campaign.pairing_rule.equivalent_ratio,
        )?;
        let pair_binding = json!({
            "campaign_id": campaign.campaign_id,
            "pair_index": packet_index + 1,
            "resin_proposal_id": resin.proposal_id,
            "resin_structure_sha256": resin.canonical_structure_sha256,
            "hardener_proposal_id": hardener.proposal_id,
            "hardener_structure_sha256": hardener.canonical_structure_sha256,
        });
        let formula_candidate = formulation_candidate(packet_index, resin, hardener, &balance);
        let result = engine.score_campaign_modules(
            &formula_candidate,
            campaign
                .deterministic_seed
                .wrapping_add(packet_index as u64),
            &format!("{}-pair-{:02}", campaign.campaign_id, packet_index + 1),
            &FORMULATION_MODULES,
        )?;
        collect_envelope_hashes(&result, &mut module_envelope_hashes)?;
        pair_calculations.push(serde_json::to_value(&balance)?);
        let blind_hash = stable_hash(&pair_binding);
        let mut packet = CroProtocolPackageV2::draft(
            &campaign.campaign_id,
            &pair_binding,
            balance,
            format!("BLIND-{}", &blind_hash[..12]),
        )?;
        packet.sign(&packet_signer_id, &packet_signing_key)?;
        packet.verify_signature(&packet_trust)?;
        cro_packets.push(serde_json::to_value(packet)?);
    }

    let evidence_candidate = json!({
        "candidate_id": format!("{}-evidence", campaign.campaign_id),
        "candidate_type": "evidence_package",
        "evidence_refs": {
            "campaign_manifest_sha256": campaign.sha256()?,
            "generated_structure_count": generated_structures.len(),
            "packet_count": cro_packets.len(),
            "authority_ceiling": "AUDIT_ONLY"
        }
    });
    let evidence_result = engine.score_campaign_modules(
        &evidence_candidate,
        campaign.deterministic_seed,
        &format!("{}-evidence", campaign.campaign_id),
        &EVIDENCE_MODULES,
    )?;
    collect_envelope_hashes(&evidence_result, &mut module_envelope_hashes)?;

    let packet_sha256 = cro_packets.iter().map(stable_hash).collect::<Vec<_>>();
    let mut result = CompoundCampaignResultV1 {
        schema: COMPOUND_CAMPAIGN_RESULT_SCHEMA.into(),
        campaign_id: campaign.campaign_id.clone(),
        campaign_manifest_sha256: campaign.sha256()?,
        stage_counts: CampaignStageCountsV1 {
            generation_attempts,
            generated_products: generated_structures.len() + rejects.len(),
            unique_valid_structures: generated_structures.len(),
            epoxide_bearing_structures: epoxy_count,
            reactive_amine_bearing_structures: amine_count,
            scaffold_pair_groups: scaffold_group_count,
            pair_calculations: pair_calculations.len(),
            cro_packets: cro_packets.len(),
            rejected_candidates: rejects.len(),
        },
        rejected_candidates: rejects,
        generated_structures,
        module_envelope_hashes,
        pair_calculations,
        cro_packets,
        packet_sha256,
        claim_locks: BTreeMap::from([
            ("NO_RANKING_AUTHORITY".into(), true),
            ("NO_SYNTHESIS_CLAIM".into(), true),
            ("NO_PROCUREMENT_AUTHORITY".into(), true),
            ("NO_SAFETY_CLAIM".into(), true),
            ("NO_EXECUTION_AUTHORITY".into(), true),
            ("UNMADE_DIGITAL_PROPOSALS".into(), true),
        ]),
        authority_ceiling: "AUDIT_ONLY".into(),
        ranks_present: false,
        production_scientific_ranking_enabled: false,
        deterministic_replay_sha256: String::new(),
    };
    result.deterministic_replay_sha256 = result.scientific_bytes_sha256()?;
    result.validate(&campaign)?;

    let directory = campaign_directory(root, &campaign.campaign_id)?;
    persist_immutable_json(&directory.join("manifest.v1.json"), &campaign)?;
    persist_immutable_json(&directory.join("result.v1.json"), &result)?;
    println!(
        "{}",
        serde_json::to_string(&json!({
            "schema": "amphora.compound-campaign-run-report.v1",
            "campaign_id": campaign.campaign_id,
            "result_sha256": stable_hash(&serde_json::to_value(&result)?),
            "generated_structures": result.generated_structures.len(),
            "cro_packets": result.cro_packets.len(),
            "authority_ceiling": "AUDIT_ONLY",
            "production_scientific_ranking_enabled": false,
        }))?
    );
    Ok(())
}

fn verify_campaign(root: &Path, campaign_id: &str, workers: &str) -> Result<()> {
    let workers = parse_workers(workers)?;
    let directory = campaign_directory(root, campaign_id)?;
    if directory.join("manifest.v2.json").is_file() {
        let (campaign, result, result_bytes) = load_v2_campaign_result(root, &directory)?;
        let envelope: DsseEnvelope = read_json(&directory.join("manifest.v2.dsse.json"))?;
        let trust = v2_evaluator_trust_store(root, &campaign.evaluator_key_id)?;
        campaign.verify_evaluator_envelope(&envelope, &trust)?;
        println!(
            "{}",
            serde_json::to_string(&json!({
                "schema": "amphora.compound-campaign-verification.v2",
                "campaign_id": campaign_id,
                "manifest_jcs_sha256": campaign.manifest_jcs_sha256,
                "result_file_sha256": raw_sha256(&result_bytes),
                "scientific_replay_sha256": result.scientific_replay_sha256,
                "verified": true,
                "workers": workers,
                "card_count": result.cards.len(),
                "pair_count": result.pair_calculations.len(),
                "cro_packet_count": result.cro_packets.len(),
                "ranks_present": false,
                "production_scientific_ranking_enabled": false,
            }))?
        );
        return Ok(());
    }
    let _engine = EnginePool::new(root, workers)?;
    let campaign: CompoundCampaignV1 = read_json(&directory.join("manifest.v1.json"))?;
    let result: CompoundCampaignResultV1 = read_json(&directory.join("result.v1.json"))?;
    verify_locked_inputs(root, &campaign)?;
    result.validate(&campaign)?;
    if result.deterministic_replay_sha256 != result.scientific_bytes_sha256()? {
        bail!("campaign scientific replay bytes are not identical");
    }
    let (_, _, trust) = packet_verifier(root)?;
    for packet in &result.cro_packets {
        let packet: CroProtocolPackageV2 = serde_json::from_value(packet.clone())?;
        packet.verify_signature(&trust)?;
    }
    println!(
        "{}",
        serde_json::to_string(&json!({
            "schema": "amphora.compound-campaign-verification.v1",
            "campaign_id": campaign_id,
            "result_sha256": stable_hash(&serde_json::to_value(&result)?),
            "scientific_replay_sha256": result.deterministic_replay_sha256,
            "verified": true,
            "workers": workers,
            "ranks_present": false,
            "production_scientific_ranking_enabled": false,
        }))?
    );
    Ok(())
}

fn benchmark_campaign(root: &Path, campaign_id: &str, worker_sweep: bool) -> Result<()> {
    let directory = campaign_directory(root, campaign_id)?;
    let (campaign, result, result_bytes) = load_v2_campaign_result(root, &directory)?;
    let execution = directory.join("execution");
    if !execution.is_dir() {
        bail!("campaign execution receipt directory is absent");
    }
    let scientific_result_sha256 = raw_sha256(&result_bytes);
    let mut receipts = Vec::new();
    for entry in fs::read_dir(&execution)? {
        let entry = entry?;
        if entry.file_type()?.is_symlink() || !entry.file_type()?.is_file() {
            bail!("campaign execution receipts must be regular files");
        }
        if entry.path().extension().and_then(|value| value.to_str()) != Some("json") {
            bail!("campaign execution directory contains a non-JSON file");
        }
        let receipt: CampaignExecutionReceiptV1 = read_exact_jcs(&entry.path())?;
        receipt.validate()?;
        if receipt.campaign_id != campaign.campaign_id
            || receipt.scientific_result_sha256 != scientific_result_sha256
        {
            bail!("execution receipt is bound to another campaign or scientific result");
        }
        receipts.push(receipt);
    }
    receipts.sort_by(|left, right| {
        (
            &left.workload_name,
            left.workers,
            left.batch_size,
            &left.cache_state,
        )
            .cmp(&(
                &right.workload_name,
                right.workers,
                right.batch_size,
                &right.cache_state,
            ))
    });
    if receipts.is_empty() {
        bail!("campaign has no execution receipts");
    }
    let rows = receipts
        .iter()
        .map(|receipt| {
            json!({
                "workload": receipt.workload_name,
                "workers": receipt.workers,
                "batch_size": receipt.batch_size,
                "cache_state": receipt.cache_state,
                "numerator": receipt.workload_numerator,
                "denominator_ns": receipt.workload_denominator_ns,
                "rate_ci95": [receipt.rate_ci95_low, receipt.rate_ci95_high],
                "peak_rss_bytes": receipt.peak_rss_bytes,
                "swap_delta": 0,
                "receipt_jcs_sha256": receipt.receipt_jcs_sha256,
            })
        })
        .collect::<Vec<_>>();

    println!(
        "{}",
        serde_json::to_string_pretty(&json!({
            "schema": "amphora.compound-campaign-benchmark-read.v1",
            "campaign_id": campaign_id,
            "worker_sweep": worker_sweep,
            "mode": "READ_ONLY_RECEIPT_REPORT",
            "scientific_replay_sha256": result.scientific_replay_sha256,
            "receipt_count": receipts.len(),
            "receipts": rows,
        }))?
    );
    Ok(())
}

fn build_report(root: &Path, campaign_id: &str) -> Result<()> {
    let directory = campaign_directory(root, campaign_id)?;
    let (_campaign, result, _) = load_v2_campaign_result(root, &directory).with_context(|| {
        "final report build refuses legacy/fixture campaigns and requires a complete v2 result"
    })?;
    if result.cards.len() != 20 || result.pair_calculations.len() != 12 {
        bail!("final report requires exactly 20 cards and 12 pair calculations");
    }
    if !directory
        .join("review/independent-review.v1.dsse.json")
        .is_file()
    {
        bail!("final report requires the imported independent campaign review receipt");
    }
    for module in [
        "amphora-molecule-property",
        "amphora-molecule-generator",
        "amphora-formulation-arithmetic",
        "amphora-cro-protocol-packager",
    ] {
        let movement = root
            .join("movement")
            .join(module)
            .join("phase0-movement.v2.json");
        if !movement.is_file() {
            bail!("final report requires the Phase-0 v2 movement for {module}");
        }
    }
    bail!(
        "verified Rust report packaging is not available until the campaign review and four movement artifacts pass; the legacy fixture writer has been retired"
    )
}

fn verify_report(root: &Path, campaign_id: &str) -> Result<()> {
    let directory = campaign_directory(root, campaign_id)?;
    let (_campaign, result, _) = load_v2_campaign_result(root, &directory)?;
    let report_path = directory.join("report.v1.json");
    if !report_path.is_file() {
        bail!(
            "compound report artifact is missing: {}",
            report_path.display()
        );
    }
    let report: Value = read_json(&report_path)?;
    if report.get("schema").and_then(Value::as_str) != Some("amphora.compound-report.v1")
        || report.get("authority_ceiling").and_then(Value::as_str) != Some("AUDIT_ONLY")
        || report
            .get("production_scientific_ranking_enabled")
            .and_then(Value::as_bool)
            != Some(false)
    {
        bail!("invalid report schema or authority ceiling");
    }
    let card_count = report
        .get("cards")
        .and_then(Value::as_array)
        .map(|cards| cards.len())
        .ok_or_else(|| anyhow!("report cards are absent"))?;
    if card_count != 20 {
        bail!("report must contain exactly 20 cards: {card_count}");
    }
    let tex = root.join("reports/epoxy-amine-phase0-implementation-review.tex");
    let pdf = root.join("reports/epoxy-amine-phase0-implementation-review.pdf");
    if !tex.is_file() || !pdf.is_file() {
        bail!("compiled report artifacts are missing");
    }
    let pdfinfo = Command::new("pdfinfo").arg(&pdf).output()?;
    if !pdfinfo.status.success() {
        bail!("pdfinfo rejected the compound report PDF");
    }
    let pdfinfo = String::from_utf8(pdfinfo.stdout)?;
    if !pdfinfo
        .lines()
        .any(|line| line.trim() == "Pages:           15")
        || !pdfinfo.lines().any(|line| {
            line.starts_with("Page size:")
                && line.contains("841.89 x 595.276 pts")
                && line.contains("A4")
        })
    {
        bail!("compound report must be exactly 15 A4 landscape pages");
    }
    let extracted = Command::new("pdftotext")
        .args(["-layout"])
        .arg(&pdf)
        .arg("-")
        .output()?;
    if !extracted.status.success() {
        bail!("pdftotext rejected the compound report PDF");
    }
    let extracted = String::from_utf8(extracted.stdout)?;
    for card in &result.cards {
        if !extracted.contains(&card.proposal_id) {
            bail!("compound report omits proposal {}", card.proposal_id);
        }
    }
    for module in amphora_core::required_compound_report_modules() {
        if !extracted.contains(module) {
            bail!("compound report omits module code {module}");
        }
    }
    for prohibited in [
        "FINAL AGGREGATE SCORE: 0",
        "FINAL AGGREGATE SCORE: 1",
        "RANK: 1",
        "execution_authorized: true",
        "production_scientific_ranking_enabled: true",
    ] {
        if extracted.contains(prohibited) {
            bail!("compound report contains prohibited claim text: {prohibited}");
        }
    }
    if !extracted.contains("FINAL AGGREGATE SCORE: NOT AUTHORIZED")
        || !extracted.contains("RANK: NONE")
    {
        bail!("compound report omits mandatory score and rank claim locks");
    }
    let verapdf = root.join("artifacts/toolchains/verapdf-1.30.2/verapdf");
    if !verapdf.is_file() {
        bail!("pinned veraPDF 1.30.2 verifier is absent");
    }
    let validation = Command::new(verapdf)
        .args(["--format", "text", "--flavour", "2u"])
        .arg(&pdf)
        .output()?;
    if !validation.status.success() || !String::from_utf8_lossy(&validation.stdout).contains("PASS")
    {
        bail!("veraPDF did not validate the report as PDF/A-2u");
    }
    println!(
        "{}",
        serde_json::to_string_pretty(&json!({
            "schema": "amphora.compound-report-verification.v1",
            "campaign_id": campaign_id,
            "verified": true,
            "report": report_path,
            "tex": tex,
            "pdf": pdf,
            "generated_count": result.valid_generated_compounds.len(),
            "card_count": card_count,
            "module_outcome_rows": 29,
            "page_count": 15,
            "pdfa": "PDF/A-2u",
            "authority_ceiling": "AUDIT_ONLY",
            "production_scientific_ranking_enabled": false,
        }))?
    );
    Ok(())
}

fn export_campaign_review(root: &Path, campaign_id: &str) -> Result<()> {
    let directory = campaign_directory(root, campaign_id)?;
    let (campaign, result, result_bytes) = load_v2_campaign_result(root, &directory)?;
    let redteam = directory.join("redteam/summary.v1.json");
    if !redteam.is_file() {
        bail!("campaign red-team summary is absent");
    }
    let report_input = directory.join("review/report-input.v1.json");
    if !report_input.is_file() {
        bail!("campaign report-input binding is absent");
    }
    let request = json!({
        "schema": "amphora.compound-independent-review-request.v1",
        "campaign_id": campaign.campaign_id,
        "campaign_manifest_jcs_sha256": campaign.manifest_jcs_sha256,
        "campaign_result_sha256": raw_sha256(&result_bytes),
        "portable_toolchain_sha256": campaign.artifacts.portable_toolchain_manifest.sha256,
        "optimized_toolchain_sha256": campaign.artifacts.optimized_toolchain_manifest.sha256,
        "grammar_sha256": campaign.artifacts.ord_grammar.sha256,
        "redteam_summary_sha256": raw_sha256(&fs::read(redteam)?),
        "clean_replay_sha256": result.scientific_replay_sha256,
        "report_input_sha256": raw_sha256(&fs::read(report_input)?),
        "nonce": campaign.redteam_request_nonce,
        "authorized_reviewer_key_id": campaign.authorized_reviewer_key_id,
        "expected_authority": "AUDIT_ONLY",
        "production_scientific_ranking_enabled": false,
    });
    let output = directory.join("review/independent-review-request.v1.json");
    persist_immutable_json(&output, &request)?;
    println!(
        "{}",
        serde_json::to_string(&json!({
            "campaign_id": campaign_id,
            "review_request": output,
            "request_sha256": raw_sha256(&fs::read(&output)?),
            "authority": "AUDIT_ONLY",
        }))?
    );
    Ok(())
}

fn import_campaign_review(root: &Path, campaign_id: &str, receipt_arg: &Path) -> Result<()> {
    const PAYLOAD_TYPE: &str = "application/vnd.amphora.compound-independent-review-receipt.v1+jcs";
    let directory = campaign_directory(root, campaign_id)?;
    let (campaign, result, result_bytes) = load_v2_campaign_result(root, &directory)?;
    let receipt_path = rooted(root, receipt_arg)?;
    let envelope_bytes =
        fs::read(&receipt_path).with_context(|| format!("reading {}", receipt_path.display()))?;
    let envelope_value = parse_json_strict(&envelope_bytes)?;
    let envelope: DsseEnvelope = serde_json::from_value(envelope_value)?;
    if envelope.payload_type != PAYLOAD_TYPE {
        bail!("independent campaign review has the wrong DSSE payload type");
    }
    let trust = v2_independent_reviewer_trust_store(
        root,
        &campaign.authorized_reviewer_key_id,
        &campaign.evaluator_key_id,
    )?;
    let verified = verify_dsse(&envelope, &trust)?;
    if verified.key_id != campaign.authorized_reviewer_key_id {
        bail!("independent campaign review used an unauthorized reviewer key");
    }
    let receipt_value = parse_json_strict(&verified.payload)?;
    let receipt: CampaignIndependentReviewReceiptV1 = serde_json::from_value(receipt_value)?;
    if verified.payload != jcs_bytes(&receipt)? {
        bail!("independent campaign review payload is not exact compact JCS");
    }
    receipt.validate()?;
    let redteam = directory.join("redteam/summary.v1.json");
    let report_input = directory.join("review/report-input.v1.json");
    if receipt.reviewer_key_id != verified.key_id
        || receipt.campaign_manifest_sha256 != campaign.manifest_jcs_sha256
        || receipt.campaign_result_sha256 != raw_sha256(&result_bytes)
        || receipt.portable_toolchain_sha256
            != campaign.artifacts.portable_toolchain_manifest.sha256
        || receipt.optimized_toolchain_sha256
            != campaign.artifacts.optimized_toolchain_manifest.sha256
        || receipt.grammar_sha256 != campaign.artifacts.ord_grammar.sha256
        || receipt.redteam_summary_sha256 != raw_sha256(&fs::read(&redteam)?)
        || receipt.clean_replay_sha256 != result.scientific_replay_sha256
        || receipt.report_input_sha256 != raw_sha256(&fs::read(&report_input)?)
    {
        bail!("independent campaign review receipt bindings do not match local evidence");
    }
    let destination = directory.join("review/independent-review.v1.dsse.json");
    persist_immutable_bytes(&destination, &envelope_bytes)?;
    println!(
        "{}",
        serde_json::to_string(&json!({
            "campaign_id": campaign_id,
            "review_receipt": destination,
            "reviewer_key_id": verified.key_id,
            "authority": receipt.authority,
            "verified": true,
        }))?
    );
    Ok(())
}

fn v2_independent_reviewer_trust_store(
    root: &Path,
    reviewer_key_id: &str,
    evaluator_key_id: &str,
) -> Result<TrustStore> {
    if reviewer_key_id == evaluator_key_id {
        bail!("campaign evaluator and independent reviewer must be distinct");
    }
    let value: Value = read_json(&root.join("config/phase0-trust-store.v2.json"))?;
    let keys = value
        .get("keys")
        .and_then(Value::as_array)
        .ok_or_else(|| anyhow!("Phase-0 v2 trust store has no keys"))?;
    let mut trust = TrustStore::default();
    let mut matched = false;
    for key in keys {
        let key_id = key
            .get("key_id")
            .and_then(Value::as_str)
            .ok_or_else(|| anyhow!("Phase-0 v2 trust key has no key_id"))?;
        let roles = key
            .get("roles")
            .and_then(Value::as_array)
            .into_iter()
            .flatten()
            .filter_map(Value::as_str)
            .collect::<BTreeSet<_>>();
        let active = key.get("status").and_then(Value::as_str) == Some("ACTIVE");
        if key_id == reviewer_key_id {
            if !active || !roles.contains("PHASE0_INDEPENDENT_REVIEWER") {
                bail!("review key is not an active PHASE0_INDEPENDENT_REVIEWER");
            }
            matched = true;
        }
        let public = decode_hex_32(
            key.get("public_key_hex")
                .and_then(Value::as_str)
                .ok_or_else(|| anyhow!("Phase-0 v2 trust key has no public_key_hex"))?,
        )?;
        trust.insert(key_id, public)?;
        if !active {
            trust.revoke(key_id);
        }
    }
    if !matched {
        bail!("authorized independent reviewer is absent from the Phase-0 v2 trust store");
    }
    Ok(trust)
}

fn export_cro(root: &Path, campaign_id: &str) -> Result<()> {
    let directory = campaign_directory(root, campaign_id)?;
    if directory.join("manifest.v2.json").is_file() {
        let (_campaign, result, _) = load_v2_campaign_result(root, &directory)?;
        println!(
            "{}",
            serde_json::to_string_pretty(&json!({
                "schema": "amphora.cro-feasibility-export.v2",
                "campaign_id": campaign_id,
                "license": "CC-BY-SA-4.0",
                "attribution": "Derived reaction grammar and proposals use Open Reaction Database evidence; see packet source bindings.",
                "share_alike_required": true,
                "status": "DRAFT_FOR_CRO_FEASIBILITY_REVIEW",
                "execution_authorized": false,
                "authority_ceiling": "AUDIT_ONLY",
                "packets": result.cro_packets,
            }))?
        );
        return Ok(());
    }
    let campaign: CompoundCampaignV1 = read_json(&directory.join("manifest.v1.json"))?;
    let result: CompoundCampaignResultV1 = read_json(&directory.join("result.v1.json"))?;
    result.validate(&campaign)?;
    println!(
        "{}",
        serde_json::to_string_pretty(&json!({
            "schema": "amphora.cro-feasibility-export.v1",
            "campaign_id": campaign_id,
            "license": "CC-BY-SA-4.0",
            "attribution": "Derived reaction grammar and proposals use Open Reaction Database evidence; see packet source bindings.",
            "share_alike_required": true,
            "status": "DRAFT_FOR_CRO_FEASIBILITY_REVIEW",
            "execution_authorized": false,
            "authority_ceiling": "AUDIT_ONLY",
            "packets": result.cro_packets,
        }))?
    );
    Ok(())
}

fn verify_locked_inputs(root: &Path, campaign: &CompoundCampaignV1) -> Result<()> {
    for binding in [&campaign.feedback_snapshot, &campaign.chebi_snapshot] {
        let path = rooted(root, Path::new(&binding.catalog_path))?;
        if raw_sha256(&fs::read(&path)?) != binding.catalog_sha256 {
            bail!(
                "locked snapshot catalog hash mismatch: {}",
                binding.snapshot_id
            );
        }
    }
    let ord_manifest_path = rooted(root, Path::new(&campaign.ord_snapshot.object_manifest_path))?;
    let ord_catalog: Value = read_json(&ord_manifest_path)?;
    let ord_tree = ord_catalog
        .pointer("/acquisition_units/0/ord_git_lfs_tree")
        .ok_or_else(|| anyhow!("ORD object manifest is absent"))?;
    let objects = ord_tree
        .get("objects")
        .ok_or_else(|| anyhow!("ORD object list is absent"))?;
    if stable_hash(objects) != campaign.ord_snapshot.object_manifest_sha256
        || ord_tree.get("git_commit").and_then(Value::as_str)
            != Some(campaign.ord_snapshot.git_commit.as_str())
        || ord_tree.get("object_count").and_then(Value::as_u64)
            != Some(campaign.ord_snapshot.object_count)
        || ord_tree.get("total_bytes").and_then(Value::as_u64)
            != Some(campaign.ord_snapshot.total_bytes)
    {
        bail!("ORD object manifest binding is stale or partial");
    }
    let acquisition_receipt =
        root.join("feedback/v4/receipts/acquisition/ord_reaction_protobufs_v4.json");
    if !acquisition_receipt.is_file() {
        bail!("complete ORD Git LFS snapshot has not been acquired");
    }
    let build_manifest = rooted(root, Path::new(&campaign.rdkit_build.build_manifest_path))?;
    if raw_sha256(&fs::read(&build_manifest)?) != campaign.rdkit_build.build_manifest_sha256 {
        bail!("pinned RDKit build manifest is absent or altered");
    }
    for (path, expected) in &campaign.rdkit_build.library_sha256 {
        let path = rooted(root, Path::new(path))?;
        if raw_sha256(&fs::read(&path)?) != *expected {
            bail!("pinned RDKit library hash mismatch");
        }
    }
    let backend = amphora_rdkit_ffi::backend_status();
    if !backend.available
        || !backend.exact_version_match
        || backend.detected_version.as_deref() != Some(campaign.rdkit_build.version.as_str())
    {
        bail!("compound campaign requires the exact pinned RDKit C++ backend");
    }
    Ok(())
}

fn deterministic_pairs(
    proposals: &[GeneratedCompoundV1],
    packet_count: usize,
) -> Result<Vec<(usize, usize)>> {
    let resins = proposals
        .iter()
        .enumerate()
        .filter(|(_, proposal)| proposal.requested_role == "resin")
        .map(|(index, _)| index)
        .collect::<Vec<_>>();
    let hardeners = proposals
        .iter()
        .enumerate()
        .filter(|(_, proposal)| proposal.requested_role == "hardener")
        .map(|(index, _)| index)
        .collect::<Vec<_>>();
    let mut all = resins
        .iter()
        .flat_map(|resin| hardeners.iter().map(move |hardener| (*resin, *hardener)))
        .collect::<Vec<_>>();
    all.sort_by_key(|(resin, hardener)| {
        stable_hash(&json!({
            "resin": proposals[*resin].canonical_structure_sha256,
            "hardener": proposals[*hardener].canonical_structure_sha256,
        }))
    });
    let mut selected = Vec::new();
    let mut groups = BTreeSet::new();
    for pair in &all {
        let group = (
            proposals[pair.0].scaffold_sha256.as_str(),
            proposals[pair.1].scaffold_sha256.as_str(),
        );
        if groups.insert(group) {
            selected.push(*pair);
        }
    }
    for pair in all {
        if selected.len() == packet_count {
            break;
        }
        if !selected.contains(&pair) {
            selected.push(pair);
        }
    }
    selected.truncate(packet_count);
    if selected.len() != packet_count {
        bail!("insufficient finite resin/hardener pair combinations");
    }
    Ok(selected)
}

fn molecule_candidate(proposal: &GeneratedCompoundV1) -> Value {
    json!({
        "candidate_id": proposal.proposal_id,
        "candidate_type": "molecule",
        "context": {"campaign_authority": "AUDIT_ONLY"},
        "evidence_refs": {
            "grammar_sha256": proposal.grammar_sha256,
            "source_reaction_ids": proposal.source_reaction_ids,
        },
        "molecule": {
            "role": proposal.requested_role,
            "smiles": proposal.canonical_isomeric_smiles,
            "source_status": "UNMADE_DIGITAL_PROPOSAL"
        }
    })
}

fn formulation_candidate(
    index: usize,
    resin: &GeneratedCompoundV1,
    hardener: &GeneratedCompoundV1,
    balance: &EquivalentBalanceV1,
) -> Value {
    json!({
        "candidate_id": format!("pair-{:02}", index + 1),
        "candidate_type": "formulation",
        "context": {"campaign_authority": "AUDIT_ONLY"},
        "evidence_refs": {},
        "formulation": {
            "part_A": {(resin.proposal_id.clone()): balance.resin_mass_g},
            "part_B": {(hardener.proposal_id.clone()): balance.hardener_mass_g}
        }
    })
}

fn collect_envelope_hashes(
    result: &Value,
    output: &mut BTreeMap<String, Vec<String>>,
) -> Result<()> {
    let envelopes = result
        .get("score_envelopes")
        .and_then(Value::as_array)
        .ok_or_else(|| anyhow!("campaign module traversal returned no score envelopes"))?;
    for envelope in envelopes {
        if envelope.get("usable_by_optimizer").and_then(Value::as_bool) != Some(false)
            || !envelope
                .get("objective_values")
                .and_then(Value::as_object)
                .is_some_and(|values| values.is_empty())
        {
            bail!("campaign module attempted to emit ranking or optimizer authority");
        }
        let module_id = envelope
            .get("module_id")
            .and_then(Value::as_str)
            .ok_or_else(|| anyhow!("campaign module envelope has no module ID"))?;
        output
            .entry(module_id.into())
            .or_default()
            .push(stable_hash(envelope));
    }
    Ok(())
}

fn packet_signer(root: &Path) -> Result<(SigningKey, String, TrustStore)> {
    let key_path = std::env::var_os("AMPHORA_CRO_PACKET_SIGNING_KEY_FILE")
        .ok_or_else(|| anyhow!("AMPHORA_CRO_PACKET_SIGNING_KEY_FILE is required"))?;
    let canonical_root = fs::canonicalize(root)?;
    let canonical_key = fs::canonicalize(PathBuf::from(key_path))?;
    if canonical_key.starts_with(&canonical_root) {
        bail!("CRO packet private key must remain outside the repository");
    }
    let bytes = decode_hex_32(fs::read_to_string(canonical_key)?.trim())?;
    let signing_key = SigningKey::from_bytes(&bytes);
    let (_, _, trust) = packet_verifier(root)?;
    let public = signing_key.verifying_key().to_bytes();
    let public_hex = encode_hex(&public);
    let trust_value: Value = read_json(&root.join(".amphora/evidence/trust-store.v1.json"))?;
    let key_id = trust_value
        .get("keys")
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
        .find_map(|row| {
            (row.get("public_key_hex").and_then(Value::as_str) == Some(public_hex.as_str())
                && row.get("status").and_then(Value::as_str) == Some("TRUSTED"))
            .then(|| row.get("key_id").and_then(Value::as_str).map(str::to_owned))
            .flatten()
        });
    let key_id = key_id
        .ok_or_else(|| anyhow!("CRO packet signing key is not a trusted registered identity"))?;
    Ok((signing_key, key_id, trust))
}

fn packet_verifier(root: &Path) -> Result<(String, [u8; 32], TrustStore)> {
    let value: Value = read_json(&root.join(".amphora/evidence/trust-store.v1.json"))?;
    let mut trust = TrustStore::default();
    let mut first = None;
    for row in value
        .get("keys")
        .and_then(Value::as_array)
        .ok_or_else(|| anyhow!("host evidence trust store has no keys"))?
    {
        let key_id = row
            .get("key_id")
            .and_then(Value::as_str)
            .ok_or_else(|| anyhow!("host trust key has no ID"))?;
        let bytes = decode_hex_32(
            row.get("public_key_hex")
                .and_then(Value::as_str)
                .ok_or_else(|| anyhow!("host trust key has no public bytes"))?,
        )?;
        trust.insert(key_id, bytes)?;
        if row.get("status").and_then(Value::as_str) == Some("REVOKED") {
            trust.revoke(key_id);
        } else if first.is_none() {
            first = Some((key_id.to_owned(), bytes));
        }
    }
    let (key_id, bytes) = first.ok_or_else(|| anyhow!("host trust store has no trusted key"))?;
    Ok((key_id, bytes, trust))
}

fn campaign_directory(root: &Path, campaign_id: &str) -> Result<PathBuf> {
    if campaign_id.is_empty()
        || campaign_id.len() > 128
        || !campaign_id
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'-' | b'_'))
    {
        bail!("unsafe compound campaign identity");
    }
    Ok(root.join("artifacts/compound-campaigns").join(campaign_id))
}

fn parse_workers(raw: &str) -> Result<usize> {
    if raw == "auto" {
        let detected = thread::available_parallelism().map_err(|error| {
            anyhow!("unable to detect host parallelism for worker resolution: {error}")
        })?;
        Ok(detected.get())
    } else {
        let workers: usize = raw.parse()?;
        if workers == 0 {
            bail!("campaign verification workers must be greater than zero");
        }
        Ok(workers)
    }
}

fn persist_immutable_json<T: serde::Serialize>(path: &Path, value: &T) -> Result<()> {
    let bytes = serde_json::to_vec_pretty(value)?;
    if path.is_file() {
        if fs::read(path)? == bytes {
            return Ok(());
        }
        bail!("immutable campaign artifact conflicts: {}", path.display());
    }
    fs::create_dir_all(
        path.parent()
            .ok_or_else(|| anyhow!("campaign artifact has no parent"))?,
    )?;
    fs::write(path, bytes)?;
    Ok(())
}

fn persist_immutable_bytes(path: &Path, bytes: &[u8]) -> Result<()> {
    if path.is_file() {
        if fs::read(path)? == bytes {
            return Ok(());
        }
        bail!("immutable campaign artifact conflicts: {}", path.display());
    }
    fs::create_dir_all(
        path.parent()
            .ok_or_else(|| anyhow!("campaign artifact has no parent"))?,
    )?;
    fs::write(path, bytes)?;
    Ok(())
}

fn load_v2_campaign_result(
    root: &Path,
    directory: &Path,
) -> Result<(CompoundCampaignV2, CompoundCampaignResultV2, Vec<u8>)> {
    let manifest_path = directory.join("manifest.v2.json");
    let result_path = directory.join("result.v2.json");
    let campaign: CompoundCampaignV2 = read_exact_jcs(&manifest_path)?;
    campaign.verify_bound_files(root)?;
    let result_bytes =
        fs::read(&result_path).with_context(|| format!("reading {}", result_path.display()))?;
    let result_value = parse_json_strict(&result_bytes)?;
    let result: CompoundCampaignResultV2 = serde_json::from_value(result_value)?;
    if result_bytes != jcs_bytes(&result)? {
        bail!("v2 campaign result is not authoritative compact JCS");
    }
    result.validate(&campaign)?;
    Ok((campaign, result, result_bytes))
}

fn read_exact_jcs<T>(path: &Path) -> Result<T>
where
    T: DeserializeOwned + serde::Serialize,
{
    let bytes = fs::read(path).with_context(|| format!("reading {}", path.display()))?;
    let value = parse_json_strict(&bytes)?;
    let parsed: T =
        serde_json::from_value(value).with_context(|| format!("parsing {}", path.display()))?;
    if bytes != jcs_bytes(&parsed)? {
        bail!(
            "authoritative v2 artifact is not compact JCS: {}",
            path.display()
        );
    }
    Ok(parsed)
}

fn read_json<T: DeserializeOwned>(path: &Path) -> Result<T> {
    let bytes = fs::read(path).with_context(|| format!("reading {}", path.display()))?;
    let value = parse_json_strict(&bytes)?;
    serde_json::from_value(value).with_context(|| format!("parsing {}", path.display()))
}

fn rooted(root: &Path, path: &Path) -> Result<PathBuf> {
    if path.is_absolute() {
        return Ok(path.into());
    }
    if path
        .components()
        .any(|part| matches!(part, Component::ParentDir | Component::RootDir))
    {
        bail!("relative path escapes the workspace root");
    }
    Ok(root.join(path))
}

fn raw_sha256(bytes: &[u8]) -> String {
    let mut digest = Sha256::new();
    digest.update(bytes);
    format!("{:x}", digest.finalize())
}

fn decode_hex_32(value: &str) -> Result<[u8; 32]> {
    if value.len() != 64 {
        bail!("expected 32-byte hexadecimal key");
    }
    let mut output = [0_u8; 32];
    for (index, byte) in output.iter_mut().enumerate() {
        *byte = u8::from_str_radix(&value[index * 2..index * 2 + 2], 16)?;
    }
    Ok(output)
}

fn encode_hex(bytes: &[u8]) -> String {
    bytes.iter().map(|byte| format!("{byte:02x}")).collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    fn proposal(id: &str, role: &str, scaffold: &str) -> GeneratedCompoundV1 {
        GeneratedCompoundV1 {
            proposal_id: id.into(),
            request_id: id.into(),
            requested_role: role.into(),
            canonical_isomeric_smiles: id.into(),
            canonical_structure_sha256: stable_hash(&Value::String(id.into())),
            scaffold: scaffold.into(),
            scaffold_sha256: stable_hash(&Value::String(scaffold.into())),
            molecule_facts: json!({}),
            molecule_facts_sha256: stable_hash(&json!({})),
            reaction_family: "family".into(),
            reaction_template_sha256: "a".repeat(64),
            grammar_sha256: "b".repeat(64),
            source_reaction_ids: vec!["reaction".into()],
            source_dataset_ids: vec!["dataset".into()],
            deterministic_seed: 1,
            unmade: true,
            authority_ceiling: "AUDIT_ONLY".into(),
        }
    }

    #[test]
    fn pairing_is_deterministic_and_prefers_distinct_scaffold_groups() {
        let rows = vec![
            proposal("r1", "resin", "rs1"),
            proposal("r2", "resin", "rs2"),
            proposal("r3", "resin", "rs3"),
            proposal("h1", "hardener", "hs1"),
            proposal("h2", "hardener", "hs2"),
            proposal("h3", "hardener", "hs3"),
        ];
        let first = deterministic_pairs(&rows, 9).unwrap();
        let second = deterministic_pairs(&rows, 9).unwrap();
        assert_eq!(first, second);
        assert_eq!(first.len(), 9);
        assert_eq!(
            first
                .iter()
                .map(|(r, h)| (&rows[*r].scaffold, &rows[*h].scaffold))
                .collect::<BTreeSet<_>>()
                .len(),
            9
        );
    }

    #[test]
    fn envelope_collector_rejects_objectives_and_optimizer_use() {
        for envelope in [
            json!({"module_id":"m","usable_by_optimizer":true,"objective_values":{}}),
            json!({"module_id":"m","usable_by_optimizer":false,"objective_values":{"x":1}}),
        ] {
            let mut output = BTreeMap::new();
            assert!(
                collect_envelope_hashes(&json!({"score_envelopes":[envelope]}), &mut output)
                    .is_err()
            );
        }
    }

    #[test]
    fn report_card_lanes_cover_each_campaign_module_once() {
        let mut lane_modules = REPORT_MOLECULE_MODULES
            .iter()
            .chain(REPORT_FORMULATION_MODULES.iter())
            .chain(REPORT_EVIDENCE_MODULES.iter())
            .copied()
            .collect::<Vec<_>>();
        lane_modules.sort_unstable();
        let mut required = REPORT_CARD_MODULES.to_vec();
        required.sort_unstable();
        assert_eq!(lane_modules, required);
        assert_eq!(
            required.len(),
            required.iter().collect::<BTreeSet<_>>().len()
        );
    }
}
