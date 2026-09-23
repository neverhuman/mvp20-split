#!/usr/bin/env python3
"""Build the DR-STD-MAP consolidated foreign-standard -> ASTM/ISO mapping
table for amphora-dataset-recon, then run an independent completeness +
scope-consistency checker against it (two-replay + planted-defect positive
control). AUDIT_ONLY. No acquisition -- all data below is either (a) already
recorded in this campaign's own ledgers from prior DR-LANG-* fires, or (b) a
fresh title/scope-level WebSearch this fire (never full-text, never cached).
"""
import copy
import hashlib
import json
import re
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-dataset-recon"
LEDGERS = MOD / "evidence/ledgers"
ITEM = MOD / "evidence/phase0/repairs/DR-STD-MAP"
WORK = ITEM / "work"
DONE = ITEM / "done"
WORK.mkdir(parents=True, exist_ok=True)
DONE.mkdir(parents=True, exist_ok=True)

FIRE_ID = "20260810T160002-3096524-741041e674fd"
DATE = "2026-08-10"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def canon(obj):
    return json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False).encode("utf-8")


def jloads_lines(p):
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


# ---------------------------------------------------------------------------
# 0. Snapshot pre-fire ledger bytes (needed for the append chain later).
# ---------------------------------------------------------------------------
dsl_bytes_before = (LEDGERS / "dataset-ledger.v1.jsonl").read_bytes()
dl_bytes_before = (LEDGERS / "disposition-ledger.v1.jsonl").read_bytes()
sr_bytes_before = (LEDGERS / "search-record.v1.jsonl").read_bytes()
cm_bytes_before = (LEDGERS / "coverage-map.v1.json").read_bytes()

dsl_lines = jloads_lines(LEDGERS / "dataset-ledger.v1.jsonl")
dl_lines = jloads_lines(LEDGERS / "disposition-ledger.v1.jsonl")
sr_lines = jloads_lines(LEDGERS / "search-record.v1.jsonl")
cm_obj = json.loads(cm_bytes_before)

ALL_LEDGER_TEXT = "\n".join([
    dsl_bytes_before.decode("utf-8"),
    dl_bytes_before.decode("utf-8"),
    sr_bytes_before.decode("utf-8"),
    cm_bytes_before.decode("utf-8"),
])

# ---------------------------------------------------------------------------
# 1. CENSUS -- regex scan of the raw ledger bytes (not my own memory) for
# every non-ASTM/ISO standard-code-like token belonging to the directive's
# named classes (GB/T, JIS, DIN, GOST, KS, NF) plus the analogous national
# EN-ISO-adoption classes this campaign's DR-LANG-* fires actually surfaced
# (CSN/UNI/NEN/PN/UNE/NP). This is what an independent auditor re-running
# this script would find; the MAPPING_TABLE below is then checked against
# this census, not the other way around.
# ---------------------------------------------------------------------------
CENSUS_PATTERNS = {
    "GB/T": re.compile(r"GB\s?/?\s?T\s?\d{4,6}(?:-\d{4})?"),
    "JIS": re.compile(r"JIS\s?[A-Z]\s?\d{3,5}(?::\d{4})?"),
    "DIN": re.compile(r"DIN(?:\s?EN)?(?:\s?ISO)?\s?\d{3,6}|DIN(?!\s?Media|\s?/)"),
    "GOST": re.compile(r"ГОСТ|GOST\s?[РP]?\s?\d{1,3}(?:\.\d{2,3})?(?:-\d{2,4})?"),
    "KS": re.compile(r"KS\s?[A-Z]\s?(?:ISO\s?)?\d{3,5}"),
    "NF": re.compile(r"NF(?:\s?EN)?(?:\s?ISO)?\s?\d{3,6}"),
    "natl_en_iso": re.compile(r"(?:CSN|ČSN|UNI|NEN|PN|UNE|NP)[\s-]?EN[\s-]?ISO[\s-]?\d{3,6}"),
}
census_hits = {}
for cls, pat in CENSUS_PATTERNS.items():
    census_hits[cls] = sorted(set(m.strip() for m in pat.findall(ALL_LEDGER_TEXT) if m.strip()))

# ---------------------------------------------------------------------------
# 2. Fresh title/scope-level WebSearch evidence gathered THIS fire (recorded
# verbatim here and in the search-record append below). No full text
# acquired; no dataset cached. This fills 4 standards that were cited in
# search-record.v1.jsonl / coverage-map.v1.json prose during prior DR-LANG-*
# fires but never promoted to a disposition-ledger row with a structured
# standard_mapping triple -- and confirms one (GB/T 10125) that was never
# even searched before.
# ---------------------------------------------------------------------------
FRESH_EVIDENCE = {
    "GOST_9.032": (
        "GOST 9.032-74 (ЕСЗКС. Покрытия лакокрасочные. Группы, технические "
        "требования и обозначения / Unified System for Protection Against "
        "Corrosion and Aging. Paint and varnish coatings. Groups, technical "
        "requirements and designations). Defines 7 appearance/defect classes "
        "for paint/varnish coatings and a designation scheme referencing "
        "operating-condition groups (per GOST 9.104-79) -- a coating "
        "appearance-classification and designation standard, not a single "
        "numbered performance/test-method standard."
    ),
    "GOST_9.401": (
        "GOST 9.401-2018 (current edition; supersedes GOST 9.401-91): ЕСЗКС. "
        "Покрытия лакокрасочные. Общие требования и методы ускоренных "
        "испытаний на стойкость к воздействию климатических факторов / "
        "Unified System for Protection Against Corrosion and Aging. Paint "
        "and varnish coatings. General requirements and methods of "
        "accelerated tests for resistance to climatic factors."
    ),
    "GB/T_6748": (
        "GB/T 6748-2008 (船用防锈底漆 / general specification of "
        "anticorrosive marine paint, supersedes GB 6748-1986). Specifies "
        "classification, requirements, test methods, inspection rules, "
        "marking/packaging/transport/storage for rust-preventive paint on "
        "ship-hull parts above the design waterline and internal structures "
        "(excluding liquid tanks) -- the above-waterline sibling standard to "
        "GB/T 6822's below-waterline antifouling scope."
    ),
    "GB/T_10125": (
        "GB/T 10125-2021 (人造气氛腐蚀试验 盐雾试验 / Corrosion tests in "
        "artificial atmospheres -- Salt spray tests), implemented "
        "2022-03-01, replaces GB/T 10125-2012. Explicitly a modified "
        "adoption of ISO 9227:2017 per its own published metadata (nssi.org.cn, "
        "ndls.org.cn national standard library records). Specifies "
        "apparatus/reagents/procedure for NSS/AASS/CASS salt-spray tests, "
        "same scope class as ISO 9227."
    ),
    "KS_M_2270": (
        "Investigated in the DR-LANG-KO fire (fire_id "
        "20260810T100002-3826207-0feb3e17adea, search-record query 'KS "
        "ㅌ 방청도료 규격 아연분말 "
        "프라이머'): result_note explicitly identifies KS M "
        "2270 as 'unrelated asphalt primer, false-positive on primer'. "
        "EXCLUDED from this mapping table by design -- it is not a coating/"
        "corrosion-test standard relevant to this portfolio's scope, "
        "already correctly disclosed as a rejected false-positive, not an "
        "unmapped standard."
    ),
}

# ISO/ASTM target-scope reference text, independently re-confirmed this fire
# via live WebSearch against iso.org / ansi webstore / q-lab mirrors (used by
# the checker's scope-consistency rule below -- this is the "cross-check
# mappings against the standards' own scopes" attack the item's ATTACK SHAPE
# names explicitly).
ISO_SCOPES = {
    "ISO 9227": (
        "ISO 9227:2022 specifies the apparatus, the reagents and the "
        "procedure to be used in conducting the neutral salt spray (NSS), "
        "acetic acid salt spray (AASS) and copper-accelerated acetic acid "
        "salt spray (CASS) tests for assessment of the corrosion resistance "
        "of metallic materials, with or without permanent or temporary "
        "corrosion protection. Useful for detecting discontinuities such as "
        "pores and other defects in coatings."
    ),
    "ISO 3001": (
        "ISO 3001:1999 specifies a method for the determination of the "
        "epoxy equivalent, applicable to all epoxy compounds (with an "
        "epoxyamine modification in annex A). Epoxy equivalent = mass of "
        "resin in grams containing one mole of epoxy groups. Test principle: "
        "epoxy groups reacted with nascent HBr from perchloric acid and "
        "tetraethylammonium bromide -- a titrimetric method."
    ),
    "ISO 12944": (
        "ISO 12944 (Paints and varnishes -- Corrosion protection of steel "
        "structures by protective paint systems) specifies performance "
        "requirements, corrosivity categories (C1-C5, CX/Im immersion) and "
        "test methods for protective coating systems on structural steel, "
        "including Part 9 offshore-structure scope."
    ),
}

