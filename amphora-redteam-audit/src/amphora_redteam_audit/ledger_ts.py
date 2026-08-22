"""Tolerant reader for the `ts` field of logs/falsification-ledger.jsonl.

The ledger is append-only. Two historical rows carry a stray leading
backslash in `ts`, written by a since-fixed shell-substitution bug in the
ledger-append template (the template now builds ts via jq `(now|todate)`
with no shell substitution, so no new corrupt rows can appear):

  - fire 20260803T150004-335042-88e86edf7333 (module amphora-ip-fto-guard),
    ledger line 56: ts == "\\2026-08-03T15:08:37+00:00"
  - fire 20260804T100001-3937441-823cffd3f9d8 (module amphora-sourceability-ehs),
    ledger line 75: ts == "\\2026-08-04T10:07:20+00:00"

Those two rows are permanent (fixing the ledger in place would violate
append-only and destroy tamper-evidence). Every reader of ledger `ts`
values should go through this module instead of parsing `ts` directly, so
the two corrupt rows are read correctly rather than raising or sorting out
of chronological order (a bare leading backslash is ASCII 0x5C, which sorts
after every digit 0x30-0x39, so naive string-sorting on raw `ts` pushes
both corrupt rows to the end regardless of their real date).
"""
from datetime import datetime

_LEADING_BACKSLASH = "\\"


def clean_ledger_ts(ts):
    """Strip any stray leading backslash(es) from a raw ledger ts string.

    Idempotent: a clean ts is returned unchanged.
    """
    if ts is None:
        return ts
    s = str(ts)
    while s.startswith(_LEADING_BACKSLASH):
        s = s[1:]
    return s


def parse_ledger_ts(ts):
    """Parse a raw ledger `ts` field into an aware datetime.

    Tolerates the leading-backslash corruption on the two known-permanent
    rows; otherwise behaves exactly like `datetime.fromisoformat` on an
    ISO-8601 string (accepting a trailing 'Z' as UTC).
    """
    s = clean_ledger_ts(ts).replace("Z", "+00:00")
    return datetime.fromisoformat(s)


def ledger_sort_key(record):
    """Chronological string sort key for a parsed ledger JSON record.

    Safe against the leading-backslash corruption: sorting directly on
    record["ts"] would place the two corrupt rows after every normal row
    regardless of their real timestamp, because '\\' (0x5C) sorts after
    every ASCII digit. This strips the corruption first so lexicographic
    order on the returned string matches chronological order.
    """
    return clean_ledger_ts(record.get("ts") or "")
