#!/usr/bin/env python3
"""Independent re-derivation attack on ARITH-A221-X70P1-VOLUME-SOLIDS.

The known-answer control_by_control_receipt.v1.json (SHA-256
be537c06a3cc325b4ecd6ee71bd6ed284d570883bb2f123e7c969d574c60d3cc, compile-time
embedded by amphora-assurance-capabilities/src/lib.rs and asserted bit-exact by
known_answer_benchmarks_phase0_kpi.rs, backing the KPI
`arithmetic_subset_6_of_6_pass_rate` in evidence/phase0/benchmark/result.v1.json,
SHA-256 5404f989cdf3ef818a5f05c96c522efe548b8ee89532664ab0e2b2a3b70652c8) records:

    ARITH-A221-X70P1-VOLUME-SOLIDS: expected=42.5, actual=43.7,
    tolerance=ABSOLUTE 2.0 percentage_point, status=VERIFIED_PASS

reference/mvp20/out/arithmetic_audit.json labels 43.7 "recomputed" from the same
Evonik Ancamide 221 EMEA TDS
(https://products.evonik.com/assets/em/ea/Ancamide_221_EMEA_TDS_EN_EN_TDS_PV_52041324_en_GB_EMEA.pdf,
cited by that file itself) that also PUBLISHES the target 42.5% directly.

This script re-derives Mix volume-solids % for the A221-X70P1 anti-corrosive
primer formulation using ONLY numbers transcribed verbatim from that same PDF
(Appendix I formulation table, p.10, and the paired Technical Data table, p.11,
fetched 2026-08-03), using exact rational (fractions.Fraction) arithmetic so the
result is float-free and byte-stable.

Source table values transcribed from the PDF (p.10-11):
  A-component total mass  = 1000.00 g   (DER 671X75 280g + MIBK 80g + Xylene 110g
                             + n-Butanol 30g + Blanc fix Micro 100g + Talc 10MO 100g
                             + Heucophos ZPO 140g + Bayferrox 130M 150g)
  B-component total mass  = 200.00 g    (Ancamide 221-X70 106g + Xylene 59g + Dowanol PM 35g)
  Density Part A          = 1.51 g/mL
  Density Part B          = 0.92 g/mL
  Density Mix (published) = 1.37 g/mL
  Solid content vol% A    = 46.0
  Solid content vol% B    = 31.5
  Solid content vol% Mix (published, = the receipt's "expected") = 42.5
  Solid content wt% A     = 70.0
  Solid content wt% B     = 37.1
  Solid content wt% Mix (published, cross-check only) = 64.5

Two independent recomputations of Mix volume-solids %:
  (1) CORRECT: volume-weighted average, i.e. total solids volume / total mix
      volume, where each component's volume is mass/density. This is the only
      physically valid way to combine two volume-basis percentages from
      components of different density.
  (2) HYPOTHESIZED BUG MECHANISM: mass-fraction-weighted average of the two
      components' volume-solids percentages (a unit-basis conflation: weighting
      a volume-basis quantity by a mass-basis weight is invalid whenever
      density_A != density_B, which holds here: 1.51 vs 0.92).

Also cross-checks the (independently reproducible) weight%-solids number
against the TDS's own published 64.5% mix value as an internal-consistency
sanity gate on the transcribed source numbers.
"""
import hashlib
import json
from fractions import Fraction as F
from pathlib import Path

OUT = Path(__file__).resolve().parent / "volume_solids_conflation_report.v1.json"

SOURCE = {
    "document": "Evonik Ancamide 221 EMEA Technical Data Sheet (Ancamide 221-X70 curing agent)",
    "url": "https://products.evonik.com/assets/em/ea/Ancamide_221_EMEA_TDS_EN_EN_TDS_PV_52041324_en_GB_EMEA.pdf",
    "footer_stamp_in_pdf": "Evonik Operations | Ancamide 221 EMEA | 3/26/2026",
    "fetched": "2026-08-03",
    "formulation": "A221-X70P1 (Anti-Corrosive Primer), Appendix I p.10 + Technical Data p.11",
    "cited_by_amphora_as": "amphora-known-answer-benchmarks/reference/mvp20/out/arithmetic_audit.json row id=A221-X70P1",
}

mass_A = F(1000)
mass_B = F(200)
dens_A = F("1.51")
dens_B = F("0.92")
vol_pct_A = F("46.0")
vol_pct_B = F("31.5")
wt_pct_A = F("70.0")
wt_pct_B = F("37.1")

vol_A = mass_A / dens_A
vol_B = mass_B / dens_B
total_vol = vol_A + vol_B
total_mass = mass_A + mass_B

