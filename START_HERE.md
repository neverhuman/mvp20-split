# Start here: Amphora MVP20

Amphora is handed off in a clean, reproducible, intentionally paused state.
Do not authenticate Claude, remove the hard stop, or enable any Amphora cron
entry until the user explicitly approves activation.

## System map

| Host | Path | Purpose | Git state |
|---|---|---|---|
| GitHub | `neverhuman/mvp20-split` | Private, source-only handoff plus reviewed operations | `main` + `demo/founder-showcase` |
| xbabe1 | `/home/ubuntu/mvp20-split/legacy/canonical-history.git` | Bare mirror of the canonical repository — the **473-commit** development history, on no remote. Archived here 2026-08-24. | `main` @ `7d85419`, `demo/founder-showcase` @ `209f6b5` |
| xbabe1 | `/home/ubuntu/mvp20-split` | Protected runtime and complete read-only clone of every published ref | Exact GitHub `main`; non-shallow/non-partial |
| xbabe1 | `/home/ubuntu/mvp20-split/state` | Mutable campaign, queue, locks, counters, logs. Was `~/amphora-cron`; consolidated 2026-08-24. | Gitignored, deliberately not tracked |
| xbabe1 | `/home/ubuntu/mvp20-split/legacy/cron-legacy-archive` | Lossless legacy controller archive. Holds commit `8d76070`, which `CORRECTIONS.md` cites and which is unreachable from a GitHub clone. | Original 35-commit `.git` retained |
| xbabe1 | `/home/ubuntu/mvp20-split/legacy/xbabe2-amphora` | Everything else that was on xbabe2: earlier MVP generations, the meta-loop programme, the NOMAD corpus, `scq` and its source. See its `ARCHIVE-NOTES.md`. | mixed; mostly no version control |

The owned stop is
`AMPHORA-HANDOFF-20260823T025604Z-CODEX-7F3A92` at
`xbabe1:/home/ubuntu/mvp20-split/state/state/HARD_STOP`. The xbabe1 hourly launcher,
xbabe1 10-minute mirror, and xbabe2 forensic autocommit guard are disabled.
There are no active lanes or Claude processes.

## First day

**Verify the freeze** (two checks, both must be exact):

```bash
ssh xbabe1 cat /home/ubuntu/mvp20-split/state/state/HARD_STOP
#   must print exactly: AMPHORA-HANDOFF-20260823T025604Z-CODEX-7F3A92
sha256sum ops/amphora-controller/bootstrap/freeze/cron-legacy.MANIFEST.json
#   must print: 9aa79a55e2220ef92739c603e9af5e176166fd3163c57143fc7940aa0b96b70e
```

Then, in the protected xbabe1 runtime checkout:

```bash
cd /home/ubuntu/mvp20-split
ops/amphora-controller/bin/amphora status    # PAUSED, the two disabled jobs, "standalone: no target host"
ops/amphora-controller/bin/amphora doctor    # standalone; reports the seed present
cargo test --workspace --locked              # 395 pass, 1 ignored
```

Both exit 0. They used to report `xbabe2=UNREACHABLE` and exit 1, which was correct when a
second host was expected; since 2026-08-24 there is no second host, and `AMPHORA_TARGET_HOST`
is empty, so a standalone result is the right answer rather than a fault to be fixed. If you
ever see an `UNREACHABLE` line again, something has *re-introduced* a target host.

**Then get oriented, in this order:**

1. [README.md](README.md) — what the system is and why it is built the way it is.
2. [docs/MODULE-STATUS.md](docs/MODULE-STATUS.md) — all 29 capability modules and their
   declared adapter/model, authority, evidence, tests, and refutations.
3. [docs/MODULE-ANATOMY.md](docs/MODULE-ANATOMY.md) — then read one module end to end.
   `amphora-viscosity-score` is a good first one: it is a real crate, it has a mission
   document, a retraction index, and pre-registered benchmarks.
4. That module's `evidence/phase0/kpis/RETRACTION-INDEX.md` — what it withdrew, and why.
5. [CONTRIBUTING.md](CONTRIBUTING.md) — the change→land loop and the three rules about
   frozen evidence. Read this **before** your first edit; two of the three rules exist
   because they were broken.
6. Create a **separate development clone** at a path you choose, then make one real change
   and open a PR. Never develop in `/home/ubuntu/mvp20-split`; it is the protected runtime.
   [docs/BACKLOG.md](docs/BACKLOG.md) has nine actionable software items.

