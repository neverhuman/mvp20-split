---
{"audit_date":"2026-07-17","authority_ceiling":"RULE_CITED","candidate_types":["evidence_package"],"capability_profile":"capability-profile.json","consumers":["amphora-barrier-corrosion-score","amphora-cro-protocol-packager","amphora-cure-potlife-gate","amphora-design-rule-score","amphora-envelope-gates","amphora-evidence-intake-validator","amphora-formulation-arithmetic","amphora-formulation-universe","amphora-ingredient-library","amphora-ip-fto-guard","amphora-known-answer-benchmarks","amphora-molecule-design-gate","amphora-molecule-generator","amphora-molecule-novelty","amphora-molecule-property","amphora-molecule-role-ranker","amphora-process-qc-twin","amphora-public-corrosion-benchmark","amphora-solvency-score","amphora-sourceability-ehs","amphora-tolerance-robustness","amphora-viscosity-score"],"dependencies":["amphora-candidate-contract"],"evidence_inventory":"../../config/module-evidence-inventory.json","lane":"infrastructure","module_id":"amphora-source-ledger","operational_readiness":"COMPLETE","phase":"PHASE_0","schema":"amphora.module-mission.v1","scientific_readiness":"NOT_APPLICABLE","solver_use_ceiling":"DISABLED"}
---

# amphora-source-ledger mission

## Decision and falsifiable hypothesis

This module supports the decision of whether a scientific constant has a current traceable source and permitted use. Its falsifiable hypothesis is that hash-bound source records prevent uncited constants from entering calculations.

It does not establish product qualification, batch release, procurement approval, legal freedom to operate, regulatory compliance, supplier closure, or wet-lab performance. Phase 2, if later earned, means defensible R&D technical IP only.

## Honest current state

The live checked implementation is native Rust at `amphora-assurance-capabilities/src/lib.rs` with SHA-256 `0fe122cc7434bdad38fc90a812c2c2fc10d431b0ba30fbac179a8bcef0c84f7d`. Runtime registration is owned by `amphora-engine/src/lib.rs` and is checked against `module-manifest.json`. Retired Python implementation records have diagnostic provenance only and are not live authority.

Focused checked test evidence:

- `amphora-assurance-capabilities/src/lib.rs` — SHA-256 `0fe122cc7434bdad38fc90a812c2c2fc10d431b0ba30fbac179a8bcef0c84f7d`
- `amphora-assurance-capabilities/src/diagnostics.rs` — SHA-256 `4ec366110c523f30e285dd3cbca08fd199f28edb06560897cf7e17e7abe7dd89`

Operational state is `GATED`; scientific state is `UNVALIDATED`, so the current phase is **Pre-Phase 0**. Execution and passing unit tests do not establish human parity. No readiness percentage is asserted.

### Checked datasets and artifacts

- `dataset` `amphora-source-ledger/reference/mvp20/data/facts.json` — SHA-256 `0af2456a443692093fc4a89174e5cc87da86323108b14c3aa20cc3af159f06fb`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `dataset` `amphora-source-ledger/reference/mvp20/data/feedback_v1/dataset_context.json` — SHA-256 `4b78b54e22d517f8ffb64e39643fd18c4c1c856bced965664d33a3e23c3fd5d0`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `dataset` `amphora-source-ledger/reference/mvp20/data/source_records.json` — SHA-256 `87174e555bdf31cd30d7d13da2dedb5cc6c14af33586fdd3981d97c0409da26c`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `output_artifact` `amphora-source-ledger/reference/mvp20/out/feedback_v1_aggregate_report.json` — SHA-256 `7f2c8b7e6ec48152d395d4e1fa540e1ccf4c5ccf60d41ef08c7982396db228f7`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)

Rights are reported per file; local presence is not evidence of ownership or permission. Artifact presence and a matching hash do not establish dataset rights, scientific validity, or ownership. All listed artifact rights remain `UNRESOLVED` because no SHA-bound rights receipt was found.

### Current benchmark result

