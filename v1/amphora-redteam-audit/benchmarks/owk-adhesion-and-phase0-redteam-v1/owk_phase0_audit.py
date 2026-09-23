#!/usr/bin/env python3
"""owk-adhesion-and-phase0-redteam-v1 -- AUDIT_ONLY red-team increment.

Two deliverables, one deterministic two-replay-byte-stable diagnostic:

(A) PHASE-0 HONESTY RED-TEAM (the founder-facing map). Recomputed LIVE from the
    on-host governance artifacts (phase0-decision-report.v2.json,
    module-manifest.json, and all 29 canonical evidence/phase0 benchmark-lock
    files). Directly tests the claim "we have FULL Phase-0". Findings:
      * scientific_readiness == VALIDATED for 0 / 29 modules (even the crown-jewel
        solvency-score module is LOCKED_INTERNAL, not externally VALIDATED).
      * Of the 10 modules the report labels PHASE_0, 6 are scientific_readiness
        NOT_APPLICABLE (pure governance/infra: no science object to validate) and
        3 are LOCKED_INTERNAL (science ceiling is internal, not validated).
      * scientific_success_required_for_phase0 == false in ALL 29 benchmark-locks
        => "Phase-0" is a GOVERNANCE gate, not a validated-science gate.
      * The 19 PRE_PHASE_0 modules, bucketed by their EXACT blocking gate, so the
        founder can see which walls are data-rights, which are the human-key
        signature ceremony, and which are un-executed benchmarks.
    Conclusion: NO module can be moved PRE_PHASE_0 -> PHASE_0 by this autonomous
    cron -- promotion requires two distinct trusted HUMAN-key signatures on a
    module-local movement event, which this run cannot and must not forge.

(B) A REAL NEW SCIENCE INCREMENT establishing the ADHESION axis -- the biggest
    coating-physics capability currently ABSENT from the portfolio (the marine
    two-part epoxy "big three" is barrier + Tg + adhesion; Tg is diagnosed and
    data-rights-blocked, adhesion had no engine at all). We build and VALIDATE
    the Owens-Wendt-Kaelble / Fowkes geometric-mean combining rule -- the exact
    engine that computes coating<->substrate work of adhesion and interfacial
    water resistance (cathodic-disbondment relevance) -- on the textbook-canonical
    public-domain Fowkes (1964) water / n-alkane interfacial-tension dataset.
      * NON-CIRCULAR KPI: leave-one-out. Recover the dispersive surface-tension
        component of water gamma_w^d from n-1 alkanes, PREDICT the held-out
        alkane's water interfacial tension gamma_12, compare to measurement.
      * POSITIVE CONTROL: aromatics / CCl4 (pi-electron & induced-dipole
        interactions violate the pure-dispersive geometric mean) are correctly
        flagged as >3 sigma outliers -- the model fails exactly where theory says
        it must.
      * IN-SCOPE APPLICATION: Young-Dupre work of adhesion of water on a cured
        DGEBA + DDS marine epoxy from a rights-clean CC BY 4.0 water contact angle
        (61.77 deg, MDPI Polymers 2024 16(1)67 = PMC10780492, CC BY 4.0).

HONESTY POSTURE: promotes nothing; signs no phase0 evaluation/review; modifies no
existing receipt, the manifest, or any of the 66 signed receipts. The coating
solid-surface capstone (invert OWK on a MULTI-liquid contact-angle set to get
gamma_s^d / gamma_s^p and predict a held-out liquid's angle) remains blocked on
rights-clean data: this run's literature sweep found only single-liquid (water)
contact angles in CC-licensed DGEBA-amine sources -- so ADHESION is data-rights-
walled just like Tg. All arithmetic is deterministic and two-replay byte-stable.
"""
import hashlib
import json
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]


def sha(b):
    return hashlib.sha256(b).hexdigest()


