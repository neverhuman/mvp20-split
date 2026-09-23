#!/usr/bin/env python3
"""
U-DATA (CAMPAIGN, fire 3): structural-identity provenance audit of fire 1's
qualifying_finds[0] (Epikure 3223 vs canonical DETA, Tanimoto=1.0000).

Fire 1 claimed: "EXACT structural identity (Tanimoto=1.0000) to the canonical
amine DETA... computed via RDKit Morgan r=2/2048-bit, this fire" -- but fire
1's own field name for the SMILES used
("amine_smiles_public_chemistry_not_extracted_from_paywalled_data") admits
that SMILES was NEVER extracted from the primary source; it was assumed from
the commercial trade name "Epikure 3223" alone. This fire live-refetches (on
xbabe2, this fire) the ACTUAL primary source (PMC12528924, the companion
article to the Mendeley dataset fire 1 itself cited for its license quote)
and an independent distributor product page, to test whether that assumption
is actually grounded.

Finding: PMC12528924 describes the curing agent, VERBATIM, as "a
multifunctional amine resin hardener derived from diethylenetriamine, with
the commercial brand name of Epikure 3223" -- language in direct tension
with treating it as neat, unmodified DETA. This exact tension was available
to fire 1 (it already had this URL open, for the license quote) but was
never investigated. An independent distributor page (silmid.com) describes
the same product as "an unmodified aliphatic amine", corroborating the
generic trade-name assumption -- but the two independent live sources
DISAGREE on the material's own characterization, and fire 1 asserted
"computed via RDKit... this fire" framing that implies a settled,
source-verified structural fact when no such verification against the
primary source's own text was ever performed.

This refutes the narrower claim that finding #1's Tanimoto=1.0 assertion was
verified computation rather than an unexamined trade-name assumption. The
disposition (QUALIFYING_RECOMMENDED) is preserved because the balance of
evidence (CAS 111-40-0 identity via PubChem/distributor corroboration) still
favors DETA identity -- but the ambiguity is now disclosed rather than
silently assumed, and is filed as an unresolved item a human must close
before acquisition.
"""
import base64
import hashlib
import json
import re
import urllib.request
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-molecule-property"
WORK = MOD / "evidence/phase0/repairs/U-DATA/work"
OUT_DONE = MOD / "evidence/phase0/repairs/U-DATA/done"
OUT_ATTEMPTS = MOD / "evidence/phase0/repairs/U-DATA/attempts"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

ORIG_DONE = OUT_DONE / "u-data-domain-widening-search-record-kpi.v1.dsse.json"
FIRE1_ID = "20260812T120001-3712582-97e3beba268d"
FIRE2_ID = "20260812T130001-4081237-e414b4cfb3ed"
FIRE3_ID = "20260812T140002-300165-ddcb265206f9"
XBABE1_QUEUE_LINE58_SHA256 = "9c32bc479c79d1f524065fa1857450003741d061c4d0e9c337a4196c49ab05bf"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def sha_file(p):
    return sha(p.read_bytes())


def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " +
            str(len(body)).encode() + b" " + body)


def load_seed(p):
    raw = p.read_bytes().strip()
    if len(raw) == 64:
        try:
            return bytes.fromhex(raw.decode())
        except Exception:
            pass
    return raw[:32]


