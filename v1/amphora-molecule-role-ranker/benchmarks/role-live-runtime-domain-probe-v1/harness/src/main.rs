// role-live-runtime-domain-probe-v1 harness
//
// Calls the REAL production RDKit C++ FFI (amphora_rdkit_ffi::molecule_facts,
// which invokes amphora-rdkit-ffi/src/bridge.cc count_oxirane_rings and
// count_reactive_amine_hydrogens byte-identically to the live checked
// amphora-molecule-role-ranker runtime) on a curated set of REAL, published,
// coating-relevant epoxy/amine molecules that are held out of the module's
// self-authored 39-record known-answer fixture
// (phase0-role-known-answer.v1.json, sha 8ce4d541...). Applies the module's
// own documented zero-parameter deterministic role rule (inferred_role in
// amphora-molecule-capabilities/src/lib.rs: oxirane & !amine -> resin;
// amine & !oxirane -> hardener; both -> ambiguous; neither -> out_of_domain)
// and checks agreement against structurally hand-derived ground truth for
// each named, cited compound. No fitted parameters; no re-implementation of
// chemistry -- this is the identical production binary logic under new inputs.

use serde_json::{json, Value};
use std::collections::BTreeMap;

struct Probe {
    id: &'static str,
    smiles: &'static str,
    citation: &'static str,
    expected_oxirane: Option<u32>,
    expected_amine_h: Option<u32>,
    expected_role: Option<&'static str>,
    note: &'static str,
}

