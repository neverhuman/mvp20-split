#!/usr/bin/env python3
"""DSSE-Ed25519-sign the alam2022-pa450-pa3282-acquisition-v1 AUDIT_ONLY receipt
for amphora-barrier-corrosion-score, campaign item C4. Documents the acquisition
of a third strictly in-class, open table-read, rights-clean (CC-BY-4.0) epoxy-
polyamide EIS ladder, refuting the prior systematic_search_ledger's implicit
exhaustiveness (>=3 bar was unmet at 2/3; now 3/3). AUDIT_ONLY: does not modify
the portfolio manifest or any mission.md, does not promote Phase-0 status."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-barrier-corrosion-score"
AUDIT_DIR = MOD / "evidence/audit/alam2022-pa450-pa3282-acquisition-v1"
DATA_DIR = MOD / "reference/mvp20/data"
SERIES_PATH = DATA_DIR / "corrosion_series.json"
EXTRACTION_PATH = DATA_DIR / "literature_extractions/alam2022_pa450_pa3282.json"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"


def sha(b): return hashlib.sha256(b).hexdigest()


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


extraction_bytes = EXTRACTION_PATH.read_bytes()
extraction_sha256 = sha(extraction_bytes)
series_bytes = SERIES_PATH.read_bytes()
series_sha256_after = sha(series_bytes)
series_json = json.loads(series_bytes)

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"
eval_pin = rev_pin = False
if TRUST.exists():
    trust = json.loads(TRUST.read_text())
    tbr = {k.get("role"): k for k in trust.get("keys", [])}
    eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
    rev_pin = (rev_key_id == tbr.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))

body_obj = {
    "schema": "amphora.barrier-corrosion-score.literature-acquisition-receipt.v1",
    "module": "amphora-barrier-corrosion-score",
    "benchmark": "alam2022-pa450-pa3282-acquisition-v1",
    "campaign_item_id": "C4",
    "authority": "AUDIT_ONLY",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_mission_md": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "opened_or_parsed_quarantined_asset": False,
    "claim_under_attack": {
        "receipt_path": "amphora-barrier-corrosion-score/reference/mvp20/data/corrosion_series.json",
        "claim_text": "systematic_search_ledger is exhaustive: no third strictly in-class, open table-read, rights-clean epoxy-amine EIS ladder exists in the accessible literature.",
        "verdict": "REFUTED",
        "strict_literature_count_before": 2,
        "strict_literature_series_before": ["asperti2024", "zhu2022"],
        "strict_literature_count_after": 3,
        "strict_literature_series_after": ["asperti2024", "zhu2022", "alam2022_pa450_pa3282"]
    },
    "purpose": (
        "Genuine literature sweep (MDPI Coatings/Materials/Polymers, ACS AuthorChoice/Omega, "
        "RSC open access, Scientific Reports/Nature Comms, 2020-2026) for a third strictly "
        "in-class (epoxy-amine/polyamide marine coating), open table-read, ordered side-by-side "
        "formulation->EIS series, rights-clean (CC-BY/CC0/public-domain). Found: Alam et al., "
        "Materials 15(7):2562 (2022), DOI 10.3390/ma15072562, PMCID PMC8999854 -- a CC-BY-4.0 "
        "epoxy-polyamide (DGEBA + Aradur 450 BD / Aradur 3282 BD) hardener-stoichiometry ladder "
        "(E-0/E-1/E-2 and F-0/F-1/F-2) with open numeric EIS equivalent-circuit tables (Table 5, "
        "Table 6) across 5 immersion timepoints. This satisfies the module's own >=3 strict "
        "literature bar (corrosion_series.json strict_validation_bar), which was previously unmet "
        "at 2/3 (asperti2024, zhu2022) despite a five-topic prior systematic search."
    ),
    "search_record": {
        "queries_run": 5,
        "records_screened": 33,
        "near_misses_rejected": 5,
        "near_miss_summary": "one candidate excluded for being a RETRACTED article (PMC10173445, ACS Omega imidazolium-ionic-liquid epoxy hardener); others excluded for unconfirmed curative class, figure-only EIS reporting, or fetch-blocked rights verification -- see systematic_search_ledger entry appended to corrosion_series.json for full detail per near-miss.",
        "full_ledger_entry_appended_to": "amphora-barrier-corrosion-score/reference/mvp20/data/corrosion_series.json#systematic_search_ledger[-1]"
    },
    "asset": {
        "cite": "Alam, Samad, Seikh, Mohammed, Al-Zahrani, Sherif, Materials (Basel) 15(7):2562 (2022)",
        "doi": "10.3390/ma15072562",
        "pmcid": "PMC8999854",
        "pmid": "35407894",
        "url_primary": "https://www.mdpi.com/1996-1944/15/7/2562",
        "url_pmc_mirror": "https://pmc.ncbi.nlm.nih.gov/articles/PMC8999854/",
        "license_type": "CC-BY-4.0",
        "license_text_source_1_pmc": "This article is an open access article distributed under the terms and conditions of the Creative Commons Attribution (CC BY) license (https://creativecommons.org/licenses/by/4.0/).",
        "license_text_source_2_europepmc_xml": "Licensee MDPI, Basel, Switzerland. This article is an open access article distributed under the terms and conditions of the Creative Commons Attribution (CC BY) license",
        "license_cross_sourced_independently": True,
        "retraction_check_performed": True,
        "retraction_check_result": "no retraction/erratum/correction notice found",
        "in_class": "epoxy-polyamide (DGEBA + polyaminoamine/polyamidoamine adducts), offshore/marine application, mild steel substrate",
        "table_read": True,
        "extraction_path": "amphora-barrier-corrosion-score/reference/mvp20/data/literature_extractions/alam2022_pa450_pa3282.json",
        "extraction_sha256": extraction_sha256,
        "extraction_method": "AI-mediated single-pass full-text read of PMC HTML mirror; license independently cross-sourced from Europe PMC fullTextXML; numeric table values NOT independently double-keyed by a second extraction pass",
        "extraction_confidence_caveat": (
            "Numeric transcription of Table 5/Table 6 relied on a single automated full-text read "
            "(direct MDPI fetch was blocked with HTTP 403; PMC mirror succeeded). Internal-consistency "
            "checks passed: all 30 CPE dispersion exponents (Q1_n, Q2_n) fall in the physically valid "
            "[0,1] range, and both hardener series (E-series, F-series) independently reproduce the "
            "authors' stated qualitative conclusion (mid-stoichiometry formulation E-1/F-1 outperforms "
            "the two stoichiometric extremes) -- but this is not a substitute for manual cell-by-cell "
            "verification against the primary PDF. Flagged as a residual data-quality ask below."
        )
    },
    "corrosion_series_json_update": {
        "path": "amphora-barrier-corrosion-score/reference/mvp20/data/corrosion_series.json",
        "sha256_after": series_sha256_after,
        "fields_changed": ["systematic_search_ledger (+1 entry)", "series (+1 entry: alam2022_pa450_pa3282)",
                            "strict_literature_count (2 -> 3)", "strict_literature_series (+alam2022_pa450_pa3282)",
                            "literature_bar_status (not met -> met)", "honest_assessment (updated count + caveat)"],
        "predictive_model_status_unchanged": series_json["predictive_model_status"],
        "candidate_prediction_status_unchanged": series_json["candidate_prediction_status"],
        "note": "Meeting the literature-count bar changes only the search-exhaustiveness claim; it does NOT change predictive_model_status or candidate_prediction_status, both of which remain FAILED for the reasons already on record (no own wet-lab candidate panels)."
    },
    "residual_data_ask": {
        "gap": "alam2022_pa450_pa3282 Table 5/Table 6 numeric values transcribed via single-pass AI-mediated read, not manually double-keyed against primary PDF",
        "candidate_source": "same asset already acquired (CC-BY, no further rights action needed)",
        "url_or_doi": "10.3390/ma15072562",
        "license": "CC-BY-4.0",
        "license_verified": True,
        "estimated_records": 30,
        "next_action": "human or independent second-pass spot-check of a sample of Table 5/6 cells against the MDPI PDF before this series is used for anything beyond bibliographic/design-rule anchoring (its current, already-limited, use_limit)"
    },
    "does_not_close": [
        "Does not validate or predict the mvp20 candidate ranking (use_limit unchanged: within-study direction/bibliographic anchor only, no cross-study pooling).",
        "Does not change predictive_model_status or candidate_prediction_status (both remain FAILED).",
        "Does not promote any authority, phase, or manifest state.",
        "Does not resolve the still-open, separately-tracked C2 (ST-19168 rights review) or C3 (pre-registration) campaign items on this module."
    ],
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under amphora-barrier-corrosion-score/evidence/audit/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin)},
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER", "key_id": rev_key_id, "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin), "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed."},
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.barrier-corrosion-alam2022-acquisition+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
out = AUDIT_DIR / "acquisition-receipt.v1.dsse.json"
out_bytes = json.dumps(receipt, indent=2, sort_keys=True).encode()
out.write_bytes(out_bytes)
# verify immediately
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("extraction_sha256", extraction_sha256)
print("series_sha256_after", series_sha256_after)
print("envelope_sha256", sha(out_bytes))
print("signature_verified", True)
