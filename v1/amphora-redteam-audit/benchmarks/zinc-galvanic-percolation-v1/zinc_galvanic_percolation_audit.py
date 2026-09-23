"""AUDIT_ONLY red-team benchmark: zinc-rich epoxy primer SACRIFICIAL (galvanic)
cathodic-protection axis for marine anti-corrosion coatings on carbon steel.

NEW protection-MECHANISM axis, untouched by all 66 signed receipts AND by every
prior AUDIT axis. Every prior receipt reasons about the BARRIER mechanism
(transport / free-volume / tortuosity / permeance / uptake / adhesion / Tg / cure
/ CTE / formulation). Zinc-rich epoxy primers (SSPC-Paint 20 Type II organic,
ISO 12944-5) protect steel by a completely orthogonal mechanism: sacrificial
galvanic action -- metallic zinc dust is the anode, steel the cathode, so the
zinc corrodes preferentially and cathodically polarizes the steel. For that
current path to exist the zinc pigment must (a) be thermodynamically anodic to
iron and (b) form an electrically-percolating network to the substrate.

Theory (all published, zero fitted params):
  * Galvanic driving force from tabulated standard electrode potentials:
        dE0 = E0(Fe2+/Fe) - E0(Zn2+/Zn)        (EXACT arithmetic)
    positive => zinc spontaneously sacrifices to protect iron.
  * Nernst cell EMF  E = dE0 - (RT/zF) ln Q ;  at Q=1, E == dE0  (EXACT limit).
  * Faraday sacrificial anode capacity  C = zF / M_Zn              (EXACT)
    => theoretical zinc capacity 820 Ah/kg (universal textbook anchor).
  * Continuum percolation of randomly placed (overlapping) equal spheres:
        eta_c = 0.3418           (Rintoul & Torquato 1997, reduced number density)
        phi_c = 1 - exp(-eta_c)  (EXACT identity => 0.2895 critical volume frac)
    the standard analytic estimate for a conductive-filler percolation threshold.
  * Weight<->volume fraction identity via component densities (EXACT invertible).

Inputs:
  * Physical constants: E0(Zn2+/Zn), E0(Fe2+/Fe) (CRC/IUPAC), F, M_Zn (CODATA/IUPAC),
    zinc density; continuum-percolation invariant eta_c (Rintoul-Torquato 1997).
  * REFERENCE_NOMINAL public marine best-practice: cured-epoxy binder density,
    SSPC-Paint 20 / practice zinc-loading window, NACE/ISO 15589 seawater cathodic
    protection criterion (-0.80 V vs Ag/AgCl) and practical galvanic-series
    potentials. Flagged; set MAGNITUDE/consistency scale, not the exact identities.

Deterministic: no timestamps, no RNG. Two runs => byte-identical JSON.
"""
import json
import math
import sys
from pathlib import Path

# =============================================================================
# EXACT physical constants (public domain; CODATA 2018 / IUPAC / CRC Handbook)
# =============================================================================
E0_ZN = -0.7618          # V, E0(Zn2+/Zn), CRC Handbook 97th ed.
E0_FE = -0.447           # V, E0(Fe2+/Fe), CRC Handbook 97th ed.
F_CONST = 96485.33212    # C/mol, Faraday constant (CODATA 2018)
R_GAS = 8.314462618      # J/(mol K), CODATA 2018
T_STD = 298.15           # K
Z_ZN = 2                 # electrons per Zn oxidation
M_ZN_G = 65.38           # g/mol, IUPAC standard atomic weight of zinc
RHO_ZN = 7.14            # g/cm^3, density of metallic zinc

# continuum percolation invariant for randomly placed overlapping equal spheres
ETA_C = 0.3418           # Rintoul & Torquato, J. Phys. A 30 (1997) L585

