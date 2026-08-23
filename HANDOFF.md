# Amphora MVP20 full handoff

This private repository is a source-only handoff plus the reviewed automation
needed to operate it. The fleet is intentionally frozen. Publication does not
authorize authentication, cron enablement, hard-stop removal, or a fire.

## Provenance and final state

- GitHub repository: `neverhuman/mvp20-split`, private, `main` only.
- Preserved GitHub root commit: `d2209cead0a94c02f4e1f1570aa8dc8be0338bb6`.
- Operations publication: the single child of that root commit on `main` (a
  commit cannot contain its own content-derived SHA; `git rev-parse main`
  resolves the exact published value).
- Canonical xbabe2 path: `/home/ubuntu/amphora/build/mvp20-split`.
- Final clean xbabe2 autocommit:
  `7d85419158795c63ff2ee4a41d95a8f5789f9003` (462 local commits). Its final
  excluded log append preserves sandbox alerts discovered during protected-host
  validation; no source or dataset byte changed.
- Source snapshot underlying the preserved root commit:
  `f5b2238720999cc765a751928942ad67d8e419d8` (443 commits). The only changes
  through the final xbabe2 SHA are excluded runtime logs/audit rotation.
- xbabe1 legacy controller Git SHA:
  `5e153948b9983d74c93ac88c56ec76fc0056c1c5` (35 commits, not imported).
- Final operations validation capture: `2026-08-23T04:02:42+00:00`; the frozen
  campaign-chain checkpoint itself was captured at `2026-08-23T03:17:11+00:00`.
- Owned hard stop:
  `AMPHORA-HANDOFF-20260823T025604Z-CODEX-7F3A92`.
- xbabe1 archive:
  `/home/ubuntu/amphora-archive/cron-legacy-20260823T031711Z`.
- Archive inventory SHA-256:
  `9aa79a55e2220ef92739c603e9af5e176166fd3163c57143fc7940aa0b96b70e`.

The xbabe1 hourly launcher and 10-minute mirror and the xbabe2 forensic
autocommit entry are disabled. There are zero active lanes, zero held Amphora
fleet locks, and zero Claude processes. Unrelated crontab lines did not change.
The exact before/after crontabs and hashes are under
`ops/amphora-controller/bootstrap/freeze/`.

## Repository contents and exclusions

The root commit contains the filtered MVP20 source tree. The one operations
commit adds `START_HERE.md`, this handoff, `OPERATIONS.local.json`, and
`ops/amphora-controller/`: active four-lane launcher and prompt, mirror,
libraries, directive registry/build/reconciliation tools, inherited and new
tests, operator CLI, configuration examples, staged-file policy, exclusive-
drain autocommit guard, reviewed snapshot workflow, runbook, controller hash
manifest, and frozen resumable state.

The GitHub repository excludes:

- the xbabe1 cron repository's `.git` and all 35 legacy commits;
- runtime logs, locks, lane history, and counters;
- credentials, Claude state, GitHub keys, and evaluator signing seeds;
- stale controller/prompt/campaign backups;
- unused `module-queue.json`;
- two malformed newline-bearing filenames;
- caches, local environments, build output, compiled binaries, model/archive
  formats, generated report binaries, and disallowed oversized data;
- raw or derived dataset payloads listed in `DATASETS.local.json`;
- GitHub Actions workflows, LFS objects, tags, and extra branches.

Nothing excluded was deleted from the canonical sources. The entire original
xbabe1 tree—including its Git history, logs, credentials/state, backups,
malformed filenames, and counters—is preserved byte-for-byte in the archive
with a base64-path deterministic inventory. The live xbabe1 `.git` directory
was renamed to `.git.legacy-frozen-20260823T031711Z` after archiving, so
`/home/ubuntu/amphora-cron` is mutable state and no longer a Git repository.
No source or dataset was deleted, moved, or rewritten on xbabe2.

`DATASETS.local.json` is the deterministic 1,372-entry inventory for omitted
non-cache datasets and artifacts. Every row carries path, size, hash, and
category and was revalidated against final xbabe2. `OPERATIONS.local.json` is
the corresponding operations provenance and exclusion record.

## Controller changes

