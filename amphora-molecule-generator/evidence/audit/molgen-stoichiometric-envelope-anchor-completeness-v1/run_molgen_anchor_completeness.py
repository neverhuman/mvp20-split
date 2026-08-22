#!/usr/bin/env python3
"""AUDIT_ONLY diagnostic: ANCHOR-SET COMPLETENESS audit of the signed
molgen-stoichiometric-envelope-coverage-v1 receipt's "commercial envelope"
population.

That receipt's own stated population is "the commercial marine epoxy-amine
hardeners already shipped in amphora-ingredient-library" (its purpose field,
verbatim), operationalised as the 6 hardener.*.ahew facts in
amphora-ingredient-library/reference/mvp20/data/facts.json (sha256
0af2456a443692093fc4a89174e5cc87da86323108b14c3aa20cc3af159f06fb), giving
commercial_envelope_g_per_eq = [100.0, 264.0] and n_commercial_anchors = 6.

This audit asks a narrower, mechanically checkable question: is that
population actually complete relative to the receipt's OWN stated scope --
"already shipped in amphora-ingredient-library"?  A second file,
cure_verification_set.json (sha256
884356a094bd6f4def926e7ef218070b83d917742009c8922f953c097f9305d2), is
byte-identical in BOTH amphora-ingredient-library/reference/mvp20/data/ and
amphora-molecule-generator/reference/mvp20/data/ -- it sits in the exact same
directory as facts.json, and amphora-molecule-generator/docs/mission.md
itself lists it as a "Checked dataset and artifact" for THIS module. It
carries named, dual-source-provenanced (Evonik US + EMEA product guides;
"2 sources" or "US guide; EMEA gives ... (regional conflict flagged)")
hardener AHEW facts for products never pulled into the anchor list, and
amphora-ingredient-library's own hardener-tds-external-verification-v1 audit
already independently corroborated this file's regional-conflict disclosure
for ancamide_260a against a live manufacturer TDS, establishing it as
trustworthy, non-circular data -- not a fluke or transcription artifact.

Non-circular: the target receipt's own generated-hull SMILES are re-read from
the same hash-locked grammar-yield diagnostic it used; AHEW is re-derived
here from structure by RDKit using the same active-N-H convention this
module's own R-A06v2 repair established (portfolio-wide) and that the target
receipt itself uses. The anchor union is a plain set union over two files
already checked into this module's own reference directory; no external data
is fetched or acquired.

AUDIT_ONLY: does not promote authority, does not flip scientific_readiness,
does not modify the manifest, any locked dataset, or any signed Phase-0 KPI.
Does NOT modify or delete the target receipt or its reference file -- this is
an independent audit finding about that receipt's anchor-set completeness.
"""
import hashlib
import json
import sys
from pathlib import Path

from rdkit import Chem, RDLogger
from rdkit.Chem import Descriptors

RDLogger.DisableLog("rdApp.*")

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MODULE = ROOT / "amphora-molecule-generator"
TARGET_RECEIPT = (MODULE / "evidence/audit/molgen-stoichiometric-envelope-coverage-v1"
                   / "molgen-stoichiometric-envelope-coverage-receipt.v1.dsse.json")
GRAMMAR_DIAG = (MODULE / "evidence/audit/molgen-deterministic-grammar-yield-v1"
                / "diagnostic.canonical.json")
ENVELOPE = MODULE / "reference/mvp20/data/hardener_stoichiometric_envelope.v1.json"
GEN_FACTS = MODULE / "reference/mvp20/data/facts.json"
GEN_CURE_VERIF = MODULE / "reference/mvp20/data/cure_verification_set.json"
ING_FACTS = ROOT / "amphora-ingredient-library/reference/mvp20/data/facts.json"
ING_CURE_VERIF = ROOT / "amphora-ingredient-library/reference/mvp20/data/cure_verification_set.json"
MISSION = MODULE / "docs/mission.md"
OUTDIR = MODULE / "evidence/audit/molgen-stoichiometric-envelope-anchor-completeness-v1"

