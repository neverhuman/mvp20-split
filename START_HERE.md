# Start here: Amphora MVP20

Amphora is handed off in a clean, reproducible, intentionally paused state.
Do not authenticate Claude, remove the hard stop, or enable any Amphora cron
entry until the user explicitly approves activation.

## System map

| Host | Path | Purpose | Git state |
|---|---|---|---|
| GitHub | `neverhuman/mvp20-split` | Private, source-only handoff plus reviewed operations | `main` + `demo/founder-showcase` |
| GitHub | `neverhuman/mvp20-split-history` | Private disaster-recovery mirror of the canonical 462-commit history | `main` @ `7d85419`, `demo/founder-showcase` |
| xbabe2 | `/home/ubuntu/amphora/build/mvp20-split-github` | **The only clone with push authority.** Publish from here. | `main`, tracks origin |
| xbabe1 | `/home/ubuntu/mvp20-split` | Read-only full checkout and controller code | Exact GitHub `main` |
| xbabe1 | `/home/ubuntu/amphora-cron` | Mutable campaign, queue, locks, counters, logs. Also holds **superseded** copies of the controller executables — see its `README.SUPERSEDED`. | Deliberately not a Git repository |
| xbabe1 | `/home/ubuntu/amphora-archive/cron-legacy-20260823T031711Z` | Lossless legacy controller archive. Holds commit `8d76070`, which `CORRECTIONS.md` cites and which is unreachable from a GitHub clone. | Original 35-commit `.git` retained |
| xbabe1 | `/home/ubuntu/amphora-archive/mvp20-split-pre-final-{4e8b963,b74d7879}` | **SUPERSEDED** abandoned rebuilds. Both mimic the real handoff commit's subject and author date and report "in sync" against a dead origin. Deletable. See that directory's `README.md`. | not authoritative |
| xbabe2 | `/home/ubuntu/amphora/build/mvp20-split` | Canonical operational source/evidence and 831 historical reproducers | Local-only history, final `7d85419158795c63ff2ee4a41d95a8f5789f9003` |

The owned stop is
`AMPHORA-HANDOFF-20260823T025604Z-CODEX-7F3A92` at
`xbabe1:/home/ubuntu/amphora-cron/state/HARD_STOP`. The xbabe1 hourly launcher,
xbabe1 10-minute mirror, and xbabe2 forensic autocommit guard are disabled.
There are no active lanes or Claude processes.

## First day

**Verify the freeze** (two checks, both must be exact):

```bash
ssh xbabe1 cat /home/ubuntu/amphora-cron/state/HARD_STOP
#   must print exactly: AMPHORA-HANDOFF-20260823T025604Z-CODEX-7F3A92
sha256sum ops/amphora-controller/bootstrap/freeze/cron-legacy.MANIFEST.json
#   must print: 9aa79a55e2220ef92739c603e9af5e176166fd3163c57143fc7940aa0b96b70e
```

Then, on xbabe1 from your own clone:

```bash
ops/amphora-controller/bin/amphora status    # the three cron lines, live
ops/amphora-controller/bin/amphora doctor
cargo test --workspace --locked              # 395 pass, 1 ignored
```

**Then get oriented, in this order:**

1. [README.md](README.md) — what the system is and why it is built the way it is.
2. [docs/MODULE-ANATOMY.md](docs/MODULE-ANATOMY.md) — then read one module end to end.
   `amphora-viscosity-score` is a good first one: it is a real crate, it has a mission
   document, a retraction index, and pre-registered benchmarks.
3. That module's `evidence/phase0/kpis/RETRACTION-INDEX.md` — what it withdrew, and why.
4. [CONTRIBUTING.md](CONTRIBUTING.md) — the change→land loop and the three rules about
   frozen evidence. Read this **before** your first edit; two of the three rules exist
   because they were broken.
5. **Make one real change and open a PR.** [docs/BACKLOG.md](docs/BACKLOG.md) has nine
   items actionable in software today; `R-C01-V` through `R-C05-V` are the gentlest.

Note that `neverhuman/mvp20-split` carries `main` plus the unmerged `demo/founder-showcase`
(see [docs/DEMO.md](docs/DEMO.md)), and `neverhuman/mvp20-split-history` is the 462-commit
disaster-recovery mirror. Branch protection is not configured and is unavailable on the
owner's current GitHub plan.

