#!/usr/bin/env python3
"""W-T-ARITH: independent conformance audit of amphora-formulation-arithmetic's
dimensioned identities (VOC g/L, volume solids, weight solids, density) against
the NAMED PUBLISHED BASELINE EPA Method 24 (40 CFR Part 60, Appendix A-7,
"Determination of Volatile Matter Content, Water Content, Density, Volume
Solids, and Weight Solids of Surface Coatings"; unofficial internet version
dated October 7, 2020, retrieved 2026-08-13 from
https://www.epa.gov/sites/default/files/2020-12/documents/method_24.pdf ;
authoritative text at https://www.ecfr.gov/current/title-40/chapter-I/
subchapter-C/part-60/appendix-Appendix%20A-7%20to%20Part%2060). This is US
federal regulation, public domain (17 U.S.C. sec 105) -- no DOI/ISBN applies
to a CFR appendix; the CFR citation itself is the standard scholarly cite.

ASTM D2697 / D6093 / D1475 are CITED where Method 24 itself delegates to them
(sections 6.1-6.6) but are NOT purchased or reproduced; their text is never
quoted here, only the fact that Method 24 defers to them.

Prior fires on this claim:
  T-05 (2026-08-05): attacked EquivalentBalanceV1 stoichiometric mass-vs-volume
    basis via a live-Rust harness; found a candidate-supplied-constant
    injection defect (unrelated axis) -- REFUTED.
  CF-ARITH (2026-08-10): independently re-derived a candidate BOM's VOC/volume-
    solids envelope numbers from scratch, xylene-density positive control --
    SURVIVED.
Neither prior fire measured the module's arithmetic against a NAMED PUBLISHED
BASELINE; both compared against the module's own re-derivation or fixture.
This fire is the first to open EPA Method 24 itself and test equation-by-
equation. New attack surface: enumerate >=6 Method-24 normative requirements
and the density-basis identities derivable from them; check the module's
dimensioned reference engine (amphora-redteam-audit/benchmarks/formulation-
arithmetic-dimensioned-v1/formulation_dimensioned_audit.py, the only place in
tree the VOC/volume-solids arithmetic actually lives -- live Rust is still
MASS_ONLY per mission.md) against each one.
"""
import json
import hashlib
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-formulation-arithmetic"
DIM_DIAG = ROOT / "amphora-redteam-audit/benchmarks/formulation-arithmetic-dimensioned-v1/diagnostic.canonical.json"
UNC_DIAG = MOD / "evidence/audit/uncertainty-propagation-v1/diagnostic.canonical.json"
FACTS = ROOT / "amphora-ingredient-library/reference/mvp20/data/facts.json"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def fsha(p: Path) -> str:
    return sha(p.read_bytes())


def r(x, nd=10):
    v = round(float(x), nd)
    return 0.0 if v == 0.0 else v


# ----------------------------------------------------------------------------
# 1. Reload the module's own real-primer dimensioned computation (unmodified,
#    read-only) -- do NOT recompute it differently; the point is to check
#    THIS module's actual numbers against the baseline, not a fresh model.
# ----------------------------------------------------------------------------
dim = json.loads(DIM_DIAG.read_text())
unc = json.loads(UNC_DIAG.read_text())
primer = dim["real_formulation"]
props = primer["properties"]
totals = primer["totals"]
closure = primer["closure_residuals"]

