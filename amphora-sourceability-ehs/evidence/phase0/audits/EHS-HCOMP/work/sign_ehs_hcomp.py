#!/usr/bin/env python3
"""Signs the EHS-HCOMP done receipt: dedicated falsification fire against the
H-statement completeness of the DETA/TETA hazard cards in the currently
authoritative GHS/CLP 5-canonical-epoxy-amine receipt (R-N01 fire 2). Closes
the "future dedicated falsification fire" that X-EHS-CID (2026-08-14) and
Y-EHS-GATE (2026-08-14) both flagged as an unactioned out-of-scope aside.
AUDIT_ONLY. Does not modify any existing receipt/KPI, does not touch
mission.md front-matter, does not modify the manifest, does not change any
procurement_gate_outcome (disclosure only, same conservative-default posture
established by W-EHS1).
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-sourceability-ehs"
ITEM_DIR = MOD / "evidence/phase0/audits/EHS-HCOMP"
WORK = ITEM_DIR / "work"

SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = json.loads((ROOT / "config/phase0-trust-store.v1.json").read_text())

OUT_PATH = MOD / "reference/mvp20/data/deta_teta_h_statement_completeness_audit_receipt.v1.json"

THIS_FIRE_ID = "20260815T000001-4006146-25a0bf6559b0"

GATE_RULE = ("if H350/H340/H360 present -> SVHC_REVIEW_REQUIRED; "
             "elif H334 present -> RESPIRATORY_SENSITISER_CONTAINMENT_REQUIRED; "
             "elif H351 present -> CARCINOGEN_CAT_2_MONITORING_REQUIRED; "
             "elif H314 present -> CORROSIVE_PPE_PLAN_REQUIRED; else STANDARD_PROCUREMENT. "
             "(No branch keyed on H330/H331/H332/H335 acute-inhalation-toxicity codes at all -- "
             "the structural blind spot Y-EHS-GATE, 2026-08-14, already proved by ablation on m-XDA.)")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def canon(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()


def pae(t: str, body: bytes) -> bytes:
    return b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " + str(len(body)).encode() + b" " + body


def load_seed(p: Path) -> bytes:
    b = p.read_bytes().strip()
    if len(b) == 64:
        try:
            return bytes.fromhex(b.decode())
        except Exception:
            pass
    return b[:32]


eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
tbr = {k.get("role"): k for k in TRUST["keys"]}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
assert eval_pin, "evaluator key_id does not derive pinned trust store entry"

diag_a_bytes = (WORK / "diagnostic.canonical.json").read_bytes()
diag_b_bytes = (WORK / "diagnostic.runB.json").read_bytes()
diag_a = json.loads(diag_a_bytes)
two_replay_byte_identical = sha(diag_a_bytes) == sha(diag_b_bytes)
assert two_replay_byte_identical, "two-replay byte-stability gate FAILED"
assert diag_a["any_candidate_refuted"] is True

authoritative_receipt_bytes = (MOD / "evidence/phase0/repairs/R-N01/done/r-n01-fire2-ghs-clp-hazard-card-correction-receipt.v1.dsse.json").read_bytes()

body_obj = {
    "schema": "amphora.sourceability-ehs.audit.ehs-hcomp.v1",
    "audit_item_id": "EHS-HCOMP",
    "module": "amphora-sourceability-ehs",
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "EVIDENCE_ONLY",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "modifies_manifest": False,
    "modifies_existing_receipts_or_kpis": False,
    "modifies_procurement_gate_outcome": False,
    "fire_id": THIS_FIRE_ID,
    "date": "2026-08-15",
    "claim_under_attack": {
        "receipt_path": "amphora-sourceability-ehs/evidence/phase0/repairs/R-N01/done/r-n01-fire2-ghs-clp-hazard-card-correction-receipt.v1.dsse.json",
        "receipt_sha256": sha(authoritative_receipt_bytes),
        "field": "corrected_hazard_cards[DETA, TETA].h_statement_codes",
        "claim_text": (
            "DETA and TETA's h_statement_codes (unchanged since the original 2026-07-23 hand-compiled "
            "card; correction_applied_this_repair=false for both in R-N01 fire 2, because their PubChem "
            "CID citations were already correct so no CID-attribution correction applied) faithfully "
            "represent the ECHA C&L aggregate GHS classification each card's own `pubchem_notifications_summary` "
            "field already cites by report/notification count as its source."
        ),
        "why_this_is_the_strongest_standing_untested_claim": (
            "X-EHS-CID (2026-08-14) and Y-EHS-GATE (2026-08-14) both independently observed that DETA's "
            "live PubChem aggregate diverges from its card and explicitly flagged 'a future dedicated "
            "falsification fire against the KPI's H-statement-derivation methodology' as necessary -- "
            "neither fire ran that dedicated attack; both treated it as an out-of-scope aside. This fire "
            "is that dedicated attack, extended in scope to TETA (not previously checked) and formalized "
            "with its own refutation criterion, fresh independent fetch, negative control and verdict."
        ),
    },
    "refutation_criterion": (
        "For DETA (CAS 111-40-0, CID 8111) or TETA (CAS 112-24-3, CID 5565): identify, in a fresh live "
        "PubChem PUG-View GHS-Classification fetch, the specific ReferenceNumber-grouped sub-record whose "
        "own 'ECHA C&L Notifications Summary' text cites the EXACT same report-count/notification-count "
        "pair the candidate's current card already quotes verbatim in its own pubchem_notifications_summary "
        "field (i.e. the card's own self-declared source aggregate, not a different sub-population). If that "
        "matched aggregate reports ANY H-code at >=10% of companies (PubChem's own disclosed threshold for "
        "which codes it shows at all) that is absent from the card's h_statement_codes, OR reports a "
        "DIFFERENT chronic-aquatic-toxicity severity tier (H410 vs H411 vs H412) at >=10% prevalence than "
        "the tier the card states, the completeness claim is REFUTED for that candidate."
    ),
    "method": {
        "fresh_fetch": "Live PubChem PUG-View GHS Classification fetch for CID 8111 (DETA) and CID 5565 "
                        "(TETA), performed this fire (2026-08-15), a new HTTP round-trip distinct from "
                        "R-N01 fire 2's 2026-08-04 fetch and X-EHS-CID's 2026-08-14 fetch.",
        "extraction": "ReferenceNumber-grouped aggregate identification (same methodology X-EHS-CID's "
                       "aggregated_ghs() used), matched to the card's own cited report/notification count "
                       "to select the correct sub-record rather than any individual company classification.",
        "cross_fire_corroboration": "The same extraction re-run against X-EHS-CID's independently-fetched "
                                     "2026-08-14 raw PUG-View JSON for the same two CIDs (already committed "
                                     "in this repo at evidence/phase0/repairs/X-EHS-CID/work/raw/) reproduces "
                                     "an IDENTICAL majority-code set to this fire's fresh 2026-08-15 fetch -- "
                                     "two independent HTTP round-trips a day apart agree exactly.",
        "negative_control": (
            "The identical audit was run against IPDA (CID 17857) and m-XDA (CID 15133) -- the two "
            "candidates R-N01 fire 2 DID PubChem-re-derive (correction_applied_this_repair=true) -- using "
            "X-EHS-CID's already-committed raw fetches for those CIDs. Result: zero missing codes for both "
            "(IPDA live majority == card exactly; m-XDA live majority == card exactly, including its H330/"
            "H331/H332 codes already added by R-N01 fire 2). This shows the audit methodology does not "
            "spuriously flag a genuinely complete card -- it flags DETA/TETA specifically and only because "
            "those two cards were never actually re-derived from PubChem, unlike the other three."
        ),
        "two_replay_byte_stability": {
            "diagnostic_canonical_sha256": sha(diag_a_bytes),
            "diagnostic_runB_sha256": sha(diag_b_bytes),
            "byte_identical": two_replay_byte_identical,
        },
    },
    "findings": {
        "DETA": {
            "cas": "111-40-0",
            "cid": 8111,
            "card_h_statement_codes": diag_a["candidates"]["DETA"]["card_h_statement_codes"],
            "live_aggregate_matched_reference_number": diag_a["candidates"]["DETA"]["live_aggregate_matched_reference_number"],
            "live_majority_codes_ge10pct": diag_a["candidates"]["DETA"]["live_majority_codes_ge10pct"],
            "missing_from_card": diag_a["candidates"]["DETA"]["missing_from_card_non_aquatic"],
            "missing_from_card_detail": [
                {"code": "H318", "pct": "68.3%", "hazard_class": "Serious eye damage", "text": "Causes serious eye damage"},
                {"code": "H330", "pct": "71.7%", "hazard_class": "Acute toxicity inhalation", "text": "Fatal if inhaled"},
                {"code": "H335", "pct": "70.7%", "hazard_class": "STOT single exposure", "text": "May cause respiratory irritation"},
            ],
            "aquatic_tier_mismatch": diag_a["candidates"]["DETA"]["aquatic_tier_mismatch"],
            "refuted": diag_a["candidates"]["DETA"]["refuted_for_candidate"],
            "gate_impact_if_h_codes_corrected": (
                "None. gate_for(current H302/H312/H314/H317/H411) == gate_for(+ H318/H330/H335) == "
                "CORROSIVE_PPE_PLAN_REQUIRED in both cases, because gate_rule's H314 branch already fires "
                "and there is no branch for H318/H330/H335 to reach. This is the same structural blind spot "
                "Y-EHS-GATE proved on m-XDA (2026-08-14), now shown to also mask a card-completeness defect "
                "on a SECOND candidate that additionally carries H330 'Fatal if inhaled' at 71.7% prevalence "
                "in its own already-cited source aggregate."
            ),
        },
        "TETA": {
            "cas": "112-24-3",
            "cid": 5565,
            "card_h_statement_codes": diag_a["candidates"]["TETA"]["card_h_statement_codes"],
            "live_aggregate_matched_reference_number": diag_a["candidates"]["TETA"]["live_aggregate_matched_reference_number"],
            "live_majority_codes_ge10pct": diag_a["candidates"]["TETA"]["live_majority_codes_ge10pct"],
            "missing_from_card": diag_a["candidates"]["TETA"]["missing_from_card_non_aquatic"],
            "missing_from_card_detail": [
                {"code": "H318", "pct": "39.4%", "hazard_class": "Serious eye damage", "text": "Causes serious eye damage"},
            ],
            "aquatic_tier_mismatch": diag_a["candidates"]["TETA"]["aquatic_tier_mismatch"],
            "card_aquatic_tier": diag_a["candidates"]["TETA"]["card_aquatic_tier"],
            "live_majority_aquatic_tier": diag_a["candidates"]["TETA"]["live_majority_aquatic_tier"],
            "aquatic_tier_finding": (
                "Card states H411 ('Toxic to aquatic life with long-lasting effects'). The exact same "
                "aggregate the card cites by report/notification count (2507 reports / 30 notifications) "
                "reports H412 ('Harmful to aquatic life with long-lasting effects', a LOWER severity tier) "
                "at 99.5% prevalence -- not H411. The card's H411 traces to a separate 1-notification "
                "minority environmental sub-block, not the majority aggregate it purports to summarize. "
                "This is a severity-direction-ambiguous discrepancy (the majority tier is actually LESS "
                "severe than what the card states), not obviously a safety-relevant undercount -- flagged "
                "as a distinct finding from the H318 omission, not conflated with it."
            ),
            "refuted": diag_a["candidates"]["TETA"]["refuted_for_candidate"],
            "gate_impact_if_h_codes_corrected": (
                "None. TETA carries H314 either way; gate_rule's H314 branch fires regardless of the H318 "
                "addition or H411-vs-H412 correction. procurement_gate_outcome unchanged either way: "
                "CORROSIVE_PPE_PLAN_REQUIRED."
            ),
        },
    },
    "negative_control_ipda_mxda": {
        "IPDA": {"card_codes": ["H302", "H312", "H314", "H317", "H318", "H412"],
                 "live_majority_codes": ["H302", "H312", "H314", "H317", "H318", "H412"],
                 "missing_from_card": []},
        "m-XDA": {"card_codes": ["H302", "H312", "H314", "H317", "H318", "H330", "H331", "H332", "H412"],
                  "live_majority_codes": ["H302", "H312", "H314", "H317", "H318", "H330", "H331", "H332", "H412"],
                  "missing_from_card": []},
        "interpretation": "Zero false positives on the two cards R-N01 fire 2 actually re-derived from "
                           "PubChem -- corroborates that the DETA/TETA findings are real card-completeness "
                           "defects, not an artifact of the extraction methodology.",
    },
    "gate_rule": GATE_RULE,
    "verdict": "CLAIM_REFUTED",
    "verdict_summary": (
        "REFUTED. DETA's card omits H318 (68.3%), H330 'Fatal if inhaled' (71.7%), and H335 (70.7%) -- all "
        "majority-prevalence codes in the exact ECHA C&L aggregate the card cites as its own source; TETA's "
        "card omits H318 (39.4%) from the same self-cited aggregate and states a chronic-aquatic-toxicity "
        "tier (H411) that the majority aggregate does not support (majority reports H412, 99.5%). Both "
        "findings reproduce identically across two independent live fetches (2026-08-14 and 2026-08-15) and "
        "do not reproduce on the two candidates whose cards WERE PubChem-re-derived (negative control). No "
        "procurement_gate_outcome changes as a result -- gate_rule's blind spot (already proved by "
        "Y-EHS-GATE) makes the H318/H330/H335 additions gate-invisible while H314 remains present."
    ),
    "does_not_close": [
        "Does not modify DETA/TETA's h_statement_codes, procurement_gate_outcome, or any existing signed "
        "receipt/KPI -- disclosure only, per the conservative-default posture established by W-EHS1 "
        "(2026-08-05): a safety-relevant hazard-card correction is a human-reviewable change, not an "
        "unreviewed mechanical patch.",
        "Does not patch gate_rule's H330/H331/H332/H335 acute-inhalation/STOT blind spot -- that defect was "
        "already proved by Y-EHS-GATE (2026-08-14) and remains open for a dedicated repair fire (distinct "
        "from this fire's card-completeness finding).",
        "Does not extend to DDS -- DDS's only prior open question (H351/IARC grounding) was already closed "
        "by W-EHS1; a full DDS H-statement-completeness re-audit against this fire's methodology is left for "
        "a future fire if warranted.",
        "AUDIT_ONLY: no GHS/CLP compliance, toxicological, procurement, or regulatory-closure authority.",
    ],
    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "derives_pinned_trust_store_key_id": bool(eval_pin),
    },
}

body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.sourceability-ehs-audit-ehs-hcomp+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {
    "payload": base64.standard_b64encode(body).decode(),
    "payloadType": ptype,
    "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}],
}
receipt = {
    "evaluator_key_id": eval_key_id,
    "evaluator_public_key_hex": eval_pub_hex,
    "signature": envelope,
}

OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
OUT_PATH.write_text(json.dumps(receipt, indent=2, sort_keys=True))

Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])),
)
print("WROTE", OUT_PATH)
print("self_verify_signature", True)
print("envelope_sha256", sha(OUT_PATH.read_bytes()))