`neverhuman/mvp20-split` carries `main` plus the unmerged `demo/founder-showcase`; see
[docs/DEMO.md](docs/DEMO.md). Branch protection is not configured and is unavailable on the
owner's current GitHub plan. Read [docs/DATA-BOUNDARY.md](docs/DATA-BOUNDARY.md) before
adding data or sharing any retained evidence.

Review `DATASETS.local.json` before restoring omitted data and `OPERATIONS.local.json`
before changing controller state.

## What this repository actually contains

Read [README.md](README.md) before the operational material. Two points a newcomer
consistently misses:

- The repository holds **two independent programs**. Amphora (coatings, Rust) is the
  subject of this handoff; NOMAD Crystal360 / CrystalAtlas (materials ML, Python) shares
  these hosts and nothing else. Its 40 GB input corpus is not here — see
  [EXTERNAL_INPUTS.md](EXTERNAL_INPUTS.md).
- Of the 41 `amphora-*` directories, 15 are workspace crates and two more carry code;
  the other 24 are evidence/documentation trees. See [docs/MODULE-ANATOMY.md](docs/MODULE-ANATOMY.md).

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

**xbabe1 is now the only place this project exists.** Amphora was removed from xbabe2 on
2026-08-24 after everything was copied here and verified. There is no second host.

The GitHub repository holds the filtered handoff — source, evidence, and the reviewed
operations tree. It does **not** hold, and cannot hold:

- the **473-commit** canonical development history (`legacy/canonical-history.git`) — this is
  on no remote at all; the repository it came from had a remote named `history-mirror` that
  in fact contained a completely disjoint lineage, which made it look backed up when it was
  not
- 6.20 GB of datasets and artifacts inventoried in `DATASETS.local.json`
- the 40 GB NOMAD corpus and ~38 GB of generated results with no other copy
- the `scq` source tree and its 20 MB `.git`, which has no remote
- **the 32-byte evaluator signing seed** and the three other signing seeds beside it — see
  [EXTERNAL_INPUTS.md](EXTERNAL_INPUTS.md)

**Establishing an off-host backup is now the single most valuable thing to do on takeover.**
Until that exists, one lost disk ends the project. `git clean -xdf` in this checkout would
also destroy the datasets, `state/`, and `legacy/` — see the warning in `.gitignore`.

## What this repository actually contains

Read [README.md](README.md) before the operational material. Two points a newcomer
consistently misses:

- The repository holds **two independent programs**. Amphora (coatings, Rust) is the
  subject of this handoff; NOMAD Crystal360 / CrystalAtlas (materials ML, Python) shares
  these hosts and nothing else. Its 40 GB input corpus is not here — see
  [EXTERNAL_INPUTS.md](EXTERNAL_INPUTS.md).
- Of the 41 `amphora-*` directories, 15 are workspace crates and two more carry code;
  the other 24 are evidence/documentation trees. See [docs/MODULE-ANATOMY.md](docs/MODULE-ANATOMY.md).

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

The unsafe canonical-history GitHub mirror was purged from every ref and archived after it
was found to contain dataset payloads and a local signing key. The following therefore exist
**on xbabe1 and nowhere else**:

- the 473-commit canonical operational history (`legacy/canonical-history.git`)
- 6.20 GB of datasets and artifacts inventoried in `DATASETS.local.json`
- the 146 MB `.amphora/` control plane (2,588 receipts, 226 run archives)
- the 40 GB NOMAD corpus and the ~20 driver scripts that generated its results
- **the 32-byte evaluator signing seed** — see [EXTERNAL_INPUTS.md](EXTERNAL_INPUTS.md)

Until 2026-08-24 that list read "xbabe2". The move to a single host did not reduce the
exposure, it relocated it: there is still exactly one copy, and now there is no second machine
to fall back to. **If xbabe1 is lost, the programme is lost.** Establishing an off-host backup
— and custody of the signing seed in particular — is the first thing worth doing on takeover,
ahead of any code change.

Note also that `git clean -xdf` in this tree would destroy the history mirror, the datasets,
the controller state and the xbabe2 archive, none of which can be re-fetched from anywhere.

## One known exposure