Review `DATASETS.local.json` before restoring omitted data and `OPERATIONS.local.json`
before changing controller state.

## What this repository actually contains

Read [README.md](README.md) before the operational material. Two points a newcomer
consistently misses:

- The repository holds **two independent programs**. Amphora (coatings, Rust) is the
  subject of this handoff; NOMAD Crystal360 / CrystalAtlas (materials ML, Python) shares
  these hosts and nothing else. Its 40 GB input corpus is not here — see
  [EXTERNAL_INPUTS.md](EXTERNAL_INPUTS.md).
- Of the 41 `amphora-*` directories, only 15 contain code. See
  [docs/MODULE-ANATOMY.md](docs/MODULE-ANATOMY.md).

To build or test anything, start at [BUILD.md](BUILD.md).

## What we got wrong

The most valuable material in this repository is the record of what it measured, published,
and then **withdrew**. It is not summarised anywhere else:

- **22 `evidence/phase0/kpis/RETRACTION-INDEX.md` files**, one per module that has retracted
  something.
- **58 `CLAIM_REFUTED` adversarial verdicts** recorded in the modules' `docs/mission.md`
  and `evidence/audit/` trees.

Before relying on any module-level result, read that module's retraction index.
[PROGRAM_STATUS.md](PROGRAM_STATUS.md) is a 2026-07-17 snapshot and does **not** include
refutations filed after that date.

## Backup and single point of failure

The 462-commit canonical history and the `demo/founder-showcase` branch are now mirrored to
`neverhuman/mvp20-split-history`. What is still **unreplicated on xbabe2 alone**:

- 6.20 GB of datasets and artifacts inventoried in `DATASETS.local.json`
- the 146 MB `.amphora/` control plane (2,588 receipts, 226 run archives)
- the 40 GB NOMAD corpus at `/home/ubuntu/nomad`
- **the 32-byte evaluator signing seed** — see [EXTERNAL_INPUTS.md](EXTERNAL_INPUTS.md)

If xbabe2 is lost, all of the above is lost. Establishing a backup for these — and custody
of the signing seed in particular — is the first thing worth doing on takeover.

## One known exposure

`.amphora/control/local-ed25519.key` was briefly reachable on GitHub through the
`demo/founder-showcase` branch's original ancestry, and is retained in the
`mvp20-split-history` mirror by construction. Reachability from this repository has been
removed; the key was deliberately **not** rotated. Treat any signature bearing
`local-9028773f49591193` as provenance intent, not authenticity. This does not affect the
evaluator identity, whose seed has never left xbabe2. Full account in
[HANDOFF.md](HANDOFF.md#signing-key-exposure-2026-08-23).

## What xbabe1 can and cannot reach

xbabe1 was decommissioned for handoff on 2026-08-23. From that host you can reach
**GitHub, read-only, and nothing else**:

- `~/.ssh/` holds only `amphora_mvp20_ro_ed25519` (the read-only deploy key) and a
  `known_hosts` containing github.com alone, pinned against GitHub's published
  fingerprints. `~/.ssh/config` has one stanza.
- The lateral keys that reached xbabe2, xbabe3 and the Mac hosts were removed, and
  revoked on the far side. `ssh xbabe2` from xbabe1 no longer authenticates.
- The previous owner's Anthropic, Codex, HuggingFace and Docker credentials, and the
  shell and prompt history, were removed from the host.

Two consequences worth knowing:

**`ops/restore-datasets.sh` cannot run from xbabe1 any more.** It pulls from
`xbabe2:/home/ubuntu/amphora/build/mvp20-split` over ssh, which is now blocked. The
minimum needed for the CLI — `feedback/v1/derived/`, ~385 MB — is **already restored** in
this checkout, so `demo`, `inspect` and `replay --verify` work as shipped. If you need
more of the 6.20 GB inventory, ask the owner to run the restore or to grant a scoped
path to xbabe2.

**Pushing goes through your own GitHub account.** The deploy key on this host is
read-only by design. See [CONTRIBUTING.md](CONTRIBUTING.md).

The `xbabe2` rows in the system map above describe where things live, not somewhere you
can currently reach.

## Safe commands now## Safe commands now

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
