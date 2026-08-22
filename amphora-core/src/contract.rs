use serde::de::{self, DeserializeSeed, MapAccess, SeqAccess, Visitor};
use serde_json::{Map, Value};
use sha2::{Digest, Sha256};
use std::collections::BTreeSet;
use std::fmt;
use thiserror::Error;

pub const MAX_JSON_BYTES: usize = 8 * 1024 * 1024;
pub const MAX_JSON_DEPTH: usize = 64;
pub const MAX_COLLECTION_ENTRIES: usize = 100_000;

#[derive(Debug, Error)]
pub enum ContractError {
    #[error("JSON request exceeds {MAX_JSON_BYTES} bytes")]
    RequestTooLarge,
    #[error("JSON input is not valid UTF-8")]
    InvalidUtf8,
    #[error("invalid JSON: {0}")]
    InvalidJson(String),
    #[error("candidate envelope must be an object")]
    CandidateNotObject,
    #[error("candidate_id must be a non-empty string")]
    InvalidCandidateId,
    #[error("candidate_type must be molecule, formulation, or evidence_package")]
    InvalidCandidateType,
    #[error("candidate payload does not match candidate_type {0}")]
    PayloadMismatch(String),
    #[error("v2 chemistry input requires the pinned RDKit normalization boundary")]
    ChemistryNormalizationUnavailable,
}

#[derive(Default)]
struct ParseBudget {
    entries: usize,
}

struct StrictSeed<'a> {
    budget: &'a mut ParseBudget,
    depth: usize,
}

impl<'de> DeserializeSeed<'de> for StrictSeed<'_> {
    type Value = Value;

    fn deserialize<D>(self, deserializer: D) -> Result<Self::Value, D::Error>
    where
        D: de::Deserializer<'de>,
    {
        if self.depth > MAX_JSON_DEPTH {
            return Err(de::Error::custom(format!(
                "JSON depth exceeds {MAX_JSON_DEPTH}"
            )));
        }
        deserializer.deserialize_any(StrictVisitor {
            budget: self.budget,
            depth: self.depth,
        })
    }
}

struct StrictVisitor<'a> {
    budget: &'a mut ParseBudget,
    depth: usize,
}

impl<'de> Visitor<'de> for StrictVisitor<'_> {
    type Value = Value;

    fn expecting(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("a JSON value")
    }

    fn visit_bool<E>(self, value: bool) -> Result<Self::Value, E> {
        Ok(Value::Bool(value))
    }

    fn visit_i64<E>(self, value: i64) -> Result<Self::Value, E> {
        Ok(Value::Number(value.into()))
    }

    fn visit_u64<E>(self, value: u64) -> Result<Self::Value, E> {
        Ok(Value::Number(value.into()))
    }

    fn visit_f64<E>(self, value: f64) -> Result<Self::Value, E>
    where
        E: de::Error,
    {
        if !value.is_finite() {
            return Err(E::custom("non-finite JSON number"));
        }
        serde_json::Number::from_f64(value)
            .map(Value::Number)
            .ok_or_else(|| E::custom("non-finite JSON number"))
    }

    fn visit_str<E>(self, value: &str) -> Result<Self::Value, E> {
        Ok(Value::String(value.to_owned()))
    }

    fn visit_string<E>(self, value: String) -> Result<Self::Value, E> {
        Ok(Value::String(value))
    }

    fn visit_none<E>(self) -> Result<Self::Value, E> {
        Ok(Value::Null)
    }

    fn visit_unit<E>(self) -> Result<Self::Value, E> {
        Ok(Value::Null)
    }

    fn visit_some<D>(self, deserializer: D) -> Result<Self::Value, D::Error>
    where
        D: de::Deserializer<'de>,
    {
        StrictSeed {
            budget: self.budget,
            depth: self.depth,
        }
        .deserialize(deserializer)
    }

    fn visit_seq<A>(self, mut sequence: A) -> Result<Self::Value, A::Error>
    where
        A: SeqAccess<'de>,
    {
        let mut values = Vec::new();
        while let Some(value) = sequence.next_element_seed(StrictSeed {
            budget: self.budget,
            depth: self.depth + 1,
        })? {
            values.push(value);
            self.budget.entries += 1;
            if values.len() > MAX_COLLECTION_ENTRIES || self.budget.entries > MAX_COLLECTION_ENTRIES
            {
                return Err(de::Error::custom(format!(
                    "JSON collection entries exceed {MAX_COLLECTION_ENTRIES}"
                )));
            }
        }
        Ok(Value::Array(values))
    }

    fn visit_map<A>(self, mut object: A) -> Result<Self::Value, A::Error>
    where
        A: MapAccess<'de>,
    {
        let mut values = Map::new();
        let mut keys = BTreeSet::new();
        while let Some(key) = object.next_key::<String>()? {
            if !keys.insert(key.clone()) {
                return Err(de::Error::custom(format!("duplicate JSON key: {key}")));
            }
            let value = object.next_value_seed(StrictSeed {
                budget: self.budget,
                depth: self.depth + 1,
            })?;
            values.insert(key, value);
            self.budget.entries += 1;
            if values.len() > MAX_COLLECTION_ENTRIES || self.budget.entries > MAX_COLLECTION_ENTRIES
            {
                return Err(de::Error::custom(format!(
                    "JSON collection entries exceed {MAX_COLLECTION_ENTRIES}"
                )));
            }
        }
        Ok(Value::Object(values))
    }
}

