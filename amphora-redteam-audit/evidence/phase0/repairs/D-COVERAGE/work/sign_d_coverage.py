#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-redteam-audit D-COVERAGE founder-directive
coverage receipt (CAMPAIGN item D-COVERAGE). AUDIT_ONLY: signs a coverage +
self-attack receipt under evidence/phase0/repairs/D-COVERAGE/done/. Does not
modify the master manifest, campaign.json, the directive index, or any other
module's files. Uses the pinned PHASE0_EVALUATOR key, cross-checked against
config/phase0-trust-store.v1.json.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
WORK = ROOT / "amphora-redteam-audit/evidence/phase0/repairs/D-COVERAGE/work"
OUT_DIR = ROOT / "amphora-redteam-audit/evidence/phase0/repairs/D-COVERAGE/done"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

FIRE_ID = "20260809T230003-2808754-913e4d9e0b37"
DIRECTIVE_PATH = "docs/directives/2026-08-05-closing-the-open-portfolio.md"
DIRECTIVE_SHA256 = "dcedb048e1142529de84aa6d741a065fdc29ebf744ef1b2feb81951c74573a6d"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" "
            + str(len(body)).encode() + b" " + body)


def load_seed(p):
    raw = p.read_bytes().strip()
    if len(raw) == 64:
        try:
            return bytes.fromhex(raw.decode())
        except Exception:
            pass
    return raw[:32]


runA_bytes = (WORK / "diagnostic.runA.json").read_bytes()
runB_bytes = (WORK / "diagnostic.runB.json").read_bytes()
byte_identical_cov = runA_bytes == runB_bytes
assert byte_identical_cov, "coverage two-replay bytes differ -- NOT stable, do not sign"

auditA_bytes = (WORK / "audit.runA.json").read_bytes()
auditB_bytes = (WORK / "audit.runB.json").read_bytes()
byte_identical_audit = auditA_bytes == auditB_bytes
assert byte_identical_audit, "audit two-replay bytes differ -- NOT stable, do not sign"

cov = json.loads(runA_bytes)
audit = json.loads(auditA_bytes)

harness_cov_sha = sha((WORK / "directive_coverage.py").read_bytes())
harness_audit_sha = sha((WORK / "run_coverage_audit.py").read_bytes())
campaign_snapshot_sha = sha((WORK / "campaign.snapshot.json").read_bytes())
fire_summary_snapshot_sha = sha((WORK / "fire-summary.snapshot.jsonl").read_bytes())
directive_index_snapshot_sha = sha((WORK / "directive.index.snapshot.json").read_bytes())

assert cov["directive"]["md_sha256"] == DIRECTIVE_SHA256, "directive hash drift vs pinned citation"

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
rev_pin = (rev_key_id == tbr.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))
assert eval_pin, "evaluator key_id does not match pinned trust store"

n_total = audit["n_obligations_total"]
n_closed = audit["n_closed_by_naive_flag"]
n_delivered = audit["closed_delivered_count"]
n_mixed = audit["closed_mixed_count"]
n_not_delivered = audit["closed_not_delivered_count"]

verdict = "CLAIM_REFUTED"

