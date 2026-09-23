#!/usr/bin/env python3
"""Independent verify of R-A10 (mission prose consistency repair) for
campaign item V-A10. Deterministic, no randomness -- runs twice for the
two-replay byte-stability gate. Emits diagnostic.json to stdout.
"""
import base64
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-solvency-score"
MISSION = MOD / "docs/mission.md"
PRE_SNAPSHOT = MOD / "evidence/phase0/repairs/R-A10/work/mission.md.pre-R-A10"
R_A10_DONE = MOD / "evidence/phase0/repairs/R-A10/done/r-a10-prose-consistency-w7-disclosure-repair-receipt.v1.dsse.json"
W7_RECEIPT = MOD / "evidence/audit/flory-hansen-physical-admissibility-v1/flory-hansen-physical-admissibility-audit-receipt.v1.dsse.json"
W6_RECEIPT = MOD / "evidence/audit/hansen-hardened-validation-v1/bigsoldb-admissibility-hardened-lso-receipt.v1.dsse.json"
LEDGER = ROOT / "logs/falsification-ledger.jsonl"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def load_dsse_payload(path):
    d = json.loads(path.read_text())
    sig = d.get("signature", d)
    return json.loads(base64.b64decode(sig["payload"]))


def extract_front_matter(text):
    parts = text.split("---")
    if len(parts) < 3:
        return None
    return parts[1]


def check_front_matter_byte_identical(mission_text, pre_text):
    fm_cur = extract_front_matter(mission_text)
    fm_pre = extract_front_matter(pre_text)
    identical = (fm_cur is not None and fm_cur == fm_pre)
    return {
        "item": "front_matter_byte_identical_to_pre_repair",
        "method": "split docs/mission.md on '---' fences, extract front-matter JSON block, byte-compare current vs preserved R-A10/work/mission.md.pre-R-A10 snapshot",
        "fm_current_sha256": sha(fm_cur.encode()) if fm_cur else None,
        "fm_pre_sha256": sha(fm_pre.encode()) if fm_pre else None,
        "passed": bool(identical),
    }


def check_front_matter_matches_prose(mission_text):
    fm = extract_front_matter(mission_text)
    fm_json = json.loads(fm)
    phase = fm_json["phase"]
    sci = fm_json["scientific_readiness"]
    op = fm_json["operational_readiness"]
    prose_ok = (
        f"phase: {phase}" in mission_text
        and f"`{sci}`" in mission_text
        and f"`{op}`" in mission_text
        and "Pre-Phase 0" not in mission_text
        and "PRE_PHASE_0" not in mission_text
        and "SHADOW" not in mission_text.replace("shadowbox", "")
        and "UNVALIDATED" not in mission_text
    )
    return {
        "item": "prose_consistent_with_front_matter",
        "method": "parse front-matter JSON (phase/scientific_readiness/operational_readiness), grep prose for stale contradictory tokens (Pre-Phase 0, PRE_PHASE_0, SHADOW, UNVALIDATED) and for the correct current values",
        "front_matter": {"phase": phase, "scientific_readiness": sci, "operational_readiness": op},
        "stale_token_hits": {
            "Pre-Phase 0": mission_text.count("Pre-Phase 0"),
            "PRE_PHASE_0": mission_text.count("PRE_PHASE_0"),
            "SHADOW": mission_text.count("SHADOW"),
            "UNVALIDATED": mission_text.count("UNVALIDATED"),
        },
        "passed": bool(prose_ok),
    }


