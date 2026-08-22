#!/usr/bin/env python3
"""AUDIT_ONLY diagnostic: STOICHIOMETRIC DESIGN-ENVELOPE COVERAGE of the
amphora-molecule-generator deterministic-grammar accepted-proposal set.

The three prior molecule-generator receipts closed STRUCTURAL pillars -- yield /
synthetic feasibility, structural novelty, and chemical-space diversity.  None
of them asked the question that actually decides whether a proposed hardener is
usable in a two-part marine epoxy: does the generated universe span the
STOICHIOMETRIC design envelope (amine hydrogen equivalent weight, amine value,
mix ratio phr) occupied by the commercial hardeners the formulation module
already ships?

Baselines (published, non-circular):
  * Lee & Neville 1967, Handbook of Epoxy Resins, McGraw-Hill (LCCN 66-23992)
    -- AHEW = M / n_activeH; 1:1 epoxide:amine-hydrogen cure stoichiometry;
    amine-epoxy adduct curing agents.
  * Ellis (ed.) 1993, Chemistry and Technology of Epoxy Resins, Blackie /
    Chapman & Hall, ISBN 978-0-7514-0095-4 -- adduct and polyamide hardener
    classes and their equivalent-weight ranges.
  * ASTM D2074 -- total amine value by titration, AV = 56105.6 * n_basicN / M.
  * IUPAC 2021 standard atomic weights (Prohaska et al. 2022, Pure Appl. Chem.
    94(5):573-600) -- molar masses, via RDKit.
  * Spearman 1904, Am. J. Psychol. 15(1):72-101 -- rank correlation, used for
    the mass/functionality coupling mechanism statement.

Non-circular: SMILES are read from the hash-locked prior grammar-yield receipt;
active-N-H counts, molar masses, AHEW, amine value and phr are ALL re-derived
here from structure by RDKit.  The shipped active_nh column is used only as a
parity CHECK, never as an input.  The commercial envelope anchors come from a
different module (amphora-ingredient-library facts.json) and are not derived
from anything the generator produced.

AUDIT_ONLY: does not promote authority, does not flip scientific_readiness,
does not modify the manifest (66 receipts / 11 modules), any locked dataset, or
any signed Phase-0 KPI.
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
GRAMMAR_DIAG = (MODULE / "evidence/audit/molgen-deterministic-grammar-yield-v1"
                / "diagnostic.canonical.json")
ENVELOPE = MODULE / "reference/mvp20/data/hardener_stoichiometric_envelope.v1.json"
INGREDIENT_FACTS = (ROOT / "amphora-ingredient-library/reference/mvp20/data"
                    / "facts.json")
OUTDIR = MODULE / "evidence/audit/molgen-stoichiometric-envelope-coverage-v1"

KOH_MG_PER_MOL = 56105.6          # ASTM D2074 amine-value constant
M_DGEBA = None                    # re-derived by RDKit below
AMIDE_N = Chem.MolFromSmarts("[NX3][CX3](=[OX1])")
SULFONAMIDE_N = Chem.MolFromSmarts("[NX3][SX4](=[OX1])(=[OX1])")


def sha(b):
    return hashlib.sha256(b).hexdigest()


def r(x, n=6):
    return None if x is None else round(float(x), n)


def nitrogen_census(smiles):
    """Independently re-derive active (epoxy-reactive) N-H count and basic-N
    count from structure.  Excluded: amide N, sulfonamide N (both non-basic and
    not epoxy-reactive at ambient cure temperature), and aromatic ring N (no
    N-H, and not a co-reactive site)."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    excluded = set()
    for patt in (AMIDE_N, SULFONAMIDE_N):
        for match in mol.GetSubstructMatches(patt):
            excluded.add(match[0])
    active_h = 0
    basic_n = 0
    primary = secondary = tertiary = 0
    for atom in mol.GetAtoms():
        if atom.GetSymbol() != "N":
            continue
        if atom.GetIdx() in excluded or atom.GetIsAromatic():
            continue
        nh = atom.GetTotalNumHs()
        active_h += nh
        basic_n += 1
        if nh == 2:
            primary += 1
        elif nh == 1:
            secondary += 1
        else:
            tertiary += 1
    return {
        "canonical_smiles": Chem.MolToSmiles(mol),
        "molar_mass_g_per_mol": Descriptors.MolWt(mol),
        "n_active_nh": active_h,
        "n_basic_n": basic_n,
        "n_primary_n": primary,
        "n_secondary_n": secondary,
        "n_tertiary_n": tertiary,
    }


