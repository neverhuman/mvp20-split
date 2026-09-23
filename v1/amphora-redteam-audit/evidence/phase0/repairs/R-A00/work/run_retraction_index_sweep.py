#!/usr/bin/env python3
"""R-A00 canary: portfolio retraction-index completeness sweep.

Pre-registered falsification criterion (fixed BEFORE inspecting any module):
  For every module with >=1 REFUTED verdict in the pinned ledger snapshot,
  amphora-redteam-audit CLAIMS evidence/phase0/kpis/RETRACTION-INDEX.md exists
  in that module AND every receipt path cited in that file's "refuted-by
  receipt (path)" and "superseded-by" table columns resolves to a real file
  on disk (checked relative to the module root, falling back to repo root for
  cross-module pointer paths).

  CLAIM_REFUTED  if >=1 such module is missing the index, OR >=1 cited
                 receipt path in those two columns does not resolve.
  CLAIM_SURVIVED if every such module has the index and every cited path
                 resolves.

Deterministic / re-checkable: reads from a pinned, sha256-recorded snapshot
of logs/falsification-ledger.jsonl (never the live-appending file) so a
concurrent ledger append during this fire cannot change the result. Stdlib
only, no RNG, no wall-clock in the diagnostic body.
"""
import hashlib
import json
import os
import re
import sys

ROOT = "/home/ubuntu/amphora/build/mvp20-split"
LEDGER_SNAPSHOT = os.path.join(
    ROOT, "amphora-redteam-audit/evidence/phase0/repairs/R-A00/work/falsification-ledger.snapshot.jsonl")

PATH_TOK_RE = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_\-./]*\.(?:json|md|py|rs|csv|toml|jsonl|txt)\b")


def sha(b):
    return hashlib.sha256(b).hexdigest()


def clean(tok):
    return tok.strip("`,;()")


def resolve(module, p):
    for candidate in (os.path.join(ROOT, module, p), os.path.join(ROOT, p)):
        if os.path.isfile(candidate):
            return candidate
    return None


def main():
    ledger_bytes = open(LEDGER_SNAPSHOT, "rb").read()
    ledger_sha256 = sha(ledger_bytes)
    lines = [l for l in ledger_bytes.decode().splitlines() if l.strip()]

    refuted_modules = set()
    parse_errors = 0
    for line in lines:
        try:
            d = json.loads(line)
        except Exception:
            parse_errors += 1
            continue
        if d.get("verdict") == "REFUTED":
            m = d.get("module")
            if m:
                refuted_modules.add(m)
    refuted_modules = sorted(refuted_modules)

    coverage = {}
    any_missing = False
    any_dangling = False
    for m in refuted_modules:
        module_root = os.path.join(ROOT, m)
        idx_rel = "evidence/phase0/kpis/RETRACTION-INDEX.md"
        idx_path = os.path.join(module_root, idx_rel)
        present = os.path.isfile(idx_path)
        entry = {"index_present": present, "index_path": os.path.join(m, idx_rel) if present else None}
        if not present:
            entry.update(index_sha256=None, n_rows=0, n_receipt_paths_cited=0,
                          n_rows_with_no_receipt_path=0, receipt_paths_cited=[],
                          n_dangling=0, dangling_paths=[])
            coverage[m] = entry
            any_missing = True
            continue

        idx_bytes = open(idx_path, "rb").read()
        entry["index_sha256"] = sha(idx_bytes)
        text = idx_bytes.decode()
        table_lines = [l for l in text.splitlines() if l.strip().startswith("|")]
        data_rows = [l for l in table_lines if not re.match(r"^\|[\s:-]+\|", l)]
        if data_rows:
            data_rows = data_rows[1:]  # drop header row
        entry["n_rows"] = len(data_rows)

        receipt_paths = set()
        rows_with_no_path = 0
        for row in data_rows:
            cells = row.split("|")
            if len(cells) < 5:
                continue
            refuted_by_cell, superseded_by_cell = cells[2], cells[3]
            row_paths = set()
            for cell in (refuted_by_cell, superseded_by_cell):
                for tok in PATH_TOK_RE.findall(cell):
                    row_paths.add(clean(tok))
            if not row_paths:
                rows_with_no_path += 1
            receipt_paths |= row_paths
        receipt_paths = sorted(receipt_paths)
        entry["n_receipt_paths_cited"] = len(receipt_paths)
        entry["n_rows_with_no_receipt_path"] = rows_with_no_path

        dangling = []
        cited_detail = []
        for p in receipt_paths:
            resolved = resolve(m, p)
            cited_detail.append({
                "cited_path": p,
                "resolved": resolved is not None,
                "resolved_sha256": sha(open(resolved, "rb").read()) if resolved else None,
            })
            if resolved is None:
                dangling.append(p)
        entry["receipt_paths_cited"] = cited_detail
        entry["n_dangling"] = len(dangling)
        entry["dangling_paths"] = dangling
        if dangling:
            any_dangling = True
        coverage[m] = entry

    verdict = "CLAIM_REFUTED" if (any_missing or any_dangling) else "CLAIM_SURVIVED"

    diagnostic = {
        "schema": "amphora.redteam-audit.retraction-index-completeness-sweep.v1",
        "item_id": "R-A00",
        "claim_under_attack": {
            "receipt_path": "logs/falsification-ledger.jsonl",
            "claim_text": ("Every module with >=1 REFUTED ledger verdict has a "
                            "RETRACTION-INDEX.md in evidence/phase0/kpis/ whose rows "
                            "cite resolving receipt paths that exist."),
        },
        "pre_registered_refutation_criteria": {
            "criterion": ("CLAIM_REFUTED if any module with >=1 REFUTED ledger verdict "
                           "lacks evidence/phase0/kpis/RETRACTION-INDEX.md, OR any receipt "
                           "path cited in that file's refuted-by/superseded-by table columns "
                           "fails to resolve to a file on disk (module-relative, falling back "
                           "to repo-root for cross-module pointers). CLAIM_SURVIVED only if "
                           "every such module has the index and every cited path resolves."),
            "any_module_missing_index": any_missing,
            "any_dangling_receipt_path": any_dangling,
            "verdict": verdict,
        },
        "ledger_snapshot": {
            "path": "amphora-redteam-audit/evidence/phase0/repairs/R-A00/work/falsification-ledger.snapshot.jsonl",
            "sha256": ledger_sha256,
            "line_count": len(lines),
            "parse_errors": parse_errors,
        },
        "n_modules_with_refuted_verdict": len(refuted_modules),
        "modules_with_refuted_verdict": refuted_modules,
        "coverage": coverage,
        "summary_counts": {
            "modules_index_present": sum(1 for e in coverage.values() if e["index_present"]),
            "modules_index_missing": sum(1 for e in coverage.values() if not e["index_present"]),
            "modules_with_dangling_paths": sum(1 for e in coverage.values() if e.get("n_dangling", 0) > 0),
            "total_receipt_paths_cited": sum(e.get("n_receipt_paths_cited", 0) for e in coverage.values()),
            "total_dangling_paths": sum(e.get("n_dangling", 0) for e in coverage.values()),
        },
    }
    print(json.dumps(diagnostic, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
