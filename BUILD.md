# Building and verifying Amphora MVP20

Everything below runs on a fresh clone with no datasets restored. Commands that need
the omitted datasets skip with a message naming what to restore, rather than failing.

## Prerequisites

| Tool | Version | Notes |
|---|---|---|
| `rustup` | any recent | Required. `rust-toolchain.toml` pins the compiler to **1.96.0**; rustup honours it automatically on first build. Without rustup the pin is inert and you get whatever `rustc` is on `PATH`. |
| `uv` | any recent | Only for the Python programs (Crystal360 / CrystalAtlas / benchkit). `pip install -r <lock>` also works. |
| C++20 toolchain + CMake | — | **Only** for the optional `rdkit` cargo feature. Not needed for a normal build. |

No other wrapper is required. If a command in this repo does not run with plain `cargo`,
that is a bug — please report it rather than working around it.

> **Running these over SSH:** `ssh xbabe1 'cargo test …'` fails with `cargo: command not
> found`. A non-interactive SSH command does not source `~/.profile`, which is what puts
> `~/.cargo/bin` on `PATH`. Use a login shell — `ssh xbabe1 'bash -lc "cargo test …"'` — or
> call `~/.cargo/bin/cargo` directly. Both hosts have rustup with 1.96.0 installed, so the
> `rust-toolchain.toml` pin resolves without a download.

## Build and verify

```bash
cargo check --workspace --all-targets --locked     # compiles everything
cargo test  --workspace --locked                   # 395 pass, 1 ignored, 0 fail
cargo run -p xtask -- audit                        # evidence/registry integrity gate
scripts/verify-hash-bindings.sh --quiet            # no regression above the 458 historical baseline
```