- Code/state separation and `/home/ubuntu/.config/amphora/mvp20-cron.env` with
  environment overrides.
- Parameters for controller, mutable state, campaign, queue, prompt, directive
  registry, target host/root, model, Claude binary, SSH command, and signing
  seed path.
- Operator commands: `doctor`, `status`, `test`, `pause`, `drain`, `resume`,
  and explicit `install --apply`.
- Exact-tag, non-overwriting hard stops; resume removes only the exact owned
  stop after enabling the three reviewed cron entries.
- Hash inventory and read-only deployment protection over the whole controller
  tree.
- Dynamic Bash descriptor awareness in the unbound-variable checker.
- Correct DSSE payload decoding in reconnaissance receipt validation.
- Intentional `EXHAUSTED_ROTATION` recognition for zero pending items plus the
  complete, unique 30-module fallback rotation.
- Exact baselines, without evidence rewrites, for 21 historical append-only
  reconnaissance deviations, the CF-TEST 4/2 historical budget overrun, and
  blocked legacy C2/C9 without structured done checks.
- An xbabe2 guard that holds an exclusive drain marker, waits for all lanes,
  quarantines rejected schema-flip bytes, refuses deletions/renames and unsafe
  files, stages only approved paths, commits locally, and never pushes.
- A reviewed snapshot flow that defaults to dry-run and separates pause,
  export, manifest regeneration, policy/secret checks, review, commit, and push.

Exactly 831 historical evidence, benchmark, and report reproduction source
files retaining the canonical xbabe2 path remain byte-faithful. They are
provenance records, not maintained portable entry points.

## Validation

The publication gate covers:

```text
bash -n and ShellCheck on active operational scripts
Python AST and import checks
151 inherited controller regression checks
18 new configuration/hard-stop/installer/migration/DSSE/policy/guard/sandbox checks
cargo test --workspace --locked --no-run
cargo test --workspace --locked -- --skip cf_packet_blueprint_citation_binding_probe
pytest tests/crystal360
pytest amphora-redteam-audit/tests/test_ledger_ts.py
pytest benchkit/tests
campaign and reconnaissance invariant baselines (zero new deviations)
directive coverage (zero unmapped obligations, zero orphan references)
```

Publication also requires the staged tree, full history, and a fresh clone to
pass redacted Gitleaks and TruffleHog scans; manifest hashes and sizes; forbidden
path, credential, binary, and oversize checks; `git fsck`; privacy; branch/tag
counts; workflow absence; and verification that the 831 canonical-path files
match xbabe2 byte-for-byte.

The final Rust compile gate passed in the publication tree. The execution gate
passed against the clean canonical xbabe2 tree, which retains the intentionally
omitted 7 MB T-04 forgery fixture: 395 tests passed and only the stale
`cf_packet_blueprint_citation_binding_probe` gap-reproduction probe was
filtered. Crystal360 passed 107 tests, the portable red-team ledger passed 6,
and benchkit passed 21 with four manifest-backed skips for its intentionally
omitted local dataset.

## Known debt

- 21 append-only reconnaissance rows predate the current framing/quarantine
  invariants. They are retained and exact-baselined, not rewritten.
- CF-TEST historically consumed four fires against `max_fires=2`.
- Blocked C2 and C9 predate structured `done_check`; reopening either requires
  adding a reviewed structured check first.
- The campaign is exhausted. Undirected fallback rotation is intentional, but
  future work should be filed as reviewed campaign items where possible.
- Claude authentication is deliberately absent/stale and remains an activation
  prerequisite, not a handoff defect.

## Activation boundary

Activation is a separate, explicitly approved operation. The sequence is:

1. Reauthenticate Claude as `ubuntu` on xbabe1.
2. Run `doctor`, sandbox and repository tests, SSH checks, and a no-write
   preflight.
3. Confirm the exact hard-stop tag.
4. Run the CLI's exact-tag resume to enable the hourly launcher, 10-minute
   mirror, and idle guarded autocommit, then remove only that stop.
5. Observe the first complete fire and perform a reviewed snapshot if xbabe2
   changes.

Until explicit approval is received, retain the owned hard stop, leave all
three jobs disabled, and do not reauthenticate or resume anything.
