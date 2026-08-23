# Amphora MVP20

Amphora is a pre-Phase-0 research and diagnostics system for protective-coating formulation.
It generates and ingests candidate formulations, rejects malformed input, runs deterministic
diagnostics across 29 registered capability modules, packages experiments for external labs,
and preserves hash-bound, replayable evidence for every decision it makes.

It makes no claim to scientific superiority, product readiness, or qualification — and the
interesting part is how hard it works to keep it that way.

## What is unusual about this system

**It attacks its own claims and files the receipts.** 242 adversarial audit probes, 58
`CLAIM_REFUTED` verdicts recorded in the modules' own mission documents, 22 retraction
indexes, 38 supersession records. A red-team report in `reports/` opens with *"Verdict: we do
NOT have full Phase 0."* The record of what this program measured and then **withdrew** is
kept as carefully as the record of what worked — start at
[`START_HERE.md`](START_HERE.md#what-we-got-wrong).

**Green tests cannot promote anything.** From [`PROGRAM_STATUS.md`](PROGRAM_STATUS.md):
*"Software parity, successful compilation, green unit tests, or a generated report cannot
promote scientific authority."* A module becomes ranking-eligible only when its manifest
policy is changed through review **and** its named external gate passes. That rule is
enforced in code, not just asserted.

**Decisions are replayable byte-for-byte.** 568 signed DSSE receipts and 142 pre-registered
benchmarks. `cargo run --release -- replay --verify` re-derives a run's event-hash chain and
prints its root. Canonical JSON hashing is exact enough that `serde_json`'s `float_roundtrip`
feature is a correctness requirement, not an optimisation — see the comment in `Cargo.toml`.

**The automation that produced it is real infrastructure.** A four-lane autonomous controller
with a fixed total lock order (`slot → fleet → campaign → state`), module leases, structural
fire caps, and a drain-and-quarantine autocommit guard. It ran hourly for weeks. It is now
deliberately paused — see below.

For a running demonstration, see [`docs/DEMO.md`](docs/DEMO.md).

## Operational state

**The fleet is intentionally paused.** All three cron entries are disabled behind a named
hard stop and no Claude process is running. Do not authenticate Claude, remove the hard stop,
or enable a cron entry without the owner's explicit approval.
[`ops/amphora-controller/CRON.md`](ops/amphora-controller/CRON.md) has the three entries
verbatim and how they are toggled.

## Getting started

| | |
|---|---|
| Taking over the system | [START_HERE.md](START_HERE.md) |
| Build, test, run | [BUILD.md](BUILD.md) |
| Make a change and land it | [CONTRIBUTING.md](CONTRIBUTING.md) |
| What to work on | [docs/BACKLOG.md](docs/BACKLOG.md) |

Deeper: [HANDOFF.md](HANDOFF.md) (what was handed over and what was left behind),
[docs/MODULE-ANATOMY.md](docs/MODULE-ANATOMY.md) (what a module directory contains),
[AMPHORA_RUST.md](AMPHORA_RUST.md) (the Rust workspace),
[ops/amphora-controller/RUNBOOK.md](ops/amphora-controller/RUNBOOK.md) (operating the
automation), [PROGRAM_STATUS.md](PROGRAM_STATUS.md) (what may and may not be claimed).

```bash
cargo test --workspace --locked     # 395 pass, 1 ignored — green on a bare clone
```

## Layout

**Amphora (coatings)** — 41 `amphora-*` directories, of which 15 are Rust crates in the
workspace and the rest are documentation-and-evidence trees; plus `ops/amphora-controller/`,
`config/`, `registry/`, `schemas/`, `reports/`. The [module manifest](module-manifest.json)
is the runtime policy registry and binds every mission and capability profile.
Runtime chemistry support is JSON plus molecule SMILES; the broader adapters are targets and
fail closed.

**NOMAD Crystal360 / CrystalAtlas (materials ML)** — a separate Python program sharing these
hosts and nothing else. It owns the root `pyproject.toml`, the `atlas_*.py` / `build_*.py` /
`run_*.py` scripts, `nomad_crystal360/`, `nomad_feature_hunt/`, `crystal360_schema.json`, and
`tests/`. Entry points: [CRYSTAL360.md](CRYSTAL360.md), [CRYSTALATLAS.md](CRYSTALATLAS.md).
Its 40 GB input corpus is not in this repository — see
[EXTERNAL_INPUTS.md](EXTERNAL_INPUTS.md).

`benchkit/` is a third, small, self-contained numerical package.

Two module directories sit outside `module-manifest.json` by design and are not
engine-loadable: `amphora-dataset-recon/` and `amphora-solver-lab/`.

See the [readiness crosswalk](docs/readiness-crosswalk.md) and
[dependency-aware roadmap](docs/roadmap.md) for per-module status and priority.
