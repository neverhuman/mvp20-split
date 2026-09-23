#!/usr/bin/env python3
"""X-COV-CPVC: cross-check amphora-formulation-arithmetic's coverage-spreading-v1
WFT/DFT/TC engine (signed 2026-07-29, two-replay aed83340...) against its OWN
sibling receipt reduced-pvc-porosity-v1 (signed 2026-07-31, two-replay
a98c7281...), which independently established that above the Bierwagen
Critical Pigment Volume Concentration (CPVC) a real dry film's volume is
amplified by LAMBDA = PVC/CPVC relative to the void-free packing assumption.

coverage-spreading-v1's wet_film_thickness_um() / theoretical_coverage_m2_per_L()
formulas (WFT = DFT/VS_frac, KA4 closure: WFT*VS_frac == DFT exactly) assume
void-free close packing -- they have NO PVC/CPVC awareness at all (confirmed:
zero of coverage-spreading-v1's 9 known-answer-battery cases and zero fields in
its applied_spec / does_not_close touch PVC, CPVC, or porosity). reduced-pvc-
porosity-v1's own case study already computed the consequence for a real,
sibling-receipt-cited in-domain marine anti-corrosion primer (iron-oxide-red at
PVC 0.50, CPVC 0.4183) but that finding was never propagated back into
coverage-spreading-v1 as a repair, supersession, or disclosed scope boundary --
the coverage-spreading-v1 receipt still reads unconditionally "ENGINE_READY".

This script independently reimplements BOTH engines from their own published
source (verbatim copies, not trusted blindly), reproduces both receipts' point
estimates bit-exact as a provenance guard, then composes them to ask: if
coverage-spreading-v1's own WFT prescription is applied to an in-domain porous
(PVC>=CPVC) marine primer at its own declared target DFT, does the ACTUAL dry
film thickness delivered match the target within the receipt's own calibrated
uncertainty?

Prior fires on this claim lineage:
  T-05 (2026-08-05): EquivalentBalanceV1 host-fact authority bypass -- REFUTED
    (different arithmetic surface: stoichiometric equivalents, not coverage).
  CF-ARITH (2026-08-10): candidate BOM VOC/volume-solids re-derivation,
    xylene-density positive control -- SURVIVED (self-referential fixture).
  W-T-ARITH (2026-08-13): dimensioned VOC formula vs EPA Method 24 named
    baseline, waterborne positive control -- REFUTED (water/exempt-solvent
    exclusion gap). W-T-ARITH's own R8 followup flagged (but did not test)
    that the module's symmetric GUM/MC intervals have no CPVC/porosity
    awareness either.
This fire is the first to actually COMPOSE coverage-spreading-v1 with its own
sibling reduced-pvc-porosity-v1 finding and quantify the film-build error on a
concrete in-domain case -- a distinct attack surface from all three prior
fires (none of them touched coverage/WFT arithmetic or the CPVC axis together).
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-formulation-arithmetic"
COV_DIAG = MOD / "evidence/audit/coverage-spreading-v1/diagnostic.canonical.json"
RPVC_DIAG = MOD / "evidence/audit/reduced-pvc-porosity-v1/diagnostic.canonical.json"
ING_DIAG = ROOT / "amphora-ingredient-library/evidence/audit/oil-absorption-cpvc-v1/diagnostic.canonical.json"
FACTS = ROOT / "amphora-ingredient-library/reference/mvp20/data/facts.json"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def fsha(p: Path) -> str:
    return sha(p.read_bytes())


def r(x, nd=10):
    v = round(float(x), nd)
    return 0.0 if v == 0.0 else v


# ----------------------------------------------------------------------------
# 1. Reload both sibling receipts, read-only, unmodified.
# ----------------------------------------------------------------------------
cov = json.loads(COV_DIAG.read_text())
rpvc = json.loads(RPVC_DIAG.read_text())
ing = json.loads(ING_DIAG.read_text())
facts = json.loads(FACTS.read_text())["entries"]

# ----------------------------------------------------------------------------
# 2. Independent reimplementation of coverage-spreading-v1's engine, copied
#    verbatim from run_coverage_spreading.py (not altered).
# ----------------------------------------------------------------------------
def theoretical_coverage_m2_per_L(vs_frac, dft_um):
    return 1000.0 * vs_frac / dft_um


def wet_film_thickness_um(dft_um, vs_frac):
    return dft_um / vs_frac


COV_COMPONENTS = [
    ("dgeba_der331",                100.0, 1.16, 1.0),
    ("teta_hardener",                13.0, 0.982, 1.0),
    ("iron_oxide_red",               55.0, 5.00, 1.0),
    ("zinc_phosphate_anticorrosive", 30.0, 3.30, 1.0),
    ("barytes_extender",             40.0, 4.45, 1.0),
    ("talc_extender",                20.0, 2.80, 1.0),
    ("mica_barrier",                 15.0, 2.85, 1.0),
    ("xylene_solvent",               45.0, 0.87, 0.0),
    ("n_butanol_solvent",            15.0, 0.81, 0.0),
]


def volume_solids(comps):
    V_total = V_solid = 0.0
    for _cid, mass, rho, nonvol in comps:
        v = mass / rho
        V_total += v
        if nonvol > 0.0:
            V_solid += v * nonvol
    return V_solid / V_total


VS = volume_solids(COV_COMPONENTS)
DFT_TARGET_UM = 127.0  # coverage-spreading-v1's own declared applied spec (5 mil)
WFT = wet_film_thickness_um(DFT_TARGET_UM, VS)
TC = theoretical_coverage_m2_per_L(VS, DFT_TARGET_UM)

reproduces_coverage_receipt = {
    "volume_solids_frac": {"reimpl": r(VS), "signed": cov["point_estimates"]["volume_solids_frac"],
                            "match": abs(VS - cov["point_estimates"]["volume_solids_frac"]) < 1e-9},
    "wet_film_thickness_um": {"reimpl": r(WFT), "signed": cov["point_estimates"]["wet_film_thickness_um"],
                               "match": abs(WFT - cov["point_estimates"]["wet_film_thickness_um"]) < 1e-6},
    "theoretical_coverage_m2_per_L": {"reimpl": r(TC), "signed": cov["point_estimates"]["theoretical_coverage_m2_per_L"],
                                       "match": abs(TC - cov["point_estimates"]["theoretical_coverage_m2_per_L"]) < 1e-9},
}
assert all(v["match"] for v in reproduces_coverage_receipt.values()), "coverage-spreading-v1 reimplementation mismatch"

# KA battery axis coverage check -- confirm zero PVC/CPVC/porosity awareness.
ka_ids = [k["id"] for k in cov["known_answer_battery"]]
ka_mentions_pvc = any("pvc" in k["id"].lower() or "cpvc" in k["id"].lower() for k in cov["known_answer_battery"])
scope_mentions_pvc = any("pvc" in str(x).lower() or "cpvc" in str(x).lower() for x in cov.get("does_not_close", []))

# ----------------------------------------------------------------------------
# 3. Independent reimplementation of reduced-pvc-porosity-v1's engine, copied
#    verbatim from run_reduced_pvc.py (not altered).
# ----------------------------------------------------------------------------
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
    check_domain(pvc, cpvc)
    lam = pvc / cpvc
    return lam if lam > 1.0 else 1.0


def film_density(pvc, cpvc, rho_p, rho_b):
    if rho_p <= 0.0 or rho_b <= 0.0:
        raise ValueError("density must be positive")
    rho_nv = pvc * rho_p + (1.0 - pvc) * rho_b
    return (1.0 - porosity(pvc, cpvc)) * rho_nv


iox_row = next(row for row in ing["checkA_daniel_cpvc"]["per_constant"]
               if row["constant_density"] == "pigment.iron_oxide_red.density")
CPVC = iox_row["cpvc_volume_fraction"]
RHO_P = iox_row["skeletal_density_g_per_cm3"]

rho_a = facts["resin.dgeba_331.density"]["value"]
eew = facts["resin.dgeba_331.eew"]["value"]
rho_h = facts["hardener.ancamide_350a.density"]["value"]
ahew = facts["hardener.ancamide_350a.ahew"]["value"]
phr = 100.0 * ahew / eew
RHO_B = (100.0 + phr) / (100.0 / rho_a + phr / rho_h)

reproduces_rpvc_receipt = {
    "cpvc": {"reimpl": CPVC, "signed": rpvc["case_study"]["cpvc"], "match": CPVC == rpvc["case_study"]["cpvc"]},
    "binder_ideal_mix_density_g_cm3": {"reimpl": r(RHO_B, 6), "signed": rpvc["case_study"]["binder_ideal_mix_density_g_cm3"],
                                        "match": abs(RHO_B - rpvc["case_study"]["binder_ideal_mix_density_g_cm3"]) < 1e-6},
}
overshoot = rpvc["case_study"]["points"]["overshoot_pvc_050"]
lam_reimpl = reduced_pvc(0.50, CPVC)
reproduces_rpvc_receipt["lambda_pvc050"] = {
    "reimpl": r(lam_reimpl, 6), "signed": overshoot["lambda"], "match": abs(lam_reimpl - overshoot["lambda"]) < 1e-6,
}
assert all(v["match"] for v in reproduces_rpvc_receipt.values()), "reduced-pvc-porosity-v1 reimplementation mismatch"

# ----------------------------------------------------------------------------
# 4. THE ATTACK. Compose: apply coverage-spreading-v1's own signed WFT
#    prescription to the in-domain porous system reduced-pvc-porosity-v1
#    itself names ("iron_oxide_red in DGEBA-331 + Ancamide 350A stoichiometric
#    binder" at PVC 0.50, CPVC 0.4183) at coverage-spreading-v1's own declared
#    target DFT (127 um). LAMBDA acts on the nonvolatile-to-dry-film-volume
#    step and is independent of solvent/VS_frac dilution (reduced-pvc-porosity
#    derivation sec: "porous-regime DFT = LAMBDA * void-free DFT"), so it
#    applies directly to coverage-spreading-v1's own DFT_target/WFT pair.
# ----------------------------------------------------------------------------
PVC_OVERSHOOT = 0.50
# film_volume_factor (not the raw reduced_pvc ratio) is the physical dry-film
# amplification factor: it clamps to 1.0 below CPVC (binder fully fills the
# interstitial space, no voids -- see reduced-pvc-porosity-v1 sec on
# film_volume_factor()), whereas raw PVC/CPVC can be <1 there with no physical
# amplification meaning.
LAMBDA = film_volume_factor(PVC_OVERSHOOT, CPVC)
lambda_raw_ratio = reduced_pvc(PVC_OVERSHOOT, CPVC)
dft_actual_um = LAMBDA * DFT_TARGET_UM
dft_overshoot_pct = 100.0 * (dft_actual_um / DFT_TARGET_UM - 1.0)
rho_dry_voidfree = cov["point_estimates"]["dry_film_density_g_cm3"]
# areal-mass invariance (mass/area is independent of porosity): rho_actual = rho_voidfree / LAMBDA
rho_dry_actual = rho_dry_voidfree / LAMBDA
rho_dry_error_pct = 100.0 * (rho_dry_actual / rho_dry_voidfree - 1.0)

# Positive/negative control: a BELOW-CPVC formulation (barrier_pvc_035, PVC
# 0.35 < CPVC 0.4183) must show LAMBDA clamped to 1 and zero divergence --
# confirms the bias is specifically the CPVC/porosity effect, not a bug in
# this reimplementation.
barrier = rpvc["case_study"]["points"]["barrier_pvc_035"]
lam_control = film_volume_factor(0.35, CPVC)
lam_control_raw_ratio = reduced_pvc(0.35, CPVC)
dft_actual_control = lam_control * DFT_TARGET_UM
control_divergence_pct = 100.0 * (dft_actual_control / DFT_TARGET_UM - 1.0)

# Calibrated-uncertainty comparison: how many multiples of coverage-spreading-
# v1's own signed 95% MC interval half-width (both variants) is the LAMBDA bias.
wft_at_nominal = cov["results"]["wet_film_thickness_um"]["at_nominal_dft"]
wft_as_applied = cov["results"]["wet_film_thickness_um"]["as_applied_with_dft_control"]
bias_um = dft_actual_um - DFT_TARGET_UM
ratio_vs_nominal_halfwidth = abs(bias_um) / wft_at_nominal["mc_ci95_halfwidth"]
ratio_vs_applied_halfwidth = abs(bias_um) / wft_as_applied["mc_ci95_halfwidth"]

detected = bool(dft_overshoot_pct > 5.0)  # >5% is far outside any formulation-arithmetic identity tolerance
control_clean = bool(abs(control_divergence_pct) < 1e-9)

diagnostic = {
    "schema": "amphora.formulation-arithmetic.coverage-cpvc-crosscheck.v1",
    "run_type": "X-COV-CPVC_SIBLING_RECEIPT_COMPOSITION_AUDIT",
    "target_module": "amphora-formulation-arithmetic",
    "campaign_item_id": "X-COV-CPVC",
    "claim_under_attack": {
        "receipt_path": "amphora-formulation-arithmetic/evidence/audit/coverage-spreading-v1/coverage-spreading-receipt.v1.dsse.json",
        "claim_text": "COVERAGE_SPREADING_ENGINE_READY__KNOWN_ANSWER_BATTERY_PASS__1604_ANCHOR_EXACT -- "
                      "the WFT/TC/PC/dry-film-areal-mass engine, with its GUM LPU + Monte Carlo calibrated "
                      "intervals, correctly and completely converts a formulated recipe's volume solids + "
                      "target DFT into the applied-film arithmetic for the module's declared applicability "
                      "domain (solvent-borne two-component epoxy-amine marine-coating R&D, which the module's "
                      "own sibling receipts treat as including anti-corrosion pigmented / inhibitive primers).",
    },
    "sibling_receipt_used_as_baseline": {
        "path": "amphora-formulation-arithmetic/evidence/audit/reduced-pvc-porosity-v1/reduced-pvc-porosity-receipt.v1.dsse.json",
        "signed_date": "2026-07-31",
        "two_replay_sha256": "a98c7281...",
        "finding_reused": "Above CPVC, real dry-film volume is amplified by LAMBDA=PVC/CPVC vs void-free packing "
                           "(Asbeck & Van Loo 1949 DOI 10.1021/ie50475a042; Bierwagen & Hay 1975 "
                           "DOI 10.1016/0300-9440(75)80047-4); case study names iron-oxide-red anticorrosive "
                           "primer at PVC 0.50 (CPVC 0.4183) as the worked in-domain example.",
    },
    "attacked_receipt_signed_date": "2026-07-29",
    "attacked_receipt_two_replay_sha256": "aed83340...",
    "prior_fires_on_this_module": {
        "T-05_2026-08-05": "EquivalentBalanceV1 host-fact authority bypass -- REFUTED (unrelated arithmetic surface)",
        "CF-ARITH_2026-08-10": "candidate BOM VOC/volume-solids re-derivation -- SURVIVED (self-referential fixture)",
        "W-T-ARITH_2026-08-13": "dimensioned VOC vs EPA Method 24 -- REFUTED (water/exempt-solvent exclusion); "
                                 "its R8 followup flagged but did NOT test that the module's symmetric GUM/MC "
                                 "intervals have no CPVC/porosity awareness",
        "gap_this_fire_closes": "no prior fire composed coverage-spreading-v1 with its own sibling reduced-pvc-"
                                 "porosity-v1 finding, nor touched the WFT/TC/coverage arithmetic surface at all",
    },
    "reproduces_coverage_spreading_v1_point_estimates": reproduces_coverage_receipt,
    "reproduces_reduced_pvc_porosity_v1_case_study": reproduces_rpvc_receipt,
    "coverage_spreading_v1_ka_battery_ids": ka_ids,
    "coverage_spreading_v1_ka_battery_has_pvc_cpvc_case": ka_mentions_pvc,
    "coverage_spreading_v1_scope_discloses_pvc_cpvc_boundary": scope_mentions_pvc,
    "composed_case": {
        "system": "iron_oxide_red anticorrosive primer, DGEBA-331 + Ancamide 350A stoichiometric binder "
                   "(same system reduced-pvc-porosity-v1's case_study names; cpvc/binder-density independently "
                   "reproduced above, not merely copied)",
        "cpvc": CPVC,
        "rho_p_g_per_cm3": RHO_P,
        "rho_b_ideal_mix_g_per_cm3": r(RHO_B, 6),
        "pvc_overshoot_case": {
            "pvc": PVC_OVERSHOOT,
            "lambda_film_volume_factor": r(LAMBDA, 6),
            "lambda_raw_pvc_over_cpvc_ratio": r(lambda_raw_ratio, 6),
            "coverage_spreading_v1_signed_wft_um_at_this_dft_target": cov["point_estimates"]["wet_film_thickness_um"],
            "dft_target_um": DFT_TARGET_UM,
            "dft_actual_um_after_lambda_amplification": r(dft_actual_um, 4),
            "dft_overshoot_pct": r(dft_overshoot_pct, 4),
            "dry_film_density_voidfree_g_cm3_signed": rho_dry_voidfree,
            "dry_film_density_actual_g_cm3": r(rho_dry_actual, 6),
            "dry_film_density_error_pct": r(rho_dry_error_pct, 4),
        },
        "pvc_below_cpvc_control_case": {
            "pvc": 0.35,
            "lambda_film_volume_factor": r(lam_control, 6),
            "lambda_raw_pvc_over_cpvc_ratio": r(lam_control_raw_ratio, 6),
            "dft_actual_um": r(dft_actual_control, 4),
            "dft_divergence_pct": r(control_divergence_pct, 9),
            "note": "below-CPVC control: film_volume_factor clamps LAMBDA to 1 exactly (raw PVC/CPVC ratio "
                    "0.8368 has no physical amplification meaning below CPVC -- binder fully fills the "
                    "interstitial space, no voids), so film-build divergence is exactly zero -- confirms the "
                    "+19.5% overshoot above is specifically the CPVC/porosity effect, not a reimplementation bug",
        },
    },
    "calibrated_uncertainty_comparison": {
        "coverage_spreading_v1_wft_at_nominal_dft_mc_ci95_halfwidth_um": wft_at_nominal["mc_ci95_halfwidth"],
        "coverage_spreading_v1_wft_as_applied_with_dft_control_mc_ci95_halfwidth_um": wft_as_applied["mc_ci95_halfwidth"],
        "lambda_bias_um": r(bias_um, 4),
        "bias_as_multiple_of_at_nominal_halfwidth": r(ratio_vs_nominal_halfwidth, 2),
        "bias_as_multiple_of_as_applied_halfwidth": r(ratio_vs_applied_halfwidth, 2),
        "interpretation": "The at_nominal_dft interval is the module's own claim for pure formulation-arithmetic "
                           "precision (excludes operator DFT-control variance): the LAMBDA bias is ~29x that "
                           "interval's half-width. Even against the wider as_applied_with_dft_control interval "
                           "(which folds in an UNRELATED +/-20% operator DFT-control tolerance), the LAMBDA bias "
                           "is still a majority-sized, wholly separate, systematic (unidirectional) effect that "
                           "the module's error budget has no term for at all -- GUM (JCGM 100:2008 sec 3.2.3, "
                           "6.3.1) requires known systematic effects to be corrected before an expanded "
                           "uncertainty is reported as a coverage interval for the measurand; this one is neither "
                           "corrected nor disclosed.",
    },
    "positive_control": {
        "planted_defect": "none needed -- this is a REFUTED verdict with self-evidencing composition of two "
                           "already-signed in-tree receipts; a below-CPVC control case is included anyway for rigor",
        "how_planted": "n/a",
        "detected": detected,
        "evidence": {"dft_overshoot_pct": r(dft_overshoot_pct, 4), "control_divergence_pct": r(control_divergence_pct, 9)},
    },
    "control_clean": control_clean,
    "overall_verdict": "CLAIM_REFUTED",
    "overall_verdict_reasoning": (
        "coverage-spreading-v1's WFT/TC engine (KA4 closure: WFT*VS_frac==DFT exactly) assumes void-free "
        "close packing with zero PVC/CPVC awareness -- confirmed by direct inspection: none of its 9 "
        "known-answer-battery cases and no field in applied_spec/does_not_close reference PVC, CPVC, or "
        "porosity. The module's OWN sibling receipt reduced-pvc-porosity-v1 (signed two days later) already "
        "established that above CPVC a real dry film's volume is amplified by LAMBDA=PVC/CPVC, and named "
        "exactly this iron-oxide-red-primer-at-PVC-0.50 case as its worked in-domain example -- but that "
        "finding was never propagated back into coverage-spreading-v1 as a repair, supersession, or disclosed "
        "scope caveat. Applying coverage-spreading-v1's own signed WFT prescription (190.30 um, unchanged) to "
        "this in-domain porous primer at its own declared 127 um DFT target delivers an actual film build of "
        f"{r(dft_actual_um, 2)} um, a {r(dft_overshoot_pct, 1)}% overshoot -- roughly 29x the receipt's own "
        "at_nominal_dft calibrated 95% interval half-width (0.67% relative) and a wholly unmodeled systematic "
        "effect even against the wider as-applied interval. The below-CPVC control case shows zero divergence "
        "(LAMBDA=1 exactly), confirming the bias is the CPVC/porosity effect specifically, not an artifact of "
        "this reimplementation. The claim 'COVERAGE_SPREADING_ENGINE_READY' as currently signed overclaims: it "
        "is READY only for the (undisclosed) below-CPVC subset of the module's own declared applicability "
        "domain."
    ),
    "proposed_followups": [
        {
            "finding": "coverage-spreading-v1's WFT/TC/PC/areal-mass formulas have no PVC/CPVC term and silently "
                       "mis-predict film build by exactly LAMBDA for any porous (PVC>=CPVC) in-domain formulation.",
            "proposed_repair_criterion": "add an explicit PVC/CPVC-aware branch to the coverage engine (multiply "
                       "void-free DFT by LAMBDA when PVC>=CPVC, matching reduced-pvc-porosity-v1's already-signed "
                       "closed form), add a PVC>=CPVC known-answer case to the battery so the gap cannot silently "
                       "regress, and either disclose the below-CPVC restriction explicitly in does_not_close or "
                       "close the gap before the receipt is cited as covering pigmented anti-corrosion primers.",
        },
    ],
}

HERE = Path(__file__).resolve().parent
out = HERE / (sys.argv[1] if len(sys.argv) > 1 else "diagnostic.canonical.json")
out.write_text(json.dumps(diagnostic, indent=2, sort_keys=True))
print("WROTE", out)
print("dft_overshoot_pct:", r(dft_overshoot_pct, 4))
print("control_divergence_pct:", r(control_divergence_pct, 9))
print("ratio_vs_nominal_halfwidth:", r(ratio_vs_nominal_halfwidth, 2))
print("overall_verdict:", diagnostic["overall_verdict"])
print("sha256:", sha(out.read_bytes()))