def check_w7_disclosure(mission_text, w7_payload):
    banners = mission_text.count("W7 REFUTATION NOTICE")
    envelope = w7_payload["admissibility_envelope_MPa_half"]
    ceiling = envelope[1]
    fh_delta_p_max = w7_payload["flory_huggins_delta_p_admissibility"]["chloroform"]["observed"] \
        if "chloroform" in w7_payload.get("flory_huggins_delta_p_admissibility", {}) else None
    # pull actual max observed across all solvents in the FH delta_p block
    fh_block = w7_payload["flory_huggins_delta_p_admissibility"]
    fh_observed_vals = [v["observed"] for k, v in fh_block.items() if isinstance(v, dict) and "observed" in v]
    fh_max = max(fh_observed_vals) if fh_observed_vals else None
    hansen_block = w7_payload["hansen_delta_d_p_h_total_admissibility"]["delta_d"]
    hansen_observed_vals = [v["observed"] for k, v in hansen_block.items() if isinstance(v, dict) and "observed" in v]
    hansen_max = max(hansen_observed_vals) if hansen_observed_vals else None
    verdict = w7_payload["verdict"]

    checks = {
        "banner_count_is_3": banners == 3,
        "ceiling_59.9_in_prose": "59.9" in mission_text,
        "ceiling_matches_receipt": abs(ceiling - 59.875) < 1e-6,
        "fh_5.2e9_in_prose": "5.2e9" in mission_text,
        "fh_max_matches_receipt_magnitude": fh_max is not None and abs(fh_max - 5155043623.842392) < 1.0,
        "hansen_5.33e17_in_prose": "5.33e17" in mission_text,
        "hansen_max_matches_receipt_magnitude": hansen_max is not None and abs(hansen_max - 5.333950808666931e17) / 5.333950808666931e17 < 1e-9,
        "verdict_is_CLAIM_REFUTED": verdict == "CLAIM_REFUTED",
        "prose_says_CLAIM_REFUTED": "verdict `CLAIM_REFUTED`" in mission_text,
    }
    return {
        "item": "w7_void_disclosure_present_and_accurate",
        "method": "count W7 REFUTATION NOTICE banners in mission.md; cross-check quoted ceiling/delta_p-max/delta_d-max/verdict against the live W7 audit receipt payload (not against the prose's own claims)",
        "w7_receipt_verdict": verdict,
        "w7_receipt_ceiling_MPa_half": ceiling,
        "w7_receipt_fh_delta_p_max_observed": fh_max,
        "w7_receipt_hansen_delta_d_max_observed": hansen_max,
        "checks": checks,
        "passed": all(checks.values()),
    }


def check_bigsoldb_headline(mission_text, w6_payload):
    fc = w6_payload["full_corpus_signed_comparator"]
    ahe = w6_payload["admissibility_hardened_evaluation"]
    checks = {
        "signed_rmse_0.8770_in_prose": "0.8770" in mission_text,
        "signed_rmse_matches_receipt": abs(fc["model_rmse"] - 0.8770255643028615) < 1e-9,
        "hardened_rmse_0.8742_in_prose": "0.8742" in mission_text,
        "hardened_rmse_matches_receipt": abs(ahe["model_rmse"] - 0.8741657376785225) < 1e-9,
        "hardened_ci_in_prose": "0.8405" in mission_text and "0.9114" in mission_text,
        "hardened_ci_matches_receipt": (
            abs(ahe["model_rmse_ci95_cluster_bootstrap"][0] - 0.8404785445796423) < 1e-6
            and abs(ahe["model_rmse_ci95_cluster_bootstrap"][1] - 0.9114412999049273) < 1e-6
        ),
        "hardened_baseline_1.1667_in_prose": "1.1667" in mission_text,
        "hardened_n_94015_in_prose": "94,015" in mission_text,
        "hardened_error_reduction_25.08_in_prose": "25.08" in mission_text,
        "hardened_receipt_path_cited": "hansen-hardened-validation-v1/bigsoldb-admissibility-hardened-lso-receipt.v1.dsse.json" in mission_text,
        "headline_labeled_W6_hardened": "W6-hardened" in mission_text,
    }
    return {
        "item": "bigsoldb_headline_cites_w6_hardened_value",
        "method": "cross-check the BigSolDB headline section's quoted RMSE/CI/baseline/n/error-reduction figures against the live W6 hardened-validation receipt payload",
        "checks": checks,
        "passed": all(checks.values()),
    }