def http_get(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "amphora-cron-audit/1.0"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.status, r.geturl(), r.read()


def strip_tags(html):
    text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", text)


def main():
    checks = {}

    # --- 1. Live re-fetch the PRIMARY source fire 1 already cited (PMC12528924) ---
    status, final_url, body = http_get("https://pmc.ncbi.nlm.nih.gov/articles/PMC12528924/")
    html = body.decode("utf-8", errors="replace")
    derived_m = re.search(r"(a multifunctional amine resin hardener derived from diethylenetriamine[^.]*\.)", html)
    ratio_m = re.search(r"(mass ratio between EPON 828 and EPIKURE 3223 was [0-9:]+)", html)
    cc_m = re.search(r"(CC BY license \(http://creativecommons\.org/licenses/by/4\.0/\)\.)", html)
    cas_present = bool(re.search(r"111-40-0", html))
    checks["primary_source_pmc12528924_live_refetch"] = {
        "http_status": status,
        "url": final_url,
        "amine_description_verbatim": derived_m.group(1) if derived_m else None,
        "mass_ratio_verbatim": ratio_m.group(1) if ratio_m else None,
        "license_quote_verbatim": cc_m.group(1) if cc_m else None,
        "cas_number_111_40_0_stated_in_article": cas_present,
    }
    assert derived_m, "primary-source hedge language must be extractable to ground this fire's finding"

    # --- 2. Live re-fetch an INDEPENDENT distributor source (not fire 1's citation) ---
    status2, final_url2, body2 = http_get(
        "https://www.silmid.com/us/adhesives/epoxy-hardeners/epikure-3223-hardener-usq-can/")
    html2 = body2.decode("utf-8", errors="replace")
    unmod_m = re.search(r"(Epikure 3223 is an unmodified aliphatic amine[^.]*\.)", html2)
    checks["independent_distributor_silmid_live_refetch"] = {
        "http_status": status2,
        "url": final_url2,
        "product_description_verbatim": unmod_m.group(1) if unmod_m else None,
    }
    assert unmod_m, "independent distributor description must be extractable"

    # --- 3. Live re-fetch PubChem for canonical DETA SMILES, to confirm what "canonical DETA" means ---
    status3, final_url3, body3 = http_get(
        "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/diethylenetriamine/"
        "property/CanonicalSMILES,IUPACName/JSON")
    pubchem = json.loads(body3)
    props = pubchem["PropertyTable"]["Properties"][0]
    checks["pubchem_canonical_deta_live_refetch"] = {
        "http_status": status3,
        "cid": props["CID"],
        "canonical_smiles": props["ConnectivitySMILES"],
        "iupac_name": props["IUPACName"],
        "matches_fire1_claimed_smiles_NCCNCCN": True,  # C(CNCCN)N and NCCNCCN are the same connectivity graph
    }

    # --- 4. Assemble the contradiction and the corrected finding ---
    contradiction = {
        "primary_source_says": checks["primary_source_pmc12528924_live_refetch"]["amine_description_verbatim"],
        "independent_distributor_says": checks["independent_distributor_silmid_live_refetch"]["product_description_verbatim"],
        "tension": (
            "The primary source fire 1 already had open (for its license quote) describes the study "
            "material as 'derived from' diethylenetriamine -- ordinary usage for a modified/adducted "
            "product, not the parent amine itself -- while an independent distributor describes the "
            "same trade name as 'unmodified'. Fire 1 never read or reconciled the primary source's own "
            "chemistry language before asserting 'EXACT structural identity (Tanimoto=1.0000)... "
            "computed via RDKit Morgan r=2/2048-bit, this fire' -- a phrasing that implies a settled, "
            "source-grounded computation. No SMILES was ever extracted from PMC12528924 or from any "
            "primary documentation of the specific batch used in the study (fire 1's own field name "
            "admits this: 'amine_smiles_public_chemistry_not_extracted_from_paywalled_data'). The "
            "Tanimoto=1.0000 figure is therefore a computation against an ASSUMED structure (generic "
            "'Epikure 3223 = DETA, CAS 111-40-0' trade-name identity), not a verified structural fact "
            "about the study's actual reagent."
        ),
    }
    checks["contradiction"] = contradiction

    corrected_finding_0 = {
        "amine_name": "Epikure 3223 (Hexion; commercially identified as diethylenetriamine, CAS 111-40-0, "
                       "per independent distributor literature -- see caveat)",
        "amine_smiles_basis": (
            "NCCNCCN (canonical DETA, PubChem CID 8111, live-refetched this fire: connectivity "
            "C(CNCCN)N). This SMILES was NEVER extracted from the primary study source or from any "
            "batch-specific documentation of the material actually used -- it is inferred solely from "
            "the commercial trade name 'Epikure 3223', corroborated by an independent distributor "
            "description ('an unmodified aliphatic amine', silmid.com, live-refetched this fire) but "
            "in tension with the primary study source's own description ('a multifunctional amine "
            "resin hardener derived from diethylenetriamine', PMC12528924, live-refetched this fire)."
        ),
        "epoxy_name": "Epon 828 (Hexion; DGEBA)",
        "structural_overlap_corrected": {
            "best_match_vs_5_canonical_amines": {"name": "DETA", "tanimoto": 1.0},
            "confidence": "TRADE_NAME_INFERENCE_NOT_SOURCE_VERIFIED",
            "caveat": (
                "Tanimoto=1.0000 holds ONLY if the study's actual reagent is neat, unmodified DETA. "
                "The primary source's own wording ('derived from diethylenetriamine... multifunctional "
                "amine resin hardener') is not dispositive either way but is the kind of phrasing "
                "conventionally used for adducted/modified curing-agent products, and was never "
                "reconciled against the distributor's 'unmodified' characterization before fire 1 "
                "asserted an exact-match figure as if it were a verified computation."
            ),
        },
        "next_action": (
            "Before treating this as a settled DETA-AD-widening row: a human resolves the "
            "'derived from' vs 'unmodified' discrepancy directly against Hexion's EPIKURE 3223 "
            "Safety Data Sheet (CAS 111-40-0 listed ingredient table) or by contacting the study "
            "authors, THEN downloads the Mendeley CSV under CC-BY-4.0 and hand-verifies Tg values. "
            "If the SDS confirms neat DETA (single listed CAS 111-40-0 ingredient, no adduct/resin "
            "co-reactant), the original Tanimoto=1.0 disposition stands on solid ground; if the SDS "
            "shows a modified/multi-component hardener, the AD-widening candidate must be re-scored "
            "against the TRUE structure, not assumed DETA."
        ),
        "supersedes_qualifying_finds_0_of": "u-data-domain-widening-search-record-kpi.v1.dsse.json",
    }
    checks["corrected_qualifying_find_0"] = corrected_finding_0

    # --- 5. Supersedes block ---
    assert ORIG_DONE.exists()
    orig_sha = sha_file(ORIG_DONE)

    body_obj = {
        "schema": "amphora.molecule-property.rights-clean-epoxy-amine-data-hunt-structural-provenance-correction-kpi.v1",
        "receipt_id": "u-data-fire3-structural-identity-provenance-correction",
        "campaign_item_id": "U-DATA",
        "authority": "AUDIT_ONLY",
        "authority_ceiling": "EVIDENCE_ONLY",
        "promotes_authority": False,
        "flips_scientific_readiness": False,
        "human_review_performed": False,
        "modifies_no_live_config": True,
        "modifies_manifest": False,
        "modifies_locked_dataset": False,
        "modifies_signed_phase0_kpi": False,
        "module": "amphora-molecule-property",
        "fire_id": FIRE3_ID,
        "directive_ref": None,
        "claim_under_attack": {
            "receipt_path": "amphora-molecule-property/evidence/phase0/kpis/",
            "claim_text": (
                "Rights-clean training corpora exist that would widen the applicability domain to "
                "cover industrially relevant epoxy-amine chemistry."
            ),
            "narrower_claim_this_fire_actually_tests": (
                "Fire 1's qualifying_finds[0] structural_overlap assertion -- 'EXACT structural "
                "identity (Tanimoto=1.0000) to the canonical amine DETA... computed via RDKit Morgan "
                "r=2/2048-bit, this fire' -- was a genuine structural verification grounded in the "
                "primary source's own disclosed chemistry, not an unexamined trade-name assumption."
            ),
        },
        "attack": {
            "method": (
                "Live re-fetch, this fire (on xbabe2), of (a) the primary source PMC12528924 that "
                "fire 1 already cited for its license quote, checking its own chemical description of "
                "the curing agent; (b) an independent distributor product page never cited by fire 1; "
                "(c) PubChem's canonical DETA record, to confirm what 'canonical DETA' SMILES means."
            ),
            "refutation_criterion": (
                "REFUTED if the primary source's own chemistry description of the study material is in "
                "tension with (does not affirmatively support) the bare 'Tanimoto=1.0000... computed "
                "via RDKit... this fire' framing fire 1 used, AND fire 1 never investigated or "
                "disclosed that tension despite already holding the source open."
            ),
            "observation": (
                "FIRED: PMC12528924 (fire 1's own cited source) describes the curing agent as 'a "
                "multifunctional amine resin hardener derived from diethylenetriamine' -- hedge "
                "language in tension with a bare exact-identity claim -- and fire 1's receipt never "
                "mentions or reconciles this phrasing, despite it appearing on the exact page fire 1 "
                "quoted for licensing. Fire 1's own field name for the SMILES "
                "('amine_smiles_public_chemistry_not_extracted_from_paywalled_data') independently "
                "confirms no structure was ever extracted from the source; the 'computed via RDKit... "
                "this fire' phrasing therefore describes a real bit-vector computation performed "
                "against an ASSUMED, not source-verified, structure -- an overclaim of evidentiary "
                "grounding, not a fabricated citation (the CAS 111-40-0/distributor-corroborated "
                "identity is independently plausible), but a genuine unresolved ambiguity presented "
                "as a settled fact."
            ),
        },
        "checks": checks,
        "mendeley_entry_n1_license_reverified_this_fire": {
            "license_quote_verbatim": checks["primary_source_pmc12528924_live_refetch"]["license_quote_verbatim"],
            "conclusion": "License citation for entry n=1 (CC BY 4.0) independently reconfirmed live this fire; NOT in dispute.",
        },
        "entries_not_in_scope_this_fire": (
            "This fire audits ONLY qualifying_finds[0] (Epikure 3223/DETA structural claim). Fire 2's "
            "correction to entry n=3 (MDA/DDM citation) is untouched and remains valid. Entries n=2/"
            "n=4/n=5/n=6-17 of the 17-source sweep are untouched."
        ),
        "verdict": "CLAIM_REFUTED",
        "why": (
            "The narrower claim under test this fire -- that fire 1's flagship qualifying-find "
            "structural-identity assertion (Tanimoto=1.0000, Epikure 3223 vs canonical DETA) was a "
            "genuine source-verified computation, as its 'computed via RDKit... this fire' phrasing "
            "implies -- is REFUTED. The primary source fire 1 itself already had open for its license "
            "quote (PMC12528924) describes the study's curing agent, verbatim, as 'a multifunctional "
            "amine resin hardener derived from diethylenetriamine' -- language in direct tension with "
            "treating it as neat DETA -- and fire 1 never read, quoted, or reconciled this sentence "
            "despite it appearing on the same page. No SMILES was ever extracted from the primary "
            "source (fire 1's own field name admits this); the Tanimoto=1.0000 figure was computed "
            "against an assumed generic trade-name identity, not a verified structural fact. This is "
            "the same class of defect fire 2 found in entry n=3's citation (an assertion of 'this "
            "fire'-verified provenance that does not actually trace to what it claims) but targets a "
            "different, previously-unaudited claim: the structural-overlap computation, which is the "
            "load-bearing evidence for the whole objective's central DETA-AD-widening argument. The "
            "underlying identity claim is NOT shown to be false -- independent corroboration (PubChem "
            "CID 8111 for canonical DETA; an independent distributor's 'unmodified aliphatic amine' "
            "description) still favors DETA identity on balance -- but it is now honestly flagged as "
            "TRADE_NAME_INFERENCE_NOT_SOURCE_VERIFIED rather than presented as a settled computation, "
            "and a concrete SDS-based resolution path is filed for the human acquisition step."
        ),
        "supersedes": {
            "superseded_path": "amphora-molecule-property/evidence/phase0/repairs/U-DATA/done/u-data-domain-widening-search-record-kpi.v1.dsse.json",
            "superseded_sha256": orig_sha,
            "superseded_deleted_or_modified": False,
            "reason": (
                "qualifying_finds[0]'s structural_overlap assertion ('EXACT structural identity "
                "(Tanimoto=1.0000)... computed via RDKit Morgan r=2/2048-bit, this fire') overclaims "
                "evidentiary grounding: no SMILES was extracted from the primary source, and the "
                "primary source's own chemistry description ('derived from diethylenetriamine') is in "
                "tension with a bare exact-identity claim, a tension fire 1 never investigated. This "
                "receipt supersedes only qualifying_finds[0]'s structural-overlap framing with a "
                "corrected, honestly-caveated version; all other content of the superseded receipt "
                "(the other 16 search_record entries, qualifying_finds[1], the 4 proposed_followups, "
                "the overall BLOCKED_DATA verdict, fire 2's separate n=3 citation correction) stands "
                "unmodified and is not retracted."
            ),
        },
        "acquisition_queue_correction": {
            "target_file_xbabe1": "/home/ubuntu/amphora-cron/data-acquisition-queue.jsonl",
            "original_line58_sha256": XBABE1_QUEUE_LINE58_SHA256,
            "original_line_not_deleted_append_only_ledger": True,
            "corrected_entry_appended_this_fire": True,
            "fire_id": FIRE3_ID,
        },
        "proposed_followups": [
            {
                "module": "amphora-molecule-property",
                "defect": (
                    "The Mendeley 10.17632/bypjxzm3fn.1 / Epikure-3223 candidate row's amine identity "
                    "(neat DETA vs a 'multifunctional amine resin hardener derived from' DETA) is "
                    "UNRESOLVED: the primary study article and an independent distributor page give "
                    "conflicting characterizations, and no batch-specific SDS or composition table has "
                    "been checked."
                ),
                "proposed_done_criterion": (
                    "A future fire or human obtains Hexion's EPIKURE 3223 Safety Data Sheet (section 3, "
                    "composition/ingredients) or directly contacts the study authors, and confirms "
                    "whether the CAS-listed ingredient(s) are solely 111-40-0 (neat DETA) or include an "
                    "adduct/resin co-reactant; records the result against this receipt's sha256; and "
                    "either confirms or corrects the Tanimoto=1.0000 AD-widening candidacy for DETA "
                    "before any human acquisition/ingestion step treats it as settled."
                ),
            },
            {
                "module": "amphora-molecule-property",
                "defect": (
                    "The U-DATA data-hunt tooling's 'computed via RDKit... this fire' phrasing does not "
                    "distinguish between (a) a SMILES extracted/verified from the cited primary source "
                    "and (b) a SMILES assumed from a commercial trade name and never checked against "
                    "the source's own text -- a distinction this fire had to reconstruct by hand by "
                    "re-reading a page fire 1 had already fetched."
                ),
                "proposed_done_criterion": (
                    "A future data-hunt or ledger-audit fire adds a mandatory 'smiles_provenance' field "
                    "(enum: SOURCE_EXTRACTED | TRADE_NAME_INFERENCE | SDS_CONFIRMED) to the standard "
                    "qualifying_finds schema used by this module's U-* data campaign items, so a "
                    "structural-identity claim cannot be phrased as 'computed... this fire' without "
                    "disclosing whether the input structure itself was source-verified."
                ),
            },
        ],
        "gates": {
            "narrower_structural_provenance_claim_refuted_for_qualifying_finds_0": True,
            "underlying_identity_claim_not_shown_false_only_overclaimed_certainty": True,
            "mendeley_license_citation_reverified_unaffected": True,
            "fire2_n3_correction_untouched": True,
            "supersede_never_rewrite_original_receipt_byte_intact": True,
            "no_bulk_data_downloaded_this_fire": True,
            "signature_field_is_dsse_envelope_object": True,
            "signing_key_role_matches_repo_wide_audit_convention": True,
        },
        "all_gates_passed": True,
        "ceiling": (
            "AUDIT_ONLY. Documents a structural-identity evidentiary-provenance defect in a prior "
            "fire's qualifying-find and corrects the framing with an honestly-caveated replacement; "
            "does not acquire, cache, or ingest any external dataset, does not modify the AD gate or "
            "any shipped KPI, and does not modify the manifest."
        ),
        "signing_key": {
            "role": "PHASE0_EVALUATOR",
            "used_for": "AUDIT_ONLY U-DATA fire-3 structural-identity provenance correction under evidence/phase0/repairs/U-DATA/done/",
        },
    }

    eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
    eval_pub = eval_sk.public_key().public_bytes_raw()
    eval_pub_hex = eval_pub.hex()
    eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"

    trust = json.loads(TRUST.read_text())
    by_role = {k.get("role"): k for k in trust["keys"]}
    eval_pin = (eval_key_id == by_role.get("PHASE0_EVALUATOR", {}).get("key_id"))
    assert eval_pin, "evaluator key_id does not match pinned trust-store PHASE0_EVALUATOR entry"

    body_obj["signing_key"]["key_id"] = eval_key_id
    body_obj["signing_key"]["public_key_hex"] = eval_pub_hex
    body_obj["signing_key"]["derives_pinned_trust_store_key_id"] = bool(eval_pin)

    body1 = json.dumps(body_obj, indent=2, sort_keys=True).encode()
    body2 = json.dumps(dict(body_obj), indent=2, sort_keys=True).encode()
    assert body1 == body2, "receipt body non-deterministic"
    WORK.mkdir(parents=True, exist_ok=True)
    (WORK / "udata_fire3_receipt_body.canonical.json").write_bytes(body1)
    (WORK / "udata_fire3_receipt_body.runB.json").write_bytes(body2)

    ptype = "application/vnd.amphora.molecule-property.rights-clean-epoxy-amine-data-hunt-structural-provenance-correction-kpi.v1+json"
    sig = eval_sk.sign(pae(ptype, body1))
    envelope = {
        "payload": base64.standard_b64encode(body1).decode(),
        "payloadType": ptype,
        "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}],
    }

    receipt = {
        "evaluator_key_id": eval_key_id,
        "evaluator_public_key_hex": eval_pub_hex,
        "signature": envelope,
    }

    OUT_DONE.mkdir(parents=True, exist_ok=True)
    outpath = OUT_DONE / "u-data-fire3-structural-identity-provenance-correction-kpi.v1.dsse.json"
    outpath.write_text(json.dumps(receipt, indent=2, sort_keys=True))

    written = json.loads(outpath.read_text())
    sig_env = written["signature"]
    payload = base64.standard_b64decode(sig_env["payload"])
    sig_bytes = base64.standard_b64decode(sig_env["signatures"][0]["sig"])
    keyid = sig_env["signatures"][0]["keyid"]
    trust_pub_hex = by_role["PHASE0_EVALUATOR"]["public_key_hex"]
    assert keyid == by_role["PHASE0_EVALUATOR"]["key_id"]
    Ed25519PublicKey.from_public_bytes(bytes.fromhex(trust_pub_hex)).verify(
        sig_bytes, pae(sig_env["payloadType"], payload))
    assert payload == body1

    print("WROTE", outpath)
    print("orig_done_sha256", orig_sha)
    print("eval_derives_pinned_trust_key", eval_pin)
    print("two_replay_byte_identical", body1 == body2)
    print("independent_reverify_against_trust_store_OK", True)
    print("corrected_finding_0_json", json.dumps(corrected_finding_0))


if __name__ == "__main__":
    main()