# category keyword sets used by the checker's scope-consistency rule
CATEGORY_KEYWORDS = {
    "SALT_SPRAY": {"salt", "spray", "corrosion", "nss", "aass", "cass", "盐雾",
                   "塔水", "塔ノ", "염수", "солян",
                   "тумане", "zoutneve", "zoutsproei", "nebbia salina",
                   "essai au brouillard"},
    "EEW": {"epoxy equivalent", "epoxide equivalent", "epoxy compounds",
             "epoxy groups", "epoxidic groups", "titration", "环氧",
             "エポキシ", "에폭시", "hbr", "perchloric",
             "tetraethylammonium"},
    "MARINE_COATING": {"hull", "ship", "vessel", "offshore", "antifoul",
                        "anticorros", "marine", "船体", "防锘",
                        "防污", "structural steel", "paint system", "coating system"},
    "CLASSIFICATION": {"classification", "groups", "designation", "appearance",
                        "класс", "defect"},
    "ACCREDITATION": {"accreditation", "laboratory", "calibration", "17025"},
    "GENERAL_WEATHERING": {"climatic", "accelerated", "weathering", "general requirements",
                            "ускоренных"},
}


def categorize(text):
    t = text.lower()
    hit = set()
    for cat, kws in CATEGORY_KEYWORDS.items():
        for kw in kws:
            if kw.lower() in t:
                hit.add(cat)
                break
    return hit


# ---------------------------------------------------------------------------
# 3. MAPPING TABLE -- every distinct non-ASTM/ISO standard entity found in
# the census, sourced either from an existing disposition-ledger
# standard_mapping{} triple (source.kind = "disposition_ledger"), from a
# coverage-map gap-note that stated a mapping in prose but never got a
# structured row (source.kind = "coverage_map_prose_elevated" -- promoted to
# a proper row THIS fire), or from fresh WebSearch this fire
# (source.kind = "fresh_websearch_this_fire").
# ---------------------------------------------------------------------------
MAPPING_TABLE = []


def row(std_id, std_class, published_standard, own_category, astm_iso_equiv,
        methodological_deltas, comparability_rating, source, integrity_gap,
        integrity_gap_reason=None):
    r = {
        "standard_id": std_id,
        "standard_class": std_class,
        "published_standard": published_standard,
        "own_scope_category": sorted(own_category) if isinstance(own_category, set) else own_category,
        "astm_iso_equiv": astm_iso_equiv,
        "methodological_deltas": methodological_deltas,
        "comparability_rating": comparability_rating,
        "source": source,
        "integrity_gap": integrity_gap,
    }
    if integrity_gap_reason:
        r["integrity_gap_reason"] = integrity_gap_reason
    MAPPING_TABLE.append(r)


# -- China (zh) --
row("GB/T 6822-2024 (supersedes GB/T 6822-2014)", "GB/T",
    "GB/T 6822-2024 船体防污防锈漆体系 (Anti-fouling and "
    "anti-corrosive paint systems on ship hulls, implemented 2025-06-01, replaces "
    "GB/T 6822-2014)",
    {"MARINE_COATING"},
    "NOT_FOUND -- searched explicitly in DR-LANG-ZH (fire_id 20260810T060001-1892882-de641a9ef68c); "
    "no stated ISO/ASTM cross-reference located on the SAMR metadata page.",
    "N/A -- no equivalence found to state a delta against.",
    "unconfirmed_no_equivalence_found",
    {"kind": "disposition_ledger", "candidate_id": "DR-LANG-ZH-04",
     "ledger_path": "amphora-dataset-recon/evidence/ledgers/disposition-ledger.v1.jsonl"},
    True, "No closest ASTM/ISO equivalent found despite an explicit search -- ship-hull-specific "
          "antifouling standards appear to be a genuinely national-only regulatory niche in every "
          "language community this campaign has searched so far (zh is the only one with a codified "
          "number at all; ja/de/fr/nl/it/pl/cs/ko/es/pt all returned empty for this same sub-question).")

row("GB/T 13351-1992", "GB/T",
    "GB/T 13351-1992 船底防锈漆通用技术条件, "
    "ABOLISHED 2008-04-01, superseded by the GB/T 6748 and GB/T 6822 lineage.",
    {"MARINE_COATING"}, "N/A -- moot, standard is abolished.", "N/A -- abolished, no current text to diff.",
    "not_applicable_abolished",
    {"kind": "disposition_ledger", "candidate_id": "DR-LANG-ZH-05",
     "ledger_path": "amphora-dataset-recon/evidence/ledgers/disposition-ledger.v1.jsonl"},
    False)

row("GB/T 6748-2008", "GB/T",
    FRESH_EVIDENCE["GB/T_6748"], {"MARINE_COATING"},
    "NOT_FOUND -- searched explicitly this fire (WebSearch 'GB/T 6748 涂料标准 "
    "环氧当量 OR 船底漆'); no stated ISO/ASTM cross-reference "
    "located in available metadata.",
    "N/A -- no equivalence found to state a delta against.",
    "unconfirmed_no_equivalence_found",
    {"kind": "fresh_websearch_this_fire", "query": "GB/T 6748 涂料标准 环氧当量 OR 船底漆"},
    True, "Standard was cited only in passing (DR-LANG-ZH-05's disposition note, as GB/T 6822's "
          "above-waterline sibling) and never independently mapped -- this fire closed that gap by "
          "searching it directly; result is a genuine unmapped-standard integrity gap, same shape as "
          "GB/T 6822 itself.")

row("GB/T 10125-2021", "GB/T",
    FRESH_EVIDENCE["GB/T_10125"], {"SALT_SPRAY"},
    "ISO 9227:2017 (stated 'modified adoption' relationship per nssi.org.cn / ndls.org.cn national "
    "standard library metadata, confirmed via fresh WebSearch this fire); method-class-comparable to "
    "ASTM B117 (both neutral-salt-spray tests).",
    "Modified (not identical) adoption of ISO 9227:2017 -- exact clause-level deltas not confirmed "
    "this fire (no full text acquired, per no-acquisition discipline); title/scope-level convergence "
    "only, matching the confidence level already used for GOST 34388-2018 and KS D ISO 9227.",
    "iso_direct_adoption_stated",
    {"kind": "fresh_websearch_this_fire", "query": "GB/T 10125-2021 人造气氛腐蚀试验 盐雾试验 ISO 9227"},
    False, None)

# -- Japan (ja) --
row("JIS Z 2371:2015", "JIS",
    "JIS Z 2371:2015 塔水噪霧試験方法 (salt spray test method)",
    {"SALT_SPRAY"},
    "ISO 9227:2012 (explicit technical-modification adoption stated by source); broadly "
    "method-class-comparable to ASTM B117 (both neutral-salt-spray tests).",
    "Technical modifications from ISO 9227:2012 -- source states this is a modified (not verbatim) "
    "adoption; clause-by-clause diff not performed this fire.",
    "method_class_confirmed_iso_explicit_astm_inferred",
    {"kind": "disposition_ledger", "candidate_id": "DR-LANG-JA-04",
     "ledger_path": "amphora-dataset-recon/evidence/ledgers/disposition-ledger.v1.jsonl"},
    False)

