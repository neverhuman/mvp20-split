#!/usr/bin/env python3
"""amphora-envelope-gates :: W-D-ENVGATE data-sourcing sweep + re-score.

Deterministic, no randomness/wall-clock. Consumes only on-disk fixture bytes
and a hardcoded record of the web sweep performed this fire (queries run,
documents fetched, license text quoted verbatim, numeric facts extracted).
AUDIT_ONLY. Does not promote authority, does not modify the manifest/KPI/
benchmark-lock, does not flip scientific_readiness.
"""
import hashlib, json
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-envelope-gates"
KAT = MOD / "reference/phase0-envelope-gates-known-answer.v1.json"


def sha(b):
    return hashlib.sha256(b).hexdigest()


# ----------------------------------------------------------------------------
# 1. SOURCE SWEEP RECORD -- every source touched this fire, its query string,
#    and its license status quoted verbatim (or the blocking license quoted
#    verbatim). This satisfies the item's ">=12 named sources swept" bar.
# ----------------------------------------------------------------------------
SOURCES = [
    {
        "name": "Huntsman Araldite LY 1564 / Aradur 3486 / Aradur 3487 TDS (2012)",
        "query": "Huntsman Aradur 3486 technical data sheet mix ratio",
        "url": "https://www.swiss-composite.ch/pdf/t-Araldite-LY1564-Aradur3486-3487-e.pdf",
        "license_status": "BLOCKING",
        "license_quote_verbatim": "Copyright © 2012 Huntsman Corporation or an affiliate thereof. All rights reserved.",
        "mix_ratio_found_by_weight": "100 : 34 (Araldite LY 1564 : Aradur 3486)",
        "explicit_tolerance_band": None,
        "notes": "Fixture cites 'Huntsman Aradur 3486 amidoamine primer TDS 100:50 by mass'. "
                 "The only Huntsman Aradur 3486 TDS locatable states 100:34 by weight against "
                 "LY 1564, not LY/DGEBA 828 and not 100:50, and does not carry the ' ±5% "
                 "by weight' tolerance quote the fixture attributes to it. No explicit numeric "
                 "tolerance percentage appears anywhere in this document.",
    },
    {
        "name": "Huntsman / Vantico Araldite GY 6010 Data Sheet (2003)",
        "query": "Huntsman Araldite GY 6010 HY 2954 technical data sheet mix ratio by weight",
        "url": "https://www.usna.edu/Users/mecheng/pjoyce/composites/em436/sampe-bridge/Kit_Data/GY6010.pdf",
        "license_status": "BLOCKING",
        "license_quote_verbatim": "THERE IS NO WARRANTY OR CONDITION, WHETHER EXPRESS OR IMPLIED BY ANY STATUTE OR OTHERWISE... The following shall supersede any provision in Buyer's forms, letters and papers.",
        "mix_ratio_found_by_weight": None,
        "explicit_tolerance_band": None,
        "notes": "Fixture cites 'Huntsman Araldite GY-6010 + HY 2954 (IPDA) TDS 100:24 nominal by "
                 "mass'. The real GY 6010 TDS's own hardener compatibility table lists 17 named "
                 "Aradur/HY hardeners with their phr ratios (Aradur 956-1, 943, 3440, 3441, 2964, "
                 "2963, 265, 355, 847, 3100, 3150, 815-2, 825-2, 840-2, 283, 360, HY 906 NMA, "
                 "Aradur 917 MTHPA) -- HY 2954 is ABSENT from this list. The cited product "
                 "combination could not be located in the document the fixture attributes it to.",
    },
    {
        "name": "Evonik Ancamine 2049 Curing Agent Product Information",
        "query": "Evonik Ancamine 2049 technical data sheet DGEBA mix ratio",
        "url": "https://crosslinkers-web.panpage.de/en2/crosslinkers/ancamine/usa/ancamine_2049_us.pdf",
        "license_status": "BLOCKING",
        "license_quote_verbatim": "EVONIK EXPRESSLY DISCLAIMS ANY REPRESENTATIONS AND WARRANTIES OF ANY KIND, WHETHER EXPRESS OR IMPLIED, AS TO THE ACCURACY, COMPLETENESS, NON-INFRINGEMENT, MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE...",
        "mix_ratio_found_by_weight": "Use Level 32.0 PHR (i.e. 100 : 32)",
        "explicit_tolerance_band": None,
        "notes": "Fixture cites 'Air Products Ancamine 2049 (PACM) marine topcoat TDS 100:30 by "
                 "mass' and 'ratio ±5% by weight' (Air Products' curing-agents line was sold "
                 "to Evonik in 2018; this is the current manufacturer document for the same "
                 "product). Real use level is 32.0 PHR, not 30. No explicit tolerance percentage "
                 "appears anywhere in this document.",
    },
    {
        "name": "Dow D.E.H. 24 / D.E.H. 20 Epoxy Curing Agent Product Information",
        "query": "Olin DER 331 DEH 24 epoxy hardener technical data sheet mix ratio parts by weight",
        "url": "https://www.stobec.com/data/produit/1544~v~data_8493.pdf",
        "license_status": "BLOCKING",
        "license_quote_verbatim": "Notice: No freedom from any patent owned by Dow or others is to be inferred... NO WARRANTIES ARE GIVEN; ALL IMPLIED WARRANTIES OF MERCHANTABILITY OR FITNESS FOR A PARTICULAR PURPOSE ARE EXPRESSLY EXCLUDED.",
        "mix_ratio_found_by_weight": "D.E.H. 24 (TETA): 13 phr with D.E.R. 331; D.E.H. 20 (DETA): 11 phr with D.E.R. 331",
        "explicit_tolerance_band": None,
        "notes": "Fixture cites 'Dow DER 331 + DEH 24 TDS' for a 9:1 (100:11.11) envelope and "
                 "'Dow DER 331 + DEH 20 TDS' for a 17:1 (100:5.88) envelope. The real Dow "
                 "product-family table states D.E.H. 24/TETA at 13 phr and D.E.H. 20/DETA at 11 "
                 "phr -- both fixture ratios are far off the real published use ratios (see "
                 "MISMATCHES below). Document instead warns mix ratios are 'inconvenient... "
                 "which must be weighed very accurately' -- no numeric tolerance percentage "
                 "given.",
    },
    {
        "name": "Simco Coatings / San Diego Seal MIL-DTL-24441 Formula 150/151/157 TDS compilation",
        "query": "MIL-DTL-24441 epoxy coating mix ratio tolerance public",
        "url": "https://sandiegoseal.com/pdf/epoxy.pdf",
        "license_status": "MIXED_PARTIAL_PUBLIC_DOMAIN",
        "license_quote_verbatim": "The technical data listed herein has been compiled for your convenience and guidance... Simco Coatings, Inc. assumes no responsibility whatsoever for coverage, performance, or any other damages... (no copyright claim found on the vendor's own compiled sheet)",
        "mix_ratio_found_by_weight": "54 : 46 (base : hardener) by weight; 50:50 by volume; also 1:1 by volume for Formula 151/157",
        "explicit_tolerance_band": None,
        "explicit_tolerance_band_note": "No explicit band on the mix ratio itself, but explicit numeric \u00b1 bands are given on adjacent QC properties: mass density 11.0 \u00b1 0.5 lbs/gal, solids by volume 63 \u00b1 2%.",
        "notes": "MIL-DTL-24441 is a US federal specification; specification TEXT authored by the "
                 "US government carries no copyright under 17 U.S.C. §105 (public domain). "
                 "This particular vendor's TDS reproduction is a separate compiled document "
                 "whose own rights status is not explicitly stated either way -- recorded "
                 "conservatively as not fully rights-clean for redistribution. Not cited by any "
                 "of the fixture's 10 envelopes (independent structural-overlap source only).",
    },
    {
        "name": "WEST SYSTEM 105/205 (Gougeon Brothers) Technical Data Sheet",
        "query": "epoxy hardener mix ratio ±5% technical data sheet by weight coating",
        "url": "https://www.westsystem.com/app/uploads/2022/09/105_205-207-Combined.pdf",
        "license_status": "BLOCKING",
        "license_quote_verbatim": "All rights reserved. No part of the contents may be reproduced or transmitted in any form or by any means without written permission. (Gougeon Brothers, Inc. copyright pattern confirmed across the publisher's other westsystem.com manuals; no distinct footer license line was present on the TDS pages themselves.)",
        "mix_ratio_found_by_weight": "5.19 : 1 (resin : hardener)",
        "explicit_tolerance_band": "Acceptable ratio range by weight: 4.83:1 to 6.20:1 (asymmetric: -6.9% / +19.5% vs. nominal ratio)",
        "notes": "QUALIFIES as an explicit tolerance-band source. Real published band is NOT "
                 "symmetric +/-5%.",
    },
    {
        "name": "WEST SYSTEM 105/206 (Gougeon Brothers) Technical Data Sheet",
        "query": "epoxy hardener mix ratio ±5% technical data sheet by weight coating",
        "url": "https://www.westsystem.com/app/uploads/2022/09/105_205-207-Combined.pdf",
        "license_status": "BLOCKING",
        "license_quote_verbatim": "All rights reserved. No part of the contents may be reproduced or transmitted in any form or by any means without written permission. (same publisher pattern as 105/205)",
        "mix_ratio_found_by_weight": "5.36 : 1 (resin : hardener)",
        "explicit_tolerance_band": "Acceptable ratio range by weight: 4.84:1 to 6.19:1 (asymmetric: -9.7% / +15.5% vs. nominal ratio)",
        "notes": "QUALIFIES as an explicit tolerance-band source.",
    },
    {
        "name": "WEST SYSTEM 105/207 (Gougeon Brothers) Technical Data Sheet",
        "query": "epoxy hardener mix ratio ±5% technical data sheet by weight coating",
        "url": "https://www.westsystem.com/app/uploads/2022/09/105_205-207-Combined.pdf",
        "license_status": "BLOCKING",
        "license_quote_verbatim": "All rights reserved. No part of the contents may be reproduced or transmitted in any form or by any means without written permission. (same publisher pattern as 105/205)",
        "mix_ratio_found_by_weight": "3.64 : 1 (resin : hardener)",
        "explicit_tolerance_band": "Acceptable ratio range by weight: 3.41:1 to 4.16:1 (asymmetric: -6.3% / +14.3% vs. nominal ratio)",
        "notes": "QUALIFIES as an explicit tolerance-band source.",
    },
    {
        "name": "WEST SYSTEM 105/209 (Gougeon Brothers) Technical Data Sheet",
        "query": "epoxy hardener mix ratio ±5% technical data sheet by weight coating",
        "url": "https://www.westsystem.com/app/uploads/2022/09/105_205-207-Combined.pdf",
        "license_status": "BLOCKING",
        "license_quote_verbatim": "All rights reserved. No part of the contents may be reproduced or transmitted in any form or by any means without written permission. (same publisher pattern as 105/205)",
        "mix_ratio_found_by_weight": "3.68 : 1 (resin : hardener)",
        "explicit_tolerance_band": "Acceptable ratio range by weight: 3.30:1 to 4.03:1 (asymmetric: -10.3% / +9.5% vs. nominal ratio)",
        "notes": "QUALIFIES as an explicit tolerance-band source.",
    },
    {
        "name": "System Three T-88 Structural Aircraft Adhesive Technical Data Sheet",
        "query": "System Three epoxy resin technical data sheet acceptable ratio range mix ratio tolerance",
        "url": "https://www.aircraftspruce.com/catalog/pdf/t88tds.pdf",
        "license_status": "BLOCKING",
        "license_quote_verbatim": "System Three Resins, Inc. makes no warranty, expressed or implied, regarding the accuracy of these data or the results to be obtained from the use thereof.",
        "mix_ratio_found_by_weight": "100 : 83 (resin : hardener); 1:1 by volume",
        "explicit_tolerance_band": None,
        "notes": "Fixed ratio only; document explicitly warns against varying it ('Excessive Part "
                 "B will degrade, rather than expedite cure') but states no numeric tolerance.",
    },
    {
        "name": "Molecules (MDPI) 28(11):4259 -- Benchmark Study of Epoxy Coatings with "
                "Bio-Based Phenalkamine vs. Fossil-Based Amine Crosslinkers",
        "query": "MDPI Coatings journal epoxy amine stoichiometric ratio open access",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC10254157/",
        "license_status": "RIGHTS_CLEAN",
        "license_quote_verbatim": "Licensee MDPI, Basel, Switzerland. This article is an open access article distributed under the terms and conditions of the Creative Commons Attribution (CC BY) license (https://creativecommons.org/licenses/by/4.0/).",
        "doi": "10.3390/molecules28114259",
        "mix_ratio_found_by_weight": "DGEBA:FA1 = 2:1 (w/w); DGEBA:PK1 = 2:1.25 (w/w)",
        "explicit_tolerance_band": None,
        "notes": "Rights-clean, CC-BY, DOI-cited. Confirms stoichiometric mixing is standard "
                 "peer-reviewed practice for DGEBA-amine coatings but states no mixing tolerance "
                 "band; not usable for the re-score, only for the source-sweep count.",
    },
    {
        "name": "MIL-DTL-24441 (US Department of Defense two-part epoxy-polyamide coating "
                "specification family) -- specification text itself, distinct from any vendor "
                "reproduction",
        "query": "MIL-DTL-24441 epoxy coating mix ratio tolerance public",
        "url": "n/a (federal specification; vendor reproductions checked at "
               "sandiegoseal.com/pdf/epoxy.pdf and milspeccoating.com)",
        "license_status": "PUBLIC_DOMAIN",
        "license_quote_verbatim": "Works of the United States Government are not subject to copyright protection in the United States (17 U.S.C. § 105).",
        "mix_ratio_found_by_weight": "54:46 by weight / 50:50 by volume (Formula 150/151/157, per vendor-reproduced TDS)",
        "explicit_tolerance_band": None,
        "notes": "The underlying specification text is public domain by statute; the numeric "
                 "values used above were read off the vendor reproduction (source #5) since the "
                 "specification's own PDF text was not directly retrievable this fire.",
    },
]

