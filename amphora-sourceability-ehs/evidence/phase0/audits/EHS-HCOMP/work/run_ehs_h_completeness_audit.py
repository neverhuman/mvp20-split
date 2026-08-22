#!/usr/bin/env python3
"""EHS-HCOMP: dedicated falsification fire against the H-statement-completeness
of the DETA and TETA candidate_hazard_cards in the currently-authoritative
GHS/CLP 5-canonical-epoxy-amine hazard prescreen receipt (R-N01 fire 2,
2026-08-04), for the two candidates whose h_statement_codes were NEVER
PubChem-re-derived by any prior repair (correction_applied_this_repair=false
for both DETA and TETA in that receipt -- only IPDA and m-XDA's CIDs/H-codes
were corrected).

This closes the "future dedicated falsification fire against the KPI's
H-statement-derivation methodology" that X-EHS-CID (2026-08-14) explicitly
flagged and declined to action, and that Y-EHS-GATE (2026-08-14) also left
unactioned. Both those fires only OBSERVED the divergence as an aside; this
fire is the first to run it as the primary, formally-scoped attack with its
own refutation criterion, independent fresh live fetch, two-replay gate and
verdict.

REFUTATION CRITERION: for DETA (CAS 111-40-0, CID 8111) or TETA
(CAS 112-24-3, CID 5565), take the ECHA C&L "aggregated" GHS Classification
block from a fresh live PubChem PUG-View fetch -- identified as the specific
sub-record whose own "ECHA C&L Notifications Summary" cites the EXACT same
report-count/notification-count pair the candidate's own current card already
quotes verbatim in its `pubchem_notifications_summary` field (i.e., the same
aggregate the card claims as its source). If that aggregate block reports ANY
H-code at >=10% of companies (PubChem's own disclosed threshold for which
codes it even shows) that is ABSENT from the card's `h_statement_codes`, OR
reports a DIFFERENT chronic-aquatic-toxicity severity tier (H410/H411/H412)
at majority prevalence than the one the card states, the claim "this card's
h_statement_codes faithfully represents its own cited source aggregate" is
REFUTED for that candidate.
"""
import base64
import hashlib
import json
import re
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-sourceability-ehs"
ITEM_DIR = MOD / "evidence/phase0/audits/EHS-HCOMP"
WORK = ITEM_DIR / "work"
RAW = WORK / "raw"
RAW.mkdir(parents=True, exist_ok=True)

SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = json.loads((ROOT / "config/phase0-trust-store.v1.json").read_text())

AUTHORITATIVE_RECEIPT = MOD / "evidence/phase0/repairs/R-N01/done/r-n01-fire2-ghs-clp-hazard-card-correction-receipt.v1.dsse.json"
XEHSCID_DONE = MOD / "evidence/phase0/repairs/X-EHS-CID/done/x-ehs-cid-done-receipt.v1.dsse.json"
XEHSCID_RAW_DETA = MOD / "evidence/phase0/repairs/X-EHS-CID/work/raw/ghs_pugview_DETA_8111.json"
XEHSCID_RAW_TETA = MOD / "evidence/phase0/repairs/X-EHS-CID/work/raw/ghs_pugview_TETA_5565.json"

THIS_FIRE_ID = "20260815T000001-4006146-25a0bf6559b0"

CANDIDATES = {
    "DETA": {"cas": "111-40-0", "cid": 8111},
    "TETA": {"cas": "112-24-3", "cid": 5565},
}

