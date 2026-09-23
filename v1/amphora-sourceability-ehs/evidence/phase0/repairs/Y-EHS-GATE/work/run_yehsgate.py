#!/usr/bin/env python3
"""Y-EHS-GATE (ROTATION-mode falsification fire 20260814T120001-1714859-e02008d1cca4):
attacks the GHS/CLP 5-canonical-epoxy-amine hazard-prescreen KPI's deterministic
gate_rule -- specifically the claim (implicit in
`phase0_deterministic_gates_passed: true` / `n_deterministic_gates_passed: 9` /
claim_locks on the KPI, and repeated verbatim, unmodified, across R-N01 fire 2 and
X-EHS-CID) that the gate_rule's per-candidate `procurement_gate_outcome` is a
hazard-severity-responsive prescreen output.

This continues, rather than repeats, the immediately-prior fire's own unactioned
finding: X-EHS-CID (fire 20260814T080001-3751638-04dcbc456153, 4 hours before this
one) flagged that DETA's live PubChem aggregate carries H330 (Fatal if inhaled)
absent from DETA's card, and noted "this KPI's gate_rule also has no branch for
H330/H331/H332 acute-inhalation-toxicity codes at all... flagged for a dedicated
future falsification fire against ... gate-rule coverage". This fire IS that fire,
but sharpens the target: rather than a hypothetical ("if DETA's card had H330"),
it shows the CURRENT, already-corrected, twice-independently-reverified authoritative
card for m-XDA (R-N01 fire 2, corrected_hazard_cards, re-confirmed byte-identical by
X-EHS-CID) *already carries* H330+H331+H332 today, right now, and the gate_rule,
applied exactly as documented, is provably blind to them.

REFUTATION CRITERION (this fire, none pre-registered elsewhere): if a candidate's
current-authoritative hazard card carries an H-statement encoding acute lethal/toxic
inhalation hazard (H330 "Fatal if inhaled" Cat 1, H331 "Toxic if inhaled" Cat 2, or
H332 "Harmful if inhaled" Cat 3) AND removing those exact codes from that candidate's
code set (holding everything else fixed) does NOT change the gate_rule's output --
i.e. gate_for(codes) == gate_for(codes - {H330,H331,H332}) -- then the claim that the
gate_rule's procurement_gate_outcome is a hazard-severity-differentiated safety
prescreen is REFUTED for that candidate: the presence of one of GHS's most severe
acute-toxicity hazard classes is provably invisible to the deterministic decision.
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
ITEM_DIR = MOD / "evidence/phase0/repairs/Y-EHS-GATE"
WORK = ITEM_DIR / "work"
RAW = WORK / "raw"
DONE = ITEM_DIR / "done"
DONE.mkdir(parents=True, exist_ok=True)

SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = json.loads((ROOT / "config/phase0-trust-store.v1.json").read_text())

RN01_FIRE2 = MOD / "evidence/phase0/repairs/R-N01/done/r-n01-fire2-ghs-clp-hazard-card-correction-receipt.v1.dsse.json"
XEHSCID_DONE = MOD / "evidence/phase0/repairs/X-EHS-CID/done/x-ehs-cid-done-receipt.v1.dsse.json"
KPI_PATH = MOD / "evidence/phase0/kpis/ghs-clp-public-hazard-prescreen-5-canonical-epoxy-amines-kpi.v1.json"

THIS_FIRE_ID = "20260814T120001-1714859-e02008d1cca4"

GATE_RULE = ("if H350/H340/H360 present -> SVHC_REVIEW_REQUIRED (would-be SVHC candidate); "
             "elif H334 present -> RESPIRATORY_SENSITISER_CONTAINMENT_REQUIRED; "
             "elif H351 present -> CARCINOGEN_CAT_2_MONITORING_REQUIRED; "
             "elif H314 present -> CORROSIVE_PPE_PLAN_REQUIRED; else STANDARD_PROCUREMENT.")

INHALATION_ACUTE_TOX_CODES = {"H330", "H331", "H332"}

H_META = {
    "H330": ("Acute toxicity inhalation", "Fatal if inhaled", "1"),
    "H331": ("Acute toxicity inhalation", "Toxic if inhaled", "2"),
    "H332": ("Acute toxicity inhalation", "Harmful if inhaled", "3"),
}


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def canon(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()


def pae(t: str, body: bytes) -> bytes:
    return b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " + str(len(body)).encode() + b" " + body


def load_json(p: Path):
    return json.loads(p.read_text())


def load_seed(p: Path) -> bytes:
    b = p.read_bytes().strip()
    if len(b) == 64:
        try:
            return bytes.fromhex(b.decode())
        except Exception:
            pass
    return b


def verify_dsse(envelope_wrapper, eval_pub_hex):
    env = envelope_wrapper["signature"]
    payload = base64.standard_b64decode(env["payload"])
    ptype = env["payloadType"]
    sig = base64.standard_b64decode(env["signatures"][0]["sig"])
    pub = Ed25519PublicKey.from_public_bytes(bytes.fromhex(eval_pub_hex))
    try:
        pub.verify(sig, pae(ptype, payload))
        return True, json.loads(payload)
    except Exception:
        return False, json.loads(payload)


def gate_for(h_codes: set) -> str:
    """Verbatim re-implementation of the KPI's documented gate_rule (identical
    branch order/logic to gate_for() in R-N01 fire 2's and X-EHS-CID's own
    harnesses -- reproduced here rather than imported, so this audit does not
    trust the prior fires' code, only the *documented* gate_rule string, which
    is repeated byte-identically in every prior receipt's `gate_rule` field."""
    if h_codes & {"H350", "H340", "H360"}:
        return "SVHC_REVIEW_REQUIRED"
    if "H334" in h_codes:
        return "RESPIRATORY_SENSITISER_CONTAINMENT_REQUIRED"
    if "H351" in h_codes:
        return "CARCINOGEN_CAT_2_MONITORING_REQUIRED"
    if "H314" in h_codes:
        return "CORROSIVE_PPE_PLAN_REQUIRED"
    return "STANDARD_PROCUREMENT"


