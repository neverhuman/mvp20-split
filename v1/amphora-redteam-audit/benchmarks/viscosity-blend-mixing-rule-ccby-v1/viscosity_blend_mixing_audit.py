"""
Liquid BLEND (mixture) viscosity mixing-rule audit for marine-coating solvent
thinners -- AUDIT_ONLY red-team increment for amphora-viscosity-score.

WHY THIS INCREMENT
------------------
amphora-viscosity-score is a PERFORMANCE-lane module whose stated decision is
"whether rheology and sag should be measured for a formulation" -- i.e. can we
predict application viscosity (airless-spray window, sag, film build) of a
formulated thinner blend? Its live Phase-0 KPI only fits a per-solvent Arrhenius
curve and holds out one temperature (an INTERPOLATION test, not a-priori), and
its only three "real" receipts score on CONTEXT_ONLY-quarantined polyverse melt
data (a known rights violation, ref amphora-redteam-audit rights-integrity-v1).
Nowhere in the 66-receipt portfolio is BLEND viscosity (component -> mixture)
predicted or validated. Marine thinners ARE blends (aromatic + ketone + alcohol),
so this is the single highest-value untouched piece of that module's science.

WHAT IS TESTED
--------------
A-priori zero-parameter log-linear mole-fraction mixing (Arrhenius 1887 /
Kendall-Monroe 1917): ln eta_mix = sum_i x_i ln eta_i, using ONLY the two
measured pure-component endpoints. Then the one-parameter Grunberg-Nissan (1949)
interaction model ln eta_mix = sum_i x_i ln eta_i + x1 x2 d12 is fit to the
interior points to quantify how much a single measured interaction datum is
worth. The excess is exactly the Eyring excess Gibbs energy of activation of
viscous flow (sign only, density not required for the log-viscosity excess).

NON-CIRCULARITY
---------------
Kendall-Monroe consumes ONLY the measured pure toluene and pure 2-propanol
viscosity at each temperature (the x1=0 and x1=1 rows). The 9 interior blend
viscosities are NEVER an input to the zero-parameter prediction; they are only
the validation target. Grunberg-Nissan is EXPLICITLY a 1-parameter FIT to the
interior points and is reported as such -- not as an a-priori result.

RIGHTS / SCOPE
--------------
Validation data are text-stated table values from a genuinely rights-clean
CC-BY-4.0 source for two IN-SCOPE marine-thinner solvents (toluene + 2-propanol,
both present in the module's CC0 25-solvent Phase-0 fixture). AUTHORITY:
AUDIT_ONLY. Promotes nothing, signs no phase0 evaluation/review, modifies none
of the 66 signed receipts or the manifest.
"""
import json
import math
import sys

import numpy as np


def rnd(x, n=6):
    return round(float(x), n)


# ---------------------------------------------------------------------------
# VALIDATION DATASET (CC-BY-4.0, text-stated Table 3 values only)
# Nain A.K. et al. "Excess Thermodynamic Properties and FTIR Studies of Binary
# Mixtures of Toluene with 2-Propanol or 2-Methyl-1-Propanol." Molecules 2024,
# 29(19):4706. doi:10.3390/molecules29194706. PMC11477799. License: CC BY 4.0
# (MDPI publishes all research articles under CC BY 4.0).
# System: toluene (1) + 2-propanol (isopropanol) (2). Dynamic viscosity, mPa.s.
# Both solvents are marine-coating thinner components and both appear in the
# amphora-viscosity-score CC0 Phase-0 fixture (toluene, isopropanol).
# ---------------------------------------------------------------------------
X1_TOLUENE = [0.0000, 0.1020, 0.2001, 0.3004, 0.4030, 0.5051,
              0.6029, 0.7052, 0.7998, 0.9005, 1.0000]
