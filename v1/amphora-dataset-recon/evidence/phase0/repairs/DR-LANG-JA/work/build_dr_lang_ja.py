#!/usr/bin/env python3
"""Build DR-LANG-JA deliverable: search-record append, disposition-ledger append,
coverage-map merge, independent checker with two-replay + 5-mutant positive control,
DSSE-signed done receipt. AUDIT_ONLY. Pinned Phase-0 evaluator key only.
Mirrors the DR-LANG-ZH precedent exactly (same rubric, same checker shape).
"""
import base64
import copy
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-dataset-recon"
LEDGERS = MOD / "evidence/ledgers"
ITEM = MOD / "evidence/phase0/repairs/DR-LANG-JA"
WORK = ITEM / "work"
DONE = ITEM / "done"
WORK.mkdir(parents=True, exist_ok=True)
DONE.mkdir(parents=True, exist_ok=True)

SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"
DIRECTIVE_MD = ROOT / "docs/directives/2026-08-09-dataset-reconnaissance-multilingual.md"
DIRECTIVE_SHA_EXPECTED = "97fad5d1636f5ccb106562c2d940535651c216d357dd5276088f2db12bdba207"

FIRE_ID = "20260810T070001-2413728-f647d0aacb23"
RUN_ID = f"DR-LANG-JA-{FIRE_ID}"
DATE = "2026-08-10"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " +
            str(len(body)).encode() + b" " + body)


def load_seed(p):
    raw = p.read_bytes().strip()
    if len(raw) == 64:
        try:
            return bytes.fromhex(raw.decode())
        except Exception:
            pass
    return raw[:32]


def canon(obj):
    return json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False).encode("utf-8")


directive_bytes = DIRECTIVE_MD.read_bytes()
directive_sha_actual = sha(directive_bytes)
assert directive_sha_actual == DIRECTIVE_SHA_EXPECTED, "directive md sha mismatch"

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
assert eval_pin, "evaluator key_id does not derive pinned trust store entry"

# ---------------------------------------------------------------------------
# 1. search-record.v1.jsonl new line
# ---------------------------------------------------------------------------
SR_PATH = LEDGERS / "search-record.v1.jsonl"
sr_before = SR_PATH.read_bytes()
sr_prior_prefix_sha = sha(sr_before)
sr_prior_lines = sr_before.decode("utf-8").splitlines()
sr_prior_line_count = len(sr_prior_lines)
sr_prior_lines_parsed = [json.loads(l) for l in sr_prior_lines if l.strip()]

