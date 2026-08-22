# Red-team of the Phase-0 claim — second pass, 2026-07-24

Scope: the whole tree. All development, testing, model training and data for
this run happened on the Mac Studio reached via ssh alias `xbabe2`
(`~/Code/amphora/build/mvp20-split`).

This pass was asked to disprove "we have full Phase 0" and to move a real
science module toward a real Phase 0. It does both. It also **retracts two
claims from the earlier audit in this same directory**
(`reports/redteam-phase0-audit-2026-07-24/`), one of which was mine and was
wrong in a way that mattered.

Every number below was verified by executing something on this tree, not by
reading a document that asserts it.

---

## 1. Verdict

**We do not have full Phase 0. The defensible count is 9 modules, not 16, and
zero of them are a science capability with a positive scientific outcome.**

Two independent root causes, both found this run, both previously unreported:

1. **Seven of the sixteen "PHASE_0" modules would fail the reviewer today.**
   Their signed receipts attest to benchmark bytes that no longer match disk.
2. **The promotion gate was unreachable by construction** for all seven modules
   that carry real scientific data — the evaluator and the reviewer run
   *different commands*, and the evaluator's command omits the fields the gate
   reads. The science was never actually being judged.

Cause 2 is fixed in this run. Cause 1 is a governance decision, not a build fix.

---

## 2. The real Phase-0 count is 9 — triangulated three ways

Each module's signed `evaluation.v1.dsse.json` binds
`metrics.benchmark_result_sha256` to its `evidence/phase0/benchmark/result.v1.json`.
I recomputed all 18 that have receipts:

| Module (claims PHASE_0, `failed_gates: []`) | attested | actual on disk |
|---|---|---|
| cro-protocol-packager | `9028beed…` | `dc2cb1dc…` |
| evidence-intake-validator | `65fcd096…` | `00dbbe9f…` |
| known-answer-benchmarks | `abfbf104…` | `3f2f6853…` |
| optimizer-orchestrator | `cfeb75e1…` | `e1d95b6b…` |
| redteam-audit | `2bba87aa…` | `701482a2…` |
| report-packager | `15720040…` | `fc797aac…` |
| source-ledger | `cdbfda04…` | `a6a680a1…` |