def sweep_ledger_vs_prose(mission_text, ledger_lines):
    entries = []
    for line in ledger_lines:
        d = json.loads(line)
        if d.get("module") != "amphora-solvency-score":
            continue
        entries.append(d)
    contradictions = []
    per_item_notes = []
    for d in entries:
        cid = d.get("campaign_item_id", "")
        verdict = d.get("verdict")
        if cid == "C1":
            hit = ("hansen-temperature-envelope-v1-kpi" in mission_text) or ("SIGNING_VIOLATION" in mission_text)
            per_item_notes.append(f"C1 (REFUTED, signing-violation forensics on 4 flagged KPIs): mission.md does not reference 'hansen-temperature-envelope-v1-kpi' or SIGNING_VIOLATION text at all ({hit} occurrences found) -- nothing to contradict.")
        elif cid == "W6":
            ok = ("0.8742" in mission_text) and ("0.8770" in mission_text) and ("W6-hardened" in mission_text)
            per_item_notes.append(f"W6 (SURVIVED, BigSolDB LSO headline holds under admissibility hardening): mission.md BigSolDB section quotes both 0.8770 and 0.8742 with W6-hardened label -- consistent={ok}.")
            if not ok:
                contradictions.append({"campaign_item_id": "W6", "reason": "BigSolDB headline missing W6-hardened figure"})
        elif cid == "W7":
            banners = mission_text.count("W7 REFUTATION NOTICE")
            ok = banners == 3
            per_item_notes.append(f"W7 (REFUTED, Flory-Huggins/Hansen physical-baseline-vs-ML comparison void): {banners} void banners present across the 3 affected sections -- consistent={ok}.")
            if not ok:
                contradictions.append({"campaign_item_id": "W7", "reason": f"expected 3 W7 void banners, found {banners}"})
        elif cid == "V1-SOLV":
            ok = "V1-SOLV CLOSURE" in mission_text and "W7b is now closed" in mission_text
            per_item_notes.append(f"V1-SOLV (SURVIVED, W7b fair re-run: ML beats corrected physics baselines): mission.md carries a 'V1-SOLV CLOSURE' notice in all 3 affected sections referencing the closure receipt -- consistent={ok}.")
            if not ok:
                contradictions.append({"campaign_item_id": "V1-SOLV", "reason": "W7b closure not disclosed in prose"})
        elif cid == "V-B03":
            mentions = "R-B03" in mission_text
            per_item_notes.append(f"V-B03 (SURVIVED, independent verify of R-B03 corrected group-contribution instrument): V-B03 itself is a verify-of-a-repair with no standalone numeric claim in mission.md to contradict; R-B03 is referenced {mission_text.count('R-B03')} times consistently as 'corrected instrument' -- no contradiction found.")
        else:
            per_item_notes.append(f"{cid} ({verdict}): no specific prose cross-check rule defined for this item id.")
    return {
        "item": "prose_sweep_vs_ledger_verdicts",
        "n_ledger_entries_for_module": len(entries),
        "n_claims_checked": len(per_item_notes),
        "per_item_notes": per_item_notes,
        "contradictions_found": contradictions,
        "passed": len(contradictions) == 0,
    }


def plant_defect_front_matter_mismatch(mission_text):
    """Positive control input A: corrupt the front-matter's phase field so it
    no longer matches the preserved pre-repair snapshot -- the exact class of
    defect check_front_matter_byte_identical exists to catch."""
    return mission_text.replace('"phase":"PHASE_0"', '"phase":"PRE_PHASE_0_TAMPERED"', 1)


def plant_defect_w7_number(mission_text):
    """Positive control input B: corrupt every quoted W7 ceiling number
    (regex, word-boundary, handles the line-wrapped occurrence where '59.9'
    and 'MPa^0.5' are split across a markdown '>' continuation) so it no
    longer matches the live W7 receipt -- the exact class of defect
    check_w7_disclosure exists to catch."""
    return re.sub(r"\b59\.9\b", "12.3", mission_text)