def rnd(x, n=6):
    if isinstance(x, float):
        if math.isnan(x) or math.isinf(x):
            return None
        return round(x, n)
    if isinstance(x, dict):
        return {k: rnd(v, n) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [rnd(v, n) for v in x]
    return x


# --------------------------------------------------------------------------
# (A) PHASE-0 HONESTY RED-TEAM -- recomputed live from on-host governance state
# --------------------------------------------------------------------------
def phase0_redteam():
    rep_path = REPO / "config/program/phase0-decision-report.v2.json"
    man_path = REPO / "module-manifest.json"
    rep_bytes = rep_path.read_bytes()
    man_bytes = man_path.read_bytes()
    rep = json.loads(rep_bytes)
    man = json.loads(man_bytes)

    mods = rep["modules"]
    by_phase = {}
    for m in mods:
        by_phase.setdefault(m["phase"], []).append(m)

    phase0 = sorted(by_phase.get("PHASE_0", []), key=lambda m: m["module_id"])
    pre = sorted(by_phase.get("PRE_PHASE_0", []), key=lambda m: m["module_id"])

    # scientific_readiness distribution across ALL modules and within PHASE_0
    def readiness_hist(ms):
        h = {}
        for m in ms:
            h[m["scientific_readiness"]] = h.get(m["scientific_readiness"], 0) + 1
        return dict(sorted(h.items()))

    # blocker taxonomy for PRE_PHASE_0
    RIGHTS = "RIGHTS_OR_LICENSE_INCOMPLETE"
    NOTEXEC = "SCIENTIFIC_BENCHMARK_NOT_EXECUTED"
    NOSIG = "EVALUATION_SIGNATURE_ABSENT"
    buckets = {
        "data_rights_walled": [],       # rights/license incomplete (needs rights-clean data)
        "benchmark_not_executed": [],   # science harness exists but has not been run+signed
        "eval_binding_mismatch": [],    # governance: recorded benchmark not bound / diagnostic drift
        "other": [],
    }
    for m in pre:
        fg = m.get("failed_gates", [])
        fg_join = ";".join(fg)
        if any(g == RIGHTS for g in fg):
            buckets["data_rights_walled"].append(m["module_id"])
        elif any(g == NOTEXEC for g in fg):
            buckets["benchmark_not_executed"].append(m["module_id"])
        elif "EVALUATION_RESULT_MISMATCH" in fg_join:
            buckets["eval_binding_mismatch"].append(m["module_id"])
        else:
            buckets["other"].append(m["module_id"])
    buckets = {k: sorted(v) for k, v in buckets.items()}

    # every PRE_PHASE_0 module also carries an unmet human-signature/promotion gate
    needs_human_signature = sorted(
        m["module_id"] for m in pre
        if (NOSIG in m.get("failed_gates", [])) or (m.get("target_status") == "LOCKED_INTERNAL")
    )

    # scan ALL 29 canonical benchmark-locks for scientific_success_required_for_phase0
    lock_vals = []
    for lock in sorted(REPO.glob("*/evidence/phase0/benchmark/benchmark-lock.v1.json")):
        d = json.loads(lock.read_bytes())
        lock_vals.append((d.get("module_id", lock.parts[-5]),
                          d.get("scientific_success_required_for_phase0", "ABSENT")))
    ssr_true = sum(1 for _, v in lock_vals if v is True)
    ssr_false = sum(1 for _, v in lock_vals if v is False)

    all_readiness = readiness_hist(mods)
    n_validated = all_readiness.get("VALIDATED", 0)

    return {
        "inputs": {
            "phase0_decision_report_v2_sha256": sha(rep_bytes),
            "module_manifest_sha256": sha(man_bytes),
            "n_benchmark_locks_scanned": len(lock_vals),
        },
        "live_counts": {
            "module_count": rep.get("module_count"),
            "phase0_count": rep.get("phase0_count"),
            "pre_phase0_count": rep.get("pre_phase0_count"),
            "status": rep.get("status"),
        },
        "scientific_readiness_all_modules": all_readiness,
        "n_modules_scientifically_VALIDATED": n_validated,
        "phase0_modules_readiness_breakdown": readiness_hist(phase0),
        "phase0_module_ids": [m["module_id"] for m in phase0],
        "phase0_readiness_per_module": {
            m["module_id"]: m["scientific_readiness"] for m in phase0
        },
        "benchmark_lock_governance": {
            "scientific_success_required_for_phase0__true": ssr_true,
            "scientific_success_required_for_phase0__false": ssr_false,
            "interpretation": (
                "Phase-0 is a GOVERNANCE gate: no benchmark-lock in the portfolio "
                "makes scientific success a precondition for Phase-0. 'FULL Phase-0' "
                "therefore does NOT mean 'validated science'."),
        },
        "pre_phase0_blocker_taxonomy": buckets,
        "pre_phase0_needs_human_key_signature": needs_human_signature,
        "founder_question_answer": {
            "can_this_cron_move_any_module_PRE_to_PHASE_0": False,
            "why": (
                "Phase advancement is derived only from a module-local movement "
                "event carrying two DISTINCT trusted-human-key signatures. An "
                "autonomous cron holds only the LOCAL_DEVELOPMENT_AUDIT_ONLY key "
                "(not trust-anchored), so it can neither forge the movement event "
                "nor sign the evaluation/review. Every PRE_PHASE_0 module additionally "
                "carries at least one unmet gate (data-rights, un-executed benchmark, "
                "or eval-binding). Honest verdict: 0 autonomous promotions available."),
            "closest_to_real_science": {
                "module": "amphora-solvency-score",
                "state": "already PHASE_0 by governance; the ONLY module with an "
                         "externally-validated scientific track record behind it "
                         "(BigSolDB leave-solute-out RMSE 0.877), yet its "
                         "scientific_readiness ceiling is still LOCKED_INTERNAL, "
                         "not VALIDATED.",
            },
        },
    }


# --------------------------------------------------------------------------
# (B) OWK / FOWKES ADHESION ENGINE -- validated on public-domain constants
# --------------------------------------------------------------------------
# Fowkes, Ind. Eng. Chem. 1964, 56(12), 40; values reproduced verbatim in
# Adamson & Gast, "Physical Chemistry of Surfaces" and Israelachvili,
# "Intermolecular and Surface Forces". Water surface tension gamma_w = 72.8 mN/m
# at 20 C. Alkanes/cyclo-alkanes are purely dispersive (gamma^d = gamma_total).
# gamma_2 = liquid surface tension; gamma_12 = liquid/water interfacial tension.
GAMMA_W = 72.8  # mN/m, water surface tension at 20 C (dispersive + polar)

# purely-dispersive hydrocarbons (the geometric-mean rule SHOULD hold)
ALIPHATIC = [
    # name, gamma_2 (=gamma_2^d), gamma_12 (measured, vs water)
    ("n-hexane",      18.4, 51.1),
    ("n-heptane",     20.4, 50.2),
    ("n-octane",      21.8, 50.8),
    ("n-decane",      23.9, 51.2),
    ("n-tetradecane", 25.6, 52.2),
    ("cyclohexane",   25.5, 50.2),
    ("decalin",       29.9, 51.4),
]

# non-dispersive / polarizable controls (rule MUST fail: pi-electron & induced
# dipole interactions add attraction not captured by the dispersive geometric mean)
CONTROLS = [
    ("benzene",             28.9, 35.0),
    ("toluene",             28.5, 36.1),
    ("carbon_tetrachloride", 26.8, 45.0),
]


def recover_gamma_w_d(gamma_2, gamma_12):
    """Fowkes inversion for a purely-dispersive liquid:
       gamma_12 = gamma_w + gamma_2 - 2*sqrt(gamma_w^d * gamma_2)
       => gamma_w^d = (gamma_w + gamma_2 - gamma_12)^2 / (4*gamma_2)."""
    return (GAMMA_W + gamma_2 - gamma_12) ** 2 / (4.0 * gamma_2)


def predict_gamma_12(gamma_w_d, gamma_2):
    return GAMMA_W + gamma_2 - 2.0 * math.sqrt(gamma_w_d * gamma_2)


def owk_engine():
    # per-aliphatic recovered gamma_w^d
    recov = [(name, g2, g12, recover_gamma_w_d(g2, g12)) for name, g2, g12 in ALIPHATIC]
    gwd_vals = [r[3] for r in recov]
    n = len(gwd_vals)
    mean_gwd = sum(gwd_vals) / n
    var_gwd = sum((v - mean_gwd) ** 2 for v in gwd_vals) / (n - 1)
    sd_gwd = math.sqrt(var_gwd)

    # NON-CIRCULAR leave-one-out gamma_12 prediction:
    # gamma_w^d fitted on the OTHER n-1 aliphatics, predict held-out gamma_12.
    loo_rows = []
    abs_errs = []
    pct_errs = []
    for i, (name, g2, g12, _) in enumerate(recov):
        others = [gwd_vals[j] for j in range(n) if j != i]
        gwd_fit = sum(others) / len(others)
        g12_pred = predict_gamma_12(gwd_fit, g2)
        ae = abs(g12_pred - g12)
        pe = 100.0 * ae / g12
        abs_errs.append(ae)
        pct_errs.append(pe)
        loo_rows.append({
            "liquid": name, "gamma_2_mN_m": g2, "gamma_w_d_fit_mN_m": gwd_fit,
            "gamma_12_pred_mN_m": g12_pred, "gamma_12_meas_mN_m": g12,
            "abs_err_mN_m": ae, "pct_err": pe,
        })
    loo_mae = sum(abs_errs) / n
    loo_mape = sum(pct_errs) / n
    max_ae = max(abs_errs)

    # POSITIVE CONTROL: recovered apparent gamma_w^d for polar/polarizable liquids
    # should be many sigma away from the aliphatic 21.8 mN/m consensus.
    ctrl_rows = []
    for name, g2, g12 in CONTROLS:
        app = recover_gamma_w_d(g2, g12)
        z = (app - mean_gwd) / sd_gwd
        ctrl_rows.append({
            "liquid": name, "gamma_2_mN_m": g2, "gamma_12_meas_mN_m": g12,
            "apparent_gamma_w_d_mN_m": app, "sigma_from_aliphatic_consensus": z,
            "flagged_nondispersive": abs(z) > 3.0,
        })
    controls_all_flagged = all(r["flagged_nondispersive"] for r in ctrl_rows)

    return {
        "theory": ("Fowkes / Owens-Wendt-Kaelble geometric-mean combining rule for the "
                   "dispersive component of interfacial free energy: "
                   "gamma_12 = gamma_1 + gamma_2 - 2*sqrt(gamma_1^d * gamma_2^d). This is "
                   "the engine that yields the solid<->coating work of adhesion "
                   "W_a = gamma_1 + gamma_2 - gamma_12 and the interfacial water resistance "
                   "governing marine cathodic disbondment."),
        "constants": {"gamma_water_mN_m_at_20C": GAMMA_W,
                      "reference_gamma_water_d_literature_mN_m": 21.8},
        "data_source": ("Fowkes, Ind. Eng. Chem. 1964, 56(12):40 (public-domain fundamental "
                        "physical measurements; values reproduced verbatim in Adamson & Gast "
                        "and in Israelachvili). Alkane/cyclo-alkane surface tensions and "
                        "their water interfacial tensions at 20 C."),
        "recovered_gamma_w_d": [
            {"liquid": r[0], "gamma_2_mN_m": r[1], "gamma_12_mN_m": r[2],
             "recovered_gamma_w_d_mN_m": r[3]} for r in recov],
        "gamma_w_d_consensus": {
            "n_aliphatic": n, "mean_mN_m": mean_gwd, "sd_mN_m": sd_gwd,
            "abs_dev_from_literature_21_8": abs(mean_gwd - 21.8),
            "all_within_1_mN_m_of_mean": all(abs(v - mean_gwd) <= 1.0 for v in gwd_vals),
        },
        "loo_prediction_kpi": {
            "description": ("leave-one-out: gamma_w^d fitted on the other n-1 aliphatics, "
                            "predict the held-out liquid/water interfacial tension"),
            "rows": loo_rows,
            "loo_mae_mN_m": loo_mae,
            "loo_mape_pct": loo_mape,
            "loo_max_abs_err_mN_m": max_ae,
            "n": n,
        },
        "positive_control_nondispersive": {
            "description": ("aromatics & CCl4: apparent gamma_w^d must diverge (>3 sigma) from "
                            "the aliphatic consensus because pi/induced-dipole interactions "
                            "are not captured by the dispersive geometric mean"),
            "rows": ctrl_rows,
            "all_controls_correctly_flagged": controls_all_flagged,
        },
        "verdict": (
            "ENGINE_VALIDATED_ON_PUBLIC_DOMAIN_CONSTANTS: the dispersive geometric-mean "
            "combining rule recovers gamma_w^d = %.2f +/- %.2f mN/m across 7 independent "
            "aliphatics (literature 21.8), LOO interfacial-tension MAPE %.2f%%, and correctly "
            "rejects all 3 non-dispersive controls (>3 sigma). The OWK adhesion engine is "
            "sound; the coating solid-surface-energy CAPSTONE remains data-rights-blocked "
            "(no CC-licensed MULTI-liquid contact-angle set on cured DGEBA-amine found this run)."
        ) % (mean_gwd, sd_gwd, loo_mape),
    }


def coating_application():
    # Young-Dupre work of adhesion (exact thermodynamic identity, no fitting):
    #   W_a(liquid on solid) = gamma_liquid * (1 + cos theta)
    # Rights-clean CC BY 4.0 anchor: static water contact angle on a cured
    # DGEBA + DDS (4,4'-diaminodiphenyl sulfone) marine epoxy, pristine (t=0),
    # 61.77 deg -- MDPI Polymers 2024, 16(1):67 = PMC10780492, CC BY 4.0.
    theta_deg = 61.77
    theta = math.radians(theta_deg)
    w_adh_water = GAMMA_W * (1.0 + math.cos(theta))
    # spreading coefficient of water on the epoxy: S = gamma_s - gamma_l - gamma_sl;
    # equivalently S = gamma_l*(cos theta - 1) <= 0 (water does NOT spread => desirable
    # hydrophobic marine surface).
    spreading = GAMMA_W * (math.cos(theta) - 1.0)
    return {
        "model": "Young-Dupre (exact identity): W_a = gamma_l (1 + cos theta)",
        "rights_clean_anchor": {
            "system": "cured DGEBA + DDS marine epoxy (pristine, t=0)",
            "measured_water_contact_angle_deg": theta_deg,
            "source": "MDPI Polymers 2024, 16(1):67 (PMC10780492)",
            "license": "CC BY 4.0",
        },
        "water_work_of_adhesion_mN_m": w_adh_water,
        "water_spreading_coefficient_mN_m": spreading,
        "interpretation": (
            "W_a(water) = 107.2 mN/m and S < 0: water wets but does not spread on the "
            "cured DGEBA-DDS surface -- a moderately hydrophobic interface consistent with "
            "marine barrier intent. This is a single rights-clean coating datapoint, NOT a "
            "cross-system KPI; the multi-system adhesion KPI is data-rights-blocked."),
        "scope_honesty": (
            "Young-Dupre needs only one liquid and gives W_a directly; it does NOT decompose "
            "into gamma_s^d / gamma_s^p (that needs >=2 liquids). The decomposition + held-out-"
            "liquid prediction (the true adhesion capstone) awaits a CC-licensed multi-liquid "
            "contact-angle dataset on DGEBA-amine networks."),
    }


def main():
    diag = {
        "schema": "amphora.redteam-audit.owk-adhesion-and-phase0-redteam.v1",
        "authority": "AUDIT_ONLY",
        "target_module": "amphora-molecule-property",
        "target_capability": "work_of_adhesion / interfacial_free_energy (ADHESION axis)",
        "target_kpi_id": "owk-fowkes-combining-rule-loo-interfacial-tension",
        "predecessor": "surface-tension-parachor-ccby-v1 (liquid surface tension input)",
        "promotes_authority": False,
        "human_review_performed": False,
        "organizational_independence_asserted": False,
        "supersedes_nothing": True,
        "phase0_reconciliation_redteam": phase0_redteam(),
        "owk_adhesion_engine": owk_engine(),
        "coating_application": coating_application(),
        "does_not": [
            "promote any module or change the Phase-0 count",
            "sign any phase0 evaluation or review receipt",
            "modify any of the 66 existing signed receipts or the manifest",
            "assert scientific VALIDATED status for any module",
            "use a measured target as a model feature (non-circular)",
        ],
    }
    diag = rnd(diag, 6)
    out = json.dumps(diag, indent=2, sort_keys=True).encode()
    dest = sys.argv[1] if len(sys.argv) > 1 else "diagnostic.OUT.json"
    Path(dest).write_bytes(out)
    print("WROTE", dest)
    print("diagnostic_sha256", sha(out))


if __name__ == "__main__":
    main()
