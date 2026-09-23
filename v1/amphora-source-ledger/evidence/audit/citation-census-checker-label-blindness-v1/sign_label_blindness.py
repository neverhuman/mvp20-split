#!/usr/bin/env python3
"""DSSE-Ed25519-sign the citation-census-checker-label-blindness receipt for
amphora-source-ledger. AUDIT_ONLY.

ROTATION-mode fire. Attacks the strongest currently-standing claim in this
module: evidence/audit/full-loadbearing-citation-census-v1's assertion that a
"mechanized checker (t14_census_checker.py)" verified label-correct,
product-specific support for the 11 previously-unsampled load-bearing
citations, and its claim_verdict_reasoning that 9/11 were verified "by exact
literal string match at a recognizable property label."
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
OUT_DIR = MOD / "evidence/audit/citation-census-checker-label-blindness-v1"
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
oracle_sha = sha_file(OUT_DIR / "label_blindness_oracle.py")
diagnostic_sha = sha_file(OUT_DIR / "diagnostic.canonical.json")

prior_receipt_path = MOD / "evidence/audit/full-loadbearing-citation-census-v1/full-loadbearing-citation-census-receipt.v1.dsse.json"
prior_receipt_sha = sha_file(prior_receipt_path)

assert diagnostic["refutation_confirmed"] is True, "refutation did not reproduce"
assert diagnostic["summary"]["original_checker_wrongly_validates_n"] == 2
assert diagnostic["summary"]["original_checker_correctly_validates_real_n"] == 2

body_obj = {
    "schema": "amphora.source-ledger.audit.citation-census-checker-label-blindness.v1",
    "module": "amphora-source-ledger",
    "campaign_item_id": "",
    "mode": "ROTATION",
    "authority": "AUDIT_ONLY",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "fire_id": "20260817T120001-2867018-f9b56fb31fee",
    "claim_under_attack": {
        "claim_text": (
            "evidence/audit/full-loadbearing-citation-census-v1's `method` field states 'A "
            "mechanized checker (t14_census_checker.py) then verified the exact asserted numeric "
            "string is present in each entry's extracted text'; its `claim_verdict_reasoning` "
            "states 9/11 of the newly-checked load-bearing citations were verified '9/11 by exact "
            "literal string match at a recognizable property label.' Read together, this is a claim "
            "that the cited MECHANIZED artifact establishes label-correct, product-specific "
            "citation support -- i.e. that the checker (not just a human curator's prose note) "
            "verifies the matched value belongs to the specific product named by the facts.json "
            "key, not merely that the value appears somewhere in a (possibly multi-product) "
            "document. This is currently the module's strongest standing, most recently-signed "
            "claim (2026-08-15) about citation support quality."
        ),
        "prior_receipt": "amphora-source-ledger/evidence/audit/full-loadbearing-citation-census-v1/full-loadbearing-citation-census-receipt.v1.dsse.json",
        "prior_receipt_sha256": prior_receipt_sha,
    },
    "attack_type": "checker re-derivation + wrong-product-swap positive-control probe on the cited mechanized artifact",
    "objective": (
        "Independently re-derive what t14_census_checker.py's check_entry() function actually "
        "verifies (reproduced verbatim from the same checked-in, hash-pinned file the prior "
        "receipt cites, unmodified), and test whether it -- or a stricter label-proximity "
        "re-implementation -- can distinguish a genuine citation from a deliberately mis-attributed "
        "wrong-product citation that shares the same literal numeric figure in the same shared, "
        "multi-product source document. Two of the 11 newly-census'd entries are drawn from such "
        "shared documents: resin.dgeba_331.density's 'Specific Gravity, 25/25C = 1.16' figure "
        "recurs identically for 7 distinct Dow D.E.R. grades (317/330/331/332/337/364/383) in the "
        "same table column; hardener.ancamide_2353.density's 'Specific Gravity = 1.01' figure "
        "recurs identically for 10 distinct Evonik ANCAMINE/ANCAMIDE grades in the same table "
        "column."
    ),
    "refutation_criterion": (
        "If the verbatim, unmodified check_entry() function reports verdict=supports for a "
        "(key, expected_value, text_file) tuple where the claimed product identity has been "
        "deliberately swapped to a DIFFERENT, real product's row in the same shared document "
        "(same literal figure, different product) -- i.e. the checker cannot discriminate a "
        "true citation from a wrong-product citation sharing the same number -- that REFUTES the "
        "claim that the mechanized checker verifies label-correct, product-specific support."
    ),
    "corpus_scored": {
        "facts_path": "amphora-source-ledger/reference/mvp20/data/facts.json",
        "facts_sha256": facts_sha,
        "records_path": "amphora-source-ledger/reference/mvp20/data/source_records.json",
        "records_sha256": records_sha,
        "note": "Both hashes byte-identical to the pinned values the prior census/T-14/V1-REAL-SL/W-T-SLEDGER receipts scored; no data file was modified by this fire.",
    },
    "checker_under_attack": {
        "path": "amphora-source-ledger/evidence/phase0/repairs/T14-CENSUS/work/t14_census_checker.py",
        "sha256": checker_sha,
        "note": "unmodified -- byte-identical to the sha256 the prior full-loadbearing-citation-census-v1 receipt cites as `checker_script`; the check_entry() function's matching logic was reproduced verbatim (not paraphrased) in this fire's oracle script to guarantee no straw-man drift.",
    },
    "method": (
        "1) Verified check_entry()'s only matching predicate is `found = expected in text` -- a "
        "bare substring test; the `key` parameter (product identity) is never referenced by the "
        "matching logic (read directly from the checked-in source, hash-pinned above). "
        "2) Counted raw occurrences of each of the two ambiguous entries' asserted literal values "
        "in their cited source documents: '1.16' occurs 9x in the Dow D.E.R. resins PDF; '1.01' "
        "occurs 10x in the Evonik curing-agent guide PDF. "
        "3) Read the actual table headers surrounding each occurrence to confirm the matched "
        "column is genuinely 'Specific Gravity' (not a coincidental unrelated-property match, and "
        "not a mis-parsed artifact -- confirmed by a control row, D.E.R. 362, whose Specific "
        "Gravity genuinely differs at 1.14, proving the column is a real, varying, correctly-parsed "
        "field). 4) Ran the verbatim original checker against the TRUE (key, expected_value, "
        "text_file) tuples -- reproduces the prior receipt's finding, both entries verdict=supports "
        "(not disputed). 5) Ran the verbatim original checker against a WRONG-PRODUCT planted "
        "defect: kept the same key and expected literal value, but the row now claimed to support "
        "it is a different, real, adjacent product's row from the same shared document (D.E.R. 337 "
        "in place of D.E.R. 331; ANCAMINE(R) 2286 in place of ANCAMIDE(R) 2353) -- the checker "
        "returned verdict=supports for BOTH, identical to the true entries, because its logic "
        "cannot see product identity at all. 6) As a secondary probe, built and ran a stricter "
        "label-proximity re-implementation (value must occur within a 60-char window of the "
        "claimed product-identifier string) against the same real and wrong-product tuples -- this "
        "ALSO validated both wrong-product entries, because the wrong-product rows genuinely carry "
        "their own adjacent product label alongside the identical figure (this is not a checker "
        "bug fixable by tightening the window; it is a structural property of these near-duplicate "
        "product family tables, where several distinct real products share an identical Specific "
        "Gravity in the same column)."
    ),
    "table_header_confirmation": diagnostic["table_header_confirmation"],
    "occurrence_census": diagnostic["occurrence_census"],
    "original_checker_on_real_entries": diagnostic["original_checker_on_real_entries"],
    "original_checker_on_wrongproduct_planted_entries": diagnostic["original_checker_on_wrongproduct_planted_entries"],
    "label_aware_checker_on_real_entries": diagnostic["label_aware_checker_on_real_entries"],
    "label_aware_checker_on_wrongproduct_planted_entries": diagnostic["label_aware_checker_on_wrongproduct_planted_entries"],
    "two_replay_byte_stability": {
        "diagnostic_canonical_sha256": diagnostic_sha,
        "diagnostic_runB_matches_canonical": True,
        "oracle_script_path": "amphora-source-ledger/evidence/audit/citation-census-checker-label-blindness-v1/label_blindness_oracle.py",
        "oracle_script_sha256": oracle_sha,
    },
    "claim_verdict": "CLAIM_REFUTED",
    "claim_verdict_reasoning": (
        "The claim under attack -- that t14_census_checker.py, the mechanized artifact the prior "
        "receipt cites as verification, establishes label-correct product-specific support ('at a "
        "recognizable property label') -- is REFUTED. The checker's only predicate is bare "
        "substring presence; it never inspects the `key` (product identity) parameter it is given. "
        "For 2/11 of the newly-census'd load-bearing entries, this is not hypothetical: their cited "
        "source documents are multi-product comparison tables where 7 (D.E.R. resins) and 10 "
        "(Evonik curing agents) distinct real products share the exact literal Specific Gravity "
        "figure in the same column. Run verbatim and unmodified, the checker reports "
        "verdict=supports for a deliberately mis-attributed wrong-product citation exactly as "
        "readily as for the true citation -- it cannot tell them apart. A stricter label-proximity "
        "re-implementation, tested as a candidate fix, ALSO fails to discriminate here, because the "
        "wrong-product rows genuinely carry their own adjacent product label next to the identical "
        "figure; this is a structural property of the source corpus (near-duplicate-valued sibling "
        "products), not merely a patchable checker bug. Whatever product-label correctness the "
        "prior receipt's '9/11 ... at a recognizable property label' framing implies was "
        "established, it was established by unreproducible human judgment recorded only in prose "
        "`note` fields -- not by the mechanized checker cited as the receipt's verifying artifact. "
        "This does NOT show the underlying facts.json values (1.16, 1.01) are wrong for D.E.R. 331 "
        "or ANCAMIDE 2353 specifically -- both are independently confirmed correct by reading the "
        "true table rows in this fire's own diagnostic (label_aware_checker_on_real_entries) -- it "
        "shows the mechanized-verification claim for this document class is overstated."
    ),
    "does_not_close": [
        "No coating-efficacy, product-performance, batch-release, procurement, or freedom-to-operate authority.",
        "Does not dispute any facts.json numeric value; both real (key, product) attributions independently confirmed correct by this fire's own diagnostic.",
        "Does not repair or contradict T-14's still-standing REFUTED finding that the runtime's uncited_constants_rejected gate performs no resolve or support check at all -- that root cause is orthogonal to and unaffected by this finding.",
        "Does not modify facts.json, source_records.json, lib.rs, mission.md front-matter, t14_census_checker.py, or the master manifest.",
        "Limited to the 2/11 entries where the cited source is a genuine multi-product comparison table with a shared literal figure; the other 9/11 newly-census'd entries were not tested for this defect class and may or may not be similarly exposed.",
    ],
    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under evidence/audit/citation-census-checker-label-blindness-v1/",
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
ptype = "application/vnd.amphora.source-ledger-citation-census-checker-label-blindness+json"
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
out = OUT_DIR / "citation-census-checker-label-blindness-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

# self-verify -- replay twice for byte-stability
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
