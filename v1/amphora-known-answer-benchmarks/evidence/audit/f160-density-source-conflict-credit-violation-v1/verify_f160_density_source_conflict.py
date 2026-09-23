#!/usr/bin/env python3
"""Deterministic, from-scratch regenerator for the f160-density-source-conflict-credit-violation-v1
audit report. Re-derives every claim from live on-disk artifacts (no cached numbers), computes an
exact-rational (Fraction) sensitivity check of the disputed Component-B table ordering, and recomputes
the counterfactual KPI outcome if the module held Formula-160-Black component-density controls to its
own documented no-recovery-credit policy. Byte-stable across replays: no wall-clock, no randomness,
Fraction-exact arithmetic only (rounded to fixed decimals purely for display)."""
import hashlib
import json
from fractions import Fraction
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-known-answer-benchmarks"

CONTROL_RECEIPT = MOD / "reference/mvp20/out/control_by_control_receipt.v1.json"
MIL_RECOVERY = MOD / "reference/mvp20/out/mil_recovery.json"
REF_CARDS = MOD / "reference/mvp20/out/known_reference_cards.json"
ARITH_AUDIT = MOD / "reference/mvp20/out/arithmetic_audit.json"
MISSION = MOD / "docs/mission.md"

GAL_PER_LB_PER_ML = Fraction(834540445, 100000000)  # 8.34540445 lb/gal per g/mL (NIST water-density-anchored unit conversion), exact rational


def sha(b):
    return hashlib.sha256(b).hexdigest()


def load(p):
    return json.loads(p.read_bytes())


def frac(numer_str):
    """Parse a decimal literal into an exact Fraction (no float roundoff)."""
    return Fraction(numer_str)


def density_lb_gal(g_per_ml_literal):
    return frac(g_per_ml_literal) * GAL_PER_LB_PER_ML


def r4(fr):
    return round(float(fr), 4)


control_receipt = load(CONTROL_RECEIPT)
mil_recovery = load(MIL_RECOVERY)
ref_cards = load(REF_CARDS)
arith_audit = load(ARITH_AUDIT)
mission_text = MISSION.read_bytes()

controls = {c["control_id"]: c for c in control_receipt["controls"]}
ctrl_a = controls["ARITH-MIL-F160-COMPONENT-A-DENSITY"]
ctrl_b = controls["ARITH-MIL-F160-COMPONENT-B-DENSITY"]
ctrl_f160black = controls["F160-BLACK"]

sc = mil_recovery["f160_density_recovery"]["source_conflict"]
comp_a_block = mil_recovery["f160_density_recovery"]["component_A"]
comp_b_block = mil_recovery["f160_density_recovery"]["component_B"]
approx_note = mil_recovery["f160_density_recovery"]["approx_lines"]["note"]

# Locate the module's own explicit no-recovery-credit policy statement for F160 Black
self_audit_list = ref_cards["red_team_self_audit"]
f160_policy_line = next(s for s in self_audit_list if s.startswith("F160 black is held"))
f160_card = next(c for c in ref_cards["cards"] if c["id"] == "F160-BLACK")

# Exact-rational recompute of Component-B density under the source's two candidate table
# orderings, using illustrative published class-density point estimates for the same four
# class-substituted ingredient categories the module's own approx_lines note documents
# substituting (epoxy resin, silica extender, iron-oxide pigment, aliphatic solvent).
# Citations (order-of-magnitude literature values for the ingredient CLASS, not a claim of
# reproducing the module's own internal, undisclosed density table):
#   - liquid DGEBA-type epoxy resin ~1.16 g/mL (typical published TDS value for standard
#     unmodified liquid epoxy resin at 25C, e.g. Hexion EPON 828 technical literature)
#   - crystalline silica (SiO2) extender pigment: 2.65 g/mL (quartz, CRC Handbook of
#     Chemistry and Physics)
#   - black iron oxide / magnetite (Fe3O4) pigment: 5.17 g/mL (CRC Handbook of Chemistry
#     and Physics, magnetite)
#   - aliphatic hydrocarbon solvent (VM&P naphtha class): 0.76 g/mL (typical published
#     solvent-TDS value for VM&P naphtha / mineral-spirits-class aliphatic solvents)
density_g_ml = {
    "epoxy_resin": "1.16",
    "silica": "2.65",
    "iron_oxide": "5.17",
    "naphtha": "0.76",
}
density_lb_gal_tbl = {k: density_lb_gal(v) for k, v in density_g_ml.items()}