# ----------------------------------------------------------------------------
# 2. Independent re-implementation of the SAME compute_formulation identity
#    (copied verbatim from the audited script, not altered) so we can run a
#    waterborne VARIANT the existing fixture never tests -- the fixture is
#    solvent-only (xylene + n-butanol), so Eq. 24-4's water-exclusion clause
#    has never been exercised in this module at all.
# ----------------------------------------------------------------------------
def compute_formulation(ingredients):
    M_total = V_total = M_nv = M_vol = V_solids = V_volatile = 0.0
    for ing in ingredients:
        m = ing["mass_g"]
        rho = ing["density"]
        f = ing["nonvol"]
        vol = m / rho
        nvm = m * f
        vm = m * (1.0 - f)
        M_total += m
        V_total += vol
        M_nv += nvm
        M_vol += vm
        V_solids += nvm / rho
        V_volatile += vm / rho
    rho_wet = M_total / V_total
    voc_g_L_engine_formula = 1000.0 * M_vol / V_total  # module's ACTUAL formula
    vol_solids = V_solids / V_total
    wt_solids = M_nv / M_total
    return {
        "M_total": M_total, "V_total": V_total, "M_nv": M_nv, "M_vol": M_vol,
        "rho_wet": rho_wet, "voc_g_L_engine_formula": voc_g_L_engine_formula,
        "vol_solids": vol_solids, "wt_solids": wt_solids,
    }


facts = json.loads(FACTS.read_text())["entries"]


def fv(key):
    return facts[key]["value"]


BASE_INGREDIENTS = [
    {"id": "dgeba_der331", "mass_g": 100.0, "density": fv("resin.dgeba_331.density"), "nonvol": 1.0},
    {"id": "teta_hardener", "mass_g": 13.0, "density": 0.982, "nonvol": 1.0},
    {"id": "iron_oxide_red", "mass_g": 55.0, "density": fv("pigment.iron_oxide_red.density"), "nonvol": 1.0},
    {"id": "zinc_phosphate_anticorrosive", "mass_g": 30.0, "density": fv("pigment.zinc_phosphate.density"), "nonvol": 1.0},
    {"id": "barytes_extender", "mass_g": 40.0, "density": fv("pigment.barytes.density"), "nonvol": 1.0},
    {"id": "talc_extender", "mass_g": 20.0, "density": fv("pigment.talc.density"), "nonvol": 1.0},
    {"id": "mica_barrier", "mass_g": 15.0, "density": fv("pigment.mica.density"), "nonvol": 1.0},
    {"id": "xylene_solvent", "mass_g": 45.0, "density": fv("solvent.xylene.density"), "nonvol": 0.0},
    {"id": "n_butanol_solvent", "mass_g": 15.0, "density": fv("solvent.n_butanol.density"), "nonvol": 0.0},
]

# sanity: reproduce the audited module's own real-primer numbers bit-close
# before trusting the re-implementation for the water-variant probe.
base = compute_formulation(BASE_INGREDIENTS)
reproduces_prior = {
    "total_mass_g": {"reimpl": r(base["M_total"]), "audited": totals["total_mass_g"],
                      "match": abs(base["M_total"] - totals["total_mass_g"]) < 1e-9},
    "total_volume_cm3": {"reimpl": r(base["V_total"]), "audited": totals["total_volume_cm3"],
                          "match": abs(base["V_total"] - totals["total_volume_cm3"]) < 1e-6},
    "voc_g_per_L": {"reimpl": r(base["voc_g_L_engine_formula"]), "audited": props["voc_g_per_L_epa_method24"],
                     "match": abs(base["voc_g_L_engine_formula"] - props["voc_g_per_L_epa_method24"]) < 1e-6},
    "volume_solids": {"reimpl": r(base["vol_solids"]), "audited": props["volume_solids_frac_astm_d2697"],
                       "match": abs(base["vol_solids"] - props["volume_solids_frac_astm_d2697"]) < 1e-9},
}
assert all(v["match"] for v in reproduces_prior.values()), "reimplementation does not reproduce audited engine"

# ----------------------------------------------------------------------------
# 3. Waterborne variant: add water as the module's ONLY volatile category
#    ("solvent", nonvol=0.0) since the ingredient schema has no water/exempt-
#    solvent role at all (confirmed: 0/83 facts.json entries are water or
#    exempt-solvent). Water density 1.00 g/cm3 is itself an EPA Method 24
#    analyte (section 1.1: "Water, CAS No. 7732-18-5").
# ----------------------------------------------------------------------------
WATER_MASS_G = 30.0
water_ingredients = BASE_INGREDIENTS + [
    {"id": "water_diluent", "mass_g": WATER_MASS_G, "density": 1.00, "nonvol": 0.0},
]
wet = compute_formulation(water_ingredients)

