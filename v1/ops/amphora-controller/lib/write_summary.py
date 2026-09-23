#!/usr/bin/env python3
"""write_summary.py — append one fire-summary record.

The agent's RUN_SUMMARY_JSON arrives on STDIN (never on argv: v2 passed
`artifacts`/`claim_tested` as argv and a large value tripped execve E2BIG,
which discarded every verification field for that fire). Launcher-computed
fields arrive as argv, which are all short and shell-safe.

Truncation is codepoint-safe (v2 used `head -c`, which splits UTF-8).

The append is a single os.write() on an O_APPEND fd. With concurrent lanes the
offset is claimed atomically per syscall; Python's buffered writer splits any
payload over 8192 bytes into multiple write()s, which is exactly how one lane's
line ends up interleaved through another's. Every unbounded field is clipped so
the record cannot reach that size even in the worst legal case.
"""
import json
import os
import sys

FIELDS = [
    "path", "ts", "module", "mode", "model", "campaign_item_id",
    "item_status_applied", "outcome", "outcome_raw", "fire_id",
    "signing_check", "protected_check", "runtime_s", "verified_new_signed",
    "signing_violations", "ledger_has_fire_id", "directive_ref",
    # Why the fire ended as it did. Without these, "the agent ran and learned
    # nothing" and "the agent never ran" were the same record, and the stall of
    # 2026-08-06 could only be diagnosed by grepping prose out of the log.
    "agent_rc", "fire_class",
    # Which of the (up to four) lanes ran this fire. Default "1" so a launcher
    # that predates lanes still writes valid records.
    "lane",
]


def as_json(value, max_bytes=2000):
    """argv carries the item's directive_ref as a JSON string; store it as an
    object. Bounded: an oversized value is truncated to a marker rather than
    stored -- directive_ref is a six-key record (~260 B in practice) and
    anything larger is malformed input, not data to preserve."""
    try:
        v = json.loads(value) if value else None
    except ValueError:
        return None
    if v and len(json.dumps(v)) > max_bytes:
        return {"_clipped": True, "_reason": "directive_ref exceeded %dB" % max_bytes}
    return v or None


def clip(value, n=400):
    return str(value)[:n]


def main():
    a = dict(zip(FIELDS, sys.argv[1:]))
    raw = sys.stdin.read().strip()
    try:
        payload = json.loads(raw) if raw else {}
        if not isinstance(payload, dict):
            payload = {}
    except ValueError:
        payload = {}

    def as_int(v, default=0):
        try:
            return int(v)
        except (TypeError, ValueError):
            return default

    rec = {
        "ts": a.get("ts", ""),
        "fire_id": a.get("fire_id", ""),
        "module": a.get("module", ""),
        "mode": a.get("mode", ""),
        "model": a.get("model", ""),
        "campaign_item_id": a.get("campaign_item_id", ""),
        "item_status_applied": a.get("item_status_applied", ""),
        "outcome": a.get("outcome", "UNKNOWN"),
        "outcome_raw": a.get("outcome_raw", ""),
        "signing_check": a.get("signing_check", ""),
        "protected_check": a.get("protected_check", ""),
        "runtime_s": as_int(a.get("runtime_s")),
        "agent_rc": as_int(a.get("agent_rc"), None),
        "fire_class": a.get("fire_class", ""),
        "verified_new_signed": as_int(a.get("verified_new_signed")),
        "signing_violations": as_int(a.get("signing_violations")),
        "ledger_has_fire_id": a.get("ledger_has_fire_id") == "true",
        "claim_tested": clip(payload.get("claim_tested", "")),
        "attack_type": clip(payload.get("attack_type", "")),
        "verdict_summary": clip(payload.get("verdict_summary", "")),
        # 16x200 keeps the worst legal record under 8192 B, so even a torn-free
        # single write() is also a single page -- belt and braces.
        "artifacts": [clip(x, 200) for x in (payload.get("artifacts") or [])][:16],
        "receipts_added": as_int(payload.get("receipts_added")),
        "data_asks_added": as_int(payload.get("data_asks_added")),
        "notes": clip(payload.get("notes", "")),
        # Which founder-directive obligation this fire served. The launcher
        # supplies the authoritative value from the campaign item; the agent's
        # own echo is kept beside it so the two can be compared -- a fire that
        # reports a different obligation than the one it was given is worth
        # seeing, and collapsing them into one field would hide that.
        "directive_ref": as_json(a.get("directive_ref")),
        # Agent-supplied and previously unbounded -- the one field that could
        # push the record past a single write().
        "directive_ref_reported": as_json(json.dumps(payload.get("directive_ref")))
        if payload.get("directive_ref") else None,
        "lane": a.get("lane", "1"),
    }
    data = (json.dumps(rec) + "\n").encode()
    fd = os.open(a["path"], os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
    try:
        os.write(fd, data)
    finally:
        os.close(fd)


if __name__ == "__main__":
    main()