assert len(SOURCES) == 12, f"expected 12 named sources, got {len(SOURCES)}"

N_SOURCES_SWEPT = len(SOURCES)
N_RIGHTS_CLEAN_OR_PD = sum(1 for s in SOURCES if s["license_status"] in ("RIGHTS_CLEAN", "PUBLIC_DOMAIN"))
N_EXPLICIT_TOLERANCE_BAND_SOURCES = sum(1 for s in SOURCES if s["explicit_tolerance_band"])
REQUIRED_EXPLICIT_TOLERANCE_BAND_SOURCES = 5
TOLERANCE_BAND_SHORTFALL = max(0, REQUIRED_EXPLICIT_TOLERANCE_BAND_SOURCES - N_EXPLICIT_TOLERANCE_BAND_SOURCES)


# ----------------------------------------------------------------------------
# 2. RE-SCORE: substitute the real external nominal ratios found above into
#    the fixture's own envelope constraints and see whether the CORRECT,
#    real-world stoichiometric mix would PASS or FAIL the module's own
#    self-authored gate. This is the module's own G1/G3 logic (see
#    benchmarks/constraint-envelope-oracle-v1/run_envelope_gates.py),
#    replayed here with externally-sourced substitutions instead of the
#    fixture's self-authored numbers.
# ----------------------------------------------------------------------------
kat = json.loads(KAT.read_bytes())
envelopes = {e["envelope_id"]: e for e in kat["envelopes"]}