engine_naive_voc = wet["voc_g_L_engine_formula"]  # module's ACTUAL formula: 1000*M_vol/V_total, water included
M_organic_volatile = wet["M_vol"] - WATER_MASS_G   # = Wo-relevant mass per Eq. 24-4
epa_conformant_voc = 1000.0 * M_organic_volatile / wet["V_total"]  # 1000*Wo*Dc, water excluded
voc_divergence_abs = engine_naive_voc - epa_conformant_voc
voc_divergence_rel = voc_divergence_abs / epa_conformant_voc

# no-water control: with WATER_MASS_G=0 the two formulas must coincide exactly
# (this is what the existing fixture already implicitly tests, P1/P2 above).
zero_water = compute_formulation(BASE_INGREDIENTS + [{"id": "water_diluent", "mass_g": 0.0, "density": 1.00, "nonvol": 0.0}])
zw_naive = zero_water["voc_g_L_engine_formula"]
zw_conformant = 1000.0 * (zero_water["M_vol"] - 0.0) / zero_water["V_total"]
zero_water_divergence = zw_naive - zw_conformant

# ----------------------------------------------------------------------------
# 4. Requirement-by-requirement conformance table.
# ----------------------------------------------------------------------------
BASELINE = {
    "name": "EPA Method 24 -- Determination of Volatile Matter Content, Water "
            "Content, Density, Volume Solids, and Weight Solids of Surface Coatings",
    "citation": "40 CFR Part 60, Appendix A-7 (Test Methods 19 through 25E)",
    "version": "unofficial internet version dated October 7, 2020 (points to eCFR as authoritative)",
    "url_primary": "https://www.epa.gov/sites/default/files/2020-12/documents/method_24.pdf",
    "url_authoritative": "https://www.ecfr.gov/current/title-40/chapter-I/subchapter-C/part-60/appendix-Appendix%20A-7%20to%20Part%2060",
    "doi_isbn": "not applicable -- US federal regulation (40 CFR), public domain under 17 U.S.C. sec 105; CFR citation is the standard scholarly reference in place of a DOI/ISBN",
    "retrieved": "2026-08-13",
    "public_domain": True,
    "astm_conventions_cited_not_reproduced": [
        "ASTM D1475 (density of paint/varnish/lacquer) -- Method 24 sec 6.1, 11.3.3",
        "ASTM D2369 (volatile content of coatings) -- Method 24 sec 6.2, 11.2.2/11.3.1",
        "ASTM D2697 -- referenced by this module's own docs as the volume-solids convention Method 24 sec 11.3.4 delegates to ('manufacturer's formulation'); Method 24's own text does not name D2697 explicitly, D2697 is this module's citation, not the CFR's",
        "ASTM D6093 -- not cited by Method 24 text at all; appears only in this module's campaign-item framing as an alternate industry convention",
    ],
}

requirements = []


def req(rid, epa_cite, quoted, paraphrase, verdict, evidence, applies_to):
    requirements.append({
        "id": rid, "epa_citation": epa_cite, "epa_quoted_text": quoted,
        "requirement_paraphrase": paraphrase, "verdict": verdict,
        "evidence": evidence, "applies_to": applies_to,
    })


req(
    "R1", "Method 24 sec 12.5, Eq. 24-6",
    "\"Weight Fraction Solids. Ws = 1 - Wv  Eq. 24-6\"",
    "Weight fraction solids and weight fraction volatile matter must sum to exactly 1 (mass balance).",
    "CONFORMANT",
    {
        "computation": "module's own wt_solids (M_nv/M_total) + volatile weight fraction (M_vol/M_total) for the real primer",
        "wt_solids": props["weight_solids_frac"],
        "volatile_weight_frac": r(totals["volatile_mass_g"] / totals["total_mass_g"]),
        "sum": r(props["weight_solids_frac"] + totals["volatile_mass_g"] / totals["total_mass_g"], 12),
        "residual_from_1": r(props["weight_solids_frac"] + totals["volatile_mass_g"] / totals["total_mass_g"] - 1.0, 15),
    },
    "amphora-formulation-arithmetic dimensioned engine, weight_solids_frac output",
)

