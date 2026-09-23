---
{"audit_date":"2026-07-17","authority_ceiling":"REAL_ARITHMETIC","candidate_types":["molecule"],"capability_profile":"capability-profile.json","consumers":[],"dependencies":["amphora-candidate-contract","amphora-source-ledger"],"evidence_inventory":"../../config/module-evidence-inventory.json","lane":"molecule","module_id":"amphora-molecule-design-gate","operational_readiness":"READY","phase":"PHASE_0","schema":"amphora.module-mission.v1","scientific_readiness":"NOT_APPLICABLE","solver_use_ceiling":"CONSTRAINT_ONLY"}
---

# amphora-molecule-design-gate mission

## Decision and falsifiable hypothesis

This module supports the decision of whether a defined molecule passes structural applicability rules. Its falsifiable hypothesis is that explicit-role substructure controls reject malformed and nonreactive candidates.

It does not establish product qualification, batch release, procurement approval, legal freedom to operate, regulatory compliance, supplier closure, or wet-lab performance. Phase 2, if later earned, means defensible R&D technical IP only.

## Honest current state

The live checked implementation is native Rust at `amphora-molecule-capabilities/src/lib.rs` with SHA-256 `258043a42c015587600da417a50170928b57f4f2eb2a0bfcee9b0ac14ada750c`. Runtime registration is owned by `amphora-engine/src/lib.rs` and is checked against `module-manifest.json`. Retired Python implementation records have diagnostic provenance only and are not live authority.

Focused checked test evidence:

- `amphora-molecule-capabilities/src/lib.rs` — SHA-256 `258043a42c015587600da417a50170928b57f4f2eb2a0bfcee9b0ac14ada750c`

Operational state is `READY`; scientific state is `UNVALIDATED`, so the current phase is **Pre-Phase 0**. Execution and passing unit tests do not establish human parity. No readiness percentage is asserted.

### Checked datasets and artifacts

- None discovered. No checked-in dataset, output artifact, or non-README fixture was discovered for this module.

No checked-in dataset, output artifact, or non-README fixture was discovered for this module. Artifact presence and a matching hash do not establish dataset rights, scientific validity, or ownership. All listed artifact rights remain `UNRESOLVED` because no SHA-bound rights receipt was found.

### Current benchmark result

Phase-0 known-answer harness at
`amphora-molecule-capabilities/tests/design_gate_phase0_kpi.rs` drives
the deterministic `design_gate_result` capability across a self-authored
fixture at
`amphora-molecule-design-gate/reference/phase0-design-gate-known-answer.v1.json`
(SHA-256 `45ed29ed699f6c089848d72496f136ef1148497b802a8095ca426ef54392930c`;
CC0-1.0, `eligible_for_derivatives: true`; 42 labelled molecule test
cases: 8 valid resins + 8 valid hardeners + 5 wrong-role + 3 missing-role
+ 4 mismatched-resin + 4 mismatched-hardener + 5 dual-functional
glycidylamines + 5 synthetic malformed lexical cases; every structural
molecule cited via a PubChem CID) and emits a byte-stable canonical
receipt at
`evidence/phase0/benchmark/result.v1.json` (SHA-256
`8873baa3d050984dbf58fadd8d78a12f03c586e436a1c243a268ff0c93945964`).
The Phase-0 KPI receipt lives at
`evidence/phase0/kpis/design-gate-structural-applicability-kpi.v1.json`.

Observed Phase-0 KPI outcomes (all deterministic, `cargo test --workspace --locked`):

- `gate_decision_correctness_rate` observed **1.0** (42/42 cases; 21 expected-pass and 21 expected-fail each matching) — **PASSED** (floor 1.0)
- `gate_reason_attribution_correctness_rate` observed **1.0** (42/42; every one of the six categorical `gate_reason` values exactly matches expected) — **PASSED** (floor 1.0)
- `role_appropriate_reactivity_correctness_rate` observed **1.0** (42/42; `gates["role_appropriate_reactivity"]` agrees with expected under the mechanistic rule "role X iff matching reactive group Y") — **PASSED** (floor 1.0)
- `explicit_role_correctness_rate` observed **1.0** (42/42; `gates["explicit_role"]` correctly true iff role ∈ {resin, hardener}) — **PASSED** (floor 1.0)
- `valid_single_component_correctness_rate` observed **1.0** (42/42; lexical structure_text validity agrees with expected) — **PASSED** (floor 1.0)
- `malformed_structure_fail_closed_rate` observed **1.0** (5/5 malformed probes: empty SMILES, multi-fragment 'CC.O', wildcard '*', wildcard '~', missing structure/role all fail closed with the correct `ObviousStructureIssue` name in `gate_reason`) — **PASSED** (floor 1.0)
- `authority_lock_preservation_rate` observed **1.0** (42/42; `evidence_scope` correctly set per code path, `score_0_1 == None`, `objective_values` empty, `structural_applicability_only == true` on SCORED path) — **PASSED** (floor 1.0)
- `byte_stable_two_replay_rate` observed **1.0** (42/42 back-to-back invocations byte-identical) — reported observationally.

