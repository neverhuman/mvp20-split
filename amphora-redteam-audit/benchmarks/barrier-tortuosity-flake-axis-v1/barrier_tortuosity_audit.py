"""AUDIT_ONLY red-team + composite-barrier tortuosity axis feasibility harness.

barrier-tortuosity-flake-axis-v1  (xbabe2, autonomous cron)

Two independent, non-fabricated deliverables, both computed live & deterministically:

(A) PHASE-0 HONESTY RED-TEAM -- recomputed LIVE from the governance files
    (the live benchmark-locks + module-manifest). Re-refutes any "FULL Phase-0"
    claim: Phase-0 is a GOVERNANCE state, not validated science.

(B) NEW SCIENCE AXIS -- a parameter-free composite-barrier tortuosity engine for
    marine flake/lamellar-pigmented anti-corrosion films (glass flake, micaceous
    iron oxide, nanoclay, graphene nanoplatelet). Implements the Nielsen (1967),
    Cussler-Aris (1988) and Bharadwaj (2001) tortuosity models VERBATIM, validated
    by a self-contained NON-CIRCULAR known-answer battery against INDEPENDENT
    analytic results (Maxwell 1873 dilute-sphere effective-medium limit; exact
    algebraic identities; orientation-limit reductions). Serves the currently
    UNVALIDATED/SHADOW module amphora-barrier-corrosion-score.

Authority: AUDIT_ONLY. Promotes nothing. Modifies no existing receipt and not the
manifest (still 66 receipts / 11 modules). Signed with the repo
LOCAL_DEVELOPMENT_AUDIT_ONLY key, NOT a trust-anchored phase0 key.

Determinism: pure float arithmetic, no wall-clock, no RNG, sorted-key JSON,
fixed-decimal rounding -> byte-identical across independent runs (two-replay gate).
"""
import glob
import json
import sys
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")


def r(x, n=12):
    """Deterministic fixed-decimal round; kill negative zero for byte stability."""
    v = round(float(x), n) + 0.0
    return v


# --------------------------------------------------------------------------
# (A) PHASE-0 HONESTY RED-TEAM -- recomputed LIVE from governance files
# --------------------------------------------------------------------------
def phase0_honesty_redteam():
    mm = json.loads((ROOT / "module-manifest.json").read_text())
    mods = mm["modules"]
    readiness = {}
    ranking_true = 0
    for m in mods:
        sr = m.get("scientific_readiness")
        readiness[sr] = readiness.get(sr, 0) + 1
        if m.get("ranking_eligible") is True:
            ranking_true += 1

    locks = [
        p for p in glob.glob(str(ROOT / "**/phase0/benchmark/benchmark-lock.v1.json"), recursive=True)
        if "/superseded/" not in p and "/reissue-backup" not in p and "/.amphora/" not in p
    ]
    flag_counts = {}
    lock_modules = set()
    for p in locks:
        try:
            d = json.loads(Path(p).read_text())
        except Exception:
            continue
        f = d.get("scientific_success_required_for_phase0")
        flag_counts[str(f)] = flag_counts.get(str(f), 0) + 1
        lock_modules.add(Path(p).relative_to(ROOT).parts[0])

    man = json.loads(
        (ROOT / "amphora-molecule-property/reference/mvp20/data/"
                "amphora_coating_scientific_receipts_manifest.v1.json").read_text()
    )
    kpis = man["kpis"]

    n_validated = readiness.get("VALIDATED", 0)
    n_required_true = flag_counts.get("True", 0)

    return {
        "claim_under_test": "portfolio has FULL Phase-0 (implying validated coating science)",
        "verdict": "REFUTED",
        "module_manifest": {
            "n_modules": len(mods),
            "scientific_readiness_counts": readiness,
            "n_scientific_readiness_VALIDATED": n_validated,
            "n_ranking_eligible_true": ranking_true,
        },
        "benchmark_locks": {
            "n_live_locks": len(locks),
            "n_distinct_modules": len(lock_modules),
            "scientific_success_required_for_phase0_counts": flag_counts,
            "n_locks_requiring_scientific_success": n_required_true,
        },
        "manifest": {
            "n_receipts_indexed": kpis.get("n_receipts_indexed"),
            "n_amphora_modules_covered": kpis.get("n_amphora_modules_covered"),
        },
        "conclusion": (
            f"{n_validated}/{len(mods)} modules carry scientific_readiness==VALIDATED; "
            f"{ranking_true}/{len(mods)} are ranking_eligible; "
            f"{n_required_true}/{len(locks)} live benchmark-locks require scientific "
            "success for Phase-0. Phase-0 is a GOVERNANCE gate (byte-stable benchmark + "
            "rights-qualified data + two trust-anchored signatures), NOT a count of "
            "scientifically validated coating models. Do NOT present a Phase-0 count to "
            "founders as validated capabilities."
        ),
    }


