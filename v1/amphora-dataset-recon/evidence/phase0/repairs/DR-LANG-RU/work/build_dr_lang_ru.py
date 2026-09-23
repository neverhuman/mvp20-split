#!/usr/bin/env python3
"""Build DR-LANG-RU deliverable: search-record append, disposition-ledger append,
coverage-map merge, independent checker with two-replay + 5-mutant positive control,
DSSE-signed done receipt. AUDIT_ONLY. Pinned Phase-0 evaluator key only.
Mirrors the DR-LANG-ZH / DR-LANG-JA precedent: Russian (Cyrillic) is a script
distinct from Latin/English, so native-language integrity is checked via a
Cyrillic-presence regex (like the zh/ja CJK-presence check), not DE's
marker-word approach.
"""
import base64
import copy
import hashlib
import json
import re
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-dataset-recon"
LEDGERS = MOD / "evidence/ledgers"
ITEM = MOD / "evidence/phase0/repairs/DR-LANG-RU"
WORK = ITEM / "work"
DONE = ITEM / "done"
WORK.mkdir(parents=True, exist_ok=True)
DONE.mkdir(parents=True, exist_ok=True)

SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"
DIRECTIVE_MD = ROOT / "docs/directives/2026-08-09-dataset-reconnaissance-multilingual.md"
DIRECTIVE_SHA_EXPECTED = "97fad5d1636f5ccb106562c2d940535651c216d357dd5276088f2db12bdba207"

