#!/usr/bin/env python3
"""DSSE-Ed25519-sign the DR-GAP campaign-item done receipt for
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
ITEM = MOD / "evidence/phase0/repairs/DR-GAP"
WORK = ITEM / "work"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

DIRECTIVE_MD = ROOT / "docs/directives/2026-08-09-dataset-reconnaissance-multilingual.md"
DIRECTIVE_SHA_EXPECTED = "97fad5d1636f5ccb106562c2d940535651c216d357dd5276088f2db12bdba207"

FIRE_ID = "20260810T050001-1454665-a2c9f114184d"


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

diagnostic = json.loads((WORK / "diagnostic.canonical.json").read_bytes())
assert diagnostic["real_register"]["refutation_criterion_fired"] is False, "corrected register must NOT fire"
assert diagnostic["mutant_a_deleted_row"]["refutation_criterion_fired"] is True
assert diagnostic["mutant_b_blanked_fact"]["refutation_criterion_fired"] is True

runA_sha = sha((WORK / "diagnostic.runA.json").read_bytes())
runB_sha = sha((WORK / "diagnostic.runB.json").read_bytes())
assert runA_sha == runB_sha, "two-replay byte-stability gate failed"

register = json.loads((WORK / "gap-register.v1.json").read_bytes())
register_sha = sha((WORK / "gap-register.v1.json").read_bytes())
prefix_miss_sha = sha((WORK / "gap-register.v1.PREFIX_MISS_amphora-sourceability-ehs.json").read_bytes())
queue_snapshot_sha = sha((WORK / "data-acquisition-queue.snapshot.jsonl").read_bytes())
build_script_sha = sha((WORK / "build_register.py").read_bytes())
checker_script_sha = sha((WORK / "check_completeness.py").read_bytes())

assert len(register["rows"]) == 26
assert register["methodology"]["pre_tier_0_modules_count"] == 12
assert "amphora-sourceability-ehs" in register["methodology"]["pre_tier_0_modules_found"]

body_obj = {
    "schema": "amphora.dataset-recon.repair-done.dr-gap.v1",
    "module": "amphora-dataset-recon",
    "campaign_item_id": "DR-GAP",
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "EVIDENCE_ONLY",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "fire_id": FIRE_ID,
    "date": "2026-08-10",
    "phase": "PRE_PHASE_0",
    "scientific_success_required_for_phase0": False,
    "no_acquisition_attestation": (
        "This fire made zero web queries, fetches, downloads, or acquisitions. All "
        "inputs are already-resident portfolio files read this fire: 29 modules' "
        "docs/mission.md front-matter and 'KPI register and promotion gates' prose "
        "(read directly, not cached beyond normal editor buffers), a full-tree grep "
        "sweep for MODELED/ASSUMED recipe-element markers and recipe/BOM-named files "
        "(found none, R01 empty-set finding), and a read-only copy of "
        "data-acquisition-queue.jsonl from xbabe1 (the portfolio's own internal queue, "
        "not an external dataset) mirrored into this item's work/ directory for "
        "deterministic re-processing. Nothing was written outside "
        "amphora-dataset-recon this fire except the read-only queue-file mirror copy "
        "sourced from xbabe1's own campaign-queue file (not a third-party or "
        "external-web artifact)."
    ),
    "done_criterion_verbatim": (
        "Signed gap register in which every row states the four mandated facts: what "
        "measurement or label class is missing, at what minimum n, under what "
        "measurement standard, and what a qualifying dataset would have to contain. "
        "Sources: every open data-acquisition-queue ask, every Pre-Tier-0 promotion "
        "blocker naming a dataset, every lab-in-the-loop spec referencing an external "
        "corpus, and every MODELED/ASSUMED recipe element already published at the "
        "register's snapshot date."
    ),
    "done_criterion_met": True,
    "done_criterion_met_note": (
        "Met by the CORRECTED register embedded below (26 rows), after this fire's "
        "own attack found and repaired a real completeness gap in the first-built "
        "25-row draft -- see refutation_finding_this_fire below."
    ),
    "claim_tested": (
        "The current DR-GAP deliverable state is complete and accurate for its scope "
        "(finding a miss is CLAIM_REFUTED and is progress)."
    ),
    "claim_verdict": "CLAIM_REFUTED",
    "refutation_finding_this_fire": {
        "summary": (
            "The first-built gap register (25 rows, sha256 %s, preserved unmodified as "
            "work/gap-register.v1.PREFIX_MISS_amphora-sourceability-ehs.json) omitted "
            "amphora-sourceability-ehs, a genuine Pre-Tier-0 (phase == PRE_PHASE_0) "
            "module whose mission.md 'External dependency or delay' bullet names a "
            "missing dataset/measurement class ('Current candidate- and issuer-bound "
            "supplier declarations and lot evidence')."
        ) % prefix_miss_sha,
        "how_found": (
            "check_completeness.py independently re-derives the Pre-Tier-0 module set "
            "from scratch by re-parsing every amphora-*/docs/mission.md front-matter "
            "JSON line directly -- it never imports or trusts build_register.py's "
            "hardcoded PROMOTION_BLOCKERS list. Run against the real 25-row register, "
            "it found independent_pre_tier0_module_count=12 (including "
            "amphora-sourceability-ehs) vs register_blocker_modules=11, so "
            "refutation_criterion_fired=true with reason \"Pre-Tier-0 module "
            "'amphora-sourceability-ehs' promotion blocker absent from register\"."
        ),
        "repair_this_fire": (
            "Added row B12 to build_register.py's PROMOTION_BLOCKERS list, sourced "
            "directly from amphora-sourceability-ehs/docs/mission.md's own 'KPI "
            "register and promotion gates' section (primary_kpi 'evidence question "
            "accuracy at gates.sourceability_status', external_dependency 'Current "
            "candidate- and issuer-bound supplier declarations and lot evidence', "
            "minimum_n NOT_SPECIFIED_IN_SOURCE, same honesty standard as the other 11 "
            "blocker rows), then rebuilt the register (now 26 rows, sha256 %s) and "
            "re-ran the independent checker: refutation_criterion_fired=false, zero "
            "reasons."
        ) % register_sha,
        "repair_status": "fix_landed_and_reverified_same_fire",
    },
    "attack_shape_executed": (
        "Built the register from four declared source categories (queue asks, "
        "Pre-Tier-0 promotion blockers, lab-in-the-loop specs [collapsed into the "
        "blocker rows, declared], MODELED/ASSUMED recipe elements [empty set, "
        "declared]), then wrote an independent second-party completeness checker "
        "that never imports the builder and re-derives every source set from scratch "
        "(re-reads the queue file directly for line hashes; re-parses all 29 "
        "mission.md front-matter blocks directly for the Pre-Tier-0 module set). Ran "
        "it against the real register (found and drove the repair above), then ran "
        "it twice more as a two-replay byte-stability gate on the corrected register "
        "(byte-identical, sha256 %s), then against two deliberately mutated copies: "
        "mutant A deletes queue-derived row Q07 (module amphora-cure-potlife-gate, "
        "the st-19168 EIS rights-review consolidation ask); mutant B blanks the "
        "'qualifying_dataset_requirements' mandated fact on promotion-blocker row B05 "
        "(amphora-ip-fto-guard). Both mutants correctly fired the refutation "
        "criterion, proving the checker is non-vacuous."
    ) % runA_sha,
    "directive_path": "docs/directives/2026-08-09-dataset-reconnaissance-multilingual.md",
    "directive_sha256": directive_sha_actual,
    "directive_obligation": "DR-GAP",
    "directive_refutation_criterion_verbatim": (
        "Any gap row lacks one of the four mandated statements, or a data ask live in "
        "the queue at the register's snapshot date, a promotion blocker naming a "
        "dataset, or a MODELED or ASSUMED recipe element published before that "
        "snapshot is absent from the register."
    ),
    "directive_refutation_criterion_observation": (
        "OCCURRED against the first-built 25-row register this fire (see "
        "refutation_finding_this_fire): a genuine Pre-Tier-0 promotion blocker "
        "(amphora-sourceability-ehs) was absent from the register. Repaired within "
        "this same fire; the corrected 26-row register embedded below (gap_register "
        "field) does NOT trigger the criterion under the same independent checker, "
        "confirmed by re-derivation of every source set from scratch plus a "
        "byte-identical two-replay and two non-vacuous positive-control mutations. "
        "The verdict for this fire is CLAIM_REFUTED because the criterion fired "
        "during this fire's own attack -- per the campaign item's framing, 'finding "
        "a miss is CLAIM_REFUTED and is progress' -- not CLAIM_SURVIVED, even though "
        "the deliverable now (post-repair) satisfies its done_criterion."
    ),
    "positive_control": {
        "planted_defect": (
            "Two independent defects planted in mutated copies of the corrected "
            "register: (A) deleted queue-derived row Q07 entirely; (B) blanked the "
            "'qualifying_dataset_requirements' mandated fact on row B05."
        ),
        "how_planted": (
            "mutant A: gap-register.mutantA_deleted_row.v1.json is a deep copy of the "
            "corrected register with the row whose row_id=='Q07' filtered out of the "
            "'rows' list. mutant B: gap-register.mutantB_blanked_fact.v1.json is a "
            "deep copy with row_id=='B05' 'qualifying_dataset_requirements' set to ''."
        ),
        "detected": True,
        "evidence": (
            "diagnostic.canonical.json mutant_a_deleted_row.refutation_criterion_fired"
            "=true (reason: queue line sha256=87d3f9d220722431... absent from "
            "register); mutant_b_blanked_fact.refutation_criterion_fired=true (reason: "
            "row B05 missing/empty mandated fact 'qualifying_dataset_requirements')."
        ),
    },
    "reproducibility": {
        "byte_identical": bool(runA_sha == runB_sha),
        "runA_diagnostic_sha256": runA_sha,
        "runB_diagnostic_sha256": runB_sha,
        "replay_method": (
            "check_completeness.py was invoked twice as independent OS-level "
            "subprocess-equivalent runs (separate python3 invocations) over the same "
            "frozen gap-register.v1.json, data-acquisition-queue.snapshot.jsonl, and "
            "the 29 on-disk mission.md files; determinism is by construction (pure "
            "set/dict operations, sorted-key canonical JSON, no wall-clock or random "
            "input). This gate certifies the diagnostic is a byte-stable function of "
            "the already-recorded inputs; it does not and cannot certify that a future "
            "re-scan of mission.md would be unchanged if those files are edited by "
            "other agents -- that is disclosed here, not hidden."
        ),
    },
    "gap_register": register,
    "artifact_hashes": {
        "gap-register.v1.json (corrected, 26 rows)": register_sha,
        "gap-register.v1.PREFIX_MISS_amphora-sourceability-ehs.json (uncorrected, 25 rows, preserved as evidence)": prefix_miss_sha,
        "data-acquisition-queue.snapshot.jsonl": queue_snapshot_sha,
        "build_register.py": build_script_sha,
        "check_completeness.py": checker_script_sha,
        "diagnostic.canonical.json": sha((WORK / "diagnostic.canonical.json").read_bytes()),
    },
    "artifact_paths": {
        "gap_register_corrected": "amphora-dataset-recon/evidence/phase0/repairs/DR-GAP/work/gap-register.v1.json",
        "gap_register_uncorrected_evidence": "amphora-dataset-recon/evidence/phase0/repairs/DR-GAP/work/gap-register.v1.PREFIX_MISS_amphora-sourceability-ehs.json",
        "queue_snapshot": "amphora-dataset-recon/evidence/phase0/repairs/DR-GAP/work/data-acquisition-queue.snapshot.jsonl",
        "build_script": "amphora-dataset-recon/evidence/phase0/repairs/DR-GAP/work/build_register.py",
        "checker_script": "amphora-dataset-recon/evidence/phase0/repairs/DR-GAP/work/check_completeness.py",
        "diagnostic": "amphora-dataset-recon/evidence/phase0/repairs/DR-GAP/work/diagnostic.canonical.json",
        "mutant_a": "amphora-dataset-recon/evidence/phase0/repairs/DR-GAP/work/gap-register.mutantA_deleted_row.v1.json",
        "mutant_b": "amphora-dataset-recon/evidence/phase0/repairs/DR-GAP/work/gap-register.mutantB_blanked_fact.v1.json",
    },
    "recon_mode_compliance": {
        "read_to_evaluate_only": True,
        "no_downloads_no_caching_no_scraping": True,
        "native_script_citations_preserved": "N/A this fire -- no new native-language source was read; DR-GAP consolidates already-recorded portfolio gaps, none of which are native-script sourced.",
        "translation_confidence_rated_never_silently_accepted": "N/A this fire, same reason.",
        "units_as_published_conversions_shown": "N/A this fire -- no physical measurement conversion performed; queue-ask gap text is quoted verbatim from its source line.",
        "credited_artifact_is_dsse_receipt": True,
        "ledger_lines_appended_this_fire": 0,
        "ledger_note": (
            "DR-GAP's deliverable is a new gap-register artifact, not an addition to "
            "dataset-ledger.v1.jsonl/disposition-ledger.v1.jsonl/coverage-map.v1.json "
            "(those carry external-dataset RECOMMENDATIONS from Mandate A web search; "
            "DR-GAP instead consolidates the portfolio's OWN internal gap inventory "
            "per directive Section 3, which anchors future search per the item title "
            "-- no ledger line was due this fire)."
        ),
    },
    "does_not_close": [
        "No promotion, procurement, safety, synthesis, or freedom-to-operate authority.",
        "MODELED/ASSUMED recipe elements are an honest empty set THIS SNAPSHOT because "
        "no Candidate Formulation Package exists yet anywhere in the tree -- this is "
        "not evidence that none will ever exist; when CF-TIER produces one, DR-FRESH's "
        "run-2 obligation (per this item's own objective text) must fold its per-element "
        "MODELED/ASSUMED tiers into a superseding register revision.",
        "Several promotion-blocker rows (B01, B03, B04, B05, B06, B07, B08, B09, B12 -- "
        "8 of 12) honestly record minimum_n as NOT_SPECIFIED_IN_SOURCE because the "
        "underlying mission.md promotion gate states no numeric threshold; this register "
        "does not fabricate a number to fill the gap, but it does mean those 8 rows are "
        "individually a weaker 'four mandated facts' statement than the queue-ask rows "
        "and the 4 blocker rows that do carry numeric n (B02, B10, B11) -- flagged "
        "honestly rather than papered over.",
        "amphora-ip-fto-guard's blocker row (B05) is predominantly a counsel/legal-"
        "service dependency, not a pure dataset ask; included per a literal reading of "
        "the directive's 'promotion blocker names a missing dataset or measurement "
        "class' test, flagged rather than silently dropped or silently included without "
        "comment.",
        "Does not modify or re-sign PROBE-WEB's or DR-RUBRIC's done receipts; both are "
        "referenced by path only, not re-verified beyond what this fire's own diagnostic "
        "needed.",
    ],
    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY repair-done receipt under evidence/phase0/repairs/DR-GAP/done/",
        "derives_pinned_trust_store_key_id": bool(eval_pin),
    },
}

body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.dataset-recon-repair-done-dr-gap+json"
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
out = ITEM / "done" / "dr-gap-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))

print("WROTE", out)
print("claim_verdict", body_obj["claim_verdict"])
print("done_criterion_met", body_obj["done_criterion_met"])
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
