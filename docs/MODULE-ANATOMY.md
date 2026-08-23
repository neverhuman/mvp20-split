# Module anatomy

There are 41 `amphora-*` directories. They are not uniform, and the difference matters
before you go looking for code.

## Two kinds of module

**15 are Rust crates** — they have a `Cargo.toml` and are members of the root workspace:

`amphora-core`, `amphora-ord-codec`, `amphora-assurance-capabilities`,
`amphora-formulation-capabilities`, `amphora-molecule-capabilities`, `amphora-rdkit-ffi`,
`amphora-engine`, `amphora-cure-potlife-gate`, `amphora-viscosity-score`,
`amphora-solvency-score`, `amphora-barrier-corrosion-score`, `amphora-tui`, `amphora-cli`,
`amphora-phase0-reviewer`, `amphora-solver-lab`.

**Two more carry code that is not a workspace crate:** `amphora-redteam-audit` has a real
Python package (`src/amphora_redteam_audit/ledger_ts.py`, exercised by
`pytest amphora-redteam-audit/tests/test_ledger_ts.py`, which is part of the publication
gate), and `amphora-formulation-arithmetic` carries a standalone `t05_harness/` crate under
`src/`.

**The remaining 24 have no executable code.** They are documentation-and-evidence trees. Their
capability is implemented inside one of the crates above (usually
`amphora-assurance-capabilities`, `amphora-formulation-capabilities`, or
`amphora-molecule-capabilities`) and registered through `module-manifest.json`. A module's
own `docs/capability-profile.json` names the implementing file under `implementation.path`.

`README.md` lists 29 *registered missions*. That is a policy-registry count, not a crate
count, and it is not the same set as the 41 directories.

## The shared directory layout

| Directory | What it is | Who writes it |
|---|---|---|
| `docs/mission.md` | The module's canonical capability contract: what it claims, its authority ceiling, its known contradictions, and the dated adversarial verdicts against it. **This is the document to read first.** | Reviewed edits + `cargo run -p xtask -- reconcile-native-evidence` for the hash pins |
| `docs/capability-profile.json` | The machine-readable form of the same contract, bound from `module-manifest.json`. The runtime reads this, not the prose. | `xtask reconcile-native-evidence` |
| `evidence/phase0/` | **Frozen, append-only audit trail.** Signed DSSE receipts, source locks, bundles, benchmark locks. Do not edit in place — supersede. | the Phase-0 evaluator (requires the signing seed) |
| `evidence/phase0/kpis/RETRACTION-INDEX.md` | **The record of claims this module made and then withdrew.** 22 exist across the tree; the modules' `docs/mission.md` files carry 58 `CLAIM_REFUTED` verdicts between them. Check a module's retraction index before relying on any of its results. | reviewed |
| `evidence/phase0/repairs/<ITEM>/` | Per-campaign-item working directories: `attempts/`, `work/`, `done/`. A `done/` receipt means the item's `done_criterion` was met. | the hourly loop, when it was running |
| `evidence/audit/` | Adversarial red-team probes and their signed verdicts. This is where refutations originate. | reviewed |
| `evidence/superseded/supersession-<sha>/` | Archived prior states of the evidence tree. Never deleted; this is how correction works without rewriting history. | supersession events |
| `benchmarks/<name>-v1/` | Pre-registered, locked evaluations. Contain their own `HANDOFF.md`/`PREREGISTRATION.md` where one exists. | reviewed |
| `reference/mvp20/` | Input fixtures and generated output artifacts (`out/`). Dataset payloads under `data/` are largely omitted — see `DATASETS.local.json`. | generated, then pinned |
| `movement/events/` | Module movement/promotion events. The directory must exist for `xtask audit` even when empty. | the engine |
| `ip/` | Claim contracts, prior art, disclosure logs, technical dossiers. | reviewed |
| `fixtures/`, `tests/`, `examples/`, `src/` | Present only where the module has code. | — |

## Things that will surprise you

- **`src/` without `Cargo.toml` is not always dead.** `amphora-redteam-audit/src/amphora_redteam_audit/`
  has an empty `__init__.py` but a working `ledger_ts.py`, imported by that module's tests and
  run by the publication gate. Check for a sibling `tests/` before assuming a `src/` is vestigial.
- **Absolute paths inside evidence and benchmark files.** 918 tracked files hard-code
  `/home/ubuntu/amphora/build/mvp20-split`, enumerated in
  [`frozen-provenance-files.txt`](frozen-provenance-files.txt). These are frozen provenance
  records, pinned to the canonical tree's path on purpose. They are **not** expected to run from a clone and
  should not be "fixed". The same applies to the 48 `Cargo.toml` files inside
  `evidence/`/`benchmarks/` harness directories — they are records, not buildable crates.
- **`reference/mvp20/data/facts.json` is duplicated verbatim across 14 modules.** They are
  identical today by convention, not by construction. If you correct a value, correct all 14.
- **Missing dataset directories.** `evidence/phase0/raw/objects/` is tracked but empty (a
  `.gitkeep` holds it). The payloads are inventoried in `DATASETS.local.json` and live only
  on the canonical xbabe2 tree.

## Zero-byte files and `work/scratch/` are usually real

322 tracked files are zero bytes. 230 are `.gitkeep` directory placeholders; the other 92 —
mostly `.txt` and `.err` — plus 11 files under a `work/scratch/` path, look like debris.
Mostly they are not:

- An empty `*.err` / `*.err.txt` is a **result**: it records that the command produced no
  stderr. Deleting it destroys that observation.
- `work/scratch/` inside a repair directory holds the raw stdout/stderr captures a
  diagnostic was computed from. At least one of them,
  `amphora-candidate-contract/evidence/phase0/repairs/T-01B/work/scratch/clean_candidate.json`,
  is referenced by a live audit diagnostic.

Check for a reference before assuming anything under `evidence/` is disposable, and run
`scripts/verify-hash-bindings.sh` before and after any bulk change. See
[`../CONTRIBUTING.md`](../CONTRIBUTING.md).

## Reading order for a module you have never seen

1. `docs/mission.md` — what it claims and what has already refuted it.
2. `evidence/phase0/kpis/RETRACTION-INDEX.md` — what it withdrew.
3. `docs/capability-profile.json` — the machine contract, including `implementation.path`.
4. That implementation file, in whichever crate owns it.
