#!/usr/bin/env python3
"""DSSE-Ed25519-sign the DR-LANG-IBERIAN campaign-item done receipt for
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
ITEM = MOD / "evidence/phase0/repairs/DR-LANG-IBERIAN"
WORK = ITEM / "work"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

DIRECTIVE_MD = ROOT / "docs/directives/2026-08-09-dataset-reconnaissance-multilingual.md"
DIRECTIVE_SHA_EXPECTED = "97fad5d1636f5ccb106562c2d940535651c216d357dd5276088f2db12bdba207"

FIRE_ID = "20260810T120002-779591-d566098d9684"
RUN_ID = f"DR-LANG-IBERIAN-{FIRE_ID}"
DATE = "2026-08-10"
PREVIOUSLY_SUPPLIED_ID = "PRIOR-BARRIER-DIFFUSION-POLIMEROS-01"


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
assert len(disp_this_fire) == 6
cm_after = json.loads(cm_bytes)
sr_lines = [json.loads(l) for l in sr_bytes.decode("utf-8").splitlines() if l.strip()]
sr_line_this_fire = next(l for l in sr_lines if l.get("fire_id") == FIRE_ID)
dsl_lines = [json.loads(l) for l in dsl_bytes.decode("utf-8").splitlines() if l.strip()]
dsl_entries_this_fire = [l for l in dsl_lines if l.get("fire_id") == FIRE_ID]
assert len(dsl_entries_this_fire) == 3
assert {e["candidate_id"] for e in dsl_entries_this_fire} == {"DR-LANG-IBERIAN-01", "DR-LANG-IBERIAN-02", "DR-LANG-IBERIAN-05"}
rediscovery_entry = next(e for e in dsl_entries_this_fire if e["candidate_id"] == "DR-LANG-IBERIAN-01")
assert rediscovery_entry.get("rediscovers") == PREVIOUSLY_SUPPLIED_ID

candidate_scores_summary = ", ".join(
    f"{d['candidate_id']}={d['disposition']['verdict']}({d['rubric_overall_score']})"
    for d in sorted(disp_this_fire, key=lambda x: -x["rubric_overall_score"])
)

body_obj = {
    "schema": "amphora.dataset-recon-repair-done-dr-lang-iberian.v1",
    "module": "amphora-dataset-recon",
    "campaign_item_id": "DR-LANG-IBERIAN",
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
    "directive_obligation": "DR-LANG-IBERIAN",
    "claim_tested": (
        "The current DR-LANG-IBERIAN deliverable state is complete and accurate for its scope "
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
        "for Spanish and Portuguese's shared Latin script -- see adaptation_note below) was run "
        "twice against this fire's REAL disposition-ledger (7 lines: 1 candidate-intake manifest "
        "+ 6 candidate dispositions) and REAL search-record (8 lines: 7 prior lines from "
        "PROBE-WEB/DR-LANG-ZH/DR-LANG-JA/DR-LANG-DE/DR-LANG-RU/DR-LANG-KO/DR-LANG-FR plus 1 line "
        f"appended this fire): violation_count=0 both runs, byte-identical diagnostic (sha256 "
        f"{shas['runA_sha']}) -- two-replay gate PASS. None of the five refutation-criterion "
        "limbs fired against the real deliverable: every claimed-searched url (SciELO Polimeros, "
        "LNEG repository x2, LNEG journal homepage, Dialnet x2, CENIM) has a recorded query/"
        "result/url this fire; all 14 native es/pt query strings this fire contain genuine "
        "Spanish/Portuguese technical vocabulary and none is byte-identical to its own English "
        "gloss; every license_evidence_quote appears verbatim in this fire's recorded "
        "search-record evidence; every es/pt native_citation appears verbatim in this fire's "
        "recorded search-record evidence (the Latin-script analogue of the zh/ja CJK-presence "
        "check, reused byte-for-byte in structure from the de/fr fires' adaptation); and -- for "
        "the FIRST time this campaign -- a REAL (non-synthetic) previously-supplied candidate "
        f"({PREVIOUSLY_SUPPLIED_ID!r}, found live in amphora-redteam-audit's "
        "barrier-diffusion-timelag-fickian-ccby-v1/diagnostic.canonical.json) was independently "
        "rediscovered by DR-LANG-IBERIAN-01, confirmed by rule 5 finding a matching rediscovers "
        "link. Verdict: CLAIM_SURVIVED for this fire's deliverable state."
    ),
    "adaptation_note": (
        "Spanish and Portuguese use the SAME Latin script as English (and as German/French, the "
        "prior Latin-script adaptation precedent), so a script-presence check would be vacuous. "
        "This fire reused the de/fr fires' redesign exactly, extended to a combined es+pt marker "
        "vocabulary: rule 2 (native_query_not_literal_translation) requires the query to contain "
        "a curated Spanish-or-Portuguese technical-vocabulary marker word AND to differ from its "
        "own English gloss field; rule 4 (native_citation_verbatim_in_evidence) requires every "
        "citation to be an exact, byte-for-byte substring of this fire's own recorded "
        "search-record evidence text, for BOTH es and pt entries. Validated the same way: a "
        "positive-control mutant (native_citation_not_verbatim) proves rule 4 fires when a "
        "citation is silently translated, and a positive-control mutant "
        "(literal_english_translation_query) proves rule 2 fires when a query is silently "
        "replaced by its English gloss."
    ),
    "attack_shape_executed": (
        "Built the full DR-LANG-IBERIAN deliverable from 14 real native-es/pt WebSearch calls "
        "(amine cure-kinetics literature in both languages, CENIM/CSIC, LNEC/LNEG, UNE-EN ISO "
        "9227 and NP EN ISO 9227 salt-spray mapping, NP EN ISO 3001 EEW empty-result probe, two "
        "ship-hull-antifouling empty-result probes, ABNT/NBR ISO 12944 offshore mapping, TESEO/ "
        "Dialnet DSC/Kissinger thesis search, and a REDISCOVERY-targeted pair of queries for the "
        "previously-supplied Polimeros/SciELO source) plus 9 native-es/pt WebFetch license/"
        "metadata evaluations (2 raw-PDF-binary extraction failures, 1 TLS-certificate failure "
        "against www.tdx.cat worked around via a Dialnet mirror rather than left as a dead end, "
        "6 successful evaluative summaries), scored all 6 candidates deterministically via the "
        "existing DR-RUBRIC rubric.v1.json (reused byte-for-byte, not reimplemented), then wrote "
        "and ran an independent second-party checker implementing all 5 limbs of the "
        "pre-committed refutation criterion (adapted for Spanish/Portuguese's Latin script per "
        "adaptation_note) against the frozen deliverable. Ran it twice for byte-stability "
        "(two-replay gate), then against 5 independently-planted mutants, one per limb -- "
        "including, for the first time this campaign, a REAL (not synthetic) previously-supplied-"
        "candidate id for the rediscovery-recall mutant, since this fire found a genuine one via "
        "a repo-wide grep that surfaced amphora-redteam-audit's own use of a Spanish/Portuguese-"
        "language source."
    ),
    "candidate_intake_manifest": manifest_this_fire,
    "candidate_scores_summary": candidate_scores_summary,
    "dataset_ledger_entries_added_this_fire": 3,
    "dataset_ledger_note": (
        "THREE entries added to dataset-ledger.v1.jsonl this fire: DR-LANG-IBERIAN-01 (the "
        "rediscovered SciELO/Polimeros DGEBA/TETA water-absorption source, pt), "
        "DR-LANG-IBERIAN-02 (LNEG's marine antifouling-paint-scheme article, pt), and "
        "DR-LANG-IBERIAN-05 (UPC's elastomer-modified-epoxy DSC cure-kinetics thesis, es). "
        "IBERIAN-01's RECOMMENDED verdict is a disclosed mechanical-rubric artifact identical in "
        "kind to the DR-LANG-FR-04 precedent: it scores fully_redundant (0/10) on uniqueness "
        "because it duplicates a source the portfolio ALREADY uses, yet still clears RECOMMENDED "
        "on the strength of its other 5 dimensions (open CC BY license, direct download, primary "
        "experimental data, named-module-gap fit, high translation confidence) -- included "
        "specifically because directive rule 'independently rediscovered' requires confirming, "
        "not skipping, previously-supplied sources. It also surfaced a genuine, UNRESOLVED "
        "numeric discrepancy against the prior citation (see integrity_risk_note on that "
        "candidate) -- an honest, interesting finding, not silently smoothed over."
    ),
    "dataset_ledger_entries_full": dsl_entries_this_fire,
    "rediscovery_result": {
        "previously_supplied_id": PREVIOUSLY_SUPPLIED_ID,
        "found_in": "amphora-redteam-audit/benchmarks/barrier-diffusion-timelag-fickian-ccby-v1/diagnostic.canonical.json (and byte-identical diagnostic.runB.json), doi_or_id field 'Polimeros/scielo HsgPHhmYmRSPPKQPqKFLdck'",
        "rediscovered_by": "DR-LANG-IBERIAN-01 (dataset-ledger DSL-01)",
        "rediscovered": True,
        "numeric_discrepancy_flagged": True,
        "numeric_discrepancy_detail": (
            "Prior citation: D=2.17e-11 m2/s, M_inf=4.82% at phr13 (stoichiometric). This fire's "
            "WebFetch AI-summarized extraction of the same live article: M_inf range 2.78%-6.56%, "
            "D range 0.8-3.94e-7 mm2/s (= 8e-14 to 3.94e-13 m2/s) across all 8 tested ratios. The "
            "cited phr13 point is not obviously contained in the converted range -- UNRESOLVED, "
            "not silently reconciled, since no-acquisition discipline forbids downloading the "
            "full article/table to isolate the exact phr13 row and confirm units this fire. "
            "Flagged as next_human_action on DR-LANG-IBERIAN-01."
        ),
    },
    "disposition_ledger_entries_added_this_fire": 7,
    "disposition_ledger_full_this_fire": [manifest_this_fire] + disp_this_fire,
    "coverage_map_merged_not_overwritten": (
        "coverage-map.v1.json is a single JSON file (not .jsonl), so it cannot be byte-appended; "
        "this fire read the pre-fire file (zh + ja + de + ru + ko + fr gaps), preserved every "
        "existing gap entry unmodified, and added 8 new iberian gap entries. Nothing from any "
        "prior fire's gaps[] was removed or rewritten."
    ),
    "coverage_map_full": cm_after,
    "search_record_line_this_fire": sr_line_this_fire,
    "no_acquisition_attestation": sr_line_this_fire["no_acquisition_attestation"],
    "previously_supplied_candidates_rediscovered": {
        "none_found": False,
        "explanation": (
            "For the first time this campaign, a REAL previously-supplied Spanish/Portuguese-"
            "language candidate was found and independently rediscovered -- see "
            "rediscovery_result above. Checked the same source-path set as every prior DR-LANG "
            "fire (DR-RUBRIC's frozen candidate_snapshot.v1.json, feedback/v1-v4 catalogs, "
            "xbabe1's data-acquisition-queue.jsonl -- zero es/pt matches in all of those) PLUS a "
            "repo-wide grep across every module for scielo|redalyc|dialnet|.es/|.pt/|.br/, which "
            "is what surfaced the real candidate inside amphora-redteam-audit's own benchmark "
            "diagnostics -- a source path no prior DR-LANG fire checked. This satisfies the "
            "directive's 'independently rediscovered OR THEIR ABSENCE EXPLAINED' clause via the "
            "rediscovery branch."
        ),
        "source_paths_checked": manifest_this_fire["source_paths_checked_for_prior_iberian_candidates"],
    },
    "positive_control": {
        "all_mutants_fired_correctly": all(v["refutation_criterion_fired"] for v in mutants.values()),
        "detected": True,
        "mutants": mutants,
        "summary": (
            "5 independent planted defects, one per refutation-criterion limb; all 5 detected. "
            "Mutant 5 (rediscovery_dropped) used the REAL previously-supplied-candidate id "
            f"({PREVIOUSLY_SUPPLIED_ID!r}) this time, not a synthetic stand-in -- the first time "
            "this campaign the rediscovery-recall rule has been exercised against genuine, "
            "non-synthetic data."
        ),
    },
    "reproducibility": {
        "byte_identical": True,
        "runA_diagnostic_sha256": shas["runA_sha"],
        "runB_diagnostic_sha256": shas["runA_sha"],
        "two_replay_sha256_gate": "PASS",
        "replay_method": (
            "The checker was invoked twice as independent calls over the same frozen "
            "disposition-ledger and search-record inputs; determinism is by construction (pure "
            "substring/set-membership operations over a fixed Spanish+Portuguese marker-word "
            "list, sorted-key canonical JSON, no wall-clock or random input). This gate certifies "
            "the diagnostic is a byte-stable function of the already-recorded inputs; it does not "
            "and cannot certify that a future live re-fetch of these URLs would return unchanged "
            "content."
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
            "operation": "append",
            "appended_line_range": [shas["dsl_appended_line_start"], shas["dsl_appended_line_end"]],
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
        "build_script": "amphora-dataset-recon/evidence/phase0/repairs/DR-LANG-IBERIAN/work/build_dr_lang_iberian.py",
        "search_record": "amphora-dataset-recon/evidence/ledgers/search-record.v1.jsonl",
        "disposition_ledger": "amphora-dataset-recon/evidence/ledgers/disposition-ledger.v1.jsonl",
        "dataset_ledger": "amphora-dataset-recon/evidence/ledgers/dataset-ledger.v1.jsonl",
        "coverage_map": "amphora-dataset-recon/evidence/ledgers/coverage-map.v1.json",
        "diagnostic_runA": "amphora-dataset-recon/evidence/phase0/repairs/DR-LANG-IBERIAN/work/diagnostic.runA.json",
        "diagnostic_runB": "amphora-dataset-recon/evidence/phase0/repairs/DR-LANG-IBERIAN/work/diagnostic.runB.json",
        "diagnostic_mutants": "amphora-dataset-recon/evidence/phase0/repairs/DR-LANG-IBERIAN/work/diagnostic.mutants.json",
    },
    "artifact_hashes": {
        "search-record.v1.jsonl (appended line only)": shas["sr_appended_sha"],
        "search-record.v1.jsonl (full file, after append)": shas["sr_file_sha_after"],
        "disposition-ledger.v1.jsonl (appended lines)": shas["dl_appended_sha"],
        "disposition-ledger.v1.jsonl (full file, after append)": shas["dl_file_sha_after"],
        "dataset-ledger.v1.jsonl (appended lines)": shas["dsl_appended_sha"],
        "dataset-ledger.v1.jsonl (full file, after append)": shas["dsl_file_sha_after"],
        "coverage-map.v1.json (full file, after merge)": shas["cm_after_sha"],
        "diagnostic.runA.json": shas["runA_sha"],
        "diagnostic.runB.json": shas["runA_sha"],
    },
    "recon_mode_compliance": {
        "read_to_evaluate_only": True,
        "no_downloads_no_caching_no_scraping": True,
        "native_script_citations_preserved": (
            "Every es/pt disposition entry carries native_citation preserving Spanish/Portuguese "
            "orthography (accents, tildes) as published; native_citation_romanization is "
            "explicitly None for all es/pt entries since both languages use Latin script (no "
            "romanization step applies, unlike zh/ja/ko/ru) -- matching the de/fr fires' "
            "identical disclosed schema choice."
        ),
        "translation_confidence_rated_never_silently_accepted": True,
        "units_as_published_conversions_shown": (
            "The DR-LANG-IBERIAN-01 D-value conversion (0.8-3.94e-7 mm2/s -> 8e-14 to 3.94e-13 "
            "m2/s) is shown explicitly with the conversion factor (1 mm2/s = 1e-6 m2/s) rather "
            "than left in mixed units, precisely so the resulting discrepancy against the prior "
            "citation's m2/s figure is visible rather than hidden by a silent unit switch -- "
            "directly actioning directive rule 5's locale/unit-hazard discipline."
        ),
        "search_the_open_web_used_websearch_webfetch": True,
        "empty_result_reported_honestly": (
            "salt-spray-standard-mapping-iberian, eew-testdata-annex-iberian, and "
            "ship-hull-antifouling-standard-mapping-iberian: all three confirmed as direct "
            "UNE-EN/NP-EN/NBR adoptions of the underlying ISO standard with no open test-data "
            "annex or Iberian-specific standard number found. Recorded as empty results in "
            "coverage-map.v1.json, not fabricated as candidates, per directive rule 7."
        ),
        "native_terminology_not_literal_translation": (
            "All 14 native es/pt WebSearch queries this fire composed from practitioner domain "
            "terminology (e.g. curado/cura 'curing', niebla salina/nevoeiro salino 'salt spray', "
            "equivalente epóxido 'epoxy equivalent', antiincrustante/antifouling, difusão "
            "'diffusion') rather than word-for-word translation of an English keyword list; "
            "verified this fire by the checker's Spanish+Portuguese marker-word + "
            "gloss-divergence rule on every recorded es/pt query."
        ),
        "credited_artifact_is_dsse_receipt": True,
        "ledger_lines_appended_this_fire": 11,
    },
    "does_not_close": [
        "No promotion, procurement, safety, synthesis, or freedom-to-operate authority.",
        "DR-LANG-IBERIAN-01's RECOMMENDED verdict reflects a mechanical rubric artifact (a fully "
        "redundant rediscovery scoring maximally on 5 of 6 dimensions) -- it is a REDISCOVERY of "
        "an already-in-use source, not new coverage. Disclosed prominently, not silently "
        "absorbed.",
        "The DGEBA/TETA D-value/unit discrepancy this fire surfaced against the prior citation "
        "is UNRESOLVED, not a confirmed error in either source -- a human with full-text access "
        "is needed to isolate the exact phr13 row and settle it.",
        "DR-LANG-IBERIAN-02 (LNEG antifouling paint) is adjacent-domain (aluminum substrate, not "
        "the portfolio's steel/DGEBA-amine class) -- disclosed, not conflated.",
        "www.tdx.cat's TLS certificate failure was worked around via a Dialnet mirror this fire "
        "but not independently re-confirmed via raw curl from xbabe1 (the PROBE-WEB precedent "
        "for CNKI/HAL) -- open for a future fire.",
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
        "used_for": "AUDIT_ONLY repair-done receipt under evidence/phase0/repairs/DR-LANG-IBERIAN/done/",
        "derives_pinned_trust_store_key_id": bool(eval_pin),
    },
}

body = json.dumps(body_obj, indent=2, sort_keys=True, ensure_ascii=False).encode("utf-8")
ptype = "application/vnd.amphora.dataset-recon-repair-done-dr-lang-iberian+json"
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
out = ITEM / "done" / "dr-lang-iberian-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False))

Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))

print("WROTE", out)
print("claim_verdict", body_obj["claim_verdict"])
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
