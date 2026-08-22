---
{"audit_date":"2026-07-17","authority_ceiling":"EVIDENCE_ONLY","candidate_types":["molecule","formulation","evidence_package"],"capability_profile":"capability-profile.json","consumers":["amphora-barrier-corrosion-score","amphora-cro-protocol-packager","amphora-cure-potlife-gate","amphora-design-rule-score","amphora-envelope-gates","amphora-evidence-intake-validator","amphora-formulation-arithmetic","amphora-formulation-universe","amphora-ingredient-library","amphora-ip-fto-guard","amphora-known-answer-benchmarks","amphora-model-card-authority","amphora-molecule-design-gate","amphora-molecule-generator","amphora-molecule-novelty","amphora-molecule-property","amphora-molecule-role-ranker","amphora-optimizer-orchestrator","amphora-process-qc-twin","amphora-public-corrosion-benchmark","amphora-redteam-audit","amphora-report-packager","amphora-run-provenance","amphora-solvency-score","amphora-source-ledger","amphora-sourceability-ehs","amphora-tolerance-robustness","amphora-viscosity-score"],"dependencies":[],"evidence_inventory":"../../config/module-evidence-inventory.json","lane":"infrastructure","module_id":"amphora-candidate-contract","operational_readiness":"COMPLETE","phase":"PHASE_0","schema":"amphora.module-mission.v1","scientific_readiness":"NOT_APPLICABLE","solver_use_ceiling":"DISABLED"}
---

# amphora-candidate-contract mission

## Decision and falsifiable hypothesis

This module supports the decision of whether candidate and score messages are canonical and safe to dispatch. Its falsifiable hypothesis is that runtime and JSON Schema accept and reject the same finite typed corpus.

It does not establish product qualification, batch release, procurement approval, legal freedom to operate, regulatory compliance, supplier closure, or wet-lab performance. Phase 2, if later earned, means defensible R&D technical IP only.

## Honest current state

The live checked implementation is native Rust at `amphora-engine/src/lib.rs` with SHA-256 `6b007d7d9d0acd453aac5e7c300ab16fb9a7253337c722cc4cffe0be23db62b4`. Runtime registration is owned by `amphora-engine/src/lib.rs` and is checked against `module-manifest.json`. Retired Python implementation records have diagnostic provenance only and are not live authority.

Focused checked test evidence:

- `amphora-engine/src/lib.rs` — SHA-256 `6b007d7d9d0acd453aac5e7c300ab16fb9a7253337c722cc4cffe0be23db62b4`

Operational state is `COMPLETE`; scientific state is `UNVALIDATED`, so the current phase is **Pre-Phase 0**. Execution and passing unit tests do not establish human parity. No readiness percentage is asserted.

### Checked datasets and artifacts

- `input_fixture` `amphora-candidate-contract/fixtures/canonical_formulation_candidate.json` — SHA-256 `8be98d9ed927346fb23b6abd030528a202fa87621c1ecc3ebbc5b149e87ee0f8`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `input_fixture` `amphora-candidate-contract/fixtures/evidence_package_candidate.json` — SHA-256 `da26a9f8c7c59cbc4eb47f099db22808bb83dd804161005d2aefc3323f61f5fb`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `input_fixture` `amphora-candidate-contract/fixtures/formulation_candidate.json` — SHA-256 `de617b7311530cb2d6701860daba9db9b37a0ea0d0733ed4e969b8db617f614f`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `input_fixture` `amphora-candidate-contract/fixtures/molecule_candidate.json` — SHA-256 `9cee73f4158c404a09f969ab1bd710f8174ef9ef59fc01ac41cec267a5c6ed5f`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `input_fixture` `amphora-candidate-contract/fixtures/score_artifact_only_evidence.json` — SHA-256 `2781f8179a5115b209e1da6d40c21c7affd7ac9ee49dc76ded40fc2fd2e11fd7`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `input_fixture` `amphora-candidate-contract/fixtures/score_failed_gate.json` — SHA-256 `4486661e9f0140187226175796ea3a86c7582e73b3021d29a6c3ca7b43546218`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `input_fixture` `amphora-candidate-contract/fixtures/score_formulation_objective.json` — SHA-256 `8e4868f25a86167201eaa39685e6e93c2283669fd058b7b43bf98168518722ef`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `input_fixture` `amphora-candidate-contract/fixtures/score_molecule_objective.json` — SHA-256 `c86ba9daa7d1b62c243bd849aa6b2c52dbf66c1bca323f302115f8ca90a90744`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `input_fixture` `amphora-candidate-contract/fixtures/score_no_authority.json` — SHA-256 `850fac537acb659af8d0463fc2ae3e74bf65dcd8d47b0b36a1e2447725ada20e`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `input_fixture` `amphora-candidate-contract/fixtures/score_roadmap_generated_lead.json` — SHA-256 `cc438c0821e98f57929512f515365751ef52b0b7ac6e8813bb83fdabe337c48b`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)

