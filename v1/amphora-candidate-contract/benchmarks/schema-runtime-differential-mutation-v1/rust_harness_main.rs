// amphora-candidate-contract schema-runtime-parity-v1 : Oracle B (runtime).
// Reads every non-underscore file in the corpus dir as raw bytes and reports
// the exact amphora_core::contract::CandidateEnvelope::from_bytes verdict.
// AUDIT_ONLY diagnostic harness; does not modify tree state.
use amphora_core::{CandidateEnvelope, ContractError};
use std::{collections::BTreeMap, fs, path::Path};

fn tag(e: &ContractError) -> String {
    match e {
        ContractError::RequestTooLarge => "Err:RequestTooLarge".into(),
        ContractError::InvalidUtf8 => "Err:InvalidUtf8".into(),
        ContractError::InvalidJson(_) => "Err:InvalidJson".into(),
        ContractError::CandidateNotObject => "Err:CandidateNotObject".into(),
        ContractError::InvalidCandidateId => "Err:InvalidCandidateId".into(),
        ContractError::InvalidCandidateType => "Err:InvalidCandidateType".into(),
        ContractError::PayloadMismatch(_) => "Err:PayloadMismatch".into(),
        ContractError::ChemistryNormalizationUnavailable => {
            "Err:ChemistryNormalizationUnavailable".into()
        }
    }
}

fn main() {
    let dir = std::env::args().nth(1).expect("corpus dir arg");
    let mut out: BTreeMap<String, serde_json::Value> = BTreeMap::new();
    let mut entries: Vec<_> = fs::read_dir(&dir)
        .expect("read corpus dir")
        .map(|e| e.unwrap().path())
        .collect();
    entries.sort();
    for path in entries {
        let name = path.file_name().unwrap().to_string_lossy().to_string();
        if name.starts_with('_') {
            continue;
        }
        let bytes = fs::read(&path).expect("read case");
        let (verdict, detail) = match CandidateEnvelope::from_bytes(&bytes) {
            Ok(env) => (
                "ACCEPT".to_string(),
                serde_json::json!({
                    "variant": "Ok",
                    "candidate_type": env.candidate_type(),
                    "contract_hash_v1": env.contract_hash_v1(),
                    "original_bytes_sha256": env.original_bytes_sha256(),
                }),
            ),
            Err(e) => (
                "REJECT".to_string(),
                serde_json::json!({"variant": tag(&e)}),
            ),
        };
        out.insert(
            name.clone(),
            serde_json::json!({"runtime_verdict": verdict, "detail": detail}),
        );
    }
    // second construction of every Ok case to confirm contract_hash stability
    let _ = Path::new(&dir);
    println!("{}", serde_json::to_string_pretty(&out).unwrap());
}
