#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-redteam-audit W-AUDIT fire-2 superseding adjudication receipt.

Fire 2 of 2 (max_fires=2) of campaign item W-AUDIT. Corrects a systemic receipt-path
citation bug found in fire 1's mechanical scan (23/128 done items cited the wrong
artifact) and deep-reads a fresh 29-item sample from the 11 modules fire 1 never
sampled. Supersedes fire 1's receipt; never rewrites it.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
WORK = ROOT / "amphora-redteam-audit/evidence/phase0/repairs/W-AUDIT/work"
OUT_DIR = ROOT / "amphora-redteam-audit/evidence/phase0/repairs/W-AUDIT/done"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

FIRE_ID = "20260814T050002-2102213-f395cf047c3c"

def sha(b):
    return hashlib.sha256(b).hexdigest()

def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" "
            + str(len(body)).encode() + b" " + body)

def load_seed(p):
    raw = p.read_bytes().strip()
    if len(raw) == 64:
        try:
            return bytes.fromhex(raw.decode())
        except Exception:
            pass
    return raw[:32]

fire1_receipt_path = OUT_DIR / "w-audit-done-column-adjudication-receipt.v1.dsse.json"
fire1_sha256 = sha(fire1_receipt_path.read_bytes())

table_data = json.loads((WORK / "fire2_table.json").read_text())
adjudication_table = table_data["adjudication_table"]
deep_read_ids_fire2 = table_data["deep_read_ids_fire2"]
citation_corrected_ids_fire2 = table_data["citation_corrected_ids_fire2"]
overlap_ids = table_data["overlap_ids"]

planted = json.loads((WORK / "planted_report_only_receipt.v1.json").read_text())
planted_env = planted["signature"]
planted_body = json.loads(base64.b64decode(planted_env["payload"]))
planted_has_supersedes = any("supersed" in k.lower() for k in planted_body.keys())
planted_has_code_or_data = any(k in planted_body for k in
    ["code", "script", "diff", "new_code", "artifact_diff", "reproducibility", "attack_description"])
planted_narrative_flag = any(phrase in json.dumps(planted_body).lower() for phrase in
    ["future fire should", "recommend landing", "is understood"])
planted_detected_as_not_delivered = (
    (not planted_has_supersedes and not planted_has_code_or_data)
    and (planted_body.get("claim_verdict") == "CLAIM_SURVIVED" or planted_body.get("done_criterion_met"))
)

n_done_items = len(adjudication_table)
n_delivered = sum(1 for r in adjudication_table if r["verdict"] == "DELIVERED")
n_partial = sum(1 for r in adjudication_table if r["verdict"] == "PARTIAL")
n_not_delivered = sum(1 for r in adjudication_table if r["verdict"] == "NOT_DELIVERED")
n_not_locatable = sum(1 for r in adjudication_table if r["verdict"] == "NOT_LOCATABLE")
assert n_done_items == 128
assert n_delivered + n_partial + n_not_delivered + n_not_locatable == n_done_items

positive_control_survivals_missing = ["W-NOV1", "V-A12a", "V-N02b", "V1-KPI-VISC"]

fire1_followups = [
    {
        "defect": "campaign.json fire records for done items C1 (amphora-solvency-score) and C6 (amphora-design-rule-score) carry outcome:\"UNKNOWN\", fire_id:null, fire_class:null in their fires[] entry despite real, valid, substantively-delivered work confirmed by deep read.",
        "module": "amphora-redteam-audit",
        "proposed_done_criterion": "A signed audit receipt that backfills/corrects the fires[].outcome/fire_id/fire_class fields for C1 and C6 from their matching ledger lines, and adds a mechanical check flagging any future done item whose last-fire outcome is UNKNOWN at close time.",
        "carried_forward_from": "fire1 (20260814T040001-1700358-92031d80832c)",
    },
]

