#!/usr/bin/env python3
"""CF-ARITH: envelope arithmetic for the candidate epoxy-polyamide formulation.

Builds a candidate 2K epoxy-polyamide BOM from real, cited amphora-ingredient-library
facts, derives the stoichiometric (EEW/AHEW) hardener demand and a solvent/pigment
split that lands the charter's 1:1-by-volume mix ratio and 65%+/-2% volume-solids
target, then INDEPENDENTLY re-derives volume-solids / VOC / mix-ratio from the final
BOM table via a forward summation function that has no knowledge of the design
algebra used to construct the BOM. Every envelope threshold is read live from
amphora-envelope-gates/reference/mvp20/charter/v5_requirements.json -- none is
retyped as a literal in this script.

Also runs the attack: perturbs one ingredient density in a BOM copy and checks
that the same forward-computation + charter-bound checker correctly flags the
resulting breach (positive control for a CLAIM_SURVIVED verdict).
"""
import hashlib
import json
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
CHARTER_PATH = ROOT / "amphora-envelope-gates/reference/mvp20/charter/v5_requirements.json"
FACTS_PATH = ROOT / "amphora-ingredient-library/reference/mvp20/data/facts.json"


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load_json(p: Path):
    return json.loads(p.read_text())


charter = load_json(CHARTER_PATH)
charter_sha256 = sha256_file(CHARTER_PATH)
facts_doc = load_json(FACTS_PATH)
facts = facts_doc["entries"]
facts_sha256 = sha256_file(FACTS_PATH)

# ---------------------------------------------------------------------------
# Envelope constants -- read live from the charter file only, never retyped.
# ---------------------------------------------------------------------------
fc = charter["fixed_constraints"]
pe = charter["performance_envelope"]

mix_ratio_spec = fc["mix_ratio_by_volume"]          # {"A":1,"B":1,"kind":"nominal","engine_tolerance_pct":3}
vs_spec = fc["volume_solids_pct"]                    # {"target":65,"tol":2,"min":63,"max":67}
voc_spec = fc["voc_g_per_l"]                         # {"max":340,"design_to":320,"method":...}
dft_spec = fc["dft_mils_per_coat"]                   # {"min":4.5,"max":6.0}
wft_spec = pe["wft_mils"]                            # {"min":7.0,"max":9.0}
pot_life_spec = pe["pot_life_h"]                     # {"min":1.5,"condition":...}

ENVELOPE_CITATIONS = {
    "mix_ratio_by_volume": {"path": "amphora-envelope-gates/reference/mvp20/charter/v5_requirements.json",
                             "sha256": charter_sha256, "json_pointer": "/fixed_constraints/mix_ratio_by_volume",
                             "value": mix_ratio_spec},
    "volume_solids_pct": {"path": "amphora-envelope-gates/reference/mvp20/charter/v5_requirements.json",
                           "sha256": charter_sha256, "json_pointer": "/fixed_constraints/volume_solids_pct",
                           "value": vs_spec},
    "voc_g_per_l": {"path": "amphora-envelope-gates/reference/mvp20/charter/v5_requirements.json",
                     "sha256": charter_sha256, "json_pointer": "/fixed_constraints/voc_g_per_l",
                     "value": voc_spec},
    "dft_mils_per_coat": {"path": "amphora-envelope-gates/reference/mvp20/charter/v5_requirements.json",
                           "sha256": charter_sha256, "json_pointer": "/fixed_constraints/dft_mils_per_coat",
                           "value": dft_spec},
    "wft_mils": {"path": "amphora-envelope-gates/reference/mvp20/charter/v5_requirements.json",
                  "sha256": charter_sha256, "json_pointer": "/performance_envelope/wft_mils",
                  "value": wft_spec},
    "pot_life_h": {"path": "amphora-envelope-gates/reference/mvp20/charter/v5_requirements.json",
                    "sha256": charter_sha256, "json_pointer": "/performance_envelope/pot_life_h",
                    "value": pot_life_spec},
}

# ---------------------------------------------------------------------------
# Ingredient facts -- read live from amphora-ingredient-library facts.json.
# ---------------------------------------------------------------------------
def fact(key):
    rec = facts[key]
    return rec["value"], rec