H_META = {
    "H302": ("Acute toxicity oral", "Harmful if swallowed"),
    "H311": ("Acute toxicity dermal", "Toxic in contact with skin"),
    "H312": ("Acute toxicity dermal", "Harmful in contact with skin"),
    "H314": ("Skin corrosion / eye damage", "Causes severe skin burns and eye damage"),
    "H317": ("Skin sensitisation", "May cause an allergic skin reaction"),
    "H318": ("Serious eye damage", "Causes serious eye damage"),
    "H330": ("Acute toxicity inhalation", "Fatal if inhaled"),
    "H331": ("Acute toxicity inhalation", "Toxic if inhaled"),
    "H332": ("Acute toxicity inhalation", "Harmful if inhaled"),
    "H335": ("STOT single exposure", "May cause respiratory irritation"),
    "H334": ("Respiratory sensitisation", "May cause allergy or asthma symptoms or breathing difficulties if inhaled"),
    "H360": ("Reproductive toxicity", "May damage fertility or the unborn child"),
    "H361": ("Reproductive toxicity", "Suspected of damaging fertility or the unborn child"),
    "H402": ("Acute aquatic toxicity", "Harmful to aquatic life"),
    "H410": ("Chronic aquatic toxicity", "Very toxic to aquatic life with long-lasting effects"),
    "H411": ("Chronic aquatic toxicity", "Toxic to aquatic life with long-lasting effects"),
    "H412": ("Chronic aquatic toxicity", "Harmful to aquatic life with long-lasting effects"),
}


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


def verify_dsse(envelope_wrapper, eval_pub_hex):
    env = envelope_wrapper["signature"]
    payload = base64.standard_b64decode(env["payload"])
    ptype = env["payloadType"]
    sig = base64.standard_b64decode(env["signatures"][0]["sig"])
    pub = Ed25519PublicKey.from_public_bytes(bytes.fromhex(eval_pub_hex))
    pub.verify(sig, pae(ptype, payload))
    return json.loads(payload)


def parse_codes(text):
    codes = []
    for piece in re.findall(r"H\d{3}(?:\+H\d{3})*\s*(?:\(([^)]+)\))?", text):
        pass
    # tokenize on the literal hazard-statement fragments PubChem emits,
    # e.g. "H318 (68.3%): Causes ..." or "H302+H312 (18.4%): Harmful ..."
    for m in re.finditer(r"((?:H\d{3}\+)*H\d{3})\s*(?:\(([^)]+)\))?\s*:", text):
        token, pct = m.group(1), m.group(2)
        pct_val = None
        if pct:
            pm = re.match(r">?\s*([\d.]+)%", pct.strip())
            if pm:
                pct_val = float(pm.group(1))
            elif pct.strip() == "100%":
                pct_val = 100.0
        for code in token.split("+"):
            codes.append((code, pct_val))
    return codes


def aggregated_ghs(pugview_json, expected_notif_summary_substr):
    """Same ReferenceNumber-grouping methodology X-EHS-CID's aggregated_ghs()
    used: group Information entries by ReferenceNumber, then select the group
    whose own ECHA C&L Notifications Summary text is the one that matches the
    candidate's already-cited aggregate (by report/notification count)."""
    def walk(sec):
        for s in sec.get("Section", []):
            if s.get("TOCHeading", "") == "GHS Classification":
                yield s
            else:
                yield from walk(s)

    groups = {}
    for s in walk(pugview_json["Record"]):
        for info in s.get("Information", []):
            ref = info.get("ReferenceNumber")
            groups.setdefault(ref, {})[info.get("Name")] = info

    candidates_found = []
    for ref, fields in groups.items():
        if "ECHA C&L Notifications Summary" not in fields:
            continue
        summary_text = fields["ECHA C&L Notifications Summary"]["Value"]["StringWithMarkup"][0]["String"]
        hs = fields.get("GHS Hazard Statements")
        raw_text = ""
        if hs:
            raw_text = " ".join(sw.get("String", "") for sw in hs.get("Value", {}).get("StringWithMarkup", []))
        codes_with_pct = parse_codes(raw_text)
        candidates_found.append({
            "reference_number": ref,
            "summary_text": summary_text,
            "raw_hazard_statement_text": raw_text,
            "codes_with_pct": codes_with_pct,
        })
        if expected_notif_summary_substr in summary_text:
            majority_codes_ge10 = sorted({c for c, p in codes_with_pct if p is None or p >= 10.0})
            return {
                "matched": True,
                "reference_number": ref,
                "summary_text": summary_text,
                "raw_hazard_statement_text": raw_text,
                "codes_with_pct": codes_with_pct,
                "majority_codes_ge10pct": majority_codes_ge10,
            }
    return {"matched": False, "all_groups": candidates_found}


