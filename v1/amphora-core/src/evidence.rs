use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::fs::{self, File, OpenOptions};
use std::io::{Read, Write};
use std::path::{Component, Path, PathBuf};
use thiserror::Error;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct AcceptedArtifact {
    pub sha256: String,
    pub size_bytes: u64,
    pub stored_path: PathBuf,
}

#[derive(Debug, Error)]
pub enum EvidenceIntakeError {
    #[error("evidence path must be a traversal-free relative path")]
    UnsafePath,
    #[error("evidence path is outside the configured capability root")]
    OutsideRoot,
    #[error("evidence path contains a symlink")]
    Symlink,
    #[error("evidence target is not a regular file")]
    NotRegular,
    #[error("evidence bytes changed while hashing")]
    Mutated,
    #[error("evidence content hash does not match the signed manifest")]
    HashMismatch,
    #[error("evidence I/O: {0}")]
    Io(#[from] std::io::Error),
}

pub fn intake_regular_file(
    capability_root: &Path,
    relative_path: &Path,
    content_store: &Path,
    expected_sha256: &str,
) -> Result<AcceptedArtifact, EvidenceIntakeError> {
    if relative_path.is_absolute()
        || relative_path
            .components()
            .any(|component| !matches!(component, Component::Normal(_)))
    {
        return Err(EvidenceIntakeError::UnsafePath);
    }
    let root = capability_root.canonicalize()?;
    let mut current = root.clone();
    for component in relative_path.components() {
        let Component::Normal(name) = component else {
            return Err(EvidenceIntakeError::UnsafePath);
        };
        current.push(name);
        let metadata = fs::symlink_metadata(&current)?;
        if metadata.file_type().is_symlink() {
            return Err(EvidenceIntakeError::Symlink);
        }
    }
    let canonical = current.canonicalize()?;
    if !canonical.starts_with(&root) {
        return Err(EvidenceIntakeError::OutsideRoot);
    }
    let before = fs::metadata(&canonical)?;
    if !before.is_file() {
        return Err(EvidenceIntakeError::NotRegular);
    }
    let mut file = File::open(&canonical)?;
    let opened_before = file.metadata()?;
    if !opened_before.is_file() {
        return Err(EvidenceIntakeError::NotRegular);
    }
    let mut digest = Sha256::new();
    let mut buffer = [0_u8; 64 * 1024];
    loop {
        let count = file.read(&mut buffer)?;
        if count == 0 {
            break;
        }
        digest.update(&buffer[..count]);
    }
    let after = file.metadata()?;
    if opened_before.len() != after.len()
        || opened_before.modified().ok() != after.modified().ok()
        || before.len() != after.len()
        || before.modified().ok() != after.modified().ok()
    {
        return Err(EvidenceIntakeError::Mutated);
    }
    let sha256 = format!("{:x}", digest.finalize());
    if sha256 != expected_sha256 {
        return Err(EvidenceIntakeError::HashMismatch);
    }
    let store = if content_store.exists() {
        content_store.canonicalize()?
    } else {
        fs::create_dir_all(content_store)?;
        content_store.canonicalize()?
    };
    let shard = store.join(&sha256[..2]);
    fs::create_dir_all(&shard)?;
    if fs::symlink_metadata(&shard)?.file_type().is_symlink() {
        return Err(EvidenceIntakeError::Symlink);
    }
    let destination = shard.join(&sha256);
    if destination.exists() {
        let metadata = fs::symlink_metadata(&destination)?;
        if metadata.file_type().is_symlink() || !metadata.is_file() {
            return Err(EvidenceIntakeError::NotRegular);
        }
        if hash_file(&destination)? != sha256 {
            return Err(EvidenceIntakeError::HashMismatch);
        }
    } else {
        let temporary = shard.join(format!(".{sha256}.tmp-{}", std::process::id()));
        if temporary.exists() {
            fs::remove_file(&temporary)?;
        }
        let mut output = OpenOptions::new()
            .create_new(true)
            .write(true)
            .open(&temporary)?;
        let mut input = File::open(&canonical)?;
        std::io::copy(&mut input, &mut output)?;
        output.flush()?;
        output.sync_all()?;
        match fs::hard_link(&temporary, &destination) {
            Ok(()) => {}
            Err(error) if error.kind() == std::io::ErrorKind::AlreadyExists => {
                if hash_file(&destination)? != sha256 {
                    fs::remove_file(&temporary)?;
                    return Err(EvidenceIntakeError::HashMismatch);
                }
            }
            Err(error) => {
                fs::remove_file(&temporary)?;
                return Err(error.into());
            }
        }
        fs::remove_file(&temporary)?;
    }
    Ok(AcceptedArtifact {
        sha256,
        size_bytes: after.len(),
        stored_path: destination,
    })
}

fn hash_file(path: &Path) -> Result<String, std::io::Error> {
    let mut file = File::open(path)?;
    let mut digest = Sha256::new();
    let mut buffer = [0_u8; 64 * 1024];
    loop {
        let count = file.read(&mut buffer)?;
        if count == 0 {
            break;
        }
        digest.update(&buffer[..count]);
    }
    Ok(format!("{:x}", digest.finalize()))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn rejects_traversal_before_filesystem_access() {
        let error = intake_regular_file(
            Path::new("."),
            Path::new("../outside"),
            Path::new("store"),
            "unused",
        )
        .unwrap_err();
        assert!(matches!(error, EvidenceIntakeError::UnsafePath));
    }
}