FIRE_ID = "20260810T090001-3307991-b3648fc59c25"
RUN_ID = f"DR-LANG-RU-{FIRE_ID}"
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
        "DR-LANG-RU gap-targeted native-Russian-language reconnaissance fire "
        "(directive obligation DR-LANG-RU, AMPHORA-DIRECTIVE-2026-08-09 Section 4). "
        "First RU-language fire for this module; searches eLIBRARY.ru/RSCI (RINC), "
        "GOST/GOST R standards annexes (epoxy-equivalent method, salt-spray method, "
        "marine anti-corrosion product standard), institute report archives (VIAM "
        "corrosion-testing center, TsNII KM Prometey marine-materials institute), the "
        "open-access CyberLeninka literature aggregator, and the Russian Maritime "
        "Register of Shipping's coating-condition guidance."
    ),
    "language_communities_touched": ["ru"],
    "repository_classes_touched": [
        "open_access_literature_aggregator (CyberLeninka / КиберЛенинка, ru)",
        "national_citation_index (eLIBRARY.ru / РИНЦ -- Russian Science Citation Index, ru)",
        "national_standards_body (GOST / ГОСТ, ГОСТ Р 56752-2015, ГОСТ 34388-2018, ru)",
        "national_standards_mirror (docs.cntd.ru, allgosts.ru, vsegost.com -- unofficial GOST full-text mirrors, ru)",
        "government_technical_institute (VIAM / ВИАМ corrosion-testing center, ru)",
        "national_materials_institute (TsNII KM Prometey / ЦНИИ КМ «Прометей», ru; shipbuilding materials science)",
        "ship_classification_society (Russian Maritime Register of Shipping / Российский морской регистр судоходства, ru)",
    ],
    "queries": [
        {
            "tool": "WebSearch", "language": "ru",
            "query": "эпоксидная смола отверждение амин кинетика данные elibrary",
            "query_gloss_en": "epoxy resin cure amine kinetics data elibrary",
            "purpose": "gap-targeted native-ru query for amine-class epoxy cure-kinetics literature/datasets, the directive's opening scope element",
            "result_count": 6,
            "result_note": "Surfaced a CyberLeninka open-access article «Кинетика отверждения эпоксидных смол аминами» (Kinetics of hardening of epoxide resins with amines) plus a Ural Federal University analytical-chemistry journal article on TLC-based cure monitoring; formal first-order kinetics reported for BFA (bisphenol A) conversion under PEPA and Etal-45M amine hardeners at 50-100C.",
            "sample_urls": ["https://cyberleninka.ru/article/n/kinetika-otverzhdeniya-epoksidnyh-smol-aminami", "https://journals.urfu.ru/index.php/analitika/article/view/2449"],
        },
        {
            "tool": "WebSearch", "language": "ru",
            "query": "судостроительное противокоррозионное покрытие ГОСТ эпоксидное",
            "query_gloss_en": "shipbuilding anti-corrosion coating GOST epoxy",
            "purpose": "target GOST standards annex directly named by directive Section 4, marine/ship-hull scope",
            "result_count": 5,
            "result_evidence_quote": "При проектировании систем антикоррозионной защиты на эпоксидной основе учитывают требования ГОСТ 9.032, ГОСТ 9.401, ISO 12944.",
            "sample_urls": ["https://vmp-holding.ru/blog/antikorrozionnye-materialy/epoksidnye-pokrytiya-vmp-nadezhnaya-zashchita-sudov-ot-korrozii/", "http://vmp-anticor.ru/publishing/257/384/"],
        },
        {
            "tool": "WebSearch", "language": "ru",
            "query": "site:elibrary.ru эпоксидная смола кинетика отверждения аминный отвердитель",
            "query_gloss_en": "site:elibrary.ru epoxy resin cure kinetics amine hardener",
            "purpose": "target eLIBRARY/RSCI directly, the directive-named national literature aggregator, for amine cure-kinetics articles",
            "result_count": 10,
            "result_note": "Multiple eLIBRARY.ru item pages surfaced, several access-restricted to unregistered users; most relevant open-metadata hit: item id=24102757 «ВЛИЯНИЕ УГЛЕРОДНЫХ НАНОТРУБОК НА КИНЕТИЧЕСКИЕ АСПЕКТЫ ОТВЕРЖДЕНИЯ ТЕРМОРЕАКТИВНЫХ СВЯЗУЮЩИХ НА ПРИМЕРЕ ЭПОКСИДНЫХ СМОЛ» (influence of carbon nanotubes on kinetic aspects of curing thermosetting binders using epoxy resins as an example), DSC-based.",
            "sample_urls": ["https://www.elibrary.ru/item.asp?id=24102757", "https://elibrary.ru/item.asp?id=38278254"],
        },
        {
            "tool": "WebSearch", "language": "ru",
            "query": "ГОСТ соляной туман коррозионные испытания ISO 9227 соответствие",
            "query_gloss_en": "GOST salt spray corrosion tests ISO 9227 correspondence",
            "purpose": "directive-mandated standard-mapping check: GOST salt-spray test-method annex vs. the portfolio's ASTM/ISO corrosion-test baseline",
            "result_count": 8,
            "result_evidence_quote": "ГОСТ 34388-2018 модифицирован на основе международного стандарта ISO 9227:2012",
            "result_titles_observed": ["ГОСТ 34388-2018 (ISO 9227:2012) Трубы стальные. Метод испытаний коррозионной стойкости в соляном тумане"],
            "sample_urls": ["http://docs.cntd.ru/document/1200160489", "https://npalib.ru/2023/04/04/gost-34388-2023-iso-9227-2017-id444784/"],
        },
        {
            "tool": "WebSearch", "language": "ru",
            "query": "ВИАМ противокоррозионное покрытие эпоксидное морская вода отчет",
            "query_gloss_en": "VIAM anti-corrosion epoxy coating seawater report",
            "purpose": "target VIAM (Всероссийский институт авиационных материалов), a directive-scope-adjacent national materials institute, for a coating/seawater corrosion report",
            "result_count": 5,
            "result_note": "Surfaced only commercial VMP-holding marketing content (ВИНИКОР-марин coating system, ISO 12944-5:2007 service-life claim), not a VIAM institute report; VIAM's own corrosion-testing lab domain was located separately via query 8 (isp.viam.ru).",
            "sample_urls": ["https://vmp-holding.ru/blog/antikorrozionnye-materialy/sistema-pokrytiy-na-osnove-vinikor-marin-nadezhnaya-zashchita-podvodnoy-chasti-korpusa-sudna/"],
        },
        {
            "tool": "WebSearch", "language": "ru",
            "query": "ЦНИИ КМ Прометей эпоксидное покрытие судостроение коррозионная стойкость",
            "query_gloss_en": "Central Research Institute of Structural Materials Prometey epoxy coating shipbuilding corrosion resistance",
            "purpose": "search for Russia's leading marine-materials national institute (directive's 'institute report archives' scope element, wherever the research leads)",
            "result_count": 6,
            "result_evidence_quote": "ФГУП ЦНИИ КМ Прометей рекомендует материалы ФЛК-2, ФЛК-3 и ФЛК-ПА для защиты металла от коррозии в условиях воздействия горячей морской воды до 100°С",
            "result_note": "Confirms ЦНИИ КМ «Прометей» (part of NRC Kurchatov Institute) as the country's leading shipbuilding/marine-materials science center; no specific downloadable report or dataset located this fire, only product-recommendation summaries via secondary sources.",
            "sample_urls": ["https://www.crism-prometey.ru/upload/iblock/82b/ulnd06t61v2aw24m08ogmkf19yb00xie/Russian2_86_2016.pdf"],
        },
        {
            "tool": "WebSearch", "language": "ru",
            "query": "эпоксидное число смолы ГОСТ метод определения эпоксидных групп",
            "query_gloss_en": "epoxy number of resin GOST method for determining epoxy groups",
            "purpose": "directive rule 7 empty-is-an-answer probe combined with standard-mapping requirement: target the GOST test-method annex for epoxy-equivalent-weight (EEW), used to characterize the portfolio's DGEBA/amine stoichiometry",
            "result_count": 9,
            "result_evidence_quote": "ГОСТ Р 56752-2015 (ИСО 3001:1999) Смолы и соединения эпоксидные. Методы определения массовой доли эпоксидных групп и эпоксидного эквивалента",
            "result_note": "Also surfaced the older GOST 12497-78 (Пластмассы. Методы определения эпоксидных групп), effective 1979, RF-only scope, no stated ISO equivalence -- superseded in practice by GOST Р 56752-2015 for the ISO-3001-mapped method.",
            "sample_urls": ["http://docs.cntd.ru/document/1200128340", "https://allgosts.ru/83/080/gost_r_56752-2015", "https://vsegost.com/Catalog/32/32459.shtml"],
        },
        {
            "tool": "WebSearch", "language": "ru",
            "query": "база данных коррозия металлов атмосферная испытания открытые данные Россия",
            "query_gloss_en": "database corrosion of metals atmospheric tests open data Russia",
            "purpose": "directive rule 7 empty-is-an-answer probe: search for an open Russian atmospheric/general corrosion database analogous to the zh National Materials Corrosion and Protection Science Data Center rediscovery",
            "result_count": 7,
            "result_evidence_quote": "Испытания коррозии цинка в различных атмосферных условиях в течение 20 лет позволили установить среднюю скорость коррозии: промышленная атмосфера – 6,4 мкм/год, берег моря – 1,5, сельская атмосфера – 1,1, пустыня – 0,18 мкм/год.",
            "result_note": "No public open-data corrosion database was found; surfaced isp.viam.ru/corrosiontests (VIAM's own corrosion-testing lab page, evaluated separately by WebFetch below) as the closest named national-institute match. Honest empty result for an open Russian corrosion database -- recorded in coverage-map.v1.json, not fabricated.",
            "sample_urls": ["https://isp.viam.ru/corrosiontests", "https://edu.truboprovod.ru/kbase/doc/start/WebHelp_ru/basecorrosion.htm"],
        },
        {
            "tool": "WebSearch", "language": "ru",
            "query": "protect.gost.ru ГОСТ Р 56752-2015 официальный текст скачать",
            "query_gloss_en": "protect.gost.ru GOST R 56752-2015 official text download",
            "purpose": "evaluate the official Rosstandart (Росстандарт) national standards portal's access terms for the EEW standard found by query 7",
            "result_count": 8,
            "result_evidence_quote": "ГОСТ Р 56752-2015 is a standard for epoxy resins and compounds that covers methods for determining the mass fraction of epoxy groups and epoxy equivalent, and is based on the international standard ISO 3001:1999",
            "result_note": "protect.gost.ru (official Rosstandart portal) confirmed as the authoritative source; no direct free-download link to the specific standard's full text was surfaced this fire.",
            "sample_urls": ["https://protect.gost.ru/", "https://protect.gost.ru/gost/", "https://www.gostrf.com/normativ/1/4293836/4293836037.htm"],
        },
        {
            "tool": "WebSearch", "language": "ru",
            "query": "РИНЦ elibrary база данных научного цитирования условия доступа регистрация",
            "query_gloss_en": "RSCI elibrary scientific citation database access terms registration",
            "purpose": "evaluate access/registration terms of eLIBRARY.ru / РИНЦ (RSCI), the directive-named 'eLIBRARY/RSCI' literature community itself",
            "result_count": 6,
            "result_evidence_quote": "РИНЦ is completely free; you only need to register on the eLibrary.Ru website to use all its features... To access full-text versions of some journals, a subscription is required; otherwise, only keywords and abstracts will be available.",
            "sample_urls": ["https://lib.unn.ru/elektronnye-resursy/rossijskie-elektronnye-resursy/risc/", "https://sciguide.hse.ru/sources/elibrary/"],
        },
        {
            "tool": "WebSearch", "language": "ru",
            "query": "ГОСТ судовая краска противообрастающая противокоррозионная номер стандарта корпус судна",
            "query_gloss_en": "GOST ship paint antifouling anticorrosive standard number ship hull",
            "purpose": "directive rule 7 empty-is-an-answer probe: search for a ship-hull-specific GOST antifouling/anticorrosive paint standard number, analogous to zh's GB/T 6822",
            "result_count": 6,
            "result_note": "No ship-hull-specific GOST antifouling/anticorrosive paint standard number was found despite an explicit search -- honest negative result, the THIRD independent language-community confirmation of this exact null finding (ja's JIS search and de's DIN search each also found no ship-hull-specific national standard number). Only commercial enamel product names (ХС-5226, ХС-416, КС-101, ХВ-453) were surfaced, without a cited GOST number.",
            "sample_urls": ["https://www.spec-emal.ru/blog/?p=617"],
        },
        {
            "tool": "WebSearch", "language": "ru",
            "query": "Российский морской регистр судоходства требования покрытия корпуса судна коррозия",
            "query_gloss_en": "Russian Maritime Register of Shipping requirements ship hull coating corrosion",
            "purpose": "follow-up after query 11 found no GOST product standard number: check the Russian Maritime Register of Shipping (РС), the national ship-classification authority, for its own coating-condition requirement",
            "result_count": 7,
            "result_evidence_quote": "Приложение 52 «Руководство по освидетельствованию и оценке технического состояния защитных покрытий помещений судна»",
            "result_note": "Confirms РС (Russian Maritime Register of Shipping) publishes classification-rules guidance (Appendix 52) on inspecting/assessing ship coating condition, but this is an inspection/assessment guideline, not a distinct product performance standard number analogous to GB/T 6822 -- reinforces query 11's honest negative result rather than reversing it. PDF documents not evaluated further this fire (no-acquisition discipline; full rules PDFs run to hundreds of pages).",
            "sample_urls": ["https://rs-class.org/upload/iblock/ad4/ad46e563256b0569ffa5581995e9a6ac.pdf"],
        },
        {
            "tool": "WebFetch", "language": "ru",
            "url": "https://isp.viam.ru/corrosiontests",
            "purpose": "evaluate VIAM's corrosion-testing center page -- organization, services, and access/license terms for any published data",
            "result_evidence_quote": "The center appears accredited by Russian aviation, maritime, and defense agencies and can provide testing documentation and pricing upon request... No explicit open license or public data sharing terms are stated on this page—services are available through commercial engagement.",
        },
        {
            "tool": "WebFetch", "language": "ru",
            "url": "https://cyberleninka.ru/article/n/kinetika-otverzhdeniya-epoksidnyh-smol-aminami",
            "purpose": "evaluate bibliographic metadata, measurement content, and license terms of the amine cure-kinetics article surfaced by query 1",
            "result_evidence_quote": "Title: 'Кинетика отверждения эпоксидных смол аминами' (Kinetics of Hardening of Epoxide Resins with Amines). Authors: A. G. Lundin, A. M. Ostapkovich, E. Yu. Yushkova. Journal: Известия высших учебных заведений. Химия и химическая технология. Year: 2005. The page displays a CC BY (Creative Commons Attribution) license icon, indicating open-access distribution with attribution requirements.",
        },
        {
            "tool": "WebFetch", "language": "ru",
            "url": "http://docs.cntd.ru/document/1200128340",
            "purpose": "evaluate GOST Р 56752-2015's official document-mirror page (scope, ISO equivalence statement, access terms)",
            "result": "FAILED -- connect ECONNREFUSED. The docs.cntd.ru host refused the connection outright; no page content of any kind was retrieved.",
        },
        {
            "tool": "WebFetch", "language": "ru",
            "url": "https://allgosts.ru/83/080/gost_r_56752-2015",
            "purpose": "evaluate an alternate GOST standards mirror for the same EEW standard, since docs.cntd.ru refused the connection",
            "result": "FAILED -- the page returned only a CAPTCHA verification challenge ('Проверка', bot-detection image challenge); no standard content, title, scope, or access terms were retrievable.",
        },
        {
            "tool": "WebFetch", "language": "ru",
            "url": "https://elibrary.ru",
            "purpose": "evaluate eLIBRARY.ru's homepage access/license/registration terms directly",
            "result": "FAILED -- WebFetch timed out after 60000ms; no page content retrieved this attempt.",
        },
        {
            "tool": "WebFetch", "language": "ru",
            "url": "https://cyberleninka.ru",
            "purpose": "evaluate CyberLeninka's overall scope and license model as a repository class (directive's 'institute report archives and wherever the research leads')",
            "result_evidence_quote": "CyberLeninka is a Russian scientific digital library built on open science principles... Content is 'размещаются по лицензии Creative Commons Attribution (CC-BY)'... 'бесплатный оперативный доступ к научным публикациями'.",
        },
        {
            "tool": "WebFetch", "language": "ru",
            "url": "https://vsegost.com/Catalog/32/32459.shtml",
            "purpose": "evaluate a third GOST standards mirror (after cntd.ru refused and allgosts.ru CAPTCHA-blocked) for the related GOST 12497-78 epoxy-groups method, to confirm whether this mirror class exposes free full text or access terms",
            "result_evidence_quote": "GOST 12497-78: 'Пластмассы. Методы определения эпоксидных групп'... The page displays thumbnail links to 12 document pages but does not explicitly state whether full-text access is free or requires payment. No licensing information is provided.",
        },
        {
            "tool": "curl_raw_http_xbabe1", "language": "ru",
            "url": "https://elibrary.ru/",
            "purpose": "confirm raw-HTTP reachability of eLIBRARY.ru independent of the WebFetch tool layer, since WebFetch(elibrary.ru) timed out",
            "result": "HTTP 302 (redirect) -- host is reachable and responds; WebFetch's timeout was tool/content-processing-side, not a network-level block, unlike the docs.cntd.ru case below.",
        },
        {
            "tool": "curl_raw_http_xbabe1", "language": "ru",
            "url": "https://www.elibrary.ru/project_risc.asp",
            "purpose": "confirm raw-HTTP reachability of the RSCI (РИНЦ)-specific page directly named by the directive",
            "result": "HTTP 302 (redirect) -- reachable.",
        },
        {
            "tool": "curl_raw_http_xbabe1", "language": "ru",
            "url": "https://docs.cntd.ru",
            "purpose": "determine whether the WebFetch docs.cntd.ru ECONNREFUSED failure was tool-specific or network-level, mirroring PROBE-WEB's CNKI cross-check methodology",
            "result": "FAILED -- HTTP 000 (curl exit 28, connection timeout) via raw curl too, confirming the docs.cntd.ru failure is a network/routing-level block from this host, not a WebFetch-tool-specific refusal.",
        },
    ],
    "no_acquisition_attestation": (
        "No dataset file, record set, table, standard full-text PDF, or bulk content was "
        "downloaded, cached, or scraped this fire. All 12 WebSearch calls returned ranked "
        "result snippets only. All 7 WebFetch calls retrieved the tool's own evaluative "
        "summary of page content (bibliographic metadata, access-tier descriptions, license "
        "statements) or a structured failure (ECONNREFUSED / CAPTCHA-block / timeout) -- never "
        "raw page bytes written to any file on xbabe2. The 3 curl calls were HTTP status/"
        "reachability checks (-o /dev/null, body discarded). Nothing beyond this ledger line, "
        "the disposition-ledger and coverage-map entries it supports, this item's work/ "
        "diagnostics, and this fire's signed receipt was written under mvp20-split."
    ),
    "next_run_should_extend": (
        "Untouched this fire, open for a future DR-LANG-RU or adjacent fire: (1) protect.gost.ru "
        "(official Rosstandart portal) was surfaced but not WebFetched directly -- a retry could "
        "confirm official free/paid full-text access terms for GOST Р 56752-2015 and GOST "
        "34388-2018 beyond the third-party-mirror evidence gathered this fire; (2) the Russian "
        "Maritime Register of Shipping's full Rules for Classification and Construction PDF "
        "(and Appendix 52 specifically) was located but not extracted -- no-acquisition "
        "discipline deliberately deferred this; (3) eLIBRARY.ru item id=24102757 (carbon-"
        "nanotube epoxy cure-kinetics DSC study) surfaced as access-restricted to unregistered "
        "users -- not independently evaluated for gap-fit beyond its title; (4) GOST 9.032 and "
        "GOST 9.401 (the general anti-corrosion coating-system standards named by query 2) were "
        "not individually resolved to their own standard-detail pages; (5) ЦНИИ КМ «Прометей»'s "
        "own institutional publication archive (distinct from third-party citations of its "
        "recommendations) was not directly located or searched."
    ),
    "previously_supplied_ru_candidates": {
        "none_found": True,
        "source_paths_checked": [
            "amphora-dataset-recon/evidence/phase0/repairs/DR-RUBRIC/work/candidate_snapshot.v1.json",
            "feedback/v1/dataset_sources.json",
            "feedback/v2/catalog.json",
            "feedback/v3/catalog.json",
            "/home/ubuntu/amphora-cron/data-acquisition-queue.jsonl (xbabe1)",
        ],
    },
}

