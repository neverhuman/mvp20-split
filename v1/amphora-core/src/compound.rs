use crate::stable_hash;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::{BTreeMap, BTreeSet};
use std::path::{Component, Path};
use thiserror::Error;

pub const COMPOUND_CAMPAIGN_SCHEMA: &str = "amphora.compound-campaign.v1";
pub const COMPOUND_CAMPAIGN_RESULT_SCHEMA: &str = "amphora.compound-campaign-result.v1";
pub const COMPOUND_EXECUTION_PROFILE_SCHEMA: &str = "amphora.compound-execution-profile.v1";
const REQUIRED_RDKIT_VERSION: &str = "2026.03.2";
const REQUIRED_RDKIT_COMMIT: &str = "42fe8c952589bb750e27ea7f259a50b36576bfa5";
const REQUIRED_ORD_COMMIT: &str = "ddb0d25770c80a0a6fcf9948c26e1c8f828cb8ad";
const REQUIRED_ORD_SCHEMA_VERSION: &str = "0.6.3";
const REQUIRED_ORD_SCHEMA_COMMIT: &str = "0a6c92558898156f06365220d3acbe2bea0a1e69";
const REQUIRED_CAMPAIGN_MODULES: [&str; 12] = [
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

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct CampaignExecutionProfileV1 {
    pub schema: String,
    pub profile_id: String,
    pub rdkit_profile: String,
    pub workers: Vec<usize>,
    pub batch_sizes: Vec<usize>,
    pub cpu_features: Vec<String>,
    pub libraries: Vec<String>,
    pub cache_profile: String,
    pub deterministic_seed: u64,
}

impl CampaignExecutionProfileV1 {
    pub fn validate(&self) -> Result<(), CompoundCampaignError> {
        if self.schema != COMPOUND_EXECUTION_PROFILE_SCHEMA
            || self.profile_id.trim().is_empty()
            || self.rdkit_profile.trim().is_empty()
            || self.workers.is_empty()
            || self.workers.iter().any(|worker| *worker == 0)
            || self.batch_sizes.is_empty()
            || self.batch_sizes.iter().any(|size| *size == 0)
            || self.cache_profile.trim().is_empty()
            || self.deterministic_seed == 0
        {
            return Err(CompoundCampaignError::InvalidManifest);
        }
        for feature in &self.cpu_features {
            if feature.trim().is_empty() {
                return Err(CompoundCampaignError::InvalidManifest);
            }
        }
        for library in &self.libraries {
            if !library.trim().is_empty() && !require_safe_path(library).is_ok() {
                return Err(CompoundCampaignError::Path);
            }
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct CampaignSnapshotBindingV1 {
    pub snapshot_id: String,
    pub catalog_path: String,
    pub catalog_sha256: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct OrdSnapshotBindingV1 {
    pub git_commit: String,
    pub ord_schema_version: String,
    pub ord_schema_commit: String,
    pub object_manifest_path: String,
    pub object_manifest_sha256: String,
    pub object_count: u64,
    pub total_bytes: u64,
    pub acquisition_kind: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct RdkitBuildBindingV1 {
    pub version: String,
    pub git_commit: String,
    pub build_manifest_path: String,
    pub build_manifest_sha256: String,
    pub source_sha256: String,
    pub library_sha256: BTreeMap<String, String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct CampaignCohortThresholdsV1 {
    pub unique_structures: usize,
    pub epoxide_bearing: usize,
    pub reactive_amine_bearing: usize,
    pub scaffold_pair_groups: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct CampaignPairingRuleV1 {
    pub method: String,
    pub resin_mass_g: f64,
    pub equivalent_ratio: f64,
    pub deterministic_tie_break: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct CampaignGenerationRequestV1 {
    pub request_id: String,
    pub parent_structures: Vec<String>,
    pub reaction_family: String,
    pub requested_role: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct CompoundCampaignV1 {
    pub schema: String,
    pub campaign_id: String,
    pub feedback_snapshot: CampaignSnapshotBindingV1,
    pub chebi_snapshot: CampaignSnapshotBindingV1,
    pub ord_snapshot: OrdSnapshotBindingV1,
    pub rdkit_build: RdkitBuildBindingV1,
    pub deterministic_seed: u64,
    pub cohort_thresholds: CampaignCohortThresholdsV1,
    pub maximum_generation_attempts: usize,
    pub pairing_rule: CampaignPairingRuleV1,
    pub packet_count: usize,
    pub authority_ceiling: String,
    pub production_scientific_ranking_enabled: bool,
    pub generation_requests: Vec<CampaignGenerationRequestV1>,
}

impl CompoundCampaignV1 {
    pub fn validate(&self) -> Result<(), CompoundCampaignError> {
        if self.schema != COMPOUND_CAMPAIGN_SCHEMA
            || self.campaign_id.trim().is_empty()
            || self.feedback_snapshot.snapshot_id != "feedback-v4-2026-07-19"
            || self.chebi_snapshot.snapshot_id != "feedback-v3-2026-07-19"
            || self.ord_snapshot.git_commit != REQUIRED_ORD_COMMIT
            || self.ord_snapshot.ord_schema_version != REQUIRED_ORD_SCHEMA_VERSION
            || self.ord_snapshot.ord_schema_commit != REQUIRED_ORD_SCHEMA_COMMIT
            || self.ord_snapshot.acquisition_kind != "ORD_GIT_LFS_TREE"
            || self.rdkit_build.version != REQUIRED_RDKIT_VERSION
            || self.rdkit_build.git_commit != REQUIRED_RDKIT_COMMIT
            || self.authority_ceiling != "AUDIT_ONLY"
            || self.production_scientific_ranking_enabled
            || self.cohort_thresholds.unique_structures < 24
            || self.cohort_thresholds.epoxide_bearing < 8
            || self.cohort_thresholds.reactive_amine_bearing < 8
            || self.cohort_thresholds.scaffold_pair_groups < 6
            || self.packet_count != 12
            || self.maximum_generation_attempts < self.cohort_thresholds.unique_structures
            || self.generation_requests.is_empty()
            || self.generation_requests.len() > self.maximum_generation_attempts
            || self.pairing_rule.method != "CANONICAL_HASH_ROLE_SCAFFOLD_STRATA"
            || self.pairing_rule.deterministic_tie_break != "SHA256_ASCENDING"
            || !self.pairing_rule.resin_mass_g.is_finite()
            || self.pairing_rule.resin_mass_g <= 0.0
            || !self.pairing_rule.equivalent_ratio.is_finite()
            || self.pairing_rule.equivalent_ratio <= 0.0
        {
            return Err(CompoundCampaignError::InvalidManifest);
        }
        for binding in [&self.feedback_snapshot, &self.chebi_snapshot] {
            require_hash(&binding.catalog_sha256)?;
            require_safe_path(&binding.catalog_path)?;
        }
        require_hash(&self.ord_snapshot.object_manifest_sha256)?;
        require_safe_path(&self.ord_snapshot.object_manifest_path)?;
        require_hash(&self.rdkit_build.build_manifest_sha256)?;
        require_hash(&self.rdkit_build.source_sha256)?;
        require_safe_path(&self.rdkit_build.build_manifest_path)?;
        if self.ord_snapshot.object_count == 0
            || self.ord_snapshot.total_bytes == 0
            || self.rdkit_build.library_sha256.is_empty()
            || self
                .rdkit_build
                .library_sha256
                .iter()
                .any(|(path, hash)| require_safe_path(path).is_err() || require_hash(hash).is_err())
        {
            return Err(CompoundCampaignError::InvalidManifest);
        }
        let mut request_ids = BTreeSet::new();
        if self.generation_requests.iter().any(|request| {
            !request_ids.insert(request.request_id.as_str())
                || request.parent_structures.is_empty()
                || request
                    .parent_structures
                    .iter()
                    .any(|structure| structure.trim().is_empty())
                || request.reaction_family.trim().is_empty()
                || !matches!(request.requested_role.as_str(), "resin" | "hardener")
        }) {
            return Err(CompoundCampaignError::InvalidManifest);
        }
        Ok(())
    }

    pub fn sha256(&self) -> Result<String, CompoundCampaignError> {
        self.validate()?;
        Ok(stable_hash(&serde_json::to_value(self)?))
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct CampaignStageCountsV1 {
    pub generation_attempts: usize,
    pub generated_products: usize,
    pub unique_valid_structures: usize,
    pub epoxide_bearing_structures: usize,
    pub reactive_amine_bearing_structures: usize,
    pub scaffold_pair_groups: usize,
    pub pair_calculations: usize,
    pub cro_packets: usize,
    pub rejected_candidates: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct CampaignRejectedCandidateV1 {
    pub request_id: String,
    pub attempted_product: Option<String>,
    pub reason: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct GeneratedCompoundV1 {
    pub proposal_id: String,
    pub request_id: String,
    pub requested_role: String,
    pub canonical_isomeric_smiles: String,
    pub canonical_structure_sha256: String,
    pub scaffold: String,
    pub scaffold_sha256: String,
    pub molecule_facts: Value,
    pub molecule_facts_sha256: String,
    pub reaction_family: String,
    pub reaction_template_sha256: String,
    pub grammar_sha256: String,
    pub source_reaction_ids: Vec<String>,
    pub source_dataset_ids: Vec<String>,
    pub deterministic_seed: u64,
    pub unmade: bool,
    pub authority_ceiling: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct CompoundCampaignResultV1 {
    pub schema: String,
    pub campaign_id: String,
    pub campaign_manifest_sha256: String,
    pub stage_counts: CampaignStageCountsV1,
    pub rejected_candidates: Vec<CampaignRejectedCandidateV1>,
    pub generated_structures: Vec<GeneratedCompoundV1>,
    pub module_envelope_hashes: BTreeMap<String, Vec<String>>,
    pub pair_calculations: Vec<Value>,
    pub cro_packets: Vec<Value>,
    pub packet_sha256: Vec<String>,
    pub claim_locks: BTreeMap<String, bool>,
    pub authority_ceiling: String,
    pub ranks_present: bool,
    pub production_scientific_ranking_enabled: bool,
    pub deterministic_replay_sha256: String,
}

impl CompoundCampaignResultV1 {
    pub fn validate(&self, campaign: &CompoundCampaignV1) -> Result<(), CompoundCampaignError> {
        campaign.validate()?;
        if self.schema != COMPOUND_CAMPAIGN_RESULT_SCHEMA
            || self.campaign_id != campaign.campaign_id
            || self.campaign_manifest_sha256 != campaign.sha256()?
            || self.authority_ceiling != "AUDIT_ONLY"
            || self.ranks_present
            || self.production_scientific_ranking_enabled
            || self.claim_locks.is_empty()
            || self.claim_locks.values().any(|value| !value)
            || [
                "NO_RANKING_AUTHORITY",
                "NO_SYNTHESIS_CLAIM",
                "NO_PROCUREMENT_AUTHORITY",
                "NO_SAFETY_CLAIM",
                "NO_EXECUTION_AUTHORITY",
                "UNMADE_DIGITAL_PROPOSALS",
            ]
            .iter()
            .any(|lock| self.claim_locks.get(*lock) != Some(&true))
            || self.stage_counts.unique_valid_structures != self.generated_structures.len()
            || self.stage_counts.rejected_candidates != self.rejected_candidates.len()
            || self.stage_counts.pair_calculations != self.pair_calculations.len()
            || self.stage_counts.cro_packets != self.cro_packets.len()
            || self.packet_sha256.len() != self.cro_packets.len()
            || self.generated_structures.len() < campaign.cohort_thresholds.unique_structures
            || self.stage_counts.epoxide_bearing_structures
                < campaign.cohort_thresholds.epoxide_bearing
            || self.stage_counts.reactive_amine_bearing_structures
                < campaign.cohort_thresholds.reactive_amine_bearing
            || self.stage_counts.scaffold_pair_groups
                < campaign.cohort_thresholds.scaffold_pair_groups
            || self.pair_calculations.len() != campaign.packet_count
            || self.cro_packets.len() != campaign.packet_count
        {
            return Err(CompoundCampaignError::InvalidResult);
        }
        let expected_modules = REQUIRED_CAMPAIGN_MODULES
            .into_iter()
            .collect::<BTreeSet<_>>();
        let observed_modules = self
            .module_envelope_hashes
            .keys()
            .map(String::as_str)
            .collect::<BTreeSet<_>>();
        if observed_modules != expected_modules
            || self.module_envelope_hashes.values().any(|hashes| {
                hashes.is_empty() || hashes.iter().any(|hash| require_hash(hash).is_err())
            })
            || self.pair_calculations.iter().any(|balance| {
                balance.get("schema").and_then(Value::as_str)
                    != Some("amphora.equivalent-balance.v1")
                    || balance.get("authority_ceiling").and_then(Value::as_str)
                        != Some("AUDIT_ONLY")
                    || balance
                        .get("candidate_property_overrides_accepted")
                        .and_then(Value::as_bool)
                        != Some(false)
                    || balance.get("ranking_eligible").and_then(Value::as_bool) != Some(false)
            })
        {
            return Err(CompoundCampaignError::InvalidResult);
        }
        let mut identities = BTreeSet::new();
        for proposal in &self.generated_structures {
            if proposal.proposal_id.trim().is_empty()
                || !matches!(proposal.requested_role.as_str(), "resin" | "hardener")
                || !identities.insert(proposal.canonical_structure_sha256.as_str())
                || stable_hash(&proposal.molecule_facts) != proposal.molecule_facts_sha256
                || proposal
                    .molecule_facts
                    .get("canonical_structure_sha256")
                    .and_then(Value::as_str)
                    != Some(proposal.canonical_structure_sha256.as_str())
                || !proposal.unmade
                || proposal.authority_ceiling != "AUDIT_ONLY"
                || proposal.source_reaction_ids.is_empty()
                || proposal.source_dataset_ids.is_empty()
            {
                return Err(CompoundCampaignError::InvalidResult);
            }
            for hash in [
                &proposal.canonical_structure_sha256,
                &proposal.scaffold_sha256,
                &proposal.molecule_facts_sha256,
                &proposal.reaction_template_sha256,
                &proposal.grammar_sha256,
            ] {
                require_hash(hash)?;
            }
        }
        for (packet, expected_hash) in self.cro_packets.iter().zip(&self.packet_sha256) {
            require_hash(expected_hash)?;
            if stable_hash(packet) != *expected_hash
                || packet.get("status").and_then(Value::as_str)
                    != Some("DRAFT_FOR_CRO_FEASIBILITY_REVIEW")
                || packet.get("execution_authorized").and_then(Value::as_bool) != Some(false)
                || packet.get("authority_ceiling").and_then(Value::as_str) != Some("AUDIT_ONLY")
                || !packet.get("signature").is_some_and(Value::is_object)
            {
                return Err(CompoundCampaignError::InvalidResult);
            }
        }
        let value = serde_json::to_value(self)?;
        if contains_forbidden_authority(&value) {
            return Err(CompoundCampaignError::ForbiddenAuthority);
        }
        require_hash(&self.deterministic_replay_sha256)?;
        Ok(())
    }

    pub fn scientific_bytes_sha256(&self) -> Result<String, CompoundCampaignError> {
        let mut replay = self.clone();
        replay.deterministic_replay_sha256.clear();
        Ok(stable_hash(&serde_json::to_value(replay)?))
    }
}

#[derive(Debug, Error)]
pub enum CompoundCampaignError {
    #[error("invalid locked compound campaign manifest")]
    InvalidManifest,
    #[error("invalid compound campaign result")]
    InvalidResult,
    #[error("compound campaign contains forbidden ranking, objective, procurement, synthesis, or execution authority")]
    ForbiddenAuthority,
    #[error("compound campaign SHA-256 is invalid")]
    Hash,
    #[error("compound campaign path is unsafe")]
    Path,
    #[error("compound campaign JSON: {0}")]
    Json(#[from] serde_json::Error),
}

fn require_hash(value: &str) -> Result<(), CompoundCampaignError> {
    if value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        Ok(())
    } else {
        Err(CompoundCampaignError::Hash)
    }
}

fn require_safe_path(value: &str) -> Result<(), CompoundCampaignError> {
    let path = Path::new(value);
    if value.trim().is_empty()
        || path.is_absolute()
        || path
            .components()
            .any(|part| matches!(part, Component::ParentDir | Component::RootDir))
    {
        Err(CompoundCampaignError::Path)
    } else {
        Ok(())
    }
}

fn contains_forbidden_authority(value: &Value) -> bool {
    match value {
        Value::Object(object) => object.iter().any(|(key, value)| {
            matches!(
                key.as_str(),
                "rank"
                    | "ranks"
                    | "ranked_candidates"
                    | "optimizer_objective"
                    | "optimizer_objectives"
                    | "synthesis_recommendation"
                    | "procurement_decision"
            ) || (key == "execution_authorized" && value.as_bool() != Some(false))
                || contains_forbidden_authority(value)
        }),
        Value::Array(values) => values.iter().any(contains_forbidden_authority),
        _ => false,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn digest(label: &str) -> String {
        stable_hash(&Value::String(label.into()))
    }

    fn campaign() -> CompoundCampaignV1 {
        CompoundCampaignV1 {
            schema: COMPOUND_CAMPAIGN_SCHEMA.into(),
            campaign_id: "epoxy-amine-phase0-v1".into(),
            feedback_snapshot: CampaignSnapshotBindingV1 {
                snapshot_id: "feedback-v4-2026-07-19".into(),
                catalog_path: "feedback/v4/catalog.json".into(),
                catalog_sha256: digest("v4"),
            },
            chebi_snapshot: CampaignSnapshotBindingV1 {
                snapshot_id: "feedback-v3-2026-07-19".into(),
                catalog_path: "feedback/v3/catalog.json".into(),
                catalog_sha256: digest("v3"),
            },
            ord_snapshot: OrdSnapshotBindingV1 {
                git_commit: REQUIRED_ORD_COMMIT.into(),
                ord_schema_version: REQUIRED_ORD_SCHEMA_VERSION.into(),
                ord_schema_commit: REQUIRED_ORD_SCHEMA_COMMIT.into(),
                object_manifest_path: "feedback/v4/manifests/ord.json".into(),
                object_manifest_sha256: digest("ord"),
                object_count: 550,
                total_bytes: 1_180_000_000,
                acquisition_kind: "ORD_GIT_LFS_TREE".into(),
            },
            rdkit_build: RdkitBuildBindingV1 {
                version: REQUIRED_RDKIT_VERSION.into(),
                git_commit: REQUIRED_RDKIT_COMMIT.into(),
                build_manifest_path: "config/rdkit/build.v1.json".into(),
                build_manifest_sha256: digest("rdkit-build"),
                source_sha256: digest("rdkit-source"),
                library_sha256: BTreeMap::from([("lib/libRDKitGraphMol.so".into(), digest("lib"))]),
            },
            deterministic_seed: 20_260_719,
            cohort_thresholds: CampaignCohortThresholdsV1 {
                unique_structures: 24,
                epoxide_bearing: 8,
                reactive_amine_bearing: 8,
                scaffold_pair_groups: 6,
            },
            maximum_generation_attempts: 100,
            pairing_rule: CampaignPairingRuleV1 {
                method: "CANONICAL_HASH_ROLE_SCAFFOLD_STRATA".into(),
                resin_mass_g: 100.0,
                equivalent_ratio: 1.0,
                deterministic_tie_break: "SHA256_ASCENDING".into(),
            },
            packet_count: 12,
            authority_ceiling: "AUDIT_ONLY".into(),
            production_scientific_ranking_enabled: false,
            generation_requests: vec![CampaignGenerationRequestV1 {
                request_id: "request-1".into(),
                parent_structures: vec!["C1OC1".into()],
                reaction_family: "family".into(),
                requested_role: "resin".into(),
            }],
        }
    }

    #[test]
    fn manifest_locks_versions_thresholds_and_nonranking_authority() {
        let campaign = campaign();
        campaign.validate().unwrap();
        let mutations: Vec<Box<dyn Fn(&mut CompoundCampaignV1)>> = vec![
            Box::new(|value| value.production_scientific_ranking_enabled = true),
            Box::new(|value| value.rdkit_build.version = "2026.03.1".into()),
            Box::new(|value| value.ord_snapshot.object_count = 0),
            Box::new(|value| value.cohort_thresholds.unique_structures = 23),
            Box::new(|value| value.packet_count = 11),
            Box::new(|value| value.generation_requests[0].requested_role = "optimizer".into()),
        ];
        for mutate in mutations {
            let mut changed = campaign.clone();
            mutate(&mut changed);
            assert!(changed.validate().is_err());
        }
    }

    #[test]
    fn result_scanner_rejects_nested_rank_or_execution_authority() {
        let ranked = serde_json::json!({"nested": {"rank": 1}});
        let executing = serde_json::json!({"execution_authorized": true});
        let held = serde_json::json!({"execution_authorized": false});
        assert!(contains_forbidden_authority(&ranked));
        assert!(contains_forbidden_authority(&executing));
        assert!(!contains_forbidden_authority(&held));
    }
}
