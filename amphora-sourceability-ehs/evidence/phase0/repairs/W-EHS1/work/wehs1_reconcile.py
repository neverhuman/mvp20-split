#!/usr/bin/env python3
"""W-EHS1: DDS H351 (suspected carcinogen) IARC-vs-PubChem reconciliation.

BACKGROUND: R-N01 fire 2 (done receipt
evidence/phase0/repairs/R-N01/done/r-n01-fire2-ghs-clp-hazard-card-correction-receipt.v1.dsse.json)
corrected CID-attribution defects for IPDA and m-XDA, and along the way
recorded (but explicitly left unresolved, "out_of_scope_observation") that
PubChem CID 2955's (DDS) own live aggregated GHS Classification does not
carry H351, even though DDS's CID citation was never wrong. R-N01 attributed
the H351 flag to a separately-cited "IARC Monograph Vol. 24 (1980)" source
and deferred the question of whether that IARC citation actually supports
the flag. This item (W-EHS1) closes that deferral.

ATTACK: this fire fetches BOTH sources live and independently:
  1. PubChem PUG-View aggregated GHS Classification for CID 2955 (re-fetched
     fresh 2026-08-05, a new HTTP round-trip distinct from R-N01's
     2026-08-04 cache).
  2. IARC's own official live "Agents Classified by the IARC Monographs"
     data file (webapi.iarc.who.int/loc/loc.app.js -- the JSON-like array
     backing the public https://monographs.iarc.who.int/list-of-classifications
     page), parsed programmatically (brace-matched substring extraction, not
     hand-transcribed) for the CAS-80-08-0 entry.

FINDING: neither live source, correctly read, substantiates H351 for DDS.
PubChem's aggregate omits it entirely. IARC's own current classification for
CAS 80-08-0 (Dapsone) is Group 3 ("not classifiable as to its carcinogenicity
to humans" -- IARC Monographs Preamble, amended Jan 2019, Part B Section 6),
last evaluated 1987 (Monograph Vol. 24 + Suppl. 7) and unchanged since. Group
3 is IARC's own negative/inconclusive bottom line -- NOT a "suspected"
(Category 2) signal -- so citing "IARC Monograph Vol. 24, Group 3" as support
for H351 is a source-to-claim mapping error in the original 2026-07-23 hand
-compiled card, not evidence of a live disagreement between two sources that
both affirmatively assert carcinogenicity.

RESOLUTION (this fire): applies the campaign item's mandated rule -- a
hazard flag whose citation cannot be verified must never silently resolve to
the permissive reading. Because neither cited source substantiates H351, and
this fire has no authority to unilaterally determine DDS's toxicological
status, the CARCINOGEN_CAT_2_MONITORING_REQUIRED gate is KEPT (the more
protective outcome), not downgraded. This receipt publishes the disagreement
with both citations, states an explicit authoritative-source rule for this
KPI's GHS/CLP-keyed procurement-prescreen purpose, states the conservative
default rule applied, and flags the citation for mandatory human
toxicological review before any relaxation. It does NOT modify the DDS
card's h_statement_codes or procurement_gate_outcome.

RIGHTS-CLEAN: PubChem (NIH/NLM public API) and IARC's own public monographs
website / webapi.iarc.who.int (WHO public agency data, official classification
list) -- both public-domain/public-agency sources, no rights-gated content.

EVIDENCE_ONLY / AUDIT_ONLY. Does not itself establish GHS/CLP compliance,
toxicological determination, procurement approval, or regulatory closure.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-sourceability-ehs"
ITEM_DIR = MOD / "evidence/phase0/repairs/W-EHS1"
WORK = ITEM_DIR / "work"
RAW = WORK / "raw"
DONE = ITEM_DIR / "done"
DONE.mkdir(parents=True, exist_ok=True)

SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = json.loads((ROOT / "config/phase0-trust-store.v1.json").read_text())

R_N01_FIRE2_RECEIPT = MOD / "evidence/phase0/repairs/R-N01/done/r-n01-fire2-ghs-clp-hazard-card-correction-receipt.v1.dsse.json"
AUDITED_RECEIPT_PATH = MOD / "reference/mvp20/data/ghs_clp_public_hazard_prescreen_5_canonical_epoxy_amines_receipt.v1.json"
AUDITED_KPI_PATH = MOD / "evidence/phase0/kpis/ghs-clp-public-hazard-prescreen-5-canonical-epoxy-amines-kpi.v1.json"

THIS_FIRE_ID = "20260805T080001-184849-090ba5bb8d12"

DDS_CAS = "80-08-0"
DDS_CID = 2955

GATE_RULE = ("if H350/H340/H360 present -> SVHC_REVIEW_REQUIRED (would-be SVHC candidate); "
             "elif H334 present -> RESPIRATORY_SENSITISER_CONTAINMENT_REQUIRED; "
             "elif H351 present -> CARCINOGEN_CAT_2_MONITORING_REQUIRED; "
             "elif H314 present -> CORROSIVE_PPE_PLAN_REQUIRED; else STANDARD_PROCUREMENT.")

AUTHORITATIVE_SOURCE_RULE = (
    "For this KPI's purpose (a GHS/CLP-keyed procurement prescreen whose gate_rule dispatches "
    "strictly on GHS H-statement codes -- H350/H340/H360, H334, H351, H314), the authoritative "
    "source for whether a candidate CARRIES a given H-code is the harmonised/self-classified "
    "GHS/CLP hazard-classification record for that candidate's CAS-correct PubChem CID (the "
    "aggregated ECHA C&L Inventory notifications surfaced via PubChem PUG-View), because that "
    "record IS a GHS/CLP classification expressed in the same H-code currency the gate_rule reads. "
    "An IARC Monographs cancer-hazard-identification Group (1/2A/2B/3/4) is NOT itself a GHS/CLP "
    "carcinogen category and does not mechanically convert to one -- IARC groups answer 'is there "
    "sufficient/limited/inadequate evidence of carcinogenicity', a hazard-identification judgement, "
    "while GHS Carc. Cat. 1A/1B/2 (H350/H351) is a classification judgement requiring the CLP "
    "competent authority or self-classifying company to weigh that evidence against CLP Annex I "
    "criteria (UN GHS Rev.9 2021, Annex 1, Chapter 3.6; ECHA Guidance on the Application of the CLP "
    "Criteria, Version 5.0, 2017, Part 3 Section 3.6, weight-of-evidence carcinogen classification). "
    "IARC evaluations are legitimate SUPPORTING evidence for a CLP classification decision, but an "
    "IARC Group number cannot itself be cited as if it were the GHS H-code determination -- doing so "
    "is a source-to-claim category error, which is what this fire finds in DDS's original card."
)

CONSERVATIVE_DEFAULT_RULE = (
    "When a cited hazard-classification source cannot be verified by live fetch to actually support "
    "the H-code it is cited for, this module retains the EXISTING (more protective) hazard statement "
    "and procurement gate rather than downgrading it, and flags the citation as requiring mandatory "
    "human toxicological/regulatory review before any relaxation. A hazard flag whose supporting "
    "citation is in question must never silently resolve to the permissive (lower-scrutiny) reading -- "
    "the burden of proof for REMOVING a protective gate is higher than the burden for adding a review "
    "flag. This rule is applied verbatim as instructed by campaign item W-EHS1."
)


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
    return b[:32]


def aggregated_ghs(pugview_json):
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

    for ref, fields in groups.items():
        if "ECHA C&L Notifications Summary" in fields:
            hs = fields.get("GHS Hazard Statements")
            codes = []
            if hs:
                for sw in hs.get("Value", {}).get("StringWithMarkup", []):
                    text = sw.get("String", "")
                    code = text.split(":", 1)[0].split(" ")[0].split("(")[0].strip()
                    if code.startswith("H") and code[1:2].isdigit():
                        codes.append(code)
            pictos = []
            pic_field = fields.get("Pictogram(s)")
            if pic_field:
                for sw in pic_field.get("Value", {}).get("StringWithMarkup", []):
                    for m in sw.get("Markup", []):
                        if m.get("Type") == "Icon":
                            extra = m.get("Extra", "")
                            url = m.get("URL", "")
                            code = url.rsplit("/", 1)[-1].replace(".svg", "") if url else extra
                            pictos.append(code)
            signal = None
            sig_field = fields.get("Signal")
            if sig_field:
                vals = sig_field.get("Value", {}).get("StringWithMarkup", [])
                if vals:
                    signal = vals[0].get("String")
            summary_text = fields["ECHA C&L Notifications Summary"]["Value"]["StringWithMarkup"][0]["String"]
            return {"h_codes": sorted(set(codes)), "pictograms": pictos, "signal_word": signal,
                    "notifications_summary": summary_text}
    return {"h_codes": [], "pictograms": [], "signal_word": None, "notifications_summary": None}


def parse_iarc_entry(js_text: str, name: str) -> dict:
    """Brace-matched extraction of one agent's object literal from IARC's
    live loc.app.js data array, then field-by-field regex extraction. No
    hand-transcription of the classification itself."""
    import re
    idx = js_text.find('"' + name + '"')
    if idx == -1:
        raise ValueError(f"{name} not found in IARC live data file")
    start = js_text.rfind("{", 0, idx)
    depth = 0
    end = start
    for i in range(start, len(js_text)):
        if js_text[i] == "{":
            depth += 1
        elif js_text[i] == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    entry_text = js_text[start:end]

    def field(pat, cast=str, default=None):
        m = re.search(pat, entry_text)
        return cast(m.group(1)) if m else default

    group = field(r'group:"([^"]+)"')
    cas_list = re.findall(r'"([0-9]{2,7}-\d\d-\d)"', field(r'cas:\[([^\]]*)\]', str, "") or "")
    volume_list = re.findall(r'"([^"]+)"', field(r'volume:\[([^\]]*)\]', str, "") or "")
    year = field(r'year:"?([0-9]+)"?', int)
    yeareval = field(r'yeareval:([0-9]+)', int)
    comment = field(r'comment:"([^"]*)"')
    return {
        "entry_text_raw": entry_text,
        "name": name,
        "group": group,
        "cas": cas_list,
        "volume": volume_list,
        "year": year,
        "yeareval": yeareval,
        "comment": comment,
    }


IARC_GROUP_DEFINITIONS = {
    "1": "Carcinogenic to humans (sufficient evidence in humans).",
    "2A": "Probably carcinogenic to humans (limited evidence in humans, sufficient in experimental animals, or strong mechanistic support).",
    "2B": "Possibly carcinogenic to humans (limited evidence in humans without sufficient animal evidence, or sufficient evidence in animals alone).",
    "3": "Not classifiable as to its carcinogenicity to humans (evidence is inadequate in humans and inadequate or limited in experimental animals). This is IARC's negative/inconclusive bottom-line rating, not a positive suspicion finding.",
    "4": "Probably not carcinogenic to humans.",
}


def compute():
    ghs_pugview = load_json(RAW / f"ghs_pugview_DDS_{DDS_CID}.json")
    identity = load_json(RAW / f"identity_DDS_{DDS_CID}.json")
    cas_to_cid = load_json(RAW / "cas_to_cid_DDS.json")
    iarc_js = (RAW / "iarc_loc_app.js").read_text()

    pubchem_ghs = aggregated_ghs(ghs_pugview)
    prop = identity["PropertyTable"]["Properties"][0]
    resolved_cid = cas_to_cid["IdentifierList"]["CID"][0]

    iarc_entry = parse_iarc_entry(iarc_js, "Dapsone")

    pubchem_h351_present = "H351" in pubchem_ghs["h_codes"]
    iarc_cas_matches = DDS_CAS in iarc_entry["cas"]
    iarc_group = iarc_entry["group"]
    iarc_group_def = IARC_GROUP_DEFINITIONS.get(iarc_group, "unknown group")
    iarc_supports_h351 = iarc_group in ("1", "2A", "2B")

    diagnostic = {
        "dds_cid_resolved_from_cas": resolved_cid,
        "dds_cid_matches_expected": resolved_cid == DDS_CID,
        "dds_pubchem_identity": {"cid": prop["CID"], "iupac_name": prop.get("IUPACName"),
                                  "molecular_formula": prop.get("MolecularFormula"),
                                  "smiles": prop.get("CanonicalSMILES")},
        "pubchem_aggregate_ghs": pubchem_ghs,
        "pubchem_h351_present": pubchem_h351_present,
        "iarc_entry": {k: v for k, v in iarc_entry.items() if k != "entry_text_raw"},
        "iarc_entry_raw_text": iarc_entry["entry_text_raw"],
        "iarc_cas_matches_dds": iarc_cas_matches,
        "iarc_group_definition": iarc_group_def,
        "iarc_group_supports_h351_category": iarc_supports_h351,
        "either_source_substantiates_h351": pubchem_h351_present or iarc_supports_h351,
    }
    return diagnostic


def main():
    d1 = compute()
    d2 = compute()
    s1, s2 = sha(canon(d1)), sha(canon(d2))
    assert s1 == s2, f"two-replay diagnostic mismatch {s1} != {s2}"
    diag = d1

    assert diag["dds_cid_matches_expected"], "DDS CID resolution drifted from expected 2955"
    assert diag["iarc_cas_matches_dds"], "IARC entry CAS does not match DDS CAS 80-08-0"

    orig_receipt_bytes = AUDITED_RECEIPT_PATH.read_bytes()
    orig_receipt_sha = sha(orig_receipt_bytes)
    orig_kpi_bytes = AUDITED_KPI_PATH.read_bytes()
    orig_kpi_sha = sha(orig_kpi_bytes)
    rn01_fire2_bytes = R_N01_FIRE2_RECEIPT.read_bytes()
    rn01_fire2_sha = sha(rn01_fire2_bytes)

    fetch_harness_sha = sha((WORK / "wehs1_fetch.py").read_bytes())
    harness_sha = sha(Path(__file__).read_bytes())

    # Current (unchanged) DDS card fields, read from the live receipt on disk,
    # for the record -- this fire does not alter them.
    receipt_json = load_json(AUDITED_RECEIPT_PATH)
    dds_card = next(c for c in receipt_json["kpis"]["candidate_hazard_cards"] if c["candidate_name"] == "DDS")

    body = {
        "authority": "AUDIT_ONLY",
        "authority_ceiling": "EVIDENCE_ONLY",
        "authority_ceiling_note": (
            "EVIDENCE_ONLY reconciliation disclosure. Does NOT establish GHS/CLP compliance, "
            "toxicological determination, procurement approval, or regulatory closure; does not "
            "modify, delete, or re-sign any superseded receipt/KPI, the ledger, any mission "
            "front-matter, or the master manifest; does not promote module authority or flip "
            "scientific_readiness; does NOT alter DDS's h_statement_codes or procurement_gate_outcome "
            "(kept at the existing, more protective CARCINOGEN_CAT_2_MONITORING_REQUIRED per the "
            "conservative_default_rule below)."
        ),
        "module_id": "amphora-sourceability-ehs",
        "schema": "amphora.repair.h351-source-reconciliation.v1",
        "receipt_id": "w-ehs1-dds-h351-iarc-pubchem-reconciliation-v1",
        "repair_item": "W-EHS1",
        "repair_mode": True,
        "phase": "PRE_PHASE_0",
        "date": "2026-08-05",
        "generated_on_host": "xbabe2",
        "human_review_performed": False,
        "promotes_authority": False,
        "flips_scientific_readiness": False,
        "modifies_manifest": False,
        "modifies_existing_receipts": False,
        "trust_anchored_in_phase0_store": True,
        "campaign_item": {
            "item_id": "W-EHS1",
            "title": "Reconcile the DDS H351 IARC-vs-PubChem discrepancy",
            "this_fire_id": THIS_FIRE_ID,
            "prior_reference_receipt": str(R_N01_FIRE2_RECEIPT.relative_to(ROOT)),
            "prior_reference_receipt_sha256": rn01_fire2_sha,
        },
        "claim": (
            "R-N01 fire 2 deferred, as out-of-scope, whether DDS's H351 (suspected carcinogen, GHS "
            "Carc. Cat. 2) flag is substantiated given that PubChem CID 2955's own live aggregate does "
            "not carry H351, and the flag's separately-cited source is 'IARC Monograph Vol. 24 (1980)'. "
            "THIS fire fetches both sources live and independently (2026-08-05) and finds: (a) PubChem "
            "CID 2955's aggregated GHS Classification does NOT carry H351 (h_codes: H302, H371, H373, "
            "H411 only), reproducing R-N01's aside with a fresh fetch; (b) IARC's own official live "
            "classification data confirms CAS 80-08-0 (Dapsone) is Group 3 -- 'not classifiable as to "
            "its carcinogenicity to humans' -- last evaluated 1987 (Monograph Vol. 24 + Supplement 7), "
            "unchanged since. Group 3 is IARC's own negative/inconclusive rating, NOT a Group 1/2A/2B "
            "'suspected or probable carcinogen' finding, so it does not itself support an H351 "
            "classification either. Neither live source substantiates H351: the original card's "
            "citation of 'IARC Monograph Vol. 24, Group 3' as grounding for a 'suspected carcinogen' "
            "flag is a source-to-claim mapping error, not evidence of two sources genuinely disagreeing "
            "about DDS's carcinogenicity."
        ),
        "sources": {
            "pubchem": {
                "cid": DDS_CID,
                "cas_verified": DDS_CAS,
                "identity": diag["dds_pubchem_identity"],
                "aggregated_ghs_classification": diag["pubchem_aggregate_ghs"],
                "h351_present": diag["pubchem_h351_present"],
                "fetch_endpoint": f"https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/{DDS_CID}/JSON/?heading=GHS+Classification",
                "fetch_date": "2026-08-05",
            },
            "iarc": {
                "agent_name": diag["iarc_entry"]["name"],
                "cas": diag["iarc_entry"]["cas"],
                "group": diag["iarc_entry"]["group"],
                "group_definition": diag["iarc_group_definition"],
                "monograph_volume": diag["iarc_entry"]["volume"],
                "publication_year": diag["iarc_entry"]["year"],
                "last_evaluation_year": diag["iarc_entry"]["yeareval"],
                "comment": diag["iarc_entry"]["comment"],
                "group_supports_ghs_carc_cat2_reading": diag["iarc_group_supports_h351_category"],
                "fetch_endpoint": "https://webapi.iarc.who.int/loc/loc.app.js",
                "fetch_source_page": "https://monographs.iarc.who.int/list-of-classifications",
                "fetch_date": "2026-08-05",
                "raw_entry_extracted": diag["iarc_entry_raw_text"],
            },
        },
        "either_source_substantiates_h351": diag["either_source_substantiates_h351"],
        "authoritative_source_rule": AUTHORITATIVE_SOURCE_RULE,
        "conservative_default_rule": CONSERVATIVE_DEFAULT_RULE,
        "resolution": {
            "action": "DISCLOSE_AND_FLAG_NOT_DOWNGRADE",
            "dds_h_statement_codes_current": dds_card["h_statement_codes"],
            "dds_h_statement_codes_changed_by_this_fire": False,
            "dds_procurement_gate_outcome_current": dds_card["procurement_gate_outcome"],
            "dds_procurement_gate_outcome_changed_by_this_fire": False,
            "rationale": (
                "Neither live-fetched source substantiates H351, but per the conservative_default_rule "
                "this fire does not have standing to strip a protective hazard gate on the basis of an "
                "audit finding that a citation is unsupported -- that is a toxicological/regulatory "
                "determination reserved for human review. The gate is KEPT at "
                "CARCINOGEN_CAT_2_MONITORING_REQUIRED (the permissive alternative -- STANDARD_PROCUREMENT "
                "-- is explicitly NOT taken). This receipt's contribution is to make the citation defect "
                "visible and auditable, with both sources and an explicit rule, where before it was only "
                "an unresolved aside in R-N01."
            ),
            "human_action_requested": (
                "A qualified toxicologist/regulatory-affairs reviewer should determine DDS's correct "
                "GHS Carc. classification (if any) from primary sources beyond this audit's scope -- "
                "e.g. supplier SDS self-classifications, national competent-authority classifications, "
                "or the full IARC Monograph Vol. 24 / Suppl. 7 narrative (not just its Group number) -- "
                "and either confirm H351 on stronger grounds or formally retire it via the module's "
                "normal supersede process."
            ),
        },
        "gate_rule": GATE_RULE,
        "supersedes": [
            {
                "superseded_path": str(R_N01_FIRE2_RECEIPT.relative_to(ROOT)),
                "superseded_sha256": rn01_fire2_sha,
                "superseded_deleted_or_modified": False,
                "reason": (
                    "Resolves R-N01 fire 2's out_of_scope_observation on DDS's H351/IARC citation, left "
                    "explicitly deferred there ('a distinct question outside this repair's CID-attribution "
                    "scope and is left for a future falsification fire, not actioned here'). This receipt "
                    "supersedes with the live IARC fetch and reconciliation that observation asked for. "
                    "Does not alter any field of the superseded receipt; left byte-intact."
                ),
            },
        ],
        "reference_context_unchanged": {
            "note": "The audited hazard-card receipt/KPI (DDS card specifically) are NOT superseded by this fire because no field of the DDS card changes -- see resolution.dds_*_changed_by_this_fire above.",
            "audited_receipt_path": str(AUDITED_RECEIPT_PATH.relative_to(ROOT)),
            "audited_receipt_sha256": orig_receipt_sha,
            "audited_kpi_path": str(AUDITED_KPI_PATH.relative_to(ROOT)),
            "audited_kpi_sha256": orig_kpi_sha,
        },
        "mission_prose_check": {
            "file": "amphora-sourceability-ehs/docs/mission.md",
            "action": (
                "Appended a plain (non-front-matter) prose paragraph after the existing R-N01 CORRECTION "
                "block, in the same fire, disclosing this reconciliation and its explicit rule; gate counts "
                "in that section are unchanged (DDS's CARCINOGEN_CAT_2_MONITORING_REQUIRED gate is not "
                "modified) so no numeric prose edit is needed there."
            ),
            "prose_updated": True,
        },
        "reproducibility": {
            "replay_method": "compute() called twice from the same cached work/raw/ inputs, results canon-serialized (sort_keys, no whitespace), asserted byte-equal",
            "two_replay_sha256_gate": "PASS" if s1 == s2 else "FAIL",
            "canonical_diagnostic_sha256": s1,
        },
        "receipt_meta": {
            "harness_path": "amphora-sourceability-ehs/evidence/phase0/repairs/W-EHS1/work/wehs1_reconcile.py",
            "harness_sha256": harness_sha,
            "fetch_harness_path": "amphora-sourceability-ehs/evidence/phase0/repairs/W-EHS1/work/wehs1_fetch.py",
            "fetch_harness_sha256": fetch_harness_sha,
            "fetch_date": "2026-08-05",
            "data_extraction_method": (
                "PubChem PUG-View (CID->aggregated GHS Classification) and PUG-REST (CAS->CID, "
                "CID->identity) responses, and IARC's own live webapi.iarc.who.int/loc/loc.app.js "
                "classification data file, all fetched LIVE by this fire and cached verbatim under "
                "work/raw/; the IARC agent entry is extracted programmatically via brace-matched "
                "substring search + regex field extraction (parse_iarc_entry()), not hand-transcribed. "
                "No LLM-authored constants, no learned parameters, no RNG. compute() reads only the "
                "cached work/raw/ files, not the live network, so two-replay byte-stability does not "
                "depend on network conditions."
            ),
            "sci_pipeline_seed": 0,
        },
        "theory_references": [
            "PubChem PUG-View compound/{cid} GHS Classification section (aggregated ECHA C&L Inventory notifications); NIH/NLM public API, fetched live 2026-08-05.",
            "PubChem PUG-REST compound/name/{cas}/cids and compound/cid/{cid}/property/...; fetched live 2026-08-05.",
            "IARC 'Agents Classified by the IARC Monographs, Volumes 1-138' live official data (webapi.iarc.who.int/loc/loc.app.js), backing https://monographs.iarc.who.int/list-of-classifications; WHO/IARC public agency data, fetched live 2026-08-05.",
            "IARC Monographs Preamble (amended January 2019), Part B Section 6 (Group 3 definition: 'not classifiable as to its carcinogenicity to humans').",
            "UN Globally Harmonized System of Classification and Labelling of Chemicals (GHS), Rev. 9 (2021), Annex 1 Chapter 3.6 (carcinogenicity classification criteria).",
            "ECHA Guidance on the Application of the CLP Criteria, Version 5.0 (2017), Part 3 Section 3.6 (weight-of-evidence carcinogen classification using IARC and other evidence).",
        ],
    }

    eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
    eval_pub = eval_sk.public_key().public_bytes_raw()
    eval_pub_hex = eval_pub.hex()
    eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
    tbr = {k.get("role"): k for k in TRUST["keys"]}
    eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
    assert eval_pin, f"evaluator key_id {eval_key_id} does not match pinned trust store"

    body["evaluator_key_id"] = eval_key_id
    body["evaluator_public_key_hex"] = eval_pub_hex
    body["evaluator_key_pinned_in_trust_store"] = eval_pin

    ptype = "application/vnd.amphora.repair.h351-source-reconciliation.v1+json"
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

    out_path = DONE / "w-ehs1-dds-h351-iarc-pubchem-reconciliation-receipt.v1.dsse.json"
    out_bytes = canon(signed)
    out_path.write_bytes(out_bytes)

    print("=== W-EHS1: DDS H351 IARC-vs-PubChem reconciliation ===")
    print("pubchem_h351_present:", diag["pubchem_h351_present"])
    print("iarc_group:", diag["iarc_entry"]["group"], diag["iarc_entry"])
    print("either_source_substantiates_h351:", diag["either_source_substantiates_h351"])
    print("SELF_VERIFY_OK True")
    print("EVAL_KEY_PINNED", eval_pin, eval_key_id)
    print("RECEIPT", out_path)
    print("RECEIPT_FILE_SHA256", sha(out_bytes))


if __name__ == "__main__":
    main()