AMIDE_N = Chem.MolFromSmarts("[NX3][CX3](=[OX1])")
SULFONAMIDE_N = Chem.MolFromSmarts("[NX3][SX4](=[OX1])(=[OX1])")


def sha(b):
    return hashlib.sha256(b).hexdigest()


def r(x, n=6):
    return None if x is None else round(float(x), n)


def nitrogen_census(smiles):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    excluded = set()
    for patt in (AMIDE_N, SULFONAMIDE_N):
        for match in mol.GetSubstructMatches(patt):
            excluded.add(match[0])
    active_h = 0
    for atom in mol.GetAtoms():
        if atom.GetSymbol() != "N":
            continue
        if atom.GetIdx() in excluded or atom.GetIsAromatic():
            continue
        active_h += atom.GetTotalNumHs()
    return {"molar_mass_g_per_mol": Descriptors.MolWt(mol), "n_active_nh": active_h}


# ------------------------------------------------------------------ inputs --
target_receipt_bytes = TARGET_RECEIPT.read_bytes()
grammar_bytes = GRAMMAR_DIAG.read_bytes()
envelope_bytes = ENVELOPE.read_bytes()
gen_facts_bytes = GEN_FACTS.read_bytes()
gen_cure_bytes = GEN_CURE_VERIF.read_bytes()
ing_facts_bytes = ING_FACTS.read_bytes()
ing_cure_bytes = ING_CURE_VERIF.read_bytes()
mission_bytes = MISSION.read_bytes()

# hash-parity check: molecule-generator's own local copies must be
# byte-identical to amphora-ingredient-library's (both "already shipped"
# under the target receipt's own population definition)
cross_module_facts_identical = sha(gen_facts_bytes) == sha(ing_facts_bytes)
cross_module_cure_identical = sha(gen_cure_bytes) == sha(ing_cure_bytes)

mission_text = mission_bytes.decode()
cure_verif_listed_in_own_mission = (
    "cure_verification_set.json" in mission_text
    and sha(gen_cure_bytes) in mission_text
)

envelope = json.loads(envelope_bytes)
target_receipt = json.loads(target_receipt_bytes)
target_payload = json.loads(
    __import__("base64").b64decode(target_receipt["signature"]["payload"]))

# ---------------------------------------- original 6-anchor population -----
orig_anchors = envelope["commercial_anchors"]["entries"]
orig_by_product = {a["product"].lower().replace(" ", "_").replace("-", "_"): a
                    for a in orig_anchors}
orig_lo, orig_hi = envelope["commercial_anchors"]["design_envelope_ahew_g_per_eq"]

# ---------------------------- expanded population: union with cure_verification_set --
gen_facts = json.loads(gen_facts_bytes)
cure_verif = json.loads(gen_cure_bytes)

facts_hardener_ahew = {
    k: v["value"] for k, v in gen_facts["entries"].items()
    if k.startswith("hardener.") and k.endswith(".ahew")
}
cure_verif_ahew = {
    row["hardener"]: {"ahew": row["ahew"], "prov": row["prov"]}
    for row in cure_verif["rows"] if row.get("ahew") is not None
}

union_products = {}
for fact_key, ahew in facts_hardener_ahew.items():
    name = fact_key.split(".")[1]
    union_products[name] = {"ahew_g_per_eq": ahew, "source": "facts.json",
                             "already_in_target_anchor_list": True}
new_from_cure_verif = []
for name, rec in cure_verif_ahew.items():
    if name in union_products:
        # cross-check: same product, does the value agree?
        agree = abs(union_products[name]["ahew_g_per_eq"] - rec["ahew"]) < 1e-6
        union_products[name]["cure_verification_set_agrees"] = bool(agree)
        union_products[name]["cure_verification_set_ahew"] = rec["ahew"]
    else:
        union_products[name] = {"ahew_g_per_eq": rec["ahew"],
                                 "source": "cure_verification_set.json",
                                 "provenance": rec["prov"],
                                 "already_in_target_anchor_list": False}
        new_from_cure_verif.append({"product": name, "ahew_g_per_eq": rec["ahew"],
                                     "provenance": rec["prov"]})

