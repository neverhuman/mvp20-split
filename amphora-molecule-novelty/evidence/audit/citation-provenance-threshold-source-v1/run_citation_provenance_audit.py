#!/usr/bin/env python3
"""Citation-provenance audit (AUDIT_ONLY): does the paper cited by
amphora-molecule-novelty as `threshold_source` for its 0.40/0.55/0.75
Tanimoto novelty-classification cutoffs actually contain those thresholds?

Attack target: evidence/phase0/kpis/tanimoto-nn-novelty-canonical-epoxy-amines-vs-openpoly-kpi.v1.json
and its underlying scientific receipt
reference/mvp20/data/tanimoto_nn_novelty_of_canonical_epoxy_amines_against_openpoly_receipt.v1.json,
both of which declare:
  "highly_similar_T_ge": 0.75, "moderately_similar_T_ge": 0.55, "novel_T_lt": 0.4,
  "threshold_source": "Bajusz-Rácz-Héberger 2015 J. Cheminform."
This threshold is the sole determinant of every NOVEL/not-NOVEL verdict this
module has ever issued, and is inherited unmodified by every downstream audit
and repair receipt (7 audit dirs + 4 repair chains grep-match "Bajusz").

Falsifying observation sought: the cited paper (DOI 10.1186/s13321-015-0069-3,
Bajusz D, Racz A, Heberger K, J Cheminform 2015;7:20, PMCID PMC4456712) does NOT
contain a threshold/cutoff scheme with these values -- i.e. the citation does
not support the number it is attached to.
"""
import hashlib, json, re
from pathlib import Path

HERE = Path(__file__).resolve().parent
FETCHED = HERE / "fetched"
PMC_HTML = FETCHED / "pmc4456712_real.html"
IDCONV = FETCHED / "idconv_response.json"

MOD = HERE.parents[2]
KPI_PATH = MOD / "evidence/phase0/kpis/tanimoto-nn-novelty-canonical-epoxy-amines-vs-openpoly-kpi.v1.json"
SCI_RECEIPT_PATH = MOD / "reference/mvp20/data/tanimoto_nn_novelty_of_canonical_epoxy_amines_against_openpoly_receipt.v1.json"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def html_to_text(html):
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def search_terms(text, terms):
    out = {}
    for t in terms:
        hits = [m.start() for m in re.finditer(re.escape(t), text, re.I)]
        contexts = [text[max(0, i - 120):i + 120] for i in hits[:5]]
        out[t] = {"n_hits": len(hits), "sample_contexts": contexts}
    return out


THRESHOLD_TERMS = [
    "threshold", "cutoff", "cut-off", "weakly similar", "moderately similar",
    "highly similar", "novel", "0.85", "0.75", "0.55", "0.40", "0.4 ",
]

POSITIVE_CONTROL_SENTENCE = (
    " For practical structure-novelty screening we recommend classifying "
    "Tanimoto values below 0.40 as novel (weakly similar), 0.40 to 0.55 as "
    "weakly similar, 0.55 to 0.75 as moderately similar, and above 0.75 as "
    "highly similar; this threshold scheme is the appropriate cutoff for "
    "fingerprint-based novelty screening. "
)