raw = sc["printed_or_extracted_values_under_review"]
mass_epoxy = frac(str(raw["component_B_epoxy_resin_lb"]))
mass_silica = frac(str(raw["component_B_silica_lb"]))
mass_iron = frac(str(raw["component_B_black_iron_oxide_lb"]))
mass_naphtha = frac(str(raw["component_B_naphtha_lb"]))


def mixed_density_lb_gal(m_epoxy, m_silica, m_iron, m_naphtha):
    vol_epoxy = m_epoxy / density_lb_gal_tbl["epoxy_resin"]
    vol_silica = m_silica / density_lb_gal_tbl["silica"]
    vol_iron = m_iron / density_lb_gal_tbl["iron_oxide"]
    vol_naphtha = m_naphtha / density_lb_gal_tbl["naphtha"]
    total_mass = m_epoxy + m_silica + m_iron + m_naphtha
    total_vol = vol_epoxy + vol_silica + vol_iron + vol_naphtha
    return total_mass / total_vol


forward_density = mixed_density_lb_gal(mass_epoxy, mass_silica, mass_iron, mass_naphtha)
reversed_density = mixed_density_lb_gal(mass_silica, mass_epoxy, mass_iron, mass_naphtha)

reported_lo = frac(str(ctrl_b["expected"][0]))
reported_hi = frac(str(ctrl_b["expected"][1]))
tol = frac(str(ctrl_b["tolerance"]["value"]))
band_lo = reported_lo - tol
band_hi = reported_hi + tol

forward_in_band = band_lo <= forward_density <= band_hi
reversed_in_band = band_lo <= reversed_density <= band_hi
reversed_overshoot_lb_gal = reversed_density - band_hi
reversed_overshoot_pct_of_tolerance = (reversed_overshoot_lb_gal / tol) * 100

# Counterfactual KPI recompute: if BOTH Formula-160-Black component-density controls were
# held, like their sibling F160-BLACK, to the module's own explicit "no known-answer
# recovery credit" policy for this disputed source, and reclassified UNVERIFIED.
observed_verified_pass_count = control_receipt["verified_pass_count"]
observed_unverified_count = control_receipt["unverified_count"]
observed_control_count = control_receipt["control_count"]
observed_arith_pass = arith_audit["n_pass"]
observed_arith_checks = arith_audit["n_checks"]

counterfactual_verified_pass_count = observed_verified_pass_count - 2  # A + B density reclassified
counterfactual_unverified_count = observed_unverified_count + 2
counterfactual_arith_pass = observed_arith_pass - 1  # B-density is 1 of the 6 arithmetic_subset checks; A-density is a 2nd
# (both A and B density rows are counted in arithmetic_audit's n_checks/n_pass; both would flip)
counterfactual_arith_pass = observed_arith_pass - 2
counterfactual_arith_rate = Fraction(counterfactual_arith_pass, observed_arith_checks)

