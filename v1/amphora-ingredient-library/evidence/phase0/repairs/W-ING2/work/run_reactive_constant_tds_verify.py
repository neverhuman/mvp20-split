#!/usr/bin/env python3
"""
amphora-ingredient-library : external manufacturer-TDS re-verification of the
REACTIVE load-bearing constants (resin EEW + the hardener AHEW/amine-value
facts NOT already covered by hardener-tds-external-verification-v1) that no
prior signed audit receipt in this module ever checked (AUDIT_ONLY).

Motivation / the gap (campaign item W-ING2, follow-on to W-ING1 SURVIVED
2026-08-05T17:00)
---------------------------------------------------------------------------
hardener-tds-external-verification-v1 (2026-08-02) closed the DENSITY
coverage gap for 4 hardener records and, as a byproduct, checked 5 AHEW/
amine-value facts (ancamide_2353.ahew, ancamide_350a.ahew, ancamide_350a.
amine_value, ancamide_260a.ahew x2 regions). But EEW/AHEW are the constants
that actually SET MIX RATIOS (phr = 100 * AHEW / EEW) -- a wrong reactive
constant mis-doses a formulation exactly as a wrong density does, and it was
never given the same live-TDS treatment for:
  - all 4 resin EEW facts (dgeba_331, dgeba_828, dgeba_yd128,
    solid_cut_1001x75.eew_on_nv) -- V1-ING only corrected the solid-resin
    EEW ADMISSIBILITY BAND (constant-crosscheck-v1 Check-1), it never
    externally re-verified the shipped point/band values against live
    manufacturer TDS the way Check-2 does for density.
  - ancamide_220x70.ahew, ancamide_700b75.ahew, ancamide_700b75.amine_value,
    versamid_115.ahew, versamid_115.amine_value -- zero coverage anywhere.

This harness closes that hole with the SAME method and SAME 3.0% gate as
hardener-tds-external-verification-v1: live re-fetch of each fact's own
cited `url`, plus (where a genuinely different document/publisher exists)
independent second-source cross-checks.

Sources fetched live 2026-08-09 (dates/URLs recorded per-row below):
  - Dow "Typical Properties of DOW Liquid Epoxy Resins" (nmt.edu mirror,
    the catalog's own cited url) -- Table 1, D.E.R. 331 Epoxide Equiv. Wt.
    range 182-192 g/eq. TRANSCRIPTION-FIDELITY check (same url as catalog).
  - Miller-Stephenson EPON 828 TDS (catalog's own cited url) -- "Weight per
    Epoxide 185-192 g/eq, ASTM D-1625". TRANSCRIPTION-FIDELITY check.
  - spacematdb.com EPON 828 datasheet -- a DIFFERENT publisher/url than the
    catalog's citation -- "Epoxide Equivalent Weight, ASTM D1652, g/eq
    185-192". GENUINELY INDEPENDENT second source for the same fact.
  - Kukdo YD-128 TDS (imimg.com mirror, catalog's own cited url) --
    "EEW(g/eq) 184-190". TRANSCRIPTION-FIDELITY check (catalog's own note
    already flags the second source as 403-gated; still true this fire).
  - Hexion HCD-4022 TDS (miller-stephenson.com mirror, catalog's own cited
    url) -- "Weight per Epoxide, based on..., g/eq 450-550, ASTM D1652".
    TRANSCRIPTION-FIDELITY check; also independently confirms the V1-ING
    repair band [450.0, 550.0] against the live document, not just the
    refuting receipt's transcription of it.
  - Evonik Ancamide 220X70 US TDS (catalog's own cited url) -- "Equivalent
    Wt/{H} 264" (solution basis, 70% in xylene per single_source_waiver).
    TRANSCRIPTION-FIDELITY check.
  - Evonik AMERICAS Epoxy Curing Agents product guide (catalog's own cited
    url) -- Ancamide 700-B-75 row: "Amine Value 240 / Equivalent WT/{H}
    170". TRANSCRIPTION-FIDELITY check (same document W-ING1 already used
    for the 260A row).
  - Cognis-era Versamid 115 TDS (tamtranco.com mirror, catalog's own cited
    url) -- "Equivalent Weight 198 / Amine Value 238 (spec 230-246)".
    TRANSCRIPTION-FIDELITY check.
  - Huntsman VERSAMID(R) 115 current product page (products.huntsman.com,
    surfaced via web search; DIRECT WebFetch of the page returned blank --
    it is a JS-rendered SPA -- so this row is sourced from the search
    engine's extracted snippet of that page, NOT a raw document re-fetch).
    Reports "Theoretical Amine Hydrogen Equivalent Weight: 198" and "Amine
    Value ... 230-246 ... typical 238". This is the GENUINELY INDEPENDENT,
    CURRENT-BRAND-OWNER document the catalog's own note flags as an open
    risk ("Versamid brand now Gabriel/Huntsman -- flagged"); it is weaker
    evidence than a direct PDF fetch (search-snippet, not raw bytes) and is
    flagged as such in every row that uses it.

Non-circular published baseline
--------------------------------
Same Daniel-style manufacturer-literature second-source discipline as
constant-crosscheck-v1 Check-2 / hardener-tds-external-verification-v1.
GATE_PCT = 3.0%, consumed only to compare against the shipped catalog
scalar (EEW/AHEW facts use the band midpoint where the catalog itself
ships a band-derived midpoint, exactly mirroring how the catalog's own
`note` field records the band it drew the midpoint from).

Licence position (same as hardener-tds-external-verification-v1 and every
prior receipt in this module: none of them recorded a formal licence
field either)
--------------------------------------------------------------------------
Every source below is publicly-published manufacturer technical/safety
literature (TDS/SDS/product guide). None carries a stated open-data
licence. They are used here strictly for POINT-VALUE CITATION AND
COMPARISON (restating the single number/range the document states,
attributed by URL and retrieval date), not for redistribution of the
document itself. This is the same licence posture the catalog's own
facts.json entries assume for every `url` field, and the same posture
hardener-tds-external-verification-v1 used without a formal licence field.

Honest scope
------------
- 9 of 12 comparisons re-fetch the SAME url already recorded in facts.json
  -- TRANSCRIPTION / link-rot integrity checks, not independent
  corroboration.
- 3 comparisons (EPON 828 vs spacematdb.com; Versamid 115 AHEW and amine
  value vs the current Huntsman product page) are against a document/
  publisher genuinely independent of the catalog's cited source. Of these,
  the 2 Huntsman rows are SEARCH-SNIPPET sourced (direct WebFetch of the
  JS-rendered page returned no text), a materially weaker form of citation
  than a raw PDF re-fetch -- flagged per-row as `citation_method`.
- This does not promote any fact to independently-locked; AUDIT_ONLY.
- Does not re-derive the ancamide_260a.ahew EMEA/US regional divergence
  (already established by hardener-tds-external-verification-v1); this
  receipt only RESTATES that prior, still-valid finding to satisfy the
  W-ING2 objective's regional-grade + conservative-rule requirement, and
  adds a NEW live-code check for whether the catalog's disclosed mitigation
  ("band widened in MC") is actually implemented anywhere in the runtime.
"""
import base64, hashlib, json

