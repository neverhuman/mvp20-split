#!/usr/bin/env python3
"""nielsen-tortuosity-baseline-v1  (amphora-barrier-corrosion-score, AUDIT_ONLY)

First PHYSICAL (named, a-priori, published-parameter) barrier baseline for the
module. Prior barrier-null-char-v1 showed only that MONOTONE *nulls* (solids-only,
PVC-only) fail to reproduce the intermediate Rc optimum. This asks a sharper,
falsifiable question with real coating physics:

  Can a published platelet-tortuosity barrier model -- Nielsen (1967) or
  Cussler (1988) -- reproduce the observed within-study Rc(loading) behaviour of
  the two strict in-class epoxy-amine nanofiller EIS ladders (asperti2024 clay,
  zhu2022 graphene), using ONLY published component densities and published
  filler aspect-ratio ranges (no fit to the Rc data)?

Two independent tests per series:
  (T1) STRUCTURAL / optimum-location. Nielsen and Cussler barrier improvement
       factor (BIF) are both strictly INCREASING in filler volume fraction phi,
       so both predict the best barrier at the HIGHEST loading. Observed optima
       are interior (clay 1 wt%, graphene 0.7 wt%). => both physical models are
       REFUTED on optimum location, exactly where the note attributes the drop to
       dispersion/agglomeration (a formulation-processing variable outside
       continuum tortuosity). Stronger than the trivial monotone null.
  (T2) INITIAL-RISE inversion. On the level-0 -> observed-optimum segment (where
       tortuosity CAN in principle apply), invert each model for the effective
       aspect ratio alpha_eff that the observed Rc-improvement factor demands,
       propagated over the published density band. Compare alpha_eff to the
       PUBLISHED aspect-ratio ceiling of that filler:
         - if alpha_eff <= published ceiling  => tortuosity is a SUFFICIENT a-priori
           explanation of the initial rise (CONSISTENT);
         - if alpha_eff  > published ceiling  => tortuosity ALONE cannot explain the
           rise; another mechanism dominates (REFUTED as sole cause).

Named baselines / parameters (all published, rights-clean constants):
  * Nielsen, L.E. J. Macromol. Sci. A 1967, 1(5), 929-942,
      doi 10.1080/10601326708053745.  BIF = tau = (1 + (alpha/2) phi)/(1 - phi).
  * Cussler, E.L. et al. J. Membr. Sci. 1988, 38(2), 161-174,
      doi 10.1016/S0376-7388(00)80877-7.  High-aspect regular-array flake limit
      P0/P = 1 + alpha^2 phi^2/(1 - phi).
  * Barrier-resistance mapping Rc/Rc0 = P0/P (ideal defect-free two-phase
      impermeable-platelet-in-resistive-matrix film: the same geometric
      tortuosity factor scales both diffusive permeability and ionic pore
      resistance). This idealisation is stated as the load-bearing assumption.
  * Densities: cured DGEBA-amine matrix 1.10-1.20 g/cm^3 (nominal 1.15; cf.
      Bicerano, Prediction of Polymer Properties, 3rd ed. 2002; and in-tree
      DGEBA+IPDA measured 1.105); organo-montmorillonite Cloisite 30B 1.90-2.00
      g/cm^3 (nominal 1.98, BYK/Southern Clay TDS); graphene 2.00-2.26 g/cm^3
      (nominal 2.20, graphite crystal density).
  * Published aspect-ratio ceilings: exfoliated montmorillonite alpha in
      [50, 1000] (LeBaron, Wang, Pinnavaia, Appl. Clay Sci. 1999, 15, 11-29;
      Bharadwaj, Macromolecules 2001, 34, 9189-9192);
      graphene / GNP flakes alpha in [1000, 30000] (few-layer lateral um / nm
      thickness; Cui, Kundalwal, Kumar, Carbon 2016, 98, 313-333).

Deterministic: stdlib only, no random, no timestamp, all floats round(.,6).
"""
import json, hashlib
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
DATA = ROOT / "amphora-barrier-corrosion-score/reference/mvp20/data/corrosion_series.json"
RND = 6


def r(x):
    return round(float(x), RND)


def vol_fraction(w_frac, rho_f, rho_m):
    """wt fraction -> volume fraction of filler."""
    if w_frac <= 0.0:
        return 0.0
    vf = w_frac / rho_f
    vm = (1.0 - w_frac) / rho_m
    return vf / (vf + vm)


def nielsen_bif(phi, alpha):
    """Nielsen 1967 tortuosity barrier improvement factor Rc/Rc0."""
    return (1.0 + 0.5 * alpha * phi) / (1.0 - phi)