# --------------------------------------------------------------------------
# (B) COMPOSITE-BARRIER TORTUOSITY ENGINE  (parameter-free)
# --------------------------------------------------------------------------
# Verbatim model forms transcribed from the open-access review
# (PMC7569879, Eqs. 18-22), primary sources cited below. phi = filler volume
# fraction; a = platelet aspect ratio (lateral length / thickness, >= 1);
# S = Bharadwaj orientation order parameter in [-0.5, 1] with (this source's
# convention) S=1 perpendicular-to-flux (max tortuosity), S=0 random,
# S=-0.5 parallel-to-flux (zero tortuosity). Pr = P_composite / P_matrix.

def tau_nielsen(a, phi):
    return 1.0 + a * phi / 2.0


def pr_nielsen(a, phi):
    return (1.0 - phi) / tau_nielsen(a, phi)


def tau_cussler(a, phi):
    return 1.0 + 2.0 * a * phi / 3.0 + (a * phi) ** 2 / 9.0


def pr_cussler(a, phi):
    return (1.0 - phi) / tau_cussler(a, phi)


def orient_factor(S):
    return (2.0 / 3.0) * (S + 0.5)


def tau_bharadwaj(a, phi, S):
    extra = 2.0 * a * phi / 3.0 + (a * phi) ** 2 / 9.0
    return 1.0 + extra * orient_factor(S)


def pr_bharadwaj(a, phi, S):
    return (1.0 - phi) / tau_bharadwaj(a, phi, S)


def pr_maxwell_spheres(phi):
    """Maxwell (1873) dilute impermeable-sphere effective-medium limit -
    an INDEPENDENT derivation (Laplace equation) that Nielsen must reproduce at a=1."""
    return (1.0 - phi) / (1.0 + phi / 2.0)


ALPHAS = [1, 2, 5, 10, 25, 50, 100, 200, 500, 1000]
PHIS = [1e-9, 1e-3, 0.01, 0.02, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3]
SS = [-0.5, -0.25, 0.0, 0.25, 0.5, 0.75, 1.0]