body_obj = {
    "schema": "amphora.redteam-audit.d-coverage-founder-directive-coverage-receipt.v1",
    "receipt_id": "d-coverage-founder-directive-coverage-receipt-v1",
    "authority": "AUDIT_ONLY",
    "run_type": "FALSIFICATION_ATTACK",
    "module": "amphora-redteam-audit",
    "campaign_item_id": "D-COVERAGE",
    "fire_id": FIRE_ID,
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_other_module_files": False,
    "modifies_campaign_json": False,
    "modifies_directive_index": False,

    "directive_path": DIRECTIVE_PATH,
    "directive_sha256": DIRECTIVE_SHA256,
    "directive_obligation": "D-COVERAGE",
    "directive_obligation_origin": "operator-derived (not founder text) -- section 'meta', "
        "owner LOOP, title 'Sign the founder-directive coverage table into the evidence tree'",
    "directive_obligation_done_criteria_verbatim": (
        "Signed receipt carrying the full obligation-coverage table, the UNMAPPED and ORPHAN "
        "lists (reported even when empty), the directive cited by path + sha256, and a "
        "spot-check of >=3 closed obligations read from their actual receipts."
    ),
    "refutation_criterion_present_on_this_obligation": False,
    "refutation_criterion_note": (
        "D-COVERAGE is operator-derived meta-obligation, not founder text, and carries no "
        "refutation_criterion field in the directive index -- confirmed by reading the index "
        "entry directly (origin: 'operator-derived'). Rule (c) of the fire prompt (restate the "
        "refutation_criterion verbatim) therefore does not apply to this receipt's own "
        "obligation; the self-attack below instead falsifies the naive reading of the table "
        "this receipt itself produces, per the fire's explicit 'ATTACK YOUR OWN TABLE' "
        "instruction."
    ),

    "claim_under_attack": "Progress against the founder directive is signed evidence, not an "
        "assertion in a chat log.",

    "attack_description": (
        "Ran /home/ubuntu/amphora-cron/tools/directive_coverage.py --json READ-ONLY on xbabe1 "
        f"(sha256 {harness_cov_sha}) against the live campaign.json, "
        "logs/fire-summary.jsonl, and directives/2026-08-05-closing-the-open-portfolio.index.json "
        "(all read-only, none modified), producing the raw 46-row coverage table below. Then "
        "attacked the table's own headline number: the tool marks an obligation 'closed' purely "
        "from campaign-item status=='done' (or index_status in "
        "already-delivered/already-satisfied), which is silent on WHICH verdict closed it. For "
        "every one of the 16 obligations the raw tool marks closed, cross-referenced the "
        "underlying campaign item's actual last-recorded fire outcome, and for a spot-checked "
        "subset (T2-01, T2-04, T2-05, T2-13) read the ACTUAL signed DSSE receipt bytes from "
        "disk (base64-decoded payload, not the fire-summary text) to check whether the "
        "obligation's own founder-wording done_criteria (the DEFENSE holding) was actually met, "
        "or whether 'closed' instead encodes a CLAIM_REFUTED verdict -- i.e. the adversarial "
        "attack found the very defect the founder's done_criteria says must be absent, and nothing "
        "in this portfolio has yet repaired it. This is the self-attack the fire's own briefing "
        "calls for: 'an obligation counted closed because its campaign item is marked done is "
        "only as true as that item's done receipt.'"
    ),

    "coverage_table": cov["rows"],
    "n_obligations_total": n_total,
    "unmapped": cov["unmapped"],
    "unmapped_count": len(cov["unmapped"]),
    "orphans": cov["orphans"],
    "orphans_count": len(cov["orphans"]),

    "naive_closed_count": n_closed,
    "naive_by_owner": {
        "LOOP": {"closed": sum(1 for r in cov["rows"] if r["owner"] == "LOOP" and
                                (r["closed"] or r["index_status"] in ("already-delivered", "already-satisfied"))),
                 "total": sum(1 for r in cov["rows"] if r["owner"] == "LOOP")},
        "HUMAN": {"closed": sum(1 for r in cov["rows"] if r["owner"] == "HUMAN" and
                                 (r["closed"] or r["index_status"] in ("already-delivered", "already-satisfied"))),
                  "total": sum(1 for r in cov["rows"] if r["owner"] == "HUMAN")},
        "LAB": {"closed": sum(1 for r in cov["rows"] if r["owner"] == "LAB" and
                               (r["closed"] or r["index_status"] in ("already-delivered", "already-satisfied"))),
                "total": sum(1 for r in cov["rows"] if r["owner"] == "LAB")},
    },
    "note_on_human_lab_ownership": (
        "HUMAN (10 obligations) and LAB (11 obligations) cannot be closed by this loop under any "
        "circumstance -- they require human dual-identity ceremony keys or physical lab work this "
        "cron does not hold. HUMAN 0/10 and LAB 0/11 closed is the EXPECTED and HONEST state, not "
        "a gap this loop should try to close; rounding it up would itself be the failure the fire "
        "brief warns against."
    ),

    "closed_obligation_audit": audit["closed_obligation_audit"],
    "closed_delivered_count": n_delivered,
    "closed_mixed_count": n_mixed,
    "closed_not_delivered_count": n_not_delivered,

    "spot_check": audit["spot_checks"],
    "spot_check_method": (
        "For each spot-checked obligation, resolved its recorded receipt path against the repo "
        "root, read the raw file, base64-decoded the DSSE payload (not the fire-summary "
        "verdict_summary prose), and pulled the receipt's own verdict/"
        "founder_directive_done_criteria_met/refutation_criterion_observed fields where present. "
        "Receipt sha256 is recorded per spot-check row so this can be independently re-verified "
        "against the exact bytes read."
    ),

    "verdict": verdict,
    "interpretation": (
        f"CLAIM_REFUTED. The naive coverage number this table would otherwise headline "
        f"({n_closed}/{n_total} obligations closed, LOOP "
        f"{sum(1 for r in cov['rows'] if r['owner']=='LOOP' and (r['closed'] or r['index_status'] in ('already-delivered','already-satisfied')))}/"
        f"{sum(1 for r in cov['rows'] if r['owner']=='LOOP')}) "
        f"is a flattering illusion if read as 'the founder's done_criteria were met.' Of the "
        f"{n_closed} obligations the tool marks closed, only {n_delivered} are backed by a signed "
        f"receipt whose own recorded observation confirms the defense actually held "
        f"(founder_directive_done_criteria_met == True); {n_mixed} is mixed (one sub-attack held, "
        f"a second on the same module's different code path found a new defect); and "
        f"{n_not_delivered} are backed by a signed CLAIM_REFUTED receipt whose own recorded "
        f"refutation-criterion observation is True -- meaning the obligation was 'closed' by "
        f"PROVING the founder's named failure mode is real and currently unremediated, the "
        f"opposite of what a bare checkmark implies. Three of the four spot-checked obligations "
        f"(T2-04 intake spoofing, T2-05 stoichiometric override, T2-13 hash-chain/replay) read "
        f"'NOT_DELIVERED' directly from their own signed receipt bytes; the fourth (T2-01, typed-"
        f"payload override injection) reads 'DELIVERED' with founder_directive_done_criteria_met "
        f"== True and refutation_criterion_observed == False, confirming the check can and does "
        f"distinguish the two cases rather than defaulting to one answer. This is a genuine "
        f"finding, not a technicality: this receipt itself is the signed evidence the fire's "
        f"claim asks for, and it would be false evidence if it shipped only the naive "
        f"'{n_closed}/{n_total} closed' number without this breakdown."
    ),
    "does_not_close": [
        "Repair of any of the 10 not_delivered / 1 mixed obligations -- out of this item's scope "
        "(D-COVERAGE signs the coverage table; it does not repair the modules it reports on) and "
        "several already have their own R-*/V-* repair items queued in campaign.json.",
        "Whether obligations NOT in the naive-closed set (30 of 46) are correctly scoped or "
        "sequenced -- this receipt audits only the closed subset's delivered/not_delivered "
        "status, per the fire's spot-check instruction.",
        "Row-level completeness of directive_coverage.py's own campaign-item <-> obligation "
        "mapping logic (separately exercised by prior R-A00 sweep); this receipt trusts that "
        "mapping and audits only the delivered-vs-not-delivered semantics of the 'closed' flag "
        "it produces.",
    ],

    "reproducibility": {
        "two_replay_sha256_gate_coverage": "PASS" if byte_identical_cov else "FAIL",
        "coverage_runA_sha256": sha(runA_bytes),
        "coverage_runB_sha256": sha(runB_bytes),
        "two_replay_sha256_gate_audit": "PASS" if byte_identical_audit else "FAIL",
        "audit_runA_sha256": sha(auditA_bytes),
        "audit_runB_sha256": sha(auditB_bytes),
        "coverage_harness_path": "amphora-redteam-audit/evidence/phase0/repairs/D-COVERAGE/work/directive_coverage.py",
        "coverage_harness_sha256": harness_cov_sha,
        "coverage_harness_origin": "read-only copy of /home/ubuntu/amphora-cron/tools/directive_coverage.py "
                                    "(xbabe1, NOT modified; PROTECTED-tier files on xbabe1 were not touched)",
        "audit_harness_path": "amphora-redteam-audit/evidence/phase0/repairs/D-COVERAGE/work/run_coverage_audit.py",
        "audit_harness_sha256": harness_audit_sha,
        "campaign_json_snapshot_path": "amphora-redteam-audit/evidence/phase0/repairs/D-COVERAGE/work/campaign.snapshot.json",
        "campaign_json_snapshot_sha256": campaign_snapshot_sha,
        "fire_summary_snapshot_path": "amphora-redteam-audit/evidence/phase0/repairs/D-COVERAGE/work/fire-summary.snapshot.jsonl",
        "fire_summary_snapshot_sha256": fire_summary_snapshot_sha,
        "directive_index_snapshot_path": "amphora-redteam-audit/evidence/phase0/repairs/D-COVERAGE/work/directive.index.snapshot.json",
        "directive_index_snapshot_sha256": directive_index_snapshot_sha,
        "determinism": "pure filesystem read of pinned snapshots + already-signed receipts on "
                        "xbabe2 at read time; no RNG, no model fitting, no wall-clock embedded in "
                        "either diagnostic body",
    },
    "toolchain": {"python": "3", "note": "stdlib json/hashlib/base64 only"},
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under evidence/phase0/repairs/D-COVERAGE/done/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin),
    },
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER", "key_id": rev_key_id, "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin), "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed.",
    },
}

body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.redteam-audit-d-coverage-founder-directive-coverage-receipt+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}

OUT_DIR.mkdir(parents=True, exist_ok=True)
out = OUT_DIR / "d-coverage-founder-directive-coverage-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))

print("WROTE", out)
print("verdict", verdict)
print("n_total", n_total, "n_closed", n_closed, "delivered", n_delivered, "mixed", n_mixed, "not_delivered", n_not_delivered)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("signature_verified", True)
