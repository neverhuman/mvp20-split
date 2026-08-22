#!/usr/bin/env python3
"""Re-derive real counts from facts.json + source_records.json for the FAIR/VIM
citation-sufficiency baseline (campaign item W-T-SLEDGER). AUDIT_ONLY, read-only.
Writes a diagnostic JSON of the observed evidence used by the signed receipt.
"""
import json
import re
import hashlib
from pathlib import Path

MOD = Path("/home/ubuntu/amphora/build/mvp20-split/amphora-source-ledger")
FACTS_PATH = MOD / "reference/mvp20/data/facts.json"
RECORDS_PATH = MOD / "reference/mvp20/data/source_records.json"


def sha_file(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


facts = json.loads(FACTS_PATH.read_text())
recs_doc = json.loads(RECORDS_PATH.read_text())
entries = facts["entries"]
records = recs_doc["records"]

n_entries = len(entries)
n_records = len(records)
n_load_bearing = sum(1 for v in entries.values() if v.get("load_bearing"))
n_waiver = sum(1 for v in entries.values() if v.get("single_source_waiver"))
n_second_url = sum(1 for v in entries.values() if v.get("second_url"))
n_url_present = sum(1 for v in entries.values() if v.get("url"))

fact_urls = set(v.get("url") for v in entries.values() if v.get("url"))
rec_urls = set(r.get("url") for r in records if r.get("url"))
overlap = fact_urls & rec_urls

doi_facts = sum(1 for v in entries.values() if v.get("url") and "doi.org" in v["url"])
doi_records = sum(1 for r in records if r.get("url") and "doi.org" in r["url"])

has_uncertainty_field_facts = sum(
    1 for v in entries.values() if "uncertainty" in v or "tolerance" in v
)
boilerplate_tol = {"exact page read", "not applicable", None}
records_real_tolerance = sum(
    1 for r in records if r.get("numeric_tolerance") not in boilerplate_tol
)

astm_iso_pattern = re.compile(r"ASTM|ISO |D-?[0-9]{3,4}")
records_cite_method = [
    r["id"] for r in records if astm_iso_pattern.search(json.dumps(r))
]
facts_mention_method = sum(1 for v in entries.values() if "method" in json.dumps(v).lower())

license_free_text_only = True  # no structured license enum field exists in either file
schema_facts = facts.get("schema")
schema_records = recs_doc.get("schema")

link_audit_statuses = recs_doc.get("link_audit_statuses")

# F4 check: is there any searchable citation index distinct from the raw two files?
registry_dir = MOD / "evidence/phase0/registry"
registry_files = sorted(p.name for p in registry_dir.glob("*.json")) if registry_dir.exists() else []

out = {
    "schema": "amphora.source-ledger.w-t-sledger.fair-vim-baseline-diagnostic.v1",
    "inputs": {
        "facts_path": str(FACTS_PATH.relative_to(MOD.parent)),
        "facts_sha256": sha_file(FACTS_PATH),
        "records_path": str(RECORDS_PATH.relative_to(MOD.parent)),
        "records_sha256": sha_file(RECORDS_PATH),
    },
    "counts": {
        "n_entries": n_entries,
        "n_records": n_records,
        "n_load_bearing": n_load_bearing,
        "n_single_source_waiver": n_waiver,
        "n_second_url": n_second_url,
        "n_url_present": n_url_present,
        "n_distinct_fact_urls": len(fact_urls),
        "n_distinct_record_urls": len(rec_urls),
        "n_fact_urls_corroborated_by_source_records": len(overlap),
        "fact_url_corroboration_rate": round(len(overlap) / len(fact_urls), 4) if fact_urls else None,
        "n_doi_urls_in_facts": doi_facts,
        "n_doi_urls_in_records": doi_records,
        "n_facts_entries_with_uncertainty_or_tolerance_field": has_uncertainty_field_facts,
        "n_records_with_non_boilerplate_numeric_tolerance": records_real_tolerance,
        "n_records_with_non_boilerplate_numeric_tolerance_rate": round(records_real_tolerance / n_records, 4),
        "n_records_citing_astm_iso_or_dxxxx_method": len(records_cite_method),
        "records_citing_method_ids_sample": records_cite_method[:10],
        "n_facts_entries_mentioning_method": facts_mention_method,
        "schema_facts": schema_facts,
        "schema_records": schema_records,
        "link_audit_status_vocabulary": link_audit_statuses,
        "registry_dir_files": registry_files,
        "license_field_is_free_text_not_structured_enum": license_free_text_only,
    },
}

out_path = MOD / "evidence/phase0/repairs/W-T-SLEDGER/work/fair_vim_baseline_diagnostic.json"
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps(out, indent=2, sort_keys=True))
print(json.dumps(out, indent=2, sort_keys=True))
print("WROTE", out_path)
