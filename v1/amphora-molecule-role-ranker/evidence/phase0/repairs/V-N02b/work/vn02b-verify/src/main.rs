// V-N02b: INDEPENDENT VERIFY of repair R-N02 on the molecule-role-ranker side.
//
// This harness was NOT written by R-N02's author; it is a fresh adversarial
// re-derivation. It attacks four independent claims made by the R-N02 done
// receipt (amphora-molecule-role-ranker/evidence/phase0/repairs/R-N02/done/
// rn02-molecule-role-ranker-coordinated-cn-fix-repair-receipt.v1.dsse.json):
//
//   (1) DPG (CAS 102-06-7) and DOTG (CAS 97-39-2) classify out_of_domain with
//       reactive_amine_hydrogen_count==0 THROUGH THE REAL production RDKit
//       C++ FFI (amphora_rdkit_ffi::molecule_facts, feature=rdkit) -- not a
//       synthesized/hand-computed fact.
//   (2) The sha-locked 39-record v1 fixture is byte-intact (unchanged sha256)
//       and every one of its records reproduces through the real FFI.
//   (3) fixture v2 SUPERSEDES v1 (embeds all 39 v1 records byte-identically
//       plus appends new guanidine-class records) rather than replacing it;
//       v1's file is untouched on disk.
//   (4) The fix generalizes to guanidine-family accelerators NEVER tested by
//       R-N02 or its refuting receipts: three novel probes not in the
//       original 5 (DPG, DOTG, guanidine, DICY, biguanide):
//         - TMG   1,1,3,3-tetramethylguanidine, CAS 80-70-6 (C5H13N3,
//           MW 115.18) -- discriminating case: exactly one N-H, on the
//           imino nitrogen itself, which must be excluded via the new
//           is_amidine_or_guanidine_carbon neighbor check.
//         - Barton's base, 2-tert-butyl-1,1,3,3-tetramethylguanidine,
//           CAS 29166-72-1 (C9H21N3, MW 171.28) -- non-discriminating
//           boundary case: fully N-substituted, zero N-H by construction;
//           confirms out_of_domain classification is stable regardless of
//           which mechanism drives the N-H count to zero.
//         - 1-phenylguanidine, CAS 2002-98-6 (C7H9N3, MW 135.17) --
//           discriminating case: primary NH2 (single-bonded neighbor to the
//           guanidine carbon) plus imino N-H, a different substitution
//           pattern (mono-aryl, free NH2) than any of the original 5 probes.
//         - Agmatine, CAS 306-60-5 (C5H14N4, MW 130.19) -- ADVERSARIAL
//           over-exclusion probe: a real primary amine (terminal butyl NH2)
//           structurally remote from an incidental guanidine group in the
//           same molecule. Expects reactive_amine_hydrogen_count==2 and
//           role==hardener, NOT out_of_domain -- tests that the fix excludes
//           only the guanidine's own N-H, not the whole molecule's N-H.
//
// Pre-registered refute criterion: CLAIM_REFUTED if ANY of the following:
//   - v1 fixture sha256 != 8ce4d54192a20e8de1bb89f6181b11630fc184b4dda2918ce934610630855c8f
//   - any of the 39 v1 records fails to reproduce via the real FFI
//   - v2 fixture sha256 != 7345ab13d31d9d8ce31392e3648c6a74db3e541162e0aea9ff24035b38a22a4e
//   - v2's first 39 records are not byte-identical to v1's 39 records
//   - v2 does not have exactly 44 records
//   - DPG or DOTG observed_role != out_of_domain or reactive_amine_hydrogen_count != 0
//   - any of the 3 novel probes observed_role != out_of_domain or
//     reactive_amine_hydrogen_count != expected
// No RNG, no wall clock: deterministic given the checked-in fixtures, the
// hardcoded probe SMILES, and the pinned RDKit 2026.03.2 backend.

use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;

const ROOT: &str = "/home/ubuntu/amphora/build/mvp20-split";
const V1_SHA_EXPECTED: &str =
    "8ce4d54192a20e8de1bb89f6181b11630fc184b4dda2918ce934610630855c8f";
const V2_SHA_EXPECTED: &str =
    "7345ab13d31d9d8ce31392e3648c6a74db3e541162e0aea9ff24035b38a22a4e";

fn sha256_hex(bytes: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(bytes);
    format!("{:x}", hasher.finalize())
}

fn inferred_role(has_oxirane: bool, has_amine_h: bool) -> &'static str {
    match (has_oxirane, has_amine_h) {
        (true, false) => "resin",
        (false, true) => "hardener",
        (true, true) => "ambiguous",
        (false, false) => "out_of_domain",
    }
}