row("JIS K 5551:2018 / JIS K 5552 / JIS K 5553", "JIS",
    "JIS K 5551:2018 (構造物用さび止めペイント, "
    "structural rust-preventive paint); JIS K 5552 (zinc-rich primer); JIS K 5553 "
    "(thick-film zinc-rich paint)",
    {"MARINE_COATING"},
    "NOT_FOUND -- searched implicitly via the marine-hull query in DR-LANG-JA; no stated ISO/ASTM "
    "cross-reference located this fire.",
    "N/A -- no equivalence found to state a delta against.",
    "unconfirmed_no_equivalence_found",
    {"kind": "disposition_ledger", "candidate_id": "DR-LANG-JA-05",
     "ledger_path": "amphora-dataset-recon/evidence/ledgers/disposition-ledger.v1.jsonl"},
    True, "General structural/zinc-rich paint standards, not confirmed marine-hull-specific and not "
          "confirmed against any ASTM/ISO number -- an honest unmapped-standard gap, same class as "
          "GB/T 6822/6748.")

row("JIS K 7236", "JIS",
    "JIS K 7236 エポキシ樹脂のエポキシ当量 "
    "試験方法 (epoxy resin -- test method for epoxy equivalent)",
    {"EEW"},
    "ISO 3001:1999 (Plastics -- Epoxy compounds -- Determination of epoxy equivalent) -- title/scope "
    "level convergence stated in the ja fire's WebSearch evidence.",
    "Direct-adoption pattern per this campaign's own convention for JIS ISO-based standards (same "
    "pattern as JIS Z 2371 -> ISO 9227); clause-by-clause diff not performed -- no full text acquired.",
    "identical_to_iso_by_direct_adoption_astm_unconfirmed",
    {"kind": "coverage_map_prose_elevated", "gap_id": "jis-eew-testdata-annex-ja",
     "ledger_path": "amphora-dataset-recon/evidence/ledgers/coverage-map.v1.json",
     "note": "This standard's ISO 3001 mapping previously existed ONLY as free-text inside "
             "coverage-map.v1.json's gaps[].commissioned_measurement_candidate field -- never as a "
             "disposition-ledger row with a structured standard_mapping{published_standard, "
             "astm_iso_equiv, comparability_rating} triple. Promoted to a proper row this fire."},
    False)

# -- Germany (de) --
row("DIN EN ISO 12944", "natl_en_iso",
    "DIN EN ISO 12944 (Parts 1-9, esp. Part 9 offshore) -- Korrosionsschutz von Stahlbauten durch "
    "Beschichtungssysteme",
    {"MARINE_COATING"},
    "DIN EN ISO 12944 IS the direct German/European-language adoption of ISO 12944 itself. No "
    "specific ASTM single-standard equivalent confirmed this fire.",
    "None stated -- direct EN adoption, not a separate national standard (unlike GB/T 6822).",
    "identical_to_iso_by_direct_adoption_astm_unconfirmed",
    {"kind": "disposition_ledger", "candidate_id": "DR-LANG-DE-04",
     "ledger_path": "amphora-dataset-recon/evidence/ledgers/disposition-ledger.v1.jsonl"},
    False)

row("DIN EN ISO 9227", "natl_en_iso",
    "DIN EN ISO 9227 -- Korrosionsprüfungen in künstlichen Atmosphären, Salzsprühnebelprüfungen",
    {"SALT_SPRAY"},
    "DIN EN ISO 9227 IS the direct German/European adoption of ISO 9227 itself; method-class-comparable "
    "to ASTM B117.",
    "None stated -- direct EN adoption, no separate national number.",
    "identical_to_iso_by_direct_adoption_method_class_confirmed_astm_inferred",
    {"kind": "disposition_ledger", "candidate_id": "DR-LANG-DE-05",
     "ledger_path": "amphora-dataset-recon/evidence/ledgers/disposition-ledger.v1.jsonl"},
    False)

row("DIN EN ISO 3001", "natl_en_iso",
    "DIN EN ISO 3001 -- Epoxidharze, Bestimmung des Epoxidäquivalents",
    {"EEW"},
    "ISO 3001:1999, direct DIN EN adoption -- title/scope level only.",
    "None stated -- direct EN adoption.",
    "identical_to_iso_by_direct_adoption_astm_unconfirmed",
    {"kind": "coverage_map_prose_elevated", "gap_id": "din-eew-testdata-annex-de",
     "ledger_path": "amphora-dataset-recon/evidence/ledgers/coverage-map.v1.json",
     "note": "Previously prose-only inside coverage-map gaps[]; promoted to a structured row this fire."},
    False)

row("DIN EN ISO 17025", "natl_en_iso",
    "DIN EN ISO 17025 -- testing/calibration laboratory accreditation",
    {"ACCREDITATION"},
    "N/A -- accreditation standard, not a coating test method.",
    "N/A -- category mismatch, no coating-performance delta applies.",
    "not_applicable_accreditation_standard",
    {"kind": "disposition_ledger", "candidate_id": "DR-LANG-DE-02",
     "ledger_path": "amphora-dataset-recon/evidence/ledgers/disposition-ledger.v1.jsonl"},
    False)

# -- Russia (ru) --
row("GOST 34388-2018", "GOST",
    "ГОСТ 34388-2018 Трубы стальные. "
    "Метод испытаний коррозионной "
    "стойкости в соляном тумане",
    {"SALT_SPRAY"},
    "ИСО 9227:2012 (explicit technical-modification adoption per own text: "
    "'модифицирован на основе "
    "международного стандарта "
    "ISO 9227:2012'); method-class-comparable to ASTM B117.",
    "Modified adoption -- own text states 'modified based on' ISO 9227:2012, exact clauses not diffed.",
    "iso_direct_adoption_stated",
    {"kind": "disposition_ledger", "candidate_id": "DR-LANG-RU-02",
     "ledger_path": "amphora-dataset-recon/evidence/ledgers/disposition-ledger.v1.jsonl"},
    False)

row("GOST Р 56752-2015", "GOST",
    "ГОСТ Р 56752-2015 (эпоксидное "
    "число, epoxy equivalent determination)",
    {"EEW"},
    "ISO 3001:1999 -- title-level convergence, WebSearch-surfaced only (both direct WebFetch attempts "
    "against docs.cntd.ru and allgosts.ru failed this campaign -- connection refused / CAPTCHA).",
    "Direct-adoption pattern inferred from title, NOT independently page-confirmed -- disclosed as a "
    "lower-confidence mapping than the DIN/JIS/KS/NF/NL/IT rows above.",
    "identical_to_iso_by_direct_adoption_astm_unconfirmed_page_unreachable",
    {"kind": "coverage_map_prose_elevated", "gap_id": "gost-eew-testdata-annex-ru",
     "ledger_path": "amphora-dataset-recon/evidence/ledgers/coverage-map.v1.json",
     "note": "Previously prose-only inside coverage-map gaps[]; promoted to a structured row this fire."},
    False)

row("GOST 12497-78", "GOST",
    "ГОСТ 12497-78 Пластмассы. "
    "Методы определения "
    "эпоксидных групп (Plastics. Methods for determination of epoxy groups), effective 1979, "
    "RF-only scope.",
    {"EEW"},
    "NOT_FOUND -- source's own recorded evidence states no stated ISO equivalence; superseded in "
    "practice by GOST Р 56752-2015, which IS mapped to ISO 3001:1999 (see that row above).",
    "N/A -- no equivalence stated for this specific (older) standard; the ISO-3001 mapping applies "
    "to its de-facto successor, not to this standard's own text.",
    "not_applicable_superseded_in_practice",
    {"kind": "disposition_ledger", "note": "Recorded in DR-LANG-RU's search-record.v1.jsonl "
     "(fire_id 20260810T090001-3307991-b3648fc59c25) result_note, never promoted to its own "
     "disposition-ledger candidate row -- this fire elevated it to a structured mapping-table row.",
     "ledger_path": "amphora-dataset-recon/evidence/ledgers/search-record.v1.jsonl"},
    False)

row("GOST 9.032-74", "GOST", FRESH_EVIDENCE["GOST_9.032"], {"CLASSIFICATION"},
    "N/A -- coating-classification/designation standard (7 appearance/defect classes + "
    "operating-condition group codes), not a single-number ASTM/ISO test-method equivalent. Adjacent "
    "in concept to ISO 12944's corrosivity-category system (C1-C5/CX) but not a stated direct "
    "equivalence.",
    "N/A -- different standard TYPE (classification/designation vs. performance/test-method); no "
    "single delta statement applies.",
    "not_directly_comparable_classification_system",
    {"kind": "fresh_websearch_this_fire",
     "query": "GOST 9.032 покрытия лакокрасочные группы"},
    True, "Cited only in a coverage-map gap NOTE ('GOST 9.032 and GOST 9.401 are the general "
          "anti-corrosion coating-system standards referenced alongside ISO 12944') alongside GOST "
          "9.401, never independently mapped with its own closest-equivalent/delta/rating triple -- "
          "this fire closed the citation-discovery gap by researching it directly, but a "
          "classification-vs-performance-standard type mismatch means no single ASTM/ISO number is a "
          "genuine equivalent; declared as an integrity gap rather than forced into a false mapping.")