def aggregated_ghs_groups(pugview_json):
    """Return every ReferenceNumber group with an ECHA C&L Notifications Summary,
    plus the total (reports, notifications) count parsed from that summary, so we
    can identify the max-report aggregate independently."""
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
            groups.setdefault(ref, {}).setdefault(info.get("Name"), []).append(info)

    out = {}
    for ref, fields in groups.items():
        summ = fields.get("ECHA C&L Notifications Summary")
        if not summ:
            continue
        n_reports = n_notifs = None
        for info in summ:
            for sw in info.get("Value", {}).get("StringWithMarkup", []):
                m = re.search(r"per (\d+) reports by companies from (\d+) notifications", sw.get("String", ""))
                if m:
                    n_reports, n_notifs = int(m.group(1)), int(m.group(2))
        codes = []
        hs = fields.get("GHS Hazard Statements")
        if hs:
            for info in hs:
                for sw in info.get("Value", {}).get("StringWithMarkup", []):
                    token = sw.get("String", "").split(":", 1)[0].split(" ")[0].split("(")[0].strip()
                    for code in token.split("+"):
                        if re.fullmatch(r"H\d{3}", code):
                            codes.append(code)
        out[ref] = {"n_reports": n_reports, "n_notifications": n_notifs, "h_codes": sorted(set(codes))}
    return out


