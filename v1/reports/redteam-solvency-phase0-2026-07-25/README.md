# Red-team + real progress — amphora-solvency-score → PHASE_0 (2026-07-25)

Host: canonical (xbabe2), `/home/ubuntu/amphora/build/mvp20-split`. All actions below
were performed on the canonical host with the in-tree Rust CLI
(`target/release/amphora-tui`) and the independent reviewer
(`target/release/amphora-phase0-reviewer`).

## 1. Red-team of the "full Phase-0 / 16 PHASE_0" claim — it is FALSE (and was not even live-reproducible)

The stored decision report (`config/program/phase0-decision-report.v2.json`) claimed
**16 PHASE_0 / 13 PRE_PHASE_0**. That number is stale and was **not reproducible by the
current verifier**.

Root cause discovered this run: the registry **succession chain**
(`registry/succession-chain.v1.json`) contained **2 records**, but BOTH the CLI
(`amphora-cli/src/phase0.rs:1691`) and the independent reviewer
(`amphora-phase0-reviewer/src/main.rs:903`) require **exactly 3 records**
(`chain.records.len() != 3`). Consequently, before this run **every one of the 29
modules failed live `phase0 verify`** with:

    STALE_OR_UNCONFINED_PARENT: registry succession chain genesis, head, or
    immutable first record is invalid

i.e. **live-verifiable PHASE_0 count = 0**, not 16. The "16" only ever existed in a
report file produced by an earlier binary/state; it does not survive a fresh
verification with the code that is actually in the tree.

This is not sabotage — it is a **staged, not-yet-executed governance step**. The code
names the intended 3rd succession explicitly and specifically:
`THIRD_SUCCESSION_CONTROLS = ["amphora-solvency-score"]`
(`amphora-cli/src/phase0.rs:52`, mirrored in the reviewer), and pins its exact shape
(`amphora-cli/src/phase0.rs:1780-1793`): **exactly two edits, both on
amphora-solvency-score, fields `readiness` and `operational_readiness`, both
`SHADOW → READY`.** The data (the 3rd succession record + advanced manifest) had never
been minted, so verification was globally broken.

## 2. What genuine evidence solvency actually has (the reason it is promotable)

- **Rights are already clean and cryptographically bound.** `source-lock.v2` carries
  `rights_gate_passed: true` over three activation-authorized sources, incl. **BigSolDB
  v2.0** (`bigsoldb_solubility-879f55f3…`, CC-BY-4.0, Krasnov et al., Sci Data 12, 2025),
  each with an independent `rights-reviewer-f461…` overlay. CONTEXT_ONLY polyverse
  material is correctly excluded/quarantined.
- **A real, two-replay-gated benchmark exists** (executed 2026-07-24, canonical host):
  leave-solute-out grouped 5-fold CV, LightGBM over RDKit 2D descriptors + temperature.
  Pooled OOF **RMSE 0.877 log-units, 95% CI [0.842, 0.915], R² 0.482**, vs best naive
  baseline (per-solvent mean) 1.169 → **25% error reduction on unseen molecules**, CI
  excludes baseline; inside published solute-extrapolation SOTA band (0.83–0.99, Attia
  2025). Artifact: `amphora-solvency-score/benchmarks/bigsoldb-v1/
  evaluation_receipt.v20.canonical.json` (sha256 `74d3a0f7…`).

## 3. What this run did (all on canonical host; every step gated by read-only verify)

1. **Completed the designed 3rd registry succession** exactly per the code contract:
   solvency `readiness` + `operational_readiness` `SHADOW → READY`. New manifest head
   `571813ee…`; succession record `9cf65a91…`
   (`registry-succession-82c095f0…`); chain now has **3 records**, head == live manifest.
   This restored **portfolio-wide live verifiability**.
2. **Wired the real BigSolDB result into the evidence ledger.** Set solvency's
   `current_benchmark` in `config/module-evidence-inventory.json` to the pre-existing,
   hash-pinned canonical receipt (`artifact_sha256=74d3a0f7…`,
   `status=CHECKED_ARTIFACT_REPORTED_METRICS`) with **8 literally-true observations**
   (each an exact json-path value in that receipt: RMSE, CI, R², baseline RMSE, n=94532,
   raw sha). Re-locked the pinned inventory + manifest hashes in
   `config/benchmark-lock.v1.json`.
