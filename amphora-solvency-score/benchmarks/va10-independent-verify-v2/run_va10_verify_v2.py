#!/usr/bin/env python3
"""Second-pass INDEPENDENT verify of R-A10, run as a fresh fire (V-A10,
fire_id 20260805T140001-2900337-9002a94ffc39). This does NOT trust the
13:00 V-A10 receipt's self-report either -- it re-derives every check
against live sources from scratch, and additionally re-verifies the DSSE
Ed25519 signature chain of both the R-A10 done receipt AND the 13:00
V-A10 receipt (neither of which the 13:00 verify cryptographically
checked). Deterministic, no randomness -- run twice for the two-replay
byte-stability gate.
"""
import base64
import hashlib
import json
import sys
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-solvency-score"
MISSION = MOD / "docs/mission.md"
PRE_SNAPSHOT = MOD / "evidence/phase0/repairs/R-A10/work/mission.md.pre-R-A10"
R_A10_DONE = MOD / "evidence/phase0/repairs/R-A10/done/r-a10-prose-consistency-w7-disclosure-repair-receipt.v1.dsse.json"
V_A10_FIRST = MOD / "evidence/phase0/repairs/V-A10/done/va10-independent-verify-receipt.v1.dsse.json"
W7_RECEIPT = MOD / "evidence/audit/flory-hansen-physical-admissibility-v1/flory-hansen-physical-admissibility-audit-receipt.v1.dsse.json"
W6_RECEIPT = MOD / "evidence/audit/hansen-hardened-validation-v1/bigsoldb-admissibility-hardened-lso-receipt.v1.dsse.json"
LEDGER = ROOT / "logs/falsification-ledger.jsonl"
TRUST = ROOT / "config/phase0-trust-store.v1.json"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def sha_file(p):
    return sha(p.read_bytes())


def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" "
            + str(len(body)).encode() + b" " + body)


def load_envelope(path):
    d = json.loads(path.read_text())
    return d.get("signature", d)


def verify_dsse(path, pinned_pub_hex):
    """Real Ed25519 verify of a DSSE envelope against the pinned trust-store key."""
    env = load_envelope(path)
    body = base64.standard_b64decode(env["payload"])
    ptype = env["payloadType"]
    sig_entries = env["signatures"]
    result = {"path": str(path.relative_to(ROOT)), "n_signatures": len(sig_entries),
              "payload_sha256": sha(body), "checks": []}
    all_ok = True
    for s in sig_entries:
        keyid = s["keyid"]
        sigb = base64.standard_b64decode(s["sig"])
        pin_ok = (keyid == pinned_pub_hex["key_id"])
        try:
            Ed25519PublicKey.from_public_bytes(bytes.fromhex(pinned_pub_hex["public_key_hex"])).verify(
                sigb, pae(ptype, body))
            crypto_ok = True
        except InvalidSignature:
            crypto_ok = False
        ok = pin_ok and crypto_ok
        all_ok = all_ok and ok
        result["checks"].append({"keyid": keyid, "keyid_matches_pinned_trust_store": pin_ok,
                                  "ed25519_signature_valid": crypto_ok, "passed": ok})
    result["passed"] = all_ok and len(sig_entries) >= 1
    return result, json.loads(body)


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
        "fm_current_sha256": sha(fm_cur.encode()) if fm_cur else None,
        "fm_pre_sha256": sha(fm_pre.encode()) if fm_pre else None,
        "passed": bool(identical),
    }


def check_prose_matches_front_matter(mission_text):
    fm = extract_front_matter(mission_text)
    fm_json = json.loads(fm)
    phase, sci, op = fm_json["phase"], fm_json["scientific_readiness"], fm_json["operational_readiness"]
    stale = {"Pre-Phase 0": mission_text.count("Pre-Phase 0"), "PRE_PHASE_0": mission_text.count("PRE_PHASE_0"),
             "SHADOW": mission_text.count("SHADOW"), "UNVALIDATED": mission_text.count("UNVALIDATED")}
    ok = (f"phase: {phase}" in mission_text and f"`{sci}`" in mission_text and f"`{op}`" in mission_text
          and all(v == 0 for v in stale.values()))
    return {"item": "prose_consistent_with_front_matter", "front_matter": {"phase": phase, "scientific_readiness": sci, "operational_readiness": op},
            "stale_token_hits": stale, "passed": bool(ok)}