`.amphora/control/local-ed25519.key` was briefly reachable on GitHub through the
`demo/founder-showcase` branch's original ancestry and the unsafe history mirror. All live
refs now point only to the filtered handoff; the history repository is private and archived,
but GitHub may retain unreachable objects until an owner deletes it. The key was deliberately
**not** rotated. Treat any signature bearing
`local-9028773f49591193` as provenance intent, not authenticity. This does not affect the
evaluator identity. Full account in
[HANDOFF.md](HANDOFF.md#signing-key-exposure-2026-08-23).

## xbabe1 is self-contained

As of 2026-08-24, everything lives in **one directory**, `/home/ubuntu/mvp20-split`, and the
host needs nothing from any other machine except GitHub.

```
/home/ubuntu/mvp20-split          HEAD == origin/main, git status clean   ← the synced part
├── feedback/  artifacts/         3.9 G + 603 M restored dataset inventory (gitignored)
├── .amphora/                     this host's own run archives (gitignored)
├── state/                        controller state: HARD_STOP, campaign, queue (gitignored)
├── legacy/                       provenance archives (gitignored)
└── target/                       build output (gitignored)
```

**The complete 1,344-file `DATASETS.local.json` inventory is restored and hash-verified.**
Confirm it any time — the check is local and contacts nothing:

```bash
ops/restore-datasets.sh     # "every selected path is present and hash-verified"
```

Three things necessarily live outside that directory, because they are host configuration
rather than project content: `~/.config/amphora/mvp20-cron.env`,
`~/.local/share/amphora/` (the pinned RDKit build and the signing seeds), and `~/.ssh/`.

**xbabe2 no longer holds anything.** As of 2026-08-24 Amphora was removed from it entirely.
Everything that was there is under `legacy/` — the 473-commit canonical history as a bare
mirror at `legacy/canonical-history.git`, and the rest at `legacy/xbabe2-amphora/` with an
`ARCHIVE-NOTES.md` explaining what was and was not copied. **This host is now the only place
the project exists.**

### What it can reach

**GitHub, read-only, and nothing else.** `~/.ssh/` holds one key — the read-only deploy key —
and a `known_hosts` containing github.com alone, pinned against GitHub's published
fingerprints. The keys that reached xbabe2, xbabe3 and the Mac hosts were removed and
revoked on the far side, and the previous owner's Anthropic, Codex, HuggingFace and Docker
credentials were removed from the host.

Consequence: `ops/restore-datasets.sh` can only *verify* what is already here; there is
nowhere left to fetch from. `ops/push-datasets-to.sh` was written to push this data from the
canonical host, and that host is gone — the script is kept because it is the right tool for
seeding a *future* second machine, which is exactly what the backup above requires.

### Signing on this host

`~/.local/share/amphora/phase0/keys/evaluator.ed25519.seed` is present (mode 0600 in a 0700
directory) and derives `phase0-evaluator-3ef6b35cdbbfea74` — the identity every shipped
receipt was signed under. Verified by signing and verifying a payload here.

This is deliberate: it makes the `R-C01-V`…`R-C05-V` verification items in
[docs/BACKLOG.md](docs/BACKLOG.md) actionable, and makes the outstanding
`source-lock.v1.json` repair possible rather than permanently blocked. Whoever holds this
host can sign as the evaluator. Treat the seed accordingly, and never commit it.

### One hazard worth knowing

**Do not run `git clean -xdf` here.** It removes ignored files, which on this host means the
6.2 GB dataset inventory, the controller state including `HARD_STOP`, and `legacy/`. The
data cannot be re-fetched locally — recovery needs the owner to re-push it.

## Safe commands now## Safe commands now

```bash
cd /home/ubuntu/mvp20-split
ops/amphora-controller/bin/amphora status || true  # target UNREACHABLE is expected while decommissioned
ops/amphora-controller/bin/amphora test
ops/amphora-controller/reviewed-snapshot.sh
python3 ops/amphora-controller/tools/controller_tree_manifest.py verify
```

The snapshot command above is a dry run. `install` is also a dry run unless
given `--apply`. `pause` and `resume` require both an exact tag and `--apply`;
resume enables all three reviewed cron entries and removes only the matching
stop, so it is an activation action.

The runtime has ignored `target/`, `.amphora/`, `state/`, `legacy/`, and the complete
hash-verified 6.2 GB dataset inventory.
They are not in Git; `git status` alone does not show them.

## Access requirements

- SSH as `ubuntu` to xbabe1. Separately provisioned xbabe1→xbabe2 SSH is an activation
  prerequisite and is intentionally absent now.
- Read access to the private GitHub repository. xbabe1 uses its dedicated,
  read-only deploy key; it has no push authority.
- A GitHub identity with reviewed push authority only for publication.
- The 32-byte evaluator seed. As of 2026-08-24 it is on **xbabe1 only**
  (`~/.local/share/amphora/phase0/keys/`, mode 0600), so this host can issue signed evidence
  and is the sole custodian of that ability. It must still never be committed to Git.
  See "Signing on this host" below.
- Interactive Claude authentication as `ubuntu` on xbabe1, but only during an
  explicitly approved activation window.

The later activation sequence is in the runbook. Nothing in this repository
constitutes approval to execute it.