def constraint(env, feature_path):
    return next(c for c in env["policy"]["constraints"] if c["feature_path"] == feature_path)


def gate_check(value, lower, upper):
    return lower <= value <= upper


MISMATCHES = []

# --- (A) dgeba-teta-primer-9to1 vs real Dow D.E.H. 24 / D.E.R. 331 ratio (13 phr) ---
env = envelopes["dgeba-teta-primer-9to1"]
part_b = constraint(env, "mass.part_B_g")
real_part_b_g = env["nominal_part_a_g"] * (13.0 / 100.0)  # 13 phr of D.E.H. 24 real use ratio
fixture_part_b_g = env["nominal_part_b_g"]
MISMATCHES.append({
    "envelope_id": env["envelope_id"],
    "cited_source": "Dow DER 331 + DEH 24 TDS",
    "fixture_nominal_part_b_g": fixture_part_b_g,
    "real_supplier_part_b_g_for_same_part_a": round(real_part_b_g, 3),
    "relative_deviation_pct": round(abs(fixture_part_b_g - real_part_b_g) / real_part_b_g * 100, 2),
    "fixture_envelope_bounds_part_b_g": [part_b["lower_inclusive"], part_b["upper_inclusive"]],
    "real_value_passes_fixture_envelope": gate_check(real_part_b_g, part_b["lower_inclusive"], part_b["upper_inclusive"]),
})

