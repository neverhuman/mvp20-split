---
{"audit_date":"2026-07-17","authority_ceiling":"EVIDENCE_ONLY","candidate_types":["formulation"],"capability_profile":"capability-profile.json","consumers":["amphora-optimizer-orchestrator","amphora-redteam-audit"],"dependencies":["amphora-candidate-contract","amphora-run-provenance"],"evidence_inventory":"../../config/module-evidence-inventory.json","lane":"infrastructure","module_id":"amphora-model-card-authority","operational_readiness":"COMPLETE","phase":"PHASE_0","schema":"amphora.module-mission.v1","scientific_readiness":"NOT_APPLICABLE","solver_use_ceiling":"DISABLED"}
---

# amphora-model-card-authority mission

## Decision and falsifiable hypothesis

This module supports the decision of whether a model receipt may be used at a requested R&D authority level. Its falsifiable hypothesis is that minimum-privilege policy rejects every incomplete, stale, spoofed, or over-ceiling grant.

It does not establish product qualification, batch release, procurement approval, legal freedom to operate, regulatory compliance, supplier closure, or wet-lab performance. Phase 2, if later earned, means defensible R&D technical IP only.

## Honest current state

The live checked implementation is native Rust at `amphora-engine/src/lib.rs` with SHA-256 `ddfd50fcebf96b096fff8406dfe27b512ab8e88564f76b644ffda776df662abb`. Runtime registration is owned by `amphora-engine/src/lib.rs` and is checked against `module-manifest.json`. Retired Python implementation records have diagnostic provenance only and are not live authority.

Focused checked test evidence:

- `amphora-engine/src/lib.rs` — SHA-256 `ddfd50fcebf96b096fff8406dfe27b512ab8e88564f76b644ffda776df662abb`

Operational state is `COMPLETE`; scientific state is `UNVALIDATED`, so the current phase is **Pre-Phase 0**. Execution and passing unit tests do not establish human parity. No readiness percentage is asserted.

### Checked datasets and artifacts

- `output_artifact` `amphora-model-card-authority/reference/mvp20/out/validation_cards.json` — SHA-256 `bea4ba80cdcd694189b7123448644ec842ea9b763a80a22ca2feaf56ec26da42`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)

Rights are reported per file; local presence is not evidence of ownership or permission. Artifact presence and a matching hash do not establish dataset rights, scientific validity, or ownership. All listed artifact rights remain `UNRESOLVED` because no SHA-bound rights receipt was found.

### Current benchmark result

No checked-in module-specific benchmark result artifact was identified.

No checked result promotes this module. The locked independent benchmark remains `NOT_PASSED` until a qualifying receipt meets the KPI gate.

### Known contradictions

- A model card records and restricts authority but cannot grant scientific validation, legal approval, or product authority.