search_record_line_obj = {
    "schema": "amphora.dataset-recon.search-record.v1",
    "run_id": RUN_ID,
    "fire_id": FIRE_ID,
    "date": DATE,
    "purpose": (
        "DR-LANG-JA gap-targeted native-Japanese-language reconnaissance fire "
        "(directive obligation DR-LANG-JA, AMPHORA-DIRECTIVE-2026-08-09 Section 4). "
        "Extends PROBE-WEB's tooling probe (search-record.v1.jsonl line 1, sha256 "
        "0fd12053ad9db240c027485f01ef3c4a625291da6f2b1639ee55592419f8f651), which "
        "explicitly left the ja native-script SERP round-trip open, into a full "
        "gap-targeted sweep across J-STAGE, NIMS/PoLyInfo-class national materials "
        "databases, and JIS test-data annexes."
    ),
    "language_communities_touched": ["ja"],
    "repository_classes_touched": [
        "national_repository_index (J-STAGE / ジーステージ, ja)",
        "national_materials_database (NIMS PoLyInfo / 物質・材料研究機構, ja; rediscovery of previously-supplied candidate)",
        "national_materials_database (NIMS MatNavi DataSheet Collection / データシート資料集, ja)",
        "national_standards_body (JIS / 日本産業規格, ja; K5551/K5552/K5553/Z2371/K7236)",
        "industry_technical_society (日本接着学会 / Japan Adhesion Society, ja)",
        "industry_technical_society (日本船舶海洋工学会 / JASNAOE, ja)",
    ],
    "queries": [
        {
            "tool": "WebSearch",
            "language": "ja",
            "query": "エポキシ樹脂 アミン硬化剤 硬化反応速度論 データ J-STAGE",
            "query_gloss_en": "epoxy resin amine hardener cure reaction kinetics data J-STAGE",
            "purpose": "gap-targeted native-ja query for amine-class epoxy cure-kinetics literature on J-STAGE, the directive-named national literature aggregator",
            "result_count": 10,
            "sample_urls": [
                "https://www.jstage.jst.go.jp/article/networkpolymer/32/4/32_188/_pdf/-char/ja",
                "https://www.jstage.jst.go.jp/article/adhesion/53/4/53_4-3/_pdf/-char/ja",
                "https://www.jstage.jst.go.jp/article/koron1974/41/5/41_5_293/_article/-char/ja",
            ],
            "result_note": "Multiple J-STAGE-hosted cure-kinetics papers surfaced directly, including a rate-constant (DSC, pseudo-third-order) study ranking aliphatic > phenylalkyl > alicyclic > aromatic amine reactivity by basicity (pKa correlation).",
        },
        {
            "tool": "WebSearch",
            "language": "ja",
            "query": "PoLyInfo 物質・材料研究機構 高分子物性 データベース 公開 利用規約",
            "query_gloss_en": "PoLyInfo National Institute for Materials Science polymer properties database public usage terms",
            "purpose": "independently rediscover previously-supplied candidate 'polyinfo' (feedback/v1/dataset_sources.json, feedback/v2/catalog.json rights_polyinfo_licensed_export=PROHIBITED_BULK) using native-Japanese practitioner terminology, not the English name alone",
            "result_count": 10,
            "sample_urls": [
                "https://polymer.nims.go.jp/",
                "https://polymer.nims.go.jp/PoLyInfo/guide/en/what_is_polyinfo.html",
                "https://dice.nims.go.jp/",
            ],
            "result_evidence_quote": "To use MatNavi, \"DICE Account User Registration\", \"Domain Name Registration of E-mail Address\", and \"MatNavi Usage Application\" are required. Importantly, web scraping of data is prohibited, and the acquisition of large amounts of data by manual or mechanical means is prohibited by the MatNavi Service Terms of Use.",
        },
        {
            "tool": "WebSearch",
            "language": "ja",
            "query": "JIS K 5551 船底 防食塗料 規格 エポキシ樹脂系",
            "query_gloss_en": "JIS K 5551 ship hull anti-corrosion paint standard epoxy resin type",
            "purpose": "target JIS test-data/standards annex directly named by directive Section 4, marine-hull scope",
            "result_count": 6,
            "sample_urls": [
                "https://toryo-info.jp/jis-k-5551/",
                "https://jis.eomec.com/jisk55512018",
            ],
            "result_note": "JIS K 5551:2018 is scoped to structural steel/plant anti-rust paint, not confirmed ship-hull-specific; epoxy resin types (reaction-hardening and modified) are covered.",
        },
        {
            "tool": "WebSearch",
            "language": "ja",
            "query": "腐食データベース 物質・材料研究機構 MatNavi 大気暴露",
            "query_gloss_en": "corrosion database National Institute for Materials Science MatNavi atmospheric exposure",
            "purpose": "search for a NIMS/MatNavi-class corrosion dataset analogous to the zh fire's national corrosion data center rediscovery",
            "result_count": 10,
            "sample_urls": ["https://dsc.nims.go.jp/", "https://mits.nims.go.jp/"],
            "result_note": "MatNavi's DataSheet Collection (データシート資料集) lists a single atmospheric-corrosion data sheet: No.18 Fe基二元系合金の大気腐食特性 (Atmospheric Corrosion Characteristics of Fe-Based Binary Alloys).",
        },
        {
            "tool": "WebSearch",
            "language": "ja",
            "query": "JIS Z 2371 塩水噴霧試験 ASTM B117 対応 ISO 9227",
            "query_gloss_en": "JIS Z 2371 salt spray test ASTM B117 correspondence ISO 9227",
            "purpose": "directive-mandated standard-mapping check: JIS test-data annex vs. the portfolio's ASTM/ISO corrosion-test baseline",
            "result_count": 7,
            "sample_urls": ["https://kikakurui.com/z2/Z2371-2015-01.html", "https://webdesk.jsa.or.jp/books/W11M0090/index/?bunsyo_id=JIS+Z+2371%3A2015"],
            "result_evidence_quote": "JIS Z 2371:2015 is based on ISO 9227:2012 (Corrosion tests in artificial atmospheres−Salt spray tests) with technical modifications.",
        },
        {
            "tool": "WebSearch",
            "language": "ja",
            "query": "JIS 船底 防食塗料 規格番号 防錙",
            "query_gloss_en": "JIS ship hull anti-corrosion paint standard number rust-prevention",
            "purpose": "follow-up query after JIS K 5551 proved structural-steel-scoped, to check for a ship-hull-specific JIS anti-corrosion paint number",
            "result_count": 10,
            "sample_urls": ["https://www.jasnaoe.or.jp/research/dl/report.P-49.pdf", "https://www.dnt.co.jp/products/structure/list/upload_files/kouzoubutsu-jis.pdf"],
            "result_note": "JIS K 5551:2018 (構造物用さび止めペイント, structural rust-preventive paint) is scoped to structural steel/plant anti-rust paint, not confirmed ship-hull-specific. Surfaced JIS K 5552 (ジンクリッチプライマー, zinc-rich primer) and JIS K 5553 (厚膜形ジンクリッチペイント, thick-film zinc-rich paint) as the heavy-duty anti-corrosion system components; also surfaced JASNAOE's own ship-coating design-guideline report (P-49-18). No single ship-hull-specific JIS anti-corrosive-paint standard number (analogous to zh's GB/T 6822) was found -- honest negative result for that specific sub-question.",
        },
        {
            "tool": "WebSearch",
            "language": "ja",
            "query": "JIS K 7236 エポキシ当量 試験方法 データ 公開",
            "query_gloss_en": "JIS K 7236 epoxy equivalent weight test method data public",
            "purpose": "directive rule 7 empty-is-an-answer probe: search for an open JIS test-data annex specifically for the epoxy-equivalent-weight (EEW) test method used to characterize the portfolio's DGEBA/amine stoichiometry",
            "result_count": 8,
            "sample_urls": ["https://kikakurui.com/k7/K7236-2009-01.html", "https://jis.eomec.com/jisk72362001"],
            "result_evidence_quote": "The 2009 standard corresponds to the international standard ISO 3001:1999 (Plastics−Epoxy compounds−Determination of epoxy equivalent). The search results do not contain specific publicly available test data or datasets from this standard.",
            "empty_result": True,
            "empty_result_note": "Standard method itself confirmed and mapped to ISO 3001:1999, but no open EEW measurement-record dataset was found -- an honest empty result, not fabricated. Recorded in coverage-map.v1.json rather than as a disposition-ledger candidate.",
        },
        {
            "tool": "WebFetch",
            "language": "ja",
            "url": "https://www.jstage.jst.go.jp/article/adhesion/53/4/53_4-3/_article/-char/ja/",
            "purpose": "evaluate bibliographic metadata and license/copyright terms of a J-STAGE-hosted Japan Adhesion Society review article on epoxy hardeners",
            "result_evidence_quote": "Journal: 日本接着学会誌 (Journal of the Japan Adhesion Society), Vol 53, Issue 4, pages 122-128, 2017, DOI 10.11618/adhesion.53.122. Footer states © 2017 一般社団法人 日本接着学会 (Copyright 2017, Japan Adhesion Society). PDF download option available; specific access model (open vs subscription) not explicitly stated on this metadata page.",
        },
        {
            "tool": "WebFetch",
            "language": "ja",
            "url": "https://dsc.nims.go.jp/",
            "purpose": "evaluate the NIMS DataSheet Collection's corrosion-relevant holdings and access/registration terms",
            "result_evidence_quote": "Only one corrosion dataset is listed: No. 18 \"Fe基二元系合金の大気腐食特性\" (Atmospheric Corrosion Characteristics of Fe-Based Binary Alloys). Free access with registration required (DICEアカウントのユーザ登録). Explicit prohibition quoted: \"手動や機械的な方法を問わず、まとまったデータ量の取得はMatNaviサービス利用約款により禁止されています。\" Citation of URL and access date required when referencing data.",
        },
        {
            "tool": "WebFetch",
            "language": "ja",
            "url": "https://www.jasnaoe.or.jp/research/dl/report.P-49.pdf",
            "purpose": "evaluate JASNAOE's ship-coating anti-corrosion design guideline revision report (directly ship-hull-scoped, highest gap-fit candidate this fire)",
            "result": "FAILED -- WebFetch could not extract readable text; the PDF's content stream returned as binary/compressed data the fetch tool could not decode into text this fire. HTTP-level retrieval succeeded (no paywall/login block encountered), but no title, date, or license terms could be confirmed from the extracted content.",
        },
        {
            "tool": "WebFetch",
            "language": "ja",
            "url": "https://www.jstage.jst.go.jp/article/networkpolymer/32/4/32_188/_article/-char/ja/",
            "purpose": "evaluate bibliographic metadata and license/copyright terms of the aromatic-amine-cured epoxy fast-curing study surfaced by query 1",
            "result_evidence_quote": "Title (ja): 「芳香族アミン硬化エポキシ樹脂の速硬化に関する研究」. Authors: 奥野 つばさ, 石川 和憲. Journal: ネットワークポリマー (Network Polymer), Vol 32, Issue 4, pages 188-191, 2011. DOI 10.11364/networkpolymer.32.188. Published 2011-07-10, J-STAGE publication date 2014-04-22. © 2011 合成樹脂工業協会 (Copyright 2011 Synthetic Resin Industry Association). PDF download available; specific license terms not explicitly stated beyond copyright notice.",
        },
        {
            "tool": "WebFetch",
            "language": "ja",
            "url": "https://kikakurui.com/z2/Z2371-2015-01.html",
            "purpose": "evaluate JIS Z 2371:2015's scope and the mirror site's copyright/access terms",
            "result_evidence_quote": "Specifies neutral salt spray (NSS), acetic acid salt spray (AASS), and copper-accelerated acetic acid salt spray (CASS) test methods. Third-party mirror (kikakurui.com), not the official JSA source. Copyright notice: \"この規格は，著作権法で保護対象となっている著作物である。\" (This standard is a copyrighted work protected under copyright law.) Full text displayed without login gate, but reproduction restricted by copyright.",
        },
    ],
    "no_acquisition_attestation": (
        "No dataset file, record set, table, standard full-text PDF, or bulk content was "
        "downloaded, cached, or scraped this fire. All 7 WebSearch calls returned ranked "
        "result snippets only. All 5 WebFetch calls retrieved the tool's own evaluative "
        "summary of page content (bibliographic metadata, access-tier descriptions, license "
        "statements) -- never raw page bytes written to any file on xbabe2. One WebFetch call "
        "(JASNAOE PDF) triggered the WebFetch tool's own internal 15-minute self-cleaning cache "
        "to save a copy of the fetched PDF binary under this agent's LOCAL xbabe1 tool-results "
        "cache directory (a fixed WebFetch platform behavior, not a deliberate acquisition "
        "action by this fire) -- nothing was written to xbabe2 from that call, extraction "
        "failed, and the tool-cache copy is disclosed here rather than hidden; it is a single "
        "document, not bulk data, and is not referenced as evidence for any disposition-ledger "
        "score. Nothing beyond this ledger line, the disposition-ledger and coverage-map "
        "entries it supports, this item's work/ diagnostics, and this fire's signed receipt "
        "was written under mvp20-split."
    ),
    "next_run_should_extend": (
        "Untouched this fire, open for a future DR-LANG-JA or adjacent fire: (1) no ship-hull-"
        "specific JIS anti-corrosive-paint standard number (analogous to zh's GB/T 6822) was "
        "found despite an explicit search -- worth a follow-up query against ClassNK (日本船籍協会) "
        "coating specifications directly; (2) JASNAOE report P-49-18 extraction failed this "
        "fire -- retry with a PDF-text-capable extraction path (e.g. curl + a real PDF parser) "
        "rather than WebFetch's AI-summarization pipeline; (3) 日本接着学会誌 review article "
        "(query 8) was evaluated for bibliographic metadata only, not scored as a disposition "
        "candidate -- general review, not primary data; (4) JIS K 7236 (EEW test method) "
        "confirmed mapped to ISO 3001:1999 but no open test-data annex found -- recorded as an "
        "honest empty result in coverage-map.v1.json, not converted to a fabricated candidate."
    ),
}