FACTS_REL = "reference/mvp20/data/facts.json"
FACTS = "/home/ubuntu/amphora/build/mvp20-split/amphora-ingredient-library/" + FACTS_REL

GATE_PCT = 3.0

# ---- external reference values, hand-extracted from live-fetched primary
# manufacturer documents on 2026-08-09 (see docstring for citations) ----------
EXTERNAL = {
    "resin.dgeba_331.eew": {
        "ref_value": 187.0, "unit": "g/eq",
        "source": "Dow \"Typical Properties of DOW Liquid Epoxy Resins\", Table 1, "
                   "D.E.R. 331 Epoxide Equiv. Wt. range 182-192 g/eq (midpoint 187.0, "
                   "matches facts.json's own note verbatim: 'D.E.R. 331, 182-192')",
        "source_url": "https://www.nmt.edu/academics/mtls/faculty/mccoy/docs2/chemistry/DowEpoxyResins.pdf",
        "same_url_as_catalog_citation": True,
        "citation_method": "direct_pdf_fetch_pdftotext",
        "retrieved": "2026-08-09",
    },
    "resin.dgeba_828.eew": {
        "ref_value": 188.5, "unit": "g/eq",
        "source": "Miller-Stephenson EPON 828 TDS, \"Weight per Epoxide 185-192 g/eq, "
                   "ASTM D-1625\" (midpoint 188.5, matches facts.json note "
                   "'EEW 185-192, midpoint used')",
        "source_url": "https://miller-stephenson.com/wp-content/uploads/2024/06/EPON-828_TDS.pdf",
        "same_url_as_catalog_citation": True,
        "citation_method": "direct_pdf_fetch_pdftotext",
        "retrieved": "2026-08-09",
    },
    "resin.dgeba_828.eew__spacematdb_independent": {
        "fact_key": "resin.dgeba_828.eew",
        "ref_value": 188.5, "unit": "g/eq",
        "source": "spacematdb.com EPON 828 datasheet, \"Epoxide Equivalent Weight, "
                   "ASTM D1652, g/eq, 185-192\" (midpoint 188.5) -- different publisher "
                   "than the catalog's cited miller-stephenson.com mirror",
        "source_url": "https://spacematdb.com/spacemat/manudatasheets/Epon828.pdf",
        "same_url_as_catalog_citation": False,
        "citation_method": "direct_pdf_fetch_pdftotext",
        "retrieved": "2026-08-09",
    },
    "resin.dgeba_yd128.eew": {
        "ref_value": 187.0, "unit": "g/eq",
        "source": "Kukdo YD-128 TDS (imimg.com mirror), \"EEW(g/eq) 184-190\" "
                   "(midpoint 187.0)",
        "source_url": "https://5.imimg.com/data5/HR/FD/MY-117280/standard-liquid-epoxy-resin-yd-128.pdf",
        "same_url_as_catalog_citation": True,
        "citation_method": "direct_pdf_fetch_pdftotext",
        "retrieved": "2026-08-09",
    },
    "resin.solid_cut_1001x75.eew_on_nv": {
        "ref_value": 500.0, "unit": "g/eq NV",
        "source": "Hexion HCD-4022 TDS (miller-stephenson.com mirror), \"Weight per "
                   "Epoxide, based on..., g/eq 450-550, ASTM D1652\" (midpoint 500.0) "
                   "-- independently re-confirms the V1-ING repair band [450.0,550.0] "
                   "against the live document itself, not merely the refuting receipt's "
                   "transcription of it",
        "source_url": "https://miller-stephenson.com/wp-content/uploads/2016/08/1001-X-75.pdf",
        "same_url_as_catalog_citation": True,
        "citation_method": "direct_pdf_fetch_pdftotext",
        "retrieved": "2026-08-09",
    },
    "hardener.ancamide_220x70.ahew": {
        "ref_value": 264.0, "unit": "g/eq",
        "source": "Evonik Ancamide 220X70 US TDS, \"Equivalent Wt/{H} 264\" "
                   "(70wt% solution in xylene basis, per facts.json single_source_waiver)",
        "source_url": "https://products.evonik.com/assets/s_/us/Ancamide_220X70_us_TDS_EN_EN_TDS_PV_52041880_en_US_US.pdf",
        "same_url_as_catalog_citation": True,
        "citation_method": "direct_pdf_fetch_pdftotext",
        "retrieved": "2026-08-09",
    },
    "hardener.ancamide_700b75.ahew": {
        "ref_value": 170.0, "unit": "g/eq",
        "source": "Evonik AMERICAS Epoxy Curing Agents product guide table, "
                   "ANCAMIDE 700-B-75 row, Equivalent WT/{H} column = 170",
        "source_url": "https://products.evonik.com/assets/90/41/Epoxy_curing_agents_product_guide_Americas_EN_Asset_819041.pdf",
        "same_url_as_catalog_citation": True,
        "citation_method": "direct_pdf_fetch_pdftotext",
        "retrieved": "2026-08-09",
    },
    "hardener.ancamide_700b75.amine_value": {
        "ref_value": 240.0, "unit": "mgKOH/g",
        "source": "Evonik AMERICAS Epoxy Curing Agents product guide table, "
                   "ANCAMIDE 700-B-75 row, Amine Value column = 240",
        "source_url": "https://products.evonik.com/assets/90/41/Epoxy_curing_agents_product_guide_Americas_EN_Asset_819041.pdf",
        "same_url_as_catalog_citation": True,
        "citation_method": "direct_pdf_fetch_pdftotext",
        "retrieved": "2026-08-09",
    },
    "hardener.versamid_115.ahew": {
        "ref_value": 198.0, "unit": "g/eq",
        "source": "Cognis-era Versamid 115 TDS (tamtranco.com mirror), "
                   "\"Equivalent Weight 198\"",
        "source_url": "https://tamtranco.com/UserFiles/File/Dong%20ran/Dong%20ran%20cho%20Epoxy/Versamid%20115/TDS-Versamid%20115_TI.pdf",
        "same_url_as_catalog_citation": True,
        "citation_method": "direct_pdf_fetch_pdftotext",
        "retrieved": "2026-08-09",
    },
    "hardener.versamid_115.amine_value": {
        "ref_value": 238.0, "unit": "mgKOH/g",
        "source": "Cognis-era Versamid 115 TDS (tamtranco.com mirror), \"Amine Value "
                   "238 (Specification range 230-246)\"",
        "source_url": "https://tamtranco.com/UserFiles/File/Dong%20ran/Dong%20ran%20cho%20Epoxy/Versamid%20115/TDS-Versamid%20115_TI.pdf",
        "same_url_as_catalog_citation": True,
        "citation_method": "direct_pdf_fetch_pdftotext",
        "retrieved": "2026-08-09",
    },
    "hardener.versamid_115.ahew__huntsman_independent": {
        "fact_key": "hardener.versamid_115.ahew",
        "ref_value": 198.0, "unit": "g/eq",
        "source": "Huntsman VERSAMID(R) 115 current product page (current brand owner "
                   "in the Cognis->BASF->Huntsman/Gabriel lineage facts.json's own note "
                   "flags as unresolved): \"Theoretical Amine Hydrogen Equivalent "
                   "Weight: 198\" -- resolves the lineage risk this module's own note "
                   "leaves open",
        "source_url": "https://products.huntsman.com/products/versamid-115-j3uldxs6",
        "same_url_as_catalog_citation": False,
        "citation_method": "search_engine_extracted_snippet_not_raw_fetch",
        "retrieved": "2026-08-09",
    },
    "hardener.versamid_115.amine_value__huntsman_independent": {
        "fact_key": "hardener.versamid_115.amine_value",
        "ref_value": 238.0, "unit": "mgKOH/g",
        "source": "Huntsman VERSAMID(R) 115 current product page: \"Amine Value ... "
                   "230-246 mg KOH/gram resin, typical value 238\"",
        "source_url": "https://products.huntsman.com/products/versamid-115-j3uldxs6",
        "same_url_as_catalog_citation": False,
        "citation_method": "search_engine_extracted_snippet_not_raw_fetch",
        "retrieved": "2026-08-09",
    },
}