# ---------------------------------------------------------------------------
# 2. disposition-ledger.v1.jsonl new lines (manifest + 6 candidate dispositions)
# ---------------------------------------------------------------------------
DL_PATH = LEDGERS / "disposition-ledger.v1.jsonl"
dl_before = DL_PATH.read_bytes()
dl_prior_prefix_sha = sha(dl_before)
dl_prior_lines = dl_before.decode("utf-8").splitlines()
dl_prior_line_count = len(dl_prior_lines)

manifest = {
    "candidates_pinned": [],
    "date": DATE,
    "entry_type": "candidate_intake_manifest",
    "fire_id": FIRE_ID,
    "framing": "AUDIT-ONLY",
    "note": (
        "ZERO previously-supplied Russian-language candidates were found anywhere in the "
        "portfolio as of this fire's start. Searched: (1) DR-RUBRIC's frozen "
        "candidate_snapshot.v1.json (candidates C1-C4 -- all zh/ja, none ru); (2) "
        "feedback/v1/dataset_sources.json (schema amphora.feedback_v1.dataset_sources.v1, "
        "'sources' array -- no Russian-origin or Russian-language source_url/id found by "
        "direct read); (3) feedback/v2/catalog.json, feedback/v3/catalog.json (schema "
        "amphora.data-catalog.v2/v3, source arrays -- no Russian-origin source found by direct "
        "read; a naive substring grep for 'ru' only matched incidental English words like "
        "'true'/'structure', not a real Russian-language entry); (4) "
        "/home/ubuntu/amphora-cron/data-acquisition-queue.jsonl on xbabe1 (grepped for "
        "russia|russian|gost|elibrary|viam -- the only hit was DR-LANG-DE's own Kuron 1984 "
        "German entry, a false positive from 'russia' not appearing at all; zero real Russian "
        "matches). This satisfies the directive's and this item's own done_criterion "
        "alternative branch: 'Previously-supplied candidates in these languages must be "
        "independently rediscovered OR THEIR ABSENCE EXPLAINED.' The absence is explained "
        "above with the exact source paths checked; there is nothing to rediscover. "
        "Positive-control mutant 5 (below) therefore uses a SYNTHETIC previously-supplied-"
        "candidate ID to prove the rediscovery-recall checker rule is a real, non-vacuous "
        "check rather than one that can never fire because the input list is empty by "
        "construction -- mirroring the DR-LANG-DE fire's identical situation and fix."
    ),
    "run_id": RUN_ID,
    "schema": "amphora.dataset-recon.disposition-ledger.v1",
    "source_paths_checked_for_prior_ru_candidates": [
        "amphora-dataset-recon/evidence/phase0/repairs/DR-RUBRIC/work/candidate_snapshot.v1.json",
        "feedback/v1/dataset_sources.json",
        "feedback/v2/catalog.json",
        "feedback/v3/catalog.json",
        "/home/ubuntu/amphora-cron/data-acquisition-queue.jsonl (xbabe1)",
    ],
}

