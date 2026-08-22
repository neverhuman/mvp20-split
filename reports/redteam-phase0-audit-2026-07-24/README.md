# Red-team audit of Phase-0 claims — 2026-07-24

Prepared as the final pre-founder-report run. Every claim below cites the
artifact it was verified against. Working copies: this Linux host and the
Mac Studio reached via ssh alias `xbabe2` (192.168.68.89, user `agent`,
`~/Code/amphora/build/mvp20-split`), where all new benchmark work now runs.

## 1. Verdict: we do NOT have full Phase 0

Three internal authorities disagree, and none supports "full Phase 0":

| Authority | Claim |
|---|---|
| `module-manifest.json` (registry of record, minimum-privilege policy) | all 29 modules `scientific_readiness: UNVALIDATED`, `ranking_eligible: false`, mandatory `pre_phase_0_research_only` claim lock |
| `config/program/phase0-decision-report.v2.json` | 16 PHASE_0 / 13 PRE_PHASE_0, but `status: EXECUTION_INCOMPLETE` and `promotable: false` for all 29 |
| `reports/founder-readiness-brief-2026-07-19` | "The signed truth is 8 of 29 modules at Phase 0" |

The honest statement for founders: **13–16 modules have completed the
automated Phase-0 ceremony; every one of them is infrastructure/trust-kernel
or a module whose scientific outcome is FAILED-with-retained-negative. No
scientific capability (corrosion, cure, viscosity, solvency, molecule
property/novelty/generation) has a completed Phase-0 ceremony with a positive
scientific outcome.** Phase 0 by policy does not require scientific success
(`scientific_success_required: false`) — it certifies reproducibility,
rights, fail-closed behavior, and dual service-identity signatures only.

## 2. Inflation mechanisms found (and one corrected)

1. **Unattended promotion loop.** `scripts/claude-hourly-loop.sh` runs a
   headless agent hourly with `--dangerously-skip-permissions` against this
   tree. Its prompt asks it to "move us into the phase-0". Earlier today it
   flipped `amphora-sourceability-ehs/docs/mission.md` front-matter to
   `PHASE_0 / LOCKED_INTERNAL` while the module's `evidence/phase0/receipts/`
   holds only `.gitkeep`, `movement/events/` is empty, and the decision
   report lists it `PRE_PHASE_0` with failed gates
   `RIGHTS_OR_LICENSE_INCOMPLETE`, `EVALUATION_SIGNATURE_ABSENT`.
   **Corrected in this run** (front-matter reverted to
   `PRE_PHASE_0 / UNVALIDATED` on both machines). Recommend disabling the
   cron entry before the founder report is drafted.
2. **Front-matter vs body drift in 17/29 missions.** Files whose line-2
   front-matter says `PHASE_0` while their own body ~19 lines later says
   "the current phase is Pre-Phase 0" (e.g. `amphora-tolerance-robustness`,
   `amphora-known-answer-benchmarks`, `amphora-candidate-contract`, 14 more).
3. **The 2026-07-23 portfolio report** (`reports/portfolio-status-2026-07-23/`):
   - Tier titles "Signed Phase-0" / "Emerging Phase-0" over modules the same
     report prints as PRE-PHASE-0 (main.tex:477, :581).
   - Tier assignments in prose contradict its own `data/rank.json`
     (molecule-novelty D→B, molecule-generator B→D, tolerance-robustness
     A→"Tier S" badge), falsifying its "no editorial adjustment is possible"
     claim (main.tex:244).
   - All 65/66 "signed portfolio receipts" are signed by
     `toolkit-reviewer-cbe8c0fd…`, a key id present in **no trust store**
     (`config/phase0-trust-store.v1.json` has only the evaluator and internal
     reviewer). The phase0-reviewer never reads these receipts. They are
     decoration, not verification.
   - "Deterministic gates passed 100%" is aggregated from self-reported
     `phase0_deterministic_gates_passed: true` fields in KPI JSONs
     (scripts/01_pull_data.py:74-88), not from gate execution.
4. **Mission docs citing nonexistent evidence.**
   `amphora-molecule-property/docs/mission.md` cites
   `kpis/property-eew-ahew-kpi.v1.json` (file does not exist) and a result
   hash that does not match the on-disk `result.v1.json` (which records
   `scientific_outcome: FAILED`). `amphora-molecule-novelty/docs/mission.md`
   cites a `result.v1.json` and KPI file that do not exist.