req(
    "R2", "Method 24 sec 12.4, Eq. 24-3/24-4/24-5",
    "\"12.4.2 Waterborne Coatings. Wo = Wv - Ww  Eq. 24-4\" ; "
    "\"12.4.3 Coatings Containing Exempt Solvents. Wo = Wv - WE - Ww  Eq. 24-5\" "
    "(contrast: \"12.4.1 Solvent-borne Coatings. Wo = Wv  Eq. 24-3\")",
    "The VOC-relevant volatile fraction (Wo, 'nonaqueous volatile matter') MUST "
    "exclude water and exempt-solvent mass from the numerator whenever either "
    "is present; only solvent-borne coatings with neither may use total "
    "volatile mass Wv directly as Wo.",
    "DIVERGENT",
    {
        "structural_gap": "amphora-ingredient-library/reference/mvp20/data/facts.json has 0/83 entries tagged water or exempt-solvent; the dimensioned engine's ingredient schema (formulation_dimensioned_audit.py) has exactly one volatile role ('solvent', nonvol=0.0) with no water/exempt distinction, so it has no way to compute Wo != Wv even in principle.",
        "engine_formula": "voc_g_L = 1000 * M_vol / V_total, where M_vol sums ALL nonvol<1 ingredient mass indiscriminately -- this is 1000*Wv*Dc, not 1000*Wo*Dc.",
        "no_water_control": {
            "note": "with water mass 0, the naive and EPA-conformant (Wo-based) formulas must coincide -- verifies the probe itself is sound",
            "engine_naive_voc_g_L": r(zw_naive),
            "epa_conformant_voc_g_L": r(zw_conformant),
            "divergence": r(zero_water_divergence, 9),
        },
        "waterborne_probe": {
            "note": "same primer + 30g water treated by the engine as an ordinary 'solvent' ingredient (density 1.00 g/cm3, the value Method 24 sec 1.1 itself assigns water, CAS 7732-18-5)",
            "engine_naive_voc_g_L_includes_water_mass": r(engine_naive_voc),
            "epa_conformant_voc_g_L_excludes_water_per_Eq24-4": r(epa_conformant_voc),
            "divergence_abs_g_per_L": r(voc_divergence_abs),
            "divergence_rel": r(voc_divergence_rel, 6),
        },
    },
    "amphora-formulation-arithmetic dimensioned engine, voc_g_per_L_epa_method24 output -- the field is even NAMED after this method while not implementing its water-exclusion clause",
)

req(
    "R3", "Method 24 sec 11.3.3 Dc + sec 12.4 Wo (density-basis identity derivable, not itself an EPA equation number)",
    "Dc (sec 11.3.3, \"Determine the density (Dc, kg/l) of the surface coating\") "
    "combined with Wo (sec 12.4) implies VOC content per liter of coating = "
    "1000 * Wo * Dc (g/L); Method 24 does not print this composite equation, "
    "it is the direct dimensional consequence of its own defined quantities.",
    "the module's VOC formula equals the EPA-derivable density-basis identity "
    "1000*Wo*Dc, provided Wo (not Wv) is used",
    "CONFORMANT_CONDITIONAL",
    {
        "no_water_case": {
            "engine_value": props["voc_g_per_L_epa_method24"],
            "derived_1000_Wo_Dc": r(1000.0 * (totals["volatile_mass_g"] / totals["total_mass_g"]) * (totals["total_mass_g"] / totals["total_volume_cm3"])),
            "abs_diff": r(abs(props["voc_g_per_L_epa_method24"] - 1000.0 * (totals["volatile_mass_g"] / totals["total_mass_g"]) * (totals["total_mass_g"] / totals["total_volume_cm3"])), 9),
        },
        "conditional_on": "R2 -- the identity only holds because the real-primer fixture happens to contain no water/exempt solvent (Wo==Wv there); it is NOT a general guarantee, as R2's waterborne probe demonstrates",
    },
    "amphora-formulation-arithmetic dimensioned engine, voc_g_per_L_epa_method24 output on the existing (solvent-only) fixture",
)