sr_line_bytes = json.dumps(search_record_line_obj, sort_keys=True, ensure_ascii=False).encode("utf-8")
sr_new_content = sr_before
if not sr_new_content.endswith(b"\n"):
    sr_new_content += b"\n"
sr_new_content += sr_line_bytes + b"\n"
# NOTE: write deferred until after all checker/positive-control assertions pass (see bottom of file)
sr_appended_line_no = sr_prior_line_count + 1
sr_appended_sha = sha(sr_line_bytes)
sr_file_sha_after = sha(sr_new_content)

# ---------------------------------------------------------------------------
# 2. disposition-ledger.v1.jsonl new lines (1 intake manifest + 6 dispositions)
# ---------------------------------------------------------------------------
DL_PATH = LEDGERS / "disposition-ledger.v1.jsonl"
dl_before = DL_PATH.read_bytes() if DL_PATH.exists() else b""
dl_prior_prefix_sha = sha(dl_before)
dl_prior_lines = dl_before.decode("utf-8").splitlines() if dl_before else []
dl_prior_line_count = len(dl_prior_lines)

intake_manifest = {
    "schema": "amphora.dataset-recon.disposition-ledger.v1",
    "entry_type": "candidate_intake_manifest",
    "run_id": RUN_ID,
    "fire_id": FIRE_ID,
    "date": DATE,
    "framing": "AUDIT-ONLY",
    "candidates_pinned": ["C1", "C2", "C3", "C4", "polyinfo"],
    "note": (
        "Frozen candidate-intake manifest of every previously-furnished ja-relevant source as "
        "of this fire's start. C3 (J-STAGE, from DR-RUBRIC's candidate_snapshot.v1.json) is IN "
        "SCOPE for DR-LANG-JA and was explicitly deferred to this item by the DR-LANG-ZH done "
        "receipt's candidate_intake_manifest.out_of_scope_this_fire note. 'polyinfo' (from "
        "feedback/v1/dataset_sources.json id=polyinfo, source_url=https://polymer.nims.go.jp/en/, "
        "and feedback/v2/catalog.json rights_decision_id=rights_polyinfo_licensed_export, "
        "rights_class=PROHIBITED_BULK) is a second, independently-tracked previously-supplied "
        "ja candidate outside the DR-RUBRIC C1-C4 snapshot, surfaced by a direct search of the "
        "portfolio's own prior feedback/v1 and feedback/v2 acquisition records for Japan-origin "
        "sources. Both are independently re-searched and re-evaluated below with a 'rediscovers' "
        "backlink. C1, C2, C4 (zh) are out of scope for this ja-only item and were already "
        "handled by DR-LANG-ZH."
    ),
    "source_paths": [
        "amphora-dataset-recon/evidence/phase0/repairs/DR-RUBRIC/work/candidate_snapshot.v1.json",
        "feedback/v1/dataset_sources.json",
        "feedback/v2/catalog.json",
    ],
}

