---
{"audit_date":"2026-07-17","authority_ceiling":"EVIDENCE_ONLY","candidate_types":["evidence_package"],"capability_profile":"capability-profile.json","consumers":[],"dependencies":["amphora-candidate-contract","amphora-redteam-audit"],"evidence_inventory":"../../config/module-evidence-inventory.json","lane":"infrastructure","module_id":"amphora-report-packager","operational_readiness":"COMPLETE","phase":"PHASE_0","schema":"amphora.module-mission.v1","scientific_readiness":"NOT_APPLICABLE","solver_use_ceiling":"DISABLED"}
---

# amphora-report-packager mission

## Decision and falsifiable hypothesis

This module supports the decision of whether validated envelopes can be packaged without stripping locks or escalating claims. Its falsifiable hypothesis is that downstream packaging preserves every authority and claim-lock field.

It does not establish product qualification, batch release, procurement approval, legal freedom to operate, regulatory compliance, supplier closure, or wet-lab performance. Phase 2, if later earned, means defensible R&D technical IP only.

## Honest current state

The live checked implementation is native Rust at `amphora-assurance-capabilities/src/lib.rs` with SHA-256 `0fe122cc7434bdad38fc90a812c2c2fc10d431b0ba30fbac179a8bcef0c84f7d`. Runtime registration is owned by `amphora-engine/src/lib.rs` and is checked against `module-manifest.json`. Retired Python implementation records have diagnostic provenance only and are not live authority.

Focused checked test evidence:

- `amphora-assurance-capabilities/src/lib.rs` — SHA-256 `0fe122cc7434bdad38fc90a812c2c2fc10d431b0ba30fbac179a8bcef0c84f7d`
- `amphora-assurance-capabilities/src/diagnostics.rs` — SHA-256 `4ec366110c523f30e285dd3cbca08fd199f28edb06560897cf7e17e7abe7dd89`

Operational state is `READY`; scientific state is `UNVALIDATED`, so the current phase is **Pre-Phase 0**. Execution and passing unit tests do not establish human parity. No readiness percentage is asserted.

### Checked datasets and artifacts

- `output_artifact` `amphora-report-packager/reference/mvp20/out/CUSTOMER_FACING.tex` — SHA-256 `ba69a64ca49fc5973faea36c0cbcbc6ea89fca60b73d3556758f4882cad83b71`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `output_artifact` `amphora-report-packager/reference/mvp20/out/FOUNDER_FACING.tex` — SHA-256 `d0517f12e93ffec1a8ebac67fb5040bd6c70627e57738b4f6fbb8448e10b6742`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `output_artifact` `amphora-report-packager/reference/mvp20/out/blueprint.md` — SHA-256 `b3db17345245812b4b186433e56f9bb86fc04e28d47f3d121d4036d5dc9cc879`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `output_artifact` `amphora-report-packager/reference/mvp20/out/f718_style_datasheet.md` — SHA-256 `0c34557390f7cf8f38e5bc375646ce325c53c0451a14ef52b9b1c8934291795b`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)

Rights are reported per file; local presence is not evidence of ownership or permission. Artifact presence and a matching hash do not establish dataset rights, scientific validity, or ownership. All listed artifact rights remain `UNRESOLVED` because no SHA-bound rights receipt was found.

### Current benchmark result

Phase-0 known-answer harness at
`amphora-assurance-capabilities/tests/report_packager_phase0_kpi.rs`
drives `evaluate_report_packager` across 5 evidence_package candidates
plus 3 fail-closed probes on unsupported inputs. Runtime counts 4
compile-time-embedded REPORT_ARTIFACTS (CUSTOMER_FACING.tex,
FOUNDER_FACING.tex, blueprint.md, f718_style_datasheet.md) and honestly
returns INSUFFICIENT_INPUT with all 4 gates pinned false because signed
score envelopes and a deterministic report package are not yet
available. Byte-stable receipt at
`evidence/phase0/benchmark/result.v1.json` (SHA-256
`fc797aac97caa75ce25fba2f3c7b00742c7b3a601647982284c223121f0fc6e1`).
Phase-0 KPI receipt at
`evidence/phase0/kpis/report-packager-signed-deliverable-quarantine-kpi.v1.json`.