req(
    "R4", "Method 24 sec 11.3.4",
    "\"11.3.4 Solids Content. Determine the volume fraction (Vs) solids of the "
    "coating by calculation using the manufacturer's formulation.\"",
    "Method 24 itself specifies NO numeric equation for volume-fraction solids "
    "-- it explicitly delegates the calculation to 'the manufacturer's "
    "formulation' with no formula given anywhere in the method text (sections "
    "1 through 17 read in full; no Vs equation number exists alongside "
    "Eq. 24-1 through 24-6).",
    "NOT_APPLICABLE_AT_EQUATION_LEVEL",
    {
        "finding": "cannot be checked bit-for-bit against Method-24 TEXT because the text contains no such equation to check against -- this is a genuine gap in the free/public baseline, not a module defect",
        "module_convention_used": "vol_solids = V_solids / V_total (component-volume summation from mass/density) -- this is the module's own docs' citation of ASTM D2697, not a CFR-defined formula",
        "engine_value": props["volume_solids_frac_astm_d2697"],
        "closure_check": "volume_fraction_sum_minus_1 residual (module's own internal identity, not an EPA identity)",
        "closure_value": closure["volume_fraction_sum_minus_1"],
    },
    "amphora-formulation-arithmetic dimensioned engine, volume_solids_frac_astm_d2697 output",
)

req(
    "R5", "Method 24 sec 11.3.3 (\"Dc, kg/l\") and sec 12.1 nomenclature (\"Dc = Density of coating or ink, g/cm3(g/in3)\")",
    "\"Determine the density (Dc, kg/l) of the surface coating using the "
    "procedure in ASTM D 1475.\" / \"Dc = Density of coating or ink, "
    "g/cm3(g/in3).\"",
    "coating density must be a single self-consistent quantity Dc; kg/L and "
    "g/cm3 are numerically identical units (1 g/cm3 = 1 kg/L), so both of "
    "Method 24's own unit statements must agree with each other and with the "
    "mass/volume identity M_total = Dc * V_total.",
    "CONFORMANT",
    {
        "units_dimensionally_consistent": True,
        "note": "1 g/cm3 == 1 kg/L numerically; Method 24's two nomenclature statements (sec 11.3.3 kg/l vs sec 12.1 g/cm3) are the same number, not a contradiction",
        "engine_wet_density_g_cm3": props["wet_paint_density_g_cm3"],
        "engine_wet_density_g_L": props["wet_paint_density_g_L"],
        "g_cm3_times_1000_equals_g_L": r(props["wet_paint_density_g_cm3"] * 1000.0 - props["wet_paint_density_g_L"], 9),
        "density_roundtrip_residual_M_total_minus_rho_times_V": closure["density_roundtrip"],
    },
    "amphora-formulation-arithmetic dimensioned engine, wet_paint_density_g_cm3 / wet_paint_density_g_L outputs",
)

