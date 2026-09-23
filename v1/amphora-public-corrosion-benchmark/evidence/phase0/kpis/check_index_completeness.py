#!/usr/bin/env python3
"""
amphora-public-corrosion-benchmark : build-time completeness gate for the
module's consolidated audit-verdicts KPI index.

Repair item R-S07. The defect this exists to catch has recurred twice in
this module's own history: a signed evidence/audit/ (or benchmarks/) receipt
lands on disk and the hand-maintained *-consolidated-kpi index is not
rebuilt to reference it.
  - v1 -> v2 (repair R-A08): consolidated-kpi-staleness-v1 found 2/6 signed
    receipts on disk absent from the v1 index.
  - v2 -> v3 (repair R-N03): the v2 index's own referenced-KPI pointer went
    stale relative to a newly-landed refutation (nist-baseline-material-
    group-extrapolation-v1), even though v2's receipt *enumeration* itself
    was complete.
This script is a mechanical, independent, re-runnable enumerate + set-diff.
It does not re-derive or trust any prior audit's statistics, and it does not
trust the KPI file's own self-reported `completeness_check` field -- it
recomputes the set-diff itself, every run, from what is actually on disk.

Identity key: receipt_path (relative to module root), not audit_id. Some
receipts in this module's own evidence/audit/ tree carry no explicit
`audit_id` field in their signed payload and are stored in the index with
audit_id: null (see completeness_check note in the R-S07 done receipt) --
receipt_path is always present and unambiguous, so it is the correct
completeness key; audit_id is carried in the diagnostic output for
readability only and never drives the gate.

Auto-discovers the currently-live (non-superseded) *-consolidated-kpi DSSE
file by following each candidate's own `supersedes.superseded_path` field,
so this gate does not itself go stale by hardcoding a KPI version number.
Pass --index-path to override discovery (e.g. to point at a copy under a
tempdir for a controlled test).

Usage:
    check_index_completeness.py [--module-root PATH] [--index-path PATH]

Exit code 0 : every on-disk evidence/audit/ (+ benchmarks/) signed receipt
              (excl. evidence/superseded/) is referenced by receipt_path in
              the live consolidated-kpi index's audit_verdicts_index.
Exit code 1 : at least one is not (STALE INDEX -- the recurring defect).
Exit code 2 : structural error (no unique live index found, malformed JSON).

AUDIT_ONLY. Grants no coating-efficacy, product-performance, batch-release,
or corrosion-rank authority. Never modifies, deletes, or re-signs any
receipt or KPI file; read-only over whatever --module-root points at.
"""
import argparse
import base64
import glob
import hashlib
import json
import os
import sys

DEFAULT_MODULE_ROOT = "/home/ubuntu/amphora/build/mvp20-split/amphora-public-corrosion-benchmark"


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_dsse_payload(path):
    """Decode a DSSE-signed receipt's payload. Tolerates this module's two
    on-disk envelope shapes: {"signature": {"payload": <b64>, ...}, ...} and
    a bare {"payload": <b64>, ...}. Does NOT verify the Ed25519 signature --
    this gate's job is completeness (does every receipt appear in the
    index?), not authenticity (is the index itself validly signed?); the
    latter is audited independently and orthogonally (see
    evidence/audit/consolidated-kpi-staleness-v1's own T1)."""
    d = json.load(open(path))
    env = d["signature"] if "signature" in d else d
    return json.loads(base64.b64decode(env["payload"]))


def norm_rel(path, module_root):
    return os.path.relpath(os.path.abspath(path), module_root).replace(os.sep, "/")


def discover_current_index(module_root):
    candidates = sorted(set(
        glob.glob(os.path.join(module_root, "evidence/phase0/kpis/*consolidated-kpi*.json"))
        + glob.glob(os.path.join(module_root, "evidence/phase0/repairs/*/done/*consolidated-kpi*.dsse.json"))
    ))
    candidates = [c for c in candidates if "/superseded/" not in c]

    parsed = {}
    for c in candidates:
        try:
            parsed[c] = load_dsse_payload(c)
        except Exception:
            continue

    superseded_abs = set()
    for c, payload in parsed.items():
        sup = (payload.get("supersedes") or {}).get("superseded_path")
        if sup:
            superseded_abs.add(os.path.normpath(os.path.join(module_root, sup)))

    live = [c for c in parsed if os.path.normpath(c) not in superseded_abs]
    if len(live) != 1:
        raise RuntimeError(
            "expected exactly one live (non-superseded) *-consolidated-kpi index under "
            "evidence/phase0/kpis/ or evidence/phase0/repairs/*/done/, found %d: %r"
            % (len(live), [norm_rel(c, module_root) for c in live])
        )
    return live[0], parsed[live[0]]


def enumerate_on_disk_receipts(module_root):
    patterns = ["evidence/audit/*/*.dsse.json", "benchmarks/*/*.dsse.json"]
    paths = []
    for pat in patterns:
        paths.extend(glob.glob(os.path.join(module_root, pat)))
    paths = sorted(p for p in set(paths) if "/superseded/" not in p)

    receipts = []
    for p in paths:
        rel = norm_rel(p, module_root)
        entry = {"receipt_path": rel, "receipt_sha256": sha256_file(p)}
        try:
            payload = load_dsse_payload(p)
            entry["audit_id"] = payload.get("audit_id") or os.path.basename(os.path.dirname(p))
        except Exception as e:
            entry["audit_id"] = None
            entry["load_error"] = str(e)
        receipts.append(entry)
    return receipts


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--module-root", default=DEFAULT_MODULE_ROOT)
    ap.add_argument("--index-path", default=None,
                     help="Override auto-discovery. Absolute, or relative to --module-root.")
    args = ap.parse_args(argv)

    module_root = os.path.abspath(args.module_root)

    try:
        if args.index_path:
            index_path = (args.index_path if os.path.isabs(args.index_path)
                          else os.path.join(module_root, args.index_path))
            index_path = os.path.abspath(index_path)
            index_payload = load_dsse_payload(index_path)
        else:
            index_path, index_payload = discover_current_index(module_root)
    except Exception as e:
        print(json.dumps({
            "schema": "amphora.public-corrosion-benchmark.check-index-completeness.v1",
            "gate": "ERROR",
            "error": str(e),
        }, indent=2, sort_keys=True))
        return 2

    on_disk = enumerate_on_disk_receipts(module_root)
    on_disk_paths = sorted(set(r["receipt_path"] for r in on_disk))

    indexed_paths = sorted(set(
        (e.get("receipt_path") or "").replace(os.sep, "/")
        for e in index_payload.get("audit_verdicts_index", [])
        if e.get("receipt_path")
    ))

    missing = sorted(set(on_disk_paths) - set(indexed_paths))
    extra = sorted(set(indexed_paths) - set(on_disk_paths))

    result = {
        "schema": "amphora.public-corrosion-benchmark.check-index-completeness.v1",
        "module_root": module_root,
        "index_path": norm_rel(index_path, module_root),
        "index_kpi_id": index_payload.get("kpi_id"),
        "identity_key": "receipt_path",
        "n_on_disk_receipts": len(on_disk_paths),
        "n_indexed_receipt_paths": len(indexed_paths),
        "on_disk_receipt_paths": on_disk_paths,
        "indexed_receipt_paths": indexed_paths,
        "missing_from_index": missing,
        "extra_in_index_not_on_disk": extra,
        "gate": "FAIL_STALE_INDEX" if missing else "PASS",
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