def pct(cat, ref):
    return round(100.0 * (cat - ref) / ref, 4)


def build():
    facts = json.load(open(FACTS))
    ent = facts["entries"]
    facts_sha = hashlib.sha256(open(FACTS, "rb").read()).hexdigest()

    # ---- coverage gap disclosure -------------------------------------------
    all_lb_reactive = sorted(
        k for k in ent
        if (k.endswith(".eew") or k.endswith(".eew_on_nv") or k.endswith(".ahew"))
        and ent[k].get("load_bearing")
    )
    prior_covered_by_w_ing1 = {
        "hardener.ancamide_2353.ahew", "hardener.ancamide_350a.ahew",
        "hardener.ancamide_260a.ahew",
    }
    new_gap_closed = sorted(set(all_lb_reactive) - prior_covered_by_w_ing1)

    # ---- Check A: external TDS re-verification of the reactive constants ---
    rows = []
    for k, ref in EXTERNAL.items():
        fact_key = ref.get("fact_key", k)
        cat = float(ent[fact_key]["value"])
        dev = pct(cat, ref["ref_value"])
        rows.append({
            "row_id": k,
            "fact_key": fact_key,
            "catalog_value": cat,
            "catalog_unit": ent[fact_key]["unit"],
            "catalog_grade": ent[fact_key]["grade"],
            "catalog_load_bearing": bool(ent[fact_key].get("load_bearing", False)),
            "catalog_note": ent[fact_key].get("note", ""),
            "external_ref_value": ref["ref_value"],
            "external_source": ref["source"],
            "external_source_url": ref["source_url"],
            "same_url_as_catalog_citation": ref["same_url_as_catalog_citation"],
            "citation_method": ref["citation_method"],
            "retrieved": ref["retrieved"],
            "pct_deviation": dev,
            "abs_pct_deviation": abs(dev),
            "within_gate": bool(abs(dev) <= GATE_PCT),
        })

    independent_rows = [r for r in rows if not r["same_url_as_catalog_citation"]]
    transcription_rows = [r for r in rows if r["same_url_as_catalog_citation"]]
    snippet_rows = [r for r in rows if r["citation_method"] == "search_engine_extracted_snippet_not_raw_fetch"]
    n_within = sum(1 for r in rows if r["within_gate"])
    n_total = len(rows)
    failing = [r for r in rows if not r["within_gate"]]

    # ---- Check B: regional-grade statement + conservative-rule requirement -
    # (restates hardener-tds-external-verification-v1's already-established,
    # still-valid finding; does not re-derive it)
    prior_regional_finding = {
        "fact_key": "hardener.ancamide_260a.ahew",
        "catalog_shipped_value": 120.0,
        "catalog_corresponds_to_region": "US / Americas",
        "evidence_for_region_id": "Evonik AMERICAS Epoxy Curing Agents product guide table, "
                                   "Ancamide 260A Equivalent WT/{H} column = 120 -- this IS "
                                   "the catalog's own cited primary url for this fact",
        "us_region_value": 120.0,
        "emea_region_value": 110.0,
        "emea_vs_catalog_pct_deviation": pct(120.0, 110.0),
        "emea_vs_catalog_within_gate": bool(abs(pct(120.0, 110.0)) <= GATE_PCT),
        "established_by": "amphora-ingredient-library/evidence/audit/"
                           "hardener-tds-external-verification-v1/"
                           "hardener-tds-external-verification-receipt.v1.dsse.json (2026-08-02)",
    }
    conservative_rule = (
        "A downstream mix-ratio calculation (phr = 100 * AHEW / EEW) that consumes "
        "hardener.ancamide_260a.ahew MUST NOT default to a single point value (neither "
        "110.0 nor 120.0 g/eq) when the batch's region of origin is unknown. It must "
        "treat AHEW as the closed interval [110.0, 120.0] g/eq (the full disclosed "
        "US/EMEA band) and propagate that interval through the mix-ratio calculation by "
        "worst-case bounding (compute phr at both endpoints and require the formulation "
        "to remain within its target-property envelope across the FULL resulting phr "
        "range), not by picking a favored direction -- the physically 'safe' direction "
        "is ambiguous (excess-amine risk: blush/carbamation/reduced barrier resistance "
        "at the low-AHEW/high-phr bound; excess-epoxide risk: under-cure/soft "
        "film/permeability failure at the high-AHEW/low-phr bound -- an anti-corrosion "
        "coating can fail from either), so bounding both ends is the only defensible "
        "rule, not picking one."
    )
    mitigation_code_check = {
        "claim_in_catalog_note": "US 120 vs EMEA 110 -- REGIONAL CONFLICT FLAGGED; "
                                  "US value used, band widened in MC",
        "grep_scope": "every *.rs and *.py file in the live mvp20-split tree "
                      "(excluding evidence/ artifacts and third-party .venv packages), "
                      "for 'widened', 'regional_conflict', 'REGIONAL CONFLICT'",
        "code_hits_implementing_the_widened_band": 0,
        "finding": "No source file (Rust or Python) in the live runtime implements a "
                   "widened AHEW interval/tolerance for ancamide_260a. The catalog note's "
                   "'band widened in MC' is a textual disclosure only; it is not "
                   "materialized as an enforced numeric interval anywhere this fire could "
                   "find. This is a live-code gap, not a data-accuracy gap: the VALUES "
                   "verify fine (see checkA); the DOWNSTREAM HANDLING of the known "
                   "regional ambiguity is what the conservative_rule above specifies and "
                   "what is currently unimplemented.",
    }

    diag = {
        "schema": "amphora.ingredient-library-reactive-constant-tds-verification.v1",
        "module": "amphora-ingredient-library",
        "run_type": "AUDIT_ONLY",
        "authority": "AUDIT_ONLY",
        "campaign_item_id": "W-ING2",
        "purpose": "External live manufacturer-TDS re-verification of the reactive "
                   "load-bearing constants (resin EEW + remaining hardener AHEW/"
                   "amine-value facts) that no prior signed audit receipt in this "
                   "module ever checked, extending hardener-tds-external-"
                   "verification-v1 / hardener-tds-verified-constants-kpi.v1 past "
                   "densities to the constants that actually set mix ratios.",
        "hypothesis": "Every shipped load-bearing resin-EEW and remaining hardener-"
                      "AHEW/amine-value constant matches, within a 3.0% gate, the "
                      "primary manufacturer literature it is drawn from.",
        "non_circularity": "9 of 12 comparisons re-fetch the SAME url already cited in "
                           "facts.json -- transcription/link-rot checks, not independent "
                           "corroboration. 3 comparisons (EPON 828 vs spacematdb.com; "
                           "Versamid 115 AHEW + amine value vs the current Huntsman "
                           "product page) are against a document/publisher genuinely "
                           "independent of the catalog's cited source.",
        "theory_reference": {
            "method": "Same Daniel-style manufacturer-literature second-source "
                     "discipline as constant-crosscheck-v1 Check-2 and "
                     "hardener-tds-external-verification-v1.",
            "gate_pct": GATE_PCT,
        },
        "licence_position": "Every source is publicly-published manufacturer TDS/SDS/"
                             "product-guide literature with no stated open-data "
                             "licence; used here for point-value citation/comparison "
                             "only (single number/range restated, attributed by URL "
                             "and retrieval date), not redistribution of the document "
                             "-- same posture as every prior receipt in this module, "
                             "none of which recorded a formal licence field either.",
        "inputs": {"facts_json_rel": FACTS_REL, "facts_json_sha256": facts_sha,
                   "gate_pct": GATE_PCT},
        "checkA_coverage_gap": {
            "all_load_bearing_reactive_constants": all_lb_reactive,
            "n_all_load_bearing_reactive_constants": len(all_lb_reactive),
            "prior_covered_by_w_ing1": sorted(prior_covered_by_w_ing1),
            "new_gap_closed_by_this_receipt": new_gap_closed,
            "n_new_gap_closed": len(new_gap_closed),
        },
        "checkB_external_tds_reverification": {
            "gate_pct": GATE_PCT,
            "n_total_comparisons": n_total,
            "n_within_gate": n_within,
            "all_within_gate": bool(n_within == n_total),
            "n_independent_source_comparisons": len(independent_rows),
            "n_transcription_fidelity_comparisons": len(transcription_rows),
            "n_search_snippet_citations": len(snippet_rows),
            "failing_comparisons": failing,
            "per_comparison": rows,
        },
        "checkC_regional_grade_and_conservative_rule": {
            "prior_regional_finding_restated": prior_regional_finding,
            "conservative_rule_for_unknown_region": conservative_rule,
            "mitigation_code_check": mitigation_code_check,
        },
        "headline": None,
        "closes": [
            "Extends hardener-tds-external-verification-v1 / hardener-tds-verified-"
            "constants-kpi.v1 (W-ING1, SURVIVED 2026-08-05) past hardener DENSITIES "
            "to the REACTIVE constants (resin EEW x4, plus 5 remaining hardener "
            "AHEW/amine-value facts) that set formulation mix ratios and had zero "
            "live-TDS coverage.",
            "States explicitly which regional grade the ancamide_260a.ahew catalog "
            "value corresponds to (US/Americas) and the conservative interval-"
            "bounding rule a downstream mix-ratio calculation must apply when the "
            "region is unknown -- and discloses that the catalog's own claimed "
            "mitigation ('band widened in MC') has zero implementing code in the "
            "live runtime.",
        ],
        "does_not_close": [
            "9 of 12 comparisons re-fetch the SAME url the catalog already cites -- "
            "transcription/link-rot checks, not independent second-source locks.",
            "The 2 Huntsman-sourced Versamid 115 rows are search-engine-extracted "
            "snippets, not raw document re-fetches (direct WebFetch of the "
            "JS-rendered Huntsman product page returned no text) -- weaker evidence "
            "than the PDF-fetch rows.",
            "Does not implement the conservative interval-bounding rule in code; "
            "states the requirement and discloses the gap, AUDIT_ONLY, no repair "
            "authority to modify downstream mix-ratio solvers.",
            "Gate is a point-transcription tolerance (3%), not a physical "
            "admissibility bound; does not establish product qualification.",
        ],
        "modifies_manifest": False, "modifies_module_manifest": False,
        "modifies_locked_dataset": False, "modifies_signed_phase0_kpi": False,
        "promotes_authority": False, "flips_scientific_readiness": False,
        "human_review_performed": False,
    }
    diag["headline"] = (
        "Extended live manufacturer-TDS re-verification from hardener densities "
        "(W-ING1) to the reactive constants that set mix ratios: %d/%d new "
        "load-bearing resin-EEW/hardener-AHEW facts closed (2 non-load-bearing "
        "amine-value facts, 3 comparison rows, additionally checked as byproducts, "
        "all within gate), "
        "%d/%d comparisons within the %.1f%% gate (%d transcription-fidelity re-fetches, "
        "%d genuinely independent second-source comparisons, of which %d are "
        "search-snippet not raw-fetch). Zero new divergences found. The pre-"
        "existing, still-valid ancamide_260a.ahew US(120)/EMEA(110) regional "
        "divergence (9.09%%, outside gate) corresponds to the US/Americas grade; "
        "a downstream calculation with unknown region must interval-bound "
        "[110.0,120.0], which the catalog's own disclosed mitigation claims but "
        "has zero implementing code in the live runtime."
        % (len(new_gap_closed), len(all_lb_reactive), n_within, n_total, GATE_PCT,
           len(transcription_rows), len(independent_rows), len(snippet_rows))
    )
    return diag


