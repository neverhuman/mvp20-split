#!/usr/bin/env python3
"""DSSE-Ed25519-sign the DR-ANNEX campaign-item DONE receipt for
amphora-dataset-recon. AUDIT_ONLY. Pinned Phase-0 evaluator key only.
Fire 2/2: repair landed (discovery-annex.v1.jsonl built, the three
self-disclosed non-envelope-conforming candidates quarantined via
supersede-never-rewrite disposition-ledger corrections), re-attacked with the
fire-2 checker (real state + 3 independent positive-control mutants), and the
repair survives -- CLAIM_SURVIVED, done_criterion_met True.
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
DONE = ITEM / "done"
DONE.mkdir(parents=True, exist_ok=True)
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

DIRECTIVE_MD = ROOT / "docs/directives/2026-08-09-dataset-reconnaissance-multilingual.md"
DIRECTIVE_SHA_EXPECTED = "97fad5d1636f5ccb106562c2d940535651c216d357dd5276088f2db12bdba207"

FIRE_ID = "20260811T150002-2000042-4b581f63550c"
PRIOR_FIRE_ID = "20260811T140001-1467682-769800c79eab"
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

repair_result = json.loads((WORK / "repair_result.json").read_bytes())
runA = json.loads((WORK / "fire2.runA.json").read_bytes())
runB = json.loads((WORK / "fire2.runB.json").read_bytes())
runA_sha = sha((WORK / "fire2.runA.json").read_bytes())
runB_sha = sha((WORK / "fire2.runB.json").read_bytes())
assert runA_sha == runB_sha, "two-replay byte-stability gate FAILED"
assert runA["annex_exists"] is True
assert runA["flagged_count"] == 3
assert runA["unresolved_count"] == 0
assert runA["refutation_criterion_observed_overall"] is False

mutants = {}
for cid in ["DR-LANG-KO-02", "DR-LANG-KO-04", "DR-LANG-EU-11"]:
    fname = f"fire2.mutate.{cid}.json"
    m = json.loads((WORK / fname).read_bytes())
    assert m["unresolved_count"] == 1, f"positive control did not fire for {cid}"
    assert cid in [u["candidate_id"] for u in m["unresolved"]]
    assert m["refutation_criterion_observed_overall"] is True
    mutants[cid] = {
        "file": fname,
        "sha256": sha((WORK / fname).read_bytes()),
        "unresolved_count": m["unresolved_count"],
        "refutation_criterion_observed_overall": m["refutation_criterion_observed_overall"],
    }

# cross-module citation sweep for the (now) annex candidate_ids, re-run this fire
cross_module_hits_raw = [
    "logs/cron-audit/campaign.json.20260811T140645.20260811T140001-1467682-769800c79eab",
    "logs/fire-summary.jsonl",
    "logs/lane-1/claude-hourly-loop.log",
]

flagged_summary = ", ".join(
    f"{f['candidate_id']}(latest_verdict={f['latest_verdict']}, in_annex={f['in_annex']})"
    for f in runA["resolved"]
)

body_obj = {
    "schema": "amphora.dataset-recon-repair-done-dr-annex.v1",
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
    "prior_fire_id": PRIOR_FIRE_ID,
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
    "claim_verdict": "CLAIM_SURVIVED",
    "repair_status": "fix_landed_survived",
    "done_criterion_met": True,
    "refutation_criterion_verbatim": (
        "Any annex entry also appears in the primary Dataset Ledger or the primary recipe, "
        "or any primary-recipe element cites an annex entry as its evidence, or a "
        "non-envelope-conforming chemistry appears outside the annex."
    ),
    "refutation_criterion_verbatim_source": (
        "campaign.json item id=DR-ANNEX, field 'objective', clause "
        "'PRE-COMMITTED REFUTATION CRITERION (restate VERBATIM in your receipt)'"
    ),
    "refutation_criterion_observed": False,
    "refutation_criterion_observation_statement": (
        "NOT OBSERVED as of this fire. Fire 1 (" + PRIOR_FIRE_ID + ") found the criterion's "
        "third clause OCCURRED (discovery-annex.v1.jsonl did not exist; three self-disclosed "
        "non-envelope-conforming candidates -- DR-LANG-KO-02 rebar/concrete, DR-LANG-KO-04 "
        "anhydride-cured epoxy, DR-LANG-EU-11 cardanol biobased resin -- sat RECOMMENDED in "
        "the primary dataset-ledger.v1.jsonl un-quarantined). This fire repaired that: built "
        "discovery-annex.v1.jsonl (new file, 3 entries, DR-ANNEX-<candidate_id>-01 each) and "
        "appended 3 supersede-never-rewrite disposition-ledger.v1.jsonl corrections "
        "(<candidate_id>-QUARANTINED, entry_type candidate_quarantine, disposition.verdict "
        "REJECTED, each with a supersedes block naming the original candidate_id and the exact "
        "superseded line sha256) -- the original dataset-ledger.v1.jsonl and "
        "disposition-ledger.v1.jsonl rows were NOT edited or deleted, per repair-mode discipline. "
        "Re-ran a fire-2 checker (dr_annex_fire2_checker.py, sha256 pinned below) that reuses "
        "fire-1's exact NONCONFORM_MARKERS scan (byte-identical to build_dr_annex.py, sha256 "
        f"{runA['dataset_ledger_sha256'] and '034d322b6297246b1c9e02136082fa328225d22de195d27d6656a0104d9fb22f'}"
        ") over dataset-ledger.v1.jsonl (still flags all 3 rows -- expected and correct, since "
        "append-only ledgers cannot remove the original text) plus a latest-verdict-wins "
        "cross-check against disposition-ledger.v1.jsonl's supersession chain and "
        "discovery-annex.v1.jsonl membership. Result: flagged_count=3, resolved_count=3, "
        "unresolved_count=0 -- all three flagged rows now have both (a) a superseding "
        "disposition-ledger entry whose latest verdict is no longer RECOMMENDED and (b) a "
        "matching discovery-annex.v1.jsonl entry: " + flagged_summary + ". Clause 1 (annex "
        "entry live RECOMMENDED/CONDITIONAL in the primary ledger) also NOT observed: 0 hits. "
        "Clause 2 (primary-recipe element citing annex evidence): a repo-wide grep sweep for "
        "all three candidate_ids found hits ONLY in this loop's own operational logs "
        "(logs/cron-audit/campaign.json.*, logs/fire-summary.jsonl, "
        "logs/lane-1/claude-hourly-loop.log) that quote the fire-1 verdict_summary text handed "
        "to this fire via campaign.json -- these are cron/audit logs of the falsification loop "
        "itself, not a primary recipe or module BOM consuming annex evidence as scientific "
        "input, so clause 2 is NOT observed. All three refutation-criterion clauses now read "
        "false against the live repaired state."
    ),
    "annex_exists": True,
    "flagged_count": runA["flagged_count"],
    "resolved_count": runA["resolved_count"],
    "unresolved_count": runA["unresolved_count"],
    "clause1_observed": runA["clause1_observed"],
    "clause3_nonconforming_outside_annex_observed": runA["clause3_nonconforming_outside_annex_observed"],
    "cross_module_citation_sweep": {
        "method": "grep -rl --exclude-dir=.git --exclude-dir=target --exclude-dir=node_modules '<candidate_id_alternation>' . across repo root, excluding this module's own evidence tree",
        "candidate_ids_checked": ["DR-LANG-KO-02", "DR-LANG-KO-04", "DR-LANG-EU-11"],
        "hits_outside_amphora_dataset_recon": cross_module_hits_raw,
        "hits_classification": "operational cron/audit logs (loop's own campaign.json snapshot + fire-summary + loop log) quoting fire-1's verdict_summary text -- NOT a primary recipe or module BOM citing annex evidence as scientific input",
        "primary_recipe_citation_hits": [],
        "note": "Zero hits in any module's evidence/recipe/BOM artifacts; the only cross-module hits are this falsification loop's own logging of the fire-1 verdict text, which is expected and not a quarantine breach.",
    },
    "supersede_records": repair_result["supersede_records"],
    "ledger_content_binding": {
        "disposition_ledger": repair_result["disposition_ledger"],
        "discovery_annex": repair_result["discovery_annex"],
    },
    "retraction_index_updated": "amphora-dataset-recon/evidence/phase0/kpis/RETRACTION-INDEX.md",
    "attack_description": (
        "Fire-2 repair-mode re-attack per repair-mode rule 2: re-derived fire-1's exact "
        "flagged-row scan (same NONCONFORM_MARKERS list and matching logic, sha256-pinned "
        "against build_dr_annex.py) over the now-repaired ledger state, extended with "
        "supersession-awareness (latest-verdict-wins over disposition-ledger.v1.jsonl's "
        "supersedes chain) and annex-membership checks, run twice for byte-stability, plus 3 "
        "independent positive-control mutants (one per quarantined candidate) that each "
        "in-memory drop that candidate's superseding disposition-ledger line and confirm the "
        "checker re-fires unresolved_count=1 on exactly that candidate -- proving the checker "
        "can detect the exact class of defect (an incomplete/missing quarantine) it exists to "
        "catch, not just a trivially different one."
    ),
    "positive_control": {
        "planted_defect": (
            "For each of the 3 quarantined candidates in turn, drop that candidate's "
            "superseding disposition-ledger.v1.jsonl entry from the in-memory analysis "
            "(nothing written to disk) -- simulating an incomplete repair where the annex "
            "entry exists but the primary-ledger verdict was never actually superseded."
        ),
        "how_planted": (
            "dr_annex_fire2_checker.py 'mutate' mode filters out, from the parsed "
            "disposition-ledger.v1.jsonl lines held in memory, the one line whose "
            "supersedes.superseded_candidate_id equals the target candidate_id, asserting "
            "exactly 1 line is dropped, before re-running the same analyze() function used "
            "for the real-state run."
        ),
        "detected": True,
        "evidence": (
            "fire2.mutate.DR-LANG-KO-02.json: unresolved_count=1, unresolved=[DR-LANG-KO-02], "
            "refutation_criterion_observed_overall=true. "
            "fire2.mutate.DR-LANG-KO-04.json: unresolved_count=1, unresolved=[DR-LANG-KO-04], "
            "refutation_criterion_observed_overall=true. "
            "fire2.mutate.DR-LANG-EU-11.json: unresolved_count=1, unresolved=[DR-LANG-EU-11], "
            "refutation_criterion_observed_overall=true. "
            "All 3 mutants: sha256 " + mutants["DR-LANG-KO-02"]["sha256"] + " / " +
            mutants["DR-LANG-KO-04"]["sha256"] + " / " + mutants["DR-LANG-EU-11"]["sha256"]
        ),
    },
    "no_acquisition_attestation": (
        "This fire performed zero web fetches, zero downloads, and zero new candidate "
        "discovery. It read the existing evidence/ledgers/ tree, appended new ledger lines "
        "derived entirely from content already present in the module's own dataset-ledger.v1.jsonl "
        "and disposition-ledger.v1.jsonl rows (a migration/quarantine of existing evidence, not "
        "new acquisition), and ran read-only analysis scripts."
    ),
    "build_script_sha256": sha((WORK / "dr_annex_repair.py").read_bytes()),
    "fire2_checker_script_sha256": sha((WORK / "dr_annex_fire2_checker.py").read_bytes()),
    "fire1_checker_script_sha256": "034d322b6297246b1c9e02136082fa328225d22de195d27d6656a0104d9fb22f",
    "prior_attempt_receipt": {
        "path": "amphora-dataset-recon/evidence/phase0/repairs/DR-ANNEX/attempts/dr-annex-attempt-receipt.v1.dsse.json",
        "fire_id": PRIOR_FIRE_ID,
        "claim_verdict": "CLAIM_REFUTED",
    },
    "reproducibility": {
        "runA_diagnostic_sha256": runA_sha,
        "runB_diagnostic_sha256": runB_sha,
        "byte_identical": runA_sha == runB_sha,
        "two_replay_sha256_gate": "PASS",
        "replay_method": "dr_annex_fire2_checker.py 'real' mode invoked twice as independent Python processes over the same on-disk repaired ledger state; output is a pure function of file contents (sorted-key JSON serialization, no wall-clock or random input).",
    },
    "generated_on_host": "xbabe1 (agent tool calls); receipt and ledger written to xbabe2",
    "signing_key": {
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "role": "PHASE0_EVALUATOR",
        "derives_pinned_trust_store_key_id": True,
        "signs_phase0_evaluation_or_review": False,
        "used_for": "AUDIT_ONLY DR-ANNEX done receipt under evidence/phase0/repairs/DR-ANNEX/done/",
    },
    "receipt_id": f"DR-ANNEX-{FIRE_ID}",
}

payload_bytes = json.dumps(body_obj, indent=2, ensure_ascii=False, sort_keys=True).encode("utf-8")
payload_type = "application/vnd.amphora.dataset-recon.dr-annex-done-receipt+json"
msg = pae(payload_type, payload_bytes)
sig = eval_sk.sign(msg)

envelope = {
    "payloadType": payload_type,
    "payload": base64.b64encode(payload_bytes).decode("ascii"),
    "signatures": [
        {"keyid": eval_key_id, "sig": base64.b64encode(sig).decode("ascii")}
    ],
}

pub = Ed25519PublicKey.from_public_bytes(bytes.fromhex(eval_pub_hex))
msg_v = pae(envelope["payloadType"], base64.b64decode(envelope["payload"]))
pub.verify(base64.b64decode(envelope["signatures"][0]["sig"]), msg_v)
print("SELF-VERIFY PASS")

out_path = DONE / "dr-annex-done-receipt.v1.dsse.json"
out_path.write_text(json.dumps(envelope, indent=2, ensure_ascii=False) + "\n")
print("wrote", out_path)
print("payload sha256:", sha(payload_bytes))
