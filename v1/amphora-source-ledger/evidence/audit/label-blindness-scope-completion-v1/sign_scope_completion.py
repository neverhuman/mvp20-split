#!/usr/bin/env python3
"""DSSE-Ed25519-sign the label-blindness-scope-completion receipt for
amphora-source-ledger. AUDIT_ONLY.

ROTATION-mode fire. Extends evidence/audit/citation-census-checker-label-blindness-v1
(2026-08-17, CLAIM_REFUTED), which tested only 2 of the 23 load-bearing facts.json
constants for the wrong-product-swap defect and explicitly left the other 21
untested ("may or may not be similarly exposed"). This fire completes that
census for the 4 highest-risk remaining entries (all sourced from the same
shared multi-product Evonik curing-agent guide document) and confirms the same
defect recurs identically in all 4.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-source-ledger"
CENSUS_WORK = MOD / "evidence/phase0/repairs/T14-CENSUS/work"
OUT_DIR = MOD / "evidence/audit/label-blindness-scope-completion-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

FACTS_PATH = MOD / "reference/mvp20/data/facts.json"
RECORDS_PATH = MOD / "reference/mvp20/data/source_records.json"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def sha_file(p):
    return sha(p.read_bytes())


def pae(t, body):
    return (
        b"DSSEv1 "
        + str(len(t)).encode()
        + b" "
        + t.encode()
        + b" "
        + str(len(body)).encode()
        + b" "
        + body
    )


def load_seed(p):
    raw = p.read_bytes().strip()
    if len(raw) == 64:
        try:
            return bytes.fromhex(raw.decode())
        except Exception:
            pass
    return raw[:32]


eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id")
rev_pin = rev_key_id == tbr.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id")
assert eval_pin, "evaluator key_id does not derive pinned trust store entry"

FACTS_SHA_PINNED = "0af2456a443692093fc4a89174e5cc87da86323108b14c3aa20cc3af159f06fb"
RECORDS_SHA_PINNED = "87174e555bdf31cd30d7d13da2dedb5cc6c14af33586fdd3981d97c0409da26c"
CHECKER_SHA_PINNED = "9f862d9686f4a17c3843001a41e8b52e8a03a125236b2c395bce5547b76759ac"
facts_sha = sha_file(FACTS_PATH)
records_sha = sha_file(RECORDS_PATH)
checker_sha = sha_file(CENSUS_WORK / "t14_census_checker.py")
assert facts_sha == FACTS_SHA_PINNED, f"facts.json drifted: {facts_sha}"
assert records_sha == RECORDS_SHA_PINNED, f"source_records.json drifted: {records_sha}"
assert checker_sha == CHECKER_SHA_PINNED, f"t14_census_checker.py drifted (not the same audited artifact): {checker_sha}"

diagnostic = json.loads((OUT_DIR / "diagnostic.canonical.json").read_text())
diagnostic_runB = json.loads((OUT_DIR / "diagnostic.runB.json").read_text())
assert diagnostic == diagnostic_runB, "two-replay byte-stability check failed on diagnostic content"
oracle_sha = sha_file(OUT_DIR / "scope_oracle.py")
diagnostic_sha = sha_file(OUT_DIR / "diagnostic.canonical.json")

prior_label_blindness_path = MOD / "evidence/audit/citation-census-checker-label-blindness-v1/citation-census-checker-label-blindness-receipt.v1.dsse.json"
prior_label_blindness_sha = sha_file(prior_label_blindness_path)
prior_census_path = MOD / "evidence/audit/full-loadbearing-citation-census-v1/full-loadbearing-citation-census-receipt.v1.dsse.json"
prior_census_sha = sha_file(prior_census_path)

assert diagnostic["refutation_confirmed"] is True, "refutation did not reproduce"
assert diagnostic["summary"]["original_checker_wrongly_validates_n"] == 4
assert diagnostic["summary"]["original_checker_correctly_validates_real_n"] == 4

FIRE_ID = "20260819T060001-352501-5cdfc6a1d4ac"

body_obj = {
    "schema": "amphora.source-ledger.audit.label-blindness-scope-completion.v1",
    "module": "amphora-source-ledger",
    "campaign_item_id": "",
    "mode": "ROTATION",
    "authority": "AUDIT_ONLY",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "fire_id": FIRE_ID,
    "claim_under_attack": {
        "claim_text": (
            "evidence/audit/citation-census-checker-label-blindness-v1 (2026-08-17, CLAIM_REFUTED) "
            "established that t14_census_checker.py cannot discriminate a true citation from a "
            "wrong-product citation sharing the same literal figure, but tested only 2 of the 23 "
            "load-bearing facts.json constants (resin.dgeba_331.density, hardener.ancamide_2353.density). "
            "Its own does_not_close list states: 'the other 9/11 newly-census'd entries were not tested "
            "for this defect class and may or may not be similarly exposed.' The full-loadbearing-"
            "citation-census-v1 receipt's 22/23 (95.7%) 'substantively supported' figure therefore still "
            "stands, unqualified, for those 21 untested entries -- this is the module's most recent "
            "unresolved scope gap and the strongest currently-standing unaudited claim."
        ),
        "prior_receipt_label_blindness": "amphora-source-ledger/evidence/audit/citation-census-checker-label-blindness-v1/citation-census-checker-label-blindness-receipt.v1.dsse.json",
        "prior_receipt_label_blindness_sha256": prior_label_blindness_sha,
        "prior_receipt_census": "amphora-source-ledger/evidence/audit/full-loadbearing-citation-census-v1/full-loadbearing-citation-census-receipt.v1.dsse.json",
        "prior_receipt_census_sha256": prior_census_sha,
    },
    "attack_type": "scope-completion: wrong-product-swap positive-control probe extended to all remaining load-bearing entries sourced from the same shared multi-product document",
    "objective": (
        "Identify every load-bearing facts.json entry (beyond the 2 already tested) whose citation "
        "is drawn from a document shared with an already-confirmed-vulnerable entry, and test each "
        "for the same wrong-product-swap defect using the byte-identical, unmodified check_entry() "
        "logic. Direct inspection of the T-14 and T14-CENSUS citation-sample findings identified 4 "
        "such untested entries, all sourced from the same Evonik 'Epoxy curing agents product guide "
        "(Americas)' PDF as the already-refuted hardener.ancamide_2353.density: "
        "hardener.ancamide_2353.ahew (WT/H=114), hardener.ancamide_260a.ahew (WT/H=120), "
        "hardener.ancamide_700b75.ahew (WT/H=170), and hardener.ancamide_260a.density (SG=0.960). "
        "As a scope-boundary control, 3 single-product-TDS entries from the same census "
        "(solvent.mak.density, solvent.mibk.density, solvent.n_butanol.density) were occurrence-"
        "counted to confirm the defect class requires a shared multi-product document to be "
        "exploitable at all."
    ),
    "refutation_criterion": (
        "Same criterion as the prior fire, applied to 4 new (key, expected_value, text_file) tuples: "
        "if the verbatim, unmodified check_entry() function reports verdict=supports for a tuple "
        "where the claimed product identity has been swapped to a DIFFERENT real product's row in "
        "the same shared document sharing the identical literal figure, that further confirms the "
        "checker cannot discriminate label-correct support and extends the already-REFUTED claim's "
        "confirmed scope."
    ),
    "corpus_scored": {
        "facts_path": "amphora-source-ledger/reference/mvp20/data/facts.json",
        "facts_sha256": facts_sha,
        "records_path": "amphora-source-ledger/reference/mvp20/data/source_records.json",
        "records_sha256": records_sha,
        "note": "Both hashes byte-identical to the pinned values all prior T-14/T14-CENSUS/W-T-SLEDGER/label-blindness receipts scored; no data file was modified by this fire.",
    },
    "checker_under_attack": {
        "path": "amphora-source-ledger/evidence/phase0/repairs/T14-CENSUS/work/t14_census_checker.py",
        "sha256": checker_sha,
        "note": "unmodified -- byte-identical to the sha256 the prior label-blindness-v1 and full-loadbearing-citation-census-v1 receipts cite; check_entry() reproduced verbatim (not paraphrased) in this fire's oracle script.",
    },
    "method": (
        "1) Read the T-14 (12-entry) and T14-CENSUS (11-entry) citation-sample findings to identify "
        "which of the 21 not-yet-label-blindness-tested load-bearing entries are sourced from a "
        "document shared with an already-confirmed-vulnerable entry. Found 4: 3 more rows in the same "
        "Evonik curing-agent guide already implicated by hardener.ancamide_2353.density (2353.ahew, "
        "260a.ahew, 700b75.ahew), plus the previously-untested density column for 260a itself. "
        "2) Confirmed each asserted WT/{H}=AHEW or Specific-Gravity figure is genuinely duplicated by "
        "a distinct, real, adjacent product row by directly reading the extracted table text "
        "(table_row_confirmation in the diagnostic) -- not inferred from occurrence counts alone. "
        "3) Ran the verbatim original check_entry() against the 4 TRUE (key, expected_value, "
        "text_file) tuples -- all 4 verdict=supports (not disputed; matches how these entries would "
        "have scored had the census checker actually run them). "
        "4) Ran the verbatim original check_entry() against 4 WRONG-PRODUCT planted tuples -- same "
        "key and expected literal value, but the row now claimed to support it is a different, real, "
        "adjacent product from the same shared document (ANCAMIDE 2424 in place of 2353, 261A in "
        "place of 260A, 702-B-75 in place of 700-B-75, 260TN in place of 260A) -- the checker returned "
        "verdict=supports for all 4, identical to the true entries: it cannot discriminate them, "
        "extending the prior fire's finding from 2/23 to 6/23 confirmed-exposed load-bearing entries. "
        "5) Ran a stricter label-proximity re-implementation (60-char window) as a secondary probe: for "
        "the density entry (260a.density) it reproduced the prior fire's exact failure mode (validates "
        "both real and wrong-product identically). For the 3 AHEW entries it instead returned "
        "DOES_NOT_SUPPORT for BOTH real and wrong-product tuples -- the WT/{H} column sits further "
        "than 60 characters from the product-identifier text in this table's pdftotext layout, so the "
        "label-aware probe under-fires there rather than over-fires; this is a distinct, weaker "
        "failure mode from the density case and is reported precisely rather than folded into the "
        "'also insufficient' framing. 6) Occurrence-counted 3 single-product-TDS control entries "
        "(solvent.mak/mibk/n_butanol.density) to confirm the defect requires a shared multi-product "
        "document to be exploitable -- each control document names exactly one commercial product, "
        "so no wrong-product row exists there to swap in, bounding the finding's scope rather than "
        "implying every load-bearing entry is exposed."
    ),
    "table_row_confirmation": diagnostic["table_row_confirmation"],
    "occurrence_census_new_entries": diagnostic["occurrence_census_new_entries"],
    "occurrence_census_control_entries": diagnostic["occurrence_census_control_entries"],
    "original_checker_on_new_real_entries": diagnostic["original_checker_on_new_real_entries"],
    "original_checker_on_new_wrongproduct_planted_entries": diagnostic["original_checker_on_new_wrongproduct_planted_entries"],
    "label_aware_checker_on_new_real_entries": diagnostic["label_aware_checker_on_new_real_entries"],
    "label_aware_checker_on_new_wrongproduct_planted_entries": diagnostic["label_aware_checker_on_new_wrongproduct_planted_entries"],
    "original_checker_on_control_single_product_entries": diagnostic["original_checker_on_control_single_product_entries"],
    "summary": diagnostic["summary"],
    "two_replay_byte_stability": {
        "diagnostic_canonical_sha256": diagnostic_sha,
        "diagnostic_runB_matches_canonical": True,
        "oracle_script_path": "amphora-source-ledger/evidence/audit/label-blindness-scope-completion-v1/scope_oracle.py",
        "oracle_script_sha256": oracle_sha,
    },
    "claim_verdict": "CLAIM_REFUTED",
    "claim_verdict_reasoning": (
        "The prior label-blindness fire's finding is CONFIRMED TO EXTEND beyond the 2 entries it "
        "tested. All 4 newly-tested load-bearing entries drawn from the same shared multi-product "
        "Evonik curing-agent guide -- hardener.ancamide_2353.ahew, hardener.ancamide_260a.ahew, "
        "hardener.ancamide_700b75.ahew, and hardener.ancamide_260a.density -- exhibit the identical "
        "defect: the verbatim, unmodified check_entry() reports verdict=supports for a deliberately "
        "mis-attributed wrong-product citation exactly as readily as for the true citation, in all 4 "
        "cases (4/4), because its only predicate is bare substring presence and it never inspects "
        "product identity. Direct table-row inspection confirms this is not hypothetical: WT/H=114 is "
        "genuinely shared by ANCAMIDE 2353/2424/2767; WT/H=120 by 260A/261A/260TN; WT/H=170 by "
        "700-B-75/702-B-75; Specific Gravity=0.960 by 260A/260TN/375A -- all real, distinct products in "
        "the same table columns. Combined with the prior fire's 2 confirmed entries, this establishes "
        "6 of 23 (26.1%) load-bearing facts.json constants -- not 2 of 23 (8.7%) -- as confirmed-exposed "
        "to the mechanized-checker's product-identity blindness. This does NOT show any of these 6 "
        "facts.json values are actually wrong for their claimed products (all 4 new true attributions "
        "independently confirmed correct by table-row inspection in this fire's diagnostic); it further "
        "quantifies how much of the census's '22/23 substantively supported' framing rests on "
        "unreproducible human prose judgment rather than the cited mechanized artifact. The remaining "
        "17 of 23 entries (single-product TDS/product-page citations, per the citation_sample locators) "
        "were not individually re-tested by this fire, but the 3 spot-checked controls (solvent.mak/"
        "mibk/n_butanol.density) confirm the defect class structurally requires a shared multi-product "
        "document -- these single-product citations have no candidate wrong-product row to be confused "
        "with, bounding rather than closing the remaining scope gap."
    ),
    "does_not_close": [
        "No coating-efficacy, product-performance, batch-release, procurement, or freedom-to-operate authority.",
        "Does not dispute any facts.json numeric value; all 4 new (key, product) attributions independently confirmed correct by this fire's own table-row inspection.",
        "Does not repair or contradict T-14's still-standing REFUTED finding that the runtime's uncited_constants_rejected gate performs no resolve or support check at all -- orthogonal and unaffected.",
        "Does not modify facts.json, source_records.json, lib.rs, mission.md front-matter, t14_census_checker.py, or the master manifest.",
        "13 of the 23 load-bearing entries remain unaudited for this specific defect class (single-product-doc entries not individually swap-tested, only occurrence-spot-checked at n=3); the structural argument that single-product TDS citations cannot be exposed to a wrong-PRODUCT swap is sound, but was not exhaustively verified for every remaining entry.",
        "The label-aware (60-char window) secondary probe is not a validated fix candidate: it under-fires (false DOES_NOT_SUPPORT) on 3/4 of the new AHEW entries and over-fires (false supports, identical to original) on the 1 new density entry -- it is unreliable in both directions, not merely 'also insufficient' in the way the prior fire found for the 2 density-column cases.",
    ],
    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under evidence/audit/label-blindness-scope-completion-v1/",
        "derives_pinned_trust_store_key_id": bool(eval_pin),
    },
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER",
        "key_id": rev_key_id,
        "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin),
        "reviewer_signature_present": False,
    },
}

body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.source-ledger-label-blindness-scope-completion+json"
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
OUT_DIR.mkdir(parents=True, exist_ok=True)
out = OUT_DIR / "label-blindness-scope-completion-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

bytes1 = out.read_bytes()
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])),
)
bytes2 = json.dumps(receipt, indent=2, sort_keys=True).encode()
assert bytes1 == bytes2, "byte-stability replay mismatch"

print("WROTE", out)
print("claim_verdict", body_obj["claim_verdict"])
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified_and_byte_stable", True)
