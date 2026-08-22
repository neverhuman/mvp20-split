#![forbid(unsafe_code)]

use amphora_core::{
    jcs_bytes, parse_json_strict, prove_read_only, verify_toolchain_profile, CompoundCampaignV2,
    FileArtifactBindingV1, MethodLockPayloadV1, MethodRegistryV1,
};
use amphora_engine::NativeRegistry;
use serde::Serialize;
use serde_json::json;
use serde_json::Value;
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, VecDeque};
use std::fs;
use std::io::{self, Write};
use std::path::{Path, PathBuf};
use std::process::Command;

#[derive(Serialize)]
struct RetirementRow {
    source_path: String,
    source_sha256: String,
    disposition: &'static str,
    rust_replacement: &'static str,
    verification: &'static str,
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .expect("xtask has workspace parent")
        .to_path_buf();
    let args: Vec<String> = std::env::args().collect();
    match args.get(1).map(String::as_str) {
        Some("audit") => prove_read_only(&root, || audit(&root)),
        Some("retire-python") => {
            let apply = args.iter().any(|argument| argument == "--apply");
            retire_python(&root, apply)
        }
        Some("rewrite-native-commands") => rewrite_native_commands(&root),
        Some("reconcile-native-evidence") => reconcile_native_evidence(&root),
        Some("snapshot-registry") => snapshot_registry(&root),
        Some("toolchain") => {
            if args.get(2).is_none_or(|value| value.as_str() != "verify") {
                Err("usage: cargo xtask toolchain verify --all".into())
            } else {
                let all = args.get(3).is_some_and(|value| value == "--all");
                if args.len() != 4 || !all {
                    return Err("usage: cargo xtask toolchain verify --all".into());
                }
                prove_read_only(&root, || toolchain_verify(&root, all))
            }
        }
        Some("compound-config") => {
            if args.len() != 3 || args.get(2).is_none_or(|value| value != "seal") {
                return Err("usage: cargo xtask compound-config seal".into());
            }
            compound_config_seal(&root)
        }
        Some("python-runtime-audit") => {
            let compound_paths = args.get(2).is_some_and(|value| value == "--compound-paths");
            if args.len() != 3 || !compound_paths {
                return Err("usage: cargo xtask python-runtime-audit --compound-paths".into());
            }
            python_runtime_audit(&root)
        }
        _ => {
            Err("usage: cargo xtask <audit|retire-python [--apply]|rewrite-native-commands|reconcile-native-evidence|snapshot-registry|toolchain verify --all|compound-config seal|python-runtime-audit --compound-paths>".into())
        }
    }
}

const METHOD_REGISTRY_PATH: &str = "config/program/epoxy-amine-method-registry.v1.json";
const COMPOUND_CAMPAIGN_V2_PATH: &str = "config/program/epoxy-amine-compound-campaign.v2.json";
const PROGRAM_SUMS_PATH: &str = "config/program/SHA256SUMS";

fn compound_config_seal(root: &Path) -> Result<(), Box<dyn std::error::Error>> {
    let registry_path = root.join(METHOD_REGISTRY_PATH);
    let registry_value = parse_json_strict(&fs::read(&registry_path)?)?;
    let mut registry: MethodRegistryV1 = serde_json::from_value(registry_value)?;

    let mut writes = BTreeMap::<PathBuf, Vec<u8>>::new();
    for card in registry.modules.values_mut() {
        let lock_path = root.join(&card.lock_path);
        let lock_value = parse_json_strict(&fs::read(&lock_path)?)?;
        let mut lock: MethodLockPayloadV1 = serde_json::from_value(lock_value)?;
        lock.seal_self_hash()?;
        let lock_bytes = jcs_bytes(&lock)?;
        if lock.module_id != card.module_id
            || lock.method_status != card.method_status
            || lock.method_version != card.method_version
            || lock.source_identity != card.source_identity
            || lock.applicability_boundary != card.applicability_boundary
            || lock.missing_evidence != card.missing_evidence
            || lock.non_acceptance_reason != card.non_acceptance_reason
            || lock.actual_authority != card.actual_authority
        {
            return Err(format!(
                "method lock payload does not match registry card: {}",
                card.module_id
            )
            .into());
        }
        card.lock_hash = lock.lock_hash.clone();
        card.lock_file_sha256 = sha256(&lock_bytes);
        writes.insert(lock_path, lock_bytes);
    }
    registry.seal_self_hash()?;
    let registry_bytes = jcs_bytes(&registry)?;

    let campaign_path = root.join(COMPOUND_CAMPAIGN_V2_PATH);
    let campaign_value = parse_json_strict(&fs::read(&campaign_path)?)?;
    let mut campaign: CompoundCampaignV2 = serde_json::from_value(campaign_value)?;
    refresh_campaign_binding_hashes(root, &mut campaign, &registry_bytes)?;
    campaign.seal_self_hash()?;
    let campaign_bytes = jcs_bytes(&campaign)?;

    // Validate the complete prospective state before staging a single byte.
    let staged_root = temporary_seal_root(root)?;
    for (path, bytes) in &writes {
        stage_relative(root, &staged_root, path, bytes)?;
    }
    stage_relative(root, &staged_root, &registry_path, &registry_bytes)?;
    stage_relative(root, &staged_root, &campaign_path, &campaign_bytes)?;
    mirror_campaign_bound_files(root, &staged_root, &campaign)?;
    registry.verify_files(&staged_root)?;
    campaign.verify_bound_files(&staged_root)?;

    let sums_path = root.join(PROGRAM_SUMS_PATH);
    let sums_bytes = sealed_program_sums(
        &fs::read_to_string(&sums_path)?,
        &[
            (METHOD_REGISTRY_PATH, sha256(&registry_bytes)),
            (COMPOUND_CAMPAIGN_V2_PATH, sha256(&campaign_bytes)),
        ],
    )?;
    writes.insert(registry_path, registry_bytes);
    writes.insert(campaign_path, campaign_bytes);
    writes.insert(sums_path, sums_bytes);

    commit_staged_writes(root, writes)?;
    let _ = fs::remove_dir_all(staged_root);
    println!(
        "{}",
        serde_json::to_string(&json!({
            "command": "compound-config seal",
            "campaign_manifest_jcs_sha256": campaign.manifest_jcs_sha256,
            "method_registry_jcs_sha256": registry.registry_hash,
            "sealed_method_locks": registry.modules.len(),
            "pass": true,
        }))?
    );
    Ok(())
}

fn refresh_campaign_binding_hashes(
    root: &Path,
    campaign: &mut CompoundCampaignV2,
    prospective_registry: &[u8],
) -> Result<(), Box<dyn std::error::Error>> {
    let registry_path = campaign.artifacts.method_registry.path.clone();
    let mut bindings: Vec<&mut FileArtifactBindingV1> = vec![
        &mut campaign.feedback_v3_catalog,
        &mut campaign.feedback_v4_catalog,
        &mut campaign.feedback_v5_catalog,
        &mut campaign.artifacts.ord_complete_tree,
        &mut campaign.artifacts.ord_schema_identity,
        &mut campaign.artifacts.ord_decoded_reactions,
        &mut campaign.artifacts.ord_exclusions,
        &mut campaign.artifacts.ord_split,
        &mut campaign.artifacts.ord_grammar,
        &mut campaign.artifacts.ord_rights_receipt,
        &mut campaign.artifacts.portable_toolchain_manifest,
        &mut campaign.artifacts.optimized_toolchain_manifest,
        &mut campaign.artifacts.reactive_group_ontology,
        &mut campaign.artifacts.method_registry,
        &mut campaign.artifacts.benchmark_lock_set,
    ];
    bindings.extend(campaign.artifacts.execution_profiles.iter_mut());
    for binding in bindings {
        // FileArtifactBindingV1 owns the safe-path and nonzero-hash policy.
        binding.sha256 = "f".repeat(64);
        binding.validate()?;
        binding.sha256 = if binding.path == registry_path {
            sha256(prospective_registry)
        } else {
            sha256(&fs::read(root.join(&binding.path)).map_err(|error| {
                format!("unresolved campaign artifact {}: {error}", binding.path)
            })?)
        };
    }
    Ok(())
}

fn temporary_seal_root(root: &Path) -> Result<PathBuf, Box<dyn std::error::Error>> {
    let base = root.join("target/compound-config-seal");
    if base.exists() {
        fs::remove_dir_all(&base)?;
    }
    fs::create_dir_all(&base)?;
    Ok(base)
}

fn stage_relative(
    root: &Path,
    staged_root: &Path,
    source_path: &Path,
    bytes: &[u8],
) -> Result<(), Box<dyn std::error::Error>> {
    let relative = source_path.strip_prefix(root)?;
    let destination = staged_root.join(relative);
    fs::create_dir_all(destination.parent().ok_or("staged path has no parent")?)?;
    fs::write(destination, bytes)?;
    Ok(())
}

fn mirror_campaign_bound_files(
    root: &Path,
    staged_root: &Path,
    campaign: &CompoundCampaignV2,
) -> Result<(), Box<dyn std::error::Error>> {
    let value = serde_json::to_value(campaign)?;
    let mut paths = Vec::new();
    collect_binding_paths(&value, &mut paths);
    for relative in paths {
        let source = root.join(&relative);
        let destination = staged_root.join(&relative);
        if destination.exists() {
            continue;
        }
        fs::create_dir_all(destination.parent().ok_or("bound path has no parent")?)?;
        fs::copy(source, destination)?;
    }
    Ok(())
}

fn collect_binding_paths(value: &Value, paths: &mut Vec<String>) {
    match value {
        Value::Object(map) => {
            if map.len() == 2 && map.contains_key("sha256") {
                if let Some(path) = map.get("path").and_then(Value::as_str) {
                    paths.push(path.to_owned());
                }
            }
            for child in map.values() {
                collect_binding_paths(child, paths);
            }
        }
        Value::Array(values) => {
            for child in values {
                collect_binding_paths(child, paths);
            }
        }
        _ => {}
    }
}

