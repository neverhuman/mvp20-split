#!/usr/bin/env python3
"""V1-RESOLVE: portfolio-wide RETRACTION-INDEX resolution sweep.

Escalates R-A00 (presence-only) to RESOLUTION: for every row of every
module's RETRACTION-INDEX.md, checks:
  (a) exists  - superseded-by target(s) resolve to a real file on disk
               (a literal 'PENDING' token is a hard failure for that row)
  (b) verifies - if the resolved target is JSON carrying a top-level or
               nested {payload, payloadType, signatures:[{keyid,sig}]}
               DSSE envelope, the Ed25519 signature verifies against the
               single pinned PHASE0_EVALUATOR key in
               config/phase0-trust-store.v1.json
  (c) covers  - LEFT NULL here; filled in by a human-in-the-loop-style
               read-and-judge pass (sign_v1_resolve.py) after this
               diagnostic is emitted, because judging whether a payload's
               *content* actually addresses a specific refuted claim is a
               semantic task this mechanical sweep cannot perform honestly.

Deterministic / re-checkable: pure filesystem read + regex parse over the
live module trees at read time. No RNG, no wall-clock embedded in the body
(the sweep is re-run twice and byte-diffed by the caller for the two-replay
gate; only the read timestamp is intentionally excluded from the payload).
"""
import base64
import hashlib
import json
import os
import re

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

ROOT = "/home/ubuntu/amphora/build/mvp20-split"
TRUST = os.path.join(ROOT, "config/phase0-trust-store.v1.json")

PATH_TOK_RE = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_\-./]*\.(?:json|md|py|rs|csv|toml|jsonl|txt)\b")


def sha(b):
    return hashlib.sha256(b).hexdigest()


def clean(tok):
    return tok.strip("`,;()")


def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" "
            + str(len(body)).encode() + b" " + body)


def load_trust():
    trust = json.loads(open(TRUST, "rb").read())
    by_role = {k["role"]: k for k in trust["keys"]}
    ev = by_role["PHASE0_EVALUATOR"]
    assert not ev["revoked"] and ev["phase0_authorized"]
    return ev["key_id"], bytes.fromhex(ev["public_key_hex"])


EVAL_KEY_ID, EVAL_PUB_BYTES = load_trust()
EVAL_PUBKEY = Ed25519PublicKey.from_public_bytes(EVAL_PUB_BYTES)


def find_dsse_envelope(d):
    """Find a dict with payload/payloadType/signatures, top-level or one level nested."""
    if isinstance(d, dict) and {"payload", "payloadType", "signatures"} <= set(d.keys()):
        return d
    if isinstance(d, dict):
        for v in d.values():
            if isinstance(v, dict) and {"payload", "payloadType", "signatures"} <= set(v.keys()):
                return v
    return None


def verify_dsse(path):
    """Returns dict describing DSSE verification outcome for a JSON file, or None if not JSON/no envelope."""
    try:
        raw = open(path, "rb").read()
        d = json.loads(raw)
    except Exception:
        return None
    env = find_dsse_envelope(d)
    if env is None:
        return {"is_dsse": False}
    try:
        body = base64.standard_b64decode(env["payload"])
        ptype = env["payloadType"]
        sigs = env["signatures"]
    except Exception as e:
        return {"is_dsse": True, "verifies": False, "reason": f"malformed envelope: {e}"}
    verified_keyids = []
    for s in sigs:
        keyid = s.get("keyid")
        try:
            sig = base64.standard_b64decode(s["sig"])
        except Exception:
            continue
        if keyid != EVAL_KEY_ID:
            continue
        try:
            EVAL_PUBKEY.verify(sig, pae(ptype, body))
            verified_keyids.append(keyid)
        except InvalidSignature:
            pass
    return {
        "is_dsse": True,
        "verifies": EVAL_KEY_ID in verified_keyids,
        "verified_against_pinned_evaluator_key": EVAL_KEY_ID in verified_keyids,
        "keyids_present": [s.get("keyid") for s in sigs],
        "pinned_evaluator_key_id": EVAL_KEY_ID,
        "payload_sha256": sha(body),
    }


def resolve(module, p):
    for candidate in (os.path.join(ROOT, module, p), os.path.join(ROOT, p)):
        if os.path.isfile(candidate):
            return candidate
    return None


def extract_paths(cell_text):
    return sorted({clean(t) for t in PATH_TOK_RE.findall(cell_text)})


def parse_table_rows(text):
    """Yields (claim, refuted_by_cell, superseded_by_cell) for markdown-table rows.
    Header column order varies (4 or 5 cols); locate by header name."""
    lines = text.splitlines()
    i = 0
    rows = []
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("|") and "---" not in line:
            header_cells = [c.strip().lower() for c in line.strip().strip("|").split("|")]
            if i + 1 < len(lines) and re.match(r"^\|[\s:-]+\|", lines[i + 1]):
                # this is a header row
                claim_idx = next((j for j, h in enumerate(header_cells) if "claim" in h), 0)
                refby_idx = next((j for j, h in enumerate(header_cells) if "refuted-by" in h or "refuted by" in h), None)
                supby_idx = next((j for j, h in enumerate(header_cells) if "superseded-by" in h or "superseded by" in h), None)
                j = i + 2
                while j < len(lines) and lines[j].strip().startswith("|"):
                    cells = [c.strip() for c in lines[j].strip().strip("|").split("|")]
                    claim = cells[claim_idx] if claim_idx is not None and claim_idx < len(cells) else ""
                    refby = cells[refby_idx] if refby_idx is not None and refby_idx < len(cells) else ""
                    supby = cells[supby_idx] if supby_idx is not None and supby_idx < len(cells) else ""
                    rows.append((claim, refby, supby))
                    j += 1
                i = j
                continue
        i += 1
    return rows