fn probes() -> Vec<Probe> {
    vec![
        Probe {
            id: "erl4221-cycloaliphatic-diepoxide",
            smiles: "C1(COC(=O)C2CC3OC3CC2)CC4OC4CC1",
            citation: "3,4-epoxycyclohexylmethyl 3,4-epoxycyclohexanecarboxylate (ERL-4221 / \
                       Dow CAS 2386-87-0, PubChem CID 68563), formula C14H20O4 MW 252.30",
            expected_oxirane: Some(2),
            expected_amine_h: Some(0),
            expected_role: Some("resin"),
            note: "cycloaliphatic (non-glycidyl-ether) diepoxide resin adjacent to an ester \
                   carbonyl; fixture only carries glycidyl-ether/aromatic oxiranes plus one \
                   plain cyclohexene oxide, none ester-adjacent",
        },
        Probe {
            id: "edr148-triethyleneglycol-diamine",
            smiles: "NCCOCCOCCOCCN",
            citation: "4,7,10-trioxatridecane-1,13-diamine (Jeffamine EDR-148, CAS 929-59-9), \
                       formula C10H24N2O3 MW 220.31",
            expected_oxirane: Some(0),
            expected_amine_h: Some(4),
            expected_role: Some("hardener"),
            note: "real commercial ether-backbone diamine hardener class, absent from fixture \
                   (fixture diamines are all alkylene/aromatic/cycloaliphatic, no ether linkage)",
        },
        Probe {
            id: "aep-aminoethylpiperazine",
            smiles: "NCCN1CCNCC1",
            citation: "1-(2-aminoethyl)piperazine (AEP, CAS 140-31-8)",
            expected_oxirane: Some(0),
            expected_amine_h: Some(3),
            expected_role: Some("hardener"),
            note: "mixed primary(2H)+secondary-ring(1H)+tertiary-ring(0H) nitrogen in one \
                   molecule; fixture's only piperazine (ambiguous-glycidyl-piperazine) has no \
                   free ring N-H",
        },
        Probe {
            id: "aspartic-ester-secondary-amine",
            smiles: "CCCCNC(CC(=O)OCC)C(=O)OCC",
            citation: "diethyl 2-(butylamino)succinate -- monofunctional model of the \
                       Michael-adduct secondary amine in commercial aspartic-ester hardeners \
                       (e.g. Desmophen NH-series polyaspartics used in fast-cure protective/\
                       marine topcoats)",
            expected_oxirane: Some(0),
            expected_amine_h: Some(1),
            expected_role: Some("hardener"),
            note: "secondary amine N whose alpha-carbon itself bears a direct ester substituent \
                   (N-CH(CO2Et)-CH2CO2Et); tests that the carbonyl exclusion looks at the \
                   nitrogen's DIRECT neighbor atom (must not be a carbonyl carbon) and does not \
                   over-exclude a non-carbonyl alpha-carbon merely adjacent to an ester group",
        },
        Probe {
            id: "bdma-tertiary-amine-accelerator",
            smiles: "CN(C)Cc1ccccc1",
            citation: "N,N-dimethylbenzylamine (BDMA, CAS 103-83-3), a common epoxy cure \
                       accelerator/catalyst, not a stoichiometric hardener",
            expected_oxirane: Some(0),
            expected_amine_h: Some(0),
            expected_role: Some("out_of_domain"),
            note: "hostile-null: a real catalyst molecule must fail closed (no reactive N-H), \
                   not be silently promoted to hardener stoichiometry",
        },
        Probe {
            id: "emi24-imidazole-latent-hardener",
            smiles: "Cc1c[nH]c(CC)n1",
            citation: "2-ethyl-4-methylimidazole (EMI-24, CAS 931-36-2), a latent epoxy curing \
                       agent that cures by anionic ring-opening homopolymerisation initiation, \
                       not stoichiometric amine N-H addition",
            expected_oxirane: Some(0),
            expected_amine_h: Some(0),
            expected_role: Some("out_of_domain"),
            note: "hostile-null: the ring N-H is aromatic (pyrrole-type); counting it as a \
                   reactive amine hydrogen would fabricate a chemically meaningless AHEW for a \
                   catalyst whose real mechanism is not N-H addition",
        },
        Probe {
            id: "dds-diaminodiphenylsulfone",
            smiles: "Nc1ccc(cc1)S(=O)(=O)c1ccc(N)cc1",
            citation: "4,4'-diaminodiphenyl sulfone (DDS, CAS 80-08-0), a widely used \
                       high-Tg aromatic diamine curing agent",
            expected_oxirane: Some(0),
            expected_amine_h: Some(4),
            expected_role: Some("hardener"),
            note: "tests that the sulfonyl exclusion (correctly scoped to a nitrogen's direct \
                   sulfonyl neighbor per bridge.cc is_sulfonyl_sulfur) does not over-reach to an \
                   unrelated sulfone many bonds from the reactive anilines",
        },
        Probe {
            id: "ddm-diaminodiphenylmethane",
            smiles: "Nc1ccc(Cc2ccc(N)cc2)cc1",
            citation: "4,4'-diaminodiphenylmethane (DDM/MDA, CAS 101-77-9), common aromatic \
                       diamine hardener and precursor of the fixture's tgddm resin",
            expected_oxirane: Some(0),
            expected_amine_h: Some(4),
            expected_role: Some("hardener"),
            note: "the free diamine itself is absent from the fixture (only its \
                   tetraglycidyl derivative, resin-tgddm, is present)",
        },
        Probe {
            id: "detda-hindered-aromatic-diamine",
            smiles: "Cc1c(N)c(CC)cc(CC)c1N",
            citation: "diethyltoluenediamine (DETDA / Ethacure 100 congener, CAS 68479-98-1), \
                       sterically hindered fast-cure aromatic diamine hardener",
            expected_oxirane: Some(0),
            expected_amine_h: Some(4),
            expected_role: Some("hardener"),
            note: "alkyl-flanked (sterically hindered) aniline nitrogens; structural rule is \
                   silent on steric hindrance by design (kinetics, not stoichiometry) -- checks \
                   the handle still fires",
        },
        Probe {
            id: "dicy-dicyandiamide",
            smiles: "NC(=N)NC#N",
            citation: "dicyandiamide (DICY, CAS 461-58-5), the most common latent one-part \
                       epoxy hardener",
            expected_oxirane: None,
            expected_amine_h: None,
            expected_role: None,
            note: "OPEN CHEMISTRY QUESTION, not scored pass/fail: DICY cures through a complex \
                   catalysed nitrile-addition/cyclisation mechanism, not simple 1:1 N-H:epoxide \
                   stoichiometry, so there is no uncontested 'correct' reactive_amine_hydrogen_\
                   count for AHEW purposes. Recorded for the module's docs/mission.md known-\
                   contradictions register, not as a refutation.",
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
        let scored = p.expected_role.is_some();
        let pass = match (p.expected_oxirane, p.expected_amine_h, p.expected_role) {
            (Some(eo), Some(ea), Some(er)) => {
                facts.oxirane_ring_count == eo
                    && facts.reactive_amine_hydrogen_count == ea
                    && role == er
            }
            _ => true,
        };
        if scored {
            scored_total += 1;
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
        }
        results.push(json!({
            "id": p.id,
            "smiles": p.smiles,
            "canonical_isomeric_smiles": facts.canonical_isomeric_smiles,
            "formula": facts.formula,
            "average_molecular_weight_g_mol": facts.average_molecular_weight_g_mol,
            "citation": p.citation,
            "note": p.note,
            "scored": scored,
            "expected_oxirane_ring_count": p.expected_oxirane,
            "expected_reactive_amine_hydrogen_count": p.expected_amine_h,
            "expected_role": p.expected_role,
            "observed_oxirane_ring_count": facts.oxirane_ring_count,
            "observed_reactive_amine_hydrogen_count": facts.reactive_amine_hydrogen_count,
            "observed_role": role,
            "pass": if scored { Some(pass) } else { None },
        }));
    }

    let mut out: BTreeMap<&str, Value> = BTreeMap::new();
    out.insert(
        "schema",
        json!("amphora.molecule-role-ranker.role-live-runtime-domain-probe-v1.diagnostic.v1"),
    );
    out.insert(
        "purpose",
        json!(
            "Falsification attack on the amphora-molecule-role-ranker flagship Phase-0 KPI \
             (role-classification-kpi.v1.json, structural_inference_agreement_rate=1.0) by \
             invoking the REAL production RDKit C++ FFI (amphora-rdkit-ffi molecule_facts, \
             pinned RDKit 2026.03.2, the same bridge.cc logic the live checked Rust runtime \
             uses) on real, named, cited, coating-relevant molecules held out of the self-\
             authored 39-record known-answer fixture."
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
    out.insert(
        "results",
        Value::Array(results),
    );
    out.insert(
        "summary",
        json!({
            "n_scored_probes": scored_total,
            "n_pass": scored_pass,
            "n_disagreements": disagreements.len() as u32,
            "n_open_question_probes_not_scored": (probes().len() as u32) - scored_total,
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