- W-T-MCA (2026-08-13, `evidence/phase0/repairs/W-T-MCA/done/w-t-mca-mitchell-2019-conformance-done-receipt.v1.dsse.json`): FIRST NAMED-PUBLISHED-BASELINE VERDICT for this module -- CLAIM_REFUTED. 9 normative sections enumerated from Mitchell et al. (2019), "Model Cards for Model Reporting" (FAT* '19, DOI 10.1145/3287560.3287596) -- Model Details, Intended Use, Factors, Metrics, Evaluation Data, Training Data, Quantitative Analyses, Ethical Considerations, Caveats and Recommendations -- scored mechanically against the live `metrics.model_card` object emitted by `amphora-engine/src/lib.rs:270` (using the already-captured live-runtime-envelope-parity-v1 ground truth, not a new run). Result: 0/9 conformant, 9/9 divergent, 0/9 not_applicable. Sharpest finding: this module's OWN score-envelope.schema.json already requires kpi_name, unit, direction, validation_bar, dataset_ids, dataset_checksums, and current_status on every model_card, yet the live runtime emits none of those 7 fields in any of the 3 captured non-error cases -- the published baseline names, with external authority, a completeness gap this module's own contract already specified and never enforced. Mapped 4 of the portfolio's already-REFUTED claims (ip-fto metric-schema-parity, ip-fto claim-chart-provenance, tolerance-robustness repeated-scaffold Monte Carlo, ip-fto counsel-assertion-detection-completeness) to the specific requirement IDs that would have surfaced them earlier. 9 proposed_followups filed, one per divergent section. Does not affect the separate authority-lattice-completeness claim (Denning 1976 baseline, evidence/audit/authority-lattice-completeness-v1) -- that concerns the grant-ceiling lattice, not card field completeness.

- T-07 (2026-08-13, `evidence/phase0/repairs/T-07/done/t07-authority-escalation-encoding-done-receipt.v1.dsse.json`): FIRST ADVERSARIAL AUTHORITY-LATTICE VERDICT for this module -- CLAIM_REFUTED. A live-Rust differential probe (links the real amphora-core crate; NOT a re-implementation) drove amphora_core::rank_candidates / authorize_optimizer_request with 6 authority-escalation cases x 4 alternate JSON encodings each (24 combinations) against a hypothetical maximally-compliant amphora-model-card-authority card. 3 combinations (case authority_tier-above-ceiling, encodings lowercase "ranking", trailing-space-padded "RANKING ", and Cyrillic-homoglyph "RANKІNG") achieved feasible=true / ACCEPT from the live reference monitor: its forbidden-tier guard is an exact-byte-equality denylist (`"RANKING"|"OPTIMIZER"|"PRODUCTION"`) with no case-folding, trimming, or Unicode normalization, so a byte-distinct but visually/semantically equivalent encoding of a forbidden tier is not caught. This refutes authority_registry_is_binding as a robust property of the reference monitor against a spoofed or corrupted engine-result.v1 document (in the live production pipeline authority_tier is always registry-derived, never candidate-controlled, so blast radius is scoped to that document boundary). failed_cards_cannot_rank separately holds, but only because `ranked` is a hardcoded-false constant in amphora_core::rank_candidates for every input, not because card content is discriminated -- confirmed by a runtime assertion that fired zero times across all 26 live calls. A positive control (a deliberately weakened re-implementation omitting the ranking_eligible/usable_by_optimizer guard) confirmed the harness can detect a planted defect of this kind.

- candidate-strict-parse-front-door-v1 (2026-08-15, `evidence/audit/candidate-strict-parse-front-door-v1/candidate-strict-parse-front-door-receipt.v1.dsse.json`): CLAIM_REFUTED, scoped to the live-runtime-envelope-parity-v1 KPI's own methodology (that KPI's overall SURVIVED verdict from 2026-08-04 stands otherwise). That KPI's probe (`runtime_probe/src/main.rs`) documents its ground truth as captured "exactly as a hostile caller would exercise it" via "the strict candidate-contract front door." A live differential probe (links the real `amphora_core::parse_json_strict` and `EnginePool::score_campaign_modules`, no re-implementation) fed one fixed raw-bytes candidate containing a duplicate `candidate_type` JSON object key ("evidence_package" then "formulation") through both paths. The real byte-level front door (`CandidateEnvelope::from_bytes` → `parse_json_strict`) correctly rejects it: `duplicate JSON key: candidate_type`. The KPI's own methodology — `serde_json`'s default lenient parse (silent last-key-wins) followed by `CandidateEnvelope::from_value`, which never calls `parse_json_strict` — silently accepts it and scores it (`ok:true`, resolved to "formulation"), with none of the KPI's g0–g5 gates capable of detecting the divergence. Two-replay byte-identical. Does not demonstrate an authority escalation for this module: `TrustCapability::evaluate`'s branch for `amphora-model-card-authority` is a hardcoded default arm that reads neither candidate_type content nor payload content, and `usable_by_optimizer`/`ranking_eligible`/`granted_level` are descriptor-derived constants never read from candidate JSON — so no client-controlled duplicate key can raise this module's own granted authority. What is refuted is narrower: the KPI's claim that its differential-testing methodology is equivalent to the real hostile-caller entry point, and its blindness to an entire class of duplicate-key divergence that `amphora-core` visibly built defenses against elsewhere in the same crate. Proposed followup: add a g6 gate asserting `from_bytes` and `from_value` agree on every corpus case's raw bytes, or read the corpus through `parse_json_strict`.

