use sha2::{Digest, Sha256};
use std::fs;
use std::path::PathBuf;

const SCHEMA_FILES: [(&str, &str); 3] = [
    (
        "schema/ord-schema/proto/dataset.proto",
        "60f44fbf7b01c0e0d219d7017254c64034eaee8d739a148f33d53c36ecc52b11",
    ),
    (
        "schema/ord-schema/proto/reaction.proto",
        "f1546142d8b727f9c05aee7176287f1b0ff172966d125cd1f44b1a910530ceea",
    ),
    (
        "schema/ord-schema/proto/test.proto",
        "86cfe00045a1439463f33fc132f578e8eab942f7cc82bf6b7207e685f69c01e4",
    ),
];

fn main() -> Result<(), Box<dyn std::error::Error>> {
    for (path, expected) in SCHEMA_FILES {
        println!("cargo:rerun-if-changed={path}");
        let observed = sha256(&fs::read(path)?);
        if observed != expected {
            return Err(format!("pinned ORD schema hash mismatch for {path}: {observed}").into());
        }
    }
    println!("cargo:rerun-if-changed=schema/ord-schema-v0.6.3.descriptor.sha256");

    let out_dir = PathBuf::from(std::env::var_os("OUT_DIR").ok_or("OUT_DIR is unset")?);
    let descriptor_path = out_dir.join("ord-schema-v0.6.3.descriptor.pb");
    let protoc = protoc_bin_vendored::protoc_bin_path()?;
    let mut config = prost_build::Config::new();
    config.protoc_executable(protoc);
    config.file_descriptor_set_path(&descriptor_path);
    config.compile_protos(
        &[
            "schema/ord-schema/proto/dataset.proto",
            "schema/ord-schema/proto/reaction.proto",
            "schema/ord-schema/proto/test.proto",
        ],
        &["schema"],
    )?;

    let observed = sha256(&fs::read(&descriptor_path)?);
    let expected = fs::read_to_string("schema/ord-schema-v0.6.3.descriptor.sha256")?;
    if observed != expected.trim() {
        return Err(format!(
            "pinned ORD descriptor-set hash mismatch: expected {}, observed {observed}",
            expected.trim()
        )
        .into());
    }
    Ok(())
}

fn sha256(bytes: &[u8]) -> String {
    let mut digest = Sha256::new();
    digest.update(bytes);
    format!("{:x}", digest.finalize())
}
