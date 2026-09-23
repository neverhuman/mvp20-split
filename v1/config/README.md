# config/

Program-level configuration and the global evidence registry. Read by the Rust workspace at
runtime and by `cargo run -p xtask -- audit`.

| Path | What it is | Written by |
|---|---|---|
| `module-evidence-inventory.json` | The global evidence registry: per-module implementation, tests, artifacts, rights, and their SHA-256 pins. Each module's `docs/capability-profile.json` must agree with its row here — `xtask audit` enforces it. | `xtask reconcile-native-evidence` |
| `module-priorities.json` | Per-module priority scores and their factor breakdown. Mirrors the scored ladder in `docs/roadmap.md`. | reviewed |
| `benchmark-lock.v1.json`, `benchmark-locks/*.json` | Locked benchmark definitions, global and per module. | reviewed |
| `program/*.json` | Per-program source censuses and splits (corrosion, cure, viscosity, solvency, molecule). These reference dataset payloads under `feedback/`, which is **omitted** from this repository — see `DATASETS.local.json`. | reviewed |

`module-evidence-inventory.json` also carries a `seal_reissues` block recording any pin
re-issued after an artifact was legitimately rewritten by a repair, with the previous and
new digests and the receipts authorising it.