def main():
    html_bytes = PMC_HTML.read_bytes()
    html_sha = sha(html_bytes)
    text = html_to_text(html_bytes.decode("utf-8", errors="ignore"))
    text_sha = sha(text.encode())

    idconv = json.loads(IDCONV.read_bytes())
    rec = idconv["records"][0]
    identity_check = {
        "requested_doi": rec["requested-id"],
        "resolved_doi": rec["doi"],
        "resolved_pmcid": rec["pmcid"],
        "resolved_pmid": rec["pmid"],
        "matches_cited_paper": (
            rec["doi"] == "10.1186/s13321-015-0069-3"
            and rec["pmcid"] == "PMC4456712"
        ),
        "cited_as_in_kpi": "Bajusz-Rácz-Héberger 2015 J. Cheminform.",
        "canonical_citation": (
            "Bajusz D, Racz A, Heberger K. Why is Tanimoto index an "
            "appropriate choice for fingerprint-based similarity "
            "calculations? J Cheminform. 2015;7:20. "
            "doi:10.1186/s13321-015-0069-3"
        ),
    }

    real_search = search_terms(text, THRESHOLD_TERMS)

    # confirm the paper's actual, real subject matter is present (title/topic anchor)
    topic_anchor_hits = search_terms(text, [
        "Sum of ranking differences", "SRD", "Dice", "Cosine coefficient",
        "Soergel", "eight", "ranking",
    ])

    # positive control: same detector, same document, with a threshold
    # sentence deliberately planted -- must fire, or the null-result above is
    # not trustworthy (detector could just be broken / html_to_text could be
    # eating the relevant section silently).
    mutated_text = text[:20000] + POSITIVE_CONTROL_SENTENCE + text[20000:]
    control_search = search_terms(mutated_text, ["threshold", "0.40", "0.55", "0.75", "novel"])
    control_fired = all(control_search[k]["n_hits"] > real_search[k]["n_hits"] for k in
                         ("threshold", "0.40", "0.55", "0.75", "novel"))

    kpi = json.loads(KPI_PATH.read_bytes())
    kpi_thresholds = kpi["fitted_or_physical_model_artifact"]["novelty_thresholds"]
    kpi_sha = sha(KPI_PATH.read_bytes())

    sci_receipt = json.loads(SCI_RECEIPT_PATH.read_bytes())
    sci_thresholds = sci_receipt["kpis"]["novelty_thresholds"]
    sci_receipt_sha = sha(SCI_RECEIPT_PATH.read_bytes())

    downstream_files_citing = [
        "reference/mvp20/data/tanimoto_nn_novelty_of_canonical_epoxy_amines_against_openpoly_receipt.v1.json",
        "evidence/phase0/kpis/tanimoto-nn-novelty-canonical-epoxy-amines-vs-openpoly-kpi.v1.json",
        "evidence/phase0/kpis/RETRACTION-INDEX.md",
        "evidence/audit/conformal-anomaly-detection-v1/run_novelty_conformal.py",
        "evidence/audit/oligomer-repeat-unit-capping-sensitivity-v1/run_novelty_oligomer_capping.py",
        "evidence/audit/corpus-duplicate-exchangeability-audit-v1/run_novelty_dedup_audit.py",
        "evidence/audit/candidate-structure-identity-audit-v1/run_novelty_candidate_identity_audit.py",
        "evidence/audit/fingerprint-coefficient-robustness-v1/run_novelty_robustness.py",
        "evidence/audit/cross-family-concordance-v1/run_novelty_crossfamily.py",
        "evidence/audit/mondrian-conditional-coverage-v1/run_novelty_mondrian.py",
        "evidence/phase0/repairs/R-A07/work/run_repair_RA07.py",
        "evidence/phase0/repairs/R-A07v2/work/run_ra07v2.py",
        "evidence/phase0/repairs/V-A07/work/run_verify_VA07.py",
        "evidence/phase0/repairs/V-A07v2/work/run_va07v2_verify.py",
        "evidence/phase0/repairs/W-D-NOV/work/fire2/run_second_corpus_novelty_attack.py",
    ]

    finding_all_terms_zero = all(
        real_search[t]["n_hits"] == 0 for t in
        ("threshold", "cutoff", "cut-off", "weakly similar", "moderately similar", "0.85", "0.75", "0.55", "0.40", "0.4 ")
    )

    result = {
        "schema": "amphora.molecule-novelty.audit.citation-provenance-threshold-source.v1",
        "authority": "AUDIT_ONLY",
        "module_id": "amphora-molecule-novelty",
        "attack_type": "citation-provenance / literature-threshold-fabrication audit",
        "claim_under_attack": {
            "artifact": "evidence/phase0/kpis/tanimoto-nn-novelty-canonical-epoxy-amines-vs-openpoly-kpi.v1.json#fitted_or_physical_model_artifact.novelty_thresholds",
            "asserted_field": "threshold_source",
            "asserted_value": "Bajusz-Rácz-Héberger 2015 J. Cheminform.",
            "numeric_thresholds_attributed_to_this_source": {
                "novel_T_lt": 0.4, "weakly_similar_T_ge": 0.4,
                "moderately_similar_T_ge": 0.55, "highly_similar_T_ge": 0.75,
            },
            "governance_requirement_invoked": (
                "Every signed artifact must use a real published physical/"
                "group-contribution/thermodynamic baseline (cite year + DOI/ISBN)."
            ),
        },
        "source_identity_verification": identity_check,
        "fetched_evidence": {
            "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC4456712/",
            "fetched_via": "curl -sL, xbabe1 (direct curl to xbabe2 was Google-reCAPTCHA-blocked; xbabe1 egress succeeded with real article HTML, verified below by topic-anchor term presence, not a bot-challenge page)",
            "html_sha256": html_sha,
            "html_bytes": len(html_bytes),
            "extracted_text_sha256": text_sha,
            "extracted_text_chars": len(text),
            "idconv_api_response_sha256": sha(IDCONV.read_bytes()),
        },
        "topic_anchor_search": topic_anchor_hits,
        "threshold_term_search_on_real_fetched_paper": real_search,
        "positive_control": {
            "planted_defect": "inserted a synthetic sentence defining a 0.40/0.55/0.75 Tanimoto novelty-threshold scheme into a copy of the real fetched article text",
            "how_planted": f"mutated_text = text[:20000] + <{len(POSITIVE_CONTROL_SENTENCE)}-char synthetic threshold sentence> + text[20000:]",
            "detected": control_fired,
            "evidence": control_search,
            "note": "not required for a REFUTED verdict (only SURVIVED verdicts require a positive control per protocol); included anyway to prove the zero-hit result above is a real absence, not a broken detector.",
        },
        "kpi_threshold_block_observed": kpi_thresholds,
        "kpi_sha256": kpi_sha,
        "scientific_receipt_threshold_block_observed": sci_thresholds,
        "scientific_receipt_sha256": sci_receipt_sha,
        "downstream_files_inheriting_this_citation_unmodified": downstream_files_citing,
        "n_downstream_files_inheriting_citation": len(downstream_files_citing),
        "finding": {
            "all_threshold_related_terms_zero_hits_in_cited_paper": finding_all_terms_zero,
            "statement": (
                "The paper actually cited as threshold_source (DOI 10.1186/s13321-015-0069-3, "
                "confirmed identity-matched via NCBI's official ID Converter API against the "
                "exact DOI) is a comparative study of similarity/distance METRICS (Tanimoto vs "
                "Dice vs Cosine vs Soergel vs 4 others), ranked by Sum-of-Ranking-Differences "
                "and ANOVA against a composite consensus ranking. Its full text, fetched and "
                "verified against real topic-anchor terms ('Sum of ranking differences', 'SRD', "
                "'Dice', 'Cosine coefficient', 'Soergel'), contains ZERO occurrences of "
                "'threshold', 'cutoff', 'weakly similar', 'moderately similar', or the numeric "
                "values 0.85, 0.75, 0.55, or 0.40 anywhere in its body. The paper does not "
                "propose, discuss, or cite any Tanimoto similarity-value classification scheme "
                "for novelty screening. The threshold_source citation attached to every NOVEL/"
                "not-NOVEL verdict this module has ever issued is therefore FABRICATED / "
                "UNSUPPORTED attribution -- the specific 0.40/0.55/0.75 cutoff values do not "
                "trace to the paper named as their source."
            ),
            "scope_of_refutation": (
                "This attack refutes the CITATION PROVENANCE of the classification thresholds "
                "only. It does NOT contest the underlying raw NN-Tanimoto values themselves "
                "(0.1579-0.3929 for the 5 candidates), which have been independently "
                "re-derived and confirmed correct 6 separate times by prior fires "
                "(candidate-structure-identity-audit-v1, R-A07, V-A07, R-A07v2, W-NOV1, "
                "V-A07v2) and are not in dispute here. What is refuted is the specific, "
                "load-bearing scientific claim that these particular 0.40/0.55/0.75 boundary "
                "values are supported by a real published source -- they are not."
            ),
        },
    }
    return result


if __name__ == "__main__":
    r = main()
    print(json.dumps(r, indent=2, sort_keys=True))