# --- (B) dgeba-deta-industrial-primer-17to1 vs real Dow D.E.H. 20 / D.E.R. 331 ratio (11 phr) ---
env = envelopes["dgeba-deta-industrial-primer-17to1"]
part_b = constraint(env, "mass.part_B_g")
real_part_b_g = env["nominal_part_a_g"] * (11.0 / 100.0)
fixture_part_b_g = env["nominal_part_b_g"]
MISMATCHES.append({
    "envelope_id": env["envelope_id"],
    "cited_source": "Dow DER 331 + DEH 20 TDS",
    "fixture_nominal_part_b_g": fixture_part_b_g,
    "real_supplier_part_b_g_for_same_part_a": round(real_part_b_g, 3),
    "relative_deviation_pct": round(abs(fixture_part_b_g - real_part_b_g) / real_part_b_g * 100, 2),
    "fixture_envelope_bounds_part_b_g": [part_b["lower_inclusive"], part_b["upper_inclusive"]],
    "real_value_passes_fixture_envelope": gate_check(real_part_b_g, part_b["lower_inclusive"], part_b["upper_inclusive"]),
})

# --- (C) dgeba-amidoamine-huntsman-100to50 vs real Huntsman Aradur 3486 ratio (34 pbw) ---
env = envelopes["dgeba-amidoamine-huntsman-100to50"]
part_b = constraint(env, "mass.part_B_g")
real_part_b_g = env["nominal_part_a_g"] * (34.0 / 100.0)
fixture_part_b_g = env["nominal_part_b_g"]
MISMATCHES.append({
    "envelope_id": env["envelope_id"],
    "cited_source": "Huntsman Aradur 3486 amidoamine primer TDS",
    "fixture_nominal_part_b_g": fixture_part_b_g,
    "real_supplier_part_b_g_for_same_part_a": round(real_part_b_g, 3),
    "relative_deviation_pct": round(abs(fixture_part_b_g - real_part_b_g) / real_part_b_g * 100, 2),
    "fixture_envelope_bounds_part_b_g": [part_b["lower_inclusive"], part_b["upper_inclusive"]],
    "real_value_passes_fixture_envelope": gate_check(real_part_b_g, part_b["lower_inclusive"], part_b["upper_inclusive"]),
})

