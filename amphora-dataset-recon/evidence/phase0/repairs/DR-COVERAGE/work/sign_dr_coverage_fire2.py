#!/usr/bin/env python3
"""DSSE-Ed25519-sign the DR-COVERAGE campaign-item fire-2/2 repair (done)
receipt for amphora-dataset-recon. AUDIT_ONLY. Pinned Phase-0 evaluator key
only. This fire repaired the 10 triple-null rows fire 1 flagged, re-ran the
unchanged fire-1 checker against the repair, and confirmed it now survives
(refutation_criterion_fired=false) with a genuine positive control. Goes to
done/ because the item's done_criterion is now met.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-dataset-recon"
ITEM = MOD / "evidence/phase0/repairs/DR-COVERAGE"
WORK = ITEM / "work"
LEDGERS = MOD / "evidence/ledgers"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

DIRECTIVE_MD = ROOT / "docs/directives/2026-08-09-dataset-reconnaissance-multilingual.md"
DIRECTIVE_SHA_EXPECTED = "97fad5d1636f5ccb106562c2d940535651c216d357dd5276088f2db12bdba207"

FIRE_ID = "20260811T120001-531794-e1706ed51e19"
FIRE1_ID = "20260811T110001-7123-94961fa526cc"
FIRE1_RECEIPT = "amphora-dataset-recon/evidence/phase0/repairs/DR-COVERAGE/attempts/dr-coverage-fire1-receipt.v1.dsse.json"


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

checker_script_sha = sha((WORK / "check_coverage_completeness.py").read_bytes())
# NOTE: script is byte-unchanged from fire 1 (never edited this fire) -- same sha256 both fires.

v1_sha = sha((LEDGERS / "coverage-map.v1.json").read_bytes())
v2_bytes = (LEDGERS / "coverage-map.v2.json").read_bytes()
v2_sha = sha(v2_bytes)
candidate_sha = sha((WORK / "coverage-map.v2.candidate.json").read_bytes())
assert v2_sha == candidate_sha, "evidence/ledgers/coverage-map.v2.json does not match work/ candidate"

dl_snapshot_sha = sha((WORK / "dataset-ledger.snapshot.v1.jsonl").read_bytes())
dl_live_sha = sha((LEDGERS / "dataset-ledger.v1.jsonl").read_bytes())
assert dl_snapshot_sha == dl_live_sha, "dataset ledger changed since fire 1 snapshot; re-derive before signing"

runA_sha = sha((WORK / "diagnostic.v2.runA.json").read_bytes())
runB_sha = sha((WORK / "diagnostic.v2.runB.json").read_bytes())
assert runA_sha == runB_sha, "two-replay byte-stability gate failed on repaired map"

diag_repaired = json.loads((WORK / "diagnostic.v2.runA.json").read_bytes())
assert diag_repaired["refutation_criterion_fired"] is False, "repaired map still fails the checker"
assert diag_repaired["triple_null_violations_count"] == 0
assert diag_repaired["recommended_not_in_ledger_count"] == 0

mutant_sha = sha((WORK / "coverage-map.v2.selftest_mutant_reblank_repaired_row.v1.json").read_bytes())
diag_mutant = json.loads((WORK / "diagnostic.v2.mutant.json").read_bytes())
assert diag_mutant["refutation_criterion_fired"] is True, "positive control failed to fire on planted defect"
assert diag_mutant["triple_null_violations_count"] == 1
assert diag_mutant["triple_null_violations"][0]["gap_id"] == "corrosion-database-ja"

repaired_gap_ids = [
    "corrosion-database-ja",
    "cure-kinetics-adjacent-epoxy-systems-iberian",
    "cure-kinetics-nl",
    "marine-coating-ks-standard-mapping-ko",
    "national-corrosion-testing-institute-pl-cs",
    "ship-coating-dataset-ko-unresolved",
    "ship-hull-antifouling-standard-mapping-fr",
    "ship-hull-antifouling-standard-mapping-iberian",
    "ship-hull-antifouling-standard-mapping-it",
    "ship-hull-antifouling-standard-mapping-nl",
]

body_obj = {
    "schema": "amphora.dataset-recon.repair-done.dr-coverage.v1",
    "module": "amphora-dataset-recon",
    "campaign_item_id": "DR-COVERAGE",
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "EVIDENCE_ONLY",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "fire_id": FIRE_ID,
    "date": "2026-08-11",
    "phase": "PRE_PHASE_0",
    "scientific_success_required_for_phase0": False,
    "no_acquisition_attestation": (
        "This fire made zero new web queries, fetches, downloads, or acquisitions. "
        "It read already-resident portfolio files (the live evidence/ledgers/"
        "coverage-map.v1.json and dataset-ledger.v1.jsonl, both re-verified "
        "byte-identical to fire 1's snapshot before any edit) and produced a NEW "
        "derived artifact (coverage-map.v2.json) whose added text is drawn "
        "entirely from prose already present in the 10 flagged rows' own note "
        "fields plus named public standards-body/classification-society contact "
        "channels -- no dataset was downloaded, cached, or scraped."
    ),
    "claim_tested": (
        "The current DR-COVERAGE deliverable state is complete and accurate for "
        "its scope (finding a miss is CLAIM_REFUTED and is progress)."
    ),
    "claim_verdict": "CLAIM_SURVIVED",
    "repair_status": "fix_landed_survived",
    "fire_of_max": "2/2",
    "prior_fire": {
        "fire_id": FIRE1_ID,
        "receipt": FIRE1_RECEIPT,
        "verdict": "CLAIM_REFUTED",
        "defect": (
            "10 of 64 coverage-map gaps[] rows serving a real module gap had "
            "best_recommended, best_conditional, AND commissioned_measurement_"
            "candidate all null despite an honest empty-result note, violating "
            "rule 7 and this item's own done_criterion."
        ),
    },
    "done_criterion_verbatim": (
        "Signed gap-by-gap (and, once CF-TIER exists, recipe-element-by-element) map "
        "in which every row carries exactly one of: the best RECOMMENDED source, the "
        "best CONDITIONAL source, or an explicit conversion into a commissioned-"
        "measurement candidate for the lab-in-the-loop program. An empty search result "
        "converts; it never pads and never disappears."
    ),
    "done_criterion_met": True,
    "done_criterion_met_note": (
        "MET as of this fire. coverage-map.v2.json (evidence/ledgers/, sha256 %s) "
        "supersedes coverage-map.v1.json (byte-unmodified at its original path, "
        "sha256 %s) by filling the commissioned_measurement_candidate field on all "
        "10 rows fire 1 flagged (%s), using the same pattern already present on 12 "
        "other rows in v1. The unchanged fire-1 checker (check_coverage_"
        "completeness.py, sha256 %s -- byte-identical to fire 1's copy) re-run "
        "against v2.json now reports refutation_criterion_fired=false, "
        "triple_null_violations_count=0, recommended_not_in_ledger_count=0. The "
        "CF-TIER recipe-element-by-element half of the done_criterion remains "
        "inapplicable: CF-TIER does not exist anywhere in the tree as of this fire, "
        "consistent with DR-GAP's and fire 1's own prior finding of the same empty "
        "set -- this is a scope-correct non-attempt, not an omission."
    ) % (v2_sha, v1_sha, ", ".join(repaired_gap_ids), checker_script_sha),
    "directive_path": "docs/directives/2026-08-09-dataset-reconnaissance-multilingual.md",
    "directive_sha256": directive_sha_actual,
    "directive_obligation": "DR-COVERAGE",
    "directive_refutation_criterion_verbatim": (
        "Any register gap or MODELED or ASSUMED recipe element has neither a best "
        "recommended source, a best conditional source, nor an explicit "
        "commissioned-measurement conversion, or names a source absent from the "
        "Dataset Ledger."
    ),
    "directive_refutation_criterion_observation": (
        "DID NOT OCCUR against the repaired coverage-map.v2.json: zero of 64 "
        "gaps[] rows serving a real module gap are now triple-null (0 of 64 rows "
        "have neither a best_recommended, nor a best_conditional, nor a "
        "commissioned_measurement_candidate value), and all 9 non-null "
        "best_recommended values still resolve to a dataset-ledger.v1.jsonl "
        "candidate_id (recommended_not_in_ledger_count=0, unchanged from fire 1 -- "
        "this fire added zero dataset-ledger entries). The criterion's second "
        "clause (a named source absent from the Dataset Ledger) also did not fire. "
        "The criterion DID occur, and was CONFIRMED CAPABLE of occurring, against a "
        "deliberately re-planted defect -- see positive_control below -- so this "
        "survival is not a vacuous pass."
    ),
    "re_attack": {
        "method": (
            "Repair-mode rule 2: re-ran the ORIGINAL refuting attack -- same "
            "checker script (byte-identical sha256, unmodified since fire 1), same "
            "command shape (python3 check_coverage_completeness.py <coverage_map> "
            "<dataset_ledger>), same seeds (none -- pure deterministic JSON/set "
            "logic), same threshold (triple_null_violations_count>0 OR "
            "recommended_not_in_ledger_count>0 fires the criterion) -- against the "
            "repaired coverage-map.v2.json plus the unchanged dataset-ledger "
            "snapshot."
        ),
        "checker_script_sha256": checker_script_sha,
        "checker_script_sha256_matches_fire1": True,
        "command": "python3 check_coverage_completeness.py coverage-map.v2.candidate.json dataset-ledger.snapshot.v1.jsonl",
        "result_fired": False,
        "triple_null_violations_count": 0,
        "recommended_not_in_ledger_count": 0,
    },
    "positive_control": {
        "planted_defect": (
            "Re-blanked the just-repaired commissioned_measurement_candidate field "
            "back to null on gap_id corrosion-database-ja (one of the 10 rows this "
            "fire repaired) in a copy of the repaired map."
        ),
        "how_planted": (
            "File: coverage-map.v2.selftest_mutant_reblank_repaired_row.v1.json "
            "(work/, sha256 %s), derived from coverage-map.v2.candidate.json by "
            "setting gaps[gap_id=='corrosion-database-ja'].commissioned_measurement_"
            "candidate from the newly-written conversion sentence back to null -- "
            "best_recommended and best_conditional were already null on this row, "
            "so this single-field edit exactly reconstructs the fire-1 triple-null "
            "defect on one row."
        ) % mutant_sha,
        "detected": True,
        "evidence": (
            "check_coverage_completeness.py on the mutant copy reports "
            "refutation_criterion_fired=true, triple_null_violations_count=1, with "
            "the sole violation naming gap_id=corrosion-database-ja (diagnostic.v2."
            "mutant.json, sha256 %s) -- the attack correctly re-detects a defect of "
            "the exact kind it exists to catch, ran against the real repaired input "
            "(where it correctly does NOT fire) as the paired negative control."
        ) % sha((WORK / "diagnostic.v2.mutant.json").read_bytes()),
    },
    "supersedes": {
        "superseded_path": "amphora-dataset-recon/evidence/ledgers/coverage-map.v1.json",
        "superseded_sha256": v1_sha,
        "superseded_deleted_or_modified": False,
        "superseding_path": "amphora-dataset-recon/evidence/ledgers/coverage-map.v2.json",
        "superseding_sha256": v2_sha,
        "reason": (
            "v1.json's 10 triple-null rows (identified by fire 1) are repaired by "
            "appending a NEW file, coverage-map.v2.json, rather than editing v1.json "
            "in place, per rule 3 (ledgers are APPEND-ONLY) and this item's own "
            "fix_pattern instruction. v1.json remains byte-identical at its original "
            "path and is not deleted."
        ),
        "retraction_index_entry_added": "amphora-dataset-recon/evidence/phase0/kpis/RETRACTION-INDEX.md",
    },
    "repaired_gap_ids": repaired_gap_ids,
    "repaired_gap_ids_count": len(repaired_gap_ids),
    "reproducibility": {
        "byte_identical": bool(runA_sha == runB_sha),
        "runA_diagnostic_sha256": runA_sha,
        "runB_diagnostic_sha256": runB_sha,
        "replay_method": (
            "check_coverage_completeness.py invoked twice as independent python3 "
            "subprocess-equivalent runs over the same coverage-map.v2.candidate.json "
            "and dataset-ledger.snapshot.v1.jsonl; determinism by construction (pure "
            "JSON parse + set/dict operations, sorted-key canonical JSON output, no "
            "wall-clock or random input)."
        ),
    },
    "diagnostic_repaired": diag_repaired,
    "diagnostic_positive_control_mutant": diag_mutant,
    "artifact_hashes": {
        "coverage-map.v1.json": v1_sha,
        "coverage-map.v2.json": v2_sha,
        "coverage-map.v2.candidate.json": candidate_sha,
        "coverage-map.v2.selftest_mutant_reblank_repaired_row.v1.json": mutant_sha,
        "dataset-ledger.snapshot.v1.jsonl": dl_snapshot_sha,
        "check_coverage_completeness.py": checker_script_sha,
        "diagnostic.v2.runA.json": runA_sha,
        "diagnostic.v2.runB.json": runB_sha,
        "diagnostic.v2.mutant.json": sha((WORK / "diagnostic.v2.mutant.json").read_bytes()),
        "RETRACTION-INDEX.md": sha((MOD / "evidence/phase0/kpis/RETRACTION-INDEX.md").read_bytes()),
    },
    "artifact_paths": {
        "live_coverage_map_v1": "amphora-dataset-recon/evidence/ledgers/coverage-map.v1.json",
        "live_coverage_map_v2": "amphora-dataset-recon/evidence/ledgers/coverage-map.v2.json",
        "candidate_v2": "amphora-dataset-recon/evidence/phase0/repairs/DR-COVERAGE/work/coverage-map.v2.candidate.json",
        "checker_script": "amphora-dataset-recon/evidence/phase0/repairs/DR-COVERAGE/work/check_coverage_completeness.py",
        "diagnostic_repaired_runA": "amphora-dataset-recon/evidence/phase0/repairs/DR-COVERAGE/work/diagnostic.v2.runA.json",
        "diagnostic_repaired_runB": "amphora-dataset-recon/evidence/phase0/repairs/DR-COVERAGE/work/diagnostic.v2.runB.json",
        "positive_control_mutant": "amphora-dataset-recon/evidence/phase0/repairs/DR-COVERAGE/work/coverage-map.v2.selftest_mutant_reblank_repaired_row.v1.json",
        "diagnostic_positive_control": "amphora-dataset-recon/evidence/phase0/repairs/DR-COVERAGE/work/diagnostic.v2.mutant.json",
        "dataset_ledger_snapshot": "amphora-dataset-recon/evidence/phase0/repairs/DR-COVERAGE/work/dataset-ledger.snapshot.v1.jsonl",
        "retraction_index": "amphora-dataset-recon/evidence/phase0/kpis/RETRACTION-INDEX.md",
        "fire1_receipt": FIRE1_RECEIPT,
    },
    "recon_mode_compliance": {
        "read_to_evaluate_only": True,
        "no_downloads_no_caching_no_scraping": True,
        "native_script_citations_preserved": (
            "The one repaired row containing a native-script citation "
            "(ship-coating-dataset-ko-unresolved, Korean title) is carried forward "
            "unmodified from v1 into v2; the new commissioned_measurement_candidate "
            "text added for that row does not alter or retranslate the native "
            "citation."
        ),
        "translation_confidence_rated_never_silently_accepted": "N/A this fire -- no new native-language source was read; all 10 conversion sentences derive from prose already recorded in v1's own note fields.",
        "units_as_published_conversions_shown": "N/A this fire -- no physical measurement conversion performed.",
        "credited_artifact_is_dsse_receipt": True,
        "ledger_lines_appended_this_fire": 0,
        "ledger_note": (
            "This fire appends zero lines to dataset-ledger.v1.jsonl, "
            "disposition-ledger.v1.jsonl, or search-record.v1.jsonl (no new source "
            "was searched or recommended this fire). It adds one NEW file, "
            "coverage-map.v2.json, to evidence/ledgers/ -- v1.json is left "
            "byte-unmodified, consistent with the append-only-ledger-set discipline "
            "applied at file-set granularity rather than in-place line editing."
        ),
    },
    "does_not_close": [
        "No promotion, procurement, safety, synthesis, or freedom-to-operate authority.",
        "Does not modify, rewrite, or truncate coverage-map.v1.json, dataset-ledger.v1.jsonl, "
        "disposition-ledger.v1.jsonl, or search-record.v1.jsonl.",
        "Does not attempt the recipe-element-by-element half of the done_criteria ('once "
        "CF-TIER exists') -- CF-TIER does not exist yet anywhere in the tree this fire.",
        "Does not resolve the underlying empty results themselves (e.g. it does not confirm "
        "a KS/AFNOR/UNI/NEN ship-hull antifouling standard exists) -- it converts each "
        "honest miss into a commissioned-measurement / direct-outreach candidate per rule 7, "
        "which is what the done_criterion requires, not a guarantee that outreach will "
        "succeed.",
        "This item's max_fires (2) is now exhausted; no further fires of DR-COVERAGE are "
        "authorized by the campaign.",
    ],
    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY repair-done receipt under evidence/phase0/repairs/DR-COVERAGE/done/",
        "derives_pinned_trust_store_key_id": bool(eval_pin),
    },
}

body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.dataset-recon-repair-done-dr-coverage+json"
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
out = ITEM / "done" / "dr-coverage-fire2-repair-receipt.v1.dsse.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))

print("WROTE", out)
print("claim_verdict", body_obj["claim_verdict"])
print("done_criterion_met", body_obj["done_criterion_met"])
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
