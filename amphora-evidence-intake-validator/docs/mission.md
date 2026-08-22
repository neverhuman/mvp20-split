---
{"audit_date":"2026-07-17","authority_ceiling":"EVIDENCE_ONLY","candidate_types":["evidence_package"],"capability_profile":"capability-profile.json","consumers":[],"dependencies":["amphora-candidate-contract","amphora-source-ledger"],"evidence_inventory":"../../config/module-evidence-inventory.json","lane":"infrastructure","module_id":"amphora-evidence-intake-validator","operational_readiness":"COMPLETE","phase":"PHASE_0","schema":"amphora.module-mission.v1","scientific_readiness":"NOT_APPLICABLE","solver_use_ceiling":"DISABLED"}
---

# amphora-evidence-intake-validator mission

## Decision and falsifiable hypothesis

This module supports the decision of whether observed evidence bytes may enter the accepted evidence store. Its falsifiable hypothesis is that byte hashing and manifest binding reject missing, mutated, unsigned, or overclaiming packages.

It does not establish product qualification, batch release, procurement approval, legal freedom to operate, regulatory compliance, supplier closure, or wet-lab performance. Phase 2, if later earned, means defensible R&D technical IP only.

## Honest current state

The live checked implementation is native Rust at `amphora-assurance-capabilities/src/lib.rs` with SHA-256 `c0b2540fa84a9b8c98d2be5d82cbb1d21e9fd8b9806edad23815a0d912f4ab4d`. Runtime registration is owned by `amphora-engine/src/lib.rs` and is checked against `module-manifest.json`. Retired Python implementation records have diagnostic provenance only and are not live authority.

Focused checked test evidence:

- `amphora-assurance-capabilities/src/lib.rs` — SHA-256 `c0b2540fa84a9b8c98d2be5d82cbb1d21e9fd8b9806edad23815a0d912f4ab4d`
- `amphora-assurance-capabilities/src/diagnostics.rs` — SHA-256 `bab349d7039ab3d323c3313f3edc6680932278842d6e0512d9d929dbccaf987a`

Operational state is `COMPLETE`; scientific state is `UNVALIDATED`, so the current phase is **Pre-Phase 0**. Execution and passing unit tests do not establish human parity. No readiness percentage is asserted.

### Checked datasets and artifacts

- `output_artifact` `amphora-evidence-intake-validator/reference/mvp20/out/v5_evidence_intake_validator.json` — SHA-256 `169ec39a3038d726d8c5b5263e7abd2b5ad7c28c0501490edd66848fb1167a46`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `output_artifact` `amphora-evidence-intake-validator/reference/mvp20/out/v5_non_candidate_fixture_packages.json` — SHA-256 `64a9d98a23fce4531254acff7b4cd981413760c7c0cfad15bf4155ff1d011ce8`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `output_artifact` `amphora-evidence-intake-validator/reference/mvp20/out/v5_validator_dry_run_results.json` — SHA-256 `5a30d78b583b615f101a60b19cf072343221f524f7d07485fd9c2917ca0f6aba`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)

Rights are reported per file; local presence is not evidence of ownership or permission. Artifact presence and a matching hash do not establish dataset rights, scientific validity, or ownership. All listed artifact rights remain `UNRESOLVED` because no SHA-bound rights receipt was found.

### Current benchmark result

Phase-0 known-answer harness at
`amphora-assurance-capabilities/tests/evidence_intake_validator_phase0_kpi.rs`
drives the deterministic `evaluate_evidence_intake` runtime via
`AssuranceCapability::new("amphora-evidence-intake-validator")` across
3 positive scenarios (baseline primer lab measurement, topcoat DFT
measurement, adhesive pull-off strength) with properly-constructed
11-field host-verified Ed25519 receipts, plus 14 adversarial mutation
probes each targeting exactly one receipt integrity condition (missing
feature, wrong schema, accepted/signature_verified/revocation_checked/
fresh flipped, wrong algorithm ES256, trust_store_status=UNTRUSTED,
wrong candidate_id, wrong candidate_contract_hash_v1, wrong
package_sha256, empty verifier_id, extra 12th field, missing required
field), plus 3 fail-closed probes on unsupported inputs. Byte-stable
receipt at `evidence/phase0/benchmark/result.v1.json` (SHA-256
`00dbbe9f58921b7dcc65afaa39b7f09a03e6b9647b9c17ed9342a8dca62b9738`).
Phase-0 KPI receipt at
`evidence/phase0/kpis/evidence-intake-validator-host-receipt-integrity-kpi.v1.json`.

