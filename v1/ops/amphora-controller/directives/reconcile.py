#!/usr/bin/env python3
"""reconcile.py — derive obligation status from the LIVE campaign.

Extracted from build_index.py so both directive builders share one copy. The
first index hand-asserted campaign_items and status, and by the time the items
were actually filed 17 of 45 records were lying about their own state -- in
the one artifact whose entire job is telling the truth about coverage.
Deriving it removes the failure mode instead of correcting it once.

An obligation is joined to campaign items BIDIRECTIONALLY (items that cite it
via directive_ref.item_id, plus items it names in campaign_items) -- either
direction alone misses real mappings. Authored judgements (already-delivered,
already-satisfied, reconciled-with-deviation) are never overwritten.
"""
import json

AUTHORED_FINAL = ("already-delivered", "already-satisfied", "reconciled-with-deviation")
VALID_OWNER = ("LOOP", "HUMAN", "LAB")
VALID_STATUS = ("mapped", "to-file", "already-delivered", "already-satisfied",
                "reconciled-with-deviation", "closed", "blocked", "in-progress")


def reconcile(obligations, campaign_path, directive_id=None):
    """Mutates obligations in place; returns them. Never raises on a campaign
    read failure -- a broken queue must not break the index build."""
    try:
        with open(campaign_path) as fh:
            camp = json.load(fh)
        items = camp["items"] if isinstance(camp, dict) else camp
    except Exception as e:
        print("WARNING: could not read %s (%s); statuses left as authored" % (campaign_path, e))
        return obligations

    by_obl = {}
    for it in items:
        ref = it.get("directive_ref") or {}
        if directive_id and ref.get("doc") not in (None, directive_id):
            continue                      # another directive's item, same obligation id
        oid = ref.get("item_id")
        if oid:
            by_obl.setdefault(oid, []).append(it)

    for o in obligations:
        hits = by_obl.get(o["id"], [])
        named = [i for i in items if i["id"] in (o.get("campaign_items") or [])]
        joined = {i["id"]: i for i in hits + named}
        if not joined:
            continue
        o["campaign_items"] = sorted(joined)
        if o["status"] in AUTHORED_FINAL:
            continue
        st = {i["status"] for i in joined.values()}
        o["status"] = ("closed" if st == {"done"}
                       else "blocked" if st == {"blocked"}
                       else "in-progress")
    return obligations


def validate(obligations):
    seen = set()
    for o in obligations:
        assert o["id"] not in seen, "duplicate obligation id %s" % o["id"]
        seen.add(o["id"])
        assert o["owner"] in VALID_OWNER, o
        assert o["status"] in VALID_STATUS, o
    return obligations