EEW_R, eew_r_rec = fact("resin.dgeba_828.eew")
RHO_R, rho_r_rec = fact("resin.dgeba_828.density")
AHEW_H, ahew_h_rec = fact("hardener.ancamide_2353.ahew")
RHO_H, rho_h_rec = fact("hardener.ancamide_2353.density")
RHO_ZP, rho_zp_rec = fact("pigment.zinc_phosphate.density")
RHO_TALC, rho_talc_rec = fact("pigment.talc.density")
RHO_XYL, rho_xyl_rec = fact("solvent.xylene.density")
RHO_BUOH, rho_buoh_rec = fact("solvent.n_butanol.density")

INGREDIENT_CITATIONS = {
    "resin.dgeba_828.eew": eew_r_rec, "resin.dgeba_828.density": rho_r_rec,
    "hardener.ancamide_2353.ahew": ahew_h_rec, "hardener.ancamide_2353.density": rho_h_rec,
    "pigment.zinc_phosphate.density": rho_zp_rec, "pigment.talc.density": rho_talc_rec,
    "solvent.xylene.density": rho_xyl_rec, "solvent.n_butanol.density": rho_buoh_rec,
}

# ---------------------------------------------------------------------------
# Design algebra: build a BOM (per 100 g DGEBA-828 resin basis) that lands
# stoichiometric EEW/AHEW balance, then solve for pigment loading (PVC) and
# solvent A/B split so the mixed system lands 1:1 volume and target VS%.
# ---------------------------------------------------------------------------
R_MASS = 100.0                       # g DGEBA-828, resin basis
PVC = 0.25                           # pigment volume conc. of total solids volume (design choice, marine anti-corrosive primer range)
PIGMENT_ZP_VOL_FRAC = 0.60           # of pigment volume: zinc phosphate (inhibitive) vs talc (extender)
SOLVENT_XYL_VOL_FRAC = 0.80          # of solvent volume: xylene vs n-butanol (HSP-matched coalescing blend)

VS_TARGET = vs_spec["target"] / 100.0

# stoichiometric hardener mass: n_eq(resin) = R/EEW_R; mass_hardener = n_eq * AHEW_H
H_MASS = R_MASS * (AHEW_H / EEW_R)

V_r = R_MASS / RHO_R
V_h = H_MASS / RHO_H

V_p = PVC * (V_r + V_h) / (1.0 - PVC)
V_zp = PIGMENT_ZP_VOL_FRAC * V_p
V_talc = (1.0 - PIGMENT_ZP_VOL_FRAC) * V_p
M_zp = V_zp * RHO_ZP
M_talc = V_talc * RHO_TALC

V_solids = V_r + V_h + V_p
V_solvent_total = V_solids * (1.0 - VS_TARGET) / VS_TARGET

V_xyl = SOLVENT_XYL_VOL_FRAC * V_solvent_total
V_buoh = (1.0 - SOLVENT_XYL_VOL_FRAC) * V_solvent_total
M_xyl = V_xyl * RHO_XYL
M_buoh = V_buoh * RHO_BUOH

# Solve solvent A/B split fraction f_A so that V_A == V_B (1:1 by volume).
# V_A = V_r + V_p + f_A*V_solvent_total ; V_B = V_h + (1-f_A)*V_solvent_total
f_A = (V_h + V_solvent_total - V_r - V_p) / (2.0 * V_solvent_total)

M_xyl_A = f_A * M_xyl
M_buoh_A = f_A * M_buoh
M_xyl_B = (1.0 - f_A) * M_xyl
M_buoh_B = (1.0 - f_A) * M_buoh