candidates = [
    {
        "candidate_id": "DR-LANG-JA-01",
        "name": "PoLyInfo (Polymer Database), NIMS / MatNavi",
        "language": "ja",
        "native_citation": "高分子データベース（PoLyInfo）",
        "native_citation_romanization": "Kobunshi Detabesu (PoLyInfo)",
        "url": "https://polymer.nims.go.jp/",
        "custodian": "国立研究開発法人物質・材料研究機構 (National Institute for Materials Science, NIMS)",
        "rediscovers": "polyinfo",
        "coverage": "Over half a million data points from ~20 years of manual literature extraction; ~100 property types (thermal, electrical, mechanical); homopolymers, copolymers, blends, composites, compounds. Epoxy-amine-coating-specific subset size not individually confirmed this fire (no per-dataset drill-down, per no-acquisition discipline).",
        "gap_match_class": "adjacent_domain",
        "meets_minimum_n_and_measurement_class": "unknown",
        "data_class": "compilation_of_primary",
        "standard_and_uncertainty_disclosed": "neither_stated",
        "rights_tier": "quarantined_or_prohibited",
        "redundancy_class": "no_known_portfolio_overlap",
        "translation_confidence": "native_script_verified_high",
        "translation_confidence_note": "Native label and access-terms language directly quoted from the ja WebSearch/tool summary this fire, not machine-translated after the fact.",
        "integrity_risks": [],
        "reachability": "reachable_agreement_process_required",
        "serves": {"module_gaps": [], "recipe_elements": []},
        "license_evidence_quote": "To use MatNavi, \"DICE Account User Registration\", \"Domain Name Registration of E-mail Address\", and \"MatNavi Usage Application\" are required. Importantly, web scraping of data is prohibited, and the acquisition of large amounts of data by manual or mechanical means is prohibited by the MatNavi Service Terms of Use.",
        "standard_mapping": {
            "published_standard": "N/A -- polymer property compilation database, not a single measurement standard.",
            "astm_iso_equiv": "N/A",
            "comparability_rating": "not_applicable_database",
        },
        "confidence_flag": "MEDIUM",
    },
    {
        "candidate_id": "DR-LANG-JA-02",
        "name": "NIMS DataSheet Collection (データシート資料集) -- No.18 Fe基二元系合金の大気腐食特性",
        "language": "ja",
        "native_citation": "Fe基二元系合金の大気腐食特性",
        "native_citation_romanization": "Fe-kei Nigenkei Goukin no Taiki Fushoku Tokusei",
        "url": "https://dsc.nims.go.jp/",
        "custodian": "国立研究開発法人物質・材料研究機構 (NIMS)",
        "rediscovers": None,
        "coverage": "Single data sheet: atmospheric corrosion characteristics of Fe-based binary alloys. Not epoxy-coating-specific; bare-alloy atmospheric exposure, not coated-steel corrosion. Only corrosion-class sheet in the collection's 20 documented resources.",
        "gap_match_class": "adjacent_domain",
        "meets_minimum_n_and_measurement_class": "unknown",
        "data_class": "primary_experimental",
        "standard_and_uncertainty_disclosed": "standard_named_no_uncertainty",
        "rights_tier": "quarantined_or_prohibited",
        "redundancy_class": "no_known_portfolio_overlap",
        "translation_confidence": "native_script_verified_high",
        "translation_confidence_note": "Native data-sheet title and prohibition-clause text directly quoted from the ja WebFetch evidence this fire.",
        "integrity_risks": [],
        "reachability": "reachable_agreement_process_required",
        "serves": {"module_gaps": ["amphora-public-corrosion-benchmark", "amphora-barrier-corrosion-score"], "recipe_elements": []},
        "license_evidence_quote": "Free access with registration required (DICEアカウントのユーザ登録). Explicit prohibition quoted: \"手動や機械的な方法を問わず、まとまったデータ量の取得はMatNaviサービス利用約款により禁止されています。\" Citation of URL and access date required when referencing data.",
        "standard_mapping": {
            "published_standard": "Atmospheric-exposure corrosion data sheet; specific JIS exposure-test method not individually confirmed this fire.",
            "astm_iso_equiv": "NOT_CONFIRMED_THIS_FIRE",
            "comparability_rating": "unconfirmed_no_per_dataset_drilldown",
        },
        "confidence_flag": "MEDIUM",
    },
    {
        "candidate_id": "DR-LANG-JA-03",
        "name": "\"Research on Rapid Curing of Aromatic Amine-Cured Epoxy Resins\", Network Polymer 2011, 32(4), 188-191",
        "language": "ja",
        "native_citation": "芳香族アミン硬化エポキシ樹脂の速硬化に関する研究",
        "native_citation_romanization": "Houkouzoku Amin Kouka Epokishi Jushi no Sokkouka ni Kansuru Kenkyuu",
        "url": "https://www.jstage.jst.go.jp/article/networkpolymer/32/4/32_188/_article/-char/ja/",
        "custodian": "合成樹脂工業協会 (Synthetic Resin Industry Association) / J-STAGE (JST)",
        "rediscovers": "C3",
        "doi": "10.11364/networkpolymer.32.188",
        "coverage": "Rapid-cure study of aromatic-amine-cured epoxy resin systems. Authors: 奥野つばさ, 石川和憲. Single research group, n and measurement-uncertainty reporting not confirmed beyond abstract-level bibliographic metadata (full text not acquired).",
        "gap_match_class": "named_module_gap",
        "meets_minimum_n_and_measurement_class": "unknown",
        "data_class": "primary_experimental",
        "standard_and_uncertainty_disclosed": "standard_named_no_uncertainty",
        "rights_tier": "paywalled_unclear_bulk_rights",
        "redundancy_class": "partial_overlap_adds_coverage",
        "translation_confidence": "native_script_verified_high",
        "translation_confidence_note": "Native title, author names, journal, volume/issue/pages, and DOI directly quoted from the WebFetch bibliographic-metadata evidence this fire, not machine-translated after the fact.",
        "integrity_risks": [],
        "reachability": "reachable_index_only_dataset_unclear",
        "serves": {"module_gaps": ["amphora-cure-kinetics", "amphora-cure-potlife-gate"], "recipe_elements": []},
        "license_evidence_quote": "Title (ja): 「芳香族アミン硬化エポキシ樹脂の速硬化に関する研究」. Authors: 奥野 つばさ, 石川 和憲. Journal: ネットワークポリマー (Network Polymer), Vol 32, Issue 4, pages 188-191, 2011. DOI 10.11364/networkpolymer.32.188. Published 2011-07-10, J-STAGE publication date 2014-04-22. © 2011 合成樹脂工業協会 (Copyright 2011 Synthetic Resin Industry Association). PDF download available; specific license terms not explicitly stated beyond copyright notice.",
        "standard_mapping": {
            "published_standard": "Rapid-cure aromatic-amine epoxy study; specific DSC/kinetic method not confirmed beyond abstract-level metadata (full text not acquired, per no-acquisition discipline).",
            "astm_iso_equiv": "NOT_CONFIRMED_THIS_FIRE",
            "comparability_rating": "unconfirmed_no_full_text",
        },
        "confidence_flag": "MEDIUM",
    },
    {
        "candidate_id": "DR-LANG-JA-04",
        "name": "JIS Z 2371:2015 塩水噴霧試験方法 (Salt Spray Test Methods)",
        "language": "ja",
        "native_citation": "JIS Z 2371:2015 塩水噴霧試験方法",
        "native_citation_romanization": "JIS Z 2371:2015 Ensui Funmu Shiken Houhou",
        "url": "https://kikakurui.com/z2/Z2371-2015-01.html",
        "custodian": "日本産業標準調査会 (Japanese Industrial Standards Committee, JISC) / 日本規格協会 (JSA)",
        "rediscovers": None,
        "data_class_note": "This is a published national STANDARD document, not a raw-measurement dataset -- category mismatch with the rubric's data_class vocabulary (built for datasets) is flagged honestly rather than silently forced into a better-scoring bucket.",
        "coverage": "Specifies neutral salt spray (NSS), acetic acid salt spray (AASS), and copper-accelerated acetic acid salt spray (CASS) test methods: solution prep, apparatus, specimen handling, test conditions, reporting.",
        "gap_match_class": "named_module_gap",
        "meets_minimum_n_and_measurement_class": "unknown",
        "data_class": "compilation_of_primary",
        "standard_and_uncertainty_disclosed": "published_standard_and_uncertainty",
        "rights_tier": "paywalled_unclear_bulk_rights",
        "redundancy_class": "partial_overlap_adds_coverage",
        "translation_confidence": "native_script_verified_high",
        "translation_confidence_note": "Standard number, scope, and ISO cross-reference cross-confirmed across the official-terms search summary and the kikakurui.com mirror's own quoted text.",
        "integrity_risks": [],
        "reachability": "reachable_index_only_dataset_unclear",
        "serves": {"module_gaps": ["amphora-public-corrosion-benchmark"], "recipe_elements": ["salt-spray-standard-mapping"]},
        "license_evidence_quote": "Specifies neutral salt spray (NSS), acetic acid salt spray (AASS), and copper-accelerated acetic acid salt spray (CASS) test methods. Third-party mirror (kikakurui.com), not the official JSA source. Copyright notice: \"この規格は，著作権法で保護対象となっている著作物である。\" (This standard is a copyrighted work protected under copyright law.) Full text displayed without login gate, but reproduction restricted by copyright.",
        "standard_mapping": {
            "published_standard": "JIS Z 2371:2015 塩水噴霧試験方法",
            "astm_iso_equiv": "ISO 9227:2012 (Corrosion tests in artificial atmospheres -- Salt spray tests), explicit technical-modification alignment stated by source; broadly method-class-comparable to ASTM B117 (both neutral-salt-spray tests) but a clause-by-clause ASTM B117 diff was NOT performed this fire.",
            "comparability_rating": "method_class_confirmed_iso_explicit_astm_inferred",
        },
        "confidence_flag": "MEDIUM",
    },
    {
        "candidate_id": "DR-LANG-JA-05",
        "name": "JIS K 5551:2018 構造物用さび止めペイント / JIS K 5552 ジンクリッチプライマー / JIS K 5553 厚膜形ジンクリッチペイント",
        "language": "ja",
        "native_citation": "JIS K 5551 構造物用さび止めペイント、JIS K 5552 ジンクリッチプライマー、JIS K 5553 厚膜形ジンクリッチペイント",
        "native_citation_romanization": "JIS K 5551 Kouzoubutsu-you Sabidome Peinto; JIS K 5552 Jinku Ricchi Puraima; JIS K 5553 Koumakugata Jinku Ricchi Peinto",
        "url": "https://jis.eomec.com/jisk55512018",
        "custodian": "日本産業標準調査会 (JISC) / 日本規格協会 (JSA)",
        "rediscovers": None,
        "data_class_note": "Published national STANDARDS documents (structural-steel anti-rust and zinc-rich coating specs), not raw-measurement datasets -- same category-mismatch disclosure as DR-LANG-JA-04.",
        "coverage": "JIS K 5551:2018 covers structural rust-preventive paint (types A-E, including reaction-hardening epoxy and water-based heavy-duty variants) for steel/aluminum structures (bridges, tanks, plants). K5552/K5553 cover zinc-rich primer/paint, the heavy-duty anti-corrosion system's metallic layer. Ship-hull-specific scope NOT confirmed -- structural/general-steel application named, not marine hull.",
        "gap_match_class": "adjacent_domain",
        "meets_minimum_n_and_measurement_class": "unknown",
        "data_class": "compilation_of_primary",
        "standard_and_uncertainty_disclosed": "standard_named_no_uncertainty",
        "rights_tier": "paywalled_unclear_bulk_rights",
        "redundancy_class": "partial_overlap_adds_coverage",
        "translation_confidence": "native_script_verified_high",
        "translation_confidence_note": "Standard numbers and Japanese titles directly quoted from ja WebSearch results (toryo-info.jp, jis.eomec.com, dnt.co.jp industry pages); official JSA full text not fetched.",
        "integrity_risks": ["locale_unit_convention_unverified"],
        "reachability": "reachable_index_only_dataset_unclear",
        "serves": {"module_gaps": ["amphora-zinc-galvanic-percolation"], "recipe_elements": ["zinc-rich-primer-standard-mapping"]},
        "license_evidence_quote": "JIS K 5551:2018 (構造物用さび止めペイント, structural rust-preventive paint) is scoped to structural steel/plant anti-rust paint, not confirmed ship-hull-specific. Surfaced JIS K 5552 (ジンクリッチプライマー, zinc-rich primer) and JIS K 5553 (厚膜形ジンクリッチペイント, thick-film zinc-rich paint) as the heavy-duty anti-corrosion system components;",
        "standard_mapping": {
            "published_standard": "JIS K 5551:2018 (structural rust-preventive paint); JIS K 5552 (zinc-rich primer); JIS K 5553 (thick-film zinc-rich paint).",
            "astm_iso_equiv": "NOT_FOUND -- searched implicitly via the marine-hull query; no stated ISO/ASTM cross-reference located this fire.",
            "comparability_rating": "unconfirmed_no_equivalence_found",
        },
        "confidence_flag": "LOW",
    },
    {
        "candidate_id": "DR-LANG-JA-06",
        "name": "船舶塗装防食設計指針の改訂 (Revision of the Ship Coating Anti-corrosion Design Guidelines), JASNAOE, 2018",
        "language": "ja",
        "native_citation": "船舶塗装防食設計指針の改訂",
        "native_citation_romanization": "Senpaku Tosou Boushoku Sekkei Shishin no Kaitei",
        "url": "https://www.jasnaoe.or.jp/research/dl/report.P-49.pdf",
        "custodian": "公益社団法人日本船舶海洋工学会 (Japan Society of Naval Architects and Ocean Engineers, JASNAOE), 造船設計・生産技術研究会",
        "rediscovers": None,
        "coverage": "UNKNOWN this fire -- WebFetch could not extract readable text from the PDF (binary/compressed content stream). Title and publisher are known from the search-result title snippet only; scope, JIS standard citations, and license terms are NOT confirmed.",
        "gap_match_class": "named_module_gap",
        "meets_minimum_n_and_measurement_class": "unknown",
        "data_class": "extracted_or_estimated",
        "data_class_note": "Honest worst-case categorical value: content could not be confirmed at all this fire, so it is not scored as primary_experimental or compilation_of_primary despite the title's strong topical match.",
        "standard_and_uncertainty_disclosed": "neither_stated",
        "rights_tier": "paywalled_unclear_bulk_rights",
        "redundancy_class": "no_known_portfolio_overlap",
        "translation_confidence": "no_translation_attempted_unknown",
        "translation_confidence_note": "Title is taken from the WebSearch result-title snippet (native ja), not independently verified against extracted document content, since extraction failed.",
        "integrity_risks": ["digitization_quality_concern"],
        "reachability": "reachable_index_only_dataset_unclear",
        "serves": {"module_gaps": ["amphora-ip-fto-guard", "amphora-owk-adhesion"], "recipe_elements": ["marine-hull-coating-design-guideline"]},
        "license_evidence_quote": "FAILED -- WebFetch could not extract readable text; the PDF's content stream returned as binary/compressed data the fetch tool could not decode into text this fire. HTTP-level retrieval succeeded (no paywall/login block encountered), but no title, date, or license terms could be confirmed from the extracted content.",
        "standard_mapping": {
            "published_standard": "UNKNOWN -- extraction failed this fire.",
            "astm_iso_equiv": "NOT_CONFIRMED_THIS_FIRE",
            "comparability_rating": "unconfirmed_extraction_failed",
        },
        "confidence_flag": "LOW",
    },
]

