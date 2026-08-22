#!/usr/bin/env python3
"""DR-ANNEX fire-2 repair: build discovery-annex.v1.jsonl and append
supersede-never-rewrite quarantine corrections to disposition-ledger.v1.jsonl
for the three self-disclosed non-envelope-conforming candidates fire 1 found
un-quarantined in the primary ledger (DR-LANG-KO-02, DR-LANG-KO-04,
DR-LANG-EU-11). Follows the exact candidate_correction/supersedes convention
already established by the DR-LANG-EU fire-2 spot-check repair
(disposition-ledger.v1.jsonl lines 73-74): new suffixed candidate_id,
entry_type candidate_correction/candidate_quarantine, a `supersedes` block
naming the original candidate_id + exact superseded line sha256, original
rows never edited or deleted. AUDIT_ONLY, no acquisition.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-dataset-recon"
LEDGERS = MOD / "evidence/ledgers"

FIRE_ID = "20260811T150002-2000042-4b581f63550c"
DATE = "2026-08-11"

ENVELOPE_SCOPE_STATEMENT = (
    "Coating IP scope ONLY: marine anti-corrosion, two-part epoxy-amine, "
    "DGEBA + amine hardeners, related pigments/fillers/solvents."
)

FLAGGED = [
    {
        "candidate_id": "DR-LANG-KO-02",
        "quarantine_class": "adjacent-domain-non-conforming",
        "nonconformance_reason": (
            "Concrete-embedded structural rebar (reinforcement steel) inspection "
            "dataset across bridges/tunnels/dams/ports/rivers/water-sewage systems "
            "-- not a coated-steel/marine-hull coating dataset at all; outside "
            "Coating IP scope."
        ),
    },
    {
        "candidate_id": "DR-LANG-KO-04",
        "quarantine_class": "adjacent-hardener-chemistry-non-conforming",
        "nonconformance_reason": (
            "Epoxy/acid-anhydride cure system -- a different hardener chemistry "
            "class than the portfolio's amine-hardener scope; its own coverage "
            "field states 'anhydride-cured, not amine-cured' in the same breath "
            "as being recommended into the primary ledger."
        ),
    },
    {
        "candidate_id": "DR-LANG-EU-11",
        "quarantine_class": "adjacent-resin-chemistry-non-conforming",
        "nonconformance_reason": (
            "Cardanol/biobased-resin system, not the portfolio's core DGEBA+amine "
            "chemistry; was wired via serves.recipe_elements to "
            "amine-cure-conversion-tracking un-quarantined prior to this repair."
        ),
    },
]


def sha(b):
    return hashlib.sha256(b).hexdigest()


def dumps(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(", ", ": "))


def load_jsonl(p):
    return [json.loads(l) for l in p.read_bytes().decode("utf-8").splitlines() if l.strip()]


def find_dsl_entry(cid):
    for d in load_jsonl(LEDGERS / "dataset-ledger.v1.jsonl"):
        if d.get("candidate_id") == cid:
            return d
    raise KeyError(cid)


def find_disp_entry_and_line(cid):
    disp_path = LEDGERS / "disposition-ledger.v1.jsonl"
    raw_lines = disp_path.read_bytes().decode("utf-8").splitlines()
    for i, line in enumerate(raw_lines):
        if not line.strip():
            continue
        obj = json.loads(line)
        if obj.get("candidate_id") == cid and (obj.get("disposition") or {}).get("verdict") == "RECOMMENDED":
            return obj, line.encode("utf-8"), i + 1  # 1-indexed
    raise KeyError(cid)


def main():
    disp_path = LEDGERS / "disposition-ledger.v1.jsonl"
    annex_path = LEDGERS / "discovery-annex.v1.jsonl"

    disp_prior_bytes = disp_path.read_bytes()
    disp_prior_prefix_sha256 = sha(disp_prior_bytes)
    disp_prior_line_count = len([l for l in disp_prior_bytes.decode("utf-8").splitlines() if l.strip()])

    annex_prior_bytes = annex_path.read_bytes() if annex_path.exists() else b""
    annex_prior_prefix_sha256 = sha(annex_prior_bytes)
    annex_prior_line_count = len([l for l in annex_prior_bytes.decode("utf-8").splitlines() if l.strip()]) if annex_prior_bytes else 0
    annex_created_new_file = not annex_path.exists()

    new_disp_lines = []
    new_annex_lines = []
    supersede_records = []

    for spec in FLAGGED:
        cid = spec["candidate_id"]
        dsl_entry = find_dsl_entry(cid)
        disp_entry, disp_raw_line_bytes, disp_line_no = find_disp_entry_and_line(cid)
        superseded_line_sha256 = sha(disp_raw_line_bytes)
        corrected_cid = f"{cid}-QUARANTINED"
        annex_entry_id = f"DR-ANNEX-{cid}-01"

        annex_entry = {
            "entry_type": "discovery_annex_entry",
            "schema": "amphora.dataset-recon.discovery-annex.v1",
            "annex_entry_id": annex_entry_id,
            "candidate_id": cid,
            "quarantine_class": spec["quarantine_class"],
            "nonconformance_reason": spec["nonconformance_reason"],
            "envelope_scope_statement": ENVELOPE_SCOPE_STATEMENT,
            "framing": "AUDIT-ONLY",
            "language": dsl_entry.get("language"),
            "native_citation": dsl_entry.get("native_citation"),
            "name": dsl_entry.get("name"),
            "custodian": dsl_entry.get("publisher_custodian") or disp_entry.get("custodian"),
            "url_or_doi": dsl_entry.get("url_or_doi") or disp_entry.get("url"),
            "coverage": dsl_entry.get("coverage"),
            "estimated_records_and_coverage": dsl_entry.get("estimated_records_and_coverage"),
            "license_as_published": dsl_entry.get("license_as_published"),
            "standard_mapping": dsl_entry.get("standard_mapping"),
            "translation_confidence": dsl_entry.get("translation_confidence"),
            "confidence_flag": dsl_entry.get("confidence_flag"),
            "integrity_risks": dsl_entry.get("integrity_risks"),
            "rubric_overall_score": dsl_entry.get("rubric_overall_score"),
            "rubric_path": dsl_entry.get("rubric_path"),
            "origin": {
                "dataset_ledger_path": "amphora-dataset-recon/evidence/ledgers/dataset-ledger.v1.jsonl",
                "origin_ledger_entry_id": dsl_entry.get("ledger_entry_id"),
                "origin_fire_id": dsl_entry.get("fire_id"),
                "origin_run_id": dsl_entry.get("run_id"),
                "origin_disposition_verdict_superseded": "RECOMMENDED",
                "origin_disposition_ledger_line_no": disp_line_no,
                "origin_disposition_ledger_line_sha256": superseded_line_sha256,
            },
            "never_cited_by_primary_attestation": (
                "Quarantined per AMPHORA-DIRECTIVE-2026-08-09 S9 rule 6: this annex "
                "entry MUST NOT be cited by the primary dataset-ledger.v1.jsonl (no new "
                "primary-ledger line may reference this candidate_id going forward) or "
                "by any primary recipe/module BOM."
            ),
            "quarantine": {
                "verdict": "QUARANTINED_TO_ANNEX",
                "quarantined_by_fire_id": FIRE_ID,
                "quarantined_date": DATE,
                "superseding_disposition_candidate_id": corrected_cid,
                "superseded_disposition_verdict": "RECOMMENDED",
                "superseded_disposition_ledger_line_no": disp_line_no,
                "superseded_disposition_ledger_line_sha256": superseded_line_sha256,
            },
            "snapshot_date": DATE,
            "fire_id": FIRE_ID,
            "run_id": f"DR-ANNEX-{FIRE_ID}",
        }
        new_annex_lines.append(dumps(annex_entry))

        superseding_disp_entry = {
            "candidate_id": corrected_cid,
            "confidence_flag": dsl_entry.get("confidence_flag"),
            "coverage": dsl_entry.get("coverage"),
            "custodian": dsl_entry.get("publisher_custodian") or disp_entry.get("custodian"),
            "data_class_note": (
                "QUARANTINE correction (not an edition/fact correction): the original "
                "RECOMMENDED verdict placed a self-disclosed non-envelope-conforming "
                "chemistry in the primary dataset-ledger.v1.jsonl un-quarantined. This "
                "entry supersedes that verdict with REJECTED-and-quarantined; full "
                "content migrated to discovery-annex.v1.jsonl entry " + annex_entry_id + "."
            ),
            "date": DATE,
            "disposition": {
                "reason": (
                    f"Supersedes the RECOMMENDED verdict at disposition-ledger.v1.jsonl "
                    f"line {disp_line_no} (sha256 {superseded_line_sha256}) per DR-ANNEX "
                    f"fire {FIRE_ID}. " + spec["nonconformance_reason"] +
                    " Non-envelope-conforming per the portfolio scope statement: " +
                    ENVELOPE_SCOPE_STATEMENT +
                    " Migrated to discovery-annex.v1.jsonl entry " + annex_entry_id +
                    "; MUST NOT be cited by the primary ledger or primary recipe going forward."
                ),
                "verdict": "REJECTED",
                "verdict_change_from_original": True,
            },
            "entry_type": "candidate_quarantine",
            "fire_id": FIRE_ID,
            "framing": "AUDIT-ONLY",
            "integrity_risks": dsl_entry.get("integrity_risks"),
            "language": dsl_entry.get("language"),
            "license_evidence_quote": disp_entry.get("license_evidence_quote"),
            "name": dsl_entry.get("name") + " [QUARANTINED TO ANNEX: DR-ANNEX fire " + FIRE_ID + "]",
            "native_citation": dsl_entry.get("native_citation"),
            "native_citation_romanization": disp_entry.get("native_citation_romanization"),
            "quarantine": {
                "annex_path": "amphora-dataset-recon/evidence/ledgers/discovery-annex.v1.jsonl",
                "annex_entry_id": annex_entry_id,
                "quarantine_class": spec["quarantine_class"],
                "quarantined": True,
            },
            "rank": disp_entry.get("rank"),
            "rediscovers": None,
            "run_id": f"DR-ANNEX-{FIRE_ID}",
            "schema": "amphora.dataset-recon.disposition-ledger.v1",
            "serves": {"module_gaps": [], "recipe_elements": []},
            "snapshot_date": DATE,
            "standard_mapping": dsl_entry.get("standard_mapping"),
            "supersedes": {
                "reason": spec["nonconformance_reason"] + " Quarantined per directive S9 rule 6.",
                "superseded_candidate_id": cid,
                "superseded_deleted_or_modified": False,
                "superseded_disposition_ledger_line_sha256": superseded_line_sha256,
            },
            "translation_confidence": dsl_entry.get("translation_confidence"),
            "translation_confidence_note": "Unchanged from original entry -- this is a quarantine-verdict correction, not a translation correction.",
            "url": disp_entry.get("url"),
        }
        new_disp_lines.append(dumps(superseding_disp_entry))

        supersede_records.append({
            "candidate_id": cid,
            "corrected_candidate_id": corrected_cid,
            "annex_entry_id": annex_entry_id,
            "superseded_disposition_line_no": disp_line_no,
            "superseded_disposition_line_sha256": superseded_line_sha256,
        })

    disp_append_bytes = ("\n".join(new_disp_lines) + "\n").encode("utf-8")
    with open(disp_path, "ab") as f:
        f.write(disp_append_bytes)
    disp_new_total_lines = disp_prior_line_count + len(new_disp_lines)
    disp_appended_line_range = [disp_prior_line_count + 1, disp_new_total_lines]

    annex_append_bytes = ("\n".join(new_annex_lines) + "\n").encode("utf-8")
    with open(annex_path, "ab") as f:
        f.write(annex_append_bytes)
    annex_new_total_lines = annex_prior_line_count + len(new_annex_lines)
    annex_appended_line_range = [annex_prior_line_count + 1, annex_new_total_lines]

    result = {
        "fire_id": FIRE_ID,
        "disposition_ledger": {
            "path": "amphora-dataset-recon/evidence/ledgers/disposition-ledger.v1.jsonl",
            "prior_prefix_sha256": disp_prior_prefix_sha256,
            "prior_line_count": disp_prior_line_count,
            "appended_line_range": disp_appended_line_range,
            "sha256_of_appended_lines": sha(disp_append_bytes),
            "new_total_lines": disp_new_total_lines,
        },
        "discovery_annex": {
            "path": "amphora-dataset-recon/evidence/ledgers/discovery-annex.v1.jsonl",
            "created_new_file": annex_created_new_file,
            "prior_prefix_sha256": annex_prior_prefix_sha256,
            "prior_line_count": annex_prior_line_count,
            "appended_line_range": annex_appended_line_range,
            "sha256_of_appended_lines": sha(annex_append_bytes),
            "new_total_lines": annex_new_total_lines,
        },
        "supersede_records": supersede_records,
    }
    Path(sys.argv[1]).write_text(dumps(result) + "\n")
    print(dumps(result))


if __name__ == "__main__":
    main()