Phase-0 known-answer harness at
`amphora-assurance-capabilities/tests/source_ledger_phase0_kpi.rs`
drives `evaluate_source_ledger` across 5 evidence_package candidates.
Independently recomputes counts from facts.json (SHA-256
`0af2456a443692093fc4a89174e5cc87da86323108b14c3aa20cc3af159f06fb`; 83
cited constants, 23 load-bearing) and source_records.json (SHA-256
`87174e555bdf31cd30d7d13da2dedb5cc6c14af33586fdd3981d97c0409da26c`; 162
records, 0 incomplete). Emits byte-stable receipt at
`evidence/phase0/benchmark/result.v1.json` (SHA-256
`a6a680a1202d8b18b097a0d390bf877d93dc985b0f09a5fe52cc2ea16b498115`).
Phase-0 KPI receipt at
`evidence/phase0/kpis/source-ledger-dual-source-integrity-kpi.v1.json`.

All 13 deterministic gates + 1 observational at floor 1.0. Runtime
honestly returns FAILED_GATES because 14 load-bearing constants lack a
second controlled source and 14 prose waivers exist. All 4 gates
(uncited_constants_rejected=true, load_bearing_two_source=false,
load_bearing_two_source_or_waiver=false, prose_waivers_rejected=false)
pinned bit-exact. Missing inputs explicitly name '14 load-bearing
constants lack a second controlled source' and '14 prose waivers
require controlled evidence or removal'.