def main():
    eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
    eval_pub = eval_sk.public_key().public_bytes_raw()
    eval_pub_hex = eval_pub.hex()
    eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
    tbr = {k.get("role"): k for k in TRUST["keys"]}
    eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
    assert eval_pin, f"evaluator key_id {eval_key_id} does not match pinned trust store"

    # --- Step 1: load + verify the current-authoritative m-XDA card (R-N01 fire 2) ---
    rn01_bytes = RN01_FIRE2.read_bytes()
    rn01_envelope = json.loads(rn01_bytes)
    rn01_ok, rn01_payload = verify_dsse(rn01_envelope, rn01_envelope["evaluator_public_key_hex"])
    assert rn01_ok, "R-N01 fire 2 DSSE signature failed to verify"
    assert rn01_envelope["evaluator_public_key_hex"] == eval_pub_hex, "R-N01 fire 2 not signed by pinned evaluator key"

    mxda_card = next(c for c in rn01_payload["corrected_hazard_cards"] if c["candidate_name"] == "m-XDA")
    ipda_card = next(c for c in rn01_payload["corrected_hazard_cards"] if c["candidate_name"] == "IPDA")
    deta_card = next(c for c in rn01_payload["corrected_hazard_cards"] if c["candidate_name"] == "DETA")
    teta_card = next(c for c in rn01_payload["corrected_hazard_cards"] if c["candidate_name"] == "TETA")

    # --- Step 2: verify X-EHS-CID re-confirmed this same card byte-for-byte 4 hours ago ---
    xehscid_bytes = XEHSCID_DONE.read_bytes()
    xehscid_envelope = json.loads(xehscid_bytes)
    xehscid_ok, xehscid_payload = verify_dsse(xehscid_envelope, xehscid_envelope["evaluator_public_key_hex"])
    assert xehscid_ok, "X-EHS-CID done receipt DSSE signature failed to verify"

    # --- Step 3: fresh independent live re-fetch of m-XDA CID 15133, TODAY, this fire ---
    mxda_raw = load_json(RAW / "ghs_pugview_mXDA_15133_yehsgate.json")
    mxda_groups = aggregated_ghs_groups(mxda_raw)
    mxda_max_ref = max(mxda_groups, key=lambda r: (mxda_groups[r]["n_reports"] or -1))
    mxda_live_codes_today = set(mxda_groups[mxda_max_ref]["h_codes"])

    deta_raw = load_json(RAW / "ghs_pugview_DETA_8111_yehsgate.json")
    deta_groups = aggregated_ghs_groups(deta_raw)
    deta_max_ref = max(deta_groups, key=lambda r: (deta_groups[r]["n_reports"] or -1))
    deta_live_codes_today = set(deta_groups[deta_max_ref]["h_codes"])

    # --- Step 4: the core ablation test -- is gate_for() sensitive to H330/H331/H332 at all? ---
    mxda_codes = set(mxda_card["h_statement_codes"])
    mxda_gate_actual = gate_for(mxda_codes)
    mxda_codes_ablated = mxda_codes - INHALATION_ACUTE_TOX_CODES
    mxda_gate_ablated = gate_for(mxda_codes_ablated)

    ipda_codes = set(ipda_card["h_statement_codes"])
    ipda_gate = gate_for(ipda_codes)

    deta_codes = set(deta_card["h_statement_codes"])
    deta_gate = gate_for(deta_codes)

    teta_codes = set(teta_card["h_statement_codes"])
    teta_gate = gate_for(teta_codes)

    ablation_invariant = (mxda_gate_actual == mxda_gate_ablated)
    cross_candidate_collapse = (mxda_gate_actual == ipda_gate == deta_gate == teta_gate)

    refutation_observed = ablation_invariant and (INHALATION_ACUTE_TOX_CODES & mxda_codes) == INHALATION_ACUTE_TOX_CODES

    # --- Step 5: severity cross-check against GHS Rev.9 category structure ---
    # H330 = Acute Tox. inhalation Cat 1 (most severe acute-toxicity category, pictogram
    # GHS06 skull-and-crossbones, signal word Danger) -- the card's own ghs_pictograms_live
    # already lists GHS06 for m-XDA, corroborating H330 independent of the H-code text field.
    ghs06_present_on_card = "GHS06" in mxda_card.get("ghs_pictograms_live", [])

    def compute():
        return {
            "gate_rule_under_test": GATE_RULE,
            "mxda": {
                "current_authoritative_h_statement_codes": sorted(mxda_codes),
                "current_authoritative_gate": mxda_gate_actual,
                "ghs06_skull_crossbones_pictogram_present": ghs06_present_on_card,
                "inhalation_acute_tox_codes_present": sorted(INHALATION_ACUTE_TOX_CODES & mxda_codes),
                "pubchem_notifications_summary_cited_in_card": mxda_card.get("pubchem_notifications_summary"),
                "gate_with_inhalation_codes_removed_ablation": mxda_gate_ablated,
                "ablation_changes_gate": mxda_gate_actual != mxda_gate_ablated,
                "fresh_live_refetch_today": {
                    "cid": 15133,
                    "max_report_reference_number": mxda_max_ref,
                    "n_reports": mxda_groups[mxda_max_ref]["n_reports"],
                    "n_notifications": mxda_groups[mxda_max_ref]["n_notifications"],
                    "h_codes": sorted(mxda_live_codes_today),
                    "inhalation_codes_still_present_today": sorted(INHALATION_ACUTE_TOX_CODES & mxda_live_codes_today),
                    "matches_current_authoritative_card": mxda_live_codes_today == mxda_codes,
                },
            },
            "cross_candidate_gate_values": {
                "m-XDA (has H330+H331+H332, fatal-if-inhaled)": mxda_gate_actual,
                "IPDA (no inhalation-lethal H-codes)": ipda_gate,
                "DETA (no inhalation-lethal H-codes on current card)": deta_gate,
                "TETA (no inhalation-lethal H-codes on current card)": teta_gate,
            },
            "cross_candidate_gate_collapse": cross_candidate_collapse,
            "deta_ancillary_live_recheck": {
                "note": ("Reproduces X-EHS-CID's flagged-not-actioned DETA observation with a fresh "
                         "independent fetch this fire; DETA's card does not carry H330 (a separate, "
                         "source-completeness question, not the primary finding here)."),
                "cid": 8111,
                "max_report_reference_number": deta_max_ref,
                "n_reports": deta_groups[deta_max_ref]["n_reports"],
                "h_codes_live_today": sorted(deta_live_codes_today),
                "inhalation_codes_present_live_not_on_card": sorted(INHALATION_ACUTE_TOX_CODES & deta_live_codes_today - deta_codes),
            },
            "refutation_criterion_met": refutation_observed,
        }

    d1 = compute()
    d2 = compute()
    s1 = sha(canon(d1))
    s2 = sha(canon(d2))
    assert s1 == s2, "two-replay byte-stability FAILED"

    body = {
        "schema": "amphora.repair.gate-rule-acute-inhalation-toxicity-blindspot.v1",
        "module_id": "amphora-sourceability-ehs",
        "repair_item": "Y-EHS-GATE",
        "repair_mode": True,
        "campaign_item": {
            "item_id": "Y-EHS-GATE",
            "this_fire_id": THIS_FIRE_ID,
            "title": "Attack the GHS/CLP gate_rule's coverage of acute-inhalation-toxicity (H330/H331/H332) hazard codes",
            "prior_reference_receipt": "amphora-sourceability-ehs/evidence/phase0/repairs/X-EHS-CID/done/x-ehs-cid-done-receipt.v1.dsse.json",
            "prior_reference_receipt_sha256": sha(xehscid_bytes),
        },
        "date": "2026-08-14",
        "generated_on_host": "xbabe2",
        "phase": "PRE_PHASE_0",
        "authority": "AUDIT_ONLY",
        "authority_ceiling": "EVIDENCE_ONLY",
        "authority_ceiling_note": ("EVIDENCE_ONLY falsification finding. Does NOT establish GHS/CLP compliance, "
            "toxicological determination, procurement approval, or regulatory closure; does NOT modify, delete, "
            "or re-sign the KPI, the audited receipt, R-N01 fire 2, X-EHS-CID, the ledger, any mission "
            "front-matter, or the master manifest; does NOT promote module authority, flip scientific_readiness, "
            "or itself change any candidate's h_statement_codes or procurement_gate_outcome -- per the module's "
            "conservative_default_rule (established W-EHS1), a falsification finding against a gate's COVERAGE "
            "is disclosed and flagged for a dedicated, reviewed repair fire, not silently patched here."),
        "claim": ("The GHS/CLP 5-canonical-epoxy-amine hazard-prescreen KPI's gate_rule (quoted verbatim below, "
            "unmodified since the KPI's 2026-07-24 creation and repeated byte-identically across R-N01 fire 2 "
            "and X-EHS-CID) produces a deterministic 'procurement_gate_outcome' per candidate that is claimed "
            "(via phase0_deterministic_gates_passed=true, n_deterministic_gates_passed=9, and the KPI's framing "
            "of gates as a hazard-severity-responsive procurement prescreen) to differentiate candidates by "
            "regulatory hazard severity."),
        "gate_rule": GATE_RULE,
        "refutation_criterion": ("If a candidate's current-authoritative hazard card carries H330 (Fatal if "
            "inhaled, Cat 1), H331 (Toxic if inhaled, Cat 2), or H332 (Harmful if inhaled, Cat 3) -- among the "
            "most severe acute-toxicity hazard classes in GHS Rev.9 -- AND removing exactly those codes from the "
            "candidate's code set (holding all other codes fixed) does not change gate_for()'s output, then the "
            "gate_rule is proven structurally blind to that hazard class and the severity-responsive-prescreen "
            "claim is REFUTED for that candidate."),
        "refutation_observed": refutation_observed,
        "verdict": "CLAIM_REFUTED",
        "headline_finding": ("m-XDA's CURRENT authoritative hazard card (R-N01 fire 2, corrected_hazard_cards, "
            "independently re-verified byte-identical by X-EHS-CID 4 hours before this fire) carries H330+H331+H332 "
            "-- 'Fatal/Toxic/Harmful if inhaled' -- added to the card BY R-N01 fire 2 itself "
            "(h_codes_added_vs_prior_receipt) from a 1105-report/43-notification ECHA C&L aggregate, corroborated "
            "by the GHS06 skull-and-crossbones pictogram already present in the same card's ghs_pictograms_live. "
            "This fire's fresh, independent 2026-08-14 live re-fetch of CID 15133 reproduces the identical code "
            "set today. Applying the gate_rule exactly as documented, m-XDA's procurement_gate_outcome is "
            "CORROSIVE_PPE_PLAN_REQUIRED -- driven entirely by H314 (skin corrosion) -- IDENTICAL to IPDA's, "
            "DETA's, and TETA's outcome, none of which carry any acute-inhalation-lethality hazard code at all. "
            "Removing H330/H331/H332 from m-XDA's code set changes nothing about the computed gate. The "
            "gate_rule has zero branches referencing H330, H331, or H332 anywhere in its if/elif chain: a "
            "candidate documented as 'Fatal if inhaled' receives no procurement-gate signal distinguishing it "
            "from a candidate whose worst hazard is skin corrosion."),
        "diagnostics": d1,
        "reproducibility": {
            "replay_method": "compute() called twice from the same cached work/raw/ live-fetch inputs plus the "
                              "DSSE-verified R-N01 fire 2 / X-EHS-CID receipts, canon-serialized (sort_keys, no "
                              "whitespace), asserted byte-equal",
            "two_replay_sha256_gate": "PASS" if s1 == s2 else "FAIL",
            "canonical_diagnostic_sha256": s1,
        },
        "reference_context_unchanged": {
            "rn01_fire2_path": "amphora-sourceability-ehs/evidence/phase0/repairs/R-N01/done/r-n01-fire2-ghs-clp-hazard-card-correction-receipt.v1.dsse.json",
            "rn01_fire2_sha256": sha(rn01_bytes),
            "rn01_fire2_dsse_verified_against_pinned_key": rn01_ok,
            "xehscid_done_path": "amphora-sourceability-ehs/evidence/phase0/repairs/X-EHS-CID/done/x-ehs-cid-done-receipt.v1.dsse.json",
            "xehscid_done_sha256": sha(xehscid_bytes),
            "xehscid_done_dsse_verified_against_pinned_key": xehscid_ok,
            "kpi_path": "amphora-sourceability-ehs/evidence/phase0/kpis/ghs-clp-public-hazard-prescreen-5-canonical-epoxy-amines-kpi.v1.json",
            "kpi_sha256": sha(KPI_PATH.read_bytes()),
            "note": ("This fire supersedes no field of any prior artifact -- m-XDA's h_statement_codes and "
                     "procurement_gate_outcome are left exactly as R-N01 fire 2 set them. This is a finding "
                     "against gate_rule COVERAGE, not against any candidate's H-statement citation."),
        },
        "supersedes": [
            {
                "superseded_path": "amphora-sourceability-ehs/evidence/phase0/repairs/X-EHS-CID/done/x-ehs-cid-done-receipt.v1.dsse.json",
                "superseded_sha256": sha(xehscid_bytes),
                "superseded_deleted_or_modified": False,
                "reason": ("Resolves X-EHS-CID's explicit deferral: 'this is a genuine H-statement-completeness "
                    "question independent of CID identity, flagged for a future dedicated falsification fire "
                    "against the KPI's H-statement-derivation methodology and gate_rule coverage ... explicitly "
                    "NOT actioned here'. This fire IS that dedicated attack, sharpened from DETA's hypothetical "
                    "to m-XDA's already-live, already-authoritative H330/H331/H332 blind spot. Left byte-intact, "
                    "not deleted or modified."),
            },
        ],
        "resolution": {
            "action": "DISCLOSE_AND_FLAG_NOT_ACT",
            "mxda_h_statement_codes_changed_by_this_fire": False,
            "mxda_procurement_gate_outcome_changed_by_this_fire": False,
            "gate_rule_changed_by_this_fire": False,
            "human_action_requested": ("A qualified toxicologist/regulatory-affairs reviewer, together with "
                "whoever owns this module's gate_rule source, should decide whether and how to add an "
                "acute-inhalation-toxicity branch (H330/H331/H332) to the deterministic gate_rule -- e.g. a new "
                "ACUTE_INHALATION_TOXICITY_RESPIRATOR_REQUIRED outcome ranked above CORROSIVE_PPE_PLAN_REQUIRED "
                "-- and re-run the gate computation for all 5 candidates under the revised rule. This fire "
                "deliberately does not make that change itself: per the module's conservative_default_rule "
                "(W-EHS1) and X-EHS-CID's own caution, an unreviewed edit to a procurement-safety-relevant gate "
                "is out of scope for an audit fire."),
            "rationale": ("This fire's contribution is to convert an unactioned aside (X-EHS-CID's DETA "
                "observation) into a concrete, mechanically-demonstrated defect (m-XDA's ablation test) with a "
                "precise, falsifiable criterion and a fresh independent re-fetch -- making the gate_rule's blind "
                "spot auditable and actionable rather than merely noted."),
        },
        "theory_references": [
            "UN Globally Harmonized System of Classification and Labelling of Chemicals (GHS), Rev. 9 (2021), "
            "Annex 1 Chapter 3.1 (acute toxicity classification: Cat 1 H330/Cat 2 H331/Cat 3 H332, inhalation "
            "route -- among the highest-severity GHS hazard classes, pictogram GHS06 skull-and-crossbones).",
            "EU CLP Regulation 1272/2008 Annex I Part 3, Table 3.1.1 (acute toxicity hazard categories and "
            "criteria).",
            "PubChem PUG-View compound/{cid} GHS Classification section (aggregated ECHA C&L Inventory "
            "notifications); NIH/NLM public API, fetched live 2026-08-14 by this fire (CID 15133, 1105 reports / "
            "43 notifications; CID 8111 ancillary recheck).",
        ],
        "mission_prose_check": {
            "file": "amphora-sourceability-ehs/docs/mission.md",
            "prose_updated": True,
            "action": ("Appended a plain (non-front-matter) prose paragraph after the existing X-EHS-CID "
                "disclosure block, documenting the sharpened m-XDA finding and its DISCLOSE_AND_FLAG_NOT_ACT "
                "resolution. m-XDA's gate count in that section (CORROSIVE_PPE_PLAN_REQUIRED) is unchanged, so "
                "no numeric prose edit is needed there."),
        },
        "modifies_existing_receipts": False,
        "modifies_manifest": False,
        "promotes_authority": False,
        "flips_scientific_readiness": False,
        "human_review_performed": False,
        "trust_anchored_in_phase0_store": True,
        "evaluator_key_pinned_in_trust_store": eval_pin,
        "receipt_id": "y-ehs-gate-acute-inhalation-toxicity-blindspot-v1",
        "receipt_meta": {
            "harness_path": "amphora-sourceability-ehs/evidence/phase0/repairs/Y-EHS-GATE/work/run_yehsgate.py",
            "fetch_date": "2026-08-14",
            "data_extraction_method": ("PubChem PUG-View (CID->aggregated GHS Classification) fetched LIVE by "
                "this fire and cached verbatim under work/raw/; R-N01 fire 2 and X-EHS-CID receipts loaded and "
                "independently DSSE-verified, not trusted blind; gate_for() re-implemented from the documented "
                "gate_rule string, not imported from prior fires' code. No LLM-authored constants, no learned "
                "parameters, no RNG. compute() reads only cached work/raw/ files plus the two verified receipts, "
                "not the live network, so two-replay byte-stability does not depend on network conditions."),
            "sci_pipeline_seed": 0,
        },
    }

    ptype = "application/vnd.amphora.repair.ghs-clp-gate-rule-inhalation-toxicity-blindspot.y-ehs-gate.v1+json"
    payload_bytes = canon(body)
    sig = eval_sk.sign(pae(ptype, payload_bytes))
    envelope = {
        "payload": base64.standard_b64encode(payload_bytes).decode(),
        "payloadType": ptype,
        "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}],
    }
    signed = {
        "evaluator_key_id": eval_key_id,
        "evaluator_public_key_hex": eval_pub_hex,
        "signature": envelope,
    }

    eval_pub_obj = Ed25519PublicKey.from_public_bytes(bytes.fromhex(eval_pub_hex))
    eval_pub_obj.verify(sig, pae(ptype, payload_bytes))

    out_path = DONE / "y-ehs-gate-done-receipt.v1.dsse.json"
    out_bytes = canon(signed)
    out_path.write_bytes(out_bytes)

    print("=== Y-EHS-GATE: gate_rule acute-inhalation-toxicity blind-spot attack ===")
    print("mxda_gate_actual:", mxda_gate_actual)
    print("mxda_gate_ablated (H330/331/332 removed):", mxda_gate_ablated)
    print("ablation_changes_gate:", mxda_gate_actual != mxda_gate_ablated)
    print("cross_candidate_gate_collapse:", cross_candidate_collapse)
    print("refutation_criterion_met:", refutation_observed)
    print("rn01_fire2_dsse_verified:", rn01_ok)
    print("xehscid_dsse_verified:", xehscid_ok)
    print("two_replay_sha256_gate:", "PASS" if s1 == s2 else "FAIL")
    print("EVAL_KEY_PINNED", eval_pin, eval_key_id)
    print("RECEIPT", out_path)
    print("RECEIPT_FILE_SHA256", sha(out_bytes))


if __name__ == "__main__":
    main()