RUBRIC = {
    "gap_match_class": {"named_module_gap": 6, "adjacent_domain": 3, "off_scope": 0},
    "meets_minimum_n_and_measurement_class": {"yes": 4, "unknown": 2, "no": 0},
    "data_class": {"primary_experimental": 6, "compilation_of_primary": 3, "extracted_or_estimated": 0},
    "standard_and_uncertainty_disclosed": {"published_standard_and_uncertainty": 4, "standard_named_no_uncertainty": 2, "neither_stated": 0},
    "rights_tier": {"open_no_restriction": 10, "open_with_attribution": 8, "agreement_gated_named_terms": 5, "paywalled_unclear_bulk_rights": 2, "quarantined_or_prohibited": 0},
    "redundancy_class": {"no_known_portfolio_overlap": 10, "partial_overlap_adds_coverage": 6, "mostly_redundant": 2, "fully_redundant": 0},
    "translation_confidence": {"native_script_verified_high": 10, "machine_translated_medium": 6, "machine_translated_low_or_unverified": 3, "no_translation_attempted_unknown": 0},
    "reachability": {"reachable_direct_open_download": 10, "reachable_agreement_process_required": 6, "reachable_index_only_dataset_unclear": 4, "unreachable_network_blocked": 0},
}


def score_candidate(c):
    gap_fit = RUBRIC["gap_match_class"][c["gap_match_class"]] + RUBRIC["meets_minimum_n_and_measurement_class"][c["meets_minimum_n_and_measurement_class"]]
    provenance = RUBRIC["data_class"][c["data_class"]] + RUBRIC["standard_and_uncertainty_disclosed"][c["standard_and_uncertainty_disclosed"]]
    rights = RUBRIC["rights_tier"][c["rights_tier"]]
    uniqueness = RUBRIC["redundancy_class"][c["redundancy_class"]]
    integrity = max(0, RUBRIC["translation_confidence"][c["translation_confidence"]] - 2 * len(c["integrity_risks"]))
    acquisition = RUBRIC["reachability"][c["reachability"]]
    overall = round((gap_fit + provenance + rights + uniqueness + integrity + acquisition) / 6.0, 4)
    if rights == 0 or acquisition == 0 or gap_fit == 0:
        verdict = "REJECTED"
    elif overall >= 7.0 and rights >= 5 and acquisition >= 4:
        verdict = "RECOMMENDED"
    else:
        verdict = "CONDITIONAL"
    return {
        "gap_fit": gap_fit, "provenance_measurement_quality": provenance, "rights_clarity": rights,
        "uniqueness": uniqueness, "integrity_risk": integrity, "acquisition_cost_friction": acquisition,
        "overall": overall, "verdict": verdict,
    }