dgeba_density_input = next(i for i in unc["input_uncertainty_budget"]["inputs"] if i["name"] == "density::dgeba_der331")
req(
    "R6", "Method 24 sec 13.1, Table 24-1",
    "\"TABLE 24-1 -- ANALYTICAL PRECISION STATEMENTS ... Density, Dc "
    "Intra-laboratory +/-0.001 kg/l ; Inter-laboratory +/-0.002 kg/l\"",
    "Method 24 states the empirically-measured repeatability of a Dc "
    "determination is +/-0.001 kg/L (intra-lab) / +/-0.002 kg/L (inter-lab) "
    "-- this is a measurement-precision floor a calibrated uncertainty budget "
    "for coating density should at minimum be able to compare itself against.",
    "DIVERGENT_IN_KIND",
    {
        "finding": "the module's GUM Type-B density uncertainty (evidence/audit/uncertainty-propagation-v1) is built entirely from SUPPLIER-GRADE dispersion bands (TDS 0.5%, SUPPLIER_GUIDE 1.5%, DISTRIBUTOR 2.5%, REFERENCE_NOMINAL 3.0%) and never references or includes Method 24's Table 24-1 measurement-repeatability floor as a component at all",
        "dgeba_331_density_u_combined_kg_per_L": dgeba_density_input["u_combined"],
        "epa_intra_lab_density_precision_kg_per_L": 0.001,
        "ratio_module_uncertainty_to_epa_floor": r(dgeba_density_input["u_combined"] / 0.001, 3),
        "interpretation": "these are different uncertainty SOURCES (supplier declaration variability vs analytical measurement repeatability), so a numeric mismatch is not itself a bug -- but the module's budget has no explicit floor/component tied to the published measurement-precision standard, which is the completeness gap being reported",
    },
    "amphora-formulation-arithmetic/evidence/audit/uncertainty-propagation-v1 GUM Type-B budget, density::dgeba_der331 input",
)

req(
    "R7", "Method 24 sec 12.2, Eq. 24-1",
    "\"12.2 To determine if a coating or ink can be classified as a thin-film "
    "UV cured coating or ink, use the following equation: C = F A Dc  Eq. 24-1\"",
    "thin-film UV-radiation-cured coating classification requires substrate "
    "area (A), manufacturer film thickness (F), and coating-on-substrate mass "
    "(C).",
    "NOT_APPLICABLE",
    {
        "reason": "amphora-formulation-arithmetic has no UV-cured-coating scope and no F/A/C fields anywhere in its ingredient or formulation schema (confirmed by reading formulation_dimensioned_audit.py's compute_formulation() signature and the module's fixture)",
    },
    "n/a -- scope boundary check",
)

req(
    "R8", "Method 24 sec 9.2, 12.6",
    "\"9.2 Confidence Limits for Waterborne Coatings. Because of the inherent "
    "increased imprecision in the determination of the VOC content of "
    "waterborne coatings as the weight percent of water increases, measured "
    "parameters for waterborne coatings are replaced with appropriate "
    "confidence limits... For Wv and Dc, use the lower confidence limits; for "
    "Ww, use the upper confidence limit.\"",
    "for waterborne coatings, Method 24 requires ASYMMETRIC treatment: Wv and "
    "Dc pulled to their lower confidence bound, Ww pushed to its upper bound, "
    "when computing the reported VOC figure -- not a symmetric interval.",
    "NOT_APPLICABLE",
    {
        "reason": "the module's GUM/MC uncertainty engine (uncertainty-propagation-v1) reports symmetric two-sided intervals (ci95_lpu_low/high, mc_ci95_low/high) for every output uniformly, with no waterborne-specific asymmetric confidence-limit substitution rule; consistent with R2's finding that the module has no waterborne coating category at all, so this Method-24 requirement has no formulation in scope to apply to yet",
        "voc_g_per_L_ci95_lpu_low": unc["results"]["voc_g_per_L"]["ci95_lpu_low"],
        "voc_g_per_L_ci95_lpu_high": unc["results"]["voc_g_per_L"]["ci95_lpu_high"],
        "symmetric_around_point_estimate": True,
    },
    "amphora-formulation-arithmetic/evidence/audit/uncertainty-propagation-v1 -- and, if a waterborne formulation were ever added, this asymmetric rule would need to be implemented alongside the R2 fix",
)

n_conformant = sum(1 for x in requirements if x["verdict"] in ("CONFORMANT", "CONFORMANT_CONDITIONAL"))
n_divergent = sum(1 for x in requirements if x["verdict"] in ("DIVERGENT", "DIVERGENT_IN_KIND"))
n_na = sum(1 for x in requirements if x["verdict"].startswith("NOT_APPLICABLE"))