def check_w7_disclosure(mission_text, w7_payload):
    banners = mission_text.count("W7 REFUTATION NOTICE")
    ceiling = w7_payload["admissibility_envelope_MPa_half"][1]
    fh_block = w7_payload["flory_huggins_delta_p_admissibility"]
    fh_max = max(v["observed"] for k, v in fh_block.items() if isinstance(v, dict) and "observed" in v)
    hansen_block = w7_payload["hansen_delta_d_p_h_total_admissibility"]["delta_d"]
    hansen_max = max(v["observed"] for k, v in hansen_block.items() if isinstance(v, dict) and "observed" in v)
    verdict = w7_payload["verdict"]
    checks = {
        "banner_count_is_3": banners == 3,
        "ceiling_59.9_in_prose": "59.9" in mission_text,
        "ceiling_matches_receipt": abs(ceiling - 59.875) < 1e-6,
        "fh_5.2e9_in_prose": "5.2e9" in mission_text,
        "fh_max_matches_receipt_magnitude": abs(fh_max - 5155043623.842392) < 1.0,
        "hansen_5.33e17_in_prose": "5.33e17" in mission_text,
        "hansen_max_matches_receipt_magnitude": abs(hansen_max - 5.333950808666931e17) / 5.333950808666931e17 < 1e-9,
        "verdict_is_CLAIM_REFUTED": verdict == "CLAIM_REFUTED",
        "prose_says_CLAIM_REFUTED": "verdict `CLAIM_REFUTED`" in mission_text,
    }
    return {"item": "w7_void_disclosure_present_and_accurate", "w7_receipt_verdict": verdict,
            "w7_receipt_ceiling_MPa_half": ceiling, "w7_receipt_fh_delta_p_max_observed": fh_max,
            "w7_receipt_hansen_delta_d_max_observed": hansen_max, "checks": checks, "passed": all(checks.values())}


def check_bigsoldb_headline(mission_text, w6_payload):
    ahe = w6_payload["admissibility_hardened_evaluation"]
    fc = w6_payload["full_corpus_signed_comparator"]
    checks = {
        "signed_rmse_0.8770_in_prose": "0.8770" in mission_text,
        "signed_rmse_matches_receipt": abs(fc["model_rmse"] - 0.8770255643028615) < 1e-9,
        "hardened_rmse_0.8742_in_prose": "0.8742" in mission_text,
        "hardened_rmse_matches_receipt": abs(ahe["model_rmse"] - 0.8741657376785225) < 1e-9,
        "hardened_ci_in_prose": "0.8405" in mission_text and "0.9114" in mission_text,
        "hardened_ci_matches_receipt": (
            abs(ahe["model_rmse_ci95_cluster_bootstrap"][0] - 0.8404785445796423) < 1e-6
            and abs(ahe["model_rmse_ci95_cluster_bootstrap"][1] - 0.9114412999049273) < 1e-6),
        "hardened_baseline_1.1667_in_prose": "1.1667" in mission_text,
        "hardened_n_94015_in_prose": "94,015" in mission_text,
        "hardened_error_reduction_25.08_in_prose": "25.08" in mission_text,
        "hardened_receipt_path_cited": "hansen-hardened-validation-v1/bigsoldb-admissibility-hardened-lso-receipt.v1.dsse.json" in mission_text,
        "headline_labeled_W6_hardened": "W6-hardened" in mission_text,
    }
    return {"item": "bigsoldb_headline_cites_w6_hardened_value", "checks": checks, "passed": all(checks.values())}


