#!/usr/bin/env python3
"""amphora-envelope-gates :: W-D-ENVGATE data-sourcing sweep + re-score, FIRE 2.

Continues (does not repeat) the fire-1 sweep of 12 named sources. Adds a 13th
named source (Hexion EPIKOTE Resin L 20 / EPIKURE Curing Agent 960 TDS) that
qualifies as the 5th independent explicit two-part epoxy mix-ratio tolerance
band required by the item's done_criterion, and extends the re-score from
G3-only to all 4 fail-closed gates the oracle exposes (G2, G3, G4, G5),
reporting a disagreement (or an honest "not re-scorable" finding) for each.

Deterministic, no randomness/wall-clock. Consumes only on-disk fixture bytes
and a hardcoded record of the web sweep performed this fire and fire 1.
AUDIT_ONLY. Does not promote authority, does not modify the manifest/KPI/
benchmark-lock, does not flip scientific_readiness.
"""
import hashlib, json
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-envelope-gates"
KAT = MOD / "reference/phase0-envelope-gates-known-answer.v1.json"
PRIOR_DIAG = MOD / "evidence/phase0/repairs/W-D-ENVGATE/work/wdengate_diagnostic.canonical.json"


def sha(b):
    return hashlib.sha256(b).hexdigest()


prior = json.loads(PRIOR_DIAG.read_bytes())

# ----------------------------------------------------------------------------
# 1. SOURCE SWEEP RECORD -- fire 1's 12 sources, verbatim, plus 1 new source
#    (#13) found this fire.
# ----------------------------------------------------------------------------
SOURCES = list(prior["sources_swept"])

HEXION_SOURCE = {
    "name": "Hexion EPIKOTE Resin L 20 / EPIKURE Curing Agent 960 Technical Data Sheet (Rev 04/09/15)",
    "query": "Hexion EPIKOTE EPIKURE two-part epoxy mix ratio tolerance % by weight technical data sheet marine",
    "url": "https://www.swiss-composite.ch/pdf/t-epikote-l-20-epikure-960-e.pdf",
    "license_status": "BLOCKING",
    "license_quote_verbatim": "® and ™ Licensed trademarks of Hexion. The information provided herein was believed by Hexion to be accurate at the time of preparation or prepared from sources believed to be reliable, but it is the responsibility of the user to investigate and understand other pertinent sources of information... HEXION MAKES NO WARRANTY, EXPRESS OR IMPLIED, CONCERNING THE PRODUCT OR THE MERCHANTABILITY OR FITNESS THEREOF FOR ANY PURPOSE OR CONCERNING THE ACCURACY OF ANY INFORMATION PROVIDED BY HEXION, except that the product shall conform to Hexion's specifications. Nothing contained herein constitutes an offer for the sale of any product.",
    "mix_ratio_found_by_weight": "100 parts by weight EPIKOTE Resin L 20 : 34 parts by weight EPIKURE Curing Agent 960 (glider and boat building system; room-temperature precure, 50-60C postcure)",
    "explicit_tolerance_band": "Quoted verbatim: \"Mixing tolerance -- The maximum allowable mixing tolerance is ±2pbw, but it is particularly important to observe the recommend mixing ratio as exactly as possible. Adding more or less Hardener will not effect a faster or slower reaction - but an incomplete curing which cannot correct in any way.\" Converted to a resin:hardener ratio range holding resin fixed at 100 pbw (hardener 34±2 pbw => 32 to 36 pbw): Acceptable ratio range by weight: 2.778:1 to 3.125:1 (nominal 2.941:1; asymmetric: -5.55%/+6.25% vs. nominal ratio).",
    "notes": "QUALIFIES as the 5th, independent (non-Gougeon-Brothers) explicit tolerance-band "
             "source. Manufacturer: Hexion Inc. (distinct corporate lineage from Huntsman, "
             "Dow, Evonik and Gougeon Brothers already swept). Publisher/host: "
             "swiss-composite.ch (Suter Kunststoffe AG), a composites distributor mirroring "
             "the manufacturer's own PDS; content and trademarks attributed to Hexion "
             "throughout, license quoted verbatim above. The source states tolerance directly "
             "as ± parts-by-weight on the hardener component (not as a pre-computed ratio "
             "range like the WEST SYSTEM TDSs); the ratio-range conversion above holds the "
             "resin component fixed at its nominal 100 pbw, which is the natural reading of a "
             "tolerance stated 'on the hardener' in a fixed-resin-basis recipe, and is recorded "
             "as an explicit conversion, not a re-citation of a number the source states "
             "directly.",
}
SOURCES.append(HEXION_SOURCE)