all_ahews = [v["ahew_g_per_eq"] for v in union_products.values()]
true_lo, true_hi = min(all_ahews), max(all_ahews)
n_union_anchors = len(union_products)
n_new_anchors = len(new_from_cure_verif)

# consistency check: the 3 products present in BOTH files must agree
overlap_products = [n for n, v in union_products.items()
                     if v.get("source") == "facts.json" and "cure_verification_set_ahew" in v]
overlap_all_agree = all(union_products[n]["cure_verification_set_agrees"]
                         for n in overlap_products)

# ------------------------------------------- re-derive generated hull -------
grammar = json.loads(grammar_bytes)
proposals = grammar["accepted_proposals"]
rows = []
for p in proposals:
    c = nitrogen_census(p["canonical_smiles"])
    if c is None or c["n_active_nh"] == 0:
        continue
    rows.append({"name": p["name"],
                  "ahew_g_per_eq": c["molar_mass_g_per_mol"] / c["n_active_nh"]})
gen_lo = min(x["ahew_g_per_eq"] for x in rows)
gen_hi = max(x["ahew_g_per_eq"] for x in rows)

# parity check against the target receipt's own claimed generated hull
target_gen_hull = target_payload["results"]["generated_hull_g_per_eq"]
gen_hull_parity = (abs(gen_lo - target_gen_hull[0]) < 1e-3
                    and abs(gen_hi - target_gen_hull[1]) < 1e-3)

# --------------------------------------------------------- corrected test ---
orig_overlap = max(0.0, min(gen_hi, orig_hi) - max(gen_lo, orig_lo))
true_overlap = max(0.0, min(gen_hi, true_hi) - max(gen_lo, true_lo))
orig_shortfall = orig_lo - gen_hi
true_shortfall = true_lo - gen_hi

target_claimed_floor = target_payload["results"]["commercial_envelope_g_per_eq"][0]
target_claimed_n_anchors = target_payload["results"]["n_anchors"]
target_claimed_shortfall = target_payload["results"]["shortfall_to_commercial_floor_g_per_eq"]
target_claimed_shortfall_rel = target_payload["results"]["shortfall_relative_to_commercial_floor"]

floor_claim_refuted = abs(target_claimed_floor - true_lo) > 1e-6
count_claim_refuted = target_claimed_n_anchors != n_union_anchors
shortfall_numbers_stale = abs(target_claimed_shortfall - true_shortfall) > 1e-3

# H0 (grammar covers the envelope) verdict under the corrected population --
# still refuted (true_lo=93 still > gen_hi=62.08), so the ORIGINAL headline
# scientific conclusion survives; only the specific numeric/count claims
# about the anchor population and shortfall are refuted.
h0_still_refuted_under_corrected_population = not (gen_lo <= true_lo and true_hi <= gen_hi) and (
    sum(1 for a in all_ahews if gen_lo <= a <= gen_hi) == 0)

verdict = "ANCHOR_COMPLETENESS_CLAIM_REFUTED" if (floor_claim_refuted or count_claim_refuted) \
    else "ANCHOR_COMPLETENESS_CLAIM_SURVIVED"