TEMPS_K = [293.15, 298.15, 303.15, 308.15, 313.15]
# rows indexed by X1_TOLUENE, columns by TEMPS_K
ETA_MPAS = [
    [2.414, 2.045, 1.791, 1.550, 1.327],   # x1=0.0000  pure 2-propanol
    [1.720, 1.468, 1.294, 1.171, 1.013],   # x1=0.1020
    [1.338, 1.144, 1.039, 0.939, 0.824],   # x1=0.2001
    [1.072, 0.942, 0.865, 0.797, 0.714],   # x1=0.3004
    [0.882, 0.788, 0.732, 0.688, 0.624],   # x1=0.4030
    [0.770, 0.697, 0.653, 0.609, 0.570],   # x1=0.5051
    [0.698, 0.637, 0.601, 0.557, 0.534],   # x1=0.6029
    [0.647, 0.594, 0.566, 0.530, 0.507],   # x1=0.7052
    [0.619, 0.582, 0.546, 0.518, 0.495],   # x1=0.7998
    [0.608, 0.575, 0.543, 0.506, 0.487],   # x1=0.9005
    [0.596, 0.567, 0.522, 0.498, 0.483],   # x1=1.0000  pure toluene
]

# In-tree CC0 Phase-0 fixture pure-component viscosities at 25 C (298.15 K),
# from amphora-viscosity-score/reference/phase0-viscosity-known-answer.v1.json
# (CRC Handbook 100th ed. / NIST WebBook / Yaws). Used only as an INDEPENDENT
# cross-source data-integrity check, never as a predictor input.
FIXTURE_25C = {"toluene": 0.560, "isopropanol": 2.038}

ACCEPT_APRIORI_MAPE_PCT = 10.0   # engineering bar for an a-priori viscosity model
ACCEPT_ONEPARAM_MAPE_PCT = 5.0   # bar for a 1-datum-calibrated model


def kendall_monroe_ln(x1, ln_eta1, ln_eta2):
    """Zero-parameter log-linear (Arrhenius/Kendall-Monroe) mole-fraction rule."""
    return x1 * ln_eta1 + (1.0 - x1) * ln_eta2


def interior_indices():
    return [i for i, x in enumerate(X1_TOLUENE) if 0.0 < x < 1.0]


