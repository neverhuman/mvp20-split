# Red-team + real progress — molecule-property ChEBI truth-set + RDKit-backend unlock (2026-07-25)

Host: canonical **xbabe2** `/home/ubuntu/amphora/build/mvp20-split`. Invoked headless from xbabe1.
AUDIT_ONLY. **Nothing was promoted. No existing receipt or manifest was modified.** Live
`phase0_count` before and after this run = **10** (verified with the rebuilt binary).

## 1. Red-team of "we have FULL Phase-0" — REJECTED (with the true, reproducible state)

Live `portfolio phase0 status --all` (reproducible by anyone) = **10 PHASE_0 / 19 PRE_PHASE_0**:

- The 10 are: candidate-contract, envelope-gates, formulation-arithmetic, formulation-universe,
  model-card-authority, molecule-design-gate, run-provenance (all `NOT_APPLICABLE` science) +
  process-qc-twin, tolerance-robustness, **solvency-score** (`LOCKED_INTERNAL`).
- **Only ONE module is real externally-validated coating science: solvency-score** (BigSolDB
  CC-BY leave-solute-out RMSE 0.877, 25% over baseline; promoted 2026-07-25). process-qc-twin
  and tolerance-robustness are `LOCKED_INTERNAL` internal-consistency, not external science.
- The other 7 are infrastructure / deterministic control.

Two integrity findings founders must carry:
1. **Every `docs/mission.md` body prose says "current phase is Pre-Phase 0"** — including all
   ~15 whose JSON front-matter asserts `"phase":"PHASE_0"`. The front-matter is the live gate of
   record; the prose is stale boilerplate, but the contradiction should be reconciled before the
   report ships (do not quote the prose as the status).
2. **7 modules previously counted as PHASE_0 are currently FAILING live verification** with
   `EVALUATION_RESULT_MISMATCH` (cro-protocol-packager, evidence-intake-validator,
   known-answer-benchmarks, optimizer-orchestrator, redteam-audit, report-packager, source-ledger)
   — a pre-existing post-signing drift (result.v1.json overwritten 2026-07-22). The live count of
   10 already excludes them; a naive front-matter count would over-report. Not touched this run.

## 2. cure-potlife-gate — sound theory, REAL data wall, NOT promotable (confirmed)

Its Arrhenius pot-life KPI is genuinely good (MAPE 0.147, 6/6 metrics pass, Ea externally
corroborated). **But its only pot-life data is quarantined vendor technical datasheets** (Evonik,
Huntsman, Cardolite): the three `.amphora/data/cure-potlife-gate-rights-cleared-*.json` objects are
**zero-row** records, every source `eligible_for_derivatives:false, status:QUARANTINED`. `source-lock.v2`
has `eligible_sources:[]`, `rights_gate_passed:false`. Promoting it would require rights-clean
multi-temperature gel-time data that does not exist in-tree. Honestly blocked. No change made.

## 3. Real progress this run — molecule-property, the foundational chemistry module

molecule-property's Phase-0 gate is the **exact-locked EEW/AHEW benchmark** (epoxide-equivalent-weight
and amine-hydrogen-equivalent-weight that set the DGEBA + amine stoichiometric mix ratio — the core
two-part marine epoxy coating calculation). The prior gap ledger named 4 walls. This run closed/de-risked 3:

**(a) RDKit C++ FFI backend — CLOSED.** Rebuilt `amphora-tui` + `amphora-phase0-reviewer` with
`--features rdkit` against pinned RDKit C++ **2026.03.2** (libs already on host). Live
`benchmark run --locked --module amphora-molecule-property` now reports `backend_status.available=true`,
`exact_version_match=true`, and computes EEW/AHEW to **max abs error 0.0338 g/eq**. Gate
`pinned_rdkit_2026_03_2_available` flipped **false -> true**; all five chemistry gates now pass
(`equivalent_weight_max_abs_error_at_most_0_5`, `reactive_group_counts_100_percent`,
`structure_identity_and_mass_agree`, `invalid_and_out_of_domain_rejection_100_percent`,
`all_exact_controls_executed`). The "chemistry only works in Python" caveat is removed — the live
shipping Rust binary does the coating stoichiometry exactly.

