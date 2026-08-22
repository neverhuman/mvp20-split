#!/usr/bin/env python3
"""DSSE-Ed25519-sign the DR-LANG-DE campaign-item done receipt for
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
ITEM = MOD / "evidence/phase0/repairs/DR-LANG-DE"
WORK = ITEM / "work"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

DIRECTIVE_MD = ROOT / "docs/directives/2026-08-09-dataset-reconnaissance-multilingual.md"
DIRECTIVE_SHA_EXPECTED = "97fad5d1636f5ccb106562c2d940535651c216d357dd5276088f2db12bdba207"

FIRE_ID = "20260810T080001-2919803-f979e09ce9dd"
RUN_ID = f"DR-LANG-DE-{FIRE_ID}"
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
assert sha((WORK / "diagnostic.runA.json").read_bytes()) == sha((WORK / "diagnostic.runB.json").read_bytes())
assert runA["refutation_criterion_fired"] is False
assert all(v["refutation_criterion_fired"] for v in mutants.values())

# self-verify current on-disk ledger state matches what the builder committed
sr_bytes = (LEDGERS / "search-record.v1.jsonl").read_bytes()
dl_bytes = (LEDGERS / "disposition-ledger.v1.jsonl").read_bytes()
dsl_bytes = (LEDGERS / "dataset-ledger.v1.jsonl").read_bytes()
cm_bytes = (LEDGERS / "coverage-map.v1.json").read_bytes()
assert sha(sr_bytes) == shas["sr_file_sha_after"]
assert sha(dl_bytes) == shas["dl_file_sha_after"]
assert sha(dsl_bytes) == shas["dsl_file_sha_after"]
assert sha(cm_bytes) == shas["cm_after_sha"]

dl_lines = [json.loads(l) for l in dl_bytes.decode("utf-8").splitlines() if l.strip()]
disp_this_fire = [d for d in dl_lines if d.get("entry_type") == "candidate_disposition" and d.get("fire_id") == FIRE_ID]
manifest_this_fire = next(d for d in dl_lines if d.get("entry_type") == "candidate_intake_manifest" and d.get("fire_id") == FIRE_ID)
assert len(disp_this_fire) == 8
cm_after = json.loads(cm_bytes)
sr_lines = [json.loads(l) for l in sr_bytes.decode("utf-8").splitlines() if l.strip()]
sr_line_this_fire = next(l for l in sr_lines if l.get("fire_id") == FIRE_ID)
dsl_lines = [json.loads(l) for l in dsl_bytes.decode("utf-8").splitlines() if l.strip()]
dsl_entry_this_fire = dsl_lines[-1]
assert dsl_entry_this_fire["fire_id"] == FIRE_ID and dsl_entry_this_fire["candidate_id"] == "DR-LANG-DE-06"

candidate_scores_summary = ", ".join(
    f"{d['candidate_id']}={d['disposition']['verdict']}({d['rubric_overall_score']})"
    for d in sorted(disp_this_fire, key=lambda x: -x["rubric_overall_score"])
)

body_obj = {
    "schema": "amphora.dataset-recon-repair-done-dr-lang-de.v1",
    "module": "amphora-dataset-recon",
    "campaign_item_id": "DR-LANG-DE",
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
    "directive_obligation": "DR-LANG-DE",
    "claim_tested": (
        "The current DR-LANG-DE deliverable state is complete and accurate for its scope "
        "(finding a miss is CLAIM_REFUTED and is progress)."
    ),
    "claim_verdict": "CLAIM_SURVIVED",
    "refutation_criterion_verbatim": (
        "A spot-check finds a claimed-searched repository with no recorded query and result "
        "sample, a native-language query that is a literal English translation, a cited source "
        "whose recorded license text differs from its live license page, a native-script "
        "citation that fails to resolve, or a previously-supplied candidate in this language "
        "that the fresh search neither rediscovered nor explained."
    ),
    "refutation_criterion_observation_statement": (
        "DID NOT OCCUR against the real deliverable. An independent checker (5 limbs, adapted "
        "for German's Latin script -- see adaptation_note below) was run twice against this "
        "fire's REAL disposition-ledger (9 lines: 1 candidate-intake manifest + 8 candidate "
        "dispositions) and REAL search-record (1 line appended this fire, plus the 3 prior "
        "lines from PROBE-WEB/DR-LANG-ZH/DR-LANG-JA): violation_count=0 both runs, "
        f"byte-identical diagnostic (sha256 {shas['runA_sha']}) -- two-replay gate PASS. None of "
        "the five refutation-criterion limbs fired against the real deliverable: every "
        "claimed-searched url (DECHEMA-Werkstoff-Tabelle, Fraunhofer IFAM, GfKORR, DIN EN ISO "
        "12944, DIN EN ISO 9227, TU Darmstadt tuprints, BAW Merkblatt, Wiley/Kuron 1984) has a "
        "recorded query/result/url this fire; all 12 native de query strings this fire contain "
        "genuine German technical vocabulary and none is byte-identical to its own English "
        "gloss; every license_evidence_quote appears verbatim in this fire's recorded "
        "search-record evidence; every de native_citation appears verbatim in this fire's "
        "recorded search-record evidence (the Latin-script analogue of the zh/ja CJK-presence "
        "check); and the previously-supplied-candidate list is genuinely empty (zero German "
        "candidates exist anywhere in the portfolio's frozen snapshot, feedback catalogs, or "
        "acquisition queue -- explained explicitly in the intake manifest, which the directive's "
        "own 'rediscovered OR explained' clause permits). Verdict: CLAIM_SURVIVED for this "
        "fire's deliverable state."
    ),
    "adaptation_note": (
        "The zh/ja precedent checkers used CJK-character presence to distinguish native-script "
        "queries/citations from literal English translations, because Chinese/Japanese use a "
        "distinct script from English. German uses the SAME Latin script as English, so a "
        "script-presence check would be vacuous (it would never fire, making 'survival' cheap "
        "rather than earned). This fire's checker was redesigned for that reality: rule 2 "
        "(native_query_not_literal_translation) requires the query to contain a curated German "
        "technical-vocabulary marker word AND to differ from its own English gloss field; rule 4 "
        "(native_citation_verbatim_in_evidence) requires every citation to be an exact, "
        "byte-for-byte substring of this fire's own recorded search-record evidence text, "
        "catching silent paraphrase/translation of a citation rather than relying on script "
        "detection. This redesign was validated the same way the rules themselves were: a "
        "positive-control mutant (native_citation_not_verbatim) proves rule 4 fires when a "
        "citation is silently translated, and a positive-control mutant "
        "(literal_english_translation_query) proves rule 2 fires when a query is silently "
        "replaced by its English gloss."
    ),
    "own_draft_bug_caught_and_fixed": (
        "The FIRST run of this fire's own checker against its own first-draft deliverable "
        "correctly fired 4 real violations under rule 4 (native_citation_verbatim_in_evidence): "
        "DR-LANG-DE-02, DR-LANG-DE-03, DR-LANG-DE-04, and DR-LANG-DE-05 each had a native_citation "
        "string that was not byte-present in the recorded search-record evidence text (either "
        "because the exact title/phrase quoted had not yet been copied into the evidence, or "
        "because a punctuation character, e.g. an en-dash vs. a hyphen, did not match the source "
        "verbatim). This is exactly the class of defect the directive's refutation criterion "
        "exists to catch. All four were fixed by adding the exact verbatim source text (search-"
        "result titles and the DIN EN ISO 12944 overview sentence, quoted precisely including "
        "punctuation) into the search-record evidence before any ledger write occurred -- no "
        "ledger or receipt was ever written in the failing state; the builder defers all real "
        "file writes until after every assertion, including the real two-replay gate and all 5 "
        "positive-control mutants, passes."
    ),
    "attack_shape_executed": (
        "Built the full DR-LANG-DE deliverable from 12 real native-de WebSearch calls (amine "
        "cure-kinetics literature, DECHEMA-Werkstoff-Tabelle, DIN EN ISO 12944 offshore mapping, "
        "Fraunhofer IFAM, GfKORR, DIN EN ISO 9227 salt-spray mapping, DIN EN ISO 3001 EEW empty-"
        "result probe, Werkstoffe und Korrosion journal, TIB/TU Darmstadt dissertation search, a "
        "ship-hull DIN-standard empty-result probe, a DSC/Kissinger follow-up, and Farbe und Lack "
        "trade press) plus 5 native-de WebFetch license/metadata evaluations (one hard PDF-"
        "extraction failure, one hard HTTP 402 paywall, three successful evaluative summaries), "
        "scored all 8 candidates deterministically via the existing DR-RUBRIC rubric.v1.json "
        "(reused byte-for-byte, not reimplemented), then wrote and ran an independent second-"
        "party checker implementing all 5 limbs of the pre-committed refutation criterion "
        "(adapted for German's Latin script, see adaptation_note) against the frozen "
        "deliverable. Ran it twice for byte-stability (two-replay gate), then against 5 "
        "independently-planted mutants, one per limb -- including a synthetic previously-"
        "supplied-candidate id for the rediscovery-recall mutant, since this fire genuinely "
        "found zero real prior de candidates to rediscover (proving that rule is non-vacuous "
        "even though it never fires on the real, honestly-empty input). The checker caught 4 "
        "real bugs in its own first draft (see own_draft_bug_caught_and_fixed) before any "
        "receipt was signed."
    ),
    "candidate_intake_manifest": manifest_this_fire,
    "candidate_scores_summary": candidate_scores_summary,
    "dataset_ledger_entries_added_this_fire": 1,
    "dataset_ledger_note": (
        "ONE entry added to dataset-ledger.v1.jsonl this fire -- the FIRST-EVER entry across "
        "the entire DR-LANG-* campaign (PROBE-WEB, DR-RUBRIC, DR-LANG-ZH, DR-LANG-JA all "
        "recorded 0 dataset-ledger entries; their best candidates topped out at 6.33/10, below "
        "the 7.0 RECOMMENDED threshold). DR-LANG-DE-06 (TU Darmstadt open-access CC BY-NC-ND "
        "dissertation with primary DSC/Kissinger cure-kinetics data) scored 9.0/10 and cleared "
        "all three RECOMMENDED floors (overall>=7.0, rights_clarity=8>=5, "
        "acquisition_cost_friction=10>=4). The entry's schema is authored fresh from directive "
        "Section 8.A's field list since no prior dataset-ledger.v1.jsonl precedent existed to "
        "reuse -- see dataset_ledger_entry.schema_note in the ledger line itself."
    ),
    "dataset_ledger_entry_full": dsl_entry_this_fire,
    "disposition_ledger_entries_added_this_fire": 9,
    "disposition_ledger_full_this_fire": [manifest_this_fire] + disp_this_fire,
    "coverage_map_merged_not_overwritten": (
        "coverage-map.v1.json is a single JSON file (not .jsonl), so it cannot be byte-appended; "
        "this fire read the pre-fire file (DR-LANG-ZH's 4 zh gaps + DR-LANG-JA's 5 ja gaps), "
        "preserved every existing gap entry unmodified, and added 7 new de gap entries. Nothing "
        "from any prior fire's gaps[] was removed or rewritten."
    ),
    "coverage_map_full": cm_after,
    "search_record_line_this_fire": sr_line_this_fire,
    "no_acquisition_attestation": sr_line_this_fire["no_acquisition_attestation"],
    "previously_supplied_candidates_rediscovered": {
        "none_found": True,
        "explanation": (
            "Zero previously-supplied German-language candidates exist anywhere in the "
            "portfolio as of this fire's start: checked DR-RUBRIC's frozen "
            "candidate_snapshot.v1.json (C1-C4, all zh/ja), feedback/v1/dataset_sources.json, "
            "feedback/v2-v4/catalog.json (all 'source_intents'/'sources' arrays), and "
            "/home/ubuntu/amphora-cron/data-acquisition-queue.jsonl on xbabe1 (grepped for "
            "german|deutsch|DECHEMA|Fraunhofer|DIN, zero matches). This satisfies the directive's "
            "and this item's own done_criterion via its explicit alternative branch: candidates "
            "must be 'independently rediscovered OR THEIR ABSENCE EXPLAINED' -- the absence is "
            "explained here with the exact source paths checked."
        ),
        "source_paths_checked": manifest_this_fire["source_paths_checked_for_prior_de_candidates"],
    },
    "positive_control": {
        "all_mutants_fired_correctly": all(v["refutation_criterion_fired"] for v in mutants.values()),
        "detected": True,
        "mutants": mutants,
        "summary": "5 independent planted defects, one per refutation-criterion limb; all 5 detected. Mutant 5 (rediscovery_dropped) used a synthetic previously-supplied-candidate id since the real list is genuinely empty this fire.",
    },
    "reproducibility": {
        "byte_identical": True,
        "runA_diagnostic_sha256": shas["runA_sha"],
        "runB_diagnostic_sha256": shas["runA_sha"],
        "two_replay_sha256_gate": "PASS",
        "replay_method": (
            "The checker was invoked twice as independent calls over the same frozen "
            "disposition-ledger and search-record inputs; determinism is by construction (pure "
            "substring/set-membership operations over a fixed German marker-word list, "
            "sorted-key canonical JSON, no wall-clock or random input). This gate certifies the "
            "diagnostic is a byte-stable function of the already-recorded inputs; it does not "
            "and cannot certify that a future live re-fetch of these URLs would return "
            "unchanged content."
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
        {
            "ledger_path": "amphora-dataset-recon/evidence/ledgers/disposition-ledger.v1.jsonl",
            "operation": "append",
            "appended_line_range": [shas["dl_appended_line_start"], shas["dl_appended_line_end"]],
            "prior_prefix_sha256": shas["dl_prior_prefix_sha"],
            "sha256_of_appended_lines": shas["dl_appended_sha"],
            "file_sha256_after": shas["dl_file_sha_after"],
        },
        {
            "ledger_path": "amphora-dataset-recon/evidence/ledgers/dataset-ledger.v1.jsonl",
            "operation": "append (first-ever entry, file created this fire)",
            "appended_line_range": [shas["dsl_appended_line_no"], shas["dsl_appended_line_no"]],
            "prior_prefix_sha256": shas["dsl_prior_prefix_sha"],
            "sha256_of_appended_lines": shas["dsl_appended_sha"],
            "file_sha256_after": shas["dsl_file_sha_after"],
        },
        {
            "ledger_path": "amphora-dataset-recon/evidence/ledgers/coverage-map.v1.json",
            "operation": "merge_full_file_replace",
            "prior_sha256": shas["cm_before_sha"],
            "sha256_of_content_after": shas["cm_after_sha"],
        },
    ],
    "artifact_paths": {
        "build_script": "amphora-dataset-recon/evidence/phase0/repairs/DR-LANG-DE/work/build_dr_lang_de.py",
        "search_record": "amphora-dataset-recon/evidence/ledgers/search-record.v1.jsonl",
        "disposition_ledger": "amphora-dataset-recon/evidence/ledgers/disposition-ledger.v1.jsonl",
        "dataset_ledger": "amphora-dataset-recon/evidence/ledgers/dataset-ledger.v1.jsonl",
        "coverage_map": "amphora-dataset-recon/evidence/ledgers/coverage-map.v1.json",
        "diagnostic_runA": "amphora-dataset-recon/evidence/phase0/repairs/DR-LANG-DE/work/diagnostic.runA.json",
        "diagnostic_runB": "amphora-dataset-recon/evidence/phase0/repairs/DR-LANG-DE/work/diagnostic.runB.json",
        "diagnostic_mutants": "amphora-dataset-recon/evidence/phase0/repairs/DR-LANG-DE/work/diagnostic.mutants.json",
    },
    "artifact_hashes": {
        "search-record.v1.jsonl (appended line only)": shas["sr_appended_sha"],
        "search-record.v1.jsonl (full file, after append)": shas["sr_file_sha_after"],
        "disposition-ledger.v1.jsonl (appended lines 15-23)": shas["dl_appended_sha"],
        "disposition-ledger.v1.jsonl (full file, after append)": shas["dl_file_sha_after"],
        "dataset-ledger.v1.jsonl (appended line only, first-ever)": shas["dsl_appended_sha"],
        "dataset-ledger.v1.jsonl (full file, after append)": shas["dsl_file_sha_after"],
        "coverage-map.v1.json (full file, after merge)": shas["cm_after_sha"],
        "diagnostic.runA.json": shas["runA_sha"],
        "diagnostic.runB.json": shas["runA_sha"],
    },
    "recon_mode_compliance": {
        "read_to_evaluate_only": True,
        "no_downloads_no_caching_no_scraping": True,
        "native_script_citations_preserved": (
            "Every de disposition entry carries native_citation preserving German orthography "
            "(umlauts, eszett) as published; native_citation_romanization is explicitly None for "
            "German entries since German uses Latin script (no romanization step applies, unlike "
            "zh/ja) -- this itself is a disclosed, deliberate difference from the zh/ja schema "
            "usage, not an omission."
        ),
        "translation_confidence_rated_never_silently_accepted": True,
        "units_as_published_conversions_shown": "N/A this fire -- no physical measurement unit conversion required (standards-mapping and dataset-access evaluation only, no quantitative value transcribed from a foreign-unit source, aside from the two direct quantitative quotes from DR-LANG-DE-06 which are reported exactly as published in J/g and kJ/mol, no unit conversion performed or needed).",
        "search_the_open_web_used_websearch_webfetch": True,
        "empty_result_reported_honestly": (
            "din-eew-testdata-annex-de: DIN EN ISO 3001 (epoxy equivalent weight) confirmed as "
            "the direct German/European adoption of ISO 3001:1999, but no open EEW test-data "
            "annex/dataset was found. Recorded as an empty result in coverage-map.v1.json, not "
            "fabricated as a candidate, per directive rule 7."
        ),
        "native_terminology_not_literal_translation": (
            "All 12 native de WebSearch queries this fire composed from practitioner domain "
            "terminology (e.g. Härtungskinetik 'cure kinetics', Salzsprühnebelprüfung 'salt "
            "spray test', Epoxidäquivalent 'epoxy equivalent', Korrosionsschutz 'corrosion "
            "protection', Unterwasseranstrich 'underwater paint') rather than word-for-word "
            "translation of an English keyword list; verified this fire by the checker's German "
            "marker-word + gloss-divergence rule on every recorded de query."
        ),
        "credited_artifact_is_dsse_receipt": True,
        "ledger_lines_appended_this_fire": 10,
    },
    "does_not_close": [
        "No promotion, procurement, safety, synthesis, or freedom-to-operate authority.",
        "DR-LANG-DE-06's CC BY-NC-ND license carries a real NonCommercial restriction disclosed "
        "in its rights_note -- the dataset-ledger RECOMMENDED verdict is a rubric-mechanical "
        "outcome under the closed vocabulary, not a claim that this portfolio may freely "
        "repackage the dissertation's figures/data in a commercial deliverable without the "
        "human next-action (author/TU Darmstadt clearance) named in the entry.",
        "No ship-hull-specific DIN antifouling standard number was found (unlike the general "
        "DIN EN ISO 12944) -- disclosed as a real scope gap, mirroring the identical ja-fire "
        "finding for JIS, not papered over.",
        "DR-LANG-DE-07 (BAW Merkblatt MKWAS, the single highest-gap-fit-by-title candidate) "
        "could not be content-evaluated this fire -- WebFetch failed to extract its PDF text. "
        "This is an honest evidence-quality gap, scored conservatively (extracted_or_estimated / "
        "neither_stated) rather than assumed favorable, exactly mirroring DR-LANG-JA-06.",
        "DR-LANG-DE-08 (Kuron 1984, Werkstoffe und Korrosion) is blocked by a hard, directly-"
        "confirmed HTTP 402 paywall -- content unconfirmed, scored conservatively.",
        "The checker's live-evidence comparison is only as strong as this fire's own recorded "
        "WebFetch/WebSearch transcripts; it does not re-fetch pages a third time at receipt-"
        "build time, so a live page that changed AFTER this fire's queries ran would not be "
        "caught until a future fire re-queries it -- disclosed, not hidden.",
        "max_fires=2 for this item; this is fire 1 of at most 2. If a future spot-check finds a "
        "real gap in this deliverable, that is CLAIM_REFUTED and is progress, per the item's own "
        "claim framing.",
    ],
    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY repair-done receipt under evidence/phase0/repairs/DR-LANG-DE/done/",
        "derives_pinned_trust_store_key_id": bool(eval_pin),
    },
}

body = json.dumps(body_obj, indent=2, sort_keys=True, ensure_ascii=False).encode("utf-8")
ptype = "application/vnd.amphora.dataset-recon-repair-done-dr-lang-de+json"
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
out = ITEM / "done" / "dr-lang-de-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False))

Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))

print("WROTE", out)
print("claim_verdict", body_obj["claim_verdict"])
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