Structural applicability for role X iff the molecule carries reactive
group Y is the mechanistic basis of two-part epoxy-amine cure chemistry
(Wicks/Jones/Pappas 2007 §15.2-15.4; Ellis 1993 §6.2). The runtime
reproduces this admission decision on 42 labelled molecule test cases at
100% correctness including fine-grained categorical `gate_reason`
attribution across six failure modes. Every one of the 23 red-team
attack axes declared in `evidence/phase0/benchmark/benchmark-lock.v1.json`
is exercised end-to-end in the integration test or in the six new
red-team unit tests in `amphora-molecule-capabilities/src/lib.rs`.

### Phase-0 readiness

All Phase-0 deterministic gates in
`evidence/phase0/promotion/policy.v1.json` (`RIGHTS` for the CC0
self-authored labelled-molecule compilation, `LOCKED_SPLIT`,
`LOCKED_BENCHMARK`, `TWO_REPLAYS`, `RED_TEAM` across 23 attack axes,
`CLAIM_LOCKS`, `FOLDER_CONFINEMENT`, `BENCHMARK_EXECUTION_COMPLETE`,
`MODULE_INVARIANTS`) are passing. Awaiting `PHASE0_EVALUATOR` and
`PHASE0_INTERNAL_REVIEWER` signatures per the `evaluation.v1.dsse.json`
and `phase0-review-receipt.v1.json` protocol before the `phase` header
becomes substantively — rather than aspirationally — `PHASE_0`. Until
the signed receipt lands, the module's advertised `phase: PHASE_0` in
the front-matter is a target; this Phase-0 push lands the deterministic
KPI receipt that will make the target substantive at the moment of
signing.

### Known contradictions

