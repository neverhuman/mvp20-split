// role-flory-gelation-amine-smarts-parity-v1 harness
//
// Falsification attack on amphora-molecule-role-ranker/benchmarks/role-flory-gelation-v1
// (Flory-Stockmayer network-adequacy sub-grade, verdict HYPOTHESIS_CORROBORATED,
// rederivation.agreement_rate=1.0 on its own 24-record single-role fixture, never
// before ledger-attacked).
//
// run_flory_gel.py claims its per-molecule (f,g) functionality is "RE-DERIVED
// independently from SMILES with pinned RDKit SMARTS and cross-checked byte-for-byte
// against the fixture's stored facts (anti-circularity)". Its local Python amine-H
// SMARTS is:
//   [NX3;H1,H2;!$(NC=O);!$(N=*);!$([N+]);!a]
// This excludes only the single nitrogen that itself carries the formal C=N double
// bond. It does NOT implement the broader Y-delocalized-resonance guanidine/amidine
// exclusion that amphora-rdkit-ffi's real production backend (bridge.cc,
// count_reactive_amine_hydrogens) carries after the R-N02 / W-FFI2 repairs -- the
// exact defect class twice already refuted against sibling artifacts in this module
// (amine-nh-guanidine-conjugation-gap-v1, role-guanidine-accelerator-domain-probe-v1).
// The flory-gelation fixture contains ZERO guanidine-class records, so this
// divergence between the module's own local re-derivation and its own real
// production ground truth has never been exercised.
//
// This harness calls the REAL production RDKit C++ FFI (amphora_rdkit_ffi::
// molecule_facts, pinned RDKit 2026.03.2 -- the same backend the pinned regression
// guard pinned_native_backend_excludes_guanidine_class_amine_hydrogens tests) on the
// same probe set, to establish live ground truth this fire independently confirms
// (not merely cited from the existing test file).

use serde_json::{json, Value};

struct Probe {
    id: &'static str,
    smiles: &'static str,
    citation: &'static str,
}

fn probes() -> Vec<Probe> {
    vec![
        Probe {
            id: "dpg-diphenylguanidine-accelerator",
            smiles: "c1ccccc1NC(=N)Nc2ccccc2",
            citation: "1,3-diphenylguanidine (DPG, CAS 102-06-7). Same molecule as \
                       role-guanidine-accelerator-domain-probe-v1's already-ledgered probe.",
        },
        Probe {
            id: "dotg-di-o-tolylguanidine-accelerator",
            smiles: "Cc1ccccc1NC(=N)Nc2ccccc2C",
            citation: "N,N'-di-o-tolylguanidine (DOTG, CAS 97-39-2). Same molecule as \
                       role-guanidine-accelerator-domain-probe-v1's already-ledgered probe.",
        },
        Probe {
            id: "guanidine",
            smiles: "NC(=N)N",
            citation: "Guanidine (CAS 113-00-8), the parent Y-delocalized structure; pinned \
                       regression control in amphora-rdkit-ffi::pinned_native_backend_\
                       excludes_guanidine_class_amine_hydrogens.",
        },
        Probe {
            id: "biguanide",
            smiles: "NC(=N)NC(=N)N",
            citation: "Biguanide (CAS 56-03-1), same pinned regression control set.",
        },
        Probe {
            id: "dicyandiamide-narrow-exemption",
            smiles: "NC(=NC#N)N",
            citation: "Dicyandiamide / cyanoguanidine (DICY, CAS 461-58-5), the sole named \
                       carve-out (W-FFI2, WO1993010168A1): a real functionality-4 \
                       stoichiometric hardener whose cyanamide-substituted imine nitrogen \
                       breaks the symmetric resonance the guanidine exclusion relies on.",
        },
        Probe {
            id: "n-methylguanidine-narrowness-control",
            smiles: "CN=C(N)N",
            citation: "N-methylguanidine: adversarial narrowness control from the pinned \
                       amphora-rdkit-ffi test suite -- imine-N alkyl substituent, no \
                       nitrile, must stay excluded (reactive_amine_hydrogen_count == 0).",
        },
    ]
}

fn main() {
    let status = amphora_rdkit_ffi::backend_status();
    let mut results = Vec::new();

    for p in probes() {
        let facts = amphora_rdkit_ffi::molecule_facts(p.smiles)
            .unwrap_or_else(|e| panic!("probe {} failed to parse/derive: {e:?}", p.id));
        results.push(json!({
            "id": p.id,
            "smiles": p.smiles,
            "canonical_isomeric_smiles": facts.canonical_isomeric_smiles,
            "formula": facts.formula,
            "citation": p.citation,
            "production_oxirane_ring_count": facts.oxirane_ring_count,
            "production_reactive_amine_hydrogen_count": facts.reactive_amine_hydrogen_count,
            "production_has_reactive_amine_hydrogen": facts.reactive_flags.has_reactive_amine_hydrogen,
        }));
    }

    let out = json!({
        "schema": "amphora.molecule-role-ranker.role-flory-gelation-amine-smarts-parity-v1.live_ffi_ground_truth.v1",
        "purpose": "Live production RDKit C++ FFI ground truth (oxirane_ring_count, \
                    reactive_amine_hydrogen_count) for 6 guanidine/amidine-class probes, to \
                    be diffed against role-flory-gelation-v1's local Python SMARTS \
                    re-derivation for the same SMILES.",
        "toolkit_provenance": {
            "toolkit": "RDKit C++",
            "required_version": amphora_rdkit_ffi::REQUIRED_RDKIT_VERSION,
            "detected_version": status.detected_version,
            "exact_version_match": status.exact_version_match,
        },
        "results": Value::Array(results),
    });

    println!("{}", serde_json::to_string_pretty(&out).unwrap());
}
