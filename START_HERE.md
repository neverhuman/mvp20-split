# Start here: Amphora MVP20

Amphora is handed off in a clean, reproducible, intentionally paused state.
Do not authenticate Claude, remove the hard stop, or enable any Amphora cron
entry until the user explicitly approves activation.

## System map

| Host | Path | Purpose | Git state |
|---|---|---|---|
| GitHub | `neverhuman/mvp20-split` | Private, source-only handoff plus reviewed operations | `main` only |
| xbabe1 | `/home/ubuntu/mvp20-split` | Read-only full checkout and controller code | Exact GitHub `main` |
| xbabe1 | `/home/ubuntu/amphora-cron` | Mutable campaign, queue, locks, counters, logs | Deliberately not a Git repository |
| xbabe1 | `/home/ubuntu/amphora-archive/cron-legacy-20260823T031711Z` | Lossless legacy controller archive | Original 35-commit `.git` retained |
| xbabe2 | `/home/ubuntu/amphora/build/mvp20-split` | Canonical operational source/evidence and 831 historical reproducers | Local-only history, final `7d85419158795c63ff2ee4a41d95a8f5789f9003` |

The owned stop is
`AMPHORA-HANDOFF-20260823T025604Z-CODEX-7F3A92` at
`xbabe1:/home/ubuntu/amphora-cron/state/HARD_STOP`. The xbabe1 hourly launcher,
xbabe1 10-minute mirror, and xbabe2 forensic autocommit guard are disabled.
There are no active lanes or Claude processes.

## First-day checklist

1. Read [the operator runbook](ops/amphora-controller/RUNBOOK.md) and
   [the complete handoff](HANDOFF.md).
2. Confirm the GitHub repository is private and has only `main`, no tags, and
   no `.github/workflows` files.
3. On xbabe1, run `ops/amphora-controller/bin/amphora status`, `doctor`, and
   `test` from `/home/ubuntu/mvp20-split`.
4. Verify the hard-stop content exactly; do not merely test that a file exists.
5. Verify the archive inventory SHA-256 is
   `9aa79a55e2220ef92739c603e9af5e176166fd3163c57143fc7940aa0b96b70e`.
6. Review `DATASETS.local.json` before restoring omitted data and
   `OPERATIONS.local.json` before changing controller state.

## Safe commands now

```bash
cd /home/ubuntu/mvp20-split
ops/amphora-controller/bin/amphora status
ops/amphora-controller/bin/amphora doctor
ops/amphora-controller/bin/amphora test
ops/amphora-controller/reviewed-snapshot.sh
python3 ops/amphora-controller/tools/controller_tree_manifest.py verify
```

The snapshot command above is a dry run. `install` is also a dry run unless
given `--apply`. `pause` and `resume` require both an exact tag and `--apply`;
resume enables all three reviewed cron entries and removes only the matching
stop, so it is an activation action.

## Access requirements

- SSH as `ubuntu` to xbabe1 and xbabe2.
- Read access to the private GitHub repository. xbabe1 uses its dedicated,
  read-only deploy key; it has no push authority.
- A GitHub identity with reviewed push authority only for publication.
- The existing 32-byte evaluator seed on xbabe2. Never copy it into GitHub or
  xbabe1 controller state.
- Interactive Claude authentication as `ubuntu` on xbabe1, but only during an
  explicitly approved activation window.

The later activation sequence is in the runbook. Nothing in this repository
constitutes approval to execute it.