proposed_followups = [
    {
        "requirement_id": "R2",
        "finding": "voc_g_per_L_epa_method24 (and any downstream field derived from it) computes Wv*Dc, not Wo*Dc; it silently includes water and exempt-solvent mass in the VOC numerator whenever either is present, because the ingredient schema has no category for either. This is the same mass/volume-basis-conflation defect class the founder brief names as having already bitten this portfolio once.",
        "proposed_repair_criterion": "add explicit 'water' and 'exempt_solvent' roles (or boolean flags) to the dimensioned-engine ingredient schema; change voc_g_L computation to M_vol_organic_only/V_total per Eq. 24-3/24-4/24-5's Wo hierarchy; add a waterborne known-answer probe (e.g. this fire's 30g-water variant) asserting engine_voc == epa_conformant_voc to the known-answer battery so the gap cannot silently regress; rename the field away from '_epa_method24' suffix until the fix lands, since the current name overclaims conformance",
    },
    {
        "requirement_id": "R4",
        "finding": "Method 24 sec 11.3.4 delegates the volume-solids formula to 'the manufacturer's formulation' with no equation given in the CFR text itself; the module's ASTM-D2697-style component-volume-summation convention cannot be verified against Method 24's own (silent) text at the equation level, only cited as an industry convention.",
        "proposed_repair_criterion": "either (a) obtain lawful access to ASTM D2697 text and verify the module's Vs formula reproduces D2697's worked examples exactly, filing that as a NEW, separate paid-standard-conformance receipt (never reproducing D2697 text), or (b) explicitly document in mission.md that volume-solids arithmetic conforms to the ASTM D2697 CONVENTION by citation only and is NOT verifiable against the free EPA Method 24 text, closing this as a permanent NOT_APPLICABLE_AT_EQUATION_LEVEL rather than an open gap",
    },
    {
        "requirement_id": "R6",
        "finding": "the module's GUM Type-B density uncertainty budget never references Method 24 Table 24-1's measured intra/inter-laboratory density precision (+/-0.001 / +/-0.002 kg/L) as a floor or component, even though that table is a directly-applicable published precision statement for exactly the quantity (Dc) the budget models.",
        "proposed_repair_criterion": "add a Table-24-1-derived measurement-precision floor as an explicit additional Type-B component (or a documented lower bound) in uncertainty-propagation-v1's density budget, and report the ratio of supplier-grade dispersion to EPA measurement-precision floor per ingredient so a reader can see which term dominates",
    },
    {
        "requirement_id": "R8",
        "finding": "Method 24's asymmetric waterborne confidence-limit rule (lower bound for Wv/Dc, upper bound for Ww) has no counterpart in the module's symmetric GUM/MC intervals; currently moot only because R2 means no waterborne formulation can be correctly represented at all yet.",
        "proposed_repair_criterion": "once R2 is repaired and a waterborne ingredient category exists, add the sec 9.2/12.6 asymmetric confidence-limit substitution as an explicit computation path, gated on a 'waterborne: true' formulation flag, with its own known-answer probe",
    },
]