row("GOST 9.401-2018", "GOST", FRESH_EVIDENCE["GOST_9.401"], {"GENERAL_WEATHERING"},
    "Method-class-comparable to ISO 12944 (general coating-system corrosion-protection performance "
    "requirements) and to accelerated-weathering test-method standards (e.g. ISO 16474-class / ASTM "
    "G154), not clause-by-clause confirmed this fire; no single explicit ISO/ASTM cross-reference "
    "number found in available metadata.",
    "Unconfirmed -- title/scope only, no cross-reference number found to diff against.",
    "method_class_plausible_not_clause_confirmed",
    {"kind": "fresh_websearch_this_fire",
     "query": "GOST 9.401 покрытия лакокрасочные общие требования"},
    True, "Same citation-discovery gap as GOST 9.032 above -- previously only in a coverage-map "
          "prose note, never independently mapped. No single ASTM/ISO equivalence number was found "
          "this fire; declared as an integrity gap rather than forced into a false mapping.")

# -- Korea (ko) --
row("KS D ISO 9227:2005", "KS",
    "KS D ISO 9227:2005 인공대기에서의 부식 - 염수분무시험",
    {"SALT_SPRAY"},
    "ISO 9227:1990 (identical adoption, per KSA); broadly method-class-comparable to ASTM B117.",
    "None stated -- identical adoption per source (KSSN / e-나라 표준인증 "
    "government portal).",
    "method_class_confirmed_iso_explicit_astm_inferred",
    {"kind": "disposition_ledger", "candidate_id": "DR-LANG-KO-01",
     "ledger_path": "amphora-dataset-recon/evidence/ledgers/disposition-ledger.v1.jsonl"},
    False)

row("KS D 9502", "KS",
    "KS D 9502 염수 분무 시험방법 (중성, "
    "아세트산 및 캐스 분무 시험) -- Salt spray test "
    "method (neutral, acetic-acid, and CASS spray tests); Korea's own domestic salt-spray "
    "designation, related to but recorded separately from KS D ISO 9227:2005 in this campaign's own "
    "DR-LANG-KO search-record (result_note: 'Also surfaced KS D 9502 ... a related domestic "
    "salt-spray method').",
    {"SALT_SPRAY"},
    "Same NSS/AASS/CASS test-type structure as ISO 9227 (confirmed via fresh WebSearch this fire); "
    "not explicitly stated as an ISO-adoption in its own designation (unlike KS D ISO 9227:2005, "
    "which carries 'ISO' directly in its number) -- method-class-comparable to ASTM B117 / ISO 9227, "
    "not independently clause-confirmed.",
    "Unconfirmed whether KS D 9502 and KS D ISO 9227:2005 are the same standard under two Korean "
    "designations (pre- and post- ISO-alignment renumbering) or two genuinely distinct domestic "
    "standards -- this campaign never resolved that question and no full text was acquired to check.",
    "method_class_plausible_not_clause_confirmed",
    {"kind": "fresh_websearch_this_fire", "query": "KS D 9502 한국산업표준 염수분무시험",
     "note": "Standard number was already recorded in DR-LANG-KO's search-record.v1.jsonl "
             "(fire_id 20260810T100002-3826207-0feb3e17adea) but never independently mapped -- this "
             "fire closed that citation-discovery gap."},
    True, "Cited in search-record prose only, never independently mapped with its own "
          "closest-equivalent/delta/rating triple, AND this fire could not resolve whether it is "
          "identical to or distinct from KS D ISO 9227:2005 -- declared as an integrity gap rather "
          "than silently merged into the confirmed KS D ISO 9227 row.")

row("KS M 2270", "KS", FRESH_EVIDENCE["KS_M_2270"], set(),
    "EXCLUDED -- not a coating/corrosion-test standard (confirmed unrelated asphalt primer).",
    "N/A -- excluded, not a real citation requiring a mapping.", "excluded_confirmed_irrelevant",
    {"kind": "disposition_ledger", "candidate_id": None,
     "ledger_path": "amphora-dataset-recon/evidence/ledgers/search-record.v1.jsonl",
     "note": "DR-LANG-KO fire_id 20260810T100002-3826207-0feb3e17adea own result_note already "
             "disposed of this as a false positive."},
    False)

row("KS M ISO 9227", "KS",
    "Query-string artifact, not a real Korean standard designation -- the DR-LANG-KO fire's own "
    "search-record result_note discloses: 'Query used an incorrect prefix guess (KS M); the actual "
    "Korean designation is KS D ISO 9227, not KS M -- an honest correction of my own query, not a "
    "source discrepancy.'",
    set(), "SAME STANDARD AS KS D ISO 9227:2005 (see that row above) -- 'KS M' was this campaign's "
    "own incorrect query guess, not a second real standard.",
    "N/A -- not a distinct standard.", "excluded_query_artifact_not_a_real_designation",
    {"kind": "disposition_ledger", "candidate_id": None,
     "ledger_path": "amphora-dataset-recon/evidence/ledgers/search-record.v1.jsonl",
     "note": "DR-LANG-KO fire_id 20260810T100002-3826207-0feb3e17adea query text, not a standard "
             "citation."},
    False)

row("KS M ISO 14855", "KS",
    "A sample_urls entry (ksNo=KSMISO14855-1) that appeared as an incidental Korean-government-"
    "portal search-result link inside the DR-LANG-KO fire's KS M ISO 3001 (EEW) query -- never "
    "evaluated, never claimed as gap-relevant, and outside this portfolio's coating/corrosion scope "
    "(ISO 14855 is a biodegradability-under-composting-conditions test method, unrelated to marine "
    "epoxy-amine coatings).",
    set(), "EXCLUDED -- unrelated search-result noise, not a claimed citation.",
    "N/A -- excluded.", "excluded_unrelated_search_noise",
    {"kind": "disposition_ledger", "candidate_id": None,
     "ledger_path": "amphora-dataset-recon/evidence/ledgers/search-record.v1.jsonl",
     "note": "sample_urls artifact inside DR-LANG-KO fire_id 20260810T100002-3826207-0feb3e17adea, "
             "never asserted as a real citation by that fire itself."},
    False)

row("KS M ISO 3001", "KS",
    "KS M ISO 3001 -- 에폭시 당량 결정 (epoxy equivalent determination)",
    {"EEW"},
    "ISO 3001:1999 -- identical adoption per the official e-나라 표준인증 "
    "government portal.",
    "None stated -- identical adoption.",
    "identical_to_iso_by_direct_adoption_astm_unconfirmed",
    {"kind": "coverage_map_prose_elevated", "gap_id": "ks-eew-testdata-annex-ko",
     "ledger_path": "amphora-dataset-recon/evidence/ledgers/coverage-map.v1.json",
     "note": "Previously prose-only inside coverage-map gaps[]; promoted to a structured row this fire."},
    False)

# -- France (fr) --
row("NF EN ISO 12944", "NF",
    "NF EN ISO 12944 (Parties 1-9, esp. Partie 9 offshore)",
    {"MARINE_COATING"},
    "NF EN ISO 12944 IS the direct French/European-language adoption of ISO 12944 itself. No specific "
    "ASTM single-standard equivalent confirmed this fire.",
    "None stated -- direct EN adoption.",
    "identical_to_iso_by_direct_adoption_astm_unconfirmed",
    {"kind": "disposition_ledger", "candidate_id": "DR-LANG-FR-01",
     "ledger_path": "amphora-dataset-recon/evidence/ledgers/disposition-ledger.v1.jsonl"},
    False)

