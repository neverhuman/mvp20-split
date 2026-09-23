use crate::{
    strict_from_value, ExpertPacketV1, IndependentReviewV1, PotLifeBenchmarkLockV1, PotLifeError,
    PotLifeModelArtifactV1, PotLifePredictionV1, PotLifeProtocolV1, PotLifeRunV1,
    PotLifeScaleQualificationV1,
};
use serde_json::Value;
use std::collections::BTreeMap;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PotLifeContractKind {
    ScaleQualification,
    Run,
    Protocol,
    BenchmarkLock,
    ModelArtifact,
    Prediction,
    IndependentReview,
    ExpertPacket,
}

impl PotLifeContractKind {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::ScaleQualification => "scale-qualification",
            Self::Run => "run",
            Self::Protocol => "protocol",
            Self::BenchmarkLock => "benchmark-lock",
            Self::ModelArtifact => "model-artifact",
            Self::Prediction => "prediction",
            Self::IndependentReview => "independent-review",
            Self::ExpertPacket => "expert-packet",
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PotLifeContractPreflight {
    pub kind: PotLifeContractKind,
    pub schema: String,
    pub track_id: Option<String>,
    pub contract_id: String,
    pub raw_file_hashes: BTreeMap<String, String>,
}

pub fn preflight_contract(
    kind: PotLifeContractKind,
    value: Value,
) -> Result<PotLifeContractPreflight, PotLifeError> {
    let (schema, track_id, contract_id, raw_file_hashes) = match kind {
        PotLifeContractKind::ScaleQualification => {
            let contract: PotLifeScaleQualificationV1 = strict_from_value(value)?;
            contract.validate()?;
            (
                contract.schema,
                None,
                contract.qualification_id,
                BTreeMap::new(),
            )
        }
        PotLifeContractKind::Run => {
            let contract: PotLifeRunV1 = strict_from_value(value)?;
            contract.validate()?;
            (
                contract.schema,
                Some(contract.track_id),
                contract.run_id,
                contract.raw_file_hashes,
            )
        }
        PotLifeContractKind::Protocol => {
            let contract: PotLifeProtocolV1 = strict_from_value(value)?;
            contract.validate()?;
            (
                contract.schema,
                Some(contract.track_id),
                contract.protocol_id,
                BTreeMap::new(),
            )
        }
        PotLifeContractKind::BenchmarkLock => {
            let contract: PotLifeBenchmarkLockV1 = strict_from_value(value)?;
            contract.validate()?;
            (
                contract.schema,
                Some(contract.track_id),
                contract.benchmark_id,
                BTreeMap::new(),
            )
        }
        PotLifeContractKind::ModelArtifact => {
            let contract: PotLifeModelArtifactV1 = strict_from_value(value)?;
            contract.validate()?;
            (
                contract.schema,
                Some(contract.track_id),
                contract.model_id,
                BTreeMap::new(),
            )
        }
        PotLifeContractKind::Prediction => {
            let contract: PotLifePredictionV1 = strict_from_value(value)?;
            contract.validate()?;
            (
                contract.schema,
                Some(contract.track_id),
                contract.prediction_id,
                BTreeMap::new(),
            )
        }
        PotLifeContractKind::IndependentReview => {
            let contract: IndependentReviewV1 = strict_from_value(value)?;
            contract.validate()?;
            (
                contract.schema,
                Some(contract.track_id),
                contract.reviewer_id,
                BTreeMap::new(),
            )
        }
        PotLifeContractKind::ExpertPacket => {
            let contract: ExpertPacketV1 = strict_from_value(value)?;
            contract.validate()?;
            (
                contract.schema,
                Some(contract.track_id),
                contract.packet_id,
                BTreeMap::new(),
            )
        }
    };
    Ok(PotLifeContractPreflight {
        kind,
        schema,
        track_id,
        contract_id,
        raw_file_hashes,
    })
}
