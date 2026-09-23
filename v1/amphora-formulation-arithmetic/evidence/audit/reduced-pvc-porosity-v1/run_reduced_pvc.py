#!/usr/bin/env python3
"""AUDIT_ONLY reduced-PVC / above-CPVC porosity battery for
amphora-formulation-arithmetic.

Adds the *pigmentation-regime* layer of dimensioned formulation arithmetic that
the module's prior receipts did NOT compute.  The prior surface computes PVC and
(via the ingredient-library Daniel receipt) CPVC as numbers; this receipt adds
the zero-fitted-parameter Bierwagen reduced pigment volume concentration and its
exact geometric consequences above CPVC:

  * reduced PVC:                    LAMBDA = PVC / CPVC
  * air-void porosity (PVC>=CPVC):  pi = 1 - CPVC/PVC = 1 - 1/LAMBDA
                                    (pi = 0 for PVC < CPVC)
  * dry-film volume amplification:  V_film / V_nonvolatile = LAMBDA  (PVC>=CPVC)
                                    => porous-regime DFT = LAMBDA * void-free DFT
  * dry-film density:               rho_film = (1 - pi) * rho_nv,
                                    rho_nv = PVC*rho_p + (1-PVC)*rho_b

Derivation (volume bookkeeping, checked numerically in KA12): above CPVC the
pigment skeleton packs at its critical packing fraction, so the film volume is
set by the pigment alone, V_film = V_p/CPVC; binder fills part of the
interstitial space and the remainder is air.  With V_p = PVC*V_nv this gives
V_film = LAMBDA*V_nv and pi = 1 - CPVC/PVC exactly.

Primary sources (rights-clean primary/secondary literature, coating scope):
  * Asbeck, W.K. & Van Loo, M. 1949, "Critical Pigment Volume Relationships",
    Ind. Eng. Chem. 41(7) 1470-1475, DOI 10.1021/ie50475a042 -- CPVC concept,
    void formation above CPVC.
  * Bierwagen, G.P. & Hay, T.K. 1975, "The reduced pigment volume concentration
    as an important parameter in interpreting and predicting the properties of
    organic coatings", Prog. Org. Coat. 3(4) 281-303,
    DOI 10.1016/0300-9440(75)80047-4 -- reduced PVC LAMBDA = PVC/CPVC and the
    porosity relation above CPVC.
  * Patton, T.C. 1979, "Paint Flow and Pigment Dispersion", 2nd ed., Wiley,
    ISBN 0-471-03272-7 -- CPVC/porosity arithmetic and the Daniel oil-absorption
    -> CPVC relation used by the in-tree ingredient-library receipt.

Inputs are carried verbatim from in-tree rights-clean artifacts (SHA-256
recorded): the 10 Daniel-CPVC values + skeletal densities + D281 oil absorptions
from the signed amphora-ingredient-library oil-absorption-cpvc-v1 diagnostic,
and DGEBA-331 + Ancamide 350A densities/equivalent weights from facts.json for
the stoichiometric ideal-mix binder density.  NOTE the binder density is the
ASTM D2697-consistent ideal-mixing NONVOLATILE density convention used by the
prior dimensioned receipt; it is NOT a cured-network density claim (a-priori
cured density was REFUTED in amphora-cured-network-density-apriori-refuted).

ZERO fitted parameters.  No promotion, no manifest edit, no scientific_readiness
flip, no live-Rust-engine edit, no locked-dataset or signed-KPI edit. AUDIT_ONLY.
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
ING_DIAG = ROOT / "amphora-ingredient-library/evidence/audit/oil-absorption-cpvc-v1/diagnostic.canonical.json"
ING_RECEIPT = ROOT / "amphora-ingredient-library/evidence/audit/oil-absorption-cpvc-v1/oil-absorption-cpvc-receipt.v1.dsse.json"
FACTS = ROOT / "amphora-ingredient-library/reference/mvp20/data/facts.json"
OUT = HERE / (sys.argv[1] if len(sys.argv) > 1 else "diagnostic.canonical.json")

MC_SEED = 20260731
MC_N = 400_000
OA_DECLARED_REL_HALFWIDTH = 0.10  # declared rectangular supplier-spread band on OA


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def r6(x):
    return round(float(x), 6)


# ----- fail-closed core arithmetic ------------------------------------------
def check_domain(pvc, cpvc):
    if not (0.0 <= pvc <= 1.0):
        raise ValueError("PVC outside [0,1]")
    if not (0.0 < cpvc <= 1.0):
        raise ValueError("CPVC outside (0,1]")


def reduced_pvc(pvc, cpvc):
    check_domain(pvc, cpvc)
    return pvc / cpvc


def porosity(pvc, cpvc):
    check_domain(pvc, cpvc)
    return max(0.0, 1.0 - cpvc / pvc) if pvc > 0.0 else 0.0


def film_volume_factor(pvc, cpvc):
    """V_film per unit nonvolatile (pigment+binder) volume."""
    check_domain(pvc, cpvc)
    lam = pvc / cpvc
    return lam if lam > 1.0 else 1.0


def film_density(pvc, cpvc, rho_p, rho_b):
    if rho_p <= 0.0 or rho_b <= 0.0:
        raise ValueError("density must be positive")
    rho_nv = pvc * rho_p + (1.0 - pvc) * rho_b
    return (1.0 - porosity(pvc, cpvc)) * rho_nv


def porosity_by_volume_bookkeeping(pvc, cpvc):
    """Independent derivation path: explicit 3-component volume balance."""
    check_domain(pvc, cpvc)
    if pvc == 0.0:
        return 0.0
    v_nv = 1.0                      # unit nonvolatile volume
    v_p = pvc * v_nv
    v_b = (1.0 - pvc) * v_nv
    v_film = v_p / cpvc             # pigment skeleton sets film volume
    if v_film <= v_nv:              # binder still overfills: void-free film
        return 0.0
    v_void = v_film - v_p - v_b
    return v_void / v_film


# ----- inputs ----------------------------------------------------------------
ing = json.loads(ING_DIAG.read_text())
facts = json.loads(FACTS.read_text())["entries"]

pigments = []
for row in ing["checkA_daniel_cpvc"]["per_constant"]:
    name = row["constant_density"].split(".")[1]
    pigments.append({
        "pigment": name,
        "cpvc": row["cpvc_volume_fraction"],
        "rho_p": row["skeletal_density_g_per_cm3"],
        "oa_g_per_100g": row["oa_g_per_100g"],
        "oa_grade": row["oa_grade"],
    })
pigments.sort(key=lambda p: p["pigment"])
RHO_OIL = ing["constants"]["rho_oil_g_per_mL"]

# stoichiometric ideal-mix binder density, DGEBA-331 + Ancamide 350A
rho_a = facts["resin.dgeba_331.density"]["value"]        # 1.16
eew = facts["resin.dgeba_331.eew"]["value"]              # 187
rho_h = facts["hardener.ancamide_350a.density"]["value"] # 0.97
ahew = facts["hardener.ancamide_350a.ahew"]["value"]     # 100
phr = 100.0 * ahew / eew
RHO_B = (100.0 + phr) / (100.0 / rho_a + phr / rho_h)

PVC_GRID = [0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75]

# ----- known-answer battery --------------------------------------------------
TOL = 1e-12
ka = {}

# KA1 continuity at CPVC: pi(CPVC)=0, LAMBDA=1 exactly
ka["ka1_continuity_at_cpvc"] = all(
    porosity(p["cpvc"], p["cpvc"]) == 0.0 and reduced_pvc(p["cpvc"], p["cpvc"]) == 1.0
    for p in pigments)

# KA2 identity pi = 1 - 1/LAMBDA on the full grid above CPVC
ka["ka2_pi_lambda_identity"] = all(
    abs(porosity(pvc, p["cpvc"]) - (1.0 - 1.0 / reduced_pvc(pvc, p["cpvc"]))) < TOL
    for p in pigments for pvc in PVC_GRID if pvc >= p["cpvc"])

# KA3 below-CPVC clamp: pi=0 and film factor 1
ka["ka3_below_cpvc_void_free"] = all(
    porosity(pvc, p["cpvc"]) == 0.0 and film_volume_factor(pvc, p["cpvc"]) == 1.0
    for p in pigments for pvc in PVC_GRID if pvc < p["cpvc"])

# KA4 monotonicity: pi strictly increasing in PVC above CPVC; decreasing in CPVC
mono_pvc = all(
    porosity(b, p["cpvc"]) > porosity(a, p["cpvc"])
    for p in pigments
    for a, b in zip(PVC_GRID, PVC_GRID[1:]) if a > p["cpvc"])
mono_cpvc = all(
    porosity(0.70, c1) > porosity(0.70, c2)
    for c1, c2 in [(0.35, 0.40), (0.40, 0.45), (0.45, 0.50), (0.50, 0.55)])
ka["ka4_monotonicity"] = mono_pvc and mono_cpvc

# KA5 all-pigment limit PVC->1: pi=1-CPVC and rho_film=CPVC*rho_p exactly
ka["ka5_pvc1_limit"] = all(
    abs(porosity(1.0, p["cpvc"]) - (1.0 - p["cpvc"])) < TOL and
    abs(film_density(1.0, p["cpvc"], p["rho_p"], RHO_B) - p["cpvc"] * p["rho_p"]) < TOL
    for p in pigments)

# KA6 film-volume amplification equals LAMBDA above CPVC and 1/(1-pi)
ka["ka6_film_volume_amplification"] = all(
    abs(film_volume_factor(pvc, p["cpvc"]) - reduced_pvc(pvc, p["cpvc"])) < TOL and
    abs(film_volume_factor(pvc, p["cpvc"]) - 1.0 / (1.0 - porosity(pvc, p["cpvc"]))) < 1e-9
    for p in pigments for pvc in PVC_GRID if pvc > p["cpvc"])

# KA7 mass closure: voids are massless, rho_film*V_film == rho_nv*V_nv
def mass_closure(pvc, cpvc, rho_p, rho_b):
    rho_nv = pvc * rho_p + (1.0 - pvc) * rho_b
    vf = film_volume_factor(pvc, cpvc)
    return abs(film_density(pvc, cpvc, rho_p, rho_b) * vf - rho_nv * 1.0)

ka["ka7_mass_closure"] = all(
    mass_closure(pvc, p["cpvc"], p["rho_p"], RHO_B) < 1e-9
    for p in pigments for pvc in PVC_GRID)

# KA8 pi/LAMBDA take no density argument (geometry only); rho_film is degree-1
# homogeneous in the densities: doubling both densities doubles rho_film
ka["ka8_density_homogeneity"] = all(
    abs(film_density(pvc, p["cpvc"], 2.0 * p["rho_p"], 2.0 * RHO_B)
        - 2.0 * film_density(pvc, p["cpvc"], p["rho_p"], RHO_B)) < 1e-9
    for p in pigments for pvc in PVC_GRID)

# KA9 scale invariance: intensive outputs unchanged under batch scaling
def intensive(pvc, cpvc, rho_p, rho_b, scale):
    v_p, v_b = scale * pvc, scale * (1.0 - pvc)
    pvc_s = v_p / (v_p + v_b)
    return (porosity(pvc_s, cpvc), reduced_pvc(pvc_s, cpvc),
            film_density(pvc_s, cpvc, rho_p, rho_b))

ka["ka9_scale_invariance"] = all(
    all(abs(x - y) < TOL for x, y in
        zip(intensive(0.55, p["cpvc"], p["rho_p"], RHO_B, 1.0),
            intensive(0.55, p["cpvc"], p["rho_p"], RHO_B, 137.5)))
    for p in pigments)

# KA10 hostile nulls fail closed
def rejects(fn, *args):
    try:
        fn(*args)
        return False
    except ValueError:
        return True

ka["ka10_hostile_nulls_fail_closed"] = all([
    rejects(porosity, -0.1, 0.5), rejects(porosity, 1.1, 0.5),
    rejects(porosity, 0.5, 0.0), rejects(porosity, 0.5, -0.2),
    rejects(porosity, 0.5, 1.0001), rejects(reduced_pvc, 0.5, 0.0),
    rejects(film_density, 0.5, 0.5, -1.0, 1.0),
    rejects(film_density, 0.5, 0.5, 5.0, 0.0),
])

# KA11 Daniel parity: re-derive the 10 receipt CPVCs from OA (provenance parity,
# same formula as the signed ingredient receipt -- NOT independent validation)
daniel_rows = []
for p in pigments:
    cpvc_rederived = 1.0 / (1.0 + p["oa_g_per_100g"] * p["rho_p"] / (100.0 * RHO_OIL))
    match = abs(round(cpvc_rederived, 4) - p["cpvc"]) < 1e-12
    daniel_rows.append({"pigment": p["pigment"], "cpvc_receipt": p["cpvc"],
                        "cpvc_rederived_4dp": round(cpvc_rederived, 4), "match": match})
daniel_parity = sum(1 for r in daniel_rows if r["match"])
ka["ka11_daniel_parity_10_of_10"] = daniel_parity == len(pigments)

# KA12 closed form vs explicit volume bookkeeping (independent derivation path)
ka["ka12_volume_bookkeeping_equals_closed_form"] = all(
    abs(porosity_by_volume_bookkeeping(pvc, p["cpvc"]) - porosity(pvc, p["cpvc"])) < TOL
    for p in pigments for pvc in [0.0] + PVC_GRID + [1.0])

battery_pass = all(ka.values())

# ----- consequence ladder ----------------------------------------------------
ladder = []
for p in pigments:
    rows = []
    for pvc in PVC_GRID:
        lam = reduced_pvc(pvc, p["cpvc"])
        pi = porosity(pvc, p["cpvc"])
        rows.append({
            "pvc": pvc, "lambda_reduced_pvc": r6(lam), "porosity_volfrac": r6(pi),
            "regime": "POROUS_ABOVE_CPVC" if pi > 0 else "VOID_FREE_BARRIER",
            "dft_amplification_vs_voidfree": r6(film_volume_factor(pvc, p["cpvc"])),
            "dry_film_density_g_cm3": r6(film_density(pvc, p["cpvc"], p["rho_p"], RHO_B)),
        })
    ladder.append({"pigment": p["pigment"], "cpvc": p["cpvc"],
                   "rho_p_g_cm3": p["rho_p"], "grid": rows})

# case study: iron-oxide-red anticorrosive primer
iox = next(p for p in pigments if p["pigment"] == "iron_oxide_red")
cs = {}
for tag, pvc in [("barrier_pvc_035", 0.35), ("overshoot_pvc_050", 0.50)]:
    lam = reduced_pvc(pvc, iox["cpvc"])
    pi = porosity(pvc, iox["cpvc"])
    rho_nv = pvc * iox["rho_p"] + (1.0 - pvc) * RHO_B
    cs[tag] = {
        "pvc": pvc, "lambda": r6(lam), "porosity_volfrac": r6(pi),
        "dft_readthrough_error_pct_vs_voidfree": r6(100.0 * (film_volume_factor(pvc, iox["cpvc"]) - 1.0)),
        "voidfree_nv_density_g_cm3": r6(rho_nv),
        "dry_film_density_g_cm3": r6(film_density(pvc, iox["cpvc"], iox["rho_p"], RHO_B)),
    }
case_study = {
    "system": "iron_oxide_red in DGEBA-331 + Ancamide 350A stoichiometric binder",
    "cpvc": iox["cpvc"], "binder_ideal_mix_density_g_cm3": r6(RHO_B),
    "binder_density_convention": "ASTM D2697-consistent ideal-mix nonvolatile density; NOT a cured-network density claim (see amphora-cured-network-density-apriori-refuted)",
    "points": cs,
}

# onset sensitivity: pi(1+eps) = eps/(1+eps), first-order in relative overshoot
onset = []
for eps in [0.01, 0.02, 0.05, 0.10, 0.20]:
    pi_exact = porosity((1.0 + eps) * 0.5, 0.5)
    onset.append({"relative_pvc_overshoot": eps,
                  "porosity_volfrac_exact": r6(pi_exact),
                  "closed_form_eps_over_1_plus_eps": r6(eps / (1.0 + eps)),
                  "match": abs(pi_exact - eps / (1.0 + eps)) < TOL})
onset_ok = all(o["match"] for o in onset)

# ----- GUM LPU + Monte-Carlo on porosity through the OA->CPVC chain ----------
rng = np.random.default_rng(MC_SEED)
lpu_rows = []
for p in pigments:
    pvc_eval = round(1.2 * p["cpvc"], 6)          # smooth porous region, LAMBDA=1.2
    k = p["rho_p"] / (100.0 * RHO_OIL)
    oa = p["oa_g_per_100g"]
    u_oa = OA_DECLARED_REL_HALFWIDTH * oa / np.sqrt(3.0)    # rectangular
    dcpvc_doa = -k * p["cpvc"] ** 2
    dpi_dcpvc = -1.0 / pvc_eval
    u_pi_lpu = abs(dpi_dcpvc * dcpvc_doa) * u_oa
    oa_mc = rng.uniform(oa * (1 - OA_DECLARED_REL_HALFWIDTH),
                        oa * (1 + OA_DECLARED_REL_HALFWIDTH), MC_N)
    cpvc_mc = 1.0 / (1.0 + oa_mc * k)
    pi_mc = 1.0 - cpvc_mc / pvc_eval              # smooth branch by construction
    u_pi_mc = float(np.std(pi_mc, ddof=1))
    ratio = u_pi_lpu / u_pi_mc
    lpu_rows.append({
        "pigment": p["pigment"], "pvc_eval_lambda_1p2": pvc_eval,
        "porosity_point": r6(porosity(pvc_eval, p["cpvc"])),
        "u_porosity_lpu": r6(u_pi_lpu), "u_porosity_mc": r6(u_pi_mc),
        "lpu_over_mc_ratio": r6(ratio), "lpu_within_10pct_of_mc": bool(0.9 < ratio < 1.1),
    })
lpu_all_ok = all(r["lpu_within_10pct_of_mc"] for r in lpu_rows)

# ----- diagnostic ------------------------------------------------------------
diag = {
    "schema": "amphora.formulation-arithmetic.reduced-pvc-porosity-diagnostic.v1",
    "authority": "AUDIT_ONLY",
    "module": "amphora-formulation-arithmetic",
    "axis": "theory (option B): Bierwagen reduced-PVC + above-CPVC porosity arithmetic",
    "theory_reference": [
        "Asbeck & Van Loo 1949, Ind. Eng. Chem. 41(7) 1470-1475, DOI 10.1021/ie50475a042",
        "Bierwagen & Hay 1975, Prog. Org. Coat. 3(4) 281-303, DOI 10.1016/0300-9440(75)80047-4",
        "Patton 1979, Paint Flow and Pigment Dispersion, 2nd ed., Wiley, ISBN 0-471-03272-7",
    ],
    "fitted_parameters": 0,
    "declared_application_parameter": {
        "oa_rel_halfwidth_rectangular": OA_DECLARED_REL_HALFWIDTH,
        "note": "declared supplier-spread band on D281 oil absorption for the uncertainty chain; a declared input like prior receipts' metering/DFT bands, not fitted and not a validated supplier statistic.",
    },
    "inputs_provenance": {
        "ingredient_diagnostic": str(ING_DIAG.relative_to(ROOT)),
        "ingredient_diagnostic_sha256": sha(ING_DIAG),
        "ingredient_receipt_sha256": sha(ING_RECEIPT),
        "facts_json": str(FACTS.relative_to(ROOT)),
        "facts_json_sha256": sha(FACTS),
        "rho_oil_g_per_mL": RHO_OIL,
        "binder": {
            "resin": "resin.dgeba_331 (rho 1.16 g/mL, EEW 187)",
            "hardener": "hardener.ancamide_350a (rho 0.97 g/mL, AHEW 100)",
            "stoich_phr": r6(phr),
            "ideal_mix_density_g_cm3": r6(RHO_B),
        },
    },
    "known_answer_battery": ka,
    "known_answer_battery_pass": battery_pass,
    "daniel_parity": {"rows": daniel_rows, "n_match": daniel_parity,
                      "non_circularity_note": "same Daniel formula as the signed ingredient receipt: provenance parity, NOT independent validation of CPVC"},
    "onset_sensitivity": {"rows": onset, "closed_form_verified": onset_ok,
                          "statement": "porosity onset above CPVC is first-order in relative PVC overshoot: pi = eps/(1+eps); +5% PVC error at CPVC -> 4.76 vol% voids"},
    "reduced_pvc_ladder": ladder,
    "case_study": case_study,
    "lpu_vs_mc": {"mc_seed": MC_SEED, "mc_n": MC_N, "rows": lpu_rows,
                  "lpu_validated_by_mc_all_outputs": lpu_all_ok},
    "lpu_validated_by_mc_all_outputs": lpu_all_ok,
    "acceptance": {
        "known_answer_battery_pass": battery_pass,
        "daniel_parity_10_of_10": daniel_parity == 10,
        "onset_closed_form_verified": onset_ok,
        "lpu_validated_by_mc_all_outputs": lpu_all_ok,
    },
    "verdict": ("REDUCED_PVC_POROSITY_ENGINE_READY_AUDIT_ONLY"
                if battery_pass and lpu_all_ok and onset_ok
                else "BATTERY_OR_LPU_FAILED"),
    "finding": (
        "For the 10 in-tree Daniel-CPVC pigments (CPVC 0.4183-0.6365) the reduced-PVC arithmetic is exact and "
        "zero-parameter: below CPVC porosity is identically 0 (consistent with the barrier module's void-free "
        "Fickian assumption), and above CPVC porosity onsets FIRST-ORDER in relative PVC overshoot "
        "(pi = eps/(1+eps): a +5% PVC error at CPVC already creates 4.76 vol% air voids), so CPVC is a cliff, "
        "not a soft optimum. Above CPVC the module's void-free coverage/DFT arithmetic mis-reads film build by "
        "exactly LAMBDA and dry-film density by exactly 1/LAMBDA: an iron-oxide-red epoxy-polyamide primer "
        "formulated at PVC 0.50 (CPVC 0.4183, LAMBDA 1.195) delivers +19.5% DFT and -16.3% dry-film density "
        "versus the void-free arithmetic. Porosity uncertainty inherited from a declared +/-10% oil-absorption "
        "band is u(pi) ~= 0.02-0.05 at LAMBDA 1.2 (GUM LPU validated by 400k-draw MC on all 10 pigments), "
        "comparable to the porosity created by a 5% PVC overshoot -- so near CPVC, OA data quality and PVC "
        "metering discipline are co-equal load-bearing controls."),
    "closes": [
        "adds reduced-PVC (LAMBDA), above-CPVC porosity, DFT amplification, and dry-film density to the dimensioned arithmetic surface",
        "quantifies the porosity cliff at CPVC (first-order in PVC overshoot) and the exact above-CPVC misread of the coverage-spreading DFT arithmetic",
        "carries the GUM+MC uncertainty chain from D281 oil absorption through Daniel CPVC onto porosity",
    ],
    "does_not_close": [
        "not a measured-porosity validation (no mercury-porosimetry or gas-permeation dataset in tree); geometric idealization assumes CPVC-invariant pigment packing above CPVC",
        "binder density is the ideal-mix nonvolatile convention, not a cured-network density claim (see amphora-cured-network-density-apriori-refuted)",
        "does not modify the live Rust engine (still MASS_ONLY), any locked dataset, the signed Phase-0 KPI, or the 66/11 manifest",
    ],
    "connects_to": [
        "amphora-ingredient-library-oil-absorption-cpvc (Daniel CPVC inputs, 4b127f2d...)",
        "amphora-formulation-arithmetic coverage-spreading-v1 (void-free WFT/DFT arithmetic this receipt bounds, ba579323...)",
        "amphora-barrier-* (below-CPVC void-free premise of Fickian/tortuosity receipts)",
        "amphora-zinc-galvanic-percolation (zinc-rich primers deliberately formulated above CPVC for particle contact)",
    ],
}

txt = json.dumps(diag, indent=2, sort_keys=True)
OUT.write_text(txt)
print("WROTE", OUT)
print("sha256", hashlib.sha256(txt.encode()).hexdigest())
print("battery_pass", battery_pass, "daniel_parity", daniel_parity, "lpu_all_ok", lpu_all_ok)
print("verdict", diag["verdict"])