row("NF EN ISO 9227", "NF",
    "NF EN ISO 9227 -- Essai au brouillard salin",
    {"SALT_SPRAY"},
    "NF EN ISO 9227 IS the direct French/European adoption of ISO 9227; method-class-comparable to "
    "ASTM B117.",
    "None stated -- direct EN adoption.",
    "identical_to_iso_by_direct_adoption_method_class_confirmed_astm_inferred",
    {"kind": "disposition_ledger", "candidate_id": "DR-LANG-FR-02",
     "ledger_path": "amphora-dataset-recon/evidence/ledgers/disposition-ledger.v1.jsonl"},
    False)

row("NF EN ISO 3001", "NF",
    "NF EN ISO 3001 -- Équivalent époxyde",
    {"EEW"},
    "ISO 3001:1999, direct NF EN adoption -- title/scope/method-principle level (fr search surfaced "
    "the exact titration-principle text).",
    "None stated -- direct EN adoption.",
    "identical_to_iso_by_direct_adoption_astm_unconfirmed",
    {"kind": "coverage_map_prose_elevated", "gap_id": "nf-eew-testdata-annex-fr",
     "ledger_path": "amphora-dataset-recon/evidence/ledgers/coverage-map.v1.json",
     "note": "Previously prose-only inside coverage-map gaps[]; promoted to a structured row this fire."},
    False)

# -- Italy (it) / Netherlands (nl) -- use the CORRECTED live editions from
# the DR-LANG-EU fire-2 spot-check, not the withdrawn fire-1 editions.
row("UNI EN ISO 12944", "natl_en_iso",
    "UNI EN ISO 12944-9:2018 (Parti 1-9, esp. Parte 9 offshore)",
    {"MARINE_COATING"},
    "UNI EN ISO 12944 IS the direct Italian/European-language adoption of ISO 12944 itself.",
    "None stated -- direct EN adoption.",
    "identical_to_iso_by_direct_adoption_astm_unconfirmed",
    {"kind": "disposition_ledger", "candidate_id": "DR-LANG-EU-06",
     "ledger_path": "amphora-dataset-recon/evidence/ledgers/disposition-ledger.v1.jsonl"},
    False)

row("UNI EN ISO 9227:2024", "natl_en_iso",
    "UNI EN ISO 9227:2024 (current, in force since 2024-09-12; corrected from the withdrawn 2017 "
    "edition, via the also-withdrawn 2023 intermediate, in the DR-LANG-EU fire-2 spot-check)",
    {"SALT_SPRAY"},
    "Direct Italian/European adoption tracking ISO 9227:2022/Amd1:2024's lineage.",
    "None stated -- direct EN adoption; UNI's edition numbering lags the ISO/EN year by one cycle.",
    "identical_to_iso_by_direct_adoption_astm_unconfirmed",
    {"kind": "disposition_ledger", "candidate_id": "DR-LANG-EU-07-CORRECTED",
     "ledger_path": "amphora-dataset-recon/evidence/ledgers/disposition-ledger.v1.jsonl"},
    False)

row("UNI EN ISO 3001", "natl_en_iso",
    "UNI EN ISO 3001 -- equivalente epossidico",
    {"EEW"},
    "ISO 3001:1999, direct UNI-EN adoption -- title/scope/method-principle level (it search surfaced "
    "the exact TEABr/perchloric-acid titration principle text).",
    "None stated -- direct EN adoption.",
    "identical_to_iso_by_direct_adoption_astm_unconfirmed",
    {"kind": "coverage_map_prose_elevated", "gap_id": "it-eew-testdata-annex",
     "ledger_path": "amphora-dataset-recon/evidence/ledgers/coverage-map.v1.json",
     "note": "Previously prose-only inside coverage-map gaps[]; promoted to a structured row this fire."},
    False)

row("NEN-EN-ISO 12944", "natl_en_iso",
    "NEN-EN-ISO 12944 (Delen 1-9, esp. Deel 9 offshore)",
    {"MARINE_COATING"},
    "NEN-EN-ISO 12944 IS the direct Dutch/European-language adoption of ISO 12944 itself.",
    "None stated -- direct EN adoption.",
    "identical_to_iso_by_direct_adoption_astm_unconfirmed",
    {"kind": "disposition_ledger", "candidate_id": "DR-LANG-EU-01",
     "ledger_path": "amphora-dataset-recon/evidence/ledgers/disposition-ledger.v1.jsonl"},
    False)

row("NEN-EN-ISO 9227:2022", "natl_en_iso",
    "NEN-EN-ISO 9227:2022 (+A1:2024) (current, corrected from the withdrawn 2017 edition in the "
    "DR-LANG-EU fire-2 spot-check)",
    {"SALT_SPRAY"},
    "Direct Dutch/European adoption of ISO 9227:2022 (Edition 5); Amendment 1:2024 is a "
    "footnote-of-warning amendment, not a substantive method change.",
    "None stated -- direct EN adoption.",
    "identical_to_iso_by_direct_adoption_astm_unconfirmed",
    {"kind": "disposition_ledger", "candidate_id": "DR-LANG-EU-02-CORRECTED",
     "ledger_path": "amphora-dataset-recon/evidence/ledgers/disposition-ledger.v1.jsonl"},
    False)

row("NEN-EN-ISO 3001", "natl_en_iso",
    "NEN-EN-ISO 3001 -- epoxide-equivalent",
    {"EEW"},
    "ISO 3001:1999/1997, direct NEN-EN adoption -- title/scope level only.",
    "None stated -- direct EN adoption.",
    "identical_to_iso_by_direct_adoption_astm_unconfirmed",
    {"kind": "coverage_map_prose_elevated", "gap_id": "nl-eew-testdata-annex",
     "ledger_path": "amphora-dataset-recon/evidence/ledgers/coverage-map.v1.json",
     "note": "Previously prose-only inside coverage-map gaps[]; promoted to a structured row this fire."},
    False)

# -- Poland (pl) / Czechia (cs) --
row("PN-EN ISO 12944", "natl_en_iso",
    "PN-EN ISO 12944 (Parts 1-9, esp. Part 9 offshore)",
    {"MARINE_COATING"},
    "PN-EN ISO 12944 IS the direct Polish/European-language adoption of ISO 12944 itself.",
    "None stated -- direct EN adoption.",
    "identical_to_iso_by_direct_adoption_astm_unconfirmed",
    {"kind": "disposition_ledger", "candidate_id": "DR-LANG-CEE-02",
     "ledger_path": "amphora-dataset-recon/evidence/ledgers/disposition-ledger.v1.jsonl"},
    False)

row("PN-EN ISO 9227", "natl_en_iso",
    "PN-EN ISO 9227 -- direct Polish/European adoption of ISO 9227",
    {"SALT_SPRAY"},
    "Direct Polish/European adoption of ISO 9227; method-class-comparable to ASTM B117.",
    "None stated -- direct EN adoption.",
    "identical_to_iso_by_direct_adoption_method_class_confirmed_astm_inferred",
    {"kind": "disposition_ledger", "candidate_id": "DR-LANG-CEE-03",
     "ledger_path": "amphora-dataset-recon/evidence/ledgers/disposition-ledger.v1.jsonl"},
    False)

row("ČSN EN ISO 12944", "natl_en_iso",
    "ČSN EN ISO 12944 (Parts 1-9, esp. Part 9 offshore)",
    {"MARINE_COATING"},
    "Direct Czech/European adoption of ISO 12944 itself.",
    "None stated -- direct EN adoption.",
    "identical_to_iso_by_direct_adoption_astm_unconfirmed",
    {"kind": "disposition_ledger", "candidate_id": "DR-LANG-CEE-07",
     "ledger_path": "amphora-dataset-recon/evidence/ledgers/disposition-ledger.v1.jsonl"},
    False)

row("ČSN EN ISO 9227", "natl_en_iso",
    "ČSN EN ISO 9227 -- expected direct Czech/European adoption of ISO 9227",
    {"SALT_SPRAY"},
    "NOT INDEPENDENTLY CONFIRMED THIS CAMPAIGN -- coverage-map's own DR-LANG-CEE gap note states "
    "explicitly: 'Czech CSN EN ISO 9227 not separately searched this fire, but ISO 9227 is expected "
    "to be an identical direct adoption per the established EN-adoption pattern.' Inference by "
    "pattern only, never independently verified by a dedicated Czech-language search or WebFetch.",
    "Unconfirmed -- no independent verification performed.",
    "identical_to_iso_by_pattern_inference_unconfirmed_this_campaign",
    {"kind": "coverage_map_prose_elevated", "gap_id": "salt-spray-standard-mapping-pl-cs",
     "ledger_path": "amphora-dataset-recon/evidence/ledgers/coverage-map.v1.json"},
    True, "The campaign's own coverage-map explicitly discloses this mapping was NEVER independently "
          "searched or confirmed -- it is an inference by pattern from the other EN-ISO-adoption "
          "national standards, not a verified finding. Declared as an integrity gap per the item's "
          "own instruction that an unmapped/unconfirmed standard must be declared as one, not quietly "
          "treated as equivalent to the confirmed rows above.")