BOM = {
    "part_A": [
        {"name": "resin.dgeba_828", "mass_g": R_MASS, "density_key": "resin.dgeba_828.density",
         "density_g_ml": RHO_R, "nonvolatile": True, "role": "epoxy resin (binder)"},
        {"name": "pigment.zinc_phosphate", "mass_g": M_zp, "density_key": "pigment.zinc_phosphate.density",
         "density_g_ml": RHO_ZP, "nonvolatile": True, "role": "anti-corrosive inhibitive pigment"},
        {"name": "pigment.talc", "mass_g": M_talc, "density_key": "pigment.talc.density",
         "density_g_ml": RHO_TALC, "nonvolatile": True, "role": "extender"},
        {"name": "solvent.xylene", "mass_g": M_xyl_A, "density_key": "solvent.xylene.density",
         "density_g_ml": RHO_XYL, "nonvolatile": False, "role": "diluent (VOC)"},
        {"name": "solvent.n_butanol", "mass_g": M_buoh_A, "density_key": "solvent.n_butanol.density",
         "density_g_ml": RHO_BUOH, "nonvolatile": False, "role": "coalescing/coupling solvent (VOC)"},
    ],
    "part_B": [
        {"name": "hardener.ancamide_2353", "mass_g": H_MASS, "density_key": "hardener.ancamide_2353.density",
         "density_g_ml": RHO_H, "nonvolatile": True, "role": "polyamide curing agent"},
        {"name": "solvent.xylene", "mass_g": M_xyl_B, "density_key": "solvent.xylene.density",
         "density_g_ml": RHO_XYL, "nonvolatile": False, "role": "curing-agent-side diluent (VOC)"},
        {"name": "solvent.n_butanol", "mass_g": M_buoh_B, "density_key": "solvent.n_butanol.density",
         "density_g_ml": RHO_BUOH, "nonvolatile": False, "role": "curing-agent-side diluent (VOC)"},
    ],
}


# ---------------------------------------------------------------------------
# INDEPENDENT forward re-derivation: pure summation over the final BOM table.
# This function has NO knowledge of PVC / f_A / the design algebra above --
# it only ever sees (name, mass_g, density_g_ml, nonvolatile) rows, exactly
# as a bench chemist reading the BOM off a page would recompute it.
# ---------------------------------------------------------------------------
def forward_recompute(bom, density_overrides=None):
    density_overrides = density_overrides or {}
    rows = []
    for part_name, items in bom.items():
        for item in items:
            rho = density_overrides.get((part_name, item["name"]), item["density_g_ml"])
            vol = item["mass_g"] / rho
            rows.append({**item, "part": part_name, "density_used_g_ml": rho, "volume_ml": vol})

    def part_volume(part_name):
        return sum(r["volume_ml"] for r in rows if r["part"] == part_name)

    V_A = part_volume("part_A")
    V_B = part_volume("part_B")
    total_volume_ml = V_A + V_B
    solids_volume_ml = sum(r["volume_ml"] for r in rows if r["nonvolatile"])
    voc_mass_g = sum(r["mass_g"] for r in rows if not r["nonvolatile"])

    volume_solids_pct = 100.0 * solids_volume_ml / total_volume_ml
    voc_g_per_l = voc_mass_g / (total_volume_ml / 1000.0)
    mix_ratio_A_over_B = V_A / V_B

    return {
        "rows": rows,
        "V_A_ml": V_A,
        "V_B_ml": V_B,
        "total_volume_ml": total_volume_ml,
        "solids_volume_ml": solids_volume_ml,
        "voc_mass_g": voc_mass_g,
        "volume_solids_pct": volume_solids_pct,
        "voc_g_per_l": voc_g_per_l,
        "mix_ratio_A_over_B": mix_ratio_A_over_B,
    }


def check_against_charter(fr):
    """Charter-bound pass/fail checker. Bounds read live from `charter`, not hardcoded."""
    results = {}

    ratio = fr["mix_ratio_A_over_B"]
    tol = mix_ratio_spec["engine_tolerance_pct"] / 100.0
    nominal = mix_ratio_spec["A"] / mix_ratio_spec["B"]
    lo, hi = nominal * (1 - tol), nominal * (1 + tol)
    results["mix_ratio_by_volume"] = {
        "observed": ratio, "nominal": nominal, "lo": lo, "hi": hi,
        "passed": lo <= ratio <= hi,
    }

    vs = fr["volume_solids_pct"]
    results["volume_solids_pct"] = {
        "observed": vs, "min": vs_spec["min"], "max": vs_spec["max"],
        "passed": vs_spec["min"] <= vs <= vs_spec["max"],
    }

    voc = fr["voc_g_per_l"]
    results["voc_g_per_l"] = {
        "observed": voc, "max": voc_spec["max"],
        "passed": voc <= voc_spec["max"],
    }

    dft_min = wft_spec["min"] * (vs / 100.0)
    dft_max = wft_spec["max"] * (vs / 100.0)
    results["dft_mils_per_coat"] = {
        "observed_range": [dft_min, dft_max],
        "charter_min": dft_spec["min"], "charter_max": dft_spec["max"],
        "passed": (dft_min >= dft_spec["min"] * 0.999) and (dft_max <= dft_spec["max"] * 1.001),
    }

    results["all_passed"] = all(v["passed"] for v in results.values() if isinstance(v, dict) and "passed" in v)
    return results


