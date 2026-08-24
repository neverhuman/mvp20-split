# Amphora MVP20 full handoff

This private repository is a source-only handoff plus the reviewed automation
needed to operate it. The fleet is intentionally frozen. Publication does not
authorize authentication, cron enablement, hard-stop removal, or a fire.

## Provenance and final state

- GitHub repository: `neverhuman/mvp20-split`, private. `main` plus the unmerged
  `demo/founder-showcase` (see "Published branches" below).
- Preserved GitHub root commit: `d2209cead0a94c02f4e1f1570aa8dc8be0338bb6`.
- Handoff publication: the reviewed commit series at the tip of `main`. Its exact final SHA
  is obtained with `git rev-parse origin/main` (a commit cannot contain its own SHA). The
  existing `handoff-20260823` tag predates this final hardening pass and is intentionally
  left at its original commit; no tag is moved or added.
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
- Final data/operations manifest revalidation: `2026-08-23T16:45:34+00:00`; the frozen
  campaign-chain checkpoint itself was captured at `2026-08-23T03:17:11+00:00`.
- Owned hard stop:
  `AMPHORA-HANDOFF-20260823T025604Z-CODEX-7F3A92`.
- xbabe1 archive:
  `xbabe1:/home/ubuntu/mvp20-split/legacy/cron-legacy-archive` (was
  `~/amphora-archive/cron-legacy-20260823T031711Z`; consolidated 2026-08-24).
- Archive inventory SHA-256:
  `9aa79a55e2220ef92739c603e9af5e176166fd3163c57143fc7940aa0b96b70e`.

The xbabe1 hourly launcher and 10-minute mirror and the xbabe2 forensic
autocommit entry are disabled. There are zero active lanes, zero held Amphora
fleet locks, and zero Claude processes. Unrelated crontab lines did not change.

The crontab records under `ops/amphora-controller/bootstrap/freeze/` are:

- `xbabe{1,2}.crontab.current` — **the current live state**, Amphora entries only. Compare
  against these.
- `xbabe{1,2}.crontab.before` / `.after` — the full before/after pair captured at the
  2026-08-23T02:56Z freeze. **The `.after` pair is superseded**: `bin/amphora install --apply`
  ran at 04:07 and migrated both the disable marker (`AMPHORA_HANDOFF_DISABLED` →
  `AMPHORA_MANAGED_DISABLED`) and the script paths (`/home/ubuntu/amphora-cron/…` →
  `/home/ubuntu/mvp20-split/ops/amphora-controller/…`, and the xbabe2 guard to
  `/home/ubuntu/.local/libexec/`). They are retained unmodified because their SHA-256s are
  attested in `record.json`; **do not restore a crontab from them.**

[ops/amphora-controller/CRON.md](ops/amphora-controller/CRON.md) is the single human-readable
record of all three entries, verbatim, and of how they are enabled and disabled.

## Repository contents and exclusions

The root commit contains the filtered MVP20 source tree. The reviewed handoff commits add
`START_HERE.md`, this handoff, `OPERATIONS.local.json`, developer documentation, and
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
- GitHub Actions workflows and LFS objects. The existing annotated handoff tag contains
  metadata only and introduces no payload tree.

### Published branches

`main` is the handoff. **`demo/founder-showcase`** (tip
`e8e3acd31550137874ea086919f63180c16682c1`, 11 hand-written commits) was published on
2026-08-23 and is **not** merged. It contains the founder demo TUI —
`amphora-cli/src/showcase.rs`, `screen.rs`, `build.rs`,
`amphora-core/tests/t13_verify_run_hardening.rs`, ~1,485 lines of Rust — plus three
security-hardening commits (`78d9ab48` R1/T-01B caller-echoed candidate hashes, `30c2ae93`
R2/T-13 event-hash chain recomputation, `403e0ccc` R3/T-05 molecule fact attestation).

It is unmerged because R2 and R3 have declared breaking effects: legacy run archives written
under the superseded event-hash format fail loudly against them. Merging is a reviewed
decision, not a cleanup. R1 was independently landed on `main` as `acf268f6`; only R2/R3
and the showcase remain branch-only.
Its worktree was `xbabe2:/home/ubuntu/amphora/demo-2026-08-11`; that host was cleared on
2026-08-24 and the worktree was not copied, being reconstructible from
`legacy/canonical-history.git`.

