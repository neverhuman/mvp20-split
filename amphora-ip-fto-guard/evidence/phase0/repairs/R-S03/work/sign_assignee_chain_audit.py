#!/usr/bin/env python3
"""DSSE-Ed25519-sign the ip-fto-guard assignee/ownership-chain integrity
audit receipt (campaign item R-S03).

AUDIT_ONLY. Signs the byte-stable two-replay diagnostic with the on-host
Phase-0 evaluator Ed25519 seed. Does not promote authority, does not modify
the manifest, does not modify patent_landscape.json (the fixture itself is
left untouched; the misattribution finding is filed as a proposed_followup
for a separate superseding-patch repair fire).
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-ip-fto-guard/evidence/phase0/repairs/R-S03/work"
DONE_DIR = ROOT / "amphora-ip-fto-guard/evidence/phase0/repairs/R-S03/done"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

FIRE_ID = "20260812T180001-2123863-491622607315"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def sha_file(p):
    return sha(Path(p).read_bytes())


def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" "
            + str(len(body)).encode() + b" " + body)


def load_seed(path):
    raw = path.read_bytes().strip()
    if len(raw) == 64:
        try:
            return bytes.fromhex(raw.decode())
        except Exception:
            pass
    return raw[:32]


# --- two-replay gate --------------------------------------------------------
canon = (BENCH / "diagnostic.canonical.json").read_bytes()
runB = (BENCH / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag = json.loads(canon)
harness_sha = sha((BENCH / "run_assignee_chain_audit.py").read_bytes())

# --- fail-closed mutation demo -----------------------------------------------
fc_diag = json.loads((BENCH / "diagnostic.fail_closed_demo.json").read_text())
fc_row2 = next(r for r in fc_diag["rows"] if r["n"] == 2)
real_row2 = next(r for r in diag["rows"] if r["n"] == 2)
fail_closed_mutation_demo = {
    "planted_defect": "family n=2 (EP3328938B1) assignee field mutated from "
                       "'Elementis Specialties Inc' to 'Elementis "
                       "Specialties Inc / BASF' in a copy of "
                       "patent_landscape.json (mutated_landscape_fail_closed_demo.json)",
    "real_input_chain_status_row_n2": real_row2["chain_status"],
    "mutated_input_chain_status_row_n2": fc_row2["chain_status"],
    "detector_fired_on_mutation": fc_row2["chain_status"] == "misattributed"
                                   and real_row2["chain_status"] != "misattributed",
    "mutated_input_rationale": fc_row2["rationale"],
    "mutated_diagnostic_sha256": sha((BENCH / "diagnostic.fail_closed_demo.json").read_bytes()),
    "mutated_landscape_sha256": sha_file(BENCH / "mutated_landscape_fail_closed_demo.json"),
    "note": "Demonstrates the detector's compound-label check is general "
            "(fires on an arbitrary planted extra-assignee token, not "
            "hardcoded to only the real Blue-Cube/Dow finding at row n=3).",
}
assert fail_closed_mutation_demo["detector_fired_on_mutation"], \
    "fail-closed mutation demo did not fire -- do not sign"

# --- derive public keys / key_ids from on-host seeds ------------------------
eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"

rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"

trust = json.loads(TRUST.read_text())
trust_by_role = {k.get("role"): k for k in trust["keys"]}
eval_derives_pin = (eval_key_id == trust_by_role.get("PHASE0_EVALUATOR", {}).get("key_id"))
rev_derives_pin = (rev_key_id == trust_by_role.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))

# --- hash-pin all raw evidence -----------------------------------------------
raw_hashes = {}
for sub in ("live", "registers", "corroboration"):
    d = BENCH / "raw" / sub
    for f in sorted(d.glob("*")):
        if f.is_file() and f.name != "SHA256SUMS.raw":
            raw_hashes[f"raw/{sub}/{f.name}"] = sha_file(f)

prior_snapshot_dir = ROOT / "amphora-ip-fto-guard/evidence/audit/claim-chart-provenance-v1"
prior_snapshot_shasums_sha256 = sha_file(prior_snapshot_dir / "SHA256SUMS.raw")

# --- receipt body -----------------------------------------------------------
body_obj = {
    "schema": "amphora.ip-fto-guard.assignee-ownership-chain-audit-receipt.v1",
    "study_id": diag["study_id"],
    "authority": "AUDIT_ONLY",
    "run_type": "falsification_attack",
    "module": "amphora-ip-fto-guard",
    "campaign_item_id": "R-S03",
    "fire_id": FIRE_ID,
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_pinned_fixture": False,
    "claim_under_attack": diag["claim_under_attack"],
    "purpose": "Verify assignee-of-record and ownership-chain currency for "
               "the 6 claim-charted patent_landscape.json families "
               "(independent_claim_chart.charted=true), the open gap named "
               "by the prior legal-status-term-severability receipt.",
    "non_circularity": "Adjudication is grounded in sources independent of "
                        "patent_landscape.json itself: a live re-fetch of "
                        "each family's own Google Patents biblio page "
                        "(hash-pinned, this fire), the prior independently "
                        "hash-pinned snapshot from claim-chart-provenance-v1 "
                        "(2026-08-03, drift-checked), and -- for the Blue "
                        "Cube IP LLC entity specifically -- two independent "
                        "corroborating public-record sources (Wikipedia's "
                        "Olin Corporation article and SEC EDGAR company "
                        "registrations for 'Blue Cube Spinco Inc.' and "
                        "'Olin Corporation') neither of which is authored "
                        "or controlled by this module or by Google Patents.",
    "charted_family_count": diag["charted_family_count"],
    "charted_ns": diag["charted_ns"],
    "register_attempts": diag["register_attempts"],
    "corroboration": diag["corroboration"],
    "per_family_adjudication": diag["rows"],
    "counts": diag["counts"],
    "refutation_evidence_family_n": diag["refutation_evidence_family_n"],
    "headline": (
        "5 of 6 claim-charted families' assignee-of-record is current per "
        "the best independently-reachable public source (Google Patents "
        "biblio, live-refetched and drift-checked against the 2026-08-03 "
        "in-tree snapshot; both EPO Register and USPTO PatentsView/"
        "assignment-search access were attempted and blocked -- see "
        "register_attempts). Family n=3's own assignee text ('Blue Cube IP "
        "/ Dow') is MISATTRIBUTED: it asserts a current Dow ownership tie "
        "for the entity 'Blue Cube IP LLC' that two independent public "
        "sources (Wikipedia + SEC EDGAR) contradict -- Blue Cube entities "
        "were transferred to Olin Corporation's control on 2015-10-05."
    ),
    "verdict": diag["verdict"],
    "fail_closed_mutation_demo": fail_closed_mutation_demo,
    "proposed_followups": [
        {
            "module": "amphora-ip-fto-guard",
            "defect": "patent_landscape.json family n=3 (EP2931822A2) "
                      "'assignee' field reads 'Blue Cube IP / Dow'. The "
                      "live Google Patents current-assignee for this "
                      "family is 'Blue Cube IP LLC' alone; independent "
                      "corroboration (Wikipedia Olin_Corporation article + "
                      "SEC EDGAR registered-address match between 'Blue "
                      "Cube Spinco Inc.' and 'Olin Corporation') shows Blue "
                      "Cube entities were transferred out of Dow's control "
                      "to Olin Corporation on 2015-10-05. The appended "
                      "'/ Dow' asserts a current ownership tie the public "
                      "record contradicts.",
            "proposed_done_criterion": "Correct family n=3's 'assignee' "
                      "field from 'Blue Cube IP / Dow' to 'Blue Cube IP "
                      "LLC' (optionally with a parenthetical historical "
                      "note that the invention was originally filed under "
                      "Dow Global Technologies LLC before the 2015-10-05 "
                      "Dow-to-Olin epoxy-business transfer), via a "
                      "superseding patch (never rewrite in place), signed "
                      "and cross-referenced in the module's "
                      "RETRACTION-INDEX.md, with a re-verification that no "
                      "other row shares the same "
                      "compound-assignee-with-uncorroborated-extra-party "
                      "pattern.",
        },
        {
            "module": "amphora-ip-fto-guard",
            "defect": "Families n=1 (WO2016187380A1, assignee 'Blue Cube "
                      "IP LLC') and n=4 (WO2013159277A1, assignee 'Dow "
                      "Global Technologies LLC') were adjudicated 'current' "
                      "at LOW confidence: both entities' patent estates "
                      "were touched by the 2015-10-05 Dow-to-Olin Global "
                      "Epoxy divestiture, and this audit could not reach "
                      "either primary assignment-of-record register (EPO "
                      "Register: blocked by Cloudflare bot-challenge, HTTP "
                      "403 on all 3 EP application-number lookups "
                      "attempted; USPTO PatentsView/assignment search: "
                      "legacy free API retired -- 301 redirect to a "
                      "client-side AWS-WAF-JS-challenge-gated portal, and "
                      "4 legacy assignment-search hostnames NXDOMAIN on "
                      "this network) to confirm no further un-recorded-at-"
                      "Google reassignment has since occurred.",
            "proposed_done_criterion": "From an environment with either (a) "
                      "a registered USPTO PatentsView/Patent-Assignment-"
                      "Search API key, or (b) browser-automation capable of "
                      "clearing the EPO Register's Cloudflare JS challenge, "
                      "pull the full assignment-recordal history (reel/"
                      "frame chain) for WO2016187380A1's US/EP family "
                      "members and WO2013159277A1's US/EP family members; "
                      "update chain_status to 'current' (confirmed) or "
                      "'stale' with the correct current owner named, "
                      "signed as a superseding patch to this receipt.",
        },
        {
            "module": "amphora-ip-fto-guard",
            "defect": "Families n=2 (Elementis Specialties Inc) and n=26 "
                      "(Hempel A/S) were adjudicated 'current' resting on "
                      "the Google Patents aggregator alone -- the module's "
                      "own disclaimer text notes Google 'has not performed "
                      "a legal analysis and makes no representation or "
                      "warranty as to the accuracy of the list.' EPO "
                      "Register access (the authoritative independent "
                      "register for both, since both are EP-numbered "
                      "families) was attempted and blocked by a Cloudflare "
                      "bot-challenge (HTTP 403).",
            "proposed_done_criterion": "From an environment that can clear "
                      "the EPO Register's Cloudflare JS challenge (e.g. a "
                      "licensed EPO Open Patent Services API key, or "
                      "browser automation), pull the 'Current proprietor' "
                      "and full procedural-steps transfer history for "
                      "EP3328938B1 (app EP16833614) and EP2653485A2 (app "
                      "EP13172326); confirm or correct chain_status with "
                      "primary-register evidence, signed as a superseding "
                      "patch to this receipt.",
        },
    ],
    "does_not_close": [
        "Does not verify legal status, prosecution history, claim scope, "
        "jurisdictions, or dependents of any family -- assignee-of-record "
        "chain integrity only.",
        "Does not modify patent_landscape.json; the n=3 misattribution "
        "finding is filed as a proposed_followup, not repaired in this "
        "fire.",
        "EPO Register and USPTO PatentsView/assignment-search were both "
        "attempted and blocked in this environment (see register_attempts); "
        "5 of 6 'current' calls rest on the Google Patents aggregator, "
        "which explicitly disclaims assignee accuracy, plus (for n=1/n=3 "
        "Blue Cube entities) independent Wikipedia/SEC EDGAR corroboration. "
        "None of the 6 current-status calls is a positive, register-"
        "confirmed currency proof; see proposed_followups for the primary-"
        "register access needed to close that gap.",
        "The fail-closed mutation demo proves the detector generalizes "
        "beyond the one real defect found (n=3); it does not prove the "
        "detector catches every possible misattribution pattern (e.g. a "
        "single-token assignee that is simply wrong, with no corroborating "
        "counter-source in this audit's fixed source set, would only be "
        "caught if it also fails the live-Google-Patents match).",
    ],
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": sha(canon),
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "harness_sha256": harness_sha,
        "raw_evidence_sha256": raw_hashes,
        "prior_snapshot_shasums_file_sha256": prior_snapshot_shasums_sha256,
    },
    "repair_status": "not_applicable_audit_only",
    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY campaign repair receipt under "
                    "evidence/phase0/repairs/R-S03/done/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_derives_pin),
    },
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER",
        "key_id": rev_key_id,
        "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_derives_pin),
        "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no "
                "independent human review performed.",
    },
}

body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.ip-fto-guard-assignee-ownership-chain-audit+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {
    "payload": base64.standard_b64encode(body).decode(),
    "payloadType": ptype,
    "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}],
}

receipt = {
    "evaluator_key_id": eval_key_id,
    "evaluator_public_key_hex": eval_pub_hex,
    "reviewer_public_key_hex": rev_pub_hex,
    "signature": envelope,
}

DONE_DIR.mkdir(parents=True, exist_ok=True)
out = DONE_DIR / "assignee-ownership-chain-audit.R-S03.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

# --- self-verify ------------------------------------------------------------
pk = Ed25519PublicKey.from_public_bytes(eval_pub)
pk.verify(base64.standard_b64decode(envelope["signatures"][0]["sig"]),
          pae(ptype, base64.standard_b64decode(envelope["payload"])))

print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_derives_pin)
print("reviewer_derives_pinned_trust_key", rev_derives_pin)
print("receipt_body_sha256", sha(body))
print("envelope_sha256", sha(out.read_bytes()))
print("verdict", body_obj["verdict"])
print("signature_verified", True)
