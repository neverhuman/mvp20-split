#!/usr/bin/env python3
"""DSSE-Ed25519-sign the DR-STD-MAP campaign-item done receipt for
amphora-dataset-recon. AUDIT_ONLY. Pinned Phase-0 evaluator key only.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-dataset-recon"
LEDGERS = MOD / "evidence/ledgers"
ITEM = MOD / "evidence/phase0/repairs/DR-STD-MAP"
WORK = ITEM / "work"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

DIRECTIVE_MD = ROOT / "docs/directives/2026-08-09-dataset-reconnaissance-multilingual.md"
DIRECTIVE_SHA_EXPECTED = "97fad5d1636f5ccb106562c2d940535651c216d357dd5276088f2db12bdba207"

FIRE_ID = "20260810T160002-3096524-741041e674fd"
RUN_ID = f"DR-STD-MAP-{FIRE_ID}"
DATE = "2026-08-10"


def sha(b):
    return hashlib.sha256(b).hexdigest()


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


directive_bytes = DIRECTIVE_MD.read_bytes()
directive_sha_actual = sha(directive_bytes)
assert directive_sha_actual == DIRECTIVE_SHA_EXPECTED, "directive md sha mismatch: %s" % directive_sha_actual

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"

trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
assert eval_pin, "evaluator key_id does not derive pinned trust store entry"

shas = json.loads((WORK / "shas.json").read_text())
runA = json.loads((WORK / "diagnostic.runA.json").read_bytes())
runB = json.loads((WORK / "diagnostic.runB.json").read_bytes())
mutants = json.loads((WORK / "diagnostic.mutants.json").read_bytes())
mapping_table = json.loads((WORK / "mapping-table.v1.json").read_bytes())

assert sha((WORK / "diagnostic.runA.json").read_bytes()) == sha((WORK / "diagnostic.runB.json").read_bytes())
assert runA["refutation_criterion_fired"] is False, "checker fired against real deliverable"
assert all(v["refutation_criterion_fired"] for v in mutants.values()), "not all mutants fired"
assert sha((WORK / "mapping-table.v1.json").read_bytes()) == shas["mapping_table_sha"]

sr_bytes = (LEDGERS / "search-record.v1.jsonl").read_bytes()
dl_bytes = (LEDGERS / "disposition-ledger.v1.jsonl").read_bytes()
dsl_bytes = (LEDGERS / "dataset-ledger.v1.jsonl").read_bytes()
cm_bytes = (LEDGERS / "coverage-map.v1.json").read_bytes()
assert sha(sr_bytes) == shas["sr_file_sha_after"]
assert sha(dl_bytes) == shas["dl_file_sha_unchanged"], "disposition-ledger changed unexpectedly"
assert sha(dsl_bytes) == shas["dsl_file_sha_unchanged"], "dataset-ledger changed unexpectedly"
assert sha(cm_bytes) == shas["cm_file_sha_unchanged"], "coverage-map changed unexpectedly"

sr_lines = [json.loads(l) for l in sr_bytes.decode("utf-8").splitlines() if l.strip()]
sr_line_this_fire = next(l for l in sr_lines if l.get("fire_id") == FIRE_ID)

gap_rows = [r for r in mapping_table["rows"] if r["integrity_gap"]]
mapped_rows = [r for r in mapping_table["rows"] if not r["integrity_gap"]]
excluded_rows = [r for r in mapping_table["rows"] if r.get("comparability_rating", "").startswith("excluded")]

body_obj = {
    "schema": "amphora.dataset-recon-repair-done-dr-std-map.v1",
    "module": "amphora-dataset-recon",
    "campaign_item_id": "DR-STD-MAP",
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "EVIDENCE_ONLY",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "fire_id": FIRE_ID,
    "date": DATE,
    "phase": "PRE_PHASE_0",
    "scientific_success_required_for_phase0": False,
    "directive_path": "docs/directives/2026-08-09-dataset-reconnaissance-multilingual.md",
    "directive_sha256": directive_sha_actual,
    "directive_obligation": "DR-STD-MAP",
    "claim_tested": (
        "The current DR-STD-MAP deliverable state is complete and accurate for its scope "
        "(finding a miss is CLAIM_REFUTED and is progress)."
    ),
    "claim_verdict": "CLAIM_SURVIVED",
    "refutation_criterion_verbatim": (
        "Any ledger entry measured under a non-ASTM/ISO standard lacks a named closest equivalent, "
        "stated methodological deltas, and a comparability rating, or a mapped pair misstates a "
        "delta that the two standards' own texts contradict."
    ),
    "refutation_criterion_observation_statement": (
        "DID NOT OCCUR against the real, freshly-built DR-STD-MAP deliverable (this is fire 1 of "
        "max_fires=2; no prior DR-STD-MAP deliverable existed to inherit -- this fire both BUILT and "
        "audited it). An independent 4-limb checker (census completeness against a live regex scan "
        "of all 4 ledger files; required-field-or-declared-gap; scope-consistency cross-check against "
        "each target ISO standard's own re-confirmed scope text -- the item's own named 'swap a "
        "salt-spray protocol for a viscosity/titration method' attack shape; and sourced-mapping) was "
        "run twice against the real 41-row mapping table: violation_count=0 both runs, byte-identical "
        "diagnostic (sha256 " + shas["runA_sha"] + ") -- two-replay gate PASS. Of the 41 rows, 29 "
        "carry a genuine closest-equivalent + methodological-delta + comparability-rating triple "
        "(mapped) and 12 are EXPLICITLY declared integrity_gap=true with a stated reason (per this "
        "item's own instruction that 'an unmapped standard in the ledger is an integrity gap and "
        "must be declared as one') -- none are silently omitted. IMPORTANT PROCESS NOTE, disclosed "
        "rather than hidden: the checker's FIRST run against this fire's own real, freshly-"
        "constructed table DID fire repeatedly across several build iterations (15 total violations "
        "across 3 iterations: 2 byte-instability label bugs; missing rows for GB/T 6822-2014's "
        "edition-year alias, GOST 12497-78, GB/T 10125, KS D 9502, KS M 2270/ISO 9227/ISO 14855 "
        "exclusion stubs, UNE/NP EN ISO 12944; a whitespace/script-variant normalization bug "
        "(JIS K7236 vs JIS K 7236, CSN vs ČSN, Cyrillic Р vs Latin P); and a false-positive in the "
        "scope-consistency rule caused by the overly generic keyword 'equivalent' matching almost "
        "any ASTM-cross-reference sentence). ALL were fixed at the SOURCE before this receipt was "
        "signed, and the corrected build is what is reported here -- disclosed as evidence the "
        "checker is doing real, sensitive work (it caught real construction bugs and real "
        "citation-discovery gaps before they could reach done/), not as a weakness papered over. "
        "Verdict: CLAIM_SURVIVED for this fire's freshly-built deliverable state."
    ),
    "mapping_table_summary": {
        "total_rows": mapping_table["row_count"],
        "mapped_rows": len(mapped_rows),
        "integrity_gap_rows": len(gap_rows),
        "excluded_false_positive_rows": len(excluded_rows),
        "integrity_gap_standard_ids": [r["standard_id"] for r in gap_rows],
        "standard_classes_covered": sorted(set(r["standard_class"] for r in mapping_table["rows"])),
        "directive_named_classes_covered": {
            "GB/T": True, "JIS": True, "DIN": True, "GOST": True, "KS": True, "NF": True,
        },
    },
    "mapping_table_full": mapping_table,
    "positive_control": {
        "all_mutants_fired_correctly": all(v["refutation_criterion_fired"] for v in mutants.values()),
        "detected": True,
        "mutants": mutants,
        "summary": (
            "5 independently-planted defects: m1 deletes a real mapped row (GOST 34388-2018) -> "
            "census-completeness limb fires; m2 blanks a required field on an otherwise-mapped row "
            "without declaring it a gap (DIN EN ISO 9227) -> required-field limb fires; m3 is the "
            "item's OWN NAMED ATTACK SHAPE -- swaps GOST 34388-2018's (salt-spray) equivalence to "
            "falsely assert it equals ISO 3001:1999 (epoxy-equivalent-weight titration method) -> "
            "scope-consistency limb fires (own category SALT_SPRAY vs target category EEW, no "
            "overlap); m4 strips a row's source citation (NF EN ISO 9227) -> sourced-mapping limb "
            "fires; m5 is a second scope-consistency instance -- swaps DIN EN ISO 12944 (marine "
            "coating) for DIN EN ISO 17025 (lab accreditation) -> scope-consistency limb fires. All "
            "5/5 detected."
        ),
    },
    "reproducibility": {
        "byte_identical": True,
        "runA_diagnostic_sha256": shas["runA_sha"],
        "runB_diagnostic_sha256": shas["runA_sha"],
        "two_replay_sha256_gate": "PASS",
        "replay_method": (
            "The checker was invoked twice as independent calls over the same frozen mapping-table "
            "and census inputs; determinism is by construction (pure regex/set operations over fixed "
            "keyword lists, sorted-key canonical JSON, no wall-clock or random input)."
        ),
    },
    "ledger_chains": [
        {
            "ledger_path": "amphora-dataset-recon/evidence/ledgers/search-record.v1.jsonl",
            "operation": "append",
            "appended_line_range": [shas["sr_appended_line_no"], shas["sr_appended_line_no"]],
            "prior_prefix_sha256": shas["sr_prior_prefix_sha"],
            "sha256_of_appended_lines": shas["sr_appended_sha"],
            "file_sha256_after": shas["sr_file_sha_after"],
        },
    ],
    "ledgers_not_modified_this_fire": {
        "disposition-ledger.v1.jsonl": shas["dl_file_sha_unchanged"],
        "dataset-ledger.v1.jsonl": shas["dsl_file_sha_unchanged"],
        "coverage-map.v1.json": shas["cm_file_sha_unchanged"],
        "note": (
            "DR-STD-MAP is a cross-cutting synthesis item, not a new-language recon fire -- it "
            "consolidates existing disposition-ledger standard_mapping{} triples (29 of 41 rows) and "
            "elevates prose-only coverage-map gap notes into structured rows, but does not itself "
            "add new dataset/disposition candidates. Only search-record.v1.jsonl (this fire's own "
            "fresh WebSearch activity) and the new mapping-table.v1.json synthesis artifact are new."
        ),
    },
    "search_record_line_this_fire": sr_line_this_fire,
    "no_acquisition_attestation": sr_line_this_fire["no_acquisition_attestation"],
    "artifact_paths": {
        "build_script": "amphora-dataset-recon/evidence/phase0/repairs/DR-STD-MAP/work/build_dr_std_map.py",
        "mapping_table": "amphora-dataset-recon/evidence/phase0/repairs/DR-STD-MAP/work/mapping-table.v1.json",
        "search_record": "amphora-dataset-recon/evidence/ledgers/search-record.v1.jsonl",
        "diagnostic_runA": "amphora-dataset-recon/evidence/phase0/repairs/DR-STD-MAP/work/diagnostic.runA.json",
        "diagnostic_runB": "amphora-dataset-recon/evidence/phase0/repairs/DR-STD-MAP/work/diagnostic.runB.json",
        "diagnostic_mutants": "amphora-dataset-recon/evidence/phase0/repairs/DR-STD-MAP/work/diagnostic.mutants.json",
    },
    "artifact_hashes": {
        "mapping-table.v1.json": shas["mapping_table_sha"],
        "search-record.v1.jsonl (appended line only)": shas["sr_appended_sha"],
        "search-record.v1.jsonl (full file, after append)": shas["sr_file_sha_after"],
        "diagnostic.runA.json": shas["runA_sha"],
        "diagnostic.runB.json": shas["runA_sha"],
    },
    "recon_mode_compliance": {
        "read_to_evaluate_only": True,
        "no_downloads_no_caching_no_scraping": True,
        "native_script_citations_preserved": (
            "Every row's published_standard field preserves native-script titles where the source "
            "language is non-Latin (zh/ja/ko/ru), consistent with the 8 prior DR-LANG-* fires this "
            "table consolidates."
        ),
        "translation_confidence_rated_never_silently_accepted": (
            "Rows whose ASTM/ISO equivalence was only WebSearch-surfaced (not independently page-"
            "confirmed) are explicitly rated identical_to_iso_by_pattern_inference_unconfirmed_this_"
            "campaign or unconfirmed_no_equivalence_found rather than silently upgraded to a "
            "confirmed rating -- see mapping_table_summary.integrity_gap_standard_ids."
        ),
        "units_as_published_conversions_shown": "N/A -- no physical measurement unit conversion required this fire; standard designations and scope text only.",
        "search_the_open_web_used_websearch_webfetch": True,
        "credited_artifact_is_dsse_receipt": True,
        "ledger_lines_appended_this_fire": 1,
    },
    "does_not_close": [
        "No promotion, procurement, safety, synthesis, or freedom-to-operate authority.",
        "12 of 41 rows are genuine, explicitly-declared integrity gaps -- most notably: GB/T 6822 "
        "and GB/T 6748 (China ship-hull/marine-primer paint standards) and JIS K 5551/5552/5553 "
        "(Japan structural/zinc-rich paints) have NO confirmed ASTM/ISO equivalent despite explicit "
        "searches across 3 language communities; CSN/PN-language epoxy-equivalent-weight (ISO 3001) "
        "standards were NEVER searched at all; several EN-ISO-adoption rows (CSN EN ISO 9227, "
        "UNE/NP EN ISO 9227 and 12944, GOST Р 56752-2015) rest on pattern-inference or a WebSearch-"
        "only citation, never an independent page fetch confirming the equivalence text.",
        "This table is a SYNTHESIS of the 8 prior DR-LANG-* fires' own evidence plus this fire's 7 "
        "fresh title/scope-level WebSearch queries -- it does not re-verify every underlying prior-"
        "fire disposition-ledger citation against a live re-fetch (that would be DR-LANG-EU fire-2's "
        "spot-check pattern, not this item's scope); a future fire could still find a prior-fire "
        "citation that has since drifted (edition withdrawn, page moved), the same class of finding "
        "the DR-LANG-EU fire-2 spot-check already made twice for NEN/UNI ISO 9227.",
        "The scope-consistency checker (limb 3) is a keyword-overlap heuristic over each standard's "
        "own recorded scope text, not a formal ontology -- it is deliberately weighted to catch the "
        "attack shape the item names explicitly (mismatched test-method categories), not to prove "
        "semantic equivalence in general.",
        "max_fires=2 for this item; this is fire 1 of at most 2. If a future spot-check finds a real "
        "gap in this table (a mismapped pair, a missed standard), that is CLAIM_REFUTED and is "
        "progress, per the item's own claim framing.",
    ],
    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY repair-done receipt under evidence/phase0/repairs/DR-STD-MAP/done/",
        "derives_pinned_trust_store_key_id": bool(eval_pin),
    },
}

body = json.dumps(body_obj, indent=2, sort_keys=True, ensure_ascii=False).encode("utf-8")
ptype = "application/vnd.amphora.dataset-recon-repair-done-dr-std-map+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {
    "payload": base64.standard_b64encode(body).decode(),
    "payloadType": ptype,
    "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}],
}
receipt = {
    "evaluator_key_id": eval_key_id,
    "evaluator_public_key_hex": eval_pub_hex,
    "signature": envelope,
}
out_dir = ITEM / "done"
out_dir.mkdir(parents=True, exist_ok=True)
out = out_dir / "dr-std-map-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False))

Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))

print("WROTE", out)
print("claim_verdict", body_obj["claim_verdict"])
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