# -- Iberian (es/pt) --
row("UNE-EN ISO 9227", "natl_en_iso",
    "UNE-EN ISO 9227 (Spain, AENOR) -- salt spray, paywalled",
    {"SALT_SPRAY"},
    "Direct national adoption of ISO 9227 per the established EN-adoption pattern across this "
    "campaign; NOT independently page-confirmed (AENOR store is paywalled, no free scope text "
    "surfaced this campaign).",
    "Unconfirmed -- paywalled, title-level inference only.",
    "identical_to_iso_by_pattern_inference_unconfirmed_this_campaign",
    {"kind": "coverage_map_prose_elevated", "gap_id": "salt-spray-standard-mapping-iberian",
     "ledger_path": "amphora-dataset-recon/evidence/ledgers/coverage-map.v1.json"},
    True, "Paywalled at AENOR; only the standard NUMBER and its EN-ISO-adoption pattern were found, "
          "never a scope-text confirmation. Declared as an integrity gap rather than silently folded "
          "into the confirmed DIN/NF/NEN/UNI rows.")

row("UNE-EN ISO 12944", "natl_en_iso",
    "UNE-EN ISO 12944 (Spain, AENOR) -- general structural-steel coating-system standard, direct "
    "national adoption of ISO 12944, referenced only in the iberian fire's ship-hull-antifouling "
    "empty-result gap note, not independently page-confirmed.",
    {"MARINE_COATING"},
    "Direct national adoption of ISO 12944 per the established EN-adoption pattern across this "
    "campaign; NOT independently page-confirmed this campaign.",
    "Unconfirmed -- title-level inference only, no dedicated es-language WebFetch performed.",
    "identical_to_iso_by_pattern_inference_unconfirmed_this_campaign",
    {"kind": "coverage_map_prose_elevated", "gap_id": "ship-hull-antifouling-standard-mapping-iberian",
     "ledger_path": "amphora-dataset-recon/evidence/ledgers/coverage-map.v1.json"},
    True, "Only ever named in passing inside a gap note about the ABSENCE of an Iberian ship-hull-"
          "specific standard; never itself independently searched or scope-confirmed. Declared as an "
          "integrity gap rather than silently treated as equivalent-confirmed like the DIN/NF/NEN/UNI "
          "rows above.")

row("NP EN ISO 12944", "natl_en_iso",
    "NP EN ISO 12944 (Portugal, IPQ) -- general structural-steel coating-system standard, direct "
    "national adoption of ISO 12944, referenced only in the iberian fire's ship-hull-antifouling "
    "empty-result gap note, not independently page-confirmed.",
    {"MARINE_COATING"},
    "Direct national adoption of ISO 12944 per the established EN-adoption pattern across this "
    "campaign; NOT independently page-confirmed this campaign.",
    "Unconfirmed -- title-level inference only, no dedicated pt-language WebFetch performed.",
    "identical_to_iso_by_pattern_inference_unconfirmed_this_campaign",
    {"kind": "coverage_map_prose_elevated", "gap_id": "ship-hull-antifouling-standard-mapping-iberian",
     "ledger_path": "amphora-dataset-recon/evidence/ledgers/coverage-map.v1.json"},
    True, "Same as UNE-EN ISO 12944 above -- named only in passing, never independently confirmed.")

row("NP EN ISO 9227", "natl_en_iso",
    "NP EN ISO 9227 (Portugal, IPQ) -- salt spray, paywalled",
    {"SALT_SPRAY"},
    "Direct national adoption of ISO 9227 per the established EN-adoption pattern; NOT independently "
    "page-confirmed (IPQ store is paywalled).",
    "Unconfirmed -- paywalled, title-level inference only.",
    "identical_to_iso_by_pattern_inference_unconfirmed_this_campaign",
    {"kind": "coverage_map_prose_elevated", "gap_id": "salt-spray-standard-mapping-iberian",
     "ledger_path": "amphora-dataset-recon/evidence/ledgers/coverage-map.v1.json"},
    True, "Same paywalled-inference gap as UNE-EN ISO 9227 above.")

row("NP EN ISO 3001", "natl_en_iso",
    "NP EN ISO 3001 -- epoxy equivalent, Portugal (IPQ)",
    {"EEW"},
    "ISO 3001:1999, direct NP EN adoption -- title/scope level only.",
    "None stated -- direct EN adoption (title/scope level).",
    "identical_to_iso_by_direct_adoption_astm_unconfirmed",
    {"kind": "coverage_map_prose_elevated", "gap_id": "eew-testdata-annex-iberian",
     "ledger_path": "amphora-dataset-recon/evidence/ledgers/coverage-map.v1.json",
     "note": "Previously prose-only inside coverage-map gaps[]; promoted to a structured row this fire."},
    False)

# CSN / PN EEW (ISO 3001) were never searched at all in any Czech or Polish
# query this campaign -- an honest, declared, never-searched gap (not a
# false claim of equivalence-by-pattern for a standard whose EXISTENCE was
# never even confirmed, unlike the salt-spray/12944 EN-adoption rows above).
row("ČSN EN ISO 3001 / PN-EN ISO 3001", "natl_en_iso",
    "NOT SEARCHED -- no Czech or Polish epoxy-equivalent-weight standard query was run in any "
    "DR-LANG-CEE fire; existence of a numbered ČSN/PN EN ISO 3001 standard is presumed by the "
    "EN-ISO-adoption pattern but was never even looked up, unlike every other EEW row in this table.",
    {"EEW"}, "NOT_SEARCHED_THIS_CAMPAIGN", "N/A -- not searched, no evidence to state a delta from.",
    "unmapped_never_searched",
    {"kind": "census_gap", "note": "No pl/cs EEW search exists anywhere in search-record.v1.jsonl."},
    True, "This is a stronger integrity gap than the paywalled Iberian rows above: this campaign never "
          "even issued a search query for the Czech/Polish epoxy-equivalent-weight standard, so its "
          "existence (let alone its ISO/ASTM equivalence) is unconfirmed. Declared honestly rather "
          "than silently omitted from the table.")

MAPPING_TABLE_INDEX = {r["standard_id"]: r for r in MAPPING_TABLE}

# Several rows state a bare "ISO NNNN, direct XX adoption -- title/scope
# level only" without repeating that target standard's own domain
# vocabulary, which would leave the checker's limb-3 scope-consistency rule
# unable to categorize the target text at all (empty target_cats silently
# skips the check). Backfill each such row with a short, verbatim-sourced
# clause drawn from this fire's own ISO_SCOPES re-confirmation, so the
# cross-check has real content for every row, not just the ones with
# hand-written prose.
for _r in MAPPING_TABLE:
    _et = _r.get("astm_iso_equiv", "")
    if "ISO 3001" in _et and "epoxy equivalent" not in _et.lower():
        _r["astm_iso_equiv"] = _et + " (ISO 3001's own scope: determination of the epoxy equivalent.)"
    if "ISO 9227" in _et and "salt spray" not in _et.lower() and "corrosion" not in _et.lower():
        _r["astm_iso_equiv"] = _et + " (ISO 9227's own scope: salt spray corrosion tests.)"
    if "ISO 12944" in _et and "coating" not in _et.lower() and "paint" not in _et.lower():
        _r["astm_iso_equiv"] = _et + " (ISO 12944's own scope: protective paint/coating systems.)"

# ---------------------------------------------------------------------------
# 4. INDEPENDENT CHECKER -- 4 limbs, run against the frozen (real) table,
# then against 5 planted-defect mutants (one per limb + one extra for the
# swap-mapping attack shape the item names explicitly).
# ---------------------------------------------------------------------------
REQUIRED_FIELDS = ("astm_iso_equiv", "methodological_deltas", "comparability_rating")


