# Red-team + real-science run — 2026-07-24 (hourly cron, host xbabe1→xbabe2)

## 0. Scope of this run
Independent red-team of the Phase-0 claims **plus** one piece of genuinely new,
reproducible science executed on the canonical machine. All work on
`ssh xbabe2:/home/ubuntu/amphora/build/mvp20-split`. No existing signed receipt
modified. No front-matter promoted. xbabe1 tree untouched.

## 1. Verdict (independently re-verified, not taken on faith)
**We do NOT have full Phase 0.** Confirmed from three independent authorities on
this host:
- `config/program/phase0-decision-report.v2.json`: `status=EXECUTION_INCOMPLETE`,
  **16 PHASE_0 / 13 PRE_PHASE_0**, `promotable=false` for all 29.
- Front-matter phase of all 29 missions re-read directly: the 16 PHASE_0 modules
  are **every one** infrastructure / trust-kernel / fail-closed
  (candidate-contract, envelope-gates, run-provenance, report-packager,
  redteam-audit, source-ledger, formulation-arithmetic, known-answer-benchmarks,
  process-qc-twin, tolerance-robustness, …). **Every scientific-capability module
  is PRE_PHASE_0**: solvency, barrier-corrosion, cure-potlife, viscosity,
  molecule-property / novelty / generator / role-ranker, design-rule,
  public-corrosion.
- solvency-score decision record: `PRE_PHASE_0`, failed gates
  `SCIENTIFIC_BENCHMARK_NOT_EXECUTED`, `EVALUATION_SIGNATURE_ABSENT`.

## 2. Prior-audit claims I independently corroborated
- **Trust-store gap CONFIRMED.** `config/phase0-trust-store.v1.json` pins exactly
  two keys (`phase0-evaluator-3ef6b35c…`, `phase0-internal-reviewer-47233af1…`).
  The `toolkit-reviewer-cbe8c0fd…` key that signs **65/66** manifest receipts is
  **absent from the trust store** → those receipts are self-attested, not
  trust-anchored. The "66 signed receipts" headline must not be presented to
  founders as independently verified.
- **design-rule-score retraction is real and correct to keep.** The +0.856 was a
  duplicate-row leakage artifact; honest value **R² −0.259**. Retraction doc
  present. Do NOT resurrect it as a positive.
- **sourceability-ehs dishonest promotion stayed reverted** (`PRE_PHASE_0 /
  UNVALIDATED` on this host). Good.
- **Signing keys for a real Phase-0 ceremony are absent on this host** — the
  trust-anchored evaluator/reviewer private keys are not here, so
  `EVALUATION_SIGNATURE_ABSENT` **cannot** be honestly cleared this run. That is a
  governance/key-custody action, not a build step.

## 3. Divergence found this run (important for the founder report)
The prior audit's headline new science — solvency `bigsoldb-v1` RMSE 0.856 and
the RDKit C++ 2026.03.2 build — was produced on a **different host** (the Mac
Studio reachable as `xbabe2` from *that* environment). On THIS canonical host
(`/home/ubuntu/…`): only the benchmark **scripts** were present — **no data
artifact, no receipts, no RDKit C++ prefix** (`~/opt/amphora-rdkit-2026.03.2`
does not exist). The founder report must not cite that 0.856 as if it lives in
the canonical tree.

## 4. New real science executed HERE this run (closes a real gap)
`amphora-solvency-score/benchmarks/bigsoldb-v1/` — re-derived from scratch on the
**in-tree rights-cleared** data actually present:
`feedback/v1/external_data/bigsoldb_v2/raw/BigSolDBv2.0.csv` (BigSolDB v2.0,
CC-BY-4.0, Krasnov et al., *Sci Data* 12 (2025), doi:10.1038/s41597-025-05559-8),
raw SHA-256 recorded in the receipt.

- **Curation (fail-closed):** 103,944 raw rows → 2,961 missing-target rows
  rejected and counted (never imputed) → 96,924 rows; 1,445 unique solutes ×
  70 solvents; **0 SMILES-parse failures** and 0 out-of-range temperatures under
  RDKit 2026.03.2 canonicalization; replicate (solute,solvent,T) triples
  collapsed to median, spread retained as an empirical noise floor (median 0.0,
  p90 0.0, max 6.50 log units). Raw SHA-256
  `879f55f39db977e295c705e304d011d89d6e10da1daaa3f069181108c1de38b0`.