# (1) correct volume-weighted recompute
solids_vol_A = vol_A * vol_pct_A / 100
solids_vol_B = vol_B * vol_pct_B / 100
mix_vol_solids_correct = (solids_vol_A + solids_vol_B) / total_vol * 100

# internal-consistency check: weight%-solids from the same masses
solids_mass_A = mass_A * wt_pct_A / 100
solids_mass_B = mass_B * wt_pct_B / 100
mix_wt_solids_check = (solids_mass_A + solids_mass_B) / total_mass * 100

# (2) hypothesized bug: mass-fraction-weighted average of volume%
mfrac_A = mass_A / total_mass
mfrac_B = mass_B / total_mass
mix_vol_solids_massweighted = mfrac_A * vol_pct_A + mfrac_B * vol_pct_B

# derived mix density, for reference (not the attacked control)
mix_density_derived = total_mass / total_vol


def r(x, nd=4):
    return float(round(x, nd))


control = {
    "control_id": "ARITH-A221-X70P1-VOLUME-SOLIDS",
    "expected_in_receipt": 42.5,
    "actual_in_receipt": 43.7,
    "tolerance_absolute_pp": 2.0,
    "status_in_receipt": "VERIFIED_PASS",
}

report = {
    "schema": "amphora.known-answer.volume-solids-mass-basis-conflation-report.v1",
    "attacked_control": control,
    "source": SOURCE,
    "transcribed_source_values": {
        "mass_A_g": float(mass_A), "mass_B_g": float(mass_B),
        "density_A_g_per_mL": float(dens_A), "density_B_g_per_mL": float(dens_B),
        "vol_pct_solids_A": float(vol_pct_A), "vol_pct_solids_B": float(vol_pct_B),
        "wt_pct_solids_A": float(wt_pct_A), "wt_pct_solids_B": float(wt_pct_B),
        "published_mix_density_g_per_mL": 1.37,
        "published_mix_vol_pct_solids": 42.5,
        "published_mix_wt_pct_solids": 64.5,
    },
    "internal_consistency_gate": {
        "recomputed_mix_wt_pct_solids": r(mix_wt_solids_check),
        "published_mix_wt_pct_solids": 64.5,
        "delta": r(mix_wt_solids_check - F("64.5")),
        "passes_sanity_gate_abs_lt_0_1pp": abs(mix_wt_solids_check - F("64.5")) < F("0.1"),
    },
    "results": {
        "correct_volume_weighted_recompute": {
            "method": "solids_volume_total / mix_volume_total * 100, "
                      "where component volume = component mass / component density",
            "value": r(mix_vol_solids_correct),
            "delta_vs_receipt_expected_42_5": r(mix_vol_solids_correct - F("42.5")),
            "delta_vs_receipt_actual_43_7": r(mix_vol_solids_correct - F("43.7")),
            "matches_receipt_expected_within_0_2pp": abs(mix_vol_solids_correct - F("42.5")) < F("0.2"),
            "matches_receipt_actual_within_tolerance_2pp": abs(mix_vol_solids_correct - F("43.7")) < F("2.0"),
        },
        "hypothesized_bug_mass_fraction_weighted": {
            "method": "mass_fraction_A * vol_pct_A + mass_fraction_B * vol_pct_B "
                      "(INVALID: weights a volume-basis quantity by mass fraction; "
                      "only valid if density_A == density_B, which is false: 1.51 vs 0.92)",
            "value": r(mix_vol_solids_massweighted),
            "delta_vs_receipt_actual_43_7": r(mix_vol_solids_massweighted - F("43.7")),
            "closely_reproduces_receipt_actual_within_0_2pp": abs(mix_vol_solids_massweighted - F("43.7")) < F("0.2"),
        },
        "derived_mix_density_reference_only": r(mix_density_derived, 5),
    },
    "verdict": {
        "receipt_actual_43_7_is_reproducible_from_cited_source_by_correct_method": False,
        "receipt_actual_43_7_is_reproducible_from_cited_source_by_mass_fraction_conflation": True,
        "correct_recompute_instead_reproduces_receipt_expected_42_5": True,
        "gap_between_correct_recompute_and_receipt_actual_pp": r(abs(mix_vol_solids_correct - F("43.7"))),
        "gap_as_fraction_of_tolerance_band": r(abs(mix_vol_solids_correct - F("43.7")) / F("2.0"), 3),
    },
}

OUT.write_text(json.dumps(report, indent=2, sort_keys=True))
print(json.dumps(report, indent=2, sort_keys=True))
print("WROTE", OUT, "sha256", hashlib.sha256(OUT.read_bytes()).hexdigest())