def run_checker(table_rows, census, iso_scopes, label):
    violations = []

    # Limb 1: completeness -- every distinct GB/T-code found in the raw
    # ledger census must correspond to a row whose standard_id contains that
    # exact code string (normalized whitespace).
    def norm(s):
        # Cyrillic capital Er (U+0420) and Latin P are visually identical in
        # this campaign's mixed-script GOST citations ("ГОСТ Р 56752-2015"
        # vs "GOST Р 56752-2015" vs a hand-typed "GOST P 56752-2015") --
        # normalize both to Latin P. Also strip ALL whitespace so
        # formatting variants of the same code ("JIS K 7236" vs "JIS
        # K7236", "KS M ISO 3001" vs "KSMISO3001") compare equal --
        # standard codes in this census are specific enough that
        # whitespace-insensitive comparison does not create false matches
        # between genuinely different standards.
        s = s.replace("Р", "P").replace("Č", "C").replace("č", "c")
        return re.sub(r"\s+", "", s).strip()

    table_ids_norm = [norm(r["standard_id"]) for r in table_rows]
    for cls, codes in census.items():
        for code in codes:
            code_norm = norm(code)
            if cls == "DIN" and code_norm in ("DIN", "DIN Media", "DIN /"):
                continue
            if cls == "GOST" and code_norm == "ГОСТ":
                # bare native-script abbreviation with no attached number --
                # every GOST number this campaign cited also appears in its
                # own Latin-script GOST-NNNN form elsewhere in the ledgers,
                # which IS checked below; this bare token is not itself a
                # distinct standard citation.
                continue
            found = any(code_norm in tid or tid in code_norm for tid in table_ids_norm)
            if not found:
                violations.append({
                    "limb": 1, "rule": "census_completeness",
                    "detail": f"census token '{code_norm}' (class {cls}) has no matching mapping_table row",
                })

    # Limb 2: every row has all three required fields non-empty, OR is
    # explicitly integrity_gap=true with a stated reason.
    for r in table_rows:
        missing = [f for f in REQUIRED_FIELDS if not str(r.get(f, "")).strip()]
        if missing and not r.get("integrity_gap"):
            violations.append({
                "limb": 2, "rule": "required_fields_or_declared_gap",
                "detail": f"{r['standard_id']}: missing {missing} and NOT declared integrity_gap",
            })
        if r.get("integrity_gap") and not str(r.get("integrity_gap_reason", "")).strip():
            violations.append({
                "limb": 2, "rule": "gap_needs_reason",
                "detail": f"{r['standard_id']}: integrity_gap=true but no integrity_gap_reason",
            })

    # Limb 3: scope-consistency cross-check (the item's own "swap a
    # salt-spray protocol for a viscosity method" attack shape). For every
    # row that states a concrete ASTM/ISO equivalence (not N/A / NOT_FOUND /
    # NOT_SEARCHED), the row's own declared category must overlap with the
    # category the target text (astm_iso_equiv field) actually belongs to.
    NEGATIVE_MARKERS = ("N/A", "NOT_FOUND", "NOT_SEARCHED", "NOT INDEPENDENTLY CONFIRMED",
                         "not_applicable", "unmapped_never_searched")
    for r in table_rows:
        equiv_text = str(r.get("astm_iso_equiv", ""))
        if any(m in equiv_text for m in NEGATIVE_MARKERS):
            continue
        own_cats = set(r.get("own_scope_category") or [])
        target_cats = categorize(equiv_text)
        if own_cats and target_cats and not (own_cats & target_cats):
            violations.append({
                "limb": 3, "rule": "scope_consistency",
                "detail": (f"{r['standard_id']}: own category {sorted(own_cats)} does not overlap "
                           f"target-equivalence category {sorted(target_cats)} -- possible mismatched "
                           f"mapping (e.g. a salt-spray protocol mapped to a titration/EEW method)"),
            })

    # Limb 4: every non-N/A row must cite a source (ledger/candidate ref or
    # a fresh-websearch query) -- an unsourced mapping is unverifiable.
    for r in table_rows:
        src = r.get("source") or {}
        if not src.get("kind"):
            violations.append({
                "limb": 4, "rule": "sourced_mapping",
                "detail": f"{r['standard_id']}: no source.kind recorded",
            })

    diag = {
        "label": label,
        "row_count": len(table_rows),
        "violation_count": len(violations),
        "violations": violations,
        "refutation_criterion_fired": len(violations) > 0,
    }
    return diag


runA = run_checker(MAPPING_TABLE, census_hits, ISO_SCOPES, "real_deliverable")
runB = run_checker(MAPPING_TABLE, census_hits, ISO_SCOPES, "real_deliverable")
assert sha(canon(runA)) == sha(canon(runB)), "two-replay byte-stability gate FAILED"
assert runA["refutation_criterion_fired"] is False, (
    f"checker fired against the REAL deliverable -- violations: {runA['violations']}"
)

# ---------------------------------------------------------------------------
# 5. POSITIVE CONTROL -- 5 independently-planted mutants, one per limb, plus
# the item's named swap-mapping attack as mutant #3 (limb 3).
# ---------------------------------------------------------------------------
mutants = {}

# Mutant 1 (limb 1): delete a real row entirely -> census completeness fails.
m1 = [copy.deepcopy(r) for r in MAPPING_TABLE if r["standard_id"] != "GOST 34388-2018"]
mutants["m1_delete_row_gost_34388"] = run_checker(m1, census_hits, ISO_SCOPES, "mutant1")

# Mutant 2 (limb 2): blank out a required field on an otherwise-mapped row
# without declaring it an integrity gap.
m2 = [copy.deepcopy(r) for r in MAPPING_TABLE]
for r in m2:
    if r["standard_id"] == "DIN EN ISO 9227":
        r["comparability_rating"] = ""
        r["integrity_gap"] = False
mutants["m2_blank_required_field"] = run_checker(m2, census_hits, ISO_SCOPES, "mutant2")

# Mutant 3 (limb 3) -- THE ITEM'S OWN NAMED ATTACK SHAPE: swap a salt-spray
# protocol's equivalence to assert it equals the epoxy-equivalent-weight
# (titration/"viscosity-class") method instead.
m3 = [copy.deepcopy(r) for r in MAPPING_TABLE]
for r in m3:
    if r["standard_id"] == "GOST 34388-2018":
        r["astm_iso_equiv"] = (
            "ISO 3001:1999 (Plastics -- Epoxy compounds -- Determination of epoxy equivalent) -- "
            "direct adoption, titrimetric epoxy-equivalent-weight method."
        )
mutants["m3_swap_saltspray_for_eew_ATTACK_SHAPE"] = run_checker(m3, census_hits, ISO_SCOPES, "mutant3")

# Mutant 4 (limb 4): strip the source citation from a row.
m4 = [copy.deepcopy(r) for r in MAPPING_TABLE]
for r in m4:
    if r["standard_id"] == "NF EN ISO 9227":
        r["source"] = {}
mutants["m4_strip_source"] = run_checker(m4, census_hits, ISO_SCOPES, "mutant4")

# Mutant 5 (limb 3, second instance): swap a marine-coating standard's
# equivalence to assert it equals an unrelated lab-accreditation standard.
m5 = [copy.deepcopy(r) for r in MAPPING_TABLE]
for r in m5:
    if r["standard_id"] == "DIN EN ISO 12944":
        r["astm_iso_equiv"] = (
            "DIN EN ISO 17025 (testing/calibration laboratory accreditation) -- asserted equivalence."
        )
mutants["m5_swap_coating_for_accreditation"] = run_checker(m5, census_hits, ISO_SCOPES, "mutant5")

all_fired = all(v["refutation_criterion_fired"] for v in mutants.values())
assert all_fired, f"one or more mutants did NOT fire: {[(k, v['refutation_criterion_fired']) for k, v in mutants.items()]}"