- Structural applicability gates do not establish EHS acceptability, synthesis feasibility, qualification, procurement, or performance.
- Before 2026-08-06 this module had never received an adversarial verdict; its `evidence/audit/*` receipts (fact-snapshot-authority-v1, smiles-representation-invariance-v1, rdkit-structural-facts-parity-v1, nitrogen-nucleophilicity-authenticity-v1) are constructive/audit evidence, not falsification attempts. Campaign item T-08 (`evidence/phase0/repairs/T-08/done/t08-design-gate-live-runtime-adversarial-receipt.v1.dsse.json`, DSSE-signed by `PHASE0_EVALUATOR`) is the first adversarial attack: it drove `design_gate_result` through the REAL pinned RDKit C++ FFI (not synthetic/verbatim facts, unlike the prior audit receipts) on 13 held-out real coating molecules including 4 hostile-null accelerators/latent hardeners (BDMA, EMI-24, DPG, DOTG), plus a founder-directive (T2-08) fail-closed attack against wildcard/multi-fragment/invalid-valence inputs and a chemistry-changing mutation/generation-authorization attempt. Verdict: **CLAIM_SURVIVED** — 13/13 gate probes matched expectation, 0 structural slip-throughs, 0 mutation-quarantine violations, 0 unauthorized generation. A positive control (a hand-poisoned facts snapshot fed to the same live gate call) confirmed the attack's own checker fires on a planted defect. The receipt also re-affirms, without reopening, the pre-existing fact-snapshot-authority-v1 finding that `design_gate_result` trusts any schema-conformant `MoleculeFactsV1` snapshot without re-binding it to the candidate's raw structure text — not independently reachable in production because `molecule_facts()` itself refuses wildcard/multi-fragment SMILES before the RDKit backend runs.
- The PHASE-0 BINDING GAP named by the founder directive (front-matter `"phase":"PHASE_0"` vs. this document's own prose stating the current phase is Pre-Phase 0, immediately below) is recorded, not repaired, by T-08; repair needs the human dual-identity Phase-0 promotion ceremony.
- Campaign item W-T-DESIGNGATE (`evidence/phase0/repairs/W-T-DESIGNGATE/done/w-t-designgate-ad-comparator-receipt.v1.dsse.json`, DSSE-signed by `PHASE0_EVALUATOR`) closes the standing theory gap that the module's sole Phase-0 KPI (`design-gate-structural-applicability-kpi.v1.json`) had only ever been measured against its own self-authored 42-record fixture. It enumerates the 5 OECD (2004/2007) normative requirements for (Q)SAR model validation applied to this module (2 conformant: defined endpoint, unambiguous algorithm; 1 conformant on mechanistic grounds; 2 divergent: no published applicability-domain definition and no externally-sourced validation set existed before this fire) and implements a named published applicability-domain comparator (hat-matrix leverage / Williams plot, Gramatica 2007, QSAR & Comb. Sci. 26(5):694-701, DOI 10.1002/qsar.200610151) over the fixture's 37 fact-bearing records plus the 13 T-08 held-out live-RDKit probes. Verdict: **CLAIM_REFUTED** -- 21 of 55 comparison rows (38.2%) diverge between the gate's structural pass/fail decision and the leverage-AD in/out-of-domain flag; every divergence is characterised (accelerator/hostile-null hardener declarations that are numerically in-domain but structurally rejected, and one real held-out hardener (diethyl 2-(butylamino)succinate, an aspartic-ester secondary amine) that the gate SCOREs while leverage-AD flags as an extrapolation risk) and filed to `proposed_followups[]` with a proposed repair criterion each. This does not show the gate is wrong -- the two methods answer different questions (numeric-range similarity vs mechanistic role-appropriateness) -- but it does show the module's 1.0 self-consistency figure is not equivalent to, and had never been checked against, a named published external-validation standard.
- `evidence/audit/steric-shielded-amine-hostile-null-v1/steric-shielded-amine-hostile-null-receipt.v1.dsse.json` (DSSE-signed by `PHASE0_EVALUATOR`, 2026-08-15 ROTATION-mode attack) found a **CLAIM_REFUTED**: the live production `design_gate_result` path, exercised through the REAL pinned RDKit C++ FFI, admits a real, currently-marketed marine-coating additive as a valid stoichiometric hardener. `amphora-rdkit-ffi/src/bridge.cc::count_reactive_amine_hydrogens`'s exclusion clauses (carbonyl/sulfonyl neighbor, amidine/guanidine conjugation, formal charge) are all electronic; none is steric. Tinuvin 770 (BASF, CAS 52829-07-9, bis(2,2,6,6-tetramethyl-4-piperidyl) sebacate -- a Hindered Amine Light Stabilizer sold exclusively as a UV stabilizer, never with a published amine value/AHEW, never marketed as a hardener) and its parent scaffold TEMP (2,2,6,6-tetramethylpiperidine, CAS 768-66-1) both reach `SCORED` with `role_appropriate_reactivity == true` when declared `role: "hardener"`, because their ring N-H is sterically shielded (why this scaffold is instead used to synthesize the TEMPO nitroxide radical: Gugumus 1993, Polym. Degrad. Stab. 40(2):167-215) but formally passes every existing clause. Internal controls confirm specificity: the N-methylated tertiary analog (Tinuvin 292, zero N-H) correctly fails via the pre-existing tertiary-amine exclusion, and unhindered piperidine correctly passes. This is a distinct physical mechanism from, and is not closed by, the prior `nitrogen-nucleophilicity-authenticity-v1` finding's electronic-only 6-clause predicate. Proposed followup `R-DESIGNGATE-STERIC` (steric neighbor-substitution clause in `bridge.cc` + HALS fixture records) is filed, unresolved.
- `evidence/audit/design-gate-oxirane-steric-hostile-null-v1/design-gate-oxirane-steric-hostile-null-receipt.v1.dsse.json` (DSSE-signed by `PHASE0_EVALUATOR`, 2026-08-19 ROTATION-mode attack) found a **CLAIM_REFUTED** on the RESIN side, the mirror image of the hardener-side finding above. `amphora-rdkit-ffi/src/bridge.cc::count_oxirane_rings` carries NO exclusion clause of any kind (electronic or steric) -- it counts any three-membered ring of one degree-2, neutral oxygen singly bonded to two singly-bonded carbons, regardless of substitution. 2,2,3,3-tetramethyloxirane (tetramethylethylene oxide, CAS 5076-20-0, both epoxide carbons quaternary) and 2,2,3-trimethyloxirane (2,3-epoxy-2-methylbutane, CAS 5076-19-7, one epoxide carbon quaternary) both reach `SCORED` with `role_appropriate_reactivity == true` when declared `role: "resin"`, despite neither being sold, classified, or usable as a two-part epoxy-amine coating resin by any supplier -- both are small-molecule synthesis reagents whose fully-substituted epoxide carbons sterically block the backside nucleophilic ring-opening amine cure depends on (Parker & Isaacs, "Mechanisms of Epoxide Reactions," Chem. Rev. 1959, 59(4):737-799, DOI 10.1021/cr50028a006). Internal controls confirm specificity: phenyl glycidyl ether (a real, commercially marketed epoxy reactive diluent with an unhindered terminal glycidyl carbon) correctly reaches `SCORED`, and oxetane (a four-membered, non-oxirane cyclic ether) correctly `FAILED_GATES` via the pre-existing ring-size clause. Proposed followup `R-DESIGNGATE-OXIRANE-STERIC` (substitution/glycidyl-motif clause in `bridge.cc` + hindered-epoxide fixture records) is filed, unresolved.

Across the portfolio, the emitted envelope, adapter, manifest, model receipt/card, portfolio policy, and Rust ranking boundary must all agree. The most restrictive policy controls.

## Inputs, outputs, and normalization

Current accepted format: canonical CandidateEnvelope JSON. The current runtime supports JSON plus molecule SMILES only through the central candidate contract. Target interface: canonical CandidateEnvelope JSON. That target interface is already the runtime interface for this module. Unsupported formats fail closed.

External chemistry normalizes once in `amphora-candidate-contract`; this module consumes canonical `CandidateEnvelope` data. Original bytes, normalized structure/formula, toolkit/version, stereochemistry, isotope, charge, fragment, mixture, polymer, and commercial-grade policies are retained in the capability profile.

Canonical input is a finite `molecule` `CandidateEnvelope` whose payload matches `candidate_type`. Canonical output is `ScoreEnvelope`; the primary value path is `gates.pass_all_hard`. Units, direction, nullability, authority, uncertainty, and claim locks are explicit in the profile and envelope. A null or blocked value cannot be converted to an objective.

## Canonical current examples and typed paths

```json
{"candidate_id": "amphora-molecule-design-gate-example", "candidate_type": "molecule", "molecule": {"role": "resin", "smiles": "CC"}}
```

The schema-valid fail-closed output example is checked in at `docs/capability-profile.json#/examples/current_output`. Exact paths are: objective `None`, metric `gates.pass_all_hard`, gate `gates`, uncertainty `uncertainty`, evidence gaps `missing_inputs`, and claim locks `claim_locks`. Nullability is explicit; empirical units and direction come only from the locked benchmark receipt. The authority ceiling is `REAL_ARITHMETIC` and solver-use ceiling is `CONSTRAINT_ONLY`.

## Data, theory, model, and uncertainty strategy

Applicability domain is solvent-borne two-component epoxy-polyamide marine-coating R&D and the explicitly declared candidate types. Missing values are not imputed across an authority boundary. Empirical work uses group, family, source, and time-safe splits; computed values remain labeled computed; candidate evidence remains separate from public context. Subgroup reporting and calibrated intervals are required wherever the locked KPI is empirical. Named standard, expert/CRO, primary-literature, simple physical, and hostile-null baselines precede promotion.

## KPI register and promotion gates

Primary KPI: **negative-control rejection** at `gates.pass_all_hard`. Direction and unit are declared by the locked benchmark; population is the declared applicability domain; split is group/time/source-safe; confidence intervals are mandatory for empirical claims. Locked target: Zero silent acceptance of malformed, unsupported, or unauthorized inputs before Phase 0; locked module-specific benchmark required for Phase 1.

- Phase 0 — Useful: deterministic or evidence-bound capability, contract parity, fail-closed malformed/OOD behavior, no unresolved authority contradiction, and the module acceptance tests pass.
- Phase 1 — Human parity: the locked independent evaluation beats or matches the best reproducible named baseline at the stated target with uncertainty.
- Phase 2 — Defensible IP: prospective superiority repeats independently, owned provenance and ablations freeze, and patent-versus-trade-secret review is documented. Counsel separately determines FTO.

Focused acceptance command: `cargo test --workspace --locked`. The native demo and replay commands in `AMPHORA_RUST.md` are the portfolio acceptance path.

External dependency or delay:

- Independent structural controls, EHS review, and synthesis assessment

Estimated effort is represented by the checked-in 0–5 priority factors, not a fabricated schedule. Schema drift, source mutation, incomplete folds, non-finite output, authority escalation, or lost claim locks automatically demote the module.

## Red-team dossier

Regression coverage must exercise malformed chemistry; mixtures, fragments, and polymers; unsupported formats; unit ambiguity; zero-mass ingredients; NaN and Infinity; out-of-domain inputs; group/source/time leakage; mutated sources; computed-as-measured records; spoofed identity; authority escalation; stripped or unknown claim locks; fixed-seed replay drift; and legal, regulatory, supplier, procurement, qualification, or release overclaim. Every such case must fail closed or remain an explicit evidence gap.

Module-focused checked fixture: `amphora-molecule-capabilities/src/lib.rs` via `cargo test --workspace --locked`. Scenario: Reject malformed chemistry and preserve EHS/synthesis/performance claim locks.