- manifest-tamper-surface-reachability-v1 (2026-08-17, `evidence/audit/manifest-tamper-surface-reachability-v1/manifest-tamper-surface-reachability-receipt.v1.dsse.json`): CLAIM_REFUTED, attacking the two prior NON-RUNTIME Python-transcription receipts least-privilege-authority-parity-v1 (gate G3, 10 manifest-tamper probes) and authority-lattice-completeness-v1 (gate N, 26 single-clause knockouts). Both corroborate "minimum-privilege policy rejects every incomplete, stale, spoofed, or over-ceiling grant" by mutating a Python copy of module-manifest.json and showing their own transcription of `amphora-engine::validate_manifest` (lib.rs:318) rejects every mutation — neither ever calls live Rust. A static source-provenance analysis (deterministic grep/regex over the checked-in Rust source, not a re-implementation of policy logic) establishes that `validate_manifest` is unreachable by any live caller with anything other than the single compile-time manifest: (a) it carries no `pub` modifier — Rust's own privacy rule forbids any call from outside `amphora-engine/src/lib.rs`; (b) it has exactly one call site workspace-wide (`NativeRegistry::build()`, lib.rs:176); (c) that call site is reachable only via `OnceLock::get_or_init` — evaluated at most once per process, cached forever, no reset/reload method exists; (d) the manifest bytes it validates are `const MANIFEST_BYTES: &[u8] = include_bytes!("../../module-manifest.json")` — a compile-time constant frozen into the binary, with the sole call site's argument-derivation chain reading that constant directly, no path/env/fs indirection anywhere in the chain. Because no live grant attempt can ever reach this function, the G3/N tamper-probe results — while internally consistent as Python computations — do not corroborate rejection of any "spoofed"/"stale"/"incomplete"/"over-ceiling" GRANT as the module's falsifiable hypothesis requires: `validate_manifest` is a build-time/startup integrity check on the one embedded manifest, not a per-grant runtime defense. The two receipts' own "does_not_close" text ("a live-runtime differential harness remains Phase-1") undersold this — it framed the gap as work not yet done, when the tested threat model has zero live attack surface by construction. The actual attacker-reachable grant-decision path (`NativeRegistry::envelope` → `TrustCapability::evaluate` → `amphora_core::rank_candidates`/`authorize_optimizer_request`) is a separate code path already probed live by T-07, which found it DOES leak (encoding-based `authority_tier` escalation) — a gap the manifest-tamper probes gave zero coverage of. Does not reopen G1/G2 (least-privilege-authority-parity-v1) or L (authority-lattice-completeness-v1), which concern `score_semantics`/the authority envelope on the real, valid manifest, not manifest-tamper reachability.

Across the portfolio, the emitted envelope, adapter, manifest, model receipt/card, portfolio policy, and Rust ranking boundary must all agree. The most restrictive policy controls.

## Inputs, outputs, and normalization

Current accepted format: canonical CandidateEnvelope JSON. The current runtime supports JSON plus molecule SMILES only through the central candidate contract. Target interface: canonical CandidateEnvelope JSON. That target interface is already the runtime interface for this module. Unsupported formats fail closed.

External chemistry normalizes once in `amphora-candidate-contract`; this module consumes canonical `CandidateEnvelope` data. Original bytes, normalized structure/formula, toolkit/version, stereochemistry, isotope, charge, fragment, mixture, polymer, and commercial-grade policies are retained in the capability profile.