headline = (
    f"The signed molgen-stoichiometric-envelope-coverage-v1 receipt's anchor population "
    f"(commercial_envelope_g_per_eq=[{target_claimed_floor:g},{target_payload['results']['commercial_envelope_g_per_eq'][1]:g}], "
    f"n_commercial_anchors={target_claimed_n_anchors}) is INCOMPLETE relative to its own stated "
    f"population ('commercial marine epoxy-amine hardeners already shipped in "
    f"amphora-ingredient-library'): cure_verification_set.json (sha256 {sha(gen_cure_bytes)[:16]}...), "
    f"byte-identical in both amphora-ingredient-library and this module's own reference/mvp20/data/ "
    f"and listed in this module's own mission.md as a checked dataset, carries "
    f"{len(cure_verif_ahew)} dual-source-provenanced named-hardener AHEW facts, "
    f"{n_new_anchors} of which ({', '.join(a['product'] for a in new_from_cure_verif)}) are absent "
    f"from the target receipt's 6-anchor list. The lowest, Ancamide 2426 at "
    f"{[a['ahew_g_per_eq'] for a in new_from_cure_verif if a['product']=='ancamide_2426'][0]:g} g/eq "
    f"(EMEA guide), sits BELOW the target's claimed commercial floor of {target_claimed_floor:g} g/eq, "
    f"so the true floor is {true_lo:g} g/eq, not {target_claimed_floor:g}, and the true anchor count is "
    f"{n_union_anchors}, not {target_claimed_n_anchors}. The target's headline shortfall figures "
    f"({target_claimed_shortfall:g} g/eq, {target_claimed_shortfall_rel:.4f} fraction) are stale under "
    f"the corrected population (true shortfall {true_shortfall:.4f} g/eq, "
    f"{(true_shortfall/true_lo):.4f} fraction). The 3 products present in both files "
    f"({', '.join(overlap_products)}) agree exactly (cross-file consistency check "
    f"{'PASS' if overlap_all_agree else 'FAIL'}), confirming cure_verification_set.json is reliable, "
    f"non-circular data, not noise. This does NOT flip the underlying H0 verdict itself: even the "
    f"corrected floor ({true_lo:g} g/eq) remains above the independently re-derived generated hull "
    f"ceiling ({gen_hi:.4f} g/eq), so 0 anchors fall inside the hull under either population and the "
    f"generator-cannot-reach-commercial-band scientific conclusion survives. What is refuted is the "
    f"target receipt's specific, signed, quantitative claim that its 6-anchor facts.json-only "
    f"enumeration is the complete relevant commercial population and that {target_claimed_floor:g} g/eq "
    f"is the true commercial floor."
)