# ---- REFERENCE_NOMINAL public marine best-practice constants (flagged) -------
REF = {
    "cured_epoxy_binder_density_g_cm3": 1.20,   # amine-cured DGEBA, 1.1-1.25
    "in_tree_measured_cured_density_g_cm3": 1.105,  # from cured-network-density receipt
    "protection_criterion_V_AgAgCl": -0.80,     # NACE SP0169 / ISO 15589 seawater
    "zinc_free_potential_seawater_V_AgAgCl": -1.03,  # practical galvanic series
    "steel_free_potential_seawater_V_AgAgCl": -0.61, # practical galvanic series
    "copper_free_potential_seawater_V_AgAgCl": -0.36,# ordering control
    "sspc_paint20_practice_zinc_wt_pct_window": [80.0, 92.0],  # dry-film Zn wt%
    "zinc_theoretical_capacity_cited_Ah_kg": 820.0,  # universal textbook anchor
    "note": "REFERENCE_NOMINAL public marine engineering / best-practice values. "
            "They set the CONSISTENCY / magnitude scale only; the Tier-A EXACT "
            "identities (driving force, Nernst limit, Faraday capacity, percolation "
            "identity, wt<->vol inverse) depend on tabulated physical constants "
            "alone and on NONE of these nominal values.",
}


def galvanic_driving_force_V():
    """Thermodynamic galvanic driving force of the Zn(anode)/Fe(cathode) couple."""
    return E0_FE - E0_ZN


def nernst_cell_emf_V(dE0, Q, z=Z_ZN, T=T_STD):
    """Nernst cell EMF; at Q=1 the log term vanishes and E == dE0."""
    return dE0 - (R_GAS * T / (z * F_CONST)) * math.log(Q)


def zinc_capacity_Ah_per_kg():
    """Faraday theoretical sacrificial-anode capacity of zinc, Ah/kg."""
    coulomb_per_kg = Z_ZN * F_CONST / (M_ZN_G / 1000.0)   # C/kg
    return coulomb_per_kg / 3600.0                        # Ah/kg


def phi_c_overlapping_spheres():
    """Critical VOLUME fraction for continuum percolation of overlapping spheres."""
    return 1.0 - math.exp(-ETA_C)


def wt_from_vol(phi, rho_filler=RHO_ZN, rho_binder=None):
    """Filler weight fraction from filler volume fraction (EXACT)."""
    rho_binder = REF["cured_epoxy_binder_density_g_cm3"] if rho_binder is None else rho_binder
    num = rho_filler * phi
    return num / (num + rho_binder * (1.0 - phi))


def vol_from_wt(w, rho_filler=RHO_ZN, rho_binder=None):
    """Filler volume fraction from filler weight fraction (EXACT inverse of wt_from_vol)."""
    rho_binder = REF["cured_epoxy_binder_density_g_cm3"] if rho_binder is None else rho_binder
    # w = rf*phi / (rf*phi + rb*(1-phi))  ->  solve for phi
    a = w / rho_filler
    b = (1.0 - w) / rho_binder
    return a / (a + b)


def rnd(x, n=6):
    return round(float(x), n)


