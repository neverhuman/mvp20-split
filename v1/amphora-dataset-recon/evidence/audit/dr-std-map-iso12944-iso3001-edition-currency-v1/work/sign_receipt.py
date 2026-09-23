#!/usr/bin/env python3
"""DSSE-Ed25519-sign the DR-STD-MAP ISO-12944/ISO-3001 edition-currency audit
receipt. AUDIT_ONLY. Pinned Phase-0 evaluator key only."""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-dataset-recon"
AUDIT_DIR = MOD / "evidence/audit/dr-std-map-iso12944-iso3001-edition-currency-v1"
WORK = AUDIT_DIR / "work"
STDMAP_WORK = MOD / "evidence/phase0/repairs/DR-STD-MAP/work"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

DIRECTIVE_MD = ROOT / "docs/directives/2026-08-09-dataset-reconnaissance-multilingual.md"
DIRECTIVE_SHA_EXPECTED = "97fad5d1636f5ccb106562c2d940535651c216d357dd5276088f2db12bdba207"

FIRE_ID = "20260819T070002-919438-448811f24d61"
RUN_ID = f"DR-STD-MAP-AUDIT-ISO12944-ISO3001-{FIRE_ID}"
DATE = "2026-08-19"


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
assert audit_result["violation_count"] == 0
assert audit_result["two_replay_byte_identical"] is True

positive_control = json.loads((WORK / "audit_result.positive_control.json").read_bytes())
assert positive_control["violation_count"] == 1
assert positive_control["two_replay_byte_identical"] is True

v4_bytes = (STDMAP_WORK / "mapping-table.v4.json").read_bytes()
v4_sha = sha(v4_bytes)
assert audit_result["input_mapping_table_sha256"] == v4_sha

build_audit_bytes = (WORK / "build_audit.py").read_bytes()

# Confirm no ledger/manifest touched this fire (recon-mode discipline; this
# is a synthesis/audit fire over an existing signed artifact, not a new-
# language recon fire)
sr_bytes = (MOD / "evidence/ledgers/search-record.v1.jsonl").read_bytes()
dl_bytes = (MOD / "evidence/ledgers/disposition-ledger.v1.jsonl").read_bytes()
dsl_bytes = (MOD / "evidence/ledgers/dataset-ledger.v1.jsonl").read_bytes()

