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
`xbabe1:/home/ubuntu/mvp20-split/state/state/HARD_STOP`. Both managed cron entries — the
hourly launcher and the 10-minute mirror — are disabled. (A third, a forensic autocommit
guard, ran on xbabe2; that host holds nothing now, so `resume` writes two lines, not three.)
There are no active lanes or Claude processes.

## Log in as `amphora`, not `ubuntu`

The project is owned by a dedicated **`amphora`** account, created 2026-08-24. Log in as that
user. It owns `/home/ubuntu/mvp20-split` outright, has its own Rust toolchain at the pinned
1.96.0, its own `~/.config/amphora/mvp20-cron.env`, and its own copies of the four signing
seeds at mode 0600.

It deliberately has **no sudo**, and cannot read the `ubuntu` account's SSH keys, Claude or
Codex state, or the several unrelated projects that share this machine. That boundary is the
point: xbabe1 is not a dedicated Amphora box. It also runs a Docker Swarm manager, five
long-lived containers, PostgreSQL, `scqd`, and a second login user `deploy`. **None of that
is yours and none of it is Amphora.** Leave it alone.

The path still reads `/home/ubuntu/...` because moving the tree would invalidate hundreds of
recorded paths for no benefit. Ownership, not location, is what changed.

## First day

You are on xbabe1, logged in over SSH. Everything below runs there, in one directory.

**Verify the freeze** (two checks, both must be exact):

```bash
cd /home/ubuntu/mvp20-split
cat state/state/HARD_STOP
#   must print exactly: AMPHORA-HANDOFF-20260823T025604Z-CODEX-7F3A92
sha256sum ops/amphora-controller/bootstrap/freeze/cron-legacy.MANIFEST.json
#   must print: 9aa79a55e2220ef92739c603e9af5e176166fd3163c57143fc7940aa0b96b70e
```

Then, in the same directory:

```bash
ops/amphora-controller/bin/amphora status    # PAUSED, the two disabled jobs, "standalone: no target host"
ops/amphora-controller/bin/amphora doctor    # standalone; reports the seed present
cargo test --workspace --locked              # 395 pass, 1 ignored
```

Both `status` and `doctor` exit 0. They used to report `xbabe2=UNREACHABLE` and exit 1, which
was correct when a second host was expected; since 2026-08-24 there is no second host, and
`AMPHORA_TARGET_HOST` is empty in `~/.config/amphora/mvp20-cron.env`, so standalone is the
right answer rather than a fault to fix.

If you ever see an `UNREACHABLE` line again, a target host has been re-introduced — and the
most likely cause is that config file being lost or bypassed, because `bin/amphora`'s built-in
`DEFAULTS` still fall back to `AMPHORA_TARGET_HOST = "xbabe2"` and a state root of
`/home/ubuntu/amphora-cron`. Both are pre-consolidation values that no longer exist. The env
file is what keeps them from taking effect.

**If you drive this over `ssh xbabe1 '…'` rather than an interactive shell**, `cargo` will not
be found: non-interactive SSH does not source `~/.profile`, which is what puts `~/.cargo/bin`
on `PATH`. Use `ssh xbabe1 'bash -lc "cargo test …"'`.

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

### Before you publish anything, anywhere

Read the root [LICENSE](LICENSE). This material is proprietary and confidential, and access to
the repository is **not** permission to redistribute what is in it. The constraint is not
uniform and it is not theoretical: [docs/DATA-BOUNDARY.md](docs/DATA-BOUNDARY.md) records 103
retained paths whose rights status is `UNRESOLVED`, 16 of 31 sources that are not
`DERIVATIVE_ALLOWED`, and 33 CC-BY-4.0 sources whose attribution notices **have not been
assembled yet**. Every rights decision currently carries a `null` decision receipt.

In practice: do not put evidence artifacts, benchmark inputs, or reference tables into a
paper, an issue, a public repository, or a model prompt without checking that file's rights
status first.

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

**xbabe1 is the only place this project exists.** Amphora was removed from xbabe2 on
2026-08-24, after everything was copied here and verified. There is no second host.

The GitHub repository holds the filtered handoff — source, evidence, and the reviewed
operations tree. It does **not** hold, and cannot hold:

- the canonical development history at `legacy/canonical-history.git` — **473 commits across
  both tips** (`main` @ `7d85419` is 462 of them; `demo/founder-showcase` @ `209f6b5` adds 11).
  This is on no remote at all. The repository it came from had a remote named `history-mirror`
  that in fact held a completely disjoint lineage, which made it look backed up when it was not.
- 6.20 GB of datasets and artifacts inventoried in `DATASETS.local.json`
- the 146 MB `.amphora/` control plane — 2,588 receipt files and 226 files across 33 run
  directories. **It is not the `.amphora/` in this tree.** The live one is 2.6 MB of current
  control state; the full plane is archived at
  `legacy/xbabe2-amphora/build/mvp20-split/.amphora/`. Seeing 2.6 MB and concluding it was
  lost is the expected mistake — it was not.
- the 40 GB NOMAD corpus, the ~38 GB of results generated from it, and the ~20 driver scripts
  that produced them, which are in no repository