HUMAN_ACTIONS = {
    "DR-LANG-JA-01": "human obtains a licensed PoLyInfo export or NIMS collaboration grant per MatNavi Service Terms of Use; bulk scraping remains prohibited regardless.",
    "DR-LANG-JA-02": "human registers a DICE account and submits a MatNavi usage application, then confirms whether the single Fe-alloy data sheet's exposure protocol is coating-relevant.",
    "DR-LANG-JA-03": "human obtains institutional/J-STAGE-society access to DOI 10.11364/networkpolymer.32.188 and confirms DSC method + uncertainty reporting against the portfolio's cure-kinetics benchmark bar.",
    "DR-LANG-JA-04": "human purchases official JIS Z 2371:2015 full text via JSA Webdesk (or confirms the kikakurui.com mirror's fidelity) and performs a clause-by-clause ASTM B117 diff.",
    "DR-LANG-JA-05": "human purchases official JIS K 5551/K5552/K5553 full text via JSA and confirms whether any cited application scope includes ship hulls below the waterline.",
    "DR-LANG-JA-06": "human re-fetches the JASNAOE PDF with a text-capable extraction path (not WebFetch's AI summarizer) to confirm scope, JIS citations, and license terms.",
}

disp_entries = []
scores = {}
for c in candidates:
    s = score_candidate(c)
    scores[c["candidate_id"]] = s
    entry = {
        "schema": "amphora.dataset-recon.disposition-ledger.v1",
        "entry_type": "candidate_disposition",
        "candidate_id": c["candidate_id"],
        "run_id": RUN_ID,
        "fire_id": FIRE_ID,
        "framing": "AUDIT-ONLY",
        "snapshot_date": DATE,
        "language": c["language"],
        "name": c["name"],
        "native_citation": c["native_citation"],
        "native_citation_romanization": c["native_citation_romanization"],
        "url": c["url"],
        "custodian": c["custodian"],
        "rediscovers": c["rediscovers"],
        "coverage": c["coverage"],
        "rank": 0,
        "rubric_path": "amphora-dataset-recon/evidence/phase0/repairs/DR-RUBRIC/work/rubric.v1.json",
        "rubric_dimensions": {
            "gap_fit": s["gap_fit"], "provenance_measurement_quality": s["provenance_measurement_quality"],
            "rights_clarity": s["rights_clarity"], "uniqueness": s["uniqueness"],
            "integrity_risk": s["integrity_risk"], "acquisition_cost_friction": s["acquisition_cost_friction"],
        },
        "rubric_overall_score": s["overall"],
        "disposition": {
            "verdict": s["verdict"],
            "reason": (
                f"rubric.v1.json score: gap_fit={s['gap_fit']}, provenance_measurement_quality={s['provenance_measurement_quality']}, "
                f"rights_clarity={s['rights_clarity']}, uniqueness={s['uniqueness']}, integrity_risk={s['integrity_risk']}, "
                f"acquisition_cost_friction={s['acquisition_cost_friction']}, overall={s['overall']} -> {s['verdict']}. "
                + ("Floor rule: " if s["verdict"] == "REJECTED" else "")
                + (f"Blocker/next action: {HUMAN_ACTIONS[c['candidate_id']]}")
            ),
        },
        "confidence_flag": c["confidence_flag"],
        "integrity_risks": c["integrity_risks"],
        "translation_confidence": c["translation_confidence"],
        "translation_confidence_note": c["translation_confidence_note"],
        "standard_mapping": c["standard_mapping"],
        "serves": c["serves"],
        "license_evidence_quote": c["license_evidence_quote"],
    }
    if "data_class_note" in c:
        entry["data_class_note"] = c["data_class_note"]
    if "doi" in c:
        entry["doi"] = c["doi"]
    disp_entries.append(entry)

ranked = sorted(disp_entries, key=lambda e: (-e["rubric_overall_score"], e["candidate_id"]))
for i, e in enumerate(ranked, start=1):
    e["rank"] = i

dl_lines = [intake_manifest] + disp_entries
dl_line_bytes_list = [json.dumps(x, sort_keys=True, ensure_ascii=False).encode("utf-8") for x in dl_lines]
dl_appended_bytes = b"\n".join(dl_line_bytes_list) + b"\n"
dl_new_content = dl_before
if dl_before and not dl_new_content.endswith(b"\n"):
    dl_new_content += b"\n"
dl_new_content += dl_appended_bytes
# NOTE: write deferred until after all checker/positive-control assertions pass (see bottom of file)
dl_appended_line_start = dl_prior_line_count + 1
dl_appended_line_end = dl_prior_line_count + len(dl_lines)
dl_appended_sha = sha(dl_appended_bytes)
dl_file_sha_after = sha(dl_new_content)

# ---------------------------------------------------------------------------
# 3. coverage-map.v1.json -- merge (preserve ZH gaps, add JA gaps)
# ---------------------------------------------------------------------------
CM_PATH = LEDGERS / "coverage-map.v1.json"
cm_before_bytes = CM_PATH.read_bytes()
cm_before_sha = sha(cm_before_bytes)
cm_before = json.loads(cm_before_bytes)

best_conditional_by_gap = {}
for e in disp_entries:
    for g in e["serves"]["module_gaps"] or ["_unassigned"]:
        pass

def best_for(gap_id, candidate_ids):
    best = None
    for cid in candidate_ids:
        e = next(x for x in disp_entries if x["candidate_id"] == cid)
        if e["disposition"]["verdict"] == "REJECTED":
            continue
        if best is None or e["rubric_overall_score"] > best[1]:
            best = (cid, e["rubric_overall_score"])
    return best[0] if best else None

