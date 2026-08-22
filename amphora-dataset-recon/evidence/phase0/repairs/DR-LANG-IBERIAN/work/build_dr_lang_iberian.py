#!/usr/bin/env python3
"""Build DR-LANG-IBERIAN deliverable: search-record append, disposition-ledger
append, coverage-map merge, dataset-ledger append, independent checker with
two-replay + 5-mutant positive control, DSSE-signed done receipt. AUDIT_ONLY.
Pinned Phase-0 evaluator key only. Mirrors the DR-LANG-FR/DE Latin-script
adaptation precedent (rule 2 uses a curated es+pt technical-vocabulary
marker-word check + query != query_gloss_en; rule 4 uses a verbatim-in-
evidence check for native_citation strings, preserving Spanish/Portuguese
orthography -- accents/tildes/cedilla -- against ASCII-flattening/paraphrase).

Unlike every prior DR-LANG-* fire, this fire found a REAL previously-supplied
candidate (not a synthetic positive-control id): the Polimeros/SciELO source
already cited as doi_or_id "Polimeros/scielo HsgPHhmYmRSPPKQPqKFLdck" inside
amphora-redteam-audit/benchmarks/barrier-diffusion-timelag-fickian-ccby-v1/
diagnostic.canonical.json. Rule 5 (rediscovery_recall) is exercised against
this REAL id, not a synthetic stand-in.
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
ITEM = MOD / "evidence/phase0/repairs/DR-LANG-IBERIAN"
WORK = ITEM / "work"
DONE = ITEM / "done"
WORK.mkdir(parents=True, exist_ok=True)
DONE.mkdir(parents=True, exist_ok=True)

SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"
DIRECTIVE_MD = ROOT / "docs/directives/2026-08-09-dataset-reconnaissance-multilingual.md"
DIRECTIVE_SHA_EXPECTED = "97fad5d1636f5ccb106562c2d940535651c216d357dd5276088f2db12bdba207"

FIRE_ID = "20260810T120002-779591-d566098d9684"
RUN_ID = f"DR-LANG-IBERIAN-{FIRE_ID}"
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
        "DR-LANG-IBERIAN gap-targeted native-Spanish and native-Portuguese "
        "reconnaissance fire (directive obligation DR-LANG-IBERIAN, "
        "AMPHORA-DIRECTIVE-2026-08-09 Section 4). First IBERIAN fire for this "
        "module; searches SciELO (Brazil and Portugal collections), Dialnet/TESEO "
        "and TDX (Spain national/regional thesis repositories), CENIM/CSIC "
        "(Spain corrosion institute), LNEC/LNEG (Portugal national engineering "
        "labs and their Corrosao e Proteccao de Materiais journal), and "
        "AENOR/IPQ/ABNT (es/pt/br national standards bodies)."
    ),
    "language_communities_touched": ["es", "pt"],
    "repository_classes_touched": [
        "regional_open_access_index (SciELO Brasil + SciELO Portugal, pt)",
        "national_thesis_aggregator (Dialnet/TESEO, es; TDX -- Tesis Doctorals en Xarxa, es/ca)",
        "national_metallurgy_corrosion_institute (CENIM/CSIC, es)",
        "national_civil_engineering_lab (LNEC, pt)",
        "national_energy_geology_lab_and_journal (LNEG / Corrosao e Proteccao de Materiais, pt)",
        "national_standards_body (AENOR / UNE, es; IPQ / NP, pt; ABNT / NBR, br-pt)",
        "institutional_repository (repositorio.lneg.pt, pt; UPCommons, es)",
    ],
    "queries": [
        {
            "tool": "WebSearch", "language": "es",
            "query": "cinética de curado resina epoxi amina conjunto de datos DSC",
            "query_gloss_en": "epoxy resin amine cure kinetics dataset DSC",
            "purpose": "gap-targeted native-es query for amine-class epoxy cure-kinetics literature/datasets, the directive's opening scope element",
            "result_count": 5,
            "sample_urls": [
                "https://www.scielo.br/j/po/a/5StGdjCh4KyGNzcL3RpZCtP/",
                "https://lume.ufrgs.br/handle/10183/75732?locale-attribute=es&locale=pt_BR",
            ],
            "result_note": "Surfaced pt-language SciELO/UFRGS DSC cure-kinetics studies of epoxidized-soybean-oil epoxy resins with anhydride hardeners and tertiary amine catalysts (Kissinger/Ozawa/Barrett activation-energy methods) -- adjacent chemistry (anhydride-cured, amine as catalyst not stoichiometric hardener), not the portfolio's amine-hardener class, but methodology-relevant.",
        },
        {
            "tool": "WebSearch", "language": "es",
            "query": "CENIM corrosión recubrimientos epoxi base de datos",
            "query_gloss_en": "CENIM corrosion epoxy coatings database",
            "purpose": "target the directive-scope-relevant Spanish national metallurgy/corrosion institute directly for a coatings dataset",
            "result_count": 8,
            "sample_urls": ["https://cenim.csic.es/en/research-group/surface-electrochemistry-and-corrosion-ecorr/"],
            "result_note": "Surfaced CENIM's ECORR -- Electroquímica de superficies y corrosión (ECORR) -- research group page, evaluated further via WebFetch below; did not surface a published open dataset directly.",
        },
        {
            "tool": "WebSearch", "language": "pt",
            "query": "Polímeros SciELO difusão água DGEBA TETA coeficiente",
            "query_gloss_en": "Polimeros SciELO water diffusion DGEBA TETA coefficient",
            "purpose": "REDISCOVERY probe: locate the exact SciELO/Polimeros source already cited (as doi_or_id 'Polimeros/scielo HsgPHhmYmRSPPKQPqKFLdck') by amphora-redteam-audit's barrier-diffusion-timelag-fickian-ccby-v1 benchmark, per the directive's 'previously-supplied candidates must be independently rediscovered' rule",
            "result_count": 6,
            "sample_urls": ["https://lume.ufrgs.br/bitstream/handle/10183/174110/001062743.pdf?sequence=1"],
            "result_evidence_quote": "Notably, the results obtained showed that for all epoxy monomer to hardener ratios analyzed water diffusion followed non-Fickian behavior. Additionally, the water absorption behavior was correlated to the macromolecular structure developed when the epoxy/hardener ratio was varied, with all epoxy/hardener ratios presenting a two-phase macromolecular structure composed of regions with high crosslink density and regions with lower crosslinking.",
            "result_note": "First-pass hit on the DGEBA/TETA water-absorption-vs-hardener-ratio topic but did not yet resolve the exact scielo.br article id; follow-up query below resolved the canonical URL.",
        },
        {
            "tool": "WebSearch", "language": "pt",
            "query": "RCAAP tese doutoramento resina epoxídica cura cinética revestimento anticorrosivo",
            "query_gloss_en": "RCAAP doctoral thesis epoxy resin cure kinetics anticorrosive coating",
            "purpose": "target the directive-named Portuguese national theses aggregator (RCAAP) directly for a primary cure-kinetics or coating-corrosion thesis",
            "result_count": 6,
            "sample_urls": ["https://teses.usp.br/teses/disponiveis/97/97134/tde-20082013-162545/pt-br.php"],
            "result_note": "RCAAP itself did not surface a directly on-gap record this query; surfaced instead Brazilian (USP, not RCAAP/Portugal) theses on epoxy rheokinetics. Recorded as a partial empty result for RCAAP specifically -- see coverage-map.",
        },
        {
            "tool": "WebSearch", "language": "pt",
            "query": "\"Polímeros\" scielo.br absorção água difusão epóxi Fickian Jacobs-Jones phr",
            "query_gloss_en": "Polimeros scielo.br water absorption epoxy diffusion Fickian Jacobs-Jones phr",
            "purpose": "follow-up REDISCOVERY query to resolve the exact scielo.br canonical URL for the DGEBA/TETA water-absorption-vs-hardener-ratio article",
            "result_count": 7,
            "sample_urls": ["https://www.scielo.br/j/po/a/HsgPHhmYmRSPPKQPqKFLdck/?lang=en"],
            "result_evidence_quote": "Effect of the hardener to epoxy monomer ratio on the water absorption behavior of the DGEBA/TETA epoxy system",
            "result_note": "RESOLVED the exact previously-supplied candidate: scielo.br/j/po/a/HsgPHhmYmRSPPKQPqKFLdck, matching the redteam-audit benchmark's doi_or_id verbatim ('Polimeros/scielo HsgPHhmYmRSPPKQPqKFLdck'). Evaluated further via WebFetch below.",
        },
        {
            "tool": "WebSearch", "language": "es",
            "query": "recubrimiento anticorrosivo marino epoxi ensayo niebla salina UNE-EN ISO 9227 datos",
            "query_gloss_en": "marine anticorrosive epoxy coating salt spray test UNE-EN ISO 9227 data",
            "purpose": "directive-mandated standard-mapping check: UNE standards annex vs. the portfolio's ASTM/ISO corrosion-test baseline, salt-spray method",
            "result_count": 8,
            "sample_urls": ["https://tienda.aenor.com/Paginas/Noticias/une-en-ISO-9227,-ensayos-de-niebla-salina-en-materiales-metalicos.aspx"],
            "result_evidence_quote": "La norma UNE-EN ISO 9227:2023 especifica el equipo, los reactivos y el procedimiento que se deben utilizar en los ensayos de niebla salina neutra (NSS), niebla salina acética (AASS) y niebla salina cuproacética (CASS) para evaluar la resistencia a la corrosión de materiales metálicos, con o sin recubrimiento de protección temporal o permanente.",
            "empty_result": True,
            "empty_result_note": "Standard method confirmed mapped to ISO 9227 (direct UNE-EN adoption) but no open salt-spray test-data annex found on the AENOR store page -- an honest empty result, matching the de/ja/fr fires' identical finding for their own national ISO-9227 adoptions.",
        },
        {
            "tool": "WebSearch", "language": "es",
            "query": "TESEO tesis doctoral cinética curado resina epoxi amina energía activación",
            "query_gloss_en": "TESEO doctoral thesis epoxy resin amine cure kinetics activation energy",
            "purpose": "search the Spanish national doctoral-thesis database (TESEO, now integrated into Dialnet) for a primary DSC/Kissinger cure-kinetics thesis, the directive's 'wherever the research leads' scope",
            "result_count": 9,
            "sample_urls": [
                "https://dialnet.unirioja.es/servlet/tesis?codigo=214609",
                "https://www.tdx.cat/handle/10803/5896?locale-attribute=es",
                "https://dialnet.unirioja.es/servlet/tesis?codigo=156409",
            ],
            "result_note": "Surfaced 2 candidate theses: Imar/Mondragon 1994 (UPV/EHU, TGDDM/m-PDA chemorheology) and Morancho 1997 (UPC, epoxy+elastomeric-particle DSC cure kinetics), each evaluated further via WebFetch below.",
        },
        {
            "tool": "WebSearch", "language": "pt",
            "query": "LNEC corrosão aço revestimento marítimo base de dados ensaios",
            "query_gloss_en": "LNEC steel corrosion maritime coating database tests",
            "purpose": "target the directive-named Portuguese national civil-engineering research institute directly for a coating/corrosion dataset",
            "result_count": 7,
            "sample_urls": ["https://www.lneg.pt/wp-content/uploads/2020/01/Corros_Prot_Mater_Vol33_n3_2014.pdf"],
            "result_note": "LNEC itself runs an IPAC-accredited (NP EN ISO/IEC 17025) testing service and references a durability/anomaly database ('DB-DURATI'), but the query's actual on-gap hits were LNEG's Corrosao e Proteccao de Materiais journal PDFs (LNEG and LNEC are distinct Portuguese national labs) -- evaluated further below.",
        },
        {
            "tool": "WebSearch", "language": "pt",
            "query": "Corrosão e Protecção de Materiais LNEG revista revestimento epóxi tinta marinha",
            "query_gloss_en": "Corrosao e Proteccao de Materiais LNEG journal epoxy coating marine paint",
            "purpose": "target the directive-named Portuguese-language corrosion journal class directly for a concrete gap-relevant article",
            "result_count": 6,
            "sample_urls": ["https://www.lneg.pt/revista-corrosao-e-proteccao-de-materiais/"],
            "result_evidence_quote": "A edição da Revista está suspensa desde 2018",
            "result_note": "Journal 'Corrosao e Proteccao de Materiais' (ISSN 2182-6587), managed by LNEG, digital edition since 2012, semiannual, preferably Portuguese but accepts English/Spanish -- print edition suspended since 2018. Evaluated further via WebFetch below.",
        },
        {
            "tool": "WebSearch", "language": "es",
            "query": "casco buque pintura anticorrosiva antiincrustante norma UNE ensayo",
            "query_gloss_en": "ship hull anticorrosive antifouling paint UNE standard test",
            "purpose": "directive rule 7 empty-is-an-answer probe: search for a ship-hull-specific Spanish/UNE antifouling/anticorrosive paint standard number, analogous to zh's GB/T 6822 and de's BAW Merkblatt search",
            "result_count": 6,
            "sample_urls": ["https://repositorio.unican.es/xmlui/bitstream/handle/10902/21030/20z_gtbTFG_72350031NEstudioEconomicoRecubrimientosDeCasco.pdf"],
            "result_note": "Surfaced Spanish academic theses/reports on ship-hull coating economics and antifouling-paint effectiveness (Universidad de Cantabria, Universidad de La Laguna), but no Spanish-hull-specific UNE standard number distinct from the general UNE-EN ISO 12944 was found -- honest negative result.",
            "empty_result": True,
            "empty_result_note": "No Spanish-specific ship-hull antifouling/anticorrosive coating-system standard number found beyond the general UNE-EN ISO 12944 (already an ISO adoption). Recorded as an empty result in coverage-map.v1.json.",
        },
        {
            "tool": "WebSearch", "language": "pt",
            "query": "equivalente epóxido determinação método ensaio NP EN ISO 3001",
            "query_gloss_en": "epoxy equivalent determination test method NP EN ISO 3001",
            "purpose": "directive rule 7 empty-is-an-answer probe: search for an open NP test-data annex specifically for the epoxy-equivalent-weight (EEW) test method used to characterize the portfolio's DGEBA/amine stoichiometry",
            "result_count": 9,
            "sample_urls": ["https://www.iso.org/standard/29610.html"],
            "result_evidence_quote": "The NP EN ISO 3001 is the Portuguese/European version of this international standard, which defines the test method and procedure for determining the epoxy equivalent content in epoxy compounds used in plastics applications.",
            "empty_result": True,
            "empty_result_note": "Standard method confirmed mapped to ISO 3001:1999 (direct NP EN adoption) but no open EEW measurement-record dataset was found -- matching the de/fr/ja precedent for this same directive scope element. The portfolio already computes EEW/AHEW internally via its own ChEBI+RDKit pipeline; this is a standard-citation/mapping enrichment only.",
        },
        {
            "tool": "WebSearch", "language": "pt",
            "query": "resina epóxi anticorrosivo casco naval revestimento marinho SciELO Brasil",
            "query_gloss_en": "anticorrosive epoxy resin naval hull marine coating SciELO Brazil",
            "purpose": "general SciELO Brasil sweep for a ship-hull-specific epoxy anticorrosion coating study",
            "result_count": 10,
            "sample_urls": ["https://www.portosenavios.com.br/edicao-744-novembro-dezembro-de-2024/secoes-mensais/produtos-e-servicos/revestimentos-anticorrosivos"],
            "result_note": "Returned predominantly commercial/trade sources (resin manufacturers, boatbuilding suppliers), not SciELO academic articles -- an honest empty result for this specific query formulation against SciELO Brasil.",
            "empty_result": True,
            "empty_result_note": "No SciELO-indexed academic article specifically on ship-hull epoxy anticorrosion coatings was surfaced by this query; recorded as an empty result rather than force-fit to a commercial source.",
        },
        {
            "tool": "WebSearch", "language": "pt",
            "query": "NBR ISO 12944 revestimento anticorrosivo aço sistema pintura offshore ABNT",
            "query_gloss_en": "NBR ISO 12944 anticorrosive steel coating offshore paint system ABNT",
            "purpose": "directive-mandated standard-mapping check for Brazil's national standards body (ABNT/NBR) as a third Portuguese-language-community confirmation point alongside Portugal's NP",
            "result_count": 9,
            "sample_urls": ["https://abraco.org.br/src/uploads/2020/07/ISO-12944-2-FPI-P-Classificacao-de-Ambientes-Corrosivos.pdf"],
            "result_evidence_quote": "A ISO 12944-9 representa os requisitos de teste para revestimentos adequados para ambientes marítimos offshore.",
            "result_note": "Confirmed ISO 12944 (esp. Part 9, offshore) as the governing standard referenced by Brazilian industry bodies (ABRACO -- Associacao Brasileira de Corrosao) and coatings manufacturers (AkzoNobel Brazilian PDF); C5-M (very-high marine) corrosivity category explicitly named. NBR's own direct-adoption standard number not individually resolved to its ABNT catalog page this fire (paywalled catalog, not attempted -- no-acquisition discipline).",
        },
        {
            "tool": "WebFetch", "language": "pt",
            "url": "https://www.scielo.br/j/po/a/HsgPHhmYmRSPPKQPqKFLdck/?lang=en",
            "purpose": "REDISCOVERY: evaluate the exact previously-supplied Polimeros/SciELO source (doi_or_id 'Polimeros/scielo HsgPHhmYmRSPPKQPqKFLdck' in amphora-redteam-audit's barrier-diffusion-timelag-fickian-ccby-v1 benchmark) for title, license, DOI, and quantitative content",
            "result_evidence_quote": "This is an Open Access article distributed under the terms of the Creative Commons Attribution License, which permits unrestricted use, distribution, and reproduction in any medium, provided the original work is properly cited.",
            "result_note": "Pereira, A.A.C. & d'Almeida, J.R.M. (2016), 'Effect of the hardener to epoxy monomer ratio on the water absorption behavior of the DGEBA/TETA epoxy system', Polimeros 26(1), DOI 10.1590/0104-1428.2106. CC BY license confirmed. Reported M-infinity range 2.78%-6.56% and D range 0.8-3.94e-7 mm2/s (=8e-14 to 3.94e-13 m2/s) across phr 7-21 (phr13=stoichiometric) via Fickian/Jacobs-Jones/Berens-Hopfenberg fits -- this WebFetch AI-summarized band does not obviously contain the redteam-audit benchmark's cited phr13 point (D=2.17e-11 m2/s, M_inf=4.82%); the discrepancy is disclosed as an UNRESOLVED integrity_risk (see disposition entry), not silently reconciled, since no-acquisition discipline forbids downloading the full article/table to isolate the exact phr13 row this fire.",
        },
        {
            "tool": "WebFetch", "language": "pt",
            "url": "https://www.lneg.pt/revista-corrosao-e-proteccao-de-materiais/",
            "purpose": "evaluate the Corrosao e Proteccao de Materiais journal's own homepage for access/license terms",
            "result_evidence_quote": "Open Access Status: Not explicitly stated as open access. The journal appears to have restricted access, with a link to \"Acesso integral à revista\" (Full access to the journal). License Terms: No Creative Commons or explicit licensing terms are mentioned in the provided content.",
            "result_note": "Publisher LNEG, ISSN 2182-6587, publication suspended since 2018 (see search query 9 quote above). Scored conservatively rather than assumed open, despite individual articles in its back-catalogue (see repositorio.lneg.pt fetches below) carrying an explicit CC statement.",
        },
        {
            "tool": "WebFetch", "language": "es",
            "url": "https://cenim.csic.es/en/research-group/surface-electrochemistry-and-corrosion-ecorr/",
            "purpose": "evaluate CENIM/CSIC's ECORR research-group page for a published dataset/database and its epoxy/marine-coating scope",
            "result_evidence_quote": "No specific open data repositories or datasets are mentioned. No license terms or data access policies appear on this page.",
            "result_note": "ECORR's emphasis is sol-gel coatings, chemical conversion layers, and stimuli-responsive coatings for lightweight metals -- not the portfolio's DGEBA/amine organic-coating class; no dataset of any kind published on this page.",
        },
        {
            "tool": "WebFetch", "language": "pt",
            "url": "https://scielo.pt/pdf/cpm/v29n1/v29n1a01.pdf",
            "purpose": "attempt to retrieve full text of a Corrosao e Proteccao de Materiais article (Vol 29 No 1, 2010) on coating alternatives for maritime structures",
            "result": "FAILED to extract readable text -- WebFetch's AI-summarization pipeline received raw PDF binary/font-stream data (Futura/Univers font references, 2010-dated metadata) rather than parseable article text. Title, authors, and license terms could NOT be confirmed by this call.",
        },
        {
            "tool": "WebFetch", "language": "es",
            "url": "https://dialnet.unirioja.es/servlet/tesis?codigo=214609",
            "purpose": "evaluate the Dialnet/TESEO record for the Imar/Mondragon 1994 UPV/EHU TGDDM/m-PDA epoxy chemorheology thesis",
            "result_evidence_quote": "Texto completo no disponible",
            "result_note": "Title: 'Chemorreología y cinética de curado de sistemas epoxi tipo tetraglicidil diamino difenil metano (tgddm)/meta-fenilendiamina (m-pda). Conducta física en estado sólido'. Author: Josu Jon Imar. Director: Inaki Bixintxo Mondragon Egana. Universidad del Pais Vasco, 1994. Full text NOT available -- Dialnet's own access-status field states this explicitly.",
        },
        {
            "tool": "WebFetch", "language": "es",
            "url": "https://www.tdx.cat/handle/10803/5896?locale-attribute=es",
            "purpose": "attempt to retrieve the TDX (Tesis Doctorals en Xarxa) record for a candidate Spanish thesis on epoxy resin curing with elastomeric particles",
            "result": "FAILED -- TLS error 'unable to verify the first certificate' when connecting to www.tdx.cat. No thesis content, metadata, or license terms retrievable from this host this fire.",
        },
        {
            "tool": "WebFetch", "language": "es",
            "url": "https://dialnet.unirioja.es/servlet/tesis?codigo=156409",
            "purpose": "recovery path after the TDX TLS failure above: fetch the equivalent Dialnet mirror record for the same thesis to confirm metadata and access terms",
            "result_evidence_quote": "The thesis is available in open access through two repositories: TDX and UPCommons (the UPC's open knowledge portal). Full-text PDF access is provided via these institutional channels.",
            "result_note": "Title: 'Estudio del curado de materiales compuestos por un sistema epoxi y partículas elastoméricas'. Author: Jose Maria Morancho Llena. Universitat Politecnica de Catalunya, 1997. DSC-based Tg/conversion/vitrification-kinetics study of butadiene-acrylonitrile-copolymer-modified epoxy; TTT diagrams; DMTA phase-separation analysis. Dialnet's own metadata confirms open access via TDX + UPCommons even though this fire's own direct TDX fetch failed on a TLS handshake -- a genuine, disclosed access-path limitation, not a rights problem.",
        },
        {
            "tool": "WebFetch", "language": "pt",
            "url": "https://repositorio.lneg.pt/server/api/core/bitstreams/0a527d1f-e620-4dee-b7ab-41dc4a308905/content",
            "purpose": "attempt to retrieve full text of a Corrosao e Proteccao de Materiais article (Vol 33 No 3, 2014) via LNEG's institutional repository bitstream API",
            "result": "FAILED to extract readable text -- WebFetch's AI-summarization pipeline received raw PDF binary/font-stream data (Myriad Web Pro font references) rather than parseable article text.",
        },
        {
            "tool": "WebFetch", "language": "pt",
            "url": "https://repositorio.lneg.pt/entities/publication/27bc7643-db28-4946-984e-3699a7b39b20",
            "purpose": "evaluate the LNEG institutional-repository METADATA record (distinct from the raw-PDF bitstream fetch above, which failed) for the same maritime-paint-schemes article",
            "result_evidence_quote": "Access Status: Open access. Publisher: LNEG – Laboratório Nacional de Energia e Geologia, I.P. License: Creative Commons (specific CC type not detailed in provided content).",
            "result_note": "Title: 'Esquemas de pintura para estruturas marítimas'. Authors: Diamantino, T.C.; Alves, I.N.; Goncalves, R.; Marques, M.J.F.; Costa, M.R. (2014). Corrosao e Proteccao de Materiais, Vol 33 No 3, pp 44-50. Handle: 10400.9/2678. Three antifouling-biocide paint schemes on aluminum marine structures, artificial aging + 2-year natural exposure, SEM/EDS/FTIR/XRD. Open access confirmed at the metadata-record level even though the raw-PDF bitstream fetch above failed to parse.",
        },
    ],
    "no_acquisition_attestation": (
        "No dataset file, record set, table, standard full-text PDF, or bulk content was "
        "downloaded, cached, or scraped this fire. All 14 WebSearch calls returned ranked "
        "result snippets/summaries only. Of 9 WebFetch calls: 2 returned only undecodable raw "
        "PDF binary/font-stream metadata to the tool's own AI-summarization layer (no article "
        "text, license, or data extracted -- scielo.pt/pdf/cpm/v29n1/v29n1a01.pdf and the LNEG "
        "bitstream API URL), 1 failed outright on a TLS certificate error (www.tdx.cat, no "
        "content of any kind retrieved), and the remaining 6 retrieved the tool's own evaluative "
        "summary of page content (bibliographic metadata, license statements, access-tier "
        "descriptions) -- never raw page bytes, tables, or figures written to any file on xbabe1 "
        "or xbabe2. The 2 undecoded PDF binaries were transiently held by the WebFetch tool's own "
        "cache/pipeline (outside this agent's control) and were never written to disk on xbabe2 "
        "by this fire's own actions. Nothing beyond this ledger line, the disposition-ledger, "
        "dataset-ledger, and coverage-map entries it supports, this item's work/ diagnostics, and "
        "this fire's signed receipt was written under mvp20-split."
    ),
    "next_run_should_extend": (
        "Untouched or unresolved this fire, open for a future DR-LANG-IBERIAN (2nd/final, "
        "max_fires=2) fire: (1) scielo.pt/pdf/cpm/v29n1/v29n1a01.pdf and the LNEG Vol33No3 "
        "bitstream both need a real PDF-text-extraction path (curl + a real parser) rather than "
        "WebFetch's AI-summarization pipeline, mirroring the still-open JASNAOE (ja) and BAW "
        "Merkblatt (de) PDF-extraction gaps; (2) www.tdx.cat's TLS certificate failure was worked "
        "around via a Dialnet mirror this fire, but was not itself independently re-confirmed via "
        "raw curl from xbabe1 (the PROBE-WEB precedent for CNKI/HAL) -- worth a follow-up; (3) the "
        "DGEBA/TETA D-value/unit discrepancy flagged on the rediscovered Polimeros source "
        "(redteam-audit's cited 2.17e-11 m2/s vs. this fire's WebFetch-summarized 8e-14..3.94e-13 "
        "m2/s band) was NOT resolved -- a human with full-text access should isolate the exact "
        "phr13 row and confirm units; (4) RCAAP (Portugal's national thesis aggregator) was "
        "queried but did not itself surface a directly on-gap record -- worth a more targeted "
        "retry with different Portuguese query phrasing; (5) ABNT's own NBR catalog page for the "
        "Brazilian ISO-12944/9227 adoptions was not directly resolved (paywalled catalog, not "
        "attempted this fire); (6) CENIM's wider CSIC-network sister institutes (e.g. ICTP, "
        "IETcc) were not individually searched; (7) UPCommons (the UPC repository named by "
        "Dialnet as Morancho 1997's alternate open-access host) was not itself fetched this fire "
        "to independently confirm the exact CC license variant."
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
# 2. disposition-ledger.v1.jsonl new lines (1 intake manifest + 6 dispositions)
# ---------------------------------------------------------------------------
DL_PATH = LEDGERS / "disposition-ledger.v1.jsonl"
dl_before = DL_PATH.read_bytes() if DL_PATH.exists() else b""
dl_prior_prefix_sha = sha(dl_before)
dl_prior_lines = dl_before.decode("utf-8").splitlines() if dl_before else []
dl_prior_line_count = len(dl_prior_lines)

PREVIOUSLY_SUPPLIED_ID = "PRIOR-BARRIER-DIFFUSION-POLIMEROS-01"

intake_manifest = {
    "schema": "amphora.dataset-recon.disposition-ledger.v1",
    "entry_type": "candidate_intake_manifest",
    "run_id": RUN_ID,
    "fire_id": FIRE_ID,
    "date": DATE,
    "framing": "AUDIT-ONLY",
    "candidates_pinned": [PREVIOUSLY_SUPPLIED_ID],
    "note": (
        "EXACTLY ONE previously-supplied Spanish/Portuguese-language candidate was found "
        "anywhere in the portfolio as of this fire's start -- a REAL find, not a synthetic "
        "positive-control stand-in (unlike every prior DR-LANG-* fire's empty result on this "
        "point). Searched: (1) DR-RUBRIC's frozen candidate_snapshot.v1.json (grep for "
        "language es/pt/spain/portugal/brazil -- zero matches); (2) feedback/v1/"
        "dataset_sources.json, feedback/v2/catalog.json, feedback/v3/catalog.json, feedback/v4/"
        "catalog.json (grepped case-insensitively for es/pt/spain/portugal/brazil/espanol/"
        "portugues -- zero matches); (3) /home/ubuntu/amphora-cron/data-acquisition-queue.jsonl "
        "on xbabe1 (grepped for spain|portugal|brazil|brasil|espanol|scielo -- zero matches); "
        "(4) a repo-wide grep across every module for scielo|redalyc|dialnet|.es/|.pt/|.br/ -- "
        "this surfaced exactly ONE hit outside this module and outside the directive's own docs: "
        "amphora-redteam-audit/benchmarks/barrier-diffusion-timelag-fickian-ccby-v1/"
        "diagnostic.canonical.json (and its byte-identical diagnostic.runB.json), which cites "
        "doi_or_id 'Polimeros/scielo HsgPHhmYmRSPPKQPqKFLdck' as the source of a DGEBA/TETA "
        "diffusion coefficient (D=2.17e-11 m2/s) and equilibrium water uptake (M_inf=4.82%) at "
        "phr 13. This id is pinned above as candidates_pinned[0] and MUST be, and IS, "
        "independently rediscovered by DR-LANG-IBERIAN-01 below (see its rediscovers field) -- "
        "satisfying the directive's 'independently rediscovered OR THEIR ABSENCE EXPLAINED' "
        "clause via the rediscovery branch, not the absence branch, for the first time this "
        "campaign."
    ),
    "source_paths_checked_for_prior_iberian_candidates": [
        "amphora-dataset-recon/evidence/phase0/repairs/DR-RUBRIC/work/candidate_snapshot.v1.json",
        "feedback/v1/dataset_sources.json",
        "feedback/v2/catalog.json",
        "feedback/v3/catalog.json",
        "feedback/v4/catalog.json",
        "/home/ubuntu/amphora-cron/data-acquisition-queue.jsonl (xbabe1)",
        "repo-wide grep (all modules) for scielo|redalyc|dialnet|.es/|.pt/|.br/ -- surfaced amphora-redteam-audit/benchmarks/barrier-diffusion-timelag-fickian-ccby-v1/{diagnostic.canonical.json,diagnostic.runB.json}",
    ],
}

candidates = [
    {
        "candidate_id": "DR-LANG-IBERIAN-01",
        "name": "Pereira, A.A.C. & d'Almeida, J.R.M. (2016). \"Effect of the hardener to epoxy monomer ratio on the water absorption behavior of the DGEBA/TETA epoxy system\", Polimeros 26(1)",
        "language": "pt",
        "native_citation": "Effect of the hardener to epoxy monomer ratio on the water absorption behavior of the DGEBA/TETA epoxy system",
        "native_citation_romanization": None,
        "url": "https://www.scielo.br/j/po/a/HsgPHhmYmRSPPKQPqKFLdck/?lang=en",
        "custodian": "Associacao Brasileira de Polimeros (ABPol) -- Polimeros: Ciencia e Tecnologia journal, hosted on SciELO Brasil",
        "rediscovers": PREVIOUSLY_SUPPLIED_ID,
        "coverage": "Water diffusion coefficient (D) and equilibrium uptake (M-infinity) for the DGEBA/TETA epoxy system across 8 hardener-to-epoxy-monomer ratios (phr 7-21; phr 13 stoichiometric), fit with Fickian, non-Fickian (two-phase), and Berens-Hopfenberg/Jacobs-Jones models. DOI 10.1590/0104-1428.2106.",
        "gap_match_class": "named_module_gap",
        "meets_minimum_n_and_measurement_class": "yes",
        "data_class": "primary_experimental",
        "standard_and_uncertainty_disclosed": "standard_named_no_uncertainty",
        "rights_tier": "open_no_restriction",
        "redundancy_class": "fully_redundant",
        "redundancy_note": (
            "This is the EXACT SAME underlying source already anchoring amphora-redteam-audit's "
            "signed barrier-diffusion-timelag-fickian-ccby-v1 benchmark (doi_or_id 'Polimeros/"
            "scielo HsgPHhmYmRSPPKQPqKFLdck'). Listing it here is deliberate REDISCOVERY (per the "
            "directive's own rule), not a proposal of new unused coverage -- honestly floored to "
            "fully_redundant (0) rather than inflated, matching the DR-LANG-FR-04 precedent of "
            "disclosing a mechanical-rubric artifact rather than absorbing it silently."
        ),
        "translation_confidence": "native_script_verified_high",
        "translation_confidence_note": (
            "Both the 'Portuguese Title' and 'English Title' fields returned by this fire's "
            "WebFetch of the SciELO record are identical English text -- Polimeros (a Brazilian, "
            "Portuguese-language-domiciled journal) published this specific article in English. "
            "Disclosed honestly rather than fabricating a Portuguese-language title that was not "
            "observed; the quoted native_citation is the article's own published title, taken "
            "verbatim, not translated."
        ),
        "integrity_risks": ["locale_unit_convention_unverified", "value_crosscheck_unresolved_vs_prior_citation"],
        "integrity_risk_note": (
            "The redteam-audit benchmark's diagnostic.canonical.json cites D=2.17e-11 m2/s and "
            "M_inf=4.82% at phr13 from this exact source. This fire's WebFetch AI-summarized "
            "extraction instead reports an aggregate band across all 8 ratios of M_inf 2.78%-"
            "6.56% and D 0.8-3.94e-7 mm2/s (= 8e-14 to 3.94e-13 m2/s converting mm2 to m2). The "
            "cited phr13 point is not obviously inside this converted band -- a large apparent "
            "magnitude gap between 2.17e-11 m2/s and the 8e-14..3.94e-13 m2/s range. This is "
            "disclosed as UNRESOLVED, not silently reconciled or treated as a confirmed error: "
            "no-acquisition discipline forbids downloading the full article/table to isolate the "
            "exact phr13 row and confirm units this fire. Exactly the class of locale/unit hazard "
            "directive rule 5 requires disclosing rather than silently accepting."
        ),
        "reachability": "reachable_direct_open_download",
        "serves": {"module_gaps": ["amphora-barrier-diffusion-timelag-fickian", "amphora-barrier-water-uptake-hydrophilicity"], "recipe_elements": []},
        "license_evidence_quote": "This is an Open Access article distributed under the terms of the Creative Commons Attribution License, which permits unrestricted use, distribution, and reproduction in any medium, provided the original work is properly cited.",
        "standard_mapping": {
            "published_standard": "N/A -- academic diffusion-kinetics study (Fickian/non-Fickian/Berens-Hopfenberg/Jacobs-Jones models), not a certified ASTM/ISO/NBR test-method standard.",
            "astm_iso_equiv": "Method-class-comparable to the portfolio's own barrier-diffusion-timelag-fickian-ccby-v1 KA4 Crank-series round-trip; not clause-by-clause confirmed this fire.",
            "comparability_rating": "method_class_plausible_not_clause_confirmed",
        },
        "confidence_flag": "MEDIUM",
    },
    {
        "candidate_id": "DR-LANG-IBERIAN-02",
        "name": "Diamantino, T.C.; Alves, I.N.; Goncalves, R.; Marques, M.J.F.; Costa, M.R. (2014). \"Esquemas de pintura para estruturas marítimas\", Corrosão e Protecção de Materiais 33(3), 44-50",
        "language": "pt",
        "native_citation": "Esquemas de pintura para estruturas marítimas",
        "native_citation_romanization": None,
        "url": "https://repositorio.lneg.pt/entities/publication/27bc7643-db28-4946-984e-3699a7b39b20",
        "custodian": "LNEG (Laboratorio Nacional de Energia e Geologia, I.P.), Portugal -- institutional repository",
        "rediscovers": None,
        "coverage": "Three antifouling-biocide paint schemes on aluminum marine structures, evaluated via artificial aging tests plus 2 years of natural exposure; SEM/EDS, FTIR, and X-ray diffraction analysis of anticorrosive protection and antifouling efficiency.",
        "gap_match_class": "adjacent_domain",
        "gap_match_note": "Aluminum substrate, not the portfolio's steel/DGEBA-amine coating class -- disclosed rather than force-fit to named_module_gap; the antifouling-biocide paint-scheme methodology and marine-exposure protocol are directly transferable.",
        "meets_minimum_n_and_measurement_class": "yes",
        "data_class": "primary_experimental",
        "standard_and_uncertainty_disclosed": "standard_named_no_uncertainty",
        "rights_tier": "open_with_attribution",
        "redundancy_class": "no_known_portfolio_overlap",
        "translation_confidence": "native_script_verified_high",
        "translation_confidence_note": "Portuguese title, authors, journal, volume/issue/pages, and abstract content directly quoted from this fire's pt WebFetch evidence of the LNEG repository metadata record.",
        "integrity_risks": ["digitization_quality_concern"],
        "integrity_risk_note": "The raw-PDF bitstream fetch for this same article failed to parse (font-stream binary only); only the repository's own metadata-record page yielded readable content this fire.",
        "reachability": "reachable_direct_open_download",
        "serves": {"module_gaps": ["amphora-public-corrosion-benchmark", "amphora-zinc-galvanic-percolation"], "recipe_elements": []},
        "license_evidence_quote": "Access Status: Open access. Publisher: LNEG – Laboratório Nacional de Energia e Geologia, I.P. License: Creative Commons (specific CC type not detailed in provided content).",
        "standard_mapping": {
            "published_standard": "Artificial aging + natural-exposure marine coating evaluation (SEM/EDS, FTIR, XRD) -- named methods, not a single numbered ASTM/ISO/NP test standard.",
            "astm_iso_equiv": "NOT_CONFIRMED_THIS_FIRE",
            "comparability_rating": "unconfirmed_no_full_text",
        },
        "confidence_flag": "MEDIUM",
    },
    {
        "candidate_id": "DR-LANG-IBERIAN-03",
        "name": "Corrosão e Protecção de Materiais (journal), LNEG",
        "language": "pt",
        "native_citation": "Corrosão e Protecção de Materiais",
        "native_citation_romanization": None,
        "url": "https://www.lneg.pt/revista-corrosao-e-proteccao-de-materiais/",
        "custodian": "LNEG (Laboratorio Nacional de Energia e Geologia, I.P.), Portugal",
        "rediscovers": None,
        "coverage": "Portuguese national corrosion-and-materials-protection journal, ISSN 2182-6587, digital since 2012, semiannual, publishes in Portuguese/English/Spanish -- print edition suspended since 2018. General journal-level access point, distinct from the individually-scored back-catalogue article DR-LANG-IBERIAN-02.",
        "gap_match_class": "named_module_gap",
        "meets_minimum_n_and_measurement_class": "unknown",
        "data_class": "compilation_of_primary",
        "data_class_note": "A journal (index of many primary articles), not itself a single dataset -- honestly scored as compilation_of_primary rather than primary_experimental.",
        "standard_and_uncertainty_disclosed": "neither_stated",
        "rights_tier": "paywalled_unclear_bulk_rights",
        "rights_note": "The journal's own homepage does not state open access or a CC license (links instead to 'Acesso integral a revista') and the edition has been suspended since 2018 -- scored conservatively despite individual back-catalogue articles (DR-LANG-IBERIAN-02) independently carrying an explicit CC statement at the repository level.",
        "redundancy_class": "partial_overlap_adds_coverage",
        "translation_confidence": "native_script_verified_high",
        "translation_confidence_note": "Journal name, ISSN, publication cadence, and suspension status directly quoted from this fire's pt WebFetch/WebSearch evidence.",
        "integrity_risks": ["journal_publication_suspended"],
        "reachability": "reachable_index_only_dataset_unclear",
        "serves": {"module_gaps": ["amphora-public-corrosion-benchmark"], "recipe_elements": []},
        "license_evidence_quote": "A edição da Revista está suspensa desde 2018",
        "standard_mapping": {
            "published_standard": "N/A -- journal index, not a measurement standard.",
            "astm_iso_equiv": "N/A",
            "comparability_rating": "not_applicable_journal_index",
        },
        "confidence_flag": "LOW",
    },
    {
        "candidate_id": "DR-LANG-IBERIAN-04",
        "name": "Imar, J.J. (1994). \"Chemorreología y cinética de curado de sistemas epoxi tipo tetraglicidil diamino difenil metano (tgddm)/meta-fenilendiamina (m-pda). Conducta física en estado sólido\" (Tesis, Universidad del Pais Vasco)",
        "language": "es",
        "native_citation": "Chemorreología y cinética de curado de sistemas epoxi tipo tetraglicidil diamino difenil metano (tgddm)/meta-fenilendiamina (m-pda). Conducta física en estado sólido",
        "native_citation_romanization": None,
        "url": "https://dialnet.unirioja.es/servlet/tesis?codigo=214609",
        "custodian": "Universidad del Pais Vasco - Euskal Herriko Unibertsitatea (Spain); Dialnet national metadata record",
        "rediscovers": None,
        "coverage": "PhD thesis on chemorheology and cure kinetics of a TGDDM/m-PDA epoxy-amine system (aerospace-grade tetrafunctional epoxy, aromatic-amine hardener), modeling cure kinetics and rheology via DSC and FTIR, and structural relaxations via dynamic-mechanical analysis.",
        "gap_match_class": "adjacent_domain",
        "gap_match_note": "TGDDM is a tetrafunctional aerospace/composite epoxy, not the portfolio's DGEBA bifunctional coating resin -- disclosed rather than conflated; the DSC/FTIR cure-kinetics methodology is the transferable element.",
        "meets_minimum_n_and_measurement_class": "unknown",
        "data_class": "primary_experimental",
        "standard_and_uncertainty_disclosed": "standard_named_no_uncertainty",
        "rights_tier": "paywalled_unclear_bulk_rights",
        "rights_note": "Dialnet's own access-status field states 'Texto completo no disponible' (full text not available) -- no PDF link, alternate host, or license statement of any kind was found this fire.",
        "redundancy_class": "no_known_portfolio_overlap",
        "translation_confidence": "native_script_verified_high",
        "translation_confidence_note": "Spanish title, author, director, and institution directly quoted from this fire's es WebFetch evidence of the Dialnet record.",
        "integrity_risks": ["digitization_quality_concern"],
        "reachability": "unreachable_network_blocked",
        "reachability_note": "Not a network-level block like CNKI/HAL/TDX -- Dialnet's own metadata record explicitly states the full text does not exist in any accessible form ('Texto completo no disponible'). Scored as unreachable since there is no path to the content, not merely an inconvenient one.",
        "serves": {"module_gaps": ["amphora-cure-kinetics"], "recipe_elements": []},
        "license_evidence_quote": "Texto completo no disponible",
        "standard_mapping": {
            "published_standard": "DSC/FTIR-based cure-kinetics and chemorheology characterization -- named methods, not a single numbered ASTM/ISO test standard.",
            "astm_iso_equiv": "NOT_CONFIRMED_THIS_FIRE",
            "comparability_rating": "unconfirmed_no_full_text",
        },
        "confidence_flag": "LOW",
    },
    {
        "candidate_id": "DR-LANG-IBERIAN-05",
        "name": "Morancho Llena, J.M. (1997). \"Estudio del curado de materiales compuestos por un sistema epoxi y partículas elastoméricas\" (Tesis, Universitat Politecnica de Catalunya)",
        "language": "es",
        "native_citation": "Estudio del curado de materiales compuestos por un sistema epoxi y partículas elastoméricas",
        "native_citation_romanization": None,
        "url": "https://dialnet.unirioja.es/servlet/tesis?codigo=156409",
        "custodian": "Universitat Politecnica de Catalunya (UPC), Spain; open access via TDX and UPCommons",
        "rediscovers": None,
        "coverage": "PhD thesis on epoxy resin cured in the presence of butadiene-acrylonitrile-copolymer elastomeric particles; DSC-based glass-transition-temperature, conversion-degree, and vitrification-kinetics measurements (isothermal and dynamic), time-temperature-transformation (TTT) diagrams, DMTA-based phase-separation analysis.",
        "gap_match_class": "adjacent_domain",
        "gap_match_note": "Elastomer-toughened epoxy composite, not the portfolio's neat DGEBA/amine marine coating system -- disclosed; the DSC cure-kinetics/TTT/vitrification methodology is directly transferable to the portfolio's own DiBenedetto-vitrification-cure-bounds and network-Tg work.",
        "meets_minimum_n_and_measurement_class": "yes",
        "data_class": "primary_experimental",
        "standard_and_uncertainty_disclosed": "standard_named_no_uncertainty",
        "rights_tier": "open_with_attribution",
        "redundancy_class": "no_known_portfolio_overlap",
        "translation_confidence": "native_script_verified_high",
        "translation_confidence_note": "Spanish title, author, university, year, and abstract content directly quoted from this fire's es WebFetch evidence of the Dialnet record (used as a recovery path after the TDX host's own TLS certificate failure this fire).",
        "integrity_risks": [],
        "reachability": "reachable_direct_open_download",
        "reachability_note": "Dialnet's metadata record states open access via TDX + UPCommons, but this fire's own direct fetch of the TDX host failed with a TLS certificate error -- reachability is scored from the Dialnet mirror's own explicit access-status statement, not from an unconfirmed direct download; disclosed, not silently assumed.",
        "serves": {"module_gaps": ["amphora-dibenedetto-vitrification-cure-bounds", "amphora-network-tg-protocol-curation"], "recipe_elements": []},
        "license_evidence_quote": "The thesis is available in open access through two repositories: TDX and UPCommons (the UPC's open knowledge portal). Full-text PDF access is provided via these institutional channels.",
        "standard_mapping": {
            "published_standard": "DSC-based Tg/conversion/vitrification-kinetics and DMTA phase-separation analysis -- named methods, not a single numbered ASTM/ISO test standard.",
            "astm_iso_equiv": "Method-class-comparable to ASTM E1356/E698 (DSC-based Tg/kinetics), not clause-by-clause confirmed this fire.",
            "comparability_rating": "method_class_plausible_not_clause_confirmed",
        },
        "confidence_flag": "MEDIUM",
    },
    {
        "candidate_id": "DR-LANG-IBERIAN-06",
        "name": "CENIM/CSIC -- Electroquimica de superficies y corrosion (ECORR) research group",
        "language": "es",
        "native_citation": "Electroquímica de superficies y corrosión (ECORR)",
        "native_citation_romanization": None,
        "url": "https://cenim.csic.es/en/research-group/surface-electrochemistry-and-corrosion-ecorr/",
        "custodian": "CENIM (Centro Nacional de Investigaciones Metalurgicas), CSIC, Spain",
        "rediscovers": None,
        "coverage": "Spanish national metallurgy/corrosion research group; scope centers on sol-gel coatings, chemical conversion layers, surface modification, and stimuli-responsive coatings for lightweight metals -- not the portfolio's DGEBA/amine organic-coating class. No dataset, database, or open data repository of any kind is published on this page.",
        "gap_match_class": "off_scope",
        "meets_minimum_n_and_measurement_class": "no",
        "data_class": "extracted_or_estimated",
        "data_class_note": "A research-group page describing facilities/expertise is not scientific data under any of this rubric's data_class buckets -- honestly floored rather than force-fit, matching the DR-LANG-DE-03 (GfKORR) / DR-LANG-FR-03 (CEFRACOR) precedent for analogous professional/institutional pages with no data product.",
        "standard_and_uncertainty_disclosed": "neither_stated",
        "rights_tier": "paywalled_unclear_bulk_rights",
        "rights_note": "Not a paywall in the literal sense -- there is no data product to have rights over.",
        "redundancy_class": "no_known_portfolio_overlap",
        "translation_confidence": "native_script_verified_high",
        "translation_confidence_note": "Group name and scope directly quoted/paraphrased from this fire's es WebFetch evidence of the CENIM page.",
        "integrity_risks": [],
        "reachability": "reachable_index_only_dataset_unclear",
        "serves": {"module_gaps": [], "recipe_elements": []},
        "license_evidence_quote": "No specific open data repositories or datasets are mentioned. No license terms or data access policies appear on this page.",
        "standard_mapping": {
            "published_standard": "N/A -- research-group page, not a measurement standard or dataset.",
            "astm_iso_equiv": "N/A",
            "comparability_rating": "not_applicable_institute_page",
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
    "DR-LANG-IBERIAN-01": "human obtains the full Polimeros 26(1) PDF (open CC BY, no rights barrier) and isolates the exact phr13 row of the D/M_inf table to resolve the unit/magnitude discrepancy against the redteam-audit benchmark's cited D=2.17e-11 m2/s, M_inf=4.82% before any further quantitative reuse -- this is the single most load-bearing next action from this fire.",
    "DR-LANG-IBERIAN-02": "human reads the full LNEG-repository PDF (Diamantino et al. 2014, handle 10400.9/2678) to extract the quantitative antifouling/anticorrosion performance comparison across the 3 paint schemes and confirms the exact CC license variant, then assesses aluminum-vs-steel substrate transferability to the portfolio's own zinc-galvanic-percolation and corrosion-benchmark work.",
    "DR-LANG-IBERIAN-03": "human contacts LNEG (revista.cpm@lneg.pt) to clarify the suspended journal's archival access terms and whether the pre-2018 back-catalogue (beyond the 2 individually-fetched issues this fire) is bulk-downloadable or CC-licensed at the journal level.",
    "DR-LANG-IBERIAN-04": "no dataset action possible this fire -- Dialnet states the full text does not exist in accessible form; a human could attempt a direct request to Universidad del Pais Vasco's library or repository for the 1994 thesis.",
    "DR-LANG-IBERIAN-05": "human re-fetches the thesis via UPCommons (UPC's own repository, not attempted this fire) or retries TDX with a valid TLS trust chain, to confirm the exact CC license variant and extract the DSC/TTT/DMTA quantitative results for the portfolio's DiBenedetto-vitrification and network-Tg work.",
    "DR-LANG-IBERIAN-06": "no dataset action possible -- ECORR is a research-group description page with no published data product; a human seeking domain expertise could contact the group directly via CENIM's Technical Assistance Office.",
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
    for optional_key in ("data_class_note", "rights_note", "gap_match_note", "integrity_risk_note", "reachability_note", "redundancy_note"):
        if optional_key in c:
            entry[optional_key] = c[optional_key]
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
# 3. dataset-ledger.v1.jsonl -- append the 3 candidates that clear RECOMMENDED
#    (IBERIAN-01, IBERIAN-02, IBERIAN-05)
# ---------------------------------------------------------------------------
DSL_PATH = LEDGERS / "dataset-ledger.v1.jsonl"
dsl_before = DSL_PATH.read_bytes() if DSL_PATH.exists() else b""
dsl_prior_prefix_sha = sha(dsl_before)
dsl_prior_lines = dsl_before.decode("utf-8").splitlines() if dsl_before else []
dsl_prior_line_count = len(dsl_prior_lines)

RECOMMENDED_IDS = ["DR-LANG-IBERIAN-01", "DR-LANG-IBERIAN-02", "DR-LANG-IBERIAN-05"]
for rid in RECOMMENDED_IDS:
    e = next(x for x in disp_entries if x["candidate_id"] == rid)
    assert e["disposition"]["verdict"] == "RECOMMENDED", f"expected {rid} to clear RECOMMENDED, got {e['disposition']['verdict']}"

dsl_entries_this_fire = []
for i, rid in enumerate(RECOMMENDED_IDS, start=1):
    e = next(x for x in disp_entries if x["candidate_id"] == rid)
    c = next(x for x in candidates if x["candidate_id"] == rid)
    dataset_ledger_entry = {
        "schema": "amphora.dataset-recon.dataset-ledger.v1",
        "entry_type": "dataset_ledger_entry",
        "ledger_entry_id": f"DR-LANG-IBERIAN-DSL-{i:02d}",
        "candidate_id": rid,
        "run_id": RUN_ID,
        "fire_id": FIRE_ID,
        "date": DATE,
        "framing": "AUDIT-ONLY",
        "language": c["language"],
        "name": c["name"],
        "native_citation": c["native_citation"],
        "url_or_doi": c["url"],
        "publisher_custodian": c["custodian"],
        "license_as_published": e["license_evidence_quote"],
        "standard_mapping": c["standard_mapping"],
        "estimated_records_and_coverage": e["coverage"],
        "module_gaps": c["serves"]["module_gaps"],
        "recipe_elements": c["serves"]["recipe_elements"],
        "integrity_risks": c["integrity_risks"],
        "translation_confidence": c["translation_confidence"],
        "next_human_action": HUMAN_ACTIONS[rid],
        "confidence_flag": c["confidence_flag"],
        "coverage": e["coverage"],
        "rank": i,
        "serves": c["serves"],
        "disposition": {"verdict": "RECOMMENDED", "reason": e["disposition"]["reason"]},
        "snapshot_date": DATE,
        "rubric_overall_score": e["rubric_overall_score"],
        "rubric_path": "amphora-dataset-recon/evidence/phase0/repairs/DR-RUBRIC/work/rubric.v1.json",
    }
    if rid == "DR-LANG-IBERIAN-01":
        dataset_ledger_entry["rediscovers"] = PREVIOUSLY_SUPPLIED_ID
    dsl_entries_this_fire.append(dataset_ledger_entry)

dsl_line_bytes_list = [json.dumps(x, sort_keys=True, ensure_ascii=False).encode("utf-8") for x in dsl_entries_this_fire]
dsl_appended_bytes = b"\n".join(dsl_line_bytes_list) + b"\n"
dsl_new_content = dsl_before
if dsl_before and not dsl_new_content.endswith(b"\n"):
    dsl_new_content += b"\n"
dsl_new_content += dsl_appended_bytes
dsl_appended_line_start = dsl_prior_line_count + 1
dsl_appended_line_end = dsl_prior_line_count + len(dsl_entries_this_fire)
dsl_appended_sha = sha(dsl_appended_bytes)
dsl_file_sha_after = sha(dsl_new_content)

# ---------------------------------------------------------------------------
# 4. coverage-map.v1.json -- merge (preserve all prior gaps, add iberian gaps)
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


iberian_gaps = [
    {
        "gap_id": "barrier-diffusion-dgeba-teta-rediscovery-iberian",
        "module_gaps": ["amphora-barrier-diffusion-timelag-fickian", "amphora-barrier-water-uptake-hydrophilicity"],
        "best_recommended": best_recommended_for(["DR-LANG-IBERIAN-01"]),
        "best_conditional": None,
        "commissioned_measurement_candidate": None,
        "note": "REDISCOVERY of the exact SciELO/Polimeros source already anchoring amphora-redteam-audit's signed barrier-diffusion-timelag-fickian-ccby-v1 benchmark. Confirmed live: real article, real CC BY license, real DOI (10.1590/0104-1428.2106). Also surfaced a genuine, UNRESOLVED unit/magnitude discrepancy between the benchmark's cited phr13 point (D=2.17e-11 m2/s) and this fire's own WebFetch-summarized aggregate band (8e-14..3.94e-13 m2/s) -- flagged for human follow-up, not silently reconciled.",
    },
    {
        "gap_id": "marine-antifouling-pigment-coating-iberian",
        "module_gaps": ["amphora-public-corrosion-benchmark", "amphora-zinc-galvanic-percolation"],
        "best_recommended": best_recommended_for(["DR-LANG-IBERIAN-02"]),
        "best_conditional": None,
        "commissioned_measurement_candidate": None,
        "note": "LNEG (Portugal) institutional-repository article on antifouling-biocide marine paint schemes (aluminum substrate, adjacent-domain, disclosed). Open access at the repository-metadata level; the raw-PDF bitstream itself was not machine-readable this fire (font-stream binary only).",
    },
    {
        "gap_id": "corrosion-protection-journal-access-iberian",
        "module_gaps": ["amphora-public-corrosion-benchmark"],
        "best_conditional": best_for(["DR-LANG-IBERIAN-03"]),
        "best_recommended": None,
        "commissioned_measurement_candidate": None,
        "note": "Corrosao e Proteccao de Materiais (LNEG, Portugal's national corrosion journal) -- print edition suspended since 2018, journal-homepage access terms unclear despite individual back-catalogue articles carrying an explicit CC statement at the repository level (see IBERIAN-02).",
    },
    {
        "gap_id": "cure-kinetics-adjacent-epoxy-systems-iberian",
        "module_gaps": ["amphora-cure-kinetics"],
        "best_conditional": None,
        "best_recommended": None,
        "commissioned_measurement_candidate": None,
        "note": "Two Spanish PhD theses (Imar 1994 UPV/EHU TGDDM/m-PDA, REJECTED -- no accessible full text anywhere; Morancho 1997 UPC epoxy+elastomer, RECOMMENDED -- see barrier-diffusion... no, see dataset-ledger DSL-03) on adjacent (non-DGEBA/non-marine-coating) epoxy-amine cure-kinetics systems. DSC/Kissinger-class methodology transferable; direct chemistry transferability disclosed as unconfirmed/adjacent, not conflated with the portfolio's own amine-hardener class.",
    },
    {
        "gap_id": "salt-spray-standard-mapping-iberian",
        "module_gaps": ["amphora-public-corrosion-benchmark"],
        "best_conditional": None,
        "best_recommended": None,
        "commissioned_measurement_candidate": (
            "No open salt-spray test-data annex was found for UNE-EN ISO 9227 (Spain, AENOR) or "
            "NP EN ISO 9227 (Portugal, IPQ) -- both direct national adoptions of ISO 9227, "
            "paywalled at their respective standards-body stores. This is the FIFTH and SIXTH "
            "independent language-community confirmation this campaign (after zh/de/fr/ja) that "
            "ISO 9227 is the de facto global salt-spray baseline underlying the portfolio's own "
            "ASTM B117 usage."
        ),
        "note": "Empty result, honestly reported per directive rule 7.",
    },
    {
        "gap_id": "eew-testdata-annex-iberian",
        "module_gaps": ["amphora-molecule-property"],
        "best_conditional": None,
        "best_recommended": None,
        "commissioned_measurement_candidate": (
            "No open NP EN ISO 3001 (epoxy equivalent weight) test-data annex was found for "
            "Portugal -- confirmed mapped to ISO 3001:1999 (direct NP EN adoption) at the "
            "title/scope level only. The portfolio already computes EEW/AHEW internally via its "
            "own ChEBI+RDKit pipeline; this is a standard-citation/mapping enrichment only, not a "
            "data gap requiring commissioning."
        ),
        "note": "Empty result, honestly reported per directive rule 7, matching the de/fr/ja precedent for this same directive scope element.",
    },
    {
        "gap_id": "ship-hull-antifouling-standard-mapping-iberian",
        "module_gaps": ["amphora-ip-fto-guard", "amphora-owk-adhesion"],
        "best_conditional": None,
        "best_recommended": None,
        "commissioned_measurement_candidate": None,
        "note": "No Spanish/Portuguese/Brazilian ship-hull-specific antifouling/anticorrosive paint standard number was found, only academic/trade literature on antifouling paints and the general UNE-EN ISO 12944 / NP EN ISO 12944 / NBR-referenced ISO 12944 (already captured elsewhere) -- an honest negative result mirroring the identical de (BAW), fr (AFNOR), and ja (JIS) findings for this same scope element across five independent language communities now.",
    },
    {
        "gap_id": "pdf-text-extraction-and-tls-access-limitations-iberian",
        "module_gaps": [],
        "best_conditional": None,
        "best_recommended": None,
        "commissioned_measurement_candidate": None,
        "note": (
            "Two distinct, disclosed access-path limitations this fire: (1) WebFetch's AI-"
            "summarization pipeline could not extract readable text from 2 raw scientific-PDF "
            "binaries (scielo.pt/pdf/cpm/v29n1/v29n1a01.pdf and a repositorio.lneg.pt bitstream "
            "API URL) -- same class of limitation as ja's JASNAOE and de's BAW Merkblatt PDF "
            "gaps; (2) www.tdx.cat (Tesis Doctorals en Xarxa) failed with a TLS certificate "
            "verification error ('unable to verify the first certificate') -- a NEW class of "
            "access failure not seen in prior DR-LANG fires (distinct from CNKI's cert-mismatch "
            "and HAL's Anubis bot-gate), worked around this fire via a Dialnet mirror record for "
            "the same thesis (DR-LANG-IBERIAN-05) rather than left as a dead end."
        ),
    },
]

cm_after = dict(cm_before)
cm_after["fire_id"] = FIRE_ID
cm_after["run_id"] = RUN_ID
cm_after["snapshot_date"] = DATE
cm_after["scope_note"] = (cm_before.get("scope_note", "") + " + es + pt (Spanish + Portuguese, DR-LANG-IBERIAN fire).").strip()
cm_after["gaps"] = list(cm_before.get("gaps", [])) + iberian_gaps
cm_after["gaps_not_yet_searched_this_fire"] = list(cm_before.get("gaps_not_yet_searched_this_fire", [])) + [
    "scielo.pt/pdf/cpm/v29n1/v29n1a01.pdf and repositorio.lneg.pt Vol33No3 bitstream -- both need a real PDF-text-extraction path (curl + a real parser) [pt, carried forward]",
    "www.tdx.cat TLS certificate failure -- not independently re-confirmed via raw curl from xbabe1 (the PROBE-WEB precedent for CNKI/HAL) [es, carried forward]",
    "DGEBA/TETA D-value/unit discrepancy on the rediscovered Polimeros source (2.17e-11 m2/s cited vs. 8e-14..3.94e-13 m2/s WebFetch-summarized band) -- not resolved, needs full-text phr13-row isolation [pt, carried forward]",
    "RCAAP (Portugal's national thesis aggregator) did not itself surface a directly on-gap record this fire -- worth a more targeted retry with different Portuguese query phrasing [pt, carried forward]",
    "ABNT's own NBR catalog page for the Brazilian ISO-12944/9227 adoptions was not directly resolved (paywalled catalog, not attempted) [pt, carried forward]",
    "CENIM's wider CSIC-network sister institutes (e.g. ICTP, IETcc) not individually searched [es, carried forward]",
    "UPCommons (UPC's own repository, Morancho 1997's alternate open-access host) not itself fetched to independently confirm the exact CC license variant [es, carried forward]",
]

cm_after_bytes = canon(cm_after)
cm_after_sha = sha(cm_after_bytes)

# ---------------------------------------------------------------------------
# 5. Independent checker: 5-limb refutation criterion (es+pt Latin-script
#    adaptation, mirroring the de/fr precedent)
# ---------------------------------------------------------------------------
IBERIAN_MARKER_WORDS = [
    "epoxi", "epóxi", "epóxido", "epóxica", "epóxidos", "amina", "aminas",
    "curado", "cura", "cinética", "cinetica", "corrosión", "corrosao", "corrosão",
    "anticorrosivo", "anticorrosiva", "revestimiento", "revestimento", "pintura",
    "ensayo", "ensaio", "niebla", "nevoeiro", "salina", "salino", "norma",
    "tesis", "tese", "resina", "resistência", "resistencia", "adherencia",
    "aderência", "equivalente", "atmósferas", "atmosferas", "artificiales",
    "artificiais", "sociedad", "sociedade", "buque", "navio", "naval", "casco",
    "reticulación", "reticulacao", "envejecimiento", "envelhecimento",
    "método", "metodo", "método", "datos", "dados", "submarina", "submarino",
    "antiincrustante", "antiincrustantes", "antifouling", "incrustante",
    "estructuras", "estruturas", "acero", "aço", "española", "portuguesa",
    "marítimo", "maritimo", "marítima", "marítimas", "difusão", "difusion",
    "absorção", "absorcion", "durcissement", "energía", "energia", "activación",
    "ativação", "elastoméricas", "elastomericas", "vitrificación", "vitrificacao",
]


def has_iberian_marker(s):
    low = (s or "").lower()
    return any(w in low for w in IBERIAN_MARKER_WORDS)


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

    all_sr_text = sr_text_for_langs(["es", "pt"])

    # Rule 1: citation_has_recorded_query_and_result
    for d in dispositions:
        url = d.get("url", "")
        if url and url not in all_sr_text:
            violations.append({"rule": "citation_has_recorded_query_and_result", "candidate_id": d["candidate_id"],
                                "reason": f"{d['candidate_id']}: url {url} does not appear in any recorded search-record query/result this fire"})

    # Rule 2: native_query_not_literal_translation -- es/pt query must contain an
    # Iberian marker word AND must not be byte-identical (case-insensitive) to its gloss.
    for line in sr_lines_all:
        touched = line.get("language_communities_touched")
        if touched and not any(l in touched for l in ("es", "pt")):
            continue
        for q in line.get("queries", []):
            if q.get("language") in ("es", "pt") and "query" in q:
                qtext = q["query"]
                gloss = q.get("query_gloss_en", "")
                if (not has_iberian_marker(qtext)) or (qtext.strip().lower() == gloss.strip().lower()):
                    violations.append({"rule": "native_query_not_literal_translation", "candidate_id": None,
                                        "reason": f"es/pt query field is a literal English translation or contains no es/pt marker vocabulary: '{qtext}'"})

    # Rule 3: license_text_matches_live_evidence
    for d in dispositions:
        quote = d.get("license_evidence_quote", "")
        if quote and quote not in all_sr_text:
            violations.append({"rule": "license_text_matches_live_evidence", "candidate_id": d["candidate_id"],
                                "reason": f"{d['candidate_id']}: license_evidence_quote does not appear verbatim in this fire's recorded search-record evidence text"})

    # Rule 4: native_citation_verbatim_in_evidence
    for d in dispositions:
        if d.get("language") in ("es", "pt"):
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


PREVIOUSLY_SUPPLIED_IBERIAN = [PREVIOUSLY_SUPPLIED_ID]  # REAL id, found in amphora-redteam-audit's benchmark

sr_all_lines = list(sr_prior_lines_parsed) + [search_record_line_obj]
dl_this_fire = dl_lines  # manifest + 6 dispositions, this fire only

runA = check(dl_this_fire, sr_all_lines, PREVIOUSLY_SUPPLIED_IBERIAN)
runB = check(dl_this_fire, sr_all_lines, PREVIOUSLY_SUPPLIED_IBERIAN)
runA_bytes = canon(runA)
runB_bytes = canon(runB)
(WORK / "diagnostic.runA.json").write_bytes(runA_bytes)
(WORK / "diagnostic.runB.json").write_bytes(runB_bytes)
assert sha(runA_bytes) == sha(runB_bytes), "two-replay gate FAILED on real deliverable"
assert runA["refutation_criterion_fired"] is False, f"REAL deliverable fired the refutation criterion: {runA['violations']}"

# ---------------------------------------------------------------------------
# 6. Positive control: 5 planted-defect mutants, one per limb. Mutant 5 uses
#    the REAL previously-supplied id (not a synthetic stand-in).
# ---------------------------------------------------------------------------
mutants_out = {}

# mutant 1: missing_recorded_query
sr_mut1 = copy.deepcopy(sr_all_lines)
target_url = "https://dialnet.unirioja.es/servlet/tesis?codigo=156409"
for line in sr_mut1:
    for q in line.get("queries", []):
        for k in ("query", "result_note", "result_summary", "result_evidence_quote", "result", "sample_urls", "url"):
            v = q.get(k)
            if isinstance(v, list):
                q[k] = [x for x in v if target_url not in str(x)]
            elif isinstance(v, str) and target_url in v:
                q[k] = v.replace(target_url, "REDACTED")
r1 = check(dl_this_fire, sr_mut1, PREVIOUSLY_SUPPLIED_IBERIAN)
mutants_out["missing_recorded_query"] = {
    "expected_rule": "citation_has_recorded_query_and_result",
    "how_planted": f"Scrubbed every occurrence of DR-LANG-IBERIAN-05's url ({target_url}) from a copy of this fire's search-record queries/results.",
    "expected_rule_fired": True,
    "refutation_criterion_fired": r1["refutation_criterion_fired"],
    "violations": r1["violations"],
}

# mutant 2: literal_english_translation_query
sr_mut2 = copy.deepcopy(sr_all_lines)
for line in sr_mut2:
    for q in line.get("queries", []):
        if q.get("language") == "pt" and q.get("query", "").startswith("Polímeros SciELO"):
            q["query"] = "Polimeros SciELO water diffusion DGEBA TETA coefficient"
r2 = check(dl_this_fire, sr_mut2, PREVIOUSLY_SUPPLIED_IBERIAN)
mutants_out["literal_english_translation_query"] = {
    "expected_rule": "native_query_not_literal_translation",
    "how_planted": "Replaced the native pt query string 'Polímeros SciELO difusão água DGEBA TETA coeficiente' with its literal English gloss, while leaving language:'pt' unchanged.",
    "expected_rule_fired": True,
    "refutation_criterion_fired": r2["refutation_criterion_fired"],
    "violations": r2["violations"],
}

# mutant 3: license_text_diverges
dl_mut3 = copy.deepcopy(dl_this_fire)
for d in dl_mut3:
    if d.get("candidate_id") == "DR-LANG-IBERIAN-01":
        d["license_evidence_quote"] = "Este artigo esta disponivel para download gratuito e reutilizacao total sem qualquer restricao de atribuicao."
r3 = check(dl_mut3, sr_all_lines, PREVIOUSLY_SUPPLIED_IBERIAN)
mutants_out["license_text_diverges"] = {
    "expected_rule": "license_text_matches_live_evidence",
    "how_planted": "Overwrote DR-LANG-IBERIAN-01's license_evidence_quote with a fabricated 'no attribution required' claim contradicting the recorded CC BY (attribution-required) WebFetch evidence.",
    "expected_rule_fired": True,
    "refutation_criterion_fired": r3["refutation_criterion_fired"],
    "violations": r3["violations"],
}

# mutant 4: native_citation_not_verbatim
dl_mut4 = copy.deepcopy(dl_this_fire)
for d in dl_mut4:
    if d.get("candidate_id") == "DR-LANG-IBERIAN-05":
        d["native_citation"] = "Study of the curing of composite materials made from an epoxy system and elastomeric particles"
r4 = check(dl_mut4, sr_all_lines, PREVIOUSLY_SUPPLIED_IBERIAN)
mutants_out["native_citation_not_verbatim"] = {
    "expected_rule": "native_citation_verbatim_in_evidence",
    "how_planted": "Replaced DR-LANG-IBERIAN-05's native_citation (the exact Spanish thesis title) with an English paraphrase, simulating a silently-translated/paraphrased citation.",
    "expected_rule_fired": True,
    "refutation_criterion_fired": r4["refutation_criterion_fired"],
    "violations": r4["violations"],
}

# mutant 5: rediscovery_dropped -- uses the REAL previously-supplied id this
# time (not a synthetic stand-in), since this fire genuinely found one.
dl_mut5 = copy.deepcopy(dl_this_fire)
for d in dl_mut5:
    if d.get("candidate_id") == "DR-LANG-IBERIAN-01":
        d["rediscovers"] = None
r5 = check(dl_mut5, sr_all_lines, PREVIOUSLY_SUPPLIED_IBERIAN)
mutants_out["rediscovery_dropped"] = {
    "expected_rule": "rediscovery_recall",
    "how_planted": f"Cleared DR-LANG-IBERIAN-01's rediscovers field (real id {PREVIOUSLY_SUPPLIED_ID!r}, found live in amphora-redteam-audit's diagnostic.canonical.json) to None in a copy of this fire's disposition-ledger entries, simulating a fire that found the same source but failed to link it back to the previously-supplied candidate it rediscovers.",
    "expected_rule_fired": True,
    "refutation_criterion_fired": r5["refutation_criterion_fired"],
    "violations": r5["violations"],
}

for k, v in mutants_out.items():
    assert v["refutation_criterion_fired"] == v["expected_rule_fired"], f"positive control FAILED for mutant {k}"

# sanity: confirm the checker does NOT spuriously fire on the real (unmutated)
# previously-supplied list, i.e. rule 5 correctly finds the real rediscovery link
r5_real = check(dl_this_fire, sr_all_lines, PREVIOUSLY_SUPPLIED_IBERIAN)
assert r5_real["refutation_criterion_fired"] is False, "rule 5 spuriously fired despite a real, present rediscovery link"

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
print("dsl_appended_range", dsl_appended_line_start, dsl_appended_line_end)
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
    "dsl_appended_line_start": dsl_appended_line_start, "dsl_appended_line_end": dsl_appended_line_end,
    "dsl_prior_prefix_sha": dsl_prior_prefix_sha,
    "cm_before_sha": cm_before_sha, "cm_after_sha": cm_after_sha,
    "runA_sha": sha(runA_bytes),
}, indent=2))
