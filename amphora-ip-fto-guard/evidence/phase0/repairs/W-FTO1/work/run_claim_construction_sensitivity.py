#!/usr/bin/env python3
"""Claim-construction sensitivity attack on amphora-ip-fto-guard's claim-charted
families (patent_landscape.json families n=1,2,3,4,5,26; independent_claim_chart.charted=true).

Claim under attack: "The FTO screen's conclusions are robust to reasonable
variation in how patent claims are construed."

For each charted family, this script:
  1. Re-derives the REAL, independently-published claim-1 text from the same
     hash-pinned Google Patents snapshots already used and SHA-pinned by the
     prior claim-chart-provenance-v1 audit (reused read-only; not re-fetched).
  2. Identifies the specific claim term(s) the fixture's `why` field relies on
     to ground its `reads_on_ours: NO` conclusion.
  3. Applies THREE claim constructions a competent practitioner could adopt:
       - narrow: the fixture's own implicit reading (bare numeric/threshold,
         ignoring any hedge word in the real claim).
       - plain: ordinary POSA meaning, including a modest, industry-standard
         tolerance for any "about"/hedge qualifier actually present in the
         claim (informed by ASTM volume-solids method reproducibility).
       - broad: the broadest reading a cautious FTO practitioner would adopt,
         informed by the patent's OWN specification language (lexicography /
         disclosed embodiment ranges) for the same term.
  4. Reports FLIP (the bright-line reads_on_ours=NO stops being the only
     reasonable outcome) or NO_FLIP (every construction agrees) per family.

Family 26 (EP2653485A2 / Hempel) is EXCLUDED from the flip/no-flip population:
its charted `key_elements` were already found in evidence/audit/claim-chart-
provenance-v1 (REFUTED, ledger 2026-08-03T15:08:37Z) to include a fabricated
element not present in the real claim text. Layering a construction-sensitivity
verdict on an already-fabricated chart would be circular; it is reported as
EXCLUDED_MOOT_PRIOR_PROVENANCE_DEFECT, not counted toward SURVIVED/REFUTED.

This is AUDIT_ONLY. It re-derives from public patent text already on disk; it
performs no new fetch, modifies no fixture, and renders no legal opinion.
"""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-ip-fto-guard"
RAW = MOD / "evidence/audit/claim-chart-provenance-v1/raw"
PROV_RECEIPT = MOD / "evidence/audit/claim-chart-provenance-v1/claim-chart-provenance-receipt.v1.dsse.json"
LANDSCAPE = MOD / "reference/mvp20/data/patent_landscape.json"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def strip_html(raw_bytes):
    import html as ihtml
    text = re.sub(rb"<[^>]+>", b" ", raw_bytes).decode("utf-8", errors="ignore")
    text = ihtml.unescape(text)
    return re.sub(r"\s+", " ", text)


PINNED_RAW_SHA256 = {
    "EP2653485A2.html": "54ea48f9eb65fbd93fdd1b479a4fd1c410ad1f1c74c96e22470b983c1c28cd0e",
    "EP2931822A2.html": "b7831640e0c5585356d774043e62174e1d08c7f1947eab5a0f4b4c4ff05a1a15",
    "EP3328938B1.html": "2be62772cd5b6e74c1c35f093638da55001879bd025bb54bc0252717fa567a11",
    "US5059640A.html": "dbe292c5d6054a1e73ecc8903d5e4d5c515cc011640c6cbb55fdedb65edee4f2",
    "WO2013159277A1.html": "14cfaa8dcc87f0065e2da9b85f159262adfd83fa95bd5f57f9df339c6e231d3a",
    "WO2016187380A1.html": "f8dc254181e4b5171f6678009d1f6f65b17c0d7e9961fcd6127c4d93b1b735b2",
}


def load_verified(fname):
    b = (RAW / fname).read_bytes()
    got = sha(b)
    pin = PINNED_RAW_SHA256[fname]
    assert got == pin, f"raw snapshot hash drift for {fname}: {got} != {pin}"
    return strip_html(b), got


def extract(text, start, end_marker, max_len=1400):
    idx = text.find(start)
    assert idx != -1, f"anchor not found: {start!r}"
    end = text.find(end_marker, idx)
    if end == -1 or end - idx > max_len:
        end = idx + max_len
    return text[idx:end].strip()


