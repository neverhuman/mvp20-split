#!/usr/bin/env python3
"""DSSE-Ed25519-sign the DR-ANNEX campaign-item CHECKPOINT receipt for
amphora-dataset-recon. AUDIT_ONLY. Pinned Phase-0 evaluator key only.
Verdict: CLAIM_REFUTED -- done_criterion NOT met, so this receipt is written
to attempts/, never done/.
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
ITEM = MOD / "evidence/phase0/repairs/DR-ANNEX"
WORK = ITEM / "work"
ATTEMPTS = ITEM / "attempts"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

DIRECTIVE_MD = ROOT / "docs/directives/2026-08-09-dataset-reconnaissance-multilingual.md"
DIRECTIVE_SHA_EXPECTED = "97fad5d1636f5ccb106562c2d940535651c216d357dd5276088f2db12bdba207"

FIRE_ID = "20260811T140001-1467682-769800c79eab"
RUN_ID = f"DR-ANNEX-{FIRE_ID}"
DATE = "2026-08-11"


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

runA = json.loads((WORK / "diagnostic.runA.json").read_bytes())
runB = json.loads((WORK / "diagnostic.runB.json").read_bytes())
runA_sha = sha((WORK / "diagnostic.runA.json").read_bytes())
runB_sha = sha((WORK / "diagnostic.runB.json").read_bytes())
assert runA_sha == runB_sha, "two-replay byte-stability gate FAILED"
assert runA["refutation_criterion_observed_overall"] is True
assert runA["annex_exists"] is False
assert runA["flagged_count"] == 3

flagged_summary = ", ".join(
    f"{f['candidate_id']}(verdict={f['disposition_verdict']}, markers={f['markers_hit']})"
    for f in runA["flagged_nonconforming_in_primary_ledger"]
)

body_obj = {
    "schema": "amphora.dataset-recon-repair-attempt-dr-annex.v1",
    "module": "amphora-dataset-recon",
    "campaign_item_id": "DR-ANNEX",
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
    "directive_path": "docs/directives/2026-08-09-dataset-reconnaissance-multilingual.md",
    "directive_sha256": directive_sha_actual,
    "directive_obligation": "DR-ANNEX",
    "claim_tested": (
        "The current DR-ANNEX deliverable state is complete and accurate for its scope "
        "(finding a miss is CLAIM_REFUTED and is progress)."
    ),
    "claim_verdict": "CLAIM_REFUTED",
    "repair_status": "in_progress",
    "done_criterion_met": False,
    "refutation_criterion_verbatim": (
        "Any annex entry also appears in the primary Dataset Ledger or the primary recipe, "
        "or any primary-recipe element cites an annex entry as its evidence, or a "
        "non-envelope-conforming chemistry appears outside the annex."
    ),
    "refutation_criterion_verbatim_source": (
        "campaign.json item id=DR-ANNEX, field 'objective', clause "
        "'PRE-COMMITTED REFUTATION CRITERION (restate VERBATIM in your receipt)'"
    ),
    "refutation_criterion_observation_statement": (
        "OCCURRED. Two independent findings, both mechanically checked against the real "
        f"evidence/ledgers/ state (dataset-ledger.v1.jsonl, sha256 {runA['dataset_ledger_sha256']}, "
        f"{runA['dataset_ledger_total_lines']} lines):\n\n"
        "(1) discovery-annex.v1.jsonl -- the quarantine file the module's own README.md "
        "documents as one of 'the four deliverable ledgers plus the quarantined annex' -- "
        "DOES NOT EXIST anywhere under evidence/ledgers/. Directive rule 6 ('QUARANTINE THE "
        "ANNEX. Superior non-conforming chemistries and adjacent discoveries go to "
        "discovery-annex.v1.jsonl and are NEVER cited by the primary ledger or the primary "
        "recipe') has zero implementation: no file, and grep across every build_dr_*.py "
        "script in this module found no code path that writes to, checks against, or enforces "
        "disjointness with any such file. The annex is documentation-only, never built.\n\n"
        "(2) Because the annex does not exist, the third clause of the refutation criterion -- "
        "'a non-envelope-conforming chemistry appears outside the annex' -- is trivially and "
        "observably true: THREE candidates that self-disclose as outside the portfolio's "
        "envelope scope (" + runA["envelope_scope_statement"] + ") sit directly in the PRIMARY "
        "dataset-ledger.v1.jsonl with disposition RECOMMENDED, not quarantined anywhere: "
        f"{flagged_summary}. DR-LANG-KO-02 is concrete-embedded structural rebar inspection "
        "data, not a coating dataset at all. DR-LANG-KO-04 is an epoxy/acid-anhydride cure "
        "system -- a different hardener chemistry than the portfolio's amine-hardener scope; "
        "its own 'coverage' field states 'anhydride-cured, not amine-cured' in the same breath "
        "as recommending it into the primary ledger. DR-LANG-EU-11 is a cardanol/biobased-resin "
        "system explicitly flagged 'not the portfolio's core DGEBA+amine chemistry' -- and this "
        "one is not even a dormant ledger row: its serves.recipe_elements field already reads "
        "['amine-cure-conversion-tracking'], meaning a non-envelope-conforming chemistry is "
        "already wired to serve a named recipe element, un-quarantined. The first and second "
        "clauses of the refutation criterion (annex entry appearing in primary ledger/recipe; "
        "primary-recipe element citing annex evidence) are NOT APPLICABLE as literally worded "
        "because no annex exists for anything to leak from -- stated explicitly rather than "
        "counted as passing by vacuous truth. A cross-module grep sweep for all three flagged "
        "candidate_ids found zero citations anywhere outside amphora-dataset-recon/, so no "
        "OTHER module's primary recipe has (yet) ingested this contamination -- the leak is "
        "presently confined to this module's own primary ledger."
    ),
    "refutation_criterion_observed": True,
    "annex_exists": False,
    "flagged_nonconforming_entries": runA["flagged_nonconforming_in_primary_ledger"],
    "flagged_count": runA["flagged_count"],
    "cross_module_citation_sweep": runA["cross_module_citation_sweep"],
    "attack_description": (
        "Grepped the primary dataset-ledger.v1.jsonl for self-disclosed adjacent-domain / "
        "non-envelope-conforming marker phrases (a mechanical keyword scan over every entry's "
        "serialized JSON text: 'adjacent-domain', 'anhydride', 'not amine-cured', "
        "'not coated-steel', 'biobased', 'cardanol', etc.), then cross-checked whether "
        "discovery-annex.v1.jsonl exists and whether any flagged candidate_id is cited outside "
        "this module. This directly executes the item's ATTACK SHAPE ('grep the primary "
        "artifacts for annex identifiers') adapted to the discovered reality that the intended "
        "'copy one annex chemistry into a primary-BOM copy' probe is moot -- the primary ledger "
        "already contains un-quarantined non-conforming chemistry without any copying needed."
    ),
    "no_acquisition_attestation": (
        "This fire performed zero web fetches, zero downloads, and zero new candidate "
        "discovery. It is a pure read-and-audit pass over the existing evidence/ledgers/ tree "
        "and a repo-wide grep sweep for three known candidate_id strings. Nothing new landed "
        "on xbabe2 except this diagnostic, this receipt, and the falsification-ledger line."
    ),
    "downstream_effect": (
        "A future DR-ANNEX fire (this item permits max_fires=2; this is fire 1) or an "
        "R-DR-ANNEX repair item must: (a) create discovery-annex.v1.jsonl with the annex "
        "entry schema, (b) append superseding disposition-ledger entries for DR-LANG-KO-02, "
        "DR-LANG-KO-04, and DR-LANG-EU-11 that supersede their RECOMMENDED verdicts with a "
        "QUARANTINED-to-annex verdict per the supersede-never-rewrite rule (dataset-ledger.v1.jsonl "
        "and disposition-ledger.v1.jsonl are append-only; the original rows must not be edited "
        "or deleted), (c) migrate the three entries' content into discovery-annex.v1.jsonl, and "
        "(d) re-run this fire's exact scanner (build_dr_annex.py, sha256 pinned below) as the "
        "acceptance re-attack before any done/ receipt is written."
    ),
    "build_script_sha256": sha((WORK / "build_dr_annex.py").read_bytes()),
    "reproducibility": {
        "runA_diagnostic_sha256": runA_sha,
        "runB_diagnostic_sha256": runB_sha,
        "byte_identical": runA_sha == runB_sha,
        "two_replay_sha256_gate": "PASS",
        "replay_method": "build_dr_annex.py invoked twice as independent Python processes over the same frozen dataset-ledger.v1.jsonl and discovery-annex.v1.jsonl (absence) state; output is a pure function of file contents on disk (sorted-key JSON serialization, no wall-clock or random input).",
    },
    "generated_on_host": "xbabe1 (agent tool calls); receipt and ledger written to xbabe2",
    "signing_key": {
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "role": "PHASE0_EVALUATOR",
        "derives_pinned_trust_store_key_id": True,
        "signs_phase0_evaluation_or_review": False,
        "used_for": "AUDIT_ONLY DR-ANNEX checkpoint receipt under evidence/phase0/repairs/DR-ANNEX/attempts/",
    },
    "receipt_id": f"DR-ANNEX-{FIRE_ID}",
}

payload_bytes = json.dumps(body_obj, indent=2, ensure_ascii=False, sort_keys=True).encode("utf-8")
payload_type = "application/vnd.amphora.dataset-recon.dr-annex-attempt-receipt+json"
msg = pae(payload_type, payload_bytes)
sig = eval_sk.sign(msg)

envelope = {
    "payloadType": payload_type,
    "payload": base64.b64encode(payload_bytes).decode("ascii"),
    "signatures": [
        {"keyid": eval_key_id, "sig": base64.b64encode(sig).decode("ascii")}
    ],
}

# self-verify
pub = Ed25519PublicKey.from_public_bytes(bytes.fromhex(eval_pub_hex))
msg_v = pae(envelope["payloadType"], base64.b64decode(envelope["payload"]))
pub.verify(base64.b64decode(envelope["signatures"][0]["sig"]), msg_v)
print("SELF-VERIFY PASS")

out_path = ATTEMPTS / "dr-annex-attempt-receipt.v1.dsse.json"
out_path.write_text(json.dumps(envelope, indent=2, ensure_ascii=False) + "\n")
print("wrote", out_path)
print("payload sha256:", sha(payload_bytes))