Rights are reported per file; local presence is not evidence of ownership or permission. Artifact presence and a matching hash do not establish dataset rights, scientific validity, or ownership. All listed artifact rights remain `UNRESOLVED` because no SHA-bound rights receipt was found.

### Current benchmark result

Phase-0 known-answer harness at
`amphora-core/tests/candidate_contract_phase0_kpi.rs` drives
`CandidateEnvelope::from_bytes` and `from_value` across 3 positive
scenarios (molecule CCl4, epoxy-polyamide primer, evidence_package) and
18 adversarial probes: 2 CandidateNotObject, 3 InvalidCandidateId, 2
InvalidCandidateType, 3 PayloadMismatch (missing molecule/formulation/
evidence_refs), 1 PayloadMismatch (chemistry_v2 field without opt-in),
1 ChemistryNormalizationUnavailable, 1 RequestTooLarge (>8 MiB), 1
InvalidUtf8, 5 InvalidJson (trailing comma, duplicate keys, NaN,
Infinity, 100-level nesting depth-exhaustion). Byte-stable receipt at
`evidence/phase0/benchmark/result.v1.json` (SHA-256
`e7d8c3ee72c24b406685a475a6729218bde1b8a878f6b28251d82528b8642fbf`).
Phase-0 KPI receipt at
`evidence/phase0/kpis/candidate-contract-strict-json-integrity-kpi.v1.json`.

All 8 deterministic gates + 1 observational at floor 1.0. All 18
adversarial probes fail closed with the exact expected ContractError
variant. Positive scenarios: candidate_id + candidate_type match input
bit-exact; original_bytes_sha256 equals independently-computed SHA-256
of input bytes; contract_hash_v1 stable across two from_bytes
constructions and agrees with from_value (a bespoke canonical-JSON
invariant -- self-consistent, NOT verified to match RFC 8785 JCS; see
correction below).

CORRECTION (W-T-CONTRACT, 2026-08-13): the "RFC 8785 JCS canonical
invariant" characterization of contract_hash_v1 above was FALSE and is
retracted -- see RETRACTION-INDEX.md. `CandidateEnvelope::contract_hash_v1`
is computed via `amphora-core::stable_hash` -> `canonicalize()`
(amphora-core/src/lib.rs), a bespoke scheme that sorts object keys by
Rust's default code-point string order, NOT RFC 8785 section 3.2.3's
required UTF-16-code-unit order, and does not canonicalize negative zero
to "0" per RFC 8785/ECMAScript Number::toString. A real, independently
RFC-8785-conformance-tested implementation already exists unused in the
same crate at `amphora-core/src/jcs.rs` (`jcs_bytes`/`jcs_sha256`, backed
by `serde_jcs`). Live-reproduced divergence:
`evidence/phase0/repairs/W-T-CONTRACT/done/`. contract_hash_v1's
byte-stability across replays (RFC 8259/8785 grammar conformance of the
*input*, and self-consistency of the *output*) remains true and
load-bearing for the portfolio's two-replay gates; only the RFC-8785
attribution for *why* it is stable was wrong.

Theory: RFC 8259 JSON grammar; RFC 8785 JCS canonicalization (see
correction above -- contract_hash_v1 does not conform); OWASP
A08:2021 Software/Data Integrity Failures; OWASP JSON parser safety
guidance (2020); IEEE 754-2019 non-finite semantics; CWE-121/400
depth+size exhaustion mitigation; NIST FIPS 180-4 SHA-256; Salzer 1975
complete-mediation; Anderson 1980 reference-monitor.

### Phase-0 readiness

All Phase-0 deterministic gates in
`evidence/phase0/promotion/policy.v1.json` passing. Awaiting
`PHASE0_EVALUATOR` and `PHASE0_INTERNAL_REVIEWER` signatures.
Front-matter preserved.

### Known contradictions

- Runtime support is JSON CandidateEnvelope plus molecule SMILES; InChI, MOL, SDF, and recipe CSV remain target contracts rather than implemented parsers.
- `schemas/candidate-envelope.schema.json` (JSON Schema draft 2020-12) alone is NOT a safe substitute for the Rust runtime front door: the signed `evidence/audit/schema-runtime-parity-v1` receipt (jsonschema==4.26.0, Draft202012Validator) shows the schema-only oracle ACCEPTS 6 classes of input (non-finite numbers, duplicate JSON keys, >8 MiB, >64 nesting depth, >100k collection entries) that the Rust runtime correctly REJECTS, because draft 2020-12 has no vocabulary for lexical/resource-layer constraints on an already-parsed value. Structural (candidate_type/payload) parity is 16/16 CORROBORATED; overall hypothesis is PARTIALLY_REFUTED.

