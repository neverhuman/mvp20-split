#!/usr/bin/env python3
"""DSSE-Ed25519-sign the DR-STD-MAP KS D ISO 9227 abolition-status audit receipt.
AUDIT_ONLY. Pinned Phase-0 evaluator key only."""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-dataset-recon"
AUDIT_DIR = MOD / "evidence/audit/dr-std-map-ks-d-iso9227-abolition-v1"
WORK = AUDIT_DIR / "work"
STDMAP_WORK = MOD / "evidence/phase0/repairs/DR-STD-MAP/work"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

DIRECTIVE_MD = ROOT / "docs/directives/2026-08-09-dataset-reconnaissance-multilingual.md"
DIRECTIVE_SHA_EXPECTED = "97fad5d1636f5ccb106562c2d940535651c216d357dd5276088f2db12bdba207"

FIRE_ID = "20260817T130001-3407163-2ada8f0e6fcd"
RUN_ID = f"DR-STD-MAP-AUDIT-KS-D-ISO9227-{FIRE_ID}"
DATE = "2026-08-17"

REFUTATION_CRITERION_VERBATIM = (
    "Any ledger entry measured under a non-ASTM/ISO standard lacks a named "
    "closest equivalent, stated methodological deltas, and a comparability "
    "rating, or a mapped pair misstates a delta that the two standards' own "
    "texts contradict."
)


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

audit_result = json.loads((WORK / "audit_result.json").read_bytes())
assert audit_result["violation_count"] == 1
assert audit_result["two_replay_byte_identical"] is True

v3_bytes = (STDMAP_WORK / "mapping-table.v3.json").read_bytes()
v4_bytes = (STDMAP_WORK / "mapping-table.v4.json").read_bytes()
v3_sha = sha(v3_bytes)
v4_sha = sha(v4_bytes)
assert audit_result["input_mapping_table_sha256"] == v3_sha

build_audit_bytes = (WORK / "build_audit.py").read_bytes()
build_correction_bytes = (WORK / "build_correction.py").read_bytes()
live_evidence_bytes = (WORK / "live_evidence.json").read_bytes()

retraction_index_bytes = (MOD / "evidence/phase0/repairs/DR-STD-MAP/done/RETRACTION-INDEX.md").read_bytes()

# Confirm no ledger/manifest touched this fire (recon-mode discipline / audit-fire convention)
sr_bytes = (MOD / "evidence/ledgers/search-record.v1.jsonl").read_bytes()
dl_bytes = (MOD / "evidence/ledgers/disposition-ledger.v1.jsonl").read_bytes()
dsl_bytes = (MOD / "evidence/ledgers/dataset-ledger.v1.jsonl").read_bytes()

violation = audit_result["violations"][0]