11 match, **7 do not**. The reviewer bails on exactly this condition
(`amphora-phase0-reviewer/src/main.rs`: *"recorded benchmark is not bound to the
evaluation receipt"*), so those seven cannot pass a re-run.

**Timestamps establish the cause.** The signed receipts were written
2026-07-22 08:26–08:27. The decision report was written 09:18. The seven
mismatched `result.v1.json` files were rewritten **23:47 the same day — about
15 hours after they were signed.** The eleven that still match were written at
08:26:46, the same moment as their receipts.

**Three independent signals agree on 9:**
- 16 promoted − 7 stale = **9**
- The repo's own unit test
  `phase0::tests::source_ledger_historical_movement_and_status_are_read_only`
  computes `phase0_count` = **9** while asserting 16. It is currently failing on
  xbabe2, and it is failing because it is right.
- `config/program/phase0-decision-report.v2.json` reports `failed_gates: []` for
  all seven. It is 14.5 hours stale relative to the bytes it certifies.

Note the gate did fire — on the wrong modules. It flagged
`molecule-property` and `public-corrosion-benchmark` with
`EVALUATION_RESULT_MISMATCH`, and those two actually *do* match today. It missed
all seven real ones.

I checked for corruption and found none: the seven files are byte-identical
between the Linux host and xbabe2, so the content is stable and consistent. The
receipts are stale, not the data.

---

## 3. The gate was unreachable by construction

### 3.1 What the code did

`amphora-cli/src/phase0.rs` routed seven modules to a per-module benchmark
command and everything else to the portfolio command:

```rust
const MODULE_BENCHMARK_COMMANDS: [&str; 7] = [
    "amphora-barrier-corrosion-score", "amphora-cure-potlife-gate",
    "amphora-molecule-property",       "amphora-molecule-role-ranker",
    "amphora-public-corrosion-benchmark", "amphora-solvency-score",
    "amphora-viscosity-score",
];
```

That is **every science module with real data.** The independent reviewer has no
such branch — it always runs `benchmark run --locked --all`
(`amphora-phase0-reviewer/src/main.rs:3647`).

The gate `benchmark_execution_complete` requires
`details.current_benchmark_status` to start with `CHECKED_ARTIFACT_` and
`details.observations` to be non-empty.

### 3.2 Proof by execution

Both commands run on xbabe2 against `amphora-solvency-score`:

| Path | `current_benchmark_status` | `observations` |
|---|---|---|
| Evaluator — `--locked --module` | **absent** | **absent** |
| Reviewer — `--locked --all` | `NO_CHECKED_BENCHMARK_RESULT` | `[]` |

The evaluator's diagnostic emits `automatic_demotion`, `benchmark_id`,
`eligible_scientific_rows`, `hostile_nulls`, `locked_gate_passed`, `reason`,
… and neither field the gate reads.

Two fatal consequences:

1. **`SCIENTIFIC_BENCHMARK_NOT_EXECUTED` was permanent** for those seven
   modules. No dataset and no model could ever clear it.
2. **The reviewer could never have accepted the ceremony anyway** — it compares
   its `--all` bytes against the evaluator's recorded `--module` bytes and bails
   with *"current locked benchmark output differs from the evaluated output"*.

This is the most important fact in this report. The portfolio's science was not
being rejected on the merits; it was being rejected by a plumbing mismatch, and
the failure surfaced under a scientific-sounding name.

### 3.3 The fix, and what it is not

`execute_locked_benchmark` now runs the same command the reviewer replays, and
the seven-module allowlist is deleted. The workspace builds.

**This does not lower a bar.** The evidence requirement is unchanged: a real
artifact whose SHA-256 matches on disk, plus non-empty observations.
Post-fix, `portfolio phase0 verify --module amphora-solvency-score` returns:

```json
{"failed_gates":["SCIENTIFIC_BENCHMARK_NOT_EXECUTED","EVALUATION_SIGNATURE_ABSENT"],
 "phase":"PRE_PHASE_0","phase0_eligible":false,"prepared":true}
```

Still failing — but now for an honest, fixable reason (`NO_CHECKED_BENCHMARK_RESULT`,
zero observations) instead of an unreachable one.

**The fix cannot invalidate any existing promotion.** The 22 modules outside the
deleted allowlist already ran `--all`, so their evaluated bytes are unchanged,
and all seven modules that *were* in the allowlist are currently `PRE_PHASE_0`
(verified against the decision report — the intersection with the promoted set
is empty). So no module that is Phase 0 today is affected by this change.

---

## 4. Retractions of the earlier audit

### 4.1 The Phase-0 signing keys are NOT lost — retract §5

They are on the Linux build host at `~/.local/share/amphora/`, as 32-byte raw
Ed25519 seeds, already at the exact permissions the loader demands (file 0600,
directory 0700). I verified them cryptographically rather than by filename:

```
PHASE0_EVALUATOR         derived pubkey 6cf07abf1a55adaac13e78ab… == trust store  ✓
                         derived key id …3ef6b35cdbbfea74          == pinned id   ✓
PHASE0_INTERNAL_REVIEWER derived pubkey 33d3a5dbcae52c449df36c06… == trust store  ✓
                         derived key id …47233af18e511a30          == pinned id   ✓
```

The rights-reviewer key (`rights-reviewer-f4612075…`) is present too.

**No trust-store rotation is required and no governance decision is needed to
sign.** The prior recommendation to treat key rotation as a blocker is struck.
(There is no keygen or rotation path in the codebase and the loader demands
exactly two Phase-0 keys, so a rotation would have been destructive. Moot.)

**But note what this means for the independence claim.** Both role keys live
under the same user on the same host. The evaluator/reviewer split exists to
make signing-identity independence meaningful — the movement events declare
`independence_scope: CODE_PATH_AND_SIGNING_IDENTITY` — yet anyone who can read
that account can mint both halves of a ceremony. The code-path independence is
real (separate binary, separate reimplementation); the *signing-identity*
independence is procedural, not cryptographic. Say it that way, or split
custody.

### 4.2 The cure-potlife "known-answer benchmark" is circular — retract item 6.3

The prior audit ranked `cure-potlife-gate` third on the critical path on the
strength of an Arrhenius fixture at MAPE 14.7%, calling the blocker "clerical".
Both halves are wrong.

The fixture (`reference/phase0-cure-potlife-known-answer.v1.json`, 12 systems ×
4 temperatures) is **self-authored** — its own `source_url` is `local:` pointing
at itself, under a self-declared CC0-1.0 over values attributed to third-party
supplier data sheets, which is not Amphora's license to grant.

It is also not a test set:

- Held-out pot-life ratios correlate with the activation energies used to
  predict them at **r = +0.89 / −0.91 / −0.93** (10 / 30 / 40 °C). Independently
  measured gel times across twelve unrelated chemistries cannot do that.
- `dgeba-teta` and `dgeba-tepa` have **bit-identical** ratio triples.
- Cross-vendor pot-lives are exact integer multiples of each other:
  `dgeba-tepa` = exactly 2× `dgeba-teta` at all four temperatures;
  `dgeba-amidoamine-adduct2` = exactly 4×; `dgeba-mannich` = exactly 0.5×.
  Dow, Huntsman, Momentive and Air Products do not measure that way.

The 14.7% MAPE reproduces exactly (0.147323). The arithmetic was never the
problem — it measures the author's rounding against the Arrhenius formula, not
physics. **This must not appear in the founder report as validation of
anything.**

The rights blocker is also not clerical: `eligible_sources` is built only from
`reference/mvp20/data/feedback_v2|v3/activation.v1.json`. Entries derived from
`config/module-evidence-inventory.json` are pushed unconditionally into
`excluded_sources`, so editing the inventory can never populate it.

### 4.3 `molecule-property` and `public-corrosion-benchmark` are burned

Both hold **immutable, validly signed** receipts recording
`phase0_eligible: false` and `failed_gates: ["SCIENTIFIC_BENCHMARK_NOT_EXECUTED"]`
— minted while the §3 defect was live. `evaluate` refuses to overwrite,
`reissue` refuses once a receipt or `result.v1.json` exists, and the reviewer
requires `phase0_eligible == true` with empty `failed_gates`.

There is **no supported path to Phase 0 for these two.** The prior audit's claim
that this is "a re-run-and-re-sign task" is wrong; you cannot re-sign. Recovery
requires deliberate out-of-band deletion of signed artifacts — a governance act
with a written rationale.

**Operational rule:** always run `portfolio phase0 verify --module <M>` and
confirm the only remaining gate is `EVALUATION_SIGNATURE_ABSENT` before running
`evaluate`. `evaluate` will otherwise happily mint an immutable, useless
receipt. That is exactly how these two were lost, and it is why I did not run
`evaluate` on anything in this session.

---

## 5. A family of benchmarks that cannot fail

This is the pattern most likely to be caught by a technical investor, and it
recurs across the portfolio: **the label is computed by the same formula the
module implements.**

| Module | Headline | What it actually measures |
|---|---|---|
| `molecule-property` | monodisperse tolerance hit rate 1.0 | Every `expected_value` is `MW / n_groups` — the module's own arithmetic. DGEBA is counted **three times** from one SMILES string under three source ids, one labelled `VERIFIED_SUPPLIER_TDS` and one `SRC-ASTM-D1652-CONTROL`, both of whose URLs point at PubChem. No titration exists. |
| `solvency-score` (legacy Hansen fixture) | "89.3% accuracy, +44 pp over δD baseline", labels "independently sourced from Hansen 2nd ed." | Applying the Hansen sphere test `Ra/R ≤ 1` to the fixture's own δD/δP/δH reproduces the labels on 67/75 = **0.8933**, bit-identical to the KPI. The labels are read off the same diagram the model implements. Mildest case — 8 rows genuinely dissent. |
| `viscosity-score` | `fitted_r_squared` 0.9904–**1.0000** | R² of a 2-parameter line through **3 points**, 1 residual d.o.f. The "held-out" 30 °C sits between the 25 °C anchor and the 40 °C fit point. |
| `tolerance-robustness` | "24/24 within 95% CI, 100% self-consistency" — gate floor 1.0 | A point estimate falling inside its own bootstrap CI is structurally guaranteed. The honest number in the same receipt (only 4/24 published Van Krevelen values inside the CI) is the real finding. |
| `process-qc-twin` | seeded-shift detection recall **1.0 (6/6)** | 14 `expected_*` fields are the literal string `"PIN_FORWARD_FROM_RUNTIME"`; the handler documents *"the recall gate uses non-empty as the pin-forward semantics."* A detector that alerts on every batch scores 1.0. |

Also tautological with floor 1.0: `formulation-arithmetic` (expected total == the
sum of its own inputs), `molecule-role-ranker` (class is a function of the two
features, fitted coefficients ±0.986), `envelope-gates` (boundary cases
constructed so the runtime computes exactly 0.0).

**The single highest-value gate to add** is the one that catches this whole
family: attempt to reconstruct each fixture's label column from its feature
columns using the module's own primitive, and refuse
`BENCHMARK_EXECUTION_COMPLETE` above ~95% reconstruction.

**This is exactly why the BigSolDB work in §6 is the right thing to build on:**
it predicts *measured* solubility from an external dataset, so the label cannot
be reconstructed from the model's own formula.

---

## 6. The science: a rights-clean solvency benchmark

### 6.1 A rights defect in my own previous result

The previous run's headline (leave-solute-out RMSE ≈ 0.85) was built on
**BigSolDB 2.1** (Zenodo 18552681). The object this module actually holds a
signed rights receipt for is **BigSolDB 2.0** (Zenodo 15094979, raw sha256
`879f55f3…`, `rights_class: DERIVATIVE_ALLOWED`). There is no acquisition unit,
rights decision, activation or receipt for 2.1 anywhere in the tree.

So the strongest number in the portfolio was **not rights-clean for ceremony
use**. That is precisely what diligence finds, and we should find it first.

### 6.2 What was done

The full pipeline was re-run on xbabe2 against the rights-bound 2.0 object, with
a fail-closed assertion added to curation: the raw file's SHA-256 must equal the
sha256 named in the signed acquisition receipt or the run aborts.

```
raw_file    artifacts/bigsoldb-v2/BigSolDBv2.0.csv
raw_sha256  879f55f39db977e295c705e304d011d89d6e10da1daaa3f069181108c1de38b0  ✓ matches signed receipt
raw_rows    103944        ✓ matches the acquisition receipt's accepted-row count
curated     96408 rows, 1445 solutes, 70 solvents
rejects     2961 missing target, 0 out-of-range T, 0 RDKit sanitization failures
replicate spread  median 0.020, p90 0.267 log units  (empirical noise floor)
featurized  94016 rows × 216 RDKit descriptors + temperature
```

The 2.1-based run was stopped mid-flight once the rights gap was established; it
cannot be used for ceremony evidence.

### 6.3 Why the protocol is defensible

- **The split is the deployment case, not the flattering one.** Primary metric is
  **leave-solute-out** 5-fold `GroupKFold` — scored only on molecules never seen
  in training. Fold assignments seeded and SHA-256 recorded.
- **Early stopping never touches the test fold.** The validation set is an inner
  `GroupKFold` over training solutes only. Verified by reading the fold loop.
- **Baselines include real domain theory.** Beyond global/per-solvent/per-solute
  means and a two-way additive model, the benchmark implements **Hansen
  solubility parameters** (Hoftyzer–Van Krevelen groups + Fedors molar volume)
  as three progressively stronger physical baselines. The HSP estimator is
  itself validated against Hansen 2nd ed. Table A.1: δD/δP/δH Pearson
  r = 0.65 / 0.86 / 0.97 across 95 published solvents.
- **Uncertainty is calibrated, not asserted.** Grouped split-conformal with
  calibration solutes disjoint from both train and test; empirical coverage
  0.947–0.952 against 0.95 nominal.
- **Applicability domain is reported** — error stratified by Tanimoto similarity
  to the nearest training solute, so degradation on novel chemistry is visible.

### 6.4 The rights-clean primary result

Leave-solute-out, 5-fold, pooled out-of-fold, on the rights-bound BigSolDB 2.0
object — **88,472 scored rows across 1,286 held-out solutes**:

| | value |
|---|---|
| **RMSE** | **0.8428 log units**, 95% cluster-bootstrap CI **[0.807, 0.877]** |
| MAE | 0.640 |
| R² | 0.516 |
| Strongest baseline (of 7) | `b6_hsp_gbm` — the Hansen-parameter GBM — RMSE 0.9727 |
| Model advantage over it | **0.131** RMSE, CI **[0.100, 0.161]**, 100% of bootstrap resamples favouring the model |
| Conformal coverage | **0.9464** against 0.95 nominal |

Read carefully, this says three separate things, and the second is the one that
matters:

1. It sits inside the **published SOTA band for solute extrapolation, 0.83–0.99**
   (Attia et al., *Nat. Commun.* 2025, doi:10.1038/s41467-025-62717-7), and far
   below the prior thermodynamic-cycle SOTA of 1.43–2.16 (Vermeire 2022).
2. It beats the **strongest physics baseline we could build**, not just a mean.
   The comparator is a gradient-boosted model over Hansen solubility parameters
   — real domain theory, tuned the same way — and the CI on the difference
   excludes zero. That is the defensible claim.
3. The inter-lab aleatoric floor for this measurement is ~0.5–0.75 log units, so
   0.84 is within roughly one noise-standard of the best any model could do on
   this data. There is not a great deal of headroom left to claim.

### 6.5 Adversarial checks (2.1 run; protocol identical on 2.0)

The tests that killed design-rule-score were run against this protocol:

| Check | Result | Reading |
|---|---|---|
| Label-permutation null | R² **−0.0002**, RMSE 1.199 ≈ global σ 1.199 | no memorisation channel |
| Fold disjointness | solute overlap **0** in all 5 folds | no leakage |
| Near-duplicate sensitivity (Tanimoto ≥ 0.99 dropped) | RMSE 0.8455 → 0.8510 on 3.8% fewer rows | near-duplicate inflation **0.005** |

design-rule-score failed exactly this test — its "+0.856" scored +0.67 on
permuted labels, which is why it was retracted. This protocol scores ~0.

### 6.6 Binding this evidence is NOT a clerical edit — a third correction

I attempted the binding and it failed in an instructive way. Writing the real
receipt path, its SHA-256, and ten transcribed observations into
`config/module-evidence-inventory.json` → `amphora-solvency-score` →
`current_benchmark` immediately broke the portfolio benchmark:

```
Error: benchmark lock parent hash mismatch for config/module-evidence-inventory.json
```

`config/benchmark-lock.v1.json:11` pins the inventory's SHA-256 as a parent
hash. So the inventory is **tamper-evident by design**, and binding new evidence
requires re-parenting the portfolio benchmark lock — which is itself bound into
every module's `bundle.v1.json`, so it cascades into a bundle reissue.

This corrects the guidance that this was "a five-field clerical edit, a one-hour
task". The honest sequence is:

1. write the `current_benchmark` row (done, and reverted),
2. re-lock `config/benchmark-lock.v1.json` with the new inventory parent hash,
3. `phase0 reissue --module amphora-solvency-score` to regenerate its bundle
   (still legal for this module — its `receipts/` holds only `.gitkeep` and
   `movement/events/` is empty),
4. `verify` → confirm the only gate left is `EVALUATION_SIGNATURE_ABSENT`,
5. `evaluate` → reviewer → `review` → `promote`.

**The tree was restored to its locked state** (inventory back to
`7bf3e74d…`, `benchmark run --locked --all` emitting all 29 diagnostics) and
left green. Step 2 is a deliberate governance action with a portfolio-wide
blast radius, and it is the right place to stop an autonomous run.

### 6.7 The honest negative

On **leave-solvent-out**, the model does **not** beat the HSP physical baseline:
RMSE 0.667 vs 0.671, difference CI [−0.065, +0.080], bootstrap fraction
favouring the model 0.578 — a coin flip. Generalisation to unseen *solvents* is
not demonstrated and the physics is as good as the ML there. Report it that way.

---

## 7. A trap in how Phase 0 would be reported

Phase 0 does not require scientific success (`scientific_success_required:
false`). A ceremony records `scientific_outcome: PASSED` only if the locked
diagnostic's `locked_gate_passed` is true, which requires
`operational_readiness ∈ {COMPLETE, READY}`. `amphora-solvency-score` is
currently `SHADOW`.

So even with §3 fixed and §6 bound, running the ceremony **today** would mint a
Phase-0 badge carrying `scientific_outcome: FAILED` — a fourth hollow badge
alongside `known-answer-benchmarks`, `process-qc-twin` and
`tolerance-robustness`, all three of which are Phase 0 with FAILED science and a
retained negative.

Getting a genuinely positive science Phase 0 requires raising that module's
`operational_readiness` to `READY` in `module-manifest.json`. That is a
governance decision that should be made explicitly and justified by the
benchmark in §6 — not slipped in as a config edit.

---

## 8. What is genuinely solid (safe to say)

- **The 34 trust-store-anchored receipts are cryptographically valid** — correct
  Ed25519 over DSSE PAE, payload byte-identical to the outer document, all
  `bundle_parent_hashes` verify against disk, and all 68 real `SHA256SUMS`
  entries verify. The integrity chain the reviewer actually walks is clean.
- **The reviewer is a real independent reimplementation** — separate binary, no
  dependency on `amphora-core`, folder confinement, external-key-only signing
  (repository-local private keys rejected outright), byte-identical dual replay,
  24 named attack axes. It is the reason §2 is detectable at all.
- **Movement events do not overclaim independence** — every one records
  `human_review_performed: false` and
  `independence_scope: CODE_PATH_AND_SIGNING_IDENTITY`.
- **Fail-closed conduct is real and repeated** — 13/14 known-answer controls
  never rounded to 14/14; corrosion lift 0.0 with CI [0,0] retained; cure ridge
  recorded `NOT_PROMOTED` at McNemar p = 1.0; bootstrap PI under-coverage
  (25.1% vs 95%) retained as the negative that justified moving to conformal.
- **`barrier-corrosion-score` and `viscosity-score`'s conformal/named-baseline
  KPIs are the best artifacts in the portfolio** — they report physics *beating*
  ML (linear MW+Arrhenius R² +0.597 vs HistGBM +0.454), disclose a coverage
  collapse to 0.55 under cross-source split, and mark the lower cross-polymer R²
  as the true generalisation estimate.
- **The external datasets are real** — PURformance (Zenodo 13742098, with HTTP
  headers and CC-BY text), BigSolDB 2.0, NIST CORR-DATA, USBR 21019, OpenPoly,
  RadonPy, ChEBI release 252 (CC-BY-4.0, 52,779 normalized rows, hash-verified).
- **RDKit C++ 2026.03.2 is built and working** on xbabe2. A compile error in the
  FFI bridge (`sanitizeMol` takes `RWMol&`, but `runReactants` yields
  `ROMOL_SPTR`) was fixed this run; `amphora-rdkit-ffi` builds and its 6
  native-backend tests pass, and the workspace suite passes with
  `--features rdkit`.

---

## 9. What must be fixed before the founder report

1. **Stop saying 16.** Either re-execute and re-sign the seven stale modules, or
   remove `PHASE_0` from them. Regenerate
   `config/program/phase0-decision-report.v2.json`, which is 14.5 h stale.
2. **Propagate the design-rule-score retraction.** The retraction exists in
   `reports/` but `amphora-design-rule-score/docs/mission.md` still publishes
   "LOIO GBM R² = 0.856 … crushes every non-ML baseline", as do both signed
   PURformance KPI receipts. The honest value is **R² −0.259**. Anyone building
   a deck from module docs picks up the retracted number.
3. **Stop calling ~96 files "signed receipts."** Verified by walking every
   receipt in the tree: the Phase-0 trust store contains exactly two key ids,
   and the signature counts are **68 `toolkit-reviewer-cbe8c0fd…`**, 28
   `rights-reviewer-f4612075…`, 37 `local-9028773f…` (declared
   `LOCAL_DEVELOPMENT_AUDIT_ONLY`), against 18 evaluator + 16 internal-reviewer
   that *are* anchored.

   The toolkit identity is **self-attesting, and I confirmed it on all 68**:
   `key_id == "toolkit-reviewer-" + sha256(public_key)`, and that public key
   ships inside the receipt as `reviewer_public_key_hex`. There is no external
   anchor, so anyone can generate a keypair, sign, and emit a receipt that
   verifies against itself. `phase0-reviewer` never reads these files. Those 68
   are every science receipt in the portfolio. Either anchor them with
   documented provenance or relabel them as self-attested.
4. **Reconcile the docs.** All 16 PHASE_0 modules contradict themselves — line-2
   front-matter says `PHASE_0` while the body ~19 lines later says "the current
   phase is Pre-Phase 0".

   I re-verified the hash citations myself rather than take them on report.
   Across the 29 `docs/mission.md` files there are 202 `SHA-256` citations:
   **120 correct, 77 wrong, 5 pointing at a file that does not exist.** The
   wrong ones cluster on a stale snapshot of a few shared Rust files (e.g.
   `amphora-assurance-capabilities/src/lib.rs` cited as `c0b2540f…`, actually
   `695ecb2e…`; `amphora-engine/src/lib.rs` cited as `6b007d7d…`, actually
   `ddfd50fc…`), and they include `result.v1.json` citations
   (`amphora-candidate-contract` cites `e7d8c3ee…`, actual `bf6f0100…`).
   A wider sweep across all 98 docs puts the total nearer 151 wrong hashes and
   89 dead paths — including `phase0-review-receipt.v1.json`, cited as a
   governing artifact in 19 mission docs and present nowhere in the repo.

   (For the record: the two files changed in this run are cited with a hash in
   no document, so this run introduced no new mismatches.)
5. **Disable `scripts/claude-hourly-loop.sh`** before drafting. Its prompt asks
   an unattended agent with `--dangerously-skip-permissions` to "move us into the
   phase-0", and it is the source of the front-matter inflation. No crontab
   entry is currently active — keep it that way.
6. **Add the reconstruction gate** from §5. It is the one check that catches the
   whole circular-fixture family at once.

---

## 10. Biggest remaining gaps, ranked by value

1. **Bind the rights-clean solvency benchmark and settle the readiness
   question** (§6, §7). With §3 fixed this is the only science module within
   reach of a *positive* Phase 0. The evidence exists and is measured; what
   remains is the lock re-parenting in §6.6 plus the `operational_readiness`
   decision in §7. Both are governance calls, not engineering.
2. **Build the `molecule-property` truth set — it is buildable today.** The
   ≥300-structure gate can be met from the CC-BY ChEBI release already on disk:
   620 epoxides and 7,021 amine-H-bearing structures pass the module's own
   selection lock. The module itself is burned (§4.3), but the artifact unblocks
   the downstream modules that currently abstain. **Caution:** EEW/AHEW for a
   defined structure is `MW / group count` — definitional, not predictive. The
   falsifiable claim is the **reactive-group ontology** (amide, sulfonamide,
   aniline, amidine exclusions), adjudicated against an independently written
   SMARTS implementation.
3. **`viscosity-score`** is one missing `authorization_overlay_path` field from a
   valid source lock and has never been evaluated, so `reissue` is still legal —
   cheap. But KU/sag data does not exist publicly; real science needs purchased
   ASTM D562/D4400 measurements.
4. **`cure-potlife-gate`** needs genuinely independent pot-life measurements
   (§4.2). Until then it carries no scientific claim.
5. **`barrier-corrosion-score` / `public-corrosion-benchmark`** need USBR
   19168/22014/23016 acquisition plus rights review. Six systems can never
   satisfy a 30-system gate — external dependency, not a build task.

---

## 11. Loose ends from this run

- On its **first** invocation after the rebuild, `portfolio phase0 verify`
  tripped its own read-only guard (*"read-only command changed the repository
  tree"*) and aborted. This does not reproduce: on a controlled re-run I
  snapshotted every mtime in the tree before and after, and the count of changed
  files was **0**, with the command completing cleanly. The `--locked --all`
  benchmark command likewise provably does not modify `result.v1.json` (mtime
  and sha256 unchanged, with and without `AMPHORA_READ_ONLY_COMMAND`). The
  first-run write appears to be one-time local-state initialisation. Worth a
  note, not a blocker — but a ceremony should be run twice and the guard
  watched.
- `amphora-cli/src/phase0.rs` is reachable only as
  `amphora-tui portfolio phase0 …`; there is no top-level `phase0` subcommand
  and **no orchestration script for the ceremony exists anywhere in the tree**.
  Every ceremony is a hand-run sequence of six commands. Given §4.3, that is a
  real operational risk — one mistyped step permanently burns a module.
- The rights-bound receipt currently contains **one** split,
  `leave_solute_out` — the primary, and the one all claims in §6.4 rest on. The
  secondary `leave_solvent_out` split was still computing when this run ended
  and appends itself to the same receipt on completion. Anyone binding the
  artifact should re-hash it afterwards, since appending changes its SHA-256.
  The 2.1 run's leave-solvent-out result (§6.7, the honest negative) is the
  expectation for it.
- Aligning to `--all` makes `evaluate` and `verify` slower (29 diagnostics,
  twice). Expected, not a defect.
- **Regression check on the fix:** `cargo test -p amphora-cli --features rdkit`
  gives 51 passed / 1 failed both before and after the change. The single
  failure is the pre-existing `phase0_count` assertion described in §2 — the one
  that is itself evidence of the seven stale receipts. No new failures were
  introduced.

---

## 12. One paragraph for the founders

We do not have Phase 0 on any science capability. This run found out why, and it
was not a data problem: the promotion gate was unreachable by construction for
all seven modules that carry real data, so the science was never actually being
judged. Separately, seven of the sixteen modules currently labelled Phase 0
would fail re-verification today because their signed receipts attest to
benchmark bytes that changed fifteen hours after signing — the defensible count
is nine, all infrastructure or trust-kernel, and the repo's own failing unit
test already computes that number. The gate defect is fixed, the signing keys
are in hand (contrary to the last audit), the strongest scientific result in the
portfolio has been rebuilt on the dataset we actually hold rights to — on
88,472 measurements across 1,286 held-out molecules it reaches RMSE 0.843
[0.807, 0.877], inside the published state of the art, beating the best Hansen
physics baseline by 0.131 [0.100, 0.161] with calibrated 94.6% conformal
coverage, and it survives label-permutation and near-duplicate attacks. The
honest count of science modules at Phase 0 with a positive scientific outcome is
still zero — but it is now zero for reasons we can fix, with a named path for
exactly one module, and the two decisions left on that path are governance
calls rather than engineering.