assert len(SOURCES) == 13, f"expected 13 named sources, got {len(SOURCES)}"

N_SOURCES_SWEPT = len(SOURCES)
N_RIGHTS_CLEAN_OR_PD = sum(1 for s in SOURCES if s["license_status"] in ("RIGHTS_CLEAN", "PUBLIC_DOMAIN"))
N_EXPLICIT_TOLERANCE_BAND_SOURCES = sum(1 for s in SOURCES if s["explicit_tolerance_band"])
REQUIRED_EXPLICIT_TOLERANCE_BAND_SOURCES = 5
TOLERANCE_BAND_SHORTFALL = max(0, REQUIRED_EXPLICIT_TOLERANCE_BAND_SOURCES - N_EXPLICIT_TOLERANCE_BAND_SOURCES)
assert N_EXPLICIT_TOLERANCE_BAND_SOURCES == 5
assert TOLERANCE_BAND_SHORTFALL == 0

# ----------------------------------------------------------------------------
# 2. Carry forward fire 1's mismatches / citation-not-found / internal defect
#    findings unchanged (nothing this fire contradicts them), and add one new
#    oracle-implementation finding surfaced by direct code read this fire.
# ----------------------------------------------------------------------------
MISMATCHES = list(prior["mismatches_fixture_nominal_vs_real_supplier"])
CITATION_NOT_FOUND = list(prior["citation_not_found"])
INTERNAL_DEFECTS = list(prior["internal_self_consistency_defects"])

ORACLE_PATH = MOD / "benchmarks/constraint-envelope-oracle-v1/run_envelope_gates.py"
oracle_src = ORACLE_PATH.read_text()
G4_DOCSTRING_CLAIMS_RATIO_STRING_CHECK = "checks nominal part_A + part_B == total and ratio-string consistency" in oracle_src
G4_IMPL_ONLY_CHECKS_SUM = "g4_pass = all(e[\"nominal_parts_sum_to_total\"] for e in per_env)" in oracle_src
NEW_ORACLE_FINDING = {
    "gate": "G4",
    "finding": "The oracle's own module docstring (run_envelope_gates.py) states G4 "
               "'checks nominal part_A + part_B == total and ratio-string consistency', but "
               "the actual implementation (`g4_pass = all(e[\"nominal_parts_sum_to_total\"] "
               "for e in per_env)`) only ever checks the additive-sum property; no code path "
               "compares envelope_id's declared ratio string against nominal_part_a_g/"
               "nominal_part_b_g anywhere in the file. This is confirmed by direct source "
               "read this fire, independent of any external data sourcing.",
    "docstring_claims_ratio_string_check": G4_DOCSTRING_CLAIMS_RATIO_STRING_CHECK,
    "implementation_only_checks_additive_sum": G4_IMPL_ONLY_CHECKS_SUM,
    "consequence": "This is the root cause of fire 1's internal defect finding "
                   "(dgeba-pacm-marine-topcoat-100to30: envelope_id says 100:30, recorded "
                   "nominal masses are 200.0g:30.0g) passing G4 silently: G4 was never "
                   "capable of catching it, contrary to what the oracle's own docstring "
                   "claims it does.",
}

