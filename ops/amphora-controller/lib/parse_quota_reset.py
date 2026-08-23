#!/usr/bin/env python3
"""parse_quota_reset.py — turn a usage-limit refusal into a hold deadline.

When the agent is refused for quota it says so in prose, e.g.

    You've hit your weekly limit · resets Aug 7, 12pm (UTC)
    You've hit your weekly limit · resets 12pm (UTC)

v3 threw that sentence away, counted the refusal as an exhausted hour, and
after three of them latched the saturation gate for 80 hours. The reset time
is the one piece of information that says when firing can usefully resume, so
it is parsed here and turned into an epoch the launcher holds against.

Fails safe in both directions. An unparseable message still produces a hold
(never "no hold", which is how the loop burned three fires it could not win),
and no parse can produce a hold longer than max_hold (never "forever", which
is the failure this whole change exists to remove).

Reads the transcript fragment on argv[1] or stdin; prints one epoch integer.
"""
import datetime as dt
import os
import re
import sys

# "resets" then optionally "<Mon> <day>," then "<hour>[:<min>] [am|pm]"
RESET_RE = re.compile(
    r"resets\s+(?:([A-Za-z]{3,9})\s+(\d{1,2})\s*,?\s*)?(\d{1,2})(?::(\d{2}))?\s*([ap]m)?",
    re.I,
)


def parse_reset(text, now, fallback_secs, max_hold_secs, min_hold_secs=300):
    """Return (epoch, how) where how explains which branch produced it."""
    target, how = None, "fallback"
    m = RESET_RE.search(text or "")
    if m:
        mon, day, hh, mm, ampm = m.groups()
        hh, mm = int(hh), int(mm or 0)
        if ampm:
            ampm = ampm.lower()
            if ampm == "pm" and hh != 12:
                hh += 12
            elif ampm == "am" and hh == 12:
                hh = 0
        if hh < 24 and mm < 60:
            try:
                if mon:
                    month = dt.datetime.strptime(mon[:3].title(), "%b").month
                    target = dt.datetime(now.year, month, int(day), hh, mm,
                                         tzinfo=dt.timezone.utc)
                    # The message never carries a year. A date that lands far in
                    # the past is a December->January rollover, not a stale claim.
                    if target < now - dt.timedelta(days=180):
                        target = target.replace(year=now.year + 1)
                    how = "dated"
                else:
                    # Bare clock time: the next occurrence of it.
                    target = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
                    if target <= now:
                        target += dt.timedelta(days=1)
                    how = "time-only"
            except ValueError:
                target = None

    if target is None:
        target, how = now + dt.timedelta(seconds=fallback_secs), "fallback"
    elif target <= now:
        # The message says the window has already reset, yet the agent was just
        # refused. Believe the refusal but not the wait: retry on the next tick
        # rather than idling for hours on a claim that contradicts itself.
        target, how = now + dt.timedelta(seconds=min_hold_secs), "already-passed"

    epoch = int(target.timestamp())
    lo, hi = int(now.timestamp()) + min_hold_secs, int(now.timestamp()) + max_hold_secs
    return max(lo, min(epoch, hi)), how


def main():
    text = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()
    now_env = os.environ.get("QUOTA_NOW_EPOCH")  # tests pin "now"; production does not
    now = (dt.datetime.fromtimestamp(int(now_env), dt.timezone.utc) if now_env
           else dt.datetime.now(dt.timezone.utc))
    epoch, how = parse_reset(
        text,
        now,
        int(os.environ.get("QUOTA_FALLBACK_SECS", 21600)),
        int(os.environ.get("QUOTA_HOLD_MAX", 691200)),
    )
    sys.stdout.write("%d %s\n" % (epoch, how))


if __name__ == "__main__":
    main()
