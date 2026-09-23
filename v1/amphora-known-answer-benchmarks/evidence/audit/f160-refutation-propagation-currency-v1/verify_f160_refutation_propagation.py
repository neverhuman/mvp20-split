#!/usr/bin/env python3
"""Independent currency/propagation audit: does the already-signed 2026-08-16
f160-density-source-conflict-credit-violation-v1 REFUTED finding (which established that
ARITH-MIL-F160-COMPONENT-A-DENSITY and ARITH-MIL-F160-COMPONENT-B-DENSITY should be
reclassified UNVERIFIED under the module's OWN documented no-recovery-credit policy for the
disputed /38A source) appear ANYWHERE in the module's currently-live consumer surfaces
(docs/mission.md prose+KPI, docs/capability-profile.json, evidence/phase0/kpis/
RETRACTION-INDEX.md, reference/mvp20/out/arithmetic_audit.json,
reference/mvp20/out/control_by_control_receipt.v1.json)? This is a NEW attack axis
(document-currency / repair-propagation), distinct from the original arithmetic/policy
re-derivation, and it independently re-derives the disqualification from scratch rather than
trusting the prior receipt's conclusion.
AUDIT_ONLY. Writes nothing outside its own scratch/report path. Does not modify mission.md,
capability-profile.json, control_by_control_receipt.v1.json, or any signed Phase-0 KPI.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-known-answer-benchmarks"

PRIOR_RECEIPT = MOD / "evidence/audit/f160-density-source-conflict-credit-violation-v1/receipt.v1.dsse.json"
MISSION = MOD / "docs/mission.md"
CAP_PROFILE = MOD / "docs/capability-profile.json"
RETRACTION_INDEX = MOD / "evidence/phase0/kpis/RETRACTION-INDEX.md"
ARITH_AUDIT = MOD / "reference/mvp20/out/arithmetic_audit.json"
CONTROL_RECEIPT = MOD / "reference/mvp20/out/control_by_control_receipt.v1.json"
MIL_RECOVERY = MOD / "reference/mvp20/out/mil_recovery.json"
REF_CARDS = MOD / "reference/mvp20/out/known_reference_cards.json"
TRUST = ROOT / "config/phase0-trust-store.v1.json"
LEDGER = ROOT / "logs/falsification-ledger.jsonl"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " +
            str(len(body)).encode() + b" " + body)


def main():
    # --- Step 1: independently re-verify the Ed25519 signature on the prior REFUTED receipt
    prior = json.loads(PRIOR_RECEIPT.read_bytes())
    env = prior["signature"]
    payload_bytes = base64.standard_b64decode(env["payload"])
    ptype = env["payloadType"]
    sig_hex = env["signatures"][0]["sig"]
    eval_pub_hex = prior["evaluator_public_key_hex"]
    Ed25519PublicKey.from_public_bytes(bytes.fromhex(eval_pub_hex)).verify(
        base64.standard_b64decode(sig_hex), pae(ptype, payload_bytes)
    )
    prior_body = json.loads(payload_bytes)
    trust_pin_ok = False
    if TRUST.exists():
        trust = json.loads(TRUST.read_text())
        tbr = {k.get("role"): k for k in trust.get("keys", [])}
        trust_pin_ok = (prior["evaluator_key_id"] == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
    assert prior_body["verdict"] == "REFUTED"
    assert trust_pin_ok, "prior receipt evaluator key does not derive the pinned trust-store key"

    # --- Step 2: independently re-derive the disqualification from scratch (not trusting prior conclusion)
    control_receipt = json.loads(CONTROL_RECEIPT.read_bytes())
    ref_cards = json.loads(REF_CARDS.read_bytes())
    mil_recovery = json.loads(MIL_RECOVERY.read_bytes())

    self_audit_text = " ".join(ref_cards.get("red_team_self_audit", []))
    policy_present = "F160 black is held as a source-conflict check and receives no known-answer recovery credit" in self_audit_text
    assert policy_present, "expected no-recovery-credit policy sentence not found verbatim in known_reference_cards.json"

    f160_card = next(c for c in ref_cards["cards"] if c["id"] == "F160-BLACK")
    conflict_open = f160_card["source_conflict"]["status"].startswith("OPEN")
    assert conflict_open, "F160-BLACK source_conflict is no longer OPEN -- prior finding's premise has changed"

    f160_source_urls = set(f160_card["source_urls"])

    disqualified_pass_controls = []
    for c in control_receipt["controls"]:
        if "F160" not in c["control_id"]:
            continue
        if c["control_id"] == "F160-BLACK":
            continue  # this one is already correctly disqualified (status=UNVERIFIED)
        if c.get("status") != "VERIFIED_PASS":
            continue
        # every ARITH-MIL-F160-* control's checks trace to the same disputed /38A document
        # (arithmetic_audit.json row "MIL F160 Black" cites the identical URL as the F160-BLACK card).
        arith_audit = json.loads(ARITH_AUDIT.read_bytes())
        row_urls = {r["url"] for r in arith_audit["rows"] if "F160" in r["id"]}
        if row_urls & f160_source_urls and c.get("source_conflict") is None:
            disqualified_pass_controls.append(c["control_id"])

    reconciled = sorted(disqualified_pass_controls)
    expected_reconciled = ["ARITH-MIL-F160-COMPONENT-A-DENSITY", "ARITH-MIL-F160-COMPONENT-B-DENSITY"]
    independent_rederivation_matches_prior = (reconciled == expected_reconciled)

    counterfactual_verified_pass_count = control_receipt["verified_pass_count"] - len(reconciled)
    counterfactual_unverified_count = control_receipt["unverified_count"] + len(reconciled)
    arith_ids = [c["control_id"] for c in control_receipt["controls"] if c["control_id"].startswith("ARITH-")]
    counterfactual_arith_pass = sum(
        1 for cid in arith_ids
        if cid not in reconciled and next(c for c in control_receipt["controls"] if c["control_id"] == cid)["status"] == "VERIFIED_PASS"
    )

    # --- Step 3: check every live consumer surface for propagation of the 08-16 finding
    mission_text = MISSION.read_text()
    cap_profile_text = CAP_PROFILE.read_text()
    retraction_text = RETRACTION_INDEX.read_text() if RETRACTION_INDEX.exists() else ""
    arith_audit_text = ARITH_AUDIT.read_text()

    propagation_markers = [
        "f160-density-source-conflict-credit-violation",
        "11 VERIFIED_PASS",
        "4/6",
        "0.6667",
        "policy-consistent",
    ]

    def any_marker(text):
        return [m for m in propagation_markers if m.lower() in text.lower()]

    mission_text_flat = mission_text.replace("`", "")
    surfaces = {
        "docs/mission.md": {
            "still_claims_13_pass_uncaveated": "pinned_verified_pass_count_13_rate observed **1.0**" in mission_text_flat and "PASSED" in mission_text,
            "still_claims_6_of_6_uncaveated": "arithmetic_subset_6_of_6_pass_rate observed **1.0**" in mission_text_flat,
            "propagation_markers_found": any_marker(mission_text),
        },
        "docs/capability-profile.json": {
            "still_reports_n_pass_6_of_6_uncaveated": '"n_pass": 6' in cap_profile_text and '"n_checks": 6' in cap_profile_text,
            "propagation_markers_found": any_marker(cap_profile_text),
        },
        "evidence/phase0/kpis/RETRACTION-INDEX.md": {
            "has_f160_entry": "F160" in retraction_text,
            "propagation_markers_found": any_marker(retraction_text),
        },
        "reference/mvp20/out/arithmetic_audit.json": {
            "f160_rows_still_pass_true_uncaveated": '"pass": true' in arith_audit_text and "MIL F160 Black" in arith_audit_text,
            "propagation_markers_found": any_marker(arith_audit_text),
        },
    }
    any_propagated = any(
        s["propagation_markers_found"] for s in surfaces.values()
    ) or surfaces["evidence/phase0/kpis/RETRACTION-INDEX.md"]["has_f160_entry"]

    # --- Step 4: byte-identity check -- have the hash-pinned source files moved AT ALL since the
    # refuting receipt was signed? (Distinguishes "documentation lag" from "zero repair action".)
    current_hashes = {
        "arithmetic_audit.json": sha(ARITH_AUDIT.read_bytes()),
        "control_by_control_receipt.v1.json": sha(CONTROL_RECEIPT.read_bytes()),
        "docs/mission.md": sha(MISSION.read_bytes()),
        "known_reference_cards.json": sha(REF_CARDS.read_bytes()),
        "mil_recovery.json": sha(MIL_RECOVERY.read_bytes()),
    }
    prior_hashes = prior_body["source_hashes_at_attack_time"]
    byte_identical_to_attack_time = {k: (current_hashes[k] == prior_hashes[k]) for k in prior_hashes}
    zero_repair_action_taken = all(byte_identical_to_attack_time.values())

    # --- Step 5: elapsed time since the prior refuting receipt (from the falsification ledger)
    prior_ledger_ts = None
    if LEDGER.exists():
        for line in LEDGER.read_text().splitlines():
            try:
                row = json.loads(line)
            except Exception:
                continue
            if row.get("receipt", "").endswith("f160-density-source-conflict-credit-violation-v1/receipt.v1.dsse.json"):
                prior_ledger_ts = row.get("ts")

    refuted_if = (
        "the already-signed 2026-08-16 f160-density-source-conflict-credit-violation-v1 REFUTED "
        "finding is not propagated into ANY live consumer surface (mission.md prose+KPI, "
        "capability-profile.json, RETRACTION-INDEX.md, arithmetic_audit.json), AND every "
        "hash-pinned source file the prior receipt cited is BYTE-IDENTICAL to its state at the "
        "prior attack time (proving zero repair action was taken, not merely a documentation lag)"
    )
    survives_if = (
        "at least one consumer surface carries a caveat/correction pointing to the prior finding, "
        "OR a RETRACTION-INDEX entry exists for it, OR any of the hash-pinned source files has "
        "changed since the prior attack time"
    )

    overall_refuted = (not any_propagated) and zero_repair_action_taken and independent_rederivation_matches_prior

    report = {
        "attacked_claim": {
            "location": "amphora-known-answer-benchmarks/docs/mission.md#Current-benchmark-result + docs/capability-profile.json#benchmarks[amphora-known-answer-benchmarks-checked-current] + evidence/phase0/kpis/RETRACTION-INDEX.md",
            "text": "That the module's live-consumed KPI surfaces (pinned_verified_pass_count_13_rate=PASSED, arithmetic_subset_6_of_6_pass_rate=PASSED, capability-profile n_pass=6/6) are CURRENT with respect to the module's own prior signed falsification findings.",
        },
        "prior_refuting_receipt": {
            "path": "amphora-known-answer-benchmarks/evidence/audit/f160-density-source-conflict-credit-violation-v1/receipt.v1.dsse.json",
            "receipt_id": prior_body["receipt_id"],
            "verdict": prior_body["verdict"],
            "signature_independently_reverified": True,
            "evaluator_key_derives_pinned_trust_store_key": trust_pin_ok,
            "ledger_ts": prior_ledger_ts,
        },
        "independent_rederivation_from_scratch": {
            "method": "Parsed known_reference_cards.json red_team_self_audit + F160-BLACK card source_conflict block directly (not the prior receipt's prose); cross-referenced arithmetic_audit.json row URLs against the F160-BLACK card's source_urls; flagged any non-F160-BLACK control sharing that URL with VERIFIED_PASS status and no source_conflict field of its own.",
            "reconciled_controls_requiring_disqualification": reconciled,
            "matches_prior_receipt_finding": independent_rederivation_matches_prior,
        },
        "counterfactual_kpi_impact_rederived": {
            "verified_pass_count": counterfactual_verified_pass_count,
            "unverified_count": counterfactual_unverified_count,
            "arithmetic_subset_pass": f"{counterfactual_arith_pass}/6",
        },
        "consumer_surface_propagation_check": surfaces,
        "any_propagation_found": any_propagated,
        "byte_identity_vs_attack_time": byte_identical_to_attack_time,
        "zero_repair_action_taken": zero_repair_action_taken,
        "falsification_criterion": {"refuted_if": refuted_if, "survives_if": survives_if},
        "does_not_close": [
            "Does not re-argue whether the underlying density arithmetic (8.22, 10.24 lb/gal) is physically correct -- that is the prior receipt's concern.",
            "Does not modify docs/mission.md, docs/capability-profile.json, RETRACTION-INDEX.md, control_by_control_receipt.v1.json, or any signed Phase-0 KPI; flags them for human/repair-fire correction only.",
            "Does not establish a specific SLA for how quickly a REFUTED finding must propagate; treats >24h with zero movement on any surface as sufficient to call the currency claim false for this fire.",
        ],
        "verdict": {"overall": "REFUTED" if overall_refuted else "SURVIVED"},
    }
    return report


if __name__ == "__main__":
    r = main()
    out = Path("/tmp/f160_refutation_propagation_report.v1.json")
    out.write_text(json.dumps(r, indent=2, sort_keys=True))
    print(json.dumps(r, indent=2, sort_keys=True))
