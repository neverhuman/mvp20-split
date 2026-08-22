#!/usr/bin/env python3
"""
Independent re-derivation of amphora-assurance-capabilities/src/lib.rs::evaluate_source_ledger
(lines 678-800, SHA-256 c0b2540fa84a9b8c98d2be5d82cbb1d21e9fd8b9806edad23815a0d912f4ab4d as pinned
in amphora-source-ledger/docs/mission.md), translated field-for-field, no logic added or removed.
Used to test whether the gate can detect (a) non-resolving URLs, (b) resolving-but-wrong-support
citations, (c) malformed source records -- none of which the Rust source reads or checks.
"""
import json
import sys
import copy

FACTS_PATH = "amphora-source-ledger/reference/mvp20/data/facts.json"
RECORDS_PATH = "amphora-source-ledger/reference/mvp20/data/source_records.json"


def evaluate_source_ledger(entries: dict, source_records: list, required_fields: list) -> dict:
    load_bearing = [row for row in entries.values() if row.get("load_bearing") is True]
    corroborated = sum(
        1 for row in load_bearing
        if isinstance(row.get("second_url"), str) and row.get("second_url").strip()
    )
    prose_waivers = sum(
        1 for row in load_bearing
        if isinstance(row.get("single_source_waiver"), str) and row.get("single_source_waiver").strip()
    )
    missing_url = sum(
        1 for row in entries.values()
        if not (isinstance(row.get("url"), str) and row.get("url").strip())
    )
    incomplete_records = sum(
        1 for row in source_records
        if any(row.get(f) is None for f in required_fields)
    )
    evidence_complete = (
        corroborated == len(load_bearing)
        and prose_waivers == 0
        and missing_url == 0
        and incomplete_records == 0
    )
    gates = {
        "uncited_constants_rejected": missing_url == 0,
        "load_bearing_two_source": corroborated == len(load_bearing),
        "load_bearing_two_source_or_waiver": corroborated == len(load_bearing) and prose_waivers == 0,
        "prose_waivers_rejected": prose_waivers == 0,
    }
    return {
        "status": "SCORED" if evidence_complete else "FAILED_GATES",
        "score": 1.0 if evidence_complete else 0.0,
        "metrics": {
            "cited_constant_count": len(entries),
            "load_bearing_constant_count": len(load_bearing),
            "two_source_count": corroborated,
            "prose_waiver_count": prose_waivers,
            "missing_url_count": missing_url,
            "source_record_count": len(source_records),
            "incomplete_source_record_count": incomplete_records,
        },
        "gates": gates,
    }


def main():
    facts = json.load(open(FACTS_PATH))
    entries = facts["entries"]
    records_doc = json.load(open(RECORDS_PATH))
    source_records = records_doc["records"]
    required_fields = records_doc["required_record_fields"]

    baseline = evaluate_source_ledger(entries, source_records, required_fields)
    print("=== BASELINE (real facts.json + source_records.json, unmodified) ===")
    print(json.dumps(baseline, indent=2))

    # --- Planted defect A: resolving-but-wrong-support citation on a load-bearing constant.
    # The real hardener.ancamide_220x70.ahew=264.0 g/eq cites a page that literally shows
    # "Equivalent Wt/{H} 264" (verified above). We swap its url to a DIFFERENT, live,
    # human-verifiable page (Wikipedia's Epoxy article) that resolves fine but says nothing
    # about Ancamide 220X70's AHEW=264 at all -- wrong page, wrong substance-specificity.
    entries_a = copy.deepcopy(entries)
    entries_a["hardener.ancamide_220x70.ahew"]["url"] = "https://en.wikipedia.org/wiki/Epoxy"
    result_a = evaluate_source_ledger(entries_a, source_records, required_fields)
    print("\n=== PLANTED DEFECT A: swap AHEW=264 citation to a resolving-but-non-supporting URL ===")
    print(json.dumps(result_a, indent=2))
    print(f"uncited_constants_rejected still True despite wrong-support citation: "
          f"{result_a['gates']['uncited_constants_rejected'] is True}")

    # --- Planted defect B: a URL string that is syntactically present but does NOT resolve
    # at all (dead domain). Contrast with the REAL xylene SDS citation in facts.json, which
    # returns HTTP 403 (Cloudflare bot-wall) under automated verification -- i.e. an
    # unresolvable citation already lives in production and the gate cannot see it either.
    entries_b = copy.deepcopy(entries)
    entries_b["hardener.ancamide_220x70.ahew"]["url"] = "https://this-domain-does-not-exist-amphora-t14.invalid/dead.pdf"
    result_b = evaluate_source_ledger(entries_b, source_records, required_fields)
    print("\n=== PLANTED DEFECT B: swap AHEW=264 citation to a non-existent domain (never resolves) ===")
    print(json.dumps(result_b, indent=2))
    print(f"uncited_constants_rejected still True despite dead-domain citation: "
          f"{result_b['gates']['uncited_constants_rejected'] is True}")

    # --- Planted defect C: malformed / ISO-690-incoherent source record. Every required
    # field is present-and-non-null (so incomplete_records will NOT flag it) but every value
    # is garbage: not a real date, not a real URL-status enum, non-numeric tolerance, etc.
    records_c = copy.deepcopy(source_records)
    malformed = {f: "garbage-not-a-real-value-###" for f in required_fields}
    malformed["id"] = "SRC-T14-PLANTED-MALFORMED"
    malformed["numeric_tolerance"] = "not-a-number"
    malformed["url_status"] = "not_a_real_status_enum_value"
    malformed["revision_date"] = "35th of Undecember, year zero"
    records_c.append(malformed)
    result_c = evaluate_source_ledger(entries, records_c, required_fields)
    print("\n=== PLANTED DEFECT C: append a fully-populated but semantically garbage/malformed source record ===")
    print(json.dumps(result_c, indent=2))
    baseline_incomplete = baseline["metrics"]["incomplete_source_record_count"]
    c_incomplete = result_c["metrics"]["incomplete_source_record_count"]
    print(f"incomplete_source_record_count unchanged ({baseline_incomplete} -> {c_incomplete}) "
          f"despite appended malformed record: {baseline_incomplete == c_incomplete}")


if __name__ == "__main__":
    main()
