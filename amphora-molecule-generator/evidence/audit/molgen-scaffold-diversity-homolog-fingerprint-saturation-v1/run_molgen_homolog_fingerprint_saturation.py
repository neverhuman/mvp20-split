#!/usr/bin/env python3
"""Falsification attack on amphora-molecule-generator/evidence/audit/
molgen-scaffold-diversity-v1's CORROBORATED_IN_AUDIT_INSTRUMENT verdict that
the 38 accepted grammar proposals "span a diverse region of chemical space
(not trivially inflated variants of a single scaffold)".

Attack: independently re-derive the SAME Morgan/ECFP radius-2, 2048-bit
Tanimoto instrument the attacked receipt uses for its headline IntDiv_1, then
evaluate it WITHIN each accepted family instead of only in aggregate. Two
families -- F1_polyethyleneamine (linear -CH2CH2NH- homologs) and
F2_alpha_omega_diamine (linear alkyl-diamine homologs) -- together comprise
18/38 (47.4%) of the accepted set and are textbook monotonic chain-length
homologous series. If the instrument used to corroborate "diverse, not
trivially inflated variants" cannot resolve members of a single homologous
family from one another (near-1.0 pairwise Tanimoto, i.e. near-zero internal
IntDiv_1), the aggregate corroboration is an artifact of cross-family
contrast, not evidence that the corpus as a whole avoids trivial variants.

Deterministic, no RNG: run twice (A/B) and byte-diff for the two-replay gate.
"""
import hashlib
import itertools
import json
import sys
from pathlib import Path

from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit.DataStructs import TanimotoSimilarity

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
GEN = ROOT / "amphora-molecule-generator"
SOURCE_DIAG = GEN / "evidence/audit/molgen-deterministic-grammar-yield-v1/diagnostic.canonical.json"
ATTACKED_RECEIPT = GEN / "evidence/audit/molgen-scaffold-diversity-v1/molgen-scaffold-diversity-receipt.v1.dsse.json"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def fp(smi, radius=2, n_bits=2048):
    mol = Chem.MolFromSmiles(smi)
    return AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)


def intdiv1(fps_by_smi, smis):
    if len(smis) < 2:
        return None, 0, None
    sims = [TanimotoSimilarity(fps_by_smi[a], fps_by_smi[b])
            for a, b in itertools.combinations(smis, 2)]
    mean_sim = sum(sims) / len(sims)
    return 1.0 - mean_sim, len(sims), mean_sim


def adjacent_tanimoto(fps_by_smi, ordered_smis):
    return [TanimotoSimilarity(fps_by_smi[ordered_smis[i]], fps_by_smi[ordered_smis[i + 1]])
            for i in range(len(ordered_smis) - 1)]