fn sealed_program_sums(
    current: &str,
    replacements: &[(&str, String)],
) -> Result<Vec<u8>, Box<dyn std::error::Error>> {
    let replacements = replacements.iter().cloned().collect::<BTreeMap<_, _>>();
    let mut observed = std::collections::BTreeSet::new();
    let mut output = String::new();
    for line in current.lines() {
        let (declared, path) = line
            .split_once("  ")
            .ok_or("program SHA256SUMS row is malformed")?;
        if declared.len() != 64 || !declared.bytes().all(|byte| byte.is_ascii_hexdigit()) {
            return Err("program SHA256SUMS row has an invalid digest".into());
        }
        let digest = replacements
            .get(path)
            .map_or_else(|| declared.to_owned(), Clone::clone);
        if replacements.contains_key(path) {
            observed.insert(path);
        }
        output.push_str(&digest);
        output.push_str("  ");
        output.push_str(path);
        output.push('\n');
    }
    if observed.len() != replacements.len() {
        return Err("program SHA256SUMS is missing a sealed artifact row".into());
    }
    Ok(output.into_bytes())
}

fn commit_staged_writes(
    root: &Path,
    writes: BTreeMap<PathBuf, Vec<u8>>,
) -> Result<(), Box<dyn std::error::Error>> {
    for (index, (path, bytes)) in writes.into_iter().enumerate() {
        let relative = path.strip_prefix(root)?;
        let temp = root
            .join("target/compound-config-seal/commit")
            .join(format!("{index}.tmp"));
        fs::create_dir_all(temp.parent().ok_or("seal temp path has no parent")?)?;
        fs::write(&temp, bytes)?;
        fs::rename(temp, root.join(relative))?;
    }
    Ok(())
}

fn toolchain_verify(root: &Path, all: bool) -> Result<(), Box<dyn std::error::Error>> {
    if !all {
        return Err("toolchain verify requires --all".into());
    }
    let portable = verify_toolchain_profile(root, "portable")?;
    let optimized = verify_toolchain_profile(root, "host-optimized")?;
    println!(
        "{}",
        serde_json::to_string(&json!({
            "command": "toolchain verify --all",
            "verified_manifests": [
                {
                    "profile_id": portable.profile_id,
                    "manifest_jcs_sha256": portable.manifest_payload_jcs_sha256,
                    "installed_tree_sha256": portable.installed_tree_sha256,
                },
                {
                    "profile_id": optimized.profile_id,
                    "manifest_jcs_sha256": optimized.manifest_payload_jcs_sha256,
                    "installed_tree_sha256": optimized.installed_tree_sha256,
                }
            ],
            "pass": true,
        }))?
    );
    Ok(())
}

fn python_runtime_audit(root: &Path) -> Result<(), Box<dyn std::error::Error>> {
    let paths = fs::read_dir(root)?
        .filter_map(Result::ok)
        .filter_map(|entry| {
            let name = entry.file_name().to_string_lossy().into_owned();
            let scoped = entry.file_type().is_ok_and(|kind| kind.is_dir())
                && (name.starts_with("amphora-")
                    || matches!(
                        name.as_str(),
                        "xtask" | "config" | "feedback" | "reports" | "scripts"
                    ));
            scoped.then_some(entry.path())
        })
        .collect::<Vec<_>>();
    let mut scanned = 0_u64;
    let mut findings = Vec::new();
    let interpreter = ["py", "thon"].concat();
    let interpreter3 = format!("{interpreter}3");
    let rust_invocations = [
        format!("command::new(\"{interpreter}"),
        format!("command::new('{interpreter}"),
        format!(".command(\"{interpreter}"),
        format!(".command('{interpreter}"),
        ["sys", ".executable"].concat(),
    ];

    for base in paths {
        let mut queue: VecDeque<PathBuf> = VecDeque::from([base]);
        while let Some(path) = queue.pop_front() {
            if !path.exists() {
                continue;
            }
            for entry in fs::read_dir(&path)? {
                let entry = entry?;
                let next = entry.path();
                if entry.file_type()?.is_dir() {
                    if next
                        .file_name()
                        .and_then(|name| name.to_str())
                        .is_some_and(|name| {
                            !matches!(name, "target" | ".git" | "external-cache" | "tool-cache")
                        })
                    {
                        queue.push_back(next);
                    }
                    continue;
                }
                let extension = next.extension().and_then(|value| value.to_str());
                if extension == Some("py") {
                    findings.push(json!({
                        "path": next.strip_prefix(root)?.display().to_string(),
                        "line": 1,
                        "reason": "SCOPED_PYTHON_PRODUCTION_ENTRYPOINT",
                    }));
                    continue;
                }
                let is_entrypoint = matches!(
                    extension,
                    Some("rs" | "sh" | "toml" | "json" | "yaml" | "yml" | "typ" | "tex")
                ) || next
                    .file_name()
                    .and_then(|value| value.to_str())
                    .is_some_and(|name| matches!(name, "Dockerfile" | "Makefile"));
                if !is_entrypoint {
                    continue;
                }
                scanned += 1;
                let bytes = fs::read_to_string(&next)?;
                for (line_no, line) in bytes.lines().enumerate() {
                    let lowered = line.to_ascii_lowercase();
                    let forbidden = lowered.starts_with("#!") && lowered.contains(&interpreter)
                        || extension == Some("rs")
                            && rust_invocations
                                .iter()
                                .any(|pattern| lowered.contains(pattern))
                        || extension == Some("sh")
                            && lowered
                                .split(|character: char| {
                                    !(character.is_ascii_alphanumeric() || character == '_')
                                })
                                .any(|token| token == interpreter || token == interpreter3);
                    if forbidden {
                        findings.push(json!({
                            "path": next.strip_prefix(root)?.display().to_string(),
                            "line": line_no + 1,
                            "reason": "SCOPED_INTERPRETER_INVOCATION",
                        }));
                    }
                }
            }
        }
    }
    if !findings.is_empty() {
        println!(
            "{}",
            serde_json::to_string_pretty(&json!({
                "command": "python-runtime-audit --compound-paths",
                "scanned_entrypoint_files": scanned,
                "static_findings": findings,
                "runtime_trace_completed": false,
                "pass": false,
            }))?
        );
        return Err("Wave 1 static audit detected a forbidden interpreter entrypoint".into());
    }

    let result = root.join("artifacts/compound-campaigns/epoxy-amine-phase0-v1/result.v2.json");
    let binary = root.join("target/debug/amphora-tui");
    let tracer = command_path("strace");
    if !result.is_file() || !binary.is_file() || tracer.is_none() {
        println!(
            "{}",
            serde_json::to_string_pretty(&json!({
                "command": "python-runtime-audit --compound-paths",
                "scanned_entrypoint_files": scanned,
                "static_findings": [],
                "runtime_trace_completed": false,
                "runtime_blockers": {
                    "campaign_result_v2_present": result.is_file(),
                    "prebuilt_compound_binary_present": binary.is_file(),
                    "execve_tracer_present": tracer.is_some(),
                },
                "pass": false,
            }))?
        );
        return Err("Wave 1 runtime audit requires the completed v2 campaign, prebuilt CLI, and execve tracer".into());
    }

    let trace_staging = root.join("target/compound-python-wave1/execve.trace");
    fs::create_dir_all(
        trace_staging
            .parent()
            .ok_or("runtime trace staging path has no parent")?,
    )?;
    if trace_staging.exists() {
        fs::remove_file(&trace_staging)?;
    }
    let status = Command::new(tracer.expect("tracer presence was checked"))
        .current_dir(root)
        .args(["-f", "-qq", "-e", "trace=execve", "-o"])
        .arg(&trace_staging)
        .arg(&binary)
        .args([
            "compound",
            "campaign",
            "verify",
            "--campaign",
            "epoxy-amine-phase0-v1",
            "--workers",
            "1",
        ])
        .status()?;
    let trace = fs::read(&trace_staging)?;
    let trace_text = String::from_utf8(trace.clone())?;
    let quoted_interpreter = format!("\"{interpreter}");
    let forbidden_execve = trace_text
        .lines()
        .filter(|line| {
            let lowered = line.to_ascii_lowercase();
            let executable_is_interpreter = lowered
                .split_once("execve(\"")
                .and_then(|(_, tail)| tail.split_once('"'))
                .and_then(|(path, _)| Path::new(path).file_name())
                .and_then(|name| name.to_str())
                .is_some_and(|name| name.starts_with(&interpreter));
            executable_is_interpreter || lowered.contains(&quoted_interpreter)
        })
        .map(str::to_owned)
        .collect::<Vec<_>>();
    if !status.success() || !forbidden_execve.is_empty() {
        return Err(
            "Wave 1 traced campaign verification failed or executed a forbidden interpreter".into(),
        );
    }

    let trace_path = root.join("artifacts/compound-milestone/python-wave1-execve.trace");
    persist_audit_artifact(&trace_path, &trace)?;
    let trace_sha256 = sha256(&trace);
    let mut receipt = json!({
        "schema": "amphora.python-wave1-runtime-audit-receipt.v1",
        "campaign_id": "epoxy-amine-phase0-v1",
        "verification_command": "compound campaign verify --campaign epoxy-amine-phase0-v1 --workers 1",
        "scanned_entrypoint_files": scanned,
        "static_findings": [],
        "trace_path": "artifacts/compound-milestone/python-wave1-execve.trace",
        "trace_sha256": trace_sha256,
        "forbidden_execve_count": 0,
        "classification": "LOCKED_INTERNAL",
        "authority_ceiling": "AUDIT_ONLY",
        "pass": true,
        "receipt_jcs_sha256": "",
    });
    let unsigned = jcs_bytes(&receipt)?;
    receipt["receipt_jcs_sha256"] = Value::String(sha256(&unsigned));
    let receipt_bytes = jcs_bytes(&receipt)?;
    persist_audit_artifact(
        &root.join("artifacts/compound-milestone/python-wave1-audit.receipt.v1.json"),
        &receipt_bytes,
    )?;
    println!(
        "{}",
        serde_json::to_string_pretty(&json!({
            "command": "python-runtime-audit --compound-paths",
            "scanned_entrypoint_files": scanned,
            "static_findings": [],
            "runtime_trace_completed": true,
            "trace_sha256": trace_sha256,
            "pass": true,
        }))?
    );
    Ok(())
}