Across the portfolio, the emitted envelope, adapter, manifest, model receipt/card, portfolio policy, and Rust ranking boundary must all agree. The most restrictive policy controls.

## Inputs, outputs, and normalization

Current accepted format: JSON, molecule SMILES. The current runtime supports JSON plus molecule SMILES only through the central candidate contract. Target interface: isomeric SMILES, canonical SMILES, InChI, InChIKey, MOL V2000, MOL V3000, single-record SDF, multi-record SDF, canonical formulation JSON, recipe CSV. Those target adapters are **not runtime features in this phase**. Unsupported formats fail closed.

External chemistry normalizes once in `amphora-candidate-contract`; this module consumes canonical `CandidateEnvelope` data. Original bytes, normalized structure/formula, toolkit/version, stereochemistry, isotope, charge, fragment, mixture, polymer, and commercial-grade policies are retained in the capability profile.

Canonical input is a finite `molecule` `CandidateEnvelope` whose payload matches `candidate_type`. Canonical output is `ScoreEnvelope`; the primary value path is `gates.contract_valid`. Units, direction, nullability, authority, uncertainty, and claim locks are explicit in the profile and envelope. A null or blocked value cannot be converted to an objective.

## Canonical current examples and typed paths

```json
{"candidate_id": "amphora-candidate-contract-example", "candidate_type": "molecule", "molecule": {"role": "resin", "smiles": "CC"}}
```

The schema-valid fail-closed output example is checked in at `docs/capability-profile.json#/examples/current_output`. Exact paths are: objective `None`, metric `gates.contract_valid`, gate `gates`, uncertainty `uncertainty`, evidence gaps `missing_inputs`, and claim locks `claim_locks`. Nullability is explicit; empirical units and direction come only from the locked benchmark receipt. The authority ceiling is `EVIDENCE_ONLY` and solver-use ceiling is `DISABLED`.

## Data, theory, model, and uncertainty strategy

Applicability domain is solvent-borne two-component epoxy-polyamide marine-coating R&D and the explicitly declared candidate types. Missing values are not imputed across an authority boundary. Empirical work uses group, family, source, and time-safe splits; computed values remain labeled computed; candidate evidence remains separate from public context. Subgroup reporting and calibrated intervals are required wherever the locked KPI is empirical. Named standard, expert/CRO, primary-literature, simple physical, and hostile-null baselines precede promotion.

## KPI register and promotion gates

Primary KPI: **schema parity** at `gates.contract_valid`. Direction and unit are declared by the locked benchmark; population is the declared applicability domain; split is group/time/source-safe; confidence intervals are mandatory for empirical claims. Locked target: Zero silent acceptance of malformed, unsupported, or unauthorized inputs before Phase 0; locked module-specific benchmark required for Phase 1.

- Phase 0 — Useful: deterministic or evidence-bound capability, contract parity, fail-closed malformed/OOD behavior, no unresolved authority contradiction, and the module acceptance tests pass.
- Phase 1 — Human parity: the locked independent evaluation beats or matches the best reproducible named baseline at the stated target with uncertainty.
- Phase 2 — Defensible IP: prospective superiority repeats independently, owned provenance and ablations freeze, and patent-versus-trade-secret review is documented. Counsel separately determines FTO.

Focused acceptance command: `rtk cargo test --workspace --locked`. The native demo and replay commands in `AMPHORA_RUST.md` are the portfolio acceptance path.

External dependency or delay:

- Validated chemistry file parsers and locked cross-toolkit normalization vectors

Estimated effort is represented by the checked-in 0–5 priority factors, not a fabricated schedule. Schema drift, source mutation, incomplete folds, non-finite output, authority escalation, or lost claim locks automatically demote the module.

## Red-team dossier

Regression coverage must exercise malformed chemistry; mixtures, fragments, and polymers; unsupported formats; unit ambiguity; zero-mass ingredients; NaN and Infinity; out-of-domain inputs; group/source/time leakage; mutated sources; computed-as-measured records; spoofed identity; authority escalation; stripped or unknown claim locks; fixed-seed replay drift; and legal, regulatory, supplier, procurement, qualification, or release overclaim. Every such case must fail closed or remain an explicit evidence gap.

Module-focused checked fixture: `amphora-engine/src/lib.rs` via `rtk cargo test --workspace --locked`. Scenario: Reject non-finite candidate and score values before serialization.
