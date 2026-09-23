#!/usr/bin/env python3
"""Directive coverage — what has the founder directive actually bought us?

Joins the directive index x campaign.json x fire-summary.jsonl and reports, per
obligation: owner, status, the campaign items serving it, fires spent, and the
receipts produced.

The point of this tool is the two failure lists, not the pretty table:

  UNMAPPED  a founder obligation with no campaign item behind it -- work we owe
            and have not queued. This is how an obligation gets silently dropped.
  ORPHAN    a campaign item claiming a directive_ref that does not resolve, or
            whose recorded document hash does not match the index -- work that
            believes it is authorised by a document that does not say so.

Exits non-zero if either list is non-empty, so it can gate a deploy.

  usage: directive_coverage.py [--json] [--quiet]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IDX = os.path.join(ROOT, "directives", "2026-08-05-closing-the-open-portfolio.index.json")
CAMP = os.path.join(ROOT, "campaign.json")
FIRES = os.path.join(ROOT, "logs", "fire-summary.jsonl")

G, R, Y, B, DIM, OFF = "\033[32m", "\033[31m", "\033[33m", "\033[1m", "\033[2m", "\033[0m"
if not sys.stdout.isatty():
    G = R = Y = B = DIM = OFF = ""


def load():
    idx = json.load(open(IDX))
    raw = json.load(open(CAMP))
    items = raw["items"] if isinstance(raw, dict) else raw
    fires = []
    if os.path.exists(FIRES):
        for line in open(FIRES):
            line = line.strip()
            if not line:
                continue
            try:
                fires.append(json.loads(line))
            except ValueError:
                continue          # a truncated tail line must not break the report
    return idx, items, fires


def build(idx, items, fires):
    obl = {o["id"]: o for o in idx["obligations"]}
    doc_sha = idx["directive"]["md_sha256"]
    by_id = {i["id"]: i for i in items}

    # campaign items grouped by the obligation they claim
    claimed, orphans = {}, []
    for it in items:
        dr = it.get("directive_ref")
        if not dr:
            continue
        oid = dr.get("item_id")
        if oid not in obl:
            orphans.append((it["id"], "claims unknown obligation %r" % oid))
            continue
        if dr.get("md_sha256") != doc_sha:
            orphans.append((it["id"], "directive_ref hash %s != index %s"
                            % (str(dr.get("md_sha256"))[:12], doc_sha[:12])))
            continue
        claimed.setdefault(oid, []).append(it)

    # fires and receipts, per campaign item
    fires_by_item, receipts_by_item = {}, {}
    for f in fires:
        cid = f.get("campaign_item_id")
        if not cid:
            continue
        fires_by_item[cid] = fires_by_item.get(cid, 0) + 1
        for a in (f.get("artifacts") or []):
            receipts_by_item.setdefault(cid, set()).add(a)

    rows, unmapped = [], []
    for oid, o in obl.items():
        # An obligation is served by the items the index names AND by any item
        # that claims it -- either direction alone would miss a real mapping.
        served = {i["id"] for i in claimed.get(oid, [])} | {
            c for c in o.get("campaign_items", []) if c in by_id}
        served = sorted(served)
        st = o.get("status", "mapped")
        n_fires = sum(fires_by_item.get(c, 0) for c in served)
        recs = set()
        for c in served:
            recs |= receipts_by_item.get(c, set())
        statuses = [by_id[c]["status"] for c in served if c in by_id]
        if not served and st in ("mapped", "to-file"):
            unmapped.append((oid, o["owner"], o.get("title", "")))
        rows.append({
            "id": oid, "section": o["section"], "owner": o["owner"],
            "title": o.get("title", ""), "index_status": st,
            "campaign_items": served, "item_statuses": statuses,
            "fires": n_fires, "receipts": sorted(recs),
            "closed": bool(statuses) and all(s == "done" for s in statuses),
        })
    rows.sort(key=lambda r: (r["owner"] != "LOOP", r["section"], r["id"]))
    return rows, unmapped, orphans


def main():
    as_json = "--json" in sys.argv
    quiet = "--quiet" in sys.argv
    idx, items, fires = load()
    rows, unmapped, orphans = build(idx, items, fires)

    if as_json:
        json.dump({"directive": idx["directive"], "rows": rows,
                   "unmapped": unmapped, "orphans": orphans}, sys.stdout, indent=2)
        print()
        return 1 if (unmapped or orphans) else 0

    d = idx["directive"]
    print(f"{B}Directive coverage — {d['title'][:70]}{OFF}")
    print(f"{DIM}  {d['md_path']}  sha256 {d['md_sha256'][:16]}…  (canonical on {d['host']}){OFF}\n")

    if not quiet:
        cur = None
        for r in rows:
            if r["owner"] != cur:
                cur = r["owner"]
                print(f"{B}── {cur} {'─' * (58 - len(cur))}{OFF}")
            if r["closed"]:
                mark, col = "✓", G
            elif r["index_status"] in ("already-delivered", "already-satisfied"):
                mark, col = "✓", G
            elif r["index_status"] == "reconciled-with-deviation":
                mark, col = "≠", Y
            elif not r["campaign_items"]:
                mark, col = "!", R
            else:
                mark, col = "·", DIM
            served = ",".join(r["campaign_items"]) or "—"
            print(f"  {col}{mark}{OFF} {r['id']:18s} {r['section']:5s} {served:26s} "
                  f"fires={r['fires']:<3d} {DIM}{r['title'][:44]}{OFF}")
        print()

    n = len(rows)
    closed = sum(1 for r in rows if r["closed"] or
                 r["index_status"] in ("already-delivered", "already-satisfied"))
    by_owner = {}
    for r in rows:
        by_owner.setdefault(r["owner"], [0, 0])
        by_owner[r["owner"]][0] += 1
        if r["closed"] or r["index_status"] in ("already-delivered", "already-satisfied"):
            by_owner[r["owner"]][1] += 1
    print(f"{B}Coverage{OFF}  {closed}/{n} obligations closed  " +
          "  ".join(f"{k} {v[1]}/{v[0]}" for k, v in sorted(by_owner.items())))
    print(f"          {sum(r['fires'] for r in rows)} fires spent against directive obligations, "
          f"{len({x for r in rows for x in r['receipts']})} distinct receipts")

    bad = False
    if unmapped:
        bad = True
        print(f"\n{R}{B}UNMAPPED — obligations with no campaign item ({len(unmapped)}){OFF}")
        for oid, owner, title in unmapped:
            print(f"  {R}!{OFF} {oid:18s} [{owner}] {title[:60]}")
    if orphans:
        bad = True
        print(f"\n{R}{B}ORPHAN — items citing an unresolvable directive_ref ({len(orphans)}){OFF}")
        for cid, why in orphans:
            print(f"  {R}!{OFF} {cid:18s} {why}")
    if not bad:
        print(f"\n{G}Every obligation has an owner and every directive_ref resolves.{OFF}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