landscape = json.loads(LANDSCAPE.read_text())
fixture_sha256 = sha(LANDSCAPE.read_bytes())
families_by_n = {f["n"]: f for f in landscape["families"] if f.get("independent_claim_chart", {}).get("charted")}
assert sorted(families_by_n) == [1, 2, 3, 4, 5, 26], sorted(families_by_n)

results = []

# ---------------------------------------------------------------------------
# n=1 WO2016187380A1 -- reactive-compatibilizer + volume-solids coating claim
# ---------------------------------------------------------------------------
text1, h1 = load_verified("WO2016187380A1.html")
claim1_real = extract(
    text1,
    "What is claimed is: 1 .",
    "2. The curable composition of claim 1",
)
spec_range_disclosure = extract(
    text1,
    "the high volume solids of the curable composition may range from about 50",
    "the high PVC of the curable composition",
)
our_baseline = landscape["our_primer_assumed"]
fx1 = families_by_n[1]

constructions_1 = [
    {
        "name": "narrow (fixture-implicit)",
        "basis": "Fixture `why` field treats the limitation as a bare threshold: 'our VS ~65% (<70%)'.",
        "construed_scope": "volume solids content > 70.0% exactly, no tolerance",
        "ours_within_scope": False,
        "reads_on_ours_under_this_construction": "NO",
    },
    {
        "name": "plain/ordinary (POSA, hedge honored, modest tolerance)",
        "basis": (
            "Real claim 1 text (independently re-derived, quoted below) says "
            "'volume solids content of greater than about 70 percent', not a bare "
            "'70 percent'. A POSA applying ordinary claim-construction practice to "
            "an 'about'-qualified numeric limitation gives it a modest tolerance "
            "tied to the field's own measurement reproducibility (ASTM D2697 / "
            "D5201 volume-solids determinations are typically reproducible to a "
            "few points, not to +/-5 points)."
        ),
        "construed_scope": "volume solids content roughly >= 67-68% (small 'about' tolerance around 70%)",
        "ours_within_scope": False,
        "reads_on_ours_under_this_construction": "NO",
    },
    {
        "name": "broad / specification-informed, practitioner-cautious",
        "basis": (
            "The specification's own general description of the invention "
            "(quoted below) discloses OVERLAPPING 'high volume solids' embodiment "
            "ranges for the same concept the claim numerically pins at 'about 70 "
            "percent': 'about 50% to about 100%', '60% to about 95%', and '70% to "
            "about 90%'. FTO counsel construing an ambiguous, hedge-qualified "
            "numeric term is expected to adopt the reading LEAST favorable to a "
            "clean-exclusion conclusion (i.e. the broadest reading a competent "
            "adversary could press), not the reading most convenient for the "
            "screen. Read in light of the spec's own lower embodiment floors for "
            "the identical 'high volume solids' concept, 'about 70 percent' is "
            "not demonstrably a hard, isolated 70.0% cutoff -- a coating at ~65% "
            "VS sits inside two of the three disclosed embodiment ranges for the "
            "same invention concept ('about 50% to about 100%' and '60% to about "
            "95%'), so it cannot be confidently excluded on this limitation alone "
            "without further quantitative work the fixture does not do."
        ),
        "construed_scope": "volume solids content within the invention's own disclosed 'high volume solids' embodiment space (as low as ~50-60%), not a rigid 70.0% line",
        "ours_within_scope": "AMBIGUOUS / NOT CLEARLY EXCLUDED",
        "reads_on_ours_under_this_construction": "UNCERTAIN (not a confident NO)",
    },
]

flip_1 = any(c["reads_on_ours_under_this_construction"] not in ("NO",) for c in constructions_1)

results.append({
    "n": 1,
    "doc": fx1["doc_read"],
    "raw_snapshot_sha256": h1,
    "fixture_reads_on_ours": fx1["reads_on_ours"],
    "fixture_why": fx1["why"],
    "our_baseline_assumed": our_baseline,
    "grounding_term_tested": "volume solids content of greater than about 70 percent (claim 1)",
    "real_claim1_excerpt": claim1_real,
    "specification_disclosure_excerpt": spec_range_disclosure,
    "note_on_other_limitation": (
        "Family 1's NO also rests on a second, independent limitation ('no distinct "
        "reactive polar compatibilizer', claim-1 component (c)). That element was "
        "separately checked: claim 1 requires component (c) as a THIRD, distinct "
        "ingredient beyond (a) epoxy and (b) polyamide hardener; our_primer_assumed "
        "lists epoxy + polyamide hardener + silica extender + iron-oxide color + "
        "solvent -- no third reactive/polar component under any construction tested "
        "(narrow, plain, or broad functional reading of 'reactive compatibilizer "
        "agent ... having at least one polar functionality'). This element does NOT "
        "flip; only the volume-solids element does."
    ),
    "constructions": constructions_1,
    "flip": flip_1,
    "verdict": "FLIP - NOT ROBUST" if flip_1 else "NO_FLIP - ROBUST",
})

