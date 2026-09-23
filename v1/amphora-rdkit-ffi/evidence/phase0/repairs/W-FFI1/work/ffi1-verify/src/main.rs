use amphora_rdkit_ffi::molecule_facts;
use serde_json::{json, Value};

// W-FFI1: validate count_reactive_amine_hydrogens (bridge.cc) against the
// PUBLISHED active-hydrogen convention (Lee & Neville 1967, Handbook of Epoxy
// Resins) across amine classes, using the REAL production FFI (not a
// reimplementation). Pre-registered probe set. No RNG, no wall clock, fixed
// hardcoded list, deterministic serde_json output.
struct Probe {
    id: &'static str,
    smiles: &'static str,
    class: &'static str,
    published_active_h: u32,
    published_source: &'static str,
    // Some class members carry an independently-published molecular formula
    // and/or molecular weight we can cross-check the toolkit's own facts
    // against, strengthening the external-anchoring of the expectation.
    expect_formula: Option<&'static str>,
    expect_mw_g_mol: Option<f64>,
}

fn main() {
    let probes: Vec<Probe> = vec![
        // ---- primary aliphatic ----
        Probe {
            id: "eda-ethylenediamine",
            smiles: "NCCN",
            class: "primary_aliphatic",
            published_active_h: 4,
            published_source: "Lee & Neville 1967, Handbook of Epoxy Resins (McGraw-Hill), curing-agent table; CAS 107-15-3, MW 60.10, AHEW 15.03 (2 x primary NH2, universally tabulated)",
            expect_formula: Some("C2H8N2"),
            expect_mw_g_mol: Some(60.10),
        },
        // ---- secondary aliphatic ----
        Probe {
            id: "piperazine-anhydrous",
            smiles: "C1CNCCN1",
            class: "secondary_aliphatic",
            published_active_h: 2,
            published_source: "Lee & Neville 1967 counting convention applied to CAS 110-85-0: two ring secondary-amine N-H, no aromaticity/carbonyl/amidine exclusion applicable -- unambiguous under the convention itself, not a disputed empirical figure",
            expect_formula: Some("C4H10N2"),
            expect_mw_g_mol: Some(86.14),
        },
        // ---- tertiary aliphatic (zero-active-H control) ----
        Probe {
            id: "triethylamine-tertiary-control",
            smiles: "CCN(CC)CC",
            class: "tertiary_aliphatic",
            published_active_h: 0,
            published_source: "Definitional baseline of the AHEW convention itself (Lee & Neville 1967): a tertiary amine nitrogen bears no N-H and contributes zero active hydrogen",
            expect_formula: Some("C6H15N"),
            expect_mw_g_mol: Some(101.19),
        },
        // ---- cycloaliphatic ----
        Probe {
            id: "ipda-isophoronediamine",
            smiles: "CC1(C)CC(N)CC(C)(CN)C1",
            class: "cycloaliphatic",
            published_active_h: 4,
            published_source: "Evonik/Huntsman IPDA TDS, CAS 2855-13-2, MW 170.30, AHEW ~42.5 g/eq widely tabulated (also the in-tree known_answer_amines entry, hardener_stoichiometric_envelope.v1.json)",
            expect_formula: Some("C10H22N2"),
            expect_mw_g_mol: Some(170.30),
        },
        // ---- aromatic, direct N-aryl ----
        Probe {
            id: "mda-ddm-diaminodiphenylmethane",
            smiles: "Nc1ccc(Cc2ccc(N)cc2)cc1",
            class: "aromatic_direct",
            published_active_h: 4,
            published_source: "Lee & Neville 1967 curing-agent table, CAS 101-77-9, MW 198.26, AHEW ~49.6 g/eq widely tabulated (also the in-tree known_answer_amines entry)",
            expect_formula: Some("C13H14N2"),
            expect_mw_g_mol: Some(198.26),
        },
        Probe {
            id: "dds-diaminodiphenylsulfone",
            smiles: "Nc1ccc(S(=O)(=O)c2ccc(N)cc2)cc1",
            class: "aromatic_direct",
            published_active_h: 4,
            published_source: "Lee & Neville 1967 curing-agent table, CAS 80-08-0, MW 248.30, AHEW ~62.1 g/eq widely tabulated (also the in-tree known_answer_amines entry)",
            expect_formula: Some("C12H12N2O2S"),
            expect_mw_g_mol: Some(248.30),
        },
        // ---- hindered aromatic (steric hindrance affects cure kinetics, not
        // the stoichiometric N-H count under the convention) ----
        Probe {
            id: "detda-ethacure100-hindered-aromatic",
            smiles: "Cc1c(N)c(CC)cc(CC)c1N",
            class: "hindered_aromatic",
            published_active_h: 4,
            published_source: "Albemarle ETHACURE 100 Curative TDS, CAS 68479-98-1, molecular formula C11H18N2, MW 178.28 (confirmed via SpecialChem/ChemicalBook product data, independent of this repo); two primary aromatic amines, steric ethyl-hindrance slows cure rate but does not change the active-hydrogen count under the convention",
            expect_formula: Some("C11H18N2"),
            expect_mw_g_mol: Some(178.28),
        },
        // ---- amide (must be EXCLUDED under the convention) ----
        Probe {
            id: "n-2-aminoethyl-acetamide",
            smiles: "CC(=O)NCCN",
            class: "amide",
            published_active_h: 2,
            published_source: "Lee & Neville 1967 convention: amide/imide N-H is not counted as active hydrogen for epoxide-curing stoichiometry (amide N is far less nucleophilic than amine N at ambient/moderate cure temperatures); model compound for the amide linkages present in polyamidoamine hardeners -- only the terminal primary amine's 2 H are active",
            expect_formula: Some("C4H10N2O"),
            expect_mw_g_mol: Some(102.14),
        },
        // ---- polyamine oligomers (already in-tree known_answer_amines) ----
        Probe {
            id: "deta-diethylenetriamine",
            smiles: "NCCNCCN",
            class: "polyamine_oligomer",
            published_active_h: 5,
            published_source: "Union Carbide/Huntsman DETA TDS, CAS 111-40-0, MW 103.17, AHEW ~20.6; in-tree known_answer_amines (hardener_stoichiometric_envelope.v1.json)",
            expect_formula: Some("C4H13N3"),
            expect_mw_g_mol: Some(103.17),
        },
        Probe {
            id: "teta-triethylenetetramine",
            smiles: "NCCNCCNCCN",
            class: "polyamine_oligomer",
            published_active_h: 6,
            published_source: "Union Carbide/Huntsman TETA TDS, CAS 112-24-3, MW 146.23, AHEW ~24.4; in-tree known_answer_amines",
            expect_formula: Some("C6H18N4"),
            expect_mw_g_mol: Some(146.23),
        },
        Probe {
            id: "tepa-tetraethylenepentamine",
            smiles: "NCCNCCNCCNCCN",
            class: "polyamine_oligomer",
            published_active_h: 7,
            published_source: "Union Carbide/Huntsman TEPA TDS, CAS 112-57-2, MW 189.30, AHEW ~27.0; in-tree known_answer_amines",
            expect_formula: Some("C8H23N5"),
            expect_mw_g_mol: Some(189.30),
        },
        // ---- amidine/guanidine: catalytic accelerator sub-class (weak,
        // fully-delocalized bases; NOT sold or used as stoichiometric
        // hardeners; R-N02/V-N02c precedent) ----
        Probe {
            id: "guanidine-accelerator",
            smiles: "NC(=N)N",
            class: "amidine_guanidine_accelerator",
            published_active_h: 0,
            published_source: "R-N02/V-N02c precedent: guanidine is used as a strong, fully-delocalized non-nucleophilic base/accelerator, never marketed or dosed as a stoichiometric epoxy hardener; no TDS lists an AHEW for it",
            expect_formula: None,
            expect_mw_g_mol: None,
        },
        Probe {
            id: "dpg-diphenylguanidine-accelerator",
            smiles: "c1ccccc1NC(=N)Nc2ccccc2",
            class: "amidine_guanidine_accelerator",
            published_active_h: 0,
            published_source: "R-N02/V-N02c precedent: DPG is a rubber/epoxy cure accelerator dosed at phr levels far below stoichiometric amine-hydrogen dosing; no TDS lists an AHEW for it",
            expect_formula: None,
            expect_mw_g_mol: None,
        },
        // ---- amidine/guanidine: STOICHIOMETRIC HARDENER sub-class --
        // dicyandiamide (DICY) is dosed near-stoichiometrically in real
        // production epoxy coatings and powder coatings, unlike the pure
        // accelerators above. This is the pre-registered refuting probe. ----
        Probe {
            id: "dicy-dicyandiamide-hardener",
            smiles: "NC(=NC#N)N",
            class: "amidine_guanidine_hardener",
            published_active_h: 4,
            published_source: "WO1993010168A1 'Bis-dicyandiamides as curing agents for epoxy resins' (1993), explicit quote: \"dicyandiamide (cyanoguanidine) has a defined degree of functionality of four, that is, it is capable of addition to four epoxide radicals\"; corroborated independently by multiple epoxy-curing patent/technical sources describing dicyandiamide as possessing four active hydrogens (with some literature noting apparent 3-active-hydrogen kinetic behavior, but never zero)",
            expect_formula: Some("C2H4N4"),
            expect_mw_g_mol: Some(84.08),
        },
    ];

    let mut rows: Vec<Value> = Vec::new();
    let mut n_class_mismatch = 0u32;
    let mut n_formula_or_mw_mismatch = 0u32;
    for p in &probes {
        let facts = molecule_facts(p.smiles).expect("probe SMILES must parse");
        let observed = facts.reactive_amine_hydrogen_count;
        let matches_published = observed == p.published_active_h;
        if !matches_published {
            n_class_mismatch += 1;
        }
        let formula_ok = p.expect_formula.map(|f| f == facts.formula).unwrap_or(true);
        let mw_ok = p
            .expect_mw_g_mol
            .map(|mw| (facts.average_molecular_weight_g_mol - mw).abs() < 0.05)
            .unwrap_or(true);
        if !(formula_ok && mw_ok) {
            n_formula_or_mw_mismatch += 1;
        }
        let observed_ahew = if observed > 0 {
            Some(facts.average_molecular_weight_g_mol / observed as f64)
        } else {
            None
        };
        rows.push(json!({
            "id": p.id,
            "smiles": p.smiles,
            "canonical_smiles": facts.canonical_isomeric_smiles,
            "class": p.class,
            "observed_formula": facts.formula,
            "expected_formula": p.expect_formula,
            "formula_matches": formula_ok,
            "observed_mw_g_mol": facts.average_molecular_weight_g_mol,
            "expected_mw_g_mol": p.expect_mw_g_mol,
            "mw_matches_within_0.05": mw_ok,
            "observed_reactive_amine_hydrogen_count": observed,
            "published_active_hydrogen_count": p.published_active_h,
            "matches_published_convention": matches_published,
            "observed_ahew_g_per_eq": observed_ahew,
            "published_source": p.published_source,
        }));
    }

    let n_classes: std::collections::BTreeSet<&str> =
        probes.iter().map(|p| p.class).collect();
    let mut per_class_verdict: Vec<Value> = Vec::new();
    for class in &n_classes {
        let class_rows: Vec<&Value> = rows
            .iter()
            .filter(|r| r["class"] == *class)
            .collect();
        let all_match = class_rows
            .iter()
            .all(|r| r["matches_published_convention"] == true);
        per_class_verdict.push(json!({
            "class": class,
            "n_members": class_rows.len(),
            "all_members_match_published_convention": all_match,
            "verdict": if all_match { "CLAIM_SURVIVED_FOR_CLASS" } else { "CLAIM_REFUTED_FOR_CLASS" },
        }));
    }

    let toolkit = amphora_rdkit_ffi::backend_status();

    let overall_verdict = if n_class_mismatch == 0 {
        "CLAIM_SURVIVED"
    } else {
        "CLAIM_REFUTED"
    };

    let out = json!({
        "schema": "amphora.rdkit-ffi.w-ffi1-ahew-class-validation-diagnostic.v1",
        "n_probes_total": probes.len(),
        "n_probes_mismatching_published_convention": n_class_mismatch,
        "n_probes_formula_or_mw_mismatch": n_formula_or_mw_mismatch,
        "probe_rows": rows,
        "per_class_verdict": per_class_verdict,
        "toolkit_provenance": {
            "toolkit": "RDKit C++",
            "required_version": toolkit.required_version,
            "detected_version": toolkit.detected_version,
            "exact_version_match": toolkit.exact_version_match,
        },
        "verdict": overall_verdict,
    });

    println!("{}", serde_json::to_string_pretty(&out).unwrap());
}