All 9 deterministic gates + 1 observational at floor 1.0: positive
scenarios all return SCORED with score=1.0 and both output gates true;
all 14 receipt-mutation probes return FAILED_GATES with score=0.0 and
both gates false; wrong candidate_type / unknown module_id /
whitespace module_id fail closed via CapabilityError.

Theory: NIST SP 800-53 Rev. 5 SI-7 (2020); NIST FIPS 186-5 EdDSA
(2023); RFC 8032 Ed25519 (2017); RFC 5280 PKIX (2008); in-toto
Attestation v1.0 (2020); SLSA v1.0 (2023); NIST SP 800-207 Zero Trust
(2020); Anderson 1980 reference-monitor.

### Phase-0 readiness

All Phase-0 deterministic gates in
`evidence/phase0/promotion/policy.v1.json` (RIGHTS for in-Rust scenario
construction, LOCKED_SPLIT, LOCKED_BENCHMARK, TWO_REPLAYS, RED_TEAM
across 23 axes plus 14 dedicated receipt-mutation probes, CLAIM_LOCKS,
FOLDER_CONFINEMENT, BENCHMARK_EXECUTION_COMPLETE, MODULE_INVARIANTS)
passing. Awaiting `PHASE0_EVALUATOR` and `PHASE0_INTERNAL_REVIEWER`
signatures. Front-matter preserved.

### Known contradictions

- Synthetic rejection fixtures test intake behavior; accepted intake cannot by itself create scientific, legal, supplier, or procurement authority.
- V1-REAL-EIV (2026-08-04, `evidence/phase0/repairs/V1-REAL-EIV/done/v1-real-eiv-superseding-kpi.v1.dsse.json`): the shipped 1.0 positive_scenarios_scored_rate does NOT generalize to the module's own real in-tree DSSE corpus. On n=66 real manifest-indexed receipts, an honestly-implemented host (real Ed25519 verification + real trust-store lookup instead of an asserted-true FeatureSnapshot) measures positive_scenarios_scored_rate=0.0, because all 66 are signed by a single toolkit-reviewer identity absent from `config/phase0-trust-store.v1.json`. On n=9 real known-defective receipts (R-A11/R-A12 classes) the predicate correctly returns FAILED_GATES 9/9, but for the same trust-anchoring reason it rejects genuine evidence, not because it distinguishes good from bad real evidence. See RETRACTION-INDEX.md.

- T-04 (2026-08-05, `evidence/phase0/repairs/T-04/done/t04-adversarial-forgery-done.v1.dsse.json`): FIRST ADVERSARIAL VERDICT for this module -- CLAIM_REFUTED. 12 real-DSSE/real-Ed25519 cases run through the live native `evaluate_evidence_intake`/`host_receipt_valid` AND the live native `amphora_core::verify_dsse` (the real verifier already used by the sibling CroProtocolPackage capability in the same source file) side by side. All 5 named forgery classes (re-signed-with-wrong-key, truncated-keyid, payload/signature mismatch, valid-envelope-tampered-payload, cross-module replay) and 3 of the founder T2-04 directive's 4 categories (non-anchored dev key, stale/revoked, rights-unresolved/quarantined) were ADMITTED by the shipped predicate despite `verify_dsse` correctly rejecting every corresponding forged envelope. Only the hash-mismatch-to-artifact category is genuinely blocked (positive control), and 4/4 valid-but-unusual DSSE envelopes (multi-signature, unknown payloadType, nested envelope, large payload) were correctly accepted, so the module is not simply fail-closed-by-accident -- the specific defect is that `host_receipt_valid` never calls any signature, trust-store, or revocation check of its own. See RETRACTION-INDEX.md.

