#!/usr/bin/env python3
"""DSSE-Ed25519-sign the DR-STD-MAP ISO-9227 edition-currency audit receipt.
AUDIT_ONLY. Pinned Phase-0 evaluator key only."""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-dataset-recon"
AUDIT_DIR = MOD / "evidence/audit/dr-std-map-iso9227-edition-currency-v1"
WORK = AUDIT_DIR / "work"
STDMAP_WORK = MOD / "evidence/phase0/repairs/DR-STD-MAP/work"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

DIRECTIVE_MD = ROOT / "docs/directives/2026-08-09-dataset-reconnaissance-multilingual.md"
DIRECTIVE_SHA_EXPECTED = "97fad5d1636f5ccb106562c2d940535651c216d357dd5276088f2db12bdba207"

FIRE_ID = "20260815T190002-1692638-e6c8305dbc05"
RUN_ID = f"DR-STD-MAP-AUDIT-ISO9227-{FIRE_ID}"
DATE = "2026-08-15"


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
assert audit_result["violation_count"] == 3
assert audit_result["two_replay_byte_identical"] is True

v2_bytes = (STDMAP_WORK / "mapping-table.v2.json").read_bytes()
v3_bytes = (STDMAP_WORK / "mapping-table.v3.json").read_bytes()
v2_sha = sha(v2_bytes)
v3_sha = sha(v3_bytes)
assert audit_result["input_mapping_table_sha256"] == v2_sha

build_audit_bytes = (WORK / "build_audit.py").read_bytes()
build_correction_bytes = (WORK / "build_correction.py").read_bytes()

retraction_index_bytes = (MOD / "evidence/phase0/repairs/DR-STD-MAP/done/RETRACTION-INDEX.md").read_bytes()

# Confirm no other ledger/manifest touched this fire (recon-mode discipline)
sr_bytes = (MOD / "evidence/ledgers/search-record.v1.jsonl").read_bytes()
dl_bytes = (MOD / "evidence/ledgers/disposition-ledger.v1.jsonl").read_bytes()
dsl_bytes = (MOD / "evidence/ledgers/dataset-ledger.v1.jsonl").read_bytes()

