use crate::{ModelArtifactV1, RightsRecordV1};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::{BTreeMap, BTreeSet};
use thiserror::Error;

pub const CORROSION_OBSERVATION_SCHEMA: &str = "amphora.corrosion-observation.v1";
pub const CURE_OBSERVATION_SCHEMA: &str = "amphora.cure-observation.v1";
pub const TECHNICAL_IP_DOSSIER_SCHEMA: &str = "amphora.technical-ip-dossier.v1";
pub const VERIFIED_MODEL_INPUT_SCHEMA: &str = "amphora.host-verified-model-input.v1";
pub const VERIFIED_FORMULATION_MODEL_INPUT_SCHEMA: &str =
    "amphora.host-verified-formulation-model-input.v1";
pub const VERIFIED_FORMULATION_MODEL_INPUT_V2_SCHEMA: &str =
    "amphora.host-verified-formulation-model-input.v2";
pub const EXPERIMENTAL_CAMPAIGN_SCHEMA: &str = "amphora.experimental-campaign.v1";

#[derive(Debug, Error, PartialEq, Eq)]
pub enum TechnicalContractError {
    #[error("unexpected schema: {0}")]
    Schema(String),
    #[error("required field is empty: {0}")]
    Empty(&'static str),
    #[error("invalid SHA-256: {0}")]
    Hash(&'static str),
    #[error("source and rights records do not match")]
    RightsSourceMismatch,
    #[error("rights-blocked observation must be quarantined")]
    RightsNotQuarantined,
    #[error("eligible observation cannot be assigned to quarantine")]
    EligibleObservationQuarantined,
    #[error("invalid endpoint unit")]
    EndpointUnit,
    #[error("invalid electrochemical spectrum declaration")]
    SpectrumDeclaration,
    #[error("QC exclusion status, reason, and split are inconsistent")]
    QcExclusion,
    #[error("measurement must be finite")]
    NonFinite,
    #[error("model artifact binding is invalid")]
    ModelBinding,
    #[error("candidate observation binding is invalid")]
    ObservationBinding,
    #[error("evaluation or independent-review receipt binding is invalid")]
    ReceiptBinding,
    #[error("dataset, split, benchmark lock, or raw-file parent binding is invalid")]
    ParentBinding,
    #[error("duplicate campaign identity: {0}")]
    Duplicate(&'static str),
    #[error("an endpoint was exposed as an input to a different endpoint model")]
    EndpointLeakage,
    #[error("FTO status must remain FTO NOT PERFORMED")]
    FtoStatus,
    #[error("a filing recommendation requires a locked technical differentiator")]
    FilingWithoutDifferentiator,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct SourceBindingV1 {
    pub source_id: String,
    pub publisher: String,
    pub source_url: String,
    pub raw_artifact: String,
    pub raw_sha256: String,
    pub source_row: u64,
    pub rights: RightsRecordV1,
}

impl SourceBindingV1 {
    pub fn validate(&self) -> Result<(), TechnicalContractError> {
        require("source_id", &self.source_id)?;
        require("publisher", &self.publisher)?;
        require("source_url", &self.source_url)?;
        require("raw_artifact", &self.raw_artifact)?;
        require_hash("raw_sha256", &self.raw_sha256)?;
        if self.rights.source_id != self.source_id {
            return Err(TechnicalContractError::RightsSourceMismatch);
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum CorrosionEndpointV1 {
    ImpedanceModulus,
    Phase,
    Ocv,
    OcvSlope,
    RustCreep,
    WetAdhesion,
    CathodicDisbondment,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum EisSpectrumKindV1 {
    NotApplicable,
    SingleFrequencySummary,
    FrequencyResolvedComplex,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum ObservationQcStatusV1 {
    Included,
    Excluded,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct CorrosionObservationV1 {
    pub schema: String,
    pub observation_id: String,
    pub source: SourceBindingV1,
    pub study_id: String,
    pub system_id: String,
    pub panel_id: String,
    pub replicate_id: String,
    pub split: String,
    pub method: String,
    pub endpoint: CorrosionEndpointV1,
    pub value: f64,
    pub unit: String,
    pub exposure_hours: Option<f64>,
    pub frequency_hz: Option<f64>,
    pub spectrum_kind: EisSpectrumKindV1,
    pub qc_status: ObservationQcStatusV1,
    pub qc_exclusion_reason: Option<String>,
    #[serde(default)]
    pub conditions: BTreeMap<String, String>,
}

impl CorrosionObservationV1 {
    pub fn validate(&self) -> Result<(), TechnicalContractError> {
        if self.schema != CORROSION_OBSERVATION_SCHEMA {
            return Err(TechnicalContractError::Schema(self.schema.clone()));
        }
        self.source.validate()?;
        for (field, value) in [
            ("observation_id", self.observation_id.as_str()),
            ("study_id", self.study_id.as_str()),
            ("system_id", self.system_id.as_str()),
            ("panel_id", self.panel_id.as_str()),
            ("replicate_id", self.replicate_id.as_str()),
            ("split", self.split.as_str()),
            ("method", self.method.as_str()),
        ] {
            require(field, value)?;
        }
        validate_rights_split(&self.source.rights, &self.split)?;
        match (self.qc_status, self.qc_exclusion_reason.as_deref()) {
            (ObservationQcStatusV1::Included, None) if self.split != "QC_EXCLUDED" => {}
            (ObservationQcStatusV1::Excluded, Some(reason))
                if !reason.trim().is_empty() && self.split == "QC_EXCLUDED" => {}
            _ => return Err(TechnicalContractError::QcExclusion),
        }
        if !self.value.is_finite()
            || self
                .exposure_hours
                .is_some_and(|value| !value.is_finite() || value < 0.0)
            || self
                .frequency_hz
                .is_some_and(|value| !value.is_finite() || value <= 0.0)
        {
            return Err(TechnicalContractError::NonFinite);
        }
        let expected_unit = match self.endpoint {
            CorrosionEndpointV1::ImpedanceModulus => "ohm",
            CorrosionEndpointV1::Phase => "degree",
            CorrosionEndpointV1::Ocv => "V",
            CorrosionEndpointV1::OcvSlope => "V/s",
            CorrosionEndpointV1::RustCreep | CorrosionEndpointV1::CathodicDisbondment => "mm",
            CorrosionEndpointV1::WetAdhesion => "MPa",
        };
        if self.unit != expected_unit {
            return Err(TechnicalContractError::EndpointUnit);
        }
        let eis_endpoint = matches!(
            self.endpoint,
            CorrosionEndpointV1::ImpedanceModulus | CorrosionEndpointV1::Phase
        );
        match (eis_endpoint, self.spectrum_kind, self.frequency_hz) {
            (true, EisSpectrumKindV1::SingleFrequencySummary, Some(_))
            | (true, EisSpectrumKindV1::FrequencyResolvedComplex, Some(_))
            | (false, EisSpectrumKindV1::NotApplicable, None) => Ok(()),
            _ => Err(TechnicalContractError::SpectrumDeclaration),
        }
    }

    pub fn allows_kramers_kronig_or_equivalent_circuit(&self) -> bool {
        self.spectrum_kind == EisSpectrumKindV1::FrequencyResolvedComplex
    }
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum CureEndpointV1 {
    GelTime,
    PotLife,
    DryHardTime,
    ThroughCureTime,
    DscConversion,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct CureObservationV1 {
    pub schema: String,
    pub observation_id: String,
    pub source: SourceBindingV1,
    pub resin_family: Option<String>,
    pub hardener_family: Option<String>,
    pub mix_ratio_phr: Option<f64>,
    pub temperature_c: Option<f64>,
    pub test_mass_g: Option<f64>,
    pub method: Option<String>,
    pub endpoint: CureEndpointV1,
    pub value: f64,
    pub unit: String,
    pub split: String,
    #[serde(default)]
    pub conditions: BTreeMap<String, String>,
}

impl CureObservationV1 {
    pub fn validate(&self) -> Result<(), TechnicalContractError> {
        if self.schema != CURE_OBSERVATION_SCHEMA {
            return Err(TechnicalContractError::Schema(self.schema.clone()));
        }
        self.source.validate()?;
        require("observation_id", &self.observation_id)?;
        require("split", &self.split)?;
        validate_rights_split(&self.source.rights, &self.split)?;
        if !self.value.is_finite()
            || self
                .mix_ratio_phr
                .is_some_and(|value| !value.is_finite() || value <= 0.0)
            || self.temperature_c.is_some_and(|value| !value.is_finite())
            || self
                .test_mass_g
                .is_some_and(|value| !value.is_finite() || value <= 0.0)
        {
            return Err(TechnicalContractError::NonFinite);
        }
        let valid_unit = match self.endpoint {
            CureEndpointV1::GelTime
            | CureEndpointV1::PotLife
            | CureEndpointV1::DryHardTime
            | CureEndpointV1::ThroughCureTime => matches!(self.unit.as_str(), "min" | "h"),
            CureEndpointV1::DscConversion => {
                self.unit == "fraction_0_1" && (0.0..=1.0).contains(&self.value)
            }
        };
        if !valid_unit {
            return Err(TechnicalContractError::EndpointUnit);
        }
        Ok(())
    }

    pub fn is_primary_benchmark_eligible(&self) -> bool {
        self.source.rights.eligible_for_derivatives
            && self.endpoint == CureEndpointV1::GelTime
            && self
                .resin_family
                .as_deref()
                .is_some_and(|resin| matches!(resin, "BIS_A" | "DGEBA" | "BIS_A_DGEBA"))
            && self
                .hardener_family
                .as_deref()
                .is_some_and(|value| !value.is_empty())
            && self.mix_ratio_phr.is_some()
            && self.temperature_c.is_some()
            && self.test_mass_g.is_some()
            && self
                .method
                .as_deref()
                .is_some_and(|value| !value.is_empty())
            && self.split != "QUARANTINE"
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct VerifiedModelInputV1 {
    pub schema: String,
    pub module_id: String,
    pub accepted: bool,
    pub signature_verified: bool,
    pub artifact_hash_verified: bool,
    pub rights_eligible: bool,
    pub method_comparable: bool,
    pub model_artifact_sha256: String,
    pub model_artifact: ModelArtifactV1,
    #[serde(default)]
    pub benchmark_metrics: BTreeMap<String, Value>,
}

impl VerifiedModelInputV1 {
    pub fn validate(&self) -> Result<(), TechnicalContractError> {
        if self.schema != VERIFIED_MODEL_INPUT_SCHEMA {
            return Err(TechnicalContractError::Schema(self.schema.clone()));
        }
        require("module_id", &self.module_id)?;
        require_hash("model_artifact_sha256", &self.model_artifact_sha256)?;
        self.model_artifact
            .validate()
            .map_err(|_| TechnicalContractError::ModelBinding)?;
        let artifact_value = serde_json::to_value(&self.model_artifact)
            .map_err(|_| TechnicalContractError::ModelBinding)?;
        if crate::stable_hash(&artifact_value) != self.model_artifact_sha256
            || !self.accepted
            || !self.signature_verified
            || !self.artifact_hash_verified
        {
            return Err(TechnicalContractError::ModelBinding);
        }
        Ok(())
    }
}

/// Host-owned admission record for formulation models. Candidate JSON is never
/// deserialized into this type; the runtime accepts it only from FeatureSnapshot.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct VerifiedFormulationModelInputV1 {
    pub schema: String,
    pub module_id: String,
    pub candidate_id: String,
    pub candidate_contract_hash_v1: String,
    pub accepted: bool,
    pub model_signature_verified: bool,
    pub model_artifact_hash_verified: bool,
    pub evaluation_receipt_verified: bool,
    pub rights_eligible: bool,
    pub method_comparable: bool,
    pub applicability_domain_verified: bool,
    pub raw_file_hashes_verified: bool,
    pub model_artifact_sha256: String,
    pub evaluation_receipt_sha256: String,
    pub observation_bundle_sha256: String,
    pub model_artifact: Value,
    pub observation_bundle: Value,
    #[serde(default)]
    pub raw_file_hashes: BTreeMap<String, String>,
    #[serde(default)]
    pub benchmark_metrics: BTreeMap<String, Value>,
}

impl VerifiedFormulationModelInputV1 {
    pub fn validate(&self) -> Result<(), TechnicalContractError> {
        if self.schema != VERIFIED_FORMULATION_MODEL_INPUT_SCHEMA {
            return Err(TechnicalContractError::Schema(self.schema.clone()));
        }
        require("module_id", &self.module_id)?;
        require("candidate_id", &self.candidate_id)?;
        for (field, hash) in [
            (
                "candidate_contract_hash_v1",
                self.candidate_contract_hash_v1.as_str(),
            ),
            ("model_artifact_sha256", self.model_artifact_sha256.as_str()),
            (
                "evaluation_receipt_sha256",
                self.evaluation_receipt_sha256.as_str(),
            ),
            (
                "observation_bundle_sha256",
                self.observation_bundle_sha256.as_str(),
            ),
        ] {
            require_hash(field, hash)?;
        }
        for hash in self.raw_file_hashes.values() {
            require_hash("raw_file_hashes", hash)?;
        }
        if !self.accepted
            || !self.model_signature_verified
            || !self.model_artifact_hash_verified
            || !self.evaluation_receipt_verified
            || !self.rights_eligible
            || !self.method_comparable
            || !self.applicability_domain_verified
            || !self.raw_file_hashes_verified
            || crate::stable_hash(&self.model_artifact) != self.model_artifact_sha256
        {
            return Err(TechnicalContractError::ModelBinding);
        }
        if crate::stable_hash(&self.observation_bundle) != self.observation_bundle_sha256 {
            return Err(TechnicalContractError::ObservationBinding);
        }
        Ok(())
    }

    pub fn validate_candidate(
        &self,
        candidate_id: &str,
        candidate_contract_hash_v1: &str,
    ) -> Result<(), TechnicalContractError> {
        self.validate()?;
        if self.candidate_id != candidate_id
            || self.candidate_contract_hash_v1 != candidate_contract_hash_v1
        {
            return Err(TechnicalContractError::ObservationBinding);
        }
        Ok(())
    }
}

/// Content-bound admission record for empirical formulation models.
///
/// V1 is retained for diagnostic replay. Evidence-bound coatings modules use
/// this contract so that a host cannot replace checked receipt content with a
/// boolean or a free-form benchmark metric.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct VerifiedFormulationModelInputV2 {
    pub schema: String,
    pub module_id: String,
    pub candidate_id: String,
    pub candidate_contract_hash_v1: String,
    pub model_artifact_sha256: String,
    pub observation_bundle_sha256: String,
    pub evaluation_receipt_sha256: String,
    pub independent_review_receipt_sha256: String,
    pub dataset_sha256: String,
    pub split_sha256: String,
    pub benchmark_lock_sha256: String,
    pub raw_file_manifest_sha256: String,
    pub model_artifact: Value,
    pub observation_bundle: Value,
    pub evaluation_receipt: Value,
    pub independent_review_receipt: Value,
    pub dataset: Value,
    pub split: Value,
    pub benchmark_lock: Value,
    pub raw_file_hashes: BTreeMap<String, String>,
}

impl VerifiedFormulationModelInputV2 {
    pub fn validate(&self) -> Result<(), TechnicalContractError> {
        if self.schema != VERIFIED_FORMULATION_MODEL_INPUT_V2_SCHEMA {
            return Err(TechnicalContractError::Schema(self.schema.clone()));
        }
        require("module_id", &self.module_id)?;
        require("candidate_id", &self.candidate_id)?;
        for (field, hash) in [
            (
                "candidate_contract_hash_v1",
                self.candidate_contract_hash_v1.as_str(),
            ),
            ("model_artifact_sha256", self.model_artifact_sha256.as_str()),
            (
                "observation_bundle_sha256",
                self.observation_bundle_sha256.as_str(),
            ),
            (
                "evaluation_receipt_sha256",
                self.evaluation_receipt_sha256.as_str(),
            ),
            (
                "independent_review_receipt_sha256",
                self.independent_review_receipt_sha256.as_str(),
            ),
            ("dataset_sha256", self.dataset_sha256.as_str()),
            ("split_sha256", self.split_sha256.as_str()),
            ("benchmark_lock_sha256", self.benchmark_lock_sha256.as_str()),
            (
                "raw_file_manifest_sha256",
                self.raw_file_manifest_sha256.as_str(),
            ),
        ] {
            require_hash(field, hash)?;
        }
        if self.raw_file_hashes.is_empty() {
            return Err(TechnicalContractError::Empty("raw_file_hashes"));
        }
        for (path, hash) in &self.raw_file_hashes {
            require("raw_file_path", path)?;
            require_hash("raw_file_hashes", hash)?;
        }

        for (content, expected) in [
            (&self.model_artifact, &self.model_artifact_sha256),
            (&self.observation_bundle, &self.observation_bundle_sha256),
            (&self.evaluation_receipt, &self.evaluation_receipt_sha256),
            (
                &self.independent_review_receipt,
                &self.independent_review_receipt_sha256,
            ),
            (&self.dataset, &self.dataset_sha256),
            (&self.split, &self.split_sha256),
            (&self.benchmark_lock, &self.benchmark_lock_sha256),
        ] {
            if crate::stable_hash(content) != *expected {
                return Err(TechnicalContractError::ParentBinding);
            }
        }
        let raw_manifest = serde_json::to_value(&self.raw_file_hashes)
            .map_err(|_| TechnicalContractError::ParentBinding)?;
        if crate::stable_hash(&raw_manifest) != self.raw_file_manifest_sha256 {
            return Err(TechnicalContractError::ParentBinding);
        }

        for content in [
            &self.model_artifact,
            &self.observation_bundle,
            &self.evaluation_receipt,
            &self.independent_review_receipt,
            &self.dataset,
            &self.split,
            &self.benchmark_lock,
        ] {
            if content
                .get("module_id")
                .and_then(Value::as_str)
                .is_some_and(|module| module != self.module_id)
            {
                return Err(TechnicalContractError::ParentBinding);
            }
        }
        if self
            .observation_bundle
            .get("candidate_id")
            .and_then(Value::as_str)
            != Some(self.candidate_id.as_str())
        {
            return Err(TechnicalContractError::ObservationBinding);
        }

        require_bound_hash(&self.split, "dataset_sha256", &self.dataset_sha256)?;
        require_bound_hash(&self.benchmark_lock, "dataset_sha256", &self.dataset_sha256)?;
        require_bound_hash(&self.benchmark_lock, "split_sha256", &self.split_sha256)?;
        require_model_parent_hash(
            &self.model_artifact,
            "dataset_sha256",
            "dataset",
            &self.dataset_sha256,
        )?;
        require_model_parent_hash(
            &self.model_artifact,
            "split_sha256",
            "split",
            &self.split_sha256,
        )?;
        require_model_parent_hash(
            &self.model_artifact,
            "benchmark_lock_sha256",
            "benchmark_lock",
            &self.benchmark_lock_sha256,
        )?;

        for (field, expected) in [
            ("model_artifact_sha256", self.model_artifact_sha256.as_str()),
            ("dataset_sha256", self.dataset_sha256.as_str()),
            ("split_sha256", self.split_sha256.as_str()),
            ("benchmark_lock_sha256", self.benchmark_lock_sha256.as_str()),
            (
                "raw_file_manifest_sha256",
                self.raw_file_manifest_sha256.as_str(),
            ),
        ] {
            require_bound_hash(&self.evaluation_receipt, field, expected)
                .map_err(|_| TechnicalContractError::ReceiptBinding)?;
        }
        if self
            .evaluation_receipt
            .get("passed")
            .and_then(Value::as_bool)
            != Some(true)
        {
            return Err(TechnicalContractError::ReceiptBinding);
        }
        require_bound_hash(
            &self.independent_review_receipt,
            "model_artifact_sha256",
            &self.model_artifact_sha256,
        )
        .map_err(|_| TechnicalContractError::ReceiptBinding)?;
        let review_receipt_hash = self
            .independent_review_receipt
            .get("evaluation_receipt_sha256")
            .or_else(|| {
                self.independent_review_receipt
                    .get("benchmark_receipt_sha256")
            })
            .and_then(Value::as_str);
        if review_receipt_hash != Some(self.evaluation_receipt_sha256.as_str()) {
            return Err(TechnicalContractError::ReceiptBinding);
        }
        Ok(())
    }

    pub fn validate_candidate(
        &self,
        candidate_id: &str,
        candidate_contract_hash_v1: &str,
    ) -> Result<(), TechnicalContractError> {
        self.validate()?;
        if self.candidate_id != candidate_id
            || self.candidate_contract_hash_v1 != candidate_contract_hash_v1
        {
            return Err(TechnicalContractError::ObservationBinding);
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct CampaignInstrumentV1 {
    pub instrument_id: String,
    pub instrument_kind: String,
    pub calibration_sha256: String,
    pub qualification_raw_file: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct CampaignSampleV1 {
    pub sample_id: String,
    pub candidate_sha256: String,
    pub recipe_sha256: String,
    pub material_lots: BTreeMap<String, String>,
    pub blinding_assignment: String,
    pub protocol_sha256: String,
    pub instrument_ids: Vec<String>,
    pub raw_file_hashes: BTreeMap<String, String>,
    pub prepared_at: String,
    pub measured_at: String,
    pub rights_receipt_sha256: String,
    pub rights_permit_derived_use: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct CampaignEndpointLinkV1 {
    pub sample_id: String,
    pub measured_endpoint: String,
    pub model_input_endpoint: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct ExperimentalCampaignV1 {
    pub schema: String,
    pub campaign_id: String,
    pub lab_issuer: String,
    pub protocol_sha256: String,
    pub started_at: String,
    pub completed_at: String,
    pub instruments: Vec<CampaignInstrumentV1>,
    pub samples: Vec<CampaignSampleV1>,
    #[serde(default)]
    pub endpoint_links: Vec<CampaignEndpointLinkV1>,
}

impl ExperimentalCampaignV1 {
    pub fn validate(&self) -> Result<(), TechnicalContractError> {
        if self.schema != EXPERIMENTAL_CAMPAIGN_SCHEMA {
            return Err(TechnicalContractError::Schema(self.schema.clone()));
        }
        require("campaign_id", &self.campaign_id)?;
        require("lab_issuer", &self.lab_issuer)?;
        require("started_at", &self.started_at)?;
        require("completed_at", &self.completed_at)?;
        require_hash("protocol_sha256", &self.protocol_sha256)?;
        if self.instruments.is_empty() || self.samples.is_empty() {
            return Err(TechnicalContractError::Empty("campaign records"));
        }
        let mut instrument_ids = BTreeSet::new();
        for instrument in &self.instruments {
            require("instrument_id", &instrument.instrument_id)?;
            require("instrument_kind", &instrument.instrument_kind)?;
            require("qualification_raw_file", &instrument.qualification_raw_file)?;
            require_hash("calibration_sha256", &instrument.calibration_sha256)?;
            if !instrument_ids.insert(instrument.instrument_id.as_str()) {
                return Err(TechnicalContractError::Duplicate("instrument_id"));
            }
        }
        let mut sample_ids = BTreeSet::new();
        for sample in &self.samples {
            require("sample_id", &sample.sample_id)?;
            require("blinding_assignment", &sample.blinding_assignment)?;
            require("prepared_at", &sample.prepared_at)?;
            require("measured_at", &sample.measured_at)?;
            for (field, hash) in [
                ("candidate_sha256", sample.candidate_sha256.as_str()),
                ("recipe_sha256", sample.recipe_sha256.as_str()),
                ("protocol_sha256", sample.protocol_sha256.as_str()),
                (
                    "rights_receipt_sha256",
                    sample.rights_receipt_sha256.as_str(),
                ),
            ] {
                require_hash(field, hash)?;
            }
            if sample.protocol_sha256 != self.protocol_sha256
                || !sample.rights_permit_derived_use
                || sample.material_lots.is_empty()
                || sample.raw_file_hashes.is_empty()
                || sample.instrument_ids.is_empty()
                || sample
                    .instrument_ids
                    .iter()
                    .any(|id| !instrument_ids.contains(id.as_str()))
            {
                return Err(TechnicalContractError::ParentBinding);
            }
            for (name, lot) in &sample.material_lots {
                require("material_name", name)?;
                require("material_lot", lot)?;
            }
            for (path, hash) in &sample.raw_file_hashes {
                require("raw_file_path", path)?;
                require_hash("raw_file_hashes", hash)?;
            }
            if !sample_ids.insert(sample.sample_id.as_str()) {
                return Err(TechnicalContractError::Duplicate("sample_id"));
            }
        }
        for link in &self.endpoint_links {
            require("measured_endpoint", &link.measured_endpoint)?;
            require("model_input_endpoint", &link.model_input_endpoint)?;
            if !sample_ids.contains(link.sample_id.as_str()) {
                return Err(TechnicalContractError::ParentBinding);
            }
            if link.measured_endpoint != link.model_input_endpoint {
                return Err(TechnicalContractError::EndpointLeakage);
            }
        }
        Ok(())
    }

    pub fn identity_hash(&self) -> String {
        crate::stable_hash(&serde_json::to_value(self).expect("campaign serializes"))
    }
}

fn require_bound_hash(
    value: &Value,
    field: &'static str,
    expected: &str,
) -> Result<(), TechnicalContractError> {
    if value.get(field).and_then(Value::as_str) == Some(expected) {
        Ok(())
    } else {
        Err(TechnicalContractError::ParentBinding)
    }
}

fn require_model_parent_hash(
    model: &Value,
    direct_field: &'static str,
    parent_name: &'static str,
    expected: &str,
) -> Result<(), TechnicalContractError> {
    let observed = model
        .get(direct_field)
        .or_else(|| {
            model
                .get("parent_hashes")
                .and_then(|parents| parents.get(parent_name))
        })
        .and_then(Value::as_str);
    if observed == Some(expected) {
        Ok(())
    } else {
        Err(TechnicalContractError::ParentBinding)
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct ClosestArtElementChartV1 {
    pub family_id: String,
    pub source_url: String,
    pub elements: BTreeMap<String, String>,
    pub unresolved_elements: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct HostileNullAblationV1 {
    pub module_id: String,
    pub null_name: String,
    pub metric: String,
    pub candidate_value: Option<f64>,
    pub null_value: Option<f64>,
    pub reproducible_differentiator: bool,
    pub receipt_hash: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct DisclosureLogEntryV1 {
    pub date: String,
    pub recipient_class: String,
    pub subject: String,
    pub confidentiality: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum IpDispositionV1 {
    PatentFile,
    TradeSecret,
    NoFile,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct IpRecommendationV1 {
    pub hypothesis_id: String,
    pub disposition: IpDispositionV1,
    pub rationale: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct TechnicalIpDossierV1 {
    pub schema: String,
    pub dossier_id: String,
    pub generated_on: String,
    pub modules: Vec<String>,
    pub conception_dates: BTreeMap<String, String>,
    pub contributors: Vec<String>,
    pub technical_problem: Vec<String>,
    pub model_architecture: Vec<String>,
    pub evidence_hashes: BTreeMap<String, String>,
    pub closest_art_element_charts: Vec<ClosestArtElementChartV1>,
    pub hostile_null_ablations: Vec<HostileNullAblationV1>,
    pub alternatives: Vec<String>,
    pub disclosure_log: Vec<DisclosureLogEntryV1>,
    pub recommendations: Vec<IpRecommendationV1>,
    pub locked_differentiator_present: bool,
    pub fto_status: String,
}

impl TechnicalIpDossierV1 {
    pub fn validate(&self) -> Result<(), TechnicalContractError> {
        if self.schema != TECHNICAL_IP_DOSSIER_SCHEMA {
            return Err(TechnicalContractError::Schema(self.schema.clone()));
        }
        require("dossier_id", &self.dossier_id)?;
        require("generated_on", &self.generated_on)?;
        if self.modules.is_empty() {
            return Err(TechnicalContractError::Empty("modules"));
        }
        if self.fto_status != "FTO NOT PERFORMED" {
            return Err(TechnicalContractError::FtoStatus);
        }
        for hash in self.evidence_hashes.values() {
            require_hash("evidence_hashes", hash)?;
        }
        if !self.locked_differentiator_present
            && self
                .recommendations
                .iter()
                .any(|row| row.disposition == IpDispositionV1::PatentFile)
        {
            return Err(TechnicalContractError::FilingWithoutDifferentiator);
        }
        Ok(())
    }
}

fn validate_rights_split(
    rights: &RightsRecordV1,
    split: &str,
) -> Result<(), TechnicalContractError> {
    if rights.eligible_for_derivatives && split == "QUARANTINE" {
        return Err(TechnicalContractError::EligibleObservationQuarantined);
    }
    if !rights.eligible_for_derivatives && split != "QUARANTINE" {
        return Err(TechnicalContractError::RightsNotQuarantined);
    }
    Ok(())
}

fn require(field: &'static str, value: &str) -> Result<(), TechnicalContractError> {
    if value.trim().is_empty() {
        Err(TechnicalContractError::Empty(field))
    } else {
        Ok(())
    }
}

fn require_hash(field: &'static str, value: &str) -> Result<(), TechnicalContractError> {
    if value.len() == 64 && value.bytes().all(|byte| byte.is_ascii_hexdigit()) {
        Ok(())
    } else {
        Err(TechnicalContractError::Hash(field))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn rights(eligible: bool) -> RightsRecordV1 {
        RightsRecordV1 {
            source_id: "source".into(),
            license: "explicit-test-license".into(),
            status: if eligible { "ACCEPTED" } else { "QUARANTINED" }.into(),
            source_url: "https://example.invalid/source".into(),
            restrictions: Vec::new(),
            eligible_for_derivatives: eligible,
        }
    }

    fn source(eligible: bool) -> SourceBindingV1 {
        SourceBindingV1 {
            source_id: "source".into(),
            publisher: "publisher".into(),
            source_url: "https://example.invalid/source".into(),
            raw_artifact: "raw.csv".into(),
            raw_sha256: "a".repeat(64),
            source_row: 1,
            rights: rights(eligible),
        }
    }

    #[test]
    fn single_frequency_eis_never_enables_spectrum_claims() {
        let mut observation = CorrosionObservationV1 {
            schema: CORROSION_OBSERVATION_SCHEMA.into(),
            observation_id: "obs".into(),
            source: source(true),
            study_id: "study".into(),
            system_id: "system".into(),
            panel_id: "panel-1".into(),
            replicate_id: "1".into(),
            split: "TRAIN".into(),
            method: "EIS_SINGLE_FREQUENCY_SUMMARY".into(),
            endpoint: CorrosionEndpointV1::ImpedanceModulus,
            value: 1e9,
            unit: "ohm".into(),
            exposure_hours: Some(24.0),
            frequency_hz: Some(0.01),
            spectrum_kind: EisSpectrumKindV1::SingleFrequencySummary,
            qc_status: ObservationQcStatusV1::Included,
            qc_exclusion_reason: None,
            conditions: BTreeMap::new(),
        };
        observation.validate().unwrap();
        assert!(!observation.allows_kramers_kronig_or_equivalent_circuit());
        observation.qc_status = ObservationQcStatusV1::Excluded;
        observation.split = "QC_EXCLUDED".into();
        assert_eq!(
            observation.validate(),
            Err(TechnicalContractError::QcExclusion)
        );
        observation.qc_exclusion_reason = Some("OCV drift exceeded preregistered limit".into());
        observation.validate().unwrap();
    }

    #[test]
    fn rights_blocked_rows_must_be_quarantined() {
        let observation = CureObservationV1 {
            schema: CURE_OBSERVATION_SCHEMA.into(),
            observation_id: "obs".into(),
            source: source(false),
            resin_family: Some("DGEBA".into()),
            hardener_family: Some("polyamide".into()),
            mix_ratio_phr: Some(50.0),
            temperature_c: Some(25.0),
            test_mass_g: Some(100.0),
            method: Some("supplier gel test".into()),
            endpoint: CureEndpointV1::GelTime,
            value: 60.0,
            unit: "min".into(),
            split: "TRAIN".into(),
            conditions: BTreeMap::new(),
        };
        assert_eq!(
            observation.validate(),
            Err(TechnicalContractError::RightsNotQuarantined)
        );
    }

    #[test]
    fn gel_time_and_pot_life_are_distinct_endpoints() {
        let mut observation = CureObservationV1 {
            schema: CURE_OBSERVATION_SCHEMA.into(),
            observation_id: "obs".into(),
            source: source(true),
            resin_family: Some("DGEBA".into()),
            hardener_family: Some("polyamide".into()),
            mix_ratio_phr: Some(50.0),
            temperature_c: Some(25.0),
            test_mass_g: Some(100.0),
            method: Some("ASTM gel test".into()),
            endpoint: CureEndpointV1::GelTime,
            value: 60.0,
            unit: "min".into(),
            split: "HOLDOUT".into(),
            conditions: BTreeMap::new(),
        };
        assert!(observation.is_primary_benchmark_eligible());
        observation.endpoint = CureEndpointV1::PotLife;
        assert!(!observation.is_primary_benchmark_eligible());
    }

    #[test]
    fn dossier_cannot_recommend_filing_without_locked_differentiator() {
        let dossier = TechnicalIpDossierV1 {
            schema: TECHNICAL_IP_DOSSIER_SCHEMA.into(),
            dossier_id: "dossier".into(),
            generated_on: "2026-07-17".into(),
            modules: vec!["module".into()],
            conception_dates: BTreeMap::new(),
            contributors: Vec::new(),
            technical_problem: Vec::new(),
            model_architecture: Vec::new(),
            evidence_hashes: BTreeMap::new(),
            closest_art_element_charts: Vec::new(),
            hostile_null_ablations: Vec::new(),
            alternatives: Vec::new(),
            disclosure_log: Vec::new(),
            recommendations: vec![IpRecommendationV1 {
                hypothesis_id: "hypothesis".into(),
                disposition: IpDispositionV1::PatentFile,
                rationale: "test".into(),
            }],
            locked_differentiator_present: false,
            fto_status: "FTO NOT PERFORMED".into(),
        };
        assert_eq!(
            dossier.validate(),
            Err(TechnicalContractError::FilingWithoutDifferentiator)
        );
    }

    #[test]
    fn formulation_model_binding_rejects_forged_candidate_or_rights() {
        let model_artifact = serde_json::json!({
            "schema": "amphora.test-model.v1",
            "module_id": "amphora-viscosity-score",
            "coefficient": 1.25
        });
        let observation_bundle = serde_json::json!({
            "schema": "amphora.test-observation-bundle.v1",
            "candidate_id": "candidate-1"
        });
        let mut binding = VerifiedFormulationModelInputV1 {
            schema: VERIFIED_FORMULATION_MODEL_INPUT_SCHEMA.into(),
            module_id: "amphora-viscosity-score".into(),
            candidate_id: "candidate-1".into(),
            candidate_contract_hash_v1: "a".repeat(64),
            accepted: true,
            model_signature_verified: true,
            model_artifact_hash_verified: true,
            evaluation_receipt_verified: true,
            rights_eligible: true,
            method_comparable: true,
            applicability_domain_verified: true,
            raw_file_hashes_verified: true,
            model_artifact_sha256: crate::stable_hash(&model_artifact),
            evaluation_receipt_sha256: "b".repeat(64),
            observation_bundle_sha256: crate::stable_hash(&observation_bundle),
            model_artifact,
            observation_bundle,
            raw_file_hashes: BTreeMap::from([("measurement.csv".into(), "c".repeat(64))]),
            benchmark_metrics: BTreeMap::new(),
        };
        binding
            .validate_candidate("candidate-1", &"a".repeat(64))
            .unwrap();
        assert_eq!(
            binding.validate_candidate("candidate-forged", &"a".repeat(64)),
            Err(TechnicalContractError::ObservationBinding)
        );
        binding.rights_eligible = false;
        assert_eq!(
            binding.validate(),
            Err(TechnicalContractError::ModelBinding)
        );

        let mut value = serde_json::to_value(&binding).unwrap();
        value["candidate_asserted_validation"] = serde_json::Value::Bool(true);
        assert!(serde_json::from_value::<VerifiedFormulationModelInputV1>(value).is_err());
    }

    #[test]
    fn formulation_v2_binds_receipt_and_every_parent_content() {
        let module = "amphora-viscosity-score";
        let dataset = serde_json::json!({"module_id": module, "rows": [1, 2]});
        let dataset_sha256 = crate::stable_hash(&dataset);
        let split = serde_json::json!({
            "module_id": module,
            "dataset_sha256": dataset_sha256,
            "assignments": ["FIT", "EXTERNAL"]
        });
        let split_sha256 = crate::stable_hash(&split);
        let benchmark_lock = serde_json::json!({
            "module_id": module,
            "dataset_sha256": dataset_sha256,
            "split_sha256": split_sha256,
            "immutable": true
        });
        let benchmark_lock_sha256 = crate::stable_hash(&benchmark_lock);
        let model_artifact = serde_json::json!({
            "module_id": module,
            "dataset_sha256": dataset_sha256,
            "split_sha256": split_sha256,
            "benchmark_lock_sha256": benchmark_lock_sha256,
            "coefficient": 1.0
        });
        let model_artifact_sha256 = crate::stable_hash(&model_artifact);
        let observation_bundle = serde_json::json!({
            "module_id": module,
            "candidate_id": "candidate-1",
            "observation": {"temperature_C": 25.0}
        });
        let raw_file_hashes = BTreeMap::from([("measurement.csv".into(), "a".repeat(64))]);
        let raw_file_manifest_sha256 = crate::stable_hash(
            &serde_json::to_value(&raw_file_hashes).expect("raw manifest serializes"),
        );
        let evaluation_receipt = serde_json::json!({
            "module_id": module,
            "model_artifact_sha256": model_artifact_sha256,
            "dataset_sha256": dataset_sha256,
            "split_sha256": split_sha256,
            "benchmark_lock_sha256": benchmark_lock_sha256,
            "raw_file_manifest_sha256": raw_file_manifest_sha256,
            "passed": true
        });
        let evaluation_receipt_sha256 = crate::stable_hash(&evaluation_receipt);
        let independent_review_receipt = serde_json::json!({
            "module_id": module,
            "model_artifact_sha256": model_artifact_sha256,
            "benchmark_receipt_sha256": evaluation_receipt_sha256,
            "reviewer_independent": true
        });
        let mut binding = VerifiedFormulationModelInputV2 {
            schema: VERIFIED_FORMULATION_MODEL_INPUT_V2_SCHEMA.into(),
            module_id: module.into(),
            candidate_id: "candidate-1".into(),
            candidate_contract_hash_v1: "b".repeat(64),
            model_artifact_sha256,
            observation_bundle_sha256: crate::stable_hash(&observation_bundle),
            evaluation_receipt_sha256,
            independent_review_receipt_sha256: crate::stable_hash(&independent_review_receipt),
            dataset_sha256,
            split_sha256,
            benchmark_lock_sha256,
            raw_file_manifest_sha256,
            model_artifact,
            observation_bundle,
            evaluation_receipt,
            independent_review_receipt,
            dataset,
            split,
            benchmark_lock,
            raw_file_hashes,
        };
        binding
            .validate_candidate("candidate-1", &"b".repeat(64))
            .unwrap();
        binding.evaluation_receipt["passed"] = Value::Bool(false);
        assert_eq!(
            binding.validate(),
            Err(TechnicalContractError::ParentBinding)
        );
    }

    #[test]
    fn campaign_rejects_cross_endpoint_feature_linkage() {
        let protocol = "a".repeat(64);
        let mut campaign = ExperimentalCampaignV1 {
            schema: EXPERIMENTAL_CAMPAIGN_SCHEMA.into(),
            campaign_id: "campaign-1".into(),
            lab_issuer: "independent-lab".into(),
            protocol_sha256: protocol.clone(),
            started_at: "2026-07-17T00:00:00Z".into(),
            completed_at: "2026-09-30T00:00:00Z".into(),
            instruments: vec![CampaignInstrumentV1 {
                instrument_id: "rheometer-1".into(),
                instrument_kind: "RHEOMETER".into(),
                calibration_sha256: "b".repeat(64),
                qualification_raw_file: "qualification.csv".into(),
            }],
            samples: vec![CampaignSampleV1 {
                sample_id: "sample-1".into(),
                candidate_sha256: "c".repeat(64),
                recipe_sha256: "d".repeat(64),
                material_lots: BTreeMap::from([("resin".into(), "lot-1".into())]),
                blinding_assignment: "BLIND-001".into(),
                protocol_sha256: protocol,
                instrument_ids: vec!["rheometer-1".into()],
                raw_file_hashes: BTreeMap::from([("flow.csv".into(), "e".repeat(64))]),
                prepared_at: "2026-08-01T00:00:00Z".into(),
                measured_at: "2026-08-01T01:00:00Z".into(),
                rights_receipt_sha256: "f".repeat(64),
                rights_permit_derived_use: true,
            }],
            endpoint_links: vec![CampaignEndpointLinkV1 {
                sample_id: "sample-1".into(),
                measured_endpoint: "SAG".into(),
                model_input_endpoint: "BARRIER".into(),
            }],
        };
        assert_eq!(
            campaign.validate(),
            Err(TechnicalContractError::EndpointLeakage)
        );
        campaign.endpoint_links[0].model_input_endpoint = "SAG".into();
        campaign.validate().unwrap();
    }
}