- W-T-EIV (2026-08-13, `evidence/phase0/repairs/W-T-EIV/done/w-t-eiv-dsse-spec-conformance-done-receipt.v1.dsse.json`): FIRST NAMED-PUBLISHED-BASELINE VERDICT for this module -- CLAIM_REFUTED. 11 normative requirements enumerated from the DSSE specification (secure-systems-lab/dsse, Version 1.0.2, 2024-05-10, https://github.com/secure-systems-lab/dsse) -- covering the envelope JSON schema (payload/payloadType/signatures, keyid optionality, sig requirement, multi-signature array support) and the PAE (Pre-Authentication Encoding) construction and verification procedure -- tested mechanically against the live `evaluate_evidence_intake`/`host_receipt_valid`. Result: 0/11 conformant, 8/11 divergent, 3/11 not_applicable. The live 11-field receipt schema carries no `payload`, `payloadType`, or `signatures` field, the predicate performs zero PAE computation, and it never calls any signature/trust-store/revocation primitive of its own (0 calls to `verify_dsse`/`sign_dsse` in the evidence-intake region, vs. 1 call each elsewhere in the same file by the sibling CroProtocolPackage capability, which IS structurally DSSE-conformant). Gives a spec-named structural cause for T-04's prior behavioral finding. Neither half of the audited claim ("conforms to DSSE" / "divergence is deliberate and stated") survives: this module's docs had never named the DSSE spec as a baseline this receipt format diverges from. See RETRACTION-INDEX.md is not applicable here (no prior number superseded); see the receipt's `proposed_followups[]` for the 8 filed repair candidates.

- from-value-strict-parse-bypass-v1 (2026-08-15, `evidence/audit/from-value-strict-parse-bypass-v1/from-value-strict-parse-bypass-receipt.v1.dsse.json`): STRUCTURAL/ENTRY-POINT VERDICT -- CLAIM_REFUTED. `CandidateEnvelope::from_value` (the constructor the real scoring entrypoint `amphora-engine::execute()` uses exclusively, never `from_bytes`/`parse_json_strict`) applies none of the strict parser's duplicate-key rejection, `MAX_JSON_DEPTH`, or `MAX_COLLECTION_ENTRIES` checks. A live end-to-end probe shows the real predicate SCOREs a 104-deep and a 150000-entry evidence package that `from_bytes` correctly rejects. `mission.md`'s "Unsupported formats fail closed" does not hold for the module's real scoring entrypoint. amphora-cli's own `read_json()` happens to pre-filter via `parse_json_strict` today, so this is an architectural/latent gap in `from_value` itself, not a demonstrated CLI-level intrusion.

- production-feature-gap-v1 (2026-08-17, `evidence/audit/production-feature-gap-v1/production-feature-gap-receipt.v1.dsse.json`): PRODUCTION-WIRING VERDICT -- CLAIM_REFUTED. A live end-to-end probe plus a repo-wide static grep (re-run at signing time) show that `amphora-engine::execute()` (the ONLY non-test code in the repository that ever builds the `FeatureSnapshot` passed into a real scoring call) never inserts the `evidence_intake.host_verified_receipt` feature key that `host_receipt_valid` requires to ever return `verified=true`, for any candidate type, unconditionally. Every insertion of that key repo-wide is inside a `#[test]` fn or a test/audit-probe file. A maximally honest, correctly-bound receipt for a legitimate evidence package is REJECTED (FAILED_GATES, score 0.0) under the feature set production code actually builds, and ACCEPTED (SCORED, score 1.0) only when hand-inserted the way every prior test/audit harness -- but no production code -- does it. As currently wired, this module's accept branch is unconditionally unreachable by the real engine: it cannot enter ANY evidence into the accepted evidence store, honest or forged, contradicting the `operational_readiness: COMPLETE` front-matter and the "may enter the accepted evidence store" decision this document claims the module makes.

Across the portfolio, the emitted envelope, adapter, manifest, model receipt/card, portfolio policy, and Rust ranking boundary must all agree. The most restrictive policy controls.

## Inputs, outputs, and normalization

Current accepted format: canonical CandidateEnvelope JSON. The current runtime supports JSON plus molecule SMILES only through the central candidate contract. Target interface: canonical CandidateEnvelope JSON. That target interface is already the runtime interface for this module. Unsupported formats fail closed.

External chemistry normalizes once in `amphora-candidate-contract`; this module consumes canonical `CandidateEnvelope` data. Original bytes, normalized structure/formula, toolkit/version, stereochemistry, isotope, charge, fragment, mixture, polymer, and commercial-grade policies are retained in the capability profile.

Canonical input is a finite `evidence_package` `CandidateEnvelope` whose payload matches `candidate_type`. Canonical output is `ScoreEnvelope`; the primary value path is `gates.evidence_package_accepted`. Units, direction, nullability, authority, uncertainty, and claim locks are explicit in the profile and envelope. A null or blocked value cannot be converted to an objective.

## Canonical current examples and typed paths

```json
{"candidate_id": "amphora-evidence-intake-validator-example", "candidate_type": "evidence_package", "evidence_refs": {"evidence_package": {}}}
```

The schema-valid fail-closed output example is checked in at `docs/capability-profile.json#/examples/current_output`. Exact paths are: objective `None`, metric `gates.evidence_package_accepted`, gate `gates`, uncertainty `uncertainty`, evidence gaps `missing_inputs`, and claim locks `claim_locks`. Nullability is explicit; empirical units and direction come only from the locked benchmark receipt. The authority ceiling is `EVIDENCE_ONLY` and solver-use ceiling is `DISABLED`.

## Data, theory, model, and uncertainty strategy

Applicability domain is solvent-borne two-component epoxy-polyamide marine-coating R&D and the explicitly declared candidate types. Missing values are not imputed across an authority boundary. Empirical work uses group, family, source, and time-safe splits; computed values remain labeled computed; candidate evidence remains separate from public context. Subgroup reporting and calibrated intervals are required wherever the locked KPI is empirical. Named standard, expert/CRO, primary-literature, simple physical, and hostile-null baselines precede promotion.

## KPI register and promotion gates

Primary KPI: **malformed package rejection** at `gates.evidence_package_accepted`. Direction and unit are declared by the locked benchmark; population is the declared applicability domain; split is group/time/source-safe; confidence intervals are mandatory for empirical claims. Locked target: Zero silent acceptance of malformed, unsupported, or unauthorized inputs before Phase 0; locked module-specific benchmark required for Phase 1.

- Phase 0 — Useful: deterministic or evidence-bound capability, contract parity, fail-closed malformed/OOD behavior, no unresolved authority contradiction, and the module acceptance tests pass.
- Phase 1 — Human parity: the locked independent evaluation beats or matches the best reproducible named baseline at the stated target with uncertainty.
- Phase 2 — Defensible IP: prospective superiority repeats independently, owned provenance and ablations freeze, and patent-versus-trade-secret review is documented. Counsel separately determines FTO.

Focused acceptance command: `rtk cargo test --workspace --locked`. The native demo and replay commands in `AMPHORA_RUST.md` are the portfolio acceptance path.

External dependency or delay:

- Issuer-bound cryptographic or independently verifiable evidence receipts

Estimated effort is represented by the checked-in 0–5 priority factors, not a fabricated schedule. Schema drift, source mutation, incomplete folds, non-finite output, authority escalation, or lost claim locks automatically demote the module.

## Red-team dossier

Regression coverage must exercise malformed chemistry; mixtures, fragments, and polymers; unsupported formats; unit ambiguity; zero-mass ingredients; NaN and Infinity; out-of-domain inputs; group/source/time leakage; mutated sources; computed-as-measured records; spoofed identity; authority escalation; stripped or unknown claim locks; fixed-seed replay drift; and legal, regulatory, supplier, procurement, qualification, or release overclaim. Every such case must fail closed or remain an explicit evidence gap.

Module-focused checked fixture: `amphora-assurance-capabilities/src/lib.rs` via `rtk cargo test --workspace --locked`. Scenario: Reject nonexistent files and duplicate resolution of one manifest entry.
