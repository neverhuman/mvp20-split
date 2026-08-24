# External inputs not in this repository

> **Everything below moved to xbabe1 on 2026-08-24**, when Amphora was removed from xbabe2.
> The paths in this file are xbabe1 paths. See
> `legacy/xbabe2-amphora/ARCHIVE-NOTES.md` for what was archived and what was deliberately
> left behind.

`DATASETS.local.json` inventories the 1,344 files (6.20 GB) that were omitted from
**within** the `mvp20-split` tree. This file records dependencies that live entirely
**outside** that tree — things a successor will otherwise discover only when a command
fails.

## NOMAD corpus — 40 GB

| | |
|---|---|
| Path | `xbabe1:/home/ubuntu/mvp20-split/legacy/xbabe2-amphora/out-of-tree/nomad` |
| Size | 40 GB |
| Used by | `build_nomad_crystal360.py`, `build_nomad_crystal_atlas.py`, `run_nomad_crystal_atlas.py`, `nomad_crystal360/*` |
| Referenced from | [CRYSTAL360.md](CRYSTAL360.md) (`--dataset` default), [CRYSTALATLAS.md](CRYSTALATLAS.md) |
| Provenance | The unchanged NOMAD 449-column baseline. `crystal360_schema.json` (in-repo, 412 KB) is the frozen schema over it, carrying every formula, unit, and column definition. |
| Status | **Not backed up.** Not inventoried in `DATASETS.local.json` (which is scoped to the mvp20-split tree only). ~31 MB of it is the re-downloadable Kaggle core; the remaining ~38 GB under `artifacts/` is generated compute with no other copy, and the ~20 top-level driver scripts that produced it exist in no repository. |

Without it, the Crystal360 and CrystalAtlas build commands cannot run. The Amphora
coatings program does not depend on it at all.

## `scq` cluster-queue binary — 7.3 MB

| | |
|---|---|
| Path | `xbabe1:/home/ubuntu/mvp20-split/legacy/xbabe2-amphora/out-of-tree/remote_super/smart_cluster/target/release/scq` |
| Hard-coded at | `nomad_feature_hunt/v2/catboost_feature_ga.py:39` |
| Purpose | Job submission across the three-node fleet |
| Status | Built from a source tree that is not in this repository. That tree **is** archived alongside the binary, and its 20 MB `.git` has **no remote** — the archived copy is the only one. Rebuild with `cargo build --release` inside it. |

## Fleet topology

`nomad_feature_hunt/v2/catboost_feature_ga.py:38` declares
`NODES = ("xbabe1", "xbabe2", "xbabe3")`.

`xbabe3` (`192.168.68.54`) is a real, reachable third node used only by the NOMAD
feature-hunt program. It plays **no part** in the Amphora coatings system: the Amphora
controller targets xbabe1 (controller) and xbabe2 (canonical tree) only, as recorded in
[START_HERE.md](START_HERE.md) and [ops/amphora-controller/CRON.md](ops/amphora-controller/CRON.md).

## Evaluator signing seed

| | |
|---|---|
| Path | `xbabe1:/home/ubuntu/.local/share/amphora/phase0/keys/evaluator.ed25519.seed` (mode 0600, in a 0700 directory) |
| Size | 32 bytes |
| Purpose | Signs every Phase-0 DSSE evaluation receipt. Required to issue or re-issue any evidence receipt. |
| Status | **Single copy, on xbabe1, not backed up.** It was deliberately placed there on 2026-08-24 so this host can issue evidence; it must still **never** be committed to this repository. Verified there: it derives `phase0-evaluator-3ef6b35cdbbfea74`, the identity every shipped receipt was signed under. |

Losing it means no future evidence receipt can be issued under the existing evaluator
identity. Because it is now the only copy anywhere, **backing it up is the single
highest-value thing to do on takeover** — and note that a `git clean -xdf` in this checkout
would not touch it, but a lost or reimaged host would.

The same directory also holds `internal-reviewer.ed25519.seed` and the `toolkit-review` /
`rights-review` reviewer seeds. All four are 32 bytes, mode 0600, and equally unbacked.