Last verified 2026-08-23 against a fresh `git clone` on xbabe1: `cargo check` passes,
`cargo test` reports **395 passed, 0 failed, 1 ignored**, the controller manifest verifies
(57 files), the controller suite passes, and `xtask audit` fails with exactly the one
message in [Known debt](#known-debt) below.

`cargo test` is the command named as the focused acceptance command by all 29
`docs/mission.md` files. On a fresh clone it is green:

- **1 ignored** — `cf_packet_blueprint_citation_binding_probe`. A stale gap-reproduction
  probe: it asserts a defect is *still present*, and that defect has since been fixed, so it
  fails by construction. Retained deliberately. Run it with
  `cargo test --workspace --locked -- --ignored cf_packet_blueprint_citation_binding_probe`.
- **8 tests self-skip.** Seven need the omitted `feedback/` dataset tree; the eighth,
  `t04_adversarial_forgery_report`, needs the separately-omitted `t04_cases.json` forgery
  corpus (its generator is checked in). Run with `-- --nocapture` to see which, and what to
  restore.

## Running the CLI

```bash
cargo run --release -- demo
cargo run --release -- run \
  --candidate amphora-candidate-contract/fixtures/formulation_candidate.json --headless --jsonl
cargo run --release -- replay --verify
cargo run --release -- inspect \
  --candidate amphora-candidate-contract/fixtures/formulation_candidate.json --headless
```

Run these from the repository root — `default-members = ["amphora-cli"]`, so bare
`cargo run` resolves to the CLI.

> **These need one dataset directory restored.** All of them read
> `feedback/v1/derived/build_manifest.json`, which is omitted from this repository, and on a
> bare clone they exit immediately with `No such file or directory`.
>
> On xbabe1 all 6.20 GB is already restored. Elsewhere, one prefix is enough to get the
> CLI running:
>
> ```bash
> ops/restore-datasets.sh --apply --only feedback/v1/derived/   # ~385 MB, 4 files
> ```
>
> Verified on xbabe1 after that restore: `demo` and `inspect` run, and `replay --verify`
> then reports `replay verified: 158 events root=…`. Note the order — `replay` replays the
> most recent run archive, so it needs a `demo` or `run` to have happened first; on a tree
> with no runs it exits `No such file or directory`. `cargo test --workspace --locked` is
> green without any restore at all.

## Restoring the omitted datasets

`DATASETS.local.json` inventories the 1,344 omitted files (6.20 GB) with path, size,
sha256, and category. `ops/restore-datasets.sh` reads it, pulls from the canonical tree, and
verifies every digest after transfer:

```bash
ops/restore-datasets.sh                      # dry run: what is missing
ops/restore-datasets.sh --apply              # everything (6.20 GB)
ops/restore-datasets.sh --apply --only feedback/   # one prefix
```

It refuses to run unless the canonical host's `git rev-parse HEAD` matches the sha the
manifest was captured from, so it cannot silently pull from the wrong tree.

**On xbabe1 the complete inventory is already restored and hash-verified.** Run the script
with no arguments to re-verify; it cannot fetch anything, because as of 2026-08-24 there is
no canonical host left to fetch from — Amphora was removed from xbabe2 and its tree is
archived at `legacy/xbabe2-amphora/`. `ops/push-datasets-to.sh` remains for pushing to a
*new* host from this one.

## Optional: the pinned RDKit chemistry boundary

Chemistry normalization fails closed without RDKit; it never substitutes a fallback
canonicalizer. The `rdkit` feature is **not** in `default`, so a normal build does not
need it.

Two build recipes exist and they are **not** equivalent:

- **`ops/rdkit/Dockerfile` is canonical.** It emits `RDKIT-LIBRARY-SHA256SUMS` and
  `build-flags.txt`, so a build is reproducible and attestable. Prefer it.
- `tools/build-rdkit-2026.03.2.sh` is the no-Docker fallback. It pins the same upstream
  commit (`42fe8c952589bb750e27ea7f259a50b36576bfa5`, `Release_2026_03_2`) but emits no
  hash manifest, so builds from it are not attestable.

```bash
bash tools/build-rdkit-2026.03.2.sh /absolute/install/prefix
export RDKIT_INCLUDE_DIR=/absolute/install/prefix/include/rdkit
export RDKIT_LIB_DIR=/absolute/install/prefix/lib
export BOOST_INCLUDE_DIR=/absolute/install/prefix/include
cargo test --workspace --locked --features rdkit
```

## Python programs

These belong to the NOMAD Crystal360 / CrystalAtlas program, not to Amphora — see
[README.md](README.md). The two environments pin **incompatible** numpy/pandas versions
and must stay separate.

```bash
uv venv .venv-crystal360     --python 3.12
uv pip install --python .venv-crystal360/bin/python     -r requirements-crystal360.lock

uv venv .venv-crystal-atlas  --python 3.12
uv pip install --python .venv-crystal-atlas/bin/python  -r requirements-crystal-atlas.lock
```

`benchkit/` is a separate, self-contained package: `pytest benchkit/tests` (21 pass, 4 skip
for its intentionally omitted local dataset).

## Updating the protected runtime checkout

`xbabe1:/home/ubuntu/mvp20-split/ops/amphora-controller` is deployed at mode 0555 — the
protection that backstops the controller's integrity model. Git updates a file by unlinking
and recreating it inside its directory, so a read-only directory makes `git pull`,
`git stash pop`, `git restore`, and `git clean` fail **part way through**, leaving a
half-applied checkout rather than a clean refusal.

```bash
ops/amphora-controller/bin/amphora unprotect --apply
git fetch origin
git merge --ff-only origin/main
ops/amphora-controller/bin/amphora protect --apply
python3 ops/amphora-controller/tools/controller_tree_manifest.py verify
```

Never `git reset --hard` or force-update that checkout — see
[RUNBOOK.md](ops/amphora-controller/RUNBOOK.md). **Better: do not develop in it at all.**
Clone to your own path and leave the runtime checkout pinned.

## Publication gate

`ops/amphora-controller/reviewed-snapshot.sh` is dry-run by default. It was written for a
two-host world -- pause/drain on protected xbabe1, then regenerate the dataset inventory, scan
the staged tree, full tree and full history, commit and push from a writable publish clone on
xbabe2. **That second host no longer exists.** Amphora was removed from xbabe2 on 2026-08-24
and the publish clone with it.

So an applied snapshot needs a writable clone that is not yet provisioned. xbabe1's `origin`
resolves through the `github-amphora-mvp20` SSH alias to a read-only deploy key, so `git push`
from the runtime checkout fails by design and no amount of `gh auth login` changes it. Before
anyone can publish again, the owner must either grant that deploy key write access or add the
new engineer as a collaborator so they can push from their own clone (`CONTRIBUTING.md`).
Until then the dry form is the only form, and it remains safe.

## Known debt

`cargo run -p xtask -- audit` currently exits non-zero on one module:

```
amphora-cro-protocol-packager bundle parent is stale or unconfined:
  evidence/phase0/sources/source-lock.v1.json
```

Cause, fully traced: the 2026-08-11 CF-TEST (fire 2/2) and CF-RISK (fire 2/2) repairs
legitimately rewrote three output artifacts. The live registry pins were re-issued on
2026-08-23 (`config/module-evidence-inventory.json`, the module's `docs/capability-profile.json`
and `docs/mission.md`), but the module's `evidence/phase0/sources/source-lock.v1.json` still
records the pre-repair digests while asserting `hash_current: true` for all three:

| artifact | locked | actual |
|---|---|---|
| `reference/mvp20/out/capture_template.json` | `dc0b3bb4…` | `a5c7f81c…` |
| `reference/mvp20/out/cro_protocol.md` | `4e001dc8…` | `84d6e280…` |
| `reference/mvp20/out/falsification_protocol.json` | `b2fa8de6…` | `79040c13…` |

That file is digested into `evidence/phase0/bundle.v1.json`, which is covered by the signed
`evidence/phase0/receipts/evaluation.v1.dsse.json`. Correcting it therefore means re-issuing
a supersession record and **re-signing the evaluation receipt with the evaluator Ed25519
seed** — an evidentiary act, deliberately left to the owner rather than done as cleanup.
The seed lives only at `xbabe1:/home/ubuntu/.local/share/amphora/phase0/keys/evaluator.ed25519.seed`
(mode 0600) -- the sole copy, so whoever holds xbabe1 can perform this repair.

This is the only known failing gate. It is bounded to three entries in one module; every
other module's source lock and every `bundle.v1.json` digest in the repository verifies clean.
