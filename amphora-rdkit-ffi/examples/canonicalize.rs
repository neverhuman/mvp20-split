#[cfg(feature = "rdkit")]
fn main() {
    for input in std::env::args().skip(1) {
        let facts = amphora_rdkit_ffi::molecule_facts(&input)
            .unwrap_or_else(|error| panic!("{input}: {error}"));
        println!(
            "{}\t{}\t{}",
            input, facts.canonical_isomeric_smiles, facts.canonical_structure_sha256
        );
    }
}

#[cfg(not(feature = "rdkit"))]
fn main() {
    panic!("canonicalize requires --features rdkit");
}