All 12 deterministic gates + 1 observational at floor 1.0. Theory:
IEEE 830-1998 SRS; ISO/IEC 26514:2022 documentation lifecycle; IEEE
15288-2015 systems engineering; FTC 16 CFR Part 260 Green Guides; FDA
21 CFR Part 801 labeling; SLSA v1.0 producer/verifier separation;
in-toto Attestation v1.0; The Turing Way reproducibility; PRISMA 2020;
Anderson 1980 reference-monitor.

### Phase-0 readiness

All Phase-0 deterministic gates in
`evidence/phase0/promotion/policy.v1.json` passing. Awaiting
`PHASE0_EVALUATOR` and `PHASE0_INTERNAL_REVIEWER` signatures.
Front-matter preserved.

### Known contradictions

- Packaging valid envelopes cannot upgrade their claim locks, evidence tier, legal status, or product authority.
- 2026-08-15 report-fixture-title-overclaim-v1 (AUDIT_ONLY, evidence/audit/report-fixture-title-overclaim-v1/): the known-answer fixture acceptance control report_fixture_accepted (diagnostics.rs) scans narrative for banned regulatory/qualification overclaim text but never scans title, though render_report emits title verbatim as the rendered document heading. A self-signed known-answer fixture with a banned claim only in title is returned ACCEPT. Fix (Phase-1 material): also lint title; also pin the fixture-signing key per render-claim-lock-preservation-v1's existing unpinned-key finding.
- 2026-08-17 report-fixture-narrative-zerowidth-lint-evasion-v1 (AUDIT_ONLY, evidence/audit/report-fixture-narrative-zerowidth-lint-evasion-v1/): normalize_claim (diagnostics.rs) maps invisible Unicode Cf format characters (ZERO WIDTH SPACE/NON-JOINER/JOINER) to spaces without NFKC stripping them first, so inserting one such character inside a single-word token of a banned phrase (e.g. procurement, patentable, qualified) inside payload.narrative -- the field the lint DOES scan -- splits the token and defeats the substring check. Verified on 3 independent phrases/characters, all ACCEPT; the identical phrases minus the invisible character ARE caught (isolates the mechanism). Distinct from the title field-coverage gap above and from T-12's homoglyph-substitution vector. Fix (Phase-1 material): strip Unicode Cf format characters before the alphanumeric sweep in normalize_claim.
- 2026-08-19 report-fixture-narrative-cross-line-phrase-split-v1 (AUDIT_ONLY, evidence/audit/report-fixture-narrative-cross-line-phrase-split-v1/): report_fixture_accepted checks contains_banned_claim PER ELEMENT of payload.narrative (`.any(|line| ...)`), never over the joined or rendered text; render_report concatenates narrative elements in order with no paragraph separator. Splitting any banned two-word phrase across the boundary between two consecutive narrative elements (first word ends element N, second word begins element N+1) means neither element alone contains the phrase, so the lint never fires, while the rendered document shows the two lines immediately adjacent, reading as one continuous overclaim. Pure ASCII, no Unicode tricks. Verified on 3 independent banned phrases, all ACCEPT; the identical phrase on a single unsplit line IS caught (isolates the mechanism). Distinct from the title field-coverage gap, from T-12's homoglyph-substitution vector, and from the zerowidth intra-line Cf-character vector above. Fix (Phase-1 material): run contains_banned_claim over the whole joined narrative / rendered_document text in addition to per-line.

Across the portfolio, the emitted envelope, adapter, manifest, model receipt/card, portfolio policy, and Rust ranking boundary must all agree. The most restrictive policy controls.

## Inputs, outputs, and normalization

