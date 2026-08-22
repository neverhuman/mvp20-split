//! Run one solver-lab demo and write its canonical diagnostic bytes.
//! Two-replay protocol: invoke twice with different output paths
//! (diagnostic.canonical.json, diagnostic.runB.json); the DSSE signer
//! refuses to sign unless the two files are byte-identical.

use amphora_solver_lab::demos;
use amphora_solver_lab::oracle::sha256_hex;
use anyhow::{Context, Result};
use std::path::Path;

fn main() -> Result<()> {
    let args: Vec<String> = std::env::args().collect();
    anyhow::ensure!(
        args.len() == 3,
        "usage: solver_lab_demo <p1|p3|p4> <output_path>"
    );
    let bytes = demos::run(&args[1])?;
    let out = Path::new(&args[2]);
    if let Some(parent) = out.parent() {
        std::fs::create_dir_all(parent).context("creating output directory")?;
    }
    std::fs::write(out, &bytes).with_context(|| format!("writing {}", out.display()))?;
    eprintln!(
        "wrote {} ({} bytes, sha256 {})",
        out.display(),
        bytes.len(),
        sha256_hex(&bytes)
    );
    Ok(())
}