struct Probe {
    id: &'static str,
    smiles: &'static str,
    citation: &'static str,
    expected_formula: &'static str,
    expected_mw: f64,
    expected_amine_h: u32,
    expected_role: &'static str,
    novel: bool,
}

fn probes() -> Vec<Probe> {
    vec![
        Probe {
            id: "dpg-diphenylguanidine-accelerator",
            smiles: "c1ccccc1NC(=N)Nc2ccccc2",
            citation: "1,3-diphenylguanidine (DPG), CAS 102-06-7, rubber vulcanization \
                       secondary accelerator; US Patent 9,238,706 documents guanidine \
                       derivatives as epoxy curing accelerators. Original R-N02 refuting probe.",
            expected_formula: "C13H13N3",
            expected_mw: 211.268,
            expected_amine_h: 0,
            expected_role: "out_of_domain",
            novel: false,
        },
        Probe {
            id: "dotg-di-o-tolylguanidine-accelerator",
            smiles: "Cc1ccccc1NC(=N)Nc2ccccc2C",
            citation: "N,N'-di-o-tolylguanidine (DOTG), CAS 97-39-2, rubber vulcanization \
                       accelerator, structural analog of DPG. Original R-N02 refuting probe.",
            expected_formula: "C15H17N3",
            expected_mw: 239.322,
            expected_amine_h: 0,
            expected_role: "out_of_domain",
            novel: false,
        },
        Probe {
            id: "tmg-tetramethylguanidine-novel",
            smiles: "CN(C)C(=N)N(C)C",
            citation: "1,1,3,3-tetramethylguanidine (TMG), CAS 80-70-6, C5H13N3, MW 115.18. \
                       Widely used non-nucleophilic organic superbase catalyst/accelerator in \
                       epoxy (anhydride-cure) and polyurethane chemistry. NOT one of R-N02's \
                       original 5 probes (DPG, DOTG, guanidine, DICY, biguanide).",
            expected_formula: "C5H13N3",
            expected_mw: 115.183,
            expected_amine_h: 0,
            expected_role: "out_of_domain",
            novel: true,
        },
        Probe {
            id: "bartons-base-tbtmg-novel",
            smiles: "CC(C)(C)N=C(N(C)C)N(C)C",
            citation: "2-tert-butyl-1,1,3,3-tetramethylguanidine (Barton's base), CAS \
                       29166-72-1, C9H21N3, MW 171.28. Strong hindered guanidine base/catalyst. \
                       NOT one of R-N02's original 5 probes; fully N-substituted (zero N-H by \
                       construction) -- tests classification stability when the exclusion rule \
                       is not even needed to reach count=0.",
            expected_formula: "C9H21N3",
            expected_mw: 171.288,
            expected_amine_h: 0,
            expected_role: "out_of_domain",
            novel: true,
        },
        Probe {
            id: "1-phenylguanidine-novel",
            smiles: "NC(=N)Nc1ccccc1",
            citation: "1-phenylguanidine, CAS 2002-98-6, C7H9N3, MW 135.17. Mono-aryl \
                       guanidine with a free primary NH2 plus imino N-H -- a different \
                       substitution pattern (primary amine neighbor) than any of R-N02's \
                       original 5 probes, none of which carried a free NH2 on the guanidine \
                       carbon.",
            expected_formula: "C7H9N3",
            expected_mw: 135.174,
            expected_amine_h: 0,
            expected_role: "out_of_domain",
            novel: true,
        },
        Probe {
            id: "agmatine-over-exclusion-boundary-novel",
            smiles: "NCCCCNC(=N)N",
            citation: "Agmatine (4-aminobutylguanidine), CAS 306-60-5, C5H14N4, MW 130.19. \
                       ADVERSARIAL over-exclusion probe: a molecule with a real, structurally \
                       remote primary amine (terminal butyl -NH2, 2 H's, attached to a plain \
                       CH2 carbon far from the guanidine carbon) COEXISTING with an incidental \
                       guanidine group elsewhere in the same molecule. The R-N02 fix must \
                       exclude only the N-H atoms whose OWN attached carbon bears the C=N bond \
                       (the guanidine's own 3 N's), not collaterally zero out unrelated amine \
                       N-H elsewhere in the molecule. Not tested by R-N02, its refuting \
                       receipts, or any other novel probe in this verify -- every other probe \
                       here has zero non-guanidine N-H, so none could catch a too-broad, \
                       whole-molecule exclusion bug. Pre-registered refute trigger: observed \
                       reactive_amine_hydrogen_count != 2 or observed_role != hardener.",
            expected_formula: "C5H14N4",
            expected_mw: 130.195,
            expected_amine_h: 2,
            expected_role: "hardener",
            novel: true,
        },
    ]
}