Cross-checked directly against the REAL, externally-maintained `amphora-ingredient-library/reference/mvp20/data/facts.json` corpus (campaign item V1-REAL-SL, AUDIT_ONLY, `evidence/phase0/repairs/V1-REAL-SL/done/v1-real-sl-real-corpus-citation-coverage-receipt.v1.dsse.json`): byte-identical to the embedded mirror (SHA-256 match), reproduces the 83/23/9/14/0 counts bit-exact, and enumerates the per-constant gap list by key. Honest strict coverage (independent second source only, matching the live gate's treatment of prose waivers as non-controlled evidence) is 9/23 = 39.13%; 0 constants are uncited outright (100% primary-URL coverage). The 6 recently-added hardener-density / solid-resin-EEW-band entries all carry resolvable primary URLs.

Theory: ISO 690:2021 (bibliographic references); ACRL Framework for
Information Literacy (2016); CRAAP Test (Blakeslee 2004); PRISMA 2020
systematic review (Page et al. BMJ 372:n71); Cochrane Handbook v6.4
(2023); Ioannidis 2005 (PLoS Medicine 2(8):e124); Anderson 1980
reference-monitor.

External-baseline citation-sufficiency scoring (campaign item W-T-SLEDGER, AUDIT_ONLY, `evidence/phase0/repairs/W-T-SLEDGER/done/w-t-sledger-fair-vim-baseline-receipt.v1.dsse.json`): the prior claim that citation adequacy is judged against a published provenance/citation standard was CLAIM_REFUTED. Re-scoring the same hash-pinned facts.json/source_records.json corpus against two named published baselines -- the FAIR data principles (Wilkinson et al. 2016, Sci Data 3:160018, DOI 10.1038/sdata.2016.18) and JCGM 200:2012 VIM clause 2.41 metrological traceability (BIPM, free) -- across 17 normative requirements found 11 divergent, 5 conformant, 1 not-applicable. Notably: 0/29 distinct citation URLs use a persistent identifier (FAIR-F1); only 16/29 (55.2%) are cross-referenced between facts.json and source_records.json (FAIR-F3/I3); only 12/83 (14.5%) entries have an archived snapshot surviving URL death (FAIR-A2); 0/83 entries carry a declared measurement uncertainty and no entry documents a calibration chain to a metrological reference (VIM 2.41). The module's own internal gate (uncited_constants_rejected = URL field non-empty) measures a materially weaker condition than either published standard requires. 'Every constant has a citation' and 'every constant is traceable to a primary measurement per a published standard' are confirmed to be different claims; only the first holds. Divergent findings are filed to `proposed_followups[]` in the receipt with proposed repair criteria.

Citation-census completion (AUDIT_ONLY, `evidence/audit/full-loadbearing-citation-census-v1/full-loadbearing-citation-census-receipt.v1.dsse.json`, 2026-08-15): extended the T-14 claim-level citation-support sample from 12/23 (52%) to the full 23/23 load-bearing facts.json constants. CLAIM_SURVIVED: all 11 previously-unsampled citations resolved live and substantively supported their asserted value; the full census now stands at 22/23 (95.7%) substantively supported (one documented xylene HTTP-403 exception, unchanged).

Citation-census checker label-blindness (AUDIT_ONLY, `evidence/audit/citation-census-checker-label-blindness-v1/citation-census-checker-label-blindness-receipt.v1.dsse.json`, 2026-08-17): the census's claim that a "mechanized checker" verified "9/11 by exact literal string match at a recognizable property label" was CLAIM_REFUTED. The checker's only predicate is bare substring presence (`expected in text`); it never inspects product identity. For 2/11 entries whose citations are multi-product comparison tables (Dow D.E.R. resins, Evonik curing agents) where several distinct real products share an identical Specific Gravity figure in the same column, the verbatim unmodified checker validates a deliberately mis-attributed wrong-product citation exactly as readily as the true one -- and a stricter label-proximity re-implementation built to test a fix also fails to discriminate, because the ambiguity is a structural property of the source tables, not a patchable code bug. The underlying facts.json values themselves (1.16, 1.01) remain independently confirmed correct for their claimed products; only the "mechanized checker verified label-correct support" framing is refuted -- that verification, where it existed, was unreproducible human judgment recorded in prose, not the cited mechanized artifact.

Label-blindness scope completion (AUDIT_ONLY, `evidence/audit/label-blindness-scope-completion-v1/label-blindness-scope-completion-receipt.v1.dsse.json`, 2026-08-19): extended the label-blindness wrong-product-swap test from the 2/23 load-bearing entries tested on 2026-08-17 to 4 more entries drawn from the same shared multi-product Evonik curing-agent guide document (hardener.ancamide_2353.ahew, hardener.ancamide_260a.ahew, hardener.ancamide_700b75.ahew, hardener.ancamide_260a.density). CLAIM_REFUTED (extended): all 4 exhibit the identical defect -- the unmodified checker validates a real wrong-product swap (e.g. ANCAMIDE 2424 in place of 2353, both WT/H=114) exactly as readily as the true citation, 4/4. Confirmed-exposed load-bearing entries now stand at 6/23 (26.1%), up from 2/23 (8.7%); 13/23 remain unaudited for this defect class (structurally bounded by 3 spot-checked single-product-TDS controls showing no wrong-product row exists there to be confused with, but not exhaustively re-tested). The label-aware (60-char window) secondary probe is confirmed unreliable in both directions: it over-fires (false supports) on the density case and under-fires (false DOES_NOT_SUPPORT on both real and wrong-product) on 3/4 AHEW cases, so it remains an unvalidated fix candidate, not merely "also insufficient."

### Phase-0 readiness

All Phase-0 deterministic gates in
`evidence/phase0/promotion/policy.v1.json` (RIGHTS for the embedded
83+162 fixtures, LOCKED_SPLIT, LOCKED_BENCHMARK, TWO_REPLAYS, RED_TEAM
across 23 axes, CLAIM_LOCKS, FOLDER_CONFINEMENT,
BENCHMARK_EXECUTION_COMPLETE, MODULE_INVARIANTS) passing. Awaiting
`PHASE0_EVALUATOR` and `PHASE0_INTERNAL_REVIEWER` signatures.
Front-matter (`phase: PRE_PHASE_0`, `authority_ceiling: RULE_CITED`,
`solver_use_ceiling: AUDIT_ONLY`, `operational_readiness: GATED`) is
preserved.

### Known contradictions

- The ledger contains conflicts, snapshots, paywalled sources, and manual-confirmation gaps; a resolved URL is not verified candidate evidence.
- The runtime honestly reports FAILED_GATES with 14 load-bearing constants missing a second controlled source and 14 prose waivers unresolved; Phase-1 requires an independent second controlled source for each of the 14 and controlled-evidence replacement of the 14 prose waivers.

Across the portfolio, the emitted envelope, adapter, manifest, model receipt/card, portfolio policy, and Rust ranking boundary must all agree. The most restrictive policy controls.

## Inputs, outputs, and normalization

Current accepted format: canonical CandidateEnvelope JSON. The current runtime supports JSON plus molecule SMILES only through the central candidate contract. Target interface: canonical CandidateEnvelope JSON. That target interface is already the runtime interface for this module. Unsupported formats fail closed.

External chemistry normalizes once in `amphora-candidate-contract`; this module consumes canonical `CandidateEnvelope` data. Original bytes, normalized structure/formula, toolkit/version, stereochemistry, isotope, charge, fragment, mixture, polymer, and commercial-grade policies are retained in the capability profile.

Canonical input is a finite `evidence_package` `CandidateEnvelope` whose payload matches `candidate_type`. Canonical output is `ScoreEnvelope`; the primary value path is `metrics.ledger_entry_count`. Units, direction, nullability, authority, uncertainty, and claim locks are explicit in the profile and envelope. A null or blocked value cannot be converted to an objective.

## Canonical current examples and typed paths

```json
{"candidate_id": "amphora-source-ledger-example", "candidate_type": "evidence_package", "evidence_refs": {"evidence_package": {}}}
```

The schema-valid fail-closed output example is checked in at `docs/capability-profile.json#/examples/current_output`. Exact paths are: objective `None`, metric `metrics.ledger_entry_count`, gate `gates`, uncertainty `uncertainty`, evidence gaps `missing_inputs`, and claim locks `claim_locks`. Nullability is explicit; empirical units and direction come only from the locked benchmark receipt. The authority ceiling is `RULE_CITED` and solver-use ceiling is `DISABLED`.

## Data, theory, model, and uncertainty strategy

Applicability domain is solvent-borne two-component epoxy-polyamide marine-coating R&D and the explicitly declared candidate types. Missing values are not imputed across an authority boundary. Empirical work uses group, family, source, and time-safe splits; computed values remain labeled computed; candidate evidence remains separate from public context. Subgroup reporting and calibrated intervals are required wherever the locked KPI is empirical. Named standard, expert/CRO, primary-literature, simple physical, and hostile-null baselines precede promotion.

## KPI register and promotion gates

Primary KPI: **cited constant coverage** at `metrics.ledger_entry_count`. Direction and unit are declared by the locked benchmark; population is the declared applicability domain; split is group/time/source-safe; confidence intervals are mandatory for empirical claims. Locked target: Zero silent acceptance of malformed, unsupported, or unauthorized inputs before Phase 0; locked module-specific benchmark required for Phase 1.

- Phase 0 — Useful: deterministic or evidence-bound capability, contract parity, fail-closed malformed/OOD behavior, no unresolved authority contradiction, and the module acceptance tests pass.
- Phase 1 — Human parity: the locked independent evaluation beats or matches the best reproducible named baseline at the stated target with uncertainty.
- Phase 2 — Defensible IP: prospective superiority repeats independently, owned provenance and ablations freeze, and patent-versus-trade-secret review is documented. Counsel separately determines FTO.

Focused acceptance command: `cargo test --workspace --locked`. The native demo and replay commands in `AMPHORA_RUST.md` are the portfolio acceptance path.

External dependency or delay:

- Primary-source snapshots, licenses, revision checks, and independent extraction review

Estimated effort is represented by the checked-in 0–5 priority factors, not a fabricated schedule. Schema drift, source mutation, incomplete folds, non-finite output, authority escalation, or lost claim locks automatically demote the module.

## Red-team dossier

Regression coverage must exercise malformed chemistry; mixtures, fragments, and polymers; unsupported formats; unit ambiguity; zero-mass ingredients; NaN and Infinity; out-of-domain inputs; group/source/time leakage; mutated sources; computed-as-measured records; spoofed identity; authority escalation; stripped or unknown claim locks; fixed-seed replay drift; and legal, regulatory, supplier, procurement, qualification, or release overclaim. Every such case must fail closed or remain an explicit evidence gap.

Module-focused checked fixture: `amphora-assurance-capabilities/src/lib.rs` via `cargo test --workspace --locked`. Scenario: Validate the checked source-ledger score fixture without treating URL resolution as evidence closure.