RUBRIC_PATH = "amphora-dataset-recon/evidence/phase0/repairs/DR-RUBRIC/work/rubric.v1.json"


def score(dims):
    total = sum(dims.values())
    overall = round(total / 6.0, 4)
    if dims["rights_clarity"] == 0 or dims["acquisition_cost_friction"] == 0 or dims["gap_fit"] == 0:
        verdict = "REJECTED"
    elif overall >= 7.0 and dims["rights_clarity"] >= 5 and dims["acquisition_cost_friction"] >= 4:
        verdict = "RECOMMENDED"
    else:
        verdict = "CONDITIONAL"
    return overall, verdict


candidates_raw = [
    {
        "candidate_id": "DR-LANG-RU-01",
        "name": "Lundin, A.G., Ostapkovich, A.M., Yushkova, E.Yu. (2005). \"Кинетика отверждения эпоксидных смол аминами\" (Kinetics of Hardening of Epoxide Resins with Amines)",
        "native_citation": "Кинетика отверждения эпоксидных смол аминами",
        "url": "https://cyberleninka.ru/article/n/kinetika-otverzhdeniya-epoksidnyh-smol-aminami",
        "publisher_custodian": "Известия высших учебных заведений. Химия и химическая технология (Proceedings of Higher Educational Institutions. Chemistry and Chemical Technology), 2005; hosted open-access on CyberLeninka.",
        "coverage": "NMR-spectroscopy-based cure-kinetics study of epoxy resin ED-16 with amine hardeners including aromatic amines and aminotriazoles; reports temperature-dependent NMR second moments and spin-lattice relaxation times (T1), and cure-rate dependence on amine-group count and reactive-proton count.",
        "license_evidence_quote": "The page displays a CC BY (Creative Commons Attribution) license icon, indicating open-access distribution with attribution requirements.",
        "module_gaps": ["amphora-cure-kinetics"],
        "dims": {"gap_fit": 8, "provenance_measurement_quality": 6, "rights_clarity": 8, "uniqueness": 10, "integrity_risk": 8, "acquisition_cost_friction": 10},
        "translation_confidence": "native_script_verified_high",
        "integrity_risks": ["locale_unit_convention_unverified"],
        "translation_confidence_note": "Native Cyrillic title/author/journal fields were read directly from the CyberLeninka page; the quantitative NMR relaxation-time and second-moment values were not independently re-verified for decimal-comma-vs-period convention against the original PDF this fire (WebFetch's English AI summary only), per the directive's rule-5 locale-hazard discipline -- flagged rather than silently trusted.",
        "standard_mapping": {"published_standard": "NMR spectroscopy (no named ASTM/GOST test-method standard for this academic cure-kinetics study)", "astm_iso_equiv": "N/A -- academic measurement method, not a certified test standard", "comparability_rating": "method_not_standard_based"},
        "next_human_action": "Human downloads the freely-available CyberLeninka PDF to extract the full NMR second-moment/T1 dataset and confirm decimal-convention/unit handling before any quantitative reuse in the cure-kinetics benchmark; CC BY attribution required.",
        "confidence_flag": "MEDIUM",
    },
    {
        "candidate_id": "DR-LANG-RU-02",
        "name": "ГОСТ 34388-2018 (ISO 9227:2012) Трубы стальные. Метод испытаний коррозионной стойкости в соляном тумане",
        "native_citation": "ГОСТ 34388-2018 (ISO 9227:2012) Трубы стальные. Метод испытаний коррозионной стойкости в соляном тумане",
        "url": "http://docs.cntd.ru/document/1200160489",
        "publisher_custodian": "Rosstandart / Межгосударственный совет по стандартизации, метрологии и сертификации (interstate GOST standard).",
        "coverage": "Salt-spray (neutral, acetic-acid, copper-accelerated-acetic-acid) corrosion-resistance test-method standard, explicitly stated as a technical modification of ISO 9227:2012 -- directly satisfies the directive's standard-mapping requirement for the portfolio's salt-spray corrosion-test baseline (ASTM B117-class).",
        "license_evidence_quote": "ГОСТ 34388-2018 модифицирован на основе международного стандарта ISO 9227:2012",
        "module_gaps": ["amphora-public-corrosion-benchmark"],
        "dims": {"gap_fit": 8, "provenance_measurement_quality": 7, "rights_clarity": 2, "uniqueness": 6, "integrity_risk": 8, "acquisition_cost_friction": 4},
        "translation_confidence": "native_script_verified_high",
        "integrity_risks": ["digitization_quality_concern"],
        "translation_confidence_note": "The ISO 9227:2012 equivalence is stated directly in the standard's own recorded title/designation (a strong signal), but the primary docs.cntd.ru page itself could not be directly WebFetched (connection refused) or confirmed via allgosts.ru (CAPTCHA-blocked) this fire -- confidence rests on WebSearch-surfaced title text, not a directly-fetched primary page, flagged accordingly.",
        "standard_mapping": {"published_standard": "GOST 34388-2018", "astm_iso_equiv": "ISO 9227:2012 (explicit technical-modification adoption); method-class-comparable to ASTM B117", "comparability_rating": "iso_direct_adoption_stated"},
        "next_human_action": "Human with institutional/Rosstandart access confirms full clause-by-clause text and purchases/accesses the official protect.gost.ru copy to verify the technical-modification deltas from ISO 9227:2012 before citing as a certified equivalence.",
        "confidence_flag": "MEDIUM",
    },
    {
        "candidate_id": "DR-LANG-RU-03",
        "name": "VIAM Testing Center -- Коррозионные испытания (isp.viam.ru)",
        "native_citation": "Коррозионные испытания",
        "url": "https://isp.viam.ru/corrosiontests",
        "publisher_custodian": "Испытательный центр НИЦ «Курчатовский институт» - ВИАМ (Testing Center of NRC Kurchatov Institute -- VIAM), Moscow.",
        "coverage": "Commercial accelerated-corrosion testing services (salt/marine fog, aggressive-gas exposure, fuel/oil/hydraulic-fluid corrosivity, local-corrosion resistance) for aviation, maritime, and defense clients. No published dataset -- services offered on a contract basis only.",
        "license_evidence_quote": "No explicit open license or public data sharing terms are stated on this page—services are available through commercial engagement.",
        "module_gaps": ["amphora-public-corrosion-benchmark", "amphora-barrier-corrosion-score"],
        "dims": {"gap_fit": 0, "provenance_measurement_quality": 0, "rights_clarity": 2, "uniqueness": 10, "integrity_risk": 10, "acquisition_cost_friction": 4},
        "translation_confidence": "native_script_verified_high",
        "integrity_risks": [],
        "translation_confidence_note": "Directly WebFetched; no ambiguity about page content -- a service-offering page, not a dataset, hence gap_fit scored off_scope=0 per the rubric floor rule (mirrors the de fire's identical treatment of Fraunhofer IFAM and GfKORR).",
        "standard_mapping": {"published_standard": "Not stated on this page", "astm_iso_equiv": "N/A", "comparability_rating": "not_applicable_service_not_dataset"},
        "next_human_action": "None -- this is a paid testing service, not a data source; no human action unlocks it as a dataset candidate.",
        "confidence_flag": "LOW",
    },
    {
        "candidate_id": "DR-LANG-RU-04",
        "name": "ФГУП ЦНИИ КМ «Прометей» (Central Research Institute of Structural Materials \"Prometey\")",
        "native_citation": "ФГУП ЦНИИ КМ «Прометей»",
        "url": "https://www.crism-prometey.ru/upload/iblock/82b/ulnd06t61v2aw24m08ogmkf19yb00xie/Russian2_86_2016.pdf",
        "publisher_custodian": "NRC Kurchatov Institute -- ЦНИИ КМ «Прометей», Saint Petersburg; Russia's leading shipbuilding/marine-materials science center.",
        "coverage": "Institute-level product recommendations (coating materials ФЛК-2, ФЛК-3, ФЛК-ПА for hot-seawater corrosion protection up to 100C) surfaced only via secondary/third-party citation this fire; no institute-published dataset, test report, or measurement record was itself located and evaluated.",
        "license_evidence_quote": "no specific downloadable report or dataset located this fire, only product-recommendation summaries via secondary sources.",
        "module_gaps": ["amphora-public-corrosion-benchmark", "amphora-owk-adhesion"],
        "dims": {"gap_fit": 0, "provenance_measurement_quality": 0, "rights_clarity": 2, "uniqueness": 10, "integrity_risk": 10, "acquisition_cost_friction": 4},
        "translation_confidence": "native_script_verified_high",
        "integrity_risks": [],
        "translation_confidence_note": "Institute name and product designations confirmed in native Cyrillic; gap_fit scored off_scope=0 because no institute-published, independently evaluable document was actually located this fire -- only secondary citations of its recommendations, which is not itself a scoreable data source.",
        "standard_mapping": {"published_standard": "Not identified this fire", "astm_iso_equiv": "N/A", "comparability_rating": "not_applicable_no_document_located"},
        "next_human_action": "Human searches ЦНИИ КМ «Прометей»'s own institutional publication archive directly (not yet located this fire) for a citable primary report.",
        "confidence_flag": "LOW",
    },
    {
        "candidate_id": "DR-LANG-RU-05",
        "name": "eLIBRARY.ru / Российский индекс научного цитирования (РИНЦ, Russian Science Citation Index)",
        "native_citation": "Российский индекс научного цитирования (РИНЦ)",
        "url": "https://lib.unn.ru/elektronnye-resursy/rossijskie-elektronnye-resursy/risc/",
        "publisher_custodian": "eLIBRARY.ru, in cooperation with Russian academic institutions; national citation-index infrastructure, directly named by the directive as 'eLIBRARY/RSCI'.",
        "coverage": "National citation-index aggregator covering 12+ million publications by Russian authors and 6,000+ current Russian journals; the primary literature-discovery layer for Russian-language coatings/materials-science research (surfaced the CyberLeninka and raw eLIBRARY.ru items evaluated separately in this fire).",
        "license_evidence_quote": "РИНЦ is completely free; you only need to register on the eLibrary.Ru website to use all its features... To access full-text versions of some journals, a subscription is required; otherwise, only keywords and abstracts will be available.",
        "module_gaps": [],
        "dims": {"gap_fit": 8, "provenance_measurement_quality": 3, "rights_clarity": 5, "uniqueness": 6, "integrity_risk": 10, "acquisition_cost_friction": 6},
        "translation_confidence": "native_script_verified_high",
        "integrity_risks": [],
        "translation_confidence_note": "Access-terms text directly WebSearch-confirmed and raw-HTTP-reachability-confirmed via curl (HTTP 302 both elibrary.ru/ and project_risc.asp) independent of the WebFetch tool layer, which itself timed out -- cross-tool corroboration, same methodology as PROBE-WEB's CNKI check.",
        "standard_mapping": {"published_standard": "N/A -- literature aggregator, not a measurement-standard source", "astm_iso_equiv": "N/A", "comparability_rating": "not_applicable"},
        "next_human_action": "Human registers a free eLIBRARY.ru account to browse citation-index metadata at no cost; a paid subscription is a separate, later decision only needed for specific subscription-gated full-text journal access.",
        "confidence_flag": "MEDIUM",
    },
    {
        "candidate_id": "DR-LANG-RU-06",
        "name": "docs.cntd.ru -- Электронный фонд правовых и нормативно-технических документов (GOST standards mirror)",
        "native_citation": "Электронный фонд правовых и нормативно-технических документов",
        "url": "https://docs.cntd.ru",
        "publisher_custodian": "Kodeks/Consultant-class Russian legal/technical-document aggregator (third-party GOST mirror, not Rosstandart itself).",
        "coverage": "Unknown -- platform unreachable from this host both via WebFetch (ECONNREFUSED) and raw curl (HTTP 000, connection timeout) this fire.",
        "license_evidence_quote": "FAILED -- HTTP 000 (curl exit 28, connection timeout) via raw curl too, confirming the docs.cntd.ru failure is a network/routing-level block from this host, not a WebFetch-tool-specific refusal.",
        "module_gaps": [],
        "dims": {"gap_fit": 5, "provenance_measurement_quality": 0, "rights_clarity": 2, "uniqueness": 6, "integrity_risk": 0, "acquisition_cost_friction": 0},
        "translation_confidence": "no_translation_attempted_unknown",
        "integrity_risks": [],
        "translation_confidence_note": "No page content of any kind was retrieved (network-level block via two independent tools -- WebFetch and raw curl); nothing to translate. Failure mode is connection-refused/timeout, distinct from PROBE-WEB's CNKI TLS-certificate-mismatch failure -- disclosed as a different mechanism, not conflated with it.",
        "standard_mapping": {"published_standard": "N/A -- platform unreachable, no specific standard content retrieved", "astm_iso_equiv": "N/A", "comparability_rating": "unconfirmed_unreachable"},
        "next_human_action": "Human attempts access from a host/egress path not affected by this connection-level block, or uses the official protect.gost.ru portal / a paid GOST database service instead of this third-party mirror.",
        "confidence_flag": "LOW",
    },
]