# ---------------------------------------------------------------------------
# n=2 EP3328938B1 -- micronized polyamide rheology-additive composition claim
# ---------------------------------------------------------------------------
text2, h2 = load_verified("EP3328938B1.html")
claim1_real_2 = extract(
    text2,
    "Claims ( 17 ) A polyamide composition consisting essentially of",
    "The polyamide composition according to claim 1, wherein the diamine is ethylene diamine.",
)
fx2 = families_by_n[2]
constructions_2 = [
    {
        "name": "narrow (fixture-implicit)",
        "basis": "Fixture: 'a specific micronized polyamide RHEOLOGY additive, not a curing agent'.",
        "construed_scope": "solid powder, median particle size 1-10 um, specific diamine/monoacid/fatty-acid triad",
        "ours_within_scope": False,
        "reads_on_ours_under_this_construction": "NO",
    },
    {
        "name": "plain/ordinary (POSA)",
        "basis": (
            "Real claim 1 (quoted below) requires 'a median particle size ranging "
            "from 1 um to 10 um'. A liquid curative has no median particle size in "
            "the ordinary sense a POSA in coatings/rheology additives would apply "
            "the term (a solid-particulate distribution measurement); the term does "
            "not read on a bulk liquid under its plain meaning."
        ),
        "construed_scope": "solid/powder form only",
        "ours_within_scope": False,
        "reads_on_ours_under_this_construction": "NO",
    },
    {
        "name": "broad / practitioner-cautious",
        "basis": (
            "Even reading 'particle size' as broadly as the specification allows "
            "(dispersed/emulsified droplet form is discussed elsewhere in the spec "
            "for handling), our_primer_assumed's 'dimer-acid reactive polyamide' is "
            "compositionally a condensation product of DIMER fatty acids with "
            "polyamines -- chemically outside the claim's own closed acid set "
            "(diamine limited to ethylene/hexamethylene diamine; monoacid limited "
            "to acetic/propionic; fatty acid limited to 12-hydroxystearic/"
            "lesquerolic). 'Consisting essentially of' this specific triad forecloses "
            "a broad reading that would sweep in a structurally different dimer-acid "
            "curative."
        ),
        "construed_scope": "closed triad (specified diamine + specified monoacid + specified fatty acid), any form",
        "ours_within_scope": False,
        "reads_on_ours_under_this_construction": "NO",
    },
]
flip_2 = any(c["reads_on_ours_under_this_construction"] != "NO" for c in constructions_2)
results.append({
    "n": 2, "doc": fx2["doc_read"], "raw_snapshot_sha256": h2,
    "fixture_reads_on_ours": fx2["reads_on_ours"], "fixture_why": fx2["why"],
    "our_baseline_assumed": our_baseline,
    "grounding_term_tested": "median particle size 1-10 um + closed diamine/monoacid/fatty-acid triad (claim 1)",
    "real_claim1_excerpt": claim1_real_2,
    "specification_disclosure_excerpt": None,
    "constructions": constructions_2, "flip": flip_2,
    "verdict": "FLIP - NOT ROBUST" if flip_2 else "NO_FLIP - ROBUST",
})

