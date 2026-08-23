# Amphora cron entries

**All three Amphora cron entries are DISABLED and must stay disabled until the user
explicitly approves activation.** This document is the single human-readable record of
what they are, where they live, what they do, and how they are turned on and off.

## The three entries, verbatim

`ops/amphora-controller/bin/amphora` → `cron_entries()` is the only code that generates
these lines, and `install` / `pause` / `resume` are the only commands that write them.
Nothing else should ever edit an Amphora crontab line by hand.

### xbabe1 — hourly launcher

| | |
|---|---|
| Schedule | `0 * * * *` (top of every hour) |
| Implemented by | `ops/amphora-controller/claude-hourly-loop.sh` |
| Purpose | Runs one four-lane autonomous Claude fire against the campaign queue. Self-limits to `LANE_COUNT` slot locks and exits, so a duplicate cron entry cannot double-fire. |
| Log | `/home/ubuntu/amphora-cron/logs/` |

```
# enabled form
0 * * * * /home/ubuntu/mvp20-split/ops/amphora-controller/claude-hourly-loop.sh

# current (disabled) form
# AMPHORA_MANAGED_DISABLED AMPHORA-HANDOFF-20260823T025604Z-CODEX-7F3A92 0 * * * * /home/ubuntu/mvp20-split/ops/amphora-controller/claude-hourly-loop.sh
```

### xbabe1 — 10-minute log mirror

| | |
|---|---|
| Schedule | `*/10 * * * *` |
| Implemented by | `ops/amphora-controller/mirror-log.sh` |
| Purpose | Mirrors the append-only per-lane logs, fire summaries, and heartbeats to the target host. |
| Log | discarded (`>/dev/null 2>&1`) |

```
# enabled form
*/10 * * * * /home/ubuntu/mvp20-split/ops/amphora-controller/mirror-log.sh >/dev/null 2>&1

# current (disabled) form
# AMPHORA_MANAGED_DISABLED AMPHORA-HANDOFF-20260823T025604Z-CODEX-7F3A92 */10 * * * * /home/ubuntu/mvp20-split/ops/amphora-controller/mirror-log.sh >/dev/null 2>&1
```

### xbabe2 — guarded forensic autocommit

| | |
|---|---|
| Schedule | `30 * * * *` (half past every hour, i.e. between launcher fires) |
| Implemented by | `ops/amphora-controller/autocommit-guard.sh`, **deployed to** `/home/ubuntu/.local/libexec/amphora-autocommit-guard.sh` |
| Purpose | Takes an exclusive `AUTOCOMMIT_DRAIN` marker, waits for every lane and fleet lock to drain, quarantines rejected schema-flip bytes, stages only policy-approved paths, commits locally, and **never pushes**. |
| Log | `/home/ubuntu/amphora/build/mvp20-split/logs/autocommit-guard.log` |

```
# enabled form
30 * * * * flock -n /tmp/amphora-git-autocommit.lock /home/ubuntu/.local/libexec/amphora-autocommit-guard.sh >/dev/null 2>&1

# current (disabled) form
# AMPHORA_MANAGED_DISABLED AMPHORA-HANDOFF-20260823T025604Z-CODEX-7F3A92 30 * * * * flock -n /tmp/amphora-git-autocommit.lock /home/ubuntu/.local/libexec/amphora-autocommit-guard.sh >/dev/null 2>&1
```

> The guard script is deployed **outside** the repo, to `/home/ubuntu/.local/libexec/`, by
> `bin/amphora install --apply`. `bin/amphora doctor` checks the deployed guard and policy
> hashes against the current repository when xbabe2 access is provisioned.
> Do not edit a deployed copy — edit the repository and re-run `install --apply` during an
> approved activation/maintenance window.
>
> A 15-line predecessor of this guard used to live at `/home/ubuntu/amphora-autocommit-guard.sh`
> — the path named by the historical `xbabe2.crontab.after` freeze record. It did a bare
> `git add -A` on the canonical tree with no drain, no policy, and no quarantine. It was
> renamed to `….legacy-superseded-20260823` and made non-executable on 2026-08-23. This is
> the reason the `.after` freeze records must not be used to restore a crontab.