ja_gaps = [
    {
        "gap_id": "cure-kinetics-ja-amine-class",
        "module_gaps": ["amphora-cure-kinetics", "amphora-cure-potlife-gate"],
        "best_conditional": best_for("cure-kinetics-ja-amine-class", ["DR-LANG-JA-03"]),
        "best_recommended": None,
        "commissioned_measurement_candidate": None,
        "note": "Aromatic-amine fast-cure epoxy study (Network Polymer 32(4) 2011) rediscovers prior generic candidate C3 (J-STAGE) as a concrete instance; paywalled, single-group study, not RECOMMENDED-grade this fire.",
    },
    {
        "gap_id": "corrosion-database-ja",
        "module_gaps": ["amphora-public-corrosion-benchmark", "amphora-barrier-corrosion-score"],
        "best_conditional": None,
        "best_recommended": None,
        "commissioned_measurement_candidate": None,
        "note": "Both ja national-materials-database candidates found (PoLyInfo, MatNavi DataSheet Collection No.18) are REJECTED on the rubric's rights-clarity floor -- MatNavi Service Terms of Use prohibit bulk/scripted acquisition regardless of registration status. This mirrors the zh fire's PoLyInfo-class rejection pattern (same underlying custodian, NIMS). No open ja corrosion dataset was found this fire.",
    },
    {
        "gap_id": "marine-coating-jis-standard-mapping",
        "module_gaps": ["amphora-ip-fto-guard", "amphora-owk-adhesion"],
        "best_conditional": best_for("marine-coating-jis-standard-mapping", ["DR-LANG-JA-05", "DR-LANG-JA-06"]),
        "best_recommended": None,
        "commissioned_measurement_candidate": None,
        "note": "No ship-hull-specific JIS anti-corrosive-paint standard number (analogous to zh's GB/T 6822) was found despite an explicit search -- JIS K 5551/5552/5553 are structural/general-steel-scoped, not confirmed marine-hull-specific. JASNAOE's own ship-coating design guideline (P-49-18) is the best gap-fit match but its PDF failed to extract this fire (DR-LANG-JA-06) -- an honest evidence-quality gap, not a fabricated read.",
    },
    {
        "gap_id": "salt-spray-standard-mapping-ja",
        "module_gaps": ["amphora-public-corrosion-benchmark"],
        "best_conditional": best_for("salt-spray-standard-mapping-ja", ["DR-LANG-JA-04"]),
        "best_recommended": None,
        "commissioned_measurement_candidate": None,
        "note": "JIS Z 2371:2015 confirmed explicitly aligned to ISO 9227:2012 (source states 'based on ISO 9227:2012... with technical modifications'); broadly method-class-comparable to ASTM B117 (both neutral-salt-spray). This directly satisfies the directive's standard-mapping requirement for the salt-spray test method.",
    },
    {
        "gap_id": "jis-eew-testdata-annex-ja",
        "module_gaps": ["amphora-molecule-property"],
        "best_conditional": None,
        "best_recommended": None,
        "commissioned_measurement_candidate": (
            "No open JIS K 7236 (epoxy equivalent weight) test-data annex was found -- an honest "
            "empty result for the directive's 'JIS test-data annexes' scope element, per rule 7. "
            "Standard method confirmed mapped to ISO 3001:1999 (title-and-scope level only). Note: "
            "the portfolio already computes EEW/AHEW internally via its own ChEBI+RDKit pipeline "
            "(amphora-molecule-property EEW/AHEW verification result, err 0.03) -- this ja finding "
            "is a standard-citation/mapping enrichment only, not a data gap requiring commissioning."
        ),
        "note": "Empty result, honestly reported per directive rule 7 ('An empty result for a gap is a valid, reportable answer').",
    },
]

cm_after = dict(cm_before)
cm_after["fire_id"] = FIRE_ID
cm_after["run_id"] = RUN_ID
cm_after["snapshot_date"] = DATE
cm_after["scope_note"] = "Merged: zh (Chinese, DR-LANG-ZH fire) + ja (Japanese, DR-LANG-JA fire) language communities. Each gaps[] entry's gap_id and module_gaps disambiguate scope; no entry from either fire was removed or rewritten."
cm_after["gaps"] = list(cm_before.get("gaps", [])) + ja_gaps
cm_after["gaps_not_yet_searched_this_fire"] = [
    "ClassNK (日本船級協会) ship-coating specification documents -- surfaced as a plausible next source for a ship-hull-specific standard, not yet queried",
    "JASNAOE P-49-18 full content -- extraction failed this fire, needs a non-WebFetch text-extraction retry",
    "日本接着学会誌 (Japan Adhesion Society) broader corpus beyond the two articles evaluated this fire",
    "PoLyInfo/MatNavi per-dataset epoxy-coating-specific subset size -- not drilled down (no-acquisition discipline; would require the registration this fire deliberately did not pursue)",
]
cm_after["ja_no_empty_result_gap_this_fire"] = False
cm_after["ja_empty_result_gap_note"] = "jis-eew-testdata-annex-ja is a genuine empty result this fire (see gaps[] entry) -- honestly reported, not padded, and not silently converted into a fabricated candidate."

cm_after_bytes = canon(cm_after)
# NOTE: write deferred until after all checker/positive-control assertions pass (see bottom of file)
cm_after_sha = sha(cm_after_bytes)

# ---------------------------------------------------------------------------
# 4. Independent checker: 5-limb refutation criterion
# ---------------------------------------------------------------------------
import re

CJK_RE = re.compile(r"[぀-ヿ㐀-䶿一-鿿]")


def has_cjk(s):
    return bool(CJK_RE.search(s or ""))


def check(disp_lines, sr_lines_all, previously_supplied_ids):
    """disp_lines: list of dicts (manifest + dispositions). sr_lines_all: list of
    search-record line dicts (the full ledger, all fires, so citations from any
    prior fire also resolve). Returns diagnostic dict, never raises."""
    violations = []
    manifest = next((d for d in disp_lines if d.get("entry_type") == "candidate_intake_manifest"), None)
    dispositions = [d for d in disp_lines if d.get("entry_type") == "candidate_disposition"]

    # build a flat text blob of every recorded query/result field across all search-record lines
    def sr_text_for_lang(lang):
        parts = []
        for line in sr_lines_all:
            if line.get("language_communities_touched") and lang not in line["language_communities_touched"]:
                continue
            for q in line.get("queries", []):
                for k in ("query", "query_gloss_en", "purpose", "result_note", "result_summary",
                          "result_evidence_quote", "result", "sample_urls", "url"):
                    v = q.get(k)
                    if isinstance(v, list):
                        parts.extend(str(x) for x in v)
                    elif v:
                        parts.append(str(v))
        return "\n".join(parts)

    all_sr_text = sr_text_for_lang("ja")

    # Rule 1: citation_has_recorded_query_and_result
    for d in dispositions:
        url = d.get("url", "")
        if url and url not in all_sr_text:
            violations.append({"rule": "citation_has_recorded_query_and_result", "candidate_id": d["candidate_id"],
                                "reason": f"{d['candidate_id']}: url {url} does not appear in any recorded search-record query/result this fire"})

    # Rule 2: native_query_not_literal_translation -- every ja query string must contain CJK
    for line in sr_lines_all:
        if line.get("language_communities_touched") and "ja" not in line["language_communities_touched"]:
            continue
        for q in line.get("queries", []):
            if q.get("language") == "ja" and "query" in q:
                if not has_cjk(q["query"]):
                    violations.append({"rule": "native_query_not_literal_translation", "candidate_id": None,
                                        "reason": f"ja query field contains no CJK characters: '{q['query']}'"})

    # Rule 3: license_text_matches_live_evidence -- license_evidence_quote must appear verbatim in recorded evidence
    for d in dispositions:
        quote = d.get("license_evidence_quote", "")
        if quote and quote not in all_sr_text:
            violations.append({"rule": "license_text_matches_live_evidence", "candidate_id": d["candidate_id"],
                                "reason": f"{d['candidate_id']}: license_evidence_quote does not appear verbatim in this fire's recorded search-record evidence text"})

    # Rule 4: native_script_citation_integrity -- every ja native_citation must contain CJK
    for d in dispositions:
        if d.get("language") == "ja":
            nc = d.get("native_citation", "")
            if not has_cjk(nc):
                violations.append({"rule": "native_script_citation_integrity", "candidate_id": d["candidate_id"],
                                    "reason": f"{d['candidate_id']}: native_citation '{nc}' contains no CJK characters"})

    # Rule 5: rediscovery_recall -- every previously-supplied candidate must have a disposition with rediscovers==id
    rediscovered = {d.get("rediscovers") for d in dispositions if d.get("rediscovers")}
    for pid in previously_supplied_ids:
        if pid not in rediscovered:
            violations.append({"rule": "rediscovery_recall", "candidate_id": pid,
                                "reason": f"previously-supplied candidate {pid} was neither rediscovered (no disposition entry with rediscovers=={pid}) nor explicitly explained"})

    return {
        "refutation_criterion_fired": len(violations) > 0,
        "violation_count": len(violations),
        "violations": violations,
    }