# ---------------------------------------------------------------------------
# 6. Write mapping table + diagnostics to work/.
# ---------------------------------------------------------------------------
mapping_table_obj = {
    "schema": "amphora.dataset-recon.standard-mapping-table.v1",
    "module": "amphora-dataset-recon",
    "campaign_item_id": "DR-STD-MAP",
    "fire_id": FIRE_ID,
    "date": DATE,
    "framing": "AUDIT-ONLY",
    "scope_note": (
        "Every non-ASTM/ISO standard cited anywhere across dataset-ledger.v1.jsonl, "
        "disposition-ledger.v1.jsonl, search-record.v1.jsonl, and coverage-map.v1.json as of this "
        "fire's start, consolidated into one signed table with a closest ASTM/ISO equivalent named, "
        "known methodological deltas stated, and a comparability rating -- or, where any of those "
        "three is genuinely unavailable, an explicit integrity_gap declaration with a reason, per "
        "the item's own instruction that an unmapped standard is an integrity gap that must be "
        "declared, not silently omitted."
    ),
    "row_count": len(MAPPING_TABLE),
    "integrity_gap_count": sum(1 for r in MAPPING_TABLE if r["integrity_gap"]),
    "rows": MAPPING_TABLE,
    "census_hits_this_fire": census_hits,
    "iso_scope_reference_text": ISO_SCOPES,
}
(WORK / "mapping-table.v1.json").write_bytes(canon(mapping_table_obj))
(WORK / "diagnostic.runA.json").write_bytes(canon(runA))
(WORK / "diagnostic.runB.json").write_bytes(canon(runB))
(WORK / "diagnostic.mutants.json").write_bytes(canon(mutants))

print("row_count", len(MAPPING_TABLE))
print("integrity_gap_count", mapping_table_obj["integrity_gap_count"])
print("runA violations", runA["violation_count"])
print("mutants all fired", all_fired)

# ---------------------------------------------------------------------------
# 7. Append ONE search-record line documenting this fire's fresh WebSearch
# activity (rule: "a search that leaves no record did not happen").
# ---------------------------------------------------------------------------
sr_prior_prefix_sha = sha(sr_bytes_before)
sr_line_obj = {
    "date": DATE,
    "fire_id": FIRE_ID,
    "language_communities_touched": ["zh", "ru", "ko"],
    "no_acquisition_attestation": (
        "No dataset file, record set, table, or bulk content was downloaded, cached, or scraped this "
        "fire. All WebSearch calls retrieved title/scope-level metadata only (standard titles, scope "
        "sentences, ISO cross-reference statements already published on standards-library index "
        "pages) -- never full standard text, never a bulk dataset. Nothing new landed on xbabe2 from "
        "this fire except this search-record line, the mapping-table.v1.json synthesis artifact "
        "(itself built from already-recorded prior-fire evidence plus this fire's own title-level "
        "search results), and the signed receipt."
    ),
    "purpose": (
        "DR-STD-MAP (directive obligation DR-STD-MAP, AMPHORA-DIRECTIVE-2026-08-09 Section 4): "
        "consolidate every non-ASTM/ISO standard cited across all 8 prior DR-LANG-* fires into one "
        "signed mapping table, and independently research the standards that were cited in "
        "coverage-map/search-record prose but never got their own disposition-ledger standard_mapping "
        "row (GOST 9.032, GOST 9.401, GB/T 6748) plus one standard never previously searched at all "
        "(GB/T 10125, China's national salt-spray standard).",
    ),
    "queries": [
        {"language": "en", "purpose": "independently re-confirm ISO 9227's own published scope text "
                                       "for the mapping table's scope-consistency cross-check",
         "query": "ISO 9227:2022 corrosion tests artificial atmospheres salt spray scope",
         "query_gloss_en": "ISO 9227:2022 corrosion tests artificial atmospheres salt spray scope",
         "result_count": 8, "tool": "WebSearch",
         "result_evidence_quote": ISO_SCOPES["ISO 9227"]},
        {"language": "en", "purpose": "independently re-confirm ISO 3001's own published scope text "
                                       "for the mapping table's scope-consistency cross-check",
         "query": "ISO 3001:1999 epoxy resins determination epoxy equivalent scope",
         "query_gloss_en": "ISO 3001:1999 epoxy resins determination epoxy equivalent scope",
         "result_count": 10, "tool": "WebSearch",
         "result_evidence_quote": ISO_SCOPES["ISO 3001"]},
        {"language": "ru", "purpose": "close the citation-discovery gap for GOST 9.032, cited only in "
                                       "a coverage-map prose note and never independently mapped",
         "query": "GOST 9.032 ГОСТ 9.032 покрытия лакокрасочные группы условия эксплуатации обозначения",
         "query_gloss_en": "GOST 9.032 paint/varnish coatings groups operating conditions designations",
         "result_count": 8, "tool": "WebSearch",
         "result_evidence_quote": FRESH_EVIDENCE["GOST_9.032"]},
        {"language": "ru", "purpose": "close the citation-discovery gap for GOST 9.401",
         "query": "GOST 9.401 ГОСТ 9.401 покрытия лакокрасочные общие требования методы ускоренных испытаний",
         "query_gloss_en": "GOST 9.401 paint/varnish coatings general requirements accelerated test methods",
         "result_count": 6, "tool": "WebSearch",
         "result_evidence_quote": FRESH_EVIDENCE["GOST_9.401"]},
        {"language": "zh", "purpose": "close the citation-discovery gap for GB/T 6748, GB/T 6822's "
                                       "above-waterline sibling standard, cited only in passing in "
                                       "DR-LANG-ZH-05's disposition note",
         "query": "GB/T 6748 涂料标准 环氧当量 OR 船底漆",
         "query_gloss_en": "GB/T 6748 coating standard epoxy equivalent OR ship bottom paint",
         "result_count": 10, "tool": "WebSearch",
         "result_evidence_quote": FRESH_EVIDENCE["GB/T_6748"]},
        {"language": "zh", "purpose": "search for China's national salt-spray standard (parallel to "
                                       "GOST 34388-2018/JIS Z2371/KS D ISO9227/etc.), never previously "
                                       "searched despite GB/T 6822 having been found in DR-LANG-ZH",
         "query": "GB/T 10125-2021 人造气氛腐蚀试验 盐雾试验 ISO 9227",
         "query_gloss_en": "GB/T 10125-2021 artificial atmosphere corrosion test salt spray test ISO 9227",
         "result_count": 8, "tool": "WebSearch",
         "result_evidence_quote": FRESH_EVIDENCE["GB/T_10125"]},
        {"language": "ko", "purpose": "re-verify KS M 2270's DR-LANG-KO disposal as an unrelated "
                                       "asphalt-primer false-positive, so it is correctly EXCLUDED from "
                                       "this mapping table rather than silently omitted without reason",
         "query": "KS M 2270 한국산업표준 도료",
         "query_gloss_en": "KS M 2270 Korean Industrial Standard paint/coating",
         "result_count": 6, "tool": "WebSearch",
         "result_evidence_quote": FRESH_EVIDENCE["KS_M_2270"]},
    ],
}
sr_line_bytes = canon(sr_line_obj) + b"\n"
sr_lines_new = sr_bytes_before + (b"" if sr_bytes_before.endswith(b"\n") or not sr_bytes_before else b"\n") + json.dumps(sr_line_obj, sort_keys=True, ensure_ascii=False).encode("utf-8") + b"\n"
(LEDGERS / "search-record.v1.jsonl").write_bytes(sr_lines_new)
sr_bytes_after = (LEDGERS / "search-record.v1.jsonl").read_bytes()
sr_appended_line_no = len(sr_lines) + 1
sr_appended_sha = sha(json.dumps(sr_line_obj, sort_keys=True, ensure_ascii=False).encode("utf-8") + b"\n")

shas = {
    "runA_sha": sha(canon(runA)),
    "mapping_table_sha": sha((WORK / "mapping-table.v1.json").read_bytes()),
    "sr_prior_prefix_sha": sr_prior_prefix_sha,
    "sr_appended_line_no": sr_appended_line_no,
    "sr_appended_sha": sr_appended_sha,
    "sr_file_sha_after": sha(sr_bytes_after),
    "dsl_file_sha_unchanged": sha(dsl_bytes_before),
    "dl_file_sha_unchanged": sha(dl_bytes_before),
    "cm_file_sha_unchanged": sha(cm_bytes_before),
}
(WORK / "shas.json").write_text(json.dumps(shas, indent=2, sort_keys=True))
print("WROTE shas.json")
print(json.dumps(shas, indent=2))
