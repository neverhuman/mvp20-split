use serde::Serialize;
use sha2::{Digest, Sha256};
use thiserror::Error;

/// Errors raised while producing or checking RFC 8785 JSON Canonicalization
/// Scheme bytes.
#[derive(Debug, Error)]
pub enum JcsError {
    #[error("JCS serialization failed: {0}")]
    Serialization(#[from] serde_json::Error),
    #[error("expected JCS SHA-256 must be 64 lowercase hexadecimal characters and nonzero")]
    InvalidExpectedHash,
    #[error("JCS SHA-256 mismatch: expected {expected}, observed {observed}")]
    HashMismatch { expected: String, observed: String },
}

/// Serialize a value to the exact RFC 8785 JCS byte representation.
///
/// Non-finite floating-point values are rejected by the pinned serializer.
pub fn jcs_bytes<T: Serialize>(value: &T) -> Result<Vec<u8>, JcsError> {
    Ok(serde_jcs::to_vec(value)?)
}

/// Hash the exact RFC 8785 representation of a serializable value.
pub fn jcs_sha256<T: Serialize>(value: &T) -> Result<String, JcsError> {
    let bytes = jcs_bytes(value)?;
    let mut digest = Sha256::new();
    digest.update(bytes);
    Ok(format!("{:x}", digest.finalize()))
}

/// Verify a value against a nonzero, lowercase SHA-256 of its JCS bytes.
pub fn verify_jcs_sha256<T: Serialize>(value: &T, expected: &str) -> Result<(), JcsError> {
    if !is_nonzero_sha256(expected) {
        return Err(JcsError::InvalidExpectedHash);
    }
    let observed = jcs_sha256(value)?;
    if observed != expected {
        return Err(JcsError::HashMismatch {
            expected: expected.to_owned(),
            observed,
        });
    }
    Ok(())
}

fn is_nonzero_sha256(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
        && value.bytes().any(|byte| byte != b'0')
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::{json, Value};

    #[test]
    fn rfc8785_property_order_and_unicode_are_canonical() {
        let value = json!({
            "\u{20ac}": "Euro Sign",
            "\r": "Carriage Return",
            "\u{fb33}": "Hebrew Letter Dalet With Dagesh",
            "1": "One",
            "\u{1f600}": "Emoji: Grinning Face",
            "\u{0080}": "Control",
            "ö": "Latin Small Letter O With Diaeresis"
        });
        assert_eq!(
            String::from_utf8(jcs_bytes(&value).unwrap()).unwrap(),
            "{\"\\r\":\"Carriage Return\",\"1\":\"One\",\"\u{80}\":\"Control\",\"ö\":\"Latin Small Letter O With Diaeresis\",\"€\":\"Euro Sign\",\"😀\":\"Emoji: Grinning Face\",\"דּ\":\"Hebrew Letter Dalet With Dagesh\"}"
        );
    }

    #[test]
    fn rfc8785_number_formatting_is_ecmascript_compatible() {
        let values: Vec<Value> = serde_json::from_str(
            "[333333333.33333329,1E30,4.50,2e-3,0.000000000000000000000000001]",
        )
        .unwrap();
        assert_eq!(
            String::from_utf8(jcs_bytes(&values).unwrap()).unwrap(),
            "[333333333.3333333,1e+30,4.5,0.002,1e-27]"
        );
        assert_eq!(jcs_bytes(&-0.0_f64).unwrap(), b"0");
    }

    #[test]
    fn non_finite_values_and_invalid_expected_hashes_are_rejected() {
        for value in [f64::NAN, f64::INFINITY, f64::NEG_INFINITY] {
            assert!(jcs_bytes(&value).is_err());
        }
        let value = json!({"a": 1});
        assert!(matches!(
            verify_jcs_sha256(&value, &"0".repeat(64)),
            Err(JcsError::InvalidExpectedHash)
        ));
        assert!(matches!(
            verify_jcs_sha256(&value, &"a".repeat(64)),
            Err(JcsError::HashMismatch { .. })
        ));
        let digest = jcs_sha256(&value).unwrap();
        verify_jcs_sha256(&value, &digest).unwrap();
    }
}
