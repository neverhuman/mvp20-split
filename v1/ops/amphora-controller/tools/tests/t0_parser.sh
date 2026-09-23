#!/usr/bin/env bash
# T0: quota reset parser, with "now" pinned so the real 2026-08-06 transcript is
# evaluated as of the moment it was actually emitted.
set -uo pipefail
P="$(cd "$(dirname "$0")/../.." && pwd)/lib/parse_quota_reset.py"
AUG6=$(date -u -d '2026-08-06T10:37:00Z' +%s)
pass=0; fail=0
NOW=$AUG6
t() { # t <label> <expected iso|expected how> <raw> [field]
    local got
    got=$(QUOTA_NOW_EPOCH=$NOW python3 "$P" "$3")
    local epoch=${got%% *} how=${got#* }
    local actual
    if [ "${4:-iso}" = how ]; then actual=$how
    else actual=$(date -u -d "@$epoch" +%Y-%m-%dT%H:%M:%SZ); fi
    if [ "$actual" = "$2" ]; then echo "  PASS  $1"; pass=$((pass+1))
    else echo "  FAIL  $1: expected [$2] got [$actual]"; fail=$((fail+1)); fi
}

echo "T0: quota reset parsing (now pinned to 2026-08-06T10:37Z)"
t "real Aug-6 message -> Aug 7 12:00 UTC" "2026-08-07T12:00:00Z" "resets Aug 7, 12pm (UTC)"
t "  ... classified as dated"             "dated"                "resets Aug 7, 12pm (UTC)" how
t "bare '12pm' -> next 12:00"             "2026-08-06T12:00:00Z" "resets 12pm (UTC)"
t "bare '9am' already passed -> tomorrow" "2026-08-07T09:00:00Z" "resets 9am (UTC)"
t "midnight 12am -> 00:00 next day"       "2026-08-07T00:00:00Z" "resets 12am (UTC)"
t "with minutes"                          "2026-08-07T12:30:00Z" "resets Aug 7, 12:30pm (UTC)"
t "24h clock, no am/pm"                   "2026-08-07T14:00:00Z" "resets Aug 7, 14 (UTC)"
t "unparseable -> 6h fallback"            "2026-08-06T16:37:00Z" "try again later"
t "  ... classified as fallback"          "fallback"             "try again later" how
t "reset already in the past -> 5m retry" "2026-08-06T10:42:00Z" "resets Aug 1, 12pm (UTC)"
t "  ... classified as already-passed"    "already-passed"       "resets Aug 1, 12pm (UTC)" how
t "garbage hour 99 -> fallback"           "2026-08-06T16:37:00Z" "resets Aug 7, 99pm (UTC)"
t "absurd future clamped to 8d"           "2026-08-14T10:37:00Z" "resets Dec 31, 11pm (UTC)"

# The message carries no year, so a hold requested on Dec 30 for "Jan 2" must
# roll into the next year rather than resolve 363 days into the past.
NOW=$(date -u -d '2026-12-30T23:00:00Z' +%s)
t "Dec->Jan rollover resolves forward"    "2027-01-02T12:00:00Z" "resets Jan 2, 12pm (UTC)"
t "  ... and is not the past-reset branch" "dated"               "resets Jan 2, 12pm (UTC)" how
NOW=$AUG6

echo; echo "== $pass passed, $fail failed =="; [ "$fail" -eq 0 ]