def cussler_bif(phi, alpha):
    """Cussler 1988 high-aspect regular-array flake barrier improvement factor."""
    return 1.0 + (alpha * alpha * phi * phi) / (1.0 - phi)


def nielsen_alpha_from_bif(bif, phi):
    """Invert Nielsen for aspect ratio given observed BIF at phi."""
    # bif = (1 + 0.5 a phi)/(1-phi)  ->  a = 2*(bif*(1-phi) - 1)/phi
    return 2.0 * (bif * (1.0 - phi) - 1.0) / phi


def cussler_alpha_from_bif(bif, phi):
    """Invert Cussler for aspect ratio given observed BIF at phi."""
    # bif = 1 + a^2 phi^2/(1-phi)  ->  a = sqrt((bif-1)*(1-phi))/phi
    val = (bif - 1.0) * (1.0 - phi)
    if val < 0.0:
        val = 0.0
    return (val ** 0.5) / phi


# ---- published, rights-clean physical constants (citations in module docstring) ----
DENS = {
    "matrix_epoxy_amine": {"min": 1.10, "nom": 1.15, "max": 1.20},
    "cloisite30b":        {"min": 1.90, "nom": 1.98, "max": 2.00},
    "graphene":           {"min": 2.00, "nom": 2.20, "max": 2.26},
}
ALPHA_CEILING = {
    "montmorillonite": {"lo": 50.0, "hi": 1000.0,
                        "cite": "LeBaron 1999 Appl.Clay Sci. 15:11-29; Bharadwaj 2001 Macromolecules 34:9189"},
    "graphene":        {"lo": 1000.0, "hi": 30000.0,
                        "cite": "Cui,Kundalwal,Kumar 2016 Carbon 98:313-333"},
}

SERIES_CFG = {
    "asperti2024": {"filler_density_key": "cloisite30b", "alpha_family": "montmorillonite",
                    "matrix_note": "neat cured epoxy-amine matrix; clean single-filler ladder",
                    "confound": "none (single nanoclay loading ladder in neat epoxy-amine)"},
    "zhu2022":     {"filler_density_key": "graphene", "alpha_family": "graphene",
                    "matrix_note": "graphene added on top of a FIXED 35% mica/epoxy base",
                    "confound": "graphene increment sits on a 35% mica matrix; phi_graphene "
                                "referenced to total film. A denser mica-composite matrix "
                                "would LOWER phi_graphene and RAISE alpha_eff -- reported band "
                                "is therefore a lower bound on alpha_eff. SECONDARY/DIRECTIONAL."}
}


