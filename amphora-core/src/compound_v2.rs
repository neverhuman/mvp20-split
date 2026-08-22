use crate::{
    jcs_bytes, jcs_sha256, verify_dsse, CampaignCohortThresholdsV1, CampaignGenerationRequestV1,
    CampaignPairingRuleV1, CampaignStageCountsV1, DsseEnvelope, JcsError, TrustStore,
};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};
use std::fs;
use std::path::{Component, Path};
use std::process::Command;
use thiserror::Error;

pub const COMPOUND_CAMPAIGN_SCHEMA_V2: &str = "amphora.compound-campaign.v2";
pub const COMPOUND_CAMPAIGN_RESULT_SCHEMA_V2: &str = "amphora.compound-campaign-result.v2";
pub const TOOLCHAIN_MANIFEST_SCHEMA: &str = "amphora.toolchain-manifest.v1";
pub const ORD_SCHEMA_IDENTITY_SCHEMA: &str = "amphora.ord-schema-identity.v1";
pub const ORD_REACTION_RECORD_SCHEMA: &str = "amphora.ord-reaction-record.v1";
pub const ORD_EXCLUSION_SCHEMA: &str = "amphora.ord-exclusion.v1";
pub const REACTION_SPLIT_MANIFEST_SCHEMA: &str = "amphora.reaction-split-manifest.v1";
pub const REACTION_GRAMMAR_CORPUS_SCHEMA: &str = "amphora.reaction-grammar-corpus.v1";
pub const METHOD_REGISTRY_SCHEMA: &str = "amphora.method-registry.v1";
pub const METHOD_BENCHMARK_LOCK_SCHEMA: &str = "amphora.method-benchmark-lock.v1";
pub const CAMPAIGN_EXECUTION_RECEIPT_SCHEMA: &str = "amphora.compound-execution-receipt.v1";
pub const COMPOUND_CARD_SCHEMA: &str = "amphora.compound-card.v1";
pub const CAMPAIGN_INDEPENDENT_REVIEW_RECEIPT_SCHEMA: &str =
    "amphora.compound-independent-review-receipt.v1";
pub const CAMPAIGN_MANIFEST_PAYLOAD_TYPE: &str = "application/vnd.amphora.compound-campaign.v2+jcs";

const REQUIRED_RDKIT_VERSION: &str = "2026.03.2";
const REQUIRED_RDKIT_COMMIT: &str = "42fe8c952589bb750e27ea7f259a50b36576bfa5";
const REQUIRED_RDKIT_SOURCE_SHA256: &str =
    "9bea418c32b553920dc3491b282bbfc47e10728ad20ea874ca47c38cc1b0818b";
const REQUIRED_UBUNTU_INDEX_DIGEST: &str =
    "sha256:4fbb8e6a8395de5a7550b33509421a2bafbc0aab6c06ba2cef9ebffbc7092d90";
const REQUIRED_UBUNTU_AMD64_DIGEST: &str =
    "sha256:52df9b1ee71626e0088f7d400d5c6b5f7bb916f8f0c82b474289a4ece6cf3faf";
const REQUIRED_UBUNTU_SNAPSHOT: &str = "2026-07-19T00:00:00Z";
const REQUIRED_ORD_VERSION: &str = "0.6.3";
const REQUIRED_ORD_TAG_OBJECT: &str = "0a6c92558898156f06365220d3acbe2bea0a1e69";
const REQUIRED_ORD_SOURCE_COMMIT: &str = "7eb730963d7a47e1d6a6c5366806ad2133422df4";
const REQUIRED_DATASET_PROTO_SHA256: &str =
    "60f44fbf7b01c0e0d219d7017254c64034eaee8d739a148f33d53c36ecc52b11";
const REQUIRED_REACTION_PROTO_SHA256: &str =
    "f1546142d8b727f9c05aee7176287f1b0ff172966d125cd1f44b1a910530ceea";
const REQUIRED_TEST_PROTO_SHA256: &str =
    "86cfe00045a1439463f33fc132f578e8eab942f7cc82bf6b7207e685f69c01e4";
const REQUIRED_FAMILIES: [&str; 2] = ["ORD_GLYCIDYL_ETHER_FORMATION", "ORD_REDUCTIVE_AMINATION"];
const REQUIRED_MODULES: [&str; 29] = [
    "amphora-barrier-corrosion-score",
    "amphora-candidate-contract",
    "amphora-cro-protocol-packager",
    "amphora-cure-potlife-gate",
    "amphora-design-rule-score",
    "amphora-envelope-gates",
    "amphora-evidence-intake-validator",
    "amphora-formulation-arithmetic",
    "amphora-formulation-universe",
    "amphora-ingredient-library",
    "amphora-ip-fto-guard",
    "amphora-known-answer-benchmarks",
    "amphora-model-card-authority",
    "amphora-molecule-design-gate",
    "amphora-molecule-generator",
    "amphora-molecule-novelty",
    "amphora-molecule-property",
    "amphora-molecule-role-ranker",
    "amphora-optimizer-orchestrator",
    "amphora-process-qc-twin",
    "amphora-public-corrosion-benchmark",
    "amphora-redteam-audit",
    "amphora-report-packager",
    "amphora-run-provenance",
    "amphora-solvency-score",
    "amphora-source-ledger",
    "amphora-sourceability-ehs",
    "amphora-tolerance-robustness",
    "amphora-viscosity-score",
];

pub fn required_compound_report_modules() -> &'static [&'static str] {
    &REQUIRED_MODULES
}

