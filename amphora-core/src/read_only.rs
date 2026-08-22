use sha2::{Digest, Sha256};
use std::fs;
use std::io::{self, Read};
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::mpsc;
use std::thread;
use thiserror::Error;

#[derive(Debug, Error)]
pub enum ReadOnlyError {
    #[error("repository tree I/O: {0}")]
    Io(#[from] io::Error),
    #[error("read-only command changed the repository tree: before={before}, after={after}")]
    Changed { before: String, after: String },
}

/// Hash the scoped repository tree from sorted relative paths, file types,
/// modes, sizes, and file bytes. Only build products and external tool caches
/// are excluded; evidence, configuration, reports, and `.amphora` are covered.
pub fn repository_tree_hash(root: &Path) -> Result<String, ReadOnlyError> {
    let mut files = Vec::new();
    collect(root, root, &mut files)?;
    files.sort();
    let records = hash_records_parallel(root, &files)?;
    let mut tree = Sha256::new();
    for (relative, record) in files.into_iter().zip(records) {
        tree.update(relative.to_string_lossy().as_bytes());
        tree.update([0, record.kind]);
        tree.update(record.mode.to_le_bytes());
        tree.update(record.len.to_le_bytes());
        tree.update(record.content_digest);
        tree.update([0xff]);
    }
    Ok(format!("{:x}", tree.finalize()))
}

struct FileRecord {
    kind: u8,
    mode: u32,
    len: u64,
    content_digest: Vec<u8>,
}

fn hash_records_parallel(root: &Path, files: &[PathBuf]) -> io::Result<Vec<FileRecord>> {
    if files.is_empty() {
        return Ok(Vec::new());
    }
    let workers = thread::available_parallelism()
        .map(usize::from)
        .unwrap_or(1)
        .min(16)
        .min(files.len());
    let next = AtomicUsize::new(0);
    let (sender, receiver) = mpsc::channel();
    thread::scope(|scope| {
        for _ in 0..workers {
            let sender = sender.clone();
            let next = &next;
            scope.spawn(move || loop {
                let index = next.fetch_add(1, Ordering::Relaxed);
                let Some(relative) = files.get(index) else {
                    break;
                };
                let result = hash_record(&root.join(relative));
                if sender.send((index, result)).is_err() {
                    break;
                }
            });
        }
        drop(sender);
        let mut records = (0..files.len()).map(|_| None).collect::<Vec<_>>();
        for (index, result) in receiver {
            records[index] = Some(result?);
        }
        records
            .into_iter()
            .map(|record| record.ok_or_else(|| io::Error::other("tree hash worker stopped")))
            .collect()
    })
}

fn hash_record(path: &Path) -> io::Result<FileRecord> {
    let metadata = fs::symlink_metadata(path)?;
    let kind = if metadata.file_type().is_symlink() {
        b'L'
    } else if metadata.file_type().is_file() {
        b'F'
    } else {
        b'O'
    };
    let content_digest = if metadata.file_type().is_symlink() {
        Sha256::digest(fs::read_link(path)?.to_string_lossy().as_bytes()).to_vec()
    } else if metadata.file_type().is_file() {
        let mut file = fs::File::open(path)?;
        let mut hasher = Sha256::new();
        let mut buffer = vec![0_u8; 1024 * 1024];
        loop {
            let count = file.read(&mut buffer)?;
            if count == 0 {
                break;
            }
            hasher.update(&buffer[..count]);
        }
        hasher.finalize().to_vec()
    } else {
        Sha256::digest([]).to_vec()
    };
    Ok(FileRecord {
        kind,
        mode: mode(&metadata),
        len: metadata.len(),
        content_digest,
    })
}

pub fn prove_read_only<T, E>(root: &Path, operation: impl FnOnce() -> Result<T, E>) -> Result<T, E>
where
    E: From<ReadOnlyError>,
{
    let before = repository_tree_hash(root).map_err(E::from)?;
    let result = operation();
    let after = repository_tree_hash(root).map_err(E::from)?;
    if before != after {
        return Err(E::from(ReadOnlyError::Changed { before, after }));
    }
    result
}

fn collect(root: &Path, directory: &Path, output: &mut Vec<PathBuf>) -> io::Result<()> {
    let mut entries = fs::read_dir(directory)?.collect::<Result<Vec<_>, _>>()?;
    entries.sort_by_key(|entry| entry.file_name());
    for entry in entries {
        let path = entry.path();
        let relative = path
            .strip_prefix(root)
            .expect("walked path remains below repository root");
        if excluded(relative) {
            continue;
        }
        let metadata = fs::symlink_metadata(&path)?;
        if metadata.file_type().is_dir() {
            collect(root, &path, output)?;
        } else {
            output.push(relative.to_path_buf());
        }
    }
    Ok(())
}

fn excluded(relative: &Path) -> bool {
    let mut components = relative.components();
    let first = components.next().map(|value| value.as_os_str());
    if matches!(
        first.and_then(|value| value.to_str()),
        Some(".git" | "target")
    ) {
        return true;
    }
    matches!(
        relative.to_str(),
        Some(path)
            if path.starts_with("artifacts/toolchains/cache/")
                || path.starts_with("artifacts/toolchains/.cache/")
                || path.starts_with(".codex/cache/")
    )
}

#[cfg(unix)]
fn mode(metadata: &fs::Metadata) -> u32 {
    use std::os::unix::fs::MetadataExt;
    metadata.mode()
}

#[cfg(not(unix))]
fn mode(metadata: &fs::Metadata) -> u32 {
    u32::from(metadata.permissions().readonly())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn mutation_is_detected_and_build_outputs_are_excluded() {
        let temporary = tempfile::tempdir().unwrap();
        fs::write(temporary.path().join("catalog.json"), b"locked").unwrap();
        fs::create_dir(temporary.path().join("target")).unwrap();
        let unchanged = prove_read_only::<_, ReadOnlyError>(temporary.path(), || {
            fs::write(temporary.path().join("target/build.log"), b"ignored")?;
            Ok(())
        });
        assert!(unchanged.is_ok());
        let changed = prove_read_only::<_, ReadOnlyError>(temporary.path(), || {
            fs::write(temporary.path().join("catalog.json"), b"altered")?;
            Ok(())
        });
        assert!(matches!(changed, Err(ReadOnlyError::Changed { .. })));

        fs::write(temporary.path().join("catalog.json"), b"locked").unwrap();
        let changed_before_error = prove_read_only::<(), ReadOnlyError>(temporary.path(), || {
            fs::write(temporary.path().join("catalog.json"), b"altered")?;
            Err(ReadOnlyError::Io(io::Error::other("operation failed")))
        });
        assert!(matches!(
            changed_before_error,
            Err(ReadOnlyError::Changed { .. })
        ));
    }
}
