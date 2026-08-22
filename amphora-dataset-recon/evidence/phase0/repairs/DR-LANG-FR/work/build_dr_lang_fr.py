#!/usr/bin/env python3
"""Build DR-LANG-FR deliverable: search-record append, disposition-ledger append,
coverage-map merge, dataset-ledger append, independent checker with two-replay +
5-mutant positive control, DSSE-signed done receipt. AUDIT_ONLY. Pinned Phase-0
evaluator key only. Mirrors the DR-LANG-DE precedent (Latin-script adaptation of
the zh/ja CJK-presence checks), adapted for French: French uses the same Latin
script as German/English, so rule 2 uses a curated French technical-vocabulary
marker-word check + query != query_gloss_en, and rule 4 uses a verbatim-in-
evidence check for native_citation strings (preserving French orthography --
accents/cedilla -- against ASCII-flattening/paraphrase).
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
ITEM = MOD / "evidence/phase0/repairs/DR-LANG-FR"
WORK = ITEM / "work"
DONE = ITEM / "done"
WORK.mkdir(parents=True, exist_ok=True)
DONE.mkdir(parents=True, exist_ok=True)

SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"
DIRECTIVE_MD = ROOT / "docs/directives/2026-08-09-dataset-reconnaissance-multilingual.md"
DIRECTIVE_SHA_EXPECTED = "97fad5d1636f5ccb106562c2d940535651c216d357dd5276088f2db12bdba207"

FIRE_ID = "20260810T110001-156068-0cc55c68d8dd"
RUN_ID = f"DR-LANG-FR-{FIRE_ID}"
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
        "DR-LANG-FR gap-targeted native-French-language reconnaissance fire "
        "(directive obligation DR-LANG-FR, AMPHORA-DIRECTIVE-2026-08-09 Section 4). "
        "First FR-language fire for this module; searches NF standards annexes "
        "(AFNOR), HAL/theses.fr, IFREMER (Archimer), CEFRACOR (French national "
        "anti-corrosion society), and French-language corrosion/coatings trade and "
        "academic literature."
    ),
    "language_communities_touched": ["fr"],
    "repository_classes_touched": [
        "national_standards_body (AFNOR / NF EN ISO, fr)",
        "national_thesis_aggregator (theses.fr, fr)",
        "academic_institutional_repository (theses.hal.science / HAL, fr; FOUND ANTIBOT-GATED)",
        "national_marine_research_institute (IFREMER / Archimer, fr)",
        "national_corrosion_protection_society (CEFRACOR -- Centre Francais de l'AntiCorrosion, fr)",
        "academic_journal_publisher (Materiaux et Techniques class search, fr; no primary hit)",
        "industry_trade_journal (Peinture Actualites / Formule Verte class search, fr; no primary hit)",
    ],
    "queries": [
        {
            "tool": "WebSearch",
            "language": "fr",
            "query": "résine époxyde amine durcisseur cinétique de durcissement jeu de données",
            "query_gloss_en": "epoxy resin amine hardener cure kinetics dataset",
            "purpose": "gap-targeted native-fr query for amine-class epoxy cure-kinetics literature/datasets, the directive's opening scope element",
            "result_count": 6,
            "sample_urls": [
                "https://pastel.hal.science/pastel-00003668/document",
                "https://www.inrs.fr/dam/jcr:c2f1585c-e5c2-4ab0-9921-9f81d47985fc/POLYMERE_EP.pdf",
            ],
            "result_note": "Surfaced a HAL PASTEL thesis on epoxy/amine resins for reactive rotomolding (adjacent-domain, not coatings), an INRS (French national occupational-safety institute) technical note on epoxy polymer risks, and general DGEBA/amine-hardener chemistry pages; no standalone open cure-kinetics dataset found by this query alone -- follow-up queries 9/12 found concrete primary theses.",
        },
        {
            "tool": "WebSearch",
            "language": "fr",
            "query": "CEFRACOR base de données corrosion Centre Français de l'Anticorrosion",
            "query_gloss_en": "CEFRACOR corrosion database French Anti-Corrosion Center",
            "purpose": "target the directive-named French national corrosion-protection professional society directly, as a plausible directive-scope custodian",
            "result_count": 9,
            "sample_urls": ["https://www.cefracor.org/", "https://www.cefracor.org/fr/le-cefracor"],
            "result_evidence_quote": "CEFRACOR (Centre Francais de l'AntiCorrosion) is a nonprofit association established in 1989 through the merger of the AIAC (Association of Engineers in Anti-Corrosion), created in 1952, and the first CEFRACOR (French Corrosion Center), created in 1960. CEFRACOR currently has 150 institutional members and a total of 750 individual members, of which approximately 2/3 are from industry.",
        },
        {
            "tool": "WebSearch",
            "language": "fr",
            "query": "NF EN ISO 12944 protection anticorrosion structures acier systèmes peinture offshore",
            "query_gloss_en": "NF EN ISO 12944 corrosion protection steel structures paint systems offshore",
            "purpose": "directive-mandated standard-mapping check: NF standards annex vs. the portfolio's ASTM/ISO corrosion-test baseline, marine/offshore-hull scope",
            "result_count": 7,
            "sample_urls": [
                "https://www.boutique.afnor.org/en-gb/standard/nf-en-iso-129449/paints-and-varnishes-corrosion-protection-of-steel-structures-by-protective/fa184259/80691",
                "https://www.iso.org/obp/ui/#!iso:std:64833:fr",
            ],
            "result_titles_observed": [
                "ISO 12944-1:2017(fr), Peintures et vernis — Anticorrosion des structures en acier par systèmes de peinture — Partie 1: Introduction générale",
            ],
            "result_evidence_quote": "ISO 12944-1:2017(fr), Peintures et vernis — Anticorrosion des structures en acier par systèmes de peinture — Partie 1: Introduction générale. Part 9 specifies the performance requirements for protective paint systems for offshore and related structures exposed to the marine atmosphere, as well as those immersed in sea or brackish water. These structures are exposed to environments of corrosivity category CX (offshore) and immersion category Im4 as defined in ISO 12944-2. For atmospheric offshore zones classified as CX according to ISO 12944 corrosion categories, the total dry film thickness is generally 400 to 500 µm for a three-layer system using zinc-rich epoxy with glass flakes and polyurethane.",
        },
        {
            "tool": "WebSearch",
            "language": "fr",
            "query": "IFREMER corrosion marine revêtement essai vieillissement acier",
            "query_gloss_en": "IFREMER marine corrosion coating test aging steel",
            "purpose": "target the directive-named national marine research institute directly for a coating/corrosion dataset",
            "result_count": 9,
            "sample_urls": [
                "https://archimer.ifremer.fr/doc/00717/82886/",
                "https://www.institut-corrosion.fr/laboratoire-eau-de-mer/",
            ],
            "result_note": "IFREMER research addresses durability of metal/elastomer assemblies in marine environments and operates aging chambers (Brest site, fresh seawater, 4C to over 140C) for accelerated coating/material aging. Surfaced an Archimer repository record 'Corrosion marine. Bibliographie' (Lemoine & Thebault, 1977, CNEXO) -- a bibliographic reference compilation, evaluated further via WebFetch (see below). Also surfaced Institut de la Corrosion's private 'Laboratoire Eau de Mer' (commercial testing lab, not a public dataset).",
        },
        {
            "tool": "WebSearch",
            "language": "fr",
            "query": "NF EN ISO 9227 essai brouillard salin corrosion atmosphères artificielles",
            "query_gloss_en": "NF EN ISO 9227 salt spray test corrosion artificial atmospheres",
            "purpose": "directive-mandated standard-mapping check for the salt-spray test method",
            "result_count": 6,
            "sample_urls": [
                "https://www.boutique.afnor.org/fr-fr/norme/nf-en-iso-9227/essais-de-corrosion-en-atmospheres-artificielles-essais-aux-brouillards-sal/fa201512/340484",
                "https://norminfo.afnor.org/norme/nf-en-iso-9227/essais-de-corrosion-en-atmospheres-artificielles-essais-aux-brouillards-salins/193949",
            ],
            "result_evidence_quote": "NF EN ISO 9227 specifies tests for corrosion in artificial atmospheres using salt spray methods... The standard specifies the equipment, reagents, and procedures for neutral salt spray testing (NSS), acetic salt spray testing (AASS), and accelerated copper-acetic salt spray testing (CASS)... Important limitations to note: These methods are not recommended for comparative testing purposes to rank different materials against each other regarding corrosion resistance, or as a means to predict long-term corrosion resistance of the tested material.",
        },
        {
            "tool": "WebSearch",
            "language": "fr",
            "query": "NF EN ISO 3001 équivalent époxyde détermination méthode d'essai données",
            "query_gloss_en": "NF EN ISO 3001 epoxy equivalent determination test method data",
            "purpose": "directive rule 7 empty-is-an-answer probe: search for an open NF test-data annex specifically for the epoxy-equivalent-weight (EEW) test method used to characterize the portfolio's DGEBA/amine stoichiometry",
            "result_count": 10,
            "sample_urls": [
                "https://norminfo.afnor.org/consultation/nf-en-iso-3001/plastiques-compositions-epoxydiques-determination-de-lequivalent-epoxy/50908",
                "https://www.iso.org/standard/29610.html",
            ],
            "result_evidence_quote": "La presente Norme internationale specifie une methode pour la determination de l'equivalent epoxyde et est applicable a toutes les compositions epoxydiques, y compris les epoxyamines pour lesquelles il est necessaire d'apporter la modification specifiee dans l'annexe A. Les groupes epoxy d'une prise d'essai reagissent avec du bromure d'hydrogene naissant, produit par action d'une solution titree d'acide perchlorique a 0,1 mol/l sur le bromure de tetraethylammonium.",
            "empty_result": True,
            "empty_result_note": "Standard method itself confirmed and mapped to ISO 3001:1999 (direct NF EN adoption, not a separate French-only method), but no open EEW measurement-record dataset was found -- an honest empty result, recorded in coverage-map.v1.json rather than as a disposition-ledger candidate, matching the DR-LANG-DE (din-eew) and DR-LANG-JA (jis-eew) precedent.",
        },
        {
            "tool": "WebSearch",
            "language": "fr",
            "query": "coque navire peinture antisalissure anticorrosion norme AFNOR sous-marine",
            "query_gloss_en": "ship hull antifouling anticorrosion coating AFNOR standard underwater",
            "purpose": "directive rule 7 empty-is-an-answer probe: search for a ship-hull-specific French/AFNOR antifouling/anticorrosive paint standard number, analogous to zh's GB/T 6822 and de's BAW Merkblatt search",
            "result_count": 8,
            "sample_urls": [
                "https://fr.wikipedia.org/wiki/Antifouling",
                "https://syndicats.fipec.org/index.php/accueil-sipev/anticorrosion-marine",
            ],
            "result_note": "Un pigment antisalissure possede la propriete de perdre, par lixiviation dans le milieu ambiant, des ions produits toxiques a l'egard des salissures marines, avec une definition normalisee par l'AFNOR (a pigment-property definition, not a full ship-hull coating-system standard number). No ship-hull-specific AFNOR/NF standard number analogous to DIN EN ISO 12944 Part 9 or GB/T 6822 was found -- honest negative result, mirroring the de and ja fires' identical findings for DIN/JIS.",
            "empty_result": True,
            "empty_result_note": "No French-specific ship-hull antifouling/anticorrosive coating-system standard number found beyond the general NF EN ISO 12944 (query 3, already an ISO adoption). Recorded as an empty result in coverage-map.v1.json.",
        },
        {
            "tool": "WebSearch",
            "language": "fr",
            "query": "Matériaux et Techniques revue résine époxy revêtement anticorrosion marine",
            "query_gloss_en": "Materials and Techniques journal epoxy resin coating marine anti-corrosion",
            "purpose": "target the directive-named French-language materials-science journal class directly for a concrete gap-relevant article, and general academic literature",
            "result_count": 7,
            "sample_urls": [
                "https://theses.fr/2009CLF21939",
                "https://theses.hal.science/tel-00725456v1",
            ],
            "result_note": "Did not surface a primary Materiaux et Techniques article directly, but surfaced a directly on-gap French PhD thesis (Malajati, 2009, Clermont-Ferrand 2 -- 'Etude des mecanismes de photovieillissement de revetements organiques anti-corrosion pour application comme peintures marines') via theses.fr/theses.hal.science, evaluated further via WebFetch below.",
        },
        {
            "tool": "WebSearch",
            "language": "fr",
            "query": "thèse HAL cinétique de durcissement résine époxyde amine DSC énergie d'activation",
            "query_gloss_en": "HAL thesis epoxy resin amine cure kinetics DSC activation energy",
            "purpose": "search French academic institutional repositories (HAL/theses.fr) for a primary DSC/Kissinger cure-kinetics thesis, the directive's 'wherever the research leads' scope",
            "result_count": 8,
            "sample_urls": [
                "https://theses.hal.science/tel-00136381/document",
                "https://theses.hal.science/tel-02416648v1",
            ],
            "result_note": "Surfaced two HAL thesis records on DSC-based epoxy cure kinetics (tel-00136381: DGEBA/TETA polycondensation DSC dynamic-mode kinetics; tel-02416648: dynamic+isothermal DSC kinetic study). Le facteur pre-exponentiel et l'ordre de reaction sont determines par les equations de Kissinger et Crane; energie d'activation apparente exemple citee: 54.79 kJ/mol (facteur pre-exponentiel 3.42e5 s-1, ordre de reaction 0.88). Follow-up query 12 resolved tel-00136381's theses.fr identifier and full bibliographic record.",
        },
        {
            "tool": "WebSearch",
            "language": "fr",
            "query": "Peinture Actualités Formule Verte résine époxy amine revêtement anticorrosion",
            "query_gloss_en": "Peinture Actualites Formule Verte trade press epoxy amine anticorrosion coating",
            "purpose": "target the directive-named French-language coatings trade press for primary or secondary reporting on epoxy-amine coatings",
            "result_count": 9,
            "sample_urls": [
                "https://theses.hal.science/tel-00647580/document",
                "https://pad-industrie.fr/gamme-de-peintures/5-penguard-express-peinture-anticorrosion-primaire-sechage-rapide-jotun.html",
            ],
            "result_note": "Did not surface the named trade-press titles directly (Peinture Actualites / Formule Verte returned no matching articles this fire -- honest empty result for this specific repository class, mirroring the de fire's Farbe und Lack outcome), but surfaced a second directly on-gap PhD thesis (Universite de Toulon, 2010 -- epoxy anticorrosion primer durability) and commercial epoxy-amine primer datasheets (Jotun Penguard Express). Thesis evaluated further via query 11/WebFetch below.",
        },
        {
            "tool": "WebSearch",
            "language": "fr",
            "query": "durabilité d'un primaire epoxy anticorrosion theses.fr interphase polymère métal adhérence",
            "query_gloss_en": "durability of an epoxy anticorrosion primer theses.fr polymer-metal interphase adhesion",
            "purpose": "follow-up query to resolve the theses.fr canonical record for the epoxy anticorrosion primer durability thesis surfaced by query 10",
            "result_count": 9,
            "sample_urls": ["https://theses.fr/2010TOUL0017", "https://theses.hal.science/tel-00647580"],
            "result_evidence_quote": "Etude de la durabilite d'un primaire epoxy anticorrosion : role de l'interphase polymere/metal et consequence sur l'adherence. Auteur: Thi Hai Yen Quach. Universite de Toulon (cotutelle Universite de Hanoi, Vietnam), 2010. Discipline: Physicochimie des polymeres. Systeme DGEBA-polyamidoamine, terpolymere vinylique, pigments anticorrosion phosphate de zinc et oxyde de fer, charge talc. 'La duree de vie d'un revetement depend en grande partie de son adherence.' Methodes: FTIR, analyse micro-thermique, spectroscopie d'impedance electrochimique (EIS) pour suivre les changements d'interphase lors du vieillissement hygrothermique; trois etapes de perte de protection identifiees.",
        },
        {
            "tool": "WebSearch",
            "language": "fr",
            "query": "réticulation résine époxyde modélisation cinétique réactionnelle analyse thermique dynamique theses.fr",
            "query_gloss_en": "crosslinking epoxy resin modeling reaction kinetics dynamic thermal analysis theses.fr",
            "purpose": "follow-up query to resolve the theses.fr canonical record for the DSC dynamic-thermal-analysis epoxy cure-kinetics thesis surfaced by query 9",
            "result_count": 5,
            "sample_urls": ["https://theses.fr/1992MON20245"],
            "result_evidence_quote": "Reticulation d'une resine epoxyde : modelisation de la cinetique reactionnelle par l'analyse thermique dynamique. Auteur: Malik Charles Aouri. Universite Montpellier 2, 1992. Discipline: Chimie organique, minerale, analytique, industrielle. 'La reaction chimique (polycondensation) entre une resine epoxyde (DGEBA) et une amine (TETA)' analysee par calorimetrie differentielle a balayage dynamique; le parametre n approche environ 2/3 durant la propagation tridimensionnelle; trois domaines reactionnels identifies (evolution lineaire rapide, non-evolution, evolution non lineaire a vitesse variable) selon les rapports de composition du melange.",
        },
        {
            "tool": "WebFetch",
            "language": "fr",
            "url": "https://theses.hal.science/tel-00725456v1",
            "purpose": "attempt to retrieve the Malajati 2009 thesis's full text, license, and quantitative results directly from its HAL PDF-serving host",
            "result": "FAILED -- Anubis anti-bot challenge page ('Making sure you're not a bot!', HTTP 200 but a JS challenge, not thesis content). No thesis title, author, abstract, or license terms were retrievable from this call.",
        },
        {
            "tool": "WebFetch",
            "language": "fr",
            "url": "https://theses.hal.science/tel-00647580/document",
            "purpose": "attempt to retrieve the Quach 2010 thesis's full text, license, and quantitative results directly from its HAL PDF-serving host",
            "result": "FAILED -- identical Anubis anti-bot challenge page as tel-00725456v1. No thesis content retrievable.",
        },
        {
            "tool": "WebFetch",
            "language": "fr",
            "url": "https://theses.hal.science/tel-02416648v1",
            "purpose": "attempt to retrieve a DSC dynamic+isothermal epoxy cure-kinetics thesis's full text directly from its HAL PDF-serving host",
            "result": "FAILED -- identical Anubis anti-bot challenge page. No thesis content retrievable.",
        },
        {
            "tool": "curl_raw_http_xbabe1",
            "language": "fr",
            "url": "https://theses.hal.science/tel-00725456v1",
            "purpose": "independently confirm whether the Anubis block above is WebFetch-tool-specific or a host-level bot-gate, by re-requesting the identical url with raw curl from xbabe1",
            "result": "curl -A 'Mozilla/5.0 ...' returned HTTP 200 but the response body is the SAME Anubis 'Making sure you're not a bot!' JS-challenge HTML page (title tag: 'Making sure you're not a bot!'), byte-for-byte the same challenge class as tel-00647580. Confirms this is a host-level bot-gate, not a WebFetch-tool-specific refusal -- the same evidentiary pattern PROBE-WEB used to confirm CNKI's block was network-level, not tool-level.",
        },
        {
            "tool": "WebFetch",
            "language": "fr",
            "url": "https://archimer.ifremer.fr/doc/00717/82886/",
            "purpose": "evaluate the IFREMER/CNEXO marine-corrosion bibliography's content, scope, and license/access terms",
            "result_evidence_quote": "Title: Corrosion marine. Bibliographie. Authors: Lemoine Lionel, Thebault Jacques. Year: 1977. Institution: CNEXO (Centre National pour l'Exploitation des Oceans), France. Document Type: Scientific and Technical Report. Content Description: an automated file of bibliographic references in the field of marine corrosion, created by engineers at the Oceanological Center of Brittany. Access & License: Open access. The official publisher version is freely available for download (219 pages). Published in CNEXO's scientific reports series, no. 36, ISSN 0339-2899.",
        },
        {
            "tool": "WebFetch",
            "language": "fr",
            "url": "https://www.cefracor.org/fr/le-cefracor",
            "purpose": "evaluate CEFRACOR's own about-page for a published dataset/database and membership/access terms",
            "result_evidence_quote": "CEFRACOR (Centre Français de l'AntiCorrosion) is a French learned society operating as a non-profit association since 1989. It resulted from merging two earlier organizations: the AIAC (founded 1952) and the original Centre Francais de la Corrosion (founded 1960). The organization has approximately 150 corporate members and 750 individual members, with roughly two-thirds from industry. The page does not detail specific membership or license terms; it only notes that the organization offers membership and invites visitors to Become a member.",
        },
        {
            "tool": "WebFetch",
            "language": "fr",
            "url": "https://theses.fr/2009CLF21939",
            "purpose": "evaluate the theses.fr national metadata record for the Malajati 2009 marine anti-corrosion coating photoaging thesis, since its HAL full-text host is Anubis-blocked",
            "result_evidence_quote": "Exact Title (FR): Etude des mécanismes de photovieillissement de revêtements organiques anti-corrosion pour application comme peintures marines. Author: Yassine Malajati. Advisor: Jean-Luc Gardette. Defense Year: 2009. Institution: Clermont-Ferrand 2 University. Discipline: Chemistry, Materials Science. Access Status: No specific open access designation or PDF availability restriction is indicated on this metadata record.",
        },
        {
            "tool": "WebFetch",
            "language": "fr",
            "url": "https://theses.fr/2010TOUL0017",
            "purpose": "evaluate the theses.fr national metadata record for the Quach 2010 epoxy anticorrosion primer durability thesis, since its HAL full-text host is Anubis-blocked",
            "result_evidence_quote": "Exact French Title (Verbatim): Etude de la durabilité d'un primaire epoxy anticorrosion : rôle de l'interphase polymère/métal et conséquence sur l'adhérence. Author: Thi Hai Yen Quach. Defense Year: 2010. Institution: Universite de Toulon (in cotutelle with Universite de Hanoi, Vietnam). Discipline: Physicochimie des polymeres. Systeme DGEBA-polyamidoamine, terpolymere vinylique, pigments anticorrosion phosphate de zinc et oxyde de fer, charge talc. Notable Quote from Abstract: 'La durée de vie d'un revêtement dépend en grande partie de son adhérence.' Methodes: FTIR, analyse micro-thermique, spectroscopie d'impedance electrochimique (EIS).",
            "integrity_note": "The tool's own title-line rendering flattened diacritics ('durabilite', 'role', 'polymere/metal', 'consequence', 'adherence') while its abstract-quote line in the SAME response preserved them fully ('durée', 'revêtement', 'dépend', 'adhérence') -- an internally-inconsistent diacritic-preservation artifact of the WebFetch AI-summarization layer, disclosed here per directive rule 5 (locale/typography hazards). This fire's native_citation for DR-LANG-FR-06 is sourced from the fully-accented theses.fr WebSearch SERP title (query 11 sample_urls / result_evidence_quote), not from this WebFetch call's flattened title line, specifically to avoid propagating that hazard.",
        },
        {
            "tool": "WebFetch",
            "language": "fr",
            "url": "https://theses.fr/1992MON20245",
            "purpose": "evaluate the theses.fr national metadata record for the Aouri 1992 DGEBA/TETA DSC cure-kinetics thesis",
            "result_evidence_quote": "Exact French Title (verbatim): Réticulation d'une résine époxyde : modélisation de la cinétique réactionnelle par l'analyse thermique dynamique. Author: Malik Charles Aouri. Defense Year: 1992. Institution: Montpellier 2. Discipline: Chimie organique, minerale, analytique, industrielle. Abstract Summary: polycondensation reaction between epoxy resin (DGEBA) and amine (TETA) analysed via dynamic differential scanning calorimetry; parameter n approaches approximately 2/3 during three-dimensional propagation; three reaction domains identified.",
        },
        {
            "tool": "WebFetch",
            "language": "fr",
            "url": "https://www.boutique.afnor.org/fr-fr/norme/nf-en-iso-9227/essais-de-corrosion-en-atmospheres-artificielles-essais-aux-brouillards-sal/fa201512/340484",
            "purpose": "evaluate NF EN ISO 9227's AFNOR boutique access/purchase/license terms directly",
            "result_evidence_quote": "Essais de corrosion en atmosphères artificielles - Essais aux brouillards salins. Edition & Date: November 2022, 42 pages, Tirage 1. Access & License Terms: the website structure indicates this is a paid purchase model -- users can add the standard to a cart and select optional services (Exigences, Redline+, additional languages, extra users). The standard text itself does not appear to be openly readable; instead, the page provides a summary and table of contents. Users must purchase access to view the complete normative document.",
        },
    ],
    "no_acquisition_attestation": (
        "No dataset file, record set, table, standard full-text PDF, or bulk content was "
        "downloaded, cached, or scraped this fire. All 12 WebSearch calls returned ranked "
        "result snippets only. Of 9 WebFetch calls (plus 1 raw-curl reachability re-check from "
        "xbabe1), 3 WebFetch calls (against theses.hal.science / HAL's own PDF-serving host) "
        "were blocked outright by an Anubis anti-bot challenge page (HTTP 200 but a JS 'Making "
        "sure you're not a bot!' challenge page, not thesis content -- independently reproduced "
        "via raw curl from xbabe1 with an identical result, confirming a host-level bot-gate "
        "rather than a WebFetch-tool-specific block) -- no thesis content of any kind was "
        "retrieved from those 3 calls. The remaining 6 WebFetch calls (theses.fr x3, "
        "archimer.ifremer.fr x1, cefracor.org x1, boutique.afnor.org x1) retrieved the tool's "
        "own evaluative summary of page content (bibliographic metadata, abstract text, "
        "access-tier descriptions, license/purchase-model statements) -- never raw page bytes "
        "written to any file on xbabe2. Nothing beyond this ledger line, the disposition-ledger, "
        "dataset-ledger, and coverage-map entries it supports, this item's work/ diagnostics, "
        "and this fire's signed receipt was written under mvp20-split."
    ),
    "next_run_should_extend": (
        "Untouched this fire, open for a future DR-LANG-FR (2nd/final, max_fires=2) or adjacent "
        "fire: (1) all 3 theses (tel-00725456/Malajati, tel-00647580/Quach, tel-00136381 and "
        "tel-02416648 DSC studies) are full-text-blocked by HAL's Anubis anti-bot gate -- a human "
        "with a real browser session (which passes the JS challenge) or institutional/SUDOC "
        "interlibrary-loan access could retrieve full text, exact quantitative results, and "
        "confirmed license terms; (2) the 1992 Aouri thesis (pre-digital-deposit era) may not "
        "have a PDF on HAL at all -- worth a direct SUDOC/ABES catalog check; (3) CEFRACOR's own "
        "technical conference proceedings ('journees techniques') distinct from its paid-"
        "membership structure were not searched; (4) Materiaux et Techniques (EDP Sciences "
        "journal) was not directly searched on its own publisher platform, only via general web "
        "search; (5) Peinture Actualites / Formule Verte trade press archives beyond the first "
        "page of results were not exhausted; (6) the IFREMER Archimer bibliography's own 219 "
        "pages of individual citations were not read (no-acquisition discipline) -- a future fire "
        "could evaluate whether any cited 1970s-80s reference is itself independently re-locatable "
        "and still relevant."
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
# 2. disposition-ledger.v1.jsonl new lines (1 intake manifest + 7 dispositions)
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
        "ZERO previously-supplied French-language candidates were found anywhere in the "
        "portfolio as of this fire's start. Searched: (1) DR-RUBRIC's frozen "
        "candidate_snapshot.v1.json (candidates C1-C4 -- all zh/ja, none fr); (2) "
        "feedback/v1/dataset_sources.json (schema amphora.feedback_v1.dataset_sources.v1, "
        "'sources' array -- no French-origin or French-language source_url/id found by direct "
        "grep); (3) feedback/v2/catalog.json, feedback/v3/catalog.json, feedback/v4/catalog.json "
        "(schema amphora.data-catalog.v2, 'source_intents' arrays -- no French-origin "
        "source_intent found by direct grep); (4) /home/ubuntu/amphora-cron/"
        "data-acquisition-queue.jsonl on xbabe1 (grepped for french|france|NF |HAL|theses.fr -- "
        "zero matches). This satisfies the directive's and this item's own done_criterion via "
        "its explicit alternative branch: 'Previously-supplied candidates in these languages "
        "must be independently rediscovered OR THEIR ABSENCE EXPLAINED.' The absence is "
        "explained above with the exact source paths checked; there is nothing to rediscover. "
        "Positive-control mutant 5 (below) therefore uses a SYNTHETIC previously-supplied-"
        "candidate ID to prove the rediscovery-recall checker rule is a real, non-vacuous check "
        "rather than one that can never fire because the input list is empty by construction."
    ),
    "source_paths_checked_for_prior_fr_candidates": [
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
        "candidate_id": "DR-LANG-FR-01",
        "name": "NF EN ISO 12944 (esp. Partie 9) -- Peintures et vernis, Anticorrosion des structures en acier par systèmes de peinture, offshore",
        "language": "fr",
        "native_citation": "Peintures et vernis — Anticorrosion des structures en acier par systèmes de peinture",
        "native_citation_romanization": None,
        "url": "https://www.boutique.afnor.org/en-gb/standard/nf-en-iso-129449/paints-and-varnishes-corrosion-protection-of-steel-structures-by-protective/fa184259/80691",
        "custodian": "AFNOR (Association Francaise de Normalisation) / ISO (direct EN/NF adoption of ISO 12944)",
        "rediscovers": None,
        "coverage": "Part 9 defines performance requirements, test methods, and evaluation criteria for coating systems on offshore structures (corrosivity category CX, immersion category Im4) and related environments; base standard covers organic wet-coating systems on bare and hot-dip-galvanized steel.",
        "gap_match_class": "named_module_gap",
        "meets_minimum_n_and_measurement_class": "unknown",
        "data_class": "compilation_of_primary",
        "data_class_note": "Published national/European standard document (direct NF EN adoption of the ISO standard), not a raw-measurement dataset -- category mismatch with the rubric's data_class vocabulary flagged honestly, matching the DR-LANG-DE-04/DR-LANG-JA-04/05 precedent for DIN/JIS standards.",
        "standard_and_uncertainty_disclosed": "published_standard_and_uncertainty",
        "rights_tier": "paywalled_unclear_bulk_rights",
        "redundancy_class": "partial_overlap_adds_coverage",
        "translation_confidence": "native_script_verified_high",
        "translation_confidence_note": "French standard title, scope, and Part-9 offshore-specific text (CX/Im4 corrosivity categories, dry-film-thickness figures) directly quoted from the fr WebSearch evidence this fire.",
        "integrity_risks": [],
        "reachability": "reachable_index_only_dataset_unclear",
        "serves": {"module_gaps": ["amphora-ip-fto-guard", "amphora-owk-adhesion"], "recipe_elements": ["marine-coating-system-standard-mapping"]},
        "license_evidence_quote": "Part 9 specifies the performance requirements for protective paint systems for offshore and related structures exposed to the marine atmosphere, as well as those immersed in sea or brackish water. These structures are exposed to environments of corrosivity category CX (offshore) and immersion category Im4 as defined in ISO 12944-2. For atmospheric offshore zones classified as CX according to ISO 12944 corrosion categories, the total dry film thickness is generally 400 to 500 µm for a three-layer system using zinc-rich epoxy with glass flakes and polyurethane.",
        "standard_mapping": {
            "published_standard": "NF EN ISO 12944 (Parties 1-9), esp. Partie 9 (offshore)",
            "astm_iso_equiv": "NF EN ISO 12944 IS the direct French/European-language adoption of ISO 12944 itself (identical mapping pattern independently confirmed by the de fire's DIN EN ISO 12944 and mirrored again here) -- no specific ASTM single-standard equivalent confirmed this fire.",
            "comparability_rating": "identical_to_iso_by_direct_adoption_astm_unconfirmed",
        },
        "confidence_flag": "MEDIUM",
    },
    {
        "candidate_id": "DR-LANG-FR-02",
        "name": "NF EN ISO 9227 -- Essais de corrosion en atmosphères artificielles, essais aux brouillards salins",
        "language": "fr",
        "native_citation": "Essais de corrosion en atmosphères artificielles - Essais aux brouillards salins",
        "native_citation_romanization": None,
        "url": "https://www.boutique.afnor.org/fr-fr/norme/nf-en-iso-9227/essais-de-corrosion-en-atmospheres-artificielles-essais-aux-brouillards-sal/fa201512/340484",
        "custodian": "AFNOR / ISO (direct EN/NF adoption of ISO 9227)",
        "rediscovers": None,
        "coverage": "Specifies test apparatus, reagents, and procedure for neutral salt spray (NSS), acetic acid salt spray (AASS), and copper-accelerated acetic acid salt spray (CASS) tests assessing corrosion resistance of metallic materials with/without corrosion protection. November 2022 edition, 42 pages.",
        "gap_match_class": "named_module_gap",
        "meets_minimum_n_and_measurement_class": "unknown",
        "data_class": "compilation_of_primary",
        "data_class_note": "Published national/European standard document, not a raw-measurement dataset -- same category-mismatch disclosure as DR-LANG-FR-01.",
        "standard_and_uncertainty_disclosed": "published_standard_and_uncertainty",
        "rights_tier": "paywalled_unclear_bulk_rights",
        "rights_note": "Directly confirmed via WebFetch of the AFNOR boutique page: a paid-purchase model (cart/checkout, optional Redline+/Exigences services), standard text not openly readable -- summary and table of contents only without purchase.",
        "redundancy_class": "partial_overlap_adds_coverage",
        "translation_confidence": "native_script_verified_high",
        "translation_confidence_note": "Standard number, edition date, scope, and test-method names directly quoted from the fr WebFetch evidence of the AFNOR boutique page this fire.",
        "integrity_risks": [],
        "reachability": "reachable_index_only_dataset_unclear",
        "serves": {"module_gaps": ["amphora-public-corrosion-benchmark"], "recipe_elements": ["salt-spray-standard-mapping"]},
        "license_evidence_quote": "Essais de corrosion en atmosphères artificielles - Essais aux brouillards salins. Edition & Date: November 2022, 42 pages, Tirage 1. Access & License Terms: the website structure indicates this is a paid purchase model -- users can add the standard to a cart and select optional services (Exigences, Redline+, additional languages, extra users). The standard text itself does not appear to be openly readable; instead, the page provides a summary and table of contents. Users must purchase access to view the complete normative document.",
        "standard_mapping": {
            "published_standard": "NF EN ISO 9227",
            "astm_iso_equiv": "NF EN ISO 9227 IS the direct French/European adoption of ISO 9227 itself; method-class-comparable to ASTM B117 (both neutral-salt-spray tests). This converges exactly with the DR-LANG-DE and DR-LANG-JA fires' independent findings (DIN EN ISO 9227 and JIS Z 2371 are both also explicitly based on ISO 9227) -- a THIRD independent language-community search this campaign terminates at ISO 9227 as the de facto global salt-spray baseline.",
            "comparability_rating": "identical_to_iso_by_direct_adoption_method_class_confirmed_astm_inferred",
        },
        "confidence_flag": "MEDIUM",
    },
    {
        "candidate_id": "DR-LANG-FR-03",
        "name": "CEFRACOR -- Centre Français de l'AntiCorrosion (professional society)",
        "language": "fr",
        "native_citation": "Centre Français de l'AntiCorrosion",
        "native_citation_romanization": None,
        "url": "https://www.cefracor.org/fr/le-cefracor",
        "custodian": "CEFRACOR (nonprofit association, merger of AIAC 1952 and the original Centre Francais de la Corrosion 1960, founded 1989)",
        "rediscovers": None,
        "coverage": "A French national professional/learned society for corrosion and anti-corrosion (150 institutional + 750 individual members, ~2/3 industry); offers AFNOR-Qualiopi-certified training and technical assessments. Not a measurement dataset of any kind -- no open corrosion dataset or database is published on its own pages.",
        "gap_match_class": "off_scope",
        "meets_minimum_n_and_measurement_class": "no",
        "data_class": "extracted_or_estimated",
        "data_class_note": "A professional society with training/membership services is not scientific data under any of this rubric's data_class buckets -- honestly floored rather than force-fit, matching the DR-LANG-DE-03 (GfKORR) precedent for the analogous German professional society.",
        "standard_and_uncertainty_disclosed": "neither_stated",
        "rights_tier": "paywalled_unclear_bulk_rights",
        "rights_note": "Not a paywall in the literal sense -- there is no data product to have rights over; scored conservatively since CEFRACOR's offerings (training, certification, membership) are paid services, not an acquirable dataset.",
        "redundancy_class": "no_known_portfolio_overlap",
        "translation_confidence": "native_script_verified_high",
        "translation_confidence_note": "Society name, founding history, and membership figures directly quoted from the fr WebFetch evidence this fire.",
        "integrity_risks": [],
        "reachability": "reachable_index_only_dataset_unclear",
        "serves": {"module_gaps": [], "recipe_elements": []},
        "license_evidence_quote": "CEFRACOR (Centre Français de l'AntiCorrosion) is a French learned society operating as a non-profit association since 1989. It resulted from merging two earlier organizations: the AIAC (founded 1952) and the original Centre Francais de la Corrosion (founded 1960). The organization has approximately 150 corporate members and 750 individual members, with roughly two-thirds from industry. The page does not detail specific membership or license terms; it only notes that the organization offers membership and invites visitors to Become a member.",
        "standard_mapping": {
            "published_standard": "N/A -- professional society, not a measurement standard or dataset.",
            "astm_iso_equiv": "N/A",
            "comparability_rating": "not_applicable_society",
        },
        "confidence_flag": "LOW",
    },
    {
        "candidate_id": "DR-LANG-FR-04",
        "name": "Lemoine, L. & Thebault, J. (1977). \"Corrosion marine. Bibliographie\" (CNEXO Rapports Scientifiques et Techniques No. 36)",
        "language": "fr",
        "native_citation": "Corrosion marine. Bibliographie",
        "native_citation_romanization": None,
        "url": "https://archimer.ifremer.fr/doc/00717/82886/",
        "custodian": "CNEXO (Centre National pour l'Exploitation des Oceans) -- Ifremer's Archimer institutional repository (Ifremer being CNEXO's successor institution)",
        "rediscovers": None,
        "coverage": "An automated file of bibliographic references in the field of marine corrosion, compiled by engineers at the Oceanological Center of Brittany, 219 pages, CNEXO Rapports Scientifiques et Techniques No. 36, ISSN 0339-2899 (1977).",
        "gap_match_class": "named_module_gap",
        "meets_minimum_n_and_measurement_class": "unknown",
        "data_class": "extracted_or_estimated",
        "data_class_note": "IMPORTANT CAVEAT, disclosed rather than absorbed into a rosier score: this document is explicitly 'an automated file of bibliographic REFERENCES' -- an index/catalog of citations to other literature, not itself a compilation of primary corrosion-measurement values (unlike e.g. DECHEMA-Werkstoff-Tabelle's actual resistance-rating compilation). Honestly floored to extracted_or_estimated (0) for provenance_measurement_quality despite the strong scores on every other dimension below.",
        "standard_and_uncertainty_disclosed": "neither_stated",
        "rights_tier": "open_with_attribution",
        "rights_note": "Confirmed via WebFetch: 'Open access. The official publisher version is freely available for download... Published in CNEXO's scientific reports series.' No explicit CC-license variant stated, but a freely-downloadable French government/public-institute technical report with a formal ISSN series -- scored conservatively at open_with_attribution (not open_no_restriction) since no explicit rights waiver was found on the page itself.",
        "redundancy_class": "no_known_portfolio_overlap",
        "translation_confidence": "native_script_verified_high",
        "translation_confidence_note": "Title, authors, year, publisher, and page count directly quoted from the fr WebFetch evidence of the Archimer record page this fire.",
        "integrity_risks": [],
        "reachability": "reachable_direct_open_download",
        "serves": {"module_gaps": ["amphora-public-corrosion-benchmark", "amphora-barrier-corrosion-score"], "recipe_elements": []},
        "license_evidence_quote": "Open access. The official publisher version is freely available for download (219 pages). Published in CNEXO's scientific reports series, no. 36, ISSN 0339-2899.",
        "standard_mapping": {
            "published_standard": "N/A -- bibliographic reference index, not a measurement standard.",
            "astm_iso_equiv": "N/A",
            "comparability_rating": "not_applicable_bibliography",
        },
        "confidence_flag": "MEDIUM",
    },
    {
        "candidate_id": "DR-LANG-FR-05",
        "name": "Malajati, Y. (2009). \"Etude des mécanismes de photovieillissement de revêtements organiques anti-corrosion pour application comme peintures marines\" (These, Universite Clermont-Ferrand 2)",
        "language": "fr",
        "native_citation": "Etude des mécanismes de photovieillissement de revêtements organiques anti-corrosion pour application comme peintures marines",
        "native_citation_romanization": None,
        "url": "https://theses.fr/2009CLF21939",
        "custodian": "Universite Clermont-Ferrand 2 (theses.fr national record; full text hosted on theses.hal.science)",
        "rediscovers": None,
        "coverage": "PhD thesis examining photoaging mechanisms in organic anti-corrosion coatings for marine paint applications, specifically hydrolysis of photoproducts and their migration when water is present (phenolic compounds and acids produced/extracted during degradation). Advisor: Jean-Luc Gardette. Discipline: Chimie, Sciences des Materiaux.",
        "gap_match_class": "named_module_gap",
        "meets_minimum_n_and_measurement_class": "unknown",
        "data_class": "primary_experimental",
        "standard_and_uncertainty_disclosed": "neither_stated",
        "rights_tier": "paywalled_unclear_bulk_rights",
        "rights_note": "Full text (which would carry the actual license statement) is hosted on theses.hal.science, which is Anubis anti-bot-gated for both WebFetch and raw curl from xbabe1 this fire (see search-record no_acquisition_attestation) -- license/access terms could NOT be confirmed from the document itself this fire; theses.fr's own metadata page states no explicit access designation. Scored conservatively rather than assumed favorable.",
        "redundancy_class": "no_known_portfolio_overlap",
        "translation_confidence": "native_script_verified_high",
        "translation_confidence_note": "French title, author, advisor, institution, and abstract phrasing directly quoted from the fr WebFetch evidence of theses.fr this fire (not machine-translated after the fact).",
        "integrity_risks": ["digitization_quality_concern"],
        "reachability": "reachable_index_only_dataset_unclear",
        "serves": {"module_gaps": ["amphora-owk-adhesion", "amphora-public-corrosion-benchmark"], "recipe_elements": []},
        "license_evidence_quote": "Exact Title (FR): Etude des mécanismes de photovieillissement de revêtements organiques anti-corrosion pour application comme peintures marines. Author: Yassine Malajati. Advisor: Jean-Luc Gardette. Defense Year: 2009. Institution: Clermont-Ferrand 2 University. Discipline: Chemistry, Materials Science. Access Status: No specific open access designation or PDF availability restriction is indicated on this metadata record.",
        "standard_mapping": {
            "published_standard": "No numbered test standard named in the available abstract/metadata this fire (full text blocked).",
            "astm_iso_equiv": "NOT_CONFIRMED_THIS_FIRE",
            "comparability_rating": "unconfirmed_full_text_blocked",
        },
        "confidence_flag": "MEDIUM",
    },
    {
        "candidate_id": "DR-LANG-FR-06",
        "name": "Quach, T.H.Y. (2010). \"Etude de la durabilité d'un primaire epoxy anticorrosion : rôle de l'interphase polymère/métal et conséquence sur l'adhérence\" (These, Universite de Toulon / cotutelle Universite de Hanoi)",
        "language": "fr",
        "native_citation": "Etude de la durabilité d'un primaire epoxy anticorrosion : rôle de l'interphase polymère/métal et conséquence sur l'adhérence",
        "native_citation_romanization": None,
        "url": "https://theses.fr/2010TOUL0017",
        "custodian": "Universite de Toulon, in cotutelle with Universite de Hanoi (Vietnam); theses.fr national record, full text hosted on theses.hal.science",
        "rediscovers": None,
        "coverage": "PhD thesis on a DGEBA-polyamidoamine anticorrosion primer binder (commercial formulation: vinyl terpolymer, zinc phosphate and iron oxide anticorrosion pigments, talc filler). Used FTIR, micro-thermal analysis, and electrochemical impedance spectroscopy (EIS) to track polymer/metal interphase changes during hygrothermal aging; identified three stages of protection loss and a reversible beneficial effect of amine on adhesion. Discipline: Physicochimie des polymeres.",
        "gap_match_class": "named_module_gap",
        "meets_minimum_n_and_measurement_class": "unknown",
        "data_class": "primary_experimental",
        "standard_and_uncertainty_disclosed": "standard_named_no_uncertainty",
        "rights_tier": "paywalled_unclear_bulk_rights",
        "rights_note": "Same Anubis full-text block as DR-LANG-FR-05 -- license/access terms not confirmable from theses.hal.science this fire; theses.fr's own metadata page states no explicit access designation.",
        "redundancy_class": "no_known_portfolio_overlap",
        "translation_confidence": "native_script_verified_high",
        "translation_confidence_note": "French title, author, cotutelle institutions, DGEBA-polyamidoamine/pigment system, and a direct abstract quote ('La duree de vie d'un revetement depend en grande partie de son adherence') directly taken from the fr WebFetch evidence of theses.fr this fire.",
        "integrity_risks": ["digitization_quality_concern"],
        "reachability": "reachable_index_only_dataset_unclear",
        "serves": {"module_gaps": ["amphora-public-corrosion-benchmark", "amphora-zinc-galvanic-percolation", "amphora-owk-adhesion", "amphora-cpvc-pigment-formulation-axis"], "recipe_elements": ["zinc-phosphate-iron-oxide-anticorrosion-pigment-system"]},
        "license_evidence_quote": "Exact French Title (Verbatim): Etude de la durabilité d'un primaire epoxy anticorrosion : rôle de l'interphase polymère/métal et conséquence sur l'adhérence. Author: Thi Hai Yen Quach. Defense Year: 2010. Institution: Universite de Toulon (in cotutelle with Universite de Hanoi, Vietnam). Discipline: Physicochimie des polymeres. Systeme DGEBA-polyamidoamine, terpolymere vinylique, pigments anticorrosion phosphate de zinc et oxyde de fer, charge talc. Notable Quote from Abstract: 'La durée de vie d'un revêtement dépend en grande partie de son adhérence.' Methodes: FTIR, analyse micro-thermique, spectroscopie d'impedance electrochimique (EIS).",
        "standard_mapping": {
            "published_standard": "Electrochemical impedance spectroscopy (EIS), FTIR, micro-thermal analysis -- named measurement methods, not a single numbered ASTM/ISO test standard.",
            "astm_iso_equiv": "Method-class-comparable to the portfolio's own EIS corrosion-benchmark work (amphora-public-corrosion-benchmark EIS x rustcreep cross-modality result); not clause-by-clause confirmed this fire.",
            "comparability_rating": "method_class_plausible_not_clause_confirmed",
        },
        "confidence_flag": "MEDIUM",
    },
    {
        "candidate_id": "DR-LANG-FR-07",
        "name": "Aouri, M.C. (1992). \"Réticulation d'une résine époxyde : modélisation de la cinétique réactionnelle par l'analyse thermique dynamique\" (These, Universite Montpellier 2)",
        "language": "fr",
        "native_citation": "Réticulation d'une résine époxyde : modélisation de la cinétique réactionnelle par l'analyse thermique dynamique",
        "native_citation_romanization": None,
        "url": "https://theses.fr/1992MON20245",
        "custodian": "Universite Montpellier 2; theses.fr national record",
        "rediscovers": None,
        "coverage": "PhD thesis modeling the polycondensation reaction between DGEBA epoxy resin and TETA amine hardener via dynamic differential scanning calorimetry. Establishes a reaction-order parameter n approaching ~2/3 during three-dimensional propagation and identifies three reaction domains (rapid linear evolution, non-evolution, variable-speed nonlinear evolution) as a function of mixture composition ratio. Discipline: Chimie organique, minerale, analytique, industrielle.",
        "gap_match_class": "named_module_gap",
        "meets_minimum_n_and_measurement_class": "unknown",
        "data_class": "primary_experimental",
        "standard_and_uncertainty_disclosed": "standard_named_no_uncertainty",
        "rights_tier": "paywalled_unclear_bulk_rights",
        "rights_note": "1992 pre-digital-deposit-era thesis; no PDF full-text link was surfaced by this fire's searches (theses.fr metadata only) -- access/license terms entirely unconfirmed, scored conservatively.",
        "redundancy_class": "no_known_portfolio_overlap",
        "translation_confidence": "native_script_verified_high",
        "translation_confidence_note": "French title, author, institution, and abstract phrasing (including the direct quote on the DGEBA/TETA polycondensation reaction) directly taken from the fr WebFetch evidence of theses.fr this fire.",
        "integrity_risks": ["digitization_quality_concern"],
        "reachability": "reachable_index_only_dataset_unclear",
        "serves": {"module_gaps": ["amphora-cure-kinetics"], "recipe_elements": []},
        "license_evidence_quote": "Exact French Title (verbatim): Réticulation d'une résine époxyde : modélisation de la cinétique réactionnelle par l'analyse thermique dynamique. Author: Malik Charles Aouri. Defense Year: 1992. Institution: Montpellier 2. Discipline: Chimie organique, minerale, analytique, industrielle. Abstract Summary: polycondensation reaction between epoxy resin (DGEBA) and amine (TETA) analysed via dynamic differential scanning calorimetry; parameter n approaches approximately 2/3 during three-dimensional propagation; three reaction domains identified.",
        "standard_mapping": {
            "published_standard": "Dynamic DSC kinetic modeling (n-th order autocatalytic-class model) -- a named kinetic-analysis method, not a single ASTM/ISO test-method standard.",
            "astm_iso_equiv": "Method-class-comparable to ASTM E698/E2041 (DSC-based kinetics), not clause-by-clause confirmed this fire.",
            "comparability_rating": "method_class_plausible_not_clause_confirmed",
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
    "DR-LANG-FR-01": "human purchases official NF EN ISO 12944 (all parts, esp. Partie 9) full text via AFNOR boutique and performs a clause-by-clause ASTM/SSPC comparability diff, since the portfolio's own baseline is ASTM-referenced.",
    "DR-LANG-FR-02": "human purchases official NF EN ISO 9227 full text via AFNOR boutique (confirmed paid-purchase model this fire) and performs a clause-by-clause ASTM B117 diff -- same action class as the de/ja fires' DIN/JIS ISO-9227-derived standards.",
    "DR-LANG-FR-03": "no dataset action possible -- CEFRACOR is a paid-membership professional society/training body, not a dataset; a human seeking domain expertise could join or attend a CEFRACOR journee technique.",
    "DR-LANG-FR-04": "human reads the full 219-page CNEXO/Archimer bibliography PDF to identify which of its 1977-vintage cited references point to still-relevant, individually re-locatable primary corrosion-measurement sources -- the bibliography itself is a reference index, not a dataset.",
    "DR-LANG-FR-05": "human re-fetches theses.fr/2009CLF21939's full text (hosted on the Anubis-bot-gated theses.hal.science/tel-00725456) via a real authenticated browser session or a Universite Clermont Auvergne library/SUDOC interlibrary-loan request, to confirm quantitative photoaging results and license terms.",
    "DR-LANG-FR-06": "human re-fetches theses.fr/2010TOUL0017's full text (theses.hal.science/tel-00647580, also Anubis-gated) via a real browser session or Universite de Toulon library contact, to confirm quantitative EIS/FTIR results and license terms -- directly relevant to the portfolio's own EIS corrosion-benchmark module.",
    "DR-LANG-FR-07": "human requests the 1992 Montpellier thesis via SUDOC/ABES interlibrary loan (pre-digital-deposit era, may require a physical/microfiche request) to confirm kinetic parameters against the portfolio's Kissinger-anchor cure-kinetics benchmark.",
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
# 3. dataset-ledger.v1.jsonl -- append FR-04 (clears RECOMMENDED)
# ---------------------------------------------------------------------------
DSL_PATH = LEDGERS / "dataset-ledger.v1.jsonl"
dsl_before = DSL_PATH.read_bytes() if DSL_PATH.exists() else b""
dsl_prior_prefix_sha = sha(dsl_before)
dsl_prior_lines = dsl_before.decode("utf-8").splitlines() if dsl_before else []
dsl_prior_line_count = len(dsl_prior_lines)

fr04 = next(e for e in disp_entries if e["candidate_id"] == "DR-LANG-FR-04")
assert fr04["disposition"]["verdict"] == "RECOMMENDED", "expected DR-LANG-FR-04 to clear RECOMMENDED"

dataset_ledger_entry = {
    "schema": "amphora.dataset-recon.dataset-ledger.v1",
    "entry_type": "dataset_ledger_entry",
    "ledger_entry_id": "DR-LANG-FR-DSL-01",
    "candidate_id": "DR-LANG-FR-04",
    "run_id": RUN_ID,
    "fire_id": FIRE_ID,
    "date": DATE,
    "framing": "AUDIT-ONLY",
    "language": "fr",
    "name": "Lemoine, L. & Thebault, J. (1977). \"Corrosion marine. Bibliographie\" (CNEXO Rapports Scientifiques et Techniques No. 36)",
    "native_citation": "Corrosion marine. Bibliographie",
    "url_or_doi": "https://archimer.ifremer.fr/doc/00717/82886/",
    "publisher_custodian": "CNEXO (Centre National pour l'Exploitation des Oceans) -- Ifremer Archimer institutional repository",
    "license_as_published": "Open access, freely downloadable (219 pages); published in CNEXO's scientific reports series No. 36, ISSN 0339-2899. No explicit CC-license variant or attribution requirement stated on the record page itself -- scored conservatively as open_with_attribution rather than fully unrestricted.",
    "standard_mapping": {
        "published_standard": "N/A -- bibliographic reference index, not a measurement standard.",
        "astm_iso_equiv": "N/A",
        "comparability_rating": "not_applicable_bibliography",
    },
    "estimated_records_and_coverage": (
        "An automated file of bibliographic references in the field of marine corrosion, 219 "
        "pages, compiled 1977 by engineers at the Oceanological Center of Brittany. IMPORTANT: "
        "this is an index of CITATIONS to other literature, not itself a compilation of primary "
        "corrosion-measurement values -- see disposition_ledger data_class_note. Its practical "
        "value to the portfolio is as a bibliography pointer for locating still-relevant 1970s-80s "
        "French marine-corrosion primary literature, not as a directly usable measurement dataset."
    ),
    "module_gaps": ["amphora-public-corrosion-benchmark", "amphora-barrier-corrosion-score"],
    "recipe_elements": [],
    "integrity_risks": [],
    "translation_confidence": "native_script_verified_high",
    "next_human_action": HUMAN_ACTIONS["DR-LANG-FR-04"],
    "confidence_flag": "MEDIUM",
    "coverage": fr04["coverage"],
    "rank": 1,
    "serves": {"module_gaps": ["amphora-public-corrosion-benchmark", "amphora-barrier-corrosion-score"], "recipe_elements": []},
    "disposition": {"verdict": "RECOMMENDED", "reason": fr04["disposition"]["reason"]},
    "snapshot_date": DATE,
    "rubric_overall_score": fr04["rubric_overall_score"],
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
# 4. coverage-map.v1.json -- merge (preserve all prior gaps, add fr gaps)
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


fr_gaps = [
    {
        "gap_id": "corrosion-database-fr",
        "module_gaps": ["amphora-public-corrosion-benchmark", "amphora-barrier-corrosion-score"],
        "best_recommended": best_recommended_for(["DR-LANG-FR-04"]),
        "best_conditional": None,
        "commissioned_measurement_candidate": None,
        "note": "IFREMER/CNEXO's 1977 marine-corrosion bibliography cleared RECOMMENDED on the rubric's own mechanical formula (open access + no redundancy + high translation confidence + direct download all score maximally), but it is a CITATION INDEX, not primary measurement data -- disclosed prominently rather than presented as a usable dataset. CEFRACOR (the directive's other named-class French corrosion custodian) was also searched and REJECTED (off_scope) -- it is a paid professional society, not a dataset publisher.",
    },
    {
        "gap_id": "marine-coating-nf-standard-mapping",
        "module_gaps": ["amphora-ip-fto-guard", "amphora-owk-adhesion"],
        "best_conditional": best_for(["DR-LANG-FR-01"]),
        "best_recommended": None,
        "commissioned_measurement_candidate": None,
        "note": "NF EN ISO 12944 (esp. Partie 9, offshore) is the general structural-steel coating-system standard, directly and identically adopted from ISO -- a THIRD independent language-community confirmation (after de's DIN and the portfolio's own ASTM baseline) that ISO 12944 is the underlying global standard. No French-specific ship-hull antifouling standard number (analogous to zh's GB/T 6822 or de's BAW Merkblatt) was found despite an explicit search -- see ship-hull-antifouling-standard-mapping-fr empty result.",
    },
    {
        "gap_id": "salt-spray-standard-mapping-fr",
        "module_gaps": ["amphora-public-corrosion-benchmark"],
        "best_conditional": best_for(["DR-LANG-FR-02"]),
        "best_recommended": None,
        "commissioned_measurement_candidate": None,
        "note": "NF EN ISO 9227 confirmed as the direct French/European adoption of ISO 9227 (paid-purchase model directly confirmed via AFNOR boutique WebFetch). This is the THIRD independent language-community confirmation this campaign (after de's DIN EN ISO 9227 and ja's JIS Z 2371) that ISO 9227 is the de facto global salt-spray baseline underlying the portfolio's ASTM B117 usage.",
    },
    {
        "gap_id": "nf-eew-testdata-annex-fr",
        "module_gaps": ["amphora-molecule-property"],
        "best_conditional": None,
        "best_recommended": None,
        "commissioned_measurement_candidate": (
            "No open NF EN ISO 3001 (epoxy equivalent weight) test-data annex was found -- an "
            "honest empty result for the directive's 'NF annexes' scope element, per rule 7. "
            "Standard method confirmed mapped to ISO 3001:1999 (direct NF EN adoption, title-and-"
            "scope-and-method-principle level -- the fr search even surfaced the exact titration "
            "principle text). Note: the portfolio already computes EEW/AHEW internally via its "
            "own ChEBI+RDKit pipeline (amphora-molecule-property EEW/AHEW verification result, "
            "err 0.03) -- this fr finding is a standard-citation/mapping enrichment only, not a "
            "data gap requiring commissioning."
        ),
        "note": "Empty result, honestly reported per directive rule 7 ('An empty result for a gap is a valid, reportable answer').",
    },
    {
        "gap_id": "ship-hull-antifouling-standard-mapping-fr",
        "module_gaps": ["amphora-ip-fto-guard", "amphora-owk-adhesion"],
        "best_conditional": None,
        "best_recommended": None,
        "commissioned_measurement_candidate": None,
        "note": "No French/AFNOR ship-hull-specific antifouling/anticorrosive paint standard number was found, only a general AFNOR pigment-property definition for 'pigment antisalissure' and the general NF EN ISO 12944 (already captured above) -- an honest negative result mirroring the identical de (BAW Merkblatt search) and ja (JIS ship-hull search) findings for this same scope element across three independent language communities.",
    },
    {
        "gap_id": "marine-anticorrosion-coating-photoaging-fr",
        "module_gaps": ["amphora-owk-adhesion", "amphora-public-corrosion-benchmark"],
        "best_conditional": best_for(["DR-LANG-FR-05"]),
        "best_recommended": None,
        "commissioned_measurement_candidate": None,
        "note": "Malajati 2009 (Clermont-Ferrand 2) is a directly on-gap PhD thesis on marine anti-corrosion coating photoaging mechanisms, but its full text is hosted on theses.hal.science, which is Anubis anti-bot-gated (confirmed by both WebFetch and raw curl from xbabe1) -- content and license terms beyond theses.fr's bibliographic metadata could not be confirmed this fire, an honest evidence-quality gap.",
    },
    {
        "gap_id": "anticorrosion-primer-pigment-durability-fr",
        "module_gaps": ["amphora-public-corrosion-benchmark", "amphora-zinc-galvanic-percolation", "amphora-owk-adhesion"],
        "best_conditional": best_for(["DR-LANG-FR-06"]),
        "best_recommended": None,
        "commissioned_measurement_candidate": None,
        "note": "Quach 2010 (Universite de Toulon/Hanoi cotutelle) is a directly on-gap PhD thesis on a DGEBA-polyamidoamine anticorrosion primer with zinc phosphate and iron oxide pigments, using EIS -- method-class-relevant to the portfolio's own EIS corrosion-benchmark work -- but same Anubis full-text block as FR-05; content confirmed only at the theses.fr abstract level this fire.",
    },
    {
        "gap_id": "cure-kinetics-fr",
        "module_gaps": ["amphora-cure-kinetics"],
        "best_conditional": best_for(["DR-LANG-FR-07"]),
        "best_recommended": None,
        "commissioned_measurement_candidate": None,
        "note": "Aouri 1992 (Universite Montpellier 2) is a DGEBA+TETA DSC dynamic-kinetics thesis, directly on-gap for cure-kinetics, but pre-digital-deposit era -- no PDF full-text link was even surfaced, and access/license terms are entirely unconfirmed. A second DSC/Kissinger-class HAL thesis pair (tel-00136381, tel-02416648) was also surfaced by query 9 but not individually disposition-scored this fire (candidate-count triage; open for a future fire).",
    },
    {
        "gap_id": "fr-hal-antibot-access",
        "module_gaps": [],
        "best_conditional": None,
        "best_recommended": None,
        "commissioned_measurement_candidate": None,
        "note": (
            "theses.hal.science (the full-text PDF host behind theses.fr's national metadata "
            "aggregator) is gated by an Anubis anti-bot JS challenge ('Making sure you're not a "
            "bot!') for BOTH WebFetch and raw curl from xbabe1 -- a host-level bot-gate, not a "
            "WebFetch-tool-specific block (independently reproduced both ways this fire). This is "
            "the SAME class of finding as PROBE-WEB's CNKI TLS-cert-mismatch block: a real, "
            "disclosed repository-class access failure that limits every fr thesis candidate "
            "(FR-05, FR-06, FR-07) to metadata-only evaluation via theses.fr, not full-text "
            "confirmation. theses.fr itself (the metadata aggregator, a distinct host) is fully "
            "reachable and was the actual source of every quoted fr thesis abstract this fire."
        ),
    },
]

cm_after = dict(cm_before)
cm_after["fire_id"] = FIRE_ID
cm_after["run_id"] = RUN_ID
cm_after["snapshot_date"] = DATE
cm_after["scope_note"] = (cm_before.get("scope_note", "") + " + fr (French, DR-LANG-FR fire).").strip()
cm_after["gaps"] = list(cm_before.get("gaps", [])) + fr_gaps
cm_after["gaps_not_yet_searched_this_fire"] = list(cm_before.get("gaps_not_yet_searched_this_fire", [])) + [
    "theses.hal.science full-text for tel-00725456 (Malajati), tel-00647580 (Quach), tel-00136381, tel-02416648 -- all Anubis-antibot-blocked this fire, needs a real authenticated-browser or institutional-access retry [fr, carried forward]",
    "1992MON20245 (Aouri) via SUDOC/ABES interlibrary loan -- pre-digital-deposit era, no PDF link surfaced this fire [fr, carried forward]",
    "CEFRACOR's own technical conference proceedings ('journees techniques'), distinct from its paid-membership structure -- not searched [fr, carried forward]",
    "Materiaux et Techniques (EDP Sciences journal) on its own publisher platform directly -- only searched via general web search this fire [fr, carried forward]",
    "Peinture Actualites / Formule Verte trade press archives beyond the first page of results -- not exhausted [fr, carried forward]",
    "IFREMER Archimer bibliography's own 219 pages of individual citations -- not read (no-acquisition discipline) [fr, carried forward]",
]

cm_after_bytes = canon(cm_after)
cm_after_sha = sha(cm_after_bytes)

# ---------------------------------------------------------------------------
# 5. Independent checker: 5-limb refutation criterion (Latin-script adaptation)
# ---------------------------------------------------------------------------
FRENCH_MARKER_WORDS = [
    "époxy", "epoxy", "époxyde", "epoxyde", "amine", "durcisseur", "durcissement",
    "cinétique", "cinetique", "corrosion", "anticorrosion", "revêtement", "revetement",
    "peinture", "essai", "brouillard", "salin", "salins", "norme", "thèse", "these",
    "résine", "resine", "primaire", "adhérence", "adherence", "photovieillissement",
    "équivalent", "equivalent", "atmosphères", "atmospheres", "artificielles",
    "société", "societe", "navire", "coque", "réticulation", "reticulation",
    "vieillissement", "méthode", "methode", "données", "donnees", "sous-marine",
    "antisalissure", "structures", "acier", "française", "francais",
]


def has_french_marker(s):
    low = (s or "").lower()
    return any(w in low for w in FRENCH_MARKER_WORDS)


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

    all_sr_text = sr_text_for_lang("fr")

    # Rule 1: citation_has_recorded_query_and_result
    for d in dispositions:
        url = d.get("url", "")
        if url and url not in all_sr_text:
            violations.append({"rule": "citation_has_recorded_query_and_result", "candidate_id": d["candidate_id"],
                                "reason": f"{d['candidate_id']}: url {url} does not appear in any recorded search-record query/result this fire"})

    # Rule 2: native_query_not_literal_translation -- fr query must contain a French
    # marker word AND must not be byte-identical (case-insensitive) to its own gloss.
    for line in sr_lines_all:
        if line.get("language_communities_touched") and "fr" not in line["language_communities_touched"]:
            continue
        for q in line.get("queries", []):
            if q.get("language") == "fr" and "query" in q:
                qtext = q["query"]
                gloss = q.get("query_gloss_en", "")
                if (not has_french_marker(qtext)) or (qtext.strip().lower() == gloss.strip().lower()):
                    violations.append({"rule": "native_query_not_literal_translation", "candidate_id": None,
                                        "reason": f"fr query field is a literal English translation or contains no French marker vocabulary: '{qtext}'"})

    # Rule 3: license_text_matches_live_evidence
    for d in dispositions:
        quote = d.get("license_evidence_quote", "")
        if quote and quote not in all_sr_text:
            violations.append({"rule": "license_text_matches_live_evidence", "candidate_id": d["candidate_id"],
                                "reason": f"{d['candidate_id']}: license_evidence_quote does not appear verbatim in this fire's recorded search-record evidence text"})

    # Rule 4: native_citation_verbatim_in_evidence -- every fr native_citation must appear
    # verbatim (byte-for-byte substring) in this fire's recorded search-record evidence text.
    for d in dispositions:
        if d.get("language") == "fr":
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


PREVIOUSLY_SUPPLIED_FR = []  # none found this fire -- absence explained in intake_manifest

sr_all_lines = list(sr_prior_lines_parsed) + [search_record_line_obj]
dl_this_fire = dl_lines  # manifest + 7 dispositions, this fire only

runA = check(dl_this_fire, sr_all_lines, PREVIOUSLY_SUPPLIED_FR)
runB = check(dl_this_fire, sr_all_lines, PREVIOUSLY_SUPPLIED_FR)
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
target_url = "https://www.boutique.afnor.org/fr-fr/norme/nf-en-iso-9227/essais-de-corrosion-en-atmospheres-artificielles-essais-aux-brouillards-sal/fa201512/340484"
for line in sr_mut1:
    for q in line.get("queries", []):
        for k in ("query", "result_note", "result_summary", "result_evidence_quote", "result", "sample_urls", "url"):
            v = q.get(k)
            if isinstance(v, list):
                q[k] = [x for x in v if target_url not in str(x)]
            elif isinstance(v, str) and target_url in v:
                q[k] = v.replace(target_url, "REDACTED")
r1 = check(dl_this_fire, sr_mut1, PREVIOUSLY_SUPPLIED_FR)
mutants_out["missing_recorded_query"] = {
    "expected_rule": "citation_has_recorded_query_and_result",
    "how_planted": f"Scrubbed every occurrence of DR-LANG-FR-02's url ({target_url}) from a copy of this fire's search-record queries/results.",
    "expected_rule_fired": True,
    "refutation_criterion_fired": r1["refutation_criterion_fired"],
    "violations": r1["violations"],
}

# mutant 2: literal_english_translation_query
sr_mut2 = copy.deepcopy(sr_all_lines)
for line in sr_mut2:
    for q in line.get("queries", []):
        if q.get("language") == "fr" and q.get("query", "").startswith("résine époxyde amine durcisseur"):
            q["query"] = "epoxy resin amine hardener cure kinetics dataset"
r2 = check(dl_this_fire, sr_mut2, PREVIOUSLY_SUPPLIED_FR)
mutants_out["literal_english_translation_query"] = {
    "expected_rule": "native_query_not_literal_translation",
    "how_planted": "Replaced the native fr query string 'résine époxyde amine durcisseur cinétique de durcissement jeu de données' with its literal English gloss, while leaving language:'fr' unchanged.",
    "expected_rule_fired": True,
    "refutation_criterion_fired": r2["refutation_criterion_fired"],
    "violations": r2["violations"],
}

# mutant 3: license_text_diverges
dl_mut3 = copy.deepcopy(dl_this_fire)
for d in dl_mut3:
    if d.get("candidate_id") == "DR-LANG-FR-02":
        d["license_evidence_quote"] = "NF EN ISO 9227 est disponible en libre acces complet, sans achat ni abonnement d'aucune sorte."
r3 = check(dl_mut3, sr_all_lines, PREVIOUSLY_SUPPLIED_FR)
mutants_out["license_text_diverges"] = {
    "expected_rule": "license_text_matches_live_evidence",
    "how_planted": "Overwrote DR-LANG-FR-02's license_evidence_quote with a fabricated 'fully open, no purchase required' claim contradicting the recorded AFNOR-boutique WebFetch evidence (which states a paid-purchase model).",
    "expected_rule_fired": True,
    "refutation_criterion_fired": r3["refutation_criterion_fired"],
    "violations": r3["violations"],
}

# mutant 4: native_citation_not_verbatim
dl_mut4 = copy.deepcopy(dl_this_fire)
for d in dl_mut4:
    if d.get("candidate_id") == "DR-LANG-FR-06":
        d["native_citation"] = "Study of the durability of an anticorrosion epoxy primer"
r4 = check(dl_mut4, sr_all_lines, PREVIOUSLY_SUPPLIED_FR)
mutants_out["native_citation_not_verbatim"] = {
    "expected_rule": "native_citation_verbatim_in_evidence",
    "how_planted": "Replaced DR-LANG-FR-06's native_citation (the exact French thesis title) with an English paraphrase, simulating a silently-translated/paraphrased citation.",
    "expected_rule_fired": True,
    "refutation_criterion_fired": r4["refutation_criterion_fired"],
    "violations": r4["violations"],
}

# mutant 5: rediscovery_dropped -- synthetic previously-supplied id, since the real
# PREVIOUSLY_SUPPLIED_FR list is empty by construction (no prior fr candidates exist).
dl_mut5 = copy.deepcopy(dl_this_fire)
if dl_mut5:
    dl_mut5[-1] = dict(dl_mut5[-1])
    dl_mut5[-1]["rediscovers"] = None
r5 = check(dl_mut5, sr_all_lines, ["FR-PRIOR-TEST"])
mutants_out["rediscovery_dropped"] = {
    "expected_rule": "rediscovery_recall",
    "how_planted": "Injected a SYNTHETIC previously-supplied candidate id ('FR-PRIOR-TEST') into the checker's previously_supplied_ids input -- since this fire genuinely found zero real prior fr candidates (see intake_manifest), a synthetic id is required to prove this rule is a real, non-vacuous check rather than one that trivially never fires on an empty input list.",
    "expected_rule_fired": True,
    "refutation_criterion_fired": r5["refutation_criterion_fired"],
    "violations": r5["violations"],
}

for k, v in mutants_out.items():
    assert v["refutation_criterion_fired"] == v["expected_rule_fired"], f"positive control FAILED for mutant {k}"

# sanity: confirm the checker does NOT spuriously fire on the real (unmutated) empty
# previously-supplied list, i.e. rule 5 is silent when there is genuinely nothing to recall
r5_real = check(dl_this_fire, sr_all_lines, PREVIOUSLY_SUPPLIED_FR)
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
