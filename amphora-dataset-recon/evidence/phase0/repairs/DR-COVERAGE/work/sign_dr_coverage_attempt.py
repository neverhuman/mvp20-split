#!/usr/bin/env python3
"""DSSE-Ed25519-sign the DR-COVERAGE campaign-item attempt receipt for
amphora-dataset-recon. AUDIT_ONLY. Pinned Phase-0 evaluator key only.
This fire's attack REFUTED the claim under test, so the receipt goes to
attempts/, not done/ (done_criterion was not met).
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
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

DIRECTIVE_MD = ROOT / "docs/directives/2026-08-09-dataset-reconnaissance-multilingual.md"
DIRECTIVE_SHA_EXPECTED = "97fad5d1636f5ccb106562c2d940535651c216d357dd5276088f2db12bdba207"

FIRE_ID = "20260811T110001-7123-94961fa526cc"


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

diagA = json.loads((WORK / "diagnostic.runA.json").read_bytes())
diagB = json.loads((WORK / "diagnostic.runB.json").read_bytes())
runA_sha = sha((WORK / "diagnostic.runA.json").read_bytes())
runB_sha = sha((WORK / "diagnostic.runB.json").read_bytes())
assert runA_sha == runB_sha, "two-replay byte-stability gate failed"
assert diagA["refutation_criterion_fired"] is True, "expected the live map to fail its own completeness check"

selftest_repaired_sha = sha((WORK / "coverage-map.selftest_repaired.v1.json").read_bytes())
selftest_mutant_sha = sha((WORK / "coverage-map.selftest_mutant_blank_good_row.v1.json").read_bytes())
coverage_map_snapshot_sha = sha((WORK / "coverage-map.snapshot.v1.json").read_bytes())
dataset_ledger_snapshot_sha = sha((WORK / "dataset-ledger.snapshot.v1.jsonl").read_bytes())
checker_script_sha = sha((WORK / "check_coverage_completeness.py").read_bytes())

body_obj = {
    "schema": "amphora.dataset-recon.repair-attempt.dr-coverage.v1",
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
        "This fire made zero web queries, fetches, downloads, or acquisitions. All "
        "inputs are already-resident portfolio files read this fire: a read-only "
        "snapshot copy of the live evidence/ledgers/coverage-map.v1.json (64 gaps[] "
        "rows, built by prior DR-LANG-* fires) and evidence/ledgers/dataset-ledger.v1.jsonl "
        "(14 RECOMMENDED-grade entries), both taken under the module's advisory flock "
        "and content-hashed before any analysis. No dataset was downloaded, cached, or "
        "scraped; the checker script only reads already-resident JSON/JSONL files."
    ),
    "claim_tested": (
        "The current DR-COVERAGE deliverable state is complete and accurate for its "
        "scope (finding a miss is CLAIM_REFUTED and is progress)."
    ),
    "claim_verdict": "CLAIM_REFUTED",
    "done_criterion_verbatim": (
        "Signed gap-by-gap (and, once CF-TIER exists, recipe-element-by-element) map "
        "in which every row carries exactly one of: the best RECOMMENDED source, the "
        "best CONDITIONAL source, or an explicit conversion into a commissioned-"
        "measurement candidate for the lab-in-the-loop program. An empty search result "
        "converts; it never pads and never disappears."
    ),
    "done_criterion_met": False,
    "done_criterion_met_note": (
        "NOT met. The live coverage-map.v1.json (evidence/ledgers/, snapshot sha256 "
        "%s, 64 gaps[] rows contributed across the PROBE-WEB/DR-LANG-ZH/JA/DE/RU/KO/FR/"
        "IBERIAN/CEE/EU campaign) contains 10 rows that serve a real module gap "
        "(module_gaps non-empty) whose note text describes an honest empty search "
        "result, but whose best_recommended, best_conditional, AND "
        "commissioned_measurement_candidate fields are ALL null -- the empty result "
        "was disclosed in prose but never structurally converted into a "
        "commissioned-measurement candidate, contrary to rule 7 ('An empty search "
        "result converts; it never pads and never disappears') and this item's own "
        "done_criterion. This receipt therefore attaches to attempts/, not done/."
    ) % coverage_map_snapshot_sha,
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
        "OCCURRED. 10 of 64 coverage-map gaps[] rows that serve a real module gap "
        "(module_gaps non-empty) have neither a best_recommended, nor a "
        "best_conditional, nor a commissioned_measurement_candidate value: "
        "corrosion-database-ja, cure-kinetics-adjacent-epoxy-systems-iberian, "
        "cure-kinetics-nl, marine-coating-ks-standard-mapping-ko, "
        "national-corrosion-testing-institute-pl-cs, ship-coating-dataset-ko-unresolved, "
        "ship-hull-antifouling-standard-mapping-fr, "
        "ship-hull-antifouling-standard-mapping-iberian, "
        "ship-hull-antifouling-standard-mapping-it, "
        "ship-hull-antifouling-standard-mapping-nl (full detail in "
        "diagnostic.runA.json.triple_null_violations, embedded below). The second "
        "clause of the criterion (a named source absent from the Dataset Ledger) did "
        "NOT occur: all 9 non-null best_recommended values resolve to a "
        "dataset-ledger.v1.jsonl candidate_id (recommended_not_in_ledger_count=0). "
        "best_conditional values were NOT checked against the Dataset Ledger -- "
        "directive Section 8 defines the Dataset Ledger as holding one entry per "
        "RECOMMENDED source only ('Dataset Ledger. One structured entry per "
        "recommended source'), with CONDITIONAL candidates instead living in the "
        "Disposition Ledger (verified: best_conditional candidate DR-LANG-ZH-03 is "
        "present in disposition-ledger.v1.jsonl, absent from dataset-ledger.v1.jsonl, "
        "which is the designed split, not a defect)."
    ),
    "attack_shape_executed": (
        "Per this item's own ATTACK SHAPE ('Blank one gap's row in a copy and attack "
        "whether the map-completeness check fires; cross-check that every named "
        "source exists in the Dataset Ledger'): built an independent checker "
        "(check_coverage_completeness.py) that re-derives both facts from scratch "
        "over frozen snapshots (never imports any prior build script), ran it twice "
        "as separate python3 invocations for a byte-stability gate (byte-identical, "
        "sha256 %s), then non-vacuity-tested it two ways: (a) a hypothetical repaired "
        "copy (coverage-map.selftest_repaired.v1.json, sha256 %s) with all 10 real "
        "violations filled with a placeholder commissioned_measurement_candidate -- "
        "checker correctly reports refutation_criterion_fired=false, "
        "triple_null_violations_count=0; (b) a mutant copy "
        "(coverage-map.selftest_mutant_blank_good_row.v1.json, sha256 %s) that blanks "
        "one PREVIOUSLY-GOOD row (jis-eew-testdata-annex-ja, which legitimately uses "
        "commissioned_measurement_candidate in the live map) -- checker correctly "
        "detects the freshly planted defect, violations count rising from 10 to 11. "
        "This confirms the checker is non-vacuous in both directions on top of firing "
        "correctly against the real, unmutated live map -- so no additional "
        "positive_control block is required for this CLAIM_REFUTED verdict (refutations "
        "carry their own evidence per the outcomes' rules)."
    ) % (runA_sha, selftest_repaired_sha, selftest_mutant_sha),
    "reproducibility": {
        "byte_identical": bool(runA_sha == runB_sha),
        "runA_diagnostic_sha256": runA_sha,
        "runB_diagnostic_sha256": runB_sha,
        "replay_method": (
            "check_coverage_completeness.py was invoked twice as independent "
            "python3 subprocess-equivalent runs over the same frozen "
            "coverage-map.snapshot.v1.json and dataset-ledger.snapshot.v1.jsonl; "
            "determinism is by construction (pure JSON parse + set/dict operations, "
            "sorted-key canonical JSON output, no wall-clock or random input)."
        ),
    },
    "diagnostic_runA": diagA,
    "artifact_hashes": {
        "coverage-map.snapshot.v1.json": coverage_map_snapshot_sha,
        "dataset-ledger.snapshot.v1.jsonl": dataset_ledger_snapshot_sha,
        "check_coverage_completeness.py": checker_script_sha,
        "diagnostic.runA.json": runA_sha,
        "diagnostic.runB.json": runB_sha,
        "coverage-map.selftest_repaired.v1.json": selftest_repaired_sha,
        "coverage-map.selftest_mutant_blank_good_row.v1.json": selftest_mutant_sha,
    },
    "artifact_paths": {
        "coverage_map_snapshot": "amphora-dataset-recon/evidence/phase0/repairs/DR-COVERAGE/work/coverage-map.snapshot.v1.json",
        "dataset_ledger_snapshot": "amphora-dataset-recon/evidence/phase0/repairs/DR-COVERAGE/work/dataset-ledger.snapshot.v1.jsonl",
        "checker_script": "amphora-dataset-recon/evidence/phase0/repairs/DR-COVERAGE/work/check_coverage_completeness.py",
        "diagnostic_runA": "amphora-dataset-recon/evidence/phase0/repairs/DR-COVERAGE/work/diagnostic.runA.json",
        "diagnostic_runB": "amphora-dataset-recon/evidence/phase0/repairs/DR-COVERAGE/work/diagnostic.runB.json",
        "selftest_repaired": "amphora-dataset-recon/evidence/phase0/repairs/DR-COVERAGE/work/coverage-map.selftest_repaired.v1.json",
        "selftest_mutant": "amphora-dataset-recon/evidence/phase0/repairs/DR-COVERAGE/work/coverage-map.selftest_mutant_blank_good_row.v1.json",
        "live_coverage_map_audited": "amphora-dataset-recon/evidence/ledgers/coverage-map.v1.json",
        "live_dataset_ledger_audited": "amphora-dataset-recon/evidence/ledgers/dataset-ledger.v1.jsonl",
    },
    "recon_mode_compliance": {
        "read_to_evaluate_only": True,
        "no_downloads_no_caching_no_scraping": True,
        "native_script_citations_preserved": "N/A this fire -- audit-only, no new native-language source was read.",
        "translation_confidence_rated_never_silently_accepted": "N/A this fire, same reason.",
        "units_as_published_conversions_shown": "N/A this fire -- no physical measurement conversion performed.",
        "credited_artifact_is_dsse_receipt": True,
        "ledger_lines_appended_this_fire": 0,
        "ledger_note": (
            "This fire is an AUDIT of coverage-map.v1.json, not a new search fire -- "
            "it appends zero lines to dataset-ledger.v1.jsonl, disposition-ledger.v1.jsonl, "
            "search-record.v1.jsonl, or coverage-map.v1.json itself. Per rule 3 those "
            "ledgers are APPEND-ONLY; repairing the 10 flagged rows (converting each "
            "honest empty result into an explicit commissioned-measurement candidate, "
            "the DR-GAP/DR-LANG precedent already used for the other 12 empty-result "
            "rows in the same file) is left to a future fire of this same item (max_fires=2) "
            "or a dedicated repair item, so the supersede-never-rewrite discipline is "
            "exercised deliberately rather than rushed into this fire's remaining budget."
        ),
    },
    "does_not_close": [
        "No promotion, procurement, safety, synthesis, or freedom-to-operate authority.",
        "Does not modify, rewrite, or truncate coverage-map.v1.json, dataset-ledger.v1.jsonl, "
        "disposition-ledger.v1.jsonl, or search-record.v1.jsonl -- all four ledgers are "
        "read-only inputs this fire, copied into this item's own work/ snapshot before analysis.",
        "Does not attempt the recipe-element-by-element half of the done_criteria ('once "
        "CF-TIER exists') -- CF-TIER does not exist yet anywhere in the tree this fire "
        "(consistent with DR-GAP's own prior finding of the same empty set).",
        "The remaining fire budget for this item (max_fires=2, this is fire 1 of 2) is "
        "left for a future fire to either repair the 10 flagged rows (supersede-never-"
        "rewrite, a NEW coverage-map append, not an edit) or re-verify the repair.",
    ],
    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY repair-attempt receipt under evidence/phase0/repairs/DR-COVERAGE/attempts/",
        "derives_pinned_trust_store_key_id": bool(eval_pin),
    },
}

body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.dataset-recon-repair-attempt-dr-coverage+json"
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
out = ITEM / "attempts" / "dr-coverage-fire1-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))

print("WROTE", out)
print("claim_verdict", body_obj["claim_verdict"])
print("done_criterion_met", body_obj["done_criterion_met"])
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