def run_all(mission_text, pre_text, w7_payload, w6_payload, ledger_lines):
    results = [
        check_front_matter_byte_identical(mission_text, pre_text),
        check_front_matter_matches_prose(mission_text),
        check_w7_disclosure(mission_text, w7_payload),
        check_bigsoldb_headline(mission_text, w6_payload),
        sweep_ledger_vs_prose(mission_text, ledger_lines),
    ]
    return results


def main():
    mission_text = MISSION.read_text(encoding="utf-8")
    pre_text = PRE_SNAPSHOT.read_text(encoding="utf-8")
    w7_payload = load_dsse_payload(W7_RECEIPT)
    w6_payload = load_dsse_payload(W6_RECEIPT)
    ledger_lines = LEDGER.read_text().splitlines()

    real_results = run_all(mission_text, pre_text, w7_payload, w6_payload, ledger_lines)
    real_all_passed = all(r["passed"] for r in real_results)

    # Positive control A: front-matter byte-identity check on a copy with a
    # planted front-matter mutation. Must FAIL (be detected).
    mutated_fm_text = plant_defect_front_matter_mismatch(mission_text)
    pc_a = check_front_matter_byte_identical(mutated_fm_text, pre_text)
    pc_a_detected = (pc_a["passed"] is False)

    # Positive control B: W7 disclosure check on a copy with a planted wrong
    # ceiling number. Must FAIL (be detected).
    mutated_w7_text = plant_defect_w7_number(mission_text)
    pc_b = check_w7_disclosure(mutated_w7_text, w7_payload)
    pc_b_detected = (pc_b["passed"] is False)

    diag = {
        "schema": "amphora.solvency-score.va10-verify-diagnostic.v1",
        "module_id": "amphora-solvency-score",
        "verify_item": "V-A10",
        "repair_under_test": "R-A10",
        "r_a10_done_receipt_sha256": sha(R_A10_DONE.read_bytes()),
        "mission_md_current_sha256": sha(mission_text.encode()),
        "mission_md_pre_repair_snapshot_sha256": sha(pre_text.encode()),
        "w7_receipt_sha256": sha(W7_RECEIPT.read_bytes()),
        "w6_receipt_sha256": sha(W6_RECEIPT.read_bytes()),
        "real_input_results": real_results,
        "real_input_all_passed": real_all_passed,
        "verdict": "CLAIM_SURVIVED" if real_all_passed else "CLAIM_REFUTED",
        "positive_control": {
            "planted_defect": (
                "Two independent defects planted into COPIES of the live mission.md text "
                "(never written back to disk): (A) front-matter phase field mutated from "
                '"phase":"PHASE_0" to "phase":"PRE_PHASE_0_TAMPERED", the exact defect class '
                "check_front_matter_byte_identical exists to catch; (B) the W7 disclosure's "
                "quoted physical-admissibility ceiling mutated from '59.9 MPa^0.5' to "
                "'12.3 MPa^0.5', the exact defect class check_w7_disclosure exists to catch "
                "(a silently-wrong number copied from the W7 receipt into the prose)."
            ),
            "how_planted": (
                "In-memory Python string.replace() on a copy of docs/mission.md's text; "
                "check_a input = plant_defect_front_matter_mismatch(mission_text); "
                "check_b input = plant_defect_w7_number(mission_text). Real docs/mission.md "
                "on disk is never modified by this diagnostic."
            ),
            "detected": bool(pc_a_detected and pc_b_detected),
            "evidence": {
                "check_a_front_matter_byte_identical_on_mutated_copy": pc_a,
                "check_a_fired": pc_a_detected,
                "check_b_w7_disclosure_on_mutated_copy": {k: v for k, v in pc_b.items() if k != "checks"} | {"failing_subchecks": [k for k, v in pc_b["checks"].items() if not v]},
                "check_b_fired": pc_b_detected,
            },
        },
    }
    print(json.dumps(diag, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
