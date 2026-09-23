// role-external-corpus-validation-v1 harness
//
// W-D-ROLE data-dimension attack on the amphora-molecule-role-ranker flagship
// Phase-0 KPI (role-classification-kpi.v1.json,
// structural_inference_agreement_rate=1.0) which is scored ONLY on the
// module's own 44-record self-authored fixture
// (reference/phase0-role-known-answer.v2.json). The W-D-ROLE campaign item's
// claim under attack is that "the role-classification rule can be tested
// against molecules from outside its own fixture." This harness does that
// test directly: it builds real, independently-attested, rights-clean
// external molecules (found and licence-verified in the prior fire's
// 13-source sweep, W-D-ROLE-source-sweep-receipt.v1.dsse.json) and invokes
// the REAL production RDKit C++ FFI (amphora_rdkit_ffi::molecule_facts,
// pinned RDKit 2026.03.2 -- not a Python re-derivation) on them, exactly as
// role-guanidine-accelerator-domain-probe-v1 did for the guanidine chemotype
// that broke the rule.
//
// Five real external probes, none of them fixture-disjoint collisions
// (verified against reference/phase0-role-known-answer.v2.json canonical
// SMILES before this harness was written -- ipda was dropped from the
// candidate set for exactly this reason, it collided):
//   1. dds  -- 4,4'-diaminodiphenyl sulfone, hot-curing aromatic diamine
//              reference amine in Wiegand & Osburg (2023), Polymers 15(4):990,
//              CC BY 4.0, https://doi.org/10.3390/polym15040990
//   2. c5   -- 4-amino-3-methoxybenzylamine ("Compound 5"), a novel
//              vanillin-derived bio-based amine hardener from the same
//              CC BY 4.0 paper, independently DSC/TGA-confirmed as a
//              functional epoxy curing agent (cold-curing, similar to IPDA).
//   3. c6   -- 4-amino-3,5-dimethoxybenzylamine ("Compound 6"), the
//              syringaldehyde-derived analog from the same paper.
//   4. jea  -- a discrete n=5 oligomer analog of BASF Baxxodur EC 302
//              (a polyetheramine described by BASF's own product line as
//              "D 400 analog"), representing the polyetheramine chemotype
//              flagged by the prior sweep as having ZERO fixture
//              representation.
//   5. phk  -- a phenalkamine: a saturated-C15-alkyl-chain, single-Mannich-
//              site TETA (triethylenetetramine) condensation product of
//              cardanol, representing the Cardolite NX-series phenalkamine
//              chemotype (also zero fixture representation). Real
//              commercial phenalkamines use CNSL's mixed mono/di/tri-ene
//              C15 chain (41% triene major component) and are often
//              polysubstituted at more than one Mannich site; this harness
//              uses a simplified saturated single-Mannich-site analog
//              because the role_fit rule under test
//              (has_oxirane=false & reactive_amine_hydrogen_count>0 =>
//              hardener) is insensitive to alkyl-chain saturation state or
//              Mannich-site multiplicity -- it only depends on whether any
//              N-H survives the carbonyl/sulfonyl exclusion, which neither
//              simplification changes.
//
// Plus one POSITIVE CONTROL (compound6-epoxide-contamination): a copy of
// probe c6 with a glycidyl ether group substituted onto one of its OMe
// positions -- a defect of the exact kind this attack exists to catch (an
// externally-sourced hardener record silently contaminated with an
// oxirane, e.g. by a mislabeled/dual-functional supplier sample). Its
// "expected_role" is deliberately left at the ORIGINAL compound 6's
// attested role ("hardener", unchanged) rather than updated for the
// planted defect, so a correctly-functioning harness disagreement check
// must fire on it. This is not a claim that the production code has a
// bug -- it demonstrates that this harness's own pass/fail scoring can
// detect a real structural mismatch when one exists, which is the
// precondition for treating its silence on the five real probes as
// informative rather than vacuous.

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
    is_positive_control: bool,
}