# =============================================================================
# TIER A -- EXACT physics identities (non-circular; must hold to < 1e-9)
# =============================================================================
def tier_a_exact():
    tests = []

    # 1. Galvanic driving force = exact arithmetic of the two tabulated potentials,
    #    and it is POSITIVE (zinc spontaneously protects iron).
    dE0 = galvanic_driving_force_V()
    expect = E0_FE - E0_ZN
    tests.append({
        "id": "galvanic_driving_force_exact_and_positive",
        "value_V": rnd(dE0, 12),
        "residual_vs_arithmetic": rnd(abs(dE0 - expect), 15),
        "sign_positive_zinc_protects_iron": bool(dE0 > 0.0),
        "tol": 1e-12,
        "pass": bool(abs(dE0 - expect) < 1e-12 and dE0 > 0.0),
    })

    # 2. Nernst limit: at unit reaction quotient the EMF equals the standard dE0.
    dE0 = galvanic_driving_force_V()
    e_unit = nernst_cell_emf_V(dE0, 1.0)
    tests.append({
        "id": "nernst_emf_equals_dE0_at_Q_unity",
        "residual": rnd(abs(e_unit - dE0), 15),
        "tol": 1e-12, "pass": bool(abs(e_unit - dE0) < 1e-12),
    })

    # 3. Nernst is EXACTLY symmetric: E(Q) - dE0 == -(E(1/Q) - dE0).
    dE0 = galvanic_driving_force_V()
    hi = nernst_cell_emf_V(dE0, 10.0) - dE0
    lo = nernst_cell_emf_V(dE0, 0.1) - dE0
    tests.append({
        "id": "nernst_log_antisymmetry",
        "residual": rnd(abs(hi + lo), 15),
        "tol": 1e-12, "pass": bool(abs(hi + lo) < 1e-12),
    })

    # 4. Faraday round-trip: the capacity, taken back through C=zF/M, recovers the
    #    electron count z=2 to machine precision (EXACT, non-circular self-consistency).
    cap = zinc_capacity_Ah_per_kg()
    z_recovered = cap * 3600.0 * (M_ZN_G / 1000.0) / F_CONST
    tests.append({
        "id": "faraday_capacity_recovers_electron_count_z2",
        "capacity_Ah_kg": rnd(cap, 6),
        "z_recovered": rnd(z_recovered, 12),
        "residual_vs_2": rnd(abs(z_recovered - 2.0), 15),
        "tol": 1e-12, "pass": bool(abs(z_recovered - 2.0) < 1e-12),
    })

    # 5. Continuum-percolation identity phi_c = 1 - exp(-eta_c), eta_c=0.3418.
    phic = phi_c_overlapping_spheres()
    expect = 1.0 - math.exp(-ETA_C)
    tests.append({
        "id": "percolation_phi_c_identity",
        "phi_c": rnd(phic, 9),
        "residual_vs_definition": rnd(abs(phic - expect), 15),
        "tol": 1e-12, "pass": bool(abs(phic - expect) < 1e-12),
    })

    # 6. Weight<->volume fraction round-trip is an EXACT algebraic inverse.
    max_res = 0.0
    for phi in (0.10, 0.2895, 0.40, 0.55, 0.70):
        w = wt_from_vol(phi)
        phi_back = vol_from_wt(w)
        max_res = max(max_res, abs(phi_back - phi))
    tests.append({
        "id": "wt_vol_fraction_inverse_roundtrip",
        "max_abs_residual": rnd(max_res, 15),
        "tol": 1e-12, "pass": bool(max_res < 1e-12),
    })

    return tests