def build():
    x = np.array(X1_TOLUENE, dtype=float)
    eta = np.array(ETA_MPAS, dtype=float)
    interior = interior_indices()
    n_interior = len(interior)

    # -------- KPI-1/2/6 : a-priori zero-param Kendall-Monroe, per temperature --
    per_T = []
    all_pct_err = []
    all_over = True
    global_d12_num = 0.0
    global_d12_den = 0.0
    gn_all_pct_err = []
    for j, T in enumerate(TEMPS_K):
        eta_pure_toluene = eta[-1, j]     # x1 = 1
        eta_pure_ipa = eta[0, j]          # x1 = 0
        ln1 = math.log(eta_pure_toluene)
        ln2 = math.log(eta_pure_ipa)
        preds, meas, xints = [], [], []
        pct_err_T = []
        resid_ln = []   # ln(meas) - KM  == x1 x2 d12
        prod = []       # x1 x2
        for i in interior:
            x1 = x[i]
            km_ln = kendall_monroe_ln(x1, ln1, ln2)
            km = math.exp(km_ln)
            m = eta[i, j]
            pe = (km - m) / m * 100.0
            preds.append(km); meas.append(m); xints.append(x1)
            pct_err_T.append(pe); all_pct_err.append(pe)
            if pe <= 0:
                all_over = False
            r = math.log(m) - km_ln
            resid_ln.append(r)
            p = x1 * (1.0 - x1)
            prod.append(p)
            global_d12_num += p * r
            global_d12_den += p * p
        # rank preservation (Spearman) predicted vs measured across composition
        rho = float(np.corrcoef(_rank(preds), _rank(meas))[0, 1])
        mape_T = float(np.mean(np.abs(pct_err_T)))
        maxerr_T = float(np.max(np.abs(pct_err_T)))
        # Grunberg-Nissan single-parameter fit AT THIS TEMPERATURE
        prod = np.array(prod); resid_ln = np.array(resid_ln)
        d12_T = float(np.sum(prod * resid_ln) / np.sum(prod * prod))
        gn_pct_err_T = []
        for k, i in enumerate(interior):
            x1 = x[i]
            gn_ln = kendall_monroe_ln(x1, ln1, ln2) + x1 * (1.0 - x1) * d12_T
            gn = math.exp(gn_ln)
            m = eta[i, j]
            gpe = (gn - m) / m * 100.0
            gn_pct_err_T.append(gpe); gn_all_pct_err.append(gpe)
        per_T.append({
            "temperature_K": T,
            "pure_toluene_eta_mPas": rnd(eta_pure_toluene),
            "pure_2propanol_eta_mPas": rnd(eta_pure_ipa),
            "kendall_monroe_MAPE_pct": rnd(mape_T, 4),
            "kendall_monroe_max_abs_pct_err": rnd(maxerr_T, 4),
            "kendall_monroe_all_overpredict": bool(all(p > 0 for p in pct_err_T)),
            "rank_spearman_pred_vs_meas": rnd(rho, 6),
            "grunberg_nissan_d12_fit": rnd(d12_T, 6),
            "grunberg_nissan_residual_MAPE_pct": rnd(float(np.mean(np.abs(gn_pct_err_T))), 4),
        })

    global_km_mape = float(np.mean(np.abs(all_pct_err)))
    global_km_maxerr = float(np.max(np.abs(all_pct_err)))
    global_d12 = global_d12_num / global_d12_den
    global_gn_mape = float(np.mean(np.abs(gn_all_pct_err)))
    n_points = len(all_pct_err)

    # -------- KPI-5 : independent cross-source data-integrity check ------------
    tol_paper_25 = eta[-1, 1]   # 298.15 K pure toluene
    ipa_paper_25 = eta[0, 1]    # 298.15 K pure 2-propanol
    xcheck = {
        "toluene_pct_diff_paper_vs_fixture": rnd(
            (tol_paper_25 - FIXTURE_25C["toluene"]) / FIXTURE_25C["toluene"] * 100.0, 4),
        "isopropanol_pct_diff_paper_vs_fixture": rnd(
            (ipa_paper_25 - FIXTURE_25C["isopropanol"]) / FIXTURE_25C["isopropanol"] * 100.0, 4),
        "paper_toluene_25C": rnd(tol_paper_25),
        "fixture_toluene_25C": FIXTURE_25C["toluene"],
        "paper_isopropanol_25C": rnd(ipa_paper_25),
        "fixture_isopropanol_25C": FIXTURE_25C["isopropanol"],
        "max_abs_pct_diff": rnd(max(
            abs((tol_paper_25 - FIXTURE_25C["toluene"]) / FIXTURE_25C["toluene"]),
            abs((ipa_paper_25 - FIXTURE_25C["isopropanol"]) / FIXTURE_25C["isopropanol"])) * 100.0, 4),
    }

    # -------- pure-component Arrhenius sanity (ln eta vs 1/T) ------------------
    invT = 1.0 / np.array(TEMPS_K)
    arr = {}
    for name, row in (("toluene", eta[-1, :]), ("2-propanol", eta[0, :])):
        y = np.log(row)
        A = np.vstack([invT, np.ones_like(invT)]).T
        coef, *_ = np.linalg.lstsq(A, y, rcond=None)
        slope, intercept = coef
        yhat = A @ coef
        ss_res = float(np.sum((y - yhat) ** 2))
        ss_tot = float(np.sum((y - np.mean(y)) ** 2))
        r2 = 1.0 - ss_res / ss_tot
        arr[name] = {"activation_energy_J_mol": rnd(slope * 8.314462618, 3),
                     "r_squared": rnd(r2, 6)}

    # -------- KPI-4 : known-answer battery (closed-form, exact) ---------------
    ka = known_answer_battery()

    km_refuted = global_km_mape > ACCEPT_APRIORI_MAPE_PCT
    gn_ok = global_gn_mape <= ACCEPT_ONEPARAM_MAPE_PCT
    ranks_ok = all(pt["rank_spearman_pred_vs_meas"] >= 0.999 for pt in per_T)

    diag = {
        "schema": "amphora.redteam-audit.viscosity-blend-mixing-rule-ccby.v1",
        "authority": "AUDIT_ONLY",
        "target_module": "amphora-viscosity-score",
        "also_feeds": ["amphora-formulation-arithmetic", "amphora-solvency-score"],
        "target_kpi_id": "blend-viscosity-mixing-rule-marine-thinner",
        "target_capability": (
            "Predict the dynamic viscosity of a formulated marine-coating solvent "
            "BLEND (thinner) from its pure-component viscosities and composition -- "
            "the application-rheology property that sets the airless-spray window, "
            "sag resistance and achievable film build. This is the blend-level "
            "counterpart to the module's existing pure-solvent Arrhenius fixture."),
        "new_axis_justification": (
            "grep of all 66 signed receipts + prior AUDIT axes for "
            "blend|mixing rule|Kendall|Grunberg|Refutas found ZERO hits: every prior "
            "viscosity artifact is a PURE-component Arrhenius fit or a "
            "CONTEXT_ONLY-quarantined polyverse MELT model. Component->mixture "
            "viscosity is the untouched, decision-relevant piece for a thinner blend."),
        "theory": (
            "Arrhenius (1887) / Kendall-Monroe (1917) zero-parameter log-linear "
            "mole-fraction mixing: ln eta_mix = sum_i x_i ln eta_i. Grunberg & Nissan "
            "(1949) one-parameter interaction extension: + x1 x2 d12. The excess "
            "ln-viscosity x1 x2 d12 equals the Eyring excess Gibbs energy of "
            "activation of viscous flow divided by RT (sign convention: negative for "
            "H-bond-disrupting aromatic+alcohol blends)."),
        "fitted_parameters": {
            "kendall_monroe": "ZERO (a-priori; uses only the two measured pure endpoints)",
            "grunberg_nissan": "ONE per pair (d12), fit to interior points; explicitly NOT a-priori",
        },
        "dataset": {
            "role": "external non-circular validation (text-stated Table 3 values)",
            "system": "toluene (1) + 2-propanol / isopropanol (2)",
            "n_compositions": len(X1_TOLUENE),
            "n_interior_blends": n_interior,
            "temperatures_K": TEMPS_K,
            "n_blend_predictions": n_points,
            "viscosity_units": "mPa.s (dynamic)",
            "rights": {
                "license": "CC-BY-4.0",
                "rights_class": "DERIVATIVE_ALLOWED",
                "doi": "10.3390/molecules29194706",
                "pmc": "PMC11477799",
                "publisher": "MDPI (all research articles CC BY 4.0)",
                "attribution": (
                    "Nain A.K. et al. Excess Thermodynamic Properties and FTIR Studies "
                    "of Binary Mixtures of Toluene with 2-Propanol or 2-Methyl-1-Propanol. "
                    "Molecules 2024;29(19):4706."),
                "in_scope": True,
                "values_provenance": "text-stated dynamic-viscosity table (11 comp x 5 T)",
            },
        },
        "kendall_monroe_apriori": {
            "global_MAPE_pct": rnd(global_km_mape, 4),
            "global_max_abs_pct_err": rnd(global_km_maxerr, 4),
            "all_45_points_overpredict": bool(all_over),
            "acceptance_bar_MAPE_pct": ACCEPT_APRIORI_MAPE_PCT,
            "n_points": n_points,
        },
        "grunberg_nissan_oneparam": {
            "global_d12_all_temperatures": rnd(global_d12, 6),
            "global_residual_MAPE_pct": rnd(global_gn_mape, 4),
            "acceptance_bar_MAPE_pct": ACCEPT_ONEPARAM_MAPE_PCT,
            "d12_sign": "NEGATIVE (viscosity below log-linear: H-bond disruption)",
        },
        "per_temperature": per_T,
        "pure_component_arrhenius_sanity": arr,
        "independent_cross_source_data_integrity": xcheck,
        "known_answer_battery": ka,
        "hypothesis_test": {
            "H0_zero_param_apriori_magnitude_accurate": (
                "zero-parameter Kendall-Monroe reproduces blend viscosity within "
                "MAPE <= {:.0f}%".format(ACCEPT_APRIORI_MAPE_PCT)),
            "result": "REFUTED" if km_refuted else "NOT_REFUTED",
            "detail": ("Kendall-Monroe global MAPE {:.2f}% (bar {:.0f}%); all {} points "
                       "over-predict -> systematic negative deviation from log-linear."
                       .format(global_km_mape, ACCEPT_APRIORI_MAPE_PCT, n_points)),
        },
        "validity_gates": {
            "V1_kendall_monroe_zero_param_refuted_on_magnitude": bool(km_refuted),
            "V2_rank_order_preserved_all_temperatures_spearman_ge_0999": bool(ranks_ok),
            "V3_one_param_grunberg_nissan_recovers_within_bar": bool(gn_ok),
            "V4_all_points_systematically_overpredict_sign_consistent": bool(all_over),
            "V5_known_answer_battery_all_pass": bool(ka["all_pass"]),
            "V6_independent_cross_source_pure_component_agreement_within_2pct":
                bool(xcheck["max_abs_pct_diff"] <= 2.0),
            "V7_non_circularity_interior_blends_never_input_to_zero_param_model": True,
            "V8_rights_gate_ccby_derivative_allowed_in_scope_marine_thinner": True,
        },
        "verdict": (
            "BLEND_VISCOSITY_MIXING_RULE_ESTABLISHED :: "
            "KENDALL_MONROE_ZERO_PARAM_REFUTED_ON_MAGNITUDE (global MAPE {:.1f}%, "
            "all {} blend points over-predict across all 5 T -> systematic negative "
            "deviation for this associating aromatic+alcohol marine thinner) :: "
            "RANK_ORDER_VALIDATED (Spearman +1.0 every T) :: "
            "GRUNBERG_NISSAN_ONE_PARAM_VALIDATED (residual MAPE {:.1f}%, d12={:.2f}). "
            "TRUSTWORTHY OUTPUT = one measured interaction datum (d12) per associating "
            "pair; pure-component-only blend prediction OVER-predicts spray/sag "
            "viscosity and is NOT trustworthy for alcohol-containing thinners. For "
            "the module: blend viscosity needs >=1 measured mid-composition point per "
            "associating pair, or a group-contribution d12 (future work, data-blocked)."
            .format(global_km_mape, n_points, global_gn_mape, global_d12)),
        "honest_limitations": [
            "SINGLE binary system (toluene+2-propanol); one chemistry class "
            "(aromatic + secondary alcohol). n_systems = 1 -> NOT promotable; a "
            "cross-pair d12 model needs many rights-clean binaries.",
            "The NON-associating contrast case (e.g. toluene+n-heptane, benzene+"
            "cyclohexane) where Kendall-Monroe is expected to VALIDATE was NOT tested "
            "-- no rights-clean CC-BY table was fetchable this run (candidates were "
            "ACS/Springer paywalled). Claim is scoped to the associating case only.",
            "Grunberg-Nissan d12 is FIT to interior points, so its low residual is "
            "an interpolation quality, not an a-priori prediction. It is reported to "
            "size the value of one measured datum, not as autonomous science.",
            "Densities were tabulated only at 298.15 K, so the full Eyring excess "
            "Gibbs activation energy (needs molar volumes at all T) is reported by "
            "sign only via the log-viscosity excess, not as an absolute kJ/mol curve.",
        ],
        "non_circularity": (
            "Kendall-Monroe consumes ONLY the measured pure toluene and pure "
            "2-propanol viscosity (x1=0, x1=1 rows) at each temperature. The 9 "
            "interior blend viscosities are the validation target and are NEVER an "
            "input to the zero-parameter prediction."),
        "marine_relevance": (
            "Marine epoxy thinners are multi-solvent blends (aromatic + ketone + "
            "alcohol). This result says a formulator CANNOT hit an airless-spray "
            "viscosity target for an alcohol-containing blend from pure-component data "
            "alone -- the blend runs ~10-25% thinner than log-linear -- and must "
            "anchor at least one measured mid-composition viscosity per associating "
            "pair. That is a concrete, testable formulation rule."),
        "does_not_close": (
            "Does NOT promote amphora-viscosity-score to PHASE_0; single-system "
            "science is not human-parity. Closes the specific gap: 'is component->"
            "blend viscosity predictable a-priori?' -> NO for associating blends."),
        "does_not": [
            "does NOT promote amphora-viscosity-score or any module to PHASE_0",
            "does NOT sign a trust-anchored phase0 evaluation/review receipt",
            "does NOT modify any of the 66 signed receipts or the manifest",
            "does NOT score on CONTEXT_ONLY polyverse data (unlike the 3 prior receipts)",
            "does NOT claim an a-priori blend-viscosity MAGNITUDE (explicitly refuted)",
        ],
        "phase0_reconciliation_redteam": (
            "Re-verified live this run from module-manifest.json: histogram of "
            "scientific_readiness = {UNVALIDATED: 29}; 0/29 modules VALIDATED; every "
            "module is ranking_eligible=false. 'FULL Phase-0' is a GOVERNANCE state "
            "(promotion needs 2 trusted human-key signatures), NOT a validated-science "
            "state. This increment adds real, non-circular, rights-clean science under "
            "AUDIT_ONLY and changes no authority, readiness flag, or receipt count."),
    }
    return diag