def analyze(series):
    sid = series["id"]
    cfg = SERIES_CFG[sid]
    levels = [float(x) for x in series["levels"]]          # wt%
    rc = [float(x) for x in series["values"]]              # ohm.cm2
    rho_f = DENS[cfg["filler_density_key"]]
    ceil = ALPHA_CEILING[cfg["alpha_family"]]

    # observed optimum
    best_idx = max(range(len(rc)), key=lambda i: rc[i])
    obs_best_level = levels[best_idx]
    model_best_idx = max(range(len(levels)), key=lambda i: levels[i])  # highest loading
    # both Nielsen and Cussler are strictly increasing in phi (hence in wt%)

    # phi per level at nominal densities (for reporting/monotonicity)
    phi_nom = [vol_fraction(w / 100.0, rho_f["nom"], DENS["matrix_epoxy_amine"]["nom"])
               for w in levels]

    # ---- T1 structural: model predicted best vs observed best ----
    t1 = {
        "observed_optimum_wt_pct": r(obs_best_level),
        "nielsen_predicted_best_wt_pct": r(levels[model_best_idx]),
        "cussler_predicted_best_wt_pct": r(levels[model_best_idx]),
        "both_models_strictly_increasing_in_phi": True,
        "nielsen_reproduces_optimum_location": best_idx == model_best_idx,
        "cussler_reproduces_optimum_location": best_idx == model_best_idx,
        "verdict": ("REFUTED_optimum_interior" if best_idx != model_best_idx
                    else "consistent_optimum_at_max_loading"),
    }

    # ---- T2 initial-rise inversion (level0 -> observed optimum) ----
    rc0 = rc[0]
    bif_obs = rc[best_idx] / rc0
    w_opt = obs_best_level / 100.0
    # density band -> phi band (filler dense & matrix light -> smaller phi -> larger alpha_eff)
    phi_hi = vol_fraction(w_opt, rho_f["min"], DENS["matrix_epoxy_amine"]["max"])  # largest phi
    phi_lo = vol_fraction(w_opt, rho_f["max"], DENS["matrix_epoxy_amine"]["min"])  # smallest phi
    phi_mid = vol_fraction(w_opt, rho_f["nom"], DENS["matrix_epoxy_amine"]["nom"])

    def band(inv):
        # alpha_eff is monotonically DECREASING in phi -> phi_lo gives max alpha, phi_hi gives min
        a_max = inv(bif_obs, phi_lo)
        a_min = inv(bif_obs, phi_hi)
        a_nom = inv(bif_obs, phi_mid)
        return a_min, a_nom, a_max

    ni_min, ni_nom, ni_max = band(nielsen_alpha_from_bif)
    cu_min, cu_nom, cu_max = band(cussler_alpha_from_bif)

    def classify(a_min):
        # tortuosity sufficient only if even the SMALLEST demanded alpha exceeds the
        # published ceiling => REFUTED; if a_min <= ceiling.hi it is physically reachable
        return "tortuosity_sufficient" if a_min <= ceil["hi"] else "tortuosity_insufficient_REFUTED"

    t2 = {
        "initial_rise_bif_observed": r(bif_obs),
        "optimum_wt_pct": r(obs_best_level),
        "phi_optimum_band": {"lo": r(phi_lo), "nom": r(phi_mid), "hi": r(phi_hi)},
        "published_alpha_ceiling": {"lo": r(ceil["lo"]), "hi": r(ceil["hi"]), "cite": ceil["cite"]},
        "nielsen_alpha_eff_band": {"min": r(ni_min), "nom": r(ni_nom), "max": r(ni_max)},
        "cussler_alpha_eff_band": {"min": r(cu_min), "nom": r(cu_nom), "max": r(cu_max)},
        "nielsen_verdict": classify(ni_min),
        "cussler_verdict": classify(cu_min),
        "interpretation": (
            "alpha_eff required by the observed initial Rc rise vs published filler "
            "aspect-ratio ceiling. Nielsen (linear-in-phi) demands the larger alpha; "
            "Cussler (quadratic) the smaller. Both compared to the SAME published ceiling."),
    }

    # ---- fail-closed sanity checks ----
    checks = {
        "phi_zero_at_zero_loading": phi_nom[0] == 0.0,
        "phi_monotone_increasing": all(phi_nom[i] < phi_nom[i + 1] for i in range(len(phi_nom) - 1)),
        "bif_unity_at_zero_loading": r(nielsen_bif(0.0, ceil["hi"])) == 1.0
                                     and r(cussler_bif(0.0, ceil["hi"])) == 1.0,
        "nielsen_strictly_increasing":
            all(nielsen_bif(phi_nom[i], ceil["hi"]) < nielsen_bif(phi_nom[i + 1], ceil["hi"])
                for i in range(len(phi_nom) - 1)),
        "cussler_strictly_increasing":
            all(cussler_bif(phi_nom[i], ceil["hi"]) < cussler_bif(phi_nom[i + 1], ceil["hi"])
                for i in range(len(phi_nom) - 1)),
        "alpha_eff_positive_finite": all(x > 0.0 for x in (ni_min, ni_nom, ni_max, cu_min, cu_nom, cu_max)),
        "observed_optimum_is_interior": 0 < best_idx < len(rc) - 1,
    }

    return {
        "id": sid,
        "cite": series["cite"],
        "doi": series["doi"],
        "in_class": series["in_class"],
        "variable": series["variable"],
        "filler_family": cfg["alpha_family"],
        "filler_density_g_cm3": {"min": rho_f["min"], "nom": rho_f["nom"], "max": rho_f["max"]},
        "matrix_note": cfg["matrix_note"],
        "confound": cfg["confound"],
        "levels_wt_pct": [r(x) for x in levels],
        "rc_ohm_cm2": [r(x) for x in rc],
        "phi_nominal": [r(x) for x in phi_nom],
        "use_limit": series["use_limit"],
        "T1_structural_optimum_location": t1,
        "T2_initial_rise_aspect_ratio_inversion": t2,
        "fail_closed_checks": checks,
        "all_checks_pass": all(checks.values()),
    }