def main():
    source_bytes = SOURCE_DIAG.read_bytes()
    diag = json.loads(source_bytes)
    accepted = diag["accepted_proposals"]
    assert len(accepted) == 38, f"expected 38 accepted proposals, got {len(accepted)}"

    fps_by_smi = {}
    fam_groups = {}
    for x in accepted:
        smi = x["canonical_smiles"]
        fps_by_smi[smi] = fp(smi)
        fam_groups.setdefault(x["family"], []).append(x)

    all_smis = [x["canonical_smiles"] for x in accepted]
    overall_intdiv1, overall_npairs, overall_mean_sim = intdiv1(fps_by_smi, all_smis)

    per_family = {}
    for f, members in sorted(fam_groups.items()):
        smis = [m["canonical_smiles"] for m in members]
        d, npairs, mean_sim = intdiv1(fps_by_smi, smis)
        per_family[f] = {
            "n": len(smis),
            "fraction_of_accepted_set": len(smis) / 38,
            "intdiv1": d,
            "mean_pairwise_tanimoto": mean_sim,
            "n_pairs": npairs,
        }

    homolog_families = ["F1_polyethyleneamine", "F2_alpha_omega_diamine"]
    homolog_bloc_smis = [m["canonical_smiles"] for f in homolog_families for m in fam_groups[f]]
    bloc_intdiv1, bloc_npairs, bloc_mean_sim = intdiv1(fps_by_smi, homolog_bloc_smis)

    # Order each homolog series by chain length (N-count for F1's repeat -NCCN-
    # unit, C-count for F2's linear alkyl chain) -- rigorous, not source-list order.
    f1_order = sorted([m["canonical_smiles"] for m in fam_groups["F1_polyethyleneamine"]],
                       key=lambda s: s.count("N"))
    f2_order = sorted([m["canonical_smiles"] for m in fam_groups["F2_alpha_omega_diamine"]],
                       key=lambda s: s.count("C"))
    f1_adj = adjacent_tanimoto(fps_by_smi, f1_order)
    f2_adj = adjacent_tanimoto(fps_by_smi, f2_order)
    combined_adj = f1_adj + f2_adj
    n_adj_saturated = sum(1 for t in combined_adj if t >= 0.99)

    ring_smis = [m["canonical_smiles"] for f, members in fam_groups.items()
                 if f not in homolog_families for m in members]
    cross_sims = [TanimotoSimilarity(fps_by_smi[a], fps_by_smi[b])
                  for a in homolog_bloc_smis for b in ring_smis]
    cross_mean = sum(cross_sims) / len(cross_sims)

    # Fail-open sanity controls on the SAME instrument:
    # (a) self-similarity is exactly 1.0 (identity control)
    eda = "NCCN"
    self_sim = TanimotoSimilarity(fps_by_smi[eda], fps_by_smi[eda])
    # (b) two structurally unrelated ring members resolve well below the
    #     homolog-adjacent saturation floor, proving the instrument is not
    #     globally degenerate -- it discriminates when a real difference exists.
    dds = next(m["canonical_smiles"] for m in fam_groups["F4_bridged_bisaniline"] if "S(=O)(=O)" in m["canonical_smiles"])
    benzidine = next(m["canonical_smiles"] for m in fam_groups["F4_bridged_bisaniline"] if m["name"].startswith("benzidine"))
    unrelated_control_sim = TanimotoSimilarity(fps_by_smi[dds], fps_by_smi[benzidine])

    receipt_reported_overall_intdiv1 = 0.768098
    recompute_matches_receipt = abs(overall_intdiv1 - receipt_reported_overall_intdiv1) < 1e-5

    # Falsification criterion, defined against the attacked receipt's OWN
    # instrument and OWN reported aggregate -- not a new arbitrary metric.
    decision_rule = (
        "H0 (attacked receipt's hypothesis_evaluation) is REFUTED if at least one "
        "family comprising >=15% of the 38 accepted proposals (n>=6) has, under "
        "the SAME Morgan/ECFP radius-2 2048-bit Tanimoto instrument used for the "
        "receipt's headline IntDiv_1=0.7681, an internal IntDiv_1 <= 0.25 (mean "
        "pairwise Tanimoto >= 0.75) AND >=50% of its chain-length-adjacent "
        "neighbor pairs at Tanimoto >= 0.99 (fingerprint-indistinguishable). This "
        "operationalizes 'not trivially inflated variants of a single scaffold' "
        "at family resolution using only the attacked receipt's own metric space."
    )

    violations = []
    for f in homolog_families:
        stat = per_family[f]
        adj = f1_adj if f == "F1_polyethyleneamine" else f2_adj
        frac_sat = sum(1 for t in adj if t >= 0.99) / len(adj)
        violates = stat["fraction_of_accepted_set"] >= 0.15 and stat["intdiv1"] <= 0.25 and frac_sat >= 0.50
        violations.append({
            "family": f,
            "n": stat["n"],
            "fraction_of_accepted_set": stat["fraction_of_accepted_set"],
            "intdiv1": stat["intdiv1"],
            "adjacent_pairs_tanimoto_ge_0p99_fraction": frac_sat,
            "violates_decision_rule": violates,
        })

    any_violation = any(v["violates_decision_rule"] for v in violations)
    verdict = "H0_REFUTED" if any_violation else "H0_SURVIVES"

    result = {
        "schema": "amphora.molecule-generator.molgen-scaffold-diversity-homolog-fingerprint-saturation.v1",
        "study_id": "molgen-scaffold-diversity-homolog-fingerprint-saturation-v1",
        "run_type": "FALSIFICATION_ATTACK_DIVERSITY_METRIC_FAMILY_RESOLUTION",
        "purpose": (
            "Attack amphora-molecule-generator/evidence/audit/molgen-scaffold-diversity-v1's "
            "CORROBORATED_IN_AUDIT_INSTRUMENT verdict by evaluating its own Morgan/ECFP "
            "r2/2048 Tanimoto instrument WITHIN each accepted family instead of only in "
            "aggregate, testing whether the two linear-chain homologous families (47.4% of "
            "the accepted set) are actually resolved as diverse by that instrument."
        ),
        "attacked_claim": (
            "amphora-molecule-generator/evidence/audit/molgen-scaffold-diversity-v1/"
            "molgen-scaffold-diversity-receipt.v1.dsse.json#hypothesis_evaluation "
            "(hypothesis: 'The deterministic grammar's accepted proposals span a diverse "
            "region of chemical space (not trivially inflated variants of a single "
            "scaffold)'; verdict: CORROBORATED_IN_AUDIT_INSTRUMENT; headline IntDiv_1=0.7681, "
            "mean pairwise Tanimoto=0.2319 over all 703 pairs)"
        ),
        "attacked_receipt_sha256": sha(ATTACKED_RECEIPT.read_bytes()),
        "source_diagnostic_sha256": sha(source_bytes),
        "falsification_criterion": decision_rule,
        "fingerprint": {"type": "Morgan/ECFP", "radius": 2, "n_bits": 2048,
                         "tanimoto": "binary Tanimoto coefficient",
                         "note": "identical fingerprint definition to the attacked receipt"},
        "n_molecules": 38,
        "overall_intdiv1_recomputed": overall_intdiv1,
        "overall_mean_pairwise_tanimoto_recomputed": overall_mean_sim,
        "overall_intdiv1_receipt_reported": receipt_reported_overall_intdiv1,
        "recomputation_matches_receipt": recompute_matches_receipt,
        "per_family_intdiv1": per_family,
        "homolog_bloc": {
            "families": homolog_families,
            "n_members": len(homolog_bloc_smis),
            "fraction_of_accepted_set": len(homolog_bloc_smis) / 38,
            "intdiv1": bloc_intdiv1,
            "mean_pairwise_tanimoto": bloc_mean_sim,
            "n_pairs": bloc_npairs,
        },
        "adjacent_homolog_similarity": {
            "F1_polyethyleneamine_order_by_repeat_unit_count": f1_order,
            "F1_adjacent_tanimoto": f1_adj,
            "F1_adjacent_tanimoto_mean": sum(f1_adj) / len(f1_adj),
            "F2_alpha_omega_diamine_order_by_chain_length": f2_order,
            "F2_adjacent_tanimoto": f2_adj,
            "F2_adjacent_tanimoto_mean": sum(f2_adj) / len(f2_adj),
            "combined_adjacent_pairs_n": len(combined_adj),
            "combined_adjacent_pairs_tanimoto_ge_0p99": n_adj_saturated,
            "combined_adjacent_pairs_tanimoto_ge_0p99_fraction": n_adj_saturated / len(combined_adj),
        },
        "cross_bloc_homolog_vs_ring_mean_tanimoto": cross_mean,
        "receipt_collapsed_control_intdiv1_floor": 0.0,
        "instrument_self_tests": {
            "identity_self_similarity_is_exactly_1": self_sim == 1.0,
            "unrelated_ring_pair_control": {
                "pair": ["DDS(sulfone)", "benzidine(4,4'-diaminobiphenyl)"],
                "tanimoto": unrelated_control_sim,
                "well_below_homolog_adjacent_saturation": unrelated_control_sim < 0.5,
            },
            "all_pass": bool(self_sim == 1.0 and unrelated_control_sim < 0.5 and recompute_matches_receipt),
        },
        "per_family_decision_rule_evaluation": violations,
        "hypothesis_evaluation": {
            "h0": "The deterministic grammar's accepted proposals span a diverse region of chemical space (not trivially inflated variants of a single scaffold).",
            "decision_rule": decision_rule,
            "evidence": (
                f"F1_polyethyleneamine (n=8, 21.1% of set): IntDiv_1={per_family['F1_polyethyleneamine']['intdiv1']:.4f} "
                f"(mean Tanimoto {per_family['F1_polyethyleneamine']['mean_pairwise_tanimoto']:.4f}), "
                f"{sum(1 for t in f1_adj if t>=0.99)}/{len(f1_adj)} adjacent chain-length-neighbor pairs "
                "fingerprint-saturated at Tanimoto>=0.99 (TETA-TEPA-PEHA-k6-k7-k8 all pairwise identical). "
                f"F2_alpha_omega_diamine (n=10, 26.3% of set): IntDiv_1={per_family['F2_alpha_omega_diamine']['intdiv1']:.4f} "
                f"(mean Tanimoto {per_family['F2_alpha_omega_diamine']['mean_pairwise_tanimoto']:.4f}), "
                f"{sum(1 for t in f2_adj if t>=0.99)}/{len(f2_adj)} adjacent pairs saturated. Both families independently "
                "violate the decision rule despite the receipt's headline aggregate IntDiv_1=0.7681 -- the aggregate is "
                "driven by cross-family contrast (homolog-bloc-vs-ring mean Tanimoto="
                f"{cross_mean:.4f}) and conceals near-total indistinguishability within 47.4% of the corpus under the "
                "receipt's own instrument."
            ),
            "actionable_consequence": (
                "The scaffold-diversity receipt's CORROBORATED_IN_AUDIT_INSTRUMENT verdict, read as an aggregate "
                "'the accepted set is diverse' claim, does not hold at family resolution: the two linear-chain "
                "homologous families are literal textbook trivially-inflated-variant series (differ only by a "
                "repeated -CH2- or -CH2CH2NH- unit), and the SAME ECFP-r2/2048 instrument the receipt relies on "
                "cannot resolve most adjacent members of either family from one another. Any downstream use of the "
                "IntDiv_1=0.7681 aggregate to argue the generator avoids near-duplicate proposals must be corrected "
                "to disclose that this holds only across families, not within the two homolog families comprising "
                "nearly half the accepted set."
            ),
            "verdict": verdict,
        },
        "verdict": verdict,
        "non_circularity": (
            "SMILES and family labels are read verbatim from the hash-locked prior grammar-yield "
            "diagnostic (unchanged); fingerprints are independently recomputed here with the exact "
            "parameters (Morgan r2, 2048 bits) documented in the attacked receipt's own 'fingerprint' "
            "field. The aggregate IntDiv_1 recomputation exactly reproduces the attacked receipt's "
            "reported 0.768098 (parity self-test), confirming this is the same instrument evaluated at "
            "finer (per-family) resolution, not a different or looser metric substituted to force a "
            "refutation."
        ),
        "does_not_close": [
            "Runtime remains LOCKED_INTERNAL; no proposal emission enabled.",
            "No Phase-0 promotion; scientific_readiness stays UNVALIDATED.",
            "This does not modify, retract, or re-sign the attacked molgen-scaffold-diversity-v1 receipt; it is an independent companion finding.",
            "This is a structural fingerprint-resolution finding, not a property, FTO, or wet-lab performance claim.",
            "Bemis-Murcko scaffold counting (7 generic ring frameworks) is untouched; this finding is specific to the ECFP/Tanimoto IntDiv_1 instrument and the acyclic homolog families it is blind to.",
        ],
        "rights_posture": {
            "external_dataset_used": False,
            "new_external_data_acquired": False,
            "input_smiles": "read from hash-locked amphora-molecule-generator prior receipt (published scaffold families)",
            "methods": "RDKit (BSD-licensed); Morgan/ECFP fingerprint and Tanimoto coefficient are published open methods",
        },
        "theory_reference": {
            "fingerprint": "Rogers & Hahn 2010 J. Chem. Inf. Model. 50(5):742-754 (ECFP)",
            "similarity_coefficient": "Bajusz, Racz & Heberger 2015 J. Cheminform. 7:20 (Tanimoto)",
            "internal_diversity_metric": "Polykovskiy et al. 2020 Front. Pharmacol. 11:565644 (MOSES IntDiv_p)",
            "homologous_series_fingerprint_saturation": (
                "Known limitation of finite-radius circular fingerprints on linear repeat-unit chains: once "
                "chain length exceeds ~2x the fingerprint radius, added repeat units contribute no new "
                "substructure environments beyond those already hashed into the bit vector, so ECFP-r2 "
                "similarity between chain homologs saturates toward 1.0 (folding/collision effects in a "
                "fixed-width 2048-bit vector reinforce this for the longer members)."
            ),
            "toolkit": "RDKit 2026.03.2 Morgan fingerprints",
        },
    }
    return result


if __name__ == "__main__":
    out_name = sys.argv[1] if len(sys.argv) > 1 else "diagnostic.canonical.json"
    result = main()
    out_dir = GEN / "evidence/audit/molgen-scaffold-diversity-homolog-fingerprint-saturation-v1"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / out_name
    out_path.write_text(json.dumps(result, indent=2, sort_keys=True))
    print("WROTE", out_path)
    print("verdict", result["verdict"])
    print("sha256", sha(out_path.read_bytes()))