disp_this_fire = []
for c in candidates_raw:
    overall, verdict = score(c["dims"])
    reason = (
        f"rubric.v1.json score: " +
        ", ".join(f"{k}={v}" for k, v in c["dims"].items()) +
        f", overall={overall} -> {verdict}. Next action: {c['next_human_action']}"
    )
    disp_this_fire.append({
        "candidate_id": c["candidate_id"],
        "confidence_flag": c["confidence_flag"],
        "coverage": c["coverage"],
        "date": DATE,
        "disposition": {"reason": reason, "verdict": verdict},
        "entry_type": "candidate_disposition",
        "fire_id": FIRE_ID,
        "framing": "AUDIT-ONLY",
        "integrity_risks": c["integrity_risks"],
        "language": "ru",
        "license_evidence_quote": c["license_evidence_quote"],
        "name": c["name"],
        "native_citation": c["native_citation"],
        "rank": 0,
        "rubric_dimensions": c["dims"],
        "rubric_overall_score": overall,
        "rubric_path": RUBRIC_PATH,
        "run_id": RUN_ID,
        "schema": "amphora.dataset-recon.disposition-ledger.v1",
        "serves": {"module_gaps": c["module_gaps"], "recipe_elements": []},
        "snapshot_date": DATE,
        "standard_mapping": c["standard_mapping"],
        "translation_confidence": c["translation_confidence"],
        "translation_confidence_note": c["translation_confidence_note"],
        "url": c["url"],
        "next_human_action": c["next_human_action"],
        "publisher_custodian": c["publisher_custodian"],
    })