- the `scq` source tree and its 20 MB `.git`, which has no remote
- **the 32-byte evaluator signing seed** and the three other seeds beside it — see
  [EXTERNAL_INPUTS.md](EXTERNAL_INPUTS.md)

Until 2026-08-24 that list read "xbabe2". Moving to a single host did not reduce the exposure,
it relocated it: there is still exactly one copy, and now there is no second machine to fall
back to. **If xbabe1 is lost, the programme is lost.**

So back it up before you change anything:

```bash
ops/backup-to-disk.sh --list                 # what would be copied, and to where
ops/backup-to-disk.sh /mnt/amphora-backup --apply
```

That writes to a second disk **in this same machine**, which protects against disk failure and
against an accidental deletion. It does not protect against losing the machine. Getting a copy
onto separate hardware is still the most valuable thing you can do on takeover.

Note also that `git clean -xdf` in this tree would destroy the history mirror, the datasets,
the controller state and the xbabe2 archive, none of which can be re-fetched from anywhere.

## The pause was not a clean stop

`HARD_STOP` is a deliberate freeze, and it is the thing that keeps the fleet off. But it was
applied on top of a fleet that had **already stalled**, and nothing in `status` or `doctor`
tells you so. In `state/state/` you will find:

```
STALLED                     {"kind":"INFRA","reason":"6 consecutive fires that never
                             produced a result (quota, network, or timeout)",
                             "held_since":"2026-08-20T02:00:01Z",
                             "release":"2026-08-22T12:00:02+00:00"}
gate-hold-level             7
consecutive-infra-fail.txt  6
```

Read that plainly: on 2026-08-20 six fires in a row produced nothing — quota, network, or
timeout — the controller put itself into an INFRA hold, and the backoff had climbed to level
7. The hold's own release time has since passed, so the stall is not what is stopping the
fleet now; `HARD_STOP` is. But **do not read the freeze as evidence the last run was healthy.**
It was not.

Before activating, decide deliberately whether to clear that state or let it expire, and find
out what the six dead fires were. `logs/fire-summary.jsonl` is where they are recorded.

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
├── .amphora/               2.6 M this host's own run archives (gitignored)
├── state/                        controller state: state/HARD_STOP, campaign, queue (gitignored)
├── legacy/                  57 G provenance archives — the canonical history mirror, the
│                                 archived xbabe2 tree, NOMAD, scq (gitignored)
└── target/                 6.3 G build output (gitignored)
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

## Safe commands now

```bash
cd /home/ubuntu/mvp20-split
ops/amphora-controller/bin/amphora status   # exits 0
ops/amphora-controller/bin/amphora test
ops/amphora-controller/reviewed-snapshot.sh
python3 ops/amphora-controller/tools/controller_tree_manifest.py verify
```

The snapshot command above is a dry run. `install` is also a dry run unless
given `--apply`. `pause` and `resume` require both an exact tag and `--apply`;
resume enables **two** reviewed cron entries — the hourly launcher and the 10-minute mirror —
and removes only the matching stop, so it is an activation action. (There used to be a third,
a forensic autocommit guard deployed to xbabe2. With no target host, `set_crons()` writes two.)

### The controller tree is read-only, deliberately

`ops/amphora-controller` is mode 0555 and its files 0444, so the first edit you attempt
anywhere inside it fails with `Permission denied`, and `git pull` touching it can fail
**part way through** rather than refusing cleanly. That is a deployment protection, not damage.
Lift it and put it back:

```bash
ops/amphora-controller/bin/amphora unprotect --apply   # before editing or pulling
# ... make the change ...
ops/amphora-controller/bin/amphora protect --apply     # after
```

`controller_tree_manifest.py verify` works read-only; `generate` needs the tree unprotected
first.

The runtime has ignored `target/`, `.amphora/`, `state/`, `legacy/`, and the complete
hash-verified 6.2 GB dataset inventory.
They are not in Git; `git status` alone does not show them.

## Access requirements

- SSH to xbabe1. That is the whole access surface; there is no second host to provision
  trust with, and the activation sequence no longer asks for any.
- Read access to the private GitHub repository — **with your own account**. xbabe1 holds no
  GitHub credential at all: the read-only deploy key was removed at handover, deliberately, so
  this host cannot reach GitHub and no shared key is being passed to you. `git fetch` and
  `git pull` here will fail, and that is the intended state. Clone separately with your own
  identity, work there, push from there. Ask the owner to add you as a collaborator; until
  that happens nothing can be published from anywhere.
- `git config user.name` / `user.email` are unset on this host. Set them in your own clone
  before your first commit.
- The 32-byte evaluator seed. As of 2026-08-24 it is on **xbabe1 only**
  (`~/.local/share/amphora/phase0/keys/`, mode 0600), so this host can issue signed evidence
  and is the sole custodian of that ability. It must still never be committed to Git.
  See "Signing on this host" above.
- Interactive Claude authentication, but only during an explicitly approved activation
  window. Note that `doctor` currently reports one FAIL — `Claude binary not executable` —
  because the `amphora` account has no Claude installed. That is correct and expected: the
  logged-in Claude belongs to the `ubuntu` account and is not shared across the boundary.
  Installing and authenticating Claude for whichever account runs the fleet is an activation
  step, not a handoff defect.

The later activation sequence is in the runbook. Nothing in this repository
constitutes approval to execute it.
