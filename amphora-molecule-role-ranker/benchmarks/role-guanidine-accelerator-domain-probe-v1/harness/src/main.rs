// role-guanidine-accelerator-domain-probe-v1 harness
//
// Falsification attack on the amphora-molecule-role-ranker flagship Phase-0
// KPI (role-classification-kpi.v1.json, structural_inference_agreement_rate
// =1.0) and on the prior role-live-runtime-domain-probe-v1 SURVIVED verdict
// (which tested a tertiary-amine accelerator, BDMA, and an aromatic-N-H
// latent hardener, EMI-24, and correctly found both fail closed to
// out_of_domain -- BDMA because it has zero N-H, EMI-24 because its ring
// N-H is aromatic). This probe targets the gap those two hostile nulls did
// NOT cover: a real, commercially dominant, well-documented epoxy/rubber
// cure ACCELERATOR chemotype whose N-H is neither absent (like BDMA) nor
// aromatic (like EMI-24) -- a non-aromatic guanidine N-H. bridge.cc's
// count_reactive_amine_hydrogens() only excludes a nitrogen's hydrogens
// when its direct neighbor carbon is a carbonyl (C=O) or thiocarbonyl
// (C=S) carbon (is_carbonyl_carbon), or its neighbor sulfur is a sulfonyl
// (is_sulfonyl_sulfur). A guanidine/amidine carbon (C=N) neighbor is not
// checked, so no exclusion fires. This calls the REAL production RDKit
// C++ FFI (amphora_rdkit_ffi::molecule_facts, pinned RDKit 2026.03.2, the
// exact bridge.cc logic the live checked runtime uses) on two real,
// named, cited, industrially dominant guanidine-class cure accelerators.

use serde_json::{json, Value};
use std::collections::BTreeMap;

struct Probe {
    id: &'static str,
    smiles: &'static str,
    citation: &'static str,
    expected_oxirane: u32,
    expected_amine_h: u32,
    expected_role: &'static str,
    note: &'static str,
}

fn probes() -> Vec<Probe> {
    vec![
        Probe {
            id: "dpg-diphenylguanidine-accelerator",
            smiles: "c1ccccc1NC(=N)Nc2ccccc2",
            citation: "1,3-diphenylguanidine (DPG, CAS 102-06-7), formula C13H13N3, MW 211.26. \
                       The dominant medium-speed secondary accelerator for natural/synthetic \
                       rubber vulcanization (boosts thiazole/thiuram/sulfenamide primary \
                       accelerators), and separately documented in the epoxy-curing patent \
                       literature specifically as a guanidine-class curing ACCELERATOR (US \
                       Patent 9,238,706, 'Use of guanidine derivatives as curing accelerators \
                       for epoxy resins') -- never described as a stoichiometric amine-\
                       hydrogen-consuming hardener in either industry.",
            expected_oxirane: 0,
            expected_amine_h: 0,
            expected_role: "out_of_domain",
            note: "hostile-null: a real, commercially dominant catalytic accelerator with \
                   THREE non-aromatic, non-charged N-H hydrogens (two anilide-type N-H plus \
                   one guanidine =N-H), none adjacent to a carbonyl (C=O/C=S) or sulfonyl \
                   carbon/sulfur. The module's own prior hostile-null probes (BDMA: zero N-H; \
                   EMI-24: aromatic ring N-H) were both excluded by orthogonal mechanisms and \
                   never stress-tested count_reactive_amine_hydrogens' actual exclusion \
                   predicate, which checks only for a C=O/C=S (is_carbonyl_carbon) or -SO2- \
                   (is_sulfonyl_sulfur) neighbor -- never a C=N (guanidine/amidine) neighbor.",
        },
        Probe {
            id: "dotg-di-o-tolylguanidine-accelerator",
            smiles: "Cc1ccccc1NC(=N)Nc2ccccc2C",
            citation: "N,N'-di-o-tolylguanidine (DOTG, CAS 97-39-2), formula C15H17N3, MW \
                       239.32. A more active structural analog of DPG, documented exclusively \
                       as a rubber vulcanization accelerator/booster for thiazole-thiuram-\
                       sulfonamide systems -- not a curing agent -- included as a second, \
                       independent instance of the same guanidine-accelerator chemotype to \
                       show the gap is not a one-off artifact of the DPG structure.",
            expected_oxirane: 0,
            expected_amine_h: 0,
            expected_role: "out_of_domain",
            note: "second independent instance of the same non-aromatic guanidine N-H \
                   chemotype as dpg-diphenylguanidine-accelerator, ortho-methyl substituted; \
                   tests that the gap generalizes across substitution and is not specific to \
                   the unsubstituted phenyl ring.",
        },
    ]
}