# ---------------------------------------------------------------------------
# n=3 EP2931822A2 / US2015-0329739A1 family -- CHDM epoxy blend claim
# ---------------------------------------------------------------------------
text3, h3 = load_verified("EP2931822A2.html")
claim1_real_3 = extract(
    text3,
    "ted to a curable coating composition including: a blend of at least two or more epoxy resins",
    "Another aspect of the present invention",
)
fx3 = families_by_n[3]
constructions_3 = [
    {
        "name": "narrow (fixture-implicit)", "basis": "Fixture: 'we use standard DGEBA only, no CHDM epoxy'.",
        "construed_scope": "CHDM (1,4-cyclohexanedimethanol) diglycidyl ether epoxy resin specifically",
        "ours_within_scope": False, "reads_on_ours_under_this_construction": "NO",
    },
    {
        "name": "plain/ordinary (POSA)",
        "basis": "CHDM is a specific, named aliphatic diol (1,4-cyclohexanedimethanol); DGEBA's backbone is bisphenol-A, an aromatic diphenol. The terms name chemically non-overlapping monomer classes.",
        "construed_scope": "same as narrow -- the term is a specific chemical name, not a functional term",
        "ours_within_scope": False, "reads_on_ours_under_this_construction": "NO",
    },
    {
        "name": "broad / practitioner-cautious",
        "basis": "Even the broadest reading in the spec ('CHDM epoxy resin may include a mixture of CHDM diglycidylether with other compounds such as impurities') stays anchored to CHDM as the defining monomer; it does not extend to bisphenol-A-based DGEBA under any disclosed embodiment.",
        "construed_scope": "CHDM-monomer-containing epoxy resins, including minor-impurity variants -- still excludes DGEBA",
        "ours_within_scope": False, "reads_on_ours_under_this_construction": "NO",
    },
]
flip_3 = any(c["reads_on_ours_under_this_construction"] != "NO" for c in constructions_3)
results.append({
    "n": 3, "doc": fx3["doc_read"], "raw_snapshot_sha256": h3,
    "fixture_reads_on_ours": fx3["reads_on_ours"], "fixture_why": fx3["why"],
    "our_baseline_assumed": our_baseline,
    "grounding_term_tested": "CHDM (1,4-cyclohexanedimethanol) epoxy resin component (claim 1)",
    "real_claim1_excerpt": claim1_real_3,
    "specification_disclosure_excerpt": None,
    "constructions": constructions_3, "flip": flip_3,
    "verdict": "FLIP - NOT ROBUST" if flip_3 else "NO_FLIP - ROBUST",
})

# ---------------------------------------------------------------------------
# n=4 WO2013159277A1 -- chlorinated polyolefin terpolymer overcoatability claim
# ---------------------------------------------------------------------------
text4, h4 = load_verified("WO2013159277A1.html")
claim1_real_4 = extract(
    text4,
    "or a mixture thereof; b) from 1 wt.% to 20 wt.% a chlorinated polyolefin based terpolymer; and c) from 1 wt.%) to 40 wt.% a curing agent. 2.",
    "2. The curable compos",
)
fx4 = families_by_n[4]
constructions_4 = [
    {
        "name": "narrow (fixture-implicit)", "basis": "Fixture: 'no chlorinated polyolefin terpolymer in our primer'.",
        "construed_scope": "poly(vinyl chloride-vinyl alcohol-vinyl acetate) or poly(vinyl chloride-vinyl acetate-maleic acid) terpolymer",
        "ours_within_scope": False, "reads_on_ours_under_this_construction": "NO",
    },
    {
        "name": "plain/ordinary (POSA)",
        "basis": "Spec names commercial exemplars (CONVINYL G-75, C-47) and gives explicit monomer-unit mole-percent ranges; the term is understood in the field as a specific chlorine-bearing vinyl terpolymer class, not any halogen-containing additive.",
        "construed_scope": "same as narrow", "ours_within_scope": False,
        "reads_on_ours_under_this_construction": "NO",
    },
    {
        "name": "broad / practitioner-cautious",
        "basis": "Even under the broadest disclosed variant (either named terpolymer chemistry, 1-20 wt% loading window), the limitation requires a chlorine-bearing terpolymer component to be PRESENT; our_primer_assumed contains no chlorinated component of any kind (DGEBA + dimer-acid polyamide + silica + iron oxide + naphtha/butanol). Absence of any candidate ingredient forecloses a flip regardless of how broadly the term is read.",
        "construed_scope": "any chlorine-bearing polyolefin terpolymer at 1-20 wt%", "ours_within_scope": False,
        "reads_on_ours_under_this_construction": "NO",
    },
]
flip_4 = any(c["reads_on_ours_under_this_construction"] != "NO" for c in constructions_4)
results.append({
    "n": 4, "doc": fx4["doc_read"], "raw_snapshot_sha256": h4,
    "fixture_reads_on_ours": fx4["reads_on_ours"], "fixture_why": fx4["why"],
    "our_baseline_assumed": our_baseline,
    "grounding_term_tested": "chlorinated polyolefin based terpolymer, 1-20 wt% (claim 1)",
    "real_claim1_excerpt": claim1_real_4,
    "specification_disclosure_excerpt": None,
    "constructions": constructions_4, "flip": flip_4,
    "verdict": "FLIP - NOT ROBUST" if flip_4 else "NO_FLIP - ROBUST",
})

