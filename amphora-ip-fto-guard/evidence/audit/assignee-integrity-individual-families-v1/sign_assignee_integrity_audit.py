#!/usr/bin/env python3
"""DSSE-Ed25519-sign the ip-fto-guard assignee-integrity audit for the 10
individual-patent-family rows (n=27..36) of patent_landscape.json.

AUDIT_ONLY. Signs the byte-stable two-replay diagnostic plus a fail-closed
positive-control mutation demo with the on-host Phase-0 evaluator Ed25519
seed. Does not promote authority, does not modify the manifest, does not
modify patent_landscape.json.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
AUDIT_DIR = ROOT / "amphora-ip-fto-guard/evidence/audit/assignee-integrity-individual-families-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

FIRE_ID = "20260814T180001-765497-ba3f5d3d6be3"
FIXTURE = ROOT / "amphora-ip-fto-guard/reference/mvp20/data/patent_landscape.json"


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
canon = (AUDIT_DIR / "diagnostic.canonical.json").read_bytes()
runB = (AUDIT_DIR / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag = json.loads(canon)
harness_sha = sha((AUDIT_DIR / "run_assignee_integrity_audit.py").read_bytes())

assert diag["verdict"] == "REFUTED", "expected REFUTED verdict, refusing to sign otherwise"
assert diag["mismatch_ns"] == [29, 31, 34, 36], "unexpected mismatch set, refusing to sign"

# --- fail-closed positive-control mutation demo ------------------------------
fc_diag = json.loads((AUDIT_DIR / "diagnostic.fail_closed_demo.json").read_text())
fc_row30 = next(r for r in fc_diag["rows"] if r["n"] == 30)
real_row30 = next(r for r in diag["rows"] if r["n"] == 30)
positive_control = {
    "planted_defect": "family n=30 (US4865653A) assignee field mutated from "
                       "'Henkel Corporation' (a real, verified match) to "
                       "'Henkel Corporation / BASF SE' (an uncorroborated "
                       "extra-party compound label of the exact kind found "
                       "for real at family n=3 in the prior R-S03 audit), "
                       "in a copy of patent_landscape.json "
                       "(mutated_landscape_fail_closed_demo.json)",
    "how_planted": "reference/mvp20/data/patent_landscape.json family "
                   "n=30 field 'assignee': 'Henkel Corporation' -> "
                   "'Henkel Corporation / BASF SE' (fixture bytes on disk "
                   "left untouched; mutation applied only to an in-memory "
                   "copy written to mutated_landscape_fail_closed_demo.json)",
    "real_input_verdict_row_n30": real_row30["verdict"],
    "mutated_input_verdict_row_n30": fc_row30["verdict"],
    "detected": fc_row30["verdict"] == "mismatch" and real_row30["verdict"] == "match",
    "evidence": f"real: fixture_assignee={real_row30['fixture_assignee']!r} "
                f"live={real_row30['live_assignee_current']!r} -> "
                f"verdict={real_row30['verdict']!r}; "
                f"mutated: fixture_assignee={fc_row30['fixture_assignee']!r} "
                f"live={fc_row30['live_assignee_current']!r} -> "
                f"verdict={fc_row30['verdict']!r}",
    "mutated_diagnostic_sha256": sha((AUDIT_DIR / "diagnostic.fail_closed_demo.json").read_bytes()),
    "mutated_landscape_sha256": sha_file(AUDIT_DIR / "mutated_landscape_fail_closed_demo.json"),
    "note": "Demonstrates the exact-match-after-corporate-suffix-strip rule "
            "is not a substring-matching false-negative trap (an earlier "
            "iteration of this detector used substring matching in both "
            "directions and FAILED to catch this exact same planted "
            "compound-label defect -- 'henkel' being a substring of "
            "'henkelbasfse' -- before being tightened to exact equality; "
            "that failed iteration's diagnostic was discarded and never "
            "signed).",
}
assert positive_control["detected"], "positive control did not fire -- do not sign"

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
d = AUDIT_DIR / "raw/live"
for f in sorted(d.glob("*")):
    if f.is_file() and f.name != "SHA256SUMS.raw":
        raw_hashes[f"raw/live/{f.name}"] = sha_file(f)

fixture_bytes = FIXTURE.read_bytes()

# --- receipt body -----------------------------------------------------------
body_obj = {
    "schema": "amphora.ip-fto-guard.assignee-integrity-individual-families-audit-receipt.v1",
    "study_id": diag["study_id"],
    "authority": "AUDIT_ONLY",
    "run_type": "falsification_attack",
    "module": "amphora-ip-fto-guard",
    "campaign_item_id": "",
    "fire_id": FIRE_ID,
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_pinned_fixture": False,
    "claim_under_attack": diag["claim_under_attack"],
    "purpose": "ROTATION-mode ip-fto-guard falsification: attack the "
               "assignee-of-record accuracy of patent_landscape.json for "
               "the 10 individual-patent-family rows (n=27..36) that were "
               "left un-audited by both prior assignee/ownership work "
               "(R-S03, which covered only the 6 claim-charted families) "
               "and the CPC/IPC screen work (R-S02, which covered the 54 "
               "'assignee: multiple' category-screen rows) -- this is the "
               "strongest standing un-attacked claim identified this fire.",
    "non_circularity": "Adjudication is grounded in a source independent of "
                        "patent_landscape.json itself: a fresh live fetch "
                        "(this fire) of each row's own cited Google Patents "
                        "url, hash-pinned as raw evidence, with the "
                        "assignee value extracted mechanically by a fixed "
                        "regex over the bibliographic front-matter block "
                        "(bounded by the first '<h2>Links</h2>' marker, "
                        "which always precedes the Citations / Similar "
                        "Documents / Legal Events tables listing OTHER "
                        "documents' assignees), not by free-form reading.",
    "extraction_method": diag["extraction_method"],
    "audited_ns": diag["audited_ns"],
    "not_yet_audited_scope": "families n=1..5,26 (6 claim-charted, covered "
                              "by R-S03) and n=6..25,37..60 (54 category-"
                              "screen rows with assignee='multiple', "
                              "assignee-of-record not applicable/covered by "
                              "R-S02's CPC-level audit instead).",
    "fixture_sha256_observed": diag["fixture_sha256_observed"],
    "fixture_sha256_pinned_in_mission_and_manifest": diag["fixture_sha256_pinned_in_mission_and_manifest"],
    "fixture_sha256_matches_pin": diag["fixture_sha256_matches_pin"],
    "per_family_adjudication": diag["rows"],
    "counts": diag["counts"],
    "mismatch_ns": diag["mismatch_ns"],
    "corroborated_ns": diag["corroborated_ns"],
    "mismatch_detail": diag["mismatch_detail"],
    "ma_corroboration_for_n33": {
        "note": "n=33 (EP1865013B1) is excluded from the mismatch count: "
                "Air Products and Chemicals Inc's Performance Materials "
                "Division (~40% epoxy-curing-agents by revenue) was sold "
                "to Evonik Industries AG, deal closed 2017-01-03, $3.8B. "
                "The fixture's 'Evonik Operations GmbH family' assignee is "
                "MORE current than Google Patents' own stale top-level "
                "bibliographic field ('Air Products and Chemicals Inc'), "
                "consistent with the aggregator-lag pattern already "
                "documented in the R-S03 receipt.",
        "sources": [
            "https://www.prnewswire.com/news-releases/air-products-completes-38-billion-performance-materials-division-sale-to-evonik-300384611.html",
            "https://cen.acs.org/articles/94/i20/Evonik-acquire-Air-Productsspecialties.html",
        ],
    },
    "headline": diag["headline"],
    "verdict": diag["verdict"],
    "positive_control": positive_control,
    "proposed_followups": [
        {
            "module": "amphora-ip-fto-guard",
            "defect": "patent_landscape.json family n=29 (WO2018010615A1) "
                      "'assignee' field reads 'Elementis Specialties, "
                      "Inc.', which is not this patent's own bibliographic "
                      "assignee ('Deuchem Shanghai Chemical Co Ltd') but "
                      "IS the assignee of a different, merely-cited patent "
                      "(EP1162242A1) appearing in the same page's Citations "
                      "table -- symptomatic of a table-selection extraction "
                      "bug during fixture construction, not a typo.",
            "proposed_done_criterion": "Correct family n=29's 'assignee' "
                      "field to 'Deuchem Shanghai Chemical Co Ltd' (or "
                      "replace the row entirely with the evidently-intended "
                      "EP1162242A1 record if that was the original source "
                      "of the claim1_gist/key_elements content -- counsel "
                      "must determine which), via a superseding patch, "
                      "signed and cross-referenced in RETRACTION-INDEX.md.",
        },
        {
            "module": "amphora-ip-fto-guard",
            "defect": "patent_landscape.json family n=31 (US3178319A) "
                      "'assignee' field reads 'Monsanto Company'; the "
                      "patent's own bibliographic assignee (current and "
                      "original) is 'GERALDINE D HENRICKS', an individual, "
                      "with no Monsanto entity in the record at all.",
            "proposed_done_criterion": "Correct family n=31's 'assignee' "
                      "field to 'Geraldine D Henricks' via a superseding "
                      "patch, signed and cross-referenced in "
                      "RETRACTION-INDEX.md.",
        },
        {
            "module": "amphora-ip-fto-guard",
            "defect": "patent_landscape.json family n=34 (US6391464B1) "
                      "'assignee' field reads 'International Paint LLC "
                      "family'; the patent's own bibliographic assignee "
                      "(current and original) is 'General Electric Co', a "
                      "GE/silicone-materials lineage with no International "
                      "Paint entity in either field, despite the title "
                      "('Epoxy coatings and surfaces coated therewith') "
                      "plausibly reading as International Paint's domain.",
            "proposed_done_criterion": "Correct family n=34's 'assignee' "
                      "field to 'General Electric Co' via a superseding "
                      "patch, signed and cross-referenced in "
                      "RETRACTION-INDEX.md; counsel should separately "
                      "check whether a genuine International Paint tie-"
                      "coat patent was the intended row and file it "
                      "instead if so.",
        },
        {
            "module": "amphora-ip-fto-guard",
            "defect": "patent_landscape.json family n=36 (US2986539A) "
                      "'assignee' field reads 'General Mills Inc.'; the "
                      "patent's own bibliographic assignee is 'American Can "
                      "Co' (original) / 'Primerica Inc' (current), with no "
                      "General Mills connection, despite family n=35 "
                      "(US2705223A) genuinely and correctly being a General "
                      "Mills Inc. patent.",
            "proposed_done_criterion": "Correct family n=36's 'assignee' "
                      "field to 'American Can Co (orig.) / Primerica Inc "
                      "(current, per Google Patents bibliographic data; "
                      "expired 1978, ownership currency not material to "
                      "FTO screening but material to bibliographic "
                      "accuracy)' via a superseding patch, signed and "
                      "cross-referenced in RETRACTION-INDEX.md.",
        },
        {
            "module": "amphora-ip-fto-guard",
            "defect": "Family n=28 (WO2014093115A2) 'assignee' field "
                      "reads 'Dow Global Technologies LLC' only; the "
                      "patent's own bibliographic data lists a co-assignee, "
                      "'Rohm and Haas Co', that the fixture omits. Not "
                      "counted as a mismatch (the named assignee IS a real "
                      "current assignee) but flagged as an incompleteness "
                      "gap of the same general class.",
            "proposed_done_criterion": "Amend family n=28's 'assignee' "
                      "field to 'Dow Global Technologies LLC / Rohm and "
                      "Haas Co' via a superseding patch, or file counsel "
                      "note that the omission is immaterial to the FTO "
                      "technical screen.",
        },
    ],
    "does_not_close": [
        "Does not verify legal status, prosecution history, claim scope, "
        "jurisdictions, or dependents of any family -- assignee-of-record "
        "field accuracy only.",
        "Does not modify patent_landscape.json; all 4 misattribution "
        "findings are filed as proposed_followups, not repaired in this "
        "fire (per REPAIR MODE discipline: audits under evidence/audit/ "
        "file findings, repairs under evidence/phase0/repairs/<item>/ "
        "apply superseding patches once a campaign item exists).",
        "Google Patents' own disclaimer applies to all live data used "
        "here ('the listed assignees may be inaccurate... makes no "
        "representation or warranty as to the accuracy of the list'); "
        "the 4 mismatches found are not disclaimer-explainable drift -- "
        "each fixture value names an entity with ZERO textual or "
        "corporate-lineage relationship to the patent's own bibliographic "
        "record, as distinct from n=33's genuine stale-aggregator case.",
        "The exact-match-after-corporate-suffix-normalization rule may "
        "still under-detect a genuinely wrong single-token assignee that "
        "happens to normalize identically to the real one (e.g. two "
        "different real companies that both reduce to the same stripped "
        "token); the positive control proves it catches compound-label "
        "and wrong-company-name defects, not every conceivable defect "
        "class.",
        "families n=1..5,26 and n=6..25,37..60 remain outside this "
        "audit's scope (see not_yet_audited_scope); n=1..5,26 already "
        "carry their own R-S03 assignee audit (which itself found a "
        "misattribution at n=3, still an open proposed_followup there).",
    ],
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": sha(canon),
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "harness_sha256": harness_sha,
        "raw_evidence_sha256": raw_hashes,
        "fixture_sha256": sha(fixture_bytes),
    },
    "repair_status": "not_applicable_audit_only",
    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY falsification receipt under "
                    "evidence/audit/assignee-integrity-individual-families-v1/",
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
ptype = "application/vnd.amphora.ip-fto-guard-assignee-integrity-individual-families-audit+json"
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

out = AUDIT_DIR / "assignee-integrity-individual-families-receipt.v1.dsse.json"
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