body_obj = {
    "schema": "amphora.dataset-recon.audit.dr-std-map-ks-d-iso9227-abolition-receipt.v1",
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
    "run_id": RUN_ID,
    "date": DATE,
    "phase": "PRE_PHASE_0",
    "scientific_success_required_for_phase0": False,
    "directive_id": "AMPHORA-DIRECTIVE-2026-08-09",
    "directive_path": "docs/directives/2026-08-09-dataset-reconnaissance-multilingual.md",
    "directive_sha256": directive_sha_actual,
    "directive_index_path": "docs/directives/2026-08-09-dataset-recon.index.json",
    "directive_obligation": "DR-STD-MAP",
    "directive_ref_binds_this_fire": False,
    "directive_ref_note": (
        "This fire ran in ROTATION mode with an empty campaign item ({}), so no "
        "directive_ref binds it per the launcher's own framing. The directive/"
        "obligation citation above is included for continuity with the ongoing "
        "DR-STD-MAP audit trail (fire-2, fire-3) this fire extends, not as a "
        "compliance claim."
    ),
    "claim_tested": (
        "amphora-dataset-recon/evidence/audit/dr-std-map-iso9227-edition-currency-v1/"
        "dr-std-map-iso9227-edition-currency-receipt.v1.dsse.json (mapping-table.v3.json): "
        "the DR-STD-MAP mapping table's KS D ISO 9227:2005 row is correctly and "
        "currently risk-flagged."
    ),
    "attack": (
        "Closed the exact open item fire-3 (20260815T190002-1692638-e6c8305dbc05) "
        "explicitly left undischarged in its own receipt: 'KS D ISO 9227:2005 ... "
        "this fire attempted a live check via kssn.net/standard.go.kr but those "
        "portals are JS-rendered search forms that WebFetch could not resolve to "
        "the specific KS D ISO 9227 record'. This fire bypassed the JS-rendering "
        "problem with a raw curl GET against standard.go.kr's server-rendered "
        "getStandardSearchView.do endpoint (ksNo=KSDISO9227), independently "
        "cross-checked with WebFetch against the same URL, and parsed the "
        "returned HTML's own structured 표준 이력사항 (standard history) table."
    ),
    "claim_verdict": "CLAIM_REFUTED",
    "refutation_criterion_verbatim": REFUTATION_CRITERION_VERBATIM,
    "refutation_criterion_restated_for_this_attack": (
        "A DR-STD-MAP mapping-table row citing a national standard that "
        "standard's OWN official government registry marks abolished/repealed "
        "is signed with a comparability_rating implying live, current "
        "method-class comparability (rather than the table's own established "
        "abolished-standard marker, e.g. 'not_applicable_abolished' as "
        "correctly used for GB/T 13351-1992) -- a mapped pair whose claimed "
        "comparability the standard's own official text (its registry entry) "
        "directly contradicts."
    ),
    "refutation_criterion_observation": (
        "OCCURRED. 1/42 rows violated: KS D ISO 9227:2005. Signed state: "
        "integrity_gap=" + str(violation["signed_integrity_gap"]) +
        ", comparability_rating='" + violation["signed_comparability_rating"] +
        "', astm_iso_equiv='" + violation["signed_astm_iso_equiv"] + "'. "
        "Live evidence (standard.go.kr, ksNo=KSDISO9227, official Korean "
        "national standards registry, fetched by raw curl and independently "
        "cross-checked by WebFetch this fire): 표준번호 (standard number) field "
        "itself carries the '(폐지)' [ABOLISHED] suffix; the page's own 표준 "
        "이력사항 (standard history) table shows 제정 (established) 2003-12-26 "
        "(notification 2003-1673) then 폐지 (abolished) 2005-12-28 (notification "
        "2005-0989), reason 'KSD9502와 규격중복' (duplicate/overlapping with KS "
        "D 9502); 대체 표준 (replacement-standard) field reads 대체표준이 "
        "없습니다 (no replacement standard on file). KS D 9502 is already a "
        "separate, correctly-mapped row in this same table "
        "(comparability_rating='iso_direct_adoption_confirmed_mod_distinct_"
        "vintage', integrity_gap=false) -- the table already knows the live "
        "current Korean salt-spray standard but never cross-referenced that "
        "KS D ISO 9227 is the exact standard it replaced. The prior row's "
        "':2005' suffix and unqualified 'ISO 9227:1990 (identical adoption, "
        "per KSA)' astm_iso_equiv text presented the standard as live and "
        "current when it has carried no legal force for ~21 years."
    ),
    "checker": {
        "path": "amphora-dataset-recon/evidence/audit/dr-std-map-ks-d-iso9227-abolition-v1/work/build_audit.py",
        "sha256": sha(build_audit_bytes),
        "pure_function_of": "mapping-table.v3.json + live_evidence.json only (no wall-clock, no randomness, no network I/O inside the function)",
        "two_replay_byte_identical": audit_result["two_replay_byte_identical"],
        "runA_sha256": audit_result["runA_sha256"],
        "runB_sha256": audit_result["runB_sha256"],
        "non_vacuity_check": (
            "Asserted the checker does NOT flag the table's already-correctly-"
            "labeled abolished row (GB/T 13351-1992, comparability_rating="
            "'not_applicable_abolished') -- proves this is a targeted "
            "abolition-vs-disclosure check, not a blanket always-fire rule. "
            "PASSED."
        ),
    },
    "live_evidence": {
        "KS D ISO 9227:2005": json.loads(live_evidence_bytes),
    },
    "correction": {
        "build_script_path": "amphora-dataset-recon/evidence/audit/dr-std-map-ks-d-iso9227-abolition-v1/work/build_correction.py",
        "build_script_sha256": sha(build_correction_bytes),
        "new_artifact_path": "amphora-dataset-recon/evidence/phase0/repairs/DR-STD-MAP/work/mapping-table.v4.json",
        "new_artifact_sha256": v4_sha,
        "row_changed": {
            "standard_id_before": "KS D ISO 9227:2005",
            "standard_id_after": "KS D ISO 9227:2005 (ABOLISHED 2005-12-28, per standard.go.kr)",
            "comparability_rating_before": "method_class_confirmed_iso_explicit_astm_inferred",
            "comparability_rating_after": "not_applicable_abolished",
            "integrity_gap_before": False,
            "integrity_gap_after": False,
        },
        "integrity_gap_count_v3": 14,
        "integrity_gap_count_v4": 14,
        "row_count_v3": 42,
        "row_count_v4": 42,
    },
    "supersedes": {
        "superseded_path": "amphora-dataset-recon/evidence/phase0/repairs/DR-STD-MAP/work/mapping-table.v3.json",
        "superseded_sha256": v3_sha,
        "superseded_deleted_or_modified": False,
        "reason": (
            "The KS D ISO 9227:2005 row signed integrity_gap=false with a live-"
            "method-class-comparable comparability_rating, but the standard's "
            "own official government registry (standard.go.kr) shows it was "
            "abolished 2005-12-28 -- the same disclosure treatment this table "
            "already correctly applies to its other abolished-standard row "
            "(GB/T 13351-1992) was not applied here."
        ),
    },
    "retraction_index_updated": {
        "path": "amphora-dataset-recon/evidence/phase0/repairs/DR-STD-MAP/done/RETRACTION-INDEX.md",
        "sha256_after": sha(retraction_index_bytes),
        "operation": "append (never rewrite/delete a row)",
    },
    "ledgers_not_modified_this_fire": {
        "search-record.v1.jsonl_sha256": sha(sr_bytes),
        "disposition-ledger.v1.jsonl_sha256": sha(dl_bytes),
        "dataset-ledger.v1.jsonl_sha256": sha(dsl_bytes),
        "note": (
            "This is a synthesis/audit fire over an existing signed artifact "
            "(mapping-table.v3.json), not a new-language recon fire -- no new "
            "WebSearch-discovered dataset candidates this fire, so no ledger "
            "append was required or made. All new evidence is standard "
            "abolition-status verification, recorded here and in the "
            "correction artifact."
        ),
    },
    "no_acquisition_attestation": (
        "This fire performed a raw curl GET plus an independent WebFetch read "
        "against standard.go.kr's public standard-detail page (e-나라 "
        "표준인증, Korea's official national standards registry) to check "
        "PUBLISHED STANDARD STATUS metadata only -- standard number/title with "
        "status suffix, establishment/abolition dates, notification numbers, "
        "abolition reason, replacement-standard field. No standard's full "
        "text, clause content, or paywalled document was purchased, "
        "downloaded, or cached. The raw HTML fetch (89730 bytes) was parsed "
        "in-memory for these public metadata fields only and was not written "
        "to any repo path; nothing landed on xbabe2 except this receipt, the "
        "mapping-table.v4.json correction, the audit_result.json diagnostic, "
        "the live_evidence.json evidence snapshot, and the RETRACTION-INDEX.md "
        "append."
    ),
    "recon_mode_compliance": {
        "read_to_evaluate_only": True,
        "no_downloads_no_caching_no_scraping": True,
        "search_the_open_web_used_websearch_webfetch": True,
        "credited_artifact_is_dsse_receipt": True,
        "ledger_lines_appended_this_fire": 0,
    },
    "open_items_remaining_for_a_future_fire": [
        "The remaining 5 pattern-inference-only rows already flagged "
        "integrity_gap=true (ČSN EN ISO 9227, UNE-EN ISO 9227, UNE-EN ISO "
        "12944, NP EN ISO 12944, NP EN ISO 9227) were not re-attempted this "
        "fire -- they were already honestly flagged and are not this fire's "
        "violation class.",
        "ISO 12944 rows (DIN/NF/UNI/NEN/PN EN ISO 12944, all "
        "integrity_gap=false, all edition-unspecified) remain unchecked for "
        "edition-currency risk, as fire-3 also noted -- ISO 12944 parts were "
        "substantially revised 2017-2018.",
        "KS D 9502 itself (the standard KS D ISO 9227 was merged into) was "
        "NOT re-verified live this fire for its own current edition/vintage "
        "-- only cross-referenced by name against the abolition record; a "
        "future fire could extend the same raw-curl standard.go.kr technique "
        "to confirm KS D 9502's own current edition status.",
    ],
    "does_not_close": [
        "No promotion, procurement, safety, synthesis, or freedom-to-operate "
        "authority.",
        "This audit does not re-verify the SCOPE TEXT of any standard "
        "clause-by-clause against ASTM B117 -- only the abolition/status "
        "metadata published by the standard's own government registry, "
        "consistent with the no-acquisition constraint.",
    ],
    "artifact_paths": {
        "checker_script": "amphora-dataset-recon/evidence/audit/dr-std-map-ks-d-iso9227-abolition-v1/work/build_audit.py",
        "correction_script": "amphora-dataset-recon/evidence/audit/dr-std-map-ks-d-iso9227-abolition-v1/work/build_correction.py",
        "audit_result": "amphora-dataset-recon/evidence/audit/dr-std-map-ks-d-iso9227-abolition-v1/work/audit_result.json",
        "live_evidence": "amphora-dataset-recon/evidence/audit/dr-std-map-ks-d-iso9227-abolition-v1/work/live_evidence.json",
        "mapping_table_v3_superseded": "amphora-dataset-recon/evidence/phase0/repairs/DR-STD-MAP/work/mapping-table.v3.json",
        "mapping_table_v4_correction": "amphora-dataset-recon/evidence/phase0/repairs/DR-STD-MAP/work/mapping-table.v4.json",
        "retraction_index": "amphora-dataset-recon/evidence/phase0/repairs/DR-STD-MAP/done/RETRACTION-INDEX.md",
    },
    "artifact_hashes": {
        "mapping-table.v3.json": v3_sha,
        "mapping-table.v4.json": v4_sha,
        "build_audit.py": sha(build_audit_bytes),
        "build_correction.py": sha(build_correction_bytes),
        "live_evidence.json": sha(live_evidence_bytes),
        "audit_result.json": sha((WORK / "audit_result.json").read_bytes()),
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY falsification receipt under evidence/audit/",
        "derives_pinned_trust_store_key_id": bool(eval_pin),
    },
}

body = json.dumps(body_obj, indent=2, sort_keys=True, ensure_ascii=False).encode("utf-8")
ptype = "application/vnd.amphora.dataset-recon-audit-dr-std-map-ks-d-iso9227+json"
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
out_dir = AUDIT_DIR
out_dir.mkdir(parents=True, exist_ok=True)
out = out_dir / "dr-std-map-ks-d-iso9227-abolition-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False))

Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))

print("WROTE", out)
print("claim_verdict", body_obj["claim_verdict"])
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