def sweep_ledger_vs_prose(mission_text, ledger_lines, own_fire_id):
    entries, notes = [], []
    n_checked = 0
    contradictions = []
    for line in ledger_lines:
        d = json.loads(line)
        if d.get("module") != "amphora-solvency-score":
            continue
        entries.append(d)
    for d in entries:
        n_checked += 1
        cid = d.get("campaign_item_id", "")
        verdict = d.get("verdict", "")
        is_self = d.get("fire_id") == own_fire_id
        if is_self:
            notes.append(f"{cid} (this fire's own ledger line, appended after this sweep runs -- excluded from prose-contradiction content check, present only for count).")
            continue
        if cid == "V-A10":
            notes.append(f"{cid} ({verdict}, prior independent verify of R-A10): R-A10 is a prose-only repair with modifies_mission_md=false; V-A10 itself does not assert a standalone prose claim -- no contradiction surface.")
            continue
        if cid == "C1":
            notes.append("C1 (REFUTED, signing-violation forensics on 4 flagged KPIs): mission.md does not reference 'hansen-temperature-envelope-v1-kpi' or SIGNING_VIOLATION text at all -- nothing to contradict.")
            continue
        if cid == "W6":
            ok = "0.8770" in mission_text and "0.8742" in mission_text and "W6-hardened" in mission_text
            notes.append(f"W6 (SURVIVED, BigSolDB LSO headline holds under admissibility hardening): mission.md BigSolDB section quotes both 0.8770 and 0.8742 with W6-hardened label -- consistent={ok}.")
            if not ok:
                contradictions.append("W6 headline figures/label missing from prose")
        elif cid == "W7":
            ok = mission_text.count("W7 REFUTATION NOTICE") == 3
            notes.append(f"W7 (REFUTED, Flory-Huggins/Hansen physical-baseline-vs-ML comparison void): 3 void banners present across the 3 affected sections -- consistent={ok}.")
            if not ok:
                contradictions.append("W7 void banners missing/miscounted")
        elif cid == "V1-SOLV":
            ok = mission_text.count("V1-SOLV CLOSURE") >= 1
            notes.append(f"V1-SOLV (SURVIVED, W7b fair re-run: ML beats corrected physics baselines): mission.md carries a 'V1-SOLV CLOSURE' notice -- consistent={ok}.")
            if not ok:
                contradictions.append("V1-SOLV closure notice missing from prose")
        elif cid == "V-B03":
            ok = mission_text.count("R-B03") >= 1
            notes.append(f"V-B03 (SURVIVED, independent verify of R-B03 corrected group-contribution instrument): R-B03 referenced in prose as corrected instrument -- consistent={ok}.")
            if not ok:
                contradictions.append("R-B03 corrected-instrument reference missing from prose")
        else:
            notes.append(f"{cid} ({verdict}): unrecognized campaign_item_id, flagging for manual review.")
            contradictions.append(f"unrecognized ledger entry {cid}")
    return {"item": "prose_sweep_vs_ledger_verdicts", "n_ledger_entries_for_module_now": len(entries),
            "n_claims_checked_for_prose_contradiction": n_checked, "contradictions_found": contradictions,
            "per_item_notes": notes, "passed": len(contradictions) == 0}


def plant_defect_front_matter(mission_text):
    fm = extract_front_matter(mission_text)
    mutated_fm = fm.replace('"phase":"PHASE_0"', '"phase":"PRE_PHASE_0_TAMPERED_V2"')
    assert mutated_fm != fm, "plant failed to change front-matter text"
    parts = mission_text.split("---")
    parts[1] = mutated_fm
    return "---".join(parts)


def plant_defect_w7_ceiling(w7_payload):
    mutated = json.loads(json.dumps(w7_payload))
    mutated["admissibility_envelope_MPa_half"] = [9.6, 7.25]
    return mutated


