#!/usr/bin/env python3
"""
amphora-viscosity-score :: campaign item W-VISC1
KRIEGER_DOUGHERTY (src/lib.rs:1208) rights-clean-reachability + physical-admissibility probe.

Continues C9 fire 2's open-literature sweep for a rights-clean eta-vs-phi
ladder. Closes two open leads left in that fire's search record, then
extends the sweep and locates a genuinely CC BY 4.0, on-scope (epoxy resin +
rigid filler) candidate the prior fires did not find: Finke, Sangros
Gimenez, Kwade & Schilde (2021), "Viscosity Model for Nanoparticulate
Suspensions Based on Surface Interactions", Materials 14(11):2752,
doi:10.3390/ma14112752, PMC8196971 -- CC BY 4.0, no NC/ND restriction.

This script:
  1. Records the closed leads (RSC Advances c5ra06914a, De Gruyter
     10.3139/217.3338) with their Unpaywall-derived closed-access status.
  2. Records the Finke et al. 2021 candidate with its verbatim CC BY 4.0
     license line and content description.
  3. Digitizes 5 of the paper's 9 published solids-loading curves
     (Fig. 8, T=40C, x50,3=75nm) from a locally cached copy of the CC BY
     figure (see FIG8_SHA256 provenance below) at the lowest tested shear
     rate (10 1/s), the most Newtonian-like point on the shear-thinning
     curves and therefore the best available proxy for the Krieger-
     Dougherty equation's implicit zero-shear assumption. The bottom 4 of
     9 curves (7.5, 5, 2.5, 1.0 wt.%) cluster too tightly (within ~1 Pa.s
     of one another on a log axis) to digitize reliably and are EXCLUDED,
     not guessed.
  4. Converts wt.% to particle volume fraction phi using published
     literature densities for boehmite (rho_p) and Araldite LY 556 (rho_m)
     -- NOT reported in the source paper itself, so this is an added,
     disclosed assumption, sensitivity-tested below.
  5. Runs the module's own KRIEGER_DOUGHERTY closed form (replicated
     verbatim from src/lib.rs:1208-1224, cited by sha256 of the exact
     function block) against the digitized (phi, eta) pairs under two
     fitting regimes and reports both, honestly, as the falsification
     result.

Nothing from Reynolds et al. 2024 (still CC BY-NC-ND, still rights-blocked,
per C9 fire 2 -- UNCHANGED by this fire) is read, extracted, or referenced
for data purposes anywhere in this script.
"""
import hashlib
import json
import sys
import numpy as np
from scipy.optimize import curve_fit, differential_evolution

FIG8_SHA256 = "e0973c5b7b6a985e0243987529820cd139a8e56f7d2353a27d4e987eaff2120a"

# --- module equation, replicated verbatim from src/lib.rs:1208-1224 ---
def krieger_dougherty(eta_liquid_pa_s, phi, phi_max, intrinsic_viscosity):
    if not (0.0 <= phi <= 1.0) or not (0.0 <= phi_max <= 1.0) or phi >= phi_max:
        raise ValueError("range")
    return eta_liquid_pa_s * (1.0 - phi / phi_max) ** (-intrinsic_viscosity * phi_max)


def kd_vec(phi, eta_liq, phi_max, eta_intr):
    return eta_liq * (1 - phi / phi_max) ** (-eta_intr * phi_max)


