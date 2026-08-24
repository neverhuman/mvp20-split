# Contributing

## The loop

```bash
# 1. change code
cargo test --workspace --locked          # 395 pass, 1 ignored, 0 fail

# 2. regenerate the hash pins your change invalidated
cargo run -p xtask -- reconcile-native-evidence

# 3. integrity gate
cargo run -p xtask -- audit

# 4. nothing you touched broke a recorded digest
scripts/verify-hash-bindings.sh

# 5. only if you touched ops/amphora-controller/
python3 ops/amphora-controller/tools/controller_tree_manifest.py generate
bash ops/amphora-controller/tests/run.sh
```

Step 4 is a ratchet, not a zero target. Thousands of SHA-256 values are embedded across the
evidence, benchmark, and report trees; many sit in dated snapshots that are *supposed* to
diverge. The script fails only when the count goes **up**, which is what an accidental edit
to a pinned file looks like. If it fires, you edited something frozen — revert, do not
update the baseline.

Step 2 matters more than it looks. Module `docs/mission.md` and `docs/capability-profile.json`
carry SHA-256 pins of the source files they describe, and `config/module-evidence-inventory.json`
carries them again globally. `xtask audit` compares all three. Edit `src/lib.rs` without
re-running `reconcile-native-evidence` and the gate fails — correctly.

## Three rules that are not negotiable

**1. Never hand-edit a hash pin.** Run `reconcile-native-evidence`. Editing a digest to match
a file is how you get an inventory that agrees with itself and with nothing else. Three seals
in `amphora-cro-protocol-packager` went stale for twelve days exactly this way, and the repair
is still outstanding — see [BUILD.md](BUILD.md#known-debt).

**2. Never edit or delete anything under `evidence/`, `benchmarks/`, or `reports/`.**
These are frozen records. They are not documentation, and several are bound by a digest
recorded somewhere else in the tree:

- A `*.pre-repair` / `*.before` / `*.installed` file inside `evidence/phase0/repairs/<ITEM>/work/`
  is the **before** state that a repair receipt attests to. Deleting one breaks a signed DSSE
  receipt.
- `benchmarks/*/analyze_*.py` scripts are pinned by `frozen_*_script_sha256` fields in the
  result files beside them. Changing a **comment** in one is enough to break the binding.
- `PREREGISTRATION.md` files are pre-registrations. Editing one after the fact defeats the
  point of having pre-registered.

Correction happens by **supersession**, never in place: archive the prior state under
`evidence/superseded/supersession-<sha>/`, file a new record, re-sign. That needs the
evaluator seed, which lives only on xbabe1 at
`~/.local/share/amphora/phase0/keys/evaluator.ed25519.seed` (mode 0600). That is the only
copy in existence.

Corollary: a stale-looking command inside a frozen record — including the `rtk` wrapper that
appears in a few of them — is **history, not a defect**. It records what was actually run.
Leave it.

**3. Zero-byte files in `evidence/` are usually real.** An empty `*.err` means *the command
produced no stderr*, which is a result. Check for a reference before assuming debris.

## First, create a development clone

Do not develop or authenticate a push account in the protected runtime at
`xbabe1:/home/ubuntu/mvp20-split`. Create a separate clone at a path you own. For an HTTPS
workflow backed by your GitHub identity:

```bash
gh auth login
gh auth setup-git
git clone https://github.com/neverhuman/mvp20-split.git /path/to/your/mvp20-split
cd /path/to/your/mvp20-split
git config --global user.name  "Your Real Name"
git config --global user.email "you@example.com"
```

The runtime checkout's `origin` uses the `github-amphora-mvp20` SSH alias for both fetch and
push, permanently selecting a **read-only** deploy key. `gh auth login` does not change that
SSH identity, so `git push origin` from the runtime correctly fails. Use your separate HTTPS
clone (or a separately configured personal SSH remote) after the owner adds your account as a
collaborator.

## Branches and review

- Branch from `main`; short descriptive names (`fix/t01b-caller-hash`, `feat/cf-bom`).
- Open a PR. There is more than one person on this repository now, and branch protection is
  unavailable on the current GitHub plan, so the PR *is* the review record.
- Commit messages: what changed and why. No trailing metadata.

## What needs the omitted datasets

`cargo test --workspace --locked` is green on a bare clone: 8 tests self-skip and say what
they need. Everything else — `demo`, `run`, `inspect`, `replay --verify` — requires the
dataset tree. Restore the minimum with:

```bash
ops/restore-datasets.sh --apply --only feedback/v1/derived/    # ~385 MB
```

On xbabe1 the **complete** inventory is already restored and hash-verified, so nothing
skips. That host can also sign: the evaluator seed is present, which makes the `R-C0x-V`
verification items actionable. See [BUILD.md](BUILD.md) and [START_HERE.md](START_HERE.md).

**Never run `git clean -xdf`** — it removes ignored files, which here means the 6.2 GB
dataset inventory, the controller `state/` including `HARD_STOP`, and all of `legacy/`
(the 473-commit canonical history mirror and the xbabe2 archive). Since 2026-08-24 this host
is the only place any of that exists, so there is nowhere to re-fetch it from.

## Where to start

[`docs/BACKLOG.md`](docs/BACKLOG.md) — 48 open campaign items grouped by who can move them.
Nine are actionable in software today.

## Operational boundary

The autonomous controller is **paused behind a named hard stop** and must stay that way.
Do not enable a cron entry, remove the hard stop, or authenticate Claude without explicit
approval from the owner. See [`ops/amphora-controller/CRON.md`](ops/amphora-controller/CRON.md)
and [`ops/amphora-controller/RUNBOOK.md`](ops/amphora-controller/RUNBOOK.md). Nothing in this
repository constitutes that approval.