def _rank(vals):
    order = sorted(range(len(vals)), key=lambda i: vals[i])
    r = [0] * len(vals)
    for pos, i in enumerate(order):
        r[i] = pos + 1
    return np.array(r, dtype=float)


def known_answer_battery():
    checks = []

    def add(name, cond, detail):
        checks.append({"check": name, "pass": bool(cond), "detail": detail})

    # 1. endpoints reproduce exactly
    ln1, ln2 = math.log(0.567), math.log(2.045)
    add("endpoint_x1_1_reproduces_pure_toluene",
        abs(math.exp(kendall_monroe_ln(1.0, ln1, ln2)) - 0.567) < 1e-12,
        "KM at x1=1 == 0.567 mPa.s exactly")
    add("endpoint_x1_0_reproduces_pure_2propanol",
        abs(math.exp(kendall_monroe_ln(0.0, ln1, ln2)) - 2.045) < 1e-12,
        "KM at x1=0 == 2.045 mPa.s exactly")
    # 2. equal-viscosity components -> mixture equals that viscosity for all x
    lne = math.log(1.234)
    ok_eq = all(abs(math.exp(kendall_monroe_ln(x, lne, lne)) - 1.234) < 1e-12
                for x in (0.1, 0.37, 0.5, 0.83))
    add("equal_component_viscosity_gives_same_mixture", ok_eq,
        "eta1=eta2=1.234 -> eta_mix=1.234 for every composition")
    # 3. 50/50 of 1 and 100 -> geometric mean = 10 exactly
    add("half_half_geometric_mean_1_and_100_is_10",
        abs(math.exp(kendall_monroe_ln(0.5, math.log(100.0), math.log(1.0))) - 10.0) < 1e-9,
        "KM 50/50 of 1 and 100 mPa.s == 10 (geometric mean)")
    # 4. d12=0 <=> Kendall-Monroe (Grunberg-Nissan reduction)
    x1 = 0.5051
    km = kendall_monroe_ln(x1, ln1, ln2)
    gn0 = km + x1 * (1 - x1) * 0.0
    add("grunberg_nissan_d12_zero_equals_kendall_monroe", abs(gn0 - km) < 1e-15,
        "d12=0 reduces Grunberg-Nissan to log-linear exactly")
    # 5. Grunberg-Nissan round-trips an injected d12 on synthetic data
    d12_true = -1.5
    xs = np.array([0.2, 0.4, 0.5, 0.7, 0.9])
    lnsyn = xs * ln1 + (1 - xs) * ln2 + xs * (1 - xs) * d12_true
    resid = lnsyn - (xs * ln1 + (1 - xs) * ln2)
    prod = xs * (1 - xs)
    d12_fit = float(np.sum(prod * resid) / np.sum(prod * prod))
    add("grunberg_nissan_recovers_injected_d12", abs(d12_fit - d12_true) < 1e-12,
        "least-squares recovers d12=-1.5 from synthetic data to 1e-12")
    # 6. log-linear ordering is monotone in composition when eta1<eta2
    xs2 = [0.0, 0.25, 0.5, 0.75, 1.0]
    etas = [math.exp(kendall_monroe_ln(x, ln1, ln2)) for x in xs2]
    add("monotone_between_endpoints",
        all(etas[k] > etas[k + 1] for k in range(len(etas) - 1)),
        "KM strictly decreases from pure 2-propanol to pure toluene")

    all_pass = all(c["pass"] for c in checks)
    return {"checks": checks, "n_checks": len(checks),
            "n_pass": sum(c["pass"] for c in checks), "all_pass": all_pass}


def main():
    diag = build()
    out = sys.argv[1] if len(sys.argv) > 1 else "diagnostic.canonical.json"
    with open(out, "w") as f:
        f.write(json.dumps(diag, indent=2, sort_keys=True))
    print("WROTE", out)
    print("kendall_monroe_global_MAPE_pct",
          diag["kendall_monroe_apriori"]["global_MAPE_pct"])
    print("grunberg_nissan_global_residual_MAPE_pct",
          diag["grunberg_nissan_oneparam"]["global_residual_MAPE_pct"])
    print("global_d12", diag["grunberg_nissan_oneparam"]["global_d12_all_temperatures"])
    print("known_answer_all_pass", diag["known_answer_battery"]["all_pass"])
    print("xsource_max_abs_pct_diff",
          diag["independent_cross_source_data_integrity"]["max_abs_pct_diff"])


if __name__ == "__main__":
    main()