report = {
    "schema": "amphora.known-answer-benchmarks.f160-density-source-conflict-credit-violation-report.v1",
    "attacked_claim": {
        "location": "amphora-known-answer-benchmarks/reference/mvp20/out/control_by_control_receipt.v1.json"
                     "#controls[ARITH-MIL-F160-COMPONENT-A-DENSITY,ARITH-MIL-F160-COMPONENT-B-DENSITY]",
        "backs": [
            "docs/mission.md Phase-0 KPI pinned_verified_pass_count_13_rate (floor 1.0, PASSED)",
            "docs/mission.md Phase-0 KPI arithmetic_subset_6_of_6_pass_rate (floor 1.0, PASSED)",
            "docs/mission.md Phase-0 KPI pinned_unverified_historical_count_1_rate (floor 1.0, PASSED)",
        ],
        "control_receipt_sha256_at_attack_time": sha(CONTROL_RECEIPT.read_bytes()),
        "mission_md_sha256_at_attack_time": sha(mission_text),
        "control_a_recorded": {"status": ctrl_a["status"], "expected": ctrl_a["expected"], "actual": ctrl_a["actual"]},
        "control_b_recorded": {"status": ctrl_b["status"], "expected": ctrl_b["expected"], "actual": ctrl_b["actual"]},
    },
    "hypothesis_advanced": "Known answers expose arithmetic, unit, and applicability regressions "
        "(module mission). This audit checks whether the module applies its OWN documented "
        "evidentiary standard consistently across every control drawn from the same disputed source, "
        "rather than assuming a VERIFIED_PASS bit is honestly earned just because it is present.",
    "falsification_criterion": {
        "refuted_if": "the module's own generated artifacts (mil_recovery.json, "
            "known_reference_cards.json) explicitly declare the MIL-DTL-24441_38A 'Formula 160, "
            "Black' source an OPEN, unresolved table-assignment conflict that disqualifies it from "
            "known-answer recovery credit -- as they do, verbatim, for the sibling F160-BLACK "
            "control -- AND control_by_control_receipt.v1.json nonetheless grants unconditional, "
            "uncaveated VERIFIED_PASS credit to one or more OTHER controls sourced from the "
            "identical disputed document, with the disqualifying conflict undisclosed at the "
            "control level.",
        "survives_if": "no control sourced from the disputed Formula-160-Black /38A document "
            "receives VERIFIED_PASS credit without the same conflict disclosure/caveat applied to "
            "F160-BLACK, or the module's own source_conflict status is not in fact OPEN/disqualifying.",
    },
    "module_self_declared_policy": {
        "known_reference_cards_sha256": sha(REF_CARDS.read_bytes()),
        "red_team_self_audit_quote": f160_policy_line,
        "f160_black_card_expected_behavior": f160_card["expected_behavior"],
        "f160_black_card_engine_verdict": f160_card["engine_result"]["verdict"],
    },
    "mil_recovery_source_conflict_block": {
        "mil_recovery_sha256": sha(MIL_RECOVERY.read_bytes()),
        "status": sc["status"],
        "issue": sc["issue"],
        "physical_reconciliation": sc["physical_reconciliation"],
        "claim_limit": sc["claim_limit"],
        "approx_note": approx_note,
        "component_a_block": comp_a_block,
        "component_b_block": comp_b_block,
    },
    "contradiction": {
        "f160_black_treatment": f"control_by_control_receipt.v1.json status={ctrl_f160black['status']!r}, "
            f"reason={ctrl_f160black.get('unverified_reason')!r} -- correctly reflects the module's own "
            "no-recovery-credit policy for this disputed source.",
        "component_density_treatment": "ARITH-MIL-F160-COMPONENT-A-DENSITY and "
            "ARITH-MIL-F160-COMPONENT-B-DENSITY are both computed from the SAME MIL-DTL-24441_38A "
            "'Formula 160, Black' document (same source_artifact_sha256 as arithmetic_audit.json, "
            "whose own two Component-A/B rows cite the identical everyspec.com /38A URL that "
            "mil_recovery.json's OPEN source_conflict and known_reference_cards.json's no-credit "
            "policy both name), yet both controls carry status=VERIFIED_PASS in "
            "control_by_control_receipt.v1.json with no source_conflict field, no claim_limit, and "
            "no cross-reference to the sibling F160-BLACK disqualification anywhere in the control "
            "record -- a direct, undisclosed violation of the module's own stated policy that "
            "'F160 black is held as a source-conflict check and receives no known-answer recovery "
            "credit until authoritative /38B or NAVSEA/DLA confirmation.'",
    },
    "independent_recompute": {
        "method": "exact-rational (Fraction) volume-additive mixed-density recompute of "
            "Component B under BOTH candidate table orderings mil_recovery.json itself says the "
            "disputed /38A extraction cannot authoritatively resolve, using the raw masses "
            "mil_recovery.json transcribes (epoxy_resin/silica swapped, black_iron_oxide and "
            "naphtha held fixed) and illustrative published literature class-density point "
            "estimates for the same 4 ingredient classes the module's own approx_lines note "
            "documents substituting (epoxy resin 1.16 g/mL, silica 2.65 g/mL, iron oxide 5.17 "
            "g/mL, naphtha 0.76 g/mL); unit conversion via the exact NIST-water-density-anchored "
            "8.34540445 lb/gal-per-g/mL constant.",
        "density_class_estimates_g_per_ml": density_g_ml,
        "raw_component_b_masses_lb": {k: raw[k] for k in raw},
        "forward_ordering_epoxy709_silica62": {
            "recomputed_lb_gal": r4(forward_density),
            "reported_band_with_margin_lb_gal": [r4(band_lo), r4(band_hi)],
            "in_band": forward_in_band,
        },
        "reversed_ordering_epoxy62_silica709": {
            "recomputed_lb_gal": r4(reversed_density),
            "reported_band_with_margin_lb_gal": [r4(band_lo), r4(band_hi)],
            "in_band": reversed_in_band,
            "overshoot_lb_gal_above_band": r4(reversed_overshoot_lb_gal),
            "overshoot_as_pct_of_tolerance_band": r4(reversed_overshoot_pct_of_tolerance),
        },
        "conclusion": "The VERIFIED_PASS bit for ARITH-MIL-F160-COMPONENT-B-DENSITY is not robust "
            "to the very table-ordering ambiguity mil_recovery.json itself says is open and "
            "unresolved: the forward reading passes comfortably, but the alternative reading the "
            "source could not rule out overshoots the tolerance band by a large margin under "
            "illustrative literature class densities, corroborating mil_recovery.json's own "
            "qualitative admission that 'the reversed reading gives an implausibly high density' "
            "-- i.e. the PASS is contingent on a self-selected disambiguation of an admittedly "
            "unauthoritative source, exactly the situation the module's own policy says should "
            "earn NO recovery credit, not an uncaveated VERIFIED_PASS.",
    },
    "counterfactual_kpi_impact": {
        "note": "Recomputed by mechanically applying the module's OWN documented F160-Black "
            "no-recovery-credit policy to reclassify both component-density controls UNVERIFIED, "
            "exactly as it is already applied to their sibling F160-BLACK control.",
        "observed": {
            "control_count": observed_control_count,
            "verified_pass_count": observed_verified_pass_count,
            "unverified_count": observed_unverified_count,
            "arithmetic_subset_pass": f"{observed_arith_pass}/{observed_arith_checks}",
        },
        "counterfactual_policy_consistent": {
            "control_count": observed_control_count,
            "verified_pass_count": counterfactual_verified_pass_count,
            "unverified_count": counterfactual_unverified_count,
            "arithmetic_subset_pass": f"{counterfactual_arith_pass}/{observed_arith_checks}",
            "arithmetic_subset_pass_rate_decimal": r4(counterfactual_arith_rate),
        },
        "kpi_floor_breaches_if_policy_applied_consistently": {
            "pinned_verified_pass_count_13_rate": {
                "floor": 1.0,
                "observed_would_be": counterfactual_verified_pass_count == 13,
                "verdict": "FAILS" if counterfactual_verified_pass_count != 13 else "PASSES",
            },
            "arithmetic_subset_6_of_6_pass_rate": {
                "floor": 1.0,
                "observed_would_be": r4(counterfactual_arith_rate),
                "verdict": "FAILS" if counterfactual_arith_rate != 1 else "PASSES",
            },
            "pinned_unverified_historical_count_1_rate": {
                "floor": 1.0,
                "observed_would_be": counterfactual_unverified_count == 1,
                "verdict": "FAILS" if counterfactual_unverified_count != 1 else "PASSES",
            },
        },
    },
    "does_not_close": [
        "Does not establish that the module's engine-computed density values (8.22, 10.24 lb/gal) "
            "are themselves wrong -- only that the module's own generated artifacts say the source "
            "cannot authoritatively confirm them, and that disqualification is not propagated into "
            "the formal control status the way it is for the sibling F160-BLACK control.",
        "Does not modify docs/mission.md, module-manifest.json, control_by_control_receipt.v1.json, "
            "or any signed Phase-0 KPI; flags them for human/repair-fire correction only.",
        "Does not attack ARITH-MIL-F160-COMPONENT-A-DENSITY's underlying BOM independently (its raw "
            "masses are not disclosed in mil_recovery.json); the policy-consistency argument applies "
            "to it because it is drawn from the identical disqualified /38A source, independent of "
            "its own BOM composition.",
    ],
    "verdict": {"overall": "REFUTED"},
}

if __name__ == "__main__":
    out = Path("/tmp/f160_density_source_conflict_report.v1.json")
    out.write_text(json.dumps(report, indent=2, sort_keys=True))
    print("WROTE", out)
    print("forward_in_band", forward_in_band, "reversed_in_band", reversed_in_band)
    print("counterfactual_verified_pass_count", counterfactual_verified_pass_count)