fn command_path(command: &str) -> Option<PathBuf> {
    std::env::var_os("PATH").and_then(|paths| {
        std::env::split_paths(&paths)
            .map(|path| path.join(command))
            .find(|candidate| candidate.is_file())
    })
}

fn persist_audit_artifact(path: &Path, bytes: &[u8]) -> Result<(), Box<dyn std::error::Error>> {
    if path.exists() {
        if fs::read(path)? == bytes {
            return Ok(());
        }
        return Err(format!("immutable audit artifact conflicts: {}", path.display()).into());
    }
    fs::create_dir_all(path.parent().ok_or("audit artifact has no parent")?)?;
    let mut file = fs::OpenOptions::new()
        .create_new(true)
        .write(true)
        .open(path)?;
    file.write_all(bytes)?;
    file.sync_all()?;
    Ok(())
}

fn snapshot_registry(root: &Path) -> Result<(), Box<dyn std::error::Error>> {
    let bytes = fs::read(root.join("module-manifest.json"))?;
    let digest = sha256(&bytes);
    let archive = root
        .join("registry/archive")
        .join(&digest)
        .join("module-manifest.json");
    if archive.exists() {
        if fs::read(&archive)? != bytes {
            return Err("hash-addressed registry archive contains altered bytes".into());
        }
    } else {
        fs::create_dir_all(archive.parent().ok_or("registry archive has no parent")?)?;
        let mut output = fs::OpenOptions::new()
            .create_new(true)
            .write(true)
            .open(&archive)?;
        output.write_all(&bytes)?;
        output.sync_all()?;
    }
    println!("{}  {}", digest, archive.display());
    Ok(())
}

fn reconcile_native_evidence(root: &Path) -> Result<(), Box<dyn std::error::Error>> {
    const INVENTORY_PATH: &str = "config/module-evidence-inventory.json";
    let manifest: Value = serde_json::from_slice(&fs::read(root.join("module-manifest.json"))?)?;
    let profile_paths: BTreeMap<_, _> = manifest["modules"]
        .as_array()
        .ok_or("manifest modules are absent")?
        .iter()
        .map(|row| {
            Ok::<_, Box<dyn std::error::Error>>((
                row["project"]
                    .as_str()
                    .ok_or("manifest module ID missing")?
                    .to_owned(),
                row["capability_profile"]
                    .as_str()
                    .ok_or("manifest profile path missing")?
                    .to_owned(),
            ))
        })
        .collect::<Result<_, _>>()?;
    let mut inventory: Value = serde_json::from_slice(&fs::read(root.join(INVENTORY_PATH))?)?;
    let rows = inventory["modules"]
        .as_array_mut()
        .ok_or("inventory modules are absent")?;
    for row in rows.iter_mut() {
        let module_id = row["module_id"]
            .as_str()
            .ok_or("inventory module ID missing")?
            .to_owned();
        if !profile_paths.contains_key(&module_id) {
            return Err(format!("inventory module is absent from manifest: {module_id}").into());
        }
        let (implementation_path, version_source_path) = native_implementation_paths(&module_id);
        let implementation_hash = sha256(&fs::read(root.join(implementation_path))?);
        let version_source_hash = sha256(&fs::read(root.join(version_source_path))?);
        row["implementation"] = serde_json::json!({
            "path": implementation_path,
            "sha256": implementation_hash,
            "version": "0.1.0-rust",
            "version_source_path": version_source_path,
            "version_source_sha256": version_source_hash,
        });
        let runtime = row["runtime_integration"]
            .as_object_mut()
            .ok_or_else(|| format!("runtime integration is absent for {module_id}"))?;
        runtime.insert("adapter_registered".into(), Value::Bool(true));
        runtime.insert(
            "registry_path".into(),
            Value::String("amphora-engine/src/lib.rs".into()),
        );
        runtime.insert(
            "registry_sha256".into(),
            Value::String(sha256(&fs::read(root.join("amphora-engine/src/lib.rs"))?)),
        );
        row["tests"] = Value::Array(
            native_test_paths(&module_id, implementation_path)
                .into_iter()
                .map(|path| {
                    Ok::<_, Box<dyn std::error::Error>>(serde_json::json!({
                        "path": path,
                        "sha256": sha256(&fs::read(root.join(path))?),
                    }))
                })
                .collect::<Result<_, _>>()?,
        );
        if let Some(fixture) = row
            .get_mut("red_team_fixture")
            .and_then(Value::as_object_mut)
        {
            fixture.insert("path".into(), Value::String(implementation_path.to_owned()));
            fixture.insert(
                "selector".into(),
                Value::String("native_workspace_locked".into()),
            );
        }
        for artifact in row["artifacts"]
            .as_array_mut()
            .ok_or_else(|| format!("artifacts are absent for {module_id}"))?
        {
            if let Some(path) = artifact["path"].as_str() {
                let artifact_path = root.join(path);
                if artifact_path.is_file() {
                    artifact["sha256"] = Value::String(sha256(&fs::read(artifact_path)?));
                }
            }
        }
        if module_id == "amphora-known-answer-benchmarks" {
            let receipt_path = "amphora-known-answer-benchmarks/reference/mvp20/out/control_by_control_receipt.v1.json";
            let artifacts = row["artifacts"]
                .as_array_mut()
                .ok_or("known-answer artifacts are absent")?;
            artifacts.retain(|artifact| artifact["path"] != receipt_path);
            artifacts.push(serde_json::json!({
                "kind": "evaluation_receipt",
                "path": receipt_path,
                "sha256": sha256(&fs::read(root.join(receipt_path))?),
                "rights": {
                    "status": "KNOWN",
                    "evidence_path": receipt_path,
                    "gap": "One historical control remains UNVERIFIED; the arithmetic subset is 6/6 only."
                }
            }));
        }
    }
    let reconciled_rows = rows.clone();
    let mut inventory_bytes = serde_json::to_vec_pretty(&inventory)?;
    inventory_bytes.push(b'\n');
    atomic_write(&root.join(INVENTORY_PATH), &inventory_bytes)?;
    let mut benchmark_lock: Value =
        serde_json::from_slice(&fs::read(root.join("config/benchmark-lock.v1.json"))?)?;
    benchmark_lock["dataset_hashes"][INVENTORY_PATH] = Value::String(sha256(&inventory_bytes));
    let mut benchmark_bytes = serde_json::to_vec_pretty(&benchmark_lock)?;
    benchmark_bytes.push(b'\n');
    atomic_write(
        &root.join("config/benchmark-lock.v1.json"),
        &benchmark_bytes,
    )?;

    for row in &reconciled_rows {
        let module_id = row["module_id"].as_str().expect("validated module ID");
        let profile_path = &profile_paths[module_id];
        let mut profile: Value = serde_json::from_slice(&fs::read(root.join(profile_path))?)?;
        let mut mirrored = row.clone();
        let object = mirrored.as_object_mut().expect("inventory row is object");
        object.remove("module_id");
        object.remove("portfolio_edges");
        object.insert(
            "registry".into(),
            serde_json::json!({
                "module_id": module_id,
                "path": "../../config/module-evidence-inventory.json"
            }),
        );
        profile["evidence_inventory"] = mirrored;
        let mut profile_bytes = serde_json::to_vec_pretty(&profile)?;
        profile_bytes.push(b'\n');
        atomic_write(&root.join(profile_path), &profile_bytes)?;

        let documentation_path = manifest["modules"]
            .as_array()
            .expect("validated manifest")
            .iter()
            .find(|manifest_row| manifest_row["project"] == module_id)
            .and_then(|manifest_row| manifest_row["documentation"].as_str())
            .ok_or_else(|| format!("documentation path is absent for {module_id}"))?;
        let (implementation_path, _) = native_implementation_paths(module_id);
        let implementation_hash = sha256(&fs::read(root.join(implementation_path))?);
        let mission = fs::read_to_string(root.join(documentation_path))?;
        let replacement = format!(
            "The live checked implementation is native Rust at `{implementation_path}` with SHA-256 `{implementation_hash}`. Runtime registration is owned by `amphora-engine/src/lib.rs` and is checked against `module-manifest.json`. Retired Python implementation records have diagnostic provenance only and are not live authority."
        );
        let mut replaced = false;
        let mut lines = Vec::new();
        for line in mission.lines() {
            if line.starts_with("The checked implementation is ")
                || line.starts_with("The live checked implementation is native Rust at ")
            {
                lines.push(replacement.clone());
                replaced = true;
            } else if line.starts_with("Module-focused checked fixture:") {
                let scenario = row
                    .get("red_team_fixture")
                    .and_then(|fixture| fixture.get("scenario"))
                    .and_then(Value::as_str)
                    .unwrap_or("Exercise the module's fail-closed native checks.");
                lines.push(format!(
                    "Module-focused checked fixture: `{implementation_path}` via `rtk cargo test --workspace --locked`. Scenario: {scenario}"
                ));
            } else {
                lines.push(line.to_owned());
            }
        }
        if !replaced {
            return Err(format!("mission implementation record is absent for {module_id}").into());
        }
        let mut updated_mission = lines.join("\n");
        let evidence_heading = "Focused checked test evidence:\n\n";
        let evidence_start = updated_mission
            .find(evidence_heading)
            .ok_or_else(|| format!("mission test evidence heading is absent for {module_id}"))?
            + evidence_heading.len();
        let evidence_end = updated_mission[evidence_start..]
            .find("\n\nOperational state")
            .map(|offset| evidence_start + offset)
            .ok_or_else(|| format!("mission test evidence boundary is absent for {module_id}"))?;
        let test_evidence = native_test_paths(module_id, implementation_path)
            .into_iter()
            .map(|path| {
                Ok::<_, Box<dyn std::error::Error>>(format!(
                    "- `{path}` — SHA-256 `{}`",
                    sha256(&fs::read(root.join(path))?)
                ))
            })
            .collect::<Result<Vec<_>, _>>()?
            .join("\n");
        updated_mission.replace_range(evidence_start..evidence_end, &test_evidence);
        let mut mission_bytes = updated_mission.into_bytes();
        mission_bytes.push(b'\n');
        atomic_write(&root.join(documentation_path), &mission_bytes)?;
    }
    println!(
        "reconciled native implementation, profile, mission, and runtime evidence for 29 modules"
    );
    Ok(())
}