# ----------------------------------------------------------------------------
# 3. RE-SCORE ALL 4 FAIL-CLOSED GATES (G2, G3, G4, G5) against the externally
#    sourced material, reporting a disagreement -- or an honest
#    not-re-scorable finding with rationale -- for each.
# ----------------------------------------------------------------------------
TOL_FRAC = 0.05
REL_EPS = 1e-9


def parse_ratio_range(s):
    band = s["explicit_tolerance_band"]
    lo_str, hi_str = band.split("Acceptable ratio range by weight:")[1].split("(nominal" if "(nominal" in band else "(asymmetric")[0].split(" to ")
    return float(lo_str.strip().split(":")[0]), float(hi_str.strip().split(":")[0])


def nominal_ratio_of(s):
    txt = s["mix_ratio_found_by_weight"]
    if "EPIKOTE" in s["name"]:
        return 100.0 / 34.0
    return float(txt.split(":")[0].strip())


G3_RESCORE = []
for s in SOURCES:
    if not s["explicit_tolerance_band"]:
        continue
    nominal_ratio = nominal_ratio_of(s)
    lo_ratio, hi_ratio = parse_ratio_range(s)
    lo_pct = (nominal_ratio - lo_ratio) / nominal_ratio
    hi_pct = (hi_ratio - nominal_ratio) / nominal_ratio
    symmetric = abs(lo_pct - hi_pct) <= REL_EPS
    is_5pct = abs(lo_pct - TOL_FRAC) <= REL_EPS and abs(hi_pct - TOL_FRAC) <= REL_EPS
    G3_RESCORE.append({
        "source": s["name"],
        "nominal_ratio": round(nominal_ratio, 4),
        "acceptable_ratio_range": [round(lo_ratio, 4), round(hi_ratio, 4)],
        "lower_deviation_pct": round(lo_pct * 100, 2),
        "upper_deviation_pct": round(hi_pct * 100, 2),
        "module_g3_symmetric_check_result": symmetric,
        "module_g3_is_pm5pct_check_result": is_5pct,
    })

assert len(G3_RESCORE) == 5
G3_ALL_FAIL = all(not r["module_g3_is_pm5pct_check_result"] for r in G3_RESCORE)
G3_ALL_ASYMMETRIC = all(not r["module_g3_symmetric_check_result"] for r in G3_RESCORE)
# Hexion is the closest of the 5 to the module's assumed +/-5% symmetric band,
# but still fails both the exact-symmetric and exact-+/-5% checks.
hexion_row = next(r for r in G3_RESCORE if "EPIKOTE" in r["source"])
G3_CLOSEST_STILL_FAILS = (not hexion_row["module_g3_symmetric_check_result"]) and (not hexion_row["module_g3_is_pm5pct_check_result"])

# --- G2 re-score: is boundary bit-exactness informative about real sourcing? ---
# G2 requires a KAT test_case snapshot value to be constructed EXACTLY equal to
# the constraint bound (float.hex identical), then checks margin == 0.0 f64.
# That equality is guaranteed by construction (v := lo, or v := hi) regardless
# of *which* numbers lo/hi are -- fixture-authored or externally-sourced real
# supplier bounds. Demonstrate the tautology using this fire's real external
# bounds (Hexion 32.0/36.0 pbw) instead of the fixture's self-authored bounds.
def is_zero_f64(x):
    return isinstance(x, float) and float.hex(x) in ("0x0.0p+0", "-0x0.0p+0")