CITATION_NOT_FOUND = [{
    "envelope_id": "dgeba-ipda-marine-primer-100to24",
    "cited_source": "Huntsman Araldite GY-6010 + HY 2954 (IPDA) TDS",
    "finding": "HY 2954 does not appear anywhere in the real GY 6010 TDS's 17-entry hardener "
               "compatibility table; the cited source/product-combination could not be located.",
}]

# --- (D) internal self-consistency defect, independent of any external source ---
env = envelopes["dgeba-pacm-marine-topcoat-100to30"]
INTERNAL_DEFECTS = [{
    "envelope_id": env["envelope_id"],
    "defect": "envelope_id declares a 100:30 ratio, but the envelope's own "
              "nominal_part_a_g/nominal_part_b_g are 200.0/30.0 (a 200:30, i.e. ~100:15, "
              "ratio) -- the id-declared ratio and the recorded nominal masses disagree with "
              "each other. This is a defect internal to the self-authored fixture, requiring "
              "no external source to establish.",
    "oracle_gap": "G4 (nominal_parts_sum_to_total in run_envelope_gates.py) checks only that "
                  "nominal_part_a_g + nominal_part_b_g == nominal_total_g (200+30==230, TRUE); "
                  "it never checks that the envelope_id's stated ratio matches the recorded "
                  "nominal masses, so this defect passes every check the module's own oracle "
                  "runs.",
}]