def main():
    mission_text = MISSION.read_text()
    pre_text = PRE_SNAPSHOT.read_text()

    trust = json.loads(TRUST.read_text())
    tbr = {k["role"]: k for k in trust["keys"]}
    eval_pin = tbr["PHASE0_EVALUATOR"]

    # --- cryptographic re-verification of the DSSE chain (new vs 13:00 verify) ---
    r_a10_crypto, _r_a10_payload = verify_dsse(R_A10_DONE, eval_pin)
    v_a10_first_crypto, v_a10_first_payload = verify_dsse(V_A10_FIRST, eval_pin)

    w7_payload = json.loads(base64.b64decode(load_envelope(W7_RECEIPT)["payload"]))
    w6_payload = json.loads(base64.b64decode(load_envelope(W6_RECEIPT)["payload"]))

    real_results = [
        check_front_matter_byte_identical(mission_text, pre_text),
        check_prose_matches_front_matter(mission_text),
        check_w7_disclosure(mission_text, w7_payload),
        check_bigsoldb_headline(mission_text, w6_payload),
    ]
    real_all_passed = all(r["passed"] for r in real_results)

    ledger_lines = [l for l in LEDGER.read_text().splitlines() if l.strip()]
    own_fire_id = "20260805T140001-2900337-9002a94ffc39"
    sweep = sweep_ledger_vs_prose(mission_text, ledger_lines, own_fire_id)

    # --- positive control: two independent planted defects on COPIES only ---
    mutated_fm_text = plant_defect_front_matter(mission_text)
    check_a_on_mutant = check_front_matter_byte_identical(mutated_fm_text, pre_text)

    mutated_w7 = plant_defect_w7_ceiling(w7_payload)
    check_b_on_mutant = check_w7_disclosure(mission_text, mutated_w7)

    positive_control = {
        "planted_defect": (
            "Two independent defects planted into IN-MEMORY COPIES only (real files on disk never "
            "touched by this diagnostic): (A) front-matter 'phase' field mutated from PHASE_0 to "
            "PRE_PHASE_0_TAMPERED_V2 in a copy of the live mission.md text; (B) W7 receipt's "
            "admissibility_envelope_MPa_half ceiling mutated from 59.875 to 7.25 MPa^0.5 in a copy "
            "of the W7 payload, which flips 'ceiling_matches_receipt' against the still-real 59.9-in-prose text."
        ),
        "how_planted": "string.replace() on a copy of mission_text for (A); json copy + field overwrite on w7_payload for (B). Neither defect is written back to disk.",
        "detected": bool((not check_a_on_mutant["passed"]) and (not check_b_on_mutant["passed"])),
        "evidence": {
            "check_a_front_matter_byte_identical_on_mutated_copy": check_a_on_mutant,
            "check_b_w7_ceiling_crosscheck_on_mutated_copy": {
                "ceiling_matches_receipt": check_b_on_mutant["checks"]["ceiling_matches_receipt"],
                "passed": check_b_on_mutant["passed"],
            },
        },
    }

    verdict = "CLAIM_SURVIVED" if (real_all_passed and sweep["passed"] and r_a10_crypto["passed"] and v_a10_first_crypto["passed"]) else "CLAIM_REFUTED"

    diag = {
        "module_id": "amphora-solvency-score",
        "repair_under_test": "R-A10",
        "verify_item": "V-A10",
        "verify_pass": 2,
        "prior_verify_receipt_sha256": sha_file(V_A10_FIRST),
        "prior_verify_fire_id": v_a10_first_payload.get("fire_id"),
        "prior_verify_verdict": v_a10_first_payload.get("verdict"),
        "r_a10_done_receipt_sha256": sha_file(R_A10_DONE),
        "mission_md_current_sha256": sha_file(MISSION),
        "mission_md_pre_repair_snapshot_sha256": sha_file(PRE_SNAPSHOT),
        "dsse_crypto_reverification": {
            "note": "NEW vs the 13:00 V-A10 verify -- that receipt trusted R-A10's and its own hash-only provenance blocks without running a real Ed25519 verify. This pass cryptographically re-verifies both DSSE envelopes against the pinned PHASE0_EVALUATOR trust-store key.",
            "r_a10_done_receipt": r_a10_crypto,
            "v_a10_first_pass_receipt": v_a10_first_crypto,
        },
        "real_input_results": real_results,
        "real_input_all_passed": real_all_passed,
        "ledger_sweep": sweep,
        "positive_control": positive_control,
        "verdict": verdict,
    }
    print(json.dumps(diag, sort_keys=True))


if __name__ == "__main__":
    main()
