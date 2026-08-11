fn main() {
    // T-01B/Act-2 demo: bake the pinned RDKit shared-library directory as an
    // rpath on the amphora-tui binary so it always resolves RDKit C++ 2026.03.2
    // from the audited prefix -- never a stale system /lib RDKit -- and runs
    // without a caller-supplied LD_LIBRARY_PATH. A dependency build script's
    // link-args do not propagate to the final binary; the binary crate's do.
    println!("cargo:rerun-if-env-changed=RDKIT_LIB_DIR");
    if let Ok(lib) = std::env::var("RDKIT_LIB_DIR") {
        if !lib.is_empty() {
            // DT_RPATH (not DT_RUNPATH): RUNPATH is not consulted for the
            // transitively-loaded RDKit libraries, which would then fall back to
            // a stale system /lib RDKit and crash on a symbol mismatch. RPATH is
            // inherited by those indirect loads, so the whole RDKit closure
            // resolves from the pinned prefix.
            println!("cargo:rustc-link-arg=-Wl,--disable-new-dtags");
            println!("cargo:rustc-link-arg=-Wl,-rpath,{lib}");
        }
    }
}