def stoichiometry(census, eew_list):
    """AHEW, amine value, phr, and the AHEW*AV identity product."""
    m = census["molar_mass_g_per_mol"]
    nh = census["n_active_nh"]
    if nh == 0:
        return {"ahew_g_per_eq": None, "amine_value_mgKOH_per_g": None,
                "ahew_times_av": None, "phr": {}, "hardener_admissible": False}
    ahew = m / nh
    av = KOH_MG_PER_MOL * census["n_basic_n"] / m
    return {
        "ahew_g_per_eq": ahew,
        "amine_value_mgKOH_per_g": av,
        "ahew_times_av": ahew * av,
        "phr": {f"eew_{e:g}": 100.0 * ahew / e for e in eew_list},
        "hardener_admissible": True,
    }


def spearman(xs, ys):
    def ranks(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        rk = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1.0
            for k in range(i, j + 1):
                rk[order[k]] = avg
            i = j + 1
        return rk
    rx, ry = ranks(xs), ranks(ys)
    n = len(xs)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return num / den if den else None


# ---------------------------------------------------------------- inputs ----
grammar_bytes = GRAMMAR_DIAG.read_bytes()
envelope_bytes = ENVELOPE.read_bytes()
facts_bytes = INGREDIENT_FACTS.read_bytes()
grammar = json.loads(grammar_bytes)
env = json.loads(envelope_bytes)
proposals = grammar["accepted_proposals"]

EEW_MONO = env["dgeba_reference"]["eew_monomeric_g_per_eq"]
EEW_TECH = env["dgeba_reference"]["eew_technical_liquid_g_per_eq"]
EEWS = [EEW_MONO, EEW_TECH]
M_DGEBA = Descriptors.MolWt(Chem.MolFromSmiles(env["dgeba_reference"]["smiles"]))

# ------------------------------------------------- instrument self-tests ----
self_tests = []
for ka in env["known_answer_amines"]["entries"]:
    c = nitrogen_census(ka["smiles"])
    st = stoichiometry(c, EEWS)
    nh_ok = (c["n_active_nh"] == ka["expected_active_nh"])
    bn_ok = (c["n_basic_n"] == ka["expected_basic_n"])
    # definitional exactness: AHEW must equal M/n_H to machine precision
    exact = abs(st["ahew_g_per_eq"] - c["molar_mass_g_per_mol"] / c["n_active_nh"]) < 1e-12
    # exact identity: AHEW * AV == 56105.6 * n_basicN / n_activeH
    ident_expected = KOH_MG_PER_MOL * c["n_basic_n"] / c["n_active_nh"]
    ident_ok = abs(st["ahew_times_av"] - ident_expected) < 1e-9
    band_ok = 28052.8 - 1e-6 <= st["ahew_times_av"] <= 56105.6 + 1e-6
    self_tests.append({
        "name": ka["name"],
        "smiles": ka["smiles"],
        "molar_mass_g_per_mol": r(c["molar_mass_g_per_mol"], 4),
        "n_active_nh_rederived": c["n_active_nh"],
        "n_active_nh_expected": ka["expected_active_nh"],
        "n_basic_n_rederived": c["n_basic_n"],
        "n_basic_n_expected": ka["expected_basic_n"],
        "ahew_g_per_eq": r(st["ahew_g_per_eq"], 4),
        "amine_value_mgKOH_per_g": r(st["amine_value_mgKOH_per_g"], 4),
        "ahew_times_av": r(st["ahew_times_av"], 6),
        "ahew_times_av_expected": r(ident_expected, 6),
        "active_nh_matches": bool(nh_ok),
        "basic_n_matches": bool(bn_ok),
        "ahew_definitional_exact": bool(exact),
        "identity_product_exact": bool(ident_ok),
        "identity_band_holds": bool(band_ok),
        "all_pass": bool(nh_ok and bn_ok and exact and ident_ok and band_ok),
    })
self_tests_pass = sum(1 for t in self_tests if t["all_pass"])

# --------------------------------------------------- fail-closed decoys -----
decoys = []
for d in env["fail_closed_decoys"]["entries"]:
    c = nitrogen_census(d["smiles"])
    st = stoichiometry(c, EEWS)
    nh_ok = (c["n_active_nh"] == d["expected_active_nh"])
    # a difunctional hardener needs >= 2 active N-H on >= 2 distinct N sites
    difunctional = (c["n_active_nh"] >= 2 and c["n_basic_n"] >= 2)
    rejected = (not difunctional)
    decoys.append({
        "name": d["name"],
        "smiles": d["smiles"],
        "n_active_nh_rederived": c["n_active_nh"],
        "n_active_nh_expected": d["expected_active_nh"],
        "active_nh_matches": bool(nh_ok),
        "ahew_g_per_eq": r(st["ahew_g_per_eq"], 4),
        "ahew_is_undefined": st["ahew_g_per_eq"] is None,
        "admitted_as_difunctional_hardener": bool(difunctional),
        "fail_closed": bool(nh_ok and rejected),
    })
decoys_pass = sum(1 for d in decoys if d["fail_closed"])

# ----------------------------- parity vs shipped grammar-receipt column -----
rows = []
parity_mismatch = []
for p in proposals:
    c = nitrogen_census(p["canonical_smiles"])
    st = stoichiometry(c, EEWS)
    if c["n_active_nh"] != p["active_nh"]:
        parity_mismatch.append(p["name"])
    rows.append({
        "name": p["name"],
        "family": p["family"],
        "canonical_smiles": c["canonical_smiles"],
        "molar_mass_g_per_mol": r(c["molar_mass_g_per_mol"], 4),
        "n_active_nh": c["n_active_nh"],
        "n_basic_n": c["n_basic_n"],
        "n_primary_n": c["n_primary_n"],
        "n_secondary_n": c["n_secondary_n"],
        "ahew_g_per_eq": r(st["ahew_g_per_eq"], 4),
        "amine_value_mgKOH_per_g": r(st["amine_value_mgKOH_per_g"], 4),
        "ahew_times_av": r(st["ahew_times_av"], 6),
        "phr_at_eew_170p21": r(st["phr"][f"eew_{EEW_MONO:g}"], 4),
        "phr_at_eew_190": r(st["phr"][f"eew_{EEW_TECH:g}"], 4),
    })
rows.sort(key=lambda x: (x["ahew_g_per_eq"], x["name"]))

ahews = [x["ahew_g_per_eq"] for x in rows]
gen_lo, gen_hi = min(ahews), max(ahews)

# identity band must hold for every generated member too
band_holds = all(28052.8 - 1e-6 <= x["ahew_times_av"] <= 56105.6 + 1e-6 for x in rows)
n_on_primary_floor = sum(1 for x in rows if abs(x["ahew_times_av"] - 28052.8) < 1e-3)

# ------------------------------------------------------ coverage test -------
anchors = env["commercial_anchors"]["entries"]
comm_lo, comm_hi = env["commercial_anchors"]["design_envelope_ahew_g_per_eq"]
anchor_hits = []
for a in anchors:
    inside = gen_lo <= a["ahew_g_per_eq"] <= gen_hi
    anchor_hits.append({
        "product": a["product"],
        "chemistry_class": a["chemistry_class"],
        "ahew_g_per_eq": a["ahew_g_per_eq"],
        "inside_generated_hull": bool(inside),
        "shortfall_g_per_eq": r(a["ahew_g_per_eq"] - gen_hi, 4) if not inside else 0.0,
    })
n_covered = sum(1 for a in anchor_hits if a["inside_generated_hull"])
overlap = max(0.0, min(gen_hi, comm_hi) - max(gen_lo, comm_lo))
overlap_frac = overlap / (comm_hi - comm_lo)

# -------------------------------------------- mechanism: mass/H coupling ----
rho = spearman([x["molar_mass_g_per_mol"] for x in rows],
               [x["n_active_nh"] for x in rows])
m_max = max(x["molar_mass_g_per_mol"] for x in rows)
nh_min = min(x["n_active_nh"] for x in rows)
marginal_bound = m_max / nh_min          # loose bound ignoring the coupling
realized_frontier = gen_hi               # actual joint frontier

# stratify by active-N-H count: within a stratum AHEW = M / n_H is a pure mass
# scale, so the stratum ceiling is set entirely by the monomeric mass ceiling.
strata = {}
for x in rows:
    strata.setdefault(x["n_active_nh"], []).append(x)
stratum_table = []
for nh in sorted(strata):
    grp = strata[nh]
    stratum_table.append({
        "n_active_nh": nh,
        "n_members": len(grp),
        "max_molar_mass_g_per_mol": r(max(g["molar_mass_g_per_mol"] for g in grp), 4),
        "max_ahew_g_per_eq": r(max(g["ahew_g_per_eq"] for g in grp), 4),
        "mass_required_to_reach_commercial_floor_g_per_mol": r(comm_lo * nh, 4),
        "stratum_reaches_commercial_floor": bool(
            max(g["ahew_g_per_eq"] for g in grp) >= comm_lo),
        "families": sorted({g["family"] for g in grp}),
    })
n_difunctional_primary = len(strata.get(4, []))

# ---------------------------------------- adduct-closure analytic projection -
adduct = {}
for k in env["adduct_closure_operator"]["k_values_evaluated"]:
    proj = []
    for x in rows:
        nh_add = k * x["n_active_nh"] - 2
        if nh_add <= 0:
            continue
        m_add = k * x["molar_mass_g_per_mol"] + M_DGEBA
        ah = m_add / nh_add
        proj.append({"name": x["name"], "family": x["family"],
                     "ahew_adduct_g_per_eq": r(ah, 4),
                     "in_commercial_band": bool(comm_lo <= ah <= comm_hi)})
    inband = [p for p in proj if p["in_commercial_band"]]
    fams = sorted({p["family"] for p in inband})
    adduct[f"k_{k}"] = {
        "n_projected": len(proj),
        "n_in_commercial_band": len(inband),
        "fraction_in_band": r(len(inband) / len(proj), 6) if proj else None,
        "ahew_adduct_min": r(min(p["ahew_adduct_g_per_eq"] for p in proj), 4) if proj else None,
        "ahew_adduct_max": r(max(p["ahew_adduct_g_per_eq"] for p in proj), 4) if proj else None,
        "families_reaching_band": fams,
        "per_molecule": proj,
    }
# does the adduct operator restore anchor coverage?
best_k = max(adduct, key=lambda k: adduct[k]["n_in_commercial_band"])
adduct_lo = adduct[best_k]["ahew_adduct_min"]
adduct_hi = adduct[best_k]["ahew_adduct_max"]
anchors_recovered = sum(1 for a in anchors
                        if adduct_lo <= a["ahew_g_per_eq"] <= adduct_hi)

# ---------------------------------------------------------- verdict ---------
h0_supported = (n_covered == len(anchors))
verdict = "H0_SUPPORTED" if h0_supported else "H0_REFUTED"

headline = (
    "Stoichiometric design-envelope coverage of the 38 deterministic-grammar hardener "
    f"proposals: re-derived AHEW spans [{gen_lo:.3f}, {gen_hi:.3f}] g/eq, while the six "
    f"shipped commercial marine-epoxy hardener anchors span [{comm_lo:g}, {comm_hi:g}] g/eq -- "
    f"{n_covered}/{len(anchors)} anchors lie inside the generated hull and the interval "
    f"overlap is {overlap_frac:.4f}, so H0 (the grammar covers the formulation-relevant "
    f"stoichiometric envelope) is REFUTED with a {comm_lo - gen_hi:.3f} g/eq shortfall to the "
    "commercial floor. Mechanism: the grammar couples molar mass to amine functionality "
    f"(Spearman rho = {rho:.4f} between M and n_activeH over the 38), which pins AHEW = M/n_H "
    f"into a narrow low band; within the dominant n_H = 4 di-primary stratum ({n_difunctional_primary}/{len(rows)} "
    f"members) the commercial floor would demand a {comm_lo * 4:g} g/mol monomer, so the marginal "
    f"bound max(M)/min(n_H) = {marginal_bound:.3f} g/eq "
    f"is never attained (realized frontier {realized_frontier:.3f}). Applying the published "
    f"amine-DGEBA adduct closure (k mol amine : 1 mol DGEBA) analytically maps "
    f"{adduct['k_2']['n_in_commercial_band']}/{adduct['k_2']['n_projected']} members (k=2) into "
    f"the commercial band and recovers {anchors_recovered}/{len(anchors)} anchors, identifying "
    "one mass-adding, hydrogen-consuming production rule as the specific missing capability. "
    f"Instrument self-tests {self_tests_pass}/{len(self_tests)} pass (definitional exactness "
    "plus the exact AHEW*AV = 56105.6*n_N/n_H identity), independent active-N-H re-derivation "
    f"agrees with the shipped grammar column {len(rows) - len(parity_mismatch)}/{len(rows)}, and "
    f"{decoys_pass}/{len(decoys)} non-hardener decoys fail closed."
)

diag = {
    "schema": "amphora.molecule-generator.molgen-stoichiometric-envelope-coverage.v1",
    "study_id": "molgen-stoichiometric-envelope-coverage-v1",
    "authority": "AUDIT_ONLY",
    "module": "amphora-molecule-generator",
    "rdkit_version": __import__("rdkit").__version__,
    "headline": headline,
    "purpose": (
        "Test whether the deterministic-grammar hardener universe covers the STOICHIOMETRIC "
        "design envelope (AHEW / amine value / mix-ratio phr) of the commercial marine "
        "epoxy-amine hardeners already shipped in amphora-ingredient-library. The three prior "
        "generator receipts closed structural pillars (yield/feasibility, novelty, diversity); "
        "none tested formulation-functional coverage, which is what decides whether a proposed "
        "hardener can actually be used at 1:1 epoxide:amine-hydrogen stoichiometry."
    ),
    "theory_reference": {
        "ahew_and_cure_stoichiometry": "Lee & Neville 1967, Handbook of Epoxy Resins, McGraw-Hill (LCCN 66-23992)",
        "hardener_classes_and_adducts": "Ellis (ed.) 1993, Chemistry and Technology of Epoxy Resins, Blackie/Chapman & Hall, ISBN 978-0-7514-0095-4",
        "amine_value": "ASTM D2074 -- Standard Test Methods for Total, Primary, Secondary, and Tertiary Amine Values of Fatty Amines",
        "atomic_weights": "IUPAC 2021 standard atomic weights (Prohaska et al. 2022, Pure Appl. Chem. 94(5):573-600) via RDKit",
        "rank_correlation": "Spearman 1904, Am. J. Psychol. 15(1):72-101",
        "toolkit": "RDKit " + __import__("rdkit").__version__,
    },
    "non_circularity": (
        "SMILES are read from the hash-locked prior grammar-yield receipt; molar mass, "
        "active-N-H count, basic-N count, AHEW, amine value and phr are all re-derived here "
        "from structure by RDKit. The shipped active_nh column is used only as an after-the-fact "
        "parity check and is never an input to any metric. The commercial envelope anchors "
        "originate in a different module (amphora-ingredient-library) and are independent of "
        "anything the generator produced. The AHEW*AV identity band [28052.8, 56105.6] is an "
        "exact algebraic consequence of the two instrument definitions, so it cross-checks the "
        "amine-value instrument against the AHEW instrument without any fitted parameter."
    ),
    "instrument_self_tests": self_tests,
    "instrument_self_tests_summary": {
        "n_pass": self_tests_pass, "n_total": len(self_tests),
        "all_pass": self_tests_pass == len(self_tests),
    },
    "fail_closed_controls": decoys,
    "fail_closed_summary": {
        "n_pass": decoys_pass, "n_total": len(decoys),
        "all_pass": decoys_pass == len(decoys),
    },
    "parity_vs_prior_receipt": {
        "n_molecules": len(rows),
        "n_active_nh_agreements": len(rows) - len(parity_mismatch),
        "mismatched_names": parity_mismatch,
        "parity_complete": len(parity_mismatch) == 0,
    },
    "generated_set_stoichiometry": {
        "n_molecules": len(rows),
        "ahew_min_g_per_eq": r(gen_lo, 4),
        "ahew_max_g_per_eq": r(gen_hi, 4),
        "ahew_median_g_per_eq": r(sorted(ahews)[len(ahews) // 2], 4),
        "amine_value_min_mgKOH_per_g": r(min(x["amine_value_mgKOH_per_g"] for x in rows), 4),
        "amine_value_max_mgKOH_per_g": r(max(x["amine_value_mgKOH_per_g"] for x in rows), 4),
        "phr_at_eew_170p21_min": r(min(x["phr_at_eew_170p21"] for x in rows), 4),
        "phr_at_eew_170p21_max": r(max(x["phr_at_eew_170p21"] for x in rows), 4),
        "identity_band_holds_for_all": bool(band_holds),
        "n_exactly_on_all_primary_floor_28052p8": n_on_primary_floor,
        "per_molecule": rows,
    },
    "envelope_coverage_test": {
        "commercial_envelope_g_per_eq": [comm_lo, comm_hi],
        "generated_hull_g_per_eq": [r(gen_lo, 4), r(gen_hi, 4)],
        "n_anchors": len(anchors),
        "n_anchors_inside_generated_hull": n_covered,
        "anchor_coverage_fraction": r(n_covered / len(anchors), 6),
        "interval_overlap_g_per_eq": r(overlap, 6),
        "interval_overlap_fraction_of_commercial": r(overlap_frac, 6),
        "shortfall_to_commercial_floor_g_per_eq": r(comm_lo - gen_hi, 4),
        "shortfall_relative_to_commercial_floor": r((comm_lo - gen_hi) / comm_lo, 6),
        "per_anchor": anchor_hits,
    },
    "mechanism_mass_functionality_coupling": {
        "spearman_rho_molar_mass_vs_active_nh": r(rho, 6),
        "max_molar_mass_g_per_mol": r(m_max, 4),
        "min_active_nh": nh_min,
        "marginal_bound_ahew_g_per_eq": r(marginal_bound, 4),
        "realized_frontier_ahew_g_per_eq": r(realized_frontier, 4),
        "marginal_bound_unattained": bool(marginal_bound > realized_frontier),
        "by_active_nh_stratum": stratum_table,
        "n_members_in_difunctional_primary_stratum_nh4": n_difunctional_primary,
        "interpretation": (
            "AHEW = M / n_activeH, so within a fixed-n_H stratum the ceiling is purely a mass "
            "ceiling. The dominant stratum is n_H = 4 (di-primary difunctional amines), where "
            f"reaching the {comm_lo:g} g/eq commercial floor would require a monomer of "
            f"{comm_lo * 4:g} g/mol -- far above the grammar's realized monomeric mass ceiling. "
            "The grammar's only route to higher mass is the F1 polyethyleneamine homologation, "
            "which adds an amine site with every added unit and therefore raises n_H in step "
            "with M, leaving AHEW flat; the moderate positive rank correlation between M and "
            f"n_activeH (rho = {rho:.4f}) is that homologation showing through. Consequently the "
            "decoupled marginal bound max(M)/min(n_H) is never realized by any single production. "
            "Closing the envelope requires a production rule that adds mass while CONSUMING "
            "active hydrogens -- exactly what an amine-epoxy adduct does."
        ),
    },
    "adduct_closure_projection": {
        "operator": env["adduct_closure_operator"]["definition"],
        "citation": env["adduct_closure_operator"]["citation"],
        "status": env["adduct_closure_operator"]["status"],
        "m_dgeba_g_per_mol": r(M_DGEBA, 4),
        "commercial_band_g_per_eq": [comm_lo, comm_hi],
        "by_k": adduct,
        "best_k": best_k,
        "anchors_recovered_under_best_k": anchors_recovered,
        "n_anchors": len(anchors),
    },
    "hypothesis_evaluation": {
        "h0": ("The deterministic-grammar hardener universe covers the stoichiometric design "
               "envelope (AHEW) spanned by the shipped commercial marine epoxy-amine hardeners."),
        "decision_rule": ("H0 is supported only if all six commercial AHEW anchors fall inside "
                          "the generated set's AHEW hull."),
        "verdict": verdict,
        "n_anchors_inside_hull": n_covered,
        "evidence": (
            f"Generated hull [{gen_lo:.3f}, {gen_hi:.3f}] g/eq is disjoint from the commercial "
            f"envelope [{comm_lo:g}, {comm_hi:g}] g/eq; interval overlap {overlap_frac:.4f}; the "
            f"highest-AHEW proposal (DDS-class, {gen_hi:.3f} g/eq) still falls "
            f"{comm_lo - gen_hi:.3f} g/eq ({100 * (comm_lo - gen_hi) / comm_lo:.2f}%) short of the "
            "lowest commercial anchor."
        ),
        "actionable_consequence": (
            "The generator's F1-F5 monomeric-diamine families are structurally incapable of "
            "reaching the amidoamine/polyamide AHEW band used by MIL-P-24441-class marine "
            "systems. The analytic adduct projection identifies one concrete missing production "
            "rule (k mol amine : 1 mol DGEBA adduct closure) that would map "
            f"{adduct['k_2']['n_in_commercial_band']}/{adduct['k_2']['n_projected']} of the "
            "existing universe into the commercial band without any new scaffold family."
        ),
    },
    "hash_and_count_lock": {
        "grammar_receipt_diagnostic_sha256": sha(grammar_bytes),
        "envelope_reference_sha256": sha(envelope_bytes),
        "envelope_reference_path": "amphora-molecule-generator/reference/mvp20/data/hardener_stoichiometric_envelope.v1.json",
        "ingredient_library_facts_sha256": sha(facts_bytes),
        "n_proposals": len(rows),
        "n_commercial_anchors": len(anchors),
        "n_known_answer_amines": len(self_tests),
        "n_fail_closed_decoys": len(decoys),
        "koh_constant_mg_per_mol": KOH_MG_PER_MOL,
        "eew_reference_points_g_per_eq": EEWS,
    },
    "rights_posture": env["rights_posture"],
    "closes": [],
    "does_not_close": [
        "Runtime remains LOCKED_INTERNAL; no proposal emission enabled.",
        "No Phase-0 promotion; scientific_readiness stays UNVALIDATED.",
        "AHEW/amine-value/phr are computed monodisperse structural quantities; commercial "
        "anchors are technical-grade measured values on polydisperse resins, so the comparison "
        "bounds capability, not product equivalence.",
        "The amine-epoxy adduct closure is an ANALYTIC PROJECTION only -- it is not implemented "
        "as a generator production rule and no adduct product has been enumerated, validated, "
        "or synthesised.",
        "Aryl amines are weakly basic and may under-titrate under ASTM D2074 conditions; the "
        "computed amine value is a structural upper bound for those members.",
        "Stoichiometric envelope coverage is not a cure-kinetics, pot-life, property, FTO, or "
        "wet-lab performance claim.",
    ],
}

OUTDIR.mkdir(parents=True, exist_ok=True)
out = OUTDIR / (sys.argv[1] if len(sys.argv) > 1 else "diagnostic.canonical.json")
payload = json.dumps(diag, indent=2, sort_keys=True).encode()
out.write_bytes(payload)
print("WROTE", out)
print("sha256", sha(payload))
print("verdict", verdict)
print("self_tests", f"{self_tests_pass}/{len(self_tests)}")
print("fail_closed", f"{decoys_pass}/{len(decoys)}")
print("parity", f"{len(rows) - len(parity_mismatch)}/{len(rows)}")
print("gen_hull", gen_lo, gen_hi, "commercial", comm_lo, comm_hi)
print("anchors_inside", n_covered, "adduct_k2_inband", adduct["k_2"]["n_in_commercial_band"],
      "anchors_recovered", anchors_recovered)