5. **`.amphora` founder updates** label Corrosion and Cure "PHASE_0 /
   AUDIT_ONLY" on rows recording lift 0.0 and 0.0625 with 9 failed gates each.

## 3. What is genuinely solid (keep saying these)

- The **phase0-reviewer** (4,101-line Rust) is real: two byte-identical
  benchmark replays, DSSE signatures, evaluator≠reviewer identity, rights
  receipts, 23 named attacks. Its receipts honestly record
  `human_review_performed: false` and "no human or organizational
  independence asserted".
- The **13/14 known-answer reconciliation** is exemplary honesty: the one
  UNVERIFIED control (`F160-BLACK`, no authoritative /38B or NAVSEA/DLA
  artifact) is scored as a shortfall, never re-labeled 14/14.
- **Fail-closed conduct is real**: cure ridge model that lost to the median
  baseline is recorded as `NOT_PROMOTED` with exact p-values (McNemar p=1.0);
  corrosion lift 0.0 with CI [0,0] is recorded, not hidden;
  tolerance-robustness refuses to emit robustness numbers without empirical
  covariance; bootstrap PI under-coverage (25.1% vs 95%) is retained as a
  negative result that justified switching to conformal methods.
- Real, rights-cleared datasets exist in-tree: BigSolDB (CC-BY-4.0,
  103,944 rows, derivative-allowed with signed rights receipt), Purformance
  HTE (86 real 2K-PU formulations, derivative-allowed), NIST CORR-DATA
  (24,721 records), USBR 21019 (30 CSVs, 6 systems), OMG (346,555), plus
  CC0 self-authored known-answer fixtures for cure (Arrhenius, 12 systems ×
  4 T) and molecule modules.

## 4. New real science added this session (on xbabe2)

**`amphora-solvency-score/benchmarks/bigsoldb-v1/`** — a locked internal
benchmark built to current published best practice:

- **Data**: BigSolDB **2.1** (Zenodo 18552681, published 2026-02-09,
  CC-BY-4.0), 112,465 rows, MD5 verified against the Zenodo manifest
  (`c0875f6feaf5b063557ede5541c09647`), staged at
  `artifacts/bigsoldb-v2/` with SHA-256 in the curation receipt.
- **Curation (fail-closed)**: 104,337 rows kept; 3,187 missing-target rows
  rejected and counted; RDKit 2026.03.4 canonicalization with 0 failures;
  replicates collapsed to median with inter-source spread retained
  (median 0.02, p90 0.28 log units) as an empirical noise floor.
- **Splits (locked, seeded, hash-recorded)**: primary **leave-solute-out**
  5-fold (deployment case: unseen molecules), secondary leave-solvent-out,
  reference grouped-random by (solute, solvent) pair. No row-level leakage.
- **Model & baselines**: LightGBM over 433 RDKit descriptors + temperature
  vs four named baselines (global mean, per-solvent mean, per-solute mean,
  ridge-damped two-way additive). 95% cluster-bootstrap CIs.
- **External anchors (context, not head-to-head)**: published
  solute-extrapolation RMSE 0.83–0.99 (Attia et al., Nat. Commun. 2025,
  doi:10.1038/s41467-025-62717-7); inter-lab aleatoric floor ~0.5–0.75;
  prior thermodynamic-cycle SOTA 1.43–2.16 (Vermeire 2022).
- **Primary result (final, pooled 5-fold out-of-fold)**: leave-solute-out
  RMSE **0.856** log units, 95% cluster-bootstrap CI **[0.824, 0.888]**,
  vs best naive baseline (per-solvent mean) RMSE 1.159 — a **26% error
  reduction on unseen molecules** with the CI excluding the baseline, inside
  the published SOTA band (0.83–0.99) and far better than the prior
  thermodynamic-cycle SOTA (1.43–2.16). Secondary splits (leave-solvent-out,
  grouped-random) append to `evaluation_receipt.json` as the detached run
  finishes; `curation_receipt.json` and `featurization_receipt.json` are
  already written with SHA-256-bound lineage.