def parse_bullet_rows(text):
    """amphora-tolerance-robustness style: '## <claim>' followed by '- refuted-by: ...' / '- superseded-by: ...'."""
    rows = []
    blocks = re.split(r"\n##\s+", text)
    for block in blocks[1:]:
        lines = block.splitlines()
        claim = lines[0].strip()
        refby = ""
        supby = ""
        for l in lines[1:]:
            ls = l.strip()
            if ls.lower().startswith("- refuted-by:"):
                refby = ls.split(":", 1)[1].strip()
            elif ls.lower().startswith("- superseded-by:"):
                supby = ls.split(":", 1)[1].strip()
        if refby or supby:
            rows.append((claim, refby, supby))
    return rows


def main():
    index_files = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in (".git",)]
        for fn in filenames:
            if fn == "RETRACTION-INDEX.md":
                index_files.append(os.path.join(dirpath, fn))
    index_files.sort()

    modules_out = {}
    all_rows = []
    distinct_paths = {}  # cited path -> verification result (dedup)

    for idx_path in index_files:
        rel_idx = os.path.relpath(idx_path, ROOT)
        module = rel_idx.split("/")[0]
        text = open(idx_path, "rb").read().decode()
        idx_sha = sha(open(idx_path, "rb").read())

        table_rows = parse_table_rows(text)
        rows = table_rows if table_rows else parse_bullet_rows(text)

        module_rows = []
        for claim, refby_cell, supby_cell in rows:
            supby_paths = extract_paths(supby_cell)
            refby_paths = extract_paths(refby_cell)
            literal_pending = bool(re.search(r"\bPENDING\b", supby_cell))
            row_entry = {
                "module": module,
                "index_path": rel_idx,
                "claim_excerpt": claim[:220],
                "refuted_by_cell": refby_cell[:400],
                "superseded_by_cell": supby_cell[:600],
                "superseded_by_paths_cited": supby_paths,
                "refuted_by_paths_cited": refby_paths,
                "literal_pending": literal_pending,
            }
            per_path = []
            for p in supby_paths:
                resolved = resolve(module, p)
                key = resolved if resolved else f"UNRESOLVED::{module}::{p}"
                if key not in distinct_paths:
                    result = {"cited_path": p, "module": module, "resolved_path": resolved,
                              "exists": resolved is not None}
                    if resolved:
                        result["sha256"] = sha(open(resolved, "rb").read())
                        dsse = verify_dsse(resolved)
                        result["dsse"] = dsse if dsse is not None else {"is_dsse": False}
                    distinct_paths[key] = result
                per_path.append(key)
            row_entry["superseded_by_resolved_keys"] = per_path
            row_entry["superseded_by_exists"] = (
                False if literal_pending
                else (bool(supby_paths) and all(distinct_paths[k]["exists"] for k in per_path))
            )
            row_entry["superseded_by_verifies"] = (
                False if literal_pending
                else (bool(supby_paths) and all(
                    distinct_paths[k].get("dsse", {}).get("verifies", False)
                    or distinct_paths[k].get("dsse", {}).get("is_dsse") is False  # non-JSON supporting doc, not itself signed
                    for k in per_path))
            )
            module_rows.append(row_entry)
            all_rows.append(row_entry)
        modules_out[module] = {"index_path": rel_idx, "index_sha256": idx_sha, "n_rows": len(module_rows),
                                "rows": module_rows}

    n_rows = len(all_rows)
    n_pending = sum(1 for r in all_rows if r["literal_pending"])
    n_no_path = sum(1 for r in all_rows if not r["literal_pending"] and not r["superseded_by_paths_cited"])
    n_dangling = sum(1 for r in all_rows if not r["literal_pending"] and r["superseded_by_paths_cited"]
                      and not r["superseded_by_exists"])

    diagnostic = {
        "schema": "amphora.redteam-audit.v1-resolve-retraction-resolution-sweep.v1",
        "item_id": "V1-RESOLVE",
        "index_files_found": [os.path.relpath(p, ROOT) for p in index_files],
        "n_index_files": len(index_files),
        "modules": modules_out,
        "distinct_superseded_by_targets": distinct_paths,
        "n_distinct_superseded_by_targets": len(distinct_paths),
        "summary_counts": {
            "n_rows_total": n_rows,
            "n_rows_literal_pending": n_pending,
            "n_rows_no_superseded_by_path_cited": n_no_path,
            "n_rows_dangling_superseded_by_path": n_dangling,
        },
        "trust_store": {"pinned_evaluator_key_id": EVAL_KEY_ID},
    }
    print(json.dumps(diagnostic, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
