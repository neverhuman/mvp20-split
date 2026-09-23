# Corrections to the permanent record

Claims that turned out to be false when written. A wrong statement in git history
gets a correction in git history, not a silent fix in a later commit.

---

## 2026-08-05 — commit `8d76070` overstated the HUMAN/LAB guard

**What the commit message said:**

> "Filed as 'blocked' with an owner class. The picker skips non-pending items, so
> there is no queue pollution and no risk of a fire executing one; **a validator
> now asserts that no HUMAN- or LAB-owned item is ever pending**, which would be
> the failure mode worth catching."

**What was actually true.** No such validator was committed. The assertion existed
only inside `phase4_delta.py`, a one-shot generator script that ran once from a
scratch directory and was never part of the repository. Nothing in
`claude-hourly-loop.sh`, `lib/`, or `tools/` checked owner classes at all.

The protection that genuinely existed was weaker and different in kind: all 21
HUMAN- and LAB-owned items happened to carry `status: "blocked"`, and the picker
skips non-pending items. That is a **data state**, not an enforced invariant. A
manual edit, a bad delta script, or a future reopening could have flipped one to
`pending`, and the loop would then have dispatched a fire against an obligation
the founder must own — with nothing but prose in the item's own objective text to
stop it.

**How it was found.** An adversarial review of the day's commits, requested after
the work was reported as complete. The reviewer grepped every `.py` and `.sh` file
in the repo and found no owner assertion anywhere, then read the picker and
confirmed it branches on `status` alone.

**What was done about it** (same day, commits following this file):

1. `tools/campaign_invariants.py` — the validator the commit message claimed,
   built for real, with a positive control proving it fails on a HUMAN item
   flipped to `pending` rather than only passing on a healthy campaign.
2. A runtime `OWNER_GUARD_SKIP` in the picker, so the loop is *structurally*
   incapable of selecting a HUMAN- or LAB-owned item regardless of its status.

**Why this file exists.** The loop's entire value rests on claims being checkable.
A commit message asserting a guard that does not exist is the same defect class as
a receipt asserting an attack that could not have failed — the thing this campaign
was created to hunt. Correcting it quietly would have been the wrong response,
because the next reader of that commit would still have believed it.