PREVIOUSLY_SUPPLIED_JA = ["C3", "polyinfo"]

# Build in-memory (pre-fire content + this fire's new lines) -- do NOT read from
# disk here, since nothing has been written yet (writes are deferred to the end,
# after every assertion below passes).
sr_all_lines = list(sr_prior_lines_parsed) + [search_record_line_obj]
dl_this_fire = dl_lines  # manifest + 6 dispositions, this fire only

runA = check(dl_this_fire, sr_all_lines, PREVIOUSLY_SUPPLIED_JA)
runB = check(dl_this_fire, sr_all_lines, PREVIOUSLY_SUPPLIED_JA)
runA_bytes = canon(runA)
runB_bytes = canon(runB)
(WORK / "diagnostic.runA.json").write_bytes(runA_bytes)
(WORK / "diagnostic.runB.json").write_bytes(runB_bytes)
assert sha(runA_bytes) == sha(runB_bytes), "two-replay gate FAILED on real deliverable"
assert runA["refutation_criterion_fired"] is False, f"REAL deliverable fired the refutation criterion: {runA['violations']}"

# ---------------------------------------------------------------------------
# 5. Positive control: 5 planted-defect mutants, one per limb
# ---------------------------------------------------------------------------
mutants_out = {}

# mutant 1: missing_recorded_query -- scrub a disposition URL out of the search-record text copy
sr_mut1 = copy.deepcopy(sr_all_lines)
target_url = "https://dsc.nims.go.jp/"
for line in sr_mut1:
    for q in line.get("queries", []):
        for k in ("query", "result_note", "result_summary", "result_evidence_quote", "result", "sample_urls", "url"):
            v = q.get(k)
            if isinstance(v, list):
                q[k] = [x for x in v if target_url not in str(x)]
            elif isinstance(v, str) and target_url in v:
                q[k] = v.replace(target_url, "REDACTED")
r1 = check(dl_this_fire, sr_mut1, PREVIOUSLY_SUPPLIED_JA)
mutants_out["missing_recorded_query"] = {
    "expected_rule": "citation_has_recorded_query_and_result",
    "how_planted": f"Scrubbed every occurrence of DR-LANG-JA-02's url ({target_url}) from a copy of this fire's search-record queries/results.",
    "expected_rule_fired": True,
    "refutation_criterion_fired": r1["refutation_criterion_fired"],
    "violations": r1["violations"],
}

# mutant 2: literal_english_translation_query
sr_mut2 = copy.deepcopy(sr_all_lines)
for line in sr_mut2:
    for q in line.get("queries", []):
        if q.get("language") == "ja" and q.get("query", "").startswith("エポキシ樹脂 アミン硬化剤"):
            q["query"] = "epoxy resin amine hardener cure reaction kinetics data J-STAGE"
r2 = check(dl_this_fire, sr_mut2, PREVIOUSLY_SUPPLIED_JA)
mutants_out["literal_english_translation_query"] = {
    "expected_rule": "native_query_not_literal_translation",
    "how_planted": "Replaced the native ja query string 'エポキシ樹脂 アミン硬化剤 硬化反応速度論 データ J-STAGE' with its literal English gloss, while leaving language:'ja' unchanged.",
    "expected_rule_fired": True,
    "refutation_criterion_fired": r2["refutation_criterion_fired"],
    "violations": r2["violations"],
}

# mutant 3: license_text_diverges
dl_mut3 = copy.deepcopy(dl_this_fire)
for d in dl_mut3:
    if d.get("candidate_id") == "DR-LANG-JA-01":
        d["license_evidence_quote"] = "PoLyInfo is fully open access with no registration or usage restriction of any kind."
r3 = check(dl_mut3, sr_all_lines, PREVIOUSLY_SUPPLIED_JA)
mutants_out["license_text_diverges"] = {
    "expected_rule": "license_text_matches_live_evidence",
    "how_planted": "Overwrote DR-LANG-JA-01's license_evidence_quote with a fabricated 'fully open, no registration' claim contradicting the recorded WebSearch/WebFetch evidence (which states registration + scraping-prohibited terms).",
    "expected_rule_fired": True,
    "refutation_criterion_fired": r3["refutation_criterion_fired"],
    "violations": r3["violations"],
}

# mutant 4: native_citation_not_resolvable
dl_mut4 = copy.deepcopy(dl_this_fire)
for d in dl_mut4:
    if d.get("candidate_id") == "DR-LANG-JA-03":
        d["native_citation"] = d["native_citation_romanization"]
r4 = check(dl_mut4, sr_all_lines, PREVIOUSLY_SUPPLIED_JA)
mutants_out["native_citation_not_resolvable"] = {
    "expected_rule": "native_script_citation_integrity",
    "how_planted": "Replaced DR-LANG-JA-03's native_citation (native kanji/kana title) with its bare romanization.",
    "expected_rule_fired": True,
    "refutation_criterion_fired": r4["refutation_criterion_fired"],
    "violations": r4["violations"],
}

# mutant 5: rediscovery_dropped
dl_mut5 = copy.deepcopy(dl_this_fire)
for d in dl_mut5:
    if d.get("candidate_id") == "DR-LANG-JA-01":
        d["rediscovers"] = None
r5 = check(dl_mut5, sr_all_lines, PREVIOUSLY_SUPPLIED_JA)
mutants_out["rediscovery_dropped"] = {
    "expected_rule": "rediscovery_recall",
    "how_planted": "Cleared DR-LANG-JA-01's rediscovers field (was 'polyinfo') to None, simulating a fresh search that silently fails to link back to the previously-supplied PoLyInfo candidate.",
    "expected_rule_fired": True,
    "refutation_criterion_fired": r5["refutation_criterion_fired"],
    "violations": r5["violations"],
}

for k, v in mutants_out.items():
    assert v["refutation_criterion_fired"] == v["expected_rule_fired"], f"positive control FAILED for mutant {k}"

mutants_bytes = canon(mutants_out)
(WORK / "diagnostic.mutants.json").write_bytes(mutants_bytes)
all_mutants_fired = all(v["refutation_criterion_fired"] for v in mutants_out.values())
assert all_mutants_fired, "not all planted defects were detected -- positive control invalid"

# ---------------------------------------------------------------------------
# All assertions passed -- now (and only now) commit the real ledger writes.
# ---------------------------------------------------------------------------
SR_PATH.write_bytes(sr_new_content)
assert sha(SR_PATH.read_bytes()) == sr_file_sha_after
DL_PATH.write_bytes(dl_new_content)
assert sha(DL_PATH.read_bytes()) == dl_file_sha_after
CM_PATH.write_bytes(cm_after_bytes)
assert sha(CM_PATH.read_bytes()) == cm_after_sha

print("BUILD OK")
print("sr_appended_line_no", sr_appended_line_no)
print("dl_appended_range", dl_appended_line_start, dl_appended_line_end)
print("runA==runB byte-identical", sha(runA_bytes) == sha(runB_bytes))
print("real_refutation_criterion_fired", runA["refutation_criterion_fired"])
print("all_mutants_fired_correctly", all_mutants_fired)
for c in ranked:
    print(c["candidate_id"], c["disposition"]["verdict"], c["rubric_overall_score"])