ranked = sorted(disp_this_fire, key=lambda d: (-d["rubric_overall_score"], d["candidate_id"]))
for i, d in enumerate(ranked, start=1):
    d["rank"] = i

dl_lines = [manifest] + disp_this_fire
dl_new_content_lines = [json.dumps(l, sort_keys=True, ensure_ascii=False) for l in dl_lines]
dl_appended_text = "\n".join(dl_new_content_lines) + "\n"
dl_appended_sha = sha(dl_appended_text.encode("utf-8"))
dl_appended_line_start = dl_prior_line_count + 1
dl_appended_line_end = dl_prior_line_count + len(dl_lines)
dl_new_content = dl_before + (b"" if dl_before.endswith(b"\n") or not dl_before else b"\n") + dl_appended_text.encode("utf-8")
dl_file_sha_after = sha(dl_new_content)

# ---------------------------------------------------------------------------
# search-record file assembly
# ---------------------------------------------------------------------------
sr_appended_line_no = sr_prior_line_count + 1
sr_line_text = json.dumps(search_record_line_obj, sort_keys=True, ensure_ascii=False)
sr_appended_sha = sha((sr_line_text + "\n").encode("utf-8"))
sr_new_content = sr_before + (b"" if sr_before.endswith(b"\n") or not sr_before else b"\n") + (sr_line_text + "\n").encode("utf-8")
sr_file_sha_after = sha(sr_new_content)

# ---------------------------------------------------------------------------
# 3. coverage-map.v1.json merge (full-file replace, preserving all prior gaps)
# ---------------------------------------------------------------------------
CM_PATH = LEDGERS / "coverage-map.v1.json"
cm_before_bytes = CM_PATH.read_bytes()
cm_before_sha = sha(cm_before_bytes)
cm_before = json.loads(cm_before_bytes)