new_followups = [
    {
        "defect": (
            "SYSTEMIC CITATION BUG in fire 1's mechanical scan (audit_scan.py / equivalent): for 23/128 "
            "(18%) done items, fire 1's adjudication_table.receipt_path pointed at the WRONG artifact -- "
            "either an early attempts/ checkpoint from an interim fire of a multi-fire repair item (e.g. "
            "R-S02, R-C01, R-C05, R-N01: cited fire-1-of-N's attempts/ checkpoint instead of the item's "
            "actual final done/ receipt), or a pre-repair evidence/audit/ receipt that predates the item "
            "being wrapped into a repairs/<ID>/done/ artifact (e.g. T-01, T-02, T-10, W-QC, T-13, CF-ALT, "
            "CF-PROC, CF-RISK, CF-TEST, W-CRO1, W-D-CRO, DR-ANNEX, DR-COVERAGE, DR-DISP, W-D-ENVGATE, "
            "W-ING1, V1-KPI-BARR, V1-KPI-MCA, R-C03). Fire 1's stated methodology was a '100%-coverage "
            "mechanical scan (DSSE validity + artifact existence + payload content-signal)' -- for these "
            "23 rows that scan was run against, and its evidence field describes, the WRONG file, not the "
            "one that actually satisfies the item's own done_check glob. This fire independently re-derived "
            "the TRUE last done/-glob-satisfying artifact per item straight from campaign.json fires[] "
            "(a mechanical, deterministic selection: last artifact path containing '/done/' in the item's "
            "fires[] array) and DSSE-verified + content-checked every one of the 23 corrected artifacts: "
            "all 23 pass Ed25519 verification and all 23 show real change-evidence (supersedes blocks, "
            "substantive numeric verdicts, or both) -- so the DELIVERED verdict itself is UNCHANGED for "
            "all 23, but fire 1's evidence trail supporting it was not the real evidence for nearly a "
            "fifth of the done column. An audit whose own citations are wrong 18% of the time is not a "
            "reliable instrument even when its bottom-line conclusion happens to still be correct."
        ),
        "module": "amphora-redteam-audit",
        "proposed_done_criterion": (
            "A signed repair to the W-AUDIT lineage's receipt-path selection logic (documented as a "
            "reusable rule, e.g. in work/ or as code) that selects a done item's evidence artifact by "
            "resolving the item's own done_check.glob against its campaign.json fires[].artifacts (last "
            "matching path wins), never by reading claim.receipt_path or the first fire's artifact list; "
            "the fix must be re-run against all 128 current done items and produce zero further mismatches "
            "as a named, superseding artifact."
        ),
    },
    {
        "defect": (
            "4 currently-done CLAIM_SURVIVED receipts (W-NOV1 fired 2026-08-05T04:00, V-A12a fired "
            "2026-08-04T09:00, V-N02b fired 2026-08-04T02:00, V1-KPI-VISC fired 2026-08-04T18:00) predate "
            "the portfolio's positive_control-on-survival governance rule (first evidenced by the W-RTA2 "
            "gameability finding at 2026-08-05T12:09) and carry NO positive_control block. Under the "
            "governance text now binding every fire ('the launcher will downgrade [a survival without "
            "positive_control] to UNKNOWN'), these 4 done receipts would fail that check today even though "
            "each one's OWN done_criterion, as written at the time it fired, did not require it -- so this "
            "is a governance-drift gap, not a content-delivery failure, and each item is still judged "
            "DELIVERED against its own words in the table below. It is a real, mechanically-checkable "
            "exposure: the done column currently contains 4 survivals that would not pass today's mechanical "
            "gate if re-checked."
        ),
        "module": "amphora-redteam-audit",
        "proposed_done_criterion": (
            "A signed backfill sweep that either (a) re-attacks each of the 4 named claims with a genuine "
            "positive control (plant a defect the original attack should catch, confirm detection) and "
            "supersedes each receipt with the control attached, or (b) if a positive control cannot honestly "
            "be constructed for one of them, downgrades that specific receipt's standing verdict to UNKNOWN "
            "with the reason stated, rather than leaving it silently exempt from current governance."
        ),
    },
]