# ---------------------------------------------------------------------------
# Run 1: unperturbed (real, cited densities) -- must PASS.
# ---------------------------------------------------------------------------
fr_real = forward_recompute(BOM)
check_real = check_against_charter(fr_real)

# ---------------------------------------------------------------------------
# Run 2: perturbation attack -- plant a defect in ONE ingredient density in a
# BOM copy (xylene density mis-transcribed +40%, e.g. confused with a heavier
# aromatic solvent) and confirm the SAME checker fires (detects a breach).
# The BOM masses (what would actually be weighed into the batch) are left
# untouched; only the density used to convert those masses to volumes is
# perturbed, exactly as the attack shape in the campaign item specifies.
# ---------------------------------------------------------------------------
PERTURBED_DENSITY_FACTOR = 1.40
perturbed_xylene_density = RHO_XYL * PERTURBED_DENSITY_FACTOR
density_overrides = {
    ("part_A", "solvent.xylene"): perturbed_xylene_density,
    ("part_B", "solvent.xylene"): perturbed_xylene_density,
}
fr_perturbed = forward_recompute(BOM, density_overrides=density_overrides)
check_perturbed = check_against_charter(fr_perturbed)

positive_control = {
    "planted_defect": f"solvent.xylene.density mis-transcribed from {RHO_XYL} g/mL to {perturbed_xylene_density:.4f} g/mL (+{(PERTURBED_DENSITY_FACTOR-1)*100:.0f}%) in both parts of a BOM copy",
    "how_planted": "density_overrides dict passed to forward_recompute() for ('part_A','solvent.xylene') and ('part_B','solvent.xylene'); BOM masses (the weighed batch quantities) are untouched -- only the mass->volume conversion constant is perturbed.",
    "detected": not check_perturbed["all_passed"],
    "evidence": {
        "real_run_all_passed": check_real["all_passed"],
        "perturbed_run_all_passed": check_perturbed["all_passed"],
        "perturbed_volume_solids_pct": fr_perturbed["volume_solids_pct"],
        "perturbed_voc_g_per_l": fr_perturbed["voc_g_per_l"],
        "perturbed_mix_ratio": fr_perturbed["mix_ratio_A_over_B"],
        "which_checks_failed": [k for k, v in check_perturbed.items() if isinstance(v, dict) and v.get("passed") is False],
    },
}

# ---------------------------------------------------------------------------
# Second independent re-derivation path: exact-rational (fractions.Fraction)
# recompute of the same forward summation, to rule out any float-rounding
# masking a bound violation near an edge.
# ---------------------------------------------------------------------------
from fractions import Fraction


def forward_recompute_exact(bom):
    rows = []
    for part_name, items in bom.items():
        for item in items:
            mass = Fraction(item["mass_g"]).limit_denominator(10**12)
            rho = Fraction(item["density_g_ml"]).limit_denominator(10**12)
            vol = mass / rho
            rows.append({"part": part_name, "name": item["name"], "nonvolatile": item["nonvolatile"], "volume_ml": vol})
    V_A = sum(r["volume_ml"] for r in rows if r["part"] == "part_A")
    V_B = sum(r["volume_ml"] for r in rows if r["part"] == "part_B")
    total = V_A + V_B
    solids = sum(r["volume_ml"] for r in rows if r["nonvolatile"])
    return {
        "volume_solids_pct_exact": float(100 * solids / total),
        "mix_ratio_exact": float(V_A / V_B),
    }