new_gaps = [
    {
        "gap_id": "cure-kinetics-ru",
        "module_gaps": ["amphora-cure-kinetics"],
        "best_recommended": "DR-LANG-RU-01",
        "best_conditional": None,
        "commissioned_measurement_candidate": None,
        "note": "CyberLeninka open-access (CC BY) NMR cure-kinetics study (Lundin, Ostapkovich, Yushkova, 2005) for epoxy resin ED-16 with amine hardeners -- the first RU-language RECOMMENDED-grade candidate, mirroring the de fire's TU Darmstadt dissertation as the campaign's second-ever dataset-ledger RECOMMENDED entry.",
    },
    {
        "gap_id": "salt-spray-standard-mapping-ru",
        "module_gaps": ["amphora-public-corrosion-benchmark"],
        "best_recommended": None,
        "best_conditional": "DR-LANG-RU-02",
        "commissioned_measurement_candidate": None,
        "note": "GOST 34388-2018 confirmed explicitly modified from ISO 9227:2012 (source states 'модифицирован на основе международного стандарта ISO 9227:2012'). This is the THIRD independent language-community confirmation this campaign that the underlying salt-spray baseline is ISO 9227 (ja's JIS Z 2371 and de's DIN EN ISO 9227 both converge on the same standard).",
    },
    {
        "gap_id": "gost-eew-testdata-annex-ru",
        "module_gaps": ["amphora-molecule-property"],
        "best_recommended": None,
        "best_conditional": None,
        "commissioned_measurement_candidate": (
            "No open GOST test-data annex for the epoxy-equivalent-weight (EEW) method was "
            "found -- an honest empty result for the directive's 'GOST test-data annexes' scope "
            "element, per rule 7. Standard method confirmed mapped: GOST Р 56752-2015 (ИСО "
            "3001:1999) -- the THIRD independent language-community convergence on ISO 3001:1999 "
            "for this exact method, after ja's JIS K 7236 and de's DIN EN ISO 3001. Note: the "
            "portfolio already computes EEW/AHEW internally via its own ChEBI+RDKit pipeline "
            "(amphora-molecule-property EEW/AHEW verification result, err 0.03) -- this ru "
            "finding is a standard-citation/mapping enrichment only, not a data gap requiring "
            "commissioning. Confidence caveat: the ISO-equivalence text was WebSearch-surfaced "
            "only -- both attempts to directly WebFetch the primary GOST Р 56752-2015 page "
            "failed this fire (docs.cntd.ru refused the connection, allgosts.ru returned a "
            "CAPTCHA challenge) -- disclosed, not silently treated as page-confirmed."
        ),
    },
    {
        "gap_id": "corrosion-database-ru",
        "module_gaps": ["amphora-public-corrosion-benchmark", "amphora-barrier-corrosion-score"],
        "best_recommended": None,
        "best_conditional": None,
        "commissioned_measurement_candidate": (
            "No open Russian atmospheric/general corrosion database was found this fire -- an "
            "honest empty result. Both national-institute candidates found (VIAM's isp.viam.ru "
            "corrosion-testing center, DR-LANG-RU-03; TsNII KM Prometey, DR-LANG-RU-04) are "
            "REJECTED on the rubric's gap_fit floor -- neither publishes an open dataset, both "
            "are service/recommendation sources. This mirrors the ja fire's identical "
            "PoLyInfo/MatNavi rejection pattern for a distinct underlying reason (there, rights-"
            "clarity floor; here, gap_fit floor since no evaluable document was even located)."
        ),
    },
    {
        "gap_id": "marine-coating-gost-standard-mapping",
        "module_gaps": ["amphora-ip-fto-guard", "amphora-owk-adhesion"],
        "best_recommended": None,
        "best_conditional": None,
        "commissioned_measurement_candidate": (
            "No ship-hull-specific GOST antifouling/anticorrosive paint standard number "
            "(analogous to zh's GB/T 6822) was found despite two explicit searches -- honest "
            "negative result, the THIRD independent language-community confirmation of this "
            "exact null finding (ja's JIS search and de's DIN search each also found no "
            "ship-hull-specific national standard number; only the zh fire found one, GB/T "
            "6822-2024). GOST 9.032 and GOST 9.401 are the general anti-corrosion "
            "coating-system standards referenced alongside ISO 12944 (mirrors ja's JIS K 5551 "
            "and de's DIN EN ISO 12944 general-scope findings). The Russian Maritime Register "
            "of Shipping (РС) publishes Appendix 52, an inspection/assessment guideline for "
            "ship coating condition -- a real, gap-relevant document, but an inspection "
            "methodology, not a distinct product performance standard number."
        ),
    },
    {
        "gap_id": "ru-general-aggregator-access",
        "module_gaps": [],
        "best_recommended": None,
        "best_conditional": "DR-LANG-RU-05",
        "commissioned_measurement_candidate": None,
        "note": (
            "eLIBRARY.ru / РИНЦ (DR-LANG-RU-05, the directive-named 'eLIBRARY/RSCI') is "
            "reachable (curl HTTP 302, independent of the WebFetch tool layer which itself "
            "timed out) and free to register for citation-index browsing, but full-text "
            "access to many journals is subscription-gated. docs.cntd.ru (DR-LANG-RU-06, a "
            "third-party GOST standards mirror) is REJECTED -- network-unreachable from this "
            "host via both WebFetch and raw curl this fire, a DIFFERENT failure mechanism "
            "(connection-refused/timeout) than the zh fire's CNKI TLS-certificate mismatch, "
            "not conflated with it. allgosts.ru (a second GOST mirror) is reachable but "
            "CAPTCHA-blocks automated access; vsegost.com (a third GOST mirror) is directly "
            "reachable and returned real standard content."
        ),
    },
]

cm_after = copy.deepcopy(cm_before)
cm_after["gaps"] = cm_before.get("gaps", []) + new_gaps
cm_after["fire_id"] = FIRE_ID
cm_after["run_id"] = RUN_ID
cm_after["snapshot_date"] = DATE
cm_after["scope_note"] = (
    "Merged: zh (Chinese, DR-LANG-ZH fire) + ja (Japanese, DR-LANG-JA fire) + de (German, "
    "DR-LANG-DE fire) + ru (Russian, DR-LANG-RU fire) language communities. Each gaps[] "
    "entry's gap_id and module_gaps disambiguate scope; no entry from any prior fire was "
    "removed or rewritten."
)
cm_after["ru_empty_result_gap_note"] = (
    "gost-eew-testdata-annex-ru, corrosion-database-ru, and marine-coating-gost-standard-"
    "mapping are all genuine empty results this fire (see gaps[] entries) -- honestly "
    "reported, not padded, and not silently converted into fabricated candidates."
)
cm_after["ru_no_empty_result_gap_this_fire"] = False
cm_after.pop("no_empty_result_gap_this_fire", None)
cm_after.pop("no_empty_result_gap_this_fire_note", None)
cm_after["gaps_not_yet_searched_this_fire"] = cm_before.get("gaps_not_yet_searched_this_fire", []) + [
    "protect.gost.ru official full-text access terms for GOST Р 56752-2015 / GOST 34388-2018 -- not directly WebFetched [ru, carried forward]",
    "Russian Maritime Register of Shipping Rules for Classification and Construction Appendix 52 full content -- located, not extracted (no-acquisition discipline) [ru, carried forward]",
    "eLIBRARY.ru item id=24102757 (carbon-nanotube epoxy cure-kinetics DSC study) -- access-restricted, not independently evaluated beyond title [ru, carried forward]",
    "TsNII KM Prometey's own institutional publication archive (distinct from third-party citations) -- not directly located [ru, carried forward]",
]

cm_after_bytes = canon(cm_after)
cm_after_sha = sha(cm_after_bytes)

# ---------------------------------------------------------------------------
# 4. Independent checker: 5-limb refutation criterion (Cyrillic-script analogue
#    of the zh/ja CJK-presence checker)
# ---------------------------------------------------------------------------
CYRILLIC_RE = re.compile(r"[Ѐ-ӿ]")


def has_cyrillic(s):
    return bool(CYRILLIC_RE.search(s or ""))