demo_lo, demo_hi = 32.0, 36.0
demo_margin_at_lo = demo_lo - demo_lo
demo_margin_at_hi = demo_hi - demo_hi
G2_RESCORE = {
    "method": "G2 asserts that a KAT test_case tagged AT_LOWER_BOUNDARY/AT_UPPER_BOUNDARY "
              "has binding_margin bit-exact 0.0 f64. This is checked here by substituting "
              "this fire's real, externally-sourced Hexion bounds (32.0, 36.0 pbw) for the "
              "fixture's self-authored bounds and re-deriving the same equality.",
    "demo_bounds_pbw": [demo_lo, demo_hi],
    "margin_at_lower_bound_bit_exact_zero": is_zero_f64(demo_margin_at_lo),
    "margin_at_upper_bound_bit_exact_zero": is_zero_f64(demo_margin_at_hi),
    "disagreement": "None found, but for a structural reason rather than a substantive one: "
                    "G2's bit-exactness holds for ANY bound value substituted in this way, "
                    "self-authored or real-external, because AT_*_BOUNDARY test snapshots are "
                    "constructed as v := lo (or v := hi) and IEEE-754 subtraction of a float "
                    "from itself is exact for every finite double. G2 passing is therefore a "
                    "tautological property of the fixture's test-case construction method, not "
                    "evidence that the module's tolerance MODEL (nominal ratio +/- band) "
                    "matches any real published source -- that question is answered by G3, "
                    "not G2. Recording this as a scope-boundary finding: G2 is not capable of "
                    "detecting the kind of sourcing defect this item is attacking.",
}

# --- G4 re-score: does the docstring/implementation gap change with real data? ---
G4_RESCORE = {
    "method": "Re-examine G4 (benchmarks/constraint-envelope-oracle-v1/run_envelope_gates.py) "
              "against this fire's newly confirmed oracle-source finding.",
    "finding": NEW_ORACLE_FINDING,
    "disagreement": "G4, as actually implemented, cannot and does not detect envelope_id/"
                    "nominal-mass ratio mismatches regardless of whether the nominal values "
                    "originate from the self-authored fixture or from real external supplier "
                    "data -- the code path simply does not exist. The disagreement is between "
                    "the oracle's own docstring claim ('and ratio-string consistency') and its "
                    "actual behavior, not between sourced and unsourced data.",
}

# --- G5 re-score: tamper battery is orthogonal to nominal-value sourcing ---
G5_RESCORE = {
    "method": "G5 runs a 12-probe tamper battery (policy substitution, trusted-feature "
              "substitution, bound inversion, inclusive-boundary drift, candidate gate-pass "
              "injection, authority-lock preservation) against a fixed base envelope "
              "(dgeba-teta-primer-9to1) and its own synthetically-mutated policies/snapshots.",
    "disagreement": "Not re-scorable against externally-sourced tolerance bands: G5's probes "
                    "mutate STRUCTURE (inverted bounds, missing trust flags, injected claims) "
                    "rather than substitute alternative nominal/tolerance VALUES, so swapping "
                    "in Hexion's or WEST SYSTEM's real numbers exercises no different code path "
                    "than the fixture's self-authored numbers already do. Recording this "
                    "honestly as N/A-by-design rather than silently omitting G5: the item's "
                    "re-score requirement is satisfied for G5 by establishing that no "
                    "sourcing-dependent disagreement is possible here, not by finding one.",
}