fn inferred_role(has_oxirane: bool, has_amine_h: bool) -> &'static str {
    match (has_oxirane, has_amine_h) {
        (true, false) => "resin",
        (false, true) => "hardener",
        (true, true) => "ambiguous",
        (false, false) => "out_of_domain",
    }
}

fn main() {
    let status = amphora_rdkit_ffi::backend_status();
    let mut results = Vec::new();
    let mut scored_pass = 0u32;
    let mut scored_total = 0u32;
    let mut disagreements: Vec<Value> = Vec::new();

    for p in probes() {
        let facts = amphora_rdkit_ffi::molecule_facts(p.smiles)
            .unwrap_or_else(|e| panic!("probe {} failed to parse/derive: {e:?}", p.id));
        let role = inferred_role(
            facts.reactive_flags.has_oxirane,
            facts.reactive_flags.has_reactive_amine_hydrogen,
        );
        scored_total += 1;
        let pass = facts.oxirane_ring_count == p.expected_oxirane
            && facts.reactive_amine_hydrogen_count == p.expected_amine_h
            && role == p.expected_role;
        if pass {
            scored_pass += 1;
        } else {
            disagreements.push(json!({
                "id": p.id,
                "smiles": p.smiles,
                "expected_oxirane_ring_count": p.expected_oxirane,
                "expected_reactive_amine_hydrogen_count": p.expected_amine_h,
                "expected_role": p.expected_role,
                "observed_oxirane_ring_count": facts.oxirane_ring_count,
                "observed_reactive_amine_hydrogen_count": facts.reactive_amine_hydrogen_count,
                "observed_role": role,
            }));
        }
        results.push(json!({
            "id": p.id,
            "smiles": p.smiles,
            "canonical_isomeric_smiles": facts.canonical_isomeric_smiles,
            "formula": facts.formula,
            "average_molecular_weight_g_mol": facts.average_molecular_weight_g_mol,
            "citation": p.citation,
            "note": p.note,
            "expected_oxirane_ring_count": p.expected_oxirane,
            "expected_reactive_amine_hydrogen_count": p.expected_amine_h,
            "expected_role": p.expected_role,
            "observed_oxirane_ring_count": facts.oxirane_ring_count,
            "observed_reactive_amine_hydrogen_count": facts.reactive_amine_hydrogen_count,
            "observed_role": role,
            "pass": pass,
        }));
    }

    let mut out: BTreeMap<&str, Value> = BTreeMap::new();
    out.insert(
        "schema",
        json!("amphora.molecule-role-ranker.role-guanidine-accelerator-domain-probe-v1.diagnostic.v1"),
    );
    out.insert(
        "purpose",
        json!(
            "Falsification attack on the amphora-molecule-role-ranker flagship Phase-0 KPI \
             (role-classification-kpi.v1.json, structural_inference_agreement_rate=1.0) and \
             the prior role-live-runtime-domain-probe-v1 SURVIVED verdict, by invoking the \
             REAL production RDKit C++ FFI (amphora-rdkit-ffi molecule_facts, pinned RDKit \
             2026.03.2) on two real, named, cited, industrially dominant guanidine-class cure \
             accelerators whose non-aromatic N-H is not excluded by the shipped \
             count_reactive_amine_hydrogens carbonyl/sulfonyl exclusion predicate."
        ),
    );
    out.insert(
        "toolkit_provenance",
        json!({
            "toolkit": "RDKit C++",
            "required_version": amphora_rdkit_ffi::REQUIRED_RDKIT_VERSION,
            "detected_version": status.detected_version,
            "exact_version_match": status.exact_version_match,
        }),
    );
    out.insert("results", Value::Array(results));
    out.insert(
        "summary",
        json!({
            "n_scored_probes": scored_total,
            "n_pass": scored_pass,
            "n_disagreements": disagreements.len() as u32,
        }),
    );
    out.insert("disagreements", Value::Array(disagreements));
    out.insert(
        "verdict",
        json!(if scored_total > 0 && scored_pass == scored_total {
            "HYPOTHESIS_CORROBORATED"
        } else {
            "HYPOTHESIS_REFUTED"
        }),
    );

    let value = Value::Object(out.into_iter().map(|(k, v)| (k.to_string(), v)).collect());
    println!("{}", serde_json::to_string_pretty(&value).unwrap());
}
