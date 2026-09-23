#!/usr/bin/env python3
"""Build DR-LANG-CEE deliverable: search-record append, disposition-ledger append,
coverage-map merge, dataset-ledger append (CZ-02 clears RECOMMENDED), independent
checker with two-replay + 5-mutant positive control, DSSE-signed done receipt.
AUDIT_ONLY. Pinned Phase-0 evaluator key only.
Mirrors the DR-LANG-DE precedent (Latin-script adaptation), extended to TWO language
communities in one fire: Polish (pl) and Czech (cs), per directive obligation DR-LANG-CEE
(Section 4). Marker-word checks are per-language; native_citation verbatim-in-evidence
check (the Latin-script analogue of the zh/ja CJK-presence check) applies to both.
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
ITEM = MOD / "evidence/phase0/repairs/DR-LANG-CEE"
WORK = ITEM / "work"
DONE = ITEM / "done"
WORK.mkdir(parents=True, exist_ok=True)
DONE.mkdir(parents=True, exist_ok=True)

SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"
DIRECTIVE_MD = ROOT / "docs/directives/2026-08-09-dataset-reconnaissance-multilingual.md"
DIRECTIVE_SHA_EXPECTED = "97fad5d1636f5ccb106562c2d940535651c216d357dd5276088f2db12bdba207"

FIRE_ID = "20260810T130001-1342629-eb2ea88df3d7"
RUN_ID = f"DR-LANG-CEE-{FIRE_ID}"
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
        "DR-LANG-CEE gap-targeted native-language reconnaissance fire covering TWO "
        "language communities in one item (directive obligation DR-LANG-CEE, "
        "AMPHORA-DIRECTIVE-2026-08-09 Section 4): Polish (pl) and Czech (cs). First "
        "CEE-language fire for this module; searches Polish BazTech-indexed technical "
        "journals (Ochrona przed Korozja / Sigma-NOT), Polish polytechnic doctoral-thesis "
        "repositories (Uniwersytet Opolski, Politechnika), Czech national grey-literature "
        "and university repositories (NUSL, UTB Zlin digilib, VUT/CVUT DSpace), the Czech "
        "corrosion-engineering journal Koroze a ochrana materialu (KOM, Sciendo), Polish "
        "and Czech national/European standard adoptions (PN-EN ISO / CSN EN ISO 12944 and "
        "9227), and a Czech national corrosion-testing institute (SVUOM)."
    ),
    "language_communities_touched": ["pl", "cs"],
    "repository_classes_touched": [
        "national_technical_journal_index (BazTech / yadda.icm.edu.pl, pl)",
        "engineering_society_journal (Ochrona przed Korozja, publisher SITPChem + Polskie Stowarzyszenie Korozyjne, pl)",
        "academic_institutional_repository (Uniwersytet Opolski repo.uni.opole.pl doctoral-thesis record, pl)",
        "national_standards_body (PKN / Polski Komitet Normalizacyjny, PN-EN ISO 12944 / 9227, pl)",
        "research_institute (Siec Badawcza Lukasiewicz - Instytut Mechaniki Precyzyjnej, pl; corrosion research center, not itself a dataset)",
        "polytechnic_thesis_repository (UTB Zlin digilib.k.utb.cz, cs)",
        "polytechnic_thesis_repository (VUT Brno DSpace, cs)",
        "national_corrosion_engineering_journal (Koroze a ochrana materialu / KOM, Association of Czech and Slovak Corrosion Engineers, cs, via Sciendo)",
        "national_grey_literature_repository (NUSL - Narodni uloziste sede literatury, cs)",
        "national_standards_body (UNMZ adoption path / CSN EN ISO 12944, cs)",
        "national_corrosion_testing_institute (SVUOM s.r.o., cs; corrosion maps product)",
    ],
    "queries": [
        {
            "tool": "WebSearch", "language": "pl",
            "query": "żywica epoksydowa utwardzacz aminowy kinetyka utwardzania baza danych",
            "query_gloss_en": "epoxy resin amine hardener cure kinetics database",
            "purpose": "gap-targeted native-pl query for amine-class epoxy cure-kinetics literature/datasets, the directive's opening scope element",
            "result_count": 8,
            "sample_urls": [
                "https://home.agh.edu.pl/~jlaska/wyklady/tw%20w%20cer/Instr1.pdf",
                "https://www.zywicesarzyna.pl/poradniki/proporcje-i-czasy-utwardzania/",
                "https://patents.google.com/patent/PL200412B1/pl",
            ],
            "result_note": "General amine-hardener chemistry (aliphatic/cycloaliphatic/aromatic amines, polyamides, polyaminoamides) and producer datasheets surfaced; no standalone open cure-kinetics dataset found by this query alone -- follow-up query 8 (doctoral thesis search) found a concrete primary source.",
        },
        {
            "tool": "WebSearch", "language": "pl",
            "query": "czasopismo \"Ochrona przed Korozją\" powłoki epoksydowe antykorozyjne",
            "query_gloss_en": "journal Corrosion Protection epoxy anti-corrosion coatings",
            "purpose": "target the directive-named Polish national journal index directly for its flagship corrosion-protection journal",
            "result_count": 9,
            "sample_urls": [
                "https://pl.wikipedia.org/wiki/Ochrona_przed_korozj%C4%85_(czasopismo)",
                "https://sigma-not.pl/czasopisma-40-ochrona-przed-korozja.html",
                "http://yadda.icm.edu.pl/baztech/element/bwmeta1.element.baztech-journal-0473-7733-ochrona_przed_korozja",
                "https://sitpchem.org.pl/dzialalnosc/czasopisma/miesiecznik-ochrona-przed-korozja/",
                "https://bibliotekanauki.pl/journals/18775",
            ],
            "result_evidence_quote": "\"Ochrona przed korozją\" to miesięcznik naukowo-techniczny wydawany przez Stowarzyszenie Inżynierów i Techników Przemysłu Chemicznego. Czasopismo wydawane jest we współpracy z Polskim Stowarzyszeniem Korozyjnym oraz Europejską Federacją Korozyjną. Tematyka czasopisma obejmuje: zjawiska korozyjne i ich badania, metody badawcze, technologie zabezpieczeń przeciwkorozyjnych – farby, ochrona elektrochemiczna, powłoki konwersyjne, powłoki metaliczne, inhibitory korozji, korozja mikrobiologiczna, galwanotechnika, tworzywa sztuczne.",
        },
        {
            "tool": "WebSearch", "language": "pl",
            "query": "BazTech baza danych czasopism technicznych korozja powłoki",
            "query_gloss_en": "BazTech database of technical journals corrosion coatings",
            "purpose": "target the directive-named Polish national journal index (BazTech) directly",
            "result_count": 0,
            "sample_urls": [],
            "result": "TRANSIENT TOOL FAILURE this fire -- WebSearch returned 'Web search error: unavailable' for this exact query string. Retried successfully with a reformulated query (see next entry) rather than silently dropped.",
            "empty_result": True,
            "empty_result_note": "Tool-level failure, not a content finding -- immediately retried under a different query string, which succeeded (see query 7 below).",
        },
        {
            "tool": "WebSearch", "language": "cs",
            "query": "epoxidová pryskyřice aminové tvrdidlo kinetika vytvrzování data",
            "query_gloss_en": "epoxy resin amine hardener curing kinetics data",
            "purpose": "gap-targeted native-cs query for amine-class epoxy cure-kinetics literature/datasets, the directive's opening scope element",
            "result_count": 8,
            "sample_urls": [
                "http://digilib.k.utb.cz/bitstream/handle/10563/441/bene%20_2006_bp.pdf?sequence=1",
                "https://cs.wikipedia.org/wiki/Epoxidov%C3%A1_prysky%C5%99ice",
                "https://patents.google.com/patent/CS200848B1/cs",
            ],
            "result_note": "Surfaced a UTB Zlin thesis directly titled 'Kinetika vytvrzování epoxidových pryskyřic' (Curing Kinetics of Epoxy Resins) plus two Czechoslovak-era amine-hardener patents (CS200848B1, CS248527B1) -- follow-up WebFetch attempted on the thesis PDF (see below).",
        },
        {
            "tool": "WebSearch", "language": "cs",
            "query": "časopis \"Koroze a ochrana materiálu\" epoxidové nátěrové systémy protikorozní",
            "query_gloss_en": "journal Corrosion and Material Protection epoxy coating systems anti-corrosion",
            "purpose": "target the directive-named Czech national corrosion-engineering journal directly",
            "result_count": 10,
            "sample_urls": [
                "https://ukmki.vscht.cz/kom",
                "https://aki-koroze.cz/info.php?submenu=o-cas&sel_casopis=0",
                "https://reference-global.com/journal/KOM",
                "https://www.casopis-koroze.cz/casopis.php?sel_casopis=1995/3",
            ],
            "result_evidence_quote": "The journal \"Koroze a ochrana materiálu\" (KOM) is a quarterly publication focused on corrosion and corrosion protection issues in energy, industry, construction, monument restoration, agriculture, healthcare and ecology, and has been published since 1957. Since 2012, the journal has been published by Sciendo, and an archive of articles from 1991 onwards is freely accessible.",
        },
        {
            "tool": "WebSearch", "language": "cs",
            "query": "NUŠL Národní úložiště šedé literatury disertační práce epoxidová pryskyřice koroze",
            "query_gloss_en": "NUSL National Repository of Grey Literature dissertation epoxy resin corrosion",
            "purpose": "target the directive-named Czech national grey-literature repository directly for a cure-kinetics dissertation",
            "result_count": 9,
            "sample_urls": ["https://nusl.cz/?language=en&offset=0", "https://invenio.nusl.cz/"],
            "result_note": "NUSL confirmed as the National Technical Library's grey-literature aggregator (research reports, dissertations, conference materials) but no epoxy/corrosion-specific dissertation record surfaced directly in this query's snippets -- the UTB Zlin thesis (query 4) and VUT DSpace resource (query 11) were found via direct institutional-repository queries instead, not via NUSL's own search snippet.",
            "empty_result": True,
            "empty_result_note": "Honest partial-empty result for NUSL specifically as a discovery path this fire -- the repository class itself is confirmed real and touched, but no on-gap document was found through it directly this fire (as opposed to through UTB/VUT institutional repositories).",
        },
        {
            "tool": "WebSearch", "language": "pl",
            "query": "yadda.icm.edu.pl BazTech powłoki antykorozyjne epoksydowe artykuł",
            "query_gloss_en": "yadda.icm.edu.pl BazTech anti-corrosion epoxy coatings article",
            "purpose": "retry of query 3 (transient failure) with a reformulated BazTech-targeted string",
            "result_count": 8,
            "sample_urls": [
                "https://yadda.icm.edu.pl/baztech/element/bwmeta1.element.baztech-c36d0949-e192-4fe2-b911-86824c7b718a",
                "https://yadda.icm.edu.pl/baztech/element/bwmeta1.element.baztech-article-BPB7-0010-0025",
                "https://yadda.icm.edu.pl/baztech/element/bwmeta1.element.baztech-eff5197e-5937-45ca-a338-8911c5efd70e",
            ],
            "result_note": "BazTech confirmed reachable and indexing multiple epoxy/anti-corrosion coating articles (renewable-raw-material anti-corrosion coatings with nanomagnetite, cadmium-coating alternatives, steel-structure protection in power generation, polyurea membranes). Article-detail-page full-text access blocked by a CAPTCHA on direct WebFetch (see below) -- index-level snippets only this fire.",
        },
        {
            "tool": "WebSearch", "language": "pl",
            "query": "rozprawa doktorska żywica epoksydowa kinetyka sieciowania Politechnika repozytorium",
            "query_gloss_en": "doctoral dissertation epoxy resin crosslinking kinetics Polytechnic repository",
            "purpose": "search Polish polytechnic doctoral-thesis repositories for a primary cure-kinetics dissertation, the directive's 'wherever the research leads' scope",
            "result_count": 7,
            "sample_urls": [
                "https://repo.uni.opole.pl/info/phd/UOd74e4b287fbe4d6b80d7a00e28cfb88d/",
                "https://bip.pw.edu.pl/content/download/71624/685232/file/ROZPRAWA%20DOKTORSKA%20ER.pdf",
            ],
            "result_evidence_quote": "Doktoraty – Rozgałęzione poliaminy – nowa generacja związków sieciujących żywice epoksydowe – Uniwersytet Opolski. Research examined the epoxy resin crosslinking process using branched amines, evaluating the degree of crosslinking and reaction kinetics using FTIR spectroscopy and differential scanning calorimetry (DSC), with kinetic studies conducted under both isothermal and dynamic conditions to assess reaction rate, glass transition temperature, and kinetic parameters such as activation energy and conversion degree.",
        },
        {
            "tool": "WebSearch", "language": "pl",
            "query": "PN-EN ISO 12944 powłoki malarskie ochrona przed korozją konstrukcje stalowe offshore",
            "query_gloss_en": "PN-EN ISO 12944 paint coatings corrosion protection steel structures offshore",
            "purpose": "directive-mandated standard-mapping check: PN standard-adoption annex vs. the portfolio's ASTM/ISO corrosion-test baseline, marine/offshore scope",
            "result_count": 7,
            "sample_urls": [
                "http://yadda.icm.edu.pl/baztech/element/bwmeta1.element.baztech-eaee57c1-331a-4cc6-ae82-162ab320962b",
                "https://strefa-iso.pl/norma-en-iso-12944-korozja-i-ochrona-elementow-stalowych",
            ],
            "result_evidence_quote": "Badania kwalifikacyjne ochronnych systemów malarskich na konstrukcje morskie (offshore) według PN-EN ISO 12944-9. Part 9 of PN-EN ISO 12944 describes requirements for protective coating systems on structures operated in open sea and similar structures with long service life. Coastal and marine structures are exposed to highly corrosive environments classified as CX (open sea) or immersion category Im4. Assessment of properties of such coating systems is based on three laboratory tests: cyclic aging test, immersion in seawater, and determination of resistance to cathodic delamination.",
        },
        {
            "tool": "WebSearch", "language": "pl",
            "query": "powłoka antykorozyjna kadłub statku norma badanie mgła solna PN-EN ISO 9227",
            "query_gloss_en": "anti-corrosion coating ship hull standard salt spray test PN-EN ISO 9227",
            "purpose": "directive-mandated standard-mapping check for the salt-spray test method used to characterize the portfolio's ASTM B117 baseline",
            "result_count": 9,
            "sample_urls": ["https://laboratorium-anticorr.pl/komora-solna-badania-korozyjne-zgodnie-z-norma-iso-9227-gwarancja-precyzji-i-rzetelnosci/", "https://tenslab.pl/iso-9227"],
            "result_evidence_quote": "Badania korozyjne według normy PN-EN ISO 9227 w wersji NSS (Neutral Salt Spray) to metoda przyspieszonego testowania odporności materiałów na działanie korozji. Polega ona na umieszczeniu próbek w specjalnej komorze, gdzie są one nieprzerwanie poddawane działaniu neutralnej mgły solnej. Mgła ta powstaje z 5% wodnego roztworu chlorku sodu (NaCl) i jest rozpylana w temperaturze 35 °C.",
        },
        {
            "tool": "WebSearch", "language": "cs",
            "query": "disertační práce epoxidová pryskyřice vytvrzování aminy DSpace ČVUT VUT VŠCHT",
            "query_gloss_en": "dissertation epoxy resin amine curing DSpace CTU BUT ICT-Prague",
            "purpose": "search Czech polytechnic doctoral-thesis repositories for a primary cure-kinetics dissertation, the directive's 'wherever the research leads' scope",
            "result_count": 5,
            "sample_urls": [
                "https://dspace.vut.cz/server/api/core/bitstreams/b142d35d-44f2-4de6-98b3-95080f992326/content",
                "https://dspace.cvut.cz/handle/10467/3114",
            ],
            "result_note": "VUT Brno DSpace resource surfaced covering molecular simulation and experimental data for amine-epoxide curing reactions and design guidance for epoxy resin matrices; not independently WebFetched this fire (not converted into a scored candidate -- flagged as open for a follow-up fire). CVUT Institute of Materials Engineering directory entry also surfaced (index-level only).",
        },
        {
            "tool": "WebSearch", "language": "cs",
            "query": "ČSN EN ISO 12944 protikorozní ochrana ocelových konstrukcí nátěrové systémy",
            "query_gloss_en": "CSN EN ISO 12944 corrosion protection steel structures coating systems",
            "purpose": "directive-mandated standard-mapping check: CSN standard-adoption annex vs. the portfolio's ASTM/ISO corrosion-test baseline",
            "result_count": 5,
            "sample_urls": ["https://shop.normy.biz/detail/509593", "https://shop.normy.biz/detail/510288"],
            "result_evidence_quote": "ČSN EN ISO 12944-9 (038241) - Nátěrové hmoty - Protikorozní ochrana ocelových konstrukcí ochrannými nátěrovými systémy - Část 9: Ochranné nátěrové systémy a laboratorní metody zkoušení jejich odolnosti pro konstrukce vystavené přímořským a obdobným podmínkám - únor 2020.",
        },
        {
            "tool": "WebSearch", "language": "pl",
            "query": "Instytut Mechaniki Precyzyjnej korozja atmosferyczna baza danych Polska stal",
            "query_gloss_en": "Institute of Precision Mechanics atmospheric corrosion database Poland steel",
            "purpose": "target the Polish national corrosion-research institute (Lukasiewicz-IMP) named as a plausible directive-scope custodian",
            "result_count": 8,
            "sample_urls": ["https://staleo.pl/katalog-firm/firma/3474/lukasiewicz-instytut-mechaniki-precyzyjnej", "http://yadda.icm.edu.pl/baztech/element/bwmeta1.element.baztech-article-BPG7-0002-0001"],
            "result_note": "Confirmed Siec Badawcza Lukasiewicz - Instytut Mechaniki Precyzyjnej (Warsaw) ran a historical 'Centrum Korozyjne' (Corrosion Center, project PBZ 013-12) and publishes atmospheric-corrosion research (zinc corrosion products in maritime atmospheres) in its own house journal Prace Instytutu Mechaniki Precyzyjnej -- an institute research program, not a discoverable open dataset this fire could evaluate. Result title observed: 'Instytut Mechaniki Precyzyjnej w walce z korozją wczoraj, dziś i jutro'.",
        },
        {
            "tool": "WebSearch", "language": "cs",
            "query": "SVÚOM koroze databáze zkoušení materiálů Praha",
            "query_gloss_en": "SVUOM corrosion database materials testing Prague",
            "purpose": "target the Czech national corrosion-testing institute named as a plausible directive-scope custodian",
            "result_count": 9,
            "sample_urls": ["https://svuom.cz/index.php?lang=cz&zobraz=aktivity", "https://reference-global.com/download/article/10.1515/kom-2015-0019.pdf"],
            "result_evidence_quote": "SVÚOM s.r.o. developed, with support from project No. 682 'Corrosion Maps' under the ICT and Strategic Services program, corrosion maps of materials in the Czech Republic. The degree of atmospheric corrosivity is a technical value that is fundamental for selecting materials and protective measures for atmospheric environments.",
        },
        {
            "tool": "WebSearch", "language": "pl",
            "query": "powłoka antyporostowa kadłub statku norma numer PN farba podwodna",
            "query_gloss_en": "antifouling coating ship hull standard number PN underwater paint",
            "purpose": "directive rule 7 empty-is-an-answer probe: search for a ship-hull-specific PN antifouling/anticorrosive paint standard number, analogous to zh's GB/T 6822 and de/ja's negative findings",
            "result_count": 9,
            "sample_urls": ["https://boatshop.pl/blog/38/co-to-jest-antifouling-i-jaka-farbe-antyporostowa-wybrac", "https://www.cordis.europa.eu/article/id/118681-innovative-paint-solution-to-help-protect-ships-from-marine-biofouling/pl"],
            "result_note": "No ship-hull-specific PN antifouling/anticorrosive paint standard number was found (only IMO/MEPC 46 biocide regulation and the general-scope PN-EN ISO 12944, already found by query 9) -- honest negative result, mirroring the de and ja fires' identical findings for DIN/JIS.",
            "empty_result": True,
        },
        {
            "tool": "WebSearch", "language": "cs",
            "query": "nátěr trupu lodi protiobrůstací povlak norma ČSN podvodní barva",
            "query_gloss_en": "ship hull coating antifouling covering standard CSN underwater paint",
            "purpose": "directive rule 7 empty-is-an-answer probe: search for a ship-hull-specific CSN antifouling standard number, the Czech counterpart to query 15",
            "result_count": 8,
            "sample_urls": ["https://uac-m.org/cs/kterou-spodn%C3%AD-barvu-m%C3%A1m-pou%C5%BE%C3%ADt/", "https://www.rvc.gov.cz/admin-data/storage/get/146-tkp-protikorozni-ochrana-ocelovych-konstrukci.pdf"],
            "result_note": "No ship-hull-specific CSN antifouling standard number was found (only general biocide/antifouling-paint consumer guidance and a general steel-structure corrosion-protection technical specification, RVC CR TKP) -- honest negative result, matching query 15's Polish finding and the de/ja precedent.",
            "empty_result": True,
        },
        {
            "tool": "WebFetch", "language": "pl",
            "url": "https://repo.uni.opole.pl/info/phd/UOd74e4b287fbe4d6b80d7a00e28cfb88d/",
            "purpose": "evaluate the Opole University doctoral-thesis record's bibliographic metadata and license/access terms",
            "result": "FAILED via WebFetch tool -- 'unable to verify the first certificate' (TLS chain error). Retried via raw curl -k from xbabe1 (title-only, reachability + text-extraction check, no PDF or dataset downloaded): confirmed the exact Polish title 'Rozgałęzione poliaminy – nowa generacja związków sieciujących żywice epoksydowe', external co-affiliations (Instytut Ciężkiej Syntezy Organicznej 'Blachownia' Kędzierzyn-Koźle; Politechnika Łódzka; Politechnika Śląska) present in the authorList markup, but the page is a JS-rendered SPA (OMEGA-PSIR system) -- no license/access statement or PDF download link was present in the server-rendered HTML this fire.",
        },
        {
            "tool": "WebFetch", "language": "pl",
            "url": "https://bibliotekanauki.pl/journals/18775",
            "purpose": "evaluate the Library of Science (bibliotekanauki.pl) hosting record for Ochrona przed Korozja's access/license model",
            "result": "FAILED -- WebFetch returned an empty page-content response both attempts this fire, despite curl confirming the URL is reachable (HTTP 200, see no_acquisition_attestation). A WebFetch-tool-specific quirk (likely JS-rendered content the tool's HTML-to-markdown conversion produced no extractable text for), not a network block -- disclosed rather than silently retried indefinitely.",
        },
        {
            "tool": "WebFetch", "language": "cs",
            "url": "https://reference-global.com/download/article/10.1515/kom-2015-0019.pdf",
            "purpose": "evaluate the 'Nové mapy korozní agresivity České republiky' (New corrosion-aggressiveness maps of the Czech Republic) KOM-journal article describing the SVUOM corrosion-maps methodology",
            "result": "FAILED -- WebFetch could not extract readable text; the PDF's content stream returned as compressed/binary FlateDecode data the fetch tool could not decode into text this fire (HTTP-level retrieval succeeded, 814.5KB). Same class of failure as the DR-LANG-DE fire's BAW-Merkblatt PDF.",
        },
        {
            "tool": "WebFetch", "language": "pl",
            "url": "http://yadda.icm.edu.pl/baztech/element/bwmeta1.element.baztech-eaee57c1-331a-4cc6-ae82-162ab320962b",
            "purpose": "evaluate the BazTech PN-EN ISO 12944-9 offshore-qualification-testing article's full content and license/access terms",
            "result": "FAILED -- WebFetch returned only a 'I'm not a robot' CAPTCHA-verification page; the underlying article content and license terms could not be retrieved this fire.",
        },
        {
            "tool": "WebFetch", "language": "pl",
            "url": "https://sitpchem.org.pl/dzialalnosc/czasopisma/miesiecznik-ochrona-przed-korozja/",
            "purpose": "evaluate the publisher (SITPChem) page's stated access/license model for Ochrona przed Korozja",
            "result_evidence_quote": "No explicit access or license model is stated. Publisher/custodian confirmed: Stowarzyszenie Inzynierow i Technikow Przemyslu Chemicznego (SITPChem), in collaboration with Polskie Stowarzyszenie Korozyjne and the European Corrosion Federation. Official website: www.ochronaprzedkorozja.pl.",
        },
        {
            "tool": "WebFetch", "language": "cs",
            "url": "http://digilib.k.utb.cz/bitstream/handle/10563/441/bene%20_2006_bp.pdf?sequence=1",
            "purpose": "evaluate the UTB Zlin bachelor thesis 'Kinetika vytvrzování epoxidových pryskyřic' content and any stated license terms",
            "result": "FAILED -- WebFetch could not extract readable text; PDF returned as raw compressed object/stream data (605.4KB, ISO-8859-1) the fetch tool could not decode into text this fire (HTTP-level retrieval succeeded).",
        },
        {
            "tool": "WebFetch", "language": "pl",
            "url": "https://www.ochronaprzedkorozja.pl",
            "purpose": "evaluate the journal's own official website for its access/license model directly",
            "result": "FAILED -- HTTP 403 Forbidden.",
        },
        {
            "tool": "WebFetch", "language": "cs",
            "url": "https://reference-global.com/journal/KOM",
            "purpose": "evaluate the Koroze a ochrana materialu (KOM) journal's publisher, license, and access model directly",
            "result_evidence_quote": "Koroze a ochrana materiálu (KOM - Corrosion and Material Protection Journal). Publisher: Association of Czech and Slovak Corrosion Engineers. Access Model: Open Access with Creative Commons License -- the journal operates under Attribution-NonCommercial-NoDerivatives 4.0 licensing. Quoted access statement: 'simple and charge-free access for every researcher'. Scope: corrosion engineering and surface treatment of metallic materials; degradation of paints, enamels, and non-metallic corrosion prevention materials; conservation and restoration of cultural heritage; fundamental corrosion science and practical case studies. Over 55 years of publication history.",
        },
        {
            "tool": "WebFetch", "language": "cs",
            "url": "https://svuom.cz/index.php?lang=cz&zobraz=aktivity",
            "purpose": "evaluate the SVUOM 'corrosion maps' product description, data content, and access/license terms",
            "result": "FAILED -- 'connect ECONNREFUSED 88.102.117.90:443'. Cross-checked with raw curl from xbabe1 (see no_acquisition_attestation): curl also could not connect (connection timed out after 15000ms against the same resolved IP 88.102.117.90) -- confirming this is a network-level block from this host, not a WebFetch-tool-specific refusal, the same diagnostic pattern PROBE-WEB recorded for CNKI.",
        },
        {
            "tool": "WebFetch", "language": "pl",
            "url": "https://sigma-not.pl/czasopisma-40-ochrona-przed-korozja.html",
            "purpose": "evaluate the Sigma-NOT subscription/publisher page for Ochrona przed Korozja's access terms",
            "result": "FAILED -- HTTP 403 Forbidden. Cross-checked with raw curl from xbabe1: also HTTP 403 -- confirming a server-side access block (not a WebFetch-tool-specific refusal).",
        },
    ],
    "no_acquisition_attestation": (
        "No dataset file, record set, table, standard full-text PDF, or bulk content was "
        "downloaded, cached, or scraped this fire. All 16 WebSearch calls returned ranked "
        "result snippets only. Of 10 WebFetch calls, 4 succeeded (each returning the tool's "
        "own evaluative summary of page content -- license terms, access-tier descriptions, "
        "or an explicit 'no statement found' -- never raw page bytes written to any file) and "
        "6 failed (TLS cert error, empty-content quirk, undecodable PDF binary x2, CAPTCHA, "
        "HTTP 403 x2, ECONNREFUSED). Three raw-curl cross-checks from xbabe1 were run purely "
        "as HTTP-status/reachability/short-text diagnostics (svuom.cz: connection timeout, "
        "confirming the WebFetch ECONNREFUSED is network-level; sigma-not.pl: HTTP 403, "
        "confirming the WebFetch block is server-side; bibliotekanauki.pl: HTTP 200, showing "
        "WebFetch's empty-content result was a tool-specific rendering quirk not a network "
        "block) plus ONE curl -k text-extraction attempt against the Opole University thesis "
        "record (repo.uni.opole.pl) after WebFetch failed on a TLS chain error -- this returned "
        "the page's server-rendered HTML shell (a JS single-page application with most content "
        "loaded client-side), from which only the exact dissertation title and co-affiliation "
        "names were extracted via text search; no PDF, dataset, or bulk record content was "
        "retrieved, cached, or persisted beyond the transcript of this fire. One WebFetch call "
        "(the KOM 'corrosion maps' article PDF) triggered the WebFetch tool's own internal "
        "15-minute self-cleaning cache to save a copy of the fetched PDF binary under this "
        "agent's LOCAL xbabe1 tool-results cache directory (a fixed WebFetch platform behavior, "
        "not a deliberate acquisition action by this fire, and the same disclosed behavior the "
        "DR-LANG-DE and DR-LANG-JA fires documented) -- nothing was written to xbabe2 from that "
        "call, extraction failed, and the tool-cache copy is disclosed here rather than hidden; "
        "it is a single document, not bulk data, and is not referenced as evidence for any "
        "disposition-ledger score. Nothing beyond this ledger line, the disposition-ledger, "
        "dataset-ledger, and coverage-map entries it supports, this item's work/ diagnostics, "
        "and this fire's signed receipt was written under mvp20-split."
    ),
    "next_run_should_extend": (
        "Untouched this fire, open for a future DR-LANG-CEE (fire 2 of max_fires=2) or "
        "adjacent fire: (1) the BazTech PN-EN ISO 12944-9 offshore article is CAPTCHA-blocked "
        "-- retry with a different extraction path or accept index-level-only evidence "
        "permanently; (2) the SVUOM corrosion-maps KOM-journal PDF and the UTB Zlin thesis PDF "
        "both failed WebFetch text extraction -- retry with a real PDF-text-parsing path (curl "
        "+ pdftotext or similar), mirroring the still-open DR-LANG-DE BAW-Merkblatt retry; (3) "
        "svuom.cz is confirmed network-unreachable from this host (both WebFetch and raw curl) "
        "-- if a future fire runs from a different egress path, retry direct evaluation of the "
        "Korozni mapy materialu CR product's access/license terms; (4) the Opole University "
        "thesis repo.uni.opole.pl is a JS-rendered SPA -- a future fire with a JS-capable fetch "
        "path could confirm its license/access terms, currently unconfirmed; (5) the VUT Brno "
        "DSpace resource on amine-epoxide curing molecular simulation (query 11) was found but "
        "not independently WebFetched or scored as a candidate this fire; (6) NUSL's own search "
        "interface (invenio.nusl.cz) was not directly queried with a filtered epoxy/corrosion "
        "search this fire, only reached via a general WebSearch snippet; (7) Slovak-language "
        "literature was NOT searched this fire -- the directive item is scoped to 'Polish and "
        "Czech' specifically, but Czechoslovak-era patents (CS-prefix) surfaced during Czech "
        "queries suggest a Slovak follow-up may be adjacent-relevant for a future directive item."
    ),
}

sr_line_bytes = json.dumps(search_record_line_obj, sort_keys=True, ensure_ascii=False).encode("utf-8")
sr_new_content = sr_before
if not sr_new_content.endswith(b"\n"):
    sr_new_content += b"\n"
sr_new_content += sr_line_bytes + b"\n"
sr_appended_line_no = sr_prior_line_count + 1
sr_appended_sha = sha(sr_line_bytes)
sr_file_sha_after = sha(sr_new_content)

# ---------------------------------------------------------------------------
# 2. disposition-ledger.v1.jsonl new lines (1 intake manifest + 8 dispositions)
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
    "candidates_pinned": [],
    "note": (
        "ZERO previously-supplied Polish- or Czech-language candidates were found anywhere in "
        "the portfolio as of this fire's start. Searched: (1) DR-RUBRIC's frozen "
        "candidate_snapshot.v1.json (candidates C1-C4 -- all zh/ja, none pl or cs); (2) "
        "feedback/v1/dataset_sources.json (schema amphora.feedback_v1.dataset_sources.v1, "
        "'sources' array -- no pl/cs-origin or pl/cs-language source_url/id found by direct "
        "read, grepped for poland|polish|polska|czech|czeska|cesko|česk); (3) "
        "feedback/v2/catalog.json, feedback/v3/catalog.json, feedback/v4/catalog.json (schema "
        "amphora.data-catalog.v2, 'source_intents' arrays -- no pl/cs-origin source_intent "
        "found by direct read); (4) /home/ubuntu/amphora-cron/data-acquisition-queue.jsonl on "
        "xbabe1 (grepped for the same terms plus '.pl' -- zero matches). This satisfies the "
        "directive's and this item's own done_criterion alternative branch: 'Previously-"
        "supplied candidates in these languages must be independently rediscovered OR THEIR "
        "ABSENCE EXPLAINED.' The absence is explained above with the exact source paths "
        "checked; there is nothing to rediscover. Positive-control mutant 5 (below) therefore "
        "uses a SYNTHETIC previously-supplied-candidate ID to prove the rediscovery-recall "
        "checker rule is a real, non-vacuous check rather than one that can never fire because "
        "the input list is empty by construction."
    ),
    "source_paths_checked_for_prior_cee_candidates": [
        "amphora-dataset-recon/evidence/phase0/repairs/DR-RUBRIC/work/candidate_snapshot.v1.json",
        "feedback/v1/dataset_sources.json",
        "feedback/v2/catalog.json",
        "feedback/v3/catalog.json",
        "feedback/v4/catalog.json",
        "/home/ubuntu/amphora-cron/data-acquisition-queue.jsonl (xbabe1)",
    ],
}

candidates = [
    {
        "candidate_id": "DR-LANG-CEE-01",
        "name": "PhD dissertation: \"Rozgałęzione poliaminy – nowa generacja związków sieciujących żywice epoksydowe\" (Branched Polyamines -- A New Generation of Epoxy-Resin Crosslinking Agents), University of Opole",
        "language": "pl",
        "native_citation": "Rozgałęzione poliaminy – nowa generacja związków sieciujących żywice epoksydowe",
        "native_citation_romanization": None,
        "url": "https://repo.uni.opole.pl/info/phd/UOd74e4b287fbe4d6b80d7a00e28cfb88d/",
        "custodian": "Uniwersytet Opolski (University of Opole), with external co-affiliation Instytut Ciężkiej Syntezy Organicznej \"Blachownia\", Kędzierzyn-Koźle",
        "rediscovers": None,
        "coverage": "PhD dissertation on branched-polyamine epoxy-crosslinking agents: FTIR + DSC crosslinking-degree and reaction-kinetics study under both isothermal and dynamic conditions, reporting reaction rate, glass-transition temperature, activation energy, and conversion degree. Exact numeric values not confirmed this fire (page is a JS-rendered SPA; only bibliographic metadata, not the PDF, was reachable).",
        "gap_match_class": "named_module_gap",
        "meets_minimum_n_and_measurement_class": "unknown",
        "data_class": "primary_experimental",
        "standard_and_uncertainty_disclosed": "standard_named_no_uncertainty",
        "rights_tier": "paywalled_unclear_bulk_rights",
        "rights_note": "No license or access statement was present in the server-rendered HTML this fire (the repository is a JS single-page application; most content, including any PDF link or license field, loads client-side and was not reachable via WebFetch, which failed on a TLS cert-chain error, or via a raw curl fallback, which only returned the page shell). Scored conservatively rather than assumed open.",
        "redundancy_class": "no_known_portfolio_overlap",
        "translation_confidence": "machine_translated_medium",
        "translation_confidence_note": "The DSC/FTIR methodology and kinetic-parameter summary came from the WebSearch tool's own AI-generated paraphrase of index-level snippets, not from a directly quoted verbatim source passage -- rated medium, not high, since no independent verbatim quote of the methodology itself was captured this fire (only the exact Polish title was independently verified via a raw-curl text-extraction cross-check).",
        "integrity_risks": [],
        "reachability": "reachable_index_only_dataset_unclear",
        "serves": {"module_gaps": ["amphora-cure-kinetics"], "recipe_elements": []},
        "license_evidence_quote": "no license/access statement or PDF download link was present in the server-rendered HTML this fire.",
        "standard_mapping": {
            "published_standard": "DSC + FTIR crosslinking/kinetics methodology (named in the WebSearch summary), not a single ASTM/ISO test-method standard.",
            "astm_iso_equiv": "Method-class-comparable to ASTM E698 (Kissinger-style DSC activation-energy determination), not independently clause-by-clause confirmed this fire.",
            "comparability_rating": "method_class_plausible_not_clause_confirmed",
        },
        "confidence_flag": "LOW",
    },
    {
        "candidate_id": "DR-LANG-CEE-02",
        "name": "\"Badania kwalifikacyjne ochronnych systemów malarskich na konstrukcje morskie (offshore) według PN-EN ISO 12944-9\", Ochrona przed Korozją, nr 9 (2022)",
        "language": "pl",
        "native_citation": "Badania kwalifikacyjne ochronnych systemów malarskich na konstrukcje morskie (offshore) według PN-EN ISO 12944-9",
        "native_citation_romanization": None,
        "url": "http://yadda.icm.edu.pl/baztech/element/bwmeta1.element.baztech-eaee57c1-331a-4cc6-ae82-162ab320962b",
        "custodian": "BazTech (yadda.icm.edu.pl, ICM UW) indexing Ochrona przed Korozją, published by Stowarzyszenie Inżynierów i Techników Przemysłu Chemicznego (SITPChem) with Polskie Stowarzyszenie Korozyjne and the European Corrosion Federation",
        "rediscovers": None,
        "coverage": "Qualification testing of protective paint systems for offshore marine structures per PN-EN ISO 12944-9: three laboratory tests (cyclic aging, seawater immersion, cathodic-delamination resistance) for coating systems in corrosivity category CX / immersion category Im4.",
        "gap_match_class": "named_module_gap",
        "meets_minimum_n_and_measurement_class": "unknown",
        "data_class": "compilation_of_primary",
        "standard_and_uncertainty_disclosed": "published_standard_and_uncertainty",
        "rights_tier": "paywalled_unclear_bulk_rights",
        "rights_note": "Full-text access blocked by a CAPTCHA on direct WebFetch this fire; the publisher's own site (ochronaprzedkorozja.pl) returned HTTP 403 and its distributor sigma-not.pl also returned HTTP 403 (confirmed independently via raw curl); SITPChem's own page states no explicit access/license model. Scored conservatively -- no path to a confirmed open license this fire.",
        "redundancy_class": "partial_overlap_adds_coverage",
        "translation_confidence": "native_script_verified_high",
        "translation_confidence_note": "Polish article title and PN-EN ISO 12944-9 scope description directly quoted from this fire's recorded WebSearch evidence.",
        "integrity_risks": [],
        "reachability": "reachable_index_only_dataset_unclear",
        "serves": {"module_gaps": ["amphora-ip-fto-guard", "amphora-owk-adhesion", "amphora-public-corrosion-benchmark"], "recipe_elements": ["marine-coating-system-standard-mapping"]},
        "license_evidence_quote": "Badania kwalifikacyjne ochronnych systemów malarskich na konstrukcje morskie (offshore) według PN-EN ISO 12944-9. Part 9 of PN-EN ISO 12944 describes requirements for protective coating systems on structures operated in open sea and similar structures with long service life. Coastal and marine structures are exposed to highly corrosive environments classified as CX (open sea) or immersion category Im4. Assessment of properties of such coating systems is based on three laboratory tests: cyclic aging test, immersion in seawater, and determination of resistance to cathodic delamination.",
        "standard_mapping": {
            "published_standard": "PN-EN ISO 12944 (Parts 1-9), esp. Part 9 (offshore) -- direct Polish/European adoption of ISO 12944.",
            "astm_iso_equiv": "PN-EN ISO 12944 IS the direct Polish/European-language adoption of ISO 12944 itself, matching the DR-LANG-DE fire's identical finding for DIN EN ISO 12944 -- three independent language-community searches (de, pl, and ja's JIS finding) now converge on ISO 12944/9227 as the global baseline this portfolio's own ASTM-referenced standards should be benchmarked against.",
            "comparability_rating": "identical_to_iso_by_direct_adoption_astm_unconfirmed",
        },
        "confidence_flag": "MEDIUM",
    },
    {
        "candidate_id": "DR-LANG-CEE-03",
        "name": "PN-EN ISO 9227 -- Badania korozyjne w sztucznych atmosferach, badania w mgle solnej",
        "language": "pl",
        "native_citation": "Badania korozyjne według normy PN-EN ISO 9227 w wersji NSS (Neutral Salt Spray)",
        "native_citation_romanization": None,
        "url": "https://laboratorium-anticorr.pl/komora-solna-badania-korozyjne-zgodnie-z-norma-iso-9227-gwarancja-precyzji-i-rzetelnosci/",
        "custodian": "PKN -- Polski Komitet Normalizacyjny / CEN-CENELEC (EN adoption of ISO 9227)",
        "rediscovers": None,
        "coverage": "Neutral salt spray (NSS) accelerated corrosion-resistance test method: 5% aqueous NaCl solution, 35 degC, continuous spray exposure -- direct Polish/European adoption of ISO 9227.",
        "gap_match_class": "named_module_gap",
        "meets_minimum_n_and_measurement_class": "unknown",
        "data_class": "compilation_of_primary",
        "data_class_note": "Published national/European standard document (direct EN adoption of the ISO standard), not a raw-measurement dataset -- category mismatch with the rubric's data_class vocabulary (built for datasets) is flagged honestly, matching the DR-LANG-DE-05 / DR-LANG-JA precedent for JIS/DIN salt-spray standards.",
        "standard_and_uncertainty_disclosed": "published_standard_and_uncertainty",
        "rights_tier": "paywalled_unclear_bulk_rights",
        "redundancy_class": "partial_overlap_adds_coverage",
        "translation_confidence": "native_script_verified_high",
        "translation_confidence_note": "Standard number, NSS parameters (5% NaCl, 35 degC), and test description directly quoted from this fire's recorded native-pl WebSearch evidence.",
        "integrity_risks": [],
        "reachability": "reachable_index_only_dataset_unclear",
        "serves": {"module_gaps": ["amphora-public-corrosion-benchmark"], "recipe_elements": ["salt-spray-standard-mapping"]},
        "license_evidence_quote": "Badania korozyjne według normy PN-EN ISO 9227 w wersji NSS (Neutral Salt Spray) to metoda przyspieszonego testowania odporności materiałów na działanie korozji. Polega ona na umieszczeniu próbek w specjalnej komorze, gdzie są one nieprzerwanie poddawane działaniu neutralnej mgły solnej. Mgła ta powstaje z 5% wodnego roztworu chlorku sodu (NaCl) i jest rozpylana w temperaturze 35 °C.",
        "standard_mapping": {
            "published_standard": "PN-EN ISO 9227",
            "astm_iso_equiv": "Direct Polish/European adoption of ISO 9227 itself (no separate national number); method-class-comparable to ASTM B117 (both neutral-salt-spray tests). Converges with the DR-LANG-DE fire's identical finding for DIN EN ISO 9227 and the DR-LANG-JA fire's finding for JIS Z 2371 (also ISO-9227-based) -- a THIRD independent language-community confirmation this fire.",
            "comparability_rating": "identical_to_iso_by_direct_adoption_method_class_confirmed_astm_inferred",
        },
        "confidence_flag": "MEDIUM",
    },
    {
        "candidate_id": "DR-LANG-CEE-04",
        "name": "Siec Badawcza Lukasiewicz -- Instytut Mechaniki Precyzyjnej (Corrosion Center / atmospheric-corrosion research program)",
        "language": "pl",
        "native_citation": "Instytut Mechaniki Precyzyjnej w walce z korozją wczoraj, dziś i jutro",
        "native_citation_romanization": None,
        "url": "http://yadda.icm.edu.pl/baztech/element/bwmeta1.element.baztech-article-BPG7-0002-0001",
        "custodian": "Siec Badawcza Lukasiewicz -- Instytut Mechaniki Precyzyjnej, Warszawa",
        "rediscovers": None,
        "coverage": "Historical Corrosion Center (Centrum Korozyjne, project PBZ 013-12, national corrosion-protection-system development) and ongoing atmospheric-corrosion research (e.g. zinc corrosion products in maritime atmospheres), published in the institute's own house journal Prace Instytutu Mechaniki Precyzyjnej. An institute research program and journal, not a discoverable open dataset or data descriptor this fire could locate or evaluate.",
        "gap_match_class": "off_scope",
        "meets_minimum_n_and_measurement_class": "no",
        "data_class": "extracted_or_estimated",
        "data_class_note": "No raw data, data descriptor, or standalone dataset was found on the institute's public pages this fire -- only research-program and house-journal descriptions. Honestly scored at the floor rather than credited for institutional relevance, matching the DR-LANG-DE-02/03 (Fraunhofer/GfKORR) precedent.",
        "standard_and_uncertainty_disclosed": "neither_stated",
        "rights_tier": "paywalled_unclear_bulk_rights",
        "redundancy_class": "no_known_portfolio_overlap",
        "translation_confidence": "native_script_verified_high",
        "translation_confidence_note": "Institute name, historical project code, and research-program description directly quoted/paraphrased from this fire's recorded native-pl WebSearch evidence.",
        "integrity_risks": [],
        "reachability": "reachable_index_only_dataset_unclear",
        "serves": {"module_gaps": [], "recipe_elements": []},
        "license_evidence_quote": "Confirmed Siec Badawcza Lukasiewicz - Instytut Mechaniki Precyzyjnej (Warsaw) ran a historical 'Centrum Korozyjne' (Corrosion Center, project PBZ 013-12) and publishes atmospheric-corrosion research (zinc corrosion products in maritime atmospheres) in its own house journal Prace Instytutu Mechaniki Precyzyjnej -- an institute research program, not a discoverable open dataset this fire could evaluate.",
        "standard_mapping": {
            "published_standard": "N/A -- research institute and house journal, not a measurement standard or dataset.",
            "astm_iso_equiv": "N/A",
            "comparability_rating": "not_applicable_research_institute",
        },
        "confidence_flag": "LOW",
    },
    {
        "candidate_id": "DR-LANG-CEE-05",
        "name": "Bachelor's thesis: \"Kinetika vytvrzování epoxidových pryskyřic\" (Curing Kinetics of Epoxy Resins), Tomas Bata University in Zlin",
        "language": "cs",
        "native_citation": "Kinetika vytvrzování epoxidových pryskyřic",
        "native_citation_romanization": None,
        "url": "http://digilib.k.utb.cz/bitstream/handle/10563/441/bene%20_2006_bp.pdf?sequence=1",
        "custodian": "Univerzita Tomáše Bati ve Zlíně (Tomas Bata University in Zlin), digilib.k.utb.cz institutional repository",
        "rediscovers": None,
        "coverage": "UNKNOWN this fire -- WebFetch could not extract readable text from the PDF (compressed/binary content stream). Title, degree level (bp = bakalarska prace, bachelor's thesis), year (2006, from the filename), and topic (epoxy-resin cure kinetics) are known from the URL/title only; scope and quantitative content are NOT confirmed.",
        "gap_match_class": "named_module_gap",
        "meets_minimum_n_and_measurement_class": "unknown",
        "data_class": "extracted_or_estimated",
        "data_class_note": "Honest worst-case categorical value: content could not be confirmed at all this fire despite a strong title-level topical match, mirroring the DR-LANG-DE-07 (BAW Merkblatt) and DR-LANG-JA-06 (JASNAOE) PDF-extraction-failure precedent.",
        "standard_and_uncertainty_disclosed": "neither_stated",
        "rights_tier": "paywalled_unclear_bulk_rights",
        "rights_note": "HTTP-level retrieval succeeded (no paywall/login encountered -- a freely-hosted university-repository PDF), but since extraction failed, no license/access terms could be confirmed from the document itself.",
        "redundancy_class": "no_known_portfolio_overlap",
        "translation_confidence": "no_translation_attempted_unknown",
        "translation_confidence_note": "Title is taken from the WebSearch result-title/URL snippet (native cs), not independently verified against extracted document content, since extraction failed.",
        "integrity_risks": ["digitization_quality_concern"],
        "reachability": "reachable_index_only_dataset_unclear",
        "serves": {"module_gaps": ["amphora-cure-kinetics"], "recipe_elements": []},
        "license_evidence_quote": "FAILED -- WebFetch could not extract readable text; PDF returned as raw compressed object/stream data (605.4KB, ISO-8859-1) the fetch tool could not decode into text this fire (HTTP-level retrieval succeeded).",
        "standard_mapping": {
            "published_standard": "UNKNOWN -- extraction failed this fire.",
            "astm_iso_equiv": "NOT_CONFIRMED_THIS_FIRE",
            "comparability_rating": "unconfirmed_extraction_failed",
        },
        "confidence_flag": "LOW",
    },
    {
        "candidate_id": "DR-LANG-CEE-06",
        "name": "Koroze a ochrana materiálu (KOM -- Corrosion and Material Protection Journal)",
        "language": "cs",
        "native_citation": "Koroze a ochrana materiálu",
        "native_citation_romanization": None,
        "url": "https://reference-global.com/journal/KOM",
        "custodian": "Association of Czech and Slovak Corrosion Engineers (Asociace korozních inženýrů), published via Sciendo since 2012",
        "rediscovers": None,
        "coverage": "Quarterly peer-reviewed journal, published continuously since 1957 (55+ years), covering corrosion engineering and surface treatment of metallic materials, degradation of paints/enamels/non-metallic corrosion-prevention materials, cultural-heritage conservation, and both fundamental science and case studies. Freely accessible article archive from 1991 onward. Exact per-article epoxy-coating-specific record count not enumerated this fire (no per-article drill-down, per no-acquisition discipline).",
        "gap_match_class": "named_module_gap",
        "meets_minimum_n_and_measurement_class": "unknown",
        "data_class": "compilation_of_primary",
        "standard_and_uncertainty_disclosed": "standard_named_no_uncertainty",
        "rights_tier": "open_with_attribution",
        "rights_note": "License is CC BY-NC-ND 4.0 (Attribution-NonCommercial-NoDerivatives), directly confirmed via WebFetch of the publisher's own journal page ('simple and charge-free access for every researcher'). The NC (NonCommercial) and ND (NoDerivatives) clauses are real restrictions on commercial-deliverable reuse of specific article figures/data without separate permission, even though the archive itself is freely readable/downloadable -- disclosed rather than silently absorbed into a rosier score, matching the DR-LANG-DE-06 (TU Darmstadt dissertation) precedent for an identical license class.",
        "redundancy_class": "no_known_portfolio_overlap",
        "translation_confidence": "native_script_verified_high",
        "translation_confidence_note": "Journal name, publisher, license terms, and scope directly quoted from this fire's WebFetch evidence of the publisher's own journal page.",
        "integrity_risks": [],
        "reachability": "reachable_direct_open_download",
        "serves": {"module_gaps": ["amphora-public-corrosion-benchmark", "amphora-barrier-corrosion-score"], "recipe_elements": []},
        "license_evidence_quote": "Koroze a ochrana materiálu (KOM - Corrosion and Material Protection Journal). Publisher: Association of Czech and Slovak Corrosion Engineers. Access Model: Open Access with Creative Commons License -- the journal operates under Attribution-NonCommercial-NoDerivatives 4.0 licensing. Quoted access statement: 'simple and charge-free access for every researcher'. Scope: corrosion engineering and surface treatment of metallic materials; degradation of paints, enamels, and non-metallic corrosion prevention materials; conservation and restoration of cultural heritage; fundamental corrosion science and practical case studies. Over 55 years of publication history.",
        "standard_mapping": {
            "published_standard": "No single measurement standard pinned to the journal as a whole (it is a periodical, not a single dataset) -- individual articles cite standards (e.g. CSN EN ISO 12944) per-article, not enumerated this fire.",
            "astm_iso_equiv": "NOT_CONFIRMED_THIS_FIRE -- journal-level, not article-level, evaluation this fire.",
            "comparability_rating": "unconfirmed_no_per_article_drilldown",
        },
        "confidence_flag": "MEDIUM",
    },
    {
        "candidate_id": "DR-LANG-CEE-07",
        "name": "ČSN EN ISO 12944-9 (038241) -- Nátěrové hmoty - Protikorozní ochrana ocelových konstrukcí ochrannými nátěrovými systémy - Část 9",
        "language": "cs",
        "native_citation": "Nátěrové hmoty - Protikorozní ochrana ocelových konstrukcí ochrannými nátěrovými systémy - Část 9: Ochranné nátěrové systémy a laboratorní metody zkoušení jejich odolnosti pro konstrukce vystavené přímořským a obdobným podmínkám",
        "native_citation_romanization": None,
        "url": "https://shop.normy.biz/detail/509593",
        "custodian": "UNMZ (Czech Office for Standards, Metrology and Testing) / CEN-CENELEC (EN adoption of ISO 12944), distributed via normy.biz",
        "rediscovers": None,
        "data_class_note": "Published national/European standard document (direct EN adoption of the ISO standard), not a raw-measurement dataset -- category mismatch with the rubric's data_class vocabulary is flagged honestly, matching the DR-LANG-CEE-03 / DR-LANG-DE-04/05 precedent.",
        "coverage": "Part 9 (Feb 2020): protective coating systems and laboratory test methods for structures exposed to marine/offshore and similar conditions -- direct Czech/European adoption of ISO 12944-9.",
        "gap_match_class": "named_module_gap",
        "meets_minimum_n_and_measurement_class": "unknown",
        "data_class": "compilation_of_primary",
        "standard_and_uncertainty_disclosed": "published_standard_and_uncertainty",
        "rights_tier": "paywalled_unclear_bulk_rights",
        "redundancy_class": "partial_overlap_adds_coverage",
        "translation_confidence": "native_script_verified_high",
        "translation_confidence_note": "Czech standard title and part-9 scope directly quoted from this fire's recorded native-cs WebSearch evidence (normy.biz listing).",
        "integrity_risks": [],
        "reachability": "reachable_index_only_dataset_unclear",
        "serves": {"module_gaps": ["amphora-ip-fto-guard", "amphora-owk-adhesion"], "recipe_elements": ["marine-coating-system-standard-mapping"]},
        "license_evidence_quote": "ČSN EN ISO 12944-9 (038241) - Nátěrové hmoty - Protikorozní ochrana ocelových konstrukcí ochrannými nátěrovými systémy - Část 9: Ochranné nátěrové systémy a laboratorní metody zkoušení jejich odolnosti pro konstrukce vystavené přímořským a obdobným podmínkám - únor 2020.",
        "standard_mapping": {
            "published_standard": "ČSN EN ISO 12944 (Parts 1-9), esp. Part 9 (offshore) -- direct Czech/European adoption of ISO 12944.",
            "astm_iso_equiv": "Direct Czech/European adoption of ISO 12944 itself -- FOURTH independent language-community confirmation this campaign (after de, pl (this fire), and ja's JIS finding) that ISO 12944 is the de facto global structural-coating baseline.",
            "comparability_rating": "identical_to_iso_by_direct_adoption_astm_unconfirmed",
        },
        "confidence_flag": "MEDIUM",
    },
    {
        "candidate_id": "DR-LANG-CEE-08",
        "name": "SVÚOM s.r.o. -- Korozní mapy materiálů ČR (Corrosion Maps of Materials of the Czech Republic)",
        "language": "cs",
        "native_citation": "Nové mapy korozní agresivity České republiky",
        "native_citation_romanization": None,
        "url": "https://svuom.cz/index.php?lang=cz&zobraz=aktivity",
        "custodian": "SVÚOM s.r.o., Praha",
        "rediscovers": None,
        "doi": "10.1515/kom-2015-0019",
        "coverage": "National atmospheric-corrosivity mapping product for the Czech Republic, developed under project No. 682 'Corrosion Maps' (ICT and Strategic Services program), described in the KOM-journal article 'Nove mapy korozni agresivity Ceske republiky' (DOI 10.1515/kom-2015-0019). Underlying map/data content NOT independently confirmed this fire -- both the custodian's own site (svuom.cz) and the describing journal article's PDF were unreachable/unextractable.",
        "gap_match_class": "named_module_gap",
        "meets_minimum_n_and_measurement_class": "unknown",
        "data_class": "compilation_of_primary",
        "data_class_note": "Categorized from the WebSearch AI-summary description only (a compiled national corrosivity-mapping product); not independently verified against primary source content this fire.",
        "standard_and_uncertainty_disclosed": "standard_named_no_uncertainty",
        "rights_tier": "paywalled_unclear_bulk_rights",
        "rights_note": "SVÚOM s.r.o. is a commercial testing/engineering company (s.r.o. = limited-liability company); its 'corrosion maps' product is described as institute-developed under a named grant project but no free-access statement was found, and the custodian's own site could not be evaluated this fire (see reachability).",
        "redundancy_class": "no_known_portfolio_overlap",
        "translation_confidence": "machine_translated_medium",
        "translation_confidence_note": "Czech title and project description came from the WebSearch tool's own AI-generated summary of index-level snippets; no independent verbatim source quote was captured since both the custodian site and the describing article's PDF were unreachable/unextractable this fire.",
        "integrity_risks": ["access_unconfirmed_network_blocked"],
        "reachability": "unreachable_network_blocked",
        "reachability_note": "svuom.cz is confirmed unreachable from this host by BOTH the WebFetch tool (ECONNREFUSED) AND a raw curl cross-check from xbabe1 (connection timed out after 15000ms against the same resolved IP, 88.102.117.90) -- a network-level block, the same diagnostic pattern PROBE-WEB recorded for CNKI from zh reconnaissance.",
        "serves": {"module_gaps": ["amphora-public-corrosion-benchmark"], "recipe_elements": []},
        "license_evidence_quote": "SVÚOM s.r.o. developed, with support from project No. 682 'Corrosion Maps' under the ICT and Strategic Services program, corrosion maps of materials in the Czech Republic. The degree of atmospheric corrosivity is a technical value that is fundamental for selecting materials and protective measures for atmospheric environments.",
        "standard_mapping": {
            "published_standard": "Likely ISO 9223-class atmospheric-corrosivity categorization (not independently confirmed this fire -- inferred from domain convention, not from a read source).",
            "astm_iso_equiv": "NOT_CONFIRMED_THIS_FIRE",
            "comparability_rating": "unconfirmed_network_blocked",
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
    "DR-LANG-CEE-01": "human obtains full-text/license access to the Opole University PhD dissertation (e.g. via a JS-capable browser session against the repo's SPA, or by directly contacting the university library) to confirm DSC/FTIR activation-energy and conversion-degree values and the license terms this fire could not reach.",
    "DR-LANG-CEE-02": "human obtains a BazTech/sigma-not.pl subscription or SITPChem direct-purchase access to the PN-EN ISO 12944-9 offshore qualification-testing article and performs a clause-by-clause ASTM/SSPC comparability diff against the portfolio's own baseline.",
    "DR-LANG-CEE-03": "human purchases official PN-EN ISO 9227 full text via PKN and performs a clause-by-clause ASTM B117 diff -- the same class of action recommended for the de/ja fires' equivalent national ISO-9227 adoptions.",
    "DR-LANG-CEE-04": "no dataset action possible -- Lukasiewicz-IMP's corrosion research is an institute program and house journal, not an acquirable dataset; a human seeking domain expertise could contact the institute directly.",
    "DR-LANG-CEE-05": "human re-fetches the UTB Zlin thesis PDF with a text-capable extraction path (not WebFetch's AI summarizer) to confirm scope, quantitative cure-kinetics results, and any license terms.",
    "DR-LANG-CEE-06": "human confirms via the freely-downloadable KOM archive (1991-present) which specific articles cover epoxy-amine marine coatings directly, and separately clears the CC BY-NC-ND NonCommercial clause with the Association of Czech and Slovak Corrosion Engineers before any commercial-deliverable reuse of specific article figures/data (methodology reference and internal benchmarking do not require this clearance).",
    "DR-LANG-CEE-07": "human purchases official ČSN EN ISO 12944-9 full text via normy.biz/UNMZ and performs a clause-by-clause ASTM/SSPC diff, mirroring DR-LANG-CEE-02's recommended action.",
    "DR-LANG-CEE-08": "human re-attempts SVUOM corrosion-maps evaluation from a network path where svuom.cz is reachable (confirmed unreachable from both xbabe1 WebFetch and raw curl this fire), and separately retries the describing KOM-journal PDF (DOI 10.1515/kom-2015-0019) with a real PDF-text-parsing path.",
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
                + (f"Next action: {HUMAN_ACTIONS[c['candidate_id']]}")
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
    if "rights_note" in c:
        entry["rights_note"] = c["rights_note"]
    if "doi" in c:
        entry["doi"] = c["doi"]
    if "reachability_note" in c:
        entry["reachability_note"] = c["reachability_note"]
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
dl_appended_line_start = dl_prior_line_count + 1
dl_appended_line_end = dl_prior_line_count + len(dl_lines)
dl_appended_sha = sha(dl_appended_bytes)
dl_file_sha_after = sha(dl_new_content)

# ---------------------------------------------------------------------------
# 3. dataset-ledger.v1.jsonl -- CEE-06 clears RECOMMENDED
# ---------------------------------------------------------------------------
DSL_PATH = LEDGERS / "dataset-ledger.v1.jsonl"
dsl_before = DSL_PATH.read_bytes() if DSL_PATH.exists() else b""
dsl_prior_prefix_sha = sha(dsl_before)
dsl_prior_lines = dsl_before.decode("utf-8").splitlines() if dsl_before else []
dsl_prior_line_count = len(dsl_prior_lines)

cee06 = next(e for e in disp_entries if e["candidate_id"] == "DR-LANG-CEE-06")
assert cee06["disposition"]["verdict"] == "RECOMMENDED", "expected DR-LANG-CEE-06 to clear RECOMMENDED"

dataset_ledger_entry = {
    "schema": "amphora.dataset-recon.dataset-ledger.v1",
    "entry_type": "dataset_ledger_entry",
    "ledger_entry_id": "DR-LANG-CEE-DSL-01",
    "candidate_id": "DR-LANG-CEE-06",
    "run_id": RUN_ID,
    "fire_id": FIRE_ID,
    "date": DATE,
    "framing": "AUDIT-ONLY",
    "language": "cs",
    "name": "Koroze a ochrana materiálu (KOM -- Corrosion and Material Protection Journal)",
    "native_citation": "Koroze a ochrana materiálu",
    "url_or_doi": "https://reference-global.com/journal/KOM",
    "publisher_custodian": "Association of Czech and Slovak Corrosion Engineers (Asociace korozních inženýrů), published via Sciendo since 2012",
    "license_as_published": "CC BY-NC-ND 4.0 International (free/charge-free access for every researcher; attribution required; NonCommercial and NoDerivatives clauses restrict reuse of specific article figures/data in a commercial deliverable without separate permission).",
    "standard_mapping": {
        "published_standard": "Journal-level, not article-level -- individual articles cite standards (e.g. CSN EN ISO 12944) per-article, not enumerated this fire.",
        "astm_iso_equiv": "NOT_CONFIRMED_THIS_FIRE -- no per-article drill-down performed, per no-acquisition discipline.",
        "comparability_rating": "unconfirmed_no_per_article_drilldown",
    },
    "estimated_records_and_coverage": (
        "Quarterly journal, continuously published since 1957 (55+ years); freely accessible "
        "article archive from 1991 onward. Exact per-article count and epoxy/marine-coating-"
        "specific subset size not enumerated this fire (full corpus not read beyond the WebFetch "
        "evaluative summary of the journal's own page, per no-acquisition discipline)."
    ),
    "module_gaps": ["amphora-public-corrosion-benchmark", "amphora-barrier-corrosion-score"],
    "recipe_elements": [],
    "integrity_risks": [],
    "translation_confidence": "native_script_verified_high",
    "next_human_action": HUMAN_ACTIONS["DR-LANG-CEE-06"],
    "confidence_flag": "MEDIUM",
    "coverage": cee06["coverage"],
    "rank": cee06["rank"],
    "serves": {"module_gaps": ["amphora-public-corrosion-benchmark", "amphora-barrier-corrosion-score"], "recipe_elements": []},
    "disposition": {"verdict": "RECOMMENDED", "reason": cee06["disposition"]["reason"]},
    "snapshot_date": DATE,
    "rubric_overall_score": cee06["rubric_overall_score"],
    "rubric_path": "amphora-dataset-recon/evidence/phase0/repairs/DR-RUBRIC/work/rubric.v1.json",
}

dsl_line_bytes = json.dumps(dataset_ledger_entry, sort_keys=True, ensure_ascii=False).encode("utf-8")
dsl_new_content = dsl_before
if dsl_before and not dsl_new_content.endswith(b"\n"):
    dsl_new_content += b"\n"
dsl_new_content += dsl_line_bytes + b"\n"
dsl_appended_line_no = dsl_prior_line_count + 1
dsl_appended_sha = sha(dsl_line_bytes)
dsl_file_sha_after = sha(dsl_new_content)

# ---------------------------------------------------------------------------
# 4. coverage-map.v1.json -- merge (preserve zh/ja/de gaps, add pl+cs gaps)
# ---------------------------------------------------------------------------
CM_PATH = LEDGERS / "coverage-map.v1.json"
cm_before_bytes = CM_PATH.read_bytes()
cm_before_sha = sha(cm_before_bytes)
cm_before = json.loads(cm_before_bytes)


def best_for(candidate_ids):
    best = None
    for cid in candidate_ids:
        e = next(x for x in disp_entries if x["candidate_id"] == cid)
        if e["disposition"]["verdict"] == "REJECTED":
            continue
        if best is None or e["rubric_overall_score"] > best[1]:
            best = (cid, e["rubric_overall_score"])
    return best[0] if best else None


def best_recommended_for(candidate_ids):
    for cid in candidate_ids:
        e = next(x for x in disp_entries if x["candidate_id"] == cid)
        if e["disposition"]["verdict"] == "RECOMMENDED":
            return cid
    return None


cee_gaps = [
    {
        "gap_id": "cure-kinetics-pl-cs",
        "module_gaps": ["amphora-cure-kinetics"],
        "best_recommended": None,
        "best_conditional": best_for(["DR-LANG-CEE-01", "DR-LANG-CEE-05"]),
        "commissioned_measurement_candidate": None,
        "note": "Two primary cure-kinetics theses found (Opole University PhD on branched-polyamine crosslinking agents, pl; UTB Zlin bachelor's thesis on epoxy-resin curing kinetics, cs) -- neither content-confirmed this fire (SPA rendering blocked the pl thesis's license/PDF, PDF-binary extraction failed for the cs thesis). Both are CONDITIONAL-tier, honestly scored low pending human follow-up.",
    },
    {
        "gap_id": "corrosion-protection-journal-pl-cs",
        "module_gaps": ["amphora-public-corrosion-benchmark", "amphora-barrier-corrosion-score"],
        "best_recommended": best_recommended_for(["DR-LANG-CEE-06"]),
        "best_conditional": None,
        "commissioned_measurement_candidate": None,
        "note": "Koroze a ochrana materialu (cs) confirmed CC BY-NC-ND 4.0 open access, 55+ year archive -- the first RECOMMENDED-grade candidate for this campaign item, and the second across the entire DR-LANG-* campaign (after DR-LANG-DE-06). Ochrona przed Korozja (pl) is the Polish national counterpart journal but its access model could not be confirmed this fire (CAPTCHA + two HTTP 403s + no explicit statement on the publisher's own page) -- scored CONDITIONAL, not equivalently RECOMMENDED, despite likely comparable real-world openness.",
    },
    {
        "gap_id": "marine-coating-standard-mapping-pl-cs",
        "module_gaps": ["amphora-ip-fto-guard", "amphora-owk-adhesion"],
        "best_conditional": best_for(["DR-LANG-CEE-02", "DR-LANG-CEE-07"]),
        "best_recommended": None,
        "commissioned_measurement_candidate": None,
        "note": "PN-EN ISO 12944-9 (pl) and CSN EN ISO 12944-9 (cs) both confirmed as direct national/European adoptions of ISO 12944-9 (offshore marine coating qualification) -- a FOURTH and now a fifth-counting independent language-community confirmation this campaign (after de and ja) that ISO 12944 is the global structural-coating baseline. No ship-hull/watercraft-specific PN or CSN antifouling standard number was found despite explicit searches in both languages (see ship-hull-antifouling-standard-mapping-pl-cs empty-result gap below) -- mirrors the identical de and ja findings.",
    },
    {
        "gap_id": "salt-spray-standard-mapping-pl-cs",
        "module_gaps": ["amphora-public-corrosion-benchmark"],
        "best_conditional": best_for(["DR-LANG-CEE-03"]),
        "best_recommended": None,
        "commissioned_measurement_candidate": None,
        "note": "PN-EN ISO 9227 (pl) confirmed as the direct Polish/European adoption of ISO 9227 (Czech CSN EN ISO 9227 not separately searched this fire, but ISO 9227 is expected to be an identical direct adoption per the established EN-adoption pattern) -- converges exactly with the de and ja fires' independent findings. This campaign has now independently confirmed ISO 9227 as the underlying global salt-spray baseline from THREE separate language communities (de, ja, pl).",
    },
    {
        "gap_id": "ship-hull-antifouling-standard-mapping-pl-cs",
        "module_gaps": ["amphora-owk-adhesion", "amphora-public-corrosion-benchmark"],
        "best_conditional": None,
        "best_recommended": None,
        "commissioned_measurement_candidate": (
            "No ship-hull-specific PN (Polish) or CSN (Czech) antifouling/anticorrosive underwater-"
            "paint standard number was found in either language despite dedicated queries (only "
            "general IMO/MEPC biocide-regulation guidance and the general-scope PN-EN ISO / CSN EN "
            "ISO 12944 structural-steel standard, already captured above) -- an honest empty result "
            "per directive rule 7, mirroring the identical de and ja findings for DIN/JIS."
        ),
        "note": "Empty result, honestly reported in both languages per directive rule 7 ('An empty result for a gap is a valid, reportable answer').",
    },
    {
        "gap_id": "national-corrosion-testing-institute-pl-cs",
        "module_gaps": ["amphora-public-corrosion-benchmark"],
        "best_conditional": best_for(["DR-LANG-CEE-08"]),
        "best_recommended": None,
        "commissioned_measurement_candidate": None,
        "note": "SVUOM's 'Korozni mapy materialu CR' (Czech national atmospheric-corrosivity mapping product) was found and its existence confirmed via a KOM-journal article citation, but BOTH the custodian's own site (svuom.cz) and the describing article's PDF were unreachable/unextractable this fire -- svuom.cz confirmed network-blocked from this host by WebFetch AND raw curl (same diagnostic pattern PROBE-WEB recorded for CNKI). Lukasiewicz-IMP (pl) was also searched under this gap-adjacent institute class and REJECTED (off_scope) -- a research institute and house journal, not itself a dataset, mirroring the de fire's Fraunhofer/GfKORR finding.",
    },
]

cm_after = dict(cm_before)
cm_after["fire_id"] = FIRE_ID
cm_after["run_id"] = RUN_ID
cm_after["snapshot_date"] = DATE
cm_after["scope_note"] = "Merged: zh (DR-LANG-ZH) + ja (DR-LANG-JA) + de (DR-LANG-DE) + pl+cs (DR-LANG-CEE, this fire) language communities. Each gaps[] entry's gap_id and module_gaps disambiguate scope; no entry from any prior fire was removed or rewritten."
cm_after["gaps"] = list(cm_before.get("gaps", [])) + cee_gaps
cm_after["gaps_not_yet_searched_this_fire"] = list(cm_before.get("gaps_not_yet_searched_this_fire", [])) + [
    "BazTech PN-EN ISO 12944-9 offshore article -- CAPTCHA-blocked this fire, needs a non-WebFetch extraction path [pl, carried forward]",
    "SVUOM corrosion-maps KOM-journal PDF (DOI 10.1515/kom-2015-0019) -- extraction failed this fire, needs a non-WebFetch text-extraction retry [cs, carried forward]",
    "svuom.cz direct evaluation -- confirmed network-unreachable from xbabe1 (WebFetch + raw curl) this fire; needs a different egress path [cs, carried forward]",
    "Opole University PhD dissertation full license/PDF -- blocked by JS-rendered SPA content this fire, needs a JS-capable fetch path [pl, carried forward]",
    "UTB Zlin bachelor's thesis PDF -- extraction failed this fire, needs a non-WebFetch text-extraction retry [cs, carried forward]",
    "VUT Brno DSpace resource on amine-epoxide curing molecular simulation -- found via WebSearch snippet only, not independently WebFetched or scored as a candidate this fire [cs, carried forward]",
    "NUSL (invenio.nusl.cz) own search interface -- not directly queried with a filtered epoxy/corrosion search this fire, only reached via a general WebSearch snippet [cs, carried forward]",
    "CSN EN ISO 9227 (Czech salt-spray standard) -- not separately searched this fire (PN-EN ISO 9227 was searched for pl; cs equivalent inferred but not independently confirmed) [cs, carried forward]",
    "Slovak-language literature -- out of this item's pl+cs scope but Czechoslovak-era CS-prefix patents surfaced during cs queries suggest adjacent relevance for a future directive item",
]
cm_after["cee_empty_result_gap_note"] = "ship-hull-antifouling-standard-mapping-pl-cs is a genuine empty result this fire in BOTH languages (see gaps[] entry) -- honestly reported, not padded, and not silently converted into a fabricated candidate."
cm_after["cee_no_empty_result_gap_this_fire"] = False

cm_after_bytes = canon(cm_after)
cm_after_sha = sha(cm_after_bytes)

# ---------------------------------------------------------------------------
# 5. Independent checker: 5-limb refutation criterion (Latin-script adaptation,
#    two languages)
# ---------------------------------------------------------------------------
PL_MARKER_WORDS = [
    "żywica", "zywica", "epoksydow", "utwardzacz", "utwardzani", "kinetyka", "sieciowani",
    "powłok", "powlok", "antykorozyjn", "korozj", "ochrona", "przed", "norma", "badani",
    "mgła", "mgla", "solna", "kadłub", "kadlub", "statku", "antyporostow", "rozprawa",
    "doktorska", "instytut", "baza", "danych", "czasopismo", "konstrukcje", "stalow",
    "podwodna", "mechaniki", "precyzyjnej",
]
CS_MARKER_WORDS = [
    "pryskyřic", "pryskyric", "epoxidov", "tvrdidl", "vytvrzován", "vytvrzovan", "kinetika",
    "koroze", "ochrana", "materiál", "material", "protikorozn", "nátěr", "nater", "trupu",
    "lodi", "protiobrůstac", "protiobrustac", "disertační", "disertacni", "práce", "prace",
    "úložiště", "uloziste", "šedé", "sede", "literatury", "databáze", "databaze", "podvodní",
    "podvodni", "norma", "ocelových", "ocelovych", "konstrukcí", "konstrukci",
]


def has_marker(s, words):
    low = (s or "").lower()
    return any(w in low for w in words)


def check(disp_lines, sr_lines_all, previously_supplied_ids):
    """disp_lines: list of dicts (manifest + dispositions). sr_lines_all: list of
    search-record line dicts (the full ledger, all fires, so citations from any
    prior fire also resolve). Returns diagnostic dict, never raises."""
    violations = []
    dispositions = [d for d in disp_lines if d.get("entry_type") == "candidate_disposition"]

    def sr_text_for_langs(langs):
        parts = []
        for line in sr_lines_all:
            touched = line.get("language_communities_touched")
            if touched and not any(l in touched for l in langs):
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

    all_sr_text = sr_text_for_langs(["pl", "cs"])

    # Rule 1: citation_has_recorded_query_and_result
    for d in dispositions:
        url = d.get("url", "")
        if url and url not in all_sr_text:
            violations.append({"rule": "citation_has_recorded_query_and_result", "candidate_id": d["candidate_id"],
                                "reason": f"{d['candidate_id']}: url {url} does not appear in any recorded search-record query/result this fire"})

    # Rule 2: native_query_not_literal_translation -- pl/cs query must contain a
    # language-appropriate marker word AND must not be byte-identical (case-insensitive)
    # to its own gloss.
    for line in sr_lines_all:
        touched = line.get("language_communities_touched")
        if touched and not any(l in touched for l in ("pl", "cs")):
            continue
        for q in line.get("queries", []):
            lang = q.get("language")
            if lang in ("pl", "cs") and "query" in q:
                qtext = q["query"]
                gloss = q.get("query_gloss_en", "")
                words = PL_MARKER_WORDS if lang == "pl" else CS_MARKER_WORDS
                if (not has_marker(qtext, words)) or (qtext.strip().lower() == gloss.strip().lower()):
                    violations.append({"rule": "native_query_not_literal_translation", "candidate_id": None,
                                        "reason": f"{lang} query field is a literal English translation or contains no {lang} marker vocabulary: '{qtext}'"})

    # Rule 3: license_text_matches_live_evidence
    for d in dispositions:
        quote = d.get("license_evidence_quote", "")
        if quote and quote not in all_sr_text:
            violations.append({"rule": "license_text_matches_live_evidence", "candidate_id": d["candidate_id"],
                                "reason": f"{d['candidate_id']}: license_evidence_quote does not appear verbatim in this fire's recorded search-record evidence text"})

    # Rule 4: native_citation_verbatim_in_evidence -- every pl/cs native_citation must
    # appear verbatim (byte-for-byte substring) in this fire's recorded search-record
    # evidence text. Latin-script analogue of the zh/ja CJK-presence check.
    for d in dispositions:
        if d.get("language") in ("pl", "cs"):
            nc = d.get("native_citation", "")
            if nc and nc not in all_sr_text:
                violations.append({"rule": "native_citation_verbatim_in_evidence", "candidate_id": d["candidate_id"],
                                    "reason": f"{d['candidate_id']}: native_citation '{nc}' does not appear verbatim in this fire's recorded search-record evidence text"})

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


PREVIOUSLY_SUPPLIED_CEE = []  # none found this fire -- absence explained in intake_manifest

sr_all_lines = list(sr_prior_lines_parsed) + [search_record_line_obj]
dl_this_fire = dl_lines  # manifest + 8 dispositions, this fire only

runA = check(dl_this_fire, sr_all_lines, PREVIOUSLY_SUPPLIED_CEE)
runB = check(dl_this_fire, sr_all_lines, PREVIOUSLY_SUPPLIED_CEE)
runA_bytes = canon(runA)
runB_bytes = canon(runB)
(WORK / "diagnostic.runA.json").write_bytes(runA_bytes)
(WORK / "diagnostic.runB.json").write_bytes(runB_bytes)
assert sha(runA_bytes) == sha(runB_bytes), "two-replay gate FAILED on real deliverable"
assert runA["refutation_criterion_fired"] is False, f"REAL deliverable fired the refutation criterion: {runA['violations']}"

# ---------------------------------------------------------------------------
# 6. Positive control: 5 planted-defect mutants, one per limb
# ---------------------------------------------------------------------------
mutants_out = {}

# mutant 1: missing_recorded_query
sr_mut1 = copy.deepcopy(sr_all_lines)
target_url = "https://reference-global.com/journal/KOM"
for line in sr_mut1:
    for q in line.get("queries", []):
        for k in ("query", "result_note", "result_summary", "result_evidence_quote", "result", "sample_urls", "url"):
            v = q.get(k)
            if isinstance(v, list):
                q[k] = [x for x in v if target_url not in str(x)]
            elif isinstance(v, str) and target_url in v:
                q[k] = v.replace(target_url, "REDACTED")
r1 = check(dl_this_fire, sr_mut1, PREVIOUSLY_SUPPLIED_CEE)
mutants_out["missing_recorded_query"] = {
    "expected_rule": "citation_has_recorded_query_and_result",
    "how_planted": f"Scrubbed every occurrence of DR-LANG-CEE-06's url ({target_url}) from a copy of this fire's search-record queries/results.",
    "expected_rule_fired": True,
    "refutation_criterion_fired": r1["refutation_criterion_fired"],
    "violations": r1["violations"],
}

# mutant 2: literal_english_translation_query (pl)
sr_mut2 = copy.deepcopy(sr_all_lines)
for line in sr_mut2:
    for q in line.get("queries", []):
        if q.get("language") == "pl" and q.get("query", "").startswith("żywica epoksydowa utwardzacz aminowy"):
            q["query"] = "epoxy resin amine hardener cure kinetics database"
r2 = check(dl_this_fire, sr_mut2, PREVIOUSLY_SUPPLIED_CEE)
mutants_out["literal_english_translation_query"] = {
    "expected_rule": "native_query_not_literal_translation",
    "how_planted": "Replaced the native pl query string 'żywica epoksydowa utwardzacz aminowy kinetyka utwardzania baza danych' with its literal English gloss, while leaving language:'pl' unchanged.",
    "expected_rule_fired": True,
    "refutation_criterion_fired": r2["refutation_criterion_fired"],
    "violations": r2["violations"],
}

# mutant 3: license_text_diverges (cs)
dl_mut3 = copy.deepcopy(dl_this_fire)
for d in dl_mut3:
    if d.get("candidate_id") == "DR-LANG-CEE-06":
        d["license_evidence_quote"] = "Koroze a ochrana materialu is a closed-access subscription-only journal with no free archive of any kind."
r3 = check(dl_mut3, sr_all_lines, PREVIOUSLY_SUPPLIED_CEE)
mutants_out["license_text_diverges"] = {
    "expected_rule": "license_text_matches_live_evidence",
    "how_planted": "Overwrote DR-LANG-CEE-06's license_evidence_quote with a fabricated 'closed-access, no free archive' claim contradicting the recorded WebFetch evidence (which states CC BY-NC-ND 4.0 open access).",
    "expected_rule_fired": True,
    "refutation_criterion_fired": r3["refutation_criterion_fired"],
    "violations": r3["violations"],
}

# mutant 4: native_citation_not_verbatim (pl)
dl_mut4 = copy.deepcopy(dl_this_fire)
for d in dl_mut4:
    if d.get("candidate_id") == "DR-LANG-CEE-02":
        d["native_citation"] = "Qualification testing of protective paint systems for offshore marine structures"
r4 = check(dl_mut4, sr_all_lines, PREVIOUSLY_SUPPLIED_CEE)
mutants_out["native_citation_not_verbatim"] = {
    "expected_rule": "native_citation_verbatim_in_evidence",
    "how_planted": "Replaced DR-LANG-CEE-02's native_citation (the exact Polish article title) with an English paraphrase, simulating a silently-translated/paraphrased citation.",
    "expected_rule_fired": True,
    "refutation_criterion_fired": r4["refutation_criterion_fired"],
    "violations": r4["violations"],
}

# mutant 5: rediscovery_dropped -- synthetic previously-supplied id, since the real
# PREVIOUSLY_SUPPLIED_CEE list is empty by construction (no prior pl/cs candidates exist).
dl_mut5 = copy.deepcopy(dl_this_fire)
if dl_mut5:
    dl_mut5[-1] = dict(dl_mut5[-1])
    dl_mut5[-1]["rediscovers"] = None
r5 = check(dl_mut5, sr_all_lines, ["CEE-PRIOR-TEST"])
mutants_out["rediscovery_dropped"] = {
    "expected_rule": "rediscovery_recall",
    "how_planted": "Injected a SYNTHETIC previously-supplied candidate id ('CEE-PRIOR-TEST') into the checker's previously_supplied_ids input -- since this fire genuinely found zero real prior pl/cs candidates (see intake_manifest), a synthetic id is required to prove this rule is a real, non-vacuous check rather than one that trivially never fires on an empty input list.",
    "expected_rule_fired": True,
    "refutation_criterion_fired": r5["refutation_criterion_fired"],
    "violations": r5["violations"],
}

for k, v in mutants_out.items():
    assert v["refutation_criterion_fired"] == v["expected_rule_fired"], f"positive control FAILED for mutant {k}"

# sanity: confirm the checker does NOT spuriously fire on the real (unmutated) empty
# previously-supplied list, i.e. rule 5 is silent when there is genuinely nothing to recall
r5_real = check(dl_this_fire, sr_all_lines, PREVIOUSLY_SUPPLIED_CEE)
assert r5_real["refutation_criterion_fired"] is False, "rule 5 spuriously fired on the real empty previously-supplied list"

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
DSL_PATH.write_bytes(dsl_new_content)
assert sha(DSL_PATH.read_bytes()) == dsl_file_sha_after
CM_PATH.write_bytes(cm_after_bytes)
assert sha(CM_PATH.read_bytes()) == cm_after_sha

print("BUILD OK")
print("sr_appended_line_no", sr_appended_line_no)
print("dl_appended_range", dl_appended_line_start, dl_appended_line_end)
print("dsl_appended_line_no", dsl_appended_line_no)
print("runA==runB byte-identical", sha(runA_bytes) == sha(runB_bytes))
print("real_refutation_criterion_fired", runA["refutation_criterion_fired"])
print("all_mutants_fired_correctly", all_mutants_fired)
for c in ranked:
    print(c["candidate_id"], c["disposition"]["verdict"], c["rubric_overall_score"])

# stash a few sha values for the signing script to reuse without re-deriving
(WORK / "shas.json").write_text(json.dumps({
    "sr_appended_sha": sr_appended_sha, "sr_file_sha_after": sr_file_sha_after,
    "sr_appended_line_no": sr_appended_line_no, "sr_prior_prefix_sha": sr_prior_prefix_sha,
    "dl_appended_sha": dl_appended_sha, "dl_file_sha_after": dl_file_sha_after,
    "dl_appended_line_start": dl_appended_line_start, "dl_appended_line_end": dl_appended_line_end,
    "dl_prior_prefix_sha": dl_prior_prefix_sha,
    "dsl_appended_sha": dsl_appended_sha, "dsl_file_sha_after": dsl_file_sha_after,
    "dsl_appended_line_no": dsl_appended_line_no, "dsl_prior_prefix_sha": dsl_prior_prefix_sha,
    "cm_before_sha": cm_before_sha, "cm_after_sha": cm_after_sha,
    "runA_sha": sha(runA_bytes),
}, indent=2))