### Backup and single point of failure

The former `neverhuman/mvp20-split-history` mirror was found to contain dataset payloads,
`.amphora/`, logs, and a local signing key. Every published ref was replaced with filtered
handoff `main`, the unsafe demo ref was deleted, and the private repository was archived.
GitHub may retain unreachable objects until an owner with `delete_repo` scope deletes it;
do not unarchive or share it. See `docs/DATA-BOUNDARY.md`.

Held on xbabe1 and nowhere else: the 473-commit canonical history, the 6.20 GB of
inventoried datasets, the 146 MB `.amphora/` control plane, the 40 GB NOMAD corpus, and the
32-byte evaluator signing seed. Until 2026-08-24 this said "xbabe2"; the single copy moved,
it did not become two. See [EXTERNAL_INPUTS.md](EXTERNAL_INPUTS.md) and
[START_HERE.md](START_HERE.md).

Nothing excluded was deleted from the canonical sources. The entire original
xbabe1 tree—including its Git history, logs, credentials/state, backups,
malformed filenames, and counters—is preserved byte-for-byte in the archive
with a base64-path deterministic inventory. The live xbabe1 `.git` directory
was renamed to `.git.legacy-frozen-20260823T031711Z` after archiving, so
that state is mutable and not a Git repository. It now lives at
`xbabe1:/home/ubuntu/mvp20-split/state` (consolidated 2026-08-24, gitignored).
No source or dataset was deleted, moved, or rewritten on xbabe2.

`DATASETS.local.json` is the deterministic 1,344-entry inventory for omitted
non-cache datasets and artifacts. Every row carries path, size, hash, and
category and was revalidated against final xbabe2. `OPERATIONS.local.json` is
the corresponding operations provenance and exclusion record.

## Controller changes

- Code/state separation and `/home/ubuntu/.config/amphora/mvp20-cron.env` with
  environment overrides.
- Parameters for controller, mutable state, campaign, queue, prompt, directive
  registry, target host/root, model, Claude binary, SSH/SCP commands, and signing
  seed path.
- Operator commands: `doctor`, `status`, `test`, `pause`, `drain`, `resume`, `protect`,
  `unprotect`, and explicit `install --apply`.
- Exact-tag, non-overwriting hard stops; resume removes only the exact owned
  stop after enabling the two reviewed cron entries.
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
  export, manifest regeneration, staged/full-tree/full-history policy and secret checks,
  review, commit, and push.

918 evidence, benchmark, reference, and report files retain the canonical xbabe2 path
and remain byte-faithful. They are provenance records, not portable entry points, and the
path is part of what they attest. The full list is checked in at
[`docs/frozen-provenance-files.txt`](docs/frozen-provenance-files.txt) with the command to
regenerate it, so the figure is verifiable rather than asserted.

## Validation

The publication gate covers:

```text
bash -n and ShellCheck on active operational scripts
Python AST and import checks
151 inherited controller regression checks
34 operator, configuration, hard-stop, installer, migration, DSSE, policy, guard, and sandbox checks
cargo test --workspace --locked --no-run
cargo test --workspace --locked
.venv-crystal360/bin/python -m pytest tests/crystal360
pytest amphora-redteam-audit/tests/test_ledger_ts.py
pytest benchkit/tests
campaign and reconnaissance invariant baselines (zero new deviations)
directive coverage (zero unmapped obligations, zero orphan references)
```

Publication also requires the staged tree, full history, and a fresh clone to
pass redacted Gitleaks and TruffleHog scans; manifest hashes and sizes; forbidden
path, credential, binary, and oversize checks; `git fsck`; privacy; branch/tag
counts; workflow absence; and verification that the canonical-path files listed in
`docs/frozen-provenance-files.txt` match xbabe2 byte-for-byte.

### Verification as of 2026-08-23

Re-run against **this published tree** (not the canonical tree), on a clone with no datasets
restored:

| Command | Result |
|---|---|
| `cargo check --workspace --all-targets --locked` | passes |
| `cargo test --workspace --locked` | **395 passed, 0 failed, 1 ignored** |
| `gitleaks git . --config .gitleaks.toml --exit-code 1` | exit 0, no leaks |
| `python3 ops/amphora-controller/tools/controller_tree_manifest.py verify` | passes, 57 files |
| `ops/amphora-controller/tests/run.sh`, `tools/tests/run-all.sh` | pass |
| `scripts/verify-hash-bindings.sh --quiet` | passes the 459 historical-break ratchet; zero new breaks |
| `cargo run -p xtask -- audit` | **fails — one known item, see Known debt** |

The 1 ignored test is `cf_packet_blueprint_citation_binding_probe`, a stale
gap-reproduction probe whose gap has been closed. Eight further tests self-skip when the
omitted `feedback/` tree is absent, naming what to restore. See [BUILD.md](BUILD.md).

Crystal360 passes 107 tests, the portable red-team ledger 6, and benchkit 21 with four
manifest-backed skips for its intentionally omitted local dataset.

## Signing-key exposure, 2026-08-23

`.amphora/control/local-ed25519.key` — a 32-byte Ed25519 private key — was briefly
reachable on GitHub and should be treated as burned.

**What happened.** `.amphora/` has always been tracked in the canonical xbabe2 repository.
`main` correctly excludes it. But when `demo/founder-showcase` was first published on
2026-08-23 it was pushed with its full canonical ancestry (189 commits), which carried
3,130 `.amphora/` files including that key. The former canonical-history mirror also carried
it by construction.

**What was done.** `demo/founder-showcase` was rebuilt as the 11 demo commits rebased
directly onto the filtered handoff, with no canonical ancestry and zero `.amphora/` files.
The unsafe mirror's live refs were purged and it was archived. Complete GitHub-side erasure
still requires repository deletion by an owner token with `delete_repo` scope.

**What was not done, and why.** The key was **not** rotated. It declares its own authority
as `LOCAL_DEVELOPMENT_AUDIT_ONLY` (`key_id: local-9028773f49591193`, schema
`amphora.local-trust-key.v1`) and carries no promotion authority by construction. It signed
175 tracked artifacts — 56 DSSE receipts and 119 manifests/acquisition receipts — each
through a bespoke `sign_*.py` in its own evidence directory. Re-signing all of them would
change 175 file hashes and cascade into every digest that records them, which is a larger
integrity risk than the exposure it would remedy.

**What a successor should assume.** Treat any signature bearing `local-9028773f49591193` as
establishing *provenance intent*, not authenticity — anyone with the repository history could
have produced it. This does not affect the evaluator identity
(`phase0-evaluator-3ef6b35cdbbfea74`), whose seed now lives only on xbabe1 and which signs
everything that carries actual Phase-0 authority. If you later need authenticated local
signatures, issue a new key rather than reusing this one.

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
- `cargo run -p xtask -- audit` fails on one module. The 2026-08-11 CF-TEST and CF-RISK
  repairs rewrote three `amphora-cro-protocol-packager` output artifacts; the live registry
  pins were re-issued on 2026-08-23, but `evidence/phase0/sources/source-lock.v1.json` still
  records the pre-repair digests while asserting `hash_current: true`. That file is digested
  into a signed `evaluation.v1.dsse.json`, so correcting it requires a supersession record
  and re-signing with the evaluator seed — deliberately left to the owner. Full trace in
  [BUILD.md](BUILD.md#known-debt). Bounded to three entries in one module; every other
  source lock and every `bundle.v1.json` digest verifies clean.
- The fleet was frozen mid-`INFRA` stall at gate-hold level 7, after six consecutive fires
  produced no result. The stop itself is clean — zero lanes, zero locks, zero processes —
  but the loop was already not making progress when it was frozen. Whoever activates should
  diagnose the stall before expecting useful fires.
- `reference/mvp20/data/facts.json` is duplicated verbatim across 14 modules with nothing
  enforcing parity. Correcting a value in one silently forks the canonical fact table.
- Branch protection is not configured on the handoff GitHub repository and is unavailable on the
  owner's current plan. Repository ownership is a single personal account with one admin and
  one non-expiring read-only deploy key; there is no documented succession for the account
  itself.

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
