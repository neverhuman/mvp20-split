//! Sha256-pinned read-only oracles over already-signed KPI/receipt JSON in
//! the tree. No live model calls, no new science: an oracle can only surface
//! numbers that already exist in a pinned, signed artifact, and it records the
//! source path + sha256 it read. A pin mismatch (tampered or superseded
//! source) is a refusal, not a warning.

use serde::Deserialize;
use serde_json::Value;
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;
use std::path::{Path, PathBuf};

pub const PINS_SCHEMA: &str = "amphora.solver-lab.source-pins.v1";

#[derive(Debug, thiserror::Error)]
pub enum OracleError {
    #[error("pins file {0} unreadable/invalid: {1}")]
    PinsInvalid(String, String),
    #[error("no pin registered for logical id '{0}'; refusing to read an unpinned source (fail-closed)")]
    NoSuchPin(String),
    #[error("source unreadable for '{logical_id}' at {rel_path}: {err}")]
    SourceUnreadable {
        logical_id: String,
        rel_path: String,
        err: String,
    },
    #[error("SOURCE PIN MISMATCH for '{logical_id}' at {rel_path}: pinned sha256 {pinned} but on-disk bytes hash to {actual}; refusing tampered/superseded source (fail-closed)")]
    PinMismatch {
        logical_id: String,
        rel_path: String,
        pinned: String,
        actual: String,
    },
    #[error("source parse failure for '{logical_id}' at {rel_path}: {err}")]
    ParseFailure {
        logical_id: String,
        rel_path: String,
        err: String,
    },
}

#[derive(Debug, Clone, Deserialize)]
pub struct PinnedSource {
    pub logical_id: String,
    pub rel_path: String,
    pub sha256: String,
}

#[derive(Debug, Deserialize)]
struct PinsFile {
    schema: String,
    pins: Vec<PinnedSource>,
}

/// A completed oracle read: the parsed value plus the provenance record
/// (path + sha256) that every downstream diagnostic must embed.
#[derive(Debug, Clone)]
pub struct OracleReading {
    pub logical_id: String,
    pub rel_path: String,
    pub sha256: String,
    pub value: Value,
}

pub struct SourceOracle {
    repo_root: PathBuf,
    pins: BTreeMap<String, PinnedSource>,
}

pub fn sha256_hex(bytes: &[u8]) -> String {
    let digest = Sha256::digest(bytes);
    let mut s = String::with_capacity(64);
    for b in digest {
        s.push_str(&format!("{:02x}", b));
    }
    s
}

impl SourceOracle {
    /// Repo root as seen from this crate (compile-time manifest dir's parent).
    pub fn manifest_repo_root() -> PathBuf {
        Path::new(env!("CARGO_MANIFEST_DIR"))
            .parent()
            .expect("crate dir has a parent")
            .to_path_buf()
    }

    /// The crate's own pins file.
    pub fn pinned_default() -> Result<Self, OracleError> {
        let pins_path = Path::new(env!("CARGO_MANIFEST_DIR")).join("pins/source_pins.v1.json");
        Self::from_pins_file(Self::manifest_repo_root(), &pins_path)
    }

    pub fn from_pins_file(repo_root: PathBuf, pins_path: &Path) -> Result<Self, OracleError> {
        let shown = pins_path.display().to_string();
        let raw = std::fs::read(pins_path)
            .map_err(|e| OracleError::PinsInvalid(shown.clone(), e.to_string()))?;
        let parsed: PinsFile = serde_json::from_slice(&raw)
            .map_err(|e| OracleError::PinsInvalid(shown.clone(), e.to_string()))?;
        if parsed.schema != PINS_SCHEMA {
            return Err(OracleError::PinsInvalid(
                shown,
                format!("unexpected pins schema '{}'", parsed.schema),
            ));
        }
        let mut pins = BTreeMap::new();
        for p in parsed.pins {
            pins.insert(p.logical_id.clone(), p);
        }
        Ok(Self { repo_root, pins })
    }

    pub fn repo_root(&self) -> &Path {
        &self.repo_root
    }

    /// Deterministic (BTreeMap order) list of every registered pin.
    pub fn pin_list(&self) -> Vec<PinnedSource> {
        self.pins.values().cloned().collect()
    }

    /// Read a pinned source: bytes -> sha256 -> compare to pin -> parse.
    /// Any mismatch refuses; there is no override.
    pub fn read(&self, logical_id: &str) -> Result<OracleReading, OracleError> {
        let pin = self
            .pins
            .get(logical_id)
            .ok_or_else(|| OracleError::NoSuchPin(logical_id.to_string()))?;
        let path = self.repo_root.join(&pin.rel_path);
        let bytes = std::fs::read(&path).map_err(|e| OracleError::SourceUnreadable {
            logical_id: pin.logical_id.clone(),
            rel_path: pin.rel_path.clone(),
            err: e.to_string(),
        })?;
        let actual = sha256_hex(&bytes);
        if actual != pin.sha256 {
            return Err(OracleError::PinMismatch {
                logical_id: pin.logical_id.clone(),
                rel_path: pin.rel_path.clone(),
                pinned: pin.sha256.clone(),
                actual,
            });
        }
        let value: Value =
            serde_json::from_slice(&bytes).map_err(|e| OracleError::ParseFailure {
                logical_id: pin.logical_id.clone(),
                rel_path: pin.rel_path.clone(),
                err: e.to_string(),
            })?;
        Ok(OracleReading {
            logical_id: pin.logical_id.clone(),
            rel_path: pin.rel_path.clone(),
            sha256: actual,
            value,
        })
    }
}
