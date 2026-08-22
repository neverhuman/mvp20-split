// R-N02 FFI-side sweep (repair_mode interactive-2026-08-03).
//
// Drives the REAL production RDKit C++ FFI (amphora_rdkit_ffi::molecule_facts,
// pinned RDKit 2026.03.2, feature = "rdkit") over:
//   (a) all 39 records of the sha-locked role-ranker known-answer fixture
//       amphora-molecule-role-ranker/reference/phase0-role-known-answer.v1.json
//       (fixture is read-only here; never modified), and
//   (b) the 5 coordinated C=N probes: DPG + DOTG (the original refuting
//       probes of role-guanidine-accelerator-domain-probe-v1, same SMILES)
//       plus guanidine + DICY + biguanide (the sibling molecule-property
//       refuting probes, run through the FFI for cross-module consistency).
//
// Output: canonical JSON (BTreeMap ordering) on stdout. No RNG, no wall
// clock. Run PRE-fix and POST-fix, twice each (two-replay byte gate); the
// pre/post fixture rows must be byte-identical (zero regression) and the
// probe rows must flip to reactive_amine_hydrogen_count=0 / out_of_domain.

use serde_json::{json, Value};
use std::collections::BTreeMap;

const FIXTURE: &str = "/home/ubuntu/amphora/build/mvp20-split/amphora-molecule-role-ranker/reference/phase0-role-known-answer.v1.json";

fn inferred_role(has_oxirane: bool, has_amine_h: bool) -> &'static str {
    match (has_oxirane, has_amine_h) {
        (true, false) => "resin",
        (false, true) => "hardener",
        (true, true) => "ambiguous",
        (false, false) => "out_of_domain",
    }
}

fn facts_row(id: &str, smiles: &str) -> Value {
    let facts = amphora_rdkit_ffi::molecule_facts(smiles)
        .unwrap_or_else(|e| panic!("{id}: molecule_facts failed: {e:?}"));
    json!({
        "id": id,
        "smiles": smiles,
        "canonical_isomeric_smiles": facts.canonical_isomeric_smiles,
        "formula": facts.formula,
        "average_molecular_weight_g_mol": facts.average_molecular_weight_g_mol,
        "oxirane_ring_count": facts.oxirane_ring_count,
        "reactive_amine_hydrogen_count": facts.reactive_amine_hydrogen_count,
        "inferred_role": inferred_role(
            facts.reactive_flags.has_oxirane,
            facts.reactive_flags.has_reactive_amine_hydrogen,
        ),
    })
}

fn main() {
    let status = amphora_rdkit_ffi::backend_status();
    let fixture_bytes = std::fs::read(FIXTURE).expect("fixture readable");
    let fixture_sha256 = {
        use sha2::{Digest, Sha256};
        let mut d = Sha256::new();
        d.update(&fixture_bytes);
        format!("{:x}", d.finalize())
    };
    let fixture: Value = serde_json::from_slice(&fixture_bytes).expect("fixture JSON");

    let mut fixture_rows = Vec::new();
    for record in fixture["records"].as_array().expect("records") {
        let id = record["record_id"].as_str().expect("record_id");
        let smiles = record["smiles"].as_str().expect("smiles");
        let row = facts_row(id, smiles);
        let expected_ox = record["facts"]["oxirane_ring_count"].as_u64().unwrap();
        let expected_nh = record["facts"]["reactive_amine_hydrogen_count"].as_u64().unwrap();
        let matches_fixture_facts = row["oxirane_ring_count"].as_u64().unwrap() == expected_ox
            && row["reactive_amine_hydrogen_count"].as_u64().unwrap() == expected_nh;
        let mut row_map = row.as_object().unwrap().clone();
        row_map.insert("fixture_oxirane_ring_count".into(), json!(expected_ox));
        row_map.insert("fixture_reactive_amine_hydrogen_count".into(), json!(expected_nh));
        row_map.insert("matches_fixture_facts".into(), json!(matches_fixture_facts));
        fixture_rows.push(Value::Object(row_map));
    }

    let probes = [
        ("dpg-diphenylguanidine-accelerator", "c1ccccc1NC(=N)Nc2ccccc2"),
        ("dotg-di-o-tolylguanidine-accelerator", "Cc1ccccc1NC(=N)Nc2ccccc2C"),
        ("guanidine", "NC(=N)N"),
        ("dicyandiamide", "NC(=NC#N)N"),
        ("biguanide", "NC(=N)NC(=N)N"),
    ];
    let probe_rows: Vec<Value> = probes
        .iter()
        .map(|(id, smiles)| facts_row(id, smiles))
        .collect();

    let mut out: BTreeMap<&str, Value> = BTreeMap::new();
    out.insert("schema", json!("amphora.rn02-ffi-sweep.diagnostic.v1"));
    out.insert("repair_item", json!("R-N02"));
    out.insert("repair_mode", json!("interactive-2026-08-03"));
    out.insert(
        "toolkit_provenance",
        json!({
            "toolkit": "RDKit C++",
            "required_version": amphora_rdkit_ffi::REQUIRED_RDKIT_VERSION,
            "detected_version": status.detected_version,
            "exact_version_match": status.exact_version_match,
        }),
    );
    out.insert("fixture_path", json!("amphora-molecule-role-ranker/reference/phase0-role-known-answer.v1.json"));
    out.insert("fixture_sha256", json!(fixture_sha256));
    out.insert("n_fixture_records", json!(fixture_rows.len()));
    out.insert(
        "n_fixture_records_matching_fixture_facts",
        json!(fixture_rows
            .iter()
            .filter(|r| r["matches_fixture_facts"] == json!(true))
            .count()),
    );
    out.insert("fixture_records", Value::Array(fixture_rows));
    out.insert("probe_records", Value::Array(probe_rows));

    let value = Value::Object(out.into_iter().map(|(k, v)| (k.to_string(), v)).collect());
    println!("{}", serde_json::to_string_pretty(&value).unwrap());
}