- **Model / protocol:** LightGBM (deterministic) over RDKit-2026.03.2 2D
  descriptors (solute + solvent) + temperature; **primary split = leave-solute-out
  grouped 5-fold** (deployment case: unseen molecules), plus leave-solvent-out and
  grouped-random-in-domain; inner grouped holdout for early stopping; 95%
  cluster-bootstrap CIs. No row-level leakage.
- **Baselines:** global-mean, per-solvent mean, per-solute mean, ridge-damped
  two-way additive.
- **Primary result (leave-solute-out, pooled out-of-fold, N=96,924 over 1,445
  solute groups):** model **RMSE = 0.877 log units**, 95% cluster-bootstrap CI
  **[0.842, 0.915]**, R² = 0.482, frac|err|≤1log ≈ per receipt. Best naive
  baseline (per-solvent mean) RMSE = 1.169 → **≈25% error reduction on unseen
  molecules**, with the model CI entirely below the baseline. Per-fold RMSE
  {0.868, 0.833, 0.881, 0.875, 0.925} reproduced **byte-identically** across
  three independent executions.
- **External context anchors (not head-to-head):** Attia et al. 2025 (Nat.
  Commun., doi:10.1038/s41467-025-62717-7) solute-extrapolation RMSE 0.83–0.99,
  inter-lab aleatoric floor ~0.5–0.75; Vermeire 2022 thermodynamic-cycle 1.43–2.16.
- **Reproducibility (two-replay SHA-256 gate = PASS):** two fully independent
  executions of the locked pipeline. Curation receipts byte-identical. Evaluation
  receipts differed **only** in the `wall_seconds` timing field (271.6 vs 247.7);
  every split, metric, CI, fold-assignment hash, feature count and raw-data SHA
  byte-identical. Canonical (timing-free) evaluation receipt SHA-256
  `74d3a0f71e6512283de2bf32a16fc76a1543439dbbb0a92c73e986d4f187a9ae`
  (run-A full `934b3b83…`, run-B full `57c593ec…`).
- **Signature:** DSSE Ed25519 over the canonical receipt with the repo
  `LOCAL_DEVELOPMENT_AUDIT_ONLY` key `local-9028773f49591193` (NOT trust-anchored);
  signature verified against the pinned public key; envelope byte-stable on
  re-sign (`8dd6dd61…`). Receipt:
  `amphora-solvency-score/benchmarks/bigsoldb-v1/inhouse_benchmark_receipt.v1.dsse.json`.

**Honest status change:** this **closes the scientific half** of solvency-score's
blockers — `SCIENTIFIC_BENCHMARK_NOT_EXECUTED` now has a real, reproducible,
leakage-safe, on-canonical-host result. It does **NOT** clear
`EVALUATION_SIGNATURE_ABSENT` (needs the trust-anchored evaluator key + human
review). solvency-score therefore stays `PRE_PHASE_0`; front-matter untouched.
It is now the **single closest scientific module to Phase 0**, blocked only on a
governance/key step, not on science.

## 5. Biggest remaining gaps (priority for founders)
1. **Key custody / governance.** No new science-positive Phase-0 ceremony can be
   minted until the trust-anchored evaluator/reviewer keys are located or a
   documented trust-store rotation is approved. This gates EVERY science module.
2. **solvency-score** — science done (this run); needs only the signature/review
   governance step.
3. **cure-potlife-gate** — real Arrhenius primitive exists (CC0 fixture); blocker
   is clerical (bind fixture into evidence inventory) + signature.
4. **RDKit C++ FFI** not built on canonical host → molecule-property /
   design-gate / novelty / role-ranker remain abstaining. Python RDKit works
   (used here); the Rust `--features rdkit` path needs the C++ prefix.
5. **Corrosion / viscosity** — external data acquisition (USBR 19168/22014/23016;
   owned ASTM D562/D4400) — cannot be closed by software.

## 6. What did NOT change (honesty guarantees)
No existing receipt altered. No manifest KPI count changed. No front-matter
promoted to PHASE_0. The new receipt is AUDIT_ONLY and self-declares
`promotes_authority=false`, `human_review_performed=false`. NOMAD crystal /
semiconductor data in-tree was left untouched (out of coating IP scope).