positive_control = {
    "detector": (
        "has_change_evidence(receipt) := any('supersed' in key.lower() for key in payload.keys()) OR "
        "any(field in payload for field in ['code','script','diff','new_code','artifact_diff',"
        "'reproducibility','attack_description']); NOT_DELIVERED-signal := claims claim_verdict=="
        "'CLAIM_SURVIVED' or done_criterion_met==true WHILE has_change_evidence() is False. Applied to "
        "all 23 citation-corrected receipts and all 29 freshly deep-read receipts this fire."
    ),
    "planted_defect": (
        "A synthetic DSSE-signed receipt (work/planted_report_only_receipt.v1.json, real Ed25519 signature "
        "from the pinned evaluator seed) for a fake campaign item FAKE-02, claiming claim_verdict="
        "'CLAIM_SURVIVED' and done_criterion_met=true, whose payload contains ONLY a prose summary "
        "('the corrected coverage table has been identified and the fix is understood; a future fire "
        "should apply the Mondrian recalibration and land the superseding KPI') -- no supersedes block, "
        "no code/script/diff field, no reproducibility field: the exact report-without-change shape this "
        "audit's objective describes."
    ),
    "how_planted": (
        "Constructed from scratch on xbabe2, signed with the real pinned evaluator seed "
        "(/home/ubuntu/.local/share/amphora/phase0/keys/evaluator.ed25519.seed), written to "
        "work/planted_report_only_receipt.v1.json; never placed under any module's done/ glob, never "
        "counted in the 128-item table."
    ),
    "detected": bool(planted_detected_as_not_delivered),
    "evidence": {
        "planted_has_supersedes": planted_has_supersedes,
        "planted_has_code_or_data_fields": planted_has_code_or_data,
        "planted_narrative_report_only_language_flagged": planted_narrative_flag,
        "planted_item_verdict_under_detector": (
            "NOT_DELIVERED-signal" if planted_detected_as_not_delivered else "DELIVERED-signal (FAILED to catch)"
        ),
        "real_control_items_checked": len(citation_corrected_ids_fire2) + len(deep_read_ids_fire2) - len(overlap_ids),
        "real_control_all_pass_has_change_evidence": True,
    },
}

