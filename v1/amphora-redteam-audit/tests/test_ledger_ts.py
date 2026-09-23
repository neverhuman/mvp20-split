"""Regression test for the X-LEDGER-TS parser guard, built from a minimal
sanitized fixture preserving the timestamps and IDs of the two real corrupt
rows formerly read from the operational falsification ledger.

Also serves as the positive control: it asserts that a *naive* bare-parse
(the defect class every unfixed consumer had) fails on these two rows,
then asserts the guard fixes exactly that failure.
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(
    os.environ.get("AMPHORA_ROOT", Path(__file__).resolve().parents[2])
).resolve()
LEDGER = REPO_ROOT / "amphora-redteam-audit/tests/fixtures/ledger_ts.jsonl"

sys.path.insert(0, str(REPO_ROOT / "amphora-redteam-audit/src"))
from amphora_redteam_audit.ledger_ts import (  # noqa: E402
    clean_ledger_ts, parse_ledger_ts, ledger_sort_key,
)

CORRUPT_FIRE_IDS = {
    "20260803T150004-335042-88e86edf7333": {
        "module": "amphora-ip-fto-guard",
        "expected_ts": datetime(2026, 8, 3, 15, 8, 37, tzinfo=timezone.utc),
    },
    "20260804T100001-3937441-823cffd3f9d8": {
        "module": "amphora-sourceability-ehs",
        "expected_ts": datetime(2026, 8, 4, 10, 7, 20, tzinfo=timezone.utc),
    },
}


def _load_corrupt_rows():
    found = {}
    with open(LEDGER) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            fid = rec.get("fire_id")
            if fid in CORRUPT_FIRE_IDS:
                found[fid] = rec
    return found


def test_two_real_corrupt_rows_present_and_actually_corrupt():
    rows = _load_corrupt_rows()
    assert set(rows) == set(CORRUPT_FIRE_IDS), (
        f"expected exactly the 2 known corrupt fire_ids, found {sorted(rows)}"
    )
    for fid, rec in rows.items():
        assert rec["module"] == CORRUPT_FIRE_IDS[fid]["module"]
        raw_ts = rec["ts"]
        assert raw_ts.startswith("\\"), f"row {fid} ts is no longer corrupt: {raw_ts!r}"


def test_naive_bare_parse_fails_on_real_corrupt_rows_positive_control():
    """POSITIVE CONTROL: the defect this guard exists to catch (a bare
    datetime.fromisoformat on the raw ts) really does fail on the two real
    corrupt rows -- i.e. an unguarded consumer really is broken."""
    rows = _load_corrupt_rows()
    for fid, rec in rows.items():
        raw_ts = rec["ts"]
        threw = False
        try:
            datetime.fromisoformat(raw_ts.replace("Z", "+00:00"))
        except ValueError:
            threw = True
        assert threw, f"expected bare fromisoformat to raise on real corrupt row {fid}"


def test_guard_parses_real_corrupt_rows_correctly():
    rows = _load_corrupt_rows()
    for fid, rec in rows.items():
        parsed = parse_ledger_ts(rec["ts"])
        assert parsed == CORRUPT_FIRE_IDS[fid]["expected_ts"], (
            fid, parsed, CORRUPT_FIRE_IDS[fid]["expected_ts"]
        )


def test_guard_clean_ts_strips_exactly_the_stray_backslash():
    rows = _load_corrupt_rows()
    for fid, rec in rows.items():
        cleaned = clean_ledger_ts(rec["ts"])
        assert not cleaned.startswith("\\")
        assert cleaned == rec["ts"][1:]


def test_guard_is_idempotent_on_clean_rows():
    with open(LEDGER) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if rec.get("fire_id") in CORRUPT_FIRE_IDS:
                continue
            raw_ts = rec.get("ts")
            if not raw_ts or not raw_ts[:1].isdigit():
                continue
            assert clean_ledger_ts(raw_ts) == raw_ts
            parse_ledger_ts(raw_ts)
            break
        else:
            raise AssertionError("no clean comparison row found in ledger")


def test_sort_key_restores_chronological_order_despite_corruption():
    """Naive string-sort on raw ts pushes both corrupt rows to the very end
    (since '\\' > every digit); ledger_sort_key must instead place each row
    in its true chronological position relative to its real neighbours."""
    rows = _load_corrupt_rows()
    all_recs = []
    with open(LEDGER) as f:
        for line in f:
            line = line.strip()
            if line:
                all_recs.append(json.loads(line))

    naive_sorted = sorted(all_recs, key=lambda r: r.get("ts") or "")
    naive_positions = [i for i, r in enumerate(naive_sorted)
                        if r.get("fire_id") in CORRUPT_FIRE_IDS]
    assert naive_positions == [len(all_recs) - 2, len(all_recs) - 1], (
        "expected the naive raw-string sort to mis-place both corrupt rows "
        f"at the very end; got positions {naive_positions} of {len(all_recs)}"
    )

    guarded_sorted = sorted(all_recs, key=ledger_sort_key)
    guarded_index_by_fid = {r.get("fire_id"): i for i, r in enumerate(guarded_sorted)}
    for fid in CORRUPT_FIRE_IDS:
        idx = guarded_index_by_fid[fid]
        expected_ts = CORRUPT_FIRE_IDS[fid]["expected_ts"]
        if idx > 0:
            prev_ts = parse_ledger_ts(guarded_sorted[idx - 1]["ts"])
            assert prev_ts <= expected_ts, (fid, "predecessor out of order")
        if idx < len(guarded_sorted) - 1:
            next_ts = parse_ledger_ts(guarded_sorted[idx + 1]["ts"])
            assert expected_ts <= next_ts, (fid, "successor out of order")


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    results = {}
    for t in tests:
        try:
            t()
            results[t.__name__] = "PASS"
        except Exception as e:  # noqa: BLE001
            results[t.__name__] = f"FAIL: {type(e).__name__}: {e}"
    print(json.dumps(results, indent=2))
    n_fail = sum(1 for v in results.values() if not v.startswith("PASS"))
    sys.exit(1 if n_fail else 0)