diagnostic = {
    "schema": "amphora.formulation-arithmetic.epa-method24-conformance-audit.v1",
    "run_type": "W-T-ARITH_NAMED_PUBLISHED_BASELINE_CONFORMANCE_AUDIT",
    "target_module": "amphora-formulation-arithmetic",
    "campaign_item_id": "W-T-ARITH",
    "claim_under_attack": {
        "receipt_path": "amphora-formulation-arithmetic/evidence/phase0/kpis/",
        "claim_text": "The arithmetic identities conform to the published standards that define them.",
    },
    "baseline": BASELINE,
    "prior_fires_on_this_claim_id": {
        "T-05_2026-08-05": "attacked stoichiometric EquivalentBalanceV1 mass-vs-volume basis via live Rust; unrelated defect found (candidate-supplied-constant injection); REFUTED",
        "CF-ARITH_2026-08-10": "independently re-derived a candidate BOM's VOC/volume-solids numbers from scratch with a xylene-density positive control; SURVIVED",
        "gap_this_fire_closes": "neither prior fire measured against a NAMED PUBLISHED BASELINE (EPA Method 24); both compared against the module's own re-derivation",
    },
    "reproduces_prior_audited_engine_output": reproduces_prior,
    "requirements": requirements,
    "requirement_count": len(requirements),
    "verdict_counts": {"conformant": n_conformant, "divergent": n_divergent, "not_applicable": n_na},
    "proposed_followups": proposed_followups,
    "positive_control": {
        "planted_defect": "added a 30 g water ingredient (density 1.00 g/cm3, the value EPA Method 24 sec 1.1 itself assigns water CAS 7732-18-5) to the real marine-primer fixture, tagged with the module's ONLY available volatile role ('solvent', nonvol=0.0) since no water-specific role exists",
        "how_planted": "in-memory ingredient list for the re-implemented compute_formulation() call only -- no in-tree file was modified; BASE_INGREDIENTS (from formulation_dimensioned_audit.py, unmodified) plus one appended dict {id: water_diluent, mass_g: 30.0, density: 1.00, nonvol: 0.0}",
        "detected": bool(abs(voc_divergence_abs) > 1.0),
        "evidence": {
            "engine_naive_voc_g_per_L": r(engine_naive_voc),
            "epa_conformant_voc_g_per_L": r(epa_conformant_voc),
            "divergence_abs_g_per_L": r(voc_divergence_abs),
            "divergence_rel": r(voc_divergence_rel, 6),
            "zero_water_control_divergence": r(zero_water_divergence, 9),
        },
        "note": "included for rigor even though the overall verdict is CLAIM_REFUTED (which does not strictly require a positive control) -- demonstrates the R2 divergence is a real, structural, repeatable defect and not a one-off arithmetic slip: the zero-water control shows the two formulas coincide exactly (divergence 0.0) when no water is present, and diverge by the water's full mass contribution the instant water is added, exactly as Eq. 24-4 predicts.",
    },
    "overall_verdict": "CLAIM_REFUTED",
    "overall_verdict_reasoning": (
        "R2 is a genuine, structural divergence from EPA Method 24 Eq. 24-3/24-4/24-5: "
        "the module's voc_g_per_L_epa_method24 field -- named for this exact method -- "
        "computes Wv*Dc (total volatile mass basis) unconditionally, never Wo*Dc "
        "(nonaqueous-volatile-only basis), because its ingredient schema has no water "
        "or exempt-solvent category at all (0/83 facts.json entries). Method 24 makes "
        "this exclusion non-optional the moment water or an exempt solvent is present "
        "(Eq. 24-4, Eq. 24-5). The waterborne probe shows a "
        + str(r(voc_divergence_rel * 100, 1))
        + "% VOC overstatement versus the EPA-conformant value on a realistic 30g-water "
        "addition to the module's own marine-primer fixture. This is the SAME mass/"
        "volume-basis-conflation defect CLASS already found once in this portfolio "
        "(amphora-known-answer-benchmarks ARITH-A221-X70P1-VOLUME-SOLIDS, "
        "2026-08-03) -- a self-referential fixture that never exercised the water/"
        "exempt-solvent path let it go undetected until measured against the actual "
        "regulatory text. R4/R6/R8 are additional, lower-severity gaps filed as "
        "proposed_followups. R1/R3/R5/R7 hold as CONFORMANT/NOT_APPLICABLE for the "
        "cases they cover."
    ),
}

out = Path("/tmp/w_t_arith_diagnostic.canonical.json")
out.write_text(json.dumps(diagnostic, indent=2, sort_keys=True))
print("WROTE", out)
print("requirement_count:", len(requirements))
print("verdict_counts:", diagnostic["verdict_counts"])
print("overall_verdict:", diagnostic["overall_verdict"])
print("voc_divergence_abs:", r(voc_divergence_abs), "rel:", r(voc_divergence_rel, 4))
print("sha256:", sha(out.read_bytes()))
