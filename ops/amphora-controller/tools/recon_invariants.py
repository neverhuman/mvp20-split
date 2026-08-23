#!/usr/bin/env python3
"""Recon invariants — the properties the Mandate-A ledgers must always hold.

Runs against the amphora-dataset-recon evidence tree on xbabe2 (over ssh), or
against a local copy for tests. Mechanical enforcement of the directive's
binding rules, so compliance is a check anyone can re-run, not prose:

  R1  disposition   every candidate in the intake manifest has EXACTLY ONE
                    verdict (RECOMMENDED/CONDITIONAL/REJECTED) with a reason;
                    "not selected" without a reason is not a permitted state
  R2  coupling      a RECOMMENDED entry has a non-empty serves{} — every
                    recommendation states what it serves (directive §1)
  R3  quarantine    no discovery-annex entry appears in the primary dataset
                    ledger; the annex is separate and quarantined (§9)
  R4  framing       every ledger line carries framing:"AUDIT-ONLY" (§5)
  R5  native score  a dataset-ledger entry in a non-Latin-script language
                    carries a native_citation containing non-ASCII (§4:
                    native script preserved, not romanization-only)
  R6  chain         every dataset-ledger line's fire_id resolves to a DSSE
                    receipt under evidence/ (the .jsonl ledgers are invisible
                    to the module hash scan, so an unchained line is an
                    unverifiable line)

  usage: recon_invariants.py [--root DIR] [--json] [--self-test]
         default root: ssh xbabe2 copy is NOT implied — pass a local path or
         run from a host that mounts the tree; the launcher-side habit is
         `ssh xbabe2 'python3 -' < tools/recon_invariants.py -- --root ...`

exit 0 = all hold (or vacuously, before any ledger exists); exit 1 = violated
"""
import glob
import base64
import binascii
import json
import os
import sys

MOD = "amphora-dataset-recon"
VERDICTS = {"RECOMMENDED", "CONDITIONAL", "REJECTED"}
NON_LATIN = {"zh", "ja", "ko", "ru"}          # script check applies to these
DEFAULT_BASELINE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "baselines", "recon.v1.json")


def dsse_payload_text(path):
    """Return decoded DSSE payload text for either supported envelope shape."""
    try:
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, ValueError):
        return ""
    if not isinstance(doc, dict):
        return ""
    env = doc
    if "payload" not in env and isinstance(env.get("signature"), dict):
        env = env["signature"]
    payload = env.get("payload")
    if not isinstance(payload, str):
        return ""
    try:
        return base64.b64decode(payload, validate=True).decode("utf-8", "replace")
    except (ValueError, UnicodeError, binascii.Error):
        return ""


def load_baseline(path):
    try:
        doc = json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError):
        return set()
    return {(row.get("rule"), row.get("detail")) for row in doc.get("allowed", [])}