Current accepted format: canonical CandidateEnvelope JSON. The current runtime supports JSON plus molecule SMILES only through the central candidate contract. Target interface: canonical CandidateEnvelope JSON. That target interface is already the runtime interface for this module. Unsupported formats fail closed.

External chemistry normalizes once in `amphora-candidate-contract`; this module consumes canonical `CandidateEnvelope` data. Original bytes, normalized structure/formula, toolkit/version, stereochemistry, isotope, charge, fragment, mixture, polymer, and commercial-grade policies are retained in the capability profile.

Canonical input is a finite `evidence_package` `CandidateEnvelope` whose payload matches `candidate_type`. Canonical output is `ScoreEnvelope`; the primary value path is `gates.authority_lock_present`. Units, direction, nullability, authority, uncertainty, and claim locks are explicit in the profile and envelope. A null or blocked value cannot be converted to an objective.

## Canonical current examples and typed paths

```json
{"candidate_id": "amphora-report-packager-example", "candidate_type": "evidence_package", "evidence_refs": {"evidence_package": {}}}
```

The schema-valid fail-closed output example is checked in at `docs/capability-profile.json#/examples/current_output`. Exact paths are: objective `None`, metric `gates.authority_lock_present`, gate `gates`, uncertainty `uncertainty`, evidence gaps `missing_inputs`, and claim locks `claim_locks`. Nullability is explicit; empirical units and direction come only from the locked benchmark receipt. The authority ceiling is `EVIDENCE_ONLY` and solver-use ceiling is `DISABLED`.

## Data, theory, model, and uncertainty strategy

Applicability domain is solvent-borne two-component epoxy-polyamide marine-coating R&D and the explicitly declared candidate types. Missing values are not imputed across an authority boundary. Empirical work uses group, family, source, and time-safe splits; computed values remain labeled computed; candidate evidence remains separate from public context. Subgroup reporting and calibrated intervals are required wherever the locked KPI is empirical. Named standard, expert/CRO, primary-literature, simple physical, and hostile-null baselines precede promotion.

## KPI register and promotion gates

Primary KPI: **claim-lock preservation** at `gates.authority_lock_present`. Direction and unit are declared by the locked benchmark; population is the declared applicability domain; split is group/time/source-safe; confidence intervals are mandatory for empirical claims. Locked target: Zero silent acceptance of malformed, unsupported, or unauthorized inputs before Phase 0; locked module-specific benchmark required for Phase 1.

- Phase 0 — Useful: deterministic or evidence-bound capability, contract parity, fail-closed malformed/OOD behavior, no unresolved authority contradiction, and the module acceptance tests pass.
- Phase 1 — Human parity: the locked independent evaluation beats or matches the best reproducible named baseline at the stated target with uncertainty.
- Phase 2 — Defensible IP: prospective superiority repeats independently, owned provenance and ablations freeze, and patent-versus-trade-secret review is documented. Counsel separately determines FTO.

Focused acceptance command: `cargo test --workspace --locked`. The native demo and replay commands in `AMPHORA_RUST.md` are the portfolio acceptance path.

External dependency or delay:

- Approved audience-specific claim policy and independently accepted input envelopes

Estimated effort is represented by the checked-in 0–5 priority factors, not a fabricated schedule. Schema drift, source mutation, incomplete folds, non-finite output, authority escalation, or lost claim locks automatically demote the module.

## Red-team dossier

Regression coverage must exercise malformed chemistry; mixtures, fragments, and polymers; unsupported formats; unit ambiguity; zero-mass ingredients; NaN and Infinity; out-of-domain inputs; group/source/time leakage; mutated sources; computed-as-measured records; spoofed identity; authority escalation; stripped or unknown claim locks; fixed-seed replay drift; and legal, regulatory, supplier, procurement, qualification, or release overclaim. Every such case must fail closed or remain an explicit evidence gap.

Module-focused checked fixture: `amphora-assurance-capabilities/src/lib.rs` via `cargo test --workspace --locked`. Scenario: Reject empty or malformed artifact lists and claim-lock stripping.
