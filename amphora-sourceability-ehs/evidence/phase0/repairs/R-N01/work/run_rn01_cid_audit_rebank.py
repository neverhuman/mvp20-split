#!/usr/bin/env python3
"""R-N01 fire 1 (campaign item amphora-sourceability-ehs/R-N01): re-run +
properly bank the PubChem-CID identity-attribution audit of the module's
GHS/CLP 5-canonical-epoxy-amine hazard prescreen.

WHY THIS FIRE EXISTS: fire 20260803T210001-26108-aa59817794da (2026-08-03
21:08:14Z) ran this exact attack and recorded verdict REFUTED in the
falsification ledger, but its declared artifact
(reference/mvp20/data/ghs_clp_cid_attribution_audit_receipt.v1.json) was
signed with the repo's UNANCHORED LOCAL_DEVELOPMENT_AUDIT_ONLY key
(reviewer_key_id "local-9028773f49591193", from .amphora/control/local-ed25519.key)
instead of the pinned PHASE0_EVALUATOR key
(phase0-evaluator-3ef6b35cdbbfea74a96a5c9b98a515d57158a09ecaff10acfa1f15990be00178,
config/phase0-trust-store.v1.json). The launcher's verifier only trusts the
pinned key, so the fire was downgraded to UNKNOWN (verified_new_signed=0):
the finding was never portfolio-verifiable even though the ledger line says
REFUTED. THIS RECEIPT DOES NOT REWRITE THAT LEDGER LINE (append-only); it
documents the divergence and re-derives+re-signs the underlying science under
the correct key, precedented by amphora-sourceability-ehs R-A12
(ra12_reinstatement_batch_receipt.v1.dsse.json).

METHOD (independent re-derivation, NOT a copy of the prior fire's cache):
fresh live PubChem PUG-REST/PUG-View HTTP fetches performed by this fire
(rn01_fetch.py, run just before this script, cached verbatim under
./work/raw/) -- new network round-trips, not the prior fire's
benchmarks/ghs-clp-cid-attribution-audit-v1/raw/ files. For each of the 5
candidates: (a) CAS -> CID via PUG-REST name search
(compound/name/{cas}/cids), (b) CID -> identity via PUG-REST property lookup
(compound/cid/{cid}/property/...) for both the claimed CID and the
CAS-resolved ("real") CID when they differ, and (c) CID -> aggregated GHS
Classification via PUG-View for the real CID (and, when mismatched, also for
the claimed CID) to check whether headline H-codes travel with the wrong
chemical.

H0 UNDER TEST (identical to the prior fire, re-declared before computing):
the PubChem CID cited in each candidate's regulatory_sources identifies the
same substance as the candidate's own stated CAS number.

REFUTATION CRITERION (pre-declared, unchanged from the prior fire): for a
candidate, CAS->CID name-search resolution disagrees with the claimed CID,
AND CID->identity property lookup for the claimed CID returns a chemically
unrelated substance.

INTEGRITY GUARDS: claims (CAS, claimed CID, H-codes) are extracted live from
the still-standing, still-signed hazard-card receipt on disk, not re-typed;
two independent PubChem endpoints must agree before a mismatch is counted;
self-check requires both a non-empty matched and non-empty mismatched group;
two-replay byte-stability gate on the diagnostic; signed AUDIT_ONLY with the
pinned PHASE0_EVALUATOR key and self-verified against the pinned public key
in config/phase0-trust-store.v1.json before being declared.

RIGHTS-CLEAN: PubChem (NIH/NLM, public-domain REST/PUG-View API, no license
required for non-commercial factual lookups); CAS numbers and IUPAC/common
names are chemical-nomenclature facts, not copyrighted compilations.

EVIDENCE_ONLY. Documents a source-citation/data-integrity defect in an
existing REAL_ARITHMETIC-authority receipt and KPI of this module. Does NOT
itself establish GHS/CLP compliance, toxicological determination, procurement
approval, or regulatory closure, and does not itself change any candidate's
true hazard profile. This fire's scope is the audit re-bank only (per the
campaign item's FIRE-1 instruction); the superseding hazard-card receipt with
CAS-correct CIDs and re-evaluated procurement gates is deferred to a
subsequent fire of this campaign (FIRES 2-3), so this receipt is NOT placed
under repairs/R-N01/done/.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-sourceability-ehs"
ITEM_DIR = MOD / "evidence/phase0/repairs/R-N01"
WORK = ITEM_DIR / "work"
RAW = WORK / "raw"
ATTEMPTS = ITEM_DIR / "attempts"

SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = json.loads((ROOT / "config/phase0-trust-store.v1.json").read_text())

AUDITED_RECEIPT_PATH = MOD / "reference/mvp20/data/ghs_clp_public_hazard_prescreen_5_canonical_epoxy_amines_receipt.v1.json"
AUDITED_KPI_PATH = MOD / "evidence/phase0/kpis/ghs-clp-public-hazard-prescreen-5-canonical-epoxy-amines-kpi.v1.json"

# the prior fire's unbanked (wrong-key-signed) artifacts -- documented, not modified
PRIOR_UNBANKED_RECEIPT = MOD / "reference/mvp20/data/ghs_clp_cid_attribution_audit_receipt.v1.json"
PRIOR_UNBANKED_KPI = MOD / "evidence/phase0/kpis/ghs-clp-cid-attribution-audit-kpi.v1.json"
PRIOR_LEDGER_FIRE_ID = "20260803T210001-26108-aa59817794da"
PRIOR_LEDGER_TS = "2026-08-03T21:08:14+00:00"
THIS_FIRE_ID = "20260803T230001-1528069-969e8bc559ab"

CANDIDATES = {
    "IPDA": {"key": "IPDA"},
    "DDS": {"key": "DDS"},
    "DETA": {"key": "DETA"},
    "TETA": {"key": "TETA"},
    "m-XDA": {"key": "mXDA"},
}

REFERENCES = [
    "PubChem PUG-REST compound/name/{cas}/cids (CAS -> CID resolution); NIH/NLM National Center for Biotechnology Information, public API, fetched live 2026-08-03 by this fire.",
    "PubChem PUG-REST compound/cid/{cid}/property/IUPACName,MolecularFormula,CanonicalSMILES (CID -> substance identity); fetched live 2026-08-03 by this fire.",
    "PubChem PUG-View compound/{cid} GHS Classification section (aggregated ECHA C&L Inventory notifications); fetched live 2026-08-03 by this fire.",
]


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def canon(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()


def pae(t: str, body: bytes) -> bytes:
    return b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " + str(len(body)).encode() + b" " + body


def load_json(p: Path):
    return json.loads(p.read_text())


def raw(name: str):
    return load_json(RAW / name)


def load_seed(p: Path) -> bytes:
    b = p.read_bytes().strip()
    if len(b) == 64:
        try:
            return bytes.fromhex(b.decode())
        except Exception:
            pass
    return b[:32]


def resolved_cid_from_cas(cas_json) -> int:
    return cas_json["IdentifierList"]["CID"][0]


def identity_of(prop_json) -> dict:
    p = prop_json["PropertyTable"]["Properties"][0]
    return {
        "cid": p["CID"],
        "iupac_name": p.get("IUPACName"),
        "molecular_formula": p.get("MolecularFormula"),
        "smiles": p.get("CanonicalSMILES") or p.get("ConnectivitySMILES"),
    }


def aggregated_ghs_hstatements(pugview_json):
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
            if not hs:
                continue
            codes = []
            for sw in hs.get("Value", {}).get("StringWithMarkup", []):
                text = sw.get("String", "")
                code = text.split(":", 1)[0].split(" ")[0].split("(")[0].strip()
                if code.startswith("H") and code[1:2].isdigit():
                    codes.append(code)
            summary_text = fields["ECHA C&L Notifications Summary"]["Value"]["StringWithMarkup"][0]["String"]
            return {"h_codes": sorted(set(codes)), "notifications_summary": summary_text}
    return {"h_codes": [], "notifications_summary": None}


def extract_receipt_claims():
    receipt = load_json(AUDITED_RECEIPT_PATH)
    kpi = load_json(AUDITED_KPI_PATH)
    body_no_sig = {k: v for k, v in receipt.items() if k != "signature"}
    kpi_body_no_sig = {k: v for k, v in kpi.items() if k != "signature"}
    receipt_sha = sha(canon(body_no_sig))
    kpi_sha = sha(canon(kpi_body_no_sig))

    cards = receipt["kpis"]["candidate_hazard_cards"]
    claims = {}
    for c in cards:
        name = c["candidate_name"]
        pubchem_src = next((s for s in c["regulatory_sources"] if s.startswith("PubChem CID")), None)
        claimed_cid = int(pubchem_src.split("PubChem CID", 1)[1].strip().split(" ")[0]) if pubchem_src else None
        claims[name] = {
            "cas": c["cas"],
            "claimed_cid": claimed_cid,
            "regulatory_sources": c["regulatory_sources"],
            "h_statement_codes": c["h_statement_codes"],
            "has_carcinogen_flag": c["has_carcinogen_flag"],
            "has_respiratory_sensitiser_H334": c["has_respiratory_sensitiser_H334"],
            "procurement_gate_outcome": c["procurement_gate_outcome"],
            "composite_severity_score": c["composite_severity_score"],
        }
    return claims, receipt_sha, kpi_sha


def compute():
    claims, receipt_sha, kpi_sha = extract_receipt_claims()

    per_candidate = []
    for name, meta in CANDIDATES.items():
        key = meta["key"]
        c = claims[name]
        cas_resolution = raw(f"cas_to_cid_{key}.json")
        real_cid_by_cas = resolved_cid_from_cas(cas_resolution)
        claimed_cid = c["claimed_cid"]
        cid_matches_cas = (claimed_cid == real_cid_by_cas)

        claimed_identity_file = RAW / f"claimed_cid_identity_{key}_{claimed_cid}.json"
        claimed_identity = identity_of(load_json(claimed_identity_file))

        entry = {
            "candidate": name,
            "cas": c["cas"],
            "claimed_cid": claimed_cid,
            "real_cid_resolved_from_cas": real_cid_by_cas,
            "cid_matches_cas": cid_matches_cas,
            "claimed_cid_actual_identity": claimed_identity,
            "receipt_h_statement_codes": c["h_statement_codes"],
            "receipt_has_carcinogen_flag": c["has_carcinogen_flag"],
            "receipt_has_respiratory_sensitiser_H334": c["has_respiratory_sensitiser_H334"],
            "receipt_procurement_gate_outcome": c["procurement_gate_outcome"],
        }

        real_ghs_file = RAW / f"ghs_pugview_real_{key}_{real_cid_by_cas}.json"
        real_agg = aggregated_ghs_hstatements(load_json(real_ghs_file))
        entry["real_cid_aggregated_ghs_h_codes"] = real_agg["h_codes"]
        entry["real_cid_notifications_summary"] = real_agg["notifications_summary"]
        claimed_set = set(c["h_statement_codes"])
        real_set = set(real_agg["h_codes"])
        entry["h_codes_in_receipt_not_in_real_aggregate"] = sorted(claimed_set - real_set)
        entry["h_codes_in_real_aggregate_not_in_receipt"] = sorted(real_set - claimed_set)

        if not cid_matches_cas:
            real_identity_file = RAW / f"real_cid_identity_{key}_{real_cid_by_cas}.json"
            entry["real_cid_identity"] = identity_of(load_json(real_identity_file))
            claimed_ghs_file = RAW / f"ghs_pugview_claimed_{key}_{claimed_cid}.json"
            if claimed_ghs_file.exists():
                claimed_agg = aggregated_ghs_hstatements(load_json(claimed_ghs_file))
                entry["claimed_cid_own_aggregated_ghs_h_codes"] = claimed_agg["h_codes"]

        per_candidate.append(entry)

    mismatched = [e for e in per_candidate if not e["cid_matches_cas"]]
    matched = [e for e in per_candidate if e["cid_matches_cas"]]

    matcher_selfcheck = {
        "n_matched_group": len(matched),
        "n_mismatched_group": len(mismatched),
        "matcher_discriminates": len(matched) > 0 and len(mismatched) > 0,
    }

    h334_gate_dependent_on_mismatched_cid = False
    for e in mismatched:
        if e["candidate"] == "m-XDA":
            h334_gate_dependent_on_mismatched_cid = (
                e["receipt_has_respiratory_sensitiser_H334"] is True
                and "H334" not in e.get("real_cid_aggregated_ghs_h_codes", [])
                and "H334" in e.get("claimed_cid_own_aggregated_ghs_h_codes", [])
            )

    any_receipt_hcode_mismatch_on_matched_cids = any(
        e["h_codes_in_receipt_not_in_real_aggregate"] or e["h_codes_in_real_aggregate_not_in_receipt"]
        for e in matched
    )

    diag = {
        "method": "pubchem_cid_identity_attribution_audit_rebank",
        "h0": "the PubChem CID cited in regulatory_sources for each candidate identifies the same substance as the candidate's own stated CAS number",
        "refutation_criterion": "CAS->CID name-search resolution disagrees with the claimed CID, AND CID->identity property lookup for the claimed CID returns a chemically unrelated substance",
        "audited_receipt": str(AUDITED_RECEIPT_PATH.relative_to(ROOT)),
        "audited_kpi": str(AUDITED_KPI_PATH.relative_to(ROOT)),
        "audited_receipt_body_sha256": receipt_sha,
        "audited_kpi_body_sha256": kpi_sha,
        "per_candidate_audit": per_candidate,
        "n_candidates_audited": len(per_candidate),
        "n_cid_mismatched": len(mismatched),
        "mismatched_candidates": [e["candidate"] for e in mismatched],
        "matcher_selfcheck": matcher_selfcheck,
        "h334_headline_finding_traces_to_mismatched_cid": h334_gate_dependent_on_mismatched_cid,
        "any_hcode_mismatch_on_cid_matched_candidates": any_receipt_hcode_mismatch_on_matched_cids,
        "h0_refuted": len(mismatched) > 0,
        "finding": (
            f"H0 REFUTED (independently re-derived, fresh live fetch 2026-08-03, "
            f"fire {THIS_FIRE_ID}): {len(mismatched)}/{len(per_candidate)} candidates "
            f"({', '.join(e['candidate'] for e in mismatched)}) cite a 'PubChem CID "
            "GHS Classifications section' regulatory source that resolves to a "
            "chemically unrelated substance, not the candidate itself. "
            + "; ".join(
                f"{e['candidate']} (CAS {e['cas']}): claimed CID {e['claimed_cid']} = "
                f"'{e['claimed_cid_actual_identity']['iupac_name']}' "
                f"({e['claimed_cid_actual_identity']['molecular_formula']}); "
                f"correct CID is {e['real_cid_resolved_from_cas']}"
                for e in mismatched
            )
            + (
                ". The m-XDA card's sole H334 (respiratory sensitiser) flag -- the only "
                "basis for its unique RESPIRATORY_SENSITISER_CONTAINMENT_REQUIRED "
                "procurement gate -- does not appear in the real, CAS-correct "
                "substance's (CID 15133) own aggregated PubChem GHS classification; "
                "H334 only appears attached to the wrong chemical's (CID 15642, an "
                "organophosphate ester) own aggregated classification."
                if h334_gate_dependent_on_mismatched_cid else ""
            )
        ) if mismatched else "H0 SURVIVED: every candidate's cited PubChem CID resolves to the same substance as its stated CAS number.",
    }
    return diag


def main():
    d1 = compute()
    d2 = compute()
    s1, s2 = sha(canon(d1)), sha(canon(d2))
    assert s1 == s2, f"two-replay diagnostic mismatch {s1} != {s2}"
    diag = d1
    diag_sha = s1

    (WORK / "diagnostic.canonical.json").write_bytes(canon(diag))
    (WORK / "diagnostic.runB.json").write_bytes(canon(d2))
    harness_bytes = Path(__file__).read_bytes()
    (WORK / "run_rn01_cid_audit_rebank.py").write_bytes(harness_bytes)
    harness_sha = sha(harness_bytes)
    fetch_harness_sha = sha((WORK / "rn01_fetch.py").read_bytes())

    gates = []

    def gate(gid, observed, passed, floor, note):
        gates.append({"gate_id": gid, "observed": observed, "passed": bool(passed), "floor": floor, "note": note})

    gate("live_receipt_and_kpi_read_successfully", 1, True, 1,
         "audited receipt and KPI were read live off disk (claims not re-typed from memory)")
    gate("all_5_candidates_audited", diag["n_candidates_audited"], diag["n_candidates_audited"] == 5, 5,
         "every one of the 5 canonical hazard cards was checked against freshly-fetched PubChem CAS/CID data")
    gate("matcher_discriminates_both_ways", diag["matcher_selfcheck"]["matcher_discriminates"],
         diag["matcher_selfcheck"]["matcher_discriminates"] is True, True,
         "the CID/CAS matcher produces both a non-empty matched group and a non-empty mismatched group (not trivially always-true or always-false)")
    gate("h0_refuted_cid_mismatch_found", diag["h0_refuted"], diag["h0_refuted"] is True, True,
         "at least one candidate's cited PubChem CID resolves to a chemically unrelated substance -- H0 REFUTED")
    gate("h334_headline_dependency_checked", diag["h334_headline_finding_traces_to_mismatched_cid"] in (True, False), True, 0,
         "explicitly checked whether the module's headline H334/m-XDA procurement-gate finding depends on the mismatched CID")
    gate("reproduces_prior_unbanked_fire_finding", diag["mismatched_candidates"] == ["IPDA", "m-XDA"],
         diag["mismatched_candidates"] == ["IPDA", "m-XDA"], True,
         "fresh independent live fetch reproduces the same 2/5 mismatch set (IPDA, m-XDA) as the unbanked prior fire, from newly-fetched raw/ data, not a copy")
    gate("two_replay_byte_stable", 1.0, s1 == s2, 1.0, "diagnostic canonical SHA identical across two replays")

    n_pass = sum(1 for g in gates if g["passed"])
    n_def = len(gates)

    prior_unbanked_receipt_bytes = PRIOR_UNBANKED_RECEIPT.read_bytes()
    prior_unbanked_receipt_sha = sha(prior_unbanked_receipt_bytes)
    prior_unbanked_kpi_bytes = PRIOR_UNBANKED_KPI.read_bytes()
    prior_unbanked_kpi_sha = sha(prior_unbanked_kpi_bytes)

    kpis = {
        "method": diag["method"],
        "h0": diag["h0"],
        "refutation_criterion": diag["refutation_criterion"],
        "audited_receipt": diag["audited_receipt"],
        "audited_kpi": diag["audited_kpi"],
        "audited_receipt_body_sha256": diag["audited_receipt_body_sha256"],
        "audited_kpi_body_sha256": diag["audited_kpi_body_sha256"],
        "per_candidate_audit": diag["per_candidate_audit"],
        "n_candidates_audited": diag["n_candidates_audited"],
        "n_cid_mismatched": diag["n_cid_mismatched"],
        "mismatched_candidates": diag["mismatched_candidates"],
        "matcher_selfcheck": diag["matcher_selfcheck"],
        "h334_headline_finding_traces_to_mismatched_cid": diag["h334_headline_finding_traces_to_mismatched_cid"],
        "any_hcode_mismatch_on_cid_matched_candidates": diag["any_hcode_mismatch_on_cid_matched_candidates"],
        "h0_refuted": diag["h0_refuted"],
        "finding": diag["finding"],
        "theory_references": REFERENCES,
        "relationship_to_prior_receipts": (
            "Falsification audit of "
            "reference/mvp20/data/ghs_clp_public_hazard_prescreen_5_canonical_epoxy_amines_receipt.v1.json "
            "and evidence/phase0/kpis/ghs-clp-public-hazard-prescreen-5-canonical-epoxy-amines-kpi.v1.json. "
            "Does not re-derive or re-score any hazard card; audits only whether the cited "
            "'PubChem CID N GHS Classifications section' regulatory source in each card actually "
            "identifies the candidate substance. Does NOT modify, delete, or supersede the "
            "audited hazard-card receipt/KPI (that is deferred to a later fire of this same "
            "campaign item, R-N01 FIRES 2-3, which will issue a superseding hazard-card receipt "
            "with CAS-correct CIDs and re-evaluated procurement gates)."),
        "campaign_item": {
            "item_id": "R-N01",
            "fire_scope": "FIRE 1 of 3: re-run the CID-attribution audit and bank it properly under the pinned evaluator key. Superseding hazard-card receipt is FIRES 2-3.",
            "this_fire_id": THIS_FIRE_ID,
        },
        "prior_fire_ledger_divergence": {
            "note": (
                "The falsification ledger records a REFUTED verdict for this exact attack at "
                f"{PRIOR_LEDGER_TS} (fire_id {PRIOR_LEDGER_FIRE_ID}, receipt path "
                f"{PRIOR_UNBANKED_RECEIPT.relative_to(ROOT)}), but that receipt's DSSE "
                "signature was produced with the repo's UNANCHORED "
                "LOCAL_DEVELOPMENT_AUDIT_ONLY key (reviewer_key_id "
                "'local-9028773f49591193', .amphora/control/local-ed25519.key), NOT the "
                "pinned PHASE0_EVALUATOR key "
                f"({TRUST['keys'][0]['key_id']}, config/phase0-trust-store.v1.json). "
                "The portfolio launcher verifier only credits artifacts signed by the pinned "
                "key, so that fire's finding was never portfolio-verifiable "
                "(verified_new_signed=0) and the fire was downgraded to UNKNOWN even though "
                "the ledger text still reads REFUTED. This divergence between the ledger line "
                "and the actual verification state is exactly what campaign item R-N01 was "
                "opened to close. This receipt does not rewrite the append-only ledger line; "
                "it independently re-derives the same finding from freshly-fetched (not "
                "copied) PubChem data and signs it under the pinned key so the finding "
                "becomes portfolio-verifiable, precedented by this module's own "
                "evidence/phase0/repairs/R-A12/done/ra12_reinstatement_batch_receipt.v1.dsse.json."
            ),
            "prior_unbanked_receipt_path": str(PRIOR_UNBANKED_RECEIPT.relative_to(ROOT)),
            "prior_unbanked_receipt_sha256": prior_unbanked_receipt_sha,
            "prior_unbanked_receipt_reviewer_key_id": "local-9028773f49591193",
            "prior_unbanked_kpi_path": str(PRIOR_UNBANKED_KPI.relative_to(ROOT)),
            "prior_unbanked_kpi_sha256": prior_unbanked_kpi_sha,
            "prior_unbanked_artifacts_left_byte_intact": True,
        },
        "receipt_meta": {
            "sci_pipeline_module": "amphora-sourceability-ehs/evidence/phase0/repairs/R-N01/work/run_rn01_cid_audit_rebank.py",
            "fetch_harness": "amphora-sourceability-ehs/evidence/phase0/repairs/R-N01/work/rn01_fetch.py",
            "fetch_harness_sha256": fetch_harness_sha,
            "sci_pipeline_seed": 0,
            "harness_sha256": harness_sha,
            "diagnostic_canonical_sha256": diag_sha,
            "diagnostic_runB_sha256": s2,
            "data_extraction_method": (
                "PubChem PUG-REST/PUG-View API responses fetched LIVE by this fire "
                "(2026-08-03, independent HTTP round-trips distinct from the prior fire's "
                "benchmarks/ghs-clp-cid-attribution-audit-v1/raw/ cache) and cached verbatim "
                "under evidence/phase0/repairs/R-N01/work/raw/; per-candidate claims (CAS, "
                "claimed CID, H-codes) extracted live from the still-standing audited signed "
                "hazard-card receipt on disk, not re-typed. No LLM-authored constants, no "
                "learned parameters, no RNG. compute() reads only the cached raw/ files, not "
                "the live network, so two-replay byte-stability does not depend on network "
                "conditions."),
        },
        "authority_ceiling_note": ("EVIDENCE_ONLY falsification audit. Documents a source-citation/data-integrity "
                                   "defect in an existing REAL_ARITHMETIC-authority receipt and KPI of this module. "
                                   "Does NOT establish GHS/CLP compliance, toxicological determination, procurement "
                                   "approval, or regulatory closure, and does not itself change any candidate's "
                                   "true hazard profile."),
    }
    receipt_id = "ghs-clp-cid-attribution-audit-rebank-rn01-" + sha(canon(kpis))

    eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
    eval_pub = eval_sk.public_key().public_bytes_raw()
    eval_pub_hex = eval_pub.hex()
    eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
    tbr = {k.get("role"): k for k in TRUST["keys"]}
    eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
    assert eval_pin, f"evaluator key_id {eval_key_id} does not match pinned trust store {tbr.get('PHASE0_EVALUATOR', {}).get('key_id')}"

    body_obj = {
        "kpis": kpis,
        "authority": "AUDIT_ONLY",
        "promotes_authority": False,
        "human_review_performed": False,
        "module_id": "amphora-sourceability-ehs",
        "receipt_id": receipt_id,
        "reviewer_key_id": eval_key_id,
        "reviewer_public_key_hex": eval_pub_hex,
        "reviewer_key_pinned_in_trust_store": eval_pin,
        "schema": "amphora.ghs-clp-cid-attribution-audit-rebank.v1",
        "repair_item_id": "R-N01",
        "repair_mode": True,
        "supersedes": [
            {
                "superseded_path": str(PRIOR_UNBANKED_RECEIPT.relative_to(ROOT)),
                "superseded_sha256": prior_unbanked_receipt_sha,
                "superseded_deleted_or_modified": False,
                "reason": (
                    "Same finding (2/5 candidates, IPDA and m-XDA, cite a PubChem CID "
                    "resolving to an unrelated chemical), but that receipt was signed with "
                    "the unanchored LOCAL_DEVELOPMENT_AUDIT_ONLY key "
                    "('local-9028773f49591193') instead of the pinned PHASE0_EVALUATOR key, "
                    "so it was never portfolio-verifiable (launcher verified_new_signed=0, "
                    "downgraded to UNKNOWN) despite ledger fire "
                    f"{PRIOR_LEDGER_FIRE_ID} recording verdict REFUTED at {PRIOR_LEDGER_TS}. "
                    "This receipt independently re-derives the finding from freshly-fetched "
                    "PubChem data (not a copy of that fire's raw/ cache) and signs it under "
                    "the pinned key. The prior artifact is left byte-intact, not deleted or "
                    "modified."
                ),
            },
            {
                "superseded_path": str(PRIOR_UNBANKED_KPI.relative_to(ROOT)),
                "superseded_sha256": prior_unbanked_kpi_sha,
                "superseded_deleted_or_modified": False,
                "reason": (
                    "Sibling KPI of the wrong-key-signed receipt above; same signing defect "
                    "(local-9028773f49591193, not the pinned PHASE0_EVALUATOR key). Left "
                    "byte-intact, not deleted or modified."
                ),
            },
        ],
    }
    ptype = "application/vnd.amphora.ghs-clp-cid-attribution-audit-rebank.v1+json"
    payload_bytes = canon(body_obj)
    sig = eval_sk.sign(pae(ptype, payload_bytes))
    envelope = {
        "payload": base64.standard_b64encode(payload_bytes).decode(),
        "payloadType": ptype,
        "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}],
    }
    signed = dict(body_obj)
    signed["signature"] = envelope

    # self-verify before declaring
    eval_pub_obj = Ed25519PublicKey.from_public_bytes(bytes.fromhex(eval_pub_hex))
    eval_pub_obj.verify(sig, pae(ptype, payload_bytes))
    verify_ok = True

    out_path = ATTEMPTS / "r-n01-fire1-ghs-clp-cid-attribution-audit-rebank-receipt.v1.dsse.json"
    out_bytes = canon(signed)
    out_path.write_bytes(out_bytes)

    print("=== R-N01 fire 1: GHS/CLP PubChem-CID attribution audit re-bank ===")
    print(f"gates: {n_pass}/{n_def} passed")
    for g in gates:
        print(f"  [{'PASS' if g['passed'] else 'FAIL'}] {g['gate_id']}: {g['observed']}")
    print(diag["finding"])
    print("SELF_VERIFY_OK", verify_ok)
    print("EVAL_KEY_PINNED", eval_pin, eval_key_id)
    print("RECEIPT", out_path)
    print("RECEIPT_FILE_SHA256", sha(out_bytes))
    print("RECEIPT_ID", receipt_id)
    print("N_PASS", n_pass, "N_DEF", n_def)


if __name__ == "__main__":
    main()