## How disabling works

`pause` prepends this prefix to each managed line, leaving the line commented out but
completely recoverable:

```
# AMPHORA_MANAGED_DISABLED <TAG> <original line>
```

`resume --tag <TAG> --apply` strips exactly that prefix and removes only the matching hard
stop. `is_target_cron()` deliberately recognises **both** marker generations
(`AMPHORA_MANAGED_DISABLED` and the older `AMPHORA_HANDOFF_DISABLED`) and **both** script
path generations (`/home/ubuntu/amphora-cron/…` and
`/home/ubuntu/mvp20-split/ops/amphora-controller/…`), so a tree frozen under either
convention is still managed correctly.

`install --apply` rewrites all three managed lines and **appends them at the end of the
crontab**; unrelated entries are preserved byte-identically but line ordering changes.

## Why they are off

The fleet was deliberately frozen for handoff. The owned hard stop is:

```
AMPHORA-HANDOFF-20260823T025604Z-CODEX-7F3A92
```

at `xbabe1:/home/ubuntu/amphora-cron/state/HARD_STOP` (mode 0600). While that file exists
with that exact content, the launcher refuses to fire even if a cron entry were enabled.
`resume` refuses to act on a hard stop whose content does not match the tag you pass, so a
foreign stop can never be silently removed.

## Where to run these commands

**Run host-mutating `bin/amphora` commands from xbabe1, from
`/home/ubuntu/mvp20-split`.**

This matters more than it looks. `install`, `pause`, and `resume` reach the target host over
`$AMPHORA_SSH_COMMAND $AMPHORA_TARGET_HOST` (`xbabe2`) to write the remote crontab and deploy
the guard. The handoff state intentionally has no xbabe1→xbabe2 host trust or credential;
restoring a dedicated path is an activation prerequisite. On other machines the alias may
mean something else, so the host guard refuses applied mutations anywhere but xbabe1.

```bash
cd /home/ubuntu/mvp20-split
ops/amphora-controller/bin/amphora status    # prints local state, then target UNREACHABLE now
ops/amphora-controller/bin/amphora doctor    # expected to fail SSH until activation access exists
```

## Checked-in crontab records

| File | What it is |
|---|---|
| `bootstrap/freeze/xbabe1.crontab.current`, `xbabe2.crontab.current` | **Current state.** Amphora-only extract of the live crontabs. Compare against these. |
| `bootstrap/freeze/xbabe1.crontab.before`, `xbabe2.crontab.before` | Historical: full crontabs immediately **before** the 2026-08-23T02:56Z freeze. |
| `bootstrap/freeze/xbabe1.crontab.after`, `xbabe2.crontab.after` | Historical: full crontabs immediately **after** that freeze. **Superseded** — `install --apply` ran at 04:07 and migrated the marker and script paths. Their SHA-256s are attested in `record.json`; they are kept unmodified as forensic evidence and must not be used to restore a crontab. |

To verify the live state matches the repo:

```bash
# on xbabe1
diff <(crontab -l | grep -E 'AMPHORA_(MANAGED|HANDOFF)_DISABLED') \
     <(grep -E 'AMPHORA_(MANAGED|HANDOFF)_DISABLED' \
         ops/amphora-controller/bootstrap/freeze/xbabe1.crontab.current)

# after activation access is provisioned, from xbabe1
ssh xbabe2 'crontab -l | grep -E "AMPHORA_(MANAGED|HANDOFF)_DISABLED"' | diff - \
     <(grep -E 'AMPHORA_(MANAGED|HANDOFF)_DISABLED' \
         ops/amphora-controller/bootstrap/freeze/xbabe2.crontab.current)
```

Both must print nothing. Before activation access, compare the xbabe1 lines locally and use
the frozen xbabe2 record plus an independent xbabe2 login; `status` fails closed rather than
claiming an unverified remote line.

## Activation

Enabling any of these is a separate, explicitly approved operation. The full sequence is in
[RUNBOOK.md](RUNBOOK.md) under "Eventual activation". Nothing in this repository constitutes
approval to execute it.