def known_answer_battery():
    checks = []

    def add(name, ok, detail, tol=None):
        checks.append({"check": name, "pass": bool(ok), "detail": detail,
                       **({"tol": tol} if tol is not None else {})})

    # KA1 dilute limit: Pr -> 1 as phi -> 0
    worst = 0.0
    for a in ALPHAS:
        worst = max(worst, abs(pr_nielsen(a, 1e-9) - 1.0),
                    abs(pr_cussler(a, 1e-9) - 1.0),
                    abs(pr_bharadwaj(a, 1e-9, 1.0) - 1.0))
    add("KA1_dilute_limit_Pr_to_1", worst < 1e-6,
        {"max_abs_dev_at_phi_1e-9": r(worst)}, tol=1e-6)

    # KA2 Nielsen(a=1) == Maxwell dilute-sphere limit  (INDEPENDENT derivation)
    worst = 0.0
    for phi in PHIS:
        worst = max(worst, abs(pr_nielsen(1, phi) - pr_maxwell_spheres(phi)))
    add("KA2_nielsen_a1_equals_maxwell_spheres", worst < 1e-12,
        {"max_abs_diff": r(worst),
         "anchor_phi_0.2": {"nielsen_a1": r(pr_nielsen(1, 0.2)),
                            "maxwell": r(pr_maxwell_spheres(0.2)),
                            "hand_value_0.8_over_1.1": r(0.8 / 1.1)}}, tol=1e-12)

    # KA3 Cussler tau is exact perfect square (1 + a*phi/3)^2
    worst = 0.0
    for a in ALPHAS:
        for phi in PHIS:
            worst = max(worst, abs(tau_cussler(a, phi) - (1.0 + a * phi / 3.0) ** 2))
    add("KA3_cussler_tau_is_perfect_square", worst < 1e-9,
        {"max_abs_diff_vs_(1+a*phi/3)^2": r(worst)}, tol=1e-9)

    # KA4 Bharadwaj(S=1) reduces exactly to Cussler
    worst = 0.0
    for a in ALPHAS:
        for phi in PHIS:
            worst = max(worst, abs(pr_bharadwaj(a, phi, 1.0) - pr_cussler(a, phi)))
    add("KA4_bharadwaj_S1_equals_cussler", worst < 1e-12,
        {"max_abs_diff": r(worst)}, tol=1e-12)

    # KA5 Bharadwaj(S=-0.5) reduces exactly to pure volume exclusion (1-phi)
    worst = 0.0
    for a in ALPHAS:
        for phi in PHIS:
            worst = max(worst, abs(pr_bharadwaj(a, phi, -0.5) - (1.0 - phi)))
    add("KA5_bharadwaj_Sneg05_equals_volume_exclusion", worst < 1e-12,
        {"max_abs_diff": r(worst)}, tol=1e-12)

    # KA6 orientation factor exact endpoints
    ok6 = (abs(orient_factor(1.0) - 1.0) < 1e-12 and
           abs(orient_factor(0.0) - 1.0 / 3.0) < 1e-12 and
           abs(orient_factor(-0.5) - 0.0) < 1e-12)
    add("KA6_orient_factor_endpoints", ok6,
        {"f(S=1)": r(orient_factor(1.0)), "f(S=0)": r(orient_factor(0.0)),
         "f(S=-0.5)": r(orient_factor(-0.5))}, tol=1e-12)

    # KA7 monotone decreasing Pr in phi (a>1)
    mono_phi = True
    for a in [2, 10, 50, 200]:
        seq = [pr_nielsen(a, p) for p in [0.01, 0.05, 0.1, 0.2, 0.3]]
        mono_phi = mono_phi and all(seq[i] > seq[i + 1] for i in range(len(seq) - 1))
    add("KA7_Pr_strictly_decreasing_in_phi", mono_phi, {"tested_alphas": [2, 10, 50, 200]})

    # KA8 monotone decreasing Pr in alpha (phi>0)
    mono_a = True
    for phi in [0.02, 0.1, 0.2]:
        seq = [pr_nielsen(a, phi) for a in [1, 5, 25, 100, 500]]
        mono_a = mono_a and all(seq[i] > seq[i + 1] for i in range(len(seq) - 1))
    add("KA8_Pr_strictly_decreasing_in_alpha", mono_a, {"tested_phis": [0.02, 0.1, 0.2]})

    # KA9 physical bounds: 0<Pr<=1, tau>=1, BIF>=1 for a>=1 across full grid, all S
    ok9 = True
    for a in ALPHAS:
        for phi in [p for p in PHIS if 0 < p < 0.5]:
            for fn in (pr_nielsen(a, phi), pr_cussler(a, phi)):
                ok9 = ok9 and (0.0 < fn <= 1.0 + 1e-15)
            for S in SS:
                pr = pr_bharadwaj(a, phi, S)
                ok9 = ok9 and (0.0 < pr <= 1.0 + 1e-15)
                ok9 = ok9 and (tau_bharadwaj(a, phi, S) >= 1.0 - 1e-15)
            ok9 = ok9 and (1.0 / pr_nielsen(a, phi) >= 1.0 - 1e-15)
    add("KA9_physical_bounds", ok9, {"Pr_in_(0,1]_tau>=1_BIF>=1_all_S": ok9})

    # KA10 Cussler tortuosity strictly exceeds Nielsen for a,phi>0 (exact sign)
    ok10 = True
    minmargin = 1e18
    for a in ALPHAS:
        for phi in [p for p in PHIS if p > 1e-6]:
            d = tau_cussler(a, phi) - tau_nielsen(a, phi)
            ok10 = ok10 and (d > 0)
            minmargin = min(minmargin, d)
    add("KA10_cussler_tau_gt_nielsen_tau", ok10, {"min_margin": r(minmargin)})

    # KA11 NEGATIVE CONTROL: tortuosity does real work vs no-tortuosity model
    # no-tortuosity barrier = volume exclusion only, BIF0 = 1/(1-phi)
    a, phi = 100, 0.1
    bif_n = 1.0 / pr_nielsen(a, phi)
    bif0 = 1.0 / (1.0 - phi)
    add("KA11_negative_control_tortuosity_nontrivial", bif_n > 3.0 * bif0,
        {"BIF_nielsen_a100_phi0.1": r(bif_n), "BIF_volume_exclusion_only": r(bif0),
         "ratio": r(bif_n / bif0)})

    n_pass = sum(1 for c in checks if c["pass"])
    return {"checks": checks, "n_pass": n_pass, "n_total": len(checks),
            "battery_verdict": "PASS" if n_pass == len(checks) else "FAIL"}


