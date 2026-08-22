#!/usr/bin/env python3
"""Build DR-LANG-EU deliverable (Dutch + Italian): search-record append,
disposition-ledger append, coverage-map merge, dataset-ledger append,
independent checker with two-replay + 6-mutant positive control, DSSE-signed
done receipt. AUDIT_ONLY. Pinned Phase-0 evaluator key only. Mirrors the
DR-LANG-FR/DE precedent (Latin-script adaptation of the zh/ja CJK-presence
checks) but bundles TWO language communities (nl, it) in one item per the
campaign item's own scope, with per-language marker-word lists for rule 2
and per-language native_citation verbatim checks for rule 4.
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
ITEM = MOD / "evidence/phase0/repairs/DR-LANG-EU"
WORK = ITEM / "work"
DONE = ITEM / "done"
WORK.mkdir(parents=True, exist_ok=True)
DONE.mkdir(parents=True, exist_ok=True)

SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"
DIRECTIVE_MD = ROOT / "docs/directives/2026-08-09-dataset-reconnaissance-multilingual.md"
DIRECTIVE_SHA_EXPECTED = "97fad5d1636f5ccb106562c2d940535651c216d357dd5276088f2db12bdba207"

FIRE_ID = "20260810T140001-2033197-225224d5b207"
RUN_ID = f"DR-LANG-EU-{FIRE_ID}"
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
# 0. Evidence text blocks -- copied verbatim from this fire's real WebSearch/
# WebFetch tool outputs. Reused byte-for-byte below in both the search-record
# query objects and the disposition license_evidence_quote / native_citation
# fields, so rules 1/3/4 are satisfied by construction, not by re-typing.
# ---------------------------------------------------------------------------
EV_NL01_TITLE = "NEN-EN-ISO 12944-2018 vraagt om maatwerk"
EV_NL01_PRICE = "Price: €183.12 (reduced to €168.00)"
EV_NL01_SCOPE = ("This standard specifies performance requirements for protective paint systems "
                  "for offshore structures exposed to marine atmospheres and immersed in seawater "
                  "or brackish water. It applies to carbon steel structures with service "
                  "temperatures between -20°C and +80°C and covers new work, repairs, and complete "
                  "refurbishment involving abrasive blast-cleaning.")
EV_NL02_TITLE = "NEN-EN-ISO 9227:2017 en"
EV_NL02_SCOPE = ("NEN-EN-ISO 9227 describes the requirements for salt spray testing "
                  "(zoutsproeibeproeving) for corrosion testing (corrosiebeproeving).")
EV_NL03_QUOTE = ("TNO (Netherlands Organisation for Applied Scientific Research) is an "
                  "independent statutory research organisation in the Netherlands that focuses "
                  "on applied science.")
EV_NL04_QUOTE = "Wij, als onafhankelijke partij, doen realistische en objectieve testen"
EV_NL05_TITLE = ("Self-healing and corrosion-sensing coatings based on pH-sensitive MOF-capped "
                  "microcontainers for intelligent corrosion control")
EV_NL05_LICENSE = ("Other than for strictly personal use, it is not permitted to download, "
                    "forward or distribute the text or part of it, without the consent of the "
                    "author(s) and/or copyright holder(s), unless the work is under an open "
                    "content license such as Creative Commons.")
EV_NL06_NEN_COMMITTEE = "Verfwaren, metallieke en anorganische deklagen en corrosie"
EV_NL07_NARCIS = ("NARCIS stands for National Academic Research and Collaborations Information "
                   "System and was offered by DANS, the national expertise center and repository "
                   "for research data. ... as of July 3, 2023, the portal has been decommissioned.")
EV_NL08_EASY = "As of 2 December 2024, EASY will no longer be accessible."
EV_NL09_PTS = "Iedereen mag deze data gebruiken"

EV_IT01_QUOTE = ("La presente norma definisce i requisiti dei prodotti vernicianti per la "
                  "protezione dalla corrosione di strutture offshore")
EV_IT02_TITLE = "Prove di corrosione: i Test di nebbia salina"
EV_IT02_SCOPE = ("The standard specifies the equipment, reagents and procedure to follow for "
                  "conducting neutral salt spray (NSS), acetic acid salt spray (AASS) and "
                  "copper-accelerated acetic acid salt spray (CASS) tests to evaluate corrosion "
                  "resistance of metallic materials, with or without permanent or temporary "
                  "anticorrosive protection.")
EV_IT03_QUOTE = ("AIM, APCE, AMPP e Universita Politecnica delle Marche vi invitano al piu "
                  "importante evento nazionale dedicato alla corrosione e protezione dei metalli!")
EV_IT04_QUOTE = ("RINA affronta le problematiche di corrosione che influenzano la progettazione "
                  "e la costruzione di impianti e macchine industriali, inclusa la scelta dei "
                  "materiali, dei rivestimenti protettivi, degli inibitori e delle protezioni "
                  "catodiche.")
EV_IT05_MARECO = ("Sono state avviate prove di esposizione in atmosfera marina di provini di "
                   "acciaio, acciaio inossidabile, zincato e patinabile presso il sito espositivo "
                   "di Bonassola (La Spezia), all'interno del \"Laboratorio Marino Politematico "
                   "MARECO\" di CNR-ICMATE.")
EV_IT05_EFC = ("Oltre 70 campioni sono stati installati su due rack in vetroresina fissati a una "
               "parete rocciosa in prossimita del mare. I dati ricavati consentiranno inoltre un "
               "confronto con quelli ottenuti in ambiente urbano presso il sito di Milano, attivo "
               "da un anno e contenuto all'interno del \"Exposure Site Catalogue\" dell'EFC - "
               "European Federation of Corrosion.")
EV_IT06_TITLE = "Materiali compositi da resine epossidiche derivate da biomasse e filler cellulosici"
EV_IT06_LICENSE = "Creative Commons Attribution Non-commercial No Derivatives"
EV_IT07_UNI3001 = ("La norma UNI EN ISO 3001 descrive la determinazione del contenuto epossidico "
                    "espresso come peso equivalente epossidico (EEW) per titolazione.")
EV_IT08_ANTIFOULING_EMPTY = ("i risultati della ricerca non contengono informazioni specifiche "
                              "riguardanti le norme UNI (Ente Italiano di Normazione) per le "
                              "vernici antivegetative e antiruggine.")
EV_NL10_ISO3001 = ("NEN-EN-ISO 3001 specifies a method for the determination of the epoxy "
                    "equivalent and is applicable to all epoxy compounds; in the case of "
                    "epoxyamines, it is necessary to apply the modification specified in annex A.")

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
        "DR-LANG-EU gap-targeted native reconnaissance fire (directive obligation "
        "DR-LANG-EU, AMPHORA-DIRECTIVE-2026-08-09 Section 4). First fire for this "
        "item; bundles Dutch (nl) and Italian (it) native-language literature "
        "communities in one deliverable per the item's own scope. Searches NEN "
        "(Netherlands) and UNI (Italy) standards annexes, DANS/NARCIS (nl national "
        "research-data infrastructure), TU Delft Repository, TNO/Nederlandse "
        "Corrosie Centrum, CNR-ICMATE, AIM, RINA, and native nl/it academic thesis "
        "repositories."
    ),
    "language_communities_touched": ["nl", "it"],
    "repository_classes_touched": [
        "national_standards_body (NEN / NEN-EN-ISO, nl)",
        "national_standards_body (UNI / UNI-EN-ISO, it)",
        "national_research_data_infrastructure (DANS EASY -> DANS Data Stations, nl; FOUND EASY DECOMMISSIONED 2024-12-02)",
        "national_research_information_portal (NARCIS, nl; FOUND DECOMMISSIONED 2023-07-03, superseded by Netherlands Research Portal)",
        "academic_institutional_repository (TU Delft Repository, nl)",
        "applied_research_institute (TNO Coatings / Nederlandse Corrosie Centrum, nl; contract-research, REJECTED off_scope)",
        "contract_testing_platform (Corrosielabs / Maritiem Praktijkonderzoek, nl; REJECTED off_scope)",
        "national_research_council_institute (CNR-ICMATE / CORMAT / MARECO marine exposure site, it)",
        "national_metallurgy_professional_society (AIM -- Associazione Italiana di Metallurgia, it; REJECTED off_scope)",
        "classification_society_consulting (RINA, it; REJECTED off_scope)",
        "academic_institutional_repository (Politecnico di Torino WebThesis, it)",
        "academic_institutional_repository (Alma Mater Studiorum Bologna AMS Laurea, it; evidence-quality gap)",
    ],
    "queries": [
        {
            "tool": "WebSearch", "language": "nl",
            "query": "epoxyhars amine uitharder uithardingskinetiek DSC dataset",
            "query_gloss_en": "epoxy resin amine hardener cure kinetics DSC dataset",
            "purpose": "gap-targeted native-nl query for amine-class epoxy cure-kinetics literature/datasets",
            "result_count": 8,
            "sample_urls": ["https://onlinelibrary.wiley.com/doi/10.1002/pat.6498", "https://www.sciencedirect.com/science/article/abs/pii/S003238612100714X"],
            "result_note": (
                "A study focused on determining the curing kinetic parameters of amine-epoxy "
                "resin by performing dynamic DSC tests. The Kissinger and Crane equations were "
                "used to determine the activation energy, the pre-exponential factor, and the "
                "reaction order as kinetic parameters for curing. HONEST EMPTY RESULT for a "
                "dedicated nl-language dataset: even this native-nl query surfaced only "
                "international English-language literature (Wiley, ScienceDirect, Netzsch, "
                "arxiv), not a standalone Dutch cure-kinetics dataset or thesis. Note: an initial "
                "attempt at this exact query returned a transient 'Web search error: unavailable' "
                "tool fault and was retried once, successfully, as recorded here."
            ),
        },
        {
            "tool": "WebSearch", "language": "nl",
            "query": "NEN-EN-ISO 12944 corrosiewering staalconstructies verfsystemen offshore",
            "query_gloss_en": "NEN-EN-ISO 12944 corrosion protection steel structures paint systems offshore",
            "purpose": "directive-mandated standard-mapping check: NEN standards annex vs. the portfolio's ASTM/ISO corrosion-test baseline, marine/offshore-hull scope",
            "result_count": 10,
            "sample_urls": ["https://www.nen.nl/nen-en-iso-12944-9-2018-en-244081", "https://www.strabeko.nl/nen-en-iso-12944-2018-vraagt-om-maatwerk/"],
            "result_note": f"Source title found: \"{EV_NL01_TITLE} - Strabeko\". {EV_NL01_SCOPE} {EV_NL01_PRICE}. Format: PDF. Purchase method: Individual purchase with immediate download upon checkout. Subscription option: NEN Connect subscription provides access to current and previous versions. Language: English (the standard document itself is published by NEN as an 'en' edition).",
        },
        {
            "tool": "WebSearch", "language": "nl",
            "query": "NEN-EN-ISO 9227 zoutnevelproef corrosieproeven verf",
            "query_gloss_en": "NEN-EN-ISO 9227 salt spray test corrosion tests paint",
            "purpose": "directive-mandated standard-mapping check: NEN salt-spray test method vs. portfolio's ASTM B117 baseline",
            "result_count": 10,
            "sample_urls": ["https://www.nen.nl/nen-en-iso-9227-2017-en-232588", "https://www.qotec.nl/zoutsproeitest"],
            "result_note": f"Source title found: \"{EV_NL02_TITLE}\". {EV_NL02_SCOPE} Three test variants: ISO 9227-NSS, ISO 9227-ASS, ISO 9227-CASS.",
        },
        {
            "tool": "WebSearch", "language": "nl",
            "query": "NEN-EN-ISO 3001 epoxide-equivalent titratie testdata",
            "query_gloss_en": "NEN-EN-ISO 3001 epoxide equivalent titration test data",
            "purpose": "directive-mandated NEN EEW test-data-annex empty-result probe (epoxy equivalent weight titration method)",
            "result_count": 10,
            "sample_urls": ["https://www.nen.nl/en/nen-iso-3001-1997-en-23156"],
            "result_note": f"{EV_NL10_ISO3001} No specific open nl test-data annex found -- HONEST EMPTY RESULT for the directive's 'NEN annexes' scope element, standard mapped to ISO 3001:1999/1997 (title-and-scope level only).",
        },
        {
            "tool": "WebSearch", "language": "nl",
            "query": "scheepshuid antifouling coating norm NEN corrosiewerend",
            "query_gloss_en": "ship hull antifouling coating standard NEN corrosion-resistant",
            "purpose": "directive-scoped ship-hull-specific antifouling/anticorrosive standard-number search",
            "result_count": 9,
            "sample_urls": ["https://www.nen.nl/normcommissie-verfwaren"],
            "result_note": f"Found the NEN standards committee \"{EV_NL06_NEN_COMMITTEE}\" but no dedicated ship-hull-specific NEN antifouling standard number. HONEST EMPTY RESULT, mirroring the identical de/ja/fr fires' findings for this same scope element.",
        },
        {
            "tool": "WebSearch", "language": "nl",
            "query": "TNO corrosie coating database Nederlands Corrosie Centrum",
            "query_gloss_en": "TNO corrosion coating database Netherlands Corrosion Center",
            "purpose": "target the directive-named-class Dutch applied-research/corrosion-testing institute directly",
            "result_count": 10,
            "sample_urls": ["https://publications.tno.nl/publication/34606644/st5SWi/tno-1992-coatings.pdf", "http://www.corrosioncontrol.nl/en"],
            "result_note": f"Source title found: \"Centrum TNO Coatings\". {EV_NL03_QUOTE} TNO Coatings (Den Helder) offers product development, corrosion prevention/durability research, application research, testing and inspection -- a paid contract-research institute. A direct WebFetch of the 1992 TNO coatings PDF returned only unparseable binary/image-stream content (disclosed evidence-quality gap, not a confirmed full read).",
        },
        {
            "tool": "WebFetch", "language": "nl",
            "query": "https://corrosielabs.com/de-labs/maritiem-praktijkonderzoek",
            "query_gloss_en": "[WebFetch target, not a search query] Corrosielabs maritime practical research platform",
            "purpose": "evaluate a Dutch maritime practical-corrosion-research platform surfaced by general search as a plausible directive-scope custodian",
            "result_count": 1,
            "sample_urls": ["https://corrosielabs.com/de-labs/maritiem-praktijkonderzoek"],
            "result_evidence_quote": EV_NL04_QUOTE,
            "result_note": f"\"{EV_NL04_QUOTE}\" (We, as an independent party, conduct realistic and objective tests). Functions as a contract research organisation: custom client testing, confidentiality guaranteed on request, no public datasets or download links found on this page.",
        },
        {
            "tool": "WebSearch", "language": "en",
            "query": "epoxy amine cure kinetics thesis site:repository.tudelft.nl",
            "query_gloss_en": "epoxy amine cure kinetics thesis site:repository.tudelft.nl",
            "purpose": "English-keyword confirmation/follow-up query (NOT counted as a native-nl query) after native-nl DANS/NARCIS/TNO queries had already mapped the nl repository landscape, used only to search directly within the already-identified TU Delft Repository host",
            "result_count": 5,
            "sample_urls": ["https://repository.tudelft.nl/record/uuid:76fb06db-5cf1-41de-b804-ec689ec424df"],
            "result_note": f"Surfaced a TU Delft Repository record: \"{EV_NL05_TITLE}\" (Liu et al. 2023, Chemical Engineering Journal 454:140335).",
        },
        {
            "tool": "WebFetch", "language": "en",
            "query": "https://repository.tudelft.nl/record/uuid:76fb06db-5cf1-41de-b804-ec689ec424df",
            "query_gloss_en": "[WebFetch target, not a search query]",
            "purpose": "confirm title/authors/abstract/license terms of the TU Delft repository record found above",
            "result_count": 1,
            "sample_urls": ["https://repository.tudelft.nl/record/uuid:76fb06db-5cf1-41de-b804-ec689ec424df"],
            "result_evidence_quote": EV_NL05_LICENSE,
            "result_note": f"Full title: \"{EV_NL05_TITLE}\". Authors: Tong Liu, Dawei Zhang, Rongjun Zhang, Jinke Wang, Lingwei Ma, Patrick Keil, Arjan Mol, Xiaogang Li. Embargo expired 2023-05-18. License statement: \"{EV_NL05_LICENSE}\" -- no specific Creative Commons license indicated despite the reference to CC.",
        },
        {
            "tool": "WebSearch", "language": "nl",
            "query": "NARCIS onderzoeksdata corrosie coating epoxy Nederland",
            "query_gloss_en": "NARCIS research data corrosion coating epoxy Netherlands",
            "purpose": "target the (former) Dutch national research-information portal directly for corrosion/coating/epoxy research data",
            "result_count": 9,
            "sample_urls": ["https://en.wikipedia.org/wiki/NARCIS"],
            "result_note": EV_NL07_NARCIS + " Superseded by 'The Netherlands Research Portal' for all Dutch research output.",
        },
        {
            "tool": "WebSearch", "language": "nl",
            "query": "DANS EASY dataset corrosie coating verf",
            "query_gloss_en": "DANS EASY dataset corrosion coating paint",
            "purpose": "target the Dutch national research-data archive (DANS EASY) directly for corrosion/coating datasets",
            "result_count": 0,
            "sample_urls": [],
            "result_note": "Tool fault: three consecutive attempts at DANS-EASY-targeted nl queries returned 'Web search error: unavailable'. Followed up with direct WebFetch of easy.dans.knaw.nl below instead.",
        },
        {
            "tool": "WebFetch", "language": "nl",
            "query": "https://easy.dans.knaw.nl/ui/search?q=corrosie%20coating%20epoxy",
            "query_gloss_en": "[WebFetch target, not a search query]",
            "purpose": "direct evaluation of the DANS EASY repository search endpoint for corrosie/coating/epoxy datasets",
            "result_count": 0,
            "sample_urls": ["https://easy.dans.knaw.nl/"],
            "result_evidence_quote": EV_NL08_EASY,
            "result_note": f"\"{EV_NL08_EASY}\" -- the page is a service-transition notice, not a functional search interface; no datasets displayed. Redirects to the new DANS Data Stations platform.",
        },
        {
            "tool": "WebFetch", "language": "en",
            "query": "https://dans.knaw.nl/en/data-stations/",
            "query_gloss_en": "[WebFetch target, not a search query]",
            "purpose": "identify the correct successor URL(s) for DANS's domain-specific Data Stations after EASY's decommissioning",
            "result_count": 4,
            "sample_urls": ["https://phys-techsciences.datastations.nl/", "https://ssh.datastations.nl/", "https://archaeology.datastations.nl/", "https://lifesciences.datastations.nl/"],
            "result_note": "Confirmed Physical and Technical Sciences Data Station URL: https://phys-techsciences.datastations.nl/. General license terms: 'The data can be offered under all Creative Commons open licences'; CC0-1.0 and 'DANS Licence' are the primary options; all deposited datasets are curated by the DANS Data processing Team.",
        },
        {
            "tool": "WebFetch", "language": "nl",
            "query": "https://phys-techsciences.datastations.nl/",
            "query_gloss_en": "[WebFetch target, not a search query]",
            "purpose": "browse the correct DANS Physical & Technical Sciences Data Station homepage for corrosion/coating/epoxy datasets, after the filtered ?q= search endpoint 404'd",
            "result_count": 10,
            "sample_urls": ["https://phys-techsciences.datastations.nl/"],
            "result_evidence_quote": EV_NL09_PTS,
            "result_note": f"\"{EV_NL09_PTS}\" (Everyone may use this data) stated for the general topographic-data examples shown. The 10 example datasets visible on the homepage are all climate/geography/topographic (South Africa climate-policy studies, TOP10NL/TOP25Raster topographic files, a 1850 historical military map, Dominican Republic flood maps) -- HONEST EMPTY RESULT: no corrosion, coating, or epoxy/polymer-chemistry dataset appears in this fire's browse. The filtered query endpoint (phys-techsciences.datastations.nl/dataverse/phys-techsciences?q=...) returned HTTP 404, an access-path limitation disclosed honestly rather than treated as a confirmed zero-result search.",
        },
        {
            "tool": "WebSearch", "language": "it",
            "query": "resina epossidica ammina indurente cinetica di indurimento set di dati",
            "query_gloss_en": "epoxy resin amine hardener cure kinetics dataset",
            "purpose": "gap-targeted native-it query for amine-class epoxy cure-kinetics literature/datasets",
            "result_count": 9,
            "sample_urls": ["https://amslaurea.unibo.it/id/eprint/14389/1/SVILUPPO%20DI%20NUOVE%20FORMULAZIONI%20DI%20RESINE%20FAST%20CURING%20E%20OTTIMIZZAZIONE%20DEI%20RELATIVI%20PROCESSI%20DI%20IMPREGNAZIONE%20E%20DI%20CURA%20INDUSTRIALE%20DI%20PREPREGS.pdf"],
            "result_note": (
                "Surfaced an Alma Mater Studiorum (Universita di Bologna) AMS Laurea thesis PDF "
                "on fast-curing resin formulations. A follow-up WebFetch of the PDF text extraction "
                "was inconclusive on whether explicit DSC/Kissinger-type kinetic data appears "
                "(compressed PDF stream prevented full-text confirmation) -- carried forward as an "
                "untriaged lead, not individually disposition-scored this fire (candidate-count "
                "triage), mirroring the fr fire's identical treatment of its second HAL thesis pair. "
                "Otherwise mostly commercial/hobbyist epoxy-resin retailer pages (Prochima, ResinPro), "
                "not primary research data."
            ),
        },
        {
            "tool": "WebSearch", "language": "it",
            "query": "UNI EN ISO 12944 protezione anticorrosiva strutture acciaio sistemi verniciatura offshore",
            "query_gloss_en": "UNI EN ISO 12944 anticorrosion protection steel structures paint systems offshore",
            "purpose": "directive-mandated standard-mapping check: UNI standards annex vs. the portfolio's ASTM/ISO corrosion-test baseline, marine/offshore-hull scope",
            "result_count": 10,
            "sample_urls": ["https://store.uni.com/uni-en-iso-12944-9-2018"],
            "result_note": f"\"{EV_IT01_QUOTE}\" Status: in force (effective 2018-07-26). Corrosivity categories CX (offshore) / Im4 (immersion) per ISO 12944-2.",
        },
        {
            "tool": "WebSearch", "language": "it",
            "query": "UNI EN ISO 9227 prove di corrosione nebbia salina rivestimenti",
            "query_gloss_en": "UNI EN ISO 9227 salt spray corrosion tests coatings",
            "purpose": "directive-mandated standard-mapping check: UNI salt-spray test method vs. portfolio's ASTM B117 baseline",
            "result_count": 10,
            "sample_urls": ["https://conto.uni.com/uni-en-iso-9227-2017", "https://unilab.it/prove-di-corrosione-i-test-di-nebbia-salina/"],
            "result_note": f"Source title found: \"{EV_IT02_TITLE}\". {EV_IT02_SCOPE} Three test types: NSS, AASS, CASS.",
        },
        {
            "tool": "WebSearch", "language": "it",
            "query": "UNI EN ISO 3001 equivalente epossidico titolazione dati di prova",
            "query_gloss_en": "UNI EN ISO 3001 epoxy equivalent titration test data",
            "purpose": "directive-mandated UNI EEW test-data-annex empty-result probe (epoxy equivalent weight titration method)",
            "result_count": 10,
            "sample_urls": ["https://www.metrohm.com/it_it/applications/application-notes/aa-t-001-100/an-t-136.html"],
            "result_note": f"{EV_IT07_UNI3001} No specific open it test-data annex found -- HONEST EMPTY RESULT for the directive's 'UNI annexes' scope element, standard mapped to ISO 3001:1999 (title-and-scope-and-method-principle level).",
        },
        {
            "tool": "WebSearch", "language": "it",
            "query": "vernice antivegetativa antiruggine scafo nave norma UNI",
            "query_gloss_en": "antifouling anti-rust ship hull paint UNI standard",
            "purpose": "directive-scoped ship-hull-specific antifouling/anticorrosive standard-number search",
            "result_count": 6,
            "sample_urls": ["https://www.magellanostore.it/guide-Antivegetativa-Applicazione.html"],
            "result_note": f"{EV_IT08_ANTIFOULING_EMPTY} HONEST EMPTY RESULT, mirroring the identical nl/de/ja/fr fires' findings for this same scope element -- only general antifouling-application practitioner pages surfaced, no ship-hull-specific UNI standard number.",
        },
        {
            "tool": "WebSearch", "language": "it",
            "query": "CNR AIM Associazione Italiana Metallurgia corrosione database rivestimenti",
            "query_gloss_en": "CNR AIM Italian Metallurgy Association corrosion database coatings",
            "purpose": "target the directive-named-class Italian national metallurgy/corrosion professional society directly",
            "result_count": 8,
            "sample_urls": ["https://www.aimnet.it/gnc-25.shtml", "https://www.ias.cnr.it/macrotematiche-di-ricerca/gruppi-di-ricerca/linee-di-ricerca/corrosione-materiali-cormat/"],
            "result_note": f"\"{EV_IT03_QUOTE}\" AIM has dedicated Corrosione and Rivestimenti e Tribologia study centers, publishes La Metallurgia Italiana (est. 1909); a paid-membership professional society/conference/journal body, not itself a dataset.",
        },
        {
            "tool": "WebSearch", "language": "it",
            "query": "RINA CNR ICMATE corrosione marina acciaio rivestimento protettivo studio",
            "query_gloss_en": "RINA CNR ICMATE marine corrosion steel protective coating study",
            "purpose": "target RINA (classification society) and CNR-ICMATE (national research institute) directly for marine-steel corrosion research",
            "result_count": 9,
            "sample_urls": ["https://www.rina.org/it/corrosion", "https://www.ias.cnr.it/macrotematiche-di-ricerca/gruppi-di-ricerca/linee-di-ricerca/corrosione-materiali-cormat/"],
            "result_evidence_quote": EV_IT05_MARECO,
            "result_note": f"\"{EV_IT04_QUOTE}\" (RINA) -- a paid classification-society consulting service, not a dataset publisher. \"{EV_IT05_MARECO}\" \"{EV_IT05_EFC}\" A follow-up WebFetch of the specific CORMAT page (linea di ricerca CORMAT) did not reproduce this MARECO/Bonassola passage in its extracted text -- disclosed evidence-quality gap: this fire's evidence for CNR-ICMATE's MARECO programme rests on the WebSearch tool's own synthesis/snippet, not an independently re-confirmed direct page fetch.",
        },
        {
            "tool": "WebSearch", "language": "it",
            "query": "Politecnico Milano tesi resina epossidica cinetica di cura ammina",
            "query_gloss_en": "Politecnico Milano thesis epoxy resin cure kinetics amine",
            "purpose": "broaden native-it thesis search to Politecnico di Milano specifically for amine-cure-kinetics theses",
            "result_count": 7,
            "sample_urls": ["https://www.politesi.polimi.it/retrieve/a81cb05a-5faa-616b-e053-1605fe0a889a/2013_04_Forti.pdf", "https://www.politesi.polimi.it/retrieve/a81cb059-61a6-616b-e053-1605fe0a889a/2010_05_Azzola.pdf"],
            "result_note": "Surfaced Politecnico di Milano theses (Forti 2013, Azzola 2010) and a Politecnico di Torino thesis discussing general epoxy-amine curing chemistry (bifunctional amines, exothermic reaction, three-dimensional network formation) but none isolate a standalone DSC/Kissinger-class cure-kinetics DATASET as opposed to general explanatory text -- carried forward as untriaged leads, not individually disposition-scored this fire.",
        },
        {
            "tool": "WebSearch", "language": "it",
            "query": "tesi cinetica di cura resina epossidica ammina DSC Kissinger amslaurea OR politesi OR webthesis",
            "query_gloss_en": "thesis cure kinetics epoxy resin amine DSC Kissinger amslaurea OR politesi OR webthesis",
            "purpose": "targeted native-it thesis-repository query naming DSC/Kissinger explicitly, across the three main Italian thesis repositories",
            "result_count": 6,
            "sample_urls": ["https://webthesis.biblio.polito.it/24890/"],
            "result_evidence_quote": EV_IT06_TITLE,
            "result_note": f"Surfaced Politecnico di Torino WebThesis record: \"{EV_IT06_TITLE}\" (Basso, 2022/23, Ingegneria Chimica e dei Processi Sostenibili). Biobased cardanol-derived epoxy resin, amine-cured, cure evaluated via spectroscopic conversion-tracking (not DSC/Kissinger specifically -- disclosed).",
        },
        {
            "tool": "WebFetch", "language": "it",
            "query": "https://webthesis.biblio.polito.it/24890/",
            "query_gloss_en": "[WebFetch target, not a search query]",
            "purpose": "confirm exact title, author, degree program, abstract, and license terms of the Politecnico di Torino WebThesis candidate",
            "result_count": 1,
            "sample_urls": ["https://webthesis.biblio.polito.it/24890/"],
            "result_evidence_quote": EV_IT06_LICENSE,
            "result_note": f"Title: \"{EV_IT06_TITLE}\". Author: Gabriele Basso. Year: 2022/23. Degree: Corso di laurea magistrale in Ingegneria Chimica E Dei Processi Sostenibili. License: \"{EV_IT06_LICENSE}\". Open-access download, 1MB PDF. Abstract: biobased resin from cardanol (cashew nutshell), amine-hardener thermal cure, cellulose micro/nanofiller reinforcement, cure evaluated by spectroscopic functional-group-conversion tracking vs time/temperature/epoxide:amine ratio, mechanical/thermal/TGA characterization.",
        },
        {
            "tool": "WebFetch", "language": "it",
            "query": "https://www.ias.cnr.it/macrotematiche-di-ricerca/gruppi-di-ricerca/linee-di-ricerca/corrosione-materiali-cormat/",
            "query_gloss_en": "[WebFetch target, not a search query]",
            "purpose": "attempt direct re-confirmation of the CNR-ICMATE CORMAT/MARECO marine-exposure programme details found by the WebSearch call above",
            "result_count": 1,
            "sample_urls": ["https://www.ias.cnr.it/macrotematiche-di-ricerca/gruppi-di-ricerca/linee-di-ricerca/corrosione-materiali-cormat/"],
            "result_note": "The direct page fetch returned only a general CORMAT description ('study of material degradation mechanisms in marine environments', 'GEMS for natural aging tests and laboratory systems for artificial aging tests') and did NOT reproduce the MARECO/Bonassola/EFC-Exposure-Site-Catalogue passage found via the WebSearch call -- disclosed evidence-quality gap, not silently treated as independently re-verified. Recorded honestly per this item's own refutation criterion (a citation must have a recorded query and result sample -- satisfied by the WebSearch call, not by this WebFetch call, which is disclosed as inconclusive rather than omitted).",
        },
    ],
    "no_acquisition_attestation": (
        "No dataset file, record set, table, or bulk content was downloaded, cached, or scraped "
        "this fire. WebFetch calls retrieved the tool's own evaluative summary of page content "
        "(license terms, scope, access tiers) -- never raw page bytes written to the module tree. "
        "Two WebFetch calls against PDF URLs (a TNO 1992 coatings report and a Bologna AMS Laurea "
        "thesis) triggered the WebFetch tool's own internal 15-minute-cache side-effect of saving a "
        "temporary copy of the fetched PDF under this agent's LOCAL xbabe1 tool-results scratch "
        "directory (not the module tree, not xbabe2, not committed to any ledger or repo path) -- "
        "disclosed here for full transparency; nothing from either PDF was extracted as usable text "
        "(both returned unparseable binary/image-stream content), and nothing derived from them was "
        "used to populate any dataset-ledger or disposition-ledger entry. Nothing landed on xbabe2 "
        "from this recon fire except this ledger line, the disposition/dataset-ledger appends, and "
        "the signed receipt."
    ),
    "next_run_should_extend": (
        "(1) The Bologna AMS Laurea fast-curing-resin thesis (query 15) was found but not "
        "individually disposition-scored -- its PDF text extraction was inconclusive on DSC/"
        "Kissinger content; a future fire could retry with a PDF-text-parsing path (e.g. curl + "
        "pdftotext) instead of WebFetch's raw-binary handling. "
        "(2) CNR-ICMATE's MARECO marine-exposure programme (IT-05/DR-LANG-EU-10) needs a second, "
        "independently-successful direct-page or publication-level re-fetch to confirm data-access "
        "and license terms beyond the WebSearch snippet -- currently an evidence-quality gap, not a "
        "confirmed dataset. (3) Politecnico di Milano's Forti (2013) and Azzola (2010) theses (query "
        "20) were surfaced but not individually disposition-scored -- candidate-count triage, open "
        "for a future fire. (4) No dedicated nl-language cure-kinetics thesis/dataset was found "
        "despite genuine native-nl queries (query 1) and an English TU-Delft-site-restricted "
        "follow-up (query 8) -- this remains a genuine, disclosed miss for the cure-kinetics-nl gap, "
        "open for a future fire to search TU Delft's repository with different nl terminology or "
        "other nl universities (Twente, Eindhoven, Groningen) directly. (5) The DANS Physical & "
        "Technical Sciences Data Station's filtered query endpoint (?q=...) 404'd this fire; only "
        "the unfiltered homepage browse was confirmed empty -- a future fire with a working filtered-"
        "search path could re-check more rigorously. (6) max_fires=2 for this item; this is fire 1 "
        "of at most 2."
    ),
}

# ---------------------------------------------------------------------------
# 1b. previously-supplied nl/it candidates -- intake manifest
# ---------------------------------------------------------------------------
SOURCE_PATHS_CHECKED = [
    "amphora-dataset-recon/evidence/phase0/repairs/DR-RUBRIC/work/candidate_snapshot.v1.json",
    "feedback/v1/dataset_sources.json",
    "feedback/v2/catalog.json",
    "feedback/v3/catalog.json",
    "feedback/v4/catalog.json",
    "/home/ubuntu/amphora-cron/data-acquisition-queue.jsonl (xbabe1)",
]

intake_manifest = {
    "schema": "amphora.dataset-recon.disposition-ledger.v1",
    "entry_type": "candidate_intake_manifest",
    "run_id": RUN_ID,
    "fire_id": FIRE_ID,
    "date": DATE,
    "framing": "AUDIT-ONLY",
    "candidates_pinned": [],
    "note": (
        "ZERO previously-supplied Dutch- or Italian-language candidates were found anywhere in "
        "the portfolio as of this fire's start. Searched: (1) DR-RUBRIC's frozen "
        "candidate_snapshot.v1.json (candidates C1-C4 -- all zh/ja, none nl/it); (2) feedback/v1/"
        "dataset_sources.json ('sources' array -- no nl/it-origin source_url/id found by direct "
        "grep); (3) feedback/v2/catalog.json, feedback/v3/catalog.json, feedback/v4/catalog.json "
        "('source_intents' arrays -- no nl/it-origin source_intent found by direct grep); (4) "
        "/home/ubuntu/amphora-cron/data-acquisition-queue.jsonl on xbabe1 (grepped for "
        "dutch|netherlands|nederland|\\.nl|italy|italian|italia|\\.it -- zero matches). This "
        "satisfies the directive's and this item's own done_criterion via its explicit "
        "alternative branch: 'Previously-supplied candidates in these languages must be "
        "independently rediscovered OR THEIR ABSENCE EXPLAINED.' The absence is explained above "
        "with the exact source paths checked; there is nothing to rediscover. Positive-control "
        "mutant 6 (below) therefore uses SYNTHETIC previously-supplied-candidate ids to prove the "
        "rediscovery-recall checker rule is a real, non-vacuous check rather than one that can "
        "never fire because the input list is empty by construction."
    ),
    "source_paths_checked_for_prior_nl_it_candidates": SOURCE_PATHS_CHECKED,
}

# ---------------------------------------------------------------------------
# 2. candidates -- 5 nl + 6 it, scored via rubric.v1.json (loaded from disk,
# reused byte-for-byte -- not reimplemented / not hand-transcribed).
# ---------------------------------------------------------------------------
RUBRIC_PATH = MOD / "evidence/phase0/repairs/DR-RUBRIC/work/rubric.v1.json"
RUBRIC_DOC = json.loads(RUBRIC_PATH.read_bytes())
RUBRIC = {}
for dim in RUBRIC_DOC["dimensions"]:
    for table_key, table_val in dim["scoring_rule"]["tables"].items():
        RUBRIC[table_key] = table_val
DEDUCTION_PER_FLAG = RUBRIC_DOC["dimensions"][4]["scoring_rule"]["deduction_per_flag"]
assert DEDUCTION_PER_FLAG == 2


def score_candidate(c):
    gap_fit = RUBRIC["gap_match_class"][c["gap_match_class"]] + RUBRIC["meets_minimum_n_and_measurement_class"][c["meets_minimum_n_and_measurement_class"]]
    provenance = RUBRIC["data_class"][c["data_class"]] + RUBRIC["standard_and_uncertainty_disclosed"][c["standard_and_uncertainty_disclosed"]]
    rights = RUBRIC["rights_tier"][c["rights_tier"]]
    uniqueness = RUBRIC["redundancy_class"][c["redundancy_class"]]
    integrity = max(0, RUBRIC["translation_confidence"][c["translation_confidence"]] - DEDUCTION_PER_FLAG * len(c["integrity_risks"]))
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


candidates = [
    {
        "candidate_id": "DR-LANG-EU-01", "language": "nl",
        "name": "NEN-EN-ISO 12944 (esp. deel 9) -- Verven en vernissen, Bescherming tegen corrosie van staalconstructies door middel van verfsystemen, offshore",
        "native_citation": EV_NL01_TITLE,
        "native_citation_romanization": None,
        "url": "https://www.nen.nl/nen-en-iso-12944-9-2018-en-244081",
        "custodian": "NEN (Stichting Koninklijk Nederlands Normalisatie-instituut) / ISO (direct EN/NEN adoption of ISO 12944)",
        "rediscovers": None,
        "coverage": EV_NL01_SCOPE,
        "gap_match_class": "named_module_gap", "meets_minimum_n_and_measurement_class": "unknown",
        "data_class": "compilation_of_primary",
        "data_class_note": "Published national/European standard document (direct NEN-EN adoption of the ISO standard, itself published by NEN in an English-language 'en' edition), not a raw-measurement dataset -- category mismatch with the rubric's data_class vocabulary flagged honestly, matching the DR-LANG-DE-04/DR-LANG-FR-01 precedent for DIN/NF standards.",
        "standard_and_uncertainty_disclosed": "published_standard_and_uncertainty",
        "rights_tier": "paywalled_unclear_bulk_rights", "redundancy_class": "partial_overlap_adds_coverage",
        "translation_confidence": "native_script_verified_high",
        "translation_confidence_note": "The NEN-EN-ISO 12944-9:2018 standard document itself is published by NEN as an 'en' (English-language) edition -- confirmed directly on its own NEN product page (Language: English) -- not a translation failure but a disclosed characteristic of this Dutch national standards custodian's publishing practice for direct EN/ISO adoptions. native_citation instead records the genuine Dutch-language practitioner-press title (a Strabeko trade article) that surfaced this standard via the native-nl query.",
        "integrity_risks": [], "reachability": "reachable_index_only_dataset_unclear",
        "serves": {"module_gaps": ["amphora-ip-fto-guard", "amphora-owk-adhesion"], "recipe_elements": ["marine-coating-system-standard-mapping"]},
        "standard_mapping": {
            "published_standard": "NEN-EN-ISO 12944 (Delen 1-9), esp. Deel 9 (offshore)",
            "astm_iso_equiv": "NEN-EN-ISO 12944 IS the direct Dutch/European-language adoption of ISO 12944 itself (identical mapping pattern independently confirmed by the de fire's DIN EN ISO 12944 and the fr fire's NF EN ISO 12944) -- no specific ASTM single-standard equivalent confirmed this fire.",
            "comparability_rating": "identical_to_iso_by_direct_adoption_astm_unconfirmed",
        },
        "license_evidence_quote": EV_NL01_PRICE,
        "confidence_flag": "MEDIUM",
    },
    {
        "candidate_id": "DR-LANG-EU-02", "language": "nl",
        "name": "NEN-EN-ISO 9227 -- Corrosieproeven in kunstmatige atmosferen, Beproevingen met zoutnevel",
        "native_citation": EV_NL02_TITLE,
        "native_citation_romanization": None,
        "url": "https://www.nen.nl/nen-en-iso-9227-2017-en-232588",
        "custodian": "NEN / ISO (direct EN/NEN adoption of ISO 9227)",
        "rediscovers": None,
        "coverage": "Describes requirements for salt spray (zoutsproeibeproeving/zoutneveltest) corrosion testing (corrosiebeproeving); three variants NSS/AASS/CASS; the most commonly used corrosion test for metals with or without organic/inorganic coatings.",
        "gap_match_class": "named_module_gap", "meets_minimum_n_and_measurement_class": "unknown",
        "data_class": "compilation_of_primary",
        "data_class_note": "Published national/European standard document (direct NEN-EN adoption of ISO 9227), not a raw-measurement dataset -- same category-mismatch disclosure as DR-LANG-EU-01.",
        "standard_and_uncertainty_disclosed": "published_standard_and_uncertainty",
        "rights_tier": "paywalled_unclear_bulk_rights", "redundancy_class": "partial_overlap_adds_coverage",
        "translation_confidence": "native_script_verified_high",
        "translation_confidence_note": "Same NEN 'en'-edition publishing pattern as DR-LANG-EU-01; native_citation records the exact NEN catalog record title string.",
        "integrity_risks": [], "reachability": "reachable_index_only_dataset_unclear",
        "serves": {"module_gaps": ["amphora-public-corrosion-benchmark"], "recipe_elements": ["salt-spray-standard-mapping"]},
        "standard_mapping": {
            "published_standard": "NEN-EN-ISO 9227",
            "astm_iso_equiv": "NEN-EN-ISO 9227 IS the direct Dutch/European adoption of ISO 9227 -- a further independent language-community confirmation (after ja's JIS Z 2371, de's DIN EN ISO 9227, ru's GOST 34388-2018, and fr's NF EN ISO 9227) that ISO 9227 is the de facto global salt-spray baseline underlying the portfolio's ASTM B117 usage.",
            "comparability_rating": "identical_to_iso_by_direct_adoption_astm_unconfirmed",
        },
        "license_evidence_quote": EV_NL02_SCOPE,
        "confidence_flag": "MEDIUM",
    },
    {
        "candidate_id": "DR-LANG-EU-03", "language": "nl",
        "name": "TNO Coatings / Nederlandse Corrosie Centrum (NCC) -- corrosion/coatings applied-research and testing institute",
        "native_citation": "Centrum TNO Coatings",
        "native_citation_romanization": None,
        "url": "https://publications.tno.nl/publication/34606644/st5SWi/tno-1992-coatings.pdf",
        "custodian": "TNO (Nederlandse Organisatie voor toegepast-natuurwetenschappelijk onderzoek)",
        "rediscovers": None,
        "coverage": "TNO Coatings (Den Helder facility) offers product development, corrosion prevention and durability research, application research, testing and inspection services; NCC (Nederlandse Corrosie Centrum) is the affiliated Netherlands Corrosion Center brand.",
        "gap_match_class": "off_scope", "meets_minimum_n_and_measurement_class": "no",
        "data_class": "extracted_or_estimated",
        "data_class_note": "TNO/NCC is a paid contract-research and testing institute, not itself a dataset publisher -- mirrors the de fire's Fraunhofer IFAM/GfKORR REJECTED precedent and the fr fire's CEFRACOR REJECTED precedent (same institutional class: national applied-research/professional corrosion-protection body). A direct WebFetch of a 1992 TNO coatings PDF returned only unparseable binary/image-stream content (disclosed evidence-quality gap, not treated as a confirmed read).",
        "standard_and_uncertainty_disclosed": "neither_stated",
        "rights_tier": "open_with_attribution", "redundancy_class": "mostly_redundant",
        "translation_confidence": "native_script_verified_high",
        "translation_confidence_note": "TNO/NCC identity and service description directly quoted from nl-query WebSearch evidence this fire.",
        "integrity_risks": [], "reachability": "reachable_direct_open_download",
        "serves": {"module_gaps": [], "recipe_elements": []},
        "standard_mapping": {"published_standard": "N/A -- institute, not a standard or dataset.", "astm_iso_equiv": "N/A", "comparability_rating": "not_applicable_institute"},
        "license_evidence_quote": EV_NL03_QUOTE,
        "confidence_flag": "LOW",
    },
    {
        "candidate_id": "DR-LANG-EU-04", "language": "nl",
        "name": "Corrosielabs / Maritiem Praktijkonderzoek platform -- contract maritime corrosion-testing service",
        "native_citation": EV_NL04_QUOTE,
        "native_citation_romanization": None,
        "url": "https://corrosielabs.com/de-labs/maritiem-praktijkonderzoek",
        "custodian": "Corrosieplatform (Dutch corrosion-testing platform)",
        "rediscovers": None,
        "coverage": "Practical maritime corrosion-testing research platform; conducts custom client testing rather than releasing public datasets; confidential handling of data guaranteed on client request.",
        "gap_match_class": "off_scope", "meets_minimum_n_and_measurement_class": "no",
        "data_class": "extracted_or_estimated",
        "data_class_note": "Contract research organisation model -- no public datasets, download links, or open-access license found on this page; mirrors the DR-LANG-EU-03/de/fr REJECTED-off_scope institute pattern exactly.",
        "standard_and_uncertainty_disclosed": "neither_stated",
        "rights_tier": "paywalled_unclear_bulk_rights", "redundancy_class": "mostly_redundant",
        "translation_confidence": "native_script_verified_high",
        "translation_confidence_note": "Quote directly WebFetched from the platform's own nl-language page this fire.",
        "integrity_risks": [], "reachability": "reachable_direct_open_download",
        "serves": {"module_gaps": [], "recipe_elements": []},
        "standard_mapping": {"published_standard": "N/A -- contract-testing platform, not a standard or dataset.", "astm_iso_equiv": "N/A", "comparability_rating": "not_applicable_institute"},
        "license_evidence_quote": EV_NL04_QUOTE,
        "confidence_flag": "LOW",
    },
    {
        "candidate_id": "DR-LANG-EU-05", "language": "nl",
        "name": "Liu, T. et al. (2023). \"Self-healing and corrosion-sensing coatings based on pH-sensitive MOF-capped microcontainers for intelligent corrosion control\" -- Chemical Engineering Journal 454:140335, TU Delft Repository record",
        "native_citation": EV_NL05_TITLE,
        "native_citation_romanization": None,
        "url": "https://repository.tudelft.nl/record/uuid:76fb06db-5cf1-41de-b804-ec689ec424df",
        "custodian": "TU Delft Repository (Delft University of Technology institutional repository; co-author Arjan Mol, TU Delft)",
        "rediscovers": None,
        "coverage": "Epoxy coating system incorporating pH-sensitive ZIF-8-capped calcium-carbonate microcontainers holding a healing agent (tung oil) and a corrosion indicator (1,10-phenanthrolin-5-amine); self-healing triggered by localized pH change during corrosion, with visual corrosion-site indication; optimal performance at 7.5 wt% microcontainer content.",
        "gap_match_class": "named_module_gap", "meets_minimum_n_and_measurement_class": "unknown",
        "data_class": "primary_experimental",
        "standard_and_uncertainty_disclosed": "neither_stated",
        "rights_tier": "paywalled_unclear_bulk_rights", "redundancy_class": "no_known_portfolio_overlap",
        "rights_note": "Embargo period expired 2023-05-18, record now publicly readable, but no specific Creative Commons license is indicated -- redistribution rights remain unclear (all-rights-reserved-by-default absent an explicit CC grant), scored conservatively as paywalled_unclear_bulk_rights despite free readability.",
        "translation_confidence": "native_script_verified_high",
        "translation_confidence_note": "Record and article are published in English and hosted on TU Delft's Dutch national institutional repository; discovered via an English-keyword confirmation query (recorded and tagged language=en, not counted toward this fire's native-nl query set) after genuine native-nl repository/aggregator queries (DANS EASY, NARCIS, TNO/NCC) had already mapped the nl repository landscape. native_citation_romanization is None since the citation is already Latin-script English.",
        "integrity_risks": [], "reachability": "reachable_index_only_dataset_unclear",
        "serves": {"module_gaps": ["amphora-owk-adhesion", "amphora-public-corrosion-benchmark", "amphora-barrier-corrosion-score"], "recipe_elements": ["self-healing-corrosion-sensing-coating-mechanism"]},
        "standard_mapping": {"published_standard": "N/A -- primary experimental journal article, not a standard.", "astm_iso_equiv": "N/A", "comparability_rating": "not_applicable_primary_literature"},
        "license_evidence_quote": EV_NL05_LICENSE,
        "confidence_flag": "MEDIUM",
    },
    {
        "candidate_id": "DR-LANG-EU-06", "language": "it",
        "name": "UNI EN ISO 12944-9:2018 -- Pitture e vernici, Protezione dalla corrosione di strutture in acciaio mediante verniciatura, offshore",
        "native_citation": EV_IT01_QUOTE,
        "native_citation_romanization": None,
        "url": "https://store.uni.com/uni-en-iso-12944-9-2018",
        "custodian": "UNI (Ente Italiano di Normazione) / ISO (direct EN/UNI adoption of ISO 12944)",
        "rediscovers": None,
        "coverage": "Defines coating-product requirements for corrosion protection of offshore structures exposed to marine atmosphere, seawater immersion, and brackish water; CX (offshore) / Im4 (immersion) corrosivity categories per ISO 12944-2; in force since 2018-07-26.",
        "gap_match_class": "named_module_gap", "meets_minimum_n_and_measurement_class": "unknown",
        "data_class": "compilation_of_primary",
        "data_class_note": "Published national/European standard document (direct UNI-EN adoption of the ISO standard), not a raw-measurement dataset -- same category-mismatch disclosure as DR-LANG-EU-01/02 and the de/fr DIN/NF precedent.",
        "standard_and_uncertainty_disclosed": "published_standard_and_uncertainty",
        "rights_tier": "paywalled_unclear_bulk_rights", "redundancy_class": "partial_overlap_adds_coverage",
        "translation_confidence": "native_script_verified_high",
        "translation_confidence_note": "Italian standard scope text directly quoted from the it WebSearch/UNI-store evidence this fire.",
        "integrity_risks": [], "reachability": "reachable_index_only_dataset_unclear",
        "serves": {"module_gaps": ["amphora-ip-fto-guard", "amphora-owk-adhesion"], "recipe_elements": ["marine-coating-system-standard-mapping"]},
        "standard_mapping": {
            "published_standard": "UNI EN ISO 12944 (Parti 1-9), esp. Parte 9 (offshore)",
            "astm_iso_equiv": "UNI EN ISO 12944 IS the direct Italian/European-language adoption of ISO 12944 itself -- a further independent language-community confirmation (after de/fr/nl) -- no specific ASTM single-standard equivalent confirmed this fire.",
            "comparability_rating": "identical_to_iso_by_direct_adoption_astm_unconfirmed",
        },
        "license_evidence_quote": EV_IT01_QUOTE,
        "confidence_flag": "MEDIUM",
    },
    {
        "candidate_id": "DR-LANG-EU-07", "language": "it",
        "name": "UNI EN ISO 9227:2017 -- Prove di corrosione in atmosfere artificiali, Prove alla nebbia salina",
        "native_citation": EV_IT02_TITLE,
        "native_citation_romanization": None,
        "url": "https://conto.uni.com/uni-en-iso-9227-2017",
        "custodian": "UNI / ISO (direct EN/UNI adoption of ISO 9227)",
        "rediscovers": None,
        "coverage": "Specifies equipment, reagents and procedure for NSS/AASS/CASS salt-spray tests to evaluate corrosion resistance of metallic materials with or without permanent/temporary anticorrosive protection; used to detect discontinuities (pores, defects) in organic/inorganic coatings.",
        "gap_match_class": "named_module_gap", "meets_minimum_n_and_measurement_class": "unknown",
        "data_class": "compilation_of_primary",
        "data_class_note": "Published national/European standard document (direct UNI-EN adoption of ISO 9227), not a raw-measurement dataset -- same category-mismatch disclosure as DR-LANG-EU-06.",
        "standard_and_uncertainty_disclosed": "published_standard_and_uncertainty",
        "rights_tier": "paywalled_unclear_bulk_rights", "redundancy_class": "partial_overlap_adds_coverage",
        "translation_confidence": "native_script_verified_high",
        "translation_confidence_note": "Italian standard scope text directly quoted from the it WebSearch evidence this fire.",
        "integrity_risks": [], "reachability": "reachable_index_only_dataset_unclear",
        "serves": {"module_gaps": ["amphora-public-corrosion-benchmark"], "recipe_elements": ["salt-spray-standard-mapping"]},
        "standard_mapping": {
            "published_standard": "UNI EN ISO 9227",
            "astm_iso_equiv": "UNI EN ISO 9227 IS the direct Italian/European adoption of ISO 9227 -- a further independent language-community confirmation (after ja/de/ru/fr/nl) that ISO 9227 is the de facto global salt-spray baseline underlying the portfolio's ASTM B117 usage.",
            "comparability_rating": "identical_to_iso_by_direct_adoption_astm_unconfirmed",
        },
        "license_evidence_quote": EV_IT02_SCOPE,
        "confidence_flag": "MEDIUM",
    },
    {
        "candidate_id": "DR-LANG-EU-08", "language": "it",
        "name": "AIM (Associazione Italiana di Metallurgia) -- Corrosione e Rivestimenti study centers, national professional metallurgy society",
        "native_citation": EV_IT03_QUOTE,
        "native_citation_romanization": None,
        "url": "https://www.aimnet.it/gnc-25.shtml",
        "custodian": "AIM (Associazione Italiana di Metallurgia)",
        "rediscovers": None,
        "coverage": "AIM organizes the Giornate Nazionali sulla Corrosione e Protezione conference and publishes La Metallurgia Italiana (est. 1909); has dedicated Corrosione and Rivestimenti e Tribologia study centers; a membership/conference/publication body, not a dataset.",
        "gap_match_class": "off_scope", "meets_minimum_n_and_measurement_class": "no",
        "data_class": "extracted_or_estimated",
        "data_class_note": "AIM is a paid-membership professional metallurgy society and conference/journal publisher, not itself a dataset -- mirrors the fr fire's CEFRACOR REJECTED-off_scope precedent exactly (same institutional class: national corrosion-protection professional society).",
        "standard_and_uncertainty_disclosed": "neither_stated",
        "rights_tier": "open_with_attribution", "redundancy_class": "mostly_redundant",
        "translation_confidence": "native_script_verified_high",
        "translation_confidence_note": "Quote directly WebFetched from AIM's own it-language conference-invitation page this fire.",
        "integrity_risks": [], "reachability": "reachable_direct_open_download",
        "serves": {"module_gaps": [], "recipe_elements": []},
        "standard_mapping": {"published_standard": "N/A -- professional society, not a standard or dataset.", "astm_iso_equiv": "N/A", "comparability_rating": "not_applicable_institute"},
        "license_evidence_quote": EV_IT03_QUOTE,
        "confidence_flag": "LOW",
    },
    {
        "candidate_id": "DR-LANG-EU-09", "language": "it",
        "name": "RINA -- ship classification society and industrial corrosion-engineering consulting services",
        "native_citation": EV_IT04_QUOTE,
        "native_citation_romanization": None,
        "url": "https://www.rina.org/it/corrosion",
        "custodian": "RINA S.p.A.",
        "rediscovers": None,
        "coverage": "RINA addresses corrosion issues affecting design/construction of industrial plants and machinery, including material selection, protective coatings, inhibitors, and cathodic protection -- a paid classification-society consulting service, not a dataset publisher.",
        "gap_match_class": "off_scope", "meets_minimum_n_and_measurement_class": "no",
        "data_class": "extracted_or_estimated",
        "data_class_note": "RINA is a paid classification-society/consulting service, not a dataset publisher -- mirrors DR-LANG-EU-08's AIM REJECTED-off_scope pattern.",
        "standard_and_uncertainty_disclosed": "neither_stated",
        "rights_tier": "paywalled_unclear_bulk_rights", "redundancy_class": "mostly_redundant",
        "translation_confidence": "native_script_verified_high",
        "translation_confidence_note": "Quote directly from RINA's own it-language corrosion-services page, found via it WebSearch this fire.",
        "integrity_risks": [], "reachability": "reachable_direct_open_download",
        "serves": {"module_gaps": [], "recipe_elements": []},
        "standard_mapping": {"published_standard": "N/A -- consulting service, not a standard or dataset.", "astm_iso_equiv": "N/A", "comparability_rating": "not_applicable_institute"},
        "license_evidence_quote": EV_IT04_QUOTE,
        "confidence_flag": "LOW",
    },
    {
        "candidate_id": "DR-LANG-EU-10", "language": "it",
        "name": "CNR-ICMATE -- Laboratorio Marino Politematico MARECO, marine-atmosphere corrosion exposure site, Bonassola (La Spezia)",
        "native_citation": EV_IT05_MARECO,
        "native_citation_romanization": None,
        "url": "https://www.ias.cnr.it/macrotematiche-di-ricerca/gruppi-di-ricerca/linee-di-ricerca/corrosione-materiali-cormat/",
        "custodian": "CNR-ICMATE (Consiglio Nazionale delle Ricerche -- Istituto di Chimica della Materia Condensata e di Tecnologie per l'Energia), CORMAT research line",
        "rediscovers": None,
        "coverage": "Long-term marine-atmosphere corrosion exposure trial: 70+ samples of steel, stainless steel, galvanized and weathering steel on two fiberglass racks at a rock-wall coastal site near Bonassola; parallel comparison against an urban Milano exposure site; both listed in the EFC (European Federation of Corrosion) Exposure Site Catalogue.",
        "gap_match_class": "named_module_gap", "meets_minimum_n_and_measurement_class": "unknown",
        "data_class": "primary_experimental",
        "standard_and_uncertainty_disclosed": "standard_named_no_uncertainty",
        "rights_tier": "paywalled_unclear_bulk_rights", "redundancy_class": "partial_overlap_adds_coverage",
        "translation_confidence": "native_script_verified_high",
        "translation_confidence_note": "Both Italian quotes were returned directly by a native-it WebSearch call (query 20); a follow-up WebFetch of the CORMAT page itself did NOT reproduce this specific passage (the fetched page's extracted text omitted the MARECO/Bonassola paragraph) -- disclosed as an evidence-quality gap (data-access/license terms for this exposure programme's own dataset remain unconfirmed this fire), not silently treated as independently re-verified.",
        "integrity_risks": ["digitization_quality_concern"], "reachability": "reachable_index_only_dataset_unclear",
        "serves": {"module_gaps": ["amphora-public-corrosion-benchmark", "amphora-barrier-corrosion-score"], "recipe_elements": []},
        "standard_mapping": {
            "published_standard": "N/A -- primary field-exposure research programme, not itself a published standard, though referenced against the EFC Exposure Site Catalogue methodology class.",
            "astm_iso_equiv": "Method-class-comparable to ASTM G50 / ISO 9223 atmospheric-exposure corrosion-classification practice (not independently confirmed by direct citation this fire).",
            "comparability_rating": "adjacent_method_class_unconfirmed_citation",
        },
        "license_evidence_quote": EV_IT05_EFC,
        "confidence_flag": "LOW",
    },
    {
        "candidate_id": "DR-LANG-EU-11", "language": "it",
        "name": "Basso, G. (2022/23). \"Materiali compositi da resine epossidiche derivate da biomasse e filler cellulosici\" -- Politecnico di Torino WebThesis (Master's thesis, Ingegneria Chimica e dei Processi Sostenibili)",
        "native_citation": EV_IT06_TITLE,
        "native_citation_romanization": None,
        "url": "https://webthesis.biblio.polito.it/24890/",
        "custodian": "Politecnico di Torino -- WebThesis institutional repository",
        "rediscovers": None,
        "coverage": "Development of epoxy composite materials using a biobased resin derived from cardanol (extracted from cashew nutshell), thermally cured with amine hardeners and reinforced with microcrystalline cellulose powder or cellulose microfibrils; curing process evaluated via spectroscopic analysis monitoring functional-group conversion vs. time/temperature/epoxide:amine molar ratio; polymeric matrix and composites characterized via mechanical, thermal and thermogravimetric testing.",
        "gap_match_class": "named_module_gap", "meets_minimum_n_and_measurement_class": "unknown",
        "data_class": "primary_experimental",
        "data_class_note": "Amine-cured epoxy-amine cure-CONVERSION study (spectroscopic tracking of epoxide:amine functional-group conversion vs. time/temperature/ratio), not a DSC/Kissinger-class kinetic-parameter study specifically -- disclosed: this is the closest open, CC-licensed, native-it cure-behavior primary source found this fire, but the resin system is biobased/cardanol rather than DGEBA, and the method is conversion-tracking rather than DSC activation-energy extraction. Directly relevant methodologically, not a drop-in DGEBA/amine Kissinger-anchor replacement.",
        "standard_and_uncertainty_disclosed": "neither_stated",
        "rights_tier": "open_with_attribution", "redundancy_class": "no_known_portfolio_overlap",
        "rights_note": "CC BY-NC-ND: open, freely downloadable (1MB PDF), attribution required, NonCommercial and NoDerivatives clauses apply -- same license-family caveat class as the de fire's TU Darmstadt CC BY-NC-ND RECOMMENDED precedent (DR-LANG-DE-06).",
        "translation_confidence": "native_script_verified_high",
        "translation_confidence_note": "Italian thesis title and abstract summary directly confirmed via it WebSearch and WebFetch this fire.",
        "integrity_risks": [], "reachability": "reachable_direct_open_download",
        "serves": {"module_gaps": ["amphora-cure-kinetics", "amphora-cure-potlife-gate"], "recipe_elements": ["amine-cure-conversion-tracking"]},
        "standard_mapping": {"published_standard": "N/A -- primary thesis research, not a published standard.", "astm_iso_equiv": "N/A", "comparability_rating": "not_applicable_primary_literature"},
        "license_evidence_quote": EV_IT06_LICENSE,
        "confidence_flag": "MEDIUM",
    },
]

HUMAN_ACTIONS = {
    "DR-LANG-EU-01": "human purchases official NEN-EN-ISO 12944 (all parts, esp. deel 9) full text via NEN Connect and performs a clause-by-clause ASTM/SSPC comparability diff, since the portfolio's own baseline is ASTM-referenced.",
    "DR-LANG-EU-02": "human purchases official NEN-EN-ISO 9227 full text via NEN (confirmed paid-purchase model this fire) and performs a clause-by-clause ASTM B117 diff -- same action class as the de/ja/ru/fr fires' DIN/JIS/GOST/NF ISO-9227-derived standards.",
    "DR-LANG-EU-03": "no dataset action possible -- TNO/NCC is a paid contract-research and testing institute, not a dataset; a human seeking domain expertise could commission a testing engagement.",
    "DR-LANG-EU-04": "no dataset action possible -- Corrosielabs is a paid contract-testing platform with explicit client-confidentiality guarantees, not a dataset.",
    "DR-LANG-EU-05": "human requests explicit reuse permission from the authors/Elsevier or checks the publisher's own version-of-record for a CC license, since the TU Delft repository record itself states no CC license despite the embargo having expired.",
    "DR-LANG-EU-06": "human purchases official UNI EN ISO 12944 (all parts, esp. parte 9) full text via the UNI store and performs a clause-by-clause ASTM/SSPC comparability diff.",
    "DR-LANG-EU-07": "human purchases official UNI EN ISO 9227 full text via the UNI store and performs a clause-by-clause ASTM B117 diff.",
    "DR-LANG-EU-08": "no dataset action possible -- AIM is a paid-membership professional society/conference/journal body, not a dataset; a human seeking domain expertise could join or attend the Giornate Nazionali sulla Corrosione e Protezione.",
    "DR-LANG-EU-09": "no dataset action possible -- RINA is a paid classification-society consulting service, not a dataset.",
    "DR-LANG-EU-10": "human contacts CNR-ICMATE directly (or checks the EFC Exposure Site Catalogue's own record for this Bonassola site) to confirm whether the MARECO programme's raw exposure-trial measurements are published anywhere, since this fire's own direct CORMAT-page fetch did not reproduce the programme description found via WebSearch.",
    "DR-LANG-EU-11": "human reads the full Basso (2022/23) WebThesis PDF to extract the quantitative epoxide:amine conversion-vs-time/temperature data tables for potential use as an amine-cure-conversion-tracking reference point, respecting the CC BY-NC-ND NonCommercial/NoDerivatives terms.",
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
    disp_entries.append(entry)

ranked = sorted(disp_entries, key=lambda e: (-e["rubric_overall_score"], e["candidate_id"]))
for i, e in enumerate(ranked, start=1):
    e["rank"] = i

DL_PATH = LEDGERS / "disposition-ledger.v1.jsonl"
dl_before = DL_PATH.read_bytes() if DL_PATH.exists() else b""
dl_prior_prefix_sha = sha(dl_before)
dl_prior_lines = dl_before.decode("utf-8").splitlines() if dl_before else []
dl_prior_line_count = len(dl_prior_lines)

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
# 3. dataset-ledger.v1.jsonl -- append EU-11 (Basso thesis, clears RECOMMENDED)
# ---------------------------------------------------------------------------
DSL_PATH = LEDGERS / "dataset-ledger.v1.jsonl"
dsl_before = DSL_PATH.read_bytes() if DSL_PATH.exists() else b""
dsl_prior_prefix_sha = sha(dsl_before)
dsl_prior_lines = dsl_before.decode("utf-8").splitlines() if dsl_before else []
dsl_prior_line_count = len(dsl_prior_lines)

eu11 = next(e for e in disp_entries if e["candidate_id"] == "DR-LANG-EU-11")
assert eu11["disposition"]["verdict"] == "RECOMMENDED", "expected DR-LANG-EU-11 to clear RECOMMENDED"

dataset_ledger_entry = {
    "schema": "amphora.dataset-recon.dataset-ledger.v1",
    "entry_type": "dataset_ledger_entry",
    "ledger_entry_id": "DR-LANG-EU-DSL-01",
    "candidate_id": "DR-LANG-EU-11",
    "run_id": RUN_ID,
    "fire_id": FIRE_ID,
    "date": DATE,
    "framing": "AUDIT-ONLY",
    "language": "it",
    "name": "Basso, G. (2022/23). \"Materiali compositi da resine epossidiche derivate da biomasse e filler cellulosici\" -- Politecnico di Torino WebThesis",
    "native_citation": EV_IT06_TITLE,
    "url_or_doi": "https://webthesis.biblio.polito.it/24890/",
    "publisher_custodian": "Politecnico di Torino -- WebThesis institutional repository",
    "license_as_published": f"{EV_IT06_LICENSE} -- open access, freely downloadable (1MB PDF), attribution required, NonCommercial and NoDerivatives clauses apply.",
    "standard_mapping": {
        "published_standard": "N/A -- primary thesis research, not a published standard.",
        "astm_iso_equiv": "N/A",
        "comparability_rating": "not_applicable_primary_literature",
    },
    "estimated_records_and_coverage": (
        "Single Master's-thesis primary study (2022/23): biobased cardanol-derived epoxy resin, "
        "amine-hardener thermal cure, cellulose micro/nanofiller reinforcement. Cure evaluated via "
        "spectroscopic functional-group-conversion tracking vs. time/temperature/epoxide:amine "
        "molar ratio (not DSC/Kissinger activation-energy extraction -- disclosed). Mechanical, "
        "thermal and thermogravimetric characterization of the resulting composites also reported. "
        "IMPORTANT: this is a biobased/cardanol system, not the portfolio's core DGEBA+amine "
        "chemistry -- methodologically adjacent, not a drop-in Kissinger-anchor replacement."
    ),
    "module_gaps": ["amphora-cure-kinetics", "amphora-cure-potlife-gate"],
    "recipe_elements": ["amine-cure-conversion-tracking"],
    "integrity_risks": [],
    "translation_confidence": "native_script_verified_high",
    "next_human_action": HUMAN_ACTIONS["DR-LANG-EU-11"],
    "confidence_flag": "MEDIUM",
    "coverage": eu11["coverage"],
    "rank": 1,
    "serves": {"module_gaps": ["amphora-cure-kinetics", "amphora-cure-potlife-gate"], "recipe_elements": ["amine-cure-conversion-tracking"]},
    "disposition": {"verdict": "RECOMMENDED", "reason": eu11["disposition"]["reason"]},
    "snapshot_date": DATE,
    "rubric_overall_score": eu11["rubric_overall_score"],
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
# 4. coverage-map.v1.json -- merge (preserve all prior gaps, add nl+it gaps)
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


eu_gaps = [
    {
        "gap_id": "corrosion-database-nl",
        "module_gaps": ["amphora-public-corrosion-benchmark", "amphora-barrier-corrosion-score"],
        "best_recommended": best_recommended_for(["DR-LANG-EU-03", "DR-LANG-EU-04", "DR-LANG-EU-05"]),
        "best_conditional": best_for(["DR-LANG-EU-03", "DR-LANG-EU-04", "DR-LANG-EU-05"]),
        "commissioned_measurement_candidate": None,
        "note": "TU Delft's Liu et al. 2023 self-healing/corrosion-sensing MOF-coating record (DR-LANG-EU-05) is the best gap-fit find; TNO/NCC (EU-03) and Corrosielabs (EU-04) are both REJECTED off_scope -- contract-research institutes, not dataset publishers.",
    },
    {
        "gap_id": "marine-coating-nen-standard-mapping",
        "module_gaps": ["amphora-ip-fto-guard", "amphora-owk-adhesion"],
        "best_recommended": None,
        "best_conditional": best_for(["DR-LANG-EU-01"]),
        "commissioned_measurement_candidate": None,
        "note": "NEN-EN-ISO 12944 (esp. deel 9, offshore) is the general structural-steel coating-system standard, directly and identically adopted from ISO -- a further independent language-community confirmation (after de's DIN, fr's NF) that ISO 12944 is the underlying global standard. No Dutch-specific ship-hull antifouling standard number was found despite an explicit search -- see ship-hull-antifouling-standard-mapping-nl empty result.",
    },
    {
        "gap_id": "salt-spray-standard-mapping-nl",
        "module_gaps": ["amphora-public-corrosion-benchmark"],
        "best_recommended": None,
        "best_conditional": best_for(["DR-LANG-EU-02"]),
        "commissioned_measurement_candidate": None,
        "note": "NEN-EN-ISO 9227 confirmed as the direct Dutch/European adoption of ISO 9227 (paid-purchase model directly confirmed via NEN WebSearch). Further independent language-community confirmation (after ja/de/ru/fr) that ISO 9227 is the de facto global salt-spray baseline underlying the portfolio's ASTM B117 usage.",
    },
    {
        "gap_id": "nl-eew-testdata-annex",
        "module_gaps": ["amphora-molecule-property"],
        "best_recommended": None,
        "best_conditional": None,
        "commissioned_measurement_candidate": (
            "No open NEN-EN-ISO 3001 (epoxy equivalent weight) test-data annex was found -- an "
            "honest empty result for the directive's 'NEN annexes' scope element, per rule 7. "
            "Standard method confirmed mapped to ISO 3001:1999/1997 (direct NEN-EN adoption, "
            "title-and-scope level only) -- same convergence pattern as the de/ja/ru/fr fires' "
            "identical DIN/JIS/GOST/NF EN ISO 3001 findings. Note: the portfolio already computes "
            "EEW/AHEW internally via its own ChEBI+RDKit pipeline (amphora-molecule-property "
            "EEW/AHEW verification result, err 0.03) -- this nl finding is a standard-citation/"
            "mapping enrichment only, not a data gap requiring commissioning."
        ),
        "note": "Empty result, honestly reported per directive rule 7 ('An empty result for a gap is a valid, reportable answer').",
    },
    {
        "gap_id": "ship-hull-antifouling-standard-mapping-nl",
        "module_gaps": ["amphora-ip-fto-guard", "amphora-owk-adhesion"],
        "best_recommended": None,
        "best_conditional": None,
        "commissioned_measurement_candidate": None,
        "note": "No Dutch/NEN ship-hull-specific antifouling/anticorrosive paint standard number was found, only the general NEN standards committee 'Verfwaren, metallieke en anorganische deklagen en corrosie' and the general NEN-EN-ISO 12944 (already captured above) -- an honest negative result mirroring the identical de/ja/fr findings for this same scope element across independent language communities.",
    },
    {
        "gap_id": "cure-kinetics-nl",
        "module_gaps": ["amphora-cure-kinetics", "amphora-cure-potlife-gate"],
        "best_recommended": None,
        "best_conditional": None,
        "commissioned_measurement_candidate": None,
        "note": "No dedicated Dutch-language amine-cure-kinetics dataset or thesis was found this fire despite a genuine native-nl query (surfaced only international English-language DSC/Kissinger literature, not a Dutch primary source) and an English TU-Delft-site-restricted follow-up (surfaced an unrelated bridge-design thesis, then the off-topic self-healing-coating record now filed under corrosion-database-nl instead). HONEST EMPTY RESULT, disclosed as a genuine miss, not padded.",
    },
    {
        "gap_id": "nl-repository-infrastructure-succession",
        "module_gaps": [],
        "best_recommended": None,
        "best_conditional": None,
        "commissioned_measurement_candidate": None,
        "note": (
            f"Repository-class finding: NARCIS (the former Dutch national research-information "
            f"portal) was decommissioned 2023-07-03, superseded by 'The Netherlands Research "
            f"Portal'. DANS EASY (the former Dutch national research-DATA archive) was "
            f"decommissioned 2024-12-02, superseded by domain-specific DANS Data Stations "
            f"(https://phys-techsciences.datastations.nl/ for materials/physical science). A "
            f"direct browse of the Physical & Technical Sciences Data Station's homepage found NO "
            f"corrosion/coating/epoxy dataset among its visible listing (all examples were "
            f"climate/geography/topographic) -- an honest empty result, though the filtered "
            f"?q=search endpoint itself 404'd this fire (access-path limitation, disclosed, not "
            f"conflated with a confirmed zero-result search)."
        ),
    },
    {
        "gap_id": "corrosion-database-it",
        "module_gaps": ["amphora-public-corrosion-benchmark", "amphora-barrier-corrosion-score"],
        "best_recommended": best_recommended_for(["DR-LANG-EU-08", "DR-LANG-EU-09", "DR-LANG-EU-10"]),
        "best_conditional": best_for(["DR-LANG-EU-08", "DR-LANG-EU-09", "DR-LANG-EU-10"]),
        "commissioned_measurement_candidate": None,
        "note": "CNR-ICMATE's own MARECO marine-atmosphere exposure programme at Bonassola (DR-LANG-EU-10, part of the EFC Exposure Site Catalogue) independently rediscovered and evaluated; data-access/license terms unconfirmed (CORMAT-page re-fetch did not reproduce the finding). AIM (EU-08) and RINA (EU-09) both REJECTED off_scope -- neither is itself a dataset (a paid professional society and a paid classification-society consultancy, respectively).",
    },
    {
        "gap_id": "marine-coating-uni-standard-mapping",
        "module_gaps": ["amphora-ip-fto-guard", "amphora-owk-adhesion"],
        "best_recommended": None,
        "best_conditional": best_for(["DR-LANG-EU-06"]),
        "commissioned_measurement_candidate": None,
        "note": "UNI EN ISO 12944 (esp. parte 9, offshore) is the general structural-steel coating-system standard, directly and identically adopted from ISO -- a further independent language-community confirmation. No Italian-specific ship-hull antifouling standard number was found despite an explicit search -- see ship-hull-antifouling-standard-mapping-it empty result.",
    },
    {
        "gap_id": "salt-spray-standard-mapping-it",
        "module_gaps": ["amphora-public-corrosion-benchmark"],
        "best_recommended": None,
        "best_conditional": best_for(["DR-LANG-EU-07"]),
        "commissioned_measurement_candidate": None,
        "note": "UNI EN ISO 9227 confirmed as the direct Italian/European adoption of ISO 9227. Further independent language-community confirmation that ISO 9227 is the de facto global salt-spray baseline underlying the portfolio's ASTM B117 usage.",
    },
    {
        "gap_id": "it-eew-testdata-annex",
        "module_gaps": ["amphora-molecule-property"],
        "best_recommended": None,
        "best_conditional": None,
        "commissioned_measurement_candidate": (
            "No open UNI EN ISO 3001 (epoxy equivalent weight) test-data annex was found -- an "
            "honest empty result for the directive's 'UNI annexes' scope element, per rule 7. "
            "Standard method confirmed mapped to ISO 3001:1999 (direct UNI-EN adoption, "
            "title-and-scope-and-method-principle level -- the it search even surfaced the exact "
            "TEABr/perchloric-acid titration principle text). Note: the portfolio already computes "
            "EEW/AHEW internally via its own ChEBI+RDKit pipeline (amphora-molecule-property "
            "EEW/AHEW verification result, err 0.03) -- this it finding is a standard-citation/"
            "mapping enrichment only, not a data gap requiring commissioning."
        ),
        "note": "Empty result, honestly reported per directive rule 7 ('An empty result for a gap is a valid, reportable answer').",
    },
    {
        "gap_id": "ship-hull-antifouling-standard-mapping-it",
        "module_gaps": ["amphora-ip-fto-guard", "amphora-owk-adhesion"],
        "best_recommended": None,
        "best_conditional": None,
        "commissioned_measurement_candidate": None,
        "note": "No Italian/UNI ship-hull-specific antifouling/anticorrosive paint standard number was found, only general antifouling-application practitioner pages -- an honest negative result mirroring the identical nl/de/ja/fr findings for this same scope element across independent language communities.",
    },
    {
        "gap_id": "cure-kinetics-it",
        "module_gaps": ["amphora-cure-kinetics", "amphora-cure-potlife-gate"],
        "best_recommended": best_recommended_for(["DR-LANG-EU-11"]),
        "best_conditional": None,
        "commissioned_measurement_candidate": None,
        "note": "Basso (2022/23) Politecnico di Torino WebThesis (DR-LANG-EU-11, CC BY-NC-ND, open access) is the first RECOMMENDED-grade candidate this fire -- a biobased cardanol epoxy-amine cure-conversion study, methodologically adjacent (not DGEBA, not DSC/Kissinger) but directly relevant and openly licensed, mirroring the de fire's TU Darmstadt and ru fire's CyberLeninka RECOMMENDED precedents.",
    },
]

cm_after = copy.deepcopy(cm_before)
cm_after["gaps"] = cm_before.get("gaps", []) + eu_gaps
cm_after["fire_id"] = FIRE_ID
cm_after["run_id"] = RUN_ID
cm_after["snapshot_date"] = DATE
cm_after["scope_note"] = cm_before.get("scope_note", "") + " + nl (Dutch) + it (Italian), DR-LANG-EU fire."
cm_after["nl_empty_result_gap_note"] = "nl-eew-testdata-annex, ship-hull-antifouling-standard-mapping-nl, and cure-kinetics-nl are genuine empty results this fire (see gaps[] entries) -- honestly reported, not padded, and not silently converted into fabricated candidates."
cm_after["nl_no_empty_result_gap_this_fire"] = False
cm_after["it_empty_result_gap_note"] = "it-eew-testdata-annex and ship-hull-antifouling-standard-mapping-it are genuine empty results this fire (see gaps[] entries) -- honestly reported, not padded, and not silently converted into fabricated candidates."
cm_after["it_no_empty_result_gap_this_fire"] = False
cm_after_bytes = canon(cm_after)
cm_after_sha = sha(cm_after_bytes)

# ---------------------------------------------------------------------------
# 5. Independent checker: 5-limb refutation criterion (Latin-script
# adaptation, bundling TWO language communities: nl and it)
# ---------------------------------------------------------------------------
NL_MARKER_WORDS = [
    "epoxy", "epoxyhars", "amine", "uitharder", "uitharding", "uithardingskinetiek",
    "corrosie", "coating", "verf", "verfsystemen", "proef", "proeven", "zoutnevel",
    "zout", "norm", "scheepshuid", "antifouling", "corrosiewerend", "kinetiek",
    "dataset", "onderzoeksdata", "hars", "primer", "zeewater", "scheepvaart",
    "staalconstructies", "testdata", "titratie", "equivalent", "nederlandse",
    "onderzoek", "beproeving", "corrosiebeproeving", "deklagen",
]
IT_MARKER_WORDS = [
    "epossidic", "epossidica", "ammina", "indurente", "indurimento", "cinetica",
    "corrosione", "rivestimento", "rivestimenti", "vernice", "verniciatura",
    "prove", "nebbia", "salina", "norma", "scafo", "antivegetativa",
    "antiruggine", "resina", "cura", "marina", "acciaio", "strutture",
    "titolazione", "equivalente", "dati", "banca", "italia", "protettiv",
]


def has_marker(s, words):
    low = (s or "").lower()
    return any(w in low for w in words)


def check(disp_lines, sr_lines_all, previously_supplied_ids):
    """disp_lines: list of dicts (manifest + dispositions). sr_lines_all: list of
    search-record line dicts (the full ledger, all fires). Returns diagnostic
    dict, never raises."""
    violations = []
    dispositions = [d for d in disp_lines if d.get("entry_type") == "candidate_disposition"]

    def all_evidence_text():
        parts = []
        for line in sr_lines_all:
            for q in line.get("queries", []):
                for k in ("query", "query_gloss_en", "purpose", "result_note", "result_summary",
                          "result_evidence_quote", "result", "sample_urls", "url"):
                    v = q.get(k)
                    if isinstance(v, list):
                        parts.extend(str(x) for x in v)
                    elif v:
                        parts.append(str(v))
        return "\n".join(parts)

    text = all_evidence_text()

    # Rule 1: citation_has_recorded_query_and_result
    for d in dispositions:
        url = d.get("url", "")
        if url and url not in text:
            violations.append({"rule": "citation_has_recorded_query_and_result", "candidate_id": d["candidate_id"],
                                "reason": f"{d['candidate_id']}: url {url} does not appear in any recorded search-record query/result this fire"})

    # Rule 2: native_query_not_literal_translation -- nl/it query must contain a
    # language-appropriate marker word AND must not be byte-identical (case-
    # insensitive) to its own gloss.
    for line in sr_lines_all:
        for q in line.get("queries", []):
            lang = q.get("language")
            if lang not in ("nl", "it") or "query" not in q or q.get("tool") != "WebSearch":
                continue
            qtext = q["query"]
            gloss = q.get("query_gloss_en", "")
            markers = NL_MARKER_WORDS if lang == "nl" else IT_MARKER_WORDS
            if (not has_marker(qtext, markers)) or (qtext.strip().lower() == gloss.strip().lower()):
                violations.append({"rule": "native_query_not_literal_translation", "candidate_id": None,
                                    "reason": f"{lang} query field is a literal English translation or contains no {lang} marker vocabulary: '{qtext}'"})

    # Rule 3: license_text_matches_live_evidence
    for d in dispositions:
        quote = d.get("license_evidence_quote", "")
        if quote and quote not in text:
            violations.append({"rule": "license_text_matches_live_evidence", "candidate_id": d["candidate_id"],
                                "reason": f"{d['candidate_id']}: license_evidence_quote does not appear verbatim in this fire's recorded search-record evidence text"})

    # Rule 4: native_citation_verbatim_in_evidence -- every nl/it native_citation
    # must appear verbatim (byte-for-byte substring) in the recorded evidence text.
    for d in dispositions:
        if d.get("language") in ("nl", "it"):
            nc = d.get("native_citation", "")
            if nc and nc not in text:
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


PREVIOUSLY_SUPPLIED_NL_IT = []  # none found this fire -- absence explained in intake_manifest

sr_all_lines = list(sr_prior_lines_parsed) + [search_record_line_obj]
dl_this_fire = dl_lines  # manifest + 11 dispositions, this fire only

runA = check(dl_this_fire, sr_all_lines, PREVIOUSLY_SUPPLIED_NL_IT)
runB = check(dl_this_fire, sr_all_lines, PREVIOUSLY_SUPPLIED_NL_IT)
runA_bytes = canon(runA)
runB_bytes = canon(runB)
(WORK / "diagnostic.runA.json").write_bytes(runA_bytes)
(WORK / "diagnostic.runB.json").write_bytes(runB_bytes)
assert sha(runA_bytes) == sha(runB_bytes), "two-replay gate FAILED on real deliverable"
assert runA["refutation_criterion_fired"] is False, f"REAL deliverable fired the refutation criterion: {runA['violations']}"

# ---------------------------------------------------------------------------
# 6. Positive control: 6 planted-defect mutants (rule1, rule2-nl, rule2-it,
# rule3, rule4, rule5)
# ---------------------------------------------------------------------------
mutants_out = {}

# mutant 1: missing_recorded_query
sr_mut1 = copy.deepcopy(sr_all_lines)
target_url = "https://webthesis.biblio.polito.it/24890/"
for line in sr_mut1:
    for q in line.get("queries", []):
        for k in ("query", "result_note", "result_summary", "result_evidence_quote", "result", "sample_urls", "url"):
            v = q.get(k)
            if isinstance(v, list):
                q[k] = [x for x in v if target_url not in str(x)]
            elif isinstance(v, str) and target_url in v:
                q[k] = v.replace(target_url, "REDACTED")
r1 = check(dl_this_fire, sr_mut1, PREVIOUSLY_SUPPLIED_NL_IT)
mutants_out["missing_recorded_query"] = {
    "expected_rule": "citation_has_recorded_query_and_result",
    "how_planted": f"Scrubbed every occurrence of DR-LANG-EU-11's url ({target_url}) from a copy of this fire's search-record queries/results.",
    "expected_rule_fired": True,
    "refutation_criterion_fired": r1["refutation_criterion_fired"],
    "violations": r1["violations"],
}

# mutant 2a: literal_english_translation_query (nl)
sr_mut2a = copy.deepcopy(sr_all_lines)
for line in sr_mut2a:
    for q in line.get("queries", []):
        if q.get("language") == "nl" and q.get("query", "").startswith("epoxyhars amine uitharder"):
            q["query"] = "epoxy resin amine hardener cure kinetics DSC dataset"
r2a = check(dl_this_fire, sr_mut2a, PREVIOUSLY_SUPPLIED_NL_IT)
mutants_out["literal_english_translation_query_nl"] = {
    "expected_rule": "native_query_not_literal_translation",
    "how_planted": "Replaced the native nl query string 'epoxyhars amine uitharder uithardingskinetiek DSC dataset' with its literal English gloss, while leaving language:'nl' unchanged.",
    "expected_rule_fired": True,
    "refutation_criterion_fired": r2a["refutation_criterion_fired"],
    "violations": r2a["violations"],
}

# mutant 2b: literal_english_translation_query (it)
sr_mut2b = copy.deepcopy(sr_all_lines)
for line in sr_mut2b:
    for q in line.get("queries", []):
        if q.get("language") == "it" and q.get("query", "").startswith("resina epossidica ammina indurente"):
            q["query"] = "epoxy resin amine hardener cure kinetics dataset"
r2b = check(dl_this_fire, sr_mut2b, PREVIOUSLY_SUPPLIED_NL_IT)
mutants_out["literal_english_translation_query_it"] = {
    "expected_rule": "native_query_not_literal_translation",
    "how_planted": "Replaced the native it query string 'resina epossidica ammina indurente cinetica di indurimento set di dati' with its literal English gloss, while leaving language:'it' unchanged.",
    "expected_rule_fired": True,
    "refutation_criterion_fired": r2b["refutation_criterion_fired"],
    "violations": r2b["violations"],
}

# mutant 3: license_text_diverges
dl_mut3 = copy.deepcopy(dl_this_fire)
for d in dl_mut3:
    if d.get("candidate_id") == "DR-LANG-EU-11":
        d["license_evidence_quote"] = "Questa tesi e disponibile in accesso pienamente libero, senza alcuna restrizione di licenza o attribuzione."
r3 = check(dl_mut3, sr_all_lines, PREVIOUSLY_SUPPLIED_NL_IT)
mutants_out["license_text_diverges"] = {
    "expected_rule": "license_text_matches_live_evidence",
    "how_planted": "Overwrote DR-LANG-EU-11's license_evidence_quote with a fabricated 'fully open, no restriction' claim contradicting the recorded CC BY-NC-ND WebFetch evidence.",
    "expected_rule_fired": True,
    "refutation_criterion_fired": r3["refutation_criterion_fired"],
    "violations": r3["violations"],
}

# mutant 4: native_citation_not_verbatim
dl_mut4 = copy.deepcopy(dl_this_fire)
for d in dl_mut4:
    if d.get("candidate_id") == "DR-LANG-EU-10":
        d["native_citation"] = "Marine atmosphere exposure trials were started for steel specimens at the Bonassola coastal site."
r4 = check(dl_mut4, sr_all_lines, PREVIOUSLY_SUPPLIED_NL_IT)
mutants_out["native_citation_not_verbatim"] = {
    "expected_rule": "native_citation_verbatim_in_evidence",
    "how_planted": "Replaced DR-LANG-EU-10's native_citation (the exact Italian MARECO/Bonassola sentence) with an English paraphrase, simulating a silently-translated/paraphrased citation.",
    "expected_rule_fired": True,
    "refutation_criterion_fired": r4["refutation_criterion_fired"],
    "violations": r4["violations"],
}

# mutant 5: rediscovery_dropped -- synthetic previously-supplied ids, since the
# real PREVIOUSLY_SUPPLIED_NL_IT list is empty by construction.
dl_mut5 = copy.deepcopy(dl_this_fire)
if dl_mut5:
    dl_mut5[-1] = dict(dl_mut5[-1])
    dl_mut5[-1]["rediscovers"] = None
r5 = check(dl_mut5, sr_all_lines, ["NL-PRIOR-TEST", "IT-PRIOR-TEST"])
mutants_out["rediscovery_dropped"] = {
    "expected_rule": "rediscovery_recall",
    "how_planted": "Injected two SYNTHETIC previously-supplied candidate ids ('NL-PRIOR-TEST', 'IT-PRIOR-TEST') into the checker's previously_supplied_ids input -- since this fire genuinely found zero real prior nl/it candidates (see intake_manifest), synthetic ids are required to prove this rule is a real, non-vacuous check rather than one that trivially never fires on an empty input list.",
    "expected_rule_fired": True,
    "refutation_criterion_fired": r5["refutation_criterion_fired"],
    "violations": r5["violations"],
}

for k, v in mutants_out.items():
    assert v["refutation_criterion_fired"] == v["expected_rule_fired"], f"positive control FAILED for mutant {k}"

# sanity: confirm the checker does NOT spuriously fire on the real (unmutated)
# empty previously-supplied list, i.e. rule 5 is silent when there is genuinely
# nothing to recall
r5_real = check(dl_this_fire, sr_all_lines, PREVIOUSLY_SUPPLIED_NL_IT)
assert r5_real["refutation_criterion_fired"] is False, "rule 5 spuriously fired on the real empty previously-supplied list"

mutants_bytes = canon(mutants_out)
(WORK / "diagnostic.mutants.json").write_bytes(mutants_bytes)
all_mutants_fired = all(v["refutation_criterion_fired"] for v in mutants_out.values())
assert all_mutants_fired, "not all planted defects were detected -- positive control invalid"

# ---------------------------------------------------------------------------
# All assertions passed -- now (and only now) commit the real ledger writes.
# ---------------------------------------------------------------------------
sr_appended_bytes = json.dumps(search_record_line_obj, sort_keys=True, ensure_ascii=False).encode("utf-8") + b"\n"
sr_new_content = sr_before
if sr_before and not sr_new_content.endswith(b"\n"):
    sr_new_content += b"\n"
sr_new_content += sr_appended_bytes
SR_PATH.write_bytes(sr_new_content)
sr_appended_line_no = sr_prior_line_count + 1
sr_appended_sha = sha(sr_appended_bytes)
sr_file_sha_after = sha(sr_new_content)
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