# ---------------------------------------------------------------------------
# n=5 US5059640A -- zinc phosphate/molybdate/benzoate inhibitor triad claim
# ---------------------------------------------------------------------------
text5, h5 = load_verified("US5059640A.html")
claim1_real_5 = extract(
    text5,
    "consisting essentially of about 10 to 120 parts by weight of at least one zinc phosphate",
    "all three of the zinc salts",
)
fx5 = families_by_n[5]
constructions_5 = [
    {
        "name": "narrow (fixture-implicit)",
        "basis": "Fixture: 'primary has no zinc phosphate; Enhanced-65 has zinc phosphate alone, with no molybdate/benzoate'.",
        "construed_scope": "consisting essentially of ALL THREE: zinc phosphate + zinc molybdate + zinc benzoate salt, each within its stated parts-by-weight window",
        "ours_within_scope": False, "reads_on_ours_under_this_construction": "NO",
    },
    {
        "name": "plain/ordinary (POSA)",
        "basis": "'Consisting essentially of' (a recognized intermediate transitional phrase) still requires the basic and novel characteristic -- here, presence of all three named zinc salts -- to be met; it does not excuse ABSENCE of a required component, only tolerate unlisted non-material additions.",
        "construed_scope": "same as narrow", "ours_within_scope": False,
        "reads_on_ours_under_this_construction": "NO",
    },
    {
        "name": "broad / practitioner-cautious",
        "basis": "No construction of 'consisting essentially of X, Y, and Z' can be stretched to cover a formulation missing X entirely (primary) or missing Y and Z entirely (Enhanced-65); this is a presence/absence question, not an interpretive-boundary question, so breadth of construction cannot supply an absent ingredient. (Separately, the patent is EXPIRED ~2003 by fee lapse, so a flip here would not even change FTO risk -- noted for completeness, not relied upon for the construction verdict.)",
        "construed_scope": "same as narrow", "ours_within_scope": False,
        "reads_on_ours_under_this_construction": "NO",
    },
]
flip_5 = any(c["reads_on_ours_under_this_construction"] != "NO" for c in constructions_5)
results.append({
    "n": 5, "doc": fx5["doc_read"], "raw_snapshot_sha256": h5,
    "fixture_reads_on_ours": fx5["reads_on_ours"], "fixture_why": fx5["why"],
    "our_baseline_assumed": our_baseline,
    "grounding_term_tested": "consisting essentially of zinc phosphate + zinc molybdate + zinc benzoate triad (claim 1)",
    "real_claim1_excerpt": claim1_real_5,
    "specification_disclosure_excerpt": None,
    "constructions": constructions_5, "flip": flip_5,
    "verdict": "FLIP - NOT ROBUST" if flip_5 else "NO_FLIP - ROBUST",
})

# ---------------------------------------------------------------------------
# n=26 EP2653485A2 -- EXCLUDED, prior provenance defect (fabricated element)
# ---------------------------------------------------------------------------
prov_receipt_bytes = PROV_RECEIPT.read_bytes()
fx26 = families_by_n[26]
results.append({
    "n": 26, "doc": fx26["doc_read"],
    "status": "EXCLUDED_MOOT_PRIOR_PROVENANCE_DEFECT",
    "reason": (
        "evidence/audit/claim-chart-provenance-v1 (ledger entry fire_id "
        "20260803T150004-335042-88e86edf7333, verdict REFUTED, 2026-08-03T15:08:37Z) "
        "already found this family's charted 'polyurea topcoat' element was not "
        "faithfully re-derived from the real claim text it cites. Running a "
        "claim-construction-sensitivity test on top of a chart already found "
        "fabricated would test the fabrication, not claim construction; the prior "
        "REFUTED finding stands and is not re-litigated here."
    ),
    "prior_refuting_receipt": "amphora-ip-fto-guard/evidence/audit/claim-chart-provenance-v1/claim-chart-provenance-receipt.v1.dsse.json",
    "prior_refuting_receipt_sha256": sha(prov_receipt_bytes),
    "flip": None,
    "verdict": "EXCLUDED",
})

# ---------------------------------------------------------------------------
tested = [r for r in results if r.get("verdict") not in ("EXCLUDED",)]
flips = [r for r in tested if r["flip"]]
overall_verdict = "CLAIM_REFUTED" if flips else "CLAIM_SURVIVED"