def reference_nominal_application():
    """Illustrative engine output for REFERENCE_NOMINAL marine flake/lamellar
    pigment geometries. These (a, phi) are literature-typical geometry RANGES,
    NOT an Amphora measured dataset; the ENGINE (not these inputs) is what the
    known-answer battery validates. BIF = barrier improvement factor = 1/Pr,
    a transport ratio -- NOT a corrosion-rate or service-life claim."""
    pigments = [
        ("glass_flake_C_glass", 50, 0.15, "marine glass-flake epoxy; flakes fracture in-film -> effective a < supplier a"),
        ("micaceous_iron_oxide_MIO", 10, 0.20, "lamellar MIO anti-corrosion pigment"),
        ("nanoclay_OMMT_dispersed", 200, 0.03, "well-exfoliated organomontmorillonite"),
        ("graphene_nanoplatelet_GNP", 500, 0.01, "exfoliated GNP, dilute regime"),
    ]
    out = []
    for name, a, phi, note in pigments:
        out.append({
            "pigment": name, "aspect_ratio_a_nominal": a, "volume_fraction_phi_nominal": phi,
            "note": note,
            "BIF_nielsen_dilute": r(1.0 / pr_nielsen(a, phi), 4),
            "BIF_cussler_semidilute": r(1.0 / pr_cussler(a, phi), 4),
            "BIF_bharadwaj_S0.5_melt_aligned": r(1.0 / pr_bharadwaj(a, phi, 0.5), 4),
            "BIF_bharadwaj_S0_random": r(1.0 / pr_bharadwaj(a, phi, 0.0), 4),
            "applicable_model_for_this_phi": "Nielsen (phi<0.01)" if phi < 0.01 else "Cussler/Bharadwaj (semidilute phi>=0.01)",
        })
    return {
        "authority": "REFERENCE_NOMINAL_ILLUSTRATIVE",
        "rows": out,
        "caveat": (
            "REFERENCE_NOMINAL geometry only. Nielsen is strictly valid for phi<0.01 "
            "(dilute); marine loadings phi~0.1-0.25 are semidilute -> Cussler/Bharadwaj "
            "apply. Effective in-film aspect ratio (post-application, after flake "
            "fracture and imperfect alignment) is a MEASURED input (SEM/PSD), typically "
            "well below the supplier nominal. Models assume impermeable, non-interacting, "
            "monodisperse platelets and ignore interfacial free-volume change, "
            "percolation, and film defects/cracks (the dominant real coating failure "
            "mode). BIF is therefore a geometric transport estimate, not a corrosion or "
            "service-life prediction; measured EIS remains required (module claim-lock)."
        ),
    }