fn native_implementation_paths(module_id: &str) -> (&'static str, &'static str) {
    match module_id {
        "amphora-barrier-corrosion-score" => (
            "amphora-barrier-corrosion-score/src/lib.rs",
            "amphora-barrier-corrosion-score/Cargo.toml",
        ),
        "amphora-cure-potlife-gate" => (
            "amphora-cure-potlife-gate/src/lib.rs",
            "amphora-cure-potlife-gate/Cargo.toml",
        ),
        "amphora-solvency-score" => (
            "amphora-solvency-score/src/lib.rs",
            "amphora-solvency-score/Cargo.toml",
        ),
        "amphora-viscosity-score" => (
            "amphora-viscosity-score/src/lib.rs",
            "amphora-viscosity-score/Cargo.toml",
        ),
        "amphora-molecule-generator"
        | "amphora-molecule-role-ranker"
        | "amphora-molecule-novelty"
        | "amphora-molecule-property"
        | "amphora-molecule-design-gate" => (
            "amphora-molecule-capabilities/src/lib.rs",
            "amphora-molecule-capabilities/Cargo.toml",
        ),
        "amphora-evidence-intake-validator"
        | "amphora-source-ledger"
        | "amphora-known-answer-benchmarks"
        | "amphora-sourceability-ehs"
        | "amphora-cro-protocol-packager"
        | "amphora-ip-fto-guard"
        | "amphora-report-packager"
        | "amphora-redteam-audit" => (
            "amphora-assurance-capabilities/src/lib.rs",
            "amphora-assurance-capabilities/Cargo.toml",
        ),
        "amphora-ingredient-library"
        | "amphora-formulation-arithmetic"
        | "amphora-envelope-gates"
        | "amphora-formulation-universe"
        | "amphora-design-rule-score"
        | "amphora-public-corrosion-benchmark"
        | "amphora-tolerance-robustness"
        | "amphora-process-qc-twin" => (
            "amphora-formulation-capabilities/src/lib.rs",
            "amphora-formulation-capabilities/Cargo.toml",
        ),
        _ => ("amphora-engine/src/lib.rs", "amphora-engine/Cargo.toml"),
    }
}