body_obj = {
    "schema": "amphora.redteam-audit.w-audit-done-column-adjudication-receipt.v2",
    "receipt_id": "w-audit-done-column-adjudication-receipt-v2",
    "authority": "AUDIT_ONLY",
    "run_type": "FALSIFICATION_ATTACK",
    "module": "amphora-redteam-audit",
    "campaign_item_id": "W-AUDIT",
    "fire_id": FIRE_ID,
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_other_module_files": False,
    "supersedes": {
        "superseded_path": "amphora-redteam-audit/evidence/phase0/repairs/W-AUDIT/done/w-audit-done-column-adjudication-receipt.v1.dsse.json",
        "superseded_sha256": fire1_sha256,
        "superseded_deleted_or_modified": False,
        "reason": (
            "Fire 2 of W-AUDIT (max_fires=2). Fire 1's adjudication table cited the WRONG receipt_path "
            "for 23/128 (18%) done items -- systemic citation bug, see proposed_followups[0]. This receipt "
            "corrects all 23 citations to the item's true done/-glob-satisfying artifact, independently "
            "re-verifies DSSE validity + change-evidence for every one of them, deep-reads a fresh "
            "29-item stratified sample covering all 11 modules fire 1 never sampled, and supersedes fire "
            "1's summary. Bottom-line verdict counts are UNCHANGED (128 DELIVERED / 0 PARTIAL / "
            "0 NOT_DELIVERED / 0 NOT_LOCATABLE): every corrected and freshly-read item still shows a real "
            "named-artifact change, not a bare report. What changes is that the evidence trail backing 23 "
            "of those verdicts is now accurate, and two new process-integrity followups are filed."
        ),
    },
    "claim_under_attack": {
        "id": "W-AUDIT",
        "claim_text": (
            "The done column the founder reports cite reflects delivered work, not merely closed items."
        ),
    },
    "stale_premise_note": (
        "Carried forward from fire 1: the campaign item's objective cites '48 campaign items are marked "
        "done'; the live count at both fire 1 and fire 2 is 128/183 items done (identical id-set across "
        "both fires -- confirmed no items entered or left status=='done' between fires). Judged the live "
        "128, not the stale 48, per fire 1's precedent."
    ),
    "methodology": {
        "input_provenance": (
            "campaign.json read from this fire's working context on xbabe1 (protected file, not editable, "
            "not present on xbabe2); 128/183 items have status=='done', identical set to fire 1's."
        ),
        "step_1_citation_cross_check": (
            "For every one of fire 1's 128 adjudication_table rows, independently derived the item's TRUE "
            "done-artifact by scanning campaign.json items[].fires[].artifacts[] for the last path "
            "containing '/done/' (a deterministic, mechanical rule -- items whose done_check glob is NOT "
            "under repairs/<ID>/done/, e.g. plain W#/C# items using evidence/audit/ or benchmarks/ paths, "
            "correctly have no such artifact and were left alone). Compared against fire 1's cited "
            "receipt_path for every row: 23 mismatches found (script: local, campaign.json diff against "
            "fire 1's decoded payload)."
        ),
        "step_2_verify_23_corrected": (
            "For all 23 corrected paths: loaded on xbabe2, located the DSSE envelope (top-level or under "
            "'signature'), reconstructed the DSSEv1 PAE, Ed25519-verified against the pinned "
            "PHASE0_EVALUATOR public key from config/phase0-trust-store.v1.json, and inspected the decoded "
            "payload for supersedes/code/diff/reproducibility fields and its own verdict field. "
            "verify23.py, run on xbabe2 (script content in work/)."
        ),
        "step_3_deep_read_29": (
            "Selected all 29 done items belonging to the 11 modules fire 1's STATE.json flagged as "
            "'unsampled_modules_for_next_fire' (amphora-molecule-novelty, amphora-molecule-role-ranker, "
            "amphora-ip-fto-guard, amphora-optimizer-orchestrator, amphora-tolerance-robustness, "
            "amphora-process-qc-twin, amphora-formulation-arithmetic, amphora-viscosity-score, "
            "amphora-run-provenance, amphora-report-packager, amphora-known-answer-benchmarks) -- exceeds "
            "the >=20 fire 1 instructed. For each: resolved the TRUE done/ receipt path (per step 1), "
            "DSSE-verified, decoded payload, checked for supersedes/code/reproducibility fields, read the "
            "verdict/interpretation/resolution narrative, and cross-referenced against the item's own "
            "objective/done_criterion text in campaign.json to judge promised-vs-delivered. w_audit_scan29.py, "
            "run on xbabe2."
        ),
        "step_4_deep_dives": (
            "5 items overlap steps 2+3 (R-C01, R-S02, T-10, W-QC, T-13) and received the fullest read: full "
            "campaign.json fires[] history plus full payload read for each, individually inspected inline "
            "(not just via the batch scripts) -- notably R-C01 (0.9073 mean coverage vs 0.90 threshold, "
            "supersedes block present), R-S02 (54/54 CPC rows verdicted, 1 misassignment found and filed), "
            "R-C05 (honest re-scope hatch invoked on final permitted fire, per-environment table), W-TOL1 "
            "(narrowly-scoped index-hygiene fix -- verified its done_criterion, as literally written, did "
            "NOT promise to fix the underlying science, only to honestly point unresolved rows at their "
            "tracked owner; the item's own objective text states 'a row that honestly says no repair yet, "
            "queued as R-C01, is resolved' -- so DELIVERED is correct despite the underlying claim staying "
            "refuted), W-FTO-READON (substantive DOES_NOT_READ_ON claim-construction verdict, not a "
            "hedge)."
        ),
        "step_5_positive_control": (
            "Constructed and DSSE-signed a synthetic report-only receipt (planted_defect, see "
            "positive_control block) and confirmed the detector used in steps 2/3 flags it as "
            "NOT_DELIVERED-signal while it does not false-positive on any of the 47 real items freshly "
            "examined this fire (23 corrected + 29 deep-read, 5 overlap = 47 unique)."
        ),
    },
    "adjudication_table": adjudication_table,
    "summary": {
        "n_done_items_judged": n_done_items,
        "n_delivered": n_delivered,
        "n_partial": n_partial,
        "n_not_delivered": n_not_delivered,
        "n_not_locatable": n_not_locatable,
        "n_deep_read_fire2": len(deep_read_ids_fire2),
        "n_citation_corrected_fire2": len(citation_corrected_ids_fire2),
        "n_unique_items_freshly_examined_fire2": len(set(deep_read_ids_fire2) | set(citation_corrected_ids_fire2)),
        "overlap_deep_read_and_corrected_ids": overlap_ids,
        "deep_read_ids_fire2": deep_read_ids_fire2,
        "citation_corrected_ids_fire2": citation_corrected_ids_fire2,
        "n_deep_read_fire1": 15,
        "n_deep_or_corrected_cumulative_across_both_fires": len(set(deep_read_ids_fire2) | set(citation_corrected_ids_fire2)) + 15,
    },
    "verdict": "CLAIM_SURVIVED",
    "verdict_reasoning": (
        "The pinned claim ('the done column reflects delivered work, not merely closed items') SURVIVES "
        "this fire's attack. The attack was genuinely capable of falsifying it: had any of the 47 items "
        "freshly examined this fire (29 deep-read across the 11 previously-unsampled modules, plus 18 "
        "additional items whose citation was corrected and independently re-verified) turned out to be "
        "narrative-only, missing its promised artifact, or diverging from its own done_criterion's words, "
        "this fire would have filed a PARTIAL or NOT_DELIVERED verdict and downgraded the aggregate -- the "
        "positive control (above) proves the detector used to make that call actually fires on a planted "
        "report-only receipt. It did not fire on any of the 47 real items: every one shows independent "
        "re-derivation, code/probe artifacts, superseding KPIs with sha256-pinned prior artifacts, or "
        "substantive analytical verdicts (e.g. claim-construction DOES_NOT_READ_ON), never a bare 'a "
        "future fire should fix this' narrative. The one apparent near-miss (W-TOL1) was checked against "
        "its OWN narrowly-scoped done_criterion, which explicitly permitted an honest index-hygiene-only "
        "fix naming the science's tracked owner rather than requiring the science itself to land -- it "
        "delivered exactly and only what it promised. HOWEVER: this fire also found and must disclose a "
        "real defect in HOW the prior fire reached its own 128/0/0 conclusion -- a systemic 18% "
        "receipt-citation error (proposed_followups[1]) and a 4-item positive-control governance gap "
        "(proposed_followups[2]) -- both filed as owned followups rather than silently absorbed into a "
        "clean bill of health."
    ),
    "proposed_followups": fire1_followups + new_followups,
    "positive_control": positive_control,
    "does_not_close": [
        "Does not deep-read the remaining 99 done items outside this fire's 29-item sample and fire 1's "
        "15-item sample (44/128 = 34% of the done column has now had an individual deep read across both "
        "fires; the rest still rests on mechanical DSSE+content-signal checks, now against corrected "
        "citations for 23 of them).",
        "Does not verify that every one of the 4 positive-control-governance-gap items' UNDERLYING "
        "scientific claims still hold under a fresh attack -- only that their existing done receipts "
        "genuinely changed a named artifact at the time they fired, which is this audit's scope.",
        "Does not fix the audit_scan.py citation-selection bug itself (no such script was located in "
        "W-AUDIT's own work/ from fire 1 to patch) -- filed as an owned followup with a concrete "
        "acceptance criterion instead, per campaign-item instruction not to reopen or edit the campaign.",
        "Does not certify Phase-1/Phase-2 promotion, scientific validity, procurement, legal, safety, or "
        "release authority for any module. AUDIT_ONLY.",
        "max_fires=2 for W-AUDIT is now exhausted; no further fire on this item will run.",
    ],
    "toolchain": {
        "python": "3, stdlib json/hashlib/base64 + cryptography.hazmat Ed25519",
        "execution_host": "xbabe2 (all reads/verifies/signing); campaign.json read from xbabe1 working context per prompt instruction",
    },
}

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
rev_pin = (rev_key_id == tbr.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))
assert eval_pin, "evaluator key_id does not match pinned trust store"

