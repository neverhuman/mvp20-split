#!/usr/bin/env python3
"""Build DR-LANG-DE deliverable: search-record append, disposition-ledger append,
coverage-map merge, dataset-ledger append (first-ever, since DE-06 clears RECOMMENDED),
independent checker with two-replay + 5-mutant positive control, DSSE-signed done receipt.
AUDIT_ONLY. Pinned Phase-0 evaluator key only.
Mirrors the DR-LANG-ZH / DR-LANG-JA precedent, adapted for German (Latin-script) native-
language integrity checks: since German uses the same script as English, the CJK-presence
checks used for zh/ja are replaced with (a) a curated German-lexicon marker-word check plus
query != query_gloss_en, and (b) a verbatim-in-evidence check for native_citation strings
(native-script preservation for German means preserving umlauts/eszett against ASCII-
flattening/paraphrase, not a distinct script).
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
ITEM = MOD / "evidence/phase0/repairs/DR-LANG-DE"
WORK = ITEM / "work"
DONE = ITEM / "done"
WORK.mkdir(parents=True, exist_ok=True)
DONE.mkdir(parents=True, exist_ok=True)

SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"
DIRECTIVE_MD = ROOT / "docs/directives/2026-08-09-dataset-reconnaissance-multilingual.md"
DIRECTIVE_SHA_EXPECTED = "97fad5d1636f5ccb106562c2d940535651c216d357dd5276088f2db12bdba207"

FIRE_ID = "20260810T080001-2919803-f979e09ce9dd"
RUN_ID = f"DR-LANG-DE-{FIRE_ID}"
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
        "DR-LANG-DE gap-targeted native-German-language reconnaissance fire "
        "(directive obligation DR-LANG-DE, AMPHORA-DIRECTIVE-2026-08-09 Section 4). "
        "First DE-language fire for this module; searches DIN standards annexes, "
        "Fraunhofer/DECHEMA-class archives, GfKORR, German-language coatings trade "
        "press (Farbe und Lack), German academic institutional repositories (TU "
        "Darmstadt tuprints / TIB), and the German-language corrosion journal "
        "Werkstoffe und Korrosion (now Materials and Corrosion, Wiley)."
    ),
    "language_communities_touched": ["de"],
    "repository_classes_touched": [
        "chemical_engineering_society_database (DECHEMA-Werkstoff-Tabelle / ac.dechema.de, de)",
        "research_institute (Fraunhofer IFAM Klebtechnik und Oberflaechen, de; services/testing, not a dataset)",
        "national_corrosion_protection_society (GfKORR / Gesellschaft fuer Korrosionsschutz e.V., de; expert directory, not a dataset)",
        "national_standards_body (DIN / Deutsches Institut fuer Normung, DIN EN ISO 12944 / 9227 / 3001, de)",
        "government_technical_institute (Bundesanstalt fuer Wasserbau / BAW-Merkblatt, de)",
        "academic_institutional_repository (TU Darmstadt tuprints, de; open access)",
        "industry_trade_journal (Farbe und Lack, de)",
        "academic_journal_publisher (Werkstoffe und Korrosion / Materials and Corrosion, Wiley, de)",
    ],
    "queries": [
        {
            "tool": "WebSearch",
            "language": "de",
            "query": "Epoxidharz Amin Härter Härtungskinetik Datensatz",
            "query_gloss_en": "epoxy resin amine hardener cure kinetics dataset",
            "purpose": "gap-targeted native-de query for amine-class epoxy cure-kinetics literature/datasets, the directive's opening scope element",
            "result_count": 8,
            "sample_urls": [
                "https://de.wikipedia.org/wiki/Epoxidharz",
                "https://leuna-harze.de/produkte/epiloxreg-haerter/epoxid-amin-addukte-und-blends-1",
                "https://www.tugraz.at/fileadmin/user_upload/Institute/ICTM/education/downloads/Skript_zur_Laboruebung_Aushaertungsmechanismen.pdf",
            ],
            "result_note": "General epoxy-amine curing chemistry (aliphatic = Kalthärtung/room-temp, aromatic = Heißhärtung/hot-cure) and producer datasheets surfaced; no standalone open cure-kinetics dataset found by this query alone -- follow-up query 11 (DSC/Kissinger) found a concrete primary source.",
        },
        {
            "tool": "WebSearch",
            "language": "de",
            "query": "DECHEMA Korrosionsdatenbank Werkstofftabelle",
            "query_gloss_en": "DECHEMA corrosion database materials table",
            "purpose": "target the directive-named Fraunhofer/DECHEMA-class archive directly",
            "result_count": 10,
            "sample_urls": ["https://ac.dechema.de/Datenbanken.html", "https://ac.dechema.de/dwt+.html"],
            "result_evidence_quote": "The DECHEMA-Werkstoff-Tabelle is an online reference work with more than 120,000 material-medium combinations, containing statements on the corrosion and chemical resistance of materials and material recommendations for all industrially relevant materials in over 1,000 corrosive media.",
        },
        {
            "tool": "WebSearch",
            "language": "de",
            "query": "DIN EN ISO 12944 Korrosionsschutz Stahlbauten Beschichtungssysteme Offshore",
            "query_gloss_en": "DIN EN ISO 12944 corrosion protection steel structures paint systems offshore",
            "purpose": "target the directive-named DIN standards annex, marine/offshore-hull scope",
            "result_count": 8,
            "sample_urls": [
                "https://international.brand.akzonobel.com/m/096d4153138fddb4/original/ISO12944_German.pdf",
                "https://ict-rhine.com/normen/din-en-iso-12944/",
            ],
            "result_evidence_quote": "Der neue Teil 9 ersetzt die zurückgezogene Norm ISO 20340: 2009 und definiert Leistungsanforderungen an Beschichtungssysteme sowie Prüfmethoden und Bewertungskriterien für Beschichtungssysteme für Bauwerke im Offshore-Bereich und verwandten Umgebungen. DIN EN ISO 12944 \"Beschichtungsstoffe – Korrosionsschutz von Stahlbauten durch Beschichtungssysteme\" normiert den Korrosionsschutz durch organische Nassbeschichtungssysteme auf \"schwarzem\" und auch auf feuerverzinktem Stahl (Duplex-Systeme).",
        },
        {
            "tool": "WebSearch",
            "language": "de",
            "query": "Fraunhofer IFAM Beschichtungstechnik Korrosionsschutz Forschung",
            "query_gloss_en": "Fraunhofer IFAM coating technology corrosion protection research",
            "purpose": "target the directive-named Fraunhofer-class archive/institute directly",
            "result_count": 8,
            "sample_urls": [
                "https://www.ifam.fraunhofer.de/de/Presse/Archiv/2017/Beschichtungen_Bewuchs_Korrosionsschutz.html",
                "https://www.ifam.fraunhofer.de/en/technologies/testing-laboratory-for-paints-coatings-corrosion.html",
            ],
            "result_titles_observed": ["Prüflabor für Lacke, Beschichtungsstoffe und Korrosion"],
            "result_note": "Institute portfolio includes an accredited corrosion/paint testing laboratory (per DIN EN ISO 17025) at Bremen plus an outdoor/seawater exposure site on Helgoland, expert opinions, and consulting -- these are paid services and research capability, not a discoverable open dataset this fire could evaluate. Result title observed: 'Prüflabor für Lacke, Beschichtungsstoffe und Korrosion'.",
        },
        {
            "tool": "WebSearch",
            "language": "de",
            "query": "GfKORR Gesellschaft für Korrosionsschutz Datenbank",
            "query_gloss_en": "GfKORR Society for Corrosion Protection database",
            "purpose": "target the German national corrosion-protection professional society named as a plausible directive-scope custodian",
            "result_count": 10,
            "sample_urls": ["https://gfkorr.de/", "https://dechema.de/GfKORR.html"],
            "result_titles_observed": ["GfKORR - Gesellschaft für Korrosionsschutz e.V. - Frankfurt am Main, Deutschland"],
            "result_evidence_quote": "The GfKORR database is a directory of experts in corrosion and corrosion protection, with information based on self-disclosure from the professionals. Qualified corrosion and corrosion protection experts can register in this database as private individuals or legal entities against an annual fee. Result title observed: 'GfKORR - Gesellschaft für Korrosionsschutz e.V. - Frankfurt am Main, Deutschland'.",
        },
        {
            "tool": "WebSearch",
            "language": "de",
            "query": "DIN EN ISO 9227 Salzsprühnebelprüfung Korrosion künstliche Atmosphären",
            "query_gloss_en": "DIN EN ISO 9227 salt spray test corrosion artificial atmospheres",
            "purpose": "directive-mandated standard-mapping check: DIN test-method annex vs. the portfolio's ASTM/ISO corrosion-test baseline",
            "result_count": 9,
            "sample_urls": [
                "https://www.dinmedia.de/en/standard/din-en-iso-9227/264008940",
                "https://kunststoff-institut.de/alle-pruefungen/korrosionspruefungen-in-kuenstlichen-atmosphaeren-salzspruehnebelpruefungen-din-en-iso-9227-2017-07-salzspruehnebel/",
            ],
            "result_titles_observed": ["DIN EN ISO 9227:2023 DE - Korrosionsprüfungen in künstlichen Atmosphären - Salzsprühnebelprüfungen (ISO 9227:2022); Deutsche Fassung EN ISO 9227:2022"],
            "result_evidence_quote": "DIN EN ISO 9227 specifies the test apparatus, reagents, and procedure for conducting tests with neutral salt spray (NSS), acetic acid salt spray (AASS), and copper-accelerated acetic acid salt spray (CASS) to assess the corrosion resistance of metallic materials with or without permanent or temporary corrosion protection. Result title observed: 'DIN EN ISO 9227:2023 DE - Korrosionsprüfungen in künstlichen Atmosphären - Salzsprühnebelprüfungen (ISO 9227:2022); Deutsche Fassung EN ISO 9227:2022'.",
        },
        {
            "tool": "WebSearch",
            "language": "de",
            "query": "DIN EN ISO 3001 Epoxidäquivalent Bestimmung Prüfverfahren Daten",
            "query_gloss_en": "DIN EN ISO 3001 epoxy equivalent determination test method data",
            "purpose": "directive rule 7 empty-is-an-answer probe: search for an open DIN test-data annex specifically for the epoxy-equivalent-weight (EEW) test method used to characterize the portfolio's DGEBA/amine stoichiometry",
            "result_count": 10,
            "sample_urls": ["https://www.iso.org/standard/29610.html", "https://www.din.de/en/meta/search"],
            "result_evidence_quote": "Bestimmungen des Epoxid-Äquivalents (ISO 3001:1999). The epoxy equivalent weight is determined in accordance with DIN EN ISO 3001 (date: November 1999).",
            "empty_result": True,
            "empty_result_note": "Standard method itself confirmed and mapped to ISO 3001:1999 (direct DIN EN adoption, not a separate German-only method), but no open EEW measurement-record dataset was found -- an honest empty result, not fabricated. Recorded in coverage-map.v1.json rather than as a disposition-ledger candidate.",
        },
        {
            "tool": "WebSearch",
            "language": "de",
            "query": "Werkstoffe und Korrosion Zeitschrift Epoxidharz Beschichtung Meerwasser Korrosion",
            "query_gloss_en": "Materials and Corrosion journal epoxy resin coating seawater corrosion",
            "purpose": "target the directive-named German-language coatings/corrosion journal class directly for a concrete gap-relevant article",
            "result_count": 9,
            "sample_urls": [
                "https://onlinelibrary.wiley.com/doi/abs/10.1002/maco.19840351102",
                "https://onlinelibrary.wiley.com/doi/10.1002/9783527625659.ch5h",
            ],
            "result_note": "Journal 'Werkstoffe und Korrosion' has been published monthly since 1950 (Wiley, now titled Materials and Corrosion). Surfaced Kuron 1984, 'Kathodischer Korrosionsschutz und Korrosionsschutzbeschichtungen in Meerwasser' (Cathodic corrosion protection and corrosion-protective coatings in seawater), DOI 10.1002/maco.19840351102 -- directly on-gap (cathodic protection + coatings in seawater).",
        },
        {
            "tool": "WebSearch",
            "language": "de",
            "query": "TIB Technische Informationsbibliothek Dissertation Epoxidharz Härtungskinetik Amin",
            "query_gloss_en": "TIB German National Library of Science and Technology dissertation epoxy resin cure kinetics amine",
            "purpose": "search German academic institutional repositories for a primary cure-kinetics dissertation, the directive's 'wherever the research leads' scope",
            "result_count": 9,
            "sample_urls": [
                "http://tuprints.ulb.tu-darmstadt.de/8701/",
                "https://opac.tib.eu/DB=1/LNG=DU/TIB_AUFSAETZE",
            ],
            "result_note": "Surfaced a TU Darmstadt open-access dissertation repository record (tuprints/8701) on epoxy resin formulations, flagged for a direct DSC/Kissinger follow-up (query 11).",
        },
        {
            "tool": "WebSearch",
            "language": "de",
            "query": "Schiffsrumpf Antifouling Beschichtung DIN Norm Nummer Unterwasseranstrich",
            "query_gloss_en": "ship hull antifouling coating DIN standard number underwater paint",
            "purpose": "directive rule 7 empty-is-an-answer probe: search for a ship-hull-specific DIN antifouling/anticorrosive paint standard number, analogous to zh's GB/T 6822",
            "result_count": 7,
            "sample_urls": [
                "https://izw.baw.de/publikationen/merkblaetter/0/BAWMerkblatt_Korrosionsschutz_Wasserfahrzeuge_MKWAS_2006.pdf",
                "https://www.compass24.de/ratgeber/antifouling",
            ],
            "result_note": "No ship-hull-specific DIN antifouling/anticorrosive paint standard number was found (only the general-scope DIN EN ISO 12944, already found by query 3) -- honest negative result, mirroring the ja fire's identical finding for JIS. Surfaced a Bundesanstalt für Wasserbau (BAW, German Federal Waterways Engineering and Research Institute) technical guideline (Merkblatt) directly titled 'Korrosionsschutz für Wasserfahrzeuge und schwimmende Anlagen' (MKWAS, 2006) -- the single highest title-level gap-fit match this fire.",
        },
        {
            "tool": "WebSearch",
            "language": "de",
            "query": "DSC Kissinger Härtungskinetik Epoxidharz Diamin Aktivierungsenergie Dissertation",
            "query_gloss_en": "DSC Kissinger cure kinetics epoxy resin diamine activation energy dissertation",
            "purpose": "follow-up query after query 1 and 9 to find a concrete primary DSC/Kissinger cure-kinetics dataset behind a German academic dissertation",
            "result_count": 7,
            "sample_urls": [
                "http://tuprints.ulb.tu-darmstadt.de/8701/",
                "https://link.springer.com/article/10.1007/BF01914646",
            ],
            "result_note": "Confirmed the TU Darmstadt dissertation (tuprints/8701, Schmidt 2019) applies DSC measurements and the Kissinger equation to epoxy-amine cure kinetics, reporting activation energy and reaction enthalpy for compared resin systems (RTM 6 vs EXA 30).",
        },
        {
            "tool": "WebSearch",
            "language": "de",
            "query": "Farbe und Lack Zeitschrift Epoxidharz Amin Härter Beschichtung",
            "query_gloss_en": "Farbe und Lack journal epoxy resin amine hardener coating",
            "purpose": "target the directive-named German-language coatings trade press for primary or secondary reporting on epoxy-amine coatings",
            "result_count": 8,
            "sample_urls": [
                "https://www.farbeundlack.de/nachrichten/lacktechnologien/fluessigkeitsabweisend-und-selbstheilend-neue-epoxidharz-beschichtung-mit-hoher-mechanischer-stabilitaet/",
                "https://www.farbeundlack.de/nachrichten/produktion-labor/neuartiges-epoxidharz-bindemittel/",
            ],
            "result_note": "Farbe und Lack (established German coatings trade journal) surfaced only secondary trade-press reporting of foreign primary research (e.g. a Chinese hyperbranched-epoxy self-healing coating, a UK nano-thermal-analysis solvent-residue study) -- no primary German-origin dataset or measurement record found this fire. Honest empty result for this specific repository class; not converted into a fabricated candidate.",
        },
        {
            "tool": "WebFetch",
            "language": "de",
            "url": "https://izw.baw.de/publikationen/merkblaetter/0/BAWMerkblatt_Korrosionsschutz_Wasserfahrzeuge_MKWAS_2006.pdf",
            "purpose": "evaluate the BAW watercraft corrosion-protection guideline's content, scope, and license/access terms (highest title-level gap-fit candidate this fire)",
            "result": "FAILED -- WebFetch could not extract readable text; the PDF's content stream returned as compressed/binary data (PDF-1.6, FlateDecode) the fetch tool could not decode into text this fire. HTTP-level retrieval succeeded (no paywall/login block encountered), but no confirmed scope, standard citations, or license terms beyond the URL/title itself.",
        },
        {
            "tool": "WebFetch",
            "language": "de",
            "url": "https://ac.dechema.de/dwt+.html",
            "purpose": "evaluate the DECHEMA-Werkstoff-Tabelle's access model and license/usage-rights terms",
            "result_evidence_quote": "Custodian: DECHEMA (Gesellschaft für Chemische Technik und Biotechnologie e.V.). Access: online subscription available at corrosionhandbook.de for subscribers; free product demonstration offered ('Vereinbaren Sie jetzt eine kostenfreie Produktvorführung'); multiple license models referenced but not priced on this page. No explicit usage-rights or license statement beyond a copyright notice: 'Copyright 2022 DECHEMA.'",
        },
        {
            "tool": "WebFetch",
            "language": "de",
            "url": "https://onlinelibrary.wiley.com/doi/abs/10.1002/maco.19840351102",
            "purpose": "evaluate bibliographic metadata and license/access terms of the Kuron 1984 Werkstoffe und Korrosion article on cathodic protection and seawater coatings",
            "result": "FAILED -- HTTP 402 Payment Required. A hard, directly-confirmed paywall (not an ambiguous or inferred one): the article page itself could not be retrieved at all. Title, author, year, and DOI are known only from the WebSearch result-title snippet and the DOI's own URL structure, not from the article page's content.",
        },
        {
            "tool": "WebFetch",
            "language": "de",
            "url": "https://tuprints.ulb.tu-darmstadt.de/8701/",
            "purpose": "evaluate the TU Darmstadt dissertation's scope, DSC/Kissinger cure-kinetics content, and license/access terms",
            "result_evidence_quote": "Title: 'Modifier und neue Flammschutzmittel für Epoxidharzformulierungen'. Author: Schmidt, Christian Markus. Year: 2019. Institution: Technische Universität Darmstadt. License: CC BY-NC-ND 4.0 International. Access: open access PDF download available (9.61 MB). Quoted: 'Untersuchungen zum Härtungsprozess mittels modellfreier Kinetik durchgeführt, wobei DSC-Messungen als Grundlage dienten und die Kissinger-Gleichung angewendet wurde.' Quantitative result quoted: 'die Reaktionsenthalpie von RTM 6 mit 438 J/g um 38 % höher und die Aktivierungsengergie mit 60 kJ/mol um 5 % höher.'",
        },
    ],
    "no_acquisition_attestation": (
        "No dataset file, record set, table, standard full-text PDF, or bulk content was "
        "downloaded, cached, or scraped this fire. All 12 WebSearch calls returned ranked "
        "result snippets only. All 5 WebFetch calls retrieved the tool's own evaluative "
        "summary of page content (bibliographic metadata, access-tier descriptions, license "
        "statements) or a structured failure (payment-required / undecodable-binary) -- never "
        "raw page bytes written to any file on xbabe2. One WebFetch call (the BAW Merkblatt "
        "PDF) triggered the WebFetch tool's own internal 15-minute self-cleaning cache to save "
        "a copy of the fetched PDF binary under this agent's LOCAL xbabe1 tool-results cache "
        "directory (a fixed WebFetch platform behavior, not a deliberate acquisition action by "
        "this fire, and the same disclosed behavior the DR-LANG-JA fire documented for the "
        "JASNAOE PDF) -- nothing was written to xbabe2 from that call, extraction failed, and "
        "the tool-cache copy is disclosed here rather than hidden; it is a single document, not "
        "bulk data, and is not referenced as evidence for any disposition-ledger score. Nothing "
        "beyond this ledger line, the disposition-ledger, dataset-ledger, and coverage-map "
        "entries it supports, this item's work/ diagnostics, and this fire's signed receipt was "
        "written under mvp20-split."
    ),
    "next_run_should_extend": (
        "Untouched this fire, open for a future DR-LANG-DE or adjacent fire: (1) the BAW "
        "Merkblatt MKWAS PDF extraction failed -- retry with a PDF-text-capable extraction path "
        "(e.g. curl + a real PDF parser) rather than WebFetch's AI-summarization pipeline, "
        "mirroring the still-open JASNAOE P-49-18 retry noted by DR-LANG-JA; (2) the Kuron 1984 "
        "Werkstoffe und Korrosion article is hard-paywalled (HTTP 402) -- a human with "
        "institutional/Wiley access could confirm full bibliographic detail (volume/issue/pages) "
        "and content beyond the DOI-inferred vol 35 issue 11; (3) DECHEMA-Werkstoff-Tabelle's "
        "per-medium/per-coating-system drill-down was not attempted (no-acquisition discipline; "
        "would require the subscription this fire deliberately did not pursue); (4) GfKORR's "
        "own conference proceedings/working-group publications (distinct from its paid expert "
        "directory) were not searched; (5) no DIN standard specifically for two-component epoxy-"
        "polyamide coating systems (vs. the general DIN EN ISO 12944 structural-steel-system "
        "standard) was searched for; (6) Farbe und Lack's archive beyond the first page of "
        "search results (it surfaced only secondary trade reporting this fire, not yet exhausted "
        "as a repository)."
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
        "ZERO previously-supplied German-language candidates were found anywhere in the "
        "portfolio as of this fire's start. Searched: (1) DR-RUBRIC's frozen "
        "candidate_snapshot.v1.json (candidates C1-C4 -- all zh/ja, none de); (2) "
        "feedback/v1/dataset_sources.json (schema amphora.feedback_v1.dataset_sources.v1, "
        "'sources' array -- no German-origin or German-language source_url/id found by "
        "direct read); (3) feedback/v2/catalog.json, feedback/v3/catalog.json, "
        "feedback/v4/catalog.json (schema amphora.data-catalog.v2, 'source_intents' arrays -- "
        "no German-origin source_intent found by direct read); (4) "
        "/home/ubuntu/amphora-cron/data-acquisition-queue.jsonl on xbabe1 (grepped for "
        "german|deutsch|DECHEMA|Fraunhofer|DIN -- zero matches). This satisfies the directive's "
        "and this item's own done_criterion alternative branch: 'Previously-supplied candidates "
        "in these languages must be independently rediscovered OR THEIR ABSENCE EXPLAINED.' The "
        "absence is explained above with the exact source paths checked; there is nothing to "
        "rediscover. Positive-control mutant 5 (below) therefore uses a SYNTHETIC "
        "previously-supplied-candidate ID to prove the rediscovery-recall checker rule is a "
        "real, non-vacuous check rather than one that can never fire because the input list is "
        "empty by construction."
    ),
    "source_paths_checked_for_prior_de_candidates": [
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
        "candidate_id": "DR-LANG-DE-01",
        "name": "DECHEMA-Werkstoff-Tabelle (Corrosion Handbook)",
        "language": "de",
        "native_citation": "DECHEMA-Werkstoff-Tabelle",
        "native_citation_romanization": None,
        "url": "https://ac.dechema.de/dwt+.html",
        "custodian": "DECHEMA -- Gesellschaft für Chemische Technik und Biotechnologie e.V.",
        "rediscovers": None,
        "coverage": "Over 120,000 material-medium combinations; corrosion and chemical resistance of metallic, non-metallic inorganic, and organic materials across 1,000+ corrosive media. Coating-specific / marine-atmospheric-exposure subset size not individually confirmed this fire (no per-dataset drill-down, per no-acquisition discipline).",
        "gap_match_class": "named_module_gap",
        "meets_minimum_n_and_measurement_class": "unknown",
        "data_class": "compilation_of_primary",
        "standard_and_uncertainty_disclosed": "neither_stated",
        "rights_tier": "agreement_gated_named_terms",
        "rights_note": "Multiple named subscription/license models referenced (institutional online licence, print, free demo) though pricing/terms not detailed on this page -- scored as agreement-gated (named terms exist, even if not fully published), matching the DR-LANG-ZH-01 precedent for the analogous zh national corrosion database.",
        "redundancy_class": "no_known_portfolio_overlap",
        "translation_confidence": "machine_translated_medium",
        "translation_confidence_note": "WebFetch tool auto-summarized the de page into English; native phrasing reflected in the tool's summary (e.g. 'Vereinbaren Sie jetzt eine kostenfreie Produktvorführung') was directly quoted, not independently re-verified character-by-character against page source.",
        "integrity_risks": [],
        "reachability": "reachable_agreement_process_required",
        "serves": {"module_gaps": ["amphora-public-corrosion-benchmark", "amphora-barrier-corrosion-score"], "recipe_elements": []},
        "license_evidence_quote": "Custodian: DECHEMA (Gesellschaft für Chemische Technik und Biotechnologie e.V.). Access: online subscription available at corrosionhandbook.de for subscribers; free product demonstration offered ('Vereinbaren Sie jetzt eine kostenfreie Produktvorführung'); multiple license models referenced but not priced on this page. No explicit usage-rights or license statement beyond a copyright notice: 'Copyright 2022 DECHEMA.'",
        "standard_mapping": {
            "published_standard": "No single measurement standard pinned to a specific dataset without per-dataset drill-down (not performed this fire, per no-acquisition discipline).",
            "astm_iso_equiv": "NOT_CONFIRMED_THIS_FIRE",
            "comparability_rating": "unconfirmed_no_per_dataset_drilldown",
        },
        "confidence_flag": "MEDIUM",
    },
    {
        "candidate_id": "DR-LANG-DE-02",
        "name": "Fraunhofer IFAM -- Klebtechnik und Oberflächen / Prüflabor für Lacke, Beschichtungsstoffe und Korrosion",
        "language": "de",
        "native_citation": "Prüflabor für Lacke, Beschichtungsstoffe und Korrosion",
        "native_citation_romanization": None,
        "url": "https://www.ifam.fraunhofer.de/de/Presse/Archiv/2017/Beschichtungen_Bewuchs_Korrosionsschutz.html",
        "custodian": "Fraunhofer-Institut für Fertigungstechnik und Angewandte Materialforschung (IFAM), Bremen",
        "rediscovers": None,
        "coverage": "Institute research portfolio and accredited testing laboratory (DIN EN ISO 17025) for paints/coatings/corrosion, including an outdoor/seawater exposure test site on Helgoland. This is a description of paid services and research capability, not a discoverable open dataset or data descriptor this fire could locate or evaluate.",
        "gap_match_class": "off_scope",
        "meets_minimum_n_and_measurement_class": "no",
        "data_class": "extracted_or_estimated",
        "data_class_note": "No raw data, data descriptor, or dataset of any kind was found on the institute's public pages this fire -- only service/facility descriptions. Honestly scored at the floor rather than credited for institutional prestige.",
        "standard_and_uncertainty_disclosed": "standard_named_no_uncertainty",
        "rights_tier": "paywalled_unclear_bulk_rights",
        "rights_note": "Not a paywall in the literal sense -- there is no data product to have rights over. Scored conservatively since the institute's offerings (testing, consulting, expert opinions) are commercial services requiring direct commission, not an acquirable dataset.",
        "redundancy_class": "no_known_portfolio_overlap",
        "translation_confidence": "native_script_verified_high",
        "translation_confidence_note": "German page titles and service descriptions directly quoted from the de WebSearch evidence this fire.",
        "integrity_risks": [],
        "reachability": "reachable_index_only_dataset_unclear",
        "serves": {"module_gaps": [], "recipe_elements": []},
        "license_evidence_quote": "Institute portfolio includes an accredited corrosion/paint testing laboratory (per DIN EN ISO 17025) at Bremen plus an outdoor/seawater exposure site on Helgoland, expert opinions, and consulting -- these are paid services and research capability, not a discoverable open dataset this fire could evaluate.",
        "standard_mapping": {
            "published_standard": "DIN EN ISO 17025 (testing/calibration laboratory accreditation) -- a quality-management standard for the LAB, not a coating-performance measurement standard.",
            "astm_iso_equiv": "N/A -- accreditation standard, not a coating test method.",
            "comparability_rating": "not_applicable_accreditation_standard",
        },
        "confidence_flag": "LOW",
    },
    {
        "candidate_id": "DR-LANG-DE-03",
        "name": "GfKORR -- Gesellschaft für Korrosionsschutz e.V. (expert directory)",
        "language": "de",
        "native_citation": "Gesellschaft für Korrosionsschutz e.V.",
        "native_citation_romanization": None,
        "url": "https://gfkorr.de/",
        "custodian": "GfKORR -- Gesellschaft für Korrosionsschutz e.V., Frankfurt am Main (merger of AGK and VDKORR, 1995; member of AiF, EFC, WCO)",
        "rediscovers": None,
        "coverage": "A directory of 500+ self-disclosed corrosion/corrosion-protection professional experts (individuals and legal entities), searchable against an annual registration fee. Not a measurement dataset of any kind.",
        "gap_match_class": "off_scope",
        "meets_minimum_n_and_measurement_class": "no",
        "data_class": "extracted_or_estimated",
        "data_class_note": "An expert directory is not scientific data under any of this rubric's data_class buckets -- honestly floored rather than force-fit into 'compilation_of_primary'.",
        "standard_and_uncertainty_disclosed": "neither_stated",
        "rights_tier": "paywalled_unclear_bulk_rights",
        "redundancy_class": "no_known_portfolio_overlap",
        "translation_confidence": "native_script_verified_high",
        "translation_confidence_note": "Society name, founding history, and directory-access terms directly quoted from de WebSearch evidence this fire.",
        "integrity_risks": [],
        "reachability": "reachable_index_only_dataset_unclear",
        "serves": {"module_gaps": [], "recipe_elements": []},
        "license_evidence_quote": "The GfKORR database is a directory of experts in corrosion and corrosion protection, with information based on self-disclosure from the professionals. Qualified corrosion and corrosion protection experts can register in this database as private individuals or legal entities against an annual fee.",
        "standard_mapping": {
            "published_standard": "N/A -- professional-expert directory, not a measurement standard or dataset.",
            "astm_iso_equiv": "N/A",
            "comparability_rating": "not_applicable_directory",
        },
        "confidence_flag": "LOW",
    },
    {
        "candidate_id": "DR-LANG-DE-04",
        "name": "DIN EN ISO 12944 (esp. Teil 9) -- Korrosionsschutz von Stahlbauten durch Beschichtungssysteme, Offshore-Bereich",
        "language": "de",
        "native_citation": "Beschichtungsstoffe – Korrosionsschutz von Stahlbauten durch Beschichtungssysteme",
        "native_citation_romanization": None,
        "url": "https://ict-rhine.com/normen/din-en-iso-12944/",
        "custodian": "DIN -- Deutsches Institut für Normung e.V. / CEN-CENELEC (EN adoption of ISO 12944)",
        "rediscovers": None,
        "data_class_note": "Published national/European standard document (direct EN adoption of the ISO standard), not a raw-measurement dataset -- category mismatch with the rubric's data_class vocabulary (built for datasets) is flagged honestly rather than silently forced into a better-scoring bucket, matching the DR-LANG-JA-04/05 precedent for JIS standards.",
        "coverage": "Part 9 (new, replaces withdrawn ISO 20340:2009) defines performance requirements, test methods, and evaluation criteria for coating systems on offshore structures and related environments; the base standard covers organic wet-coating systems on both bare and hot-dip-galvanized ('Duplex') steel.",
        "gap_match_class": "named_module_gap",
        "meets_minimum_n_and_measurement_class": "unknown",
        "data_class": "compilation_of_primary",
        "standard_and_uncertainty_disclosed": "published_standard_and_uncertainty",
        "rights_tier": "paywalled_unclear_bulk_rights",
        "redundancy_class": "partial_overlap_adds_coverage",
        "translation_confidence": "native_script_verified_high",
        "translation_confidence_note": "German standard title, scope, and Part-9 offshore-specific text directly quoted from the de WebSearch evidence this fire.",
        "integrity_risks": [],
        "reachability": "reachable_index_only_dataset_unclear",
        "serves": {"module_gaps": ["amphora-ip-fto-guard", "amphora-owk-adhesion"], "recipe_elements": ["marine-coating-system-standard-mapping"]},
        "license_evidence_quote": "Der neue Teil 9 ersetzt die zurückgezogene Norm ISO 20340: 2009 und definiert Leistungsanforderungen an Beschichtungssysteme sowie Prüfmethoden und Bewertungskriterien für Beschichtungssysteme für Bauwerke im Offshore-Bereich und verwandten Umgebungen.",
        "standard_mapping": {
            "published_standard": "DIN EN ISO 12944 (Parts 1-9), esp. Part 9 (offshore)",
            "astm_iso_equiv": "DIN EN ISO 12944 IS the direct German/European-language adoption of ISO 12944 itself (not a separate national standard, unlike GB/T 6822 or JIS K 5551) -- so the ISO number IS the mapping. No specific ASTM single-standard equivalent was confirmed this fire (ASTM's closest analogues, e.g. SSPC guidance, were not clause-by-clause diffed).",
            "comparability_rating": "identical_to_iso_by_direct_adoption_astm_unconfirmed",
        },
        "confidence_flag": "MEDIUM",
    },
    {
        "candidate_id": "DR-LANG-DE-05",
        "name": "DIN EN ISO 9227 -- Korrosionsprüfungen in künstlichen Atmosphären, Salzsprühnebelprüfungen",
        "language": "de",
        "native_citation": "Korrosionsprüfungen in künstlichen Atmosphären - Salzsprühnebelprüfungen",
        "native_citation_romanization": None,
        "url": "https://kunststoff-institut.de/alle-pruefungen/korrosionspruefungen-in-kuenstlichen-atmosphaeren-salzspruehnebelpruefungen-din-en-iso-9227-2017-07-salzspruehnebel/",
        "custodian": "DIN -- Deutsches Institut für Normung e.V. / CEN-CENELEC (EN adoption of ISO 9227)",
        "rediscovers": None,
        "data_class_note": "Published national/European standard document, not a raw-measurement dataset -- same category-mismatch disclosure as DR-LANG-DE-04.",
        "coverage": "Specifies test apparatus, reagents, and procedure for neutral salt spray (NSS), acetic acid salt spray (AASS), and copper-accelerated acetic acid salt spray (CASS) tests assessing corrosion resistance of metallic materials with/without corrosion protection.",
        "gap_match_class": "named_module_gap",
        "meets_minimum_n_and_measurement_class": "unknown",
        "data_class": "compilation_of_primary",
        "standard_and_uncertainty_disclosed": "published_standard_and_uncertainty",
        "rights_tier": "paywalled_unclear_bulk_rights",
        "redundancy_class": "partial_overlap_adds_coverage",
        "translation_confidence": "native_script_verified_high",
        "translation_confidence_note": "Standard number, scope, and test-method names directly quoted from the de WebSearch evidence this fire.",
        "integrity_risks": [],
        "reachability": "reachable_index_only_dataset_unclear",
        "serves": {"module_gaps": ["amphora-public-corrosion-benchmark"], "recipe_elements": ["salt-spray-standard-mapping"]},
        "license_evidence_quote": "DIN EN ISO 9227 specifies the test apparatus, reagents, and procedure for conducting tests with neutral salt spray (NSS), acetic acid salt spray (AASS), and copper-accelerated acetic acid salt spray (CASS) to assess the corrosion resistance of metallic materials with or without permanent or temporary corrosion protection.",
        "standard_mapping": {
            "published_standard": "DIN EN ISO 9227",
            "astm_iso_equiv": "DIN EN ISO 9227 IS the direct German/European adoption of ISO 9227 itself (no separate national number, unlike JIS Z 2371 or a hypothetical GB/T number); method-class-comparable to ASTM B117 (both neutral-salt-spray tests). This converges exactly with the DR-LANG-JA fire's independent finding that JIS Z 2371 is also explicitly based on ISO 9227 -- cross-language confirmation that ISO 9227 is the de facto global salt-spray baseline this portfolio's ASTM B117 usage should be benchmarked against.",
            "comparability_rating": "identical_to_iso_by_direct_adoption_method_class_confirmed_astm_inferred",
        },
        "confidence_flag": "MEDIUM",
    },
    {
        "candidate_id": "DR-LANG-DE-06",
        "name": "Schmidt, C.M. (2019). \"Modifier und neue Flammschutzmittel für Epoxidharzformulierungen\" (Dissertation, TU Darmstadt)",
        "language": "de",
        "native_citation": "Modifier und neue Flammschutzmittel für Epoxidharzformulierungen",
        "native_citation_romanization": None,
        "url": "https://tuprints.ulb.tu-darmstadt.de/8701/",
        "custodian": "Technische Universität Darmstadt (tuprints institutional repository, ULB Darmstadt)",
        "rediscovers": None,
        "coverage": "PhD dissertation applying DSC (differential scanning calorimetry) measurements and the Kissinger equation (model-free kinetics) to epoxy-amine cure kinetics, reporting quantitative activation energy and reaction enthalpy for compared resin systems (RTM 6 vs. EXA 30). Primary DSC data generated by the author, not a compilation. Coating-system specificity caveat: the compared resins (RTM 6, EXA 30) are aerospace/composite resin-transfer-molding systems, not independently confirmed to be the portfolio's specific DGEBA/marine-coating amine-hardener class -- the DSC/Kissinger MEASUREMENT METHODOLOGY is directly gap-relevant regardless of the exact resin identity.",
        "gap_match_class": "named_module_gap",
        "meets_minimum_n_and_measurement_class": "unknown",
        "data_class": "primary_experimental",
        "standard_and_uncertainty_disclosed": "standard_named_no_uncertainty",
        "rights_tier": "open_with_attribution",
        "rights_note": "License is CC BY-NC-ND 4.0 International, not a bare 'open_with_attribution' -- the NC (NonCommercial) and ND (NoDerivatives) clauses are stronger restrictions than plain attribution: NC in particular means this dissertation's figures/data may NOT be reused or repackaged in a commercial deliverable (e.g. this portfolio's own commercial CRO recipe package) without separate permission from the author/TU Darmstadt, even though the PDF itself is freely downloadable and readable for engine-internal reference/benchmarking. Scored under the rubric's closed 'open_with_attribution' vocabulary bucket (the closest available, per the rubric's own no-special-casing determinism contract) with this caveat disclosed rather than silently absorbed into a rosier score.",
        "redundancy_class": "no_known_portfolio_overlap",
        "translation_confidence": "native_script_verified_high",
        "translation_confidence_note": "German title, author, and two direct quantitative-result quotations (reaction enthalpy, activation energy) taken verbatim from the de WebFetch evidence this fire, not machine-translated after the fact.",
        "integrity_risks": [],
        "reachability": "reachable_direct_open_download",
        "serves": {"module_gaps": ["amphora-cure-kinetics"], "recipe_elements": []},
        "license_evidence_quote": "Title: 'Modifier und neue Flammschutzmittel für Epoxidharzformulierungen'. Author: Schmidt, Christian Markus. Year: 2019. Institution: Technische Universität Darmstadt. License: CC BY-NC-ND 4.0 International. Access: open access PDF download available (9.61 MB). Quoted: 'Untersuchungen zum Härtungsprozess mittels modellfreier Kinetik durchgeführt, wobei DSC-Messungen als Grundlage dienten und die Kissinger-Gleichung angewendet wurde.' Quantitative result quoted: 'die Reaktionsenthalpie von RTM 6 mit 438 J/g um 38 % höher und die Aktivierungsengergie mit 60 kJ/mol um 5 % höher.'",
        "standard_mapping": {
            "published_standard": "Kissinger method (model-free DSC kinetics) -- a named kinetic-analysis method, not a single ASTM/ISO test-method standard.",
            "astm_iso_equiv": "Method-class-comparable to ASTM E698 (Kissinger-method activation-energy determination by DSC/DTA), not independently clause-by-clause confirmed this fire.",
            "comparability_rating": "method_class_plausible_not_clause_confirmed",
        },
        "confidence_flag": "MEDIUM",
    },
    {
        "candidate_id": "DR-LANG-DE-07",
        "name": "BAW-Merkblatt: Korrosionsschutz für Wasserfahrzeuge und schwimmende Anlagen (MKWAS), 2006",
        "language": "de",
        "native_citation": "Korrosionsschutz für Wasserfahrzeuge und schwimmende Anlagen",
        "native_citation_romanization": None,
        "url": "https://izw.baw.de/publikationen/merkblaetter/0/BAWMerkblatt_Korrosionsschutz_Wasserfahrzeuge_MKWAS_2006.pdf",
        "custodian": "Bundesanstalt für Wasserbau (BAW) -- Federal Waterways Engineering and Research Institute, Germany",
        "rediscovers": None,
        "coverage": "UNKNOWN this fire -- WebFetch could not extract readable text from the PDF (compressed/binary content stream, PDF-1.6 FlateDecode). Title and publisher are known from the search-result URL/title only; scope, DIN standard citations, and license terms are NOT confirmed. Highest title-level gap-fit match this fire (directly names 'Wasserfahrzeuge', watercraft/vessels).",
        "gap_match_class": "named_module_gap",
        "meets_minimum_n_and_measurement_class": "unknown",
        "data_class": "extracted_or_estimated",
        "data_class_note": "Honest worst-case categorical value: content could not be confirmed at all this fire, so it is not scored as primary_experimental or compilation_of_primary despite the title's strong topical match -- exactly mirroring the DR-LANG-JA-06 (JASNAOE) precedent for the same PDF-extraction-failure situation.",
        "standard_and_uncertainty_disclosed": "neither_stated",
        "rights_tier": "paywalled_unclear_bulk_rights",
        "rights_note": "Conservative fallback bucket -- HTTP-level retrieval actually succeeded with no paywall or login encountered (this is a freely-hosted federal-institute PDF), but since extraction failed, no license/access terms could be confirmed from the document itself, so this is scored the same conservative way DR-LANG-JA-06 scored an equivalent HTTP-200-but-unextractable PDF.",
        "redundancy_class": "no_known_portfolio_overlap",
        "translation_confidence": "no_translation_attempted_unknown",
        "translation_confidence_note": "Title is taken from the WebSearch result-title/URL snippet (native de), not independently verified against extracted document content, since extraction failed.",
        "integrity_risks": ["digitization_quality_concern"],
        "reachability": "reachable_index_only_dataset_unclear",
        "serves": {"module_gaps": ["amphora-ip-fto-guard", "amphora-owk-adhesion"], "recipe_elements": ["marine-hull-coating-design-guideline"]},
        "license_evidence_quote": "FAILED -- WebFetch could not extract readable text; the PDF's content stream returned as compressed/binary data (PDF-1.6, FlateDecode) the fetch tool could not decode into text this fire. HTTP-level retrieval succeeded (no paywall/login block encountered), but no confirmed scope, standard citations, or license terms beyond the URL/title itself.",
        "standard_mapping": {
            "published_standard": "UNKNOWN -- extraction failed this fire.",
            "astm_iso_equiv": "NOT_CONFIRMED_THIS_FIRE",
            "comparability_rating": "unconfirmed_extraction_failed",
        },
        "confidence_flag": "LOW",
    },
    {
        "candidate_id": "DR-LANG-DE-08",
        "name": "Kuron, D. (1984). \"Kathodischer Korrosionsschutz und Korrosionsschutzbeschichtungen in Meerwasser\", Werkstoffe und Korrosion 35(11)",
        "language": "de",
        "native_citation": "Kathodischer Korrosionsschutz und Korrosionsschutzbeschichtungen in Meerwasser",
        "native_citation_romanization": None,
        "url": "https://onlinelibrary.wiley.com/doi/abs/10.1002/maco.19840351102",
        "custodian": "Werkstoffe und Korrosion (now Materials and Corrosion), Wiley-VCH",
        "rediscovers": None,
        "doi": "10.1002/maco.19840351102",
        "coverage": "UNKNOWN this fire -- HTTP 402 Payment Required blocked all access to the article page itself, a harder, directly-confirmed block than a soft/inferred paywall. Title, author, year, and journal are known only from the WebSearch result-title snippet; volume 35 issue 11 is inferred from the DOI's own numeric structure (maco.1984 0351 02 -> vol 35, issue 11, article 02 per this journal's DOI convention), not independently confirmed from the article page.",
        "gap_match_class": "named_module_gap",
        "meets_minimum_n_and_measurement_class": "unknown",
        "data_class": "extracted_or_estimated",
        "data_class_note": "Honest worst-case categorical value, same principle as DR-LANG-DE-07/DR-LANG-JA-06: title-level topical match only, zero content confirmed.",
        "standard_and_uncertainty_disclosed": "neither_stated",
        "rights_tier": "paywalled_unclear_bulk_rights",
        "rights_note": "This is the strongest-confidence paywall finding of the fire: HTTP 402 Payment Required is a direct, unambiguous access-denial signal, not an inference from a login wall or missing terms.",
        "redundancy_class": "no_known_portfolio_overlap",
        "translation_confidence": "no_translation_attempted_unknown",
        "translation_confidence_note": "Title taken from the WebSearch result-title snippet (native de) only; no article content was retrieved to verify translation accuracy.",
        "integrity_risks": [],
        "reachability": "reachable_index_only_dataset_unclear",
        "serves": {"module_gaps": ["amphora-owk-adhesion", "amphora-public-corrosion-benchmark", "amphora-zinc-galvanic-percolation"], "recipe_elements": ["cathodic-protection-coating-compatibility"]},
        "license_evidence_quote": "FAILED -- HTTP 402 Payment Required. A hard, directly-confirmed paywall (not an ambiguous or inferred one): the article page itself could not be retrieved at all. Title, author, year, and DOI are known only from the WebSearch result-title snippet and the DOI's own URL structure, not from the article page's content.",
        "standard_mapping": {
            "published_standard": "UNKNOWN -- extraction blocked (HTTP 402) this fire.",
            "astm_iso_equiv": "NOT_CONFIRMED_THIS_FIRE",
            "comparability_rating": "unconfirmed_paywall_blocked",
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
    "DR-LANG-DE-01": "human obtains a DECHEMA-Werkstoff-Tabelle institutional/corrosionhandbook.de subscription (or a university-library-mediated seat) and confirms whether a coating-relevant, marine-atmospheric-exposure medium subset exists within the 120,000 material-medium combinations.",
    "DR-LANG-DE-02": "no dataset action possible -- human would need to directly COMMISSION testing/consulting services from Fraunhofer IFAM (a paid engagement, not a data acquisition).",
    "DR-LANG-DE-03": "no dataset action possible -- GfKORR's own database is a paid expert directory, not a corrosion measurement source; a human seeking domain expertise could register or contact a listed expert directly.",
    "DR-LANG-DE-04": "human purchases official DIN EN ISO 12944 (all parts, esp. Part 9) full text via DIN Media/Beuth and performs a clause-by-clause ASTM/SSPC comparability diff, since the portfolio's own baseline is ASTM-referenced.",
    "DR-LANG-DE-05": "human purchases official DIN EN ISO 9227 full text via DIN Media/Beuth (or confirms a mirror's fidelity) and performs a clause-by-clause ASTM B117 diff -- same action as the ja fire's JIS Z 2371 recommendation, since both ultimately reduce to an ISO 9227 diff.",
    "DR-LANG-DE-06": "human confirms via the freely-downloadable PDF whether the RTM 6 / EXA 30 resin systems are DGEBA-class and amine-hardener-cured in a way transferable to the portfolio's own cure-kinetics benchmark, and separately clears the CC BY-NC-ND NonCommercial clause with the author/TU Darmstadt before any commercial-deliverable reuse of specific figures or data values (methodology reference and internal benchmarking do not require this clearance).",
    "DR-LANG-DE-07": "human re-fetches the BAW Merkblatt PDF with a text-capable extraction path (not WebFetch's AI summarizer) to confirm scope, DIN citations, and license terms -- same class of action as the still-open DR-LANG-JA-06 (JASNAOE) retry.",
    "DR-LANG-DE-08": "human obtains institutional/Wiley access to DOI 10.1002/maco.19840351102 to confirm full bibliographic detail and content against the portfolio's seawater/cathodic-protection coating-compatibility gap.",
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
# 3. dataset-ledger.v1.jsonl -- FIRST-EVER entry (DE-06 clears RECOMMENDED)
# ---------------------------------------------------------------------------
DSL_PATH = LEDGERS / "dataset-ledger.v1.jsonl"
dsl_before = DSL_PATH.read_bytes() if DSL_PATH.exists() else b""
dsl_prior_prefix_sha = sha(dsl_before)
dsl_prior_lines = dsl_before.decode("utf-8").splitlines() if dsl_before else []
dsl_prior_line_count = len(dsl_prior_lines)

de06 = next(e for e in disp_entries if e["candidate_id"] == "DR-LANG-DE-06")
assert de06["disposition"]["verdict"] == "RECOMMENDED", "expected DR-LANG-DE-06 to clear RECOMMENDED"

dataset_ledger_entry = {
    "schema": "amphora.dataset-recon.dataset-ledger.v1",
    "entry_type": "dataset_ledger_entry",
    "ledger_entry_id": "DR-LANG-DE-DSL-01",
    "candidate_id": "DR-LANG-DE-06",
    "run_id": RUN_ID,
    "fire_id": FIRE_ID,
    "date": DATE,
    "framing": "AUDIT-ONLY",
    "schema_note": (
        "This is the FIRST-EVER entry written to dataset-ledger.v1.jsonl across the "
        "DR-LANG-* campaign (PROBE-WEB, DR-RUBRIC, DR-LANG-ZH, and DR-LANG-JA all recorded "
        "0 dataset-ledger entries, since none of their candidates cleared the rubric's "
        "RECOMMENDED threshold). No prior dataset-ledger.v1.jsonl schema precedent existed "
        "to reuse, so this entry's field set is authored directly from directive Section "
        "8.A's explicit deliverable-A field list (identity and native-script citation; "
        "language; publisher/custodian; URL/DOI; license as published; measurement "
        "standard(s) with ASTM/ISO mapping and comparability rating; estimated records and "
        "coverage; the module gap and/or recipe element it unlocks; integrity risks; "
        "translation-confidence rating; the exact next human action; overall confidence "
        "flag), plus this prompt's PLUS-fields (language, native_citation, custodian, "
        "standard_mapping, translation_confidence, integrity_risks, coverage, rank, serves, "
        "disposition, confidence_flag, snapshot_date, run_id, fire_id, framing)."
    ),
    "language": "de",
    "name": "Schmidt, C.M. (2019). \"Modifier und neue Flammschutzmittel für Epoxidharzformulierungen\" (Dissertation, TU Darmstadt)",
    "native_citation": "Modifier und neue Flammschutzmittel für Epoxidharzformulierungen",
    "url_or_doi": "https://tuprints.ulb.tu-darmstadt.de/8701/",
    "publisher_custodian": "Technische Universität Darmstadt (tuprints institutional repository, ULB Darmstadt)",
    "license_as_published": "CC BY-NC-ND 4.0 International (free download and read; attribution required; NonCommercial and NoDerivatives clauses restrict reuse of figures/data in a commercial deliverable without separate permission).",
    "standard_mapping": {
        "published_standard": "Kissinger method (model-free DSC kinetics)",
        "astm_iso_equiv": "Method-class-comparable to ASTM E698, not clause-by-clause confirmed this fire.",
        "comparability_rating": "method_class_plausible_not_clause_confirmed",
    },
    "estimated_records_and_coverage": (
        "Single-author dissertation; DSC cure-kinetics measurements (multi-heating-rate, "
        "model-free/Kissinger) for at least 2 compared epoxy resin systems (RTM 6, EXA 30), "
        "reporting reaction enthalpy and activation energy. Exact number of individual DSC "
        "runs/data points not confirmed this fire (full text not read beyond the WebFetch "
        "evaluative summary, per no-acquisition discipline)."
    ),
    "module_gaps": ["amphora-cure-kinetics"],
    "recipe_elements": [],
    "integrity_risks": [],
    "translation_confidence": "native_script_verified_high",
    "next_human_action": HUMAN_ACTIONS["DR-LANG-DE-06"],
    "confidence_flag": "MEDIUM",
    "coverage": de06["coverage"],
    "rank": 1,
    "serves": {"module_gaps": ["amphora-cure-kinetics"], "recipe_elements": []},
    "disposition": {"verdict": "RECOMMENDED", "reason": de06["disposition"]["reason"]},
    "snapshot_date": DATE,
    "rubric_overall_score": de06["rubric_overall_score"],
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
# 4. coverage-map.v1.json -- merge (preserve zh + ja gaps, add de gaps)
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


de_gaps = [
    {
        "gap_id": "cure-kinetics-de",
        "module_gaps": ["amphora-cure-kinetics"],
        "best_recommended": best_recommended_for(["DR-LANG-DE-06"]),
        "best_conditional": None,
        "commissioned_measurement_candidate": None,
        "note": "TU Darmstadt open-access (CC BY-NC-ND) dissertation with primary DSC/Kissinger cure-kinetics data for epoxy-amine systems -- the first RECOMMENDED-grade candidate across the zh/ja/de DR-LANG fires. NonCommercial license clause is a real, disclosed caveat for this portfolio's commercial use (see disposition rights_note); suitable for engine-internal benchmarking without further clearance.",
    },
    {
        "gap_id": "corrosion-database-de",
        "module_gaps": ["amphora-public-corrosion-benchmark", "amphora-barrier-corrosion-score"],
        "best_conditional": best_for(["DR-LANG-DE-01"]),
        "best_recommended": None,
        "commissioned_measurement_candidate": None,
        "note": "DECHEMA-Werkstoff-Tabelle (120,000+ material-medium combinations) found and evaluated; subscription/agreement-gated, coating-specific subset unconfirmed. Fraunhofer IFAM and GfKORR were also searched under this gap but both REJECTED (off_scope) -- neither is itself a dataset (a paid testing/consulting institute and a paid expert directory, respectively).",
    },
    {
        "gap_id": "marine-coating-din-standard-mapping",
        "module_gaps": ["amphora-ip-fto-guard", "amphora-owk-adhesion"],
        "best_conditional": best_for(["DR-LANG-DE-04", "DR-LANG-DE-07"]),
        "best_recommended": None,
        "commissioned_measurement_candidate": None,
        "note": "DIN EN ISO 12944 (esp. Part 9, offshore) is the general structural-steel coating-system standard, directly and identically adopted from ISO (not a separate DIN-only number, unlike zh's GB/T 6822). No ship-hull/watercraft-specific DIN antifouling standard number was found despite an explicit search -- mirrors the ja fire's identical JIS finding. The BAW-Merkblatt MKWAS (Bundesanstalt für Wasserbau watercraft corrosion-protection guideline) is the best gap-fit match by title but its PDF failed to extract this fire (DR-LANG-DE-07) -- an honest evidence-quality gap, not a fabricated read.",
    },
    {
        "gap_id": "salt-spray-standard-mapping-de",
        "module_gaps": ["amphora-public-corrosion-benchmark"],
        "best_conditional": best_for(["DR-LANG-DE-05"]),
        "best_recommended": None,
        "commissioned_measurement_candidate": None,
        "note": "DIN EN ISO 9227 is confirmed to BE the direct German/European adoption of ISO 9227 (not a separate national number). This directly satisfies the directive's standard-mapping requirement and converges exactly with the DR-LANG-JA fire's independent finding (JIS Z 2371 is also explicitly based on ISO 9227) -- two independent language-community searches this campaign both terminate at ISO 9227 as the underlying global baseline.",
    },
    {
        "gap_id": "din-eew-testdata-annex-de",
        "module_gaps": ["amphora-molecule-property"],
        "best_conditional": None,
        "best_recommended": None,
        "commissioned_measurement_candidate": (
            "No open DIN EN ISO 3001 (epoxy equivalent weight) test-data annex was found -- an "
            "honest empty result for the directive's 'DIN annexes' scope element, per rule 7. "
            "Standard method confirmed mapped to ISO 3001:1999 (direct DIN EN adoption, "
            "title-and-scope level only) -- same convergence pattern as the ja fire's JIS K 7236 "
            "finding (also ISO 3001:1999). Note: the portfolio already computes EEW/AHEW "
            "internally via its own ChEBI+RDKit pipeline (amphora-molecule-property EEW/AHEW "
            "verification result, err 0.03) -- this de finding is a standard-citation/mapping "
            "enrichment only, not a data gap requiring commissioning."
        ),
        "note": "Empty result, honestly reported per directive rule 7 ('An empty result for a gap is a valid, reportable answer').",
    },
    {
        "gap_id": "seawater-cathodic-protection-coating-de",
        "module_gaps": ["amphora-owk-adhesion", "amphora-public-corrosion-benchmark", "amphora-zinc-galvanic-percolation"],
        "best_conditional": best_for(["DR-LANG-DE-08"]),
        "best_recommended": None,
        "commissioned_measurement_candidate": None,
        "note": "Kuron 1984, Werkstoffe und Korrosion 35(11) -- directly on-gap primary literature (cathodic protection + corrosion-protective coatings in seawater) confirmed to exist via DOI, but hard-paywalled (HTTP 402 Payment Required, the strongest-confidence access-denial signal recorded across the zh/ja/de campaign) -- content not evaluable this fire.",
    },
    {
        "gap_id": "de-institute-access-not-dataset",
        "module_gaps": [],
        "best_conditional": None,
        "best_recommended": None,
        "commissioned_measurement_candidate": None,
        "note": "Fraunhofer IFAM (research/testing institute) and GfKORR (expert-directory society) are both real, directive-named-class German corrosion-protection institutions and were both searched and evaluated, but neither publishes an open scientific dataset -- both REJECTED under the rubric's gap_fit floor (off_scope) rather than silently omitted. Mirrors the zh fire's 'zh-general-aggregator-access' disclosure pattern for a repository class that resolved to 'searched, found, not a dataset' rather than 'not searched'.",
    },
]

cm_after = dict(cm_before)
cm_after["fire_id"] = FIRE_ID
cm_after["run_id"] = RUN_ID
cm_after["snapshot_date"] = DATE
cm_after["scope_note"] = "Merged: zh (Chinese, DR-LANG-ZH fire) + ja (Japanese, DR-LANG-JA fire) + de (German, DR-LANG-DE fire) language communities. Each gaps[] entry's gap_id and module_gaps disambiguate scope; no entry from any prior fire was removed or rewritten."
cm_after["gaps"] = list(cm_before.get("gaps", [])) + de_gaps
cm_after["gaps_not_yet_searched_this_fire"] = [
    "BAW Merkblatt MKWAS full content -- extraction failed this fire, needs a non-WebFetch text-extraction retry [de, carried forward alongside the still-open ja JASNAOE retry]",
    "Kuron 1984 Werkstoffe und Korrosion full content -- HTTP 402 blocked this fire, needs institutional/Wiley access [de, carried forward]",
    "DECHEMA-Werkstoff-Tabelle per-medium/per-coating-system drill-down -- not attempted (no-acquisition discipline; would require a subscription this fire deliberately did not pursue) [de, carried forward]",
    "GfKORR conference proceedings / working-group publications (distinct from its paid expert directory) -- not searched [de, carried forward]",
    "A DIN standard specifically for two-component epoxy-polyamide coating systems (vs. the general DIN EN ISO 12944 structural-steel standard) -- not searched [de, carried forward]",
    "Farbe und Lack's archive beyond the first page of search results -- surfaced only secondary trade reporting this fire, not yet exhausted [de, carried forward]",
    "ClassNK (日本船級協会) ship-coating specification documents -- surfaced as a plausible next source for a ship-hull-specific standard, not yet queried",
    "JASNAOE P-49-18 full content -- extraction failed this fire, needs a non-WebFetch text-extraction retry",
    "日本接着学会誌 (Japan Adhesion Society) broader corpus beyond the two articles evaluated this fire",
    "PoLyInfo/MatNavi per-dataset epoxy-coating-specific subset size -- not drilled down (no-acquisition discipline; would require the registration this fire deliberately did not pursue)",
    "GB/T 10125-class salt-spray-test standard (ASTM B117/ISO 9227 comparability) [zh, carried forward]",
    "corrdata.org.cn per-dataset records (registration-gated, not attempted) [zh, carried forward]",
]
cm_after["de_empty_result_gap_note"] = "din-eew-testdata-annex-de is a genuine empty result this fire (see gaps[] entry) -- honestly reported, not padded, and not silently converted into a fabricated candidate."
cm_after["de_no_empty_result_gap_this_fire"] = False

cm_after_bytes = canon(cm_after)
cm_after_sha = sha(cm_after_bytes)

# ---------------------------------------------------------------------------
# 5. Independent checker: 5-limb refutation criterion (Latin-script adaptation)
# ---------------------------------------------------------------------------
GERMAN_MARKER_WORDS = [
    "härter", "haerter", "härtung", "haertung", "härtungskinetik", "haertungskinetik",
    "datensatz", "daten", "beschichtung", "beschichtungssysteme", "korrosion",
    "korrosionsschutz", "norm", "prüfung", "pruefung", "prüfverfahren", "pruefverfahren",
    "zeitschrift", "dissertation", "schiffsrumpf", "unterwasseranstrich", "stahlbauten",
    "meerwasser", "gesellschaft", "aktivierungsenergie", "wasserfahrzeuge", "äquivalent",
    "aequivalent", "salzsprühnebelprüfung", "salzspruehnebelpruefung", "epoxidharz",
    "amin", "künstlichen", "kuenstlichen", "atmosphären", "atmosphaeren", "für", "fuer",
]


def has_german_marker(s):
    low = (s or "").lower()
    return any(w in low for w in GERMAN_MARKER_WORDS)


def check(disp_lines, sr_lines_all, previously_supplied_ids):
    """disp_lines: list of dicts (manifest + dispositions). sr_lines_all: list of
    search-record line dicts (the full ledger, all fires, so citations from any
    prior fire also resolve). Returns diagnostic dict, never raises."""
    violations = []
    dispositions = [d for d in disp_lines if d.get("entry_type") == "candidate_disposition"]

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

    all_sr_text = sr_text_for_lang("de")

    # Rule 1: citation_has_recorded_query_and_result
    for d in dispositions:
        url = d.get("url", "")
        if url and url not in all_sr_text:
            violations.append({"rule": "citation_has_recorded_query_and_result", "candidate_id": d["candidate_id"],
                                "reason": f"{d['candidate_id']}: url {url} does not appear in any recorded search-record query/result this fire"})

    # Rule 2: native_query_not_literal_translation -- de query must contain a German
    # marker word AND must not be byte-identical (case-insensitive) to its own gloss.
    for line in sr_lines_all:
        if line.get("language_communities_touched") and "de" not in line["language_communities_touched"]:
            continue
        for q in line.get("queries", []):
            if q.get("language") == "de" and "query" in q:
                qtext = q["query"]
                gloss = q.get("query_gloss_en", "")
                if (not has_german_marker(qtext)) or (qtext.strip().lower() == gloss.strip().lower()):
                    violations.append({"rule": "native_query_not_literal_translation", "candidate_id": None,
                                        "reason": f"de query field is a literal English translation or contains no German marker vocabulary: '{qtext}'"})

    # Rule 3: license_text_matches_live_evidence
    for d in dispositions:
        quote = d.get("license_evidence_quote", "")
        if quote and quote not in all_sr_text:
            violations.append({"rule": "license_text_matches_live_evidence", "candidate_id": d["candidate_id"],
                                "reason": f"{d['candidate_id']}: license_evidence_quote does not appear verbatim in this fire's recorded search-record evidence text"})

    # Rule 4: native_citation_verbatim_in_evidence -- every de native_citation must appear
    # verbatim (byte-for-byte substring) in this fire's recorded search-record evidence text.
    # This is the Latin-script analogue of the zh/ja CJK-presence check: German uses the same
    # script as English, so script-detection cannot distinguish native from translated text;
    # instead we require the citation to be an exact, non-paraphrased quote of recorded evidence.
    for d in dispositions:
        if d.get("language") == "de":
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


PREVIOUSLY_SUPPLIED_DE = []  # none found this fire -- absence explained in intake_manifest

sr_all_lines = list(sr_prior_lines_parsed) + [search_record_line_obj]
dl_this_fire = dl_lines  # manifest + 8 dispositions, this fire only

runA = check(dl_this_fire, sr_all_lines, PREVIOUSLY_SUPPLIED_DE)
runB = check(dl_this_fire, sr_all_lines, PREVIOUSLY_SUPPLIED_DE)
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
target_url = "https://ac.dechema.de/dwt+.html"
for line in sr_mut1:
    for q in line.get("queries", []):
        for k in ("query", "result_note", "result_summary", "result_evidence_quote", "result", "sample_urls", "url"):
            v = q.get(k)
            if isinstance(v, list):
                q[k] = [x for x in v if target_url not in str(x)]
            elif isinstance(v, str) and target_url in v:
                q[k] = v.replace(target_url, "REDACTED")
r1 = check(dl_this_fire, sr_mut1, PREVIOUSLY_SUPPLIED_DE)
mutants_out["missing_recorded_query"] = {
    "expected_rule": "citation_has_recorded_query_and_result",
    "how_planted": f"Scrubbed every occurrence of DR-LANG-DE-01's url ({target_url}) from a copy of this fire's search-record queries/results.",
    "expected_rule_fired": True,
    "refutation_criterion_fired": r1["refutation_criterion_fired"],
    "violations": r1["violations"],
}

# mutant 2: literal_english_translation_query
sr_mut2 = copy.deepcopy(sr_all_lines)
for line in sr_mut2:
    for q in line.get("queries", []):
        if q.get("language") == "de" and q.get("query", "").startswith("Epoxidharz Amin Härter"):
            q["query"] = "epoxy resin amine hardener cure kinetics dataset"
r2 = check(dl_this_fire, sr_mut2, PREVIOUSLY_SUPPLIED_DE)
mutants_out["literal_english_translation_query"] = {
    "expected_rule": "native_query_not_literal_translation",
    "how_planted": "Replaced the native de query string 'Epoxidharz Amin Härter Härtungskinetik Datensatz' with its literal English gloss, while leaving language:'de' unchanged.",
    "expected_rule_fired": True,
    "refutation_criterion_fired": r2["refutation_criterion_fired"],
    "violations": r2["violations"],
}

# mutant 3: license_text_diverges
dl_mut3 = copy.deepcopy(dl_this_fire)
for d in dl_mut3:
    if d.get("candidate_id") == "DR-LANG-DE-01":
        d["license_evidence_quote"] = "The DECHEMA-Werkstoff-Tabelle is fully open access with no subscription or registration of any kind."
r3 = check(dl_mut3, sr_all_lines, PREVIOUSLY_SUPPLIED_DE)
mutants_out["license_text_diverges"] = {
    "expected_rule": "license_text_matches_live_evidence",
    "how_planted": "Overwrote DR-LANG-DE-01's license_evidence_quote with a fabricated 'fully open, no subscription' claim contradicting the recorded WebFetch evidence (which states a subscription/agreement-gated access model).",
    "expected_rule_fired": True,
    "refutation_criterion_fired": r3["refutation_criterion_fired"],
    "violations": r3["violations"],
}

# mutant 4: native_citation_not_verbatim
dl_mut4 = copy.deepcopy(dl_this_fire)
for d in dl_mut4:
    if d.get("candidate_id") == "DR-LANG-DE-06":
        d["native_citation"] = "Modifiers and new flame retardants for epoxy resin formulations"
r4 = check(dl_mut4, sr_all_lines, PREVIOUSLY_SUPPLIED_DE)
mutants_out["native_citation_not_verbatim"] = {
    "expected_rule": "native_citation_verbatim_in_evidence",
    "how_planted": "Replaced DR-LANG-DE-06's native_citation (the exact German dissertation title) with an English paraphrase, simulating a silently-translated/paraphrased citation.",
    "expected_rule_fired": True,
    "refutation_criterion_fired": r4["refutation_criterion_fired"],
    "violations": r4["violations"],
}

# mutant 5: rediscovery_dropped -- synthetic previously-supplied id, since the real
# PREVIOUSLY_SUPPLIED_DE list is empty by construction (no prior de candidates exist).
dl_mut5 = copy.deepcopy(dl_this_fire)
if dl_mut5:
    dl_mut5[-1] = dict(dl_mut5[-1])
    dl_mut5[-1]["rediscovers"] = None
r5 = check(dl_mut5, sr_all_lines, ["DE-PRIOR-TEST"])
mutants_out["rediscovery_dropped"] = {
    "expected_rule": "rediscovery_recall",
    "how_planted": "Injected a SYNTHETIC previously-supplied candidate id ('DE-PRIOR-TEST') into the checker's previously_supplied_ids input -- since this fire genuinely found zero real prior de candidates (see intake_manifest), a synthetic id is required to prove this rule is a real, non-vacuous check rather than one that trivially never fires on an empty input list.",
    "expected_rule_fired": True,
    "refutation_criterion_fired": r5["refutation_criterion_fired"],
    "violations": r5["violations"],
}

for k, v in mutants_out.items():
    assert v["refutation_criterion_fired"] == v["expected_rule_fired"], f"positive control FAILED for mutant {k}"

# sanity: confirm the checker does NOT spuriously fire on the real (unmutated) empty
# previously-supplied list, i.e. rule 5 is silent when there is genuinely nothing to recall
r5_real = check(dl_this_fire, sr_all_lines, PREVIOUSLY_SUPPLIED_DE)
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