# --- (E) G3 re-score: real West System tolerance bands vs the module's assumed symmetric +/-5% ---
TOL_FRAC = 0.05
REL_EPS = 1e-9
G3_RESCORE = []
for s in SOURCES:
    if not s["explicit_tolerance_band"]:
        continue
    # parse "X:1 to Y:1" acceptable ratio range and nominal ratio from mix_ratio_found_by_weight
    nominal_ratio = float(s["mix_ratio_found_by_weight"].split(":")[0].strip())
    band = s["explicit_tolerance_band"]
    lo_str, hi_str = band.split("Acceptable ratio range by weight:")[1].split("(asymmetric")[0].split(" to ")
    lo_ratio = float(lo_str.strip().split(":")[0])
    hi_ratio = float(hi_str.strip().split(":")[0])
    # ratio = resin/hardener; lower ratio bound = more hardener allowed; higher ratio bound = less hardener allowed
    lo_pct = (nominal_ratio - lo_ratio) / nominal_ratio
    hi_pct = (hi_ratio - nominal_ratio) / nominal_ratio
    symmetric = abs(lo_pct - hi_pct) <= REL_EPS
    is_5pct = abs(lo_pct - TOL_FRAC) <= REL_EPS and abs(hi_pct - TOL_FRAC) <= REL_EPS
    G3_RESCORE.append({
        "source": s["name"],
        "nominal_ratio": nominal_ratio,
        "acceptable_ratio_range": [lo_ratio, hi_ratio],
        "lower_deviation_pct": round(lo_pct * 100, 2),
        "upper_deviation_pct": round(hi_pct * 100, 2),
        "module_g3_symmetric_check_result": symmetric,
        "module_g3_is_pm5pct_check_result": is_5pct,
    })

G3_ALL_FAIL = all(not r["module_g3_is_pm5pct_check_result"] for r in G3_RESCORE)
G3_ALL_ASYMMETRIC = all(not r["module_g3_symmetric_check_result"] for r in G3_RESCORE)