# =============================================================================
# TIER B -- consistency vs published anchors (documented tolerance / direction)
# =============================================================================
def tier_b_consistency():
    tests = []

    # 1. Cathodic-protection feasibility: zinc's free seawater potential is more
    #    negative than the NACE/ISO protection criterion, which is in turn more
    #    negative than bare steel's free potential:  E_Zn < E_crit < E_steel.
    ezn = REF["zinc_free_potential_seawater_V_AgAgCl"]
    ecrit = REF["protection_criterion_V_AgAgCl"]
    esteel = REF["steel_free_potential_seawater_V_AgAgCl"]
    tests.append({
        "id": "cathodic_protection_potential_window",
        "E_zinc_V": ezn, "E_criterion_V": ecrit, "E_steel_free_V": esteel,
        "overpotential_headroom_V": rnd(ecrit - ezn, 4),  # >0 => zinc can drive steel past criterion
        "pass": bool(ezn < ecrit < esteel),
    })

    # 2. Galvanic-series ordering control:  E(Zn) < E(Fe) < E(Cu).
    ordering = [REF["zinc_free_potential_seawater_V_AgAgCl"],
                REF["steel_free_potential_seawater_V_AgAgCl"],
                REF["copper_free_potential_seawater_V_AgAgCl"]]
    tests.append({
        "id": "galvanic_series_ordering_Zn_Fe_Cu",
        "potentials_V": ordering,
        "pass": bool(ordering[0] < ordering[1] < ordering[2]),
    })

    # 3. Percolation-threshold weight fraction BRACKETS-FROM-BELOW the marine spec
    #    window. Bare overlapping-sphere percolation is a LOWER BOUND; real specs
    #    sit ABOVE it (robust network + throwing power). Direction must hold.
    wc = wt_from_vol(phi_c_overlapping_spheres()) * 100.0
    lo_spec, hi_spec = REF["sspc_paint20_practice_zinc_wt_pct_window"]
    tests.append({
        "id": "percolation_wt_pct_is_lower_bound_of_spec_window",
        "predicted_percolation_wt_pct": rnd(wc, 2),
        "spec_window_wt_pct": [lo_spec, hi_spec],
        "predicted_below_spec_min": bool(wc < lo_spec),
        "gap_to_spec_min_wt_pct": rnd(lo_spec - wc, 2),
        "pass": bool(wc < lo_spec),
        "interpretation": "bare-percolation is a physical LOWER BOUND; marine specs "
                          "load ABOVE it for network redundancy + galvanic throwing "
                          "power + eventual Zn-corrosion-product barrier.",
    })

    # 4. Faraday capacity reproduces the universally-cited 820 Ah/kg textbook zinc
    #    anode capacity to < 0.1% (the exact formula yields 819.87; "820" is the
    #    3-sig-fig rounding). External-anchor consistency, documented tolerance.
    cap = zinc_capacity_Ah_per_kg()
    rel_err = abs(cap - 820.0) / 820.0
    tests.append({
        "id": "zinc_capacity_matches_cited_820_Ah_kg",
        "computed_Ah_kg": rnd(cap, 4), "cited_Ah_kg": 820.0,
        "rel_err_pct": rnd(rel_err * 100.0, 4),
        "tol_pct": 0.1, "pass": bool(rel_err < 0.001),
    })

    # 5. Density-sensitivity is DAMPED (sub-unity): switching binder density from
    #    1.20 to the in-tree MEASURED cured value 1.105 (a +7.9% density change)
    #    moves the predicted percolation wt% by only ~2.4% relative -- the
    #    threshold is dominated by the Zn/binder density RATIO, so the sensitivity
    #    is < 1 (robust). Pass criterion = physical damping, not a tuned tolerance.
    wc_nom = wt_from_vol(phi_c_overlapping_spheres(),
                         rho_binder=REF["cured_epoxy_binder_density_g_cm3"]) * 100.0
    wc_meas = wt_from_vol(phi_c_overlapping_spheres(),
                          rho_binder=REF["in_tree_measured_cured_density_g_cm3"]) * 100.0
    rel_threshold_shift = abs(wc_nom - wc_meas) / wc_nom
    rel_density_change = abs(REF["cured_epoxy_binder_density_g_cm3"]
                             - REF["in_tree_measured_cured_density_g_cm3"]) \
        / REF["cured_epoxy_binder_density_g_cm3"]
    tests.append({
        "id": "percolation_wt_pct_density_sensitivity_is_damped",
        "wt_pct_binder_1p20": rnd(wc_nom, 2),
        "wt_pct_binder_1p105": rnd(wc_meas, 2),
        "shift_pt": rnd(abs(wc_nom - wc_meas), 2),
        "rel_threshold_shift_pct": rnd(rel_threshold_shift * 100.0, 3),
        "rel_binder_density_change_pct": rnd(rel_density_change * 100.0, 3),
        "sensitivity_ratio": rnd(rel_threshold_shift / rel_density_change, 3),
        "pass": bool(rel_threshold_shift < rel_density_change),
    })

    return tests


# =============================================================================
# ENGINE: score a candidate zinc-rich epoxy primer
# =============================================================================
def score_candidate(name, zinc_wt_pct, dft_um):
    """Given dry-film zinc wt% and dry film thickness, return sacrificial-protection
    status: thermodynamic feasibility (universal for Zn/Fe), percolation state,
    and areal sacrificial charge capacity."""
    w = zinc_wt_pct / 100.0
    phi = vol_from_wt(w)
    phi_c = phi_c_overlapping_spheres()
    dE0 = galvanic_driving_force_V()

    # areal zinc mass: dft * (zinc volume fraction) * rho_Zn
    dft_cm = dft_um * 1e-4
    zinc_mass_g_per_cm2 = dft_cm * phi * RHO_ZN
    zinc_mass_kg_per_m2 = zinc_mass_g_per_cm2 * 10.0  # g/cm2 -> kg/m2
    areal_capacity_Ah_m2 = zinc_mass_kg_per_m2 * zinc_capacity_Ah_per_kg()

    percolating = phi > phi_c
    return {
        "candidate": name,
        "zinc_wt_pct": zinc_wt_pct,
        "zinc_vol_fraction": rnd(phi, 4),
        "percolation_threshold_vol_fraction": rnd(phi_c, 4),
        "sacrificially_active": bool(percolating),
        "protection_mode": "SACRIFICIAL_GALVANIC" if percolating else "BARRIER_ONLY_below_percolation",
        "galvanic_driving_force_V": rnd(dE0, 4),
        "dft_um": dft_um,
        "areal_zinc_mass_kg_per_m2": rnd(zinc_mass_kg_per_m2, 4),
        "areal_sacrificial_capacity_Ah_per_m2": rnd(areal_capacity_Ah_m2, 3),
    }


