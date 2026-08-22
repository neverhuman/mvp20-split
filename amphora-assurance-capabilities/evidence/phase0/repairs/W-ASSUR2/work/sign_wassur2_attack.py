#!/usr/bin/env python3
"""DSSE-Ed25519-sign the W-ASSUR2 attack receipt for
amphora-assurance-capabilities. Attacks W-ASSUR1's SURVIVED claim ("The
NFKD-based confusable detector catches novel encodings without rejecting
legitimate keys") across 5 confusable families beyond the 13 known probes,
plus a legitimate-key false-positive control set. Construction replicates
amphora-assurance-capabilities/evidence/phase0/repairs/W-ASSUR1/work/
sign_wassur1_repair.py: pae(), load_seed(), payloadType, envelope fields,
trust-store key-id derivation, post-write signature verification.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-assurance-capabilities"
REPAIR = MOD / "evidence/phase0/repairs/W-ASSUR2"
WORK = REPAIR / "work"
DONE = REPAIR / "done"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

SUPERSEDED = MOD / "evidence/phase0/repairs/W-ASSUR1/done/repair-receipt.W-ASSUR1.v1.dsse.json"
SUPERSEDED_SHA = "186dbbe236e1b164caa4bf6f82768237a547b013f78cae2864d1fd851b7b857e"
LIB_RS = MOD / "src/lib.rs"
LIB_RS_SHA = "ae46b34766f092ddd332fa617a4348c3fda5e0c2b014f54a1662004c73ae7b5d"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha_file(p: Path) -> str:
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


assert sha_file(SUPERSEDED) == SUPERSEDED_SHA, "superseded W-ASSUR1 receipt drifted"
assert sha_file(LIB_RS) == LIB_RS_SHA, "lib.rs was NOT touched this fire (attack item, no repair expected)"

run1 = json.loads((WORK / "wassur2_attack.run1.output.json").read_bytes())
run1_sha = sha_file(WORK / "wassur2_attack.run1.output.json")
run2_sha = sha_file(WORK / "wassur2_attack.run2.output.json")
assert run1_sha == run2_sha, "two-replay differs -- not byte-stable"

records = {r["scenario_id"]: r for r in run1["records"]}

# ---- sanity: A8 known-good probe and clean negative still behave as before ----
assert records["control-clean-negative"]["detected"] is False
assert records["control-known-good-A8-cyrillic-dze"]["detected"] is True

FAMILIES = ["CG", "MA", "FW", "ZB", "CM"]
family_summary = {}
evading_encodings = []
for fam in FAMILIES:
    fam_records = [r for r in run1["records"] if r["family"] == fam]
    detected = sum(1 for r in fam_records if r["detected"])
    evaded = sum(1 for r in fam_records if r["evaded"])
    family_summary[fam] = {
        "probed": len(fam_records),
        "detected": detected,
        "evaded": evaded,
        "scenario_ids": [r["scenario_id"] for r in fam_records],
    }
    for r in fam_records:
        if r["evaded"]:
            evading_encodings.append({
                "scenario_id": r["scenario_id"],
                "family": fam,
                "boolean_counsel_assertion_ignored": r["boolean_counsel_assertion_ignored"],
            })

assert family_summary["CG"]["evaded"] == 4, "expected exactly 4 CG evasions"
assert sum(family_summary[f]["evaded"] for f in ["MA", "FW", "ZB", "CM"]) == 0, \
    "expected 0 evasions outside the CG family"
# baseline sanity: uncorrupted equivalents of the evading CG probes ARE detected,
# proving the corruption itself (not mere absence of "fto"/"counsel" substrings)
# causes the evasion
cg_baseline = [r for r in run1["records"] if r["family"] == "CG-baseline"]
assert len(cg_baseline) == 2 and all(r["detected"] for r in cg_baseline), \
    "CG baselines (uncorrupted) must be detected to prove corruption causes the evasion"

FP_records = [r for r in run1["records"] if r["family"] == "FP"]
assert len(FP_records) >= 10, "need >=10 legitimate control keys"
false_positives = [r for r in FP_records if r["false_positive"]]
assert len(false_positives) == 2, "expected exactly 2 false positives in this control set"

cargo_crate_log = (WORK / "wassur2_cargo_test_crate_output.txt").read_text()
cargo_workspace_log = (WORK / "wassur2_cargo_test_workspace_output.txt").read_text()
assert "test result: FAILED" not in cargo_crate_log, "crate cargo test has a FAILED target"
assert "test result: FAILED" not in cargo_workspace_log, "workspace cargo test has a FAILED target"
assert cargo_crate_log.count("test result: ok") >= 1
assert cargo_workspace_log.count("test result: ok") >= 1

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
rev_pin = (rev_key_id == tbr.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))

body_obj = {
    "schema": "amphora.assurance-capabilities.attack-w-assur2-receipt.v1",
    "receipt_id": "attack-W-ASSUR2-v1",
    "campaign_item_id": "W-ASSUR2",
    "module_id": "amphora-assurance-capabilities",
    "attacks_claim": (
        "W-ASSUR1 SURVIVED claim: 'The NFKD-based confusable detector catches "
        "novel encodings without rejecting legitimate keys.'"
    ),
    "attacked_receipt": {
        "path": "amphora-assurance-capabilities/evidence/phase0/repairs/W-ASSUR1/done/repair-receipt.W-ASSUR1.v1.dsse.json",
        "sha256": SUPERSEDED_SHA,
    },
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "EVIDENCE_ONLY",
    "phase": "PRE_PHASE_0",
    "date": "2026-08-09",
    "generated_on_host": "xbabe2",
    "modifies_existing_receipts": False,
    "modifies_manifest": False,
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "mission_prose_touched": False,
    "trust_anchored_in_phase0_store": True,
    "lib_rs_touched_this_fire": False,
    "lib_rs_sha256": LIB_RS_SHA,
    "verdict": "CLAIM_REFUTED",
    "supersedes": [
        {
            "superseded_path": "amphora-assurance-capabilities/evidence/phase0/repairs/W-ASSUR1/done/repair-receipt.W-ASSUR1.v1.dsse.json",
            "superseded_sha256": SUPERSEDED_SHA,
            "superseded_deleted_or_modified": False,
            "reason": (
                "W-ASSUR1's repair (normalized_key_skeleton: NFKC -> NFKD) fixed "
                "the specific precomposed-diacritic-drop bug V-B01 found and "
                "SURVIVED re-attack on the then-known 13 probes (A1..A8 + V1..V5). "
                "This item (W-ASSUR2) attacks the stronger, more general claim "
                "that the repair 'catches novel encodings without rejecting "
                "legitimate keys' -- i.e. that it generalizes beyond the known "
                "13 and does not over-match. It does not: 4 novel Cyrillic/Greek "
                "confusable-letter substitutions (a family the SURVIVED claim "
                "was never actually tested against -- fold_confusable's table "
                "covers only a hand-picked whitelist, and NFKD does nothing for "
                "unmapped homoglyphs since they have no canonical/compatibility "
                "decomposition) evade detection entirely, AND 2 of 13 legitimate "
                "control keys are wrongly flagged as counsel-signoff assertions. "
                "W-ASSUR1's SURVIVED verdict remains a true historical record of "
                "what it actually tested (13 known encodings); it is superseded "
                "here as an over-broad generalization, not erased."
            ),
        },
    ],
    "root_cause_evasion": (
        "fold_confusable() is a hand-picked whitelist of a subset of Cyrillic "
        "and Greek homoglyphs (only a,c,d,e,i,j,o,p,s,y,x,w cyrillic and "
        "a,e,i,k,v,o,p,t,u greek). Any OTHER real Unicode confusable letter -- "
        "e.g. U+03B7 GREEK SMALL LETTER ETA (eta, confusable for Latin 'n' per "
        "Unicode TR39 confusables.txt), U+0433 CYRILLIC SMALL LETTER GHE (ge, "
        "confusable for Latin 'r'), U+0442 CYRILLIC SMALL LETTER TE (te, "
        "confusable for Latin 't') -- has NO canonical or compatibility Unicode "
        "decomposition, so NFKD (the fix W-ASSUR1 landed) does nothing for it: "
        "it passes through fold_confusable() unchanged (not in the match arms), "
        "then fails the is_ascii_alphanumeric filter and is SILENTLY DROPPED "
        "from the skeleton rather than folded to its Latin lookalike. Dropping "
        "(rather than folding) a letter inside a required token (e.g. dropping "
        "the corrupted char from 'cleared', 'signed', 'attorney', 'attest') "
        "breaks that token's substring match, which can drop the semantic-token "
        "class count below the 2-of-3 threshold in key_asserts_counsel_signoff, "
        "causing a genuine counsel-signoff assertion to evade detection "
        "entirely. This is a materially different, broader defect class than "
        "the one V-B01/W-ASSUR1 found and fixed (precomposed-diacritic drop): "
        "it affects any confusable letter outside the hand-picked table, not "
        "just precomposed Latin-with-diacritic forms."
    ),
    "root_cause_false_positive": (
        "key_asserts_counsel_signoff's 2-of-3 semantic-token-class heuristic "
        "(counsel_party={counsel,attorney,lawyer}, fto={fto,freedomtooperate}, "
        "sign_off={sign,clear,approv,grant,confirm,attest}) matches on bare "
        "substring containment with no word-boundary or semantic-relationship "
        "check between the matched tokens. A legitimate metadata key that "
        "happens to contain words from two different classes -- without "
        "asserting an actual counsel sign-off -- is flagged identically to a "
        "genuine assertion. Confirmed on two ordinary formulation-candidate "
        "metadata field names: 'counsel_review_confirmation_id' (an ID "
        "reference field, matches counsel_party via 'counsel' + sign_off via "
        "'confirm') and 'attorney_confirmed_meeting_time' (a calendar-metadata "
        "field, matches counsel_party via 'attorney' + sign_off via "
        "'confirm')."
    ),
    "families_probed": family_summary,
    "families_probed_count": len(FAMILIES),
    "evading_encodings": evading_encodings,
    "evading_encodings_detail": {
        "CG1-eta-for-n-in-signed": {
            "key": "counsel_sig\\u03B7ed_off (Greek eta U+03B7 replacing 'n' in 'signed')",
            "intended_meaning": "signed off by counsel",
            "why_it_evades": (
                "eta is dropped (not in fold_confusable table, no decomposition), "
                "leaving skeleton 'counselsigedoff': contains 'counsel' "
                "(counsel_party=true) but NOT 'sign' (sign_off=false, since "
                "'siged' is missing the 'n'), NOT 'fto' (fto=false) -> only 1 "
                "class -> below the 2-of-3 threshold -> undetected."
            ),
        },
        "CG2-ghe-for-r-in-cleared-with-fto": {
            "key": "fto_clea\\u0433ed (Cyrillic ghe U+0433 replacing 'r' in 'cleared')",
            "intended_meaning": "FTO cleared",
            "why_it_evades": (
                "ghe dropped, skeleton 'ftocleaed': contains 'fto' (fto=true) "
                "but NOT 'clear' (sign_off=false, 'cleaed' missing the 'r'), "
                "NOT counsel_party -> only 1 class -> undetected. Uncorrupted "
                "baseline 'fto_cleared' (CG-baseline-fto-cleared-uncorrupted) "
                "IS detected (fto+clear=2 classes), proving the corruption "
                "itself causes the evasion, not mere absence of the words."
            ),
        },
        "CG3-ghe-for-r-in-attorney-with-fto": {
            "key": "atto\\u0433ney_fto (Cyrillic ghe U+0433 replacing 'r' in 'attorney')",
            "intended_meaning": "attorney-cleared FTO",
            "why_it_evades": (
                "ghe dropped, skeleton 'attoneyfto': does NOT contain 'attorney' "
                "(missing 'r', 'attoney'), 'counsel', or 'lawyer' -> "
                "counsel_party=false; contains 'fto' -> fto=true; sign_off=false "
                "-> only 1 class -> undetected. Uncorrupted baseline "
                "'attorney_fto' IS detected (counsel_party+fto=2 classes)."
            ),
        },
        "CG4-te-for-t-in-attest-with-counsel": {
            "key": "counsel_a\\u0442\\u0442est (Cyrillic te U+0442 x2 replacing both 't's in 'attest')",
            "intended_meaning": "attested by counsel",
            "why_it_evades": (
                "both te's dropped, skeleton 'counselaes': contains 'counsel' "
                "(counsel_party=true) but 'aes' matches none of "
                "sign/clear/approv/grant/confirm/attest (sign_off=false); "
                "fto=false -> only 1 class -> undetected."
            ),
        },
    },
    "false_positive_control_set": {
        "total_legitimate_keys_tested": len(FP_records),
        "false_positive_count": len(false_positives),
        "false_positive_scenario_ids": [r["scenario_id"] for r in false_positives],
        "false_positives_detail": [
            {
                "scenario_id": r["scenario_id"],
                "boolean_counsel_assertion_ignored": r["boolean_counsel_assertion_ignored"],
            }
            for r in false_positives
        ],
        "all_scenario_ids": [r["scenario_id"] for r in FP_records],
        "note": (
            "13 legitimate (non-attack) candidate-metadata keys were tested, "
            "including several containing genuine non-ASCII text (French "
            "accented supplier name, degree-sign viscosity unit, facade/micron "
            "with cedilla and mu, naive with diaeresis). 11/13 correctly did "
            "NOT trigger the counsel-signoff-assertion flag. 2/13 -- ordinary, "
            "unremarkable formulation-candidate metadata field names with no "
            "attack intent -- were wrongly flagged, because the 2-of-3 "
            "semantic-token-class heuristic has no requirement that the "
            "matched tokens be semantically related to each other, only that "
            "each SOME token from 2 of the 3 classes appears anywhere as a "
            "bare substring of the key."
        ),
    },
    "harness": {
        "description": (
            "Standalone cargo bin harness (path-dep only on amphora-core and "
            "amphora-assurance-capabilities, driving the real compiled "
            "AssuranceCapability::evaluate('amphora-ip-fto-guard') code path, "
            "not a re-implementation), same construction as V-B01/W-ASSUR1's "
            "harnesses. 30 scenarios: 2 sanity controls, 4 CG attack probes + "
            "2 CG uncorrupted baselines, 4 MA attack probes, 2 FW attack "
            "probes, 3 ZB attack probes, 2 CM attack probes, 13 FP legitimate-"
            "key control probes."
        ),
        "harness_source": "evidence/phase0/repairs/W-ASSUR2/work/ip_fto_probe_wassur2.main.rs",
        "harness_source_sha256": sha_file(WORK / "ip_fto_probe_wassur2.main.rs"),
        "cargo_toml": "evidence/phase0/repairs/W-ASSUR2/work/ip_fto_probe_wassur2.Cargo.toml",
        "cargo_toml_sha256": sha_file(WORK / "ip_fto_probe_wassur2.Cargo.toml"),
        "run1_output": "evidence/phase0/repairs/W-ASSUR2/work/wassur2_attack.run1.output.json",
        "run2_output": "evidence/phase0/repairs/W-ASSUR2/work/wassur2_attack.run2.output.json",
        "run1_sha256": run1_sha,
        "run2_sha256": run2_sha,
        "two_replay_byte_identical": run1_sha == run2_sha,
        "build_profile": "release",
        "deterministic_seed": 20260809,
    },
    "cargo_test": {
        "crate": {
            "command": "~/.cargo/bin/cargo test --offline --locked -p amphora-assurance-capabilities",
            "green": "test result: FAILED" not in cargo_crate_log,
            "log_path": "evidence/phase0/repairs/W-ASSUR2/work/wassur2_cargo_test_crate_output.txt",
            "ok_blocks": cargo_crate_log.count("test result: ok"),
        },
        "workspace": {
            "command": "~/.cargo/bin/cargo test --offline --locked --workspace",
            "green": "test result: FAILED" not in cargo_workspace_log,
            "log_path": "evidence/phase0/repairs/W-ASSUR2/work/wassur2_cargo_test_workspace_output.txt",
            "ok_blocks": cargo_workspace_log.count("test result: ok"),
        },
    },
    "repair_status": "not_yet_repaired",
    "recommended_followup": (
        "A future repair item should (a) replace the whitelist-based "
        "fold_confusable() with a generic Unicode confusables-table lookup "
        "(e.g. embed/derive from Unicode's published confusables.txt, or a "
        "skeleton-based algorithm per UTS #39 section 4) so unmapped "
        "homoglyphs fold to their Latin base instead of being silently "
        "dropped, and (b) add a word-boundary or token-adjacency requirement "
        "to key_asserts_counsel_signoff's 2-of-3 heuristic so unrelated "
        "substrings from ordinary metadata keys stop counting as a semantic "
        "class match."
    ),
    "reproducibility": {
        "payload_canonicalization": "json.dumps(sort_keys=True, separators=(',',':'))",
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "attack receipt under evidence/phase0/repairs/W-ASSUR2/done/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin),
    },
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER",
        "key_id": rev_key_id,
        "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin),
        "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed.",
    },
}

body1 = json.dumps(body_obj, sort_keys=True, separators=(",", ":")).encode()
body2 = json.dumps(body_obj, sort_keys=True, separators=(",", ":")).encode()
assert body1 == body2, "payload canonical serialization not byte-stable"
payload_sha = sha(body1)
body_obj["reproducibility"]["payload_two_replay_sha256"] = payload_sha
body = json.dumps(body_obj, sort_keys=True, separators=(",", ":")).encode()
body_check = json.dumps(body_obj, sort_keys=True, separators=(",", ":")).encode()
assert body == body_check, "final payload serialization not byte-stable"

ptype = "application/vnd.amphora.assurance-capabilities-attack-w-assur2+json"
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
DONE.mkdir(parents=True, exist_ok=True)
out = DONE / "attack-receipt.W-ASSUR2.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("payload_two_replay_sha256", sha(body))
print("receipt_sha256", sha(out.read_bytes()))
print("signature_verified", True)
print("families_probed", list(family_summary.keys()))
print("family_summary", json.dumps(family_summary))
print("false_positive_count", len(false_positives))
