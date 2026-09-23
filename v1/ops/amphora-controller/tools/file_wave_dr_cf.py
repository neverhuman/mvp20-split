#!/usr/bin/env python3
"""File Wave DR/CF — campaign items for AMPHORA-DIRECTIVE-2026-08-09.

Items are GENERATED from the directive index (one source of truth: the
obligation's own wording travels into the item, never a retyping), filed at
the queue head per the operator's priority decision, and written under
campaign.lock with the pre/post sha recorded in the lease history -- an
operator edit that keeps the chain intact instead of tripping the alert.

Idempotent: an obligation whose item id already exists is left alone.
LOOP obligations file as pending (DR-FRESH blocked: nothing to diff until a
second sweep); HUMAN/LAB obligations file as blocked -- the owner guard would
refuse to dispatch them anyway, but blocked is the truthful state.

Module exclusivity note: every DR item lives in amphora-dataset-recon, so the
lease ledger serializes the DR program one-fire-at-a-time regardless of lane
count -- which also makes the queue order (PROBE-WEB -> CF-ARITH -> DR-RUBRIC
-> DR-GAP -> languages) a real execution order for that module. CF items
parallelize across their two modules on other lanes.

usage: file_wave_dr_cf.py [--dry-run]
"""
import fcntl
import hashlib
import json
import os
import sys
import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE_ROOT = os.environ.get("AMPHORA_STATE_ROOT", "/home/ubuntu/amphora-cron")
CAMPAIGN = os.environ.get("AMPHORA_CAMPAIGN_PATH", os.path.join(STATE_ROOT, "campaign.json"))
DIRECTIVE_ROOT = os.environ.get("AMPHORA_DIRECTIVE_ROOT", os.path.join(ROOT, "directives"))
INDEX = os.path.join(DIRECTIVE_ROOT, "2026-08-09-dataset-recon.index.json")
HIST = os.path.join(STATE_ROOT, "state", "lane-ledger.history.jsonl")
LOCK = os.path.join(STATE_ROOT, "state", "locks", "campaign.lock")
DOC = "AMPHORA-DIRECTIVE-2026-08-09"

# Queue order for the new wave (operator decision 2026-08-10: new wave first).
ORDER = ["PROBE-WEB", "CF-ARITH", "DR-RUBRIC", "DR-GAP",
         "DR-LANG-ZH", "DR-LANG-JA", "DR-LANG-DE", "DR-LANG-RU", "DR-LANG-KO",
         "DR-LANG-FR", "DR-LANG-IBERIAN", "DR-LANG-CEE", "DR-LANG-EU",
         "DR-STD-MAP", "CF-BOM", "CF-PROC", "DR-DISP", "CF-TIER", "CF-ALT",
         "CF-TEST", "CF-RISK", "DR-COVERAGE", "DR-SEARCH-RECORD", "DR-ANNEX",
         "DR-FRESH", "CF-PACKET", "DR-D2-COVERAGE",
         # human/lab spine, filed blocked, appended after the LOOP wave
         "DR-RIGHTS", "DR-ACQ", "CF-EXEC-REVIEW", "CF-LAB-EXEC"]

REPAIR_RULES = ("REPAIR-MODE rules apply (see prompt): supersede-never-rewrite; sign only with "
                "the pinned evaluator seed and self-verify DSSE before declaring; declare ONLY "
                "DSSE receipts in artifacts; done receipt ONLY into the done/ glob when the "
                "criterion is met, signed checkpoints into attempts/ otherwise; multi-fire state "
                "in work/STATE.json; run compute in the FOREGROUND under `timeout 1500`.")

PROBE_NOTE = ("Read PROBE-WEB's done receipt first (amphora-dataset-recon/evidence/phase0/"
              "repairs/PROBE-WEB/done/) for the verified tool inventory. If WebSearch is "
              "unavailable headless, run DEGRADED fetch reconnaissance (WebFetch/curl against "
              "repository-native search endpoints) and record the coverage honestly as "
              "non-exhaustive in the search record — the operator pre-approved this fallback; "
              "a degraded honest sweep beats a blocked perfect one.")


# HUMAN obligations have no executing module, but every campaign item needs one
# (invariants: "picker subscripts it"; precedent: B-CREDENTIALS lives in
# amphora-redteam-audit). They get the module whose evidence tree will hold
# their eventual receipts.
HUMAN_MODULE = {"DR-RIGHTS": "amphora-dataset-recon",
                "DR-ACQ": "amphora-dataset-recon",
                "CF-EXEC-REVIEW": "amphora-cro-protocol-packager"}


