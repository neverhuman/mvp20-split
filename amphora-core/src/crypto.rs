use base64::engine::general_purpose::STANDARD;
use base64::Engine;
use ed25519_dalek::{Signature, Signer, SigningKey, Verifier, VerifyingKey};
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet};
use thiserror::Error;

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct DsseEnvelope {
    pub payload_type: String,
    pub payload: String,
    pub signatures: Vec<DsseSignature>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DsseSignature {
    pub keyid: String,
    pub sig: String,
}

#[derive(Debug, Clone, Default)]
pub struct TrustStore {
    keys: BTreeMap<String, VerifyingKey>,
    revoked: BTreeSet<String>,
}

impl TrustStore {
    pub fn insert(
        &mut self,
        key_id: impl Into<String>,
        public_key: [u8; 32],
    ) -> Result<(), VerificationError> {
        let key_id = key_id.into();
        if self.keys.contains_key(&key_id) {
            return Err(VerificationError::DuplicateKey(key_id));
        }
        let key = VerifyingKey::from_bytes(&public_key)
            .map_err(|_| VerificationError::InvalidPublicKey(key_id.clone()))?;
        self.keys.insert(key_id, key);
        Ok(())
    }

    pub fn revoke(&mut self, key_id: impl Into<String>) {
        self.revoked.insert(key_id.into());
    }
}

#[derive(Debug, Clone)]
pub struct VerifiedPayload {
    pub key_id: String,
    pub payload_type: String,
    pub payload: Vec<u8>,
}

pub fn sign_dsse(
    payload_type: &str,
    payload: &[u8],
    key_id: &str,
    signing_key: &SigningKey,
) -> DsseEnvelope {
    let signature = signing_key.sign(&pae(payload_type, payload));
    DsseEnvelope {
        payload_type: payload_type.to_owned(),
        payload: STANDARD.encode(payload),
        signatures: vec![DsseSignature {
            keyid: key_id.to_owned(),
            sig: STANDARD.encode(signature.to_bytes()),
        }],
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct RemoteResultBinding {
    pub scorer_binary_hash: String,
    pub candidate_hash: String,
    pub model_hash: String,
    pub dataset_hash: String,
    pub policy_hash: String,
    pub output_hash: String,
    pub nonce: String,
    pub expires_at_unix: u64,
}

#[derive(Debug, Error)]
pub enum VerificationError {
    #[error("DSSE payload encoding is invalid")]
    PayloadEncoding,
    #[error("DSSE signature encoding is invalid for key {0}")]
    SignatureEncoding(String),
    #[error("unknown DSSE signing key {0}")]
    UnknownKey(String),
    #[error("revoked DSSE signing key {0}")]
    RevokedKey(String),
    #[error("invalid Ed25519 public key {0}")]
    InvalidPublicKey(String),
    #[error("duplicate Ed25519 key ID {0}")]
    DuplicateKey(String),
    #[error("DSSE signature verification failed")]
    Signature,
    #[error("DSSE envelope has no signatures")]
    MissingSignature,
    #[error("remote result payload type is not authorized")]
    PayloadType,
    #[error("remote result binding is malformed: {0}")]
    Binding(String),
    #[error("remote result binding does not match the requested execution")]
    BindingMismatch,
    #[error("remote result binding is expired")]
    Expired,
}

pub fn verify_dsse(
    envelope: &DsseEnvelope,
    trust_store: &TrustStore,
) -> Result<VerifiedPayload, VerificationError> {
    if envelope.signatures.is_empty() {
        return Err(VerificationError::MissingSignature);
    }
    let payload = STANDARD
        .decode(envelope.payload.as_bytes())
        .map_err(|_| VerificationError::PayloadEncoding)?;
    let message = pae(&envelope.payload_type, &payload);
    let mut saw_trusted_key = false;
    for row in &envelope.signatures {
        if trust_store.revoked.contains(&row.keyid) {
            return Err(VerificationError::RevokedKey(row.keyid.clone()));
        }
        let Some(key) = trust_store.keys.get(&row.keyid) else {
            continue;
        };
        saw_trusted_key = true;
        let bytes = STANDARD
            .decode(row.sig.as_bytes())
            .map_err(|_| VerificationError::SignatureEncoding(row.keyid.clone()))?;
        let signature = Signature::from_slice(&bytes)
            .map_err(|_| VerificationError::SignatureEncoding(row.keyid.clone()))?;
        if key.verify(&message, &signature).is_ok() {
            return Ok(VerifiedPayload {
                key_id: row.keyid.clone(),
                payload_type: envelope.payload_type.clone(),
                payload,
            });
        }
    }
    if saw_trusted_key {
        Err(VerificationError::Signature)
    } else {
        Err(VerificationError::UnknownKey(
            envelope.signatures[0].keyid.clone(),
        ))
    }
}

pub fn verify_remote_result(
    envelope: &DsseEnvelope,
    trust_store: &TrustStore,
    expected: &RemoteResultBinding,
    now_unix: u64,
) -> Result<VerifiedPayload, VerificationError> {
    const PAYLOAD_TYPE: &str = "application/vnd.amphora.remote-result.v1+json";
    if envelope.payload_type != PAYLOAD_TYPE {
        return Err(VerificationError::PayloadType);
    }
    let verified = verify_dsse(envelope, trust_store)?;
    let value = crate::parse_json_strict(&verified.payload)
        .map_err(|error| VerificationError::Binding(error.to_string()))?;
    let binding: RemoteResultBinding = serde_json::from_value(value)
        .map_err(|error| VerificationError::Binding(error.to_string()))?;
    if [
        &binding.scorer_binary_hash,
        &binding.candidate_hash,
        &binding.model_hash,
        &binding.dataset_hash,
        &binding.policy_hash,
        &binding.output_hash,
        &binding.nonce,
    ]
    .iter()
    .any(|value| value.is_empty())
    {
        return Err(VerificationError::Binding(
            "required binding field is empty".into(),
        ));
    }
    if binding.expires_at_unix < now_unix {
        return Err(VerificationError::Expired);
    }
    if &binding != expected {
        return Err(VerificationError::BindingMismatch);
    }
    Ok(verified)
}

fn pae(payload_type: &str, payload: &[u8]) -> Vec<u8> {
    format!(
        "DSSEv1 {} {} {} ",
        payload_type.len(),
        payload_type,
        payload.len()
    )
    .into_bytes()
    .into_iter()
    .chain(payload.iter().copied())
    .collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use ed25519_dalek::{Signer, SigningKey};

    #[test]
    fn verifies_ed25519_dsse_and_rejects_revocation() {
        let signing = SigningKey::from_bytes(&[7; 32]);
        let payload = br#"{"candidate_hash":"abc"}"#;
        let payload_type = "application/vnd.amphora.remote-result.v1+json";
        let signature = signing.sign(&pae(payload_type, payload));
        let envelope = DsseEnvelope {
            payload_type: payload_type.into(),
            payload: STANDARD.encode(payload),
            signatures: vec![DsseSignature {
                keyid: "test".into(),
                sig: STANDARD.encode(signature.to_bytes()),
            }],
        };
        let mut trust = TrustStore::default();
        trust
            .insert("test", signing.verifying_key().to_bytes())
            .unwrap();
        assert_eq!(verify_dsse(&envelope, &trust).unwrap().payload, payload);
        trust.revoke("test");
        assert!(matches!(
            verify_dsse(&envelope, &trust),
            Err(VerificationError::RevokedKey(_))
        ));
    }

    #[test]
    fn trust_store_rejects_key_id_overwrite() {
        let first = SigningKey::from_bytes(&[7; 32]);
        let second = SigningKey::from_bytes(&[8; 32]);
        let mut trust = TrustStore::default();
        trust
            .insert("stable-id", first.verifying_key().to_bytes())
            .unwrap();
        assert!(matches!(
            trust.insert("stable-id", second.verifying_key().to_bytes()),
            Err(VerificationError::DuplicateKey(key)) if key == "stable-id"
        ));
    }
}