diagnostic = {
    "schema": "amphora.ip-fto-guard.claim-construction-sensitivity.v1",
    "study_id": "amphora-ip-fto-guard/W-FTO1/claim-construction-sensitivity",
    "run_type": "audit_re_derivation",
    "module": "amphora-ip-fto-guard",
    "campaign_item_id": "W-FTO1",
    "purpose": (
        "Falsification attack on the claim: 'The FTO screen's conclusions are "
        "robust to reasonable variation in how patent claims are construed', "
        "restricted to the 6 claim-charted families in patent_landscape.json "
        "(independent_claim_chart.charted=true)."
    ),
    "non_circularity": (
        "Real claim-1 text is independently re-derived from the same hash-pinned "
        "raw HTML snapshots the prior claim-chart-provenance-v1 audit already "
        "fetched and pinned (SHA256 re-verified below, byte-for-byte, before use); "
        "this run performs no new network fetch. Constructions are applied to the "
        "REAL claim text and the REAL specification disclosure, not to the "
        "fixture's paraphrase."
    ),
    "theory_reference": (
        "Phillips v. AWH Corp., 415 F.3d 1303 (Fed. Cir. 2005) (en banc) -- claims "
        "construed in light of the specification and prosecution history, not in "
        "isolation; Pall Corp. v. Micron Separations, Inc., 66 F.3d 1211 (Fed. Cir. "
        "1995) -- 'about'/approximation terms construed by context, breadth varies "
        "with specification support; MPEP 2111.01 -- broadest reasonable "
        "interpretation informs how a competent, cautious practitioner should treat "
        "an ambiguous claim term for clearance purposes."
    ),
    "inputs": {
        "patent_landscape_fixture_sha256": fixture_sha256,
        "patent_landscape_fixture_path": "amphora-ip-fto-guard/reference/mvp20/data/patent_landscape.json",
        "raw_snapshot_sha256_pins_reused_from": "amphora-ip-fto-guard/evidence/audit/claim-chart-provenance-v1/SHA256SUMS.raw",
        "raw_snapshot_sha256_reverified": PINNED_RAW_SHA256,
    },
    "hash_and_count_lock": {
        "manifest_receipt_count_unchanged": True,
        "manifest_module_count_unchanged": True,
        "fixture_modified": False,
        "note": "This run reads patent_landscape.json read-only; it is never written.",
    },
    "charted_family_count": 6,
    "families_tested": 5,
    "families_excluded": 1,
    "results": results,
    "flip_families": [r["n"] for r in flips],
    "no_flip_families": [r["n"] for r in tested if not r["flip"]],
    "excluded_families": [r["n"] for r in results if r.get("verdict") == "EXCLUDED"],
    "verdict": overall_verdict,
    "headline": (
        f"Family n=1 (WO2016187380A1): the fixture's bright-line 'reads_on_ours: "
        f"NO' rests in part on treating claim 1's hedge-qualified 'volume solids "
        f"content of greater than about 70 percent' as a bare, unqualified 70% "
        f"threshold. Re-reading the ACTUAL claim text and the specification's own "
        f"disclosed 'high volume solids' embodiment ranges (which extend down to "
        f"'about 50%' and '60% to about 95%' for the identical concept) shows a "
        f"reasonable, spec-informed construction under which a ~65% VS coating is "
        f"not confidently excluded. This is a genuine claim-construction-sensitivity "
        f"flip: 4/5 tested families (n=2,3,4,5) are robust across all three "
        f"constructions tested (narrow, plain, broad); n=1 is not."
    ) if flips else "All tested families robust across narrow/plain/broad constructions.",
    "does_not_close": [
        "No FTO, no legal advice, no clearance opinion. This is a re-derivation "
        "exercise over the fixture's own claim-charted families using public "
        "patent text already on disk.",
        "The 'broad / practitioner-cautious' construction for family n=1 is "
        "presented as a REASONABLE alternative a competent, cautious FTO counsel "
        "could adopt -- not as a definitive infringement conclusion. Whether "
        "counsel would ultimately adopt it requires prosecution-history review "
        "(file wrapper, any examiner remarks on 'about 70 percent' during "
        "examination) which this audit does not perform.",
        "Does not modify the manifest (66 receipts / 11 modules), the pinned "
        "patent_landscape.json fixture, or any signed Phase-0 KPI.",
        "AUDIT_ONLY: promotes no authority and flips no scientific_readiness.",
    ],
}

canon_bytes = json.dumps(diagnostic, indent=2, sort_keys=True).encode()
print(canon_bytes.decode())