**(b) Rights-clean in-scope truth-set data — ACQUIRED + HASH-VERIFIED.** Fetched the pinned
`FETCH_LOCKED_NOT_ACQUIRED` source: **ChEBI-252 3-star SDF, CC BY 4.0, EMBL-EBI**
(`chebi_3_stars.sdf.gz`, 59,482,451 B). Observed sha256
`8f17627476c66e899dabe3cd7ae1cbb94f7ee6c67f2ee91f077a77a19c940ad7` == fetch-lock expected (exact);
LICENSE sha256 `fe7b4ce8...` == expected. Both match the pre-staged acquisition record.

**(c) >=300 truth-set gate proven reachable (30x margin).** Deterministic RDKit-2026.03.2 census of
the release: 52,903 records -> 52,806 parsed -> 50,749 single-component -> 43,859 defined/no-wildcard ->
**9,025 in-scope reactive molecules** (315 epoxide, 8,729 amine N-H). `minimum_300_truth_set_molecules`
is reachable by ~30x. The data wall that blocks this module is broken.

All of (b)/(c) plus the backend deltas are captured in a **DSSE-Ed25519 two-replay AUDIT receipt**
(byte-identical replays, SHA-256 gate PASS), signed with the repo `LOCAL_DEVELOPMENT_AUDIT_ONLY` key
`local-9028773f...` (explicitly **NOT** trust-anchored):
`amphora-redteam-audit/benchmarks/molecule-property-chebi-truthset-unlock-v1/`.

## 4. Honest remaining work to actually promote molecule-property (scoped for next run)

Three gates still fail; none is a science defect, all are curation/governance:
1. `minimum_300_truth_set_molecules` — build the frozen set from ChEBI per `selection_lock`:
   ascending ChEBI-ID order, PubChem PUG-REST identity cross-check (exact InChIKey, exact formula,
   mass <=0.05 g/mol) — network-bounded, deferred deliberately (not rushed).
2. `independent_reference_receipt_bound` — mint the independent structure/mass reference receipt.
3. `sealed_controls_present` — seal the exact-control set.
Then run evaluate -> review (2x replay) -> promote with the trust-anchored Phase-0 keys (present on
host). This would make molecule-property the **2nd real-science Phase-0 module, and the first that
needs no proprietary data** (first-principles chemistry on a CC-BY truth set).

## Key hashes
| artifact | sha256 |
|---|---|
| ChEBI-252 payload (CC-BY-4.0) | `8f17627476c66e899dabe3cd7ae1cbb94f7ee6c67f2ee91f077a77a19c940ad7` |
| ChEBI-252 LICENSE | `fe7b4ce83b8381cc5b216bbb4af73c570688d1b819c73bbaed8ca401f4677cd6` |
| audit diagnostic (two-replay, identical) | `34ae598e9821fbf97ec50e6103e49b1e38841220b461b5208e7486150ff99e39` |
| audit DSSE envelope | `2fcb9f6b2d2845446244057ac3cea69d3334cd3db86d9d80ea391b766ce5c774` |

## Files added this run (audit trail; nothing existing modified)
- `amphora-molecule-property/reference/chebi/rel252/chebi_3_stars.sdf.gz` + `LICENSE.txt` (acquired, hash-verified)
- `amphora-redteam-audit/benchmarks/molecule-property-chebi-truthset-unlock-v1/` (scripts, 2 diagnostics, signed receipt, this analysis)
- `target/release/{amphora-tui,amphora-phase0-reviewer}` rebuilt with `--features rdkit` (prior binaries backed up in `/tmp/*.nofeature.bak`)
- config `molecule-property-sources.v1.json` acquisition_status left as-is (wiring deferred to the ceremony run, to avoid a half-wired state before the founder report)