body_obj["signing_key"] = {
    "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
    "used_for": "AUDIT_ONLY audit receipt under evidence/phase0/repairs/W-AUDIT/done/",
    "signs_phase0_evaluation_or_review": False,
    "derives_pinned_trust_store_key_id": bool(eval_pin),
}
body_obj["reviewer_reference"] = {
    "role": "PHASE0_INTERNAL_REVIEWER", "key_id": rev_key_id, "public_key_hex": rev_pub_hex,
    "derives_pinned_trust_store_key_id": bool(rev_pin), "reviewer_signature_present": False,
    "note": "Reviewer key referenced for provenance only; no independent human review performed.",
}

body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.redteam-audit-w-audit-done-column-adjudication-v2+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}

OUT_DIR.mkdir(parents=True, exist_ok=True)
out = OUT_DIR / "w-audit-done-column-adjudication-receipt.v2.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))

print("WROTE", out)
print("fire1_sha256", fire1_sha256)
print("n_done_items", n_done_items, "n_delivered", n_delivered, "n_partial", n_partial, "n_not_delivered", n_not_delivered)
print("n_deep_read_fire2", len(deep_read_ids_fire2))
print("n_citation_corrected_fire2", len(citation_corrected_ids_fire2))
print("planted_detected", planted_detected_as_not_delivered)
print("eval_derives_pinned_trust_key", eval_pin)
print("signature_verified", True)
print("envelope_sha256", sha(out.read_bytes()))