fn main() {
    let status = amphora_rdkit_ffi::backend_status();
    let mut refute_reasons: Vec<String> = Vec::new();

    // --- (2) v1 fixture byte-intact + every record reproduces via real FFI ---
    let v1_path = format!(
        "{ROOT}/amphora-molecule-role-ranker/reference/phase0-role-known-answer.v1.json"
    );
    let v1_bytes = std::fs::read(&v1_path).expect("v1 fixture readable");
    let v1_sha = sha256_hex(&v1_bytes);
    if v1_sha != V1_SHA_EXPECTED {
        refute_reasons.push(format!(
            "v1 fixture sha256 mismatch: expected {V1_SHA_EXPECTED}, got {v1_sha}"
        ));
    }
    let v1: Value = serde_json::from_slice(&v1_bytes).expect("v1 JSON");
    let v1_records = v1["records"].as_array().expect("v1 records").clone();

    let mut fixture_rows = Vec::new();
    let mut n_fixture_mismatch = 0u32;
    for record in &v1_records {
        let id = record["record_id"].as_str().expect("record_id");
        let smiles = record["smiles"].as_str().expect("smiles");
        let facts = amphora_rdkit_ffi::molecule_facts(smiles)
            .unwrap_or_else(|e| panic!("{id}: molecule_facts failed: {e:?}"));
        let expected_ox = record["facts"]["oxirane_ring_count"].as_u64().unwrap();
        let expected_nh = record["facts"]["reactive_amine_hydrogen_count"]
            .as_u64()
            .unwrap();
        let matches = facts.oxirane_ring_count as u64 == expected_ox
            && facts.reactive_amine_hydrogen_count as u64 == expected_nh;
        if !matches {
            n_fixture_mismatch += 1;
        }
        fixture_rows.push(json!({
            "id": id,
            "matches_fixture_facts": matches,
            "observed_oxirane_ring_count": facts.oxirane_ring_count,
            "observed_reactive_amine_hydrogen_count": facts.reactive_amine_hydrogen_count,
        }));
    }
    if n_fixture_mismatch > 0 {
        refute_reasons.push(format!(
            "{n_fixture_mismatch}/{} v1 fixture records failed to reproduce via real FFI",
            v1_records.len()
        ));
    }

    // --- (3) v2 fixture: sha, record count, supersedes-not-replaces ---
    let v2_path = format!(
        "{ROOT}/amphora-molecule-role-ranker/reference/phase0-role-known-answer.v2.json"
    );
    let v2_bytes = std::fs::read(&v2_path).expect("v2 fixture readable");
    let v2_sha = sha256_hex(&v2_bytes);
    if v2_sha != V2_SHA_EXPECTED {
        refute_reasons.push(format!(
            "v2 fixture sha256 mismatch: expected {V2_SHA_EXPECTED}, got {v2_sha}"
        ));
    }
    let v2: Value = serde_json::from_slice(&v2_bytes).expect("v2 JSON");
    let v2_records = v2["records"].as_array().expect("v2 records").clone();
    if v2_records.len() != 44 {
        refute_reasons.push(format!(
            "v2 record count expected 44, got {}",
            v2_records.len()
        ));
    }
    let v2_first_39: Vec<Value> = v2_records.iter().take(39).cloned().collect();
    let v1_json_norm: Vec<Value> = v1_records.clone();
    let embedded_byte_identical = v2_first_39 == v1_json_norm;
    if !embedded_byte_identical {
        refute_reasons.push(
            "v2's first 39 records are not structurally identical to v1's 39 records"
                .to_string(),
        );
    }
    // v1 file must exist unmodified on disk at its own path (not deleted, not merged into v2).
    let v1_still_exists_standalone = std::path::Path::new(&v1_path).exists();
    if !v1_still_exists_standalone {
        refute_reasons.push("v1 fixture file no longer exists on disk (would mean replace, not supersede)".to_string());
    }

    // --- (4) KPI harness still reads v1 (v2 not silently substituted in) ---
    let kpi_test_path =
        format!("{ROOT}/amphora-molecule-capabilities/tests/role_ranker_phase0_kpi.rs");
    let kpi_test_src = std::fs::read_to_string(&kpi_test_path).expect("kpi test readable");
    let kpi_binds_v1 = kpi_test_src.contains("phase0-role-known-answer.v1.json");
    let kpi_binds_v2 = kpi_test_src.contains("phase0-role-known-answer.v2.json");
    if !kpi_binds_v1 || kpi_binds_v2 {
        refute_reasons.push(format!(
            "KPI harness fixture binding changed: binds_v1={kpi_binds_v1} binds_v2={kpi_binds_v2} (expected v1 only, unre-baselined)"
        ));
    }

    // --- (1) + novel guanidine-family probes, real FFI ---
    let mut probe_rows = Vec::new();
    let mut n_probe_fail = 0u32;
    let mut n_novel_scored = 0u32;
    for p in probes() {
        let facts = amphora_rdkit_ffi::molecule_facts(p.smiles)
            .unwrap_or_else(|e| panic!("probe {} failed to parse/derive: {e:?}", p.id));
        let role = inferred_role(
            facts.reactive_flags.has_oxirane,
            facts.reactive_flags.has_reactive_amine_hydrogen,
        );
        let formula_ok = facts.formula == p.expected_formula;
        let mw_ok = (facts.average_molecular_weight_g_mol - p.expected_mw).abs() < 0.05;
        let nh_ok = facts.reactive_amine_hydrogen_count == p.expected_amine_h;
        let role_ok = role == p.expected_role;
        let pass = formula_ok && mw_ok && nh_ok && role_ok;
        if !pass {
            n_probe_fail += 1;
        }
        if p.novel {
            n_novel_scored += 1;
        }
        probe_rows.push(json!({
            "id": p.id,
            "novel_vs_r_n02_original_5": p.novel,
            "smiles": p.smiles,
            "citation": p.citation,
            "canonical_isomeric_smiles": facts.canonical_isomeric_smiles,
            "formula": facts.formula,
            "expected_formula": p.expected_formula,
            "formula_matches_published": formula_ok,
            "average_molecular_weight_g_mol": facts.average_molecular_weight_g_mol,
            "expected_mw": p.expected_mw,
            "mw_matches_published": mw_ok,
            "oxirane_ring_count": facts.oxirane_ring_count,
            "reactive_amine_hydrogen_count": facts.reactive_amine_hydrogen_count,
            "expected_reactive_amine_hydrogen_count": p.expected_amine_h,
            "reactive_amine_hydrogen_count_matches_expected": nh_ok,
            "observed_role": role,
            "expected_role": p.expected_role,
            "role_matches_expected": role_ok,
            "pass": pass,
        }));
    }
    if n_probe_fail > 0 {
        refute_reasons.push(format!(
            "{n_probe_fail}/{} probes (incl. novel guanidine-family) failed via real FFI",
            probes().len()
        ));
    }
    if n_novel_scored < 2 {
        refute_reasons.push(format!(
            "only {n_novel_scored} novel guanidine-family probes scored, need >=2"
        ));
    }

    let verdict = if refute_reasons.is_empty() {
        "CLAIM_SURVIVED"
    } else {
        "CLAIM_REFUTED"
    };

    let mut out: BTreeMap<&str, Value> = BTreeMap::new();
    out.insert(
        "schema",
        json!("amphora.molecule-role-ranker.v-n02b-independent-verify.diagnostic.v1"),
    );
    out.insert(
        "toolkit_provenance",
        json!({
            "toolkit": "RDKit C++",
            "detected_version": status.detected_version,
            "exact_version_match": status.exact_version_match,
        }),
    );
    out.insert("v1_fixture_sha256", json!(v1_sha));
    out.insert("v1_fixture_sha256_expected", json!(V1_SHA_EXPECTED));
    out.insert("v1_fixture_n_records", json!(v1_records.len()));
    out.insert("v1_fixture_n_mismatch_via_real_ffi", json!(n_fixture_mismatch));
    out.insert("v1_fixture_rows", json!(fixture_rows));
    out.insert("v2_fixture_sha256", json!(v2_sha));
    out.insert("v2_fixture_sha256_expected", json!(V2_SHA_EXPECTED));
    out.insert("v2_fixture_n_records", json!(v2_records.len()));
    out.insert("v2_embeds_v1_39_records_structurally_identical", json!(embedded_byte_identical));
    out.insert("v1_file_still_exists_standalone", json!(v1_still_exists_standalone));
    out.insert("kpi_harness_binds_v1_only", json!(kpi_binds_v1 && !kpi_binds_v2));
    out.insert("probe_rows", json!(probe_rows));
    out.insert("n_probes_total", json!(probes().len()));
    out.insert("n_probes_novel", json!(n_novel_scored));
    out.insert("n_probes_failed", json!(n_probe_fail));
    out.insert("refute_reasons", json!(refute_reasons));
    out.insert("verdict", json!(verdict));

    println!("{}", serde_json::to_string_pretty(&out).unwrap());
}