pub fn parse_json_strict(bytes: &[u8]) -> Result<Value, ContractError> {
    if bytes.len() > MAX_JSON_BYTES {
        return Err(ContractError::RequestTooLarge);
    }
    std::str::from_utf8(bytes).map_err(|_| ContractError::InvalidUtf8)?;
    let mut deserializer = serde_json::Deserializer::from_slice(bytes);
    let mut budget = ParseBudget::default();
    let value = StrictSeed {
        budget: &mut budget,
        depth: 0,
    }
    .deserialize(&mut deserializer)
    .map_err(|error| ContractError::InvalidJson(error.to_string()))?;
    deserializer
        .end()
        .map_err(|error| ContractError::InvalidJson(error.to_string()))?;
    Ok(value)
}

#[derive(Debug, Clone)]
pub struct CandidateEnvelope {
    value: Value,
    original_bytes_sha256: String,
    contract_hash_v1: String,
}

impl CandidateEnvelope {
    pub fn from_bytes(bytes: &[u8]) -> Result<Self, ContractError> {
        let value = parse_json_strict(bytes)?;
        let original_bytes_sha256 = sha256(bytes);
        Self::build(value, original_bytes_sha256)
    }

    pub fn from_value(value: Value) -> Result<Self, ContractError> {
        let canonical =
            serde_json::to_vec(&crate::canonicalize(&value)).expect("JSON values are serializable");
        Self::build(value, sha256(&canonical))
    }

    fn build(value: Value, original_bytes_sha256: String) -> Result<Self, ContractError> {
        let object = value.as_object().ok_or(ContractError::CandidateNotObject)?;
        let candidate_id = object
            .get("candidate_id")
            .and_then(Value::as_str)
            .filter(|value| !value.is_empty())
            .ok_or(ContractError::InvalidCandidateId)?;
        let _ = candidate_id;
        let candidate_type = object
            .get("candidate_type")
            .and_then(Value::as_str)
            .ok_or(ContractError::InvalidCandidateType)?;
        let required_payload = match candidate_type {
            "molecule" => "molecule",
            "formulation" => "formulation",
            "evidence_package" => "evidence_refs",
            _ => return Err(ContractError::InvalidCandidateType),
        };
        if !object.get(required_payload).is_some_and(Value::is_object) {
            return Err(ContractError::PayloadMismatch(candidate_type.to_owned()));
        }
        let chemistry_v2 = [
            "inchi",
            "inchi_key",
            "inchikey",
            "mol",
            "mol_block",
            "mol_v2000",
            "mol_v3000",
            "sdf",
            "sdf_records",
            "recipe_csv",
        ]
        .iter()
        .any(|key| object.contains_key(*key));
        if chemistry_v2 {
            let opted_in = object.get("schema_version").and_then(Value::as_str)
                == Some("amphora.candidate-envelope.v2");
            if !opted_in {
                return Err(ContractError::PayloadMismatch(candidate_type.to_owned()));
            }
            return Err(ContractError::ChemistryNormalizationUnavailable);
        }
        let contract_hash_v1 = crate::stable_hash(&value);
        Ok(Self {
            value,
            original_bytes_sha256,
            contract_hash_v1,
        })
    }

    pub fn candidate_id(&self) -> &str {
        self.value["candidate_id"]
            .as_str()
            .expect("validated candidate_id")
    }

    pub fn candidate_type(&self) -> &str {
        self.value["candidate_type"]
            .as_str()
            .expect("validated candidate_type")
    }

    pub fn value(&self) -> &Value {
        &self.value
    }

    pub fn into_value(self) -> Value {
        self.value
    }

    pub fn original_bytes_sha256(&self) -> &str {
        &self.original_bytes_sha256
    }

    pub fn contract_hash_v1(&self) -> &str {
        &self.contract_hash_v1
    }
}

fn sha256(bytes: &[u8]) -> String {
    let mut digest = Sha256::new();
    digest.update(bytes);
    format!("{:x}", digest.finalize())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn strict_parser_rejects_duplicate_and_escaped_duplicate_keys() {
        for payload in [br#"{"a":1,"a":2}"#.as_slice(), br#"{"a":1,"\u0061":2}"#] {
            let error = parse_json_strict(payload).unwrap_err().to_string();
            assert!(error.contains("duplicate JSON key"));
        }
    }

    #[test]
    fn strict_parser_rejects_invalid_utf8_and_excess_depth() {
        assert!(matches!(
            parse_json_strict(&[0xff]),
            Err(ContractError::InvalidUtf8)
        ));
        let payload = format!("{}0{}", "[".repeat(65), "]".repeat(65));
        assert!(parse_json_strict(payload.as_bytes()).is_err());
    }

    #[test]
    fn candidate_keeps_original_and_v1_hashes_separate() {
        let compact =
            br#"{"candidate_id":"x","candidate_type":"molecule","molecule":{"smiles":"C"}}"#;
        let spaced =
            br#"{ "molecule":{"smiles":"C"}, "candidate_type":"molecule", "candidate_id":"x" }"#;
        let first = CandidateEnvelope::from_bytes(compact).unwrap();
        let second = CandidateEnvelope::from_bytes(spaced).unwrap();
        assert_eq!(first.contract_hash_v1(), second.contract_hash_v1());
        assert_ne!(
            first.original_bytes_sha256(),
            second.original_bytes_sha256()
        );
    }
}