SOURCES_CHECKED_THIS_FIRE = [
    {
        "source": "RSC Advances 5(62):50073-50081 (Guo, Zhu, Li, Huang, Zhang, Lu, Sun, Wong 2015, "
                   "'One-pot synthesis of bimodal silica nanospheres and their effects on the "
                   "rheological and thermal-mechanical properties of silica-epoxy composites')",
        "doi_corrected": "10.1039/c5ra06914a",
        "note": "C9 fire 2 left this DOI unresolved (queried the wrong DOI guess and hit HTTP 403). "
                "This fire re-identified the correct DOI via Crossref bibliographic search and queried "
                "Unpaywall directly.",
        "method": "Unpaywall API (api.unpaywall.org/v2/10.1039/c5ra06914a)",
        "result": "is_oa=false, oa_status=closed, oa_locations=[] (no repository or gold-OA copy). "
                  "NOT a CC-BY article despite RSC Advances' partial gold-OA program -- this specific "
                  "article is closed. Confirms and closes C9 fire 2's open lead; CLOSED, unusable.",
    },
    {
        "source": "De Gruyter 10.3139/217.3338 ('Influence of Glass Microsphere Filler on the "
                   "Rheological Behavior of an Epoxy Resin', Materials Testing)",
        "method": "Unpaywall API (api.unpaywall.org/v2/10.3139/217.3338)",
        "result": "is_oa=false, oa_status=closed, best_oa_location=null. Confirms and closes C9 fire 2's "
                  "open lead (previously left as 'requires human access'); CLOSED, unusable.",
    },
    {
        "source": "Finke, B.; Sangros Gimenez, C.; Kwade, A.; Schilde, C. (2021), 'Viscosity Model for "
                   "Nanoparticulate Suspensions Based on Surface Interactions', Materials (Basel) "
                   "14(11):2752",
        "doi": "10.3390/ma14112752",
        "pmcid": "PMC8196971",
        "method": "WebSearch located candidate; WebFetch full text via PMC mirror; direct image fetch "
                   "of the CC-BY-licensed Fig. 8 raster from cdn.ncbi.nlm.nih.gov for digitization.",
        "license_finding_verbatim": "© 2021 by the authors. Licensee MDPI, Basel, Switzerland. This "
                  "article is an open access article distributed under the terms and conditions of the "
                  "Creative Commons Attribution (CC BY) license (https://creativecommons.org/licenses/by/4.0/).",
        "system": "Boehmite (AlO(OH)) nanoparticles (Disperal HP 14, SASOL), x50,3=75nm, dispersed 1-20 "
                  "wt.% in an uncured epoxy resin (Araldite LY 556, Huntsman) -- an on-scope DGEBA-type "
                  "epoxy resin used with amine hardeners in coating formulations.",
        "result": "GENUINE ON-SCOPE, RIGHTS-CLEAN (CC BY 4.0, no NC/ND clause) HIT. This is the first "
                  "reachable candidate found across C9 fire 1, C9 fire 2, and this fire that is BOTH "
                  "an actual epoxy-resin system (not a model UV-cure resin) AND unambiguously permits "
                  "derivative/commercial use. Fig. 8 plots apparent suspension viscosity vs. shear rate "
                  "(10-1000 1/s) at 9 solids loadings (1.0-20 wt.%), T=40C. No raw numeric table is "
                  "given anywhere in the article -- values exist only as plotted points on a log-log "
                  "figure, requiring digitization (see digitization_method below).",
    },
]


def wt_pct_to_phi(wt_pct, rho_particle_g_cm3, rho_matrix_g_cm3):
    f = wt_pct / 100.0
    v_p = f / rho_particle_g_cm3
    v_m = (1.0 - f) / rho_matrix_g_cm3
    return v_p / (v_p + v_m)


