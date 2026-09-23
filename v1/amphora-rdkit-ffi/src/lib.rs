use serde::{Deserialize, Serialize};
#[cfg(any(feature = "rdkit", test))]
use sha2::{Digest, Sha256};
use thiserror::Error;

pub const REQUIRED_RDKIT_VERSION: &str = "2026.03.2";
pub const REACTIVE_ONTOLOGY_VERSION: &str = "amphora.reactive-ontology.v1";

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct BackendStatus {
    pub available: bool,
    pub required_version: &'static str,
    pub detected_version: Option<String>,
    pub exact_version_match: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct ReactiveFlagsV1 {
    pub has_oxirane: bool,
    pub has_reactive_amine_hydrogen: bool,
    pub dual_role: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct ToolkitProvenanceV1 {
    pub toolkit: String,
    pub required_version: String,
    pub detected_version: String,
    pub exact_version_match: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct MoleculeFactsV1 {
    pub schema: String,
    pub canonical_isomeric_smiles: String,
    pub structure_identity: String,
    pub canonical_structure_sha256: String,
    pub formula: String,
    pub average_molecular_weight_g_mol: f64,
    pub oxirane_ring_count: u32,
    pub reactive_amine_hydrogen_count: u32,
    pub reactive_flags: ReactiveFlagsV1,
    pub ontology_version: String,
    pub toolkit_provenance: ToolkitProvenanceV1,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct MorganFingerprintV1 {
    pub schema: String,
    pub canonical_isomeric_smiles: String,
    pub canonical_structure_sha256: String,
    pub radius: u32,
    pub bit_count: u32,
    pub use_chirality: bool,
    pub on_bits: Vec<u32>,
    pub bemis_murcko_scaffold: String,
    pub scaffold_on_bits: Vec<u32>,
    pub toolkit_provenance: ToolkitProvenanceV1,
}

#[derive(Debug, Error)]
pub enum ChemistryError {
    #[error("pinned RDKit C++ {REQUIRED_RDKIT_VERSION} is unavailable")]
    Unavailable,
    #[error("RDKit version mismatch: expected {REQUIRED_RDKIT_VERSION}, got {0}")]
    VersionMismatch(String),
    #[error("RDKit rejected the structure: {0}")]
    InvalidStructure(String),
    #[error("defined molecule must contain exactly one connected component")]
    MultiFragmentStructure,
    #[error("wildcards, query atoms, and polymer placeholders are unsupported")]
    WildcardOrPolymerStructure,
    #[error("RDKit returned an invalid molecule-facts record")]
    InvalidFactsRecord,
}

#[cfg(feature = "rdkit")]
#[cxx::bridge(namespace = "amphora::rdkit")]
mod ffi {
    unsafe extern "C++" {
        include!("bridge.h");

        fn rdkit_version() -> String;
        fn canonical_smiles(input: &str) -> Result<String>;
        fn molecule_facts_record(input: &str) -> Result<String>;
        fn novelty_record(input: &str) -> Result<String>;
        fn reaction_products(reaction_smarts: &str, reactants: &str) -> Result<String>;
    }
}

pub fn morgan_fingerprint(input: &str) -> Result<MorganFingerprintV1, ChemistryError> {
    validate_supported_smiles(input)?;
    #[cfg(feature = "rdkit")]
    {
        let status = backend_status();
        if !status.exact_version_match {
            return Err(ChemistryError::VersionMismatch(
                status.detected_version.unwrap_or_else(|| "unknown".into()),
            ));
        }
        let detected = status
            .detected_version
            .expect("feature-enabled backend status records a version");
        let record = ffi::novelty_record(input)
            .map_err(|error| ChemistryError::InvalidStructure(error.to_string()))?;
        return parse_novelty_record(&record, &detected);
    }
    #[cfg(not(feature = "rdkit"))]
    {
        Err(ChemistryError::Unavailable)
    }
}

pub fn fingerprint_tanimoto(left: &[u32], right: &[u32]) -> Option<f64> {
    let mut left_index = 0;
    let mut right_index = 0;
    let mut intersection = 0_usize;
    while left_index < left.len() && right_index < right.len() {
        match left[left_index].cmp(&right[right_index]) {
            std::cmp::Ordering::Less => left_index += 1,
            std::cmp::Ordering::Greater => right_index += 1,
            std::cmp::Ordering::Equal => {
                intersection += 1;
                left_index += 1;
                right_index += 1;
            }
        }
    }
    let union = left.len() + right.len() - intersection;
    if union == 0 {
        Some(1.0)
    } else {
        Some(intersection as f64 / union as f64)
    }
}

pub fn molecule_facts(input: &str) -> Result<MoleculeFactsV1, ChemistryError> {
    validate_supported_smiles(input)?;
    #[cfg(feature = "rdkit")]
    {
        let status = backend_status();
        if !status.exact_version_match {
            return Err(ChemistryError::VersionMismatch(
                status.detected_version.unwrap_or_else(|| "unknown".into()),
            ));
        }
        let detected = status
            .detected_version
            .expect("feature-enabled backend status records a version");
        let record = ffi::molecule_facts_record(input)
            .map_err(|error| ChemistryError::InvalidStructure(error.to_string()))?;
        return parse_facts_record(&record, &detected);
    }
    #[cfg(not(feature = "rdkit"))]
    {
        Err(ChemistryError::Unavailable)
    }
}

/// Execute one host-authorized reaction SMARTS against defined reactants.
/// Candidate input cannot provide the reaction SMARTS through this API.
pub fn execute_reaction(
    reaction_smarts: &str,
    reactants: &[String],
) -> Result<Vec<String>, ChemistryError> {
    if reaction_smarts.trim().is_empty() || reactants.is_empty() {
        return Err(ChemistryError::InvalidStructure(
            "reaction SMARTS and reactants are required".into(),
        ));
    }
    for reactant in reactants {
        validate_supported_smiles(reactant)?;
        if reactant.contains('\u{1e}') || reactant.contains('\n') {
            return Err(ChemistryError::InvalidStructure(
                "reaction reactant contains a reserved delimiter".into(),
            ));
        }
    }
    #[cfg(feature = "rdkit")]
    {
        let status = backend_status();
        if !status.exact_version_match {
            return Err(ChemistryError::VersionMismatch(
                status.detected_version.unwrap_or_else(|| "unknown".into()),
            ));
        }
        let encoded = reactants.join("\u{1e}");
        let products = ffi::reaction_products(reaction_smarts, &encoded)
            .map_err(|error| ChemistryError::InvalidStructure(error.to_string()))?;
        let products = products
            .lines()
            .filter(|line| !line.trim().is_empty())
            .map(str::to_owned)
            .collect::<Vec<_>>();
        if products.is_empty() {
            return Err(ChemistryError::InvalidStructure(
                "reaction produced no valid single-component products".into(),
            ));
        }
        return Ok(products);
    }
    #[cfg(not(feature = "rdkit"))]
    {
        Err(ChemistryError::Unavailable)
    }
}

fn validate_supported_smiles(input: &str) -> Result<(), ChemistryError> {
    let input = input.trim();
    if input.is_empty() {
        return Err(ChemistryError::InvalidStructure("empty SMILES".into()));
    }
    if input.contains('.') {
        return Err(ChemistryError::MultiFragmentStructure);
    }
    if input.contains('*') || input.contains('~') {
        return Err(ChemistryError::WildcardOrPolymerStructure);
    }
    Ok(())
}

#[cfg(any(feature = "rdkit", test))]
fn parse_facts_record(
    record: &str,
    detected_version: &str,
) -> Result<MoleculeFactsV1, ChemistryError> {
    let fields = record.split('\t').collect::<Vec<_>>();
    if fields.len() != 5 {
        return Err(ChemistryError::InvalidFactsRecord);
    }
    let canonical_isomeric_smiles = fields[0].to_owned();
    let formula = fields[1].to_owned();
    if canonical_isomeric_smiles.is_empty() || formula.is_empty() {
        return Err(ChemistryError::InvalidFactsRecord);
    }
    let average_molecular_weight_g_mol = fields[2]
        .parse::<f64>()
        .map_err(|_| ChemistryError::InvalidFactsRecord)?;
    if !average_molecular_weight_g_mol.is_finite() || average_molecular_weight_g_mol <= 0.0 {
        return Err(ChemistryError::InvalidFactsRecord);
    }
    let oxirane_ring_count = fields[3]
        .parse::<u32>()
        .map_err(|_| ChemistryError::InvalidFactsRecord)?;
    let reactive_amine_hydrogen_count = fields[4]
        .parse::<u32>()
        .map_err(|_| ChemistryError::InvalidFactsRecord)?;
    let canonical_structure_sha256 = sha256(canonical_isomeric_smiles.as_bytes());
    Ok(MoleculeFactsV1 {
        schema: "amphora.molecule-facts.v1".into(),
        structure_identity: format!("smiles-sha256:{canonical_structure_sha256}"),
        canonical_structure_sha256,
        formula,
        average_molecular_weight_g_mol,
        oxirane_ring_count,
        reactive_amine_hydrogen_count,
        reactive_flags: ReactiveFlagsV1 {
            has_oxirane: oxirane_ring_count > 0,
            has_reactive_amine_hydrogen: reactive_amine_hydrogen_count > 0,
            dual_role: oxirane_ring_count > 0 && reactive_amine_hydrogen_count > 0,
        },
        ontology_version: REACTIVE_ONTOLOGY_VERSION.into(),
        toolkit_provenance: ToolkitProvenanceV1 {
            toolkit: "RDKit C++".into(),
            required_version: REQUIRED_RDKIT_VERSION.into(),
            detected_version: detected_version.into(),
            exact_version_match: detected_version == REQUIRED_RDKIT_VERSION,
        },
        canonical_isomeric_smiles,
    })
}

#[cfg(any(feature = "rdkit", test))]
fn parse_novelty_record(
    record: &str,
    detected_version: &str,
) -> Result<MorganFingerprintV1, ChemistryError> {
    let fields = record.split('\t').collect::<Vec<_>>();
    if fields.len() != 4 || fields[0].is_empty() {
        return Err(ChemistryError::InvalidFactsRecord);
    }
    let on_bits = parse_on_bits(fields[2])?;
    let scaffold_on_bits = parse_on_bits(fields[3])?;
    Ok(MorganFingerprintV1 {
        schema: "amphora.morgan-fingerprint.v1".into(),
        canonical_isomeric_smiles: fields[0].into(),
        canonical_structure_sha256: sha256(fields[0].as_bytes()),
        radius: 2,
        bit_count: 2048,
        use_chirality: true,
        on_bits,
        bemis_murcko_scaffold: fields[1].into(),
        scaffold_on_bits,
        toolkit_provenance: ToolkitProvenanceV1 {
            toolkit: "RDKit C++".into(),
            required_version: REQUIRED_RDKIT_VERSION.into(),
            detected_version: detected_version.into(),
            exact_version_match: detected_version == REQUIRED_RDKIT_VERSION,
        },
    })
}

#[cfg(any(feature = "rdkit", test))]
fn parse_on_bits(value: &str) -> Result<Vec<u32>, ChemistryError> {
    if value.is_empty() {
        return Ok(Vec::new());
    }
    let bits = value
        .split(',')
        .map(|bit| {
            bit.parse::<u32>()
                .map_err(|_| ChemistryError::InvalidFactsRecord)
        })
        .collect::<Result<Vec<_>, _>>()?;
    if bits.iter().any(|bit| *bit >= 2048) || bits.windows(2).any(|pair| pair[0] >= pair[1]) {
        return Err(ChemistryError::InvalidFactsRecord);
    }
    Ok(bits)
}

#[cfg(any(feature = "rdkit", test))]
fn sha256(bytes: &[u8]) -> String {
    let mut digest = Sha256::new();
    digest.update(bytes);
    format!("{:x}", digest.finalize())
}

pub fn backend_status() -> BackendStatus {
    #[cfg(feature = "rdkit")]
    {
        let detected = ffi::rdkit_version();
        return BackendStatus {
            available: detected == REQUIRED_RDKIT_VERSION,
            required_version: REQUIRED_RDKIT_VERSION,
            exact_version_match: detected == REQUIRED_RDKIT_VERSION,
            detected_version: Some(detected),
        };
    }
    #[cfg(not(feature = "rdkit"))]
    BackendStatus {
        available: false,
        required_version: REQUIRED_RDKIT_VERSION,
        detected_version: None,
        exact_version_match: false,
    }
}

pub fn normalize_smiles(input: &str) -> Result<String, ChemistryError> {
    validate_supported_smiles(input)?;
    #[cfg(feature = "rdkit")]
    {
        let status = backend_status();
        if !status.exact_version_match {
            return Err(ChemistryError::VersionMismatch(
                status.detected_version.unwrap_or_else(|| "unknown".into()),
            ));
        }
        return ffi::canonical_smiles(input)
            .map_err(|error| ChemistryError::InvalidStructure(error.to_string()));
    }
    #[cfg(not(feature = "rdkit"))]
    {
        let _ = input;
        Err(ChemistryError::Unavailable)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[cfg(not(feature = "rdkit"))]
    #[test]
    fn missing_pinned_backend_fails_closed() {
        assert!(!backend_status().available);
        assert!(matches!(
            normalize_smiles("CCO"),
            Err(ChemistryError::Unavailable)
        ));
        assert!(matches!(
            molecule_facts("CCO"),
            Err(ChemistryError::Unavailable)
        ));
    }

    #[test]
    fn unsupported_components_and_polymers_fail_before_backend_use() {
        assert!(matches!(
            molecule_facts("CC.O"),
            Err(ChemistryError::MultiFragmentStructure)
        ));
        assert!(matches!(
            molecule_facts("[*]CC[*]"),
            Err(ChemistryError::WildcardOrPolymerStructure)
        ));
    }

    #[test]
    fn native_record_builds_deterministic_versioned_facts() {
        let facts = parse_facts_record(
            "CC1(C)CC(N)CC(C)(CN)C1\tC10H22N2\t170.300000\t0\t4",
            REQUIRED_RDKIT_VERSION,
        )
        .unwrap();
        assert_eq!(facts.formula, "C10H22N2");
        assert_eq!(facts.reactive_amine_hydrogen_count, 4);
        assert!(!facts.reactive_flags.dual_role);
        assert_eq!(facts.ontology_version, REACTIVE_ONTOLOGY_VERSION);
        assert_eq!(facts.canonical_structure_sha256.len(), 64);
    }

    #[test]
    fn fingerprint_record_and_tanimoto_are_deterministic() {
        let fingerprint =
            parse_novelty_record("c1ccccc1\tc1ccccc1\t1,4,7\t1,4,7", REQUIRED_RDKIT_VERSION)
                .unwrap();
        assert_eq!(fingerprint.radius, 2);
        assert_eq!(fingerprint.bit_count, 2048);
        assert_eq!(fingerprint.on_bits, vec![1, 4, 7]);
        assert_eq!(
            fingerprint_tanimoto(&fingerprint.on_bits, &[1, 4, 9]),
            Some(0.5)
        );
        assert!(parse_novelty_record("CC\t\t4,1\t", REQUIRED_RDKIT_VERSION).is_err());
    }

    #[cfg(feature = "rdkit")]
    #[test]
    fn pinned_native_backend_matches_reactive_ontology_controls() {
        let controls = [
            ("NCCNCCN", 0, 5),
            ("CC(=O)N", 0, 0),
            ("NCCNC(=O)C", 0, 2),
            ("NS(=O)(=O)C", 0, 0),
            ("CN(C)C", 0, 0),
            ("C1OC1", 1, 0),
            ("C1OC1CN", 1, 2),
        ];
        for (smiles, oxirane, amine_hydrogens) in controls {
            let facts = molecule_facts(smiles).unwrap();
            assert_eq!(facts.oxirane_ring_count, oxirane, "{smiles}");
            assert_eq!(
                facts.reactive_amine_hydrogen_count, amine_hydrogens,
                "{smiles}"
            );
        }
    }

    /// R-N02 regression guard: amidine/guanidine N-H (attached carbon bears a
    /// C=N double bond) is excluded from reactive amine hydrogens, symmetric
    /// with the long-standing C=O/C=S amide exclusion. Probes are the exact
    /// molecules of the two 2026-08-03 refuting receipts
    /// (amine-nh-guanidine-conjugation-gap-v1 and
    /// role-guanidine-accelerator-domain-probe-v1). Categorical
    /// classification only: whether guanidine N-H is exactly 0 in a
    /// quantitative AHEW sense stays explicitly open.
    ///
    /// W-FFI2 (2026-08-06): dicyandiamide is carved OUT of this all-zero list.
    /// It is a real functionality-4 stoichiometric hardener (WO1993010168A1)
    /// whose cyanamide-substituted imine nitrogen breaks the symmetric
    /// Y-delocalized resonance the R-N02 exclusion relies on (see
    /// is_cyanamide_substituted_guanidine_carbon in bridge.cc for the
    /// structural criterion and citations). Pure alkyl/aryl/H-substituted
    /// guanidines (DPG, DOTG, guanidine, biguanide) are unaffected and stay 0.
    #[cfg(feature = "rdkit")]
    #[test]
    fn pinned_native_backend_excludes_guanidine_class_amine_hydrogens() {
        let guanidine_class = [
            // (id, SMILES): all must yield reactive_amine_hydrogen_count == 0.
            ("dpg-diphenylguanidine-accelerator", "c1ccccc1NC(=N)Nc2ccccc2"),
            (
                "dotg-di-o-tolylguanidine-accelerator",
                "Cc1ccccc1NC(=N)Nc2ccccc2C",
            ),
            ("guanidine", "NC(=N)N"),
            ("biguanide", "NC(=N)NC(=N)N"),
        ];
        for (id, smiles) in guanidine_class {
            let facts = molecule_facts(smiles).unwrap();
            assert_eq!(facts.oxirane_ring_count, 0, "{id}");
            assert_eq!(facts.reactive_amine_hydrogen_count, 0, "{id}");
            assert!(!facts.reactive_flags.has_reactive_amine_hydrogen, "{id}");
            assert!(!facts.reactive_flags.dual_role, "{id}");
        }
        // The symmetric exclusions and plain amines are unchanged.
        let unchanged = [("NCCNCCN", 5), ("CC(=O)N", 0), ("NCCNC(=O)C", 2)];
        for (smiles, amine_hydrogens) in unchanged {
            let facts = molecule_facts(smiles).unwrap();
            assert_eq!(
                facts.reactive_amine_hydrogen_count, amine_hydrogens,
                "{smiles}"
            );
        }
    }

    /// W-FFI2 repair guard: dicyandiamide (cyanoguanidine, CAS 461-58-5) is a
    /// real near-stoichiometric one-part epoxy hardener with a published
    /// functionality of four (WO1993010168A1, 1993), not zero. The narrow
    /// structural exemption (cyanamide substituent on the guanidine carbon's
    /// imine nitrogen) must fire on dicyandiamide itself while leaving every
    /// plain alkyl/aryl/H-substituted guanidine/amidine at 0, and must not
    /// over-fire on a molecule that merely contains a nitrile ELSEWHERE
    /// (not attached to the imine nitrogen of an amidine/guanidine carbon).
    #[cfg(feature = "rdkit")]
    #[test]
    fn pinned_native_backend_scores_dicyandiamide_functionality_four() {
        let facts = molecule_facts("NC(=NC#N)N").unwrap();
        assert_eq!(facts.formula, "C2H4N4");
        assert_eq!(facts.reactive_amine_hydrogen_count, 4, "dicyandiamide");
        assert!(facts.reactive_flags.has_reactive_amine_hydrogen);

        // Adversarial narrowness probe: an amidine/guanidine carbon whose
        // imine nitrogen carries a plain alkyl substituent (not a nitrile)
        // must NOT be caught by the cyanamide exemption -- N-H stays 0.
        let n_methylguanidine = molecule_facts("CN=C(N)N").unwrap();
        assert_eq!(
            n_methylguanidine.reactive_amine_hydrogen_count, 0,
            "n-methylguanidine (imine-N alkyl substituent, no nitrile) must stay excluded"
        );

        // Adversarial narrowness probe: a nitrile present elsewhere in the
        // molecule, NOT bonded to the amidine/guanidine carbon's imine
        // nitrogen, must not trigger the exemption either.
        let remote_nitrile_guanidine = molecule_facts("N#CCNC(=N)N").unwrap();
        assert_eq!(
            remote_nitrile_guanidine.reactive_amine_hydrogen_count, 0,
            "remote nitrile (not on the imine nitrogen) must not exempt the guanidine N-H"
        );
    }

    /// W-FFI2 fire 2 (2026-08-06) regression guard: dicyandiamide's three
    /// guanidine nitrogens are resonance-equivalent (that is the entire
    /// premise the R-N02 exclusion and its cyanamide exemption both rely
    /// on), so which nitrogen carries the FORMAL C=N in a given SMILES is a
    /// kekulization/tautomer choice, not a chemical fact. RDKit does not
    /// tautomer-canonicalize on parse. A prior version of
    /// is_cyanamide_substituted_guanidine_carbon only inspected the
    /// double-bonded nitrogen and so silently scored 0 (not 4) for equally
    /// valid alternate-tautomer SMILES of the identical molecule -- this
    /// reproduced the exact defect W-FFI1 refuted, undetected by every
    /// fixture in the portfolio because all of them hardcode the single
    /// canonical string "NC(=NC#N)N". Every representation below is the
    /// same molecule (formula C2H4N4) and must score functionality 4.
    #[cfg(feature = "rdkit")]
    #[test]
    fn pinned_native_backend_dicyandiamide_score_is_tautomer_representation_invariant() {
        let tautomer_smiles = [
            "NC(=NC#N)N",   // canonical fixture form (double bond on cyanamide N)
            "N=C(N)NC#N",   // double bond on a terminal NH2 instead
            "N#CNC(N)=N",   // reordered atoms, same tautomer as above
            "N#CNC(=N)N",   // leading-nitrile ordering, same tautomer as above
            "C(=NC#N)(N)N", // PubChem CID 10005-style atom ordering
        ];
        for smiles in tautomer_smiles {
            let facts = molecule_facts(smiles).unwrap();
            assert_eq!(facts.formula, "C2H4N4", "{smiles}");
            assert_eq!(
                facts.reactive_amine_hydrogen_count, 4,
                "dicyandiamide tautomer {smiles} must score functionality 4 regardless of which nitrogen carries the formal C=N"
            );
            assert!(
                facts.reactive_flags.has_reactive_amine_hydrogen,
                "{smiles}"
            );
        }
    }

    #[cfg(feature = "rdkit")]
    #[test]
    fn pinned_native_fingerprints_replay_and_preserve_stereochemistry() {
        let first = morgan_fingerprint("N[C@@H](C)C(=O)O").unwrap();
        let second = morgan_fingerprint("N[C@@H](C)C(=O)O").unwrap();
        let opposite = morgan_fingerprint("N[C@H](C)C(=O)O").unwrap();
        assert_eq!(first, second);
        assert_ne!(first.on_bits, opposite.on_bits);
        assert_eq!(
            first.toolkit_provenance.detected_version,
            REQUIRED_RDKIT_VERSION
        );
    }

    #[cfg(feature = "rdkit")]
    #[test]
    fn native_identity_preserves_isotope_charge_and_stereochemistry() {
        for smiles in ["[13CH3]C", "C[NH3+]", "N[C@@H](C)C(=O)O"] {
            let facts = molecule_facts(smiles).unwrap();
            assert!(!facts.canonical_isomeric_smiles.is_empty());
            assert_eq!(
                facts.toolkit_provenance.detected_version,
                REQUIRED_RDKIT_VERSION
            );
        }
        assert!(molecule_facts("not-a-smiles").is_err());
    }
}