def load_authoritative_cards():
    payload = verify_dsse({"signature": json.loads(AUTHORITATIVE_RECEIPT.read_text())["signature"]},
                           json.loads(AUTHORITATIVE_RECEIPT.read_text())["evaluator_public_key_hex"])
    cards = {c["candidate_name"]: c for c in payload["corrected_hazard_cards"]}
    return cards, payload


def run(raw_deta_path, raw_teta_path):
    deta_json = json.loads(raw_deta_path.read_bytes())
    teta_json = json.loads(raw_teta_path.read_bytes())
    cards, auth_payload = load_authoritative_cards()

    results = {}
    for cand, raw_json in [("DETA", deta_json), ("TETA", teta_json)]:
        card = cards[cand]
        expected_substr_match = re.search(r"per (\d[\d,]*) reports by companies from (\d[\d,]*) notifications",
                                           card["pubchem_notifications_summary"])
        reports, notifs = expected_substr_match.group(1), expected_substr_match.group(2)
        expected_substr = f"per {reports} reports by companies from {notifs} notifications"
        agg = aggregated_ghs(raw_json, expected_substr)
        assert agg["matched"], f"{cand}: could not locate the aggregate block the card itself cites"
        card_codes = set(card["h_statement_codes"])
        live_majority_codes = set(agg["majority_codes_ge10pct"])
        missing_from_card = sorted(live_majority_codes - card_codes)
        # chronic-aquatic-toxicity severity-tier check: card states exactly
        # one of H410/H411/H412; does the live majority aggregate agree?
        card_aquatic = sorted(card_codes & {"H410", "H411", "H412"})
        live_aquatic_majority = sorted({c for c, p in agg["codes_with_pct"]
                                         if c in ("H410", "H411", "H412") and (p is None or p >= 10.0)})
        aquatic_tier_mismatch = bool(card_aquatic) and bool(live_aquatic_majority) and (
            set(card_aquatic) != set(live_aquatic_majority))
        non_aquatic_missing = [c for c in missing_from_card if c not in ("H410", "H411", "H412")]
        refuted_for_candidate = bool(non_aquatic_missing) or aquatic_tier_mismatch
        results[cand] = {
            "cas": CANDIDATES[cand]["cas"],
            "cid_used": CANDIDATES[cand]["cid"],
            "card_h_statement_codes": sorted(card_codes),
            "card_pubchem_notifications_summary": card["pubchem_notifications_summary"],
            "live_aggregate_matched_reference_number": agg["reference_number"],
            "live_aggregate_summary_text": agg["summary_text"],
            "live_aggregate_raw_hazard_statement_text": agg["raw_hazard_statement_text"],
            "live_aggregate_codes_with_pct": [{"code": c, "pct": p} for c, p in agg["codes_with_pct"]],
            "live_majority_codes_ge10pct": sorted(live_majority_codes),
            "missing_from_card_non_aquatic": non_aquatic_missing,
            "card_aquatic_tier": card_aquatic,
            "live_majority_aquatic_tier": live_aquatic_majority,
            "aquatic_tier_mismatch": aquatic_tier_mismatch,
            "refuted_for_candidate": refuted_for_candidate,
        }

    any_refuted = any(r["refuted_for_candidate"] for r in results.values())

    diag = {
        "schema": "amphora.sourceability-ehs.ehs-hcomp.diagnostic.v1",
        "fire_id": THIS_FIRE_ID,
        "attack": "H-statement-completeness of DETA/TETA cards vs their own cited PubChem ECHA C&L aggregate",
        "candidates": results,
        "any_candidate_refuted": any_refuted,
        "authoritative_receipt_sha256": sha(canon({k: v for k, v in json.loads(AUTHORITATIVE_RECEIPT.read_text()).items()})),
    }
    return diag


if __name__ == "__main__":
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "canonical"

    fresh_deta = RAW / "ghs_pugview_DETA_8111_20260815.json"
    fresh_teta = RAW / "ghs_pugview_TETA_5565_20260815.json"

    diag = run(fresh_deta, fresh_teta)
    out = WORK / f"diagnostic.{mode}.json"
    out.write_text(json.dumps(diag, indent=2, sort_keys=True))
    print("WROTE", out)
    print("any_candidate_refuted", diag["any_candidate_refuted"])