exact_check = forward_recompute_exact(BOM)
independent_agreement = {
    "volume_solids_pct_float_vs_exact_abs_diff": abs(fr_real["volume_solids_pct"] - exact_check["volume_solids_pct_exact"]),
    "mix_ratio_float_vs_exact_abs_diff": abs(fr_real["mix_ratio_A_over_B"] - exact_check["mix_ratio_exact"]),
    "agrees_within_1e-9": (
        abs(fr_real["volume_solids_pct"] - exact_check["volume_solids_pct_exact"]) < 1e-9
        and abs(fr_real["mix_ratio_A_over_B"] - exact_check["mix_ratio_exact"]) < 1e-9
    ),
}

# ---------------------------------------------------------------------------
# Pot-life: explicitly OUT OF SCOPE for this module's mass-balance/stoichiometry
# arithmetic. Not computed here; not asserted; deferred to amphora-cure-potlife.
# ---------------------------------------------------------------------------
pot_life_scope_note = (
    "pot_life_h is a reaction-kinetics property (Arrhenius/isoconversional cure "
    "kinetics), not a mass-balance or EEW/AHEW stoichiometry quantity. This "
    "module's authority_ceiling is REAL_ARITHMETIC over mass/volume/stoichiometry "
    "only; no pot-life number is asserted or derived here. The stoichiometric "
    "ratio landed above (1.000 x equivalents, i.e. EEW/AHEW-balanced, no excess "
    "amine) is the input amphora-cure-potlife's own signed class-conditional "
    "model would consume for this hardener's amine class -- that model, not this "
    "one, is the authority for any pot-life number. Charter's pot_life_h.min is "
    "cited above for completeness; it is NOT independently reproduced by this "
    "receipt and the campaign item's refutation_criterion does not name it."
)

diagnostic = {
    "schema": "amphora.cf-arith.blueprint-arithmetic.v1",
    "module": "amphora-formulation-arithmetic",
    "campaign_item_id": "CF-ARITH",
    "charter_citation": {
        "path": "amphora-envelope-gates/reference/mvp20/charter/v5_requirements.json",
        "sha256": charter_sha256,
    },
    "facts_citation": {
        "path": "amphora-ingredient-library/reference/mvp20/data/facts.json",
        "sha256": facts_sha256,
    },
    "envelope_citations": ENVELOPE_CITATIONS,
    "ingredient_citations": INGREDIENT_CITATIONS,
    "design_parameters": {
        "resin_basis_g": R_MASS, "pigment_volume_concentration": PVC,
        "pigment_zp_vol_frac_of_pigment": PIGMENT_ZP_VOL_FRAC,
        "solvent_xylene_vol_frac_of_solvent": SOLVENT_XYL_VOL_FRAC,
        "solvent_split_fraction_to_part_A": f_A,
        "stoichiometric_hardener_mass_g": H_MASS,
        "stoichiometric_equivalence_ratio": 1.0,
    },
    "bom": BOM,
    "forward_recompute_real": fr_real,
    "check_real": check_real,
    "forward_recompute_perturbed": fr_perturbed,
    "check_perturbed": check_perturbed,
    "positive_control": positive_control,
    "exact_rational_cross_check": exact_check,
    "independent_agreement": independent_agreement,
    "pot_life_scope_note": pot_life_scope_note,
    "refutation_criterion_verbatim": (
        "The shown mass-balance and stoichiometry, independently re-computed, "
        "fails to land the 1:1 volume mix, 65±2% volume solids, or ≤340 g/L VOC "
        "targets as cited from the charter, or any envelope number in the "
        "blueprint differs from that file."
    ),
    "refutation_observation_occurred": not check_real["all_passed"],
    "verdict": "CLAIM_SURVIVED" if check_real["all_passed"] and positive_control["detected"] else "CLAIM_REFUTED",
}

out_path = Path("/tmp/cf_arith_diagnostic.canonical.json")
canonical = json.dumps(diagnostic, sort_keys=True, separators=(",", ":"), indent=2)
out_path.write_text(canonical)
print(canonical[:2000])
print("...")
print(json.dumps({
    "verdict": diagnostic["verdict"],
    "check_real_all_passed": check_real["all_passed"],
    "check_perturbed_all_passed": check_perturbed["all_passed"],
    "positive_control_detected": positive_control["detected"],
    "mix_ratio_real": fr_real["mix_ratio_A_over_B"],
    "volume_solids_pct_real": fr_real["volume_solids_pct"],
    "voc_g_per_l_real": fr_real["voc_g_per_l"],
    "f_A": f_A,
}, indent=2))