Canonical input is a finite `formulation` `CandidateEnvelope` whose payload matches `candidate_type`. Canonical output is `ScoreEnvelope`; the primary value path is `metrics.may_rank`. Units, direction, nullability, authority, uncertainty, and claim locks are explicit in the profile and envelope. A null or blocked value cannot be converted to an objective.

## Canonical current examples and typed paths

```json
{"candidate_id": "amphora-model-card-authority-example", "candidate_type": "formulation", "formulation": {"application": {"dft_mil": 5.0, "relative_humidity_pct": 50.0, "substrate": "steel", "surface_preparation": "declared", "temperature_C": 25.0}, "basis": "mass_g_per_batch", "batch_mass_g": 137.13, "ingredient_catalog_version": "facts.v2", "process": {"application_method": null, "induction_time_min": null, "mix_order": null, "pot_age_h": 0.0}, "recipe": {"part_A": {"dgeba_828": {"ingredient_id": "dgeba_828", "mass_g": 100.0}}, "part_B": {"ancamide_350a": {"ingredient_id": "ancamide_350a", "mass_g": 37.13}}}}}
```

The schema-valid fail-closed output example is checked in at `docs/capability-profile.json#/examples/current_output`. Exact paths are: objective `None`, metric `metrics.may_rank`, gate `gates`, uncertainty `uncertainty`, evidence gaps `missing_inputs`, and claim locks `claim_locks`. Nullability is explicit; empirical units and direction come only from the locked benchmark receipt. The authority ceiling is `EVIDENCE_ONLY` and solver-use ceiling is `DISABLED`.

## Data, theory, model, and uncertainty strategy

Applicability domain is solvent-borne two-component epoxy-polyamide marine-coating R&D and the explicitly declared candidate types. Missing values are not imputed across an authority boundary. Empirical work uses group, family, source, and time-safe splits; computed values remain labeled computed; candidate evidence remains separate from public context. Subgroup reporting and calibrated intervals are required wherever the locked KPI is empirical. Named standard, expert/CRO, primary-literature, simple physical, and hostile-null baselines precede promotion.

## KPI register and promotion gates

Primary KPI: **unauthorized grant rate** at `metrics.may_rank`. Direction and unit are declared by the locked benchmark; population is the declared applicability domain; split is group/time/source-safe; confidence intervals are mandatory for empirical claims. Locked target: Zero silent acceptance of malformed, unsupported, or unauthorized inputs before Phase 0; locked module-specific benchmark required for Phase 1.

- Phase 0 — Useful: deterministic or evidence-bound capability, contract parity, fail-closed malformed/OOD behavior, no unresolved authority contradiction, and the module acceptance tests pass.
- Phase 1 — Human parity: the locked independent evaluation beats or matches the best reproducible named baseline at the stated target with uncertainty.
- Phase 2 — Defensible IP: prospective superiority repeats independently, owned provenance and ablations freeze, and patent-versus-trade-secret review is documented. Counsel separately determines FTO.

Focused acceptance command: `cargo test --workspace --locked`. The native demo and replay commands in `AMPHORA_RUST.md` are the portfolio acceptance path.

External dependency or delay:

- Independent validation receipts bound to frozen model and dataset hashes

Estimated effort is represented by the checked-in 0–5 priority factors, not a fabricated schedule. Schema drift, source mutation, incomplete folds, non-finite output, authority escalation, or lost claim locks automatically demote the module.

## Red-team dossier

Regression coverage must exercise malformed chemistry; mixtures, fragments, and polymers; unsupported formats; unit ambiguity; zero-mass ingredients; NaN and Infinity; out-of-domain inputs; group/source/time leakage; mutated sources; computed-as-measured records; spoofed identity; authority escalation; stripped or unknown claim locks; fixed-seed replay drift; and legal, regulatory, supplier, procurement, qualification, or release overclaim. Every such case must fail closed or remain an explicit evidence gap.

Module-focused checked fixture: `amphora-engine/src/lib.rs` via `cargo test --workspace --locked`. Scenario: Validate the checked model-card authority fixture and its fail-closed envelope fields.
