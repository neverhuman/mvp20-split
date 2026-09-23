# Amphora cron entries

**Both Amphora cron entries are DISABLED and must stay disabled until the user explicitly
approves activation.** This document is the single human-readable record of what they are,
where they live, what they do, and how they are turned on and off.

There were three. The third ran on xbabe2, which no longer holds any part of this project —
Amphora was removed from it on 2026-08-24. With `AMPHORA_TARGET_HOST` empty, `set_crons()`
writes two lines and prints `standalone: no remote guard`. The third is documented below
because the guard script is still in the repository and still deployed by `install --apply`,
and because you need to know that a two-line `resume` is complete, not partial.

## The entries, verbatim

`ops/amphora-controller/bin/amphora` → `cron_entries()` is the only code that generates
these lines, and `install` / `pause` / `resume` are the only commands that write them.
Nothing else should ever edit an Amphora crontab line by hand.

### xbabe1 — hourly launcher

| | |
|---|---|
| Schedule | `0 * * * *` (top of every hour) |
| Implemented by | `ops/amphora-controller/claude-hourly-loop.sh` |
| Purpose | Runs one four-lane autonomous Claude fire against the campaign queue. Self-limits to `LANE_COUNT` slot locks and exits, so a duplicate cron entry cannot double-fire. |
| Log | `$AMPHORA_STATE_ROOT/logs/` — on xbabe1, `/home/ubuntu/mvp20-split/state/logs/` |

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

### xbabe2 — guarded forensic autocommit  *(historical; no target host today)*

| | |
|---|---|
| Schedule | `30 * * * *` (half past every hour, i.e. between launcher fires) |
| Implemented by | `ops/amphora-controller/autocommit-guard.sh`, **deployed to** `/home/ubuntu/.local/libexec/amphora-autocommit-guard.sh` |
| Purpose | Takes an exclusive `AUTOCOMMIT_DRAIN` marker, waits for every lane and fleet lock to drain, quarantines rejected schema-flip bytes, stages only policy-approved paths, commits locally, and **never pushes**. |
| Log | was `/home/ubuntu/amphora/build/mvp20-split/logs/autocommit-guard.log` on xbabe2 — that path no longer exists |

```
# enabled form
30 * * * * flock -n /tmp/amphora-git-autocommit.lock /home/ubuntu/.local/libexec/amphora-autocommit-guard.sh >/dev/null 2>&1

# current (disabled) form
# AMPHORA_MANAGED_DISABLED AMPHORA-HANDOFF-20260823T025604Z-CODEX-7F3A92 30 * * * * flock -n /tmp/amphora-git-autocommit.lock /home/ubuntu/.local/libexec/amphora-autocommit-guard.sh >/dev/null 2>&1
```

> The guard script is deployed **outside** the repo, to `/home/ubuntu/.local/libexec/`, by
> `bin/amphora install --apply`. `bin/amphora doctor` checks the deployed guard and policy
> hashes against the current repository when a target host is configured. With none, that
> check is skipped rather than failed.
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

at `$AMPHORA_STATE_ROOT/state/HARD_STOP` (mode 0600) — on xbabe1,
`/home/ubuntu/mvp20-split/state/state/HARD_STOP`. While that file exists
with that exact content, the launcher refuses to fire even if a cron entry were enabled.
`resume` refuses to act on a hard stop whose content does not match the tag you pass, so a
foreign stop can never be silently removed.

## Where to run these commands

**Run host-mutating `bin/amphora` commands from xbabe1, from
`/home/ubuntu/mvp20-split`.**

This matters more than it looks. `install`, `pause` and `resume` *used to* reach a target host
over `$AMPHORA_SSH_COMMAND $AMPHORA_TARGET_HOST` to write a remote crontab and deploy the
guard. `AMPHORA_TARGET_HOST` is now empty, so they operate purely locally. On other machines
the `xbabe1` alias may mean something else, so the host guard still refuses applied mutations
anywhere but this host.

```bash
cd /home/ubuntu/mvp20-split
ops/amphora-controller/bin/amphora status    # local state, then "standalone: ..."; exits 0
ops/amphora-controller/bin/amphora doctor    # standalone; reports the local seed; exits 0
```

Both exit 0. If either prints an `UNREACHABLE` line, a target host has been re-introduced —
most likely because `~/.config/amphora/mvp20-cron.env` was lost or bypassed, since
`bin/amphora`'s built-in `DEFAULTS` still fall back to `AMPHORA_TARGET_HOST = "xbabe2"` and a
state root of `/home/ubuntu/amphora-cron`. Both are pre-consolidation values; the env file is
what keeps them from taking effect.

## Checked-in crontab records

| File | What it is |
|---|---|
| `bootstrap/freeze/xbabe1.crontab.current` | **Current state.** Amphora-only extract of the live crontab. Compare against this. |
| `bootstrap/freeze/xbabe2.crontab.current` | Historical. That host holds no Amphora cron any more; the record is kept as evidence, not as a comparison target. |
| `bootstrap/freeze/xbabe1.crontab.before`, `xbabe2.crontab.before` | Historical: full crontabs immediately **before** the 2026-08-23T02:56Z freeze. |
| `bootstrap/freeze/xbabe1.crontab.after`, `xbabe2.crontab.after` | Historical: full crontabs immediately **after** that freeze. **Superseded** — `install --apply` ran at 04:07 and migrated the marker and script paths. Their SHA-256s are attested in `record.json`; they are kept unmodified as forensic evidence and must not be used to restore a crontab. |

To verify the live state matches the repo:

```bash
# on xbabe1
diff <(crontab -l | grep -E 'AMPHORA_(MANAGED|HANDOFF)_DISABLED') \
     <(grep -E 'AMPHORA_(MANAGED|HANDOFF)_DISABLED' \
         ops/amphora-controller/bootstrap/freeze/xbabe1.crontab.current)
```

It must print nothing. There is no second crontab to check: the Amphora line was removed from
xbabe2 on 2026-08-24 along with everything else.

## Activation

Enabling any of these is a separate, explicitly approved operation. The full sequence is in
[RUNBOOK.md](RUNBOOK.md) under "Eventual activation". Nothing in this repository constitutes
approval to execute it.
