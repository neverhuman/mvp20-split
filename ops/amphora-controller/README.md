# Amphora four-lane controller

This directory contains the active v5 four-lane launcher, prompt, log mirror,
verification libraries, directive registry and tooling, invariant checks,
151 inherited regression checks, guarded xbabe2 autocommit, operator CLI,
staged-file policy, reviewed snapshot flow, and a frozen resumable bootstrap.

Code and state are intentionally separated:

- Controller: `/home/ubuntu/mvp20-split/ops/amphora-controller` (read-only).
- Mutable state: `$AMPHORA_STATE_ROOT` (not Git). On xbabe1 that is
  `/home/ubuntu/mvp20-split/state`; the path is set in `~/.config/amphora/mvp20-cron.env`,
  which overrides the hardcoded default in `bin/amphora`.
- Configuration: `/home/ubuntu/.config/amphora/mvp20-cron.env` (mode `0600`).
- Target: `xbabe2:/home/ubuntu/amphora/build/mvp20-split`.

Environment variables override literal values in the configuration file. The
controller, state, campaign, queue, prompt, directive registry, target host and
root, model, Claude binary, signing seed, and SSH/SCP commands are parameterized.

The handoff deliberately removes xbabe1's lateral credentials. Local status and tests work;
target checks, applied install/pause/resume, and fires remain unavailable until the separate
activation procedure provisions dedicated xbabe2 access.

`bootstrap/` contains the frozen campaign, acquisition queue, chain checkpoint,
freeze evidence, and archive inventory. It excludes the cron repository's Git
history, logs, credentials, backups, unused module queue, malformed filenames,
lane history, locks, and counters. Those bytes remain in the lossless xbabe1
archive described by `OPERATIONS.local.json`.

See [RUNBOOK.md](RUNBOOK.md) before any operational action.