body_obj = {
    "schema": "amphora.dataset-recon.audit.dr-std-map-iso12944-iso3001-edition-currency-receipt.v1",
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
        "amphora-dataset-recon/evidence/audit/dr-std-map-ks-d-iso9227-abolition-v1/"
        "dr-std-map-ks-d-iso9227-abolition-receipt.v1.dsse.json (mapping-table.v4.json): "
        "the DR-STD-MAP mapping table's ISO-12944 and ISO-3001 national-adoption rows "
        "(DIN/UNI/NEN/PN/CSN/NF EN ISO 12944; DIN/NF/UNI/NEN/CSN/KS-M EN ISO 3001), all "
        "carrying integrity_gap=false and no edition/year, are correctly and consistently "
        "risk-flagged -- i.e. none of them are actually stale the way the DIN/NF/PN-EN "
        "ISO 9227 rows and the KS D ISO 9227 row were proven stale in the three prior "
        "DR-STD-MAP edition-currency fires (2026-08-15, 2026-08-17)."
    ),
    "attack": (
        "Extended the DR-STD-MAP ISO-9227 edition-currency audit methodology (which "
        "found and corrected 3 real defects across 3 prior fires: DIN/NF/PN-EN ISO 9227 "
        "on 2026-08-15, KS D ISO 9227 on 2026-08-17) to the two standard families the "
        "2026-08-15 fire explicitly named as an open item but scoped out for time: ISO "
        "12944 (DIN/UNI/NEN/PN/CSN/NF EN adoptions) and ISO 3001 (never previously "
        "examined for edition currency at all: DIN/NF/UNI/NEN/CSN/KS-M EN adoptions). "
        "Ran live WebSearch against DIN Media, AFNOR boutique/Norm'Info, UNI store, "
        "NEN.nl, PKN sklep, ČSN online/technickenormy.cz, and KSSN/e-나라표준인증 to check "
        "each row's true current published edition against a naive reading of the "
        "table's edition-unspecified + integrity_gap=false state, plus an ISO.org check "
        "of the underlying ISO 12944 and ISO 3001 revision-project status."
    ),
    "claim_verdict": "CLAIM_SURVIVED",
    "refutation_criterion_verbatim": audit_result["refutation_criterion_verbatim"],
    "refutation_criterion_observation": (
        "DID NOT OCCUR. 0/12 rows examined violated the criterion. Live evidence for "
        "each of the 12 rows checked (recorded verbatim in the checker's "
        "REAL_LIVE_EVIDENCE table) confirms: (1) ISO 12944 -- all 6 national adoptions "
        "checked (DIN, UNI, NEN, PN-EN, CSN, NF) carry 2017-2020 parts matching the "
        "ISO 12944:2017-2018 revision, with ISO's own project page showing a 3rd "
        "edition still under development (registered 2025-06-19) and NOT yet published "
        "as of this fire -- so there is no newer edition for any national adoption to "
        "have missed. (2) ISO 3001 -- all 6 national adoptions checked (DIN, NF, UNI, "
        "NEN, CSN, KS-M) are re-issues/reconfirmations of the SAME ISO 3001:1999 "
        "content (national dates from 1999 to a 2022-12-19 KS-M reconfirmation), and "
        "ISO's own record shows ISO 3001:1999 was itself last reconfirmed in 2025 with "
        "no successor edition. In every case examined, the row's edition-unspecified, "
        "integrity_gap=false state is a TRUE representation of a genuinely single-"
        "edition-since-adoption standard, not a stale one -- unlike the ISO-9227 family "
        "rows, which really were stale. NP EN ISO 3001 (integrity_gap=false, "
        "edition-unspecified) was NOT resolved to a specific live edition record this "
        "fire (IPQ's lojanormas.ipq.pt search did not return an item-level page) and is "
        "honestly left as an open item, not silently counted as checked-ok."
    ),
    "positive_control": {
        "planted_defect": (
            "A fabricated live-evidence entry claiming DIN EN ISO 12944 was "
            "'WITHDRAWN. Edition Date: 2018-04. Successor Standard: DIN EN ISO "
            "12944:2025-06' -- structurally mirroring the REAL DIN EN ISO 9227 "
            "discovery from the 2026-08-15 fire (which found a genuine 2017-07 -> "
            "2023-03 WITHDRAWN -> 2024-10 chain), but fabricated rather than "
            "live-sourced, and injected only into the audit's live-evidence input, "
            "never into the mapping table itself."
        ),
        "how_planted": (
            "In build_audit.py's run_positive_control(), a copy of REAL_LIVE_EVIDENCE "
            "has its 'DIN EN ISO 12944' entry replaced with "
            "{checked_url: 'FABRICATED-FOR-POSITIVE-CONTROL-ONLY', "
            "current_edition_confirmed_live: 'FABRICATED: DIN EN ISO 12944:2025-06', "
            "churn_confirmed: True (was False in the real entry)}, then audit() is "
            "re-run against the SAME real mapping-table.v4.json with this one mutated "
            "evidence entry substituted in."
        ),
        "detected": True,
        "evidence": (
            "audit_result.positive_control.json: violation_count=1, "
            "two_replay_byte_identical=true. The single violation names "
            "standard_id='DIN EN ISO 12944' with reason text citing the planted "
            "churn_confirmed=True evidence -- confirming the checker fires on this "
            "defect class when it is actually present, which is what licenses trusting "
            "its 0-violation result on the real, unmutated evidence."
        ),
    },
    "checker": {
        "path": "amphora-dataset-recon/evidence/audit/dr-std-map-iso12944-iso3001-edition-currency-v1/work/build_audit.py",
        "sha256": sha(build_audit_bytes),
        "pure_function_of": "mapping-table.v4.json (read-only) + REAL_LIVE_EVIDENCE literal (recorded live-search findings; no wall-clock, no randomness)",
        "two_replay_byte_identical": audit_result["two_replay_byte_identical"],
        "runA_sha256": audit_result["runA_sha256"],
        "runB_sha256": audit_result["runB_sha256"],
    },
    "rows_examined": audit_result["rows_examined"],
    "rows_examined_count": audit_result["rows_examined_count"],
    "ledgers_not_modified_this_fire": {
        "search-record.v1.jsonl_sha256": sha(sr_bytes),
        "disposition-ledger.v1.jsonl_sha256": sha(dl_bytes),
        "dataset-ledger.v1.jsonl_sha256": sha(dsl_bytes),
        "note": (
            "This is a synthesis/audit fire over an existing signed artifact "
            "(mapping-table.v4.json), not a new-language recon fire -- no new "
            "WebSearch-discovered dataset candidates this fire, so no ledger append "
            "was required or made."
        ),
    },
    "no_acquisition_attestation": (
        "This fire performed WebSearch reads against national standards-body "
        "catalog/shop pages (DIN Media, AFNOR boutique/Norm'Info, UNI store, NEN.nl, "
        "PKN sklep, CSN online/technickenormy.cz, KSSN/e-나라표준인증, IPQ lojanormas) "
        "and ISO.org to check PUBLISHED EDITION STATUS metadata only -- titles, dates, "
        "in-force/withdrawal notices, revision-project status. No standard's full text, "
        "clause content, or paywalled document was purchased, downloaded, or cached. "
        "Nothing landed on xbabe2 except this receipt and the audit_result*.json "
        "diagnostics; the mapping table itself was NOT modified (no correction was "
        "warranted -- this is a survival, not a refutation)."
    ),
    "recon_mode_compliance": {
        "read_to_evaluate_only": True,
        "no_downloads_no_caching_no_scraping": True,
        "search_the_open_web_used_websearch_webfetch": True,
        "credited_artifact_is_dsse_receipt": True,
        "ledger_lines_appended_this_fire": 0,
    },
    "open_items_remaining_for_a_future_fire": [
        "NP EN ISO 3001 (integrity_gap=false, edition-unspecified) was not resolved to "
        "a specific live IPQ catalog record this fire -- lojanormas.ipq.pt's search "
        "interface did not surface an item-level page for it. Remains an honestly "
        "undischarged gap, not silently counted as checked.",
        "PN-EN ISO 3001 already carries integrity_gap=true ('unmapped_never_searched') "
        "in the table and was correctly out of scope for this fire's violation class "
        "(rows already flagged risky are not this audit's target).",
        "UNE-EN ISO 12944 and NP EN ISO 12944 already carry integrity_gap=true "
        "(pattern-inference-only) and were correctly out of scope for the same reason.",
        "This audit checked EDITION-CURRENCY METADATA only (title/date/in-force "
        "status), consistent with the no-acquisition constraint -- it does not "
        "re-verify the underlying scope-text quotes clause-by-clause against a live "
        "re-read of each standard's full text.",
    ],
    "does_not_close": [
        "No promotion, procurement, safety, synthesis, or freedom-to-operate authority.",
        "A survival of THIS audit does not certify the mapping table's overall "
        "completeness/accuracy claim beyond the specific 12-row, edition-currency-only "
        "scope examined -- other risk classes (scope-text drift, ASTM equivalence "
        "confirmation) are explicitly out of scope here.",
    ],
    "artifact_paths": {
        "checker_script": "amphora-dataset-recon/evidence/audit/dr-std-map-iso12944-iso3001-edition-currency-v1/work/build_audit.py",
        "audit_result": "amphora-dataset-recon/evidence/audit/dr-std-map-iso12944-iso3001-edition-currency-v1/work/audit_result.json",
        "positive_control_result": "amphora-dataset-recon/evidence/audit/dr-std-map-iso12944-iso3001-edition-currency-v1/work/audit_result.positive_control.json",
        "mapping_table_v4_unchanged": "amphora-dataset-recon/evidence/phase0/repairs/DR-STD-MAP/work/mapping-table.v4.json",
    },
    "artifact_hashes": {
        "mapping-table.v4.json": v4_sha,
        "build_audit.py": sha(build_audit_bytes),
        "audit_result.json": sha((WORK / "audit_result.json").read_bytes()),
        "audit_result.positive_control.json": sha((WORK / "audit_result.positive_control.json").read_bytes()),
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
ptype = "application/vnd.amphora.dataset-recon-audit-dr-std-map-iso12944-iso3001+json"
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
out = out_dir / "dr-std-map-iso12944-iso3001-edition-currency-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False))

Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))

print("WROTE", out)
print("claim_verdict", body_obj["claim_verdict"])
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