fn probes() -> Vec<Probe> {
    vec![
        Probe {
            id: "dds-diaminodiphenyl-sulfone",
            smiles: "Nc1ccc(cc1)S(=O)(=O)c1ccc(N)cc1",
            citation: "4,4'-Diaminodiphenyl sulfone (DDS), CAS 80-08-0, formula C12H12N2O2S, \
                       MW 248.30. Cited as the hot-curing aromatic-amine reference hardener in \
                       Wiegand & Osburg (2023), 'Synthesis, Curing and Thermal Behavior of Amine \
                       Hardeners from Potentially Renewable Sources', Polymers 15(4):990, \
                       https://doi.org/10.3390/polym15040990 (CC BY 4.0; fetched and license \
                       text confirmed verbatim from https://pmc.ncbi.nlm.nih.gov/articles/PMC9962791/ \
                       in the prior W-D-ROLE sweep fire, source 9).",
            expected_oxirane: 0,
            expected_amine_h: 4,
            expected_role: "hardener",
            note: "real external molecule, canonical SMILES verified disjoint from all 41 \
                   canonical SMILES in reference/phase0-role-known-answer.v2.json (44 records). \
                   Both amines are aniline-type (exocyclic NH2 on an aromatic ring, not an \
                   in-ring pyrrole/imidazole N-H like EMI-24's hostile null), neither adjacent \
                   to the ring's own carbonyl/sulfonyl carbon (the sulfone S is two bonds from \
                   each N, not a direct neighbor), so both should count as reactive amine H.",
            is_positive_control: false,
        },
        Probe {
            id: "compound5-vanillin-derived-amine-hardener",
            smiles: "NCc1cc(OC)c(N)cc1",
            citation: "4-Amino-3-methoxybenzylamine ('Compound 5' in the source paper), \
                       synthesized from vanillin, formula C8H12N2O, MW 152.2 (matches the \
                       paper's reported M+=152). Wiegand & Osburg (2023), Polymers 15(4):990, \
                       https://doi.org/10.3390/polym15040990 (CC BY 4.0). Paper states: 'Two \
                       differently substituted diamines were prepared to act as amine-curing \
                       agents for epoxy resins' and reports DSC onset 71C / Tg 68C, cold-curing \
                       behavior similar to IPDA -- an independent published DSC/TGA cure-\
                       behavior attestation of hardener role, not a supplier TDS claim.",
            expected_oxirane: 0,
            expected_amine_h: 4,
            expected_role: "hardener",
            note: "novel bio-based/renewable amine hardener chemotype (lignin-derived), zero \
                   representation in the 44-record self-authored fixture per the prior sweep's \
                   structural_or_factor_overlap finding. One aromatic (aniline-type) NH2 plus \
                   one aliphatic benzylic CH2NH2, neither carbonyl/sulfonyl-adjacent.",
            is_positive_control: false,
        },
        Probe {
            id: "compound6-syringaldehyde-derived-amine-hardener",
            smiles: "NCc1cc(OC)c(N)c(OC)c1",
            citation: "4-Amino-3,5-dimethoxybenzylamine ('Compound 6' in the source paper), \
                       synthesized from syringaldehyde, formula C9H14N2O2, MW 182.22 (matches \
                       the paper's reported M+=182). Same source and license as compound 5. \
                       Paper reports DSC onset 79C / Tg 160C and TGA thermal stability \
                       'similar to those formed with IPDA'.",
            expected_oxirane: 0,
            expected_amine_h: 4,
            expected_role: "hardener",
            note: "second independent instance of the lignin-derived bio-based amine hardener \
                   chemotype, dimethoxy-substituted analog of compound 5.",
            is_positive_control: false,
        },
        Probe {
            id: "jeffamine-d400-baxxodur-ec302-polyetheramine-analog",
            smiles: "CC(N)COC(C)COC(C)COC(C)COC(C)COC(C)CN",
            citation: "Discrete n=5 oligomer analog of a poly(propylene glycol) diamine \
                       polyetheramine (Jeffamine/Baxxodur-class; BASF's own Baxxodur EC-1xx/2xx/3xx \
                       product-line description states 'EC 302 = polyetheramine D 400 analog', \
                       fetched verbatim from basf.com/global/en/legal.html + product pages in the \
                       prior W-D-ROLE sweep fire, source 4). Commercial Jeffamine/Baxxodur \
                       polyetheramine products are average-MW mixtures over a distribution of \
                       n; this harness uses a single discrete n=5 oligomer (MW 364.5) as a \
                       structural representative, matching how the portfolio's own DGEBA \
                       oligomer-series receipts already handle polymeric analogs with an \
                       explicit n.",
            expected_oxirane: 0,
            expected_amine_h: 4,
            expected_role: "hardener",
            note: "polyetheramine chemotype, zero representation in the 44-record fixture per \
                   the prior sweep's structural_or_factor_overlap finding. Two terminal primary \
                   amines on secondary carbons, polyether backbone, no carbonyl/sulfonyl \
                   neighbor to either amine nitrogen.",
            is_positive_control: false,
        },
        Probe {
            id: "phenalkamine-cardanol-teta-mannich-base",
            smiles: "Oc1cc(CCCCCCCCCCCCCCC)ccc1CNCCNCCNCCN",
            citation: "Simplified single-Mannich-site phenalkamine: cardanol (a C15-alkyl-\
                       substituted phenol from cashew nutshell liquid, CNSL) condensed with \
                       formaldehyde and triethylenetetramine (TETA) via the Mannich reaction, \
                       the synthesis route documented for Cardolite NX-series phenalkamine \
                       curing agents (cardolite.com/phenalkamines/, prior W-D-ROLE sweep fire \
                       source 5) and in the open cure-chemistry literature (e.g. Jaillet et al. \
                       and related cardanol-Mannich-base curing-kinetics studies of phenalkamines \
                       synthesized from polyethylenepolyamines). Uses a saturated C15 alkyl \
                       chain in place of real cardanol's mixed mono/di/tri-ene chain (41% triene \
                       major component) -- immaterial to the has_oxirane/reactive_amine_hydrogen \
                       rule under test, which does not inspect the alkyl tail.",
            expected_oxirane: 0,
            expected_amine_h: 5,
            expected_role: "hardener",
            note: "phenalkamine chemotype, zero representation in the 44-record fixture per the \
                   prior sweep's structural_or_factor_overlap finding -- flagged there as \
                   directly analogous in kind to the guanidine gap that broke the rule once \
                   already (a whole chemotype family absent from the self-authored fixture). \
                   Three secondary benzylamine/polyamine N-H (1H each) plus one terminal \
                   primary N-H2 (2H) = 5 reactive amine H expected; none adjacent to a \
                   carbonyl/sulfonyl carbon or sulfur. Phenalkamines are formulated as the \
                   stoichiometric hardener component in industry TDS/literature (unlike DPG/ \
                   DOTG guanidine accelerators, which are never listed as curing agents and are \
                   used at sub-stoichiometric catalytic loadings), so 'hardener' is the correct \
                   attested expectation, not a repeat of the guanidine failure mode.",
            is_positive_control: false,
        },
        Probe {
            id: "compound6-epoxide-contamination-positive-control",
            smiles: "NCc1cc(OCC2CO2)c(N)c(OC)c1",
            citation: "POSITIVE CONTROL, not an external source citation. Constructed in-harness \
                       by substituting one of compound 6's two OMe groups with a glycidyl ether \
                       (-O-CH2-[oxirane]) group, simulating a mislabeled or dual-functional-\
                       contaminated external sample filed under compound 6's original attested \
                       role. planted_defect: added one oxirane ring to a real external hardener's \
                       structure while leaving expected_role at the ORIGINAL 'hardener' label \
                       (not updated for the defect). If this harness's disagreement-detection is \
                       working, observed_role must come back 'ambiguous' (oxirane present AND \
                       amine H present) and register a disagreement against the stale 'hardener' \
                       expectation.",
            expected_oxirane: 0,
            expected_amine_h: 4,
            expected_role: "hardener",
            note: "expected_oxirane and expected_role are DELIBERATELY the pre-defect values \
                   (compound 6's real, correct attestation), not the correct facts for this \
                   mutated structure -- the mismatch against reality is the planted defect. The \
                   attack fires (a disagreement is recorded) if and only if this harness's \
                   scoring can detect the injected structural mismatch.",
            is_positive_control: true,
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
    let mut real_probe_pass = 0u32;
    let mut real_probe_total = 0u32;
    let mut positive_control_fired = false;

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
                "is_positive_control": p.is_positive_control,
            }));
        }
        if p.is_positive_control {
            if !pass {
                positive_control_fired = true;
            }
        } else {
            real_probe_total += 1;
            if pass {
                real_probe_pass += 1;
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
            "is_positive_control": p.is_positive_control,
            "expected_oxirane_ring_count": p.expected_oxirane,
            "expected_reactive_amine_hydrogen_count": p.expected_amine_h,
            "expected_role": p.expected_role,
            "observed_oxirane_ring_count": facts.oxirane_ring_count,
            "observed_reactive_amine_hydrogen_count": facts.reactive_amine_hydrogen_count,
            "observed_role": role,
            "pass": pass,
        }));
    }

    let real_probes_all_agree = real_probe_pass == real_probe_total;
    let verdict = if !real_probes_all_agree {
        "HYPOTHESIS_REFUTED"
    } else if positive_control_fired {
        "HYPOTHESIS_SURVIVED_WITH_POSITIVE_CONTROL"
    } else {
        "HYPOTHESIS_SURVIVED_NO_POSITIVE_CONTROL_UNRELIABLE"
    };

    let mut out: BTreeMap<&str, Value> = BTreeMap::new();
    out.insert(
        "schema",
        json!("amphora.molecule-role-ranker.role-external-corpus-validation-v1.diagnostic.v1"),
    );
    out.insert(
        "purpose",
        json!(
            "W-D-ROLE data-dimension attack: tests the amphora-molecule-role-ranker flagship \
             Phase-0 KPI (role-classification-kpi.v1.json, \
             structural_inference_agreement_rate=1.0, scored ONLY on the module's own \
             44-record self-authored fixture) against 5 real, independently-attested, \
             rights-clean external molecules found and licence-verified in the prior W-D-ROLE \
             sweep fire, invoking the REAL production RDKit C++ FFI. Plus 1 positive control \
             probe verifying this harness's own disagreement-detection fires on a planted \
             defect."
        ),
    );
    out.insert("toolkit_provenance", json!(status));
    out.insert("results", json!(results));
    out.insert(
        "summary",
        json!({
            "n_scored_probes": scored_total,
            "n_pass": scored_pass,
            "n_disagreements": disagreements.len() as u32,
            "n_real_external_probes": real_probe_total,
            "n_real_external_probes_pass": real_probe_pass,
            "real_probes_all_agree": real_probes_all_agree,
            "positive_control_fired": positive_control_fired,
        }),
    );
    out.insert("disagreements", json!(disagreements));
    out.insert("verdict", json!(verdict));

    println!("{}", serde_json::to_string_pretty(&out).unwrap());
}