def main():
    raw = DATA.read_bytes()
    d = json.loads(raw)
    strict = {s["id"]: s for s in d["series"] if s["id"] in ("asperti2024", "zhu2022")}
    per = [analyze(strict[k]) for k in sorted(strict)]

    result = {
        "schema": "amphora.barrier-corrosion-score.nielsen-tortuosity-baseline.v1",
        "module": "amphora-barrier-corrosion-score",
        "benchmark": "nielsen-tortuosity-baseline-v1",
        "authority": "AUDIT_ONLY",
        "promotes_authority": False,
        "modifies_manifest": False,
        "input_dataset": {
            "path": "amphora-barrier-corrosion-score/reference/mvp20/data/corrosion_series.json",
            "sha256": hashlib.sha256(raw).hexdigest(),
            "schema": d["schema"],
        },
        "named_baselines": [
            {"name": "Nielsen platelet-tortuosity barrier model",
             "citation": "Nielsen, L.E., J. Macromol. Sci. A 1967, 1(5), 929-942",
             "doi": "10.1080/10601326708053745",
             "form": "Rc/Rc0 = (1 + (alpha/2) phi)/(1 - phi)"},
            {"name": "Cussler high-aspect regular-array flake barrier model",
             "citation": "Cussler et al., J. Membr. Sci. 1988, 38(2), 161-174",
             "doi": "10.1016/S0376-7388(00)80877-7",
             "form": "Rc/Rc0 = 1 + alpha^2 phi^2/(1 - phi)"},
        ],
        "load_bearing_assumption": (
            "Rc/Rc0 = P0/P: the coating (pore) resistance improvement equals the "
            "permeability-reduction (tortuosity) factor, valid for an ideal defect-free "
            "two-phase film of impermeable platelets in an ionically-resistive matrix. "
            "Defects, active inhibition, cathodic delamination and cure-state effects are "
            "outside this idealisation."),
        "physical_constants": {"densities_g_cm3": DENS, "published_alpha_ceilings": ALPHA_CEILING},
        "rights": {
            "sources": ["asperti2024 (MDPI Materials, CC BY 4.0)",
                        "zhu2022 (MDPI Materials, CC BY 4.0)"],
            "use_limit_respected": "within-study direction only; NO cross-study pooling",
            "rights_class": "OPEN_ACCESS_CC_BY_4_0",
            "constants_class": "published physical constants / group-contribution reference values",
        },
        "per_series": per,
        "aggregate": {
            "n_strict_in_class_series": len(per),
            "both_physical_models_refuted_on_optimum_location": all(
                x["T1_structural_optimum_location"]["verdict"].startswith("REFUTED") for x in per),
            "initial_rise_nielsen_verdicts": {x["id"]: x["T2_initial_rise_aspect_ratio_inversion"]["nielsen_verdict"] for x in per},
            "initial_rise_cussler_verdicts": {x["id"]: x["T2_initial_rise_aspect_ratio_inversion"]["cussler_verdict"] for x in per},
        },
        "verdict": {
            "finding": (
                "Two published a-priori platelet-tortuosity barrier models (Nielsen 1967, "
                "Cussler 1988), parameterised with published densities and aspect-ratio "
                "ceilings and NOT fit to Rc, are STRUCTURALLY REFUTED on optimum LOCATION "
                "for both strict in-class epoxy-amine ladders: both are monotone in phi and "
                "predict best barrier at maximum loading, whereas both series peak at an "
                "interior loading. On the level-0 -> optimum INITIAL RISE the two fillers "
                "diverge: the clay ladder (asperti2024) demands an effective aspect ratio "
                "ABOVE the published montmorillonite ceiling (tortuosity insufficient to "
                "explain the initial jump alone), while the graphene ladder (zhu2022) is "
                "reproducible within the published graphene aspect-ratio range (tortuosity "
                "a sufficient a-priori explanation of its initial rise; mica-base confound "
                "noted, secondary)."),
            "advance_over_prior": (
                "barrier-null-char-v1 showed only that MONOTONE nulls fail on optimum "
                "location. This adds the first PHYSICAL named baselines, quantifies WHY "
                "they fail (interior optimum = dispersion/agglomeration beyond continuum "
                "tortuosity), and adds a NEW falsifiable a-priori discriminator: the "
                "effective-aspect-ratio inversion separates tortuosity-consistent (graphene) "
                "from tortuosity-insufficient (clay) initial barrier gains."),
            "does_not_establish": (
                "A validated positive barrier ranking model. The interior optimum -- the "
                "part of the signal that beats a monotone predictor -- is driven by "
                "dispersion/agglomeration, a formulation-processing variable no zero-"
                "parameter continuum-tortuosity model can capture. Closing that still needs "
                ">=3 pooled, protocol-controlled formulation->Rc series with dispersion/PVC "
                "metadata (the standing DATA wall)."),
            "scope_honesty": "Organic epoxy-amine coating-barrier EIS, correct module scope.",
        },
        "determinism": {"stdlib_only": True, "no_random": True, "no_timestamp": True,
                        "float_round_decimals": RND},
    }
    return result


def canonical(obj):
    return json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=True)


if __name__ == "__main__":
    import sys
    out = canonical(main())
    if len(sys.argv) > 1:
        Path(sys.argv[1]).write_text(out + "\n")
        print("wrote", sys.argv[1], "sha256",
              hashlib.sha256((out + "\n").encode()).hexdigest())
    else:
        print(out)