#[derive(Debug, Error)]
pub enum CompoundV2Error {
    #[error("invalid compound v2 contract: {0}")]
    Invalid(&'static str),
    #[error("invalid or all-zero SHA-256: {0}")]
    Hash(String),
    #[error("unsafe repository-relative path: {0}")]
    Path(String),
    #[error("bound artifact is absent: {0}")]
    MissingArtifact(String),
    #[error("bound artifact hash mismatch for {path}: expected {expected}, observed {observed}")]
    ArtifactHash {
        path: String,
        expected: String,
        observed: String,
    },
    #[error("JCS: {0}")]
    Jcs(#[from] JcsError),
    #[error("JSON: {0}")]
    Json(#[from] serde_json::Error),
    #[error("I/O: {0}")]
    Io(#[from] std::io::Error),
    #[error("DSSE verification failed: {0}")]
    Dsse(#[from] crate::VerificationError),
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct FileArtifactBindingV1 {
    pub path: String,
    pub sha256: String,
}

impl FileArtifactBindingV1 {
    pub fn validate(&self) -> Result<(), CompoundV2Error> {
        require_safe_path(&self.path)?;
        require_hash(&self.sha256)
    }

    pub fn verify(&self, root: &Path) -> Result<(), CompoundV2Error> {
        self.validate()?;
        let path = root.join(&self.path);
        let metadata = fs::symlink_metadata(&path)
            .map_err(|_| CompoundV2Error::MissingArtifact(self.path.clone()))?;
        if !metadata.file_type().is_file() || metadata.file_type().is_symlink() {
            return Err(CompoundV2Error::MissingArtifact(self.path.clone()));
        }
        let observed = sha256_bytes(&fs::read(&path)?);
        if observed != self.sha256 {
            return Err(CompoundV2Error::ArtifactHash {
                path: self.path.clone(),
                expected: self.sha256.clone(),
                observed,
            });
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct InstalledFileV1 {
    pub path: String,
    pub size: u64,
    pub mode: u32,
    pub sha256: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct ToolchainDependencyV1 {
    pub name: String,
    pub version: String,
    pub source_identity: String,
    pub sha256: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct SharedLibraryV1 {
    pub path: String,
    pub soname: String,
    pub needed: Vec<String>,
    pub runpath: Option<String>,
    pub rpath: Option<String>,
    pub resolved_runtime_closure: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct ToolchainTestReceiptV1 {
    pub command: Vec<String>,
    pub passed: u64,
    pub failed: u64,
    pub skipped: u64,
    pub log: FileArtifactBindingV1,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct ToolchainReproducibilityV1 {
    pub first_tree_sha256: String,
    pub second_tree_sha256: String,
    pub comparison_receipt: FileArtifactBindingV1,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct ToolchainPgoV1 {
    pub corpus_manifest: FileArtifactBindingV1,
    pub raw_profile_sha256: String,
    pub merged_profile_sha256: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct ToolchainManifestV1 {
    pub schema: String,
    pub profile_id: String,
    pub rdkit_version: String,
    pub rdkit_commit: String,
    pub source_archive_sha256: String,
    pub ubuntu_image_index_digest: String,
    pub ubuntu_amd64_manifest_digest: String,
    pub ubuntu_snapshot_timestamp: String,
    pub ubuntu_inrelease: FileArtifactBindingV1,
    pub ubuntu_release: FileArtifactBindingV1,
    pub ubuntu_package_indexes: Vec<FileArtifactBindingV1>,
    pub compiler: String,
    pub linker: String,
    pub cmake: String,
    pub ninja: String,
    pub cxx_standard: String,
    pub compile_flags: Vec<String>,
    pub link_flags: Vec<String>,
    pub enabled_rdkit_components: Vec<String>,
    pub python_wrappers_enabled: bool,
    pub cpu_requirements: Vec<String>,
    pub observed_build_host_features: Vec<String>,
    pub dependencies: Vec<ToolchainDependencyV1>,
    pub installed_files: Vec<InstalledFileV1>,
    pub shared_libraries: Vec<SharedLibraryV1>,
    pub cpp_tests: ToolchainTestReceiptV1,
    pub portable_reproducibility: Option<ToolchainReproducibilityV1>,
    pub pgo: Option<ToolchainPgoV1>,
    pub spdx_3_sbom: FileArtifactBindingV1,
    pub slsa_v1_2_provenance: FileArtifactBindingV1,
    pub install_prefix: String,
    pub installed_tree_sha256: String,
    pub manifest_payload_jcs_sha256: String,
}

impl ToolchainManifestV1 {
    pub fn validate(&self) -> Result<(), CompoundV2Error> {
        if self.schema != TOOLCHAIN_MANIFEST_SCHEMA {
            return Err(CompoundV2Error::Invalid("toolchain schema"));
        }
        if !matches!(
            self.profile_id.as_str(),
            "portable-x86-64-v2" | "host-optimized-znver2-avx2-lto-pgo"
        ) || self.rdkit_version != REQUIRED_RDKIT_VERSION
            || self.rdkit_commit != REQUIRED_RDKIT_COMMIT
            || self.source_archive_sha256 != REQUIRED_RDKIT_SOURCE_SHA256
            || self.ubuntu_image_index_digest != REQUIRED_UBUNTU_INDEX_DIGEST
            || self.ubuntu_amd64_manifest_digest != REQUIRED_UBUNTU_AMD64_DIGEST
            || self.ubuntu_snapshot_timestamp != REQUIRED_UBUNTU_SNAPSHOT
            || self.compiler.trim().is_empty()
            || self.linker.trim().is_empty()
            || self.cmake.trim().is_empty()
            || self.ninja.trim().is_empty()
            || self.cxx_standard != "C++20"
            || self.compile_flags.is_empty()
            || self.link_flags.is_empty()
            || self.python_wrappers_enabled
            || self.cpu_requirements.is_empty()
            || self.observed_build_host_features.is_empty()
            || self.dependencies.is_empty()
            || self.installed_files.is_empty()
            || self.shared_libraries.is_empty()
            || self.cpp_tests.command.is_empty()
            || self.cpp_tests.passed == 0
            || self.cpp_tests.failed != 0
            || self.ubuntu_package_indexes.is_empty()
        {
            return Err(CompoundV2Error::Invalid("toolchain content"));
        }
        require_hash(&self.installed_tree_sha256)?;
        require_hash(&self.manifest_payload_jcs_sha256)?;
        require_safe_path(&self.install_prefix)?;
        let required_components = [
            "INCHI",
            "MOLSTANDARDIZE",
            "MOLDRAW2D_SVG",
            "DESCRIPTORS",
            "MORGAN_FINGERPRINTS",
            "REACTIONS",
            "SUBSTRUCTURE_MATCHING",
            "SUBSTRUCT_LIBRARY",
            "CPP_TESTS",
        ];
        if required_components.iter().any(|component| {
            !self
                .enabled_rdkit_components
                .iter()
                .any(|observed| observed == component)
        }) {
            return Err(CompoundV2Error::Invalid("enabled RDKit components"));
        }
        for required_flag in [
            "-O3",
            "-fno-fast-math",
            "-fno-unsafe-math-optimizations",
            "-ffp-contract=off",
        ] {
            if !self.compile_flags.iter().any(|flag| flag == required_flag) {
                return Err(CompoundV2Error::Invalid("strict floating-point flags"));
            }
        }
        if !self
            .compile_flags
            .iter()
            .any(|flag| flag.starts_with("-ffile-prefix-map="))
            || !self.compiler.to_ascii_lowercase().contains("gcc")
            || !self.compiler.contains("13.3")
            || !self.cmake.contains("4.3.2")
        {
            return Err(CompoundV2Error::Invalid("pinned build tools"));
        }
        for binding in self.ubuntu_package_indexes.iter().chain([
            &self.ubuntu_inrelease,
            &self.ubuntu_release,
            &self.cpp_tests.log,
            &self.spdx_3_sbom,
            &self.slsa_v1_2_provenance,
        ]) {
            binding.validate()?;
        }
        validate_sorted_unique(
            self.installed_files.iter().map(|row| row.path.as_str()),
            "installed-file inventory",
        )?;
        for row in &self.installed_files {
            require_safe_path(&row.path)?;
            require_hash(&row.sha256)?;
        }
        let mut dependencies = BTreeSet::new();
        for row in &self.dependencies {
            if row.name.trim().is_empty()
                || row.version.trim().is_empty()
                || row.source_identity.trim().is_empty()
                || !dependencies.insert(row.name.as_str())
            {
                return Err(CompoundV2Error::Invalid("toolchain dependency"));
            }
            require_hash(&row.sha256)?;
        }
        if !self
            .dependencies
            .iter()
            .any(|row| row.name.eq_ignore_ascii_case("boost") && row.version == "1.89.0")
            || manifest_mentions_python(self)
        {
            return Err(CompoundV2Error::Invalid("toolchain dependency closure"));
        }
        for library in &self.shared_libraries {
            require_safe_path(&library.path)?;
            if library.soname.trim().is_empty()
                || library.needed.iter().any(|name| name.trim().is_empty())
                || library
                    .resolved_runtime_closure
                    .iter()
                    .any(|path| path.trim().is_empty())
                || library
                    .runpath
                    .as_deref()
                    .is_some_and(|path| !path.split(':').all(|row| row.starts_with("$ORIGIN")))
                || library.rpath.is_some()
            {
                return Err(CompoundV2Error::Invalid("shared-library closure"));
            }
        }
        match self.profile_id.as_str() {
            "portable-x86-64-v2" => {
                if !self
                    .compile_flags
                    .iter()
                    .any(|flag| flag == "-march=x86-64-v2")
                    || !self
                        .compile_flags
                        .iter()
                        .any(|flag| flag == "-mtune=generic")
                {
                    return Err(CompoundV2Error::Invalid("portable CPU flags"));
                }
                let reproducibility = self
                    .portable_reproducibility
                    .as_ref()
                    .ok_or(CompoundV2Error::Invalid("portable reproducibility"))?;
                require_hash(&reproducibility.first_tree_sha256)?;
                require_hash(&reproducibility.second_tree_sha256)?;
                reproducibility.comparison_receipt.validate()?;
                if reproducibility.first_tree_sha256 != reproducibility.second_tree_sha256
                    || reproducibility.first_tree_sha256 != self.installed_tree_sha256
                    || self.pgo.is_some()
                {
                    return Err(CompoundV2Error::Invalid("portable reproducibility"));
                }
            }
            "host-optimized-znver2-avx2-lto-pgo" => {
                if !self
                    .compile_flags
                    .iter()
                    .any(|flag| flag == "-march=znver2")
                    || !self
                        .compile_flags
                        .iter()
                        .any(|flag| flag == "-mtune=znver2")
                    || !self.compile_flags.iter().any(|flag| flag == "-flto=auto")
                {
                    return Err(CompoundV2Error::Invalid("optimized CPU flags"));
                }
                if self.portable_reproducibility.is_some() {
                    return Err(CompoundV2Error::Invalid("optimized reproducibility fields"));
                }
                let pgo = self
                    .pgo
                    .as_ref()
                    .ok_or(CompoundV2Error::Invalid("optimized PGO"))?;
                pgo.corpus_manifest.validate()?;
                require_hash(&pgo.raw_profile_sha256)?;
                require_hash(&pgo.merged_profile_sha256)?;
                for feature in ["avx2", "fma", "bmi2", "popcnt"] {
                    if !self.cpu_requirements.iter().any(|row| row == feature) {
                        return Err(CompoundV2Error::Invalid("optimized CPU requirements"));
                    }
                }
            }
            _ => unreachable!(),
        }
        self.verify_self_hash()
    }

    pub fn verify_files(&self, root: &Path) -> Result<(), CompoundV2Error> {
        self.validate()?;
        for binding in self.ubuntu_package_indexes.iter().chain([
            &self.ubuntu_inrelease,
            &self.ubuntu_release,
            &self.cpp_tests.log,
            &self.spdx_3_sbom,
            &self.slsa_v1_2_provenance,
        ]) {
            binding.verify(root)?;
        }
        if let Some(row) = &self.portable_reproducibility {
            row.comparison_receipt.verify(root)?;
        }
        if let Some(row) = &self.pgo {
            row.corpus_manifest.verify(root)?;
        }
        let install_root = root.join(&self.install_prefix);
        let install_metadata = fs::symlink_metadata(&install_root)
            .map_err(|_| CompoundV2Error::MissingArtifact(self.install_prefix.clone()))?;
        if !install_metadata.is_dir() || install_metadata.file_type().is_symlink() {
            return Err(CompoundV2Error::Invalid("toolchain install prefix"));
        }
        for installed in &self.installed_files {
            let path = install_root.join(&installed.path);
            let metadata = fs::symlink_metadata(&path)?;
            if !metadata.file_type().is_file() || metadata.file_type().is_symlink() {
                return Err(CompoundV2Error::Invalid("installed-file type"));
            }
            if sha256_bytes(&fs::read(&path)?) != installed.sha256 {
                return Err(CompoundV2Error::Invalid("installed-file hash"));
            }
            if metadata.len() != installed.size {
                return Err(CompoundV2Error::Invalid("installed-file size"));
            }
            #[cfg(unix)]
            {
                use std::os::unix::fs::PermissionsExt;
                if metadata.permissions().mode() & 0o7777 != installed.mode {
                    return Err(CompoundV2Error::Invalid("installed-file mode"));
                }
            }
        }
        let observed_files = inventory_install_tree(&install_root)?;
        if observed_files != self.installed_files {
            return Err(CompoundV2Error::Invalid("installed-file inventory closure"));
        }
        let tree_hash = installed_tree_hash(&self.installed_files)?;
        if tree_hash != self.installed_tree_sha256 {
            return Err(CompoundV2Error::Invalid("installed-tree hash"));
        }
        for library in &self.shared_libraries {
            verify_elf_dynamic_section(&install_root.join(&library.path), library)?;
            for closure_path in &library.resolved_runtime_closure {
                let resolved = if Path::new(closure_path).is_absolute() {
                    Path::new(closure_path).to_path_buf()
                } else {
                    install_root.join(closure_path)
                };
                if !resolved.is_file() {
                    return Err(CompoundV2Error::Invalid("resolved runtime closure"));
                }
            }
        }
        if self.profile_id == "host-optimized-znver2-avx2-lto-pgo" {
            verify_runtime_cpu_features(&self.cpu_requirements)?;
        }
        Ok(())
    }

    pub fn seal_self_hash(&mut self) -> Result<(), CompoundV2Error> {
        self.manifest_payload_jcs_sha256.clear();
        self.manifest_payload_jcs_sha256 = jcs_sha256(self)?;
        Ok(())
    }

    fn verify_self_hash(&self) -> Result<(), CompoundV2Error> {
        let mut unsigned = self.clone();
        unsigned.manifest_payload_jcs_sha256.clear();
        let expected = jcs_sha256(&unsigned)?;
        if self.manifest_payload_jcs_sha256 != expected {
            return Err(CompoundV2Error::Invalid("toolchain manifest self-hash"));
        }
        Ok(())
    }
}

/// Load and fully verify one installed toolchain profile using the shared
/// implementation consumed by both command-line frontends.
pub fn verify_toolchain_profile(
    root: &Path,
    profile: &str,
) -> Result<ToolchainManifestV1, CompoundV2Error> {
    let directory = match profile {
        "portable" | "portable-x86-64-v2" => "portable",
        "host-optimized" | "host-optimized-znver2-avx2-lto-pgo" => "host-optimized",
        _ => return Err(CompoundV2Error::Invalid("unknown toolchain profile")),
    };
    let relative = format!(
        "artifacts/toolchains/rdkit-{REQUIRED_RDKIT_VERSION}/{directory}/build-manifest.v1.json"
    );
    let path = root.join(&relative);
    let metadata = fs::symlink_metadata(&path)
        .map_err(|_| CompoundV2Error::MissingArtifact(relative.clone()))?;
    if !metadata.file_type().is_file() || metadata.file_type().is_symlink() {
        return Err(CompoundV2Error::MissingArtifact(relative));
    }
    let bytes = fs::read(&path)?;
    let value = crate::parse_json_strict(&bytes)
        .map_err(|_| CompoundV2Error::Invalid("toolchain manifest JSON"))?;
    let manifest: ToolchainManifestV1 = serde_json::from_value(value)?;
    manifest.validate()?;
    if bytes != jcs_bytes(&manifest)? {
        return Err(CompoundV2Error::Invalid(
            "toolchain manifest is not authoritative compact JCS",
        ));
    }
    let expected_profile = if directory == "portable" {
        "portable-x86-64-v2"
    } else {
        "host-optimized-znver2-avx2-lto-pgo"
    };
    if manifest.profile_id != expected_profile {
        return Err(CompoundV2Error::Invalid("toolchain profile path binding"));
    }
    manifest.verify_files(root)?;
    Ok(manifest)
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct OrdSchemaIdentityV1 {
    pub schema: String,
    pub version: String,
    pub tagged_object_commit: String,
    pub source_commit: String,
    pub dataset_proto_sha256: String,
    pub reaction_proto_sha256: String,
    pub test_proto_sha256: String,
    pub descriptor_set_sha256: String,
}

impl OrdSchemaIdentityV1 {
    pub fn validate(&self) -> Result<(), CompoundV2Error> {
        if self.schema != ORD_SCHEMA_IDENTITY_SCHEMA
            || self.version != REQUIRED_ORD_VERSION
            || self.tagged_object_commit != REQUIRED_ORD_TAG_OBJECT
            || self.source_commit != REQUIRED_ORD_SOURCE_COMMIT
            || self.dataset_proto_sha256 != REQUIRED_DATASET_PROTO_SHA256
            || self.reaction_proto_sha256 != REQUIRED_REACTION_PROTO_SHA256
            || self.test_proto_sha256 != REQUIRED_TEST_PROTO_SHA256
        {
            return Err(CompoundV2Error::Invalid("ORD schema identity"));
        }
        require_hash(&self.descriptor_set_sha256)
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct OrdDatasetRecordV1 {
    pub schema: String,
    pub source_object_path: String,
    pub source_object_sha256: String,
    pub dataset_id: String,
    pub reaction_count: u64,
    pub raw_dataset_sha256: String,
    pub schema_identity: OrdSchemaIdentityV1,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct OrdCompoundV1 {
    pub canonical_isomeric_smiles: String,
    pub canonical_structure_sha256: String,
    pub atom_map_numbers: Vec<u32>,
    pub scaffold_sha256: String,
    pub reaction_role: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum OrdBondChangeKindV1 {
    Addition,
    Deletion,
    OrderChange,
    StereoChange,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct OrdBondChangeV1 {
    pub kind: OrdBondChangeKindV1,
    pub atom_map_a: u32,
    pub atom_map_b: u32,
    pub before_order: Option<String>,
    pub after_order: Option<String>,
    pub before_stereo: Option<String>,
    pub after_stereo: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct OrdReactionCenterV1 {
    pub atom_maps: Vec<u32>,
    pub bonds: Vec<OrdBondChangeV1>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct ReactionComponentV1 {
    pub component_id: String,
    pub reaction_ids: Vec<String>,
    pub canonical_reaction_identities: Vec<String>,
    pub compound_family_identities: Vec<String>,
    pub scaffold_hashes: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct OrdReactionRecordV1 {
    pub schema: String,
    pub source_object_path: String,
    pub source_object_sha256: String,
    pub dataset_id: String,
    pub reaction_ordinal: u64,
    pub reaction_id: String,
    pub raw_reaction_message_sha256: String,
    pub reactants: Vec<OrdCompoundV1>,
    pub products: Vec<OrdCompoundV1>,
    pub mapped_reaction_identifier: String,
    pub bond_changes: Vec<OrdBondChangeV1>,
    pub reaction_center: OrdReactionCenterV1,
    pub reaction_family: String,
    pub validation_state: String,
    pub schema_identity: OrdSchemaIdentityV1,
}

impl OrdReactionRecordV1 {
    pub fn validate(&self) -> Result<(), CompoundV2Error> {
        if self.schema != ORD_REACTION_RECORD_SCHEMA
            || self.source_object_path.trim().is_empty()
            || self.dataset_id.trim().is_empty()
            || self.reaction_id.trim().is_empty()
            || self.mapped_reaction_identifier.trim().is_empty()
            || self.reactants.is_empty()
            || self.products.is_empty()
            || self.bond_changes.is_empty()
            || self.reaction_center.atom_maps.is_empty()
            || self.reaction_center.bonds.is_empty()
            || self.validation_state.trim().is_empty()
            || !(REQUIRED_FAMILIES.contains(&self.reaction_family.as_str())
                || self.reaction_family == "UNCLASSIFIED")
        {
            return Err(CompoundV2Error::Invalid("ORD reaction record"));
        }
        require_safe_path(&self.source_object_path)?;
        require_hash(&self.source_object_sha256)?;
        require_hash(&self.raw_reaction_message_sha256)?;
        self.schema_identity.validate()?;
        let center_atoms = self
            .reaction_center
            .atom_maps
            .iter()
            .copied()
            .collect::<BTreeSet<_>>();
        if center_atoms.len() != self.reaction_center.atom_maps.len()
            || self.reaction_center.bonds != self.bond_changes
        {
            return Err(CompoundV2Error::Invalid("ORD reaction center"));
        }
        for compound in self.reactants.iter().chain(&self.products) {
            if compound.canonical_isomeric_smiles.trim().is_empty()
                || compound.reaction_role.trim().is_empty()
                || compound.atom_map_numbers.is_empty()
            {
                return Err(CompoundV2Error::Invalid("ORD compound"));
            }
            require_hash(&compound.canonical_structure_sha256)?;
            require_hash(&compound.scaffold_sha256)?;
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum OrdExclusionScopeV1 {
    Dataset,
    Reaction,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum OrdExclusionReasonV1 {
    MissingDatasetId,
    MissingReactionId,
    ProtobufDecodeFailed,
    RawReactionScanMismatch,
    MissingMappedIdentifier,
    AmbiguousMappedIdentifier,
    UnsupportedReactant,
    UnsupportedProduct,
    AmbiguousProductOutcome,
    StructuredMappedMismatch,
    MissingAtomMap,
    DuplicateAtomMap,
    UnmappedChangedAtom,
    ZeroBondChanges,
    DisconnectedReactionCenter,
    UnsupportedStereo,
    UnsupportedStructure,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct OrdExclusionV1 {
    pub schema: String,
    pub scope: OrdExclusionScopeV1,
    pub reason: OrdExclusionReasonV1,
    pub source_object_path: String,
    pub source_object_sha256: String,
    pub dataset_id: Option<String>,
    pub reaction_id: Option<String>,
    pub reaction_ordinal: Option<u64>,
    pub raw_reaction_message_sha256: Option<String>,
    pub detail: String,
}

impl OrdExclusionV1 {
    pub fn validate(&self) -> Result<(), CompoundV2Error> {
        if self.schema != ORD_EXCLUSION_SCHEMA || self.detail.trim().is_empty() {
            return Err(CompoundV2Error::Invalid("ORD exclusion"));
        }
        require_safe_path(&self.source_object_path)?;
        require_hash(&self.source_object_sha256)?;
        if let Some(hash) = &self.raw_reaction_message_sha256 {
            require_hash(hash)?;
        }
        match self.scope {
            OrdExclusionScopeV1::Dataset => {
                if self.reaction_id.is_some()
                    || self.reaction_ordinal.is_some()
                    || self.raw_reaction_message_sha256.is_some()
                {
                    return Err(CompoundV2Error::Invalid("dataset exclusion scope"));
                }
            }
            OrdExclusionScopeV1::Reaction => {
                if self.reaction_ordinal.is_none() || self.raw_reaction_message_sha256.is_none() {
                    return Err(CompoundV2Error::Invalid("reaction exclusion scope"));
                }
            }
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum ReactionSplitComponentV1 {
    Extraction,
    Validation,
    HeldOut,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct ReactionSplitManifestV1 {
    pub schema: String,
    pub seed: u64,
    pub components: Vec<ReactionComponentV1>,
    pub assignments: BTreeMap<String, ReactionSplitComponentV1>,
    pub extraction_reaction_ids: Vec<String>,
    pub validation_reaction_ids: Vec<String>,
    pub heldout_reaction_ids: Vec<String>,
    pub leakage_proof_sha256: String,
    pub split_jcs_sha256: String,
}

impl ReactionSplitManifestV1 {
    pub fn seal_self_hash(&mut self) -> Result<(), CompoundV2Error> {
        self.leakage_proof_sha256 =
            split_leakage_proof_hash(self.seed, &self.components, &self.assignments)?;
        self.split_jcs_sha256.clear();
        self.split_jcs_sha256 = jcs_sha256(self)?;
        self.validate()
    }

    pub fn validate(&self) -> Result<(), CompoundV2Error> {
        if self.schema != REACTION_SPLIT_MANIFEST_SCHEMA
            || self.seed == 0
            || self.components.is_empty()
            || self.extraction_reaction_ids.is_empty()
            || self.validation_reaction_ids.is_empty()
            || self.heldout_reaction_ids.is_empty()
        {
            return Err(CompoundV2Error::Invalid("reaction split"));
        }
        require_hash(&self.leakage_proof_sha256)?;
        require_hash(&self.split_jcs_sha256)?;
        validate_sorted_unique(
            self.extraction_reaction_ids.iter().map(String::as_str),
            "reaction split extraction ordering",
        )?;
        validate_sorted_unique(
            self.validation_reaction_ids.iter().map(String::as_str),
            "reaction split validation ordering",
        )?;
        validate_sorted_unique(
            self.heldout_reaction_ids.iter().map(String::as_str),
            "reaction split held-out ordering",
        )?;
        if self.assignments.len() != self.components.len()
            || self
                .components
                .windows(2)
                .any(|window| window[0].component_id >= window[1].component_id)
        {
            return Err(CompoundV2Error::Invalid("reaction split partition"));
        }
        let mut component_ids = BTreeSet::new();
        let mut reaction_ids = BTreeSet::new();
        let mut reaction_identities = BTreeSet::new();
        let mut compound_families = BTreeSet::new();
        let mut scaffolds = BTreeSet::new();
        let mut expected_extraction = Vec::new();
        let mut expected_validation = Vec::new();
        let mut expected_heldout = Vec::new();
        for component in &self.components {
            validate_sorted_unique(
                component.reaction_ids.iter().map(String::as_str),
                "reaction component reaction IDs",
            )?;
            validate_sorted_unique(
                component
                    .canonical_reaction_identities
                    .iter()
                    .map(String::as_str),
                "reaction component identities",
            )?;
            validate_sorted_unique(
                component
                    .compound_family_identities
                    .iter()
                    .map(String::as_str),
                "reaction component compound families",
            )?;
            validate_sorted_unique(
                component.scaffold_hashes.iter().map(String::as_str),
                "reaction component scaffolds",
            )?;
            for hash in &component.scaffold_hashes {
                require_hash(hash)?;
            }
            let expected_id = reaction_component_id(self.seed, &component.reaction_ids)?;
            let expected_partition = reaction_component_partition(&expected_id)?;
            if component.component_id != expected_id
                || !component_ids.insert(component.component_id.as_str())
                || self.assignments.get(&component.component_id) != Some(&expected_partition)
                || component
                    .reaction_ids
                    .iter()
                    .any(|id| !reaction_ids.insert(id.as_str()))
                || component
                    .canonical_reaction_identities
                    .iter()
                    .any(|id| !reaction_identities.insert(id.as_str()))
                || component
                    .compound_family_identities
                    .iter()
                    .any(|id| !compound_families.insert(id.as_str()))
                || component
                    .scaffold_hashes
                    .iter()
                    .any(|id| !scaffolds.insert(id.as_str()))
            {
                return Err(CompoundV2Error::Invalid("reaction split component"));
            }
            match expected_partition {
                ReactionSplitComponentV1::Extraction => {
                    expected_extraction.extend(component.reaction_ids.iter().cloned())
                }
                ReactionSplitComponentV1::Validation => {
                    expected_validation.extend(component.reaction_ids.iter().cloned())
                }
                ReactionSplitComponentV1::HeldOut => {
                    expected_heldout.extend(component.reaction_ids.iter().cloned())
                }
            }
        }
        expected_extraction.sort();
        expected_validation.sort();
        expected_heldout.sort();
        if expected_extraction != self.extraction_reaction_ids
            || expected_validation != self.validation_reaction_ids
            || expected_heldout != self.heldout_reaction_ids
            || self.leakage_proof_sha256
                != split_leakage_proof_hash(self.seed, &self.components, &self.assignments)?
        {
            return Err(CompoundV2Error::Invalid(
                "reaction split coverage or leakage proof",
            ));
        }
        let mut unsigned = self.clone();
        unsigned.split_jcs_sha256.clear();
        if jcs_sha256(&unsigned)? != self.split_jcs_sha256 {
            return Err(CompoundV2Error::Invalid("reaction split self-hash"));
        }
        Ok(())
    }
}

fn reaction_component_id(seed: u64, reaction_ids: &[String]) -> Result<String, CompoundV2Error> {
    Ok(jcs_sha256(&serde_json::json!({
        "seed": seed,
        "reaction_ids": reaction_ids,
    }))?)
}

fn reaction_component_partition(
    component_id: &str,
) -> Result<ReactionSplitComponentV1, CompoundV2Error> {
    require_hash(component_id)?;
    let bucket = u64::from_str_radix(&component_id[..16], 16)
        .map_err(|_| CompoundV2Error::Invalid("reaction component hash bucket"))?
        % 100;
    Ok(match bucket {
        0..=69 => ReactionSplitComponentV1::Extraction,
        70..=84 => ReactionSplitComponentV1::Validation,
        _ => ReactionSplitComponentV1::HeldOut,
    })
}

fn split_leakage_proof_hash(
    seed: u64,
    components: &[ReactionComponentV1],
    assignments: &BTreeMap<String, ReactionSplitComponentV1>,
) -> Result<String, CompoundV2Error> {
    Ok(jcs_sha256(&serde_json::json!({
        "seed": seed,
        "components": components,
        "assignments": assignments,
        "canonical_reaction_identity_crossings": [],
        "compound_family_identity_crossings": [],
        "scaffold_crossings": [],
    }))?)
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct ReactionGrammarRuleV1 {
    pub family: String,
    pub canonical_reaction_smarts: String,
    pub applicability_fingerprint: Vec<u8>,
    pub required_substructures: Vec<String>,
    pub changed_atoms: Vec<u32>,
    pub changed_bonds: Vec<OrdBondChangeV1>,
    pub stereo_behavior: String,
    pub extraction_source_reaction_ids: Vec<String>,
    pub extraction_source_dataset_ids: Vec<String>,
    pub extraction_partition_component_ids: Vec<String>,
    pub template_sha256: String,
    pub rule_jcs_sha256: String,
}

impl ReactionGrammarRuleV1 {
    pub fn seal_self_hash(&mut self) -> Result<(), CompoundV2Error> {
        self.required_substructures.sort();
        self.changed_atoms.sort_unstable();
        self.extraction_source_reaction_ids.sort();
        self.extraction_source_dataset_ids.sort();
        self.extraction_partition_component_ids.sort();
        for bond in &mut self.changed_bonds {
            if bond.atom_map_a > bond.atom_map_b {
                std::mem::swap(&mut bond.atom_map_a, &mut bond.atom_map_b);
            }
        }
        self.changed_bonds
            .sort_by(|left, right| bond_change_sort_key(left).cmp(&bond_change_sort_key(right)));
        self.template_sha256 = sha256_bytes(self.canonical_reaction_smarts.as_bytes());
        self.rule_jcs_sha256.clear();
        self.rule_jcs_sha256 = jcs_sha256(self)?;
        self.validate()
    }

    pub fn validate(&self) -> Result<(), CompoundV2Error> {
        if !REQUIRED_FAMILIES.contains(&self.family.as_str())
            || self.canonical_reaction_smarts.trim().is_empty()
            || self.applicability_fingerprint.len() != 256
            || self.changed_bonds.is_empty()
            || self.stereo_behavior.trim().is_empty()
        {
            return Err(CompoundV2Error::Invalid("grammar rule"));
        }
        validate_sorted_unique(
            self.required_substructures.iter().map(String::as_str),
            "grammar required substructures",
        )?;
        validate_sorted_unique(
            self.extraction_source_reaction_ids
                .iter()
                .map(String::as_str),
            "grammar source reaction IDs",
        )?;
        validate_sorted_unique(
            self.extraction_source_dataset_ids
                .iter()
                .map(String::as_str),
            "grammar source dataset IDs",
        )?;
        validate_sorted_unique(
            self.extraction_partition_component_ids
                .iter()
                .map(String::as_str),
            "grammar source component IDs",
        )?;
        if self.changed_atoms.is_empty()
            || self
                .changed_atoms
                .windows(2)
                .any(|atoms| atoms[0] >= atoms[1])
            || self
                .changed_bonds
                .windows(2)
                .any(|bonds| bond_change_sort_key(&bonds[0]) >= bond_change_sort_key(&bonds[1]))
            || self.changed_bonds.iter().any(|bond| {
                bond.atom_map_a >= bond.atom_map_b
                    || self.changed_atoms.binary_search(&bond.atom_map_a).is_err()
                    || self.changed_atoms.binary_search(&bond.atom_map_b).is_err()
            })
        {
            return Err(CompoundV2Error::Invalid("grammar changed atoms or bonds"));
        }
        require_hash(&self.template_sha256)?;
        require_hash(&self.rule_jcs_sha256)?;
        let template_hash = sha256_bytes(self.canonical_reaction_smarts.as_bytes());
        if template_hash != self.template_sha256 {
            return Err(CompoundV2Error::Invalid("grammar template hash"));
        }
        let mut unsigned = self.clone();
        unsigned.rule_jcs_sha256.clear();
        if jcs_sha256(&unsigned)? != self.rule_jcs_sha256 {
            return Err(CompoundV2Error::Invalid("grammar rule self-hash"));
        }
        Ok(())
    }
}

fn bond_change_sort_key(
    bond: &OrdBondChangeV1,
) -> (
    u8,
    u32,
    u32,
    Option<&str>,
    Option<&str>,
    Option<&str>,
    Option<&str>,
) {
    let kind = match bond.kind {
        OrdBondChangeKindV1::Addition => 0,
        OrdBondChangeKindV1::Deletion => 1,
        OrdBondChangeKindV1::OrderChange => 2,
        OrdBondChangeKindV1::StereoChange => 3,
    };
    (
        kind,
        bond.atom_map_a,
        bond.atom_map_b,
        bond.before_order.as_deref(),
        bond.after_order.as_deref(),
        bond.before_stereo.as_deref(),
        bond.after_stereo.as_deref(),
    )
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct ReactionGrammarCorpusV1 {
    pub schema: String,
    pub schema_identity: OrdSchemaIdentityV1,
    pub split_sha256: String,
    pub source_complete_tree_sha256: String,
    pub license: String,
    pub rules: Vec<ReactionGrammarRuleV1>,
    pub corpus_jcs_sha256: String,
}

impl ReactionGrammarCorpusV1 {
    pub fn seal_self_hash(&mut self) -> Result<(), CompoundV2Error> {
        for rule in &mut self.rules {
            rule.seal_self_hash()?;
        }
        self.rules.sort_by(|left, right| {
            (&left.family, &left.template_sha256, &left.rule_jcs_sha256).cmp(&(
                &right.family,
                &right.template_sha256,
                &right.rule_jcs_sha256,
            ))
        });
        self.corpus_jcs_sha256.clear();
        self.corpus_jcs_sha256 = jcs_sha256(self)?;
        self.validate()
    }

    pub fn validate(&self) -> Result<(), CompoundV2Error> {
        if self.schema != REACTION_GRAMMAR_CORPUS_SCHEMA
            || self.license != "CC-BY-SA-4.0"
            || self.rules.len() < 2
        {
            return Err(CompoundV2Error::Invalid("grammar corpus"));
        }
        self.schema_identity.validate()?;
        require_hash(&self.split_sha256)?;
        require_hash(&self.source_complete_tree_sha256)?;
        require_hash(&self.corpus_jcs_sha256)?;
        let mut rule_hashes = BTreeSet::new();
        let mut template_hashes = BTreeSet::new();
        let mut families = BTreeSet::new();
        for (index, rule) in self.rules.iter().enumerate() {
            rule.validate()?;
            if !rule_hashes.insert(rule.rule_jcs_sha256.as_str())
                || !template_hashes.insert(rule.template_sha256.as_str())
                || index > 0
                    && (
                        &self.rules[index - 1].family,
                        &self.rules[index - 1].template_sha256,
                        &self.rules[index - 1].rule_jcs_sha256,
                    ) >= (&rule.family, &rule.template_sha256, &rule.rule_jcs_sha256)
            {
                return Err(CompoundV2Error::Invalid("duplicate grammar rule"));
            }
            families.insert(rule.family.as_str());
        }
        if !REQUIRED_FAMILIES
            .iter()
            .all(|family| families.contains(family))
        {
            return Err(CompoundV2Error::Invalid("missing campaign grammar family"));
        }
        let mut unsigned = self.clone();
        unsigned.corpus_jcs_sha256.clear();
        if jcs_sha256(&unsigned)? != self.corpus_jcs_sha256 {
            return Err(CompoundV2Error::Invalid("grammar corpus self-hash"));
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct MethodCardV1 {
    pub module_id: String,
    pub method_status: String,
    pub method_version: String,
    pub source_identity: String,
    pub applicability_boundary: String,
    pub missing_evidence: Vec<String>,
    pub non_acceptance_reason: Option<String>,
    pub actual_authority: String,
    pub lock_path: String,
    pub lock_hash: String,
    pub lock_file_sha256: String,
}

impl MethodCardV1 {
    pub fn validate(&self) -> Result<(), CompoundV2Error> {
        if !REQUIRED_MODULES.contains(&self.module_id.as_str())
            || self.method_version.trim().is_empty()
            || self.source_identity.trim().is_empty()
            || self.applicability_boundary.trim().is_empty()
            || self.actual_authority != "AUDIT_ONLY"
            || !matches!(
                self.method_status.as_str(),
                "EVALUATION_LOCKED" | "AUDIT_ONLY" | "DEFERRED" | "SHADOW" | "EXCLUDED"
            )
        {
            return Err(CompoundV2Error::Invalid("method card"));
        }
        require_safe_path(&self.lock_path)?;
        require_hash(&self.lock_hash)?;
        require_hash(&self.lock_file_sha256)?;
        if matches!(
            self.method_status.as_str(),
            "DEFERRED" | "SHADOW" | "EXCLUDED"
        ) && (self.missing_evidence.is_empty()
            || self
                .non_acceptance_reason
                .as_deref()
                .is_none_or(str::is_empty))
        {
            return Err(CompoundV2Error::Invalid("deferred method lock"));
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct MethodLockPayloadV1 {
    pub schema: String,
    pub module_id: String,
    pub method_status: String,
    pub method_version: String,
    pub source_identity: String,
    pub applicability_boundary: String,
    pub missing_evidence: Vec<String>,
    pub non_acceptance_reason: Option<String>,
    pub actual_authority: String,
    pub lock_hash: String,
}

impl MethodLockPayloadV1 {
    pub fn seal_self_hash(&mut self) -> Result<(), CompoundV2Error> {
        self.lock_hash.clear();
        self.lock_hash = jcs_sha256(self)?;
        self.validate()
    }

    pub fn validate(&self) -> Result<(), CompoundV2Error> {
        if self.schema != "amphora.method-lock.v1" {
            return Err(CompoundV2Error::Invalid("method lock schema"));
        }
        MethodCardV1 {
            module_id: self.module_id.clone(),
            method_status: self.method_status.clone(),
            method_version: self.method_version.clone(),
            source_identity: self.source_identity.clone(),
            applicability_boundary: self.applicability_boundary.clone(),
            missing_evidence: self.missing_evidence.clone(),
            non_acceptance_reason: self.non_acceptance_reason.clone(),
            actual_authority: self.actual_authority.clone(),
            lock_path: "method-locks/validation.json".into(),
            lock_hash: self.lock_hash.clone(),
            lock_file_sha256: "a".repeat(64),
        }
        .validate()?;
        let mut unsigned = self.clone();
        unsigned.lock_hash.clear();
        if jcs_sha256(&unsigned)? != self.lock_hash {
            return Err(CompoundV2Error::Invalid("method lock self-hash"));
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct MethodRegistryV1 {
    pub schema: String,
    pub snapshot_id: String,
    pub all_modules: Vec<String>,
    pub modules: BTreeMap<String, MethodCardV1>,
    pub registry_hash: String,
}

impl MethodRegistryV1 {
    pub fn seal_self_hash(&mut self) -> Result<(), CompoundV2Error> {
        self.registry_hash.clear();
        self.registry_hash = jcs_sha256(self)?;
        self.validate()
    }

    pub fn validate(&self) -> Result<(), CompoundV2Error> {
        if self.schema != METHOD_REGISTRY_SCHEMA || self.snapshot_id.trim().is_empty() {
            return Err(CompoundV2Error::Invalid("method registry"));
        }
        let expected = REQUIRED_MODULES.into_iter().collect::<BTreeSet<_>>();
        let listed = self
            .all_modules
            .iter()
            .map(String::as_str)
            .collect::<BTreeSet<_>>();
        let keyed = self
            .modules
            .keys()
            .map(String::as_str)
            .collect::<BTreeSet<_>>();
        if self.all_modules.len() != REQUIRED_MODULES.len()
            || listed != expected
            || keyed != expected
        {
            return Err(CompoundV2Error::Invalid("method registry module set"));
        }
        for (module_id, card) in &self.modules {
            card.validate()?;
            if card.module_id != *module_id {
                return Err(CompoundV2Error::Invalid("method registry module binding"));
            }
        }
        require_hash(&self.registry_hash)?;
        let mut unsigned = self.clone();
        unsigned.registry_hash.clear();
        if jcs_sha256(&unsigned)? != self.registry_hash {
            return Err(CompoundV2Error::Invalid("method registry self-hash"));
        }
        Ok(())
    }

    pub fn verify_files(&self, root: &Path) -> Result<(), CompoundV2Error> {
        self.validate()?;
        for card in self.modules.values() {
            let binding = FileArtifactBindingV1 {
                path: card.lock_path.clone(),
                sha256: card.lock_file_sha256.clone(),
            };
            binding.verify(root)?;
            let bytes = fs::read(root.join(&card.lock_path))?;
            let value = crate::parse_json_strict(&bytes)
                .map_err(|_| CompoundV2Error::Invalid("method lock JSON"))?;
            let payload: MethodLockPayloadV1 = serde_json::from_value(value)?;
            payload.validate()?;
            if bytes != jcs_bytes(&payload)?
                || payload.module_id != card.module_id
                || payload.method_status != card.method_status
                || payload.method_version != card.method_version
                || payload.source_identity != card.source_identity
                || payload.applicability_boundary != card.applicability_boundary
                || payload.missing_evidence != card.missing_evidence
                || payload.non_acceptance_reason != card.non_acceptance_reason
                || payload.actual_authority != card.actual_authority
                || payload.lock_hash != card.lock_hash
            {
                return Err(CompoundV2Error::Invalid("method lock binding"));
            }
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct MethodBenchmarkLockV1 {
    pub schema: String,
    pub lock_id: String,
    pub module_id: String,
    pub artifact: FileArtifactBindingV1,
    pub accepted: bool,
    pub authority: String,
}

impl MethodBenchmarkLockV1 {
    pub fn validate(&self) -> Result<(), CompoundV2Error> {
        if self.schema != METHOD_BENCHMARK_LOCK_SCHEMA
            || self.lock_id.trim().is_empty()
            || !REQUIRED_MODULES.contains(&self.module_id.as_str())
            || self.authority != "AUDIT_ONLY"
        {
            return Err(CompoundV2Error::Invalid("benchmark lock"));
        }
        self.artifact.validate()
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct CampaignArtifactBindingsV1 {
    pub ord_complete_tree: FileArtifactBindingV1,
    pub ord_schema_identity: FileArtifactBindingV1,
    pub ord_decoded_reactions: FileArtifactBindingV1,
    pub ord_exclusions: FileArtifactBindingV1,
    pub ord_split: FileArtifactBindingV1,
    pub ord_grammar: FileArtifactBindingV1,
    pub ord_rights_receipt: FileArtifactBindingV1,
    pub portable_toolchain_manifest: FileArtifactBindingV1,
    pub optimized_toolchain_manifest: FileArtifactBindingV1,
    pub reactive_group_ontology: FileArtifactBindingV1,
    pub method_registry: FileArtifactBindingV1,
    pub benchmark_lock_set: FileArtifactBindingV1,
    pub execution_profiles: Vec<FileArtifactBindingV1>,
}

impl CampaignArtifactBindingsV1 {
    fn all(&self) -> impl Iterator<Item = &FileArtifactBindingV1> {
        [
            &self.ord_complete_tree,
            &self.ord_schema_identity,
            &self.ord_decoded_reactions,
            &self.ord_exclusions,
            &self.ord_split,
            &self.ord_grammar,
            &self.ord_rights_receipt,
            &self.portable_toolchain_manifest,
            &self.optimized_toolchain_manifest,
            &self.reactive_group_ontology,
            &self.method_registry,
            &self.benchmark_lock_set,
        ]
        .into_iter()
        .chain(self.execution_profiles.iter())
    }

    fn validate(&self) -> Result<(), CompoundV2Error> {
        if self.execution_profiles.is_empty() {
            return Err(CompoundV2Error::Invalid("campaign execution profiles"));
        }
        for binding in self.all() {
            binding.validate()?;
        }
        Ok(())
    }

    fn verify(&self, root: &Path) -> Result<(), CompoundV2Error> {
        self.validate()?;
        for binding in self.all() {
            binding.verify(root)?;
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct CompoundCampaignV2 {
    pub schema: String,
    pub campaign_id: String,
    pub deterministic_seed: u64,
    pub feedback_v3_catalog: FileArtifactBindingV1,
    pub feedback_v4_catalog: FileArtifactBindingV1,
    pub feedback_v5_catalog: FileArtifactBindingV1,
    pub artifacts: CampaignArtifactBindingsV1,
    pub generation_requests: Vec<CampaignGenerationRequestV1>,
    pub cohort_thresholds: CampaignCohortThresholdsV1,
    pub maximum_generation_attempts: usize,
    pub pairing_policy: CampaignPairingRuleV1,
    pub redteam_request_nonce: String,
    pub authorized_reviewer_key_id: String,
    pub evaluator_key_id: String,
    pub claim_locks: BTreeMap<String, bool>,
    pub classification: String,
    pub authority_ceiling: String,
    pub production_scientific_ranking_enabled: bool,
    pub manifest_jcs_sha256: String,
}

impl CompoundCampaignV2 {
    pub fn seal_self_hash(&mut self) -> Result<(), CompoundV2Error> {
        self.manifest_jcs_sha256.clear();
        self.manifest_jcs_sha256 = jcs_sha256(self)?;
        self.validate()
    }

    pub fn validate(&self) -> Result<(), CompoundV2Error> {
        if self.schema != COMPOUND_CAMPAIGN_SCHEMA_V2
            || self.campaign_id.trim().is_empty()
            || self.deterministic_seed == 0
            || self.maximum_generation_attempts < self.cohort_thresholds.unique_structures
            || self.generation_requests.is_empty()
            || self.generation_requests.len() > self.maximum_generation_attempts
            || self.cohort_thresholds.unique_structures < 24
            || self.cohort_thresholds.epoxide_bearing < 8
            || self.cohort_thresholds.reactive_amine_bearing < 8
            || self.cohort_thresholds.scaffold_pair_groups < 6
            || self.pairing_policy.method != "CANONICAL_HASH_ROLE_SCAFFOLD_STRATA"
            || self.pairing_policy.deterministic_tie_break != "SHA256_ASCENDING"
            || !self.pairing_policy.resin_mass_g.is_finite()
            || self.pairing_policy.resin_mass_g <= 0.0
            || !self.pairing_policy.equivalent_ratio.is_finite()
            || self.pairing_policy.equivalent_ratio <= 0.0
            || self.redteam_request_nonce.trim().is_empty()
            || self.authorized_reviewer_key_id.trim().is_empty()
            || self.evaluator_key_id.trim().is_empty()
            || self.authorized_reviewer_key_id == self.evaluator_key_id
            || self.classification != "LOCKED_INTERNAL"
            || self.authority_ceiling != "AUDIT_ONLY"
            || self.production_scientific_ranking_enabled
        {
            return Err(CompoundV2Error::Invalid("campaign manifest"));
        }
        for binding in [
            &self.feedback_v3_catalog,
            &self.feedback_v4_catalog,
            &self.feedback_v5_catalog,
        ] {
            binding.validate()?;
        }
        self.artifacts.validate()?;
        for lock in required_claim_locks() {
            if self.claim_locks.get(*lock) != Some(&true) {
                return Err(CompoundV2Error::Invalid("campaign claim locks"));
            }
        }
        let mut request_ids = BTreeSet::new();
        for request in &self.generation_requests {
            if request.request_id.trim().is_empty()
                || !request_ids.insert(request.request_id.as_str())
                || request.parent_structures.is_empty()
                || !REQUIRED_FAMILIES.contains(&request.reaction_family.as_str())
                || !matches!(request.requested_role.as_str(), "resin" | "hardener")
            {
                return Err(CompoundV2Error::Invalid("campaign generation request"));
            }
        }
        require_hash(&self.manifest_jcs_sha256)?;
        let mut unsigned = self.clone();
        unsigned.manifest_jcs_sha256.clear();
        if jcs_sha256(&unsigned)? != self.manifest_jcs_sha256 {
            return Err(CompoundV2Error::Invalid("campaign manifest self-hash"));
        }
        Ok(())
    }

    pub fn verify_bound_files(&self, root: &Path) -> Result<(), CompoundV2Error> {
        self.validate()?;
        for binding in [
            &self.feedback_v3_catalog,
            &self.feedback_v4_catalog,
            &self.feedback_v5_catalog,
        ] {
            binding.verify(root)?;
        }
        self.artifacts.verify(root)
    }

    pub fn verify_evaluator_envelope(
        &self,
        envelope: &DsseEnvelope,
        trust_store: &TrustStore,
    ) -> Result<(), CompoundV2Error> {
        self.validate()?;
        if envelope.payload_type != CAMPAIGN_MANIFEST_PAYLOAD_TYPE {
            return Err(CompoundV2Error::Invalid("campaign DSSE payload type"));
        }
        let verified = verify_dsse(envelope, trust_store)?;
        if verified.key_id != self.evaluator_key_id || verified.payload != jcs_bytes(self)? {
            return Err(CompoundV2Error::Invalid("campaign DSSE payload bytes"));
        }
        Ok(())
    }

    pub fn authorize_grammar(
        &self,
        envelope: &DsseEnvelope,
        trust_store: &TrustStore,
        grammar: &ReactionGrammarCorpusV1,
        split: &ReactionSplitManifestV1,
        rights_receipt_sha256: &str,
        toolchain_manifest_sha256: &str,
        candidate_supplied_source_refs: &[String],
    ) -> Result<AuthorizedCampaignGrammarV1, CompoundV2Error> {
        self.verify_evaluator_envelope(envelope, trust_store)?;
        grammar.validate()?;
        split.validate()?;
        let grammar_artifact_sha256 = jcs_sha256(grammar)?;
        let split_artifact_sha256 = jcs_sha256(split)?;
        let schema_artifact_sha256 = jcs_sha256(&grammar.schema_identity)?;
        if !candidate_supplied_source_refs.is_empty()
            || grammar_artifact_sha256 != self.artifacts.ord_grammar.sha256
            || split_artifact_sha256 != self.artifacts.ord_split.sha256
            || schema_artifact_sha256 != self.artifacts.ord_schema_identity.sha256
            || grammar.split_sha256 != split_artifact_sha256
            || rights_receipt_sha256 != self.artifacts.ord_rights_receipt.sha256
            || ![
                self.artifacts.portable_toolchain_manifest.sha256.as_str(),
                self.artifacts.optimized_toolchain_manifest.sha256.as_str(),
            ]
            .contains(&toolchain_manifest_sha256)
            || grammar.source_complete_tree_sha256 != self.artifacts.ord_complete_tree.sha256
            || self.authority_ceiling != "AUDIT_ONLY"
        {
            return Err(CompoundV2Error::Invalid("campaign grammar authorization"));
        }
        let extraction_ids = split
            .extraction_reaction_ids
            .iter()
            .map(String::as_str)
            .collect::<BTreeSet<_>>();
        let extraction_components = split
            .assignments
            .iter()
            .filter_map(|(id, partition)| {
                (*partition == ReactionSplitComponentV1::Extraction).then_some(id.as_str())
            })
            .collect::<BTreeSet<_>>();
        for rule in &grammar.rules {
            if rule
                .extraction_source_reaction_ids
                .iter()
                .any(|id| !extraction_ids.contains(id.as_str()))
                || rule
                    .extraction_partition_component_ids
                    .iter()
                    .any(|id| !extraction_components.contains(id.as_str()))
            {
                return Err(CompoundV2Error::Invalid("grammar source partition"));
            }
        }
        Ok(AuthorizedCampaignGrammarV1 {
            campaign_id: self.campaign_id.clone(),
            grammar_sha256: grammar_artifact_sha256,
            authority: "AUDIT_ONLY".into(),
            rules: grammar.rules.clone(),
        })
    }
}

#[derive(Debug, Clone)]
pub struct AuthorizedCampaignGrammarV1 {
    campaign_id: String,
    grammar_sha256: String,
    authority: String,
    rules: Vec<ReactionGrammarRuleV1>,
}

impl AuthorizedCampaignGrammarV1 {
    pub fn campaign_id(&self) -> &str {
        &self.campaign_id
    }

    pub fn grammar_sha256(&self) -> &str {
        &self.grammar_sha256
    }

    pub fn authority(&self) -> &str {
        &self.authority
    }

    pub fn rules(&self) -> &[ReactionGrammarRuleV1] {
        &self.rules
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum ModuleOutcomeStatusV1 {
    Pass,
    Fail,
    Abstain,
    NotApplicable,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum ReportLaneV1 {
    Trust,
    Chemistry,
    FormulationPhysics,
    Transfer,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct MeasuredScalarV1 {
    pub value: f64,
    pub unit: String,
    pub measurement_type: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct ModuleOutcomeV1 {
    pub module_id: String,
    pub lane: ReportLaneV1,
    pub status: ModuleOutcomeStatusV1,
    pub reason_code: String,
    pub scalar: Option<MeasuredScalarV1>,
    pub envelope_sha256: String,
    pub result_sha256: String,
}

impl ModuleOutcomeV1 {
    pub fn validate(&self) -> Result<(), CompoundV2Error> {
        if !REQUIRED_MODULES.contains(&self.module_id.as_str())
            || self.reason_code.trim().is_empty()
            || self.lane != lane_for_module(&self.module_id)?
        {
            return Err(CompoundV2Error::Invalid("module outcome"));
        }
        require_hash(&self.envelope_sha256)?;
        require_hash(&self.result_sha256)?;
        if let Some(scalar) = &self.scalar {
            if !scalar.value.is_finite()
                || scalar.unit.trim().is_empty()
                || scalar.measurement_type.trim().is_empty()
            {
                return Err(CompoundV2Error::Invalid("module report scalar"));
            }
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct StructureRenderBindingV1 {
    pub canonical_structure_sha256: String,
    pub highlighted_atom_indices: Vec<u32>,
    pub svg: FileArtifactBindingV1,
    pub pdf: FileArtifactBindingV1,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct CompoundPairContextV1 {
    pub pair_id: String,
    pub pair_sha256: String,
    pub resin_proposal_id: String,
    pub hardener_proposal_id: String,
    pub resin_structure_sha256: String,
    pub hardener_structure_sha256: String,
    pub eew: MeasuredScalarV1,
    pub ahew: MeasuredScalarV1,
    pub equivalents: MeasuredScalarV1,
    pub hardener_phr: MeasuredScalarV1,
    pub resin_mass: MeasuredScalarV1,
    pub hardener_mass: MeasuredScalarV1,
    pub total_mass: MeasuredScalarV1,
    pub balance_sha256: String,
    pub cro_packet: FileArtifactBindingV1,
}

impl CompoundPairContextV1 {
    pub fn validate(&self) -> Result<(), CompoundV2Error> {
        if self.pair_id.trim().is_empty()
            || self.resin_proposal_id.trim().is_empty()
            || self.hardener_proposal_id.trim().is_empty()
        {
            return Err(CompoundV2Error::Invalid("pair context"));
        }
        for hash in [
            &self.pair_sha256,
            &self.resin_structure_sha256,
            &self.hardener_structure_sha256,
            &self.balance_sha256,
        ] {
            require_hash(hash)?;
        }
        for scalar in [
            &self.eew,
            &self.ahew,
            &self.equivalents,
            &self.hardener_phr,
            &self.resin_mass,
            &self.hardener_mass,
            &self.total_mass,
        ] {
            if !scalar.value.is_finite()
                || scalar.value <= 0.0
                || scalar.unit.trim().is_empty()
                || scalar.measurement_type.trim().is_empty()
            {
                return Err(CompoundV2Error::Invalid("pair scalar"));
            }
        }
        self.cro_packet.validate()
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct CompoundCardV1 {
    pub schema: String,
    pub proposal_id: String,
    pub proposal_name: String,
    pub role: String,
    pub canonical_isomeric_smiles: String,
    pub canonical_structure_sha256: String,
    pub inchi_key: String,
    pub formula: String,
    pub molecular_mass: MeasuredScalarV1,
    pub oxirane_count: u32,
    pub reactive_amine_h_count: u32,
    pub scaffold: String,
    pub scaffold_sha256: String,
    pub ord_reaction_ids: Vec<String>,
    pub ord_dataset_ids: Vec<String>,
    pub pair_context: CompoundPairContextV1,
    pub structure_render: StructureRenderBindingV1,
    pub module_outcomes: Vec<ModuleOutcomeV1>,
    pub final_disposition: String,
    pub unmade: bool,
    pub claim_locks: BTreeMap<String, bool>,
    pub authority_ceiling: String,
}

impl CompoundCardV1 {
    pub fn validate(&self) -> Result<(), CompoundV2Error> {
        if self.schema != COMPOUND_CARD_SCHEMA
            || self.proposal_id.trim().is_empty()
            || self.proposal_name.trim().is_empty()
            || !matches!(self.role.as_str(), "resin" | "hardener")
            || self.canonical_isomeric_smiles.trim().is_empty()
            || self.inchi_key.trim().is_empty()
            || self.formula.trim().is_empty()
            || self.scaffold.trim().is_empty()
            || self.ord_reaction_ids.is_empty()
            || self.ord_dataset_ids.is_empty()
            || self.final_disposition.trim().is_empty()
            || !self.unmade
            || self.authority_ceiling != "AUDIT_ONLY"
            || !self.molecular_mass.value.is_finite()
            || self.molecular_mass.value <= 0.0
            || self.molecular_mass.unit != "g/mol"
        {
            return Err(CompoundV2Error::Invalid("compound card"));
        }
        require_hash(&self.canonical_structure_sha256)?;
        require_hash(&self.scaffold_sha256)?;
        if self.structure_render.canonical_structure_sha256 != self.canonical_structure_sha256 {
            return Err(CompoundV2Error::Invalid("card structure render binding"));
        }
        self.structure_render.svg.validate()?;
        self.structure_render.pdf.validate()?;
        self.pair_context.validate()?;
        for lock in required_claim_locks() {
            if self.claim_locks.get(*lock) != Some(&true) {
                return Err(CompoundV2Error::Invalid("card claim locks"));
            }
        }
        let mut modules = BTreeSet::new();
        for outcome in &self.module_outcomes {
            outcome.validate()?;
            if !modules.insert(outcome.module_id.as_str()) {
                return Err(CompoundV2Error::Invalid("duplicate card module outcome"));
            }
        }
        let expected = REQUIRED_MODULES.into_iter().collect::<BTreeSet<_>>();
        if modules != expected {
            return Err(CompoundV2Error::Invalid("card module outcome set"));
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum CampaignAttemptKindV1 {
    Accepted,
    Rejected,
    NegativeResult,
    Duplicate,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct CampaignAttemptV1 {
    pub ordinal: u64,
    pub request_id: String,
    pub kind: CampaignAttemptKindV1,
    pub reason_code: String,
    pub canonical_structure_sha256: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct CompoundCampaignResultV2 {
    pub schema: String,
    pub campaign_id: String,
    pub campaign_manifest_jcs_sha256: String,
    pub raw_stage_counts: CampaignStageCountsV1,
    pub attempts: Vec<CampaignAttemptV1>,
    pub valid_generated_compounds: Vec<Value>,
    pub pair_calculations: Vec<CompoundPairContextV1>,
    pub cro_packets: Vec<Value>,
    pub cards: Vec<CompoundCardV1>,
    pub module_envelope_hashes: BTreeMap<String, Vec<String>>,
    pub scientific_replay_sha256: String,
    pub claim_locks: BTreeMap<String, bool>,
    pub authority_ceiling: String,
    pub production_scientific_ranking_enabled: bool,
}

impl CompoundCampaignResultV2 {
    pub fn seal_scientific_replay_hash(
        &mut self,
        campaign: &CompoundCampaignV2,
    ) -> Result<(), CompoundV2Error> {
        self.scientific_replay_sha256.clear();
        self.scientific_replay_sha256 = jcs_sha256(self)?;
        self.validate(campaign)
    }

    pub fn validate(&self, campaign: &CompoundCampaignV2) -> Result<(), CompoundV2Error> {
        campaign.validate()?;
        if self.schema != COMPOUND_CAMPAIGN_RESULT_SCHEMA_V2
            || self.campaign_id != campaign.campaign_id
            || self.campaign_manifest_jcs_sha256 != campaign.manifest_jcs_sha256
            || self.attempts.len() != self.raw_stage_counts.generation_attempts
            || self.valid_generated_compounds.len() != self.raw_stage_counts.unique_valid_structures
            || self.pair_calculations.len() != 12
            || self.cro_packets.len() != 12
            || self.cards.len() != 20
            || self.authority_ceiling != "AUDIT_ONLY"
            || self.production_scientific_ranking_enabled
        {
            return Err(CompoundV2Error::Invalid("campaign result"));
        }
        let ordinals = self
            .attempts
            .iter()
            .map(|row| row.ordinal)
            .collect::<BTreeSet<_>>();
        if ordinals.len() != self.attempts.len()
            || self
                .attempts
                .iter()
                .any(|row| row.request_id.trim().is_empty() || row.reason_code.trim().is_empty())
        {
            return Err(CompoundV2Error::Invalid("campaign attempts"));
        }
        for row in &self.attempts {
            if let Some(hash) = &row.canonical_structure_sha256 {
                require_hash(hash)?;
            }
        }
        for pair in &self.pair_calculations {
            pair.validate()?;
        }
        let mut proposal_ids = BTreeSet::new();
        for card in &self.cards {
            card.validate()?;
            if !proposal_ids.insert(card.proposal_id.as_str()) {
                return Err(CompoundV2Error::Invalid("duplicate compound card"));
            }
        }
        for module in REQUIRED_MODULES {
            let hashes = self
                .module_envelope_hashes
                .get(module)
                .ok_or(CompoundV2Error::Invalid("result module envelopes"))?;
            if hashes.is_empty() {
                return Err(CompoundV2Error::Invalid("result module envelopes"));
            }
            for hash in hashes {
                require_hash(hash)?;
            }
        }
        if self.module_envelope_hashes.len() != REQUIRED_MODULES.len() {
            return Err(CompoundV2Error::Invalid("result module envelope set"));
        }
        for lock in required_claim_locks() {
            if self.claim_locks.get(*lock) != Some(&true) {
                return Err(CompoundV2Error::Invalid("result claim locks"));
            }
        }
        require_hash(&self.scientific_replay_sha256)?;
        let mut unsigned = self.clone();
        unsigned.scientific_replay_sha256.clear();
        if jcs_sha256(&unsigned)? != self.scientific_replay_sha256 {
            return Err(CompoundV2Error::Invalid("scientific replay hash"));
        }
        let value = serde_json::to_value(self)?;
        if contains_forbidden_authority(&value) {
            return Err(CompoundV2Error::Invalid("forbidden result authority"));
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct CampaignRateRepeatV1 {
    pub repeat: u32,
    pub numerator: u64,
    pub denominator_ns: u64,
    pub rate_per_second: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct CampaignExecutionReceiptV1 {
    pub schema: String,
    pub campaign_id: String,
    pub hardware_identity: String,
    pub os_identity: String,
    pub kernel_identity: String,
    pub cpu_affinity: String,
    pub frequency_policy: String,
    pub host_load: String,
    pub toolchain_profile_sha256: String,
    pub workers: usize,
    pub batch_size: usize,
    pub cache_state: String,
    pub os_page_cache_evicted: bool,
    pub workload_name: String,
    pub workload_numerator: u64,
    pub workload_denominator_ns: u64,
    pub attempts: u64,
    pub accepts: u64,
    pub rejects: u64,
    pub duplicates: u64,
    pub wall_time_ns: u64,
    pub cpu_time_ns: u64,
    pub cpu_utilization_fraction: f64,
    pub peak_rss_bytes: u64,
    pub swap_in_before: u64,
    pub swap_in_after: u64,
    pub swap_out_before: u64,
    pub swap_out_after: u64,
    pub repeats: Vec<CampaignRateRepeatV1>,
    pub rate_ci95_low: f64,
    pub rate_ci95_high: f64,
    pub scientific_result_sha256: String,
    pub receipt_jcs_sha256: String,
}

impl CampaignExecutionReceiptV1 {
    pub fn seal_self_hash(&mut self) -> Result<(), CompoundV2Error> {
        self.receipt_jcs_sha256.clear();
        self.receipt_jcs_sha256 = jcs_sha256(self)?;
        self.validate()
    }

    pub fn validate(&self) -> Result<(), CompoundV2Error> {
        if self.schema != CAMPAIGN_EXECUTION_RECEIPT_SCHEMA
            || self.campaign_id.trim().is_empty()
            || self.hardware_identity.trim().is_empty()
            || self.os_identity.trim().is_empty()
            || self.kernel_identity.trim().is_empty()
            || self.cpu_affinity.trim().is_empty()
            || self.frequency_policy.trim().is_empty()
            || self.host_load.trim().is_empty()
            || self.workers == 0
            || self.batch_size == 0
            || !matches!(self.cache_state.as_str(), "COLD" | "APPLICATION_WARM")
            || self.workload_name.trim().is_empty()
            || self.workload_numerator == 0
            || self.workload_denominator_ns == 0
            || self.wall_time_ns == 0
            || self.cpu_time_ns == 0
            || !self.cpu_utilization_fraction.is_finite()
            || self.cpu_utilization_fraction < 0.0
            || self.peak_rss_bytes == 0
            || self.peak_rss_bytes >= 96 * 1024 * 1024 * 1024
            || self.swap_in_before != self.swap_in_after
            || self.swap_out_before != self.swap_out_after
            || self.repeats.len() != 5
            || !self.rate_ci95_low.is_finite()
            || !self.rate_ci95_high.is_finite()
            || self.rate_ci95_low > self.rate_ci95_high
            || self.attempts != self.accepts + self.rejects + self.duplicates
        {
            return Err(CompoundV2Error::Invalid("execution receipt"));
        }
        require_hash(&self.toolchain_profile_sha256)?;
        require_hash(&self.scientific_result_sha256)?;
        require_hash(&self.receipt_jcs_sha256)?;
        for (index, repeat) in self.repeats.iter().enumerate() {
            if repeat.repeat as usize != index + 1
                || repeat.numerator == 0
                || repeat.denominator_ns == 0
                || !repeat.rate_per_second.is_finite()
                || repeat.rate_per_second <= 0.0
            {
                return Err(CompoundV2Error::Invalid("execution repeat"));
            }
        }
        let mut unsigned = self.clone();
        unsigned.receipt_jcs_sha256.clear();
        if jcs_sha256(&unsigned)? != self.receipt_jcs_sha256 {
            return Err(CompoundV2Error::Invalid("execution receipt self-hash"));
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct CampaignIndependentReviewReceiptV1 {
    pub schema: String,
    pub campaign_manifest_sha256: String,
    pub campaign_result_sha256: String,
    pub portable_toolchain_sha256: String,
    pub optimized_toolchain_sha256: String,
    pub grammar_sha256: String,
    pub redteam_summary_sha256: String,
    pub clean_replay_sha256: String,
    pub report_input_sha256: String,
    pub reviewer_implementation_sha256: String,
    pub reviewer_key_id: String,
    pub authority: String,
}

impl CampaignIndependentReviewReceiptV1 {
    pub fn validate(&self) -> Result<(), CompoundV2Error> {
        if self.schema != CAMPAIGN_INDEPENDENT_REVIEW_RECEIPT_SCHEMA
            || self.reviewer_key_id.trim().is_empty()
            || self.authority != "AUDIT_ONLY"
        {
            return Err(CompoundV2Error::Invalid("independent review receipt"));
        }
        for hash in [
            &self.campaign_manifest_sha256,
            &self.campaign_result_sha256,
            &self.portable_toolchain_sha256,
            &self.optimized_toolchain_sha256,
            &self.grammar_sha256,
            &self.redteam_summary_sha256,
            &self.clean_replay_sha256,
            &self.report_input_sha256,
            &self.reviewer_implementation_sha256,
        ] {
            require_hash(hash)?;
        }
        Ok(())
    }
}

fn manifest_mentions_python(manifest: &ToolchainManifestV1) -> bool {
    let mentions = |value: &str| value.to_ascii_lowercase().contains("python");
    manifest
        .dependencies
        .iter()
        .any(|row| mentions(&row.name) || mentions(&row.version) || mentions(&row.source_identity))
        || manifest
            .installed_files
            .iter()
            .any(|row| mentions(&row.path))
        || manifest.shared_libraries.iter().any(|row| {
            mentions(&row.path)
                || mentions(&row.soname)
                || row.needed.iter().any(|value| mentions(value))
                || row
                    .resolved_runtime_closure
                    .iter()
                    .any(|value| mentions(value))
        })
        || manifest
            .cpp_tests
            .command
            .iter()
            .any(|value| mentions(value))
        || manifest.compile_flags.iter().any(|value| mentions(value))
        || manifest.link_flags.iter().any(|value| mentions(value))
        || [
            &manifest.compiler,
            &manifest.linker,
            &manifest.cmake,
            &manifest.ninja,
            &manifest.install_prefix,
            &manifest.spdx_3_sbom.path,
            &manifest.slsa_v1_2_provenance.path,
        ]
        .iter()
        .any(|value| mentions(value))
}

fn inventory_install_tree(root: &Path) -> Result<Vec<InstalledFileV1>, CompoundV2Error> {
    let mut pending = vec![root.to_path_buf()];
    let mut files = Vec::new();
    while let Some(directory) = pending.pop() {
        for entry in fs::read_dir(&directory)? {
            let entry = entry?;
            let path = entry.path();
            let metadata = fs::symlink_metadata(&path)?;
            if metadata.file_type().is_symlink() {
                return Err(CompoundV2Error::Invalid("symlink in installed tree"));
            }
            if metadata.is_dir() {
                pending.push(path);
                continue;
            }
            if !metadata.file_type().is_file() {
                return Err(CompoundV2Error::Invalid(
                    "non-regular file in installed tree",
                ));
            }
            let relative = path
                .strip_prefix(root)
                .map_err(|_| CompoundV2Error::Invalid("installed path prefix"))?
                .to_str()
                .ok_or(CompoundV2Error::Invalid("installed path encoding"))?
                .replace('\\', "/");
            #[cfg(unix)]
            let mode = {
                use std::os::unix::fs::PermissionsExt;
                metadata.permissions().mode() & 0o7777
            };
            #[cfg(not(unix))]
            let mode = 0;
            files.push(InstalledFileV1 {
                path: relative,
                size: metadata.len(),
                mode,
                sha256: sha256_bytes(&fs::read(&path)?),
            });
        }
    }
    files.sort_by(|left, right| left.path.cmp(&right.path));
    Ok(files)
}

fn verify_elf_dynamic_section(
    path: &Path,
    expected: &SharedLibraryV1,
) -> Result<(), CompoundV2Error> {
    let output = Command::new("readelf").arg("-d").arg(path).output()?;
    if !output.status.success() {
        return Err(CompoundV2Error::Invalid("readelf dynamic inspection"));
    }
    let stdout = String::from_utf8(output.stdout)
        .map_err(|_| CompoundV2Error::Invalid("readelf output encoding"))?;
    let mut soname = None;
    let mut needed = Vec::new();
    let mut runpath = None;
    let mut rpath = None;
    for line in stdout.lines() {
        let extract = || {
            line.split_once('[')
                .and_then(|(_, tail)| tail.split_once(']'))
                .map(|(value, _)| value.to_owned())
        };
        if line.contains("(SONAME)") {
            soname = extract();
        } else if line.contains("(NEEDED)") {
            if let Some(value) = extract() {
                needed.push(value);
            }
        } else if line.contains("(RUNPATH)") {
            runpath = extract();
        } else if line.contains("(RPATH)") {
            rpath = extract();
        }
    }
    needed.sort();
    let mut expected_needed = expected.needed.clone();
    expected_needed.sort();
    if soname.as_deref() != Some(expected.soname.as_str())
        || needed != expected_needed
        || runpath != expected.runpath
        || rpath != expected.rpath
    {
        return Err(CompoundV2Error::Invalid("ELF ABI metadata mismatch"));
    }
    let closure_names = expected
        .resolved_runtime_closure
        .iter()
        .filter_map(|value| Path::new(value).file_name().and_then(|name| name.to_str()))
        .collect::<BTreeSet<_>>();
    if expected
        .needed
        .iter()
        .any(|name| !closure_names.contains(name.as_str()))
    {
        return Err(CompoundV2Error::Invalid("unresolved ELF dependency"));
    }
    Ok(())
}

fn verify_runtime_cpu_features(requirements: &[String]) -> Result<(), CompoundV2Error> {
    let cpuinfo = fs::read_to_string("/proc/cpuinfo")?;
    let features = cpuinfo
        .lines()
        .find_map(|line| {
            let (name, value) = line.split_once(':')?;
            (name.trim() == "flags").then_some(value.split_whitespace().collect::<BTreeSet<_>>())
        })
        .ok_or(CompoundV2Error::Invalid("runtime CPU feature inventory"))?;
    for required in ["avx2", "fma", "bmi2", "popcnt"] {
        if requirements.iter().any(|value| value == required) && !features.contains(required) {
            return Err(CompoundV2Error::Invalid("runtime CPU is incompatible"));
        }
    }
    Ok(())
}

fn installed_tree_hash(files: &[InstalledFileV1]) -> Result<String, CompoundV2Error> {
    #[derive(Serialize)]
    struct TreeRow<'a> {
        path: &'a str,
        size: u64,
        mode: u32,
        sha256: &'a str,
    }
    let rows = files
        .iter()
        .map(|row| TreeRow {
            path: &row.path,
            size: row.size,
            mode: row.mode,
            sha256: &row.sha256,
        })
        .collect::<Vec<_>>();
    Ok(jcs_sha256(&rows)?)
}

fn lane_for_module(module_id: &str) -> Result<ReportLaneV1, CompoundV2Error> {
    let lane = match module_id {
        "amphora-candidate-contract"
        | "amphora-source-ledger"
        | "amphora-evidence-intake-validator"
        | "amphora-model-card-authority"
        | "amphora-run-provenance"
        | "amphora-known-answer-benchmarks"
        | "amphora-redteam-audit"
        | "amphora-report-packager" => ReportLaneV1::Trust,
        "amphora-ingredient-library"
        | "amphora-molecule-design-gate"
        | "amphora-molecule-generator"
        | "amphora-molecule-novelty"
        | "amphora-molecule-property"
        | "amphora-molecule-role-ranker"
        | "amphora-ip-fto-guard"
        | "amphora-sourceability-ehs" => ReportLaneV1::Chemistry,
        "amphora-barrier-corrosion-score"
        | "amphora-cure-potlife-gate"
        | "amphora-design-rule-score"
        | "amphora-envelope-gates"
        | "amphora-formulation-arithmetic"
        | "amphora-formulation-universe"
        | "amphora-solvency-score"
        | "amphora-tolerance-robustness"
        | "amphora-viscosity-score"
        | "amphora-process-qc-twin"
        | "amphora-public-corrosion-benchmark" => ReportLaneV1::FormulationPhysics,
        "amphora-cro-protocol-packager" | "amphora-optimizer-orchestrator" => {
            ReportLaneV1::Transfer
        }
        _ => return Err(CompoundV2Error::Invalid("unknown report module")),
    };
    Ok(lane)
}

fn required_claim_locks() -> &'static [&'static str] {
    &[
        "NO_RANKING_AUTHORITY",
        "NO_OBJECTIVE_AUTHORITY",
        "NO_SYNTHESIS_CLAIM",
        "NO_PROCUREMENT_AUTHORITY",
        "NO_SAFETY_CLAIM",
        "NO_PERFORMANCE_CLAIM",
        "NO_EXECUTION_AUTHORITY",
        "UNMADE_DIGITAL_PROPOSALS",
    ]
}

fn validate_sorted_unique<'a>(
    values: impl Iterator<Item = &'a str>,
    label: &'static str,
) -> Result<(), CompoundV2Error> {
    let values = values.collect::<Vec<_>>();
    if values.is_empty()
        || values.windows(2).any(|window| window[0] >= window[1])
        || values.iter().any(|value| value.trim().is_empty())
    {
        return Err(CompoundV2Error::Invalid(label));
    }
    Ok(())
}

fn require_hash(value: &str) -> Result<(), CompoundV2Error> {
    if value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
        && value.bytes().any(|byte| byte != b'0')
    {
        Ok(())
    } else {
        Err(CompoundV2Error::Hash(value.to_owned()))
    }
}

fn require_safe_path(value: &str) -> Result<(), CompoundV2Error> {
    let path = Path::new(value);
    if value.trim().is_empty()
        || path.is_absolute()
        || path.components().any(|component| {
            matches!(
                component,
                Component::ParentDir | Component::RootDir | Component::Prefix(_)
            )
        })
    {
        Err(CompoundV2Error::Path(value.to_owned()))
    } else {
        Ok(())
    }
}

fn contains_forbidden_authority(value: &Value) -> bool {
    match value {
        Value::Object(object) => object.iter().any(|(key, value)| {
            matches!(
                key.as_str(),
                "rank"
                    | "ranks"
                    | "ranked_candidates"
                    | "optimizer_objective"
                    | "optimizer_objectives"
                    | "synthesis_recommendation"
                    | "procurement_decision"
                    | "safety_conclusion"
            ) || (key == "usable_by_optimizer" && value.as_bool() != Some(false))
                || (key == "execution_authorized" && value.as_bool() != Some(false))
                || contains_forbidden_authority(value)
        }),
        Value::Array(values) => values.iter().any(contains_forbidden_authority),
        _ => false,
    }
}

fn sha256_bytes(bytes: &[u8]) -> String {
    let mut digest = Sha256::new();
    digest.update(bytes);
    format!("{:x}", digest.finalize())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn all_zero_hashes_are_rejected_for_v2_contracts() {
        assert!(require_hash(&"0".repeat(64)).is_err());
        assert!(FileArtifactBindingV1 {
            path: "artifacts/example.json".into(),
            sha256: "0".repeat(64),
        }
        .validate()
        .is_err());
    }

    #[test]
    fn report_lane_table_covers_exactly_29_modules() {
        assert_eq!(REQUIRED_MODULES.len(), 29);
        for module in REQUIRED_MODULES {
            lane_for_module(module).unwrap();
        }
        let unique = REQUIRED_MODULES.into_iter().collect::<BTreeSet<_>>();
        assert_eq!(unique.len(), 29);
    }

    #[test]
    fn unsafe_artifact_paths_are_rejected() {
        for path in ["", "../escape", "/absolute", "a/../../escape"] {
            assert!(require_safe_path(path).is_err(), "accepted {path}");
        }
        require_safe_path("artifacts/compound/a.json").unwrap();
    }

    #[test]
    fn schema_identity_locks_tag_commit_and_proto_hashes() {
        let mut identity = OrdSchemaIdentityV1 {
            schema: ORD_SCHEMA_IDENTITY_SCHEMA.into(),
            version: REQUIRED_ORD_VERSION.into(),
            tagged_object_commit: REQUIRED_ORD_TAG_OBJECT.into(),
            source_commit: REQUIRED_ORD_SOURCE_COMMIT.into(),
            dataset_proto_sha256: REQUIRED_DATASET_PROTO_SHA256.into(),
            reaction_proto_sha256: REQUIRED_REACTION_PROTO_SHA256.into(),
            test_proto_sha256: REQUIRED_TEST_PROTO_SHA256.into(),
            descriptor_set_sha256: "a".repeat(64),
        };
        identity.validate().unwrap();
        identity.source_commit = identity.tagged_object_commit.clone();
        assert!(identity.validate().is_err());
    }

    #[test]
    fn reaction_split_enforces_hash_buckets_coverage_and_leakage() {
        let seed = 20_260_719;
        let mut components = Vec::new();
        for (index, wanted) in [
            ReactionSplitComponentV1::Extraction,
            ReactionSplitComponentV1::Validation,
            ReactionSplitComponentV1::HeldOut,
        ]
        .into_iter()
        .enumerate()
        {
            let mut counter = 0_u64;
            let (reaction_ids, component_id) = loop {
                let reaction_ids = vec![format!("reaction-{index}-{counter}")];
                let component_id = reaction_component_id(seed, &reaction_ids).unwrap();
                if reaction_component_partition(&component_id).unwrap() == wanted {
                    break (reaction_ids, component_id);
                }
                counter += 1;
            };
            components.push(ReactionComponentV1 {
                component_id,
                reaction_ids,
                canonical_reaction_identities: vec![format!("reaction-identity-{index}")],
                compound_family_identities: vec![format!("compound-family-{index}")],
                scaffold_hashes: vec![sha256_bytes(format!("scaffold-{index}").as_bytes())],
            });
        }
        components.sort_by(|left, right| left.component_id.cmp(&right.component_id));
        let assignments = components
            .iter()
            .map(|component| {
                (
                    component.component_id.clone(),
                    reaction_component_partition(&component.component_id).unwrap(),
                )
            })
            .collect::<BTreeMap<_, _>>();
        let ids_for = |partition| {
            let mut ids = components
                .iter()
                .filter(|component| assignments[&component.component_id] == partition)
                .flat_map(|component| component.reaction_ids.iter().cloned())
                .collect::<Vec<_>>();
            ids.sort();
            ids
        };
        let mut split = ReactionSplitManifestV1 {
            schema: REACTION_SPLIT_MANIFEST_SCHEMA.into(),
            seed,
            components: components.clone(),
            assignments: assignments.clone(),
            extraction_reaction_ids: ids_for(ReactionSplitComponentV1::Extraction),
            validation_reaction_ids: ids_for(ReactionSplitComponentV1::Validation),
            heldout_reaction_ids: ids_for(ReactionSplitComponentV1::HeldOut),
            leakage_proof_sha256: String::new(),
            split_jcs_sha256: String::new(),
        };
        split.seal_self_hash().unwrap();
        split.validate().unwrap();

        let repeated_scaffold = split.components[0].scaffold_hashes[0].clone();
        split.components[1].scaffold_hashes[0] = repeated_scaffold;
        assert!(split.seal_self_hash().is_err());
    }

    #[test]
    fn grammar_requires_packed_fingerprints_and_unique_templates() {
        let rule = |family: &str, smarts: &str| ReactionGrammarRuleV1 {
            family: family.into(),
            canonical_reaction_smarts: smarts.into(),
            applicability_fingerprint: vec![0x5a; 256],
            required_substructures: vec!["[C:1]".into()],
            changed_atoms: vec![1, 2],
            changed_bonds: vec![OrdBondChangeV1 {
                kind: OrdBondChangeKindV1::Addition,
                atom_map_a: 1,
                atom_map_b: 2,
                before_order: None,
                after_order: Some("SINGLE".into()),
                before_stereo: None,
                after_stereo: None,
            }],
            stereo_behavior: "PRESERVE".into(),
            extraction_source_reaction_ids: vec![format!("source-{family}")],
            extraction_source_dataset_ids: vec![format!("dataset-{family}")],
            extraction_partition_component_ids: vec![sha256_bytes(family.as_bytes())],
            template_sha256: String::new(),
            rule_jcs_sha256: String::new(),
        };
        let identity = OrdSchemaIdentityV1 {
            schema: ORD_SCHEMA_IDENTITY_SCHEMA.into(),
            version: REQUIRED_ORD_VERSION.into(),
            tagged_object_commit: REQUIRED_ORD_TAG_OBJECT.into(),
            source_commit: REQUIRED_ORD_SOURCE_COMMIT.into(),
            dataset_proto_sha256: REQUIRED_DATASET_PROTO_SHA256.into(),
            reaction_proto_sha256: REQUIRED_REACTION_PROTO_SHA256.into(),
            test_proto_sha256: REQUIRED_TEST_PROTO_SHA256.into(),
            descriptor_set_sha256: "a".repeat(64),
        };
        let mut corpus = ReactionGrammarCorpusV1 {
            schema: REACTION_GRAMMAR_CORPUS_SCHEMA.into(),
            schema_identity: identity.clone(),
            split_sha256: "b".repeat(64),
            source_complete_tree_sha256: "c".repeat(64),
            license: "CC-BY-SA-4.0".into(),
            rules: vec![
                rule("ORD_REDUCTIVE_AMINATION", "[C:1]=[O:2].[N:3]>>[C:1][N:3]"),
                rule("ORD_GLYCIDYL_ETHER_FORMATION", "[O:1].[C:2]>>[O:1][C:2]"),
            ],
            corpus_jcs_sha256: String::new(),
        };
        corpus.seal_self_hash().unwrap();
        corpus.validate().unwrap();

        let duplicate = "[C:1]=[O:2].[N:3]>>[C:1][N:3]";
        corpus.rules = vec![
            rule("ORD_REDUCTIVE_AMINATION", duplicate),
            rule("ORD_GLYCIDYL_ETHER_FORMATION", duplicate),
        ];
        corpus.corpus_jcs_sha256.clear();
        assert!(corpus.seal_self_hash().is_err());

        let mut short_fingerprint =
            rule("ORD_REDUCTIVE_AMINATION", "[C:1]=[O:2].[N:3]>>[C:1][N:3]");
        short_fingerprint.applicability_fingerprint.pop();
        assert!(short_fingerprint.seal_self_hash().is_err());
    }
}