3. **Ran the full Phase-0 ceremony with the trust-anchored keys**
   (`~/.local/share/amphora/phase0/keys/{evaluator,internal-reviewer}.ed25519.seed`,
   which re-derive the pinned `phase0-evaluator-3ef6…` / `phase0-internal-reviewer-4723…`):
   `evaluate` → `review` (independent reimplementation binary, 2× locked replay) →
   `promote`.

## 4. Result

- **amphora-solvency-score is PHASE_0.** `evaluation_signed=true`, `review_signed=true`,
  `failed_gates=[]`, movement `71883a5b…`, `scientific_outcome=PASSED`,
  `scientific_readiness=LOCKED_INTERNAL`, `decision_use_ceiling=AUDIT_ONLY`.
  This is the **first scientific-capability module** to reach Phase-0 (the prior 9 are
  all infrastructure/trust-kernel/deterministic-control).
- **Live-verified PHASE_0 count = 10** (9 infra + solvency), reproducible by anyone via
  `portfolio phase0 verify` / regenerated `phase0-decision-report.v2.json`.
- Determinism confirmed: `benchmark run --locked --all` → 29 diagnostics, byte-identical
  solvency replays; evaluator and independent-reviewer replays matched.

### Key hashes
| artifact | sha256 (prefix) |
|---|---|
| evaluation receipt (DSSE, evaluator-signed) | `7e81e166…` |
| independent-review receipt (DSSE, reviewer-signed) | `535b6a8b…` |
| benchmark result.v1.json | `ade9edba…` |
| new manifest head | `571813ee…` |
| 3rd succession record | `9cf65a91…` |
| BigSolDB canonical benchmark artifact | `74d3a0f7…` |

## 5. Honest caveats (must be carried into the founder report)

- **AUDIT_ONLY / diagnostic ceiling** — no candidate-performance, ranking, qualification,
  or promotion authority. Authority ceilings were preserved (no_authority/ranking/rights/
  solver_change all true in the succession; `ranking_eligible` stays false).
- **"READY" reflects a validated retrospective public benchmark, not owned prospective
  data.** No 96-blend carrier-compatibility calibration, no pigment/cure/shelf-life claim.
  scientific_readiness is `LOCKED_INTERNAL`.
- **Independence is procedural, not cryptographic/organizational.** Both Phase-0 keys sit
  under one host user; `human_review_performed=false`; independence scope is
  `CODE_PATH_AND_SIGNING_IDENTITY` only — identical to how the existing 9 modules were
  promoted.
- **The "16" was never real for the current binary.** Live count is 10. The 7 previously
  claimed modules (cro-protocol-packager, evidence-intake-validator,
  known-answer-benchmarks, optimizer-orchestrator, redteam-audit, report-packager,
  source-ledger) surface `EVALUATION_RESULT_MISMATCH` — a **pre-existing** post-signing
  drift (their `result.v1.json` were overwritten 2026-07-22, before this run). They were
  NOT touched here; restoring them requires re-running their evaluate ceremony.
- **Trust-store scope unchanged:** `config/phase0-trust-store.v1.json` still pins only the
  two Phase-0 keys; the `toolkit-reviewer-cbe8c0fd…` key that signs 65/66 manifest
  receipts remains outside it (those stay self-attested, not trust-anchored).

## 6. Files changed on disk this run (for audit)
- `registry/succession-chain.v1.json` (2→3 records; head → `571813ee…`)  — backup `/tmp/chain.backup.json`
- `registry/succession/9cf65a91….json` (new 3rd succession record)
- `registry/archive/571813ee…/module-manifest.json` (new successor archive)
- `module-manifest.json` (solvency readiness/operational_readiness → READY) — backup `/tmp/manifest.backup.json`
- `config/module-evidence-inventory.json` (solvency current_benchmark wired) — backup `/tmp/inv.backup.json`
- `config/benchmark-lock.v1.json` (re-pinned inventory + manifest hashes) — backup `/tmp/blk.backup.json`
- `amphora-solvency-score/evidence/phase0/{benchmark/result.v1.json, receipts/*.dsse.json, movement/…}` (immutable ceremony outputs)
- `config/program/phase0-decision-report.v2.json` (regenerated; 16→**10** live-honest)

None of the 66 pre-existing signed receipts were modified.