diagnostic = {
    "schema": "amphora.envelope-gates.w-d-envgate-data-sourcing-sweep-and-rescore.v1",
    "study_id": "W-D-ENVGATE-supplier-tds-sweep-and-rescore",
    "module": "amphora-envelope-gates",
    "campaign_item_id": "W-D-ENVGATE",
    "authority": "AUDIT_ONLY",
    "claim_under_attack": {
        "receipt_path": "amphora-envelope-gates/evidence/",
        "claim_text": "The envelope gates' fail-closed metrics carry a real sample size drawn "
                       "from published formulations.",
    },
    "sweep_summary": {
        "n_named_sources_swept": N_SOURCES_SWEPT,
        "n_rights_clean_or_public_domain": N_RIGHTS_CLEAN_OR_PD,
        "n_explicit_mix_ratio_tolerance_band_sources_found": N_EXPLICIT_TOLERANCE_BAND_SOURCES,
        "n_explicit_mix_ratio_tolerance_band_sources_required": REQUIRED_EXPLICIT_TOLERANCE_BAND_SOURCES,
        "explicit_tolerance_band_shortfall": TOLERANCE_BAND_SHORTFALL,
        "note_on_shortfall": "4 of 5 required explicit-tolerance-band sources found (all from "
                              "the WEST SYSTEM / Gougeon Brothers product family); a 5th "
                              "independent supplier or formulation-guide source with an "
                              "explicit numeric mix-ratio tolerance band was searched for "
                              "(Jotun, PPG/Amercoat, Sherwin-Williams, International Paint/"
                              "Intergard, Hempel, System Three, 3M Scotch-Weld, Devcon, "
                              "MIL-DTL-24441, and the fixture's own primary citation "
                              "Wicks/Jones/Pappas 2007 itself) but not located within this "
                              "fire's time budget -- see proposed_followups.",
    },
    "sources_swept": SOURCES,
    "mismatches_fixture_nominal_vs_real_supplier": MISMATCHES,
    "citation_not_found": CITATION_NOT_FOUND,
    "internal_self_consistency_defects": INTERNAL_DEFECTS,
    "g3_rescore_against_real_external_tolerance_bands": {
        "method": "The module's own oracle (benchmarks/constraint-envelope-oracle-v1/"
                  "run_envelope_gates.py, function run(), gate G3) asserts every envelope's "
                  "tolerance band is a symmetric +/-5%-by-mass-per-part window "
                  "(TOL_FRAC=0.05, checked via is_5pct). This re-score applies that identical "
                  "G3 arithmetic to 4 real, named, explicit tolerance bands found this fire "
                  "(WEST SYSTEM 105/205, 105/206, 105/207, 105/209) instead of to the "
                  "fixture's self-authored numbers.",
        "results": G3_RESCORE,
        "all_real_sources_fail_the_symmetric_pm5pct_check": G3_ALL_FAIL,
        "all_real_sources_are_asymmetric": G3_ALL_ASYMMETRIC,
        "disagreement": "Every real, named, explicit tolerance band located this fire is "
                        "asymmetric and diverges from the module's assumed symmetric +/-5% "
                        "band by a wide margin on at least one side (ranges from -6.3%/+9.5% "
                        "to -10.3%/+19.5%). Zero of 4 real sources match the module's G3 "
                        "assumption. G3, as currently written, would REJECT (is_5pct=False) "
                        "every one of these 4 real, named, published tolerance bands if they "
                        "were substituted for the fixture's self-authored numbers.",
    },
    "verdict": "CLAIM_REFUTED",
    "verdict_basis": (
        "The claim under attack asserts the fail-closed metrics' population is drawn from "
        "published formulations. This fire swept 12 named, queried sources and found: (1) 3 of "
        "the fixture's 10 envelopes (30% of the envelope population, 15 of 50 KAT test cases) "
        "cite named supplier products whose real, located technical data sheets state a "
        "materially different nominal mix ratio -- deviations of 11.4%-87.0%, all larger than "
        "the module's own asserted +/-5% QC tolerance -- such that the chemically-correct, "
        "real-world stoichiometric mix for the cited product would be REJECTED (not PASS) by "
        "the fixture's own envelope; (2) 1 envelope cites a specific product combination (GY "
        "6010 + HY 2954) that does not appear in the real, located TDS for that resin at all; "
        "(3) 1 envelope has an internal defect where the envelope_id's declared ratio "
        "(100:30) contradicts its own recorded nominal masses (200g:30g), a defect the "
        "module's own G4 self-check does not catch; (4) the module's G3 gate's foundational "
        "assumption -- that published epoxy mix-ratio QC tolerance is symmetric +/-5% by mass "
        "per part -- disagrees with all 4 real, named, explicit tolerance bands located this "
        "fire, none of which are symmetric and none of which are +/-5%. The population "
        "underlying this module's fail-closed metrics is not a reliable re-derivation of "
        "published formulations; it is a self-authored compilation whose specific numeric "
        "citations do not verify against the real documents named."
    ),
    "proposed_followups": [
        {
            "module": "amphora-envelope-gates",
            "defect": "3 of 10 self-authored KAT envelopes (dgeba-teta-primer-9to1, "
                      "dgeba-deta-industrial-primer-17to1, dgeba-amidoamine-huntsman-100to50) "
                      "cite named supplier TDSs whose real, located values diverge from the "
                      "fixture's nominal ratio by 11.4%-87.0%, and 1 envelope "
                      "(dgeba-ipda-marine-primer-100to24) cites a hardener/resin combination "
                      "(GY 6010 + HY 2954) absent from the real located TDS.",
            "proposed_done_criterion": "Either (a) re-derive these 4 envelopes' nominal ratios "
                      "and tolerance bands directly from a verbatim-quoted passage of the real "
                      "named source with the exact figure highlighted, or (b) replace the "
                      "citation with a source that can be verified, or (c) mark the envelope "
                      "provenance UNVERIFIED in the KAT fixture and exclude it from any "
                      "'published formulation' population claim until verified.",
        },
        {
            "module": "amphora-envelope-gates",
            "defect": "dgeba-pacm-marine-topcoat-100to30's envelope_id declares a 100:30 "
                      "ratio but its nominal_part_a_g/nominal_part_b_g are 200.0/30.0 (a "
                      "~100:15 ratio); the module's own oracle G4 check (nominal sum to "
                      "total) does not catch id/data ratio mismatches.",
            "proposed_done_criterion": "Either correct the envelope's nominal masses to match "
                      "its declared 100:30 id, or rename the id to match the recorded 200:30 "
                      "masses, and add an oracle check that the envelope_id's declared ratio "
                      "is consistent with nominal_part_a_g/nominal_part_b_g within a stated "
                      "tolerance.",
        },
        {
            "module": "amphora-envelope-gates",
            "defect": "The module's G3 gate assumes every published epoxy mix-ratio QC "
                      "tolerance band is symmetric +/-5% by mass per part (Wicks/Jones/Pappas "
                      "2007 Sec.24.3, uncited page/quote). All 4 real, named, explicit "
                      "tolerance bands located this fire (WEST SYSTEM 105/205, 105/206, "
                      "105/207, 105/209) are asymmetric and diverge from +/-5% by up to 4x on "
                      "one side.",
            "proposed_done_criterion": "Obtain and quote verbatim the actual Wicks/Jones/Pappas "
                      "2007 Sec.24.3 passage the module's tolerance construction is based on "
                      "(via a library/interlibrary loan or purchased excerpt, since it was not "
                      "accessible over the open web this fire), and either confirm the +/-5% "
                      "symmetric figure against that primary text or replace G3's assumption "
                      "with a tolerance model that accounts for asymmetric, product-specific "
                      "published bands.",
        },
        {
            "module": "amphora-envelope-gates",
            "defect": "This fire located only 4 of the 5 required named supplier/formulation-"
                      "guide sources carrying an explicit two-part epoxy mix-ratio tolerance "
                      "band (all 4 from one manufacturer family, WEST SYSTEM/Gougeon "
                      "Brothers); a 5th independent source was not found within budget.",
            "proposed_done_criterion": "Locate >=1 additional named supplier TDS or published "
                      "formulation guide (independent of Gougeon Brothers) that states an "
                      "explicit numeric mix-ratio tolerance band, with its license quoted "
                      "verbatim, and fold it into the G3 re-score above.",
        },
    ],
}

canon = json.dumps(diagnostic, indent=2, sort_keys=True).encode()
print(sha(canon))
(Path(__file__).parent / "wdengate_diagnostic.canonical.json").write_bytes(canon)