def item_from_obligation(o, dref):
    oid = o["id"]
    if not o.get("module"):
        o = dict(o, module=HUMAN_MODULE[oid])
    is_recon = oid.startswith(("DR-", "PROBE-")) and o["owner"] == "LOOP"
    claim = ("The current %s deliverable state is complete and accurate for its scope "
             "(finding a miss is CLAIM_REFUTED and is progress)." % oid)
    objective_bits = [
        "FOUNDER OBLIGATION %s — %s." % (oid, o["title"]),
        "WHAT DONE MEANS: %s" % o["done_criteria"],
    ]
    if o.get("attack"):
        objective_bits.append("ATTACK SHAPE: %s" % o["attack"])
    if o.get("refutation_criterion"):
        objective_bits.append("PRE-COMMITTED REFUTATION CRITERION (restate VERBATIM in your "
                              "receipt): %s" % o["refutation_criterion"])
    if is_recon and oid != "PROBE-WEB":
        objective_bits.append(PROBE_NOTE)
    objective_bits.append(REPAIR_RULES)
    it = {
        "id": oid,
        "module": o["module"],
        "max_fires": o.get("max_fires", 2),
        "title": o["title"],
        "claim": claim,
        "directive_ref": dref | {"section": o["section"], "item_id": oid, "owner": o["owner"]},
        "objective": " ".join(objective_bits),
        "done_criterion": o["done_criteria"],
        "status": "pending",
        "fires": [],
        "done_check": {"kind": "signed_receipt_glob",
                       "glob": "%s/evidence/phase0/repairs/%s/done/**/*.json" % (o["module"], oid)},
    }
    if is_recon:
        it["work_type"] = "reconnaissance"
    if o["owner"] in ("HUMAN", "LAB"):
        it["status"] = "blocked"
        it["blocked_reason"] = "owner=%s: the loop files and tracks this, never executes it. %s" % (
            o["owner"], o.get("unblock_condition", ""))
    elif oid == "DR-FRESH":
        it["status"] = "blocked"
        it["blocked_reason"] = o.get("unblock_condition", "second sweep scheduled")
    return it


def main():
    dry = "--dry-run" in sys.argv
    idx = json.load(open(INDEX))
    d = idx["directive"]
    dref = {"doc": DOC, "md_path": d["md_path"], "md_sha256": d["md_sha256"]}
    by_id = {o["id"]: o for o in idx["obligations"]}
    missing = [x for x in ORDER if x not in by_id]
    assert not missing, "ORDER names obligations absent from the index: %s" % missing
    extra = [o["id"] for o in idx["obligations"] if o["id"] not in ORDER]
    assert not extra, "index obligations missing from ORDER (silent drop!): %s" % extra

    os.makedirs(os.path.dirname(LOCK), exist_ok=True)
    lock_fd = os.open(LOCK, os.O_WRONLY | os.O_CREAT, 0o644)
    fcntl.flock(lock_fd, fcntl.LOCK_EX)
    try:
        raw = open(CAMPAIGN, "rb").read()
        pre_sha = hashlib.sha256(raw).hexdigest()
        c = json.loads(raw)
        existing = {i["id"] for i in c["items"]}
        new_items = [item_from_obligation(by_id[x], dict(dref)) for x in ORDER
                     if x not in existing]
        if not new_items:
            print("nothing to file: all %d wave items already exist" % len(ORDER))
            return 0
        # New wave at the queue head, in ORDER; everything existing after.
        c["items"] = new_items + c["items"]
        # dataset-recon joins the fallback rotation at weight 1
        rot_names = {m["name"] for m in c["fallback_rotation"]["modules"]}
        if "amphora-dataset-recon" not in rot_names:
            c["fallback_rotation"]["modules"].append(
                {"name": "amphora-dataset-recon", "weight": 1})
        body = json.dumps(c, indent=2) + "\n"
        post_sha = hashlib.sha256(body.encode()).hexdigest()
        if dry:
            print("DRY RUN: would file %d items at the queue head:" % len(new_items))
            for i in new_items:
                print("  %-18s %-32s %-8s mf=%d %s" % (
                    i["id"], i["module"], i["status"], i["max_fires"],
                    "recon" if i.get("work_type") else ""))
            return 0
        tmp = CAMPAIGN + ".wave.tmp"
        with open(tmp, "w") as fh:
            fh.write(body)
        os.replace(tmp, CAMPAIGN)
        with open(HIST, "a") as fh:
            fh.write(json.dumps({
                "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
                "event": "operator_edit", "lane": "operator", "fire_id": "wave-dr-cf-filing",
                "note": "filed %d Wave DR/CF items at queue head" % len(new_items),
                "campaign_pre_sha256": pre_sha, "campaign_post_sha256": post_sha}) + "\n")
        print("filed %d items; campaign %s -> %s" % (len(new_items), pre_sha[:12], post_sha[:12]))
    finally:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        os.close(lock_fd)
    return 0


if __name__ == "__main__":
    sys.exit(main())
