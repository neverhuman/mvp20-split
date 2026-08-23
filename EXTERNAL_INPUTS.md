# External inputs not in this repository

`DATASETS.local.json` inventories the 1,372 files (6.20 GB) that were omitted from
**within** the `mvp20-split` tree. This file records dependencies that live entirely
**outside** that tree — things a successor will otherwise discover only when a command
fails.

## NOMAD corpus — 40 GB

| | |
|---|---|
| Path | `xbabe2:/home/ubuntu/nomad` |
| Size | 40 GB |
| Used by | `build_nomad_crystal360.py`, `build_nomad_crystal_atlas.py`, `run_nomad_crystal_atlas.py`, `nomad_crystal360/*` |
| Referenced from | [CRYSTAL360.md](CRYSTAL360.md) (`--dataset` default), [CRYSTALATLAS.md](CRYSTALATLAS.md) |
| Provenance | The unchanged NOMAD 449-column baseline. `crystal360_schema.json` (in-repo, 412 KB) is the frozen schema over it, carrying every formula, unit, and column definition. |
| Status | **Not backed up.** Not inventoried in `DATASETS.local.json` (which is scoped to the mvp20-split tree only). |

Without it, the Crystal360 and CrystalAtlas build commands cannot run. The Amphora
coatings program does not depend on it at all.

## `scq` cluster-queue binary — 7.3 MB

| | |
|---|---|
| Path | `xbabe2:/home/ubuntu/remote_super/smart_cluster/target/release/scq` |
| Hard-coded at | `nomad_feature_hunt/v2/catboost_feature_ga.py:39` |
| Purpose | Job submission across the three-node fleet |
| Status | Built from a source tree that is **not** in this repository and not inventoried anywhere. |

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
| Path | `xbabe2:/home/ubuntu/.local/share/amphora/phase0/keys/evaluator.ed25519.seed` |
| Size | 32 bytes |
| Purpose | Signs every Phase-0 DSSE evaluation receipt. Required to issue or re-issue any evidence receipt. |
| Status | **Single copy. Not backed up. Must never be copied into this repository or onto xbabe1.** |

Losing it means no future evidence receipt can be issued under the existing evaluator
identity, and the outstanding `source-lock.v1.json` re-issue described in
[BUILD.md](BUILD.md#known-debt) becomes impossible to complete. Custody of this file is the
single highest-value thing to resolve on takeover.