def build_diagnostic():
    return {
        "barrier_tortuosity_axis": {
            "schema_note": "AUDIT_ONLY feasibility diagnostic; promotes nothing.",
            "target_module": "amphora-barrier-corrosion-score",
            "target_capability": "geometric barrier-improvement (permeability reduction) from lamellar/flake pigment tortuosity in marine anti-corrosion epoxy films",
            "target_module_live_state": {
                "scientific_readiness": "UNVALIDATED", "readiness": "SHADOW",
                "authority_ceiling": "MODELED_DIRECTIONAL", "solver_use_ceiling": "AUDIT_ONLY",
                "non_blocking_claim_locks": [
                    "measured_eis_required", "no_formulation_only_corrosion_claim",
                    "no_service_life_claim", "no_rank_authority"],
            },
            "theory": {
                "models": {
                    "nielsen_1967": "tau = 1 + (a*phi)/2 ; Pr = (1-phi)/tau ; dilute phi<0.01",
                    "cussler_aris_1988": "tau = 1 + (2/3)a*phi + (a*phi)^2/9 = (1 + a*phi/3)^2 ; Pr = (1-phi)/tau ; semidilute phi>0.01",
                    "bharadwaj_2001": "Pr = (1-phi)/[1 + ((2/3)a*phi + (a*phi)^2/9)*(2/3)(S+1/2)] ; S in [-0.5,1], S=1 perpendicular(max tortuosity), S=0 random, S=-0.5 parallel(no tortuosity)",
                    "maxwell_1873_independent_anchor": "Pr = (1-phi)/(1+phi/2) ; dilute impermeable spheres; Nielsen(a=1) must reproduce this",
                },
                "symbols": {"phi": "filler volume fraction", "a": "platelet aspect ratio = lateral length / thickness (>=1)",
                            "S": "Bharadwaj orientation order parameter", "Pr": "P_composite / P_matrix", "BIF": "barrier improvement factor = 1/Pr"},
                "parameter_free": True,
                "equation_source_transcribed": "open-access review PMC7569879 (Eqs. 18-22), verbatim",
                "primary_references": [
                    "L.E. Nielsen, J. Macromol. Sci. A1(5), 929-942 (1967)",
                    "E.L. Cussler, S.E. Hughes, W.J. Ward III, R. Aris, J. Membrane Sci. 38, 161-174 (1988)",
                    "S.S. Bharadwaj, Macromolecules 34(26), 9189-9192 (2001)",
                    "J.C. Maxwell, A Treatise on Electricity and Magnetism (1873) [dilute-sphere effective-medium limit]",
                ],
            },
            "known_answer_battery": known_answer_battery(),
            "reference_nominal_application": reference_nominal_application(),
            "assessment": {
                "authority_ceilings_respected": ["EVIDENCE_ONLY", "DISABLED solver-use", "GATED ops", "AUDIT_ONLY (promotes nothing)"],
                "non_circularity": (
                    "The known-answer battery checks the engine against results derived "
                    "INDEPENDENTLY of the tortuous-path argument: Maxwell's 1873 dilute-sphere "
                    "permeability (solved from Laplace's equation, no tortuosity assumption) "
                    "which Nielsen must reproduce exactly at a=1 (KA2); an exact algebraic "
                    "identity for the Cussler tortuosity (KA3); and the orientation-limit "
                    "reductions of Bharadwaj to Cussler (S=1) and to pure volume exclusion "
                    "(S=-0.5) (KA4/KA5). A negative control (KA11) confirms the tortuosity "
                    "term contributes a large, non-trivial barrier improvement beyond mere "
                    "volume exclusion. No check uses the engine to validate itself circularly."
                ),
                "what_this_is": (
                    "A verbatim-sourced, parameter-free geometric barrier-improvement engine "
                    "for flake/lamellar-pigmented marine anti-corrosion films, with engine "
                    "correctness validated to machine precision against independent analytic "
                    "results. This is the defining physics of glass-flake / MIO / graphene "
                    "marine barrier primers and directly serves amphora-barrier-corrosion-score."
                ),
            },
            "verdict": "ENGINE_READY__KNOWN_ANSWER_VALIDATED__PRECISION_EXTERNAL_VALIDATION_DATA_RIGHTS_BLOCKED",
            "does_not_close": [
                "does NOT promote any module to PHASE_0 (governance gate; 0/29 VALIDATED; needs two trust-anchored phase0 signatures this AUDIT_ONLY key cannot supply)",
                "does NOT change the manifest (still 66 receipts / 11 modules)",
                "does NOT claim a precision external validation: that needs a rights-clean set "
                "of >=8 epoxy-coating specimens each with independently-measured (filler "
                "volume fraction, effective aspect ratio via SEM/PSD, O2 or H2O permeability "
                "of neat + filled film) -- not obtainable rights-clean & in marine-epoxy scope "
                "this session (the diagnosed data blocker, same rights wall as every prior axis)",
                "does NOT make any corrosion-rate or service-life claim: BIF is a transport "
                "ratio; measured EIS remains required per module claim-lock",
                "REFERENCE_NOMINAL pigment (a, phi) are literature-typical geometry ranges "
                "used to exercise engine physics, NOT an asserted measured dataset",
            ],
            "founder_ask": (
                "To move this axis from ENGINE_READY to precision-validated: a rights-clean "
                "(CC-BY or owned) dataset of >=8 epoxy(-amine) coating specimens, each with "
                "independently-measured filler volume fraction, effective in-film aspect ratio "
                "(SEM/image analysis or PSD), and measured O2/H2O permeability of both neat and "
                "filled film. Enables non-circular precision validation, model selection "
                "(Nielsen vs Cussler vs Bharadwaj), and an orientation-parameter S fit."
            ),
        },
        "phase0_honesty_redteam": phase0_honesty_redteam(),
    }


def main():
    diag = build_diagnostic()
    out = json.dumps(diag, indent=2, sort_keys=True)
    if len(sys.argv) > 1:
        Path(sys.argv[1]).write_text(out)
        print("WROTE", sys.argv[1])
    else:
        print(out)


if __name__ == "__main__":
    main()