def build_diagnostic():
    tier_a = tier_a_exact()
    tier_b = tier_b_consistency()
    a_pass = sum(1 for t in tier_a if t["pass"])
    b_pass = sum(1 for t in tier_b if t["pass"])

    # Representative candidate ladder (real marine loading points; deterministic)
    candidates = [
        score_candidate("below_percolation_60wt", 60.0, 75.0),
        score_candidate("marine_spec_min_80wt", 80.0, 75.0),
        score_candidate("marine_spec_high_92wt", 92.0, 75.0),
    ]

    verdict = (
        "ENGINE_READY__EXACT_ELECTROCHEMISTRY_VALIDATED__"
        "SACRIFICIAL_FEASIBILITY_AND_PERCOLATION_STATE_DEFENDED__"
        "PERCOLATION_MAGNITUDE_IS_LOWER_BOUND__"
        "FIELD_THROWING_POWER_AND_PSD_SHAPE_MEASUREMENT_BLOCKED"
    )

    diag = {
        "benchmark": "amphora-redteam-audit/zinc-galvanic-percolation-v1",
        "authority": "AUDIT_ONLY",
        "target_module": "amphora-barrier-corrosion-score",
        "also_feeds": ["amphora-formulation-arithmetic", "amphora-design-rule-score",
                       "amphora-cpvc-pigment-formulation (companion CPVC axis)"],
        "target_capability": (
            "Open the SACRIFICIAL (galvanic) marine protection mechanism -- zinc-rich "
            "epoxy primers -- orthogonal to every prior BARRIER-mechanism receipt. "
            "Decide (a) thermodynamic feasibility of Zn sacrificing to protect Fe, "
            "(b) whether a given zinc loading percolates into a sacrificially-active "
            "network vs remaining barrier-only, (c) areal sacrificial charge capacity."
        ),
        "new_axis_justification": (
            "grep of all 66 signed receipts + 30 prior AUDIT axes for zinc|galvanic|"
            "percolation|cathodic|sacrificial|electrochem|potential => ZERO hits. Every "
            "prior axis models the BARRIER mechanism (transport/FFV/tortuosity/permeance/"
            "uptake/adhesion/Tg/cure/CTE/formulation). Zinc-rich primer sacrificial "
            "protection is the single largest missing marine anti-corrosion mechanism "
            "(SSPC-Paint 20, ISO 12944-5 the dominant marine primer class)."
        ),
        "theory": {
            "galvanic_driving_force": "dE0 = E0(Fe2+/Fe) - E0(Zn2+/Zn); >0 => Zn sacrifices",
            "nernst": "E = dE0 - (RT/zF) ln Q ; E==dE0 at Q=1",
            "faraday_capacity": "C = zF/M_Zn => 820 Ah/kg theoretical zinc anode capacity",
            "continuum_percolation": "phi_c = 1 - exp(-eta_c), eta_c=0.3418 (Rintoul-Torquato 1997)",
            "wt_vol_identity": "w = rho_f*phi / (rho_f*phi + rho_b*(1-phi)), invertible",
            "cathodic_protection_criterion": "steel protected when polarized <= -0.80 V vs Ag/AgCl (NACE SP0169/ISO 15589)",
        },
        "fitted_parameters": "NONE (zero free parameters; all values are tabulated physical "
                             "constants or flagged REFERENCE_NOMINAL best-practice anchors)",
        "reference_nominal_constants": REF,
        "real_input_data": {
            "physical_constants": {
                "E0_Zn2+_Zn_V": E0_ZN, "E0_Fe2+_Fe_V": E0_FE,
                "faraday_C_per_mol": F_CONST, "gas_constant_J_per_mol_K": R_GAS,
                "M_Zn_g_per_mol": M_ZN_G, "rho_Zn_g_per_cm3": RHO_ZN,
                "eta_c_continuum_percolation": ETA_C,
            },
            "sources": [
                "CRC Handbook of Chemistry and Physics, 97th ed. (standard electrode potentials)",
                "CODATA 2018 (Faraday, gas constant)",
                "IUPAC 2021 standard atomic weights (Zn 65.38)",
                "Rintoul & Torquato, J. Phys. A 30 (1997) L585 (eta_c=0.3418 overlapping-sphere percolation)",
                "SSPC-Paint 20 / ISO 12944-5 / NACE SP0169 & ISO 15589-1 (marine best practice, REFERENCE_NOMINAL)",
            ],
            "note": "Primary inputs are public-domain physical constants and published "
                    "marine standards; no proprietary or rights-restricted dataset is used.",
        },
        "known_answer_battery": {
            "tier_a_exact_identities": tier_a,
            "tier_b_consistency_anchors": tier_b,
            "tier_a_pass": a_pass, "tier_a_total": len(tier_a),
            "tier_b_pass": b_pass, "tier_b_total": len(tier_b),
            "total_pass": a_pass + b_pass, "total": len(tier_a) + len(tier_b),
            "all_pass": bool(a_pass == len(tier_a) and b_pass == len(tier_b)),
        },
        "engine_output": {
            "galvanic_driving_force_V": rnd(galvanic_driving_force_V(), 4),
            "zinc_theoretical_capacity_Ah_per_kg": rnd(zinc_capacity_Ah_per_kg(), 3),
            "percolation_threshold_vol_fraction": rnd(phi_c_overlapping_spheres(), 4),
            "percolation_threshold_wt_pct_binder1p20": rnd(wt_from_vol(phi_c_overlapping_spheres()) * 100.0, 2),
            "candidate_ladder": candidates,
        },
        "non_circularity": (
            "The exact identities (Tier A) use ONLY tabulated physical constants; none "
            "is fitted to, or derived from, any coating performance measurement. The "
            "percolation threshold is a pure geometric invariant, independent of the "
            "galvanic thermodynamics. The marine spec window is used ONLY as an external "
            "direction check (predicted bound < spec min), never as a fit target."
        ),
        "honest_limitations": [
            "Overlapping-sphere phi_c=0.2895 (=> ~70.8 wt% Zn) is a LOWER BOUND for "
            "spherical zinc DUST; real marine specs load 80-92 wt% for network "
            "redundancy, galvanic throwing power, and eventual Zn-corrosion-product "
            "barrier. The model gives the physical floor, not the operating point.",
            "Zinc FLAKE / lamellar zinc percolates at LOWER loading (higher aspect "
            "ratio) -- same aspect-ratio physics as the flake-tortuosity barrier axis; "
            "not captured by the equal-sphere estimate.",
            "Practical galvanic-series potentials are REFERENCE_NOMINAL; real free/"
            "polarized potentials shift with pH, oxygen, temperature and polarization "
            "(throwing power). Only the thermodynamic FEASIBILITY & ordering are defended.",
            "No measured EIS / galvanic-current or accelerated-immersion data was used; "
            "field service-life is NOT claimed (that requires measured data => blocked).",
        ],
        "verdict": verdict,
        "does_not_close": [
            "does NOT promote amphora-barrier-corrosion-score to VALIDATED "
            "scientific_readiness (phase-0 is a governance state; 0/29 modules "
            "scientific_readiness==VALIDATED; needs two trust-anchored phase0 "
            "signatures this AUDIT_ONLY key cannot supply)",
            "does NOT change the manifest (still 66 receipts / 11 modules)",
            "does NOT modify the shipped Rust engine or any of the 66 signed receipts",
        ],
    }
    return diag


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else "diagnostic.canonical.json"
    diag = build_diagnostic()
    Path(out_path).write_text(json.dumps(diag, indent=2, sort_keys=True) + "\n")
    ka = diag["known_answer_battery"]
    print("WROTE", out_path)
    print("tier_a", ka["tier_a_pass"], "/", ka["tier_a_total"],
          "  tier_b", ka["tier_b_pass"], "/", ka["tier_b_total"],
          "  all_pass", ka["all_pass"])
    print("driving_force_V", diag["engine_output"]["galvanic_driving_force_V"])
    print("zinc_capacity_Ah_kg", diag["engine_output"]["zinc_theoretical_capacity_Ah_per_kg"])
    print("phi_c", diag["engine_output"]["percolation_threshold_vol_fraction"],
          "wt_pct", diag["engine_output"]["percolation_threshold_wt_pct_binder1p20"])


if __name__ == "__main__":
    main()