def check(disp_lines, sr_lines_all, previously_supplied_ids):
    violations = []
    dispositions = [d for d in disp_lines if d.get("entry_type") == "candidate_disposition"]

    def sr_text_for_lang(lang):
        parts = []
        for line in sr_lines_all:
            if line.get("language_communities_touched") and lang not in line["language_communities_touched"]:
                continue
            for q in line.get("queries", []):
                for k in ("query", "query_gloss_en", "purpose", "result_note", "result_summary",
                          "result_evidence_quote", "result", "sample_urls", "url",
                          "result_titles_observed"):
                    v = q.get(k)
                    if isinstance(v, list):
                        parts.extend(str(x) for x in v)
                    elif v:
                        parts.append(str(v))
        return "\n".join(parts)

    all_sr_text = sr_text_for_lang("ru")

    # Rule 1: citation_has_recorded_query_and_result
    for d in dispositions:
        url = d.get("url", "")
        if url and url not in all_sr_text:
            violations.append({"rule": "citation_has_recorded_query_and_result", "candidate_id": d["candidate_id"],
                                "reason": f"{d['candidate_id']}: url {url} does not appear in any recorded search-record query/result this fire"})

    # Rule 2: native_query_not_literal_translation -- every ru query string must contain Cyrillic
    for line in sr_lines_all:
        if line.get("language_communities_touched") and "ru" not in line["language_communities_touched"]:
            continue
        for q in line.get("queries", []):
            if q.get("language") == "ru" and "query" in q:
                if not has_cyrillic(q["query"]):
                    violations.append({"rule": "native_query_not_literal_translation", "candidate_id": None,
                                        "reason": f"ru query field contains no Cyrillic characters: '{q['query']}'"})

    # Rule 3: license_text_matches_live_evidence
    for d in dispositions:
        quote = d.get("license_evidence_quote", "")
        if quote and quote not in all_sr_text:
            violations.append({"rule": "license_text_matches_live_evidence", "candidate_id": d["candidate_id"],
                                "reason": f"{d['candidate_id']}: license_evidence_quote does not appear verbatim in this fire's recorded search-record evidence text"})

    # Rule 4: native_script_citation_integrity -- every ru native_citation must contain Cyrillic
    for d in dispositions:
        if d.get("language") == "ru":
            nc = d.get("native_citation", "")
            if not has_cyrillic(nc):
                violations.append({"rule": "native_script_citation_integrity", "candidate_id": d["candidate_id"],
                                    "reason": f"{d['candidate_id']}: native_citation '{nc}' contains no Cyrillic characters"})

    # Rule 5: rediscovery_recall
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


PREVIOUSLY_SUPPLIED_RU = []  # genuinely empty -- see manifest note

sr_all_lines = list(sr_prior_lines_parsed) + [search_record_line_obj]
dl_this_fire = dl_lines

runA = check(dl_this_fire, sr_all_lines, PREVIOUSLY_SUPPLIED_RU)
runB = check(dl_this_fire, sr_all_lines, PREVIOUSLY_SUPPLIED_RU)
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

sr_mut1 = copy.deepcopy(sr_all_lines)
target_url = "https://isp.viam.ru/corrosiontests"
for line in sr_mut1:
    for q in line.get("queries", []):
        for k in ("query", "result_note", "result_summary", "result_evidence_quote", "result", "sample_urls", "url"):
            v = q.get(k)
            if isinstance(v, list):
                q[k] = [x for x in v if target_url not in str(x)]
            elif isinstance(v, str) and target_url in v:
                q[k] = v.replace(target_url, "REDACTED")
r1 = check(dl_this_fire, sr_mut1, PREVIOUSLY_SUPPLIED_RU)
mutants_out["missing_recorded_query"] = {
    "expected_rule": "citation_has_recorded_query_and_result",
    "how_planted": f"Scrubbed every occurrence of DR-LANG-RU-03's url ({target_url}) from a copy of this fire's search-record queries/results.",
    "expected_rule_fired": True,
    "refutation_criterion_fired": r1["refutation_criterion_fired"],
    "violations": r1["violations"],
}

sr_mut2 = copy.deepcopy(sr_all_lines)
for line in sr_mut2:
    for q in line.get("queries", []):
        if q.get("language") == "ru" and q.get("query", "").startswith("эпоксидная смола отверждение амин кинетика"):
            q["query"] = "epoxy resin cure amine kinetics data elibrary"
r2 = check(dl_this_fire, sr_mut2, PREVIOUSLY_SUPPLIED_RU)
mutants_out["literal_english_translation_query"] = {
    "expected_rule": "native_query_not_literal_translation",
    "how_planted": "Replaced the native ru query string 'эпоксидная смола отверждение амин кинетика данные elibrary' with its literal English gloss, while leaving language:'ru' unchanged.",
    "expected_rule_fired": True,
    "refutation_criterion_fired": r2["refutation_criterion_fired"],
    "violations": r2["violations"],
}

dl_mut3 = copy.deepcopy(dl_this_fire)
for d in dl_mut3:
    if d.get("candidate_id") == "DR-LANG-RU-01":
        d["license_evidence_quote"] = "The article is fully open access with no license restriction of any kind and no attribution required."
r3 = check(dl_mut3, sr_all_lines, PREVIOUSLY_SUPPLIED_RU)
mutants_out["license_text_diverges"] = {
    "expected_rule": "license_text_matches_live_evidence",
    "how_planted": "Overwrote DR-LANG-RU-01's license_evidence_quote with a fabricated 'no restriction, no attribution' claim contradicting the recorded WebFetch evidence (which states a CC BY attribution-required license).",
    "expected_rule_fired": True,
    "refutation_criterion_fired": r3["refutation_criterion_fired"],
    "violations": r3["violations"],
}

dl_mut4 = copy.deepcopy(dl_this_fire)
for d in dl_mut4:
    if d.get("candidate_id") == "DR-LANG-RU-04":
        d["native_citation"] = "TsNII KM Prometey"
r4 = check(dl_mut4, sr_all_lines, PREVIOUSLY_SUPPLIED_RU)
mutants_out["native_citation_not_resolvable"] = {
    "expected_rule": "native_script_citation_integrity",
    "how_planted": "Replaced DR-LANG-RU-04's native_citation (Cyrillic institute name) with its bare Latin-script romanization.",
    "expected_rule_fired": True,
    "refutation_criterion_fired": r4["refutation_criterion_fired"],
    "violations": r4["violations"],
}

r5_real = check(dl_this_fire, sr_all_lines, ["SYNTHETIC-RU-PRIOR-CANDIDATE-NOT-REAL"])
mutants_out["rediscovery_dropped"] = {
    "expected_rule": "rediscovery_recall",
    "how_planted": "Injected a SYNTHETIC previously-supplied-candidate id ('SYNTHETIC-RU-PRIOR-CANDIDATE-NOT-REAL') into the checker's previously_supplied_ids list, since the real list is genuinely empty this fire (see manifest note) -- no disposition entry anywhere has rediscovers=='SYNTHETIC-RU-PRIOR-CANDIDATE-NOT-REAL', so this proves rule 5 is a real, non-vacuous check.",
    "expected_rule_fired": True,
    "refutation_criterion_fired": r5_real["refutation_criterion_fired"],
    "violations": r5_real["violations"],
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

shas = {
    "sr_appended_line_no": sr_appended_line_no,
    "sr_prior_prefix_sha": sr_prior_prefix_sha,
    "sr_appended_sha": sr_appended_sha,
    "sr_file_sha_after": sr_file_sha_after,
    "dl_appended_line_start": dl_appended_line_start,
    "dl_appended_line_end": dl_appended_line_end,
    "dl_prior_prefix_sha": dl_prior_prefix_sha,
    "dl_appended_sha": dl_appended_sha,
    "dl_file_sha_after": dl_file_sha_after,
    "cm_before_sha": cm_before_sha,
    "cm_after_sha": cm_after_sha,
    "runA_sha": sha(runA_bytes),
}
(WORK / "shas.json").write_bytes(canon(shas))

print("BUILD OK")
print("sr_appended_line_no", sr_appended_line_no)
print("dl_appended_range", dl_appended_line_start, dl_appended_line_end)
print("runA==runB byte-identical", sha(runA_bytes) == sha(runB_bytes))
print("real_refutation_criterion_fired", runA["refutation_criterion_fired"])
print("all_mutants_fired_correctly", all_mutants_fired)
for c in ranked:
    print(c["candidate_id"], c["disposition"]["verdict"], c["rubric_overall_score"])
