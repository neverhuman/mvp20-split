#!/usr/bin/env python3
"""Campaign invariants — the properties campaign.json must always hold.

This is the validator commit 8d76070 claimed already existed and did not; see
directives/CORRECTIONS.md. It is deliberately a standalone, committed, runnable
check rather than an assertion inside a one-shot generator script, because the
whole point is that it can be re-run against the live file by anyone at any time.

The load-bearing invariant is OWNER: an obligation the founder must own
(directive_ref.owner HUMAN or LAB) must never be pending, because a pending item
is one the loop will pick and dispatch a fire against.

  usage: campaign_invariants.py [path/to/campaign.json] [--json]
  exit 0 = all invariants hold; exit 1 = at least one violated
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CAMP = os.environ.get("AMPHORA_CAMPAIGN_PATH",
                              os.path.join(ROOT, "bootstrap", "campaign.json"))
REGISTRY = os.path.join(ROOT, "directives", "REGISTRY.json")


def load_indexes(registry_path, base=None):
    """Return ({(doc_id, obligation_id) -> obligation}, {doc_id -> md_sha256}).
    The registry is the routing truth the launcher itself uses; keying by
    (doc, id) is what lets two directives coexist without id collisions."""
    obl, shas = {}, {}
    base = base or os.path.dirname(os.path.dirname(registry_path))
    try:
        reg = json.load(open(registry_path))
    except Exception:
        return obl, shas
    for doc, ent in (reg.get("directives") or {}).items():
        p = os.path.join(base, ent.get("index_path", ""))
        try:
            idx = json.load(open(p))
        except Exception:
            continue
        for o in idx.get("obligations", []):
            obl[(doc, o["id"])] = o
        shas[doc] = idx.get("directive", {}).get("md_sha256")
    return obl, shas

R, G, B, DIM, OFF = "\033[31m", "\033[32m", "\033[1m", "\033[2m", "\033[0m"
if not sys.stdout.isatty():
    R = G = B = DIM = OFF = ""

VALID_STATUS = {"pending", "done", "blocked"}
FORBIDDEN_PENDING_OWNERS = {"HUMAN", "LAB"}
DEFAULT_BASELINE = os.path.join(ROOT, "tools", "baselines", "campaign.v1.json")


def load_baseline(path):
    try:
        doc = json.load(open(path))
    except (OSError, ValueError):
        return set()
    return {(row.get("severity"), row.get("invariant"), row.get("detail"))
            for row in doc.get("allowed", [])}


def check(camp_path, registry_path):
    """Return a list of (severity, invariant, detail) violations."""
    v = []
    raw = json.load(open(camp_path))
    items = raw["items"] if isinstance(raw, dict) else raw

    obl, shas = load_indexes(registry_path)

    # --- OWNER: the invariant that actually matters ---------------------------
    for it in items:
        owner = (it.get("directive_ref") or {}).get("owner")
        if owner in FORBIDDEN_PENDING_OWNERS and it.get("status") == "pending":
            v.append(("CRITICAL", "owner",
                      "%s is owner=%s but status=pending — the loop would pick and "
                      "dispatch a fire against an obligation it is forbidden to execute"
                      % (it.get("id"), owner)))

    # --- identity and schema --------------------------------------------------
    seen = set()
    for it in items:
        iid = it.get("id")
        if not iid:
            v.append(("CRITICAL", "schema", "item with no id: %s" % str(it)[:120]))
            continue
        if iid in seen:
            v.append(("CRITICAL", "schema", "duplicate id %s — the picker refuses to "
                                            "run at all with duplicate ids" % iid))
        seen.add(iid)
        if not it.get("module"):
            v.append(("CRITICAL", "schema", "%s has no module (picker subscripts it)" % iid))
        st = it.get("status")
        if st not in VALID_STATUS:
            v.append(("HIGH", "schema", "%s has status %r, not one of %s"
                      % (iid, st, sorted(VALID_STATUS))))
        fires, mx = len(it.get("fires") or []), it.get("max_fires")
        if isinstance(mx, int) and fires > mx:
            v.append(("HIGH", "budget", "%s has %d fires but max_fires=%d" % (iid, fires, mx)))

    # --- done_check globs -----------------------------------------------------
    globs = {}
    for it in items:
        dc = it.get("done_check")
        if not isinstance(dc, dict):
            # Legacy items predate the structured check. Not fatal, but a blocked
            # or pending one can never be verified if it is ever reopened.
            if it.get("status") in ("pending", "blocked"):
                v.append(("LOW", "done_check",
                          "%s (status=%s) has no structured done_check — if reopened it "
                          "cannot be mechanically closed" % (it.get("id"), it.get("status"))))
            continue
        g = dc.get("glob") or ""
        if g:
            if g in globs:
                v.append(("CRITICAL", "done_check",
                          "%s and %s share the glob %s — one item's receipt could satisfy "
                          "the other's gate" % (globs[g], it.get("id"), g)))
            globs[g] = it.get("id")
            if not g.startswith((it.get("module") or "") + "/"):
                v.append(("HIGH", "done_check",
                          "%s glob does not start with its own module (%s): %s"
                          % (it.get("id"), it.get("module"), g)))

    # --- directive_ref integrity (keyed by (doc, item_id) across the registry) --
    for it in items:
        dr = it.get("directive_ref")
        if not dr:
            continue
        iid, doc, oid = it.get("id"), dr.get("doc"), dr.get("item_id")
        if obl and doc not in shas:
            v.append(("HIGH", "directive_ref",
                      "%s cites doc %r which the registry does not know — the launcher "
                      "fails such items closed" % (iid, doc)))
            continue
        if obl and (doc, oid) not in obl:
            v.append(("HIGH", "directive_ref",
                      "%s cites obligation %r which is not in %s's index" % (iid, oid, doc)))
            continue
        doc_sha = shas.get(doc)
        if doc_sha and dr.get("md_sha256") != doc_sha:
            v.append(("HIGH", "directive_ref",
                      "%s records md_sha256 %s but %s's index says %s — the item believes it is "
                      "authorised by a different document"
                      % (iid, str(dr.get("md_sha256"))[:12], doc, str(doc_sha)[:12])))
        if obl and dr.get("owner") != obl[(doc, oid)].get("owner"):
            v.append(("HIGH", "directive_ref",
                      "%s says owner=%s but obligation %s says %s"
                      % (iid, dr.get("owner"), oid, obl[(doc, oid)].get("owner"))))

    # --- backlog health / intentional exhausted-rotation mode ----------------
    mods = {it.get("module") for it in items if it.get("module")}
    pend = {}
    for it in items:
        if it.get("status") == "pending":
            pend[it["module"]] = pend.get(it["module"], 0) + 1
    rotation = raw.get("fallback_rotation") if isinstance(raw, dict) else None
    rotation_rows = rotation.get("modules", []) if isinstance(rotation, dict) else []
    rotation_names = [row.get("name") for row in rotation_rows if isinstance(row, dict)]
    exhausted_rotation = not pend and len(rotation_rows) == 30 \
        and len(set(rotation_names)) == 30 \
        and all(name in mods for name in rotation_names) \
        and all(isinstance(row.get("weight", 1), int) and row.get("weight", 1) > 0
                for row in rotation_rows)
    if not pend and not exhausted_rotation:
        v.append(("HIGH", "backlog",
                  "campaign is exhausted without a complete 30-module fallback rotation"))
    if not exhausted_rotation:
        for m in sorted(mods - set(pend)):
            v.append(("HIGH", "backlog", "%s has ZERO pending items — it makes no progress" % m))
        for m in sorted(m for m, n in pend.items() if n == 1):
            v.append(("LOW", "backlog", "%s has only 1 pending item — one fire empties it" % m))
    return v, len(items), len(pend)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    camp = args[0] if args else DEFAULT_CAMP
    registry = REGISTRY
    if args:  # a campaign passed explicitly may sit beside its own registry
        sib = os.path.join(os.path.dirname(os.path.abspath(camp)), "directives", "REGISTRY.json")
        if os.path.exists(sib):
            registry = sib
    v, n_items, n_mods = check(camp, registry)
    baseline = load_baseline(DEFAULT_BASELINE)
    annotated = [(s, i, d, (s, i, d) in baseline) for s, i, d in v]
    new_violations = [row for row in annotated if not row[3]]

    if "--json" in sys.argv:
        json.dump({"campaign": camp, "items": n_items,
                   "mode": "EXHAUSTED_ROTATION" if n_mods == 0 else "CAMPAIGN",
                   "baseline": DEFAULT_BASELINE,
                   "violations":
                   [{"severity": s, "invariant": i, "detail": d, "historical": historical}
                    for s, i, d, historical in annotated],
                   "new_violations": len(new_violations)},
                  sys.stdout, indent=2)
        print()
        return 1 if new_violations else 0

    print(f"{B}Campaign invariants{OFF}  {DIM}{camp}  ({n_items} items, {n_mods} modules with work){OFF}")
    for sev, inv, detail, historical in annotated:
        col = R if sev != "LOW" else DIM
        suffix = " (historical baseline)" if historical else ""
        print(f"  {col}{sev:8s}{OFF} {DIM}[{inv}]{OFF} {detail}{suffix}")
    if not v:
        print(f"  {G}all invariants hold{OFF}")
    elif not new_violations:
        print(f"  {G}no new violations{OFF} ({len(v)} historical baseline)")
    else:
        print(f"\n  {R}{B}{len(new_violations)} new violation(s){OFF}")
    return 1 if new_violations else 0


if __name__ == "__main__":
    sys.exit(main())