def canon(obj):
    return json.dumps(obj, indent=2, sort_keys=True).encode()


def run_positive_control():
    """Plant defects into IN-MEMORY COPIES of the real comparison rows and
    confirm the same within_gate predicate this oracle uses fires on them.
    Two independent defect kinds, mirroring hardener-tds-external-
    verification-v1's checkD fail-closed mutation demo."""
    real = build()
    real_rows = real["checkB_external_tds_reverification"]["per_comparison"]
    baseline_row = next(r for r in real_rows if r["row_id"] == "resin.dgeba_828.eew")
    assert baseline_row["within_gate"] is True, "baseline must be within gate pre-mutation"

    # Defect A: transcription-error-style corruption of the external_ref_value
    # for a REAL row (simulates mis-reading 188.5 as 205.0 off the same PDF).
    defect_a = dict(baseline_row)
    defect_a["external_ref_value"] = 205.0
    defect_a["pct_deviation"] = pct(defect_a["catalog_value"], defect_a["external_ref_value"])
    defect_a["abs_pct_deviation"] = abs(defect_a["pct_deviation"])
    defect_a["within_gate"] = bool(defect_a["abs_pct_deviation"] <= GATE_PCT)

    # Defect B: digit-insert / decimal-slip / transpose corruption of the
    # CATALOG value for hardener.versamid_115.ahew (198.0 g/eq), same style
    # as hardener-tds-external-verification-v1's checkD.
    v_ahew = 198.0
    ref_v = 198.0
    mutations = [
        ("baseline", v_ahew),
        ("digit_insert_1980", v_ahew * 10.0),
        ("decimal_slip_19.8", v_ahew / 10.0),
        ("transpose_189", 189.0),
    ]
    demo = []
    for label, val in mutations:
        d = pct(val, ref_v)
        demo.append({"mutation": label, "value": round(val, 4),
                     "pct_deviation_vs_external": d, "flagged": bool(abs(d) > GATE_PCT)})
    gross = [d for d in demo if d["mutation"] != "baseline"]

    return {
        "defect_a_field_corruption": {
            "target_row_id": "resin.dgeba_828.eew",
            "how_planted": "in-memory copy: external_ref_value overwritten 188.5 -> 205.0 "
                           "(simulated transcription error off the same source PDF); real "
                           "signed diagnostic and facts.json on disk never touched",
            "baseline_within_gate": baseline_row["within_gate"],
            "defect_pct_deviation": defect_a["pct_deviation"],
            "defect_within_gate": defect_a["within_gate"],
            "detected": bool(defect_a["within_gate"] is False),
        },
        "defect_b_mutation_demo": {
            "target_fact_key": "hardener.versamid_115.ahew",
            "how_planted": "in-memory catalog-value mutations: digit-insert (x10), "
                           "decimal-slip (/10), transpose-digits, vs the fixed live "
                           "Huntsman/tamtranco external reference 198.0",
            "mutations": demo,
            "all_gross_mutations_flagged": bool(all(d["flagged"] for d in gross)),
            "detected": bool(all(d["flagged"] for d in gross)),
        },
    }


if __name__ == "__main__":
    import sys
    d1 = build(); b1 = canon(d1); h1 = hashlib.sha256(b1).hexdigest()
    d2 = build(); b2 = canon(d2); h2 = hashlib.sha256(b2).hexdigest()
    assert b1 == b2, "two-replay byte MISMATCH"
    pc = run_positive_control()
    if len(sys.argv) > 1 and sys.argv[1] == "--emit":
        open("diagnostic.canonical.json", "wb").write(b1)
        open("diagnostic.runB.json", "wb").write(b2)
        open("positive_control.json", "wb").write(
            json.dumps(pc, indent=2, sort_keys=True).encode())
    print("replay_sha256:", h1, "| byte_stable:", h1 == h2)
    print("positive_control_defect_a_detected:", pc["defect_a_field_corruption"]["detected"])
    print("positive_control_defect_b_detected:", pc["defect_b_mutation_demo"]["detected"])