body_obj = {
    "schema": "amphora.dataset-recon.audit.dr-std-map-iso9227-edition-currency-receipt.v1",
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
    "claim_tested": (
        "amphora-dataset-recon/evidence/phase0/repairs/DR-STD-MAP/done/"
        "dr-std-map-fire2-receipt.v1.dsse.json (mapping-table.v2.json): the DR-STD-MAP "
        "mapping table's DIN EN ISO 9227 / NF EN ISO 9227 / PN-EN ISO 9227 rows are "
        "correctly and consistently risk-flagged."
    ),
    "attack": (
        "Extended the fire-2 gap-flag-consistency methodology (which found and fixed "
        "the GOST Р 56752-2015 inconsistency) to a class of row fire-2 never examined: "
        "national EN-ISO-9227 adoptions that cite NO edition/year and are flagged "
        "integrity_gap=false. Live WebSearch/WebFetch against DIN Media, AFNOR/Norm'Info, "
        "and PKN sklep confirmed all three (DIN, NF, PN-EN) underwent real edition churn "
        "-- the German case cycling through a full withdrawal (2017-07 -> 2023-03 "
        "WITHDRAWN -> 2024-10 current) -- since their original DR-LANG-DE/FR/CEE "
        "snapshot_date (all three built 2026-08-10, hours BEFORE the DR-LANG-EU fire-2 "
        "discovery at 15:10 that first surfaced this exact risk class for NL/IT, and "
        "never retroactively re-checked)."
    ),
    "claim_verdict": "CLAIM_REFUTED",
    "refutation_criterion_verbatim": (
        "A DR-STD-MAP mapping-table row citing a national EN-ISO adoption of a standard "
        "with proven live edition churn is left edition-unspecified AND flagged "
        "integrity_gap=false, while structurally identical rows for the SAME underlying "
        "ISO standard are flagged integrity_gap=true -- an internally inconsistent risk "
        "representation the table's own gap-flag-consistency methodology (established by "
        "DR-STD-MAP fire-2) exists to prevent."
    ),
    "refutation_criterion_observation": (
        "OCCURRED. 3/42 rows violated: DIN EN ISO 9227, NF EN ISO 9227, PN-EN ISO 9227. "
        "Live evidence for each: (1) DIN EN ISO 9227 -- dinmedia.de states 'Current "
        "Status: WITHDRAWN. Edition Date: 2023-03. Successor Standard: DIN EN ISO "
        "9227:2024-10', confirming the 2023-03 edition (itself a replacement of "
        "2017-07) is now dead and the true current edition is 2024-10 (ISO 9227:2022 + "
        "Amd1:2024). (2) NF EN ISO 9227 -- AFNOR boutique + Norm'Info confirm the base "
        "edition is 2022-11 with amendment NF EN ISO 9227/A1 dated 2024-06. (3) PN-EN "
        "ISO 9227 -- PKN sklep.pkn.pl confirms PN-EN ISO 9227:2017-06 was superseded by "
        "PN-EN ISO 9227:2023-02, the current edition. In every case the mapping table's "
        "row carried NO edition/year and integrity_gap=false, while its own sibling rows "
        "for the identical underlying standard (UNE-EN ISO 9227, NP EN ISO 9227, CSN EN "
        "ISO 9227) were separately flagged integrity_gap=true in the same table -- an "
        "internal inconsistency in the artifact's own risk representation, independent "
        "of whether any individual quoted scope-text sentence happens to still be "
        "accurate."
    ),
    "checker": {
        "path": "amphora-dataset-recon/evidence/audit/dr-std-map-iso9227-edition-currency-v1/work/build_audit.py",
        "sha256": sha(build_audit_bytes),
        "pure_function_of": "mapping-table.v2.json only (no wall-clock, no randomness)",
        "two_replay_byte_identical": audit_result["two_replay_byte_identical"],
        "runA_sha256": audit_result["runA_sha256"],
        "runB_sha256": audit_result["runB_sha256"],
    },
    "live_evidence": {
        v["standard_id"]: v["live_evidence"]
        for v in audit_result["violations"]
    },
    "correction": {
        "build_script_path": "amphora-dataset-recon/evidence/audit/dr-std-map-iso9227-edition-currency-v1/work/build_correction.py",
        "build_script_sha256": sha(build_correction_bytes),
        "new_artifact_path": "amphora-dataset-recon/evidence/phase0/repairs/DR-STD-MAP/work/mapping-table.v3.json",
        "new_artifact_sha256": v3_sha,
        "rows_changed": [
            {"standard_id_before": "DIN EN ISO 9227", "standard_id_after": "DIN EN ISO 9227:2024-10"},
            {"standard_id_before": "NF EN ISO 9227", "standard_id_after": "NF EN ISO 9227:2022 (+A1:2024)"},
            {"standard_id_before": "PN-EN ISO 9227", "standard_id_after": "PN-EN ISO 9227:2023-02"},
        ],
        "integrity_gap_count_v2": 11,
        "row_count_v2": 42,
    },
    "supersedes": {
        "superseded_path": "amphora-dataset-recon/evidence/phase0/repairs/DR-STD-MAP/work/mapping-table.v2.json",
        "superseded_sha256": v2_sha,
        "superseded_deleted_or_modified": False,
        "reason": (
            "3 rows signed integrity_gap=false lacked edition/year and are now proven, "
            "by live evidence, to carry the exact edition-currency risk this table's own "
            "gap-flag-consistency methodology otherwise applies to sibling rows for the "
            "same standard."
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
            "(mapping-table.v2.json), not a new-language recon fire -- no new "
            "WebSearch-discovered dataset candidates this fire, so no ledger append "
            "was required or made. All new evidence is standard-edition-currency "
            "verification, recorded here and in the correction artifact."
        ),
    },
    "no_acquisition_attestation": (
        "This fire performed WebSearch/WebFetch reads against national standards-body "
        "catalog/shop pages (DIN Media, AFNOR boutique/Norm'Info, PKN sklep, KSSN, "
        "standard.go.kr) to check PUBLISHED EDITION STATUS metadata only -- titles, "
        "dates, withdrawal/supersession notices. No standard's full text, clause "
        "content, or paywalled document was purchased, downloaded, or cached. Nothing "
        "landed on xbabe2 except this receipt, the mapping-table.v3.json correction, "
        "the audit_result.json diagnostic, and the RETRACTION-INDEX.md append."
    ),
    "recon_mode_compliance": {
        "read_to_evaluate_only": True,
        "no_downloads_no_caching_no_scraping": True,
        "search_the_open_web_used_websearch_webfetch": True,
        "credited_artifact_is_dsse_receipt": True,
        "ledger_lines_appended_this_fire": 0,
    },
    "open_items_remaining_for_a_future_fire": [
        "KS D ISO 9227:2005 explicitly cites 'ISO 9227:1990 (identical adoption, per "
        "KSA)' -- this fire attempted a live check via kssn.net/standard.go.kr but "
        "those portals are JS-rendered search forms that WebFetch could not resolve to "
        "the specific KS D ISO 9227 record; its edition-currency status (very likely "
        "also stale, given the 1990 baseline and the churn just proven for DIN/NF/PN) "
        "remains an open, honestly-undischarged gap for a future fire with better KR "
        "portal access.",
        "The remaining 5 pattern-inference-only rows already flagged integrity_gap=true "
        "(ČSN EN ISO 9227, UNE-EN ISO 9227, UNE-EN ISO 12944, NP EN ISO 12944, NP EN ISO "
        "9227) were not re-attempted this fire -- they were already honestly flagged and "
        "are not this fire's violation class.",
        "ISO 12944 rows (DIN/NF/UNI/NEN/PN EN ISO 12944, all integrity_gap=false, all "
        "edition-unspecified) were NOT checked this fire for the same edition-currency "
        "risk class -- ISO 12944 parts were substantially revised 2017-2018 and a "
        "similar audit could plausibly find similar drift; scoped out of this fire for "
        "time, named explicitly rather than silently left implying they were checked.",
    ],
    "does_not_close": [
        "No promotion, procurement, safety, synthesis, or freedom-to-operate authority.",
        "This audit does not re-verify the SCOPE TEXT of DIN/NF/PN EN ISO 9227 clause-by-"
        "clause against ASTM B117 -- only edition-currency metadata (title/date/"
        "withdrawal status), consistent with the no-acquisition constraint.",
    ],
    "artifact_paths": {
        "checker_script": "amphora-dataset-recon/evidence/audit/dr-std-map-iso9227-edition-currency-v1/work/build_audit.py",
        "correction_script": "amphora-dataset-recon/evidence/audit/dr-std-map-iso9227-edition-currency-v1/work/build_correction.py",
        "audit_result": "amphora-dataset-recon/evidence/audit/dr-std-map-iso9227-edition-currency-v1/work/audit_result.json",
        "mapping_table_v2_superseded": "amphora-dataset-recon/evidence/phase0/repairs/DR-STD-MAP/work/mapping-table.v2.json",
        "mapping_table_v3_correction": "amphora-dataset-recon/evidence/phase0/repairs/DR-STD-MAP/work/mapping-table.v3.json",
        "retraction_index": "amphora-dataset-recon/evidence/phase0/repairs/DR-STD-MAP/done/RETRACTION-INDEX.md",
    },
    "artifact_hashes": {
        "mapping-table.v2.json": v2_sha,
        "mapping-table.v3.json": v3_sha,
        "build_audit.py": sha(build_audit_bytes),
        "build_correction.py": sha(build_correction_bytes),
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
ptype = "application/vnd.amphora.dataset-recon-audit-dr-std-map-iso9227+json"
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
out = out_dir / "dr-std-map-iso9227-edition-currency-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False))

Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))

print("WROTE", out)
print("claim_verdict", body_obj["claim_verdict"])
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
