use amphora_rdkit_ffi::molecule_facts;
use serde_json::{json, Value};

struct Probe {
    id: &'static str,
    smiles: &'static str,
    expected_reactive_amine_hydrogen_count: u32,
    category: &'static str,
}

fn main() {
    // Pre-registered probe set. No RNG, no wall clock, fixed hardcoded list.
    let probes: Vec<Probe> = vec![
        // (1) The 5 guanidine-family probes from R-N02's own five_probe_summary,
        // re-derived independently via a freshly-authored harness (not R-N02's own).
        Probe { id: "dpg-diphenylguanidine-accelerator", smiles: "c1ccccc1NC(=N)Nc2ccccc2", expected_reactive_amine_hydrogen_count: 0, category: "r_n02_probe_reattack" },
        Probe { id: "dotg-di-o-tolylguanidine-accelerator", smiles: "Cc1ccccc1NC(=N)Nc2ccccc2C", expected_reactive_amine_hydrogen_count: 0, category: "r_n02_probe_reattack" },
        Probe { id: "guanidine", smiles: "NC(=N)N", expected_reactive_amine_hydrogen_count: 0, category: "r_n02_probe_reattack" },
        Probe { id: "dicyandiamide", smiles: "NC(=NC#N)N", expected_reactive_amine_hydrogen_count: 0, category: "r_n02_probe_reattack" },
        Probe { id: "biguanide", smiles: "NC(=N)NC(=N)N", expected_reactive_amine_hydrogen_count: 0, category: "r_n02_probe_reattack" },
        // (2) Real coating-relevant cycloaliphatic diamine hardener sanity check:
        // must NOT be collaterally over-excluded by the new C=N neighbor rule
        // (no C=N anywhere in this molecule).
        Probe { id: "ipda-isophoronediamine-hardener-sanity", smiles: "CC1(C)CC(CN)CC(N)C1", expected_reactive_amine_hydrogen_count: 4, category: "over_exclusion_regression_probe" },
        // (3) Adversarial whole-molecule over-exclusion probe: agmatine carries a
        // real primary amine structurally REMOTE from an incidental guanidine group.
        // A too-broad, whole-molecule (rather than per-neighbor-carbon) exclusion
        // bug would zero this out; the correctly-scoped fix must not.
        Probe { id: "agmatine-remote-amine-over-exclusion-probe", smiles: "NCCCCNC(N)=N", expected_reactive_amine_hydrogen_count: 2, category: "over_exclusion_regression_probe" },
        // (4) Protonated guanidinium sanity: formal-charge pre-filter must still
        // gate the cationic nitrogen; flanking neutral N-H's remain excluded via
        // the (unmodified) neighbor-carbon C=N check, same as the neutral case.
        Probe { id: "guanidinium-protonated-sanity", smiles: "NC(=[NH2+])N", expected_reactive_amine_hydrogen_count: 0, category: "formal_charge_interaction_sanity" },
    ];

    let mut probe_rows: Vec<Value> = Vec::new();
    let mut n_failed = 0u32;
    for p in &probes {
        let facts = molecule_facts(p.smiles).expect("probe SMILES must parse");
        let observed = facts.reactive_amine_hydrogen_count;
        let pass = observed == p.expected_reactive_amine_hydrogen_count;
        if !pass {
            n_failed += 1;
        }
        probe_rows.push(json!({
            "id": p.id,
            "smiles": p.smiles,
            "canonical_smiles": facts.canonical_isomeric_smiles,
            "category": p.category,
            "expected_reactive_amine_hydrogen_count": p.expected_reactive_amine_hydrogen_count,
            "observed_reactive_amine_hydrogen_count": observed,
            "pass": pass,
        }));
    }

    // Informational (non-refuting, pre-registered as such): disclose two
    // additional behaviors surfaced while probing, neither of which the
    // R-N02 claim under test makes any assertion about.
    let mut informational_rows: Vec<Value> = Vec::new();
    for (id, smiles, note) in [
        (
            "ketimine-self-exclusion-side-effect",
            "CC=N",
            "Primary ketimine >C=N-H: the new rule's neighbor-carbon check fires on \
             the imine's OWN double bond partner (the candidate N itself), so this \
             non-amine imine N-H is now excluded post-fix (was miscounted as 1 \
             pre-fix). This is a positive collateral correctness effect of \
             structural symmetry with is_carbonyl_carbon, not a claim made or \
             tested by R-N02; disclosed as informational only.",
        ),
        (
            "vinylogous-enaminone-conjugation-blind-spot",
            "CC(=O)C=CN",
            "Push-pull enaminone (vinylogous amide): the amine nitrogen's direct \
             neighbor is a vinyl carbon double-bonded to carbon (not O/S/N), so \
             NEITHER the pre-existing carbonyl rule NOR the new C=N rule excludes \
             it, despite real resonance delocalization through the vinyl bridge. \
             This local-neighbor-only design limitation is IDENTICAL in kind and \
             pre-existing for the O/S rule (equally misses vinylogous amides); it \
             is not introduced by, or specific to, the R-N02 C=N fix and is \
             therefore not a valid falsifier of R-N02's claim. Disclosed as an \
             out-of-scope residual gap.",
        ),
    ] {
        let facts = molecule_facts(smiles).expect("probe SMILES must parse");
        informational_rows.push(json!({
            "id": id,
            "smiles": smiles,
            "canonical_smiles": facts.canonical_isomeric_smiles,
            "observed_reactive_amine_hydrogen_count": facts.reactive_amine_hydrogen_count,
            "note": note,
        }));
    }

    let toolkit = amphora_rdkit_ffi::backend_status();

    let verdict = if n_failed == 0 {
        "CLAIM_SURVIVED"
    } else {
        "CLAIM_REFUTED"
    };

    let out = json!({
        "schema": "amphora.rdkit-ffi.v-n02c-verify-diagnostic.v1",
        "n_probes_total": probes.len(),
        "n_probes_failed": n_failed,
        "n_probes_novel_vs_all_prior_r_n02_family_fires": 3, // ipda, agmatine, guanidinium-protonated
        "probe_rows": probe_rows,
        "informational_disclosures": informational_rows,
        "toolkit_provenance": {
            "toolkit": "RDKit C++",
            "required_version": toolkit.required_version,
            "detected_version": toolkit.detected_version,
            "exact_version_match": toolkit.exact_version_match,
        },
        "verdict": verdict,
    });

    println!("{}", serde_json::to_string_pretty(&out).unwrap());
}