def read_jsonl(path):
    rows = []
    if os.path.exists(path):
        for n, line in enumerate(open(path, encoding="utf-8"), 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append((n, json.loads(line)))
            except ValueError:
                rows.append((n, {"_parse_error": True}))
    return rows


def check(root):
    led = os.path.join(root, MOD, "evidence", "ledgers")
    v = []
    dataset = read_jsonl(os.path.join(led, "dataset-ledger.v1.jsonl"))
    dispo = read_jsonl(os.path.join(led, "disposition-ledger.v1.jsonl"))
    annex = read_jsonl(os.path.join(led, "discovery-annex.v1.jsonl"))
    search = read_jsonl(os.path.join(led, "search-record.v1.jsonl"))

    for n, r in dataset + dispo + annex + search:
        if r.get("_parse_error"):
            v.append(("R0", "unparseable ledger line %d" % n))
    # coverage-map is a single JSON document, not JSONL
    cov_path = os.path.join(led, "coverage-map.v1.json")
    cov = None
    if os.path.exists(cov_path):
        try:
            cov = json.load(open(cov_path, encoding="utf-8"))
        except ValueError:
            v.append(("R0", "coverage-map.v1.json does not parse"))
        if isinstance(cov, dict) and cov.get("framing") != "AUDIT-ONLY":
            v.append(("R4", "coverage-map.v1.json lacks framing:\"AUDIT-ONLY\""))

    # R1: exactly-one-verdict over the intake manifest
    manifest = [r for _, r in dispo if r.get("kind") == "intake-manifest"]
    verdicts = {}
    for n, r in dispo:
        if r.get("candidate_id") and r.get("verdict"):
            verdicts.setdefault(r["candidate_id"], []).append((n, r))
            if r["verdict"] not in VERDICTS:
                v.append(("R1", "line %d: verdict %r not in %s" % (n, r["verdict"], sorted(VERDICTS))))
            if not (r.get("reason") or "").strip():
                v.append(("R1", "line %d: %s has verdict %s with no reason" % (n, r["candidate_id"], r["verdict"])))
    for m in manifest:
        for cand in m.get("candidates", []):
            cid = cand.get("candidate_id") or cand
            n_v = len(verdicts.get(cid, []))
            if n_v == 0:
                v.append(("R1", "manifest candidate %s has NO verdict" % cid))
            elif n_v > 1:
                v.append(("R1", "manifest candidate %s has %d verdicts" % (cid, n_v)))

    # R2: RECOMMENDED serves something
    for n, r in dispo + dataset:
        verdict = r.get("verdict") or (r.get("disposition") or {}).get("verdict")
        if verdict == "RECOMMENDED":
            serves = r.get("serves") or {}
            if not (serves.get("module_gaps") or serves.get("recipe_elements")):
                v.append(("R2", "line %d: RECOMMENDED %s serves nothing" %
                          (n, r.get("candidate_id") or r.get("url_or_doi", "?"))))

    # R3: annex/primary disjointness (by candidate_id and url_or_doi)
    primary_keys = {r.get("candidate_id") for _, r in dataset if r.get("candidate_id")} | \
                   {r.get("url_or_doi") for _, r in dataset if r.get("url_or_doi")}
    for n, r in annex:
        for k in (r.get("candidate_id"), r.get("url_or_doi")):
            if k and k in primary_keys:
                v.append(("R3", "annex line %d: %s ALSO appears in the primary dataset ledger" % (n, k)))

    # R4: framing on every line of every ledger (directive §5: AUDIT-ONLY on
    # every page of every deliverable — the search record included)
    for name, rows in (("dataset-ledger", dataset), ("disposition-ledger", dispo),
                       ("discovery-annex", annex), ("search-record", search)):
        for n, r in rows:
            if not r.get("_parse_error") and r.get("framing") != "AUDIT-ONLY":
                v.append(("R4", "%s line %d lacks framing:\"AUDIT-ONLY\"" % (name, n)))

    # R5: native script preserved for non-Latin languages
    for n, r in dataset:
        lang = (r.get("language") or "").lower()[:2]
        if lang in NON_LATIN:
            nc = r.get("native_citation") or ""
            if not any(ord(ch) > 127 for ch in nc):
                v.append(("R5", "dataset line %d: language=%s but native_citation has no native script" % (n, lang)))

    # R6: every dataset line's fire binds to a receipt
    receipt_blob = ""
    for p in glob.glob(os.path.join(root, MOD, "evidence", "**", "*.dsse.json"), recursive=True):
        receipt_blob += dsse_payload_text(p)
    for n, r in dataset:
        fid = r.get("fire_id")
        if fid and fid not in receipt_blob:
            v.append(("R6", "dataset line %d: fire_id %s appears in no DSSE receipt — unchained append" % (n, fid)))
    return v, {"dataset": len(dataset), "disposition": len(dispo), "annex": len(annex)}


def self_test():
    """Plant one defect per invariant in a scratch tree; every one must fire."""
    import shutil
    import tempfile
    root = tempfile.mkdtemp(prefix="recon-inv-selftest.")
    led = os.path.join(root, MOD, "evidence", "ledgers")
    os.makedirs(led)
    os.makedirs(os.path.join(root, MOD, "evidence", "audit"))
    W = lambda f, rows: open(os.path.join(led, f), "w").write(
        "".join(json.dumps(r) + "\n" for r in rows))
    W("disposition-ledger.v1.jsonl", [
        {"kind": "intake-manifest", "candidates": [{"candidate_id": "cand-A"}, {"candidate_id": "cand-B"}],
         "framing": "AUDIT-ONLY"},
        {"candidate_id": "cand-A", "verdict": "REJECTED", "reason": "", "framing": "AUDIT-ONLY"},   # R1 no reason
        # cand-B: no verdict at all                                                                  # R1 missing
        {"candidate_id": "cand-C", "verdict": "RECOMMENDED", "reason": "good", "serves": {},
         "framing": "AUDIT-ONLY"},                                                                   # R2 empty serves
    ])
    W("dataset-ledger.v1.jsonl", [
        {"candidate_id": "cand-D", "url_or_doi": "doi:10/xyz", "language": "zh",
         "native_citation": "Zhang 2019 (romanized only)", "fire_id": "fire-000",                     # R5 + R6
         "framing": "WRONG"},                                                                        # R4
    ])
    W("discovery-annex.v1.jsonl", [
        {"candidate_id": "cand-D", "framing": "AUDIT-ONLY"},                                         # R3 dup of primary
    ])
    W("search-record.v1.jsonl", [
        {"language": "zh", "queries": ["x"]},                                                        # R4 no framing
    ])
    open(os.path.join(led, "coverage-map.v1.json"), "w").write("{not json")                          # R0 coverage parse
    v, _ = check(root)
    fired = {code for code, _ in v}
    shutil.rmtree(root)
    want = {"R1", "R2", "R3", "R4", "R5", "R6"}
    missing = want - fired
    if missing:
        print("SELF-TEST FAIL: planted defects not caught: %s" % sorted(missing))
        return 1
    print("SELF-TEST PASS: all planted defects caught (%s)" % ", ".join(sorted(fired)))
    return 0


def main():
    if "--self-test" in sys.argv:
        return self_test()
    root = "/home/ubuntu/amphora/build/mvp20-split"
    if "--root" in sys.argv:
        root = sys.argv[sys.argv.index("--root") + 1]
    v, counts = check(root)
    baseline = load_baseline(DEFAULT_BASELINE)
    annotated = [(code, detail, (code, detail) in baseline) for code, detail in v]
    new_violations = [row for row in annotated if not row[2]]
    if "--json" in sys.argv:
        json.dump({"root": root, "counts": counts, "baseline": DEFAULT_BASELINE,
                   "violations": [{"rule": c, "detail": d, "historical": historical}
                                  for c, d, historical in annotated],
                   "new_violations": len(new_violations)}, sys.stdout, indent=2)
        print()
        return 1 if new_violations else 0
    print("Recon invariants  %s  (%s)" % (root, counts))
    for code, detail, historical in annotated:
        print("  %s  %s%s" % (code, detail,
                              " (historical baseline)" if historical else ""))
    if not v:
        print("  all recon invariants hold")
    elif not new_violations:
        print("  no new violations (%d historical baseline)" % len(v))
    else:
        print("  %d new violation(s)" % len(new_violations))
    return 1 if new_violations else 0


if __name__ == "__main__":
    sys.exit(main())
