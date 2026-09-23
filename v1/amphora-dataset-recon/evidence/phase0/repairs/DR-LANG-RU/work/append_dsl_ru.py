#!/usr/bin/env python3
"""Append the DR-LANG-RU-01 dataset-ledger entry (RECOMMENDED candidate). AUDIT_ONLY."""
import hashlib
import json
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-dataset-recon"
LEDGERS = MOD / "evidence/ledgers"
ITEM = MOD / "evidence/phase0/repairs/DR-LANG-RU"
WORK = ITEM / "work"

FIRE_ID = "20260810T090001-3307991-b3648fc59c25"
RUN_ID = f"DR-LANG-RU-{FIRE_ID}"
DATE = "2026-08-10"


def sha(b):
    return hashlib.sha256(b).hexdigest()


DSL_PATH = LEDGERS / "dataset-ledger.v1.jsonl"
dsl_before = DSL_PATH.read_bytes()
dsl_prior_prefix_sha = sha(dsl_before)
dsl_prior_lines = dsl_before.decode("utf-8").splitlines()
dsl_prior_line_count = len(dsl_prior_lines)

entry = {
    "candidate_id": "DR-LANG-RU-01",
    "confidence_flag": "MEDIUM",
    "coverage": (
        "NMR-spectroscopy-based cure-kinetics study of epoxy resin ED-16 (ЭД-16) with amine "
        "hardeners including aromatic amines and aminotriazoles. Reports temperature-dependent "
        "NMR second moments and spin-lattice relaxation times (T1), and cure-rate dependence on "
        "amine-group count and reactive-proton count of the hardener. Single-institution "
        "academic study, not a compilation."
    ),
    "date": DATE,
    "disposition": {
        "reason": (
            "rubric.v1.json score: gap_fit=8, provenance_measurement_quality=6, "
            "rights_clarity=8, uniqueness=10, integrity_risk=8, acquisition_cost_friction=10, "
            "overall=8.3333 -> RECOMMENDED. Next action: human downloads the freely-available "
            "CyberLeninka PDF to extract the full NMR second-moment/T1 dataset and confirm "
            "decimal-convention/unit handling (per directive rule 5's locale-hazard discipline) "
            "before any quantitative reuse in the cure-kinetics benchmark; CC BY attribution "
            "required."
        ),
        "verdict": "RECOMMENDED",
    },
    "entry_type": "dataset_ledger_entry",
    "estimated_records_and_coverage": (
        "Single-paper academic study; NMR-based cure-kinetics measurements (second moments, "
        "T1 relaxation times, temperature series) for epoxy resin ED-16 cured with at least 2 "
        "classes of amine hardener (aromatic amines, aminotriazoles). Exact number of individual "
        "NMR measurement points not confirmed this fire (full text not read beyond the WebFetch "
        "evaluative summary, per no-acquisition discipline)."
    ),
    "fire_id": FIRE_ID,
    "framing": "AUDIT-ONLY",
    "integrity_risks": ["locale_unit_convention_unverified"],
    "language": "ru",
    "ledger_entry_id": "DR-LANG-RU-DSL-01",
    "license_as_published": (
        "CC BY (Creative Commons Attribution) -- free open-access download and read; "
        "attribution required. No NonCommercial or NoDerivatives clause observed (unlike the "
        "de fire's CC BY-NC-ND dissertation), per the CC BY icon displayed on the CyberLeninka "
        "article page."
    ),
    "module_gaps": ["amphora-cure-kinetics"],
    "name": (
        "Lundin, A.G., Ostapkovich, A.M., Yushkova, E.Yu. (2005). \"Кинетика отверждения "
        "эпоксидных смол аминами\" (Kinetics of Hardening of Epoxide Resins with Amines), "
        "Известия высших учебных заведений. Химия и химическая технология"
    ),
    "native_citation": "Кинетика отверждения эпоксидных смол аминами",
    "next_human_action": (
        "Human downloads the freely-available CyberLeninka PDF to extract the full NMR "
        "second-moment/T1 dataset and confirm decimal-convention/unit handling before any "
        "quantitative reuse in the cure-kinetics benchmark; CC BY attribution required."
    ),
    "publisher_custodian": (
        "Известия высших учебных заведений. Химия и химическая технология (Ivanovo State "
        "University of Chemistry and Technology journal), hosted open-access on CyberLeninka."
    ),
    "rank": 1,
    "recipe_elements": [],
    "rubric_overall_score": 8.3333,
    "rubric_path": "amphora-dataset-recon/evidence/phase0/repairs/DR-RUBRIC/work/rubric.v1.json",
    "run_id": RUN_ID,
    "schema": "amphora.dataset-recon.dataset-ledger.v1",
    "serves": {"module_gaps": ["amphora-cure-kinetics"], "recipe_elements": []},
    "snapshot_date": DATE,
    "standard_mapping": {
        "astm_iso_equiv": "N/A -- academic NMR-based measurement method, not a certified ASTM/GOST/ISO test standard",
        "comparability_rating": "method_not_standard_based",
        "published_standard": "NMR spectroscopy (second-moment / spin-lattice relaxation analysis)",
    },
    "translation_confidence": "native_script_verified_high",
    "url_or_doi": "https://cyberleninka.ru/article/n/kinetika-otverzhdeniya-epoksidnyh-smol-aminami",
}

entry_text = json.dumps(entry, sort_keys=True, ensure_ascii=False)
dsl_appended_sha = sha((entry_text + "\n").encode("utf-8"))
dsl_new_content = dsl_before + (b"" if dsl_before.endswith(b"\n") or not dsl_before else b"\n") + (entry_text + "\n").encode("utf-8")
dsl_file_sha_after = sha(dsl_new_content)
dsl_appended_line_no = dsl_prior_line_count + 1

DSL_PATH.write_bytes(dsl_new_content)
assert sha(DSL_PATH.read_bytes()) == dsl_file_sha_after

shas = json.loads((WORK / "shas.json").read_text())
shas.update({
    "dsl_prior_prefix_sha": dsl_prior_prefix_sha,
    "dsl_appended_line_no": dsl_appended_line_no,
    "dsl_appended_sha": dsl_appended_sha,
    "dsl_file_sha_after": dsl_file_sha_after,
})
(WORK / "shas.json").write_text(json.dumps(shas, indent=2, sort_keys=True, ensure_ascii=False))

print("DSL appended at line", dsl_appended_line_no)
print("dsl_file_sha_after", dsl_file_sha_after)