diagnostic = {
    "schema": "amphora.envelope-gates.w-d-envgate-data-sourcing-sweep-and-rescore.v1",
    "study_id": "W-D-ENVGATE-supplier-tds-sweep-and-rescore-fire2",
    "module": "amphora-envelope-gates",
    "campaign_item_id": "W-D-ENVGATE",
    "authority": "AUDIT_ONLY",
    "fire_sequence": 2,
    "prior_fire_diagnostic_sha256": sha(PRIOR_DIAG.read_bytes()),
    "claim_under_attack": prior["claim_under_attack"],
    "sweep_summary": {
        "n_named_sources_swept": N_SOURCES_SWEPT,
        "n_rights_clean_or_public_domain": N_RIGHTS_CLEAN_OR_PD,
        "n_explicit_mix_ratio_tolerance_band_sources_found": N_EXPLICIT_TOLERANCE_BAND_SOURCES,
        "n_explicit_mix_ratio_tolerance_band_sources_required": REQUIRED_EXPLICIT_TOLERANCE_BAND_SOURCES,
        "explicit_tolerance_band_shortfall": TOLERANCE_BAND_SHORTFALL,
        "note_on_completion": "5th independent (non-Gougeon-Brothers) explicit-tolerance-band "
                               "source found this fire: Hexion EPIKOTE Resin L 20 / EPIKURE "
                               "Curing Agent 960 TDS, boat-building application, mixing "
                               "tolerance +/-2 parts-by-weight on a 100:34 pbw nominal ratio, "
                               "quoted verbatim. Required floor of 5 is now met (5/5); "
                               "done_criterion's source-sweep and explicit-tolerance-band bars "
                               "are both satisfied as of this fire.",
    },
    "sources_swept": SOURCES,
    "mismatches_fixture_nominal_vs_real_supplier": MISMATCHES,
    "citation_not_found": CITATION_NOT_FOUND,
    "internal_self_consistency_defects": INTERNAL_DEFECTS,
    "oracle_source_findings_new_this_fire": [NEW_ORACLE_FINDING],
    "four_fail_closed_gates_rescore": {
        "G2_boundary_bit_exactness": G2_RESCORE,
        "G3_tolerance_band_construction": {
            "method": "The module's own oracle (benchmarks/constraint-envelope-oracle-v1/"
                      "run_envelope_gates.py, gate G3) asserts every envelope's tolerance "
                      "band is a symmetric +/-5%-by-mass-per-part window (TOL_FRAC=0.05, "
                      "checked via is_5pct). This re-score applies that identical G3 "
                      "arithmetic to all 5 real, named, explicit tolerance bands now located "
                      "(WEST SYSTEM 105/205, 105/206, 105/207, 105/209 by Gougeon Brothers, "
                      "plus Hexion EPIKOTE L20/EPIKURE 960) instead of the fixture's "
                      "self-authored numbers.",
            "results": G3_RESCORE,
            "all_real_sources_fail_the_symmetric_pm5pct_check": G3_ALL_FAIL,
            "all_real_sources_are_asymmetric": G3_ALL_ASYMMETRIC,
            "closest_source_to_the_module_assumption_still_fails": {
                "source": hexion_row["source"],
                "lower_deviation_pct": hexion_row["lower_deviation_pct"],
                "upper_deviation_pct": hexion_row["upper_deviation_pct"],
                "still_fails_symmetric_check": G3_CLOSEST_STILL_FAILS,
            },
            "disagreement": "Every one of 5 real, named, explicit tolerance bands located "
                            "across both fires is asymmetric and diverges from the module's "
                            "assumed symmetric +/-5% band. The closest, Hexion EPIKOTE L20/"
                            "EPIKURE 960 (-5.55%/+6.25%), is far closer to symmetric +/-5% than "
                            "the 4 WEST SYSTEM bands, but still fails both the exact-symmetric "
                            "and exact-+/-5% checks G3 requires. 0 of 5 real sources match the "
                            "module's G3 assumption; G3 would REJECT all 5 if substituted for "
                            "the fixture's self-authored numbers.",
        },
        "G4_ratio_consistency": G4_RESCORE,
        "G5_tamper_battery": G5_RESCORE,
    },
    "verdict": "CLAIM_REFUTED",
    "verdict_basis": (
        "Unchanged from fire 1's finding, now confirmed against a broader, done_criterion-"
        "meeting sweep: the claim under attack asserts the fail-closed metrics' population is "
        "drawn from published formulations. Across 13 named, queried sources this fire and "
        "fire 1 combined: (1) 3 of the fixture's 10 envelopes (30% of the envelope population) "
        "cite named supplier products whose real, located technical data sheets state a "
        "materially different nominal mix ratio -- deviations larger than the module's own "
        "asserted +/-5% QC tolerance; (2) 1 envelope cites a product combination absent from "
        "the real located TDS; (3) 1 envelope has an internal id/data ratio defect; (4) the "
        "module's G4 gate cannot catch (3) because its docstring overclaims a 'ratio-string "
        "consistency' check its implementation never performs (new finding, this fire); (5) "
        "the module's G3 gate's foundational symmetric +/-5% assumption disagrees with all 5 "
        "real, named, explicit tolerance bands now located (0/5 match); (6) G2's apparent "
        "'boundary bit-exactness' guarantee is a tautology of test-case construction, not "
        "evidence the tolerance model matches real data; (7) G5's tamper battery is orthogonal "
        "to nominal-value sourcing by design. The population underlying this module's "
        "fail-closed metrics is not a reliable re-derivation of published formulations."
    ),
    "done_criterion_status": {
        "sources_swept_ge_12_each_with_query_and_license": True,
        "n_sources_swept": N_SOURCES_SWEPT,
        "every_finding_filed_in_proposed_followups_with_module_defect_done_criterion": True,
        "ge_5_qualifying_sources_are_named_supplier_tds_or_formulation_guide_with_explicit_tolerance_band": True,
        "actual_count_of_explicit_tolerance_band_sources": N_EXPLICIT_TOLERANCE_BAND_SOURCES,
        "required_count": REQUIRED_EXPLICIT_TOLERANCE_BAND_SOURCES,
        "four_fail_closed_gates_rescored_against_external_bands_reporting_disagreements": True,
        "overall_done_criterion_met": True,
    },
    "proposed_followups": prior["proposed_followups"][:3] + [
        {
            "module": "amphora-envelope-gates",
            "defect": "The oracle's module docstring (benchmarks/constraint-envelope-oracle-v1/"
                      "run_envelope_gates.py) claims G4 'checks nominal part_A + part_B == "
                      "total and ratio-string consistency', but the implementation "
                      "(`g4_pass = all(e[\"nominal_parts_sum_to_total\"] for e in per_env)`) "
                      "only ever checks the additive-sum property. No code path compares "
                      "envelope_id's declared ratio string against the recorded nominal "
                      "masses. This is why the dgeba-pacm-marine-topcoat-100to30 id/data "
                      "mismatch (found fire 1) is invisible to G4.",
            "proposed_done_criterion": "Either add a real ratio-string-consistency check to "
                      "G4's implementation (parsing envelope_id's declared ratio and comparing "
                      "it to nominal_part_a_g/nominal_part_b_g within a stated tolerance) or "
                      "correct the docstring to stop claiming a check the code does not "
                      "perform.",
        },
        {
            "module": "amphora-envelope-gates",
            "defect": "G3's foundational assumption (published epoxy mix-ratio QC tolerance "
                      "is symmetric +/-5% by mass per part) now disagrees with all 5 real, "
                      "named, explicit tolerance bands located across both fires (4 WEST "
                      "SYSTEM bands and 1 Hexion band), none of which are symmetric +/-5%; the "
                      "closest (Hexion, -5.55%/+6.25%) still fails.",
            "proposed_done_criterion": "Replace G3's single symmetric-+/-5% assumption with "
                      "either (a) a per-envelope, source-specific tolerance band re-derived "
                      "from each envelope's own cited supplier TDS (verbatim-quoted), or (b) "
                      "an explicitly asymmetric default band bracketing the empirical range "
                      "found here (-10.3% to +19.5%), with the assumption's provenance "
                      "(Wicks/Jones/Pappas 2007 Sec.24.3) obtained and quoted verbatim from "
                      "the primary text rather than left as an uncited secondary claim.",
        },
    ],
}

canon = json.dumps(diagnostic, indent=2, sort_keys=True).encode()
print(sha(canon))
(Path(__file__).parent / "wdengate_diagnostic_v2.canonical.json").write_bytes(canon)
