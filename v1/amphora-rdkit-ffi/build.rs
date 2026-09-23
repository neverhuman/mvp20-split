fn main() {
    println!("cargo:rerun-if-env-changed=RDKIT_INCLUDE_DIR");
    println!("cargo:rerun-if-env-changed=RDKIT_LIB_DIR");
    println!("cargo:rerun-if-env-changed=BOOST_INCLUDE_DIR");
    println!("cargo:rerun-if-changed=include/bridge.h");
    println!("cargo:rerun-if-changed=src/bridge.cc");
    if std::env::var_os("CARGO_FEATURE_RDKIT").is_none() {
        return;
    }
    let include = std::env::var("RDKIT_INCLUDE_DIR")
        .expect("the rdkit feature requires RDKIT_INCLUDE_DIR for RDKit C++ 2026.03.2");
    let library = std::env::var("RDKIT_LIB_DIR")
        .expect("the rdkit feature requires RDKIT_LIB_DIR for RDKit C++ 2026.03.2");
    let boost_include = std::env::var("BOOST_INCLUDE_DIR").unwrap_or_else(|_| {
        std::path::Path::new(&include)
            .parent()
            .expect("RDKIT_INCLUDE_DIR must have a parent containing pinned Boost")
            .to_string_lossy()
            .into_owned()
    });
    cxx_build::bridge("src/lib.rs")
        .file("src/bridge.cc")
        .include(&include)
        .include(boost_include)
        .include("include")
        .flag_if_supported("-std=c++20")
        .compile("amphora_rdkit_bridge");
    println!("cargo:rustc-link-search=native={library}");
    for library in [
        "RDKitChemReactions",
        "RDKitDescriptors",
        "RDKitChemTransforms",
        "RDKitFingerprints",
        "RDKitSmilesParse",
        "RDKitGraphMol",
        "RDKitDataStructs",
        "RDKitRDGeneral",
    ] {
        println!("cargo:rustc-link-lib={library}");
    }
}