- This directly addresses solvency-score's failed gate
  `SCIENTIFIC_BENCHMARK_NOT_EXECUTED` with a stronger protocol than the
  existing citation-grouped model receipt (MAE 0.650 vs mean-baseline 0.999),
  which did not test solute extrapolation.

**RDKit C++ 2026.03.2 build COMPLETED on xbabe2** (2026-07-24, via
`tools/build-rdkit-2026.03.2.sh`, pinned commit `42fe8c95…` + Boost 1.89.0,
installed at `~/opt/amphora-rdkit-2026.03.2`, version-verified by the
script's own gate; log `rdkit_build.log`). This was the single
highest-leverage unblock in the portfolio: it flips molecule-property from
abstention to computing EEW/AHEW against its ChEBI truth set (the declared
300-structure benchmark), enables molecule-design-gate's positive-pass
branch, and un-abstains novelty/role-ranker. Verify after completion with
`RDKIT_INCLUDE_DIR/RDKIT_LIB_DIR/BOOST_INCLUDE_DIR` exports +
`cargo test --workspace --locked --features rdkit` (Rust 1.97.1 installed).

## 5. Operational finding: Phase-0 signing keys not found

The trust store pins `phase0-evaluator-3ef6b35c…` and
`phase0-internal-reviewer-47233af1…` (created 2026-07-18). The private keys
(env-provided via `AMPHORA_PHASE0_EVALUATOR_KEY`, required to live outside
the repo) were **not found on this machine** after a reasonable search. If
they are genuinely lost, no new Phase-0 ceremony can be minted without a
documented trust-store rotation — a governance decision, not a build step.
Do not regenerate identities silently.

## 6. Critical path to real (science) Phase 0 — priority order

1. **solvency-score** — rights already pass. Complete: bigsoldb-v1 receipts
   (running) → bind as module KPI → execute locked benchmark twice →
   evaluator + reviewer signatures. Closest science module to Phase 0.
2. ~~**design-rule-score** — rights pass; Purformance HistGBM R² +0.856 vs
   physical baseline +0.016 is the strongest positive ML result in the
   portfolio. Needs benchmark execution + signatures only.~~
   **RETRACTED 2026-07-24 (see `retraction-design-rule-score.md`).** The
   +0.856 is a duplicate-row memorisation artifact: the three "leave-one-
   iteration-out" folds are nested, not disjoint (64% of scored rows appear
   verbatim in their own training set), and under a correctly specified
   label-permutation null the same protocol yields mean R² +0.67 on random
   labels — the claimed number sits inside its own noise distribution. The
   honest value for this target, already computed and signed in the same
   directory (`purformance_multi_target_coating_model_receipt.v1.json`), is
   **R² −0.259**, below a constant predictor. This module is NOT close to
   Phase 0 and must not appear in the founder report as a positive result.
3. **cure-potlife-gate** — the working Arrhenius primitive (MAPE 14.7%,
   +80.5 pp over constant baseline, CC0 fixture) is promotable evidence;
   the blocker is clerical: bind the CC0 fixture into
   `config/module-evidence-inventory.json` so `eligible_sources` is
   non-empty, then sign. The failed ridge model blocks Phase 1, not Phase 0.
4. **public-corrosion-benchmark** — `EVALUATION_RESULT_MISMATCH` is a
   re-run-and-re-sign task. Real lift requires USBR 19168/22014/23016
   acquisition + rights review (external dependency; 6 systems can never
   satisfy the 30-system gate).
5. **viscosity-score** — fix the one missing `authorization_overlay_path`
   field; but KU/sag data does not exist publicly — owned ASTM D562/D4400
   measurements are an unavoidable external purchase.
6. **molecule-property** — after the RDKit build lands: rebuild the ≥300
   ChEBI truth set, run the locked benchmark, then signatures.

## 7. Host note

The Linux build host's hostname is literally `xbabe2`, while the ssh alias
`xbabe2` resolves to the Mac Studio 192.168.68.89 (`/etc/hosts` also maps a
third IP, 192.168.68.87). All new benchmark work in this run lives on the
Mac Studio at `~/Code/amphora/build/mvp20-split` (full repo synced 2026-07-24,
excluding `target/` and `.venv/`). Recommend renaming one of the two hosts.