fn native_test_paths(module_id: &str, implementation_path: &'static str) -> Vec<&'static str> {
    if module_id == "amphora-cure-potlife-gate" {
        vec![
            "amphora-cure-potlife-gate/src/lib.rs",
            "amphora-cure-potlife-gate/src/contract.rs",
            "amphora-cure-potlife-gate/src/evaluation.rs",
            "amphora-cure-potlife-gate/src/physics.rs",
            "amphora-cure-potlife-gate/src/preflight.rs",
            "amphora-cure-potlife-gate/src/protocol.rs",
            "amphora-cure-potlife-gate/src/tests.rs",
        ]
    } else if matches!(
        module_id,
        "amphora-evidence-intake-validator"
            | "amphora-source-ledger"
            | "amphora-redteam-audit"
            | "amphora-report-packager"
            | "amphora-cro-protocol-packager"
    ) {
        vec![
            "amphora-assurance-capabilities/src/lib.rs",
            "amphora-assurance-capabilities/src/diagnostics.rs",
        ]
    } else if matches!(
        module_id,
        "amphora-formulation-arithmetic"
            | "amphora-formulation-universe"
            | "amphora-envelope-gates"
    ) {
        vec![
            "amphora-formulation-capabilities/src/lib.rs",
            "amphora-assurance-capabilities/src/diagnostics.rs",
        ]
    } else if module_id == "amphora-optimizer-orchestrator" {
        vec![
            "amphora-engine/src/lib.rs",
            "amphora-core/src/lib.rs",
            "amphora-assurance-capabilities/src/diagnostics.rs",
        ]
    } else {
        vec![implementation_path]
    }
}

fn rewrite_native_commands(root: &Path) -> Result<(), Box<dyn std::error::Error>> {
    let mut changed = 0_usize;
    let interpreter = ["py", "thon"].concat();
    let interpreter3 = format!("{interpreter}3");
    let test_runner = ["py", "test"].concat();
    let module_command = format!("{interpreter} -m ");
    let module3_command = format!("{interpreter3} -m ");
    let quoted_module_command = format!("`{module_command}");
    let quoted_module3_command = format!("`{module3_command}");
    let quoted_test_command = format!("`{interpreter3} -B -m {test_runner}");
    for path in collect_files(root)? {
        let extension = path.extension().and_then(|value| value.to_str());
        if extension == Some("json") {
            let Ok(bytes) = fs::read(&path) else {
                continue;
            };
            let Ok(mut value) = serde_json::from_slice::<Value>(&bytes) else {
                continue;
            };
            if rewrite_command_fields(&mut value) {
                let mut output = serde_json::to_vec_pretty(&value)?;
                output.push(b'\n');
                atomic_write(&path, &output)?;
                changed += 1;
            }
        } else if extension == Some("md") {
            let text = fs::read_to_string(&path)?;
            let mut touched = false;
            let lines: Vec<_> = text
                .lines()
                .map(|line| {
                    let trimmed = line.trim();
                    if trimmed.starts_with("Focused acceptance command:") {
                        touched = true;
                        "Focused acceptance command: `rtk cargo test --workspace --locked`. The native demo and replay commands in `AMPHORA_RUST.md` are the portfolio acceptance path.".to_owned()
                    } else if trimmed.starts_with(&module_command)
                        || trimmed.starts_with(&module3_command)
                    {
                        touched = true;
                        "rtk cargo run --release -- inspect --candidate candidate.json --headless".to_owned()
                    } else if line.contains(&quoted_module_command)
                        || line.contains(&quoted_module3_command)
                        || line.contains(&quoted_test_command)
                    {
                        touched = true;
                        "Use `rtk cargo test --workspace --locked` for the native replacement.".to_owned()
                    } else {
                        line.to_owned()
                    }
                })
                .collect();
            if touched {
                let mut output = lines.join("\n");
                output.push('\n');
                atomic_write(&path, output.as_bytes())?;
                changed += 1;
            }
        }
    }
    for schema in [
        "schemas/module-evidence-inventory.schema.json",
        "schemas/module-capability-profile.schema.json",
    ] {
        let path = root.join(schema);
        let text = fs::read_to_string(&path)?;
        let legacy_pattern =
            format!("^{interpreter3} -B -m {test_runner} -q -p no:cacheprovider amphora-");
        let updated = text.replace(&legacy_pattern, "^rtk cargo test --workspace --locked$");
        if updated != text {
            atomic_write(&path, updated.as_bytes())?;
            changed += 1;
        }
    }
    println!("rewrote native acceptance commands in {changed} files");
    Ok(())
}

fn rewrite_command_fields(value: &mut Value) -> bool {
    let mut changed = false;
    match value {
        Value::Object(object) => {
            for (key, value) in object {
                if key == "focused_acceptance_command" && value.is_string() {
                    if value.as_str() != Some("rtk cargo test --workspace --locked") {
                        *value = Value::String("rtk cargo test --workspace --locked".into());
                        changed = true;
                    }
                } else {
                    changed |= rewrite_command_fields(value);
                }
            }
        }
        Value::Array(values) => {
            for value in values {
                changed |= rewrite_command_fields(value);
            }
        }
        _ => {}
    }
    changed
}

fn audit(root: &Path) -> Result<(), Box<dyn std::error::Error>> {
    let registry = NativeRegistry::global()?;
    if registry.module_count() != 29 {
        return Err("native registry does not resolve exactly 29 modules".into());
    }
    let manifest: Value = serde_json::from_slice(&fs::read(root.join("module-manifest.json"))?)?;
    let modules = manifest["modules"]
        .as_array()
        .ok_or("manifest modules are absent")?;
    if modules.len() != 29
        || modules
            .iter()
            .any(|module| module["ranking_eligible"] != Value::Bool(false))
    {
        return Err("pre-Phase-0 manifest is not fully ranking-quarantined".into());
    }
    for module in modules {
        let module_id = module["project"].as_str().ok_or("module ID missing")?;
        let profile_path = module["capability_profile"]
            .as_str()
            .ok_or("capability profile missing")?;
        let profile: Value = serde_json::from_slice(&fs::read(root.join(profile_path))?)?;
        if profile["module_id"] != Value::String(module_id.into())
            || profile["ceilings"]["ranking_eligible"] != Value::Bool(false)
            || profile["ceilings"]["authority_tier"] != module["authority_ceiling"]
            || profile["ceilings"]["solver_use"] != module["solver_use_ceiling"]
            || profile["ceilings"]["model_readiness"] != module["model_readiness_ceiling"]
        {
            return Err(format!("manifest/profile policy mismatch for {module_id}").into());
        }
        let descriptor = registry.resolve(module_id)?.descriptor();
        if descriptor.project != module_id
            || descriptor.authority_ceiling != module["authority_ceiling"]
            || descriptor.solver_use_ceiling != module["solver_use_ceiling"]
            || descriptor.model_readiness_ceiling != module["model_readiness_ceiling"]
            || descriptor.ranking_eligible != module["ranking_eligible"].as_bool().unwrap_or(true)
            || serde_json::to_value(&descriptor.candidate_types)? != module["candidate_types"]
        {
            return Err(format!("manifest/runtime registration mismatch for {module_id}").into());
        }
        let documentation_path = module["documentation"]
            .as_str()
            .ok_or("module documentation path missing")?;
        let mission = fs::read_to_string(root.join(documentation_path))?;
        if !mission.contains("The live checked implementation is native Rust at `")
            || mission.contains("The checked implementation is version ")
        {
            return Err(format!("mission implementation record is stale for {module_id}").into());
        }
        audit_bound_module_metadata(root, module_id, profile_path)?;
    }
    audit_phase0_module_layout(root, &manifest)?;
    audit_known_answer_receipt(root)?;
    audit_coatings_program_locks(root)?;
    let files = collect_files(root)?;
    let forbidden: Vec<_> = files
        .iter()
        .filter(|path| is_retired_mvp20_source(root, path))
        .collect();
    if !forbidden.is_empty() {
        return Err(format!(
            "Python retirement incomplete: {} files remain",
            forbidden.len()
        )
        .into());
    }
    let rust_sources: Vec<_> = files
        .iter()
        .filter(|path| path.extension().and_then(|extension| extension.to_str()) == Some("rs"))
        .collect();
    let interpreter = ["py", "thon"].concat();
    let interpreter3 = format!("{interpreter}3");
    let interpreter_launch = format!("Command::new({interpreter:?})");
    let interpreter3_launch = format!("Command::new({interpreter3:?})");
    let retired_worker = ["amphora_mvp20", ".worker"].concat();
    for path in rust_sources {
        let text = fs::read_to_string(path)?;
        if text.contains(&interpreter_launch)
            || text.contains(&interpreter3_launch)
            || text.contains(&retired_worker)
        {
            return Err(format!("runtime Python launch remains in {}", path.display()).into());
        }
    }
    println!("audit passed: 29 native modules; 29 confined Phase-0 homes; zero ranking objectives; zero retired MVP20 Python runtime/files");
    Ok(())
}

#[cfg(test)]
fn audit_cure_pot_life_metadata(root: &Path) -> Result<(), Box<dyn std::error::Error>> {
    audit_bound_module_metadata(
        root,
        "amphora-cure-potlife-gate",
        "amphora-cure-potlife-gate/docs/capability-profile.json",
    )
}

fn audit_bound_module_metadata(
    root: &Path,
    module_id: &str,
    profile_path: &str,
) -> Result<(), Box<dyn std::error::Error>> {
    const INVENTORY_PATH: &str = "config/module-evidence-inventory.json";

    let inventory: Value = serde_json::from_slice(&fs::read(root.join(INVENTORY_PATH))?)?;
    let inventory_row = inventory["modules"]
        .as_array()
        .and_then(|rows| {
            rows.iter()
                .find(|row| row["module_id"] == Value::String(module_id.into()))
        })
        .ok_or_else(|| format!("{module_id} inventory row is absent"))?;
    let profile: Value = serde_json::from_slice(&fs::read(root.join(profile_path))?)?;
    if profile["module_id"] != Value::String(module_id.into())
        || profile["evidence_inventory"]["registry"]["module_id"] != Value::String(module_id.into())
        || profile["evidence_inventory"]["registry"]["path"]
            != Value::String("../../config/module-evidence-inventory.json".into())
    {
        return Err(format!("{module_id} capability profile registry binding is stale").into());
    }

    let mut expected = inventory_row.clone();
    let expected_object = expected
        .as_object_mut()
        .ok_or_else(|| format!("{module_id} inventory row is not an object"))?;
    expected_object.remove("module_id");
    expected_object.remove("portfolio_edges");
    let mut observed = profile["evidence_inventory"].clone();
    observed
        .as_object_mut()
        .ok_or_else(|| format!("{module_id} profile evidence inventory is not an object"))?
        .remove("registry");
    if observed != expected {
        return Err(
            format!("{module_id} capability profile diverges from global inventory row").into(),
        );
    }

    // Source, test, and shared-runtime hashes in the legacy inventory are
    // descriptive only. Promotion authority is bound to immutable module-local
    // parents, while implementation integrity is checked by the locked build.
    if let Some(fixture) = inventory_row
        .get("red_team_fixture")
        .and_then(Value::as_object)
    {
        let path = fixture
            .get("path")
            .and_then(Value::as_str)
            .ok_or_else(|| format!("{module_id} red-team fixture path is absent"))?;
        if path.ends_with(".py")
            || !root.join(path).is_file()
            || fixture.get("selector").and_then(Value::as_str) != Some("native_workspace_locked")
        {
            return Err(format!("{module_id} red-team fixture is not native").into());
        }
    }
    for row in inventory_row["artifacts"]
        .as_array()
        .ok_or_else(|| format!("{module_id} artifact metadata is absent"))?
    {
        audit_declared_file(root, row.get("path"), row.get("sha256"), "artifact")?;
        let rights = row
            .get("rights")
            .and_then(Value::as_object)
            .ok_or_else(|| format!("{module_id} artifact rights binding is absent"))?;
        if rights.get("status").and_then(Value::as_str) == Some("KNOWN") {
            let evidence_path = rights
                .get("evidence_path")
                .and_then(Value::as_str)
                .ok_or_else(|| format!("{module_id} known rights evidence path is absent"))?;
            if !root.join(evidence_path).is_file() {
                return Err(
                    format!("{module_id} rights evidence path is stale: {evidence_path}").into(),
                );
            }
        }
    }
    let runtime = inventory_row["runtime_integration"]
        .as_object()
        .ok_or_else(|| format!("{module_id} runtime integration metadata is absent"))?;
    if runtime.get("adapter_registered").and_then(Value::as_bool) != Some(true) {
        return Err(format!("{module_id} is not declared registered in native runtime").into());
    }
    Ok(())
}

fn audit_phase0_module_layout(
    root: &Path,
    manifest: &Value,
) -> Result<(), Box<dyn std::error::Error>> {
    let trust: Value =
        serde_json::from_slice(&fs::read(root.join("config/phase0-trust-store.v1.json"))?)?;
    let trust_keys = trust["keys"]
        .as_array()
        .ok_or("Phase-0 trust store key list is absent")?;
    if trust["schema"] != "amphora.phase0-trust-store.v1"
        || trust_keys.iter().any(|key| {
            key["phase0_authorized"] == true
                && (key["development"] == true
                    || !matches!(
                        key["role"].as_str(),
                        Some("PHASE0_EVALUATOR" | "PHASE0_INTERNAL_REVIEWER")
                    ))
        })
    {
        return Err("Phase-0 trust store authorizes an invalid or development key".into());
    }
    let rights_trust: Value = serde_json::from_slice(&fs::read(
        root.join("config/rights-review-trust-store.v1.json"),
    )?)?;
    let rights_keys = rights_trust["keys"]
        .as_array()
        .ok_or("rights-review trust store key list is absent")?;
    let rights_status = rights_trust["authorization_status"].as_str();
    let rights_store_valid = rights_trust["schema"] == "amphora.rights-review-trust-store.v1"
        && match rights_status {
            Some("PENDING_EXTERNAL_RIGHTS_REVIEWER") => rights_keys.is_empty(),
            Some("AUTHORIZED_RIGHTS_REVIEW_IDENTITIES") => {
                !rights_keys.is_empty()
                    && rights_keys.iter().all(|key| {
                        key["algorithm"] == "Ed25519"
                            && key["role"] == "RIGHTS_REVIEWER"
                            && key["rights_review_authorized"] == true
                            && key["development"] == false
                    })
                    && rights_keys.iter().any(|key| key["revoked"] == false)
            }
            _ => false,
        };
    if !rights_store_valid {
        return Err("rights-review trust store is malformed or development-authorized".into());
    }

    let report: Value = serde_json::from_slice(&fs::read(
        root.join("config/program/phase0-decision-report.v2.json"),
    )?)?;
    let report_rows = report["modules"]
        .as_array()
        .ok_or("Phase-0 V2 decision report has no modules")?;
    let registry_rows = manifest["modules"]
        .as_array()
        .ok_or("module registry has no modules")?;
    let report_ids: std::collections::BTreeSet<_> = report_rows
        .iter()
        .filter_map(|row| row["module_id"].as_str())
        .collect();
    let registry_ids: std::collections::BTreeSet<_> = registry_rows
        .iter()
        .filter_map(|row| row["project"].as_str())
        .collect();
    if report["schema"] != "amphora.module-evidence-decision-report.v2"
        || report["module_count"] != 29
        || report_rows.len() != 29
        || report_ids.len() != 29
        || report_ids != registry_ids
    {
        return Err("Phase-0 V2 report does not cover 29 unique registry modules".into());
    }

    let required = [
        "evidence/phase0/raw/SHA256SUMS",
        "evidence/phase0/dataset/dataset-manifest.v1.json",
        "evidence/phase0/split/split-manifest.v1.json",
        "evidence/phase0/benchmark/benchmark-lock.v1.json",
        "evidence/phase0/promotion/policy.v1.json",
        "evidence/phase0/bundle.v1.json",
        "ip/claim-contract.v1.json",
        "ip/technical-dossier.v1.json",
        "ip/prior-art.v1.json",
        "ip/disclosure-log.v1.json",
        "movement/ledger.v1.json",
    ];
    let mut phase0_count = 0_u64;
    let mut deterministic_count = 0_u64;
    for registry_row in registry_rows {
        let module_id = registry_row["project"]
            .as_str()
            .ok_or("registered module ID is absent")?;
        let module_dir = root.join(module_id);
        let canonical_module = module_dir.canonicalize()?;
        for relative in required {
            let path = module_dir.join(relative);
            let canonical = path.canonicalize().map_err(|error| {
                format!("{module_id} required Phase-0 artifact is absent: {relative}: {error}")
            })?;
            if !canonical.starts_with(&canonical_module) || !canonical.is_file() {
                return Err(format!(
                    "{module_id} authoritative artifact escapes its module home: {relative}"
                )
                .into());
            }
        }
        if !module_dir.join("evidence/phase0/raw/objects").is_dir()
            || !module_dir.join("movement/events").is_dir()
        {
            return Err(format!("{module_id} object or movement directory is absent").into());
        }

        let bundle: Value = serde_json::from_slice(&fs::read(
            module_dir.join("evidence/phase0/bundle.v1.json"),
        )?)?;
        let contract: Value =
            serde_json::from_slice(&fs::read(module_dir.join("ip/claim-contract.v1.json"))?)?;
        if bundle["schema"] != "amphora.module-phase0-bundle.v1"
            || bundle["module_id"] != module_id
            || contract["schema"] != "amphora.module-claim-contract.v1"
            || contract["module_id"] != module_id
            || contract["decision_use_ceiling"] != "AUDIT_ONLY"
            || contract["abstain_outside_applicability"] != true
            || bundle["claim_locks"]["no_ranking_authority"] != true
            || bundle["claim_locks"]["no_release_authority"] != true
            || bundle["claim_locks"]["no_product_performance_authority"] != true
            || bundle["claim_locks"] != contract["claim_locks"]
        {
            return Err(format!(
                "{module_id} Phase-0 identity, abstention, or authority locks are invalid"
            )
            .into());
        }
        let parents = bundle["parents"]
            .as_object()
            .ok_or_else(|| format!("{module_id} bundle parent map is absent"))?;
        if parents.is_empty() {
            return Err(format!("{module_id} bundle parent map is empty").into());
        }
        let source_locks = parents
            .keys()
            .filter(|path| {
                matches!(
                    path.as_str(),
                    "evidence/phase0/sources/source-lock.v1.json"
                        | "evidence/phase0/sources/source-lock.v2.json"
                )
            })
            .collect::<Vec<_>>();
        if source_locks.len() != 1 {
            return Err(
                format!("{module_id} bundle must bind exactly one supported source lock").into(),
            );
        }
        for (relative, declared) in parents {
            let relative_path = Path::new(relative);
            if relative_path.is_absolute()
                || relative_path
                    .components()
                    .any(|component| !matches!(component, std::path::Component::Normal(_)))
            {
                return Err(
                    format!("{module_id} bundle contains an unsafe parent: {relative}").into(),
                );
            }
            let path = module_dir.join(relative_path);
            let canonical = path.canonicalize()?;
            let expected = declared
                .as_str()
                .ok_or_else(|| format!("{module_id} parent digest is invalid: {relative}"))?;
            if !canonical.starts_with(&canonical_module)
                || !canonical.is_file()
                || sha256(&fs::read(&canonical)?) != expected
            {
                return Err(format!(
                    "{module_id} bundle parent is stale or unconfined: {relative}"
                )
                .into());
            }
        }

        let report_row = report_rows
            .iter()
            .find(|row| row["module_id"] == module_id)
            .ok_or_else(|| format!("{module_id} is absent from the V2 report"))?;
        let events = fs::read_dir(module_dir.join("movement/events"))?
            .filter_map(Result::ok)
            .filter(|entry| {
                entry.path().extension().and_then(|value| value.to_str()) == Some("json")
            })
            .collect::<Vec<_>>();
        if events.len() > 1 {
            return Err(format!("{module_id} has non-atomic multiple movement events").into());
        }
        let derived_phase = if events.is_empty() {
            "PRE_PHASE_0"
        } else {
            "PHASE_0"
        };
        if report_row["phase"] != derived_phase {
            return Err(
                format!("{module_id} V2 status is not derived from module movement").into(),
            );
        }
        if derived_phase == "PHASE_0" {
            phase0_count += 1;
            if !module_dir
                .join("evidence/phase0/receipts/evaluation.v1.dsse.json")
                .is_file()
                || !module_dir
                    .join("evidence/phase0/receipts/independent-review.v1.dsse.json")
                    .is_file()
            {
                return Err(format!("{module_id} movement lacks both required signatures").into());
            }
        }
        if report_row["target_status"] == "NOT_APPLICABLE" {
            deterministic_count += 1;
        }
    }
    if phase0_count != report["phase0_count"].as_u64().unwrap_or(u64::MAX)
        || deterministic_count != 13
    {
        return Err("Phase-0 V2 counts or deterministic cohort are invalid".into());
    }
    Ok(())
}

fn audit_known_answer_receipt(root: &Path) -> Result<(), Box<dyn std::error::Error>> {
    let path = root.join(
        "amphora-known-answer-benchmarks/reference/mvp20/out/control_by_control_receipt.v1.json",
    );
    let receipt: Value = serde_json::from_slice(&fs::read(path)?)?;
    let controls = receipt["controls"]
        .as_array()
        .ok_or("known-answer receipt controls are absent")?;
    let ids: std::collections::BTreeSet<_> = controls
        .iter()
        .filter_map(|row| row["control_id"].as_str())
        .collect();
    let verified = controls
        .iter()
        .filter(|row| row["status"] == "VERIFIED_PASS")
        .count();
    let unverified = controls
        .iter()
        .filter(|row| row["status"] == "UNVERIFIED")
        .count();
    if receipt["schema"] != "amphora.known-answer-control-receipt.v1"
        || controls.len() != 14
        || ids.len() != 14
        || verified != 13
        || unverified != 1
        || receipt["aggregate_status"] != "INCOMPLETE"
        || controls.iter().any(|row| {
            row.get("expected").is_none()
                || row.get("actual").is_none()
                || row.get("tolerance").is_none()
                || row["source_artifact_sha256"]
                    .as_str()
                    .is_none_or(|hash| hash.len() != 64)
        })
    {
        return Err("known-answer control-by-control reconciliation is invalid".into());
    }
    Ok(())
}

fn audit_coatings_program_locks(root: &Path) -> Result<(), Box<dyn std::error::Error>> {
    let preregistration: Value = serde_json::from_slice(&fs::read(
        root.join("config/program/coatings-90-day-preregistration.v1.json"),
    )?)?;
    if preregistration["status"] != "PREREGISTERED_NOT_EXECUTED"
        || preregistration["fixed_estimator"]["l2_penalty"] != 1.0
        || preregistration["fixed_estimator"]["seed"] != 20_260_717
        || preregistration["sites"]["blinded_verifier_count"] != 2
    {
        return Err("coatings preregistration lock is invalid".into());
    }
    let redteam: Value = serde_json::from_slice(&fs::read(
        root.join("config/program/coatings-redteam-lock.v1.json"),
    )?)?;
    let families = redteam["families"]
        .as_array()
        .ok_or("red-team families are absent")?;
    let internal = redteam["internal_mutation_ids"]
        .as_array()
        .ok_or("red-team internal mutations are absent")?;
    let controls = redteam["valid_control_ids"]
        .as_array()
        .ok_or("red-team controls are absent")?;
    let family_ids: std::collections::BTreeSet<_> =
        families.iter().filter_map(Value::as_str).collect();
    let mutation_ids: std::collections::BTreeSet<_> =
        internal.iter().filter_map(Value::as_str).collect();
    if redteam["status"] != "LOCKED_AWAITING_INDEPENDENT_SEALED_MUTATIONS"
        || families.len() != 16
        || family_ids.len() != 16
        || internal.len() != 64
        || mutation_ids.len() != 64
        || controls.len() != 32
        || redteam["planned_attack_count"] != 96
    {
        return Err("coatings red-team corpus lock is invalid".into());
    }
    audit_phase0_closure_program(root)?;
    let required_paths: std::collections::BTreeSet<_> = [
        "config/program/compound-host-optimized.v1.json",
        "config/program/coatings-90-day-preregistration.v1.json",
        "config/program/epoxy-amine-compound-campaign.v2.json",
        "config/program/epoxy-amine-method-registry.v1.json",
        "config/program/coatings-redteam-lock.v1.json",
        "config/program/corrosion-sources.v2.json",
        "config/program/design-rule-sources.v1.json",
        "config/program/design-rule-split.v1.json",
        "config/program/molecule-property-sources.v1.json",
        "config/program/molecule-property-split.v1.json",
        "config/program/molecule-role-sources.v1.json",
        "config/program/molecule-role-split.v1.json",
        "config/program/phase0-closure-phase1-decision.v1.json",
        "config/program/phase0-closure-phase1-work-orders.v1.json",
        "config/benchmark-locks/amphora-molecule-property.v1.json",
        "config/benchmark-locks/amphora-molecule-role-ranker.v1.json",
        "config/benchmark-locks/amphora-cure-potlife-gate.v1.json",
        "config/benchmark-locks/amphora-design-rule-score.v1.json",
        "config/benchmark-locks/amphora-viscosity-score.v1.json",
        "config/benchmark-locks/amphora-solvency-score.v1.json",
        "config/benchmark-locks/amphora-barrier-corrosion-score.v1.json",
        "config/benchmark-locks/amphora-public-corrosion-benchmark.v1.json",
        "amphora-design-rule-score/reference/purformance/zenodo-13742098/Experiment.zip",
        "amphora-design-rule-score/reference/purformance/zenodo-13742098/Evaluation.zip",
        "amphora-design-rule-score/reference/purformance/zenodo-13742098/Readme.txt",
        "amphora-design-rule-score/reference/purformance/zenodo-13742098/Experiment.acquisition.v1.json",
        "amphora-design-rule-score/reference/purformance/zenodo-13742098/Evaluation.acquisition.v1.json",
        "amphora-design-rule-score/reference/purformance/zenodo-13742098/Readme.acquisition.v1.json",
        "amphora-design-rule-score/reference/purformance/zenodo-13742098/Experiment.LICENSE.txt",
        "amphora-molecule-property/reference/chebi/rel252/chebi_3_stars.sdf.gz",
        "amphora-molecule-property/reference/chebi/rel252/chebi_3_stars.acquisition.v1.json",
        "amphora-molecule-property/reference/chebi/rel252/LICENSE.txt",
        "amphora-molecule-novelty/reference/novelty-corpus.v1.json",
        "tools/build-rdkit-2026.03.2.sh",
    ]
    .into_iter()
    .collect();
    let manifest = fs::read_to_string(root.join("config/program/SHA256SUMS"))?;
    let mut observed_paths = std::collections::BTreeSet::new();
    for line in manifest.lines() {
        let (declared_hash, path) = line
            .split_once("  ")
            .ok_or("program SHA256SUMS row is malformed")?;
        if declared_hash.len() != 64
            || !declared_hash.bytes().all(|byte| byte.is_ascii_hexdigit())
            || !required_paths.contains(path)
            || !observed_paths.insert(path)
            || sha256(&fs::read(root.join(path))?) != declared_hash
        {
            return Err("program SHA256SUMS is invalid".into());
        }
    }
    if observed_paths != required_paths {
        return Err("program SHA256SUMS is incomplete".into());
    }
    Ok(())
}

fn audit_phase0_closure_program(root: &Path) -> Result<(), Box<dyn std::error::Error>> {
    let registry: Value = serde_json::from_slice(&fs::read(root.join("module-manifest.json"))?)?;
    let registry_ids: std::collections::BTreeSet<_> = registry["modules"]
        .as_array()
        .ok_or("module registry has no modules")?
        .iter()
        .filter_map(|row| row["project"].as_str())
        .collect();
    let decision: Value = serde_json::from_slice(&fs::read(
        root.join("config/program/phase0-closure-phase1-decision.v1.json"),
    )?)?;
    let decisions = decision["modules"]
        .as_array()
        .ok_or("phase-0 decision report has no modules")?;
    let decision_ids: std::collections::BTreeSet<_> = decisions
        .iter()
        .filter_map(|row| row["module_id"].as_str())
        .collect();
    let phase1_attempts = decisions
        .iter()
        .filter(|row| row["track"] == "PHASE_1_ATTEMPT")
        .count();
    if decision["status"] != "DECISION_COMPLETE_EXECUTION_INCOMPLETE"
        || decision["module_count"] != 29
        || decisions.len() != 29
        || decision_ids.len() != 29
        || decision_ids != registry_ids
        || phase1_attempts != 7
        || decisions.iter().any(|row| {
            row["evidence_status"] != "UNVALIDATED"
                || row["target_status"].as_str().is_none_or(|status| {
                    ![
                        "INDEPENDENTLY_VALIDATED",
                        "LOCKED_INTERNAL",
                        "NOT_APPLICABLE",
                        "UNVALIDATED",
                    ]
                    .contains(&status)
                })
                || row["work_order"].as_str().is_none()
        })
    {
        return Err("phase-0 decision report coverage or status is invalid".into());
    }

    let work_orders: Value = serde_json::from_slice(&fs::read(
        root.join("config/program/phase0-closure-phase1-work-orders.v1.json"),
    )?)?;
    let orders = work_orders["work_orders"]
        .as_array()
        .ok_or("external work-order program has no orders")?;
    let order_ids: std::collections::BTreeSet<_> = orders
        .iter()
        .filter_map(|row| row["work_order_id"].as_str())
        .collect();
    if work_orders["status"] != "ISSUED_AWAITING_COUNTERSIGNATURE_AND_EXECUTION"
        || orders.len() != 8
        || order_ids.len() != 8
        || decisions.iter().any(|row| {
            row["work_order"]
                .as_str()
                .is_none_or(|id| !order_ids.contains(id))
        })
    {
        return Err("external work orders are incomplete or unreferenced".into());
    }

    let corrosion_v2: Value = serde_json::from_slice(&fs::read(
        root.join("config/program/corrosion-sources.v2.json"),
    )?)?;
    let corrosion_ids: std::collections::BTreeSet<_> = corrosion_v2["sources"]
        .as_array()
        .ok_or("corrosion V2 census has no sources")?
        .iter()
        .filter_map(|row| row["study_id"].as_str())
        .collect();
    let required_corrosion_ids: std::collections::BTreeSet<_> = [
        "USBR_ST_19168",
        "USBR_ST_21019",
        "USBR_ST_22014",
        "USBR_ST_23016",
        "USBR_ST_22024",
        "USBR_ST_22037",
    ]
    .into_iter()
    .collect();
    if corrosion_v2["schema"] != "amphora.public-corrosion-source-census.v2"
        || corrosion_ids != required_corrosion_ids
        || corrosion_v2["v2_fail_closed_gates"]["minimum_eligible_systems"] != 30
        || corrosion_v2["v2_fail_closed_gates"]["minimum_eligible_studies"] != 3
        || corrosion_v2["v2_fail_closed_gates"]["minimum_untouched_external_systems"] != 10
    {
        return Err("public-corrosion V2 census or fail-closed gates are invalid".into());
    }

    let molecule_property_sources_path = "config/program/molecule-property-sources.v1.json";
    let molecule_property_sources: Value =
        serde_json::from_slice(&fs::read(root.join(molecule_property_sources_path))?)?;
    let chebi = molecule_property_sources["sources"]
        .as_array()
        .and_then(|sources| {
            sources
                .iter()
                .find(|source| source["source_id"] == "chebi_fixed_release_truth_set")
        })
        .ok_or("molecule-property source census has no frozen ChEBI source")?;
    let chebi_payload = "amphora-molecule-property/reference/chebi/rel252/chebi_3_stars.sdf.gz";
    let chebi_license = "amphora-molecule-property/reference/chebi/rel252/LICENSE.txt";
    let chebi_acquisition =
        "amphora-molecule-property/reference/chebi/rel252/chebi_3_stars.acquisition.v1.json";
    let payload_hash = "8f17627476c66e899dabe3cd7ae1cbb94f7ee6c67f2ee91f077a77a19c940ad7";
    let license_hash = "fe7b4ce83b8381cc5b216bbb4af73c570688d1b819c73bbaed8ca401f4677cd6";
    let source_census_hash = sha256(&fs::read(root.join(molecule_property_sources_path))?);
    let acquisition: Value = serde_json::from_slice(&fs::read(root.join(chebi_acquisition))?)?;
    if chebi["release_id"] != "ChEBI-252"
        || chebi["eligible_for_derivatives"] != false
        || chebi["fetch"]["expected_sha256"] != payload_hash
        || chebi["fetch"]["license_sha256"] != license_hash
        || chebi["selection_lock"]["minimum_eligible_records"] != 300
        || chebi["selection_lock"]["missing_values_imputed"] != false
        || chebi["selection_lock"]["identity_rule"] != "exact full InChIKey"
        || sha256(&fs::read(root.join(chebi_payload))?) != payload_hash
        || sha256(&fs::read(root.join(chebi_license))?) != license_hash
        || acquisition["source_census_sha256"] != source_census_hash
        || acquisition["payload_sha256"] != payload_hash
        || acquisition["license_sha256"] != license_hash
    {
        return Err("molecule-property ChEBI acquisition or selection lock is invalid".into());
    }

    let design_sources: Value = serde_json::from_slice(&fs::read(
        root.join("config/program/design-rule-sources.v1.json"),
    )?)?;
    for source in design_sources["sources"]
        .as_array()
        .ok_or("design-rule source census has no sources")?
    {
        let path = source["local_manifest"]
            .as_str()
            .ok_or("design-rule source path is absent")?;
        let expected = source["local_manifest_sha256"]
            .as_str()
            .ok_or("design-rule source hash is absent")?;
        if sha256(&fs::read(root.join(path))?) != expected {
            return Err("PURformance source bytes do not match their census".into());
        }
    }
    let design_split: Value = serde_json::from_slice(&fs::read(
        root.join("config/program/design-rule-split.v1.json"),
    )?)?;
    if design_split["assignments"]
        .as_array()
        .is_none_or(|rows| rows.len() != 6)
        || design_split["assignments"]
            .as_array()
            .into_iter()
            .flatten()
            .filter(|row| row["split"] == "SEALED_RANDOM_TEST")
            .count()
            != 1
        || design_split["fixed_estimator"]["family"] != "STANDARDIZED_RIDGE"
        || design_split["authority"]["evidence_status_ceiling"] != "LOCKED_INTERNAL"
    {
        return Err("PURformance chronology split or authority lock is invalid".into());
    }
    Ok(())
}

fn audit_declared_file(
    root: &Path,
    path: Option<&Value>,
    declared_hash: Option<&Value>,
    kind: &str,
) -> Result<(), Box<dyn std::error::Error>> {
    let path = path
        .and_then(Value::as_str)
        .ok_or_else(|| format!("cure/pot-life {kind} path is absent"))?;
    let declared_hash = declared_hash
        .and_then(Value::as_str)
        .ok_or_else(|| format!("cure/pot-life {kind} SHA-256 is absent"))?;
    let bytes = fs::read(root.join(path))
        .map_err(|error| format!("cure/pot-life {kind} path is stale: {path}: {error}"))?;
    let observed_hash = sha256(&bytes);
    if observed_hash != declared_hash {
        return Err(format!(
            "cure/pot-life {kind} SHA-256 mismatch for {path}: declared {declared_hash}, observed {observed_hash}"
        )
        .into());
    }
    Ok(())
}

fn retire_python(root: &Path, apply: bool) -> Result<(), Box<dyn std::error::Error>> {
    let files = collect_files(root)?;
    let mut sources: Vec<_> = files
        .into_iter()
        .filter(|path| is_retired_mvp20_source(root, path))
        .collect();
    sources.sort();
    let rows: Vec<_> = sources
        .iter()
        .map(|path| {
            let relative = path.strip_prefix(root).expect("collected beneath root");
            let bytes = fs::read(path)?;
            let (disposition, replacement) = replacement(relative);
            Ok::<_, io::Error>(RetirementRow {
                source_path: relative.to_string_lossy().into_owned(),
                source_sha256: sha256(&bytes),
                disposition,
                rust_replacement: replacement,
                verification: "cargo test --workspace --locked; cargo run -p xtask -- audit",
            })
        })
        .collect::<Result<_, _>>()?;
    let migration_dir = root.join("migration");
    fs::create_dir_all(&migration_dir)?;
    let report_path = migration_dir.join("python-retirement-crosswalk.jsonl");
    let mut report = Vec::new();
    for row in &rows {
        serde_json::to_writer(&mut report, row)?;
        report.push(b'\n');
    }
    atomic_write(&report_path, &report)?;
    if apply {
        for path in &sources {
            if path.is_file() {
                fs::remove_file(path)?;
            }
        }
        remove_python_cache_dirs(root)?;
    }
    println!(
        "retirement crosswalk: {} files; apply={apply}; {}",
        rows.len(),
        report_path.display()
    );
    Ok(())
}

fn is_retired_source(path: &Path) -> bool {
    let package_manifest = ["py", "project.toml"].concat();
    let test_configuration = ["py", "test.ini"].concat();
    path.extension().and_then(|extension| extension.to_str()) == Some("py")
        || path.extension().and_then(|extension| extension.to_str()) == Some("pyc")
        || path
            .file_name()
            .and_then(|name| name.to_str())
            .is_some_and(|name| name == package_manifest || name == test_configuration)
}

fn is_retired_mvp20_source(root: &Path, path: &Path) -> bool {
    let relative = path.strip_prefix(root).unwrap_or(path);
    let in_module_home = relative
        .components()
        .next()
        .and_then(|component| component.as_os_str().to_str())
        .is_some_and(|component| component.starts_with("amphora-"));
    if in_module_home {
        return is_retired_source(path);
    }
    let unrelated_environment = relative.components().any(|component| {
        component.as_os_str().to_str().is_some_and(|name| {
            matches!(
                name,
                ".venv" | "__pycache__" | ".pytest_cache" | ".ruff_cache" | ".mypy_cache"
            ) || name.starts_with(".venv-")
        })
    });
    let independent_crystal_program = unrelated_environment
        || relative.starts_with("build/lib/nomad_crystal360")
        || relative.starts_with("build/lib/nomad_feature_hunt")
        || relative.starts_with("nomad_crystal360")
        || relative.starts_with("nomad_feature_hunt")
        || relative.starts_with("ops/nomad-feature-hunt")
        || relative.starts_with("ops/nomad-feature-hunt-v2")
        || relative.starts_with("tests/crystal360")
        || matches!(
            relative.to_str(),
            Some(
                "pyproject.toml"
                    | "build_nomad_crystal360.py"
                    | "benchmark_nomad_crystal360.py"
                    | "build_nomad_crystal_atlas.py"
                    | "atlas_model_worker.py"
                    | "atlas_bakeoff_worker.py"
                    | "run_atlas_final.py"
                    | "run_atlas_hyperion_bakeoff.py"
                    | "run_atlas_screen.py"
                    | "run_nomad_crystal_atlas.py"
            )
        );
    !independent_crystal_program && is_retired_source(path)
}

fn replacement(path: &Path) -> (&'static str, &'static str) {
    let text = path.to_string_lossy();
    if text.contains("__pycache__")
        || path.extension().and_then(|value| value.to_str()) == Some("pyc")
    {
        ("RETIRED_BUILD_ARTIFACT", "not applicable")
    } else if text.starts_with("tools/") || text == "build_split.py" {
        ("REPLACED", "xtask")
    } else if text.starts_with("tests/") || text.ends_with("/tests/test_score.py") {
        ("REPLACED", "Rust workspace unit and integration tests")
    } else if text.starts_with("science/metrics") || text.starts_with("science/benchmark") {
        (
            "REPLACED",
            "amphora-core deterministic validation primitives",
        )
    } else if text.contains("molecule") {
        ("REPLACED_OR_QUARANTINED", "amphora-molecule-capabilities")
    } else if text.contains("formulation")
        || text.contains("viscosity")
        || text.contains("corrosion")
        || text.contains("solvency")
        || text.contains("cure")
        || text.contains("tolerance")
        || text.contains("process_qc")
    {
        (
            "REPLACED_OR_QUARANTINED",
            "amphora-formulation-capabilities",
        )
    } else if text.contains("reference/mvp20") {
        ("FORMALLY_RETIRED_ORACLE", "hash retained in this crosswalk")
    } else {
        (
            "REPLACED",
            "amphora-core, amphora-engine, or assurance capabilities",
        )
    }
}

fn collect_files(root: &Path) -> io::Result<Vec<PathBuf>> {
    let mut output = Vec::new();
    let mut pending = vec![root.to_path_buf()];
    while let Some(directory) = pending.pop() {
        for entry in fs::read_dir(directory)? {
            let entry = entry?;
            let path = entry.path();
            let name = entry.file_name();
            if entry.file_type()?.is_dir() {
                let relative = path.strip_prefix(root).unwrap_or(&path);
                let in_module_home = relative
                    .components()
                    .next()
                    .and_then(|component| component.as_os_str().to_str())
                    .is_some_and(|component| component.starts_with("amphora-"));
                let unrelated_volatile = !in_module_home
                    && name.to_str().is_some_and(|name| {
                        matches!(
                            name,
                            ".venv"
                                | "__pycache__"
                                | ".pytest_cache"
                                | ".ruff_cache"
                                | ".mypy_cache"
                        ) || name.starts_with(".venv-")
                    });
                let unrelated_nomad = !in_module_home
                    && (relative.starts_with("nomad_crystal360")
                        || relative.starts_with("nomad_feature_hunt")
                        || relative.starts_with("ops/nomad-feature-hunt")
                        || relative.starts_with("ops/nomad-feature-hunt-v2")
                        || relative.starts_with("build/lib/nomad_crystal360")
                        || relative.starts_with("build/lib/nomad_feature_hunt"));
                if matches!(name.to_str(), Some("target" | ".git" | ".amphora"))
                    || unrelated_volatile
                    || unrelated_nomad
                {
                    continue;
                }
                pending.push(path);
            } else if entry.file_type()?.is_file() {
                output.push(path);
            }
        }
    }
    Ok(output)
}

fn remove_python_cache_dirs(root: &Path) -> io::Result<()> {
    let mut pending = vec![root.to_path_buf()];
    let mut caches = Vec::new();
    while let Some(directory) = pending.pop() {
        for entry in fs::read_dir(directory)? {
            let entry = entry?;
            if !entry.file_type()?.is_dir() {
                continue;
            }
            if entry.file_name() == "__pycache__" {
                caches.push(entry.path());
            } else if !matches!(
                entry.file_name().to_str(),
                Some("target" | ".git" | ".amphora")
            ) {
                pending.push(entry.path());
            }
        }
    }
    for cache in caches {
        fs::remove_dir_all(cache)?;
    }
    Ok(())
}

fn sha256(bytes: &[u8]) -> String {
    let mut digest = Sha256::new();
    digest.update(bytes);
    format!("{:x}", digest.finalize())
}

fn atomic_write(path: &Path, bytes: &[u8]) -> io::Result<()> {
    let temporary = path.with_extension(format!("tmp-{}", std::process::id()));
    if temporary.exists() {
        fs::remove_file(&temporary)?;
    }
    let mut file = fs::OpenOptions::new()
        .create_new(true)
        .write(true)
        .open(&temporary)?;
    file.write_all(bytes)?;
    file.sync_all()?;
    fs::rename(temporary, path)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::atomic::{AtomicUsize, Ordering};

    static FIXTURE_ID: AtomicUsize = AtomicUsize::new(0);

    fn workspace_root() -> PathBuf {
        PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .parent()
            .unwrap()
            .to_path_buf()
    }

    fn fixture() -> PathBuf {
        let source_root = workspace_root();
        let root = std::env::temp_dir().join(format!(
            "amphora-cure-metadata-{}-{}",
            std::process::id(),
            FIXTURE_ID.fetch_add(1, Ordering::Relaxed)
        ));
        fs::create_dir_all(root.join("config")).unwrap();
        fs::create_dir_all(root.join("amphora-cure-potlife-gate/docs")).unwrap();
        for relative in [
            "config/module-evidence-inventory.json",
            "amphora-cure-potlife-gate/docs/capability-profile.json",
        ] {
            fs::copy(source_root.join(relative), root.join(relative)).unwrap();
        }
        let inventory: Value = serde_json::from_slice(
            &fs::read(root.join("config/module-evidence-inventory.json")).unwrap(),
        )
        .unwrap();
        let row = inventory["modules"]
            .as_array()
            .unwrap()
            .iter()
            .find(|row| row["module_id"] == "amphora-cure-potlife-gate")
            .unwrap();
        let implementation = row["implementation"].as_object().unwrap();
        let paths = implementation
            .get("path")
            .into_iter()
            .chain(implementation.get("version_source_path"))
            .chain(
                row["tests"]
                    .as_array()
                    .unwrap()
                    .iter()
                    .filter_map(|item| item.get("path")),
            )
            .chain(
                row["artifacts"]
                    .as_array()
                    .unwrap()
                    .iter()
                    .filter_map(|item| item.get("path")),
            )
            .chain(row["runtime_integration"].get("registry_path"));
        for path in paths {
            let relative = path.as_str().unwrap();
            let destination = root.join(relative);
            fs::create_dir_all(destination.parent().unwrap()).unwrap();
            fs::copy(source_root.join(relative), destination).unwrap();
        }
        root
    }

    fn mutate_inventory_and_profile<F>(root: &Path, mutation: F)
    where
        F: Fn(&mut serde_json::Map<String, Value>),
    {
        let inventory_path = root.join("config/module-evidence-inventory.json");
        let profile_path = root.join("amphora-cure-potlife-gate/docs/capability-profile.json");
        let mut inventory: Value =
            serde_json::from_slice(&fs::read(&inventory_path).unwrap()).unwrap();
        let row = inventory["modules"]
            .as_array_mut()
            .unwrap()
            .iter_mut()
            .find(|row| row["module_id"] == "amphora-cure-potlife-gate")
            .unwrap()
            .as_object_mut()
            .unwrap();
        mutation(row);
        let mut mirrored = row.clone();
        fs::write(
            &inventory_path,
            serde_json::to_vec_pretty(&inventory).unwrap(),
        )
        .unwrap();

        let mut profile: Value = serde_json::from_slice(&fs::read(&profile_path).unwrap()).unwrap();
        let evidence = profile["evidence_inventory"].as_object_mut().unwrap();
        mirrored.remove("module_id");
        mirrored.remove("portfolio_edges");
        let registry = evidence.get("registry").unwrap().clone();
        *evidence = mirrored;
        evidence.insert("registry".into(), registry);
        fs::write(&profile_path, serde_json::to_vec_pretty(&profile).unwrap()).unwrap();
    }

    #[test]
    fn cure_metadata_audit_accepts_current_consistent_metadata() {
        let root = fixture();
        audit_cure_pot_life_metadata(&root).unwrap();
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn cure_metadata_audit_does_not_depend_on_legacy_implementation_paths() {
        let root = fixture();
        mutate_inventory_and_profile(&root, |row| {
            row["implementation"]["path"] = Value::String("missing/native.rs".into());
        });
        audit_cure_pot_life_metadata(&root).unwrap();
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn cure_metadata_audit_does_not_depend_on_legacy_implementation_hashes() {
        let root = fixture();
        mutate_inventory_and_profile(&root, |row| {
            row["implementation"]["sha256"] = Value::String("0".repeat(64));
        });
        audit_cure_pot_life_metadata(&root).unwrap();
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn cure_metadata_audit_rejects_profile_inventory_divergence() {
        let root = fixture();
        let profile_path = root.join("amphora-cure-potlife-gate/docs/capability-profile.json");
        let mut profile: Value = serde_json::from_slice(&fs::read(&profile_path).unwrap()).unwrap();
        profile["evidence_inventory"]["external_dependencies"] = serde_json::json!(["DIVERGED"]);
        fs::write(&profile_path, serde_json::to_vec_pretty(&profile).unwrap()).unwrap();
        let error = audit_cure_pot_life_metadata(&root).unwrap_err().to_string();
        assert!(error.contains("diverges"));
        fs::remove_dir_all(root).unwrap();
    }
}