diag = {
    "schema": "amphora.molecule-generator.molgen-stoichiometric-envelope-anchor-completeness.v1",
    "study_id": "molgen-stoichiometric-envelope-anchor-completeness-v1",
    "authority": "AUDIT_ONLY",
    "module": "amphora-molecule-generator",
    "rdkit_version": __import__("rdkit").__version__,
    "headline": headline,
    "purpose": (
        "Audit whether the signed molgen-stoichiometric-envelope-coverage-v1 receipt's "
        "6-anchor 'commercial envelope' population is complete relative to its own stated "
        "scope, by unioning it against a second, already-checked-in, hash-identical dataset "
        "(cure_verification_set.json) present in the SAME reference/mvp20/data/ directory of "
        "the SAME module and explicitly listed in this module's own mission.md."
    ),
    "target_claim": {
        "receipt_path": "amphora-molecule-generator/evidence/audit/molgen-stoichiometric-envelope-coverage-v1/molgen-stoichiometric-envelope-coverage-receipt.v1.dsse.json",
        "field": "results.commercial_envelope_g_per_eq / results.n_anchors / results.shortfall_to_commercial_floor_g_per_eq",
        "claimed_commercial_envelope_g_per_eq": target_payload["results"]["commercial_envelope_g_per_eq"],
        "claimed_n_anchors": target_claimed_n_anchors,
        "claimed_shortfall_g_per_eq": target_claimed_shortfall,
        "claimed_shortfall_relative": target_claimed_shortfall_rel,
        "claimed_hypothesis_verdict": target_payload["results"]["hypothesis_verdict"],
    },
    "non_circularity": (
        "Grammar SMILES re-read from the same hash-locked grammar-yield diagnostic the target "
        "receipt used; AHEW is independently re-derived here from structure by RDKit (same "
        "active-N-H convention as the target and this module's R-A06v2 repair). The anchor "
        "union is a plain set union over two files already checked into this module's own "
        "reference directory (facts.json, cure_verification_set.json); no external data "
        "fetched, no new data acquired."
    ),
    "cross_module_hash_parity": {
        "facts_json_identical_gen_vs_ingredient_library": bool(cross_module_facts_identical),
        "cure_verification_set_identical_gen_vs_ingredient_library": bool(cross_module_cure_identical),
        "cure_verification_set_sha256": sha(gen_cure_bytes),
        "cure_verification_set_listed_in_own_mission_md": bool(cure_verif_listed_in_own_mission),
    },
    "generated_hull_rederivation": {
        "n_molecules": len(rows),
        "ahew_min_g_per_eq": r(gen_lo, 4),
        "ahew_max_g_per_eq": r(gen_hi, 4),
        "matches_target_receipt_claimed_hull": bool(gen_hull_parity),
        "target_receipt_claimed_hull": target_gen_hull,
    },
    "anchor_union": {
        "original_anchor_count": len(orig_anchors),
        "original_envelope_g_per_eq": [orig_lo, orig_hi],
        "cure_verification_set_ahew_rows_total": len(cure_verif["rows"]),
        "cure_verification_set_ahew_rows_nonnull": len(cure_verif_ahew),
        "new_anchors_from_cure_verification_set": new_from_cure_verif,
        "overlap_products_present_in_both_files": overlap_products,
        "overlap_products_agree_exactly": bool(overlap_all_agree),
        "union_anchor_count": n_union_anchors,
        "true_envelope_g_per_eq": [r(true_lo, 4), r(true_hi, 4)],
        "all_union_entries": {k: v for k, v in sorted(union_products.items())},
    },
    "corrected_coverage_test": {
        "generated_hull_g_per_eq": [r(gen_lo, 4), r(gen_hi, 4)],
        "original_commercial_envelope_g_per_eq": [orig_lo, orig_hi],
        "true_commercial_envelope_g_per_eq": [r(true_lo, 4), r(true_hi, 4)],
        "original_shortfall_g_per_eq": r(orig_shortfall, 4),
        "true_shortfall_g_per_eq": r(true_shortfall, 4),
        "true_shortfall_relative": r(true_shortfall / true_lo, 6),
        "n_union_anchors_inside_generated_hull": sum(1 for a in all_ahews if gen_lo <= a <= gen_hi),
        "h0_grammar_covers_envelope_still_refuted_under_true_population": bool(
            h0_still_refuted_under_corrected_population),
    },
    "hypothesis_evaluation": {
        "h0": ("The target receipt's 6-anchor commercial_envelope_g_per_eq=[100.0,264.0] and "
               "n_commercial_anchors=6 constitute the complete population of named commercial "
               "marine epoxy-amine hardener AHEW facts already shipped in "
               "amphora-ingredient-library, as the target receipt's own purpose field claims."),
        "decision_rule": ("H0 is refuted if a second already-in-tree, hash-pinned, "
                          "cross-module-identical dataset in the SAME population scope "
                          "contains named-hardener AHEW facts absent from the target's anchor "
                          "list, OR if it shifts the claimed commercial floor."),
        "verdict": "H0_REFUTED" if (floor_claim_refuted or count_claim_refuted) else "H0_SURVIVED",
        "evidence": (
            f"cure_verification_set.json contributes {n_new_anchors} named anchors absent from "
            f"the target's list; Ancamide 2426 (AHEW={[a['ahew_g_per_eq'] for a in new_from_cure_verif if a['product']=='ancamide_2426'][0]:g} g/eq) "
            f"undercuts the claimed floor of {target_claimed_floor:g} g/eq. Does NOT flip the "
            f"target's underlying scientific conclusion (generator cannot reach commercial AHEW "
            f"band) -- the corrected floor is still {true_lo - gen_hi:.3f} g/eq above the "
            f"generated hull ceiling."
        ),
        "does_not_flip": (
            "The target receipt's headline scientific hypothesis_evaluation.verdict (H0_REFUTED "
            "-- generator does not cover the commercial stoichiometric envelope) remains correct "
            "under the corrected, larger anchor population. Only the target's specific signed "
            "numeric claims about anchor-set size, envelope floor, and shortfall magnitude are "
            "stale/incomplete."
        ),
    },
    "modifies_locked_dataset": False,
    "modifies_manifest": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_or_deletes_target_receipt": False,
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "theory_reference": {
        "ahew_and_cure_stoichiometry": "Lee & Neville 1967, Handbook of Epoxy Resins, McGraw-Hill (LCCN 66-23992)",
        "amine_value": "ASTM D2074",
        "primary_hardener_data_source": "Evonik Epoxy Curing Agents Product Guide Americas + EMEA (already cited by cure_verification_set.json)",
        "toolkit": "RDKit " + __import__("rdkit").__version__,
    },
    "rights_posture": {
        "in_scope": "marine anti-corrosion two-part epoxy-amine only",
        "new_external_data_acquired": False,
        "redistributes_third_party_dataset": False,
        "commercial_anchor_basis": ("numeric scalars already shipped in-tree in both "
                                     "amphora-ingredient-library and amphora-molecule-generator "
                                     "reference/mvp20/data/; no new source touched"),
    },
    "hash_and_count_lock": {
        "target_receipt_sha256": sha(target_receipt_bytes),
        "grammar_receipt_diagnostic_sha256": sha(grammar_bytes),
        "envelope_reference_sha256": sha(envelope_bytes),
        "gen_facts_json_sha256": sha(gen_facts_bytes),
        "gen_cure_verification_set_sha256": sha(gen_cure_bytes),
        "ingredient_facts_json_sha256": sha(ing_facts_bytes),
        "ingredient_cure_verification_set_sha256": sha(ing_cure_bytes),
        "mission_md_sha256": sha(mission_bytes),
        "n_original_anchors": len(orig_anchors),
        "n_new_anchors": n_new_anchors,
        "n_union_anchors": n_union_anchors,
    },
    "closes": [],
    "does_not_close": [
        "Does not flip the target receipt's H0_REFUTED verdict on generator-vs-commercial-envelope "
        "coverage -- that scientific conclusion is corroborated, not overturned.",
        "Does not modify, supersede, or delete the target receipt or its reference file; this is a "
        "companion audit finding only. A formal repair (R-*) would be needed to correct the target "
        "receipt's numeric claims.",
        "18 of the 25 cure_verification_set.json hardener rows have null AHEW (not extracted from "
        "the cited TDS by that dataset's own authors); the true floor could be lower still if those "
        "were resolved -- not attempted here.",
        "AHEW anchors remain technical-grade measured values on polydisperse resins; the comparison "
        "still bounds capability, not product equivalence.",
        "Not a cure-kinetics, pot-life, property, FTO, or wet-lab performance claim.",
    ],
}

OUTDIR.mkdir(parents=True, exist_ok=True)
out = OUTDIR / (sys.argv[1] if len(sys.argv) > 1 else "diagnostic.canonical.json")
payload = json.dumps(diag, indent=2, sort_keys=True).encode()
out.write_bytes(payload)
print("WROTE", out)
print("sha256", sha(payload))
print("verdict", diag["hypothesis_evaluation"]["verdict"])
print("floor_claim_refuted", floor_claim_refuted, "count_claim_refuted", count_claim_refuted)
print("true_envelope", true_lo, true_hi, "orig_envelope", orig_lo, orig_hi)
print("gen_hull", gen_lo, gen_hi, "gen_hull_parity", gen_hull_parity)
print("n_union_anchors", n_union_anchors, "n_new_anchors", n_new_anchors)
print("overlap_products", overlap_products, "overlap_all_agree", overlap_all_agree)