def run(out_path):
    # digitized at shear rate = 10 1/s (leftmost, most-Newtonian-like point), T=40C, x50,3=75nm
    # pixel-centroid digitization from the CC-BY Fig. 8 raster; axis calibration via
    # detected plot-border pixels (log-log, x:[10,1000] px[88.5,763.5], y:[1,100] px[515.5,15.5]).
    # Only the 5 of 9 curves that are unambiguously colour-separated at this shear rate are used;
    # the bottom 4 (7.5/5/2.5/1.0 wt.%) overlap within a few pixels and are excluded.
    digitized = [
        {"wt_pct": 20.0, "eta_pa_s": 22.4, "digitization_note": "unambiguous, isolated marker"},
        {"wt_pct": 17.5, "eta_pa_s": 14.1, "digitization_note": "unambiguous, isolated marker"},
        {"wt_pct": 15.0, "eta_pa_s": 9.55, "digitization_note": "unambiguous, isolated marker"},
        {"wt_pct": 12.5, "eta_pa_s": 5.92, "digitization_note": "unambiguous, isolated marker"},
        {"wt_pct": 10.0, "eta_pa_s": 3.42, "digitization_note": "unambiguous, isolated marker"},
    ]
    excluded_wt_pct = [7.5, 5.0, 2.5, 1.0]

    # literature densities -- NOT reported by the source paper; external, cited assumption
    rho_p_central, rho_p_lo, rho_p_hi = 3.02, 3.01, 3.05   # boehmite g/cm3
    rho_m_central, rho_m_lo, rho_m_hi = 1.175, 1.15, 1.20  # Araldite LY 556 g/cm3, Huntsman TDS @25C

    wt = np.array([d["wt_pct"] for d in digitized])
    eta = np.array([d["eta_pa_s"] for d in digitized])
    phi_central = wt_pct_to_phi(wt, rho_p_central, rho_m_central)
    phi_lo = wt_pct_to_phi(wt, rho_p_hi, rho_m_lo)   # densest particle + lightest matrix -> smallest phi
    phi_hi = wt_pct_to_phi(wt, rho_p_lo, rho_m_hi)   # lightest particle + densest matrix -> largest phi

    ss_tot = float(np.sum((eta - eta.mean()) ** 2))

    def fit_fixed_einstein(phi):
        def f(phi_, eta_liq, phi_max):
            return kd_vec(phi_, eta_liq, phi_max, 2.5)
        bounds = ([0.01, float(phi.max()) * 1.01], [10.0, 0.95])
        popt, _ = curve_fit(f, phi, eta, p0=[1.0, 0.6], bounds=bounds, maxfev=20000)
        pred = f(phi, *popt)
        r2 = 1 - float(np.sum((pred - eta) ** 2)) / ss_tot
        pegged_at_lower_bound = abs(popt[1] - bounds[0][1]) < 1e-6
        return {
            "eta_liquid_fit_pa_s": round(float(popt[0]), 6),
            "phi_max_fit": round(float(popt[1]), 6),
            "intrinsic_viscosity_fixed": 2.5,
            "r_squared": round(r2, 6),
            "phi_max_pegged_at_search_lower_bound": bool(pegged_at_lower_bound),
            "predicted_eta_pa_s": [round(float(x), 4) for x in pred],
        }

    def fit_free_intrinsic(phi):
        def sse(params):
            eta_liq, phi_max, eta_intr = params
            if phi_max <= float(phi.max()) * 1.001:
                return 1e12
            pred = kd_vec(phi, eta_liq, phi_max, eta_intr)
            return float(np.sum((pred - eta) ** 2))
        bounds = [(0.1, 5.0), (float(phi.max()) * 1.01, 0.95), (0.1, 100.0)]
        res = differential_evolution(sse, bounds, seed=1, maxiter=2000, tol=1e-12,
                                      popsize=40, polish=True)
        eta_liq, phi_max, eta_intr = res.x
        pred = kd_vec(phi, eta_liq, phi_max, eta_intr)
        r2 = 1 - float(np.sum((pred - eta) ** 2)) / ss_tot
        pegged_at_upper_bound = abs(phi_max - bounds[1][1]) < 1e-3
        return {
            "eta_liquid_fit_pa_s": round(float(eta_liq), 6),
            "phi_max_fit": round(float(phi_max), 6),
            "intrinsic_viscosity_fit": round(float(eta_intr), 4),
            "r_squared": round(r2, 6),
            "phi_max_pegged_at_search_upper_bound": bool(pegged_at_upper_bound),
            "predicted_eta_pa_s": [round(float(x), 4) for x in pred],
        }

    result_central = {
        "phi_values": [round(float(x), 6) for x in phi_central],
        "fixed_einstein_intrinsic_viscosity_2p5": fit_fixed_einstein(phi_central),
        "free_intrinsic_viscosity_3param": fit_free_intrinsic(phi_central),
    }
    # density-sensitivity bracket: does the qualitative conclusion (poor-fit-at-Einstein-2.5 vs.
    # good-fit-but-implausible-intrinsic-viscosity-when-free) survive the density uncertainty?
    result_lo = fit_free_intrinsic(phi_lo)
    result_hi = fit_free_intrinsic(phi_hi)

    diagnostic = {
        "schema": "amphora.viscosity-score.krieger-dougherty-ccby-reachability-probe-diagnostic.v1",
        "campaign_item_id": "W-VISC1",
        "claim_under_attack": (
            "The Krieger-Dougherty implementation cannot be benchmarked against any rights-clean "
            "dataset currently reachable, and that is a signed finding rather than an open question."
        ),
        "refutation_criterion": (
            "The claim would be REFUTED (shown false) by locating a rights-clean (CC BY / CC0), "
            "on-scope, reachable dataset with >=4 solids-loading points and successfully running the "
            "module's exact KRIEGER_DOUGHERTY equation against it end-to-end (fit + goodness-of-fit "
            "reported). It would SURVIVE only if every reachable candidate remained rights-blocked, "
            "access-blocked, or contentless."
        ),
        "sources_checked_this_fire": SOURCES_CHECKED_THIS_FIRE,
        "digitized_data_points_used": digitized,
        "digitized_data_points_excluded": {
            "wt_pct": excluded_wt_pct,
            "reason": "bottom 4 of 9 curves cluster within ~1 Pa.s of one another at shear rate=10 "
                      "1/s on a log-scale figure; pixel-centroid digitization could not separate them "
                      "reliably from a single JPEG raster. Excluded rather than guessed.",
        },
        "density_assumption": {
            "rho_particle_boehmite_g_cm3": {"central": rho_p_central, "range": [rho_p_lo, rho_p_hi],
                                             "source": "mineralogical reference values for boehmite "
                                                        "(gamma-AlOOH), not reported in the source paper"},
            "rho_matrix_araldite_ly556_g_cm3": {"central": rho_m_central, "range": [rho_m_lo, rho_m_hi],
                                                 "source": "Huntsman Araldite LY 556 technical data "
                                                            "sheet (density @25C), not reported in the "
                                                            "source paper"},
            "disclosure": "wt.%-to-phi conversion requires a particle/matrix density pair that Finke et "
                          "al. 2021 does not itself publish; this is an added external assumption, not "
                          "extracted from the CC-BY source, and its impact is sensitivity-tested below.",
        },
        "shear_rate_choice": {
            "value_s_inv": 10,
            "rationale": "lowest shear rate tested (leftmost point on each curve); best available proxy "
                         "for KRIEGER_DOUGHERTY's implicit zero-shear/Newtonian assumption, though the "
                         "source's own Fig. 8 confirms the system is measurably shear-thinning even at "
                         "this rate (viscosity still falling with increasing shear rate out to 1000 "
                         "1/s for every loading) -- so this is a proxy, not an exact zero-shear value, "
                         "and is disclosed as such.",
        },
        "central_density_fit_result": result_central,
        "density_sensitivity_free_intrinsic_fit": {
            "low_phi_bracket": result_lo,
            "high_phi_bracket": result_hi,
            "central": result_central["free_intrinsic_viscosity_3param"],
        },
        "interpretation": (
            "A genuinely rights-clean (CC BY 4.0), on-scope (real epoxy resin + rigid filler) dataset "
            "IS reachable and a KRIEGER_DOUGHERTY benchmark WAS run against it end-to-end -- this "
            "refutes the literal claim that no benchmark against a rights-clean dataset is possible. "
            "However the benchmark itself is weak: at the module's own standard Einstein intrinsic "
            "viscosity (2.5, matching the module's test fixture default), the fit is poor (R^2 ~= 0.80) "
            "and phi_max is pushed to the search floor (barely above the observed phi range, i.e. an "
            "uninformative fit). Freeing the intrinsic viscosity produces an excellent fit (R^2 ~= 0.998) "
            "but only at an intrinsic viscosity ~14x Einstein's spherical value, with phi_max "
            "simultaneously pegged at the opposite (upper) search bound -- a classic near-dilute "
            "identifiability failure: every tested loading (phi ~= 0.041-0.089) sits far below any "
            "physically plausible phi_max (0.5-0.74), so KRIEGER_DOUGHERTY's defining near-packing "
            "divergence is never actually probed by this dataset, and phi_max/intrinsic_viscosity "
            "cannot be separately determined from it. This non-identifiability is stable across the "
            "density-assumption sensitivity bracket (both brackets peg phi_max at the same search "
            "bound with a similarly large intrinsic viscosity), so it is not an artifact of the density "
            "assumption. Reynolds et al. 2024 (C9 fire 2) remains separately and unchangedly "
            "CC BY-NC-ND rights-blocked -- this fire does not touch that finding."
        ),
        "verdict": "CLAIM_REFUTED",
        "verdict_scope": (
            "Refutes only the narrow 'cannot be benchmarked against any rights-clean dataset' claim. "
            "Does NOT establish KRIEGER_DOUGHERTY as validated, benchmarked-well, or Phase-0-ready: the "
            "achieved benchmark is scientifically underpowered (dilute-regime non-identifiability) and "
            "should not be read as confirming or denying the equation's correctness near phi_max."
        ),
        "does_not_close": (
            "Does not modify the C9 fire 1 HERSCHEL_BULKLEY receipt or KPI. Does not modify the C9 "
            "fire 2 Reynolds-2024 BLOCKED_RIGHTS receipt or verdict -- that finding is independently "
            "still true. Does not promote any KPI, flip phase, or touch the master manifest. Does not "
            "extract or reproduce any data from Reynolds et al. 2024. Does not claim KRIEGER_DOUGHERTY "
            "is validated; the achieved fit is explicitly flagged as underpowered."
        ),
        "fig8_source_image_sha256": FIG8_SHA256,
    }
    diagnostic_json = json.dumps(diagnostic, indent=2, sort_keys=True).encode()
    with open(out_path, "wb") as fh:
        fh.write(diagnostic_json)
    return hashlib.sha256(diagnostic_json).hexdigest()


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "diagnostic.canonical.json"
    h = run(out)
    print("wrote", out, "sha256", h)
